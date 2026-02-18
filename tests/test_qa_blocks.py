import unittest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fabric.agents.rag_agent import (
    BlockSpec,
    QuestionPlan,
    DirectAnswerBlock,
    DirectAnswerBullet,
    RankedEntitiesBlock,
    RankedEntityItem,
    RankedEntityStats,
    EvidenceAuditBlock,
    validate_blocks,
    evaluate_abstention,
)


def _base_plan(intent="candidate_selection", abstain_conditions=None):
    return QuestionPlan(
        intent=intent,
        required_blocks=[BlockSpec(type="ranked_entities")],
        allowed_rank_entity_types=["candidate"],
        required_signals=["improves"],
        retrieval_queries=["petase thermostability"],
        exclude_patterns=["Received:"],
        abstain_conditions=abstain_conditions or [],
    )


class TestQABlocks(unittest.TestCase):
    def setUp(self):
        self.evidence_ids = {"E1", "E2", "E3"}

    def test_candidate_selection_ranked_or_audit(self):
        queries = [f"query_{i}" for i in range(20)]
        for idx, query in enumerate(queries):
            with self.subTest(query=query):
                plan = _base_plan()
                if idx % 2 == 0:
                    blocks = [
                        RankedEntitiesBlock(
                            type="ranked_entities",
                            entity_type="candidate",
                            items=[
                                RankedEntityItem(
                                    entity_id="cand-1",
                                    display_name="CandA",
                                    rationale="evidence=2, papers=1",
                                    supporting_evidence=["E1"],
                                    stats=RankedEntityStats(evidence_count=2, papers_count=1, contradiction=False),
                                )
                            ],
                        )
                    ]
                else:
                    blocks = [EvidenceAuditBlock(type="evidence_audit", what_is_available=[], what_is_missing=["missing"], how_to_fix=[])]
                valid, errors = validate_blocks(blocks, plan, self.evidence_ids)
                if isinstance(blocks[0], EvidenceAuditBlock):
                    self.assertFalse(errors)
                else:
                    self.assertTrue(valid)

    def test_direct_answer_requires_citations(self):
        plan = _base_plan(intent="fact_lookup")
        blocks = [DirectAnswerBlock(type="direct_answer", bullets=[DirectAnswerBullet(text="Answer without cite", citations=[])])]
        valid, errors = validate_blocks(blocks, plan, self.evidence_ids)
        self.assertFalse(valid)
        self.assertTrue(errors)

    def test_ranked_entities_requires_allowed_type(self):
        plan = _base_plan()
        blocks = [
            RankedEntitiesBlock(
                type="ranked_entities",
                entity_type="assay",
                items=[
                    RankedEntityItem(
                        entity_id="assay-1",
                        display_name="AssayX",
                        rationale="evidence=1",
                        supporting_evidence=["E1"],
                        stats=RankedEntityStats(evidence_count=1, papers_count=1, contradiction=False),
                    )
                ],
            )
        ]
        valid, errors = validate_blocks(blocks, plan, self.evidence_ids)
        self.assertFalse(valid)
        self.assertTrue(errors)

    def test_ranked_entities_missing_evidence(self):
        plan = _base_plan()
        blocks = [
            RankedEntitiesBlock(
                type="ranked_entities",
                entity_type="candidate",
                items=[
                    RankedEntityItem(
                        entity_id="cand-1",
                        display_name="CandA",
                        rationale="evidence=0",
                        supporting_evidence=[],
                        stats=RankedEntityStats(evidence_count=0, papers_count=0, contradiction=False),
                    )
                ],
            )
        ]
        valid, errors = validate_blocks(blocks, plan, self.evidence_ids)
        self.assertFalse(valid)
        self.assertTrue(errors)

    def test_abstain_condition_threshold(self):
        plan = _base_plan(abstain_conditions=["<2 ranked items with citations"])
        blocks = [
            RankedEntitiesBlock(
                type="ranked_entities",
                entity_type="candidate",
                items=[
                    RankedEntityItem(
                        entity_id="cand-1",
                        display_name="CandA",
                        rationale="evidence=1",
                        supporting_evidence=["E1"],
                        stats=RankedEntityStats(evidence_count=1, papers_count=1, contradiction=False),
                    )
                ],
            )
        ]
        abstain, reason = evaluate_abstention(plan, blocks, self.evidence_ids)
        self.assertTrue(abstain)
        self.assertIn("ranked_items<2", reason or "")

    def test_abstain_no_evidence(self):
        plan = _base_plan(abstain_conditions=["no_evidence"])
        blocks = [EvidenceAuditBlock(type="evidence_audit", what_is_available=[], what_is_missing=[], how_to_fix=[])]
        abstain, reason = evaluate_abstention(plan, blocks, set())
        self.assertTrue(abstain)
        self.assertEqual(reason, "no_evidence")

    def test_abstain_no_evidence_with_blocks(self):
        plan = _base_plan(intent="fact_lookup", abstain_conditions=["no_evidence"])
        blocks = [
            DirectAnswerBlock(
                type="direct_answer",
                bullets=[DirectAnswerBullet(text="Answer with missing evidence", citations=["E1"])],
            )
        ]
        abstain, reason = evaluate_abstention(plan, blocks, set())
        self.assertTrue(abstain)
        self.assertEqual(reason, "no_evidence")

    def test_definitional_bullet_without_citation(self):
        plan = _base_plan(intent="fact_lookup")
        blocks = [
            DirectAnswerBlock(
                type="direct_answer",
                bullets=[DirectAnswerBullet(text="Definition: X is defined as Y.", citations=[])],
            )
        ]
        valid, errors = validate_blocks(blocks, plan, self.evidence_ids)
        self.assertTrue(valid)
        self.assertFalse(errors)


if __name__ == "__main__":
    unittest.main()
