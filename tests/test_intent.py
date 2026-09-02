# -*- coding: utf-8 -*-
"""The intent generator: what it produces, what it refuses, what it records.

Four claims are load-bearing here, each checked against the thing that would
actually break rather than against a description of it:

  · the document it generates passes the same validator the published set is
    held to, and every capability carries a unique identifier (FR-DOC-01)
  · silence produces an absent section and a recorded gap, never a filled-in
    one (FR-DOC-04, NFR-DAT-06)
  · every source consulted appears in the register with origin and
    contribution, and a web address is recorded rather than fetched (FR-DOC-10)
  · nothing reaches the filesystem while a fork is open — the end-to-end claim
    the gate's own tests could not make, because there was no generator to
    invoke (FR-DOC-02, US-DOC-02-S01)

Traces: FR-DOC-01, FR-DOC-02, FR-DOC-03, FR-DOC-04, FR-DOC-07, FR-DOC-10,
NFR-ARC-01, NFR-DAT-06, NFR-GEN-01, US-DOC-01, US-DOC-02, US-CTX-01.
"""

import ast
import inspect
import json
import os
import re
import shutil
import tempfile
import unittest

from z2s import gate, paths, schema, validate, intent

#: Anything that could turn a recorded address into a request.
NETWORK = ("urllib", "http", "httplib", "socket", "ssl", "requests", "ftplib",
           "telnetlib", "webbrowser", "asyncio")

#: Anything that could read the clock, which would make two runs of unchanged
#: input differ (NFR-GEN-01).
CLOCK = ("time", "datetime", "calendar", "random", "uuid")


def imports(source):
    """Every module name a source file imports, wherever the import sits.

    Asserted against instead of searching the text: a module named in prose is
    not an import, and a search that cannot tell the difference fails on its
    own documentation.
    """
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split(".")[0])
            found.update(alias.name for alias in node.names)
    return found


def package_sources():
    """Every module in the toolchain, by name."""
    folder = os.path.dirname(os.path.abspath(intent.__file__))
    for name in sorted(os.listdir(folder)):
        if name.endswith(".py"):
            with open(os.path.join(folder, name), encoding="utf-8") as handle:
                yield name, handle.read()


def facts():
    """The three things no generator may invent."""
    return {"title": "Kestrel", "owner": "A. Owner", "date": "2026-08-14"}


def brief(**extra):
    """A brief with the required facts and one real source."""
    made = facts()
    made["sources"] = [{"kind": "narrative", "name": "Kick-off conversation",
                        "origin": "Recorded 2026-08-01",
                        "contributed": "The problem and the first two capabilities."}]
    made.update(extra)
    return made


def closed(source=None, **answers):
    """A gate over the intent's own forks, closed the way the caller asked.

    Unanswered forks take their recommendation, which is what an unattended run
    does (FR-EXE-08) and what most of these tests are not about.
    """
    run = gate.Gate(intent.SLUG, intent.FORKS, source=source or {})
    while True:
        question = run.question()
        if question is None:
            return run
        run.answer(question.id, answers.get(question.id, question.recommended.id),
                   "Chosen by the test.")


def sections(spec):
    return dict((section["id"], section) for section in spec["sections"])


