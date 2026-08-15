# -*- coding: utf-8 -*-
"""The plan generator: what it builds, and what it refuses to build.

Seven claims are load-bearing here, each checked against the thing that would
actually break rather than against a description of it:

  · a milestone's detail is picked up from its own file, by identifier, with no
    change to the spine beyond its entry — and a milestone that says it is
    detailed and has no file stops the run (M8-P1-T1-C1, M8-P1-T1-C2)
  · a dependency cycle is reported as the whole way round, and a graph that
    cannot be executed leaves the project with no file in it at all
    (M8-P1-T2-C1, M8-P1-T2-C2)
  · a task with no failing test stated, and a task nothing machine-checkable
    can prove, are both refused; a narrow written exception is a warning
    instead (M8-P1-T3-C1, M8-P1-T3-C2, M8-P1-T3-C3)
  · a milestone with no exit criteria is refused, and the prerequisites are a
    list of their own, marked human-owned (M8-P1-T4-C1, M8-P1-T4-C2)
  · every milestone in a wave waits only on milestones in earlier waves, and the
    same graph orders the same way every time (M8-P2-T1-C1, M8-P2-T1-C2)
  · the index lists every milestone, and each milestone document says which
    milestone it is (M8-P2-T2-C1, M8-P2-T2-C2)
  · every generated prompt carries all five parts a worker with no context
    needs, and the effort signal is read by no gate (M8-P2-T3-C1, M8-P2-T4-C2)

The browser checks at the end are the ones no amount of reading the data can
answer: whether a wave actually opens the milestone it names, whether a task's
claim reaches the requirement in the sibling document, and whether the boxes a
reader can see are boxes a reader cannot tick.

Traces: FR-PLN-01, FR-PLN-02, FR-PLN-03, FR-PLN-04, FR-PLN-05, FR-PLN-06,
FR-PLN-07, FR-PLN-08, FR-PLN-09, FR-PLN-12, FR-PLN-13, FR-EXE-03, FR-GEN-03,
NFR-ARC-06, NFR-DAT-05, NFR-EXE-04, NFR-GEN-01, NFR-VAL-03, NFR-VAL-04,
ADR-06, ADR-07, ADR-08, US-PLN-01, US-PLN-02, US-PLN-03, US-PLN-04, US-EXE-01.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

from z2s import (chain, context, fsd, gate, paths, plan, prd, schema, sdd,
                 stories, trace, validate, vision)

from tests.test_prd import context_brief, prd_brief, vision_brief
from tests.test_sdd import sdd_brief
from tests.test_stories import covering_fsd, stories_brief

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN_HARNESS = os.path.join(HERE, "plan_harness.js")
RENDER_HARNESS = os.path.join(HERE, "render_harness.js")
NODE = shutil.which("node")


def rendered(request):
    """One question put to the runtime with no browser involved."""
    finished = subprocess.run([NODE, RENDER_HARNESS], input=json.dumps(request),
                              capture_output=True, text=True)
    if finished.returncode != 0:
        raise AssertionError("runtime harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout)

#: What the chain above states, and therefore what a plan below it has to claim.
FUNCTIONAL = ["FR-DOC-01", "FR-DOC-02", "FR-CTX-01"]
TECHNICAL = ["NFR-ARC-01", "NFR-ARC-02", "NFR-GEN-01"]
DECISIONS = ["ADR-01", "ADR-02"]


# ------------------------------------------------------------------ fixtures

def closed(run, **answers):
    """Close every open fork, taking the recommendation where the test is silent."""
    while True:
        question = run.question()
        if question is None:
            return run
        run.answer(question.id, answers.get(question.id, question.recommended.id),
                   "Chosen by the test.")


def task(number, traces, phase="M1-P1", **extra):
    made = {"id": "%s-T%d" % (phase, number),
            "title": "Task %d" % number,
            "summary": "The %dth piece of work in this phase." % number,
            "priority": "Must", "autonomy": "auto", "layer": "generator",
            "testLayers": ["unit"], "dependsOn": [],
            "tdd": {"red": "A test asserts the behaviour and fails.",
                    "green": "Make it pass with the smallest change.",
                    "refactor": "Tidy under a green suite."},
            "criteria": [{"id": "%s-T%d-C1" % (phase, number), "kind": "auto",
                          "text": "The behaviour holds.", "done": False}],
            "traces": traces}
    made.update(extra)
    return made


def detail(**extra):
    """One phase of one milestone, claiming everything the chain above states."""
    made = {"id": "M1-P1", "title": "Build it", "summary": "All of the work.",
            "dependsOn": [], "completion": ["Every task passes."],
            "tasks": [task(1, {"fr": FUNCTIONAL}),
                      task(2, {"nfr": TECHNICAL}),
                      task(3, {"adr": DECISIONS})]}
    made.update(extra)
    return [made]


def plan_brief(**extra):
    made = {"title": "Kestrel — development plan", "owner": "A. Owner",
            "date": "2026-08-14",
            "summary": "How Kestrel gets built, and in what order.",
            "gauntlet": ["python3 -m unittest discover -s tests",
                         "python3 -m z2s.validate .zero/specs/*.html"],
            "milestones": [
                {"id": "M1", "title": "The toolchain",
                 "summary": "The generators and the documents they write.",
                 "dependsOn": [], "exit": ["Every task in the milestone passes."],
                 "detailed": True}],
            "prerequisites": [
                {"text": "A hosting account for the published documents.",
                 "owner": "human", "unblocks": ["M1-P1-T1"]}]}
    made.update(extra)
    return made


def sections(spec):
    return {one["id"]: one for one in spec["sections"]}


def entries(spec):
    for one in spec["sections"]:
        if one["type"] == "requirements":
            return one["items"]
    return []


def prompts(spec):
    for one in spec["sections"]:
        if one["type"] == "prompts":
            return {item["id"]: item["body"] for item in one["items"]}
    return {}


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def files_under(root):
    found = []
    for folder, _, names in os.walk(root):
        found.extend(os.path.join(folder, name) for name in names)
    return sorted(found)


class Sandbox(unittest.TestCase):
    """A project with the whole chain above the plan already written."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-plan-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def chain_above(self):
        build_chain(self.root)

    def write_detail(self, milestone, phases):
        paths.ensure_layout(self.root)
        target = plan.detail_path(self.root, milestone)
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(phases, handle)
        return target

    def generate(self, brief=None, phases=None, milestone="M1"):
        made = plan_brief() if brief is None else brief
        self.write_detail(milestone, detail() if phases is None else phases)
        return plan.generate(made, closed(gate.Gate(plan.SLUG, plan.forks(made),
                                                    source=made)), self.root)

    def author(self, brief=None, phases=None, milestone="M1"):
        made = plan_brief() if brief is None else brief
        self.write_detail(milestone, detail() if phases is None else phases)
        return plan.author(self.root, made,
                           closed(gate.Gate(plan.SLUG, plan.forks(made), source=made)))


