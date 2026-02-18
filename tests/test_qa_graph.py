import unittest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fabric.agents.qa_graph import EvidenceItem, EvidencePack, run_qa_graph, run_linear_qa
from fabric.agents.rag_agent import (
    BlockSpec,
    DirectAnswerBlock,
    DirectAnswerBullet,
    EvidenceAuditBlock,
    QuestionPlan,
)


def _plan():
    return QuestionPlan(
        intent="fact_lookup",
        required_blocks=[BlockSpec(type="direct_answer")],
        allowed_rank_entity_types=["candidate"],
        required_signals=[],
        retrieval_queries=["test query"],
        exclude_patterns=[],
        abstain_conditions=[],
    )


def _evidence_pack():
    items = [
        EvidenceItem(
            evidence_id="E1",
            text="EntityA improves EntityB activity.",
            title="Paper 1",
            paper="paper-1",
            source_id="chunk-1",
            score=0.9,
        )
    ]
    return EvidencePack(
        items=items,
        citations=[{"id": 1, "paper": "paper-1", "source_id": "chunk-1", "source_ids": ["chunk-1"], "title": "Paper 1"}],
        evidence_to_citation={"E1": 1},
        retrieval={},
    )


class TestQAGraph(unittest.TestCase):
    def test_graph_equivalence_to_linear(self):
        plan = _plan()
        evidence_pack = _evidence_pack()
        blocks = [DirectAnswerBlock(type="direct_answer", bullets=[DirectAnswerBullet(text="Answer", citations=["E1"])])]
        config = {
            "use_llm": False,
            "use_claims_lite": False,
            "hooks": {
                "plan": lambda state: (plan, True, None, None),
                "retrieve": lambda state: evidence_pack,
                "compose": lambda state: blocks,
            },
        }
        graph_result = run_qa_graph("q", {}, config)
        linear_result = run_linear_qa("q", {}, config)
        self.assertEqual(graph_result["blocks"], linear_result["blocks"])

    def test_retry_behavior(self):
        plan = _plan()
        evidence_pack = _evidence_pack()
        invalid_blocks = [DirectAnswerBlock(type="direct_answer", bullets=[DirectAnswerBullet(text="No cite", citations=[])])]
        valid_blocks = [DirectAnswerBlock(type="direct_answer", bullets=[DirectAnswerBullet(text="With cite", citations=["E1"])])]
        config = {
            "use_llm": False,
            "use_claims_lite": False,
            "hooks": {
                "plan": lambda state: (plan, True, None, None),
                "retrieve": lambda state: evidence_pack,
                "compose": lambda state: invalid_blocks,
                "compose_retry": lambda state: valid_blocks,
            },
        }
        result, state = run_qa_graph("q", {}, config, return_state=True)
        self.assertEqual(state.retries_used, 1)
        self.assertEqual(result["blocks"], [block.model_dump() for block in valid_blocks])

    def test_abstain_behavior(self):
        plan = QuestionPlan(
            intent="fact_lookup",
            required_blocks=[BlockSpec(type="direct_answer")],
            allowed_rank_entity_types=["candidate"],
            required_signals=[],
            retrieval_queries=["test"],
            exclude_patterns=[],
            abstain_conditions=["no_evidence"],
        )
        empty_pack = EvidencePack(items=[], citations=[], evidence_to_citation={}, retrieval={})
        config = {
            "use_llm": False,
            "use_claims_lite": False,
            "hooks": {
                "plan": lambda state: (plan, True, None, None),
                "retrieve": lambda state: empty_pack,
            },
        }
        result, state = run_qa_graph("q", {}, config, return_state=True)
        self.assertTrue(state.abstain)
        self.assertIsInstance(state.blocks[0], EvidenceAuditBlock)
        self.assertEqual(result["blocks"][0]["type"], "evidence_audit")

    def test_claims_fallback(self):
        plan = _plan()
        evidence_pack = _evidence_pack()
        blocks = [DirectAnswerBlock(type="direct_answer", bullets=[DirectAnswerBullet(text="Answer", citations=["E1"])])]
        config = {
            "use_llm": False,
            "use_claims_lite": True,
            "hooks": {
                "plan": lambda state: (plan, True, None, None),
                "retrieve": lambda state: evidence_pack,
                "claims": lambda state: ([], {"raw": 0, "kept": 0}),
                "compose": lambda state: blocks,
            },
        }
        result, state = run_qa_graph("q", {}, config, return_state=True)
        self.assertTrue(state.fallback_used)
        self.assertEqual(result["blocks"], [block.model_dump() for block in blocks])


if __name__ == "__main__":
    unittest.main()
