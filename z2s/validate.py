# -*- coding: utf-8 -*-
"""The schema validator: check a set of finished documents in one run.

Wired straight into a continuous-integration gate, so the exit status is the
answer and the printed report is for the person who has to fix it (FR-VAL-05).

Three properties this file exists to keep:

  * **Exhaustive.** Every violation in the set is reported in one run, grouped
    by document (NFR-VAL-01). A validator that stops at the first failure makes
    a reader fix one field, run again, and find the next; after the third round
    they stop running it.
  * **Set-wide.** Whether an identifier is duplicated, and whether a trace leads
    anywhere, are questions no single document can answer. One index is built
    across the whole set and exposed, so later tools reuse it rather than
    building a second one that disagrees.
  * **Honest.** A warning never fails a build and a failure never passes as a
    warning (FR-VAL-06). Severity is a property of the rule; there is no flag,
    no environment variable and no argument that moves a finding between the
    two, because a red build that can be made green without a fix is worse than
    no check at all.

Extraction lives here and only here (FR-SPC-04). A second parser elsewhere is a
second definition of what a document is.

The secret scan is delegated rather than repeated: `safety.secrets_in` reads the
file's text, and this file calls it once per source so that the check a project
already runs in continuous integration is the check that catches a leak (M6-07).

The plan document gets a second set of checks of its own (M9-P1-T2). It is the
one document in the set that is written back to, so what it says about a task's
status has to be checked in the finished file rather than trusted from the run
that produced it. Those checks read the document; they never import the plan
generator, which is the whole point of validating the artefact (ADR-09).

Traces: FR-GEN-04, FR-SPC-04, FR-TRC-02, FR-TRC-08, FR-VAL-01, FR-VAL-03,
FR-VAL-04, FR-VAL-05, FR-VAL-06, FR-VAL-08, NFR-DAT-02, NFR-SEC-01, NFR-VAL-01,
NFR-VAL-04, NFR-VAL-05, NFR-VAL-06, ADR-03, ADR-09.
"""

import collections
import json
import os
import re
import sys

from z2s import safety
from z2s import schema

#: The embedding element, found by its type rather than its identifier: the
#: identifier is type-specific by contract (NFR-DAT-01), so keying off it would
#: mean this file holding a list of every document type that will ever exist.
BLOCK = re.compile(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
                   re.DOTALL)

USAGE = ("usage: python3 -m z2s.validate [--allow name,name] <document.html> "
         "[document.html ...]")

#: How a project silences a term the plain-language rule flags. Every project
#: has words of its own that a reader of *that* project follows perfectly well,
#: and a rule with no way to say so is a rule that gets switched off entirely.
ALLOW = "--allow"


class ExtractionError(Exception):
    """A document's embedded specification is missing or unreadable."""


def extract(html):
    """The embedded specification object, or a named failure.

    A truncated or absent block is an ordinary result of pointing this at the
    wrong file, so it is reported in words rather than as a stack trace.
    """
    match = BLOCK.search(html)
    if match is None:
        raise ExtractionError("no embedded specification in this document")
    try:
        # "</" is written as "<\/" when embedding, so the specification cannot
        # end its own script element. "\/" is a standard JSON escape, so the
        # parser undoes it here with no help and no loss.
        return json.loads(match.group(1))
    except ValueError as error:
        raise ExtractionError("the embedded specification could not be parsed: %s"
                              % error)


def validate_document(spec, source, allowed=()):
    """Every check one document can answer on its own."""
    version = spec.get("schemaVersion") if isinstance(spec, dict) else None
    found = [] if schema.is_empty(version) else schema.check_version(version, source)
    if _refused(found):
        # FR-VAL-01: checking a document this tool does not understand produces
        # findings about a contract that may not even apply to it.
        return found

    found.extend(schema.check_document(spec))
    found.extend(schema.check_identifiers(spec))
    found.extend(schema.check_enumerations(spec))
    found.extend(schema.check_traces(spec))
    found.extend(schema.check_boundary(spec))
    found.extend(schema.check_plain_language(spec, allowed))
    found.extend(schema.check_emptiness(spec))
    return found


