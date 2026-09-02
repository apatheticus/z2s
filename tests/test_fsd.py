# -*- coding: utf-8 -*-
"""The functional-specification generator: what it keeps, and what it refuses.

Four claims are load-bearing here, each checked against the thing that would
actually break rather than against a description of it:

  · every requirement lands in an area the document itself declares, carries a
    priority from the closed set, and gets an identifier built from its area
    (M4-P1-T1-C1, M4-P1-T1-C2, NFR-DAT-03)
  · a requirement that names a technology is not written down. The choice is
    deferred to the technical specification as an open question, and the same
    rule is enforced again by the validator on the finished document
    (FR-DOC-05, M4-P1-T2-C1)
  · a deliberate exclusion survives as an entry with its reason, rather than
    being dropped and re-argued next quarter, and is not counted in the coverage
    universe (FR-TRC-06, M4-P1-T3-C1, M4-P1-T3-C2)
  · the document speaks the agreed language and regenerates from its own
    embedded specification (FR-CTX-05, FR-DOC-06)

Traces: FR-DOC-01, FR-DOC-04, FR-DOC-05, FR-DOC-06, FR-DOC-08, FR-DOC-10,
FR-TRC-03, FR-TRC-06, NFR-ARC-01, NFR-ARC-02, NFR-DAT-03, NFR-DAT-06,
NFR-GEN-01, US-DOC-01, US-DOC-03, US-TRC-01.
"""

import ast
import copy
import os
import shutil
import tempfile
import unittest

from z2s import chain, context, fsd, gate, paths, prd, schema, validate, intent

from tests.test_prd import context_brief, prd_brief, intent_brief

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

def fsd_brief(**extra):
    made = {"title": "Kestrel — functional specification", "owner": "A. Owner",
            "date": "2026-08-14",
            "purpose": "What Kestrel must do, as requirements that can be tested one "
                       "at a time.",
            "areas": [{"key": "FR-DOC", "name": "Document chain",
                       "description": "Authoring each document and the gate before it."},
                      {"key": "FR-CTX", "name": "Shared language",
                       "description": "One word, one meaning, everywhere after."}],
            "requirements": [
                {"area": "FR-DOC", "priority": "Must", "title": "Source register",
                 "text": "The system shall record every source consulted, what it was, "
                         "and what it contributed.",
                 "notes": "Provenance is what separates a stated fact from an assumed one.",
                 "tags": ["provenance"], "traces": {"goal": ["G-01"]}},
                {"area": "FR-DOC", "priority": "Should", "title": "Intake from notes",
                 "text": "The system shall accept existing notes as the input to a "
                         "generator.",
                 "tags": ["intake"], "traces": {"goal": ["G-01"]}},
                {"area": "FR-CTX", "priority": "Must", "title": "One agreed vocabulary",
                 "text": "Every document shall use the agreed word for a thing, and "
                         "record any synonym it retired.",
                 "tags": ["language"], "traces": {"goal": ["G-02"]}},
            ],
            "assumptions": ["A reader has a browser; no other software is required."],
            "sources": [{"kind": "narrative", "name": "Kick-off conversation",
                         "origin": "Recorded 2026-08-01",
                         "contributed": "The behaviour everyone expected."}]}
    made.update(extra)
    return made


def excluded_requirement(**extra):
    made = {"area": "FR-DOC", "priority": "Won't", "title": "Hosted editing",
            "text": "The system will not provide a hosted service or multi-user editing.",
            "notes": "Documents are files in a repository; collaboration happens through "
                     "version control.",
            "traces": {"goal": ["G-01"]}}
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
    return closed(gate.Gate(fsd.SLUG, fsd.forks(brief), source=brief), **answers)


def sections(spec):
    return dict((section["id"], section) for section in spec["sections"])


def catalogue(spec):
    return sections(spec)["requirements"]


def entries(spec):
    found = sections(spec).get("requirements")
    return found["items"] if found else []


