# -*- coding: utf-8 -*-
"""Every gate in one run, reported honestly (M9-P2-T2, M9-P2-T3).

The failure this file guards against is not a red build. It is a green one: a
check that could not run, quietly folded into a pass count, so a reader is told
something was proved when nothing was.

M16-P3-T2 adds the design gate to the same rules: a stale record warns, an
unreadable one fails, and a project that records none has the gate reported as
not run rather than counted as a pass — because "the recorded design is current"
is not something a project without a record has proved.

Traces: FR-GEN-03, FR-GEN-11, FR-DOC-06, FR-VAL-05, NFR-PRF-01, NFR-VAL-05,
NFR-VAL-06, NFR-DAT-05, US-VAL-01, US-VAL-02, US-GEN-03.
"""

import glob
import io
import os
import shutil
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import chain, design, paths, pipeline, render, schema, shell, status, validate

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
        # Two gates cannot answer here and both say so: no browser on this
        # machine, and this fixture is a bare directory with no design record.
        self.assertIn("not run: view, design", text)
        self.assertIn("gates: 4 passed · 0 failed · 2 skipped", text)

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



class TestTheSizeBudgetIsMeasuredOnEveryRun(unittest.TestCase):
    """M14-05. `shell.budget_report` existed from M1 and nothing called it, so
    a project could ship a document of any size and hear nothing. A budget
    nobody measures is a comment."""

    def setUp(self):
        self.holder = tempfile.mkdtemp(prefix="z2s-budget-")

    def tearDown(self):
        shutil.rmtree(self.holder, ignore_errors=True)

    def _document(self, name, size):
        path = os.path.join(self.holder, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("x" * size)
        return path

    def test_a_document_over_the_budget_is_reported(self):
        found = pipeline.sizes([self._document("huge.html", shell.SIZE_BUDGET + 4096)])
        self.assertEqual(1, len(found))
        self.assertEqual(schema.WARNING, found[0].severity)
        self.assertIn("huge.html", found[0].message)
        self.assertIn("split", found[0].message)

    def test_a_document_inside_the_budget_is_not(self):
        self.assertEqual([], pipeline.sizes([self._document("small.html", 64)]))

    def test_a_small_overage_never_reports_as_nothing(self):
        """"exceeds the budget by 0 KB" reads as a bug in the checker."""
        found = pipeline.sizes([self._document("just.html", shell.SIZE_BUDGET + 10)])
        self.assertNotIn(" by 0 KB", found[0].message)

    def test_the_whole_run_carries_the_measurement(self):
        """Wired into `run`, not merely available: the mutation that removed it
        from the budgets stage survived every other test in this module."""
        over = self._document("huge.html", shell.SIZE_BUDGET + 4096)
        stages = pipeline.run([over])
        budgets = [one for one in stages if one.name == "budgets"][0]
        self.assertTrue([one for one in budgets.findings
                         if one.code == "budget" and "huge.html" in one.message],
                        "the budgets gate did not measure the document size")

    def test_a_file_that_cannot_be_read_is_left_to_the_generation_gate(self):
        self.assertEqual([], pipeline.sizes([os.path.join(self.holder, "absent.html")]))


class TestTheDesignRecordIsChecked(unittest.TestCase):
    """M16-P3-T2-C2. The gate the project already runs says when the theme has
    moved on, so nobody has to remember to ask."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-design-gate-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.addCleanup(design.forget)
        design.forget()
        self.source = os.path.join(self.root, "tokens.css")
        with open(self.source, "w", encoding="utf-8") as handle:
            handle.write(":root{--surface-page:#fff;--text-body:#111}\n")

    def record(self, **extra):
        held = {"version": design.RECORD_VERSION, "scheme": "light",
                "tokens": {"surface-page": {"light": "#fff",
                                            "from": "tokens.css --surface-page"}},
                "sources": [{"path": "tokens.css", "kind": "css",
                             "sha256": design.digest(self.source), "mapped": 4,
                             "role": "base"}]}
        held.update(extra)
        design.write_record(self.root, held)
        return held

    def move(self):
        with open(self.source, "a", encoding="utf-8") as handle:
            handle.write(":root{--text-body:#222}\n")

    def test_a_current_record_says_nothing(self):
        self.record()
        self.assertEqual([], pipeline.adoption(self.root))

    def test_a_changed_source_is_a_warning_and_names_the_file(self):
        self.record()
        self.move()
        found = pipeline.adoption(self.root)
        self.assertEqual(1, len(found))
        self.assertEqual(schema.WARNING, found[0].severity)
        self.assertIn("tokens.css", found[0].message)

    def test_a_stale_record_does_not_fail_the_build(self):
        """The documents carry a design somebody chose; they carry a slightly
        old one. Stopping the build over it would make the gate the thing people
        route around."""
        self.record()
        self.move()
        stages = [stage("design", *pipeline.adoption(self.root))]
        self.assertEqual(pipeline.PASSED, pipeline.state(stages[0]))
        self.assertEqual(0, pipeline.exit_code(stages))

    def test_an_unreadable_record_fails_rather_than_warns(self):
        """Different question, different answer. Stale means the record
        disagrees with its sources; damaged means every operator value in it is
        being ignored while documents are reported as fine."""
        self.record()
        with open(design.record_path(self.root), "w", encoding="utf-8") as handle:
            handle.write("{ not json at all")
        found = pipeline.adoption(self.root)
        self.assertEqual(schema.FAILURE, found[0].severity)
        self.assertEqual(1, pipeline.exit_code([stage("design", *found)]))

    def test_a_record_with_no_tokens_block_is_unreadable_too(self):
        design.write_record(self.root, {"version": 1, "sources": []})
        self.assertEqual(schema.FAILURE, pipeline.adoption(self.root)[0].severity)

    def test_a_project_with_no_record_has_the_gate_reported_as_not_run(self):
        """Not a pass. Saying the recorded design is current in a project that
        records none is the confident false green this whole module is about."""
        found = pipeline.adoption(self.root)
        self.assertEqual([schema.SKIPPED], [one.severity for one in found])
        stages = [unrun("design", *found)]
        self.assertEqual(pipeline.SKIPPED, pipeline.state(stages[0]))
        self.assertIn("not run: design", pipeline.format_report(stages))

    def test_the_gate_says_how_to_write_the_record_it_is_missing(self):
        self.assertIn("/zero:design", pipeline.adoption(self.root)[0].message)

    def test_the_gate_is_wired_into_the_run_not_merely_available(self):
        """The mutation that removed `sizes` from the budgets stage survived
        every other test in this module; the same mutation is available here."""
        self.record()
        self.move()
        holder = tempfile.mkdtemp(prefix="z2s-design-docs-")
        self.addCleanup(shutil.rmtree, holder, ignore_errors=True)
        stages = pipeline.run([], root=self.root)
        named = [one for one in stages if one.name == "design"]
        self.assertEqual(1, len(named), "the run has no design gate")
        self.assertTrue([one for one in named[0].findings
                         if one.code == "design-stale"],
                        "the design gate ran but reported no staleness")

    def test_a_run_over_a_project_with_a_record_reports_the_gate_as_having_run(self):
        self.record()
        stages = pipeline.run([], root=self.root)
        named = [one for one in stages if one.name == "design"][0]
        self.assertTrue(named.ran)
        self.assertEqual(pipeline.PASSED, pipeline.state(named))

    def test_the_gate_writes_nothing(self):
        self.record()
        before = sorted(os.listdir(os.path.dirname(design.record_path(self.root))))
        pipeline.adoption(self.root)
        self.assertEqual(before, sorted(
            os.listdir(os.path.dirname(design.record_path(self.root)))))


if __name__ == "__main__":
    unittest.main()


class TestTheGateAProjectRunsOverItself(unittest.TestCase):
    """`--record <root>` with nothing else named.

    The shape a new project's default gauntlet is written in, and the only shape
    that can be written down before the project has any documents to name. It
    used to take the root as the last word, leave no sources, print usage and
    exit 2 — so the CI layer a fresh project was handed could never go green.
    """

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-pipeline-project-")
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)
        paths.ensure_layout(self.folder)
        self.real = render.check
        render.check = lambda sources, node=None: [
            schema.Finding(schema.SKIPPED, render.NOT_RUN, "every document",
                           "the rendered view was not checked")]
        self.addCleanup(setattr, render, "check", self.real)

    def write(self, where, name, built):
        path = paths.resolve(self.folder, where, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(chain.render(built, "plan-spec", ROOT))
        return path

    def fill(self):
        self.write(paths.SPECS_DIR, "FSD.html", document_spec(identifier="FR-VAL-02"))
        self.write(paths.PLAN_DIR, "M1-toolchain.html", milestone_spec())
        self.write(paths.PLAN_DIR, "index.html", index_spec())

    def test_it_finds_the_projects_own_documents(self):
        self.fill()
        self.assertEqual(3, len(paths.documents(self.folder)))
        out = io.StringIO()
        code = pipeline.main(["--record", self.folder], out=out)
        self.assertEqual(0, code, out.getvalue())
        self.assertNotIn("usage:", out.getvalue())

    def test_it_records_the_layer_it_ran(self):
        self.fill()
        pipeline.main(["--record", self.folder], out=io.StringIO())
        held = status.evidence(self.folder)
        self.assertTrue(held[pipeline.RECORDED_LAYER]["passed"])

    def test_a_project_with_no_documents_yet_says_so_rather_than_printing_usage(self):
        out = io.StringIO()
        self.assertEqual(2, pipeline.main(["--record", self.folder], out=out))
        self.assertIn("no documents yet", out.getvalue())
        self.assertNotIn("usage:", out.getvalue())

    def test_naming_documents_still_overrides_the_discovery(self):
        self.fill()
        named = [paths.resolve(self.folder, paths.SPECS_DIR, "FSD.html")]
        out = io.StringIO()
        pipeline.main(["--record", self.folder] + named, out=out)
        # Only the requirements document was read, so its requirement is
        # unclaimed. Had discovery run anyway, the plan would have claimed it.
        self.assertIn("is claimed by no unit of work", out.getvalue())

    def test_the_default_gauntlet_a_new_project_is_given_is_this_command(self):
        """Read from `project`, so the two cannot drift apart."""
        from z2s import project
        self.assertEqual(["python3", "-m", "z2s.pipeline", "--record", "."],
                         project.DEFAULT_GAUNTLET["CI"])
