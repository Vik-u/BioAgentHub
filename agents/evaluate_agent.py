#!/usr/bin/env python3
"""Lightweight evaluation harness for the PETase RL agent."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import List, Sequence

import typer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.rl_rag_agent import run_agent, DEFAULT_USE_LLM  # noqa: E402

DEFAULT_DATASET: Sequence[dict] = [
    {
        "question": "What mutations improve PETase thermostability?",
        "keywords": ["N233K", "R224Q", "S121E", "T140D"],
    },
    {
        "question": "Which engineered PETases target semi-crystalline PET?",
        "keywords": ["FAST-PETase", "DuraPETase", "LC-Cutinase"],
    },
    {
        "question": "At what temperatures does ThermoPETase remain active?",
        "keywords": ["ThermoPETase", "60", "70"],
    },
]

LOG_PATH = PROJECT_ROOT / "logs" / "eval_runs.jsonl"

app = typer.Typer(add_completion=False)


def evaluate(dataset: Sequence[dict], use_llm: bool) -> dict:
    rows: List[dict] = []
    for item in dataset:
        result = run_agent(item["question"], use_llm=use_llm)
        answer = result["answer"]
        tokens = answer.lower()
        hits = sum(1 for keyword in item["keywords"] if keyword.lower() in tokens)
        coverage = hits / max(len(item["keywords"]), 1)
        rows.append(
            {
                "question": item["question"],
                "keywords": item["keywords"],
                "answer": answer,
                "hits": hits,
                "coverage": coverage,
                "use_llm": use_llm,
            }
        )
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(rows[-1], ensure_ascii=False) + "\n")
    return {
        "use_llm": use_llm,
        "mean_coverage": mean(row["coverage"] for row in rows),
        "rows": rows,
    }


@app.command()
def run(
    dataset_path: Path = typer.Option(
        None,
        help="Optional JSON file containing a list of {question, keywords} entries.",
    ),
    use_llm: bool = typer.Option(
        DEFAULT_USE_LLM,
        "--use-llm/--no-llm",
        help="Toggle the local LLM summarizer during evaluation.",
    ),
) -> None:
    """Evaluate the RL agent on a small keyword-matching benchmark."""
    if dataset_path:
        dataset = json.loads(dataset_path.read_text())
    else:
        dataset = DEFAULT_DATASET
    metrics = evaluate(dataset, use_llm=use_llm)
    typer.echo(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    app()
