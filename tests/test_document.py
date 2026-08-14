# -*- coding: utf-8 -*-
"""M1-P1-T2 — minimal generator: specification object to file.

Covers criteria:
  M1-P1-T2-C1  The emitted file contains exactly one embedded specification block.
  M1-P1-T2-C2  The block parses as a single JSON object.

The generator is the contract every other tool in the method reads (FR-SPC-01),
so these tests treat the emitted text as an artefact to be parsed, never as a
string to be pattern-matched loosely.
"""

import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import document

TWO_FIELD = {"title": "A tiny document", "sections": []}

BLOCK = re.compile(
    r'<script\s+type="application/json"\s+id="([^"]+)"\s*>(.*?)</script>',
    re.S)


def blocks(html):
    """Every embedded JSON block in the emitted file, as (id, raw text)."""
    return BLOCK.findall(html)


class TestEmbeddedBlock(unittest.TestCase):

    def setUp(self):
        self.html = document.render(TWO_FIELD, "tiny-spec")

    def test_exactly_one_specification_block(self):
        """M1-P1-T2-C1"""
        self.assertEqual(1, len(blocks(self.html)))

    def test_block_carries_the_requested_identifier(self):
        """FR-SPC-01 — a stable, document-type-specific element identifier."""
        self.assertEqual("tiny-spec", blocks(self.html)[0][0])

    def test_block_parses_as_a_single_json_object(self):
        """M1-P1-T2-C2"""
        parsed = json.loads(blocks(self.html)[0][1])
        self.assertIsInstance(parsed, dict)
        self.assertEqual("A tiny document", parsed["title"])
        self.assertEqual([], parsed["sections"])

    def test_emitted_file_is_a_complete_document(self):
        """FR-SPC-03 — one file that opens with no build step."""
        self.assertTrue(self.html.startswith("<!doctype html>"))
        self.assertTrue(self.html.rstrip().endswith("</html>"))


class TestContentCannotBreakTheContainer(unittest.TestCase):
    """Authored data is arbitrary. It must never be able to alter the file
    around it — FR-GEN-01 forbids assumptions about the host project's domain.
    """

    def test_closing_script_tag_in_data_does_not_truncate(self):
        spec = {"title": "Ends early?", "body": "a literal </script> in prose"}
        html = document.render(spec, "spec")
        found = blocks(html)
        self.assertEqual(1, len(found), "data terminated the embedding element")
        self.assertEqual("a literal </script> in prose",
                         json.loads(found[0][1])["body"],
                         "escaping was not lossless")

    def test_template_placeholders_in_data_survive_verbatim(self):
        """A spec mentioning the generator's own slot names must round-trip."""
        spec = {"title": "__TITLE__", "body": "__RUNTIME__ and __SPEC_JSON__"}
        html = document.render(spec, "spec")
        parsed = json.loads(blocks(html)[0][1])
        self.assertEqual("__TITLE__", parsed["title"])
        self.assertEqual("__RUNTIME__ and __SPEC_JSON__", parsed["body"])

    def test_non_ascii_survives(self):
        spec = {"title": "Zerø Effort — naïve café", "sections": []}
        html = document.render(spec, "spec")
        self.assertEqual("Zerø Effort — naïve café",
                         json.loads(blocks(html)[0][1])["title"])


class TestAssemblyAndSerialisationAreSeparable(unittest.TestCase):
    """Refactor step: either half must be testable alone."""

    def test_serialise_alone(self):
        text = document.serialise({"b": 1, "a": 2})
        self.assertEqual({"b": 1, "a": 2}, json.loads(text))

    def test_assemble_alone(self):
        html = document.shell.assemble(spec_id="x", spec_json="{}",
                                       title="T", description="D")
        self.assertIn('id="x"', html)
        self.assertIn("<title>T</title>", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
