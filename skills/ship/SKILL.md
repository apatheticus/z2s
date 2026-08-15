---
name: ship
description: Commits everything on the current working branch, pushes it, and then asks whether to open a pull request. Never opens one without an explicit yes. Use when the operator says to ship, push or commit the branch. Invoke deliberately; never run unasked.
disable-model-invocation: true
argument-hint: [the commit subject]
---

# /zero:ship

Commits and pushes the working branch. Stops at the pull request and asks.

Read `${CLAUDE_PLUGIN_ROOT}/reference/chain-rules.md` before acting.

**Requires:** a git repository on a branch, with a remote.

## Do this

**1. Look before committing.** Read the working tree and the staged diff, and
say what is about to go in. If anything looks like a credential, a private key,
an environment file or content that should not leave the machine, **stop and
report it** — do not commit it and do not ask whether to.

**2. Write a real commit subject.** What changed and why, not "update files". If
the operator gave one, use theirs.

**3. Commit and push.**

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.ship --message "<subject>" --root .
```

It commits everything on the branch, pushes it with upstream set, and prints the
pull-request offer. A clean tree is not an error — a branch that is already
committed and merely unpushed is the common case, and it says so and pushes.

**4. Put the offer to the operator.** Do not answer it for them. It is a
question about telling other people, and that is theirs to decide.

**5. Only on an explicit yes:**

```
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m z2s.ship pull-request --title "<title>" --body "<body>" --yes --root .
```

The `--yes` is what carries their consent. Never supply it because the run
seemed to be heading that way, because a previous run had one, or because the
operator said something that could be read as approval. They have to say yes to
this.

## What is refused, and stays refused

Force-pushing, rewriting history, and deleting an unmerged branch are refused by
the toolchain before any of them runs. If you see a refusal, report it as it
stands. Do not reshape the command to get past it, and do not run the raw git
equivalent yourself — the refusal is the answer, not an obstacle.

## Never

- Never open a pull request without `--yes` from the operator in this conversation.
- Never merge anything. This skill ships a branch; merging is a separate decision
  nobody asked you to make.
- Never commit something you flagged as sensitive, whatever reassurance follows.
