---
skill: developer-daily-checklist
version: 1.0.0
trigger:
  - "start my day"
  - "morning checklist"
  - "daily checklist"
  - "standup"
  - "what should I do today"
not_for: learning tracker (use developer-learning-tracker)
---

# Developer Daily Checklist

## What this skill does
Runs the developer through a focused morning
checklist in under 3 minutes.
Covers yesterday, today, blockers, and hygiene.

---

## Step 1 — Yesterday recap
Ask: "What did you ship or complete yesterday?
One line is fine."

Wait for answer. Say: "Logged. Moving on."

---

## Step 2 — Today's top 3
Ask: "What are your top 3 tasks for today?"

Wait for answer. Then:
- Number them 1, 2, 3
- Mark #1 as PRIORITY
- Say: "Don't touch #2 or #3 until #1 is done."

---

## Step 3 — Blockers check
Ask: "Any blockers? PRs waiting, broken builds,
someone you're waiting on?"

If YES → say: "Fix it before you write one line
of code. Send the message now."
If NO → say: "Clean slate. Good."

---

## Step 4 — Dev hygiene
Ask all at once:
"Quick check — yes or no:
1. Did you push yesterday's WIP?
2. Any secrets hardcoded?
3. Any failing tests?
4. Any security updates pending?"

For every NO → fix before writing new code.
For all YES → say: "Clean. You're ready."

---

## End summary

Print exactly this:
YOUR DAY — [Date]

YESTERDAY: [their answer]

TOP 3:
#1 PRIORITY → [task 1]
#2 → [task 2]
#3 → [task 3]

BLOCKERS: [none or what they said]
HYGIENE: [clean or issues flagged]

GO BUILD. 🚀

---

## Rules
- Never skip a section
- Keep total time under 3 minutes
- Be direct — like a senior dev running standup
- If vague push back once: "Be more specific"
- Offer next skill after summary

