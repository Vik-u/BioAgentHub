#!/usr/bin/env python3
"""Embedding backend wrappers for vector store rebuilds and retrieval."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import List, Optional
from urllib import request

import numpy as np


class EmbedderUnavailable(RuntimeError):
    pass


@dataclass
class EmbedderStatus:
    backend: str
    model: str
    available: bool
    error: Optional[str] = None


class SentenceTransformerBackend:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None
        self._error = None
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name)
        except Exception as exc:
            self._error = f"{type(exc).__name__}: {exc}"

    def status(self) -> EmbedderStatus:
        return EmbedderStatus(
            backend="sentence-transformers",
            model=self.model_name,
            available=self._model is not None,
            error=self._error,
        )

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        if self._model is None:
            raise EmbedderUnavailable(self._error or "SentenceTransformer unavailable.")
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return np.asarray(embeddings, dtype="float32")


class OpenAIEmbeddingBackend:
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None) -> None:
        if not api_key:
            raise EmbedderUnavailable("OPENAI_API_KEY is not set.")
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = (base_url or "https://api.openai.com/v1/embeddings").rstrip("/")

    def status(self) -> EmbedderStatus:
        return EmbedderStatus(
            backend="openai",
            model=self.model_name,
            available=True,
            error=None,
        )

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        payload = {
            "model": self.model_name,
            "input": texts,
        }
        req = request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        data = sorted(body.get("data", []), key=lambda item: item.get("index", 0))
        embeddings = [item["embedding"] for item in data]
        return np.asarray(embeddings, dtype="float32")


def load_embedding_backend(backend: str, model_name: str) -> object:
    backend = backend.lower().strip()
    if backend in {"sentence-transformers", "sentence_transformers", "st"}:
        return SentenceTransformerBackend(model_name)
    if backend in {"openai", "openai-embeddings"}:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        base_url = os.environ.get("OPENAI_EMBED_BASE_URL", "")
        return OpenAIEmbeddingBackend(model_name, api_key, base_url or None)
    raise ValueError(f"Unknown embedding backend: {backend}")


def embed_in_batches(embedder: object, texts: List[str], batch_size: int = 64) -> np.ndarray:
    if not texts:
        return np.empty((0, 0), dtype="float32")
    chunks = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        chunk = embedder.embed_texts(batch)
        chunks.append(chunk)
        time.sleep(0.01)
    return np.vstack(chunks)
