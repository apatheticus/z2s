# -*- coding: utf-8 -*-
"""The technical-specification generator: how it will be built, and why.

Sixth in the chain. Everything above this document deliberately refuses to name
a technology: the functional specification states what must be observable and
records the choice as a question for here. This is where those questions are
answered, and where the answers are made accountable — every technical
requirement points at the functional requirement or the decision that motivates
it, every decision carries the argument that produced it, and every target is a
number somebody can measure rather than an adjective everybody can agree with.

Four rules shape everything below.

  * It runs sixth or not at all. Without a completed functional specification —
    and without the context document beside it — the generator names what is
    missing and leaves the project exactly as it found it (US-SKL-01-S02).
  * A technical requirement that answers nothing is not written down. It becomes
    an open question, because a requirement traceable to neither a stated need
    nor a recorded decision is somebody's preference arriving as a constraint
    (FR-TRC-03).
  * A decision states its context, the decision, the alternatives considered and
    the consequences accepted, or it is not written down (M6-P1-T2-C1). A
    conclusion without its argument is what gets re-argued from scratch, and a
    later reader cannot tell whether the reasoning still holds.
  * A target is a number with a note on how it is measured (M6-P1-T3-C1,
    M6-P1-T3-C2). "Fast" is a target two people can both claim to have met; the
    whole point of writing it down is that a machine can check it later.

Identifiers for decisions and targets are assigned by position in the brief,
BEFORE the sifting (M6-04). A technical requirement may cite a decision this
same run is assigning, so numbering the survivors would silently re-point every
citation past a decision that was dropped. A dropped entry leaves its number
unused, which is what ADR-03 already says happens to a retired identifier.

The document is also its own source. `regenerate` re-renders it from the
specification embedded in it, so an update is made by editing that specification
and re-rendering, never by editing rendered markup (FR-DOC-06, ADR-02).

The brief is a plain dictionary:

    {"title": ..., "owner": ..., "date": "2026-08-14",       # required facts
     "version": ..., "status": ..., "summary": ...,          # optional
     "scopeNote": ..., "releaseScope": ...,                  # optional
     "principles": [{"name": ..., "desc": ...}],
     "stack": [{"layer": ..., "choice": ..., "role": ...}],
     "components": [{"name": ..., "kind": ..., "responsibilities": ...}],
     "dataModel": [{"name": ..., "points": [...]}],
     "crosscutting": [{"name": ..., "points": [...]}],
     "decisions": [{"title": ..., "status": "Accepted", "context": ...,
                    "decision": ..., "alternatives": [...],
                    "consequences": [...], "traces": {"fr": ["FR-DOC-01"]}}],
     "areas": [{"key": "NFR-ARC", "name": ..., "description": ...}],
     "requirements": [{"area": "NFR-ARC", "priority": "Must", "title": ...,
                       "text": ..., "notes": ..., "tags": [...],
                       "traces": {"fr": ["FR-DOC-01"], "adr": ["ADR-01"]}}],
     "targets": [{"title": ..., "target": "Under 250 KB",
                  "measured": ..., "notes": ..., "traces": {...}}],
     "risks": [{"risk": ..., "mitigation": ...}],
     "assumptions": ["...", ...],
     "sources": [{"kind": ..., "name": ..., "origin": ..., "contributed": ...}]}

Traces: FR-DOC-01, FR-DOC-04, FR-DOC-06, FR-DOC-08, FR-DOC-10, FR-AMD-04,
FR-CTX-05, FR-PLN-05, FR-TRC-03, NFR-ARC-01, NFR-ARC-02, NFR-DAT-03,
NFR-DAT-06, NFR-EVO-05, NFR-GEN-01, NFR-PRF-01, US-DOC-01, US-AMD-01,
US-PLN-02, US-TRC-02, ADR-03.
"""

import collections
import re

from z2s import chain, context, fsd, gate, paths, schema

SLUG = "sdd"
TYPE = "System Design Document (SDD)"
FILENAME = "SDD.html"
SPEC_ID = SLUG + "-spec"

