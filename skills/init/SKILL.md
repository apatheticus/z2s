---
name: init
description: Sets a project up for the method — the .zero/ layout, ignore rules, design-token detection and the verification gauntlet. Idempotent. Every other chain skill runs it automatically when it finds setup missing, so invoking it by hand is optional. Invoke deliberately; never run unasked.
disable-model-invocation: true
argument-hint: [nothing]
---

# /zero:init

Performs every setup mechanic the method needs, so that no step of the method
ever asks the operator to type a shell command.

Read `${CLAUDE_PLUGIN_ROOT}/reference/chain-rules.md` before acting.

**Requires:** nothing. It works in a bare repository.

## Do this

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.project --root .
```

That is the whole skill. It creates the `.zero/` layout, writes the ignore rules,
detects the project's design system, and records a starting verification
gauntlet. Then report exactly what it printed:

- Every line marked `created` is something that was not there before.
- Every line marked `present` was already there and was **left untouched** — an
  existing ignore file may carry the project's own rules and an existing worker
  record may carry its real commands, so neither is ever overwritten.
- The design-token line names the stylesheet the theme was adopted from, or says
  plainly that none was found and the neutral theme was used.
- Any `outstanding` line is work the operator still has to decide. Do not
  paper over it and do not fill it in yourself.

With a feature open (`.zero/features/NNN-slug/`), the specifications, plan and
state directories are created inside that feature; the shared layout beside
the project is left as it is. `/zero:feature open` runs this for you.

## It is safe to run twice

A second run changes no byte. That is deliberate: it is what lets every other
skill call this one whenever it finds setup missing, without anybody having to
track whether it has already happened. Do not check first — just run it.

## What it does not do

It does not invent the project's verification commands. The gauntlet it writes
is the method's own document check, which is true of every project. The worker
list is left empty on purpose, so `/zero:build` refuses and names what is
missing rather than dispatching work to a command nobody chose.

If the operator wants real workers configured, interview them through
`/zero:questions` and write `.zero/workers.json` yourself. Never ask them to
edit it by hand.
