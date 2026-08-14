# -*- coding: utf-8 -*-
"""Structural styling: the accessibility, print and size floors that hold
without a browser (M1-P3-T2, M1-P3-T3).

The rules themselves are proved in a real browser by test_browser.py. What is
proved here is that they are present and shared — that no document can opt out
of them, because there is exactly one structural stylesheet and it is never
edited per project (NFR-ARC-04).

Traces: FR-GEN-06, FR-SPC-11, NFR-UX-01, NFR-UX-02, NFR-UX-05, NFR-PRF-02.
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import document, shell, styles, tokens

SPEC = {
    "document": {"title": "Specimen", "kicker": "Specification", "type": "SDD",
                 "version": "1.0", "status": "Draft", "date": "2026-08-14",
                 "owner": "Nobody", "summary": "A document used to measure the chrome."},
    "sections": [
        {"id": "intro", "title": "Introduction", "type": "prose",
         "body": ["One paragraph."]},
    ],
}


def specimen(spec=None):
    """Assemble a complete document the way a generator would."""
    from z2s import runtime
    return shell.assemble(
        spec_id="spec", spec_json=document.serialise(spec or SPEC),
        title="Specimen", description="A document used to measure the chrome.",
        tokens=tokens.render(tokens.NEUTRAL), struct=styles.STRUCT,
        runtime=runtime.SOURCE)


class TestTheAccessibilityRulesAreShared(unittest.TestCase):
    """NFR-UX-01, NFR-UX-02. A rule in the shared stylesheet cannot be opted out
    of; a rule a generator adds per document can."""

    def test_focus_styling_is_keyed_on_focus_visible(self):
        self.assertIn(":focus-visible", styles.STRUCT)

    def test_the_focus_indicator_is_an_outline_not_a_colour_swap(self):
        """An outline survives a background the host tokens made dark, and it is
        the one focus affordance a forced-colours mode keeps."""
        rule = re.search(r":focus-visible\s*\{([^}]*)\}", styles.STRUCT)
        self.assertIsNotNone(rule)
        self.assertIn("outline", rule.group(1))

    def test_no_element_removes_the_outline_without_replacing_it(self):
        for rule in re.findall(r"\{([^}]*)\}", styles.STRUCT):
            if re.search(r"outline\s*:\s*(none|0)\b", rule):
                self.assertIn("box-shadow", rule,
                              "outline removed with no replacement indicator")

    def test_motion_is_suppressed_under_a_reduced_motion_preference(self):
        self.assertIn("prefers-reduced-motion", styles.STRUCT)

    def test_the_reduced_motion_rule_covers_everything_not_a_named_list(self):
        """A list of animated selectors goes stale the moment one is added."""
        rule = re.search(r"@media\s*\(prefers-reduced-motion[^{]*\{([^@]*)",
                         styles.STRUCT)
        self.assertIsNotNone(rule)
        self.assertIn("*", rule.group(1))


class TestTheResponsiveAndPrintRulesAreShared(unittest.TestCase):
    """NFR-UX-05, FR-SPC-11."""

    def test_there_is_a_narrow_viewport_breakpoint(self):
        self.assertTrue(re.search(r"@media\s*\(max-width", styles.STRUCT))

    def test_there_is_a_print_stylesheet(self):
        self.assertIn("@media print", styles.STRUCT)

    def test_print_expands_collapsed_content(self):
        rule = re.search(r"@media print\s*\{(.*)", styles.STRUCT, re.S)
        self.assertIsNotNone(rule)
        self.assertIn("details", rule.group(1))


class TestTheSizeBudget(unittest.TestCase):
    """M1-P3-T3-C3 / NFR-PRF-02. One named constant, shared by this test and the
    build report, so the two can never disagree about the limit."""

    def test_the_chrome_leaves_most_of_the_budget_for_content(self):
        """What this phase controls is the chrome — styling plus runtime. If the
        chrome alone eats the budget, no specification fits inside it."""
        chrome = len(specimen().encode("utf-8")) - len(document.serialise(SPEC).encode("utf-8"))
        self.assertLessEqual(chrome, shell.CHROME_BUDGET,
                             "the shared chrome is %d bytes, over its %d budget"
                             % (chrome, shell.CHROME_BUDGET))

    def test_a_document_within_budget_reports_as_within_budget(self):
        report = shell.budget_report("specimen.html", specimen())
        self.assertTrue(report.within)
        self.assertIn("specimen.html", report.text)

    def test_a_document_over_budget_says_so_and_says_by_how_much(self):
        over = "x" * (shell.SIZE_BUDGET + 1)
        report = shell.budget_report("huge.html", over)
        self.assertFalse(report.within)
        self.assertIn("huge.html", report.text)
        self.assertIn("split", report.text.lower())

    def test_the_budget_is_not_read_from_configuration(self):
        """A budget a project can raise is not a budget."""
        self.assertIsInstance(shell.SIZE_BUDGET, int)


if __name__ == "__main__":
    unittest.main()
