import hashlib
from typing import Dict


def generate_job_external_id(career_page_id: str, job_url: str, title: str) -> str:
    """
    Generate a unique external_id for a job posting using hash of key fields.
    This helps identify duplicate jobs across scrapes.

    Args:
        career_page_id: UUID of the career page
        job_url: URL of the job posting
        title: Job title

    Returns:
        SHA256 hash string as external_id
    """
    # Combine key fields to create unique identifier
    unique_string = f"{career_page_id}:{job_url}:{title}".lower().strip()

    # Generate SHA256 hash
    hash_object = hashlib.sha256(unique_string.encode())
    return hash_object.hexdigest()


def generate_simple_hash(text: str) -> str:
    """
    Generate a simple hash for any text.

    Args:
        text: Text to hash

    Returns:
        SHA256 hash string
    """
    hash_object = hashlib.sha256(text.encode())
    return hash_object.hexdigest()
