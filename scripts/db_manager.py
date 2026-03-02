import sqlite3, sys, os

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT, "data", "metrics_history.db")

def init():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS post_metrics (
        post_id TEXT NOT NULL,
        tweet_id TEXT NOT NULL,
        account TEXT NOT NULL,
        measured_at DATETIME NOT NULL,
        hours_after_post INTEGER NOT NULL,
        likes INTEGER DEFAULT 0,
        retweets INTEGER DEFAULT 0,
        replies INTEGER DEFAULT 0,
        quotes INTEGER DEFAULT 0,
        bookmarks INTEGER DEFAULT 0,
        impressions INTEGER,
        engagement_rate REAL,
        source TEXT NOT NULL,
        PRIMARY KEY (post_id, measured_at)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS account_metrics (
        account TEXT NOT NULL,
        date DATE NOT NULL,
        followers INTEGER,
        following INTEGER,
        total_posts INTEGER,
        followers_change INTEGER,
        PRIMARY KEY (account, date)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS outbound_log (
        date DATE NOT NULL,
        account TEXT NOT NULL,
        action_type TEXT NOT NULL,
        target_handle TEXT,
        target_tweet_id TEXT,
        success BOOLEAN NOT NULL DEFAULT 1,
        api_response_code INTEGER
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS error_log (
        timestamp DATETIME NOT NULL,
        agent TEXT NOT NULL,
        error_type TEXT NOT NULL,
        error_message TEXT,
        resolution TEXT,
        resolved BOOLEAN NOT NULL DEFAULT 0
    )""")

    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_PATH}")

if __name__ == "__main__":
    init()
