"""
Test script for ScraperService

This script tests the scraper service in isolation to verify:
1. Firecrawl API connection
2. Single page scraping
3. Multi-page crawling
4. Data extraction from scrape results
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.scraper_service import ScraperService
from app.models import CareerPage
from app.database import SessionLocal, init_db
from sqlalchemy.orm import Session


async def test_scraper_single_page():
    """Test scraping a single career page"""
    print("\n" + "="*60)
    print("TEST 1: Single Page Scraping")
    print("="*60)

    db = SessionLocal()
    try:
        # Create a test career page (or use existing one)
        test_career_page = CareerPage(
            company_name="Test Company",
            url="https://jobs.ashbyhq.com/anthropic",  # Example career page
            scrape_config={"multi_page": False},
            is_active=True
        )

        # Check if it already exists
        existing = db.query(CareerPage).filter(CareerPage.url == test_career_page.url).first()
        if existing:
            test_career_page = existing
            print(f"✓ Using existing career page: {test_career_page.company_name}")
        else:
            db.add(test_career_page)
            db.commit()
            db.refresh(test_career_page)
            print(f"✓ Created new career page: {test_career_page.company_name}")

        # Initialize scraper service
        scraper = ScraperService()
        print("✓ ScraperService initialized")

        # Scrape the career page
        print(f"\nScraping URL: {test_career_page.url}")
        raw_jobs = await scraper.scrape_career_page(test_career_page, db)

        # Display results
        print(f"\n✓ Scraping completed!")
        print(f"  - Found {len(raw_jobs)} raw job entries")

        if raw_jobs:
            print("\n" + "-"*60)
            print("Sample Raw Job Data:")
            print("-"*60)
            job = raw_jobs[0]
            print(f"URL: {job.get('url')}")
            print(f"Company: {job.get('company_name')}")
            print(f"Career Page ID: {job.get('career_page_id')}")
            print(f"Raw Content Length: {len(job.get('raw_content', ''))} chars")
            print(f"HTML Content Length: {len(job.get('html_content', ''))} chars")
            print(f"Scraped At: {job.get('scraped_at')}")
            print(f"\nFirst 500 chars of content:")
            print(job.get('raw_content', '')[:500])
            print("-"*60)

        return True, raw_jobs

    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, []
    finally:
        db.close()


async def test_scraper_multi_page():
    """Test crawling multiple pages"""
    print("\n" + "="*60)
    print("TEST 2: Multi-Page Crawling")
    print("="*60)

    db = SessionLocal()
    try:
        # Create a test career page with multi-page config
        test_career_page = CareerPage(
            company_name="Multi-Page Test Company",
            url="https://www.ycombinator.com/jobs",  # Example multi-page site
            scrape_config={"multi_page": True, "page_limit": 3},
            is_active=True
        )

        # Check if it already exists
        existing = db.query(CareerPage).filter(CareerPage.url == test_career_page.url).first()
        if existing:
            test_career_page = existing
            print(f"✓ Using existing career page: {test_career_page.company_name}")
        else:
            db.add(test_career_page)
            db.commit()
            db.refresh(test_career_page)
            print(f"✓ Created new career page: {test_career_page.company_name}")

        # Initialize scraper service
        scraper = ScraperService()
        print("✓ ScraperService initialized")

        # Scrape the career page
        print(f"\nCrawling URL: {test_career_page.url}")
        print("Note: This may take a while for multi-page crawling...")
        raw_jobs = await scraper.scrape_career_page(test_career_page, db)

        # Display results
        print(f"\n✓ Crawling completed!")
        print(f"  - Found {len(raw_jobs)} pages/entries")

        if raw_jobs:
            print("\n" + "-"*60)
            print("Pages Crawled:")
            print("-"*60)
            for idx, job in enumerate(raw_jobs[:5], 1):  # Show first 5
                print(f"{idx}. URL: {job.get('url')}")
                print(f"   Content Length: {len(job.get('raw_content', ''))} chars")
            if len(raw_jobs) > 5:
                print(f"... and {len(raw_jobs) - 5} more pages")
            print("-"*60)

        return True, raw_jobs

    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, []
    finally:
        db.close()


async def main():
    print("\n" + "="*60)
    print("SCRAPER SERVICE TEST SUITE")
    print("="*60)
    print("\nThis will test the scraper service functionality:")
    print("1. Single page scraping")
    print("2. Multi-page crawling")
    print("\nMake sure you have:")
    print("✓ FIRECRAWL_API_KEY set in .env")
    print("✓ Database connection configured")
    print("✓ Internet connection")

    input("\nPress Enter to continue...")

    # Initialize database
    print("\nInitializing database...")
    init_db()
    print("✓ Database initialized")

    # Run tests
    results = []

    # Test 1: Single page scraping
    success1, raw_jobs1 = await test_scraper_single_page()
    results.append(("Single Page Scraping", success1))

    # Test 2: Multi-page crawling (optional, can be slow)
    print("\n" + "="*60)
    print("Multi-page crawling can be slow. Skip it? (y/n)")
    skip = input().lower() == 'y'

    if not skip:
        success2, raw_jobs2 = await test_scraper_multi_page()
        results.append(("Multi-Page Crawling", success2))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status} - {test_name}")

    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())