REQUIRED_FACTS = ("title", "owner", "date")
DEFAULTS = {"version": "1.0", "status": "Draft for review"}
CARRIED = ("summary", "scopeNote", "releaseScope", chain.ADDENDUM)

#: What a technical requirement must answer before it can be written down. Two
#: kinds, either of which is a real answer to "why does this exist": a need the
#: functional specification states, or a decision this document itself records.
RULE = chain.Rule(("fr", "adr"), "functional requirement or decision",
                  "technical requirement", "answers", "title",
                  "neither the functional specification nor this document states")

#: The four parts of a decision, and what to ask when one is missing. All four
#: are required because the first two are the conclusion and the last two are
#: the argument, and a conclusion nobody can audit is a conclusion that gets
#: re-taken (NFR-EVO-05).
DECISION_PARTS = collections.OrderedDict((
    ("context", "what forced the decision “%s”"),
    ("decision", "what was actually decided in “%s”"),
    ("alternatives", "what was considered and rejected before deciding “%s”"),
    ("consequences", "what was accepted as a consequence of deciding “%s”"),
))

#: What makes a target a number rather than an opinion. A digit, or a count of
#: nothing written out — "zero unclaimed requirements" is the most common target
#: this method sets, and it is as measurable as "under 250 KB".
_NUMBER = re.compile(r"\d|\bzero\b|\bnone\b", re.IGNORECASE)

#: The sections a technical document owes beyond its three catalogues, in the
#: order a reader meets them. Each names the brief key it is built from, the
#: section it becomes, what one entry is called, the field that identifies an
#: entry, the fields an entry must also state before it can be written down, the
#: builder that renders it, and what to ask when the brief says nothing at all.
#:
#: Declared as data because these five differ only in their words. Written out
#: five times, they would drift into five slightly different opinions about what
#: a silent brief means.
Plain = collections.namedtuple("Plain", "key section noun name parts build silence")

IncompleteBrief = chain.IncompleteBrief
MissingPrerequisite = chain.MissingPrerequisite


def statuses():
    """The closed set a decision's standing is drawn from (NFR-DAT-04)."""
    return [value["id"] for value in schema.ENUMS["decisionStatuses"]]


def forks(brief):
    """Every fork this brief opens.

    One. The technology choices are the brief's to make — that is what this
    document is for — and the words are the context document's. What is left to
    decide is what to do where the brief says nothing.
    """
    return (chain.gaps_fork("brief"),)


def open_gate(brief, root=None):
    """The gate this generator runs, over whatever is already known."""
    decisions = gate.load(root, SLUG) if root is not None else ()
    return gate.Gate(SLUG, forks(brief), source=brief, decisions=decisions)


# ---------------------------------------------------------------------- areas

def areas(brief):
    """The declared areas, in the order the brief declares them (NFR-DAT-03)."""
    return chain.areas(brief, "NFR-", "requirement")


# ------------------------------------------------------------------ the sifting

def _stated(items, plain):
    """Entries that state every part of themselves, and a gap for each that does not."""
    kept, gaps = list(items), []
    for field, phrasing in plain.parts:
        kept, found = chain.complete(kept, field, plain.name, phrasing)
        gaps.extend(found)
    return kept, gaps


def _reasoned(items):
    """Decisions carrying all four parts (M6-P1-T2-C1).

    One question per missing part rather than one listing them all: each part is
    a separate thing to go and find out, and a question asking for four answers
    at once gets one.
    """
    kept, gaps = [], []
    for one in items:
        absent = [part for part in DECISION_PARTS if schema.is_empty(one.get(part))]
        for part in absent:
            gaps.append(DECISION_PARTS[part] % one["title"])
        if not absent:
            kept.append(one)
    return kept, gaps


def _standing(items):
    """Decisions carrying a status from the closed set (NFR-DAT-04).

    Not defaulted to "Accepted". A decision nobody has agreed to and a decision
    in force are read completely differently by somebody deciding whether they
    may still argue with it, and inventing the stronger of the two here would
    end an argument that was never had.
    """
    allowed = statuses()
    kept, gaps = [], []
    for one in items:
        status = one.get("status")
        asked = "what standing the decision “%s” has" % one["title"]
        if schema.is_empty(status):
            gaps.append(asked)
        elif status not in allowed:
            gaps.append("%s; it states “%s”, which is not one of %s"
                        % (asked, status, ", ".join(allowed)))
        else:
            kept.append(one)
    return kept, gaps


