# Procedure: Add / Remove Competitor Account

**Applies to**: Anyone adding competitors — operator, Scout agent, or Strategist.
**Files touched**: `docs/competitor-accounts.md`, `config/competitors.json`

---

## Prerequisites

- Display name of the account
- X handle (with or without `@`)
- Market: `EN`, `JP`, or `both`
- (Optional) Notes — e.g. "AI VTuber", "China-based"

---

## Add a Competitor

### Step 1 — Check for Duplicates

Search `config/competitors.json` for the handle (case-insensitive). If it already exists, stop — the account is already tracked.

```bash
# Quick duplicate check (returns matching lines if found)
grep -i '"handle": "NewHandle"' config/competitors.json
```

### Step 2 — Update `docs/competitor-accounts.md`

Open `docs/competitor-accounts.md` and:

1. **Determine the correct table(s)**:
   - `EN` market → add a row to **EN Accounts**
   - `JP` market → add a row to **JP Accounts**
   - `both` → add a row to **both** EN and JP tables, **and** the **Overlap Accounts** table

2. **Add the row** at the end of the appropriate table(s). Increment the `#` column by 1 from the last entry.

   ```
   | 27 | New Display Name | @NewHandle | optional notes |
   ```

3. **Update the header counts**:
   - Update `**Total**:` — increment by 1 (or 2 if adding to both markets)
   - Update the per-market count in parentheses — e.g. `(26 EN + 17 JP)` → `(27 EN + 17 JP)`
   - If `both`: also increment **Unique handles** note and overlap count

### Step 3 — Update `config/competitors.json`

Add a new entry to the `competitors` array. Use this template:

```json
{
  "handle": "NewHandle",
  "user_id": "",
  "display_name": "Display Name",
  "category": "ai_beauty",
  "market": "EN",
  "priority": "medium",
  "notes": ""
}
```

**Field rules**:
| Field | Value |
|---|---|
| `handle` | Without `@`. Case-sensitive — match X exactly |
| `user_id` | Always `""` — Scout resolves on next run |
| `display_name` | As shown on their X profile |
| `category` | Always `"ai_beauty"` (for now) |
| `market` | `"EN"`, `"JP"`, or `"both"` |
| `priority` | Default `"medium"` — Strategist adjusts later |
| `notes` | Free text or `""` |

Also update the `last_updated` field at the top of the JSON to today's date (ISO 8601, e.g. `"2026-03-03"`).

> **Important**: For `"both"` market accounts, add only **one** JSON entry with `"market": "both"`. Do not create two separate entries.

### Step 4 — Validate

Run both checks to catch errors before committing:

```bash
# 1. Validate JSON syntax
python3 -c "import json; json.load(open('config/competitors.json')); print('JSON OK')"

# 2. Check for duplicate handles
python3 -c "
import json
data = json.load(open('config/competitors.json'))
handles = [c['handle'].lower() for c in data['competitors']]
dupes = [h for h in handles if handles.count(h) > 1]
print('No duplicates' if not dupes else f'DUPLICATES FOUND: {set(dupes)}')
"
```

Both commands should print success. If not, fix the issue before proceeding.

### Step 5 — Commit

```bash
git add docs/competitor-accounts.md config/competitors.json
git commit -m "Add competitor: @NewHandle (market)"
```

---

## Remove a Competitor

Use this when an account goes inactive, private, suspended, or is no longer relevant.

### Step 1 — Remove from `config/competitors.json`

Delete the entire JSON object for the account from the `competitors` array. Update `last_updated`.

### Step 2 — Remove from `docs/competitor-accounts.md`

1. Delete the row from the appropriate market table(s)
2. If the account was in the **Overlap Accounts** table, remove that row too
3. Re-number the `#` column in each affected table (no gaps)
4. Update the header counts (`Total`, per-market, unique handles)

### Step 3 — Validate & Commit

Run the same validation commands from the Add procedure, then:

```bash
git add docs/competitor-accounts.md config/competitors.json
git commit -m "Remove competitor: @OldHandle (reason)"
```

---

## Example Walkthrough — Adding a Fictional Account

**Scenario**: You found a new EN-market competitor called "Sakura Mist" with handle `@sakura_mist_ai`. She is a Flux-based AI model creator.

### 1. Check for duplicates

```bash
grep -i '"handle": "sakura_mist_ai"' config/competitors.json
# (no output — not a duplicate)
```

### 2. Update `docs/competitor-accounts.md`

Change the header:

```
**Total**: 44 entries (27 EN + 17 JP). 2 accounts appear in both markets (marked as overlap).
**Unique handles**: 42
```

Add row to the EN table:

```
| 27 | Sakura Mist | @sakura_mist_ai | Flux-based |
```

### 3. Update `config/competitors.json`

Add before the closing `]` of the `competitors` array:

```json
    {
      "handle": "sakura_mist_ai",
      "user_id": "",
      "display_name": "Sakura Mist",
      "category": "ai_beauty",
      "market": "EN",
      "priority": "medium",
      "notes": "Flux-based"
    }
```

Update `last_updated`:

```json
"last_updated": "2026-03-03",
```

### 4. Validate

```bash
python3 -c "import json; json.load(open('config/competitors.json')); print('JSON OK')"
# → JSON OK

python3 -c "
import json
data = json.load(open('config/competitors.json'))
handles = [c['handle'].lower() for c in data['competitors']]
dupes = [h for h in handles if handles.count(h) > 1]
print('No duplicates' if not dupes else f'DUPLICATES FOUND: {set(dupes)}')
"
# → No duplicates
```

### 5. Commit

```bash
git add docs/competitor-accounts.md config/competitors.json
git commit -m "Add competitor: @sakura_mist_ai (EN)"
```

---

## Quick-Reference Checklist

- [ ] Handle not already in `competitors.json`
- [ ] Row added to correct market table(s) in `competitor-accounts.md`
- [ ] Overlap table updated (if `both`)
- [ ] Header counts updated in `competitor-accounts.md`
- [ ] JSON entry added with all required fields
- [ ] `last_updated` date updated in JSON
- [ ] `python3` JSON validation passes
- [ ] `python3` duplicate check passes
- [ ] Both files committed together
