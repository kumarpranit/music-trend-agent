import pandas as pd
import requests
from io import StringIO


SPOTIFY_CHART_URL = "https://spotifycharts.com/regional/global/daily/latest/download"


def fetch_spotify_charts(limit: int = 20):
    try:
        response = requests.get(
            SPOTIFY_CHART_URL,
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/csv,application/octet-stream,text/plain,*/*",
            },
        )
        response.raise_for_status()

        raw_text = response.text.strip()

        # If Spotify returns HTML instead of CSV, fail clearly
        if raw_text.lower().startswith("<!doctype html") or raw_text.lower().startswith("<html"):
            print("Spotify chart fetch failed: endpoint returned HTML instead of CSV.")
            print("This usually means the old download URL is no longer publicly returning chart CSV data.")
            return []

        # Debug: print first few lines if needed
        preview = "\n".join(raw_text.splitlines()[:3])
        print("Spotify response preview:")
        print(preview)

        df = pd.read_csv(StringIO(raw_text))
        df.columns = [str(c).strip() for c in df.columns]
        print("Detected Spotify columns:", df.columns.tolist())

        # Flexible column matching
        rank_candidates = ["Rank", "Position", "rank", "position"]
        track_candidates = ["Track Name", "Track", "track_name", "title"]
        artist_candidates = ["Artist", "Artist Name", "artist"]
        stream_candidates = ["Streams", "streams"]
        url_candidates = ["URL", "Url", "url", "Track URL"]

        def pick_column(candidates):
            for c in candidates:
                if c in df.columns:
                    return c
            return None

        rank_col = pick_column(rank_candidates)
        track_col = pick_column(track_candidates)
        artist_col = pick_column(artist_candidates)
        stream_col = pick_column(stream_candidates)
        url_col = pick_column(url_candidates)

        missing = {
            "rank": rank_col,
            "track": track_col,
            "artist": artist_col,
            "streams": stream_col,
        }
        missing_required = [k for k, v in missing.items() if v is None]

        if missing_required:
            print(f"Spotify chart fetch failed: missing required columns {missing_required}")
            return []

        df = df.head(limit)

        results = []
        for _, row in df.iterrows():
            streams_raw = str(row[stream_col]).replace(",", "").strip()

            results.append(
                {
                    "rank": int(float(row[rank_col])),
                    "track": str(row[track_col]).strip(),
                    "artist": str(row[artist_col]).strip(),
                    "streams": int(float(streams_raw)),
                    "url": str(row[url_col]).strip() if url_col else "",
                    "source": "spotify_charts",
                }
            )

        return results

    except Exception as e:
        print("Spotify chart fetch failed:", e)
        return []