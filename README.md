# Indeed Job Monitor 🔍

Automatically scans Indeed every 2 hours for junior AI/ML Engineer roles in Toronto, scores them against Gary's resume using Claude, and sends the results to Telegram.

## How it works

```
GitHub Actions (every 2h, around the clock)
  → Indeed via python-jobspy
  → Claude haiku  (score 1-10 vs resume)
  → Telegram      (compact list every run; detailed message if score ≥ 7)
  → commit seen_jobs.json  (dedup next run)
```

---

## Setup (one-time, ~15 minutes)

### Step 1 — Get an Anthropic API key

1. Go to https://console.anthropic.com
2. Create an API key (under Settings → API Keys)
3. Add $5 credit — this lasts ~3–6 months for this use case

### Step 2 — Create a Telegram Bot & get your Chat ID

**Create the bot:**
1. Open Telegram, search for `@BotFather`
2. Send `/newbot`, follow the prompts, pick a name (e.g. `GaryJobBot`)
3. BotFather gives you a token like `123456789:ABCdef...` — save it

**Get your Chat ID:**
1. Send any message to your new bot in Telegram
2. Open this URL in your browser (replace `YOUR_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
3. Look for `"chat":{"id": 123456789}` — that number is your Chat ID

### Step 3 — Push to GitHub

```bash
cd job_serach_agent
git init
git add .
git commit -m "init: job monitor"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/job-monitor.git
git push -u origin main
```

### Step 4 — Add GitHub Secrets

In your GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret name | Value |
|-------------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic key |
| `TELEGRAM_BOT_TOKEN` | Your bot token |
| `TELEGRAM_CHAT_ID` | Your chat ID (number) |

### Step 5 — Enable GitHub Actions

Go to your repo → **Actions tab** → click **"I understand my workflows, go ahead and enable them"**

To test immediately: **Actions → Indeed Job Monitor → Run workflow**

The monitor sends one compact list on every run, including each new job's
title, score, application link, and whether the role appears relevant to CEC
skilled work. Jobs scoring 7 or higher also keep the detailed notification
format shown below, with the CEC field added.

The CEC label is a job-duty relevance signal and ignores duration. It is not a
legal determination that the candidate satisfies every IRCC Canadian
Experience Class requirement.

---

## What you'll receive on Telegram

```
⭐ 8/10 — Junior AI Engineer

🏢 Acme AI Inc.
📍 Toronto, ON (Downtown)
💰 $75,000–$95,000 CAD/yr
📅 2025-01-15 · via Indeed
🇨🇦 CEC 相关经验（不考虑时长）: 是

Strong LangGraph + RAG match for an AI-first startup

✅ Why it matches:
  • RAG pipeline experience directly relevant
  • LangGraph listed as primary framework
  • Python + FastAPI stack matches

🔗 Apply Now
```

---

## Cost estimate

| Service | Cost |
|---------|------|
| Claude haiku (scoring ~300 jobs/mo) | ~$0.50/mo |
| GitHub Actions (every 2h) | $0/mo |
| Telegram | $0 |
| **Total** | **~$0.50/mo** |

---

## Local testing

```bash
cp .env.example .env
# Fill in your keys in .env

pip install -r requirements.txt
python main.py
```
