#!/usr/bin/env python3
"""
LLM-driven hypothesis + planning helpers for the multi-agent flow.

Functions:
- generate_hypotheses: uses timeline/KG summaries + query to propose gaps and hypotheses.
- computational_plan: proposes in-silico steps (MD/stability/mutagenesis).
- experimental_plan: proposes wet-lab steps (assays/instruments).
- arbiter: merges computational/experimental into a concise plan.

These are intentionally lightweight wrappers around local_llm to keep the stack simple.
"""

from __future__ import annotations

from typing import Dict

from services import local_llm


def _llm_or_default(prompt: str, fallback: str) -> str:
    try:
        return local_llm.generate(prompt)
    except Exception:
        return fallback


def generate_hypotheses(query: str, gap_summary: Dict) -> str:
    prompt = (
        "You are a protein engineering research agent. Use the query and the timeline/KG gaps to propose hypotheses.\n"
        f"Query: {query}\n"
        f"Gaps: {gap_summary}\n"
        "Return 3-5 concise hypotheses with rationale and the evidence gaps they address."
    )
    return _llm_or_default(prompt, "Hypotheses not available (LLM offline).")


def computational_plan(query: str) -> str:
    prompt = (
        "Design a computational plan for the protein engineering query below. Include modeling/simulation, stability/activity "
        "prediction, mutagenesis design, and analysis checkpoints.\n"
        f"Query: {query}\n"
        "Return a short, ordered list."
    )
    return _llm_or_default(prompt, "Computational plan not available (LLM offline).")


def experimental_plan(query: str) -> str:
    prompt = (
        "Design an experimental plan for the protein engineering query below. Include constructs, expression, assays, and "
        "instrument notes if relevant.\n"
        f"Query: {query}\n"
        "Return a short, ordered list."
    )
    return _llm_or_default(prompt, "Experimental plan not available (LLM offline).")


def arbiter(hypotheses: str, comp: str, exp: str) -> str:
    prompt = (
        "Merge and reconcile the following hypotheses, computational plan, and experimental plan into a cohesive action plan. "
        "Highlight priority steps and expected outcomes. Keep it concise.\n"
        f"Hypotheses:\n{hypotheses}\n\nComputational:\n{comp}\n\nExperimental:\n{exp}"
    )
    return _llm_or_default(prompt, "Arbiter summary not available (LLM offline).")


if __name__ == "__main__":
    demo = generate_hypotheses("Benchmark FAST-PETase mutations at elevated temp", {"note": "demo"})
    print(demo)
