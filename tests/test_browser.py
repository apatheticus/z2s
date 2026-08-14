# -*- coding: utf-8 -*-
"""The accessibility, responsive and print floors, checked in a real browser
(M1-P3-T2, M1-P3-T3).

A stylesheet can contain a contrast rule and still fail, because the ratio that
matters depends on the background an element actually sits on. These checks read
what the browser computed rather than what the stylesheet said.

The whole module is skipped, loudly, when no browser is installed — a skipped
check is never counted as a pass (LD-04, FR-GEN-03, NFR-VAL-05).

Traces: FR-GEN-06, FR-SPC-11, NFR-UX-01, NFR-UX-02, NFR-UX-03, NFR-UX-05.
"""

import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from z2s import document, runtime, shell, styles, tokens

NODE = shutil.which("node")
HARNESS = os.path.join(HERE, "browser_harness.js")

#: WCAG AA for text at ordinary sizes. The host project may target higher; this
#: is the floor below which a document is not shipped (NFR-UX-03).
CONTRAST_FLOOR = 4.5

#: A specimen exercising every section type the runtime can render, plus one it
#: cannot — the placeholder is the only status the document displays, so it has
#: to survive the contrast and colour-alone checks like everything else.
SPEC = {
    "document": {"title": "Structural Specimen", "kicker": "Specification",
                 "type": "SDD", "version": "1.0", "status": "Draft",
                 "date": "2026-08-14", "owner": "The toolchain",
                 "summary": "Every section type the runtime renders, in one document."},
    "sections": [
        {"id": "prose", "title": "Prose", "type": "prose",
         "lede": "A short standfirst.",
         "body": ["A paragraph with **bold**, `code` and a [link](https://example.org)."]},
        {"id": "list", "title": "List", "type": "list", "items": ["First", "Second"]},
        {"id": "definitions", "title": "Definitions", "type": "definitions",
         "items": [{"term": "Token", "definition": "A named design value."}]},
        {"id": "table", "title": "Table", "type": "table",
         "columns": ["Name", "Meaning"],
         "rows": [["surface-page", "The colour behind everything"],
                  ["text-body", "The colour of ordinary reading text"]]},
        {"id": "cards", "title": "Cards", "type": "cards",
         "items": [{"title": "One", "body": "First card."},
                   {"title": "Two", "body": "Second card."}]},
        {"id": "statistics", "title": "Statistics", "type": "statistics",
         "items": [{"value": "191", "label": "Requirements"},
                   {"value": "18", "label": "Decisions"}]},
        {"id": "flow", "title": "Flow", "type": "flow",
         "steps": [{"title": "Specify", "body": "Write the specification."},
                   {"title": "Plan", "body": "Derive the plan from it."}]},
        {"id": "code", "title": "Code", "type": "code", "language": "python",
         "body": "def generate():\n    return 'a very long line of sample code that must not widen the page'\n"},
        {"id": "unknown", "title": "From A Later Schema", "type": "hologram",
         "body": ["A section type this runtime does not know."]},
    ],
}


def specimen():
    return shell.assemble(
        spec_id="spec", spec_json=document.serialise(SPEC),
        title="Structural Specimen",
        description="Every section type the runtime renders, in one document.",
        tokens=tokens.render(tokens.NEUTRAL), struct=styles.STRUCT,
        runtime=runtime.SOURCE)


