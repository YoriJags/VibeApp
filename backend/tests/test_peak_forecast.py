"""Closed-form tests for the peak forecast (countdown to a venue's best hour)."""
from datetime import datetime, timezone

from app.services import peak_forecast as pf


def at(hour_utc: int, minute: int = 0, day: int = 17):
    """2026-07-17 is a Friday -> weekend night."""
    return datetime(2026, 7, day, hour_utc, minute, tzinfo=timezone.utc)


# ── Lagos time + day type ────────────────────────────────────────────────────

def test_lagos_hour_is_utc_plus_one():
    assert pf.lagos_hour(at(22)) == 23
    assert pf.lagos_hour(at(23)) == 0      # wraps past midnight


def test_weekend_detection():
    assert pf.is_weekend_night(at(22, day=17))       # Friday
    assert not pf.is_weekend_night(at(22, day=15))   # Wednesday


# ── Peak hour selection ──────────────────────────────────────────────────────

def test_picks_highest_scoring_hour():
    stats = {22: (60.0, 5), 23: (88.0, 6), 1: (70.0, 4)}
    assert pf.peak_hour_from_history(stats) == 23


def test_ignores_hours_with_too_few_samples():
    # hour 2 scores highest but only has 1 rating behind it
    stats = {23: (70.0, 6), 2: (99.0, 1), 22: (55.0, 4)}
    assert pf.peak_hour_from_history(stats) == 23


def test_silent_when_no_hour_has_enough_samples():
    stats = {23: (90.0, 1), 0: (85.0, 2)}
    assert pf.peak_hour_from_history(stats) is None


def test_silent_when_total_history_is_thin():
    # every bucket clears the per-hour bar but the night total is too small
    stats = {23: (90.0, 3), 0: (80.0, 3)}   # 6 total < MIN_TOTAL_SAMPLES (8)
    assert pf.peak_hour_from_history(stats) is None


# ── Minutes until ────────────────────────────────────────────────────────────

def test_minutes_until_later_tonight():
    # 21:00 Lagos, peak at 23:00 -> 120 minutes
    assert pf.minutes_until_hour(at(20, 0), 23) == 120


def test_minutes_until_wraps_past_midnight():
    # 23:40 Lagos, peak at 01:00 -> 80 minutes (not negative)
    assert pf.minutes_until_hour(at(22, 40), 1) == 80


def test_inside_the_peak_hour_is_negative_offset():
    # 23:25 Lagos, peak hour 23 -> 25 minutes into it
    assert pf.minutes_until_hour(at(22, 25), 23) == -25


# ── Forecast shaping ─────────────────────────────────────────────────────────

def test_no_peak_hour_means_no_forecast():
    assert pf.build_forecast(at(21), None, 50.0) is None


def test_building_forecast_rounds_to_ten_minutes():
    f = pf.build_forecast(at(21, 18), 23, 60.0)   # 22:18 Lagos, peak 23:00 -> 42 min
    assert f["state"] == "building"
    assert f["minutes_to_peak"] == 40
    assert f["label"] == "PEAKS IN ~40 MIN"


def test_peaking_now_inside_window():
    f = pf.build_forecast(at(22, 10), 23, 88.0)   # 23:10 Lagos, peak hour 23
    assert f["state"] == "peaking_now"
    assert f["label"] == "PEAKING NOW"


def test_hours_are_humanised():
    f = pf.build_forecast(at(19, 0), 23, 40.0)    # 20:00 Lagos, peak 23:00
    assert f["label"].endswith("H")               # "PEAKS IN ~3H"


def test_silent_when_peak_is_too_far_away():
    # 02:00 Lagos, peak hour 23 -> 21h out, well past MAX_LOOKAHEAD
    assert pf.build_forecast(at(1, 0), 23, 30.0) is None


def test_never_promises_a_peak_that_already_passed():
    # peak hour 22, now 01:00 Lagos -> would be 21h away, stay quiet
    assert pf.build_forecast(at(0, 0), 22, 25.0) is None
