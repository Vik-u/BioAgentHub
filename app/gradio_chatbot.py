#!/usr/bin/env python3
"""Gradio chatbot that proxies questions to the PETase RL agent."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import os

import huggingface_hub

os.environ.setdefault("GRADIO_SKIP_URL_CHECK", "1")

if not hasattr(huggingface_hub, "HfFolder"):
    class HfFolder:  # pragma: no cover - compatibility shim
        @staticmethod
        def get_token():
            return None

        @staticmethod
        def save_token(_: str) -> None:
            return None

        @staticmethod
        def delete_token() -> None:
            return None

    huggingface_hub.HfFolder = HfFolder  # type: ignore[attr-defined]

import gradio as gr

try:  # pragma: no cover - gradio internal quirks
    import gradio.networking as _gradio_networking

    _gradio_networking.url_ok = lambda *_, **__: True
except Exception:
    pass

try:
    from gradio_client import utils as _gradio_client_utils

    _orig_get_type = _gradio_client_utils.get_type

    def _patched_get_type(schema):
        if isinstance(schema, bool):
            return "any"
        return _orig_get_type(schema)

    _gradio_client_utils.get_type = _patched_get_type
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.rl_rag_agent import run_agent  # noqa: E402


def answer_question(message: str, history: list[tuple[str, str]], mode: str, seed: int) -> tuple[str, list[tuple[str, str]]]:
    use_llm = mode == "RL + GPT-OSS"
    result = run_agent(message, use_llm=use_llm, seed=seed)
    answer = result["answer"]
    enriched = answer + "\n\n" + json.dumps(
        {"mode": mode, "steps": result["trajectory"], "rewards": result["rewards"]},
        indent=2,
        ensure_ascii=False,
    )
    history = history + [(message, enriched)]
    return "", history


with gr.Blocks(title="PETase Research Copilot") as demo:
    gr.Markdown("### PETase Research Copilot\nAsk PETase literature questions; choose RL-only or RL + GPT-OSS modes.")
    with gr.Row():
        mode = gr.Radio(["RL Only", "RL + GPT-OSS"], value="RL + GPT-OSS", label="Agent Mode")
        seed = gr.Number(value=7, label="Random Seed", precision=0)
    chatbot = gr.Chatbot(height=400)
    msg = gr.Textbox(label="Question", placeholder="e.g., Which engineered PETases target semi-crystalline PET?")
    clear = gr.Button("Clear")

    def submit(user_message, chat_history, mode_value, seed_value):
        return answer_question(user_message, chat_history, mode_value, int(seed_value))

    msg.submit(submit, inputs=[msg, chatbot, mode, seed], outputs=[msg, chatbot])
    clear.click(lambda: ([], ""), None, [chatbot, msg], queue=False)


if __name__ == "__main__":
    port = int(os.environ.get("GRADIO_SERVER_PORT", "7862"))
    share_flag = os.environ.get("GRADIO_SHARE", "0") == "1"
    print(f"[Gradio] Launching on port {port} (share={'on' if share_flag else 'off'})")
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        inbrowser=False,
        show_api=False,
        share=share_flag,
        max_threads=40,
    )
