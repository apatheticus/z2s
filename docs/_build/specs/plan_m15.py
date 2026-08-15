# -*- coding: utf-8 -*-
"""Zero-to-Ship plan detail — M15.

Its own module rather than a third milestone bolted onto `plan_m13_m14`, whose
name would then be the same quiet untruth `plan_m09_m12` had become.

M15 came out of a review, not a specification: the owner read the plan M14 had
produced and reported four faults in it. Three were usability — a prompt row
nobody could tell was a control, a whole-build prompt nobody could find, and an
expanded plan nobody could navigate — and one was size. The requirements those
faults touch were amended in place and dated rather than rewritten, so the
originals still say what every existing trace was written against.
"""

DETAIL = {

"M15": [
 {"id": "M15-P1", "title": "One document per milestone", "dependsOn": [],
  "summary": "Split the published plan into an index and one file per milestone, cross-linked, with nothing "
             "declared twice and nothing scheduled that has no document to read.",
  "completion": ["The index carries the prompts, the waves, the prerequisites and the coverage proof, and none "
                 "of the work.",
                 "Every milestone is its own file, reachable from the index and from every other milestone.",
                 "No identifier is declared twice anywhere in the set."],
  "tasks": [
   {"id": "M15-P1-T1", "title": "The plan becomes an index and one file per milestone",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Return a list of pages from the plan builder rather than one specification, writing the index "
               "under its existing name so no inbound link breaks, and one milestone document beside it.",
    "tdd": {"red": "A test asserts the plan builder returns the index plus one page per milestone, each naming "
                   "the milestone it carries; it fails while the builder returns a single specification.",
            "green": "Split the builder and let the write loop take a list of pages.",
            "refactor": "Derive every milestone filename from one map, so the links table, the waves and the "
                        "navigation cannot disagree about where a milestone lives."},
    "traces": {"fr": ["FR-SPC-09", "FR-PLN-13"], "nfr": ["NFR-PRF-02"], "us": ["US-SPC-05"]},
    "criteria": [{"id": "M15-P1-T1-C1", "kind": "auto",
                  "text": "The index keeps its filename and every milestone has its own file beside it.",
                  "done": True},
                 {"id": "M15-P1-T1-C2", "kind": "auto",
                  "text": "No single plan page exceeds half a megabyte.", "done": True}]},
   {"id": "M15-P1-T2", "title": "The index lists milestones as rows, never as entries",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit", "lint"], "dependsOn": ["M15-P1-T1"],
    "summary": "Carry the milestones on the index as a table, because every phase, task and criterion is "
               "declared on its own page and repeating them would declare each identifier twice in the set.",
    "tdd": {"red": "A test asserts the index declares no plan identifier at all and that every task in the plan "
                   "is declared exactly once across the whole set; it fails while the index repeats the "
                   "milestone entries.",
            "green": "Render the index's milestones as rows.",
            "refactor": "Let the rendered-document checker read the milestone pages for the per-task "
                        "invariants, rather than an index that no longer carries any."},
    "traces": {"fr": ["FR-TRC-02", "FR-PLN-13"], "adr": ["ADR-03"], "us": ["US-TRC-01"]},
    "criteria": [{"id": "M15-P1-T2-C1", "kind": "auto",
                  "text": "The set validator reports no duplicate identifier.", "done": True},
                 {"id": "M15-P1-T2-C2", "kind": "auto",
                  "text": "Every scheduled milestone names a detail document that the run actually wrote.",
                  "done": True}]},
   {"id": "M15-P1-T3", "title": "Every part of the plan reaches every other part",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "runtime",
    "testLayers": ["e2e", "a11y"], "dependsOn": ["M15-P1-T1"],
    "summary": "Give each plan document a list of the files it is written across, rendered beside the contents, "
               "with the part in hand stated rather than offered as a link — and kept apart from the "
               "document-set navigation, which means something different.",
    "tdd": {"red": "A browser test opens one milestone document and asserts it links the index and every other "
                   "milestone and marks itself; it fails while a reader has only the back button.",
            "green": "Carry the list in the specification and render it.",
            "refactor": "Build the list once, from the same filename map the links table uses."},
    "traces": {"fr": ["FR-SPC-09"], "nfr": ["NFR-UX-01", "NFR-UX-03"], "us": ["US-SPC-05"]},
    "criteria": [{"id": "M15-P1-T3-C1", "kind": "auto",
                  "text": "A reader on any part of the plan can reach every other part and the index.",
                  "done": True},
                 {"id": "M15-P1-T3-C2", "kind": "auto",
                  "text": "The document-set navigation is unchanged by the split.", "done": True}]}]},

 {"id": "M15-P2", "title": "A plan is navigated, not scrolled", "dependsOn": ["M15-P1"],
  "summary": "Fold every level of the work, open the first unit at each level on arrival, close a unit's "
             "siblings when it is opened, and make the execution prompt a control rather than a line of text.",
  "completion": ["A plan document arrives with the first unit at each level open and every sibling shut.",
                 "Opening one unit closes its siblings at that level, at every level.",
                 "A collapsed prompt names its unit and copies without being opened."],
  "tasks": [
   {"id": "M15-P2-T1", "title": "Every level of the work folds",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "runtime",
    "testLayers": ["e2e", "a11y"], "dependsOn": [],
    "summary": "Make phases and tasks collapsible as milestones already were, with the heading a real control "
               "so it carries keyboard handling, and the first unit at each level open per parent.",
    "tdd": {"red": "A browser test asserts the first phase and the first task of every phase arrive open and "
                   "every sibling is shut; it fails while opening a milestone renders all of its work.",
            "green": "Fold the phase and task bodies and render the arrival state.",
            "refactor": "Read the arrival state back from what was rendered, so a cleared filter returns the "
                        "reader what they were given rather than a second statement of it."},
    "traces": {"fr": ["FR-SPC-10"], "nfr": ["NFR-UX-01", "NFR-UX-05"], "us": ["US-SPC-05"]},
    "criteria": [{"id": "M15-P2-T1-C1", "kind": "auto",
                  "text": "On arrival the first unit at each level is open and every sibling is shut.",
                  "done": True},
                 {"id": "M15-P2-T1-C2", "kind": "auto",
                  "text": "The open unit at each level is the first of its own parent, not the first on the "
                          "page.", "done": True}]},
   {"id": "M15-P2-T2", "title": "Opening one unit closes its siblings",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "runtime",
    "testLayers": ["e2e"], "dependsOn": ["M15-P2-T1"],
    "summary": "Bind the rule to the reader's click rather than to the fold's own change event, so the opens "
               "the runtime performs itself — a deep link, a keyword match, expand-all — are not mistaken for "
               "a reader asking for one thing at a time.",
    "tdd": {"red": "A browser test opens a second phase and asserts the first closes while the tasks inside "
                   "the other phases are untouched; it fails while nothing closes anything.",
            "green": "Close the siblings at the same level when a unit is opened.",
            "refactor": "Extend expand-all and collapse-all to every level, so neither is a half-truth."},
    "traces": {"fr": ["FR-SPC-10"], "us": ["US-SPC-05"]},
    "criteria": [{"id": "M15-P2-T2-C1", "kind": "auto",
                  "text": "Opening a unit leaves exactly one open among its siblings.", "done": True},
                 {"id": "M15-P2-T2-C2", "kind": "auto",
                  "text": "A keyword opens every unit it matches, and clearing it restores the arrival state.",
                  "done": True},
                 {"id": "M15-P2-T2-C3", "kind": "auto",
                  "text": "A link to a unit two levels down opens every level between it and the page.",
                  "done": True}]},
   {"id": "M15-P2-T3", "title": "The execution prompt is a control",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "runtime",
    "testLayers": ["e2e", "a11y"], "dependsOn": [],
    "summary": "Name the unit the prompt belongs to, make the row read as something that opens, and keep the "
               "copy control usable while it is shut — copying is the common use and reading on screen is the "
               "rare one.",
    "tdd": {"red": "A browser test clicks the copy control on a collapsed prompt and asserts the clipboard "
                   "holds the prompt and the row is still collapsed; it fails while the control only exists "
                   "once the row is open.",
            "green": "Move the control into the summary and read the block from the whole fold.",
            "refactor": "Change the one function every level renders through, so all of them move at once."},
    "traces": {"fr": ["FR-EXE-15", "FR-EXE-16"], "nfr": ["NFR-UX-01"], "us": ["US-SPC-05", "US-EXE-08"]},
    "criteria": [{"id": "M15-P2-T3-C1", "kind": "auto",
                  "text": "A collapsed prompt names the unit it belongs to.", "done": True},
                 {"id": "M15-P2-T3-C2", "kind": "auto",
                  "text": "The copy control is usable while the prompt is collapsed, and using it leaves the "
                          "prompt collapsed.", "done": True},
                 {"id": "M15-P2-T3-C3", "kind": "human-review",
                  "text": "An operator can tell at a glance that the row opens and that a prompt is what it "
                          "holds.", "done": True}]},
   {"id": "M15-P2-T4", "title": "Paper gets what the screen folds away",
    "priority": "Should", "autonomy": "auto", "status": "passing", "layer": "runtime",
    "testLayers": ["e2e"], "dependsOn": ["M15-P2-T1"],
    "summary": "Expand every folded phase and task when printed, and keep dropping only the instructions, "
               "which a printed page cannot be copied from.",
    "tdd": {"red": "A browser test reads what the engine computed under print and asserts every folded body is "
                   "visible and every prompt is not; it fails because folding the work made the instructions a "
                   "child of a fold the print rules expand.",
            "green": "State the rule that drops instructions separately, so it wins.",
            "refactor": "Ask the browser rather than the stylesheet, since reading the stylesheet is what "
                        "missed it."},
    "traces": {"fr": ["FR-SPC-11"], "us": ["US-SPC-05"]},
    "criteria": [{"id": "M15-P2-T4-C1", "kind": "auto",
                  "text": "Under print every folded phase and task body is visible.", "done": True},
                 {"id": "M15-P2-T4-C2", "kind": "auto",
                  "text": "Under print no execution prompt is visible.", "done": True}]}]},

 {"id": "M15-P3", "title": "The same behaviour in the toolchain", "dependsOn": ["M15-P2"],
  "summary": "Apply all of it to the generator other projects use, opting in per section so no specification "
             "catalogue changes at all.",
  "completion": ["A generated plan folds, navigates and copies exactly as the published one does.",
                 "Every specification catalogue is untouched: open on arrival, nothing closing anything else."],
  "tasks": [
   {"id": "M15-P3-T1", "title": "The collapsed default is opted into per section",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "runtime",
    "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Mark the plan's work section as navigated and let the entry render as a fold only there, so a "
               "requirements catalogue rendered by the same runtime keeps showing its contents.",
    "tdd": {"red": "A browser test follows a task's claim into the specification that states it and asserts "
                   "every group there is still open and no entry is a fold; it fails if the default leaks.",
            "green": "Read the flag from the section and render accordingly.",
            "refactor": "Carry the flag in the markup, so the behaviour is decided once at render time rather "
                        "than inferred later."},
    "traces": {"fr": ["FR-SPC-10"], "nfr": ["NFR-ARC-04"], "us": ["US-SPC-05"]},
    "criteria": [{"id": "M15-P3-T1-C1", "kind": "auto",
                  "text": "A specification catalogue arrives with every group open and no entry folded.",
                  "done": True},
                 {"id": "M15-P3-T1-C2", "kind": "auto",
                  "text": "Only the plan's work section carries the navigated flag.", "done": True}]},
   {"id": "M15-P3-T2", "title": "A generated plan navigates between its own files",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["e2e"], "dependsOn": ["M15-P3-T1"],
    "summary": "Carry the list of files a generated plan is written across in every one of them, so an operator "
               "who followed a wave into a milestone can reach the index and every other milestone.",
    "tdd": {"red": "A browser test asserts a generated milestone document lists the index and every sibling "
                   "milestone and marks itself; it fails while no such navigation exists.",
            "green": "Build the list where the filenames are already known and put it in every specification.",
            "refactor": "Share one builder between the index and the milestone documents."},
    "traces": {"fr": ["FR-SPC-09", "FR-PLN-13"], "us": ["US-SPC-05"]},
    "criteria": [{"id": "M15-P3-T2-C1", "kind": "auto",
                  "text": "Every generated plan document names every other part of the plan.", "done": True},
                 {"id": "M15-P3-T2-C2", "kind": "auto",
                  "text": "The part the reader is on is stated and is not a link.", "done": True}]},
   {"id": "M15-P3-T3", "title": "The shared chrome stays inside its budget",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "foundation",
    "testLayers": ["unit"], "dependsOn": ["M15-P3-T1", "M15-P3-T2"],
    "summary": "Measure the styling and runtime a document carries before and after, and fit the change inside "
               "the existing allowance rather than moving it.",
    "tdd": {"red": "The existing budget check fails the moment the chrome grows past its allowance.",
            "green": "Condense what was written twice until the change fits.",
            "refactor": "Report the remaining headroom, so the next change starts from a number rather than "
                        "from a feeling."},
    "traces": {"nfr": ["NFR-PRF-02", "NFR-ARC-03"], "us": ["US-GEN-02"]},
    "criteria": [{"id": "M15-P3-T3-C1", "kind": "auto",
                  "text": "The shared chrome is within its budget with the change applied.", "done": True}]}]},

 {"id": "M15-P4", "title": "Amended in place, and planned", "dependsOn": ["M15-P3"],
  "summary": "Record what changed about the requirements this touches as dated amendments under the originals, "
             "render them, and plan the work as a milestone of the published plan.",
  "completion": ["Every requirement this changes carries a dated amendment and its original wording.",
                 "The published documents render an amendment.",
                 "The work is a milestone of the plan, claimed and covered like every other."],
  "tasks": [
   {"id": "M15-P4-T1", "title": "Three dated amendments, no identifier retired",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "docs",
    "testLayers": ["unit", "lint"], "dependsOn": [],
    "summary": "Amend contents navigation, expand-and-collapse and the prompt-at-every-level requirement in "
               "place and dated, leaving each original exactly as written — the method practising its own rule "
               "on itself for the first time.",
    "tdd": {"red": "A test asserts each of the three requirements carries a dated amendment and that its "
                   "original text is unchanged; it fails while the change is only in code.",
            "green": "Add the amendments to the functional specification.",
            "refactor": "Fold amendment text into what the keyword box reads, so a reader searching for the "
                        "new behaviour finds the requirement that states it."},
    "traces": {"fr": ["FR-AMD-04", "FR-TRC-01"], "adr": ["ADR-03"], "us": ["US-AMD-01"]},
    "criteria": [{"id": "M15-P4-T1-C1", "kind": "auto",
                  "text": "Each amended requirement carries a dated amendment and its original wording.",
                  "done": True},
                 {"id": "M15-P4-T1-C2", "kind": "auto",
                  "text": "The counted universe of identifiers is unchanged.", "done": True}]},
   {"id": "M15-P4-T2", "title": "The published documents render an amendment",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "runtime",
    "testLayers": ["e2e"], "dependsOn": ["M15-P4-T1"],
    "summary": "Show an amendment below the original under its own heading and date, so a reader can see which "
               "words were frozen and which arrived later.",
    "tdd": {"red": "A browser test asserts an amended requirement shows both its original text and its dated "
                   "amendment; it fails while the published renderer drops amendments silently.",
            "green": "Render them.",
            "refactor": "Match the shape the toolchain's own runtime already uses, so the two documents of the "
                        "same requirement read the same."},
    "traces": {"fr": ["FR-AMD-04", "FR-SPC-01"], "us": ["US-AMD-01"]},
    "criteria": [{"id": "M15-P4-T2-C1", "kind": "auto",
                  "text": "An amended requirement renders its original and its dated amendment.", "done": True}]},
   {"id": "M15-P4-T3", "title": "The work is a milestone of the plan",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "docs",
    "testLayers": ["unit", "CI"], "dependsOn": ["M15-P4-T1"],
    "summary": "Plan this work as a milestone with phases, tasks, failing tests and acceptance criteria, so it "
               "is covered by the same gate as everything else rather than being a change nobody scheduled.",
    "tdd": {"red": "The coverage gate fails if anything this milestone claims is claimed nowhere, and the "
                   "rendered-document checker fails on a task with no status, no criteria or no failing test.",
            "green": "Author the milestone spine entry and its detail file.",
            "refactor": "Give the milestone its own module rather than a third one bolted onto a file whose "
                        "name says it holds two."},
    "traces": {"fr": ["FR-PLN-01", "FR-PLN-04"], "nfr": ["NFR-VAL-03"], "us": ["US-PLN-01"]},
    "criteria": [{"id": "M15-P4-T3-C1", "kind": "auto",
                  "text": "The coverage gate passes with the milestone in place.", "done": True},
                 {"id": "M15-P4-T3-C2", "kind": "auto",
                  "text": "Every task in the milestone states its failing test and its criteria.",
                  "done": True}]}]},

 {"id": "M15-P5", "title": "Proved against a browser, not against a description",
  "dependsOn": ["M15-P4"],
  "summary": "Drive both renderers in a real browser, and mutate the new rules to find out which of them no "
             "test would notice the loss of.",
  "completion": ["Every claim about arrival, folding, copying, linking and printing is one a browser reported.",
                 "Every mutation of the new rules is caught by a test, and every survivor is killed with one."],
  "tasks": [
   {"id": "M15-P5-T1", "title": "Both renderers driven in a real browser",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "validator",
    "testLayers": ["e2e", "a11y"], "dependsOn": [],
    "summary": "Open the published plan and a generated one in Chromium and read back what the engine "
               "computed: the arrival state, both levels of sibling closing, the deep link, the filter, the "
               "clipboard, print, and the width of the page on a phone.",
    "tdd": {"red": "The harness fails the class outright when it runs and goes wrong, rather than reporting a "
                   "crash as an absent browser.",
            "green": "Drive both sets and assert on what came back.",
            "refactor": "Serve the pages from one intercepted secure origin, since the clipboard does not "
                        "exist in an insecure context and a copy check that cannot read it proves nothing."},
    "traces": {"fr": ["FR-VAL-06", "FR-GEN-03"], "nfr": ["NFR-VAL-05"], "us": ["US-SPC-05", "US-VAL-01"]},
    "criteria": [{"id": "M15-P5-T1-C1", "kind": "auto",
                  "text": "Every behavioural claim in this milestone is checked in a real browser.",
                  "done": True},
                 {"id": "M15-P5-T1-C2", "kind": "auto",
                  "text": "A harness that runs and fails is reported as a failure, never as a skip.",
                  "done": True}]},
   {"id": "M15-P5-T2", "title": "The new rules are mutated",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "validator",
    "testLayers": ["unit"], "dependsOn": ["M15-P5-T1"],
    "summary": "Break each new rule on purpose — an accordion that opens instead of closing, a first-open "
               "applied to everything, a copy control that only exists when open, an index carrying entries, a "
               "print rule that drops the expansion — and find out which breakages no test notices.",
    "tdd": {"red": "A mutation that survives is a rule nothing defends.",
            "green": "Kill every survivor with a test.",
            "refactor": "Never weaken a mutation to make it pass."},
    "traces": {"fr": ["FR-VAL-06"], "nfr": ["NFR-VAL-03"], "us": ["US-VAL-01"]},
    "criteria": [{"id": "M15-P5-T2-C1", "kind": "auto",
                  "text": "Every mutation of the new rules is caught by a test.", "done": True}]}]},
]

}
