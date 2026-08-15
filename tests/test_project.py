# -*- coding: utf-8 -*-
"""Setup performed by the method rather than asked of the operator (M13-P1-T4).

The two properties that matter are not what init creates but how it behaves the
second time and how it behaves over somebody else's work: a second run must
change no byte, and an existing file must never be overwritten. Everything else
here is a consequence of those two.

Traces: FR-SKL-09, FR-GEN-03, NFR-SKL-04, ADR-18, US-SKL-07.
"""

import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import paths, project, writer


def tree(folder):
    """Every file under a project, with its exact contents."""
    found = {}
    for where, _, names in os.walk(folder):
        for name in sorted(names):
            path = os.path.join(where, name)
            with open(path, "rb") as handle:
                found[os.path.relpath(path, folder)] = handle.read()
    return found


class Bare(unittest.TestCase):
    """A repository with nothing in it at all."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-init-")
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)


class TestABareRepository(Bare):
    """M13-P1-T4-C1: init creates the documented layout, ignore rules and
    gauntlet record in a bare repository."""

    def test_the_documented_layout_appears(self):
        project.initialise(self.folder)
        for relative in paths.DIRECTORIES:
            self.assertTrue(os.path.isdir(paths.resolve(self.folder, relative)),
                            relative)

    def test_the_ignore_rules_appear(self):
        project.initialise(self.folder)
        self.assertTrue(os.path.exists(paths.resolve(self.folder,
                                                     paths.IGNORE_FILE)))

    def test_the_gauntlet_record_appears(self):
        done = project.initialise(self.folder)
        with open(project.workers_path(self.folder), encoding="utf-8") as handle:
            held = handle.read()
        self.assertIn("gauntlet", held)
        self.assertIn(project.DEFAULT_GAUNTLET["CI"], held)
        self.assertIn(paths.WORKERS_FILE, done["created"])

    def test_the_probe_says_a_bare_repository_needs_setting_up(self):
        self.assertTrue(project.needs_setup(self.folder))
        project.initialise(self.folder)
        self.assertFalse(project.needs_setup(self.folder))

    def test_what_is_still_outstanding_is_named_rather_than_filled_in(self):
        """A recorded command nobody chose is worse than an absent one: it
        passes, and the passing means nothing."""
        done = project.initialise(self.folder)
        self.assertTrue(done["outstanding"])
        stated = " ".join(done["outstanding"])
        self.assertIn("/zero:build", stated)
        self.assertIn("workers", stated)

    def test_the_worker_list_is_left_empty_on_purpose(self):
        self.assertEqual([], project.STARTER["workers"])


class TestRunningItTwice(Bare):
    """M13-P1-T4-C2: a second init run changes nothing.

    This is what lets every chain skill call it whenever it finds setup missing,
    without anybody having to track whether it has already happened.
    """

    def test_a_second_run_changes_no_byte(self):
        project.initialise(self.folder)
        before = tree(self.folder)
        project.initialise(self.folder)
        self.assertEqual(before, tree(self.folder))

    def test_a_second_run_creates_nothing_and_says_so(self):
        project.initialise(self.folder)
        done = project.initialise(self.folder)
        self.assertEqual([], done["created"])
        self.assertIn("setup was already complete",
                      project.format_report(done))

    def test_a_second_run_is_not_an_error(self):
        out = io.StringIO()
        self.assertEqual(0, project.main(["--root", self.folder], out))
        self.assertEqual(0, project.main(["--root", self.folder], io.StringIO()))


class TestItNeverOverwrites(Bare):
    """An existing ignore file may carry a project's own rules and an existing
    worker record may carry its real commands. Both are somebody's work."""

    def test_an_existing_ignore_file_is_left_exactly_as_found(self):
        os.makedirs(paths.resolve(self.folder, paths.ROOT))
        mine = "state/\n# and my own rule\nscratch/\n"
        writer.write(paths.resolve(self.folder, paths.IGNORE_FILE), mine)
        project.initialise(self.folder)
        with open(paths.resolve(self.folder, paths.IGNORE_FILE),
                  encoding="utf-8") as handle:
            self.assertEqual(mine, handle.read())

    def test_an_existing_worker_record_is_left_exactly_as_found(self):
        os.makedirs(paths.resolve(self.folder, paths.ROOT))
        mine = '{"workers": [{"name": "real"}], "gauntlet": {"unit": "make test"}}\n'
        writer.write(project.workers_path(self.folder), mine)
        done = project.initialise(self.folder)
        with open(project.workers_path(self.folder), encoding="utf-8") as handle:
            self.assertEqual(mine, handle.read())
        self.assertIn(paths.WORKERS_FILE, done["existed"])
        self.assertEqual([], done["outstanding"])


class TestTheReport(Bare):
    """FR-GEN-03: a setup step that claims work it did not do is the same
    dishonesty a skipped gate reported as passed would be."""

    def test_created_and_present_are_reported_apart(self):
        found = project.format_report(project.initialise(self.folder))
        self.assertIn("created  %s" % paths.ROOT, found)
        again = project.format_report(project.initialise(self.folder))
        self.assertIn("present  %s" % paths.ROOT, again)
        self.assertNotIn("created", again)

    def test_the_design_system_is_named_or_its_absence_is(self):
        found = project.format_report(project.initialise(self.folder))
        self.assertIn("no design system found", found)

    def test_a_design_system_that_is_there_is_named(self):
        writer.write(os.path.join(self.folder, "theme.css"), """
            :root { --color-background: #101014; --color-text: #f4f4f6;
                    --color-accent: #7aa2f7; --font-family: Inter, sans-serif;
                    --color-border: #2a2a33; --border-radius: 6px; }""")
        found = project.format_report(project.initialise(self.folder))
        self.assertIn("theme.css", found)

    def test_the_command_explains_itself_when_given_nonsense(self):
        out = io.StringIO()
        self.assertEqual(2, project.main(["--wat"], out))
        self.assertIn("usage:", out.getvalue())


if __name__ == "__main__":
    unittest.main()
