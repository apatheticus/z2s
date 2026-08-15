---
name: update
description: Folds an addition or change into an already-published document, forward only — amend with a date, or retire with a successor. Never deletes and never overwrites. Use when a requirement, decision or story needs changing after it has been published. Invoke deliberately; never run unasked.
disable-model-invocation: true
argument-hint: <identifier> and what changed about it
---

# /zero:update

Changes something already published, without removing what was there.

Read `${CLAUDE_PLUGIN_ROOT}/reference/chain-rules.md` before acting.

**Requires:** the document that defines the identifier.

## There are exactly two things you can do

**Amend** — the entry is still scope, and something about it changed. The
original text stays and a dated note goes below it, so a reader meets both.

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.update amend <ID> "<what changed and why>" --date <YYYY-MM-DD> --root .
```

**Retire** — the entry is no longer scope at all. It stays where it is, its
number stays reserved forever, and the document says plainly that it was
withdrawn and why.

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.update retire <ID> "<why it is no longer scope>" --successor <ID> --root .
```

`--successor` is optional and worth supplying whenever something replaces it —
a reader who built against the old entry needs somewhere to go next.

## The date

Required, and you have to know it. The toolchain has no clock by design, so
there is nothing to default it to. If you do not know today's date, ask the
operator through `/zero:questions` — do not guess one and do not reuse a date
you saw in another document.

## When the operator asks you to delete something

They will. Do not do it, and do not pretend the command is missing:

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.update delete <ID> --root .
```

refuses and prints the retirement they should run instead. Show them that, and
explain it in one sentence: a requirement somebody built against does not vanish;
it gets withdrawn, with a reason, and its number is never reused.

If they say the entry was a mistake that was never real — a typo, a duplicate
created minutes ago — that is still a retirement. The cost of a retired number
is one line nobody reads. The cost of a reused number is a reader following a
trace to the wrong requirement.

## Adding something new

This skill changes what exists. New scope is not an update — it goes in by
addendum through the document's own skill, which assigns a fresh identifier and
never disturbs an existing one.

## Never

- Never edit a rendered document by hand to make a change "quickly".
- Never remove, replace or rewrite published text.
- Never re-use a retired identifier.
