# -*- coding: utf-8 -*-
"""The technical-specification generator: what it keeps, and what it refuses.

Five claims are load-bearing here, each checked against the thing that would
actually break rather than against a description of it:

  · every technical requirement lands in an area the document declares, carries
    a priority from the closed set, and answers either a requirement the
    functional specification counts or a decision this document records
    (M6-P1-T1-C1, M6-P1-T1-C2)
  · a decision missing its alternatives or its consequences is not written down,
    and each missing part is asked about separately (M6-P1-T2-C1)
  · a target stated as an adjective is refused, and a target with no measurement
    is refused, because neither can become a check (M6-P1-T3-C1, M6-P1-T3-C2)
  · identifiers for decisions and targets are assigned before the sifting, so a
    dropped entry leaves its number unused rather than re-pointing every
    citation past it (M6-04)
  · the technical document may name a product without being warned about it,
    and is still held to plain English everywhere else (M6-03)

Traces: FR-DOC-01, FR-DOC-04, FR-DOC-06, FR-DOC-08, FR-CTX-05, FR-PLN-05,
FR-TRC-03, NFR-ARC-01, NFR-DAT-03, NFR-DAT-06, NFR-EVO-05, NFR-GEN-01,
NFR-PRF-01, US-AMD-01, US-DOC-01, US-PLN-02, US-TRC-02.
"""

import ast
import copy
import json
import os
import shutil
import subprocess
import tempfile
import unittest

from z2s import chain, context, fsd, gate, paths, prd, schema, sdd, validate, vision

from tests.test_prd import context_brief, prd_brief, vision_brief
from tests.test_stories import covering_fsd

HERE = os.path.dirname(os.path.abspath(__file__))
RENDER_HARNESS = os.path.join(HERE, "render_harness.js")
NODE = shutil.which("node")

#: Anything that could read the clock, which would make two runs of unchanged
#: input differ (NFR-GEN-01).
CLOCK = ("time", "datetime", "calendar", "random", "uuid")


# ------------------------------------------------------------------ fixtures

