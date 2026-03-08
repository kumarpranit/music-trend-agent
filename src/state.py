from typing import TypedDict, Dict, Any, List

class MusicState(TypedDict, total=False):
    # User request 
    user_query: str #the question asked to the system

    # Config / runtime inputs
    countries: List[str] #markets we want to check, like ["United States", "United Kingdom"]
    top_n: int #how many tracks to pull

    # Raw collected data
    raw_chart_tracks: List[Dict[str, Any]] #global chart tracks from Last.fm
    raw_geo_tracks: Dict[str, List[Dict[str, Any]]] #country-specific chart tracks
    raw_track_details: List[Dict[str, Any]] #enriched track info
    raw_artist_details: List[Dict[str, Any]] #enriched artist info

    # Normalized / merged data
    normalized_tracks: List[Dict[str, Any]]#one clean merged dataset

    # Analysis
    ranked_tracks: List[Dict[str, Any]] #scored and sorted tracks
    insights: List[str]#analyst findings
    watchlist: List[Dict[str, Any]]#top breakout candidates

    # Final output
    final_report: str #summary written by reporter agent

    # Flow control / debugging
    status: str #current pipeline status 
    errors: List[str] #collected issues so the run does not silently fail