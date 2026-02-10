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

from utils.workspace_utils import resolve_workspace_root  # noqa: E402


def resolve_methodology_dirs() -> tuple[Path, Path]:
    workspace = resolve_workspace_root()
    return workspace / "methodology_vector_store", workspace / "methodology_edge_store"


class MethodologyRetrievalBackend:
    def __init__(self) -> None:
        section_dir, edge_dir = resolve_methodology_dirs()
        self.section_model = None
        self.section_embeddings = None
        self.section_metadata: List[Dict[str, Any]] = []
        self.section_faiss = None
        self.edge_model = None
        self.edge_embeddings = None
        self.edge_metadata: List[Dict[str, Any]] = []
        self.edge_faiss = None

        section_config = section_dir / "config.json"
        if section_config.exists():
            self.section_config = json.loads(section_config.read_text())
            self.section_model = SentenceTransformer(self.section_config["model"])
            self.section_embeddings = np.load(section_dir / "embeddings.npy")
            section_meta_path = section_dir / "metadata.jsonl"
            with section_meta_path.open(encoding="utf-8") as handle:
                self.section_metadata = [json.loads(line) for line in handle if line.strip()]
            section_index = section_dir / "index.faiss"
            self.section_faiss = faiss.read_index(str(section_index)) if (faiss and section_index.exists()) else None
        else:
            self.section_config = {}

        edge_config = edge_dir / "config.json"
        if edge_config.exists():
            self.edge_config = json.loads(edge_config.read_text())
            self.edge_model = SentenceTransformer(self.edge_config["model"])
            self.edge_embeddings = np.load(edge_dir / "embeddings.npy")
            edge_meta_path = edge_dir / "metadata.jsonl"
            with edge_meta_path.open(encoding="utf-8") as handle:
                self.edge_metadata = [json.loads(line) for line in handle if line.strip()]
            edge_index = edge_dir / "index.faiss"
            self.edge_faiss = faiss.read_index(str(edge_index)) if (faiss and edge_index.exists()) else None
        else:
            self.edge_config = {}

    def _vector_search(self, query: str, model, embeddings, metadata, index, top_k: int) -> List[Dict[str, Any]]:
        if model is None or embeddings is None or not metadata:
            return []
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
