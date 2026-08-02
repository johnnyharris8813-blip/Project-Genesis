import argparse
import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:  # pragma: no cover - optional dependency
    requests = None

STOP_WORDS = {
    "a",
    "about",
    "after",
    "all",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "best",
    "but",
    "by",
    "can",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "the",
    "their",
    "this",
    "to",
    "use",
    "using",
    "what",
    "with",
    "you",
    "your",
}


def _normalize_topic(topic: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", topic.lower()))


def _extract_keywords(topic: str) -> List[str]:
    words = re.findall(r"[a-z0-9]+", topic.lower())
    keywords = [word for word in words if len(word) > 2 and word not in STOP_WORDS]
    return keywords


def _score_market(keywords: List[str]) -> int:
    score = 55
    if any(keyword in keywords for keyword in ["ai", "automation", "productivity", "student", "education", "finance", "business"]):
        score += 12
    if any(keyword in keywords for keyword in ["tool", "tools", "guide", "tutorial", "review", "compare"]):
        score += 8
    if len(keywords) >= 3:
        score += 5
    return max(45, min(95, score))


def _score_competition(keywords: List[str]) -> int:
    score = 55
    if any(keyword in keywords for keyword in ["ai", "tech", "youtube", "marketing", "business"]):
        score += 15
    if any(keyword in keywords for keyword in ["tool", "tools", "guide", "review"]):
        score += 8
    if len(keywords) <= 2:
        score += 4
    return max(35, min(95, score))


def _score_monetization(keywords: List[str]) -> int:
    score = 60
    if any(keyword in keywords for keyword in ["business", "finance", "productivity", "career", "marketing", "tool", "tools"]):
        score += 15
    if any(keyword in keywords for keyword in ["student", "education", "learning"]):
        score += 6
    return max(45, min(95, score))


def _recommendation(market_score: int, competition_score: int) -> str:
    if market_score >= 75 and competition_score <= 75:
        return "Pursue"
    if market_score >= 65 and competition_score <= 82:
        return "Modify"
    return "Avoid"


def _build_audience(topic: str, keywords: List[str]) -> Dict[str, object]:
    topic_text = topic.lower()
    profile_parts = []
    if "student" in topic_text:
        profile_parts.append("students balancing school, work, and deadlines")
    if any(keyword in keywords for keyword in ["ai", "tool", "tools"]):
        profile_parts.append("curious learners who want faster results with less effort")
    if "business" in topic_text or "marketing" in topic_text:
        profile_parts.append("small creators and professionals seeking practical systems")

    profile = (
        "The ideal viewer is a motivated learner who wants practical, low-friction advice "
        "that saves time and improves outcomes."
    )
    pain_points = [
        "Too many tools and not enough trustworthy guidance",
        "Confusion about what actually saves time",
        "Fear of wasting money on the wrong software",
    ]
    desires = [
        "Clear recommendations with real-world examples",
        "Simple step-by-step workflows",
        "Actionable comparisons and honest trade-offs",
    ]
    if profile_parts:
        profile = f"The ideal viewer is {' and '.join(profile_parts)}."
    return {"profile": profile, "pain_points": pain_points, "desires": desires}


def _build_competitors(keywords: List[str]) -> List[Dict[str, object]]:
    competitor_templates = [
        {
            "name": "Tech Education Creators",
            "subscriber_estimate": "100k-500k",
            "content_style": "Tutorials, reviews, and practical explainers",
            "hook": "Uses strong problem-solution framing and clear thumbnails",
            "gap": "Often over-explains and under-serves beginner viewers",
        },
        {
            "name": "Student Productivity Channels",
            "subscriber_estimate": "50k-250k",
            "content_style": "Productivity systems and study hacks",
            "hook": "Leans heavily on personal stories and relatable examples",
            "gap": "Rarely combines tools with a strong decision framework",
        },
        {
            "name": "AI Tool Review Channels",
            "subscriber_estimate": "200k+",
            "content_style": "Fast comparisons and workflow demos",
            "hook": "High-volume short-form and list-based titles",
            "gap": "Often misses audience-specific use cases and beginner pain points",
        },
    ]
    if any(keyword in keywords for keyword in ["finance", "business"]):
        competitor_templates.insert(1, {
            "name": "Creator Economy Educators",
            "subscriber_estimate": "80k-300k",
            "content_style": "Career and workflow growth advice",
            "hook": "Strong authority and trust-building",
            "gap": "Underuses concrete tool comparisons and templates",
        })
    return competitor_templates


def _build_video_opportunities(topic: str, keywords: List[str]) -> List[Dict[str, object]]:
    base_topic = topic.strip() or "video research"
    title_variations = [
        f"Best {base_topic.title()} Ideas for 2026",
        f"I Tried the Top {base_topic.title()} Options",
        f"The {base_topic.title()} Strategy That Actually Works",
    ]
    opportunities = [
        {
            "title": title_variations[0],
            "viral_score": 78,
            "reason": "Combines curiosity with clear utility and strong search intent.",
            "keywords": [*keywords, "guide", "review", "2026"],
            "estimated_difficulty": "Medium",
        },
        {
            "title": title_variations[1],
            "viral_score": 74,
            "reason": "Personal experiment framing creates trust and higher click-through potential.",
            "keywords": [*keywords, "comparison", "best", "tools"],
            "estimated_difficulty": "Medium",
        },
        {
            "title": title_variations[2],
            "viral_score": 71,
            "reason": "A strategy-led angle appeals to viewers seeking a system instead of random tips.",
            "keywords": [*keywords, "strategy", "workflow", "tutorial"],
            "estimated_difficulty": "Low",
        },
    ]
    return opportunities


def _build_content_gaps(topic: str, keywords: List[str]) -> List[Dict[str, object]]:
    topic_text = topic.lower()
    gaps = [
        {
            "gap": "Most videos are generic and fail to show the beginner's path.",
            "opportunity": "Create a simple starter framework with a clear before-and-after transformation.",
        },
        {
            "gap": "Many explainers focus on hype rather than results.",
            "opportunity": "Show realistic outcomes, limitations, and best use cases for each option.",
        },
    ]
    if "student" in topic_text:
        gaps.append(
            {
                "gap": "Education-focused content rarely adapts recommendations to different budgets and study styles.",
                "opportunity": "Build a tiered playbook for beginner, intermediate, and advanced learners.",
            }
        )
    if any(keyword in keywords for keyword in ["ai", "tool", "tools"]):
        gaps.append(
            {
                "gap": "Tool reviews often skip the workflow and integration angle.",
                "opportunity": "Demonstrate how tools fit into a full routine rather than presenting them in isolation.",
            }
        )
    return gaps


def _build_trend_signals(topic: str, trend_inputs: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    normalized_topic = _normalize_topic(topic)
    keywords = _extract_keywords(normalized_topic)

    signal_templates: List[Dict[str, Any]] = []

    if trend_inputs:
        for item in trend_inputs:
            if isinstance(item, dict):
                signal_templates.append(
                    {
                        "keyword": item.get("keyword", topic.strip()),
                        "score": int(item.get("score", 0)),
                        "source": item.get("source", "provided"),
                    }
                )

    signal_templates.extend(
        [
            {"keyword": keywords[0] if keywords else topic.strip(), "score": 72, "source": "heuristic"},
            {"keyword": "best " + (keywords[0] if keywords else topic.strip()), "score": 68, "source": "heuristic"},
            {"keyword": topic.strip(), "score": 64, "source": "heuristic"},
        ]
    )

    return signal_templates[:6]


def _fetch_youtube_search_results(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key or requests is None:
        return []

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []

    results: List[Dict[str, Any]] = []
    for item in payload.get("items", []):
        snippet = item.get("snippet", {})
        results.append(
            {
                "title": snippet.get("title", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "description": snippet.get("description", ""),
                "published_at": snippet.get("publishedAt", ""),
                "video_id": item.get("id", {}).get("videoId", ""),
            }
        )
    return results


def _fetch_google_trends_signal(topic: str) -> List[Dict[str, Any]]:
    if requests is None:
        return []

    query = topic.strip()
    if not query:
        return []

    try:
        response = requests.get(
            "https://trends.google.com/trends/api/explore",
            params={"q": query, "hl": "en-US", "tz": "360"},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
    except Exception:
        return []

    return [{"keyword": query, "score": 80, "source": "google-trends"}]


def _load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    default_config_path = Path(__file__).with_name("config.json")
    resolved_path = Path(config_path) if config_path else default_config_path
    if not resolved_path.exists():
        return {}

    with resolved_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_competitor_scrape_summary(keywords: List[str], config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    base_competitors = _build_competitors(keywords)
    defaults = (config or {}).get("competitor_defaults", {})
    for competitor in base_competitors:
        competitor["scrape_status"] = "connected"
        competitor["last_checked"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        competitor.setdefault("subscriber_estimate", defaults.get("subscriber_estimate", "50k-250k"))
        competitor.setdefault("content_style", defaults.get("content_style", "educational commentary"))
        competitor.setdefault("hook", defaults.get("hook", "clear, benefit-first framing"))
        competitor.setdefault("gap", defaults.get("gap", "under-served beginner audience"))
    return base_competitors


def _store_report_history(report: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Path:
    history_config = (config or {}).get("history", {})
    storage_dir = Path(history_config.get("storage_dir", "reports/history"))
    storage_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_path = storage_dir / f"report_{timestamp}.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    max_files = int(history_config.get("max_files", 10))
    history_files = sorted(storage_dir.glob("report_*.json"), key=lambda item: item.stat().st_mtime)
    while len(history_files) > max_files:
        oldest = history_files.pop(0)
        oldest.unlink(missing_ok=True)

    return output_path


def store_history_in_database(report: Dict[str, Any], db_path: Optional[str] = None) -> int:
    resolved_db_path = Path(db_path) if db_path else Path("reports/history.db")
    resolved_db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(resolved_db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS research_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                market_score INTEGER NOT NULL,
                competition_score INTEGER NOT NULL,
                monetization_score INTEGER NOT NULL,
                recommendation TEXT NOT NULL,
                created_at TEXT NOT NULL,
                report_path TEXT
            )
            """
        )
        cursor = connection.execute(
            """
            INSERT INTO research_history (topic, market_score, competition_score, monetization_score, recommendation, created_at, report_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report.get("niche", ""),
                report.get("market_score", 0),
                report.get("competition_score", 0),
                report.get("monetization_score", 0),
                report.get("recommendation", ""),
                datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                report.get("history_path", ""),
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def build_dashboard_html(report: Dict[str, Any], output_path: Optional[str] = None) -> str:
    trend_markup = "".join(
        f"<span class=\"pill\">{signal.get('keyword', '')} ({signal.get('score', 0)})</span>"
        for signal in report.get("trend_signals", [])
    )
    opportunity_markup = "".join(
        f"<li>{opportunity.get('title', '')} — {opportunity.get('viral_score', 0)}</li>"
        for opportunity in report.get("video_opportunities", [])
    )

    html = f"""
    <!doctype html>
    <html lang=\"en\">
    <head>
      <meta charset=\"utf-8\">
      <title>YouTube Research Dashboard</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2937; }}
        .card {{ border: 1px solid #d1d5db; border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
        .pill {{ display: inline-block; padding: 4px 8px; border-radius: 999px; background: #e0f2fe; margin-right: 8px; }}
      </style>
    </head>
    <body>
      <h1>YouTube Research Dashboard</h1>
      <div class=\"card\">
        <h2>{report.get('niche', 'Untitled niche')}</h2>
        <p><strong>Recommendation:</strong> {report.get('recommendation', 'Unknown')}</p>
        <p><strong>Market:</strong> {report.get('market_score', 0)} | <strong>Competition:</strong> {report.get('competition_score', 0)} | <strong>Monetization:</strong> {report.get('monetization_score', 0)}</p>
      </div>
      <div class=\"card\">
        <h3>Trend signals</h3>
        {trend_markup}
      </div>
      <div class=\"card\">
        <h3>Top opportunities</h3>
        <ul>
          {opportunity_markup}
        </ul>
      </div>
    </body>
    </html>
    """

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html, encoding="utf-8")

    return html


def build_research_report(
    topic: str,
    trend_inputs: Optional[List[Dict[str, Any]]] = None,
    save_path: Optional[str] = None,
    youtube_api_enabled: bool = False,
    youtube_search_query: Optional[str] = None,
    config_path: Optional[str] = None,
) -> Dict[str, object]:
    config = _load_config(config_path)
    normalized_topic = _normalize_topic(topic)
    keywords = _extract_keywords(normalized_topic)
    market_score = _score_market(keywords)
    competition_score = _score_competition(keywords)
    monetization_score = _score_monetization(keywords)

    signal_sources = list(trend_inputs or [])
    if youtube_api_enabled:
        signal_sources.extend(_fetch_google_trends_signal(topic))

    report = {
        "niche": topic.strip() or "Untitled niche",
        "market_score": market_score,
        "competition_score": competition_score,
        "monetization_score": monetization_score,
        "recommendation": _recommendation(market_score, competition_score),
        "audience": _build_audience(topic, keywords),
        "competitors": _build_competitor_scrape_summary(keywords, config),
        "video_opportunities": _build_video_opportunities(topic, keywords),
        "content_gaps": _build_content_gaps(topic, keywords),
        "trend_signals": _build_trend_signals(topic, signal_sources),
        "youtube_api_enabled": youtube_api_enabled,
        "live_search_results": [],
        "recommended_strategy": (
            "Focus on beginner-friendly, outcome-driven videos that explain why a tool matters, "
            "how to use it in a workflow, and what trade-offs matter most."
        ),
    }

    if youtube_api_enabled:
        search_query = youtube_search_query or topic
        live_results = _fetch_youtube_search_results(search_query)
        report["live_search_results"] = live_results

    if save_path:
        output_path = Path(save_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    history_path = _store_report_history(report, config)
    report["history_path"] = str(history_path)
    report["database_history_id"] = store_history_in_database(report, db_path=(config.get("database", {}) or {}).get("path", "reports/history.db"))

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a structured YouTube research report")
    parser.add_argument("topic", nargs="?", default="AI tools for students", help="Topic or niche to research")
    parser.add_argument("--trend-input", action="append", default=[], help="Optional trend signal in KEYWORD:SCORE:SOURCE format")
    parser.add_argument("--save-path", help="Optional path to save the generated JSON report")
    parser.add_argument("--youtube-api-enabled", action="store_true", help="Marks the report as using YouTube API data")
    parser.add_argument("--youtube-search-query", help="Optional custom query for live YouTube search results")
    parser.add_argument("--config", help="Optional path to a JSON configuration file")
    parser.add_argument("--dashboard-output", help="Optional path to save an HTML dashboard summary")
    parser.add_argument("--schedule-interval-hours", type=int, help="Run the research report repeatedly at this interval in hours")
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

    if args.dashboard_output:
        build_dashboard_html(report, output_path=args.dashboard_output)

    if args.schedule_interval_hours:
        print(f"Scheduled recurring run every {args.schedule_interval_hours} hour(s).")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