def run_audit():
    """Drive the browser once and share the result across every check here."""
    finished = subprocess.run(
        [NODE, HARNESS], input=json.dumps({"op": "audit", "html": specimen()}),
        capture_output=True, text=True)
    if finished.returncode == 3:
        return None, finished.stderr.strip()
    if finished.returncode != 0:
        raise AssertionError("browser harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout), None


AUDIT, REASON = (None, "node is not installed") if NODE is None else run_audit()


@unittest.skipIf(AUDIT is None, "no browser available: %s" % REASON)
class BrowserTest(unittest.TestCase):
    """Base: every check below reads the one audit run."""

    @classmethod
    def setUpClass(cls):
        cls.audit = AUDIT


class TestKeyboardOperation(BrowserTest):
    """M1-P3-T2-C1 / NFR-UX-01."""

    def test_every_control_is_reachable_by_keyboard(self):
        """The contents list is the document's only navigation. If tabbing does
        not reach it, the document has no keyboard navigation at all."""
        reached = [stop["label"] for stop in self.audit["focus"]]
        self.assertGreaterEqual(len(reached), len(SPEC["sections"]),
                                "tabbing reached %d stops for %d sections"
                                % (len(reached), len(SPEC["sections"])))

    def test_every_focused_control_shows_a_visible_indicator(self):
        for stop in self.audit["focus"]:
            visible = (stop["outlineStyle"] not in ("none", "") and stop["outlineWidth"] >= 2)
            self.assertTrue(visible,
                            "no visible focus indicator on <%s> %r (outline %s %spx)"
                            % (stop["tag"], stop["label"], stop["outlineStyle"],
                               stop["outlineWidth"]))

    def test_every_focused_control_is_actually_on_screen(self):
        for stop in self.audit["focus"]:
            self.assertTrue(stop["onScreen"],
                            "focus moved to an invisible element: %r" % stop["label"])


class TestContrast(BrowserTest):
    """M1-P3-T2-C1 / NFR-UX-03. Measured against the background each element
    really sits on, not the one its own rule declares."""

    def test_every_measured_pair_meets_the_floor(self):
        failures = ["%s %.2f" % (name, value)
                    for name, value in sorted(self.audit["contrast"].items())
                    if value < CONTRAST_FLOOR]
        self.assertEqual([], failures,
                         "below the %s:1 floor: %s" % (CONTRAST_FLOOR, ", ".join(failures)))

    def test_the_specimen_actually_exercised_the_pairs(self):
        """A contrast check over an empty report passes vacuously."""
        self.assertGreaterEqual(len(self.audit["contrast"]), 12)


class TestStatusIsNotColourAlone(BrowserTest):
    """NFR-UX-03. The placeholder is the one status this runtime displays."""

    def test_the_status_says_what_it_is_in_words(self):
        self.assertIn("cannot display", self.audit["status"]["text"])

    def test_the_status_is_announced_to_assistive_technology(self):
        self.assertEqual("note", self.audit["status"]["role"])

    def test_the_status_is_also_marked_by_shape(self):
        self.assertGreaterEqual(self.audit["status"]["borderLeftWidth"], 2)

    def test_the_active_contents_entry_is_not_marked_by_colour_alone(self):
        active = self.audit["active"]
        self.assertNotEqual(active["plainWeight"], active["weight"])
        self.assertIn("underline", active["decoration"])


class TestReducedMotion(BrowserTest):
    """M1-P3-T2-C2 / NFR-UX-02."""

    def test_nothing_animates_when_the_reader_asked_for_less_motion(self):
        motion = self.audit["motion"]
        self.assertLessEqual(motion["longestSeconds"], 0.001,
                             "%s still animates for %ss under reduced motion"
                             % (motion["culprit"], motion["longestSeconds"]))


class TestNarrowViewport(BrowserTest):
    """M1-P3-T3-C1 / NFR-UX-05. 360px wide — a small phone in portrait."""

    def test_the_page_does_not_scroll_sideways(self):
        narrow = self.audit["narrow"]
        self.assertLessEqual(narrow["scrollWidth"], narrow["clientWidth"],
                             "page scrolls sideways by %dpx"
                             % (narrow["scrollWidth"] - narrow["clientWidth"]))

    def test_no_body_element_extends_past_the_viewport(self):
        """Wide content — a table, a long line of code — must scroll inside its
        own box rather than widening the page."""
        self.assertEqual([], self.audit["narrow"]["overflowing"])


class TestPrint(BrowserTest):
    """M1-P3-T3-C2 / FR-SPC-11."""

    def test_collapsed_content_is_expanded_on_paper(self):
        self.assertTrue(self.audit["print"]["collapsedContentShown"],
                        "a closed group printed as nothing but its summary")

    def test_interactive_chrome_is_suppressed_on_paper(self):
        self.assertFalse(self.audit["print"]["contentsShown"])

    def test_the_same_content_stays_collapsed_on_screen(self):
        """The pair is what proves the print rule did the work. Without it, both
        readings would agree and the check would pass having tested nothing."""
        self.assertFalse(self.audit["screen"]["collapsedContentShown"])

    def test_the_screen_view_keeps_its_navigation(self):
        """A print rule that leaks into the screen view would hide the document's
        navigation for every reader."""
        self.assertTrue(self.audit["screen"]["contentsShown"])


if __name__ == "__main__":
    unittest.main()
