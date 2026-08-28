# -*- coding: utf-8 -*-
"""The loop the prompts carry, and the promise that both doors say it (M14).

Two things hand work to somebody who was not in the room: a plan document an
operator copies a prompt out of, and the orchestrator handing a brief to a
worker. The rules below are about what each says and about the one thing that
matters more than either — that they say the same thing about the same unit.
"""

import inspect
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from z2s import execute, gauntlet, plan, safety, schema        # noqa: E402
from test_execute import Project                               # noqa: E402

#: One entry, complete enough to be briefed on.
ENTRY = {"id": "M1-P1-T1", "title": "A task",
         "text": "The first piece of work.",
         "autonomy": schema.AUTONOMOUS,
         "testLayers": ["unit"],
         "tdd": {"red": "A test fails.", "green": "Make it pass.",
                 "refactor": "Tidy it."},
         "criteria": [{"id": "M1-P1-T1-C1", "kind": "auto",
                       "text": "The behaviour holds.", "done": False},
                      {"id": "M1-P1-T1-C2", "kind": "human-review",
                       "text": "It reads well.", "done": False}],
         "traces": {"fr": ["FR-DOC-01"], "adr": ["ADR-01"],
                    "us": ["US-DOC-01"], "tg": ["TG-01"]}}


class Settled(object):
    """A locked decision, as the ledger hands one over."""

    question = "Which way?"
    choice = "That way."


DECISIONS = [("fsd", Settled())]
COMMANDS = ["unit python3 -m unittest"]


def made(level="task", entry=None, **extra):
    entry = ENTRY if entry is None else entry
    facts = {"unit": entry["id"], "title": entry["title"],
             "bar": gauntlet.criteria_lines(entry),
             "aiming": gauntlet.ceiling(entry),
             "entry": entry,
             "closing": gauntlet.unit_lines(entry)}
    facts.update(extra)
    return gauntlet.assemble(level, "M1.html", DECISIONS, COMMANDS, **facts)


def blocks(text):
    """A prompt, split back into the titled blocks it was built from."""
    found = {}
    for part in text.split("\n\n"):
        lines = part.split("\n")
        if len(lines) > 1 and all(one.startswith("  - ") for one in lines[1:]):
            found[lines[0]] = part
    return found


# ------------------------------------------------------------ what it carries

class TestEveryLevelCarriesTheWholeContract(unittest.TestCase):

    def test_each_of_the_four_levels_states_every_required_part(self):
        for level in ("task", "phase", "milestone", "plan"):
            self.assertEqual([], gauntlet.check(made(level), level),
                             "%s is missing parts" % level)

    def test_a_prompt_that_lost_a_block_is_reported_as_incomplete(self):
        text = made("task").replace("The higher target", "Some other heading")
        self.assertIn("The higher target", gauntlet.check(text, "task"))

    def test_what_the_unit_waits_on_is_stated_before_the_contract(self):
        text = made("task", waits=["M1-P1-T0"])
        self.assertLess(text.index("Prerequisites"), text.index("Plan document"))
        self.assertIn("M1-P1-T0", text)

    def test_a_dependency_this_run_knows_is_short_is_marked_as_such(self):
        text = made("task", waits=["M1-P1-T0"], unresolved=["M1-P1-T0"])
        self.assertIn("M1-P1-T0 — NOT YET PASSING", text)

    def test_waiting_on_nothing_is_stated_rather_than_left_out(self):
        self.assertIn("waits on nothing", made("task"))

    def test_the_bar_is_the_units_own_criteria_with_their_identifiers(self):
        text = made("task")
        self.assertIn("M1-P1-T1-C1 (auto): The behaviour holds.", text)
        self.assertIn("M1-P1-T1-C2 (human-review): It reads well.", text)

    def test_a_unit_with_no_criteria_says_so_rather_than_showing_an_empty_bar(self):
        self.assertIn("no acceptance criteria", made("task", bar=[]))


# ------------------------------------------------------------ the higher target

