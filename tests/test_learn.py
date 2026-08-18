# -*- coding: utf-8 -*-
"""Compounding memory — what a milestone taught, carried into the next (M12-P1).

The rules under test are the three the milestone states outright: a milestone
cannot close without a retrospective, every later brief has read all of them,
and a theme that keeps coming back stops being advice to the next milestone and
becomes a candidate change to the method itself.

The retrospectives here are written straight onto disk. That is deliberate: the
tool reads a directory of markdown files and nothing else, so a test can seed
the history it needs without driving eleven milestones first.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from z2s import execute, learn, paths, plan, schema, writer         # noqa: E402
from test_execute import Project, script, worker                    # noqa: E402

PACKAGE = os.path.join(os.path.dirname(HERE), "z2s")

#: A builder that does the right thing for every unit but one, and returns
#: nothing at all for that one — so the milestone ends part finished.
SULKS = """\
import json, re, sys
brief = open(sys.argv[1], encoding="utf-8").read()
if "%(unit)s" in brief.split("\\n")[0]:
    raise SystemExit(0)
found = re.search(r"M[0-9]+-P[0-9]+-T[0-9]+", brief)
json.dump({"unit": found.group(0) if found else "?",
           "red": {"command": "python3 -m unittest", "code": 1},
           "commands": [{"command": "python3 -m unittest", "code": 0}],
           "criteria": {}, "changes": [], "denied": [], "decisions": []},
          open(sys.argv[2], "w", encoding="utf-8"))
"""

#: A worker that turns the draft into whatever prose the test hands it.
SCRIBE = """\
import json, sys
open(sys.argv[1], encoding="utf-8").read()
json.dump({"text": "%(text)s"}, open(sys.argv[2], "w", encoding="utf-8"))
"""

#: A retrospective somebody already wrote. A run must not touch it.
KEPT = "# M1 — lessons learned\n\nTags: written-by-hand\n\nIt went well.\n"


def seed(root, milestone, tags=(), body="Nothing surprising.\n"):
    """A retrospective on disk, as if a previous milestone had closed."""
    text = "# %s — lessons learned\n\n%s %s\n\n%s" % (
        milestone, learn.TAG_HEADER, ", ".join(tags), body)
    writer.write(learn.path(root, milestone), text)
    return text


class Sandbox(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-learn-")
        paths.ensure_layout(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)


# ------------------------------------------------------- the close (M12-P1-T1)

class TestAMilestoneCannotCloseWithoutARetrospective(Sandbox):

    def ledger(self, **extra):
        held = execute.blank()
        held["decisions"] = [
            {"unit": "M1-P1-T1", "decision": "Stored the tags in the header",
             "why": "A second file would disagree with the first."}]
        held.update(extra)
        return held

    def test_a_milestone_with_no_retrospective_cannot_close(self):
        """M12-P1-T1-C1"""
        with self.assertRaises(learn.Refused) as caught:
            learn.close(self.root, "M1", self.ledger())
        self.assertIn("retrospective", str(caught.exception))

    def test_a_retrospective_omitting_a_recorded_decision_cannot_close(self):
        """M12-P1-T1-C2 — the decisions have to actually be in it."""
        seed(self.root, "M1", tags=["tags"], body="It went fine.\n")
        with self.assertRaises(learn.Refused) as caught:
            learn.close(self.root, "M1", self.ledger())
        self.assertIn("Stored the tags in the header", str(caught.exception))

    def test_a_retrospective_carrying_the_decisions_closes(self):
        seed(self.root, "M1", tags=["tags"],
             body="Stored the tags in the header, and it held.\n")
        self.assertEqual(learn.path(self.root, "M1"),
                         learn.close(self.root, "M1", self.ledger()))

    def test_a_milestone_with_no_recorded_decisions_still_needs_one(self):
        with self.assertRaises(learn.Refused):
            learn.close(self.root, "M1", execute.blank())

    def test_one_decision_taken_by_three_units_is_named_once(self):
        """Found by driving a real run: three units, one call, one problem."""
        ledger = self.ledger()
        for unit in ("M1-P1-T2", "M1-P1-T3"):
            ledger["decisions"].append(
                {"unit": unit, "decision": "Stored the tags in the header",
                 "why": "Same call, taken again."})
        seed(self.root, "M1", body="It went fine.\n")
        with self.assertRaises(learn.Refused) as caught:
            learn.close(self.root, "M1", ledger)
        said = str(caught.exception)
        self.assertEqual(1, said.count("Stored the tags in the header"))
        self.assertIn("1 decision this run recorded", said)

    def test_only_this_milestones_decisions_are_required(self):
        """A decision taken in M2 is not M1's to account for."""
        ledger = self.ledger()
        ledger["decisions"].append(
            {"unit": "M2-P1-T1", "decision": "Something else entirely", "why": ""})
        seed(self.root, "M1", body="Stored the tags in the header.\n")
        self.assertTrue(learn.close(self.root, "M1", ledger))


