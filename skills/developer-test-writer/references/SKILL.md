---
skill: developer-test-writer
version: 1.0.0
trigger:
  - "write tests"
  - "write unit tests"
  - "add tests"
  - "test this code"
  - "write test cases"
  - "help me test this"
not_for: debug helper (use developer-debug-helper)
---

# Developer Test Writer

## What this skill does
Writes comprehensive tests that catch real bugs.
No shallow happy-path-only tests.
Shows draft first — waits for approval.

---

## Step 1 — Get the code
Ask: "Paste the function or module
you want tested."

Wait for answer.

---

## Step 2 — Get context
Ask: "Two quick questions:
1. What testing framework?
   (Jest, Pytest, Mocha, JUnit, etc.)
2. Any specific edge cases you're worried about?"

Wait for answer.

---

## Step 3 — Write tests

Cover all 5 categories — no exceptions:

### 1. Happy path
- Normal expected behavior
- Valid typical inputs
- Correct output returned

### 2. Edge cases
- Empty input
- Null or undefined
- Zero or negative numbers
- Very large inputs
- Special characters

### 3. Error handling
- Invalid input types
- Missing required parameters
- Out of range values
- Correct errors thrown

### 4. Boundary tests
- Minimum valid input
- Maximum valid input
- Just below minimum
- Just above maximum

### 5. Integration tests
- Real dependencies
- Mocked API calls
- Database operations

---

## Step 4 — Output format

Write tests in their framework.
Add comment above each group:

Happy path tests

def test_normal_case():
...

Edge case tests

def test_empty_input():
...

Error handling tests

def test_invalid_input():
...


Print this summary after tests:
TEST SUMMARY

TOTAL TESTS: [number]
COVERAGE:

Happy path: [number]
Edge cases: [number]
Error handling: [number]
Boundary: [number]

ALSO CONSIDER:

[additional edge case not covered]

---

## Rules
- Never write only happy path tests
- Always mock external dependencies
- Test one thing per test function
- Test names must describe what they test
- If framework unknown — ask before writing
- Show tests — wait for approval
