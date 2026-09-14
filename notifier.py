import os
import requests
from datetime import date

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def _score_emoji(score: int) -> str:
    if score >= 9:
        return "🔥"
    if score >= 8:
        return "⭐"
    return "✅"


def _relative_date(date_posted) -> str:
    """Return human-readable relative date, e.g. 'Today', '2 days ago (Sep 12)'."""
    if not date_posted:
        return "Unknown date"
    try:
        d = date_posted if isinstance(date_posted, date) else date_posted
        if hasattr(d, "date"):
            d = d.date()
        delta = (date.today() - d).days
        label = d.strftime("%b %d")
        if delta == 0:
            return f"Today ({label})"
        elif delta == 1:
            return f"Yesterday ({label})"
        else:
            return f"{delta} days ago ({label})"
    except Exception:
        return str(date_posted)


def send_job_notification(job: dict, score_data: dict) -> bool:
    """Send a formatted Indeed job notification to Telegram."""
    score = score_data.get("score", 0)
    emoji = _score_emoji(score)

    title = job.get("title", "Unknown Role")
    company = job.get("company", "Unknown Company")
    num_employees = job.get("company_num_employees")
    employees_str = str(num_employees) if num_employees and str(num_employees) != "nan" else "没查到"
    location = job.get("location", "Unknown")
    is_remote = job.get("is_remote", False)
    if is_remote:
        location += " (Remote/Hybrid)"

    # Salary
    min_sal = job.get("min_amount")
    max_sal = job.get("max_amount")
    currency = job.get("currency", "CAD")
    interval = job.get("interval", "yearly")
    if min_sal and max_sal:
        salary = f"${int(min_sal):,}–${int(max_sal):,} {currency}/{interval}"
    elif min_sal:
        salary = f"${int(min_sal):,}+ {currency}/{interval}"
    else:
        salary = "Not listed"

    posted_str = _relative_date(job.get("date_posted"))
    job_url = job.get("job_url", "#")

    reasons = score_data.get("match_reasons", [])
    reasons_html = "\n".join(f"  • {r}" for r in reasons[:3]) or "  • Good overall fit"

    red_flags = score_data.get("red_flags", [])
    flags_block = ""
    if red_flags:
        flags_block = "\n⚠️ <i>" + " | ".join(red_flags[:2]) + "</i>"

    verdict = score_data.get("verdict", "")

    text = (
        f"{emoji} <b>{score}/10 — {title}</b>\n\n"
        f"🏢 {company}\n"
        f"👥 {employees_str} employees\n"
        f"📍 {location}\n"
        f"💰 {salary}\n"
        f"📅 Posted: {posted_str}\n\n"
        f"<i>{verdict}</i>\n\n"
        f"✅ <b>Why it matches:</b>\n{reasons_html}"
        f"{flags_block}\n\n"
        f'<a href="{job_url}">🔗 Apply on Indeed</a>'
    )

    resp = requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=10,
    )
    if not resp.ok:
        print(f"    Telegram error: {resp.status_code} {resp.text[:200]}")
    return resp.ok


def send_summary(new_count: int, notified_count: int) -> None:
    if notified_count == 0:
        return
    text = (
        f"📊 <b>Scan complete</b>\n"
        f"Checked {new_count} new Indeed listings → "
        f"<b>{notified_count} match(es)</b> sent above ☝️"
    )
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )
