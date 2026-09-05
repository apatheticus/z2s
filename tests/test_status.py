# -*- coding: utf-8 -*-
"""Status: the closed vocabulary, the evidence rule, and the write-back tool.

The plan document is the only place progress lives (ADR-05), which makes this
the one tool in the method that edits a finished document. Two failures matter
more than the rest, and most of this file guards them:

  * A status that was never earned. `passing` means the verification layers the
    task names actually ran and passed (NFR-EXE-10), not that somebody typed it.
  * A document damaged by the tool that was meant to record progress in it. A
    write touches the bytes of the embedded specification and nothing else
    (FR-STA-03), and a refusal writes nothing at all.

Traces: FR-STA-01, FR-STA-02, FR-STA-03, FR-STA-04, FR-STA-06, FR-STA-07,
FR-STA-08, FR-PLN-06, FR-EXE-11, NFR-DAT-04, NFR-DAT-05, NFR-EXE-10,
NFR-EXE-11, NFR-GEN-01, ADR-05, ADR-11, US-STA-01, US-STA-02, US-STA-03.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import chain, paths, schema, status, validate

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def criterion(identifier, kind="auto", done=False):
    return {"id": identifier, "kind": kind, "text": "It holds.", "done": done}


def task(identifier="M1-P1-T1", state="not-started", criteria=None,
         layers=("unit",), **extra):
    entry = {"id": identifier, "area": identifier.rsplit("-", 1)[0],
             "title": "A unit of work", "priority": "Must", "autonomy": "auto",
             "status": state, "layer": "schema", "testLayers": list(layers),
             "criteria": criteria if criteria is not None
                         else [criterion(identifier + "-C1")]}
    entry.update(extra)
    return entry


def milestone(tasks=None, identifier="M1"):
    """A milestone document as z2s/plan.py writes one."""
    items = tasks if tasks is not None else [task()]
    phases = sorted({one["area"] for one in items})
    return {
        "schemaVersion": schema.SCHEMA_VERSION,
        "document": {"title": "%s — a milestone" % identifier, "slug": "plan",
                     "type": "Delivery plan", "milestone": identifier,
                     "owner": "The build", "version": "1.0",
                     "status": "Draft for review", "summary": "One milestone."},
        "legend": schema.legend(),
        "catalog": {one["id"]: one["title"] for one in items},
        "sections": [
            {"id": "work", "type": "requirements", "title": "Phases and tasks",
             "areas": [{"key": key, "name": "Phase %s" % key} for key in phases],
             "items": items},
        ],
    }


class Case(unittest.TestCase):
    """A real project directory with a real milestone document in it."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-status-")
        paths.ensure_layout(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def plan(self, spec=None, name="M1-toolchain.html"):
        spec = milestone() if spec is None else spec
        target = paths.resolve(self.root, paths.PLAN_DIR, name)
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(chain.render(spec, "plan-spec", ROOT))
        return target

    def text(self, path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def proved(self, *layers):
        for layer in layers:
            status.record(self.root, layer, "python3 -m unittest", 0)


# ------------------------------------------------------------------ M10-P1-T1

class TestTheStatusVocabulary(unittest.TestCase):
    """M10-P1-T1. FR-STA-01, NFR-DAT-04, ADR-05."""

    def test_the_six_statuses_are_the_documented_set(self):
        self.assertEqual(["not-started", "in-progress", "passing", "failing",
                          "blocked", "needs-review"],
                         [one["id"] for one in schema.ENUMS["statuses"]])

    def test_an_unknown_status_is_rejected(self):
        """M10-P1-T1-C1.

        Rejected AS an unknown word, not as an illegal move: the two are fixed
        differently, and a refusal that says the wrong one sends the reader to
        the transition table looking for a status that was never in it.
        """
        self.assertFalse(status.known("done"))
        with self.assertRaises(status.Refused) as caught:
            status.transition("not-started", "done")
        self.assertIn("done", str(caught.exception))
        self.assertIn("is not a status", str(caught.exception))

    def test_an_illegal_transition_is_rejected(self):
        """M10-P1-T1-C2: the move nobody may make, named in the refusal."""
        with self.assertRaises(status.Refused) as caught:
            status.transition("not-started", "passing")
        self.assertIn("not-started", str(caught.exception))
        self.assertIn("passing", str(caught.exception))

    def test_the_legal_moves_are_the_ones_the_gate_settled_on(self):
        """M10-05, the whole map rather than the one interesting move."""
        for current, wanted in (("not-started", "in-progress"),
                                ("not-started", "blocked"),
                                ("in-progress", "passing"),
                                ("in-progress", "failing"),
                                ("in-progress", "needs-review"),
                                ("failing", "in-progress"),
                                ("blocked", "in-progress"),
                                ("needs-review", "passing"),
                                ("passing", "in-progress")):
            self.assertTrue(status.may_become(current, wanted),
                            "%s -> %s should be legal" % (current, wanted))
        for current, wanted in (("blocked", "passing"), ("failing", "passing"),
                                ("passing", "failing"), ("not-started", "failing")):
            self.assertFalse(status.may_become(current, wanted),
                             "%s -> %s should be refused" % (current, wanted))

    def test_setting_the_status_a_unit_already_carries_is_allowed(self):
        for one in schema.ENUMS["statuses"]:
            self.assertTrue(status.may_become(one["id"], one["id"]))

    def test_every_status_can_be_reached_from_the_starting_one(self):
        """A map with an unreachable state is a map with a typo in it."""
        seen, edge = {"not-started"}, ["not-started"]
        while edge:
            current = edge.pop()
            for wanted in schema.TRANSITIONS[current]:
                if wanted not in seen:
                    seen.add(wanted)
                    edge.append(wanted)
        self.assertEqual({one["id"] for one in schema.ENUMS["statuses"]}, seen)

    def test_the_map_names_only_statuses_that_exist(self):
        known = {one["id"] for one in schema.ENUMS["statuses"]}
        self.assertEqual(known, set(schema.TRANSITIONS))
        for current, wanted in schema.TRANSITIONS.items():
            self.assertEqual([], [one for one in wanted if one not in known],
                             "%s moves to something that is not a status" % current)


class TestHumanReviewBlocksTheMilestone(Case):
    """M10-P1-T1-C3. FR-PLN-06: it blocks the milestone, not the task."""

    def spec(self):
        return milestone([task(criteria=[criterion("M1-P1-T1-C1", done=True),
                                         criterion("M1-P1-T1-C2", "human-review")],
                              state="in-progress")])

    def test_a_task_may_pass_with_an_open_human_review_criterion(self):
        path = self.plan(self.spec())
        self.proved("unit")
        status.set_status(self.root, "M1-P1-T1", "passing")
        _, spec = status.read(path)
        self.assertEqual("passing", status.find(spec, "M1-P1-T1")["status"])

    def test_the_milestone_does_not_close_while_one_is_open(self):
        path = self.plan(self.spec())
        self.proved("unit")
        status.set_status(self.root, "M1-P1-T1", "passing")
        _, spec = status.read(path)
        self.assertEqual("needs-review", status.rollup(spec)["state"])

    def test_the_milestone_closes_once_it_is_signed_off(self):
        path = self.plan(self.spec())
        self.proved("unit")
        status.set_status(self.root, "M1-P1-T1", "passing")
        status.tick(self.root, "M1-P1-T1", ["M1-P1-T1-C2"])
        _, spec = status.read(path)
        self.assertEqual("passing", status.rollup(spec)["state"])


class TestTheLegendAndTheRuleAreOneDeclaration(unittest.TestCase):
    """M10-P1-T1's refactor step: the reader's table IS the enforced table."""

    def test_the_plan_states_the_moves_the_status_command_enforces(self):
        from z2s import plan
        rows = {row[0]: row[2] for row in plan.status_rows()}
        self.assertEqual({"Not started", "In progress", "Passing", "Failing",
                          "Blocked", "Needs review"}, set(rows))
        self.assertIn("In progress", rows["Not started"])
        self.assertNotIn("Passing", rows["Not started"])
        self.assertIn("Passing", rows["Needs review"])


# ------------------------------------------------------------------ M10-P1-T2

class TestStatusOnlyAfterVerificationRan(Case):
    """M10-P1-T2. NFR-EXE-10: proved in this run, not asserted."""

    def test_setting_passing_without_a_record_is_refused(self):
        """M10-P1-T2-C1."""
        path = self.plan(milestone([task(state="in-progress")]))
        before = self.text(path)
        with self.assertRaises(status.Refused) as caught:
            status.set_status(self.root, "M1-P1-T1", "passing")
        self.assertIn("unit", str(caught.exception))
        self.assertEqual(before, self.text(path))

    def test_a_failed_verification_is_not_evidence(self):
        self.plan(milestone([task(state="in-progress")]))
        status.record(self.root, "unit", "python3 -m unittest", 1)
        with self.assertRaises(status.Refused):
            status.set_status(self.root, "M1-P1-T1", "passing")

    def test_a_record_for_another_layer_does_not_cover_this_one(self):
        self.plan(milestone([task(state="in-progress", layers=("unit", "e2e"))]))
        self.proved("unit")
        with self.assertRaises(status.Refused) as caught:
            status.set_status(self.root, "M1-P1-T1", "passing")
        self.assertIn("e2e", str(caught.exception))

    def test_the_record_names_the_command_that_produced_the_result(self):
        """M10-P1-T2-C2."""
        status.record(self.root, "unit", "python3 -m unittest discover -s tests", 0)
        held = status.evidence(self.root)
        self.assertEqual("python3 -m unittest discover -s tests",
                         held["unit"]["command"])
        self.assertTrue(held["unit"]["passed"])

    def test_running_a_check_records_what_actually_happened(self):
        """The checker writes the evidence; nobody is taken at their word."""
        code = status.ran(self.root, "unit", [sys.executable, "-c", "raise SystemExit(0)"])
        self.assertEqual(0, code)
        self.assertTrue(status.evidence(self.root)["unit"]["passed"])

        code = status.ran(self.root, "unit", [sys.executable, "-c", "raise SystemExit(3)"])
        self.assertEqual(3, code)
        self.assertFalse(status.evidence(self.root)["unit"]["passed"])

    def test_a_check_that_never_finishes_is_stopped_and_proves_nothing(self):
        """E-03: a suite that hangs stops a run exactly as a hung worker does.

        Nothing is recorded. A check that was interrupted was not watched
        failing, and writing it down as a failure would be inventing a result.
        """
        with self.assertRaises(status.Refused) as raised:
            status.ran(self.root, "unit",
                       [sys.executable, "-c", "import time; time.sleep(600)"], 2)
        self.assertIn("did not finish within", str(raised.exception))
        self.assertEqual(status.evidence(self.root).get("unit"), None)

    def test_what_a_check_printed_is_kept_where_the_run_can_read_it(self):
        """FR-EXE-20 amended. The record here is an exit status and a sentence,
        which says that something failed and never what it named — and the run
        has a question only the output answers: whether the files a red
        implicates are files this unit was ever allowed to touch."""
        log = os.path.join(self.root, "logs", "unit.log")
        code = status.ran(self.root, "unit",
                          [sys.executable, "-c",
                           "import sys; sys.stdout.write('src/two.py:1 broken')"],
                          None, log)
        self.assertEqual(0, code)
        with open(log, encoding="utf-8") as handle:
            self.assertIn("src/two.py", handle.read())

    def test_a_check_given_no_log_still_runs(self):
        """Every existing caller passes four arguments or fewer."""
        self.assertEqual(
            0, status.ran(self.root, "unit",
                          [sys.executable, "-c", "raise SystemExit(0)"], None))

    def test_a_check_given_no_bound_still_runs(self):
        self.assertEqual(
            0, status.ran(self.root, "unit",
                          [sys.executable, "-c", "raise SystemExit(0)"], None))

    def test_a_prohibited_command_is_never_run(self):
        with self.assertRaises(status.Refused):
            status.ran(self.root, "unit", ["git", "push", "--force"])

    def test_the_record_is_transient_state_outside_version_control(self):
        """NFR-OPS-04: evidence is about a run, not about the project."""
        self.proved("unit")
        self.assertTrue(os.path.exists(paths.resolve(self.root, status.RECORD)))
        self.assertTrue(status.RECORD.startswith(paths.LEDGER_DIR))

    def test_clearing_leaves_no_evidence_behind(self):
        self.proved("unit")
        status.clear(self.root)
        self.assertEqual({}, status.evidence(self.root))

    def test_a_status_that_is_not_passing_needs_no_evidence(self):
        """Only `passing` is a claim about verification (NFR-EXE-10)."""
        self.plan()
        status.set_status(self.root, "M1-P1-T1", "in-progress")
        status.set_status(self.root, "M1-P1-T1", "failing")
        _, spec = status.read(paths.resolve(self.root, paths.PLAN_DIR,
                                            "M1-toolchain.html"))
        self.assertEqual("failing", status.find(spec, "M1-P1-T1")["status"])


# ------------------------------------------------------------------ M10-P2-T1

class TestTheWriteTouchesNothingElse(Case):
    """M10-P2-T1. FR-STA-03, NFR-GEN-01, ADR-02."""

    def test_only_bytes_inside_the_specification_block_change(self):
        """M10-P2-T1-C1."""
        path = self.plan()
        before = self.text(path)
        status.set_status(self.root, "M1-P1-T1", "in-progress")
        after = self.text(path)
        self.assertNotEqual(before, after)

        opening = validate.BLOCK.search(before)
        closing = validate.BLOCK.search(after)
        self.assertEqual(before[:opening.start(1)], after[:closing.start(1)])
        self.assertEqual(before[opening.end(1):], after[closing.end(1):])

    def test_key_order_is_stable_across_writes(self):
        """M10-P2-T1-C2: a diff shows the change and nothing else."""
        path = self.plan()
        status.set_status(self.root, "M1-P1-T1", "in-progress")
        once = self.text(path)
        status.set_status(self.root, "M1-P1-T1", "blocked")
        twice = self.text(path)
        self.assertEqual(1, len([line for line in _diff(once, twice)]),
                         "one changed line, or the diff is unreadable (ADR-11)")

    def test_a_written_document_is_what_regeneration_would_produce(self):
        """The tool edits in place, but the result is not a fork of the format:
        rendering the same specification has to produce the same bytes."""
        path = self.plan()
        status.set_status(self.root, "M1-P1-T1", "in-progress")
        held = self.text(path)
        _, spec = status.read(path)
        self.assertEqual(held, chain.render(spec, "plan-spec", ROOT))

    def test_a_file_changed_underneath_the_tool_is_not_overwritten(self):
        """LD-03: one writer per run, plus a guard for the stray hand edit."""
        path = self.plan()
        html, spec = status.read(path)
        status.apply(spec, "M1-P1-T1", "in-progress")
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("<!-- somebody was here -->")
        meddled = self.text(path)
        with self.assertRaises(status.Refused):
            status.rewrite(path, html, spec)
        self.assertEqual(meddled, self.text(path))

    def test_a_document_of_another_schema_version_is_refused(self):
        """LD-08: the writer is stricter than the readers."""
        spec = milestone()
        spec["schemaVersion"] = "2.0"
        path = self.plan(spec)
        before = self.text(path)
        with self.assertRaises(status.Refused) as caught:
            status.set_status(self.root, "M1-P1-T1", "in-progress")
        self.assertIn("2.0", str(caught.exception))
        self.assertEqual(before, self.text(path))


# ------------------------------------------------------------------ M10-P2-T2

class TestInvalidInputWritesNothing(Case):
    """M10-P2-T2. FR-STA-03, NFR-DAT-04."""

    def test_an_unknown_identifier_leaves_the_file_unchanged(self):
        """M10-P2-T2-C1."""
        path = self.plan()
        before = self.text(path)
        with self.assertRaises(status.Refused) as caught:
            status.set_status(self.root, "M9-P9-T9", "in-progress")
        self.assertIn("M9-P9-T9", str(caught.exception))
        self.assertEqual(before, self.text(path))

    def test_an_invalid_status_leaves_the_file_unchanged(self):
        """M10-P2-T2-C2."""
        path = self.plan()
        before = self.text(path)
        with self.assertRaises(status.Refused):
            status.set_status(self.root, "M1-P1-T1", "nearly-done")
        self.assertEqual(before, self.text(path))

    def test_an_unknown_criterion_leaves_the_file_unchanged(self):
        path = self.plan()
        before = self.text(path)
        with self.assertRaises(status.Refused) as caught:
            status.tick(self.root, "M1-P1-T1", ["M1-P1-T1-C9"])
        self.assertIn("M1-P1-T1-C9", str(caught.exception))
        self.assertEqual(before, self.text(path))

    def test_the_change_itself_refuses_a_unit_that_is_not_there(self):
        """Guarded where the change is made, not only where the file is found:
        a caller holding a specification can reach these directly, and an
        unknown unit has to be a refusal rather than a silent nothing."""
        spec = milestone()
        with self.assertRaises(status.Refused) as caught:
            status.apply(spec, "M9-P9-T9", "in-progress")
        self.assertIn("M9-P9-T9", str(caught.exception))
        with self.assertRaises(status.Refused):
            status.mark(spec, "M9-P9-T9")

    def test_the_enumeration_is_the_schema_s_and_not_a_second_copy(self):
        """The refactor line: share the enumeration rather than restate it."""
        with open(os.path.join(ROOT, "z2s", "status.py"), encoding="utf-8") as handle:
            source = handle.read()
        for one in schema.ENUMS["statuses"]:
            self.assertNotIn('"%s"' % one["id"], source,
                             "the status vocabulary is declared in schema.py")


# ------------------------------------------------------------------ M10-P2-T3

class TestTickingAndReporting(Case):
    """M10-P2-T3. FR-STA-06, FR-STA-07."""

    def spec(self):
        return milestone([
            task("M1-P1-T1", "in-progress",
                 [criterion("M1-P1-T1-C1"), criterion("M1-P1-T1-C2", "human-review")]),
            task("M1-P2-T1", "not-started", [criterion("M1-P2-T1-C1")]),
        ])

    def test_ticking_all_machine_criteria_leaves_human_review_untouched(self):
        """M10-P2-T3-C1."""
        path = self.plan(self.spec())
        status.tick(self.root, "M1-P1-T1")
        _, spec = status.read(path)
        marks = {one["id"]: one["done"]
                 for one in status.find(spec, "M1-P1-T1")["criteria"]}
        self.assertTrue(marks["M1-P1-T1-C1"])
        self.assertFalse(marks["M1-P1-T1-C2"])

    def test_a_named_human_review_criterion_can_be_signed_off(self):
        path = self.plan(self.spec())
        status.tick(self.root, "M1-P1-T1", ["M1-P1-T1-C2"])
        _, spec = status.read(path)
        marks = {one["id"]: one["done"]
                 for one in status.find(spec, "M1-P1-T1")["criteria"]}
        self.assertTrue(marks["M1-P1-T1-C2"])
        self.assertFalse(marks["M1-P1-T1-C1"])

    def test_the_report_prints_counts_per_phase_and_milestone(self):
        """M10-P2-T3-C2, and without opening a browser (FR-STA-06)."""
        self.plan(self.spec())
        out = io.StringIO()
        self.assertEqual(0, status.main(["report", "--root", self.root], out=out))
        text = out.getvalue()
        self.assertIn("M1-P1", text)
        self.assertIn("M1-P2", text)
        self.assertIn("M1", text)
        self.assertIn("in progress", text.lower())

    def test_the_report_reads_every_milestone_document(self):
        self.plan(self.spec())
        self.plan(milestone([task("M2-P1-T1")], identifier="M2"), "M2-later.html")
        out = io.StringIO()
        status.main(["report", "--root", self.root], out=out)
        self.assertIn("M2-P1", out.getvalue())


# ------------------------------------------------------------------ M10-P3-T1

class TestRollupsAreDerived(Case):
    """M10-P3-T1. FR-STA-04, NFR-DAT-05."""

    def spec(self):
        return milestone([task("M1-P1-T1", "passing", [criterion("M1-P1-T1-C1", done=True)]),
                          task("M1-P1-T2", "in-progress"),
                          task("M1-P2-T1", "not-started")])

    def test_a_task_status_change_updates_every_rollup(self):
        """M10-P3-T1-C1."""
        path = self.plan(self.spec())
        _, spec = status.read(path)
        before = status.rollup(spec)
        self.assertEqual(1, before["counts"]["passing"])
        self.assertEqual(1, before["phases"]["M1-P1"]["counts"]["passing"])

        status.set_status(self.root, "M1-P1-T2", "blocked")
        _, spec = status.read(path)
        after = status.rollup(spec)
        self.assertEqual(1, after["counts"]["blocked"])
        self.assertEqual(0, after["counts"]["in-progress"])
        self.assertEqual(1, after["phases"]["M1-P1"]["counts"]["blocked"])
        self.assertEqual("blocked", after["state"])

    def test_no_aggregate_is_stored_in_the_specification(self):
        """M10-P3-T1-C2: a stored total is a total that can disagree."""
        path = self.plan(self.spec())
        status.set_status(self.root, "M1-P1-T2", "blocked")
        _, spec = status.read(path)
        for key in ("counts", "rollup", "progress", "state", "totals"):
            self.assertEqual([], list(_findall(spec, key)),
                             "%s must be derived, never stored" % key)

    def test_a_milestone_with_every_task_passing_is_passing(self):
        path = self.plan(milestone([task("M1-P1-T1", "passing",
                                         [criterion("M1-P1-T1-C1", done=True)])]))
        _, spec = status.read(path)
        self.assertEqual("passing", status.rollup(spec)["state"])

    def test_an_untouched_milestone_has_not_started(self):
        path = self.plan(milestone([task("M1-P1-T1", "not-started")]))
        _, spec = status.read(path)
        self.assertEqual("not-started", status.rollup(spec)["state"])


# ------------------------------------------------------------------ M10-P3-T2

class TestTheHumanReviewQueue(Case):
    """M10-P3-T2. FR-STA-08."""

    def spec(self):
        return milestone([
            task("M1-P1-T1", "passing",
                 [criterion("M1-P1-T1-C1", done=True),
                  criterion("M1-P1-T1-C2", "human-review"),
                  criterion("M1-P1-T1-C3", "human-review", done=True)]),
            task("M1-P2-T1", "in-progress", [criterion("M1-P2-T1-C1")]),
        ])

    def test_the_queue_lists_exactly_the_outstanding_items(self):
        """M10-P3-T2-C1: not the done ones, not the machine ones."""
        path = self.plan(self.spec())
        _, spec = status.read(path)
        self.assertEqual(["M1-P1-T1-C2"],
                         [one["id"] for one in status.review(spec)])

    def test_the_queue_empties_as_items_are_signed_off(self):
        path = self.plan(self.spec())
        status.tick(self.root, "M1-P1-T1", ["M1-P1-T1-C2"])
        _, spec = status.read(path)
        self.assertEqual([], status.review(spec))

    def test_each_entry_names_the_task_it_belongs_to(self):
        path = self.plan(self.spec())
        _, spec = status.read(path)
        self.assertEqual("M1-P1-T1", status.review(spec)[0]["unit"])

    def test_the_command_lists_the_queue_across_every_milestone(self):
        self.plan(self.spec())
        self.plan(milestone([task("M2-P1-T1", "in-progress",
                                  [criterion("M2-P1-T1-C1", "human-review")])],
                            identifier="M2"), "M2-later.html")
        out = io.StringIO()
        self.assertEqual(0, status.main(["review", "--root", self.root], out=out))
        text = out.getvalue()
        self.assertIn("M1-P1-T1-C2", text)
        self.assertIn("M2-P1-T1-C1", text)
        self.assertNotIn("M1-P1-T1-C3", text)


# ------------------------------------------------------------------ M10-P3-T3

class TestOneCommitPerUnit(Case):
    """M10-P3-T3. FR-EXE-11, NFR-EXE-11, ADR-11."""

    def setUp(self):
        Case.setUp(self)
        self.git("init", "-q")
        self.git("config", "user.email", "build@example.test")
        self.git("config", "user.name", "The build")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *arguments):
        return subprocess.run(("git", "-C", self.root) + arguments,
                              capture_output=True, text=True, check=False)

    def work(self, name="z2s/thing.py"):
        target = os.path.join(self.root, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("# the work\n")
        return name

    def test_one_commit_contains_the_work_and_the_status_change(self):
        """M10-P3-T3-C1."""
        self.plan()
        made = self.work()
        self.proved("unit")
        status.set_status(self.root, "M1-P1-T1", "in-progress")
        status.commit(self.root, "M1-P1-T1", [made])
        listed = self.git("show", "--name-only", "--pretty=format:", "HEAD").stdout
        self.assertIn(made, listed)
        self.assertIn(".zero/plan/M1-toolchain.html", listed)

    def test_the_commit_message_names_the_unit_identifier(self):
        """M10-P3-T3-C2."""
        self.plan()
        status.commit(self.root, "M1-P1-T1", [self.work()])
        subject = self.git("log", "-1", "--pretty=%s").stdout.strip()
        self.assertTrue(subject.startswith("M1-P1-T1"), subject)
        self.assertIn("A unit of work", subject)

    def test_a_path_outside_the_project_is_refused(self):
        """Refused for being outside the area, and refused before git is asked:
        a run that has to be rescued by git noticing has already tried."""
        self.plan()
        with self.assertRaises(status.Refused) as caught:
            status.commit(self.root, "M1-P1-T1", ["../elsewhere/thing.py"])
        self.assertIn("owns its own area", str(caught.exception))
        self.assertEqual("", self.git("log", "--oneline").stdout.strip())

    def test_nothing_is_ever_pushed(self):
        """The standing rule: publishing is the operator's decision, always."""
        with open(os.path.join(ROOT, "z2s", "status.py"), encoding="utf-8") as handle:
            source = handle.read()
        self.assertNotIn("push", source)

    def test_an_unknown_unit_is_refused_before_git_is_touched(self):
        self.plan()
        with self.assertRaises(status.Refused):
            status.commit(self.root, "M9-P9-T9", [self.work()])
        self.assertEqual("", self.git("log", "--oneline").stdout.strip())


# ---------------------------------------------------------------- the command

class TestTheCommand(Case):
    """One entry point, and it says what it did (FR-GEN-03)."""

    def test_it_explains_itself_when_given_nothing(self):
        self.assertEqual(2, status.main([], out=io.StringIO()))

    def test_setting_a_status_reports_the_move_it_made(self):
        self.plan()
        out = io.StringIO()
        code = status.main(["set", "M1-P1-T1", "in-progress", "--root", self.root],
                           out=out)
        self.assertEqual(0, code)
        self.assertIn("M1-P1-T1", out.getvalue())
        self.assertIn("in-progress", out.getvalue())

    def test_a_refusal_exits_non_zero_and_says_why(self):
        self.plan()
        out = io.StringIO()
        code = status.main(["set", "M1-P1-T1", "passing", "--root", self.root], out=out)
        self.assertEqual(1, code)
        self.assertIn("unit", out.getvalue())


# --------------------------------------------------------- in a real browser

HARNESS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "status_harness.js")
NODE = shutil.which("node")


def drive(pages):
    """One browser run over the documents given. (report, reason)."""
    if NODE is None:
        return None, "node is not installed"
    request = {"op": "status", "pages": pages, "documents": sorted(pages)}
    finished = subprocess.run([NODE, HARNESS], input=json.dumps(request),
                              capture_output=True, text=True)
    if finished.returncode == 3:
        return None, finished.stderr.strip()
    if finished.returncode != 0:
        raise AssertionError("status harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout)["documents"], None


def _browser_fixture():
    """Build one milestone, look at it, change one status, look again.

    The pair is the point. A single look cannot tell a figure that was computed
    from a figure that was stored, because both render the same the first time
    (M10-P3-T1-C1).
    """
    root = tempfile.mkdtemp(prefix="z2s-status-browser-")
    try:
        paths.ensure_layout(root)
        spec = milestone([
            task("M1-P1-T1", "passing",
                 [criterion("M1-P1-T1-C1", done=True),
                  criterion("M1-P1-T1-C2", "human-review")]),
            task("M1-P1-T2", "in-progress"),
            task("M1-P2-T1", "not-started"),
        ])
        target = paths.resolve(root, paths.PLAN_DIR, "M1-toolchain.html")
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(chain.render(spec, "plan-spec", ROOT))

        def page():
            with open(target, encoding="utf-8") as handle:
                return handle.read()

        before, reason = drive({"M1-toolchain.html": page()})
        if before is None:
            return None, reason

        status.set_status(root, "M1-P1-T2", "blocked")
        status.tick(root, "M1-P1-T1", ["M1-P1-T1-C2"])
        after, reason = drive({"M1-toolchain.html": page()})
        if after is None:
            return None, reason
        return {"before": before[0], "after": after[0]}, None
    finally:
        shutil.rmtree(root, ignore_errors=True)


#: See the same note in `test_plan.py`: a harness that ran and went wrong is not
#: a browser that was not there, and only the second is a legitimate skip.
BROKEN = None
try:
    SEEN, REASON = _browser_fixture()
except Exception as error:             # pragma: no cover - reported, never hidden
    SEEN, REASON, BROKEN = None, "the fixture could not be built: %s" % error, error


@unittest.skipIf(SEEN is None and BROKEN is None, "no browser available: %s" % REASON)
class TestProgressInABrowser(unittest.TestCase):
    """M10-P3-T1, M10-P3-T2. The half no reading of the data can answer."""

    @classmethod
    def setUpClass(cls):
        if BROKEN is not None:         # pragma: no cover - only on a real break
            raise AssertionError(
                "the browser harness failed rather than being absent; a check "
                "that could not run is not a check that passed:\n%s" % REASON)
        cls.before = SEEN["before"]
        cls.after = SEEN["after"]

    def test_the_runtime_renders_without_throwing(self):
        self.assertEqual([], self.before["errors"])
        self.assertEqual([], self.after["errors"])

    def test_the_reader_sees_a_figure_for_the_milestone_and_each_phase(self):
        """FR-STA-04: the rollup is displayed, not merely computable."""
        for name in ("work", "M1-P1", "M1-P2"):
            self.assertIn(name, self.before["rollups"])
        self.assertIn("3 tasks", self.before["rollups"]["work"])
        self.assertIn("1 passing", self.before["rollups"]["work"])

    def test_a_status_change_updates_every_rollup(self):
        """M10-P3-T1-C1, seen in the browser rather than in the data."""
        self.assertIn("1 in progress", self.before["rollups"]["work"])
        self.assertNotIn("in progress", self.after["rollups"]["work"])
        self.assertIn("1 blocked", self.after["rollups"]["work"])
        self.assertIn("1 blocked", self.after["rollups"]["M1-P1"])
        self.assertEqual(self.before["rollups"]["M1-P2"],
                         self.after["rollups"]["M1-P2"])

    def test_the_bar_shows_how_much_is_finished(self):
        self.assertEqual("33%", self.before["fills"]["work"])

    def test_the_queue_lists_what_is_waiting_on_a_person(self):
        """M10-P3-T2-C1, and each entry leads to the criterion it names."""
        self.assertTrue(self.before["queueShown"])
        self.assertEqual(["M1-P1-T1-C2"], self.before["queue"])
        self.assertEqual(["#M1-P1-T1-C2"], self.before["targets"])

    def test_the_queue_disappears_once_it_is_empty(self):
        self.assertFalse(self.after["queueShown"])
        self.assertEqual([], self.after["queue"])

    def test_the_catalogue_still_renders_every_task(self):
        """The rollup is added beside the entries, never instead of them."""
        self.assertEqual(3, self.before["entries"])
        self.assertEqual(3, self.after["entries"])


RENDER_HARNESS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "render_harness.js")


def rendered(request):
    """One question put to the runtime with no browser involved."""
    finished = subprocess.run([NODE, RENDER_HARNESS], input=json.dumps(request),
                              capture_output=True, text=True)
    if finished.returncode != 0:
        raise AssertionError("runtime harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout)


@unittest.skipIf(NODE is None, "node is not installed")
class TestTheRenderedRollupIsAboutStatus(unittest.TestCase):
    """A catalogue with no status is not a catalogue with no progress: it is a
    catalogue progress is not a question about (requirements, decisions, use
    cases). Showing one a bar would be inventing a figure."""

    def rollup(self, items):
        return rendered({"op": "rollup", "items": items})

    def test_entries_that_carry_no_status_produce_no_figure(self):
        seen = self.rollup([{"id": "FR-DOC-01", "title": "One"},
                            {"id": "FR-DOC-02", "title": "Two"}])
        self.assertEqual(0, seen["counts"]["total"])
        self.assertEqual("", seen["rendered"])

    def test_units_of_work_produce_one(self):
        seen = self.rollup([{"id": "M1-P1-T1", "status": "passing"},
                            {"id": "M1-P1-T2", "status": "not-started"}])
        self.assertEqual(2, seen["counts"]["total"])
        self.assertIn("2 tasks", seen["rendered"])
        self.assertIn("50%", seen["rendered"])

    def test_a_mixed_catalogue_counts_only_what_carries_a_status(self):
        seen = self.rollup([{"id": "M1-P1-T1", "status": "passing"},
                            {"id": "UC-01", "title": "Not a unit of work"}])
        self.assertEqual(1, seen["counts"]["total"])
        self.assertIn("1 task ", seen["rendered"])

    def test_an_empty_queue_renders_nothing_at_all(self):
        seen = self.rollup([{"id": "M1-P1-T1", "status": "passing", "criteria": [
            {"id": "M1-P1-T1-C1", "kind": "human-review", "done": True}]}])
        self.assertEqual([], seen["outstanding"])
        self.assertEqual("", seen["queue"])


# ------------------------------------------------------------------- helpers

def _diff(before, after):
    """The lines that differ, positionally — enough to prove a diff stays small."""
    first, second = before.splitlines(), after.splitlines()
    return [pair for pair in zip(first, second) if pair[0] != pair[1]]


def _findall(node, key):
    """Every occurrence of a key anywhere in a specification."""
    if isinstance(node, dict):
        for name, value in node.items():
            if name == key:
                yield value
            for found in _findall(value, key):
                yield found
    elif isinstance(node, list):
        for value in node:
            for found in _findall(value, key):
                yield found


if __name__ == "__main__":
    unittest.main()
