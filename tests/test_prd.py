# -*- coding: utf-8 -*-
"""The product-requirements generator: what it needs, what it drops, what it says.

Four claims are load-bearing here, each checked against the thing that would
actually break rather than against a description of it:

  · the document above must exist. Without a completed context — and without the
    intent underneath it — the generator names what is missing and leaves the
    project untouched (FR-CTX-01, US-SKL-01-S02)
  · every goal traces to a capability the intent actually states. A goal citing
    nothing, or citing a capability that does not exist, is an open question
    rather than an entry (FR-TRC-03, M3-P3-T1-C2)
  · a goal nobody can measure is recorded as a gap, because a goal that cannot
    fail is decoration
  · the document speaks the agreed language, and can be regenerated from its own
    embedded specification with nothing else changed (FR-CTX-05, FR-DOC-06,
    US-SPC-01-S03)

Traces: FR-DOC-01, FR-DOC-04, FR-DOC-06, FR-DOC-08, FR-DOC-10, FR-TRC-03,
NFR-ARC-01, NFR-DAT-03, NFR-DAT-06, NFR-GEN-01, US-DOC-01, US-SPC-01.
"""

import ast
import copy
import os
import shutil
import tempfile
import unittest

from z2s import chain, context, gate, paths, prd, schema, validate, intent

#: Anything that could read the clock, which would make two runs of unchanged
#: input differ (NFR-GEN-01).
CLOCK = ("time", "datetime", "calendar", "random", "uuid")


def imports(source):
    """Every module name a source file imports, wherever the import sits."""
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split(".")[0])
            found.update(alias.name for alias in node.names)
    return found


# ------------------------------------------------------------------ fixtures

def intent_brief(**extra):
    made = {"title": "Kestrel", "owner": "A. Owner", "date": "2026-08-14",
            "statement": "Every document in one voice.",
            "capabilities": [{"title": "Record a source", "body": "Keep what was consulted."},
                             {"title": "Speak one language",
                              "body": "One word, one meaning, everywhere after."}],
            "sources": [{"kind": "narrative", "name": "Kick-off conversation",
                         "origin": "Recorded 2026-08-01",
                         "contributed": "The problem and the vocabulary."}]}
    made.update(extra)
    return made


def context_brief(**extra):
    made = {"title": "Kestrel — the domain", "owner": "A. Owner", "date": "2026-08-14",
            "overview": "What the words in this project mean.",
            "contexts": [{"name": "Authoring", "body": "Where documents are written."}],
            "terms": [{"term": "Brief", "definition": "The material a generator is handed.",
                       "source": "Kick-off conversation", "context": "Authoring",
                       "synonyms": ["input pack"]}],
            "sources": [{"kind": "narrative", "name": "Kick-off conversation",
                         "origin": "Recorded 2026-08-01", "contributed": "The vocabulary."}]}
    made.update(extra)
    return made


def prd_brief(**extra):
    made = {"title": "Kestrel — product requirements", "owner": "A. Owner",
            "date": "2026-08-14",
            "purpose": "What Kestrel must achieve before it ships.",
            "goals": [{"text": "Make an unsourced claim impossible to publish.",
                       "traces": {"cap": ["VC-01"]}},
                      {"text": "Let two readers of one document mean the same thing.",
                       "traces": {"cap": ["VC-02"]}}],
            "nonGoals": [{"text": "Not a hosted service; files in a repository."}],
            "journeys": [{"title": "Brief to a stable document set", "persona": "Author",
                          "steps": ["Bring the input pack.",
                                    "Answer the gate once.",
                                    "Generate and validate each document."],
                          "traces": {"cap": ["VC-01", "VC-02"]}}],
            "measures": [{"name": "Claims published with no source", "kind": "Outcome",
                          "target": "Zero", "traces": {"goal": ["G-01"]}},
                         {"name": "Words carrying two meanings", "kind": "Structural",
                          "target": "Zero", "traces": {"goal": ["G-02"]}}],
            "dependencies": ["A version-control system whose history is the audit trail."],
            "assumptions": ["Someone is accountable for answering the gate."],
            "risks": [{"risk": "The gate is answered without reading it.",
                       "mitigation": "One question at a time, each with a recommendation.",
                       "traces": {"goal": ["G-01"]}}],
            "sources": [{"kind": "narrative", "name": "Kick-off conversation",
                         "origin": "Recorded 2026-08-01", "contributed": "The goals."}]}
    made.update(extra)
    return made


