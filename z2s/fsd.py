# -*- coding: utf-8 -*-
"""The functional-specification generator: what the thing must do, and nothing else.

Fourth in the chain. The vision says what the world looks like once this works,
the context document agrees what the words mean, the product requirements say
which goals matter — and this document turns those goals into individually
testable requirements, grouped by area, prioritised, and free of any decision
about how they will be built.

Four rules shape everything below.

  * It runs fourth or not at all. Without a completed PRD — and without the
    context document beside it — the generator names what is missing and leaves
    the project exactly as it found it (US-SKL-01-S02).
  * A requirement that serves no goal the PRD states is not written down. It
    becomes an open question, because a requirement traceable to nothing is
    either a goal nobody wrote down or scope arriving through the side door
    (FR-TRC-03).
  * A requirement that names a technology is not written down either. The
    functional document says what must be observable; which product delivers it
    is the technical document's decision, and a functional requirement that has
    already made that decision closes it without anyone noticing (FR-DOC-05).
    The deferral is recorded as an open question, so the choice survives as a
    choice.
  * A deliberate exclusion is an entry, not an omission. It carries its reason
    and its lowest priority band, and it is not counted in the coverage universe
    (FR-TRC-06). An exclusion that is simply left out is re-argued from scratch
    next quarter.

The document is also its own source. `regenerate` re-renders it from the
specification embedded in it, so an update is made by editing that specification
and re-rendering, never by editing rendered markup (FR-DOC-06, ADR-02).

The brief is a plain dictionary:

    {"title": ..., "owner": ..., "date": "2026-08-14",       # required facts
     "version": ..., "status": ..., "summary": ...,          # optional
     "scopeNote": ..., "releaseScope": ...,                  # optional
     "purpose": "paragraph" | ["paragraph", ...],
     "areas": [{"key": "FR-DOC", "name": ..., "description": ...}],
     "requirements": [{"area": "FR-DOC", "priority": "Must", "title": ...,
                       "text": ..., "notes": ..., "tags": [...],
                       "traces": {"goal": ["G-01"]}}],
     "technologies": ["Kestrelbase", ...],   # names this project also refuses
     "assumptions": ["...", ...],
     "sources": [{"kind": ..., "name": ..., "origin": ..., "contributed": ...}]}

Traces: FR-DOC-01, FR-DOC-04, FR-DOC-05, FR-DOC-06, FR-DOC-08, FR-DOC-10,
FR-CTX-05, FR-TRC-03, FR-TRC-06, NFR-ARC-01, NFR-ARC-02, NFR-DAT-03,
NFR-DAT-06, NFR-GEN-01, US-DOC-01, US-DOC-03, US-TRC-01.
"""

import collections

from z2s import chain, context, gate, paths, prd, schema

SLUG = "fsd"
TYPE = "Functional Specification Document (FSD)"
FILENAME = "FSD.html"
SPEC_ID = SLUG + "-spec"

REQUIRED_FACTS = ("title", "owner", "date")
DEFAULTS = {"version": "1.0", "status": "Draft for review"}
CARRIED = ("summary", "scopeNote", "releaseScope")

#: The priority band that records a decision not to build (FR-TRC-06). It is a
#: value of the same closed set as every other band, so an exclusion is a
#: requirement with a priority rather than a second kind of thing.
EXCLUDED = "Won't"

#: What a requirement must trace to before it can be written down.
RULE = chain.Rule("goal", "goal", "requirement", "serves", "title",
                  "the product requirements do not state")

IncompleteBrief = chain.IncompleteBrief
MissingPrerequisite = chain.MissingPrerequisite


def priorities():
    """The closed set a requirement's priority is drawn from (NFR-DAT-04)."""
    return [value["id"] for value in schema.ENUMS["priorities"]]


def forks(brief):
    """Every fork this brief opens.

    One. The scope comes from the product requirements, the words from the
    context document, and the areas from the brief, so the only thing left to
    decide is what to do where the brief says nothing.
    """
    return (chain.gaps_fork("brief"),)


def open_gate(brief, root=None):
    """The gate this generator runs, over whatever is already known."""
    decisions = gate.load(root, SLUG) if root is not None else ()
    return gate.Gate(SLUG, forks(brief), source=brief, decisions=decisions)


# ---------------------------------------------------------------------- areas

def areas(brief):
    """The declared areas, in the order the brief declares them.

    An area key is an identifier in its own right — it is what every requirement
    in the group points at, and what its identifiers are built from — so a key
    the grammar cannot express is a malformed brief rather than a gap. Every
    requirement under it would inherit the malformation, and an identifier that
    cannot be written down cannot be traced to (NFR-DAT-03).
    """
    declared = chain.named(brief.get("areas"), "name", "area")
    for index, one in enumerate(declared):
        key = one.get("key")
        if not isinstance(key, str) or not key.startswith("FR-") \
                or schema.check_identifier(key):
            raise IncompleteBrief(
                "area %d declares key %r; an area key is FR- followed by two to four "
                "capitals, because every requirement in the area is numbered from it"
                % (index + 1, key))
    return declared


