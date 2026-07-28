"""
Peak Forecast — "this place peaks in ~40 min".

Answers the question that actually moves someone off a couch: not just
"is it alive now" but "when should I be there".

Honest by construction (the creed applies to predictions too):
  * Built from the venue's OWN history, bucketed by hour of the Lagos night,
    matched on day type (weekend vs weekday).
  * Refuses to speak without MIN_SAMPLES real ratings behind the claim.
  * Returns None when it does not know. We never dress a city-wide guess up
    as a venue-specific prediction.

Pure functions here; the DB aggregation lives in compute_peak_forecast().
"""
from datetime import datetime, timedelta, timezone

LAGOS_OFFSET_HOURS = 1          # UTC+1, no DST
LOOKBACK_WEEKS = 4
MIN_SAMPLES_PER_HOUR = 3        # ratings needed in an hour bucket to trust it
MIN_TOTAL_SAMPLES = 8           # ratings needed across the night to forecast
PEAKING_NOW_WINDOW = 20         # minutes either side of peak = "peaking now"
MAX_LOOKAHEAD_MINUTES = 300     # do not forecast more than 5h out


def lagos_hour(dt: datetime) -> int:
    """Hour of day in Lagos time (UTC+1)."""
    return (dt.hour + LAGOS_OFFSET_HOURS) % 24


def is_weekend_night(dt: datetime) -> bool:
    """Fri/Sat/Sun nights behave differently from weekdays."""
    return dt.weekday() >= 4


def peak_hour_from_history(hour_stats: dict) -> int | None:
    """
    Pick the venue's characteristic peak hour.

    hour_stats: {lagos_hour: (avg_score, sample_count)}
    Returns the hour with the highest average score among buckets that clear
    MIN_SAMPLES_PER_HOUR, or None if nothing qualifies.
    """
    eligible = {
        hour: avg
        for hour, (avg, count) in hour_stats.items()
        if count >= MIN_SAMPLES_PER_HOUR
    }
    if not eligible:
        return None
    total = sum(count for _, count in hour_stats.values())
    if total < MIN_TOTAL_SAMPLES:
        return None
    return max(eligible, key=eligible.get)


def minutes_until_hour(now: datetime, target_hour: int) -> int:
    """
    Minutes from now until the START of target_hour in Lagos time.
    Wraps past midnight (23:40 -> hour 1 is 80 minutes, not negative).
    """
    current_h = lagos_hour(now)
    current_m = now.minute
    delta_h = (target_h_norm := target_hour % 24) - current_h
    if delta_h < 0:
        delta_h += 24
    minutes = delta_h * 60 - current_m
    if minutes < 0:
        minutes += 24 * 60
    # inside the target hour already -> negative offset into it
    if target_h_norm == current_h:
        return -current_m
    return minutes


def build_forecast(now: datetime, peak_hour: int | None, current_score: float) -> dict | None:
    """
    Turn a peak hour into a display-ready forecast, or None if we should
    stay quiet.

    Returns:
      { "state": "peaking_now" | "building" ,
        "minutes_to_peak": int|None,
        "peak_hour": int,
        "label": str }
    """
    if peak_hour is None:
        return None

    mins = minutes_until_hour(now, peak_hour)

    # Inside the peak hour, or just about to enter it
    if -PEAKING_NOW_WINDOW <= mins <= PEAKING_NOW_WINDOW:
        return {
            "state": "peaking_now",
            "minutes_to_peak": 0,
            "peak_hour": peak_hour,
            "label": "PEAKING NOW",
        }

    # Already past the peak hour for tonight: say nothing rather than
    # promise a peak ~23h away.
    if mins < 0 or mins > MAX_LOOKAHEAD_MINUTES:
        return None

    rounded = int(round(mins / 10.0) * 10) or 10
    if rounded >= 60:
        hours = rounded / 60
        human = f"{hours:.1f}".rstrip("0").rstrip(".")
        label = f"PEAKS IN ~{human}H"
    else:
        label = f"PEAKS IN ~{rounded} MIN"

    return {
        "state": "building",
        "minutes_to_peak": rounded,
        "peak_hour": peak_hour,
        "label": label,
    }


async def compute_peak_forecast(venue_id: str, current_score: float, now: datetime | None = None):
    """
    DB-backed forecast for one venue. Returns None when history is too thin.
    """
    from app.config import db  # local import keeps this module unit-testable

    now = now or datetime.now(timezone.utc)
    since = now - timedelta(weeks=LOOKBACK_WEEKS)
    weekend = is_weekend_night(now)

    ratings = await db.ratings.find(
        {"venue_id": venue_id, "timestamp": {"$gte": since}},
        {"_id": 0, "timestamp": 1, "vibe_score": 1},
    ).to_list(4000)

    buckets: dict = {}
    for r in ratings:
        ts = r.get("timestamp")
        if not isinstance(ts, datetime):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        # only compare like with like: weekend nights vs weekday nights
        if is_weekend_night(ts) != weekend:
            continue
        h = lagos_hour(ts)
        total, count = buckets.get(h, (0.0, 0))
        buckets[h] = (total + float(r.get("vibe_score", 0) or 0), count + 1)

    hour_stats = {h: (total / count, count) for h, (total, count) in buckets.items() if count}
    return build_forecast(now, peak_hour_from_history(hour_stats), current_score)