class Chained(Sandbox):
    def setUp(self):
        Sandbox.setUp(self)
        self.chain_above()


# ------------------------------------------------- the spine and its detail

class TestTheSpineAndItsDetailFiles(Chained):
    """M8-P1-T1: detail is loaded by identifier, from its own file."""

    def test_a_detail_file_is_picked_up_by_identifier(self):
        _, specs, _ = self.generate()
        self.assertEqual(["M1-P1-T1", "M1-P1-T2", "M1-P1-T3"],
                         [one["id"] for one in entries(specs["M1"])])

    def test_a_second_milestone_needs_no_change_to_the_first_ones_detail(self):
        """M8-P1-T1-C1: adding a milestone is its own file plus its spine entry."""
        brief = plan_brief()
        brief["milestones"].append(
            {"id": "M2", "title": "The second thing", "summary": "More work.",
             "dependsOn": ["M1"], "exit": ["It passes."], "detailed": True})
        self.write_detail("M2", [{"id": "M2-P1", "title": "Second phase",
                                  "summary": "Its work.", "dependsOn": [],
                                  "completion": ["It passes."],
                                  "tasks": [task(1, {"fr": ["FR-DOC-01"]},
                                                 phase="M2-P1")]}])
        index, specs, _ = self.generate(brief)
        self.assertEqual(["M1", "M2"], sorted(specs))
        self.assertEqual(["M2-P1-T1"], [one["id"] for one in entries(specs["M2"])])

    def test_a_milestone_that_says_it_is_detailed_and_is_not_stops_the_run(self):
        """M8-P1-T1-C2."""
        brief = plan_brief()
        brief["milestones"][0]["id"] = "M9"
        with self.assertRaises(plan.IncompleteBrief) as raised:
            self.generate(brief, milestone="M1")
        self.assertIn("M9", str(raised.exception))
        self.assertIn("detail", str(raised.exception))

    def test_a_milestone_not_marked_detailed_is_allowed_to_have_none(self):
        brief = plan_brief()
        brief["milestones"][0]["detailed"] = False
        brief["milestones"][0]["phases"] = list(detail())
        index, specs, _ = self.generate(brief)
        self.assertEqual(3, len(entries(specs["M1"])))

    def test_an_unreadable_detail_file_is_named_rather_than_traced_back(self):
        paths.ensure_layout(self.root)
        with open(plan.detail_path(self.root, "M1"), "w", encoding="utf-8") as handle:
            handle.write("{not json")
        brief = plan_brief()
        with self.assertRaises(plan.IncompleteBrief) as raised:
            plan.generate(brief, closed(gate.Gate(plan.SLUG, plan.forks(brief),
                                                  source=brief)), self.root)
        self.assertIn("cannot be read", str(raised.exception))


# ------------------------------------------------------------- the graph

class TestTheDependencyGraph(Chained):
    """M8-P1-T2: an unexecutable graph is refused before anything is written."""

    def test_a_cycle_is_reported_with_its_full_path(self):
        """M8-P1-T2-C1."""
        phases = detail()
        phases[0]["tasks"][0]["dependsOn"] = ["M1-P1-T3"]
        phases[0]["tasks"][1]["dependsOn"] = ["M1-P1-T1"]
        phases[0]["tasks"][2]["dependsOn"] = ["M1-P1-T2"]
        with self.assertRaises(plan.BrokenGraph) as raised:
            self.generate(phases=phases)
        message = str(raised.exception)
        for unit in ("M1-P1-T1", "M1-P1-T2", "M1-P1-T3"):
            self.assertIn(unit, message)
        self.assertIn("cycle", message)

    def test_a_dependency_on_a_unit_nobody_defined_is_named(self):
        phases = detail()
        phases[0]["tasks"][0]["dependsOn"] = ["M4-P2-T7"]
        with self.assertRaises(plan.BrokenGraph) as raised:
            self.generate(phases=phases)
        self.assertIn("M4-P2-T7", str(raised.exception))

    def test_two_units_sharing_one_identifier_is_refused(self):
        phases = detail()
        phases[0]["tasks"][1]["id"] = "M1-P1-T1"
        with self.assertRaises(plan.BrokenGraph) as raised:
            self.generate(phases=phases)
        self.assertIn("M1-P1-T1", str(raised.exception))

    def test_no_file_is_written_when_the_graph_is_invalid(self):
        """M8-P1-T2-C2. The check is the filesystem, not a flag."""
        before = files_under(self.root)
        phases = detail()
        phases[0]["tasks"][0]["dependsOn"] = ["M1-P1-T3"]
        phases[0]["tasks"][2]["dependsOn"] = ["M1-P1-T1"]
        self.write_detail("M1", phases)
        after_detail = files_under(self.root)

        brief = plan_brief()
        with self.assertRaises(plan.BrokenGraph):
            plan.author(self.root, brief,
                        closed(gate.Gate(plan.SLUG, plan.forks(brief), source=brief)))
        self.assertEqual(after_detail, files_under(self.root))
        self.assertNotIn(paths.resolve(self.root, paths.PLAN_DIR, plan.INDEX_FILE),
                         files_under(self.root))
        self.assertTrue(len(before) <= len(after_detail))


