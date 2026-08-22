# -*- coding: utf-8 -*-
"""Re-rendering a project's documents against its current design system.

A generated document carries its own stylesheet, inlined. Nothing re-reads it.
So two promises in the specification set were true of a *first* generation and
false of every project that already had documents:

  * FR-GEN-02 — documents adopt the host project's design system. They adopt it
    on the day they are written and never again, so a design system that changes
    reaches nothing already written.
  * FR-DOC-06 — a document re-renders from its own embedded specification
    without loss. True one document at a time; there was no way to ask it of a
    set.

The command closes both. The claim everything else here rests on is the first
test in the file: re-rendering a project whose design has not moved produces the
bytes that are already on disk. Without that this is a command nobody can run
twice, and the rest of the promise is worth nothing.

Traces: FR-GEN-02, FR-GEN-03, FR-GEN-07, FR-DOC-06, NFR-GEN-01, NFR-GEN-02.
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

from z2s import chain, design, paths, plan, restyle, schema, tokens, validate

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: A host stylesheet with enough of the contract declared to be recognised as a
#: design system. Detection is what the middle rung of the ladder does, so the
#: values have to be findable without a record telling anybody where to look.
STYLESHEET = """
:root {
  --color-background: #eef1f5;
  --color-surface: #ffffff;
  --color-text: #10141a;
  --color-border: #ccd3dc;
  --color-primary: #1a4f8f;
}
"""


def specification(slug="vision", title="Vision"):
    """A specification document as the chain writes one."""
    return {
        "schemaVersion": schema.SCHEMA_VERSION,
        "document": {"title": title, "slug": slug, "type": "Product vision",
                     "owner": "The build", "version": "1.0",
                     "date": "2026-08-21",
                     "status": "Draft for review", "summary": "One document."},
        "sections": [{"id": "purpose", "type": "prose", "title": "Purpose",
                      "body": ["It exists."]}],
    }


def milestone(identifier="M1"):
    """A milestone document as z2s/plan.py writes one."""
    items = [{"id": "%s-P1-T1" % identifier, "area": "%s-P1" % identifier,
              "title": "A unit of work", "priority": "Must", "autonomy": "auto",
              "status": "not-started", "layer": "schema", "testLayers": ["unit"],
              "criteria": [{"id": "%s-P1-T1-C1" % identifier, "kind": "auto",
                            "text": "It holds.", "done": False}]}]
    return {
        "schemaVersion": schema.SCHEMA_VERSION,
        "document": {"title": "%s — a milestone" % identifier, "slug": "plan",
                     "type": "Delivery plan", "milestone": identifier,
                     "owner": "The build", "version": "1.0",
                     "date": "2026-08-21",
                     "status": "Draft for review", "summary": "One milestone."},
        "legend": schema.legend(),
        "catalog": {one["id"]: one["title"] for one in items},
        "sections": [{"id": "work", "type": "requirements",
                      "title": "Phases and tasks",
                      "areas": [{"key": "%s-P1" % identifier, "name": "Phase 1"}],
                      "items": items}],
    }


def index():
    """The plan index, which carries a different element identifier again."""
    spec = milestone("M1")
    spec["document"]["title"] = "The plan"
    spec["document"].pop("milestone")
    return spec


def record(background="#101418", text="#f4f6f8"):
    """A design record with an operator's own values in it."""
    return {
        "version": 1,
        "scheme": "light",
        "tokens": {"surface-page": {"light": background, "from": "app.css"},
                   "text-body": {"light": text, "from": "app.css"}},
        "overrides": {},
        "confirmed": {},
        "sources": [],
        "refused": [],
        "clamped": [],
        "unmapped": [],
    }


