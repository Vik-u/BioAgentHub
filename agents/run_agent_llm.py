#!/usr/bin/env python3
"""Convenience CLI for running the RL agent with the LLM summarizer."""

from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import typer

from agents.rl_rag_agent import run_agent

app = typer.Typer(add_completion=False)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Natural-language question for the PETase agent (LLM mode)."),
    seed: int = typer.Option(7, help="Random seed for reproducibility."),
) -> None:
    result = run_agent(question, use_llm=True, seed=seed)
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    app()
