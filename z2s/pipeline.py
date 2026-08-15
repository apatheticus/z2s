# -*- coding: utf-8 -*-
"""Every gate a change has to pass, in one run, reported honestly.

The individual gates already exist and each answers on its own. What was
missing is the run that puts them together and says plainly what happened —
because the failure this file exists to prevent is not a red build, it is a
green one:

  * A check that could not run is reported as **skipped, with its reason**, and
    is never folded into a pass count (FR-GEN-03, NFR-VAL-05). The rendered-view
    gate is the one that goes missing in practice: no browser on the machine and
    the check silently does not happen. A summary that then says "all gates
    passed" has told the reader something was proved when nothing was.
  * Generation and validation are **timed against a stated budget** (NFR-PRF-01,
    NFR-VAL-06). Ten seconds to build the set and five to check it (M9-02).
    Slow enough to survive a busy machine, tight enough that a real regression
    shows. A toolchain that takes minutes to regenerate is a toolchain people
    start hand-editing the output of, which is the failure this whole method is
    built to avoid.

The browser gate is deliberately outside the validation budget: it starts a
browser, and a budget that a machine with Playwright installed always fails is
a budget nobody keeps.

    python3 -m z2s.pipeline [--allow name,name] <document.html> ...

Traces: FR-GEN-03, FR-DOC-06, FR-VAL-01, FR-VAL-05, FR-VAL-07, NFR-PRF-01,
NFR-VAL-05, NFR-VAL-06, ADR-09, US-VAL-01, US-VAL-02.
"""

import collections
import os
import sys
import time

from z2s import chain, render, schema, shell, status, trace, validate

#: Seconds, from the M9 decision gate. Not configurable, for the same reason a
#: severity is not: a budget a project can raise when it starts failing is a
#: budget that only ever records what the code already does.
BUDGETS = collections.OrderedDict((("generation", 10.0), ("validation", 5.0)))

#: One run of one gate: what it found, how long it took, and whether it happened
#: at all. `ran` is a separate fact from the findings on purpose — a gate that
#: passes everything reports nothing, so an empty or skip-only finding list
#: cannot tell "there was nothing to say" from "this never happened".
Stage = collections.namedtuple("Stage", "name findings seconds ran")
Stage.__new__.__defaults__ = (True,)

PASSED, FAILED, SKIPPED = "passed", "failed", "skipped"

USAGE = ("usage: python3 -m z2s.pipeline [--allow name,name] [--record [root]] "
         "<document.html> [document.html ...]")

#: How a run leaves its evidence behind (M10-02). This whole command is one
#: check — the gate a change has to pass — so it records one layer, with the
#: exact command line and what came of it. A unit whose verification layers name
#: something else records that itself, through `z2s.status ran`.
RECORD = "--record"
RECORDED_LAYER = "CI"


def _timed(work):
    started = time.time()
    return work(), time.time() - started


def regenerate(sources, root="."):
    """Re-render every document from its own embedded specification (FR-DOC-06).

    This is the generation half of the timing, and a check in its own right: a
    document that cannot be rebuilt from what it carries is a document whose
    next update has to be typed into the markup by hand, which is the one thing
    ADR-02 forbids.

    The rendered text is measured and thrown away. Nothing is written, so a
    pipeline run never changes the files it is judging (NFR-DAT-05).
    """
    found = []
    for source in sources:
        try:
            with open(source, encoding="utf-8") as handle:
                spec = validate.extract(handle.read())
            # The element identifier only has to be well-formed here: the text
            # is measured and discarded, never written back over the original.
            rebuilt = chain.render(spec, "%s-spec" % spec["document"]["slug"], root)
            # A round trip rather than a render, so the timing is of real work
            # and the check has something to fail on: a document that rebuilds
            # into a different specification is not regenerable, it is lossy.
            if validate.extract(rebuilt) != spec:
                found.append(schema.Finding(
                    schema.FAILURE, "regeneration", source,
                    "%s rebuilds into a different specification than the one it "
                    "carries" % source))
        except (OSError, KeyError, TypeError, ValueError,
                validate.ExtractionError) as error:
            found.append(schema.Finding(
                schema.FAILURE, "regeneration", source,
                "%s cannot be rebuilt from its own specification: %s"
                % (source, error)))
    return found


def run(sources, allowed=(), root="."):
    """Every gate, in order. Returns the stages it ran."""
    stages = []

    findings, seconds = _timed(lambda: regenerate(sources, root))
    stages.append(Stage("generation", findings, seconds))

    grouped, checking = _timed(lambda: validate.validate_set(sources, allowed))
    stages.append(Stage("validation",
                        [one for found in grouped.values() for one in found],
                        checking))

    (coverage, _, _), covering = _timed(lambda: trace.gate(sources))
    stages.append(Stage("coverage", list(coverage), covering))

    view, viewing = _timed(lambda: render.check(sources))
    stages.append(Stage("view", view, viewing, render.ran(view)))

    stages.append(Stage("budgets", budgets(stages) + sizes(sources), 0.0))
    return stages