def _numeric(items):
    """Targets stated as a number (M6-P1-T3-C1).

    An adjective is not refused because it is vague — it is refused because
    nothing downstream can turn it into a check. "Fast enough" cannot fail a
    build, so a target written that way quietly exempts itself from the only
    thing that would have enforced it.
    """
    kept, gaps = [], []
    for one in items:
        value = one.get("target")
        asked = "what number the target “%s” is set at" % one["title"]
        if schema.is_empty(value):
            gaps.append(asked)
        elif not _NUMBER.search(value):
            gaps.append("%s; it states “%s”, which no check can be written against"
                        % (asked, value))
        else:
            kept.append(one)
    return kept, gaps


# ----------------------------------------------------------------- the sections

def _principles(items):
    return {"id": "principles", "type": "definitions", "title": "Design principles",
            "lede": "The rules that settle every technical question this document "
                    "does not answer directly.",
            "items": [{"term": one["name"], "definition": one["desc"]} for one in items]}


def _stack(items):
    return {"id": "stack", "type": "table", "title": "Composition",
            "lede": "What the system is built out of, and what each part is there to do.",
            "columns": ["Layer", "Choice", "Role"],
            "rows": [[one["layer"], one["choice"], one["role"]] for one in items]}


def _components(items):
    return {"id": "components", "type": "cards", "title": "Components",
            "items": [{"kicker": one["kind"], "title": one["name"],
                       "body": one["responsibilities"]} for one in items]}


def _grouped(section_id, title, lede):
    """A cards section whose entries carry points rather than a paragraph."""
    def build(items):
        return {"id": section_id, "type": "cards", "title": title, "lede": lede,
                "items": [{"title": one["name"],
                           "items": [point for point in one["points"]
                                     if not schema.is_empty(point)]}
                          for one in items]}
    return build


PLAIN = (
    Plain("principles", "principles", "principle", "name",
          (("desc", "what the principle “%s” means in practice"),),
          _principles,
          "which principles settle the technical questions this document leaves open"),
    Plain("stack", "stack", "layer", "layer",
          (("choice", "what was chosen for the “%s” layer"),
           ("role", "what the “%s” layer is there to do")),
          _stack,
          "what this system is built out of"),
    Plain("components", "components", "component", "name",
          (("kind", "what kind of thing the component “%s” is"),
           ("responsibilities", "what the component “%s” is responsible for")),
          _components,
          "which components this system is divided into"),
    Plain("dataModel", "data", "data-model entry", "name",
          (("points", "what the data-model entry “%s” holds"),),
          _grouped("data", "Data model",
                   "The shape of what is stored, and what may never be stored."),
          "what shape this system's data takes"),
    Plain("crosscutting", "crosscutting", "cross-cutting concern", "name",
          (("points", "what the cross-cutting concern “%s” requires"),),
          _grouped("crosscutting", "Cross-cutting concerns",
                   "What every component owes, whatever else it does."),
          "which concerns cut across every component"),
)


def _decision_entries(decisions):
    """The decisions, carrying the numbers assigned before the sifting (M6-04)."""
    built = []
    for one in decisions:
        entry = {"id": one["id"], "status": one["status"], "title": one["title"],
                 "context": one["context"], "decision": one["decision"],
                 "alternatives": [line for line in one["alternatives"]
                                  if not schema.is_empty(line)],
                 "consequences": [line for line in one["consequences"]
                                  if not schema.is_empty(line)]}
        found = chain.traces(one)
        if found:
            entry["traces"] = found
        built.append(entry)
    return built


