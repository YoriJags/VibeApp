"""
Venue Orbit — live watchers.

People who want to be there but can't: users actively monitoring a venue's
energy from outside the geofence. The app pings while a venue's detail screen
is open; the venue sees its gravitational pull ("43 watching you right now").

  watching_now     = distinct users pinging in the last WATCH_WINDOW
  watching_remote  = watchers outside the geofence (the demand-pressure number)
  watching_present = watchers verified inside the geofence

Pings are auth-required (no anonymous inflation) and idempotent per
(venue, user) — one doc, refreshed timestamp.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from app.config import db
from app.models import Coordinates
from app.services.auth import require_auth
from app.services.vibe import is_within_geofence

router = APIRouter(tags=["orbit"])

WATCH_WINDOW_MINUTES = 2


@router.post("/venues/{venue_id}/orbit/ping")
async def orbit_ping(
    venue_id: str,
    coordinates: Optional[Coordinates] = Body(default=None, embed=True),
    user: dict = Depends(require_auth),
):
    """Heartbeat while a user has this venue's energy feed open."""
    venue = await db.venues.find_one({"id": venue_id})
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    is_present = False
    if coordinates is not None and venue.get("coordinates"):
        is_present = is_within_geofence(
            coordinates,
            Coordinates(**venue["coordinates"]),
            radius_m=venue.get("geofence_radius_m", 100),
        )

    await db.venue_orbit.update_one(
        {"venue_id": venue_id, "user_id": user["id"]},
        {"$set": {
            "venue_id": venue_id,
            "user_id": user["id"],
            "present": is_present,
            "ts": datetime.now(timezone.utc),
        }},
        upsert=True,
    )
    return await _orbit_counts(venue_id)


@router.get("/venues/{venue_id}/orbit")
async def get_orbit(venue_id: str):
    """Public: who's watching this venue right now (counts only, never identities)."""
    venue = await db.venues.find_one({"id": venue_id})
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return await _orbit_counts(venue_id)


async def _orbit_counts(venue_id: str) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=WATCH_WINDOW_MINUTES)
    watchers = await db.venue_orbit.find(
        {"venue_id": venue_id, "ts": {"$gte": cutoff}},
        {"_id": 0, "user_id": 1, "present": 1},
    ).to_list(5000)
    present = sum(1 for w in watchers if w.get("present"))
    return {
        "watching_now": len(watchers),
        "watching_remote": len(watchers) - present,
        "watching_present": present,
        "window_minutes": WATCH_WINDOW_MINUTES,
    }
