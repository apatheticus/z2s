# -*- coding: utf-8 -*-
"""M1-P2 — the document runtime.

Covers criteria:
  M1-P2-T1-C1  Changing a value in the embedded object changes the rendered view.
  M1-P2-T1-C2  No content string appears in the file outside the embedded object.
  M1-P2-T2-C1  An unknown section type renders a placeholder and does not halt
               rendering.
  M1-P2-T3-C1  Authored markup is rendered as literal text.
  M1-P2-T3-C2  Only bold, inline code and links expand.
  M1-P2-T4-C1  Numbering is contiguous after inserting a section.

The runtime is JavaScript, so the assertions here drive it through a small
harness (tests/render_harness.js) run by Node. Node is a development tool only;
nothing it provides reaches a published document, which uses browser built-ins
alone (NFR-ARC-03).

M1-P2-T4-C2 — the contents entry for the section in view is marked active — is
not here. It needs a viewport, a scroll position and a live IntersectionObserver,
none of which exist outside a browser. It is covered in the browser pass at
M1-P3 rather than approximated with a fake.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import document, runtime

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.join(HERE, "render_harness.js")
NODE = shutil.which("node")

SPEC = {
    "document": {"title": "Field Report", "kicker": "Specification",
                 "summary": "What the machine reads."},
    "sections": [
        {"id": "intro", "title": "Introduction", "type": "prose",
         "body": ["The first paragraph."]},
        {"id": "parts", "title": "Parts", "type": "list",
         "items": ["Anvil", "Bellows"]},
    ],
}


def call(op, **payload):
    """Run one operation through the runtime and return its result."""
    payload["op"] = op
    finished = subprocess.run([NODE, HARNESS], input=json.dumps(payload),
                              capture_output=True, text=True)
    if finished.returncode != 0:
        raise AssertionError("runtime harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout)


def spec_with(sections, **doc):
    envelope = dict(SPEC["document"])
    envelope.update(doc)
    return {"document": envelope, "sections": sections}


@unittest.skipIf(NODE is None, "node is not installed; the runtime cannot be exercised")
class RuntimeTest(unittest.TestCase):
    pass


class TestRenderFromTheEmbeddedObject(RuntimeTest):

    def test_the_view_follows_the_data(self):
        """M1-P2-T1-C1"""
        first = call("document", spec=spec_with(SPEC["sections"], title="Field Report"))
        second = call("document", spec=spec_with(SPEC["sections"], title="Site Survey"))
        self.assertIn("Field Report", first["hero"])
        self.assertIn("Site Survey", second["hero"])
        self.assertNotIn("Field Report", second["hero"])

    def test_every_section_reaches_the_page(self):
        rendered = call("document", spec=SPEC)
        self.assertIn("Introduction", rendered["sections"])
        self.assertIn("The first paragraph.", rendered["sections"])
        self.assertIn("Parts", rendered["sections"])
        self.assertIn("Bellows", rendered["sections"])

    def test_the_contents_list_follows_document_order(self):
        rendered = call("document", spec=SPEC)
        self.assertLess(rendered["contents"].index("Introduction"),
                        rendered["contents"].index("Parts"))

    def test_an_empty_specification_still_renders(self):
        """NFR-EVO-02 — render, never refuse."""
        rendered = call("document", spec={})
        self.assertIsInstance(rendered["hero"], str)
        self.assertIsInstance(rendered["sections"], str)


class TestNoContentOutsideTheEmbeddedObject(unittest.TestCase):
    """M1-P2-T1-C2 — checked on the assembled file, not on the runtime."""

    def assembled(self):
        return document.render(SPEC, "docSpec", description="A field report",
                               runtime=runtime.SOURCE)

    def outside_the_spec_block(self, html):
        return re.sub(r'<script type="application/json".*?</script>', "", html,
                      flags=re.S)

    def test_authored_content_lives_only_in_the_embedded_object(self):
        remainder = self.outside_the_spec_block(self.assembled())
        for authored in ("The first paragraph.", "Introduction", "Parts",
                         "Anvil", "Bellows", "What the machine reads."):
            self.assertNotIn(authored, remainder,
                             "%r was baked into the markup; it must come from "
                             "the embedded object at load time" % authored)

    def test_the_title_is_the_one_permitted_duplicate(self):
        """The browser tab needs it before any script runs, so <title> is a
        deliberate exception, and it is the only one."""
        remainder = self.outside_the_spec_block(self.assembled())
        self.assertEqual(1, remainder.count("Field Report"))
        self.assertIn("<title>Field Report</title>", remainder)

    def test_the_runtime_is_actually_present(self):
        """Guards the test above from passing on an empty page."""
        self.assertIn("renderDocument", self.assembled())


class TestUnknownSectionTypes(RuntimeTest):

    def test_an_unknown_type_renders_a_placeholder_and_the_rest_survives(self):
        """M1-P2-T2-C1 / NFR-GEN-04 / NFR-EVO-02"""
        rendered = call("document", spec=spec_with([
            {"id": "a", "title": "Before", "type": "prose", "body": ["Ahead."]},
            {"id": "b", "title": "Invented", "type": "hologram", "items": ["?"]},
            {"id": "c", "title": "After", "type": "prose", "body": ["Behind."]},
        ]))
        self.assertIn("Ahead.", rendered["sections"])
        self.assertIn("Behind.", rendered["sections"])
        self.assertIn("hologram", rendered["sections"])
        self.assertIn("Invented", rendered["contents"])

    def test_a_section_with_no_type_at_all_does_not_halt_rendering(self):
        rendered = call("document", spec=spec_with([
            {"id": "a", "title": "Untyped"},
            {"id": "b", "title": "After", "type": "prose", "body": ["Behind."]},
        ]))
        self.assertIn("Behind.", rendered["sections"])

    def test_the_known_types_are_all_present(self):
        self.assertEqual(
            ["cards", "code", "definitions", "flow", "list", "prose",
             "requirements", "statistics", "table"],
            call("types"))

    def test_every_known_type_renders_its_content(self):
        cases = [
            ({"type": "prose", "body": ["Paragraph."]}, "Paragraph."),
            ({"type": "list", "items": ["Item."]}, "Item."),
            ({"type": "definitions",
              "items": [{"term": "Word", "definition": "Meaning."}]}, "Meaning."),
            ({"type": "table", "columns": ["Head"], "rows": [["Cell"]]}, "Cell"),
            ({"type": "cards",
              "items": [{"title": "Card", "body": "Face."}]}, "Face."),
            ({"type": "statistics",
              "items": [{"value": "12", "label": "Counted"}]}, "Counted"),
            ({"type": "flow",
              "steps": [{"title": "Step", "body": "Move."}]}, "Move."),
            ({"type": "code", "body": "print(1)"}, "print(1)"),
            ({"type": "requirements",
              "areas": [{"key": "FR-DOC", "name": "Chain"}],
              "items": [{"id": "FR-DOC-01", "area": "FR-DOC", "priority": "Must",
                         "title": "Named", "text": "Stated.", "tags": ["tagged"]}]},
             "Stated."),
        ]
        for section, expected in cases:
            with self.subTest(type=section["type"]):
                whole = dict(section, id="s", title="Section")
                rendered = call("document", spec=spec_with([whole]))
                self.assertIn(expected, rendered["sections"])

    def test_a_known_type_with_missing_data_still_renders(self):
        """A field that is absent is not a crash (NFR-EVO-02)."""
        for section_type in ("prose", "list", "definitions", "table", "cards",
                             "statistics", "flow", "code", "requirements"):
            with self.subTest(type=section_type):
                rendered = call("document", spec=spec_with(
                    [{"id": "s", "title": "Bare", "type": section_type}]))
                self.assertIn("Bare", rendered["sections"])


class TestEscaping(RuntimeTest):

    def test_authored_markup_is_literal_text(self):
        """M1-P2-T3-C1 / NFR-GEN-05"""
        hostile = '<script>alert("x")</script> & <b>bold?</b>'
        self.assertEqual(
            "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt; &amp; "
            "&lt;b&gt;bold?&lt;/b&gt;",
            call("esc", value=hostile))

    def test_a_script_fragment_in_any_field_stays_text(self):
        rendered = call("document", spec=spec_with(
            [{"id": "s", "title": "<script>t()</script>", "type": "prose",
              "body": ["<img src=x onerror=alert(1)>"]},
             {"id": "c", "title": "Code", "type": "code",
              "body": "</script><script>alert(1)</script>"}],
            title="<script>h()</script>"))
        whole = rendered["hero"] + rendered["contents"] + rendered["sections"]
        self.assertNotIn("<script", whole)
        self.assertNotIn("<img", whole)
        self.assertIn("&lt;script&gt;", whole)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", whole)

    def test_only_the_three_permitted_forms_expand(self):
        """M1-P2-T3-C2 / NFR-DAT-07"""
        self.assertEqual("<strong>bold</strong>", call("rich", value="**bold**"))
        self.assertEqual("<code>code</code>", call("rich", value="`code`"))
        self.assertEqual('<a href="https://example.com">text</a>',
                         call("rich", value="[text](https://example.com)"))

    def test_everything_else_authors_might_expect_stays_text(self):
        for markup in ("# Heading", "> Quote", "- Item", "1. Numbered",
                       "_italic_", "*single*", "~~struck~~", "| a | b |",
                       "<!-- comment -->"):
            with self.subTest(markup=markup):
                self.assertNotIn("<", call("rich", value=markup))

    def test_an_image_reference_becomes_a_link_not_an_image(self):
        """Markdown's image form contains a permitted link form, so the link
        expands and the leading '!' stays text. Documented rather than special-
        cased: the permitted set is three, and an image is not one of them."""
        self.assertEqual('!<a href="diagram.png">alt</a>',
                         call("rich", value="![alt](diagram.png)"))

    def test_a_link_cannot_smuggle_a_scheme(self):
        """Escaping keeps the attribute intact; the scheme check keeps it inert."""
        rendered = call("rich", value="[click](javascript:alert(1))")
        self.assertNotIn("javascript:", rendered)

    def test_code_content_is_never_expanded(self):
        """`**` in a code sample is two asterisks, not emphasis."""
        rendered = call("document", spec=spec_with(
            [{"id": "s", "title": "Sample", "type": "code",
              "body": "a ** b, `x`, [y](z)"}]))
        self.assertIn("a ** b, `x`, [y](z)", rendered["sections"])
        self.assertNotIn("<strong>", rendered["sections"])

    def test_escaping_happens_before_expansion(self):
        """Otherwise an author could close a tag from inside bold markup."""
        self.assertEqual("<strong>&lt;i&gt;</strong>", call("rich", value="**<i>**"))


class TestDerivedNumbering(RuntimeTest):

    def numbers(self, sections):
        return [entry["number"] for entry in call("outline", spec=spec_with(sections))]

    def sections(self, *ids):
        return [{"id": i, "title": i.title(), "type": "prose", "body": [i]}
                for i in ids]

    def test_numbering_is_contiguous_after_an_insertion(self):
        """M1-P2-T4-C1 / NFR-GEN-06"""
        before = self.numbers(self.sections("a", "b", "c"))
        after = self.numbers(self.sections("a", "b", "inserted", "c"))
        self.assertEqual([1, 2, 3], before)
        self.assertEqual([1, 2, 3, 4], after)

    def test_an_authored_number_is_ignored(self):
        outline = call("outline", spec=spec_with(
            [{"id": "a", "title": "First", "type": "prose", "number": 9},
             {"id": "b", "title": "Second", "type": "prose", "number": 9}]))
        self.assertEqual([1, 2], [entry["number"] for entry in outline])

    def test_the_sections_and_the_contents_share_one_ordering(self):
        sections = self.sections("a", "b", "c")
        outline = call("outline", spec=spec_with(sections))
        rendered = call("document", spec=spec_with(sections))
        order = [entry["id"] for entry in outline]
        self.assertEqual(["a", "b", "c"], order)
        positions = [rendered["contents"].index('href="#%s"' % i) for i in order]
        self.assertEqual(sorted(positions), positions)
        positions = [rendered["sections"].index('id="%s"' % i) for i in order]
        self.assertEqual(sorted(positions), positions)


if __name__ == "__main__":
    unittest.main(verbosity=2)