def build_index(specs):
    """Every identifier in the set, and everywhere it is declared.

    Exposed deliberately: the traceability matrix and the coverage gate need the
    same index, and rebuilding it in each tool is where the three drift apart.
    """
    index = collections.OrderedDict()
    for source in specs:
        for path, entry in schema.entries(specs[source]):
            identifier = entry.get("id")
            if schema.kind_of(identifier) is None:
                continue
            index.setdefault(identifier, []).append((source, path))
    return index


def declared_areas(specs, index):
    """Every group an entry is allowed to belong to.

    A catalogue declares its areas in a legend beside its entries, and those
    carry `key` rather than `id`; a catalogue that groups entries structurally
    declares them as group identifiers instead. Both are declarations, and
    looking only for the second made every requirement in a real document name
    a missing area.

    Areas are kept out of the identifier index deliberately: the same area is
    declared in more than one document by design, and counting that as a
    duplicate identifier would be wrong.
    """
    areas = set(index)
    for source in specs:
        for path, entry in schema.entries(specs[source]):
            key = entry.get("key")
            if ".areas[" in path and isinstance(key, str) and key:
                areas.add(key)
    return areas


def check_duplicates(index):
    """No identifier is declared twice anywhere in the set (FR-TRC-02, ADR-03).

    Reported against the later declaration, naming both, because a reader needs
    to see the collision from either end.
    """
    found = []
    for identifier in index:
        places = index[identifier]
        if len(places) < 2:
            continue
        where = ", ".join("%s (%s)" % (source, path) for source, path in places)
        found.append((places[-1][0],
                      schema.Finding(schema.FAILURE, "duplicate-identifier", identifier,
                                     "%s is declared %d times: %s"
                                     % (identifier, len(places), where))))
    return found


def check_references(specs, index, areas):
    """Traces and areas point at identifiers that exist (FR-TRC-08, FR-VAL-03)."""
    found = []
    for source in specs:
        for path, entry in schema.entries(specs[source]):
            owner = entry.get("id") if schema.kind_of(entry.get("id")) else path

            area = entry.get("area")
            if isinstance(area, str) and area and area not in areas:
                found.append((source, schema.Finding(
                    schema.FAILURE, "unknown-area", owner,
                    "%s names area %s, which is declared nowhere in the set"
                    % (owner, area))))

            traces = entry.get("traces")
            if not isinstance(traces, dict):
                continue
            for kind in sorted(traces):
                value = traces[kind]
                if not isinstance(value, list):
                    continue
                for target in value:
                    if isinstance(target, str) and target not in index:
                        found.append((source, schema.Finding(
                            schema.FAILURE, "dangling-trace", owner,
                            "%s traces to %s, which is defined in no document in the set"
                            % (owner, target))))
    return found


# --------------------------------------------------- the finished plan document

#: A plan document says so in its own envelope, so recognising one costs no
#: knowledge of the generator that wrote it (ADR-09).
PLAN_SLUG = "plan"


def plan_specs(specs):
    """The plan documents in this run, keyed by the file each was read from."""
    found = collections.OrderedDict()
    for source in specs:
        document = specs[source].get("document")
        if isinstance(document, dict) and document.get("slug") == PLAN_SLUG:
            found[source] = specs[source]
    return found


def plan_units(specs):
    """Every unit of work the plan documents in this run define.

    A milestone names itself in its document's envelope, a phase is the key of
    the group its tasks sit in, and a task is an entry. All three are units one
    piece of work can be made to wait on, so all three are collected together.
    """
    units = set()
    for spec in specs.values():
        milestone = (spec.get("document") or {}).get("milestone")
        if schema.plan_level(milestone) == "milestone":
            units.add(milestone)
        for _, entry in schema.entries(spec):
            for name in ("id", "key"):
                value = entry.get(name)
                if schema.plan_level(value) in ("milestone", "phase", "task"):
                    units.add(value)
    return units


