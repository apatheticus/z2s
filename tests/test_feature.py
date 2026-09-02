# -*- coding: utf-8 -*-
"""One open feature, and an audited close (FR-GEN-12, FR-GEN-13, FR-GEN-14).

Traces: FR-GEN-12, FR-GEN-13, FR-GEN-14, FR-SKL-10, NFR-OPS-07, ADR-19,
US-GEN-04, US-GEN-05, US-GEN-06.
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import chain, context, document, execute, feature, intent, paths, status, writer
from tests.test_validate import index_spec, milestone_spec, spec as document_spec, task_entry


def git(root, *args):
    return subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True)


class Project(unittest.TestCase):
    """A host project with its shared Intent and Context written, inside a
    committed git repository so the shipping question has an answer."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-feature-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "config", "user.email", "t@example.com")
        git(self.root, "config", "user.name", "t")
        paths.ensure_layout(self.root)
        self.write(intent.FILENAME, intent.SLUG, shared=True)
        self.write(context.FILENAME, context.SLUG, shared=True)
        self.commit()

    def commit(self):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "x", "--allow-empty")

    def write(self, filename, slug, shared=False, made=None):
        made = made or document_spec(slug=slug)
        made["document"]["slug"] = slug
        return chain.write(self.root, filename, made, slug + "-spec", shared=shared)

    def plan(self, *tasks):
        """A plan for the current feature carrying the given tasks."""
        folder = paths.resolve(self.root, paths.PLAN_DIR)
        for name, built in (("M1-x.html", milestone_spec(items=list(tasks))),
                            ("index.html", index_spec())):
            writer.write(os.path.join(folder, name), document.render(built, "plan-spec"))

    def invoke(self, *argv):
        out = io.StringIO()
        code = feature.main(list(argv) + ["--root", self.root], out)
        return code, out.getvalue()


class TestOpeningAFeature(Project):

    def test_the_first_feature_is_001(self):
        self.assertEqual(".zero/features/001-checkout", feature.open(self.root, "checkout"))
        self.assertTrue(os.path.isdir(paths.resolve(self.root, paths.PLAN_DETAILS_DIR)))
        self.assertEqual((1, "checkout"), feature.current(self.root))

    def test_the_next_feature_takes_the_next_number(self):
        feature.open(self.root, "checkout")
        self.write(intent.FILENAME, intent.SLUG)
        feature.close(self.root, "parked", "2026-09-02")
        self.assertEqual(".zero/features/002-refunds", feature.open(self.root, "refunds"))

    def test_a_second_open_feature_is_refused(self):
        feature.open(self.root, "checkout")
        with self.assertRaises(feature.Refused) as caught:
            feature.open(self.root, "refunds")
        self.assertIn("001-checkout is open", str(caught.exception))
        self.assertEqual([(1, "checkout")], paths.features(self.root))

    def test_a_feature_needs_the_shared_intent_and_context(self):
        os.remove(paths.shared(self.root, paths.SPECS_DIR, context.FILENAME))
        with self.assertRaises(chain.MissingPrerequisite) as caught:
            feature.open(self.root, "checkout")
        self.assertIn("opening a feature needs a completed context", str(caught.exception))
        self.assertEqual([], paths.features(self.root))

    def test_an_old_vision_counts_as_the_shared_intent(self):
        os.rename(paths.shared(self.root, paths.SPECS_DIR, intent.FILENAME),
                  paths.shared(self.root, paths.SPECS_DIR, "Vision.html"))
        made = document_spec(slug="vision")
        made["document"]["slug"] = "vision"
        writer.write(paths.shared(self.root, paths.SPECS_DIR, "Vision.html"),
                     document.render(made, "vision-spec"))
        self.assertEqual(".zero/features/001-checkout", feature.open(self.root, "checkout"))

    def test_the_name_grammar_is_the_directory_grammar(self):
        for bad in ("Checkout", "check out", "-x", "x-", "", "a--b"):
            with self.assertRaises(feature.Refused):
                feature.open(self.root, bad)


