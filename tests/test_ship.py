# -*- coding: utf-8 -*-
"""Shipping the working branch, and stopping at the offer (M13-P2-T3).

M13-P2-T3-C1 is the whole point: a pull request is created only on an explicit
yes. Commit and push are recoverable; opening a pull request is an announcement
to other people, and consent read from context is consent nobody gave.

These run against real git repositories in a temporary directory — a fake would
prove the fake. The push half uses a bare repository as the remote, so a real
push really happens without anything leaving the machine.

Traces: FR-SKL-07, FR-EXE-11, FR-EXE-12, NFR-SEC-04, US-SKL-05.
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import safety, ship

PACKAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "z2s")


def git(folder, *arguments):
    return subprocess.run(["git", "-C", folder] + list(arguments),
                          capture_output=True, text=True, check=True)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


class Repository(unittest.TestCase):
    """A real working branch with a real remote, both on disk."""

    def setUp(self):
        self.holder = tempfile.mkdtemp(prefix="z2s-ship-")
        self.addCleanup(shutil.rmtree, self.holder, ignore_errors=True)
        self.remote = os.path.join(self.holder, "remote.git")
        self.folder = os.path.join(self.holder, "work")
        subprocess.run(["git", "init", "--bare", "-b", "main", self.remote],
                       capture_output=True, check=True)
        subprocess.run(["git", "init", "-b", "main", self.folder],
                       capture_output=True, check=True)
        git(self.folder, "config", "user.email", "test@example.invalid")
        git(self.folder, "config", "user.name", "Test")
        git(self.folder, "remote", "add", "origin", self.remote)
        self.change("first.txt", "one\n")
        git(self.folder, "add", "--all")
        git(self.folder, "commit", "-m", "first")

    def change(self, name, contents):
        with open(os.path.join(self.folder, name), "w", encoding="utf-8") as handle:
            handle.write(contents)

    def invoke(self, *argv):
        out = io.StringIO()
        code = ship.main(list(argv) + ["--root", self.folder], out)
        return code, out.getvalue()

    def log(self):
        return git(self.folder, "log", "--format=%s").stdout.split()


class TestCommittingAndPushing(Repository):

    def test_it_commits_everything_on_the_branch(self):
        self.change("second.txt", "two\n")
        ship.commit(self.folder, "add the second file")
        self.assertIn("add", self.log())
        self.assertFalse(ship.pending(self.folder))

    def test_a_clean_tree_is_not_an_error(self):
        """A branch already committed and merely unpushed is the common case,
        and refusing it would make the skill useless exactly then."""
        self.assertIsNone(ship.commit(self.folder, "nothing to do"))
        code, said = self.invoke("--message", "nothing to do")
        self.assertEqual(0, code)
        self.assertIn("nothing to commit", said)

    def test_it_pushes_the_working_branch(self):
        self.change("second.txt", "two\n")
        code, said = self.invoke("--message", "add the second file")
        self.assertEqual(0, code)
        self.assertIn("pushed: main", said)
        self.assertIn("add the second file",
                      subprocess.run(["git", "-C", self.remote, "log",
                                      "--format=%s"], capture_output=True,
                                     text=True, check=True).stdout)

    def test_a_detached_head_refuses_rather_than_guessing_a_branch(self):
        git(self.folder, "checkout", "--detach", "HEAD")
        code, said = self.invoke("--message", "anything")
        self.assertEqual(1, code)
        self.assertIn("detached", said)

    def test_a_commit_needs_a_subject_somebody_chose(self):
        code, said = self.invoke()
        self.assertEqual(2, code)
        self.assertIn("--message", said)


class TestTheOffer(Repository):
    """M13-P2-T3-C1: created only on an explicit yes."""

    def test_a_plain_run_stops_at_the_offer(self):
        self.change("second.txt", "two\n")
        code, said = self.invoke("--message", "add the second file")
        self.assertEqual(0, code)
        self.assertIn("Open a pull request", said)
        self.assertIn("Nothing has been opened", said)

    def test_the_offer_creates_nothing(self):
        """Returning the words rather than asking them is what keeps the
        decision with the operator: this cannot hear a yes it was not given."""
        found = ship.offer(self.folder)
        self.assertIn(ship.CONSENT, found)
        self.assertNotIn("https://", found)

    def test_a_pull_request_without_consent_is_refused(self):
        code, said = self.invoke("pull-request", "--title", "Add the thing")
        self.assertEqual(1, code)
        self.assertIn(ship.CONSENT, said)

    def test_the_consent_check_happens_before_anything_else(self):
        """No path through the function may reach the creation without having
        passed it — including one that would have failed for another reason."""
        git(self.folder, "checkout", "--detach", "HEAD")
        with self.assertRaises(ship.Refused) as caught:
            ship.pull_request(self.folder, "Add", "body", False)
        self.assertIn(ship.CONSENT, str(caught.exception))
        self.assertNotIn("detached", str(caught.exception))

    def test_a_consented_pull_request_still_needs_a_title(self):
        with self.assertRaises(ship.Refused) as caught:
            ship.pull_request(self.folder, "", "body", True)
        self.assertIn("title", str(caught.exception))


class TestWhatIsRefused(Repository):
    """NFR-SEC-04. The never-do rules are asked, not reimplemented."""

    def test_every_git_command_goes_past_the_rules_first(self):
        self.assertIn("safety.refusal", read(os.path.join(PACKAGE, "ship.py")))

    def test_the_module_spells_no_prohibited_operation_of_its_own(self):
        """M6-08: the execution layer calls the judge, never its own matching."""
        body = read(os.path.join(PACKAGE, "ship.py"))
        for forbidden in ("--force", "filter-branch", "branch -D",
                          "push -f", "reset --hard"):
            self.assertNotIn(forbidden, body)

    def test_a_prohibited_command_is_refused_before_it_runs(self):
        with self.assertRaises(ship.Refused) as caught:
            ship._git(self.folder, "push", "--force", "origin", "main")
        self.assertIn("refused", str(caught.exception))

    def test_the_judge_is_the_shared_one(self):
        """Appending an operation to safety.PROHIBITED must reach this module
        with no change here."""
        self.assertTrue(safety.prohibited("git push --force origin main"))


if __name__ == "__main__":
    unittest.main()
