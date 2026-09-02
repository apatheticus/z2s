# -*- coding: utf-8 -*-
"""The trace universe: what exists, who owns it, and who has claimed it.

Every other tool in this method asks one of three questions about a set of
documents, and all three are answered here so that all three agree:

  * **What exists?** Every identifier the set defines, built by reading the
    documents themselves (FR-TRC-03). There is no maintained list of
    requirements anywhere, because a maintained list is a second answer to a
    question the documents already answer, and the two diverge on the day
    somebody adds a requirement in a hurry (ADR-04).
  * **Who owns it?** Which document defines which namespace, so a trace shown
    to a reader is a working link to the thing it names (FR-TRC-07). The map is
    derived from what each document actually declares rather than configured,
    so an addendum published tomorrow routes correctly with nothing to update
    (ADR-12).
  * **Who has claimed it?** Which unit of work is going to build it, and
    therefore what nobody is going to build (FR-TRC-04, FR-TRC-05).

Nothing computed here is ever written into an authored document (NFR-DAT-05).
Coverage is a fact about a set at a moment; stored, it becomes a claim that can
disagree with the documents it came from.

Four things this file decides, once, so nothing else has to:

  * **A namespace is the area code, not the kind** (M7-01). `FR-DOC` is owned;
    `FR` is not. An addendum whose entire purpose is new requirements would
    otherwise have to invent a new kind of identifier to say anything at all.
  * **The universe is requirements and decisions** (M7-02) — `FR`, `NFR`, `ADR`.
    A target, a measure and a risk are how you check scope, not scope.
  * **Two doors out, two words** (M7-03). An entry priced `Won't` with a reason
    is *excluded*: real, deliberately not built this release. An entry carrying
    a `retired` reason is *retired*: no longer scope at all, its number reserved
    for the life of the project (FR-TRC-02, ADR-03).
  * **A plan identifier is not routed.** A plan is one logical document split
    across files by design, so `M7` has no single owner and never appears as a
    trace target. Routing it would report a collision that is really a layout.

An absent document is reported and skipped, never fatal and never silent
(FR-AMD-03, NFR-VAL-05): the run says how many documents it actually read, so a
gate that passed over half a set cannot read as a gate that passed.

Traces: FR-AMD-02, FR-AMD-03, FR-GEN-03, FR-TRC-02, FR-TRC-03, FR-TRC-04,
FR-TRC-05, FR-TRC-06, FR-TRC-07, NFR-DAT-05, NFR-EVO-03, NFR-VAL-03,
NFR-VAL-05, ADR-03, ADR-04, ADR-12.
"""

import collections
import os
import re
import sys

from z2s import schema, validate

USAGE = ("usage: python3 -m z2s.trace <document.html> [document.html ...]\n"
         "       every requirement and decision must be claimed by a unit of work")

#: The kinds that must be claimed by a unit of work (M7-02). Named by kind
#: rather than by prefix so a project that registers its own requirement prefix
#: joins the universe by saying so once, in the grammar.
COUNTED = ("requirement", "decision")

#: The priority band that records a decision not to build (FR-TRC-06). The same
#: constant the functional-specification generator writes; spelled here rather
#: than imported so the reader of a set does not depend on the writer of one.
EXCLUDED = "Won't"

#: Where an exclusion's reason lives. A `Won't` entry is a decision, and a
#: decision with no argument is the one that gets re-argued.
REASON = "notes"

#: The field that retires an identifier in place. Its value is the reason.
RETIRED = "retired"

#: The field that takes a milestone out of the current release. Its value is the
#: reason (M7-05). Deferral is a property of the claiming milestone, never a
#: configuration of the gate — a gate with a setting that turns a failure into a
#: warning is a gate somebody switches off (NFR-VAL-03).
DEFERRED = "deferred"

#: An area code: two to four capitals, the second segment of `FR-DOC-01`. A
#: numeric second segment (`ADR-04`) means the kind itself is the namespace.
_AREA = re.compile(r"^[A-Z]{2,4}$")

Definition = collections.namedtuple("Definition", "source path entry")
Item = collections.namedtuple("Item", "id kind title source state reason")
Row = collections.namedtuple("Row", "id kind title source state claimants deferred")

#: What a row's state can be. Ordered as a reader reads them: the two that fail,
#: then the one that warns, then the three that pass.
UNCOVERED, CLAIMED, DEFERRED_ONLY = "uncovered", "claimed", "deferred"
STATES = (UNCOVERED, DEFERRED_ONLY, CLAIMED, "excluded", "retired")


