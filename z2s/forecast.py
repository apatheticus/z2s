# -*- coding: utf-8 -*-
"""What a plan's declared write sets cost, before a build spends anything on it.

A run is bounded by four things, and only three of them are visible while the
plan is being written. The concurrency ceiling is in the settings. The wave
order is printed in the plan index. The dependency graph is drawn on every
milestone page. The fourth is the declared write sets, and nothing said a word
about them until the build was already running — by which time the plan is a
generated document nobody edits mid-run and the cost has already been spent.

It is not a small fourth. A 191-unit build measured on 2026-09-04 ran at a mean
of 1.05 concurrent workers against a ceiling of four, for 124 hours. Replayed
through this same scheduler, raising the ceiling to eight changed nothing and
disabling waves changed nothing; disabling the write-set check took it to 3.02.
One declaration did all of it — `tests/integration/**`, claimed by 180 of the
191 units, which makes every pair of them collide and the whole plan serial.

Nothing in the toolchain was wrong. `plan.py` refuses a task that names a test
layer and declares no test path, and it is right to: a short list is a unit run
beside another unit editing the same file. But nothing pushed the other way, so
an author who was unsure satisfied "leave nothing out" by claiming the whole
directory — always safe, always accepted, and sometimes the single largest thing
standing between a plan and its ceiling.

So this prints the number before it is spent:

    python3 -m z2s.forecast [--root DIR] [--ceiling N] [--top N]

It is a PREVIEW and never a gate. It exits 0 whatever it finds, like
`z2s.restyle --check`: a plan that genuinely has to run serially is a legitimate
plan, and a tool that refused it would be refusing on its own opinion about the
one case where the answer is not obvious. It writes nothing, reads no clock, and
dispatches nothing.

Everything it knows, it asks the orchestrator. `settings`, `units`, `order`,
`current`, `ready`, `dispatchable`, `collides`, `recall`, `writes` and `implied`
are imported, never restated — the same doctrine that makes every gate one
implementation wherever it is reached from. A forecast with its own copy of the
scheduler would drift from it, and a forecast that disagrees with the run is
worse than no forecast at all.

Traces: FR-EXE-06, FR-PLN-06, NFR-EXE-09, NFR-ARC-01, NFR-GEN-01, NFR-DAT-05.
"""

import sys

from z2s import execute, paths, schema, status

#: How many of the most-claimed paths are listed. The tail is long and dull: on
#: a real plan the top few are the answer, and everything under them is one unit
#: naming one file, which is what a narrow declaration looks like.
DEFAULT_TOP = 10

USAGE = "usage: python3 -m z2s.forecast [--root DIR] [--ceiling N] [--top N]"

#: What a project that has not been given workers yet is forecast against. A
#: plan is written before `.zero/workers.json` exists — that is the whole point
#: of running this before the build — so a missing settings file is the ordinary
#: case here, rather than the refusal it correctly is in `execute.settings`.
UNCONFIGURED = {"ceiling": execute.DEFAULT_CEILING,
                "attempts": execute.DEFAULT_ATTEMPTS,
                "families": [], "appendable": []}


def configured(root):
    """(settings, note). The project's own, or the defaults and why.

    A pair rather than a silent resolution, because the two are different
    forecasts: a project with families declared has a different collision map
    from one without, and a reader who is not told which they got cannot tell a
    plan that runs serially from a plan whose settings were never read.
    """
    try:
        return execute.settings(root), ""
    except execute.Refused as error:
        return dict(UNCONFIGURED), str(error)


def claims(found, config):
    """Every declared path, and which units declare it.

    The actionable half, and pure counting — no simulation. A path near the top
    of this map with most of the plan under it is the declaration to narrow, and
    knowing which one it is answers the question the mean only raises.

    `recall` runs first, so a path a unit inherits from one of the project's
    families counts against it here exactly as the scheduler will count it.
    """
    execute.recall(execute.blank(), found, config)
    held = {}
    for unit in found.values():
        declared = execute.writes(unit.entry) + execute.implied(unit.entry)
        for path in dict.fromkeys(declared):
            held.setdefault(path, []).append(unit.id)
    return held


def schedule(root, config, ceiling=None):
    """The rounds this plan can be dispatched in, as lists of unit identifiers.

    Reads its own units and never accepts them from a caller. The simulation
    marks each dispatched unit passing to make the next round move, and handing
    back a caller's live `found` mutated would poison whatever else was holding
    it — an orchestrator asking for a forecast mid-run would find its own plan
    finished.

    # ponytail: every unit costs one round and a round ends when all of its
    # units end, so this is a structural comparison and not a schedule. Upgrade
    # path: weight each unit by its recorded duration when a ledger has one.
    """
    found = execute.units(root)
    ledger = execute.blank()
    # Once, not once per round. `recall` puts the project's families on each
    # entry from what that entry declares, and nothing the simulation does
    # changes what a unit declares. The run calls it every iteration because a
    # real run has strays and operator corrections arriving between them; a
    # forecast has a blank ledger and neither.
    execute.recall(ledger, found, config)
    rounds = execute.order(root)
    ceiling = config["ceiling"] if ceiling is None else ceiling
    appendable = config.get("appendable") or ()

    played = []
    # Bounded by the unit count: every round that happens marks at least one
    # unit passing, and a round that picks nothing ends the loop.
    for _ in range(len(found)):
        wave = execute.current(rounds, found, ledger, config) if rounds else None
        candidates = execute.ready(found, ledger, config, wave)
        picked = execute.dispatchable(candidates, [], ceiling, appendable)
        if not picked:
            break
        for unit in picked:
            unit.entry["status"] = schema.PASSING
        played.append([unit.id for unit in picked])
    return played