class Sandbox(unittest.TestCase):
    """A project root that starts genuinely empty."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-intent-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def contents(self):
        return sorted(os.listdir(self.root))

    def document(self):
        return paths.resolve(self.root, paths.SPECS_DIR, intent.FILENAME)


# --------------------------------------------------------------- the envelope

class TestFactsAreNeverInvented(unittest.TestCase):

    def test_a_brief_with_no_owner_is_refused(self):
        missing = facts()
        del missing["owner"]
        with self.assertRaises(intent.IncompleteBrief) as caught:
            intent.generate(missing, closed())
        self.assertIn("owner", str(caught.exception))

    def test_every_missing_fact_is_named_at_once(self):
        with self.assertRaises(intent.IncompleteBrief) as caught:
            intent.generate({"title": "Kestrel"}, closed())
        for name in ("owner", "date"):
            self.assertIn(name, str(caught.exception))

    def test_the_date_comes_from_the_brief_and_never_from_the_clock(self):
        spec = intent.generate(brief(), closed())
        self.assertEqual(spec["document"]["date"], "2026-08-14")
        reachable = imports(inspect.getsource(intent))
        for name in CLOCK:
            self.assertNotIn(name, reachable, name)

    def test_version_and_status_have_defensible_defaults(self):
        spec = intent.generate(brief(), closed())
        self.assertEqual(spec["document"]["version"], "1.0")
        self.assertEqual(spec["document"]["status"], "Draft for review")

    def test_a_brief_may_override_a_default(self):
        spec = intent.generate(brief(status="Agreed"), closed())
        self.assertEqual(spec["document"]["status"], "Agreed")

    def test_the_envelope_carries_every_field_the_schema_requires(self):
        spec = intent.generate(brief(), closed())
        for name in schema.REQUIRED_DOCUMENT_FIELDS:
            self.assertFalse(schema.is_empty(spec["document"].get(name)), name)


# -------------------------------------------------------- the generated document

class TestTheGeneratedIntentValidates(unittest.TestCase):
    """M3-P2-T1-C1. Held to the same validator as the published set."""

    def setUp(self):
        self.spec = intent.generate(brief(
            problem=["Specifications rot.", "Plans drift from them."],
            statement="One artefact a person reads and a machine parses.",
            principles=[{"title": "Decide once", "body": "Every fork closes before authoring."}],
            stakeholders=[{"name": "Product owner", "kind": "Decision-maker",
                           "need": "To decide once and have it stick."}],
            personas=[{"title": "The owner", "body": "Knows the problem, not the stack."}],
            capabilities=[{"title": "One artefact, two readers",
                           "body": "Readable view generated from the data."},
                          {"title": "Decide once", "body": "A single gate before authoring."}],
            scenarios=[{"title": "The Friday session", "body": "Every fork closed in an hour.",
                        "traces": {"cap": ["VC-02"]}}],
            constraints=["No third-party runtime dependencies."]), closed())

    def test_it_reports_no_findings(self):
        self.assertEqual(validate.validate_document(self.spec, "intent"), [])

    def test_every_capability_carries_a_unique_identifier(self):
        items = sections(self.spec)["capabilities"]["items"]
        identifiers = [item["id"] for item in items]
        self.assertEqual(identifiers, ["VC-01", "VC-02"])
        self.assertEqual(len(set(identifiers)), len(identifiers))

    def test_a_capability_identifier_is_well_formed(self):
        for item in sections(self.spec)["capabilities"]["items"]:
            self.assertEqual(schema.check_identifier(item["id"]), [])

    def test_a_reader_can_find_the_identifier_a_later_document_cites(self):
        # The identifier is data so a machine can trace to it, and in the title
        # so a person following that trace can see it on the page.
        titles = [item["title"] for item in sections(self.spec)["capabilities"]["items"]]
        self.assertTrue(titles[0].startswith("VC-01 "), titles[0])

    def test_scenarios_are_identified_in_their_own_series(self):
        self.assertEqual([item["id"] for item in sections(self.spec)["scenarios"]["items"]],
                         ["VS-01"])

    def test_a_scenario_keeps_its_trace_to_a_capability(self):
        self.assertEqual(sections(self.spec)["scenarios"]["items"][0]["traces"],
                         {"cap": ["VC-02"]})

    def test_a_trace_to_nothing_is_dropped_rather_than_carried_empty(self):
        # The emptiness rule applies to what a machine reads as much as to what
        # a person reads: an empty trace kind is a heading over nothing.
        spec = intent.generate(brief(scenarios=[
            {"title": "Untraced", "body": "It happens.", "traces": {"cap": []}}]), closed())
        self.assertNotIn("traces", sections(spec)["scenarios"]["items"][0])
        self.assertEqual(validate.validate_document(spec, "intent"), [])

    def test_sections_come_out_in_the_declared_order(self):
        declared = [one.id for one in intent.SECTIONS]
        produced = [section["id"] for section in self.spec["sections"]
                    if section["id"] in declared]
        self.assertEqual(produced, declared)

    def test_generating_twice_from_one_brief_produces_the_same_bytes(self):
        again = intent.generate(brief(
            problem=["Specifications rot.", "Plans drift from them."],
            statement="One artefact a person reads and a machine parses.",
            principles=[{"title": "Decide once", "body": "Every fork closes before authoring."}],
            stakeholders=[{"name": "Product owner", "kind": "Decision-maker",
                           "need": "To decide once and have it stick."}],
            personas=[{"title": "The owner", "body": "Knows the problem, not the stack."}],
            capabilities=[{"title": "One artefact, two readers",
                           "body": "Readable view generated from the data."},
                          {"title": "Decide once", "body": "A single gate before authoring."}],
            scenarios=[{"title": "The Friday session", "body": "Every fork closed in an hour.",
                        "traces": {"cap": ["VC-02"]}}],
            constraints=["No third-party runtime dependencies."]), closed())
        self.assertEqual(json.dumps(again, sort_keys=True),
                         json.dumps(self.spec, sort_keys=True))


class TestTooManyToNumber(unittest.TestCase):

    def test_a_hundredth_capability_stops_rather_than_malforming_its_identifier(self):
        many = [{"title": "C%d" % n, "body": "…"} for n in range(intent.MAX_IDENTIFIED + 1)]
        with self.assertRaises(intent.IncompleteBrief) as caught:
            intent.generate(brief(capabilities=many), closed())
        self.assertIn("VC-100", str(caught.exception))


# ------------------------------------------------------------------ the gaps

class TestSilenceIsRecordedNeverFilled(unittest.TestCase):
    """M3-P2-T2. FR-DOC-04, NFR-DAT-06."""

    def setUp(self):
        self.spec = intent.generate(brief(problem=["Specifications rot."]), closed())
        self.sections = sections(self.spec)

    def test_an_unsupported_section_is_absent_rather_than_empty(self):
        self.assertNotIn("constraints", self.sections)
        self.assertNotIn("personas", self.sections)

    def test_the_section_that_was_supported_is_present(self):
        self.assertEqual(self.sections["problem"]["body"], ["Specifications rot."])

    def test_the_gap_appears_in_open_questions(self):
        items = self.sections["open-questions"]["items"]
        self.assertTrue(any("what constrains this work" in item for item in items), items)

    def test_every_silent_section_produces_exactly_one_question(self):
        items = self.sections["open-questions"]["items"]
        for section in intent.SECTIONS:
            if section.key == "problem":
                continue
            matching = [item for item in items if section.gap in item]
            self.assertEqual(len(matching), 1, section.key)

    def test_no_gap_text_ever_becomes_content(self):
        # The failure this guards is a generator that fills a section with a
        # description of what is missing from it — an empty heading wearing a
        # sentence, which reads to a reviewer as an answer.
        elsewhere = json.dumps([section for section in self.spec["sections"]
                                if section["id"] != "open-questions"])
        for section in intent.SECTIONS:
            self.assertNotIn(section.gap, elsewhere, section.key)

    def test_an_empty_document_still_validates(self):
        self.assertEqual(validate.validate_document(self.spec, "intent"), [])

    def test_a_complete_brief_asks_nothing(self):
        complete = brief(**dict((one.key, ["something"] if one.type in ("prose", "list")
                                 else [{"title": "T", "body": "B"}]
                                 if one.type == "cards"
                                 else [{"name": "N", "kind": "K", "need": "D"}])
                                for one in intent.SECTIONS))
        spec = intent.generate(complete, closed())
        self.assertNotIn("open-questions", sections(spec))
        self.assertNotIn("assumptions", sections(spec))


class TestTheGateChoosesHowAGapIsFiled(unittest.TestCase):
    """The `gaps` fork is a visible difference, not a preference."""

    def test_asking_is_the_recommendation(self):
        self.assertEqual(intent._FORKS_BY_ID["gaps"].recommended.id, "question")

    def test_a_gap_becomes_an_open_question_by_default(self):
        spec = intent.generate(brief(), closed())
        found = sections(spec)
        self.assertIn("open-questions", found)
        self.assertNotIn("assumptions", found)

    def test_the_other_answer_files_the_same_gap_as_an_assumption(self):
        spec = intent.generate(brief(), closed(gaps="assumption"))
        found = sections(spec)
        self.assertIn("assumptions", found)
        self.assertNotIn("open-questions", found)
        self.assertTrue(any("Confirm before" in item
                            for item in found["assumptions"]["items"]))

    def test_both_answers_cover_the_same_silences(self):
        asked = sections(intent.generate(brief(), closed()))["open-questions"]["items"]
        assumed = sections(intent.generate(brief(), closed(gaps="assumption")))
        self.assertEqual(len(asked), len(assumed["assumptions"]["items"]))


class TestTheScopeForkReachesTheDocument(unittest.TestCase):

    def test_one_release_is_recorded_as_the_release_scope(self):
        spec = intent.generate(brief(), closed())
        self.assertEqual(spec["document"]["releaseScope"], "One release")

    def test_the_whole_product_records_no_release_scope(self):
        spec = intent.generate(brief(), closed(scope="product"))
        self.assertNotIn("releaseScope", spec["document"])

    def test_a_release_the_brief_names_is_used_verbatim(self):
        spec = intent.generate(brief(scope="The 1.0 launch"), closed(source=brief(
            scope="The 1.0 launch")))
        self.assertEqual(spec["document"]["releaseScope"], "The 1.0 launch")


# ------------------------------------------------------------- source register

class TestTheSourceRegister(unittest.TestCase):
    """M3-P2-T3. FR-DOC-10."""

    def setUp(self):
        self.spec = intent.generate(brief(sources=[
            {"kind": "narrative", "name": "Kick-off conversation",
             "origin": "Recorded 2026-08-01", "contributed": "The problem statement."},
            {"kind": "document", "name": "Discovery notes.md",
             "origin": "docs/discovery-notes.md", "contributed": "Two personas."},
            {"kind": "web", "name": "Competitor teardown",
             "origin": "https://example.invalid/teardown",
             "contributed": "The constraint on file size."}]), closed())

    def test_every_source_appears_with_origin_and_contribution(self):
        for entry in self.spec["sources"]:
            self.assertFalse(schema.is_empty(entry["origin"]), entry)
            self.assertFalse(schema.is_empty(entry["contributed"]), entry)

    def test_a_mixed_bundle_keeps_every_kind(self):
        self.assertEqual([entry["kind"] for entry in self.spec["sources"]],
                         ["narrative", "document", "web"])

    def test_the_register_is_rendered_for_a_reader_too(self):
        section = sections(self.spec)["sources"]
        self.assertEqual(section["columns"], list(intent.SOURCE_COLUMNS))
        self.assertEqual(len(section["rows"]), 3)
        self.assertIn("https://example.invalid/teardown", section["rows"][2])

    def test_the_register_survives_as_data_for_the_next_generator(self):
        # The context generator reads this (FR-CTX-01); reading it back out of
        # table rows would make the column order an undeclared contract.
        self.assertEqual(self.spec["sources"][1]["name"], "Discovery notes.md")

    def test_a_source_of_an_unknown_kind_is_refused(self):
        with self.assertRaises(intent.IncompleteBrief) as caught:
            intent.generate(brief(sources=[{"kind": "rumour", "name": "n",
                                            "origin": "o", "contributed": "c"}]), closed())
        self.assertIn("rumour", str(caught.exception))

    def test_a_source_with_no_contribution_recorded_becomes_a_gap(self):
        spec = intent.generate(brief(sources=[
            {"kind": "web", "name": "A blog post", "origin": "https://example.invalid/post"}]),
            closed())
        self.assertEqual(len(spec["sources"]), 1)
        self.assertTrue(any("what A blog post contributed" in item
                            for item in sections(spec)["open-questions"]["items"]))

    def test_a_intent_written_from_nothing_says_so(self):
        spec = intent.generate(facts(), closed())
        self.assertNotIn("sources", spec)
        self.assertTrue(any("what material this intent was written from" in item
                            for item in sections(spec)["open-questions"]["items"]))


class TestAWebAddressIsRecordedNotFetched(unittest.TestCase):
    """A locked decision of this build, enforced where it cannot be argued with."""

    def test_the_generator_cannot_reach_the_network(self):
        reachable = imports(inspect.getsource(intent))
        for name in NETWORK:
            self.assertNotIn(name, reachable, name)

    def test_nothing_the_generator_imports_can_reach_it_either(self):
        # An indirect fetch is still a fetch. The whole toolchain is checked,
        # so a network import cannot arrive later through a shared module.
        for name, source in package_sources():
            reachable = imports(source)
            for forbidden in NETWORK:
                self.assertNotIn(forbidden, reachable, "%s imports %s" % (name, forbidden))

    def test_an_unreachable_address_still_generates(self):
        spec = intent.generate(brief(sources=[
            {"kind": "web", "name": "Teardown", "origin": "https://example.invalid/gone",
             "contributed": "The size constraint."}]), closed())
        self.assertEqual(spec["sources"][0]["origin"], "https://example.invalid/gone")


# -------------------------------------------------------- the gate, end to end

class TestNothingIsAuthoredWhileAForkIsOpen(Sandbox):
    """M3-P2-T1, e2e. The claim M3-P1 could not make for want of a generator."""

    def test_generate_refuses_while_the_gate_is_open(self):
        run = gate.Gate(intent.SLUG, intent.FORKS)
        with self.assertRaises(gate.GateNotClosed):
            intent.generate(brief(), run)

    def test_the_open_gate_is_the_first_thing_to_refuse(self):
        # A brief with problems of its own does not get to report them first.
        # The gate is the first question asked of any authoring run (ADR-10),
        # and a run told to fix its brief would fix the wrong thing.
        run = gate.Gate(intent.SLUG, intent.FORKS)
        with self.assertRaises(gate.GateNotClosed):
            intent.generate({"title": "Kestrel"}, run)

    def test_the_project_stays_empty_through_every_open_step(self):
        run = gate.Gate(intent.SLUG, intent.FORKS)
        self.assertEqual(self.contents(), [])

        with self.assertRaises(gate.GateNotClosed):
            intent.author(self.root, brief(), run)
        self.assertEqual(self.contents(), [])

        run.answer("scope", "release", "One release, one document.")
        with self.assertRaises(gate.GateNotClosed):
            intent.author(self.root, brief(), run)
        self.assertEqual(self.contents(), [])

        run.answer("gaps", "question", "Asking beats assuming.")
        intent.author(self.root, brief(), run)
        self.assertEqual(self.contents(), [paths.ROOT])

    def test_an_incomplete_brief_writes_nothing_either(self):
        with self.assertRaises(intent.IncompleteBrief):
            intent.author(self.root, {"title": "Kestrel"}, closed())
        self.assertEqual(self.contents(), [])


class TestWhatAuthoringLeavesBehind(Sandbox):

    def setUp(self):
        Sandbox.setUp(self)
        self.path, self.spec = intent.author(self.root, brief(
            problem=["Specifications rot."],
            capabilities=[{"title": "Decide once", "body": "One gate."}]), closed())

    def test_the_document_is_where_the_layout_says_it_is(self):
        self.assertEqual(self.path, self.document())
        self.assertTrue(os.path.isfile(self.path))

    def test_the_document_carries_its_specification_back(self):
        with open(self.path, encoding="utf-8") as handle:
            embedded = validate.extract(handle.read())
        self.assertEqual(embedded, json.loads(json.dumps(self.spec)))

    def test_the_rendered_document_validates(self):
        with open(self.path, encoding="utf-8") as handle:
            embedded = validate.extract(handle.read())
        self.assertEqual(validate.validate_document(embedded, self.path), [])

    def test_the_locked_decisions_are_in_the_document(self):
        section = sections(self.spec)["locked-decisions"]
        self.assertEqual(section["columns"], list(gate.COLUMNS))
        self.assertEqual([row[0] for row in section["rows"]], ["scope", "gaps"])

    def test_the_locked_decisions_are_in_the_ledger_too(self):
        ledger = paths.resolve(self.root, paths.LEDGER_DIR, intent.SLUG + ".md")
        with open(ledger, encoding="utf-8") as handle:
            self.assertIn(gate.TABLE_HEADING, handle.read())

    def test_writing_twice_from_one_brief_produces_the_same_bytes(self):
        with open(self.path, encoding="utf-8") as handle:
            first = handle.read()
        intent.write(self.root, self.spec)
        with open(self.path, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), first)

    def test_no_temporary_file_is_left_behind(self):
        folder = os.path.dirname(self.path)
        self.assertEqual([name for name in os.listdir(folder) if "tmp" in name], [])


class TestALockedDecisionSurvivesTheConversation(Sandbox):
    """FR-DOC-03, US-DOC-02-S03: read back off disk, applied without asking."""

    def test_a_second_run_asks_nothing(self):
        first = closed(scope="product")
        intent.author(self.root, brief(), first)

        resumed = intent.open_gate(brief(), self.root)
        self.assertIsNone(resumed.question())
        self.assertEqual(intent._choice(resumed, "scope"), "product")

    def test_the_recovered_decision_reaches_the_second_document(self):
        intent.author(self.root, brief(), closed(scope="product"))
        spec = intent.generate(brief(), intent.open_gate(brief(), self.root))
        self.assertNotIn("releaseScope", spec["document"])

    def test_a_recovered_run_is_not_reported_as_a_skipped_interview(self):
        intent.author(self.root, brief(), closed())
        self.assertFalse(intent.open_gate(brief(), self.root).skipped)


class TestARichBriefSkipsTheInterview(unittest.TestCase):
    """FR-DOC-07, carried into the generator M3-P1 had no caller for."""

    def test_a_brief_answering_every_fork_asks_nothing(self):
        rich = brief(scope="The 1.0 launch", gaps="question")
        run = intent.open_gate(rich)
        self.assertIsNone(run.question())
        self.assertTrue(run.skipped)
        self.assertIn("scope", run.skip_reason)

    def test_a_thin_brief_still_gets_asked(self):
        run = intent.open_gate(brief())
        self.assertEqual([one.id for one in run.open_forks], ["scope", "gaps"])

    def test_the_skipped_interview_still_produces_a_locked_table(self):
        spec = intent.generate(brief(scope="The 1.0 launch", gaps="question"),
                               intent.open_gate(brief(scope="The 1.0 launch",
                                                      gaps="question")))
        rows = sections(spec)["locked-decisions"]["rows"]
        self.assertEqual([row[0] for row in rows], ["scope", "gaps"])
        self.assertTrue(all(gate.FROM_SOURCE in row[3] for row in rows), rows)


# ------------------------------------------------------------------ discipline

class TestTheGeneratorNeverPrompts(unittest.TestCase):
    """NFR-EXE-08: a generator that waits for a keyboard cannot run unattended."""

    def test_it_reads_no_terminal(self):
        source = inspect.getsource(intent)
        for prompt in ("input(", "raw_input(", "stdin", "getpass"):
            self.assertNotIn(prompt, source, prompt)

    def test_it_prints_nothing(self):
        for line in inspect.getsource(intent).splitlines():
            self.assertIsNone(re.match(r"\s*print\(", line), line)

    def test_it_owns_its_forks_rather_than_inheriting_them(self):
        # NFR-ARC-01: each generator owns its schema, its gate questions and its
        # validator rules, and shares the template and runtime.
        self.assertTrue(intent.FORKS)
        for one in intent.FORKS:
            self.assertEqual(len([o for o in one.options if o.recommended]), 1, one.id)


if __name__ == "__main__":
    unittest.main()
