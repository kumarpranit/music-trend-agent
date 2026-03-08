from typing import Any, Dict, List

from src.tools.scoring import rank_tracks


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_insights(
    ranked_tracks: List[Dict[str, Any]],
    countries: List[str],
) -> List[str]:
    insights: List[str] = []

    if not ranked_tracks:
        return ["No tracks were available to analyze."]

    top_track = ranked_tracks[0]
    top_rank = _safe_int(top_track.get("rank"))
    top_streams = _safe_int(top_track.get("streams"))
    top_score = _safe_float(top_track.get("trend_score"))

    headline = (
        f"Top opportunity: '{top_track.get('track', 'Unknown Track')}' by "
        f"{top_track.get('artist', 'Unknown Artist')} leads the ranking with a "
        f"trend score of {top_score:.2f}"
    )

    if top_rank > 0:
        headline += f", current chart rank #{top_rank}"
    if top_streams > 0:
        headline += f", and approximately {top_streams:,} streams"
    headline += "."

    insights.append(headline)

    breakout_tracks = [
        t for t in ranked_tracks
        if _is_breakout_track(t)
    ]
    if breakout_tracks:
        best_breakout = breakout_tracks[0]
        msg = (
            f"Breakout signal: '{best_breakout.get('track', 'Unknown Track')}' by "
            f"{best_breakout.get('artist', 'Unknown Artist')} has the strongest immediate "
            f"commercial signal"
        )
        rank = _safe_int(best_breakout.get("rank"))
        streams = _safe_int(best_breakout.get("streams"))
        if rank > 0:
            msg += f" with chart rank #{rank}"
        if streams > 0:
            msg += f" and {streams:,} streams"
        msg += "."
        insights.append(msg)

    rising_tracks = [
        t for t in ranked_tracks
        if _is_rising_track(t)
    ]
    if rising_tracks:
        best_riser = rising_tracks[0]
        insights.append(
            f"Rising track: '{best_riser.get('track', 'Unknown Track')}' by "
            f"{best_riser.get('artist', 'Unknown Artist')} is showing strong momentum "
            f"but is not yet the top breakout candidate."
        )

    cross_market_tracks = [
        t for t in ranked_tracks if len(t.get("country_chart_seen", [])) >= 2
    ]
    if cross_market_tracks:
        best_cross_market = cross_market_tracks[0]
        insights.append(
            f"Cross-market strength: '{best_cross_market.get('track', 'Unknown Track')}' "
            f"appears in multiple monitored markets "
            f"({', '.join(best_cross_market.get('country_chart_seen', []))})."
        )
    else:
        insights.append(
            "Cross-market strength is limited right now. Most tracks are concentrated "
            "in a small number of monitored markets."
        )

    tag_rich_tracks = [t for t in ranked_tracks if len(t.get("tags", [])) >= 2]
    if tag_rich_tracks:
        tag_track = tag_rich_tracks[0]
        insights.append(
            f"Genre/tag signal: '{tag_track.get('track', 'Unknown Track')}' shows strong "
            f"tag coverage ({', '.join(tag_track.get('tags', [])[:4])}), which can help "
            f"positioning and audience targeting."
        )

    low_data_tracks = [
        t for t in ranked_tracks
        if not t.get("listeners") or not t.get("playcount")
    ]
    if low_data_tracks:
        insights.append(
            f"Data quality note: {len(low_data_tracks)} track(s) had partial listener or "
            f"playcount data, so enrichment fields may understate actual momentum."
        )

    if countries:
        insights.append(
            f"Analysis was benchmarked across {len(countries)} monitored market(s): "
            f"{', '.join(countries)}."
        )

    return insights


def _is_breakout_track(track: Dict[str, Any]) -> bool:
    """
    Very strict condition.
    Only a small number of tracks should qualify.
    """
    rank = _safe_int(track.get("rank"), 9999)
    streams = _safe_int(track.get("streams"))
    score = _safe_float(track.get("trend_score"))
    country_count = len(track.get("country_chart_seen", []))

    return (
        rank <= 3
        and streams >= 5_000_000
        and score >= 60
        and country_count >= 2
    )


