---
skill: developer-github-analyzer
version: 1.0.0
trigger:
  - "analyze my GitHub"
  - "check my GitHub activity"
  - "what did I build this week"
  - "GitHub summary"
  - "my coding activity"
not_for: daily checklist (use developer-daily-checklist)
---

# Developer GitHub Analyzer

## What this skill does
Analyzes developer GitHub activity and
gives a clear picture of productivity,
consistency, and growth areas.
Shows report — waits for response.

---

## Step 1 — Get GitHub info
Ask: "What is your GitHub username?
I will analyze your public activity."

Wait for answer.

---

## Step 2 — Time period
Ask: "What period do you want analyzed?
1. Today
2. This week
3. This month
4. Last 30 days"

Wait for answer.

---

## Step 3 — What to analyze
Ask: "What do you want to focus on?
1. Commit activity
2. PR activity
3. Code review activity
4. Overall summary"

Wait for answer.

---

## Step 4 — Ask for data
Since GitHub API needs a token ask:
"Paste your recent GitHub activity or
give me these details:
- Number of commits this period
- Repos you worked on
- PRs opened or merged
- Reviews done
- Any issues closed"

Wait for answer.

---

## Step 5 — Generate report

Print exactly this:
GITHUB REPORT — [Period]
Username: [their username]

ACTIVITY SUMMARY:

Commits: [number]
PRs opened: [number]
PRs merged: [number]
Code reviews: [number]
Issues closed: [number]

TOP REPOS THIS PERIOD:

[repo name] — [what they worked on]
[repo name] — [what they worked on]

CONSISTENCY SCORE: [1-10]
[one line explanation]

STRENGTHS:

[strength 1]
[strength 2]

AREAS TO IMPROVE:

[area 1]
[area 2]

RECOMMENDATION:
[one specific action to improve next period]

---

## Rules
- Never make up data — use only what they provide
- Always give a consistency score
- Always end with one recommendation
- Show report — wait for their response
- Ask: "Want me to compare this to last period?"