class TestTheHigherTarget(unittest.TestCase):
    """M14-02. The ceiling is what the unit already traces to, and nothing else.

    The one failure worth guarding against here is an invented one: a ceiling
    filled in to avoid an empty block is an invented standard, and an invented
    standard graded as a real one is the whole failure this method exists to
    prevent.
    """

    def test_it_names_the_requirements_and_stories_the_unit_traces_to(self):
        text = made("task")
        self.assertIn("FR-DOC-01", text)
        self.assertIn("US-DOC-01", text)
        self.assertIn("TG-01", text)

    def test_a_decision_is_not_a_ceiling(self):
        # An ADR is a decision already applied, not a target to reach for.
        self.assertNotIn("ADR-01", gauntlet.ceiling(ENTRY))

    def test_it_carries_the_title_when_the_plan_knows_one(self):
        found = gauntlet.ceiling(ENTRY, {"FR-DOC-01": "Every document is generated"})
        self.assertIn("FR-DOC-01 — Every document is generated", found)

    def test_a_unit_that_traces_to_nothing_is_told_not_to_invent_one(self):
        found = gauntlet.ceiling({"id": "M1-P1-T9", "title": "Alone"})
        self.assertEqual([gauntlet.NO_CEILING], found)
        self.assertIn("Do not invent one", found[0])

    def test_the_floor_is_named_as_the_floor_so_a_ceiling_loss_cannot_fail_it(self):
        self.assertIn("Losing to them never fails the unit",
                      "\n".join(gauntlet.ceiling(ENTRY)))

    def test_a_phase_aims_at_what_the_tasks_beneath_it_aim_at(self):
        merged = gauntlet.merged_traces([
            {"traces": {"fr": ["FR-DOC-01", "FR-DOC-02"]}},
            {"traces": {"fr": ["FR-DOC-02"], "us": ["US-DOC-01"]}}])
        self.assertEqual({"fr": ["FR-DOC-01", "FR-DOC-02"],
                          "us": ["US-DOC-01"]}, dict(merged))

    def test_a_project_may_name_one_more_target_of_its_own(self):
        found = gauntlet.ceiling(ENTRY, None, "https://example.test/the-bar")
        self.assertIn("https://example.test/the-bar", found)


# ------------------------------------------------------------------ the critic

class TestTheCritic(unittest.TestCase):

    def test_the_injection_guard_is_the_last_thing_the_critic_is_told(self):
        # Verbatim, and last, so it survives a brief that gets truncated.
        self.assertEqual(gauntlet.GUARD, gauntlet.JUDGE_CONTRACT[-1])
        found = blocks(made("task"))["The critic"]
        self.assertTrue(found.rstrip().endswith(gauntlet.GUARD),
                        "the guard is not the final paragraph")

    def test_the_critic_is_told_that_being_unable_to_inspect_is_a_failure(self):
        self.assertIn("could not inspect", "\n".join(gauntlet.JUDGE_CONTRACT))

    def test_the_critic_never_receives_what_the_builder_said_about_its_work(self):
        self.assertIn("nothing the builder wrote about its own work",
                      "\n".join(gauntlet.LOOP))

    def test_a_fresh_critic_is_required_on_every_round(self):
        self.assertIn("fresh critic every round", "\n".join(gauntlet.LOOP))


# ------------------------------------------------------------------- the loop

class TestTheLoop(unittest.TestCase):

    def test_the_lead_is_told_not_to_implement_anything_itself(self):
        self.assertIn("Do not implement any of this yourself", made("task"))

    def test_a_task_is_split_by_whoever_runs_it_and_not_by_the_prompt(self):
        text = made("task")
        self.assertIn("The split is yours to make", text)
        self.assertIn("decide that split yourself", text)

    def test_a_loss_returns_exactly_one_gap_rather_than_a_list(self):
        self.assertIn("returns exactly ONE gap", made("task"))

    def test_no_prompt_states_a_number_of_rounds(self):
        """M14-11. A round count turns the loop back into "try it a few times".

        The whole point of the pattern is that the bar decides when it is done,
        not a countdown. The runner bounds its own retries from outside, which
        is a property of the run rather than a sentence in the brief.
        """
        counted = re.compile(
            r"\b(?:two|three|four|five|\d+)\s+(?:more\s+)?"
            r"(?:rounds?|passes|iterations?|attempts?|retries|tries)\b", re.I)
        for level in ("task", "phase", "milestone", "plan"):
            text = made(level)
            self.assertIsNone(counted.search(text),
                              "%s states a round count" % level)

    def test_the_smoothing_pass_is_asked_for_at_phase_level_and_above(self):
        """M14-10. Separately-built pieces come back collectively incoherent."""
        self.assertNotIn("smoothing", made("task").lower())
        for level in ("phase", "milestone", "plan"):
            self.assertIn("ONE smoothing pass over the assembled whole", made(level),
                          "%s does not ask for a smoothing pass" % level)

    def test_a_milestone_is_told_to_close_with_a_retrospective(self):
        self.assertIn("retrospective", made("milestone"))

    def test_the_whole_plan_is_told_the_coverage_gate_must_pass(self):
        self.assertIn("coverage gate", made("plan"))