def sdd_brief(**extra):
    made = {"title": "Kestrel — technical specification", "owner": "A. Owner",
            "date": "2026-08-14",
            "principles": [
                {"name": "One source of truth per fact",
                 "desc": "Each fact is stored once and everything else is derived "
                         "from it."},
                {"name": "Gates are machine-checkable",
                 "desc": "Every quality claim is enforced by a command that exits "
                         "non-zero."}],
            "stack": [
                {"layer": "Document format", "choice": "Single-file HTML",
                 "role": "The deliverable, needing no build step to read."},
                {"layer": "Storage", "choice": "SQLite",
                 "role": "Holds the run ledger between sessions."}],
            "components": [
                {"name": "Document generators", "kind": "Skill and template",
                 "responsibilities": "One per document type; each runs its gate, "
                                     "authors its specification and validates it."},
                {"name": "Validator suite", "kind": "Scripts",
                 "responsibilities": "Schema, structural and coverage checks, wired "
                                     "into the build."}],
            "dataModel": [
                {"name": "Document envelope",
                 "points": ["Every specification carries a document block.",
                            "The slug is the namespace for anything a reader stores."]}],
            "crosscutting": [
                {"name": "Determinism",
                 "points": ["Generators consult neither the clock nor a random source.",
                            "Key ordering is stable, so a regeneration shows only real "
                            "change."]}],
            "decisions": [
                {"title": "One self-contained file per document", "status": "Accepted",
                 "context": "Specifications are read by people who do not have the "
                            "project checked out.",
                 "decision": "Every document is a single file carrying its own styling, "
                             "runtime and data.",
                 "alternatives": ["A site generator — adds a build step and a host.",
                                  "Lightweight markup — not reliably machine-readable."],
                 "consequences": ["A document can be archived and opened years later.",
                                  "Each file repeats its styling; a cost accepted."],
                 "traces": {"fr": ["FR-DOC-01"]}},
                {"title": "The ledger is kept outside version control",
                 "status": "Accepted",
                 "context": "Run state changes far more often than the work it "
                            "describes, and committing it would bury the real diff.",
                 "decision": "The ledger is a plain file the repository ignores.",
                 "alternatives": ["Commit the ledger — noisy and conflict-prone."],
                 "consequences": ["A fresh checkout starts with no run history."],
                 "traces": {"fr": ["FR-DOC-02"]}}],
            "areas": [{"key": "NFR-ARC", "name": "Architecture",
                       "description": "How the parts are divided and what they may "
                                      "depend on."},
                      {"key": "NFR-GEN", "name": "Generation",
                       "description": "What every generator owes, whatever it writes."}],
            "requirements": [
                {"area": "NFR-ARC", "priority": "Must",
                 "title": "One generator per document type",
                 "text": "Each document type shall be produced by exactly one "
                         "generator, sharing the template with every other.",
                 "notes": "A second generator for a type is a second definition of it.",
                 "tags": ["architecture"], "traces": {"fr": ["FR-DOC-01"]}},
                {"area": "NFR-ARC", "priority": "Should",
                 "title": "Ledger kept out of the repository",
                 "text": "Run state shall be written to SQLite where version control "
                         "ignores it.",
                 "notes": "Named here deliberately: this is the document where the "
                          "choice of store belongs.",
                 "traces": {"adr": ["ADR-02"]}},
                {"area": "NFR-GEN", "priority": "Must", "title": "Deterministic output",
                 "text": "Unchanged input shall regenerate byte-identical output.",
                 "traces": {"fr": ["FR-CTX-01"], "adr": ["ADR-01"]}}],
            "targets": [
                {"title": "Single document size", "target": "Under 250 KB",
                 "measured": "Byte count of the written file.",
                 "notes": "Beyond this, split the document rather than compress it."},
                {"title": "Full validation pass", "target": "Under 10 seconds",
                 "measured": "Wall clock on ordinary hardware, cold start."},
                {"title": "Requirements claimed by no task", "target": "Zero",
                 "measured": "Counted by the coverage gate on every run."}],
            "risks": [
                {"risk": "A specification defect propagates into every derived "
                         "artefact.",
                 "mitigation": "The decision gate, and adversarial review before the "
                               "plan is generated."}],
            "assumptions": ["A reader has a browser; no other software is required."],
            "sources": [{"kind": "narrative", "name": "Design conversation",
                         "origin": "Recorded 2026-08-02",
                         "contributed": "The constraints everyone assumed."}]}
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
    return closed(gate.Gate(sdd.SLUG, sdd.forks(brief), source=brief), **answers)


def sections(spec):
    return dict((section["id"], section) for section in spec["sections"])


def identifiers(entries):
    return [one["id"] for one in entries]


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


def asked_about(spec, *words):
    """Whether any recorded question names all of these."""
    return any(all(word in gap for word in words) for gap in gaps_of(spec))


