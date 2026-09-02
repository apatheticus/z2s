# -*- coding: utf-8 -*-
"""The one command every document skill drives the toolchain through (M13-02).

The cycle has to be stateless, because an agent cannot hold a gate object
between turns, and it has to refuse before it writes, because a half-run that
left a file behind would make the refusal worse than useless. Both are checked
here against the real generator rather than a stand-in: the whole value of one
uniform command is that it behaves identically for all seven document steps, and
a fake would be uniform by construction and prove nothing.

Traces: FR-SKL-01, FR-SKL-02, FR-DOC-02, FR-DOC-03, FR-DOC-07, NFR-SKL-02,
US-SKL-01, US-SKL-02.
"""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import author, gate, paths, project, steps, intent

from tests.test_intent import brief


def tree(folder):
    found = {}
    for where, _, names in os.walk(folder):
        for name in sorted(names):
            path = os.path.join(where, name)
            with open(path, "rb") as handle:
                found[os.path.relpath(path, folder)] = handle.read()
    return found


class Project(unittest.TestCase):
    """A set-up project with no documents in it."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-author-")
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)
        project.initialise(self.folder)

    def write_brief(self, slug, payload):
        target = author.brief_path(self.folder, slug)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload))
        return target

    def invoke(self, *argv):
        out = io.StringIO()
        code = author.main(list(argv) + ["--root", self.folder], out)
        return code, out.getvalue()

    def interview(self, slug, rounds=8):
        """Drive the cycle to completion, taking every recommendation.

        This is exactly what the skill definition tells an agent to do, which is
        the point: the loop under test is the loop that ships.
        """
        for _ in range(rounds):
            code, said = self.invoke("run", slug)
            if code != author.ASKING:
                return code, said
            fork = [one.split(": ", 1)[1] for one in said.splitlines()
                    if one.startswith("fork: ")][0]
            choice = [one.strip().split(" — ")[0] for one in said.splitlines()
                      if "(recommended)" in one][0]
            self.invoke("answer", slug, fork, choice, "--why", "Chosen by the test.")
        self.fail("the gate never closed")


class TestTheCycle(Project):
    """The three-part shape, driven the way a skill drives it."""

    def test_an_open_fork_is_asked_rather_than_answered(self):
        self.write_brief("intent", brief())
        code, said = self.invoke("run", "intent")
        self.assertEqual(author.ASKING, code)
        self.assertIn("fork: scope", said)
        self.assertIn("(recommended)", said)

    def test_the_question_carries_every_option_with_its_meaning(self):
        """The operator is choosing between described outcomes, not
        identifiers."""
        self.write_brief("intent", brief())
        _, said = self.invoke("run", "intent")
        for one in intent.FORKS[0].options:
            self.assertIn(one.id, said)
            self.assertIn(one.label, said)
            self.assertIn(one.meaning, said)

    def test_an_answered_gate_writes_the_document(self):
        self.write_brief("intent", brief())
        code, said = self.interview("intent")
        self.assertEqual(author.WRITTEN, code)
        self.assertIn("Intent.html", said)
        self.assertTrue(steps.completed(self.folder, steps.step("intent")))

    def test_an_answer_survives_between_turns(self):
        """Each turn is a separate process. A cycle that forgot the previous
        round would ask the same question until the operator gave up."""
        self.write_brief("intent", brief())
        _, first = self.invoke("run", "intent")
        opening = [one for one in first.splitlines() if one.startswith("fork: ")][0]
        self.invoke("answer", "intent", "scope", "release", "--why", "Because.")
        _, second = self.invoke("run", "intent")
        self.assertNotIn(opening, second)

    def test_an_answer_needs_a_reason(self):
        """A choice without one is not a decision, and the ledger records both."""
        code, said = self.invoke("answer", "intent", "scope", "release")
        self.assertEqual(author.MISUSED, code)
        self.assertIn("--why", said)

    def test_a_recorded_answer_reaches_the_ledger_with_its_reason(self):
        self.write_brief("intent", brief())
        self.invoke("answer", "intent", "scope", "release",
                 "--why", "One release is all anybody has agreed to.")
        self.interview("intent")
        held = gate.load(self.folder, "intent")
        chosen = [one for one in held if one.fork == "scope"][0]
        self.assertIn("One release is all anybody has agreed to.", chosen.rationale)

    def test_a_brief_that_already_answers_a_fork_is_not_asked_about_it(self):
        """FR-DOC-07: the source is the source. A gate that re-asks what the
        operator already wrote is an interview nobody finishes."""
        self.write_brief("intent", brief(scope="the whole product"))
        _, said = self.invoke("run", "intent")
        self.assertNotIn("fork: scope", said)


class TestItRefusesBeforeItWrites(Project):
    """NFR-SKL-02: a refusal leaves the repository byte-for-byte untouched."""

    def test_a_missing_prerequisite_refuses_and_names_it(self):
        self.write_brief("fsd", {})
        code, said = self.invoke("run", "fsd")
        self.assertEqual(author.REFUSED, code)
        self.assertIn("PRD.html", said)

    def test_a_refused_run_changes_nothing(self):
        self.write_brief("fsd", {})
        before = tree(self.folder)
        self.invoke("run", "fsd")
        self.assertEqual(before, tree(self.folder))

    def test_the_prerequisite_is_checked_before_the_brief_is_even_wanted(self):
        """Otherwise the operator writes a brief for a step that could never
        have run, and finds out afterwards."""
        code, said = self.invoke("run", "fsd")
        self.assertEqual(author.REFUSED, code)
        self.assertIn("PRD.html", said)
        self.assertNotIn("no brief", said)

    def test_a_missing_brief_refuses_and_names_where_it_goes(self):
        code, said = self.invoke("run", "intent")
        self.assertEqual(author.REFUSED, code)
        self.assertIn(author.brief_path(self.folder, "intent"), said)
        self.assertIn("/zero:questions", said)

    def test_a_damaged_answer_store_is_treated_as_no_answers(self):
        """It is transient run state, and being asked again costs one round and
        loses nothing that was written."""
        self.write_brief("intent", brief())
        target = author.answers_path(self.folder, "intent")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("{ this is not json")
        code, said = self.invoke("run", "intent")
        self.assertEqual(author.ASKING, code)
        self.assertIn("fork:", said)

    def test_a_store_holding_well_formed_json_of_the_wrong_shape_is_ignored(self):
        """The one an unparseable file does not catch. A list or a bare string
        parses perfectly and then fails on the first lookup — as a crash rather
        than as a refusal, which is the worst of both."""
        self.write_brief("intent", brief())
        target = author.answers_path(self.folder, "intent")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        for wrong in ('["scope", "release"]', '"release"', "null", "42"):
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(wrong)
            code, said = self.invoke("run", "intent")
            self.assertEqual(author.ASKING, code, wrong)
            self.assertIn("fork:", said)

    def test_a_brief_of_the_wrong_shape_is_treated_as_no_brief(self):
        target = author.brief_path(self.folder, "intent")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write('["not", "a", "brief"]')
        code, said = self.invoke("run", "intent")
        self.assertEqual(author.REFUSED, code)
        self.assertIn("no brief", said)

    def test_a_locked_decision_is_applied_not_re_decided(self):
        """FR-DOC-03. An answer contradicting a locked one is a conflict to
        resolve, not a change to make."""
        self.write_brief("intent", brief())
        self.interview("intent")
        self.invoke("answer", "intent", "scope", "product", "--why", "Changed my mind.")
        code, said = self.invoke("run", "intent")
        self.assertEqual(author.REFUSED, code)
        self.assertIn("locked", said)


class TestTheCommandItself(Project):
    """Its exit status is the answer (FR-VAL-05)."""

    def test_an_operating_skill_has_nothing_to_author(self):
        code, said = self.invoke("run", "ship")
        self.assertEqual(author.MISUSED, code)
        self.assertIn("operating skill", said)

    def test_an_unknown_step_names_the_chain(self):
        code, said = self.invoke("run", "architecture")
        self.assertEqual(author.MISUSED, code)
        self.assertIn("intent", said)

    def test_no_arguments_explains_itself(self):
        code, said = self.invoke()
        self.assertEqual(author.MISUSED, code)
        self.assertIn("usage:", said)

    def test_every_document_step_is_drivable_by_this_one_command(self):
        """The whole benefit of M13-02: one shape for all seven. A step this
        command could not drive would need its own, and then there would be two."""
        for one in steps.DOCUMENTS:
            code, _ = self.invoke("run", one.module.SLUG)
            self.assertIn(code, (author.REFUSED, author.ASKING, author.WRITTEN),
                          one.name)


if __name__ == "__main__":
    unittest.main()
