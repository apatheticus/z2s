# -*- coding: utf-8 -*-
"""The adopted theme, as a browser computes it (M16-P1-T2).

Every other check on light and dark reads the style block as text. That proves
the right characters were written and nothing else: a token block whose @supports
guard is malformed reads perfectly and renders an unstyled page, and a
light-dark() pair inside a rule the browser voids resolves to nothing at all.

So these questions are put to Chromium. Does the page a reader opens on a dark
system actually come up in the project's own dark palette; does the reader's own
choice beat the one their system reports; and does it print on white — which is
the trap, because a reader on a dark screen who prints a black page has been
charged real money by a defect nobody could see in a file.

Traces: FR-GEN-02, NFR-UX-03, ADR-16.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from z2s import design, shell, styles, tokens                     # noqa: E402

NODE = shutil.which("node")
HARNESS = os.path.join(HERE, "theme_harness.js")

#: A host design system that states both schemes, which is what makes the
#: question worth asking. The values are deliberately far apart, so a check that
#: passed by reading the wrong one would have to be lucky twice.
HOST = """
:root {
  --color-background: #fdfaf4;
  --color-text: #1c1a17;
  --color-border: #ddd6c8;
  --color-primary: #b4531f;
}
@media (prefers-color-scheme: dark) {
  :root {
    --color-background: #16140f;
    --color-text: #f2eee6;
    --color-border: #3a352b;
    --color-primary: #e8935c;
  }
}
"""


def document_for(css):
    """One finished document, styled the way a real project's would be."""
    root = tempfile.mkdtemp(prefix="z2s-theme-")
    with open(os.path.join(root, "theme.css"), "w", encoding="utf-8") as handle:
        handle.write(css)
    design.forget()
    found = design.detect(root)
    text = shell.assemble("spec", "{}", "Theme", "A document",
                          tokens=tokens.render(found.values, found.dark),
                          struct=styles.STRUCT, runtime="")
    path = os.path.join(root, "doc.html")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def _drive(path):
    if not NODE:
        return None, "node is missing", None
    finished = subprocess.run([NODE, HARNESS], input=json.dumps({"file": path}),
                              capture_output=True, text=True)
    if finished.returncode == 3:
        return None, finished.stderr.strip(), None
    if finished.returncode != 0:
        return None, finished.stderr.strip(), finished.stderr.strip()
    return json.loads(finished.stdout), None, None


#: A harness that ran and went wrong is NOT a browser that was not there. The
#: difference is the whole of LD-04 and NFR-VAL-05: a check that could not run
#: may never be counted as one that passed.
SEEN, REASON, BROKEN = _drive(document_for(HOST))
PLAIN, _, _ = _drive(document_for(":root { --color-background: #eef1f5;"
                                  " --color-text: #10141a;"
                                  " --color-border: #ccd3dc;"
                                  " --color-primary: #1a4f8f }"))


@unittest.skipIf(SEEN is None and BROKEN is None,
                 "no browser available: %s" % REASON)
class TestBothSchemesResolve(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if BROKEN is not None:          # pragma: no cover - only on a real break
            raise AssertionError(
                "the browser harness failed rather than being absent; a check "
                "that could not run is not a check that passed:\n%s" % BROKEN)

    def test_the_page_uses_the_projects_own_light_palette(self):
        self.assertEqual("rgb(253, 250, 244)", SEEN["light"]["background"])
        self.assertEqual("rgb(28, 26, 23)", SEEN["light"]["colour"])

    def test_the_page_uses_the_projects_own_dark_palette(self):
        """Not an inversion of the light one — the values the project itself
        declared under prefers-color-scheme, adopted rather than computed."""
        self.assertEqual("rgb(22, 20, 15)", SEEN["dark"]["background"])
        self.assertEqual("rgb(242, 238, 230)", SEEN["dark"]["colour"])

    def test_the_document_declares_that_it_supports_both(self):
        self.assertEqual("light dark", SEEN["light"]["scheme"])
        self.assertEqual("light dark", SEEN["dark"]["scheme"])

    def test_a_reader_can_force_dark_against_a_light_system(self):
        self.assertEqual("rgb(22, 20, 15)", SEEN["light:dark"])

    def test_a_reader_can_force_light_against_a_dark_system(self):
        self.assertEqual("rgb(253, 250, 244)", SEEN["dark:light"])

    def test_paper_is_light_whatever_the_screen_is(self):
        """The trap. Without the print rule a reader on a dark screen prints a
        page of black ink, and it is the sort of defect only a browser finds."""
        self.assertEqual(SEEN["light:print"], SEEN["dark:print"])
        for value in (SEEN["light:print"], SEEN["dark:print"]):
            self.assertNotIn(value, ("rgb(22, 20, 15)", "rgb(35, 35, 32)"))

    def test_the_page_renders_without_throwing(self):
        self.assertEqual([], SEEN["errors"])


@unittest.skipIf(PLAIN is None, "no browser available: %s" % REASON)
class TestAProjectWithNoDarkThemeIsUnchanged(unittest.TestCase):
    """The promise that makes this safe to ship.

    A dark value is never synthesised. A project whose design system says
    nothing about dark gets exactly the document it got before — its own light
    palette, in both schemes — because inventing a dark ramp means guessing at
    contrast, and NFR-UX-03 pins contrast to a floor rather than to whatever an
    inversion happens to produce.
    """

    def test_a_dark_reader_gets_the_projects_light_palette_not_an_invented_one(self):
        self.assertEqual("rgb(238, 241, 245)", PLAIN["dark"]["background"])
        self.assertEqual(PLAIN["light"]["background"], PLAIN["dark"]["background"])

    def test_no_colour_scheme_is_declared_at_all(self):
        """Not "light" — nothing. The document behaves exactly as it did before
        this milestone existed, which is a stronger claim than looking right."""
        self.assertEqual("normal", PLAIN["light"]["scheme"])


if __name__ == "__main__":
    unittest.main()
