#!/usr/bin/env python3
"""Construct a heuristically extracted KG from methodology sections."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
TEMP_PATTERN = re.compile(r"(-?\d+\.?\d*)\s*(?:°\s?C|ºC|degC|degrees?\s*C)", re.I)
TEMP_RANGE_PATTERN = re.compile(r"(-?\d+\.?\d*)\s*(?:°\s?C|ºC|degC)?\s*(?:to|-|–)\s*(-?\d+\.?\d*)\s*(?:°\s?C|ºC|degC)", re.I)
TIME_PATTERN = re.compile(r"(\d+\.?\d*)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?|days?)", re.I)
PH_PATTERN = re.compile(r"\bpH\s*(\d+\.?\d*)", re.I)
VOLUME_PATTERN = re.compile(r"(\d+\.?\d*)\s*(nL|µL|uL|mL|L)\b", re.I)
CONC_PATTERN = re.compile(r"(\d+\.?\d*)\s*(µ?M|mM|nM|mg/mL|%|wt%|v/v)", re.I)
SPEED_PATTERN = re.compile(r"(\d+\.?\d*)\s*(rpm|×\s?g|xg)", re.I)
ACTION_KEYWORDS = ["incubate", "centrifuge", "mix", "add", "purify", "wash", "lyse", "express", "induce"]
OUTCOME_KEYWORDS = ["increase", "improve", "decrease", "yield", "activity", "stability", "thermostability", "conversion", "degradation"]


def yield_sentences(text: str) -> Iterable[str]:
    for sentence in SENTENCE_SPLIT.split(text):
        s = sentence.strip()
        if s:
            yield s


def categorize_relation(sentence: str) -> List[Dict[str, str]]:
    relations = []
    for match in TEMP_RANGE_PATTERN.finditer(sentence):
        relations.append({"relation": "temperature_range", "value": f"{match.group(1)} °C to {match.group(2)} °C"})
    for match in TEMP_PATTERN.finditer(sentence):
        relations.append({"relation": "temperature", "value": f"{match.group(1)} °C"})
    for match in TIME_PATTERN.finditer(sentence):
        relations.append({"relation": "duration", "value": match.group(0)})
    for match in PH_PATTERN.finditer(sentence):
        relations.append({"relation": "pH", "value": f"pH {match.group(1)}"})
    for match in VOLUME_PATTERN.finditer(sentence):
        relations.append({"relation": "volume", "value": f"{match.group(1)} {match.group(2)}"})
    for match in CONC_PATTERN.finditer(sentence):
        relations.append({"relation": "concentration", "value": match.group(0)})
    for match in SPEED_PATTERN.finditer(sentence):
        relations.append({"relation": "speed", "value": match.group(0)})
    lowered = sentence.lower()
    if any(keyword in lowered for keyword in ACTION_KEYWORDS):
        relations.append({"relation": "action", "value": sentence.strip()[:400]})
    if any(keyword in lowered for keyword in OUTCOME_KEYWORDS):
        relations.append({"relation": "outcome", "value": sentence.strip()[:400]})
    return relations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method-dir", type=Path, default=Path("KnowledgeGraph/methodology_full"))
    parser.add_argument("--out-edges", type=Path, default=Path("KnowledgeGraph/methodology_kg_edges.jsonl"))
    parser.add_argument("--summary", type=Path, default=Path("KnowledgeGraph/methodology_kg_summary.json"))
    args = parser.parse_args()

    edges: List[dict] = []
    for json_path in sorted(args.method_dir.glob("*.json")):
        data = json.loads(json_path.read_text())
        pdf = data.get("pdf_file")
        paper = data.get("title") or pdf or json_path.stem
        for section_type in ("experimental_sections", "computational_sections", "results_sections"):
            for section in data.get(section_type, []):
                heading = section.get("heading", section_type)
                for sentence in yield_sentences(section.get("text", "")):
                    for rel in categorize_relation(sentence):
                        edges.append(
                            {
                                "paper": paper,
                                "pdf_file": pdf,
                                "section_type": section_type.replace("_sections", ""),
                                "heading": heading,
                                "relation": rel["relation"],
                                "value": rel["value"],
                                "sentence": sentence[:500],
                            }
                        )
    args.out_edges.write_text("\n".join(json.dumps(edge, ensure_ascii=False) for edge in edges))
    summary: Dict[str, int] = {}
    for edge in edges:
        summary[edge["relation"]] = summary.get(edge["relation"], 0) + 1
    args.summary.write_text(json.dumps(summary, indent=2))
    print(f"Wrote {len(edges)} methodology edges to {args.out_edges}")


if __name__ == "__main__":
    main()