def check_plan(specs, sources=()):
    """The invariants that make a finished plan trustworthy (FR-VAL-04).

    Read from the rendered plan rather than from the data behind it, because the
    plan is the one document in the set that is written back to: a status the
    document does not carry is a status nobody can act on, whatever the generator
    believed when it ran.
    """
    found = []
    plans = plan_specs(specs)
    if not plans:
        return found
    units = plan_units(plans)
    held = set(unit for unit in units if schema.plan_level(unit) == "milestone")
    for source in plans:
        found.extend(_check_tasks(source, plans[source]))
        found.extend(_check_waiting(source, plans[source], units, held))
        found.extend(_check_details(source, plans[source]))
    return found


def _check_tasks(source, spec):
    """A task states its status, what it is judged by, and what it claims."""
    found = []
    catalogue = spec.get("catalog") if isinstance(spec.get("catalog"), dict) else {}
    for path, task in schema.entries(spec):
        if schema.plan_level(task.get("id")) != "task":
            continue
        unit = task["id"]

        if schema.is_empty(task.get("status")):
            found.append((source, schema.Finding(
                schema.FAILURE, "plan-status", unit,
                "%s carries no status; a task the plan cannot say the state of is a "
                "task nothing can be scheduled behind" % unit)))

        if not [one for one in task.get("criteria") or () if isinstance(one, dict)]:
            found.append((source, schema.Finding(
                schema.FAILURE, "plan-criteria", unit,
                "%s carries no acceptance criteria; nothing in the document decides "
                "when it is done" % unit)))

        # The plan's catalogue is the list of everything it is allowed to claim,
        # written into the document when it was generated. A claim outside it is
        # a claim on something this plan was never shown.
        if catalogue:
            traces = task.get("traces") if isinstance(task.get("traces"), dict) else {}
            for kind in sorted(traces):
                for target in traces[kind] if isinstance(traces[kind], list) else ():
                    if isinstance(target, str) and target not in catalogue:
                        found.append((source, schema.Finding(
                            schema.FAILURE, "plan-claim", unit,
                            "%s claims %s, which this plan's catalogue does not list"
                            % (unit, target))))

        # A task that names a verification layer writes tests, and a writes list
        # covering everything except those is read two ways at once: the brief
        # forbids the worker the tests its own criteria need, and the
        # orchestrator computes two units sharing a test directory as safe to
        # run side by side. A WARNING rather than a failure, deliberately — this
        # check runs inside the default gauntlet over a project's own plan, so
        # failing here would turn one generator defect into every unit blocked,
        # including the units that are fine. The generator refuses to write it in
        # the first place; this is what says so about a plan already on disk.
        # Only a partial list is caught: declaring nothing is honest silence and
        # still collides with everything (M11-04).
        declared = [one for one in task.get("writes") or ()
                    if not schema.is_empty(one)]
        if (task.get("testLayers") and declared
                and not any(schema.names_a_test(one) for one in declared)
                and not _excused(task, "writes")):
            found.append((source, schema.Finding(
                schema.WARNING, "plan-writes-tests", unit,
                "%s runs %s and declares no test path among the files it writes, so "
                "its brief forbids the tests its criteria need and any unit sharing "
                "that test directory is read as safe to run beside it"
                % (unit, ", ".join(str(one) for one in task["testLayers"])))))

        found.extend(_check_exceptions(source, unit, task))
    return found


def _excused(task, rule):
    """Whether this task carries a written exception to one rule.

    Spelled here as well as in the generator because the validator imports no
    generator (ADR-09). Both read `schema.EXCUSABLE_RULES`, which is the half
    that must not come to differ.
    """
    for one in task.get("exceptions") or ():
        if (isinstance(one, dict) and one.get("rule") == rule
                and not schema.is_empty(one.get("reason"))):
            return one
    return None


