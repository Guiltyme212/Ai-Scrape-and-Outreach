"""
APScheduler setup for batch processing jobs.
Runs pipeline on a schedule (e.g., every Monday at 9am).
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import get_settings

scheduler = AsyncIOScheduler()


def init_scheduler():
    """Initialize and start the scheduler with default jobs."""
    # Jobs will be added in Phase 5 when automation is implemented
    # Example future job:
    # scheduler.add_job(
    #     run_scheduled_pipeline,
    #     "cron",
    #     day_of_week="mon",
    #     hour=9,
    #     minute=0,
    #     id="weekly_pipeline",
    # )
    scheduler.start()


def shutdown_scheduler():
    """Gracefully shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
