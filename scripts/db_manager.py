import sqlite3, sys, os

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT, "data", "metrics", "metrics_history.db")


def _connect():
    """Create a connection with WAL mode and row_factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init():
    conn = _connect()
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

    # Migration: add timestamp column to outbound_log if missing
    cols = [row[1] for row in c.execute("PRAGMA table_info(outbound_log)").fetchall()]
    if "timestamp" not in cols:
        c.execute("ALTER TABLE outbound_log ADD COLUMN timestamp DATETIME")

    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_PATH}")


# --- Insert functions ---

def insert_post_metrics(post_id, tweet_id, account, measured_at, hours_after_post,
                        likes, retweets, replies, quotes, bookmarks, impressions,
                        engagement_rate, source):
    """Insert or replace a post_metrics row."""
    conn = _connect()
    conn.execute(
        """INSERT OR REPLACE INTO post_metrics
           (post_id, tweet_id, account, measured_at, hours_after_post,
            likes, retweets, replies, quotes, bookmarks, impressions,
            engagement_rate, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (post_id, tweet_id, account, measured_at, hours_after_post,
         likes, retweets, replies, quotes, bookmarks, impressions,
         engagement_rate, source))
    conn.commit()
    conn.close()


def insert_account_metrics(account, date, followers, following, total_posts, followers_change):
    """Insert or replace an account_metrics row."""
    conn = _connect()
    conn.execute(
        """INSERT OR REPLACE INTO account_metrics
           (account, date, followers, following, total_posts, followers_change)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (account, date, followers, following, total_posts, followers_change))
    conn.commit()
    conn.close()


def insert_outbound_log(date, account, action_type, target_handle, target_tweet_id,
                        success, api_response_code, timestamp):
    """Insert an outbound_log row (plain INSERT, no PK)."""
    conn = _connect()
    conn.execute(
        """INSERT INTO outbound_log
           (date, account, action_type, target_handle, target_tweet_id,
            success, api_response_code, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (date, account, action_type, target_handle, target_tweet_id,
         success, api_response_code, timestamp))
    conn.commit()
    conn.close()


def insert_error_log(timestamp, agent, error_type, error_message, resolution, resolved):
    """Insert an error_log row."""
    conn = _connect()
    conn.execute(
        """INSERT INTO error_log
           (timestamp, agent, error_type, error_message, resolution, resolved)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (timestamp, agent, error_type, error_message, resolution, resolved))
    conn.commit()
    conn.close()


# --- Query functions ---

def get_yesterday_followers(account):
    """Get the most recent followers count before today. Returns int or None."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d")
    conn = _connect()
    row = conn.execute(
        """SELECT followers FROM account_metrics
           WHERE account = ? AND date < ?
           ORDER BY date DESC LIMIT 1""",
        (account, today)).fetchone()
    conn.close()
    return row["followers"] if row else None


def get_post_metrics(post_id, measured_at=None):
    """Get post_metrics rows for a post_id. Returns list of dicts."""
    conn = _connect()
    if measured_at:
        rows = conn.execute(
            "SELECT * FROM post_metrics WHERE post_id = ? AND measured_at = ?",
            (post_id, measured_at)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM post_metrics WHERE post_id = ? ORDER BY measured_at",
            (post_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_account_metrics_range(account, start_date, end_date):
    """Get account_metrics rows for a date range. Returns list of dicts."""
    conn = _connect()
    rows = conn.execute(
        """SELECT * FROM account_metrics
           WHERE account = ? AND date >= ? AND date <= ?
           ORDER BY date""",
        (account, start_date, end_date)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_daily_summary(account, date):
    """Get aggregated daily summary: account snapshot + post metrics. Returns dict."""
    conn = _connect()
    # Account snapshot
    acct_row = conn.execute(
        "SELECT * FROM account_metrics WHERE account = ? AND date = ?",
        (account, date)).fetchone()
    # Post metrics for the day (latest measurement per post)
    post_rows = conn.execute(
        """SELECT pm.* FROM post_metrics pm
           INNER JOIN (
               SELECT post_id, MAX(measured_at) as latest
               FROM post_metrics WHERE account = ? AND measured_at LIKE ?
               GROUP BY post_id
           ) latest ON pm.post_id = latest.post_id AND pm.measured_at = latest.latest""",
        (account, f"{date}%")).fetchall()
    conn.close()

    summary = {
        "account": account,
        "date": date,
        "account_metrics": dict(acct_row) if acct_row else None,
        "post_metrics": [dict(r) for r in post_rows],
        "totals": {
            "likes": sum(r["likes"] or 0 for r in post_rows),
            "retweets": sum(r["retweets"] or 0 for r in post_rows),
            "replies": sum(r["replies"] or 0 for r in post_rows),
            "quotes": sum(r["quotes"] or 0 for r in post_rows),
            "bookmarks": sum(r["bookmarks"] or 0 for r in post_rows),
        },
    }
    return summary


def get_outbound_log(account, date):
    """Get outbound_log rows for an account and date. Returns list of dicts."""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM outbound_log WHERE account = ? AND date = ? ORDER BY timestamp",
        (account, date)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init()
