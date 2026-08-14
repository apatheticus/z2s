# -*- coding: utf-8 -*-
"""The story generator: what the requirements look like from the outside.

Fifth in the chain. The functional specification says what the system must do,
one testable requirement at a time. This document says who wanted each of those
things and how anyone will know they got it — as goal-level stories, each
carrying Given/When/Then scenarios precise enough to name an automated test
after (FR-TRC-09).

Five rules shape everything below.

  * It runs fifth or not at all. Without a completed functional specification —
    and without the context document beside it — the generator names what is
    missing and leaves the project exactly as it found it.
  * A story that covers no requirement the functional specification counts is
    not written down. It becomes an open question, because a story traceable to
    nothing is either a requirement nobody wrote down or scope arriving through
    the side door (FR-TRC-03). A story covering a requirement the specification
    deliberately excluded is refused for the opposite reason: it is work planned
    against a decision not to build.
  * A story with no scenario is not a story. It states an intention nobody can
    verify, and the whole point of this document is that its contents can be
    turned into tests without further interpretation.
  * A scenario asserts on structure, identifiers and presence — never on the
    exact words a generator produced (FR-DOC-04, M5-P1-T3-C1). Generated wording
    is improved constantly without the behaviour changing, and a suite that
    fails when a sentence is reworded is a suite people learn to ignore. A
    quoted phrase of three or more words is where that mistake actually gets
    written, so that is what is refused (M5-03).
  * A requirement no story covers is named, not silently tolerated (M5-02). It
    is filed the same way every other silence in this chain is — as a question
    against the document, which is still written.

Scenario identifiers are derived, never authored: the nth scenario of US-DOC-01
is US-DOC-01-S01. Derived means unique by construction rather than by an author
remembering (M5-P1-T2-C1), and stable, because it is a function of a position
that only changes when someone reorders the document on purpose.

The document is also its own source. `regenerate` re-renders it from the
specification embedded in it, so an update is made by editing that specification
and re-rendering, never by editing rendered markup (FR-DOC-06, ADR-02).

The brief is a plain dictionary:

    {"title": ..., "owner": ..., "date": "2026-08-14",       # required facts
     "version": ..., "status": ..., "summary": ...,          # optional
     "scopeNote": ..., "releaseScope": ...,                  # optional
     "purpose": "paragraph" | ["paragraph", ...],
     "areas": [{"key": "US-DOC", "name": ..., "description": ...}],
     "stories": [{"area": "US-DOC", "priority": "Must", "role": ...,
                  "title": ..., "narrative": ..., "tags": [...],
                  "testLayers": ["unit", "e2e"],
                  "traces": {"fr": ["FR-DOC-01"]},
                  "scenarios": [{"title": ..., "given": ..., "when": ...,
                                 "then": ...}]}],
     "assumptions": ["...", ...],
     "sources": [{"kind": ..., "name": ..., "origin": ..., "contributed": ...}]}

Traces: FR-DOC-01, FR-DOC-04, FR-DOC-06, FR-DOC-08, FR-DOC-10, FR-CTX-05,
FR-TRC-01, FR-TRC-03, FR-TRC-09, NFR-ARC-01, NFR-ARC-02, NFR-DAT-03,
NFR-DAT-06, NFR-GEN-01, US-DOC-01, US-EXE-02.
"""

import collections
import re

from z2s import chain, context, fsd, gate, paths, schema

SLUG = "stories"
TYPE = "User stories & acceptance criteria"
FILENAME = "Stories.html"
SPEC_ID = SLUG + "-spec"

REQUIRED_FACTS = ("title", "owner", "date")
DEFAULTS = {"version": "1.0", "status": "Draft for review"}
CARRIED = ("summary", "scopeNote", "releaseScope")

#: The three clauses of a scenario, in the order they are read. All three are
#: required: a Given with no Then states a situation and asserts nothing, and a
#: Then with no Given asserts against a state nobody set up.
CLAUSES = ("given", "when", "then")

#: What a story must trace to before it can be written down.
RULE = chain.Rule("fr", "requirement", "story", "covers", "title",
                  "the functional specification does not state")

#: A quoted phrase this long is a sentence being asserted on rather than a term
#: being named (M5-03). Two words is still a field name or a priority band; three
#: is where quoting turns into transcription.
MIN_QUOTED_WORDS = 3

