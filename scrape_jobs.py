"""
Tiny job scraper for public ATS boards (Greenhouse + Lever).

Usage:
  python scrape_jobs.py

Outputs:
  raw_jobs.csv
  raw_jobs_preview.csv
"""

from __future__ import annotations

import html
import sys
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup


# --------- Configuration (starter list) ---------
GREENHOUSE_BOARDS = ["oklo", "verkada", "beautifulai", "addepar1", "humansignal"]
LEVER_HANDLES = ["lever", "netlify", "postman", "mixpanel", "robinhood"]


# --------- Helpers ---------
def _clean_html_to_text(value: Optional[str]) -> str:
    """Strip HTML tags but preserve content and whitespace reasonably."""
    if not value:
        return ""
    # First unescape HTML entities, then parse and get text.
    unescaped = html.unescape(value)
    soup = BeautifulSoup(unescaped, "html.parser")
    text = soup.get_text(separator="\n")
    # Normalize excessive whitespace/newlines.
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join([line for line in lines if line])
    return cleaned.strip()


def _request_json(url: str, timeout: int = 20) -> Optional[Any]:
    """HTTP GET JSON with basic error handling."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: BLE001 - simple, clear error handling
        print(f"[WARN] Failed to fetch {url} -> {exc}")
        return None


# --------- Source fetchers ---------
def fetch_greenhouse_jobs(board_token: str) -> List[Dict[str, Any]]:
    """Fetch jobs from a Greenhouse board token."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    data = _request_json(url)
    if not data or "jobs" not in data:
        return []

    results: List[Dict[str, Any]] = []
    for job in data.get("jobs", []):
        # Greenhouse API fields can vary a bit, so keep it defensive.
        location = ""
        if isinstance(job.get("location"), dict):
            location = job.get("location", {}).get("name", "")
        else:
            location = job.get("location", "") or ""

        departments = job.get("departments") or []
        department = ""
        if isinstance(departments, list) and departments:
            department = departments[0].get("name", "") or ""

        # Greenhouse includes "content" for description HTML.
        raw_text = _clean_html_to_text(job.get("content", ""))

        results.append(
            {
                "job_id": str(job.get("id", "")),
                "source_type": "greenhouse",
                "source_name": board_token,
                "company": board_token,
                "title": job.get("title", "") or "",
                "location": location,
                "department": department,
                "team": "",  # not consistently available on GH boards
                "employment_type": "",
                "url": job.get("absolute_url", "") or "",
                "raw_text": raw_text,
            }
        )

    return results


def fetch_lever_jobs(company: str) -> List[Dict[str, Any]]:
    """Fetch jobs from a Lever company handle."""
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    data = _request_json(url)
    if not data or not isinstance(data, list):
        return []

    results: List[Dict[str, Any]] = []
    for job in data:
        location = ""
        if isinstance(job.get("categories"), dict):
            location = job.get("categories", {}).get("location", "") or ""
            department = job.get("categories", {}).get("department", "") or ""
            team = job.get("categories", {}).get("team", "") or ""
            employment_type = job.get("categories", {}).get("commitment", "") or ""
        else:
            department = ""
            team = ""
            employment_type = ""

        # Lever has multiple HTML fields; concatenate for "full messy text".
        html_parts = [
            job.get("description", ""),
            job.get("lists", ""),
            job.get("additional", ""),
        ]
        raw_text = _clean_html_to_text("\n".join([p for p in html_parts if p]))

        results.append(
            {
                "job_id": str(job.get("id", "")),
                "source_type": "lever",
                "source_name": company,
                "company": company,
                "title": job.get("text", "") or "",
                "location": location,
                "department": department,
                "team": team,
                "employment_type": employment_type,
                "url": job.get("hostedUrl", "") or "",
                "raw_text": raw_text,
            }
        )

    return results


def main() -> int:
    sources_attempted = 0
    sources_succeeded = 0
    all_jobs: List[Dict[str, Any]] = []

    # Greenhouse sources
    for board in GREENHOUSE_BOARDS:
        sources_attempted += 1
        jobs = fetch_greenhouse_jobs(board)
        if jobs:
            sources_succeeded += 1
            all_jobs.extend(jobs)

    # Lever sources
    for handle in LEVER_HANDLES:
        sources_attempted += 1
        jobs = fetch_lever_jobs(handle)
        if jobs:
            sources_succeeded += 1
            all_jobs.extend(jobs)

    # Build DataFrame, dedupe by URL, and save.
    df = pd.DataFrame(all_jobs)
    if not df.empty:
        df = df.drop_duplicates(subset=["url"]).reset_index(drop=True)
    else:
        # Ensure expected columns even when empty
        df = pd.DataFrame(
            columns=[
                "job_id",
                "source_type",
                "source_name",
                "company",
                "title",
                "location",
                "department",
                "team",
                "employment_type",
                "url",
                "raw_text",
            ]
        )

    df.to_csv("raw_jobs.csv", index=False)

    preview_cols = ["job_id", "company", "title", "location", "url"]
    df[preview_cols].to_csv("raw_jobs_preview.csv", index=False)

    print(
        f"Sources attempted: {sources_attempted} | "
        f"Succeeded: {sources_succeeded} | "
        f"Total jobs saved: {len(df)}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