def closed(run, **answers):
    """Close every open fork, taking the recommendation where the test is silent."""
    while True:
        question = run.question()
        if question is None:
            return run
        run.answer(question.id, answers.get(question.id, question.recommended.id),
                   "Chosen by the test.")


def gate_for(brief, **answers):
    return closed(gate.Gate(prd.SLUG, prd.forks(brief), source=brief), **answers)


def sections(spec):
    return dict((section["id"], section) for section in spec["sections"])


def items_of(spec, section_id):
    found = sections(spec).get(section_id)
    return found["items"] if found else []


def strings(node):
    """Every string anywhere in a specification object."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key in sorted(node):
            for found in strings(node[key]):
                yield found
    elif isinstance(node, list):
        for item in node:
            for found in strings(item):
                yield found


def gaps_of(spec):
    """Whatever the document recorded as silence, however it was filed."""
    found = sections(spec)
    return (found.get("open-questions") or found.get("assumptions") or {}).get("items", [])


class Sandbox(unittest.TestCase):
    """A project root that starts genuinely empty."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-prd-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def author_intent(self, **extra):
        brief = intent_brief(**extra)
        run = closed(gate.Gate(intent.SLUG, intent.FORKS, source=brief))
        return intent.author(self.root, brief, run)[0]

    def author_context(self, **extra):
        brief = context_brief(**extra)
        run = closed(gate.Gate(context.SLUG, context.forks(brief), source=brief))
        return context.author(self.root, brief, run)[0]

    def chain_above(self):
        self.author_intent()
        self.author_context()

    def generate(self, brief=None, **answers):
        made = prd_brief() if brief is None else brief
        return prd.generate(made, gate_for(made, **answers), self.root)

    def author(self, brief=None, **answers):
        made = prd_brief() if brief is None else brief
        return prd.author(self.root, made, gate_for(made, **answers))


# ------------------------------------------------------- the documents above

class TestTheChainAbove(Sandbox):
    """M3-P3-T1: the PRD is third in the chain and says so when it is first."""

    def test_an_empty_project_is_refused_by_name(self):
        with self.assertRaises(chain.MissingPrerequisite) as caught:
            self.generate()
        said = str(caught.exception)
        self.assertIn("context", said)
        self.assertIn(context.FILENAME, said)

    def test_a_intent_alone_is_not_enough(self):
        self.author_intent()
        with self.assertRaises(chain.MissingPrerequisite) as caught:
            self.generate()
        self.assertIn(context.FILENAME, str(caught.exception))

    def test_a_context_without_its_intent_is_refused(self):
        self.chain_above()
        os.remove(paths.resolve(self.root, paths.SPECS_DIR, intent.FILENAME))
        with self.assertRaises(chain.MissingPrerequisite) as caught:
            self.generate()
        self.assertIn(intent.FILENAME, str(caught.exception))

    def test_the_refusal_writes_nothing(self):
        with self.assertRaises(chain.MissingPrerequisite):
            self.author()
        self.assertEqual(os.listdir(self.root), [])

    def test_the_gate_refuses_before_the_chain_is_looked_for(self):
        # An open fork stops the run whatever else is wrong, so a half-answered
        # project is never told its problem is a missing file.
        brief = prd_brief()
        run = gate.Gate(prd.SLUG, prd.forks(brief), source=brief)
        with self.assertRaises(gate.GateNotClosed):
            prd.generate(brief, run, self.root)

    def test_a_document_of_the_wrong_kind_is_not_a_context(self):
        self.author_intent()
        target = paths.resolve(self.root, paths.SPECS_DIR, context.FILENAME)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("<script type=\"application/json\">"
                         "{\"document\": {\"slug\": \"fsd\"}}</script>")
        with self.assertRaises(chain.MissingPrerequisite) as caught:
            self.generate()
        self.assertIn("fsd", str(caught.exception))

    def test_a_complete_chain_is_enough(self):
        self.chain_above()
        spec = self.generate()
        self.assertEqual(spec["document"]["slug"], prd.SLUG)
        self.assertEqual(spec["schemaVersion"], schema.SCHEMA_VERSION)


