import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")


def _fmt_number(value: Any) -> str:
    try:
        if value is None or value == "":
            return "-"
        return f"{int(float(value)):,}"
    except Exception:
        return str(value)


def _card(title: str, inner_html: str) -> str:
    return f"""
    <div style="
        background:#ffffff;
        border-radius:14px;
        padding:22px;
        margin-bottom:22px;
        box-shadow:0 2px 10px rgba(0,0,0,0.08);
    ">
        <h2 style="margin:0 0 14px 0; font-size:22px; color:#111827;">{title}</h2>
        {inner_html}
    </div>
    """


def _track_row(item: Dict[str, Any]) -> str:
    artist = item.get("artist", "Unknown Artist")
    track = item.get("track", "Unknown Track")
    score = item.get("trend_score", 0.0)
    rank = item.get("rank")
    streams = item.get("streams")
    recommendation = item.get("recommendation", "")
    markets = item.get("country_chart_seen", [])
    tags = item.get("tags", [])

    meta_parts: List[str] = []
    if rank:
        meta_parts.append(f"<b>Rank:</b> #{rank}")
    if streams:
        meta_parts.append(f"<b>Streams:</b> {_fmt_number(streams)}")
    meta_parts.append(f"<b>Trend Score:</b> {score}")

    if markets:
        meta_parts.append(f"<b>Markets:</b> {', '.join(markets[:4])}")
    if tags:
        meta_parts.append(f"<b>Tags:</b> {', '.join(tags[:4])}")

    meta_html = " · ".join(meta_parts)

    return f"""
    <div style="padding:14px 0; border-bottom:1px solid #e5e7eb;">
        <div style="font-size:18px; font-weight:700; color:#111827;">
            {track} — {artist}
        </div>
        <div style="margin-top:6px; font-size:14px; color:#374151; line-height:1.5;">
            {meta_html}
        </div>
        <div style="margin-top:8px; font-size:14px; color:#2563eb;">
            <b>Recommendation:</b> {recommendation}
        </div>
    </div>
    """


def _build_breakout_card(watchlist: List[Dict[str, Any]]) -> str:
    breakout = [
        item for item in watchlist
        if "breakout" in item.get("recommendation", "").lower()
    ]

    if not breakout:
        return "<p style='margin:0; color:#4b5563;'>No breakout tracks detected.</p>"

    return "".join(_track_row(item) for item in breakout[:3])


def _build_rising_card(watchlist: List[Dict[str, Any]]) -> str:
    rising = [
        item for item in watchlist
        if "rising" in item.get("recommendation", "").lower()
        or "accelerate" in item.get("recommendation", "").lower()
    ]

    if not rising:
        return "<p style='margin:0; color:#4b5563;'>No strong rising tracks detected.</p>"

    return "".join(_track_row(item) for item in rising[:4])


def _build_watchlist_card(watchlist: List[Dict[str, Any]]) -> str:
    watch_items = [
        item for item in watchlist
        if "watchlist" in item.get("recommendation", "").lower()
        or "test promotion" in item.get("recommendation", "").lower()
    ]

    if not watch_items:
        return "<p style='margin:0; color:#4b5563;'>No watchlist tracks.</p>"

    return "".join(_track_row(item) for item in watch_items[:10])


def _build_early_signals_card(watchlist: List[Dict[str, Any]], errors: List[str]) -> str:
    early = [
        item for item in watchlist
        if "early signal" in item.get("recommendation", "").lower()
        or "niche" in item.get("recommendation", "").lower()
        or "no immediate action" in item.get("recommendation", "").lower()
    ]

    parts: List[str] = []

    if early:
        parts.append("".join(_track_row(item) for item in early[:4]))
    else:
        parts.append("<p style='margin:0 0 10px 0; color:#4b5563;'>No early-signal tracks flagged.</p>")

    if errors:
        err_html = "".join(
            f"<li style='margin-bottom:6px; color:#7c2d12;'>{err}</li>"
            for err in errors[:5]
        )
        parts.append(
            f"""
            <div style="margin-top:12px;">
                <div style="font-weight:700; margin-bottom:8px; color:#111827;">Data Warnings</div>
                <ul style="padding-left:18px; margin:0;">
                    {err_html}
                </ul>
            </div>
            """
        )

    return "".join(parts)


def _build_email_html(subject: str, result: Dict[str, Any]) -> str:
    watchlist = result.get("watchlist", [])
    insights = result.get("insights", [])
    errors = result.get("errors", [])

    insight_html = "".join(
        f"<li style='margin-bottom:8px; color:#374151;'>{insight}</li>"
        for insight in insights[:5]
    ) or "<li style='color:#374151;'>No analyst insights available.</li>"

    return f"""
    <html>
    <body style="background:#f3f4f6; font-family:Arial, Helvetica, sans-serif; padding:32px;">
        <div style="max-width:900px; margin:auto;">
            <h1 style="text-align:center; color:#111827; margin-bottom:28px;">
                🎵 {subject}
            </h1>

            {_card("🧠 Executive Highlights", f"<ul style='margin:0; padding-left:20px;'>{insight_html}</ul>")}

            {_card("🔥 Breakout Track", _build_breakout_card(watchlist))}

            {_card("📈 Rising Tracks", _build_rising_card(watchlist))}

            {_card("🎯 Watchlist", _build_watchlist_card(watchlist))}

            {_card("⚠️ Early Signals", _build_early_signals_card(watchlist, errors))}

            <div style="
                margin-top:24px;
                text-align:center;
                color:#6b7280;
                font-size:12px;
                border-top:1px solid #d1d5db;
                padding-top:14px;
            ">
                <p style="margin:4px 0;">This is an automated report generated by the Music Trend Intelligence System.</p>
                <p style="margin:4px 0;"><b>Please do not reply to this email.</b></p>
            </div>
        </div>
    </body>
    </html>
    """


def send_email(subject: str, result: Dict[str, Any], recipient: str) -> None:
    if not EMAIL_ADDRESS:
        print("Email failed: EMAIL_ADDRESS not found in .env")
        return

    if not EMAIL_APP_PASSWORD:
        print("Email failed: EMAIL_APP_PASSWORD not found in .env")
        return

    html = _build_email_html(subject, result)

    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, [recipient], msg.as_string())

        print(f"Email sent successfully to {recipient}")

    except Exception as e:
        print(f"Email failed: {e}")