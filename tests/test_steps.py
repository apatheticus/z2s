# -*- coding: utf-8 -*-
"""The chain definition (M13-P1-T2, M13-P2-T1).

Two things are being checked here, and they pull in opposite directions. The
chain has to be one definition — four callers reading one table, not four
tables — and it has to refuse in words an operator can act on. A refusal that
merely says "prerequisites not met" satisfies the first and fails the second.

Traces: FR-SKL-01, FR-SKL-02, FR-SKL-05, NFR-SKL-02, US-SKL-01, US-SKL-03.
"""

import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import paths, steps, writer

from tests.test_validate import spec

PACKAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "z2s")


class Sandbox(unittest.TestCase):
    """A project root that starts genuinely empty."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-steps-")
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)
        paths.ensure_layout(self.folder)

    def place(self, slug, filename=None, folder=None, contents=None):
        """Put a completed document for one step into the project."""
        one = steps.BY_SLUG[slug]
        target = steps.document_path(self.folder, one)
        writer.write(target, contents if contents is not None
                     else _document(slug))
        return target


def _document(slug):
    """A document carrying a readable specification for `slug`."""
    from z2s import document
    return document.render(spec(slug=slug), "%s-spec" % slug)


class TestTheChainIsOneDefinition(unittest.TestCase):
    """M13-P1-T1. Every skill the plugin ships, and one place that says so."""

    def test_every_published_skill_is_in_the_chain(self):
        self.assertEqual(
            ["init", "vision", "context", "prd", "fsd", "stories", "sdd",
             "plan", "build", "prompt", "action", "update", "ship", "questions"],
            [one.name for one in steps.CHAIN])

    def test_the_chain_is_the_documents_and_the_operations_and_nothing_else(self):
        self.assertEqual(len(steps.CHAIN),
                         len(steps.DOCUMENTS) + len(steps.OPERATIONS))
        self.assertEqual(set(steps.CHAIN),
                         set(steps.DOCUMENTS) | set(steps.OPERATIONS))

    def test_a_step_is_found_by_skill_name_or_document_slug(self):
        """Both spellings are in daily use — an operator types one and the
        toolchain speaks the other — and making a caller convert between them is
        how the two drift apart."""
        self.assertIs(steps.step("fsd"), steps.step(steps.BY_SLUG["fsd"].name))

    def test_an_unknown_step_names_the_whole_chain_rather_than_just_refusing(self):
        with self.assertRaises(steps.UnknownStep) as caught:
            steps.step("architecture")
        self.assertIn("vision", str(caught.exception))
        self.assertIn("questions", str(caught.exception))

    def test_an_operating_step_writes_no_document(self):
        """Resume must never propose one as the next thing to generate."""
        for one in steps.OPERATIONS:
            self.assertIsNone(one.module)
            self.assertIsNone(one.after)

    def test_the_command_an_operator_types_is_derived_from_the_plugin_name(self):
        """Claude Code namespaces a plugin's skills under the plugin's own name
        (M13-08), so the prefix is a fact about the manifest, not a string this
        module gets to choose independently."""
        self.assertEqual("/zero:vision", steps.command(steps.step("vision")))
        self.assertTrue(all(steps.command(one).startswith("/%s:" % steps.PLUGIN)
                            for one in steps.CHAIN))


class TestPrerequisiteRefusal(Sandbox):
    """M13-P1-T2-C1: a refusal names the missing document and leaves the
    repository untouched."""

    def test_the_first_step_needs_nothing(self):
        self.assertIsNone(steps.refusal(self.folder, steps.step("vision")))

    def test_a_refusal_names_the_missing_document(self):
        found = steps.refusal(self.folder, steps.step("fsd"))
        self.assertIn("PRD.html", found)
        self.assertIn("Context.html", found)

    def test_a_refusal_names_the_command_that_fixes_it(self):
        """"Prerequisites not met" tells an operator nothing about what to do
        next, and refusing early is only worth doing if the next action is
        obvious."""
        self.assertIn("Run /zero:vision first",
                      steps.refusal(self.folder, steps.step("fsd")))

    def test_the_command_named_is_the_earliest_gap_in_the_whole_chain(self):
        """The plan needs the functional specification, which needs the product
        requirements, which needs the context. Naming the plan's own nearest
        prerequisite would send the operator to a step that refuses in turn —
        one document per round trip — so the instruction comes from the same
        probe resume reads."""
        self.place("vision")
        self.assertIn("Run /zero:context first",
                      steps.refusal(self.folder, steps.step("plan")))
        self.place("context")
        self.assertIn("Run /zero:prd first",
                      steps.refusal(self.folder, steps.step("plan")))
        self.place("prd")
        self.assertIn("Run /zero:fsd first",
                      steps.refusal(self.folder, steps.step("plan")))

    def test_the_refusal_and_the_resume_probe_can_never_disagree(self):
        """M13-P2-T1 refactor. One completeness probe, two readers."""
        self.place("vision")
        for one in (steps.step("plan"), steps.step("stories")):
            self.assertIn(steps.command(steps.following(self.folder)),
                          steps.refusal(self.folder, one))

    def test_a_satisfied_step_is_not_refused(self):
        self.place("vision")
        self.assertIsNone(steps.refusal(self.folder, steps.step("context")))

    def test_the_probe_writes_nothing(self):
        """NFR-SKL-02: a prerequisite check reads the set without side effects."""
        before = sorted(os.listdir(paths.resolve(self.folder, paths.SPECS_DIR)))
        for one in steps.DOCUMENTS:
            steps.refusal(self.folder, one)
            steps.completed(self.folder, one)
        self.assertEqual(before,
                         sorted(os.listdir(paths.resolve(self.folder,
                                                         paths.SPECS_DIR))))

    def test_a_document_that_exists_but_carries_no_specification_is_not_complete(self):
        """A damaged file is the state an operator most needs told apart from a
        finished one, and existence alone cannot tell them apart."""
        self.place("vision", contents="<html><body>nothing here</body></html>")
        self.assertFalse(steps.completed(self.folder, steps.step("vision")))
        self.assertIsNotNone(steps.refusal(self.folder, steps.step("context")))

    def test_a_document_of_the_wrong_kind_does_not_satisfy_the_step(self):
        self.place("vision", contents=_document("prd"))
        self.assertFalse(steps.completed(self.folder, steps.step("vision")))


class TestWhereTheChainStands(Sandbox):
    """M13-P2-T1-C1: resume continues correctly from every chain position,
    including an empty set."""

    def test_an_empty_set_starts_at_the_vision(self):
        self.assertIs(steps.NOTHING, steps.position(self.folder))
        self.assertEqual("vision", steps.following(self.folder).name)

    def test_every_position_in_the_chain_reports_the_next_step(self):
        for index, one in enumerate(steps.DOCUMENTS[:-1]):
            self.place(one.module.SLUG)
            self.assertEqual(one.name, steps.position(self.folder).name)
            self.assertEqual(steps.DOCUMENTS[index + 1].name,
                             steps.following(self.folder).name)

    def test_a_complete_set_has_nothing_left_to_generate(self):
        for one in steps.DOCUMENTS:
            self.place(one.module.SLUG)
        self.assertEqual("plan", steps.position(self.folder).name)
        self.assertIsNone(steps.following(self.folder))
        self.assertIn("/zero:build", steps.format_position(self.folder))

    def test_the_walk_stops_at_the_first_gap_not_the_last_file(self):
        """A document left behind by an abandoned run, downstream of a hole, is
        not progress — and a resume that counted it would send the operator past
        the missing document rather than at it."""
        self.place("vision")
        self.place("sdd")
        self.assertEqual("vision", steps.position(self.folder).name)
        self.assertEqual("context", steps.following(self.folder).name)

    def test_the_report_states_what_is_written_before_what_comes_next(self):
        self.place("vision")
        found = steps.format_position(self.folder)
        self.assertLess(found.index("vision"), found.index("next:"))
        self.assertIn("next: /zero:context", found)

    def test_the_command_reports_and_changes_nothing(self):
        out = io.StringIO()
        self.assertEqual(0, steps.main(["--root", self.folder], out))
        self.assertIn("the set is empty", out.getvalue())
        self.assertEqual([], os.listdir(paths.resolve(self.folder,
                                                      paths.SPECS_DIR)))


if __name__ == "__main__":
    unittest.main()
