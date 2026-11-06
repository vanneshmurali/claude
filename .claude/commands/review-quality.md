---
description: Review the code quality of a file and record each issue with its severity in a Markdown report (read-only, never edits the file)
argument-hint: <file-path>
allowed-tools: Read, Grep, Glob, Write(reviews/**)
---

Review the code quality of this file: `$ARGUMENTS`

## Hard rules

- **Do not modify the file under review**, or any other source file. Do not use Edit, and do not use
  Write on any path outside `reviews/`. Do not run commands that change files (formatters, `sed -i`, git).
- The only file you may create or overwrite is the report described below.
- If `$ARGUMENTS` is empty or the file does not exist, say so and stop. Do not write a report.

## What to review

Read the whole file. Read `CLAUDE.md`, `docs/coding-conventions.md` and `docs/testing.md`, and judge the
file against them as well as against general good practice. Look at:

| Area            | Examples                                                                      |
|-----------------|-------------------------------------------------------------------------------|
| Correctness     | Logic errors, unhandled `None`/missing form keys, wrong status codes          |
| Security        | Missing auth/role checks, string-built SQL, user input via `\| safe` or `body`, POST forms without the CSRF field, secrets or plaintext passwords |
| Resource use    | DB connections not closed, missing `commit()`                                 |
| Conventions     | Violations of the project rules in `docs/coding-conventions.md`               |
| Maintainability | Duplication, overly long functions, unclear names, dead code                  |
| Testability     | Behaviour with no matching test, per `docs/testing.md`                        |

Report only real issues you can point to in the code. Do not pad the list, and do not report the same
problem twice.

## Severity

| Severity | Meaning                                                                    |
|----------|----------------------------------------------------------------------------|
| Critical | Security hole or data loss/corruption; fix before anything ships           |
| High     | Incorrect behaviour or a hard-rule violation from `CLAUDE.md`              |
| Medium   | Convention violation or a bug that needs unusual input to trigger          |
| Low      | Style, naming, readability, minor cleanup                                  |

## Output

Write the report to `reviews/<file name>-review.md` (e.g. `app.py` → `reviews/app.py-review.md`),
overwriting any earlier report for the same file. Use this layout:

```markdown
# Code Quality Review: <file path>

Reviewed: <YYYY-MM-DD>

## Summary

| Severity | Count |
|----------|-------|
| Critical | n     |
| High     | n     |
| Medium   | n     |
| Low      | n     |

<one or two sentences on overall quality>

## Issues

| # | Severity | Line(s) | Category | Issue | Suggested fix |
|---|----------|---------|----------|-------|---------------|
| 1 | High     | 42-45   | Security | ...   | ...           |
```

Sort issues by severity (Critical first), then by line number. If there are no issues, keep the summary
table with zero counts and write "No issues found." under Issues.

When done, reply with the report path and the count per severity. Do not paste the full report.
