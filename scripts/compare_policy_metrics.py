
#!/usr/bin/env python3
"""Compare heuristic, PPO, and RLHF-style policies across an extended benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stable_baselines3 import PPO  # noqa: E402
from agents.rlhf_policy import PreferenceGuidedPolicy  # noqa: E402
from agents.rl_rag_agent import run_agent  # noqa: E402
from policy_variants import POLICY_DESCRIPTORS, PolicyDescriptor  # noqa: E402


def load_questions(path: Path) -> list[str]:
    lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if len(lines) < 10:
        raise ValueError("Benchmark needs at least 10 questions; got %d" % len(lines))
    return lines


def format_metric(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def load_policy_model(descriptor: PolicyDescriptor):
    if descriptor.policy_type == "heuristic":
        return None
    if descriptor.policy_type == "rlhf":
        return PreferenceGuidedPolicy()
    if descriptor.policy_type == "ppo":
        checkpoint = descriptor.checkpoint or (PROJECT_ROOT / "models" / "ppo_policy.zip")
        if not checkpoint.exists():
            raise FileNotFoundError(f"Missing PPO checkpoint: {checkpoint}")
        return PPO.load(str(checkpoint))
    raise ValueError(f"Unsupported policy type: {descriptor.policy_type}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--questions",
        type=Path,
        default=PROJECT_ROOT / "benchmark_questions_extended.txt",
        help="Text file with >=25 PETase questions.",
    )
    parser.add_argument(
        "--output-table",
        type=Path,
        default=PROJECT_ROOT / "logs" / "policy_metrics.md",
        help="Markdown file summarizing average metrics per policy.",
    )
    parser.add_argument(
        "--output-details",
        type=Path,
        default=PROJECT_ROOT / "logs" / "policy_benchmark_outputs.jsonl",
        help="JSONL with per-question answers/metrics for each policy.",
    )
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    args.output_table.parent.mkdir(parents=True, exist_ok=True)
    args.output_details.parent.mkdir(parents=True, exist_ok=True)

    questions = load_questions(args.questions)

    table_rows = []
    with args.output_details.open("w", encoding="utf-8") as detail_f:
        for descriptor in POLICY_DESCRIPTORS:
            use_llm = descriptor.mode.lower() == "llm"
            faiss_scores = []
            kg_scores = []
            rewards = []

            for question in questions:
                policy_model = load_policy_model(descriptor)
                result = run_agent(
                    question,
                    use_llm=use_llm,
                    seed=descriptor.seed,
                    policy_model=policy_model,
                )
                metrics = result.get("metrics") or {}
                faiss_scores.append(metrics.get("faiss_avg"))
                kg_scores.append(metrics.get("kg_conf_avg"))
                rewards.append(metrics.get("rl_reward_sum"))

                detail_f.write(
                    json.dumps(
                        {
                            "policy": descriptor.key,
                            "question": question,
                            "answer": result.get("answer", ""),
                            "metrics": metrics,
                            "citations": result.get("citations"),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

            table_rows.append(
                {
                    "policy": descriptor.label,
                    "mode": descriptor.mode,
                    "description": descriptor.description,
                    "faiss": mean([s for s in faiss_scores if isinstance(s, (int, float))]) if any(s is not None for s in faiss_scores) else None,
                    "kg": mean([s for s in kg_scores if isinstance(s, (int, float))]) if any(s is not None for s in kg_scores) else None,
                    "reward": mean([s for s in rewards if isinstance(s, (int, float))]) if any(s is not None for s in rewards) else None,
                }
            )

    header = "| Policy | Mode | Avg FAISS | Avg KG conf | Avg RL reward | Description |"
    separator = "|---|---|---|---|---|---|"
    lines = [header, separator]
    for row in table_rows:
        lines.append(
            "| {policy} | {mode} | {faiss} | {kg} | {reward} | {description} |".format(
                policy=row["policy"],
                mode=row["mode"],
                faiss=format_metric(row["faiss"]),
                kg=format_metric(row["kg"]),
                reward=format_metric(row["reward"]),
                description=row["description"],
            )
        )

    lines.append(
        "\n**Metric notes**: FAISS avg measures semantic similarity of retrieved evidence; KG conf avg reflects heuristic confidence of graph edges (0–1); RL reward is the cumulative reward assigned to the retrieval policy per episode."
    )
    args.output_table.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote summary table to {args.output_table}")
    print(f"Detailed outputs saved to {args.output_details}")


if __name__ == "__main__":
    main()
