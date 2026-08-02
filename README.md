# YouTube Automation Research Agent

This project is an AI automation workshop for building a YouTube research pipeline.

## What it does

- Researches video niches and generates structured reports
- Scores market opportunity, competition, and monetization potential
- Collects trend signals and optional live YouTube search results
- Saves reports as JSON, renders an HTML dashboard, and stores history in SQLite
- Supports a lightweight web UI for browsing past reports

## Setup

1. Install Python 3.10+.
2. From the project folder, install the optional dependency if you want live API calls:

```bash
pip install requests
```

3. Set an API key if you want live YouTube Data API search results:

```bash
$env:YOUTUBE_API_KEY="your_key_here"
```

## Usage

### Run the research workflow

```bash
python run_research.py "AI tools for students" --save-path reports/latest_report.json --dashboard-output reports/dashboard.html --config config.json
```

### Run the research module directly

```bash
python research_video.py "AI tools for students" --save-path reports/latest_report.json --config config.json
```

### Start the web UI

```bash
python web_ui.py
```

Then open http://127.0.0.1:8000 in your browser.

### Generate an HTML dashboard only

```bash
python research_video.py "AI tools for students" --dashboard-output reports/dashboard.html --config config.json
```

## Output files

- JSON reports: reports/latest_report.json
- HTML dashboard: reports/dashboard.html
- JSON history files: reports/history/
- SQLite history database: reports/history.db

## Notes

- The current implementation uses fallback heuristics when API access is unavailable.
- The web UI reads recent history files from the reports/history folder.
- The runner script is intended as a simple one-command entry point for scheduled or recurring research jobs.