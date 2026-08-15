# -*- coding: utf-8 -*-
"""One command every document skill drives the toolchain through (M13-02).

Each generator has the same three-part shape: open a gate over what is already
known, answer whatever the gate still asks, then write. In a Python session that
is three calls on one `Gate` object. A skill is not a Python session — it is an
agent taking turns, and an agent cannot hold an object between them. Something
has to carry the brief and the answers to disk, or every skill invents its own
way of doing it.

So the cycle is stateless and identical for all seven document steps:

    python3 -m z2s.author run vision --root .
        exit 3 → a fork is open; the question is printed
    python3 -m z2s.author answer vision scope "..." --why "..."
    python3 -m z2s.author run vision --root .
        exit 0 → the document is written

Exit status is the answer, as it is everywhere else in this toolchain:

    0  the document was written
    1  refused — a missing prerequisite, an incomplete brief, an unresolved gap
    2  the command was used wrongly
    3  the gate is open; the printed question is the next thing to answer

The brief and the answer store both live under the run-state directory, which
the published repository layout already declares as transient and already keeps
out of version control. That is deliberate rather than convenient: a finished
document carries its own specification (FR-DOC-06), so the brief is the material
an interview was built from, not a second source of truth to keep in step with
it. Stated ceiling: a fresh clone has the documents and not the briefs, so an
operator who wants to re-derive a document from scratch re-interviews rather
than re-runs. Updating one goes through /zero:update, forward-only, which is the
supported path anyway.

Traces: FR-SKL-01, FR-SKL-02, FR-DOC-02, FR-DOC-03, FR-DOC-07, NFR-SKL-02,
NFR-SKL-04, ADR-18, US-SKL-01, US-SKL-02.
"""

import json
import os
import sys

from z2s import chain, gate, paths, steps, writer

#: Where an interview's raw material and its answers wait between turns. Both
#: sit under the ledger directory, which the layout already calls run state.
BRIEFS_DIR = paths.LEDGER_DIR + "/briefs"
ANSWERS_DIR = paths.LEDGER_DIR + "/answers"

WRITTEN, REFUSED, MISUSED, ASKING = 0, 1, 2, 3

USAGE = """\
usage: python3 -m z2s.author run <step> [--root DIR]
       python3 -m z2s.author answer <step> <fork> <choice> --why REASON [--root DIR]

steps: %s""" % ", ".join(one.module.SLUG for one in steps.DOCUMENTS)


def brief_path(root, slug):
    return paths.resolve(root, BRIEFS_DIR, "%s.json" % slug)


def answers_path(root, slug):
    return paths.resolve(root, ANSWERS_DIR, "%s.json" % slug)


