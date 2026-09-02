# -*- coding: utf-8 -*-
"""The verification layers: what they cost, which of them guard the whole repo.

A gauntlet is a set of commands and nothing in the method said what order to run
them in, so every gauntlet ran in whatever order the project happened to write
them down. On a measured build that cost 25.4 minutes to reach a verdict of "no"
— an end-to-end suite and a browser pass had already run before the static check
that was going to fail got its turn. The order is not a project's business to
get right: the same eight layers cost the same relative amounts in every project
there has ever been, so the order is stated once, here, and every gauntlet runs
in it (NFR-EXE-12).

The second thing this module knows is which layers need something that is not in
the repository — a database, a browser, a server, a person. That distinction is
what makes a preflight possible: the layers that need nothing can be run at any
moment, against any tree, by anybody, which is exactly what a run needs from a
check it wants to make before it settles a dispatch (FR-EXE-17).

And the third is a consequence of the second. A project's gauntlet usually holds
layers no single unit names — the package-wide scanners, the determinism check,
the budget summed across files this unit never opened. Seven of twelve gauntlet
failures on that same build were one of those, and every one discarded a
finished dispatch and briefed a fresh worker from nothing, because nothing in
the unit's brief had ever mentioned the guard it broke. So the brief names them
(NFR-EXE-04, amended).

A leaf, deliberately. It imports `schema` for the layer vocabulary and nothing
else in this package: `status` wants `KNOWN` from here, and importing it back
would make a cycle out of two modules that each answer one question. What runs a
command is handed in — `runner(layer, command) -> int` — so this module decides
what to run and in what order and observes nothing itself.

Traces: FR-EXE-17, NFR-EXE-12, NFR-EXE-03, NFR-EXE-04.
"""

from z2s import schema

#: Every layer the method knows, in the order the specification lists them.
#: Read from the schema rather than written again, so a layer cannot exist in
#: one of the two places.
KNOWN = tuple(one["id"] for one in schema.ENUMS["testLayers"])

#: The one published cost order, cheapest first (NFR-EXE-12). Not a project's to
#: set and not a knob: a configured order is a configured way of getting it
#: wrong, and the precedent is already set by the re-run rule in
#: `execute.prove` — a number that would let somebody hide a broken check is a
#: number this method does not offer.
#:
#: The ranking is by what a layer needs before it can say anything, not by how
#: long any particular project's command happens to take. Static analysis reads
#: files. Unit tests import them. Integration wants a database. Accessibility
#: wants a rendered page, so a server and a browser. End-to-end wants the whole
#: product running. Performance wants all of that and then wants it measured.
#: CI wants a remote. Human review wants a person, and there is nothing cheaper
#: than everything else that a person is.
COST = ("lint", "unit", "integration", "a11y", "e2e", "perf", "CI", "manual")

#: The layers that need something the repository does not contain. Everything
#: outside this set runs against a checkout and nothing more, which is what
#: makes it safe to run one at a moment the run chose rather than at the end of
#: a sequence.
INFRASTRUCTURE = frozenset(("integration", "a11y", "e2e", "perf", "CI", "manual"))

#: What a brief says about the guards, when there are any. One sentence and a
#: list, because the finding was not that workers ignored these checks — it was
#: that no worker had ever been told they existed.
PREAMBLE = ("This project runs these checks over the whole repository, not over "
            "the files this unit declares alone. They are not in this unit's "
            "own layers, and until now nothing ever told a worker they existed:")


def rank(layer):
    """Where a layer sits in the cost order. Anything unknown sorts last."""
    return COST.index(layer) if layer in COST else len(COST)


def order(named):
    """The named layers, cheapest first, each once.

    Ties cannot happen — `COST` is a total order — so the same set of layers
    always produces the same sequence, which is what lets a test assert one
    (NFR-GEN-01).
    """
    return sorted(dict.fromkeys(named), key=rank)


def cheap(stated):
    """Every stated layer that runs against a checkout and nothing more.

    This is what a preflight runs, declared by the unit or not. The first
    version ran only the guards — the layers the unit had not named — on the
    reasoning that a unit's own layers were its own business and belonged in
    the gauntlet proper. On a measured build that reasoning discarded a
    finished forty-minute dispatch for a red in the unit's OWN unit tests,
    which the worker that wrote them was the one person placed to fix. Cheap
    is cheap whoever named it; the hand-back covers all of it (FR-EXE-17,
    amended).
    """
    return order(one for one in stated if one not in INFRASTRUCTURE)


def guards(stated, named):
    """The whole-repo checks this unit did not name, cheapest first.

    `stated` is the project's gauntlet, `named` the unit's own layers. What is
    left is what the run can hold this unit to without the unit ever having been
    told — so it is told (FR-EXE-17, NFR-EXE-04). This is the NAMING half, for
    the brief; `cheap` is what a preflight actually runs.

    Infrastructure-free only. A guard that needs a database is not a guard the
    run can put in front of a dispatch at a moment of its choosing, and one that
    needs a person is not a check at all in this sense.
    """
    return [one for one in cheap(stated) if one not in (named or ())]


def lines(stated, named):
    """What a brief says about those guards. Empty when there are none."""
    found = guards(stated, named)
    if not found:
        return []
    return [PREAMBLE] + ["%s — %s" % (one, " ".join(stated[one])) for one in found]


def run(stated, chosen, runner, disagreed=None):
    """Run the chosen layers cheapest first. Returns `(layer, why)` or `("", "")`.

    Lifted from `execute.prove` unchanged in behaviour and changed in one thing
    only: the order. A layer that fails is run once more before it costs
    anything, because a check that fails and then passes over a tree nothing
    touched in between is evidence about the check rather than about the work —
    and charging for it threw away two hours of finished work that had never
    reached a judge. One re-run, not a configured number: a layer that needs
    three goes is broken in a way a knob would hide rather than fix.

    Every disagreement is appended to `disagreed`, because a flake nobody can
    see is a flake nobody fixes. The failing layer is returned beside the
    sentence so a caller can ask a second question about it — whether it was
    already red before this unit started, or who last committed the file it
    names — without parsing the sentence back apart.

    Whatever `runner` raises is the caller's: this module knows what to run and
    in what order, and nothing about how a command is allowed to run.
    """
    for layer in order(chosen):
        command = stated.get(layer)
        if not command:
            continue
        written = " ".join(command)
        code = runner(layer, list(command))
        if code == 0:
            continue
        if runner(layer, list(command)) != 0:
            return layer, "%s failed: %s exited %s" % (layer, written, code)
        if disagreed is not None:
            disagreed.append(
                "the %s layer exited %s and then passed on a second run of the "
                "same command over a tree nothing touched in between: %s — the "
                "check is not deterministic and the unit was not charged for it"
                % (layer, code, written))
    return "", ""