# -------------------------------------------------------- the task contract

class TestTheTaskContract(Chained):
    """M8-P1-T3: what a task has to state before a worker can be sent at it."""

    def refuse(self, mutate):
        phases = detail()
        mutate(phases[0]["tasks"][0])
        with self.assertRaises(plan.IncompleteBrief) as raised:
            self.generate(phases=phases)
        return str(raised.exception)

    def test_a_task_without_a_red_step_fails(self):
        """M8-P1-T3-C1."""
        message = self.refuse(lambda one: one["tdd"].pop("red"))
        self.assertIn("M1-P1-T1", message)
        self.assertIn("red", message)

    def test_each_missing_part_of_the_triple_is_reported_separately(self):
        message = self.refuse(lambda one: one.pop("tdd"))
        for part in plan.TDD_PARTS:
            self.assertIn(part, message)

    def test_a_task_without_a_machine_checkable_criterion_fails(self):
        """M8-P1-T3-C2."""
        message = self.refuse(
            lambda one: one["criteria"].__setitem__(
                0, dict(one["criteria"][0], kind="human-review")))
        self.assertIn("machine-checkable", message)

    def test_a_task_with_no_criterion_at_all_fails(self):
        message = self.refuse(lambda one: one.update({"criteria": []}))
        self.assertIn("no acceptance criterion", message)

    def test_a_criterion_must_be_individually_identified(self):
        """FR-PLN-05: a criterion nobody can name is a criterion nobody can tick."""
        message = self.refuse(lambda one: one["criteria"][0].pop("id"))
        self.assertIn("individually identified", message)

    def test_a_task_with_no_autonomy_class_fails(self):
        """FR-PLN-07."""
        message = self.refuse(lambda one: one.pop("autonomy"))
        self.assertIn("autonomy", message)

    def test_a_documented_exception_is_a_warning_and_not_a_failure(self):
        """M8-P1-T3-C3: narrow, written down, and it does not stop the run."""
        phases = detail()
        phases[0]["tasks"][0].pop("layer")
        phases[0]["tasks"][0]["exceptions"] = [
            {"rule": "layer", "reason": "The task touches every layer at once."}]
        refusals, warnings = plan.check_work(
            [{"id": "M1", "exit": ["done"], "phases": phases}])
        self.assertEqual([], refusals)
        self.assertEqual(1, len(warnings))
        self.assertIn("every layer at once", warnings[0])

    def excused(self):
        """A generated milestone whose one task is excused a rule."""
        phases = detail()
        phases[0]["tasks"][0].pop("layer")
        phases[0]["tasks"][0]["exceptions"] = [
            {"rule": "layer", "reason": "The task touches every layer at once."}]
        _, specs, _ = self.generate(phases=phases)
        return specs["M1"]

    def test_a_granted_exception_is_carried_into_the_document(self):
        """M9-P1-T3: left in the brief it was granted once and then invisible
        to every reader and every later check. The validator reports it on
        every run, and it can only do that if the document says it."""
        entry = entries(self.excused())[0]
        self.assertEqual([{"rule": "layer",
                           "reason": "The task touches every layer at once."}],
                         entry["exceptions"])

    def test_a_reader_of_the_document_is_told_what_was_excused_and_why(self):
        """A warning in a run nobody reads is not the same as saying so on the
        page the exception is on."""
        markup = json.dumps(rendered({"op": "document", "spec": self.excused()}),
                            ensure_ascii=False)
        self.assertIn("<h5>Excused from</h5>", markup)
        self.assertIn("The task touches every layer at once.", markup)

    def test_a_task_excused_nothing_renders_no_room_for_it(self):
        """NFR-DAT-06: absent, not present and empty."""
        _, specs, _ = self.generate()
        markup = json.dumps(rendered({"op": "document", "spec": specs["M1"]}))
        self.assertNotIn("Excused from", markup)

    def test_a_keyword_only_an_exception_uses_still_finds_the_task(self):
        """"What have we excused, and why" is asked of the whole plan at once,
        and the keyword box is how a reader asks it."""
        found = rendered({"op": "catalogue",
                          "item": entries(self.excused())[0]})["searchable"]
        self.assertIn("every layer at once", found)

    def test_an_exception_covers_the_verification_layers_too(self):
        """M8-P1-T3-C3, the other excusable rule. Both branches, not one."""
        phases = detail()
        phases[0]["tasks"][0]["testLayers"] = []
        phases[0]["tasks"][0]["exceptions"] = [
            {"rule": "testLayers", "reason": "It is proved by the milestone's own gate."}]
        refusals, warnings = plan.check_work(
            [{"id": "M1", "exit": ["done"], "phases": phases}])
        self.assertEqual([], refusals)
        self.assertEqual(1, len(warnings))
        self.assertIn("the milestone's own gate", warnings[0])

    def test_a_task_naming_a_layer_nobody_defined_is_refused_even_with_an_exception(self):
        """An exception excuses silence, never a value outside the closed set."""
        message = self.refuse(lambda one: one.update(
            {"testLayers": ["end-to-end"],
             "exceptions": [{"rule": "testLayers", "reason": "Close enough."}]}))
        self.assertIn("end-to-end", message)

    def test_an_exception_with_no_reason_is_still_a_refusal(self):
        message = self.refuse(lambda one: one.update(
            {"layer": None, "exceptions": [{"rule": "layer"}]}))
        self.assertIn("no reason", message)

    def test_an_exception_to_a_rule_that_cannot_be_excused_is_refused(self):
        """The two rules that make a task a task are not excusable."""
        message = self.refuse(lambda one: one.update(
            {"criteria": [], "exceptions": [{"rule": "criteria",
                                             "reason": "It is obvious."}]}))
        self.assertIn("criteria", message)
        self.assertIn(", ".join(plan.EXCUSABLE), message)

    def test_every_hole_is_named_in_one_report(self):
        """An author told about one hole at a time stops running the generator."""
        phases = detail()
        phases[0]["tasks"][0]["tdd"].pop("red")
        phases[0]["tasks"][1].pop("autonomy")
        phases[0]["tasks"][2]["criteria"] = []
        with self.assertRaises(plan.IncompleteBrief) as raised:
            self.generate(phases=phases)
        message = str(raised.exception)
        for unit in ("M1-P1-T1", "M1-P1-T2", "M1-P1-T3"):
            self.assertIn(unit, message)


