import time
import warnings
from datetime import date, timedelta

warnings.filterwarnings("ignore")

from jobspy import scrape_jobs  # python-jobspy — scrapes Indeed directly

# Multiple queries to maximise coverage; no API key needed
SEARCH_QUERIES = [
    "junior AI engineer",
    "junior AI developer",
    "junior machine learning engineer",
]

MAX_AGE_DAYS = 3  # ignore jobs older than 3 days


def fetch_jobs() -> list[dict]:
    """Scrape recent Indeed Canada jobs in Toronto and return as list of dicts."""
    cutoff = date.today() - timedelta(days=MAX_AGE_DAYS)
    all_jobs: list[dict] = []
    seen_ids: set[str] = set()

    for query in SEARCH_QUERIES:
        try:
            df = scrape_jobs(
                site_name=["indeed"],
                search_term=query,
                location="Toronto, ON",
                results_wanted=25,
                country_indeed="Canada",
                verbose=0,
            )
        except Exception as e:
            print(f"  Error scraping '{query}': {e}")
            time.sleep(3)
            continue

        kept = 0
        for _, row in df.iterrows():
            job_id = row.get("id")
            if not job_id or job_id in seen_ids:
                continue

            # Strict date filter — skip anything older than MAX_AGE_DAYS
            date_posted = row.get("date_posted")
            if date_posted:
                d = date_posted if isinstance(date_posted, date) else date_posted
                if hasattr(d, "date"):
                    d = d.date()
                if d < cutoff:
                    continue

            seen_ids.add(job_id)
            all_jobs.append(row.to_dict())
            kept += 1

        print(f"  '{query}' → {kept} recent Indeed jobs kept")
        time.sleep(3)  # polite delay between queries

    return all_jobs
