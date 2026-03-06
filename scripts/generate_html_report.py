#!/usr/bin/env python3
"""
HTML Report Generator for Telegram Review

Generates styled HTML reports from JSON pipeline data for mobile-friendly
review in Telegram's built-in browser.

Usage:
    python3 scripts/generate_html_report.py content_preview <EN_plan> <JP_plan> \
        --strategy <path> [--pipeline-state <path>]
    python3 scripts/generate_html_report.py daily_report <daily_report.json>
    python3 scripts/generate_html_report.py publish_report <EN_plan> <JP_plan> \
        [--outbound-log <path>] [--rate-limits <path>]
"""

import argparse
import json
import html
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")


# ─────────────────────────────────────────────
# Shared CSS Design System
# ─────────────────────────────────────────────

def base_css():
    return """
  :root {
    --bg: #0f172a;
    --card: #1e293b;
    --card-hover: #273548;
    --accent: #818cf8;
    --accent2: #f472b6;
    --accent3: #34d399;
    --text: #e2e8f0;
    --text-muted: #94a3b8;
    --text-dim: #64748b;
    --border: #334155;
    --danger: #ef4444;
    --warning: #f59e0b;
    --success: #22c55e;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 0;
  }
  .container { max-width: 1200px; margin: 0 auto; padding: 24px; }

  /* Header */
  .header {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4c1d95 100%);
    padding: 48px 24px;
    text-align: center;
    border-bottom: 2px solid var(--accent);
  }
  .header h1 { font-size: 2.2em; font-weight: 800; margin-bottom: 8px; }
  .header .subtitle { color: var(--accent); font-size: 1.1em; font-weight: 500; }
  .header .date { color: var(--text-muted); margin-top: 8px; }

  /* Navigation */
  .nav {
    background: var(--card);
    border-bottom: 1px solid var(--border);
    padding: 12px 24px;
    position: sticky;
    top: 0;
    z-index: 100;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
  }
  .nav a {
    color: var(--text-muted);
    text-decoration: none;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.85em;
    font-weight: 500;
    transition: all 0.2s;
  }
  .nav a:hover { background: var(--accent); color: white; }

  /* Sections */
  section { margin: 32px 0; }
  h2 {
    font-size: 1.6em;
    font-weight: 700;
    margin-bottom: 20px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--accent);
    display: flex;
    align-items: center;
    gap: 12px;
  }
  h3 {
    font-size: 1.2em;
    font-weight: 600;
    margin: 20px 0 12px;
    color: var(--accent);
  }
  h4 {
    font-size: 1em;
    font-weight: 600;
    margin: 16px 0 8px;
    color: var(--accent2);
  }

  /* Cards */
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
  }
  .card:hover { border-color: var(--accent); }
  .card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
    gap: 16px;
  }

  /* Stats */
  .stat-row {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin: 16px 0;
  }
  .stat-box {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 20px;
    flex: 1;
    min-width: 140px;
    text-align: center;
  }
  .stat-box .value {
    font-size: 1.8em;
    font-weight: 800;
    color: var(--accent);
  }
  .stat-box .label {
    font-size: 0.8em;
    color: var(--text-muted);
    margin-top: 4px;
  }
  .stat-box.pink .value { color: var(--accent2); }
  .stat-box.green .value { color: var(--accent3); }
  .stat-box.warning .value { color: var(--warning); }
  .stat-box.danger .value { color: var(--danger); }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9em;
  }
  th {
    background: #1a1a2e;
    color: var(--accent);
    font-weight: 600;
    text-align: left;
    padding: 10px 12px;
    border-bottom: 2px solid var(--accent);
    white-space: nowrap;
  }
  td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }
  tr:hover td { background: rgba(129, 140, 248, 0.05); }
  .table-wrap { overflow-x: auto; margin: 12px 0; border-radius: 8px; border: 1px solid var(--border); }

  /* Tags */
  .tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75em;
    font-weight: 600;
  }
  .tag-high { background: rgba(34, 197, 94, 0.15); color: var(--success); }
  .tag-medium { background: rgba(245, 158, 11, 0.15); color: var(--warning); }
  .tag-low { background: rgba(239, 68, 68, 0.15); color: var(--danger); }
  .tag-en { background: rgba(129, 140, 248, 0.2); color: var(--accent); }
  .tag-jp { background: rgba(244, 114, 182, 0.2); color: var(--accent2); }
  .tag-draft { background: rgba(148, 163, 184, 0.15); color: var(--text-muted); }
  .tag-approved { background: rgba(34, 197, 94, 0.15); color: var(--success); }
  .tag-posted { background: rgba(129, 140, 248, 0.2); color: var(--accent); }
  .tag-failed { background: rgba(239, 68, 68, 0.15); color: var(--danger); }

  /* Insight boxes */
  .insight {
    background: linear-gradient(135deg, rgba(129, 140, 248, 0.1) 0%, rgba(244, 114, 182, 0.05) 100%);
    border-left: 4px solid var(--accent);
    padding: 16px 20px;
    margin: 16px 0;
    border-radius: 0 8px 8px 0;
  }
  .insight.warning {
    border-left-color: var(--warning);
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.02) 100%);
  }
  .insight.danger {
    border-left-color: var(--danger);
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.02) 100%);
  }
  .insight.success {
    border-left-color: var(--success);
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(34, 197, 94, 0.02) 100%);
  }
  .insight strong { color: var(--accent); }

  /* Image prompt block */
  .image-prompt {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.85em;
  }
  .image-prompt .prompt-label {
    color: var(--accent);
    font-weight: 600;
    font-size: 0.8em;
    text-transform: uppercase;
    margin-bottom: 4px;
  }
  .image-prompt .prompt-text {
    color: var(--text-muted);
    line-height: 1.5;
  }
  .prompt-meta {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 8px;
    font-size: 0.8em;
    color: var(--text-dim);
  }
  .prompt-meta span { white-space: nowrap; }

  /* Bar chart */
  .bar-chart { margin: 12px 0; }
  .bar-row {
    display: flex;
    align-items: center;
    margin: 4px 0;
  }
  .bar-label {
    width: 140px;
    font-size: 0.8em;
    color: var(--text-muted);
    text-align: right;
    padding-right: 12px;
    flex-shrink: 0;
  }
  .bar-track {
    flex: 1;
    height: 20px;
    background: rgba(255,255,255,0.05);
    border-radius: 4px;
    overflow: hidden;
  }
  .bar-fill {
    height: 100%;
    border-radius: 4px;
    display: flex;
    align-items: center;
    padding-left: 8px;
    font-size: 0.7em;
    font-weight: 600;
    color: white;
    white-space: nowrap;
  }
  .bar-fill.purple { background: linear-gradient(90deg, var(--accent), #6366f1); }
  .bar-fill.pink { background: linear-gradient(90deg, var(--accent2), #ec4899); }
  .bar-fill.green { background: linear-gradient(90deg, var(--accent3), #10b981); }
  .bar-fill.warning { background: linear-gradient(90deg, var(--warning), #d97706); }
  .bar-fill.danger { background: linear-gradient(90deg, var(--danger), #dc2626); }

  /* Post text block */
  .post-text {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    white-space: pre-wrap;
    line-height: 1.6;
  }

  /* Reply templates */
  .reply-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 12px;
  }
  .reply-item {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.9em;
    color: var(--text-muted);
    font-style: italic;
  }

  /* Dividers */
  .divider {
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, var(--border) 50%, transparent 100%);
    margin: 32px 0;
  }

  /* Footer */
  .footer {
    text-align: center;
    padding: 32px 24px;
    color: var(--text-dim);
    font-size: 0.85em;
    border-top: 1px solid var(--border);
    margin-top: 48px;
  }
  .footer .cta {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700;
    font-size: 1.1em;
    margin-bottom: 8px;
  }

  /* Utility */
  .text-muted { color: var(--text-muted); }
  .text-accent { color: var(--accent); }
  .text-pink { color: var(--accent2); }
  .text-green { color: var(--accent3); }
  .text-danger { color: var(--danger); }
  .text-warning { color: var(--warning); }
  .text-sm { font-size: 0.85em; }
  .text-xs { font-size: 0.75em; }
  .font-bold { font-weight: 700; }
  .font-mono { font-family: 'SF Mono', 'Fira Code', monospace; }
  .mt-2 { margin-top: 8px; }
  .mt-4 { margin-top: 16px; }
  .mb-4 { margin-bottom: 16px; }

  /* Responsive */
  @media (max-width: 768px) {
    .card-grid { grid-template-columns: 1fr; }
    .reply-grid { grid-template-columns: 1fr; }
    .stat-row { flex-direction: column; }
    .header h1 { font-size: 1.6em; }
    .nav { flex-direction: column; align-items: stretch; text-align: center; }
    .bar-label { width: 100px; }
  }
"""


