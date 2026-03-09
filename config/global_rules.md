# Global Rules
# Format: - Rule text (learned YYYY-MM-DD)

- Human approval is required before any post goes live
- All X operations use official API (Playwright only for impression scraping)
- Conservative outbound limits: max 30 likes, 10 replies, 5 follows per account per day
- Never start a post with @ (X treats it as reply, hidden from followers' feeds)
- Compress images to <2MB before upload
- When an API action fails (e.g. reply 403), don't just report and stop — find an alternative path. If the agent can't do it programmatically, escalate to the human with exact actionable instructions (which account, which post URL, what text). Agents think and adapt; scripts just fail. (learned 2026-03-09)
