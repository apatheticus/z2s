# -*- coding: utf-8 -*-
"""The rendered-view check (M9-P2-T1).

A document can hold a sound specification, satisfy every structural rule, and
still show a reader an empty page. Only opening it says so.

The judging half is pure — it reads what the browser reported — so most of the
rules below are checked without a browser at all. The three that genuinely need
one are grouped in `TestARealBrowser`, and the whole class is skipped, loudly,
when Playwright is not installed: a skipped check is never a pass (LD-04,
NFR-VAL-05).

Traces: FR-VAL-07, FR-GEN-03, NFR-VAL-05, NFR-ARC-03, ADR-09, US-VAL-02.
"""

import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import chain, document, render, runtime, schema, styles, tokens

from tests.test_validate import milestone_spec, task_entry

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOWHERE = "/no/such/node"


def catalogue_spec():
    """A milestone document with enough entries to narrow and enough bands to
    switch off — a catalogue of one proves nothing about a filter."""
    return milestone_spec([
        task_entry("M1-P1-T1"),
        task_entry("M1-P1-T2", title="Plan structural invariants"),
        task_entry("M1-P1-T3", priority="Should", title="Declared exceptions")])


def written(folder, name, spec, **parts):
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(document.render(spec, "plan-spec", **parts)
                     if parts else chain.render(spec, "plan-spec", ROOT))
    return path


def dressed(**overrides):
    """The shell parts, so a test can replace exactly one of them."""
    parts = {"tokens": tokens.render(tokens.NEUTRAL), "struct": styles.STRUCT,
             "runtime": runtime.SOURCE}
    parts.update(overrides)
    return parts


def report(**overrides):
    """What the browser hands back for a healthy document."""
    built = {"name": "M1.html", "errors": [], "sections": 4, "entries": 3,
             "filtered": 1, "toggled": 1, "band": "Must",
             "exercised": list(render.CONTROLS)}
    built.update(overrides)
    return built


def codes(found, severity=None):
    return sorted(one.code for one in found
                  if severity is None or one.severity == severity)


class TestWhatTheBrowserReportedMeans(unittest.TestCase):
    """The judging half, which needs no browser."""

    def test_a_healthy_document_produces_nothing(self):
        self.assertEqual([], render.judge(report()))

    def test_a_runtime_that_threw_is_a_failure(self):
        """M9-P2-T1-C1."""
        found = render.judge(report(errors=["boom"]))
        self.assertEqual(["render-error"], codes(found, schema.FAILURE))
        self.assertIn("boom", found[0].message)

    def test_a_document_that_rendered_no_sections_is_a_failure(self):
        found = render.judge(report(sections=0, entries=0))
        self.assertEqual(["render-empty"], codes(found, schema.FAILURE))

    def test_a_filter_that_narrows_nothing_is_a_failure(self):
        found = render.judge(report(filtered=3))
        self.assertEqual(["render-filter"], codes(found, schema.FAILURE))

    def test_a_filter_that_hides_everything_is_a_failure(self):
        found = render.judge(report(filtered=0))
        self.assertEqual(["render-filter"], codes(found, schema.FAILURE))

    def test_a_band_toggle_that_removes_nothing_is_a_failure(self):
        found = render.judge(report(toggled=3))
        self.assertEqual(["render-band"], codes(found, schema.FAILURE))

    def test_a_control_that_was_never_reached_is_a_failure(self):
        """M9-P2-T1-C2: all three, or the check says which one it could not
        drive. A catalogue a reader cannot narrow is a list."""
        found = render.judge(report(exercised=["entries"]))
        self.assertEqual(["render-control"], codes(found, schema.FAILURE))
        self.assertIn("filter", found[0].message)

    def test_a_document_with_no_catalogue_is_reported_as_skipped(self):
        """Most documents have no catalogue — and so does a document whose
        catalogue stopped rendering. A check that goes quiet in both cases is
        the dishonesty NFR-VAL-05 forbids."""
        found = render.judge(report(entries=0, exercised=[]))
        self.assertEqual([schema.SKIPPED], [one.severity for one in found])
        self.assertEqual(["render-view"], codes(found))

    def test_a_catalogue_with_no_priority_bands_skips_that_half_and_says_so(self):
        """A set of decisions carries a standing where a requirement carries a
        priority. There is nothing to switch off, which is not a pass."""
        found = render.judge(report(band=None, toggled=None,
                                    exercised=["entries", "filter"]))
        self.assertEqual([schema.SKIPPED], [one.severity for one in found])
        self.assertEqual(["render-band"], codes(found))


