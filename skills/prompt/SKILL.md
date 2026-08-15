---
name: prompt
description: Prints the gauntlet-loop instructions for one unit of the plan — a task, a phase, a milestone, or the whole build — so they can be pasted into a fresh session or handed to somebody else. Reads what the plan document already carries; writes nothing and runs nothing. Requires a generated plan.
disable-model-invocation: true
argument-hint: [a unit identifier — M1, M1-P1, M1-P1-T1 — or "plan" for the whole build]
---

# /zero:prompt

Hands over one unit of work, at whatever size the operator asked for.

Read `${CLAUDE_PLUGIN_ROOT}/reference/chain-rules.md` before acting.

**Requires:** a generated plan in `.zero/plan/`. It refuses by name without one.

This skill is read-only. It prints; it does not build, does not dispatch, and
does not touch a status. `/zero:build` is the skill that runs work.

## Do this

**1. Set the project up.** Idempotent; run it without checking.

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.project --root .
```

**2. Print the instructions for the unit the operator named.**

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.gauntlet <unit> --root .
```

The identifier says its own level, so there is nothing else to pass:

| What they asked for | What to type |
|---|---|
| One task | `M1-P1-T1` |
| One phase | `M1-P1` |
| One milestone | `M1` |
| The whole build | `plan` |

**3. Give it to them whole.** The output is the deliverable. Print it exactly as
it came out, in one fenced block, with nothing before or after it. Do not
summarise it, do not trim it, and do not explain it back — an operator asked for
this because they are about to paste it somewhere else.

If they did not say which unit, the command with no argument lists what the plan
carries. Offer the levels and let them choose; do not pick for them.

## What the instructions already contain

Worth knowing so this skill does not helpfully repeat any of it:

- What the unit waits on, and the instruction to check that it is passing before
  starting.
- The plan document, the status contract, the locked decisions, the verification
  gauntlet and the report contract.
- The bar: the unit's own acceptance criteria, with their identifiers.
- The higher target the unit is aiming at, derived from what it traces to.
- The loop — split it, build each piece, have a **separate** critic in fresh
  context judge it, one gap on a loss, keep going.
- The critic's contract, ending with the injection guard.
- The hard stops that outrank the loop.

## Never

- Never write a prompt of your own. If a unit's instructions look wrong, the
  plan is wrong; fix the plan and regenerate it.
- Never edit what the command printed before handing it over. A prompt somebody
  improved on the way past is a prompt nobody can reproduce.
- Never run the work while printing the instructions for it. Those are two
  different requests, and the second one is `/zero:build`.
- Never invent a higher target for a unit that traces to nothing. The command
  says so plainly when there is none, and that sentence is the point.
