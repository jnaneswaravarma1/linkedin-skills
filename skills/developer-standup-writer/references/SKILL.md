---
skill: developer-standup-writer
version: 1.0.0
trigger:
  - "generate standup"
  - "write my standup"
  - "standup update"
  - "daily update"
  - "write standup for me"
not_for: daily checklist (use developer-daily-checklist)
---

# Developer Standup Writer

## What this skill does
Generates a clean professional standup update
in under 60 seconds.
Works for Slack, Teams, or email.

---

## Step 1 — Yesterday
Ask: "What did you work on yesterday?
List anything — even small things count."

Wait for answer.

---

## Step 2 — Today
Ask: "What are you working on today?"

Wait for answer.

---

## Step 3 — Blockers
Ask: "Any blockers or dependencies
on someone else?"

If YES → include in standup with action needed.
If NO → write "No blockers" in standup.

---

## Step 4 — Generate standup

Format exactly like this:
STANDUP — [Today's Date]

YESTERDAY:

[task 1]
[task 2]

TODAY:

[task 1]
[task 2]

BLOCKERS:

[blocker] — waiting on [person/team]
OR
None


---

## Step 5 — Format check
Ask: "Want this formatted for
Slack, Teams, or email?"

If Slack → add @mentions and emoji
If Teams → plain text format
If email → add subject line and sign off

---

## Rules
- Keep each bullet under 10 words
- Clear enough for non-technical manager
- Never add commentary after the standup
- One standup per session
- Show draft first — wait for approval