def _decision_catalogue(entries):
    """The decisions, in the same catalogue the requirements use (M6-01).

    The same section type, so the toolbar, the keyword filter, the deep links
    and the review ticks all reach them without a second implementation of any
    of it (NFR-ARC-01). A decision carries a standing rather than a priority
    band, so the band checkboxes leave it alone — which is right: a decision is
    not something a release ships without.
    """
    return {"id": "decisions", "type": "requirements",
            "title": "Architecture decisions",
            "badge": "%d decisions" % len(entries),
            "lede": "Each records the context that forced a choice, the choice, what "
                    "was rejected, and what was accepted as a consequence — so a later "
                    "reader can judge whether the reasoning still holds.",
            "items": entries}


def _entries(requirements, declared):
    """The catalogue's entries, grouped by area and numbered within it.

    Numbered within the area rather than across the document, because the area
    is part of the identifier: NFR-ARC-01 and NFR-DAT-01 are two requirements,
    and a reader who sees the second knows which group it belongs to without
    looking it up.
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
            amended = chain.amendments(one, "requirement")
            if amended:
                entry["amendments"] = amended
            tags = [tag for tag in one.get("tags") or () if not schema.is_empty(tag)]
            if tags:
                entry["tags"] = tags
            found = chain.traces(one)
            if found:
                entry["traces"] = found
            built.append(entry)
    return built


def _catalogue(declared, entries):
    """The technical requirements catalogue."""
    occupied = {one["area"] for one in entries}
    return {"id": "requirements", "type": "requirements",
            "title": "Technical requirements",
            "badge": "%d entries" % len(entries),
            "lede": "Every requirement is individually testable, belongs to one area, "
                    "and answers a stated need or a recorded decision.",
            "areas": [chain.area_section(one) for one in declared if one["key"] in occupied],
            "items": entries}


def _target_entries(targets):
    """The targets, carrying the numbers assigned before the sifting (M6-04).

    The number itself goes in `text` and the measurement in `measured`: `text`
    is what a reader reads first and what a keyword is matched against, and the
    two belong together on the page because a number whose measurement is
    somewhere else is a number two people can both claim to have met.
    """
    built = []
    for one in targets:
        entry = {"id": one["id"], "title": one["title"], "text": one["target"],
                 "measured": one["measured"]}
        if not schema.is_empty(one.get("notes")):
            entry["notes"] = one["notes"]
        found = chain.traces(one)
        if found:
            entry["traces"] = found
        built.append(entry)
    return built


def _target_catalogue(entries):
    """The targets, in the same catalogue again, and numbered for the same reason
    every other entry is: something later has to be able to cite one (M6-02)."""
    return {"id": "targets", "type": "requirements", "title": "Targets",
            "badge": "%d targets" % len(entries),
            "lede": "Numbers, not adjectives — so each can become a criterion a "
                    "machine checks rather than a claim somebody makes.",
            "items": entries}


def _risks(items):
    return {"id": "risks", "type": "table", "title": "Technical risks",
            "columns": ["Risk", "Mitigation"],
            "rows": [[one["risk"], one["mitigation"]] for one in items]}


def _section(id, type, title, key, value):
    return {"id": id, "type": type, "title": title, key: value}


# ------------------------------------------------------------------ the reading

def _items(spec, section_id):
    """One catalogue's entries, by the section that holds them.

    By section rather than by type: this document renders three catalogues of
    the same type, and a reader asking for the requirements does not want the
    decisions counted among them.
    """
    found = []
    for section in (spec.get("sections") or ()):
        if section.get("id") == section_id and section.get("type") == "requirements":
            found.extend(section.get("items") or ())
    return found


def requirements(spec):
    """Every technical requirement this document states, in document order."""
    return _items(spec, "requirements")


def decisions(spec):
    """Every decision this document records, in document order."""
    return _items(spec, "decisions")


def targets(spec):
    """Every target this document sets, in document order.

    Each carries its identifier, so the thing that will read this — a plan task
    citing one of them in a criterion — has something to cite (M6-02).
    """
    return _items(spec, "targets")


# ------------------------------------------------------------------ generation

def envelope(brief):
    """The document block, from facts only (FR-DOC-08)."""
    return chain.envelope(brief, SLUG, TYPE, REQUIRED_FACTS, DEFAULTS, CARRIED)


def generate(brief, run, root="."):
    """The technical specification object. Writes nothing.

    The gate is checked before either document above is looked for: an open fork
    stops the run whatever else is wrong, and an operator told about a missing
    file when the real problem is an unanswered question fixes the wrong thing.
    """
    run.require_closed()
    above = chain.require(root, fsd.FILENAME, fsd.SLUG,
                          "the technical-specification generator")
    words = chain.require(root, context.FILENAME, context.SLUG,
                          "the technical-specification generator", shared=True)

    block = envelope(brief)
    declared = areas(brief)
    counted, _ = fsd.universe(above)

    sections, gaps = [], []

    # ---- what the technical choices rest on, one plain section at a time
    for plain in PLAIN:
        stated = chain.named(brief.get(plain.key), plain.name, plain.noun)
        stated, found = _stated(stated, plain)
        gaps.extend(found)
        if stated:
            sections.append(plain.build(stated))
        else:
            gaps.append(plain.silence)

    # ---- the decisions, numbered before they are sifted (M6-04)
    stated = chain.named(brief.get("decisions"), "title", "decision")
    numbered = [dict(one, id=chain.identifier("ADR", index))
                for index, one in enumerate(stated)]
    for sift in (_standing, _reasoned):
        numbered, found = sift(numbered)
        gaps.extend(found)

    taken = _decision_entries(numbered)
    if taken:
        sections.append(_decision_catalogue(taken))
    else:
        gaps.append("which architecture decisions this design rests on")

    # ---- the requirements, answering a stated need or a decision above
    known = set(counted) | {one["id"] for one in taken}
    stated = chain.named(brief.get("requirements"), "title", "requirement")
    stated = chain.named(stated, "text", "requirement")

    for sift in (lambda kept: chain.placed(kept, declared, "requirement"),
                 lambda kept: chain.prioritised(kept, "requirement"),
                 lambda kept: chain.traced(kept, RULE, known)):
        stated, found = sift(stated)
        gaps.extend(found)

    entries = _entries(stated, declared)
    if entries:
        sections.append(_catalogue(declared, entries))
    else:
        gaps.append("what technical requirements this design has at all")

    # ---- the targets, numbered before they are sifted for the same reason
    stated = chain.named(brief.get("targets"), "title", "target")
    numbered = [dict(one, id=chain.identifier("TG", index))
                for index, one in enumerate(stated)]
    numbered, found = _numeric(numbered)
    gaps.extend(found)
    numbered, found = chain.complete(numbered, "measured", "title",
                                     "how the target “%s” is measured")
    gaps.extend(found)

    set_at = _target_entries(numbered)
    if set_at:
        sections.append(_target_catalogue(set_at))
    else:
        gaps.append("what this design is required to achieve, as numbers")

    # ---- what could go wrong with all of it
    stated = chain.named(brief.get("risks"), "risk", "risk")
    stated, found = chain.complete(stated, "mitigation", "risk",
                                   "how the risk “%s” is mitigated")
    gaps.extend(found)
    if stated:
        sections.append(_risks(stated))
    else:
        gaps.append("what could go wrong with this design")

    assumed = [one for one in brief.get("assumptions") or () if not schema.is_empty(one)]
    if assumed:
        sections.append(_section("assumptions", "list", "Assumptions", "items", assumed))

    sources, source_gaps = chain.register(brief)
    gaps.extend(source_gaps)
    if sources:
        sections.append(chain.register_section(sources))
    else:
        gaps.append("what material this design was written from")

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


def filename(block):
    """Where this document goes — the original, or its own addendum file."""
    return chain.addendum_file(block, FILENAME)


def write(root, spec):
    """Write the rendered technical specification into the project."""
    return chain.write(root, filename(spec["document"]), spec, SPEC_ID)


def regenerate(root, spec=None, addendum=None):
    """Re-render this document from its own embedded specification (FR-DOC-06)."""
    target = filename(spec["document"] if spec else {chain.ADDENDUM: addendum})
    return chain.regenerate(root, target, SLUG, SPEC_ID, spec)


def author(root, brief, run):
    """Gate, chain, ledger, document — in that order. Returns (path, spec)."""
    spec = generate(brief, run, root)

    paths.ensure_layout(root)
    run.record(root)
    return write(root, spec), spec
