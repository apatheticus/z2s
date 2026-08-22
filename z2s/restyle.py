# -*- coding: utf-8 -*-
"""Re-rendering every document in a project against its current design system.

A generated document inlines its own stylesheet. That is what makes it a single
file somebody can open from disk with no server (NFR-ARC-03), and it is also why
nothing that changes afterwards ever reaches it. Two promises were true of a
first generation and false of every project that already had documents:

  * **FR-GEN-02** — documents adopt the host project's design system. They adopt
    it on the day they are written. `/zero:design` says in its own words to run
    it when the design system changes, and all it writes is the record.
  * **FR-DOC-06** — a document re-renders from its own embedded specification
    without loss. True one document at a time; there was no way to ask it of a
    set, so an upgrade to the toolchain reached nothing already generated.

This closes both, by doing to a whole project what `chain.regenerate` does to one
document: read the specification each document already carries and render it
again. The design system is checked first, exactly the way a first generation
checks it — record, then detection, then neutral — because "re-style with the
current design" and "re-style with whatever was true when this process started"
are different commands, and only the first is any use.

Nothing here decides anything about colour. `design.theme` owns the ladder and
the sentence that reports it; this module's whole contribution is the loop, the
element identifier each document needs back, and the refusal.

**Every document is read before any is written.** A half-restyled set is worse
than an unstyled one: both look fine, and only one of them is consistent.

    python3 -m z2s.restyle [--check] [--root DIR]

Traces: FR-GEN-02, FR-GEN-03, FR-GEN-07, FR-DOC-06, NFR-GEN-01, NFR-GEN-02.
"""

import collections
import os
import sys

from z2s import chain, design, paths, plan, validate, writer

#: What a run did. Both halves are reported, always: a run that changed nothing
#: has to say so rather than stay quiet and read as work (FR-GEN-03).
Restyled = collections.namedtuple("Restyled", "written current note")


class Unreadable(Exception):
    """A document in the set carries no specification to render again."""


def spec_id(root, path, spec):
    """The element identifier this document is embedded under.

    Dispatched on the directory the document came from, and not on its slug.
    A plan is one document split across files and every part of it carries the
    slug "plan", so the `<slug>-spec` form every specification uses would write
    `plan-spec` into all sixteen files and quietly stop the milestones being
    milestones. `pipeline.regenerate` gets away with the slug form only because
    it throws its output away.

    The identifier cannot be read back out of the file: `validate.BLOCK` matches
    the embedding element by its type rather than its identifier (NFR-DAT-01),
    so it captures the specification and not the attribute. Adding a second
    parser here to recover one attribute would be a second definition of what a
    document is, which is the thing that regex exists to prevent.
    """
    if os.path.dirname(os.path.abspath(path)) == paths.resolve(root, paths.PLAN_DIR):
        return (plan.INDEX_SPEC_ID if os.path.basename(path) == plan.INDEX_FILE
                else plan.MILESTONE_SPEC_ID)
    return "%s-spec" % spec["document"]["slug"]


def load(root):
    """Every document in the project with the specification it carries.

    All of them, before anything is written. A document that cannot be read
    stops the run here, where nothing has been touched yet.
    """
    found = []
    for path in paths.documents(root):
        try:
            with open(path, encoding="utf-8") as handle:
                held = handle.read()
        except (OSError, UnicodeDecodeError) as trouble:
            raise Unreadable("%s could not be read (%s). Nothing was written."
                             % (path, trouble))
        try:
            spec = validate.extract(held)
        except validate.ExtractionError as error:
            raise Unreadable(
                "%s carries no readable specification (%s). A document is its own "
                "source, so there is nothing to render it from. Nothing was "
                "written." % (path, error))
        try:
            found.append((path, held, spec, spec_id(root, path, spec)))
        except KeyError:
            raise Unreadable(
                "%s names no document slug, so there is no identifier to embed "
                "it under. Nothing was written." % path)
    return found


def restyle(root, check=False):
    """Re-render every document against the project's current design system.

    The cache is dropped first. `design.theme` remembers its answer per project
    root, which is right for a generation rendering sixteen files and exactly
    wrong here: the caller most likely to run this is `/zero:design`, in the same
    process that has just written the record this run exists to pick up.
    """
    held = load(root)
    if not held:
        raise Unreadable(
            "there are no documents under %s to restyle. Generate the set first."
            % paths.resolve(root, paths.ROOT))

    design.forget()
    theme = design.theme(root)

    written, current = [], []
    for path, before, spec, identifier in held:
        after = chain.render(spec, identifier, root)
        if after == before:
            current.append(path)
            continue
        written.append(path)
        if not check:
            writer.write(path, after)
    return Restyled(written, current, theme.note)


def report(found, check=False):
    """What the run did, in the words a reader needs to act on."""
    total = len(found.written) + len(found.current)
    if check:
        line = ("would restyle %d of %d documents; %d %s already current"
                % (len(found.written), total, len(found.current),
                   "is" if len(found.current) == 1 else "are"))
    elif found.written:
        line = ("restyled %d of %d documents; %d were already current"
                % (len(found.written), total, len(found.current)))
    else:
        line = "every document was already current (%d of %d)" % (total, total)
    named = "".join("\n  %s" % os.path.basename(one) for one in found.written)
    return "%s\n%s%s" % (found.note, line, named)


USAGE = """\
usage: python3 -m z2s.restyle [--check] [--root DIR]

Re-renders every document in the project against its design system, checked the
way a first generation checks it: the design record, then the host project's own
files, then the neutral theme.

--check reports what would change and writes nothing. It is a preview and never
fails: a document waiting to be restyled is still a document worth reading."""


def main(argv, out=sys.stdout):
    """The command. Its exit status is the answer (FR-VAL-05)."""
    argv = list(argv)
    check = False
    if "--check" in argv:
        argv.remove("--check")
        check = True

    root = "."
    if "--root" in argv:
        at = argv.index("--root")
        if at + 1 >= len(argv):
            out.write("--root needs a value\n")
            return 2
        root = argv[at + 1]
        del argv[at:at + 2]

    if argv:
        out.write(USAGE + "\n")
        return 2

    try:
        found = restyle(root, check=check)
    except Unreadable as error:
        out.write("%s\n" % error)
        return 1

    out.write(report(found, check) + "\n")
    return 0


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
