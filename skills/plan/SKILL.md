---
name: plan
description: Derives the plan and proves coverage. Invoke deliberately; never run unasked.
disable-model-invocation: true
argument-hint: [milestones, ordering or delivery constraints]
---

# /zero:plan

Derives the plan and proves coverage.

Read `${CLAUDE_PLUGIN_ROOT}/reference/chain-rules.md` before acting. It carries
the four rules every skill in this chain follows, and the meaning of each exit
status below.

**Requires:** a completed Context.html and FSD.html and Stories.html and SDD.html. The command below checks and refuses by name.

## Do this

**1. Set the project up.** Idempotent, so run it every time without checking.

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.project --root .
```

**2. Write the brief.** The brief is this document's raw material. Its shape is
documented in one place — the module docstring and the section table in
`${CLAUDE_PLUGIN_ROOT}/z2s/plan.py`. Read that, not a copy of it, because a
copy is what goes stale.

Build the brief from what the operator gave you: `$ARGUMENTS`, the conversation,
any files or addresses they named. Where the brief would need a fact nobody has
stated, leave it out — the generator records a silence as an open question, and
that is more useful than an invented answer. Then write it to:

```
.zero/state/briefs/plan.json
```

Each task's `writes` list has to be COMPLETE and NARROW, and only completeness
is checked. A path left out means two workers editing one file; a directory
glob nobody needed means the whole plan runs one unit at a time whatever the
ceiling says. Name the files a task will really write wherever they can be
named, and keep a glob for where they genuinely cannot.

**3. Run the cycle.**

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.author run plan --root .
```

- **exit 1** — refused. Report the message verbatim and stop. Do not generate the
  missing document unasked.
- **exit 3** — a fork is open. Put the printed question to the operator through
  `/zero:questions`, record their answer with `python3 -m z2s.author answer
  plan <fork> <choice> --why "<their reason>" --root .`, then run again.
- **exit 0** — written. Go to step 4.

**4. See what the plan costs in concurrency.** Read-only, writes nothing,
never refuses:

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.forecast --root .
```

It reports the rounds this plan can be dispatched in and the paths most of it is
claiming. A mean near 1.0 means the plan runs serially however high the ceiling
is set, and the path at the top of its list is why. Some plans really are serial;
this is a preview, not a gate. But hand a plan to `/zero:build` knowing the
number, not after the build has spent it.

**5. Report.** Name the file written and the decisions the gate recorded. If the
document carries open questions, list them: they are what the next step needs
answered, and a report that hides them makes the next step guess.

## Never

- Never answer a fork yourself. The gate exists because these are the operator's
  decisions.
- Never write or edit the rendered document. Write the brief; the generator
  writes the document.
- Never continue past a refusal.

## Running it again

Running the plan again over documents a build has already recorded status in
keeps every status and every ticked criterion those documents hold; only what
the brief and the detail files changed — write lists, text, new tasks —
changes. So a wrong write list can be corrected and the plan regenerated
without the run losing its place. (A running build does not need even that:
add the path to `overlay` in the run ledger, or a family in `workers.json`.)
