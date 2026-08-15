# -*- coding: utf-8 -*-
"""The skill definitions and the plugin that ships them (M13-P1-T1, T3, P3-T1).

These tests read the definitions that actually ship, in the repository, rather
than a fixture. That is deliberate: the failure this milestone exists to prevent
is a skill that behaves differently once installed, and a test over a fixture
proves the fixture.

The trigger-policy lint is checked in BOTH directions. A lint that only caught a
missing manual-only marking would pass a build in which every skill, interviewer
included, had been quietly locked down — and a chain whose interview cannot fire
is a chain that guesses instead of asking.

Traces: FR-SKL-01, FR-SKL-03, FR-SKL-04, FR-SKL-08, NFR-SKL-01, NFR-SKL-03,
ADR-18, US-SKL-01, US-SKL-02, US-SKL-06.
"""

import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import pack, steps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


class TestEveryChainStepShips(unittest.TestCase):
    """M13-P1-T1-C1: each chain step is invocable by its documented name."""

    def test_every_step_has_a_definition(self):
        for one in steps.CHAIN:
            self.assertTrue(os.path.exists(pack.skill_path(ROOT, one)), one.name)

    def test_the_skills_directory_holds_nothing_the_chain_does_not_declare(self):
        """A skill nobody declared is a skill the lock does not pin and the
        documentation does not mention, and it still installs."""
        present = sorted(name for name in
                         os.listdir(os.path.join(ROOT, pack.SKILLS_DIR))
                         if not name.startswith("."))
        self.assertEqual(sorted(one.name for one in steps.CHAIN), present)

    def test_each_definition_names_itself_as_the_chain_names_it(self):
        for one in steps.CHAIN:
            _, header = pack.read_skill(ROOT, one)
            self.assertEqual(one.name, header["name"])

    def test_each_definition_carries_a_description(self):
        """The runtime lists a skill by its description; without one the
        operator has fourteen names and no idea which to reach for."""
        for one in steps.CHAIN:
            _, header = pack.read_skill(ROOT, one)
            self.assertTrue(header["description"].strip(), one.name)

    def test_every_definition_points_at_the_one_shared_preamble(self):
        """M13-P1-T1 refactor: the prerequisite rule, the interview rule and the
        report contract are stated once. Fourteen copies would drift."""
        for one in steps.CHAIN:
            self.assertIn("reference/chain-rules.md",
                          read(pack.skill_path(ROOT, one)), one.name)

    def test_the_shared_preamble_exists(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "reference",
                                                    "chain-rules.md")))


class CopiedPlugin(unittest.TestCase):
    """The shipped definitions, copied somewhere they can be broken on purpose.

    Shared by the lint tests and the lock tests deliberately: the lock is built
    over the same definitions the lint reads, and giving each its own setup is
    how two suites quietly stop testing the same thing.
    """

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-skills-")
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)
        shutil.copytree(os.path.join(ROOT, pack.SKILLS_DIR),
                        os.path.join(self.folder, pack.SKILLS_DIR))
        shutil.copytree(os.path.join(ROOT, ".claude-plugin"),
                        os.path.join(self.folder, ".claude-plugin"))

    def rewrite(self, name, old, new):
        """Change one definition, asserting the text being replaced was there.

        The assertion is what keeps a mutation honest: a replacement that
        matched nothing would leave the definition sound and the test green.
        """
        path = pack.skill_path(self.folder, steps.step(name))
        text = read(path)
        self.assertIn(old, text)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text.replace(old, new, 1))


class TestTriggerPolicy(CopiedPlugin):
    """M13-P1-T3. NFR-SKL-01: the policy lives where the runtime enforces it.

    A trigger rule stated only in documentation is a request; one stated in the
    definition is a contract.
    """

    def test_the_shipped_set_passes_the_lint(self):
        self.assertEqual([], pack.triggers(ROOT))

    def test_every_chain_skill_is_marked_manual_only(self):
        """M13-P1-T3-C1."""
        for one in steps.CHAIN:
            if one.name == steps.INTERVIEWER:
                continue
            _, header = pack.read_skill(ROOT, one)
            self.assertEqual("true", header.get(pack.MANUAL_ONLY), one.name)

    def test_only_the_interview_may_fire_on_its_own(self):
        """M13-P1-T3-C2."""
        _, header = pack.read_skill(ROOT, steps.step(steps.INTERVIEWER))
        self.assertNotIn(pack.MANUAL_ONLY, header)

    def test_a_chain_skill_that_loses_its_marking_is_caught(self):
        self.rewrite("vision", "%s: true" % pack.MANUAL_ONLY,
                     "argument-hint: [anything]")
        faults = pack.triggers(self.folder)
        self.assertEqual(1, len(faults))
        self.assertIn("vision", faults[0])

    def test_an_interview_that_is_locked_down_is_caught(self):
        """The half a one-directional lint would miss. A chain whose interview
        cannot fire is a chain that guesses instead of asking."""
        self.rewrite(steps.INTERVIEWER, "argument-hint:",
                     "%s: true\nargument-hint:" % pack.MANUAL_ONLY)
        faults = pack.triggers(self.folder)
        self.assertEqual(1, len(faults))
        self.assertIn(steps.INTERVIEWER, faults[0])

    def test_every_fault_is_reported_not_just_the_first(self):
        """An operator fixing definitions wants all of them, not one per run."""
        self.rewrite("vision", "%s: true" % pack.MANUAL_ONLY, "x-was-here: true")
        self.rewrite("ship", "%s: true" % pack.MANUAL_ONLY, "x-was-here: true")
        self.assertEqual(2, len(pack.triggers(self.folder)))

    def test_a_definition_with_no_frontmatter_is_caught(self):
        path = pack.skill_path(self.folder, steps.step("ship"))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("# just some prose\n")
        with self.assertRaises(pack.Broken) as caught:
            pack.read_skill(self.folder, steps.step("ship"))
        self.assertIn("frontmatter", str(caught.exception))

    def test_a_missing_definition_names_where_it_should_be(self):
        os.remove(pack.skill_path(self.folder, steps.step("ship")))
        with self.assertRaises(pack.Broken) as caught:
            pack.read_skill(self.folder, steps.step("ship"))
        self.assertIn("SKILL.md", str(caught.exception))


