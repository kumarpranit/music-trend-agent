from pprint import pprint
from datetime import datetime
import json
from pathlib import Path
import csv
import os

from src.graph import build_graph
from src.tools.email_sender import send_email
from src.report_utils import build_markdown_report, build_console_alert


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
HISTORY_DIR = DATA_DIR / "history"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def timestamp_slug() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")


def save_report(report_text: str) -> Path:
    path = REPORTS_DIR / f"weekly_music_report_{timestamp_slug()}.md"
    path.write_text(report_text, encoding="utf-8")
    return path


def save_latest_report(report_text: str) -> Path:
    path = REPORTS_DIR / "latest_report.md"
    path.write_text(report_text, encoding="utf-8")
    return path


def save_snapshot(result: dict) -> Path:
    path = HISTORY_DIR / f"music_snapshot_{timestamp_slug()}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    return path


def append_watchlist_history(watchlist: list[dict]) -> Path:
    path = HISTORY_DIR / "watchlist_history.csv"
    file_exists = path.exists()

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run_timestamp",
                "track",
                "artist",
                "trend_score",
                "recommendation",
            ],
        )

        if not file_exists:
            writer.writeheader()

        run_ts = datetime.utcnow().isoformat()

        for item in watchlist:
            writer.writerow(
                {
                    "run_timestamp": run_ts,
                    "track": item.get("track", ""),
                    "artist": item.get("artist", ""),
                    "trend_score": item.get("trend_score", 0.0),
                    "recommendation": item.get("recommendation", "Monitor"),
                }
            )

    return path


def main() -> None:
    app = build_graph()

    initial_state = {
        "user_query": "Which tracks should a music label watch this week?",
        "top_n": 10,
        "countries": [
            "United States",
            "United Kingdom",
            "Canada",
            "Australia",
            "Brazil",
            "India",
        ],
        "errors": [],
        "status": "initialized",
    }

    print("\nRunning music trend analysis pipeline...\n")

    result = app.invoke(initial_state)

    summary = result.get("summary", "")
    watchlist = result.get("watchlist", [])
    final_report = result.get("final_report")

    if not final_report:
        if watchlist:
            final_report = build_markdown_report(summary, watchlist)
        else:
            final_report = "No report generated."

    console_alert = build_console_alert(watchlist)

    report_path = save_report(final_report)
    latest_report_path = save_latest_report(final_report)
    snapshot_path = save_snapshot(result)
    history_path = append_watchlist_history(watchlist)

    print("\n" + "=" * 80)
    print("FINAL REPORT")
    print("=" * 80)
    print(final_report)

    print("\n" + "=" * 80)
    print("TOP ALERTS")
    print("=" * 80)
    print(console_alert)

    print("\nSaved outputs:")
    print(f"- Report:         {report_path}")
    print(f"- Latest report:  {latest_report_path}")
    print(f"- Snapshot:       {snapshot_path}")
    print(f"- Watch history:  {history_path}")

    print("\nSending email report...")
    should_send_email = os.getenv("SEND_EMAIL", "false").lower() == "true"

    if should_send_email:
        print("\nSending email report...")
    try:
        send_email(
            subject="Weekly Music Intelligence Report",
            result=result,
            recipient="pranitkumar1202@gmail.com",
        )
        print("Email sent successfully.")
    except Exception as e:
        print(f"Email sending failed: {e}")
    else:
        print("\nEmail sending skipped.")

    print("\n" + "=" * 80)
    print("WATCHLIST")
    print("=" * 80)
    for idx, item in enumerate(watchlist, start=1):
        print(
            f"{idx}. {item.get('track', 'Unknown Track')} - "
            f"{item.get('artist', 'Unknown Artist')} | "
            f"score={item.get('trend_score', 0.0)} | "
            f"action={item.get('recommendation', 'Monitor')}"
        )

    if result.get("errors"):
        print("\n" + "=" * 80)
        print("ERRORS / WARNINGS")
        print("=" * 80)
        pprint(result["errors"])

    print("\n" + "=" * 80)
    print("STATUS")
    print("=" * 80)
    print(result.get("status", "unknown"))

    print("\nPipeline finished.\n")


if __name__ == "__main__":
    main()