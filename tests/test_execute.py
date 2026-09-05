# -*- coding: utf-8 -*-
"""What the orchestrator must do, and what it must never do (M11).

The worker in these tests is a small Python script written per case. That is the
point of a worker being a command: the contract can be exercised end to end with
nothing installed, no agent, and no network — and a test can make a worker
behave exactly as badly as the rule under test needs it to.
"""

import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from z2s import dispatch, execute, gate, gauntlet, layers, paths, plan, schema, status  # noqa: E402
from test_plan import build_chain, closed, detail, plan_brief, task  # noqa: E402

PACKAGE = os.path.join(os.path.dirname(HERE), "z2s")

#: A worker that does the right thing: records a check it saw fail, names the
#: command that showed the criteria met, and writes its report where it was told.
GOOD = """\
import json, re, sys
brief = open(sys.argv[1], encoding="utf-8").read()
found = re.search(r"M[0-9]+-P[0-9]+-T[0-9]+", brief)
json.dump({"unit": found.group(0) if found else "?",
           "red": {"command": "python3 -m unittest", "code": 1},
           "commands": [{"command": "python3 -m unittest", "code": 0}],
           "criteria": {}, "changes": [], "denied": [],
           "decisions": %(decisions)s},
          open(sys.argv[2], "w", encoding="utf-8"))
open(%(trace)r, "a", encoding="utf-8").write(brief.split("\\n")[0] + "\\n")
"""

#: A worker that does everything right except name a file that exists. Git can
#: neither find nor track it, and one bad path aborts the whole `git add`.
GHOST = """\
import json, re, sys
brief = open(sys.argv[1], encoding="utf-8").read()
found = re.search(r"M[0-9]+-P[0-9]+-T[0-9]+", brief)
json.dump({"unit": found.group(0) if found else "?",
           "red": {"command": "python3 -m unittest", "code": 1},
           "commands": [{"command": "python3 -m unittest", "code": 0}],
           "criteria": {}, "changes": ["never-written.py"], "denied": [],
           "decisions": []},
          open(sys.argv[2], "w", encoding="utf-8"))
"""

#: A judge that passes everything, and records the brief it was handed so a test
#: can look at what it was and was not shown.
JUDGE = """\
import json, sys
open(%(trace)r, "a", encoding="utf-8").write(
    open(sys.argv[1], encoding="utf-8").read())
json.dump(%(answer)s, open(sys.argv[2], "w", encoding="utf-8"))
"""


def script(directory, name, body):
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)
    return path


def worker(name, role, path, **extra):
    made = {"name": name, "role": role,
            "command": [sys.executable, path,
                        execute.BRIEF_PLACEHOLDER, execute.REPORT_PLACEHOLDER]}
    made.update(extra)
    return made