# ----------------------------------------------- exits and prerequisites

class TestExitCriteriaAndPrerequisites(Chained):
    """M8-P1-T4."""

    def test_a_milestone_without_exit_criteria_fails(self):
        """M8-P1-T4-C1."""
        brief = plan_brief()
        brief["milestones"][0].pop("exit")
        with self.assertRaises(plan.IncompleteBrief) as raised:
            self.generate(brief)
        self.assertIn("exit criteria", str(raised.exception))

    def test_a_phase_without_exit_criteria_fails(self):
        phases = detail()
        phases[0].pop("completion")
        with self.assertRaises(plan.IncompleteBrief) as raised:
            self.generate(phases=phases)
        self.assertIn("M1-P1", str(raised.exception))

    def test_prerequisites_are_listed_separately_and_marked_human_owned(self):
        """M8-P1-T4-C2."""
        index, _, _ = self.generate()
        found = sections(index)["prerequisites"]
        self.assertEqual("table", found["type"])
        self.assertEqual([["PRE-01",
                           "A hosting account for the published documents.",
                           "human", "M1-P1-T1"]], found["rows"])

    def test_a_prerequisite_that_unblocks_nothing_this_plan_defines_is_refused(self):
        brief = plan_brief()
        brief["prerequisites"][0]["unblocks"] = ["M6-P1-T1"]
        with self.assertRaises(plan.IncompleteBrief) as raised:
            self.generate(brief)
        self.assertIn("M6-P1-T1", str(raised.exception))

    def test_a_prerequisite_is_not_a_unit_of_work(self):
        """FR-PLN-12: held apart from the work, so no task waits on a person."""
        index, specs, _ = self.generate()
        self.assertNotIn("PRE-01", [one["id"] for one in entries(specs["M1"])])


# ------------------------------------------------------------- the waves

class TestWaveOrdering(Chained):
    """M8-P2-T1."""

    def graph(self):
        return [{"id": "M1", "dependsOn": []},
                {"id": "M2", "dependsOn": ["M1"]},
                {"id": "M3", "dependsOn": ["M1"]},
                {"id": "M10", "dependsOn": ["M2", "M3"]}]

    def test_every_member_of_a_wave_waits_only_on_earlier_waves(self):
        """M8-P2-T1-C1."""
        built = self.graph()
        waves = plan.waves(built)
        waiting = {one["id"]: set(one["dependsOn"]) for one in built}
        seen = set()
        for wave in waves:
            for unit in wave:
                self.assertTrue(waiting[unit] <= seen,
                                "%s waits on something in its own wave" % unit)
            seen |= set(wave)

    def test_the_ordering_is_the_same_on_every_run(self):
        """M8-P2-T1-C2 (NFR-GEN-01)."""
        self.assertEqual(plan.waves(self.graph()), plan.waves(self.graph()))

    def test_changing_one_dependency_changes_the_ordering_and_nothing_else(self):
        built = self.graph()
        before = plan.waves(built)
        built[1]["dependsOn"] = []
        after = plan.waves(built)
        self.assertNotEqual(before, after)
        self.assertEqual([["M1", "M2"], ["M3"], ["M10"]], after)

    def test_a_two_digit_milestone_sorts_after_the_single_digit_ones(self):
        """Inside one wave, where plain text ordering would put M10 second."""
        built = [{"id": "M1", "dependsOn": []},
                 {"id": "M2", "dependsOn": ["M1"]},
                 {"id": "M10", "dependsOn": ["M1"]},
                 {"id": "M3", "dependsOn": ["M1"]}]
        self.assertEqual([["M1"], ["M2", "M3", "M10"]], plan.waves(built))

    def test_a_cycle_among_milestones_refuses_rather_than_looping(self):
        with self.assertRaises(plan.BrokenGraph):
            plan.waves([{"id": "M1", "dependsOn": ["M2"]},
                        {"id": "M2", "dependsOn": ["M1"]}])

    def test_the_ordering_is_derived_and_never_authored(self):
        """NFR-DAT-05: the brief states edges; nobody states a wave number."""
        index, _, _ = self.generate()
        self.assertEqual([["M1"]], index["waves"])
        self.assertNotIn("waves", plan_brief())


