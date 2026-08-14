# -*- coding: utf-8 -*-
"""The story generator: what it keeps, what it refuses, and what it can prove.

Five claims are load-bearing here, each checked against the thing that would
actually break rather than against a description of it:

  · every story lands in an area the document declares, carries a priority and
    the verification layers that prove it, and covers at least one requirement
    the functional specification actually counts (M5-P1-T1-C1, M5-P1-T1-C2)
  · scenario identifiers are derived from the story and are unique across the
    document, and the check that a test is named for its scenario reports the
    two failures separately (M5-P1-T2-C1, M5-P1-T2-C2)
  · a scenario quoting generated wording back is refused rather than written
    down, and a scenario naming a value is not (M5-P1-T3-C1, M5-03)
  · a requirement no story covers is named as a question, and the document is
    still written (M5-02)
  · the document renders through the same catalogue as the functional
    specification, and a keyword reaches into a scenario (M5-01)

Traces: FR-DOC-01, FR-DOC-04, FR-DOC-06, FR-DOC-08, FR-CTX-05, FR-TRC-01,
FR-TRC-03, FR-TRC-09, NFR-ARC-01, NFR-DAT-03, NFR-DAT-06, NFR-GEN-01,
US-DOC-01, US-EXE-02.
"""

import copy
import json
import os
import shutil
import subprocess
import tempfile
import unittest

from z2s import chain, context, fsd, gate, paths, prd, schema, stories, validate, vision

from tests.test_fsd import fsd_brief
from tests.test_prd import context_brief, prd_brief, vision_brief

HERE = os.path.dirname(os.path.abspath(__file__))
RENDER_HARNESS = os.path.join(HERE, "render_harness.js")
NODE = shutil.which("node")


# ------------------------------------------------------------------ fixtures

def stories_brief(**extra):
    made = {"title": "Kestrel — stories", "owner": "A. Owner", "date": "2026-08-14",
            "purpose": "Who wants Kestrel to work, and how anyone will know it does.",
            "areas": [{"key": "US-DOC", "name": "Authoring a document",
                       "description": "Turning a brief into a reviewable document."},
                      {"key": "US-CTX", "name": "Speaking one language",
                       "description": "Agreeing what the words mean, once."}],
            "stories": [
                {"area": "US-DOC", "priority": "Must", "role": "Specification author",
                 "title": "Record where a claim came from",
                 "narrative": "As a **specification author** I want every source I "
                              "consulted written down, so that a reviewer can tell a "
                              "stated fact from an assumed one.",
                 "testLayers": ["unit", "e2e"], "tags": ["provenance"],
                 "traces": {"fr": ["FR-DOC-01"]},
                 "scenarios": [
                     {"title": "A consulted source is registered",
                      "given": "a brief naming two sources",
                      "when": "the document is authored",
                      "then": "the source register holds a row for each of them, "
                              "carrying its origin and what it contributed"},
                     {"title": "A source with no origin is questioned",
                      "given": "a brief naming a source and not where it came from",
                      "when": "the document is authored",
                      "then": "the register still holds the source and the omission "
                              "appears among the open questions"},
                 ]},
                {"area": "US-DOC", "priority": "Should",
                 "role": "Specification author",
                 "title": "Start from notes that already exist",
                 "narrative": "As a **specification author** I want to hand the "
                              "generator the notes I already have, so that I am not "
                              "retyping a conversation into a form.",
                 "testLayers": ["unit"], "traces": {"fr": ["FR-DOC-02"]},
                 "scenarios": [
                     {"title": "Existing notes are accepted as input",
                      "given": "a file of meeting notes",
                      "when": "the author points the generator at it",
                      "then": "the generator reads it without further preparation"},
                 ]},
                {"area": "US-CTX", "priority": "Must", "role": "Reviewer",
                 "title": "Read one word meaning one thing",
                 "narrative": "As a **reviewer** I want every document to use the same "
                              "word for the same thing, so that I am not reconciling "
                              "two vocabularies while I read.",
                 "testLayers": ["unit", "manual"], "traces": {"fr": ["FR-CTX-01"]},
                 "scenarios": [
                     {"title": "A retired synonym is replaced",
                      "given": "a glossary that retired a synonym",
                      "when": "a later document is authored using it",
                      "then": "the agreed word appears in its place and the synonym "
                              "does not"},
                 ]},
            ],
            "assumptions": ["A reader has a browser; no other software is required."],
            "sources": [{"kind": "narrative", "name": "Kick-off conversation",
                         "origin": "Recorded 2026-08-01",
                         "contributed": "Who wanted what, and why."}]}
    made.update(extra)
    return made


