"""
Demo Energy Seeder — make the map glow for a live demo.

Inserts realistic scout ratings (last ~45 min) from flagged demo users, then
recomputes each venue's aggregate via the SAME calculate_venue_aggregate the
ratings route uses — so scores, labels, and velocity are indistinguishable
from organic activity.

Safe by design:
  - Only touches ratings from user_ids prefixed "demo-scout-" (re-runnable;
    each run clears its previous demo ratings first).
  - Never deletes venues, real users, or real ratings.

Usage (from backend/):
    MONGO_URL=... DB_NAME=... python scripts/demo_energy.py [--wipe]

    --wipe  remove all demo ratings + demo users and recompute aggregates
            (run this after the demo to return to organic state)
"""
import asyncio
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import db  # noqa: E402
from app.services.vibe import calculate_vibe_score, calculate_venue_aggregate  # noqa: E402

DEMO_PREFIX = "demo-scout-"

SCOUTS = [
    ("Tobi", "IGNITER"), ("Amara", "STEADY"), ("Seun", "HEAVY"),
    ("Zara", "STEADY"), ("Emeka", "IGNITER"), ("Dami", "WARMING"),
    ("Kemi", "STEADY"), ("Femi", "HEAVY"), ("Nneka", "STEADY"), ("Tunde", "IGNITER"),
]

# Energy profile per venue tier: (energy choices, capacity choices, n ratings)
PROFILES = {
    "peak":    (["peak", "peak", "lit"],       ["full", "full", "vibrant"], (6, 9)),
    "hot":     (["lit", "lit", "peak"],        ["vibrant", "full"],         (4, 7)),
    "warm":    (["warming", "lit"],            ["vibrant", "sparse"],       (3, 5)),
    "chill":   (["chill", "warming"],          ["sparse", "vibrant"],       (2, 3)),
    "quiet":   (["quiet", "chill"],            ["sparse"],                  (1, 2)),
}


def tier_for(score: float) -> str:
    if score >= 80:
        return "peak"
    if score >= 65:
        return "hot"
    if score >= 45:
        return "warm"
    if score >= 25:
        return "chill"
    return "quiet"


async def ensure_demo_users():
    # Clean slate: earlier partial runs may have inserted demo users missing
    # fields required by unique indexes (phone, username).
    await db.users.delete_many({"id": {"$regex": f"^{DEMO_PREFIX}"}})
    for i, (name, sig) in enumerate(SCOUTS):
        uid = f"{DEMO_PREFIX}{i}"
        await db.users.update_one(
            {"id": uid},
            {"$setOnInsert": {
                "id": uid,
                "name": name,
                "email": f"{uid}@demo.viibe.app",
                "phone": f"+23480000000{i:02d}",
                "username": f"{name.lower()}_demo{i}",
                "is_demo": True,
                "clout_points": random.randint(120, 900),
                "total_ratings": random.randint(8, 60),
                "rating_accuracy_score": round(random.uniform(0.7, 0.95), 2),
                "solo_signature": sig,
                "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(10, 90)),
            }},
            upsert=True,
        )


async def clear_demo_ratings():
    res = await db.ratings.delete_many({"user_id": {"$regex": f"^{DEMO_PREFIX}"}})
    return res.deleted_count


async def seed():
    await ensure_demo_users()
    cleared = await clear_demo_ratings()
    print(f"Cleared {cleared} previous demo ratings")

    venues = await db.venues.find({}, {"_id": 0}).to_list(100)
    now = datetime.now(timezone.utc)
    total = 0

    for venue in venues:
        tier = tier_for(venue.get("current_vibe_score", 50))
        energies, capacities, (lo, hi) = PROFILES[tier]
        n = random.randint(lo, hi)
        scouts = random.sample(range(len(SCOUTS)), min(n, len(SCOUTS)))

        for k, scout_idx in enumerate(scouts):
            energy = random.choice(energies)
            capacity = random.choice(capacities)
            gate = random.choices(["clear", "slow", "blocked"], weights=[6, 3, 1])[0]
            vibe_score = calculate_vibe_score(energy, capacity, gate)
            # Recent-weighted timestamps: newest ratings cluster in last 15 min
            minutes_ago = random.uniform(1, 15) if k < n // 2 else random.uniform(15, 45)
            ts = now - timedelta(minutes=minutes_ago)
            await db.ratings.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": f"{DEMO_PREFIX}{scout_idx}",
                "venue_id": venue["id"],
                "energy": energy,
                "capacity": capacity,
                "gate": gate,
                "venue_specific": None,
                "photo_base64": None,
                "timestamp": ts,
                "is_correction": False,
                "vibe_score": vibe_score,
                "synced": True,
                "taxonomy_id": None,
                "vibe_note": None,
                "provisional": False,
                "provisional_until": None,
                "credibility_weight": round(random.uniform(0.75, 1.0), 2),
                "signal_token": f"demo-{uuid.uuid4().hex[:12]}",
            })
            total += 1

        aggregate = await calculate_venue_aggregate(venue["id"])
        await db.venues.update_one({"id": venue["id"]}, {"$set": aggregate})
        updated = await db.venues.find_one({"id": venue["id"]}, {"_id": 0, "current_vibe_score": 1, "energy_level": 1, "vibe_velocity": 1})
        print(f"  {venue['name']:<28} tier={tier:<6} ratings=+{len(scouts)}  -> score={updated['current_vibe_score']} {updated.get('energy_level')}/{updated.get('vibe_velocity')}")

    print(f"\nSeeded {total} demo ratings across {len(venues)} venues")


async def wipe():
    cleared = await clear_demo_ratings()
    deleted = await db.users.delete_many({"is_demo": True})
    venues = await db.venues.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(100)
    for venue in venues:
        aggregate = await calculate_venue_aggregate(venue["id"])
        await db.venues.update_one({"id": venue["id"]}, {"$set": aggregate})
    print(f"Wiped {cleared} demo ratings, {deleted.deleted_count} demo users; aggregates recomputed")


if __name__ == "__main__":
    asyncio.run(wipe() if "--wipe" in sys.argv else seed())
