# Phase 0: Local Development Setup — Runbook

**Estimated time**: 1-2 days
**Environment**: Your own machine (macOS / Linux)
**Outcome**: Claude Code working, X API keys active, Telegram Bot operational, project directory ready — all on your local machine

---

## Why Local First?

A VPS is only needed when the system runs autonomously — executing tasks overnight while you sleep. During development, **you are the scheduler**: you type commands, inspect outputs, and iterate. Your machine is already on because you're using it.

```
Now (Phase 0-4):     Your machine → CLI → claude -p → inspect → iterate
Later (Phase 5):     Deploy to VPS → cron triggers agents → system runs itself
```

VPS provisioning, server hardening, and cron setup are deferred to the **Deployment Phase** when all agents have been built and tested locally.

---

## Checklist Overview

```
[ ] Step 1 — Verify Node.js 22+ and install Claude Code
[ ] Step 2 — Install Python 3.11+ and dependencies
[ ] Step 3 — X Developer Account & API keys
[ ] Step 4 — Create Telegram Bot
[ ] Step 5 — Set up project directory structure
[ ] Step 6 — Initialize SQLite database
[ ] Step 7 — Set up Playwright browser profiles
[ ] Step 8 — Create CLAUDE.md memory files
[ ] Step 9 — Run health check
```

---

## Step 1: Verify Node.js 22+ and Install Claude Code

```bash
# Check Node.js version (install via nvm if needed: https://github.com/nvm-sh/nvm)
node --version   # Need v22+

# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Authenticate
claude auth login
# Follow the browser-based auth flow
```

### Verify

```bash
claude --version
claude -p "Hello, respond with just 'OK'" --dangerously-skip-permissions
# Should output "OK"
```

---

## Step 2: Install Python 3.11+ and Dependencies

```bash
# Check Python version
python3 --version   # Need 3.11+

# Create project directory and virtual environment
mkdir -p ~/x-ai-beauty
cd ~/x-ai-beauty
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install \
  tweepy \
  python-telegram-bot \
  anthropic \
  playwright \
  aiohttp \
  aiosqlite

# Install Playwright browser
playwright install chromium
playwright install-deps chromium
```

### Verify

```bash
python3 -c "import tweepy; print('tweepy OK')"
python3 -c "import telegram; print('telegram OK')"
python3 -c "import playwright; print('playwright OK')"
```

---

## Step 3: X Developer Account & API Keys

### 3.1 Apply for Developer Access