class TestTheDraft(Sandbox):

    def entries(self):
        return [{"id": "M1-P1-T1", "title": "Build it", "status": "passing"},
                {"id": "M1-P1-T2", "title": "Break it", "status": "blocked"}]

    def ledger(self):
        held = execute.blank()
        held["decisions"] = [{"unit": "M1-P1-T1", "decision": "Chose the short way",
                              "why": "The long way proved nothing extra."}]
        held["unfinished"] = {"M1-P1-T2": "the unit layer failed"}
        held["gaps"] = {"M1-P1-T2": "the unit layer failed"}
        return held

    def test_the_draft_carries_every_decision_the_milestone_recorded(self):
        text = learn.draft("M1", self.ledger(), self.entries(), "2026-08-15")
        self.assertIn("Chose the short way", text)
        self.assertIn("The long way proved nothing extra.", text)

    def test_the_draft_names_what_did_not_finish(self):
        text = learn.draft("M1", self.ledger(), self.entries(), "2026-08-15")
        self.assertIn("M1-P1-T2", text)
        self.assertIn("the unit layer failed", text)

    def test_the_draft_carries_the_date_it_was_given(self):
        text = learn.draft("M1", self.ledger(), self.entries(), "2026-08-15")
        self.assertIn("2026-08-15", text)

    def test_a_draft_with_no_date_says_so_rather_than_inventing_one(self):
        text = learn.draft("M1", self.ledger(), self.entries(), "")
        self.assertIn("not stated", text)

    def test_the_draft_states_all_three_questions(self):
        text = learn.draft("M1", self.ledger(), self.entries(), "2026-08-15")
        for heading in learn.SECTIONS:
            self.assertIn(heading, text)

    def test_a_drafted_retrospective_closes_the_milestone(self):
        """The seam that matters: what is drafted satisfies what is required."""
        ledger = self.ledger()
        learn.record(self.root, "M1", ledger, "2026-08-15", self.entries())
        self.assertTrue(learn.close(self.root, "M1", ledger))

    def test_two_drafts_of_the_same_facts_are_identical(self):
        """NFR-GEN-01 reaches here too."""
        first = learn.draft("M1", self.ledger(), self.entries(), "2026-08-15")
        second = learn.draft("M1", self.ledger(), self.entries(), "2026-08-15")
        self.assertEqual(first, second)

    def test_a_decision_with_no_words_is_not_written_down_as_one(self):
        """An empty line under a heading is worse than an empty heading."""
        ledger = self.ledger()
        ledger["decisions"].append({"unit": "M1-P1-T1", "decision": "  ",
                                    "why": "Nothing was actually decided."})
        text = learn.draft("M1", ledger, self.entries(), "2026-08-15")
        self.assertNotIn("Nothing was actually decided.", text)
        self.assertEqual(1, len(learn.recorded(ledger, "M1")))

    def test_a_run_with_nothing_to_report_still_carries_a_theme(self):
        """A retrospective with no theme is invisible to every later count."""
        text = learn.draft("M1", execute.blank(), self.entries(), "2026-08-15")
        stated = learn.tags(text)
        self.assertTrue(stated, "a clean run has no theme at all")
        self.assertEqual(stated, learn.tags(text))


# ------------------------------------------------------ the history (M12-P1-T2)

class TestTheHistory(Sandbox):

    def test_retrospectives_are_read_in_milestone_order_not_name_order(self):
        for milestone in ("M2", "M10", "M1"):
            seed(self.root, milestone)
        self.assertEqual(["M1", "M2", "M10"],
                         [one.milestone for one in learn.existing(self.root)])

    def test_prior_means_every_earlier_milestone_and_not_this_one(self):
        for milestone in ("M1", "M2", "M3"):
            seed(self.root, milestone)
        self.assertEqual(["M1", "M2"],
                         [one.milestone for one in learn.prior(self.root, "M3")])

    def test_a_project_with_no_retrospectives_has_no_history(self):
        self.assertEqual([], learn.existing(self.root))

    def test_tags_are_read_from_the_header(self):
        seed(self.root, "M1", tags=["ordering", "concurrency"])
        self.assertEqual(["concurrency", "ordering"],
                         sorted(learn.existing(self.root)[0].tags))

    def test_a_retrospective_with_no_tag_header_has_no_tags(self):
        writer.write(learn.path(self.root, "M1"), "# M1\n\nIt went fine.\n")
        self.assertEqual([], learn.existing(self.root)[0].tags)


