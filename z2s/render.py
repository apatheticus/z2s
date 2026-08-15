# -*- coding: utf-8 -*-
"""The rendered-view check: does the finished document work for a reader?

Everything else in this toolchain reads a document as data. A document can hold
a sound specification, satisfy every structural rule and still show a reader
nothing: a runtime that throws on the first section leaves a heading and an
empty page, and no amount of reading the embedded JSON says so (FR-VAL-07).

So this check opens each produced file in a real browser and drives the three
things a catalogue exists for — entries appear, the keyword box narrows them,
and switching a priority band off removes its entries.

Two rules govern how it reports:

  * **A skip is not a pass.** No browser, or no Playwright, and every finding
    here is `SKIPPED` with the reason attached. The check is optional in
    everyday integration and mandatory on promotion (LD-04, NFR-VAL-05); what
    is never allowed is a summary that counts an unavailable check as proved.
  * **The browser is a development tool.** Nothing it provides reaches a
    generated document, so the zero-runtime-dependency rule is untouched
    (NFR-ARC-03). The driver is `render.js` beside this file; a project with no
    node installed loses this check and nothing else.

Traces: FR-VAL-07, FR-GEN-03, NFR-VAL-05, NFR-VAL-06, NFR-ARC-03, ADR-09,
US-VAL-02.
"""

import json
import os
import shutil
import subprocess
import sys

from z2s import schema

DRIVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "render.js")

#: Playwright's own exit code for "not installed", chosen so a missing
#: development tool is distinguishable from a document that failed the check.
UNAVAILABLE = 3

#: Everything a catalogue has to prove it can still do (M9-P2-T1-C2). Named as
#: data so the check and the report cannot disagree about what was driven.
CONTROLS = ("entries", "filter", "band")

#: The one finding that means THIS CHECK NEVER RAN, as against the per-document
#: skips below it, which mean the check ran and one document had nothing to
#: exercise. Two different facts, and a summary that cannot tell them apart
#: reports a check that drove nine documents as a check that did not happen.
NOT_RUN = "render-skipped"

#: Long enough for a cold browser start over a full set, short enough that a
#: hung check fails rather than holding a pipeline open.
TIMEOUT = 180

USAGE = "usage: python3 -m z2s.render <document.html> [document.html ...]"


def available(node=None):
    """The node binary to drive with, or None with a reason.

    Returns (path, reason) so a caller never has to guess why a check was
    skipped — an unexplained skip is the failure mode this check exists to
    avoid.
    """
    found = node or shutil.which("node")
    if found is None or shutil.which(found) is None:
        return None, "node is not installed"
    if not os.path.exists(DRIVER):
        return None, "the browser driver is missing: %s" % DRIVER
    return found, None