class Project(unittest.TestCase):
    """A real generated plan on disk, with real worker scripts beside it."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-exec-")
        self.bin = tempfile.mkdtemp(prefix="z2s-exec-bin-")
        build_chain(self.root)
        paths.ensure_layout(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.bin, ignore_errors=True)

    # ---------------------------------------------------------------- fixtures

    def plan(self, phases=None, brief=None):
        made = plan_brief() if brief is None else brief
        with open(plan.detail_path(self.root, "M1"), "w", encoding="utf-8") as handle:
            json.dump(detail() if phases is None else phases, handle)
        return plan.author(self.root, made,
                           closed(gate.Gate(plan.SLUG, plan.forks(made), source=made)))

    def builder(self, body=None, decisions="[]", name="builder", **extra):
        trace = os.path.join(self.bin, "%s-briefs.txt" % name)
        body = GOOD % {"decisions": decisions, "trace": trace} if body is None else body
        return worker(name, execute.BUILD,
                      script(self.bin, "%s.py" % name, body), **extra), trace

    def judge(self, answer='{"verdict": "pass"}', name="judge"):
        trace = os.path.join(self.bin, "%s-briefs.txt" % name)
        return worker(name, execute.JUDGE,
                      script(self.bin, "%s.py" % name,
                             JUDGE % {"trace": trace, "answer": answer})), trace

    def configure(self, workers=None, **extra):
        if workers is None:
            build, _ = self.builder()
            judged, _ = self.judge()
            workers = [build, judged]
        held = {"workers": workers,
                "gauntlet": {"unit": [sys.executable, "-c", "pass"]},
                "ceiling": 2, "attempts": 3, "commit": False}
        held.update(extra)
        path = paths.resolve(self.root, execute.SETTINGS)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(held, handle)
        return held

    def drive(self):
        out = open(os.devnull, "w")
        try:
            return execute.run(self.root, out)
        finally:
            out.close()

    def states(self):
        return {unit.id: execute.state(unit)
                for unit in execute.units(self.root).values()}

    def read(self, path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()


# --------------------------------------------------------------- the settings

class TestTheProjectMustSayWhatItsWorkersAre(Project):

    def test_a_run_with_no_settings_refuses_before_anything_starts(self):
        self.plan()
        with self.assertRaises(execute.Refused) as caught:
            execute.settings(self.root)
        self.assertIn("workers", str(caught.exception))

    def test_a_worker_that_cannot_be_told_what_to_do_is_refused(self):
        self.plan()
        broken = {"name": "mute", "role": execute.BUILD, "command": ["true"]}
        self.configure(workers=[broken, self.judge()[0]])
        with self.assertRaises(execute.Refused) as caught:
            execute.settings(self.root)
        self.assertIn(execute.BRIEF_PLACEHOLDER, str(caught.exception))

    def test_a_project_with_no_judge_is_refused(self):
        self.plan()
        self.configure(workers=[self.builder()[0]])
        with self.assertRaises(execute.Refused) as caught:
            execute.settings(self.root)
        self.assertIn(execute.JUDGE, str(caught.exception))

    def test_a_gauntlet_naming_an_unknown_layer_is_refused(self):
        self.plan()
        self.configure(gauntlet={"vibes": ["true"]})
        with self.assertRaises(execute.Refused) as caught:
            execute.settings(self.root)
        self.assertIn("verification layer", str(caught.exception))


# --------------------------------------------------------- M11-P1-T1 ready set

class TestTheReadySet(Project):

    def test_a_human_gated_unit_never_enters_the_ready_set(self):
        phases = detail()
        phases[0]["tasks"][0]["autonomy"] = schema.HUMAN_GATE
        self.plan(phases)
        config = self.configure()
        eligible = [unit.id for unit in execute.ready(
            execute.units(self.root), execute.blank(), config)]
        self.assertNotIn("M1-P1-T1", eligible)
        self.assertIn("M1-P1-T2", eligible)

    def test_a_unit_waiting_on_unfinished_work_never_enters(self):
        phases = detail()
        phases[0]["tasks"][1]["dependsOn"] = ["M1-P1-T1"]
        self.plan(phases)
        config = self.configure()
        eligible = [unit.id for unit in execute.ready(
            execute.units(self.root), execute.blank(), config)]
        self.assertIn("M1-P1-T1", eligible)
        self.assertNotIn("M1-P1-T2", eligible)

    def test_a_status_changed_outside_the_run_is_read_on_the_next_iteration(self):
        self.plan()
        config = self.configure()
        first = [unit.id for unit in execute.ready(
            execute.units(self.root), execute.blank(), config)]
        self.assertIn("M1-P1-T1", first)

        status.set_status(self.root, "M1-P1-T1", schema.IN_PROGRESS)
        second = [unit.id for unit in execute.ready(
            execute.units(self.root), execute.blank(), config)]
        self.assertNotIn("M1-P1-T1", second,
                         "the ready set is recomputed from the documents, so an "
                         "edit between iterations has to be picked up")

    def test_a_unit_out_of_attempts_stays_out(self):
        self.plan()
        config = self.configure()
        ledger = execute.blank()
        ledger["attempts"]["M1-P1-T1"] = config["attempts"]
        eligible = [unit.id for unit in execute.ready(
            execute.units(self.root), ledger, config)]
        self.assertNotIn("M1-P1-T1", eligible)

    def test_the_ready_set_can_be_printed(self):
        self.plan()
        self.configure()
        printed = execute.format_ready(self.root)
        self.assertIn("M1-P1-T1", printed)


# ------------------------------------------------------ M11-P1-T2 wave-ordered

class TestWaveOrderedDispatch(Project):

    def two_milestones(self):
        brief = plan_brief()
        brief["milestones"].append(
            {"id": "M2", "title": "The second thing",
             "summary": "Work that waits for the first milestone.",
             "dependsOn": ["M1"], "exit": ["It passes."], "detailed": True})
        second = [{"id": "M2-P1", "title": "Later", "summary": "The later work.",
                   "dependsOn": [], "completion": ["It passes."],
                   "tasks": [task(1, {"fr": ["FR-DOC-01"]}, phase="M2-P1")]}]
        with open(plan.detail_path(self.root, "M2"), "w", encoding="utf-8") as handle:
            json.dump(second, handle)
        return brief

    def test_no_unit_starts_before_its_wave_is_eligible(self):
        self.plan(brief=self.two_milestones())
        config = self.configure()
        rounds = execute.order(self.root)
        self.assertEqual(rounds[0], ["M1"])
        found = execute.units(self.root)
        wave = execute.current(rounds, found, execute.blank(), config)
        eligible = [unit.id for unit in execute.ready(
            found, execute.blank(), config, wave)]
        self.assertTrue(eligible)
        self.assertFalse([one for one in eligible if one.startswith("M2")],
                         "a later wave must not be dispatched while the first "
                         "has work left in it")

    def test_work_beyond_the_ceiling_queues_rather_than_failing(self):
        self.plan()
        candidates = list(execute.units(self.root).values())
        for unit in candidates:
            unit.entry["writes"] = ["src/%s.py" % unit.id]
        picked = execute.dispatchable(candidates, [], 2)
        self.assertEqual(len(picked), 2)
        self.assertEqual([one.id for one in picked],
                         [one.id for one in candidates[:2]],
                         "the rest wait their turn; nothing is refused")


# --------------------------------------------------- M11-P1-T3 write-set safety

class TestWriteSetDisjointness(Project):

    def unit(self, identifier, declared):
        return execute.Unit(identifier, {"id": identifier, "writes": declared},
                            "plan.html", "M1")

    def test_overlapping_write_sets_are_never_concurrent(self):
        first = self.unit("A", ["src/one.py"])
        second = self.unit("B", ["src/one.py"])
        third = self.unit("C", ["src/two.py"])
        self.assertTrue(execute.collides(first, second))
        self.assertFalse(execute.collides(first, third))
        self.assertEqual([one.id for one in
                          execute.dispatchable([first, second, third], [], 3)],
                         ["A", "C"])

    def test_a_directory_contains_the_files_beneath_it(self):
        self.assertTrue(execute.collides(self.unit("A", ["src"]),
                                         self.unit("B", ["src/deep/one.py"])))

    def test_two_units_writing_into_one_test_directory_never_run_together(self):
        """The collision this bug left unguarded on every generated plan.

        Not a new rule — `collides` always computed it correctly. The rule was
        void because no unit declared a test path at all, so units that all
        write into one test directory were computed as disjoint and dispatched
        side by side. The guard is only as good as the declaration reaching it.
        """
        first = self.unit("A", ["src/storage/**", "tests/integration/store.test.ts"])
        second = self.unit("B", ["src/db/**", "tests/integration/schema.test.ts"])
        self.assertFalse(execute.collides(first, second),
                         "distinct files in one directory are not a collision")
        broad = self.unit("C", ["src/api/**", "tests/integration/**"])
        self.assertTrue(execute.collides(first, broad),
                        "a unit claiming the whole directory collides with every "
                        "unit writing inside it")
        self.assertEqual([one.id for one in
                          execute.dispatchable([first, broad], [], 3)], ["A"])

    def test_a_pattern_and_a_path_beneath_it_are_the_same_claim(self):
        """Every real plan declares patterns — the documented example is one —
        and this check compared whole strings, so `src/storage/**` matched
        nothing at all beneath itself. Two units were computed as disjoint on
        the strength of a claim neither of them could read."""
        self.assertTrue(execute.collides(
            self.unit("A", ["src/storage/**"]),
            self.unit("B", ["src/storage/client.ts"])))
        self.assertFalse(execute.collides(
            self.unit("A", ["src/storage/**"]),
            self.unit("B", ["src/db/**"])),
            "widening a pattern to its directory must not swallow its siblings")

    def test_a_pattern_in_the_first_segment_claims_everything(self):
        self.assertTrue(execute.collides(self.unit("A", ["**"]),
                                         self.unit("B", ["docs/install.md"])))

    def test_a_unit_declaring_nothing_runs_alone(self):
        quiet = self.unit("A", [])
        other = self.unit("B", ["src/two.py"])
        self.assertTrue(execute.collides(quiet, other))
        self.assertEqual([one.id for one in
                          execute.dispatchable([quiet, other], [], 3)], ["A"])

    def test_a_declared_write_set_survives_into_the_document(self):
        """The rule is only worth anything if the declaration reaches the reader.

        Every other case here builds its units by hand, which proves the
        judgement and proves nothing about the plumbing: a generator that
        quietly dropped the field would leave every unit declaring nothing, and
        every unit declaring nothing runs alone — slow, silent, and wrong for a
        reason nobody could see.
        """
        phases = detail()
        phases[0]["tasks"][0]["writes"] = ["src/one.py", "tests/test_one.py"]
        phases[0]["tasks"][1]["writes"] = ["src/two.py", "tests/test_two.py"]
        self.plan(phases)
        found = execute.units(self.root)
        self.assertEqual(found["M1-P1-T1"].entry.get("writes"),
                         ["src/one.py", "tests/test_one.py"])
        self.assertFalse(execute.collides(found["M1-P1-T1"], found["M1-P1-T2"]))
        self.assertTrue(execute.collides(found["M1-P1-T1"], found["M1-P1-T3"]),
                        "the third task declares nothing, so it runs alone")

    def test_a_second_consecutive_edit_conflict_is_called_contention(self):
        self.plan()
        ledger = execute.blank()
        unit = execute.units(self.root)["M1-P1-T1"]
        # A document that changed underneath the run: the status tool refuses,
        # and this module has to say what a repeat of that means.
        with open(unit.document, "a", encoding="utf-8") as handle:
            handle.write("\n<!-- somebody else was here -->\n")
        original = status.rewrite

        def refuse(path, html, spec):
            raise status.Refused("%s changed while this change was being prepared"
                                 % path)
        status.rewrite = refuse
        try:
            first = execute._write(self.root, ledger, unit, schema.IN_PROGRESS)
            second = execute._write(self.root, ledger, unit, schema.IN_PROGRESS)
        finally:
            status.rewrite = original
        self.assertIn("changed while", first)
        self.assertNotIn("contention", first)
        self.assertIn("contention", second)


# ------------------------------------------------- M11-P1-T4 worker selection

class TestCostAwareSelection(Project):

    def test_the_cheapest_suitable_worker_is_chosen(self):
        cheap, _ = self.builder(name="cheap")
        dear, _ = self.builder(name="dear")
        cheap["cost"], dear["cost"] = 1, 5
        self.plan()
        config = self.configure(workers=[dear, cheap, self.judge()[0]])
        entry = execute.units(self.root)["M1-P1-T1"].entry
        self.assertEqual(execute.choose(config, entry)["name"], "cheap")

    def test_a_worker_that_does_not_suit_the_layer_is_not_chosen(self):
        cheap, _ = self.builder(name="cheap", suits=["prose"])
        dear, _ = self.builder(name="dear")
        cheap["cost"], dear["cost"] = 1, 5
        self.plan()
        config = self.configure(workers=[cheap, dear, self.judge()[0]])
        entry = execute.units(self.root)["M1-P1-T1"].entry
        self.assertEqual(execute.choose(config, entry)["name"], "dear")

    def test_a_unit_may_name_its_own_worker(self):
        cheap, _ = self.builder(name="cheap")
        dear, _ = self.builder(name="dear")
        cheap["cost"], dear["cost"] = 1, 5
        phases = detail()
        phases[0]["tasks"][0]["worker"] = "dear"
        self.plan(phases)
        config = self.configure(workers=[cheap, dear, self.judge()[0]])
        entry = execute.units(self.root)["M1-P1-T1"].entry
        self.assertEqual(execute.choose(config, entry)["name"], "dear")

    def test_selection_never_changes_the_verification_gauntlet(self):
        cheap, _ = self.builder(name="cheap")
        dear, _ = self.builder(name="dear")
        cheap["cost"], dear["cost"] = 1, 5
        self.plan()
        config = self.configure(workers=[cheap, dear, self.judge()[0]])
        entry = execute.units(self.root)["M1-P1-T1"].entry
        bar = execute.gauntlet(config, entry)
        entry["worker"] = "dear"
        self.assertEqual(execute.choose(config, entry)["name"], "dear")
        self.assertEqual(execute.gauntlet(config, entry), bar,
                         "a cheaper builder must not get an easier bar")


# ------------------------------------------------------- M11-P2-T1 the brief

class TestTheBuilderBrief(Project):

    def test_every_brief_carries_all_five_required_parts(self):
        self.plan()
        config = self.configure()
        for unit in execute.units(self.root).values():
            text = execute.brief(self.root, config, unit)
            self.assertEqual(plan.check_prompt(text), [], unit.id)

    def test_the_brief_names_nothing_outside_the_project(self):
        self.plan()
        config = self.configure()
        text = execute.brief(self.root, config,
                             execute.units(self.root)["M1-P1-T1"])
        self.assertNotIn(self.root, text,
                         "a brief names paths inside the project, not this "
                         "machine's directory layout")

    def test_the_brief_states_the_unit_and_its_criteria(self):
        self.plan()
        config = self.configure()
        text = execute.brief(self.root, config,
                             execute.units(self.root)["M1-P1-T1"])
        self.assertIn("M1-P1-T1", text)
        self.assertIn("M1-P1-T1-C1", text)
        self.assertIn("Red:", text)

    def test_a_retry_is_briefed_with_the_gap(self):
        self.plan()
        config = self.configure()
        text = execute.brief(self.root, config,
                             execute.units(self.root)["M1-P1-T1"],
                             gap="the error message says nothing useful")
        self.assertIn("the error message says nothing useful", text)


# ------------------------------------------------ M11-P2-T2/T3 the report rules

class TestTheReportContract(Project):

    def test_a_worker_returning_no_report_fails_its_unit(self):
        silent, _ = self.builder(body="import sys\n")
        self.plan()
        self.configure(workers=[silent, self.judge()[0]])
        ledger = self.drive()
        self.assertEqual(self.states()["M1-P1-T1"], schema.BLOCKED)
        self.assertIn("no report", ledger["unfinished"]["M1-P1-T1"])

    def test_a_report_with_no_observed_failing_test_is_rejected(self):
        self.assertTrue([one for one in execute.check_report({})
                         if "failing test" in one])
        self.assertTrue([one for one in execute.check_report(
            {"red": {"command": "x", "code": 0}}) if "exited zero" in one])
        self.assertEqual(execute.check_report(
            {"red": {"command": "x", "code": 1}}), [])

    def test_a_verification_claim_must_name_its_command(self):
        claimed = {"red": {"command": "x", "code": 1},
                   "criteria": {"M1-P1-T1-C1": True}}
        self.assertTrue([one for one in execute.check_report(claimed)
                         if "names no command" in one])
        claimed["commands"] = [{"command": "python3 -m unittest", "code": 0}]
        claimed["changes"] = ["z2s/thing.py"]
        self.assertEqual(execute.check_report(claimed), [])

    def test_a_verification_claim_must_name_the_files_it_changed(self):
        """The key that fed the commit, and that no brief ever named.

        A report with no `changes` passed every check, so a unit was built,
        judged and committed — and the commit held the plan document alone,
        while the work it recorded as verified stayed untracked.
        """
        claimed = {"red": {"command": "x", "code": 1},
                   "criteria": {"M1-P1-T1-C1": True},
                   "commands": [{"command": "python3 -m unittest", "code": 0}]}
        for nothing in ({}, {"changes": []}, {"changes": ["", "  "]}):
            report = dict(claimed, **nothing)
            self.assertTrue([one for one in execute.check_report(report)
                             if "names no changed file" in one], nothing)
        claimed["changes"] = ["z2s/thing.py"]
        self.assertEqual(execute.check_report(claimed), [])

    def test_a_report_answering_for_another_unit_is_caught(self):
        sound = {"red": {"command": "x", "code": 1},
                 "criteria": {"M1-P1-T1-C1": True},
                 "commands": [{"command": "python3 -m unittest", "code": 0}],
                 "changes": ["z2s/thing.py"], "unit": "M9-P9-T9"}
        self.assertTrue([one for one in execute.check_report(sound, "M1-P1-T1")
                         if "the brief was for" in one])
        sound["unit"] = "M1-P1-T1"
        self.assertEqual(execute.check_report(sound, "M1-P1-T1"), [])

    def test_criteria_written_as_a_list_are_read_not_crashed_on(self):
        """The contract names no shape, so a list of {id, met} is a fair reading.

        It used to raise AttributeError out of settle(), and nothing in this
        module catches one — so one sloppy worker took the whole run down with
        it, not just its own unit.
        """
        listed = {"red": {"command": "x", "code": 1},
                  "criteria": [{"id": "M1-P1-T1-C1", "met": True}]}
        self.assertTrue([one for one in execute.check_report(listed)
                         if "names no command" in one])
        listed["commands"] = [{"command": "python3 -m unittest", "code": 0}]
        listed["changes"] = ["z2s/thing.py"]
        self.assertEqual(execute.check_report(listed), [])

    def test_criteria_of_no_readable_shape_are_named_not_ignored(self):
        """Coercing an unreadable shape to nothing silently turns the rule off."""
        for shape in ("all met", 5, ["M1-P1-T1-C1"], [{"met": True}]):
            report = {"red": {"command": "x", "code": 1}, "criteria": shape}
            self.assertTrue([one for one in execute.check_report(report)
                             if "not readable" in one], shape)

    def test_a_malformed_report_fails_the_unit_rather_than_passing_it(self):
        sloppy, _ = self.builder(body=(
            "import json, sys\n"
            "json.dump({'changes': []}, open(sys.argv[2], 'w'))\n"))
        self.plan()
        self.configure(workers=[sloppy, self.judge()[0]])
        self.drive()
        self.assertEqual(self.states()["M1-P1-T1"], schema.BLOCKED)


# ------------------------------------------------------- M11-P2-T4 the guards

class TestUnattendedSafety(Project):

    def test_a_prohibited_command_is_refused_and_not_reshaped(self):
        self.plan()
        forbidden = {"name": "reckless", "role": execute.BUILD,
                     "command": ["git", "push", "--force", "origin", "main",
                                 execute.BRIEF_PLACEHOLDER,
                                 execute.REPORT_PLACEHOLDER]}
        config = self.configure(workers=[forbidden, self.judge()[0]])
        config = execute.settings(self.root)
        unit = execute.units(self.root)["M1-P1-T1"]
        result = execute.run_worker(self.root, config, unit, execute.BUILD,
                                    "a brief", 1)
        self.assertIsNone(result.report)
        self.assertIn("force", result.reason.lower())
        self.assertFalse(os.path.exists(os.path.join(
            execute.place(self.root, unit.id, 1, execute.BUILD), "report.json")),
            "a refused command must not have run in some other shape")

    def test_no_credential_shaped_variable_reaches_a_worker(self):
        self.plan()
        config = self.configure()
        config = execute.settings(self.root)
        entry = execute.units(self.root)["M1-P1-T1"].entry
        os.environ["Z2S_TEST_API_TOKEN"] = "not-a-real-one"
        os.environ["Z2S_TEST_PLAIN"] = "fine"
        try:
            environ = execute.environment(config, entry)
        finally:
            del os.environ["Z2S_TEST_API_TOKEN"], os.environ["Z2S_TEST_PLAIN"]
        self.assertNotIn("Z2S_TEST_API_TOKEN", environ)
        self.assertIn("Z2S_TEST_PLAIN", environ)

    def test_a_substituted_unit_gets_the_substitute_it_names(self):
        phases = detail()
        phases[0]["tasks"][0]["autonomy"] = schema.AUTO_WITH_MOCK
        phases[0]["tasks"][0]["provider"] = "WEATHER_ENDPOINT"
        self.plan(phases)
        self.configure(substitutes={"WEATHER_ENDPOINT": "http://localhost:0/fake"})
        config = execute.settings(self.root)
        entry = execute.units(self.root)["M1-P1-T1"].entry
        self.assertEqual(execute.environment(config, entry)["WEATHER_ENDPOINT"],
                         "http://localhost:0/fake")

    def test_a_substituted_unit_with_no_substitute_configured_is_refused(self):
        phases = detail()
        phases[0]["tasks"][0]["autonomy"] = schema.AUTO_WITH_MOCK
        phases[0]["tasks"][0]["provider"] = "WEATHER_ENDPOINT"
        self.plan(phases)
        self.configure()
        config = execute.settings(self.root)
        entry = execute.units(self.root)["M1-P1-T1"].entry
        with self.assertRaises(execute.Refused) as caught:
            execute.environment(config, entry)
        self.assertIn("WEATHER_ENDPOINT", str(caught.exception))

    DENYING = ("import json, sys\n"
               "json.dump({'red': {'command': 'x', 'code': 1},\n"
               "           'denied': [{'action': 'read ~/.ssh/id_rsa',\n"
               "                       'rule': 'outside the project area'}]},\n"
               "          open(sys.argv[2], 'w'))\n")

    def test_a_denied_permission_is_reported_with_its_rule(self):
        denied, _ = self.builder(body=self.DENYING)
        self.plan()
        self.configure(workers=[denied, self.judge()[0]], attempts=1)
        ledger = self.drive()
        noted = " ".join(ledger["notes"])
        self.assertIn("read ~/.ssh/id_rsa", noted)
        self.assertIn("outside the project area", noted,
                      "a denial is reported with the rule that blocked it "
                      "(NFR-SEC-05)")
        self.assertNotIn("M1-P1-T1", ledger["unfinished"],
                         "a denial is what the plan would not let the unit do, "
                         "not evidence about the work: failing the attempt for "
                         "it makes the honest answer the losing one")

    def test_a_denial_does_not_keep_the_unit_from_its_own_gauntlet(self):
        denied, _ = self.builder(body=self.DENYING)
        self.plan()
        self.configure(workers=[denied, self.judge()[0]], attempts=1,
                       gauntlet={"unit": [sys.executable, "-c",
                                          "raise SystemExit(1)"]})
        ledger = self.drive()
        self.assertIn("unit failed", ledger["unfinished"]["M1-P1-T1"],
                      "the criteria decide, so the checks have to run: a unit "
                      "that recorded a denial was failing before its gauntlet "
                      "ever started")

    def test_no_module_asks_a_question_of_a_person(self):
        for name in sorted(os.listdir(PACKAGE)):
            if not name.endswith(".py"):
                continue
            body = self.read(os.path.join(PACKAGE, name))
            self.assertNotIn("input(", body,
                             "%s would stop an unattended run dead" % name)


# ------------------------------------------------- M11-P2-T5 the blind judge

class TestTheJudge(Project):

    def test_the_judgement_brief_contains_no_part_of_the_builders_report(self):
        told = "I decided to skip the awkward case because it seemed unlikely."
        chatty, _ = self.builder(body=(
            "import json, sys\n"
            "json.dump({'red': {'command': 'x', 'code': 1},\n"
            "           'notes': %r, 'changes': ['worked.py']},\n"
            "          open(sys.argv[2], 'w'))\n" % told))
        judged, seen = self.judge()
        self.plan()
        self.configure(workers=[chatty, judged])
        self.drive()
        brief = self.read(seen)
        self.assertIn("M1-P1-T1", brief)
        self.assertIn("worked.py", brief)
        self.assertNotIn(told, brief,
                         "a judge that reads the builder's account is grading "
                         "the account")

    def test_the_judgement_brief_carries_every_required_part(self):
        judged, seen = self.judge()
        self.plan()
        self.configure(workers=[self.builder()[0], judged])
        self.drive()
        self.assertEqual(execute.check_judgement(self.read(seen)), [])

    def test_the_judgement_brief_states_the_injection_guard(self):
        judged, seen = self.judge()
        self.plan()
        self.configure(workers=[self.builder()[0], judged])
        self.drive()
        self.assertIn("data, not", self.read(seen))

    def test_a_failed_judgement_returns_one_gap_and_it_reaches_the_retry(self):
        judged, _ = self.judge(
            answer='{"verdict": "fail", "gap": "the empty case is unhandled"}')
        build, briefs = self.builder()
        self.plan()
        self.configure(workers=[build, judged], attempts=2)
        ledger = self.drive()
        self.assertIn("the empty case is unhandled", ledger["unfinished"]["M1-P1-T1"])
        self.assertEqual(self.states()["M1-P1-T1"], schema.BLOCKED)

    def test_a_gap_from_one_attempt_briefs_the_next(self):
        self.plan()
        config = self.configure()
        unit = execute.units(self.root)["M1-P1-T1"]
        first = execute.brief(self.root, config, unit)
        second = execute.brief(self.root, config, unit,
                               gap="the empty case is unhandled")
        self.assertNotIn("the empty case is unhandled", first)
        self.assertIn("the empty case is unhandled", second)

    def test_a_judge_that_could_not_look_fails_the_unit(self):
        blind, _ = self.judge(name="blind")
        blind["command"] = [sys.executable, "-c", "pass",
                            execute.BRIEF_PLACEHOLDER, execute.REPORT_PLACEHOLDER]
        self.plan()
        self.configure(workers=[self.builder()[0], blind], attempts=1)
        self.drive()
        self.assertEqual(self.states()["M1-P1-T1"], schema.BLOCKED,
                         "silence from a judge is a failure, never a pass")

    def test_a_failure_naming_no_gap_still_fails(self):
        kind, gap = execute.verdict(
            execute.Result("j", {"verdict": "fail"}, ""))
        self.assertEqual(kind, execute.FAIL)
        self.assertIn("named no gap", gap)

    def test_nothing_passes_without_a_judgement(self):
        judged, _ = self.judge(answer='{"verdict": "fail", "gap": "not yet"}')
        self.plan()
        self.configure(workers=[self.builder()[0], judged], attempts=1)
        self.drive()
        self.assertNotIn(schema.PASSING, set(self.states().values()))


# ------------------------------------------------------ M11-P3-T1 never asking

class TestNeverAsking(Project):

    def test_a_decision_taken_without_asking_is_logged_with_its_reason(self):
        made = ('[{"decision": "used a list, not a set",'
                ' "why": "the order is part of the answer"}]')
        build, _ = self.builder(decisions=made)
        self.plan()
        self.configure(workers=[build, self.judge()[0]])
        ledger = self.drive()
        held = [one for one in ledger["decisions"] if one["unit"] == "M1-P1-T1"]
        self.assertTrue(held)
        self.assertEqual(held[0]["why"], "the order is part of the answer")

    def test_the_summary_names_the_decisions_nobody_was_asked_about(self):
        made = ('[{"decision": "used a list, not a set",'
                ' "why": "the order is part of the answer"}]')
        build, _ = self.builder(decisions=made)
        self.plan()
        self.configure(workers=[build, self.judge()[0]])
        ledger = self.drive()
        self.assertIn("used a list, not a set", execute.summary(self.root, ledger))


# ------------------------------------------------ M11-P3-T2 blockers and retries

class TestAWorkerCannotGradeItself(Project):
    """FR-EXE-14, defended against the worker rather than only against the judge.

    Every builder used to be told "set it with the status command", and builders
    did — including setting themselves verified. Two things then went wrong at
    once: the run's own write of that status was allowed through as a repeat
    rather than a move, and the demote it needed when the work fell short is not
    a move that status may make. So the unit kept the status it gave itself,
    dropped out of the ready set, and was never attempted again.
    """

    #: A builder that records its own verdict before writing its report.
    GREEDY = ("import json, re, subprocess, sys\n"
              "brief = open(sys.argv[1], encoding='utf-8').read()\n"
              "unit = re.search(r'M[0-9]+-P[0-9]+-T[0-9]+', brief).group(0)\n"
              "subprocess.run([sys.executable, '-m', 'z2s.status', 'set', unit,\n"
              "                %(status)r, '--root', %(root)r], cwd=%(package)r,\n"
              "               capture_output=True)\n"
              "json.dump({'unit': unit, 'red': {'command': 'x', 'code': 1}},\n"
              "          open(sys.argv[2], 'w'))\n")

    def greedy(self, claimed):
        return self.builder(body=self.GREEDY % {
            "status": claimed, "root": self.root,
            "package": os.path.dirname(PACKAGE)})[0]

    def test_a_builder_that_passes_itself_is_failed_and_tried_again(self):
        self.plan()
        # Evidence for the layer, so the status command would otherwise let the
        # claim through: the point is the claim, not a missing check.
        status.record(self.root, "unit", "python3 -m unittest", 0)
        self.configure(workers=[self.greedy(schema.PASSING), self.judge()[0]],
                       attempts=1, ceiling=1)
        ledger = self.drive()
        self.assertIn("M1-P1-T1", ledger["unfinished"])
        self.assertIn("never by the worker that built it",
                      ledger["unfinished"]["M1-P1-T1"])
        self.assertNotEqual(self.states()["M1-P1-T1"], schema.PASSING,
                            "a unit must not keep a status it gave itself")

    def test_the_run_can_still_move_a_unit_a_worker_has_written_on(self):
        """The demote that used to be refused outright."""
        self.plan()
        status.record(self.root, "unit", "python3 -m unittest", 0)
        self.configure(workers=[self.greedy(schema.PASSING), self.judge()[0]],
                       attempts=2, ceiling=1)
        self.drive()
        self.assertEqual(self.states()["M1-P1-T1"], schema.BLOCKED)

    def test_a_dispatched_brief_never_tells_a_worker_to_set_the_status(self):
        self.plan()
        config = self.configure()
        found = execute.units(self.root)
        text = execute.brief(self.root, config, found["M1-P1-T1"])
        self.assertNotIn(gauntlet.OWN_STATUS, text)
        self.assertIn(gauntlet.RUN_STATUS, text)

    def test_a_unit_nobody_touched_is_not_accused_of_anything(self):
        self.plan()
        config = self.configure()
        found = execute.units(self.root)
        execute._write(self.root, execute.blank(), found["M1-P1-T1"],
                       schema.IN_PROGRESS)
        self.assertEqual("", execute.reclaim(self.root, execute.blank(),
                                             execute.units(self.root)["M1-P1-T1"]))


class TestAUnitNobodyCouldCommitIsNotPassing(Project):
    """A commit is one thing: one unstageable path takes the work, the plan
    document and the status change down with it. Recording passing on top of
    that is a status true of a tree nobody has (NFR-EXE-11)."""

    def setUp(self):
        Project.setUp(self)
        for arguments in (("init", "-q"),
                          ("config", "user.email", "build@example.test"),
                          ("config", "user.name", "The build"),
                          ("config", "commit.gpgsign", "false")):
            subprocess.run(("git", "-C", self.root) + arguments,
                           capture_output=True, check=False)

    def log(self):
        return subprocess.run(("git", "-C", self.root, "log", "--oneline"),
                              capture_output=True, text=True).stdout.strip()

    def test_a_unit_whose_commit_failed_is_failed_and_told_what_git_said(self):
        ghost, _ = self.builder(body=GHOST)
        self.plan()
        self.configure(workers=[ghost, self.judge()[0]],
                       attempts=1, ceiling=1, commit=True)

        ledger = self.drive()
        self.assertNotEqual(self.states()["M1-P1-T1"], schema.PASSING,
                            "nothing was recorded anywhere, so there is nothing "
                            "for passing to be true of")
        self.assertEqual("", self.log(), "and no commit was made")
        self.assertIn("never-written.py", ledger["unfinished"]["M1-P1-T1"],
                      "the next attempt is told which path git could not take, "
                      "because it is the report that was wrong")

    def test_a_unit_that_names_what_it_really_wrote_passes_and_commits(self):
        made, _ = self.builder(body=GHOST.replace(
            '"changes": ["never-written.py"]',
            '"changes": ["worked.py"]').replace(
                "brief = open", "open('worked.py', 'w').write('# the work\\n')\n"
                "brief = open"))
        self.plan()
        self.configure(workers=[made, self.judge()[0]],
                       attempts=1, ceiling=1, commit=True)

        self.drive()
        self.assertEqual(self.states()["M1-P1-T1"], schema.PASSING)
        self.assertIn("M1-P1-T1", self.log())


class TestABlockIsNotTerminalInTheDocumentEither(Project):
    """`stall` only ever set blocked, so a unit whose dependency later passed
    went on reading blocked for the rest of the run. Dispatch was unaffected —
    which is exactly why nobody noticed the plan was lying."""

    def waiting_plan(self):
        phases = detail()
        phases[0]["tasks"][1]["dependsOn"] = ["M1-P1-T1"]
        self.plan(phases)
        return self.configure()

    def test_a_unit_comes_back_when_what_it_waited_on_passes(self):
        config = self.waiting_plan()
        ledger = execute.blank()
        # Blocked the way a run blocks a unit: out of attempts. A `blocked`
        # with no cause behind it is freed by `stall` itself, so a fixture
        # that set the word alone only held for one stale pass.
        ledger["attempts"]["M1-P1-T1"] = config["attempts"]
        status.set_status(self.root, "M1-P1-T1", schema.BLOCKED)
        execute.stall(self.root, execute.units(self.root), ledger, config)
        self.assertEqual(self.states()["M1-P1-T2"], schema.BLOCKED,
                         "what it waits on has stopped")

        ledger["attempts"]["M1-P1-T1"] = 0
        status.record(self.root, "unit", "python3 -m unittest", 0)
        status.set_status(self.root, "M1-P1-T1", schema.IN_PROGRESS)
        status.set_status(self.root, "M1-P1-T1", schema.PASSING)
        freed = execute.stall(self.root, execute.units(self.root), ledger, config)
        self.assertIn("M1-P1-T2", freed)
        self.assertEqual(self.states()["M1-P1-T2"], schema.NOT_STARTED)

    def test_a_unit_blocked_by_its_own_exhausted_attempts_stays_blocked(self):
        config = self.waiting_plan()
        ledger = execute.blank()
        status.set_status(self.root, "M1-P1-T3", schema.BLOCKED)
        ledger["attempts"]["M1-P1-T3"] = config["attempts"]
        execute.stall(self.root, execute.units(self.root), ledger, config)
        self.assertEqual(self.states()["M1-P1-T3"], schema.BLOCKED)

    def test_a_dependency_merely_failing_with_attempts_left_blocks_nothing(self):
        # A misfire writes `failing` too, and the unit is dispatched again the
        # next iteration. Its dependents were being marked blocked for that one
        # iteration and cleared the next — a wave of "blocked" on the console
        # for units nothing was wrong with.
        config = self.waiting_plan()
        ledger = execute.blank()
        ledger["attempts"]["M1-P1-T1"] = 1
        status.set_status(self.root, "M1-P1-T1", schema.IN_PROGRESS)
        status.set_status(self.root, "M1-P1-T1", schema.FAILING)
        self.assertEqual(
            execute.stall(self.root, execute.units(self.root), ledger, config),
            [])
        self.assertEqual(self.states()["M1-P1-T2"], schema.NOT_STARTED)

    def test_a_chain_three_deep_clears_in_one_call(self):
        phases = detail()
        phases[0]["tasks"][1]["dependsOn"] = ["M1-P1-T1"]
        phases[0]["tasks"][2]["dependsOn"] = ["M1-P1-T2"]
        self.plan(phases)
        config = self.configure()
        ledger = execute.blank()
        ledger["attempts"]["M1-P1-T1"] = config["attempts"]
        status.set_status(self.root, "M1-P1-T1", schema.IN_PROGRESS)
        status.set_status(self.root, "M1-P1-T1", schema.FAILING)
        self.assertEqual(
            execute.stall(self.root, execute.units(self.root), ledger, config),
            ["M1-P1-T2", "M1-P1-T3"],
            "T3 waits on T2, which was only marked blocked this same pass")

        ledger["attempts"]["M1-P1-T1"] = 0
        status.record(self.root, "unit", "python3 -m unittest", 0)
        status.set_status(self.root, "M1-P1-T1", schema.IN_PROGRESS)
        status.set_status(self.root, "M1-P1-T1", schema.PASSING)
        freed = execute.stall(self.root, execute.units(self.root), ledger, config)
        self.assertEqual(freed, ["M1-P1-T2", "M1-P1-T3"])
        self.assertEqual(self.states()["M1-P1-T3"], schema.NOT_STARTED)


class TestAWorkerThatNeverStarted(Project):
    """A dispatch that never became an attempt says nothing about the unit.

    No API, no network, a binary that is not there: the unit was not tried, and
    charging it an attempt for the state of the host is how one host fault took
    a whole wave down with it.
    """

    #: A worker that dies before its first turn: no report, non-zero exit.
    MUTE = "import sys\nsys.exit(3)\n"

    def held(self, **extra):
        self.plan()
        self.configure(**extra)
        config = execute.settings(self.root)
        status.set_status(self.root, "M1-P1-T1", schema.IN_PROGRESS)
        return config, execute.blank(), execute.units(self.root)["M1-P1-T1"]

    def test_a_worker_that_did_not_run_costs_the_unit_no_attempt(self):
        config, ledger, unit = self.held()
        execute.settle(self.root, config, ledger, unit,
                       execute.Result("w", None, "the worker did not run: exit 3",
                                      False), 1)
        self.assertNotIn(unit.id, ledger["attempts"])
        self.assertEqual(ledger["misfires"], {},
                         "FR-EXE-18: nothing started, so the unit may not be "
                         "charged the one counter that blocks it either")
        self.assertEqual(ledger["launches"], [unit.id],
                         "the streak is what bounds this now, and it is a fact "
                         "about the host rather than about the unit")
        self.assertEqual(self.states()[unit.id], schema.FAILING)
        self.assertIn(unit.id, [one.id for one in execute.ready(
            execute.units(self.root), ledger, config)])

    def test_the_two_ways_of_never_starting_take_the_same_route(self):
        """Both callers compose a different sentence; only settle is shared.

        The observed symptom named `did not run: exit 1`, which is the branch
        where the launch SUCCEEDED. The genuine cannot-launch path says `could
        not be run`. Fixing either caller would have left the other one spending
        a unit's budget on the state of the host.
        """
        for reason in ("the worker did not run: exit 1",
                       "the worker could not be run: [Errno 2] no such file"):
            config, ledger, unit = self.held()
            execute.settle(self.root, config, ledger, unit,
                           execute.Result("w", None, reason, False), 1)
            self.assertEqual(ledger["misfires"], {}, reason)
            self.assertEqual(ledger["launches"], [unit.id], reason)

    def test_a_dispatch_that_ran_clears_the_streak(self):
        config, ledger, unit = self.held()
        ledger["launches"] = ["M1-P1-T1", "M1-P1-T2"]
        execute.settle(self.root, config, ledger, unit,
                       execute.Result("w", None, "the worker returned no report"),
                       1)
        self.assertEqual(ledger["launches"], [],
                         "the streak asks whether this host can start a worker "
                         "at all, and one that started has answered it")

    def test_the_wait_grows_and_the_streak_stops_the_run(self):
        ledger = execute.blank()
        self.assertEqual(execute.backoff(ledger), 0)
        self.assertEqual(execute.halted(ledger), "")
        seen = []
        for one in ("M1-P1-T1", "M1-P1-T2", "M1-P1-T3", "M1-P1-T4"):
            ledger["launches"].append(one)
            seen.append(execute.backoff(ledger))
        self.assertEqual(seen[:3], list(execute.BACKOFF),
                         "the wait grows: an API that is down and a binary that "
                         "is not there recover on different timescales")
        self.assertEqual(seen[3], execute.BACKOFF[-1], "flat after the last")
        self.assertIn("could not be started", execute.halted(ledger))

    def test_one_unit_failing_to_start_for_ever_still_stops_the_run(self):
        """The streak is consecutive, not distinct: a project with one eligible
        unit would otherwise wait for a host that is never coming back."""
        ledger = execute.blank()
        ledger["launches"] = ["M1-P1-T1"] * execute.LAUNCH_HALT
        self.assertIn("M1-P1-T1", execute.halted(ledger))

    def test_a_worker_that_ran_and_said_nothing_still_costs_one(self):
        config, ledger, unit = self.held()
        execute.settle(self.root, config, ledger, unit,
                       execute.Result("w", None, "the worker returned no report"),
                       1)
        self.assertEqual(ledger["attempts"][unit.id], 1,
                         "a worker that ran and gave a bad account of itself is "
                         "the unit's own failure, and an attempt is the price")
        self.assertEqual(ledger["misfires"], {})

    def test_a_host_that_can_start_no_worker_stops_rather_than_spinning(self):
        """Not charging an attempt cannot mean never stopping.

        The brake moved: it used to be the unit's own misfire budget, which is
        exactly what FR-EXE-18 says a host fault may not spend. What stops the
        run now is the consecutive streak, and the unit is left where it was —
        failing, retryable, and owing nothing.
        """
        mute, _ = self.builder(body=self.MUTE)
        self.plan()
        self.configure(workers=[mute, self.judge()[0]], attempts=2)
        held = execute.BACKOFF
        execute.BACKOFF = (0, 0, 0)
        try:
            ledger = self.drive()
        finally:
            execute.BACKOFF = held
        self.assertEqual(ledger["misfires"], {},
                         "the host's problem is not the unit's budget")
        self.assertEqual(ledger["unfinished"], {},
                         "nothing about the unit was ever established, so "
                         "nothing about it is unfinished")
        self.assertEqual(len(ledger["launches"]), execute.LAUNCH_HALT)
        self.assertTrue([one for one in ledger["notes"]
                         if "could not be started" in one],
                        "the run has to say why it stopped")


class TestWhatAWorkerInherits(Project):

    def test_a_worker_is_not_left_to_a_ceiling_that_discards_its_work(self):
        self.plan()
        config = self.configure()
        entry = execute.units(self.root)["M1-P1-T1"].entry
        held = execute.environment(config, entry)
        for key, value in execute.WORKER_DEFAULTS.items():
            self.assertEqual(held[key], value)

    def test_a_ceiling_the_operator_stated_is_the_one_the_worker_gets(self):
        self.plan()
        config = self.configure()
        entry = execute.units(self.root)["M1-P1-T1"].entry
        key = sorted(execute.WORKER_DEFAULTS)[0]
        os.environ[key] = "5000"
        try:
            self.assertEqual(execute.environment(config, entry)[key], "5000")
        finally:
            del os.environ[key]


class TestBlockersAndRetries(Project):

    def test_a_failing_unit_blocks_rather_than_stalling_the_run(self):
        judged, _ = self.judge(answer='{"verdict": "fail", "gap": "not yet"}')
        self.plan()
        self.configure(workers=[self.builder()[0], judged], attempts=2)
        ledger = self.drive()
        self.assertEqual(ledger["attempts"]["M1-P1-T1"], 2)
        self.assertEqual(set(self.states().values()), {schema.BLOCKED})

    def test_a_blocked_unit_becomes_eligible_when_its_dependency_passes(self):
        phases = detail()
        phases[0]["tasks"][1]["dependsOn"] = ["M1-P1-T1"]
        self.plan(phases)
        config = self.configure()
        ledger = execute.blank()
        # Out of attempts: that is what blocks (M11-P3-T2-C2), not the word
        # "failing" on a unit that will be dispatched again next iteration.
        ledger["attempts"]["M1-P1-T1"] = config["attempts"]

        found = execute.units(self.root)
        status.set_status(self.root, "M1-P1-T1", schema.IN_PROGRESS)
        status.set_status(self.root, "M1-P1-T1", schema.FAILING)
        found = execute.units(self.root)
        self.assertEqual(execute.stall(self.root, found, ledger, config),
                         ["M1-P1-T2"])
        self.assertEqual(self.states()["M1-P1-T2"], schema.BLOCKED)

        status.set_status(self.root, "M1-P1-T1", schema.IN_PROGRESS)
        status.record(self.root, "unit", "python3 -m unittest", 0)
        status.set_status(self.root, "M1-P1-T1", schema.PASSING)
        eligible = [unit.id for unit in execute.ready(
            execute.units(self.root), ledger, config)]
        self.assertIn("M1-P1-T2", eligible,
                      "a unit blocked on a dependency has to come back by itself")

    def test_the_second_attempts_brief_really_carries_the_first_gap(self):
        keeping = ("import json, sys\n"
                   "open(%r, 'a', encoding='utf-8').write(\n"
                   "    open(sys.argv[1], encoding='utf-8').read() + '\\n====\\n')\n"
                   "json.dump({'red': {'command': 'x', 'code': 1}},\n"
                   "          open(sys.argv[2], 'w'))\n")
        seen = os.path.join(self.bin, "attempts.txt")
        build, _ = self.builder(body=keeping % seen)
        judged, _ = self.judge(
            answer='{"verdict": "fail", "gap": "the empty case is unhandled"}')
        self.plan()
        self.configure(workers=[build, judged], attempts=2, ceiling=1)
        self.drive()
        briefs = self.read(seen).split("\n====\n")
        first = [one for one in briefs if "M1-P1-T1" in one]
        self.assertEqual(len(first), 2, "one unit, two attempts")
        self.assertNotIn("the empty case is unhandled", first[0])
        self.assertIn("the empty case is unhandled", first[1],
                      "the second attempt has to be told what the first missed")

    def test_a_run_where_nothing_can_move_ends_rather_than_spinning(self):
        judged, _ = self.judge(answer='{"verdict": "fail", "gap": "not yet"}')
        self.plan()
        self.configure(workers=[self.builder()[0], judged], attempts=1)
        ledger = self.drive()
        self.assertEqual(len(ledger["unfinished"]), 3)


# ------------------------------------------------------- M11-P3-T3 resumability

class TestAWorkerThatStoppedWithoutItsReport(Project):
    """The work is on disk, the account is not. Ask for the account.

    A print-mode session ends when the model stops emitting, not when the task
    is done — so a worker that writes a tidy summary of what it is about to do
    next has ended its turn, and whatever it was about to do is killed with it.
    From the harness's side that is indistinguishable from a unit that failed,
    which is why the report is asked for once rather than guessed at.
    """

    #: Writes evidence into its own dispatch directory, then stops without the
    #: report — the shape of the real fault. It writes nothing on a second turn,
    #: so a test that sees a report saw the recovery worker write it.
    STOPS = """\
