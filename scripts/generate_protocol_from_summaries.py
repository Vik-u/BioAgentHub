#!/usr/bin/env python3
"""Generate a protocol from GPT summaries/markdown files with prioritized retrieval."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Dict
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from sentence_transformers import SentenceTransformer

from services import local_llm


def load_chunks(md_dir: Path, max_chars: int = 1200) -> List[Dict[str, str]]:
    docs: List[Dict[str, str]] = []
    for md_file in sorted(md_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8", errors="ignore")
        parts = []
        current = []
        length = 0
        for paragraph in text.split("\n\n"):
            p = paragraph.strip()
            if not p:
                continue
            if length + len(p) > max_chars and current:
                parts.append("\n\n".join(current))
                current = [p]
                length = len(p)
            else:
                current.append(p)
                length += len(p)
        if current:
            parts.append("\n\n".join(current))
        for idx, chunk in enumerate(parts):
            docs.append(
                {
                    "id": f"{md_file.stem}:{idx}",
                    "source": md_file.name,
                    "text": chunk,
                }
            )
    return docs


def rank_chunks(query: str, docs: List[Dict[str, str]], model_name: str, top_k: int) -> List[Dict[str, str]]:
    model = SentenceTransformer(model_name)
    embeddings = model.encode([doc["text"] for doc in docs], normalize_embeddings=True)
    q = model.encode([query], normalize_embeddings=True)[0]
    sims = embeddings @ q
    top_idx = np.argsort(-sims)[:top_k]
    results = []
    for idx in top_idx:
        doc = docs[int(idx)]
        results.append({"score": float(sims[idx]), **doc})
    return results


PROMPT = """You are designing a Tecan Fluent-guided workflow that prepares assay plates for PETase surface-display optimization and downstream Sciex ZenoTOF 7600 MS/MS analysis.

Question: {question}

Retrieved Fluent/assay evidence (prioritized summaries):
{evidence}

Write Markdown with two sections:
## Experimental Workflow
- Provide 8–12 numbered steps covering: deck setup, reagent loading, plate layout, dispense volumes/tips/speeds, incubations, seal/unseal, transfers to MS prep.
- Each step must spell out Action, Parameters (volumes, temperatures, timing, plate type), and Fluent-specific instructions (channels, carriers, safety interlocks).
- End with a step that prepares samples/plates suitable for ZenoTOF 7600 MS/MS (state volumes, plate type, sealing).

## Computational Workflow
- Describe data handling/analysis only (no wet-lab actions), e.g., design of condition matrix, parsing MS data, and iteration.

Use concise prose (no tables), and cite sources inline as [source:filename, score]."""


def format_evidence(chunks: List[Dict[str, str]]) -> str:
    lines = []
    for c in chunks:
        lines.append(f"- [source:{c['source']}, score={c['score']:.3f}] {c['text'][:1000]}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summaries-dir", type=Path, required=True, help="Directory with GPT summary .md files.")
    parser.add_argument("--question", required=True, help="Protocol objective/question.")
    parser.add_argument("--output", type=Path, required=True, help="Where to save the generated Markdown.")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    docs = load_chunks(args.summaries_dir)
    if not docs:
        raise SystemExit(f"No .md files found in {args.summaries_dir}")
    ranked = rank_chunks(args.question, docs, args.model, args.top_k)
    prompt = PROMPT.format(question=args.question, evidence=format_evidence(ranked))
    answer = local_llm.generate(prompt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(answer, encoding="utf-8")
    print(f"Protocol saved to {args.output}")


if __name__ == "__main__":
    main()
