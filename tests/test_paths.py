# -*- coding: utf-8 -*-
"""The layout follows the open feature (FR-GEN-12, NFR-OPS-07).

A project with no `features/` directory resolves every path exactly as it
always did — that is the whole of the back-compatibility promise, and the
first class here pins it. With a feature open, the three directories that
belong to a piece of work (specifications, plan, run state) move under the
feature; everything the project shares stays where it was.

Traces: FR-GEN-01, FR-GEN-12, NFR-OPS-01, NFR-OPS-07, ADR-19.
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import chain, context, document, intent, paths, steps, writer
from tests.test_validate import spec as document_spec


class Project(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-paths-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        paths.ensure_layout(self.root)

    def feature(self, number, slug="checkout"):
        made = paths.shared(self.root, paths.feature_dir(number, slug))
        os.makedirs(made)
        paths.ensure_layout(self.root)
        return made

    def place(self, filename, slug, shared=False):
        made = document_spec(slug=slug)
        made["document"]["slug"] = slug
        return chain.write(self.root, filename, made, slug + "-spec", shared=shared)


class TestAProjectWithNoFeaturesIsUntouched(Project):
    """L9: byte for byte what it was. Every constant resolves as before."""

    def test_every_documented_location_resolves_under_the_root(self):
        for relative in paths.DIRECTORIES + (paths.WORKERS_FILE, paths.DESIGN_FILE,
                                             paths.IGNORE_FILE):
            self.assertEqual(os.path.join(self.root, relative),
                             paths.resolve(self.root, relative))

    def test_resolve_and_shared_agree(self):
        for relative in paths.SCOPED:
            self.assertEqual(paths.shared(self.root, relative, "x.html"),
                             paths.resolve(self.root, relative, "x.html"))

    def test_there_is_no_open_feature(self):
        self.assertIsNone(paths.feature(self.root))
        self.assertEqual([], paths.features(self.root))

    def test_an_empty_features_directory_is_no_feature(self):
        os.makedirs(paths.shared(self.root, paths.FEATURES_DIR))
        self.assertIsNone(paths.feature(self.root))

    def test_a_directory_that_is_not_shaped_like_a_feature_is_ignored(self):
        os.makedirs(paths.shared(self.root, paths.FEATURES_DIR, "notes"))
        os.makedirs(paths.shared(self.root, paths.FEATURES_DIR, "01-short"))
        os.makedirs(paths.shared(self.root, paths.FEATURES_DIR, "001-Upper"))
        self.assertIsNone(paths.feature(self.root))


class TestTheOpenFeatureMovesTheScopedDirectories(Project):

    def test_the_scoped_directories_follow_the_feature(self):
        self.feature(1)
        for relative in paths.SCOPED:
            self.assertEqual(
                os.path.join(self.root, paths.FEATURES_DIR, "001-checkout",
                             os.path.basename(relative)),
                paths.resolve(self.root, relative))

    def test_a_path_below_a_scoped_directory_follows_too(self):
        self.feature(1)
        self.assertEqual(
            os.path.join(self.root, paths.FEATURES_DIR, "001-checkout",
                         "plan", "_build", "details", "M1.json"),
            paths.resolve(self.root, paths.PLAN_DETAILS_DIR, "M1.json"))
        self.assertTrue(paths.resolve(self.root, paths.LEDGER_DIR + "/briefs", "x.json")
                        .startswith(paths.shared(self.root, paths.FEATURES_DIR)))

    def test_the_shared_layer_stays_where_it_was(self):
        self.feature(1)
        for relative in (paths.ROOT, paths.WORKERS_FILE, paths.DESIGN_FILE,
                         paths.IGNORE_FILE, paths.FEATURES_DIR):
            self.assertEqual(os.path.join(self.root, relative),
                             paths.resolve(self.root, relative))

    def test_shared_is_the_plain_join_whatever_is_open(self):
        self.feature(1)
        self.assertEqual(os.path.join(self.root, paths.SPECS_DIR, "Context.html"),
                         paths.shared(self.root, paths.SPECS_DIR, "Context.html"))

    def test_the_highest_numbered_feature_is_the_open_one(self):
        self.feature(2, "later")
        self.feature(1, "earlier")
        self.feature(10, "tenth")
        self.assertEqual(paths.FEATURES_DIR + "/010-tenth", paths.feature(self.root))
        self.assertEqual([(1, "earlier"), (2, "later"), (10, "tenth")],
                         paths.features(self.root))

    def test_the_layout_is_created_inside_the_feature(self):
        os.makedirs(paths.shared(self.root, paths.feature_dir(1, "checkout")))
        done = paths.ensure_layout(self.root)
        self.assertIn(paths.SPECS_DIR, done["created"])
        self.assertTrue(os.path.isdir(os.path.join(
            self.root, paths.FEATURES_DIR, "001-checkout", "plan", "_build", "details")))
        self.assertIn(paths.IGNORE_FILE, done["existed"])

    def test_a_relative_href_from_the_plan_to_the_shared_specs(self):
        self.assertEqual("../specs", paths.toward(self.root, paths.PLAN_DIR,
                                                   paths.SPECS_DIR, shared=True))
        self.feature(1)
        self.assertEqual("../specs", paths.toward(self.root, paths.PLAN_DIR, paths.SPECS_DIR))
        self.assertEqual("../../../specs", paths.toward(self.root, paths.PLAN_DIR,
                                                         paths.SPECS_DIR, shared=True))


class TestWhichDocumentsAreTheSet(Project):

    def test_with_no_feature_the_set_is_specs_and_plan(self):
        self.place("Context.html", "context", shared=True)
        self.place("FSD.html", "fsd")
        self.assertEqual(["Context.html", "FSD.html"],
                         [os.path.basename(one) for one in paths.documents(self.root)])

    def test_a_feature_document_stands_in_for_the_shared_one_of_the_same_name(self):
        self.place("Context.html", "context", shared=True)
        self.place("Intent.html", "intent", shared=True)
        self.place("FSD.html", "fsd", shared=True)
        self.feature(1)
        self.place("Intent.html", "intent")
        found = paths.specs(self.root)
        names = [os.path.relpath(one, self.root) for one in found]
        self.assertEqual([".zero/features/001-checkout/specs/Intent.html",
                          ".zero/specs/Context.html", ".zero/specs/FSD.html"], names)


class TestTheChainReadsAndWritesThroughTheSeam(Project):

    def test_a_shared_write_lands_beside_the_project(self):
        self.feature(1)
        shared = self.place("Context.html", "context", shared=True)
        scoped = self.place("PRD.html", "prd")
        self.assertEqual(paths.shared(self.root, paths.SPECS_DIR, "Context.html"), shared)
        self.assertEqual(os.path.join(self.root, paths.FEATURES_DIR, "001-checkout",
                                      "specs", "PRD.html"), scoped)
        self.assertEqual("context", chain.require(
            self.root, "Context.html", "context", "a test", shared=True)["document"]["slug"])
        with self.assertRaises(chain.MissingPrerequisite):
            chain.require(self.root, "Context.html", "context", "a test")

    def test_the_context_is_the_one_shared_document(self):
        """L19: the only document the chain writes and reads beside the project."""
        self.feature(1)
        self.assertEqual(paths.shared(self.root, paths.SPECS_DIR, context.FILENAME),
                         steps.document_path(self.root, steps.step("context")))
        self.assertEqual(paths.resolve(self.root, paths.SPECS_DIR, intent.FILENAME),
                         steps.document_path(self.root, steps.step("intent")))

    def test_an_old_vision_document_satisfies_a_need_for_the_intent(self):
        """L2 / NFR-OPS-07: a project built before the rename is not asked to
        rename anything. The alias is the one filename that has one."""
        made = document_spec(slug="vision")
        made["document"]["slug"] = "vision"
        target = paths.resolve(self.root, paths.SPECS_DIR, "Vision.html")
        writer.write(target, document.render(made, "vision-spec"))
        found = chain.require(self.root, intent.FILENAME, intent.SLUG, "the context generator")
        self.assertEqual("vision", found["document"]["slug"])
        self.assertTrue(steps.completed(self.root, steps.step("intent")))

    def test_the_alias_covers_no_other_filename(self):
        made = document_spec(slug="fsd")
        writer.write(paths.resolve(self.root, paths.SPECS_DIR, "Old-FSD.html"),
                     document.render(made, "fsd-spec"))
        with self.assertRaises(chain.MissingPrerequisite):
            chain.require(self.root, "FSD.html", "fsd", "a test")

    def test_a_new_intent_wins_over_an_old_vision(self):
        for filename, slug in (("Vision.html", "vision"), ("Intent.html", "intent")):
            made = document_spec(slug=slug)
            made["document"]["slug"] = slug
            writer.write(paths.resolve(self.root, paths.SPECS_DIR, filename),
                         document.render(made, slug + "-spec"))
        found = chain.require(self.root, intent.FILENAME, intent.SLUG, "a test")
        self.assertEqual("intent", found["document"]["slug"])


if __name__ == "__main__":
    unittest.main()
