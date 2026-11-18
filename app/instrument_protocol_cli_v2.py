#!/usr/bin/env python3
"""CLI for the instrument-aware protocol agent (v2)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fabric.agents.instrument_protocol_agent_v2 import run_instrument_protocol_v2  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="Protocol question/goal.")
    parser.add_argument("--workspace", type=Path, help="Optional workspace root (e.g., workspaces/petase).")
    parser.add_argument(
        "--enable-instruments",
        dest="enable_instruments",
        action="store_true",
        help="Enable InstrumentGraph retrieval (default).",
    )
    parser.add_argument(
        "--disable-instruments",
        dest="enable_instruments",
        action="store_false",
        help="Disable InstrumentGraph retrieval.",
    )
    parser.set_defaults(enable_instruments=True)
    parser.add_argument("--output", type=Path, help="Optional file to save Markdown output.")
    args = parser.parse_args()

    if args.workspace:
        os.environ["WORKSPACE_ROOT"] = str(args.workspace.resolve())
    os.environ["BIOAGENT_USE_INSTRUMENTS"] = "1" if args.enable_instruments else "0"

    try:
        answer = run_instrument_protocol_v2(args.question)
    except Exception as exc:
        print(f"Protocol generation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(answer)
        print(f"Protocol saved to {args.output}")
    print("\n" + answer + "\n")


if __name__ == "__main__":
    main()
