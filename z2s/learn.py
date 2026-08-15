# -*- coding: utf-8 -*-
"""Compounding memory — what a milestone taught, carried into the next one.

A run that forgets what the last run learned repeats it. This module is the
method's memory: one markdown file per closed milestone, sitting beside the
milestone document it belongs to, read by every later brief.

Three rules, and they are all about making memory unavoidable rather than
available:

* **A milestone does not close without a retrospective**, and the retrospective
  has to actually contain the decisions the run recorded (FR-LRN-01). A run may
  decide anything it likes without asking; what it may not do is decide it
  quietly and let the record close over it.
* **Every later brief has read all of them** (FR-LRN-02, FR-LRN-03). Not "may
  consult" — the brief carries them, and the check that a brief is complete
  reads the same list the builder does.
* **A theme that comes back three times stops being advice** and becomes a
  candidate change to the method itself (FR-LRN-04). Twice is a coincidence a
  human might notice; three times is a count, and a count can be automated.

The tag set is DERIVED, never stored: it is whatever the existing retrospectives
say in their headers. A second file listing the allowed tags would be a second
source of truth about a set that already exists in plain sight.

Dates come from the caller, here as everywhere else in the method (NFR-GEN-01).
A retrospective with no date says so rather than inventing one.

Traces: FR-LRN-01, FR-LRN-02, FR-LRN-03, FR-LRN-04, NFR-EVO-04, ADR-14,
US-LRN-01.
"""

import collections
import glob
import os
import sys

from z2s import paths, writer

#: The line a retrospective states its themes on. One line, comma separated,
#: because the tag set has to be readable by a person and greppable by a tool.
TAG_HEADER = "Tags:"

#: The three questions a retrospective answers. Data rather than prose in a
#: template, so the draft and any check of a draft read one list.
SECTIONS = ("What was learned",
            "What surprised the run",
            "What the next milestone should do differently")

#: How many separate retrospectives a theme must appear in before it is raised
#: against the method rather than against the next milestone.
ESCALATION = 3

#: How many before it is worth stating as a convention. Lower on purpose: a
#: convention is a suggestion to the next builder, an escalation is a change to
#: the method, and those two should not need the same weight of evidence.
CONVENTION = 2

#: The retrospective filename, split around the milestone number it carries.
#: Derived from the layout rather than spelled again here, so the two cannot
#: disagree about where a retrospective lives.
_HEAD, _TAIL = os.path.basename(paths.LESSONS_TEMPLATE).split("%s")


class Refused(Exception):
    """A milestone that will not close."""


Retrospective = collections.namedtuple("Retrospective",
                                       "milestone number path text tags")


# --------------------------------------------------------------- the locations

def number(milestone):
    """The digits of a milestone identifier — `M12` is retrospective 12."""
    return "".join(one for one in str(milestone) if one.isdigit())


def path(root, milestone):
    """Where this milestone's retrospective lives."""
    return paths.resolve(root, paths.LESSONS_TEMPLATE % number(milestone))


def _milestone_of(filename):
    """The milestone a retrospective filename belongs to, or ""."""
    name = os.path.basename(filename)
    if not name.startswith(_HEAD) or not name.endswith(_TAIL):
        return ""
    digits = name[len(_HEAD):len(name) - len(_TAIL)]
    return _HEAD + digits if digits.isdigit() else ""


# ----------------------------------------------------------------- the reading

def tags(text):
    """The themes a retrospective claims, in the order it states them.

    Repeats collapse: a retrospective that says "ordering" three times has
    raised one theme, not three, and counting it three times would let a single
    wordy retrospective escalate itself against the method.
    """
    found = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("#*- ").strip()
        if not stripped.startswith(TAG_HEADER):
            continue
        for one in stripped[len(TAG_HEADER):].split(","):
            word = one.strip().strip("`").lower()
            if word and word not in found:
                found.append(word)
    return found


def existing(root):
    """Every retrospective in the project, in milestone order.

    Milestone order, not filename order: `M10` follows `M2`, and sorting the
    names alphabetically would tell the next builder the history happened in an
    order it did not happen in.
    """
    found = []
    for name in glob.glob(paths.resolve(root, paths.LESSONS_TEMPLATE % "*")):
        milestone = _milestone_of(name)
        if not milestone:
            continue
        try:
            with open(name, encoding="utf-8") as handle:
                text = handle.read()
        except OSError:
            continue
        found.append(Retrospective(milestone, int(number(milestone)), name,
                                   text, tags(text)))
    return sorted(found, key=lambda one: one.number)


def prior(root, milestone):
    """Every retrospective a milestone should have read before starting."""
    limit = number(milestone)
    if not limit:
        return existing(root)
    return [one for one in existing(root) if one.number < int(limit)]


# ------------------------------------------------------------------ the themes

def themes(root):
    """Each theme, and the milestones that raised it."""
    raised = collections.OrderedDict()
    for one in existing(root):
        for tag in one.tags:
            raised.setdefault(tag, []).append(one.milestone)
    return collections.OrderedDict(sorted(raised.items()))


def escalations(root, threshold=ESCALATION):
    """Themes recurring often enough to be a candidate change to the method."""
    return [{"tag": tag, "milestones": milestones}
            for tag, milestones in themes(root).items()
            if len(milestones) >= threshold]


def conventions(root, threshold=CONVENTION):
    """The distilled summary every later brief carries (FR-LRN-03).

    Derived from repeated themes rather than maintained by hand: a conventions
    document nobody updates is worse than none, because it is believed.
    """
    repeated = [(tag, milestones) for tag, milestones in themes(root).items()
                if len(milestones) >= threshold]
    if not repeated:
        return ["No theme has come up in %d milestones yet; there is nothing "
                "distilled to apply." % threshold]
    return ["%s — raised by %s. Treat it as settled practice, not as news."
            % (tag, ", ".join(milestones)) for tag, milestones in repeated]


