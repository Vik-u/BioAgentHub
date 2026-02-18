#!/usr/bin/env python3
"""Unified CLI for QA, protocol, biofoundry orchestration, and multi-agent runs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from typing import List, Optional

from fabric.agents.rag_agent import generate_session_id, run_qa  # noqa: E402


def _patch_urllib3_default_ciphers() -> None:
    """Avoid botocore import errors when urllib3 lacks DEFAULT_CIPHERS."""
    try:
        import urllib3.util.ssl_ as ssl_
        if not hasattr(ssl_, "DEFAULT_CIPHERS"):
            ssl_.DEFAULT_CIPHERS = (
                "TLS_AES_256_GCM_SHA384:"
                "TLS_CHACHA20_POLY1305_SHA256:"
                "TLS_AES_128_GCM_SHA256:"
                "HIGH:!DH:!aNULL"
            )
    except Exception:
        return


def _apply_env(workspace: Optional[str], allow_noncanonical: bool, alias_expansion: bool) -> None:
    if allow_noncanonical:
        os.environ["ALLOW_NONCANONICAL_WORKSPACE"] = "1"
    else:
        os.environ["ALLOW_NONCANONICAL_WORKSPACE"] = "0"
    if workspace:
        os.environ["WORKSPACE_ROOT"] = str(Path(workspace).expanduser().resolve())
    os.environ["USE_ALIAS_EXPANSION"] = "1" if alias_expansion else "0"


def cmd_qa(args: argparse.Namespace) -> None:
    _apply_env(args.workspace, args.allow_noncanonical, args.alias_expansion)
    result = run_qa(
        question=args.question,
        use_llm=not args.no_llm,
        temperature=args.temperature if not args.no_llm else None,
        use_kg=not args.no_kg,
        enable_query_planner=not args.no_query_planner,
        enable_bm25=not args.no_bm25,
        enable_rerank=not args.no_rerank,
        enable_verifier=not args.no_verifier,
        use_understanding_layer=None,
        use_claim_store=args.use_claim_store,
        persist_claims=args.persist_claims,
        use_langgraph_qa=args.use_langgraph_qa,
        session_id=args.session_id or None,
        chat_mode=args.chat_mode,
        use_rl_policy=args.use_rl_policy,
        policy_model=None,
        output_mode=args.output_mode,
        seed=args.seed,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_qa_chat(args: argparse.Namespace) -> None:
    _apply_env(args.workspace, args.allow_noncanonical, args.alias_expansion)
    session_id = args.session_id or generate_session_id()
    print(f"session_id: {session_id}")
    print("Enter /exit to quit.")
    while True:
        try:
            question = input("you> ").strip()
        except EOFError:
            break
        if not question:
            continue
        if question.lower() in {"/exit", "/quit", "exit", "quit", ":q"}:
            break
        result = run_qa(
            question=question,
            use_llm=not args.no_llm,
            temperature=args.temperature if not args.no_llm else None,
            use_kg=not args.no_kg,
            enable_query_planner=not args.no_query_planner,
            enable_bm25=not args.no_bm25,
            enable_rerank=not args.no_rerank,
            enable_verifier=not args.no_verifier,
            use_understanding_layer=None,
            use_claim_store=args.use_claim_store,
            persist_claims=args.persist_claims,
            use_langgraph_qa=args.use_langgraph_qa,
            session_id=session_id,
            chat_mode=True,
            use_rl_policy=False,
            policy_model=None,
            output_mode=args.output_mode,
            seed=args.seed,
        )
        print(result.get("answer", ""))


def cmd_protocol(args: argparse.Namespace) -> None:
    _apply_env(args.workspace, args.allow_noncanonical, args.alias_expansion)
    _patch_urllib3_default_ciphers()
    from fabric.agents.protocol_agent_v2 import run_protocol_agent_v2  # noqa: E402
    answer = run_protocol_agent_v2(args.question)
    print("\n" + answer + "\n")


def cmd_biofoundry(args: argparse.Namespace) -> None:
    os.environ["BIOAGENT_USE_INSTRUMENTS"] = "1" if args.include_instruments else "0"
    topics: List[str] | None = None
    if args.topics:
        topics = [t.strip() for t in args.topics.split(",") if t.strip()]
    _patch_urllib3_default_ciphers()
    from fabric.agents.biofoundry_protocol_orchestrator import run_biofoundry  # noqa: E402
    result = run_biofoundry(
        topics=topics,
        use_kg=not args.no_kg,
        include_instruments=args.include_instruments,
        kg_top_k=args.kg_top_k,
        assay_enabled=not args.no_assay_evidence,
        llm_rationale=args.llm_rationale,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_multi_agent(args: argparse.Namespace) -> None:
    _apply_env(str(args.workspace), args.allow_noncanonical, args.alias_expansion)
    _patch_urllib3_default_ciphers()
    from fabric.agents.multi_agent_orchestrator import run_multi_agent  # noqa: E402
    result = run_multi_agent(args.query, args.workspace, args.alias_expansion)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_kg_build(args: argparse.Namespace) -> None:
    pdf_dir = Path(args.pdf_dir) if args.pdf_dir else Path(__file__).resolve().parents[1] / "data" / args.topic
    workspace = Path(args.workspace) if args.workspace else Path(__file__).resolve().parents[1] / "workspaces" / args.topic
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "forge" / "scripts" / "build_topic_full.py"),
        "--topic",
        args.topic,
        "--pdf-dir",
        str(pdf_dir),
        "--workspace",
        str(workspace),
        "--model",
        args.model,
        "--embedding-backend",
        args.embedding_backend,
        "--kg-model",
        args.kg_model,
        "--kg-embedding-backend",
        args.kg_embedding_backend,
        "--focus-query",
        args.focus_query,
    ]
    if args.auto_schema:
        cmd.append("--auto-schema")
    if args.skip_kg:
        cmd.append("--skip-kg")
    if args.with_artifacts:
        cmd.append("--with-artifacts")
    if args.with_facts:
        cmd.append("--with-facts")
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    qa = sub.add_parser("qa", help="Run the QA agent.")
    qa.add_argument("question")
    qa.add_argument("--workspace")
    qa.add_argument("--allow-noncanonical", action="store_true")
    qa.add_argument("--alias-expansion", action="store_true")
    qa.add_argument("--no-llm", action="store_true")
    qa.add_argument("--temperature", type=float, default=0.0)
    qa.add_argument("--no-kg", action="store_true")
    qa.add_argument("--no-query-planner", action="store_true")
    qa.add_argument("--no-bm25", action="store_true")
    qa.add_argument("--no-rerank", action="store_true")
    qa.add_argument("--no-verifier", action="store_true")
    qa.add_argument("--use-claim-store", action="store_true")
    qa.add_argument("--persist-claims", action="store_true")
    qa.add_argument("--use-langgraph-qa", action="store_true")
    qa.add_argument("--output-mode", default="answer_dual", help="answer_strict, answer_helpful, answer_dual, or protocol")
    qa.add_argument("--chat-mode", action="store_true")
    qa.add_argument("--session-id", default="")
    qa.add_argument("--use-rl-policy", action="store_true")
    qa.add_argument("--seed", type=int, default=7)
    qa.set_defaults(func=cmd_qa)

    qa_chat = sub.add_parser("qa-chat", help="Interactive QA chat session.")
    qa_chat.add_argument("--workspace")
    qa_chat.add_argument("--allow-noncanonical", action="store_true")
    qa_chat.add_argument("--alias-expansion", action="store_true")
    qa_chat.add_argument("--no-llm", action="store_true")
    qa_chat.add_argument("--temperature", type=float, default=0.0)
    qa_chat.add_argument("--no-kg", action="store_true")
    qa_chat.add_argument("--no-query-planner", action="store_true")
    qa_chat.add_argument("--no-bm25", action="store_true")
    qa_chat.add_argument("--no-rerank", action="store_true")
    qa_chat.add_argument("--no-verifier", action="store_true")
    qa_chat.add_argument("--use-claim-store", action="store_true")
    qa_chat.add_argument("--persist-claims", action="store_true")
    qa_chat.add_argument("--use-langgraph-qa", action="store_true")
    qa_chat.add_argument("--output-mode", default="answer_dual", help="answer_strict, answer_helpful, answer_dual, or protocol")
    qa_chat.add_argument("--session-id", default="")
    qa_chat.add_argument("--seed", type=int, default=7)
    qa_chat.set_defaults(func=cmd_qa_chat)

    proto = sub.add_parser("protocol", help="Run protocol agent v2.")
    proto.add_argument("question")
    proto.add_argument("--workspace")
    proto.add_argument("--allow-noncanonical", action="store_true")
    proto.add_argument("--alias-expansion", action="store_true")
    proto.set_defaults(func=cmd_protocol)

    bf = sub.add_parser("biofoundry", help="Run biofoundry template orchestration.")
    bf.add_argument("--topics", help="Comma-separated topics; if omitted, auto-discover.")
    bf.add_argument("--no-kg", action="store_true")
    bf.add_argument("--include-instruments", action="store_true")
    bf.add_argument("--kg-top-k", type=int, default=5)
    bf.add_argument("--no-assay-evidence", action="store_true")
    bf.add_argument("--llm-rationale", action="store_true")
    bf.set_defaults(func=cmd_biofoundry)

    ma = sub.add_parser("multi-agent", help="Run multi-agent orchestrator.")
    ma.add_argument("--workspace", type=Path, required=True)
    ma.add_argument("--query", required=True)
    ma.add_argument("--alias-expansion", action="store_true")
    ma.add_argument("--allow-noncanonical", action="store_true")
    ma.set_defaults(func=cmd_multi_agent)

    kg = sub.add_parser("kg-build", help="Build a topic KG from PDFs.")
    kg.add_argument("--topic", required=True)
    kg.add_argument("--pdf-dir")
    kg.add_argument("--workspace")
    kg.add_argument("--auto-schema", dest="auto_schema", action="store_true", help="Enable KG schema induction.")
    kg.add_argument("--no-auto-schema", dest="auto_schema", action="store_false", help="Disable KG schema induction.")
    kg.set_defaults(auto_schema=True)
    kg.add_argument("--skip-kg", action="store_true")
    kg.add_argument("--with-artifacts", action="store_true")
    kg.add_argument("--with-facts", action="store_true")
    kg.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    kg.add_argument("--embedding-backend", default="sentence-transformers")
    kg.add_argument("--kg-model", default="sentence-transformers/all-MiniLM-L6-v2")
    kg.add_argument("--kg-embedding-backend", default="sentence-transformers")
    kg.add_argument("--focus-query", default="protein engineering")
    kg.set_defaults(func=cmd_kg_build)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
