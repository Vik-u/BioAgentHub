#!/usr/bin/env python3
"""Standalone Gradio app for the methodology-driven PETase protocol agent."""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.protocol_agent_v2 import run_protocol_agent_v2  # noqa: E402
from agents.instrument_protocol_agent_v2 import run_instrument_protocol_v2  # noqa: E402


def handler(question: str, mode: str):
    question = (question or "").strip()
    if not question:
        return "Please enter a question."
    try:
        if mode.strip().lower().startswith("biofoundry"):
            return run_instrument_protocol_v2(question)
        return run_protocol_agent_v2(question)
    except Exception as exc:  # pragma: no cover
        return f"Protocol generation error: {exc}"


with gr.Blocks(title="PETase Protocol Workbench") as demo:
    gr.Markdown(
        "# PETase Protocol Workbench\n"
        "- **Methodology-driven**: Uses full-text experimental sections from the PETase papers.\n"
        "- **Biofoundry instrument-constrained**: Uses the instrument manuals + methodology KG."
    )
    question = gr.Textbox(label="Protocol Request", lines=4)
    mode = gr.Radio(
        choices=["Methodology-driven (papers)", "Biofoundry instrument-constrained"],
        value="Methodology-driven (papers)",
        label="Mode",
    )
    btn = gr.Button("Generate Protocol")
    output = gr.Markdown()
    btn.click(handler, inputs=[question, mode], outputs=output)


if __name__ == "__main__":  # pragma: no cover
    host = os.environ.get("GRADIO_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("GRADIO_SERVER_PORT", "7863"))
    demo.launch(server_name=host, server_port=port)