# ------------------------------------------------------------------- the goals

class TestEveryGoalServesACapability(Sandbox):
    """M3-P3-T1-C2: every goal traces to a capability that exists."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_goals_are_numbered_in_the_order_the_brief_states_them(self):
        spec = self.generate()
        self.assertEqual([one["id"] for one in items_of(spec, "goals")], ["G-01", "G-02"])

    def test_a_reader_can_see_the_identifier_a_trace_cites(self):
        # The runtime renders a definition list's term, not its identifier, so
        # the identifier has to be in the term as well as in the data.
        for one in items_of(self.generate(), "goals"):
            self.assertIn(one["id"], one["term"])

    def test_every_goal_names_a_capability_the_intent_states(self):
        spec = self.generate()
        stated = {entry["id"] for _, entry in schema.entries(
            chain.require(self.root, intent.FILENAME, intent.SLUG, "the test"))
            if schema.kind_of(entry.get("id")) == "capability"}
        self.assertTrue(stated)
        for one in items_of(spec, "goals"):
            cited = one["traces"]["cap"]
            self.assertTrue(cited)
            self.assertTrue(set(cited) <= stated)

    def test_a_goal_citing_a_capability_that_does_not_exist_is_not_an_entry(self):
        brief = prd_brief(goals=[{"text": "Ship on Tuesday.",
                                  "traces": {"cap": ["VC-99"]}}])
        spec = self.generate(brief)
        self.assertEqual(items_of(spec, "goals"), [])
        self.assertTrue(any("VC-99" in gap for gap in gaps_of(spec)))

    def test_a_goal_citing_nothing_is_not_an_entry(self):
        brief = prd_brief(goals=[{"text": "Ship on Tuesday."}])
        spec = self.generate(brief)
        self.assertEqual(items_of(spec, "goals"), [])
        self.assertTrue(any("Ship on Tuesday." in gap for gap in gaps_of(spec)))

    def test_a_dropped_goal_does_not_take_a_number_with_it(self):
        brief = prd_brief(goals=[{"text": "Ship on Tuesday."},
                                 {"text": "Make an unsourced claim impossible.",
                                  "traces": {"cap": ["VC-01"]}}])
        spec = self.generate(brief)
        self.assertEqual([one["id"] for one in items_of(spec, "goals")], ["G-01"])

    def test_a_goal_nobody_measures_is_recorded_as_a_gap(self):
        # A goal that cannot fail is decoration; the document says so rather
        # than inventing a measure for it.
        brief = prd_brief(measures=[{"name": "Claims published with no source",
                                     "kind": "Outcome", "target": "Zero",
                                     "traces": {"goal": ["G-01"]}}])
        spec = self.generate(brief)
        self.assertTrue(any("G-02" in gap and "measure" in gap for gap in gaps_of(spec)))

    def test_a_measured_goal_is_not_recorded_as_a_gap(self):
        spec = self.generate()
        self.assertFalse(any("measure" in gap for gap in gaps_of(spec)))


# ---------------------------------------------------------- the other sections

class TestWhatElseTheDocumentCarries(Sandbox):

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_non_goals_are_numbered_and_kept(self):
        entries = items_of(self.generate(), "non-goals")
        self.assertEqual([one["id"] for one in entries], ["NG-01"])
        self.assertIn("hosted service", entries[0]["definition"])

    def test_each_journey_is_its_own_ordered_walk_through(self):
        found = sections(self.generate())
        self.assertIn("J-01", found)
        journey = found["J-01"]
        self.assertEqual(journey["type"], "flow")
        self.assertEqual([step["body"] for step in journey["steps"]],
                         ["Bring the Brief.", "Answer the gate once.",
                          "Generate and validate each document."])

    def test_a_journey_names_who_walks_it(self):
        self.assertIn("Author", sections(self.generate())["J-01"]["title"])

    def test_a_journey_with_no_steps_is_a_gap_not_an_empty_walk_through(self):
        brief = prd_brief(journeys=[{"title": "Someday", "persona": "Author",
                                     "traces": {"cap": ["VC-01"]}}])
        spec = self.generate(brief)
        self.assertNotIn("J-01", sections(spec))
        self.assertTrue(any("steps" in gap and "Someday" in gap
                            for gap in gaps_of(spec)))

    def test_a_journey_serving_no_capability_is_not_walked_through(self):
        brief = prd_brief(journeys=[{"title": "Someday", "persona": "Author",
                                     "steps": ["Wait."]}])
        spec = self.generate(brief)
        self.assertNotIn("J-01", sections(spec))
        self.assertTrue(any("capability" in gap and "Someday" in gap
                            for gap in gaps_of(spec)))

    def test_measures_are_numbered_and_state_their_target(self):
        entries = items_of(self.generate(), "measures")
        self.assertEqual([one["id"] for one in entries], ["MT-01", "MT-02"])
        self.assertIn("Zero", entries[0]["body"])

    def test_a_measure_carries_the_goal_it_measures(self):
        self.assertEqual(items_of(self.generate(), "measures")[0]["traces"]["goal"],
                         ["G-01"])

    def test_dependencies_and_assumptions_are_kept_as_stated(self):
        spec = self.generate()
        self.assertIn("A version-control system whose history is the audit trail.",
                      sections(spec)["dependencies"]["items"])
        self.assertIn("Someone is accountable for answering the gate.",
                      sections(spec)["assumptions"]["items"])

    def test_a_risk_is_kept_with_the_response_to_it(self):
        entries = items_of(self.generate(), "risks")
        self.assertEqual(entries[0]["id"], "RK-01")
        self.assertIn("without reading", entries[0]["term"])
        self.assertIn("One question at a time", entries[0]["definition"])

    def test_a_measure_with_no_target_is_a_gap_not_an_entry(self):
        brief = prd_brief(measures=[{"name": "Claims published with no source",
                                     "traces": {"goal": ["G-01"]}}])
        spec = self.generate(brief)
        self.assertEqual(items_of(spec, "measures"), [])
        self.assertTrue(any("target" in gap and "Claims published" in gap
                            for gap in gaps_of(spec)))

    def test_a_measure_naming_a_goal_that_was_dropped_is_not_an_entry(self):
        # Goals are numbered at generation, so a measure citing G-02 in a brief
        # whose second goal did not survive would otherwise measure whatever
        # took that number.
        brief = prd_brief(goals=[{"text": "Make an unsourced claim impossible.",
                                  "traces": {"cap": ["VC-01"]}}])
        spec = self.generate(brief)
        self.assertEqual([one["id"] for one in items_of(spec, "measures")], ["MT-01"])
        self.assertTrue(any("G-02" in gap for gap in gaps_of(spec)))

    def test_a_risk_with_no_response_is_a_gap_not_an_entry(self):
        brief = prd_brief(risks=[{"risk": "The gate is answered without reading it.",
                                  "traces": {"goal": ["G-01"]}}])
        spec = self.generate(brief)
        self.assertEqual(items_of(spec, "risks"), [])
        self.assertTrue(any("handled" in gap and "without reading" in gap
                            for gap in gaps_of(spec)))

    def test_a_risk_threatening_no_goal_is_not_an_entry(self):
        brief = prd_brief(risks=[{"risk": "The gate is answered without reading it.",
                                  "mitigation": "One question at a time."}])
        spec = self.generate(brief)
        self.assertEqual(items_of(spec, "risks"), [])
        self.assertTrue(any("goal" in gap and "without reading" in gap
                            for gap in gaps_of(spec)))

    def test_an_entry_with_no_words_in_it_is_refused_not_recorded(self):
        # A gap names what the brief is silent about. An entry with nothing in
        # it leaves nothing to name, so it is a malformed brief, not a silence.
        with self.assertRaises(chain.IncompleteBrief) as caught:
            self.generate(prd_brief(goals=[{"traces": {"cap": ["VC-01"]}}]))
        self.assertIn("goal 1", str(caught.exception))

    def test_the_source_register_survives_into_the_specification(self):
        spec = self.generate()
        self.assertEqual(spec["sources"][0]["name"], "Kick-off conversation")


# ----------------------------------------------------------------- the silence

class TestSilenceIsRecordedNeverFilled(Sandbox):
    """FR-DOC-04, NFR-DAT-06: a section with nothing to say is absent."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_a_bare_brief_produces_no_empty_sections(self):
        bare = {"title": "Kestrel", "owner": "A. Owner", "date": "2026-08-14"}
        spec = self.generate(bare)
        for section in spec["sections"]:
            for key in ("items", "steps", "rows", "body"):
                if key in section:
                    self.assertTrue(section[key], section["id"])

    def test_every_silence_is_named(self):
        bare = {"title": "Kestrel", "owner": "A. Owner", "date": "2026-08-14"}
        spec = self.generate(bare)
        said = " ".join(gaps_of(spec))
        for subject in ("must achieve", "deliberately will not do", "journey",
                        "depends on outside itself", "stop this working",
                        "material these requirements were written from"):
            self.assertIn(subject, said)

    def test_the_gate_decides_whether_a_silence_asks_or_assumes(self):
        bare = {"title": "Kestrel", "owner": "A. Owner", "date": "2026-08-14"}
        asked = self.generate(bare, gaps="question")
        assumed = self.generate(bare, gaps="assumption")
        self.assertIn("open-questions", sections(asked))
        self.assertIn("assumptions", sections(assumed))

    def test_stated_assumptions_and_assumed_silences_share_one_section(self):
        # Both are assumptions. Two sections with one identifier would break
        # every deep link into either of them.
        spec = self.generate(prd_brief(risks=[]), gaps="assumption")
        found = [one for one in spec["sections"] if one["id"] == "assumptions"]
        self.assertEqual(len(found), 1)
        self.assertIn("Someone is accountable for answering the gate.",
                      found[0]["items"])
        self.assertTrue(any("stop this working" in item for item in found[0]["items"]))

    def test_a_brief_with_no_title_is_refused_not_defaulted(self):
        with self.assertRaises(chain.IncompleteBrief):
            self.generate({"owner": "A. Owner", "date": "2026-08-14"})