# ------------------------------------------------------------------- the stops

class TestTheStopsOutrankTheLoop(unittest.TestCase):

    def test_every_prohibited_operation_is_named_from_the_one_place(self):
        """M6-08. A caller that writes its own list has made a second rulebook.

        Appended to at run time, so a rule added to `safety.PROHIBITED` reaches
        every prompt with no edit here.
        """
        text = made("task")
        for one in safety.PROHIBITED:
            self.assertIn(one.title, text)

    def test_a_human_review_criterion_is_not_the_workers_to_decide(self):
        self.assertIn("not yours to decide", made("task"))

    def test_a_unit_that_needs_a_person_is_told_where_it_stops(self):
        entry = dict(ENTRY, autonomy=schema.HUMAN_GATE)
        self.assertIn(schema.HUMAN_GATE, made("task", entry=entry))

    def test_an_autonomous_unit_is_not_told_it_stops_at_a_gate(self):
        self.assertNotIn("stops at the gate", made("task"))

    def test_the_loop_can_never_approve_a_deploy_or_a_send(self):
        self.assertIn("can never approve a sign-off, a deploy, a send or a spend",
                      made("task"))


# -------------------------------------------------------- what a unit is told

class TestWhatAUnitIsTold(unittest.TestCase):

    def test_the_three_parts_of_the_failing_test_first_rule_are_all_stated(self):
        text = made("task")
        for part in ("Red:", "Green:", "Refactor:"):
            self.assertIn(part, text)

    def test_the_criteria_are_stated_once_and_not_again_under_this_unit(self):
        """A unit that states its bar twice invites grading against the nearer copy."""
        found = blocks(made("task"))
        self.assertIn("M1-P1-T1-C1", found["The bar"])
        self.assertNotIn("M1-P1-T1-C1", found["This unit"])

    def test_a_unit_declaring_no_write_set_is_told_it_runs_alone(self):
        self.assertIn("no write set", made("task"))

    def test_a_unit_with_a_write_set_is_told_which_files_it_may_write(self):
        entry = dict(ENTRY, writes=["z2s/thing.py"])
        text = made("task", entry=entry)
        self.assertIn("z2s/thing.py", text)
        self.assertIn("the complete set this unit is expected to touch", text,
                      "read as a bare permission the field invites a short list, "
                      "and the orchestrator schedules concurrent units from it")
        self.assertIn("exception for the plan to record", text,
                      "a unit needing a path outside its list has somewhere to "
                      "go that is not a decision recorded after the fact")

    def test_a_carried_gap_is_the_only_thing_a_retry_is_asked_to_close(self):
        found = gauntlet.unit_lines(ENTRY, "The report named no command.")
        self.assertIn("Close this and only this: The report named no command.",
                      "\n".join(found))


# --------------------------------------- the contract and the checker are one

