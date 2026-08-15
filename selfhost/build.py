# -*- coding: utf-8 -*-
"""Produce the method's own document set with the method (M12-P3-T3).

    python3 -m selfhost.build            # generate into .zero/ and check
    python3 -m selfhost.build --check    # generate, and fail if anything moved

`--check` is the one that belongs in a pipeline. It generates into a scratch
copy, compares every file with what is committed, and fails on the first
difference — which catches both halves of the claim at once: that the toolchain
still produces this set, and that the set on disk is what it produces.

A defect in a generator shows up here before it shows up in anybody else's
project, which is the whole reason for doing it this way rather than keeping a
hand-written example.

The published documents under `docs/` are NOT touched. They are built by a
separate, older generator and are the project's public face; leaving them alone
is a standing decision, and duplicating them here would create the second copy
this method exists to prevent.
"""

import filecmp
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selfhost import briefs, plan_data
from z2s import (briefing, context, fsd, gate, paths, pipeline, plan, prd,
                 sdd, stories, trace, vision)

#: Where the self-hosted set lives, relative to the repository root. Not a
#: separate directory: this IS a Zero-to-Ship project, laid out the way the
#: method lays every project out.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The chain, in order. Each entry is the generator and the brief it is given.
#: The briefing comes last because it reads everything above it.
CHAIN = ((vision, briefs.vision),
         (context, briefs.context),
         (prd, briefs.prd),
         (fsd, briefs.fsd),
         (stories, briefs.stories),
         (sdd, briefs.sdd),
         (briefing, briefs.briefing))


def _closed(run):
    """Answer every fork with its recommendation, and say that is what happened.

    The self-hosted set has an owner who is not in the room, so the honest thing
    is to take the stated recommendation and record that as the reason. A fork
    whose recommendation is wrong for this project is a fork whose brief should
    state the fact instead.
    """
    while True:
        question = run.question()
        if question is None:
            return run
        run.answer(question.id, question.recommended.id,
                   "The recommendation, taken for the method's own set.")


def specifications(root):
    """Author every document above the plan. Returns the paths written."""
    written = []
    for module, make in CHAIN:
        made = make()
        forks = module.FORKS if module is vision else module.forks(made)
        path, _ = module.author(
            root, made, _closed(gate.Gate(module.SLUG, forks, source=made)))
        written.append(path)
    return written


def plan_brief():
    return {"title": "Zero-to-Ship — Development plan",
            "owner": briefs.OWNER, "date": briefs.DATE,
            "summary": "How the method gets built, and in what order.",
            "gauntlet": list(plan_data.GAUNTLET),
            "milestones": [dict(one) for one in plan_data.MILESTONES],
            "prerequisites": [dict(one) for one in plan_data.PREREQUISITES]}


def planning(root):
    """Write the milestone detail, then author the plan. Returns the paths."""
    for identifier, phases in plan_data.DETAILS.items():
        with open(plan.detail_path(root, identifier), "w",
                  encoding="utf-8") as handle:
            json.dump(phases, handle, indent=1, sort_keys=True)
    made = plan_brief()
    written, _, _ = plan.author(
        root, made, _closed(gate.Gate(plan.SLUG, plan.forks(made), source=made)))
    return list(written)


def build(root):
    """The whole set: specifications, then the plan that claims all of it."""
    paths.ensure_layout(root)
    return specifications(root) + planning(root)


def documents(root):
    """Every file the build owns, as paths relative to the project."""
    found = []
    for relative in (paths.SPECS_DIR, paths.PLAN_DIR):
        directory = paths.resolve(root, relative)
        for name in sorted(os.listdir(directory)) if os.path.isdir(directory) else []:
            if name.endswith(".html"):
                found.append(os.path.join(relative, name))
    return sorted(found)


def gates(root, out):
    """Every gate the method has, run against the method's own set.

    The set the pipeline is given is the whole of it — specifications and plan
    together — because coverage is a property of the set and a gate handed half
    a set would pass on the half it could see (M12-P3-T3-C2).
    """
    sources = [paths.resolve(root, one) for one in documents(root)]
    return pipeline.main(sources, out)


def differences(root, other):
    """Which files differ between the committed set and a freshly built one."""
    found = []
    for relative in documents(root):
        left, right = paths.resolve(root, relative), paths.resolve(other, relative)
        if not os.path.exists(right):
            found.append("%s: the build no longer produces it" % relative)
        elif not filecmp.cmp(left, right, shallow=False):
            found.append("%s: differs from what the toolchain produces" % relative)
    for relative in documents(other):
        if not os.path.exists(paths.resolve(root, relative)):
            found.append("%s: the build produces it and it is not committed"
                         % relative)
    return found


def check(root, out):
    """Build into a scratch copy and fail on any difference (M12-P3-T3-C1)."""
    scratch = tempfile.mkdtemp(prefix="z2s-selfhost-")
    try:
        build(scratch)
        found = differences(root, scratch)
        for line in found:
            out.write("  %s\n" % line)
        out.write("self-hosted set: %d documents, %d differ%s\n"
                  % (len(documents(root)), len(found),
                     "" if len(found) == 1 else ""))
        return 1 if found else 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


USAGE = "usage: python3 -m selfhost.build [--check] [--root DIR]"


def main(argv, out=sys.stdout):
    rest, root = list(argv), ROOT
    if "--root" in rest:
        at = rest.index("--root")
        if at + 1 >= len(rest):
            out.write(USAGE + "\n")
            return 2
        root = rest[at + 1]
        del rest[at:at + 2]

    checking = "--check" in rest
    if checking:
        rest.remove("--check")
    if rest:
        out.write(USAGE + "\n")
        return 2

    if checking:
        code = check(root, out)
        if code:
            return code
    else:
        written = build(root)
        out.write("built %d documents into %s\n"
                  % (len(written), os.path.join(root, paths.ROOT)))
    return gates(root, out)


if __name__ == "__main__":                                  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