def _area_section(one):
    """One area, as a reader is shown it."""
    built = {"key": one["key"], "name": one["name"]}
    if not schema.is_empty(one.get("description")):
        built["description"] = one["description"]
    return built


# ------------------------------------------------------------------ the sifting

def _placed(requirements, declared):
    """Requirements that belong to an area this document declares."""
    known = {one["key"] for one in declared}
    kept, gaps = [], []
    for one in requirements:
        area = one.get("area")
        asked = "which area the requirement “%s” belongs to" % one["title"]
        if schema.is_empty(area):
            gaps.append(asked)
        elif area not in known:
            gaps.append("%s; it names %s, which this document does not declare"
                        % (asked, area))
        else:
            kept.append(one)
    return kept, gaps


def _prioritised(requirements):
    """Requirements carrying a priority from the closed set (M4-P1-T1-C2).

    A priority is what decides whether a release ships without the requirement,
    so a missing one is not a detail to be defaulted: "Must" invented here is a
    release blocked by nobody's decision, and "Could" invented here is a Must
    quietly dropped.
    """
    allowed = priorities()
    kept, gaps = [], []
    for one in requirements:
        priority = one.get("priority")
        asked = "what priority the requirement “%s” carries" % one["title"]
        if schema.is_empty(priority):
            gaps.append(asked)
        elif priority not in allowed:
            gaps.append("%s; it states “%s”, which is not one of %s"
                        % (asked, priority, ", ".join(allowed)))
        else:
            kept.append(one)
    return kept, gaps


def _functional(requirements, names):
    """Requirements that state behaviour rather than a technology (FR-DOC-05).

    The requirement is not rewritten with the product name taken out — that
    would be this generator deciding what the author meant. It leaves as a
    question naming both the requirement and the word that disqualified it, for
    the technical specification to answer.
    """
    kept, gaps = [], []
    for one in requirements:
        found = []
        for field in schema.BOUNDARY_FIELDS:
            for name in schema.names_technology(one.get(field), names):
                if name not in found:
                    found.append(name)
        if found:
            gaps.append("which technology the requirement “%s” assumes — its wording "
                        "names %s, and that choice belongs in the technical "
                        "specification" % (one["title"], ", ".join(found)))
        else:
            kept.append(one)
    return kept, gaps


def _justified(requirements):
    """Exclusions that say why (M4-P1-T3-C1).

    An exclusion with no reason is the decision without the argument, which is
    exactly the thing that gets re-argued. Every other priority band passes
    through untouched.
    """
    kept, gaps = [], []
    for one in requirements:
        if one["priority"] == EXCLUDED and schema.is_empty(one.get("notes")):
            gaps.append("why the requirement “%s” is excluded from this release"
                        % one["title"])
        else:
            kept.append(one)
    return kept, gaps


# ----------------------------------------------------------------- the sections

def _entries(requirements, declared):
    """The catalogue's entries, grouped by area and numbered within it.

    Numbered within the area rather than across the document, because the area
    is part of the identifier: FR-DOC-01 and FR-CTX-01 are two requirements, and
    a reader who sees the second knows which group it belongs to without looking
    it up.
    """
    built = []
    for area in declared:
        within = [one for one in requirements if one["area"] == area["key"]]
        for index, one in enumerate(within):
            entry = {"id": chain.identifier(area["key"], index),
                     "area": area["key"],
                     "priority": one["priority"],
                     "title": one["title"],
                     "text": one["text"]}
            if not schema.is_empty(one.get("notes")):
                entry["notes"] = one["notes"]
            tags = [tag for tag in one.get("tags") or () if not schema.is_empty(tag)]
            if tags:
                entry["tags"] = tags
            found = chain.traces(one)
            if found:
                entry["traces"] = found
            built.append(entry)
    return built


def _catalogue(declared, entries):
    """The requirements catalogue: the section the rest of the method reads.

    Only areas something belongs to are shown. A declared area with no
    requirement under it renders as a heading over nothing, which reads as a
    section somebody forgot to write rather than as an area nobody needed
    (NFR-DAT-06).
    """
    occupied = {one["area"] for one in entries}
    return {"id": "requirements", "type": "requirements",
            "title": "Requirements catalogue",
            "badge": "%d entries" % len(entries),
            "lede": "Every requirement is individually testable, belongs to one area, "
                    "and carries the priority band that decides whether a release can "
                    "ship without it.",
            "areas": [_area_section(one) for one in declared if one["key"] in occupied],
            "items": entries}