#: Quotation in every form the documents actually use. Bounded so that a stray
#: opening quote cannot make the rest of a paragraph look like one long phrase.
_QUOTED = re.compile(r'"([^"]{1,400})"|“([^”]{1,400})”|`([^`]{1,400})`')

#: Everything that is not a letter or a digit, for comparing an identifier with
#: a test's name. `US-DOC-01-S01` cannot appear literally in a Python function
#: name — hyphens are not legal there — so a check that demanded it would report
#: every correctly named test in the language this toolchain is written in.
_LOOSE = re.compile(r"[^a-z0-9]+")

IncompleteBrief = chain.IncompleteBrief
MissingPrerequisite = chain.MissingPrerequisite


def layers():
    """The closed set a story's verification layers are drawn from (NFR-DAT-04)."""
    return [value["id"] for value in schema.ENUMS["testLayers"]]


def forks(brief):
    """Every fork this brief opens.

    One. The scope comes from the functional specification, the words from the
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
    """The declared areas, in the order the brief declares them (NFR-DAT-03)."""
    return chain.areas(brief, "US-", "story")


# ------------------------------------------------------------------ the sifting

def _current(items, excluded):
    """Stories covering a requirement this release is actually building.

    Separate from the trace rule above it, because the two are different
    mistakes with different fixes. A story citing an identifier nobody assigned
    is a typo or an invention; a story citing a requirement the functional
    specification deliberately excluded is work planned against a decision not to
    build it, and the fix is to reopen the decision or drop the story
    (FR-TRC-06).
    """
    kept, gaps = [], []
    for one in items:
        cited = list((one.get("traces") or {}).get(RULE.kind) or ())
        against = [target for target in cited if target in excluded]
        if against:
            gaps.append("whether the story “%s” should exist at all — it covers %s, "
                        "which the functional specification excludes from this release"
                        % (one["title"], ", ".join(against)))
        else:
            kept.append(one)
    return kept, gaps


def _layered(items):
    """Stories naming the layers that have to pass before they are done.

    Drawn from the closed set rather than from prose: "end-to-end" and "e2e" are
    the same layer to a reader and two different layers to anything counting
    them, and the counting is what a plan later runs on.
    """
    allowed = layers()
    kept, gaps = [], []
    for one in items:
        stated = [layer for layer in one.get("testLayers") or ()
                  if not schema.is_empty(layer)]
        asked = "which verification layers prove the story “%s”" % one["title"]
        unknown = [layer for layer in stated if layer not in allowed]
        if not stated:
            gaps.append(asked)
        elif unknown:
            gaps.append("%s; it names %s, which is not one of %s"
                        % (asked, ", ".join(unknown), ", ".join(allowed)))
        else:
            kept.append(one)
    return kept, gaps


def _scenarised(items):
    """Stories carrying at least one complete Given/When/Then (M5-P1-T1).

    A partial scenario is reported rather than completed. Filling in a missing
    Then is this generator deciding what the story was for, which is the failure
    the whole method exists to prevent.
    """
    kept, gaps = [], []
    for one in items:
        stated = list(one.get("scenarios") or ())
        if not stated:
            gaps.append("how anyone will know the story “%s” works — it states no "
                        "scenario, and a story with no Given, When and Then names no "
                        "test" % one["title"])
            continue

        wrong = []
        for index, scenario in enumerate(stated):
            called = scenario.get("title") or "scenario %d" % (index + 1)
            if schema.is_empty(scenario.get("title")):
                wrong.append("scenario %d states no title" % (index + 1))
            absent = [clause for clause in CLAUSES
                      if schema.is_empty(scenario.get(clause))]
            if absent:
                wrong.append("“%s” states no %s" % (called, ", ".join(absent)))
        if wrong:
            gaps.append("how anyone will know the story “%s” works — %s"
                        % (one["title"], "; ".join(wrong)))
        else:
            kept.append(one)
    return kept, gaps


def quoted_wording(text):
    """Every phrase this wording quotes back at length (M5-03, M5-P1-T3-C1).

    Public because the rule is worth checking outside authoring too: the
    specification embedded in a document is the source, and an editor reaching
    for a quotation has no generator in the way.
    """
    if not isinstance(text, str) or not text:
        return []
    found = []
    for match in _QUOTED.finditer(text):
        for phrase in match.groups():
            if phrase is not None and len(phrase.split()) >= MIN_QUOTED_WORDS:
                found.append(phrase)
    return found


def _structural(items):
    """Scenarios asserting on structure rather than on generated wording.

    The offending phrase is quoted back in the question, because "asserts on
    wording" sends an author looking through three clauses for what they did.
    """
    kept, gaps = [], []
    for one in items:
        offending = []
        for index, scenario in enumerate(one.get("scenarios") or ()):
            called = scenario.get("title") or "scenario %d" % (index + 1)
            for clause in CLAUSES:
                for phrase in quoted_wording(scenario.get(clause)):
                    offending.append("“%s” quotes “%s” in its %s"
                                     % (called, phrase, clause))
        if offending:
            gaps.append("what the story “%s” asserts instead of the wording it quotes "
                        "— %s, and generated wording is reworded without the behaviour "
                        "changing" % (one["title"], "; ".join(offending)))
        else:
            kept.append(one)
    return kept, gaps


# ----------------------------------------------------------------- the sections

def scenario_identifier(story, index):
    """The identifier of the nth scenario of a story, counting from zero.

    Derived rather than authored, so uniqueness is a property of the structure
    instead of something an author has to keep track of (M5-P1-T2-C1).
    """
    if index + 1 > chain.MAX_IDENTIFIED:
        raise IncompleteBrief(
            "more than %d scenarios under %s; the identifier grammar cannot express "
            "%s-S%d, and a malformed identifier breaks every trace to it"
            % (chain.MAX_IDENTIFIED, story, story, index + 1))
    return "%s-S%02d" % (story, index + 1)


def _scenarios(story, stated):
    """One story's scenarios, numbered within it."""
    built = []
    for index, one in enumerate(stated):
        entry = {"id": scenario_identifier(story, index), "title": one["title"]}
        for clause in CLAUSES:
            entry[clause] = one[clause]
        built.append(entry)
    return built


