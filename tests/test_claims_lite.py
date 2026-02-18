import unittest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fabric.agents.rag_agent import (
    BlockSpec,
    QuestionPlan,
    Claim,
    ClaimEntity,
    RankedEntitiesBlock,
    RankedEntityItem,
    RankedEntityStats,
    DirectAnswerBlock,
    DirectAnswerBullet,
    select_claim_ids_for_blocks,
    claims_are_sufficient,
    _qualifiers_supported,
    validate_blocks,
)


def _plan():
    return QuestionPlan(
        intent="candidate_selection",
        required_blocks=[BlockSpec(type="ranked_entities")],
        allowed_rank_entity_types=["candidate"],
        required_signals=[],
        retrieval_queries=["test"],
        exclude_patterns=[],
        abstain_conditions=[],
    )


def _claim(claim_id="C1", evidence_id="E1", relation="improves", metric=None):
    qualifiers = {}
    if metric:
        qualifiers["metric"] = metric
    return Claim(
        claim_id=claim_id,
        topic="test",
        paper_id="paper-1",
        evidence_id=evidence_id,
        subject=ClaimEntity(entity_id="ent-1", text="EntityA"),
        relation=relation,
        object=ClaimEntity(entity_id="ent-2", text="EntityB"),
        qualifiers=qualifiers,
        confidence=0.9,
        canonicalized=True,
    )


class TestClaimsLite(unittest.TestCase):
    def test_claims_selected_by_block_citations(self):
        claims = [_claim("C1", "E1"), _claim("C2", "E2")]
        blocks = [
            RankedEntitiesBlock(
                type="ranked_entities",
                entity_type="candidate",
                items=[
                    RankedEntityItem(
                        entity_id="cand-1",
                        display_name="CandA",
                        rationale="supported",
                        supporting_evidence=["E2"],
                        stats=RankedEntityStats(evidence_count=1, papers_count=1, contradiction=False),
                    )
                ],
            )
        ]
        selected = select_claim_ids_for_blocks(claims, blocks)
        self.assertEqual(selected, ["C2"])

    def test_claims_too_few_triggers_fallback_logic(self):
        claims = [_claim("C1", "E1")]
        self.assertFalse(claims_are_sufficient(claims, min_items=2))

    def test_type_gate_still_enforced(self):
        plan = _plan()
        blocks = [
            RankedEntitiesBlock(
                type="ranked_entities",
                entity_type="assay",
                items=[
                    RankedEntityItem(
                        entity_id="assay-1",
                        display_name="AssayX",
                        rationale="unsupported",
                        supporting_evidence=["E1"],
                        stats=RankedEntityStats(evidence_count=1, papers_count=1, contradiction=False),
                    )
                ],
            )
        ]
        valid, errors = validate_blocks(blocks, plan, {"E1"})
        self.assertFalse(valid)
        self.assertTrue(errors)

    def test_metric_only_if_in_evidence_text(self):
        evidence_text = "The assay showed a 2-fold increase in activity."
        self.assertFalse(_qualifiers_supported({"metric": "kcat"}, evidence_text))
        self.assertTrue(_qualifiers_supported({"metric": "activity"}, evidence_text))

    def test_direct_answer_citations_still_required(self):
        plan = _plan()
        blocks = [DirectAnswerBlock(type="direct_answer", bullets=[DirectAnswerBullet(text="Answer", citations=["E1"])])]
        valid, errors = validate_blocks(blocks, plan, {"E1"})
        self.assertTrue(valid)
        self.assertFalse(errors)


if __name__ == "__main__":
    unittest.main()
