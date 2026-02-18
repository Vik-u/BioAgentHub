#!/usr/bin/env python3
"""Interactive QA chatbot with session memory powered by LangGraph."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, TypedDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fabric.agents.rag_agent import generate_session_id, run_qa  # noqa: E402
from langgraph.graph import END, StateGraph  # noqa: E402


class ChatState(TypedDict, total=False):
    session_id: str
    question: str
    answer: str
    history: List[Dict[str, str]]
    citations: List[Dict[str, Any]]
    metrics: Dict[str, Any]


def build_graph(config: Dict[str, Any]):
    def qa_node(state: ChatState) -> ChatState:
        question = (state.get("question") or "").strip()
        if not question:
            return state

        session_id = state.get("session_id") or generate_session_id()
        result = run_qa(
            question=question,
            use_llm=config["use_llm"],
            temperature=config["temperature"] if config["use_llm"] else None,
            use_kg=config["use_kg"],
            enable_query_planner=config["query_planner"],
            enable_bm25=config["bm25"],
            enable_rerank=config["rerank"],
            enable_verifier=config["verifier"],
            use_understanding_layer=None,
            use_claim_store=config["use_claim_store"],
            persist_claims=config["persist_claims"],
            session_id=session_id,
            chat_mode=True,
            use_rl_policy=False,
            policy_model=None,
        )

        answer = result.get("answer", "")
        history = list(state.get("history", []))
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})

        return {
            **state,
            "session_id": session_id,
            "answer": answer,
            "history": history,
            "citations": result.get("citations", []),
            "metrics": result.get("metrics", {}),
        }

    graph = StateGraph(ChatState)
    graph.add_node("qa", qa_node)
    graph.set_entry_point("qa")
    graph.add_edge("qa", END)
    return graph.compile()


def _print_citations(citations: List[Dict[str, Any]]) -> None:
    if not citations:
        print("sources> (no citations returned)")
        return
    print("sources>")
    for cite in citations:
        paper = cite.get("paper") or cite.get("source") or "unknown"
        cid = cite.get("id")
        label = f"[{cid}] " if cid is not None else ""
        print(f"- {label}{paper}")


def _print_metrics(metrics: Dict[str, Any]) -> None:
    if not metrics:
        print("metrics> (no metrics returned)")
        return
    print("metrics>")
    for key, value in metrics.items():
        print(f"- {key}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="Workspace root (e.g., workspaces/petase).")
    parser.add_argument(
        "--allow-noncanonical",
        action="store_true",
        help="Allow workspace paths outside the canonical workspaces/ directory.",
    )
    parser.add_argument(
        "--alias-expansion",
        action="store_true",
        help="Enable alias expansion (topic-specific).",
    )
    parser.add_argument("--session-id", default="", help="Optional session id to resume.")
    parser.add_argument("--no-llm", dest="use_llm", action="store_false", help="Disable LLM summarizer.")
    parser.set_defaults(use_llm=True)
    parser.add_argument("--temperature", type=float, default=0.0, help="LLM temperature.")
    parser.add_argument("--no-kg", dest="use_kg", action="store_false", help="Disable KG expansion.")
    parser.set_defaults(use_kg=True)
    parser.add_argument("--no-query-planner", dest="query_planner", action="store_false")
    parser.set_defaults(query_planner=True)
    parser.add_argument("--no-bm25", dest="bm25", action="store_false")
    parser.set_defaults(bm25=True)
    parser.add_argument("--no-rerank", dest="rerank", action="store_false")
    parser.set_defaults(rerank=True)
    parser.add_argument("--no-verifier", dest="verifier", action="store_false")
    parser.set_defaults(verifier=True)
    parser.add_argument("--use-claim-store", action="store_true", help="Enable claims-lite composer.")
    parser.add_argument("--persist-claims", action="store_true", help="Persist extracted claims to claim_store.")
    parser.add_argument("--show-citations", action="store_true", help="Print citation list after each answer.")
    parser.add_argument("--show-metrics", action="store_true", help="Print QA metrics after each answer.")
    args = parser.parse_args()

    if args.allow_noncanonical:
        os.environ["ALLOW_NONCANONICAL_WORKSPACE"] = "1"
    if args.workspace:
        os.environ["WORKSPACE_ROOT"] = str(args.workspace.resolve())
    if args.alias_expansion:
        os.environ["USE_ALIAS_EXPANSION"] = "1"

    config = {
        "use_llm": bool(args.use_llm),
        "temperature": float(args.temperature),
        "use_kg": bool(args.use_kg),
        "query_planner": bool(args.query_planner),
        "bm25": bool(args.bm25),
        "rerank": bool(args.rerank),
        "verifier": bool(args.verifier),
        "use_claim_store": bool(args.use_claim_store),
        "persist_claims": bool(args.persist_claims),
    }

    graph = build_graph(config)
    state: ChatState = {
        "session_id": args.session_id.strip() if args.session_id else "",
        "history": [],
    }

    banner = (
        "BioAgentHub QA chat (LangGraph). Commands: /help, /reset, /session, /exit"
    )
    print(banner)
    if state["session_id"]:
        print(f"session> {state['session_id']}")

    while True:
        try:
            user_input = input("you> ").strip()
        except EOFError:
            print()
            break
        if not user_input:
            continue
        lowered = user_input.lower()
        if lowered in {"/exit", "exit", "/quit", "quit"}:
            break
        if lowered in {"/help", "help"}:
            print("commands> /help /reset /session /exit")
            continue
        if lowered in {"/session", "session"}:
            session_id = state.get("session_id") or "(new on next turn)"
            print(f"session> {session_id}")
            continue
        if lowered in {"/reset", "reset"}:
            state = {"session_id": generate_session_id(), "history": []}
            print(f"session> reset to {state['session_id']}")
            continue

        state["question"] = user_input
        state = graph.invoke(state)

        answer = state.get("answer", "")
        print(f"\nassistant> {answer}\n")
        if args.show_citations:
            _print_citations(state.get("citations", []))
        if args.show_metrics:
            _print_metrics(state.get("metrics", {}))


if __name__ == "__main__":
    main()