class TestTheReportContractIsTheReportChecker(unittest.TestCase):
    """The defect this class exists for, stated plainly.

    `REPORT_CONTRACT` was five lines of prose naming no key at all, while
    `execute.check_report` and `execute.settle` read six keys by name — two of
    which (`red` and `changes`) appeared in no brief anywhere. A worker could
    satisfy every stated word of the contract and be rejected every single time,
    and the only way through was to read the checker's source.

    So the test is bidirectional, and it has to be: a one-way check passes a
    codebase that documents a key nobody reads, and a codebase that reads a key
    nobody documents is exactly what shipped.
    """

    #: The functions that read a BUILDER's report. `verdict` is left out
    #: deliberately — it reads a judge's report, which is a different shape with
    #: a contract of its own.
    READERS = ("check_report", "settle", "decisions")

    def read_keys(self):
        """Every top-level key those functions take out of a report.

        Matched on `report.get("x")`, which is the only way a report is opened
        here, so a nested `one.get("why")` inside a decision is not mistaken for
        a key of the report itself.
        """
        found = set()
        for name in self.READERS:
            body = inspect.getsource(getattr(execute, name))
            found.update(re.findall(r'\breport\.get\("([a-z_]+)"\)', body))
        return found

    def test_every_key_the_machine_reads_is_named_in_the_contract(self):
        for key in sorted(self.read_keys()):
            self.assertIn(key, gauntlet.REPORT_KEYS,
                          "%s is read out of a report and named in no brief; a "
                          "worker cannot supply what it was never asked for" % key)

    def test_every_key_the_contract_names_is_actually_read(self):
        read = self.read_keys()
        for key in gauntlet.REPORT_KEYS:
            self.assertIn(key, read,
                          "the contract asks for %s and nothing reads it" % key)

    def test_the_reader_scan_finds_something_at_all(self):
        """Without this the two tests above pass an empty set against itself."""
        self.assertGreaterEqual(len(self.read_keys()), 5)

    def test_the_rendered_contract_states_every_key_and_its_shape(self):
        text = "\n".join(gauntlet.REPORT_CONTRACT)
        for key, example, why in gauntlet.REPORT_SHAPE:
            self.assertIn(key, text)
            self.assertIn(example, text, "%s states no shape" % key)
            self.assertIn(why, text)

    def test_the_contract_reaches_a_real_brief(self):
        """Rendered, not merely defined. A contract in a constant nobody carries
        is the same as no contract."""
        text = made()
        for key, example, _ in gauntlet.REPORT_SHAPE:
            self.assertIn("%s: %s" % (key, example), text)

    def test_a_brief_says_when_the_report_is_due_and_not_only_what_it_holds(self):
        """The shape was stated and the moment was not, so "when done" was left
        to the worker's own judgement — and a worker that has just written a
        clean summary of its progress reads as done to itself. It stops, the
        session tears its unfinished commands down, and the report it meant to
        write next never happens."""
        text = made()
        self.assertIn("Your turn is not over until that file exists", text)
        self.assertIn("Never end a message describing what you are about to do "
                      "next", text)

    def test_the_recovery_brief_asks_for_the_report_and_nothing_else(self):
        """It is handed to a worker that has already built. A turn that starts
        by reading the original brief starts by building a second time."""
        text = gauntlet.RECOVERY % {"unit": "<unit>", "brief": "<brief>",
                                    "report": "<report>"}
        for phrase in ("start no new work", "Run no further checks",
                       "Change nothing else", "<brief>", "<report>", "<unit>"):
            self.assertIn(phrase, text)

    def test_no_example_value_looks_like_a_real_plan_identifier(self):
        """Every brief in a project carries this block. An example shaped like a
        real unit would appear in every unit's brief, and a worker copying it
        back would be answering for somebody else's work."""
        for key, example, _ in gauntlet.REPORT_SHAPE:
            self.assertIsNone(re.search(r"M\d+-P\d+-T\d+", example), key)


# ------------------------------------------------- the two doors say one thing

