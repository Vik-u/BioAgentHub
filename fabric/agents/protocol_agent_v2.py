#!/usr/bin/env python3
"""Enhanced protocol agent using full methodology sections + instrument KG."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

from services import local_llm
from utils.output_paths import logs_dir
from utils.workspace_utils import resolve_workspace_root
from services.methodology_retrieval import get_backend as get_method_backend
from services.instrument_retrieval import get_backend as get_instrument_backend

LOG_DIR = logs_dir() / "protocol_v2_runs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


DOI_RE = re.compile(r"(10\\.[0-9]{4,9}/[A-Z0-9._;()/:\\-]+)", re.IGNORECASE)


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


def load_sections_for_prompt(results: List[Dict[str, str]], source_map: Dict[tuple, int]) -> str:
    lines = []
    for doc in results:
        heading = doc.get("heading") or doc.get("section_type").title()
        paper = doc.get("paper") or Path(doc.get("pdf_file") or "").stem
        pdf_file = doc.get("pdf_file")
        doi = _extract_doi(doc.get("text")) or _doi_from_pdf(pdf_file)
        source_id = source_map.get((paper, pdf_file, doi))
        label = f"S{source_id}" if source_id else "S?"
        lines.append(f"### {heading} ({label} — {paper})\n{doc.get('text')[:1500]}")
    return "\n\n".join(lines)


def gather_methodology_edges(question: str, limit: int = 40) -> List[Dict[str, str]]:
    backend = get_method_backend()
    return backend.edge_search(question, top_k=limit)


def gather_instrument_evidence(question: str, sections: List[Dict[str, str]]) -> List[Dict[str, str]]:
    try:
        backend = get_instrument_backend()
    except Exception:
        return []
    queries = [question] + [sec.get("text", "")[:300] for sec in sections]
    evidence = []
    seen = set()
    for query in queries:
        for row in backend.vector_search(query, top_k=8):
            meta = row["metadata"]
            key = (meta["instrument"], meta["relation"], meta["value"])
            if key in seen:
                continue
            seen.add(key)
            evidence.append(
                {
                    "instrument": meta["instrument"],
                    "relation": meta["relation"],
                    "value": meta["value"],
                    "sentence": meta["sentence"],
                    "pdf_file": meta["pdf_file"],
                }
            )
            if len(evidence) >= 30:
                return evidence
    return evidence


PROMPT_TEMPLATE = """You are drafting a protocol using the provided methodology sections and instrument specifications.

Question: {question}

Sources (cite as [S#] after relevant steps):
{source_index}

Experimental methodology excerpts:
{experimental_sections}

Computational methodology excerpts:
{computational_sections}

Results/outcome snippets:
{results_sections}

Quantitative parameters:
{parameter_edges}

Instrument capabilities:
{instrument_evidence}

Write Markdown with these strict rules:
1) Include **exactly two sections** in this order: `## Computational Workflow` then `## Experimental Workflow`.
2) Computational Workflow:
   - Provide **at least 3 numbered steps** focused only on design/simulation/data processing.
   - Include a **Design-to-Experiment Handoff** step that outputs: variant list, construct plan, assay design, plate layout, and acceptance criteria.
   - Include an **Experiment-to-Design Feedback** step explaining how assay results update next designs.
   - End each step with `Citations: [S#]` or `Citations: [S?]` if no direct source exists.
3) Experimental Workflow:
   - Provide **8–12 numbered steps** covering full wet-lab execution from setup to analytics and QC.
   - Each step must include labeled sub-bullets (use this order, every time): Goal, Reagents/Volumes, Instruments, Parameters, Actions, QC/Observations, Next Step Trigger, Safety (if applicable).
   - Actions must be **execution-ready**: 2–5 imperative sentences with concrete setup, mixing, incubation, and measurement details.
   - Include controls, replicates, and acceptance criteria where relevant.
   - End each step with `Citations: [S#]` or `Citations: [S?]` if no direct source exists.
   - Use concrete numbers (volumes, temperatures, times, pH, speeds, plate formats) pulled from the excerpts/edges; avoid vague terms.
   - Cite instruments (bold names) and why they fit the step.
   - Safety: only include if a specific hazard or biosafety detail is stated; otherwise write "Safety: Not specified in sources."
