# -*- coding: utf-8 -*-
"""Zero-to-Ship plan detail — M17.

M17 came from a measurement rather than a review. A real project was built with
this toolchain and instrumented while it ran: 70 of 191 units, about 171 hours.
Seventy-seven per cent of that was the builder dispatch, and thirty-five per
cent of THAT was thrown away — 46.8 hours across 36 superseded dispatches.

The causes were not worker quality. Every one of them was something the
orchestrator did:

* Seven of twelve gauntlet failures were whole-repository invariants the unit
  had never been told existed. The dispatch was discarded and a fresh worker
  briefed from nothing, which began by rebuilding what was already on disk.
* The gauntlet ran in whatever order the project wrote it down in, so a red
  layer cost 25.4 minutes to reach a verdict of "no".
* Three failures to launch, seconds apart with no wait anywhere, spent a unit's
  whole budget and blocked three units for the state of the host.
* A write list authored in a generated document could not be corrected without
  regenerating the plan the run was holding open.
* Two units were retried for failures a third had caused, and both retries were
  spent discovering exactly that.

Four requirements this changes are amended in place and dated — NFR-EXE-03,
NFR-EXE-04, NFR-EXE-05 and NFR-EXE-10 — along with ADR-15, whose ledger now
holds corrections the plan cannot express. Five identifiers are genuinely new,
because each states an obligation none of the four had: FR-EXE-17, FR-EXE-18,
FR-EXE-19, FR-EXE-20 and NFR-EXE-12.

No new decision is minted for the alternative the owner rejected — moving status
out of the generated document. ADR-05 and ADR-15 already record storing run
state in the plan document as a rejected alternative, and minting a decision
would be re-deciding a decided thing.
"""