# ------------------------------------------------------- speaking the language

class TestTheDocumentSpeaksTheAgreedLanguage(Sandbox):
    """FR-CTX-05: a retired synonym does not survive into a later document."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_a_retired_synonym_is_replaced_by_the_canonical_term(self):
        spec = self.generate()
        said = list(strings(spec))
        self.assertFalse([one for one in said if "input pack" in one])
        self.assertTrue([one for one in said if "Bring the Brief." in one])

    def test_an_identifier_is_never_rewritten_by_the_glossary(self):
        spec = self.generate()
        self.assertEqual([one["id"] for one in items_of(spec, "goals")],
                         ["G-01", "G-02"])
        self.assertEqual(spec["document"]["slug"], prd.SLUG)


# ------------------------------------------------------------- the round trip

class TestRegenerationFromItsOwnSpecification(Sandbox):
    """M3-P3-T2-C1: a round trip changes only the edited value (FR-DOC-06)."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()
        self.path, self.spec = self.author()

    def read(self):
        with open(self.path, encoding="utf-8") as handle:
            return handle.read()

    def extracted(self):
        return validate.extract(self.read())

    def test_regenerating_an_untouched_document_changes_nothing(self):
        before = self.read()
        prd.regenerate(self.root)
        self.assertEqual(self.read(), before)

    def test_editing_one_value_changes_that_value_and_no_other(self):
        before = self.extracted()
        edited = copy.deepcopy(before)
        edited["sections"][1]["items"][0]["definition"] = "Make provenance the default."
        prd.regenerate(self.root, edited)

        after = self.extracted()
        self.assertEqual(after["sections"][1]["items"][0]["definition"],
                         "Make provenance the default.")
        after["sections"][1]["items"][0]["definition"] = \
            before["sections"][1]["items"][0]["definition"]
        self.assertEqual(after, before)

    def test_the_old_wording_survives_nowhere_in_the_file(self):
        # US-SPC-01-S03: prose and data cannot disagree, because there is only
        # one copy of the fact in the file.
        edited = self.extracted()
        stale = edited["sections"][1]["items"][0]["definition"]
        edited["sections"][1]["items"][0]["definition"] = "Make provenance the default."
        prd.regenerate(self.root, edited)
        self.assertNotIn(stale, self.read())

    def test_regeneration_needs_no_brief_and_no_gate(self):
        # An update is made by editing the specification and re-rendering. If it
        # needed the brief back, the document would not be its own source.
        self.assertEqual(prd.regenerate(self.root), self.path)