class TestTheLock(CopiedPlugin):
    """M13-P3-T1. NFR-SKL-03: the same reference resolves to the same skill set."""

    def test_two_builds_from_the_same_source_are_identical(self):
        """M13-P3-T1-C1. True because nothing here reads a clock or a random
        source, which is the same rule every other module follows."""
        self.assertEqual(pack.build(self.folder), pack.build(self.folder))

    def test_every_chain_skill_is_present_and_pinned(self):
        """M13-P3-T1-C2."""
        built = pack.build(self.folder)
        for one in steps.CHAIN:
            self.assertIn('"%s"' % one.name, built)
            self.assertIn(steps.command(one), built)
        self.assertEqual(len(steps.CHAIN), built.count('"sha256"'))

    def test_the_lock_is_generated_from_the_chain_not_maintained_by_hand(self):
        """M13-P3-T1 refactor. Adding a skill and forgetting the manifest is not
        a state this can reach."""
        self.assertIn("steps.CHAIN", read(os.path.join(ROOT, "z2s", "pack.py")))

    def test_a_changed_skill_changes_the_lock(self):
        before = pack.build(self.folder)
        path = pack.skill_path(self.folder, steps.step("vision"))
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("\nOne more sentence.\n")
        self.assertNotEqual(before, pack.build(self.folder))

    def test_the_shipped_lock_matches_the_shipped_skills(self):
        """The one that bites in practice: a skill edited and the lock left
        alone means the same reference resolves to a different skill set."""
        self.assertEqual([], pack.check(ROOT))

    def test_a_stale_lock_is_reported_rather_than_quietly_rebuilt(self):
        pack.write(self.folder)
        path = pack.skill_path(self.folder, steps.step("ship"))
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("\nOne more sentence.\n")
        differs = pack.check(self.folder)
        self.assertEqual(1, len(differs))
        self.assertIn("z2s.pack", differs[0])

    def test_a_missing_lock_says_how_to_write_it(self):
        differs = pack.check(self.folder)
        self.assertIn("is missing", differs[0])

    def test_the_check_writes_nothing(self):
        before = sorted(os.listdir(self.folder))
        pack.check(self.folder)
        self.assertEqual(before, sorted(os.listdir(self.folder)))

    def test_a_broken_trigger_policy_stops_the_build(self):
        """A plugin that ships an unmarked skill is not a plugin to pin; it is a
        plugin to fix."""
        self.rewrite("vision", "%s: true" % pack.MANUAL_ONLY, "x-was-here: true")
        with self.assertRaises(pack.Broken) as caught:
            pack.build(self.folder)
        self.assertIn("vision", str(caught.exception))
        self.assertIn(pack.MANUAL_ONLY, str(caught.exception))

    def test_the_manifest_name_is_the_prefix_operators_type(self):
        """If the two disagree, every command in the documentation is wrong."""
        self.assertIn('"%s"' % steps.PLUGIN,
                      read(os.path.join(ROOT, pack.MANIFEST)))
        self.assertEqual("1.0.0", pack.version(ROOT))


class TestTheCommand(unittest.TestCase):

    def test_the_check_passes_on_the_shipped_repository(self):
        out = io.StringIO()
        self.assertEqual(0, pack.main(["--check", "--root", ROOT], out))
        self.assertIn("14 skills", out.getvalue())

    def test_it_explains_itself_when_given_nonsense(self):
        out = io.StringIO()
        self.assertEqual(2, pack.main(["--wat"], out))
        self.assertIn("usage:", out.getvalue())


if __name__ == "__main__":
    unittest.main()