def _check_exceptions(source, unit, task):
    """Declared exceptions, reported on every run (FR-VAL-08, NFR-VAL-04).

    An exception is a decision somebody made, not a hole somebody left — so it
    is a warning rather than a failure. It is stated on every run for one reason:
    an exception granted once and then never mentioned again stops being a
    decision and becomes the way things are.

    The set of rules an exception may name is a constant in `schema`, so no
    argument, environment variable or project setting widens it (M9-P1-T3-C2).
    """
    found = []
    for one in task.get("exceptions") or ():
        if not isinstance(one, dict):
            continue
        rule = one.get("rule")
        if rule not in schema.EXCUSABLE_RULES:
            found.append((source, schema.Finding(
                schema.FAILURE, "plan-exception", unit,
                "%s claims an exception to %r; the only rules a unit of work may be "
                "excused from are %s"
                % (unit, rule, ", ".join(schema.EXCUSABLE_RULES)))))
        elif schema.is_empty(one.get("reason")):
            found.append((source, schema.Finding(
                schema.FAILURE, "plan-exception", unit,
                "%s claims an exception to %s and gives no reason; an exception "
                "nobody wrote a reason for cannot be reviewed" % (unit, rule))))
        else:
            found.append((source, schema.Finding(
                schema.WARNING, "plan-exception", unit,
                "%s is excused the %s rule: %s" % (unit, rule, one["reason"]))))
    return found


def _check_waiting(source, spec, units, held):
    """Nothing waits on a unit of work no document in this run defines.

    Judged only where this run holds the milestone the dependency belongs to. A
    plan is one document split across files, and a milestone document read on
    its own genuinely cannot see the task in the milestone before it.
    """
    found = []
    for path, entry in schema.entries(spec):
        for target in entry.get("dependsOn") or ():
            if not isinstance(target, str) or target in units:
                continue
            if target.split("-")[0] not in held:
                continue
            waiting = entry.get("id") or path
            found.append((source, schema.Finding(
                schema.FAILURE, "plan-dependency", waiting,
                "%s waits for %s, which no plan document in this run defines"
                % (waiting, target))))
    return found


def _check_details(source, spec):
    """Every milestone the index schedules has its detail document beside it.

    Only asked of a plan that is split across files. A plan small enough to be
    one document schedules nothing outside itself, and there is no second file
    for a milestone to be missing from.
    """
    found = []
    directory = os.path.dirname(os.path.abspath(source))
    for section in spec.get("sections") or ():
        if not isinstance(section, dict) or section.get("type") != "waves":
            continue
        files = section.get("files") if isinstance(section.get("files"), dict) else {}
        if not files:
            continue
        for wave in section.get("waves") or ():
            for unit in wave or ():
                filename = files.get(unit)
                if schema.is_empty(filename):
                    found.append((source, schema.Finding(
                        schema.FAILURE, "plan-detail", unit,
                        "%s is scheduled and names no detail document; the plan "
                        "schedules work nobody can read" % unit)))
                elif not os.path.exists(os.path.join(directory, filename)):
                    found.append((source, schema.Finding(
                        schema.FAILURE, "plan-detail", unit,
                        "%s names %s as its detail document, and no such file sits "
                        "beside this one" % (unit, filename))))
    return found


def allowlist(argv):
    """The arguments, split into what to check and what to leave alone.

    Repeatable and comma-separated both, because a caller writing the flag out
    by hand and a caller building it from a project's configuration reach for
    different shapes of the same list.
    """
    sources, allowed, index = [], [], 0
    while index < len(argv):
        argument = argv[index]
        if argument == ALLOW and index + 1 < len(argv):
            allowed.extend(name.strip() for name in argv[index + 1].split(",")
                           if name.strip())
            index += 2
        elif argument.startswith(ALLOW + "="):
            allowed.extend(name.strip() for name in
                           argument[len(ALLOW) + 1:].split(",") if name.strip())
            index += 1
        else:
            sources.append(argument)
            index += 1
    return sources, allowed


