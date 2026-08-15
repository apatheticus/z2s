---
name: questions
description: The shared clarification interview. Use this whenever a decision would otherwise be guessed — when a requirement is ambiguous, when two readings of a request would produce different work, when a fork in any /zero:* command needs the operator's answer, or when you are about to pick a default the operator never stated. Ask rather than assume.
argument-hint: [what needs deciding]
---

# /zero:questions

The one place every skill asks the operator anything. It only ever asks — it
never writes a document, never runs a generator, and never changes a file.

Read `${CLAUDE_PLUGIN_ROOT}/reference/chain-rules.md` before acting.

## Why this skill may fire on its own

Every other skill in this chain is manual-only and carries
`disable-model-invocation: true`. This one deliberately does not. A question
that arrives too late has already been answered by a guess, so this is the one
skill that must be able to interrupt.

**Fire when:** a decision is about to be made that the operator never stated;
two readings of the request would produce materially different work; a `/zero:*`
command exited 3 with an open fork; a default is about to be taken on a
user-visible choice.

**Do not fire when:** the answer is in the conversation already, in the
documents already, or is a routine judgement a careful colleague would just
make. Interviewing about things nobody cares about is how an interview stops
being read.

## How to ask

**One round at a time.** Gather every question you currently have, ask them as
one numbered round, wait for the answers, and only then start another round.
Questions dribbled out one per turn are the mid-build interruption this skill
exists to prevent.

**Every question carries:**

1. A number.
2. The question itself, ending in a question mark, asking for exactly one
   decision.
3. Its options, each with what it actually means for the operator — not the
   identifier, the outcome.
4. Exactly one marked **(recommended)**, with one line on why.

**Plain words.** No module names, no jargon, no describing how something works
unless asked. Say what changes for the operator. If a sentence needs a term they
would have to look up, rewrite the sentence.

**Show the shape first.** If a question rests on a structure the operator has
not agreed to — how the documents relate, where something lives, what depends on
what — draw that structure and confirm it before asking about it. A question
asked on top of an unagreed model gets rejected wholesale.

## When the question came from a command

A `/zero:*` command that exits 3 prints one fork: its identifier, the question,
and every option with its meaning and the recommendation marked. Put it to the
operator exactly as printed — do not re-word the options and do not add or
remove any. An answer outside the offered options is allowed and is kept word
for word.

Then record it, and hand back to the skill that asked:

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.author answer <step> <fork> <choice> --why "<the operator's reason>" --root .
```

The reason is the operator's, in their words. Never supply one on their behalf —
the ledger records both the choice and the why, and an invented reason is a
decision nobody made.

## Never

- Never answer for the operator, and never treat silence as agreement.
- Never invent an option that was not offered.
- Never write, generate or change anything. This skill asks; other skills act.
