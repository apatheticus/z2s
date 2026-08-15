# -*- coding: utf-8 -*-
"""M1-P1-T3 — deterministic, atomic writes.

Covers criteria:
  M1-P1-T3-C1  Two consecutive generations produce identical bytes.
  M1-P1-T3-C2  A failed generation leaves the previous file byte-identical.

A half-written document is worse than no document: it parses as nothing, and it
replaces something that worked. So the failure path is tested by actually making
the write fail, not by trusting that it would behave.
"""

import os
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import document, paths, writer

PACKAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "z2s")

SPEC = {"title": "Determinism", "sections": [{"id": "s1", "body": ["one", "two"]}]}


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


class Sandbox(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="z2s-writer-")
        self.target = os.path.join(self.dir, "Doc.html")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class TestDeterminism(Sandbox):

    def test_two_generations_produce_identical_bytes(self):
        """M1-P1-T3-C1"""
        writer.write(self.target, document.render(SPEC, "spec"))
        first = read_bytes(self.target)
        writer.write(self.target, document.render(SPEC, "spec"))
        self.assertEqual(first, read_bytes(self.target))

    def test_key_order_in_the_source_does_not_change_output(self):
        """Unordered iteration order must not reach the artefact (NFR-GEN-01)."""
        a = document.render({"b": 2, "a": 1}, "spec")
        b = document.render({"a": 1, "b": 2}, "spec")
        self.assertEqual(a, b)

    def test_line_endings_are_fixed(self):
        """Byte-identical across platforms means newlines are not negotiable."""
        writer.write(self.target, "one\ntwo\n")
        self.assertEqual(b"one\ntwo\n", read_bytes(self.target))


class TestAtomicity(Sandbox):

    def setUp(self):
        super().setUp()
        writer.write(self.target, document.render(SPEC, "spec"))
        self.original = read_bytes(self.target)

    def test_failure_at_the_swap_leaves_the_previous_file_intact(self):
        """M1-P1-T3-C2 — the rename itself fails."""
        with mock.patch.object(writer.os, "replace",
                               side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                writer.write(self.target, "REPLACEMENT CONTENT")
        self.assertEqual(self.original, read_bytes(self.target))

    def test_failure_while_writing_leaves_the_previous_file_intact(self):
        """M1-P1-T3-C2 — content production fails part-way through."""
        exploding = mock.MagicMock()
        exploding.__str__ = mock.Mock(side_effect=ValueError("bad spec"))
        with self.assertRaises((ValueError, TypeError)):
            writer.write(self.target, exploding)
        self.assertEqual(self.original, read_bytes(self.target))

    def test_no_temporary_file_is_left_behind_after_a_failure(self):
        with mock.patch.object(writer.os, "replace",
                               side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                writer.write(self.target, "REPLACEMENT CONTENT")
        leftovers = [n for n in os.listdir(self.dir) if n != "Doc.html"]
        self.assertEqual([], leftovers, "a temporary file survived the failure")

    def test_a_successful_write_replaces_the_content(self):
        """The guard must not be so cautious that nothing ever changes."""
        writer.write(self.target, "NEW")
        self.assertEqual(b"NEW", read_bytes(self.target))


class TestNoGeneratorWritesDirectly(unittest.TestCase):
    """Refactor step: one write helper, and no way around it."""

    def sources(self):
        for name in sorted(os.listdir(PACKAGE)):
            if name.endswith(".py") and name != "writer.py":
                path = os.path.join(PACKAGE, name)
                with open(path, encoding="utf-8") as fh:
                    yield name, fh.read()

    def test_only_the_writer_opens_files_for_writing(self):
        offenders = [n for n, src in self.sources()
                     if re.search(r"open\([^)]*[\"'][wax]", src)]
        self.assertEqual([], offenders,
                         "these modules write files directly instead of going "
                         "through z2s.writer")

    def test_no_module_reads_the_clock_or_a_random_source(self):
        """NFR-GEN-01 states this outright; a test makes it stay true.

        `pipeline.py` is exempt and is the only exemption: it measures how long
        the gates took against a stated budget (M9-P2-T3), which is a clock
        reading by definition. It builds no document — a separate test asserts a
        run writes nothing — so no elapsed time can reach an artefact.
        """
        banned = re.compile(r"\b(?:import\s+(?:random|time)\b"
                            r"|datetime\.now|time\.time|random\.|uuid[14])")
        offenders = [n for n, src in self.sources()
                     if banned.search(src) and n != "pipeline.py"]
        self.assertEqual([], offenders,
                         "generation must not depend on the clock or randomness")


class TestLayoutUsesTheWriter(unittest.TestCase):
    """paths.ensure_layout writes an ignore file; it must not do so by hand."""

    def test_ignore_file_is_still_written_correctly(self):
        root = tempfile.mkdtemp(prefix="z2s-layout-writer-")
        try:
            paths.ensure_layout(root)
            with open(os.path.join(root, paths.IGNORE_FILE), "rb") as fh:
                body = fh.read()
            self.assertIn(b"state/", body)
            self.assertNotIn(b"\r\n", body)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
