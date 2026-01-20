from typing import List
from sqlalchemy.orm import Session
from app.models import JobPosting, User, NotificationQueue
from datetime import datetime


class MatchingService:
    async def find_matching_users(self, job: JobPosting, db: Session) -> List[User]:
        """
        Find all users whose preferences match the given job posting.

        Args:
            job: JobPosting instance
            db: Database session

        Returns:
            List of User instances that match the job
        """
        print(f"[MATCHING] Finding users for job: {job.title}")

        # Get all active users
        all_users = db.query(User).filter(User.is_active == True).all()

        matching_users = []
        for user in all_users:
            if await self.check_user_match(user, job):
                matching_users.append(user)

        print(f"[MATCHING] Found {len(matching_users)} matching users")
        return matching_users

    async def check_user_match(self, user: User, job: JobPosting) -> bool:
        """
        Check if a job matches a user's preferences.
        Only checks fields that user has specified in preferences.

        Args:
            user: User instance with preferences
            job: JobPosting instance

        Returns:
            True if job matches user preferences, False otherwise
        """
        preferences = user.preferences or {}

        # If user has no preferences at all, they get all jobs
        if not preferences:
            return True

        # Check location preferences - ONLY if user specified location preference
        preferred_locations = preferences.get("locations", [])
        if preferred_locations:
            if not job.location:
                # User wants specific locations but job has no location
                return False

            location_match = any(
                self._location_matches(job.location, pref_location)
                for pref_location in preferred_locations
            )
            if not location_match:
                return False

        # Check job type preferences - ONLY if user specified job type preference
        preferred_job_types = preferences.get("job_types", [])
        if preferred_job_types:
            if not job.job_type:
                # User wants specific job types but job has no job type
                return False

            if job.job_type not in preferred_job_types:
                return False

        # Check experience level preferences - ONLY if user specified experience level preference
        preferred_experience_levels = preferences.get("experience_levels", [])
        if preferred_experience_levels:
            if not job.experience_level:
                # User wants specific experience levels but job has no experience level
                return False

            if job.experience_level not in preferred_experience_levels:
                return False

        # Check company preferences - ONLY if user follows specific companies
        preferred_company_ids = preferences.get("company_ids", [])
        if preferred_company_ids:
            if str(job.career_page_id) not in preferred_company_ids:
                return False

        # All specified preferences matched
        return True

    def _location_matches(self, job_location: str, preferred_location: str) -> bool:
        """
        Check if job location matches preferred location.
        Supports exact match and "Remote" keyword matching.

        Args:
            job_location: Job location string
            preferred_location: User's preferred location string

        Returns:
            True if locations match
        """
        job_location = job_location.lower().strip()
        preferred_location = preferred_location.lower().strip()

        # Exact match
        if job_location == preferred_location:
            return True

        # Remote matching
        if "remote" in preferred_location and "remote" in job_location:
            return True

        # Partial match (e.g., "San Francisco" matches "San Francisco, CA")
        if preferred_location in job_location or job_location in preferred_location:
            return True

        return False

    async def queue_notifications(self, users: List[User], job: JobPosting, db: Session):
        """
        Create notification queue entries for matched users.

        Args:
            users: List of User instances to notify
            job: JobPosting instance
            db: Database session
        """
        print(f"[MATCHING] Queueing notifications for {len(users)} users")

        for user in users:
            # Get user's notification channels
            channels = user.notification_channels or ["email"]
            channels_str = ",".join(channels)

            # Create notification queue entry
            queue_entry = NotificationQueue(
                user_id=user.id,
                job_posting_id=job.id,
                channels=channels_str,
                priority=0,
                created_at=datetime.utcnow()
            )

            db.add(queue_entry)

        db.commit()
        print(f"[MATCHING] Queued notifications for {len(users)} users")
