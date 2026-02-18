#!/usr/bin/env python3
"""FastAPI hub for QA, protocol, biofoundry orchestration, and multi-agent runs."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from fabric.agents.rag_agent import run_qa  # noqa: E402
from utils.workspace_utils import list_topics  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
app = FastAPI(
    title="BioAgentHub API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


def _apply_env(
    workspace: Optional[str],
    allow_noncanonical: bool = False,
    alias_expansion: bool = False,
) -> None:
    if allow_noncanonical:
        os.environ["ALLOW_NONCANONICAL_WORKSPACE"] = "1"
    else:
        os.environ["ALLOW_NONCANONICAL_WORKSPACE"] = "0"
    if workspace:
        os.environ["WORKSPACE_ROOT"] = str(Path(workspace).expanduser().resolve())
    os.environ["USE_ALIAS_EXPANSION"] = "1" if alias_expansion else "0"


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


class QARequest(BaseModel):
    question: str
    workspace: Optional[str] = None
    allow_noncanonical: bool = False
    alias_expansion: bool = False
    use_llm: bool = True
    temperature: float = 0.0
    use_kg: bool = True
    query_planner: bool = True
    bm25: bool = True
    rerank: bool = True
    verifier: bool = True
    use_claim_store: bool = False
    persist_claims: bool = False
    use_langgraph_qa: bool = False
    output_mode: str = "answer_dual"
    chat_mode: bool = False
    session_id: Optional[str] = None
    use_rl_policy: bool = False
    policy_path: Optional[str] = None
    seed: int = 7


class ProtocolRequest(BaseModel):
    question: str
    workspace: Optional[str] = None
    allow_noncanonical: bool = False
    alias_expansion: bool = False


class BiofoundryRequest(BaseModel):
    topics: Optional[List[str]] = Field(default=None, description="Topic list, or null to auto-discover.")
    use_kg: bool = True
    include_instruments: bool = False
    kg_top_k: int = 5
    assay_evidence: bool = True
    llm_rationale: bool = False


class MultiAgentRequest(BaseModel):
    query: str
    workspace: str
    alias_expansion: bool = False


class KGBuildRequest(BaseModel):
    topic: str
    pdf_dir: Optional[str] = None
    workspace: Optional[str] = None
    auto_schema: bool = True
    skip_kg: bool = False
    with_artifacts: bool = False
    with_facts: bool = False
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_backend: str = "sentence-transformers"
    kg_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    kg_embedding_backend: str = "sentence-transformers"
    focus_query: str = "protein engineering"


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "topics": list_topics(),
        "workspace_root": os.environ.get("WORKSPACE_ROOT"),
        "llm_backend": os.environ.get("LLM_BACKEND") or "config/llm_config.json",
    }


@app.post("/qa")
def qa(payload: QARequest) -> Dict[str, Any]:
    _apply_env(payload.workspace, payload.allow_noncanonical, payload.alias_expansion)
    try:
        result = run_qa(
            question=payload.question,
            use_llm=payload.use_llm,
            temperature=payload.temperature if payload.use_llm else None,
            use_kg=payload.use_kg,
            enable_query_planner=payload.query_planner,
            enable_bm25=payload.bm25,
            enable_rerank=payload.rerank,
            enable_verifier=payload.verifier,
            use_understanding_layer=None,
            use_claim_store=payload.use_claim_store,
            persist_claims=payload.persist_claims,
            use_langgraph_qa=payload.use_langgraph_qa,
            session_id=payload.session_id or None,
            chat_mode=payload.chat_mode,
            use_rl_policy=payload.use_rl_policy,
            policy_model=None,
            output_mode=payload.output_mode,
            seed=payload.seed,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return result


@app.post("/protocol_v2")
def protocol_v2(payload: ProtocolRequest) -> Dict[str, Any]:
    _apply_env(payload.workspace, payload.allow_noncanonical, payload.alias_expansion)
    try:
        _patch_urllib3_default_ciphers()
        from fabric.agents.protocol_agent_v2 import run_protocol_agent_v2  # noqa: E402
        answer = run_protocol_agent_v2(payload.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"answer": answer}


@app.post("/biofoundry/generate")
def biofoundry_generate(payload: BiofoundryRequest) -> Dict[str, Any]:
    if payload.include_instruments:
        os.environ["BIOAGENT_USE_INSTRUMENTS"] = "1"
    else:
        os.environ["BIOAGENT_USE_INSTRUMENTS"] = "0"
    try:
        _patch_urllib3_default_ciphers()
        from fabric.agents.biofoundry_protocol_orchestrator import run_biofoundry  # noqa: E402
        result = run_biofoundry(
            topics=payload.topics,
            use_kg=payload.use_kg,
            include_instruments=payload.include_instruments,
            kg_top_k=max(1, payload.kg_top_k),
            assay_enabled=payload.assay_evidence,
            llm_rationale=payload.llm_rationale,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return result


@app.post("/multi_agent/run")
def multi_agent(payload: MultiAgentRequest) -> Dict[str, Any]:
    try:
        _patch_urllib3_default_ciphers()
        from fabric.agents.multi_agent_orchestrator import run_multi_agent  # noqa: E402
        result = run_multi_agent(
            query=payload.query,
            workspace=Path(payload.workspace),
            use_alias_expansion=payload.alias_expansion,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return result


@app.post("/kg/build")
def kg_build(payload: KGBuildRequest) -> Dict[str, Any]:
    pdf_dir = Path(payload.pdf_dir) if payload.pdf_dir else PROJECT_ROOT / "data" / payload.topic
    workspace = Path(payload.workspace) if payload.workspace else PROJECT_ROOT / "workspaces" / payload.topic
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "forge" / "scripts" / "build_topic_full.py"),
        "--topic",
        payload.topic,
        "--pdf-dir",
        str(pdf_dir),
        "--workspace",
        str(workspace),
        "--model",
        payload.model,
        "--embedding-backend",
        payload.embedding_backend,
        "--kg-model",
        payload.kg_model,
        "--kg-embedding-backend",
        payload.kg_embedding_backend,
        "--focus-query",
        payload.focus_query,
    ]
    if payload.auto_schema:
        cmd.append("--auto-schema")
    if payload.skip_kg:
        cmd.append("--skip-kg")
    if payload.with_artifacts:
        cmd.append("--with-artifacts")
    if payload.with_facts:
        cmd.append("--with-facts")

    result = subprocess.run(cmd, capture_output=True, text=True)
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "KG build failed",
                "returncode": result.returncode,
                "stderr": stderr[-4000:],
                "stdout": stdout[-4000:],
            },
        )
    return {
        "status": "ok",
        "command": cmd,
        "workspace": str(workspace),
        "pdf_dir": str(pdf_dir),
        "stdout": stdout[-4000:],
        "stderr": stderr[-4000:],
    }