import os, sys
directory = os.path.dirname(sys.argv[1])
open(os.path.join(directory, "count.txt"), "a", encoding="utf-8").write("x")
open(os.path.join(directory, "evidence.txt"), "w", encoding="utf-8").write("23 minutes")
"""

    #: Stops on the first turn and reports on the second, which is what the
    #: recovery brief asks for. It tells the two turns apart by the brief it was
    #: handed, never by a counter — the recovery brief is the whole signal.
    LATE = """\
import json, os, re, sys
directory = os.path.dirname(sys.argv[1])
open(os.path.join(directory, "count.txt"), "a", encoding="utf-8").write("x")
brief = open(sys.argv[1], encoding="utf-8").read()
if "Recovery" not in brief:
    sys.exit(0)
found = re.search(r"M[0-9]+-P[0-9]+-T[0-9]+", brief)
json.dump({"unit": found.group(0), "red": {"command": "python3 -m unittest", "code": 1},
           "commands": [{"command": "python3 -m unittest", "code": 0}],
           "criteria": {}, "changes": [], "denied": [], "decisions": []},
          open(sys.argv[2], "w", encoding="utf-8"))
"""

    def dispatch(self, body):
        made, _ = self.builder(body=body)
        self.plan()
        self.configure(workers=[made, self.judge()[0]])
        config = execute.settings(self.root)
        unit = execute.units(self.root)["M1-P1-T1"]
        result = execute.run_worker(self.root, config, unit, execute.BUILD,
                                    "brief for M1-P1-T1", 1)
        return result, execute.place(self.root, unit.id, 1, execute.BUILD)

    def turns(self, directory):
        return len(self.read(os.path.join(directory, "count.txt")))

    def test_a_worker_asked_again_gets_its_report_read(self):
        result, directory = self.dispatch(self.LATE)
        self.assertIsNotNone(result.report, "the recovery turn wrote a report and "
                                            "the run must read it")
        self.assertEqual(result.report["unit"], "M1-P1-T1")
        self.assertEqual(result.reason, "")
        self.assertTrue(result.ran)
        self.assertEqual(self.turns(directory), 2)

    def test_a_worker_silent_twice_is_reported_exactly_as_it_was_before(self):
        result, directory = self.dispatch(self.STOPS)
        self.assertIsNone(result.report)
        self.assertEqual(result.reason, "the worker returned no report")
        self.assertTrue(result.ran, "it ran — the unit pays for this silence, "
                                    "which is what tells it apart from a host "
                                    "that could start no worker at all")
        self.assertEqual(self.turns(directory), 2,
                         "asked once more and no further; a loop here would "
                         "spend the whole run on one unit that cannot answer")

    def test_a_worker_that_died_is_not_asked_to_account_for_itself(self):
        result, directory = self.dispatch("import sys\nsys.exit(2)\n")
        self.assertFalse(result.ran)
        self.assertIn("exit 2", result.reason)
        self.assertFalse(os.path.exists(os.path.join(directory, "count.txt")),
                         "a worker that never reached a first turn cannot write "
                         "a report on a second one, and a dead host must not "
                         "cost two dispatches per attempt")

    def test_what_the_worker_left_behind_is_still_there_to_report_from(self):
        result, directory = self.dispatch(self.STOPS)
        self.assertEqual(self.read(os.path.join(directory, "evidence.txt")),
                         "23 minutes",
                         "the recovery turn reports from the evidence, so "
                         "clearing the directory would ask it to account for "
                         "work it can no longer see")
        self.assertTrue(os.path.exists(os.path.join(directory, "brief.md")),
                        "the recovery brief names the first brief as where the "
                        "report contract is stated")

    def test_the_recovery_brief_forbids_the_second_turn_starting_over(self):
        _, directory = self.dispatch(self.STOPS)
        asked = self.read(os.path.join(directory, execute.RECOVERY_BRIEF))
        self.assertIn("M1-P1-T1", asked)
        self.assertIn(os.path.join(directory, "brief.md"), asked)
        for phrase in ("start no new work", "Run no further checks"):
            self.assertIn(phrase, asked,
                          "a turn that begins by reading the original brief "
                          "begins by building again")

    def test_the_second_dispatch_is_vetted_like_the_first(self):
        """Structural, because it cannot be behavioural: recovery runs the same
        command with one path substituted differently, so no command exists that
        the first dispatch allows and the second must refuse. The check is there
        for the day that stops being true, and this is what keeps it there."""
        import inspect
        body = inspect.getsource(execute.turn)
        self.assertIn("safety.refusal", body,
                      "every command this module runs goes past the judge "
                      "first, and a second dispatch is a command")
        self.assertIn("turn(", inspect.getsource(execute.recover),
                      "the recovery turn and the guard turn are one dispatch "
                      "path; two would be two places the vetting could be left "
                      "out of")

    def test_a_recovered_report_is_graded_by_everything_it_would_have_been(self):
        made, _ = self.builder(body=self.LATE)
        judged, seen = self.judge(answer='{"verdict": "fail", "gap": "no"}')
        self.plan()
        self.configure(workers=[made, judged], attempts=1)
        ledger = self.drive()
        self.assertIn("M1-P1-T1", self.read(seen),
                      "recovery produces a report and nothing else — it still "
                      "goes to an independent judge, because a builder never "
                      "grades its own work however its account arrived")
        self.assertEqual(ledger["attempts"]["M1-P1-T1"], 1,
                         "one dispatch, one attempt: asking for the account "
                         "again is not a second attempt at the unit")
        self.assertEqual(self.states()["M1-P1-T1"], schema.BLOCKED)


class TestResuming(Project):

    def test_the_ledger_records_the_next_step_before_the_run_advances(self):
        watcher, _ = self.builder(body=(
            "import json, os, shutil, sys\n"
            "shutil.copyfile(os.path.join('.zero', 'state', 'run.json'),\n"
            "                os.path.join('.zero', 'state', 'seen.json'))\n"
            "json.dump({'red': {'command': 'x', 'code': 1}},\n"
            "          open(sys.argv[2], 'w'))\n"))
        self.plan()
        self.configure(workers=[watcher, self.judge()[0]], ceiling=1)
        self.drive()
        seen = json.loads(self.read(
            paths.resolve(self.root, paths.LEDGER_DIR, "seen.json")))
        self.assertIn("dispatch", seen["next"],
                      "the bookmark has to be written before the work starts, "
                      "not after it finishes")

    def test_a_restarted_run_repeats_no_completed_unit(self):
        build, briefs = self.builder()
        self.plan()
        self.configure(workers=[build, self.judge()[0]])
        self.drive()
        self.assertEqual(set(self.states().values()), {schema.PASSING})
        first = len(self.read(briefs).splitlines())

        self.drive()
        self.assertEqual(len(self.read(briefs).splitlines()), first,
                         "a second run must dispatch nothing that already passed")

    def test_a_plan_that_disagrees_with_the_ledger_is_believed_and_the_drift_recorded(self):
        self.plan()
        self.configure()
        ledger = execute.blank()
        ledger["done"] = ["M1-P1-T1"]
        execute.save(self.root, ledger)

        held = execute.load(self.root)
        noted = execute.reconcile(self.root, held, execute.units(self.root))
        self.assertTrue(noted)
        self.assertIn("the plan is believed", noted[0])
        self.assertNotIn("M1-P1-T1", held["done"])
        self.assertTrue(execute.load(self.root)["discrepancies"])

    def test_a_unit_a_stopped_run_was_holding_is_taken_back(self):
        build, _ = self.builder()
        self.plan()
        self.configure(workers=[build, self.judge()[0]])
        # What a killed run leaves behind: the status it wrote before dispatch,
        # and no record anywhere that the attempt ever finished.
        status.set_status(self.root, "M1-P1-T1", schema.IN_PROGRESS)

        ledger = self.drive()
        self.assertEqual(self.states()["M1-P1-T1"], schema.PASSING,
                         "a unit left in progress is skipped by the ready set, "
                         "and nothing else ever picked it up again")
        self.assertTrue(any("taken back" in one
                            for one in ledger["discrepancies"]),
                        "and it is said out loud, not quietly corrected")

    def test_the_unit_it_takes_back_reads_as_attempted_and_nothing_else_moves(self):
        self.plan()
        self.configure()
        status.set_status(self.root, "M1-P1-T1", schema.IN_PROGRESS)
        held = execute.blank()

        self.assertTrue(execute.abandoned(self.root, held,
                                          execute.units(self.root)))
        seen = self.states()
        self.assertEqual(seen["M1-P1-T1"], schema.FAILING)
        self.assertEqual(seen["M1-P1-T2"], schema.NOT_STARTED,
                         "only the unit that was in flight is touched")
        self.assertFalse(held["attempts"],
                         "the attempt was never counted, so coming back costs "
                         "the unit none of them")
        self.assertFalse(held["notes"] or held["conflicts"],
                         "a unit nobody was holding is not written to at all — "
                         "a refused write counts against the next real one")

    def test_a_report_left_by_an_earlier_dispatch_is_not_read_as_this_ones(self):
        silent, _ = self.builder(body="pass\n")
        self.plan()
        self.configure(workers=[silent, self.judge()[0]], attempts=1)
        directory = execute.place(self.root, "M1-P1-T1", 1, execute.BUILD)
        os.makedirs(directory)
        with open(os.path.join(directory, "report.json"), "w",
                  encoding="utf-8") as handle:
            json.dump({"unit": "M1-P1-T1", "red": {"command": "x", "code": 1},
                       "criteria": {}, "changes": []}, handle)

        ledger = self.drive()
        self.assertNotEqual(self.states()["M1-P1-T1"], schema.PASSING)
        self.assertIn("no report", ledger["unfinished"]["M1-P1-T1"],
                      "a dispatch directory is reused on a repeated attempt, so "
                      "the previous answer must not survive into this one")

    def test_the_only_recursive_delete_reaches_nowhere_but_a_dispatch(self):
        for outside in (self.root, os.path.dirname(self.root),
                        paths.resolve(self.root, paths.SPECS_DIR),
                        os.path.join(self.bin, "M1-P1-T1-1-build")):
            self.assertFalse(execute._dispatched(self.root, outside), outside)
        self.assertTrue(execute._dispatched(
            self.root, execute.place(self.root, "M1-P1-T1", 1, execute.BUILD)))

    def test_nothing_an_earlier_dispatch_left_behind_survives_into_this_one(self):
        self.plan()
        self.configure(attempts=1)
        stale = os.path.join(execute.place(self.root, "M1-P1-T1", 1, execute.BUILD),
                             "red-tree", "leftover_test.py")
        os.makedirs(os.path.dirname(stale))
        with open(stale, "w", encoding="utf-8") as handle:
            handle.write("# last time's working tree\n")

        self.drive()
        self.assertFalse(os.path.exists(stale),
                         "a check whose argument is a filter rather than a path "
                         "picks up another attempt's scratch tree and runs it")

    def test_work_the_plan_says_is_done_is_recorded_rather_than_repeated(self):
        self.plan()
        self.configure()
        status.set_status(self.root, "M1-P1-T1", schema.IN_PROGRESS)
        status.record(self.root, "unit", "python3 -m unittest", 0)
        status.set_status(self.root, "M1-P1-T1", schema.PASSING)
        held = execute.blank()
        noted = execute.reconcile(self.root, held, execute.units(self.root))
        self.assertIn("M1-P1-T1", held["done"])
        self.assertTrue(noted)


# -------------------------------------------------------- the run, end to end

class TestARunFromStartToFinish(Project):

    def test_every_unit_is_built_judged_and_recorded(self):
        build, briefs = self.builder()
        judged, seen = self.judge()
        self.plan()
        self.configure(workers=[build, judged])
        ledger = self.drive()
        self.assertEqual(set(self.states().values()), {schema.PASSING})
        self.assertEqual(sorted(ledger["done"]),
                         ["M1-P1-T1", "M1-P1-T2", "M1-P1-T3"])
        self.assertEqual(len(self.read(briefs).splitlines()), 3)
        self.assertEqual(self.read(seen).count("You are judging"), 3)

    def test_the_documents_still_parse_after_the_run(self):
        self.plan()
        self.configure()
        self.drive()
        for path in status.documents(self.root):
            status.read(path)

    def test_the_command_line_runs_the_plan(self):
        import io
        self.plan()
        self.configure()
        out = io.StringIO()
        code = execute.main(["--root", self.root, "run"], out)
        self.assertEqual(code, 0)
        self.assertIn("passing", out.getvalue())

    def test_the_command_line_prints_a_brief(self):
        import io
        self.plan()
        self.configure()
        out = io.StringIO()
        self.assertEqual(
            execute.main(["--root", self.root, "brief", "M1-P1-T1"], out), 0)
        self.assertEqual(plan.check_prompt(out.getvalue()), [])

    def test_the_command_line_refuses_an_unknown_unit(self):
        import io
        self.plan()
        self.configure()
        out = io.StringIO()
        self.assertEqual(
            execute.main(["--root", self.root, "brief", "M9-P9-T9"], out), 2)


# ------------------------------------------- what the module says about itself

class TestWhatTheOrchestratorSaysAboutItself(unittest.TestCase):

    def read(self, name):
        with open(os.path.join(PACKAGE, name), encoding="utf-8") as handle:
            return handle.read()

    def test_no_status_identifier_is_spelled_in_the_orchestrator(self):
        body = self.read("execute.py")
        for one in schema.ENUMS["statuses"]:
            self.assertNotIn('"%s"' % one["id"], body,
                             "the vocabulary is declared in the schema; a second "
                             "copy here would eventually disagree with it")

    def test_the_orchestrator_extracts_no_document_of_its_own(self):
        body = self.read("execute.py")
        self.assertNotIn("BLOCK = ", body)
        self.assertIn("status.read", body)

    def test_the_orchestrator_never_pushes_to_a_remote(self):
        body = self.read("execute.py")
        for word in ("push", "remote"):
            self.assertNotIn("\"%s\"" % word, body)

    def test_the_prohibited_list_is_consulted_rather_than_re_implemented(self):
        body = self.read("execute.py")
        self.assertIn("safety.refusal", body)
        for pattern in ("--force", "filter-branch", "branch -D"):
            self.assertNotIn(pattern, body)


# ------------------------------------------- the bound on one dispatch (P0/P1/P3)

#: A worker that never comes back. It writes no report and runs far longer than
#: any bound a test would set, which is the shape that idled a real run for two
#: hours and twenty-two minutes with the work already finished on disk.
SLEEPER = """\
import time
print("started", flush=True)
time.sleep(%(seconds)d)
"""

#: A worker that starts something of its own and leaves it running. Ending the
#: direct child alone leaves that grandchild behind, which is the whole reason a
#: dispatch gets its own session and is stopped by process group.
ORPHAN = """\
import os, subprocess, sys, time
child = subprocess.Popen([sys.executable, "-c",
                          "import os, time\\n"
                          "open(%(marker)r, 'w').write(str(os.getpid()))\\n"
                          "time.sleep(600)\\n"])
