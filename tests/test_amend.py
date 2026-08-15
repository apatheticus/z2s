# -*- coding: utf-8 -*-
"""Amendment: extending a shipped specification without disturbing it (M12-P2).

An identifier is permanent (ADR-03). So the only honest way to add scope to a
document somebody has already read, traced to and written tests against is to
write a NEW document under a new prefix, and to annotate the original in place
where a later decision changed it.

The three rules tested here:

  M12-P2-T1  An addendum adds scope; no original identifier moves, and the
             original file is not written to at all.
  M12-P2-T2  An amendment note lives on the entry it amends, carries its date,
             and survives every regeneration.
  M12-P2-T3  New scope that no unit of work claims fails the pipeline.
"""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from z2s import chain, fsd, gate, paths, pipeline, sdd, trace, validate  # noqa: E402
from test_plan import build_chain, closed                              # noqa: E402
from test_stories import covering_fsd                                  # noqa: E402
from test_sdd import sdd_brief                                         # noqa: E402


def addendum_brief(**extra):
    """New scope, authored as its own document under its own prefix."""
    made = {"title": "Kestrel — functional specification, addendum 01",
            "owner": "A. Owner", "date": "2026-08-15",
            "addendum": "01",
            "purpose": "What was added after the first release was agreed.",
            "areas": [{"key": "FR-NEW", "name": "Later scope",
                       "description": "Everything agreed after the freeze."}],
            "requirements": [
                {"area": "FR-NEW", "priority": "Must", "title": "Export the register",
                 "text": "The system shall let a reader take the source register away "
                         "as a file.",
                 "traces": {"goal": ["G-01"]}}],
            "sources": [{"kind": "narrative", "name": "Follow-up conversation",
                         "origin": "A call on the 15th.",
                         "contributed": "The one thing the first release left out."}]}
    made.update(extra)
    return made


def author(root, module, brief):
    run = closed(gate.Gate(module.SLUG, module.forks(brief), source=brief))
    return module.author(root, brief, run)


def read(path):
    with open(path, "rb") as handle:
        return handle.read()