# ------------------------------------------------- the index and documents

class TestTheIndexAndMilestoneDocuments(Chained):
    """M8-P2-T2."""

    def test_the_index_lists_every_milestone(self):
        """M8-P2-T2-C1."""
        brief = plan_brief()
        brief["milestones"].append(
            {"id": "M2", "title": "The second thing", "summary": "More work.",
             "dependsOn": ["M1"], "exit": ["It passes."], "detailed": False,
             "phases": []})
        index, _, _ = self.generate(brief)
        listed = [row[0] for row in sections(index)["milestones"]["rows"]]
        self.assertEqual(["M1", "M2"], listed)

    def test_each_milestone_document_says_which_milestone_it_is(self):
        """M8-P2-T2-C2: the embedded identifier matches the file."""
        written, index, specs = self.author()
        for unit in specs:
            stated = specs[unit]["document"]["milestone"]
            self.assertEqual(unit, stated)
            self.assertTrue(any(os.path.basename(path).startswith(stated + "-")
                                for path in written),
                            "no file named for %s" % stated)

    def test_the_index_and_one_document_per_milestone_are_written(self):
        written, _, _ = self.author()
        self.assertEqual([plan.INDEX_FILE, "M1-the-toolchain.html"],
                         [os.path.basename(path) for path in written])

    def test_the_whole_set_satisfies_the_schema(self):
        """Plan and specifications together: a trace across them is a real link."""
        written, _, _ = self.author()
        folder = paths.resolve(self.root, paths.SPECS_DIR)
        above = [os.path.join(folder, name) for name in sorted(os.listdir(folder))
                 if name.endswith(".html")]
        grouped = validate.validate_set(written + above)
        failures = [one for found in grouped.values() for one in found
                    if one.severity == schema.FAILURE]
        self.assertEqual([], failures)

    def test_a_task_carries_its_status_and_its_criteria_into_the_document(self):
        """FR-STA-02: the document's own data is where status lives."""
        _, specs, _ = self.generate()
        first = entries(specs["M1"])[0]
        self.assertEqual("not-started", first["status"])
        self.assertEqual([False], [one["done"] for one in first["criteria"]])

    def test_regenerating_an_untouched_document_changes_nothing(self):
        """NFR-GEN-01."""
        written, _, _ = self.author()
        before = [read(path) for path in written]
        for path in written:
            plan.regenerate(self.root, os.path.basename(path))
        self.assertEqual(before, [read(path) for path in written])

    def test_the_generator_refuses_without_the_documents_above_it(self):
        empty = tempfile.mkdtemp(prefix="z2s-bare-")
        try:
            brief = plan_brief()
            with self.assertRaises(plan.MissingPrerequisite):
                plan.generate(brief, closed(gate.Gate(plan.SLUG, plan.forks(brief),
                                                      source=brief)), empty)
        finally:
            shutil.rmtree(empty, ignore_errors=True)


# ------------------------------------------------------------ the coverage

class TestTheCoverageGate(Chained):
    """The plan is checked by the engine that checks the published set (M8-06)."""

    def test_a_requirement_no_task_claims_stops_the_run(self):
        phases = detail()
        phases[0]["tasks"][0]["traces"] = {"fr": ["FR-DOC-01"]}
        with self.assertRaises(plan.Uncovered) as raised:
            self.generate(phases=phases)
        message = str(raised.exception)
        self.assertIn("FR-CTX-01", message)
        self.assertIn("Nothing was written", message)

    def test_no_file_is_written_when_the_coverage_gate_fails(self):
        phases = detail()
        phases[0]["tasks"][2]["traces"] = {"adr": ["ADR-01"]}
        self.write_detail("M1", phases)
        before = files_under(self.root)
        brief = plan_brief()
        with self.assertRaises(plan.Uncovered):
            plan.author(self.root, brief,
                        closed(gate.Gate(plan.SLUG, plan.forks(brief), source=brief)))
        self.assertEqual(before, files_under(self.root))

    def test_the_index_shows_the_matrix_the_gate_computed(self):
        """FR-TRC-04: one computation, read by the gate and by the reader."""
        index, _, _ = self.generate()
        rows = sections(index)["coverage"]["rows"]
        self.assertEqual(sorted(FUNCTIONAL + TECHNICAL + DECISIONS),
                         sorted(row[0] for row in rows))
        for row in rows:
            self.assertTrue(row[3].startswith("M1-P1-T"), row)

    def test_a_story_describing_a_requirement_does_not_count_as_claiming_it(self):
        """Only a unit of work schedules something (trace.claims)."""
        phases = detail()
        phases[0]["tasks"][0]["traces"] = {"fr": ["FR-DOC-01", "FR-DOC-02"]}
        with self.assertRaises(plan.Uncovered) as raised:
            self.generate(phases=phases)
        self.assertIn("FR-CTX-01", str(raised.exception))


# ------------------------------------------------------------- the prompts

