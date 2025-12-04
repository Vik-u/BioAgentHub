#!/usr/bin/env python3
"""Simple CLI interface for the PETase RL agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.rl_rag_agent import run_agent  # noqa: E402

try:
    from stable_baselines3 import PPO
except Exception:  # pragma: no cover - optional
    PPO = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with the PETase RL/RAG agent from the terminal.")
    parser.add_argument(
        "--mode",
        choices=["plain", "llm"],
        default="llm",
        help="plain = RL-only summaries; llm = RL + GPT-OSS summarizer.",
    )
    parser.add_argument("--seed", type=int, default=7, help="Random seed for reproducibility.")
    parser.add_argument("--policy", type=Path, help="Optional PPO policy path for RL control.")
    args = parser.parse_args()

    use_llm = args.mode == "llm"
    policy_model = None
    if args.policy:
        if PPO is None:
            raise RuntimeError("stable-baselines3 not installed; cannot load PPO policy.")
        policy_model = PPO.load(str(args.policy))

    print("PETase Research CLI")
    print("-------------------")
    print(f"Mode: {'RL + GPT-OSS' if use_llm else 'RL only'}  |  Seed: {args.seed}")
    print("Type a question and press Enter, or 'quit' to exit.\n")

    history: list[dict[str, str]] = []

    while True:
        try:
            question = input("Q> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not question:
            continue
        if question.lower() in {"quit", "exit"}:
            print("Bye!")
            break

        context = build_context(history)
        composite_question = f"{context}Current question: {question}" if context else question

        print("...thinking...")
        result = run_agent(composite_question, use_llm=use_llm, seed=args.seed, policy_model=policy_model)
        print("\nA>\n" + result["answer"] + "\n")

        citations = result.get("citations") or []
        if citations:
            print("Citations:")
            for cite in citations:
                print(f"  [{cite['id']}] {cite['title']} ({cite['paper']})")
            print()

        metrics = result.get("metrics") or {}
        print("Metrics:")
        print(f"  FAISS avg score   : {format_metric(metrics.get('faiss_avg'))}")
        print(f"  KG confidence avg : {format_metric(metrics.get('kg_conf_avg'))}")
        print(f"  RL reward sum     : {format_metric(metrics.get('rl_reward_sum'))}")

        meta = {"steps": result["trajectory"], "rewards": result["rewards"], "mode": args.mode}
        print("meta:", json.dumps(meta, indent=2, ensure_ascii=False))
        print("-" * 60)
        history.insert(0, {"question": question, "answer": result["answer"]})


def build_context(history, max_turns=3):
    if not history:
        return ""
    recent = history[:max_turns]
    lines = ["Previous conversation:"]
    for idx, turn in enumerate(reversed(recent), start=1):
        lines.append(f"{idx}. Q: {turn['question']}")
        lines.append(f"   A: {turn['answer']}")
    lines.append("")  # blank line before new question
    return "\n".join(lines)


def format_metric(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


if __name__ == "__main__":
    main()
