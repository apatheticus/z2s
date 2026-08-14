# -*- coding: utf-8 -*-
"""The never-do rules (M6-P2).

Two prohibitions, checked here against the shapes a real leak and a real
destructive command actually take: no credential value in any artefact
(M6-P2-T1), and no destructive operation in an unattended run (M6-P2-T2).

Not one credential-shaped string is written into this file. Every seeded value
is BUILT — a prefix concatenated with filler — so that a scanner run over this
repository, this file included, finds nothing. A test fixture that trips the
project's own secret scanning is a test nobody can commit.

Traces: FR-GEN-04, FR-EXE-12, NFR-SEC-01, NFR-SEC-04.
"""

import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import safety
from z2s import schema
from z2s import validate

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: One example of every shape, assembled rather than written. The filler is
#: deliberately uniform: what is being tested is the shape, and a value that
#: looks convincing is a value somebody eventually mistakes for a real one.
#: Written as pairs rather than as a mapping on purpose: `"private-key": "…"`
#: is itself a secret-sounding name given a literal, and this file is scanned by
#: one of the tests below.
SEEDED = dict((
    ("github-token", "ghp_" + "A" * 36),
    ("openai-key", "sk-" + "B" * 32),
    ("aws-access-key", "AKIA" + "C" * 16),
    ("google-api-key", "AIza" + "D" * 35),
    ("slack-token", "xoxb-" + "1" * 12),
    ("private-key", "-----BEGIN RSA PRIVATE" + " KEY-----"),
    ("web-token", "eyJ" + "a" * 12 + ".eyJ" + "b" * 12 + "." + "c" * 16),
    ("url-credentials", "https://deploy:" + "s3cr3t" + "value@example.test/repo"),
))

#: A password with no shape at all, assembled so that this file does not contain
#: even a fake one written out.
WEAK = "hunter" + "2"


def document(body=""):
    """A minimal document with a readable specification block in it."""
    return ('<!doctype html><html><body>%s<script type="application/json">'
            '{"document": {"title": "Acme", "slug": "fsd", "type": "T", '
            '"version": "1.0", "status": "Draft", "date": "2026-08-14", '
            '"owner": "Acme"}, "schemaVersion": "1.0", '
            '"sections": [{"id": "purpose", "type": "prose", "body": "Why."}]}'
            '</script></body></html>' % body)


