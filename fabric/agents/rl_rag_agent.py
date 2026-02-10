#!/usr/bin/env python3
"""Lightweight RL-driven RAG agent over a topic-specific retrieval stack."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import random
import re
import sqlite3
import sys
import uuid
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional, Set, Literal, Union

import numpy as np

import typer
from pydantic import BaseModel, Field, ValidationError, TypeAdapter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services import local_llm
from services.retrieval_service import RetrievalBackend, get_backend, log_event
from utils.kg_schema_utils import (
    expected_entities_from_question,
    expand_query_with_schema,
    build_alias_lookup,
    load_schema,
    select_graph_seeds,
    topic_label,
)
from utils.workspace_utils import resolve_workspace_root  # noqa: E402
from utils.output_paths import logs_dir, qa_dir  # noqa: E402

LOG_PATH = logs_dir() / "rl_agent_runs.jsonl"
ACTIONS = ("vector_search", "graph_expand", "summarize", "stop")
DEFAULT_USE_LLM = os.environ.get("USE_LOCAL_LLM", "1") == "1"
VECTOR_ONLY_RAG = os.environ.get("VECTOR_ONLY_RAG", "0") == "1"
QA_OUTPUT_ROOT = qa_dir()

DEFAULT_TOP_K = int(os.environ.get("QA_DENSE_TOP_K", "20"))
DEFAULT_RRF_K = int(os.environ.get("QA_RRF_K", "60"))
DEFAULT_RERANK_TOP_K = int(os.environ.get("QA_RERANK_TOP_K", "40"))
DEFAULT_EVIDENCE_MAX_ITEMS = int(os.environ.get("QA_EVIDENCE_MAX_ITEMS", "12"))

ENTITY_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_-]{3,}\b")
NUM_UNIT_RE = re.compile(
    r"\b(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>degc|c|k|ph|%|mm|mM|um|uM|nm|nM|m|M|min|h|hr|hours|s|sec|rpm)\b",
    re.IGNORECASE,
)
STOPWORDS = {
    "the", "and", "with", "from", "that", "this", "were", "for", "into", "are", "their", "have", "has", "was", "also",
    "using", "used", "over", "after", "before", "between", "across", "when", "where", "which", "what", "who", "will",
    "can", "may", "such", "these", "those", "than", "then", "not", "but", "only", "more", "most", "less", "very", "some",
    "many", "much", "each", "per", "via", "within", "without", "out", "in", "on", "to", "of", "a", "an", "as", "is",
    "be", "by", "or", "at", "it", "its", "we", "our", "you", "your", "they", "them", "he", "she", "his", "her",
}

GENERIC_CANDIDATE_TERMS = {
    "candidate",
    "variant",
    "mutant",
    "esterase",
    "hydrolase",
    "cutinase",
    "engineering",
    "design",
    "approach",
    "method",
    "analysis",
}

UNIT_GROUPS = {
    "temp": {"°c", "c", "k"},
    "ph": {"ph"},
    "time": {"min", "h", "hr", "hours", "s", "sec"},
    "conc": {"m", "mm", "mm", "mM", "um", "uM", "nm", "nM"},
    "percent": {"%"},
    "rpm": {"rpm"},
}

CONNECTOR_PREFIXES = (
    "overall",
    "in summary",
    "in conclusion",
    "taken together",
    "collectively",
    "this suggests",
    "these results suggest",
    "in short",
    "top candidates",
    "type gate",
)

UNDERSTANDING_LAYER_MESSAGE = "understanding layer not built for this topic; run builder"

PLANNER_INTENTS = (
    "candidate_selection",
    "comparison",
    "fact_lookup",
    "limitations_or_gaps",
    "mechanism_explanation",
    "protocol_request",
    "evidence_audit",
    "other",
)

CLAIM_RELATIONS = (
    "improves",
    "reduces",
    "increases",
    "decreases",
    "stabilizes",
    "destabilizes",
    "improves_activity",
    "reduces_activity",
    "increases_stability",
    "reduces_stability",
    "improves_yield",
    "reduces_yield",
    "achieves",
    "fails_to",
    "compares_to",
    "limitation",
    "gap",
    "future_work",
    "uses_method",
    "assay_condition",
    "associated_with",
    "activates",
    "inhibits",
    "binds",
    "expressed_in",
)

DEFAULT_CLAIM_MAX_SENTENCES = 50
DEFAULT_CLAIM_MAX_ITEMS = 100
DEFAULT_CLAIM_MIN_ITEMS = 3
DEFAULT_CLAIM_CONFIDENCE = 0.55

CLAIM_METHOD_INTENTS = {"protocol_request", "mechanism_explanation"}

OUTPUT_MODES = ("answer_strict", "answer_helpful", "answer_dual", "protocol")

PHRASE_BANK = {
    "could_not_verify": [
        "I could not verify this from your corpus",
        "Not confirmed by the retrieved evidence",
        "Evidence in the corpus is insufficient to confirm",
        "Corpus coverage didn’t validate this yet",
    ],
    "next_steps": [
        "Add more targeted papers to the workspace",
        "Refine the query with specific targets/metrics",
        "Enable claims-lite persistence for future grounding",
        "Run the understanding-layer builder for this topic",
    ],
}

BANNED_RANK_TYPES = {
    "mutation",
    "mutations",
    "assay",
    "assays",
    "method",
    "methods",
    "paper",
    "papers",
}

EXCLUDE_PENALTY = 0.25


def get_workspace_root() -> Path:
    allow_noncanonical = os.environ.get("ALLOW_NONCANONICAL_WORKSPACE", "0") == "1"
    return resolve_workspace_root(allow_noncanonical=allow_noncanonical)


def get_text_dir() -> Path:
    return get_workspace_root() / "text"


def get_meta_dir() -> Path:
    return get_workspace_root() / "metadata"


class BlockSpec(BaseModel):
    type: Literal[
        "direct_answer",
        "ranked_entities",
        "caveats",
        "evidence_audit",
        "next_actions",
    ]
    entity_type: Optional[str] = None


class QuestionPlan(BaseModel):
    intent: Literal[
        "candidate_selection",
        "comparison",
        "fact_lookup",
        "limitations_or_gaps",
        "mechanism_explanation",
        "protocol_request",
        "evidence_audit",
        "other",
    ]
    required_blocks: List[BlockSpec]
    allowed_rank_entity_types: List[str]
    required_signals: List[str]
    retrieval_queries: List[str]
    exclude_patterns: List[str]
    abstain_conditions: List[str]


class DirectAnswerBullet(BaseModel):
    text: str
    citations: List[str] = Field(default_factory=list)


class DirectAnswerBlock(BaseModel):
    type: Literal["direct_answer"]
    bullets: List[DirectAnswerBullet]


class RankedEntityStats(BaseModel):
    evidence_count: int = 0
    papers_count: int = 0
    contradiction: bool = False


class RankedEntityItem(BaseModel):
    entity_id: Optional[str] = None
    display_name: str
    rationale: str
    supporting_evidence: List[str] = Field(default_factory=list)
    stats: RankedEntityStats


class RankedEntitiesBlock(BaseModel):
    type: Literal["ranked_entities"]
    entity_type: str
    items: List[RankedEntityItem]


class CaveatItem(BaseModel):
    text: str
    citations: List[str] = Field(default_factory=list)


class CaveatsBlock(BaseModel):
    type: Literal["caveats"]
    items: List[CaveatItem]


class EvidenceAuditBlock(BaseModel):
    type: Literal["evidence_audit"]
    what_is_available: List[str] = Field(default_factory=list)
    what_is_missing: List[str] = Field(default_factory=list)
    how_to_fix: List[str] = Field(default_factory=list)


class NextActionsBlock(BaseModel):
    type: Literal["next_actions"]
    items: List[str] = Field(default_factory=list)


BlockUnion = Union[DirectAnswerBlock, RankedEntitiesBlock, CaveatsBlock, EvidenceAuditBlock, NextActionsBlock]
BlocksAdapter = TypeAdapter(List[BlockUnion])


class ClaimEntity(BaseModel):
    entity_id: Optional[str] = None
    text: str


class Claim(BaseModel):
    claim_id: str
    topic: str
    paper_id: Optional[str] = None
    evidence_id: str
    subject: ClaimEntity
    relation: Literal[
        "improves",
        "reduces",
        "increases",
        "decreases",
        "stabilizes",
        "destabilizes",
        "improves_activity",
        "reduces_activity",
        "increases_stability",
        "reduces_stability",
        "improves_yield",
        "reduces_yield",
        "achieves",
        "fails_to",
        "compares_to",
        "limitation",
        "gap",
        "future_work",
        "uses_method",
        "assay_condition",
        "associated_with",
        "activates",
        "inhibits",
        "binds",
        "expressed_in",
    ]
    object: ClaimEntity
    qualifiers: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    canonicalized: bool


ClaimsAdapter = TypeAdapter(List[Claim])


class DraftDetailSection(BaseModel):
    title: str
    bullets: List[str]


class DraftAnswer(BaseModel):
    quick_answer: List[str]
    details_sections: Optional[List[DraftDetailSection]] = None
    assumptions: Optional[List[str]] = None
    questions_to_ground: Optional[List[str]] = None
    missing_to_verify: Optional[List[str]] = None
    next_steps: Optional[List[str]] = None


class GroundedBullet(BaseModel):
    text: str
    status: Literal["grounded", "partial", "inferred"]
    citations: List[str] = Field(default_factory=list)


class GroundedSection(BaseModel):
    title: str
    bullets: List[GroundedBullet]




@lru_cache(maxsize=1)
def load_pdf_titles() -> Dict[str, str]:
    titles: Dict[str, str] = {}
    meta_dir = get_meta_dir()
    if meta_dir.exists():
        for meta_file in meta_dir.glob("*.json"):
            try:
                data = json.loads(meta_file.read_text())
            except Exception:
                continue
            pdf = data.get("pdf_file")
            title = data.get("title_candidate") or meta_file.stem
            if pdf:
                titles[pdf] = title
    return titles


@lru_cache(maxsize=1)
def load_pdf_metadata() -> Dict[str, Dict[str, Any]]:
    meta: Dict[str, Dict[str, Any]] = {}
    meta_dir = get_meta_dir()
    if meta_dir.exists():
        for meta_file in meta_dir.glob("*.json"):
            try:
                data = json.loads(meta_file.read_text())
            except Exception:
                continue
            pdf = data.get("pdf_file")
            if pdf:
                meta[pdf] = data
    return meta


def _extract_doi(text: str) -> Optional[str]:
    if not text:
        return None
    match = re.search(r"(10\\.[0-9]{4,9}/[A-Z0-9._;()/:\\-]+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).rstrip(").,;")
    return None


def _extract_year(text: str) -> Optional[int]:
    if not text:
        return None
    match = re.search(r"\\b(19|20)\\d{2}\\b", text)
    if match:
        return int(match.group(0))
    return None


def _guess_authors_from_text(txt_path: Path) -> Optional[str]:
    if not txt_path.exists():
        return None
    try:
        head = txt_path.read_text(encoding="utf-8", errors="ignore").splitlines()[:40]
    except Exception:
        return None
    for line in head:
        clean = line.strip()
        if not clean or len(clean) > 180:
            continue
        lowered = clean.lower()
        if any(token in lowered for token in ("abstract", "introduction", "keywords", "frontiers", "journal")):
            continue
        if clean.count(",") >= 2 and any(ch.isalpha() for ch in clean):
            return clean
    return None


def _guess_authors_from_title(title: str | None) -> Optional[str]:
    if not title:
        return None
    cleaned = " ".join(title.split())
    match = re.match(r"^([A-Z][A-Za-z'-]+(?:\\s+[A-Z][A-Za-z'-]+)*)\\s+et\\s+al", cleaned)
    if match:
        return f"{match.group(1)} et al."
    match = re.match(r"^([A-Z][^,]{2,80})\\s*,", cleaned)
    if match:
        return match.group(1).strip()
    return None


def _clean_title_candidate(title: str | None) -> Optional[str]:
    if not title:
        return None
    cleaned = " ".join(title.split())
    lowered = cleaned.lower()
    if len(cleaned) < 8:
        return None
    if re.fullmatch(r"[\\d\\W]+", cleaned):
        return None
    if "vol.:(" in lowered or lowered.startswith(("vol.", "issue", "article")):
        return None
    return cleaned


def _guess_title_from_text(txt_path: Path) -> Optional[str]:
    if not txt_path.exists():
        return None
    try:
        lines = txt_path.read_text(encoding="utf-8", errors="ignore").splitlines()[:60]
    except Exception:
        return None
    for line in lines:
        clean = " ".join(line.strip().split())
        lowered = clean.lower()
        if not clean or len(clean) < 12:
            continue
        if any(token in lowered for token in ("abstract", "introduction", "keywords", "correspondence")):
            continue
        if re.search(r"\\bvol\\.|\\bissue\\b", lowered):
            continue
        if clean.count(",") >= 3:
            continue
        if len(clean.split()) >= 6:
            return clean
    return None


def _extract_doi_from_text_file(txt_path: Path) -> Optional[str]:
    if not txt_path.exists():
        return None
    try:
        snippet = txt_path.read_text(encoding="utf-8", errors="ignore")[:8000]
    except Exception:
        return None
    return _extract_doi(snippet)


def resolve_citation_fields(paper: str | None, snippet: str | None = None) -> Dict[str, Any]:
    meta = load_pdf_metadata()
    data = meta.get(paper or "", {})
    raw_title = data.get("title_candidate")
    title = _clean_title_candidate(raw_title)
    doi = data.get("doi") or _extract_doi(snippet or "")
    year = data.get("year") or _extract_year(title or "")
    authors = data.get("authors")
    txt_file = data.get("txt_file")
    if txt_file:
        txt_path = get_text_dir() / txt_file
    else:
        txt_path = None
    if not doi and txt_path:
        doi = _extract_doi_from_text_file(txt_path)
    if not year and txt_path:
        year = _extract_year(txt_path.read_text(encoding="utf-8", errors="ignore")[:2000])
    if not title and txt_path:
        title = _guess_title_from_text(txt_path)
    if not title:
        title = resolve_title(paper)
    if not authors:
        authors = _guess_authors_from_title(title)
    if not authors and txt_path:
        authors = _guess_authors_from_text(txt_path)
    return {
        "title": title,
        "doi": doi,
        "year": year,
        "authors": authors,
    }


def _safe_json_loads(raw: str) -> Dict[str, Any]:
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw[start : end + 1])
        raise


def _safe_json_list(raw: str) -> List[Any]:
    raw = (raw or "").strip()
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw[start : end + 1])
        raise


def _repair_blocks_json(raw: str, question: str, topic: str, plan: QuestionPlan) -> Optional[str]:
    if not raw:
        return None
    repair_prompt = (
        "You are fixing invalid JSON produced by a structured answer composer.\n"
        "Return ONLY valid JSON: a list of block objects.\n"
        "Schema summary:\n"
        "- DirectAnswerBlock: {\"type\":\"direct_answer\",\"bullets\":[{\"text\":string,\"citations\":[evidence_id]}]}\n"
        "- RankedEntitiesBlock: {\"type\":\"ranked_entities\",\"entity_type\":string,\"items\":[{\"display_name\":string,\"rationale\":string,\"supporting_evidence\":[evidence_id]}]}\n"
        "- CaveatsBlock: {\"type\":\"caveats\",\"bullets\":[string]}\n"
        "- EvidenceAuditBlock: {\"type\":\"evidence_audit\",\"what_is_available\":[string],\"what_is_missing\":[string],\"how_to_fix\":[string]}\n"
        "- NextActionsBlock: {\"type\":\"next_actions\",\"actions\":[string]}\n"
        "Constraints:\n"
        f"- Required blocks: {[spec.type for spec in plan.required_blocks or []]}\n"
        f"- Allowed rank entity types: {plan.allowed_rank_entity_types}\n"
        f"- Required signals: {plan.required_signals}\n"
        "If evidence is insufficient, return EvidenceAuditBlock only.\n"
        f"Question: {question}\n"
        f"Topic: {topic}\n"
        "Invalid JSON payload:\n"
        f"{raw}\n"
    )
    try:
        return local_llm.generate(repair_prompt, system_prompt="Return JSON only.")
    except Exception:
        return None


def list_available_entity_types(schema: Dict[str, Any]) -> List[str]:
    type_map = {
        "key_entities": "entity",
        "substrates": "substrate",
        "products": "product",
        "metrics": "metric",
        "conditions": "condition",
        "hosts": "host",
        "assays": "assay",
    }
    types: List[str] = []
    for key, label in type_map.items():
        values = schema.get(key) or []
        if values:
            types.append(label)
    if not types:
        return ["entity"]
    return types


def _default_exclude_patterns() -> List[str]:
    return [
        "Received:",
        "Accepted:",
        "Academic Editor:",
        "Correspondence:",
        "Supplementary",
        "Acknowledg",
        "Funding",
        "Conflict of interest",
        "Author contributions",
        "Data availability",
        "Ethics statement",
        "Publisher's note",
        "Copyright",
    ]


def _fallback_plan(
    question: str,
    schema: Dict[str, Any],
    session_state: Dict[str, Any],
) -> QuestionPlan:
    base = expand_query_with_schema(question, schema)
    topic = topic_label(schema, get_workspace_root())
    retrieval_queries = [base]
    entity_memory = session_state.get("entity_memory", []) or []
    if entity_memory:
        retrieval_queries.append(f"{topic} " + " ".join(entity_memory[:6]))
    allowed_types = [t for t in list_available_entity_types(schema) if t not in BANNED_RANK_TYPES]
    required_signals: List[str] = []
    lowered = question.lower()
    if any(token in lowered for token in ("condition", "conditions", "hydrolysis", "assay", "reaction")):
        required_signals = [
            "temperature",
            "pH",
            "buffer",
            "time",
            "enzyme_loading",
            "substrate_form",
            "products",
            "product_yield",
            "kinetic_metrics",
            "host_expression_system",
            "variant_comparison",
            "optimal_conditions",
            "limitations",
        ]
    return QuestionPlan(
        intent="other",
        required_blocks=[BlockSpec(type="evidence_audit")],
        allowed_rank_entity_types=allowed_types,
        required_signals=required_signals,
        retrieval_queries=[q for q in retrieval_queries if q],
        exclude_patterns=_default_exclude_patterns(),
        abstain_conditions=["planner_invalid"],
    )


def plan_question(
    question: str,
    schema: Dict[str, Any],
    session_state: Dict[str, Any],
    use_llm: bool,
) -> Tuple[QuestionPlan, bool, str | None, str | None]:
    topic = topic_label(schema, get_workspace_root())
    available_types = list_available_entity_types(schema)
    if not use_llm:
        return _fallback_plan(question, schema, session_state), False, None, "planner_disabled"
    lowered = question.lower()
    condition_signal_hint = ""
    if any(token in lowered for token in ("condition", "conditions", "hydrolysis", "assay", "reaction")):
        condition_signal_hint = (
            "If the user asks about reaction or hydrolysis conditions, include required_signals for:\n"
            "- temperature, pH, buffer, time, enzyme loading\n"
            "- substrate form (film/powder/crystallinity/particle size)\n"
            "- products (MHET, BHET, TPA, EG) and yields/ratios\n"
            "- kinetic or performance metrics (rate, % conversion, activity, turnover)\n"
            "- host/expression system when tied to conditions\n"
            "- variant comparisons only if they affect conditions/outcomes\n"
            "- optimal vs non-optimal conditions and explicit limitations\n"
        )
    prompt = (
        "You are a Question Planner for a retrieval QA system.\n"
        "Return ONLY valid JSON that matches this schema:\n"
        "{\n"
        f"  \"intent\": one of {list(PLANNER_INTENTS)},\n"
        "  \"required_blocks\": [{\"type\": one of [direct_answer, ranked_entities, caveats, evidence_audit, next_actions], \"entity_type\": optional string}],\n"
        "  \"allowed_rank_entity_types\": list of entity types,\n"
        "  \"required_signals\": list of semantic signals,\n"
        "  \"retrieval_queries\": list of search queries,\n"
        "  \"exclude_patterns\": list of strings to penalize,\n"
        "  \"abstain_conditions\": list of conditions\n"
        "}\n\n"
        f"Topic: {topic}\n"
        f"User query: {question}\n"
        f"Available entity types: {available_types}\n"
        f"Session entity_memory: {session_state.get('entity_memory', [])}\n"
        f"Session rolling_summary: {session_state.get('rolling_summary', '')[:400]}\n"
        f"Session working_set_entities: {session_state.get('working_set_entities', [])}\n"
        f"Session open_slots: {session_state.get('open_slots', [])}\n"
        f"Session last_intent: {session_state.get('last_intent', '')}\n"
        "Planner rules:\n"
        "- retrieval_queries MUST be non-empty.\n"
        "- Use exclude_patterns for boilerplate sections.\n"
        "- If unsure, include EvidenceAuditBlock in required_blocks.\n"
        "- Do not include banned types (mutation, assay, method, paper) in allowed_rank_entity_types.\n"
        + condition_signal_hint
    )
    raw = None
    try:
        raw = local_llm.generate(prompt, system_prompt="Return JSON only.")
        payload = _safe_json_loads(raw)
        plan = QuestionPlan.model_validate(payload)
        if not plan.retrieval_queries:
            raise ValueError("planner returned empty retrieval_queries")
        if condition_signal_hint:
            extra_queries = [
                f"{topic} PETase hydrolysis temperature pH buffer time enzyme loading",
                f"{topic} PETase MHET BHET TPA EG products yield conversion rate",
                f"{topic} PETase substrate film powder crystallinity particle size",
            ]
            for q in extra_queries:
                if q not in plan.retrieval_queries:
                    plan.retrieval_queries.append(q)
        return plan, True, raw, None
    except Exception as exc:
        return _fallback_plan(question, schema, session_state), False, raw, str(exc)


def resolve_title(pdf_file: str | None) -> str:
    if not pdf_file:
        return "Unknown source"
    title = load_pdf_titles().get(pdf_file)
    if title:
        return title
    try:
        return Path(pdf_file).stem
    except Exception:
        return str(pdf_file)


def _normalize_unit(unit: str) -> str:
    lowered = unit.lower()
    for group, units in UNIT_GROUPS.items():
        if lowered in {u.lower() for u in units}:
            return group
    return lowered


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part for part in (p.strip() for p in parts) if part]


def extract_entities(text: str) -> List[str]:
    entities = []
    for token in ENTITY_RE.findall(text):
        lowered = token.lower()
        if lowered in STOPWORDS:
            continue
        if token.isdigit():
            continue
        entities.append(token)
    return entities


def extract_conditions(text: str) -> List[str]:
    conditions = []
    for match in NUM_UNIT_RE.finditer(text):
        val = match.group("val")
        unit = match.group("unit")
        conditions.append(f"{val}{unit}")
    return conditions


def coverage_proxy(text: str) -> int:
    entities = extract_entities(text)
    conditions = extract_conditions(text)
    return len(set(entities + conditions))


def is_connector_sentence(sentence: str) -> bool:
    lowered = sentence.strip().lower()
    return any(lowered.startswith(prefix) for prefix in CONNECTOR_PREFIXES)


def build_sentence_map(answer: str, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    body = answer.split("Sources:", 1)[0]
    sentences = _split_sentences(body)
    id_to_sources = {}
    for entry in citations:
        cid = entry.get("id")
        source_ids = entry.get("source_ids") or [entry.get("source_id")] if entry.get("source_id") else []
        if cid is not None:
            id_to_sources[int(cid)] = [sid for sid in source_ids if sid]

    mapped = []
    for sent in sentences:
        ids = [int(cid) for cid in re.findall(r"\[(\d+)\]", sent)]
        source_ids = []
        for cid in ids:
            source_ids.extend(id_to_sources.get(cid, []))
        supported = bool(source_ids)
        connector = is_connector_sentence(sent)
        mapped.append({
            "sentence": sent,
            "citation_ids": ids,
            "source_ids": source_ids,
            "supported": supported,
            "connector": connector,
            "label": "supported" if supported or connector else "unsupported",
        })
    return mapped


def detect_intent(question: str) -> str:
    lowered = question.lower()
    compare_markers = ["compare", "versus", "vs", "better than", "relative to"]
    selection_markers = [
        "top candidate", "top candidates", "starting point", "starting points",
        "shortlist", "rank", "ranking", "best candidates", "prioritize", "which candidates",
    ]
    limitations_markers = ["limitation", "limitations", "failure", "failed", "future work", "future directions", "gaps", "caveat"]

    if any(marker in lowered for marker in compare_markers):
        return "compare_candidates"
    if any(marker in lowered for marker in selection_markers):
        return "candidate_selection"
    if any(marker in lowered for marker in limitations_markers):
        return "paper_limitations"
    return "fact_qa"


def understanding_layer_status(workspace_root: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    report_path = workspace_root / "reports" / "reasoning_graph.json"
    if not report_path.exists():
        return None, "missing"
    try:
        data = json.loads(report_path.read_text())
    except Exception:
        return None, "unreadable"

    text_dir = workspace_root / "text"
    latest_text = 0.0
    if text_dir.exists():
        for txt_path in text_dir.glob("*.txt"):
            try:
                latest_text = max(latest_text, txt_path.stat().st_mtime)
            except Exception:
                continue
    try:
        if latest_text and report_path.stat().st_mtime < latest_text:
            return None, "stale"
    except Exception:
        return None, "unreadable"
    return data, None


def _index_papers(layer: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    papers = {}
    for entry in layer.get("papers", []):
        if entry.get("paper_id"):
            papers[entry["paper_id"]] = entry
    return papers


def _collect_candidate_links(layer: Dict[str, Any], candidate_id: str) -> Dict[str, List[str]]:
    evidence_ids = []
    objective_ids = []
    intervention_ids = []
    for link in layer.get("links", []):
        if link.get("candidate_id") != candidate_id:
            continue
        if link.get("type") == "candidate_supported_by_evidence":
            evidence_ids.append(link.get("evidence_id"))
        elif link.get("type") == "candidate_evaluated_for_objective":
            objective_ids.append(link.get("objective_id"))
        elif link.get("type") == "intervention_produces_candidate":
            intervention_ids.append(link.get("intervention_id"))
    return {
        "evidence_ids": [eid for eid in evidence_ids if eid],
        "objective_ids": [oid for oid in objective_ids if oid],
        "intervention_ids": [iid for iid in intervention_ids if iid],
    }


def _match_candidates(question: str, ranked: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    lowered = question.lower()
    matched = []
    for cand in ranked:
        name = str(cand.get("name") or "").lower()
        if name and name in lowered:
            matched.append(cand)
    return matched


def render_candidate_response(layer: Dict[str, Any], question: str, limit: int = 5) -> Tuple[str, List[Dict[str, Any]]]:
    ranked = layer.get("rankings", {}).get("candidates", []) or []
    ranked_candidates = [cand for cand in ranked if cand.get("entity_type") == "candidate"]
    if not ranked_candidates:
        return "No candidates available in understanding layer.", []

    suffix_re = re.compile(r"(ase|enzyme|protein|system|protocol|strain|construct|cutinase|hydrolase)$", re.IGNORECASE)

    def is_candidate_name(name: str) -> bool:
        lowered = name.lower()
        if lowered in STOPWORDS or lowered in GENERIC_CANDIDATE_TERMS:
            return False
        if lowered in {"enzyme", "protein", "system", "protocol", "strain", "construct"}:
            return False
        if re.fullmatch(r"[A-Z]\d{1,4}[A-Z]", name):
            return False
        if suffix_re.search(name):
            return True
        if "-" in name and any(ch.isalpha() for ch in name):
            return True
        if any(ch.isupper() for ch in name) and any(ch.islower() for ch in name):
            return True
        if name.isupper() and len(name) >= 5:
            return True
        if any(ch.isdigit() for ch in name) and any(ch.isalpha() for ch in name) and len(name) >= 4:
            return True
        return False

    def question_has_specific_candidate_token(text: str) -> bool:
        tokens = re.findall(r"[A-Za-z0-9_-]{3,}", text)
        for token in tokens:
            if "-" in token:
                return True
            if any(ch.isdigit() for ch in token):
                return True
            if token.isupper() and len(token) >= 3:
                return True
            if any(ch.isupper() for ch in token[1:]):
                return True
            if token.lower().endswith("ase") and len(token) >= 5:
                return True
        return False

    def select_with_evidence(candidates: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, List[str]]]]:
        selected_items = []
        seen_names: set[str] = set()
        for cand in candidates:
            name = str(cand.get("name") or "")
            if not name:
                continue
            name_key = name.lower()
            if name_key in seen_names:
                continue
            cand_id = cand.get("entity_id")
            link_ids = _collect_candidate_links(layer, cand_id)
            if not link_ids["evidence_ids"]:
                continue
            selected_items.append((cand, link_ids))
            seen_names.add(name_key)
            if len(selected_items) >= limit:
                break
        return selected_items

    filtered = [cand for cand in ranked_candidates if is_candidate_name(str(cand.get("name") or ""))]
    matched = _match_candidates(question, ranked_candidates) if question_has_specific_candidate_token(question) else []
    matched = [cand for cand in matched if is_candidate_name(str(cand.get("name") or ""))]

    selected_items = select_with_evidence(matched) if matched else []
    if not selected_items:
        selected_items = select_with_evidence(filtered)
    if not selected_items:
        return "No candidates with validated evidence available in understanding layer.", []

    evidence_map = {e["entity_id"]: e for e in layer.get("entities", {}).get("evidence", [])}
    reflection_map = {e["entity_id"]: e for e in layer.get("entities", {}).get("reflections", [])}
    intervention_map = {e["entity_id"]: e for e in layer.get("entities", {}).get("interventions", [])}
    objective_map = {e["entity_id"]: e for e in layer.get("entities", {}).get("objectives", [])}
    paper_map = _index_papers(layer)

    citations: List[Dict[str, Any]] = []
    citation_index: Dict[str, int] = {}

    def register(source_id: str, paper_id: str) -> int:
        if source_id not in citation_index:
            citation_index[source_id] = len(citations) + 1
            paper_title = paper_map.get(paper_id, {}).get("title") or paper_id
            citations.append({
                "id": citation_index[source_id],
                "paper": paper_id,
                "title": paper_title,
                "source_id": source_id,
                "source_ids": [source_id],
            })
        return citation_index[source_id]

    lines = ["Top candidates (understanding layer, candidate-only ranking):"]
    for idx, (cand, link_ids) in enumerate(selected_items, start=1):
        cand_id = cand.get("entity_id")
        name = cand.get("name")
        stats = (
            f"evidence={cand.get('evidence_count')}, papers={cand.get('paper_count')}, "
            f"replication={cand.get('replication_count')}, context_diversity={cand.get('context_diversity')}, "
            f"contradiction={cand.get('contradiction_flags')}"
        )
        evidence_ids = link_ids["evidence_ids"][:3]
        cite_tags = []
        for evidence_id in evidence_ids:
            evidence = evidence_map.get(evidence_id, {})
            paper_id = evidence.get("paper_id", "unknown")
            cite_tags.append(f"[{register(evidence_id, paper_id)}]")
        citation_blob = " ".join(cite_tags)
        lines.append(f"{idx}. {name} — {stats} {citation_blob}".strip())

        objectives = [objective_map[obj_id]["name"] for obj_id in link_ids["objective_ids"] if obj_id in objective_map]
        if objectives:
            lines.append(f"   objectives: {', '.join(sorted(set(objectives)))}")

        intervention_details = []
        for int_id in link_ids["intervention_ids"]:
            intervention = intervention_map.get(int_id)
            if not intervention:
                continue
            priors = intervention.get("priors") or {}
            detail = intervention.get("intervention_type") or intervention.get("name")
            if any(priors.values()):
                detail += f" (priors: {priors})"
            intervention_details.append(detail)
        if intervention_details:
            lines.append(f"   interventions/details: {', '.join(intervention_details)}")

        caveats = []
        for ref_id in cand.get("caveats", [])[:2]:
            ref = reflection_map.get(ref_id)
            if not ref:
                continue
            paper_id = ref.get("paper_id", "unknown")
            cite_tag = f"[{register(ref_id, paper_id)}]"
            caveats.append(f"{ref.get('category')}: {ref.get('name')} {cite_tag}")
        if caveats:
            lines.append(f"   caveats: {'; '.join(caveats)}")

    lines.append("Type gate enforced: ranked items are candidates only; interventions listed under details.")

    if citations:
        lines.append("")
        lines.append("Sources:")
        for citation in citations:
            lines.append(f"[{citation['id']}] {citation['title']} ({citation['paper']}) {citation['source_id']}")

    return "\n".join(lines), citations


def build_candidate_blocks(
    layer: Dict[str, Any],
    question: str,
    plan: QuestionPlan,
    limit: int = 5,
) -> Tuple[List[BlockUnion], List[Dict[str, Any]], Dict[str, int]]:
    ranked = layer.get("rankings", {}).get("candidates", []) or []
    ranked_candidates = [cand for cand in ranked if cand.get("entity_type") == "candidate"]
    if not ranked_candidates:
        audit = build_evidence_audit([], plan, reason="no_candidates")
        return [audit], [], {}

    suffix_re = re.compile(r"(ase|enzyme|protein|system|protocol|strain|construct|cutinase|hydrolase)$", re.IGNORECASE)

    def is_candidate_name(name: str) -> bool:
        lowered = name.lower()
        if lowered in STOPWORDS or lowered in GENERIC_CANDIDATE_TERMS:
            return False
        if lowered in {"enzyme", "protein", "system", "protocol", "strain", "construct"}:
            return False
        if re.fullmatch(r"[A-Z]\d{1,4}[A-Z]", name):
            return False
        if suffix_re.search(name):
            return True
        if "-" in name and any(ch.isalpha() for ch in name):
            return True
        if any(ch.isupper() for ch in name) and any(ch.islower() for ch in name):
            return True
        if name.isupper() and len(name) >= 5:
            return True
        if any(ch.isdigit() for ch in name) and any(ch.isalpha() for ch in name) and len(name) >= 4:
            return True
        return False

    def question_has_specific_candidate_token(text: str) -> bool:
        tokens = re.findall(r"[A-Za-z0-9_-]{3,}", text)
        for token in tokens:
            if "-" in token:
                return True
            if any(ch.isdigit() for ch in token):
                return True
            if token.isupper() and len(token) >= 3:
                return True
            if any(ch.isupper() for ch in token[1:]):
                return True
            if token.lower().endswith("ase") and len(token) >= 5:
                return True
        return False

    def select_with_evidence(candidates: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, List[str]]]]:
        selected_items = []
        seen_names: set[str] = set()
        for cand in candidates:
            name = str(cand.get("name") or "")
            if not name:
                continue
            name_key = name.lower()
            if name_key in seen_names:
                continue
            cand_id = cand.get("entity_id")
            link_ids = _collect_candidate_links(layer, cand_id)
            if not link_ids["evidence_ids"]:
                continue
            selected_items.append((cand, link_ids))
            seen_names.add(name_key)
            if len(selected_items) >= limit:
                break
        return selected_items

    filtered = [cand for cand in ranked_candidates if is_candidate_name(str(cand.get("name") or ""))]
    matched = _match_candidates(question, ranked_candidates) if question_has_specific_candidate_token(question) else []
    matched = [cand for cand in matched if is_candidate_name(str(cand.get("name") or ""))]

    selected_items = select_with_evidence(matched) if matched else []
    if not selected_items:
        selected_items = select_with_evidence(filtered)
    if not selected_items:
        audit = build_evidence_audit([], plan, reason="no_ranked_candidates_with_evidence")
        return [audit], [], {}

    evidence_map = {e["entity_id"]: e for e in layer.get("entities", {}).get("evidence", [])}
    reflection_map = {e["entity_id"]: e for e in layer.get("entities", {}).get("reflections", [])}
    paper_map = _index_papers(layer)

    citations: List[Dict[str, Any]] = []
    evidence_to_citation: Dict[str, int] = {}

    def register(source_id: str, paper_id: str) -> int:
        if source_id not in evidence_to_citation:
            evidence_to_citation[source_id] = len(citations) + 1
            paper_title = paper_map.get(paper_id, {}).get("title") or paper_id
            citations.append(
                {
                    "id": evidence_to_citation[source_id],
                    "paper": paper_id,
                    "title": paper_title,
                    "source_id": source_id,
                    "source_ids": [source_id],
                }
            )
        return evidence_to_citation[source_id]

    items: List[RankedEntityItem] = []
    caveats: List[CaveatItem] = []
    for cand, link_ids in selected_items:
        name = cand.get("name") or cand.get("entity_id") or "candidate"
        evidence_ids = link_ids["evidence_ids"][:3]
        for evidence_id in evidence_ids:
            evidence = evidence_map.get(evidence_id, {})
            paper_id = evidence.get("paper_id", "unknown")
            register(evidence_id, paper_id)
        stats = RankedEntityStats(
            evidence_count=int(cand.get("evidence_count") or 0),
            papers_count=int(cand.get("paper_count") or 0),
            contradiction=False,
        )
        rationale = f"evidence={stats.evidence_count}, papers={stats.papers_count}"
        items.append(
            RankedEntityItem(
                entity_id=cand.get("entity_id"),
                display_name=str(name),
                rationale=rationale,
                supporting_evidence=evidence_ids,
                stats=stats,
            )
        )
        for ref_id in cand.get("caveats", [])[:2]:
            ref = reflection_map.get(ref_id)
            if not ref:
                continue
            paper_id = ref.get("paper_id", "unknown")
            register(ref_id, paper_id)
            caveats.append(
                CaveatItem(
                    text=ref.get("name") or ref.get("summary") or "Caveat reported in evidence.",
                    citations=[ref_id],
                )
            )

    blocks: List[BlockUnion] = [
        RankedEntitiesBlock(type="ranked_entities", entity_type="candidate", items=items)
    ]
    if caveats:
        blocks.append(CaveatsBlock(type="caveats", items=caveats))
    return blocks, citations, evidence_to_citation


def build_reflection_blocks(
    layer: Dict[str, Any],
    plan: QuestionPlan,
    limit: int = 20,
) -> Tuple[List[BlockUnion], List[Dict[str, Any]], Dict[str, int]]:
    reflections = layer.get("entities", {}).get("reflections", [])
    if not reflections:
        audit = build_evidence_audit([], plan, reason="no_reflections")
        return [audit], [], {}
    paper_map = _index_papers(layer)
    citations: List[Dict[str, Any]] = []
    evidence_to_citation: Dict[str, int] = {}

    def register(source_id: str, paper_id: str) -> int:
        if source_id not in evidence_to_citation:
            evidence_to_citation[source_id] = len(citations) + 1
            paper_title = paper_map.get(paper_id, {}).get("title") or paper_id
            citations.append(
                {
                    "id": evidence_to_citation[source_id],
                    "paper": paper_id,
                    "title": paper_title,
                    "source_id": source_id,
                    "source_ids": [source_id],
                }
            )
        return evidence_to_citation[source_id]

    items: List[CaveatItem] = []
    for ref in reflections[:limit]:
        ref_id = ref.get("entity_id")
        paper_id = ref.get("paper_id", "unknown")
        if ref_id:
            register(ref_id, paper_id)
        text = f"{ref.get('category')}: {ref.get('name')}".strip()
        items.append(CaveatItem(text=text, citations=[ref_id] if ref_id else []))

    blocks: List[BlockUnion] = [CaveatsBlock(type="caveats", items=items)]
    return blocks, citations, evidence_to_citation


def render_limitations_response(layer: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    reflections = layer.get("entities", {}).get("reflections", [])
    paper_map = _index_papers(layer)

    citations: List[Dict[str, Any]] = []
    citation_index: Dict[str, int] = {}

    def register(source_id: str, paper_id: str) -> int:
        if source_id not in citation_index:
            citation_index[source_id] = len(citations) + 1
            paper_title = paper_map.get(paper_id, {}).get("title") or paper_id
            citations.append({
                "id": citation_index[source_id],
                "paper": paper_id,
                "title": paper_title,
                "source_id": source_id,
                "source_ids": [source_id],
            })
        return citation_index[source_id]

    lines = ["Paper reflections (limitations, failures, future directions):"]
    for ref in reflections[:20]:
        paper_id = ref.get("paper_id", "unknown")
        tag = f"[{register(ref.get('entity_id'), paper_id)}]"
        lines.append(f"- {ref.get('category')}: {ref.get('name')} {tag}")

    if citations:
        lines.append("")
        lines.append("Sources:")
        for citation in citations:
            lines.append(f"[{citation['id']}] {citation['title']} ({citation['paper']}) {citation['source_id']}")

    return "\n".join(lines), citations


def unsupported_sentence_rate(answer: str) -> float:
    body = answer.split("Sources:", 1)[0]
    sents = _split_sentences(body)
    if not sents:
        return 1.0
    unsupported = 0
    for sent in sents:
        if not re.search(r"\[\d+\]", sent):
            unsupported += 1
    return unsupported / len(sents)


def unsupported_sentence_rate_from_map(sentence_map: List[Dict[str, Any]]) -> float:
    if not sentence_map:
        return 1.0
    unsupported = [s for s in sentence_map if s.get("label") == "unsupported"]
    return len(unsupported) / len(sentence_map)


def contradiction_proxy(answer: str) -> int:
    body = answer.split("Sources:", 1)[0]
    buckets: Dict[str, List[float]] = {}
    for match in NUM_UNIT_RE.finditer(body):
        val = float(match.group("val"))
        unit = _normalize_unit(match.group("unit"))
        buckets.setdefault(unit, []).append(val)
    contradictions = 0
    for unit, vals in buckets.items():
        if len(vals) < 2:
            continue
        vmin, vmax = min(vals), max(vals)
        if unit == "ph":
            if vmax - vmin >= 1.0:
                contradictions += 1
        elif unit == "temp":
            if vmax - vmin >= 10.0:
                contradictions += 1
        elif unit == "time":
            if vmin > 0 and (vmax / vmin) >= 2.0:
                contradictions += 1
        elif unit == "conc":
            if vmin > 0 and (vmax / vmin) >= 10.0:
                contradictions += 1
        elif unit == "percent":
            if vmax - vmin >= 20.0:
                contradictions += 1
        elif unit == "rpm":
            if vmax - vmin >= 200.0:
                contradictions += 1
        else:
            if vmax - vmin >= 5.0:
                contradictions += 1
    return contradictions


def citation_concentration(answer: str) -> float:
    body = answer.split("Sources:", 1)[0]
    ids = re.findall(r"\[(\d+)\]", body)
    if not ids:
        return 1.0
    counts = {}
    for cid in ids:
        counts[cid] = counts.get(cid, 0) + 1
    total = sum(counts.values())
    return (max(counts.values()) / total) if total else 1.0


def generate_session_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class AgentState:
    question: str
    context: List[Dict[str, Any]] = field(default_factory=list)
    graph_nodes: List[Dict[str, Any]] = field(default_factory=list)
    steps: int = 0


def state_to_observation(state: AgentState | None) -> np.ndarray:
    if state is None:
        return np.zeros(3, dtype=np.float32)
    context = min(len(state.context), 10) / 10.0
    graph = min(len(state.graph_nodes), 10) / 10.0
    steps = min(state.steps, 12) / 12.0
    return np.array([context, graph, steps], dtype=np.float32)


class RetrievalEnvironment:
    def __init__(
        self,
        backend: RetrievalBackend,
        schema: Dict[str, Any],
        graph_overview_path: Path,
        max_steps: int = 12,
        use_judge: bool = False,
        judge_mode: str = "similarity",
    ) -> None:
        self.backend = backend
        self.schema = schema
        self.graph_overview_path = graph_overview_path
        self.max_steps = max_steps
        self.state: AgentState | None = None
        self.visited_sources: Set[str] = set()
        self.use_judge = use_judge
        self.judge_mode = judge_mode
        self.judge_used = False

    def reset(self, question: str) -> AgentState:
        self.state = AgentState(question=question)
        self.visited_sources = set()
        return self.state

    def step(self, action: str) -> Tuple[AgentState, float, bool, str]:
        assert self.state is not None
        self.state.steps += 1
        done = False
        info = ""
        reward = -0.05  # stronger per-step penalty to discourage loops

        if action == "vector_search":
            results = self.backend.vector_search(self.state.question, top_k=5)
            self.state.context.extend(results)
            reward += 0.2 if results else -0.1
            new_sources = 0
            for ctx in results:
                src = ctx.get("metadata", {}).get("source")
                if src and src not in self.visited_sources:
                    self.visited_sources.add(src)
                    new_sources += 1
            reward += 0.05 * new_sources
            info = "vector_search"
        elif action == "graph_expand":
            context_sources = [
                ctx.get("metadata", {}).get("source")
                for ctx in self.state.context
                if ctx.get("metadata", {}).get("source")
            ]
            seeds = select_graph_seeds(
                context_sources,
                self.state.question,
                self.schema,
                self.graph_overview_path,
                max_seeds=6,
            )
            if not seeds:
                reward -= 0.1
                info = "graph_expand_failed"
            else:
                neighbors = self.backend.graph_neighbors_diverse(seeds, top_k=10)
                self.state.graph_nodes.extend(neighbors)
                reward += 0.15 if neighbors else -0.05
                new_sources = 0
                for node in neighbors:
                    src = node.get("source")
                    if src and src not in self.visited_sources:
                        self.visited_sources.add(src)
                        new_sources += 1
                reward += 0.04 * new_sources
                info = f"graph_expand:{'/'.join(seeds[:3])}"
        elif action == "summarize":
            if not self.state.context:
                reward -= 0.05
                info = "summarize_empty"
            else:
                info = "summarize"
                # summary credit scaled by unique evidence gathered so far
                reward += 0.15 + 0.02 * len(self.visited_sources)
                if self.use_judge and not self.judge_used:
                    judge_bonus = self._judge_reward()
                    reward += judge_bonus
                    info += f"|judge:{judge_bonus:.3f}"
                    self.judge_used = True
        elif action == "stop":
            done = True
            reward += 0.3 if self.state.context else -0.2
            info = "stop"
        else:
            raise ValueError(f"Unknown action {action}")

        if self.state.steps >= self.max_steps:
            done = True
        return self.state, reward, done, info

    def _judge_reward(self) -> float:
        """Lightweight similarity-based judge: question vs gathered evidence."""
        if self.state is None or not self.state.question:
            return -0.1
        snippets: List[str] = []
        for ctx in self.state.context[:5]:
            text = ctx.get("text") or ""
            if text:
                snippets.append(text)
        for node in self.state.graph_nodes[:3]:
            sent = node.get("sentence") or ""
            if sent:
                snippets.append(sent)
        if not snippets:
            return -0.05
        evidence_text = " ".join(snippets)[:4000]
        try:
            q_vec = self.backend.embed(self.state.question)
            e_vec = self.backend.embed(evidence_text)
        except Exception:
            return 0.0
        sim = float(np.dot(q_vec, e_vec.T).squeeze())
        sim = max(0.0, sim)  # keep non-negative
        return 0.3 * min(sim, 1.0)


class SimplePolicy:
    def select(self, state: AgentState, graph_available: bool) -> str:
        if not state.context:
            return "vector_search"
        if graph_available and len(state.graph_nodes) < 5:
            return "graph_expand"
        if state.steps >= 3:
            return "summarize"
        return "stop"


def plan_queries(
    question: str,
    schema: Dict[str, Any],
    session_state: Dict[str, Any] | None = None,
    enable_rewrite: bool = True,
    enable_decompose: bool = True,
) -> Dict[str, Any]:
    rewritten = question
    if enable_rewrite:
        rewritten = expand_query_with_schema(question, schema)
        lookup = build_alias_lookup(schema)
        alias_hits = []
        for alias, canonical in lookup.items():
            if alias and alias in question.lower():
                alias_hits.append(canonical)
        if alias_hits:
            rewritten = f"{rewritten} " + " ".join(sorted(set(alias_hits)))

    topic = topic_label(schema, get_workspace_root())
    subqueries: List[str] = []
    if enable_decompose:
        subqueries.append(f"{topic} entities key enzymes variants")
        subqueries.append(f"{topic} assay conditions temperature pH time")
        subqueries.append(f"{topic} metrics kcat km conversion yield activity")
        if any(token in question.lower() for token in ["gap", "contradiction", "disagree", "conflict"]):
            subqueries.append(f"{topic} gaps limitations contradictions")

    session_entities = []
    if session_state:
        session_entities = session_state.get("entity_memory", []) or []
    if session_entities:
        subqueries.append(f"{topic} " + " ".join(session_entities[:6]))

    return {
        "original": question,
        "rewritten": rewritten,
        "subqueries": subqueries,
    }


def rrf_fuse(results: List[List[Dict[str, Any]]], k: int = DEFAULT_RRF_K) -> Dict[str, Dict[str, Any]]:
    fused: Dict[str, Dict[str, Any]] = {}
    for result_list in results:
        for rank, item in enumerate(result_list, start=1):
            doc_id = item.get("id") or item.get("metadata", {}).get("chunk_id") or item.get("metadata", {}).get("source")
            if not doc_id:
                continue
            entry = fused.setdefault(doc_id, {"rrf_score": 0.0})
            entry["rrf_score"] += 1.0 / (k + rank)
            entry.setdefault("items", []).append(item)
    return fused


def normalize_scores(values: List[float]) -> Dict[int, float]:
    if not values:
        return {}
    vmax = max(values)
    if vmax <= 0:
        return {idx: 0.0 for idx in range(len(values))}
    return {idx: val / vmax for idx, val in enumerate(values)}


def build_keyword_boost(query: str, text: str) -> float:
    lowered = text.lower()
    tokens = [tok for tok in re.findall(r"[a-z0-9]+", query.lower()) if len(tok) > 3]
    hits = sum(1 for tok in tokens if tok in lowered)
    return 0.05 * hits


def rerank_candidates(
    candidates: List[Dict[str, Any]],
    query: str,
    prefer_cross_encoder: bool = True,
    top_k: int = DEFAULT_RERANK_TOP_K,
    exclude_patterns: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    scored = []
    dense_scores = [float(c.get("dense_score", 0.0)) for c in candidates]
    bm25_scores = [float(c.get("bm25_score", 0.0)) for c in candidates]
    dense_norm = normalize_scores(dense_scores)
    bm25_norm = normalize_scores(bm25_scores)

    cross_encoder_scores = None
    if prefer_cross_encoder:
        model_name = os.environ.get("QA_CROSS_ENCODER_MODEL", "").strip()
        if model_name:
            try:
                from sentence_transformers import CrossEncoder  # type: ignore
                encoder = CrossEncoder(model_name)
                pairs = [(query, c.get("text", "")) for c in candidates]
                cross_encoder_scores = encoder.predict(pairs).tolist()
            except Exception:
                cross_encoder_scores = None

    for idx, cand in enumerate(candidates):
        score = cand.get("rrf_score", 0.0)
        score += 0.6 * dense_norm.get(idx, 0.0)
        score += 0.4 * bm25_norm.get(idx, 0.0)
        score += build_keyword_boost(query, cand.get("text", ""))
        if exclude_patterns:
            lowered = (cand.get("text") or "").lower()
            penalty = 0.0
            for pattern in exclude_patterns:
                if pattern and pattern.lower() in lowered:
                    penalty += EXCLUDE_PENALTY
            score -= penalty
        if cross_encoder_scores is not None:
            score = 0.7 * score + 0.3 * float(cross_encoder_scores[idx])
        scored.append({**cand, "rerank_score": score})

    scored.sort(key=lambda item: item.get("rerank_score", 0.0), reverse=True)
    selected = scored[:top_k]
    return selected, scored


def verify_answer(answer: str, sentence_map: List[Dict[str, Any]] | None = None) -> Tuple[str, Dict[str, Any]]:
    body, *rest = answer.split("Sources:", 1)
    if sentence_map is None:
        sentence_map = build_sentence_map(answer, [])
    kept = []
    dropped = []
    for entry in sentence_map:
        if entry.get("supported") or entry.get("connector"):
            kept.append(entry["sentence"])
        else:
            dropped.append(entry["sentence"])
    verifier = {
        "total_sentences": len(sentence_map),
        "kept_sentences": len(kept),
        "dropped_sentences": len(dropped),
        "unsupported_sentences": dropped,
        "unsupported_sentence_rate": (len(dropped) / len(sentence_map)) if sentence_map else 1.0,
    }
    rebuilt = " ".join(kept).strip()
    if rest:
        rebuilt = (rebuilt + "\n\nSources:\n" + rest[0].strip()).strip()
    return rebuilt or "No supported statements.", verifier


def load_session_state(topic: str, session_id: str) -> Dict[str, Any]:
    session_dir = QA_OUTPUT_ROOT / topic / session_id
    state_path = session_dir / "session_state.json"
    if state_path.exists():
        try:
            return json.loads(state_path.read_text())
        except Exception:
            return {}
    return {
        "rolling_summary": "",
        "entity_memory": [],
        "cited_sources": [],
        "open_questions": [],
        "working_set_entities": [],
        "open_slots": [],
        "last_intent": "",
        "turn": 0,
    }


def update_session_state(
    state: Dict[str, Any],
    question: str,
    answer: str,
    citations: List[Dict[str, Any]],
    intent: Optional[str] = None,
) -> Dict[str, Any]:
    body = answer.split("Sources:", 1)[0]
    entities = extract_entities(body)
    cited = [c.get("paper") for c in citations if c.get("paper")] if citations else []

    state.setdefault("entity_memory", [])
    state.setdefault("cited_sources", [])
    state.setdefault("open_questions", [])
    state.setdefault("working_set_entities", [])
    state.setdefault("open_slots", [])
    state.setdefault("last_intent", "")

    for ent in entities:
        if ent not in state["entity_memory"] and len(state["entity_memory"]) < 50:
            state["entity_memory"].append(ent)
    for src in cited:
        if src not in state["cited_sources"] and len(state["cited_sources"]) < 200:
            state["cited_sources"].append(src)
    if question and question not in state["open_questions"] and len(state["open_questions"]) < 50:
        state["open_questions"].append(question)

    summary_sentences = _split_sentences(body)[:3]
    summary_snippet = " ".join(summary_sentences).strip()
    rolling = state.get("rolling_summary", "").strip()
    combined = (rolling + " " + summary_snippet).strip()
    state["rolling_summary"] = combined[-2000:] if combined else ""
    state["working_set_entities"] = state.get("entity_memory", [])
    if intent:
        state["last_intent"] = intent
    state["turn"] = int(state.get("turn", 0)) + 1
    return state


def save_run_bundle(
    topic: str,
    session_id: str,
    turn_id: int,
    payloads: Dict[str, Any],
) -> Dict[str, Any]:
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = QA_OUTPUT_ROOT / topic / session_id / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    def write_json(name: str, data: Any) -> str:
        path = run_dir / name
        path.write_text(json.dumps(data, indent=2, ensure_ascii=True))
        return str(path)

    paths = {
        "input": write_json(f"turn_{turn_id}_input.json", payloads.get("input", {})),
        "planner": write_json(f"turn_{turn_id}_planner.json", payloads.get("planner", {})),
        "queries": write_json(f"turn_{turn_id}_queries.json", payloads.get("queries", {})),
        "retrieval": write_json(f"turn_{turn_id}_retrieval.json", payloads.get("retrieval", {})),
        "fusion": write_json(f"turn_{turn_id}_fusion.json", payloads.get("fusion", {})),
        "rerank": write_json(f"turn_{turn_id}_rerank.json", payloads.get("rerank", {})),
        "answer": write_json(f"turn_{turn_id}_answer.json", payloads.get("answer", {})),
        "claims": write_json(f"turn_{turn_id}_claims.json", payloads.get("claims", {})),
        "verifier": write_json(f"turn_{turn_id}_verifier.json", payloads.get("verifier", {})),
        "validation": write_json(f"turn_{turn_id}_validation.json", payloads.get("validation", {})),
        "abstain": write_json(f"turn_{turn_id}_abstain.json", payloads.get("abstain", {})),
        "blocks": write_json(
            f"turn_{turn_id}_blocks.json",
            payloads.get("answer", {}).get("blocks", []),
        ),
        "evidence_ids": write_json(
            f"turn_{turn_id}_evidence_ids.json",
            payloads.get("selected_evidence_ids", []),
        ),
    }
    session_path = run_dir.parent / "session_state.json"
    session_path.write_text(json.dumps(payloads.get("session_state", {}), indent=2, ensure_ascii=True))
    report_path = run_dir / "run_report.md"
    report_path.write_text(payloads.get("report", ""), encoding="utf-8")

    index_row = payloads.get("index_row", {})
    index_row["run_dir"] = str(run_dir)
    index_row["timestamp"] = timestamp
    index_path = run_dir.parent / "index.jsonl"
    with index_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(index_row, ensure_ascii=True) + "\n")

    latest_pointer = run_dir.parent / "latest_pointer.json"
    latest_pointer.write_text(json.dumps({"latest": timestamp}, indent=2, ensure_ascii=True))

    paths["run_dir"] = str(run_dir)
    return paths


def write_run_summary(
    topic: str,
    run_id: str,
    query: str,
    output_mode: str,
    intent: str,
    graph_enabled: bool,
    nodes_visited: List[str],
    used_general_answer_agent: bool,
    used_claims_lite: bool,
    fallback_path: str,
    validation_pass: bool,
    validation_reason: Optional[str],
    counts: Dict[str, int],
    selected_evidence_ids_count: int,
    render_template_id: str,
    citations_count: int,
    abstain: bool,
    answer_mode: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, str]:
    workspace_root = get_workspace_root()
    qa_root = workspace_root / "qa_runs"
    qa_root.mkdir(parents=True, exist_ok=True)
    run_dir = qa_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ts = timestamp or datetime.datetime.utcnow().isoformat() + "Z"
    answer_mode = answer_mode or (
        "helpful"
        if output_mode == "answer_helpful"
        else "dual"
        if output_mode == "answer_dual"
        else "strict"
        if output_mode == "answer_strict"
        else "protocol"
    )
    summary = {
        "run_id": run_id,
        "timestamp": ts,
        "topic": topic,
        "query": query,
        "answer_mode": answer_mode,
        "output_mode": output_mode,
        "intent": intent,
        "graph_enabled": graph_enabled,
        "nodes_visited": nodes_visited,
        "used_general_answer_agent": used_general_answer_agent,
        "used_claims_lite": used_claims_lite,
        "fallback_path": fallback_path,
        "validation_pass": validation_pass,
        "validation_reason": validation_reason,
        "counts": {
            "grounded": int(counts.get("grounded", 0)),
            "partial": int(counts.get("partial", 0)),
            "inferred": int(counts.get("inferred", 0)),
        },
        "selected_evidence_ids_count": int(selected_evidence_ids_count),
        "render_template_id": render_template_id,
    }
    summary_path = run_dir / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True))
    total = summary["counts"]["grounded"] + summary["counts"]["partial"] + summary["counts"]["inferred"]
    grounded_rate = (summary["counts"]["grounded"] / total) if total else 0.0
    index_row = {
        "timestamp": ts,
        "run_id": run_id,
        "intent": intent,
        "answer_mode": answer_mode,
        "grounded_rate": grounded_rate,
        "citations_count": int(citations_count),
        "abstain": bool(abstain),
    }
    index_path = qa_root / "qa_run_index.jsonl"
    with index_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(index_row, ensure_ascii=True) + "\n")
    return {"run_summary": str(summary_path), "run_index": str(index_path), "run_dir": str(run_dir)}


def augment_with_expected_entities(state: AgentState, backend: RetrievalBackend, expected_entities: List[str]) -> None:
    present_sources = set()
    for ctx in state.context:
        source = ctx.get("metadata", {}).get("source")
        if source:
            present_sources.add(source)
    for node in state.graph_nodes:
        src = node.get("source")
        if src:
            present_sources.add(src)

    for entity in expected_entities:
        if entity in present_sources:
            continue
        edges = backend.graph_neighbors(entity, top_k=5)
        if edges:
            state.graph_nodes = edges + state.graph_nodes
            for edge in edges:
                present_sources.add(edge.get("source"))


def fetch_pdf_context(paper: str | None, sentence: str, window: int = 600) -> str:
    if not paper:
        return ""
    txt_path = get_text_dir() / (Path(paper).stem + ".txt")
    if not txt_path.exists():
        return ""
    content = txt_path.read_text(errors="ignore")
    snippet = sentence.strip()
    snippet_lower = snippet.lower()[:120]
    idx = content.lower().find(snippet_lower) if snippet_lower else -1
    if idx == -1:
        return content[:window].strip()
    start = max(0, idx - window // 2)
    end = min(len(content), idx + window // 2)
    return content[start:end].strip()


def _signal_score(text: str, signals: List[str]) -> int:
    lowered = (text or "").lower()
    score = 0
    for sig in signals or []:
        token = (sig or "").strip().lower()
        if not token:
            continue
        if token in lowered:
            score += 2
        if token in {"ph", "pH"} and "ph" in lowered:
            score += 2
        if token in {"temperature", "temp"} and ("°c" in lowered or "temperature" in lowered):
            score += 2
        if token in {"buffer", "buffer_type"} and "buffer" in lowered:
            score += 1
        if token in {"enzyme_loading", "enzyme", "concentration"} and "enzyme" in lowered:
            score += 1
        if token in {"rate", "activity"} and ("rate" in lowered or "activity" in lowered):
            score += 1
    if NUM_UNIT_RE.search(text or ""):
        score += 2
    return score


def build_evidence_from_state(
    state: AgentState,
    max_items: int = 8,
    extra_evidence: Optional[List[Dict[str, Any]]] = None,
    required_signals: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
    evidence_items: List[Dict[str, Any]] = []
    citations: List[Dict[str, Any]] = []
    evidence_to_citation: Dict[str, int] = {}

    def register_evidence(source_id: str | None, paper: str | None, title: str | None, snippet: str | None) -> str:
        evidence_id = f"E{len(evidence_items) + 1}"
        citation_id = len(citations) + 1
        fields = resolve_citation_fields(paper, snippet)
        citations.append(
            {
                "id": citation_id,
                "paper": Path(paper).name if paper else None,
                "source_id": source_id or evidence_id,
                "source_ids": [source_id or evidence_id],
                "title": title or fields.get("title") or resolve_title(paper),
                "doi": fields.get("doi"),
                "year": fields.get("year"),
                "authors": fields.get("authors"),
            }
        )
        evidence_to_citation[evidence_id] = citation_id
        return evidence_id

    def add_evidence(text: str, meta: Dict[str, Any]) -> None:
        source_id = meta.get("chunk_id") or meta.get("source") or meta.get("pdf_file") or meta.get("paper")
        paper = meta.get("paper") or meta.get("pdf_file")
        title = meta.get("title") or resolve_title(paper)
        if title and ("/" in title or "\\" in title):
            try:
                title = Path(title).stem
            except Exception:
                title = resolve_title(paper)
        if exclude_patterns:
            lowered = text.lower()
            for pattern in exclude_patterns:
                if pattern and pattern.lower() in lowered:
                    return
            if title:
                title_lower = title.lower()
                for pattern in exclude_patterns:
                    if pattern and pattern.lower() in title_lower:
                        return
        evidence_id = register_evidence(source_id, paper, title, text)
        evidence_items.append(
            {
                "evidence_id": evidence_id,
                "title": title,
                "paper": paper,
                "source_id": source_id,
                "text": text,
            }
        )

    context = list(state.context or [])
    extra_evidence = extra_evidence or []
    if required_signals and extra_evidence:
        extra_evidence = sorted(
            extra_evidence,
            key=lambda item: _signal_score(item.get("text", ""), required_signals),
            reverse=True,
        )
    reserved_extra = min(len(extra_evidence), max(4, max_items // 2)) if extra_evidence else 0
    budget_primary = max_items - reserved_extra
    if required_signals:
        scored_context = []
        for item in context:
            score = _signal_score(item.get("text", ""), required_signals)
            scored_context.append((score, float(item.get("score", 0.0)), item))
        scored_context.sort(key=lambda row: (row[0], row[1]), reverse=True)
        strong = [row[2] for row in scored_context if row[0] > 0]
        weak = [row[2] for row in scored_context if row[0] <= 0]
        context = strong + weak

    if extra_evidence:
        for ev in extra_evidence[:reserved_extra]:
            if len(evidence_items) >= max_items:
                break
            text = (ev.get("text") or "").strip()
            meta = ev.get("metadata") or {}
            if text:
                add_evidence(text[:800], meta)

    for ctx in context[:budget_primary]:
        meta = ctx.get("metadata", {})
        snippet = ctx.get("text", "").strip()
        if snippet:
            add_evidence(snippet[:800], meta)

    remaining = max_items - len(evidence_items)
    if remaining > 0:
        for neighbor in state.graph_nodes[:remaining]:
            sentence = str(neighbor.get("sentence") or neighbor.get("text") or "").strip()
            if not sentence:
                continue
            add_evidence(sentence[:800], neighbor)

    return evidence_items, citations, evidence_to_citation


def collect_methodology_evidence(
    question: str,
    limit: int = 6,
    required_signals: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    if os.environ.get("QA_METHOD_EVIDENCE", "1") != "1":
        return []
    try:
        from services.methodology_retrieval import get_backend as get_method_backend  # noqa: E402
    except Exception:
        return []
    backend = get_method_backend()
    if backend is None:
        return []
    exclude = ("acknowledg", "funding", "conflict", "author", "correspondence", "supplement")
    evidence: List[Dict[str, Any]] = []

    edges = backend.edge_search(question, top_k=max(limit * 4, 12))
    for edge in edges:
        meta = edge.get("metadata", {})
        heading = str(meta.get("heading") or "").lower()
        if any(tok in heading for tok in exclude):
            continue
        text = edge.get("text") or meta.get("sentence") or ""
        if not text:
            continue
        if required_signals and _signal_score(text, required_signals) <= 0:
            continue
        evidence.append({"text": text, "metadata": meta})
        if len(evidence) >= limit:
            break

    if len(evidence) < limit:
        sections = backend.section_search(question, top_k=limit * 2)
        for sec in sections:
            heading = str(sec.get("heading") or "").lower()
            if any(tok in heading for tok in exclude):
                continue
            text = sec.get("text") or ""
            if not text:
                continue
            if required_signals and _signal_score(text, required_signals) <= 0:
                continue
            meta = {
                "paper": sec.get("paper"),
                "pdf_file": sec.get("pdf_file"),
                "title": sec.get("paper"),
                "section_type": sec.get("section_type"),
                "heading": sec.get("heading"),
            }
            evidence.append({"text": text, "metadata": meta})
            if len(evidence) >= limit:
                break

    return evidence


def collect_kg_edge_evidence(
    workspace_root: Path,
    question: str,
    plan: QuestionPlan,
    schema: Dict[str, Any],
    limit: int = 20,
) -> List[Dict[str, Any]]:
    if os.environ.get("QA_KG_EDGE_EVIDENCE", "1") != "1":
        return []
    graph_db = workspace_root / "graph.sqlite"
    if not graph_db.exists():
        return []
    tokens = [tok for tok in re.findall(r"[a-z0-9]+", question.lower()) if len(tok) > 3]
    signals = [s.lower() for s in (plan.required_signals or []) if isinstance(s, str)]
    keywords = []
    for token in tokens:
        if token not in keywords:
            keywords.append(token)
        if len(keywords) >= 6:
            break
    for sig in signals:
        if sig not in keywords:
            keywords.append(sig)
        if len(keywords) >= 10:
            break
    rel_keywords: List[str] = []
    rel_data = schema.get("relation_keywords")
    if isinstance(rel_data, dict):
        rel_keywords = [key for key in rel_data.keys() if isinstance(key, str)]
    elif isinstance(rel_data, list):
        rel_keywords = [kw for kw in rel_data if isinstance(kw, str)]
    for rel in rel_keywords:
        rel_lower = rel.lower()
        if rel_lower not in keywords:
            keywords.append(rel_lower)
        if len(keywords) >= 12:
            break

    if not keywords:
        return []

    conditions = []
    params: List[str] = []
    for kw in keywords:
        like = f"%{kw}%"
        conditions.append("lower(e.relation) LIKE ?")
        params.append(like)
        conditions.append("lower(e.sentence) LIKE ?")
        params.append(like)
    where = " OR ".join(conditions)

    pool_limit = int(os.environ.get("QA_KG_EDGE_POOL", str(limit * 10)))
    query = f"""
        SELECT e.relation, e.paper, e.sentence,
               n1.label as source, n1.type as source_type,
               n2.label as target, n2.type as target_type
        FROM edges e
        LEFT JOIN nodes n1 ON e.source_id = n1.id
        LEFT JOIN nodes n2 ON e.target_id = n2.id
        WHERE {where}
        LIMIT {pool_limit}
    """
    results: List[Dict[str, Any]] = []
    try:
        conn = sqlite3.connect(graph_db)
        cur = conn.cursor()
        rows = cur.execute(query, params).fetchall()
        conn.close()
    except Exception:
        return []

    candidate_types = {"enzyme", "protein", "variant", "strain", "organism"}
    for relation, paper, sentence, source, source_type, target, target_type in rows:
        if plan.intent in {"candidate_selection", "comparison"}:
            if (source_type not in candidate_types) and (target_type not in candidate_types):
                continue
        if _is_generic_label(source) or _is_generic_label(target):
            continue
        text = f"{source} {relation} {target}. Evidence: {sentence}".strip()
        meta = {
            "paper": paper,
            "pdf_file": paper,
            "title": paper,
            "relation": relation,
            "source": source,
            "target": target,
            "source_type": source_type,
            "target_type": target_type,
            "sentence": sentence,
        }
        results.append({"text": text, "metadata": meta})

    if required := (plan.required_signals or []):
        results.sort(key=lambda item: _signal_score(item.get("text", ""), required), reverse=True)
        strong = [item for item in results if _signal_score(item.get("text", ""), required) > 0]
        if strong:
            results = strong
    return results[:limit]


def _specificity_score(label: str) -> int:
    score = 0
    if any(ch.isdigit() for ch in label):
        score += 2
    if any(ch.isupper() for ch in label[1:]):
        score += 1
    if "-" in label or "_" in label:
        score += 1
    if len(label) >= 8:
        score += 1
    return score


def collect_candidate_evidence(
    workspace_root: Path,
    question: str,
    plan: QuestionPlan,
    schema: Dict[str, Any],
    limit: int = 8,
) -> List[Dict[str, Any]]:
    if os.environ.get("QA_KG_CANDIDATE_EVIDENCE", "1") != "1":
        return []
    graph_db = workspace_root / "graph.sqlite"
    if not graph_db.exists():
        return []
    candidate_types = {"enzyme", "protein", "variant", "strain", "organism"}
    try:
        conn = sqlite3.connect(graph_db)
        cur = conn.cursor()
        rows = cur.execute(
            """
            SELECT n.id, n.label, n.type, COUNT(e.id) as edge_count, COUNT(DISTINCT e.paper) as paper_count
            FROM nodes n
            JOIN edges e ON n.id = e.source_id OR n.id = e.target_id
            WHERE n.type IN ('enzyme','protein','variant','strain','organism')
            GROUP BY n.id, n.label, n.type
            """
        ).fetchall()
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if not rows:
        return []

    # Build relevance keywords from question + schema + required signals
    tokens = [tok for tok in re.findall(r"[a-z0-9]+", question.lower()) if len(tok) > 3]
    key_entities = schema.get("key_entities") or []
    alias_map = schema.get("entity_aliases") or {}
    for ent in key_entities:
        tokens.extend([tok for tok in re.findall(r"[a-z0-9]+", str(ent).lower()) if len(tok) > 3])
    for alias in alias_map.keys():
        tokens.extend([tok for tok in re.findall(r"[a-z0-9]+", str(alias).lower()) if len(tok) > 3])
    if plan.required_signals:
        tokens.extend([str(sig).lower() for sig in plan.required_signals if isinstance(sig, str)])
    keywords = []
    for tok in tokens:
        if tok not in keywords:
            keywords.append(tok)
        if len(keywords) >= 12:
            break

    relevance_counts: Dict[int, int] = {}
    example_edge: Dict[int, str] = {}
    if keywords:
        conditions = []
        params: List[str] = []
        for kw in keywords:
            like = f"%{kw}%"
            conditions.append("lower(e.relation) LIKE ?")
            params.append(like)
            conditions.append("lower(e.sentence) LIKE ?")
            params.append(like)
        where = " OR ".join(conditions)
        pool_limit = int(os.environ.get("QA_KG_EDGE_POOL", "300"))
        query = f"""
            SELECT e.source_id, e.target_id, e.relation, e.sentence
            FROM edges e
            WHERE {where}
            LIMIT {pool_limit}
        """
        try:
            conn = sqlite3.connect(graph_db)
            cur = conn.cursor()
            rel_rows = cur.execute(query, params).fetchall()
        except Exception:
            rel_rows = []
        finally:
            try:
                conn.close()
            except Exception:
                pass

        for source_id, target_id, relation, sentence in rel_rows:
            if source_id is not None:
                relevance_counts[source_id] = relevance_counts.get(source_id, 0) + 1
                if source_id not in example_edge and sentence:
                    example_edge[source_id] = f"{relation}: {sentence[:160]}"
            if target_id is not None:
                relevance_counts[target_id] = relevance_counts.get(target_id, 0) + 1
                if target_id not in example_edge and sentence:
                    example_edge[target_id] = f"{relation}: {sentence[:160]}"

    topic = topic_label(schema, workspace_root).lower()
    candidates = []
    for node_id, label, node_type, edge_count, paper_count in rows:
        if node_type not in candidate_types:
            continue
        if not label:
            continue
        if _is_generic_label(label):
            continue
        label_lower = str(label).lower()
        penalty = -3 if label_lower == topic else 0
        relevance = relevance_counts.get(node_id, 0)
        score = (3 * relevance) + (1 * edge_count) + (2 * paper_count) + _specificity_score(str(label)) + penalty
        candidates.append(
            {
                "id": node_id,
                "label": label,
                "type": node_type,
                "edge_count": edge_count,
                "paper_count": paper_count,
                "relevance": relevance,
                "score": score,
                "example": example_edge.get(node_id),
            }
        )

    candidates.sort(key=lambda item: item["score"], reverse=True)
    top = candidates[:limit]
    if not top:
        return []

    lines = ["Top candidate entities ranked by KG connectivity and query relevance:"]
    for cand in top:
        reason = f"edges={cand['edge_count']}, papers={cand['paper_count']}, relevant_edges={cand['relevance']}"
        if cand.get("example"):
            reason += f"; example: {cand['example']}"
        lines.append(f"- {cand['label']} ({cand['type']}) — {reason}")
    text = "\n".join(lines)
    return [{"text": text, "metadata": {"paper": "KG_summary", "title": "KG candidate summary"}}]


def _metric_in_text(metric: str, text: str) -> bool:
    metric = (metric or "").strip().lower()
    if not metric:
        return True
    return metric in (text or "").lower()


def _numeric_in_text(value: Any, text: str) -> bool:
    text_lower = (text or "").lower()
    if isinstance(value, (int, float)):
        return str(value) in text_lower
    if isinstance(value, str):
        if not any(ch.isdigit() for ch in value):
            return True
        return value.lower() in text_lower
    return True


def _qualifiers_supported(qualifiers: Dict[str, Any], evidence_text: str) -> bool:
    if not qualifiers:
        return True
    metric = qualifiers.get("metric")
    if metric and not _metric_in_text(str(metric), evidence_text):
        return False
    for key in ("delta", "value", "temperature", "temp", "pH", "ph"):
        if key in qualifiers and not _numeric_in_text(qualifiers.get(key), evidence_text):
            return False
    return True


def _claim_matches_exclude(claim: Claim, exclude_patterns: List[str]) -> bool:
    if not exclude_patterns:
        return False
    haystack = f"{claim.subject.text} {claim.object.text}".lower()
    for pattern in exclude_patterns:
        if pattern and pattern.lower() in haystack:
            return True
    return False


def _relation_to_phrase(relation: str | None) -> str:
    if not relation:
        return ""
    mapping = {
        "catalyzes_hydrolysis_of": "catalyzes hydrolysis of",
        "depolymerizes_to": "depolymerizes to",
        "has_substrate": "has substrate",
        "has_product": "has product",
        "produces": "produces",
        "active_pH": "is active at pH",
        "targets_substrate": "targets substrate",
        "measured_by_assay": "is measured by assay",
    }
    key = relation.strip()
    if key in mapping:
        return mapping[key]
    return key.replace("_", " ")


def _is_generic_label(label: str | None) -> bool:
    if not label:
        return True
    lowered = label.strip().lower()
    generic = {
        "protein",
        "enzyme",
        "polymer",
        "compound",
        "reaction",
        "conditions",
        "substrate",
        "product",
        "buffer",
        "ph",
        "temperature",
        "assay",
        "hydrolase",
        "cutinase",
        "esterase",
        "release",
        "oxidoreductase",
        "transferase",
        "lyase",
        "ligase",
    }
    if lowered in generic:
        return True
    if lowered.startswith("with "):
        return True
    if lowered.isalpha() and lowered.endswith("ase") and label.islower():
        return True
    if len(lowered) < 3:
        return True
    return False


def post_filter_claims(
    claims: List[Claim],
    evidence_text: Dict[str, str],
    plan: QuestionPlan,
    min_confidence: float = DEFAULT_CLAIM_CONFIDENCE,
    max_claims: int = DEFAULT_CLAIM_MAX_ITEMS,
) -> Tuple[List[Claim], Dict[str, Any]]:
    filtered: List[Claim] = []
    dropped = 0
    for idx, claim in enumerate(claims, start=1):
        if claim.confidence < min_confidence:
            dropped += 1
            continue
        if claim.evidence_id not in evidence_text:
            dropped += 1
            continue
        if claim.relation in {"uses_method", "assay_condition"} and plan.intent not in CLAIM_METHOD_INTENTS:
            dropped += 1
            continue
        if _claim_matches_exclude(claim, plan.exclude_patterns):
            dropped += 1
            continue
        if not _qualifiers_supported(claim.qualifiers, evidence_text.get(claim.evidence_id, "")):
            dropped += 1
            continue
        if not claim.claim_id:
            claim.claim_id = f"C{idx}"
        canonicalized = bool(claim.subject.entity_id and claim.object.entity_id)
        if not canonicalized:
            claim.canonicalized = False
        filtered.append(claim)
        if len(filtered) >= max_claims:
            break
    stats = {
        "raw": len(claims),
        "kept": len(filtered),
        "dropped": dropped,
    }
    return filtered, stats


def claims_are_sufficient(claims: List[Claim], min_items: int = DEFAULT_CLAIM_MIN_ITEMS) -> bool:
    return len(claims) >= min_items


def extract_claims_from_evidence(
    evidence_items: List[Dict[str, Any]],
    plan: QuestionPlan,
    schema: Dict[str, Any],
    use_llm: bool,
    max_sentences: int = DEFAULT_CLAIM_MAX_SENTENCES,
    max_claims: int = DEFAULT_CLAIM_MAX_ITEMS,
    min_confidence: float = DEFAULT_CLAIM_CONFIDENCE,
) -> Tuple[List[Claim], Dict[str, Any]]:
    if not use_llm or not evidence_items:
        return [], {"error": "no_llm_or_no_evidence"}

    sentences: List[Dict[str, str]] = []
    evidence_text: Dict[str, str] = {}
    for item in evidence_items:
        evidence_id = item.get("evidence_id")
        if not evidence_id:
            continue
        text = item.get("text", "")
        evidence_text[evidence_id] = text
        for sent in _split_sentences(text):
            if len(sent) < 6:
                continue
            sentences.append({
                "evidence_id": evidence_id,
                "paper_id": item.get("paper"),
                "text": sent,
            })
            if len(sentences) >= max_sentences:
                break
        if len(sentences) >= max_sentences:
            break

    if not sentences:
        return [], {"error": "no_sentences"}

    topic = topic_label(schema, get_workspace_root())
    prompt_lines = []
    for entry in sentences:
        prompt_lines.append(
            f"- evidence_id: {entry['evidence_id']} | paper_id: {entry.get('paper_id') or 'unknown'} | sentence: {entry['text']}"
        )
    prompt = (
        "You extract atomic claims from evidence sentences.\n"
        "Return ONLY a JSON list of Claim objects matching this schema:\n"
        "{\n"
        "  \"claim_id\": string,\n"
        "  \"topic\": string,\n"
        "  \"paper_id\": string|null,\n"
        "  \"evidence_id\": string,\n"
        "  \"subject\": {\"entity_id\": string|null, \"text\": string},\n"
        f"  \"relation\": one of {list(CLAIM_RELATIONS)},\n"
        "  \"object\": {\"entity_id\": string|null, \"text\": string},\n"
        "  \"qualifiers\": dict,\n"
        "  \"confidence\": float (0..1),\n"
        "  \"canonicalized\": bool\n"
        "}\n"
        "Rules:\n"
        "- Do not invent numbers or metrics not present in the sentence.\n"
        "- If subject/object cannot be canonicalized, set entity_id=null and canonicalized=false.\n"
        "- Use the provided evidence_id values.\n"
        "- If nothing meaningful, return [] only.\n"
        f"Topic: {topic}\n"
        "Evidence sentences:\n"
        + "\n".join(prompt_lines)
    )
    raw = None
    try:
        raw = local_llm.generate(prompt, system_prompt="Return JSON only.")
        payload = _safe_json_list(raw)
        claims = ClaimsAdapter.validate_python(payload)
    except Exception:
        return [], {"error": "claim_extraction_failed", "raw": raw}

    filtered, stats = post_filter_claims(
        claims,
        evidence_text,
        plan,
        min_confidence=min_confidence,
        max_claims=max_claims,
    )
    stats["relations"] = Counter([claim.relation for claim in filtered]).most_common(5)
    stats["canonicalized_rate"] = (
        (sum(1 for claim in filtered if claim.canonicalized) / len(filtered)) if filtered else 0.0
    )
    return filtered, stats


def claim_store_dir(workspace_root: Path) -> Path:
    return workspace_root / "claim_store"


def append_claims_to_store(workspace_root: Path, claims: List[Claim]) -> None:
    if not claims:
        return
    store_dir = claim_store_dir(workspace_root)
    store_dir.mkdir(parents=True, exist_ok=True)
    path = store_dir / "claims.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        for claim in claims:
            handle.write(json.dumps(claim.model_dump(), ensure_ascii=True) + "\n")


def load_claim_index(workspace_root: Path) -> Dict[str, Dict[str, List[str]]]:
    index_path = claim_store_dir(workspace_root) / "index.json"
    if index_path.exists():
        try:
            return json.loads(index_path.read_text())
        except Exception:
            return {"by_subject_id": {}, "by_relation": {}, "by_paper_id": {}}
    return {"by_subject_id": {}, "by_relation": {}, "by_paper_id": {}}


def update_claim_index(index: Dict[str, Dict[str, List[str]]], claims: List[Claim]) -> Dict[str, Dict[str, List[str]]]:
    for claim in claims:
        if claim.subject.entity_id:
            index.setdefault("by_subject_id", {}).setdefault(claim.subject.entity_id, []).append(claim.claim_id)
        index.setdefault("by_relation", {}).setdefault(claim.relation, []).append(claim.claim_id)
        if claim.paper_id:
            index.setdefault("by_paper_id", {}).setdefault(claim.paper_id, []).append(claim.claim_id)
    return index


def persist_claim_index(workspace_root: Path, index: Dict[str, Dict[str, List[str]]]) -> None:
    index_path = claim_store_dir(workspace_root) / "index.json"
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=True))


def select_claim_ids_for_blocks(claims: List[Claim], blocks: List[BlockUnion]) -> List[str]:
    claim_map = {}
    for claim in claims:
        claim_map.setdefault(claim.evidence_id, []).append(claim.claim_id)
    selected: List[str] = []
    for block in blocks:
        if isinstance(block, RankedEntitiesBlock):
            for item in block.items:
                for eid in item.supporting_evidence:
                    selected.extend(claim_map.get(eid, []))
        elif isinstance(block, DirectAnswerBlock):
            for bullet in block.bullets:
                for eid in bullet.citations:
                    selected.extend(claim_map.get(eid, []))
        elif isinstance(block, CaveatsBlock):
            for item in block.items:
                for eid in item.citations:
                    selected.extend(claim_map.get(eid, []))
    return list(dict.fromkeys(selected))


def _is_definitional(text: str) -> bool:
    lowered = text.lower()
    return "is defined as" in lowered or "refers to" in lowered or lowered.startswith("definition")


def _style_seed(session_id: Optional[str], query: str) -> int:
    seed_source = session_id or query
    digest = hashlib.sha256(seed_source.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _pick_phrases(kind: str, seed: int, count: int) -> List[str]:
    phrases = PHRASE_BANK.get(kind, [])
    if not phrases:
        return []
    rng = random.Random(seed + len(kind))
    if count <= len(phrases):
        return rng.sample(phrases, count)
    picks = []
    while len(picks) < count:
        picks.extend(rng.sample(phrases, min(len(phrases), count - len(picks))))
    return picks[:count]


def _tokenize(text: str) -> List[str]:
    return [tok for tok in re.findall(r"[a-z0-9]+", text.lower()) if len(tok) > 3 and tok not in STOPWORDS]


def _match_claims_to_bullet(bullet: str, claims: List[Claim]) -> List[str]:
    lowered = bullet.lower()
    evidence_ids = []
    for claim in claims:
        subj = claim.subject.text.lower()
        obj = claim.object.text.lower()
        if (subj and subj in lowered) or (obj and obj in lowered):
            evidence_ids.append(claim.evidence_id)
    return list(dict.fromkeys([eid for eid in evidence_ids if eid]))


def _match_evidence_to_bullet(bullet: str, evidence_items: List[Dict[str, Any]]) -> Tuple[List[str], int]:
    tokens = set(_tokenize(bullet))
    best: List[Tuple[str, int]] = []
    for item in evidence_items:
        eid = item.get("evidence_id")
        if not eid:
            continue
        text = item.get("text", "")
        evidence_tokens = set(_tokenize(text))
        overlap = len(tokens & evidence_tokens)
        if overlap <= 0:
            continue
        best.append((eid, overlap))
    best.sort(key=lambda x: x[1], reverse=True)
    top = [eid for eid, _ in best[:2]]
    top_overlap = best[0][1] if best else 0
    return top, top_overlap


def generate_draft_answer(
    question: str,
    plan: QuestionPlan,
    session_state: Dict[str, Any],
    evidence_items: Optional[List[Dict[str, Any]]],
    use_llm: bool,
    temperature: Optional[float] = None,
) -> Tuple[DraftAnswer, Dict[str, Any]]:
    meta = {"repair_used": False, "fallback_used": False}

    def _validate_payload(payload: Dict[str, Any]) -> DraftAnswer:
        return DraftAnswer.model_validate(payload)

    if use_llm:
        evidence_lines = []
        for item in (evidence_items or [])[:8]:
            title = item.get("title") or "evidence"
            snippet = (item.get("text") or "").strip().replace("\n", " ")
            if snippet:
                evidence_lines.append(f"- {title}: {snippet[:320]}")
        prompt = (
            "You are drafting a helpful answer that is readable and structured.\n"
            "Return ONLY valid JSON matching this schema (optional fields may be omitted):\n"
            "{\n"
            "  \"quick_answer\": [string],\n"
            "  \"details_sections\"?: [{\"title\": string, \"bullets\": [string]}],\n"
            "  \"assumptions\"?: [string],\n"
            "  \"missing_to_verify\"?: [string],\n"
            "  \"next_steps\"?: [string]\n"
            "}\n\n"
            f"Question: {question}\n"
            f"Intent: {plan.intent}\n"
            f"Session summary: {(session_state.get('rolling_summary') or '')[:400]}\n"
        )
        if evidence_lines:
            prompt += "Evidence snippets:\n" + "\n".join(evidence_lines) + "\n"
        prompt += (
            "Rules:\n"
            "- quick_answer: 3–5 bullets\n"
            "- details_sections: 2–4 sections, each 2–4 bullets (optional)\n"
            "- Each bullet must be a complete sentence with subject + verb.\n"
            "- Use only information grounded in the evidence snippets.\n"
            "- Include specific entities, conditions, or metrics named in the evidence.\n"
            "- Avoid generic advice or background facts not tied to the evidence.\n"
        )
        try:
            raw = local_llm.generate(prompt, temperature=temperature, system_prompt="Return JSON only.")
            payload = _safe_json_loads(raw)
            return _validate_payload(payload), meta
        except Exception:
            try:
                repair_prompt = (
                    "Return valid JSON for this schema. Drop missing fields rather than failing.\n"
                    "Schema:\n"
                    "{\n"
                    "  \"quick_answer\": [string],\n"
                    "  \"details_sections\"?: [{\"title\": string, \"bullets\": [string]}],\n"
                    "  \"assumptions\"?: [string],\n"
                    "  \"missing_to_verify\"?: [string],\n"
                    "  \"next_steps\"?: [string]\n"
                    "}\n\n"
                    f"Original question: {question}\n"
                    f"Intent: {plan.intent}\n"
                    "Invalid JSON payload:\n"
                    f"{raw}\n"
                )
                repaired = local_llm.generate(repair_prompt, temperature=temperature, system_prompt="Return JSON only.")
                payload = _safe_json_loads(repaired)
                meta["repair_used"] = True
                return _validate_payload(payload), meta
            except Exception:
                meta["fallback_used"] = True

    # Deterministic fallback (no LLM or failed repair)
    quick = [
        f"Here is a concise answer to: {question}.",
        "Key points depend on what your corpus covers; some items may be inferred.",
        "Provide specific targets or metrics to improve grounding.",
    ]
    meta["fallback_used"] = True if not use_llm else meta["fallback_used"]
    return DraftAnswer(quick_answer=quick), meta


def ground_and_tag_draft(
    draft: DraftAnswer,
    claims: Optional[List[Claim]],
    evidence_items: List[Dict[str, Any]],
) -> Tuple[List[GroundedBullet], List[GroundedSection], Dict[str, Any]]:
    claims = claims or []
    grounding_stats = {"grounded": 0, "partial": 0, "inferred": 0, "coverage_rate": 0.0}

    def tag_bullet(text: str) -> GroundedBullet:
        citations = _match_claims_to_bullet(text, claims)
        overlap = 0
        if not citations:
            citations, overlap = _match_evidence_to_bullet(text, evidence_items)
        status = "grounded" if citations else "inferred"
        grounding_stats[status] += 1
        return GroundedBullet(text=text, status=status, citations=citations)

    quick = [tag_bullet(text) for text in draft.quick_answer]
    sections: List[GroundedSection] = []
    for section in draft.details_sections or []:
        bullets = [tag_bullet(text) for text in section.bullets]
        sections.append(GroundedSection(title=section.title, bullets=bullets))

    total = grounding_stats["grounded"] + grounding_stats["inferred"] + grounding_stats["partial"]
    grounding_stats["coverage_rate"] = (grounding_stats["grounded"] / total) if total else 0.0
    return quick, sections, grounding_stats


def render_helpful_answer(
    question: str,
    plan: QuestionPlan,
    session_state: Dict[str, Any],
    evidence_items: List[Dict[str, Any]],
    claims: Optional[List[Claim]],
    use_llm: bool,
    temperature: Optional[float],
    session_id: Optional[str],
    evidence_to_citation: Optional[Dict[str, int]] = None,
    citations: Optional[List[Dict[str, Any]]] = None,
    include_sources: bool = False,
) -> Tuple[str, Dict[str, Any]]:
    draft, draft_meta = generate_draft_answer(
        question,
        plan,
        session_state,
        evidence_items,
        use_llm,
        temperature=temperature,
    )
    quick, sections, grounding_stats = ground_and_tag_draft(draft, claims, evidence_items)
    grounding_stats["draft_fallback"] = bool(draft_meta.get("fallback_used"))
    grounding_stats["draft_repair_used"] = bool(draft_meta.get("repair_used"))
    quick = quick[:5]
    if len(quick) < 3:
        quick.extend(quick[: 3 - len(quick)])
    sections = sections[:3]
    if len(sections) < 2 and sections:
        sections = sections * 2
        sections = sections[:2]
    for section in sections:
        section.bullets = section.bullets[:4]
    seed = _style_seed(session_id, question)
    missing_phrases = _pick_phrases("could_not_verify", seed, 3)
    next_phrases = _pick_phrases("next_steps", seed, 2)

    def render_bullet(bullet: GroundedBullet) -> str:
        status = "Grounded" if bullet.status == "grounded" else "Inferred"
        cite_ids = bullet.citations or []
        if evidence_to_citation:
            cite_ids = [str(evidence_to_citation.get(cid)) for cid in cite_ids if evidence_to_citation.get(cid)]
        cites = "".join([f"[{cid}]" for cid in cite_ids]) if cite_ids else ""
        return f"- {bullet.text} [{status}] {cites}".strip()

    lines: List[str] = []
    lines.append("Quick Answer")
    for bullet in quick[:5]:
        lines.append(render_bullet(bullet))

    lines.append("")
    lines.append("Details")
    for section in sections[:4]:
        lines.append(section.title)
        for bullet in section.bullets[:4]:
            lines.append(render_bullet(bullet))

    # What couldn't be verified (max 3)
    unverified = []
    for bullet in quick:
        if bullet.status == "inferred":
            unverified.append(bullet.text)
    for section in sections:
        for bullet in section.bullets:
            if bullet.status == "inferred":
                unverified.append(bullet.text)
    unverified = list(dict.fromkeys(unverified))[:3]
    if not unverified:
        unverified = [""]
    lines.append("")
    lines.append("What I couldn't verify from your corpus")
    for idx, text in enumerate(unverified[:3]):
        prefix = missing_phrases[idx % len(missing_phrases)] if missing_phrases else "Could not verify"
        if text:
            lines.append(f"- {prefix}: {text}")
        else:
            lines.append(f"- {prefix}.")

    # Next steps (max 2)
    lines.append("")
    lines.append("Next steps")
    for step in next_phrases[:2]:
        lines.append(f"- {step}")

    if include_sources and citations:
        lines.append("")
        lines.append("Sources")
        for entry in citations:
            lines.append(f"[{entry.get('id')}] {_format_citation_entry(entry)}")

    grounding_stats["grounded_bullets"] = grounding_stats.get("grounded", 0)
    grounding_stats["partial_bullets"] = grounding_stats.get("partial", 0)
    grounding_stats["inferred_bullets"] = grounding_stats.get("inferred", 0)
    return "\n".join([line for line in lines if line]).strip(), grounding_stats


def generate_existing_protocol_plan(topic: str) -> Tuple[Dict[str, Any], str]:
    """Generate a protocol plan using the existing ModuleTemplate schema."""
    try:
        from fabric.agents import biofoundry_protocol_orchestrator as bf

        modules = bf.parse_modules_library(bf.MODULE_LIB)
        if not modules:
            raise ValueError("Modules_library missing")
        template_map = bf.build_template_map(modules)
        module_lookup = bf.build_module_lookup(modules)
        meta = None
        try:
            backend = bf.get_method_backend()
        except Exception:
            backend = None
        if backend:
            case = bf.select_template_for_topic(topic, template_map, backend, readout_bias=0)
        else:
            template_key = next(iter(template_map.keys()))
            meta = template_map[template_key]
            case = {
                "case_study_title": f"{topic} ({meta['organism']} + {meta['readout']})",
                "topic": topic,
                "organism": meta["organism"],
                "readout": meta["readout"],
                "template": template_key,
                "ordered_modules": meta["ordered_modules"],
                "selection_evidence": {},
            }
        plan = bf.render_plan(case, module_lookup)
        protocol_text = bf.render_protocol(case, module_lookup)
        if not plan.get("ordered_modules"):
            ordered = case.get("ordered_modules") or (meta.get("ordered_modules") if meta else None) or ["module_1"]
            plan["ordered_modules"] = [ordered[0]] if isinstance(ordered, list) else ["module_1"]
        return plan, protocol_text
    except Exception:
        fallback_plan = {
            "case_study_title": f"{topic} (default template)",
            "organism": "Unknown",
            "readout": "Unknown",
            "closest_template_used": "ModuleTemplate/unknown",
            "ordered_modules": ["module_1"],
            "parameters_needed": [],
            "TODOs": ["Fill in organism/readout and module parameters."],
            "assumptions": ["Default module order used due to missing template data."],
            "selection_evidence": {},
        }
        protocol_text = (
            "# Protocol (default)\n"
            "1. [module_1] Define construct inputs and prepare reaction setup.\n"
            "2. [module_2] Assemble constructs and validate outputs.\n"
        )
        return fallback_plan, protocol_text


def validate_blocks(
    blocks: List[BlockUnion],
    plan: QuestionPlan,
    evidence_ids: Set[str],
) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    relax = os.environ.get("QA_RELAX_VALIDATION", "0") == "1"
    allowed_types = {t.lower() for t in plan.allowed_rank_entity_types or []}
    for block in blocks:
        if isinstance(block, RankedEntitiesBlock):
            block_type = str(block.entity_type or "").lower()
            if not allowed_types or block_type not in allowed_types:
                errors.append(f"ranked_entities type not allowed: {block.entity_type}")
            if block_type in BANNED_RANK_TYPES:
                errors.append(f"ranked_entities type banned: {block.entity_type}")
            for item in block.items:
                if not item.supporting_evidence:
                    errors.append(f"ranked item missing evidence: {item.display_name}")
                for eid in item.supporting_evidence:
                    if eid not in evidence_ids:
                        errors.append(f"ranked item cites unknown evidence: {eid}")
        if isinstance(block, DirectAnswerBlock):
            for bullet in block.bullets:
                if not relax and not bullet.citations and not _is_definitional(bullet.text):
                    errors.append("direct_answer bullet missing citations")
                for eid in bullet.citations:
                    if eid not in evidence_ids:
                        errors.append(f"direct_answer cites unknown evidence: {eid}")
        if isinstance(block, CaveatsBlock):
            for item in block.items:
                for eid in item.citations:
                    if eid not in evidence_ids:
                        errors.append(f"caveat cites unknown evidence: {eid}")
    return not errors, errors


def evaluate_abstention(
    plan: QuestionPlan,
    blocks: List[BlockUnion],
    evidence_ids: Set[str],
    forced_reason: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    if forced_reason:
        return True, forced_reason

    def ranked_items_with_citations() -> int:
        count = 0
        for block in blocks:
            if isinstance(block, RankedEntitiesBlock):
                for item in block.items:
                    if item.supporting_evidence:
                        count += 1
        return count

    for condition in plan.abstain_conditions or []:
        lowered = condition.lower().strip()
        if lowered == "planner_invalid":
            return True, "planner_invalid"
        if lowered in {"no_evidence", "missing_evidence"} and not evidence_ids:
            return True, "no_evidence"
        if lowered == "no_ranked_items":
            if ranked_items_with_citations() == 0:
                return True, "no_ranked_items"
        match = re.search(r"<\s*(\d+)\s*ranked items with citations", lowered)
        if match:
            threshold = int(match.group(1))
            if ranked_items_with_citations() < threshold:
                return True, f"ranked_items<{threshold}"
        if lowered == "missing_direct_answer":
            if not any(isinstance(block, DirectAnswerBlock) for block in blocks):
                return True, "missing_direct_answer"
    return False, None


def build_evidence_audit(
    evidence_items: List[Dict[str, Any]],
    plan: QuestionPlan,
    reason: Optional[str] = None,
) -> EvidenceAuditBlock:
    available = [item.get("title") or item.get("evidence_id") for item in evidence_items]
    missing = []
    if plan.required_signals:
        missing.append("Missing signals: " + ", ".join(plan.required_signals))
    if reason:
        missing.append(f"Abstain reason: {reason}")
    how_to_fix = [
        "Add more topic-specific PDFs or expand the workspace corpus.",
        "Increase retrieval recall or adjust query planner settings.",
    ]
    return EvidenceAuditBlock(
        type="evidence_audit",
        what_is_available=[str(item) for item in available if item],
        what_is_missing=missing,
        how_to_fix=how_to_fix,
    )


def _fallback_direct_blocks(
    evidence_items: List[Dict[str, Any]],
    plan: QuestionPlan,
    question: str,
    max_bullets: int = 4,
) -> Optional[List[BlockUnion]]:
    if not evidence_items:
        return None
    bullets: List[DirectAnswerBullet] = []
    query_tokens = set(_tokenize(question))
    candidate_types = {"enzyme", "protein", "variant", "strain", "organism"}
    signals = plan.required_signals or []
    for item in evidence_items:
        if signals and _signal_score(item.get("text", ""), signals) <= 0:
            continue
        text = (item.get("text") or "").strip()
        if not text:
            continue
        meta = item.get("metadata") or {}
        title = str(item.get("title") or meta.get("title") or "")
        text_lower = text.lower()
        if (
            "candidate summary" in title.lower()
            or text_lower.startswith("top candidate")
            or ("candidate" in text_lower and "edges=" in text_lower)
        ):
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            for line in lines:
                if line.lower().startswith("top candidate"):
                    continue
                if line.startswith("-"):
                    line = line.lstrip("- ").strip()
                if not line:
                    continue
                bullets.append(DirectAnswerBullet(text=f"Candidate: {line}.", citations=[item.get("evidence_id")]))
                if len(bullets) >= max_bullets:
                    break
            if len(bullets) >= max_bullets:
                break
        if plan.intent in {"candidate_selection", "comparison"}:
            source_type = meta.get("source_type")
            target_type = meta.get("target_type")
            if source_type not in candidate_types and target_type not in candidate_types:
                if query_tokens and not (query_tokens & set(_tokenize(text))):
                    continue
        relation = meta.get("relation")
        source = meta.get("source")
        target = meta.get("target")
        if relation and source and target:
            phrase = _relation_to_phrase(relation)
            sentence = f"{source} {phrase} {target}."
        else:
            sentence = _split_sentences(text)[0] if text else ""
        if not sentence:
            sentence = text[:200]
        bullets.append(DirectAnswerBullet(text=sentence, citations=[item.get("evidence_id")]))
        if len(bullets) >= max_bullets:
            break
    if not bullets:
        for item in evidence_items[:max_bullets]:
            text = (item.get("text") or "").strip()
            if not text:
                continue
            sentence = _split_sentences(text)[0] if text else ""
            bullets.append(DirectAnswerBullet(text=sentence or text[:200], citations=[item.get("evidence_id")]))
    if not bullets:
        return None
    return [DirectAnswerBlock(type="direct_answer", bullets=bullets)]


def compose_blocks(
    state: AgentState,
    question: str,
    plan: QuestionPlan,
    schema: Dict[str, Any],
    use_llm: bool,
    temperature: float | None = None,
    evidence_items: Optional[List[Dict[str, Any]]] = None,
    citations: Optional[List[Dict[str, Any]]] = None,
    evidence_to_citation: Optional[Dict[str, int]] = None,
    claims: Optional[List[Claim]] = None,
    use_claims: bool = False,
    strict: bool = False,
) -> Tuple[List[BlockUnion], List[Dict[str, Any]], Dict[str, Any], Dict[str, int], List[Dict[str, Any]]]:
    if evidence_items is None or citations is None or evidence_to_citation is None:
        evidence_items, citations, evidence_to_citation = build_evidence_from_state(
            state,
            max_items=DEFAULT_EVIDENCE_MAX_ITEMS,
            required_signals=plan.required_signals,
            exclude_patterns=plan.exclude_patterns,
        )
    evidence_ids = {item.get("evidence_id") for item in evidence_items if item.get("evidence_id")}

    if not use_llm or not evidence_items:
        audit = build_evidence_audit(evidence_items, plan, reason="no_llm_or_no_evidence")
        return [audit], citations, {"valid": True, "errors": []}, evidence_to_citation, evidence_items

    topic = topic_label(schema, get_workspace_root())
    required_blocks = [spec.type for spec in plan.required_blocks or []]
    evidence_lines = []
    strict_rules = ""
    if strict:
        strict_rules = (
            "- STRICT MODE: Every bullet/item must include at least one citation.\n"
            "- STRICT MODE: Keep ranked_entities items <= 5 and direct_answer bullets <= 4.\n"
            "- STRICT MODE: If you cannot satisfy requirements, output EvidenceAuditBlock only.\n"
        )

    if use_claims and claims:
        claim_evidence_ids = {claim.evidence_id for claim in claims}
        for item in evidence_items:
            if item.get("evidence_id") in claim_evidence_ids:
                evidence_lines.append(
                    f"- {item['evidence_id']}: {item.get('title') or 'evidence'} | {item.get('text','')[:240]}"
                )
        claims_payload = [claim.model_dump() for claim in claims]
        prompt = (
            "You are a structured answer composer. Output ONLY JSON list of blocks.\n"
            f"Question: {question}\n"
            f"Topic: {topic}\n"
            f"Intent: {plan.intent}\n"
            f"Required blocks: {required_blocks}\n"
            f"Allowed rank entity types: {plan.allowed_rank_entity_types}\n"
            f"Required signals: {plan.required_signals}\n"
            "Composer rules:\n"
            + strict_rules +
            "- Use ONLY the claims provided. Do not use raw evidence text beyond minimal snippets.\n"
            "- RankedEntitiesBlock rationales must be derived from claims, not raw chunks.\n"
            "- Use evidence_id values from claims for citations.\n"
            "- Do not hallucinate metrics or effects.\n"
            "- If evidence is insufficient, include EvidenceAuditBlock.\n"
            "- Output ONLY valid JSON list.\n"
            "Claims:\n"
            + json.dumps(claims_payload, ensure_ascii=True)
            + "\nEvidence snippets (for citation context only):\n"
            + "\n".join(evidence_lines)
        )
    else:
        for item in evidence_items:
            evidence_lines.append(
                f"- {item['evidence_id']}: {item.get('title') or 'evidence'} | {item.get('text','')[:600]}"
            )
        prompt = (
            "You are a structured answer composer. Output ONLY JSON list of blocks.\n"
            f"Question: {question}\n"
            f"Topic: {topic}\n"
            f"Intent: {plan.intent}\n"
            f"Required blocks: {required_blocks}\n"
            f"Allowed rank entity types: {plan.allowed_rank_entity_types}\n"
            f"Required signals: {plan.required_signals}\n"
            "Composer rules:\n"
            + strict_rules +
            "- Use evidence_id values for citations.\n"
            "- Do not hallucinate metrics or effects.\n"
            "- If evidence is insufficient, include EvidenceAuditBlock.\n"
            "- Output ONLY valid JSON list.\n"
            "Evidence:\n"
            + "\n".join(evidence_lines)
        )
    raw = None
    try:
        raw = local_llm.generate(prompt, temperature=temperature, system_prompt="Return JSON only.")
        payload = _safe_json_list(raw)
        blocks = BlocksAdapter.validate_python(payload)
    except Exception:
        if os.environ.get("QA_COMPOSER_RELAX", "1") == "1" and raw:
            topic = topic_label(schema, get_workspace_root())
            repaired = _repair_blocks_json(raw, question, topic, plan)
            if repaired:
                try:
                    payload = _safe_json_list(repaired)
                    blocks = BlocksAdapter.validate_python(payload)
                    return blocks, citations, {"valid": True, "errors": [], "raw": repaired}, evidence_to_citation, evidence_items
                except Exception:
                    pass
        if os.environ.get("QA_BLOCK_FALLBACK", "1") == "1":
            fallback_blocks = _fallback_direct_blocks(evidence_items, plan, question)
            if fallback_blocks:
                return fallback_blocks, citations, {"valid": True, "errors": ["composer_invalid_fallback"], "raw": raw}, evidence_to_citation, evidence_items
        audit = build_evidence_audit(evidence_items, plan, reason="composer_invalid")
        return [audit], citations, {"valid": False, "errors": ["composer_invalid"], "raw": raw}, evidence_to_citation, evidence_items

    valid, errors = validate_blocks(blocks, plan, evidence_ids)
    if not valid:
        audit = build_evidence_audit(evidence_items, plan, reason="validation_failed")
        return [audit], citations, {"valid": False, "errors": errors, "raw": raw}, evidence_to_citation, evidence_items

    return blocks, citations, {"valid": True, "errors": [], "raw": raw}, evidence_to_citation, evidence_items


def _format_citation_entry(citation: Dict[str, Any]) -> str:
    title = citation.get("title") or "Unknown title"
    authors = citation.get("authors")
    year = citation.get("year")
    doi = citation.get("doi")
    parts = []
    if authors:
        if isinstance(authors, list):
            authors = ", ".join(authors)
        parts.append(str(authors))
    if year:
        parts.append(str(year))
    parts.append(title)
    if doi:
        parts.append(f"DOI:{doi}")
    return " — ".join([p for p in parts if p])


def render_blocks_text(
    blocks: List[BlockUnion],
    evidence_to_citation: Dict[str, int],
    citations: List[Dict[str, Any]],
) -> str:
    lines: List[str] = []
    for block in blocks:
        if isinstance(block, DirectAnswerBlock):
            lines.append("Answer:")
            for bullet in block.bullets:
                cite = "".join([f"[{evidence_to_citation.get(eid)}]" for eid in bullet.citations if evidence_to_citation.get(eid)])
                text = bullet.text.strip()
                if "\n- " in text:
                    parts = [part.strip() for part in text.splitlines() if part.strip()]
                    head = parts[0] if parts else text
                    lines.append(f"- {head} {cite}".strip())
                    for part in parts[1:]:
                        cleaned = part.lstrip("- ").strip()
                        if cleaned:
                            lines.append(f"  {cleaned} {cite}".strip())
                else:
                    lines.append(f"- {text} {cite}".strip())
        elif isinstance(block, RankedEntitiesBlock):
            lines.append(f"Ranked {block.entity_type}:")
            for idx, item in enumerate(block.items, start=1):
                cite = "".join([f"[{evidence_to_citation.get(eid)}]" for eid in item.supporting_evidence if evidence_to_citation.get(eid)])
                lines.append(f"{idx}. {item.display_name} — {item.rationale} {cite}".strip())
        elif isinstance(block, CaveatsBlock):
            lines.append("Caveats:")
            for item in block.items:
                cite = "".join([f"[{evidence_to_citation.get(eid)}]" for eid in item.citations if evidence_to_citation.get(eid)])
                lines.append(f"- {item.text} {cite}".strip())
        elif isinstance(block, EvidenceAuditBlock):
            available = list(dict.fromkeys([item for item in block.what_is_available if item]))
            missing = list(dict.fromkeys([item for item in block.what_is_missing if item]))
            fixes = list(dict.fromkeys([item for item in block.how_to_fix if item]))
            lines.append(
                f"Evidence audit: {len(available)} sources found, {len(missing)} gaps noted."
            )
            if available:
                lines.append("Found evidence:")
                for item in available[:5]:
                    lines.append(f"- {item}")
            if missing:
                lines.append("Missing or unverified:")
                for item in missing[:3]:
                    lines.append(f"- {item}")
            if fixes:
                lines.append("How to fix:")
                for item in fixes[:2]:
                    lines.append(f"- {item}")
        elif isinstance(block, NextActionsBlock):
            lines.append("Next actions:")
            for item in block.items:
                lines.append(f"- {item}")

    if citations:
        lines.append("\nSources:")
        for c in citations:
            lines.append(f"[{c['id']}] {_format_citation_entry(c)}")
    return "\n".join([line for line in lines if line]).strip()


def render_dual_answer(helpful_answer: str, structured_answer: str) -> str:
    parts: List[str] = []
    if helpful_answer:
        parts.append("Narrative answer")
        parts.append(helpful_answer.strip())
    if structured_answer:
        parts.append("KG-structured answer")
        parts.append(structured_answer.strip())
    return "\n\n".join([p for p in parts if p]).strip()


def compute_metrics(state: AgentState, rewards: List[float]) -> Dict[str, float | None]:
    faiss_scores = [ctx.get("score") for ctx in state.context if isinstance(ctx.get("score"), (int, float))]
    kg_conf = [node.get("confidence") for node in state.graph_nodes if isinstance(node.get("confidence"), (int, float))]
    metrics = {
        "faiss_avg": sum(faiss_scores) / len(faiss_scores) if faiss_scores else None,
        "kg_conf_avg": sum(kg_conf) / len(kg_conf) if kg_conf else None,
        "rl_reward_sum": sum(rewards) if rewards else None,
    }
    return metrics


def log_trajectory(question: str, steps: List[Dict[str, Any]], answer: str, rewards: List[float]) -> None:
    payload = {
        "question": question,
        "steps": steps,
        "answer": answer,
        "rewards": rewards,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def run_agent(
    question: str,
    use_llm: bool = DEFAULT_USE_LLM,
    seed: int = 7,
    policy_model: Optional[Any] = None,
    temperature: float | None = None,
) -> Dict[str, Any]:
    random.seed(seed)
    workspace_root = get_workspace_root()
    backend = get_backend(workspace_root)
    schema = load_schema(workspace_root)
    if backend.graph is None and not VECTOR_ONLY_RAG:
        raise SystemExit("KG graph not found for this workspace. Set VECTOR_ONLY_RAG=1 to run without KG.")
    graph_overview_path = workspace_root / "graph_overview.json"
    env = RetrievalEnvironment(backend, schema, graph_overview_path)
    heuristic_policy = SimplePolicy()
    state = env.reset(question)
    done = False
    trajectory = []
    rewards = []

    graph_available = backend.graph is not None and not VECTOR_ONLY_RAG

    while not done:
        if policy_model is not None:
            obs = state_to_observation(state)
            action_idx, _ = policy_model.predict(obs, deterministic=True)
            action = ACTIONS[int(action_idx)]
        else:
            action = heuristic_policy.select(state, graph_available=graph_available)

        # Action masking when graph is absent or disabled.
        if action == "graph_expand" and not graph_available:
            action = "summarize" if state.context else "vector_search"
        state, reward, done, info = env.step(action)
        trajectory.append({"action": action, "info": info, "context_size": len(state.context)})
        rewards.append(reward)
        if action == "summarize":
            done = True
            break

    expected = expected_entities_from_question(question, schema)
    if expected:
        augment_with_expected_entities(state, backend, expected)
    answer, citations = summarize_context(state, use_llm, question, schema, temperature=temperature)
    draft_answer = answer
    metrics = compute_metrics(state, rewards)
    log_trajectory(question, trajectory, answer, rewards)
    log_event(
        {
            "event": "rl_agent_run",
            "question": question,
            "trajectory": trajectory,
            "answer": answer,
            "use_llm": use_llm,
            "metrics": metrics,
        }
    )
    return {
        "answer": answer,
        "citations": citations,
        "metrics": metrics,
        "trajectory": trajectory,
        "rewards": rewards,
        "use_llm": use_llm,
    }


def _truncate_text(text: str, limit: int = 500) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _collect_dense_hits(backend: RetrievalBackend, query: str, top_k: int) -> List[Dict[str, Any]]:
    results = backend.vector_search(query, top_k=top_k)
    hits = []
    for rank, row in enumerate(results, start=1):
        meta = row.get("metadata", {})
        hits.append(
            {
                "id": meta.get("chunk_id") or meta.get("source"),
                "score": float(row.get("score", 0.0)),
                "rank": rank,
                "text": row.get("text", ""),
                "metadata": meta,
            }
        )
    return hits


def _collect_keyword_hits(backend: RetrievalBackend, query: str, top_k: int) -> List[Dict[str, Any]]:
    if not hasattr(backend, "keyword_search"):
        return []
    results = backend.keyword_search(query, top_k=top_k)
    hits = []
    for rank, row in enumerate(results, start=1):
        meta = row.get("metadata", {})
        hits.append(
            {
                "id": meta.get("chunk_id") or meta.get("source"),
                "score": float(row.get("score", 0.0)),
                "rank": rank,
                "text": row.get("text", ""),
                "metadata": meta,
            }
        )
    return hits


def _assemble_candidates(rrf_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates = []
    for doc_id, payload in rrf_map.items():
        items = payload.get("items", [])
        if not items:
            continue
        dense_score = 0.0
        bm25_score = 0.0
        exemplar = items[0]
        for item in items:
            score = float(item.get("score", 0.0))
            if item.get("source") == "dense":
                dense_score = max(dense_score, score)
            elif item.get("source") == "bm25":
                bm25_score = max(bm25_score, score)
        candidates.append(
            {
                "id": doc_id,
                "text": exemplar.get("text", ""),
                "metadata": exemplar.get("metadata", {}),
                "rrf_score": payload.get("rrf_score", 0.0),
                "dense_score": dense_score,
                "bm25_score": bm25_score,
            }
        )
    return candidates


def run_qa(
    question: str,
    use_llm: bool,
    temperature: float | None,
    use_kg: bool,
    enable_query_planner: bool,
    enable_bm25: bool,
    enable_rerank: bool,
    enable_verifier: bool,
    use_understanding_layer: Optional[bool],
    use_claim_store: bool,
    persist_claims: bool,
    use_langgraph_qa: bool = False,
    session_id: str | None = None,
    chat_mode: bool = False,
    use_rl_policy: bool = False,
    policy_model: Optional[Any] = None,
    output_mode: str = "answer_strict",
    seed: int = 7,
) -> Dict[str, Any]:
    random.seed(seed)
    workspace_root = get_workspace_root()
    schema = load_schema(workspace_root)
    topic = topic_label(schema, workspace_root)
    if persist_claims and not use_claim_store:
        persist_claims = False
    if output_mode not in OUTPUT_MODES:
        output_mode = "answer_strict"
    run_id = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    trace: List[str] = []
    grounding_stats: Dict[str, Any] = {}

    if output_mode == "protocol" and not use_langgraph_qa:
        trace.extend(["protocol_generate", "protocol_render", "finalize"])
        protocol_plan, protocol_text = generate_existing_protocol_plan(question)
        write_run_summary(
            topic=topic,
            run_id=run_id,
            query=question,
            output_mode=output_mode,
            intent="protocol_request",
            graph_enabled=False,
            nodes_visited=trace,
            used_general_answer_agent=False,
            used_claims_lite=False,
            fallback_path="none",
            validation_pass=True,
            validation_reason="protocol_mode",
            counts={"grounded": 0, "partial": 0, "inferred": 0},
            selected_evidence_ids_count=0,
            render_template_id="module_template_v1",
            citations_count=0,
            abstain=False,
        )
        return {
            "answer": protocol_text,
            "citations": [],
            "metrics": {},
            "trajectory": [{"action": "protocol"}],
            "use_llm": use_llm,
            "blocks": [],
            "protocol": protocol_plan,
        }

    session_id = session_id or generate_session_id()
    session_state = load_session_state(topic, session_id) if chat_mode else {
        "rolling_summary": "",
        "entity_memory": [],
        "cited_sources": [],
        "open_questions": [],
        "working_set_entities": [],
        "open_slots": [],
        "last_intent": "",
        "turn": 0,
    }

    intent = detect_intent(question)
    plan, planner_valid, planner_raw, planner_error = plan_question(
        question, schema, session_state, use_llm
    )
    trace.append("plan_question")
    forced_abstain_reason = None if planner_valid else "planner_invalid"
    planner_intent = plan.intent
    use_understanding_layer = (
        use_understanding_layer if use_understanding_layer is not None
        else intent in {"candidate_selection", "compare_candidates"}
    )

    if use_understanding_layer and intent in {"candidate_selection", "compare_candidates", "paper_limitations"}:
        layer, issue = understanding_layer_status(workspace_root)
        trace.append("understanding_layer_check")
        if issue is not None or layer is None:
            trace.append("compose_blocks")
            blocks = [build_evidence_audit([], plan, reason="understanding_layer_missing")]
            citations: List[Dict[str, Any]] = []
            evidence_to_citation: Dict[str, int] = {}
            structured_answer = render_blocks_text(blocks, evidence_to_citation, citations)
            helpful_answer = None
            answer_for_verifier = structured_answer
            if output_mode in ("answer_helpful", "answer_dual"):
                helpful_answer, grounding_stats = render_helpful_answer(
                    question,
                    plan,
                    session_state,
                    [],
                    None,
                    use_llm=use_llm,
                    temperature=temperature,
                    session_id=session_id,
                    evidence_to_citation=evidence_to_citation,
                    citations=citations,
                    include_sources=(output_mode == "answer_helpful"),
                )
                answer_for_verifier = helpful_answer
                trace.append("render_helpful")
            if output_mode == "answer_helpful":
                answer = helpful_answer or structured_answer
            elif output_mode == "answer_dual":
                answer = render_dual_answer(helpful_answer or structured_answer, structured_answer)
            else:
                answer = structured_answer
            validation = {"valid": True, "errors": []}
            abstain = True
            abstain_reason = "understanding_layer_missing"
            metrics = {
                "steps": 0,
                "unique_citations": 0,
                "coverage_proxy": coverage_proxy(answer_for_verifier),
                "unsupported_sentence_rate": 1.0,
            }
            sentence_map = build_sentence_map(answer_for_verifier, citations)
            verifier = {"unsupported_sentence_rate": unsupported_sentence_rate_from_map(sentence_map)}
            if enable_verifier:
                verified, verifier = verify_answer(answer_for_verifier, sentence_map=sentence_map)
                answer_for_verifier = verified
                if output_mode != "answer_dual":
                    answer = verified
                sentence_map = build_sentence_map(answer_for_verifier, citations)

            turn_id = int(session_state.get("turn", 0)) + 1
            session_state = update_session_state(session_state, question, answer, [], intent=planner_intent)
            report = (
                f"# QA run report\n\n"
                f"- steps: {metrics['steps']}\n"
                f"- unique_citations: {metrics['unique_citations']}\n"
                f"- coverage_proxy: {metrics['coverage_proxy']}\n"
                f"- unsupported_sentence_rate: {metrics['unsupported_sentence_rate']}\n"
            )
            trace.append("finalize")
            save_run_bundle(
                topic,
                session_id,
                turn_id,
                {
                    "input": {
                        "question": question,
                        "use_llm": use_llm,
                        "temperature": temperature,
                        "use_kg": use_kg,
                        "enable_query_planner": enable_query_planner,
                        "enable_bm25": enable_bm25,
                        "enable_rerank": enable_rerank,
                        "enable_verifier": enable_verifier,
                        "output_mode": output_mode,
                        "use_claim_store": use_claim_store,
                        "persist_claims": persist_claims,
                        "chat_mode": chat_mode,
                        "use_rl_policy": False,
                        "use_understanding_layer": use_understanding_layer,
                        "intent": intent,
                        "understanding_layer_issue": issue,
                    },
                    "planner": {
                        "plan": plan.model_dump(),
                        "valid": planner_valid,
                        "error": planner_error,
                        "raw": planner_raw,
                    },
                    "queries": {},
                    "retrieval": {"mode": "understanding_layer"},
                    "fusion": {},
                    "rerank": {},
                    "answer": {
                        "draft": answer_for_verifier,
                        "final": answer,
                        "helpful": helpful_answer,
                        "structured": structured_answer,
                        "citations": citations,
                        "blocks": [block.model_dump() for block in blocks],
                    },
                    "claims": {"enabled": False},
                    "validation": validation,
                    "abstain": {"triggered": abstain, "reason": abstain_reason},
                    "selected_evidence_ids": [],
                    "verifier": {"unsupported_sentence_rate": metrics["unsupported_sentence_rate"]},
                    "session_state": session_state,
                    "report": report,
                    "index_row": {
                        "turn": turn_id,
                        "steps": metrics["steps"],
                        "unique_citations": metrics["unique_citations"],
                        "coverage_proxy": metrics["coverage_proxy"],
                        "unsupported_sentence_rate": metrics["unsupported_sentence_rate"],
                    },
                },
            )
            counts = {
                "grounded": int(grounding_stats.get("grounded_bullets", 0)),
                "partial": int(grounding_stats.get("partial_bullets", 0)),
                "inferred": int(grounding_stats.get("inferred_bullets", 0)),
            }
            write_run_summary(
                topic=topic,
                run_id=run_id,
                query=question,
                output_mode=output_mode,
                intent=planner_intent,
                graph_enabled=False,
                nodes_visited=trace,
                used_general_answer_agent=(output_mode in ("answer_helpful", "answer_dual")),
                used_claims_lite=False,
                fallback_path="abstain",
                validation_pass=bool(validation.get("valid")),
                validation_reason=abstain_reason,
                counts=counts,
                selected_evidence_ids_count=0,
                render_template_id="dual_v1"
                if output_mode == "answer_dual"
                else "helpful_v1"
                if output_mode == "answer_helpful"
                else "blocks_v1",
                citations_count=0,
                abstain=True,
            )
            return {
                "answer": answer,
                "answer_helpful": helpful_answer,
                "answer_structured": structured_answer,
                "citations": [],
                "metrics": metrics,
                "trajectory": [],
                "use_llm": False,
                "intent": intent,
            }

        if intent in {"candidate_selection", "compare_candidates"}:
            trace.append("compose_blocks")
            blocks, citations, evidence_to_citation = build_candidate_blocks(layer, question, plan)
        else:
            trace.append("compose_blocks")
            blocks, citations, evidence_to_citation = build_reflection_blocks(layer, plan)
        evidence_ids = set(evidence_to_citation.keys())
        trace.append("verify_blocks")
        valid, errors = validate_blocks(blocks, plan, evidence_ids)
        validation = {"valid": valid, "errors": errors}
        abstain = False
        abstain_reason = None
        if not valid:
            abstain = True
            abstain_reason = "validation_failed"
            blocks = [build_evidence_audit([], plan, reason=abstain_reason)]
        else:
            abstain, abstain_reason = evaluate_abstention(plan, blocks, evidence_ids, forced_abstain_reason)
        if abstain:
            blocks = [build_evidence_audit([], plan, reason=abstain_reason)]
        structured_answer = render_blocks_text(blocks, evidence_to_citation, citations)
        helpful_answer = None
        answer_for_verifier = structured_answer
        if output_mode in ("answer_helpful", "answer_dual"):
            helpful_answer, grounding_stats = render_helpful_answer(
                question,
                plan,
                session_state,
                [],
                None,
                use_llm=use_llm,
                temperature=temperature,
                session_id=session_id,
                evidence_to_citation=evidence_to_citation,
                citations=citations,
                include_sources=(output_mode == "answer_helpful"),
            )
            answer_for_verifier = helpful_answer
            trace.append("render_helpful")
        if output_mode == "answer_helpful":
            answer = helpful_answer or structured_answer
        elif output_mode == "answer_dual":
            answer = render_dual_answer(helpful_answer or structured_answer, structured_answer)
        else:
            answer = structured_answer

        sentence_map = build_sentence_map(answer_for_verifier, citations)
        verifier = {"unsupported_sentence_rate": unsupported_sentence_rate_from_map(sentence_map)}
        if enable_verifier:
            verified, verifier = verify_answer(answer_for_verifier, sentence_map=sentence_map)
            answer_for_verifier = verified
            if output_mode != "answer_dual":
                answer = verified
            sentence_map = build_sentence_map(answer_for_verifier, citations)

        turn_id = int(session_state.get("turn", 0)) + 1
        session_state = update_session_state(session_state, question, answer, citations, intent=planner_intent)
        metrics = {
            "steps": 0,
            "unique_citations": len({c.get("id") for c in citations if c.get("id")}),
            "coverage_proxy": coverage_proxy(answer_for_verifier),
            "unsupported_sentence_rate": verifier.get("unsupported_sentence_rate", 1.0),
        }
        report = (
            f"# QA run report\n\n"
            f"- steps: {metrics['steps']}\n"
            f"- unique_citations: {metrics['unique_citations']}\n"
            f"- coverage_proxy: {metrics['coverage_proxy']}\n"
            f"- unsupported_sentence_rate: {metrics['unsupported_sentence_rate']}\n"
        )
        trace.append("finalize")
        save_run_bundle(
            topic,
            session_id,
            turn_id,
            {
                    "input": {
                        "question": question,
                        "use_llm": use_llm,
                        "temperature": temperature,
                        "use_kg": use_kg,
                        "enable_query_planner": enable_query_planner,
                        "enable_bm25": enable_bm25,
                        "enable_rerank": enable_rerank,
                        "enable_verifier": enable_verifier,
                        "output_mode": output_mode,
                        "use_claim_store": use_claim_store,
                        "persist_claims": persist_claims,
                        "chat_mode": chat_mode,
                        "use_rl_policy": False,
                        "use_understanding_layer": use_understanding_layer,
                        "intent": intent,
                        "understanding_layer_issue": None,
                },
                "planner": {
                    "plan": plan.model_dump(),
                    "valid": planner_valid,
                    "error": planner_error,
                    "raw": planner_raw,
                },
                "queries": {},
                "retrieval": {"mode": "understanding_layer"},
                "fusion": {},
                "rerank": {},
                    "answer": {
                        "draft": answer_for_verifier,
                        "final": answer,
                        "helpful": helpful_answer,
                        "structured": structured_answer,
                        "citations": citations,
                        "sentence_map": sentence_map,
                        "blocks": [block.model_dump() for block in blocks],
                    },
                    "selected_evidence_ids": list(evidence_ids),
                    "validation": validation,
                    "abstain": {"triggered": abstain, "reason": abstain_reason},
                    "claims": {"enabled": False},
                    "verifier": verifier | {"sentence_map": sentence_map},
                    "session_state": session_state,
                    "report": report,
                    "index_row": {
                    "turn": turn_id,
                    "steps": metrics["steps"],
                    "unique_citations": metrics["unique_citations"],
                    "coverage_proxy": metrics["coverage_proxy"],
                    "unsupported_sentence_rate": metrics["unsupported_sentence_rate"],
                },
            },
        )
        counts = {
            "grounded": int(grounding_stats.get("grounded_bullets", 0)),
            "partial": int(grounding_stats.get("partial_bullets", 0)),
            "inferred": int(grounding_stats.get("inferred_bullets", 0)),
        }
        fallback_path = "abstain" if abstain else ("draft_fallback" if grounding_stats.get("draft_fallback") else "none")
        write_run_summary(
            topic=topic,
            run_id=run_id,
            query=question,
            output_mode=output_mode,
            intent=planner_intent,
            graph_enabled=False,
            nodes_visited=trace,
            used_general_answer_agent=(output_mode in ("answer_helpful", "answer_dual")),
            used_claims_lite=False,
            fallback_path=fallback_path,
            validation_pass=bool(validation.get("valid")),
            validation_reason=abstain_reason or (validation.get("errors") or [None])[0],
            counts=counts,
            selected_evidence_ids_count=len(evidence_ids),
            render_template_id="dual_v1"
            if output_mode == "answer_dual"
            else "helpful_v1"
            if output_mode == "answer_helpful"
            else "blocks_v1",
            citations_count=len(citations),
            abstain=abstain,
        )
        return {
            "answer": answer,
            "answer_helpful": helpful_answer,
            "answer_structured": structured_answer,
            "citations": citations,
            "metrics": metrics,
            "trajectory": [],
            "use_llm": False,
            "intent": intent,
        }

    if use_rl_policy:
        result = run_agent(
            question,
            use_llm=use_llm,
            seed=7,
            policy_model=policy_model,
            temperature=temperature,
        )
        draft_answer = result.get("answer", "")
        citations = result.get("citations", [])
        sentence_map = build_sentence_map(draft_answer, citations)
        verifier = {"unsupported_sentence_rate": unsupported_sentence_rate_from_map(sentence_map)}
        if enable_verifier:
            verified, verifier = verify_answer(draft_answer, sentence_map=sentence_map)
            result["answer"] = verified
            sentence_map = build_sentence_map(verified, citations)
        answer = result.get("answer", "")
        metrics = {
            "steps": len(result.get("trajectory", [])),
            "unique_citations": len({c.get("id") for c in citations if c.get("id")}),
            "coverage_proxy": coverage_proxy(answer),
            "unsupported_sentence_rate": verifier.get("unsupported_sentence_rate", 1.0),
        }
        turn_id = int(session_state.get("turn", 0)) + 1
        session_state = update_session_state(session_state, question, answer, citations, intent=planner_intent)
        report = (
            f"# QA run report\n\n"
            f"- steps: {metrics['steps']}\n"
            f"- unique_citations: {metrics['unique_citations']}\n"
            f"- coverage_proxy: {metrics['coverage_proxy']}\n"
            f"- unsupported_sentence_rate: {metrics['unsupported_sentence_rate']}\n"
        )
        save_run_bundle(
            topic,
            session_id,
            turn_id,
            {
                "input": {"question": question, "use_llm": use_llm, "use_rl_policy": True},
                "planner": {
                    "plan": plan.model_dump(),
                    "valid": planner_valid,
                    "error": planner_error,
                    "raw": planner_raw,
                },
                "queries": {"original": question, "rewritten": question, "subqueries": []},
                "retrieval": {"mode": "rl_policy"},
                "fusion": {},
                "rerank": {},
                "answer": {
                    "draft": draft_answer,
                    "final": answer,
                    "citations": citations,
                    "sentence_map": sentence_map,
                    "blocks": [],
                },
                "claims": {"enabled": False},
                "verifier": verifier | {"sentence_map": sentence_map},
                "session_state": session_state,
                "report": report,
                "index_row": {
                    "turn": turn_id,
                    "steps": metrics["steps"],
                    "unique_citations": metrics["unique_citations"],
                    "coverage_proxy": metrics["coverage_proxy"],
                    "unsupported_sentence_rate": metrics["unsupported_sentence_rate"],
                },
            },
        )
        result["metrics"] = metrics
        return result

    if use_langgraph_qa and not use_understanding_layer:
        from fabric.agents.qa_graph import run_qa_graph
        graph_result = run_qa_graph(
            query=question,
            session_state=session_state,
            config={
                "use_llm": use_llm,
                "temperature": temperature,
                "use_kg": use_kg,
                "enable_query_planner": enable_query_planner,
                "enable_bm25": enable_bm25,
                "enable_rerank": enable_rerank,
                "enable_verifier": enable_verifier,
                "use_claims_lite": use_claim_store,
                "persist_claims": persist_claims,
                "session_id": session_id or "",
                "output_mode": output_mode,
                "top_k": DEFAULT_TOP_K,
                "rerank_top_k": DEFAULT_RERANK_TOP_K,
                "rrf_k": DEFAULT_RRF_K,
                "evidence_max_items": DEFAULT_EVIDENCE_MAX_ITEMS,
                "method_evidence_k": int(os.environ.get("QA_METHOD_EVIDENCE_K", "6")),
                "kg_edge_evidence_k": int(os.environ.get("QA_KG_EDGE_EVIDENCE_K", "20")),
                "kg_candidate_evidence_k": int(os.environ.get("QA_KG_CANDIDATE_EVIDENCE_K", "8")),
            },
        )
        graph_result["intent"] = intent
        return graph_result

    backend = get_backend(workspace_root)
    planned = {
        "original": question,
        "planner_intent": plan.intent,
        "retrieval_queries": plan.retrieval_queries,
        "exclude_patterns": plan.exclude_patterns,
        "required_blocks": [spec.type for spec in plan.required_blocks or []],
    }
    query_list = plan.retrieval_queries or [question]
    trace.append("retrieve_evidence")
    query_for_rerank = query_list[0]

    dense_hits: Dict[str, List[Dict[str, Any]]] = {}
    bm25_hits: Dict[str, List[Dict[str, Any]]] = {}
    rrf_inputs = []

    for q in query_list:
        dense = _collect_dense_hits(backend, q, DEFAULT_TOP_K)
        dense_hits[q] = dense
        for item in dense:
            item["source"] = "dense"
        rrf_inputs.append(dense)

        if enable_bm25:
            bm25 = _collect_keyword_hits(backend, q, DEFAULT_TOP_K)
            bm25_hits[q] = bm25
            for item in bm25:
                item["source"] = "bm25"
            rrf_inputs.append(bm25)

    fused = rrf_fuse(rrf_inputs, k=DEFAULT_RRF_K)
    candidates = _assemble_candidates(fused)
    if enable_rerank:
        selected, rerank_all = rerank_candidates(
            candidates,
            query_for_rerank,
            top_k=DEFAULT_RERANK_TOP_K,
            exclude_patterns=plan.exclude_patterns,
        )
    else:
        if plan.exclude_patterns:
            for cand in candidates:
                lowered = (cand.get("text") or "").lower()
                penalty = 0.0
                for pattern in plan.exclude_patterns:
                    if pattern and pattern.lower() in lowered:
                        penalty += EXCLUDE_PENALTY
                cand["rrf_score"] = cand.get("rrf_score", 0.0) - penalty
        rerank_all = sorted(candidates, key=lambda item: item.get("rrf_score", 0.0), reverse=True)
        selected = rerank_all[:DEFAULT_RERANK_TOP_K]

    context = []
    for item in selected:
        context.append(
            {
                "text": item.get("text", ""),
                "metadata": item.get("metadata", {}),
                "score": item.get("rerank_score", item.get("rrf_score", 0.0)),
            }
        )

    graph_nodes: List[Dict[str, Any]] = []
    if use_kg and backend.graph is not None:
        context_sources = [
            ctx.get("metadata", {}).get("source")
            for ctx in context
            if ctx.get("metadata", {}).get("source")
        ]
        graph_overview_path = workspace_root / "graph_overview.json"
        seeds = select_graph_seeds(context_sources, query_for_rerank, schema, graph_overview_path, max_seeds=6)
        if seeds:
            graph_nodes = backend.graph_neighbors_diverse(seeds, top_k=10)

    steps = 1 + (1 if (use_kg and backend.graph is not None) else 0)
    state = AgentState(question=question, context=context, graph_nodes=graph_nodes, steps=steps)
    method_evidence = []
    if plan.required_signals:
        method_evidence = collect_methodology_evidence(
            question,
            limit=int(os.environ.get("QA_METHOD_EVIDENCE_K", "6")),
            required_signals=plan.required_signals,
        )
    kg_edge_evidence = collect_kg_edge_evidence(
        workspace_root,
        question,
        plan,
        schema,
        limit=int(os.environ.get("QA_KG_EDGE_EVIDENCE_K", "20")),
    )
    candidate_evidence = []
    if plan.intent in {"candidate_selection", "comparison"}:
        candidate_evidence = collect_candidate_evidence(
            workspace_root,
            question,
            plan,
            schema,
            limit=int(os.environ.get("QA_KG_CANDIDATE_EVIDENCE_K", "8")),
        )
    extra_evidence = []
    if candidate_evidence:
        extra_evidence.extend(candidate_evidence)
    if method_evidence:
        extra_evidence.extend(method_evidence)
    if kg_edge_evidence:
        extra_evidence.extend(kg_edge_evidence)
    evidence_items, citations, evidence_to_citation = build_evidence_from_state(
        state,
        max_items=DEFAULT_EVIDENCE_MAX_ITEMS,
        extra_evidence=extra_evidence,
        required_signals=plan.required_signals,
        exclude_patterns=plan.exclude_patterns,
    )
    claims: List[Claim] = []
    claim_stats: Dict[str, Any] = {
        "enabled": use_claim_store,
        "extracted": 0,
        "relations": [],
        "canonicalized_rate": 0.0,
        "selected_claim_ids": [],
        "fallback_reason": None,
    }
    blocks: List[BlockUnion]
    validation: Dict[str, Any]
    if use_claim_store:
        trace.append("maybe_extract_claims")
        claims, claim_stats_update = extract_claims_from_evidence(
            evidence_items,
            plan,
            schema,
            use_llm=use_llm,
        )
        claim_stats.update(claim_stats_update)
        claim_stats["extracted"] = len(claims)
        if persist_claims and claims:
            append_claims_to_store(workspace_root, claims)
            index = load_claim_index(workspace_root)
            index = update_claim_index(index, claims)
            persist_claim_index(workspace_root, index)

        if claims_are_sufficient(claims):
            trace.append("compose_blocks")
            blocks, citations, validation, evidence_to_citation, evidence_items = compose_blocks(
                state,
                question,
                plan,
                schema,
                use_llm,
                temperature=temperature,
                evidence_items=evidence_items,
                citations=citations,
                evidence_to_citation=evidence_to_citation,
                claims=claims,
                use_claims=True,
            )
            if not validation.get("valid"):
                claim_stats["fallback_reason"] = "claim_validation_failed"
                trace.append("compose_blocks")
                blocks, citations, validation, evidence_to_citation, evidence_items = compose_blocks(
                    state,
                    question,
                    plan,
                    schema,
                    use_llm,
                    temperature=temperature,
                    evidence_items=evidence_items,
                    citations=citations,
                    evidence_to_citation=evidence_to_citation,
                    claims=None,
                    use_claims=False,
                )
        else:
            claim_stats["fallback_reason"] = "claims_too_few"
            trace.append("compose_blocks")
            blocks, citations, validation, evidence_to_citation, evidence_items = compose_blocks(
                state,
                question,
                plan,
                schema,
                use_llm,
                temperature=temperature,
                evidence_items=evidence_items,
                citations=citations,
                evidence_to_citation=evidence_to_citation,
                claims=None,
                use_claims=False,
            )
    else:
        trace.append("compose_blocks")
        blocks, citations, validation, evidence_to_citation, evidence_items = compose_blocks(
            state,
            question,
            plan,
            schema,
            use_llm,
            temperature=temperature,
            evidence_items=evidence_items,
            citations=citations,
            evidence_to_citation=evidence_to_citation,
            claims=None,
            use_claims=False,
        )
    evidence_ids = set(evidence_to_citation.keys())
    trace.append("verify_blocks")
    abstain, abstain_reason = evaluate_abstention(plan, blocks, evidence_ids, forced_abstain_reason)
    if abstain:
        blocks = [build_evidence_audit(evidence_items, plan, reason=abstain_reason)]
    if use_claim_store and claims:
        claim_stats["selected_claim_ids"] = select_claim_ids_for_blocks(claims, blocks)
    structured_answer = render_blocks_text(blocks, evidence_to_citation, citations)
    helpful_answer = None
    answer_for_verifier = structured_answer
    if output_mode in ("answer_helpful", "answer_dual"):
        helpful_answer, grounding_stats = render_helpful_answer(
            question,
            plan,
            session_state,
            evidence_items,
            claims if use_claim_store else None,
            use_llm=use_llm,
            temperature=temperature,
            session_id=session_id,
            evidence_to_citation=evidence_to_citation,
            citations=citations,
            include_sources=(output_mode == "answer_helpful"),
        )
        answer_for_verifier = helpful_answer
        trace.append("render_helpful")
    if output_mode == "answer_helpful":
        answer = helpful_answer or structured_answer
    elif output_mode == "answer_dual":
        answer = render_dual_answer(helpful_answer or structured_answer, structured_answer)
    else:
        answer = structured_answer
    draft_answer = answer_for_verifier

    verifier = {
        "unsupported_sentence_rate": 0.0 if validation.get("valid") and not abstain else 1.0,
        "citation_concentration": citation_concentration(answer_for_verifier),
        "contradiction_proxy": contradiction_proxy(answer_for_verifier),
    }
    sentence_map = build_sentence_map(answer_for_verifier, citations)
    if enable_verifier:
        verified, verifier = verify_answer(answer_for_verifier, sentence_map=sentence_map)
        answer_for_verifier = verified
        if output_mode != "answer_dual":
            answer = verified
        sentence_map = build_sentence_map(answer_for_verifier, citations)

    turn_id = int(session_state.get("turn", 0)) + 1
    session_state = update_session_state(session_state, question, answer, citations, intent=planner_intent)
    metrics = {
        "steps": steps,
        "unique_citations": len({c.get("id") for c in citations if c.get("id")}),
        "coverage_proxy": coverage_proxy(answer_for_verifier),
        "unsupported_sentence_rate": verifier.get("unsupported_sentence_rate", 1.0),
    }

    report = (
        f"# QA run report\n\n"
        f"- steps: {metrics['steps']}\n"
        f"- unique_citations: {metrics['unique_citations']}\n"
        f"- coverage_proxy: {metrics['coverage_proxy']}\n"
        f"- unsupported_sentence_rate: {metrics['unsupported_sentence_rate']}\n"
    )
    trace.append("finalize")

    save_run_bundle(
        topic,
        session_id,
        turn_id,
        {
            "input": {
                "question": question,
                "use_llm": use_llm,
                "temperature": temperature,
                "use_kg": use_kg,
                "enable_query_planner": enable_query_planner,
                "enable_bm25": enable_bm25,
                "enable_rerank": enable_rerank,
                "enable_verifier": enable_verifier,
                "output_mode": output_mode,
                "use_claim_store": use_claim_store,
                "persist_claims": persist_claims,
                "chat_mode": chat_mode,
                "use_rl_policy": False,
                "use_understanding_layer": use_understanding_layer,
                "intent": intent,
            },
            "planner": {
                "plan": plan.model_dump(),
                "valid": planner_valid,
                "error": planner_error,
                "raw": planner_raw,
            },
            "queries": planned,
            "retrieval": {
                "dense": {q: [{"id": h["id"], "score": h["score"], "source": h["metadata"].get("source"), "title": h["metadata"].get("title"), "text": _truncate_text(h["text"])} for h in hits] for q, hits in dense_hits.items()},
                "bm25": {q: [{"id": h["id"], "score": h["score"], "source": h["metadata"].get("source"), "title": h["metadata"].get("title"), "text": _truncate_text(h["text"])} for h in hits] for q, hits in bm25_hits.items()},
            },
            "fusion": {
                "rrf": [
                    {"id": cid, "rrf_score": payload.get("rrf_score", 0.0)}
                    for cid, payload in fused.items()
                ]
            },
            "rerank": {
                "selected": [
                    {"id": item.get("id"), "rerank_score": item.get("rerank_score", 0.0), "dense_score": item.get("dense_score", 0.0), "bm25_score": item.get("bm25_score", 0.0)}
                    for item in selected
                ],
                "all": [
                    {"id": item.get("id"), "rerank_score": item.get("rerank_score", 0.0), "dense_score": item.get("dense_score", 0.0), "bm25_score": item.get("bm25_score", 0.0)}
                    for item in rerank_all
                ],
            },
            "answer": {
                "draft": draft_answer,
                "final": answer,
                "helpful": helpful_answer,
                "structured": structured_answer,
                "citations": citations,
                "sentence_map": sentence_map,
                "blocks": [block.model_dump() for block in blocks],
            },
            "claims": claim_stats,
            "validation": validation,
            "abstain": {"triggered": abstain, "reason": abstain_reason},
            "selected_evidence_ids": list(evidence_ids),
            "verifier": verifier | {"sentence_map": sentence_map},
            "session_state": session_state,
            "report": report,
            "index_row": {
                "turn": turn_id,
                "steps": metrics["steps"],
                "unique_citations": metrics["unique_citations"],
                "coverage_proxy": metrics["coverage_proxy"],
                "unsupported_sentence_rate": metrics["unsupported_sentence_rate"],
            },
        },
    )

    return {
        "answer": answer,
        "answer_helpful": helpful_answer,
        "answer_structured": structured_answer,
        "citations": citations,
        "metrics": metrics,
        "trajectory": [{"action": "vector_search"}, {"action": "graph_expand"}] if steps == 2 else [{"action": "vector_search"}],
        "use_llm": use_llm,
        "blocks": [block.model_dump() for block in blocks],
        "claims": claim_stats,
    }


app = typer.Typer(add_completion=False)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Natural-language question for the topic agent."),
    use_llm: bool = typer.Option(
        DEFAULT_USE_LLM,
        "--use-llm/--no-llm",
        help="Toggle the local LLM summarizer.",
    ),
    temperature: float = typer.Option(
        0.0,
        help="LLM temperature for summarization (ignored when --no-llm).",
    ),
    use_kg: bool = typer.Option(
        True,
        "--use-kg/--no-kg",
        help="Toggle KG expansion for the QA agent.",
    ),
    query_planner: bool = typer.Option(
        True,
        "--query-planner/--no-query-planner",
        help="Enable deterministic query rewriting + decomposition.",
    ),
    bm25: bool = typer.Option(
        True,
        "--bm25/--no-bm25",
        help="Enable keyword/BM25 retrieval with RRF fusion.",
    ),
    rerank: bool = typer.Option(
        True,
        "--rerank/--no-rerank",
        help="Enable deterministic reranking of fused candidates.",
    ),
    verifier: bool = typer.Option(
        True,
        "--verifier/--no-verifier",
        help="Enable the citation verifier gate.",
    ),
    use_claim_store: bool = typer.Option(
        False,
        "--use-claim-store/--no-claim-store",
        help="Enable claims-lite extraction + composition.",
    ),
    persist_claims: bool = typer.Option(
        False,
        "--persist-claims/--no-persist-claims",
        help="Persist extracted claims to claim_store.",
    ),
    use_langgraph_qa: bool = typer.Option(
        False,
        "--use-langgraph-qa/--no-langgraph-qa",
        help="Enable LangGraph-based QA orchestration.",
    ),
    output_mode: str = typer.Option(
        "answer_strict",
        "--output-mode",
        help="Output mode: answer_strict, answer_helpful, answer_dual, or protocol.",
    ),
    chat_mode: bool = typer.Option(
        False,
        "--chat/--no-chat",
        help="Enable multi-turn session memory.",
    ),
    use_understanding_layer: Optional[bool] = typer.Option(
        None,
        "--use-understanding-layer/--no-use-understanding-layer",
        help="Use the deterministic understanding layer when applicable.",
        show_default=False,
    ),
    session_id: str = typer.Option(
        "",
        help="Optional session id for multi-turn runs.",
    ),
    use_rl_policy: bool = typer.Option(
        False,
        "--rl-policy/--no-rl-policy",
        help="Use the RL policy loop instead of the deterministic QA pipeline.",
    ),
    policy_path: str = typer.Option(
        "",
        help="Optional path to a serialized RL policy model (pickle).",
    ),
    seed: int = typer.Option(7, help="Random seed for reproducibility."),
) -> None:
    """Run the QA agent with deterministic retrieval enhancements."""
    policy_model = None
    if use_rl_policy and policy_path:
        try:
            import pickle
            with open(policy_path, "rb") as handle:
                policy_model = pickle.load(handle)
        except Exception:
            policy_model = None
    result = run_qa(
        question=question,
        use_llm=use_llm,
        temperature=temperature if use_llm else None,
        use_kg=use_kg,
        enable_query_planner=query_planner,
        enable_bm25=bm25,
        enable_rerank=rerank,
        enable_verifier=verifier,
        use_understanding_layer=use_understanding_layer,
        use_claim_store=use_claim_store,
        persist_claims=persist_claims,
        use_langgraph_qa=use_langgraph_qa,
        session_id=session_id or None,
        chat_mode=chat_mode,
        use_rl_policy=use_rl_policy,
        policy_model=policy_model,
        output_mode=output_mode,
    )
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    app()