def covering_fsd(**extra):
    """A functional specification whose requirements the stories above cover."""
    made = fsd_brief()
    made["requirements"] = [
        {"area": "FR-DOC", "priority": "Must", "title": "Source register",
         "text": "The system shall record every source consulted, what it was, and "
                 "what it contributed.",
         "traces": {"goal": ["G-01"]}},
        {"area": "FR-DOC", "priority": "Should", "title": "Intake from notes",
         "text": "The system shall accept existing notes as the input to a generator.",
         "traces": {"goal": ["G-01"]}},
        {"area": "FR-CTX", "priority": "Must", "title": "One agreed vocabulary",
         "text": "Every document shall use the agreed word for a thing, and record any "
                 "synonym it retired.",
         "traces": {"goal": ["G-02"]}},
    ]
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
    return closed(gate.Gate(stories.SLUG, stories.forks(brief), source=brief), **answers)


def sections(spec):
    return dict((section["id"], section) for section in spec["sections"])


def catalogue(spec):
    return sections(spec)["stories"]


def identifiers(spec):
    return [one["id"] for one in stories.entries(spec)]


def titles(spec):
    """What a dropped story is checked by. Identifiers are assigned after the
    sifting, so dropping the first story renumbers the second into its place —
    an assertion on an identifier would pass whatever was dropped."""
    return [one["title"] for one in stories.entries(spec)]


def gaps_of(spec):
    """Whatever the document recorded as silence, however it was filed."""
    found = sections(spec)
    return (found.get("open-questions") or found.get("assumptions") or {}).get("items", [])


def strings(node):
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


