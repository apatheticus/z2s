# -*- coding: utf-8 -*-
"""Every gate in one run, reported honestly (M9-P2-T2, M9-P2-T3).

The failure this file guards against is not a red build. It is a green one: a
check that could not run, quietly folded into a pass count, so a reader is told
something was proved when nothing was.

Traces: FR-GEN-03, FR-DOC-06, FR-VAL-05, NFR-PRF-01, NFR-VAL-05, NFR-VAL-06,
NFR-DAT-05, US-VAL-01, US-VAL-02.
"""

import glob
import io
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import chain, pipeline, render, schema, status, validate

from tests.test_validate import index_spec, milestone_spec, task_entry
from tests.test_validate import spec as document_spec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLISHED = sorted(glob.glob(os.path.join(ROOT, "docs", "*.html")))


def stage(name, *findings, **kwargs):
    return pipeline.Stage(name, list(findings), kwargs.get("seconds", 0.0),
                          kwargs.get("ran", True))


def unrun(name, *findings, **kwargs):
    """A gate that never happened — the browser gate with no browser."""
    kwargs["ran"] = False
    return stage(name, *findings, **kwargs)


def failure(code="broken"):
    return schema.Finding(schema.FAILURE, code, "somewhere", "it broke")


def skip(code=render.NOT_RUN):
    return schema.Finding(schema.SKIPPED, code, "every document",
                          "no browser was installed")


def partial(code="render-view"):
    """A skip from a gate that DID run: one document with no catalogue."""
    return schema.Finding(schema.SKIPPED, code, "Vision.html",
                          "renders 6 sections and no catalogue")


def warning(code="plan-exception"):
    return schema.Finding(schema.WARNING, code, "M1-P1-T1", "excused the layer rule")


class TestASkipIsNeverAPass(unittest.TestCase):
    """M9-P2-T2. FR-GEN-03, NFR-VAL-05."""

    def test_a_gate_that_only_skipped_is_reported_as_skipped(self):
        self.assertEqual(pipeline.SKIPPED, pipeline.state(unrun("view", skip())))

    def test_a_gate_that_found_nothing_passed(self):
        self.assertEqual(pipeline.PASSED, pipeline.state(stage("validation")))

    def test_a_gate_with_a_failure_failed_whatever_else_it_found(self):
        self.assertEqual(pipeline.FAILED,
                         pipeline.state(unrun("view", skip(), failure())))

    def test_a_skipped_gate_is_excluded_from_the_pass_count(self):
        """M9-P2-T2-C2. The whole point: three of four is not four."""
        gates, _ = pipeline.counts([stage("generation"), stage("validation"),
                                    stage("coverage"), unrun("view", skip())])
        self.assertEqual(3, gates[pipeline.PASSED])
        self.assertEqual(1, gates[pipeline.SKIPPED])
        self.assertEqual(0, gates[pipeline.FAILED])

    def test_the_summary_names_the_gate_that_did_not_run(self):
        """M9-P2-T2-C1: reported as skipped, with its reason."""
        text = pipeline.format_report([stage("validation"), unrun("view", skip())])
        self.assertIn("no browser was installed", text)
        self.assertIn("not run: view", text)
        self.assertIn("1 skipped", text)

    def test_gates_and_findings_are_counted_apart(self):
        """One gate can hold several findings; conflating the two is how a
        summary ends up claiming more was checked than was."""
        gates, severities = pipeline.counts(
            [stage("validation", warning(), warning()), unrun("view", skip())])
        self.assertEqual(1, gates[pipeline.PASSED])
        self.assertEqual(2, severities[schema.WARNING])
        self.assertEqual(1, severities[schema.SKIPPED])

    def test_a_skip_alone_does_not_fail_the_build(self):
        self.assertEqual(0, pipeline.exit_code([unrun("view", skip())]))


