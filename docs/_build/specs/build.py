# -*- coding: utf-8 -*-
"""Zero-to-Ship — The build process. How a plan is actually run.

Everything the toolchain writes above this point is a document. This page
describes the one part that does work: the orchestrator that hands units to
workers, has the result judged by somebody who did not build it, runs the
verification gauntlet itself, and keeps going when one unit gets stuck.

The execution contract is NOT restated here. `z2s/gauntlet.py` is the one place
it is written down and `z2s/layers.py` is the one place the cost order is, so
this module imports both and renders from them. A sentence of the loop typed
into this file would be a second definition of the method, which is the exact
fault the method exists to remove.
"""

from z2s import gauntlet, layers

DOC = {
    "title": "Zero-to-Ship — The Build Process",
    "slug": "build",
    "kicker": "Execution",
    "type": "Process reference",
    "version": "2.11",
    "status": "For use",
    "date": "2026-09-04",
    "owner": "Zerø Effort",
    "releaseScope": "The orchestrator, end to end",
    "summary": "What happens when a derived plan is handed to machines: how one unit of work is briefed, built, "
               "verified and judged, how four of them run at once without colliding, and what every bound in "
               "the run costs when it fires.",
    "scopeNote": "Read this if you are evaluating whether an unattended build can be trusted, or if you are "
                 "about to operate one. The Playbook says which command to type; this says what the command "
                 "then does, and why each part of it was built the way it was.",
}

#: The loop and the judge's contract, rendered from the module that defines
#: them. A worker reads these words in its brief; a reader of this page reads
#: the same ones, from the same tuple.
LOOP = list(gauntlet.LOOP)
JUDGE = list(gauntlet.JUDGE_CONTRACT)

#: The four levels a fan-out is asked for at, in the order a plan nests them.
#: Indexed by name rather than iterated, so the rendered page cannot depend on
#: the order a dictionary happens to hold.
LEVELS = (
    ("A task", "task"),
    ("A phase", "phase"),
    ("A milestone", "milestone"),
    ("The whole build", "plan"),
)

#: Each verification layer, and whether it needs something a checkout does not
#: contain. Read from `layers.COST` so the order on the page is the order a
#: gauntlet actually runs in, and membership-tested rather than iterated so no
#: set ordering reaches the rendered file.
LADDER = [(name, name in layers.INFRASTRUCTURE) for name in layers.COST]

#: Which rungs are drawn as having run: everything up to and including the one
#: that went red. The five above it are ghosted, because on the run this figure
#: is drawn from they never ran at all.
_RED = "integration"
_STOPPED = layers.COST.index(_RED)

_LAYER_DESC = {
    "lint": "Static analysis. It reads files and needs nothing else, so it can be run at any moment, "
            "against any tree, by anybody.",
    "unit": "Tests that import the code and nothing more. Still infrastructure-free, still the run's to "
            "start whenever it likes.",
    "integration": "Wants a database. **This is the rung that went red**, and the run stopped climbing at "
                   "it. Everything cheaper than it had already been paid for.",
    "a11y": "Wants a rendered page, so a server and a browser. Never ran.",
    "e2e": "Wants the whole product up. Never ran.",
    "perf": "Wants all of that, and then wants it measured. Never ran.",
    "CI": "Wants a remote. Never ran.",
    "manual": "Wants a person, and there is nothing more expensive than a person. Never ran.",
}


def _report_items():
    """The report contract, as definition pairs, from the one tuple that states it."""
    return [{"term": "`%s` — `%s`" % (key, example), "def": note}
            for key, example, note in gauntlet.REPORT_SHAPE]


def _fanout_paragraphs():
    return ["**%s.** %s" % (label, " ".join(gauntlet.FANOUT[key]))
            for label, key in LEVELS]


def _ladder_steps():
    steps = []
    for index, (name, needs) in enumerate(LADDER):
        step = {"title": name, "desc": _LAYER_DESC[name], "h": 44 + index * 14}
        if name == _RED:
            step["kind"] = "accent"
        elif not needs:
            step["kind"] = "input"
        elif name == "manual":
            step["kind"] = "gate"
        if index > _STOPPED:
            step["ghost"] = True
        steps.append(step)
    return steps


