# -*- coding: utf-8 -*-
"""A plan you can navigate: the split, and the way back from any part of it.

The published plan used to be one file for fourteen milestones, and said so in
writing: "the method prescribes one document per milestone, and this renders all
thirteen in a single file … in a working project, split it." These are the
assertions that make that confession untrue rather than merely deleted.

Two properties matter and are easy to lose. A plan split across files must not
declare the same identifier twice — the index has to list milestones as rows
rather than repeat the entries its pages carry. And a reader who arrives on one
part must be able to reach every other part and get back, or the split has
traded one unreadable file for fourteen unreachable ones.

Traces: FR-SPC-09, FR-SPC-10, FR-EXE-15.
"""

import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, "docs", "_build")
DOCS = os.path.join(ROOT, "docs")
sys.path.insert(0, ROOT)
sys.path.insert(0, BUILD)

import generate                                                   # noqa: E402
from specs import plan_spine                                      # noqa: E402
from z2s import schema                                            # noqa: E402

PAGES = generate.build_plan()


def declared(spec):
    """Every identifier this specification declares."""
    return sorted(entry["id"] for _, entry in schema.entries(spec)
                  if isinstance(entry.get("id"), str) and schema.kind_of(entry["id"]))


class TestThePlanIsWrittenAcrossOnePagePerMilestone(unittest.TestCase):

    def test_the_index_keeps_its_name_and_every_milestone_gets_its_own_file(self):
        names = [name for name, _, _ in PAGES]
        self.assertEqual("Z2S-Plan.html", names[0], "inbound links point at this name")
        self.assertEqual(["Z2S-Plan-%s.html" % m["id"] for m in plan_spine.MILESTONES],
                         names[1:])

    def test_every_page_is_the_same_document(self):
        """One document, split for reading — not fifteen documents."""
        for name, _, spec in PAGES:
            self.assertEqual("plan", spec["document"]["slug"], name)
            self.assertIn("catalog", spec, name)

    def test_a_milestone_page_names_the_milestone_it_carries(self):
        for (name, _, spec), m in zip(PAGES[1:], plan_spine.MILESTONES):
            self.assertEqual(m["id"], spec["document"]["milestone"], name)
            self.assertIn(m["id"], spec["document"]["title"], name)


class TestNothingIsDeclaredTwice(unittest.TestCase):
    """The trap the split sets, and the reason the index lists rows.

    An index that repeated the milestone, phase and task entries its pages carry
    would declare every one of them a second time. The validator reports that as
    a duplicate identifier — correctly — so it is a build failure, not a
    cosmetic choice.
    """

    def test_the_index_declares_no_plan_identifier_at_all(self):
        self.assertEqual([], [one for one in declared(PAGES[0][2])
                              if schema.kind_of(one) == "plan"])

    def test_the_index_lists_milestones_as_rows(self):
        section = next(s for s in PAGES[0][2]["sections"] if s["id"] == "milestones")
        self.assertEqual("table", section["type"])
        self.assertEqual(len(plan_spine.MILESTONES), len(section["rows"]))

    def test_a_milestone_page_declares_its_own_milestone_and_no_other(self):
        for (name, _, spec), m in zip(PAGES[1:], plan_spine.MILESTONES):
            milestones = [one for one in declared(spec)
                          if schema.plan_level(one) == "milestone"]
            self.assertEqual([m["id"]], milestones, name)

    def test_every_task_in_the_plan_is_declared_exactly_once_across_the_set(self):
        seen = {}
        for name, _, spec in PAGES:
            for one in declared(spec):
                seen.setdefault(one, []).append(name)
        twice = {one: where for one, where in seen.items() if len(where) > 1}
        self.assertEqual({}, twice)
        self.assertGreater(len([one for one in seen if schema.plan_level(one) == "task"]),
                           100, "the split lost most of the plan")