# ─────────────────────────────────────────────
# HTML Helpers
# ─────────────────────────────────────────────

def h(text):
    """HTML-escape text."""
    return html.escape(str(text)) if text is not None else ""


def html_head(title, subtitle, date_str):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{h(title)} — {h(date_str)}</title>
<style>{base_css()}</style>
</head>
<body>

<div class="header">
  <h1>{h(title)}</h1>
  <div class="subtitle">{h(subtitle)}</div>
  <div class="date">{h(date_str)}</div>
</div>
"""


def html_nav(links):
    """links: list of (href, label) tuples."""
    items = "\n  ".join(f'<a href="#{h(href)}">{h(label)}</a>' for href, label in links)
    return f'<nav class="nav">\n  {items}\n</nav>\n'


def html_footer(cta_text=None):
    cta = f'<div class="cta">{h(cta_text)}</div>\n  ' if cta_text else ""
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    return f"""
<div class="footer">
  {cta}<div>Generated {now} by Marc COO Agent</div>
</div>

</body>
</html>
"""


def stat_box(value, label, style=""):
    cls = f" {style}" if style else ""
    return f"""<div class="stat-box{cls}">
    <div class="value">{h(value)}</div>
    <div class="label">{h(label)}</div>
  </div>"""


def tag(text, style=""):
    cls = f" tag-{style}" if style else ""
    return f'<span class="tag{cls}">{h(text)}</span>'


def priority_tag(priority):
    return tag(priority, priority.lower() if priority else "")


def status_tag(status):
    return tag(status, status.lower() if status else "")


def account_tag(account):
    return tag(account, account.lower() if account else "")


def bar_row(label_text, pct, display_text, color="purple"):
    pct_clamped = max(0, min(100, pct))
    return f"""<div class="bar-row">
    <div class="bar-label">{h(label_text)}</div>
    <div class="bar-track">
      <div class="bar-fill {color}" style="width: {pct_clamped}%">{h(display_text)}</div>
    </div>
  </div>"""


# ─────────────────────────────────────────────
# JSON Loading
# ─────────────────────────────────────────────

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def try_load_json(path):
    if path and os.path.isfile(path):
        return load_json(path)
    return None


# ─────────────────────────────────────────────
# Content Preview Report
# ─────────────────────────────────────────────

def render_post_card(post, account):
    """Render a single post as an HTML card."""
    pid = post.get("id", "?")
    slot = post.get("slot", "?")
    time = post.get("scheduled_time", "?")
    category = post.get("category", "?")
    priority = post.get("priority", "medium")
    status = post.get("status", "draft")
    text = post.get("text", "")
    hashtags = post.get("hashtags", [])
    ab_variant = post.get("ab_test_variant")
    notes = post.get("notes", "")
    img = post.get("image_prompt", {})

    tags_html = " ".join([
        tag(f"Slot {slot}", ""),
        tag(time, ""),
        tag(category, "en" if account == "EN" else "jp"),
        priority_tag(priority),
        status_tag(status),
    ])
    if ab_variant:
        variant_style = "green" if ab_variant == "A" else "pink"
        tags_html += " " + tag(f"Variant {ab_variant}", variant_style)

    hashtags_html = " ".join(f'<span class="text-accent text-sm">{h(t)}</span>' for t in hashtags) if hashtags else ""

    img_html = ""
    if img:
        tool = img.get("tool", "?")
        prompt = img.get("prompt", "")
        neg = img.get("negative_prompt", "")
        style_ref = img.get("style_reference", "")
        aspect = img.get("aspect_ratio", "?")

        meta_parts = [f"Tool: {h(tool)}", f"Aspect: {h(aspect)}"]
        if style_ref:
            meta_parts.append(f"Style: {h(style_ref)}")
        meta_html = " ".join(f"<span>{p}</span>" for p in meta_parts)

        img_html = f"""<div class="image-prompt">
      <div class="prompt-label">Image Prompt</div>
      <div class="prompt-text">{h(prompt)}</div>"""
        if neg:
            img_html += f"""
      <div class="prompt-label mt-2">Negative Prompt</div>
      <div class="prompt-text">{h(neg)}</div>"""
        img_html += f"""
      <div class="prompt-meta">{meta_html}</div>
    </div>"""

    notes_html = f'<div class="text-sm text-dim mt-2">{h(notes)}</div>' if notes else ""

    return f"""<div class="card">
    <div style="margin-bottom: 8px">{tags_html}</div>
    <div class="font-bold" style="margin-bottom: 4px">{h(pid)}</div>
    <div class="post-text">{h(text)}</div>
    <div style="margin: 8px 0">{hashtags_html}</div>
    {img_html}
    {notes_html}
  </div>"""


def generate_content_preview(en_plan_path, jp_plan_path, strategy_path, pipeline_state_path):
    en = load_json(en_plan_path)
    jp = load_json(jp_plan_path)
    strategy = load_json(strategy_path) if strategy_path else None
    pipeline = try_load_json(pipeline_state_path)

    date = en.get("date", jp.get("date", "?"))
    en_posts = en.get("posts", [])
    jp_posts = jp.get("posts", [])
    total = len(en_posts) + len(jp_posts)

    # War Room scores from pipeline state
    war_room_en = "—"
    war_room_jp = "—"
    if pipeline:
        for task in pipeline.get("tasks", []):
            if task.get("id") == "war_room":
                notes = task.get("notes", "")
                # Parse "EN: 100/100 Excellent. JP: 100/100 Excellent."
                for part in notes.split("."):
                    part = part.strip()
                    if part.startswith("EN:"):
                        war_room_en = part.split("EN:")[1].strip().split(" ")[0] if "EN:" in part else "—"
                    elif part.startswith("JP:"):
                        war_room_jp = part.split("JP:")[1].strip().split(" ")[0] if "JP:" in part else "—"

    subtitle = f"{total} Posts Ready for Review | EN ({len(en_posts)}) + JP ({len(jp_posts)})"
    out = html_head("Content Preview", subtitle, date)

    # Nav
    nav_links = [
        ("overview", "Overview"),
        ("strategy", "Strategy"),
        ("en-posts", "EN Posts"),
        ("jp-posts", "JP Posts"),
        ("reply-templates", "Reply Templates"),
    ]
    out += html_nav(nav_links)
    out += '<div class="container">\n'

    # ── Overview ──
    out += '<section id="overview">\n<h2>Overview</h2>\n'
    out += '<div class="stat-row">\n'
    out += f'  {stat_box(total, "Total Posts")}\n'
    out += f'  {stat_box(len(en_posts), "EN Posts", "")}\n'
    out += f'  {stat_box(len(jp_posts), "JP Posts", "pink")}\n'
    out += f'  {stat_box(war_room_en, "EN War Room", "green")}\n'
    out += f'  {stat_box(war_room_jp, "JP War Room", "green")}\n'
    out += '</div>\n'

    # Pipeline timing
    if pipeline:
        duration = pipeline.get("duration_seconds", 0)
        status_val = pipeline.get("status", "?")
        warnings = pipeline.get("warnings", [])
        out += f'<div class="text-sm text-muted mt-4">Pipeline: {h(status_val)} in {duration}s</div>\n'
        for w in warnings:
            out += f'<div class="insight warning"><strong>Warning:</strong> {h(w)}</div>\n'

    out += '</section>\n'

    # ── Strategy Highlights ──
    if strategy:
        out += '<section id="strategy">\n<h2>Strategy Highlights</h2>\n'

        for acct in ["EN", "JP"]:
            acct_data = strategy.get(acct, {})
            insights = acct_data.get("key_insights", [])
            ab = acct_data.get("ab_test", {})
            risks = acct_data.get("risks", [])

            out += f'<h3>{account_tag(acct)} Key Insights</h3>\n'
            for insight_text in insights[:3]:
                out += f'<div class="insight">{h(insight_text)}</div>\n'

            if ab:
                out += f'<h4>A/B Test: {h(ab.get("variable", "?"))}</h4>\n'
                out += '<div class="card">\n'
                out += f'  <div><strong class="text-green">Variant A:</strong> {h(ab.get("variant_a", ""))}</div>\n'
                out += f'  <div class="mt-2"><strong class="text-pink">Variant B:</strong> {h(ab.get("variant_b", ""))}</div>\n'
                dur = ab.get("duration_days", "?")
                start = ab.get("start_date", "?")
                out += f'  <div class="text-sm text-muted mt-2">{dur} days starting {h(start)}</div>\n'
                out += '</div>\n'

            if risks:
                for risk in risks[:2]:
                    out += f'<div class="insight warning"><strong>Risk:</strong> {h(risk)}</div>\n'

        out += '</section>\n'

    # ── EN Posts ──
    out += '<section id="en-posts">\n<h2>EN Posts</h2>\n'
    for post in en_posts:
        out += render_post_card(post, "EN")
    out += '</section>\n'

    # ── JP Posts ──
    out += '<section id="jp-posts">\n<h2>JP Posts</h2>\n'
    for post in jp_posts:
        out += render_post_card(post, "JP")
    out += '</section>\n'

    # ── Reply Templates ──
    out += '<section id="reply-templates">\n<h2>Reply Templates</h2>\n'

    en_replies = en.get("reply_templates", [])
    jp_replies = jp.get("reply_templates", [])

    if en_replies:
        out += f'<h3>{account_tag("EN")} Reply Templates</h3>\n'
        out += '<div class="reply-grid">\n'
        for r in en_replies:
            out += f'  <div class="reply-item">{h(r)}</div>\n'
        out += '</div>\n'

    if jp_replies:
        out += f'<h3>{account_tag("JP")} Reply Templates</h3>\n'
        out += '<div class="reply-grid">\n'
        for r in jp_replies:
            out += f'  <div class="reply-item">{h(r)}</div>\n'
        out += '</div>\n'

    out += '</section>\n'

    out += '</div>\n'  # container
    out += html_footer("Use /approve in Telegram to approve this content")

    # Write output
    date_compact = date.replace("-", "")
    output_path = f"data/content_preview_{date_compact}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"[{datetime.now(JST).isoformat()}] [MARC] [INFO] Content preview HTML written to {output_path}")
    return output_path


# ─────────────────────────────────────────────
# Daily Report
# ─────────────────────────────────────────────

def render_account_section_daily(acct_key, data):
    """Render one account's section for the daily report."""
    out = ""
    followers = data.get("followers", 0)
    change = data.get("followers_change", 0)
    change_pct = data.get("followers_change_pct", 0)
    following = data.get("following", 0)
    total_posts_count = data.get("total_posts", 0)
    anomaly = data.get("anomaly", False)
    anomaly_detail = data.get("anomaly_detail")
    totals = data.get("totals", {})
    post_metrics = data.get("post_metrics", [])
    category_breakdown = data.get("category_breakdown", {})
    best_cat = data.get("best_category", "—")
    worst_cat = data.get("worst_category", "—")
    engagement_trend = data.get("engagement_trend", {})
    trend_notes = data.get("engagement_trend_notes", "")
    outbound = data.get("outbound", {})
    ab = data.get("ab_test_status", {})
    best_post = data.get("best_performing_post", {})

    change_sign = "+" if change >= 0 else ""
    change_color = "green" if change > 0 else ("danger" if change < 0 else "")

    out += f'<h3>{account_tag(acct_key)} Account Overview</h3>\n'
    out += '<div class="stat-row">\n'
    out += f'  {stat_box(followers, "Followers")}\n'
    out += f'  {stat_box(f"{change_sign}{change}", f"Change ({change_pct:+.1f}%)", change_color)}\n'
    out += f'  {stat_box(following, "Following")}\n'
    out += f'  {stat_box(total_posts_count, "Total Posts")}\n'
    out += '</div>\n'

    if anomaly and anomaly_detail:
        out += f'<div class="insight danger"><strong>Anomaly Detected:</strong> {h(anomaly_detail)}</div>\n'

    # Engagement totals
    out += '<h4>Engagement Totals</h4>\n'
    out += '<div class="stat-row">\n'
    out += f'  {stat_box(totals.get("likes", 0), "Likes")}\n'
    out += f'  {stat_box(totals.get("retweets", 0), "Retweets", "pink")}\n'
    out += f'  {stat_box(totals.get("replies", 0), "Replies")}\n'
    out += f'  {stat_box(totals.get("quotes", 0), "Quotes")}\n'
    out += f'  {stat_box(totals.get("bookmarks", 0), "Bookmarks", "green")}\n'
    out += '</div>\n'

    # Post performance table
    if post_metrics:
        out += '<h4>Post Performance</h4>\n'
        out += '<div class="table-wrap"><table>\n'
        out += '<tr><th>Post ID</th><th>Category</th><th>Likes</th><th>RTs</th><th>Replies</th><th>Hours</th><th>A/B</th></tr>\n'
        for pm in post_metrics:
            variant = pm.get("ab_test_variant", "—")
            out += f'<tr><td class="font-mono text-sm">{h(pm.get("post_id", ""))}</td>'
            out += f'<td>{h(pm.get("category", ""))}</td>'
            out += f'<td>{pm.get("likes", 0)}</td>'
            out += f'<td>{pm.get("retweets", 0)}</td>'
            out += f'<td>{pm.get("replies", 0)}</td>'
            out += f'<td>{pm.get("hours_after_post", "—")}</td>'
            out += f'<td>{h(variant)}</td></tr>\n'
        out += '</table></div>\n'

    # Category breakdown as bar chart
    if category_breakdown:
        out += '<h4>Category Breakdown</h4>\n'
        max_eng = max((v.get("total_engagement", 0) for v in category_breakdown.values()), default=1) or 1
        out += '<div class="bar-chart">\n'
        for cat, vals in sorted(category_breakdown.items(), key=lambda x: x[1].get("total_engagement", 0), reverse=True):
            eng = vals.get("total_engagement", 0)
            pct = (eng / max_eng) * 100
            color = "green" if cat == best_cat else ("danger" if cat == worst_cat else "purple")
            out += f'  {bar_row(cat, pct, str(eng) + " eng", color)}\n'
        out += '</div>\n'

    # Engagement trend
    if engagement_trend:
        out += '<h4>Engagement Trend</h4>\n'
        out += '<div class="table-wrap"><table>\n'
        out += '<tr><th>Metric</th><th>Yesterday</th><th>Today</th><th>Change</th><th>Direction</th></tr>\n'
        for metric, vals in engagement_trend.items():
            direction = vals.get("direction", "flat")
            arrow = {"up": "&#9650;", "down": "&#9660;", "flat": "&#9644;"}.get(direction, "")
            dir_color = {"up": "text-green", "down": "text-danger", "flat": "text-muted"}.get(direction, "")
            out += f'<tr><td>{h(metric)}</td>'
            out += f'<td>{vals.get("yesterday", 0)}</td>'
            out += f'<td>{vals.get("today", 0)}</td>'
            out += f'<td>{vals.get("change_pct", 0):+.1f}%</td>'
            out += f'<td class="{dir_color}">{arrow} {h(direction)}</td></tr>\n'
        out += '</table></div>\n'
        if trend_notes:
            out += f'<div class="text-sm text-muted">{h(trend_notes)}</div>\n'

    # A/B test
    if ab and ab.get("variable"):
        out += f'<h4>A/B Test: {h(ab.get("variable", ""))}</h4>\n'
        out += '<div class="card">\n'
        out += f'  <div><strong class="text-green">Variant A:</strong> {h(ab.get("variant_a", ""))}</div>\n'
        out += f'  <div class="mt-2"><strong class="text-pink">Variant B:</strong> {h(ab.get("variant_b", ""))}</div>\n'
        out += '  <div class="stat-row mt-4">\n'
        va_eng = ab.get("variant_a_avg_engagement", 0)
        vb_eng = ab.get("variant_b_avg_engagement", 0)
        verdict = ab.get("verdict", "—")
        out += f'    {stat_box(f"{va_eng:.2f}", "Variant A Avg Eng", "green")}\n'
        out += f'    {stat_box(f"{vb_eng:.2f}", "Variant B Avg Eng", "pink")}\n'
        out += f'    {stat_box(verdict, "Verdict")}\n'
        out += '  </div>\n'
        if ab.get("notes"):
            out += f'  <div class="text-sm text-muted mt-2">{h(ab["notes"])}</div>\n'
        out += '</div>\n'

    # Outbound
    if outbound:
        out += '<h4>Outbound Engagement</h4>\n'
        out += '<div class="stat-row">\n'
        out += f'  {stat_box(outbound.get("likes", 0), "Likes Sent")}\n'
        out += f'  {stat_box(outbound.get("replies", 0), "Replies Sent", "pink")}\n'
        out += f'  {stat_box(outbound.get("follows", 0), "Follows Sent", "green")}\n'
        out += '</div>\n'
        if outbound.get("all_dry_run"):
            out += '<div class="insight warning"><strong>Note:</strong> All outbound actions were dry-run only</div>\n'
        if outbound.get("notes"):
            out += f'<div class="text-sm text-muted">{h(outbound["notes"])}</div>\n'

    # Best post
    if best_post and best_post.get("post_id"):
        out += '<h4>Best Performing Post</h4>\n'
        out += '<div class="card">\n'
        out += f'  <div class="font-bold text-accent">{h(best_post.get("post_id", ""))}</div>\n'
        out += f'  <div class="text-sm text-muted">{h(best_post.get("category", ""))}</div>\n'
        eng = best_post.get("total_engagement", 0)
        likes = best_post.get("likes", 0)
        rts = best_post.get("retweets", 0)
        out += f'  <div class="mt-2">{eng} total engagement ({likes} likes, {rts} RTs)</div>\n'
        out += '</div>\n'

    return out