class TestTheConventionsSummary(Sandbox):

    def test_the_summary_names_a_theme_more_than_one_milestone_raised(self):
        seed(self.root, "M1", tags=["ordering", "one-off"])
        seed(self.root, "M2", tags=["ordering"])
        summary = " ".join(learn.conventions(self.root))
        self.assertIn("ordering", summary)
        self.assertNotIn("one-off", summary)

    def test_the_summary_says_so_when_there_is_nothing_to_distil(self):
        self.assertTrue(learn.conventions(self.root))


# --------------------------------------------------- the escalation (M12-P1-T3)

class TestRecurringThemesAreEscalated(Sandbox):

    def test_a_theme_in_three_retrospectives_is_surfaced(self):
        """M12-P1-T3-C1"""
        for milestone in ("M1", "M2", "M3"):
            seed(self.root, milestone, tags=["ordering"])
        raised = learn.escalations(self.root)
        self.assertEqual(["ordering"], [one["tag"] for one in raised])
        self.assertEqual(["M1", "M2", "M3"], raised[0]["milestones"])

    def test_a_theme_in_two_retrospectives_is_not_yet_escalated(self):
        for milestone in ("M1", "M2"):
            seed(self.root, milestone, tags=["ordering"])
        self.assertEqual([], learn.escalations(self.root))

    def test_the_same_theme_twice_in_one_retrospective_counts_once(self):
        """Otherwise a single wordy retrospective escalates itself."""
        seed(self.root, "M1", tags=["ordering", "ordering", "ordering"])
        self.assertEqual([], learn.escalations(self.root))

    def test_an_escalation_says_it_is_a_candidate_change_to_the_method(self):
        for milestone in ("M1", "M2", "M3"):
            seed(self.root, milestone, tags=["ordering"])
        self.assertIn("method", learn.format_themes(self.root))


# ------------------------------------------------- the brief (M12-P1-T2 wiring)

class TestEveryBriefHasReadTheHistory(Project):

    def brief_for(self, unit_id="M1-P1-T1"):
        config = execute.settings(self.root)
        unit = execute.units(self.root)[unit_id]
        return execute.brief(self.root, config, unit)

    def test_a_brief_names_every_prior_retrospective(self):
        """M12-P1-T2-C1"""
        self.plan()
        self.configure()
        for milestone in ("M0",):
            seed(self.root, milestone, tags=["ordering"])
        text = self.brief_for()
        self.assertIn("M0-lessons-learned.md", text)

    def test_a_brief_carries_the_conventions_summary(self):
        """M12-P1-T2-C2"""
        self.plan()
        self.configure()
        self.assertIn("Conventions", self.brief_for())

    def test_a_brief_is_missing_no_required_part(self):
        self.plan()
        self.configure()
        self.assertEqual([], execute.check_brief(self.brief_for()))

    def test_the_required_parts_include_the_history(self):
        """The check and the builder read one list, as prompts already do."""
        for part in ("Prior retrospectives", "Conventions"):
            self.assertIn(part, execute.BRIEF_PARTS)

    def test_a_brief_with_no_history_says_so_rather_than_leaving_it_blank(self):
        """A heading with nothing under it is not the same as "there is none"."""
        self.plan()
        self.configure()
        text = self.brief_for()
        self.assertEqual([], execute.check_brief(text))
        block = text.split("Prior retrospectives", 1)[1].split("Conventions")[0]
        self.assertIn("no milestone has closed yet", block)
        self.assertTrue([line for line in block.splitlines()
                         if line.strip().startswith("-")],
                        "the block states nothing at all")


