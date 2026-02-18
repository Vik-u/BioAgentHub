#!/usr/bin/env python3
"""Gradio QA chatbot with multi-turn session memory."""

from __future__ import annotations

import argparse
import atexit
import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import gradio as gr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fabric.agents.rag_agent import generate_session_id, run_qa  # noqa: E402
from utils.output_paths import logs_dir  # noqa: E402

PID_PATH = logs_dir() / "gradio_chatbot.pid"


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _pid_matches_repo(pid: int) -> bool:
    cmdline_path = Path(f"/proc/{pid}/cmdline")
    if not cmdline_path.exists():
        return False
    try:
        raw = cmdline_path.read_bytes()
    except Exception:
        return False
    parts = [p.decode(errors="ignore") for p in raw.split(b"\0") if p]
    cmdline = " ".join(parts)
    return ("gradio_chatbot.py" in cmdline) and (str(PROJECT_ROOT) in cmdline)


def _terminate_pid(pid: int, timeout_s: float = 2.0) -> bool:
    if not _pid_alive(pid):
        return True
    try:
        os.kill(pid, signal.SIGTERM)
    except Exception:
        return False
    start = time.time()
    while time.time() - start < timeout_s:
        if not _pid_alive(pid):
            return True
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except Exception:
        return False
    return not _pid_alive(pid)


def _ensure_single_instance() -> None:
    PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    if PID_PATH.exists():
        try:
            pid = int(PID_PATH.read_text().strip())
        except Exception:
            pid = 0
        if pid and pid != os.getpid() and _pid_matches_repo(pid):
            _terminate_pid(pid)
    PID_PATH.write_text(str(os.getpid()))

    def _cleanup_pid() -> None:
        try:
            PID_PATH.unlink()
        except FileNotFoundError:
            return
        except Exception:
            return

    atexit.register(_cleanup_pid)


def _format_citations(citations: List[Dict[str, Any]]) -> str:
    if not citations:
        return "No citations returned."
    lines = []
    for cite in citations:
        cid = cite.get("id")
        title = cite.get("title") or "Unknown title"
        authors = cite.get("authors")
        year = cite.get("year")
        doi = cite.get("doi")
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
        paper = " — ".join(parts) if parts else (cite.get("paper") or "unknown")
        label = f"[{cid}] " if cid is not None else ""
        lines.append(f"- {label}{paper}")
    return "\n".join(lines)


def _format_metrics(metrics: Dict[str, Any]) -> str:
    if not metrics:
        return "No metrics returned."
    return "\n".join([f"- {key}: {value}" for key, value in metrics.items()])


def _detect_base_root(path: Path) -> Path:
    if (path / "metadata").exists() or (path / "vector_store").exists() or (path / "text").exists():
        return path.parent
    return path


def _default_workspace_root() -> Path:
    env_root = os.getenv("WORKSPACE_ROOT")
    if env_root:
        resolved = Path(env_root).expanduser().resolve()
        return _detect_base_root(resolved)
    return (PROJECT_ROOT / "workspaces").resolve()


def _resolve_workspace(workspace: str) -> Path:
    if not workspace:
        base = _default_workspace_root()
        return (base / "all_topics").resolve() if (base / "all_topics").exists() else base
    candidate = Path(workspace)
    if candidate.is_absolute():
        return candidate.expanduser().resolve()
    if "/" in workspace or "\\" in workspace:
        return (_default_workspace_root() / workspace).expanduser().resolve()
    return (_default_workspace_root() / workspace).expanduser().resolve()


def _list_workspaces() -> List[str]:
    root = _default_workspace_root()
    if not root.exists():
        return []
    return sorted(
        [
            p.name
            for p in root.iterdir()
            if p.is_dir() and not p.name.startswith(".") and p.name != "all_topics"
        ]
    )