class Sandbox(unittest.TestCase):
    """A throwaway folder, so a seeded secret never touches the repository."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-safety-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def written(self, name, text):
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path


# ------------------------------------------------------- what counts as a secret

class TestASeededSecretIsFound(unittest.TestCase):

    def test_every_shape_this_tool_knows_is_caught(self):
        for name in SEEDED:
            found = safety.secrets_in("value = %s" % SEEDED[name], "f.txt")
            self.assertTrue(found, "%s was not recognised" % name)

    def test_a_finding_names_the_file_and_the_line(self):
        text = "first line\nsecond line\ntoken = %s\n" % SEEDED["github-token"]
        found = safety.secrets_in(text, "prompt.md")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].where, "prompt.md:3")
        self.assertIn("prompt.md:3", found[0].message)

    def test_a_leak_is_a_failure_never_a_warning(self):
        found = safety.secrets_in(SEEDED["aws-access-key"], "f.txt")
        self.assertEqual([one.severity for one in found], [schema.FAILURE])
        self.assertEqual([one.code for one in found], ["secret-literal"])

    def test_a_homemade_password_has_no_shape_and_is_still_caught(self):
        found = safety.secrets_in('password: "%s"' % WEAK, "config.yml")
        self.assertEqual(len(found), 1)
        self.assertIn("password", found[0].message)

    def test_one_mistake_is_reported_once(self):
        """A recognised value under a secret-sounding name is one leak, not two."""
        found = safety.secrets_in('GITHUB_TOKEN = "%s"' % SEEDED["github-token"],
                                  "f.txt")
        self.assertEqual(len(found), 1)

    def test_two_different_secrets_on_one_line_are_two_findings(self):
        found = safety.secrets_in("%s %s" % (SEEDED["aws-access-key"],
                                             SEEDED["slack-token"]), "f.txt")
        self.assertEqual(len(found), 2)

    def test_the_report_never_repeats_the_value(self):
        """The report is written to a log, a terminal, and whatever collects them."""
        secret = SEEDED["url-credentials"]
        text = 'password = "swordfishery"\nurl = "%s"\n' % secret
        said = " ".join(one.message for one in safety.secrets_in(text, "f.txt"))
        self.assertTrue(said)
        for value in ("swordfishery", "s3cr3tvalue", secret):
            self.assertNotIn(value, said)


class TestANameIsNotAValue(unittest.TestCase):
    """NFR-SEC-01: a secret may appear in an artefact only as a variable name."""

    def passes(self, line):
        self.assertEqual(safety.secrets_in(line, "f.txt"), [],
                         "%r should not be reported" % line)

    def test_a_name_on_its_own_passes(self):
        self.passes("The deploy step reads the token from GITHUB_TOKEN.")

    def test_a_name_read_from_the_environment_passes(self):
        self.passes('api_key = os.environ["API_KEY"]')
        self.passes('password = getenv("DB_PASSWORD")')
        self.passes('token: "${GITHUB_TOKEN}"')

    def test_a_placeholder_passes(self):
        self.passes('token: "<your-token-here>"')
        self.passes('password = "changeme"')
        self.passes('client_secret: "REPLACE_WITH_YOUR_SECRET"')
        self.passes('api_key = "xxxxxxxxxxxx"')

    def test_a_value_too_short_to_be_a_credential_passes(self):
        self.passes('token = "abc"')
        self.passes('password = ""')

    def test_a_name_that_only_sounds_like_a_secret_passes(self):
        """"key" alone is one of the commonest field names there is."""
        self.passes('sort_key = "created_at"')
        self.passes('tokenizer = "whitespace"')
        self.passes('partition_key: "customer_id"')

    def test_a_qualified_key_is_not_let_through(self):
        for name in ("api_key", "apiKey", "API-KEY", "access_key", "privateKey",
                     "CLIENT_SECRET", "session_key"):
            found = safety.secrets_in('%s = "wY7nQ2pLx4Rt"' % name, "f.txt")
            self.assertTrue(found, "%s was let through" % name)


class TestItDoesNotCryWolf(unittest.TestCase):
    """A check with false alarms is a check an author switches off."""

    def test_the_published_documents_hold_no_secret(self):
        folder = os.path.join(ROOT, "docs")
        names = sorted(name for name in os.listdir(folder) if name.endswith(".html"))
        self.assertTrue(names, "no published documents to check")
        for name in names:
            with open(os.path.join(folder, name), encoding="utf-8") as handle:
                found = safety.secrets_in(handle.read(), name)
            self.assertEqual([one.message for one in found], [])

    def test_this_toolchain_holds_no_secret(self):
        folder = os.path.join(ROOT, "z2s")
        for name in sorted(os.listdir(folder)):
            if not name.endswith((".py", ".js")):
                continue
            with open(os.path.join(folder, name), encoding="utf-8") as handle:
                found = safety.secrets_in(handle.read(), name)
            self.assertEqual([one.message for one in found], [])

    def test_these_tests_hold_no_secret(self):
        """The fixtures above are built, not written, and this is what proves it."""
        with open(os.path.abspath(__file__), encoding="utf-8") as handle:
            found = safety.secrets_in(handle.read(), "test_safety.py")
        self.assertEqual([one.message for one in found], [])


# -------------------------------------------------------------- the artefacts

class TestScanningWhatTheMethodLeavesBehind(Sandbox):

    def test_a_file_is_read_and_named(self):
        path = self.written("ledger.md", "- pushed with %s\n" % SEEDED["slack-token"])
        grouped = safety.scan([path])
        self.assertEqual(len(grouped[path]), 1)
        self.assertTrue(grouped[path][0].where.endswith(":1"))

    def test_a_commit_message_is_read_from_standard_input(self):
        grouped = safety.scan([safety.STDIN],
                              io.StringIO("Fix deploy\n\nkey=%s\n"
                                          % SEEDED["google-api-key"]))
        self.assertEqual(len(grouped[safety.STDIN]), 1)
        self.assertEqual(grouped[safety.STDIN][0].where, "commit:3")

    def test_a_file_that_cannot_be_read_is_reported_not_raised(self):
        missing = os.path.join(self.root, "absent.md")
        grouped = safety.scan([missing])
        self.assertEqual([one.code for one in grouped[missing]], ["unreadable"])

    def test_the_command_fails_on_a_leak_and_passes_without_one(self):
        clean = self.written("clean.md", "Read the token from GITHUB_TOKEN.\n")
        leaky = self.written("leaky.md", "token = %s\n" % SEEDED["github-token"])
        out = io.StringIO()
        self.assertEqual(safety.main([clean], out), 0)
        self.assertIn("OK", out.getvalue())
        out = io.StringIO()
        self.assertEqual(safety.main([leaky], out), 1)
        self.assertIn("1 secret found", out.getvalue())

    def test_the_command_with_nothing_to_do_says_so(self):
        out = io.StringIO()
        self.assertEqual(safety.main([], out), 2)
        self.assertIn("usage", out.getvalue())


class TestTheDocumentCheckerScansToo(Sandbox):
    """M6-07: the check a project already runs is the check that catches a leak."""

    def test_a_secret_in_a_document_fails_the_validator(self):
        path = self.written("Doc.html", document(
            "<p>Deploy with %s</p>" % SEEDED["github-token"]))
        grouped = validate.validate_set([path])
        self.assertIn("secret-literal", [one.code for one in grouped[path]])
        self.assertEqual(validate.exit_code(grouped), 1)

    def test_a_clean_document_still_passes(self):
        path = self.written("Doc.html", document("<p>Deploy with GITHUB_TOKEN.</p>"))
        grouped = validate.validate_set([path])
        self.assertEqual([one.message for one in grouped[path]], [])

    def test_a_file_with_no_specification_is_still_scanned(self):
        """A leak is a leak whether or not the schema ever sees the file."""
        path = self.written("notes.html", "<p>%s</p>" % SEEDED["aws-access-key"])
        grouped = validate.validate_set([path])
        codes = [one.code for one in grouped[path]]
        self.assertIn("secret-literal", codes)
        self.assertIn("unreadable", codes)


# -------------------------------------------------------- the banned operations

class TestTheListOfBannedOperations(unittest.TestCase):

    def test_it_names_every_operation_the_requirement_names(self):
        """NFR-SEC-04 names four; the published list contains all four."""
        self.assertEqual(sorted(one.id for one in safety.PROHIBITED),
                         ["delete-outside-area", "delete-unmerged-branch",
                          "force-push", "rewrite-history"])

    def test_every_operation_says_what_it_is_and_why(self):
        for operation in safety.PROHIBITED:
            self.assertTrue(operation.title.strip(), operation.id)
            self.assertTrue(operation.why.strip(), operation.id)
            self.assertTrue(callable(operation.matches), operation.id)


class TestJudgingACommand(unittest.TestCase):

    def caught(self, command, identifier, area=None):
        self.assertIn(identifier,
                      [one.id for one in safety.prohibited(command, area)],
                      "%r was allowed" % command)

    def allowed(self, command, area=None):
        self.assertEqual([one.id for one in safety.prohibited(command, area)], [],
                         "%r was refused" % command)

    def test_force_pushing_in_any_of_its_spellings(self):
        for command in ("git push --force origin main",
                        "git push -f origin main",
                        "git push --force-with-lease origin main",
                        "git push origin +main:main"):
            self.caught(command, "force-push")

    def test_rewriting_history(self):
        for command in ("git rebase -i main",
                        "git commit --amend --no-edit",
                        "git filter-branch --tree-filter true HEAD",
                        "git filter-repo --path src",
                        "git push --mirror backup"):
            self.caught(command, "rewrite-history")

    def test_deleting_a_branch_that_may_hold_unmerged_work(self):
        for command in ("git branch -D feature/x",
                        "git branch --delete --force feature/x",
                        "git push origin --delete feature/x",
                        "git push origin :feature/x"):
            self.caught(command, "delete-unmerged-branch")

    def test_deleting_outside_the_area_the_run_owns(self):
        for command in ("rm -rf /etc/hosts",
                        "rm -rf ../sibling",
                        "rm -rf ~/Library",
                        "cd /tmp/area && rm -rf /tmp/elsewhere"):
            self.caught(command, "delete-outside-area", "/tmp/area")

    def test_deleting_inside_the_area_is_ordinary_work(self):
        self.allowed("rm -rf build/tmp", "/tmp/area")
        self.allowed("rm -rf /tmp/area/build", "/tmp/area")

    def test_an_absolute_path_with_no_area_named_is_outside(self):
        """A run that has not said where it works has not earned the doubt."""
        self.caught("rm -rf /tmp/anywhere", "delete-outside-area")

    def test_the_safe_form_of_each_command_is_left_alone(self):
        for command in ("git push origin main",
                        "git push -u origin HEAD",
                        "git branch -d feature/x",
                        "git branch --list",
                        "git log --format=%H",
                        "rm -rf node_modules"):
            self.allowed(command)

    def test_a_word_that_merely_starts_the_same_is_not_a_command(self):
        self.allowed("git rebase-notes.md")
        self.allowed("git filter-branch-helper.sh")
        self.allowed("git filter-repository-notes.md")
        self.allowed("cat push--force.txt")
        self.allowed("echo 'never force-push'")

    def test_nothing_at_all_is_not_prohibited(self):
        self.allowed("")
        self.assertEqual(safety.prohibited(None), [])

    def test_a_refusal_says_why(self):
        said = safety.refusal("git push --force origin main")
        self.assertEqual(len(said), 1)
        self.assertIn("Force-push", said[0])
        self.assertIn("prohibited unattended", said[0])


class TestTheJudgeReadsTheList(unittest.TestCase):
    """M6-P2-T2-C2: the execution layer reads the list rather than restating it."""

    def test_an_operation_added_to_the_list_is_caught_immediately(self):
        added = safety.Operation("no-shutdown", "Shut the machine down",
                                 "Nothing else the run was asked to do will happen.",
                                 safety._any(r"\bshutdown(?![\w-])"))
        original = safety.PROHIBITED
        safety.PROHIBITED = original + (added,)
        try:
            self.assertEqual([one.id for one in safety.prohibited("sudo shutdown -h now")],
                             ["no-shutdown"])
        finally:
            safety.PROHIBITED = original
        self.assertEqual(safety.prohibited("sudo shutdown -h now"), [])

    def test_no_other_module_restates_the_rules(self):
        """One definition. A second copy is what NFR-SEC-04 is trying to prevent."""
        folder = os.path.join(ROOT, "z2s")
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".py") or name == "safety.py":
                continue
            with open(os.path.join(folder, name), encoding="utf-8") as handle:
                text = handle.read()
            for wording in ("--force", "filter-branch", "branch -D"):
                self.assertNotIn(wording, text,
                                 "%s restates a prohibited operation" % name)


class TestNothingHereReachesOut(unittest.TestCase):

    def test_it_reads_no_clock_and_no_network(self):
        with open(os.path.join(ROOT, "z2s", "safety.py"), encoding="utf-8") as handle:
            text = handle.read()
        for name in ("import socket", "import urllib", "import requests",
                     "import datetime", "import time", "import subprocess"):
            self.assertNotIn(name, text)


if __name__ == "__main__":       # pragma: no cover
    unittest.main()
