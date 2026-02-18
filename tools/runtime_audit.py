#!/usr/bin/env python3
"""Runtime audit: validate CLI scripts respond to --help without executing pipelines."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "docs" / "runtime_audit.md"

SCRIPTS = [
    "app/hub_cli.py",
    "app/gradio_chatbot.py",
    "app/qa_chat_langgraph.py",
    "app/protocol_agent_cli_v2.py",
    "app/instrument_protocol_cli_v2.py",
    "forge/run_forge.py",
    "forge/scripts/generic_run_pipeline.py",
    "forge/scripts/build_methodology_edge_store.py",
    "forge/scripts/build_methodology_kg.py",
    "forge/scripts/build_methodology_vector_store.py",
    "forge/scripts/build_vector_store.py",
    "forge/scripts/build_topic_full.py",
    "forge/scripts/build_graph_store.py",
    "forge/scripts/generic_build_vector_store.py",
    "forge/scripts/build_topic_methodology.py",
    "forge/scripts/build_timeline_graph.py",
    "forge/agents/kg_schema_agent.py",
    "forge/scripts/extract_methodology_full.py",
    "forge/scripts/extract_corpus.py",
    "forge/scripts/build_kg_edges.py",
    "forge/scripts/build_topic_workspaces.py",
    "forge/scripts/rebuild_vector_store_embeddings.py",
    "forge/scripts/generic_extract_corpus.py",
    "forge/scripts/run_structured_audit.py",
    "forge/scripts/build_structured_facts.py",
    "forge/scripts/extract_pdf_artifacts.py",
    "fabric/agents/multi_agent_orchestrator.py",
    "fabric/agents/run_agent_plain.py",
    "fabric/agents/timeline_gap_agent.py",
    "fabric/agents/run_agent_llm.py",
    "fabric/agents/top_candidates_report.py",
    "fabric/agents/biofoundry_protocol_orchestrator.py",
    "fabric/agents/timeline_summarizer.py",
    "fabric/agents/hypothesis_planner.py",
    "fabric/agents/biofoundry_protocol_agent.py",
    "fabric/agents/rag_agent.py",
    "test_hmmm/run_demos.py",
]

EXCLUDED = {
    "test_hmmm/run_demos.py": "No CLI parser; running would execute full demos.",
}


def run_help(script: str) -> Dict[str, str]:
    if script in EXCLUDED:
        return {"script": script, "status": "excluded", "reason": EXCLUDED[script]}
    path = PROJECT_ROOT / script
    if not path.exists():
        return {"script": script, "status": "missing"}
    try:
        result = subprocess.run(
            [sys.executable, str(path), "--help"],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return {"script": script, "status": "timeout"}
    if result.returncode == 0:
        return {"script": script, "status": "ok"}
    return {
        "script": script,
        "status": f"exit {result.returncode}",
        "stderr": result.stderr.strip(),
    }


def write_report(results: List[Dict[str, str]]) -> None:
    ok = [r for r in results if r["status"] == "ok"]
    excluded = [r for r in results if r["status"] == "excluded"]
    fail = [r for r in results if r["status"] not in ("ok", "excluded")]
    lines = [
        "# Runtime Audit (CLI --help)",
        "",
        "This audit checks that each script responds to `--help` without executing the full pipeline.",
        "",
        f"Total scripts: {len(results)}",
        f"OK: {len(ok)}",
        f"Excluded: {len(excluded)}",
        f"Failures: {len(fail)}",
        "",
        "## Results",
    ]
    for r in results:
        status = r["status"]
        lines.append(f"- `{r['script']}` -> {status}")
        if status == "excluded" and r.get("reason"):
            lines.append(f"  reason: {r['reason']}")
        if status not in ("ok", "missing", "excluded") and r.get("stderr"):
            lines.append(f"  stderr: {r['stderr']}")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    results = [run_help(script) for script in SCRIPTS]
    write_report(results)
    failures = [r for r in results if r["status"] not in ("ok", "excluded")]
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