def _is_rising_track(track: Dict[str, Any]) -> bool:
    rank = _safe_int(track.get("rank"), 9999)
    streams = _safe_int(track.get("streams"))
    score = _safe_float(track.get("trend_score"))
    country_count = len(track.get("country_chart_seen", []))

    return (
        rank <= 15
        and streams >= 2_000_000
        and score >= 40
        and country_count >= 1
        and not _is_breakout_track(track)
    )


def _is_high_signal_market_test(track: Dict[str, Any]) -> bool:
    rank = _safe_int(track.get("rank"), 9999)
    score = _safe_float(track.get("trend_score"))
    country_count = len(track.get("country_chart_seen", []))

    return (
        rank <= 40
        and score >= 30
        and country_count >= 2
        and not _is_breakout_track(track)
        and not _is_rising_track(track)
    )


def _is_active_watchlist(track: Dict[str, Any]) -> bool:
    score = _safe_float(track.get("trend_score"))
    rank = _safe_int(track.get("rank"), 9999)

    return (
        score >= 20
        or rank <= 75
    )


def _recommend_action(track: Dict[str, Any]) -> str:
    score = _safe_float(track.get("trend_score"))
    rank = _safe_int(track.get("rank"), 9999)
    streams = _safe_int(track.get("streams"))
    country_count = len(track.get("country_chart_seen", []))
    tag_count = len(track.get("tags", []))
    has_partial_data = not track.get("listeners") or not track.get("playcount")

    if _is_breakout_track(track):
        return "🔥 Breakout track — push immediately"

    if _is_rising_track(track):
        return "📈 Rising track — accelerate promotion this week"

    if _is_high_signal_market_test(track):
        return "🎯 Test promotion in high-signal markets"

    if _is_active_watchlist(track):
        if has_partial_data and rank <= 25 and streams >= 1_000_000:
            return "👀 Add to watchlist and validate missing enrichment data"
        return "👀 Add to active watchlist and monitor closely"

    if tag_count >= 2 and country_count >= 1:
        return "⚠️ Early signal — watch for niche or genre-based breakout"

    if rank <= 100:
        return "⚠️ Early signal — monitor but do not invest yet"

    return "No immediate action"


def _build_watchlist(
    ranked_tracks: List[Dict[str, Any]],
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    watchlist: List[Dict[str, Any]] = []

    for item in ranked_tracks[:top_k]:
        watchlist.append(
            {
                "artist": item.get("artist", ""),
                "track": item.get("track", ""),
                "rank": item.get("rank"),
                "streams": _safe_int(item.get("streams")),
                "trend_score": _safe_float(item.get("trend_score")),
                "listeners": _safe_int(item.get("listeners")),
                "playcount": _safe_int(item.get("playcount")),
                "country_chart_seen": item.get("country_chart_seen", []),
                "tags": item.get("tags", []),
                "recommendation": _recommend_action(item),
            }
        )

    return watchlist


def run_analyst_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    normalized_tracks = state.get("normalized_tracks", [])
    countries = state.get("countries", [])
    errors = list(state.get("errors", []))

    if not normalized_tracks:
        return {
            **state,
            "ranked_tracks": [],
            "watchlist": [],
            "insights": ["No normalized tracks available for analysis."],
            "status": "analyst_completed",
            "errors": errors + ["Analyst received empty normalized_tracks."],
        }

    ranked_tracks = rank_tracks(
        tracks=normalized_tracks,
        total_countries_checked=max(len(countries), 1),
    )

    top_n = state.get("top_n", 10)
    watchlist = _build_watchlist(ranked_tracks, top_k=top_n)
    insights = _build_insights(ranked_tracks, countries)

    return {
        **state,
        "ranked_tracks": ranked_tracks,
        "watchlist": watchlist,
        "insights": insights,
        "status": "analyst_completed",
        "errors": errors,
    }