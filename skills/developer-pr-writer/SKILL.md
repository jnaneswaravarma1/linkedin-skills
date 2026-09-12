---
skill: developer-pr-writer
version: 1.0.0
trigger:
  - "write my PR"
  - "PR description"
  - "pull request"
  - "write PR description"
  - "help me write a PR"
not_for: code review (use developer-code-reviewer)
---

# Developer PR Writer

## What this skill does
Writes a clean professional pull request
description that reviewers actually read.
Shows draft first — waits for approval.

---

## Step 1 — What changed
Ask: "What did you change in this PR?
Plain English — no code yet."

Wait for answer.

---

## Step 2 — Why it changed
Ask: "Why was this change needed?
What problem does it solve?"

Wait for answer.

---

## Step 3 — How to test
Ask: "How can a reviewer test this?
What steps should they follow?"

Wait for answer.

---

## Step 4 — Any risks
Ask: "Any risks or side effects the
reviewer should know about?"

Wait for answer.

---

## Step 5 — Generate PR description

Print exactly this:

What changed

[clear summary in 2-3 sentences]

Why

[problem this solves]

Changes made
[change 1]
[change 2]
[change 3]
How to test
[step 1]
[step 2]
[expected result]
Risks / side effects
[risk 1]
OR
None identified
Screenshots

[Add if UI changes — delete if not applicable]

Checklist
 Code reviewed by me
 Tests added or updated
 No console.log left in code
 No hardcoded secrets
 Docs updated if needed

 
---

## Rules
- Keep language simple and clear
- Bullets over paragraphs
- Always include the checklist
- Show draft first — wait for approval
- Ask: "Want this shorter or more detailed?"