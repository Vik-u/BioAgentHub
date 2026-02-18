#!/usr/bin/env python3
"""
Multi-agent orchestrator (KG-first) that combines:
- QA (KG + text) with LLM summarization
- Timeline/KG gap summary
- Protocol generation (methodology-driven)

Usage:
  python agents/multi_agent_orchestrator.py --workspace workspaces/petase --query "How to benchmark FAST-PETase mutations?"
"""

from __future__ import annotations

import argparse
import os
import json
import sys
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents import rag_agent  # noqa: E402
from agents.timeline_gap_agent import summarize_workspace  # noqa: E402
from agents.protocol_agent_v2 import run_protocol_agent_v2  # noqa: E402
from agents import hypothesis_planner  # noqa: E402


def ensure_workspace_env(workspace: Path, use_alias_expansion: bool) -> None:
    os.environ["WORKSPACE_ROOT"] = str(workspace.resolve())
    os.environ["USE_ALIAS_EXPANSION"] = "1" if use_alias_expansion else "0"


def run_multi_agent(query: str, workspace: Path, use_alias_expansion: bool) -> Dict[str, Any]:
    ensure_workspace_env(workspace, use_alias_expansion)

    # QA agent (KG-first; will fail if KG missing unless vector-only env is set)
    qa_result = rag_agent.run_agent(query, use_llm=True)

    # Timeline + KG gap summary
    gap_summary = summarize_workspace(workspace)

    # Hypotheses and planners
    hypotheses = hypothesis_planner.generate_hypotheses(query, gap_summary)
    comp_plan = hypothesis_planner.computational_plan(query)
    exp_plan = hypothesis_planner.experimental_plan(query)
    merged_plan = hypothesis_planner.arbiter(hypotheses, comp_plan, exp_plan)

    # Protocol suggestion (methodology template)
    protocol_text = run_protocol_agent_v2(query)

    return {
        "workspace": str(workspace),
        "qa": {
            "answer": qa_result.get("answer"),
            "metrics": qa_result.get("metrics"),
            "trajectory": qa_result.get("trajectory"),
        },
        "gaps": gap_summary,
        "hypotheses": hypotheses,
        "computational_plan": comp_plan,
        "experimental_plan": exp_plan,
        "merged_plan": merged_plan,
        "protocol": protocol_text,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace with KG + timeline.")
    parser.add_argument("--query", required=True, help="Research question or task.")
    parser.add_argument(
        "--alias-expansion",
        action="store_true",
        default=False,
        help="Enable alias expansion (PETase-specific).",
    )
    args = parser.parse_args()

    result = run_multi_agent(args.query, args.workspace, args.alias_expansion)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
