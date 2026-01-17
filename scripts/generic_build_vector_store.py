#!/usr/bin/env python3
"""Build a sentence-transformer vector store for a generic workspace."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
from sentence_transformers import SentenceTransformer

try:
    import faiss
except Exception:  # pragma: no cover
    faiss = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.kg_schema_utils import build_alias_lookup, filter_seed_candidates, load_schema  # noqa: E402

enzyme_pattern = re.compile(r"\b([A-Za-z][A-Za-z0-9-]{2,}ase)\b", re.IGNORECASE)


def load_metadata(workspace: Path) -> Dict[str, dict]:
    index_path = workspace / "corpus_index.json"
    if not index_path.exists():
        return {}
    records = json.loads(index_path.read_text())
    return {entry["txt_file"]: entry for entry in records}


def split_chunks(text: str, max_chars: int = 1200) -> List[str]:
    parts = []
    current = []
    length = 0
    for paragraph in text.split("\n\n"):
        stripped = paragraph.strip()
        if not stripped:
            continue
        if length + len(stripped) > max_chars and current:
            parts.append("\n".join(current))
            current = [stripped]
            length = len(stripped)
        else:
            current.append(stripped)
            length += len(stripped)
    if current:
        parts.append("\n".join(current))
    return parts or [text[:max_chars]]


def extract_sources(text: str, alias_lookup: Dict[str, str]) -> List[str]:
    lowered = text.lower()
    hits: List[str] = []
    for alias, canonical in alias_lookup.items():
        if alias and alias in lowered:
            hits.append(canonical)
    for match in enzyme_pattern.finditer(text):
        hits.append(match.group(1))
    return filter_seed_candidates(hits)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace created via generic_extract_corpus.")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--no-faiss", action="store_true")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    text_dir = workspace / "text"
    if not text_dir.exists():
        raise SystemExit(f"Missing text directory: {text_dir}")
    meta_map = load_metadata(workspace)
    schema = load_schema(workspace)
    alias_lookup = build_alias_lookup(schema)

    docs = []
    for txt_path in sorted(text_dir.glob("*.txt")):
        text = txt_path.read_text(errors="ignore")
        chunks = split_chunks(text)
        meta = meta_map.get(txt_path.name, {})
        for idx, chunk in enumerate(chunks):
            sources = extract_sources(chunk, alias_lookup)
            docs.append(
                {
                    "text": chunk,
                    "metadata": {
                        "chunk_id": f"{txt_path.stem}:{idx}",
                        "pdf_file": meta.get("pdf_file"),
                        "title": meta.get("title_candidate"),
                        "source": sources[0] if sources else None,
                        "sources": sources,
                    },
                }
            )

    out_dir = workspace / "vector_store"
    out_dir.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(args.model)
    embeddings = model.encode([doc["text"] for doc in docs], batch_size=64, show_progress_bar=True).astype("float32")
    np.save(out_dir / "embeddings.npy", embeddings)
    meta_path = out_dir / "metadata.jsonl"
    with meta_path.open("w", encoding="utf-8") as handle:
        for doc in docs:
            handle.write(json.dumps(doc, ensure_ascii=False) + "\n")

    faiss_path = None
    if not args.no_faiss and faiss is not None:
        normed = embeddings.copy()
        faiss.normalize_L2(normed)
        index = faiss.IndexFlatIP(normed.shape[1])
        index.add(normed)
        faiss_path = out_dir / "index.faiss"
        faiss.write_index(index, str(faiss_path))

    config = {
        "model": args.model,
        "document_count": len(docs),
        "dimension": embeddings.shape[1],
        "embedding_file": "embeddings.npy",
        "metadata_file": meta_path.name,
        "faiss_index_file": faiss_path.name if faiss_path else None,
    }
    (out_dir / "config.json").write_text(json.dumps(config, indent=2))
    print(f"Built vector store with {len(docs)} chunks under {out_dir}")


if __name__ == "__main__":
    main()
