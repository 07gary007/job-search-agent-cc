import json
from pathlib import Path

DATA_DIR = Path("data")
SEEN_JOBS_FILE = DATA_DIR / "seen_jobs.json"
MAX_SEEN = 2000  # keep last 2000 job IDs to prevent unbounded growth


def load_seen_jobs() -> set:
    DATA_DIR.mkdir(exist_ok=True)
    if not SEEN_JOBS_FILE.exists():
        return set()
    with open(SEEN_JOBS_FILE) as f:
        return set(json.load(f))


def save_seen_jobs(seen: set) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    items = list(seen)
    if len(items) > MAX_SEEN:
        items = items[-MAX_SEEN:]
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(items, f)


def mark_seen(job_id: str, seen: set) -> bool:
    """Returns True if job is new (not seen before), and adds it to seen."""
    if job_id in seen:
        return False
    seen.add(job_id)
    return True
