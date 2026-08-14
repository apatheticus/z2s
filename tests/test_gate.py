# -*- coding: utf-8 -*-
"""The decision gate: what it must refuse, what it must ask, what it must record.

Three claims are load-bearing here and each is checked against the thing that
would actually break rather than against a description of it:

  · nothing reaches the filesystem while a fork is open (FR-DOC-02, US-DOC-02-S01)
  · every question offers exactly one recommended default (FR-DOC-02)
  · a decision survives a lost conversation, because it is on disk (FR-DOC-03)

Traces: FR-DOC-02, FR-DOC-03, FR-DOC-07, FR-EXE-08, NFR-EXE-08, ADR-10,
US-DOC-01, US-DOC-02.
"""

import inspect
import os
import re
import shutil
import tempfile
import unittest

from z2s import gate, paths


def forks():
    """Two forks with different shapes: one plain, one bound to a source key."""
    return (
        gate.fork("audience", "Who is this document written for?",
                  [gate.option("owner", "The product owner", "Plain language.", recommended=True),
                   gate.option("engineer", "An engineer", "Assumes the stack.")]),
        gate.fork("scope", "How much of the release does this cover?",
                  [gate.option("release", "The whole release", "One document.", recommended=True),
                   gate.option("slice", "One slice", "Several documents.")]),
    )


