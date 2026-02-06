"""
Seed the database with test leads for development.
Usage: python -m scripts.seed_test_leads
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, SessionLocal
from app.services.pipeline import run_pipeline


async def main():
    print("Initializing database...")
    init_db()

    db = SessionLocal()
    try:
        print("Running mock pipeline to seed test leads...")
        stats = await run_pipeline(
            db,
            niche="plumber",
            location="Amsterdam, Netherlands",
            limit=15,
            campaign_name="Test Campaign — Plumbers Amsterdam",
        )
        print(f"\nDone! Pipeline results:")
        print(f"  Scraped:  {stats['scraped']}")
        print(f"  Analyzed: {stats['analyzed']}")
        print(f"  Previews: {stats['previews_generated']}")
        print(f"  Emails:   {stats['emails_drafted']}")
        if stats["errors"]:
            print(f"  Errors:   {len(stats['errors'])}")
            for err in stats["errors"]:
                print(f"    - {err}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