time.sleep(600)
"""

#: A worker that does the work, leaves the evidence in its dispatch directory,
#: and stops without an account of it. Exits non-zero, which is what a worker
#: that was killed does — and what, until this was fixed, made the one turn that
#: could rescue it unreachable.
SILENT = """\
import os, sys
open(os.path.join(os.path.dirname(sys.argv[1]), "notes.md"), "w").write("work")
raise SystemExit(%(code)d)
"""

#: The recovery turn: it is handed the recovery brief, not the original one, and
#: answers from what is already on disk.
ACCOUNT = """\
import json, os, re, sys
brief = open(sys.argv[1], encoding="utf-8").read()
found = re.search(r"M[0-9]+-P[0-9]+-T[0-9]+", brief)
if "Recovery" not in brief:
    open(os.path.join(os.path.dirname(sys.argv[1]), "notes.md"), "w").write("work")
    raise SystemExit(%(code)d)
json.dump({"unit": found.group(0) if found else "?",
           "red": {"command": "python3 -m unittest", "code": 1},
           "commands": [{"command": "python3 -m unittest", "code": 0}],
           "criteria": {}, "changes": [], "denied": [], "decisions": []},
          open(sys.argv[2], "w", encoding="utf-8"))
"""


class TestAHungWorkerDoesNotIdleTheRun(Project):
    """P0. Attempts and the gauntlet bound a run that is moving. Neither of them
    bounds one that has stopped, and until this there was nothing that did."""

    def elapsed(self):
        began = time.time()
        ledger = self.drive()
        return ledger, time.time() - began

    def test_a_worker_that_never_returns_is_stopped_and_the_run_goes_on(self):
        self.plan()
        stuck, _ = self.builder(body=SLEEPER % {"seconds": 600})
        judged, _ = self.judge()
        self.configure(workers=[stuck, judged], timeout=2, attempts=1)
        ledger, spent = self.elapsed()
        self.assertLess(spent, 120, "the run waited on a worker that was never "
                                    "coming back; a run has to be able to end one")
        stated = " ".join(list(ledger["unfinished"].values()) + ledger["notes"])
        self.assertIn("did not finish within", stated,
                      "a stopped worker must say it ran out of time")

    def test_what_the_worker_started_is_stopped_with_it(self):
        """`start_new_session` plus a group kill, and the only test that proves it.

        A worker that spawns a test runner and is then ended by its direct
        handle leaves the runner holding the tree. The next unit picks up its
        output, and nothing in the run knows why.
        """
        self.plan()
        marker = os.path.join(self.bin, "grandchild.pid")
        stuck, _ = self.builder(body=ORPHAN % {"marker": marker})
        judged, _ = self.judge()
        self.configure(workers=[stuck, judged], timeout=3, attempts=1)
        self.drive()
        self.assertTrue(os.path.exists(marker),
                        "the grandchild never started, so this proves nothing")
        left = int(self.read(marker))
        try:
            os.kill(left, 0)
        except OSError:
            return
        os.kill(left, 9)
        self.fail("the worker's own child outlived the dispatch that started it")

    def test_a_project_may_ask_for_no_bound_at_all(self):
        """A default nobody can turn off is a defect of its own."""
        self.plan()
        build, _ = self.builder()
        judged, _ = self.judge()
        held = self.configure(workers=[build, judged], timeout=None)
        self.assertIsNone(execute.settings(self.root)["timeout"])
        self.assertEqual(held["timeout"], None)
        ledger = self.drive()
        self.assertEqual(ledger["unfinished"], {},
                         "an unbounded run must still be a working run")

    def test_a_bound_that_is_not_a_number_of_seconds_is_refused(self):
        self.plan()
        build, _ = self.builder()
        judged, _ = self.judge()
        for stated in ("soon", 0, -1):
            self.configure(workers=[build, judged], timeout=stated)
            with self.assertRaises(execute.Refused):
                execute.settings(self.root)

    def test_a_worker_may_state_its_own_bound(self):
        self.plan()
        build, _ = self.builder()
        judged, _ = self.judge()
        config = {"timeout": 90, "workers": []}
        self.assertEqual(execute.bound(config, {}), 90)
        self.assertEqual(execute.bound(config, {"timeout": 5}), 5)
        self.assertIsNone(execute.bound(config, {"timeout": None}),
                          "a worker that states no bound of its own means it")

    def test_the_gauntlet_is_bounded_too(self):
        """E-03. A check that hangs wedges a run exactly as a worker does."""
        self.plan()
        build, _ = self.builder()
        judged, _ = self.judge()
        self.configure(workers=[build, judged], timeout=2, attempts=1,
                       gauntlet={"unit": [sys.executable, "-c",
                                          "import time; time.sleep(600)"]})
        ledger, spent = self.elapsed()
        self.assertLess(spent, 120, "the run waited on a check that hung")
        self.assertIn("did not finish within",
                      " ".join(ledger["unfinished"].values()),
                      "a check that was stopped must say so")



class TestAWorkerThatWillNotBeAskedIsTold(unittest.TestCase):
    """The second half of the kill, which nothing else reaches.

    A process that ignores the polite signal is exactly the process a bound
    exists for. Without the escalation the run would wait on it for ever, which
    is the defect this whole change is about — arrived at by a different road.
    """

    def setUp(self):
        self.grace = execute.dispatch.GRACE
        execute.dispatch.GRACE = 1
        self.directory = tempfile.mkdtemp(prefix="z2s-stop-")

    def tearDown(self):
        execute.dispatch.GRACE = self.grace
        shutil.rmtree(self.directory, ignore_errors=True)

    def test_a_worker_that_ignores_being_asked_is_stopped_anyway(self):
        stubborn = (
            "import signal, time\n"
            "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
            "print('ready', flush=True)\n"
            "time.sleep(600)\n")
        path = os.path.join(self.directory, "stubborn.py")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(stubborn)
        log = os.path.join(self.directory, "stubborn.log")
        code, expired = execute.dispatch.launch(
            [sys.executable, path], self.directory, timeout=1, log=log)
        self.assertTrue(expired)
        self.assertLess(code, 0, "it was signalled, not asked nicely twice")
        self.assertIn("ready", self.read(log))

    def read(self, path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()


class TestAKilledWorkerIsAskedForItsAccount(Project):
    """P1. `recover` existed for exactly this and could not be reached from it:
    the exit status was read first, and anything killed exits non-zero."""

    def test_a_worker_that_exits_badly_with_no_report_is_still_asked(self):
        self.plan()
        quiet, _ = self.builder(body=ACCOUNT % {"code": 1})
        judged, _ = self.judge()
        self.configure(workers=[quiet, judged], attempts=1)
        ledger = self.drive()
        self.assertEqual(ledger["unfinished"], {},
                         "the work was done and on disk; only the account was "
                         "missing, and asking for it is what recovery is")
        directory = execute.place(self.root, "M1-P1-T1", 1, execute.BUILD)
        self.assertTrue(os.path.exists(os.path.join(directory,
                                                    execute.RECOVERY_BRIEF)),
                        "no recovery brief was ever written")

    def test_a_stopped_dispatch_costs_the_unit_no_attempt(self):
        """The one thing that was already right on this path, kept right."""
        self.plan()
        stuck, _ = self.builder(body=SLEEPER % {"seconds": 600})
        judged, _ = self.judge()
        self.configure(workers=[stuck, judged], timeout=2, attempts=3)
        ledger = self.drive()
        self.assertEqual(ledger["attempts"].get("M1-P1-T1"), 3,
                         "a unit that never got an account of itself is charged "
                         "the budget at once, not one attempt per timeout")
        self.assertGreaterEqual(ledger["misfires"].get("M1-P1-T1", 0), 3,
                                "a dispatch that never became an attempt is "
                                "counted as a misfire, not as a failed try")

    def test_a_silence_recovery_cannot_answer_still_costs_an_attempt(self):
        self.plan()
        quiet, _ = self.builder(body=SILENT % {"code": 0})
        judged, _ = self.judge()
        self.configure(workers=[quiet, judged], attempts=1)
        ledger = self.drive()
        self.assertIn("M1-P1-T1", ledger["unfinished"])
        self.assertIn("no report", ledger["unfinished"]["M1-P1-T1"])


#: A host with something up on it, in the shape docker's own `--format` prints.
#: The real command is swapped for this so the rule can be exercised on a machine
#: with no docker, which is the same reason every worker here is a script.
LISTING = """\
print("9f3ac1 pgvector/pgvector:pg16 Up 2 hours z2s-db")
"""


class TestAStoppedDispatchSaysWhatItLeftRunning(Project):
    """R2-09. A dispatch is stopped; what its checks started is not. A database
    container outlived one by two and a half hours and four later units ran
    against it, and nothing in the run ever said so.

    Reported and never removed: tearing down a live database is not reliably a
    ten-second job, and a run that removes a container it did not start has
    destroyed something it was never asked to own.
    """

    def setUp(self):
        super(TestAStoppedDispatchSaysWhatItLeftRunning, self).setUp()
        self.asked = execute.CONTAINERS

    def tearDown(self):
        execute.CONTAINERS = self.asked
        super(TestAStoppedDispatchSaysWhatItLeftRunning, self).tearDown()

    def host(self, body):
        """Stand in for docker, so the rule is testable with none installed."""
        execute.CONTAINERS = [sys.executable,
                              script(self.bin, "host.py", body)]

    def stopped(self, **extra):
        """A worker that never comes back, run against a bound it cannot meet."""
        self.plan()
        stuck, _ = self.builder(body=SLEEPER % {"seconds": 600})
        judged, _ = self.judge()
        held = {"timeout": 2, "attempts": 3}
        held.update(extra)
        self.configure(workers=[stuck, judged], **held)
        return self.drive()

    def test_what_is_still_up_reaches_the_operator(self):
        self.host(LISTING)
        ledger = self.stopped()
        stated = " ".join(list(ledger["unfinished"].values()) + ledger["notes"])
        self.assertIn("pgvector/pgvector:pg16", stated,
                      "the run stopped a dispatch and said nothing about what "
                      "its checks had left running")
        self.assertIn("Up 2 hours", stated,
                      "the elapsed time is docker's own word for it; the run "
                      "must not compute one, and must not drop the one it has")

    def test_a_host_that_cannot_answer_changes_nothing_and_raises_nothing(self):
        execute.CONTAINERS = ["z2s-no-such-binary-anywhere", "ps"]
        ledger = self.stopped()
        stated = " ".join(list(ledger["unfinished"].values()) + ledger["notes"])
        self.assertIn("did not finish within", stated,
                      "the timeout must still be reported when the host has no "
                      "docker; a missing binary is not a fact about the unit")
        self.assertNotIn("still up on this host", stated,
                         "nothing was learned, so nothing may be claimed")

    def test_the_run_only_ever_asks_what_is_there(self):
        """The whole of R2-09's fix: it looks, and that is all it does."""
        for word in ("rm", "kill", "stop", "prune", "down", "remove"):
            self.assertNotIn(word, execute.CONTAINERS,
                             "a run may never take a container away; it says "
                             "what is there and the operator decides")
        self.assertEqual(execute.CONTAINERS[:2], ["docker", "ps"])

    def test_asking_costs_the_unit_nothing(self):
        """The counters this rides on are the ones it must not disturb."""
        self.host(LISTING)
        ledger = self.stopped()
        self.assertEqual(ledger["attempts"].get("M1-P1-T1"), 3)
        self.assertGreaterEqual(ledger["misfires"].get("M1-P1-T1", 0), 3,
                                "reporting what is up is an observation, not an "
                                "attempt the unit made and lost")

    def test_a_stopped_unit_is_not_told_no_dispatch_ever_started(self):
        """The two halves of the blocked message have to agree with each other.

        `misfired`'s default is written for a worker that never ran. Concatenated
        onto a timeout it says the run stopped a dispatch that never started.
        """
        self.host(LISTING)
        ledger = self.stopped(attempts=1)
        said = ledger["unfinished"]["M1-P1-T1"]
        self.assertIn("was stopped", said)
        self.assertNotIn("no dispatch of it has started", said,
                         "it was stopped, so one plainly did start")
        self.assertIn("finished within that bound", said,
                      "the budget went on dispatches that ran out of time, and "
                      "the message has to say which of the two it was")


