"""
Indeed Job Monitor — main entry point
Fetches new junior AI/ML jobs in Toronto, scores them against Gary's resume,
and pushes high-quality matches to Telegram.
"""
import math
import sys
from pathlib import Path

# Load .env for local development (no-op in GitHub Actions)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from scraper import fetch_jobs
from scorer import score_job
from notifier import send_job_notification
from storage import load_seen_jobs, save_seen_jobs, mark_seen

MIN_SCORE = 7


def is_qualifying_score(value: object) -> bool:
    """Only a valid numeric Claude score from 7 through 10 can notify."""
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and MIN_SCORE <= value <= 10
    )


def main() -> None:
    print("=" * 55)
    print("  Indeed Job Monitor")
    print("=" * 55)

    # ── 1. Load deduplication state ────────────────────────────
    seen_jobs = load_seen_jobs()
    print(f"📦 Previously seen jobs: {len(seen_jobs)}")

    # ── 2. Fetch recent Indeed listings ───────────────────────
    print("\n📥 Fetching jobs from API...")
    try:
        all_jobs = fetch_jobs()
    except Exception as exc:
        print(f"❌ Fatal error fetching jobs: {exc}")
        sys.exit(1)

    print(f"📊 Total fetched: {len(all_jobs)}")

    # ── 3. Filter to unseen jobs ───────────────────────────────
    new_jobs = [
        job for job in all_jobs
        if job.get("id") and str(job["id"]) not in seen_jobs
    ]
    print(f"🆕 New (unseen) jobs: {len(new_jobs)}")

    if not new_jobs:
        print("\n✅ Nothing new. Exiting without Telegram notification.")
        return

    # ── 4. Score each job with Claude ─────────────────────────
    print(f"\n🤖 Scoring {len(new_jobs)} jobs with Claude haiku...")
    notified = 0
    processing_failed = False

    for i, job in enumerate(new_jobs, 1):
        title = job.get("title") or "Unknown"
        company = job.get("company") or "Unknown"
        location = job.get("location") or ""
        print(f"\n  [{i}/{len(new_jobs)}] {title} @ {company} ({location})")

        try:
            score_data = score_job(job)
            score = score_data.get("score")
            verdict = score_data.get("verdict", "")[:70]
            print(f"    Score: {score!r}/10  |  {verdict}")

        except Exception as exc:
            print(f"    ❌ Error: {exc}")
            processing_failed = True
            continue

        # Do not coerce strings such as "7" or values such as NaN: malformed
        # model output must never create a notification.
        if not is_qualifying_score(score):
            print(f"    ⏭  Invalid or below threshold ({score!r}); skipped")
            continue

        # notifier.py repeats the threshold so any future caller is also safe.
        if send_job_notification(job, score_data):
            notified += 1
            print("    ✅ Sent job notification to Telegram")
        else:
            print("    ❌ Telegram send failed")
            processing_failed = True

    if processing_failed:
        # Do not commit these jobs as seen. A later run should retry them.
        sys.exit(1)

    for job in new_jobs:
        mark_seen(str(job["id"]), seen_jobs)
    save_seen_jobs(seen_jobs)
    print(f"\n💾 Seen jobs saved ({len(seen_jobs)} total)")

    print(f"\n📊 Done — {len(new_jobs)} new jobs, {notified} detailed notifications sent")


if __name__ == "__main__":
    main()
