import unittest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fabric.agents.rag_agent import (
    BlockSpec,
    EvidenceAuditBlock,
    QuestionPlan,
    render_blocks_text,
    render_helpful_answer,
)


def _plan():
    return QuestionPlan(
        intent="fact_lookup",
        required_blocks=[BlockSpec(type="direct_answer")],
        allowed_rank_entity_types=["candidate"],
        required_signals=[],
        retrieval_queries=["test"],
        exclude_patterns=[],
        abstain_conditions=[],
    )


class TestAnswerMode(unittest.TestCase):
    def test_helpful_starts_with_quick_answer(self):
        answer, _ = render_helpful_answer(
            "What is PETase?",
            _plan(),
            {},
            [],
            None,
            use_llm=False,
            temperature=None,
            session_id="s1",
        )
        self.assertTrue(answer.startswith("Quick Answer"))

    def test_helpful_not_evidence_audit_only(self):
        answer, _ = render_helpful_answer(
            "What is PETase?",
            _plan(),
            {},
            [],
            None,
            use_llm=False,
            temperature=None,
            session_id="s1",
        )
        self.assertNotIn("Evidence audit:", answer)

    def test_what_i_couldnt_verify_max_three(self):
        answer, _ = render_helpful_answer(
            "What is PETase?",
            _plan(),
            {},
            [],
            None,
            use_llm=False,
            temperature=None,
            session_id="s1",
        )
        lines = answer.splitlines()
        start = lines.index("What I couldn't verify from your corpus")
        end = lines.index("Next steps") if "Next steps" in lines else len(lines)
        bullet_lines = [line for line in lines[start + 1 : end] if line.startswith("- ")]
        self.assertLessEqual(len(bullet_lines), 3)

    def test_grounded_bullets_include_citations(self):
        evidence_items = [
            {"evidence_id": "E1", "text": "EntityA improves EntityB activity."}
        ]
        answer, _ = render_helpful_answer(
            "EntityA improves EntityB activity",
            _plan(),
            {},
            evidence_items,
            None,
            use_llm=False,
            temperature=None,
            session_id="s1",
        )
        self.assertIn("[Grounded]", answer)
        self.assertIn("[E1]", answer)

    def test_strict_mode_allows_evidence_audit(self):
        block = EvidenceAuditBlock(type="evidence_audit", what_is_available=[], what_is_missing=["missing"], how_to_fix=[])
        text = render_blocks_text([block], {}, [])
        self.assertIn("Evidence audit:", text)


if __name__ == "__main__":
    unittest.main()