class TestTheDocumentAndTheRunnerAgree(Project):
    """M14-01, and the drift path this closes.

    Before this, the prompt written into a plan document went through
    `context.consult` and the brief the orchestrator built did not, so the same
    unit could be described in two different vocabularies by the same project.
    The blocks below are the ones that describe the unit rather than the run,
    and they have to be the same bytes.
    """

    #: "Status contract" is deliberately NOT here. It is the one block that
    #: describes the RUN rather than the unit — who records the status — and the
    #: honest answer differs by reader. `test_only_one_of_the_two_readers_is_told
    #: _to_set_the_status` is what holds that difference where it belongs.
    SHARED = ("Prerequisites", "The bar", "The higher target", "How to run it",
              "The critic", "Stops that outrank this loop", "This unit",
              "Report contract", "Locked decisions")

    def setUp(self):
        Project.setUp(self)
        self.plan()
        self.config = self.configure()

    def both(self, unit_id="M1-P1-T1"):
        found = execute.units(self.root)
        document = gauntlet.carried(self.root)[unit_id]
        running = execute.brief(self.root, self.config, found[unit_id],
                                found=found, titles=execute.catalog(self.root))
        return blocks(document), blocks(running)

    def test_every_block_describing_the_unit_is_identical_in_both(self):
        document, running = self.both()
        for title in self.SHARED:
            self.assertIn(title, document, "the document prompt lost %s" % title)
            self.assertIn(title, running, "the runner brief lost %s" % title)
            self.assertEqual(document[title], running[title],
                             "%s differs between the document and the run" % title)

    def test_only_one_of_the_two_readers_is_told_to_set_the_status(self):
        """A pasted prompt has no run behind it; a dispatched brief does.

        Telling a dispatched worker to "set it with the status command" was an
        instruction to grade its own work, and workers followed it. A unit that
        recorded itself as verified could not then be demoted, so it left the
        ready set and was never attempted again.
        """
        document, running = self.both()
        self.assertIn(gauntlet.OWN_STATUS, document["Status contract"])
        self.assertNotIn(gauntlet.OWN_STATUS, running["Status contract"])
        self.assertIn(gauntlet.RUN_STATUS, running["Status contract"])
        self.assertNotIn(gauntlet.RUN_STATUS, document["Status contract"])
        # The vocabulary itself is not a matter of who is reading.
        for line in gauntlet.statuses():
            self.assertIn(line, document["Status contract"])
            self.assertIn(line, running["Status contract"])

    def test_both_open_with_the_same_sentence_about_the_same_unit(self):
        document = gauntlet.carried(self.root)["M1-P1-T1"]
        found = execute.units(self.root)
        running = execute.brief(self.root, self.config, found["M1-P1-T1"])
        self.assertEqual(document.split("\n")[0], running.split("\n")[0])
        self.assertEqual(document.split("\n")[2], running.split("\n")[2])

    def test_the_run_adds_what_only_a_run_knows_and_nothing_else(self):
        document, running = self.both()
        extra = set(running) - set(document)
        self.assertEqual({"Prior retrospectives", "Conventions",
                          "How this unit is judged"}, extra)

    def test_a_briefed_worker_is_told_it_is_not_appointing_its_own_judge(self):
        _, running = self.both()
        self.assertIn("never shown your report",
                      running["How this unit is judged"])

    def test_the_brief_the_orchestrator_builds_is_checked_for_every_part(self):
        found = execute.units(self.root)
        running = execute.brief(self.root, self.config, found["M1-P1-T1"])
        self.assertEqual([], execute.check_brief(running))

    def test_the_brief_check_asks_for_the_loop_as_well_as_the_contract(self):
        """A check that only looks for the five original parts would pass a
        brief with no critic contract in it at all."""
        for part in gauntlet.LOOP_PARTS:
            self.assertIn(part, execute.BRIEF_PARTS)
        found = execute.units(self.root)
        running = execute.brief(self.root, self.config, found["M1-P1-T1"])
        self.assertIn("The critic",
                      execute.check_brief(running.replace("The critic", "Whatever")))


# ---------------------------------------------------- every level, on the page

class TestThePlanDocumentsCarryAllFourLevels(Project):

    def setUp(self):
        Project.setUp(self)
        self.plan()

    def test_a_prompt_exists_for_the_plan_every_milestone_phase_and_task(self):
        found = gauntlet.carried(self.root)
        for unit in (gauntlet.WHOLE, "M1", "M1-P1",
                     "M1-P1-T1", "M1-P1-T2", "M1-P1-T3"):
            self.assertIn(unit, found)
            self.assertEqual([], gauntlet.check(
                found[unit], schema.plan_level(unit) or "plan"))

    def test_a_milestone_document_opens_with_its_own_instructions(self):
        _, spec = self._spec("M1")
        self.assertEqual("prompt", spec["sections"][0]["id"])

    def test_the_task_prompt_rides_on_the_task_and_the_phase_on_the_phase(self):
        _, spec = self._spec("M1")
        work = [one for one in spec["sections"] if one["id"] == "work"][0]
        self.assertTrue(all(one.get("prompt") for one in work["items"]))
        self.assertTrue(all(one.get("prompt") for one in work["areas"]))

    def test_the_index_lists_the_whole_build_and_the_milestones_only(self):
        """165 prompts in one index would bury the plan the index exists to show."""
        _, spec = self._spec(plan.INDEX_FILE)
        section = spec["sections"][0]
        self.assertEqual("prompts", section["type"])
        self.assertEqual(["prompt-orchestrator", "prompt-M1"],
                         [one["id"] for one in section["items"]])

    def _spec(self, name):
        from z2s import status
        for path in status.documents(self.root):
            if os.path.basename(path).startswith(name.split(".")[0]):
                return status.read(path)
        raise AssertionError("no document for %s" % name)