class TestEveryDispatchLeavesALog(Project):
    """P3. An operator cannot tell a working worker from a wedged one without
    seeing what it is saying, and it was saying it into nothing."""

    def test_the_dispatch_directory_holds_what_the_worker_printed(self):
        self.plan()
        build, _ = self.builder()
        judged, _ = self.judge()
        self.configure(workers=[build, judged])
        self.drive()
        directory = execute.place(self.root, "M1-P1-T1", 1, execute.BUILD)
        path = os.path.join(directory, "%s.log" % execute.BUILD)
        self.assertTrue(os.path.exists(path), "the dispatch left no log")

    def test_a_recovery_turn_does_not_write_over_the_first_log(self):
        self.plan()
        quiet, _ = self.builder(body=ACCOUNT % {"code": 1})
        judged, _ = self.judge()
        self.configure(workers=[quiet, judged], attempts=1)
        self.drive()
        directory = execute.place(self.root, "M1-P1-T1", 1, execute.BUILD)
        for name in ("%s.log" % execute.BUILD, execute.RECOVERY_LOG):
            self.assertTrue(os.path.exists(os.path.join(directory, name)),
                            "%s is missing; the two turns share one name" % name)

    def test_the_run_says_where_the_log_is(self):
        self.plan()
        build, _ = self.builder()
        judged, _ = self.judge()
        self.configure(workers=[build, judged])
        said = io.StringIO()
        execute.run(self.root, said)
        self.assertIn("%s.log" % execute.BUILD, said.getvalue(),
                      "a log nobody is told about is a log nobody reads")


class TestWorkAlreadyInHistoryCanBeJudged(Project):
    """P2. A unit re-dispatched after its work was committed had nothing left to
    put in `changes`, and was refused for having nothing to say."""

    def committed(self):
        """A real commit in a real repository, and the file it holds."""
        for command in (["git", "init", "-q"],
                        ["git", "config", "user.email", "z2s@example.invalid"],
                        ["git", "config", "user.name", "Z2S"]):
            subprocess.run(command, cwd=self.root, check=True)
        path = os.path.join(self.root, "landed.py")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("value = 1\n")
        subprocess.run(["git", "add", "landed.py"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "landed"], cwd=self.root, check=True)
        found = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root,
                               check=True, stdout=subprocess.PIPE)
        return found.stdout.decode().strip()

    def test_a_commit_this_repository_holds_names_the_work(self):
        sha = self.committed()
        files, why = execute.in_history(self.root, sha)
        self.assertEqual(why, "")
        self.assertEqual(files, ["landed.py"])

    def test_a_claim_backed_by_a_commit_is_not_refused_for_naming_no_file(self):
        report = {"unit": "M1-P1-T1",
                  "red": {"command": "python3 -m unittest", "code": 1},
                  "commands": [{"command": "python3 -m unittest", "code": 0}],
                  "criteria": {"M1-P1-T1-C1": True}, "changes": [],
                  "denied": [], "decisions": []}
        self.assertTrue([one for one in execute.check_report(report)
                         if "no changed file" in one])
        self.assertEqual(execute.check_report(report, None, ["landed.py"]), [])

    def test_something_that_is_not_a_commit_identifier_never_reaches_git(self):
        """Worker-supplied text at a trust boundary. Shape first, git second."""
        for stated in ("HEAD", "--output=/tmp/x", "a1b2c3d; rm -rf /", "", "zz"):
            files, why = execute.in_history(self.root, stated)
            self.assertEqual(files, [])
            self.assertIn("not a commit identifier", why)

    def test_a_commit_this_repository_does_not_hold_is_refused(self):
        self.committed()
        files, why = execute.in_history(self.root, "0" * 40)
        self.assertEqual(files, [])
        self.assertIn("not in this repository", why)

    def test_a_commit_that_changed_nothing_is_refused(self):
        sha = self.committed()
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "nothing"],
                       cwd=self.root, check=True)
        found = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root,
                               check=True, stdout=subprocess.PIPE)
        empty = found.stdout.decode().strip()
        self.assertNotEqual(empty, sha)
        files, why = execute.in_history(self.root, empty)
        self.assertEqual(files, [])
        self.assertIn("changed no file", why)

    def test_the_judge_is_shown_the_landed_files(self):
        sha = self.committed()
        self.plan()
        body = (
            "import json, re, sys\n"
            "brief = open(sys.argv[1], encoding='utf-8').read()\n"
            "found = re.search(r'M[0-9]+-P[0-9]+-T[0-9]+', brief)\n"
            "json.dump({'unit': found.group(0) if found else '?',\n"
            "           'red': {'command': 'x', 'code': 1},\n"
            "           'commands': [{'command': 'x', 'code': 0}],\n"
            "           'criteria': {'C1': True}, 'changes': [],\n"
            "           'landed': %r,\n"
            "           'denied': [], 'decisions': []},\n"
            "          open(sys.argv[2], 'w', encoding='utf-8'))\n" % sha)
        build, _ = self.builder(body=body)
        judged, seen = self.judge()
        self.configure(workers=[build, judged], attempts=1)
        self.drive()
        self.assertIn("landed.py", self.read(seen),
                      "the landed files ARE the work; a judge shown "
                      "'(the worker named no changed file)' is judging nothing")

    def test_a_report_naming_a_commit_that_is_not_there_fails_the_unit(self):
        self.committed()
        self.plan()
        body = (
            "import json, re, sys\n"
            "brief = open(sys.argv[1], encoding='utf-8').read()\n"
            "found = re.search(r'M[0-9]+-P[0-9]+-T[0-9]+', brief)\n"
            "json.dump({'unit': found.group(0) if found else '?',\n"
            "           'red': {'command': 'x', 'code': 1},\n"
            "           'commands': [{'command': 'x', 'code': 0}],\n"
            "           'criteria': {'C1': True}, 'changes': [],\n"
            "           'landed': '%s',\n"
            "           'denied': [], 'decisions': []},\n"
            "          open(sys.argv[2], 'w', encoding='utf-8'))\n" % ("0" * 40))
        build, _ = self.builder(body=body)
        judged, _ = self.judge()
        self.configure(workers=[build, judged], attempts=1)
        ledger = self.drive()
        self.assertIn("not in this repository",
                      ledger["unfinished"].get("M1-P1-T1", ""))



# ------------------------------------------------ R2-06 a layer that disagrees

class TestAFlakyLayerIsRerunBeforeItChargesTheUnit(Project):
    """R2-06. Two of the seven layers on the win-it run were not deterministic.

    `M15-P3-T2` was charged an attempt on `integration failed: … exited 1`; the
    builder that followed edited nothing, and the identical command on the
    identical tree exited zero seventeen minutes later. `e2e` did the same to
    `M15-P1-T3` and discarded two hours of finished work that never reached a
    judge. A layer that fails and then passes on an unchanged tree is evidence
    about the layer, not about the work.
    """

    def flaky(self, fails=1):
        """A check that exits 1 for its first `fails` runs and 0 thereafter."""
        marker = os.path.join(self.bin, "flaky-count")
        return [sys.executable, "-c",
                "import sys\n"
                "p = %r\n"
                "try: n = int(open(p).read())\n"
                "except Exception: n = 0\n"
                "open(p, 'w').write(str(n + 1))\n"
                "sys.exit(1 if n < %d else 0)\n" % (marker, fails)]

    def test_a_layer_that_fails_once_then_passes_does_not_charge_the_unit(self):
        self.plan()
        self.configure(gauntlet={"unit": self.flaky()}, attempts=3)
        ledger = self.drive()
        self.assertEqual(self.states()["M1-P1-T1"], schema.PASSING)
        self.assertEqual(ledger["attempts"].get("M1-P1-T1"), 1,
                         "a layer that disagreed with itself charged the unit "
                         "an attempt it never spent")
        self.assertEqual(ledger["unfinished"], {})

    def test_the_disagreement_is_recorded_and_said_on_the_run_s_line(self):
        """A flake that is invisible is a flake nobody fixes."""
        self.plan()
        self.configure(gauntlet={"unit": self.flaky()}, attempts=3)
        out = io.StringIO()
        ledger = execute.run(self.root, out)
        said = " ".join(ledger["notes"])
        self.assertIn("passed on a second run", said)
        self.assertIn("unit", said)
        self.assertIn("passed on a second run", out.getvalue())

    def test_a_layer_that_fails_twice_fails_the_unit_exactly_as_before(self):
        """Four, not two: the run now surveys the cheap layers before it
        dispatches anything (FR-EXE-20), and that survey runs this check twice
        for the same reason a gauntlet does. The fifth run would pass, so the
        one-re-run rule is still what is being asserted here."""
        self.plan()
        self.configure(gauntlet={"unit": self.flaky(fails=4)}, attempts=1)
        ledger = self.drive()
        self.assertIn("unit failed:", ledger["unfinished"].get("M1-P1-T1", ""))
        self.assertIn("exited 1", ledger["unfinished"].get("M1-P1-T1", ""))
        self.assertEqual(self.states()["M1-P1-T1"], schema.BLOCKED)



