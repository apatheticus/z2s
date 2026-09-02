# -*- coding: utf-8 -*-
"""Folding a change into a published document, forward only (FR-SKL-06).

There are exactly three things this module can do to something already
published, and none of them removes it:

  * **amend** — attach a dated note recording that a later decision changed the
    entry. The original text stays, and a reader meets both.
  * **retire** — mark the entry as no longer scope, with a reason and optionally
    the identifier that succeeds it. The number stays reserved forever.
  * **refuse** — everything else, including deleting.

Deleting is not a fourth path that happens to be unimplemented; it is refused by
name, with the retirement it should have been. An agent that asks to delete gets
told what to do instead, which is more use than a command that does not exist.

Why forward only: identifiers are permanent (ADR-12), a reader who relied on a
requirement is entitled to find out what became of it, and the history of a
specification is part of the specification. A quiet overwrite is indistinguishable
from the requirement never having existed.

What actually gets written is the specification embedded in the document, spliced
back in place through the same serialiser the generators use, so an updated
document is byte-identical to a regenerated one. The rendered view follows,
because a document renders itself from the specification it carries.

    python3 -m z2s.update amend  <ID> "<what changed>" --date YYYY-MM-DD [--root DIR]
    python3 -m z2s.update retire <ID> "<why>" [--successor ID] [--root DIR]

Traces: FR-SKL-06, FR-AMD-01, FR-AMD-04, NFR-EVO-03, ADR-12, ADR-18, US-SKL-04.
"""

import glob
import os
import sys

from z2s import chain, paths, schema, status, trace

#: The field that marks an entry retired. Spelled here as the one the trace
#: engine already reads, so a retirement this module writes is a retirement that
#: module reports — the two cannot disagree about what the word means.
RETIRED = trace.RETIRED

#: Where a successor is recorded. Beside the reason rather than inside it,
#: because "superseded by FR-DOC-14" is a link a reader should be able to follow,
#: not a sentence they have to parse.
SUCCESSOR = "supersededBy"


class Refused(Exception):
    """Raised when an update would remove or overwrite something published."""


def sources(root):
    """Every document in the set, specifications and plan alike, in a stable order.

    Both, because an identifier may be defined in either and an operator asking
    to amend one should not have to know which directory it lives in.
    """
    return paths.documents(root)


def locate(root, identifier):
    """(path, text, spec, entry) for one identifier, or a refusal naming the problem.

    Reads through the shared extraction, like everything else that opens a
    document. The entry handed back is a live reference into the specification,
    so a caller amends it and writes the specification back — there is no second
    copy to keep in step.
    """
    found = []
    for path in sources(root):
        text, spec = status.read(path)
        for _, entry in schema.entries(spec):
            if entry.get("id") == identifier:
                found.append((path, text, spec, entry))

    if not found:
        raise Refused(
            "no document in %s defines %s. Nothing was changed. Check the "
            "identifier, or generate the document that would define it."
            % (paths.resolve(root, paths.ROOT), identifier))
    if len(found) > 1:
        raise Refused(
            "%s is defined in more than one document (%s). That is a collision "
            "to fix, not an entry to amend; nothing was changed."
            % (identifier, ", ".join(os.path.basename(one[0]) for one in found)))
    return found[0]


def amend(root, identifier, text, date):
    """Attach a dated amendment to a published entry. Returns the path written.

    The entry's own text is never touched — that is the whole guarantee. The
    amendment is appended below it, and a reader meets the original followed by
    what later changed about it.

    The date is required and is not defaulted: this module has no clock, by the
    same rule every other module in the toolchain follows, and an undated
    amendment is a change nobody can place against the decision that caused it.
    """
    for name, value in (("text", text), ("date", date)):
        if schema.is_empty(value):
            raise Refused("an amendment states no %s; nothing was written" % name)

    path, html, spec, entry = locate(root, identifier)
    existing = list(entry.get("amendments") or ())
    entry["amendments"] = existing + [{"date": date, "text": text}]

    # Checked before writing rather than trusted: `chain.amendments` is what
    # renders these, and an amendment it would refuse is one that reaches the
    # reader as a generation failure instead of a note.
    try:
        chain.amendments(entry, "entry")
    except chain.IncompleteBrief as error:
        raise Refused("%s; nothing was written" % error)

    return status.rewrite(path, html, spec)


def retire(root, identifier, reason, successor=None):
    """Withdraw an entry from scope, keeping its number reserved. Returns the path.

    Retirement is the answer to "delete this". The entry stays where it is, its
    identifier is never reused, and the document says plainly that it was
    withdrawn and why — which is what a reader who built against it needs.
    """
    if schema.is_empty(reason):
        raise Refused(
            "retiring %s states no reason. A withdrawn requirement with no "
            "reason is indistinguishable from one that was lost; nothing was "
            "written." % identifier)

    path, html, spec, entry = locate(root, identifier)
    already = entry.get(RETIRED)
    if not schema.is_empty(already):
        raise Refused("%s is already retired (%s); nothing was written."
                      % (identifier, already))

    entry[RETIRED] = reason
    if not schema.is_empty(successor):
        entry[SUCCESSOR] = successor
    return status.rewrite(path, html, spec)


def refuse_removal(identifier):
    """What to say when asked to delete something published (M13-P2-T2-C1)."""
    return ("%s cannot be deleted. Published content is never removed: a reader "
            "who relied on it is entitled to find out what became of it, and its "
            "identifier stays reserved forever. Retire it instead —\n"
            "    python3 -m z2s.update retire %s \"<why it is no longer scope>\" "
            "[--successor <the identifier that replaces it>]\n"
            "Nothing was changed." % (identifier, identifier))


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
usage: python3 -m z2s.update amend  <ID> "<what changed>" --date YYYY-MM-DD [--root DIR]
       python3 -m z2s.update retire <ID> "<why>" [--successor ID] [--root DIR]

Published content is never deleted or overwritten. Those are the two paths."""


def main(argv, out=sys.stdout):
    """The command. Its exit status is the answer (FR-VAL-05)."""
    argv = list(argv)
    values = {}
    for flag in ("--root", "--date", "--successor"):
        got = _option(argv, flag, out)
        if got == "":
            return 2
        values[flag] = got
    root = values["--root"] or "."

    if len(argv) >= 2 and argv[0] in ("delete", "remove", "drop"):
        out.write(refuse_removal(argv[1]) + "\n")
        return 1

    try:
        if len(argv) == 3 and argv[0] == "amend":
            written = amend(root, argv[1], argv[2], values["--date"])
        elif len(argv) == 3 and argv[0] == "retire":
            written = retire(root, argv[1], argv[2], values["--successor"])
        else:
            out.write(USAGE + "\n")
            return 2
    except (Refused, status.Refused) as error:
        out.write("%s\n" % error)
        return 1

    out.write("wrote %s\n" % written)
    return 0


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
