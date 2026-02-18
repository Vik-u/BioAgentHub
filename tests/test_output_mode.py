import unittest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fabric.agents.qa_graph import EvidencePack, run_qa_graph
from fabric.agents.rag_agent import BlockSpec, EvidenceAuditBlock, QuestionPlan


def _plan():
    return QuestionPlan(
        intent="fact_lookup",
        required_blocks=[BlockSpec(type="direct_answer")],
        allowed_rank_entity_types=["candidate"],
        required_signals=[],
        retrieval_queries=["test"],
        exclude_patterns=[],
        abstain_conditions=["no_evidence"],
    )


class TestOutputMode(unittest.TestCase):
    def test_protocol_mode_never_evidence_audit(self):
        config = {
            "use_llm": False,
            "output_mode": "protocol",
            "hooks": {
                "plan": lambda state: (_plan(), True, None, None),
            },
        }
        result, state = run_qa_graph("q", {}, config, return_state=True)
        self.assertNotIn("evidence_audit", result.get("answer", "").lower())
        protocol = result.get("protocol", {})
        self.assertTrue(protocol)
        self.assertGreaterEqual(len(protocol.get("ordered_modules", [])), 1)

    def test_answer_helpful_never_evidence_audit_only(self):
        empty_pack = EvidencePack(items=[], citations=[], evidence_to_citation={}, retrieval={})
        config = {
            "use_llm": False,
            "output_mode": "answer_helpful",
            "hooks": {
                "plan": lambda state: (_plan(), True, None, None),
                "retrieve": lambda state: empty_pack,
            },
        }
        result = run_qa_graph("q", {}, config)
        self.assertTrue(result["answer"].startswith("Quick Answer"))
        self.assertNotIn("Evidence audit", result["answer"])

    def test_answer_strict_allows_evidence_audit(self):
        plan = _plan()
        empty_pack = EvidencePack(items=[], citations=[], evidence_to_citation={}, retrieval={})
        config = {
            "use_llm": False,
            "output_mode": "answer_strict",
            "hooks": {
                "plan": lambda state: (plan, True, None, None),
                "retrieve": lambda state: empty_pack,
                "compose": lambda state: [EvidenceAuditBlock(type="evidence_audit", what_is_available=[], what_is_missing=["missing"], how_to_fix=[])],
            },
        }
        result = run_qa_graph("q", {}, config)
        self.assertIn("Evidence audit", result["answer"])


if __name__ == "__main__":
    unittest.main()