class TestAGateThatRanIsNotReportedAsSkipped(unittest.TestCase):
    """The M12 correction. NFR-VAL-05 cuts both ways: calling a check that
    really drove documents "not run" is as false as calling an unrun one
    passed, and it is the reading that gets a real regression ignored."""

    def test_a_gate_that_drove_and_found_only_partial_skips_passed(self):
        self.assertEqual(pipeline.PASSED,
                         pipeline.state(stage("view", partial(), partial())))

    def test_the_summary_says_the_gate_ran_and_names_what_it_could_not_reach(self):
        text = pipeline.format_report(
            [stage("validation"), stage("view", partial(), partial())])
        self.assertNotIn("not run: view", text)
        self.assertIn("partly run: view (2 checks skipped)", text)
        self.assertIn("2 skipped", text)

    def test_a_gate_that_drove_everything_cleanly_is_not_named_at_all(self):
        text = pipeline.format_report([stage("validation"), stage("view")])
        self.assertNotIn("partly run", text)
        self.assertNotIn("not run", text)

    def test_the_browser_gate_answers_for_itself_whether_it_ran(self):
        """The fact lives where it is known. A per-document skip is a real
        run; only the whole-set skip means the check never happened."""
        self.assertFalse(render.ran([skip()]))
        self.assertTrue(render.ran([partial(), partial()]))
        self.assertTrue(render.ran([]))

    def test_a_failure_anywhere_fails_the_build(self):
        self.assertEqual(1, pipeline.exit_code(
            [stage("validation"), stage("view", failure())]))


class TestTheTimeBudgets(unittest.TestCase):
    """M9-P2-T3. NFR-PRF-01, NFR-VAL-06, and the numbers from M9-02."""

    def test_the_budgets_are_the_ones_the_gate_settled_on(self):
        self.assertEqual(10.0, pipeline.BUDGETS["generation"])
        self.assertEqual(5.0, pipeline.BUDGETS["validation"])

    def test_generation_over_its_budget_fails(self):
        """M9-P2-T3-C1."""
        found = pipeline.budgets([stage("generation", seconds=11.0)])
        self.assertEqual(["budget"], [one.code for one in found])
        self.assertEqual("generation", found[0].where)

    def test_validation_over_its_budget_fails(self):
        """M9-P2-T3-C2, counted across every gate that reads the documents."""
        found = pipeline.budgets([stage("validation", seconds=3.0),
                                  stage("coverage", seconds=2.5)])
        self.assertEqual(["budget"], [one.code for one in found])
        self.assertEqual("validation", found[0].where)

    def test_the_browser_is_outside_the_validation_budget(self):
        """A budget that a machine with a browser installed always breaks is a
        budget nobody keeps."""
        self.assertEqual([], pipeline.budgets([stage("view", seconds=60.0)]))

    def test_both_timings_are_in_the_summary(self):
        text = pipeline.format_report([stage("generation", seconds=0.5),
                                       stage("validation", seconds=0.25)])
        self.assertIn("generation: 0.50s of a 10.0s budget", text)
        self.assertIn("validation: 0.25s of a 5.0s budget", text)

    @unittest.skipIf(not PUBLISHED, "no published document set in this checkout")
    def test_a_real_document_set_stays_inside_both_budgets(self):
        """Measured against the real set rather than a fixture: a budget proved
        on three tiny documents is not a budget."""
        started = time.time()
        self.assertEqual([], pipeline.regenerate(PUBLISHED, ROOT))
        building = time.time() - started

        started = time.time()
        validate.validate_set(PUBLISHED)
        checking = time.time() - started

        self.assertLess(building, pipeline.BUDGETS["generation"])
        self.assertLess(checking, pipeline.BUDGETS["validation"])


