#!/usr/bin/env python3
"""CLI entrypoint for instrument-constrained PETase protocols."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.instrument_protocol_agent import run_instrument_protocol  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="Protocol request to answer.")
    parser.add_argument("--max-instruments", type=int, default=8, help="Number of instruments to surface.")
    parser.add_argument("--output", type=Path, help="Optional path to save the Markdown output.")
    args = parser.parse_args()

    response = run_instrument_protocol(args.question, top_n=args.max_instruments)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(response)
        print(f"Protocol saved to {args.output}")
    print("\n" + response + "\n")


if __name__ == "__main__":
    main()
