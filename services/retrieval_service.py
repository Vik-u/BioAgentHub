#!/usr/bin/env python3
"""FastAPI service that exposes SQLite + FAISS retrieval endpoints for topic workspaces."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import faiss
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils import enzyme_aliases  # noqa: E402
from utils.kg_schema_utils import (  # noqa: E402
    dedupe_preserve_order,
    expand_query_with_schema,
    load_schema,
    schema_entity_candidates,
)

BASE = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", BASE / "KnowledgeGraph")).resolve()
VECTOR_DIR = WORKSPACE_ROOT / "vector_store"
GRAPH_DB = WORKSPACE_ROOT / "graph.sqlite"
LOG_DIR = BASE / "logs"
LOG_DIR.mkdir(exist_ok=True)
TRAJECTORY_LOG = LOG_DIR / "retrieval_trajectories.jsonl"
USE_ALIAS_EXPANSION = os.environ.get("USE_ALIAS_EXPANSION", "1") == "1"
USE_ITERATIVE_EXPANSION = os.environ.get("USE_ITERATIVE_EXPANSION", "1") == "1"


def should_use_petase_aliases(schema: Dict[str, Any]) -> bool:
    topic = str(schema.get("topic") or "").lower()
    return USE_ALIAS_EXPANSION and "petase" in topic


def collect_expansion_terms(results: Sequence[Dict[str, Any]], schema: Dict[str, Any], max_terms: int = 4) -> List[str]:
    """Mine top hits for schema entities to expand the query in a second pass."""
    candidates = schema_entity_candidates(schema) + schema.get("metrics", []) + schema.get("substrates", [])
    lowered_candidates = {c.lower(): c for c in candidates if c}
    expansions: List[str] = []
    for row in results:
        text = row.get("text", "")
        lower = text.lower()
        for alias_lower, canonical in lowered_candidates.items():
            if alias_lower in lower and canonical not in expansions:
                expansions.append(canonical)
                if len(expansions) >= max_terms:
                    return expansions
    return expansions


class VectorSearchRequest(BaseModel):
    query: str
    top_k: int = 5


class GraphQueryRequest(BaseModel):
    node: str
    top_k: int = 10


class HybridQueryRequest(BaseModel):
    query: str
    node: Optional[str] = None
    top_k: int = 5


def log_event(event: Dict[str, Any]) -> None:
    event["type"] = event.get("type", "retrieval")
    with TRAJECTORY_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


class RetrievalBackend:
    def __init__(self) -> None:
        if not VECTOR_DIR.exists():
            raise FileNotFoundError(f"Vector store not found at {VECTOR_DIR}")
        config_path = VECTOR_DIR / "config.json"
        model_name = json.loads(config_path.read_text())["model"]
        self.model = SentenceTransformer(model_name)
        self.embeddings = np.load(VECTOR_DIR / "embeddings.npy")
        self.metadata = [json.loads(line) for line in (VECTOR_DIR / "metadata.jsonl").open()]
        faiss_index_path = VECTOR_DIR / "index.faiss"
        self.faiss_index = faiss.read_index(str(faiss_index_path)) if faiss_index_path.exists() else None
        self.graph = sqlite3.connect(GRAPH_DB) if GRAPH_DB.exists() else None

    def embed(self, text: str) -> np.ndarray:
        vector = self.model.encode([text], normalize_embeddings=True)
        return vector.astype("float32")

    def _search_embeddings(self, vector: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        if self.faiss_index is not None:
            distances, indices = self.faiss_index.search(vector, top_k)
        else:
            sims = (self.embeddings @ vector.T).flatten()
            top_idx = np.argsort(-sims)[:top_k]
            distances = np.expand_dims(sims[top_idx], axis=0)
            indices = np.expand_dims(top_idx, axis=0)
        results = []
        for score, idx in zip(distances[0], indices[0]):
            doc = self.metadata[int(idx)]
            results.append({"score": float(score), **doc})
        return results

    def vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        schema = load_schema(WORKSPACE_ROOT)
        if USE_ALIAS_EXPANSION:
            if should_use_petase_aliases(schema):
                normalized_query = enzyme_aliases.expand_query(query)
            else:
                normalized_query = expand_query_with_schema(query, schema)
        else:
            normalized_query = query

        first_pass = self._search_embeddings(self.embed(normalized_query), max(top_k * 2, top_k))
        if USE_ITERATIVE_EXPANSION:
            expansions = collect_expansion_terms(first_pass, schema)
            extras = [term for term in expansions if term.lower() not in normalized_query.lower()]
            if extras:
                expanded_query = normalized_query + " " + " ".join(extras)
                second_pass = self._search_embeddings(self.embed(expanded_query), top_k * 2)
                combined = {row["metadata"]["chunk_id"]: row for row in first_pass + second_pass}
                reranked = sorted(combined.values(), key=lambda r: r.get("score", 0), reverse=True)
                results = reranked[:top_k]
                log_event(
                    {"event": "vector_search_iterative", "query": query, "expanded_query": expanded_query, "results": results}
                )
                return results

        results = first_pass[:top_k]
        log_event({"event": "vector_search", "query": query, "results": results})
        return results

    def _fetch_edges(self, node: str, limit: int) -> List[Dict[str, Any]]:
        if self.graph is None:
            return []
        cursor = self.graph.execute(
            """
            SELECT n1.label, e.relation, n2.label, e.paper, e.sentence
            FROM edges e
            JOIN nodes n1 ON e.source_id = n1.id
            JOIN nodes n2 ON e.target_id = n2.id
            WHERE n1.label = ?
            ORDER BY e.id DESC
            LIMIT ?
            """,
            (node, limit),
        )
        return [
            {"source": row[0], "relation": row[1], "target": row[2], "paper": row[3], "sentence": row[4]}
            for row in cursor.fetchall()
        ]

    def graph_neighbors(self, node: str, top_k: int) -> List[Dict[str, Any]]:
        if self.graph is None:
            return []
        rows = self._fetch_edges(node, top_k)
        log_event({"event": "graph_neighbors", "node": node, "results": rows})
        return rows

    def graph_neighbors_diverse(self, seeds: Sequence[str], top_k: int, per_seed: int = 3) -> List[Dict[str, Any]]:
        if self.graph is None:
            return []
        results: List[Dict[str, Any]] = []
        seen = set()
        for node in dedupe_preserve_order(seeds):
            if not node:
                continue
            edges = self._fetch_edges(node, per_seed)
            for edge in edges:
                key = (edge["source"], edge["relation"], edge["target"])
                if key in seen:
                    continue
                results.append(edge)
                seen.add(key)
                if len(results) >= top_k:
                    log_event({"event": "graph_neighbors_diverse", "seeds": list(seeds), "results": results})
                    return results
        log_event({"event": "graph_neighbors_diverse", "seeds": list(seeds), "results": results})
        return results


@lru_cache(maxsize=1)
def get_backend() -> RetrievalBackend:
    return RetrievalBackend()


app = FastAPI(title="Topic Retrieval Service")


@app.post("/vector_search")
def vector_search(payload: VectorSearchRequest) -> Dict[str, Any]:
    backend = get_backend()
    results = backend.vector_search(payload.query, payload.top_k)
    return {"results": results}


@app.post("/graph_neighbors")
def graph_neighbors(payload: GraphQueryRequest) -> Dict[str, Any]:
    backend = get_backend()
    results = backend.graph_neighbors(payload.node, payload.top_k)
    return {"results": results}


@app.post("/hybrid_query")
def hybrid_query(payload: HybridQueryRequest) -> Dict[str, Any]:
    backend = get_backend()
    vector_results = backend.vector_search(payload.query, payload.top_k)
    fallback_node = payload.node or (vector_results[0]["metadata"]["source"] if vector_results else "")
    graph_results = backend.graph_neighbors(fallback_node, payload.top_k) if fallback_node else []
    combined = {
        "vector": vector_results,
        "graph": graph_results,
    }
    log_event({"event": "hybrid_query", "query": payload.query, "node": payload.node, "results": combined})
    return combined
