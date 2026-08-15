# Chain rules

Read this before acting on any `/zero:*` skill. Every skill in the chain follows
these rules; they are stated here once so that fourteen definitions cannot drift
apart from each other.

## Where things are

| Thing | Where |
|---|---|
| The toolchain | `${CLAUDE_PLUGIN_ROOT}` — run it as `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.<module>` |
| The project | the current working directory — always pass `--root .` |
| Specifications | `.zero/specs/` |
| The plan | `.zero/plan/` |
| Run state | `.zero/state/` — briefs, answers, ledger. Not in version control. |
| Worker settings | `.zero/workers.json` |

`PYTHONPATH` cannot be set once and reused: each command runs in its own shell.
Put it on every invocation.

## The four rules

**1. Setup happens by itself.** Never ask the operator to run a shell command —
not to make a directory, not to write an ignore rule, not to install anything.
If setup is missing, run it:

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.project --root .
```

It is idempotent. Running it on a project that is already set up changes no byte
and costs nothing, so run it at the head of every skill rather than working out
whether it is needed.

**2. Refuse rather than guess.** Every document skill checks its upstream
document before doing anything. When the check refuses, report the refusal
**verbatim** and stop. Do not generate the missing document unasked, do not
proceed with a partial set, and do not paraphrase the refusal — it names the
file and the command that fixes it, and that naming is the whole value.

**3. Questions go through one interview.** When a command exits 3, it has
printed one fork with its options and a recommendation. Put it to the operator
through the `/zero:questions` skill — numbered, one round at a time, each option
with its meaning and the recommendation marked. Never answer a fork on the
operator's behalf, and never invent an option that was not offered. An answer
outside the offered options is allowed and is kept word for word.

Record each answer, then run the command again:

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.author answer <step> <fork> <choice> --why "<the operator's reason>" --root .
```

The reason is required. A choice without one is not a decision, and the ledger
records both.

**4. Report what happened, not what was supposed to happen.** Say which command
you ran and what it returned. A step that was skipped is reported as skipped. A
check that did not run is never reported as passed.

## What the exit status means

| Status | Meaning | What to do |
|---|---|---|
| 0 | Done. The document was written. | Report the paths. |
| 1 | Refused. | Report the message verbatim. Stop. |
| 2 | The command was used wrongly. | Fix the invocation. This is your mistake, not the operator's. |
| 3 | A fork is open. | Interview, record the answer, run again. |

## Never

- Never edit a generated document under `.zero/specs/` or `.zero/plan/` by hand.
  A document carries its own specification; edit that and re-render, or use
  `/zero:update`. A hand edit is silently overwritten on the next run.
- Never delete or overwrite published content. Updates are forward-only:
  amend with a date, append, or retire with a successor pointer.
- Never trigger automatically. Every skill here runs because the operator asked
  for it. `/zero:questions` is the single exception, and it only ever asks — it
  never writes a document.
- Never run a git command that rewrites history, force-pushes, or deletes an
  unmerged branch. The toolchain refuses these; do not work around a refusal.
