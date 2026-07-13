"""Closed-form tests for the honest-scarcity surge policy."""
from datetime import datetime, timedelta, timezone

from app.services import surge_policy as sp


NOW = datetime(2026, 7, 13, 22, 0, tzinfo=timezone.utc)


# ── Presence damping ─────────────────────────────────────────────────────────

def test_present_tap_counts_fully():
    assert sp.presence_weight(True) == 1.0


def test_remote_tap_is_damped():
    assert sp.presence_weight(False) == sp.REMOTE_TAP_WEIGHT
    assert sp.REMOTE_TAP_WEIGHT < 0.5  # remote hype must not drive levels


# ── ELECTRIC corroboration gate ──────────────────────────────────────────────

def test_gate_closed_without_enough_present_tappers():
    assert not sp.electric_gate_open(sp.MIN_PRESENT_TAPPERS - 1, hot_ratings_30m=3)


def test_gate_closed_without_hot_vibe_check():
    assert not sp.electric_gate_open(sp.MIN_PRESENT_TAPPERS + 5, hot_ratings_30m=0)


def test_gate_open_with_bodies_and_corroboration():
    assert sp.electric_gate_open(sp.MIN_PRESENT_TAPPERS, hot_ratings_30m=1)


def test_closed_gate_caps_charge_below_electric():
    capped = sp.apply_electric_gate(1.0, gate_open=False)
    assert capped == sp.ELECTRIC_CAP
    assert capped < sp.ELECTRIC_THRESHOLD


def test_open_gate_passes_charge_through():
    assert sp.apply_electric_gate(0.95, gate_open=True) == 0.95


def test_gate_never_touches_sub_electric_charge():
    assert sp.apply_electric_gate(0.5, gate_open=False) == 0.5


# ── Sustain window ───────────────────────────────────────────────────────────

def test_below_threshold_resets_candidacy():
    charge, since = sp.sustain_state(0.5, NOW - timedelta(minutes=20), NOW)
    assert charge == 0.5
    assert since is None


def test_first_crossing_starts_candidacy_and_caps():
    charge, since = sp.sustain_state(0.9, None, NOW)
    assert charge == sp.ELECTRIC_CAP
    assert since == NOW


def test_still_capped_before_sustain_elapses():
    started = NOW - timedelta(minutes=sp.SUSTAIN_MINUTES - 1)
    charge, since = sp.sustain_state(0.9, started, NOW)
    assert charge == sp.ELECTRIC_CAP
    assert since == started


def test_electric_after_sustained_hold():
    started = NOW - timedelta(minutes=sp.SUSTAIN_MINUTES)
    charge, since = sp.sustain_state(0.9, started, NOW)
    assert charge == 0.9
    assert since == started


def test_burst_spike_then_drop_never_reaches_electric():
    # spike crosses threshold -> capped, candidacy starts
    charge, since = sp.sustain_state(1.0, None, NOW)
    assert charge < sp.ELECTRIC_THRESHOLD
    # decays below threshold 5 minutes later -> candidacy gone
    charge, since = sp.sustain_state(0.7, since, NOW + timedelta(minutes=5))
    assert since is None