class TestEveryPartCanReachEveryOther(unittest.TestCase):
    """FR-SPC-09. A reader who arrives on one page is not stranded there."""

    def test_the_index_lists_itself_as_current_and_links_every_milestone(self):
        parts = PAGES[0][2]["parts"]
        self.assertTrue(parts[0]["current"])
        self.assertEqual(generate.FILES["plan"], parts[0]["href"])
        self.assertEqual([m["id"] for m in plan_spine.MILESTONES],
                         [one["label"] for one in parts[1:]])
        self.assertEqual([], [one for one in parts[1:] if one["current"]])

    def test_a_milestone_page_marks_itself_and_links_the_index_and_the_rest(self):
        for (name, _, spec), m in zip(PAGES[1:], plan_spine.MILESTONES):
            parts = spec["parts"]
            current = [one for one in parts if one["current"]]
            self.assertEqual([m["id"]], [one["label"] for one in current], name)
            self.assertEqual(len(plan_spine.MILESTONES) + 1, len(parts), name)
            self.assertEqual(generate.FILES["plan"], parts[0]["href"], name)

    def test_the_document_set_navigation_is_untouched(self):
        """`parts` is a second list, not a widened first one.

        Putting fourteen milestones into the document-set navigation would put
        them into every other document's rail too, where they mean nothing.
        """
        for name, _, spec in PAGES:
            self.assertEqual([label for _, label in generate.NAV],
                             [one["label"] for one in spec["siblings"]], name)

    def test_a_plan_identifier_at_any_level_routes_to_the_page_that_carries_it(self):
        links = PAGES[0][2]["links"]
        for m in plan_spine.MILESTONES:
            self.assertEqual("Z2S-Plan-%s.html" % m["id"], links[m["id"]])
        # Deeper identifiers are routed by the runtime's one-segment fallback,
        # which is why no phase or task needs an entry of its own.
        self.assertNotIn("M1-P1", links)


class TestTheIndexSchedulesNothingNobodyCanRead(unittest.TestCase):

    def test_every_scheduled_milestone_names_its_detail_document(self):
        section = next(s for s in PAGES[0][2]["sections"] if s["type"] == "waves")
        scheduled = [one for wave in section["waves"] for one in wave]
        self.assertEqual(sorted(m["id"] for m in plan_spine.MILESTONES), sorted(scheduled))
        for one in scheduled:
            self.assertIn(one, section["files"], "%s is scheduled and names no document" % one)

    def test_each_named_document_is_one_the_run_writes(self):
        section = next(s for s in PAGES[0][2]["sections"] if s["type"] == "waves")
        written = {name for name, _, _ in PAGES}
        for unit, filename in section["files"].items():
            self.assertIn(filename, written, "%s names a file nothing writes" % unit)


class TestTheApologyIsGoneBecauseTheReasonIsGone(unittest.TestCase):

    def test_the_plan_no_longer_says_it_should_have_been_split(self):
        text = " ".join(str(one) for _, _, spec in PAGES for one in spec["sections"])
        self.assertNotIn("in a working project, split it", text)

    def test_no_single_page_carries_the_whole_plan_any_more(self):
        """The measurement that forced this, kept as a check rather than a memory."""
        biggest = max(os.path.getsize(os.path.join(DOCS, name))
                      for name, _, _ in PAGES if os.path.exists(os.path.join(DOCS, name)))
        self.assertLess(biggest, 512 * 1024,
                        "a plan page grew back past half a megabyte")


# --------------------------------------------------------------- the browser

NODE = shutil.which("node")
HARNESS = os.path.join(HERE, "published_harness.js")

#: One milestone with three phases and twelve tasks, and a task two levels down
#: in the middle phase — so "the first one" and "the one linked to" are never
#: the same element and a false pass needs a coincidence.
REQUEST = {"op": "plan", "dir": DOCS, "index": "Z2S-Plan.html",
           "milestone": "Z2S-Plan-M11.html", "task": "M11-P2-T5",
           "keyword": "write-set disjointness", "jumpTo": "Z2S-Plan-M4.html",
           "amended": {"file": "Z2S-FSD.html", "id": "FR-SPC-10"}}


def _drive():
    if not NODE or not os.path.exists(os.path.join(DOCS, REQUEST["milestone"])):
        return None, "node or the generated plan is missing", None
    finished = subprocess.run([NODE, HARNESS], input=json.dumps(REQUEST),
                              capture_output=True, text=True)
    if finished.returncode == 3:
        return None, finished.stderr.strip(), None
    if finished.returncode != 0:
        return None, finished.stderr.strip(), finished.stderr.strip()
    return json.loads(finished.stdout), None, None