def _apply_env(workspace: str, allow_noncanonical: bool, alias_expansion: bool) -> None:
    if allow_noncanonical:
        os.environ["ALLOW_NONCANONICAL_WORKSPACE"] = "1"
    else:
        os.environ["ALLOW_NONCANONICAL_WORKSPACE"] = "0"

    resolved = _resolve_workspace(workspace)
    os.environ["WORKSPACE_ROOT"] = str(resolved)

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


def chat_turn(
    message,
    history,
    session_id,
    workspace,
    allow_noncanonical,
    alias_expansion,
    use_llm,
    temperature,
    use_kg,
    query_planner,
    bm25,
    rerank,
    verifier,
    use_claim_store,
    persist_claims,
):
    message = (message or "").strip()
    if not message:
        return history, session_id, "", "", ""

    _apply_env(workspace, allow_noncanonical, alias_expansion)
    _patch_urllib3_default_ciphers()
    active_session = session_id.strip() or generate_session_id()

    result = run_qa(
        question=message,
        use_llm=use_llm,
        temperature=temperature if use_llm else None,
        use_kg=use_kg,
        enable_query_planner=query_planner,
        enable_bm25=bm25,
        enable_rerank=rerank,
        enable_verifier=verifier,
        use_understanding_layer=None,
        use_claim_store=use_claim_store,
        persist_claims=persist_claims,
        session_id=active_session,
        chat_mode=True,
        use_rl_policy=False,
        policy_model=None,
        output_mode="answer_dual",
    )

    answer = result.get("answer", "")
    history = list(history or [])
    history.append((message, answer))

    citations_md = _format_citations(result.get("citations", []))
    metrics_md = _format_metrics(result.get("metrics", {}))

    return history, active_session, citations_md, metrics_md, ""


def reset_session():
    new_id = generate_session_id()
    return [], new_id, "Session reset.", "Session reset."


def run_protocol(
    question,
    workspace,
    allow_noncanonical,
):
    question = (question or "").strip()
    if not question:
        return ""
    _apply_env(workspace, allow_noncanonical, alias_expansion=False)
    _patch_urllib3_default_ciphers()
    try:
        from fabric.agents.protocol_agent_v2 import run_protocol_agent_v2  # noqa: E402
    except Exception as exc:  # pragma: no cover - import-time env issues
        return f"Protocol agent failed to import: {exc}"
    try:
        return run_protocol_agent_v2(question)
    except Exception as exc:  # pragma: no cover - runtime env issues
        return f"Protocol agent error: {exc}"


def run_biofoundry(case_key):
    case_key = (case_key or "").strip()
    if not case_key:
        return "Select a case."
    try:
        from fabric.agents import biofoundry_protocol_agent as bf_agent  # noqa: E402
    except Exception as exc:  # pragma: no cover
        return f"Biofoundry agent failed to import: {exc}"
    choice = bf_agent.CASE_MAP.get(case_key)
    if not choice:
        return f"Unknown case: {case_key}"
    template_key = choice["template"]
    template_path = bf_agent.TEMPLATES[template_key]
    content = bf_agent.load_template(template_path)
    header = (
        f"# Biofoundry protocol for {case_key}\n\n"
        f"Template: {template_path.name}\n"
        f"Rationale: {choice['rationale']}\n\n"
        "Note: Content is copied verbatim from the chosen template. "
        "Do not add steps, reagents, or instruments beyond what is listed here. "
        "If downstream screening/genotyping is needed, add a TODO outside this file.\n\n"
    )
    return header + content


def run_biofoundry_orchestrator(
    topics,
    include_instruments,
    kg_top_k,
    assay_evidence,
    llm_rationale,
    no_kg,
):
    topics = (topics or "").strip()
    topic_list = [t.strip() for t in topics.split(",") if t.strip()] if topics else None
    os.environ["BIOAGENT_USE_INSTRUMENTS"] = "1" if include_instruments else "0"
    try:
        from fabric.agents.biofoundry_protocol_orchestrator import run_biofoundry  # noqa: E402
    except Exception as exc:  # pragma: no cover
        return f"Biofoundry orchestrator failed to import: {exc}"
    try:
        result = run_biofoundry(
            topics=topic_list,
            use_kg=not no_kg,
            include_instruments=include_instruments,
            kg_top_k=int(kg_top_k),
            assay_enabled=assay_evidence,
            llm_rationale=llm_rationale,
        )
    except Exception as exc:  # pragma: no cover
        return f"Biofoundry orchestrator error: {exc}"
    return json.dumps(result, indent=2, ensure_ascii=False)


