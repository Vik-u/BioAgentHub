#!/usr/bin/env python3
"""Train a PPO retrieval policy over the PETase question set."""

from __future__ import annotations

import argparse
from pathlib import Path

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stable_baselines3 import PPO

from agents.ppo_env import RetrievalGymEnv, load_questions

ROOT = PROJECT_ROOT
DEFAULT_MODEL_PATH = ROOT / "models" / "ppo_policy"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions-file", type=Path, help="Text file with one question per line.")
    parser.add_argument("--timesteps", type=int, default=10000)
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--use-llm", action="store_true", help="Allow the policy to run the LLM summarizer during training.")
    args = parser.parse_args()

    questions = load_questions(args.questions_file)
    env = RetrievalGymEnv(questions, use_llm=args.use_llm)

    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=args.timesteps)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(args.output))
    print(f"Saved PPO policy to {args.output}")


if __name__ == "__main__":
    main()
