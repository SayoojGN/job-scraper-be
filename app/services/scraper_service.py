from typing import List, Dict
from datetime import datetime
from firecrawl import FirecrawlApp
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CareerPage


class ScraperService:
    def __init__(self):
        self.firecrawl = FirecrawlApp(api_key=settings.firecrawl_api_key)

    async def scrape_career_page(self, career_page: CareerPage, db: Session) -> List[Dict]:
        """
        Scrape a career page and return raw job listings.

        Args:
            career_page: CareerPage model instance
            db: Database session

        Returns:
            List of raw job data dictionaries from Firecrawl (in memory, not saved to DB yet)
        """
        print(f"[SCRAPER] Starting scrape for {career_page.company_name} ({career_page.url})")

        try:
            # Use Firecrawl to scrape the career page
            # For multi-page sites, use crawl(); for single page, use scrape()
            scrape_config = career_page.scrape_config or {}

            if scrape_config.get("multi_page", False):
                # Crawl multiple pages (handles pagination automatically)
                result = self.firecrawl.crawl_url(
                    career_page.url,
                    params={
                        "limit": scrape_config.get("page_limit", 10),
                        "scrapeOptions": {"formats": ["markdown", "html"]}
                    }
                )
                raw_jobs = self._extract_jobs_from_crawl(result, career_page)
            else:
                # Single page scrape
                result = self.firecrawl.scrape_url(
                    career_page.url,
                    params={"formats": ["markdown", "html"]}
                )
                raw_jobs = self._extract_jobs_from_scrape(result, career_page)

            print(f"[SCRAPER] Found {len(raw_jobs)} job listings for {career_page.company_name}")

            # Update last_scraped_at
            career_page.last_scraped_at = datetime.utcnow()
            db.commit()

            return raw_jobs

        except Exception as e:
            print(f"[SCRAPER] Error scraping {career_page.company_name}: {str(e)}")
            return []

    def _extract_jobs_from_scrape(self, result: Dict, career_page: CareerPage) -> List[Dict]:
        """
        Extract job listings from single page scrape result.
        This stores the complete Firecrawl response as raw data.

        Args:
            result: Firecrawl scrape result
            career_page: CareerPage instance

        Returns:
            List of job dictionaries with raw Firecrawl data
        """
        # Store the entire Firecrawl result as one job entry
        # The LLM will parse this to extract individual jobs and their fields
        jobs = [{
            "url": career_page.url,
            "career_page_id": str(career_page.id),
            "company_name": career_page.company_name,
            "raw_content": result.get("markdown", ""),
            "html_content": result.get("html", ""),
            "metadata": result.get("metadata", {}),
            "scraped_at": datetime.utcnow().isoformat()
        }]

        return jobs

    def _extract_jobs_from_crawl(self, result: Dict, career_page: CareerPage) -> List[Dict]:
        """
        Extract job listings from multi-page crawl result.
        Each page from the crawl becomes a separate job entry for LLM processing.

        Args:
            result: Firecrawl crawl result
            career_page: CareerPage instance

        Returns:
            List of job dictionaries with raw Firecrawl data
        """
        jobs = []

        # Firecrawl crawl returns a list of pages
        pages = result.get("data", [])

        for page in pages:
            job = {
                "url": page.get("url", career_page.url),
                "career_page_id": str(career_page.id),
                "company_name": career_page.company_name,
                "raw_content": page.get("markdown", ""),
                "html_content": page.get("html", ""),
                "metadata": page.get("metadata", {}),
                "scraped_at": datetime.utcnow().isoformat()
            }
            jobs.append(job)

        return jobs