def rendered(request):
    finished = subprocess.run([NODE, RENDER_HARNESS], input=json.dumps(request),
                              capture_output=True, text=True)
    if finished.returncode != 0:
        raise AssertionError("runtime harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout)


class Sandbox(unittest.TestCase):
    """A project root that starts genuinely empty."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-sdd-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def chain_above(self):
        brief = vision_brief()
        vision.author(self.root, brief,
                      closed(gate.Gate(vision.SLUG, vision.FORKS, source=brief)))
        brief = context_brief()
        context.author(self.root, brief,
                       closed(gate.Gate(context.SLUG, context.forks(brief), source=brief)))
        brief = prd_brief()
        prd.author(self.root, brief,
                   closed(gate.Gate(prd.SLUG, prd.forks(brief), source=brief)))
        brief = covering_fsd()
        fsd.author(self.root, brief,
                   closed(gate.Gate(fsd.SLUG, fsd.forks(brief), source=brief)))

    def generate(self, brief=None, **answers):
        made = sdd_brief() if brief is None else brief
        return sdd.generate(made, gate_for(made, **answers), self.root)

    def author(self, brief=None, **answers):
        made = sdd_brief() if brief is None else brief
        return sdd.author(self.root, made, gate_for(made, **answers))


# ------------------------------------------------------------- the chain above

class TestTheChainAbove(Sandbox):
    """M6-P1-T1: the technical document is sixth in the chain and says so when it
    is asked to be first."""

    def test_an_empty_project_is_refused_by_name(self):
        with self.assertRaises(chain.MissingPrerequisite) as caught:
            self.generate()
        said = str(caught.exception)
        self.assertIn(fsd.SLUG, said)
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
        brief = sdd_brief()
        run = gate.Gate(sdd.SLUG, sdd.forks(brief), source=brief)
        with self.assertRaises(gate.GateNotClosed):
            sdd.generate(brief, run, self.root)

    def test_a_complete_chain_is_enough(self):
        self.chain_above()
        spec = self.generate()
        self.assertEqual(spec["document"]["slug"], sdd.SLUG)
        self.assertEqual(spec["schemaVersion"], schema.SCHEMA_VERSION)


# --------------------------------------------------- what a requirement carries

class TestWhatATechnicalRequirementMustCarry(Sandbox):
    """M6-P1-T1-C1, M6-P1-T1-C2."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_requirements_are_numbered_within_their_area(self):
        spec = self.generate()
        self.assertEqual(["NFR-ARC-01", "NFR-ARC-02", "NFR-GEN-01"],
                         identifiers(sdd.requirements(spec)))

    def test_an_area_the_document_does_not_declare_is_a_question(self):
        brief = sdd_brief()
        brief["requirements"][0]["area"] = "NFR-XXX"
        spec = self.generate(brief)
        self.assertNotIn("NFR-XXX-01", identifiers(sdd.requirements(spec)))
        self.assertTrue(asked_about(spec, "NFR-XXX"))

    def test_a_requirement_with_no_priority_is_a_question(self):
        brief = sdd_brief()
        del brief["requirements"][0]["priority"]
        spec = self.generate(brief)
        self.assertEqual(2, len(sdd.requirements(spec)))
        self.assertTrue(asked_about(spec, "priority", "One generator per document type"))

    def test_a_requirement_answering_nothing_is_not_written_down(self):
        brief = sdd_brief()
        del brief["requirements"][0]["traces"]
        spec = self.generate(brief)
        self.assertEqual(2, len(sdd.requirements(spec)))
        self.assertTrue(asked_about(spec, "One generator per document type"))

    def test_a_requirement_may_answer_a_decision_this_document_makes(self):
        """M6-P1-T1-C2: a decision is a real answer to "why does this exist"."""
        spec = self.generate()
        answered = dict((one["id"], one.get("traces", {}))
                        for one in sdd.requirements(spec))
        self.assertEqual({"adr": ["ADR-02"]}, answered["NFR-ARC-02"])

    def test_a_requirement_citing_a_requirement_the_specification_above_excludes(self):
        brief = sdd_brief()
        brief["requirements"][0]["traces"] = {"fr": ["FR-DOC-44"]}
        spec = self.generate(brief)
        self.assertEqual(2, len(sdd.requirements(spec)))
        self.assertTrue(asked_about(spec, "FR-DOC-44"))

    def test_a_requirement_citing_a_decision_that_was_dropped_is_a_question(self):
        """The decision left the document, so nothing supports the requirement."""
        brief = sdd_brief()
        del brief["decisions"][1]["consequences"]
        spec = self.generate(brief)
        self.assertNotIn("ADR-02", identifiers(sdd.decisions(spec)))
        self.assertTrue(asked_about(spec, "ADR-02"))


# ------------------------------------------------------------------- decisions

class TestDecisions(Sandbox):
    """M6-P1-T2-C1 and M6-04."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_a_decision_carries_all_four_parts(self):
        spec = self.generate()
        first = sdd.decisions(spec)[0]
        for part in sdd.DECISION_PARTS:
            self.assertTrue(first.get(part), part)

    def test_a_decision_missing_its_alternatives_is_not_written_down(self):
        brief = sdd_brief()
        del brief["decisions"][0]["alternatives"]
        spec = self.generate(brief)
        self.assertEqual(["ADR-02"], identifiers(sdd.decisions(spec)))
        self.assertTrue(asked_about(spec, "rejected", "One self-contained file"))

    def test_a_decision_missing_its_consequences_is_not_written_down(self):
        brief = sdd_brief()
        del brief["decisions"][0]["consequences"]
        spec = self.generate(brief)
        self.assertEqual(["ADR-02"], identifiers(sdd.decisions(spec)))
        self.assertTrue(asked_about(spec, "consequence", "One self-contained file"))

    def test_each_missing_part_is_asked_about_separately(self):
        """Four answers asked for in one question gets one answer back."""
        brief = sdd_brief()
        del brief["decisions"][0]["alternatives"]
        del brief["decisions"][0]["consequences"]
        spec = self.generate(brief)
        named = [gap for gap in gaps_of(spec) if "One self-contained file" in gap]
        self.assertEqual(2, len(named))

    def test_a_decision_with_no_standing_is_a_question(self):
        brief = sdd_brief()
        del brief["decisions"][0]["status"]
        spec = self.generate(brief)
        self.assertEqual(["ADR-02"], identifiers(sdd.decisions(spec)))
        self.assertTrue(asked_about(spec, "standing"))

    def test_a_standing_outside_the_closed_set_is_a_question(self):
        brief = sdd_brief()
        brief["decisions"][0]["status"] = "Probably"
        spec = self.generate(brief)
        self.assertEqual(["ADR-02"], identifiers(sdd.decisions(spec)))
        self.assertTrue(asked_about(spec, "Probably"))

    def test_a_dropped_decision_leaves_its_number_unused(self):
        """M6-04: numbering after the sift would silently re-point every citation
        past the decision that was dropped."""
        brief = sdd_brief()
        del brief["decisions"][0]["consequences"]
        spec = self.generate(brief)
        self.assertEqual(["ADR-02"], identifiers(sdd.decisions(spec)))

    def test_decisions_are_numbered_in_the_order_the_brief_states_them(self):
        spec = self.generate()
        self.assertEqual(["ADR-01", "ADR-02"], identifiers(sdd.decisions(spec)))


# --------------------------------------------------------------------- targets

class TestTargets(Sandbox):
    """M6-P1-T3-C1, M6-P1-T3-C2, M6-02."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def set_at(self, spec):
        return dict((one["id"], one["text"]) for one in sdd.targets(spec))

    def test_every_target_is_numbered_and_readable_by_identifier(self):
        spec = self.generate()
        self.assertEqual(["TG-01", "TG-02", "TG-03"], identifiers(sdd.targets(spec)))
        self.assertEqual("Under 250 KB", self.set_at(spec)["TG-01"])

    def test_a_target_stated_as_an_adjective_is_flagged(self):
        brief = sdd_brief()
        brief["targets"][0]["target"] = "Fast enough"
        spec = self.generate(brief)
        self.assertNotIn("TG-01", identifiers(sdd.targets(spec)))
        self.assertTrue(asked_about(spec, "Fast enough"))

    def test_a_count_of_nothing_is_a_number(self):
        """Zero unclaimed requirements is as checkable as under 250 KB."""
        self.assertEqual("Zero", self.set_at(self.generate())["TG-03"])

    def test_a_target_with_no_measurement_is_flagged(self):
        brief = sdd_brief()
        del brief["targets"][1]["measured"]
        spec = self.generate(brief)
        self.assertNotIn("TG-02", identifiers(sdd.targets(spec)))
        self.assertTrue(asked_about(spec, "measured", "Full validation pass"))

    def test_every_target_names_how_it_is_measured(self):
        """M6-P1-T3-C2."""
        for one in sdd.targets(self.generate()):
            self.assertTrue(one["measured"], one["id"])

    def test_a_dropped_target_leaves_its_number_unused(self):
        brief = sdd_brief()
        brief["targets"][0]["target"] = "Small"
        spec = self.generate(brief)
        self.assertEqual(["TG-02", "TG-03"], identifiers(sdd.targets(spec)))

    def test_a_target_is_an_identifier_something_may_trace_to(self):
        """M6-02: a plan criterion citing TG-01 is claiming to have met it, and a
        trace to a kind the grammar does not know reads as dangling."""
        self.assertEqual("target", schema.kind_of("TG-01"))
        self.assertIn("tg", schema.TRACE_KINDS)
        self.assertEqual([], schema.check_identifier("TG-01"))


# ----------------------------------------------------- what the design rests on

class TestWhatTheDesignRestsOn(Sandbox):
    """The five sections a technical document owes beyond its catalogues."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_every_plain_section_is_rendered(self):
        found = sections(self.generate())
        for identifier in ("principles", "stack", "components", "data", "crosscutting"):
            self.assertIn(identifier, found)

    def test_a_silence_is_a_question_rather_than_an_empty_section(self):
        for plain in sdd.PLAIN:
            brief = sdd_brief()
            del brief[plain.key]
            spec = self.generate(brief)
            self.assertNotIn(plain.section, sections(spec), plain.key)
            self.assertIn(plain.silence, " ".join(gaps_of(spec)), plain.key)

    def test_a_half_stated_entry_is_a_question_and_the_rest_survive(self):
        brief = sdd_brief()
        del brief["stack"][1]["choice"]
        spec = self.generate(brief)
        self.assertEqual([["Document format", "Single-file HTML",
                           "The deliverable, needing no build step to read."]],
                         sections(spec)["stack"]["rows"])
        self.assertTrue(asked_about(spec, "Storage"))

    def test_an_entry_with_no_name_at_all_is_a_malformed_brief(self):
        brief = sdd_brief()
        del brief["components"][0]["name"]
        with self.assertRaises(chain.IncompleteBrief):
            self.generate(brief)

    def test_a_risk_with_no_mitigation_is_a_question(self):
        brief = sdd_brief()
        del brief["risks"][0]["mitigation"]
        spec = self.generate(brief)
        self.assertNotIn("risks", sections(spec))
        self.assertTrue(asked_about(spec, "mitigated"))


# ------------------------------------------------------- naming the technology

class TestNamingATechnology(Sandbox):
    """M6-03: this is the document where the choice belongs."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()
        self.spec = self.generate()

    def test_the_document_may_name_a_product(self):
        self.assertIn("SQLite", list(strings(self.spec)))

    def test_naming_a_product_here_is_not_reported(self):
        found = validate.validate_document(self.spec, "SDD.html")
        self.assertEqual([], [one for one in found if "SQLite" in one.message])

    def test_the_same_wording_anywhere_else_is_still_reported(self):
        """The exemption belongs to this document, not to the rule."""
        other = copy.deepcopy(self.spec)
        other["document"]["slug"] = "prd"
        found = validate.validate_document(other, "PRD.html")
        self.assertTrue([one for one in found if "SQLite" in one.message])

    def test_an_insider_word_is_still_reported_here(self):
        other = copy.deepcopy(self.spec)
        other["sections"][0]["items"][0]["definition"] = "Held by open_gate()."
        found = validate.validate_document(other, "SDD.html")
        self.assertTrue([one for one in found if one.code == "plain-language"])


# ------------------------------------------------------------ the document itself

class TestTheDocumentItself(Sandbox):
    """FR-DOC-06, FR-CTX-05, NFR-GEN-01."""

    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()

    def test_the_generated_document_validates(self):
        """M6-P1-T1-C1.

        Against the whole set rather than the file alone: what it traces to is
        in the documents above it, and a trace is only dangling if nothing in
        the set defines its target.
        """
        target, _ = self.author()
        folder = os.path.dirname(target)
        grouped = validate.validate_set(
            [os.path.join(folder, name) for name in sorted(os.listdir(folder))])
        self.assertEqual([], [one for one in grouped[target]
                              if one.severity == schema.FAILURE])

    def test_every_identifier_it_assigns_is_well_formed(self):
        _, spec = self.author()
        for _, entry in schema.entries(spec):
            identifier = entry.get("id")
            if schema.kind_of(identifier):
                self.assertEqual([], schema.check_identifier(identifier), identifier)

    def test_it_regenerates_from_its_own_specification(self):
        target, _ = self.author()
        with open(target, encoding="utf-8") as handle:
            before = handle.read()
        sdd.regenerate(self.root)
        with open(target, encoding="utf-8") as handle:
            self.assertEqual(before, handle.read())

    def test_the_generator_reads_no_clock(self):
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "z2s", "sdd.py"), encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module.split(".")[0])
        self.assertEqual(set(), found & set(CLOCK))

    def test_it_speaks_the_agreed_language(self):
        """FR-CTX-05: the whole specification passes through the glossary last."""
        brief = sdd_brief()
        brief["requirements"][0]["text"] = ("Each document type shall be produced from "
                                            "one input pack and no other.")
        spec = self.generate(brief)
        said = " ".join(strings(spec))
        self.assertIn("Brief", said)
        self.assertNotIn("input pack", said)

    def test_the_gate_is_recorded_in_the_document(self):
        _, spec = self.author()
        self.assertIn("locked-decisions", sections(spec))

    def test_nothing_is_present_and_empty(self):
        """NFR-DAT-06."""
        self.assertEqual([], schema.check_emptiness(self.generate()))