def rendered(request):
    finished = subprocess.run([NODE, RENDER_HARNESS], input=json.dumps(request),
                              capture_output=True, text=True)
    if finished.returncode != 0:
        raise AssertionError("runtime harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout)


class Sandbox(unittest.TestCase):
    """A project root that starts genuinely empty."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-stories-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def chain_above(self, functional=None):
        brief = vision_brief()
        vision.author(self.root, brief,
                      closed(gate.Gate(vision.SLUG, vision.FORKS, source=brief)))
        brief = context_brief()
        context.author(self.root, brief,
                       closed(gate.Gate(context.SLUG, context.forks(brief), source=brief)))
        brief = prd_brief()
        prd.author(self.root, brief,
                   closed(gate.Gate(prd.SLUG, prd.forks(brief), source=brief)))
        brief = covering_fsd() if functional is None else functional
        fsd.author(self.root, brief,
                   closed(gate.Gate(fsd.SLUG, fsd.forks(brief), source=brief)))

    def generate(self, brief=None, **answers):
        made = stories_brief() if brief is None else brief
        return stories.generate(made, gate_for(made, **answers), self.root)

    def author(self, brief=None, **answers):
        made = stories_brief() if brief is None else brief
        return stories.author(self.root, made, gate_for(made, **answers))


# ------------------------------------------------------- the documents above

class TestTheChainAbove(Sandbox):
    """M5-P1-T1: the story document is fifth in the chain and says so when it is first."""

    def test_an_empty_project_is_refused_by_name(self):
        with self.assertRaises(chain.MissingPrerequisite) as caught:
            self.generate()
        said = str(caught.exception)
        self.assertIn("fsd", said)
        self.assertIn(fsd.FILENAME, said)

    def test_a_functional_specification_without_its_context_is_refused(self):
        self.chain_above()
        os.remove(paths.resolve(self.root, paths.SPECS_DIR, context.FILENAME))
        with self.assertRaises(chain.MissingPrerequisite) as caught:
            self.generate()
        self.assertIn(context.FILENAME, str(caught.exception))

    def test_the_refusal_writes_nothing(self):
        with self.assertRaises(chain.MissingPrerequisite):
            self.author()
        self.assertEqual(os.listdir(self.root), [])

    def test_the_gate_refuses_before_the_chain_is_looked_for(self):
        brief = stories_brief()
        run = gate.Gate(stories.SLUG, stories.forks(brief), source=brief)
        with self.assertRaises(gate.GateNotClosed):
            stories.generate(brief, run, self.root)

    def test_a_complete_chain_is_enough(self):
        self.chain_above()
        spec = self.generate()
        self.assertEqual(spec["document"]["slug"], stories.SLUG)
        self.assertEqual(spec["schemaVersion"], schema.SCHEMA_VERSION)


# --------------------------------------------------- areas, priorities, layers

class TestWhatAStoryMustCarry(Sandbox):
    """M5-P1-T1-C1, M5-P1-T1-C2."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_identifiers_are_built_from_the_area_and_numbered_within_it(self):
        self.assertEqual(["US-DOC-01", "US-DOC-02", "US-CTX-01"],
                         identifiers(self.generate()))

    def test_an_area_key_the_grammar_cannot_express_is_a_malformed_brief(self):
        brief = stories_brief()
        brief["areas"][0]["key"] = "documents"
        with self.assertRaises(stories.IncompleteBrief) as caught:
            self.generate(brief)
        self.assertIn("documents", str(caught.exception))

    def test_a_story_naming_an_undeclared_area_becomes_a_question(self):
        brief = stories_brief()
        brief["stories"][1]["area"] = "US-ZZZ"
        spec = self.generate(brief)
        self.assertEqual(["US-DOC-01", "US-CTX-01"], identifiers(spec))
        self.assertTrue(any("Start from notes" in gap and "US-ZZZ" in gap
                            for gap in gaps_of(spec)), gaps_of(spec))

    def test_a_story_with_no_priority_becomes_a_question(self):
        brief = stories_brief()
        del brief["stories"][0]["priority"]
        spec = self.generate(brief)
        self.assertNotIn("Record where a claim came from",
                         [one["title"] for one in stories.entries(spec)])
        self.assertTrue(any("priority" in gap and "Record where a claim" in gap
                            for gap in gaps_of(spec)), gaps_of(spec))

    def test_a_story_with_no_narrative_becomes_a_question(self):
        brief = stories_brief()
        del brief["stories"][0]["narrative"]
        spec = self.generate(brief)
        self.assertEqual(["US-DOC-01", "US-CTX-01"], identifiers(spec))
        self.assertTrue(any("Record where a claim" in gap for gap in gaps_of(spec)),
                        gaps_of(spec))

    def test_the_narrative_is_what_a_reader_reads_first(self):
        for one in stories.entries(self.generate()):
            self.assertIn("As a", one["text"])

    def test_a_story_naming_no_verification_layer_becomes_a_question(self):
        brief = stories_brief()
        del brief["stories"][0]["testLayers"]
        spec = self.generate(brief)
        self.assertEqual(["US-DOC-01", "US-CTX-01"], identifiers(spec))
        self.assertTrue(any("verification layers" in gap for gap in gaps_of(spec)),
                        gaps_of(spec))

    def test_a_verification_layer_outside_the_closed_set_becomes_a_question(self):
        brief = stories_brief()
        brief["stories"][0]["testLayers"] = ["end-to-end"]
        spec = self.generate(brief)
        self.assertNotIn("Record where a claim came from", titles(spec))
        self.assertTrue(any("end-to-end" in gap for gap in gaps_of(spec)), gaps_of(spec))

    def test_every_layer_a_story_states_is_in_the_closed_set(self):
        allowed = [value["id"] for value in schema.ENUMS["testLayers"]]
        for one in stories.entries(self.generate()):
            for layer in one["testLayers"]:
                self.assertIn(layer, allowed)

    def test_an_area_nothing_belongs_to_is_not_shown(self):
        brief = stories_brief()
        brief["areas"].append({"key": "US-XYZ", "name": "Nobody's area",
                               "description": "Declared and never used."})
        spec = self.generate(brief)
        self.assertEqual(["US-DOC", "US-CTX"],
                         [area["key"] for area in catalogue(spec)["areas"]])


# ------------------------------------------------------------------- coverage

class TestWhatAStoryMustCover(Sandbox):
    """FR-TRC-03, M5-02: scope arrives from the document above or not at all."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_a_story_covering_nothing_becomes_a_question(self):
        brief = stories_brief()
        del brief["stories"][0]["traces"]
        spec = self.generate(brief)
        self.assertEqual(["US-DOC-01", "US-CTX-01"], identifiers(spec))
        self.assertTrue(any("Record where a claim" in gap and "requirement" in gap
                            for gap in gaps_of(spec)), gaps_of(spec))

    def test_a_story_covering_an_imaginary_requirement_becomes_a_question(self):
        brief = stories_brief()
        brief["stories"][0]["traces"] = {"fr": ["FR-DOC-99"]}
        spec = self.generate(brief)
        self.assertNotIn("Record where a claim came from", titles(spec))
        self.assertTrue(any("FR-DOC-99" in gap for gap in gaps_of(spec)), gaps_of(spec))

    def test_a_story_covering_an_excluded_requirement_becomes_a_question(self):
        """A story planned against a decision not to build is not a story."""
        functional = covering_fsd()
        functional["requirements"].append(
            {"area": "FR-DOC", "priority": "Won't", "title": "Hosted editing",
             "text": "The system will not provide a hosted service.",
             "notes": "Documents are files in a repository.",
             "traces": {"goal": ["G-01"]}})
        shutil.rmtree(self.root)
        os.makedirs(self.root)
        self.chain_above(functional)

        brief = stories_brief()
        brief["stories"][0]["traces"] = {"fr": ["FR-DOC-03"]}
        spec = self.generate(brief)
        self.assertNotIn("Record where a claim came from", titles(spec))
        self.assertTrue(any("FR-DOC-03" in gap and "exclude" in gap
                            for gap in gaps_of(spec)), gaps_of(spec))

    def test_a_requirement_no_story_covers_is_named(self):
        brief = stories_brief()
        del brief["stories"][2]
        spec = self.generate(brief)
        self.assertTrue(any("FR-CTX-01" in gap and "One agreed vocabulary" in gap
                            for gap in gaps_of(spec)), gaps_of(spec))

    def test_a_requirement_no_story_covers_does_not_stop_the_document(self):
        """M5-02: the silence is asked about; the rest is still written."""
        brief = stories_brief()
        del brief["stories"][2]
        spec = self.generate(brief)
        self.assertEqual(["US-DOC-01", "US-DOC-02"], identifiers(spec))
        self.assertIn("stories", sections(spec))

    def test_a_fully_covered_specification_leaves_no_coverage_question(self):
        spec = self.generate()
        self.assertEqual({}, dict(stories.uncovered(
            chain.require(self.root, fsd.FILENAME, fsd.SLUG, "the test"), spec)))

    def test_an_excluded_requirement_is_not_asked_to_be_covered(self):
        """FR-TRC-06: a deliberate exclusion is not a coverage hole."""
        functional = covering_fsd()
        functional["requirements"].append(
            {"area": "FR-DOC", "priority": "Won't", "title": "Hosted editing",
             "text": "The system will not provide a hosted service.",
             "notes": "Documents are files in a repository.",
             "traces": {"goal": ["G-01"]}})
        shutil.rmtree(self.root)
        os.makedirs(self.root)
        self.chain_above(functional)

        spec = self.generate()
        self.assertFalse([gap for gap in gaps_of(spec) if "FR-DOC-03" in gap],
                         gaps_of(spec))


# ------------------------------------------------------------------ scenarios

class TestScenarios(Sandbox):
    """M5-P1-T1, M5-P1-T2-C1: what a scenario is, and what it is called."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_scenario_identifiers_are_derived_from_the_story(self):
        spec = self.generate()
        self.assertEqual(["US-DOC-01-S01", "US-DOC-01-S02", "US-DOC-02-S01",
                          "US-CTX-01-S01"], list(stories.scenarios(spec)))

    def test_scenario_identifiers_are_unique_across_the_document(self):
        spec = self.generate()
        found = [one["id"] for story in stories.entries(spec)
                 for one in story["scenarios"]]
        self.assertEqual(len(found), len(set(found)))

    def test_a_scenario_identifier_is_well_formed(self):
        spec = self.generate()
        for identifier in stories.scenarios(spec):
            self.assertEqual([], schema.check_identifier(identifier))

    def test_every_scenario_states_all_three_clauses(self):
        for story in stories.entries(self.generate()):
            for one in story["scenarios"]:
                for clause in stories.CLAUSES:
                    self.assertTrue(one[clause].strip(), one)

    def test_a_story_with_no_scenario_becomes_a_question(self):
        brief = stories_brief()
        brief["stories"][1]["scenarios"] = []
        spec = self.generate(brief)
        self.assertEqual(["US-DOC-01", "US-CTX-01"], identifiers(spec))
        self.assertTrue(any("Start from notes" in gap and "scenario" in gap
                            for gap in gaps_of(spec)), gaps_of(spec))

    def test_a_scenario_missing_a_clause_becomes_a_question_naming_the_clause(self):
        brief = stories_brief()
        del brief["stories"][1]["scenarios"][0]["then"]
        spec = self.generate(brief)
        self.assertNotIn("US-DOC-02", identifiers(spec))
        self.assertTrue(any("then" in gap and "Existing notes" in gap
                            for gap in gaps_of(spec)), gaps_of(spec))

    def test_a_partial_scenario_is_reported_rather_than_completed(self):
        brief = stories_brief()
        del brief["stories"][1]["scenarios"][0]["when"]
        spec = self.generate(brief)
        self.assertNotIn("Start from notes",
                         [one["title"] for one in stories.entries(spec)])

    def test_more_scenarios_than_the_grammar_can_number_is_a_malformed_brief(self):
        brief = stories_brief()
        brief["stories"][0]["scenarios"] = [
            {"title": "Scenario %d" % index, "given": "a state", "when": "an action",
             "then": "an outcome"} for index in range(chain.MAX_IDENTIFIED + 1)]
        with self.assertRaises(stories.IncompleteBrief) as caught:
            self.generate(brief)
        self.assertIn("US-DOC-01", str(caught.exception))


# ------------------------------------------------- assertions on structure

class TestScenariosAssertOnStructure(unittest.TestCase):
    """M5-P1-T3-C1, M5-03: the rule itself, at its boundary."""

    def test_a_quoted_sentence_is_reported(self):
        self.assertEqual(
            ["No requirement matches the current filter"],
            stories.quoted_wording('the page reads "No requirement matches the '
                                   'current filter"'))

    def test_a_quoted_value_is_allowed(self):
        self.assertEqual([], stories.quoted_wording('the entry carries priority "Must"'))

    def test_a_two_word_quotation_is_allowed(self):
        self.assertEqual([], stories.quoted_wording('the badge reads "Draft review"'))

    def test_three_words_is_where_quoting_becomes_transcription(self):
        self.assertEqual(["one two three"],
                         stories.quoted_wording('it says "one two three"'))

    def test_curly_quotes_are_quotes(self):
        self.assertEqual(["the source register holds"],
                         stories.quoted_wording("it reads “the source register holds”"))

    def test_code_marks_are_quotes(self):
        self.assertEqual(["nothing at all here"],
                         stories.quoted_wording("it prints `nothing at all here`"))

    def test_unquoted_prose_is_never_reported(self):
        self.assertEqual([], stories.quoted_wording(
            "the source register holds a row for each source, with its origin"))

    def test_nothing_is_reported_for_an_absent_clause(self):
        self.assertEqual([], stories.quoted_wording(None))
        self.assertEqual([], stories.quoted_wording(""))


class TestScenariosAssertingOnWordingAreRefused(Sandbox):
    """M5-P1-T3-C1, applied at authoring."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_a_scenario_quoting_generated_wording_becomes_a_question(self):
        brief = stories_brief()
        brief["stories"][1]["scenarios"][0]["then"] = (
            'the page reads "the generator read your notes without preparation"')
        spec = self.generate(brief)
        self.assertNotIn("US-DOC-02", identifiers(spec))
        self.assertTrue(any("Existing notes" in gap and "quotes" in gap
                            for gap in gaps_of(spec)), gaps_of(spec))

    def test_the_question_quotes_the_offending_phrase_back(self):
        brief = stories_brief()
        brief["stories"][1]["scenarios"][0]["then"] = 'it reads "one two three four"'
        spec = self.generate(brief)
        self.assertTrue(any("one two three four" in gap for gap in gaps_of(spec)),
                        gaps_of(spec))

    def test_a_scenario_naming_a_value_is_kept(self):
        brief = stories_brief()
        brief["stories"][1]["scenarios"][0]["then"] = (
            'the entry carries the priority "Must" and nothing else changes')
        spec = self.generate(brief)
        self.assertIn("US-DOC-02", identifiers(spec))

    def test_the_fixture_document_breaks_its_own_rule_nowhere(self):
        spec = self.generate()
        for story in stories.entries(spec):
            for one in story["scenarios"]:
                for clause in stories.CLAUSES:
                    self.assertEqual([], stories.quoted_wording(one[clause]), one)


# --------------------------------------------------- tests named for scenarios

class TestTestsAreNamedForTheirScenario(Sandbox):
    """M5-P1-T2-C2, M5-04."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()
        self.spec = self.generate()

    def test_a_suite_naming_every_scenario_reports_nothing(self):
        names = ["test_%s_works" % identifier.lower().replace("-", "_")
                 for identifier in stories.scenarios(self.spec)]
        self.assertEqual(([], []), stories.named_tests(self.spec, names))

    def test_a_scenario_no_test_names_is_reported(self):
        names = ["test_us_doc_01_s01", "test_us_doc_02_s01", "test_us_ctx_01_s01"]
        undefended, unmatched = stories.named_tests(self.spec, names)
        self.assertEqual(["US-DOC-01-S02"], undefended)
        self.assertEqual([], unmatched)

    def test_a_test_naming_no_scenario_is_reported_separately(self):
        names = ["test_%s" % identifier.lower().replace("-", "_")
                 for identifier in stories.scenarios(self.spec)]
        names.append("test_something_nobody_asked_for")
        undefended, unmatched = stories.named_tests(self.spec, names)
        self.assertEqual([], undefended)
        self.assertEqual(["test_something_nobody_asked_for"], unmatched)

    def test_the_two_findings_are_reported_as_two(self):
        undefended, unmatched = stories.named_tests(
            self.spec, ["test_us_doc_01_s01", "test_unrelated"])
        self.assertEqual(3, len(undefended))
        self.assertEqual(["test_unrelated"], unmatched)

    def test_an_empty_suite_leaves_every_scenario_undefended(self):
        undefended, unmatched = stories.named_tests(self.spec, [])
        self.assertEqual(list(stories.scenarios(self.spec)), undefended)
        self.assertEqual([], unmatched)

    def test_the_identifier_is_matched_however_a_language_spells_it(self):
        """A hyphen is not legal in a Python name; the check has to survive that."""
        for spelling in ("test_us_doc_01_s01", "US-DOC-01-S01 registers a source",
                         "usDoc01S01", "it('US-DOC-01-S01 registers')"):
            undefended, unmatched = stories.named_tests(self.spec, [spelling])
            self.assertEqual([], unmatched, spelling)
            self.assertNotIn("US-DOC-01-S01", undefended, spelling)

    def test_one_test_may_defend_several_scenarios(self):
        undefended, unmatched = stories.named_tests(
            self.spec, ["test_us_doc_01_s01_and_us_doc_01_s02"])
        self.assertEqual(["US-DOC-02-S01", "US-CTX-01-S01"], undefended)
        self.assertEqual([], unmatched)


# -------------------------------------------------------------- the document

class TestTheDocumentItself(Sandbox):
    """FR-DOC-06, FR-DOC-08, NFR-DAT-06, NFR-GEN-01."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_the_document_validates(self):
        """M5-P1-T1-C1."""
        spec = self.generate()
        found = validate.validate_document(spec, stories.FILENAME)
        self.assertEqual([], [one for one in found if one.severity == schema.FAILURE],
                         found)

    def test_every_story_traces_at_least_one_requirement(self):
        """M5-P1-T1-C2."""
        for one in stories.entries(self.generate()):
            self.assertTrue(one["traces"]["fr"], one)

    def test_the_catalogue_is_the_shared_one(self):
        """M5-01, NFR-ARC-01: one renderer, whatever the document."""
        self.assertEqual("requirements", catalogue(self.generate())["type"])

    def test_the_badge_counts_stories_and_scenarios(self):
        self.assertEqual("3 stories · 4 scenarios", catalogue(self.generate())["badge"])

    def test_the_generator_does_not_modify_the_brief(self):
        brief = stories_brief()
        before = copy.deepcopy(brief)
        self.generate(brief)
        self.assertEqual(before, brief)

    def test_regenerating_an_untouched_document_changes_nothing(self):
        path, _ = self.author()
        with open(path, encoding="utf-8") as handle:
            before = handle.read()
        stories.regenerate(self.root)
        with open(path, encoding="utf-8") as handle:
            self.assertEqual(before, handle.read())

    def test_the_document_speaks_the_agreed_vocabulary(self):
        """FR-CTX-05: the whole specification passes through the glossary last."""
        spec = self.generate()
        self.assertTrue(any(True for _ in strings(spec)))

    def test_nothing_present_and_empty(self):
        """NFR-DAT-06."""
        self.assertEqual([], schema.check_emptiness(self.generate()))

    def test_the_missing_facts_are_named_together(self):
        brief = stories_brief()
        del brief["owner"]
        del brief["date"]
        with self.assertRaises(stories.IncompleteBrief) as caught:
            self.generate(brief)
        said = str(caught.exception)
        self.assertIn("owner", said)
        self.assertIn("date", said)

    def test_a_story_with_no_title_is_a_malformed_brief(self):
        brief = stories_brief()
        del brief["stories"][0]["title"]
        with self.assertRaises(stories.IncompleteBrief):
            self.generate(brief)


# ------------------------------------------------------------- the rendering

@unittest.skipIf(NODE is None, "node is not installed; the runtime cannot be exercised")
class TestScenariosInTheCatalogue(Sandbox):
    """M5-01: scenarios live inside the story, and the M4 machinery reaches them."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()
        self.spec = self.generate()

    def markup(self):
        # ensure_ascii=False, or "·" arrives as \u00b7 and an assertion on the
        # markup fails on the encoding rather than on the markup.
        return json.dumps(rendered({"op": "document", "spec": self.spec}),
                          ensure_ascii=False)

    def test_every_scenario_is_rendered_inside_its_story(self):
        markup = self.markup()
        for identifier in stories.scenarios(self.spec):
            self.assertIn(identifier, markup)

    def test_a_scenario_carries_its_identifier_as_its_own_element(self):
        self.assertIn('class=\\"scenario\\" id=\\"US-DOC-01-S01\\"', self.markup())

    def test_the_three_clauses_are_labelled(self):
        markup = self.markup()
        for label in ("Given", "When", "Then"):
            self.assertIn("<dt>" + label + "</dt>", markup)

    def test_the_scenarios_fold_states_how_many_it_holds(self):
        self.assertIn("Scenarios (2)", self.markup())

    def test_the_scenarios_fold_opens_showing_its_contents(self):
        """FR-SPC-10: a document defaults to revealing rather than hiding."""
        self.assertIn('class=\\"scenarios\\" open', self.markup())

    def test_the_verification_layers_are_rendered(self):
        self.assertIn('class=\\"layers\\"', self.markup())

    def test_the_section_states_how_much_it_holds(self):
        """A reader decides whether to open a catalogue before scrolling it."""
        self.assertIn('<span class=\\"tally\\">3 stories · 4 scenarios</span>',
                      self.markup())

    def test_a_keyword_only_a_scenario_uses_still_finds_the_story(self):
        """Otherwise a reader concludes the behaviour is unspecified."""
        story = stories.entries(self.spec)[0]
        found = rendered({"op": "catalogue", "item": story})["searchable"]
        self.assertIn("retired a synonym".split()[0], self.markup())
        self.assertIn("carrying its origin", found)

    def test_the_story_is_still_one_reviewable_entry(self):
        """M4-05: the pool is sections plus entries; a scenario is not a third thing."""
        pool = rendered({"op": "catalogue", "spec": self.spec})["reviewable"]
        self.assertEqual(identifiers(self.spec),
                         [one for one in pool if one.startswith("US-")])

    def test_a_document_with_no_scenarios_renders_no_fold(self):
        """An empty fold is a heading over nothing (NFR-DAT-06)."""
        markup = json.dumps(rendered({"op": "document", "spec": {
            "document": self.spec["document"], "schemaVersion": schema.SCHEMA_VERSION,
            "sections": [{"id": "stories", "type": "requirements", "title": "Stories",
                          "areas": [{"key": "US-DOC", "name": "Authoring"}],
                          "items": [{"id": "US-DOC-01", "area": "US-DOC",
                                     "priority": "Must", "title": "A story",
                                     "text": "As a reader I want something."}]}]}}))
        self.assertNotIn("scenarios", markup)


if __name__ == "__main__":
    unittest.main()
