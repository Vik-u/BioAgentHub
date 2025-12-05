#!/usr/bin/env python3
"""Heuristic knowledge graph builder for instrument manuals."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
PLATE_PATTERN = re.compile(r"(6|12|24|48|96|384|1536)[-\s]*(?:well|wellplates|well\s*plates)", re.I)
TEMP_PATTERN = re.compile(r"(-?\d+\.?\d?)\s*(?:°\s?C|ºC|degC|degrees?\s*C)", re.I)
TEMP_RANGE_PATTERN = re.compile(r"(-?\d+\.?\d?)\s*(?:°\s?C|ºC|degC)?\s*(?:to|-|–)\s*(-?\d+\.?\d?)\s*(?:°\s?C|ºC|degC)", re.I)
VOLUME_PATTERN = re.compile(r"(\d+\.?\d*)\s*(nL|µL|uL|mL|L)\b")
SPEED_PATTERN = re.compile(r"(\d+\.?\d*)\s*(rpm|×\s?g|xg|g-force)", re.I)
THROUGHPUT_PATTERN = re.compile(r"(\d{2,5})\s*(?:plates|samples|wells)\s*(?:per|/)\s*(?:hour|hr|min)", re.I)
USE_CASE_KEYWORDS = {
    "dispensing": ["dispense", "filling", "reagent", "distribution"],
    "incubation": ["incubator", "incubation", "temperature control"],
    "sealing": ["seal", "sealing", "foil"],
    "labeling": ["label", "barcode"],
    "imaging": ["imaging", "camera", "fluorescence"],
    "screening": ["screening", "assay", "high-throughput"],
    "purification": ["purification", "magnetic beads", "bind-wash-elute"],
    "analysis": ["qPCR", "PCR", "fluorescence read", "spectrometer", "mass spectrometer"],
}


def yield_sentences(text: str) -> Iterable[str]:
    for sentence in SENTENCE_SPLIT.split(text):
        s = sentence.strip()
        if s:
            yield s


def infer_instrument_name(meta_entry: dict) -> str:
    pdf_file = meta_entry.get("pdf_file", "")
    if pdf_file:
        parts = Path(pdf_file).parts
        if parts:
            return parts[0]
    title = meta_entry.get("title_candidate")
    if title:
        return title[:80]
    return Path(meta_entry.get("txt_file", "instrument")).stem


def build_edges(text_dir: Path, corpus_index: List[dict]) -> List[dict]:
    edges: List[dict] = []
    for entry in corpus_index:
        txt_path = text_dir / entry["txt_file"]
        if not txt_path.exists():
            continue
        instrument = infer_instrument_name(entry)
        text = txt_path.read_text(errors="ignore")
        for sentence in yield_sentences(text):
            add_edges_from_sentence(edges, instrument, sentence, entry["pdf_file"])
    return edges


def add_edges_from_sentence(container: List[dict], instrument: str, sentence: str, pdf_file: str) -> None:
    def push(relation: str, value: str):
        container.append(
            {
                "instrument": instrument,
                "relation": relation,
                "value": value.strip(),
                "sentence": sentence[:500],
                "pdf_file": pdf_file,
            }
        )

    for match in TEMP_RANGE_PATTERN.finditer(sentence):
        push("temperature_range", f"{match.group(1)} °C to {match.group(2)} °C")
    for match in TEMP_PATTERN.finditer(sentence):
        push("temperature", f"{match.group(1)} °C")
    for match in PLATE_PATTERN.finditer(sentence):
        push("supports_plate", match.group(0))
    for match in VOLUME_PATTERN.finditer(sentence):
        push("volume", f"{match.group(1)} {match.group(2)}")
    for match in SPEED_PATTERN.finditer(sentence):
        push("speed", match.group(0))
    for match in THROUGHPUT_PATTERN.finditer(sentence):
        push("throughput", match.group(0))
    lowered = sentence.lower()
    for label, keywords in USE_CASE_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            push("use_case", label)


def summarize(edges: List[dict]) -> dict:
    summary: Dict[str, int] = {}
    for edge in edges:
        relation = edge["relation"]
        summary[relation] = summary.get(relation, 0) + 1
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text-dir", type=Path, default=Path("InstrumentGraph/text"))
    parser.add_argument("--corpus-index", type=Path, default=Path("InstrumentGraph/corpus_index.json"))
    parser.add_argument("--out-edges", type=Path, default=Path("InstrumentGraph/kg_edges.jsonl"))
    parser.add_argument("--summary", type=Path, default=Path("InstrumentGraph/kg_summary.json"))
    args = parser.parse_args()

    if not args.text_dir.exists():
        raise SystemExit(f"Text dir not found: {args.text_dir}")
    corpus_index = json.loads(args.corpus_index.read_text())
    edges = build_edges(args.text_dir, corpus_index)
    with args.out_edges.open("w", encoding="utf-8") as handle:
        for edge in edges:
            handle.write(json.dumps(edge, ensure_ascii=False) + "\n")
    args.summary.write_text(json.dumps(summarize(edges), indent=2))
    print(f"Wrote {len(edges)} edges to {args.out_edges}")


if __name__ == "__main__":
    main()
