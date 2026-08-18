# -*- coding: utf-8 -*-
"""Reader-local state and forward compatibility (M2-P3).

Two separate promises to a reader, both about what a document does *not* do.

A reviewer's ticks are their own working state. They persist so the reader can
put a long document down and come back to it, they are namespaced so several
documents from several projects can sit in one browser without overwriting each
other, and they never enter the specification object — a document handed on
must not carry the previous reader's progress (FR-SPC-08, NFR-GEN-07).

And a document authored against an earlier schema still renders. A reader with
an older document should see it, not a blank page or an error; refusing is the
job of the tools that *write* documents, where a half-understood file can be
corrupted (NFR-EVO-01 versus NFR-EVO-02, NFR-GEN-04).

The runtime is JavaScript. The storage rules are exercised through Node with a
store held in memory; the one thing only a browser has — two documents open in
one profile — is exercised through Playwright and reported as skipped when no
browser is installed, never as passed (LD-04, FR-GEN-03).

Traces: FR-SPC-02, FR-SPC-08, NFR-EVO-01, NFR-EVO-02, NFR-GEN-07.
"""

import copy
import json
import os
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import design, document, runtime, schema, styles, tokens

HERE = os.path.dirname(os.path.abspath(__file__))
RENDER = os.path.join(HERE, "render_harness.js")
REVIEW = os.path.join(HERE, "review_harness.js")
NODE = shutil.which("node")


def spec(slug="fsd", title="Acme — FSD"):
    return {
        "document": {"title": title, "slug": slug, "type": "Specification",
                     "version": "1.0", "status": "Draft for review",
                     "date": "2026-08-14", "owner": "Acme"},
        "schemaVersion": schema.SCHEMA_VERSION,
        "sections": [
            {"id": "purpose", "title": "Purpose", "type": "prose",
             "body": ["Why this document exists."]},
            {"id": "scope", "title": "Scope", "type": "list",
             "items": ["In scope", "Out of scope"]},
            {"id": "risks", "title": "Risks", "type": "table",
             "columns": ["Risk", "Mitigation"], "rows": [["Drift", "One source"]]},
        ],
    }


