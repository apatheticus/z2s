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

Traces: FR-SPC-04, FR-TRC-02, FR-TRC-08, FR-VAL-01, FR-VAL-03, FR-VAL-05,
FR-VAL-06, NFR-DAT-02, NFR-VAL-01, NFR-VAL-06, ADR-03.
"""

import collections
import json
import re
import sys

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


def validate_set(sources, allowed=()):
    """Validate every document, then everything only the set can answer.

    Returns an ordered map of source to findings — the collection, with no
    formatting in it, so the same results can be printed or returned.
    """
    grouped = collections.OrderedDict()
    specs = collections.OrderedDict()

    for source in sources:
        grouped[source] = []
        try:
            with open(source, encoding="utf-8") as handle:
                spec = extract(handle.read())
        except (OSError, ExtractionError) as error:
            grouped[source].append(schema.Finding(
                schema.FAILURE, "unreadable", source, "%s: %s" % (source, error)))
            continue

        found = validate_document(spec, source, allowed)
        grouped[source].extend(found)
        if not _refused(found):
            specs[source] = spec

    index = build_index(specs)
    areas = declared_areas(specs, index)
    for source, finding in check_duplicates(index) + check_references(specs, index, areas):
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
    lines.append("%s, %s" % (_plural(tally[schema.FAILURE], "failure"),
                             _plural(tally[schema.WARNING], "warning")))
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
