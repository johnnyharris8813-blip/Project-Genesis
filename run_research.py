import argparse
import json
import sys
from pathlib import Path

from research_video import build_research_report, build_dashboard_html


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the research workflow with one command")
    parser.add_argument("topic", nargs="?", default="AI tools for students")
    parser.add_argument("--save-path", default="reports/latest_report.json")
    parser.add_argument("--dashboard-output", default="reports/dashboard.html")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--trend-input", action="append", default=[])
    parser.add_argument("--youtube-api-enabled", action="store_true")
    parser.add_argument("--youtube-search-query")
    args = parser.parse_args()

    trend_inputs = []
    for entry in args.trend_input:
        parts = entry.split(":", 2)
        if len(parts) >= 2:
            keyword = parts[0]
            try:
                score = int(parts[1])
            except ValueError:
                score = 0
            source = parts[2] if len(parts) == 3 else "cli"
            trend_inputs.append({"keyword": keyword, "score": score, "source": source})

    report = build_research_report(
        args.topic,
        trend_inputs=trend_inputs or None,
        save_path=args.save_path,
        youtube_api_enabled=args.youtube_api_enabled,
        youtube_search_query=args.youtube_search_query,
        config_path=args.config,
    )
    build_dashboard_html(report, output_path=args.dashboard_output)

    print(json.dumps({"topic": args.topic, "report_path": args.save_path, "dashboard_path": args.dashboard_output, "database_history_id": report.get("database_history_id")}, indent=2))


if __name__ == "__main__":
    main()