class TestTheFeatureIsWhereTheChainWrites(Project):

    def setUp(self):
        super().setUp()
        feature.open(self.root, "checkout")

    def test_a_document_written_now_lands_in_the_feature(self):
        written = self.write("PRD.html", "prd")
        self.assertEqual(os.path.join(self.root, ".zero", "features", "001-checkout",
                                      "specs", "PRD.html"), written)

    def test_the_context_still_lands_beside_the_project(self):
        written = self.write(context.FILENAME, context.SLUG, shared=True)
        self.assertEqual(paths.shared(self.root, paths.SPECS_DIR, context.FILENAME), written)

    def test_the_feature_intent_is_required_not_the_projects(self):
        with self.assertRaises(chain.MissingPrerequisite):
            chain.require(self.root, intent.FILENAME, intent.SLUG, "a test")
        self.write(intent.FILENAME, intent.SLUG)
        chain.require(self.root, intent.FILENAME, intent.SLUG, "a test")

    def test_a_closed_feature_refuses_generation_and_building(self):
        self.write(intent.FILENAME, intent.SLUG)
        feature.close(self.root, "parked", "2026-09-02")
        with self.assertRaises(chain.FeatureClosed) as caught:
            self.write("PRD.html", "prd")
        self.assertIn("001-checkout is closed (2026-09-02: parked)", str(caught.exception))
        with self.assertRaises(execute.Refused):
            execute.run(self.root, io.StringIO())
        # The shared document is still writable: it is the project's.
        self.write(context.FILENAME, context.SLUG, shared=True)


class TestTheAudit(Project):

    def setUp(self):
        super().setUp()
        feature.open(self.root, "checkout")
        self.write(intent.FILENAME, intent.SLUG)

    def kinds(self):
        return sorted(one["kind"] for one in feature.audit(self.root))

    def test_a_clean_feature_audits_clean(self):
        self.plan(task_entry(status="passing"))
        self.commit()
        self.assertEqual([], feature.audit(self.root))

    def test_a_unit_not_passing_is_a_finding(self):
        self.plan(task_entry(status="in-progress"))
        self.commit()
        found = feature.audit(self.root)
        self.assertEqual([("unit", "M1-P1-T1", "status is in-progress")],
                         [(one["kind"], one["id"], one["text"]) for one in found])

    def test_a_retired_identifier_with_no_successor_is_a_finding(self):
        made = document_spec(slug="fsd")
        made["sections"][0]["entries"][0]["retired"] = "no longer wanted"
        self.write("FSD.html", "fsd", made=made)
        self.commit()
        self.assertIn("retired", self.kinds())
        made["sections"][0]["entries"][0]["supersededBy"] = "FR-DOC-02"
        self.write("FSD.html", "fsd", made=made)
        self.commit()
        self.assertNotIn("retired", self.kinds())

    def test_an_open_question_is_a_finding(self):
        made = document_spec(slug="prd")
        made["sections"].append({"id": "open-questions", "type": "list",
                                 "title": "Open questions",
                                 "items": ["The brief says nothing about pricing."]})
        self.write("PRD.html", "prd", made=made)
        self.commit()
        found = [one for one in feature.audit(self.root) if one["kind"] == "question"]
        self.assertEqual("PRD.html", found[0]["id"])
        self.assertIn("pricing", found[0]["text"])

    def test_unshipped_work_is_a_finding(self):
        self.assertIn("unshipped", self.kinds())          # the Intent is uncommitted
        self.commit()
        self.assertNotIn("unshipped", self.kinds())
        ledger = execute.blank()
        ledger["standing"]["M1-P1-T1"] = {"attempt": 1, "changes": ["src/x.py"]}
        execute.save(self.root, ledger)
        found = [one for one in feature.audit(self.root) if one["kind"] == "unshipped"]
        self.assertEqual("M1-P1-T1", found[0]["id"])