def identifiers(spec):
    return [one["id"] for one in entries(spec)]


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
        self.root = tempfile.mkdtemp(prefix="z2s-fsd-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def chain_above(self):
        brief = intent_brief()
        intent.author(self.root, brief,
                      closed(gate.Gate(intent.SLUG, intent.FORKS, source=brief)))
        brief = context_brief()
        context.author(self.root, brief,
                       closed(gate.Gate(context.SLUG, context.forks(brief), source=brief)))
        brief = prd_brief()
        prd.author(self.root, brief,
                   closed(gate.Gate(prd.SLUG, prd.forks(brief), source=brief)))

    def generate(self, brief=None, **answers):
        made = fsd_brief() if brief is None else brief
        return fsd.generate(made, gate_for(made, **answers), self.root)

    def author(self, brief=None, **answers):
        made = fsd_brief() if brief is None else brief
        return fsd.author(self.root, made, gate_for(made, **answers))


# ------------------------------------------------------- the documents above

class TestTheChainAbove(Sandbox):
    """M4-P1-T1: the FSD is fourth in the chain and says so when it is first."""

    def test_an_empty_project_is_refused_by_name(self):
        with self.assertRaises(chain.MissingPrerequisite) as caught:
            self.generate()
        said = str(caught.exception)
        self.assertIn("prd", said)
        self.assertIn(prd.FILENAME, said)

    def test_a_prd_without_its_context_is_refused(self):
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
        brief = fsd_brief()
        run = gate.Gate(fsd.SLUG, fsd.forks(brief), source=brief)
        with self.assertRaises(gate.GateNotClosed):
            fsd.generate(brief, run, self.root)

    def test_a_complete_chain_is_enough(self):
        self.chain_above()
        spec = self.generate()
        self.assertEqual(spec["document"]["slug"], fsd.SLUG)
        self.assertEqual(spec["schemaVersion"], schema.SCHEMA_VERSION)


# ---------------------------------------------------- areas, priorities, ids

class TestEveryRequirementHasAnAreaAndAPriority(Sandbox):
    """M4-P1-T1-C2."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_identifiers_are_built_from_the_area_and_numbered_within_it(self):
        spec = self.generate()
        self.assertEqual(["FR-DOC-01", "FR-DOC-02", "FR-CTX-01"], identifiers(spec))

    def test_every_entry_carries_a_declared_area_and_a_priority(self):
        spec = self.generate()
        declared = {area["key"] for area in catalogue(spec)["areas"]}
        for one in entries(spec):
            self.assertIn(one["area"], declared)
            self.assertIn(one["priority"], [value["id"] for value in schema.ENUMS["priorities"]])

    def test_the_areas_a_reader_is_shown_are_the_ones_the_brief_declared(self):
        spec = self.generate()
        self.assertEqual(["FR-DOC", "FR-CTX"],
                         [area["key"] for area in catalogue(spec)["areas"]])

    def test_a_requirement_naming_an_undeclared_area_becomes_a_question(self):
        brief = fsd_brief()
        brief["requirements"][1]["area"] = "FR-ZZZ"
        spec = self.generate(brief)
        self.assertEqual(["FR-DOC-01", "FR-CTX-01"], identifiers(spec))
        self.assertTrue(any("Intake from notes" in gap and "FR-ZZZ" in gap
                            for gap in gaps_of(spec)), gaps_of(spec))

    def test_a_requirement_with_no_priority_becomes_a_question(self):
        brief = fsd_brief()
        del brief["requirements"][0]["priority"]
        spec = self.generate(brief)
        self.assertNotIn("Source register", " ".join(strings(catalogue(spec))))
        self.assertTrue(any("priority" in gap and "Source register" in gap
                            for gap in gaps_of(spec)), gaps_of(spec))

    def test_a_priority_outside_the_closed_set_becomes_a_question(self):
        brief = fsd_brief()
        brief["requirements"][0]["priority"] = "Critical"
        spec = self.generate(brief)
        self.assertNotIn("FR-DOC-01", [one["title"] for one in entries(spec)])
        self.assertTrue(any("Critical" in gap for gap in gaps_of(spec)), gaps_of(spec))

    def test_an_area_key_the_grammar_cannot_express_is_a_malformed_brief(self):
        brief = fsd_brief()
        brief["areas"][0]["key"] = "documents"
        with self.assertRaises(fsd.IncompleteBrief) as caught:
            self.generate(brief)
        self.assertIn("documents", str(caught.exception))

    def test_an_area_nothing_belongs_to_is_not_shown(self):
        brief = fsd_brief()
        brief["areas"].append({"key": "FR-XYZ", "name": "Nobody's area",
                               "description": "Declared and never used."})
        spec = self.generate(brief)
        self.assertEqual(["FR-DOC", "FR-CTX"],
                         [area["key"] for area in catalogue(spec)["areas"]])

    def test_a_requirement_stating_no_behaviour_is_a_malformed_brief(self):
        brief = fsd_brief()
        del brief["requirements"][0]["text"]
        with self.assertRaises(fsd.IncompleteBrief):
            self.generate(brief)


# ----------------------------------------------- every requirement serves a goal

class TestEveryRequirementServesAGoal(Sandbox):
    """FR-TRC-03: scope arrives through the PRD or not at all."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_a_requirement_citing_no_goal_becomes_a_question(self):
        brief = fsd_brief()
        del brief["requirements"][0]["traces"]
        spec = self.generate(brief)
        self.assertEqual(["FR-DOC-01", "FR-CTX-01"], identifiers(spec))
        self.assertTrue(any("goal" in gap and "Source register" in gap
                            for gap in gaps_of(spec)), gaps_of(spec))

    def test_a_requirement_citing_a_goal_nobody_stated_becomes_a_question(self):
        brief = fsd_brief()
        brief["requirements"][0]["traces"] = {"goal": ["G-09"]}
        spec = self.generate(brief)
        self.assertTrue(any("G-09" in gap for gap in gaps_of(spec)), gaps_of(spec))

    def test_a_kept_requirement_carries_its_trace_forward(self):
        spec = self.generate()
        self.assertEqual({"goal": ["G-01"]}, entries(spec)[0]["traces"])


# ------------------------------------------- the functional/technical boundary

class TestTheFunctionalTechnicalBoundary(Sandbox):
    """M4-P1-T2-C1 / FR-DOC-05: what, never how."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_a_requirement_naming_a_product_is_not_written_down(self):
        brief = fsd_brief()
        brief["requirements"][0]["text"] = ("The system shall store the source register "
                                            "in SQLite.")
        spec = self.generate(brief)
        self.assertEqual(["FR-DOC-01", "FR-CTX-01"], identifiers(spec))
        self.assertNotIn("SQLite", " ".join(strings(catalogue(spec))))

    def test_the_deferral_is_recorded_and_names_the_document_it_belongs_to(self):
        brief = fsd_brief()
        brief["requirements"][0]["text"] = ("The system shall store the source register "
                                            "in SQLite.")
        gaps = gaps_of(self.generate(brief))
        self.assertTrue(any("SQLite" in gap and "technical" in gap.lower()
                            for gap in gaps), gaps)

    def test_a_technology_named_in_a_note_is_caught_too(self):
        brief = fsd_brief()
        brief["requirements"][0]["notes"] = "Probably Redis."
        gaps = gaps_of(self.generate(brief))
        self.assertTrue(any("Redis" in gap for gap in gaps), gaps)

    def test_a_word_that_merely_contains_a_product_name_is_left_alone(self):
        brief = fsd_brief()
        brief["requirements"][0]["text"] = ("The system shall keep the register in a "
                                            "reactionary order nobody reacts to.")
        spec = self.generate(brief)
        self.assertIn("FR-DOC-01", identifiers(spec))

    def test_a_project_may_add_names_of_its_own(self):
        """The prohibited vocabulary is data, so a project can refuse the product
        names its own stack is full of without editing the toolchain."""
        brief = fsd_brief(technologies=["Kestrelbase"])
        brief["requirements"][0]["text"] = "The system shall write to Kestrelbase."
        spec = self.generate(brief)
        self.assertEqual(["FR-DOC-01", "FR-CTX-01"], identifiers(spec))

    def test_the_validator_enforces_the_same_boundary_on_a_finished_document(self):
        spec = self.generate()
        entries(spec)[0]["text"] = "The system shall store the register in PostgreSQL."
        found = validate.validate_document(spec, "FSD.html")
        self.assertTrue(any(one.code == "functional-boundary" and "PostgreSQL" in one.message
                            for one in found), found)

    def test_the_validator_leaves_other_documents_alone(self):
        """A technical document names technologies for a living."""
        spec = self.generate()
        spec["document"]["slug"] = "sdd"
        entries(spec)[0]["text"] = "The system shall store the register in PostgreSQL."
        found = validate.validate_document(spec, "SDD.html")
        self.assertEqual([], [one for one in found if one.code == "functional-boundary"])

    def test_what_the_generator_writes_passes_its_own_validator(self):
        found = validate.validate_document(self.generate(), "FSD.html")
        self.assertEqual([], found)


# ------------------------------------------------------------- the exclusions

class TestAnExclusionIsRecordedNotDropped(Sandbox):
    """M4-P1-T3 / FR-TRC-06: a decision not to build survives as a decision."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_an_exclusion_is_present_with_its_reason(self):
        brief = fsd_brief()
        brief["requirements"].append(excluded_requirement())
        spec = self.generate(brief)
        found = [one for one in entries(spec) if one["priority"] == "Won't"]
        self.assertEqual(1, len(found))
        self.assertIn("version control", found[0]["notes"])

    def test_an_exclusion_is_not_counted_in_the_coverage_universe(self):
        brief = fsd_brief()
        brief["requirements"].append(excluded_requirement())
        counted, excluded = fsd.universe(self.generate(brief))
        self.assertEqual(["FR-DOC-01", "FR-DOC-02", "FR-CTX-01"], list(counted))
        self.assertEqual(["FR-DOC-03"], list(excluded))
        self.assertIn("Hosted editing", excluded["FR-DOC-03"])

    def test_an_exclusion_with_no_reason_becomes_a_question(self):
        brief = fsd_brief()
        brief["requirements"].append(excluded_requirement(notes=None))
        spec = self.generate(brief)
        self.assertEqual([], [one for one in entries(spec) if one["priority"] == "Won't"])
        self.assertTrue(any("Hosted editing" in gap and "exclu" in gap
                            for gap in gaps_of(spec)), gaps_of(spec))

    def test_the_universe_of_a_document_with_no_exclusions_is_everything(self):
        counted, excluded = fsd.universe(self.generate())
        self.assertEqual(3, len(counted))
        self.assertEqual({}, excluded)


# --------------------------------------------------- what else the document says

class TestWhatElseTheDocumentCarries(Sandbox):

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_the_envelope_is_built_from_stated_facts(self):
        block = self.generate()["document"]
        self.assertEqual("Kestrel — functional specification", block["title"])
        self.assertEqual("A. Owner", block["owner"])
        self.assertEqual("2026-08-14", block["date"])
        self.assertEqual(fsd.TYPE, block["type"])

    def test_a_brief_with_no_owner_is_refused_rather_than_invented(self):
        brief = fsd_brief()
        del brief["owner"]
        with self.assertRaises(fsd.IncompleteBrief) as caught:
            self.generate(brief)
        self.assertIn("owner", str(caught.exception))

    def test_the_source_register_is_carried(self):
        spec = self.generate()
        self.assertIn("sources", sections(spec))
        self.assertEqual([["narrative", "Kick-off conversation", "Recorded 2026-08-01",
                           "The behaviour everyone expected."]],
                         sections(spec)["sources"]["rows"])

    def test_the_locked_decisions_are_written_into_the_document(self):
        spec = self.generate()
        self.assertIn("locked-decisions", sections(spec))

    def test_the_catalogue_says_how_many_entries_it_holds(self):
        spec = self.generate()
        self.assertIn("3", catalogue(spec)["badge"])

    def test_a_brief_with_no_requirements_at_all_records_the_silence(self):
        brief = fsd_brief()
        brief["requirements"] = []
        spec = self.generate(brief)
        self.assertNotIn("requirements", sections(spec))
        self.assertTrue(any("requirement" in gap for gap in gaps_of(spec)), gaps_of(spec))

    def test_stated_assumptions_and_assumed_silences_share_one_section(self):
        brief = fsd_brief()
        del brief["sources"]
        spec = self.generate(brief, gaps="assumption")
        found = [one for one in spec["sections"] if one["id"] == "assumptions"]
        self.assertEqual(1, len(found))

    def test_the_document_speaks_the_agreed_language(self):
        brief = fsd_brief()
        brief["requirements"][0]["text"] = ("The system shall record every input pack "
                                            "it was handed.")
        spec = self.generate(brief)
        said = " ".join(strings(spec))
        self.assertIn("Brief", said)
        self.assertNotIn("input pack", said)

    def test_nothing_here_reads_the_clock_or_the_network(self):
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "z2s", "fsd.py"), encoding="utf-8") as handle:
            found = imports(handle.read())
        for name in CLOCK + ("socket", "urllib", "http", "requests"):
            self.assertNotIn(name, found)