DETAIL = {

"M17": [
 {"id": "M17-P1", "title": "One cost order, and the guards nobody was told about", "dependsOn": [],
  "summary": "State the verification layers' cost once for the whole method, run every gauntlet in it, name the "
             "whole-repository checks in the brief of every unit that does not name them itself, and settle "
             "those checks before a dispatch is thrown away.",
  "completion": ["Every gauntlet runs cheapest first, from an order no project can configure.",
                 "A brief names every check the unit will be held to, not the subset the unit asked for.",
                 "A whole-repository check that goes red reaches the worker that broke it, in the dispatch it "
                 "already worked in, exactly once."],
  "tasks": [
   {"id": "M17-P1-T1", "title": "The published cost order", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit", "lint"], "dependsOn": [],
    "summary": "Rank the eight verification layers by what each needs before it can say anything, hold the "
               "ranking in one leaf that imports only the layer vocabulary, and run every gauntlet through it.",
    "tdd": {"red": "A test declares a gauntlet holding a static check and an end-to-end suite, fails the static "
                   "one, and asserts the suite never ran; it fails while the order is the project's.",
            "green": "Sort a unit's layers by the published order before running any of them.",
            "refactor": "Lift the gauntlet loop out of the orchestrator into the leaf that owns the order, so "
                        "the order and the running of it are one thing."},
    "traces": {"nfr": ["NFR-EXE-12"], "us": ["US-EXE-10"]},
    "criteria": [{"id": "M17-P1-T1-C1", "kind": "auto",
                  "text": "Every layer the method knows has a place in the order, and the order is the same "
                          "however the project wrote its gauntlet down.", "done": True},
                 {"id": "M17-P1-T1-C2", "kind": "auto",
                  "text": "Nothing more expensive than the layer that fails is run at all.", "done": True},
                 {"id": "M17-P1-T1-C3", "kind": "auto",
                  "text": "No configuration key can change the order.", "done": True}]},
   {"id": "M17-P1-T2", "title": "A brief that names the whole bar", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit"], "dependsOn": ["M17-P1-T1"],
    "summary": "Derive the checks a project states that a unit does not name and that need nothing beyond a "
               "checkout, and put them and their commands in that unit's brief through the door only a "
               "dispatched worker reads.",
    "tdd": {"red": "A test briefs a unit against a gauntlet holding a check it never named and asserts the "
                   "brief names it; it fails while a brief carries only the unit's own layers.",
            "green": "Extend the verification block with the derived guards and one sentence saying what the "
                     "run does about a red one.",
            "refactor": "Keep the sentence in the run-only door, so nothing new reaches a published plan "
                        "document and the live site does not move."},
    "traces": {"fr": ["FR-EXE-17", "FR-EXE-03"], "nfr": ["NFR-EXE-04"], "us": ["US-EXE-10"]},
    "criteria": [{"id": "M17-P1-T2-C1", "kind": "auto",
                  "text": "A brief names every whole-repository check the unit will be held to, with its "
                          "command.", "done": True},
                 {"id": "M17-P1-T2-C2", "kind": "auto",
                  "text": "A check that needs a database, a browser or a person is never named as a guard.",
                  "done": True},
                 {"id": "M17-P1-T2-C3", "kind": "auto",
                  "text": "Nothing added here appears in a pasted prompt, and no published document moves.",
                  "done": True}]},
   {"id": "M17-P1-T3", "title": "The guards run before the dispatch is settled", "priority": "Must",
    "autonomy": "auto", "status": "passing", "layer": "orchestration", "testLayers": ["unit", "e2e"],
    "dependsOn": ["M17-P1-T2"],
    "summary": "Run those guards on the serial thread the moment a worker reports, before the report is read "
               "for anything, so a whole-repository failure is found while the tree the worker left is still "
               "the tree in front of everybody.",
    "tdd": {"red": "A test has a worker break a check the unit never named and asserts the run notices before "
                   "it settles; it fails while nothing runs a check no unit asked for.",
            "green": "Sweep the derived guards at the top of the settle.",
            "refactor": "Keep it off the concurrent half: the verification record is one file keyed by layer, "
                        "so two units proving the same layer at once would trust each other's evidence."},
    "traces": {"fr": ["FR-EXE-17"], "nfr": ["NFR-EXE-12"], "us": ["US-EXE-10"]},
    "criteria": [{"id": "M17-P1-T3-C1", "kind": "auto",
                  "text": "A guard that goes red is found before the report is judged.", "done": True},
                 {"id": "M17-P1-T3-C2", "kind": "auto",
                  "text": "The guards run on the one thread that writes, never beside another unit's.",
                  "done": True}]},
   {"id": "M17-P1-T4", "title": "A red guard goes back to whoever broke it", "priority": "Must",
    "autonomy": "auto", "status": "passing", "layer": "orchestration", "testLayers": ["unit", "e2e"],
    "dependsOn": ["M17-P1-T3"],
    "summary": "Hand a red guard back to the same worker in the same dispatch directory, once and never a loop, "
               "through the same mechanism that already asks a silent worker for its account — and commit what "
               "that turn changed with the unit.",
    "tdd": {"red": "A test asserts the worker that broke a guard is asked to fix it and the unit then passes "
                   "on its first attempt; it fails while the dispatch is discarded.",
            "green": "Write a second brief into the dispatch directory and run the same command against it.",
            "refactor": "Share one turn with the recovery path, so the safety vetting cannot be left out of "
                        "one of two places."},
    "traces": {"fr": ["FR-EXE-17"], "nfr": ["NFR-EXE-11"], "us": ["US-EXE-10"]},
    "criteria": [{"id": "M17-P1-T4-C1", "kind": "auto",
                  "text": "The worker that broke a guard is asked once, in the dispatch it already worked in.",
                  "done": True},
                 {"id": "M17-P1-T4-C2", "kind": "auto",
                  "text": "What that turn changed is committed with the unit's own work.", "done": True},
                 {"id": "M17-P1-T4-C3", "kind": "auto",
                  "text": "A guard still red after the turn fails the unit, and is not asked a third time.",
                  "done": True}]}]},

 {"id": "M17-P2", "title": "A dispatch that never started", "dependsOn": ["M17-P1"],
  "summary": "Wait between one failure to launch and the next, charge the unit neither counter for it, and stop "
             "the run once nothing at all is starting.",
  "completion": ["A failure to start costs the unit nothing and the run something.",
                 "A run that cannot launch a worker ends, saying why, rather than spinning."],
  "tasks": [
   {"id": "M17-P2-T1", "title": "A wait that is not a nap", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Wait a progressively longer interval before dispatching again after a dispatch that never "
               "started, without reading the clock and without a random source.",
    "tdd": {"red": "A test asserts the wait after the second failure is longer than after the first; it fails "
                   "while there is no wait at all.",
            "green": "Wait on an event that is never set, beside the grace period that already works that way.",
            "refactor": "Keep the schedule in the orchestrator and the waiting in the runner, so policy and "
                        "mechanism stay apart."},
    "traces": {"fr": ["FR-EXE-18"], "nfr": ["NFR-GEN-01"], "us": ["US-EXE-11"]},
    "criteria": [{"id": "M17-P2-T1-C1", "kind": "auto",
                  "text": "Each wait is longer than the one before it, up to a stated last.", "done": True},
                 {"id": "M17-P2-T1-C2", "kind": "auto",
                  "text": "Nothing added reads the clock or a random source.", "done": True}]},
   {"id": "M17-P2-T2", "title": "The host's problem is not the unit's budget", "priority": "Must",
    "autonomy": "auto", "status": "passing", "layer": "orchestration", "testLayers": ["unit"],
    "dependsOn": ["M17-P2-T1"],
    "summary": "Charge a dispatch that never started neither an attempt nor a misfire, on the one branch both "
               "routes into it already share.",
    "tdd": {"red": "A test settles a result that never ran and asserts both counters are untouched; it fails "
                   "while a misfire is charged.",
            "green": "Split the counter at the shared branch rather than at either caller.",
            "refactor": "Assert both sentences — the launch that raised and the process that exited leaving no "
                        "report — take the same route, because the observed symptom named only one."},
    "traces": {"fr": ["FR-EXE-18"], "nfr": ["NFR-EXE-05"], "us": ["US-EXE-11"]},
    "criteria": [{"id": "M17-P2-T2-C1", "kind": "auto",
                  "text": "A dispatch that never started charges the unit neither counter.", "done": True},
                 {"id": "M17-P2-T2-C2", "kind": "auto",
                  "text": "Both ways of never starting take the same route.", "done": True},
                 {"id": "M17-P2-T2-C3", "kind": "auto",
                  "text": "A dispatch that ran and then failed is charged exactly as it was before.",
                  "done": True}]},
   {"id": "M17-P2-T3", "title": "A run that stops instead of spinning", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit", "e2e"],
    "dependsOn": ["M17-P2-T2"],
    "summary": "Stop dispatching once a stated number of dispatches have failed to start consecutively, settle "
               "everything already in flight, and say why — a count any dispatch that started clears.",
    "tdd": {"red": "A test gives a project one unit and a worker that can never launch, and asserts the run "
                   "ends; it fails while nothing charges anything and the ready set never empties.",
            "green": "Keep the streak in the ledger and read it after each settle.",
            "refactor": "Drain rather than abandon: a halt starts nothing further and throws nothing away."},
    "traces": {"fr": ["FR-EXE-18", "FR-EXE-07"], "nfr": ["NFR-EXE-05"], "us": ["US-EXE-11"]},
    "criteria": [{"id": "M17-P2-T3-C1", "kind": "auto",
                  "text": "The run stops after the stated number of consecutive failures to start, and says so.",
                  "done": True},
                 {"id": "M17-P2-T3-C2", "kind": "auto",
                  "text": "Work already in flight is settled rather than abandoned.", "done": True},
                 {"id": "M17-P2-T3-C3", "kind": "auto",
                  "text": "Any dispatch that started clears the streak.", "done": True}]}]},

 {"id": "M17-P3", "title": "A failure the unit did not cause", "dependsOn": ["M17-P1"],
  "summary": "Know what was already red before anything was dispatched, sweep every stated layer at a milestone "
             "boundary, and establish from history rather than from a report whether another unit landed the "
             "file a failure names.",
  "completion": ["A unit is never charged an attempt for a layer that was failing before its worker started.",
                 "A layer no unit names is still run, at the boundary nearest whatever broke it.",
                 "Blame is read from version control, never asserted by a worker."],
  "tasks": [
   {"id": "M17-P3-T1", "title": "What was already red", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Survey the layers that need nothing beyond a checkout before the run dispatches anything, "
               "record which are failing, and drop one that has since gone green.",
    "tdd": {"red": "A test makes a layer red before the run starts and asserts the run says so before "
                   "dispatching; it fails while nothing looks.",
            "green": "Sweep the infrastructure-free layers at the top of the run.",
            "refactor": "Sweep one layer at a time, because a gauntlet stops at the first red and a survey "
                        "must not."},
    "traces": {"fr": ["FR-EXE-20"], "nfr": ["NFR-EXE-10"], "us": ["US-EXE-10"]},
    "criteria": [{"id": "M17-P3-T1-C1", "kind": "auto",
                  "text": "A layer already failing before the run is recorded and announced.", "done": True},
                 {"id": "M17-P3-T1-C2", "kind": "auto",
                  "text": "A unit whose gauntlet fails on such a layer is charged no attempt.", "done": True},
                 {"id": "M17-P3-T1-C3", "kind": "auto",
                  "text": "A layer that has gone green stops being recorded as red.", "done": True}]},
   {"id": "M17-P3-T2", "title": "Every layer at a milestone boundary", "priority": "Should", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit", "e2e"],
    "dependsOn": ["M17-P3-T1"],
    "summary": "Run every layer the project states when a wave closes, so a failure in a layer no unit names "
               "surfaces near whatever caused it rather than at whichever later unit happens to name it.",
    "tdd": {"red": "A test states a layer no unit names and asserts it is run at the boundary; it fails while "
                   "only the union of the units' layers is ever run.",
            "green": "Sweep the whole gauntlet when the wave changes and nothing is in flight.",
            "refactor": "Reuse the same survey as the opening one, so there is one implementation of what a "
                        "sweep is."},
    "traces": {"fr": ["FR-EXE-20"], "nfr": ["NFR-EXE-10"], "us": ["US-EXE-10"]},
    "criteria": [{"id": "M17-P3-T2-C1", "kind": "auto",
                  "text": "A layer no unit names is run at the milestone boundary.", "done": True},
                 {"id": "M17-P3-T2-C2", "kind": "auto",
                  "text": "The boundary sweep waits for the units already in flight.", "done": True}]},
   {"id": "M17-P3-T3", "title": "Blame read from history, never asserted", "priority": "Must",
    "autonomy": "auto", "status": "passing", "layer": "orchestration", "testLayers": ["unit"],
    "dependsOn": ["M17-P3-T1"],
    "summary": "When a unit's gauntlet fails over a file its declared write set does not cover, ask version "
               "control which unit landed that file, and treat another unit's file as a reason not to "
               "re-dispatch rather than a reason to.",
    "tdd": {"red": "A test lands a file under another unit's identifier, fails the gauntlet over it and asserts "
                   "the unit is charged no attempt; it fails while the run believes the report.",
            "green": "Read the last commit subject for the path and match the unit grammar.",
            "refactor": "Add no key to the report contract: a claim the run can check for itself is a claim it "
                        "should not be taking."},
    "traces": {"fr": ["FR-EXE-20", "FR-EXE-06"], "nfr": ["NFR-EXE-03"], "us": ["US-EXE-10"]},
    "criteria": [{"id": "M17-P3-T3-C1", "kind": "auto",
                  "text": "Which unit landed a path is read from version control.", "done": True},
                 {"id": "M17-P3-T3-C2", "kind": "auto",
                  "text": "A failure over another unit's file charges this unit no attempt.", "done": True},
                 {"id": "M17-P3-T3-C3", "kind": "auto",
                  "text": "The report contract gains no key for it.", "done": True}]}]},

 {"id": "M17-P4", "title": "A correction the plan cannot express", "dependsOn": ["M17-P1"],
  "summary": "Let an operator widen a unit's declared write set in the run's own state, apply it to the very "
             "next scheduling decision, and record which correction was acted on.",
  "completion": ["A wrong write list is corrected without the plan being regenerated.",
                 "A correction only ever widens, and the run says which one it used."],
  "tasks": [
   {"id": "M17-P4-T1", "title": "The overlay the scheduler reads", "priority": "Should", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Read an operator's additions from the ledger, put them in front of the disjointness check "
               "exactly as recorded strays already are, and never let one narrow a declared set.",
    "tdd": {"red": "A test declares two units disjoint, adds a shared path to one in the ledger, and asserts "
                   "they stop being disjoint; it fails while the document is the only source.",
            "green": "Replay the overlay onto each unit every round, beside the strays that already are.",
            "refactor": "Union it in the collision check through the same helpers the check already uses."},
    "traces": {"fr": ["FR-EXE-19"], "nfr": ["NFR-EXE-03"], "adr": ["ADR-15"], "us": ["US-EXE-11"]},
    "criteria": [{"id": "M17-P4-T1-C1", "kind": "auto",
                  "text": "A correction reaches the next scheduling decision with no regeneration.",
                  "done": True},
                 {"id": "M17-P4-T1-C2", "kind": "auto",
                  "text": "A correction only ever widens a declared write set.", "done": True},
                 {"id": "M17-P4-T1-C3", "kind": "auto",
                  "text": "A corrected path is no longer reported as a stray.", "done": True}]},
   {"id": "M17-P4-T2", "title": "The run says which correction it acted on", "priority": "Should",
    "autonomy": "auto", "status": "passing", "layer": "orchestration", "testLayers": ["unit"],
    "dependsOn": ["M17-P4-T1"],
    "summary": "Record the correction the run applied, once rather than once per round, and keep every added "
               "run-state key backward compatible by naming it where a fresh ledger is built.",
    "tdd": {"red": "A test replays the overlay twice and asserts one note; it fails while every round adds one.",
            "green": "Record on first application only.",
            "refactor": "Load a ledger written before this change and assert it gains the new keys and loses "
                        "nothing."},
    "traces": {"fr": ["FR-EXE-19"], "adr": ["ADR-15"], "nfr": ["NFR-EXE-07"], "us": ["US-EXE-11"]},
    "criteria": [{"id": "M17-P4-T2-C1", "kind": "auto",
                  "text": "The correction the run acted on is recorded exactly once.", "done": True},
                 {"id": "M17-P4-T2-C2", "kind": "auto",
                  "text": "A ledger written before this change loads unchanged and gains the new keys.",
                  "done": True}]}]},

 {"id": "M17-P5", "title": "Every surface that now says something untrue", "dependsOn": ["M17-P2", "M17-P3",
                                                                                        "M17-P4"],
  "summary": "Rewrite the published arithmetic a worker reads, because a failure to start no longer contributes "
             "to the worst case a skill body states, and a stale number is worse than none.",
  "completion": ["No prose surface states a retry bound the code no longer produces."],
  "tasks": [
   {"id": "M17-P5-T1", "title": "The retry arithmetic a worker is handed", "priority": "Must",
    "autonomy": "auto", "status": "passing", "layer": "docs", "testLayers": ["unit", "manual"],
    "dependsOn": [],
    "summary": "Rewrite the passage describing misfires, attempts and the worst case one unit can cost, rather "
               "than appending to it, and leave the re-run rule exactly as written because nothing here "
               "touches it.",
    "tdd": {"red": "A check asserts no shipped prose states the old worst case; it fails on the published "
                   "figure.",
            "green": "Rewrite the passage against what the code now does.",
            "refactor": "Repin the skill lock so the published bundle and the bodies agree."},
    "traces": {"fr": ["FR-EXE-18"], "nfr": ["NFR-EXE-05", "NFR-SKL-03"], "us": ["US-EXE-11"]},
    "criteria": [{"id": "M17-P5-T1-C1", "kind": "auto",
                  "text": "No prose surface states a retry bound the code no longer produces.", "done": True},
                 {"id": "M17-P5-T1-C2", "kind": "auto",
                  "text": "The one-re-run rule is stated exactly as it was.", "done": True},
                 {"id": "M17-P5-T1-C3", "kind": "human-review",
                  "text": "The published bundle pins every skill at the released version.", "done": True}]}]}],

}
