from __future__ import annotations

from datetime import datetime
import pandas as pd


def watchlist_to_dataframe(watchlist: list[dict]) -> pd.DataFrame:
    rows = []
    run_ts = datetime.utcnow().isoformat()

    for item in watchlist:
        rows.append(
            {
                "run_timestamp": run_ts,
                "track": item.get("track"),
                "artist": item.get("artist"),
                "trend_score": item.get("trend_score"),
                "recommendation": item.get("recommendation"),
                "current_rank": item.get("current_rank"),
                "streams": item.get("streams"),
                "markets": ", ".join(item.get("markets", [])) if item.get("markets") else "",
            }
        )

    return pd.DataFrame(rows)


def build_markdown_report(summary: str, watchlist: list[dict]) -> str:
    lines = []
    lines.append("# Weekly Music Trend Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(summary.strip() if summary else "No summary available.")
    lines.append("")
    lines.append("## Watchlist")
    lines.append("")

    for i, item in enumerate(watchlist, start=1):
        track = item.get("track", "Unknown Track")
        artist = item.get("artist", "Unknown Artist")
        trend_score = item.get("trend_score", "N/A")
        recommendation = item.get("recommendation", "Monitor")
        current_rank = item.get("current_rank", "N/A")
        streams = item.get("streams", "N/A")
        markets = ", ".join(item.get("markets", [])) if item.get("markets") else "N/A"

        lines.append(f"### {i}. {track} - {artist}")
        lines.append(f"- **Trend Score:** {trend_score}")
        lines.append(f"- **Recommendation:** {recommendation}")
        lines.append(
            f"- **Current Rank:** #{current_rank}"
            if current_rank != "N/A"
            else f"- **Current Rank:** {current_rank}"
        )
        lines.append(f"- **Streams:** {streams}")
        lines.append(f"- **Markets:** {markets}")
        lines.append("")

    return "\n".join(lines)


def build_console_alert(watchlist: list[dict], top_n: int = 5) -> str:
    lines = []
    lines.append("TOP MUSIC ALERTS")
    lines.append("=" * 50)

    for idx, item in enumerate(watchlist[:top_n], start=1):
        lines.append(
            f"{idx}. {item.get('track', 'Unknown Track')} - "
            f"{item.get('artist', 'Unknown Artist')} | "
            f"Score: {item.get('trend_score', 'N/A')} | "
            f"Action: {item.get('recommendation', 'Monitor')}"
        )

    return "\n".join(lines)