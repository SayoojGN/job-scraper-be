from typing import List
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import SessionLocal
from app.models import CareerPage, JobPosting
from app.services.scraper_service import ScraperService
from app.services.llm_service import LLMService
from app.services.matching_service import MatchingService
from app.utils import generate_job_external_id


class ScrapeWorker:
    """
    Worker that orchestrates the complete pipeline:
    1. Scrape career pages
    2. Normalize with LLM
    3. Check for duplicates
    4. Save new jobs to database
    5. Match with users and queue notifications
    """

    def __init__(self):
        self.scraper = ScraperService()
        self.llm = LLMService()
        self.matcher = MatchingService()

    async def run_scrape_pipeline(self):
        """
        Run the complete scrape pipeline for all active career pages.
        """
        print("\n" + "="*60)
        print("[WORKER] Starting scrape pipeline")
        print("="*60 + "\n")

        db = SessionLocal()

        try:
            # Get all active career pages
            career_pages = db.query(CareerPage).filter(CareerPage.is_active == True).all()

            if not career_pages:
                print("[WORKER] No active career pages found")
                return

            print(f"[WORKER] Found {len(career_pages)} active career pages")

            for career_page in career_pages:
                await self.scrape_single_career_page(career_page, db)

            print("\n" + "="*60)
            print("[WORKER] Scrape pipeline complete")
            print("="*60 + "\n")

        except Exception as e:
            print(f"[WORKER] Error in scrape pipeline: {str(e)}")
        finally:
            db.close()

    async def scrape_single_career_page(self, career_page: CareerPage, db: Session):
        """
        Run the complete pipeline for a single career page.

        This function handles:
        1. Scraping the career page URL
        2. LLM normalization of job data
        3. Duplicate detection
        4. Saving new jobs to database
        5. Matching with user preferences
        6. Queueing notifications for matched users

        Args:
            career_page: CareerPage instance
            db: Database session
        """
        print(f"\n[WORKER] Processing {career_page.company_name}")
        print("-" * 60)

        try:
            # Step 1: Scrape the career page
            raw_jobs = await self.scraper.scrape_career_page(career_page, db)

            if not raw_jobs:
                print(f"[WORKER] No jobs scraped from {career_page.company_name}")
                return

            # Step 2: Normalize each raw job with LLM
            all_normalized_jobs = []
            for raw_job in raw_jobs:
                normalized_jobs = await self.llm.normalize_job_data(raw_job)
                all_normalized_jobs.extend(normalized_jobs)

            if not all_normalized_jobs:
                print(f"[WORKER] No jobs extracted by LLM from {career_page.company_name}")
                return

            print(f"[WORKER] LLM extracted {len(all_normalized_jobs)} jobs total")

            # Step 3: Check for duplicates and save new jobs
            new_jobs_count = 0
            for normalized_job in all_normalized_jobs:
                new_job = await self.save_new_job(normalized_job, career_page.id, db)
                if new_job:
                    new_jobs_count += 1

                    # Step 4: Match with users and queue notifications
                    await self.process_new_job_notifications(new_job, db)

            print(f"[WORKER] Saved {new_jobs_count} new jobs from {career_page.company_name}")

        except Exception as e:
            print(f"[WORKER] Error processing {career_page.company_name}: {str(e)}")

    async def save_new_job(self, normalized_job: dict, career_page_id: str, db: Session) -> JobPosting:
        """
        Save a normalized job to the database if it's new.

        Args:
            normalized_job: Normalized job dictionary
            career_page_id: UUID of career page
            db: Database session

        Returns:
            JobPosting instance if new, None if duplicate
        """
        # Generate external_id for deduplication
        external_id = generate_job_external_id(
            career_page_id=str(career_page_id),
            job_url=normalized_job.get("url", ""),
            title=normalized_job.get("title", "")
        )

        # Check if job already exists
        existing_job = db.query(JobPosting).filter(
            JobPosting.external_id == external_id
        ).first()

        if existing_job:
            # Update last_seen_at for existing job
            existing_job.last_seen_at = datetime.utcnow()
            existing_job.is_active = True
            db.commit()
            return None

        # Create new job posting
        new_job = JobPosting(
            career_page_id=career_page_id,
            external_id=external_id,
            title=normalized_job.get("title"),
            location=normalized_job.get("location"),
            job_type=normalized_job.get("job_type"),
            experience_level=normalized_job.get("experience_level"),
            description=normalized_job.get("description"),
            requirements=normalized_job.get("requirements"),
            url=normalized_job.get("url"),
            raw_data=normalized_job.get("raw_data", {}),
            normalized_at=datetime.utcnow(),
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            is_active=True
        )

        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        print(f"[WORKER] New job saved: {new_job.title}")
        return new_job

    async def process_new_job_notifications(self, job: JobPosting, db: Session):
        """
        Match a new job with users and queue notifications.

        Args:
            job: JobPosting instance
            db: Database session
        """
        # Find matching users
        matching_users = await self.matcher.find_matching_users(job, db)

        if not matching_users:
            print(f"[WORKER] No matching users for job: {job.title}")
            return

        # Queue notifications for matching users
        await self.matcher.queue_notifications(matching_users, job, db)
        print(f"[WORKER] Queued notifications for {len(matching_users)} users")
