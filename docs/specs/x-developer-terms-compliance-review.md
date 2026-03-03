# X Developer Terms — Compliance Review

**Reviewed**: March 2, 2026
**Sources**: [Developer Agreement](https://docs.x.com/developer-terms/agreement), [Developer Policy](https://docs.x.com/developer-terms/policy), [Automation Rules](https://help.x.com/en/rules-and-policies/x-automation)
**Status**: Recorded for review during implementation — no spec changes made yet

---

## Issues Requiring Resolution

### 🔴 ISSUE 1: Automated Likes Are Prohibited

**Current spec**: Publisher performs up to 30 automated likes/day per account as outbound engagement.
**Rule**: X Automation Rules explicitly state automated liking is not permitted. Engagement farming via automation (likes, retweets, bookmarks) is prohibited.
**Risk**: Account suspension.
**Options**: (a) Remove automated likes entirely, (b) Make likes manual-only.
**Review during**: Phase 3 (Publisher implementation).
**Decision**: Risk accepted. Implement with awareness; monitor for enforcement changes.

---

### 🔴 ISSUE 2: Automated Follows Risk "Bulk/Aggressive" Violation

**Current spec**: Publisher performs up to 5 automated follows/day per account.
**Rule**: Bulk, aggressive, or indiscriminate following via automation is prohibited. Even low-volume automated follows can be flagged as inorganic following behavior.
**Risk**: Account restriction or suspension.
**Options**: (a) Remove automated follows entirely, (b) Limit to manual follows only, (c) Allow only "follow-back" automation (follow users who already follow us).
**Review during**: Phase 3 (Publisher implementation).
**Decision**: Risk accepted. Implement with awareness; monitor for enforcement changes.

---

### 🔴 ISSUE 3: Automated Replies Require Prior User Interaction

**Current spec**: Publisher performs up to 10 outbound replies/day, including cold outreach.
**Rule**: Automated replies may only be sent in response to a user's interaction with your account. One automated reply per user interaction. Unsolicited automated mentions/replies are prohibited.
**Risk**: Account suspension — this is actively enforced (see X Developer Community enforcement cases).
**Options**: (a) Only allow replies to users who engaged with our posts first, (b) Remove outbound replies entirely, (c) Keep reply capability but restrict to reactive-only.
**Review during**: Phase 3 (Publisher implementation).
**Decision**: Risk accepted. Implement with awareness; monitor for enforcement changes.

---

### 🔴 ISSUE 4: Playwright Scraping Is Non-API Automation (Banned)

**Current spec**: Analyst uses Playwright to scrape impression counts from our own account pages (because Basic API doesn't provide impressions).
**Rule**: Non-API-based forms of automation (scripting the X website) are explicitly prohibited and may result in permanent account suspension.
**Risk**: Permanent account suspension.
**Options**: (a) Remove Playwright entirely — accept that impressions are unavailable on Basic plan, (b) Upgrade to a plan that provides impressions via API, (c) Use only API-available metrics (likes, retweets, replies, quotes, bookmarks) as proxy for reach.
**Review during**: Phase 4 (Analyst implementation).
**Decision**: Risk accepted. Implement with awareness; monitor for enforcement changes. Impression data value justifies the risk.

---

### 🟡 ISSUE 5: Bot Account Labeling Required

**Current spec**: No mention of bot/automation labeling in account bios.
**Rule**: API-based automated accounts must clearly indicate what the account is and who is responsible for it in the profile bio.
**Nuance**: Our accounts use human-approved posting (you approve every post before it goes live). This may not qualify as a "bot account" in the traditional sense. However, since the actual POST call is made via API automation, disclosure is safest.
**Options**: (a) Add "Automated/AI-assisted posting | Operated by [name]" to bios, (b) Add a softer disclosure like "AI-curated content" since human approval is in the loop, (c) Determine if human-in-the-loop approval exempts us from bot labeling.
**Review during**: Phase 0 (account setup) or Phase 3 (before first real post).

---

### 🟡 ISSUE 6: Cross-Account Content Must Be Unique

**Current spec**: EN and JP accounts run in parallel. Creator generates content plans for both.
**Rule**: Posting duplicative or substantially similar content across multiple accounts you operate is prohibited.
**Nuance**: Since EN and JP are in different languages, a translated version of the same post might be considered "substantially similar." Same image + translated caption is likely a violation.
**Options**: (a) Require genuinely distinct content themes/images per account, (b) Allow shared images only if captions and context are meaningfully different, (c) Add explicit rule to Creator's skill file.
**Review during**: Phase 2 (Creator implementation).

---

### 🟡 ISSUE 7: Use Case Description Is Binding

**Current spec**: Runbook suggests a sample use case description for the developer application.
**Rule**: Your use case description is binding. Any substantive deviation may result in enforcement action. You must notify X of changes and receive approval.
**Action**: Write the use case description carefully to cover all planned functionality (automated posting, metric collection, outbound engagement). Avoid over-promising or describing features not yet built.
**Review during**: Phase 0 (developer account application — Step 3).

---

## Confirmed Compliant

| Area | Status | Notes |
|---|---|---|
| Basic plan scope | ✅ | Early-stage integration for own brand accounts |
| Single developer app | ✅ | One app for both EN and JP accounts |
| Automated posting of original content | ✅ | Explicitly permitted via API |
| AI-generated content | ✅ | X does not prohibit AI-written posts |
| Rate limit compliance | ✅ | Spec includes rate limit tracking and auto-pause |
| Credential security | ✅ | `chmod 600`, single protected file |
| No AI model training from X data | ✅ | We use Claude as-is, no fine-tuning |
| Not creating substitute X service | ✅ | We post to X, not replace it |
| No content redistribution | ✅ | Scout data is internal-only |
| No pay-to-engage | ✅ | No compensation for engagement |
| Content compliance (deletion/updates) | ✅ | We don't cache or redistribute others' X Content publicly |

---

## Implementation Review Schedule

| Phase | Issues to Review |
|---|---|
| Phase 0 | ISSUE 7 (use case description), ISSUE 5 (bot labeling) |
| Phase 2 | ISSUE 6 (cross-account content uniqueness) |
| Phase 3 | ISSUE 1 (likes), ISSUE 2 (follows), ISSUE 3 (replies) |
| Phase 4 | ISSUE 4 (Playwright scraping) |

---

---

## Cross-References

**Referenced by**: [Technical Specification v2.4](./x-ai-beauty-spec-v2.3.md) (Sections 2.3, 2.5, 3.4), [PRD v1.1](./x-ai-beauty-prd-v1.md) (Sections 5.1, 13.3), [Phase 0 Runbook](../phase-0-runbook.md) (Steps 3, 7)

---

*This document is a living reference. Update issue status as decisions are made during implementation.*
