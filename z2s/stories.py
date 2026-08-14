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
    against the document, which is still written. A use case counts as cover:
    a flow that spans four stories still proves what it traces to.
  * What holds for every story is stated once and referenced (M5-P2-T2). A story
    that writes a global check out again keeps its place and loses the line —
    the one rule here that does not refuse what it flags, because refusing it
    would trade a duplicated sentence for an uncovered requirement (M5-06). A
    story may be exempt from a global check, but only by naming it and saying
    why.

Some interactions are not a story at all: they cross several of them, and what
needs specifying is the interaction rather than any one capability in it. Those
are use cases (UC-nn) — actor, trigger, preconditions, a main flow, alternates,
exceptions and a guaranteed postcondition, every one required (M5-P2-T1-C1).
They are optional; a project with none simply has none.

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
     "acceptance": ["what holds for every story below", ...],
     "stories": [{"area": "US-DOC", "priority": "Must", "role": ...,
                  "title": ..., "narrative": ..., "tags": [...],
                  "testLayers": ["unit", "e2e"],
                  "traces": {"fr": ["FR-DOC-01"]},
                  "verify": ["what this story needs beyond the global list"],
                  "waives": [{"assertion": ..., "reason": ...}],
                  "scenarios": [{"title": ..., "given": ..., "when": ...,
                                 "then": ...}]}],
     "useCases": [{"priority": "Must", "title": ..., "actor": ...,
                   "goal": ..., "trigger": ..., "post": ...,
                   "pre": [...], "main": [...], "alt": [...], "exc": [...],
                   "traces": {"fr": ["FR-EXE-01"]}}],
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
TYPE = "User stories, use cases & acceptance criteria"
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

#: The same rule for a use case. Written out rather than shared with a swapped
#: noun, because the two sentences a reader is shown differ in more than the
#: noun and a format string with three holes in it is harder to read than two
#: declarations.
CASE_RULE = chain.Rule("fr", "requirement", "use case", "covers", "title",
                       "the functional specification does not state")

#: What a use case must carry, and what a reader is asked when it does not
#: (M5-P2-T1-C1). Every one is named in this phase's own completion criteria,
#: and each absence is a different hole: no actor is a flow nobody performs, no
#: trigger is a flow that never starts, and no exception path is a flow nobody
#: has thought about failing.
#:
#: A noun phrase each, because every gap is filed inside "The brief says nothing
#: about ___. What should it say?".
FLOWS = collections.OrderedDict((
    ("actor", "who performs the use case “%s”"),
    ("trigger", "what starts the use case “%s”"),
    ("pre", "what has to be true before the use case “%s” can run"),
    ("main", "the steps of the use case “%s”"),
    ("alt", "the other ways the use case “%s” can legitimately run"),
    ("exc", "what the use case “%s” does when something goes wrong"),
    ("post", "what is guaranteed once the use case “%s” has finished"),
))

#: A use case's single-sentence parts, as opposed to its lists of steps.
CASE_FACTS = ("actor", "goal", "trigger", "post")
CASE_STEPS = ("pre", "main", "alt", "exc")

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

