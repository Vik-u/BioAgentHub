#!/usr/bin/env python3
"""Protocol agent that constrains steps to the available instruments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from langchain_core.prompts import PromptTemplate

from services import local_llm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = PROJECT_ROOT / "InstrumentGraph" / "inventory.json"


@dataclass
class Instrument:
    name: str
    category: str
    capabilities: Sequence[str]
    use_cases: Sequence[str]


def load_inventory() -> List[Instrument]:
    if not INVENTORY_PATH.exists():
        return []
    data = json.loads(INVENTORY_PATH.read_text())
    instruments: List[Instrument] = []
    for entry in data:
        instruments.append(
            Instrument(
                name=entry["name"],
                category=entry.get("category", "unspecified"),
                capabilities=entry.get("capabilities", []),
                use_cases=entry.get("use_cases", []),
            )
        )
    return instruments


def score_instrument(question: str, instrument: Instrument) -> int:
    text = question.lower()
    score = 0
    for token in instrument.name.lower().split():
        if token and token in text:
            score += 2
    for snippet in instrument.use_cases:
        if any(word in text for word in snippet.lower().split()):
            score += 1
    if "thermo" in instrument.name.lower() and "temperature" in text:
        score += 1
    if "enz" in text and instrument.category in {"Automated incubator", "Automated liquid handler", "Mass spectrometer"}:
        score += 1
    return score


def select_instruments(question: str, inventory: Sequence[Instrument], top_n: int = 8) -> List[Instrument]:
    if not inventory:
        return []
    scored = [
        (score_instrument(question, instrument), instrument)
        for instrument in inventory
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    selected = [item for score, item in scored if score > 0][:top_n]
    if not selected:
        selected = list(inventory[:top_n])
    return selected


def format_inventory(instruments: Sequence[Instrument]) -> str:
    lines = []
    for idx, instrument in enumerate(instruments, start=1):
        caps = "; ".join(instrument.capabilities[:3])
        uses = ", ".join(instrument.use_cases[:3])
        lines.append(
            f"{idx}. **{instrument.name}** ({instrument.category}) – Capabilities: {caps}. Typical uses: {uses or 'n/a'}."
        )
    return "\n".join(lines)


PROMPT = PromptTemplate(
    input_variables=["question", "inventory"],
    template=(
        "You are drafting a PETase research protocol that MUST use only the instruments listed below.\n"
        "Question: {question}\n\n"
        "Available instruments:\n"
        "{inventory}\n\n"
        "Write Markdown with two sections in this order:\n"
        "## Experimental Workflow (reference instruments per step; state plate formats, incubators, dispensers, etc.)\n"
        "## Computational Workflow (mention computation + any analytical instruments for validation)\n"
        "Each step should include: Action, key parameters, and why the chosen instrument is appropriate."
    ),
)


def run_instrument_protocol(question: str, top_n: int = 8) -> str:
    inventory = load_inventory()
    selected = select_instruments(question, inventory, top_n=top_n)
    summary = format_inventory(selected)
    prompt = PROMPT.format(question=question, inventory=summary or "No instruments available.")
    return local_llm.generate(prompt)