def call(op, **payload):
    payload["op"] = op
    finished = subprocess.run([NODE, RENDER], input=json.dumps(payload),
                              capture_output=True, text=True)
    if finished.returncode != 0:
        raise AssertionError("runtime harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout)


def page(obj):
    """A complete document, the way a generator would produce one."""
    values = design.detect(HERE).values
    return document.render(obj, obj["document"]["slug"] + "-spec",
                           tokens=tokens.render(values), struct=styles.STRUCT,
                           runtime=runtime.SOURCE)


def browser_review():
    """One browser run, or the reason there wasn't one."""
    if NODE is None:
        return None, "node is not installed"
    request = {"op": "review",
               "pages": {"fsd.html": page(spec(slug="fsd")),
                         "sdd.html": page(spec(slug="sdd", title="Acme — SDD"))}}
    finished = subprocess.run([NODE, REVIEW], input=json.dumps(request),
                              capture_output=True, text=True)
    if finished.returncode == 3:
        return None, finished.stderr.strip() or "no browser available"
    if finished.returncode != 0:
        raise AssertionError("review harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout), None


AUDIT, REASON = browser_review()


@unittest.skipIf(NODE is None, "node is not installed; the runtime cannot be exercised")
class RuntimeTest(unittest.TestCase):
    pass


class TestTheNamespace(RuntimeTest):
    """M2-P3-T1 refactor: the namespace is read from the envelope, so it cannot
    drift from the identity of the document carrying it."""

    def test_the_namespace_is_the_method_and_the_document_slug(self):
        self.assertEqual("z2s:fsd", call("review", spec=spec(slug="fsd"))["key"])

    def test_two_documents_get_two_namespaces(self):
        first = call("review", spec=spec(slug="fsd"))["key"]
        second = call("review", spec=spec(slug="sdd"))["key"]
        self.assertNotEqual(first, second)

    def test_a_document_with_no_slug_still_gets_a_namespace(self):
        """A half-written specification is a thing a reader will open. It should
        keep working, not lose its storage key and throw."""
        thin = {"document": {"title": "Untitled"}, "sections": []}
        self.assertEqual("z2s:doc", call("review", spec=thin)["key"])


class TestMarksLiveOutsideTheSpecification(RuntimeTest):
    """M2-P3-T1-C2. The object is the contract; a reader's progress is not."""

    def test_marking_an_entry_leaves_the_specification_untouched(self):
        original = spec()
        before = copy.deepcopy(original)
        result = call("review", spec=original, mark={"purpose": True})
        self.assertEqual(before, result["spec"])
        self.assertEqual(before, original)

    def test_the_stored_state_is_the_only_place_a_mark_appears(self):
        result = call("review", spec=spec(), mark={"purpose": True})
        self.assertEqual(["z2s:fsd"], sorted(result["stored"]))
        self.assertNotIn("purpose", json.dumps(result["spec"]["document"]))

    def test_a_mark_survives_and_is_read_back(self):
        result = call("review", spec=spec(), mark={"purpose": True})
        self.assertEqual(True, result["after"]["purpose"])
        self.assertEqual({"reviewed": 1, "total": 3}, result["progress"])

    def test_another_documents_state_is_not_read(self):
        result = call("review", spec=spec(slug="fsd"),
                      stored={"z2s:sdd": json.dumps({"purpose": True})})
        self.assertEqual({}, result["before"])
        self.assertEqual({"reviewed": 0, "total": 3}, result["progress"])

    def test_stored_rubbish_is_ignored_rather_than_thrown(self):
        """Browser storage is shared with other tabs, extensions and older
        versions of the same document. None of them is a reason to fail to
        render (NFR-GEN-04)."""
        for rubbish in ("not json at all", "[1,2,3]", "null", '"a string"'):
            result = call("review", spec=spec(), stored={"z2s:fsd": rubbish})
            self.assertEqual({}, result["before"], "choked on %r" % rubbish)

    def test_progress_counts_only_marks_for_sections_that_exist(self):
        """A section removed from a later version leaves a mark behind. It must
        not be counted, or a reader sees four of three reviewed."""
        result = call("review", spec=spec(),
                      stored={"z2s:fsd": json.dumps({"purpose": True, "gone": True})})
        self.assertEqual({"reviewed": 1, "total": 3}, result["progress"])

    def test_every_section_is_reviewable(self):
        self.assertEqual(["purpose", "scope", "risks"],
                         call("review", spec=spec())["reviewable"])

    def test_wiring_a_document_up_never_touches_the_specification(self):
        """The criterion that matters, checked where it can actually fail. The
        embedded block is static text, so reading it back cannot catch a runtime
        that writes a reader's ticks into the object it is holding — only
        watching that object can."""
        original = spec()
        before = copy.deepcopy(original)
        result = call("apply", spec=original, tick=True)
        self.assertEqual(before, result["spec"])
        self.assertEqual("1 of 3 reviewed", result["progress"])
        self.assertEqual(["z2s:fsd"], sorted(result["stored"]))

    def test_a_stored_mark_is_restored_to_its_control(self):
        result = call("apply", spec=spec(),
                      stored={"z2s:fsd": json.dumps({"scope": True})})
        self.assertEqual(["scope"], result["restored"])
        self.assertEqual("1 of 3 reviewed", result["progress"])

    def test_the_rendered_document_carries_a_tick_and_a_count(self):
        parts = call("document", spec=spec())
        self.assertEqual(3, parts["sections"].count('type="checkbox"'))
        self.assertIn("0 of 3 reviewed", parts["contents"])


class TestBackwardCompatibleRendering(RuntimeTest):
    """M2-P3-T2-C1. NFR-EVO-02."""

    def test_the_runtime_and_the_schema_agree_on_the_version(self):
        """Two files declare it; a test is what keeps them one fact."""
        self.assertEqual(schema.SCHEMA_VERSION, call("version"))

    def test_an_earlier_minor_version_is_recognised_as_such(self):
        self.assertEqual("older-minor", call("compatible", document="1.0", runtime="1.3"))
        self.assertEqual("same", call("compatible", document="1.3", runtime="1.3"))
        self.assertEqual("newer-minor", call("compatible", document="1.4", runtime="1.3"))
        self.assertEqual("newer-major", call("compatible", document="2.0", runtime="1.3"))
        self.assertEqual("unknown", call("compatible", document="draft", runtime="1.3"))

    def test_an_earlier_minor_version_document_renders_every_section(self):
        older = spec()
        older["schemaVersion"] = "1.0"
        parts = call("document", spec=older)
        for title in ("Purpose", "Scope", "Risks"):
            self.assertIn(title, parts["sections"])
        self.assertEqual(3, parts["sections"].count('class="section"'))

    def test_a_document_missing_every_optional_field_still_renders(self):
        thin = {"document": {"title": "Thin", "slug": "thin"},
                "schemaVersion": "1.0",
                "sections": [{"id": "only", "title": "Only", "type": "prose",
                              "body": ["One line."]}]}
        parts = call("document", spec=thin)
        self.assertIn("Only", parts["sections"])
        self.assertIn("Thin", parts["hero"])

    def test_a_field_the_runtime_has_never_seen_is_ignored_not_fatal(self):
        """The other direction, and the one that actually happens: a document
        written by a newer generator, opened in an older document runtime."""
        newer = spec()
        newer["schemaVersion"] = "1.9"
        newer["provenance"] = {"generator": "some later version"}
        newer["sections"][0]["confidence"] = 0.9
        parts = call("document", spec=newer)
        self.assertEqual(3, parts["sections"].count('class="section"'))

    def test_a_section_type_from_a_later_schema_degrades_to_a_placeholder(self):
        newer = spec()
        newer["sections"].append({"id": "matrix", "title": "Matrix", "type": "heatmap"})
        parts = call("document", spec=newer)
        self.assertIn("placeholder", parts["sections"])
        self.assertEqual(4, parts["sections"].count('class="section"'))

    def test_the_runtime_never_refuses_on_a_version(self):
        """A reading tool refuses on a major difference; a document runtime does
        not. A reader who cannot open the document has no way to act on it."""
        alien = spec()
        alien["schemaVersion"] = "9.9"
        parts = call("document", spec=alien)
        self.assertEqual(3, parts["sections"].count('class="section"'))


@unittest.skipIf(AUDIT is None, "no browser available: %s" % REASON)
class TestTwoDocumentsInOneBrowser(unittest.TestCase):
    """M2-P3-T1-C1. The criterion needs a real browser: one profile, one
    origin, one localStorage, two documents."""

    @classmethod
    def setUpClass(cls):
        cls.audit = AUDIT

    def test_marking_a_section_is_shown_back_to_the_reader(self):
        first = self.audit["firstAfterMarking"]
        self.assertEqual(["purpose"], first["checked"])
        self.assertEqual("1 of 3 reviewed", first["progress"])

    def test_two_documents_keep_separate_review_state(self):
        second = self.audit["second"]
        self.assertEqual([], second["checked"])
        self.assertEqual("0 of 3 reviewed", second["progress"])

    def test_the_first_document_still_remembers_on_return(self):
        back = self.audit["firstOnReturn"]
        self.assertEqual(["purpose"], back["checked"])
        self.assertEqual("1 of 3 reviewed", back["progress"])

    def test_clearing_a_mark_persists_too(self):
        cleared = self.audit["firstAfterClearing"]
        self.assertEqual([], cleared["checked"])
        self.assertEqual("0 of 3 reviewed", cleared["progress"])

    def test_the_two_documents_wrote_to_two_keys(self):
        storage = self.audit["firstOnReturn"]["storage"]
        self.assertIn("z2s:fsd", storage)
        self.assertNotIn("z2s:sdd", storage)

    def test_the_copied_specification_contains_no_review_state(self):
        """M2-P3-T1-C2 against the real thing: the text a reader would copy out
        of the document after marking it up."""
        embedded = json.loads(self.audit["firstOnReturn"]["embedded"])
        self.assertEqual(spec(slug="fsd"), embedded)
        self.assertNotIn("z2s:", self.audit["firstOnReturn"]["embedded"])


if __name__ == "__main__":
    unittest.main()
