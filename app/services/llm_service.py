from typing import Dict, List, Optional
import json
import ollama
from app.config import settings


class LLMService:
    def __init__(self):
        self.client = ollama.Client(host=settings.ollama_base_url)
        self.model = settings.ollama_model

    async def normalize_job_data(self, raw_job: Dict) -> List[Dict]:
        """
        Use LLM to extract and normalize job postings from raw scraped data.

        Args:
            raw_job: Raw job data from Firecrawl containing markdown/html content

        Returns:
            List of normalized job dictionaries with structured fields
        """
        print(f"[LLM] Normalizing job data from {raw_job.get('company_name', 'Unknown')}")

        raw_content = raw_job.get("raw_content", "")
        company_name = raw_job.get("company_name", "")

        if not raw_content:
            print(f"[LLM] No content to normalize")
            return []

        # Build the prompt
        prompt = self._build_normalization_prompt(raw_content, company_name)

        try:
            # Call Ollama
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a job posting data extraction assistant. Extract structured job information from raw career page content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.1,  # Low temperature for consistent extraction
                }
            )

            # Parse the response
            llm_output = response["message"]["content"]
            normalized_jobs = self._parse_llm_response(llm_output, raw_job)

            print(f"[LLM] Extracted {len(normalized_jobs)} job postings")
            return normalized_jobs

        except Exception as e:
            print(f"[LLM] Error normalizing job data: {str(e)}")
            return []

    def _build_normalization_prompt(self, raw_content: str, company_name: str) -> str:
        """
        Build a prompt for the LLM to extract job information.

        Args:
            raw_content: Raw markdown/html content from Firecrawl
            company_name: Company name

        Returns:
            Formatted prompt string
        """
        prompt = f"""Extract ALL job postings from the following career page content for {company_name}.

For EACH job posting found, extract the following information:
- title: Job title (required)
- location: Job location or "Remote" if applicable
- job_type: Type of employment (e.g., "Full-time", "Part-time", "Contract", "Remote", "Hybrid")
- experience_level: Required experience level (e.g., "Entry", "Mid-level", "Senior", "Lead", "Executive")
- description: Brief job description (1-3 sentences)
- requirements: Key requirements or skills needed
- url: Direct URL to the job posting (if available in the content)

Return the results as a JSON array. Each job should be a separate object in the array.

Example output format:
[
  {{
    "title": "Senior Software Engineer",
    "location": "San Francisco, CA",
    "job_type": "Full-time",
    "experience_level": "Senior",
    "description": "Build scalable backend systems for our platform.",
    "requirements": "5+ years Python, AWS, microservices architecture",
    "url": "https://careers.company.com/jobs/12345"
  }},
  {{
    "title": "Product Designer",
    "location": "Remote",
    "job_type": "Remote",
    "experience_level": "Mid-level",
    "description": "Design user experiences for our mobile app.",
    "requirements": "3+ years UI/UX design, Figma, user research",
    "url": "https://careers.company.com/jobs/12346"
  }}
]

IMPORTANT:
- Extract ALL jobs you can find in the content
- If a field is not available, use null
- Return ONLY valid JSON, no additional text or explanations
- If no jobs are found, return an empty array: []

Career Page Content:
{raw_content[:8000]}
"""  # Limit content to ~8000 chars to avoid token limits

        return prompt

    def _parse_llm_response(self, llm_output: str, raw_job: Dict) -> List[Dict]:
        """
        Parse LLM response and create normalized job dictionaries.

        Args:
            llm_output: JSON string from LLM
            raw_job: Original raw job data

        Returns:
            List of normalized job dictionaries
        """
        try:
            # Extract JSON from response (LLM might include extra text)
            llm_output = llm_output.strip()

            # Find JSON array in response
            start_idx = llm_output.find("[")
            end_idx = llm_output.rfind("]") + 1

            if start_idx == -1 or end_idx == 0:
                print(f"[LLM] No JSON array found in response")
                return []

            json_str = llm_output[start_idx:end_idx]
            jobs_data = json.loads(json_str)

            if not isinstance(jobs_data, list):
                print(f"[LLM] Response is not a list")
                return []

            # Enhance each job with metadata from raw_job
            normalized_jobs = []
            for job in jobs_data:
                if not job.get("title"):
                    continue  # Skip jobs without titles

                normalized_job = {
                    "title": job.get("title", "").strip(),
                    "location": job.get("location", "").strip() or None,
                    "job_type": job.get("job_type", "").strip() or None,
                    "experience_level": job.get("experience_level", "").strip() or None,
                    "description": job.get("description", "").strip() or None,
                    "requirements": job.get("requirements", "").strip() or None,
                    "url": job.get("url", "").strip() or raw_job.get("url", ""),
                    "career_page_id": raw_job.get("career_page_id"),
                    "company_name": raw_job.get("company_name"),
                    "raw_data": raw_job  # Store complete raw data
                }

                normalized_jobs.append(normalized_job)

            return normalized_jobs

        except json.JSONDecodeError as e:
            print(f"[LLM] Failed to parse JSON: {str(e)}")
            print(f"[LLM] Response was: {llm_output[:500]}")
            return []
        except Exception as e:
            print(f"[LLM] Error parsing LLM response: {str(e)}")
            return []