# ----------------------------------------------------------------- the writing

class TestWhatAuthoringLeavesBehind(Sandbox):

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_the_document_lands_where_the_chain_looks_for_it(self):
        path, _ = self.author()
        self.assertEqual(path, paths.resolve(self.root, paths.SPECS_DIR, prd.FILENAME))
        self.assertTrue(os.path.exists(path))

    def test_the_answers_are_recorded_before_the_document_is_written(self):
        self.author()
        self.assertTrue(gate.load(self.root, prd.SLUG))

    def test_the_locked_decisions_reach_the_document(self):
        _, spec = self.author()
        self.assertIn("locked-decisions", sections(spec))

    def test_the_generated_document_validates(self):
        path, _ = self.author()
        with open(path, encoding="utf-8") as handle:
            spec = validate.extract(handle.read())
        self.assertEqual([one for one in validate.validate_document(spec, path)
                          if one.level == schema.FAILURE], [])

    def test_the_whole_set_validates_together(self):
        # The document alone cannot answer whether VC-01 exists. Only the set
        # can, which is why the trace check is a set-wide one.
        self.author()
        grouped = validate.validate_set([paths.resolve(self.root, paths.SPECS_DIR, name)
                                         for name in (intent.FILENAME, context.FILENAME,
                                                      prd.FILENAME)])
        found = [one for source in grouped for one in grouped[source]
                 if one.level == schema.FAILURE]
        self.assertEqual(found, [])

    def test_two_runs_of_one_brief_produce_one_document(self):
        first = prd.render(self.generate(), self.root)
        second = prd.render(self.generate(), self.root)
        self.assertEqual(first, second)

    def test_nothing_here_can_read_the_clock_or_the_network(self):
        with open(prd.__file__, encoding="utf-8") as handle:
            found = imports(handle.read())
        self.assertEqual(found & set(CLOCK), set())
        self.assertEqual(found & {"socket", "urllib", "http", "requests"}, set())


if __name__ == "__main__":
    unittest.main()
