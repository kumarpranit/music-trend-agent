import os
import time
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv


load_dotenv()

BASE_URL = "https://ws.audioscrobbler.com/2.0/"
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")


class LastFMClientError(Exception):
    pass


class LastFMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 20,
        max_retries: int = 3,
        backoff_seconds: float = 1.5,
    ) -> None:
        self.api_key = api_key or LASTFM_API_KEY
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

        if not self.api_key:
            raise LastFMClientError(
                "LASTFM_API_KEY not found. Add it to your .env file."
            )

    def _request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        query_params = {
            "method": method,
            "api_key": self.api_key,
            "format": "json",
            **params,
        }

        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(
                    BASE_URL,
                    params=query_params,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()

                if isinstance(data, dict) and "error" in data:
                    error_code = data.get("error")
                    error_message = data.get("message", "Unknown Last.fm API error")

                    if error_code == 29 and attempt < self.max_retries:
                        time.sleep(self.backoff_seconds * attempt)
                        continue

                    raise LastFMClientError(
                        f"Last.fm API error {error_code}: {error_message}"
                    )

                return data

            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * attempt)
                else:
                    raise LastFMClientError(
                        f"Request failed after {self.max_retries} attempts: {exc}"
                    ) from exc

        raise LastFMClientError(f"Unexpected request failure: {last_error}")

    def get_top_tracks(self, limit: int = 10, page: int = 1) -> List[Dict[str, Any]]:
        data = self._request(
            "chart.getTopTracks",
            {
                "limit": limit,
                "page": page,
            },
        )
        return data.get("tracks", {}).get("track", [])

    def get_geo_top_tracks(
        self,
        country: str,
        limit: int = 10,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        data = self._request(
            "geo.getTopTracks",
            {
                "country": country,
                "limit": limit,
                "page": page,
            },
        )
        return data.get("tracks", {}).get("track", [])

    def get_track_info(
        self,
        artist: str,
        track: str,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "artist": artist,
            "track": track,
            "autocorrect": 1,
        }
        if username:
            params["username"] = username

        data = self._request("track.getInfo", params)
        return data.get("track", {})

    def get_artist_info(
        self,
        artist: str,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "artist": artist,
            "autocorrect": 1,
        }
        if username:
            params["username"] = username

        data = self._request("artist.getInfo", params)
        return data.get("artist", {})


if __name__ == "__main__":
    client = LastFMClient()
    top_tracks = client.get_top_tracks(limit=10)

    print("Top 10 global chart tracks:")
    for idx, item in enumerate(top_tracks, start=1):
        artist_name = item.get("artist", {}).get("name", "Unknown Artist")
        track_name = item.get("name", "Unknown Track")
        print(f"{idx}. {track_name} - {artist_name}")