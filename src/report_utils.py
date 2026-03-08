from __future__ import annotations

from datetime import datetime
import pandas as pd


def opportunities_to_dataframe(opportunities: list[dict]) -> pd.DataFrame:
    rows = []
    run_ts = datetime.utcnow().isoformat()

    for item in opportunities:
        rows.append(
            {
                "run_timestamp": run_ts,
                "artist": item.get("artist"),
                "title": item.get("title"),
                "trend_score": item.get("trend_score"),
                "current_rank": item.get("current_rank"),
                "streams": item.get("streams"),
                "markets": ", ".join(item.get("markets", [])),
                "recommendation": item.get("recommendation"),
            }
        )

    return pd.DataFrame(rows)