def _read(path, default):
    """Whatever is stored at `path`, or `default` when there is nothing usable.

    A damaged answer store is treated as no answers rather than as a crash: the
    file is transient run state, and the recovery — being asked again — costs
    one interview round and loses nothing that was written.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            found = json.loads(handle.read())
    except (OSError, ValueError):
        return default
    # A brief and an answer store are both objects. Anything else — a list, a
    # bare string, `null` — is a file somebody meant for something else, and
    # reading it as either would produce a worse error further downstream.
    return found if isinstance(found, dict) else default


def _write(path, payload):
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    writer.write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def read_brief(root, slug):
    """The brief for one step, or None when the operator has not written one."""
    return _read(brief_path(root, slug), None)


def record(root, slug, fork, choice, why):
    """Store one answer for a later run to apply. Returns the file written.

    Answers accumulate rather than replace: an interview happens over several
    turns, and a round that forgot the previous round's answers would ask the
    same question until the operator gave up.
    """
    target = answers_path(root, slug)
    stored = _read(target, {})
    stored[fork] = {"choice": choice, "why": why}
    return _write(target, stored)


def apply(run, stored):
    """Put every stored answer to the gate, in the gate's own order.

    A fork the ledger has already locked is left alone unless the stored answer
    contradicts it — `gate.answer` raises then, and that refusal is the point: a
    locked decision is applied, never quietly re-decided (FR-DOC-03).
    """
    applied = []
    for one in run.forks:
        answer = stored.get(one.id)
        if answer is None:
            continue
        run.answer(one.id, answer.get("choice", ""), answer.get("why", ""))
        applied.append(one.id)
    return tuple(applied)


def question(one):
    """The next fork, written for whoever has to answer it.

    Printed as prose rather than as data because the reader is an interview:
    every option carries its meaning, and the recommendation is marked, so the
    operator is choosing between described outcomes rather than identifiers.
    """
    lines = ["The gate is open. Answer this before anything is written.",
             "",
             "fork: %s" % one.id,
             "question: %s" % one.question,
             "",
             "options:"]
    for option in one.options:
        marked = "  %s — %s" % (option.id, option.label)
        if option.recommended:
            marked += "  (recommended)"
        lines.append(marked)
        if option.meaning:
            lines.append("      %s" % option.meaning)
    lines.append("")
    lines.append("An answer outside these options is allowed and is kept "
                 "verbatim. Every answer needs a reason.")
    return "\n".join(lines)


def drive(root, name, out):
    """One turn of the cycle for one step. Returns the exit status.

    Order is the whole contract: prerequisites, then brief, then gate, then
    write. Every refusal happens before `author` is reached, so a run that
    refuses has created nothing and changed nothing (NFR-SKL-02).
    """
    try:
        one = steps.step(name)
    except steps.UnknownStep as error:
        out.write("%s\n" % error)
        return MISUSED

    if one.module is None:
        out.write("%s writes no document, so there is nothing to author. It is "
                  "an operating skill.\n" % one.name)
        return MISUSED

    refused = steps.refusal(root, one)
    if refused is not None:
        out.write("%s\n" % refused)
        return REFUSED

    slug = one.module.SLUG
    brief = read_brief(root, slug)
    if brief is None:
        out.write("no brief for %s at %s. Interview the operator through "
                  "/zero:questions and write the brief there first. Nothing has "
                  "been written.\n" % (slug, brief_path(root, slug)))
        return REFUSED

    try:
        run = one.module.open_gate(brief, root)
        apply(run, _read(answers_path(root, slug), {}))
    except (gate.LockedForkConflict, ValueError) as error:
        out.write("%s\n" % error)
        return REFUSED

    still_open = run.question()
    if still_open is not None:
        out.write(question(still_open) + "\n")
        return ASKING

    try:
        written = one.module.author(root, brief, run)
    except (chain.MissingPrerequisite, chain.IncompleteBrief,
            gate.GateNotClosed) as error:
        out.write("%s\n" % error)
        return REFUSED
    except Exception as error:                    # the generators' own refusals
        # Every generator raises its own named refusal — a plan that leaves a
        # requirement uncovered, a graph with a cycle, a brief that names an
        # area it never declared. Their types differ by design (they are fixed
        # differently), so they are reported by what they say rather than
        # rounded up into one and made anonymous.
        out.write("%s: %s\n" % (type(error).__name__, error))
        return REFUSED

    for path in (written if isinstance(written, (list, tuple)) else [written]):
        if isinstance(path, str):
            out.write("wrote %s\n" % path)
    return WRITTEN


def _option(argv, flag, out):
    """The value after `flag`, or None. Removes both from `argv` in place."""
    if flag not in argv:
        return None
    at = argv.index(flag)
    if at + 1 >= len(argv):
        out.write("%s needs a value\n" % flag)
        return ""
    value = argv[at + 1]
    del argv[at:at + 2]
    return value


def main(argv, out=sys.stdout):
    """The command. Its exit status is the answer (FR-VAL-05)."""
    argv = list(argv)
    root = _option(argv, "--root", out)
    if root == "":
        return MISUSED
    why = _option(argv, "--why", out)
    if why == "":
        return MISUSED
    root = root or "."

    if len(argv) >= 2 and argv[0] == "run":
        return drive(root, argv[1], out)

    if len(argv) == 4 and argv[0] == "answer":
        _, name, fork, choice = argv
        try:
            one = steps.step(name)
        except steps.UnknownStep as error:
            out.write("%s\n" % error)
            return MISUSED
        if not why or not why.strip():
            out.write("an answer needs --why. A choice without a reason is not "
                      "a decision, and the ledger records both.\n")
            return MISUSED
        target = record(root, one.module.SLUG, fork, choice, why.strip())
        out.write("recorded %s = %s in %s\n" % (fork, choice, target))
        return WRITTEN

    out.write(USAGE + "\n")
    return MISUSED


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
