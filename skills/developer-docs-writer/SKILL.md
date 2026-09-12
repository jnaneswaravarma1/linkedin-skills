---
skill: developer-docs-writer
version: 1.0.0
trigger:
  - "write docs"
  - "write documentation"
  - "document this code"
  - "write a README"
  - "add comments to this code"
  - "write docstrings"
not_for: PR writer (use developer-pr-writer)
---

# Developer Docs Writer

## What this skill does
Writes clear useful documentation that
developers actually read and understand.
Shows draft first — waits for approval.

---

## Step 1 — What to document
Ask: "What do you want documented?
1. Function or class
2. API endpoint
3. Full README
4. Inline code comments"

Wait for answer.

---

## If option 1 — Function or class

Ask: "Paste the function or class."

Write docstring in this format:

def function_name(param1, param2):
"""
One line summary.

Args:
    param1 (type): Description.
    param2 (type): Description.

Returns:
    type: What this returns.

Raises:
    ErrorType: When raised.

Example:
    result = function_name("value", 42)
    # returns: expected output
"""

---

## If option 2 — API endpoint

Ask: "Paste the endpoint code or describe it."

Write in this format:

POST /api/endpoint

Description: What this does.

Request:
{
"field1": "string",
"field2": "integer"
}

Response:
{
"status": "success",
"data": {}
}

Errors:

400 — Bad request
401 — Unauthorized
500 — Server error

---

## If option 3 — README

Ask: "What is your project in one sentence?"

Write in this format:
Project Name

One line description.

What this is

[2-3 sentences]

Getting started

git clone [repo]
cd [project]
npm install
npm start

How to use

[simple example]

Built with
[tech 1]
[tech 2]


---

## If option 4 — Inline comments

Ask: "Paste the code to comment."

Rules for comments:
- Explain WHY not WHAT
- Only comment complex logic
- Under 10 words per comment
- Never state the obvious

---

## Rules
- Always ask which type first
- Match the language of the code
- Never over-document simple code
- Show draft first — wait for approval