# ------------------------------------------------------------- the round trip

class TestRegenerationFromItsOwnSpecification(Sandbox):

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_an_untouched_regeneration_is_byte_identical(self):
        target, _ = self.author()
        with open(target, encoding="utf-8") as handle:
            before = handle.read()
        fsd.regenerate(self.root)
        with open(target, encoding="utf-8") as handle:
            self.assertEqual(before, handle.read())

    def test_a_round_trip_changes_only_the_edited_value(self):
        target, spec = self.author()
        edited = copy.deepcopy(spec)
        for one in edited["sections"]:
            if one["id"] == "requirements":
                one["items"][0]["text"] = "The system shall record what it was told."
        fsd.regenerate(self.root, edited)
        with open(target, encoding="utf-8") as handle:
            rendered = handle.read()
        self.assertIn("The system shall record what it was told.", rendered)
        self.assertNotIn("what it contributed", rendered)

    def test_authoring_leaves_a_document_and_a_ledger(self):
        target, _ = self.author()
        self.assertEqual(target, paths.resolve(self.root, paths.SPECS_DIR, fsd.FILENAME))
        self.assertTrue(os.path.exists(target))
        self.assertTrue(gate.load(self.root, fsd.SLUG))

    def test_the_whole_set_validates_together(self):
        self.author()
        grouped = validate.validate_set(
            [paths.resolve(self.root, paths.SPECS_DIR, name)
             for name in (intent.FILENAME, context.FILENAME, prd.FILENAME, fsd.FILENAME)])
        self.assertEqual([], [one for source in grouped for one in grouped[source]
                              if one.severity == schema.FAILURE])

    def test_two_runs_of_one_brief_produce_one_document(self):
        self.assertEqual(fsd.render(self.generate(), self.root),
                         fsd.render(self.generate(), self.root))


if __name__ == "__main__":                   # pragma: no cover
    unittest.main()