# ------------------------------ R2-07 what was written against what was declared

STRAY = """\
import json, re, sys
brief = open(sys.argv[1], encoding="utf-8").read()
found = re.search(r"M[0-9]+-P[0-9]+-T[0-9]+", brief).group(0)
json.dump({"unit": found,
           "red": {"command": "x", "code": 1},
           "commands": [{"command": "x", "code": 0}],
           "criteria": {found + "-C1": True},
           "changes": %(changes)s.get(found, ["src/one.py"]),
           "denied": [], "decisions": []},
          open(sys.argv[2], "w", encoding="utf-8"))
"""


class TestWhatWasWrittenIsCheckedAgainstWhatWasDeclared(Project):
    """R2-07. Three of one night's eight units wrote a file no list named.

    All three were route-shaped and all three declared the exception honestly in
    `decisions`, exactly as the brief asks — because a route absent from a shared
    manifest is unreachable, and no per-unit write list can own a shared
    manifest. Nothing in the run read the answer. At 22:19 two units ran side by
    side, judged disjoint, while one of them was writing a file its list never
    named.

    So the severity follows the hazard rather than the tidiness (E2-05): every
    out-of-set path is recorded, and only an overlap with a unit that was
    actually running beside it fails anything. Failing them all would have
    blocked three of eight units for doing the only thing possible.
    """

    def stray(self, changes, name="strayer"):
        return self.builder(body=STRAY % {"changes": repr(changes)}, name=name)

    def declared(self):
        phases = detail()
        phases[0]["tasks"][0]["writes"] = ["src/one.py", "tests/test_one.py"]
        phases[0]["tasks"][1]["writes"] = ["src/two.py", "tests/test_two.py"]
        return phases

    def test_a_path_outside_the_declared_set_is_recorded_and_the_unit_passes(self):
        self.plan(self.declared())
        build, _ = self.stray({"M1-P1-T1": ["src/one.py", "src/stray.py"]})
        judged, _ = self.judge()
        self.configure(workers=[build, judged], ceiling=1, attempts=1)
        out = io.StringIO()
        ledger = execute.run(self.root, out)
        said = " ".join(ledger["notes"])
        self.assertIn("src/stray.py", said)
        self.assertIn("src/stray.py", out.getvalue())
        self.assertEqual(self.states()["M1-P1-T1"], schema.PASSING,
                         "every occurrence observed was legitimate and honestly "
                         "declared; the hazard is concurrency, not the write")

    def test_a_path_a_unit_running_beside_it_declared_fails_the_unit(self):
        self.plan(self.declared())
        build, _ = self.stray({"M1-P1-T1": ["src/one.py", "src/two.py"]})
        judged, _ = self.judge()
        self.configure(workers=[build, judged], ceiling=2, attempts=1)
        ledger = self.drive()
        reason = ledger["unfinished"].get("M1-P1-T1", "")
        self.assertIn("src/two.py", reason)
        self.assertIn("M1-P1-T2", reason,
                      "the report has to name the unit whose guarantee broke")
        self.assertEqual(self.states()["M1-P1-T1"], schema.BLOCKED)

    def test_a_clash_is_the_runs_own_mistake_and_the_unit_does_not_pay_for_it(self):
        """R2-07 follow-up. The collision was scheduled, not committed.

        A shared append-only manifest is in nobody's declared list, so two units
        that must both add a line to it read as disjoint and are dispatched
        together. The unit did the only thing that ships a working route; the
        run chose who it ran beside. Charging an attempt for that spends a
        budget the builder had no way to protect, and three of them block a unit
        on `schema.BLOCKED` for being correct.

        Bounded exactly like a dispatch that never started, and for the same
        reason: a unit nothing charges comes straight back round for ever.
        """
        self.plan(self.declared())
        build, _ = self.stray({"M1-P1-T1": ["src/one.py", "src/two.py"],
                               "M1-P1-T2": ["src/two.py"]})
        judged, _ = self.judge()
        self.configure(workers=[build, judged], ceiling=2, attempts=2)
        ledger = self.drive()
        self.assertEqual(ledger["misfires"].get("M1-P1-T1"), 1)
        self.assertEqual(ledger["attempts"].get("M1-P1-T1"), 1,
                         "the clashing dispatch is not an attempt, so the one "
                         "that ran alone after it is still the first")
        self.assertEqual(self.states()["M1-P1-T1"], schema.PASSING)

    def test_the_console_says_a_redispatch_is_one_and_what_is_left(self):
        """F7. A misfire charges no attempt, so the second dispatch of a unit
        printed `attempt 1` again and read as a first try."""
        self.plan(self.declared())
        build, _ = self.stray({"M1-P1-T1": ["src/one.py", "src/two.py"],
                               "M1-P1-T2": ["src/two.py"]})
        judged, _ = self.judge()
        self.configure(workers=[build, judged], ceiling=2, attempts=2)
        out = io.StringIO()
        execute.run(self.root, out)
        lines = [one for one in out.getvalue().splitlines()
                 if one.startswith("dispatch M1-P1-T1 ")]
        self.assertEqual(lines[0], "dispatch M1-P1-T1 (attempt 1)",
                         "the first line is byte-identical to what it was")
        self.assertIn("dispatch M1-P1-T1 (attempt 1; redispatch after 1 misfire, "
                      "1 left)", lines)

    def test_a_report_entirely_inside_its_declared_set_says_nothing(self):
        self.plan(self.declared())
        build, _ = self.stray({"M1-P1-T1": ["src/one.py", "tests/test_one.py"]})
        judged, _ = self.judge()
        self.configure(workers=[build, judged], ceiling=1, attempts=1)
        out = io.StringIO()
        ledger = execute.run(self.root, out)
        self.assertEqual([one for one in ledger["notes"]
                          if one.startswith("M1-P1-T1:")
                          and "declared write set" in one], [])
        self.assertEqual(self.states()["M1-P1-T1"], schema.PASSING)

    def test_a_pattern_covers_the_files_beneath_it(self):
        unit = execute.Unit("A", {"id": "A", "writes": ["src/storage/**"]},
                            "plan.html", "M1")
        outside, clashes = execute.strayed(unit, ["src/storage/deep/one.ts"])
        self.assertEqual(outside, [])
        self.assertEqual(clashes, [])

    def test_a_unit_that_declared_nothing_has_no_set_to_be_outside_of(self):
        """It runs alone, so there is no guarantee for it to break."""
        unit = execute.Unit("A", {"id": "A", "writes": []}, "plan.html", "M1")
        other = execute.Unit("B", {"id": "B", "writes": ["src/two.py"]},
                             "plan.html", "M1")
        self.assertEqual(execute.strayed(unit, ["src/two.py"], [other]),
                         ([], []))

    def test_the_clash_is_judged_against_the_unit_that_ran_beside_it(self):
        """The scheduler and this check read one implementation of one claim."""
        unit = execute.Unit("A", {"id": "A", "writes": ["src/one.py"]},
                            "plan.html", "M1")
        beside = execute.Unit("B", {"id": "B", "writes": ["src/two.py"]},
                              "plan.html", "M1")
        elsewhere = execute.Unit("C", {"id": "C", "writes": ["src/three.py"]},
                                 "plan.html", "M1")
        outside, clashes = execute.strayed(unit, ["src/two.py"], [beside])
        self.assertEqual(outside, ["src/two.py"])
        self.assertEqual(clashes, [("src/two.py", "B")])
        self.assertEqual(execute.strayed(unit, ["src/two.py"], [elsewhere])[1], [])

    def test_a_stray_seen_once_keeps_the_two_apart_next_time(self):
        """Not charging for the clash is only half of not repeating it.

        The declared lists are disjoint, so the scheduler would put these two
        together for ever. What the run watched happen has to reach it.
        """
        unit = execute.Unit("A", {"id": "A", "writes": ["src/one.py"]},
                            "plan.html", "M1")
        other = execute.Unit("B", {"id": "B", "writes": ["src/two.py"]},
                             "plan.html", "M1")
        self.assertFalse(execute.collides(unit, other))
        execute.recall({"strays": {"A": ["src/two.py"]}},
                       {"A": unit, "B": other})
        self.assertTrue(execute.collides(unit, other))
        self.assertEqual(execute.strayed(unit, ["src/two.py"], [other])[0],
                         ["src/two.py"],
                         "the write is still outside the declared list and the "
                         "record of that must not be silenced")



# ------------------------- R2-01 what the previous attempt left on the tree

WHOLE = """\
import json, re, sys
brief = open(sys.argv[1], encoding="utf-8").read()
open(%(trace)r, "a", encoding="utf-8").write(brief + "\\n=====\\n")
found = re.search(r"M[0-9]+-P[0-9]+-T[0-9]+", brief).group(0)
json.dump({"unit": found,
           "red": {"command": "x", "code": 1},
           "commands": [{"command": "x", "code": 0}],
           "criteria": {found + "-C1": True},
           "changes": ["src/left.py"],
           "denied": [], "decisions": []},
          open(sys.argv[2], "w", encoding="utf-8"))
"""

#: A judge that fails the first unit it sees and passes everything after.
ONCE = """\
import json, os, sys
p = %(marker)r
seen = os.path.exists(p)
open(p, "a", encoding="utf-8").write("x")
json.dump({"verdict": "pass"} if seen
          else {"verdict": "fail", "gap": "the second figure is not held apart"},
          open(sys.argv[2], "w", encoding="utf-8"))
"""


#: A worker that breaks a whole-repository guard the unit never named, and — on
#: the turn that hands it back — puts it right without touching anything else.
MENDER = """\
import json, os, re, sys
brief = open(sys.argv[1], encoding="utf-8").read()
if brief.startswith("# Guard"):
    open(%(trace)r, "a", encoding="utf-8").write(brief)
    %(mend)s
    json.dump({"changes": ["mended.txt"]}, open(sys.argv[2], "w", encoding="utf-8"))
    sys.exit(0)
open(%(broken)r, "w", encoding="utf-8").write("broken")
found = re.search(r"M[0-9]+-P[0-9]+-T[0-9]+", brief)
json.dump({"unit": found.group(0) if found else "?",
           "red": {"command": "python3 -m unittest", "code": 1},
           "commands": [{"command": "python3 -m unittest", "code": 0}],
           "criteria": {}, "changes": ["built.txt"], "denied": [],
           "decisions": []},
          open(sys.argv[2], "w", encoding="utf-8"))
"""


class TestAGuardTheUnitNeverHeardOf(Project):
    """F1. Seven of twelve gauntlet failures on a measured build were checks
    that cover the whole repository, and every one discarded a finished
    dispatch and briefed a fresh worker from nothing."""

    def guarded(self, mend=True, red="lint"):
        self.broken = os.path.join(self.bin, "guard-broken")
        self.trace = os.path.join(self.bin, "guard-briefs.txt")
        made, _ = self.builder(
            body=MENDER % {"trace": self.trace, "broken": self.broken,
                           "mend": ("os.remove(%r)" % self.broken) if mend
                                   else "pass"})
        judged, seen = self.judge()
        self.plan()
        stated = {"unit": [sys.executable, "-c", "pass"],
                  "lint": [sys.executable, "-c", "pass"]}
        stated[red] = [sys.executable, "-c",
                       "import os,sys; sys.exit(1 if os.path.exists(%r) else 0)"
                       % self.broken]
        self.configure(workers=[made, judged], attempts=1, gauntlet=stated)
        return seen

    def test_the_brief_names_the_guards_before_the_worker_starts(self):
        self.guarded()
        config = execute.settings(self.root)
        unit = execute.units(self.root)["M1-P1-T1"]
        text = execute.brief(self.root, config, unit)
        self.assertIn(layers.PREAMBLE, text,
                      "nothing had ever told a worker these checks existed")
        self.assertIn("lint ", text)
        self.assertIn(gauntlet.RUN_GUARDS, text,
                      "what the run does about a red guard is knowledge only a "
                      "run has; a pasted prompt's reader IS the run")
        self.assertEqual([], execute.check_brief(text))

    def test_a_red_guard_goes_back_to_the_worker_that_broke_it(self):
        self.guarded()
        ledger = self.drive()
        self.assertEqual(self.states()["M1-P1-T1"], schema.PASSING,
                         "the dispatch was not discarded and no fresh worker "
                         "was briefed from nothing")
        self.assertEqual(ledger["attempts"]["M1-P1-T1"], 1)
        directory = execute.place(self.root, "M1-P1-T1", 1, execute.BUILD)
        for name in (execute.GUARD_BRIEF, execute.GUARD_REPORT, execute.GUARD_LOG):
            self.assertTrue(os.path.exists(os.path.join(directory, name)), name)
        asked = self.read(self.trace)
        self.assertIn("M1-P1-T1", asked)
        self.assertIn("lint failed", asked, "it is told which check and why")
        for phrase in ("Fix that, and nothing else", "do not weaken, skip or exempt"):
            self.assertIn(phrase, asked)

    def test_what_the_guard_turn_changed_is_committed_with_the_unit(self):
        """A fix nobody commits is a status true of a tree nobody has."""
        seen = self.guarded()
        self.drive()
        shown = self.read(seen)
        self.assertIn("built.txt", shown)
        self.assertIn("mended.txt", shown,
                      "the guard turn's own changes are part of what this unit "
                      "has to land (NFR-EXE-11)")

    def test_a_guard_still_red_after_the_turn_fails_the_unit_once(self):
        self.guarded(mend=False)
        ledger = self.drive()
        self.assertIn("lint failed", ledger["unfinished"]["M1-P1-T1"])
        self.assertEqual(self.states()["M1-P1-T1"], schema.BLOCKED)
        self.assertEqual(self.read(self.trace).count("# Guard — M1-P1-T1"), 1,
                         "one turn and never a loop: a guard still red after "
                         "the worker was told is the unit's failure")

    def test_a_layer_the_unit_names_is_not_named_as_a_guard_but_is_preflighted(self):
        """The brief does not tell a unit its own layer is somebody else's
        check; the preflight runs it all the same (FR-EXE-17, amended)."""
        self.plan()
        config = self.configure(gauntlet={"unit": [sys.executable, "-c", "pass"]})
        unit = execute.units(self.root)["M1-P1-T1"]
        self.assertIn("unit", unit.entry.get("testLayers") or [])
        self.assertEqual(layers.guards(config["gauntlet"],
                                       unit.entry["testLayers"]), [])
        self.assertEqual(layers.cheap(config["gauntlet"]), ["unit"])

    def test_a_red_in_the_units_own_layer_goes_back_to_the_worker_too(self):
        """A forty-minute dispatch was discarded on a measured build for a red
        in the unit's OWN unit tests, which the worker that wrote them was the
        one person placed to fix. Cheap is cheap whoever named it."""
        self.guarded(red="unit")
        unit = execute.units(self.root)["M1-P1-T1"]
        self.assertIn("unit", unit.entry.get("testLayers") or [])
        ledger = self.drive()
        self.assertEqual(self.states()["M1-P1-T1"], schema.PASSING,
                         "handed back once, not discarded at the gauntlet")
        self.assertEqual(ledger["attempts"]["M1-P1-T1"], 1)
        asked = self.read(self.trace)
        self.assertEqual(asked.count("# Guard — M1-P1-T1"), 1)
        self.assertIn("unit failed", asked)

    def test_a_check_already_red_before_the_dispatch_is_not_handed_back(self):
        """Not this worker's to mend, and no attempt charged for it (FR-EXE-20)."""
        self.guarded(red="unit")
        ledger = execute.blank()
        config = execute.settings(self.root)
        with open(self.broken, "w", encoding="utf-8") as handle:
            handle.write("red before anything ran")
        execute.sweep(self.root, config, ledger, ["unit"])
        self.assertIn("unit", ledger["baseline"])
        unit = execute.units(self.root)["M1-P1-T1"]
        layer, why, mended = execute.preflight(
            self.root, config, ledger, unit, 1, lambda text: None)
        self.assertEqual((layer, mended), ("unit", []))
        self.assertIn("unit failed", why)
        self.assertFalse(os.path.exists(self.trace),
                         "no guard turn was run for a red the unit inherited")


