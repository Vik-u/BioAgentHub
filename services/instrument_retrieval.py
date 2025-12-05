#!/usr/bin/env python3
"""Retrieval helpers for instrument manuals (vector store + KG)."""

from __future__ import annotations

import json
import sqlite3
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
IG_ROOT = PROJECT_ROOT / "InstrumentGraph"
VECTOR_DIR = IG_ROOT / "vector_store"
KG_DB = IG_ROOT / "instrument_graph.sqlite"


def ensure_graph_db():
    if KG_DB.exists():
        return
    import sqlite3  # local import to avoid circular

    edges_path = IG_ROOT / "kg_edges.jsonl"
    conn = sqlite3.connect(KG_DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument TEXT,
            relation TEXT,
            value TEXT,
            sentence TEXT,
            pdf_file TEXT
        )
        """
    )
    with edges_path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            conn.execute(
                "INSERT INTO edges(instrument, relation, value, sentence, pdf_file) VALUES(?,?,?,?,?)",
                (
                    payload["instrument"],
                    payload["relation"],
                    payload["value"],
                    payload["sentence"],
                    payload["pdf_file"],
                ),
            )
    conn.commit()
    conn.close()


class InstrumentRetrievalBackend:
    def __init__(self):
        config = json.loads((VECTOR_DIR / "config.json").read_text())
        self.model = SentenceTransformer(config["model"])
        self.embeddings = np.load(VECTOR_DIR / "embeddings.npy")
        self.metadata = [json.loads(line) for line in (VECTOR_DIR / "metadata.jsonl").open()]
        faiss_path = VECTOR_DIR / "index.faiss"
        self.faiss_index = faiss.read_index(str(faiss_path)) if (faiss and faiss_path.exists()) else None
        ensure_graph_db()
        self.graph = sqlite3.connect(KG_DB)

    def embed(self, text: str) -> np.ndarray:
        return self.model.encode([text], normalize_embeddings=True).astype("float32")

    def vector_search(self, query: str, top_k: int = 8) -> List[Dict[str, Any]]:
        vec = self.embed(query)
        if self.faiss_index is not None:
            distances, indices = self.faiss_index.search(vec, top_k)
        else:
            sims = (self.embeddings @ vec.T).flatten()
            idx = np.argsort(-sims)[:top_k]
            distances = np.expand_dims(sims[idx], axis=0)
            indices = np.expand_dims(idx, axis=0)
        results = []
        for score, idx in zip(distances[0], indices[0]):
            doc = self.metadata[int(idx)]
            results.append({"score": float(score), **doc})
        return results

    def graph_query(self, instrument: str, top_k: int = 20) -> List[Dict[str, Any]]:
        cursor = self.graph.execute(
            """
            SELECT relation, value, sentence, pdf_file
            FROM edges
            WHERE instrument = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (instrument, top_k),
        )
        return [
            {
                "instrument": instrument,
                "relation": row[0],
                "value": row[1],
                "sentence": row[2],
                "pdf_file": row[3],
            }
            for row in cursor.fetchall()
        ]

    def graph_search_relation(self, relation: str, keyword: str, top_k: int = 25) -> List[Dict[str, Any]]:
        cursor = self.graph.execute(
            """
            SELECT instrument, relation, value, sentence, pdf_file
            FROM edges
            WHERE relation = ? AND value LIKE ?
            LIMIT ?
            """,
            (relation, f"%{keyword}%", top_k),
        )
        return [
            {
                "instrument": row[0],
                "relation": row[1],
                "value": row[2],
                "sentence": row[3],
                "pdf_file": row[4],
            }
            for row in cursor.fetchall()
        ]


@lru_cache(maxsize=1)
def get_backend() -> InstrumentRetrievalBackend:
    return InstrumentRetrievalBackend()