#: A harness that ran and went wrong is NOT a browser that was not there. The
#: difference is the whole of LD-04 and NFR-VAL-05: a check that could not run
#: may never be counted as one that passed.
SEEN, REASON, BROKEN = _drive()


@unittest.skipIf(SEEN is None and BROKEN is None, "no browser available: %s" % REASON)
class TestTheAccordionInARealBrowser(unittest.TestCase):
    """What the owner asked for, asked of the browser rather than the markup."""

    @classmethod
    def setUpClass(cls):
        if BROKEN is not None:         # pragma: no cover - only on a real break
            raise AssertionError(
                "the browser harness failed rather than being absent; a check "
                "that could not run is not a check that passed:\n%s" % BROKEN)
        cls.seen = SEEN

    def test_the_page_renders_without_a_single_error(self):
        self.assertEqual([], self.seen["errors"])

    def test_on_arrival_the_first_unit_at_each_level_is_open_and_the_rest_are_shut(self):
        arrival = self.seen["arrival"]
        self.assertEqual([arrival["allPhases"][0]], arrival["phases"])
        # Per phase, not per page: a reader who opens the third phase should
        # find something readable in it, not another wall of shut headers.
        self.assertEqual([[ph[0]] for ph in
                          [[t for t in arrival["allTasks"] if t.startswith(one + "-")]
                           for one in arrival["allPhases"]]],
                         self.seen["tasksPerPhase"])

    def test_opening_a_phase_closes_the_other_phases(self):
        after = self.seen["afterLastPhase"]
        self.assertEqual([after["allPhases"][-1]], after["phases"])

    def test_opening_a_task_closes_the_other_tasks_in_that_phase(self):
        before = self.seen["afterLastPhase"]["tasks"]
        after = self.seen["afterSecondTask"]["tasks"]
        phase = self.seen["afterSecondTask"]["phases"][0]
        self.assertEqual(1, len([t for t in after if t.startswith(phase + "-")]))
        # And it left the other phases' open tasks exactly where they were.
        self.assertEqual([t for t in before if not t.startswith(phase + "-")],
                         [t for t in after if not t.startswith(phase + "-")])

    def test_the_only_open_one_clicked_again_shuts(self):
        phase = self.seen["afterSameTaskAgain"]["phases"][0]
        self.assertEqual([], [t for t in self.seen["afterSameTaskAgain"]["tasks"]
                              if t.startswith(phase + "-")])

    def test_expand_all_opens_everything_and_a_header_click_puts_it_back(self):
        opened = self.seen["afterExpandAll"]
        self.assertEqual(opened["allPhases"], opened["phases"])
        self.assertEqual(opened["allTasks"], opened["tasks"])
        # A header click after "expand all" means "just this one", not "close
        # the one thing I clicked" — which is what a reader is asking for.
        self.assertEqual([opened["allPhases"][0]],
                         self.seen["afterHeaderPostExpand"]["phases"])
        self.assertEqual([], self.seen["afterCollapseAll"]["phases"])
        self.assertEqual([], self.seen["afterCollapseAll"]["tasks"])

    def test_a_deep_link_reaches_a_task_two_levels_down(self):
        found = self.seen["deepLink"]
        self.assertTrue(found["found"])
        self.assertTrue(found["taskOpen"], "the task the link names is shut")
        self.assertTrue(found["phaseOpen"], "the phase holding it is shut")
        self.assertTrue(found["milestoneOpen"])
        self.assertEqual([found["phase"]], found["openPhases"])
        self.assertTrue(found["onScreen"], "the reader is looking at something else")

    def test_the_filter_opens_what_it_matches_and_clearing_it_restores_arrival(self):
        found = self.seen["filtered"]
        self.assertEqual(found["visible"], found["tasks"],
                         "a match inside a shut unit is a match nobody can see")
        self.assertEqual(self.seen["arrival"]["tasks"], found["cleared"])

    def test_the_page_does_not_scroll_sideways_on_a_phone(self):
        self.assertEqual(0, self.seen["narrow"])


