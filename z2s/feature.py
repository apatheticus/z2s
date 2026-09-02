# -*- coding: utf-8 -*-
"""One feature at a time, and a close that is audited.

A feature is a piece of work with its own specifications, plan and run state
under `.zero/features/NNN-slug/`, beside the project's shared Intent, Context,
workers and design (FR-GEN-12). Which feature is open is DERIVED — the
highest-numbered directory — never configured and never stored, and there is
exactly one: opening another while one is open is refused (FR-GEN-13,
ADR-19). Something small that lands while a feature is open goes into it by
addendum, the door every generator already has.

Closing is audited (FR-GEN-14). The audit asks four questions of the feature —
is every unit of its plan passing, is every retired identifier succeeded, is
every question it raised answered, is everything it built shipped — and a
close with no reason has to answer all four cleanly, or it refuses and lists
what is open. A close WITH a reason records what the audit found as `left`
rather than refusing: parking a feature is a decision, and the record says
what was parked. Either way the close is written into the feature's own
Intent (`document.closed`) through the same writer every status change uses,
so a closed document is byte-identical to a regenerated one.

Nothing here parses a document: every read goes through `status.read`, which
is the shared extraction, and every write through `status.rewrite`.

    python3 -m z2s.feature open <slug> [--root DIR]
    python3 -m z2s.feature close ["<why it is being closed unfinished>"] --date YYYY-MM-DD [--root DIR]
    python3 -m z2s.feature status [--root DIR]

Traces: FR-GEN-12, FR-GEN-13, FR-GEN-14, FR-SKL-10, NFR-OPS-07, ADR-19,
US-GEN-04, US-GEN-05, US-GEN-06.
"""

import os
import re
import sys

from z2s import chain, context, execute, intent, paths, schema, ship, status, trace, update

#: What a feature may be called: the slug half of its directory name. The
#: grammar is the directory grammar (`paths.FEATURE_NAME`) with the number
#: taken off.
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

#: The reason recorded when a feature closes clean.
COMPLETE = "complete"

#: The section a generator files unanswered questions under (`chain.GAP_PHRASING`).
QUESTIONS = chain.GAP_PHRASING["question"][0]


class Refused(Exception):
    """Raised when an operation would open a second feature, close nothing, or
    close over findings without saying why."""


# ------------------------------------------------------------------ reading

def current(root):
    """(number, slug) of the current feature, or None."""
    found = paths.features(root)
    return found[-1] if found else None


def record(root):
    """The current feature's Intent as (path, html, spec), or None if unwritten."""
    if current(root) is None:
        return None
    path = paths.resolve(root, paths.SPECS_DIR, intent.FILENAME)
    try:
        html, spec = status.read(path)
    except status.Refused:
        return None
    return path, html, spec


def closed(root):
    """The closed record of the current feature, or None while it is open."""
    return chain.closed(root)


# ------------------------------------------------------------------ opening

def open(root, slug):
    """Open feature `slug` as the next number. Returns its directory, relative.

    Refuses while another feature is open, and refuses when the shared Intent
    or Context is missing — in the chain's own voice, because that is the
    document to generate first.
    """
    if not isinstance(slug, str) or not SLUG.match(slug):
        raise Refused("%r is not a feature name; use lowercase words joined by "
                      "dashes, like checkout-flow. Nothing was created." % (slug,))
    held = current(root)
    if held is not None and closed(root) is None:
        raise Refused(
            "%s is open; one feature is open at a time. Finish it and close it "
            "(`python3 -m z2s.feature close --date YYYY-MM-DD`), or add to it by "
            "addendum. Nothing was created." % paths.feature_dir(*held))
    chain.require(root, intent.FILENAME, intent.SLUG, "opening a feature", shared=True)
    chain.require(root, context.FILENAME, context.SLUG, "opening a feature", shared=True)

    number = held[0] + 1 if held else 1
    relative = paths.feature_dir(number, slug)
    os.makedirs(paths.shared(root, relative))
    paths.ensure_layout(root)
    return relative


# ------------------------------------------------------------------ the audit

def _finding(kind, identifier, text):
    return {"kind": kind, "id": identifier, "text": text}