class TestTheRunWritesTheRetrospective(Project):

    def test_a_completed_milestone_leaves_a_retrospective_that_closes_it(self):
        self.plan()
        self.configure()
        ledger = self.drive()
        self.assertTrue(os.path.exists(learn.path(self.root, "M1")))
        self.assertTrue(learn.close(self.root, "M1", ledger))

    def test_the_retrospective_carries_the_decisions_the_run_recorded(self):
        """M12-P1-T1-C2, end to end."""
        self.plan()
        build, _ = self.builder(decisions=json.dumps(
            [{"decision": "Used the shorter form", "why": "It read better."}]))
        judged, _ = self.judge()
        self.configure(workers=[build, judged])
        self.drive()
        with open(learn.path(self.root, "M1"), encoding="utf-8") as handle:
            self.assertIn("Used the shorter form", handle.read())

    def test_an_unfinished_milestone_writes_no_retrospective(self):
        """A milestone that did not close has nothing to look back on yet."""
        self.plan()
        build, _ = self.builder(body="import sys\n")     # returns no report
        judged, _ = self.judge()
        self.configure(workers=[build, judged], attempts=1)
        self.drive()
        self.assertFalse(os.path.exists(learn.path(self.root, "M1")))

    def test_a_milestone_with_one_unfinished_unit_writes_no_retrospective(self):
        """The case that bites: some of it passed, so some of it looks done."""
        self.plan()
        build, _ = self.builder(body=SULKS % {"unit": "M1-P1-T3"})
        judged, _ = self.judge()
        self.configure(workers=[build, judged], attempts=1)
        self.drive()
        states = self.states()
        self.assertEqual(schema.PASSING, states["M1-P1-T1"])
        self.assertNotEqual(schema.PASSING, states["M1-P1-T3"])
        self.assertFalse(os.path.exists(learn.path(self.root, "M1")),
                         "a milestone that did not finish wrote a retrospective")

    def test_an_existing_retrospective_is_never_overwritten(self):
        """It may have been written by hand; this run has no better claim."""
        self.plan()
        self.configure()
        writer.write(learn.path(self.root, "M1"), KEPT)
        self.drive()
        with open(learn.path(self.root, "M1"), encoding="utf-8") as handle:
            self.assertEqual(KEPT, handle.read())


class TestARetrospectiveWorkerMayPolishTheDraft(Project):
    """M12-04: prose is worth having, but not at the price of the record."""

    def retrospective(self, text, name="scribe"):
        body = SCRIBE % {"text": text}
        return worker(name, execute.RETROSPECTIVE,
                      script(self.bin, "%s.py" % name, body))

    def written(self):
        with open(learn.path(self.root, "M1"), encoding="utf-8") as handle:
            return handle.read()

    def test_a_worker_that_keeps_the_record_replaces_the_draft(self):
        self.plan()
        build, _ = self.builder(decisions=json.dumps(
            [{"decision": "Used the shorter form", "why": "It read better."}]))
        judged, _ = self.judge()
        self.configure(workers=[build, judged, self.retrospective(
            "# M1\\n\\nTags: prose\\n\\nUsed the shorter form, and it held.\\n")])
        self.drive()
        self.assertIn("and it held", self.written())

    def test_a_worker_that_drops_the_record_loses_to_the_draft(self):
        self.plan()
        build, _ = self.builder(decisions=json.dumps(
            [{"decision": "Used the shorter form", "why": "It read better."}]))
        judged, _ = self.judge()
        self.configure(workers=[build, judged, self.retrospective(
            "# M1\\n\\nTags: prose\\n\\nIt all went fine.\\n")])
        ledger = self.drive()
        self.assertNotIn("It all went fine", self.written())
        self.assertIn("Used the shorter form", self.written())
        self.assertTrue([one for one in ledger["notes"] if "retrospective" in one],
                        "the rejection was not reported")

    def test_a_project_with_no_such_worker_keeps_the_draft(self):
        self.plan()
        self.configure()
        self.drive()
        self.assertIn("lessons learned", self.written())


# ------------------------------------------------------------------ the guards

class TestTheModuleKeepsTheMethodsRules(unittest.TestCase):

    def source(self):
        with open(os.path.join(PACKAGE, "learn.py"), encoding="utf-8") as handle:
            return handle.read()

    def test_the_module_never_reads_the_clock(self):
        """A retrospective's date is given to it, exactly like every other date."""
        for banned in ("datetime.now", "time.time", "import time", "import random"):
            self.assertNotIn(banned, self.source())

    def test_the_retrospective_location_is_read_from_paths(self):
        self.assertIn("LESSONS_TEMPLATE", self.source())
        self.assertNotIn("lessons-learned.md", self.source().replace(
            "LESSONS_TEMPLATE", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