def unscheduled(found, played):
    """The units no round ever picked up, each with the reason it was passed.

    A plan of two hundred units that forecasts eight rounds has either found a
    great deal of concurrency or quietly left most of the work out, and the mean
    on its own cannot tell those apart. This can.
    """
    ran = set(one for cycle in played for one in cycle)
    held = []
    for unit in found.values():
        if unit.id in ran:
            continue
        if execute.state(unit) == schema.PASSING:
            reason = "already passing"
        elif unit.entry.get("autonomy") == schema.HUMAN_GATE:
            reason = "at a human gate"
        elif execute.waiting(found, unit):
            reason = "waiting on %s" % ", ".join(execute.waiting(found, unit))
        else:
            reason = "in progress"
        held.append((unit.id, reason))
    return held


def report(root, config, top=DEFAULT_TOP, ceiling=None, note=""):
    """The whole forecast, as text a person reads. Returns it; writes nothing."""
    found = execute.units(root)
    if not found:
        return ("no plan documents in %s, so there is nothing to forecast. "
                "Run /zero:plan first."
                % paths.resolve(root, paths.PLAN_DIR))

    declared = claims(found, config)
    played = schedule(root, config, ceiling)
    left = unscheduled(found, played)
    reached = sum(len(one) for one in played)
    limit = config["ceiling"] if ceiling is None else ceiling

    lines = []
    if note:
        lines += ["%s, so this is forecast against the defaults: ceiling %d, no "
                  "families, no appendable paths." % (note, limit), ""]
    lines.append("%d units in the plan, %d of them still to dispatch."
                 % (len(found), reached))
    if not played:
        lines.append("Nothing is dispatchable, so there is no forecast to make.")
    else:
        lines.append("%d round%s at a ceiling of %d — a mean of %.2f units per "
                     "round." % (len(played), "" if len(played) == 1 else "s",
                                 limit, float(reached) / len(played)))
        lines.append("")
        lines.append("That mean is structural, not a duration: every unit costs "
                     "one round, and a")
        lines.append("round ends when all of its units end. It compares one plan "
                     "with another and")
        lines.append("with the ceiling. It is not a number of hours.")

    if left:
        counted = {}
        for _, reason in left:
            key = reason.split(" on ", 1)[0]
            counted[key] = counted.get(key, 0) + 1
        lines.append("")
        lines.append("Never dispatched: %s."
                     % ", ".join("%d %s" % (number, reason)
                                 for reason, number in sorted(counted.items())))

    if declared:
        ranked = sorted(declared.items(), key=lambda one: (-len(one[1]), one[0]))
        lines.append("")
        lines.append("Most-claimed paths:")
        for path, owners in ranked[:top]:
            lines.append("  %-44s declared by %d of %d units"
                         % (path, len(owners), len(found)))
        if len(ranked) > top:
            lines.append("  ... and %d more, each claimed by fewer units."
                         % (len(ranked) - top))
        # Said only when it is true. A plan whose widest claim is held by a
        # handful of units is a narrow plan, and telling its author to narrow it
        # is advice that teaches them to ignore the next one.
        if len(ranked[0][1]) > 1 and len(ranked[0][1]) * 2 >= len(found):
            lines.append("")
            lines.append("A path most of the plan claims makes most of the plan "
                         "collide. Naming the")
            lines.append("files a unit really writes, wherever they can be "
                         "named, is what moves the mean.")
    return "\n".join(lines)


def _number(argv, flag, out):
    """The whole number after `flag`, or None. Removes both from `argv`."""
    if flag not in argv:
        return None
    at = argv.index(flag)
    if at + 1 >= len(argv):
        out.write("%s needs a whole number\n" % flag)
        return None
    value = argv[at + 1]
    del argv[at:at + 2]
    try:
        held = int(value)
    except ValueError:
        out.write("%s must be a whole number, not %r\n" % (flag, value))
        return None
    return held if held >= 1 else None


def main(argv, out=sys.stdout):
    """The command. It is a preview, so its exit status is always 0 (LD-1).

    Everything else in this toolchain answers with its exit status, and this
    deliberately does not. A plan that has to run serially is still a plan, and
    a preview that failed a build over a number nobody has been shown before
    would be refusing on its own opinion.
    """
    argv = list(argv)
    root = "."
    if "--root" in argv:
        at = argv.index("--root")
        if at + 1 >= len(argv):
            out.write("--root needs a value\n%s\n" % USAGE)
            return 0
        root = argv[at + 1]
        del argv[at:at + 2]
    ceiling = _number(argv, "--ceiling", out)
    top = _number(argv, "--top", out) or DEFAULT_TOP

    if argv:
        out.write(USAGE + "\n")
        return 0

    config, note = configured(root)
    # Two modules raise a `Refused` of their own, and a plan document that will
    # not parse arrives as the status one, through `execute.units`. Both are
    # reported and neither is a failure: this is a preview.
    try:
        out.write(report(root, config, top=top, ceiling=ceiling, note=note) + "\n")
    except (execute.Refused, status.Refused) as error:
        out.write("%s\n" % error)
    return 0


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
