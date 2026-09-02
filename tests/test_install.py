# -*- coding: utf-8 -*-
"""Does an install actually yield a working chain? (M13-P3-T2)

M13-P3-T2-C1 asks for a clean-machine install that produces a working chain, and
the honest question underneath it is narrower than it sounds: an install puts the
plugin somewhere that is not this repository, and then the operator drives some
other project with it. Two things can go wrong there and neither shows up in any
other test in this suite —

  * the plugin quietly depends on something it does not ship (the test suite, the
    published documents, the self-hosting scripts), so it works here and nowhere
    else; and
  * the commands the skill definitions tell an agent to run are not the commands
    that work.

So this copies **only what the plugin ships** to a fresh directory, makes a
separate empty project somewhere else, and drives the chain from one against the
other by running the real command lines in real subprocesses.

Stated ceiling, because it is the part that is not proved: this does not install
into Claude Code and does not check that the runtime lists the skills. That needs
the runtime, and the criterion covering it is the human-review one below. What is
proved is that the shipped plugin is self-contained and that every command its
definitions name really runs from an installed location against a foreign project.

Traces: FR-SKL-08, FR-SKL-09, NFR-ARC-03, NFR-SKL-04, ADR-18, US-SKL-06,
US-SKL-07.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import pack, paths, steps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Exactly what a marketplace install of this plugin puts on disk. Everything
#: else in the repository — the tests, the published documents, the self-hosting
#: build — is developer material, and the plugin must not need any of it.
SHIPPED = ("z2s", "skills", "reference", ".claude-plugin", "skills.lock.json")


def installed(where):
    """A copy of the plugin, as an install would leave it, and nothing else."""
    target = os.path.join(where, "plugin")
    os.makedirs(target)
    for name in SHIPPED:
        source = os.path.join(ROOT, name)
        if os.path.isdir(source):
            shutil.copytree(source, os.path.join(target, name),
                            ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(source, os.path.join(target, name))
    return target


class Installed(unittest.TestCase):
    """The plugin at a foreign path, driving a project it has never seen."""

    def setUp(self):
        self.holder = tempfile.mkdtemp(prefix="z2s-install-")
        self.addCleanup(shutil.rmtree, self.holder, ignore_errors=True)
        self.plugin = installed(self.holder)
        self.project = os.path.join(self.holder, "somebody-elses-project")
        os.makedirs(self.project)

    def run_here(self, *arguments):
        """One command line, exactly as a skill definition spells it.

        `PYTHONPATH` is the plugin root and the working directory is the
        project, which is the arrangement `${CLAUDE_PLUGIN_ROOT}` produces. The
        environment is otherwise stripped of anything that might let the copy
        find this repository by accident.
        """
        environment = {"PATH": os.environ.get("PATH", ""),
                       "PYTHONPATH": self.plugin,
                       "HOME": self.holder}
        return subprocess.run([sys.executable] + list(arguments),
                              cwd=self.project, env=environment,
                              capture_output=True, text=True, check=False)


class TestThePluginIsSelfContained(Installed):
    """It works here because everything is here. That proves nothing."""

    def test_the_toolchain_imports_with_nothing_but_the_plugin_on_the_path(self):
        done = self.run_here("-c", "import z2s.steps, z2s.author, z2s.pack, "
                                   "z2s.project, z2s.ship, z2s.update, "
                                   "z2s.gauntlet, z2s.restyle")
        self.assertEqual(0, done.returncode, done.stderr)

    def test_it_needs_no_third_party_package(self):
        """NFR-ARC-03. The environment above carries no site-packages this
        repository installed, so an accidental dependency fails here."""
        done = self.run_here("-c", "import z2s.plan; print('ok')")
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertIn("ok", done.stdout)

    def test_nothing_shipped_reaches_back_into_the_repository(self):
        for where, _, names in os.walk(os.path.join(self.plugin, "z2s")):
            for name in names:
                if not name.endswith(".py"):
                    continue
                with open(os.path.join(where, name), encoding="utf-8") as handle:
                    body = handle.read()
                self.assertNotIn("from tests", body, name)
                self.assertNotIn("import selfhost", body, name)

    def test_the_lock_still_matches_after_being_copied(self):
        """A pin that only holds in its own repository is not a pin."""
        self.assertEqual([], pack.check(self.plugin))


class TestSetupHappensByItself(Installed):
    """FR-SKL-09 / M13-P1-T4-C2, from the installed side."""

    def test_init_sets_up_a_project_it_has_never_seen(self):
        done = self.run_here("-m", "z2s.project", "--root", ".")
        self.assertEqual(0, done.returncode, done.stderr)
        for relative in paths.DIRECTORIES:
            self.assertTrue(os.path.isdir(os.path.join(self.project, relative)),
                            relative)

    def test_running_it_twice_changes_nothing_it_reports(self):
        self.run_here("-m", "z2s.project", "--root", ".")
        done = self.run_here("-m", "z2s.project", "--root", ".")
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertIn("already complete", done.stdout)

    def test_no_step_asks_the_operator_for_a_shell_command(self):
        """NFR-SKL-04: a step whose instructions ask the operator to type a
        shell command is a defect in that step. Every command in a definition is
        one the agent runs itself, and this checks the definitions say so."""
        for one in steps.CHAIN:
            with open(pack.skill_path(ROOT, one), encoding="utf-8") as handle:
                body = handle.read()
            for phrase in ("ask the operator to run", "have the operator run",
                           "tell the user to run", "run this yourself in a terminal"):
                self.assertNotIn(phrase, body.lower(), one.name)


class TestTheChainRunsFromAnInstall(Installed):
    """M13-P3-T2-C1: a clean install yields a working chain."""

    def setUp(self):
        super(TestTheChainRunsFromAnInstall, self).setUp()
        self.run_here("-m", "z2s.project", "--root", ".")

    def test_the_position_of_an_empty_project_is_reported(self):
        done = self.run_here("-m", "z2s.steps", "--root", ".")
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertIn("the set is empty", done.stdout)
        self.assertIn("next: /zero:intent", done.stdout)

    def test_asking_for_instructions_with_no_plan_refuses_rather_than_guessing(self):
        """`/zero:prompt` prints what the plan carries, so with no plan there is
        nothing to print — and inventing one would be inventing the work."""
        done = self.run_here("-m", "z2s.gauntlet", "M1-P1-T1", "--root", ".")
        self.assertEqual(1, done.returncode, done.stderr)
        self.assertIn("generate the plan first", done.stdout)

    def test_asking_for_instructions_with_no_unit_named_is_a_misuse(self):
        done = self.run_here("-m", "z2s.gauntlet", "--root", ".")
        self.assertEqual(2, done.returncode, done.stderr)
        self.assertIn("usage", done.stdout)

    def test_a_step_with_a_missing_prerequisite_refuses_by_name(self):
        done = self.run_here("-m", "z2s.author", "run", "fsd", "--root", ".")
        self.assertEqual(1, done.returncode)
        self.assertIn("PRD.html", done.stdout)
        self.assertIn("/zero:intent", done.stdout)

    def test_the_whole_first_step_runs_end_to_end(self):
        """The interview loop the intent skill spells out, run for real: write a
        brief, get asked, answer, get asked again, answer, get a document."""
        target = os.path.join(self.project, paths.LEDGER_DIR, "briefs")
        os.makedirs(target)
        with open(os.path.join(target, "intent.json"), "w",
                  encoding="utf-8") as handle:
            handle.write(BRIEF)

        for _ in range(6):
            done = self.run_here("-m", "z2s.author", "run", "intent", "--root", ".")
            if done.returncode != 3:
                break
            fork = re.search(r"^fork: (\S+)", done.stdout, re.M).group(1)
            choice = re.search(r"^  (\S+) — .*\(recommended\)", done.stdout,
                               re.M).group(1)
            self.run_here("-m", "z2s.author", "answer", "intent", fork, choice,
                          "--why", "Chosen while proving the install.", "--root", ".")

        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        self.assertTrue(os.path.exists(os.path.join(
            self.project, paths.SPECS_DIR, "Intent.html")))

    def test_the_document_it_produced_passes_the_toolchain_s_own_gate(self):
        """A file appearing is not a working chain. A file that passes the
        validator is."""
        self.test_the_whole_first_step_runs_end_to_end()
        done = self.run_here("-m", "z2s.validate",
                             os.path.join(paths.SPECS_DIR, "Intent.html"))
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)

    def test_restyling_an_installed_project_leaves_its_document_alone(self):
        """The last command `/zero:design` runs, driven the way an install runs
        it. A restyle of a project whose design has not moved must produce the
        bytes already on disk — otherwise every operator who followed the skill
        would get a diff of noise across their whole set."""
        self.test_the_whole_first_step_runs_end_to_end()
        target = os.path.join(self.project, paths.SPECS_DIR, "Intent.html")
        with open(target, encoding="utf-8") as handle:
            before = handle.read()

        done = self.run_here("-m", "z2s.restyle", "--root", ".")
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        self.assertIn("already current", done.stdout)
        with open(target, encoding="utf-8") as handle:
            self.assertEqual(before, handle.read())

    def test_the_chain_then_reports_the_next_step(self):
        self.test_the_whole_first_step_runs_end_to_end()
        done = self.run_here("-m", "z2s.steps", "--root", ".")
        self.assertIn("the chain reaches intent", done.stdout)
        self.assertIn("next: /zero:context", done.stdout)


class TestTheInstallInstructions(unittest.TestCase):
    """M13-P3-T2-C2 is a human-review criterion — whether the instructions read
    well is a judgement. That they are exactly two commands is not, so it is
    checked here rather than left to the reviewer to count."""

    def test_the_published_instructions_are_exactly_two_commands(self):
        self.assertEqual(2, len(_install_step()["commands"]))

    def test_they_name_the_plugin_an_install_actually_produces(self):
        """If the manifest and the instructions disagree, the second command
        fails for everybody who follows the documentation."""
        stated = " ".join(_install_step()["commands"])
        self.assertIn("%s@" % steps.PLUGIN, stated)


def _install_step():
    """The published step A1, read from the specification that renders it.

    Read rather than restated: the whole claim is about what an operator who
    follows the documentation types, so a copy of the instructions here would
    make the test pass while the documentation said something else.
    """
    sys.path.insert(0, os.path.join(ROOT, "docs", "_build"))
    from specs import playbook                          # noqa: E402
    for section in playbook.SECTIONS:
        for group in section.get("groups") or ():
            for one in group["steps"]:
                if one["id"] == "S-A1":
                    return one
    raise AssertionError("the playbook no longer carries an install step")


BRIEF = """{
  "title": "Somebody Else's Project",
  "owner": "An operator who has just installed the plugin",
  "date": "2026-08-15",
  "problem": "Nobody can tell what this project is for.",
  "sources": [{"kind": "narrative", "name": "Install check",
               "origin": "Recorded during the install verification",
               "contributed": "The problem and both capabilities."}]
}
"""


if __name__ == "__main__":
    unittest.main()
