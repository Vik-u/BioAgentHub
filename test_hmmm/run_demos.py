#!/usr/bin/env python3
"""Run QA/protocol/biofoundry demos and save inputs/outputs under test_hmmm/."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fabric.agents.rl_rag_agent import run_qa  # noqa: E402
from fabric.agents.protocol_agent_v2 import run_protocol_agent_v2  # noqa: E402
from fabric.agents.instrument_protocol_agent_v2 import run_instrument_protocol_v2  # noqa: E402
from fabric.agents.biofoundry_protocol_orchestrator import run_biofoundry  # noqa: E402
OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def write_md(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def run_qa_chat_demo() -> dict:
    os.environ["WORKSPACE_ROOT"] = str(ROOT / "workspaces" / "petase")
    os.environ["USE_ALIAS_EXPANSION"] = "1"

    session_id = "demo_petase_chat_v2"
    questions = [
        "List engineered PETase variants in this workspace that improve thermostability or activity. Include variant names, mutations, and any quantitative improvements reported.",
        "For each variant you listed (e.g., ThermoPETase, FastPETase, HotPETase, DepoPETase), enumerate the exact mutations and note which ones target stability vs activity vs thermostability. Do not invent mutations; if a mutation is not explicitly stated in the corpus, say \"not reported\".",
        "What assays/methods and host organisms were used to quantify those improvements? Tie each assay/organism to the variants above.",
        "Quantify the improvements (activity, thermostability, Tm, half-life, or % conversion) and report the test conditions if stated.",
        "Compare ThermoPETase and FastPETase (or two variants you listed) and summarize trade-offs in thermostability vs activity with reported values. If the corpus lacks values, say so.",
    ]
    config = {
        "use_llm": True,
        "temperature": 0.1,
        "use_kg": True,
        "enable_query_planner": True,
        "enable_bm25": False,
        "enable_rerank": True,
        "enable_verifier": True,
        "use_claim_store": False,
        "persist_claims": False,
        "use_langgraph_qa": False,
        "output_mode": "answer_dual",
        "chat_mode": True,
        "use_rl_policy": False,
        "policy_model": None,
        "seed": 7,
    }

    turns = []
    for q in questions:
        result = run_qa(
            question=q,
            use_llm=config["use_llm"],
            temperature=config["temperature"],
            use_kg=config["use_kg"],
            enable_query_planner=config["enable_query_planner"],
            enable_bm25=config["enable_bm25"],
            enable_rerank=config["enable_rerank"],
            enable_verifier=config["enable_verifier"],
            use_understanding_layer=None,
            use_claim_store=config["use_claim_store"],
            persist_claims=config["persist_claims"],
            use_langgraph_qa=config["use_langgraph_qa"],
            session_id=session_id,
            chat_mode=config["chat_mode"],
            use_rl_policy=config["use_rl_policy"],
            policy_model=config["policy_model"],
            output_mode=config["output_mode"],
            seed=config["seed"],
        )
        turns.append(
            {
                "question": q,
                "answer": result.get("answer"),
                "answer_helpful": result.get("answer_helpful"),
                "answer_structured": result.get("answer_structured"),
                "citations": result.get("citations"),
                "metrics": result.get("metrics"),
                "blocks": result.get("blocks"),
                "claims": result.get("claims"),
            }
        )

    payload = {
        "session_id": session_id,
        "workspace": os.environ["WORKSPACE_ROOT"],
        "config": config,
        "turns": turns,
    }
    return payload


def run_protocol_v2_demo() -> dict:
    os.environ["WORKSPACE_ROOT"] = str(ROOT / "workspaces" / "petase")
    question = (
        "Design a PETase benchmarking workflow to compare engineered variants for activity and thermostability. "
        "Include wet-lab steps, key parameters, assays, and computational analysis steps."
    )
    answer = run_protocol_agent_v2(question)
    return {
        "workspace": os.environ["WORKSPACE_ROOT"],
        "question": question,
        "answer": answer,
    }


def run_instrument_protocol_demo() -> dict:
    os.environ["WORKSPACE_ROOT"] = str(ROOT / "workspaces" / "petase")
    os.environ["BIOAGENT_USE_INSTRUMENTS"] = "1"
    question = (
        "Draft a PETase variant screening protocol that uses Biofoundry instruments for high-throughput activity "
        "and thermostability assays. Include experimental and computational steps."
    )
    answer = run_instrument_protocol_v2(question)
    return {
        "workspace": os.environ["WORKSPACE_ROOT"],
        "question": question,
        "answer": answer,
    }


def run_biofoundry_demo() -> dict:
    os.environ["WORKSPACE_ROOT"] = str(ROOT / "workspaces" / "petase")
    os.environ["BIOAGENT_USE_INSTRUMENTS"] = "0"
    result = run_biofoundry(
        topics=["petase"],
        use_kg=True,
        include_instruments=False,
        kg_top_k=5,
        assay_enabled=True,
        llm_rationale=True,
    )
    return {
        "workspace": os.environ["WORKSPACE_ROOT"],
        "config": {
            "topics": ["petase"],
            "use_kg": True,
            "include_instruments": False,
            "kg_top_k": 5,
            "assay_enabled": True,
            "llm_rationale": True,
        },
        "result": result,
    }


def main() -> None:
    qa_payload = run_qa_chat_demo()
    write_json(OUT_DIR / "qa_chat_petase.json", qa_payload)

    # Human-readable QA transcript
    qa_lines = ["Start input", "", "Session:", qa_payload["session_id"], "", "Questions:"]
    for idx, turn in enumerate(qa_payload["turns"], start=1):
        qa_lines.append(f"{idx}. {turn['question']}")
    qa_lines.append("")
    qa_lines.append("Output")
    for idx, turn in enumerate(qa_payload["turns"], start=1):
        qa_lines.append("")
        qa_lines.append(f"Turn {idx} answer (verbatim):")
        qa_lines.append(turn.get("answer") or "")
    write_md(OUT_DIR / "qa_chat_petase.md", "\n".join(qa_lines).strip() + "\n")

    proto_payload = run_protocol_v2_demo()
    write_json(OUT_DIR / "protocol_agent_v2.json", proto_payload)
    proto_md = "\n".join(
        [
            "Start input",
            "",
            f"Workspace: {proto_payload['workspace']}",
            "Question:",
            proto_payload["question"],
            "",
            "Output",
            proto_payload["answer"],
        ]
    )
    write_md(OUT_DIR / "protocol_agent_v2.md", proto_md.strip() + "\n")

    inst_payload = run_instrument_protocol_demo()
    write_json(OUT_DIR / "instrument_protocol_v2.json", inst_payload)
    inst_md = "\n".join(
        [
            "Start input",
            "",
            f"Workspace: {inst_payload['workspace']}",
            "Question:",
            inst_payload["question"],
            "",
            "Output",
            inst_payload["answer"],
        ]
    )
    write_md(OUT_DIR / "instrument_protocol_v2.md", inst_md.strip() + "\n")

    bf_payload = run_biofoundry_demo()
    write_json(OUT_DIR / "biofoundry_orchestrator.json", bf_payload)
    bf_result = bf_payload["result"]
    bf_lines = [
        "Start input",
        "",
        f"Workspace: {bf_payload['workspace']}",
        "Config:",
        json.dumps(bf_payload["config"], indent=2),
        "",
        "Output",
        json.dumps(bf_result, indent=2),
    ]
    write_md(OUT_DIR / "biofoundry_orchestrator.md", "\n".join(bf_lines).strip() + "\n")


if __name__ == "__main__":
    main()
