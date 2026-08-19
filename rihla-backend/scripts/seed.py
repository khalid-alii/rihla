"""Seed script — creates the CITYU-2026 / City University Cyberjaya Campus community.

Run once against a fresh DB:
    cd rihla-backend
    python -m scripts.seed
"""
import sys
import os

# Ensure the rihla-backend/ directory is on the path when run as a module.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.community import Community
import app.models  # noqa: F401 — registers all models with Base


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.query(Community).filter(Community.code == "CITYU-2026").first()
        if existing:
            print("[seed] Community CITYU-2026 already exists — skipping.")
            return

        community = Community(
            name="City University Cyberjaya Campus",
            code="CITYU-2026",
            active=True,
        )
        db.add(community)
        db.commit()
        db.refresh(community)
        print(f"[seed] Created: {community.name} (code={community.code}, id={community.id})")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
