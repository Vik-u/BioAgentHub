#!/usr/bin/env python3
"""Heuristic KG edge extractor for PETase corpus text files."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List

sentence_splitter = re.compile(r"(?<=[.!?])\s+")
enzyme_pattern = re.compile(r"\b([A-Z][A-Za-z0-9-]{2,}ase)\b")
mutation_pattern = re.compile(r"\b[A-Z]\d{1,4}[A-Z]\b")
temp_pattern = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:°\s?C|ºC|degrees C|\s?°C|\s?C)\b")
ph_pattern = re.compile(r"\bpH\s*(\d+(?:\.\d+)?)")
degradation_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(?:%|percent)\s+(?:degradation|degraded|conversion|hydrolysis)")
time_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(?:h|hours)\b")
substrates = {
    "PET": ["PET", "polyethylene terephthalate"],
    "BHET": ["BHET", "bis(2-hydroxyethyl) terephthalate"],
    "TPA": ["TPA", "terephthalic acid"],
    "MHET": ["MHET", "mono(2-hydroxyethyl) terephthalate"],
}
substrate_patterns = {
    name: [re.compile(re.escape(term), re.IGNORECASE) for term in terms]
    for name, terms in substrates.items()
}
keywords_metrics = {
    "activity": re.compile(r"activity|kinetics|turnover", re.IGNORECASE),
    "stability": re.compile(r"stability|half-life|melting temperature|Tm", re.IGNORECASE),
    "engineering": re.compile(r"mutation|engineer|variant|designed|evolved", re.IGNORECASE),
}


def yield_sentences(text: str) -> Iterable[str]:
    for sentence in sentence_splitter.split(text):
        s = sentence.strip()
        if s:
            yield s


CANONICAL_ENZYMES = {
    "petase": "PETase",
    "ispetase": "IsPETase",
    "wtpetase": "WT-PETase",
    "fastpetase": "FAST-PETase",
    "hotpetase": "HotPETase",
    "durapetase": "DuraPETase",
    "thermopetase": "ThermoPETase",
    "turbopetase": "TurboPETase",
    "tspetase": "TS-PETase",
    "bhpetase": "BhrPETase",
}


def normalize_enzyme(label: str) -> str:
    normalized = "".join(ch for ch in label.lower() if ch.isalnum())
    return CANONICAL_ENZYMES.get(normalized, label.strip())


def compute_confidence(sentence: str, relation: str) -> float:
    score = 0.35
    text = sentence.lower()
    length = len(sentence)
    if 60 <= length <= 400:
        score += 0.2
    elif 30 <= length <= 500:
        score += 0.1
    relation_keywords = {
        "has_mutation": ["mutation", "variant", "substitution"],
        "targets_substrate": ["hydrolysis", "degrade", "substrate"],
        "active_temperature": ["°c", "temperature"],
        "active_pH": ["ph"],
        "achieves_conversion": ["conversion", "degradation", "%"],
        "discusses_metric": ["activity", "stability", "kinetic"],
    }
    for keyword in relation_keywords.get(relation, []):
        if keyword in text:
            score += 0.15
            break
    if relation == "has_mutation" and any(char.isdigit() for char in sentence):
        score += 0.1
    if relation == "targets_substrate" and "pet" in text:
        score += 0.1
    return round(min(score, 0.99), 2)


def add_edge(container: List[dict], edge_set: set, source: str, relation: str, target: str, paper: str, sentence: str) -> None:
    normalized_source = normalize_enzyme(source)
    key = (normalized_source, relation, target, paper)
    if key in edge_set:
        return
    container.append(
        {
            "source": normalized_source,
            "relation": relation,
            "target": target,
            "paper": paper,
            "sentence": sentence[:400],
            "confidence": compute_confidence(sentence, relation),
        }
    )
    edge_set.add(key)


def extract_edges(text_dir: Path, corpus_index: Dict[str, dict]) -> List[dict]:
    edges: List[dict] = []
    edge_set = set()
    for txt_path in sorted(text_dir.glob("*.txt")):
        text = txt_path.read_text(errors="ignore")
        pdf_file = corpus_index.get(txt_path.name, {}).get("pdf_file", f"{txt_path.stem}.pdf")
        for sentence in yield_sentences(text):
            enzymes = {match.group(1) for match in enzyme_pattern.finditer(sentence)}
            if not enzymes:
                continue
            mutations = mutation_pattern.findall(sentence)
            temps = [f"{value} °C" for value in temp_pattern.findall(sentence)]
            phs = [f"pH {value}" for value in ph_pattern.findall(sentence)]
            degr = [f"{value[0]}% degradation" for value in degradation_pattern.findall(sentence)]
            times = time_pattern.findall(sentence)
            for enzyme in enzymes:
                for mutation in mutations:
                    add_edge(edges, edge_set, enzyme, "has_mutation", mutation, pdf_file, sentence)
                for temp in temps:
                    add_edge(edges, edge_set, enzyme, "active_temperature", temp, pdf_file, sentence)
                for ph_value in phs:
                    add_edge(edges, edge_set, enzyme, "active_pH", ph_value, pdf_file, sentence)
                for value in degr:
                    context = value
                    if times:
                        context = f"{context} in {times[0]} h"
                    add_edge(edges, edge_set, enzyme, "achieves_conversion", context, pdf_file, sentence)
                for label, pattern_list in substrate_patterns.items():
                    if any(pattern.search(sentence) for pattern in pattern_list):
                        add_edge(edges, edge_set, enzyme, "targets_substrate", label, pdf_file, sentence)
                for metric_label, pattern in keywords_metrics.items():
                    if pattern.search(sentence):
                        add_edge(edges, edge_set, enzyme, "discusses_metric", metric_label, pdf_file, sentence)
    return edges


def summarize(edges: List[dict]) -> dict:
    relation_counts = Counter(edge["relation"] for edge in edges)
    source_counts = Counter(edge["source"] for edge in edges)
    summary = {
        "edge_count": len(edges),
        "relation_counts": relation_counts.most_common(),
        "top_sources": source_counts.most_common(20),
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--text-dir",
        type=Path,
        default=Path("KnowledgeGraph/text"),
        help="Directory with extracted text files.",
    )
    parser.add_argument(
        "--corpus-index",
        type=Path,
        default=Path("KnowledgeGraph/corpus_index.json"),
        help="Metadata index used to map text back to PDFs.",
    )
    parser.add_argument(
        "--out-edges",
        type=Path,
        default=Path("KnowledgeGraph/kg_edges.jsonl"),
        help="JSONL file for extracted edges.",
    )
    parser.add_argument(
        "--out-summary",
        type=Path,
        default=Path("KnowledgeGraph/graph_overview.json"),
        help="High-level summary JSON path.",
    )
    args = parser.parse_args()

    if not args.text_dir.exists():
        raise SystemExit(f"Text dir not found: {args.text_dir}")

    corpus_index = {entry["txt_file"]: entry for entry in json.loads(args.corpus_index.read_text())}
    edges = extract_edges(args.text_dir, corpus_index)

    with args.out_edges.open("w", encoding="utf-8") as handle:
        for edge in edges:
            handle.write(json.dumps(edge, ensure_ascii=False) + "\n")

    args.out_summary.write_text(json.dumps(summarize(edges), indent=2))
    print(f"Wrote {len(edges)} edges to {args.out_edges}")


if __name__ == "__main__":
    main()
