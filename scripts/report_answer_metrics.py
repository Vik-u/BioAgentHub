#!/usr/bin/env python3
"""Generate a metrics table for a list of PETase research questions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.rl_rag_agent import run_agent  # noqa: E402


DEFAULT_QUESTIONS = [
    "What mutations improve PETase thermostability?",
    "Which engineered PETases target semi-crystalline PET?",
    "At what temperatures does ThermoPETase remain active?",
]


def load_questions(path: Path | None) -> List[str]:
    if path:
        raw = path.read_text().splitlines()
        return [line.strip() for line in raw if line.strip()]
    return DEFAULT_QUESTIONS.copy()


def run_benchmark(
    questions: List[str],
    mode: str = "llm",
    seed: int = 7,
    policy_path: Path | None = None,
):
    rows: List[dict] = []
    policy_model = None
    if policy_path:
        from stable_baselines3 import PPO

        policy_model = PPO.load(str(policy_path))

    for q in questions:
        result = run_agent(q, use_llm=(mode == "llm"), seed=seed, policy_model=policy_model)
        metrics = result.get("metrics") or {}
        rows.append(
            {
                "question": q,
                "faiss_avg": metrics.get("faiss_avg"),
                "kg_conf_avg": metrics.get("kg_conf_avg"),
                "rl_reward_sum": metrics.get("rl_reward_sum"),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--questions-file",
        type=Path,
        help="Optional text file with one question per line.",
    )
    parser.add_argument(
        "--mode",
        choices=["plain", "llm"],
        default="llm",
        help="plain = RL-only summarizer, llm = RL + GPT-OSS",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--policy", type=Path, help="Optional PPO policy to control retrieval actions.")
    args = parser.parse_args()

    questions = load_questions(args.questions_file)
    rows = run_benchmark(questions, mode=args.mode, seed=args.seed, policy_path=args.policy)

    print(f"Mode: {args.mode}\n")
    header = f"{'Question':60} | {'FAISS avg':>10} | {'KG conf avg':>11} | {'RL reward sum':>13}"
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['question'][:60]:60} | "
            f"{format_metric(row['faiss_avg']):>10} | "
            f"{format_metric(row['kg_conf_avg']):>11} | "
            f"{format_metric(row['rl_reward_sum']):>13}"
        )

    print(
        "\nMetric definitions:\n"
        "- FAISS avg: mean cosine similarity of retrieved evidence vectors.\n"
        "- KG conf avg: mean heuristic confidence from knowledge-graph edges.\n"
        "- RL reward sum: cumulative reward given to the retrieval policy during the run."
    )


def format_metric(value):
    if value is None:
        return "n/a"
    return f"{value:.3f}"


if __name__ == "__main__":
    main()
