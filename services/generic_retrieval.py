#!/usr/bin/env python3
"""Lightweight retrieval backend for generic workspaces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class GenericRetrievalBackend:
    def __init__(self, workspace: Path) -> None:
        workspace = workspace.resolve()
        vector_dir = workspace / "vector_store"
        if not vector_dir.exists():
            raise FileNotFoundError(f"Vector store missing: {vector_dir}")
        config = json.loads((vector_dir / "config.json").read_text())
        self.model = SentenceTransformer(config["model"])
        self.embeddings = np.load(vector_dir / "embeddings.npy")
        self.metadata = [json.loads(line) for line in (vector_dir / "metadata.jsonl").open()]
        index_path = vector_dir / "index.faiss"
        self.faiss_index = faiss.read_index(str(index_path)) if index_path.exists() else None

    def search(self, query: str, top_k: int = 8) -> List[Dict[str, Any]]:
        embedding = self.model.encode([query], normalize_embeddings=True).astype("float32")
        if self.faiss_index is not None:
            distances, indices = self.faiss_index.search(embedding, top_k)
        else:
            sims = (self.embeddings @ embedding.T).flatten()
            idx = np.argsort(-sims)[:top_k]
            distances = np.expand_dims(sims[idx], axis=0)
            indices = np.expand_dims(idx, axis=0)
        results = []
        for score, idx in zip(distances[0], indices[0]):
            doc = self.metadata[int(idx)]
            results.append({"score": float(score), **doc})
        return results
