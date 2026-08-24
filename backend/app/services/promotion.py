"""
Paid promotion, kept strictly separate from the energy score.

The commercial invariant of the whole product lives here: money buys reach
(radius), position (chart placement) and a visible badge. It never buys a
higher number.

The moment a venue can purchase a better energy reading, the signal stops
being worth anything to the venues, brands and partners who pay for it
precisely because it is true. Promotion is therefore rendered the way a
sponsored search result is rendered: clearly marked, never disguised as
earned energy.

Pure functions only, no DB, so the invariant is unit-testable.
"""
from datetime import datetime, timezone

# Which sponsored slot each tier buys. None means reach and badge only.
TIER_CHART_PLACEMENT = {
    "spark": None,
    "flare": 3,
    "supernova": 1,
}


def compute_promotion(venue: dict) -> dict:
    """
    Return the paid-placement state for a venue.

    Fails closed: anything unparseable, missing or expired reads as
    not promoted, so a broken timestamp can never grant free promotion.
    """
    tier = venue.get("active_pulse_tier")
    expires = venue.get("pulse_expires_at")
    if not tier or not expires:
        return {"is_promoted": False}

    if isinstance(expires, str):
        try:
            expires = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        except ValueError:
            return {"is_promoted": False}
    if not isinstance(expires, datetime):
        return {"is_promoted": False}
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= datetime.now(timezone.utc):
        return {"is_promoted": False}

    return {
        "is_promoted": True,
        "promoted_tier": tier,
        "promoted_until": expires.isoformat(),
        "chart_placement": TIER_CHART_PLACEMENT.get(tier),
        "label": "SPONSORED",
    }
