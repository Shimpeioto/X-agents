# Global Rules
# Format: - Rule text (learned YYYY-MM-DD)

- Human approval is required before any post goes live
- All X operations use official API (Playwright only for impression scraping)
- Conservative outbound limits: max 30 likes, 0 replies, max 5 follows per account per day (operator decision: no API replies — 403 blocked for new accounts, learned 2026-03-13; auto-follows re-enabled 2026-03-14)
- No auto-replies — all replies are manual. Outbound agent identifies 10-15 reply targets per run and escalates to operator with tweet URL + pre-drafted reply text. daily_replies via API = 0 permanently. Manual replies target: 10-15/day (replies are #1 growth lever — single reply generated 2,823 impressions). (operator decision: API replies disabled 2026-03-13; manual reply target expanded 2026-03-18)
- Never start a post with @ (X treats it as reply, hidden from followers' feeds)
- Compress images to <2MB before upload
- When an API action fails (e.g. reply 403), don't just report and stop — find an alternative path. If the agent can't do it programmatically, escalate to the human with exact actionable instructions (which account, which post URL, what text). Agents think and adapt; scripts just fail. (learned 2026-03-09)
- Post approval and scheduling are ATOMIC: when approving posts, MUST set status to "approved" in JSON AND immediately run schedule_slots.py to create LaunchAgents. NEVER call publisher.py post directly — always go through schedule_slots.py. Direct publisher.py calls bypass slot scheduling and publish immediately. (learned 2026-03-21)
