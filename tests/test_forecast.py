# -*- coding: utf-8 -*-
"""What a plan costs in concurrency, computed before anything is dispatched.

Every case here is about one claim: the forecast reaches the same answer the
orchestrator would, because it asks the orchestrator. So the fixtures are real
generated plan documents rather than hand-built dictionaries — a forecast that
agreed with a fixture and disagreed with a plan would be worse than none.
"""

import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from z2s import execute, forecast, gate, paths, plan, schema  # noqa: E402
from test_plan import (DECISIONS, FUNCTIONAL, TECHNICAL, build_chain, closed,  # noqa: E402
                       plan_brief, task)


def pair(first=None, second=None):
    """Two tasks that between them claim everything the chain above states."""
    return [task(1, {"fr": FUNCTIONAL}, **(first or {})),
            task(2, {"nfr": TECHNICAL, "adr": DECISIONS}, **(second or {}))]


class Plan(unittest.TestCase):
    """A real generated plan on disk, with no workers and no run behind it."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-forecast-")
        build_chain(self.root)
        paths.ensure_layout(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write(self, tasks):
        phases = [{"id": "M1-P1", "title": "Build it",
                   "summary": "All of the work.", "dependsOn": [],
                   "completion": ["Every task in the phase passes."],
                   "tasks": tasks}]
        made = plan_brief()
        with open(plan.detail_path(self.root, "M1"), "w", encoding="utf-8") as handle:
            json.dump(phases, handle)
        return plan.author(self.root, made,
                           closed(gate.Gate(plan.SLUG, plan.forks(made), source=made)))

    def config(self, **extra):
        held = dict(forecast.UNCONFIGURED)
        held["families"] = list(held["families"])
        held["appendable"] = list(held["appendable"])
        held.update(extra)
        return held

    def rounds(self, tasks, **extra):
        self.write(tasks)
        return forecast.schedule(self.root, self.config(**extra))


# --------------------------------------------------- the whole point, in one pair

class TestWhatADeclarationCosts(Plan):

    def test_two_units_writing_different_files_run_in_one_round(self):
        played = self.rounds(pair({"writes": ["src/a.py", "tests/unit/a.py"]},
                                  {"writes": ["src/b.py", "tests/unit/b.py"]}))
        self.assertEqual([["M1-P1-T1", "M1-P1-T2"]], played)

    def test_the_same_two_claiming_one_test_directory_run_in_two(self):
        played = self.rounds(pair({"writes": ["src/a.py", "tests/**"]},
                                  {"writes": ["src/b.py", "tests/**"]}))
        self.assertEqual([["M1-P1-T1"], ["M1-P1-T2"]], played)

    def test_a_dependency_serialises_units_whose_writes_are_disjoint(self):
        played = self.rounds(pair({"writes": ["src/a.py", "tests/unit/a.py"]},
                                  {"writes": ["src/b.py", "tests/unit/b.py"],
                                   "dependsOn": ["M1-P1-T1"]}))
        self.assertEqual([["M1-P1-T1"], ["M1-P1-T2"]], played)

    def test_a_unit_declaring_nothing_runs_alone(self):
        # M11-04, reached through `collides` rather than restated here.
        played = self.rounds(pair({"writes": ["src/a.py", "tests/unit/a.py"]}, {}))
        self.assertEqual(2, len(played))


# ------------------------------------------- the exemptions the run already has

class TestTheForecastReadsTheProjectsOwnSettings(Plan):

    def test_an_appendable_path_does_not_serialise_two_units(self):
        tasks = pair({"writes": ["src/a.py", "tests/unit/a.py", "CLAUDE.md"]},
                     {"writes": ["src/b.py", "tests/unit/b.py", "CLAUDE.md"]})
        self.write(tasks)
        held = forecast.schedule(self.root, self.config())
        exempted = forecast.schedule(self.root,
                                     self.config(appendable=["CLAUDE.md"]))
        self.assertEqual([["M1-P1-T1"], ["M1-P1-T2"]], held)
        self.assertEqual([["M1-P1-T1", "M1-P1-T2"]], exempted)

    def test_a_family_implied_path_is_counted_as_a_claim(self):
        self.write(pair({"writes": ["drizzle/0001.sql", "tests/unit/a.py"]},
                        {"writes": ["src/b.py", "tests/unit/b.py"]}))
        config = self.config(families=[{"when": "drizzle/**",
                                        "also": ["drizzle/meta/_journal.json"]}])
        held = forecast.claims(execute.units(self.root), config)
        self.assertEqual(["M1-P1-T1"], held["drizzle/meta/_journal.json"])
        self.assertEqual(["M1-P1-T1"], held["drizzle/0001.sql"])

    def test_a_ceiling_the_caller_states_overrides_the_projects(self):
        tasks = [task(1, {"fr": FUNCTIONAL}, writes=["src/a.py", "tests/unit/a.py"]),
                 task(2, {"nfr": TECHNICAL}, writes=["src/b.py", "tests/unit/b.py"]),
                 task(3, {"adr": DECISIONS}, writes=["src/c.py", "tests/unit/c.py"])]
        self.write(tasks)
        self.assertEqual(1, len(forecast.schedule(self.root, self.config())))
        self.assertEqual(3, len(forecast.schedule(self.root, self.config(),
                                                  ceiling=1)))


# ------------------------------------------------------------------- the bounds

class TestTheLoopAlwaysEnds(Plan):

    def test_a_plan_nothing_can_dispatch_terminates_with_no_rounds(self):
        played = self.rounds(pair({"writes": ["src/a.py", "tests/unit/a.py"],
                                   "autonomy": schema.HUMAN_GATE},
                                  {"writes": ["src/b.py", "tests/unit/b.py"],
                                   "autonomy": schema.HUMAN_GATE}))
        self.assertEqual([], played)

    def test_no_plan_ever_takes_more_rounds_than_it_has_units(self):
        tasks = pair({"writes": ["src/a.py", "tests/**"]},
                     {"writes": ["src/b.py", "tests/**"]})
        self.write(tasks)
        played = forecast.schedule(self.root, self.config())
        self.assertLessEqual(len(played), len(execute.units(self.root)))

    def test_the_units_no_round_picked_up_are_named_with_a_reason(self):
        self.write(pair({"writes": ["src/a.py", "tests/unit/a.py"]},
                        {"writes": ["src/b.py", "tests/unit/b.py"],
                         "autonomy": schema.HUMAN_GATE}))
        found = execute.units(self.root)
        played = forecast.schedule(self.root, self.config())
        self.assertEqual([("M1-P1-T2", "at a human gate")],
                         forecast.unscheduled(found, played))


# ------------------------------------------------------- it is never a refusal

class TestItIsAPreviewAndNeverAGate(Plan):

    def out(self, argv):
        held = io.StringIO()
        code = forecast.main(argv, held)
        return code, held.getvalue()

    def test_a_project_with_no_plan_documents_exits_zero_and_says_so(self):
        empty = tempfile.mkdtemp(prefix="z2s-forecast-empty-")
        try:
            code, said = self.out(["--root", empty])
        finally:
            shutil.rmtree(empty, ignore_errors=True)
        self.assertEqual(0, code)
        self.assertIn("no plan documents", said)

    def test_a_wholly_serial_plan_still_exits_zero(self):
        self.write(pair({"writes": ["src/a.py", "tests/**"]},
                        {"writes": ["src/b.py", "tests/**"]}))
        code, said = self.out(["--root", self.root])
        self.assertEqual(0, code)
        self.assertIn("2 rounds", said)
        self.assertIn("tests/**", said)

    def test_the_report_never_states_a_duration(self):
        # LD-3. At plan time there are no durations, and a structural mean
        # quoted back as hours is the one way this number can do harm. The
        # sentence saying so is allowed to use the word; a NUMBER of them is
        # what must never appear, so the check is for a figure and a unit.
        self.write(pair({"writes": ["src/a.py", "tests/unit/a.py"]},
                        {"writes": ["src/b.py", "tests/unit/b.py"]}))
        _, said = self.out(["--root", self.root])
        self.assertIsNone(re.search(r"\d+(\.\d+)?\s*(h\b|hour|min|day|sec)",
                                    said.lower()), said)

    def test_a_project_with_no_workers_is_forecast_against_the_defaults(self):
        self.write(pair({"writes": ["src/a.py", "tests/unit/a.py"]},
                        {"writes": ["src/b.py", "tests/unit/b.py"]}))
        config, note = forecast.configured(self.root)
        self.assertEqual(forecast.UNCONFIGURED["ceiling"], config["ceiling"])
        self.assertIn("workers.json", note)
        _, said = self.out(["--root", self.root])
        self.assertIn("workers.json", said)

    def test_a_nonsense_argument_is_reported_and_still_exits_zero(self):
        code, said = self.out(["--root", self.root, "--ceiling", "banana"])
        self.assertEqual(0, code)
        self.assertIn("whole number", said)


if __name__ == "__main__":       # pragma: no cover
    unittest.main()