4) Cite sources inline as [S#] wherever possible. Do NOT use tables.
"""


def run_protocol_agent_v2(question: str) -> str:
    method_backend = get_method_backend()
    experimental = method_backend.section_search(question + " experimental workflow", top_k=6, section_type="experimental")
    computational = method_backend.section_search(question + " computational workflow", top_k=4, section_type="computational")
    results = method_backend.section_search(question + " activity results", top_k=3, section_type="results")
    edges = gather_methodology_edges(question, limit=40)
    instrument_evidence = gather_instrument_evidence(question, experimental)
    citations: List[Dict[str, str | None]] = []
    seen: Dict[tuple, int] = {}

    def register_source(paper: str | None, pdf_file: str | None, text: str | None) -> int | None:
        if not (paper or pdf_file or text):
            return None
        label = paper or (Path(pdf_file).stem if pdf_file else None)
        doi = _extract_doi(text or "") or _doi_from_pdf(pdf_file)
        key = (label, pdf_file, doi)
        if key in seen:
            return seen[key]
        seen[key] = len(citations) + 1
        citations.append({"label": label, "doi": doi, "pdf_file": pdf_file})
        return seen[key]

    source_map: Dict[tuple, int] = {}
    for doc in experimental + computational + results:
        paper = doc.get("paper") or Path(doc.get("pdf_file") or "").stem
        pdf_file = doc.get("pdf_file")
        doi = _extract_doi(doc.get("text")) or _doi_from_pdf(pdf_file)
        source_id = register_source(paper, pdf_file, doc.get("text"))
        if source_id:
            source_map[(paper, pdf_file, doi)] = source_id
    for edge in edges:
        meta = edge.get("metadata", {})
        paper = meta.get("paper") or Path(meta.get("pdf_file") or "").stem
        pdf_file = meta.get("pdf_file")
        text = edge.get("text") or meta.get("sentence")
        doi = _extract_doi(text) or _doi_from_pdf(pdf_file)
        source_id = register_source(paper, pdf_file, text)
        if source_id:
            source_map[(paper, pdf_file, doi)] = source_id
    for ev in instrument_evidence:
        paper = Path(ev.get("pdf_file") or "").stem
        pdf_file = ev.get("pdf_file")
        text = ev.get("sentence")
        doi = _extract_doi(text) or _doi_from_pdf(pdf_file)
        source_id = register_source(paper, pdf_file, text)
        if source_id:
            source_map[(paper, pdf_file, doi)] = source_id

    def source_index_text() -> str:
        lines = []
        for idx, entry in enumerate(citations, start=1):
            label = entry.get("label") or "Unknown source"
            doi = entry.get("doi")
            suffix = f" DOI:{doi}" if doi else ""
            lines.append(f"S{idx}: {label}{suffix}")
        return "\n".join(lines) if lines else "S1: No sources found."
    def format_source_id(source_id: int | None) -> str:
        return f"S{source_id}" if source_id else "S?"

    parameter_lines = []
    for edge in edges[:20]:
        meta = edge.get("metadata", {})
        source_id = register_source(meta.get("paper"), meta.get("pdf_file"), edge.get("text") or meta.get("sentence"))
        parameter_lines.append(
            f"- {meta.get('relation')}: {meta.get('value')} (source: {format_source_id(source_id)})"
        )

    instrument_lines = []
    for ev in instrument_evidence:
        source_id = register_source(Path(ev.get("pdf_file") or "").stem, ev.get("pdf_file"), ev.get("sentence"))
        instrument_lines.append(
            f"- **{ev['instrument']}** ({ev['relation']}: {ev['value']}) – {format_source_id(source_id)} {ev['sentence']}"
        )

    prompt = PROMPT_TEMPLATE.format(
        question=question,
        source_index=source_index_text(),
        experimental_sections=load_sections_for_prompt(experimental, source_map),
        computational_sections=load_sections_for_prompt(computational, source_map),
        results_sections=load_sections_for_prompt(results, source_map),
        parameter_edges="\n".join(parameter_lines),
        instrument_evidence="\n".join(instrument_lines),
    )
    answer = local_llm.generate(prompt)
    if citations:
        answer = answer.strip() + "\n\nSources:\n" + "\n".join(
            f"[S{i}] {entry.get('label')}{(' DOI:' + entry['doi']) if entry.get('doi') else ''}"
            for i, entry in enumerate(citations, start=1)
        )
    record_run(question, experimental, computational, results, edges, instrument_evidence, answer)
    return answer


def record_run(question: str, experimental, computational, results, edges, instrument_evidence, answer: str) -> None:
    payload = {
        "question": question,
        "experimental_sections": experimental,
        "computational_sections": computational,
        "results_sections": results,
        "parameter_edges": edges,
        "instrument_evidence": instrument_evidence,
        "answer": answer,
    }
    existing = []
    for path in LOG_DIR.glob("run_*.json"):
        try:
            existing.append(int(path.stem.split("_")[-1]))
        except ValueError:
            continue
    next_idx = max(existing) + 1 if existing else 0
    out_path = LOG_DIR / f"run_{next_idx:05d}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
