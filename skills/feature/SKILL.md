---
name: feature
description: Opens the next feature, closes the current one after an audit, or reports which feature is open and what its audit finds. One feature is open at a time. Invoke deliberately; never run unasked.
disable-model-invocation: true
argument-hint: [open <slug> | close [reason] | status]
---

# /zero:feature

One feature at a time. A feature is a piece of work with its own
specifications, plan and run state under `.zero/features/NNN-slug/`, beside
the project's shared Intent, Context, workers and design record. Which
feature is open is never configured: it is the highest-numbered directory.

Read `${CLAUDE_PLUGIN_ROOT}/reference/chain-rules.md` before acting.

**Requires:** a completed shared Intent.html and Context.html to open a
feature; an open feature to close one. The commands below check and refuse by
name.

## There are exactly three things you can do

**Open** — start the next feature. Refuses while one is open.

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.feature open <slug> --root .
```

`<slug>` is lowercase words joined by dashes (`checkout-flow`). The command
prints the directory it created and the next command: `/zero:intent`, which
now writes the feature's own Intent. From there the chain runs as always —
`/zero:prd` … `/zero:plan`, `/zero:build` — and every document lands inside
the feature. The Context stays the project's; `/zero:context` still writes it
beside the project.

**Close** — finish the open feature. Audited: every unit of its plan passing,
every retired identifier succeeded, every open question answered, everything
it built committed.

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.feature close --date "$(date +%F)" --root .
```

A clean audit closes the feature as `complete`. Findings refuse the close and
are printed, one per line. To close it anyway — parked, superseded, out of
time — give the reason, and the findings are recorded beside it as what was
left rather than refused:

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.feature close "<why it is closing unfinished>" --date "$(date +%F)" --root .
```

The close is written into the feature's own Intent document. A closed feature
refuses generation and building; open the next one.

**Status** — read-only.

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.feature status --root .
```

Prints the open feature and its audit, or the close record and the next
command.

## Something small while a feature is open

Do not open a second feature. A hotfix or a small addition goes into the open
feature by addendum through the document's own skill, which assigns a fresh
identifier and disturbs nothing.

## The date

Required on `close`, and you have to know it. The toolchain has no clock by
design. The shell supplies it above; if that is unavailable, ask the operator
through `/zero:questions` — do not guess one.

## Never

- Never create or rename a directory under `.zero/features/` by hand.
- Never edit a rendered document to mark a feature closed; the command writes
  the record.
- Never close over findings without a reason the operator gave.
