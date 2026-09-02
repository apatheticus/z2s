# -*- coding: utf-8 -*-
"""The product-requirements generator: what this must achieve, and how it fails.

Third in the chain. The intent says what the world looks like once this works;
the context document agrees what the words mean; this document turns both into
things that can be argued about and, later, missed — goals, the non-goals that
protect them, the journeys they serve, the measures that decide whether they
happened, and the risks to all of it.

Four rules shape everything below.

  * It runs third or not at all. Without a completed context document — and
    without the intent underneath it — the generator names what is missing and
    leaves the project exactly as it found it (US-SKL-01-S02).
  * A goal that serves no capability the intent states is not written down. It
    becomes an open question, because a goal traceable to nothing is either a
    goal the intent forgot or scope arriving through the side door (FR-TRC-03).
    The same rule holds a journey to a capability, and a measure and a risk to
    a goal.
  * A goal nobody measures is recorded as a gap. A goal that cannot fail is
    decoration, and decoration in a requirements document is how a release ends
    up meeting every goal and satisfying nobody.
  * The document speaks the agreed language: a synonym the context document
    retired does not survive into this one (FR-CTX-05).

The document is also its own source. `regenerate` re-renders it from the
specification embedded in it, so an update is made by editing that
specification and re-rendering, never by editing rendered markup (FR-DOC-06,
ADR-02).

The brief is a plain dictionary:

    {"title": ..., "owner": ..., "date": "2026-08-14",       # required facts
     "version": ..., "status": ..., "summary": ...,          # optional
     "purpose": "paragraph" | ["paragraph", ...],
     "goals":     [{"text": ..., "traces": {"cap": ["VC-01"]}}],
     "nonGoals":  [{"text": ...}],
     "journeys":  [{"title": ..., "persona": ..., "steps": [...],
                    "traces": {"cap": [...]}}],
     "measures":  [{"name": ..., "kind": ..., "target": ...,
                    "traces": {"goal": ["G-01"]}}],
     "dependencies": ["...", ...],
     "assumptions":  ["...", ...],
     "risks":     [{"risk": ..., "mitigation": ...,
                    "traces": {"goal": ["G-01"]}}],
     "sources":   [{"kind": ..., "name": ..., "origin": ..., "contributed": ...}]}

Traces: FR-DOC-01, FR-DOC-04, FR-DOC-06, FR-DOC-08, FR-DOC-10, FR-CTX-05,
FR-TRC-03, NFR-ARC-01, NFR-ARC-02, NFR-DAT-03, NFR-DAT-06, NFR-GEN-01,
US-DOC-01, US-SPC-01.
"""

from z2s import chain, context, gate, paths, schema, intent

SLUG = "prd"
TYPE = "Product Requirements Document (PRD)"
FILENAME = "PRD.html"
SPEC_ID = SLUG + "-spec"

REQUIRED_FACTS = ("title", "owner", "date")
DEFAULTS = {"version": "1.0", "status": "Draft for review"}
CARRIED = ("summary",)

IncompleteBrief = chain.IncompleteBrief
MissingPrerequisite = chain.MissingPrerequisite


# --------------------------------------------------------------- the trace rules

#: What each part of this document must trace to. The shape is the chain's
#: (`chain.Rule`); which four rules a PRD has is this document's own business.
Rule = chain.Rule

RULES = {
    "goals": Rule("cap", "capability", "goal", "serves", "text",
                  "the intent does not state"),
    "journeys": Rule("cap", "capability", "journey", "serves", "title",
                     "the intent does not state"),
    "measures": Rule("goal", "goal", "measure", "measures", "name",
                     "this document does not state"),
    "risks": Rule("goal", "goal", "risk", "threatens", "risk",
                  "this document does not state"),
}


def forks(brief):
    """Every fork this brief opens.

    One. The PRD inherits its scope from the intent and its words from the
    context document, so the only thing left to decide is what to do where the
    brief says nothing.
    """
    return (chain.gaps_fork("brief"),)


def open_gate(brief, root=None):
    """The gate this generator runs, over whatever is already known."""
    decisions = gate.load(root, SLUG) if root is not None else ()
    return gate.Gate(SLUG, forks(brief), source=brief, decisions=decisions)


# ------------------------------------------------------------------ the sifting
#
# The sifting itself belongs to the chain: every document below the intent drops
# an entry it cannot justify and records the drop as a question, and two copies
# of that rule is how two documents come to disagree about it (NFR-ARC-01).

_named = chain.named
_traced = chain.traced
_complete = chain.complete
identified = chain.identified


# ----------------------------------------------------------------- the sections

def _definitions(prefix, entries, term, definition):
    """Numbered definition-list items.

    The identifier is carried twice from one assignment, as the intent does with
    its capabilities: as data, so a later document can trace to it, and inside
    the term, because the runtime renders a definition list's term and
    definition and never its identifier.
    """
    out = []
    for index, one in enumerate(entries):
        identifier = chain.identifier(prefix, index)
        built = {"id": identifier, "term": term(identifier, one),
                 "definition": definition(one)}
        found = chain.traces(one)
        if found:
            built["traces"] = found
        out.append(built)
    return out


def _section(id, type, title, key, value):
    return {"id": id, "type": type, "title": title, key: value}


def _measure_cards(entries):
    """One card per measure: what is counted, and what the answer has to be."""
    cards = []
    for index, one in enumerate(entries):
        identifier = chain.identifier("MT", index)
        kind = one.get("kind")
        card = {"id": identifier,
                "title": "%s · %s" % (identifier, one["name"]),
                "body": ("%s measure. Target: %s." % (kind, one["target"])) if kind
                        else ("Target: %s." % one["target"])}
        found = chain.traces(one)
        if found:
            card["traces"] = found
        cards.append(card)
    return cards


