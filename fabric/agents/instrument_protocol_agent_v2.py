#!/usr/bin/env python3
"""Instrument-aware protocol generator that uses full-text KG/FAISS evidence."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

from services import local_llm
from utils.output_paths import logs_dir
from utils.workspace_utils import resolve_workspace_root
from services.instrument_retrieval import get_backend, instrument_usage_enabled
from agents.protocol_agent import retrieve_snippets

EVIDENCE_LIMIT = 40
PROTOCOL_SNIPPET_LIMIT = 4
OUTPUT_DIR = logs_dir() / "instrument_protocol_runs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DOI_RE = re.compile(r"(10\\.[0-9]{4,9}/[A-Z0-9._;()/:\\-]+)", re.IGNORECASE)


@dataclass
class Evidence:
    instrument: str
    relation: str
    value: str
    sentence: str
    pdf_file: str
    score: float = 0.0


def gather_instrument_evidence(question: str, snippets: Sequence[Dict[str, str]]) -> List[Evidence]:
    if not instrument_usage_enabled():
        return []
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


def _extract_doi(text: str | None) -> str | None:
    if not text:
        return None
    match = DOI_RE.search(text)
    if match:
        return match.group(1).rstrip(").,;")
    return None


def _text_path_for_pdf(pdf_file: str | None) -> Path | None:
    if not pdf_file:
        return None
    workspace = resolve_workspace_root()
    candidate = workspace / "text" / f"{Path(pdf_file).stem}.txt"
    return candidate if candidate.exists() else None


def _doi_from_pdf(pdf_file: str | None) -> str | None:
    txt_path = _text_path_for_pdf(pdf_file)
    if not txt_path:
        return None
    try:
        snippet = txt_path.read_text(encoding="utf-8", errors="ignore")[:20000]
    except Exception:
        return None
    return _extract_doi(snippet)


PROMPT_TEMPLATE = """You are assembling a detailed protocol that must use the listed Biofoundry instruments.

Question: {question}

Sources (cite as [S#] after relevant steps):
{source_index}

Reference protocol snippets:
{snippet_block}

Instrument evidence:
{instrument_block}

Write a comprehensive Markdown response with two sections in this order:
## Computational Workflow
- At least 3 numbered steps; only analysis/design/data handling (no pipetting).
- Include a **Design-to-Experiment Handoff** step that outputs: variant list, construct plan, assay design, plate layout, acceptance criteria.
- Include an **Experiment-to-Design Feedback** step that describes how instrument data updates the next design cycle.
- End each step with `Citations: [S#]` or `Citations: [S?]` if no direct source exists.

## Experimental Workflow
- Provide 8–12 numbered steps, covering full execution from setup to analytics.
- For **every step**, include labeled sub-bullets in this exact order: Goal, Reagents/Volumes, Instruments (bold and explain suitability), Parameters (temp, time, speed, pH, plate type), Actions (imperative), QC/Observations, Next Step Trigger, Safety (if applicable).
- Actions must be **execution-ready**: 2–5 imperative sentences with concrete setup, mixing, incubation, and measurement details.
- Use instrument evidence to anchor volumes/formats; keep this section purely wet-lab.
- Safety: only include if a specific hazard or biosafety detail is stated; otherwise write "Safety: Not specified in sources."
- End each step with `Citations: [S#]` or `Citations: [S?]` if no direct source exists.

No tables. Use concrete numbers from evidence wherever possible and cite sources as [S#]."""


def assemble_snippet_block(snippets: Sequence[Dict[str, str]]) -> str:
    lines = []
    for snip in snippets[:PROTOCOL_SNIPPET_LIMIT]:
        lines.append(f"[{snip['id']}] {snip['title']} :: {snip['text']}")
    return "\n".join(lines)


def run_instrument_protocol_v2(question: str) -> str:
    snippets = retrieve_snippets(question, top_k=6)
    evidence = gather_instrument_evidence(question, snippets)
    citations: List[Dict[str, str | None]] = []
    seen: Dict[tuple, int] = {}

    def register_source(label: str | None, pdf_file: str | None, text: str | None) -> int | None:
        if not (label or pdf_file or text):
            return None
        doi = _extract_doi(text or "") or _doi_from_pdf(pdf_file)
        key = (label, pdf_file, doi)
        if key in seen:
            return seen[key]
        seen[key] = len(citations) + 1
        citations.append({"label": label, "doi": doi, "pdf_file": pdf_file})
        return seen[key]

    def source_index_text() -> str:
        lines = []
        for idx, entry in enumerate(citations, start=1):
            label = entry.get("label") or "Unknown source"
            doi = entry.get("doi")
            suffix = f" DOI:{doi}" if doi else ""
            lines.append(f"S{idx}: {label}{suffix}")
        return "\n".join(lines) if lines else "S1: No sources found."

    for snip in snippets:
        register_source(snip.get("title"), snip.get("pdf_file"), snip.get("text"))
    for ev in evidence:
        label = Path(ev.pdf_file).stem if ev.pdf_file else ev.instrument
        register_source(label, ev.pdf_file, ev.sentence)

    prompt = PROMPT_TEMPLATE.format(
        question=question,
        source_index=source_index_text(),
        snippet_block=assemble_snippet_block(snippets),
        instrument_block=format_evidence(evidence),
    )
    answer = local_llm.generate(prompt)
    if citations:
        answer = answer.strip() + "\n\nSources:\n" + "\n".join(
            f"[S{i}] {entry.get('label')}{(' DOI:' + entry['doi']) if entry.get('doi') else ''}"
            for i, entry in enumerate(citations, start=1)
        )
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
