from typing import Any, Dict, List, Set, Tuple
from src.tools.kworb_charts import fetch_kworb_spotify_global
from src.tools.lastfm_clients import LastFMClient, LastFMClientError

def _extract_tag_names(track_info: Dict[str, Any]) -> List[str]:
    tags = track_info.get("toptags", {}).get("tag", [])
    if isinstance(tags, dict):
        tags = [tags]

    results: List[str] = []
    for tag in tags:
        if isinstance(tag, dict):
            name = str(tag.get("name", "")).strip()
            if name:
                results.append(name)
    return results


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return default


def _build_geo_presence_map(
    geo_tracks_by_country: Dict[str, List[Dict[str, Any]]],
) -> Dict[Tuple[str, str], List[str]]:
    presence_map: Dict[Tuple[str, str], List[str]] = {}

    for country, tracks in geo_tracks_by_country.items():
        for item in tracks:
            track_name = str(item.get("name", "")).strip()

            artist_obj = item.get("artist", {})
            if isinstance(artist_obj, dict):
                artist_name = str(artist_obj.get("name", "")).strip()
            else:
                artist_name = str(artist_obj).strip()

            if not track_name or not artist_name:
                continue

            key = (artist_name.lower(), track_name.lower())
            if key not in presence_map:
                presence_map[key] = []
            presence_map[key].append(country)

    return presence_map


def run_collector_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    client = LastFMClient()

    top_n = state.get("top_n", 10)
    countries = state.get(
        "countries",
        ["United States", "United Kingdom", "Canada", "Australia"],
    )

    errors: List[str] = list(state.get("errors", []))

    # 1) Get live chart tracks from Kworb
    chart_tracks = fetch_kworb_spotify_global(limit=top_n)

    if not chart_tracks:
        return {
            **state,
            "status": "collector_failed",
            "errors": errors + ["Failed to fetch chart tracks from Kworb."],
            "normalized_tracks": [],
        }

    # 2) Get geo tracks from Last.fm for cross-market presence
    raw_geo_tracks: Dict[str, List[Dict[str, Any]]] = {}
    for country in countries:
        try:
            raw_geo_tracks[country] = client.get_geo_top_tracks(
                country=country,
                limit=top_n,
            )
        except LastFMClientError as exc:
            raw_geo_tracks[country] = []
            errors.append(f"Failed to fetch geo top tracks for {country}: {exc}")

    geo_presence_map = _build_geo_presence_map(raw_geo_tracks)

    raw_track_details: List[Dict[str, Any]] = []
    raw_artist_details: List[Dict[str, Any]] = []
    normalized_tracks: List[Dict[str, Any]] = []

    seen_artist_keys: Set[str] = set()
    artist_info_lookup: Dict[str, Dict[str, Any]] = {}

    # 3) Enrich each chart track using Last.fm
    for item in chart_tracks:
        track_name = str(item.get("track", "")).strip()
        artist_name = str(item.get("artist", "")).strip()

        if not track_name or not artist_name:
            errors.append(f"Skipped invalid chart item: {item}")
            continue

        try:
            track_info = client.get_track_info(artist=artist_name, track=track_name)
        except LastFMClientError as exc:
            track_info = {}
            errors.append(
                f"Failed to fetch track info for '{track_name}' by '{artist_name}': {exc}"
            )

        raw_track_details.append(track_info)

        artist_key = artist_name.lower()
        if artist_key not in seen_artist_keys:
            try:
                artist_info = client.get_artist_info(artist=artist_name)
            except LastFMClientError as exc:
                artist_info = {}
                errors.append(f"Failed to fetch artist info for '{artist_name}': {exc}")

            seen_artist_keys.add(artist_key)
            artist_info_lookup[artist_key] = artist_info
            raw_artist_details.append(artist_info)

        artist_info = artist_info_lookup.get(artist_key, {})

        geo_key = (artist_name.lower(), track_name.lower())
        country_chart_seen = geo_presence_map.get(geo_key, [])

        listeners = _safe_int(track_info.get("listeners"))
        playcount = _safe_int(track_info.get("playcount"))
        artist_listeners = _safe_int(artist_info.get("stats", {}).get("listeners"))
        artist_playcount = _safe_int(artist_info.get("stats", {}).get("playcount"))
        tags = _extract_tag_names(track_info)

        normalized_tracks.append(
            {
                "artist": artist_name,
                "track": track_name,
                "rank": _safe_int(item.get("rank")),
                "streams": _safe_int(item.get("streams")),
                "listeners": listeners,
                "playcount": playcount,
                "artist_listeners": artist_listeners,
                "artist_playcount": artist_playcount,
                "tags": tags,
                "global_chart_seen": True,
                "country_chart_seen": country_chart_seen,
                "track_url": track_info.get("url", ""),
                "artist_url": artist_info.get("url", ""),
                "summary": artist_info.get("bio", {}).get("summary", ""),
                "source": item.get("source", "kworb_spotify_global"),
            }
        )

    return {
        **state,
        "raw_chart_tracks": chart_tracks,
        "raw_geo_tracks": raw_geo_tracks,
        "raw_track_details": raw_track_details,
        "raw_artist_details": raw_artist_details,
        "normalized_tracks": normalized_tracks,
        "status": "collector_completed",
        "errors": errors,
    }