def audit(root):
    """What stands between the current feature and a clean close.

    A list of findings, each naming what it is about; empty means clean. The
    four questions are asked in the order an operator would fix them.
    """
    found = []
    for path in status.documents(root):
        _, spec = status.read(path)
        for entry in status.tasks(spec):
            state = entry.get("status") or schema.NOT_STARTED
            if state != schema.PASSING:
                found.append(_finding("unit", entry["id"], "status is %s" % state))
    for path in paths.documents(root):
        _, spec = status.read(path)
        name = os.path.basename(path)
        for _, entry in schema.entries(spec):
            identifier = entry.get("id")
            if not isinstance(identifier, str) or trace.RETIRED not in entry:
                continue
            if schema.is_empty(entry.get(update.SUCCESSOR)):
                found.append(_finding("retired", identifier,
                                      "retired with no successor named"))
        for section in spec.get("sections") or ():
            if isinstance(section, dict) and section.get("id") == QUESTIONS:
                for item in section.get("items") or ():
                    found.append(_finding("question", name, item))
    ledger = execute.load(root)
    for unit, held in sorted((ledger.get("standing") or {}).items()):
        found.append(_finding("unshipped", unit,
                              "work rejected on the tree: %s"
                              % ", ".join(held.get("changes") or ())))
    for unit, held in sorted((ledger.get("strays") or {}).items()):
        found.append(_finding("unshipped", unit,
                              "wrote outside its declared set: %s" % ", ".join(held)))
    try:
        if ship.pending(root):
            found.append(_finding("unshipped", "working tree", "uncommitted changes"))
    except ship.Refused as error:
        found.append(_finding("unshipped", "working tree", str(error)))
    return found


def lines(findings):
    return ["%s %s: %s" % (one["kind"], one["id"], one["text"]) for one in findings]


# ------------------------------------------------------------------ closing

def close(root, reason, date):
    """Close the current feature. Returns the path written.

    The date is required and never read from a clock (NFR-GEN-01). With no
    reason the audit must be clean; with one, what the audit found is recorded
    beside it as `left`.
    """
    held = current(root)
    if held is None:
        raise Refused("no feature is open; nothing to close.")
    already = closed(root)
    if already is not None:
        raise Refused("%s is already closed (%s: %s)."
                      % (paths.feature_dir(*held), already.get("date"),
                         already.get("reason")))
    if schema.is_empty(date):
        raise Refused("a close states no date; nothing was written.")
    kept = record(root)
    if kept is None:
        raise Refused("%s has no Intent to record the close in; a feature that "
                      "wrote nothing has nothing to close. Nothing was written."
                      % paths.feature_dir(*held))
    findings = audit(root)
    if findings and schema.is_empty(reason):
        raise Refused(
            "%s is not finished, and no reason was given for closing it anyway:\n"
            "  - %s\nFinish these, or close with a reason (`close \"<why>\" "
            "--date %s`) and they are recorded as left. Nothing was written."
            % (paths.feature_dir(*held), "\n  - ".join(lines(findings)), date))
    path, html, spec = kept
    spec["document"][chain.CLOSED] = {
        "date": date, "reason": reason if not schema.is_empty(reason) else COMPLETE,
        "left": findings}
    status.rewrite(path, html, spec)
    return path


# ------------------------------------------------------------------ status

def report(root):
    """The open feature and its audit, as text."""
    held = current(root)
    if held is None:
        return "no feature is open; the project's own set is in force.\n"
    out = ["feature: %s" % paths.feature_dir(*held)]
    already = closed(root)
    if already is not None:
        out.append("closed: %s (%s)" % (already.get("date"), already.get("reason")))
        for one in lines(already.get("left") or ()):
            out.append("  left: %s" % one)
        out.append("next: python3 -m z2s.feature open <slug>")
        return "\n".join(out) + "\n"
    findings = audit(root)
    if findings:
        out.append("open: %d finding%s" % (len(findings), "" if len(findings) == 1 else "s"))
        out.extend("  - " + one for one in lines(findings))
    else:
        out.append("audit: clean; `close --date YYYY-MM-DD` would succeed")
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ the command

def _option(argv, flag, out):
    if flag not in argv:
        return None
    at = argv.index(flag)
    if at + 1 >= len(argv):
        out.write("%s needs a value\n" % flag)
        return ""
    value = argv[at + 1]
    del argv[at:at + 2]
    return value


USAGE = """\
usage: python3 -m z2s.feature open <slug> [--root DIR]
       python3 -m z2s.feature close ["<why>"] --date YYYY-MM-DD [--root DIR]
       python3 -m z2s.feature status [--root DIR]

One feature is open at a time; a close is audited, and a reason records what it left."""


def main(argv, out=sys.stdout):
    """The command. Its exit status is the answer (FR-VAL-05)."""
    argv = list(argv)
    values = {}
    for flag in ("--root", "--date"):
        got = _option(argv, flag, out)
        if got == "":
            return 2
        values[flag] = got
    root = values["--root"] or "."

    try:
        if len(argv) == 2 and argv[0] == "open":
            made = open(root, argv[1])
            out.write("opened %s\nnext: python3 -m z2s.author run %s --root %s\n"
                      % (made, intent.SLUG, root))
        elif argv and argv[0] == "close" and len(argv) <= 2:
            written = close(root, argv[1] if len(argv) == 2 else None, values["--date"])
            out.write("closed; wrote %s\n" % written)
        elif argv == ["status"]:
            out.write(report(root))
        else:
            out.write(USAGE + "\n")
            return 2
    except (Refused, chain.MissingPrerequisite, status.Refused, execute.Refused) as error:
        out.write("%s\n" % error)
        return 1
    return 0


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