def _entries(stories, declared):
    """The catalogue's entries, grouped by area and numbered within it.

    The same catalogue the functional specification renders, carrying different
    contents: one renderer, one filter, one review pass, whatever the document
    (NFR-ARC-01). The narrative goes in `text` for exactly that reason — it is
    what a reader reads first and what a keyword is matched against.
    """
    built = []
    for area in declared:
        within = [one for one in stories if one["area"] == area["key"]]
        for index, one in enumerate(within):
            identifier = chain.identifier(area["key"], index)
            entry = {"id": identifier,
                     "area": area["key"],
                     "priority": one["priority"],
                     "title": one["title"],
                     "text": one["narrative"],
                     "testLayers": [layer for layer in one["testLayers"]
                                    if not schema.is_empty(layer)],
                     "scenarios": _scenarios(identifier, one["scenarios"])}
            if not schema.is_empty(one.get("role")):
                entry["role"] = one["role"]
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
    """The story catalogue: the section the plan and the test suite both read."""
    occupied = {one["area"] for one in entries}
    counted = sum(len(one["scenarios"]) for one in entries)
    return {"id": "stories", "type": "requirements",
            "title": "Stories",
            "badge": "%d stories · %d scenarios" % (len(entries), counted),
            "lede": "Each story states who wanted the behaviour and why, and carries the "
                    "scenarios that decide whether it works. Every scenario has an "
                    "identifier, and the automated test that defends it is named for "
                    "that identifier.",
            "areas": [chain.area_section(one) for one in declared
                      if one["key"] in occupied],
            "items": entries}


def _section(id, type, title, key, value):
    return {"id": id, "type": type, "title": title, key: value}


# ------------------------------------------------------------------ the reading

def entries(spec):
    """Every story this document states, in the order it states them."""
    found = []
    for section in (spec.get("sections") or ()):
        if section.get("type") == "requirements":
            found.extend(section.get("items") or ())
    return found


def scenarios(spec):
    """Every scenario identifier this document assigns, to its title.

    Ordered, so a report reads in document order rather than in whatever order a
    set happened to hash to.
    """
    found = collections.OrderedDict()
    for story in entries(spec):
        for one in story.get("scenarios") or ():
            found[one["id"]] = one.get("title", "")
    return found