class Case(unittest.TestCase):
    """A real project with real documents in it, specifications and plan alike."""

    def setUp(self):
        design.forget()
        self.root = tempfile.mkdtemp(prefix="z2s-restyle-")
        paths.ensure_layout(self.root)
        self.specs = [chain.write(self.root, "Vision.html",
                                  specification("vision", "Vision"), "vision-spec"),
                      chain.write(self.root, "FSD.html",
                                  specification("fsd", "Specification"), "fsd-spec")]
        self.plan = [plan.write(self.root, plan.INDEX_FILE, index(),
                                plan.INDEX_SPEC_ID),
                     plan.write(self.root, "M1-the-toolchain.html", milestone(),
                                plan.MILESTONE_SPEC_ID)]
        self.all = self.specs + self.plan

    def tearDown(self):
        design.forget()
        shutil.rmtree(self.root, ignore_errors=True)

    def text(self, path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def bytes_now(self):
        return {path: self.text(path) for path in self.all}

    def write_record(self, **values):
        design.write_record(self.root, record(**values))
        design.forget()

    def host(self, name="app.css", body=STYLESHEET):
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
        design.forget()
        return path


# --------------------------------------------------------------- the claim

class TestAnUnchangedProjectIsNotRewritten(Case):
    """The claim the rest of the file rests on.

    Re-rendering is the whole mechanism, so a re-render that changes bytes on a
    project nobody has touched would mean the command could never be run twice
    without churning the set — and a diff of noise is a diff nobody reads.
    """

    def test_nothing_is_written(self):
        before = self.bytes_now()
        found = restyle.restyle(self.root)
        self.assertEqual([], found.written)
        self.assertEqual(before, self.bytes_now())

    def test_every_document_is_reported_as_already_current(self):
        """Both counts, always. A run that changed nothing has to say so
        rather than report the work it did not do (FR-GEN-03)."""
        found = restyle.restyle(self.root)
        self.assertEqual(sorted(self.all), sorted(found.current))
        self.assertIn("4", restyle.report(found))

    def test_the_documents_are_still_valid(self):
        restyle.restyle(self.root)
        for path in self.all:
            self.assertEqual([], [one for one in
                                  validate.validate_document(validate.extract(
                                      self.text(path)), path)
                                  if one.severity == schema.FAILURE])


# ------------------------------------------------- the regression it is for

class TestAChangedDesignReachesEveryDocument(Case):
    """The reason the command exists.

    `/zero:design` says in its own words to run it when the design system
    changes. All it wrote was the record. Every document written before that
    kept its old colours forever, and no command in the method could change it.
    """

    def test_the_new_value_appears_in_every_document(self):
        self.write_record(background="#123456")
        found = restyle.restyle(self.root)
        self.assertEqual(sorted(self.all), sorted(found.written))
        for path in self.all:
            self.assertIn("#123456", self.text(path))

    def test_the_plan_is_restyled_and_not_only_the_specifications(self):
        """The plan is where a project's own work lives, and it is a separate
        directory with a separate writer. Skipping it would look like success."""
        self.write_record(background="#123456")
        restyle.restyle(self.root)
        for path in self.plan:
            self.assertIn("#123456", self.text(path))

    def test_the_old_value_is_gone(self):
        self.write_record(background="#123456")
        restyle.restyle(self.root)
        for path in self.all:
            self.assertNotIn(tokens.NEUTRAL["surface-page"],
                             self.text(path))


# ------------------------------------------------------------- the ladder

class TestTheDesignIsCheckedAsIfGeneratingFresh(Case):
    """Record, then detection, then neutral — the same three rungs a first
    generation climbs, and a line saying which of them happened."""

    def test_a_record_is_adopted(self):
        self.write_record(background="#123456")
        found = restyle.restyle(self.root)
        self.assertIn(paths.DESIGN_FILE, found.note)
        self.assertIn("#123456", self.text(self.specs[0]))

    def test_a_host_stylesheet_is_detected_when_there_is_no_record(self):
        self.host()
        found = restyle.restyle(self.root)
        self.assertIn("app.css", found.note)
        self.assertIn("#eef1f5", self.text(self.specs[0]))

    def test_a_project_with_neither_falls_back_to_the_neutral_theme(self):
        found = restyle.restyle(self.root)
        self.assertIn("neutral", found.note)
        self.assertEqual([], found.written)

    def test_the_note_names_which_of_the_three_happened(self):
        """A silent fallback reads as adoption (FR-GEN-03). Three runs, three
        different sentences — never the same line whatever was found."""
        said = [restyle.restyle(self.root).note]
        self.host()
        said.append(restyle.restyle(self.root).note)
        self.write_record()
        said.append(restyle.restyle(self.root).note)
        self.assertEqual(3, len(set(said)))


class TestAStaleRecordIsUsedAndNamed(Case):
    """D-02. The record is still the operator's decision, and a re-style with a
    slightly old palette is an improvement on documents with a much older one.
    What must not happen is using it silently."""

    def test_the_record_is_still_used(self):
        path = self.host()
        found = design.detect(self.root)
        held = design.build_record(found, self.root)
        held["tokens"]["surface-page"] = {"light": "#123456", "from": "app.css"}
        design.write_record(self.root, held)
        design.forget()

        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(STYLESHEET.replace("#eef1f5", "#fafbfc"))
        design.forget()

        found = restyle.restyle(self.root)
        self.assertIn("#123456", self.text(self.specs[0]))

    def test_the_report_names_the_file_that_moved(self):
        path = self.host()
        held = design.build_record(design.detect(self.root), self.root)
        design.write_record(self.root, held)
        design.forget()
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(STYLESHEET.replace("#eef1f5", "#fafbfc"))
        design.forget()

        self.assertIn("app.css", restyle.restyle(self.root).note)


# ---------------------------------------------------------------- the trap

class TestThePlanKeepsItsOwnElementIdentifiers(Case):
    """A plan document does NOT use the slug-derived identifier every
    specification uses. Its slug is "plan" at every level, so a uniform
    "<slug>-spec" loop writes `plan-spec` into all sixteen files and the
    milestones stop being milestones — a corruption that renders perfectly.
    """

    def test_a_milestone_keeps_the_milestone_identifier(self):
        self.write_record(background="#123456")
        restyle.restyle(self.root)
        held = self.text(self.plan[1])
        self.assertIn('id="%s"' % plan.MILESTONE_SPEC_ID, held)
        self.assertNotIn('id="%s"' % plan.INDEX_SPEC_ID, held)

    def test_the_index_keeps_the_index_identifier(self):
        self.write_record(background="#123456")
        restyle.restyle(self.root)
        self.assertIn('id="%s"' % plan.INDEX_SPEC_ID, self.text(self.plan[0]))

    def test_a_specification_keeps_its_own(self):
        self.write_record(background="#123456")
        restyle.restyle(self.root)
        self.assertIn('id="vision-spec"', self.text(self.specs[0]))


# ------------------------------------------------------- refuse before writing

class TestOneUnreadableDocumentStopsTheWholeRun(Case):
    """D-06, and the house rule `plan.author` already follows: nothing on disk
    when the gate fails. A half-restyled set is worse than an unstyled one,
    because the operator cannot tell by looking which half is which.
    """

    def damage(self):
        target = paths.resolve(self.root, paths.SPECS_DIR, "Broken.html")
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("<!doctype html><html><body>no specification</body></html>")
        return target

    def test_the_run_is_refused(self):
        self.write_record(background="#123456")
        self.damage()
        with self.assertRaises(restyle.Unreadable):
            restyle.restyle(self.root)

    def test_no_document_is_written(self):
        self.write_record(background="#123456")
        before = self.bytes_now()
        self.damage()
        try:
            restyle.restyle(self.root)
        except restyle.Unreadable:
            pass
        self.assertEqual(before, self.bytes_now())

    def test_the_refusal_names_the_document(self):
        self.write_record(background="#123456")
        self.damage()
        try:
            restyle.restyle(self.root)
            self.fail("an unreadable document was not refused")
        except restyle.Unreadable as error:
            self.assertIn("Broken.html", str(error))
            self.assertIn("Nothing was written", str(error))


# ------------------------------------------------------------------ the cache

class TestTheDesignIsReadAgainAndNotRememberedFromEarlier(Case):
    """The theme is cached per project root, once, because rendering sixteen
    plan files otherwise walks the whole project sixteen times. That cache is
    exactly wrong for a command whose entire job is to pick up a design that
    changed, and the two live in the same process during `/zero:design`.
    """

    def test_a_record_written_after_the_theme_was_read_is_still_adopted(self):
        design.theme(self.root)                    # warm the cache: neutral
        design.write_record(self.root, record(background="#123456"))
        found = restyle.restyle(self.root)         # no forget() of our own
        self.assertIn("#123456", self.text(self.specs[0]))
        self.assertEqual(sorted(self.all), sorted(found.written))


# ------------------------------------------------------------------- preview

class TestCheckReportsWithoutWriting(Case):

    def test_nothing_is_written(self):
        self.write_record(background="#123456")
        before = self.bytes_now()
        found = restyle.restyle(self.root, check=True)
        self.assertEqual(sorted(self.all), sorted(found.written))
        self.assertEqual(before, self.bytes_now())

    def test_a_pending_restyle_is_not_a_failure(self):
        """It is a preview, not a gate — unlike `selfhost.build --check` and
        `z2s.pack --check`, both of which exit non-zero on a difference. A
        document waiting to be restyled is a document that is fine to read."""
        self.write_record(background="#123456")
        out = io.StringIO()
        self.assertEqual(0, restyle.main(["--check", "--root", self.root], out))
        self.assertIn("would", out.getvalue())


# -------------------------------------------------------------- the command

class TestTheCommandLine(Case):

    def run_it(self, *argv):
        out = io.StringIO()
        return restyle.main(list(argv), out), out.getvalue()

    def test_a_run_that_writes_exits_zero(self):
        self.write_record(background="#123456")
        code, said = self.run_it("--root", self.root)
        self.assertEqual(0, code)
        self.assertIn("4", said)

    def test_a_run_that_changes_nothing_exits_zero(self):
        code, said = self.run_it("--root", self.root)
        self.assertEqual(0, code)
        self.assertIn("current", said)

    def test_a_refusal_exits_one(self):
        with open(paths.resolve(self.root, paths.SPECS_DIR, "Broken.html"),
                  "w", encoding="utf-8", newline="\n") as handle:
            handle.write("<!doctype html><html></html>")
        code, said = self.run_it("--root", self.root)
        self.assertEqual(1, code)
        self.assertIn("Broken.html", said)

    def test_a_project_with_no_documents_is_refused_rather_than_called_a_success(self):
        empty = tempfile.mkdtemp(prefix="z2s-restyle-empty-")
        try:
            code, said = self.run_it("--root", empty)
            self.assertEqual(1, code)
            self.assertIn("no documents", said)
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    def test_an_unknown_argument_is_misuse(self):
        code, said = self.run_it("--nonsense")
        self.assertEqual(2, code)
        self.assertIn("usage", said)

    def test_the_usage_says_check_never_fails(self):
        """So nobody wires it into a gauntlet expecting it to catch anything."""
        self.assertIn("--check", restyle.USAGE)
        self.assertIn("never", restyle.USAGE.lower())


class TestTheModuleKeepsTheHouseGuards(unittest.TestCase):

    def source(self):
        with open(os.path.join(ROOT, "z2s", "restyle.py"), encoding="utf-8") as handle:
            return handle.read()

    def test_it_reads_documents_through_the_shared_extraction(self):
        self.assertIn("validate.extract", self.source())

    def test_it_defines_no_extraction_of_its_own(self):
        self.assertNotIn("application/json", self.source())

    def test_it_asks_the_design_module_rather_than_reading_a_stylesheet(self):
        """One ladder, in one place. A second reading of the host project here
        would be a second answer to what this project's colours are."""
        held = self.source()
        self.assertIn("design.theme", held)
        self.assertNotIn("read_stylesheet", held)


if __name__ == "__main__":
    unittest.main()