class TestTheExecutionPrompts(Chained):
    """M8-P2-T3."""

    def test_every_prompt_names_all_five_parts(self):
        """M8-P2-T3-C1."""
        index, specs, _ = self.generate()
        found = dict(prompts(index))
        for unit in specs:
            found.update(prompts(specs[unit]))
        self.assertTrue(found)
        for name in found:
            self.assertEqual([], plan.check_prompt(found[name]), name)
            # Spelled out as well as checked: a test that only asks the checker
            # passes when the checker is the thing that broke.
            for part in ("Plan document", "Status contract", "Locked decisions",
                         "Verification gauntlet", "Report contract"):
                self.assertIn(part, found[name], "%s: %s" % (name, part))

    def test_a_prompt_repeats_the_decisions_the_gate_already_settled(self):
        """FR-EXE-03: a worker that never saw the gate invents its own answers."""
        index, _, _ = self.generate()
        body = prompts(index)["prompt-M1"]
        settled = plan.locked(self.root)
        self.assertTrue(settled)
        self.assertIn(settled[0][1].choice, body)

    def test_a_plan_whose_chain_recorded_no_decisions_is_refused(self):
        """FR-EXE-03: with nothing to apply, a worker settles every fork again."""
        folder = paths.resolve(self.root, paths.LEDGER_DIR)
        for name in os.listdir(folder):
            os.remove(os.path.join(folder, name))
        self.assertEqual([], plan.locked(self.root))
        with self.assertRaises(plan.IncompleteBrief) as raised:
            self.generate()
        self.assertIn("locked decisions", str(raised.exception))

    def test_a_prompt_names_the_gauntlet_the_brief_states(self):
        index, _, _ = self.generate()
        for command in plan_brief()["gauntlet"]:
            self.assertIn(command, prompts(index)["prompt-M1"])

    def test_the_same_words_appear_in_the_index_and_in_the_milestone_document(self):
        """M8-P2-T3 refactor: one builder, so the two cannot come to disagree."""
        index, specs, _ = self.generate()
        self.assertEqual(prompts(index)["prompt-M1"], prompts(specs["M1"])["prompt-M1"])

    def test_the_orchestrator_prompt_states_the_waves(self):
        index, _, _ = self.generate()
        self.assertIn("Wave 1: M1", prompts(index)["prompt-orchestrator"])

    def test_a_plan_with_no_gauntlet_is_refused(self):
        brief = plan_brief()
        brief.pop("gauntlet")
        with self.assertRaises(plan.IncompleteBrief) as raised:
            self.generate(brief)
        self.assertIn("gauntlet", str(raised.exception))

    def test_a_prompt_references_nothing_outside_the_repository(self):
        """NFR-EXE-04: self-contained, so no inherited context is assumed."""
        index, _, _ = self.generate()
        for name, body in prompts(index).items():
            self.assertNotIn("http://", body, name)
            self.assertNotIn("https://", body, name)


# -------------------------------------------------------- the effort signal

class TestTheEffortSignal(Chained):
    """M8-P2-T4: a hint for a person, never an input to a machine."""

    def test_the_signal_is_optional_and_renders_when_present(self):
        """M8-P2-T4-C1."""
        phases = detail()
        phases[0]["tasks"][0]["effort"] = "half a day"
        _, specs, _ = self.generate(phases=phases)
        found = entries(specs["M1"])
        self.assertEqual("half a day", found[0]["effort"])
        self.assertNotIn("effort", found[1])

    def test_no_gate_reads_the_signal(self):
        """M8-P2-T4-C2. Two ways, because either alone is easy to fool."""
        plain = detail()
        marked = detail()
        for one in marked[0]["tasks"]:
            one["effort"] = "enormous"
        self.assertEqual(
            plan.check_work([{"id": "M1", "exit": ["done"], "phases": plain}]),
            plan.check_work([{"id": "M1", "exit": ["done"], "phases": marked}]))

        for module in (trace, validate, schema, chain):
            source = read(module.__file__)
            self.assertNotIn("effort", source, module.__name__)


# ------------------------------------------------------- honest reporting

class TestWhatTheGeneratorSaysAboutItself(Chained):
    """FR-GEN-03: never report a check that did not run, or work not done."""

    def test_a_refusal_names_what_to_fix_rather_than_that_it_failed(self):
        brief = plan_brief()
        brief["milestones"][0].pop("exit")
        with self.assertRaises(plan.IncompleteBrief) as raised:
            self.generate(brief)
        message = str(raised.exception)
        self.assertIn("M1", message)
        self.assertIn("Nothing was written", message)

    def test_the_generator_reaches_no_network_and_no_clock(self):
        """NFR-GEN-01: unchanged input has to regenerate unchanged bytes."""
        source = read(plan.__file__)
        for name in ("urllib", "requests", "socket", "http.client",
                     "datetime", "random", "time"):
            self.assertNotIn("import %s" % name, source, name)


# --------------------------------------------------------- in a real browser