# --------------------------------------------------------- what a reader sees

class TestWhatTheCatalogueShows(Sandbox):
    """M6-01: three catalogues of one type, so the M4 machinery reaches all three."""

    def setUp(self):
        Sandbox.setUp(self)
        if NODE is None:
            self.skipTest("node is not installed")
        self.chain_above()
        self.spec = self.generate()

    def markup(self):
        return json.dumps(rendered({"op": "document", "spec": self.spec}),
                          ensure_ascii=False)

    def test_every_entry_of_all_three_catalogues_is_reachable(self):
        found = rendered({"op": "catalogue", "spec": self.spec})["items"]
        self.assertEqual(["ADR-01", "ADR-02",
                          "NFR-ARC-01", "NFR-ARC-02", "NFR-GEN-01",
                          "TG-01", "TG-02", "TG-03"], found)

    def test_a_decision_shows_its_reasoning_in_a_fold(self):
        self.assertIn('class=\\"reasoning\\"', self.markup())

    def test_a_target_shows_how_it_is_measured(self):
        self.assertIn("Measured by:", self.markup())

    def test_a_keyword_only_a_decision_argues_reaches_its_entry(self):
        found = rendered({"op": "catalogue", "spec": self.spec,
                          "item": sdd.decisions(self.spec)[0]})["searchable"]
        self.assertIn("build step", found)

    def test_a_keyword_only_a_target_measures_by_reaches_its_entry(self):
        found = rendered({"op": "catalogue", "spec": self.spec,
                          "item": sdd.targets(self.spec)[0]})["searchable"]
        self.assertIn("byte count", found)

    def test_the_priority_bands_are_the_requirements_own(self):
        """A decision carries a standing, not a band; nothing a release ships
        without."""
        self.assertEqual(["Must", "Should"],
                         rendered({"op": "catalogue", "spec": self.spec})["bands"])

    def test_a_band_being_switched_off_leaves_a_decision_alone(self):
        found = rendered({"op": "catalogue", "spec": self.spec,
                          "cases": [{"entry": {"text": "adr-01", "band": None},
                                     "off": {"Must": True, "Should": True}}]})
        self.assertEqual([True], found["shows"])

    def test_every_entry_is_reviewable(self):
        found = rendered({"op": "review", "spec": self.spec})["reviewable"]
        for identifier in ("ADR-01", "NFR-ARC-01", "TG-01"):
            self.assertIn(identifier, found)


if __name__ == "__main__":       # pragma: no cover
    unittest.main()
