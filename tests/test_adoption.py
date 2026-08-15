# -*- coding: utf-8 -*-
"""The adoption guidance, checked against the published playbook (M12-P3-T4).

The task's failing test is a review checklist, and this is it, written as a
check rather than as a page somebody is supposed to read: the guidance has to
name the minimum viable subset explicitly and state the order of adoption, and
every step has to say which requirement it satisfies.

That last one is the part with teeth. A cross-reference to an identifier the
specification does not define is worse than no cross-reference, because it reads
as traceable and is not — so every identifier cited below is checked against the
document that assigns it.
"""

import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from z2s import schema, validate                                       # noqa: E402

REPO = os.path.dirname(HERE)
PUBLISHED = os.path.join(REPO, "docs")

PLAYBOOK = os.path.join(PUBLISHED, "Z2S-Playbook.html")
MINIMUM = "minimum"
ADOPTION = "adoption"

#: Anything that looks like a requirement or a decision, wherever it is cited.
CITED = re.compile(r"\b((?:FR|NFR|ADR)-[A-Z]{0,4}-?\d{2})\b")


def extract(path):
    with open(path, encoding="utf-8") as handle:
        return validate.extract(handle.read())


def defined():
    """Every requirement and decision the published set assigns."""
    found = set()
    for name in sorted(os.listdir(PUBLISHED)):
        if not name.endswith(".html"):
            continue
        try:
            spec = extract(os.path.join(PUBLISHED, name))
        except validate.ExtractionError:
            continue
        for _, entry in schema.entries(spec):
            if schema.kind_of(entry.get("id")) in ("requirement", "decision"):
                found.add(entry["id"])
    return found


@unittest.skipIf(not os.path.exists(PLAYBOOK), "the playbook is not published")
class TestTheGuidanceIsThere(unittest.TestCase):

    def setUp(self):
        self.spec = extract(PLAYBOOK)
        self.sections = {one["id"]: one for one in self.spec["sections"]}

    def test_the_minimum_viable_subset_is_named_explicitly(self):
        """M12-P3-T4-C2"""
        found = self.sections[MINIMUM]
        self.assertIn("minimum viable subset", found["title"].lower())
        self.assertGreaterEqual(len(found["items"]), 3)

    def test_the_order_of_adoption_is_stated(self):
        found = self.sections[ADOPTION]
        self.assertTrue(found.get("ordered"),
                        "an adoption order rendered unordered is not an order")
        self.assertGreaterEqual(len(found["items"]), 5)

    def test_the_guidance_says_it_is_for_a_project_that_already_exists(self):
        """Adoption is the case where the project is not a blank page."""
        self.assertIn("exist", self.sections[ADOPTION]["title"].lower())

    def test_each_step_states_what_it_gets_you_before_the_next_one(self):
        """Separable adoption (NFR-ARC-05) is only real if each step stands alone."""
        for item in self.sections[ADOPTION]["items"]:
            self.assertGreater(len(item), 120,
                               "a step with no stated payoff is an instruction, "
                               "not guidance: %r" % item[:60])


@unittest.skipIf(not os.path.exists(PLAYBOOK), "the playbook is not published")
class TestEveryStepNamesWhatItSatisfies(unittest.TestCase):
    """The refactor step: a cross-reference that does not resolve is a lie."""

    def setUp(self):
        self.spec = extract(PLAYBOOK)
        self.sections = {one["id"]: one for one in self.spec["sections"]}
        self.known = defined()

    def cited(self, section_id):
        return [(item, CITED.findall(item))
                for item in self.sections[section_id]["items"]]

    def test_every_adoption_step_cites_at_least_one_requirement(self):
        for item, found in self.cited(ADOPTION):
            self.assertTrue(found, "no requirement cited: %r" % item[:60])

    def test_every_minimum_subset_entry_cites_at_least_one_requirement(self):
        for item, found in self.cited(MINIMUM):
            self.assertTrue(found, "no requirement cited: %r" % item[:60])

    def test_every_identifier_the_guidance_cites_actually_exists(self):
        unknown = []
        for section_id in (ADOPTION, MINIMUM):
            for _, found in self.cited(section_id):
                unknown.extend(one for one in found if one not in self.known)
        self.assertEqual([], sorted(set(unknown)))

    def test_the_published_set_is_what_the_check_reads(self):
        """A guard on the guard: an empty known set would pass everything."""
        self.assertGreater(len(self.known), 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
