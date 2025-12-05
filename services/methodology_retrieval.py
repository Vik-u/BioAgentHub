#!/usr/bin/env python3
"""Retrieval utilities for methodology sections and KG edges."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Sequence

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional
    faiss = None
import numpy as np
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SECTION_DIR = PROJECT_ROOT / "KnowledgeGraph" / "methodology_vector_store"
EDGE_DIR = PROJECT_ROOT / "KnowledgeGraph" / "methodology_edge_store"


class MethodologyRetrievalBackend:
    def __init__(self) -> None:
        self.section_config = json.loads((SECTION_DIR / "config.json").read_text())
        self.section_model = SentenceTransformer(self.section_config["model"])
        self.section_embeddings = np.load(SECTION_DIR / "embeddings.npy")
        self.section_metadata = [json.loads(line) for line in (SECTION_DIR / "metadata.jsonl").open()]
        section_index = SECTION_DIR / "index.faiss"
        self.section_faiss = faiss.read_index(str(section_index)) if (faiss and section_index.exists()) else None

        self.edge_config = json.loads((EDGE_DIR / "config.json").read_text())
        self.edge_model = SentenceTransformer(self.edge_config["model"])
        self.edge_embeddings = np.load(EDGE_DIR / "embeddings.npy")
        self.edge_metadata = [json.loads(line) for line in (EDGE_DIR / "metadata.jsonl").open()]
        edge_index = EDGE_DIR / "index.faiss"
        self.edge_faiss = faiss.read_index(str(edge_index)) if (faiss and edge_index.exists()) else None

    def _vector_search(self, query: str, model, embeddings, metadata, index, top_k: int) -> List[Dict[str, Any]]:
        vec = model.encode([query], normalize_embeddings=True).astype("float32")
        if index is not None:
            distances, indices = index.search(vec, top_k)
        else:
            sims = (embeddings @ vec.T).flatten()
            idx = np.argsort(-sims)[:top_k]
            distances = np.expand_dims(sims[idx], axis=0)
            indices = np.expand_dims(idx, axis=0)
        results = []
        for score, idx in zip(distances[0], indices[0]):
            doc = metadata[int(idx)]
            results.append({"score": float(score), **doc})
        return results

    def section_search(self, query: str, top_k: int = 6, section_type: str | None = None) -> List[Dict[str, Any]]:
        docs = self._vector_search(query, self.section_model, self.section_embeddings, self.section_metadata, self.section_faiss, top_k * 2)
        if section_type:
            docs = [doc for doc in docs if doc.get("section_type") == section_type]
        return docs[:top_k]

    def edge_search(self, query: str, top_k: int = 40) -> List[Dict[str, Any]]:
        return self._vector_search(query, self.edge_model, self.edge_embeddings, self.edge_metadata, self.edge_faiss, top_k)

    def filter_edges_by_section(self, sections: Sequence[Dict[str, Any]], max_per_paper: int = 12) -> List[Dict[str, Any]]:
        selected: List[Dict[str, Any]] = []
        per_paper: Dict[str, int] = {}
        paper_lookup = {section["paper"]: set() for section in sections if section.get("paper")}
        for edge in self.edge_metadata:
            paper = edge["metadata"]["paper"]
            if paper not in paper_lookup:
                continue
            count = per_paper.get(paper, 0)
            if count >= max_per_paper:
                continue
            selected.append(edge["metadata"])
            per_paper[paper] = count + 1
        return selected


@lru_cache(maxsize=1)
def get_backend() -> MethodologyRetrievalBackend:
    return MethodologyRetrievalBackend()
