import os
import math
from html import escape
import requests
from datetime import date

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
MIN_NOTIFICATION_SCORE = 7


def _is_qualifying_score(value: object) -> bool:
    """Final safety gate: Telegram never receives a score below 7."""
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and MIN_NOTIFICATION_SCORE <= value <= 10
    )


def _html(value) -> str:
    """Escape dynamic values before inserting them into Telegram HTML."""
    return escape(str(value), quote=True)


def _cec_label(score_data: dict) -> str:
    labels = {
        "yes": "是",
        "no": "否",
        "unclear": "不确定",
    }
    value = str(score_data.get("cec_relevant", "unclear")).lower().strip()
    return labels.get(value, "不确定")


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
    if not _is_qualifying_score(score):
        print(f"    Telegram skipped: invalid or below-{MIN_NOTIFICATION_SCORE} score ({score!r})")
        return False
    emoji = _score_emoji(score)

    title = _html(job.get("title", "Unknown Role"))
    company = _html(job.get("company", "Unknown Company"))
    num_employees = job.get("company_num_employees")
    employees_str = str(num_employees) if num_employees and str(num_employees) != "nan" else "没查到"
    employees_str = _html(employees_str)
    location = str(job.get("location", "Unknown"))
    is_remote = job.get("is_remote", False)
    if is_remote:
        location += " (Remote/Hybrid)"
    location = _html(location)

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
    salary = _html(salary)

    posted_str = _html(_relative_date(job.get("date_posted")))
    job_url = _html(job.get("job_url", "#"))

    reasons = score_data.get("match_reasons", [])
    reasons_html = "\n".join(f"  • {_html(r)}" for r in reasons[:3]) or "  • Good overall fit"

    red_flags = score_data.get("red_flags", [])
    flags_block = ""
    if red_flags:
        flags_block = "\n⚠️ <i>" + " | ".join(_html(flag) for flag in red_flags[:2]) + "</i>"

    verdict = _html(score_data.get("verdict", ""))

    text = (
        f"{emoji} <b>{score}/10 — {title}</b>\n\n"
        f"🏢 {company}\n"
        f"👥 {employees_str} employees\n"
        f"📍 {location}\n"
        f"💰 {salary}\n"
        f"📅 Posted: {posted_str}\n\n"
        f"🇨🇦 <b>CEC 相关经验（不考虑时长）:</b> {_cec_label(score_data)}\n\n"
        f"<i>{verdict}</i>\n\n"
        f"✅ <b>Why it matches:</b>\n{reasons_html}"
        f"{flags_block}\n\n"
        f'<a href="{job_url}">🔗 Apply on Indeed</a>'
    )

    return _send_message(text, parse_mode="HTML")


def _send_message(text: str, *, parse_mode: str | None = None) -> bool:
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        resp = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json=payload,
            timeout=10,
        )
    except requests.RequestException as exc:
        print(f"    Telegram request failed: {exc}")
        return False

    if not resp.ok:
        print(f"    Telegram error: {resp.status_code} {resp.text[:300]}")
    return resp.ok