def _journey(index, one):
    """One journey, as the ordered walk-through it is.

    A journey is a sequence, so it renders as one — its own section, its steps
    in order. The persona rides in the title rather than in a field of its own:
    the runtime renders a section's title and its steps, and a fact carried
    where nothing displays it is a fact nobody reads.
    """
    identifier = chain.identifier("J", index)
    title = "%s · %s" % (identifier, one["title"])
    if one.get("persona"):
        title = "%s — %s" % (title, one["persona"])

    section = {"id": identifier, "type": "flow", "title": title,
               "steps": [{"body": step} for step in one["steps"]]}
    found = chain.traces(one)
    if found:
        section["traces"] = found
    return section


def _unmeasured(goals, measures):
    """Goals no measure names (FR-TRC-03).

    A goal that cannot fail is decoration. This does not invent a measure for
    it — that would be the fabrication the method exists to prevent — it says
    out loud which goal nobody has agreed how to judge.
    """
    counted = set()
    for one in measures:
        counted.update((one.get("traces") or {}).get("goal") or ())
    return ["how the goal %s will be measured" % one["id"]
            for one in goals if one["id"] not in counted]


# ------------------------------------------------------------------ generation

def envelope(brief):
    """The document block, from facts only (FR-DOC-08)."""
    return chain.envelope(brief, SLUG, TYPE, REQUIRED_FACTS, DEFAULTS, CARRIED)


def generate(brief, run, root="."):
    """The product-requirements specification object. Writes nothing.

    The gate is checked before either document above is looked for: an open fork
    stops the run whatever else is wrong, and an operator told about a missing
    file when the real problem is an unanswered question fixes the wrong thing.
    """
    run.require_closed()
    above = chain.require(root, context.FILENAME, context.SLUG,
                          "the product-requirements generator", shared=True)
    upstream = chain.require(root, intent.FILENAME, intent.SLUG,
                             "the product-requirements generator")

    block = envelope(brief)
    capabilities = identified(upstream, "capability")

    sections, gaps = [], []

    purpose = brief.get("purpose")
    if schema.is_empty(purpose):
        gaps.append("what this product must achieve and why now")
    else:
        sections.append(_section("purpose", "prose", "Purpose", "body",
                                 [purpose] if isinstance(purpose, str) else list(purpose)))

    # ---- goals, and the capabilities they serve
    stated, goal_gaps = _traced(_named(brief.get("goals"), "text", "goal"),
                                RULES["goals"], capabilities)
    gaps.extend(goal_gaps)
    goals = _definitions("G", stated, lambda identifier, one: identifier,
                         lambda one: one["text"])
    if goals:
        sections.append(_section("goals", "definitions", "Goals", "items", goals))
    else:
        gaps.append("what this product must achieve")

    # ---- non-goals: the scope this release is deliberately not taking
    refused = _definitions("NG", _named(brief.get("nonGoals"), "text", "non-goal"),
                           lambda identifier, one: identifier, lambda one: one["text"])
    if refused:
        sections.append(_section("non-goals", "definitions", "Non-goals", "items", refused))
    else:
        gaps.append("what this product deliberately will not do")

    # ---- journeys, one ordered walk-through each
    stated, journey_gaps = _traced(_named(brief.get("journeys"), "title", "journey"),
                                   RULES["journeys"], capabilities)
    gaps.extend(journey_gaps)
    stated, step_gaps = _complete(stated, "steps", "title",
                                  "what steps the journey “%s” walks through")
    gaps.extend(step_gaps)
    for index, one in enumerate(stated):
        sections.append(_journey(index, one))
    if not stated:
        gaps.append("what journey anyone takes through this")

    # ---- measures: what decides whether a goal happened
    known = {one["id"] for one in goals}
    stated, measure_gaps = _traced(_named(brief.get("measures"), "name", "measure"),
                                   RULES["measures"], known)
    gaps.extend(measure_gaps)
    stated, target_gaps = _complete(stated, "target", "name",
                                    "what target the measure “%s” must hit")
    gaps.extend(target_gaps)
    measures = _measure_cards(stated)
    if measures:
        sections.append(_section("measures", "cards", "Measurable outcomes",
                                 "items", measures))
    gaps.extend(_unmeasured(goals, stated))

    # ---- what this rests on, and what it takes on trust
    depends = [one for one in brief.get("dependencies") or () if not schema.is_empty(one)]
    if depends:
        sections.append(_section("dependencies", "list", "Dependencies", "items", depends))
    else:
        gaps.append("what this work depends on outside itself")

    assumed = [one for one in brief.get("assumptions") or () if not schema.is_empty(one)]
    if assumed:
        sections.append(_section("assumptions", "list", "Assumptions", "items", assumed))

    # ---- risks, and what is being done about each
    stated, risk_gaps = _traced(_named(brief.get("risks"), "risk", "risk"),
                                RULES["risks"], known)
    gaps.extend(risk_gaps)
    stated, response_gaps = _complete(stated, "mitigation", "risk",
                                      "how the risk “%s” will be handled")
    gaps.extend(response_gaps)
    risks = _definitions("RK", stated,
                         lambda identifier, one: "%s · %s" % (identifier, one["risk"]),
                         lambda one: one["mitigation"])
    if risks:
        sections.append(_section("risks", "definitions", "Risks and responses",
                                 "items", risks))
    else:
        gaps.append("what could stop this working")

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
    return context.consult(spec, context.glossary(above))


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
    """Write the rendered product-requirements document into the project."""
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
