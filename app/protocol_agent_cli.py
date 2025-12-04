#!/usr/bin/env python3
"""CLI for the experimental protocol LangChain/LangGraph agent."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.protocol_agent import run_protocol_agent  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="Experimental planning question")
    parser.add_argument("--output", type=Path, help="Optional path to save markdown output.")
    args = parser.parse_args()

    answer = run_protocol_agent(args.question)
    if args.output:
        args.output.write_text(answer)
        print(f"Protocol saved to {args.output}")
    else:
        print("\n" + answer + "\n")


if __name__ == "__main__":
    main()
