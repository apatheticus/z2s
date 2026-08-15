# -*- coding: utf-8 -*-
"""Committing and pushing the working branch, and offering — never assuming —
a pull request (FR-SKL-07).

The one thing this module exists to get right is the last step. Commit and push
are recoverable: a bad commit is amended, a pushed branch is a branch. Opening a
pull request is an announcement to other people, and it happens only when the
operator says yes in so many words. So the default run stops at the offer and
creating one is a separate invocation carrying explicit consent.

The status tool deliberately never touches a remote — publishing is the
operator's call, and a test keeps it that way. This is where that call is made,
which is why it is a separate module rather than another command there.

Every git command goes through the never-do rules before it runs, and a refusal
is reported as it stands. History is not rewritten, nothing is force-pushed, and
no branch is deleted.

    python3 -m z2s.ship --message "<subject>" [--root DIR] [--remote NAME]
    python3 -m z2s.ship pull-request --title "<title>" --body "<body>" --yes

Traces: FR-SKL-07, FR-EXE-11, FR-EXE-12, NFR-SEC-04, ADR-18, US-SKL-05.
"""

import os
import subprocess
import sys

from z2s import safety

DEFAULT_REMOTE = "origin"

#: What the operator has to say for a pull request to be created. Spelled as a
#: flag rather than inferred from a run that "looks like" it wanted one: consent
#: read from context is consent nobody gave.
CONSENT = "--yes"


class Refused(Exception):
    """Raised when a command is prohibited, or git reports a failure."""


def _git(root, *arguments):
    """Run one git command in the project, or refuse. Returns its output.

    The never-do rules are asked first, every time, and a refusal is never
    reshaped into a command that would get past them (M6-08).
    """
    command = "git " + " ".join(arguments)
    broken = safety.refusal(command, area=root)
    if broken:
        raise Refused("refused: %s" % " ".join(broken))
    finished = subprocess.run(["git", "-C", os.path.abspath(root)] + list(arguments),
                              capture_output=True, text=True, check=False)
    if finished.returncode != 0:
        raise Refused("%s failed: %s"
                      % (command, finished.stderr.strip() or finished.stdout.strip()))
    return finished.stdout.strip()


def branch(root):
    """The branch the work is on."""
    found = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if found == "HEAD":
        raise Refused("the repository is not on a branch (detached HEAD). "
                      "Check out a branch before shipping; nothing was done.")
    return found


def pending(root):
    """Whether there is anything to commit."""
    return bool(_git(root, "status", "--porcelain"))


def commit(root, message):
    """Stage everything on the working branch and commit it. Returns the subject.

    Everything, because that is what the operator asked for — a partial commit
    chosen by a tool is a tree nobody reviewed. Nothing to commit is not an
    error: a branch that is already committed and merely unpushed is the common
    case, and refusing it would make the skill useless exactly then.
    """
    if not pending(root):
        return None
    _git(root, "add", "--all")
    _git(root, "commit", "-m", message)
    return message


def push(root, remote=DEFAULT_REMOTE):
    """Push the working branch, setting upstream. Returns the branch pushed.

    A plain push. No force, no lease, no history rewritten — the never-do rules
    refuse all three, and this asks them rather than knowing better.
    """
    here = branch(root)
    _git(root, "push", "--set-upstream", remote, here)
    return here


def offer(root, remote=DEFAULT_REMOTE):
    """The pull-request question, as sentences. Creates nothing.

    Returning the words rather than asking them is what keeps the decision with
    the operator: this module cannot accidentally take silence for a yes,
    because it has no way to hear one.
    """
    here = branch(root)
    return ("%s is committed and pushed to %s.\n\n"
            "Open a pull request for it? Nothing has been opened and nothing "
            "will be unless you say so. To create one:\n"
            "    python3 -m z2s.ship pull-request --title \"<title>\" "
            "--body \"<body>\" %s" % (here, remote, CONSENT))


def pull_request(root, title, body, consented, remote=DEFAULT_REMOTE):
    """Create the pull request, and only on an explicit yes (M13-P2-T3-C1).

    The consent check happens before anything else — before the branch is read,
    before the tool is looked for — so that no path through this function can
    reach the creation without having passed it.
    """
    if not consented:
        raise Refused(
            "a pull request is created only on an explicit yes. Re-run with %s "
            "once the operator has said so. Nothing was opened." % CONSENT)
    if not title or not title.strip():
        raise Refused("a pull request needs a title; nothing was opened.")

    here = branch(root)
    command = ["gh", "pr", "create", "--head", here,
               "--title", title, "--body", body or ""]
    broken = safety.refusal(" ".join(command), area=root)
    if broken:
        raise Refused("refused: %s" % " ".join(broken))
    finished = subprocess.run(command, cwd=os.path.abspath(root),
                              capture_output=True, text=True, check=False)
    if finished.returncode != 0:
        raise Refused("opening the pull request failed: %s"
                      % (finished.stderr.strip() or finished.stdout.strip()))
    return finished.stdout.strip()


def run(root, message, remote=DEFAULT_REMOTE):
    """Commit, push, and stop at the offer. Returns the lines to report."""
    lines = []
    subject = commit(root, message)
    lines.append("committed: %s" % subject if subject
                 else "nothing to commit; the working tree is clean")
    lines.append("pushed: %s" % push(root, remote))
    lines.append("")
    lines.append(offer(root, remote))
    return lines


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
usage: python3 -m z2s.ship --message "<subject>" [--root DIR] [--remote NAME]
       python3 -m z2s.ship pull-request --title "<title>" --body "<body>" --yes

A pull request is created only on an explicit yes."""


def main(argv, out=sys.stdout):
    """The command. Its exit status is the answer (FR-VAL-05)."""
    argv = list(argv)
    consented = CONSENT in argv
    if consented:
        argv.remove(CONSENT)
    values = {}
    for flag in ("--root", "--remote", "--message", "--title", "--body"):
        got = _option(argv, flag, out)
        if got == "":
            return 2
        values[flag] = got
    root = values["--root"] or "."
    remote = values["--remote"] or DEFAULT_REMOTE

    try:
        if argv == ["pull-request"]:
            out.write(pull_request(root, values["--title"], values["--body"],
                                   consented, remote) + "\n")
            return 0
        if not argv:
            if not values["--message"] or not values["--message"].strip():
                out.write("--message is required: a commit needs a subject "
                          "somebody chose\n")
                return 2
            out.write("\n".join(run(root, values["--message"], remote)) + "\n")
            return 0
    except Refused as error:
        out.write("%s\n" % error)
        return 1

    out.write(USAGE + "\n")
    return 2


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
