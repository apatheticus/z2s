# -*- coding: utf-8 -*-
"""The vision generator: the first document in the chain.

Vision needs nothing above it. Everything else does — the context document
derives its vocabulary from this one, and the product requirements trace their
goals to the capabilities named here — so this is where identifiers enter the
method and where provenance starts being kept.

Three rules shape everything below.

  * Nothing is authored until the gate closes (FR-DOC-02). `generate` refuses
    outright, and `author` refuses before it has touched the filesystem, so a
    half-opened project cannot exist.
  * Nothing is invented (FR-DOC-04). Where the brief is silent the section is
    absent, not empty (NFR-DAT-06), and the silence is recorded — as an open
    question or as a stated assumption, whichever the gate chose.
  * Every source consulted is written down (FR-DOC-10). A web address is
    recorded and never fetched: this generator opens no socket, which is why
    it imports nothing that could.

Capabilities and scenarios are assigned identifiers here. They carry the
identifier twice — once as data, once at the front of the title — because a
later document cites "VC-03" and a reader following that citation has to be
able to find it on the page. Both spellings come from one assignment, so they
cannot drift.

The brief is a plain dictionary:

    {"title": ..., "owner": ..., "date": "2026-08-14",       # required facts
     "version": ..., "status": ..., "summary": ...,          # optional
     "problem": ["paragraph", ...],
     "statement": "paragraph" | ["paragraph", ...],
     "principles":   [{"title": ..., "body": ...}],
     "stakeholders": [{"name": ..., "kind": ..., "need": ...}],
     "personas":     [{"title": ..., "body": ...}],
     "capabilities": [{"title": ..., "body": ...}],
     "scenarios":    [{"title": ..., "body": ...,
                       "traces": {"cap": ["VC-01"]}}],
     "constraints":  ["...", ...],
     "sources":      [{"kind": "narrative" | "document" | "web",
                       "name": ..., "origin": ..., "contributed": ...}]}

Every key except the required facts may be absent. A key the brief does carry
also answers the gate's fork of the same name, so a sufficient brief is never
interviewed (FR-DOC-07).

Traces: FR-DOC-01, FR-DOC-02, FR-DOC-03, FR-DOC-04, FR-DOC-07, FR-DOC-10,
NFR-ARC-01, NFR-DAT-06, NFR-GEN-01, ADR-10, US-DOC-01, US-DOC-02, US-CTX-01.
"""

import collections

from z2s import document, gate, paths, runtime, schema, styles, tokens, writer

SLUG = "vision"
TYPE = "Vision document"
FILENAME = "Vision.html"
SPEC_ID = SLUG + "-spec"

#: Facts no generator can supply a defensible default for. `date` is here
#: rather than defaulted from the clock deliberately: reading the clock would
#: make two runs of unchanged input produce different bytes (NFR-GEN-01).
REQUIRED_FACTS = ("title", "owner", "date")

#: Facts that do have a defensible default. A first vision is a draft.
DEFAULTS = {"version": "1.0", "status": "Draft for review"}

#: Optional envelope fields this generator will carry through if the brief
#: states them. Anything else in the brief is section content.
CARRIED = ("summary",)

#: What a source may be (FR-DOC-10). A web address is a recorded origin, never
#: a fetch — see the module docstring.
SOURCE_KINDS = ("narrative", "document", "web")
SOURCE_COLUMNS = ("Kind", "Source", "Where it came from", "What it contributed")

#: The most a two-digit identifier can count to. Past this the grammar cannot
#: express the identifier, and a silently malformed one is worse than a stop.
MAX_IDENTIFIED = 99


class IncompleteBrief(Exception):
    """Raised when the brief omits a fact that cannot be defaulted or invented."""


# ------------------------------------------------------------------- the gate

FORKS = (
    gate.fork(
        "scope",
        "Does this vision cover one release, or the whole product?",
        [gate.option("release", "One release",
                     "The vision is scoped to a single release, and the document says which.",
                     recommended=True),
         gate.option("product", "The whole product",
                     "The vision covers the product's whole life; individual releases are "
                     "scoped later, in the plan.")]),

    gate.fork(
        "gaps",
        "Where the brief is silent, should the vision ask, or state an assumption?",
        [gate.option("question", "Ask an open question",
                     "The silence appears under Open questions, unanswered, for someone to "
                     "answer before the next document.",
                     recommended=True),
         gate.option("assumption", "State an assumption",
                     "The silence appears under Assumptions, as something taken to be true "
                     "and flagged for confirmation.")]),
)


def open_gate(brief, root=None):
    """The gate this generator runs, over whatever is already known.

    Decisions recorded by an earlier run are recovered from the ledger, so a
    locked row is applied rather than asked again (FR-DOC-03). The brief itself
    is the source, so a fork it already answers closes without an interview.
    """
    decisions = gate.load(root, SLUG) if root is not None else ()
    return gate.Gate(SLUG, FORKS, source=brief, decisions=decisions)