# ---------------------------------------------------------------- the command

class TestTheCommandLine(Project):

    def setUp(self):
        Project.setUp(self)
        self.plan()

    def run_it(self, *argv):
        import io
        out = io.StringIO()
        code = gauntlet.main(list(argv) + ["--root", self.root], out)
        return code, out.getvalue()

    def test_it_prints_the_prompt_a_reader_would_have_copied(self):
        code, text = self.run_it("M1-P1-T1")
        self.assertEqual(0, code)
        self.assertEqual(gauntlet.carried(self.root)["M1-P1-T1"], text.rstrip("\n"))

    def test_plan_is_accepted_as_a_name_for_the_whole_build(self):
        code, text = self.run_it("plan")
        self.assertEqual(0, code)
        self.assertEqual(gauntlet.carried(self.root)[gauntlet.WHOLE],
                         text.rstrip("\n"))

    def test_an_unknown_unit_is_refused_and_told_what_there_is(self):
        code, text = self.run_it("M9-P9-T9")
        self.assertEqual(1, code)
        self.assertIn("M1-P1-T1", text)

    def test_no_unit_named_is_a_misuse_rather_than_a_refusal(self):
        code, text = self.run_it()
        self.assertEqual(2, code)
        self.assertIn("usage", text)


# --------------------------------------------- R2-08 who runs the gauntlet

class TestOnlyARunIsToldItOwnsTheGauntlet(Project):
    """R2-08, and E2-04 held in a test.

    `claude -p` is one turn: the process exits when the model stops producing
    tool calls. Six of eleven builders dispatched after 20:00 on the win-it run
    ended their turn waiting on a long check — the shortest two minutes into a
    suite it had itself measured at nine. Every brief already said not to bet
    the unit on one more command finishing, and workers did it anyway, because
    they believed they had to establish the gauntlet themselves. Remove the
    belief and the failure mode is unreachable.

    It belongs in the run-only door and nowhere else. A pasted prompt has no run
    to own anything, exactly as with the status contract — and `LOOP` is carried
    by every published plan document, so putting it there would rewrite the live
    site to tell an operator something untrue of them.
    """

    def setUp(self):
        Project.setUp(self)
        self.plan()
        self.config = self.configure()

    def both(self, unit_id="M1-P1-T1"):
        found = execute.units(self.root)
        document = gauntlet.carried(self.root)[unit_id]
        running = execute.brief(self.root, self.config, found[unit_id],
                                found=found, titles=execute.catalog(self.root))
        return document, running

    def test_a_dispatched_brief_says_the_run_runs_the_gauntlet(self):
        _, running = self.both()
        self.assertIn(gauntlet.RUN_GAUNTLET, running)

    def test_a_pasted_prompt_never_says_it(self):
        document, _ = self.both()
        self.assertNotIn(gauntlet.RUN_GAUNTLET, document)

    def test_it_is_not_in_the_loop_every_published_document_carries(self):
        """The gate that keeps `docs/` out of this release."""
        self.assertNotIn(gauntlet.RUN_GAUNTLET, "\n".join(gauntlet.LOOP))
        for level in gauntlet.FANOUT:
            self.assertNotIn(gauntlet.RUN_GAUNTLET,
                             "\n".join(gauntlet.FANOUT[level]))
            self.assertNotIn(gauntlet.RUN_GAUNTLET, made(level))

    def test_it_tells_the_worker_to_run_only_what_shows_its_own_criteria_met(self):
        self.assertIn("only what it takes to show", gauntlet.RUN_GAUNTLET)
        self.assertIn("observes the exit status", gauntlet.RUN_GAUNTLET)

    def test_a_brief_without_it_is_incomplete(self):
        _, running = self.both()
        self.assertEqual([], execute.check_brief(running))
        stripped = running.replace(gauntlet.RUN_GAUNTLET, "")
        self.assertNotEqual([], execute.check_brief(stripped))



if __name__ == "__main__":
    unittest.main()
