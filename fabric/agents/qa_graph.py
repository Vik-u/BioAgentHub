#!/usr/bin/env python3
"""LangGraph orchestration for QA (planner -> retrieval -> claims-lite -> compose -> verify)."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from fabric.agents.rag_agent import (
    AgentState,
    BlockUnion,
    Claim,
    BlockSpec,
    QuestionPlan,
    QA_OUTPUT_ROOT,
    append_claims_to_store,
    build_evidence_audit,
    build_evidence_from_state,
    collect_candidate_evidence,
    collect_kg_edge_evidence,
    collect_methodology_evidence,
    citation_concentration,
    claims_are_sufficient,
    compose_blocks,
    contradiction_proxy,
    coverage_proxy,
    evaluate_abstention,
    extract_claims_from_evidence,
    get_workspace_root,
    generate_existing_protocol_plan,
    load_schema,
    plan_question,
    render_blocks_text,
    render_dual_answer,
    render_helpful_answer,
    rrf_fuse,
    rerank_candidates,
    select_graph_seeds,
    topic_label,
    update_session_state,
    load_claim_index,
    persist_claim_index,
    select_claim_ids_for_blocks,
    update_claim_index,
    validate_blocks,
    build_sentence_map,
    unsupported_sentence_rate_from_map,
    _assemble_candidates,
    _collect_dense_hits,
    _collect_keyword_hits,
)
from services.retrieval_service import get_backend


class EvidenceItem(BaseModel):
    evidence_id: str
    text: str
    title: Optional[str] = None
    paper: Optional[str] = None
    source_id: Optional[str] = None
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidencePack(BaseModel):
    items: List[EvidenceItem] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_to_citation: Dict[str, int] = Field(default_factory=dict)
    retrieval: Dict[str, Any] = Field(default_factory=dict)


class ValidationReport(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    abstain: bool = False
    abstain_reason: Optional[str] = None
    selected_evidence_ids: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class QAState(BaseModel):
    query: str
    topic: str
    session_state: Dict[str, Any]
    config: Dict[str, Any]
    plan: Optional[QuestionPlan] = None
    evidence_pack: Optional[EvidencePack] = None
    claims: Optional[List[Claim]] = None
    blocks: Optional[List[BlockUnion]] = None
    validation: Optional[ValidationReport] = None
    protocol_plan: Optional[Dict[str, Any]] = None
    retries_used: int = 0
    abstain: bool = False
    abstain_reason: Optional[str] = None
    fallback_used: bool = False
    timing: Dict[str, float] = Field(default_factory=dict)
    debug_log_paths: Dict[str, str] = Field(default_factory=dict)
    trace: List[str] = Field(default_factory=list)
    runtime: Dict[str, Any] = Field(default_factory=dict)


def _get_hook(state: QAState, name: str):
    hooks = state.config.get("hooks") or {}
    return hooks.get(name)


def _mark_trace(state: QAState, node: str) -> None:
    state.trace.append(node)


def _now() -> float:
    return time.monotonic()


def _used_evidence_ids(blocks: List[BlockUnion]) -> List[str]:
    used: List[str] = []
    for block in blocks:
        if hasattr(block, "items") and isinstance(getattr(block, "items"), list):
            for item in getattr(block, "items"):
                for eid in getattr(item, "supporting_evidence", []) or []:
                    used.append(eid)
                for eid in getattr(item, "citations", []) or []:
                    used.append(eid)
        if hasattr(block, "bullets") and isinstance(getattr(block, "bullets"), list):
            for bullet in getattr(block, "bullets"):
                for eid in getattr(bullet, "citations", []) or []:
                    used.append(eid)
    return list(dict.fromkeys([eid for eid in used if eid]))


def _write_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))
    return str(path)


def _write_jsonl(path: Path, records: List[Dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    return str(path)


def _graph_log_dir(topic: str, run_id: Optional[str] = None) -> Path:
    workspace_root = get_workspace_root()
    base = workspace_root / "qa_runs" / topic
    run_id = run_id or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return base / run_id


def _write_session_state(topic: str, session_id: str, session_state: Dict[str, Any]) -> None:
    session_dir = QA_OUTPUT_ROOT / topic / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "session_state.json").write_text(json.dumps(session_state, indent=2, ensure_ascii=True))


def node_plan_question(state: QAState) -> QAState:
    _mark_trace(state, "plan_question")
    start = _now()
    hook = _get_hook(state, "plan")
    if hook:
        plan, valid, raw, error = hook(state)
    else:
        schema = state.config["schema"]
        use_llm = bool(state.config.get("use_llm", True))
        plan, valid, raw, error = plan_question(state.query, schema, state.session_state, use_llm)
    state.plan = plan
    state.runtime["planner_valid"] = bool(valid)
    state.runtime["planner_raw"] = raw
    state.runtime["planner_error"] = error
    if not valid:
        state.abstain = True
        state.abstain_reason = "planner_invalid"
    state.timing["plan_question"] = _now() - start
    return state


def node_retrieve_evidence(state: QAState) -> QAState:
    _mark_trace(state, "retrieve_evidence")
    start = _now()
    hook = _get_hook(state, "retrieve")
    if hook:
        evidence_pack = hook(state)
        state.evidence_pack = evidence_pack
        state.timing["retrieve_evidence"] = _now() - start
        return state

    plan = state.plan
    if plan is None:
        state.evidence_pack = EvidencePack()
        state.timing["retrieve_evidence"] = _now() - start
        return state

    backend = state.config["backend"]
    schema = state.config["schema"]
    query_list = plan.retrieval_queries or [state.query]
    query_for_rerank = query_list[0]
    enable_bm25 = bool(state.config.get("enable_bm25", True))
    enable_rerank = bool(state.config.get("enable_rerank", True))
    use_kg = bool(state.config.get("use_kg", True))

    dense_hits: Dict[str, List[Dict[str, Any]]] = {}
    bm25_hits: Dict[str, List[Dict[str, Any]]] = {}
    rrf_inputs = []
    for q in query_list:
        dense = _collect_dense_hits(backend, q, state.config.get("top_k", 5))
        dense_hits[q] = dense
        for item in dense:
            item["source"] = "dense"
        rrf_inputs.append(dense)
        if enable_bm25:
            bm25 = _collect_keyword_hits(backend, q, state.config.get("top_k", 5))
            bm25_hits[q] = bm25
            for item in bm25:
                item["source"] = "bm25"
            rrf_inputs.append(bm25)

    fused = rrf_fuse(rrf_inputs, k=state.config.get("rrf_k", 60))
    candidates = _assemble_candidates(fused)
    if enable_rerank:
        selected, rerank_all = rerank_candidates(
            candidates,
            query_for_rerank,
            top_k=state.config.get("rerank_top_k", 20),
            exclude_patterns=plan.exclude_patterns,
        )
    else:
        rerank_all = sorted(candidates, key=lambda item: item.get("rrf_score", 0.0), reverse=True)
        selected = rerank_all[:state.config.get("rerank_top_k", 20)]

    context = [
        {
            "text": item.get("text", ""),
            "metadata": item.get("metadata", {}),
            "score": item.get("rerank_score", item.get("rrf_score", 0.0)),
        }
        for item in selected
    ]

    graph_nodes: List[Dict[str, Any]] = []
    if use_kg and backend.graph is not None:
        context_sources = [
            ctx.get("metadata", {}).get("source")
            for ctx in context
            if ctx.get("metadata", {}).get("source")
        ]
        graph_overview_path = get_workspace_root() / "graph_overview.json"
        seeds = select_graph_seeds(context_sources, query_for_rerank, schema, graph_overview_path, max_seeds=6)
        if seeds:
            graph_nodes = backend.graph_neighbors_diverse(seeds, top_k=10)

    steps = 1 + (1 if (use_kg and backend.graph is not None) else 0)
    state.runtime["steps"] = steps

    agent_state = AgentState(question=state.query, context=context, graph_nodes=graph_nodes, steps=steps)
    method_evidence = []
    if plan.required_signals:
        method_evidence = collect_methodology_evidence(
            state.query,
            limit=int(state.config.get("method_evidence_k", 6)),
            required_signals=plan.required_signals,
        )
    kg_edge_evidence = collect_kg_edge_evidence(
        get_workspace_root(),
        state.query,
        plan,
        schema,
        limit=int(state.config.get("kg_edge_evidence_k", 20)),
    )
    candidate_evidence = []
    if plan.intent in {"candidate_selection", "comparison"}:
        candidate_evidence = collect_candidate_evidence(
            get_workspace_root(),
            state.query,
            plan,
            schema,
            limit=int(state.config.get("kg_candidate_evidence_k", 8)),
        )
    extra_evidence = []
    if candidate_evidence:
        extra_evidence.extend(candidate_evidence)
    if method_evidence:
        extra_evidence.extend(method_evidence)
    if kg_edge_evidence:
        extra_evidence.extend(kg_edge_evidence)
    evidence_items, citations, evidence_to_citation = build_evidence_from_state(
        agent_state,
        max_items=int(state.config.get("evidence_max_items", 12)),
        extra_evidence=extra_evidence,
        required_signals=plan.required_signals,
        exclude_patterns=plan.exclude_patterns,
    )

    pack_items = [
        EvidenceItem(
            evidence_id=item.get("evidence_id"),
            text=item.get("text", ""),
            title=item.get("title"),
            paper=item.get("paper"),
            source_id=item.get("source_id"),
            score=item.get("score"),
            metadata={},
        )
        for item in evidence_items
        if item.get("evidence_id")
    ]
    evidence_pack = EvidencePack(
        items=pack_items,
        citations=citations,
        evidence_to_citation=evidence_to_citation,
        retrieval={
            "dense": dense_hits,
            "bm25": bm25_hits,
            "selected_ids": [item.get("id") for item in selected],
        },
    )
    state.evidence_pack = evidence_pack
    state.timing["retrieve_evidence"] = _now() - start
    return state


def node_protocol_generate(state: QAState) -> QAState:
    _mark_trace(state, "protocol_generate")
    start = _now()
    protocol_plan, protocol_text = generate_existing_protocol_plan(state.query)
    state.protocol_plan = protocol_plan
    state.runtime["protocol_text"] = protocol_text
    state.timing["protocol_generate"] = _now() - start
    return state


def node_protocol_render(state: QAState) -> QAState:
    _mark_trace(state, "protocol_render")
    protocol_text = state.runtime.get("protocol_text")
    if protocol_text:
        state.runtime["answer"] = protocol_text
    return state


def node_maybe_extract_claims(state: QAState) -> QAState:
    _mark_trace(state, "maybe_extract_claims")
    start = _now()
    hook = _get_hook(state, "claims")
    if hook:
        claims, stats = hook(state)
        state.runtime["claim_stats"] = stats or {}
        if state.config.get("use_claims_lite") and not claims_are_sufficient(claims):
            state.claims = None
            state.fallback_used = True
            state.runtime["claim_stats"]["fallback_reason"] = "claims_too_few"
        else:
            state.claims = claims
        state.timing["maybe_extract_claims"] = _now() - start
        return state

    if not state.config.get("use_claims_lite"):
        state.claims = None
        state.timing["maybe_extract_claims"] = _now() - start
        return state

    if not state.evidence_pack:
        state.claims = None
        state.fallback_used = True
        state.runtime["claim_stats"] = {"error": "no_evidence_pack"}
        state.timing["maybe_extract_claims"] = _now() - start
        return state

    evidence_items = [item.model_dump() for item in state.evidence_pack.items]
    claims, stats = extract_claims_from_evidence(
        evidence_items,
        state.plan,
        state.config["schema"],
        use_llm=bool(state.config.get("use_llm", True)),
    )
    state.runtime["claim_stats"] = stats or {}
    if not claims_are_sufficient(claims):
        state.claims = None
        state.fallback_used = True
        state.runtime["claim_stats"]["fallback_reason"] = "claims_too_few"
    else:
        state.claims = claims
        if state.config.get("persist_claims"):
            append_claims_to_store(get_workspace_root(), claims)
            index = load_claim_index(get_workspace_root())
            index = update_claim_index(index, claims)
            persist_claim_index(get_workspace_root(), index)
    state.timing["maybe_extract_claims"] = _now() - start
    return state


def node_compose_blocks(state: QAState) -> QAState:
    _mark_trace(state, "compose_blocks")
    start = _now()
    hook = _get_hook(state, "compose")
    if hook:
        state.blocks = hook(state)
        state.timing["compose_blocks"] = _now() - start
        return state

    if not state.evidence_pack or not state.plan:
        fallback_plan = QuestionPlan(
            intent="other",
            required_blocks=[BlockSpec(type="evidence_audit")],
            allowed_rank_entity_types=[],
            required_signals=[],
            retrieval_queries=[state.query],
            exclude_patterns=[],
            abstain_conditions=[],
        )
        state.blocks = [build_evidence_audit([], state.plan or fallback_plan)]
        state.timing["compose_blocks"] = _now() - start
        return state

    evidence_items = [item.model_dump() for item in state.evidence_pack.items]
    blocks, citations, validation, evidence_to_citation, _ = compose_blocks(
        AgentState(question=state.query, context=[], graph_nodes=[], steps=0),
        state.query,
        state.plan,
        state.config["schema"],
        use_llm=bool(state.config.get("use_llm", True)),
        temperature=state.config.get("temperature"),
        evidence_items=evidence_items,
        citations=state.evidence_pack.citations,
        evidence_to_citation=state.evidence_pack.evidence_to_citation,
        claims=state.claims,
        use_claims=bool(state.claims),
        strict=bool(state.config.get("strict_compose")),
    )
    state.blocks = blocks
    state.evidence_pack.citations = citations
    state.evidence_pack.evidence_to_citation = evidence_to_citation
    state.runtime["composer_validation"] = validation
    state.timing["compose_blocks"] = _now() - start
    return state


def node_verify_blocks(state: QAState) -> QAState:
    _mark_trace(state, "verify_blocks")
    start = _now()
    blocks = state.blocks or []
    plan = state.plan
    evidence_ids = set(state.evidence_pack.evidence_to_citation.keys()) if state.evidence_pack else set()
    valid, errors = validate_blocks(blocks, plan, evidence_ids) if plan else (False, ["missing_plan"])
    abstain, abstain_reason = evaluate_abstention(plan, blocks, evidence_ids, state.abstain_reason) if plan else (True, "missing_plan")
    used_evidence = _used_evidence_ids(blocks)
    report = ValidationReport(
        valid=valid,
        errors=errors,
        abstain=abstain,
        abstain_reason=abstain_reason,
        selected_evidence_ids=used_evidence,
        details={},
    )
    state.validation = report
    state.abstain = abstain
    state.abstain_reason = abstain_reason
    state.timing["verify_blocks"] = _now() - start
    return state


def node_one_retry_recompose(state: QAState) -> QAState:
    _mark_trace(state, "one_retry_recompose")
    state.retries_used += 1
    state.config["strict_compose"] = True
    hook = _get_hook(state, "compose_retry")
    if hook:
        state.blocks = hook(state)
        return state
    return node_compose_blocks(state)


def node_abstain_to_evidence_audit(state: QAState) -> QAState:
    _mark_trace(state, "abstain_to_evidence_audit")
    evidence_items = [item.model_dump() for item in state.evidence_pack.items] if state.evidence_pack else []
    plan = state.plan or QuestionPlan.model_validate(
        {
            "intent": "other",
            "required_blocks": [{"type": "evidence_audit"}],
            "allowed_rank_entity_types": [],
            "required_signals": [],
            "retrieval_queries": [state.query],
            "exclude_patterns": [],
            "abstain_conditions": [],
        }
    )
    audit = build_evidence_audit(evidence_items, plan, reason=state.abstain_reason or "abstain")
    state.blocks = [audit]
    state.abstain = True
    return state


def node_finalize(state: QAState) -> QAState:
    _mark_trace(state, "finalize")
    if not state.blocks and state.config.get("output_mode") != "protocol":
        state.blocks = [build_evidence_audit([], state.plan, reason="no_blocks")]
    if not state.evidence_pack:
        state.evidence_pack = EvidencePack()
    if state.config.get("output_mode") == "protocol" and state.runtime.get("answer"):
        structured_answer = state.runtime.get("answer", "")
    else:
        structured_answer = render_blocks_text(
            state.blocks,
            state.evidence_pack.evidence_to_citation,
            state.evidence_pack.citations,
        )
    helpful_answer = None
    answer_for_verifier = structured_answer
    verifier = {
        "unsupported_sentence_rate": 0.0 if state.validation and state.validation.valid and not state.abstain else 1.0,
        "citation_concentration": citation_concentration(answer_for_verifier),
        "contradiction_proxy": contradiction_proxy(answer_for_verifier),
    }
    grounding_stats = {}
    if state.config.get("output_mode") in ("answer_helpful", "answer_dual"):
        evidence_items = [item.model_dump() for item in state.evidence_pack.items]
        helpful_answer, grounding_stats = render_helpful_answer(
            state.query,
            state.plan,
            state.session_state,
            evidence_items,
            state.claims,
            use_llm=bool(state.config.get("use_llm", True)),
            temperature=state.config.get("temperature"),
            session_id=state.config.get("session_id"),
            evidence_to_citation=state.evidence_pack.evidence_to_citation if state.evidence_pack else None,
            citations=state.evidence_pack.citations if state.evidence_pack else None,
            include_sources=(state.config.get("output_mode") == "answer_helpful"),
        )
        answer_for_verifier = helpful_answer
    if state.config.get("output_mode") == "answer_helpful":
        answer = helpful_answer or structured_answer
    elif state.config.get("output_mode") == "answer_dual":
        answer = render_dual_answer(helpful_answer or structured_answer, structured_answer)
    else:
        answer = structured_answer
    sentence_map = build_sentence_map(answer_for_verifier, state.evidence_pack.citations)
    verifier["unsupported_sentence_rate"] = unsupported_sentence_rate_from_map(sentence_map)
    steps = int(state.runtime.get("steps", 1))
    metrics = {
        "steps": steps,
        "unique_citations": len({c.get("id") for c in state.evidence_pack.citations if c.get("id")}),
        "coverage_proxy": coverage_proxy(answer_for_verifier),
        "unsupported_sentence_rate": verifier.get("unsupported_sentence_rate", 1.0),
    }
    session_id = state.config.get("session_id") or "session"
    state.session_state = update_session_state(
        state.session_state,
        state.query,
        answer,
        state.evidence_pack.citations,
        intent=state.plan.intent if state.plan else None,
    )
    _write_session_state(state.topic, session_id, state.session_state)
    if state.claims and state.runtime.get("claim_stats") is not None:
        state.runtime["claim_stats"]["selected_claim_ids"] = select_claim_ids_for_blocks(state.claims, state.blocks)
    state.runtime["answer"] = answer
    state.runtime["answer_helpful"] = helpful_answer
    state.runtime["answer_structured"] = structured_answer
    state.runtime["metrics"] = metrics
    state.runtime["verifier"] = verifier
    if grounding_stats:
        state.runtime["grounding_stats"] = grounding_stats
    return state


def _write_graph_logs(state: QAState) -> Dict[str, str]:
    run_dir = _graph_log_dir(state.topic)
    paths = {}
    if state.plan:
        paths["plan"] = _write_json(run_dir / "plan.json", state.plan.model_dump())
    if state.evidence_pack:
        pack_payload = {
            "items": [item.model_dump() for item in state.evidence_pack.items],
            "retrieval": state.evidence_pack.retrieval,
        }
        paths["evidence_pack"] = _write_json(run_dir / "evidence_pack.json", pack_payload)
    if state.claims:
        paths["claims"] = _write_jsonl(run_dir / "claims.jsonl", [claim.model_dump() for claim in state.claims])
    if state.blocks:
        paths["blocks"] = _write_json(run_dir / "blocks.json", [block.model_dump() for block in state.blocks])
    if state.validation:
        paths["validation"] = _write_json(run_dir / "validation.json", state.validation.model_dump())
    if state.runtime.get("grounding_stats"):
        paths["grounding_stats"] = _write_json(run_dir / "grounding_stats.json", state.runtime.get("grounding_stats"))
    decision_trace = {
        "trace": state.trace,
        "retries_used": state.retries_used,
        "abstain": state.abstain,
        "abstain_reason": state.abstain_reason,
        "fallback_used": state.fallback_used,
        "claim_stats": state.runtime.get("claim_stats", {}),
    }
    paths["decision_trace"] = _write_json(run_dir / "decision_trace.json", decision_trace)
    paths["timings"] = _write_json(run_dir / "timings.json", state.timing)
    return paths


def build_graph() -> Any:
    graph = StateGraph(QAState)
    graph.add_node("plan_question", node_plan_question)
    graph.add_node("retrieve_evidence", node_retrieve_evidence)
    graph.add_node("protocol_generate", node_protocol_generate)
    graph.add_node("protocol_render", node_protocol_render)
    graph.add_node("maybe_extract_claims", node_maybe_extract_claims)
    graph.add_node("compose_blocks", node_compose_blocks)
    graph.add_node("verify_blocks", node_verify_blocks)
    graph.add_node("one_retry_recompose", node_one_retry_recompose)
    graph.add_node("abstain_to_evidence_audit", node_abstain_to_evidence_audit)
    graph.add_node("finalize", node_finalize)

    graph.set_entry_point("plan_question")

    def route_after_plan(state: QAState) -> str:
        if state.abstain and state.abstain_reason == "planner_invalid":
            if state.config.get("output_mode") == "protocol":
                return "protocol_generate"
            if state.config.get("output_mode") == "answer_helpful":
                state.abstain = False
                state.abstain_reason = None
                return "retrieve_evidence"
            return "abstain_to_evidence_audit"
        if state.config.get("output_mode") == "protocol":
            return "protocol_generate"
        return "retrieve_evidence"

    graph.add_conditional_edges("plan_question", route_after_plan)
    graph.add_edge("retrieve_evidence", "maybe_extract_claims")
    graph.add_edge("protocol_generate", "protocol_render")
    graph.add_edge("protocol_render", "finalize")
    graph.add_edge("maybe_extract_claims", "compose_blocks")
    graph.add_edge("compose_blocks", "verify_blocks")

    def route_after_verify(state: QAState) -> str:
        if state.config.get("output_mode") == "answer_helpful":
            if state.validation and not state.validation.valid and state.retries_used == 0:
                return "one_retry_recompose"
            return "finalize"
        if state.validation and not state.validation.valid:
            return "one_retry_recompose" if state.retries_used == 0 else "abstain_to_evidence_audit"
        if state.abstain:
            return "abstain_to_evidence_audit"
        return "finalize"

    graph.add_conditional_edges("verify_blocks", route_after_verify)
    graph.add_edge("one_retry_recompose", "verify_blocks")
    graph.add_edge("abstain_to_evidence_audit", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


def run_qa_graph(
    query: str,
    session_state: Dict[str, Any],
    config: Dict[str, Any],
    return_state: bool = False,
) -> Dict[str, Any] | Tuple[Dict[str, Any], QAState]:
    workspace_root = get_workspace_root()
    hooks = config.get("hooks") or {}
    schema = config.get("schema")
    backend = config.get("backend")
    if schema is None and not hooks.get("plan"):
        schema = load_schema(workspace_root)
    topic = config.get("topic") or (topic_label(schema, workspace_root) if schema else "unknown")
    if backend is None and not hooks.get("retrieve") and config.get("output_mode", "answer_strict") != "protocol":
        backend = get_backend(workspace_root)
    config = {
        **config,
        "schema": schema,
        "backend": backend,
        "topic": topic,
        "output_mode": config.get("output_mode", "answer_strict"),
    }
    state = QAState(
        query=query,
        topic=topic,
        session_state=session_state,
        config=config,
    )
    graph = build_graph()
    state = graph.invoke(state)
    if isinstance(state, dict):
        state = QAState.model_validate(state)
    paths = _write_graph_logs(state)
    state.debug_log_paths = paths
    result = {
        "answer": state.runtime.get("answer", ""),
        "citations": state.evidence_pack.citations if state.evidence_pack else [],
        "metrics": state.runtime.get("metrics", {}),
        "trajectory": [{"action": "vector_search"}, {"action": "graph_expand"}] if state.runtime.get("steps", 1) == 2 else [{"action": "vector_search"}],
        "use_llm": bool(config.get("use_llm", True)),
        "blocks": [block.model_dump() for block in state.blocks] if state.blocks else [],
        "claims": state.runtime.get("claim_stats", {}),
        "debug_log_paths": state.debug_log_paths,
    }
    if state.protocol_plan:
        result["protocol"] = state.protocol_plan
    if return_state:
        return result, state
    return result


def run_linear_qa(
    query: str,
    session_state: Dict[str, Any],
    config: Dict[str, Any],
    return_state: bool = False,
) -> Dict[str, Any] | Tuple[Dict[str, Any], QAState]:
    if config.get("output_mode") == "protocol":
        protocol_plan, protocol_text = generate_existing_protocol_plan(query)
        result = {
            "answer": protocol_text,
            "citations": [],
            "metrics": {},
            "trajectory": [{"action": "protocol"}],
            "use_llm": bool(config.get("use_llm", True)),
            "blocks": [],
            "claims": {},
            "protocol": protocol_plan,
        }
        return (result, QAState(query=query, topic="unknown", session_state=session_state, config=config)) if return_state else result
    workspace_root = get_workspace_root()
    hooks = config.get("hooks") or {}
    schema = config.get("schema")
    backend = config.get("backend")
    if schema is None and not hooks.get("plan"):
        schema = load_schema(workspace_root)
    topic = config.get("topic") or (topic_label(schema, workspace_root) if schema else "unknown")
    if backend is None and not hooks.get("retrieve") and config.get("output_mode", "answer_strict") != "protocol":
        backend = get_backend(workspace_root)
    config = {
        **config,
        "schema": schema,
        "backend": backend,
        "topic": topic,
        "output_mode": config.get("output_mode", "answer_strict"),
    }
    state = QAState(
        query=query,
        topic=topic,
        session_state=session_state,
        config=config,
    )
    state = node_plan_question(state)
    if state.abstain and state.abstain_reason == "planner_invalid":
        state = node_abstain_to_evidence_audit(state)
        state = node_finalize(state)
    else:
        state = node_retrieve_evidence(state)
        state = node_maybe_extract_claims(state)
        state = node_compose_blocks(state)
        state = node_verify_blocks(state)
        if not state.validation.valid or state.abstain:
            state = node_abstain_to_evidence_audit(state)
        state = node_finalize(state)
    result = {
        "answer": state.runtime.get("answer", ""),
        "citations": state.evidence_pack.citations if state.evidence_pack else [],
        "metrics": state.runtime.get("metrics", {}),
        "trajectory": [{"action": "vector_search"}, {"action": "graph_expand"}] if state.runtime.get("steps", 1) == 2 else [{"action": "vector_search"}],
        "use_llm": bool(config.get("use_llm", True)),
        "blocks": [block.model_dump() for block in state.blocks] if state.blocks else [],
        "claims": state.runtime.get("claim_stats", {}),
    }
    if return_state:
        return result, state
    return result