def generate_daily_report(report_path):
    report = load_json(report_path)
    date = report.get("date", "?")
    accounts = report.get("accounts", {})
    alerts = report.get("telegram_alerts", [])

    en = accounts.get("EN", {})
    jp = accounts.get("JP", {})

    en_followers = en.get("followers", 0)
    jp_followers = jp.get("followers", 0)
    en_likes = en.get("totals", {}).get("likes", 0)
    jp_likes = jp.get("totals", {}).get("likes", 0)

    subtitle = f"EN: {en_followers} followers | JP: {jp_followers} followers"
    out = html_head("Daily Performance Report", subtitle, date)

    nav_links = [
        ("overview", "Overview"),
        ("en-account", "EN Account"),
        ("jp-account", "JP Account"),
        ("alerts", "Alerts"),
    ]
    out += html_nav(nav_links)
    out += '<div class="container">\n'

    # ── Overview ──
    out += '<section id="overview">\n<h2>Overview</h2>\n'
    out += '<div class="stat-row">\n'
    out += f'  {stat_box(en_followers, "EN Followers")}\n'
    out += f'  {stat_box(jp_followers, "JP Followers", "pink")}\n'
    out += f'  {stat_box(en_likes, "EN Likes", "green")}\n'
    out += f'  {stat_box(jp_likes, "JP Likes", "green")}\n'
    out += '</div>\n'

    # Data notes
    data_notes = report.get("data_notes")
    if data_notes:
        out += f'<div class="insight warning">{h(data_notes)}</div>\n'

    out += '</section>\n'

    # ── EN Account ──
    out += '<section id="en-account">\n<h2>EN Account</h2>\n'
    out += render_account_section_daily("EN", en)
    out += '</section>\n'

    # ── JP Account ──
    out += '<section id="jp-account">\n<h2>JP Account</h2>\n'
    out += render_account_section_daily("JP", jp)
    out += '</section>\n'

    # ── Alerts ──
    out += '<section id="alerts">\n<h2>Alerts</h2>\n'
    if alerts:
        for alert in alerts:
            out += f'<div class="insight danger">{h(alert)}</div>\n'
    else:
        out += '<div class="insight success">No anomalies or alerts detected today.</div>\n'
    out += '</section>\n'

    out += '</div>\n'  # container
    out += html_footer()

    date_compact = date.replace("-", "")
    output_path = f"data/daily_report_{date_compact}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"[{datetime.now(JST).isoformat()}] [MARC] [INFO] Daily report HTML written to {output_path}")
    return output_path


