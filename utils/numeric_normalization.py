#!/usr/bin/env python3
"""Dynamic unit discovery + numeric normalization utilities."""

from __future__ import annotations

import json
import os
import hashlib
import unicodedata
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

_EMBED_MODEL: SentenceTransformer | None = None


def get_embedder(model_name: Optional[str] = None) -> SentenceTransformer:
    global _EMBED_MODEL
    if _EMBED_MODEL is not None:
        return _EMBED_MODEL
    model_name = model_name or "sentence-transformers/all-MiniLM-L6-v2"
    _EMBED_MODEL = SentenceTransformer(model_name)
    return _EMBED_MODEL

NUM_UNIT_RE = re.compile(
    r"(?P<number>[-+]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*(?P<unit>[°ºµμuA-Za-z/%]+(?:[-/][A-Za-z%]+)?)",
    re.IGNORECASE,
)
NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?(?:e[+-]?\d+)?", re.IGNORECASE)
PH_RE = re.compile(r"\bpH\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
RANGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)")
TEN_POW_RE = re.compile(r"^10\^(\d+)$")

ENZYME_PATTERN = re.compile(r"\b([A-Za-z][A-Za-z0-9-]{2,}ase)\b", re.IGNORECASE)
PROTEIN_PATTERN = re.compile(r"\b([A-Za-z0-9-]{3,}\s+protein)\b", re.IGNORECASE)


def normalize_unit_token(raw: str) -> str:
    token = unicodedata.normalize("NFKC", raw or "")
    token = token.casefold()
    token = token.replace("µ", "u").replace("μ", "u")
    token = token.replace("°", "").replace("º", "")
    token = token.replace("×", "x")
    token = re.sub(r"\bper\b", "/", token)
    token = re.sub(r"\s+", "", token)
    token = re.sub(r"[()\\[\\],;:]", "", token)
    token = re.sub(r"[^a-z0-9/%\\.x\\-]", "", token)
    if token.startswith("deg"):
        token = token[3:]
    return token


def extract_numeric_units(text: str) -> List[Tuple[str, Optional[str]]]:
    if not text:
        return []
    hits: List[Tuple[str, Optional[str]]] = []
    for match in NUM_UNIT_RE.finditer(text):
        hits.append((match.group("number"), match.group("unit")))
    for match in PH_RE.finditer(text):
        hits.append((match.group(1), "pH"))
    return hits


def parse_numeric_value(raw: str) -> Optional[float]:
    if not raw:
        return None
    compact = raw.strip()
    match = TEN_POW_RE.match(compact)
    if match:
        try:
            return float(10 ** int(match.group(1)))
        except Exception:
            return None
    try:
        return float(compact)
    except Exception:
        return None


def build_canonical_unit_map(unit_frequency: Dict[str, int]) -> Dict[str, Dict[str, Any]]:
    clusters: Dict[str, Dict[str, Any]] = {}
    for unit, count in unit_frequency.items():
        key = normalize_unit_token(unit)
        if key not in clusters:
            clusters[key] = {"aliases": [], "counts": Counter()}
        clusters[key]["aliases"].append(unit)
        clusters[key]["counts"][unit] += count
    canonical_map: Dict[str, Dict[str, Any]] = {}
    for key, payload in clusters.items():
        counts: Counter = payload["counts"]
        canonical = counts.most_common(1)[0][0] if counts else key
        canonical_map[key] = {
            "canonical_unit": canonical,
            "aliases": sorted(set(payload["aliases"])),
        }
    return canonical_map


