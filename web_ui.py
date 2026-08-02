import http.server
import json
import os
import socketserver
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"
HISTORY_DIR = REPORTS_DIR / "history"


class ResearchHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self._render_index().encode("utf-8"))
            return

        if self.path.startswith("/api/reports"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            reports = self._load_reports()
            self.wfile.write(json.dumps(reports).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def _load_reports(self):
        report_files = sorted(HISTORY_DIR.glob("report_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
        reports = []
        for report_path in report_files[:20]:
            try:
                with report_path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                reports.append({
                    "path": str(report_path),
                    "topic": data.get("niche", "Untitled"),
                    "recommendation": data.get("recommendation", "Unknown"),
                    "market_score": data.get("market_score", 0),
                })
            except Exception:
                continue
        return reports

    def _render_index(self) -> str:
        return """
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <title>YouTube Research UI</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 24px; }
            .card { border: 1px solid #d1d5db; border-radius: 8px; padding: 12px; margin-bottom: 12px; }
          </style>
        </head>
        <body>
          <h1>YouTube Research UI</h1>
          <p>Browse recent saved research reports.</p>
          <div id="reports"></div>
          <script>
            fetch('/api/reports').then(r => r.json()).then(data => {
              const container = document.getElementById('reports');
              if (!data.length) {
                container.innerHTML = '<div class="card">No reports yet.</div>';
                return;
              }
              container.innerHTML = data.map(report => `
                <div class="card">
                  <strong>${report.topic}</strong><br>
                  Recommendation: ${report.recommendation}<br>
                  Market score: ${report.market_score}<br>
                  Path: ${report.path}
                </div>
              `).join('');
            });
          </script>
        </body>
        </html>
        """


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    with socketserver.TCPServer(("127.0.0.1", port), ResearchHandler) as httpd:
        print(f"Serving web UI on http://127.0.0.1:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
