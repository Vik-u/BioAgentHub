#!/usr/bin/env python3
"""Build structured facts from text, captions, and tables with normalization."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from forge.utils.kg_schema_utils import build_alias_lookup, load_schema  # noqa: E402


SENTENCE_SPLITTER = re.compile(r"(?<=[.!?])\s+")
ENZYME_PATTERN = re.compile(r"\b([A-Za-z][A-Za-z0-9-]{2,}ase)\b", re.IGNORECASE)
PROTEIN_PATTERN = re.compile(r"\b([A-Za-z0-9-]{3,}\s+protein)\b", re.IGNORECASE)
MUTATION_PATTERN = re.compile(r"\b[A-Z]\d{1,4}[A-Z]\b")

TEMP_C_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:°\s?C|ºC|degC|degrees C|\s?°C|\s?C)\b", re.IGNORECASE)
TEMP_F_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s*°?\s*F\b", re.IGNORECASE)
TEMP_K_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s*K\b", re.IGNORECASE)
PH_PATTERN = re.compile(r"\bpH\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
PERCENT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:%|percent)\b", re.IGNORECASE)
TIME_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(s|sec|secs|seconds|min|mins|minutes|h|hr|hrs|hours|day|days)\b", re.IGNORECASE)
CONC_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(mM|uM|nM|M|mol/L|mmol/L|umol/L|nmol/L|mg/mL|ug/mL|g/L)\b",
    re.IGNORECASE,
)
KCAT_PATTERN = re.compile(r"kcat\s*[=:\s]\s*([0-9.eE+-]+)\s*([^\s,;)]+)?", re.IGNORECASE)
KM_PATTERN = re.compile(r"\bK[_\- ]?m\s*[=:\s]\s*([0-9.eE+-]+)\s*([^\s,;)]+)?", re.IGNORECASE)
KCAT_KM_PATTERN = re.compile(r"kcat\s*/\s*k[_\- ]?m\s*[=:\s]\s*([0-9.eE+-]+)\s*([^\s,;)]+)?", re.IGNORECASE)


RELATION_TYPES = {
    "has_mutation",
    "active_temperature",
    "active_ph",
    "achieves_conversion",
    "has_activity",
    "has_yield",
    "has_kcat",
    "has_km",
    "has_kcat_km",
    "has_time",
    "has_concentration",
    "has_stability",
    "targets_substrate",
    "expressed_in",
    "assayed_with",
    "discusses_metric",
}


HEADER_RELATION_MAP = {
    "activity": "has_activity",
    "specific activity": "has_activity",
    "yield": "has_yield",
    "conversion": "achieves_conversion",
    "degradation": "achieves_conversion",
    "kcat": "has_kcat",
    "km": "has_km",
    "kcat/km": "has_kcat_km",
    "kcat k m": "has_kcat_km",
    "temperature": "active_temperature",
    "temp": "active_temperature",
    "ph": "active_ph",
    "time": "has_time",
    "half-life": "has_stability",
    "t1/2": "has_stability",
}


def normalize_entity(raw: str) -> str:
    return re.sub(r"\s+", " ", raw.strip()).strip(" ,;:.()")


def canonicalize_entity(raw: str, alias_lookup: Dict[str, str]) -> str:
    cleaned = normalize_entity(raw)
    if not cleaned:
        return cleaned
    return alias_lookup.get(cleaned.lower(), cleaned)


def infer_alias_lookup(text_dir: Path) -> Dict[str, str]:
    alias_lookup: Dict[str, str] = {}
    candidates = set()
    for txt_path in sorted(text_dir.glob("*.txt"))[:8]:
        text = txt_path.read_text(errors="ignore")
        for match in ENZYME_PATTERN.finditer(text):
            candidates.add(normalize_entity(match.group(1)))
        for match in PROTEIN_PATTERN.finditer(text):
            candidates.add(normalize_entity(match.group(1)))
    for candidate in candidates:
        canonical = candidate
        if not canonical:
            continue
        alias_lookup[canonical.lower()] = canonical
        compact = re.sub(r"[\s\-]+", "", canonical).lower()
        if compact:
            alias_lookup[compact] = canonical
    return alias_lookup


def iter_sentences(text: str) -> Iterable[str]:
    for sentence in SENTENCE_SPLITTER.split(text):
        stripped = sentence.strip()
        if stripped:
            yield stripped


def extract_sources(sentence: str, alias_lookup: Dict[str, str]) -> List[str]:
    sources = []
    lowered = sentence.lower()
    for alias, canonical in alias_lookup.items():
        if alias and alias in lowered:
            sources.append(canonical)
    for pattern in (ENZYME_PATTERN, PROTEIN_PATTERN):
        for match in pattern.finditer(sentence):
            sources.append(normalize_entity(match.group(1)))
    seen = set()
    ordered = []
    for source in sources:
        if not source or source.lower() in seen:
            continue
        seen.add(source.lower())
        ordered.append(source)
    return ordered


def parse_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def normalize_temperature(value: float, unit: str) -> Tuple[Optional[float], Optional[str]]:
    unit_lower = unit.lower()
    if unit_lower in {"c", "°c", "degc"}:
        return value, "C"
    if unit_lower in {"k"}:
        return value - 273.15, "C"
    if unit_lower in {"f", "°f"}:
        return (value - 32.0) * (5.0 / 9.0), "C"
    return value, unit


def normalize_time(value: float, unit: str) -> Tuple[Optional[float], Optional[str]]:
    unit_lower = unit.lower()
    if unit_lower in {"s", "sec", "secs", "seconds"}:
        return value / 60.0, "min"
    if unit_lower in {"min", "mins", "minutes"}:
        return value, "min"
    if unit_lower in {"h", "hr", "hrs", "hours"}:
        return value * 60.0, "min"
    if unit_lower in {"day", "days"}:
        return value * 24.0 * 60.0, "min"
    return value, unit


def normalize_concentration(value: float, unit: str) -> Tuple[Optional[float], Optional[str]]:
    unit_lower = unit.lower()
    if unit_lower in {"m", "mol/l"}:
        return value, "M"
    if unit_lower in {"mm", "mmol/l", "mm"}:
        return value / 1000.0, "M"
    if unit_lower in {"um", "umol/l"}:
        return value / 1_000_000.0, "M"
    if unit_lower in {"nm", "nmol/l"}:
        return value / 1_000_000_000.0, "M"
    return value, unit


def normalize_numeric_value(raw: str, relation_type: str) -> Tuple[Optional[float], Optional[str]]:
    text = raw.strip()
    if relation_type == "active_temperature":
        match = TEMP_C_PATTERN.search(text) or TEMP_F_PATTERN.search(text) or TEMP_K_PATTERN.search(text)
        if match:
            value = parse_float(match.group(1))
            if value is None:
                return None, None
            unit = "C"
            if TEMP_F_PATTERN.search(text):
                unit = "F"
            if TEMP_K_PATTERN.search(text):
                unit = "K"
            return normalize_temperature(value, unit)
    if relation_type == "active_ph":
        match = PH_PATTERN.search(text)
        if match:
            return parse_float(match.group(1)), "pH"
    if relation_type == "achieves_conversion":
        match = PERCENT_PATTERN.search(text)
        if match:
            return parse_float(match.group(1)), "%"
    if relation_type == "has_time":
        match = TIME_PATTERN.search(text)
        if match:
            value = parse_float(match.group(1))
            if value is None:
                return None, None
            return normalize_time(value, match.group(2))
    if relation_type == "has_concentration":
        match = CONC_PATTERN.search(text)
        if match:
            value = parse_float(match.group(1))
            if value is None:
                return None, None
            return normalize_concentration(value, match.group(2))
    for pattern, rel in (
        (KCAT_KM_PATTERN, "has_kcat_km"),
        (KCAT_PATTERN, "has_kcat"),
        (KM_PATTERN, "has_km"),
    ):
        if relation_type != rel:
            continue
        match = pattern.search(text)
        if match:
            value = parse_float(match.group(1))
            unit = match.group(2) if match.group(2) else None
            return value, unit
    if relation_type in {"has_activity", "has_yield", "has_stability"}:
        match = PERCENT_PATTERN.search(text)
        if match:
            return parse_float(match.group(1)), "%"
    return None, None


def build_fact(
    facts: List[dict],
    head_raw: str,
    relation_type: str,
    tail_raw: str,
    evidence_text: str,
    provenance: Dict[str, object],
    alias_lookup: Dict[str, str],
    confidence: float,
) -> None:
    if relation_type not in RELATION_TYPES:
        return
    head_norm = canonicalize_entity(head_raw, alias_lookup)
    tail_norm = canonicalize_entity(tail_raw, alias_lookup)
    normalized_value, normalized_unit = normalize_numeric_value(tail_raw, relation_type)
    if normalized_value is not None:
        tail_norm = f"{normalized_value} {normalized_unit}".strip() if normalized_unit else str(normalized_value)
    fact = {
        "head": {"raw": head_raw, "norm": head_norm},
        "relation_type": relation_type,
        "tail": {"raw": tail_raw, "norm": tail_norm},
        "raw_value": tail_raw if normalized_value is not None else None,
        "normalized_value": normalized_value,
        "normalized_unit": normalized_unit,
        "evidence_text": evidence_text[:500],
        "provenance": provenance,
        "confidence": round(min(confidence, 0.99), 2),
    }
    facts.append(fact)


def match_header_relation(header: str) -> Optional[str]:
    clean = re.sub(r"[^a-z0-9/ ]", "", header.lower()).strip()
    for key, relation in HEADER_RELATION_MAP.items():
        if key in clean:
            return relation
    return None


def extract_table_facts(
    table: dict,
    alias_lookup: Dict[str, str],
    topic: str,
) -> List[dict]:
    rows = table.get("rows") or []
    if not rows:
        return []
    header_row = rows[0]
    header_relations = [match_header_relation(str(cell or "")) for cell in header_row]
    facts: List[dict] = []
    for row_idx, row in enumerate(rows[1:], start=1):
        cells = [str(cell or "").strip() for cell in row]
        if not any(cells):
            continue
        head_raw = ""
        for cell in cells:
            if ENZYME_PATTERN.search(cell) or PROTEIN_PATTERN.search(cell):
                head_raw = cell
                break
        if not head_raw:
            head_raw = cells[0]
        if not head_raw:
            continue
        for col_idx, cell in enumerate(cells):
            relation_type = header_relations[col_idx] if col_idx < len(header_relations) else None
            if not relation_type:
                continue
            if not cell:
                continue
            provenance = {
                "source": "table",
                "pdf": table.get("pdf_file"),
                "page": table.get("page"),
                "bbox": table.get("bbox"),
                "table_id": table.get("table_id"),
                "row": row_idx,
                "column": header_row[col_idx] if col_idx < len(header_row) else None,
                "topic": topic,
            }
            build_fact(
                facts,
                head_raw=head_raw,
                relation_type=relation_type,
                tail_raw=cell,
                evidence_text=f"{header_row[col_idx]}: {cell}",
                provenance=provenance,
                alias_lookup=alias_lookup,
                confidence=0.75,
            )
    return facts


def extract_text_facts(
    text: str,
    alias_lookup: Dict[str, str],
    schema: Dict[str, object],
    provenance_base: Dict[str, object],
    confidence_base: float,
) -> List[dict]:
    facts: List[dict] = []
    substrates = schema.get("substrates") or []
    metrics = schema.get("metrics") or []
    hosts = schema.get("hosts") or []
    assays = schema.get("assays") or []
    for sentence in iter_sentences(text):
        sources = extract_sources(sentence, alias_lookup)
        if not sources:
            continue
        for source in sources:
            for mutation in MUTATION_PATTERN.findall(sentence):
                build_fact(
                    facts,
                    source,
                    "has_mutation",
                    mutation,
                    sentence,
                    provenance_base,
                    alias_lookup,
                    confidence_base,
                )
            for temp_match in TEMP_C_PATTERN.findall(sentence):
                build_fact(
                    facts,
                    source,
                    "active_temperature",
                    f"{temp_match} C",
                    sentence,
                    provenance_base,
                    alias_lookup,
                    confidence_base,
                )
            for temp_match in TEMP_F_PATTERN.findall(sentence):
                build_fact(
                    facts,
                    source,
                    "active_temperature",
                    f"{temp_match} F",
                    sentence,
                    provenance_base,
                    alias_lookup,
                    confidence_base,
                )
            for temp_match in TEMP_K_PATTERN.findall(sentence):
                build_fact(
                    facts,
                    source,
                    "active_temperature",
                    f"{temp_match} K",
                    sentence,
                    provenance_base,
                    alias_lookup,
                    confidence_base,
                )
            for ph_match in PH_PATTERN.findall(sentence):
                build_fact(
                    facts,
                    source,
                    "active_ph",
                    f"pH {ph_match}",
                    sentence,
                    provenance_base,
                    alias_lookup,
                    confidence_base,
                )
            for percent in PERCENT_PATTERN.findall(sentence):
                build_fact(
                    facts,
                    source,
                    "achieves_conversion",
                    f"{percent} %",
                    sentence,
                    provenance_base,
                    alias_lookup,
                    confidence_base,
                )
            for time_match in TIME_PATTERN.findall(sentence):
                build_fact(
                    facts,
                    source,
                    "has_time",
                    f"{time_match[0]} {time_match[1]}",
                    sentence,
                    provenance_base,
                    alias_lookup,
                    confidence_base,
                )
            for conc_match in CONC_PATTERN.findall(sentence):
                build_fact(
                    facts,
                    source,
                    "has_concentration",
                    f"{conc_match[0]} {conc_match[1]}",
                    sentence,
                    provenance_base,
                    alias_lookup,
                    confidence_base,
                )
            kcat_match = KCAT_PATTERN.search(sentence)
            if kcat_match:
                value = kcat_match.group(1)
                unit = kcat_match.group(2) or ""
                build_fact(
                    facts,
                    source,
                    "has_kcat",
                    f"{value} {unit}".strip(),
                    sentence,
                    provenance_base,
                    alias_lookup,
                    confidence_base,
                )
            km_match = KM_PATTERN.search(sentence)
            if km_match:
                value = km_match.group(1)
                unit = km_match.group(2) or ""
                build_fact(
                    facts,
                    source,
                    "has_km",
                    f"{value} {unit}".strip(),
                    sentence,
                    provenance_base,
                    alias_lookup,
                    confidence_base,
                )
            kcat_km_match = KCAT_KM_PATTERN.search(sentence)
            if kcat_km_match:
                value = kcat_km_match.group(1)
                unit = kcat_km_match.group(2) or ""
                build_fact(
                    facts,
                    source,
                    "has_kcat_km",
                    f"{value} {unit}".strip(),
                    sentence,
                    provenance_base,
                    alias_lookup,
                    confidence_base,
                )
            for substrate in substrates:
                if substrate and substrate.lower() in sentence.lower():
                    build_fact(
                        facts,
                        source,
                        "targets_substrate",
                        substrate,
                        sentence,
                        provenance_base,
                        alias_lookup,
                        confidence_base,
                    )
            for metric in metrics:
                if metric and metric.lower() in sentence.lower():
                    build_fact(
                        facts,
                        source,
                        "discusses_metric",
                        metric,
                        sentence,
                        provenance_base,
                        alias_lookup,
                        confidence_base,
                    )
            for host in hosts:
                if host and host.lower() in sentence.lower():
                    build_fact(
                        facts,
                        source,
                        "expressed_in",
                        host,
                        sentence,
                        provenance_base,
                        alias_lookup,
                        confidence_base,
                    )
            for assay in assays:
                if assay and assay.lower() in sentence.lower():
                    build_fact(
                        facts,
                        source,
                        "assayed_with",
                        assay,
                        sentence,
                        provenance_base,
                        alias_lookup,
                        confidence_base,
                    )
    return facts


def load_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def run(
    workspace: Path,
    artifacts_dir: Path,
    out_path: Path,
) -> Dict[str, int]:
    schema = load_schema(workspace)
    alias_lookup = build_alias_lookup(schema)
    if not alias_lookup:
        alias_lookup = infer_alias_lookup(workspace / "text")
    corpus_index_path = workspace / "corpus_index.json"
    if not corpus_index_path.exists():
        raise SystemExit(f"Missing corpus index: {corpus_index_path}")
    corpus_index = json.loads(corpus_index_path.read_text())
    meta_map = {entry["txt_file"]: entry for entry in corpus_index}

    topic = workspace.name
    facts: List[dict] = []

    text_dir = workspace / "text"
    for txt_path in sorted(text_dir.glob("*.txt")):
        text = txt_path.read_text(errors="ignore")
        meta = meta_map.get(txt_path.name, {})
        provenance = {
            "source": "text",
            "pdf": meta.get("pdf_file"),
            "page": None,
            "bbox": None,
            "topic": topic,
        }
        facts.extend(extract_text_facts(text, alias_lookup, schema, provenance, 0.45))

    captions = load_jsonl(artifacts_dir / "captions.jsonl")
    for caption in captions:
        provenance = {
            "source": "caption",
            "pdf": caption.get("pdf_file"),
            "page": caption.get("page"),
            "bbox": caption.get("bbox"),
            "caption_id": caption.get("caption_id"),
            "topic": topic,
        }
        facts.extend(
            extract_text_facts(
                caption.get("text", ""),
                alias_lookup,
                schema,
                provenance,
                0.55,
            )
        )

    tables = load_jsonl(artifacts_dir / "tables.jsonl")
    for table in tables:
        structured = extract_table_facts(table, alias_lookup, topic)
        facts.extend(structured)
        if not structured and table.get("text"):
            provenance = {
                "source": "table_text",
                "pdf": table.get("pdf_file"),
                "page": table.get("page"),
                "bbox": table.get("bbox"),
                "table_id": table.get("table_id"),
                "topic": topic,
            }
            facts.extend(
                extract_text_facts(
                    table.get("text", ""),
                    alias_lookup,
                    schema,
                    provenance,
                    0.6,
                )
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for fact in facts:
            handle.write(json.dumps(fact, ensure_ascii=False) + "\n")

    summary = {
        "fact_count": len(facts),
        "relation_types": sorted({fact["relation_type"] for fact in facts}),
    }
    (out_path.parent / "facts_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace with text + schema.")
    parser.add_argument("--artifacts-dir", type=Path, help="Artifacts directory (captions/tables).")
    parser.add_argument("--out-path", type=Path, help="Output JSONL path for facts.")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    artifacts_dir = (args.artifacts_dir or (workspace / "artifacts")).resolve()
    out_path = (args.out_path or (workspace / "facts" / "facts.jsonl")).resolve()
    run(workspace, artifacts_dir, out_path)


if __name__ == "__main__":
    main()
