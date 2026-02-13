#!/usr/bin/env python3
"""Utilities for topic-aware KG schemas and seed selection."""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]

NOISE_ENTITIES = {
    "activity",
    "analysis",
    "decrease",
    "degradation",
    "enzyme",
    "enzymes",
    "expression",
    "gene",
    "genes",
    "increase",
    "mutation",
    "mutations",
    "protein",
    "proteins",
    "result",
    "results",
    "stability",
}


def resolve_workspace_root(workspace_root: Path | None = None) -> Path:
    if workspace_root:
        return workspace_root.expanduser().resolve()
    env_root = os.environ.get("WORKSPACE_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return PROJECT_ROOT / "KnowledgeGraph"


@lru_cache(maxsize=4)
def load_schema(workspace_root: Path | None = None) -> Dict[str, Any]:
    root = resolve_workspace_root(workspace_root)
    schema_path = root / "kg_schema.json"
    if schema_path.exists():
        return json.loads(schema_path.read_text())
    return {}


def topic_label(schema: Dict[str, Any], workspace_root: Path | None = None) -> str:
    topic = str(schema.get("topic") or "").strip()
    if topic:
        return topic
    return resolve_workspace_root(workspace_root).name


def normalize_entity(label: str) -> str:
    cleaned = re.sub(r"\s+", " ", label.strip())
    return cleaned.strip(" ,;:.()")


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def build_alias_lookup(schema: Dict[str, Any]) -> Dict[str, str]:
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


def expected_entities_from_question(
    question: str,
    schema: Dict[str, Any],
    max_hits: int = 6,
) -> List[str]:
    if not question:
        return []
    lookup = build_alias_lookup(schema)
    lowered = question.lower()
    hits = []
    for alias, canonical in lookup.items():
        if alias and alias in lowered:
            hits.append(canonical)
    return dedupe_preserve_order(hits)[:max_hits]


def schema_entity_candidates(schema: Dict[str, Any]) -> List[str]:
    key_entities = [normalize_entity(str(item)) for item in schema.get("key_entities") or [] if str(item).strip()]
    alias_keys = [normalize_entity(str(item)) for item in (schema.get("entity_aliases") or {}).keys() if str(item).strip()]
    return dedupe_preserve_order(key_entities + alias_keys)


def filter_seed_candidates(candidates: Sequence[str]) -> List[str]:
    cleaned = []
    for candidate in candidates:
        if not candidate:
            continue
        lowered = candidate.lower()
        if lowered in NOISE_ENTITIES:
            continue
        if len(lowered) < 3:
            continue
        if lowered.isdigit():
            continue
        cleaned.append(candidate)
    return cleaned


def expand_query_with_schema(query: str, schema: Dict[str, Any], max_entities: int = 4) -> str:
    entities = expected_entities_from_question(query, schema, max_hits=max_entities)
    if not entities:
        entities = filter_seed_candidates(schema_entity_candidates(schema))[:max_entities]
    if not entities:
        return query
    lowered = query.lower()
    extras = [entity for entity in entities if entity.lower() not in lowered]
    if not extras:
        return query
    return query + " " + " ".join(extras)


def load_graph_overview_sources(graph_overview_path: Path) -> List[str]:
    if not graph_overview_path.exists():
        return []
    payload = json.loads(graph_overview_path.read_text())
    sources = [entry[0] for entry in payload.get("top_sources", []) if entry and entry[0]]
    return sources


def select_graph_seeds(
    context_sources: Sequence[str],
    question: str,
    schema: Dict[str, Any],
    graph_overview_path: Path,
    max_seeds: int = 6,
) -> List[str]:
    seeds = dedupe_preserve_order([src for src in context_sources if src])
    extras: List[str] = []
    if len(seeds) < max_seeds:
        extras = expected_entities_from_question(question, schema, max_hits=max_seeds)
    if not extras:
        extras = filter_seed_candidates(schema_entity_candidates(schema))
    if not extras:
        extras = filter_seed_candidates(load_graph_overview_sources(graph_overview_path))
    for entity in extras:
        if entity in seeds:
            continue
        seeds.append(entity)
        if len(seeds) >= max_seeds:
            break
    return seeds