def published_names(sources):
    """Every filename the set publishes under.

    A document naming its sibling is a cross-reference, not jargon: the reader
    is holding the set, and the filename is how they reach the next document.
    Derived from the run rather than configured, so a project that adds an
    eleventh document gets the same answer with no list to keep in step.

    Deliberately a property of the SET. One document checked on its own knows
    of no siblings, and saying so is honest — nothing there tells a reader
    where that name leads.
    """
    return [os.path.basename(source) for source in sources
            if os.path.basename(source)]


def validate_set(sources, allowed=()):
    """Validate every document, then everything only the set can answer.

    Returns an ordered map of source to findings — the collection, with no
    formatting in it, so the same results can be printed or returned.
    """
    grouped = collections.OrderedDict()
    specs = collections.OrderedDict()
    allowed = list(allowed) + published_names(sources)

    for source in sources:
        grouped[source] = []
        try:
            with open(source, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as error:
            grouped[source].append(schema.Finding(
                schema.FAILURE, "unreadable", source, "%s: %s" % (source, error)))
            continue

        # The secret scan reads the file, not the specification embedded in it
        # (M6-07): a credential pasted into a heading, a script or an attribute
        # is in the artefact whether or not the schema ever sees it.
        grouped[source].extend(safety.secrets_in(text, source))

        try:
            spec = extract(text)
        except ExtractionError as error:
            grouped[source].append(schema.Finding(
                schema.FAILURE, "unreadable", source, "%s: %s" % (source, error)))
            continue

        found = validate_document(spec, source, allowed)
        grouped[source].extend(found)
        if not _refused(found):
            specs[source] = spec

    index = build_index(specs)
    areas = declared_areas(specs, index)
    for source, finding in (check_duplicates(index)
                            + check_references(specs, index, areas)
                            + check_plan(specs, sources)):
        grouped[source].append(finding)
    return grouped


def counts(grouped):
    """How many of each severity the run produced."""
    tally = collections.Counter()
    for found in grouped.values():
        for finding in found:
            tally[finding.severity] += 1
    return tally


def exit_code(grouped):
    """Non-zero when any failure exists; warnings alone never fail a build."""
    return 1 if counts(grouped)[schema.FAILURE] else 0


def format_report(grouped):
    """The same results, written for a person."""
    lines = []
    for source in grouped:
        found = grouped[source]
        if not found:
            continue
        lines.append(source)
        for finding in found:
            lines.append("  %-7s %-20s %s"
                         % (finding.severity.upper(), finding.code, finding.message))
        lines.append("")

    tally = counts(grouped)
    if not tally[schema.FAILURE]:
        lines.append("OK: %s satisfy their schema" % _plural(len(grouped), "document"))
    summary = "%s, %s" % (_plural(tally[schema.FAILURE], "failure"),
                          _plural(tally[schema.WARNING], "warning"))
    # Named only when there is one: a skipped check is never silent (NFR-VAL-05),
    # and a run with nothing skipped should not carry a zero that reads as one.
    if tally[schema.SKIPPED]:
        summary += ", %s" % _plural(tally[schema.SKIPPED], "skipped check")
    lines.append(summary)
    return "\n".join(lines)


def main(argv, out=sys.stdout):
    """The command. Its exit status is the answer (FR-VAL-05)."""
    sources, allowed = allowlist(argv)
    if not sources:
        out.write(USAGE + "\n")
        return 2
    grouped = validate_set(sources, allowed)
    out.write(format_report(grouped) + "\n")
    return exit_code(grouped)


def _refused(found):
    return any(finding.code == "schema-version" and finding.severity == schema.FAILURE
               for finding in found)


def _plural(count, noun):
    return "%d %s%s" % (count, noun, "" if count == 1 else "s")


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