class TestClosing(Project):

    def setUp(self):
        super().setUp()
        feature.open(self.root, "checkout")
        self.write(intent.FILENAME, intent.SLUG)
        self.plan(task_entry(status="in-progress"))
        self.commit()

    def held(self):
        _, spec = status.read(paths.resolve(self.root, paths.SPECS_DIR, intent.FILENAME))
        return spec["document"].get("closed")

    def test_a_dirty_audit_refuses_a_close_with_no_reason(self):
        code, text = self.invoke("close", "--date", "2026-09-02")
        self.assertEqual(1, code)
        self.assertIn("unit M1-P1-T1: status is in-progress", text)
        self.assertIsNone(self.held())

    def test_a_close_with_a_reason_records_what_was_left(self):
        code, text = self.invoke("close", "parked for the release", "--date", "2026-09-02")
        self.assertEqual(0, code, text)
        self.assertEqual({"date": "2026-09-02", "reason": "parked for the release",
                          "left": [{"kind": "unit", "id": "M1-P1-T1",
                                    "text": "status is in-progress"}]}, self.held())

    def test_a_clean_close_records_complete(self):
        self.plan(task_entry(status="passing"))
        self.commit()
        code, text = self.invoke("close", "--date", "2026-09-02")
        self.assertEqual(0, code, text)
        self.assertEqual({"date": "2026-09-02", "reason": "complete", "left": []}, self.held())

    def test_the_date_is_required(self):
        code, text = self.invoke("close", "parked")
        self.assertEqual(1, code)
        self.assertIn("no date", text)

    def test_closing_twice_is_refused(self):
        feature.close(self.root, "parked", "2026-09-02")
        code, text = self.invoke("close", "again", "--date", "2026-09-03")
        self.assertEqual(1, code)
        self.assertIn("already closed (2026-09-02: parked)", text)

    def test_a_closed_document_is_byte_identical_to_a_regenerated_one(self):
        feature.close(self.root, "parked", "2026-09-02")
        path = paths.resolve(self.root, paths.SPECS_DIR, intent.FILENAME)
        with open(path, "rb") as handle:
            before = handle.read()
        _, spec = status.read(path)
        writer.write(path, chain.render(spec, intent.SPEC_ID, self.root))
        with open(path, "rb") as handle:
            self.assertEqual(before, handle.read())

    def test_a_feature_with_no_intent_cannot_be_closed(self):
        feature.close(self.root, "parked", "2026-09-02")
        feature.open(self.root, "refunds")
        with self.assertRaises(feature.Refused) as caught:
            feature.close(self.root, "parked", "2026-09-02")
        self.assertIn("no Intent", str(caught.exception))


class TestStatus(Project):

    def test_no_feature(self):
        code, text = self.invoke("status")
        self.assertEqual(0, code)
        self.assertIn("no feature is open", text)

    def test_an_open_feature_reports_its_audit(self):
        feature.open(self.root, "checkout")
        self.write(intent.FILENAME, intent.SLUG)
        code, text = self.invoke("status")
        self.assertEqual(0, code)
        self.assertIn("feature: .zero/features/001-checkout", text)
        self.assertIn("unshipped working tree", text)

    def test_a_closed_feature_reports_the_close_and_the_next_command(self):
        feature.open(self.root, "checkout")
        self.write(intent.FILENAME, intent.SLUG)
        feature.close(self.root, "parked", "2026-09-02")
        code, text = self.invoke("status")
        self.assertIn("closed: 2026-09-02 (parked)", text)
        self.assertIn("left: unshipped working tree", text)
        self.assertIn("next: python3 -m z2s.feature open", text)

    def test_usage(self):
        code, text = self.invoke("nonsense")
        self.assertEqual(2, code)
        self.assertIn("usage:", text)


if __name__ == "__main__":
    unittest.main()