def alias_to_canonical(canonical_map: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    alias_map: Dict[str, str] = {}
    for key, payload in canonical_map.items():
        canonical = payload["canonical_unit"]
        for alias in payload.get("aliases", []):
            alias_map[alias] = canonical
        alias_map[key] = canonical
    return alias_map


def discover_units_from_edges(edges: Iterable[Dict[str, Any]]) -> Tuple[Dict[str, int], Dict[str, Dict[str, Any]], Dict[str, str]]:
    freq: Dict[str, int] = {}
    for edge in edges:
        raw_value = str(edge.get("value") or edge.get("target") or "")
        hits = extract_numeric_units(raw_value)
        for _, unit in hits:
            if not unit:
                continue
            freq[unit] = freq.get(unit, 0) + 1
    canonical_map = build_canonical_unit_map(freq)
    alias_map = alias_to_canonical(canonical_map)
    return freq, canonical_map, alias_map


def tokenize_context(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def build_dimension_model(edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    token_counts: Dict[str, Counter] = defaultdict(Counter)
    token_totals = Counter()
    categories = sorted(
        {
            edge.get("relation_category")
            for edge in edges
            if edge.get("relation_category") and edge.get("relation_category") != "other"
        }
    )
    for edge in edges:
        relation = str(edge.get("relation") or "")
        sentence = str(edge.get("sentence") or "")
        unit = str(edge.get("raw_unit") or "")
        context = f"{relation} {sentence} {unit}"
        tokens = tokenize_context(context)
        category = edge.get("relation_category")
        if not category or category == "other":
            continue
        for token in tokens:
            token_counts[category][token] += 1
            token_totals[token] += 1

    token_assoc: Dict[str, Dict[str, float]] = {}
    for token, total in token_totals.items():
        token_assoc[token] = {}
        for category in categories:
            count = token_counts[category].get(token, 0)
            if total:
                token_assoc[token][category] = count / total

    confidences: List[float] = []
    for edge in edges:
        category = edge.get("relation_category")
        if not category or category == "other":
            continue
        relation = str(edge.get("relation") or "")
        sentence = str(edge.get("sentence") or "")
        unit = str(edge.get("raw_unit") or "")
        tokens = tokenize_context(f"{relation} {sentence} {unit}")
        if not tokens:
            continue
        scores = [token_assoc.get(tok, {}).get(category, 0.0) for tok in tokens]
        if scores:
            confidences.append(sum(scores) / len(scores))

    if confidences:
        threshold = float(np.percentile(confidences, 25))
    else:
        threshold = 0.0

    return {
        "categories": categories,
        "token_assoc": token_assoc,
        "threshold": threshold,
        "confidence_samples": confidences,
    }


def apply_dimension_model(edges: List[Dict[str, Any]], model: Dict[str, Any]) -> None:
    categories: List[str] = model.get("categories", [])
    token_assoc: Dict[str, Dict[str, float]] = model.get("token_assoc", {})
    threshold = float(model.get("threshold", 0.0))

    for edge in edges:
        relation = str(edge.get("relation") or "")
        sentence = str(edge.get("sentence") or "")
        unit = str(edge.get("raw_unit") or "")
        tokens = tokenize_context(f"{relation} {sentence} {unit}")
        category = edge.get("relation_category") or "other"
        if category != "other" and category in categories:
            scores = [token_assoc.get(tok, {}).get(category, 0.0) for tok in tokens]
            confidence = (sum(scores) / len(scores)) if scores else 0.0
            edge["dimension_label"] = category
            edge["dimension_confidence"] = confidence
            continue

        if not tokens or not categories:
            edge["dimension_label"] = "UNKNOWN_DIMENSION"
            edge["dimension_confidence"] = 0.0
            continue

        cat_scores = {
            cat: sum(token_assoc.get(tok, {}).get(cat, 0.0) for tok in tokens) for cat in categories
        }
        best_cat = max(cat_scores.items(), key=lambda item: item[1])
        total_score = sum(cat_scores.values())
        confidence = (best_cat[1] / total_score) if total_score else 0.0
        if confidence >= threshold and best_cat[1] > 0.0:
            edge["dimension_label"] = best_cat[0]
            edge["dimension_confidence"] = confidence
        else:
            edge["dimension_label"] = "UNKNOWN_DIMENSION"
            edge["dimension_confidence"] = confidence


def build_unit_alias_map_by_dimension(
    edges: List[Dict[str, Any]],
) -> Tuple[int, Dict[Tuple[str, str], Dict[str, Any]], Dict[str, Dict[str, str]]]:
    counts: Dict[Tuple[str, str], Counter] = {}
    raw_unit_count = 0
    for edge in edges:
        raw_unit = edge.get("raw_unit")
        if not raw_unit:
            continue
        raw_unit_count += 1
        dimension = edge.get("dimension_label") or "UNKNOWN_DIMENSION"
        norm_unit = normalize_unit_token(raw_unit)
        key = (dimension, norm_unit)
        if key not in counts:
            counts[key] = Counter()
        counts[key][raw_unit] += 1

    canonical_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    alias_map: Dict[str, Dict[str, str]] = defaultdict(dict)
    for key, counter in counts.items():
        canonical = counter.most_common(1)[0][0] if counter else key[1]
        canonical_map[key] = {
            "dimension_label": key[0],
            "canonical_unit": canonical,
            "aliases": sorted(counter.keys()),
        }
        for alias in counter.keys():
            alias_map[key[0]][alias] = canonical
        alias_map[key[0]][key[1]] = canonical
    return raw_unit_count, canonical_map, alias_map


def apply_unit_canonicalization(edges: List[Dict[str, Any]], alias_map: Dict[str, Dict[str, str]]) -> None:
    for edge in edges:
        if edge.get("numeric_status") not in {"RAW_NUMERIC_UNNORMALIZED", "VALID_NORMALIZED"}:
            continue
        raw_unit = edge.get("raw_unit")
        if not raw_unit:
            continue
        dimension = edge.get("dimension_label") or "UNKNOWN_DIMENSION"
        lookup = alias_map.get(dimension, {})
        canonical = lookup.get(raw_unit) or lookup.get(normalize_unit_token(raw_unit))
        if canonical:
            edge["normalized_unit"] = canonical
            edge["numeric_status"] = "VALID_NORMALIZED"
        else:
            edge["normalized_unit"] = "UNRECOGNIZED_UNIT"
            edge["numeric_status"] = "UNRECOGNIZED_UNIT"


def infer_edge_type(edge: Dict[str, Any]) -> str:
    keys = set(edge.keys())
    if {"instrument", "relation", "value"}.issubset(keys):
        return "instrument_kg"
    if {"source", "relation", "target"}.issubset(keys) and "sentence" not in keys and len(keys) <= 4:
        return "timeline_kg"
    if {"source", "relation", "target"}.issubset(keys):
        return "kg_edges"
    if {"paper", "relation", "value"}.issubset(keys):
        return "methodology_kg"
    return "unknown"


def infer_entity_anchor(edge: Dict[str, Any]) -> Optional[str]:
    if edge.get("source"):
        return str(edge.get("source"))
    sentence = str(edge.get("sentence") or "")
    for pattern in (ENZYME_PATTERN, PROTEIN_PATTERN):
        match = pattern.search(sentence)
        if match:
            return match.group(1)
    return None


def infer_paper_id(edge: Dict[str, Any]) -> Optional[str]:
    raw = edge.get("pdf_file") or edge.get("paper")
    if not raw:
        return None
    text = str(raw)
    if "/" in text or text.endswith(".pdf"):
        return Path(text).stem
    return text


def infer_relation_category(relation: str, unit_token: Optional[str]) -> str:
    rel = (relation or "").lower()
    unit = normalize_unit_token(unit_token or "")
    if "ph" in rel or unit == "ph":
        return "pH"
    if "temp" in rel or unit in {"c", "f", "k"}:
        return "temperature"
    if "time" in rel or "duration" in rel or unit in {"s", "sec", "secs", "second", "min", "mins", "minute", "h", "hr", "hrs", "hour", "day", "days"}:
        return "time"
    if "volume" in rel or unit.endswith("l"):
        return "volume"
    if "concentration" in rel or "/l" in unit or unit.endswith("m") or unit.endswith("molar"):
        return "concentration"
    if "speed" in rel or unit in {"rpm", "xg", "g"}:
        return "speed"
    if unit.endswith("nm"):
        return "wavelength"
    if "%" in unit or "percent" in rel:
        return "percentage"
    return "other"


def normalize_edge_numeric(
    edge: Dict[str, Any],
    alias_map: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    enriched = dict(edge)
    edge_type = infer_edge_type(edge)
    raw_value = edge.get("value") if edge_type in {"instrument_kg", "methodology_kg"} else edge.get("target")
    raw_value = "" if raw_value is None else str(raw_value)
    sentence = str(edge.get("sentence") or "")

    numeric_hits = extract_numeric_units(raw_value)
    if not numeric_hits:
        match = NUM_RE.search(raw_value)
        if match:
            numeric_hits = [(match.group(0), None)]
    if not numeric_hits and not raw_value:
        numeric_hits = extract_numeric_units(sentence)

    numeric_status = "NO_NUMERIC"
    normalized_value = None
    normalized_unit = None
    raw_unit = None

    if numeric_hits:
        number_str, unit_str = numeric_hits[0]
        raw_unit = unit_str
        if RANGE_RE.search(raw_value) or RANGE_RE.search(sentence):
            numeric_status = "BROKEN_PARSE"
        else:
            value = parse_numeric_value(number_str)
            if value is None:
                numeric_status = "BROKEN_PARSE"
            else:
                normalized_value = value
                numeric_status = "RAW_NUMERIC_UNNORMALIZED"

    enriched.update(
        {
            "raw_value": raw_value,
            "raw_unit": raw_unit,
            "numeric_status": numeric_status,
            "normalized_value": normalized_value,
            "normalized_unit": normalized_unit,
            "paper_id": infer_paper_id(edge),
            "section_type": edge.get("section_type"),
            "entity_anchor": infer_entity_anchor(edge),
            "relation_category": infer_relation_category(str(edge.get("relation") or ""), raw_unit),
            "dimension_label": "UNKNOWN_DIMENSION",
            "dimension_confidence": 0.0,
        }
    )
    return enriched


def cluster_numeric_values(values: List[Tuple[float, int]], tolerance: float = 0.05) -> List[List[int]]:
    if not values:
        return []
    values = sorted(values, key=lambda pair: pair[0])
    clusters: List[List[int]] = []
    current: List[int] = [values[0][1]]
    base = values[0][0]
    for value, idx in values[1:]:
        threshold = max(abs(base) * tolerance, 1e-9)
        if abs(value - base) <= threshold:
            current.append(idx)
        else:
            clusters.append(current)
            current = [idx]
            base = value
    clusters.append(current)
    return clusters


def cluster_numeric_values_adaptive(values: List[Tuple[float, int]]) -> List[List[int]]:
    if not values:
        return []
    values = sorted(values, key=lambda pair: pair[0])
    if len(values) < 3:
        return [[idx for _, idx in values]]
    diffs = []
    for (v1, _), (v2, _) in zip(values, values[1:]):
        denom = max(abs(v1), 1.0)
        diffs.append(abs(v2 - v1) / denom)
    epsilon = float(np.median(diffs)) if diffs else 0.0
    if epsilon == 0.0:
        non_zero = [d for d in diffs if d > 0]
        epsilon = float(np.percentile(non_zero, 25)) if non_zero else 0.0
    clusters: List[List[int]] = []
    current = [values[0][1]]
    base = values[0][0]
    for value, idx in values[1:]:
        denom = max(abs(base), 1.0)
        diff = abs(value - base) / denom
        if diff <= epsilon:
            current.append(idx)
        else:
            clusters.append(current)
            current = [idx]
            base = value
    clusters.append(current)
    return clusters


def embed_texts(texts: List[str], model_name: Optional[str] = None, batch_size: int = 128) -> np.ndarray:
    if not texts:
        return np.zeros((0, 1), dtype="float32")
    if os.environ.get("FAST_EMBED") == "1":
        return hash_embed_texts(texts)
    try:
        model = get_embedder(model_name)
        embeddings = model.encode(texts, normalize_embeddings=True, batch_size=batch_size)
        return np.asarray(embeddings, dtype="float32")
    except Exception:
        return hash_embed_texts(texts)


def hash_embed_texts(texts: List[str], dim: int = 128) -> np.ndarray:
    if not texts:
        return np.zeros((0, dim), dtype="float32")
    vectors = np.zeros((len(texts), dim), dtype="float32")
    for i, text in enumerate(texts):
        for token in re.findall(r"[A-Za-z0-9_]+", text.lower()):
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            idx = int(digest[:8], 16) % dim
            vectors[i, idx] += 1.0
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def compute_similarity_threshold(embeddings: np.ndarray, sample_size: int = 512) -> float:
    if embeddings.size == 0:
        return 0.75
    n = embeddings.shape[0]
    if n < 3:
        return 0.85
    idx = np.linspace(0, n - 1, num=min(sample_size, n), dtype=int)
    sample = embeddings[idx]
    sims = []
    for i in range(min(50, sample.shape[0] - 1)):
        vec = sample[i]
        scores = sample[i + 1 :] @ vec
        sims.extend(scores.tolist())
    if not sims:
        return 0.8
    median = float(np.median(sims))
    return min(0.9, max(0.55, median + 0.1))


def cluster_embeddings(embeddings: np.ndarray, threshold: float) -> List[List[int]]:
    clusters: List[List[int]] = []
    if embeddings.size == 0:
        return clusters
    centroids: List[np.ndarray] = []
    for idx, vec in enumerate(embeddings):
        if not centroids:
            centroids.append(vec.copy())
            clusters.append([idx])
            continue
        sims = np.array([float(vec @ centroid) for centroid in centroids])
        best = int(np.argmax(sims))
        if sims[best] >= threshold:
            clusters[best].append(idx)
            members = embeddings[clusters[best]]
            centroids[best] = members.mean(axis=0)
        else:
            centroids.append(vec.copy())
            clusters.append([idx])
    return clusters


def infer_dimension_labels(
    edges: List[Dict[str, Any]],
    embeddings: np.ndarray,
    clusters: List[List[int]],
    min_confidence: float = 0.55,
) -> None:
    for cluster in clusters:
        if not cluster:
            continue
        category_counts = Counter()
        for idx in cluster:
            category_counts[edges[idx].get("relation_category") or "other"] += 1
        dominant, count = category_counts.most_common(1)[0]
        confidence = count / len(cluster)
        label = dominant if confidence >= min_confidence else "UNKNOWN_DIMENSION"
        for idx in cluster:
            edges[idx]["dimension_label"] = label
            edges[idx]["dimension_confidence"] = confidence
            edges[idx]["dimension_embedding_norm"] = float(np.linalg.norm(embeddings[idx]))


def build_dimension_features(edge: Dict[str, Any]) -> str:
    unit = str(edge.get("raw_unit") or edge.get("normalized_unit") or "")
    relation = str(edge.get("relation_category") or edge.get("relation") or "")
    context = str(edge.get("sentence") or "")
    context = re.sub(r"\d", "0", context)
    context = re.sub(r"\s+", " ", context).strip()[:80]
    return f"unit:{unit} relation:{relation} context:{context}"


def section_priority(section_type: Optional[str]) -> int:
    if not section_type:
        return 0
    st = section_type.lower()
    if "experimental" in st or "method" in st:
        return 3
    if "results" in st:
        return 2
    if "computational" in st:
        return 1
    return 0
