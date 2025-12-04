#!/usr/bin/env python3
"""
Unified interactive chatbot for QA and protocol generation across workspaces.

- Workspace-aware: point to any workspace under workspaces/ or a custom path.
- Continuous chat for QA (LLM or plain RL summarizer).
- Protocol modes:
    * relaxed/methodology-driven (papers)
    * standard (legacy PETase protocol agent)
    * biofoundry instrument-constrained (v2, uses InstrumentGraph)
    * legacy biofoundry-constrained (v1)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.rl_rag_agent import run_agent  # noqa: E402
from agents.protocol_agent import run_protocol_agent  # noqa: E402
from agents.protocol_agent_v2 import run_protocol_agent_v2  # noqa: E402
from agents.instrument_protocol_agent import run_instrument_protocol  # noqa: E402
from agents.instrument_protocol_agent_v2 import run_instrument_protocol_v2  # noqa: E402
from services import retrieval_service  # noqa: E402


def list_workspaces(base: Path) -> List[Path]:
    if not base.exists():
        return []
    return sorted([p for p in base.iterdir() if p.is_dir()])


def choose_workspace(path: Optional[str]) -> Path:
    base = PROJECT_ROOT / "workspaces"
    candidates = list_workspaces(base)
    if path:
        chosen = Path(path).expanduser().resolve()
        if not chosen.exists():
            raise SystemExit(f"Workspace not found: {chosen}")
        return chosen
    if not candidates:
        raise SystemExit("No workspaces found. Run scripts/build_topic_workspaces.py first.")
    print("Available workspaces:")
    for idx, ws in enumerate(candidates, start=1):
        print(f" {idx}. {ws.name}")
    raw = input(f"Select workspace [1-{len(candidates)}]: ").strip()
    if not raw.isdigit() or not (1 <= int(raw) <= len(candidates)):
        raise SystemExit("Invalid selection.")
    return candidates[int(raw) - 1].resolve()


def set_workspace_env(workspace: Path, alias_expansion: bool) -> None:
    os.environ["WORKSPACE_ROOT"] = str(workspace)
    os.environ["USE_ALIAS_EXPANSION"] = "1" if alias_expansion else "0"
    retrieval_service.get_backend.cache_clear()


def qa_loop(use_llm: bool) -> None:
    print(f"\nQA mode (LLM={'on' if use_llm else 'off'})")
    print("Type your question, or 'quit' to exit.\n")
    while True:
        try:
            q = input("Q> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break
        if q.lower() in {"quit", "exit"}:
            print("Bye!")
            break
        if not q:
            continue
        print("...thinking...")
        result = run_agent(q, use_llm=use_llm, policy_model=None)
        print("\nA>\n" + result["answer"] + "\n")
        metrics = result.get("metrics") or {}
        print(
            f"Metrics: FAISS={metrics.get('faiss_avg','n/a')} "
            f"KG={metrics.get('kg_conf_avg','n/a')} "
            f"Reward={metrics.get('rl_reward_sum','n/a')}\n"
        )


def protocol_loop(mode: str, max_instruments: int) -> None:
    print(f"\nProtocol mode: {mode}")
    print("Type your request, or 'quit' to exit.\n")
    while True:
        try:
            prompt = input("Proto> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break
        if prompt.lower() in {"quit", "exit"}:
            print("Bye!")
            break
        if not prompt:
            continue
        print("...thinking...")
        if mode == "relaxed" or mode == "methodology":
            answer = run_protocol_agent_v2(prompt)
        elif mode == "standard":
            answer = run_protocol_agent(prompt)
        elif mode == "biofoundry":
            answer = run_instrument_protocol_v2(prompt)
        elif mode == "biofoundry-legacy":
            answer = run_instrument_protocol(prompt, top_n=max_instruments)
        else:
            answer = "Unsupported protocol mode."
        print("\n" + answer + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="Workspace path (default: prompt to choose from workspaces/).")
    parser.add_argument("--mode", choices=["qa", "protocol"], default="qa")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM summarizer for QA (default off).")
    parser.add_argument("--alias-expansion", action="store_true", default=False, help="Enable PETase alias expansion.")
    parser.add_argument(
        "--protocol-mode",
        choices=["relaxed", "methodology", "standard", "biofoundry", "biofoundry-legacy"],
        default="relaxed",
        help="Protocol generation strategy.",
    )
    parser.add_argument("--max-instruments", type=int, default=8, help="Instrument cap for legacy biofoundry mode.")
    args = parser.parse_args()

    workspace = choose_workspace(str(args.workspace) if args.workspace else None)
    set_workspace_env(workspace, alias_expansion=args.alias_expansion)
    print(f"Workspace: {workspace}")

    if args.mode == "qa":
        qa_loop(use_llm=args.use_llm)
    else:
        protocol_loop(mode=args.protocol_mode, max_instruments=args.max_instruments)


if __name__ == "__main__":
    main()