def format_themes(root):
    """The themes and the escalations, as a person reads them."""
    lines = []
    for tag, milestones in themes(root).items():
        lines.append("  %-24s %d · %s" % (tag, len(milestones),
                                          ", ".join(milestones)))
    raised = escalations(root)
    if raised:
        lines.append("")
        lines.append("candidate changes to the method itself (%d), each raised "
                     "in %d or more milestones:" % (len(raised), ESCALATION))
        lines.extend("  %-24s %s" % (one["tag"], ", ".join(one["milestones"]))
                     for one in raised)
    return "\n".join(lines) if lines else "no retrospectives have been written yet"


# ------------------------------------------------------------------- the draft

def recorded(ledger, milestone):
    """The decisions this milestone's units took without asking (FR-EXE-08)."""
    prefix = str(milestone) + "-"
    return [one for one in ledger.get("decisions") or ()
            if isinstance(one, dict) and str(one.get("unit", "")).startswith(prefix)
            and (one.get("decision") or "").strip()]


def _unfinished(ledger, milestone):
    prefix = str(milestone) + "-"
    return sorted((key, value)
                  for key, value in (ledger.get("unfinished") or {}).items()
                  if key.startswith(prefix))


def _derived_tags(decided, unfinished):
    """The themes the facts themselves support. A worker may add better ones."""
    found = []
    if decided:
        found.append("decisions-taken")
    if unfinished:
        found.append("unfinished-work")
    return found or ["clean-run"]


def draft(milestone, ledger, entries, date):
    """A retrospective assembled from what the run already recorded.

    Seeded from facts, not from prose: the units and their statuses, the
    decisions the ledger holds, and what ran out of attempts. The three
    questions are left open for whoever writes the answers — this is a draft a
    human or a worker finishes, and it closes the milestone as it stands.
    """
    decided = recorded(ledger, milestone)
    stuck = _unfinished(ledger, milestone)
    lines = ["# %s — lessons learned" % milestone, "",
             "Date: %s" % (date or "not stated"),
             "%s %s" % (TAG_HEADER, ", ".join(_derived_tags(decided, stuck))),
             "", "## The work", ""]
    for entry in entries or ():
        lines.append("- %s %s — %s" % (entry.get("id"), entry.get("title") or "",
                                       entry.get("status") or "not started"))
    if not entries:
        lines.append("- (this milestone states no units of work)")

    lines.extend(["", "## Decisions taken without asking", ""])
    lines.extend("- %s: %s — %s" % (one["unit"], one["decision"],
                                    one.get("why") or "no reason recorded")
                 for one in decided)
    if not decided:
        lines.append("- (none: every call this milestone needed was already "
                     "settled)")

    if stuck:
        lines.extend(["", "## What did not finish", ""])
        lines.extend("- %s: %s" % (key, value) for key, value in stuck)

    for heading in SECTIONS:
        lines.extend(["", "## %s" % heading, "",
                      "- (to be written before the next milestone starts)"])
    return "\n".join(lines) + "\n"


def record(root, milestone, ledger, date, entries=()):
    """Write this milestone's retrospective draft. Returns where it went."""
    target = path(root, milestone)
    writer.write(target, draft(milestone, ledger, entries, date))
    return target


# ------------------------------------------------------------------- the close

def close(root, milestone, ledger):
    """Refuse to close a milestone whose record does not account for itself.

    Two refusals, and the second is the one that matters. A retrospective is
    easy to produce and easy to make say nothing; the check that bites is that
    every decision the run took without asking appears in it (M12-P1-T1-C2).
    """
    target = path(root, milestone)
    if not os.path.exists(target):
        raise Refused("%s has no retrospective at %s; a milestone does not "
                      "close without one"
                      % (milestone, os.path.relpath(target, os.path.abspath(root))))
    with open(target, encoding="utf-8") as handle:
        text = handle.read()
    # Named once each. Several units of one milestone commonly take the same
    # call, and a refusal that says the same sentence three times reads as
    # three problems (found by driving a real run, M12).
    missing = []
    for one in recorded(ledger, milestone):
        if one["decision"] not in text and one["decision"] not in missing:
            missing.append(one["decision"])
    if missing:
        raise Refused("%s's retrospective does not account for %d decision%s "
                      "this run recorded: %s"
                      % (milestone, len(missing), "" if len(missing) == 1 else "s",
                         "; ".join(missing)))
    return target


# ------------------------------------------------------------- the command line

USAGE = "usage: python3 -m z2s.learn [--root DIR] themes | history"


def _root(argv):
    rest, root = [], "."
    skip = False
    for index, word in enumerate(argv):
        if skip:
            skip = False
            continue
        if word == "--root":
            if index + 1 >= len(argv):
                raise Refused("--root needs a directory")
            root, skip = argv[index + 1], True
        else:
            rest.append(word)
    return root, rest


def main(argv, out=sys.stdout):
    if not argv:
        out.write(USAGE + "\n")
        return 2
    try:
        root, rest = _root(list(argv))
    except Refused as error:
        out.write("%s\n%s\n" % (error, USAGE))
        return 2
    if rest and rest[0] == "themes":
        out.write(format_themes(root) + "\n")
        return 0
    if rest and rest[0] == "history":
        found = existing(root)
        for one in found:
            out.write("%-6s %-40s %s\n" % (one.milestone,
                                           os.path.basename(one.path),
                                           ", ".join(one.tags) or "(no themes)"))
        if not found:
            out.write("no retrospectives have been written yet\n")
        return 0
    out.write(USAGE + "\n")
    return 2


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