class TestWhenThereIsNoBrowser(unittest.TestCase):
    """M9-P2-T2 read from this side: what an unavailable tool must report."""

    def test_an_absent_browser_is_a_skip_with_its_reason(self):
        found = render.check(["anything.html"], node=NOWHERE)
        self.assertEqual([schema.SKIPPED], [one.severity for one in found])
        self.assertIn("node is not installed", found[0].message)

    def test_a_skip_never_fails_the_run(self):
        """LD-04: the check is optional in everyday integration, mandatory on
        promotion. Optional means a machine without a browser is not red."""
        found = render.check(["anything.html"], node=NOWHERE)
        self.assertEqual([], [one for one in found
                              if one.severity == schema.FAILURE])

    def test_an_absent_browser_is_marked_as_the_check_never_running(self):
        """The M12 correction, from the side that knows. This skip means the
        gate did not happen; the per-document skip above it means the gate ran
        and one document had nothing to exercise. A summary that cannot tell
        them apart calls a real run 'not run' (NFR-VAL-05)."""
        found = render.check(["anything.html"], node=NOWHERE)
        self.assertEqual([render.NOT_RUN], codes(found))
        self.assertFalse(render.ran(found))

    def test_a_document_with_no_catalogue_still_counts_as_a_run(self):
        self.assertTrue(render.ran(render.judge(report(entries=0, exercised=[]))))

    def test_the_command_says_what_it_skipped(self):
        out = io.StringIO()
        code = render.main(["anything.html"], out=out)
        self.assertEqual(0, code)
        self.assertIn("SKIPPED", out.getvalue())

    def test_the_command_explains_itself_when_given_nothing(self):
        self.assertEqual(2, render.main([], out=io.StringIO()))

    def test_the_reason_is_never_left_to_the_reader_to_guess(self):
        found, reason = render.drive(["a.html"], node=NOWHERE)
        self.assertEqual([], found)
        self.assertTrue(reason)


def probe():
    """One browser run against one sound document, shared by the class below."""
    folder = tempfile.mkdtemp(prefix="z2s-render-probe-")
    path = written(folder, "M1.html", catalogue_spec())
    try:
        return render.drive([path])
    except RuntimeError as error:                          # pragma: no cover
        return [], str(error)


REPORTS, REASON = probe()


@unittest.skipIf(REASON is not None, "no browser available: %s" % REASON)
class TestARealBrowser(unittest.TestCase):
    """M9-P2-T1. The three things only a browser can answer."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-render-")

    def test_a_sound_document_passes(self):
        self.assertEqual([], render.judge(REPORTS[0]))

    def test_all_three_controls_are_really_exercised(self):
        """M9-P2-T1-C2, measured rather than declared: the filter narrows the
        catalogue and switching a band off removes its entries."""
        found = REPORTS[0]
        self.assertEqual(list(render.CONTROLS), found["exercised"])
        self.assertEqual(3, found["entries"])
        self.assertEqual(1, found["filtered"])
        self.assertLess(found["toggled"], found["entries"])

    def test_a_document_whose_runtime_throws_fails_the_check(self):
        """M9-P2-T1-C1. The specification is untouched and perfectly valid; the
        page a reader opens is empty."""
        path = written(self.folder, "broken.html", catalogue_spec(),
                       **dressed(runtime="throw new Error('the runtime gave up');"))
        found = render.check([path])
        self.assertIn("render-error", codes(found, schema.FAILURE))
        self.assertIn("the runtime gave up",
                      " ".join(one.message for one in found))

    def test_a_document_with_no_runtime_at_all_fails(self):
        """Nothing renders it, so there is nothing on the page — which every
        check above this one is blind to."""
        path = written(self.folder, "bare.html", catalogue_spec(),
                       **dressed(runtime=""))
        self.assertIn("render-empty", codes(render.check([path]), schema.FAILURE))

    def test_the_check_reads_the_produced_file_and_writes_nothing(self):
        """ADR-09, NFR-DAT-05."""
        path = written(self.folder, "M1.html", catalogue_spec())
        with open(path, "rb") as handle:
            before = handle.read()
        render.check([path])
        with open(path, "rb") as handle:
            self.assertEqual(before, handle.read())
        self.assertEqual(["M1.html"], sorted(os.listdir(self.folder)))


if __name__ == "__main__":
    unittest.main()