1. Go to [developer.x.com](https://developer.x.com/)
2. Sign in with your primary X account
3. Apply for developer access → Select "Basic" plan ($200/month)
4. Use case description:
   > "Building a social media management tool for our own brand accounts. The app will post
   > original content, monitor engagement metrics via API, and manage outbound engagement
   > (likes, replies, follows) for our AI-generated art accounts. All automation is for
   > accounts we own and operate. Content is human-approved before posting."

   > ⚠️ **Important**: Your use case description is binding per X Developer Terms. Ensure it accurately covers all planned functionality including outbound engagement (likes, replies, follows). See [`x-developer-terms-compliance-review.md`](./specs/x-developer-terms-compliance-review.md) Issue 7 for details.

5. Complete payment

### 3.2 Create an App

1. Developer Portal → Projects & Apps → Create new App
2. App name: `ai-beauty-manager`
3. App permissions: **Read and Write**
4. Type of App: **Web App**

### 3.3 Generate Tokens

1. App settings → "Keys and tokens"
2. Note: **API Key**, **API Secret**, **Bearer Token** (app-level, shared)
3. For each account (EN and JP), generate user-level tokens:
   - **Access Token** + **Access Token Secret** (OAuth 1.0a)
   - Or **Access Token** + **Refresh Token** (OAuth 2.0 with PKCE)

### 3.4 Quick Test

```bash
cd ~/x-ai-beauty
python3 scripts/test_x_api.py EN
python3 scripts/test_x_api.py JP
# Both should show ✅ for Read and Auth
```

(The test script is created in Step 5 along with the project structure.)

---

## Step 4: Create Telegram Bot

### 4.1 Create the Bot

1. Open Telegram → search for **@BotFather**
2. Send `/newbot`
3. Name: `AI Beauty Agent` (display name)
4. Username: `ai_beauty_agent_bot` (must end in `bot`)
5. Save the **Bot Token**

### 4.2 Get Your Chat ID

1. Send any message to your new bot (e.g., "hello")
2. Open: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find `"chat":{"id":XXXXXXXX}` — this is your Chat ID

### 4.3 Quick Test

```bash
cd ~/x-ai-beauty
python3 scripts/test_telegram.py
# Should print ✅ and you should receive a Telegram message
```

(The test script is created in Step 5.)

---

## Step 5: Set Up Project Directory Structure

```bash
cd ~/x-ai-beauty

# Create all directories
mkdir -p config data media/pending media/posted logs agents scripts browser_profiles/en_profile browser_profiles/jp_profile backups

# ── Config files ──

cat > config/accounts.json << 'EOF'
{
  "x_api": {
    "consumer_key": "REPLACE_ME",
    "consumer_secret": "REPLACE_ME",
    "bearer_token": "REPLACE_ME",
    "accounts": {
      "EN": {
        "handle": "@your_en_handle",
        "user_id": "REPLACE_ME",
        "access_token": "REPLACE_ME",
        "access_token_secret": "REPLACE_ME",
        "refresh_token": "REPLACE_ME"
      },
      "JP": {
        "handle": "@your_jp_handle",
        "user_id": "REPLACE_ME",
        "access_token": "REPLACE_ME",
        "access_token_secret": "REPLACE_ME",
        "refresh_token": "REPLACE_ME"
      }
    }
  },
  "telegram": {
    "bot_token": "REPLACE_ME",
    "chat_id": "REPLACE_ME"
  }
}
EOF
chmod 600 config/accounts.json

cat > config/competitors.json << 'EOF'
{
  "last_updated": "2026-03-01",
  "competitors": [],
  "tracked_keywords": [
    "#AIbeauty", "#AIart", "#AIgirl", "#AImodel",
    "#midjourney", "#stablediffusion", "#aiイラスト", "#AI美女"
  ]
}
EOF

cat > config/global_rules.md << 'EOF'
# Global Rules
# Format: - Rule text (learned YYYY-MM-DD)

- Human approval is required before any post goes live
- All X operations use official API (Playwright only for impression scraping)
- Conservative outbound limits: max 30 likes, 10 replies, 5 follows per account per day
- Never start a post with @ (X treats it as reply, hidden from followers' feeds)
- Compress images to <2MB before upload
EOF

cat > config/telegram_config.json << 'EOF'
{
  "commands": {
    "/approve": {"description": "Approve all or specific posts", "args": "optional: comma-separated indices"},
    "/edit": {"description": "Edit a post", "args": "<index> \"<new text>\""},
    "/status": {"description": "Pipeline health check"},
    "/pause": {"description": "Halt posting & outbound"},
    "/resume": {"description": "Resume after pause"},
    "/strategy": {"description": "Override strategy", "args": "\"<directive>\""},
    "/details": {"description": "Full content plan"},
    "/metrics": {"description": "Performance metrics", "args": "optional: en|jp"},
    "/competitors": {"description": "Competitor list & stats"},
    "/help": {"description": "List commands"}
  },
  "notification_settings": {
    "morning_brief_time": "07:00",
    "daily_report_time": "23:30",
    "timezone": "Asia/Tokyo"
  }
}
EOF

# ── Test scripts ──

cat > scripts/test_x_api.py << 'EOF'
import tweepy, json, sys

with open("config/accounts.json") as f:
    config = json.load(f)

xapi = config["x_api"]
account = sys.argv[1] if len(sys.argv) > 1 else "EN"

client = tweepy.Client(bearer_token=xapi["bearer_token"])
user = client.get_user(username=xapi["accounts"][account]["handle"].lstrip("@"))
print(f"✅ Read OK — {account}: @{user.data.username}" if user.data else f"❌ Read FAILED")

acc = xapi["accounts"][account]
auth_client = tweepy.Client(
    consumer_key=xapi["consumer_key"], consumer_secret=xapi["consumer_secret"],
    access_token=acc["access_token"], access_token_secret=acc["access_token_secret"]
)
me = auth_client.get_me()
print(f"✅ Auth OK — @{me.data.username}" if me.data else f"❌ Auth FAILED")
EOF

cat > scripts/test_telegram.py << 'EOF'
import json, asyncio
from telegram import Bot

with open("config/accounts.json") as f:
    config = json.load(f)

async def main():
    bot = Bot(token=config["telegram"]["bot_token"])
    msg = await bot.send_message(
        chat_id=config["telegram"]["chat_id"],
        text="🤖 AI Beauty Agent System — Test message\n\nTelegram is working!"
    )
    print(f"✅ Telegram OK — Message ID: {msg.message_id}")

asyncio.run(main())
EOF
```

---

## Step 6: Initialize SQLite Database

```bash
cat > scripts/db_manager.py << 'PYEOF'
import sqlite3, sys, os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "metrics_history.db")

def init():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS post_metrics (
        post_id TEXT, tweet_id TEXT, account TEXT, measured_at DATETIME,
        hours_after_post INTEGER, likes INTEGER, retweets INTEGER,
        replies INTEGER, quotes INTEGER, bookmarks INTEGER,
        impressions INTEGER, engagement_rate REAL, source TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS account_metrics (
        account TEXT, date DATE, followers INTEGER, following INTEGER,
        total_posts INTEGER, followers_change INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS outbound_log (
        date DATE, account TEXT, action_type TEXT, target_handle TEXT,
        target_tweet_id TEXT, success BOOLEAN, api_response_code INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS error_log (
        timestamp DATETIME, agent TEXT, error_type TEXT,
        error_message TEXT, resolution TEXT, resolved BOOLEAN)""")
    conn.commit(); conn.close()
    print("✅ Database initialized:", DB_PATH)

if __name__ == "__main__":
    init()
PYEOF

python3 scripts/db_manager.py
```

### Verify

```bash
sqlite3 data/metrics_history.db ".tables"
# Should show: account_metrics  error_log  outbound_log  post_metrics
```

---

## Step 7: Set Up Playwright Browser Profiles

Playwright is only used for impression scraping. Persistent profiles avoid re-login each time.

> ⚠️ **Compliance note**: Playwright scraping (even on own account pages) carries X Terms risk as non-API automation of the website is prohibited. See [`x-developer-terms-compliance-review.md`](./specs/x-developer-terms-compliance-review.md) Issue 4. Risk accepted for the value of impression data.

```bash
cat > scripts/setup_browser_profiles.py << 'PYEOF'
import asyncio
from playwright.async_api import async_playwright

async def setup_profile(account_name, profile_dir):
    print(f"\n{'='*50}")
    print(f"Setting up browser profile for {account_name}")
    print(f"1. Log into X with your {account_name} account")
    print(f"2. Close the browser window when done")
    print(f"{'='*50}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            profile_dir, headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await browser.new_page()
        await page.goto("https://x.com/login")
        try:
            await browser.wait_for_event("close", timeout=300000)
        except:
            await browser.close()
    print(f"✅ {account_name} profile saved!")

async def main():
    await setup_profile("EN", "browser_profiles/en_profile")
    await setup_profile("JP", "browser_profiles/jp_profile")

asyncio.run(main())
PYEOF

# Run it — a browser window will open for each account
python3 scripts/setup_browser_profiles.py
```

---

## Step 8: Create CLAUDE.md Memory Files

```bash
cat > ~/x-ai-beauty/CLAUDE.md << 'EOF'
# X AI Beauty Growth Agent System

## Global Rules
@config/global_rules.md

## Project Context
- Two accounts: EN (global) and JP (日本市場)
- All X operations use X API v2 Basic plan ($200/month)
- Impressions only via Playwright (own account pages)
- Human approval required before any post goes live
- All Telegram communication goes through Marc (COO)
- Task coordination via data/pipeline_state_{date}.json

## Agent Definitions
- @agents/marc.md — COO / Orchestrator / Reporter
- @agents/scout.md — Competitor Research
- @agents/strategist.md — Growth Strategy
- @agents/creator.md — Content Planning
- @agents/publisher.md — X API Posting & Outbound
- @agents/analyst.md — Metrics Collection

## Shared Conventions
- Date format: ISO 8601
- All times in JST
- Post IDs: {account}_{YYYYMMDD}_{slot}
- Log format: [YYYY-MM-DD HH:MM:SS] [AGENT] [LEVEL] message

## Tool Assignment (minimal per agent)
- Scout: X API read only
- Strategist: File read/write only
- Creator: File read/write only
- Publisher: X API write + media upload + rate limit counter
- Analyst: X API read + Playwright (impressions) + SQLite write
- Marc: Subagent invocation + file read/write + Telegram send
EOF

# Placeholder agent skill files
for agent in marc scout strategist creator publisher analyst; do
    agent_title="$(echo "$agent" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')"
    cat > agents/${agent}.md << AGENTEOF
# ${agent_title} Agent — Skill File
# Placeholder — to be built during Phases 1-4.
# See Technical Specification v2.4 for full agent definition.
AGENTEOF
done

# User-level preferences
mkdir -p ~/.claude
cat > ~/.claude/CLAUDE.md << 'EOF'
# Claude Code — User Preferences
- Respond in English
- Use concise output during pipeline execution
- Always validate JSON output before writing to files
- Log all actions with timestamps
EOF
```

---

## Step 9: Run Health Check

```bash
cat > scripts/health_check.py << 'PYEOF'
import os, sys, json, sqlite3, shutil

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
passed = failed = 0

def check(name, ok, hint=""):
    global passed, failed
    if ok: print(f"  ✅ {name}"); passed += 1
    else:
        print(f"  ❌ {name}"); failed += 1
        if hint: print(f"     → {hint}")

print("=" * 60)
print("  AI Beauty Agent System — Health Check")
print("=" * 60)

print("\n📋 System:")
check("Python 3.11+", sys.version_info >= (3, 11))
check("Node.js available", shutil.which("node") is not None, "Install Node.js 22+")
check("Claude Code available", shutil.which("claude") is not None, "npm install -g @anthropic-ai/claude-code")

print("\n📁 Project Structure:")
for d in ["config","data","media/pending","media/posted","logs","agents","scripts","backups"]:
    check(f"Dir: {d}", os.path.isdir(os.path.join(PROJECT, d)))

print("\n⚙️  Configuration:")
for f in ["config/accounts.json","config/competitors.json","config/global_rules.md","config/telegram_config.json"]:
    check(f"File: {f}", os.path.isfile(os.path.join(PROJECT, f)))
try:
    with open(os.path.join(PROJECT, "config/accounts.json")) as f:
        acc = json.load(f)
    check("X API credentials populated", acc["x_api"]["consumer_key"] != "REPLACE_ME", "Edit config/accounts.json")
    check("Telegram credentials populated", acc["telegram"]["bot_token"] != "REPLACE_ME", "Edit config/accounts.json")
except Exception as e:
    check("accounts.json valid", False, str(e))

print("\n🧠 Memory:")
check("Project CLAUDE.md", os.path.isfile(os.path.join(PROJECT, "CLAUDE.md")))
check("User CLAUDE.md", os.path.isfile(os.path.expanduser("~/.claude/CLAUDE.md")))

print("\n🤖 Agents:")
for a in ["marc","scout","strategist","creator","publisher","analyst"]:
    check(f"agents/{a}.md", os.path.isfile(os.path.join(PROJECT, f"agents/{a}.md")))

print("\n💾 Database:")
db = os.path.join(PROJECT, "data/metrics_history.db")
check("SQLite exists", os.path.isfile(db), "python3 scripts/db_manager.py")
if os.path.isfile(db):
    tables = [r[0] for r in sqlite3.connect(db).execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    for t in ["post_metrics","account_metrics","outbound_log","error_log"]:
        check(f"Table: {t}", t in tables)

print("\n" + "=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed, {failed} failed")
print("  🎉 Phase 0 complete!" if failed == 0 else f"  ⚠️  Fix {failed} issue(s) before Phase 1")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
PYEOF

python3 scripts/health_check.py
```

---

## Phase 0 Complete — What's Next?

When the health check passes, you're ready for **Phase 1: Scout + Strategist + Marc Foundation**.

### How Development Works

You trigger each agent manually from your CLI and inspect the results:

```bash
cd ~/x-ai-beauty
source .venv/bin/activate

# Test Scout
claude -p "$(cat agents/scout.md) Analyze all competitors." --dangerously-skip-permissions

# Inspect output
cat data/scout_report_$(date +%Y%m%d).json | python3 -m json.tool

# Test Strategist with Scout's output
claude -p "$(cat agents/strategist.md) Generate growth strategy." --dangerously-skip-permissions

# Inspect
cat data/strategy_current.json | python3 -m json.tool
```

Iterate on skill files until each agent produces reliable output. Only after all 6 agents work correctly do you move to VPS deployment and autonomous operation.

### Before Starting Phase 1

1. **Fill in `config/accounts.json`** with real X API keys and Telegram Bot token
2. **Fill in `config/competitors.json`** with 10+ AI beauty competitor handles

---

---

## Related Documents

- [Technical Specification v2.4](./specs/x-ai-beauty-spec-v2.3.md) — Full system design and agent specifications
- [Product Requirements Document v1.1](./specs/x-ai-beauty-prd-v1.md) — Goals, features, and success metrics
- [X Developer Terms Compliance Review](./specs/x-developer-terms-compliance-review.md) — 7 compliance issues and risk acceptance decisions
- [Project Context](./context.md) — Full project history, decisions, and architecture overview

---

*Document version: 2.1*
*Related: [Technical Specification v2.4](./specs/x-ai-beauty-spec-v2.3.md)*
