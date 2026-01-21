"""
Test script for LLMService

This script tests the LLM service in isolation to verify:
1. Ollama connection
2. Job data normalization
3. JSON parsing
4. Field extraction accuracy
"""

import asyncio
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.llm_service import LLMService


async def test_llm_connection():
    """Test basic connection to Ollama"""
    print("\n" + "="*60)
    print("TEST 1: Ollama Connection")
    print("="*60)

    try:
        llm = LLMService()
        print(f"✓ LLMService initialized")
        print(f"  - Host: {llm.client.host if hasattr(llm.client, 'host') else 'N/A'}")
        print(f"  - Model: {llm.model}")

        # Test basic chat
        print("\nTesting basic chat functionality...")
        response = llm.client.chat(
            model=llm.model,
            messages=[
                {"role": "user", "content": "Reply with just the word 'OK'"}
            ]
        )

        print("✓ Connection successful!")
        print(f"  Response: {response['message']['content'][:100]}")

        return True

    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_normalize_simple_job():
    """Test normalizing a simple job posting"""
    print("\n" + "="*60)
    print("TEST 2: Simple Job Normalization")
    print("="*60)

    try:
        llm = LLMService()

        # Create sample raw job data
        raw_job = {
            "company_name": "Test Company",
            "url": "https://example.com/careers",
            "career_page_id": "test-id-123",
            "raw_content": """
# Careers at Test Company

## Senior Software Engineer
Location: San Francisco, CA
Type: Full-time
Experience: Senior level

We're looking for a Senior Software Engineer to join our backend team.
You'll work on building scalable microservices using Python and AWS.

Requirements:
- 5+ years of Python experience
- Strong knowledge of AWS
- Experience with microservices architecture
- Excellent communication skills

## Product Designer
Location: Remote
Type: Full-time
Experience: Mid-level

Join our design team to create beautiful user experiences.

Requirements:
- 3+ years UI/UX design
- Proficiency in Figma
- Portfolio required
            """,
            "html_content": "<html>...</html>",
            "metadata": {},
            "scraped_at": "2024-01-15T10:00:00"
        }

        print("✓ Sample raw job data created")
        print(f"  - Company: {raw_job['company_name']}")
        print(f"  - Content length: {len(raw_job['raw_content'])} chars")

        # Normalize the job data
        print("\nNormalizing job data with LLM...")
        print("(This may take 10-30 seconds depending on the model)")
        normalized_jobs = await llm.normalize_job_data(raw_job)

        # Display results
        print(f"\n✓ Normalization completed!")
        print(f"  - Extracted {len(normalized_jobs)} job postings")

        if normalized_jobs:
            print("\n" + "-"*60)
            print("Extracted Jobs:")
            print("-"*60)
            for idx, job in enumerate(normalized_jobs, 1):
                print(f"\nJob {idx}:")
                print(f"  Title: {job.get('title')}")
                print(f"  Location: {job.get('location')}")
                print(f"  Job Type: {job.get('job_type')}")
                print(f"  Experience Level: {job.get('experience_level')}")
                print(f"  Description: {job.get('description', '')[:100]}...")
                print(f"  Requirements: {job.get('requirements', '')[:100]}...")
                print(f"  URL: {job.get('url')}")
                print(f"  Career Page ID: {job.get('career_page_id')}")
            print("-"*60)
        else:
            print("\n⚠ Warning: No jobs extracted")

        return True, normalized_jobs

    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, []


async def test_normalize_complex_job():
    """Test normalizing a more complex job posting with multiple formats"""
    print("\n" + "="*60)
    print("TEST 3: Complex Job Normalization")
    print("="*60)

    try:
        llm = LLMService()

        # Create sample raw job data with varied formats
        raw_job = {
            "company_name": "Tech Startup Inc",
            "url": "https://example.com/careers",
            "career_page_id": "test-id-456",
            "raw_content": """
Open Positions:

Backend Engineer (Remote) - Full Time
Looking for experienced backend engineers. Must have Go and Kubernetes knowledge.
https://example.com/jobs/backend-001

Frontend Developer | New York | Full-time | Senior
React expert needed for our dashboard team. 5+ years experience required.
Apply at: https://example.com/jobs/frontend-002

Data Scientist - Contract - SF Bay Area
Part-time contract position for ML model development. PhD preferred.

DevOps Lead - REMOTE - Executive Level
Lead our infrastructure team. 10+ years experience with AWS/GCP.
            """,
            "html_content": "<html>...</html>",
            "metadata": {},
            "scraped_at": "2024-01-15T10:00:00"
        }

        print("✓ Complex raw job data created")
        print(f"  - Company: {raw_job['company_name']}")
        print(f"  - Content length: {len(raw_job['raw_content'])} chars")

        # Normalize the job data
        print("\nNormalizing job data with LLM...")
        print("(This may take 10-30 seconds depending on the model)")
        normalized_jobs = await llm.normalize_job_data(raw_job)

        # Display results
        print(f"\n✓ Normalization completed!")
        print(f"  - Extracted {len(normalized_jobs)} job postings")

        if normalized_jobs:
            print("\n" + "-"*60)
            print("Extracted Jobs:")
            print("-"*60)
            for idx, job in enumerate(normalized_jobs, 1):
                print(f"\nJob {idx}:")
                print(json.dumps(job, indent=2, default=str))
            print("-"*60)
        else:
            print("\n⚠ Warning: No jobs extracted")

        return True, normalized_jobs

    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, []


async def main():
    print("\n" + "="*60)
    print("LLM SERVICE TEST SUITE")
    print("="*60)
    print("\nThis will test the LLM service functionality:")
    print("1. Ollama connection")
    print("2. Simple job normalization")
    print("3. Complex job normalization")
    print("\nMake sure you have:")
    print("✓ Ollama running (http://localhost:11434)")
    print("✓ Model downloaded (llama3.1:8b or your configured model)")
    print("✓ OLLAMA_BASE_URL and OLLAMA_MODEL set in .env")

    input("\nPress Enter to continue...")

    # Run tests
    results = []

    # Test 1: Connection
    success1 = await test_llm_connection()
    results.append(("Ollama Connection", success1))

    if not success1:
        print("\n⚠ Skipping remaining tests due to connection failure")
        return

    # Test 2: Simple normalization
    success2, jobs2 = await test_normalize_simple_job()
    results.append(("Simple Job Normalization", success2))

    # Test 3: Complex normalization
    success3, jobs3 = await test_normalize_complex_job()
    results.append(("Complex Job Normalization", success3))

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
