"""
Indeed Job Monitor — main entry point
Fetches new junior AI/ML jobs in Toronto, scores them against Gary's resume,
and pushes high-quality matches to Telegram.
"""
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
from notifier import send_job_notification, send_summary
from storage import load_seen_jobs, save_seen_jobs, mark_seen

MIN_SCORE = 7  # Only notify for jobs scoring 7 or above


def main() -> None:
    print("=" * 55)
    print("  Indeed Job Monitor")
    print("=" * 55)

    # ── 1. Load deduplication state ────────────────────────────
    seen_jobs = load_seen_jobs()
    print(f"📦 Previously seen jobs: {len(seen_jobs)}")

    # ── 2. Fetch from JSearch API ──────────────────────────────
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
        if job.get("id") and mark_seen(str(job["id"]), seen_jobs)
    ]
    print(f"🆕 New (unseen) jobs: {len(new_jobs)}")

    if not new_jobs:
        print("\n✅ Nothing new. Exiting.")
        save_seen_jobs(seen_jobs)
        return

    # ── 4. Score each job with Claude ─────────────────────────
    print(f"\n🤖 Scoring {len(new_jobs)} jobs with Claude haiku...")
    notified = 0

    for i, job in enumerate(new_jobs, 1):
        title = job.get("title") or "Unknown"
        company = job.get("company") or "Unknown"
        location = job.get("location") or ""
        print(f"\n  [{i}/{len(new_jobs)}] {title} @ {company} ({location})")

        try:
            score_data = score_job(job)
            score = score_data.get("score", 0)
            verdict = score_data.get("verdict", "")[:70]
            print(f"    Score: {score}/10  |  {verdict}")

            if score >= MIN_SCORE:
                ok = send_job_notification(job, score_data)
                if ok:
                    notified += 1
                    print("    ✅ Sent to Telegram")
                else:
                    print("    ❌ Telegram send failed")
            else:
                print(f"    ⏭  Below threshold ({score} < {MIN_SCORE}), skipped")

        except Exception as exc:
            print(f"    ❌ Error: {exc}")

    # ── 5. Persist & summarise ─────────────────────────────────
    save_seen_jobs(seen_jobs)
    print(f"\n💾 Seen jobs saved ({len(seen_jobs)} total)")

    send_summary(len(new_jobs), notified)
    print(f"\n📊 Done — {len(new_jobs)} new jobs, {notified} sent to Telegram")


if __name__ == "__main__":
    main()
