import json
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI

from src.prompts import REPORTER_SYSTEM_PROMPT


def _build_report_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    ranked_tracks = state.get("ranked_tracks", [])
    watchlist = state.get("watchlist", [])
    insights = state.get("insights", [])
    errors = state.get("errors", [])
    countries = state.get("countries", [])
    top_n = state.get("top_n", 10)

    top_ranked_summary: List[Dict[str, Any]] = []
    for item in ranked_tracks[:top_n]:
        top_ranked_summary.append(
            {
                "artist": item.get("artist", ""),
                "track": item.get("track", ""),
                "trend_score": item.get("trend_score", 0.0),
                "listeners": item.get("listeners", 0),
                "playcount": item.get("playcount", 0),
                "country_chart_seen": item.get("country_chart_seen", []),
                "tags": item.get("tags", []),
            }
        )

    payload = {
        "user_query": state.get("user_query", ""),
        "markets_monitored": countries,
        "top_n_analyzed": top_n,
        "insights": insights,
        "watchlist": watchlist,
        "top_ranked_tracks": top_ranked_summary,
        "errors": errors,
    }
    return payload


def run_reporter_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    errors = list(state.get("errors", []))

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
    )

    payload = _build_report_payload(state)

    user_prompt = f"""
Use the structured data below to write the final report.

Output format:
- Title
- Executive Summary
- Top Opportunities
- Recommended Actions
- Risks / Limitations

Structured data:
{json.dumps(payload, indent=2)}
""".strip()

    try:
        response = llm.invoke(
            [
                {"role": "system", "content": REPORTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )
        final_report = response.content
        status = "reporter_completed"

    except Exception as exc:
        errors.append(f"Reporter agent failed: {exc}")

        watchlist = state.get("watchlist", [])
        insights = state.get("insights", [])

        lines: List[str] = []
        lines.append("Title")
        lines.append("Music Trend Scout Report")
        lines.append("")
        lines.append("Executive Summary")
        if insights:
            for insight in insights:
                lines.append(f"- {insight}")
        else:
            lines.append("- No analyst insights were available.")
        lines.append("")
        lines.append("Top Opportunities")
        if watchlist:
            for item in watchlist[:10]:
                lines.append(
                    f"- {item.get('track', 'Unknown Track')} by {item.get('artist', 'Unknown Artist')} "
                    f"| score={item.get('trend_score', 0.0)} "
                    f"| action={item.get('recommendation', 'Monitor')}"
                )
        else:
            lines.append("- No watchlist items were available.")
        lines.append("")
        lines.append("Recommended Actions")
        lines.append("- Review the top-ranked tracks and validate with platform-specific data.")
        lines.append("- Track these songs again in the next cycle to confirm momentum.")
        lines.append("")
        lines.append("Risks / Limitations")
        lines.append("- Fallback report generated because the LLM reporter step failed.")
        if errors:
            for err in errors[-3:]:
                lines.append(f"- {err}")

        final_report = "\n".join(lines)
        status = "reporter_fallback_completed"

    return {
        **state,
        "final_report": final_report,
        "status": status,
        "errors": errors,
    }