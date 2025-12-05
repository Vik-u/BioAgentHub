#!/usr/bin/env python3
"""Gradio dashboard exposing QA, protocol, and benchmarking agents."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

import gradio as gr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.protocol_agent import run_protocol_agent  # noqa: E402
from agents.instrument_protocol_agent import run_instrument_protocol  # noqa: E402
from agents.protocol_agent_v2 import run_protocol_agent_v2  # noqa: E402
from agents.instrument_protocol_agent_v2 import run_instrument_protocol_v2  # noqa: E402
from agents.rl_rag_agent import run_agent  # noqa: E402
from scripts.report_answer_metrics import (  # noqa: E402
    format_metric,
    load_questions,
    run_benchmark,
)

try:  # pragma: no cover - optional dependency
    from stable_baselines3 import PPO
except Exception:  # pragma: no cover
    PPO = None

policy_cache: Dict[str, Optional[object]] = {}


def load_policy(path: str | None):
    if not path:
        return None
    if PPO is None:
        raise RuntimeError("stable-baselines3 not installed; cannot load PPO policy.")
    normalized = Path(path).expanduser().resolve()
    cache_key = str(normalized)
    if cache_key in policy_cache:
        return policy_cache[cache_key]
    model = PPO.load(cache_key)
    policy_cache[cache_key] = model
    return model


def ensure_workspace_env() -> Path:
    """
    Ensure WORKSPACE_ROOT points to a valid workspace.

    When GRADIO runs without this, calls can silently fail. Default to all_topics if unset.
    """
    current = os.environ.get("WORKSPACE_ROOT")
    if current:
        return Path(current).expanduser().resolve()
    default_ws = PROJECT_ROOT / "workspaces" / "all_topics"
    if not default_ws.exists():
        raise SystemExit(f"Workspace not found: {default_ws}")
    os.environ["WORKSPACE_ROOT"] = str(default_ws)
    return default_ws


WORKSPACE_PATH = ensure_workspace_env()
LOG_DIR = PROJECT_ROOT / "logs" / "protocol_runs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def qa_handler(question: str, mode: str, seed: int, policy_path: str):
    question = (question or "").strip()
    if not question:
        return "Please enter a question."
    try:
        policy = load_policy(policy_path.strip() or None)
    except Exception as exc:  # pragma: no cover
        return f"Policy load error: {exc}"
    result = run_agent(
        question,
        use_llm=(mode == "LLM"),
        seed=seed,
        policy_model=policy,
    )
    answer = result.get("answer", "")
    metrics = result.get("metrics") or {}
    cites = result.get("citations") or []
    metrics_text = (
        f"FAISS avg: {format_metric(metrics.get('faiss_avg'))} | "
        f"KG conf avg: {format_metric(metrics.get('kg_conf_avg'))} | "
        f"RL reward sum: {format_metric(metrics.get('rl_reward_sum'))}"
    )
    citation_lines = [
        f"[{c['id']}] {c['title']} ({c['paper']})" for c in cites
    ] or ["No citations."]
    return (
        f"{answer}\n\n**Metrics**\n{metrics_text}\n\n**Sources**\n" + "\n".join(citation_lines)
    )


def protocol_handler(question: str, mode: str, max_instruments: int):
    question = (question or "").strip()
    if not question:
        return "Please enter a protocol prompt."
    output = ""
    try:
        if mode == "Biofoundry-constrained (legacy)":
            output = run_instrument_protocol(question, top_n=int(max_instruments))
        elif mode == "Methodology-driven (papers)":
            output = run_protocol_agent_v2(question)
        elif mode == "Biofoundry instrument-constrained":
            output = run_instrument_protocol_v2(question)
        else:
            output = run_protocol_agent(question)
    except Exception as exc:  # pragma: no cover
        return f"Protocol generation error: {exc}"
    # Persist a copy so users can open it later.
    try:
        import datetime as _dt

        stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = LOG_DIR / f"gradio_protocol_{stamp}.md"
        with filename.open("w", encoding="utf-8") as handle:
            handle.write(output)
        output += f"\n\n_Saved to: {filename}_"
    except Exception:
        pass
    return output


def benchmark_handler(question_block: str, mode: str, seed: int, policy_path: str):
    lines = [line.strip() for line in (question_block or "").splitlines() if line.strip()]
    questions = lines or load_questions(None)
    policy_arg = Path(policy_path.strip()) if policy_path.strip() else None
    try:
        rows = run_benchmark(questions, mode=mode.lower(), seed=seed, policy_path=policy_arg)
    except Exception as exc:  # pragma: no cover
        return f"Benchmark error: {exc}"

    header = "| Question | FAISS avg | KG conf avg | RL reward sum |\n|---|---|---|---|\n"
    body = "\n".join(
        f"| {row['question'][:60]} | {format_metric(row['faiss_avg'])} | "
        f"{format_metric(row['kg_conf_avg'])} | {format_metric(row['rl_reward_sum'])} |"
        for row in rows
    )
    return header + body


with gr.Blocks(title="PETase Research Dashboard") as demo:
    gr.Markdown("# PETase Research Dashboard\nSelect a tab to run the RL/LLM QA agent, protocol designer, or benchmarking suite.")

    with gr.Tab("Question Answering"):
        question = gr.Textbox(label="Question", lines=4)
        mode = gr.Radio(choices=["LLM", "Plain"], value="LLM", label="Mode")
        seed = gr.Slider(1, 999, value=7, step=1, label="Random Seed")
        policy = gr.Textbox(label="PPO Policy Path (optional)")
        qa_btn = gr.Button("Run QA")
        qa_output = gr.Markdown()
        qa_btn.click(qa_handler, inputs=[question, mode, seed, policy], outputs=qa_output)

    with gr.Tab("Protocol Designer"):
        proto_q = gr.Textbox(label="Experimental / computational request", lines=4)
        proto_mode = gr.Radio(
            choices=[
                "Standard (legacy)",
                "Methodology-driven (papers)",
                "Biofoundry instrument-constrained",
                "Biofoundry-constrained (legacy)",
            ],
            value="Methodology-driven (papers)",
            label="Protocol Mode",
        )
        proto_max = gr.Slider(
            3,
            16,
            value=8,
            step=1,
            label="Max Instruments (constrained mode only)",
        )
        proto_btn = gr.Button("Generate Protocol")
        proto_output = gr.Markdown()
        proto_btn.click(
            protocol_handler,
            inputs=[proto_q, proto_mode, proto_max],
            outputs=proto_output,
        )

    with gr.Tab("Benchmark Metrics"):
        bench_q = gr.Textbox(
            label="Questions (one per line; leave blank for defaults)",
            lines=6,
        )
        bench_mode = gr.Radio(choices=["LLM", "Plain"], value="LLM", label="Mode")
        bench_seed = gr.Slider(1, 999, value=7, step=1, label="Random Seed")
        bench_policy = gr.Textbox(label="PPO Policy Path (optional)")
        bench_btn = gr.Button("Run Benchmark")
        bench_output = gr.Markdown()
        bench_btn.click(
            benchmark_handler,
            inputs=[bench_q, bench_mode, bench_seed, bench_policy],
            outputs=bench_output,
        )


if __name__ == "__main__":  # pragma: no cover
    host = os.environ.get("GRADIO_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
    # Gradio 5.x: queue has no args; limit global concurrency via GRADIO_NUM_BACKLOG or env if needed.
    demo.queue().launch(server_name=host, server_port=port)
