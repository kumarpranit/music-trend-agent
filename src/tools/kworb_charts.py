import pandas as pd
import requests


KWORB_GLOBAL_DAILY_URL = "https://kworb.net/spotify/country/global_daily.html"


def fetch_kworb_spotify_global(limit: int = 20):
    try:
        tables = pd.read_html(
            KWORB_GLOBAL_DAILY_URL,
            flavor="lxml",
            displayed_only=True,
        )

        if not tables:
            print("Kworb chart fetch failed: no HTML tables found.")
            return []

        # Find the first table that looks like the chart table
        chart_df = None
        for df in tables:
            cols = [str(c).strip().lower() for c in df.columns]
            if any("artist" in c for c in cols) or any("track" in c for c in cols):
                chart_df = df
                break

        if chart_df is None:
            print("Kworb chart fetch failed: could not identify chart table.")
            return []

        # Normalize columns
        chart_df.columns = [str(c).strip() for c in chart_df.columns]

        print("Detected Kworb columns:", chart_df.columns.tolist())

        # Kworb tables can vary a bit, so handle flexible names
        def pick_col(candidates):
            for c in candidates:
                if c in chart_df.columns:
                    return c
            return None

        rank_col = pick_col(["Pos", "Rank", "#"])
        artist_track_col = pick_col(["Artist and Title", "Artist / Title", "Title"])
        streams_col = pick_col(["Streams", "Streams"])

        if artist_track_col is None or streams_col is None:
            print("Kworb chart fetch failed: required columns not found.")
            return []

        chart_df = chart_df.head(limit)

        results = []
        for idx, row in chart_df.iterrows():
            raw_title = str(row[artist_track_col]).strip()

            # Typical Kworb format: "Artist - Track"
            if " - " in raw_title:
                artist, track = raw_title.split(" - ", 1)
            else:
                artist, track = "", raw_title

            rank = idx + 1
            if rank_col is not None:
                try:
                    rank = int(float(str(row[rank_col]).replace(",", "").strip()))
                except Exception:
                    rank = idx + 1

            streams_raw = str(row[streams_col]).replace(",", "").strip()
            try:
                streams = int(float(streams_raw))
            except Exception:
                streams = 0

            results.append(
                {
                    "rank": rank,
                    "artist": artist.strip(),
                    "track": track.strip(),
                    "streams": streams,
                    "source": "kworb_spotify_global",
                    "url": KWORB_GLOBAL_DAILY_URL,
                }
            )

        return results

    except Exception as e:
        print("Kworb chart fetch failed:", e)
        return []