# -*- coding: utf-8 -*-
"""Token adoption with a neutral fallback (M1-P3-T1).

A generated document should look like part of the project it describes, so the
generator reads that project's design tokens and inlines them. When the project
has no design system the document uses a neutral theme and the run says so —
never silently, because a silent fallback reads as adoption (FR-GEN-03).

Traces: FR-GEN-02, NFR-GEN-03, NFR-ARC-04, ADR-16.
"""

import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import styles, tokens


def project(**files):
    """Build a throwaway project directory and return its path."""
    root = tempfile.mkdtemp(prefix="z2s-tokens-")
    for name, body in sorted(files.items()):
        path = os.path.join(root, name)
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(body)
    return root


HOST_CSS = """
:root {
  --color-background: #101014;
  --color-surface: #1b1b22;
  --color-text: #f2f2f5;
  --color-muted: #9b9ba6;
  --color-primary: #7cc4ff;
  --color-border: #2f2f3a;
  --font-family: "Host Grotesk", sans-serif;
  --font-mono: "Host Mono", monospace;
}
"""


class TestTheContractIsOneDeclaredThing(unittest.TestCase):
    """The refactor step: fallback and mapper satisfy the same published list."""

    def test_the_neutral_theme_supplies_every_contract_token(self):
        missing = [name for name in tokens.CONTRACT if name not in tokens.NEUTRAL]
        self.assertEqual([], missing)

    def test_the_neutral_theme_supplies_nothing_outside_the_contract(self):
        extra = [name for name in tokens.NEUTRAL if name not in tokens.CONTRACT]
        self.assertEqual([], extra)

    def test_every_token_the_structural_styling_uses_is_in_the_contract(self):
        """Structural styling may not invent a token the contract does not define,
        or a host project could satisfy the contract and still get a broken page."""
        used = set(re.findall(r"var\((--z2s-[a-z0-9-]+)", styles.STRUCT))
        declared = set("--z2s-" + name for name in tokens.CONTRACT)
        self.assertEqual(set(), used - declared)


class TestHostTokensAreAdopted(unittest.TestCase):
    """M1-P3-T1-C1."""

    def setUp(self):
        self.root = project(**{"styles/theme.css": HOST_CSS})
        self.tokens, self.source = tokens.detect(self.root)

    def test_the_host_values_reach_the_style_block(self):
        block = tokens.render(self.tokens)
        self.assertIn("#f2f2f5", block)          # its text colour
        self.assertIn("#101014", block)          # its page colour
        self.assertIn("Host Grotesk", block)     # its typeface

    def test_the_run_names_the_file_it_adopted(self):
        self.assertIsNotNone(self.source)
        self.assertIn("theme.css", tokens.report(self.source))

    def test_a_token_the_host_does_not_define_falls_back_individually(self):
        """Adoption is per token. A host system that defines colour but no shadow
        gets its colours, not a half-styled document."""
        self.assertEqual(tokens.NEUTRAL["shadow-1"], self.tokens["shadow-1"])

    def test_the_result_still_satisfies_the_whole_contract(self):
        missing = [name for name in tokens.CONTRACT if name not in self.tokens]
        self.assertEqual([], missing)