def namespace(identifier):
    """The namespace that owns an identifier (M7-01).

    `FR-DOC-01` and `US-DOC-01-S01` belong to `FR-DOC` and `US-DOC`; `ADR-04`
    and `TG-01` belong to `ADR` and `TG`. Two segments where the second is an
    area code, one segment otherwise — the same rule the document runtime
    applies when it turns a trace into a link, so a link and a collision report
    can never disagree about who owns what.
    """
    parts = str(identifier or "").split("-")
    if len(parts) > 1 and _AREA.match(parts[1]):
        return "-".join(parts[:2])
    return parts[0]


# ------------------------------------------------------------------- reading

def read(sources):
    """Every document that could be read, and a finding for every one that could not.

    One guarded read for every input, required or optional alike (FR-AMD-03).
    An absent document is a warning: generation continues and produces the core
    output, and the absence is stated rather than inferred from a smaller number
    (NFR-VAL-05). A document that exists but carries no readable specification
    is a failure — that is a corrupted artefact, not an optional one.
    """
    specs, findings = collections.OrderedDict(), []
    for source in sources:
        try:
            with open(source, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as error:
            findings.append(schema.Finding(
                schema.WARNING, "skipped", source,
                "%s: skipped, not read (%s); nothing it defines is in the universe "
                "and nothing it claims is counted" % (source, error)))
            continue
        try:
            specs[source] = validate.extract(text)
        except validate.ExtractionError as error:
            findings.append(schema.Finding(
                schema.FAILURE, "unreadable", source, "%s: %s" % (source, error)))
    return specs, findings


def defines(specs):
    """Every identifier the set declares, and everywhere it is declared.

    Built by extraction on every run and cached nowhere beyond it (M7-P1-T1):
    adding a requirement to a document is the whole of adding it to the
    universe. A list of identifiers kept anywhere else would be a second
    definition of scope, and the second one is always the stale one.
    """
    index = collections.OrderedDict()
    for source in specs:
        for path, entry in schema.entries(specs[source]):
            identifier = entry.get("id")
            if not isinstance(identifier, str) or schema.kind_of(identifier) is None:
                continue
            index.setdefault(identifier, []).append(Definition(source, path, entry))
    return index


# ------------------------------------------------------------------- routing

def owners(specs):
    """Which document owns which namespace, and every namespace with two owners.

    Derived from what the documents declare, not configured (ADR-12): a project
    that adds an addendum gets correct links with nothing to maintain, and one
    that renames a file gets them back on the next run.

    Two owners fails, naming both documents and the namespace (FR-AMD-02,
    NFR-EVO-03, LD-02). The alternative is resolving by precedence, which means
    a trace that silently opens the wrong document — worse than one that does
    not open at all, because the reader has no way to tell.
    """
    routes, findings, seen, reported = collections.OrderedDict(), [], {}, set()
    for source in specs:
        for path, entry in schema.entries(specs[source]):
            identifier = entry.get("id")
            kind = schema.kind_of(identifier) if isinstance(identifier, str) else None
            if kind is None or kind == "plan":
                continue
            space = namespace(identifier)
            held = seen.get(space)
            if held is None:
                seen[space] = source
                routes[space] = os.path.basename(source)
            elif held != source and (space, source) not in reported:
                reported.add((space, source))
                findings.append(schema.Finding(
                    schema.FAILURE, "prefix-collision", space,
                    "the namespace %s is declared by two documents, %s and %s; a "
                    "namespace has one owner, and a trace to %s cannot be routed "
                    "while it has two" % (space, os.path.basename(held),
                                          os.path.basename(source), space)))
    return routes, findings


def links(specs):
    """The routing map as a document carries it: namespace to filename.

    Embedded in a document as `links` so the runtime can turn a trace into a
    link without the reader's browser holding the whole set (FR-TRC-07).
    """
    routes, _ = owners(specs)
    return dict(routes)


def route(root, filenames=None):
    """Re-render every document in a project with the routing map it needs.

    A document is written before its siblings exist, so it cannot know at
    authoring time which file owns `NFR-ARC`. This reads the set, derives the
    map and re-renders each document from its own embedded specification
    (`chain.regenerate`, FR-DOC-06) — the rendered markup is never edited
    (ADR-02). Returns the paths written.
    """
    from z2s import chain, paths                    # local: chain imports validate

    sources = paths.specs(root)
    if filenames is not None:
        sources = [one for one in sources if os.path.basename(one) in filenames]
    specs, findings = read(sources)
    owned = {os.path.basename(source): source for source in specs}
    routes = links(specs)
    shared = paths.shared(root, paths.SPECS_DIR)

    written = []
    for source in specs:
        spec = specs[source]
        if routes:
            # Relative to the document that carries the map: a feature's
            # document reaches the shared Context three directories up, and a
            # set with no features embeds the bare filenames it always did.
            here = os.path.dirname(source)
            spec["links"] = {space: os.path.relpath(owned[name], here).replace(os.sep, "/")
                             for space, name in routes.items()}
        block = spec.get("document") or {}
        written.append(chain.write(root, os.path.basename(source), spec,
                                   "%s-spec" % block.get("slug", "doc"),
                                   shared=os.path.dirname(source) == shared))
    return written, findings


# ------------------------------------------------------------------ the universe

def universe(specs, index=None):
    """Every identifier that has to be built, and every one that deliberately does not.

    Requirements and decisions only (M7-02). An area key is not here: an area
    carries `key`, an entry carries `id`, and only the second is an allocation.
    """
    index = defines(specs) if index is None else index
    items = collections.OrderedDict()
    for identifier in index:
        kind = schema.kind_of(identifier)
        if kind not in COUNTED:
            continue
        entry = index[identifier][0].entry
        if RETIRED in entry:
            state, reason = "retired", entry.get(RETIRED)
        elif entry.get("priority") == EXCLUDED:
            state, reason = "excluded", entry.get(REASON)
        else:
            state, reason = None, None
        items[identifier] = Item(identifier, kind, entry.get("title") or "",
                                 index[identifier][0].source, state, reason)
    return items


def claims(specs):
    """Which units of work claim which identifiers.

    A claimant is a unit of the plan and nothing else. A story tracing to a
    requirement describes it; only a task schedules it, and a gate that counted
    description as coverage would pass a set nobody had planned to build.
    """
    out = {}
    for source in specs:
        for path, entry in schema.entries(specs[source]):
            unit = entry.get("id")
            if not isinstance(unit, str) or schema.kind_of(unit) != "plan":
                continue
            traces = entry.get("traces")
            if not isinstance(traces, dict):
                continue
            for kind in sorted(traces):
                for target in traces[kind] or ():
                    if not isinstance(target, str):
                        continue
                    out.setdefault(target, [])
                    if unit not in out[target]:
                        out[target].append(unit)
    return out


def deferrals(specs):
    """Every unit of work taken out of the current release, and why (M7-05)."""
    out = {}
    for source in specs:
        for path, entry in schema.entries(specs[source]):
            unit = entry.get("id")
            if (isinstance(unit, str) and schema.kind_of(unit) == "plan"
                    and DEFERRED in entry):
                out[unit] = entry.get(DEFERRED)
    return out


def _milestone(unit):
    """The milestone a unit belongs to. `M7-P1-T1` is deferred if `M7` is."""
    return str(unit).split("-")[0]


def matrix(specs):
    """The coverage matrix: every identifier in the universe, with its claimants.

    Returned as data so the gate and the renderer read the same rows (FR-TRC-04)
    rather than computing the same answer twice and disagreeing under load.
    """
    items = universe(specs)
    claimed = claims(specs)
    deferred = deferrals(specs)

    rows = []
    for identifier in items:
        item = items[identifier]
        units = sorted(claimed.get(identifier, ()))
        held = sorted(unit for unit in units
                      if unit in deferred or _milestone(unit) in deferred)
        if item.state is not None:
            state = item.state
        elif not units:
            state = UNCOVERED
        elif len(held) == len(units):
            state = DEFERRED_ONLY
        else:
            state = CLAIMED
        rows.append(Row(identifier, item.kind, item.title, item.source, state,
                        units, held))
    return rows


# --------------------------------------------------------------------- the gate

def check(specs):
    """Every finding the set's coverage produces.

    A failure here is not downgradable, by argument, environment or
    configuration (NFR-VAL-03). The severity is a property of the rule; a red
    build that can be made green without a fix is worse than no gate at all.
    """
    findings = []
    _, collisions = owners(specs)
    findings.extend(collisions)

    items = universe(specs)
    for identifier in items:
        item = items[identifier]
        if item.state in ("excluded", "retired") and schema.is_empty(item.reason):
            findings.append(schema.Finding(
                schema.FAILURE, "%s-without-reason" % item.state, identifier,
                "%s is %s and says nothing about why; a decision with no argument "
                "is the one that gets re-argued" % (identifier, item.state)))

    index = defines(specs)
    for identifier in items:
        if items[identifier].state != "retired":
            continue
        live = [one for one in index[identifier] if RETIRED not in one.entry]
        if live:
            findings.append(schema.Finding(
                schema.FAILURE, "retired-identifier-reused", identifier,
                "%s is retired and is also declared live in %s; a retired number is "
                "reserved for the life of the project, because every trace, test "
                "name and commit message that used it still means it (ADR-03)"
                % (identifier, ", ".join(sorted(os.path.basename(one.source)
                                                for one in live)))))

    deferred = deferrals(specs)
    for row in matrix(specs):
        if row.state == UNCOVERED:
            findings.append(schema.Finding(
                schema.FAILURE, "uncovered", row.id,
                "%s (%s) is claimed by no unit of work: %s. Schedule it, exclude it "
                "with a reason, or retire it — but it cannot simply be unmentioned"
                % (row.id, namespace(row.id), row.title)))
        elif row.state == DEFERRED_ONLY:
            milestones = sorted(set(_milestone(unit) for unit in row.deferred))
            reasons = sorted(set(str(deferred.get(unit)
                                     or deferred.get(_milestone(unit)) or "")
                                 for unit in row.deferred) - set([""]))
            findings.append(schema.Finding(
                schema.WARNING, "deferred", row.id,
                "%s is claimed only by %s, deferred out of this release%s. It is "
                "scheduled somewhere, so this passes — and stays visible"
                % (row.id, ", ".join(milestones),
                   ": " + "; ".join(reasons) if reasons else "")))
    return findings


def gate(sources):
    """Read the set and answer the whole question: findings, rows, documents read."""
    specs, findings = read(sources)
    return findings + check(specs), matrix(specs), specs


def counts(rows):
    """How many identifiers are in each state, for the header line."""
    tally = collections.Counter(row.state for row in rows)
    tally["universe"] = sum(1 for row in rows
                            if row.state not in ("excluded", "retired"))
    return tally


#: How many unclaimed identifiers the header will name before it stops naming
#: them. Past this the list stops being a list an operator reads and becomes the
#: matrix again — which is what the header exists instead of.
NAMED_UNCLAIMED = 12


def _named(rows):
    """The unclaimed identifiers, on the line that counts them (M12-P2-T3).

    An amendment that nothing claims is one or two identifiers, and an operator
    who has just added them should be told which they are on the first line
    rather than reading a whole coverage matrix to find out (FR-AMD-05).
    """
    found = [row.id for row in rows if row.state == UNCOVERED]
    if not found:
        return ""
    if len(found) > NAMED_UNCLAIMED:
        return " — %s and %d more" % (", ".join(found[:NAMED_UNCLAIMED]),
                                      len(found) - NAMED_UNCLAIMED)
    return " — %s" % ", ".join(found)


def format_report(findings, rows, specs, sources):
    """The same answer, written for the person who has to fix it.

    States what actually ran before it states what it found (FR-GEN-03): a
    summary that does not say how many documents it read cannot be told apart
    from one that read none.
    """
    tally = counts(rows)
    kinds = collections.Counter(row.kind for row in rows
                                if row.state not in ("excluded", "retired"))
    skipped = len(sources) - len(specs)

    lines = ["documents: %d read, %d skipped" % (len(specs), skipped),
             "universe: %d  (requirements %d · decisions %d)  excluded: %d  retired: %d"
             % (tally["universe"], kinds["requirement"], kinds["decision"],
                tally["excluded"], tally["retired"]),
             "claimed: %d  deferred: %d  unclaimed: %d%s"
             % (tally[CLAIMED], tally[DEFERRED_ONLY], tally[UNCOVERED],
                _named(rows)), ""]

    for finding in findings:
        lines.append("  %-7s %-24s %s"
                     % (finding.severity.upper(), finding.code, finding.message))
    if findings:
        lines.append("")

    failures = [one for one in findings if one.severity == schema.FAILURE]
    if not failures:
        lines.append("OK: every requirement and decision is claimed by a unit of work")
    lines.append("%d failure%s, %d warning%s"
                 % (len(failures), "" if len(failures) == 1 else "s",
                    len(findings) - len(failures),
                    "" if len(findings) - len(failures) == 1 else "s"))
    return "\n".join(lines)


def exit_code(findings):
    """Non-zero on any failure. Warnings alone never fail a build."""
    return 1 if any(one.severity == schema.FAILURE for one in findings) else 0


def main(argv, out=sys.stdout):
    """The command. Its exit status is the answer (FR-TRC-05, FR-VAL-05)."""
    if not argv:
        out.write(USAGE + "\n")
        return 2
    findings, rows, specs = gate(argv)
    out.write(format_report(findings, rows, specs, argv) + "\n")
    return exit_code(findings)


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
