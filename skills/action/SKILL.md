---
name: action
description: Works out where the document chain stopped and continues from there — from the beginning when no vision exists. Use when returning to a project after a gap, or when the operator does not know what the next step is. Invoke deliberately; never run unasked.
disable-model-invocation: true
argument-hint: [nothing]
---

# /zero:action

Inspects the document set, reports where the chain reaches, and continues from
there.

Read `${CLAUDE_PLUGIN_ROOT}/reference/chain-rules.md` before acting.

**Requires:** nothing. An empty project is a valid answer — it means start at the
vision.

## Do this

**1. Set the project up.** Idempotent; run it without checking.

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.project --root .
```

**2. Find the position.** Read-only; it changes nothing.

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.steps --root .
```

It prints every document with `written` or `—`, the step the chain reaches, and
the one command to run next.

**3. Report the position before doing anything about it.** The operator has been
away. Tell them what is already written first, then what comes next. A skill
that jumps straight to acting leaves them unable to tell whether it understood
the project or guessed at it.

**4. Continue.** Invoke the skill the report names, and let that skill do its own
work — its own prerequisite check, its own interview, its own report. Do not
reimplement any of it here.

## Reading the position honestly

The walk stops at the **first gap**, not the last file that happens to exist. A
document left behind by an abandoned run, sitting downstream of a hole, does not
count as progress — and it will show as `written` in the list while the chain
still reaches only as far as the gap. Say so if that is what you see; it usually
means a run was interrupted and the operator will want to know.

A document that exists but carries no readable specification counts as **not
written**. It is a damaged file, and telling it apart from a finished one is the
single most useful thing this skill does.

## When everything is written

There is nothing left to generate. Say so, and point at `/zero:build`, which
works through the plan rather than adding to the specification set. Do not
regenerate a document that is already there — that is what `/zero:update` is
for, and it is forward-only.

## Never

- Never generate a document to fill a gap without the operator asking. Report
  the gap and name the skill.
- Never skip the report and go straight to acting.
