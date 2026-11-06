---
description: Build one roadmap phase with agents (phase-coder, then quality-verifier, then bug-fixer)
argument-hint: <phase-number>
---

Build phase `$ARGUMENTS` of `docs/PLAN.md` by running three agents in order. Pass each agent's output to
the next. Don't do their work yourself.

If `$ARGUMENTS` is not a phase number that exists in `docs/PLAN.md`, say so and stop.

## Step 1 - Code the phase

Start the `phase-coder` agent with: "Implement phase $ARGUMENTS of docs/PLAN.md."

- If it reports `RESULT: BLOCKED`, show the user the open questions with AskUserQuestion. Then start
  `phase-coder` again with the answers, telling it to finish only the blocked items.
- If tests are not all passing in its report, stop and tell the user. Don't run review on broken code.

## Step 2 - Verify quality

Start the `quality-verifier` agent with the phase number and the exact `FILES CHANGED` list from step 1.
It writes `reviews/phase-$ARGUMENTS-review.md`.

- If it found no issues, skip step 3.

## Step 3 - Fix issues

Start the `bug-fixer` agent with: "Fix the issues in reviews/phase-$ARGUMENTS-review.md one by one."

- If it reports `NEEDS DECISION` items, list them for the user at the end. Don't decide them yourself.

## Step 4 - Confirm

Run `py -m pytest -q` yourself, and read the final report file.

Then tell the user:
- what the phase added (from step 1);
- the issues found per severity, and how many were fixed, skipped, not bugs, or need a decision;
- the final test result;
- any open questions.

Link the report file.
