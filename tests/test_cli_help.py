import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

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
]

EXCLUDED = {
    "test_hmmm/run_demos.py": "No CLI parser; running would execute full demos.",
}


class TestCliHelp(unittest.TestCase):
    def test_scripts_help(self):
        failures = []
        for rel in SCRIPTS:
            path = PROJECT_ROOT / rel
            if not path.exists():
                failures.append(f"missing: {rel}")
                continue
            result = subprocess.run(
                [sys.executable, str(path), "--help"],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode != 0:
                failures.append(f"{rel} -> exit {result.returncode}: {result.stderr.strip()}")
        for rel in EXCLUDED:
            path = PROJECT_ROOT / rel
            if not path.exists():
                failures.append(f"missing: {rel}")
        if failures:
            self.fail("\n".join(failures))


if __name__ == "__main__":
    unittest.main()
