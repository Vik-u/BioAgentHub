#!/usr/bin/env python3
"""Enhanced protocol agent using full methodology sections + instrument KG."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from services import local_llm
from services.methodology_retrieval import get_backend as get_method_backend
from services.instrument_retrieval import get_backend as get_instrument_backend

LOG_DIR = Path(__file__).resolve().parents[1] / "logs" / "protocol_v2_runs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_sections_for_prompt(results: List[Dict[str, str]]) -> str:
    lines = []
    for doc in results:
        heading = doc.get("heading") or doc.get("section_type").title()
        lines.append(f"### {heading} ({doc.get('paper')})\n{doc.get('text')[:1500]}")
    return "\n\n".join(lines)


def gather_methodology_edges(question: str, limit: int = 40) -> List[Dict[str, str]]:
    backend = get_method_backend()
    return backend.edge_search(question, top_k=limit)


def gather_instrument_evidence(question: str, sections: List[Dict[str, str]]) -> List[Dict[str, str]]:
    backend = get_instrument_backend()
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
1) Include **exactly two sections**: `## Experimental Workflow` and `## Computational Workflow`.
2) Experimental Workflow:
   - Provide **8–12 numbered steps** covering the full lab execution from setup to analytics and QC.
   - Each step must include labeled sub-bullets (use this order, every time): Goal, Reagents/Volumes, Instruments, Parameters, Actions, QC/Observations, Next Step Trigger, Safety (if applicable).
   - Use concrete numbers (volumes, temperatures, times, pH, speeds, plate formats) pulled from the excerpts/edges; avoid vague terms.
   - Keep this section purely wet-lab (no modeling); cite instruments (bold names) and why they fit the step.
3) Computational Workflow:
   - Provide **at least 3 numbered steps** focused only on design, simulation, data processing, or analysis (no pipetting).
   - Reference how experimental data feeds back into design; include key parameters or model choices if present in evidence.
4) Do NOT use tables. Write concise prose with the required labeled sub-bullets for every experimental step.
"""


def run_protocol_agent_v2(question: str) -> str:
    method_backend = get_method_backend()
    experimental = method_backend.section_search(question + " experimental workflow", top_k=4, section_type="experimental")
    computational = method_backend.section_search(question + " computational workflow", top_k=3, section_type="computational")
    results = method_backend.section_search(question + " activity results", top_k=2, section_type="results")
    edges = gather_methodology_edges(question, limit=40)
    instrument_evidence = gather_instrument_evidence(question, experimental)
    prompt = PROMPT_TEMPLATE.format(
        question=question,
        experimental_sections=load_sections_for_prompt(experimental),
        computational_sections=load_sections_for_prompt(computational),
        results_sections=load_sections_for_prompt(results),
        parameter_edges="\n".join(
            f"- {edge['metadata']['relation']}: {edge['metadata']['value']} (from {edge['metadata']['paper']})"
            for edge in edges[:20]
        ),
        instrument_evidence="\n".join(
            f"- **{ev['instrument']}** ({ev['relation']}: {ev['value']}) – {ev['sentence']}" for ev in instrument_evidence
        ),
    )
    answer = local_llm.generate(prompt)
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
    out_path = LOG_DIR / f"run_{len(list(LOG_DIR.glob('run_*.json'))):05d}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