def _section(id, type, title, key, value):
    return {"id": id, "type": type, "title": title, key: value}


# ----------------------------------------------------------------- the coverage

def universe(spec):
    """What the coverage gate counts, and what it must not (M4-P1-T3-C2).

    Two ordered maps of identifier to title: the requirements a plan has to
    claim, and the deliberate exclusions it must not be asked to. Both are read
    from the same marker — the priority band on the entry itself — so the
    coverage engine and this document cannot disagree about which is which.
    """
    counted, excluded = collections.OrderedDict(), collections.OrderedDict()
    for section in (spec.get("sections") or ()):
        if section.get("type") != "requirements":
            continue
        for one in section.get("items") or ():
            where = excluded if one.get("priority") == EXCLUDED else counted
            where[one["id"]] = one.get("title", "")
    return counted, excluded


# ------------------------------------------------------------------ generation

def envelope(brief):
    """The document block, from facts only (FR-DOC-08)."""
    return chain.envelope(brief, SLUG, TYPE, REQUIRED_FACTS, DEFAULTS, CARRIED)


def generate(brief, run, root="."):
    """The functional specification object. Writes nothing.

    The gate is checked before either document above is looked for: an open fork
    stops the run whatever else is wrong, and an operator told about a missing
    file when the real problem is an unanswered question fixes the wrong thing.
    """
    run.require_closed()
    above = chain.require(root, prd.FILENAME, prd.SLUG,
                          "the functional-specification generator")
    words = chain.require(root, context.FILENAME, context.SLUG,
                          "the functional-specification generator")

    block = envelope(brief)
    declared = areas(brief)
    goals = chain.identified(above, "goal")
    refused = tuple(schema.TECHNOLOGY_NAMES) + tuple(brief.get("technologies") or ())

    sections, gaps = [], []

    purpose = brief.get("purpose")
    if schema.is_empty(purpose):
        gaps.append("what this system must do and for whom")
    else:
        sections.append(_section("purpose", "prose", "Purpose", "body",
                                 [purpose] if isinstance(purpose, str) else list(purpose)))

    # ---- the catalogue, sifted one rule at a time
    stated = chain.named(brief.get("requirements"), "title", "requirement")
    stated = chain.named(stated, "text", "requirement")

    for sift in (lambda kept: _placed(kept, declared),
                 _prioritised,
                 lambda kept: _functional(kept, refused),
                 lambda kept: chain.traced(kept, RULE, goals),
                 _justified):
        stated, found = sift(stated)
        gaps.extend(found)

    entries = _entries(stated, declared)
    if entries:
        sections.append(_catalogue(declared, entries))
    else:
        gaps.append("what functional requirements this system has at all")

    # ---- what the requirements rest on
    assumed = [one for one in brief.get("assumptions") or () if not schema.is_empty(one)]
    if assumed:
        sections.append(_section("assumptions", "list", "Assumptions", "items", assumed))

    sources, source_gaps = chain.register(brief)
    gaps.extend(source_gaps)
    if sources:
        sections.append(chain.register_section(sources))
    else:
        gaps.append("what material these requirements were written from")

    locked = run.section()
    if locked is not None:
        sections.append(locked)

    _file(sections, chain.gap_section(gaps, chain.choice(run, "gaps")))

    spec = {"document": block,
            "schemaVersion": schema.SCHEMA_VERSION,
            "sections": sections}
    if sources:
        spec["sources"] = sources

    # Everything above is said in this project's own words last, in one pass, so
    # that no builder above has to remember to do it (FR-CTX-05).
    return context.consult(spec, context.glossary(words))


def _file(sections, trailing):
    """Put the gaps where they belong, merging rather than duplicating a section.

    A brief that states its assumptions, in a run whose gate chose to file
    silence as assumptions, would otherwise produce two sections called
    Assumptions with one identifier between them — and every deep link into
    either would land on whichever the reader's browser found first.
    """
    if trailing is None:
        return
    for section in sections:
        if section["id"] == trailing["id"]:
            section["items"].extend(trailing["items"])
            return
    sections.append(trailing)


def render(spec, root="."):
    """The finished document text, styled with the host project's tokens."""
    return chain.render(spec, SPEC_ID, root)


def write(root, spec):
    """Write the rendered functional specification into the project."""
    return chain.write(root, FILENAME, spec, SPEC_ID)


def regenerate(root, spec=None):
    """Re-render this document from its own embedded specification (FR-DOC-06)."""
    return chain.regenerate(root, FILENAME, SLUG, SPEC_ID, spec)


def author(root, brief, run):
    """Gate, chain, ledger, document — in that order. Returns (path, spec)."""
    spec = generate(brief, run, root)

    paths.ensure_layout(root)
    run.record(root)
    return write(root, spec), spec
