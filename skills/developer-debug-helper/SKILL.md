---
skill: developer-debug-helper
version: 1.0.0
trigger:
  - "help me debug"
  - "I have a bug"
  - "this is not working"
  - "why is this failing"
  - "fix this error"
  - "I'm getting an error"
not_for: code review (use developer-code-reviewer)
---

# Developer Debug Helper

## What this skill does
Debugs like a senior developer.
Finds root cause fast. No guessing.
Explains why — not just what to fix.

---

## Step 1 — Get the error
Ask: "Paste the error message or describe
what's happening vs what you expected."

Wait for answer.

---

## Step 2 — Get the code
Ask: "Now paste the relevant code
where you think the bug is."

Wait for answer.

---

## Step 3 — Quick context
Ask all at once:
"Three quick questions:
1. What language and framework?
2. When did this start happening?
3. What did you change last before this broke?"

Wait for answer.

---

## Step 4 — Diagnose

Check for these common causes:
- Wrong data type
- Null or undefined value
- Wrong variable scope
- Missing import or dependency
- Async/await issue
- Off by one error
- Environment variable missing
- Wrong API endpoint or payload
- Race condition
- Circular dependency

---

## Step 5 — Output format

Print exactly this:
DEBUG REPORT — [Date]

ERROR TYPE: [type of error]
ROOT CAUSE: [one sentence]
LOCATION: [file/line number if visible]

FIX:
[exact code fix]

WHY THIS HAPPENED:
[one paragraph explanation]

PREVENT NEXT TIME:
[one tip to avoid this class of bug]


---

## Rules
- Never guess — if unsure ask one more question
- Always explain WHY not just what to fix
- Give exact fix — not "try changing this"
- If multiple bugs found — fix most critical first
- Show report — wait for their response