# ---------------------------------------------------------------- the sections

#: One declared section. `key` is what the brief calls it, `build` turns the
#: brief's value into the section's payload, and `gap` names the thing that is
#: missing when the brief says nothing — in the words the gap register uses.
#:
#: Declared as data because three things must agree about this list: what gets
#: rendered, what order it comes in, and what counts as a gap. Three separate
#: spellings of one list is how a section quietly stops being missed.
Section = collections.namedtuple("Section", "key id title type build gap")


def _prose(value):
    return {"body": [value] if isinstance(value, str) else list(value)}


def _items(value):
    return {"items": list(value)}


def _cards(value):
    return {"items": [_card(item) for item in value]}


def _card(item):
    card = {"title": item["title"], "body": item["body"]}
    traces = _traces(item)
    if traces:
        card["traces"] = traces
    return card


def _traces(item):
    """An entry's upward links, with empty kinds dropped.

    An empty trace list is a heading over nothing in a machine's reading of the
    document, and the emptiness rule applies to data as much as to prose.
    """
    return {kind: list(values) for kind, values in sorted(item.get("traces", {}).items())
            if not schema.is_empty(values)}


def _identified(prefix):
    """A card builder that numbers its items (FR-DOC-01, NFR-DAT-03)."""
    def build(value):
        return {"items": [_number(prefix, index, item) for index, item in enumerate(value)]}
    return build


def _number(prefix, index, item):
    if index + 1 > MAX_IDENTIFIED:
        raise IncompleteBrief(
            "more than %d %s entries; the identifier grammar cannot express %s-%d, and a "
            "malformed identifier breaks every trace to it"
            % (MAX_IDENTIFIED, prefix, prefix, index + 1))
    identifier = "%s-%02d" % (prefix, index + 1)
    card = _card(item)
    card["id"] = identifier
    # Said twice on purpose, from one assignment: the data carries it so a later
    # document can trace to it, and the title carries it so a reader following
    # that trace can find it on the page. This document's runtime renders a
    # card's title and body, not its identifier.
    card["title"] = "%s · %s" % (identifier, card["title"])
    return card


def _stakeholders(value):
    return {"columns": ["Stakeholder", "Kind", "What they need"],
            "rows": [[one["name"], one["kind"], one["need"]] for one in value]}


SECTIONS = (
    Section("problem", "problem", "The problem", "prose", _prose,
            "the problem this exists to solve"),
    Section("statement", "statement", "The vision", "prose", _prose,
            "what the world looks like once this works"),
    Section("principles", "principles", "Principles", "cards", _cards,
            "the principles this work is held to"),
    Section("stakeholders", "stakeholders", "Stakeholders", "table", _stakeholders,
            "who has a stake in this and what they need"),
    Section("personas", "personas", "Personas", "cards", _cards,
            "who this is for"),
    Section("capabilities", "capabilities", "Capabilities", "cards", _identified("VC"),
            "what this must be able to do"),
    Section("scenarios", "scenarios", "Scenarios", "cards", _identified("VS"),
            "what it looks like when it works"),
    Section("constraints", "constraints", "Constraints and limits", "list", _items,
            "what constrains this work"),
)


# ------------------------------------------------------------- source register

def register(brief):
    """Every source consulted, in the order the brief lists them (FR-DOC-10).

    A source with nothing recorded about what it contributed is not rejected —
    it was still consulted, and dropping it would lose the provenance the
    register exists for. It becomes a gap instead.
    """
    entries, gaps = [], []
    for index, source in enumerate(brief.get("sources", ()) or ()):
        kind = source.get("kind")
        if kind not in SOURCE_KINDS:
            raise IncompleteBrief(
                "source %d has kind %r; a source is one of %s"
                % (index + 1, kind, ", ".join(SOURCE_KINDS)))

        name = source.get("name") or ""
        entry = {"kind": kind, "name": name,
                 "origin": source.get("origin") or "",
                 "contributed": source.get("contributed") or ""}
        entries.append(entry)

        called = name or "source %d" % (index + 1)
        if schema.is_empty(entry["origin"]):
            gaps.append("where %s came from" % called)
        if schema.is_empty(entry["contributed"]):
            gaps.append("what %s contributed" % called)
    return entries, gaps


def _register_section(entries):
    return {"id": "sources", "type": "table", "title": "Source register",
            "columns": list(SOURCE_COLUMNS),
            "rows": [[one["kind"], one["name"], one["origin"], one["contributed"]]
                     for one in entries]}


# ------------------------------------------------------------------- the gaps

