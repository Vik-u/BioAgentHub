#!/usr/bin/env python3
"""CLI for the full-text instrument-constrained PETase protocol generator."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.instrument_protocol_agent_v2 import run_instrument_protocol_v2  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="Protocol request / objective.")
    parser.add_argument("--output", type=Path, help="Optional path to save the Markdown output.")
    args = parser.parse_args()

    answer = run_instrument_protocol_v2(args.question)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(answer)
        print(f"Protocol saved to {args.output}")
    print("\n" + answer + "\n")


if __name__ == "__main__":
    main()
