"""
Job Description Pipeline (Gemini)

Converts raw_jobs.csv into structured_jobs.csv using Gemini API.
"""

import os
import json
import time
import re
import pandas as pd
from google import genai

ALLOWED_REMOTE = {"remote", "hybrid", "onsite", "unknown"}
ALLOWED_EMPLOYMENT = {"internship", "full_time", "part_time", "contract", "temporary", "unknown"}
ALLOWED_SENIORITY = {"intern", "entry_level", "associate", "mid_level", "senior", "lead", "manager", "director", "executive", "unknown"}

SCHEMA_FIELDS = [
    "job_id",
    "company",
    "title_raw",
    "title_clean",
    "location_raw",
    "location_clean",
    "remote_type",
    "employment_type",
    "seniority",
    "department",
    "experience_years_min",
    "experience_years_max",
    "salary_present",
    "salary_text",
    "required_skills",
    "preferred_skills",
    "responsibilities",
    "qualifications",
    "url",
]

BASE_PROMPT = """
You are an information extraction system for job descriptions.
Return ONLY valid JSON with the exact fields listed below.
Do NOT invent facts not present in the text.
Do not invent or infer information not explicitly present in the text.
Prefer missing values over incorrect guesses.
If something is missing, use "unknown", null, or [] as appropriate.
Extract ONLY from the provided raw text.
Preserve these fields from the input exactly: job_id, company, title_raw, location_raw, url.

Required JSON fields:
job_id, company, title_raw, title_clean, location_raw, location_clean,
remote_type, employment_type, seniority, department,
experience_years_min, experience_years_max, salary_present, salary_text,
required_skills, preferred_skills, responsibilities, qualifications, url

Allowed categorical values:
remote_type: remote | hybrid | onsite | unknown
employment_type: internship | full_time | part_time | contract | temporary | unknown
seniority: intern | entry_level | associate | mid_level | senior | lead | manager | director | executive | unknown

Extraction rules:
- required_skills and preferred_skills: extract only concrete, explicit, job-relevant skills (e.g., Python, SQL, AWS, Sales, Recruiting).
  Do NOT include soft traits. Do NOT include full sentences. Each item must be 1–4 words max. If unclear, return [].
- experience_years_min and experience_years_max: extract only if explicitly stated in the text. Do NOT infer from seniority.
  If not explicitly stated, return null.
- seniority: map strictly by title keywords:
  * Intern -> intern
  * Junior, Entry -> entry_level
  * Associate -> associate
  * Senior, Sr. -> senior
  * Manager -> manager
  * Director -> director
  * Head, VP, Chief -> executive
  If unclear, return "unknown". Do NOT guess.
- responsibilities and qualifications: return bullet-style list items, each short (max ~20 words),
  limit to top 5–7 items.

Return valid JSON only.
"""

def test_gemini(client):
    """
    Quick sanity check against the Gemini API.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents='Return only this JSON: {"status":"ok"}',
    )
    response_text = response.text
    print("test_gemini() raw response:", response_text)
    return response_text


def extract_job_structured(row, model_name="gemini-1.5-flash"):
    """
    Send one job to Gemini and parse JSON response.
    Returns a dict or raises an Exception for the caller to handle.
    """
    payload = {
        "job_id": str(row["job_id"]),
        "company": str(row["company"]),
        "title_raw": str(row["title"]),
        "location_raw": str(row["location"]),
        "url": str(row["url"]),
        "raw_text": str(row["raw_text"]),
    }

    prompt = BASE_PROMPT + "\nINPUT JSON:\n" + json.dumps(payload)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    response_text = response.text

    match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if match:
        response_text = match.group(0)

    return json.loads(response_text)


def _ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [str(value)]


def _ensure_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1"}
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def _ensure_number_or_null(value):
    if value is None:
        return None
    try:
        num = float(value)
        if num.is_integer():
            return int(num)
        return num
    except Exception:
        return None


def normalize_record(rec):
    for f in SCHEMA_FIELDS:
        if f not in rec:
            rec[f] = None

    if rec["remote_type"] not in ALLOWED_REMOTE:
        rec["remote_type"] = "unknown"
    if rec["employment_type"] not in ALLOWED_EMPLOYMENT:
        rec["employment_type"] = "unknown"
    if rec["seniority"] not in ALLOWED_SENIORITY:
        rec["seniority"] = "unknown"

    rec["required_skills"] = _ensure_list(rec.get("required_skills"))
    rec["preferred_skills"] = _ensure_list(rec.get("preferred_skills"))
    rec["responsibilities"] = _ensure_list(rec.get("responsibilities"))
    rec["qualifications"] = _ensure_list(rec.get("qualifications"))

    rec["salary_present"] = _ensure_bool(rec.get("salary_present"))
    rec["experience_years_min"] = _ensure_number_or_null(rec.get("experience_years_min"))
    rec["experience_years_max"] = _ensure_number_or_null(rec.get("experience_years_max"))

    for k in ["job_id", "company", "title_raw", "location_raw", "url"]:
        rec[k] = "" if rec.get(k) is None else str(rec.get(k))

    return rec


def main():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY or GOOGLE_API_KEY before running.")

    global client
    client = genai.Client(api_key=api_key)

    # Sanity check before processing rows
    try:
        test_gemini(client)
    except Exception as e:
        raise RuntimeError(f"Gemini test failed: {e}")

    df = pd.read_csv("raw_jobs.csv")
    print("Original rows:", len(df))

    df = df.drop_duplicates(subset=["url"]).copy()
    df["raw_text"] = df["raw_text"].fillna("")
    df = df[df["raw_text"].str.len() >= 300]

    keep_cols = ["job_id", "company", "title", "location", "url", "raw_text"]
    df = df[keep_cols].copy()
    print("Cleaned rows:", len(df))

    sample_10 = df.sample(n=10, random_state=42) if len(df) >= 10 else df.copy()
    sample_50 = df.sample(n=50, random_state=42) if len(df) >= 50 else df.copy()
    print("Sample 10 rows:", len(sample_10))
    print("Sample 50 rows:", len(sample_50))

    success_rows = []
    failed_rows = []

    for _, row in sample_10.iterrows():
        try:
            # Try once; if it fails, wait and retry once.
            try:
                rec = extract_job_structured(row)
            except Exception:
                time.sleep(2)
                rec = extract_job_structured(row)

            rec = normalize_record(rec)
            success_rows.append(rec)
            print(f"[{len(success_rows)}] OK - {row['title']}")
        except Exception as e:
            failed_rows.append({
                "job_id": row.get("job_id"),
                "url": row.get("url"),
                "error": str(e),
            })
            print(f"[FAIL] {row['title']} -> {e}")

        time.sleep(1)

    structured_df = pd.DataFrame(success_rows)
    failed_df = pd.DataFrame(failed_rows)

    structured_df.to_csv("structured_jobs.csv", index=False)
    failed_df.to_csv("failed_jobs.csv", index=False)

    print("Saved structured_jobs.csv and failed_jobs.csv")
    print("Total success:", len(structured_df))
    print("Total failed:", len(failed_df))
    print("Columns:", list(structured_df.columns))
    print(structured_df.head(5))

    # Simple queries
    if not structured_df.empty:
        print(structured_df["remote_type"].value_counts(dropna=False))
        print(structured_df["employment_type"].value_counts(dropna=False))
        print(structured_df[structured_df["salary_present"] == True].shape)

        python_rows = structured_df[structured_df["required_skills"].apply(
            lambda xs: any("python" in str(x).lower() for x in xs)
        )]
        print(python_rows.shape)


if __name__ == "__main__":
    main()
