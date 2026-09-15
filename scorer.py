import json
import os
from datetime import date
import anthropic

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


GARY_PROFILE = """
Candidate: Gary (Guanyu) Li
Education:
  - MEng AI Specialization, University of Waterloo (GPA 3.7, graduating Apr 2026)
  - BSc Data Science & Big Data Technology, Shandong University (GPA 3.6, top 3%)

Core Skills (strongest first):
  - Python, SQL, TypeScript, JavaScript
  - Generative AI: LLM APIs (OpenAI/Anthropic), RAG pipelines, embeddings,
    AI agents, prompt engineering, structured outputs
  - Frameworks: LangGraph, FastAPI, Playwright
  - ML: scikit-learn, PyTorch (basics), NLP fundamentals
  - Databases: PostgreSQL, pgvector (vector search)
  - DevOps/Tools: Docker, Git, REST APIs, React Native (basics), Node.js/Express

Work Experience:
  - AI Software Engineer Intern — SELEST Security (7 months)
      Built RAG-assisted intake system, LLM workflows, TypeScript/React Native app
  - Data Analyst Intern — Nielsen (6 months)
      Python/SQL pipelines, reporting

Key Projects:
  - Vehicle Repair Triage Agent: LangGraph + RAG + pgvector + FastAPI + HITL
  - Multi-Agent Medical Device Crawler: LangGraph + Playwright + LLM extraction

Target: Junior AI / ML Engineer or AI Developer (0–3 yrs experience)
Location preference: Toronto Downtown > Toronto area > GTA hybrid > fully remote
"""


def score_job(job: dict) -> dict:
    """Score a job 1–10 for Gary using claude-haiku."""
    # Salary
    min_sal = job.get("min_amount")
    max_sal = job.get("max_amount")
    currency = job.get("currency", "CAD")
    interval = job.get("interval", "yearly")
    if min_sal and max_sal:
        salary_str = f"${int(min_sal):,}–${int(max_sal):,} {currency}/{interval}"
    elif min_sal:
        salary_str = f"${int(min_sal):,}+ {currency}/{interval}"
    else:
        salary_str = "Not listed"

    # Date
    date_posted = job.get("date_posted")
    date_str = str(date_posted) if date_posted else "Unknown"

    job_text = (
        f"Title: {job.get('title', 'N/A')}\n"
        f"Company: {job.get('company', 'N/A')}\n"
        f"Location: {job.get('location', 'N/A')}\n"
        f"Remote: {job.get('is_remote', False)}\n"
        f"Level: {job.get('job_level', 'N/A')}\n"
        f"Experience required: {job.get('experience_range', 'N/A')}\n"
        f"Salary: {salary_str}\n"
        f"Date posted: {date_str}\n"
        f"Description (first 2000 chars):\n"
        f"{str(job.get('description', ''))[:2000]}"
    )

    prompt = f"""Score this Indeed job for the candidate. Be realistic and strict.

CANDIDATE:
{GARY_PROFILE}

JOB:
{job_text}

Scoring rules (start at 5, adjust):
  +2 role is AI/LLM/ML engineering (not unrelated backend/frontend/geotechnical etc.)
  +2 clearly junior/entry level 0–2 yrs; ambiguous = 0; senior/staff = cap score at 4
  +2 Toronto Downtown or hybrid with DT office; Toronto area = +1; outside GTA no remote = -2
  +1 strong skill overlap: Python + LLM/RAG/LangGraph/agents
  +1 AI-focused company or known tech brand
  -3 completely unrelated role (geotechnical, civil, finance with no AI)

CEC-related experience classification (ignore duration completely):
  - Return "yes" when the actual duties clearly look like skilled work in a
    TEER 0–3 occupation that could be relevant to the Canadian Experience
    Class, such as software, AI/ML, data, or engineering roles.
  - Return "no" when the duties clearly look like TEER 4–5 or non-skilled work.
  - Return "unclear" when the posting does not provide enough information.
  - This is a job-duty relevance signal only, not a determination that the
    candidate satisfies IRCC's full CEC requirements.

Return ONLY valid JSON (no markdown):
{{"score": <integer 1-10>, "location_type": "<downtown|toronto|gta|remote|other>", "cec_relevant": "<yes|no|unclear>", "match_reasons": ["<reason>", "<reason>"], "red_flags": [], "verdict": "<one sentence>"}}"""

    client = _get_client()
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = msg.content[0].text.strip()
    if "```" in raw:
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw

    try:
        data = json.loads(raw)
        cec_relevant = str(data.get("cec_relevant", "unclear")).lower().strip()
        if cec_relevant not in {"yes", "no", "unclear"}:
            cec_relevant = "unclear"
        data["cec_relevant"] = cec_relevant
        return data
    except json.JSONDecodeError:
        return {
            "score": 5,
            "location_type": "unknown",
            "cec_relevant": "unclear",
            "match_reasons": ["Parse error — manual review"],
            "red_flags": [],
            "verdict": "Could not parse AI response",
        }
