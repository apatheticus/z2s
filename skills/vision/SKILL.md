---
name: vision
description: Derives the vision from any mix of narrative, documents and web addresses; maintains the source register. Invoke deliberately; never run unasked.
disable-model-invocation: true
argument-hint: [notes, documents or web addresses to derive the vision from]
---

# /zero:vision

Derives the vision from any mix of narrative, documents and web addresses; maintains the source register.

Read `${CLAUDE_PLUGIN_ROOT}/reference/chain-rules.md` before acting. It carries
the four rules every skill in this chain follows, and the meaning of each exit
status below.

**Requires:** nothing. This is where the chain starts.

## Do this

**1. Set the project up.** Idempotent, so run it every time without checking.

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.project --root .
```

**2. Write the brief.** The brief is this document's raw material. Its shape is
documented in one place — the module docstring and the section table in
`${CLAUDE_PLUGIN_ROOT}/z2s/vision.py`. Read that, not a copy of it, because a
copy is what goes stale.

Build the brief from what the operator gave you: `$ARGUMENTS`, the conversation,
any files or addresses they named. Where the brief would need a fact nobody has
stated, leave it out — the generator records a silence as an open question, and
that is more useful than an invented answer. Then write it to:

```
.zero/state/briefs/vision.json
```

**3. Run the cycle.**

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.author run vision --root .
```

- **exit 1** — refused. Report the message verbatim and stop. Do not generate the
  missing document unasked.
- **exit 3** — a fork is open. Put the printed question to the operator through
  `/zero:questions`, record their answer with `python3 -m z2s.author answer
  vision <fork> <choice> --why "<their reason>" --root .`, then run again.
- **exit 0** — written. Go to step 4.

**4. Report.** Name the file written and the decisions the gate recorded. If the
document carries open questions, list them: they are what the next step needs
answered, and a report that hides them makes the next step guess.

## Never

- Never answer a fork yourself. The gate exists because these are the operator's
  decisions.
- Never write or edit the rendered document. Write the brief; the generator
  writes the document.
- Never continue past a refusal.