@unittest.skipIf(SEEN is None and BROKEN is None, "no browser available: %s" % REASON)
class TestThePromptRowIsAControl(unittest.TestCase):
    """M14-P3-T2-C3, judged failed by the owner and rebuilt.

    The old row was small caption text with a pseudo-element triangle. It did
    not say it held a prompt, it did not look clickable, and the copy button
    only existed once the fold was open — so taking a prompt meant expanding
    five thousand words first.
    """

    @classmethod
    def setUpClass(cls):
        if BROKEN is not None:         # pragma: no cover - only on a real break
            raise AssertionError("the browser harness failed:\n%s" % BROKEN)
        cls.seen = SEEN

    def test_it_says_what_it_holds_and_which_unit_it_belongs_to(self):
        self.assertEqual("Execution prompt — M11", self.seen["prompt"]["label"])
        self.assertEqual("prompt-M11", self.seen["prompt"]["id"])

    def test_it_arrives_shut(self):
        self.assertFalse(self.seen["prompt"]["openOnArrival"])

    def test_the_copy_button_can_be_seen_and_used_without_opening_it(self):
        self.assertTrue(self.seen["prompt"]["copyInsideSummary"])
        self.assertTrue(self.seen["prompt"]["copyVisibleWhileShut"])

    def test_copying_copies_and_does_not_also_expand_the_fold(self):
        self.assertTrue(self.seen["afterCopy"]["stillShut"])
        self.assertEqual("Copied", self.seen["afterCopy"]["label"])

    def test_the_clipboard_really_holds_the_prompt(self):
        self.assertEqual(self.seen["prompt"]["body"], self.seen["afterCopy"]["held"])
        self.assertGreater(len(self.seen["afterCopy"]["held"]), 2000)


@unittest.skipIf(SEEN is None and BROKEN is None, "no browser available: %s" % REASON)
class TestPaperGetsWhatTheScreenFoldsAway(unittest.TestCase):
    """FR-SPC-11. A printed page has no controls, so what it hides it loses."""

    @classmethod
    def setUpClass(cls):
        if BROKEN is not None:         # pragma: no cover - only on a real break
            raise AssertionError("the browser harness failed:\n%s" % BROKEN)
        cls.seen = SEEN["printed"]

    def test_every_phase_and_task_body_is_expanded(self):
        self.assertEqual(0, self.seen["phaseBodiesHidden"])
        self.assertEqual(0, self.seen["taskBodiesHidden"])
        self.assertGreater(self.seen["taskBodies"], 5)

    def test_the_instructions_are_dropped_rather_than_expanded(self):
        """The one exception, and it is deliberate: paper cannot be copied from."""
        self.assertEqual(self.seen["prompts"], self.seen["promptsHidden"])
        self.assertGreater(self.seen["prompts"], 5)


@unittest.skipIf(SEEN is None and BROKEN is None, "no browser available: %s" % REASON)
class TestTheIndexInARealBrowser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if BROKEN is not None:         # pragma: no cover - only on a real break
            raise AssertionError("the browser harness failed:\n%s" % BROKEN)
        cls.seen = SEEN

    def test_the_prompts_are_the_first_thing_and_say_so(self):
        found = self.seen["index"]
        self.assertEqual("Copy a prompt to run this plan", found["promptSection"])
        self.assertEqual(1 + len(plan_spine.MILESTONES), found["promptRows"],
                         "the whole build plus one per milestone")
        self.assertEqual("prompt-orchestrator", found["firstPromptId"])

    def test_the_index_carries_the_map_and_none_of_the_work(self):
        found = self.seen["index"]
        self.assertEqual(len(plan_spine.MILESTONES), found["milestoneRows"])
        self.assertEqual(0, found["noWorkHere"], "the index is repeating the pages")

    def test_a_wave_and_a_coverage_claim_both_land_on_the_page_that_carries_them(self):
        found = self.seen["index"]
        self.assertEqual("Z2S-Plan-M1.html#M1", found["waveHref"])
        self.assertTrue(found["claimHref"].startswith("Z2S-Plan-M"), found["claimHref"])
        self.assertIn("#M", found["claimHref"])

    def test_the_rail_carries_the_plan_and_the_document_set_apart(self):
        found = self.seen["index"]
        self.assertEqual(2, found["railBlocks"])
        self.assertEqual(1 + len(plan_spine.MILESTONES), found["railParts"])
        self.assertEqual("Plan index", found["railCurrent"])

    def test_a_reader_can_get_from_the_index_to_a_milestone_and_back(self):
        found = self.seen["jumped"]
        self.assertEqual("Z2S-Plan-M4.html", found["file"])
        self.assertIn("M4", found["title"])
        self.assertEqual("M4", found["railCurrent"], "the page you are on is not a link")
        self.assertEqual("Z2S-Plan.html", found["backToIndex"])


