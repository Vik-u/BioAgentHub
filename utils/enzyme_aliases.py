#!/usr/bin/env python3
"""Shared alias utilities for PETase-related retrieval and prompting."""

from __future__ import annotations

from typing import List

ALIAS_PRIORITY = [
    "FAST-PETase",
    "FastPETase",
    "DuraPETase",
    "ThermoPETase",
    "TS-PETase",
    "HotPETase",
    "LC-Cutinase",
    "LCC",
    "ICCG",
    "LCC-ICCG",
    "LC-Cutinase",
]

QUERY_EXPANSIONS = {
    "semi-crystalline": ["FAST-PETase", "DuraPETase", "LC-Cutinase", "LCC-ICCG"],
    "semicrystalline": ["FAST-PETase", "DuraPETase", "LC-Cutinase", "LCC-ICCG"],
    "thermostable": ["ThermoPETase", "DuraPETase", "TS-PETase", "HotPETase"],
    "industrial": ["FAST-PETase", "DuraPETase", "LC-Cutinase", "LCC"],
    "biofilm": ["surface-display", "yeast FAST-PETase"],
    "enzyme comparison": ["FAST-PETase", "DuraPETase", "LCC", "ICCG"],
}

QUESTION_KEYWORDS = {
    "semi-crystalline": ["FAST-PETase", "DuraPETase", "LC-Cutinase"],
    "semicrystalline": ["FAST-PETase", "DuraPETase", "LC-Cutinase"],
    "thermostable": ["ThermoPETase", "DuraPETase", "HotPETase"],
    "stability": ["N233K", "R224Q", "T140D", "S121E"],
    "temperature": ["ThermoPETase", "DuraPETase", "FAST-PETase"],
    "rate": ["N233K", "S121E", "R224Q"],
}


def expand_query(query: str) -> str:
    lower = query.lower()
    extras: List[str] = []
    for key, additions in QUERY_EXPANSIONS.items():
        if key in lower:
            extras.extend(additions)
    if "petase" in lower and "fast" not in lower:
        extras.extend(["IsPETase", "WT PETase", "Combinatorial PETase"])
    if not extras:
        return query
    return query + " " + " ".join(sorted(set(extras)))


def preferred_sources(context_sources: List[str], extra: List[str] | None = None) -> List[str]:
    ordered = []
    for source in context_sources:
        if source and source not in ordered:
            ordered.append(source)
    for source in ALIAS_PRIORITY:
        if source not in ordered:
            ordered.append(source)
    if extra:
        for source in extra:
            if source not in ordered:
                ordered.append(source)
    return ordered


def expected_entities_from_question(question: str) -> List[str]:
    lower = question.lower()
    result: List[str] = []
    for key, vals in QUESTION_KEYWORDS.items():
        if key in lower:
            result.extend(vals)
    if "semi" in lower and "crystal" in lower:
        result.extend(["FAST-PETase", "DuraPETase", "LC-Cutinase"])
    if not result and "petase" in lower:
        result.extend(["FAST-PETase", "ThermoPETase", "DuraPETase"])
    seen = []
    for item in result:
        if item not in seen:
            seen.append(item)
    return seen[:6]
