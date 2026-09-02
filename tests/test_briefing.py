# -*- coding: utf-8 -*-
"""The narrative briefing — the document for the reader who reads no others.

M12-P3-T1. Two things make it worth generating rather than writing:

  * It is DERIVED. Change a capability, an exclusion or a decision and the
    briefing changes on the next run. A briefing typed by hand is accurate the
    week it is written and quietly wrong thereafter, which is worse than absent
    because it is believed (M12-P3-T1-C1).
  * It is LAYERED. Plain language first, technical depth last, so a reader stops
    where their interest does rather than at the first word they do not know
    (FR-DOC-09, NFR-UX-06).
"""

import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from z2s import briefing, chain, fsd, gate, paths, schema, validate     # noqa: E402
from test_fsd import excluded_requirement                              # noqa: E402
from test_plan import build_chain, closed                              # noqa: E402
from test_stories import covering_fsd                                  # noqa: E402


def brief(**extra):
    made = {"title": "Kestrel — briefing", "owner": "A. Owner",
            "date": "2026-08-15"}
    made.update(extra)
    return made


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


class Briefed(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-brief-")
        build_chain(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def author(self, **extra):
        made = brief(**extra)
        run = closed(gate.Gate(briefing.SLUG, briefing.forks(made), source=made))
        return briefing.author(self.root, made, run)

    def sections(self, spec):
        return {one["id"]: one for one in spec["sections"]}

    def reauthor_fsd(self, requirements):
        made = covering_fsd()
        made["requirements"].extend(requirements)
        fsd.author(self.root, made,
                   closed(gate.Gate(fsd.SLUG, fsd.forks(made), source=made)))


# ------------------------------------------------------------ the prerequisites

class TestTheBriefingIsDerivedOrNotWritten(Briefed):

    def test_it_refuses_without_the_documents_it_summarises(self):
        empty = tempfile.mkdtemp(prefix="z2s-brief-empty-")
        try:
            made = brief()
            run = closed(gate.Gate(briefing.SLUG, briefing.forks(made), source=made))
            with self.assertRaises(chain.MissingPrerequisite):
                briefing.author(empty, made, run)
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    def test_nothing_is_written_when_it_refuses(self):
        empty = tempfile.mkdtemp(prefix="z2s-brief-empty-")
        try:
            made = brief()
            run = closed(gate.Gate(briefing.SLUG, briefing.forks(made), source=made))
            try:
                briefing.author(empty, made, run)
            except chain.MissingPrerequisite:
                pass
            self.assertFalse(os.path.exists(
                paths.resolve(empty, paths.SPECS_DIR, briefing.FILENAME)))
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    def test_it_states_no_fact_of_its_own(self):
        """Every line in it came from a document above it."""
        _, spec = self.author()
        self.assertTrue(spec["sources"])
        stated = [row[1] for row in
                  self.sections(spec)["sources"]["rows"]]
        self.assertIn("Intent.html", stated)


class TestTheBriefingChangesWithTheSpecification(Briefed):

    def test_adding_a_capability_changes_the_briefing(self):
        """M12-P3-T1-C1"""
        written, _ = self.author()
        before = read(written)
        self.reauthor_fsd([{"area": "FR-DOC", "priority": "Must",
                            "title": "Export the register",
                            "text": "The system shall let a reader take the "
                                    "source register away as a file.",
                            "traces": {"goal": ["G-01"]}}])
        self.author()
        after = read(written)
        self.assertNotEqual(before, after)
        self.assertIn("Export the register", after)

    def test_generating_twice_from_an_unchanged_set_is_byte_identical(self):
        """NFR-GEN-01: derived does not mean unstable."""
        written, _ = self.author()
        before = read(written)
        self.author()
        self.assertEqual(before, read(written))

    def test_a_new_exclusion_reaches_the_briefing_with_its_reason(self):
        self.reauthor_fsd([excluded_requirement()])
        _, spec = self.author()
        found = self.sections(spec)[briefing.EXCLUSIONS]
        self.assertIn("Hosted editing", str(found))
        self.assertIn("version control", str(found))


class TestTheBriefingIsLayered(Briefed):

    def test_it_opens_in_plain_language_and_ends_in_the_technical_detail(self):
        _, spec = self.author()
        order = [one["id"] for one in spec["sections"]]
        self.assertLess(order.index(briefing.SHORTLY), order.index(briefing.BUILT))

    def test_every_layer_the_generator_states_is_a_section_when_it_has_content(self):
        self.reauthor_fsd([excluded_requirement()])
        _, spec = self.author()
        order = [one["id"] for one in spec["sections"]]
        for layer in briefing.LAYERS:
            self.assertIn(layer.id, order)
        self.assertEqual([one.id for one in briefing.LAYERS],
                         [one for one in order if one in briefing.BUILDERS],
                         "the layers are out of order")

    def test_a_layer_with_nothing_to_say_is_left_out_rather_than_empty(self):
        """NFR-DAT-06: a heading over nothing reads as an unfinished document."""
        _, spec = self.author()
        for section in spec["sections"]:
            self.assertTrue(section.get("body") or section.get("items")
                            or section.get("rows") or section.get("columns"),
                            "%s renders nothing" % section["id"])


class TestTheBriefingNamesNothingOnlyAnInsiderFollows(Briefed):

    def test_it_produces_no_plain_language_warning(self):
        """FR-GEN-05, NFR-UX-06 — the check the story generator already uses."""
        written, _ = self.author()
        found = schema.check_plain_language(validate.extract(read(written)))
        self.assertEqual([], found, "; ".join(one.message for one in found))

    def test_it_validates_as_a_document_in_its_own_right(self):
        written, spec = self.author()
        found = [one for one in validate.validate_document(spec, written)
                 if one.severity == schema.FAILURE]
        self.assertEqual([], found, "; ".join(one.message for one in found))

    def test_it_defines_no_identifier_of_its_own(self):
        """It is a reading of the set, not a member of it (M7-02)."""
        _, spec = self.author()
        self.assertEqual([], [entry["id"] for _, entry in schema.entries(spec)
                              if schema.kind_of(entry.get("id")) in
                              ("requirement", "decision")])


if __name__ == "__main__":
    unittest.main(verbosity=2)
