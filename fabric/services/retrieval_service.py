#!/usr/bin/env python3
"""FastAPI service that exposes SQLite + FAISS retrieval endpoints for topic workspaces."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import faiss
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils import enzyme_aliases  # noqa: E402
from utils.kg_schema_utils import (  # noqa: E402
    dedupe_preserve_order,
    expand_query_with_schema,
    load_schema,
    schema_entity_candidates,
)
from utils.workspace_utils import resolve_workspace_root  # noqa: E402
from utils.output_paths import logs_dir  # noqa: E402
from fabric.services.embedding_backends import (  # noqa: E402
    EmbedderUnavailable,
    SentenceTransformerBackend,
    OpenAIEmbeddingBackend,
    load_embedding_backend,
)

BASE = Path(__file__).resolve().parents[2]
LOG_DIR = logs_dir()
TRAJECTORY_LOG = LOG_DIR / "retrieval_trajectories.jsonl"
USE_ALIAS_EXPANSION = os.environ.get("USE_ALIAS_EXPANSION", "1") == "1"
USE_ITERATIVE_EXPANSION = os.environ.get("USE_ITERATIVE_EXPANSION", "1") == "1"
BM25_MAX_DOCS = int(os.environ.get("QA_BM25_MAX_DOCS", "20000") or 20000)


def _tokenize(text: str) -> List[str]:
    return [tok for tok in re.findall(r"[a-z0-9]+", text.lower()) if len(tok) > 2]


def _read_vector_config(vector_dir: Path) -> Dict[str, Any]:
    config_path = vector_dir / "config.json"
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text())
    except Exception:
        return {}


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
    def __init__(self, workspace_root: Path | str | None = None) -> None:
        allow_noncanonical = os.environ.get("ALLOW_NONCANONICAL_WORKSPACE", "0") == "1"
        self.workspace_root = resolve_workspace_root(
            workspace_root=workspace_root,
            allow_noncanonical=allow_noncanonical,
        )
        vector_dir = self.workspace_root / "vector_store"
        graph_db = self.workspace_root / "graph.sqlite"
        if not vector_dir.exists():
            raise FileNotFoundError(f"Vector store not found at {vector_dir}")
        config = _read_vector_config(vector_dir)
        model_name = config.get("model") or os.environ.get("EMBEDDING_MODEL", "")
        backend_name = config.get("embedding_backend") or os.environ.get("EMBEDDING_BACKEND", "sentence-transformers")
        self.metadata = [json.loads(line) for line in (vector_dir / "metadata.jsonl").open()]
        self.embedder = None
        self.embedder_status = None
        self.embedder_error = None
        if model_name:
            try:
                self.embedder = load_embedding_backend(backend_name, model_name)
                if isinstance(self.embedder, (SentenceTransformerBackend, OpenAIEmbeddingBackend)):
                    self.embedder_status = self.embedder.status()
            except Exception as exc:
                self.embedder_error = f"{type(exc).__name__}: {exc}"
        if self.embedder_status and not self.embedder_status.available and self.embedder_status.error:
            self.embedder_error = self.embedder_status.error

        self.embeddings = np.load(vector_dir / "embeddings.npy")
        self.faiss_index = None
        faiss_index_path = vector_dir / "index.faiss"
        self.faiss_index = faiss.read_index(str(faiss_index_path)) if faiss_index_path.exists() else None
        self.graph = sqlite3.connect(graph_db) if graph_db.exists() else None
        self._bm25_index = None

    def embed(self, text: str) -> np.ndarray:
        if self.embedder is None:
            raise EmbedderUnavailable(self.embedder_error or "Embedding backend unavailable.")
        vector = self.embedder.embed_texts([text])
        return vector.astype("float32")

    def _search_embeddings(self, vector: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        if self.embeddings is None:
            return []
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
        schema = load_schema(self.workspace_root)
        if USE_ALIAS_EXPANSION:
            if should_use_petase_aliases(schema):
                normalized_query = enzyme_aliases.expand_query(query)
            else:
                normalized_query = expand_query_with_schema(query, schema)
        else:
            normalized_query = query

        if self.embedder is None or self.embedder_error:
            results = self.keyword_search(normalized_query, top_k)
            log_event({
                "event": "vector_search_fallback",
                "query": query,
                "results": results,
                "embedder_error": self.embedder_error,
            })
            return results

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

    def _build_bm25(self) -> None:
        if self._bm25_index is not None:
            return
        docs = []
        doc_lens = []
        df = {}
        max_docs = min(len(self.metadata), BM25_MAX_DOCS)
        for doc in self.metadata[:max_docs]:
            text = doc.get("text", "")
            tokens = _tokenize(text)
            docs.append(tokens)
            doc_lens.append(len(tokens))
            for tok in set(tokens):
                df[tok] = df.get(tok, 0) + 1
        avgdl = sum(doc_lens) / len(doc_lens) if doc_lens else 0.0
        self._bm25_index = {
            "docs": docs,
            "doc_lens": doc_lens,
            "df": df,
            "avgdl": avgdl,
            "doc_count": len(docs),
        }

    def keyword_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Lightweight BM25 over a capped subset of the vector-store metadata."""
        self._build_bm25()
        index = self._bm25_index or {}
        docs = index.get("docs", [])
        if not docs:
            return []
        df = index.get("df", {})
        avgdl = index.get("avgdl", 0.0)
        doc_count = index.get("doc_count", 0)

        k1 = 1.2
        b = 0.75
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []
        scores = []
        for idx, tokens in enumerate(docs):
            if not tokens:
                continue
            tf = Counter(tokens)
            score = 0.0
            dl = len(tokens)
            for tok in q_tokens:
                if tok not in tf:
                    continue
                df_tok = df.get(tok, 0)
                idf = np.log((doc_count - df_tok + 0.5) / (df_tok + 0.5) + 1)
                freq = tf[tok]
                denom = freq + k1 * (1 - b + b * (dl / avgdl if avgdl else 1))
                score += idf * ((freq * (k1 + 1)) / denom)
            if score > 0:
                scores.append((score, idx))
        scores.sort(reverse=True, key=lambda pair: pair[0])
        results = []
        for score, idx in scores[:top_k]:
            doc = self.metadata[idx]
            results.append({"score": float(score), **doc})
        log_event({"event": "keyword_search", "query": query, "results": results[:5]})
        return results


@lru_cache(maxsize=None)
def get_backend(workspace_root: str | Path | None = None) -> RetrievalBackend:
    return RetrievalBackend(workspace_root)


app = FastAPI(
    title="Topic Retrieval Service",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


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