class TestTheNeutralFallbackIsAnnounced(unittest.TestCase):
    """M1-P3-T1-C2."""

    def setUp(self):
        self.root = project(**{"README.md": "A project with no design system.\n"})
        self.tokens, self.source = tokens.detect(self.root)

    def test_no_design_system_means_the_neutral_theme(self):
        self.assertIsNone(self.source)
        self.assertEqual(tokens.NEUTRAL, self.tokens)

    def test_the_run_says_it_fell_back(self):
        line = tokens.report(self.source)
        self.assertIn("neutral", line.lower())
        self.assertNotIn("adopted", line.lower())

    def test_a_stylesheet_with_no_recognisable_token_is_not_claimed_as_adoption(self):
        """A file full of ordinary CSS rules is not a design system. Claiming it
        would report a fallback as an adoption, which FR-GEN-03 forbids."""
        root = project(**{"site.css": "body { margin: 0 }\n.header { display: flex }\n"})
        found, source = tokens.detect(root)
        self.assertIsNone(source)
        self.assertEqual(tokens.NEUTRAL, found)

    def test_one_stray_custom_property_is_not_a_design_system(self):
        """The harder case: a stylesheet that does declare a variable or two.
        Below the threshold this is one developer's shortcut, and adopting it
        would produce a document coloured by an accident."""
        root = project(**{"site.css": ":root { --border: #ccc; --radius: 4px }\n"})
        found, source = tokens.detect(root)
        self.assertIsNone(source)
        self.assertEqual(tokens.NEUTRAL["border"], found["border"])

    def test_a_system_that_clears_the_threshold_is_adopted(self):
        """The pair that makes the test above mean something: the same shape of
        file, with enough of the contract named, is adopted."""
        root = project(**{"site.css": ":root { --color-background: #fff; --color-text: #111;"
                                      " --color-border: #ccc; --color-primary: #05f }\n"})
        found, source = tokens.detect(root)
        self.assertIsNotNone(source)
        self.assertEqual("#111", found["text-body"])


class TestDetectionIsDeterministic(unittest.TestCase):
    """NFR-GEN-01: two runs over the same project produce the same document."""

    def test_two_candidate_stylesheets_resolve_the_same_way_every_time(self):
        root = project(**{"a/one.css": HOST_CSS,
                          "b/two.css": HOST_CSS.replace("#f2f2f5", "#eeeeee")})
        first = tokens.detect(root)
        for _ in range(5):
            self.assertEqual(first, tokens.detect(root))


class TestNoLiteralsOutsideTheTokenBlock(unittest.TestCase):
    """M1-P3-T1-C3 / NFR-GEN-03. Enforced by a check, not by convention."""

    def body_of_the_stylesheet(self):
        """Everything a document's <style> holds except the token block itself,
        with media-query conditions removed — a breakpoint cannot be a variable,
        so its pixel value is not a hard-coded style."""
        text = styles.STRUCT
        return re.sub(r"@media[^{]*", "@media ", text)

    def test_no_colour_literal(self):
        text = self.body_of_the_stylesheet()
        found = re.findall(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(", text)
        self.assertEqual([], found)

    def test_no_typeface_literal(self):
        text = self.body_of_the_stylesheet()
        found = [value for value in re.findall(r"font-family\s*:\s*([^;}]+)", text)
                 if "var(" not in value and value.strip() != "inherit"]
        self.assertEqual([], found)

    def test_no_shadow_literal(self):
        text = self.body_of_the_stylesheet()
        found = [rule for rule in re.findall(r"box-shadow\s*:\s*([^;}]+)", text)
                 if "var(" not in rule and rule.strip() != "none"]
        self.assertEqual([], found)

    def test_no_hard_coded_length(self):
        """NFR-GEN-03 names spacing alongside colour, so lengths go through the
        contract too. Zero needs no unit and is therefore not a literal."""
        text = self.body_of_the_stylesheet()
        found = re.findall(r"(?<![\w-])\d*\.?\d+(?:px|rem|em|ch)\b", text)
        self.assertEqual([], found)

    def test_the_check_notices_a_literal_that_is_introduced(self):
        """The guard above is only worth having if it fails when it should."""
        text = "@media print { .card { color: #ff0000; padding: 4px } }"
        stripped = re.sub(r"@media[^{]*", "@media ", text)
        self.assertTrue(re.findall(r"#[0-9a-fA-F]{3,8}\b", stripped))
        self.assertTrue(re.findall(r"(?<![\w-])\d*\.?\d+(?:px|rem|em|ch)\b", stripped))


if __name__ == "__main__":
    unittest.main()
