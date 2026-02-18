import unittest

from forge.scripts import build_timeline_graph


class TestTimelineGraph(unittest.TestCase):
    def test_extract_year_from_title(self):
        entry = {"title_candidate": "Study on PETase 2022", "pdf_file": "paper.pdf"}
        self.assertEqual(build_timeline_graph.extract_year(entry), 2022)

    def test_extract_year_from_pdf_file(self):
        entry = {"title_candidate": "No year", "pdf_file": "paper_2018.pdf"}
        self.assertEqual(build_timeline_graph.extract_year(entry), 2018)


if __name__ == "__main__":
    unittest.main()