def sizes(sources):
    """Whether each document stayed inside its stated weight (NFR-PRF-02).

    `shell.budget_report` has existed since M1 and, until M14-05, nothing
    called it — so a project could ship a document of any size and hear nothing,
    which makes a stated budget a comment. Measured here rather than at the
    moment of writing, for the reason coverage is measured by the trace engine
    rather than by the plan generator (M8-06): one gate, one implementation, and
    it reaches a document however that document arrived.

    A warning rather than a failure. An oversized document is still the
    document, and the answer to it is to split the thing, which is work somebody
    has to plan — not a flag that stops the build in the meantime.
    """
    found = []
    for source in sources:
        try:
            with open(source, encoding="utf-8") as handle:
                text = handle.read()
        except (OSError, UnicodeDecodeError):
            continue                  # generation has already reported this file
        report = shell.budget_report(os.path.basename(source), text)
        if not report.within:
            found.append(schema.Finding(schema.WARNING, "budget", source,
                                        report.text))
    return found


def budgets(stages):
    """Whether the run stayed inside its stated time (M9-P2-T3).

    Validation is the checking half — every gate that reads the documents. The
    browser gate is excluded on purpose: it starts a browser, and a budget the
    presence of a development tool always breaks is a budget nobody keeps.
    """
    spent = {"generation": _seconds(stages, "generation"),
             "validation": _seconds(stages, "validation", "coverage")}
    found = []
    for name in BUDGETS:
        if spent[name] > BUDGETS[name]:
            found.append(schema.Finding(
                schema.FAILURE, "budget", name,
                "%s took %.1fs against a budget of %.1fs"
                % (name, spent[name], BUDGETS[name])))
    return found


def _seconds(stages, *names):
    return sum(one.seconds for one in stages if one.name in names)


def _skips(stage):
    return len([one for one in stage.findings
                if one.severity == schema.SKIPPED])


def state(stage):
    """What became of one gate.

    A gate that did not run is reported as skipped, and saying it passed would
    be the exact dishonesty NFR-VAL-05 forbids. What the gate FOUND does not
    decide that — a gate reports nothing when everything it drove was sound, so
    reading "no findings but skips" as "did not run" calls a check that really
    drove nine documents a check that never happened. Whether it ran is the
    gate's own answer, carried on the stage.

    A gate that ran and still could not exercise part of what it covers passes,
    and `format_report` names it as partly run — the skips are counted, printed
    and never folded into the finding count as though they were proved.
    """
    if any(one.severity == schema.FAILURE for one in stage.findings):
        return FAILED
    if not stage.ran:
        return SKIPPED
    return PASSED


def counts(stages):
    """Gates by outcome, and findings by severity, kept apart deliberately."""
    gates = collections.Counter(state(one) for one in stages)
    severities = collections.Counter(
        finding.severity for one in stages for finding in one.findings)
    return gates, severities


def exit_code(stages):
    """Non-zero on any failure. A skip never fails a build (LD-04)."""
    return 1 if any(state(one) == FAILED for one in stages) else 0


def format_report(stages):
    """The run, written for the person who has to act on it."""
    lines = []
    for stage in stages:
        for finding in stage.findings:
            lines.append("  %-7s %-14s %s"
                         % (finding.severity.upper(), finding.code, finding.message))

    lines.append("")
    for name in BUDGETS:
        spent = (_seconds(stages, "generation") if name == "generation"
                 else _seconds(stages, "validation", "coverage"))
        lines.append("%s: %.2fs of a %.1fs budget" % (name, spent, BUDGETS[name]))

    gates, severities = counts(stages)
    lines.append("gates: %d passed · %d failed · %d skipped"
                 % (gates[PASSED], gates[FAILED], gates[SKIPPED]))
    # Named individually so a skipped gate can never be read as a passed one.
    skipped = [one.name for one in stages if state(one) == SKIPPED]
    if skipped:
        lines.append("not run: %s — skipped, which is not passed"
                     % ", ".join(skipped))
    # And a gate that ran but could not exercise everything is named too. It
    # passed on what it drove; saying only "passed" would let the reader take
    # the skips inside it for proof.
    partly = ["%s (%d check%s skipped)"
              % (one.name, _skips(one), "" if _skips(one) == 1 else "s")
              for one in stages if state(one) == PASSED and _skips(one)]
    if partly:
        lines.append("partly run: %s — passed on what it drove, and the skipped "
                     "checks are not proved" % ", ".join(partly))
    lines.append("findings: %d failures · %d warnings · %d skipped"
                 % (severities[schema.FAILURE], severities[schema.WARNING],
                    severities[schema.SKIPPED]))
    return "\n".join(lines)


def recording(argv):
    """(arguments, project) with the record option taken out.

    The project defaults to here, so the common case is one word rather than a
    path somebody has to keep in step with where they are standing.
    """
    if RECORD not in argv:
        return list(argv), None
    rest = list(argv)
    at = rest.index(RECORD)
    rest.pop(at)
    if at < len(rest) and not rest[at].endswith(".html") \
            and not rest[at].startswith("-"):
        return rest[:at] + rest[at + 1:], rest[at]
    return rest, "."


def main(argv, out=sys.stdout):
    """The command. Its exit status is the answer (FR-VAL-05)."""
    argv, project = recording(argv)
    sources, allowed = validate.allowlist(argv)
    if not sources:
        out.write(USAGE + "\n")
        return 2
    stages = run(sources, allowed)
    out.write(format_report(stages) + "\n")
    code = exit_code(stages)
    if project is not None:
        # Written whether the gate passed or failed: a record saying the gate
        # went red is exactly what stops a unit claiming it is finished.
        status.record(project, RECORDED_LAYER,
                      "python3 -m z2s.pipeline " + " ".join(argv), code)
    return code


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
