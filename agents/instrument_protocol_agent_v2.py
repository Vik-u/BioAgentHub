#!/usr/bin/env python3
"""Instrument-aware protocol generator that uses full-text KG/FAISS evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

from services import local_llm
from services.instrument_retrieval import get_backend
from agents.protocol_agent import retrieve_snippets

EVIDENCE_LIMIT = 40
PROTOCOL_SNIPPET_LIMIT = 4
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "logs" / "instrument_protocol_runs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Evidence:
    instrument: str
    relation: str
    value: str
    sentence: str
    pdf_file: str
    score: float = 0.0


def gather_instrument_evidence(question: str, snippets: Sequence[Dict[str, str]]) -> List[Evidence]:
    backend = get_backend()
    query_blocks = [question] + [snip["text"] for snip in snippets]
    seen: Dict[str, Evidence] = {}
    for block in query_blocks:
        results = backend.vector_search(block, top_k=12)
        for row in results:
            meta = row["metadata"]
            key = (meta["instrument"], meta["relation"], meta["value"])
            if key in seen:
                continue
            evidence = Evidence(
                instrument=meta["instrument"],
                relation=meta["relation"],
                value=meta["value"],
                sentence=meta["sentence"],
                pdf_file=meta["pdf_file"],
                score=row.get("score", 0.0),
            )
            seen[key] = evidence
    # Expand with graph neighbors for top instruments
    top_instruments = {}
    for ev in sorted(seen.values(), key=lambda e: e.score, reverse=True):
        top_instruments.setdefault(ev.instrument, 0)
        top_instruments[ev.instrument] += 1
        if len(top_instruments) >= 8:
            break
    backend = get_backend()
    for inst in list(top_instruments.keys()):
        for row in backend.graph_query(inst, top_k=6):
            key = (row["instrument"], row["relation"], row["value"])
            if key in seen:
                continue
            seen[key] = Evidence(
                instrument=row["instrument"],
                relation=row["relation"],
                value=row["value"],
                sentence=row["sentence"],
                pdf_file=row["pdf_file"],
                score=0.2,
            )
    return sorted(seen.values(), key=lambda e: e.score, reverse=True)[:EVIDENCE_LIMIT]


def format_evidence(evidence: Sequence[Evidence]) -> str:
    lines = []
    for ev in evidence:
        lines.append(
            f"- **{ev.instrument}** ({ev.relation}: {ev.value}) — {ev.sentence.strip()} (source: {ev.pdf_file})"
        )
    return "\n".join(lines)


PROMPT_TEMPLATE = """You are assembling a detailed protocol that must use the listed Biofoundry instruments.

Question: {question}

Reference protocol snippets:
{snippet_block}

Instrument evidence:
{instrument_block}

Write a comprehensive Markdown response with two sections:
## Experimental Workflow
- Provide 8–12 numbered steps, covering full execution from setup to analytics.
- For **every step**, include labeled sub-bullets in this exact order: Goal, Reagents/Volumes, Instruments (bold and explain suitability), Parameters (temp, time, speed, pH, plate type), Actions (imperative), QC/Observations, Next Step Trigger, Safety (if applicable).
- Use instrument evidence to anchor volumes/formats; keep this section purely wet-lab.

## Computational Workflow
- At least 3 numbered steps; only analysis/design/data handling (no pipetting).
- Mention how instrument data flows into modeling/QC and drives next designs.

No tables. Use concrete numbers from evidence wherever possible."""


def assemble_snippet_block(snippets: Sequence[Dict[str, str]]) -> str:
    lines = []
    for snip in snippets[:PROTOCOL_SNIPPET_LIMIT]:
        lines.append(f"[{snip['id']}] {snip['title']} :: {snip['text']}")
    return "\n".join(lines)


def run_instrument_protocol_v2(question: str) -> str:
    snippets = retrieve_snippets(question, top_k=6)
    evidence = gather_instrument_evidence(question, snippets)
    prompt = PROMPT_TEMPLATE.format(
        question=question,
        snippet_block=assemble_snippet_block(snippets),
        instrument_block=format_evidence(evidence),
    )
    answer = local_llm.generate(prompt)
    record_run(question, snippets, evidence, answer)
    return answer


def record_run(question: str, snippets: Sequence[Dict[str, str]], evidence: Sequence[Evidence], answer: str) -> None:
    payload = {
        "question": question,
        "snippets": snippets,
        "evidence": [ev.__dict__ for ev in evidence],
        "answer": answer,
    }
    path = OUTPUT_DIR / f"protocol_run_{len(list(OUTPUT_DIR.glob('protocol_run_*.json'))):05d}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
