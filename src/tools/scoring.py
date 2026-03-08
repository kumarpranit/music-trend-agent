from typing import Any, Dict, List


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def min_max_normalize(value: float, min_value: float, max_value: float) -> float:
    if max_value <= min_value:
        return 0.0
    return (value - min_value) / (max_value - min_value)


def inverse_rank_score(rank: int, max_rank: int) -> float:
    """
    Lower chart rank is better.
    Example: rank 1 should score near 1.0, rank max_rank near 0.0.
    """
    if rank <= 0 or max_rank <= 0:
        return 0.0
    if max_rank == 1:
        return 1.0
    return max(0.0, (max_rank - rank) / (max_rank - 1))


def compute_presence_score(country_count: int, total_countries_checked: int) -> float:
    if total_countries_checked <= 0:
        return 0.0
    return country_count / total_countries_checked


def compute_tag_score(tags: List[str]) -> float:
    if not tags:
        return 0.0

    high_signal_tags = {
        "pop",
        "hip-hop",
        "rap",
        "indie",
        "indie pop",
        "rnb",
        "dance",
        "electronic",
        "viral",
        "trending",
        "latin",
        "reggaeton",
        "synthpop",
        "alternative",
        "chill",
    }

    matches = sum(1 for tag in tags if str(tag).lower() in high_signal_tags)
    return min(matches / 3.0, 1.0)


def compute_trend_score(
    rank: int,
    max_rank: int,
    streams: float,
    stream_min: float,
    stream_max: float,
    listeners: float,
    listener_min: float,
    listener_max: float,
    playcount: float,
    playcount_min: float,
    playcount_max: float,
    country_count: int,
    total_countries_checked: int,
    tags: List[str],
) -> float:
    rank_score = inverse_rank_score(rank, max_rank) if rank > 0 else 0.0
    stream_score = min_max_normalize(streams, stream_min, stream_max)
    listener_score = min_max_normalize(listeners, listener_min, listener_max)
    playcount_score = min_max_normalize(playcount, playcount_min, playcount_max)
    presence_score = compute_presence_score(country_count, total_countries_checked)
    tag_score = compute_tag_score(tags)

    # Prefer current momentum, then enrichment signals
    score = (
        0.35 * rank_score
        + 0.25 * stream_score
        + 0.15 * listener_score
        + 0.10 * playcount_score
        + 0.10 * presence_score
        + 0.05 * tag_score
    )

    return round(score * 100, 2)


def rank_tracks(
    tracks: List[Dict[str, Any]],
    total_countries_checked: int,
) -> List[Dict[str, Any]]:
    if not tracks:
        return []

    streams_list = [safe_float(track.get("streams")) for track in tracks]
    listeners_list = [safe_float(track.get("listeners")) for track in tracks]
    playcount_list = [safe_float(track.get("playcount")) for track in tracks]
    rank_list = [safe_int(track.get("rank")) for track in tracks if safe_int(track.get("rank")) > 0]

    stream_min = min(streams_list) if streams_list else 0.0
    stream_max = max(streams_list) if streams_list else 1.0

    listener_min = min(listeners_list) if listeners_list else 0.0
    listener_max = max(listeners_list) if listeners_list else 1.0

    playcount_min = min(playcount_list) if playcount_list else 0.0
    playcount_max = max(playcount_list) if playcount_list else 1.0

    max_rank = max(rank_list) if rank_list else len(tracks)

    ranked: List[Dict[str, Any]] = []

    for track in tracks:
        rank = safe_int(track.get("rank"))
        streams = safe_float(track.get("streams"))
        listeners = safe_float(track.get("listeners"))
        playcount = safe_float(track.get("playcount"))
        country_count = len(track.get("country_chart_seen", []))
        tags = track.get("tags", [])

        trend_score = compute_trend_score(
            rank=rank,
            max_rank=max_rank,
            streams=streams,
            stream_min=stream_min,
            stream_max=stream_max,
            listeners=listeners,
            listener_min=listener_min,
            listener_max=listener_max,
            playcount=playcount,
            playcount_min=playcount_min,
            playcount_max=playcount_max,
            country_count=country_count,
            total_countries_checked=total_countries_checked,
            tags=tags,
        )

        enriched = {
            **track,
            "trend_score": trend_score,
        }
        ranked.append(enriched)

    ranked.sort(
        key=lambda x: (
            x.get("trend_score", 0.0),
            -safe_int(x.get("rank"), 999999) if safe_int(x.get("rank")) > 0 else 0,
            safe_float(x.get("streams")),
        ),
        reverse=True,
    )
    return ranked


if __name__ == "__main__":
    sample_tracks = [
        {
            "artist": "Artist A",
            "track": "Track A",
            "rank": 3,
            "streams": 7200000,
            "listeners": 120000,
            "playcount": 900000,
            "country_chart_seen": ["United States", "United Kingdom"],
            "tags": ["pop", "dance"],
        },
        {
            "artist": "Artist B",
            "track": "Track B",
            "rank": 12,
            "streams": 4100000,
            "listeners": 80000,
            "playcount": 400000,
            "country_chart_seen": ["United States"],
            "tags": ["indie"],
        },
        {
            "artist": "Artist C",
            "track": "Track C",
            "rank": 1,
            "streams": 9800000,
            "listeners": 200000,
            "playcount": 1500000,
            "country_chart_seen": ["United States", "United Kingdom", "Canada"],
            "tags": ["viral", "pop"],
        },
    ]

    results = rank_tracks(sample_tracks, total_countries_checked=3)

    print("Ranked sample tracks:")
    for item in results:
        print(
            f"{item['track']} - {item['artist']} | "
            f"rank={item.get('rank')} | "
            f"streams={item.get('streams')} | "
            f"score={item['trend_score']}"
        )