# ─────────────────────────────────────────────
# Publish Report
# ─────────────────────────────────────────────

def generate_publish_report(en_plan_path, jp_plan_path, outbound_log_path, rate_limits_path):
    en = load_json(en_plan_path)
    jp = load_json(jp_plan_path)
    outbound = try_load_json(outbound_log_path)
    rate_limits = try_load_json(rate_limits_path)

    date = en.get("date", jp.get("date", "?"))
    en_posts = en.get("posts", [])
    jp_posts = jp.get("posts", [])

    posted_en = [p for p in en_posts if p.get("status") == "posted"]
    posted_jp = [p for p in jp_posts if p.get("status") == "posted"]
    failed_en = [p for p in en_posts if p.get("status") == "failed"]
    failed_jp = [p for p in jp_posts if p.get("status") == "failed"]

    subtitle = f"{len(posted_en) + len(posted_jp)} posted | {len(failed_en) + len(failed_jp)} failed"
    out = html_head("Publish Report", subtitle, date)

    nav_links = [
        ("summary", "Summary"),
        ("en-posts", "EN Posts"),
        ("jp-posts", "JP Posts"),
        ("outbound", "Outbound"),
        ("rate-limits", "Rate Limits"),
    ]
    out += html_nav(nav_links)
    out += '<div class="container">\n'

    # ── Summary ──
    out += '<section id="summary">\n<h2>Summary</h2>\n'
    out += '<div class="stat-row">\n'
    out += f'  {stat_box(len(posted_en), "EN Posted", "green")}\n'
    out += f'  {stat_box(len(posted_jp), "JP Posted", "green")}\n'
    out += f'  {stat_box(len(failed_en), "EN Failed", "danger" if failed_en else "")}\n'
    out += f'  {stat_box(len(failed_jp), "JP Failed", "danger" if failed_jp else "")}\n'
    out += '</div>\n'
    out += '</section>\n'

    # ── EN Posts ──
    out += '<section id="en-posts">\n<h2>EN Posts</h2>\n'
    for post in en_posts:
        out += render_publish_post_card(post, "EN")
    out += '</section>\n'

    # ── JP Posts ──
    out += '<section id="jp-posts">\n<h2>JP Posts</h2>\n'
    for post in jp_posts:
        out += render_publish_post_card(post, "JP")
    out += '</section>\n'

    # ── Outbound ──
    out += '<section id="outbound">\n<h2>Outbound Engagement</h2>\n'
    if outbound:
        entries = outbound if isinstance(outbound, list) else outbound.get("actions", outbound.get("entries", []))
        if isinstance(entries, list):
            likes_count = sum(1 for e in entries if e.get("action") == "like")
            replies_count = sum(1 for e in entries if e.get("action") == "reply")
            follows_count = sum(1 for e in entries if e.get("action") == "follow")
            failures = sum(1 for e in entries if e.get("status") == "failed")
            out += '<div class="stat-row">\n'
            out += f'  {stat_box(likes_count, "Likes Sent")}\n'
            out += f'  {stat_box(replies_count, "Replies Sent", "pink")}\n'
            out += f'  {stat_box(follows_count, "Follows Sent", "green")}\n'
            out += f'  {stat_box(failures, "Failures", "danger" if failures else "")}\n'
            out += '</div>\n'

            # Show details table
            if entries:
                out += '<div class="table-wrap"><table>\n'
                out += '<tr><th>Action</th><th>Target</th><th>Status</th><th>Account</th></tr>\n'
                for e in entries[:50]:  # cap at 50 rows
                    status_cls = "text-green" if e.get("status") == "success" else "text-danger"
                    out += f'<tr><td>{h(e.get("action", ""))}</td>'
                    out += f'<td>{h(e.get("target", e.get("target_handle", "")))}</td>'
                    out += f'<td class="{status_cls}">{h(e.get("status", ""))}</td>'
                    out += f'<td>{h(e.get("account", ""))}</td></tr>\n'
                out += '</table></div>\n'
        else:
            out += f'<div class="card"><pre>{h(json.dumps(outbound, indent=2, ensure_ascii=False)[:2000])}</pre></div>\n'
    else:
        out += '<div class="text-muted">No outbound log available.</div>\n'
    out += '</section>\n'

    # ── Rate Limits ──
    out += '<section id="rate-limits">\n<h2>Rate Limit Usage</h2>\n'
    if rate_limits:
        for acct_key in ["EN", "JP"]:
            acct_limits = rate_limits.get(acct_key, rate_limits.get(acct_key.lower(), {}))
            if not acct_limits:
                continue
            out += f'<h3>{account_tag(acct_key)} Rate Limits</h3>\n'
            out += '<div class="bar-chart">\n'

            limits_map = {
                "posts": ("Posts", 5),
                "likes": ("Likes", 30),
                "replies": ("Replies", 10),
                "follows": ("Follows", 5),
            }
            for key, (label, max_val) in limits_map.items():
                used = acct_limits.get(key, 0)
                pct = (used / max_val * 100) if max_val > 0 else 0
                color = "danger" if pct >= 90 else ("warning" if pct >= 60 else "green")
                out += f'  {bar_row(label, pct, f"{used}/{max_val}", color)}\n'

            out += '</div>\n'
    else:
        out += '<div class="text-muted">No rate limit data available.</div>\n'
    out += '</section>\n'

    out += '</div>\n'  # container
    out += html_footer()

    date_compact = date.replace("-", "")
    output_path = f"data/publish_report_{date_compact}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"[{datetime.now(JST).isoformat()}] [MARC] [INFO] Publish report HTML written to {output_path}")
    return output_path


