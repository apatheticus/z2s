# -*- coding: utf-8 -*-
"""Setup, performed by the method rather than asked of the operator (FR-SKL-09).

Every mechanic a project needs before the chain can run — the directory layout,
the ignore rules, the design tokens, the record of how work gets proved — is
done here, by the skill that needs it. NFR-SKL-04 states the rule plainly: a
step whose instructions ask the operator to type a shell command is a defect in
that step, not a convenience.

Two properties matter more than what it creates:

  * **It is idempotent.** A second run changes no byte. That is what lets every
    chain skill call it whenever it finds setup missing, without an operator
    having to know whether it has been called before (M13-P1-T4-C2).
  * **It never overwrites.** An existing ignore file may carry a project's own
    additions and an existing worker record may carry its real commands, so
    both are left exactly as found and reported as already present.

What it deliberately does NOT do is invent a project's verification commands out
of nothing. The gauntlet it writes is the one check that is true of every
project the method runs in — the method's own pipeline over the document set —
and the worker list is left empty, so /zero:build refuses by name until an
operator supplies real ones. A recorded command nobody chose is worse than an
absent one: it passes, and the passing means nothing.

    python3 -m z2s.project [--root DIR]

Traces: FR-SKL-09, FR-GEN-03, NFR-SKL-04, NFR-OPS-01, ADR-11, ADR-18, US-SKL-07.
"""

import json
import os
import sys

from z2s import design, paths, writer

#: The one verification layer init can honestly record. It checks the document
#: set the method itself produces, so it is true before a project has written a
#: line of its own code, and it is a real command rather than a placeholder.
DEFAULT_GAUNTLET = {"CI": "python3 -m z2s.pipeline --record ."}

#: Written only when there is no worker record at all. The empty worker list is
#: the point: it is what makes /zero:build refuse and name what is missing,
#: rather than dispatching work to a command nobody chose.
STARTER = {
    "workers": [],
    "gauntlet": dict(DEFAULT_GAUNTLET),
}

#: What is still outstanding after a bare setup, in the words a report uses.
OUTSTANDING = ("no workers are configured yet, so /zero:build will refuse until "
               "%s names at least one build worker and one judge")


def workers_path(root):
    return paths.resolve(root, paths.WORKERS_FILE)


def needs_setup(root):
    """Whether this project is missing anything the chain requires.

    Read-only, and cheap enough to run at the head of every skill — which is
    what FR-SKL-09 asks for. Existence is the whole question here: the contents
    of an ignore file or a worker record are the project's business, and a probe
    that second-guessed them would overwrite work somebody did on purpose.
    """
    for relative in paths.DIRECTORIES + (paths.IGNORE_FILE, paths.WORKERS_FILE):
        if not os.path.exists(paths.resolve(root, relative)):
            return True
    return False


def initialise(root):
    """Perform every setup mechanic, and report what actually happened.

    Returns a record of what was created, what was already there, which design
    system was adopted, and what remains outstanding. Reported rather than
    assumed, because a setup step that claims work it did not do is the same
    dishonesty a skipped gate reported as passed would be (FR-GEN-03).
    """
    done = paths.ensure_layout(root)

    target = workers_path(root)
    if os.path.exists(target):
        done["existed"].append(paths.WORKERS_FILE)
        outstanding = ()
    else:
        writer.write(target, json.dumps(STARTER, indent=2, sort_keys=True) + "\n")
        done["created"].append(paths.WORKERS_FILE)
        outstanding = (OUTSTANDING % paths.WORKERS_FILE,)

    found = design.detect(root)
    done["tokens"] = found.source
    done["outstanding"] = list(outstanding)
    return done


def format_report(done):
    """The setup, written for the person who has to act on it."""
    lines = []
    for name in done["created"]:
        lines.append("created  %s" % name)
    for name in done["existed"]:
        lines.append("present  %s" % name)
    lines.append(design.report(done["tokens"]))
    if not done["created"]:
        lines.append("setup was already complete; nothing was changed")
    for one in done["outstanding"]:
        lines.append("outstanding: %s" % one)
    return "\n".join(lines)


def main(argv, out=sys.stdout):
    """The command. Exit zero: setting an already-set-up project up is not an
    error, it is the idempotence every chain skill relies on."""
    argv = list(argv)
    root = "."
    if "--root" in argv:
        at = argv.index("--root")
        if at + 1 >= len(argv):
            out.write("--root needs a value\n")
            return 2
        root = argv[at + 1]
        del argv[at:at + 2]
    if argv:
        out.write("usage: python3 -m z2s.project [--root DIR]\n")
        return 2

    out.write(format_report(initialise(root)) + "\n")
    return 0


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
