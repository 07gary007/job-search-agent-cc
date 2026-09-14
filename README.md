# Indeed Job Monitor 🔍

Automatically scans Indeed (via JSearch API) every 2 hours for junior AI/ML Engineer roles in Toronto, scores them against Gary's resume using Claude, and sends the best matches to Telegram.

## How it works

```
GitHub Actions (every 2h, weekdays)
  → JSearch API  (real Indeed/LinkedIn data)
  → Claude haiku  (score 1-10 vs resume)
  → Telegram      (notify if score ≥ 7)
  → commit seen_jobs.json  (dedup next run)
```

---

## Setup (one-time, ~15 minutes)

### Step 1 — Get a RapidAPI key (JSearch)

1. Go to https://rapidapi.com and create a free account
2. Search for **"JSearch"** and subscribe to the **Basic (Free)** plan
3. Copy your API key from the dashboard

### Step 2 — Get an Anthropic API key

1. Go to https://console.anthropic.com
2. Create an API key (under Settings → API Keys)
3. Add $5 credit — this lasts ~3–6 months for this use case

### Step 3 — Create a Telegram Bot & get your Chat ID

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

### Step 4 — Push to GitHub

```bash
cd job_serach_agent
git init
git add .
git commit -m "init: job monitor"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/job-monitor.git
git push -u origin main
```

### Step 5 — Add GitHub Secrets

In your GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret name | Value |
|-------------|-------|
| `RAPIDAPI_KEY` | Your RapidAPI key |
| `ANTHROPIC_API_KEY` | Your Anthropic key |
| `TELEGRAM_BOT_TOKEN` | Your bot token |
| `TELEGRAM_CHAT_ID` | Your chat ID (number) |

### Step 6 — Enable GitHub Actions

Go to your repo → **Actions tab** → click **"I understand my workflows, go ahead and enable them"**

To test immediately: **Actions → Indeed Job Monitor → Run workflow**

---

## What you'll receive on Telegram

```
⭐ 8/10 — Junior AI Engineer

🏢 Acme AI Inc.
📍 Toronto, ON (Downtown)
💰 $75,000–$95,000 CAD/yr
📅 2025-01-15 · via Indeed

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
| JSearch API (free tier: 500 req/mo) | $0/mo |
| Claude haiku (scoring ~300 jobs/mo) | ~$0.50/mo |
| GitHub Actions (weekdays only) | $0/mo |
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
