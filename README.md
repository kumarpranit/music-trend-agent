🎵 Music Trend Agent

An automated AI pipeline that discovers emerging music trends, analyzes track momentum across multiple platforms, and produces a weekly scouting report for music labels. This project uses LangGraph-based AI agents, external music APIs, and GitHub Actions automation to continuously monitor chart activity and generate intelligence reports.

🚀 What This Agent Does

The system automatically:
    Collects music chart data from multiple sources
    Normalizes and analyzes track performance
    Scores songs based on momentum and popularity signals
    Generates a weekly scouting report
    Maintains historical watchlists
    Sends email alerts with key opportunities
    All of this runs automatically through GitHub Actions.

.

🧠 Agent Architecture
    The pipeline is built using LangGraph agents:

    Collector Agent
          ↓
    Analyst Agent
          ↓
    Reporter Agent
          ↓
    Email + Report Output

1️⃣ Collector Agent

Collects chart data from:
    Kworb
    Last.fm
    Normalizes tracks into a unified format.

2️⃣ Analyst Agent

    Calculates trend scores using signals like:
    chart rank
    stream momentum
    cross-market presence
    platform consistency
    Outputs a watchlist of promising tracks.

3️⃣ Reporter Agent
    Generates a structured report:
    executive summary
    top opportunities
    recommended actions
    risk considerations

Run Locally:
    python -m src.main

The pipeline is automatically executed using GitHub Actions.
    .github/workflows/music-trends.yml
Daily run at 15:00 UTC


👤 Author

Pranit Kumar
MS Business Analytics
UCLA Anderson School of Management