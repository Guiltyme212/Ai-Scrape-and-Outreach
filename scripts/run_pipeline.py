"""
CLI runner for the LeadPilot pipeline.
Usage: python -m scripts.run_pipeline --niche "plumber" --city "Amsterdam"
"""

import argparse
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.database import init_db, SessionLocal
from app.services.pipeline import run_pipeline


async def main():
    parser = argparse.ArgumentParser(description="Run LeadPilot pipeline")
    parser.add_argument("--niche", default=None, help="Business niche (e.g. plumber)")
    parser.add_argument("--city", default=None, help="City/location (e.g. Amsterdam)")
    parser.add_argument("--limit", type=int, default=20, help="Number of leads to scrape")
    args = parser.parse_args()

    settings = get_settings()
    niche = args.niche or settings.default_niche
    location = args.city or settings.default_location

    print(f"LeadPilot Pipeline")
    print(f"  Niche:    {niche}")
    print(f"  Location: {location}")
    print(f"  Limit:    {args.limit}")
    print(f"  Mock:     {settings.mock_mode}")
    print()

    init_db()
    db = SessionLocal()

    try:
        stats = await run_pipeline(db, niche, location, args.limit)
        print(f"\nPipeline complete!")
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