def drive(sources, node=None):
    """Open every document in a browser. Returns (reports, reason).

    `reason` is set when the check could not run at all, in which case the
    reports are empty. Anything the browser did report is returned as it came
    back, so the judging below is the only place a rule lives.
    """
    found, reason = available(node)
    if found is None:
        return [], reason

    pages, order = {}, []
    for source in sources:
        try:
            with open(source, encoding="utf-8") as handle:
                pages[os.path.basename(source)] = handle.read()
        except OSError as error:
            return [], "%s could not be read: %s" % (source, error)
        order.append(os.path.basename(source))

    request = json.dumps({"pages": pages, "documents": order})
    try:
        finished = subprocess.run([found, DRIVER], input=request, timeout=TIMEOUT,
                                  capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return [], "the browser did not finish within %d seconds" % TIMEOUT

    if finished.returncode == UNAVAILABLE:
        return [], finished.stderr.strip() or "no browser is installed"
    if finished.returncode != 0:
        # A driver that fell over is a failure of this check, not a skip: the
        # tool was there and something went wrong while it was running.
        raise RuntimeError(finished.stderr.strip() or "the browser driver failed")
    return json.loads(finished.stdout)["documents"], None


def check(sources, node=None):
    """Every finding the rendered view produces, skips included."""
    try:
        reports, reason = drive(sources, node)
    except RuntimeError as error:
        return [schema.Finding(schema.FAILURE, "render-driver", "the browser",
                               str(error))]
    if reason is not None:
        return [schema.Finding(
            schema.SKIPPED, NOT_RUN, "every document",
            "the rendered view was not checked: %s. It proves nothing about "
            "these documents either way" % reason)]

    found = []
    for report in reports:
        found.extend(judge(report))
    return found


def ran(found):
    """Whether the browser actually drove anything.

    A document that renders and drives cleanly produces no finding at all, so
    "nothing but skips" is not evidence that nothing ran — it is what a set of
    catalogue-less documents looks like after a real run. Only the whole-set
    skip says the check itself did not happen.
    """
    return not any(one.code == NOT_RUN for one in found)


def judge(report):
    """What one document's browser run says, as findings."""
    name = report.get("name") or "a document"
    found = []

    for message in report.get("errors") or ():
        found.append(schema.Finding(
            schema.FAILURE, "render-error", name,
            "%s threw while rendering: %s" % (name, message)))

    if not report.get("sections"):
        found.append(schema.Finding(
            schema.FAILURE, "render-empty", name,
            "%s renders no sections at all; whatever its specification says, a "
            "reader opening it sees an empty page" % name))
        return found

    entries = report.get("entries") or 0
    if not entries:
        # Said out loud rather than passed over. Most documents genuinely have
        # no catalogue — but so does a document whose catalogue stopped
        # rendering, and a check that goes quiet in both cases is the exact
        # dishonesty NFR-VAL-05 forbids.
        found.append(schema.Finding(
            schema.SKIPPED, "render-view", name,
            "%s renders %d sections and no catalogue, so the filter and the "
            "priority bands were not exercised here"
            % (name, report.get("sections") or 0)))
        return found

    exercised = report.get("exercised") or ()
    if "band" not in exercised and not report.get("band"):
        # Honest rather than silent: a catalogue whose entries carry no priority
        # band — a set of decisions, say — leaves the band check unrun, and an
        # unrun check is never a pass (NFR-VAL-05).
        found.append(schema.Finding(
            schema.SKIPPED, "render-band", name,
            "%s has no priority bands to switch off, so that half of the "
            "catalogue was not exercised here" % name))
    missing = [one for one in CONTROLS if one not in exercised
               and not (one == "band" and not report.get("band"))]
    if missing:
        found.append(schema.Finding(
            schema.FAILURE, "render-control", name,
            "%s offers no working %s; a catalogue a reader cannot narrow is a "
            "list" % (name, " or ".join(missing))))
        return found

    filtered = report.get("filtered")
    if not filtered:
        found.append(schema.Finding(
            schema.FAILURE, "render-filter", name,
            "%s hides every entry when its own identifier is typed into the "
            "filter" % name))
    elif entries > 1 and filtered >= entries:
        found.append(schema.Finding(
            schema.FAILURE, "render-filter", name,
            "%s shows the same %d entries whatever is typed into the filter"
            % (name, entries)))

    toggled = report.get("toggled")
    if not report.get("band"):
        return found
    if toggled is None or toggled >= entries:
        found.append(schema.Finding(
            schema.FAILURE, "render-band", name,
            "%s keeps showing %s entries after the %s band is switched off"
            % (name, entries, report.get("band") or "first")))
    return found


def format_report(found):
    """The same findings, written for a person."""
    lines = ["  %-7s %-14s %s" % (one.severity.upper(), one.code, one.message)
             for one in found]
    failures = len([one for one in found if one.severity == schema.FAILURE])
    skipped = len([one for one in found if one.severity == schema.SKIPPED])
    if not failures and not skipped:
        lines.append("OK: every document renders and its catalogue can be driven")
    lines.append("%d failure%s, %d skipped check%s"
                 % (failures, "" if failures == 1 else "s",
                    skipped, "" if skipped == 1 else "s"))
    return "\n".join(lines)


def main(argv, out=sys.stdout):
    """The command. A skipped run exits zero and says so (LD-04)."""
    if not argv:
        out.write(USAGE + "\n")
        return 2
    found = check(argv)
    out.write(format_report(found) + "\n")
    return 1 if any(one.severity == schema.FAILURE for one in found) else 0


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