class TestTheGauntletRunsCheapestFirst(Project):
    """F2. A red layer cost 25.4 minutes to reach a verdict of "no", because an
    end-to-end suite ran ahead of the static check that was going to fail."""

    def ordered(self, **codes):
        self.trace = os.path.join(self.bin, "gauntlet-order.txt")
        made, _ = self.builder()
        judged, _ = self.judge()
        self.plan()
        self.configure(workers=[made, judged], attempts=1, gauntlet={
            layer: [sys.executable, "-c",
                    "import sys; open(%r,'a').write(%r+chr(10)); sys.exit(%d)"
                    % (self.trace, layer, code)]
            for layer, code in codes.items()})

    def test_nothing_more_expensive_than_the_failure_ever_runs(self):
        self.ordered(unit=1, e2e=0)
        entry = execute.units(self.root)["M1-P1-T1"].entry
        entry["testLayers"] = ["e2e", "unit"]
        config = execute.settings(self.root)
        unit = execute.Unit(entry["id"], entry,
                            execute.units(self.root)["M1-P1-T1"].document, "M1")
        layer, failed = execute.prove(self.root, config, unit)
        self.assertEqual(layer, "unit")
        self.assertIn("unit failed", failed)
        self.assertEqual(self.read(self.trace).split(), ["unit", "unit"],
                         "the end-to-end suite never ran; the cheap check that "
                         "was going to fail got its turn first")

    def test_the_order_is_the_published_one_not_the_project_s(self):
        self.ordered(e2e=0, unit=0, lint=0)
        entry = execute.units(self.root)["M1-P1-T1"].entry
        entry["testLayers"] = ["e2e", "unit", "lint"]
        unit = execute.Unit(entry["id"], entry,
                            execute.units(self.root)["M1-P1-T1"].document, "M1")
        execute.prove(self.root, execute.settings(self.root), unit)
        self.assertEqual(self.read(self.trace).split(), ["lint", "unit", "e2e"])


class TestAUnitDoesNotPayForARedItInherited(Project):
    """F5. Two units on a measured build were retried for failures a third had
    caused, and both retries were spent discovering exactly that."""

    def red(self, layer="unit"):
        self.marker = os.path.join(self.bin, "already-red")
        with open(self.marker, "w", encoding="utf-8") as handle:
            handle.write("red")
        self.plan()
        return self.configure(attempts=2, gauntlet={
            layer: [sys.executable, "-c",
                    "import os,sys; sys.exit(1 if os.path.exists(%r) else 0)"
                    % self.marker]})

    def test_the_run_says_what_was_already_red_before_it_dispatched_anything(self):
        self.red()
        out = io.StringIO()
        ledger = execute.run(self.root, out)
        self.assertIn("unit", ledger["baseline"])
        self.assertIn("already red before anything was dispatched",
                      out.getvalue())

    def test_a_layer_already_red_charges_the_unit_no_attempt(self):
        self.red()
        ledger = self.drive()
        self.assertGreaterEqual(ledger["misfires"].get("M1-P1-T1", 0), 2,
                                "FR-EXE-20: it was failing before this unit's "
                                "worker started, so whatever else is true the "
                                "unit did not do it — that is a misfire, and the "
                                "misfire counter is what stops the run")
        self.assertIn("already red before this unit was ever dispatched",
                      ledger["unfinished"]["M1-P1-T1"])

    def test_a_layer_that_goes_green_stops_being_a_baseline_red(self):
        config = self.red()
        ledger = execute.blank()
        execute.sweep(self.root, config, ledger, ["unit"])
        self.assertIn("unit", ledger["baseline"])
        os.remove(self.marker)
        execute.sweep(self.root, config, ledger, ["unit"])
        self.assertEqual(ledger["baseline"], {},
                         "the record is what is true now, not what was ever true")

    def test_a_milestone_boundary_runs_every_layer_the_project_states(self):
        """A latent red nobody looks for surfaces a long way from its cause."""
        trace = os.path.join(self.bin, "boundary.txt")
        self.plan()
        self.configure(attempts=1, gauntlet={
            layer: [sys.executable, "-c",
                    "open(%r,'a').write(%r+chr(10))" % (trace, layer)]
            for layer in ("unit", "e2e")})
        out = io.StringIO()
        execute.run(self.root, out)
        self.assertIn("milestone boundary — running every layer", out.getvalue())
        self.assertIn("e2e", self.read(trace),
                      "no unit in this plan names e2e, so the boundary is the "
                      "only moment it would ever be run")

    def test_the_opening_survey_leaves_the_expensive_layers_alone(self):
        """It runs before anything is dispatched; standing an environment up to
        survey it would cost more than the survey is worth."""
        trace = os.path.join(self.bin, "opening.txt")
        self.plan()
        config = self.configure(gauntlet={
            layer: [sys.executable, "-c",
                    "open(%r,'a').write(%r+chr(10))" % (trace, layer)]
            for layer in ("unit", "e2e")})
        ledger = execute.blank()
        execute.sweep(self.root, config, ledger,
                      [one for one in config["gauntlet"]
                       if one not in layers.INFRASTRUCTURE])
        self.assertEqual(self.read(trace).split(), ["unit"])


class TestAWriteListCorrectionNeedsNoRegeneration(Project):
    """F4. A declared write set lives in a generated document, so correcting one
    used to mean regenerating the plan a run is holding open."""

    def pair(self, **overlay):
        self.plan()
        ledger = execute.blank()
        ledger["overlay"] = overlay
        found = execute.units(self.root)
        for unit in found.values():
            unit.entry["writes"] = ["src/%s" % unit.id]
        execute.recall(ledger, found)
        return ledger, found

    def test_two_units_the_plan_read_as_disjoint_stop_being_disjoint(self):
        ledger, found = self.pair()
        first, second = found["M1-P1-T1"], found["M1-P1-T2"]
        self.assertFalse(execute.collides(first, second))
        ledger["overlay"] = {"M1-P1-T1": ["src/M1-P1-T2/client.ts"]}
        execute.recall(ledger, found)
        self.assertTrue(execute.collides(first, second),
                        "the correction has to reach the next scheduling "
                        "decision, which is what `collides` is")

    def test_a_corrected_path_is_no_longer_a_stray(self):
        ledger, found = self.pair(**{"M1-P1-T1": ["shared/manifest.txt"]})
        unit = found["M1-P1-T1"]
        outside, _ = execute.strayed(unit, ["shared/manifest.txt"])
        self.assertEqual(outside, [],
                         "the operator declared it; reporting it as a stray "
                         "every round would be noise about a settled thing")

    def test_it_only_ever_widens(self):
        ledger, found = self.pair(**{"M1-P1-T1": []})
        unit = found["M1-P1-T1"]
        outside, _ = execute.strayed(unit, ["somewhere/else.ts"])
        self.assertEqual(outside, ["somewhere/else.ts"],
                         "an overlay that narrowed a write set would be a way "
                         "of switching the disjointness check off")

    def test_the_run_says_which_correction_it_acted_on_once(self):
        ledger, found = self.pair(**{"M1-P1-T1": ["shared/manifest.txt"]})
        execute.recall(ledger, found)
        execute.recall(ledger, found)
        said = [one for one in ledger["notes"] if "correction was applied" in one]
        self.assertEqual(len(said), 1)
        self.assertIn("shared/manifest.txt", said[0])

    def test_the_stray_notice_names_the_door(self):
        """The overlay existed for a whole build and nobody found it, because
        the notice named the problem and not the door."""
        phases = detail()
        phases[0]["tasks"][0]["writes"] = ["src/one.py", "tests/test_one.py"]
        self.plan(phases)
        build, _ = self.builder(body=STRAY % {"changes": repr(
            {"M1-P1-T1": ["src/one.py", "shared/manifest.txt"]})})
        judged, _ = self.judge()
        self.configure(workers=[build, judged], ceiling=1, attempts=1)
        ledger = self.drive()
        said = [one for one in ledger["notes"]
                if "shared/manifest.txt" in one and "does not cover" in one]
        self.assertTrue(said, ledger["notes"])
        self.assertIn("`overlay`", said[0])
        self.assertIn(execute._ledger_path(self.root), said[0])
        self.assertIn("family", said[0])


class TestAWriteFamilyIsDeclaredOnce(Project):
    """F6. A migration is never one file, and every migration a measured build
    made reported the other four as strays; a shared manifest every unit adds a
    line to was a collision the plan could not express."""

    FAMILIES = [{"when": "drizzle/migrations/**",
                 "also": ["drizzle/meta/_journal.json", "src/db/types.ts"]}]

    def declared(self, **writes):
        self.plan()
        found = execute.units(self.root)
        for unit in found.values():
            unit.entry["writes"] = writes.get(unit.id, ["src/%s" % unit.id])
        return found

    def test_a_unit_writing_under_a_family_is_not_stray_on_its_members(self):
        found = self.declared(**{"M1-P1-T1": ["drizzle/migrations/0007.sql"]})
        execute.recall(execute.blank(), found, {"families": self.FAMILIES})
        unit = found["M1-P1-T1"]
        self.assertEqual(unit.entry["implied"],
                         ["drizzle/meta/_journal.json", "src/db/types.ts"])
        outside, _ = execute.strayed(
            unit, ["drizzle/migrations/0007.sql", "drizzle/meta/_journal.json"])
        self.assertEqual(outside, [])

    def test_two_units_implied_onto_one_file_do_not_run_together(self):
        found = self.declared(**{"M1-P1-T1": ["drizzle/migrations/0007.sql"],
                                 "M1-P1-T2": ["drizzle/migrations/0008.sql"]})
        first, second = found["M1-P1-T1"], found["M1-P1-T2"]
        self.assertFalse(execute.collides(first, second))
        ledger = execute.blank()
        execute.recall(ledger, found, {"families": self.FAMILIES})
        self.assertTrue(execute.collides(first, second),
                        "both will write the journal; the family says so once")
        execute.recall(ledger, found, {"families": self.FAMILIES})
        said = [one for one in ledger["notes"] if "implied by" in one]
        self.assertEqual(len(said), 2, "said once per unit, not once per round")

    def test_a_family_since_removed_does_not_outlive_the_settings(self):
        found = self.declared(**{"M1-P1-T1": ["drizzle/migrations/0007.sql"]})
        execute.recall(execute.blank(), found, {"families": self.FAMILIES})
        execute.recall(execute.blank(), found, {"families": []})
        self.assertEqual(found["M1-P1-T1"].entry["implied"], [])

    def test_an_appendable_path_is_neither_a_stray_nor_a_collision(self):
        found = self.declared(**{"M1-P1-T1": ["src/one.py", "CLAUDE.md"],
                                 "M1-P1-T2": ["src/two.py", "CLAUDE.md"]})
        first, second = found["M1-P1-T1"], found["M1-P1-T2"]
        self.assertTrue(execute.collides(first, second))
        self.assertFalse(execute.collides(first, second, ["CLAUDE.md"]))
        outside, _ = execute.strayed(second, ["src/two.py", "CLAUDE.md"],
                                     appendable=["CLAUDE.md"])
        self.assertEqual(outside, [])
        self.assertEqual(execute.strayed(second, ["CLAUDE.md"])[0], [],
                         "declared, so never a stray anyway")

    def test_a_claim_on_everything_is_not_dropped_for_an_appendable_beneath_it(self):
        found = self.declared(**{"M1-P1-T1": ["**"], "M1-P1-T2": ["src/two.py"]})
        self.assertTrue(execute.collides(found["M1-P1-T1"], found["M1-P1-T2"],
                                         ["CLAUDE.md"]))

    def test_a_malformed_family_is_refused_before_anything_starts(self):
        self.plan()
        self.configure(families=[{"when": "drizzle/migrations/**"}])
        with self.assertRaises(execute.Refused) as caught:
            execute.settings(self.root)
        self.assertIn("also", str(caught.exception))
        self.configure(families="drizzle/migrations/**")
        with self.assertRaises(execute.Refused):
            execute.settings(self.root)
        self.configure(appendable="CLAUDE.md")
        with self.assertRaises(execute.Refused) as caught:
            execute.settings(self.root)
        self.assertIn("appendable", str(caught.exception))
        self.configure(families=self.FAMILIES, appendable=["CLAUDE.md"])
        held = execute.settings(self.root)
        self.assertEqual(held["families"], self.FAMILIES)
        self.assertEqual(held["appendable"], ["CLAUDE.md"])

    def test_an_old_ledger_gains_the_key_and_loses_nothing(self):
        """`load` carries forward only keys `blank` names, so every key added
        here is backward-compatible by construction."""
        path = execute._ledger_path(self.root)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"next": "dispatch M1-P1-T1", "done": ["M1-P1-T9"]}, handle)
        held = execute.load(self.root)
        self.assertEqual(held["done"], ["M1-P1-T9"])
        for key in ("overlay", "baseline", "launches"):
            self.assertEqual(held[key], execute.blank()[key], key)


class TestABlameClaimIsCheckedAgainstHistory(Project):
    """F5b. A worker asserting whose breakage this was would be a claim, and a
    claim the run can check for itself is a claim the run should not take."""

    def repo(self):
        for command in (["git", "init", "-q"],
                        ["git", "config", "user.email", "t@example.com"],
                        ["git", "config", "user.name", "t"]):
            subprocess.run(command, cwd=self.root, check=True,
                           capture_output=True)

    def landed(self, subject, path="shared/manifest.txt"):
        full = os.path.join(self.root, path)
        if not os.path.isdir(os.path.dirname(full)):
            os.makedirs(os.path.dirname(full))
        with open(full, "a", encoding="utf-8") as handle:
            handle.write("line\n")
        subprocess.run(["git", "add", "--", path], cwd=self.root, check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", subject], cwd=self.root,
                       check=True, capture_output=True)
        return path

    def test_git_names_the_unit_that_landed_a_path(self):
        self.repo()
        path = self.landed("M1-P2-T9: something else entirely")
        self.assertEqual(status.committed_by(self.root, path), "M1-P2-T9")

    def test_a_subject_this_method_did_not_write_names_nobody(self):
        self.repo()
        path = self.landed("chore: tidy up")
        self.assertEqual(status.committed_by(self.root, path), "")

    def test_no_repository_at_all_is_a_shrug_and_not_a_crash(self):
        self.assertEqual(status.committed_by(self.root, "anything.txt"), "")

    def test_a_unit_is_not_re_dispatched_over_work_another_unit_landed(self):
        self.repo()
        path = self.landed("M1-P2-T9: the unit that actually wrote this")
        self.plan()
        unit = execute.units(self.root)["M1-P1-T1"]
        self.assertEqual(execute.blamed(self.root, unit, [path]),
                         [(path, "M1-P2-T9")])
        self.assertEqual(execute.blamed(self.root, unit, ["nothing-here.txt"]), [],
                         "history that says nothing blames nobody")


class TestARetryIsToldWhatItsPredecessorLeftBehind(Project):
    """R2-01. The rule as written rewarded the looser claim.

    `M15-P1-T2` attempt 2 found its predecessor's work already standing on the
    tree, had nothing of its own to put in `changes`, and was rejected for
    naming no file. It had refused, in writing, to claim work it did not do —
    and attempt 3 listed the same five files as its own and passed. Attempt 2
    had also spent its context rebuilding that inventory by hand, under its own
    heading, because nothing told it.

    The run already holds the failed report, so nothing new is asked of a
    worker and no key joins the report contract (E2-02).
    """

    def whole(self, name="builder"):
        trace = os.path.join(self.bin, "%s-briefs.txt" % name)
        return worker(name, execute.BUILD,
                      script(self.bin, "%s.py" % name,
                             WHOLE % {"trace": trace})), trace

    def once(self, name="judge"):
        marker = os.path.join(self.bin, "%s-seen" % name)
        return worker(name, execute.JUDGE,
                      script(self.bin, "%s.py" % name,
                             ONCE % {"marker": marker}))

    def test_a_rejected_attempt_s_changes_are_kept(self):
        self.plan()
        build, _ = self.whole()
        self.configure(workers=[build, self.once()], ceiling=1, attempts=1)
        ledger = self.drive()
        self.assertEqual(ledger["standing"].get("M1-P1-T1"),
                         {"attempt": 1, "changes": ["src/left.py"]})

    def test_a_unit_that_passed_leaves_nothing_standing(self):
        self.plan()
        build, _ = self.whole()
        judged, _ = self.judge()
        self.configure(workers=[build, judged], ceiling=1, attempts=1)
        ledger = self.drive()
        self.assertNotIn("M1-P1-T1", ledger["standing"])

    def test_the_block_says_naming_the_files_is_correct_not_a_claim(self):
        self.plan()
        config = self.configure()
        unit = execute.units(self.root)["M1-P1-T1"]
        text = execute.brief(self.root, config, unit, gap="short",
                             standing={"attempt": 1, "changes": ["src/left.py"]})
        self.assertIn("src/left.py", text)
        self.assertIn("attempt 1", text.lower())
        self.assertIn("you did not write", text.lower())
        self.assertIn("changes", text)

    def test_a_brief_with_nothing_standing_carries_no_such_block(self):
        self.plan()
        config = self.configure()
        unit = execute.units(self.root)["M1-P1-T1"]
        self.assertNotIn("already standing on the working tree",
                         execute.brief(self.root, config, unit))

    def test_the_second_brief_states_the_work_and_the_retry_is_accepted(self):
        self.plan()
        build, seen = self.whole()
        self.configure(workers=[build, self.once()], ceiling=1, attempts=2)
        self.drive()
        briefs = self.read(seen).split("=====")
        self.assertNotIn("src/left.py", briefs[0],
                         "nothing was standing when the first attempt started")
        self.assertIn("src/left.py", briefs[1])
        self.assertEqual(self.states()["M1-P1-T1"], schema.PASSING)



