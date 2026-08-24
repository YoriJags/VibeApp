"""
Paid promotion is placement, never score.

These tests guard the commercial invariant: a venue can buy reach, position
and a badge, but the energy number stays earned. If someone re-adds a paid
boost to the score, the last test here fails loudly.
"""
from datetime import datetime, timedelta, timezone

from app.services.promotion import compute_promotion


def future(hours=2):
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def past(hours=2):
    return datetime.now(timezone.utc) - timedelta(hours=hours)


# ── Not promoted ─────────────────────────────────────────────────────────────

def test_plain_venue_is_not_promoted():
    assert compute_promotion({})["is_promoted"] is False


def test_tier_without_expiry_is_not_promoted():
    assert compute_promotion({"active_pulse_tier": "flare"})["is_promoted"] is False


def test_expired_promotion_is_not_promoted():
    v = {"active_pulse_tier": "supernova", "pulse_expires_at": past()}
    assert compute_promotion(v)["is_promoted"] is False


def test_unparseable_expiry_fails_closed():
    v = {"active_pulse_tier": "flare", "pulse_expires_at": "not-a-date"}
    assert compute_promotion(v)["is_promoted"] is False


# ── Promoted ─────────────────────────────────────────────────────────────────

def test_active_promotion_is_flagged_and_labelled():
    v = {"active_pulse_tier": "flare", "pulse_expires_at": future()}
    p = compute_promotion(v)
    assert p["is_promoted"] is True
    assert p["promoted_tier"] == "flare"
    assert p["label"] == "SPONSORED"   # must be visibly marked as paid


def test_tiers_map_to_chart_placement_not_score():
    assert compute_promotion({"active_pulse_tier": "supernova", "pulse_expires_at": future()})["chart_placement"] == 1
    assert compute_promotion({"active_pulse_tier": "flare", "pulse_expires_at": future()})["chart_placement"] == 3
    assert compute_promotion({"active_pulse_tier": "spark", "pulse_expires_at": future()})["chart_placement"] is None


def test_naive_expiry_is_treated_as_utc():
    naive = (datetime.now(timezone.utc) + timedelta(hours=3)).replace(tzinfo=None)
    v = {"active_pulse_tier": "spark", "pulse_expires_at": naive}
    assert compute_promotion(v)["is_promoted"] is True


def test_promotion_payload_never_carries_a_score():
    """The commercial invariant: nothing in the promotion payload can move
    the energy number. No score, no boost, no multiplier fields."""
    p = compute_promotion({"active_pulse_tier": "supernova", "pulse_expires_at": future()})
    forbidden = {"glow_boost", "score", "current_vibe_score", "boost", "multiplier"}
    assert not (forbidden & set(p)), f"paid promotion leaked into scoring: {forbidden & set(p)}"


def test_scoring_engine_has_no_paid_boost_in_the_math():
    """
    Guard against regression: the scoring engine must not reference a paid
    boost at all. Read from disk rather than importing, so this runs without
    a database.
    """
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "app" / "services" / "vibe.py").read_text(encoding="utf-8")
    offending = [
        line.strip() for line in src.splitlines()
        if "glow_boost" in line and not line.strip().startswith("#")
    ]
    assert not offending, f"paid boost is back in the scoring engine: {offending}"