class TestRegeneratingFromTheDocumentItself(unittest.TestCase):
    """M9-P2-T3's generation half is a check as well as a measurement."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-pipeline-")

    def written(self, name, spec):
        path = os.path.join(self.folder, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(chain.render(spec, "plan-spec", ROOT))
        return path

    def test_a_document_rebuilds_into_the_specification_it_carries(self):
        """FR-DOC-06, ADR-02: the document is its own source."""
        self.assertEqual([], pipeline.regenerate(
            [self.written("M1.html", milestone_spec())], ROOT))

    def test_a_document_whose_specification_cannot_be_read_is_named(self):
        path = self.written("M1.html", milestone_spec())
        with open(path, encoding="utf-8") as handle:
            html = handle.read()
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(html.replace('"schemaVersion"', '"schemaVersion', 1))
        found = pipeline.regenerate([path], ROOT)
        self.assertEqual(["regeneration"], [one.code for one in found])
        self.assertIn("M1.html", found[0].message)

    def test_a_document_that_rebuilds_into_something_else_is_named(self):
        """A round trip rather than a render: a rebuild that quietly loses part
        of the specification is worse than one that fails, because the next
        person to regenerate the document is the one who finds out."""
        path = self.written("M1.html", milestone_spec())
        lossy = milestone_spec([])
        lossy["sections"][0]["items"] = [task_entry("M1-P1-T9")]
        original = pipeline.chain.render
        pipeline.chain.render = lambda spec, spec_id, root=".": original(
            lossy, spec_id, root)
        try:
            found = pipeline.regenerate([path], ROOT)
        finally:
            pipeline.chain.render = original
        self.assertEqual(["regeneration"], [one.code for one in found])
        self.assertIn("different specification", found[0].message)

    def test_a_file_that_is_not_there_is_named_rather_than_traced_back(self):
        found = pipeline.regenerate([os.path.join(self.folder, "absent.html")], ROOT)
        self.assertEqual(["regeneration"], [one.code for one in found])

    def test_a_run_writes_nothing(self):
        """NFR-DAT-05: the pipeline judges the files, it does not touch them."""
        path = self.written("M1.html", milestone_spec())
        with open(path, "rb") as handle:
            before = handle.read()
        pipeline.regenerate([path], ROOT)
        with open(path, "rb") as handle:
            self.assertEqual(before, handle.read())
        self.assertEqual(["M1.html"], sorted(os.listdir(self.folder)))


class TestOneRunOverOneSet(unittest.TestCase):
    """The command, end to end, with the browser deliberately unavailable."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-pipeline-run-")
        self.real = render.check
        render.check = lambda sources, node=None: [
            schema.Finding(schema.SKIPPED, render.NOT_RUN, "every document",
                           "the rendered view was not checked: node is not "
                           "installed")]

    def tearDown(self):
        render.check = self.real

    def documents(self, milestone=None):
        """A whole small set: the requirements a plan claims, and the plan."""
        paths = []
        for name, built in (("FSD.html", document_spec(identifier="FR-VAL-02")),
                            ("M1-toolchain.html",
                             milestone_spec() if milestone is None else milestone),
                            ("index.html", index_spec())):
            path = os.path.join(self.folder, name)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(chain.render(built, "plan-spec", ROOT))
            paths.append(path)
        return paths

    def test_a_sound_set_passes_with_the_browser_gate_reported_as_skipped(self):
        """The whole point of M9-P2-T2: green, and honest about what is missing."""
        out = io.StringIO()
        code = pipeline.main(self.documents(), out=out)
        text = out.getvalue()
        self.assertEqual(0, code, text)
        self.assertIn("not run: view", text)
        self.assertIn("node is not installed", text)
        self.assertIn("gates: 4 passed · 0 failed · 1 skipped", text)

    def test_a_hole_in_the_plan_fails_the_run(self):
        without = task_entry()
        del without["status"]
        out = io.StringIO()
        code = pipeline.main(self.documents(milestone_spec([without])), out=out)
        self.assertEqual(1, code)
        self.assertIn("plan-status", out.getvalue())

    def test_the_command_explains_itself_when_given_nothing(self):
        self.assertEqual(2, pipeline.main([], out=io.StringIO()))

    def test_the_run_leaves_its_evidence_behind_when_asked(self):
        """M10-02: the checker writes the record, not the unit claiming to be
        finished. FR-STA-03 / NFR-EXE-10 lean on this being what actually ran."""
        sources = self.documents()
        code = pipeline.main(sources + ["--record", self.folder], out=io.StringIO())
        self.assertEqual(0, code)
        held = status.evidence(self.folder)[pipeline.RECORDED_LAYER]
        self.assertTrue(held["passed"])
        self.assertIn("z2s.pipeline", held["command"])

    def test_a_failed_run_is_recorded_as_failed(self):
        without = task_entry()
        del without["status"]
        sources = self.documents(milestone_spec([without]))
        pipeline.main(sources + ["--record", self.folder], out=io.StringIO())
        self.assertFalse(
            status.evidence(self.folder)[pipeline.RECORDED_LAYER]["passed"])

    def test_a_run_records_nothing_unless_it_is_asked_to(self):
        pipeline.main(self.documents(), out=io.StringIO())
        self.assertEqual({}, status.evidence(self.folder))

    def test_the_option_does_not_eat_a_document(self):
        rest, project = pipeline.recording(["--record", "a.html", "b.html"])
        self.assertEqual(["a.html", "b.html"], rest)
        self.assertEqual(".", project)

    def test_the_allowlist_reaches_the_validator_through_the_pipeline(self):
        sources, allowed = validate.allowlist(["--allow", "a.py", "doc.html"])
        self.assertEqual(["doc.html"], sources)
        self.assertEqual(["a.py"], allowed)


if __name__ == "__main__":
    unittest.main()
