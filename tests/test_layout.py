# -*- coding: utf-8 -*-
"""M1-P1-T1 — repository layout and ignore policy.

Covers criteria:
  M1-P1-T1-C1  Every documented path exists.
  M1-P1-T1-C2  The ledger path is ignored; the generated plan path is tracked.

The ignore assertions ask git itself rather than reading the ignore file, because
the question is what git actually does with the path, not what a rule looks like.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import paths


def git(root, *args):
    return subprocess.run(["git", "-C", root] + list(args),
                          capture_output=True, text=True)


def is_ignored(root, relpath):
    """True when git would refuse to track relpath."""
    return git(root, "check-ignore", "-q", "--no-index", relpath).returncode == 0


class BareProject(unittest.TestCase):
    """A throwaway git repository standing in for a host project."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-layout-")
        git(self.root, "init", "-q", "-b", "main")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)


class TestDocumentedPathsExist(BareProject):

    def test_every_documented_directory_exists(self):
        """M1-P1-T1-C1"""
        paths.ensure_layout(self.root)
        missing = [d for d in paths.DIRECTORIES
                   if not os.path.isdir(os.path.join(self.root, d))]
        self.assertEqual([], missing, "documented directories were not created")

    def test_layout_is_declared_once(self):
        """Refactor step: tests and generators read the same constant.

        Every directory the method owns must sit under the single root name, so
        a path is never spelled twice.
        """
        self.assertTrue(paths.DIRECTORIES, "DIRECTORIES must not be empty")
        for d in paths.DIRECTORIES:
            self.assertTrue(d == paths.ROOT or d.startswith(paths.ROOT + "/"),
                            "%s is outside the declared root %s" % (d, paths.ROOT))

    def test_running_twice_changes_nothing(self):
        """Setup is re-runnable; M13-P1-T4 later depends on this being true."""
        paths.ensure_layout(self.root)
        before = snapshot(self.root)
        paths.ensure_layout(self.root)
        self.assertEqual(before, snapshot(self.root),
                         "a second run of ensure_layout changed the tree")


class TestIgnorePolicy(BareProject):

    def test_ledger_is_ignored(self):
        """M1-P1-T1-C2, first half."""
        paths.ensure_layout(self.root)
        self.assertTrue(is_ignored(self.root, paths.LEDGER_DIR + "/z2s.md"),
                        "the run ledger must be excluded from version control "
                        "(NFR-OPS-04)")

    def test_generated_plan_documents_are_tracked(self):
        """M1-P1-T1-C2, second half — ADR-11's deliberate exception."""
        paths.ensure_layout(self.root)
        for generated in (paths.PLAN_DIR + "/index.html",
                          paths.PLAN_DIR + "/M1-foundations.html",
                          paths.SPECS_DIR + "/FSD.html"):
            self.assertFalse(is_ignored(self.root, generated),
                             "%s is generated but must still be committed "
                             "(ADR-11)" % generated)

    def test_ignore_file_documents_the_exception(self):
        """ADR-11: the exception is documented where the ignore rules live."""
        paths.ensure_layout(self.root)
        with open(os.path.join(self.root, paths.IGNORE_FILE), encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn("hand-edit", body,
                      "contributors must be told not to hand-edit generated "
                      "plan documents, where the ignore rules live")


def snapshot(root):
    """Every file under root, with its bytes — for change detection."""
    out = {}
    for base, dirs, files in os.walk(root):
        if ".git" in dirs:
            dirs.remove(".git")
        for name in files:
            p = os.path.join(base, name)
            with open(p, "rb") as fh:
                out[os.path.relpath(p, root)] = fh.read()
    return out


if __name__ == "__main__":
    unittest.main(verbosity=2)
