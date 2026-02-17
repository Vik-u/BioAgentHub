#!/usr/bin/env python3
"""Heuristic KG edge extractor for topic-agnostic corpus text files."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

sentence_splitter = re.compile(r"(?<=[.!?])\s+")
enzyme_pattern = re.compile(r"\b([A-Za-z][A-Za-z0-9-]{2,}ase)\b", re.IGNORECASE)
protein_pattern = re.compile(r"\b([A-Za-z0-9-]{3,}\s+protein)\b", re.IGNORECASE)
mutation_pattern = re.compile(r"\b[A-Z]\d{1,4}[A-Z]\b")
temp_pattern = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:°\s?C|ºC|degC|degrees C|\s?°C|\s?C)\b", re.IGNORECASE)
ph_pattern = re.compile(r"\bpH\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
degradation_pattern = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:%|percent)\s+(?:degradation|degraded|conversion|hydrolysis)",
    re.IGNORECASE,
)
time_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(h|hr|hrs|hours|min|mins|minutes|days)\b", re.IGNORECASE)

ENTITY_STOPWORDS = {
    "protein",
    "proteins",
    "enzyme",
    "enzymes",
    "gene",
    "genes",
    "strain",
    "organism",
    "increase",
    "decrease",
    "activity",
    "stability",
    "result",
}

STRUCTURED_RELATIONS = {
    "has_mutation",
    "active_temperature",
    "active_pH",
    "achieves_conversion",
    "targets_substrate",
    "discusses_metric",
}

DEFAULT_SCHEMA: Dict[str, object] = {
    "topic": "",
    "focus_query": "",
    "key_entities": [],
    "entity_aliases": {},
    "substrates": [],
    "metrics": [
        "activity",
        "stability",
        "kinetics",
        "yield",
        "conversion",
        "selectivity",
        "expression",
        "thermostability",
        "specificity",
    ],
    "hosts": [
        "E. coli",
        "Escherichia coli",
        "Saccharomyces cerevisiae",
        "Bacillus subtilis",
        "Pseudomonas",
        "Corynebacterium",
        "yeast",
    ],
    "assays": [
        "HPLC",
        "GC",
        "MS",
        "LC-MS",
        "SDS-PAGE",
        "fluorescence",
        "absorbance",
        "colorimetric",
    ],
    "relation_keywords": {
        "has_mutation": ["mutation", "mutant", "variant", "substitution", "engineered"],
        "active_temperature": ["temperature", "degrees", "thermostable", "Tm"],
        "active_pH": ["pH"],
        "achieves_conversion": ["conversion", "degradation", "hydrolysis", "yield"],
        "targets_substrate": ["substrate", "hydrolysis", "degrade", "target"],
        "discusses_metric": ["activity", "stability", "kinetic", "turnover", "selectivity", "yield"],
        "expressed_in": ["expressed in", "host", "strain", "expression in"],
        "assayed_with": ["assay", "HPLC", "GC", "MS", "SDS-PAGE", "fluorescence", "absorbance"],
    },
}


def yield_sentences(text: str) -> Iterable[str]:
    for sentence in sentence_splitter.split(text):
        s = sentence.strip()
        if s:
            yield s


def normalize_entity(label: str) -> str:
    cleaned = re.sub(r"\s+", " ", label.strip())
    return cleaned.strip(" ,;:.()")


def deep_copy_schema(schema: Dict[str, object]) -> Dict[str, object]:
    return json.loads(json.dumps(schema))


def load_schema(schema_path: Path | None, workspace: Path | None) -> Dict[str, object]:
    if schema_path and schema_path.exists():
        return json.loads(schema_path.read_text())
    if workspace:
        candidate = workspace / "kg_schema.json"
        if candidate.exists():
            return json.loads(candidate.read_text())
    return deep_copy_schema(DEFAULT_SCHEMA)


def build_alias_lookup(schema: Dict[str, object]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    entity_aliases = schema.get("entity_aliases") or {}
    if isinstance(entity_aliases, dict):
        for canonical, aliases in entity_aliases.items():
            if not canonical:
                continue
            canonical_norm = normalize_entity(str(canonical))
            lookup[canonical_norm.lower()] = canonical_norm
            for alias in aliases or []:
                alias_text = normalize_entity(str(alias))
                if alias_text:
                    lookup[alias_text.lower()] = canonical_norm
    key_entities = schema.get("key_entities") or []
    for entity in key_entities:
        entity_text = normalize_entity(str(entity))
        if entity_text:
            lookup[entity_text.lower()] = entity_text
    return lookup


def extract_sources(sentence: str, alias_lookup: Dict[str, str]) -> List[str]:
    lowered = sentence.lower()
    sources = set()
    for alias, canonical in alias_lookup.items():
        if alias and alias in lowered:
            sources.add(canonical)
    for pattern in (enzyme_pattern, protein_pattern):
        for match in pattern.finditer(sentence):
            label = normalize_entity(match.group(1))
            if not label or label.lower() in ENTITY_STOPWORDS:
                continue
            if label.islower() and len(label) <= 4:
                continue
            sources.add(label)
    return sorted(sources)


def match_terms(sentence: str, terms: Sequence[str]) -> List[str]:
    if not terms:
        return []
    lowered = sentence.lower()
    matched = []
    for term in terms:
        if not term:
            continue
        if term.lower() in lowered:
            matched.append(term)
    return matched


def compute_confidence(sentence: str, relation: str, relation_keywords: Dict[str, Sequence[str]]) -> float:
    score = 0.35
    text = sentence.lower()
    length = len(sentence)
    if 60 <= length <= 400:
        score += 0.2
    elif 30 <= length <= 500:
        score += 0.1
    for keyword in relation_keywords.get(relation, []):
        if keyword.lower() in text:
            score += 0.15
            break
    if relation == "has_mutation" and any(char.isdigit() for char in sentence):
        score += 0.1
    if relation == "targets_substrate" and ("substrate" in text or "degrad" in text):
        score += 0.05
    return round(min(score, 0.99), 2)


def add_edge(
    container: List[dict],
    edge_set: set,
    source: str,
    relation: str,
    target: str,
    paper: str,
    sentence: str,
    relation_keywords: Dict[str, Sequence[str]],
) -> None:
    source_norm = normalize_entity(source)
    target_norm = normalize_entity(target)
    key = (source_norm, relation, target_norm, paper)
    if key in edge_set:
        return
    container.append(
        {
            "source": source_norm,
            "relation": relation,
            "target": target_norm,
            "paper": paper,
            "sentence": sentence[:400],
            "confidence": compute_confidence(sentence, relation, relation_keywords),
        }
    )
    edge_set.add(key)


def extract_edges(text_dir: Path, corpus_index: Dict[str, dict], schema: Dict[str, object]) -> List[dict]:
    edges: List[dict] = []
    edge_set = set()
    alias_lookup = build_alias_lookup(schema)
    substrates = schema.get("substrates") or []
    metrics = schema.get("metrics") or []
    hosts = schema.get("hosts") or []
    assays = schema.get("assays") or []
    relation_keywords = schema.get("relation_keywords") or {}

    for txt_path in sorted(text_dir.glob("*.txt")):
        text = txt_path.read_text(errors="ignore")
        pdf_file = corpus_index.get(txt_path.name, {}).get("pdf_file", f"{txt_path.stem}.pdf")
        for sentence in yield_sentences(text):
            sources = extract_sources(sentence, alias_lookup)
            if not sources:
                continue

            mutations = mutation_pattern.findall(sentence)
            temps = [f"{value} °C" for value in temp_pattern.findall(sentence)]
            phs = [f"pH {value}" for value in ph_pattern.findall(sentence)]
            degr = [f"{value}% degradation" for value in degradation_pattern.findall(sentence)]
            times = [f"{value} {unit}" for value, unit in time_pattern.findall(sentence)]
            matched_substrates = match_terms(sentence, substrates)
            matched_metrics = match_terms(sentence, metrics)
            matched_hosts = match_terms(sentence, hosts)
            matched_assays = match_terms(sentence, assays)

            for source in sources:
                for mutation in mutations:
                    add_edge(edges, edge_set, source, "has_mutation", mutation, pdf_file, sentence, relation_keywords)
                for temp in temps:
                    add_edge(edges, edge_set, source, "active_temperature", temp, pdf_file, sentence, relation_keywords)
                for ph_value in phs:
                    add_edge(edges, edge_set, source, "active_pH", ph_value, pdf_file, sentence, relation_keywords)
                for value in degr:
                    context = value
                    if times:
                        context = f"{context} in {times[0]}"
                    add_edge(edges, edge_set, source, "achieves_conversion", context, pdf_file, sentence, relation_keywords)
                for substrate in matched_substrates:
                    add_edge(edges, edge_set, source, "targets_substrate", substrate, pdf_file, sentence, relation_keywords)
                for metric_label in matched_metrics:
                    add_edge(edges, edge_set, source, "discusses_metric", metric_label, pdf_file, sentence, relation_keywords)
                for host in matched_hosts:
                    add_edge(edges, edge_set, source, "expressed_in", host, pdf_file, sentence, relation_keywords)
                for assay in matched_assays:
                    add_edge(edges, edge_set, source, "assayed_with", assay, pdf_file, sentence, relation_keywords)

                # Generic relation keyword matches for any remaining relations.
                lowered = sentence.lower()
                for relation, keywords in relation_keywords.items():
                    if relation in STRUCTURED_RELATIONS:
                        continue
                    for keyword in keywords:
                        if keyword.lower() in lowered:
                            add_edge(edges, edge_set, source, relation, keyword, pdf_file, sentence, relation_keywords)
                            break

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
        "--workspace",
        type=Path,
        help="Workspace root (overrides individual paths: text-dir, corpus-index, out-edges, out-summary).",
    )
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
    parser.add_argument("--schema", type=Path, help="Optional schema JSON file (defaults to <workspace>/kg_schema.json).")
    parser.add_argument(
        "--focus-keywords",
        nargs="*",
        default=["mutation", "stability", "activity", "directed evolution", "assay", "temperature", "folding"],
        help="Boost extraction around these protein-engineering terms (used for confidence).",
    )
    args = parser.parse_args()

    # If a workspace is provided, derive defaults from it unless explicitly overridden.
    if args.workspace:
        base = args.workspace
        args.text_dir = base / "text"
        args.corpus_index = base / "corpus_index.json"
        args.out_edges = base / "kg_edges.jsonl"
        args.out_summary = base / "graph_overview.json"

    if not args.text_dir.exists():
        raise SystemExit(f"Text dir not found: {args.text_dir}")

    schema = load_schema(args.schema, args.workspace)
    corpus_index = {entry["txt_file"]: entry for entry in json.loads(args.corpus_index.read_text())}
    edges = extract_edges(args.text_dir, corpus_index, schema)

    # Post-boost edges that touch focus keywords in the sentence to favor protein-engineering context.
    focus_patterns = [re.compile(re.escape(term), re.IGNORECASE) for term in args.focus_keywords]
    relation_keywords = schema.get("relation_keywords") or {}
    for edge in edges:
        sentence = edge.get("sentence", "")
        if any(p.search(sentence) for p in focus_patterns):
            edge["confidence"] = min(0.99, round(edge.get("confidence", 0.0) + 0.1, 2))
        # Slightly boost edges that match relation keywords.
        for keyword in relation_keywords.get(edge["relation"], []):
            if keyword.lower() in sentence.lower():
                edge["confidence"] = min(0.99, round(edge.get("confidence", 0.0) + 0.05, 2))
                break

    with args.out_edges.open("w", encoding="utf-8") as handle:
        for edge in edges:
            handle.write(json.dumps(edge, ensure_ascii=False) + "\n")

    args.out_summary.write_text(json.dumps(summarize(edges), indent=2))
    print(f"Wrote {len(edges)} edges to {args.out_edges}")


if __name__ == "__main__":
    main()
