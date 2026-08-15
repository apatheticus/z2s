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

import os
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


if __name__ == "__main__":
    unittest.main()