#: How a gap reads under each answer to the `gaps` fork. Both say the same
#: thing about the same silence; they differ in what is being asked of the
#: reader — answer this, or confirm this.
GAP_PHRASING = {
    "question": ("open-questions", "Open questions",
                 "The brief says nothing about %s. What should it say?"),
    "assumption": ("assumptions", "Assumptions",
                   "Nothing was stated about %s; it is taken to be absent until a later "
                   "document says otherwise. Confirm before the product requirements."),
}


def _gap_section(gaps, choice):
    """The gaps, filed where the gate said to file them (FR-DOC-04)."""
    if not gaps:
        return None
    section_id, title, phrasing = GAP_PHRASING.get(choice, GAP_PHRASING["question"])
    return {"id": section_id, "type": "list", "title": title,
            "items": [phrasing % gap for gap in gaps]}


_FORKS_BY_ID = dict((one.id, one) for one in FORKS)


def _decision(run, fork_id):
    """What the gate settled one fork on, or None if it never saw that fork."""
    for decision in run.decisions:
        if decision.fork == fork_id:
            return decision
    return None


def _choice(run, fork_id):
    """A settled fork, matched back to the identifier of the option chosen.

    An answer nobody offered is returned as given rather than forced onto an
    option: the owner is allowed an answer the fork did not predict, and the
    caller decides what to do with one it does not recognise.
    """
    decision = _decision(run, fork_id)
    if decision is None:
        return None
    for one in _FORKS_BY_ID[fork_id].options:
        if decision.choice in (one.id, one.label):
            return one.id
    return decision.choice


# ------------------------------------------------------------------ generation

def envelope(brief):
    """The document block, from facts only (FR-DOC-08)."""
    missing = [name for name in REQUIRED_FACTS if schema.is_empty(brief.get(name))]
    if missing:
        raise IncompleteBrief(
            "the brief states no %s; a vision cannot be authored without it, and "
            "inventing one is the failure this method exists to prevent"
            % ", ".join(missing))

    block = {"title": brief["title"], "slug": SLUG, "type": TYPE,
             "date": brief["date"], "owner": brief["owner"]}
    for name, default in sorted(DEFAULTS.items()):
        block[name] = brief.get(name) or default
    for name in CARRIED:
        if not schema.is_empty(brief.get(name)):
            block[name] = brief[name]
    return block


def generate(brief, run):
    """The vision specification object. Authors nothing until the gate closes.

    Returns the object rather than writing it, so the refusal above can happen
    before any path is resolved and the caller can inspect what would be
    written without writing it.
    """
    run.require_closed()

    block = envelope(brief)
    scope = _decision(run, "scope")
    if scope is not None and _choice(run, "scope") != "product":
        # "The whole product" is the absence of a release scope, not a value for
        # it; anything else — the recommendation, or a release the brief names —
        # is what this document is scoped to.
        block["releaseScope"] = scope.choice

    sections, gaps = [], []
    for section in SECTIONS:
        value = brief.get(section.key)
        if schema.is_empty(value):
            gaps.append(section.gap)
            continue
        built = {"id": section.id, "type": section.type, "title": section.title}
        built.update(section.build(value))
        sections.append(built)

    sources, source_gaps = register(brief)
    gaps.extend(source_gaps)
    if sources:
        sections.append(_register_section(sources))
    else:
        gaps.append("what material this vision was written from")

    locked = run.section()
    if locked is not None:
        sections.append(locked)

    trailing = _gap_section(gaps, _choice(run, "gaps"))
    if trailing is not None:
        sections.append(trailing)

    spec = {"document": block,
            "schemaVersion": schema.SCHEMA_VERSION,
            "sections": sections}
    if sources:
        # The register is carried as data as well as rendered, because the
        # context generator reads it (FR-CTX-01) and reading it back out of
        # table rows would make the column order a contract nobody declared.
        spec["sources"] = sources
    return spec


def render(spec, root="."):
    """The finished document text, styled with the host project's tokens."""
    values, _ = tokens.detect(root)
    return document.render(spec, SPEC_ID,
                           description=spec["document"].get("summary", ""),
                           tokens=tokens.render(values),
                           struct=styles.STRUCT,
                           runtime=runtime.SOURCE)


def write(root, spec):
    """Write the rendered vision into the project. Returns the path written."""
    target = paths.resolve(root, paths.SPECS_DIR, FILENAME)
    writer.write(target, render(spec, root))
    return target


def author(root, brief, run):
    """Gate, ledger, document — in that order. Returns (path, spec).

    The order is the requirement: the locked-decisions table exists in the
    ledger before the first content section is authored (US-DOC-02-S02), and
    nothing at all exists on disk while a fork is open (US-DOC-02-S01).

    The gate is checked once, in `generate`, and `generate` runs before any
    path is resolved. A second check here would read as an extra safeguard
    while being unable to fail, and a guard that cannot fail is a guard nobody
    can tell has stopped working.
    """
    spec = generate(brief, run)

    paths.ensure_layout(root)
    run.record(root)
    return write(root, spec), spec