class Sandbox(unittest.TestCase):
    """A project root that starts genuinely empty."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-gate-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def contents(self):
        return sorted(os.listdir(self.root))

    def ledger(self):
        return paths.resolve(self.root, paths.LEDGER_DIR, "vision.md")


class TestAForkIsAQuestionWithADefault(unittest.TestCase):

    def test_exactly_one_option_is_recommended(self):
        one = gate.fork("a", "Which one?",
                        [gate.option("x", "X", recommended=True), gate.option("y", "Y")])
        self.assertEqual(one.recommended.id, "x")

    def test_no_recommended_option_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            gate.fork("a", "Which one?", [gate.option("x", "X"), gate.option("y", "Y")])
        self.assertIn("recommended", str(caught.exception))

    def test_two_recommended_options_are_refused(self):
        with self.assertRaises(ValueError) as caught:
            gate.fork("a", "Which one?",
                      [gate.option("x", "X", recommended=True),
                       gate.option("y", "Y", recommended=True)])
        self.assertIn("exactly one", str(caught.exception))

    def test_a_single_option_is_not_a_fork(self):
        with self.assertRaises(ValueError):
            gate.fork("a", "Which one?", [gate.option("x", "X", recommended=True)])

    def test_a_statement_is_not_a_question(self):
        with self.assertRaises(ValueError) as caught:
            gate.fork("a", "Confirm the audience is the owner",
                      [gate.option("x", "X", recommended=True), gate.option("y", "Y")])
        self.assertIn("question", str(caught.exception))

    def test_every_declared_fork_carries_one_recommended_default(self):
        for one in forks():
            self.assertEqual(sum(1 for o in one.options if o.recommended), 1, one.id)


class TestNothingIsWrittenWhileAForkIsOpen(Sandbox):
    """M3-P1-T1-C1. The criterion is about the filesystem, so it is asked of the
    filesystem — not of a flag the gate sets about itself."""

    def test_the_root_stays_empty_until_every_fork_is_closed(self):
        run = gate.Gate("vision", forks())

        self.assertEqual(self.contents(), [])
        with self.assertRaises(gate.GateNotClosed):
            run.record(self.root)
        self.assertEqual(self.contents(), [])

        run.answer("audience", "owner", "The owner reads it first.")
        with self.assertRaises(gate.GateNotClosed):
            run.record(self.root)
        self.assertEqual(self.contents(), [])

        run.answer("scope", "release", "One release, one document.")
        run.record(self.root)
        self.assertEqual(self.contents(), [paths.ROOT])
        self.assertTrue(os.path.isfile(self.ledger()))

    def test_the_guard_is_available_to_a_caller_that_writes(self):
        run = gate.Gate("vision", forks())
        with self.assertRaises(gate.GateNotClosed) as caught:
            run.require_closed()
        self.assertIn("audience", str(caught.exception))
        self.assertIn("scope", str(caught.exception))

    def test_the_run_reports_which_forks_it_identified(self):
        run = gate.Gate("vision", forks())
        self.assertEqual([f.id for f in run.open_forks], ["audience", "scope"])


class TestOneQuestionAtATime(unittest.TestCase):

    def test_the_gate_offers_a_single_question(self):
        run = gate.Gate("vision", forks())
        self.assertEqual(run.question().id, "audience")

    def test_the_next_question_arrives_only_after_the_last_is_answered(self):
        run = gate.Gate("vision", forks())
        self.assertEqual(run.question().id, "audience")
        self.assertEqual(run.question().id, "audience")
        run.answer("audience", "owner", "The owner reads it first.")
        self.assertEqual(run.question().id, "scope")

    def test_there_is_no_question_once_the_gate_is_closed(self):
        run = gate.Gate("vision", forks())
        run.answer("audience", "owner", "why")
        run.answer("scope", "release", "why")
        self.assertIsNone(run.question())
        self.assertTrue(run.closed)

    def test_an_unknown_fork_cannot_be_answered(self):
        run = gate.Gate("vision", forks())
        with self.assertRaises(KeyError):
            run.answer("invented", "owner", "why")

    def test_a_choice_without_a_rationale_is_refused(self):
        run = gate.Gate("vision", forks())
        with self.assertRaises(ValueError) as caught:
            run.answer("audience", "owner", "   ")
        self.assertIn("rationale", str(caught.exception))

    def test_an_answer_outside_the_offered_options_is_kept_verbatim(self):
        run = gate.Gate("vision", forks())
        run.answer("audience", "Both, in two versions", "The owner signs it, the engineer builds from it.")
        self.assertEqual(run.decisions[0].choice, "Both, in two versions")

    def test_an_offered_option_is_recorded_by_its_label_not_its_key(self):
        run = gate.Gate("vision", forks())
        run.answer("audience", "owner", "why")
        self.assertEqual(run.decisions[0].choice, "The product owner")


class TestARichSourceSkipsTheInterview(unittest.TestCase):
    """M3-P1-T3. FR-DOC-07: sufficient material is authored from, not interviewed
    about. Sufficiency is a checklist against the declared forks."""

    def test_a_complete_source_produces_no_questions(self):
        run = gate.Gate("vision", forks(),
                        source={"audience": "The product owner", "scope": "The whole release"})
        self.assertIsNone(run.question())
        self.assertTrue(run.closed)
        self.assertTrue(run.skipped)

    def test_the_skip_and_its_reason_are_reported(self):
        run = gate.Gate("vision", forks(),
                        source={"audience": "The product owner", "scope": "The whole release"})
        self.assertIn("audience", run.skip_reason)
        self.assertIn("scope", run.skip_reason)

    def test_a_partial_source_still_asks_about_what_it_omits(self):
        run = gate.Gate("vision", forks(), source={"audience": "The product owner"})
        self.assertFalse(run.skipped)
        self.assertEqual(run.question().id, "scope")

    def test_a_thin_source_asks_about_everything(self):
        run = gate.Gate("vision", forks(), source={"title": "A tool for shipping"})
        self.assertEqual([f.id for f in run.open_forks], ["audience", "scope"])
        self.assertIsNone(run.skip_reason)

    def test_a_blank_value_does_not_answer_a_fork(self):
        run = gate.Gate("vision", forks(), source={"audience": "  ", "scope": []})
        self.assertEqual([f.id for f in run.open_forks], ["audience", "scope"])

    def test_what_the_source_answered_is_recorded_as_a_decision_with_its_origin(self):
        run = gate.Gate("vision", forks(),
                        source={"audience": "The product owner", "scope": "The whole release"})
        first = run.decisions[0]
        self.assertEqual(first.choice, "The product owner")
        self.assertIn("source", first.rationale)


class TestTheLockedDecisionsTable(Sandbox):
    """M3-P1-T2-C1. The table must exist in the document and in the ledger."""

    def closed_gate(self):
        run = gate.Gate("vision", forks())
        run.answer("audience", "owner", "The owner reads it first.")
        run.answer("scope", "release", "One release, one document.")
        return run

    def test_the_table_states_decision_choice_and_rationale(self):
        text = self.closed_gate().table()
        self.assertIn("| # | Decision | Choice | Rationale |", text)
        self.assertIn("The product owner", text)
        self.assertIn("The owner reads it first.", text)

    def test_the_table_is_not_available_while_a_fork_is_open(self):
        with self.assertRaises(gate.GateNotClosed):
            gate.Gate("vision", forks()).table()

    def test_the_ledger_carries_the_table(self):
        self.closed_gate().record(self.root)
        with open(self.ledger(), encoding="utf-8") as handle:
            written = handle.read()
        self.assertIn(gate.TABLE_HEADING, written)
        self.assertIn("| audience |", written)

    def test_the_document_carries_the_table_as_a_section(self):
        section = self.closed_gate().section()
        self.assertEqual(section["type"], "table")
        self.assertEqual(section["columns"], ["#", "Decision", "Choice", "Rationale"])
        self.assertEqual([row[0] for row in section["rows"]], ["audience", "scope"])

    def test_the_section_is_absent_rather_than_empty_when_nothing_was_decided(self):
        """NFR-DAT-06 — an empty section is omitted, never emitted empty."""
        self.assertIsNone(gate.Gate("vision", ()).section())

    def test_a_pipe_in_an_answer_cannot_break_the_table(self):
        run = gate.Gate("vision", forks())
        run.answer("audience", "Owner | engineer", "Both | at once.")
        run.answer("scope", "release", "why")
        row = [line for line in run.table().splitlines() if line.startswith("| audience")][0]
        # The pipes the reader typed are escaped, not dropped, so the row still
        # has exactly the four cells the header promises.
        self.assertEqual(len(re.findall(r"(?<!\\)\|", row)) - 1, len(gate.COLUMNS), row)
        self.assertIn("Owner \\| engineer", row)

    def test_recording_twice_leaves_one_table(self):
        run = self.closed_gate()
        run.record(self.root)
        run.record(self.root)
        with open(self.ledger(), encoding="utf-8") as handle:
            written = handle.read()
        self.assertEqual(written.count(gate.TABLE_HEADING), 1)

    def test_recording_preserves_what_the_ledger_already_said(self):
        os.makedirs(os.path.dirname(self.ledger()))
        with open(self.ledger(), "w", encoding="utf-8") as handle:
            handle.write("# Ledger: vision\n\n## Log\n- started\n")
        self.closed_gate().record(self.root)
        with open(self.ledger(), encoding="utf-8") as handle:
            written = handle.read()
        self.assertIn("- started", written)
        self.assertIn(gate.TABLE_HEADING, written)


class TestALockedRowIsNotReAsked(Sandbox):
    """M3-P1-T2-C2 and US-DOC-02-S03. The point of writing decisions down is that
    they outlive the conversation, so the reload path is the real test."""

    def test_a_decision_read_back_from_the_ledger_is_not_asked_again(self):
        first = gate.Gate("vision", forks())
        first.answer("audience", "owner", "The owner reads it first.")
        first.answer("scope", "release", "One release, one document.")
        first.record(self.root)

        resumed = gate.Gate("vision", forks(), decisions=gate.load(self.root, "vision"))
        self.assertTrue(resumed.closed)
        self.assertIsNone(resumed.question())
        self.assertEqual(resumed.decisions[0].choice, "The product owner")
        self.assertEqual(resumed.decisions[0].rationale, "The owner reads it first.")

    def test_a_partially_locked_gate_asks_only_what_is_still_open(self):
        first = gate.Gate("vision", forks())
        first.answer("audience", "owner", "why")
        resumed = gate.Gate("vision", forks(), decisions=first.decisions)
        self.assertEqual(resumed.question().id, "scope")

    def test_repeating_a_locked_answer_is_accepted_in_silence(self):
        run = gate.Gate("vision", forks())
        run.answer("audience", "owner", "why")
        run.answer("audience", "owner", "why")
        self.assertEqual(len(run.decisions), 1)

    def test_contradicting_a_locked_row_is_surfaced_as_a_conflict(self):
        run = gate.Gate("vision", forks())
        run.answer("audience", "owner", "why")
        with self.assertRaises(gate.LockedForkConflict) as caught:
            run.answer("audience", "engineer", "changed my mind")
        message = str(caught.exception)
        self.assertIn("audience", message)
        self.assertIn("The product owner", message)
        self.assertIn("An engineer", message)

    def test_a_conflict_leaves_the_recorded_choice_standing(self):
        run = gate.Gate("vision", forks())
        run.answer("audience", "owner", "why")
        try:
            run.answer("audience", "engineer", "changed my mind")
        except gate.LockedForkConflict:
            pass
        self.assertEqual(run.decisions[0].choice, "The product owner")

    def test_loading_from_a_project_with_no_ledger_yields_nothing(self):
        self.assertEqual(gate.load(self.root, "vision"), ())

    def test_the_table_survives_a_round_trip_intact(self):
        run = gate.Gate("vision", forks())
        run.answer("audience", "Owner | engineer", "Both | at once.")
        run.answer("scope", "release", "One release, one document.")
        recovered = gate.read(run.table())
        self.assertEqual([d.fork for d in recovered], ["audience", "scope"])
        self.assertEqual(recovered[0].choice, "Owner | engineer")
        self.assertEqual(recovered[0].rationale, "Both | at once.")


class TestTheGateNeverPrompts(unittest.TestCase):
    """NFR-EXE-08 and M3-01: the gate emits questions, it does not conduct the
    interview. A module that reads a terminal cannot run unattended."""

    def source(self):
        return inspect.getsource(gate)

    def test_nothing_reads_the_terminal(self):
        for forbidden in ("input(", "raw_input(", "stdin", "getpass"):
            self.assertNotIn(forbidden, self.source(), forbidden)

    def test_nothing_prints(self):
        self.assertFalse(re.search(r"^\s*print\(", self.source(), re.MULTILINE))

    def test_the_answer_path_takes_the_answer_as_an_argument(self):
        taken = list(inspect.signature(gate.Gate.answer).parameters)
        self.assertEqual(taken, ["self", "fork_id", "choice", "rationale"])


if __name__ == "__main__":
    unittest.main()