def render_publish_post_card(post, account):
    """Render a post card for the publish report — shows posted/failed status with URLs."""
    pid = post.get("id", "?")
    slot = post.get("slot", "?")
    status = post.get("status", "?")
    text = post.get("text", "")
    tweet_id = post.get("tweet_id")
    post_url = post.get("post_url")
    posted_at = post.get("posted_at")
    error = post.get("error")
    failed_at = post.get("failed_at")

    tags_html = " ".join([
        tag(f"Slot {slot}", ""),
        tag(post.get("category", ""), "en" if account == "EN" else "jp"),
        status_tag(status),
    ])

    url_html = ""
    if post_url:
        url_html = f'<div class="mt-2"><a href="{h(post_url)}" target="_blank" style="color: var(--accent); text-decoration: underline;">{h(post_url)}</a></div>\n'
    elif tweet_id:
        url_html = f'<div class="mt-2 text-sm text-muted">Tweet ID: {h(tweet_id)}</div>\n'

    time_html = ""
    if posted_at:
        time_html = f'<div class="text-sm text-muted">Posted: {h(posted_at)}</div>\n'
    elif failed_at:
        time_html = f'<div class="text-sm text-danger">Failed: {h(failed_at)}</div>\n'

    error_html = ""
    if error:
        error_html = f'<div class="insight danger"><strong>Error:</strong> {h(error)}</div>\n'

    return f"""<div class="card">
    <div style="margin-bottom: 8px">{tags_html}</div>
    <div class="font-bold" style="margin-bottom: 4px">{h(pid)}</div>
    <div class="post-text">{h(text)}</div>
    {url_html}
    {time_html}
    {error_html}
  </div>"""


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate HTML reports for Telegram review")
    subparsers = parser.add_subparsers(dest="report_type", required=True)

    # content_preview
    cp = subparsers.add_parser("content_preview", help="Generate content preview HTML")
    cp.add_argument("en_plan", help="Path to EN content plan JSON")
    cp.add_argument("jp_plan", help="Path to JP content plan JSON")
    cp.add_argument("--strategy", required=True, help="Path to strategy JSON")
    cp.add_argument("--pipeline-state", help="Path to pipeline state JSON")

    # daily_report
    dr = subparsers.add_parser("daily_report", help="Generate daily report HTML")
    dr.add_argument("report", help="Path to daily report JSON")

    # publish_report
    pr = subparsers.add_parser("publish_report", help="Generate publish report HTML")
    pr.add_argument("en_plan", help="Path to EN content plan JSON (with posted status)")
    pr.add_argument("jp_plan", help="Path to JP content plan JSON (with posted status)")
    pr.add_argument("--outbound-log", help="Path to outbound log JSON")
    pr.add_argument("--rate-limits", help="Path to rate limits JSON")

    args = parser.parse_args()

    if args.report_type == "content_preview":
        path = generate_content_preview(
            args.en_plan, args.jp_plan, args.strategy,
            getattr(args, "pipeline_state", None)
        )
    elif args.report_type == "daily_report":
        path = generate_daily_report(args.report)
    elif args.report_type == "publish_report":
        path = generate_publish_report(
            args.en_plan, args.jp_plan,
            getattr(args, "outbound_log", None),
            getattr(args, "rate_limits", None)
        )
    else:
        print(f"Unknown report type: {args.report_type}", file=sys.stderr)
        sys.exit(1)

    print(f"Output: {path}")


if __name__ == "__main__":
    main()