def run_multi_agent_ui(question, workspace, allow_noncanonical, alias_expansion):
    question = (question or "").strip()
    if not question:
        return ""
    _apply_env(workspace, allow_noncanonical, alias_expansion)
    try:
        from fabric.agents.multi_agent_orchestrator import run_multi_agent  # noqa: E402
    except Exception as exc:  # pragma: no cover
        return f"Multi-agent orchestrator failed to import: {exc}"
    try:
        result = run_multi_agent(question, Path(os.environ["WORKSPACE_ROOT"]), alias_expansion)
    except Exception as exc:  # pragma: no cover
        return f"Multi-agent orchestrator error: {exc}"
    return json.dumps(result, indent=2, ensure_ascii=False)


def build_app() -> gr.Blocks:
    workspace_options = _list_workspaces()
    default_workspace = (
        "all_topics"
        if "all_topics" in workspace_options
        else (workspace_options[0] if workspace_options else "")
    )
    workspace_root = _default_workspace_root()
    with gr.Blocks(title="BioAgentHub Chat Suite") as demo:
        gr.Markdown("## BioAgentHub Chat Suite")

        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### Workspace Settings")
                gr.Markdown(f"**Workspace root:** `{workspace_root}`")
                workspace = gr.Dropdown(
                    choices=workspace_options,
                    value=default_workspace,
                    label="Workspace",
                    allow_custom_value=True,
                    info="Select a workspace name (recommended). You can also paste a full path.",
                )
                allow_noncanonical = gr.Checkbox(
                    label="Allow non-canonical workspace",
                    value=False,
                )
            with gr.Column(scale=2):
                gr.Markdown("### Info")
                gr.Markdown(
                    "Use the tabs for QA chat, protocol drafting, and biofoundry templates."
                )

        with gr.Tabs():
            with gr.TabItem("Q&A Chat"):
                with gr.Row():
                    with gr.Column(scale=3):
                        chatbot = gr.Chatbot(label="Chat", height=460)
                        message = gr.Textbox(
                            label="Message",
                            placeholder="Ask a question about the workspace...",
                        )
                        with gr.Row():
                            send = gr.Button("Send", variant="primary")
                            reset = gr.Button("Reset session")
                    with gr.Column(scale=2):
                        gr.Markdown("### Session + Options")
                        session_id = gr.Textbox(
                            label="Session ID",
                            placeholder="Leave empty to auto-generate",
                        )
                        alias_expansion = gr.Checkbox(
                            label="Alias expansion",
                            value=False,
                        )
                        use_llm = gr.Checkbox(label="Use LLM summarizer", value=True)
                        temperature = gr.Slider(
                            0.0,
                            1.0,
                            value=0.0,
                            step=0.05,
                            label="Temperature",
                        )
                        use_kg = gr.Checkbox(label="Use KG expansion", value=True)
                        query_planner = gr.Checkbox(label="Query planner", value=True)
                        bm25 = gr.Checkbox(label="BM25", value=True)
                        rerank = gr.Checkbox(label="Rerank", value=True)
                        verifier = gr.Checkbox(label="Verifier", value=True)
                        use_claim_store = gr.Checkbox(label="Claims-lite composer", value=False)
                        persist_claims = gr.Checkbox(label="Persist claims", value=False)

                        with gr.Accordion("Citations", open=False):
                            citations = gr.Markdown("No citations yet.")
                        with gr.Accordion("Metrics", open=False):
                            metrics = gr.Markdown("No metrics yet.")

                send.click(
                    chat_turn,
                    inputs=[
                        message,
                        chatbot,
                        session_id,
                        workspace,
                        allow_noncanonical,
                        alias_expansion,
                        use_llm,
                        temperature,
                        use_kg,
                        query_planner,
                        bm25,
                        rerank,
                        verifier,
                        use_claim_store,
                        persist_claims,
                    ],
                    outputs=[chatbot, session_id, citations, metrics, message],
                    api_name=False,
                )
                message.submit(
                    chat_turn,
                    inputs=[
                        message,
                        chatbot,
                        session_id,
                        workspace,
                        allow_noncanonical,
                        alias_expansion,
                        use_llm,
                        temperature,
                        use_kg,
                        query_planner,
                        bm25,
                        rerank,
                        verifier,
                        use_claim_store,
                        persist_claims,
                    ],
                    outputs=[chatbot, session_id, citations, metrics, message],
                    api_name=False,
                )
                reset.click(
                    reset_session,
                    inputs=[],
                    outputs=[chatbot, session_id, citations, metrics],
                    api_name=False,
                )

            with gr.TabItem("Protocol (general)"):
                question = gr.Textbox(
                    label="Protocol question",
                    placeholder="Describe the protocol goal...",
                )
                run = gr.Button("Generate protocol", variant="primary")
                protocol_out = gr.Markdown()
                run.click(
                    run_protocol,
                    inputs=[question, workspace, allow_noncanonical],
                    outputs=[protocol_out],
                    api_name=False,
                )

            with gr.TabItem("Biofoundry Template"):
                case_key = gr.Dropdown(
                    label="Case",
                    choices=["petase", "3hp_pand", "retron"],
                    value=None,
                )
                bf_run = gr.Button("Generate template protocol", variant="primary")
                bf_out = gr.Markdown()
                bf_run.click(
                    run_biofoundry,
                    inputs=[case_key],
                    outputs=[bf_out],
                    api_name=False,
                )

            with gr.TabItem("Biofoundry Orchestrator"):
                gr.Markdown("### Template + KG Orchestrator (module-based)")
                topics = gr.Textbox(
                    label="Topics (comma-separated)",
                    placeholder="petase, 3hp_pand, retron",
                )
                include_instruments = gr.Checkbox(
                    label="Include InstrumentGraph evidence",
                    value=False,
                )
                kg_top_k = gr.Slider(1, 20, value=5, step=1, label="KG top_k per module")
                assay_evidence = gr.Checkbox(label="Assay evidence", value=True)
                llm_rationale = gr.Checkbox(label="LLM rationale", value=False)
                no_kg = gr.Checkbox(label="Disable KG enrichment", value=False)
                bf_orch_run = gr.Button("Run orchestrator", variant="primary")
                bf_orch_out = gr.Code(label="Orchestrator output (JSON)")
                bf_orch_run.click(
                    run_biofoundry_orchestrator,
                    inputs=[topics, include_instruments, kg_top_k, assay_evidence, llm_rationale, no_kg],
                    outputs=[bf_orch_out],
                    api_name=False,
                )

            with gr.TabItem("Multi-agent Orchestrator"):
                gr.Markdown("### QA + Timeline + Hypotheses + Protocol")
                ma_question = gr.Textbox(
                    label="Query",
                    placeholder="Design a benchmarking workflow for PETase mutations.",
                )
                ma_run = gr.Button("Run multi-agent", variant="primary")
                ma_out = gr.Code(label="Multi-agent output (JSON)")
                ma_run.click(
                    run_multi_agent_ui,
                    inputs=[ma_question, workspace, allow_noncanonical, alias_expansion],
                    outputs=[ma_out],
                    api_name=False,
                )

    return demo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("GRADIO_SERVER_PORT", "7860")))
    parser.add_argument("--share", action="store_true", help="Create a public share link.")
    args = parser.parse_args()

    _ensure_single_instance()
    app = build_app()
    app.launch(server_name=args.host, server_port=args.port, share=args.share)


if __name__ == "__main__":
    main()
