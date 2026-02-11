#!/usr/bin/env python3
"""LeadPilot CLI — run the outreach pipeline."""

import argparse
import logging
import sys

from dotenv import load_dotenv


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="LeadPilot — AI-powered cold outreach preview site generator"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Max number of leads to process"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Score websites only — no preview generation, deployment, or emails",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable debug logging"
    )
    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    from leadpilot.agent import run_pipeline

    run_pipeline(limit=args.limit, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