def drive_browser(root, index_path, milestone_path):
    """One browser run over a generated plan and the documents above it."""
    if NODE is None:
        return None, "node is not installed"

    pages = {}
    for name in os.listdir(paths.resolve(root, paths.SPECS_DIR)):
        if name.endswith(".html"):
            pages["specs/" + name] = read(paths.resolve(root, paths.SPECS_DIR, name))
    for path in (index_path, milestone_path):
        pages["plan/" + os.path.basename(path)] = read(path)

    request = {"op": "plan", "pages": pages, "index": "plan/" + plan.INDEX_FILE,
               "milestone": "M1", "phase": "M1-P1",
               "task": "M1-P1-T1", "claim": "FR-DOC-01",
               "met": "M1-P1-T2-C1", "unmet": "M1-P1-T1-C1",
               # A phrase that appears verbatim in every prompt body and
               # nowhere else in the document. Typing it must return nothing at
               # all: a prompt is instructions about the catalogue, not content
               # of it, and folding prompt text into what search reads makes
               # every keyword match every task (M14).
               "promptWord": "fresh critic every round"}
    finished = subprocess.run([NODE, PLAN_HARNESS], input=json.dumps(request),
                              capture_output=True, text=True)
    if finished.returncode == 3:
        return None, finished.stderr.strip()
    if finished.returncode != 0:
        raise AssertionError("plan harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout), None


def build_chain(root):
    """Every document above the plan, written into `root`."""
    for module, brief in ((vision, vision_brief()), (context, context_brief()),
                          (prd, prd_brief()), (fsd, covering_fsd()),
                          (stories, stories_brief()), (sdd, sdd_brief())):
        forks = module.FORKS if module is vision else module.forks(brief)
        module.author(root, brief,
                      closed(gate.Gate(module.SLUG, forks, source=brief)))


def _browser_fixture():
    """Generate one plan, drive it once, and keep what the browser reported.

    One met criterion and one unmet, deliberately: a page where every box reads
    the same way cannot show that the boxes are reading anything.
    """
    root = tempfile.mkdtemp(prefix="z2s-plan-browser-")
    try:
        build_chain(root)
        paths.ensure_layout(root)
        phases = detail()
        phases[0]["tasks"][1]["criteria"][0]["done"] = True
        # A SECOND phase, for the browser fixture alone. One phase cannot show
        # that opening a phase closes the others, and a check that could not run
        # is not a check that passed (M15). The rest of the module keeps the
        # single-phase fixture, so nothing else moves.
        phases.append({"id": "M1-P2", "title": "Finish it",
                       "summary": "What is left.", "dependsOn": ["M1-P1"],
                       "completion": ["Every task in the phase passes."],
                       "tasks": [task(1, {"fr": FUNCTIONAL[:1]}, phase="M1-P2"),
                                 task(2, {"fr": FUNCTIONAL[1:]}, phase="M1-P2")]})
        with open(plan.detail_path(root, "M1"), "w", encoding="utf-8") as handle:
            json.dump(phases, handle)

        brief = plan_brief()
        written, _, _ = plan.author(
            root, brief, closed(gate.Gate(plan.SLUG, plan.forks(brief), source=brief)))
        return drive_browser(root, written[0], written[1])
    finally:
        shutil.rmtree(root, ignore_errors=True)


#: A harness that ran and went wrong is NOT a browser that was not there, and
#: the difference is the whole of LD-04 and NFR-VAL-05: a skipped check may
#: never be counted as a pass. Reporting a crash as an absence hid a real
#: failure once — found by mutating the runtime so the harness could not reach
#: the copy button, which read as a clean skip.
BROKEN = None
try:
    SEEN, REASON = _browser_fixture()
except Exception as error:             # pragma: no cover - reported, never hidden
    SEEN, REASON, BROKEN = None, "the plan could not be generated: %s" % error, error


@unittest.skipIf(SEEN is None and BROKEN is None, "no browser available: %s" % REASON)
class TestFollowingAPlanInABrowser(unittest.TestCase):
    """The questions no amount of reading the data can answer."""

    @classmethod
    def setUpClass(cls):
        if BROKEN is not None:         # pragma: no cover - only on a real break
            raise AssertionError(
                "the browser harness failed rather than being absent; a check "
                "that could not run is not a check that passed:\n%s" % REASON)
        cls.seen = SEEN

    def test_a_wave_opens_the_milestone_it_names(self):
        """FR-PLN-09: the ordering is a place to start work, not a diagram."""
        waves = self.seen["index"]["waves"]
        self.assertEqual([[{"unit": "M1", "href": "M1-the-toolchain.html"}]], waves)
        self.assertEqual("plan/M1-the-toolchain.html", self.seen["milestone"]["file"])

    def test_a_task_shows_its_failing_test_without_the_reader_opening_anything(self):
        """ADR-06: the red step is the point, so it is not behind a click."""
        found = self.seen["milestone"]
        self.assertTrue(found["task"])
        self.assertTrue(found["taskVisible"])
        self.assertTrue(found["tddOpen"])
        self.assertEqual(["Red", "Green", "Refactor"], found["tdd"])

    def test_a_met_criterion_is_ticked_and_an_unmet_one_is_not(self):
        """M8-02: the boxes are the plan's own record."""
        self.assertEqual({"checked": True, "disabled": True}, self.seen["milestone"]["met"])
        self.assertEqual({"checked": False, "disabled": True},
                         self.seen["milestone"]["unmet"])

    def test_no_reader_can_tick_a_criterion(self):
        """A control a reader can operate is one they expect to mean something."""
        for name in ("met", "unmet"):
            self.assertTrue(self.seen["milestone"][name]["disabled"], name)

    def test_a_task_claim_reaches_the_requirement_in_the_sibling_document(self):
        """FR-TRC-07: the plan and the specifications are one set, not two."""
        self.assertEqual("../specs/FSD.html#FR-DOC-01",
                         self.seen["milestone"]["claim"])
        landed = self.seen["claimed"]
        self.assertEqual("specs/FSD.html", landed["file"])
        self.assertTrue(landed["found"])
        self.assertTrue(landed["visible"])
        self.assertTrue(landed["marked"])

    def test_the_instructions_can_be_taken_in_one_press(self):
        """FR-EXE-03: a prompt nobody can lift out is a prompt nobody uses."""
        copy = self.seen["copy"]
        # "Copy prompt", not "Copy": the button sits in the fold's summary
        # now, beside the label, where a bare verb says nothing about what it
        # would copy (M15-04).
        self.assertEqual("Copy prompt", copy["before"])
        self.assertNotEqual("Copy prompt", copy["after"])
        if copy["clipboard"] is not None:
            self.assertIn("Report contract", copy["clipboard"])

    def test_the_index_carries_the_instructions_for_every_unit(self):
        self.assertEqual(["prompt-orchestrator", "prompt-M1"],
                         self.seen["index"]["prompts"])

    # ------------------------------------------------ every granularity, M14

    def test_a_milestone_document_opens_with_its_own_instructions(self):
        """M14-04: what an operator came here to take away is at the top."""
        self.assertEqual("prompt", self.seen["milestone"]["firstSection"])

    def test_a_task_carries_its_own_instructions_as_its_first_element(self):
        found = self.seen["milestone"]
        self.assertEqual({"tag": "details", "open": False, "copy": True},
                         found["unitPrompt"])
        self.assertTrue(found["promptIsFirst"],
                        "the task's instructions are not the first thing in its card")

    def test_a_phase_carries_its_own_instructions_too(self):
        self.assertEqual({"tag": "details", "open": False, "copy": True},
                         self.seen["milestone"]["phasePrompt"])

    def test_every_level_offers_its_own_copy_button(self):
        """FR-EXE-15: the operator chooses the granularity, so each one copies."""
        # One milestone, two phases, five tasks.
        self.assertEqual(8, self.seen["milestone"]["copyButtons"])

    def test_a_word_only_a_prompt_uses_brings_no_task_back(self):
        """Fold prompt bodies into what search reads and every keyword matches
        every task, which is the keyword box not working at all."""
        found = self.seen["searched"]
        self.assertEqual(0, found["showing"])
        self.assertTrue(found["noMatch"])

    # ------------------------------------------------ navigating a plan, M15

    def test_the_first_unit_at_each_level_arrives_open_and_the_rest_are_shut(self):
        """A plan is navigated, not read end to end (FR-SPC-10, amended).

        Per parent, not per page: the first task of EVERY phase is open, so a
        reader who opens the second phase finds something in it rather than
        another wall of shut headers.
        """
        found = self.seen["arrival"]
        self.assertEqual([["M1-P1", True], ["M1-P2", False]], found["areas"])
        self.assertEqual([["M1-P1-T1", True], ["M1-P1-T2", False],
                          ["M1-P1-T3", False],
                          ["M1-P2-T1", True], ["M1-P2-T2", False]],
                         found["entries"])

    def test_an_entry_in_a_navigated_catalogue_is_a_fold(self):
        self.assertEqual("DETAILS", self.seen["arrival"]["tag"])

    def test_opening_a_phase_closes_the_other_phases(self):
        self.assertEqual([["M1-P1", False], ["M1-P2", True]],
                         self.seen["afterArea"]["areas"])
        # And it left the tasks alone: closing a phase is not closing its work.
        self.assertEqual(self.seen["arrival"]["entries"],
                         self.seen["afterArea"]["entries"])

    def test_opening_a_task_closes_the_other_tasks_in_that_phase(self):
        found = self.seen["afterEntry"]["entries"]
        self.assertEqual([["M1-P2-T1", False], ["M1-P2-T2", True]],
                         [one for one in found if one[0].startswith("M1-P2-")])
        # The other phase's open task is untouched — siblings, not cousins.
        self.assertEqual([one for one in self.seen["arrival"]["entries"]
                          if one[0].startswith("M1-P1-")],
                         [one for one in found if one[0].startswith("M1-P1-")])

    def test_a_specification_read_by_the_same_runtime_does_not_fold_at_all(self):
        """M15-06. The accordion is opted into by the section, never assumed.

        Checked on the document the claim chip leads to, which is a real
        specification rendered by this same runtime: if the opt-in leaked, every
        catalogue in the set would arrive shut.
        """
        found = self.seen["claimed"]
        self.assertFalse(found["navigated"])
        self.assertEqual("ARTICLE", found["entryTag"])
        self.assertEqual(found["areas"], found["areasOpen"])
        self.assertGreater(found["areas"], 0)

    def test_every_part_of_the_plan_is_reachable_from_every_other(self):
        """FR-SPC-09. A reader who arrives on one milestone is not stranded."""
        for page in ("index", "milestone"):
            parts = self.seen[page]["parts"]
            self.assertEqual(["Plan index", "M1"],
                             [one["label"] for one in parts], page)
        # The page you are on is stated and is not a link.
        self.assertEqual([False, True],
                         [one["here"] for one in self.seen["milestone"]["parts"]])
        self.assertIsNone(self.seen["milestone"]["parts"][1]["href"])
        self.assertEqual("index.html", self.seen["milestone"]["parts"][0]["href"])
        self.assertEqual([True, False],
                         [one["here"] for one in self.seen["index"]["parts"]])

    def test_paper_gets_every_fold_except_the_instructions(self):
        """FR-SPC-11, and the defect the accordion introduced.

        Once an entry became a fold, its instructions became one of the children
        the print rules deliberately expand — so the rule that drops them stopped
        winning and a plan printed every prompt. Asked of what the browser
        computed, because reading the stylesheet is what missed it.
        """
        found = self.seen["printed"]
        self.assertGreater(found["bodies"], 10)
        self.assertEqual(found["prompts"], found["promptsHidden"])
        self.assertGreater(found["prompts"], 5)
        # Five tasks, so five hidden children — one set of instructions each,
        # and nothing else about an entry is withheld from paper.
        self.assertEqual(5, found["bodiesHidden"])


if __name__ == "__main__":              # pragma: no cover
    unittest.main()
