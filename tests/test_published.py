# -*- coding: utf-8 -*-
"""The published site's own prompts, and the one thing it must not re-spell.

`docs/_build/` is a separate generator from `z2s/` on purpose, and the owner
declined joining them (2026-08-14). It stays separate — except for the loop.
What a prompt says is the one thing that cannot be spelled twice: a published
prompt and a generated one that disagreed would each be claiming to be the
method, and a reader has no way to tell which is which.

So this module asks two questions of the published set. Does every unit of the
published plan carry a real prompt? And is that prompt the shared one, rather
than a second copy that will drift?

Traces: FR-EXE-15, FR-EXE-16, US-EXE-08, US-EXE-09.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, "docs", "_build")
sys.path.insert(0, ROOT)
sys.path.insert(0, BUILD)

from z2s import gauntlet                                          # noqa: E402

import generate                                                   # noqa: E402
from specs import plan_spine                                      # noqa: E402

PROMPTS = generate.plan_prompts()


class TestEveryPublishedUnitCarriesItsOwnPrompt(unittest.TestCase):
    """M14-04. Real ones, on every unit, not a description of one."""

    def test_the_whole_build_every_milestone_phase_and_task_has_one(self):
        wanted = [gauntlet.WHOLE]
        for one in plan_spine.MILESTONES:
            wanted.append(one["id"])
            for phase in generate.DETAIL.get(one["id"], []):
                wanted.append(phase["id"])
                wanted.extend(task["id"] for task in phase.get("tasks", []))
        self.assertEqual(sorted(wanted), sorted(PROMPTS))
        self.assertGreater(len(wanted), 150, "the published plan lost most of its units")

    def test_each_one_carries_every_part_its_level_owes(self):
        from z2s import schema
        for unit, text in PROMPTS.items():
            level = "plan" if unit == gauntlet.WHOLE else schema.plan_level(unit)
            self.assertEqual([], gauntlet.check(text, level), unit)

    def test_a_task_prompt_states_that_tasks_own_criteria(self):
        found = PROMPTS["M14-P1-T1"]
        self.assertIn("M14-P1-T1-C1", found)
        self.assertIn("M14-P1-T1-C2", found)

    def test_a_prompt_names_what_its_unit_waits_on(self):
        self.assertIn("M13", PROMPTS["M14"])
        self.assertIn("M14-P1", PROMPTS["M14-P2"])

    def test_the_higher_target_names_titles_the_reader_can_recognise(self):
        # The catalogue is right there in the same document, so a bare
        # identifier would make the reader go and look it up.
        self.assertIn("FR-EXE-15 — A prompt at every level of the plan",
                      PROMPTS["M14-P1-T3"])


class TestThePromptsReachTheDocument(unittest.TestCase):
    """Built is not the same as attached.

    Every assertion above is about the prompts this generator computes. These
    are about the specification it actually writes into `Z2S-Plan.html` — the
    mutations that dropped the whole-build section and stripped the task prompts
    survived every check that only looked at the dictionary.
    """

    @classmethod
    def setUpClass(cls):
        # The plan is one document across an index and one page per milestone,
        # so the prompts reach the reader through fifteen files rather than one.
        cls.pages = generate.build_plan()
        cls.index = cls.pages[0][2]
        cls.sections = {one["id"]: one for one in cls.index["sections"]}

    def test_the_whole_build_prompt_is_the_first_section(self):
        first = self.index["sections"][0]
        self.assertEqual("prompt", first["id"])
        self.assertEqual("prompts", first["type"])
        self.assertEqual(gauntlet.WHOLE, first["items"][0]["unit"])
        self.assertIn(gauntlet.GUARD, first["items"][0]["body"])

    def test_the_index_offers_a_prompt_for_the_build_and_for_every_milestone(self):
        """Fault 2 of the owner's review: the whole-build prompt was unfindable.

        It was the first section all along, titled "Execution instructions" and
        rendered as one more grey caption row. What was missing was a section
        that says what it holds and a row per milestone beside it.
        """
        offered = [one["unit"] for one in self.index["sections"][0]["items"]]
        self.assertEqual([gauntlet.WHOLE] + [m["id"] for m in plan_spine.MILESTONES], offered)
        self.assertIn("prompt", self.index["sections"][0]["title"].lower())

    def test_every_milestone_phase_and_task_in_the_document_carries_one(self):
        carried = [spec for _, _, spec in self.pages[1:]]
        self.assertEqual(len(plan_spine.MILESTONES), len(carried))
        tasks = 0
        for spec in carried:
            work = next(s for s in spec["sections"] if s["type"] == "milestones")
            self.assertEqual(1, len(work["items"]), "a milestone page carries exactly one")
            one = work["items"][0]
            self.assertIn(gauntlet.GUARD, one["prompt"], one["id"])
            for phase in one["phases"]:
                self.assertIn(gauntlet.GUARD, phase["prompt"], phase["id"])
                for task in phase["tasks"]:
                    self.assertIn(gauntlet.GUARD, task["prompt"], task["id"])
                    self.assertIn(task["id"], task["prompt"])
                    tasks += 1
        self.assertGreater(tasks, 100, "the published plan lost most of its tasks")


class TestThePublishedPromptIsTheSharedOne(unittest.TestCase):
    """M14-01. One definition; the site is a second door onto it, not a copy."""

    def test_the_injection_guard_is_present_verbatim(self):
        for unit in ("M14-P1-T1", "M14-P1", "M14", gauntlet.WHOLE):
            self.assertIn(gauntlet.GUARD, PROMPTS[unit], unit)

    def test_the_published_generator_spells_no_part_of_the_loop_itself(self):
        """A second copy of a sentence is a sentence that will drift.

        Checked against the actual source rather than the output: the output
        would still look right the moment after somebody pasted the text in.
        """
        sentences = list(gauntlet.LOOP) + list(gauntlet.JUDGE_CONTRACT) + \
            list(gauntlet.CEILING) + [gauntlet.NO_CEILING, gauntlet.SMOOTHING]
        for name in ("generate.py", "shell.py"):
            with open(os.path.join(BUILD, name), encoding="utf-8") as handle:
                source = handle.read()
            for one in sentences:
                # Compared on a distinctive fragment: the full sentence is
                # wrapped across source lines wherever it is written down.
                fragment = " ".join(one.split()[:7])
                self.assertNotIn(fragment, source,
                                 "%s spells the loop itself: %r" % (name, fragment))

    def test_the_prohibited_operations_come_from_the_safety_rules(self):
        from z2s import safety
        for one in safety.PROHIBITED:
            self.assertIn(one.title, PROMPTS["M14-P1-T1"])

    def test_the_settled_decisions_point_at_the_published_document(self):
        """The real ledger is not published, so the prompts send a reader to
        what they can actually open rather than to a file they do not have."""
        found = PROMPTS["M14-P1-T1"]
        self.assertIn(generate.FILES["sdd"], found)
        self.assertIn("ADR-01", found)


if __name__ == "__main__":
    unittest.main()