SECTIONS = [
    # ---------------------------------------------------------------- 01
    {"id": "whatruns", "type": "prose", "title": "What a build run is",
     "body": [
         "A plan that has passed the coverage gate is a list of units — tasks, phases, milestones — each one "
         "carrying the criteria it must meet and the check that currently fails. A build run reads that list, "
         "works out which units nothing is waiting on, and hands them out. Everything from that point is "
         "mechanical, and it is mechanical on purpose: **the standard the work will be held to was fixed before "
         "the work started**, so nothing has to stop and ask.",

         "A worker is a command. It is named in the project's own settings, it is given two file paths — where "
         "its brief is, and where its report must go — and nothing in the run knows or cares whether that "
         "command is an agent, a script, or a person at a terminal. That is not an abstraction for its own "
         "sake. It is what makes an unattended build something you can test without one.",

         "The part that matters is what happens after the work exists. The run executes the verification "
         "gauntlet itself, so the exit status of every check is observed rather than reported. Then a second "
         "worker, in fresh context, is shown the work, the criteria and the evidence — and no account of how "
         "any of it was made. **Nothing passes on its author's say-so.** A build that graded itself would be "
         "a build with no standard at all, however carefully the grading was written.",

         "When a judgement comes back a fail, it comes back naming one gap, and that gap is the next brief. "
         "The loop is bounded: three attempts by default, after which the unit is marked blocked with the "
         "reason recorded, and the rest of the run carries on without it. A run that cannot finish one unit "
         "is not a reason to stop the other forty.",
     ],
     "highlights": [
         {"label": "Runs the checks", "title": "The exit status is observed",
          "text": "The gauntlet is executed by the run, not by the worker that wrote the code. What a check "
                  "returned is a fact the run holds, not a claim it was handed."},
         {"label": "Separates the roles", "title": "The judge never sees the builder's account",
          "text": "Structural, not procedural: the function that writes the judge's brief is never passed the "
                  "builder's report, so it cannot leak what it never receives."},
         {"label": "Bounds everything", "title": "Attempts, time and launches all have a ceiling",
          "text": "Three attempts per unit, ninety minutes per dispatch, three consecutive failures to start "
                  "before the run stops dispatching at all."},
         {"label": "Records it", "title": "Status is written back into the plan",
          "text": "The document that describes the work is the document that carries its state. There is no "
                  "second record to fall out of date."},
     ],
     "note": {"kind": "info", "label": "The one sentence.",
              "text": "A build run is the plan executed by workers who are told what to do, watched while they "
                      "do it, and graded by somebody else."}},

    # ---------------------------------------------------------------- 02
    {"id": "cycle", "type": "flow", "title": "One unit, end to end",
     "body": [
         "Every unit of a plan goes through the same five stations, and the interesting one is the return "
         "rail. A pass moves on. A fail comes back carrying exactly one gap — not a list, not a review, one "
         "named thing — and that gap becomes the brief for the next attempt, read by a judge who never saw "
         "the last one. **A critic who watched the previous attempt grades the improvement rather than the "
         "bar**, and improvement always looks like progress.",

         "Below is the instruction a lead is given, in the words every brief and every pasted prompt states "
         "it. It is rendered here from the module that defines it rather than copied, so this page and the "
         "running toolchain cannot come to disagree about what a build is.",
     ] + LOOP,
     "flows": [
         {"name": "The cycle, for one unit",
          "caption": "Five stations and one return rail. The rail is what makes it a cycle rather than a "
                     "pipeline, and the bound is what stops it being a loop.",
          "arm": {"from": 3, "to": 0,
                  "label": "One named gap — re-briefed, judged by a fresh worker",
                  "bound": "Bounded by attempts, then blocked with the reason recorded",
                  "tick": "×3"},
          "steps": [
              {"title": "The brief", "kind": "input",
               "desc": "The unit, its criteria, the check that must go from failing to passing, and the "
                       "whole-repository guards no single unit names."},
              {"title": "A worker builds",
               "desc": "One command, given two paths. It produces the work and the evidence for it — the "
                       "command output, the rendered thing, the passing test."},
              {"title": "The gauntlet runs", "kind": "gate",
               "desc": "Executed by the run, cheapest layer first. A layer that fails is run once more "
                       "before it costs the unit anything."},
              {"title": "A fresh judge", "kind": "accent",
               "desc": "A separate worker, fresh context, shown the work and the criteria and the evidence — "
                       "and nothing the builder wrote about its own work."},
              {"title": "Committed",
               "desc": "A pass commits the named files and writes the unit's status back into the plan "
                       "document that describes it."},
          ]},
     ]},

    # ---------------------------------------------------------------- 03
    {"id": "roles", "type": "screen", "title": "The workers, and what each is shown",
     "body": [
         "A run has two kinds of worker and one wall between them. The builder is given the unit and produces "
         "the work; the judge is given the work and produces a verdict. What makes the verdict worth anything "
         "is not the judge's diligence but what the judge is structurally unable to see.",

         "The builder's report crosses no boundary. It is how the run learns which files to commit, which "
         "commands were run and which criteria are claimed — and it stops there. The function that assembles "
         "the judge's brief is never handed that report, so there is no path along which a builder's account "
         "of its own work can reach the person grading it. **It cannot leak what it never receives**, which is "
         "why the design lives in a function signature rather than in a rule somebody has to remember.",

         "The judge's contract, in full, as every judging worker is given it:",
     ],
     "screen": {
         "name": "Who can see what",
         "caption": "Three things pass the wall. The fourth is refused at it, and the refusal is the "
                    "guarantee.",
         "passes": [
             {"title": "The unit and its criteria",
              "desc": "What the work was supposed to be, by identifier, exactly as the plan states it."},
             {"title": "The work itself",
              "desc": "The changed files, named. The judge is told to open them and read them rather than "
                      "accept any description of them."},
             {"title": "The evidence",
              "desc": "Every gauntlet layer that ran, the command, and the exit status the run observed "
                      "itself."},
         ],
         "refused": {"title": "The builder's report",
                     "desc": "What the builder said about its own work — its account, its reasoning, its "
                             "claims about which criteria are met. The run reads it. The judge never does."},
         "judge": {"title": "The judge",
                   "desc": "A separate worker in fresh context, deciding against the criteria and the "
                           "verification results rather than against its own taste."},
         "barrier": {"title": "The separation",
                     "desc": "Structural rather than procedural: the judge's brief is assembled by a function "
                             "that is never passed the report, so nothing has to be remembered for this to "
                             "hold."},
     },
     "items": JUDGE},

    # ---------------------------------------------------------------- 04
    {"id": "contract", "type": "defs", "title": "What a worker must return",
     "intro": "One schema, eight keys, and the same tuple renders the contract into every brief and validates "
              "every report that comes back. A key added to one half and not the other is the defect this "
              "shape exists to make impossible. Note what is absent: **there is no status key**. What a worker "
              "reports is what it did, and the status that follows from it is not the worker's to claim.",
     "items": _report_items()},

    # ---------------------------------------------------------------- 05
    {"id": "fanout", "type": "flow", "title": "Running four at once without collisions",
     "body": [
         "Four workers run at the same time by default. Four rather than eight or sixteen, because the "
         "binding constraint is review capacity rather than machine capacity — every unit that comes back has "
         "to be verified and judged on one thread, and a fifth builder simply queues behind that.",

         "Concurrency is deliberately narrow. Worker processes run beside each other; everything that writes "
         "— the gauntlet, the judgement, the status write-back, the ledger, the commit — happens one at a "
         "time. **A run has exactly one writer**, and running the gauntlet concurrently would break something "
         "subtler still, because the verification record is keyed by layer and two units proving the same "
         "layer at once would each be trusting the other's evidence.",

         "Which units may go out together is a question about files. Each unit declares the files it will "
         "write; two units whose declarations intersect are never dispatched together. A unit that declares "
         "nothing runs alone — guessing the other way means two workers editing one file, which is the "
         "failure concurrency was supposed to be worth risking. The awkward case is the file nobody can "
         "declare: a shared manifest, an append-only log. When two units collide on one of those, neither is "
         "charged an attempt — the unit did the only thing that ships the work, and the run chose who it ran "
         "beside — and the pair is remembered, so it never goes out together again.",

         "How far a unit is split before any of that applies depends on what was asked for:",
     ] + _fanout_paragraphs(),
     "flows": [
         {"name": "Four in the fixture, one writer",
          "caption": "The brace means these pieces are in the fixture at the same time. Everything after it "
                     "happens on one thread, in order.",
          "steps": [
              {"title": "Ready units", "kind": "input",
               "desc": "Everything the plan says nothing is waiting on, with its declared write set attached."},
              {"branch": [
                  {"title": "Unit one",
                   "desc": "Dispatched with its own brief, its own directory and its own report path."},
                  {"title": "Unit two",
                   "desc": "**Four is the ceiling.** The bound is how much can be reviewed, not how much can "
                           "be run."},
                  {"title": "Unit three",
                   "desc": "No two units here declare a file in common. Intersecting write sets are never "
                           "paired."},
                  {"title": "Unit four",
                   "desc": "A pair that collided once on a file neither could declare is never paired again "
                           "for the rest of the run."},
              ]},
              {"branch": [
                  {"title": "Unit five",
                   "desc": "A unit that declares no write set runs alone, in a wave of one. Silence about "
                           "files collides with everything."},
              ]},
              {"title": "One thread writes", "kind": "accent",
               "desc": "The gauntlet, the judgement, the status write-back, the ledger and the commit, one "
                       "unit at a time, in the order the units came back."},
          ]},
     ]},

    # ---------------------------------------------------------------- 06
    {"id": "gauntlet", "type": "flow", "title": "The gauntlet, cheapest first",
     "body": [
         "A verification gauntlet is a set of commands, and for a long time nothing in the method said what "
         "order to run them in — so every project ran them in whatever order it happened to write them down. "
         "On one measured build that cost **25.4 minutes to reach a verdict of \"no\"**: an end-to-end suite "
         "and a browser pass both ran to completion before the static check that was always going to fail got "
         "its turn.",

         "The order is not a project's business to get right. The same eight layers cost the same relative "
         "amounts in every project there has ever been, so the order is stated once and every gauntlet runs "
         "in it. **There is no configuration knob**, because a project that could reorder them would "
         "eventually reorder them wrongly, and the failure is silent — a slow gauntlet looks exactly like a "
         "thorough one.",

         "The first two rungs need nothing a checkout does not already contain, which is what makes a "
         "preflight possible: they can be run at any moment, against any tree, by anybody. The other six want "
         "a database, a browser, a server, a remote or a person. And a layer that fails is run once more "
         "before it charges the unit anything — a check that fails and then passes over a tree nothing "
         "touched in between is evidence about the check rather than about the work. One re-run, never a "
         "configured number: a layer that needs three goes is broken in a way a setting would hide.",

         "One more finding is worth stating, because it was the expensive one. A project's gauntlet usually "
         "holds guards no single unit names — package-wide scanners, a determinism check, a budget summed "
         "across files this unit never opened. **Seven of twelve gauntlet failures on that build were one of "
         "those**, and every one discarded a finished dispatch, because nothing in the brief had ever "
         "mentioned the guard it broke. So now the brief names them.",
     ],
     "flows": [
         {"name": "The eight layers, in cost order",
          "caption": "Height is cost. The ghosted rungs never ran on this build, and the armature ends "
                     "where the run ended.",
          "steps": _ladder_steps()},
     ]},

    # ---------------------------------------------------------------- 07
    {"id": "failure", "type": "table", "title": "When it goes wrong",
     "intro": "Six ways a unit fails to get through, and what each one costs it. The distinction that does "
              "the work here is between an **attempt** — the unit was given a fair go and did not make it — "
              "and a **misfire**, where something outside the unit denied it one. They are counted "
              "separately, and only one of them is the unit's fault.",
     "columns": ["What happened", "What it costs the unit", "What bounds it"],
     "mono": [],
     "rows": [
         ["The judge returns a fail",
          "One attempt. The single gap it named becomes the next brief, read by a fresh judge.",
          "Three attempts by default, then the unit is blocked with the reason recorded."],
         ["A gauntlet layer fails twice",
          "One attempt. The unit never reaches a judge, because there is nothing yet worth judging.",
          "The same three attempts. A layer that fails once and passes on the re-run costs nothing and is "
          "recorded as a disagreement."],
         ["The worker stops moving",
          "Nothing — a misfire, not an attempt. It is stopped along with everything it started, then asked "
          "once for an account of the work it left on disk.",
          "Ninety minutes per dispatch by default, and the recovery turn shares that bound. Misfires are "
          "counted against the same three."],
         ["Two units collide on a file neither declared",
          "Nothing — a misfire. The unit did the only thing that ships the work; the run chose who it ran "
          "beside.",
          "The pair is remembered and never dispatched together again, so the same collision cannot re-form."],
         ["The worker never starts at all",
          "Nothing, and no misfire either. A host that cannot launch a process has said nothing about the "
          "unit.",
          "Each failure waits longer than the last — thirty seconds, two minutes, five — and three "
          "consecutive failures with nothing starting in between stop the run dispatching anything further."],
         ["A worker writes outside its declared set",
          "Usually nothing. It is often the only thing possible, and the paths are recorded rather than "
          "punished.",
          "Every stray path is added to the unit's write set for the rest of the run, so a pair that clashed "
          "once is never paired again."],
     ]},

    # ---------------------------------------------------------------- 08
    {"id": "economy", "type": "prose", "title": "What the bounds cost, measured",
     "body": [
         "Every number in a run is a bound somebody paid for. They are worth reading together, because the "
         "arithmetic is not one bound per unit and a reader who assumes it is will be surprised by how long a "
         "thoroughly wedged unit can take to give up.",

         "The dispatch bound is ninety minutes, and a dispatch that runs out of time is asked once for its "
         "account within the same ninety — so one wedged dispatch costs up to three hours. A timeout is a "
         "misfire rather than an attempt, so the unit is re-dispatched until it has misfired as many times as "
         "the project allows attempts. **Three at the defaults, which is a nine-hour worst case for one unit "
         "before it blocks.** Bounded, which is the whole point, and not small — so a project whose units "
         "genuinely take longer sets its own number rather than discovering this one.",

         "The recovery turn is where the largest measured saving is. A worker that stopped without a report "
         "is asked one more time, in the directory it left, with the tree and the evidence and its own "
         "working notes all still there — rather than a fresh worker being briefed from nothing and starting "
         "by rebuilding what is already on disk. On a measured build, **46.8 hours across 36 superseded "
         "dispatches** went exactly that way before the extra turn existed.",

         "The other figures are all failures somebody watched. Six of eleven builders on one night's run "
         "died mid-turn on a long check, the shortest two minutes in; a worker is now told to leave the "
         "gauntlet alone, because it cannot be relied on to survive one. A build idled for **two hours and "
         "twenty-two minutes** with the work finished on disk and nothing in the method that was ever going "
         "to notice. That is what the dispatch bound is for. And a database container outlived its dispatch "
         "by two and a half hours, with four later units running their checks against a service the run "
         "believed was gone — so a run now says what is still up on the host, and touches none of it.",
     ],
     "note": {"kind": "warn", "label": "Do the arithmetic before you trust the ceiling.",
              "text": "The published nine-hour figure depends on the recovery turn sharing the build's "
                      "timeout. Give recovery a larger bound, or no bound at all, and every number above "
                      "stops being true."}},

    # ---------------------------------------------------------------- 09
    {"id": "settings", "type": "code", "title": "What a run has to be told",
     "intro": "A run refuses before it starts a single process if any of this is missing. Discovering halfway "
              "through a milestone that there is no judge means having already written status nobody can "
              "justify. A command is an argv list and the instruction is part of it: `{brief}` and "
              "`{report}` are replaced wherever they occur, including inside the prompt itself. There "
              "are no flags for them.",
     "blocks": [
         {"title": "The project's worker record", "note": "`.zero/workers.json`",
          "code": """{
  "workers": [
    {"name": "builder",  "role": "build",
     "command": ["claude", "-p",
                 "Read the brief at {brief} and carry it out exactly. Write your report as JSON to {report} and nothing else to stdout.",
                 "--permission-mode", "acceptEdits", "--dangerously-skip-permissions"]},
    {"name": "critic",   "role": "judge",
     "command": ["claude", "-p",
                 "Read the judgement brief at {brief}. Judge the work against its acceptance criteria only. Write your verdict as JSON to {report} and nothing else to stdout.",
                 "--permission-mode", "acceptEdits", "--dangerously-skip-permissions"]}
  ],
  "gauntlet": {
    "lint":  ["python3", "-m", "z2s.validate", "docs"],
    "unit":  ["python3", "-m", "unittest", "discover", "-s", "tests"],
    "CI":    ["python3", "-m", "z2s.pipeline", "--record", "."]
  },
  "ceiling":  4,
  "attempts": 3,
  "timeout":  5400
}"""},
     ],
     "note": {"kind": "warn", "label": "That last flag is what it says it is.",
              "text": "`--dangerously-skip-permissions` turns off every approval prompt, and a worker "
                      "that keeps them stops at the first one and is killed at the bound with nothing "
                      "written. So it is the flag an unattended run needs and the flag that gives an "
                      "unattended run the whole checkout and whatever credentials the environment "
                      "carries. Run workers where that is true on purpose — a container or a "
                      "throwaway clone with no keys in it — rather than in the shell you read mail "
                      "in. `--allowedTools` narrows what a worker may reach without turning the "
                      "prompts off, and is worth the wedged dispatches if the tree is one you cannot "
                      "hand over."}},

    # ---------------------------------------------------------------- 10
    {"id": "limits", "type": "list", "title": "What a run deliberately never does",
     "intro": "Each of these was the other option once, and each is written down because the reasoning is "
              "easy to lose and the behaviour is easy to add back by accident.",
     "items": [
         {"title": "It never accepts a verdict from the author",
          "text": "A builder's report is read by the run and never by the judge. There is no flag for this, "
                  "no fast path, and no mode in which a unit passes on its own account."},
         {"title": "It never sets a dispatched worker's status",
          "text": "A worker that graded its own work would be grading its own work. The run observes the "
                  "gauntlet, takes the judgement and records what follows — and a pasted prompt says the "
                  "opposite, because there its reader is the run."},
         {"title": "It never removes a container",
          "text": "A run reports what is still up on the host and touches none of it. Tearing down a live "
                  "database is not reliably a ten-second job, and a container an operator started for their "
                  "own reasons is not the run's to destroy."},
         {"title": "It never runs a gauntlet command through a shell",
          "text": "Every command is a list of words, executed directly. A glob, a pipe, a `&&` or a "
                  "variable never expands, which is why a command written as a single string is refused "
                  "rather than split."},
         {"title": "It never performs a destructive git operation",
          "text": "Force-pushing, rewriting shared history, deleting a branch holding unmerged work and "
                  "deleting anything outside the working area are refused by one guard that every caller "
                  "asks rather than restates."},
         {"title": "It never fetches anything from the web",
          "text": "Sources are recorded, never retrieved. A test asserts that no module in the toolchain "
                  "imports a network library at all."},
         {"title": "It never loops without a bound",
          "text": "Attempts, dispatch time, launch failures and gauntlet re-runs each have a ceiling, and "
                  "the one that has no setting — a single re-run of a failed layer — has none on purpose."},
     ]},
]
