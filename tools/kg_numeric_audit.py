#!/usr/bin/env python3
"""Dynamic unit discovery + numeric normalization audit across KG edges."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.ops_tracking import start_run, log_artifact, finalize_run, append_private_metrics  # noqa: E402
from utils.numeric_normalization import (
    normalize_edge_numeric,
    cluster_numeric_values_adaptive,
    embed_texts,
    build_dimension_model,
    apply_dimension_model,
    build_unit_alias_map_by_dimension,
    apply_unit_canonicalization,
    build_dimension_features,
    normalize_unit_token,
)
from utils.workspace_utils import resolve_workspace_root

KG_PATTERNS = (
    "kg_edges.jsonl",
    "methodology_kg_edges.jsonl",
    "timeline_edges.jsonl",
)


def iter_kg_files(root: Path) -> List[Path]:
    paths = []
    for pattern in KG_PATTERNS:
        paths.extend(root.rglob(f"*{pattern}"))
    extra = root / "InstrumentGraph" / "kg_edges.jsonl"
    if extra.exists() and extra not in paths:
        paths.append(extra)
    return sorted({p.resolve() for p in paths})


def iter_edges(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def iter_all_edges(paths: List[Path]) -> Iterable[Dict[str, Any]]:
    for path in paths:
        yield from iter_edges(path)


def detect_duplicates(path: Path) -> Tuple[int, int]:
    total = 0
    seen = set()
    for edge in iter_edges(path):
        total += 1
        seen.add(json.dumps(edge, sort_keys=True, ensure_ascii=False))
    dup_exact = total - len(seen)
    return total, dup_exact


def summarize_numeric_edges(edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    status_counts = Counter()
    category_counts = Counter()
    dimension_counts = Counter()
    per_paper_total = Counter()
    per_paper_numeric = Counter()
    values_by_group: Dict[Tuple[str, str], List[Tuple[float, int, str]]] = defaultdict(list)

    for idx, edge in enumerate(edges):
        status = edge.get("numeric_status") or "NO_NUMERIC"
        status_counts[status] += 1
        paper_id = edge.get("paper_id") or ""
        per_paper_total[paper_id] += 1
        if status in {"VALID_NORMALIZED", "RAW_NUMERIC_UNNORMALIZED", "UNRECOGNIZED_UNIT"}:
            per_paper_numeric[paper_id] += 1
            dimension_counts[edge.get("dimension_label") or "UNKNOWN_DIMENSION"] += 1
        category = edge.get("relation_category") or "other"
        category_counts[category] += 1
        if status == "VALID_NORMALIZED" and edge.get("normalized_value") is not None:
            group = (category, edge.get("normalized_unit") or "")
            values_by_group[group].append((edge["normalized_value"], idx, paper_id))

    densities = []
    for paper_id, total in per_paper_total.items():
        if not paper_id:
            continue
        numeric = per_paper_numeric.get(paper_id, 0)
        densities.append((numeric / total if total else 0.0, paper_id, numeric, total))
    densities.sort(reverse=True, key=lambda row: row[0])

    consensus_clusters = []
    for (category, unit), values in values_by_group.items():
        clusters = cluster_numeric_values_adaptive([(v, idx) for v, idx, _ in values])
        for cluster in clusters:
            if not cluster:
                continue
            members = [v for v in values if v[1] in cluster]
            if not members:
                continue
            cluster_values = [m[0] for m in members]
            cluster_size = len(cluster_values)
            papers = {m[2] for m in members if m[2]}
            consensus_clusters.append(
                {
                    "relation_category": category,
                    "normalized_unit": unit,
                    "cluster_size": cluster_size,
                    "paper_diversity": len(papers),
                    "mean_value": sum(cluster_values) / cluster_size,
                }
            )
    consensus_clusters.sort(key=lambda row: (row["cluster_size"], row["paper_diversity"]), reverse=True)

    return {
        "numeric_status_counts": status_counts,
        "relation_category_distribution": category_counts,
        "dimension_distribution": dimension_counts,
        "paper_parameter_density_top": [
            {"paper_id": paper, "density": dens, "numeric": num, "total": total}
            for dens, paper, num, total in densities[:10]
        ],
        "consensus_clusters_top": consensus_clusters[:10],
    }


def apply_dimension_labels(edges: List[Dict[str, Any]], model: Dict[str, Any]) -> None:
    apply_dimension_model(edges, model)


def build_slot_stats(edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    slot_coverage = defaultdict(set)
    anchor_totals = Counter()
    anchor_numeric = Counter()
    paper_slots = defaultdict(set)
    paper_totals = Counter()
    for edge in edges:
        paper_id = edge.get("paper_id") or ""
        anchor = edge.get("entity_anchor") or ""
        relation = edge.get("relation_category") or "other"
        dimension = edge.get("dimension_label") or "UNKNOWN_DIMENSION"
        unit = edge.get("normalized_unit") or ""
        slot_key = (anchor, relation, dimension, unit)
        paper_totals[paper_id] += 1
        if edge.get("numeric_status") == "VALID_NORMALIZED":
            slot_coverage[slot_key].add(paper_id)
            paper_slots[paper_id].add(slot_key)
            anchor_numeric[anchor] += 1
        anchor_totals[anchor] += 1
    cross_paper_completeness = {
        f"{slot[0]}::{slot[1]}::{slot[2]}::{slot[3]}": len(papers)
        for slot, papers in slot_coverage.items()
    }
    anchor_density = [
        {
            "entity_anchor": anchor,
            "density": (anchor_numeric[anchor] / anchor_totals[anchor]) if anchor_totals[anchor] else 0.0,
            "numeric_edges": anchor_numeric[anchor],
            "total_edges": anchor_totals[anchor],
        }
        for anchor in anchor_totals
        if anchor
    ]
    anchor_density.sort(key=lambda row: row["density"], reverse=True)
    per_paper_slot_coverage = [
        {"paper_id": paper, "slot_count": len(slots), "total_edges": paper_totals[paper]}
        for paper, slots in paper_slots.items()
        if paper
    ]
    return {
        "cross_paper_slot_completeness": cross_paper_completeness,
        "parameter_density_per_entity_anchor": anchor_density[:20],
        "slot_coverage_per_paper": per_paper_slot_coverage[:20],
    }


class DisjointSet:
    def __init__(self) -> None:
        self.parent: Dict[str, str] = {}

    def add(self, item: str) -> None:
        if item not in self.parent:
            self.parent[item] = item

    def find(self, item: str) -> str:
        root = self.parent.get(item, item)
        if root != item:
            root = self.find(root)
            self.parent[item] = root
        return root

    def union(self, a: str, b: str) -> None:
        self.add(a)
        self.add(b)
        ra = self.find(a)
        rb = self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def component_count(self) -> int:
        roots = {self.find(node) for node in self.parent}
        return len(roots)


def build_slot_consensus(edges: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    slot_index: Dict[str, Any] = {}
    slots = defaultdict(list)
    for edge in edges:
        anchor = edge.get("entity_anchor") or "unknown_entity"
        relation = edge.get("relation_category") or "other"
        dimension = edge.get("dimension_label") or "UNKNOWN_DIMENSION"
        unit = edge.get("normalized_unit") or ""
        slots[(anchor, relation, dimension, unit)].append(edge)

    cluster_sizes = []
    distinct_paper_counts = []
    multi_paper_slots = 0
    graph = DisjointSet()
    graph_edge_count = 0

    for (anchor, relation, dimension, unit), slot_edges in slots.items():
        valid = [e for e in slot_edges if e.get("numeric_status") == "VALID_NORMALIZED"]
        # Deduplicate by (paper, value, unit)
        deduped = []
        seen = set()
        for item in valid:
            key = (item.get("paper_id"), item.get("normalized_value"), item.get("normalized_unit"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        if not deduped:
            fallback = [e for e in slot_edges if e.get("numeric_status") == "RAW_NUMERIC_UNNORMALIZED"]
            slot_index[f"{anchor}::{relation}::{dimension}::{unit}"] = {
                "fallback_used": True,
                "selected_value": fallback[0].get("raw_value") if fallback else None,
                "posterior_score": 0.0,
                "confidence_level": "LOW",
                "distribution_summary": {"count": len(fallback)},
                "clusters": [],
            }
            continue

        methods = [e for e in deduped if str(e.get("section_type") or "").lower() in {"experimental", "methods", "method"}]
        candidates = methods if methods else deduped
        values = [(e.get("normalized_value"), idx, e.get("paper_id") or "") for idx, e in enumerate(candidates)]
        values = [(v, idx, p) for v, idx, p in values if v is not None]
        if not values:
            continue
        clusters = cluster_numeric_values_adaptive([(v, idx) for v, idx, _ in values])
        cluster_records = []
        total_slot_edges = len(candidates)
        total_papers = len({e.get("paper_id") for e in candidates if e.get("paper_id")}) or 1
        texts = [build_dimension_features(e) for e in candidates]
        embeddings = embed_texts(texts)
        slot_centroid = embeddings.mean(axis=0) if embeddings.size else None
        slot_has_multi = False

        for cluster in clusters:
            members = [candidates[idx] for idx in cluster]
            cluster_values = [m.get("normalized_value") for m in members if m.get("normalized_value") is not None]
            if not cluster_values:
                continue
            cluster_size = len(cluster_values)
            papers = {m.get("paper_id") for m in members if m.get("paper_id")}
            distinct_papers = len(papers)
            methods_ratio = (
                len([m for m in members if str(m.get("section_type") or "").lower() in {"experimental", "methods", "method"}])
                / len(members)
            )
            mean_value = sum(cluster_values) / cluster_size
            variance = sum((v - mean_value) ** 2 for v in cluster_values) / cluster_size
            if embeddings.size and slot_centroid is not None:
                cluster_centroid = embeddings[cluster].mean(axis=0)
                contextual_similarity = float(cluster_centroid @ slot_centroid)
            else:
                contextual_similarity = 0.5
            dimension_conf = sum(m.get("dimension_confidence", 0.0) for m in members) / len(members)
            methods_weight = (sum(1 for _ in members) / len(members)) * (0.5 + 0.5 * methods_ratio)
            posterior = (
                (cluster_size / total_slot_edges)
                * (distinct_papers / total_papers)
                * methods_weight
                * contextual_similarity
                * dimension_conf
            )
            cluster_records.append(
                {
                    "cluster_size": cluster_size,
                    "distinct_paper_count": distinct_papers,
                    "methods_section_ratio": methods_ratio,
                    "mean_value": mean_value,
                    "variance": variance,
                    "posterior_score": posterior,
                }
            )
            cluster_sizes.append(cluster_size)
            distinct_paper_counts.append(distinct_papers)
            if distinct_papers >= 2:
                slot_has_multi = True
                papers_list = list(papers)
                if papers_list:
                    first = papers_list[0]
                    for other in papers_list[1:]:
                        graph.union(first, other)
                        graph_edge_count += 1

        if slot_has_multi:
            multi_paper_slots += 1
        if not cluster_records:
            continue
        cluster_records.sort(key=lambda row: row["posterior_score"], reverse=True)
        selected = cluster_records[0]
        confidence = "HIGH" if selected["posterior_score"] >= 0.66 else "MEDIUM" if selected["posterior_score"] >= 0.33 else "LOW"
        slot_index[f"{anchor}::{relation}::{dimension}::{unit}"] = {
            "fallback_used": False,
            "selected_value": selected["mean_value"],
            "posterior_score": selected["posterior_score"],
            "confidence_level": confidence,
            "distribution_summary": {
                "cluster_count": len(cluster_records),
                "total_edges": total_slot_edges,
                "total_papers": total_papers,
            },
            "clusters": cluster_records[:5],
        }

    stats = {
        "cluster_sizes": cluster_sizes,
        "distinct_paper_counts": distinct_paper_counts,
        "multi_paper_slots": multi_paper_slots,
        "total_slots": len(slots),
        "cross_paper_components": graph.component_count(),
        "cross_paper_nodes": len(graph.parent),
        "cross_paper_edges": graph_edge_count,
    }
    return slot_index, stats


def extract_prior_metrics(payload: Dict[str, Any] | None) -> Dict[str, float | None]:
    if not payload:
        return {
            "canonical_unit_count": None,
            "slot_fill_rate": None,
            "dimension_confident_edges_pct": None,
            "unit_compression_ratio": None,
            "multi_paper_support_pct": None,
            "cluster_size_median": None,
        }
    canonical_unit_count = payload.get("canonical_unit_count")
    if canonical_unit_count is None and "canonical_units" in payload:
        canonical_unit_count = len(payload.get("canonical_units") or [])
    dimension_confident_edges_pct = payload.get("dimension_confident_edges_pct")
    if dimension_confident_edges_pct is None and payload.get("kgs"):
        total = 0
        confident = 0
        for kg in payload.get("kgs", []):
            dist = kg.get("dimension_distribution") or {}
            for label, count in dist.items():
                total += count
                if label != "UNKNOWN_DIMENSION":
                    confident += count
        dimension_confident_edges_pct = (confident / total) if total else None
    return {
        "canonical_unit_count": canonical_unit_count,
        "slot_fill_rate": payload.get("slot_fill_rate"),
        "dimension_confident_edges_pct": dimension_confident_edges_pct,
        "unit_compression_ratio": payload.get("unit_compression_ratio"),
        "multi_paper_support_pct": payload.get("multi_paper_support_pct"),
        "cluster_size_median": (payload.get("cluster_size_distribution") or {}).get("median"),
    }


def slot_fill_rate_from_index(path: Path) -> float | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    if not isinstance(data, dict) or not data:
        return None
    total = len(data)
    filled = sum(1 for entry in data.values() if isinstance(entry, dict) and entry.get("selected_value") is not None)
    return (filled / total) if total else None


def distribution_summary(values: List[float]) -> Dict[str, float | int]:
    if not values:
        return {"count": 0}
    arr = np.asarray(values, dtype=float)
    return {
        "count": int(arr.size),
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "p25": float(np.percentile(arr, 25)),
        "p75": float(np.percentile(arr, 75)),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repo root")
    parser.add_argument("--out-dir", type=Path, help="Audit output directory")
    args = parser.parse_args()

    run_id, _ = start_run("kg_numeric_audit", {"root": str(args.root)}, "KG numeric audit")

    kg_files = iter_kg_files(args.root)
    all_edges = list(iter_all_edges(kg_files))
    enriched_all = [normalize_edge_numeric(edge) for edge in all_edges]
    dimension_model = build_dimension_model(enriched_all)
    apply_dimension_labels(enriched_all, dimension_model)
    raw_unit_count, canonical_map, alias_map = build_unit_alias_map_by_dimension(enriched_all)
    apply_unit_canonicalization(enriched_all, alias_map)

    unit_frequency = Counter(edge.get("raw_unit") for edge in enriched_all if edge.get("raw_unit"))
    unique_units_raw_count = len(unit_frequency)
    canonical_unit_count = len(canonical_map)
    unit_compression_ratio = (unique_units_raw_count / canonical_unit_count) if canonical_unit_count else 0.0

    metrics = {
        "unique_units_raw_count": unique_units_raw_count,
        "canonical_unit_count": canonical_unit_count,
        "unit_compression_ratio": unit_compression_ratio,
        "dimension_count": 0,
        "dimension_confident_edges_pct": 0.0,
        "unique_units_raw": sorted(unit_frequency.keys()),
        "unit_frequency": dict(sorted(unit_frequency.items(), key=lambda x: x[1], reverse=True)),
        "canonical_units": [
            {
                "dimension_label": entry["dimension_label"],
                "canonical_unit": entry["canonical_unit"],
                "aliases": entry["aliases"],
            }
            for entry in canonical_map.values()
        ],
        "kgs": [],
    }

    total_edges = 0
    total_dups = 0
    status_totals = Counter()
    dimension_labels = set()
    dimension_confident_edges = 0
    dimension_numeric_total = 0

    methodology_canon = set()
    full_canon = set()

    for path in kg_files:
        edges = []
        seen = set()
        total = 0
        for edge in iter_edges(path):
            total += 1
            seen.add(json.dumps(edge, sort_keys=True, ensure_ascii=False))
            edges.append(edge)
        dup_exact = total - len(seen)
        total_edges += total
        total_dups += dup_exact

        enriched = [normalize_edge_numeric(edge) for edge in edges]
        apply_dimension_labels(enriched, dimension_model)
        apply_unit_canonicalization(enriched, alias_map)
        numeric_edges = [
            e
            for e in enriched
            if e.get("numeric_status")
            in {"VALID_NORMALIZED", "RAW_NUMERIC_UNNORMALIZED", "UNRECOGNIZED_UNIT"}
        ]
        for edge in numeric_edges:
            label = edge.get("dimension_label") or "UNKNOWN_DIMENSION"
            dimension_labels.add(label)
            if label != "UNKNOWN_DIMENSION":
                dimension_confident_edges += 1
        dimension_numeric_total += len(numeric_edges)
        summary = summarize_numeric_edges(enriched)
        status_totals.update(summary["numeric_status_counts"])

        raw_unit_count_kg, canon_map_kg, _ = build_unit_alias_map_by_dimension(enriched)
        canon_units = {(entry["dimension_label"], entry["canonical_unit"]) for entry in canon_map_kg.values()}
        unit_freq_kg = Counter(edge.get("raw_unit") for edge in enriched if edge.get("raw_unit"))
        compression_ratio_kg = (len(unit_freq_kg) / len(canon_map_kg)) if canon_map_kg else 0.0

        metrics["kgs"].append(
            {
                "name": path.name,
                "path": str(path),
                "edge_count": total,
                "dup_exact": dup_exact,
                "numeric_status_counts": summary["numeric_status_counts"],
                "relation_category_distribution": summary["relation_category_distribution"],
                "dimension_distribution": summary["dimension_distribution"],
                "paper_parameter_density_top": summary["paper_parameter_density_top"],
                "consensus_clusters_top": summary["consensus_clusters_top"],
                "unique_units_raw_count": len(unit_freq_kg),
                "canonical_unit_count": len(canon_map_kg),
                "unit_compression_ratio": compression_ratio_kg,
            }
        )
        if "methodology_kg" in path.name:
            methodology_canon |= canon_units
        elif path.name.endswith("kg_edges.jsonl"):
            full_canon |= canon_units

    metrics["dimension_count"] = len({d for d in dimension_labels if d != "UNKNOWN_DIMENSION"})
    metrics["dimension_confident_edges_pct"] = (
        (dimension_confident_edges / dimension_numeric_total) if dimension_numeric_total else 0.0
    )

    unit_diversity_count = len(canonical_map)
    canonical_counts = Counter()
    for edge in enriched_all:
        raw_unit = edge.get("raw_unit")
        if not raw_unit:
            continue
        dimension = edge.get("dimension_label") or "UNKNOWN_DIMENSION"
        canonical = alias_map.get(dimension, {}).get(raw_unit) or alias_map.get(dimension, {}).get(
            normalize_unit_token(raw_unit) if raw_unit else ""
        )
        if canonical:
            canonical_counts[canonical] += 1
    top_canonical_units = [unit for unit, _ in canonical_counts.most_common(10)]

    dimension_distribution = Counter(
        edge.get("dimension_label") or "UNKNOWN_DIMENSION"
        for edge in enriched_all
        if edge.get("numeric_status") in {"VALID_NORMALIZED", "RAW_NUMERIC_UNNORMALIZED", "UNRECOGNIZED_UNIT"}
    )
    total_numeric = sum(dimension_distribution.values()) or 1
    top_dimensions = [
        {
            "dimension_label": dim,
            "count": count,
            "pct_numeric": count / total_numeric,
        }
        for dim, count in dimension_distribution.most_common(8)
    ]

    # Build slot stats + consensus for current workspace using both KGs
    workspace_root = resolve_workspace_root()
    prior_slot_fill_rate = slot_fill_rate_from_index(workspace_root / "slot_consensus_index.json")
    workspace_edges = []
    slot_fill_rate = 0.0
    avg_cluster_size = 0.0
    avg_distinct_paper_count = 0.0
    avg_posterior_confidence = 0.0
    cluster_size_summary = {"count": 0}
    distinct_paper_summary = {"count": 0}
    multi_paper_support_pct = 0.0
    cross_paper_components = 0
    cross_paper_nodes = 0
    cross_paper_edges = 0
    for suffix in ("kg_edges.jsonl", "methodology_kg_edges.jsonl"):
        path = workspace_root / suffix
        if path.exists():
            workspace_edges.extend(list(iter_edges(path)))
    if workspace_edges:
        enriched_ws = [normalize_edge_numeric(edge) for edge in workspace_edges]
        apply_dimension_labels(enriched_ws, dimension_model)
        apply_unit_canonicalization(enriched_ws, alias_map)
        slot_stats = build_slot_stats(enriched_ws)
        slot_consensus, slot_stats_extra = build_slot_consensus(enriched_ws)
        if slot_consensus:
            total_slots = len(slot_consensus)
            filled = sum(1 for value in slot_consensus.values() if value.get("selected_value") is not None)
            slot_fill_rate = filled / total_slots if total_slots else 0.0
            posterior_scores = [entry.get("posterior_score", 0.0) for entry in slot_consensus.values()]
            avg_posterior_confidence = (sum(posterior_scores) / len(posterior_scores)) if posterior_scores else 0.0
        cluster_sizes = slot_stats_extra.get("cluster_sizes", [])
        distinct_papers = slot_stats_extra.get("distinct_paper_counts", [])
        cluster_size_summary = distribution_summary(cluster_sizes)
        distinct_paper_summary = distribution_summary(distinct_papers)
        avg_cluster_size = cluster_size_summary.get("mean", 0.0) if cluster_size_summary.get("count") else 0.0
        avg_distinct_paper_count = distinct_paper_summary.get("mean", 0.0) if distinct_paper_summary.get("count") else 0.0
        total_slots = slot_stats_extra.get("total_slots", 0) or 0
        multi_paper_slots = slot_stats_extra.get("multi_paper_slots", 0) or 0
        multi_paper_support_pct = (multi_paper_slots / total_slots) if total_slots else 0.0
        cross_paper_components = slot_stats_extra.get("cross_paper_components", 0)
        cross_paper_nodes = slot_stats_extra.get("cross_paper_nodes", 0)
        cross_paper_edges = slot_stats_extra.get("cross_paper_edges", 0)

    metrics["slot_fill_rate"] = slot_fill_rate
    metrics["avg_cluster_size"] = avg_cluster_size
    metrics["avg_distinct_paper_count"] = avg_distinct_paper_count
    metrics["avg_posterior_confidence"] = avg_posterior_confidence
    metrics["cluster_size_distribution"] = cluster_size_summary
    metrics["distinct_paper_count_distribution"] = distinct_paper_summary
    metrics["multi_paper_support_pct"] = multi_paper_support_pct
    metrics["cross_paper_graph"] = {
        "components": cross_paper_components,
        "nodes": cross_paper_nodes,
        "edges": cross_paper_edges,
    }
    metrics["dimension_distribution"] = dict(dimension_distribution)
    metrics["top_dimensions"] = top_dimensions
    if methodology_canon or full_canon:
        union = methodology_canon | full_canon
        inter = methodology_canon & full_canon
        stability = (len(inter) / len(union)) if union else 0.0
    else:
        stability = 0.0
    metrics["canonical_unit_stability"] = {
        "methodology_count": len(methodology_canon),
        "full_count": len(full_canon),
        "jaccard": stability,
    }

    append_private_metrics(
        run_id,
        {
            "total_edges": total_edges,
            "duplicate_ratio": (total_dups / total_edges) if total_edges else 0.0,
            "unit_diversity_count": unit_diversity_count,
            "canonical_unit_count": len(canonical_map),
            "unit_compression_ratio": unit_compression_ratio,
            "dimension_count": metrics["dimension_count"],
            "dimension_confident_edges_pct": metrics["dimension_confident_edges_pct"],
            "status_percent": {
                key: (count / total_edges) if total_edges else 0.0
                for key, count in status_totals.items()
            },
            "top_canonical_units": top_canonical_units,
            "slot_fill_rate": slot_fill_rate,
            "avg_cluster_size": avg_cluster_size,
            "avg_distinct_paper_count": avg_distinct_paper_count,
            "avg_posterior_confidence": avg_posterior_confidence,
            "multi_paper_support_pct": multi_paper_support_pct,
            "cross_paper_components": cross_paper_components,
        },
    )

    out_dir = args.out_dir
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        metrics_path = out_dir / "METRICS.json"
        previous_metrics = None
        if metrics_path.exists():
            try:
                previous_metrics = json.loads(metrics_path.read_text())
            except Exception:
                previous_metrics = None
        prior = extract_prior_metrics(previous_metrics)
        before_canonical = prior["canonical_unit_count"]
        before_slot_fill = prior["slot_fill_rate"]
        if before_slot_fill is None and prior_slot_fill_rate is not None:
            before_slot_fill = prior_slot_fill_rate
        before_dim_conf = prior["dimension_confident_edges_pct"]
        before_unit_comp = prior["unit_compression_ratio"]
        before_multi_paper = prior["multi_paper_support_pct"]
        before_cluster_median = prior["cluster_size_median"]
        canonical_compare = (
            f"{before_canonical} -> {metrics['canonical_unit_count']}"
            if before_canonical is not None
            else f"n/a -> {metrics['canonical_unit_count']}"
        )
        slot_compare = (
            f"{before_slot_fill:.4f} -> {metrics['slot_fill_rate']:.4f}"
            if isinstance(before_slot_fill, (int, float))
            else f"n/a -> {metrics['slot_fill_rate']:.4f}"
        )
        dim_compare = (
            f"{before_dim_conf:.4f} -> {metrics['dimension_confident_edges_pct']:.4f}"
            if isinstance(before_dim_conf, (int, float))
            else f"n/a -> {metrics['dimension_confident_edges_pct']:.4f}"
        )
        comp_compare = (
            f"{before_unit_comp:.4f} -> {metrics['unit_compression_ratio']:.4f}"
            if isinstance(before_unit_comp, (int, float))
            else f"n/a -> {metrics['unit_compression_ratio']:.4f}"
        )
        multi_compare = (
            f"{before_multi_paper:.4f} -> {metrics['multi_paper_support_pct']:.4f}"
            if isinstance(before_multi_paper, (int, float))
            else f"n/a -> {metrics['multi_paper_support_pct']:.4f}"
        )
        cluster_compare = (
            f"{before_cluster_median:.4f} -> {metrics['cluster_size_distribution'].get('median', 0.0):.4f}"
            if isinstance(before_cluster_median, (int, float))
            else f"n/a -> {metrics['cluster_size_distribution'].get('median', 0.0):.4f}"
        )

        improvements = []
        regressions = []
        if isinstance(before_dim_conf, (int, float)):
            (improvements if metrics["dimension_confident_edges_pct"] > before_dim_conf else regressions).append(
                "dimension_coverage"
            )
        if isinstance(before_unit_comp, (int, float)):
            (improvements if metrics["unit_compression_ratio"] > before_unit_comp else regressions).append(
                "unit_compression"
            )
        if isinstance(before_cluster_median, (int, float)):
            (improvements if metrics["cluster_size_distribution"].get("median", 0.0) > before_cluster_median else regressions).append(
                "cluster_median"
            )
        if isinstance(before_multi_paper, (int, float)):
            (improvements if metrics["multi_paper_support_pct"] > before_multi_paper else regressions).append(
                "multi_paper_support"
            )
        improved_flag = len(improvements) > 0

        metrics["comparison"] = {
            "canonical_unit_count": canonical_compare,
            "slot_fill_rate": slot_compare,
            "dimension_confident_edges_pct": dim_compare,
            "unit_compression_ratio": comp_compare,
            "cluster_size_median": cluster_compare,
            "multi_paper_support_pct": multi_compare,
            "improved": improved_flag,
            "improvements": improvements,
            "regressions": regressions,
        }

        metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
        log_artifact(run_id, str(metrics_path), "KG numeric audit metrics")

        top_dim_summary = ", ".join(
            [f"{d['dimension_label']}={d['pct_numeric']:.2f}" for d in top_dimensions]
        )
        summary_lines = [
            "**KG Numeric Audit Summary**",
            "- Pipeline snapshot:",
            "- Canonical units: `normalize_unit_token` + `build_unit_alias_map_by_dimension` (unicode normalize, casefold, punctuation stripping, symbol equivalence) grouped by `dimension_label`.",
            "- Dimension labels: `build_dimension_model` (token association from `relation_category` + local context) + `apply_dimension_model`; `UNKNOWN_DIMENSION` if confidence < p25 of label confidences.",
            "- Clustering: `cluster_numeric_values_adaptive` (median relative diff per slot).",
            "- Protocol routing (current): `gather_methodology_edges` → `_select_parameter_line` (VALID_NORMALIZED first, then RAW, scored by relevance, cluster_size, paper_diversity, section_priority, vector_score).",
            "- FAST_EMBED=1: `embed_texts` uses `hash_embed_texts` (token-hash bag-of-words) for contextual similarity; no embedding-based dimension inference.",
            f"- KG files scanned: {len(kg_files)}",
            f"- Total edges: {total_edges}",
            f"- Duplicate ratio (exact row): {(total_dups / total_edges) if total_edges else 0.0:.4f}",
            f"- Unit diversity (canonical): {unit_diversity_count}",
            f"- Dimension count: {metrics['dimension_count']}",
            f"- Dimension-confident edges (% of numeric): {metrics['dimension_confident_edges_pct']:.4f}",
            f"- Slot fill rate: {slot_fill_rate:.4f}",
            f"- Avg cluster size: {avg_cluster_size:.4f}",
            f"- Avg distinct paper count: {avg_distinct_paper_count:.4f}",
            f"- Avg posterior confidence: {avg_posterior_confidence:.4f}",
            f"- Canonical units (before -> after): {canonical_compare}",
            f"- Slot fill rate (before -> after): {slot_compare}",
            f"- Dimension-confident edges % (before -> after): {dim_compare}",
            f"- Unit compression ratio (before -> after): {comp_compare}",
            f"- Cluster median (before -> after): {cluster_compare}",
            f"- Multi-paper support % (before -> after): {multi_compare}",
            f"- Cross-paper graph components: {cross_paper_components} (nodes={cross_paper_nodes}, edges={cross_paper_edges})",
            f"- Canonical unit stability (methodology vs full Jaccard): {metrics['canonical_unit_stability']['jaccard']:.4f}",
            f"- Top dimensions coverage: {top_dim_summary}",
            "NUMERIC EXPLOITATION NOT IMPROVED — LOGIC FAILURE" if not improved_flag else f"- Improvements detected: {', '.join(improvements)}",
            "- Top 10 canonical units (by frequency):",
        ]
        summary_lines.extend([f"- {unit}" for unit in top_canonical_units])
        summary_path = out_dir / "SUMMARY.md"
        summary_path.write_text("\n".join(summary_lines) + "\n")
        log_artifact(run_id, str(summary_path), "KG numeric audit summary")

        pipeline_path = out_dir / "PIPELINE.mmd"
        pipeline_path.write_text(
            "\n".join(
                [
                    "graph TD",
                    "Q[Query]",
                    "K[Slot K: entity_anchor + relation_category + dimension_label + normalized_unit]",
                    "C[Selected Cluster]",
                    "E[Supporting Edges]",
                    "P[Supporting Papers]",
                    "Q --> K --> C --> E --> P",
                ]
            )
            + "\n"
        )
        log_artifact(run_id, str(pipeline_path), "Query-trace DAG")

    finalize_run(run_id, ["KG numeric audit completed"], None)


if __name__ == "__main__":
    main()
