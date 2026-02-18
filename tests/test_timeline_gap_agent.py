import unittest
from pathlib import Path

from fabric.agents import timeline_gap_agent


class TestTimelineGapAgent(unittest.TestCase):
    def test_summarize_workspace_tiny_fixture(self):
        workspace = Path(__file__).resolve().parent / "fixtures" / "workspace_tiny"
        summary = timeline_gap_agent.summarize_workspace(workspace)
        self.assertEqual(summary["timeline_edges"], "present")
        self.assertEqual(summary["timeline"]["paper_count"], 2)
        self.assertEqual(summary["timeline"]["year_span"], (2019, 2021))
        self.assertIn(2020, summary["timeline"]["missing_years"])
        self.assertEqual(summary["kg"]["edge_count"], 2)


if __name__ == "__main__":
    unittest.main()
