import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research_video import build_dashboard_html, build_research_report, store_history_in_database


class ResearchVideoTests(unittest.TestCase):
    def test_build_research_report_returns_expected_structure(self):
        report = build_research_report("AI tools for students")

        self.assertIn("niche", report)
        self.assertIn("market_score", report)
        self.assertIn("competition_score", report)
        self.assertIn("monetization_score", report)
        self.assertIn("recommendation", report)
        self.assertIn("audience", report)
        self.assertIn("competitors", report)
        self.assertIn("video_opportunities", report)
        self.assertIn("content_gaps", report)
        self.assertIn("recommended_strategy", report)

        self.assertTrue(isinstance(report["video_opportunities"], list))
        self.assertTrue(report["video_opportunities"])
        self.assertTrue(isinstance(report["competitors"], list))
        self.assertTrue(report["audience"]["pain_points"])
        self.assertTrue(report["audience"]["desires"])

    def test_build_research_report_accepts_trend_inputs_and_saves_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            report = build_research_report(
                "AI tools for students",
                trend_inputs=[{"keyword": "ai tools for students", "score": 82, "source": "sample"}],
                save_path=str(output_path),
            )

            self.assertTrue(output_path.exists())
            saved_report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_report["niche"], "AI tools for students")
            self.assertEqual(report["trend_signals"][0]["keyword"], "ai tools for students")
            self.assertEqual(saved_report["trend_signals"][0]["score"], 82)

    @patch("research_video._fetch_youtube_search_results")
    def test_build_research_report_uses_live_search_results(self, mock_search):
        mock_search.return_value = [
            {"title": "Best AI tools for students", "channel_title": "StudyTech", "view_count": 120000}
        ]

        report = build_research_report(
            "AI tools for students",
            youtube_api_enabled=True,
            youtube_search_query="AI tools for students",
        )

        self.assertEqual(report["live_search_results"][0]["title"], "Best AI tools for students")
        self.assertEqual(report["live_search_results"][0]["channel_title"], "StudyTech")

    def test_history_storage_and_config_loading(self):
        config_path = Path("config.json")
        report = build_research_report("AI tools for students", config_path=str(config_path))

        self.assertIn("history_path", report)
        self.assertTrue(Path(report["history_path"]).exists())

    def test_build_dashboard_html_writes_file(self):
        report = build_research_report("AI tools for students")
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "dashboard.html"
            html = build_dashboard_html(report, output_path=str(output_path))

            self.assertIn("YouTube Research Dashboard", html)
            self.assertTrue(output_path.exists())

    def test_store_history_in_database(self):
        report = build_research_report("AI tools for students")
        db_path = Path("tests") / "history_test.sqlite"
        if db_path.exists():
            db_path.unlink(missing_ok=True)

        record_id = store_history_in_database(report, db_path=str(db_path))

        self.assertTrue(record_id)
        self.assertTrue(db_path.exists())

        with sqlite3.connect(db_path) as connection:
            rows = connection.execute("SELECT topic FROM research_history").fetchall()
            self.assertTrue(rows)


if __name__ == "__main__":
    unittest.main()