# ------------------------------------------------------- amended, not rewritten

#: The requirements this milestone changes, and a phrase from each original that
#: has to survive the change. Never a paraphrase: the point of an amendment is
#: that the frozen wording stays exactly as it was.
AMENDED = {
    "FR-SPC-09": "highlights the section currently in view",
    "FR-SPC-10": "reveals content rather than hiding it",
    "FR-EXE-15": "chooses how much of it to hand over at once",
}


class TestTheRequirementsAreAmendedNotRewritten(unittest.TestCase):
    """FR-AMD-04, applied to the method's own specification for the first time.

    The owner asked for a plan that defaults to collapsed. FR-SPC-10 says a
    document "shall default to a state that reveals content rather than hiding
    it". Both are right about different documents — a specification is read, a
    plan is navigated — so the resolution is a dated amendment carving out the
    navigated case, not a rewrite and not a quiet exception in code.
    """

    @classmethod
    def setUpClass(cls):
        from specs import fsd
        cls.fsd = fsd
        cls.by_id = {one["id"]: one for one in fsd.REQUIREMENTS}

    def test_each_one_carries_a_dated_amendment(self):
        for identifier in AMENDED:
            found = self.by_id[identifier].get("amendments") or []
            self.assertTrue(found, "%s carries no amendment" % identifier)
            for one in found:
                self.assertTrue(one.get("date"), "%s has an undated amendment" % identifier)
                self.assertTrue(one.get("text"), "%s has an empty amendment" % identifier)

    def test_every_original_still_says_what_it_said(self):
        for identifier, phrase in AMENDED.items():
            self.assertIn(phrase, self.by_id[identifier]["text"],
                          "%s was rewritten rather than amended" % identifier)

    def test_no_identifier_was_added_or_retired_to_say_it(self):
        """The counted universe is what the coverage gate is proof about.

        An amendment that added a requirement would move it; one that retired a
        requirement would move it the other way. Neither happened, which is the
        whole reason for amending in place.
        """
        import coverage as COV
        universe, excluded = COV.universe()
        self.assertEqual(194, len(universe), "the counted universe moved")
        self.assertEqual(2, len(excluded), "an exclusion was added or removed")
        for identifier in AMENDED:
            self.assertNotIn("retired", self.by_id[identifier])


@unittest.skipIf(SEEN is None and BROKEN is None, "no browser available: %s" % REASON)
class TestAnAmendmentIsVisibleToAReader(unittest.TestCase):
    """A recorded amendment nobody can see is a rewrite with extra steps."""

    @classmethod
    def setUpClass(cls):
        if BROKEN is not None:         # pragma: no cover - only on a real break
            raise AssertionError("the browser harness failed:\n%s" % BROKEN)
        cls.seen = SEEN["amended"]

    def test_the_amendment_renders_under_its_own_heading_with_its_date(self):
        self.assertTrue(self.seen["found"])
        self.assertTrue(self.seen["rendered"],
                        "the published renderer dropped the amendment silently")
        self.assertEqual("Amended since", self.seen["heading"])
        self.assertEqual("2026-08-15", self.seen["date"])
        self.assertEqual(1, self.seen["amendments"])

    def test_the_original_is_still_on_the_page_above_it(self):
        self.assertIn(AMENDED["FR-SPC-10"], self.seen["original"])


if __name__ == "__main__":
    unittest.main()
