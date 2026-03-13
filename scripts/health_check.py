import os, sys, json, sqlite3, shutil

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
passed = failed = 0

def check(name, ok, hint=""):
    global passed, failed
    if ok:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name}")
        failed += 1
        if hint:
            print(f"     → {hint}")

print("=" * 60)
print("  AI Beauty Agent System — Health Check")
print("=" * 60)

print("\n📋 System:")
check("Python 3.11+", sys.version_info >= (3, 11))
check("Node.js available", shutil.which("node") is not None, "Install Node.js 22+")
check("Claude Code available", shutil.which("claude") is not None, "npm install -g @anthropic-ai/claude-code")

print("\n📁 Project Structure:")
for d in ["config", "data", "media/pending", "media/posted", "logs", "agents", "scripts", "backups"]:
    check(f"Dir: {d}", os.path.isdir(os.path.join(PROJECT, d)))

print("\n⚙️  Configuration:")
for f in ["config/accounts.json", "config/competitors.json", "config/global_rules.md", "config/telegram_config.json"]:
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
for a in ["marc", "scout", "strategist", "creator", "publisher", "analyst"]:
    check(f"agents/{a}.md", os.path.isfile(os.path.join(PROJECT, f"agents/{a}.md")))

print("\n💾 Database:")
db = os.path.join(PROJECT, "data", "metrics", "metrics_history.db")
check("SQLite exists", os.path.isfile(db), "Run: python3 scripts/db_manager.py")
if os.path.isfile(db):
    tables = [r[0] for r in sqlite3.connect(db).execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    for t in ["post_metrics", "account_metrics", "outbound_log", "error_log"]:
        check(f"Table: {t}", t in tables)

print("\n" + "=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed, {failed} failed")
print("  🎉 Phase 0 complete!" if failed == 0 else f"  ⚠️  Fix {failed} issue(s) before Phase 1")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