if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()


#: A worker that leaves a marker behind. The check below is green until it does,
#: so the red appears where a sibling's half-written work would appear: after
#: the dispatch, not before it, and so not in the opening survey's baseline.
MARKER = """\
import json, re, sys
brief = open(sys.argv[1], encoding="utf-8").read()
found = re.search(r"M[0-9]+-P[0-9]+-T[0-9]+", brief).group(0)
open(%(marker)r, "a", encoding="utf-8").write(found + chr(10))
json.dump({"unit": found,
           "red": {"command": "x", "code": 1},
           "commands": [{"command": "x", "code": 0}],
           "criteria": {found + "-C1": True},
           "changes": ["src/one.py"], "denied": [], "decisions": []},
          open(sys.argv[2], "w", encoding="utf-8"))
"""

#: A check that goes red once the marker is there, and names one file in its
#: output. The shape is a real `tsc` line, decoration and all.
NAMING = """\
import os, sys
if not os.path.exists(%(marker)r):
    raise SystemExit(0)
sys.stdout.write(%(named)r + "(15,59): error TS2307: Cannot find module" + chr(10))
raise SystemExit(1)
"""


class TestAUnitDoesNotPayForASiblingsHalfWrittenWork(Project):
    """R3-01. Two units each lost an attempt to twelve type errors in two files
    neither of them owned.

    Both files were the declared write set of a third unit that was still
    building, and that unit was doing exactly what its brief told it to: write
    the failing test first. Its tests were on the tree before the module they
    import was. So `inherited` could not see it — the red did not exist at the
    opening survey — and `blamed` could not see it either, because it asks git
    and a unit still building has committed nothing.

    The plan could see it. The write sets that decide who may run beside whom
    also decide whose files these are.
    """

    def setUp(self):
        Project.setUp(self)
        # `implicated` drops a token whose first segment is not a directory
        # here, which is what keeps a host out of a URL from reading as a file.
        for name in ("src", "tests"):
            os.makedirs(os.path.join(self.root, name), exist_ok=True)
        self.marker = os.path.join(self.bin, "dispatched")

    def declared(self):
        phases = detail()
        phases[0]["tasks"][0]["writes"] = ["src/one.py", "tests/test_one.py"]
        phases[0]["tasks"][1]["writes"] = ["src/two.py", "tests/test_two.py"]
        phases[0]["tasks"][2]["writes"] = ["src/three.py", "tests/test_three.py"]
        return phases

    def check(self, named, layer="unit"):
        return {layer: [sys.executable,
                        script(self.bin, "check-%s.py" % layer,
                               NAMING % {"marker": self.marker, "named": named})]}

    def dispatched(self, named, layer="unit", attempts=2, out=None, **extra):
        phases = self.declared()
        if layer != "unit":
            for one in phases[0]["tasks"]:
                one["testLayers"] = [layer]
        self.plan(phases)
        build, _ = self.builder(body=MARKER % {"marker": self.marker})
        judged, _ = self.judge()
        held = {"workers": [build, judged], "ceiling": 1, "attempts": attempts}
        held.update(extra)
        self.configure(gauntlet=self.check(named, layer), **held)
        return execute.run(self.root, out) if out is not None else self.drive()

    def test_a_red_naming_only_another_units_files_charges_no_attempt(self):
        ledger = self.dispatched("src/two.py")
        self.assertGreaterEqual(ledger["misfires"].get("M1-P1-T1", 0), 2,
                                "nothing the red names is this unit's to have "
                                "touched, so the red is not this unit's")
        said = ledger["unfinished"].get("M1-P1-T1", "")
        self.assertIn("src/two.py", said)
        self.assertIn("M1-P1-T2", said,
                      "the note names the sibling that declares the file")

    def test_a_red_naming_a_file_the_unit_declared_still_charges_an_attempt(self):
        """The guard rail. Excusing every red would excuse every unit."""
        ledger = self.dispatched("src/one.py")
        self.assertEqual(ledger["misfires"].get("M1-P1-T1", 0), 0)
        self.assertEqual(ledger["attempts"].get("M1-P1-T1"), 2)
        self.assertEqual(self.states()["M1-P1-T1"], schema.BLOCKED)

    def test_the_same_holds_for_a_layer_only_the_gauntlet_reaches(self):
        """`integration` needs a database, so no preflight and no survey runs
        it — the only place it is reached is the unit's own gauntlet."""
        ledger = self.dispatched("src/two.py", layer="integration")
        self.assertGreaterEqual(ledger["misfires"].get("M1-P1-T1", 0), 2)
        self.assertIn("src/two.py", ledger["unfinished"].get("M1-P1-T1", ""))

    def test_a_red_that_is_not_this_units_is_never_handed_back_to_its_worker(self):
        """A hand-back spends a whole turn asking a worker to mend work that is
        not on the tree yet and is not its own (FR-EXE-17)."""
        out = io.StringIO()
        self.dispatched("src/two.py", attempts=1, out=out)
        said = [line for line in out.getvalue().splitlines() if "M1-P1-T1" in line]
        self.assertIn("src/two.py", "\n".join(said))
        self.assertNotIn("handed back to", "\n".join(said))
        self.assertFalse(os.path.exists(
            os.path.join(execute.place(self.root, "M1-P1-T1", 1, execute.BUILD),
                         execute.GUARD_REPORT)))
        # And the other half of the same run, which is the guard rail: the unit
        # that DOES declare `src/two.py` gets its own red handed straight back.
        self.assertIn("handed back to",
                      "\n".join(line for line in out.getvalue().splitlines()
                                if "M1-P1-T2" in line))

    def test_every_layer_leaves_what_it_printed_where_the_run_can_read_it(self):
        self.dispatched("src/two.py", attempts=1)
        log = os.path.join(execute.place(self.root, "M1-P1-T1", 1, execute.BUILD),
                           execute.LAYER_LOG % "unit")
        self.assertIn("TS2307", self.read(log),
                      "a run that threw away what a check printed could say a "
                      "layer was red and nothing at all about what it named")


class TestWhatACheckerNames(unittest.TestCase):
    """`implicated` against the shapes real tools actually print."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-named-")
        for name in ("src", "tests", "node_modules"):
            os.makedirs(os.path.join(self.root, name))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def named(self, text):
        return execute.implicated(self.root, text)

    def test_typescript(self):
        self.assertEqual(
            self.named("tests/integration/recall.test.ts(15,59): error TS2307: "
                       "Cannot find module '../../src/wanted.ts' or its "
                       "corresponding type declarations."),
            ["tests/integration/recall.test.ts"],
            "the erroring file is named; the relative import is not, because "
            "resolving it wants the parser this deliberately is not")

    def test_eslint_prints_an_absolute_path_on_a_line_of_its_own(self):
        self.assertEqual(
            self.named("%s\n  12:5  error  Unexpected any\n"
                       % os.path.join(self.root, "src", "shred.ts")),
            ["src/shred.ts"])

    def test_pytest(self):
        self.assertEqual(self.named("FAILED tests/test_one.py::test_it - "
                                    "AssertionError"),
                         ["tests/test_one.py"])

    def test_an_absolute_path_outside_the_repository_is_not_the_repositorys(self):
        self.assertEqual(self.named("/usr/lib/python3/json/decoder.py:355"), [])

    def test_dependencies_and_the_working_area_are_nobodys_declared_work(self):
        self.assertEqual(self.named("node_modules/left-pad/index.js:1\n"
                                    ".zero/state/work/M1-P1-T1-1-build/build.log"),
                         [])

    def test_a_host_out_of_a_url_is_not_a_file(self):
        self.assertEqual(self.named("see https://example.com/docs/rule.html"), [])

    def test_each_path_once_and_in_the_order_it_was_named(self):
        self.assertEqual(self.named("src/b.py:1\ntests/a.py:2\nsrc/b.py:9"),
                         ["src/b.py", "tests/a.py"])


class TestAReportTheContractRefusesIsNotAnAttempt(Project):
    """R2-05. The budget was spent on rounds that never reached a verdict.

    A report whose shape is wrong says the worker misread its instructions or
    its harness truncated the file. Either way nothing was learned about the
    work, which is exactly what a misfire is for — and still bounded, because a
    unit blocks once it has missed as many times as it may attempt.
    """

    def bad(self, body):
        self.plan()
        build, _ = self.builder(body=body)
        judged, _ = self.judge()
        self.configure(workers=[build, judged], ceiling=1, attempts=2)
        return self.drive()

    def test_a_malformed_report_is_a_misfire_and_leaves_a_gap(self):
        ledger = self.bad(
            'import json, sys\n'
            'json.dump({"unit": "?"}, open(sys.argv[2], "w", encoding="utf-8"))\n')
        self.assertGreaterEqual(ledger["misfires"].get("M1-P1-T1", 0), 2)
        self.assertIn("no observed failing test",
                      ledger["gaps"].get("M1-P1-T1", "")
                      + ledger["unfinished"].get("M1-P1-T1", ""),
                      "the next brief has to say what was wrong with the last "
                      "report, or the next worker writes the same one")

    def test_a_landed_commit_that_is_not_in_history_is_a_misfire_too(self):
        ledger = self.bad(
            'import json, re, sys\n'
            'brief = open(sys.argv[1], encoding="utf-8").read()\n'
            'found = re.search(r"M[0-9]+-P[0-9]+-T[0-9]+", brief).group(0)\n'
            'json.dump({"unit": found, "red": {"command": "x", "code": 1},\n'
            '           "commands": [{"command": "x", "code": 0}],\n'
            '           "criteria": {found + "-C1": True}, "changes": [],\n'
            '           "landed": "0123456789abcdef", "denied": [],\n'
            '           "decisions": []},\n'
            '          open(sys.argv[2], "w", encoding="utf-8"))\n')
        self.assertGreaterEqual(ledger["misfires"].get("M1-P1-T1", 0), 2)


class TestAWorkerThatSaysItDidNotFinishIsHeard(Project):
    """R2-03. A self-declared unfinished report was invisible to the run.

    Nothing read the criteria on a report that was otherwise well formed, so a
    worker that honestly reported it got part-way and one that reported it
    finished were the same line in the log. Not a verdict — only the judge
    passes a unit (FR-EXE-14) — but no longer silent.
    """

    def test_a_report_claiming_no_criterion_met_says_so_on_the_run_s_line(self):
        self.plan()
        judged, _ = self.judge()
        build, _ = self.builder()          # GOOD claims nothing met
        self.configure(workers=[build, judged], ceiling=1, attempts=1)
        out = io.StringIO()
        ledger = execute.run(self.root, out)
        self.assertIn("does not claim to have finished the unit", out.getvalue())
        self.assertIn("does not claim to have finished the unit",
                      " ".join(ledger["notes"]))

    def test_both_shapes_of_criteria_are_read_in_one_place(self):
        self.assertEqual(execute.met({"criteria": {"C1": True, "C2": False}}),
                         (["C1"], True))
        self.assertEqual(execute.met({"criteria": [{"id": "C1", "met": True},
                                                   {"id": "C2", "met": False}]}),
                         (["C1"], True))
        self.assertEqual(execute.met({"criteria": ["C1"]}), ([], False),
                         "a list of bare identifiers says who and never whether")
        self.assertEqual(execute.met({}), ([], True),
                         "nothing claimed is readable and empty, not unreadable")


#: A worker that stops the run that dispatched it, the way an operator does.
#: Its parent IS the orchestrator: `dispatch.launch` runs in one of the run's
#: own threads, so the signal goes exactly where a `kill -TERM` on the run's pid
#: would go — and, without a handler, exactly where it used to go unheard.
STOPPER = """\
import os, signal, sys, time
open(%(trace)r, "a", encoding="utf-8").write(str(os.getpid()) + chr(10))
os.kill(os.getppid(), signal.SIGTERM)
time.sleep(30)
"""


class TestStoppingTheRunStopsTheWorkers(Project):
    """R3-02. A `kill -TERM` on the orchestrator left every worker running.

    Both halves of the cause were correct on their own. A worker gets its own
    session so that its test runner's children cannot signal the operator's
    shell, and `dispatch` ends a worker by signalling that group. What was
    missing is the third thing: nothing in the run ever caught the operator's
    own stop, so the one path that never reached the group kill was the one an
    operator actually takes. Four `claude -p` processes survived each of two
    stops of a real build, still editing the tree.
    """

    def test_the_handlers_go_back_exactly_as_they_were(self):
        before = {name: signal.getsignal(getattr(signal, name))
                  for name in execute.STOPS}
        restore = execute.stopping(io.StringIO())
        self.assertNotEqual(signal.getsignal(signal.SIGTERM), before["SIGTERM"])
        restore()
        self.assertEqual({name: signal.getsignal(getattr(signal, name))
                          for name in execute.STOPS}, before,
                         "a run that left its handlers installed would catch a "
                         "signal meant for whatever ran after it")

    def test_a_run_leaves_no_handler_of_its_own_behind(self):
        before = {name: signal.getsignal(getattr(signal, name))
                  for name in execute.STOPS}
        self.plan()
        self.configure(ceiling=1, attempts=1)
        self.drive()
        self.assertEqual({name: signal.getsignal(getattr(signal, name))
                          for name in execute.STOPS}, before)

    def stopper(self):
        """A worker that stops the run, and a trace of every one that started."""
        self.trace = os.path.join(self.bin, "stopper.txt")
        return self.builder(body=STOPPER % {"trace": self.trace})[0]

    def test_a_stop_ends_the_workers_settles_nothing_and_charges_nothing(self):
        self.plan()
        build = self.stopper()
        judged, _ = self.judge()
        self.configure(workers=[build, judged], ceiling=1, attempts=2)
        out = io.StringIO()
        try:
            ledger = execute.run(self.root, out)
        finally:
            dispatch.STOPPING.clear()
        self.assertIn("ending every worker this run started", out.getvalue())
        self.assertIn("no unit was charged", out.getvalue())
        self.assertEqual(ledger["attempts"], {},
                         "nothing was settled, so nothing was charged")
        self.assertEqual(ledger["misfires"], {})
        self.assertEqual(self.states()["M1-P1-T1"], schema.IN_PROGRESS,
                         "the status the dispatch wrote stands; the next run "
                         "takes it back through `abandoned()`")
        self.assertIn("left unsettled and charged nothing",
                      " ".join(ledger["notes"]))
        self.assertEqual(dispatch._LIVE, set())

    def test_a_stopped_run_writes_no_retrospective_and_keeps_its_bookmark(self):
        self.plan()
        build = self.stopper()
        judged, _ = self.judge()
        self.configure(workers=[build, judged], ceiling=1, attempts=2)
        try:
            ledger = execute.run(self.root, io.StringIO())
        finally:
            dispatch.STOPPING.clear()
        self.assertTrue(ledger["next"],
                        "`next` is what tells the run that comes after this one "
                        "what this one was in the middle of")

    def test_a_stop_starts_nothing_further_not_even_a_recovery_turn(self):
        """The half of this that a first attempt got wrong.

        A killed worker leaves no report, and the run's answer to a worker that
        left no report is to ask it what it built — bounded, deliberate, and
        exactly wrong here. Ending four workers started four more, in a run the
        operator had just stopped, and the second wave was still editing the
        tree. The guard is on the launcher rather than on that one caller: it is
        the one door out of the run, and a check the stop interrupted must not be
        recorded as red either.
        """
        self.plan()
        build = self.stopper()
        judged, _ = self.judge()
        self.configure(workers=[build, judged], ceiling=1, attempts=2)
        try:
            execute.run(self.root, io.StringIO())
        finally:
            dispatch.STOPPING.clear()
        self.assertEqual(len(self.read(self.trace).split()), 1,
                         "one dispatch was in flight, so exactly one worker ran")

    def test_a_stopping_run_records_no_result_for_a_check_it_interrupted(self):
        self.plan()
        config = self.configure(ceiling=1, attempts=1)
        dispatch.STOPPING.set()
        try:
            with self.assertRaises(status.Refused) as caught:
                status.ran(self.root, "unit", config["gauntlet"]["unit"])
        finally:
            dispatch.STOPPING.clear()
        self.assertIn("stopping", str(caught.exception))
        self.assertEqual(status.evidence(self.root), {},
                         "a check somebody killed proved nothing, and writing "
                         "its exit status down would invent a result")