def _current(items, excluded, noun="story"):
    """Entries covering a requirement this release is actually building.

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
            gaps.append("whether the %s “%s” should exist at all — it covers %s, "
                        "which the functional specification excludes from this release"
                        % (noun, one["title"], ", ".join(against)))
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


# ------------------------------------------------------- the global acceptance

def agreed(brief):
    """The assertions that hold for every story, stated once (M5-P2-T2).

    Stated once and referenced, rather than copied into each story, because the
    copies are what drift: a document with the same assertion written into
    fourteen stories has fourteen chances to say it differently and no way to
    tell which one is current.
    """
    return [one for one in brief.get("acceptance") or () if not schema.is_empty(one)]


def _repeated(items, global_checks):
    """Stories restating something this document already states for all of them.

    The one sift here that keeps what it flags (M5-06). Everywhere else a
    rejected entry leaves the document and becomes a question; here the story
    still covers its requirement, and refusing it would trade one duplicated
    line for one uncovered requirement. So the line goes, the story stays, and
    the question names exactly what was repeated.

    Matched on the words rather than on the characters: a full stop or a
    capital letter is not a different assertion. A partial restatement — half a
    global check, reworded — is not caught, and is left to a reader; a looser
    match here would start reporting stories that merely share a subject.
    """
    marks = {_loose(one) for one in global_checks}
    kept, gaps = [], []
    for one in items:
        stated = [line for line in one.get("verify") or ()
                  if not schema.is_empty(line)]
        repeats = [line for line in stated if _loose(line) in marks]
        if repeats:
            one = dict(one, verify=[line for line in stated if _loose(line) not in marks])
            for line in repeats:
                gaps.append("why the story “%s” restates the global check “%s”; it is "
                            "already stated once for every story, and a second copy is "
                            "a copy that can drift" % (one["title"], line))
        kept.append(one)
    return kept, gaps


def _waived(items, global_checks):
    """Stories exempting themselves from a global assertion, on the record.

    A story is allowed to be the exception. It is not allowed to be the
    exception quietly: an opt-out with no reason recorded is the failure this
    method exists to prevent, written in the one place that looks like
    diligence. As with a repeat, the story itself survives — the bad waiver
    becomes a question and the story keeps covering its requirement.
    """
    marks = {_loose(one) for one in global_checks}
    kept, gaps = [], []
    for one in items:
        stated = list(one.get("waives") or ())
        allowed = []
        for waiver in stated:
            assertion = waiver.get("assertion")
            if schema.is_empty(assertion):
                gaps.append("which global check the story “%s” is exempt from"
                            % one["title"])
            elif _loose(assertion) not in marks:
                gaps.append("which global check the story “%s” is exempt from; it names "
                            "“%s”, which this document does not state for every story"
                            % (one["title"], assertion))
            elif schema.is_empty(waiver.get("reason")):
                gaps.append("why the story “%s” is exempt from the global check “%s”"
                            % (one["title"], assertion))
            else:
                allowed.append({"assertion": assertion, "reason": waiver["reason"]})
        if stated:
            one = dict(one, waives=allowed)
        kept.append(one)
    return kept, gaps


def _acceptance_section(global_checks):
    return {"id": "acceptance", "type": "list", "title": "Global acceptance",
            "lede": "These hold for every story below, unless a story records an "
                    "exemption and the reason for it. They are proved once per "
                    "surface — never re-authored inside each story, where the copies "
                    "would drift apart.",
            "items": list(global_checks)}


# ---------------------------------------------------------------- the use cases

def _flowing(items):
    """Use cases carrying every part of a flow (M5-P2-T1-C1).

    One question per missing part rather than one listing them all: each part is
    a separate thing to go and find out, and a question that asks for seven
    answers at once gets one.
    """
    kept, gaps = [], []
    for one in items:
        absent = [part for part in FLOWS if schema.is_empty(one.get(part))]
        for part in absent:
            gaps.append(FLOWS[part] % one["title"])
        if not absent:
            kept.append(one)
    return kept, gaps


def _case_entries(cases):
    """The use cases, numbered in the order the brief states them.

    Flat, with no areas: a use case identifier is `UC-01` and nothing else
    (NFR-DAT-03). They are few, and they cross the areas by definition — an
    actor-centred flow that fitted inside one area would have been a story.
    """
    built = []
    for index, one in enumerate(cases):
        entry = {"id": chain.identifier("UC", index),
                 "priority": one["priority"],
                 "title": one["title"]}
        for part in CASE_FACTS:
            if not schema.is_empty(one.get(part)):
                entry[part] = one[part]
        for part in CASE_STEPS:
            stated = [step for step in one.get(part) or ()
                      if not schema.is_empty(step)]
            if stated:
                entry[part] = stated
        found = chain.traces(one)
        if found:
            entry["traces"] = found
        built.append(entry)
    return built


def _case_catalogue(entries):
    """The use cases, in the same catalogue the stories use (M5-05).

    The same section type, so the toolbar, the keyword filter, the priority
    bands, the deep links and the review ticks all reach them without a second
    implementation of any of it (NFR-ARC-01). What differs is what is inside an
    entry, which is what a renderer is for.
    """
    return {"id": "usecases", "type": "requirements",
            "title": "Use cases",
            "badge": "%d use cases" % len(entries),
            "lede": "Actor-centred flows that run across several stories, where the "
                    "interaction is what needs specifying rather than any one "
                    "capability in it.",
            "items": entries}


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
            # What this story needs proved beyond the global list, and what it
            # is exempt from. Both are absent rather than empty when there is
            # nothing to say (NFR-DAT-06) — a story whose only "also verify"
            # line was a repeat of a global one is left with no such heading.
            extra = [line for line in one.get("verify") or ()
                     if not schema.is_empty(line)]
            if extra:
                entry["verify"] = extra
            waived = list(one.get("waives") or ())
            if waived:
                entry["waives"] = waived
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

def _items(spec, section_id):
    """One catalogue's entries, by the section that holds them.

    By section rather than by type, because this document now renders two
    catalogues of the same type and a reader asking for the stories does not
    want the use cases counted among them.
    """
    found = []
    for section in (spec.get("sections") or ()):
        if section.get("id") == section_id and section.get("type") == "requirements":
            found.extend(section.get("items") or ())
    return found


def entries(spec):
    """Every story this document states, in the order it states them."""
    return _items(spec, "stories")


def use_cases(spec):
    """Every use case this document states, in the order it states them."""
    return _items(spec, "usecases")


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
    """Requirements the functional specification counts and nothing here covers.

    Read from the functional document's own marker rather than from a second
    opinion about which requirements count, so the two cannot disagree about
    what coverage means (FR-TRC-06).

    A use case counts as cover, exactly as a story does: the method's own gate
    is that every requirement not explicitly excluded is covered by at least one
    story **or use case**, and a requirement proved by a flow that spans four
    stories is proved.
    """
    counted, _ = fsd.universe(above)
    cited = set()
    for story in entries(spec) + use_cases(spec):
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

    # ---- what holds for every story, stated once and then referenced
    global_checks = agreed(brief)
    if global_checks:
        sections.append(_acceptance_section(global_checks))
    else:
        gaps.append("which checks hold for every story, rather than being written out "
                    "again inside each of them")

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
                 _structural,
                 # Last of the story sifts, and the only pair that keeps what it
                 # flags: by here the story has earned its place, and what is
                 # wrong with it is one line rather than the whole entry (M5-06).
                 lambda kept: _repeated(kept, global_checks),
                 lambda kept: _waived(kept, global_checks)):
        stated, found = sift(stated)
        gaps.extend(found)

    built = _entries(stated, declared)
    if built:
        sections.append(_catalogue(declared, built))
    else:
        gaps.append("what anybody wants this system for at all")

    # ---- the flows no single story can carry
    cases = chain.named(brief.get("useCases"), "title", "use case")
    for sift in (lambda kept: chain.prioritised(kept, "use case"),
                 _flowing,
                 lambda kept: chain.traced(kept, CASE_RULE, known),
                 lambda kept: _current(kept, excluded, "use case")):
        cases, found = sift(cases)
        gaps.extend(found)

    if cases:
        sections.append(_case_catalogue(_case_entries(cases)))

    # ---- what the functional specification asked for and nothing here covers
    for identifier, title in uncovered(above, {"sections": sections}).items():
        # A noun phrase, not a sentence: every gap is filed inside "The brief says
        # nothing about ___. What should it say?", and a clause that reads on its
        # own reads badly once it is in there.
        gaps.append("which story or use case covers %s, “%s”, which the functional "
                    "specification requires and nothing here proves"
                    % (identifier, title))

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
