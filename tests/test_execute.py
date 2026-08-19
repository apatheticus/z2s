# -*- coding: utf-8 -*-
"""What the orchestrator must do, and what it must never do (M11).

The worker in these tests is a small Python script written per case. That is the
point of a worker being a command: the contract can be exercised end to end with
nothing installed, no agent, and no network — and a test can make a worker
behave exactly as badly as the rule under test needs it to.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from z2s import execute, gate, gauntlet, paths, plan, schema, status  # noqa: E402
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
        phases[0]["tasks"][0]["writes"] = ["src/one.py"]
        phases[0]["tasks"][1]["writes"] = ["src/two.py"]
        self.plan(phases)
        found = execute.units(self.root)
        self.assertEqual(found["M1-P1-T1"].entry.get("writes"), ["src/one.py"])
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

    def test_a_denied_permission_is_reported_with_its_rule(self):
        denied, _ = self.builder(body=(
            "import json, sys\n"
            "json.dump({'red': {'command': 'x', 'code': 1},\n"
            "           'denied': [{'action': 'read ~/.ssh/id_rsa',\n"
            "                       'rule': 'outside the project area'}]},\n"
            "          open(sys.argv[2], 'w'))\n"))
        self.plan()
        self.configure(workers=[denied, self.judge()[0]], attempts=1)
        ledger = self.drive()
        self.assertIn("outside the project area", ledger["unfinished"]["M1-P1-T1"])

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
        status.set_status(self.root, "M1-P1-T1", schema.BLOCKED)
        execute.stall(self.root, execute.units(self.root), ledger, config)
        self.assertEqual(self.states()["M1-P1-T2"], schema.BLOCKED,
                         "what it waits on has stopped")

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
        ledger["attempts"]["M1-P1-T1"] = 1

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


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