class Chain(unittest.TestCase):
    """A full generated document set, as a project that has shipped once."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-amend-")
        build_chain(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def spec_path(self, filename):
        return paths.resolve(self.root, paths.SPECS_DIR, filename)


# --------------------------------------------------------- addendum (M12-P2-T1)

class TestAnAddendumDisturbsNothing(Chain):

    def test_an_addendum_goes_into_its_own_file(self):
        written, _ = author(self.root, fsd, addendum_brief())
        self.assertTrue(os.path.exists(written))
        self.assertNotEqual(self.spec_path(fsd.FILENAME), written)

    def test_authoring_an_addendum_does_not_write_to_the_original(self):
        """M12-P2-T1-C1 — the file, not merely the identifiers."""
        before = read(self.spec_path(fsd.FILENAME))
        author(self.root, fsd, addendum_brief())
        self.assertEqual(before, read(self.spec_path(fsd.FILENAME)))

    def test_every_original_identifier_still_resolves(self):
        original = validate.extract(
            read(self.spec_path(fsd.FILENAME)).decode("utf-8"))
        counted, _ = fsd.universe(original)
        author(self.root, fsd, addendum_brief())
        after = validate.extract(
            read(self.spec_path(fsd.FILENAME)).decode("utf-8"))
        self.assertEqual(list(counted), list(fsd.universe(after)[0]))

    def test_the_addendum_prefix_is_registered_for_routing(self):
        """M12-P2-T1-C2"""
        written, _ = author(self.root, fsd, addendum_brief())
        specs, _ = trace.read([self.spec_path(fsd.FILENAME), written])
        routes, collisions = trace.owners(specs)
        self.assertEqual([], collisions)
        self.assertEqual(os.path.basename(written), routes["FR-NEW"])

    def test_addendum_identifiers_join_the_coverage_universe(self):
        written, _ = author(self.root, fsd, addendum_brief())
        specs, _ = trace.read([self.spec_path(fsd.FILENAME), written])
        self.assertIn("FR-NEW-01", trace.universe(specs))

    def test_an_addendum_reusing_the_originals_area_is_a_collision(self):
        """The guard that makes the prefix rule real rather than a convention."""
        written, _ = author(self.root, fsd,
                            addendum_brief(areas=[{"key": "FR-DOC",
                                                   "name": "Same area again"}],
                                           requirements=[
                                               {"area": "FR-DOC", "priority": "Must",
                                                "title": "Export the register",
                                                "text": "It shall be exportable.",
                                                "traces": {"goal": ["G-01"]}}]))
        specs, _ = trace.read([self.spec_path(fsd.FILENAME), written])
        _, collisions = trace.owners(specs)
        self.assertTrue(collisions)

    def test_the_addendum_says_what_it_extends(self):
        written, _ = author(self.root, fsd, addendum_brief())
        self.assertIn(fsd.FILENAME,
                      read(written).decode("utf-8"))

    def test_an_addendum_regenerates_to_its_own_file(self):
        written, spec = author(self.root, fsd, addendum_brief())
        before = read(written)
        self.assertEqual(written, fsd.regenerate(self.root, spec))
        self.assertEqual(before, read(written))

    def test_a_technical_addendum_works_the_same_way(self):
        """The rule is the chain's, not one generator's (NFR-ARC-01)."""
        written, _ = author(self.root, sdd, sdd_brief(
            addendum="01", title="Kestrel — technical specification, addendum 01",
            areas=[{"key": "NFR-NEW", "name": "Later constraints"}],
            requirements=[{"area": "NFR-NEW", "priority": "Must",
                           "title": "Export speed",
                           "text": "An export shall complete inside two seconds.",
                           "traces": {"adr": ["ADR-01"]}}]))
        self.assertNotEqual(self.spec_path(sdd.FILENAME), written)
        self.assertIn("Addendum", os.path.basename(written))

    def test_a_document_with_no_addendum_key_is_unaffected(self):
        written, _ = author(self.root, fsd, covering_fsd())
        self.assertEqual(self.spec_path(fsd.FILENAME), written)


# ------------------------------------------------------ annotation (M12-P2-T2)

class TestAnAmendmentIsAnnotatedInPlace(Chain):

    def amended(self, **extra):
        brief = covering_fsd()
        brief["requirements"][0]["amendments"] = [
            dict({"date": "2026-08-15",
                  "text": "Superseded by FR-NEW-01: the register is now exportable."},
                 **extra)]
        return brief

    def entry(self, spec, identifier="FR-DOC-01"):
        for section in spec["sections"]:
            for one in section.get("items") or ():
                if isinstance(one, dict) and one.get("id") == identifier:
                    return one
        return None

    def test_an_annotation_reaches_the_rendered_specification(self):
        _, spec = author(self.root, fsd, self.amended())
        self.assertEqual("2026-08-15",
                         self.entry(spec)["amendments"][0]["date"])

    def test_the_annotation_carries_its_date(self):
        """M12-P2-T2-C2"""
        written, _ = author(self.root, fsd, self.amended())
        self.assertIn("2026-08-15", read(written).decode("utf-8"))

    def test_an_annotation_survives_regeneration(self):
        """M12-P2-T2-C1 — regenerated from the document's own specification."""
        written, _ = author(self.root, fsd, self.amended())
        fsd.regenerate(self.root)
        after = validate.extract(read(written).decode("utf-8"))
        self.assertEqual("Superseded by FR-NEW-01: the register is now exportable.",
                         self.entry(after)["amendments"][0]["text"])

    def test_regenerating_twice_leaves_the_bytes_alone(self):
        written, _ = author(self.root, fsd, self.amended())
        fsd.regenerate(self.root)
        before = read(written)
        fsd.regenerate(self.root)
        self.assertEqual(before, read(written))

    def test_an_annotation_with_no_date_is_refused_rather_than_dated_here(self):
        """Nothing in the method reads the clock, and least of all this."""
        brief = self.amended()
        del brief["requirements"][0]["amendments"][0]["date"]
        with self.assertRaises(chain.IncompleteBrief) as caught:
            author(self.root, fsd, brief)
        self.assertIn("date", str(caught.exception))

    def test_an_annotation_with_no_words_is_refused(self):
        brief = self.amended()
        brief["requirements"][0]["amendments"][0]["text"] = ""
        with self.assertRaises(chain.IncompleteBrief):
            author(self.root, fsd, brief)

    def test_an_unamended_requirement_carries_no_empty_annotation(self):
        """NFR-DAT-06 reaches here too."""
        _, spec = author(self.root, fsd, self.amended())
        self.assertNotIn("amendments", self.entry(spec, "FR-DOC-02"))

    def test_an_annotation_does_not_change_the_identifier_or_the_text(self):
        _, plain = author(self.root, fsd, covering_fsd())
        _, marked = author(self.root, fsd, self.amended())
        self.assertEqual(self.entry(plain)["text"], self.entry(marked)["text"])
        self.assertEqual(self.entry(plain)["id"], self.entry(marked)["id"])


# ------------------------------------------------- re-derivation (M12-P2-T3)

class TestNewScopeCannotSitUnclaimed(Chain):

    def test_an_unclaimed_new_requirement_fails_the_coverage_gate(self):
        """M12-P2-T3-C1"""
        written, _ = author(self.root, fsd, addendum_brief())
        sources = sorted(
            [self.spec_path(fsd.FILENAME), written]
            + [self.spec_path(one) for one in ("SDD.html", "Stories.html")])
        findings, _, _ = trace.gate(sources)
        uncovered = [one for one in findings if one.code == "uncovered"]
        self.assertIn("FR-NEW-01", [one.where for one in uncovered])
        self.assertEqual(1, trace.exit_code(findings))

    def test_the_report_names_what_is_newly_unclaimed_rather_than_the_matrix(self):
        written, _ = author(self.root, fsd, addendum_brief())
        sources = [self.spec_path(fsd.FILENAME), written]
        findings, rows, specs = trace.gate(sources)
        report = trace.format_report(findings, rows, specs, sources)
        heading = [line for line in report.splitlines()
                   if "unclaimed:" in line]
        self.assertEqual(1, len(heading))
        self.assertIn("FR-NEW-01", heading[0])

    def test_the_pipeline_fails_on_an_amendment_nothing_claims(self):
        """The gate an operator actually runs, not the engine underneath it."""
        written, _ = author(self.root, fsd, addendum_brief())
        out = io.StringIO()
        code = pipeline.main([self.spec_path(fsd.FILENAME), written], out)
        self.assertEqual(1, code)
        self.assertIn("FR-NEW-01", out.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
