from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.workers.scrape_worker import ScrapeWorker
from app.workers.notification_worker import NotificationWorker


# Global scheduler instance
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI startup and shutdown events.
    Handles database initialization and scheduler management.
    """
    print("\n" + "="*60)
    print("[STARTUP] Initializing Job Scraper Service")
    print("="*60 + "\n")

    # Create database tables
    print("[STARTUP] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("[STARTUP] Database tables created")

    # Initialize workers
    scrape_worker = ScrapeWorker()
    notification_worker = NotificationWorker()

    # Configure scheduled jobs
    print("[STARTUP] Configuring scheduled jobs...")

    # Scrape all career pages every N hours
    scheduler.add_job(
        scrape_worker.run_scrape_pipeline,
        trigger=CronTrigger(hour=f"*/{settings.scrape_interval_hours}"),
        id="scrape_career_pages",
        name="Scrape all active career pages",
        replace_existing=True
    )
    print(f"[STARTUP] Scheduled scrape job: every {settings.scrape_interval_hours} hours")

    # Process notification queue every N minutes
    scheduler.add_job(
        notification_worker.run_notification_pipeline,
        trigger=CronTrigger(minute=f"*/{settings.notification_interval_minutes}"),
        id="process_notifications",
        name="Process notification queue",
        replace_existing=True
    )
    print(f"[STARTUP] Scheduled notification job: every {settings.notification_interval_minutes} minutes")

    # Start the scheduler
    scheduler.start()
    print("[STARTUP] Scheduler started")

    print("\n" + "="*60)
    print("[STARTUP] Job Scraper Service is ready")
    print("="*60 + "\n")

    yield  # Application runs here

    # Shutdown
    print("\n" + "="*60)
    print("[SHUTDOWN] Shutting down Job Scraper Service")
    print("="*60 + "\n")

    scheduler.shutdown()
    print("[SHUTDOWN] Scheduler stopped")
    print("[SHUTDOWN] Goodbye!")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Job scraper service that monitors career pages and notifies users of new opportunities",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """
    Basic health check endpoint.
    """
    return {
        "message": "Job Scraper Service is running",
        "app_name": settings.app_name,
        "environment": settings.app_env
    }


@app.get("/health")
async def health_check():
    """
    Detailed health check endpoint with database and scheduler status.
    """
    # Check database connection
    db_status = "healthy"
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check scheduler status
    scheduler_status = "running" if scheduler.running else "stopped"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "scheduler": scheduler_status,
        "scheduled_jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None
            }
            for job in scheduler.get_jobs()
        ]
    }


@app.post("/trigger/scrape")
async def trigger_scrape():
    """
    Manually trigger a scrape of all active career pages.
    Useful for testing without waiting for the scheduled job.
    """
    print("\n[MANUAL TRIGGER] Scrape pipeline triggered via API")

    scrape_worker = ScrapeWorker()

    # Run in background (non-blocking)
    scheduler.add_job(
        scrape_worker.run_scrape_pipeline,
        id="manual_scrape",
        name="Manual scrape trigger",
        replace_existing=True
    )

    return {
        "message": "Scrape pipeline triggered",
        "status": "running"
    }


@app.post("/trigger/notifications")
async def trigger_notifications():
    """
    Manually trigger processing of the notification queue.
    Useful for testing without waiting for the scheduled job.
    """
    print("\n[MANUAL TRIGGER] Notification processing triggered via API")

    notification_worker = NotificationWorker()

    # Run in background (non-blocking)
    scheduler.add_job(
        notification_worker.run_notification_pipeline,
        id="manual_notifications",
        name="Manual notification trigger",
        replace_existing=True
    )

    return {
        "message": "Notification processing triggered",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