def uncovered(above, spec):
    """Requirements the functional specification counts and no story covers.

    Read from the functional document's own marker rather than from a second
    opinion about which requirements count, so the two cannot disagree about
    what coverage means (FR-TRC-06).
    """
    counted, _ = fsd.universe(above)
    cited = set()
    for story in entries(spec):
        cited.update((story.get("traces") or {}).get(RULE.kind) or ())
    return collections.OrderedDict(
        (identifier, title) for identifier, title in counted.items()
        if identifier not in cited)


def _loose(value):
    """An identifier or a test's name, reduced to what the two can share."""
    return _LOOSE.sub("", (value or "").lower())


def named_tests(spec, names):
    """Which scenarios no test defends, and which tests name no scenario.

    Two lists, deliberately, because they are two different problems: the first
    is a scenario nobody has written a test for, the second is a test nobody can
    trace back to a reason it exists (FR-TRC-01, M5-P1-T2-C2). Reporting them
    together as one count hides whichever is smaller.

    The caller collects the names (M5-04). Whatever language the tests are
    written in, and whatever runner finds them, this stays a comparison.
    """
    wanted = scenarios(spec)
    marks = [(identifier, _loose(identifier)) for identifier in wanted]
    defended, unmatched = set(), []
    for name in names:
        flat = _loose(name)
        hit = [identifier for identifier, mark in marks if mark and mark in flat]
        if hit:
            defended.update(hit)
        else:
            unmatched.append(name)
    return [identifier for identifier in wanted if identifier not in defended], unmatched


# ------------------------------------------------------------------ generation

def envelope(brief):
    """The document block, from facts only (FR-DOC-08)."""
    return chain.envelope(brief, SLUG, TYPE, REQUIRED_FACTS, DEFAULTS, CARRIED)


def generate(brief, run, root="."):
    """The story document object. Writes nothing.

    The gate is checked before either document above is looked for: an open fork
    stops the run whatever else is wrong, and an operator told about a missing
    file when the real problem is an unanswered question fixes the wrong thing.
    """
    run.require_closed()
    above = chain.require(root, fsd.FILENAME, fsd.SLUG, "the story generator")
    words = chain.require(root, context.FILENAME, context.SLUG, "the story generator")

    block = envelope(brief)
    declared = areas(brief)
    counted, excluded = fsd.universe(above)
    known = set(counted) | set(excluded)

    sections, gaps = [], []

    purpose = brief.get("purpose")
    if schema.is_empty(purpose):
        gaps.append("who this system is for, and what they are trying to get done")
    else:
        sections.append(_section("purpose", "prose", "Purpose", "body",
                                 [purpose] if isinstance(purpose, str) else list(purpose)))

    # ---- the catalogue, sifted one rule at a time
    stated = chain.named(brief.get("stories"), "title", "story")

    for sift in (lambda kept: chain.placed(kept, declared, "story"),
                 lambda kept: chain.prioritised(kept, "story"),
                 lambda kept: chain.complete(
                     kept, "narrative", "title",
                     "how the story “%s” reads as a sentence — who wants it, what they "
                     "want, and what it gets them"),
                 _layered,
                 lambda kept: chain.traced(kept, RULE, known),
                 lambda kept: _current(kept, excluded),
                 _scenarised,
                 _structural):
        stated, found = sift(stated)
        gaps.extend(found)

    built = _entries(stated, declared)
    if built:
        sections.append(_catalogue(declared, built))
    else:
        gaps.append("what anybody wants this system for at all")

    # ---- what the functional specification asked for and nothing here covers
    for identifier, title in uncovered(above, {"sections": sections}).items():
        # A noun phrase, not a sentence: every gap is filed inside "The brief says
        # nothing about ___. What should it say?", and a clause that reads on its
        # own reads badly once it is in there.
        gaps.append("which story covers %s, “%s”, which the functional specification "
                    "requires and nothing here proves" % (identifier, title))

    assumed = [one for one in brief.get("assumptions") or () if not schema.is_empty(one)]
    if assumed:
        sections.append(_section("assumptions", "list", "Assumptions", "items", assumed))

    sources, source_gaps = chain.register(brief)
    gaps.extend(source_gaps)
    if sources:
        sections.append(chain.register_section(sources))
    else:
        gaps.append("what material these stories were written from")

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
    """Write the rendered story document into the project."""
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
