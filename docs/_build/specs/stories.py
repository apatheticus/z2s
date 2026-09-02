# -*- coding: utf-8 -*-
"""Zero-to-Ship — User stories, use cases and acceptance criteria (US-* / UC-*)."""

DOC = {
    "title": "Zero-to-Ship — User Stories & Use Cases",
    "slug": "stories",
    "kicker": "Acceptance basis",
    "type": "User stories, use cases & acceptance criteria",
    "version": "2.9",
    "status": "For development",
    "date": "2026-09-02",
    "owner": "Zerø Effort",
    "releaseScope": "v2 — the complete toolchain as the /zero:* skill chain",
    "summary": "Every functional requirement expressed as a goal-level story with testable acceptance criteria, "
               "plus the actor-centred use cases that span several stories. This is the basis on which the "
               "toolchain is verified.",
    "scopeNote": "This document does not restate the FSD or the SDD — it traces to them. Each scenario is a "
                 "Given/When/Then triple with a stable identifier; automated tests are named for that identifier, "
                 "so a failing test names the requirement it defends.",
}

ROLES = [
    {"name": "Specification author", "summary": "Turns intent into the document chain.",
     "can": "Run any document generator, answer the decision gate, amend by addendum."},
    {"name": "Planner", "summary": "Turns a stable specification into an executable plan.",
     "can": "Author the plan spine and milestone detail, run generation, resolve coverage failures."},
    {"name": "Operator", "summary": "Starts and supervises an autonomous run.",
     "can": "Kick off the orchestrator, clear human-gated work, sign off human-review criteria, promote a release."},
    {"name": "Worker", "summary": "An agent executing exactly one unit of work.",
     "can": "Read the plan and its brief, write code and tests, write status back, return a report."},
    {"name": "Reviewer", "summary": "Reads documents and diffs; approves promotion.",
     "can": "Filter, review-tick, deep-link, and read status history in version control."},
]

STORIES = [
    # ---- document chain ----
    {"id": "US-DOC-01", "title": "Generate a specification document from intent", "priority": "Must",
     "role": "Specification author", "testLayers": ["unit", "e2e"],
     "narrative": "As a **specification author** I want to turn a rough brief into a complete, structured "
                  "document, so that the project starts from something reviewable rather than a conversation.",
     "traces": {"fr": ["FR-DOC-01", "FR-DOC-04", "FR-DOC-07", "FR-DOC-08"], "nfr": ["NFR-ARC-01"]},
     "scenarios": [
         {"id": "US-DOC-01-S01", "title": "Rich source proceeds straight to authoring",
          "given": "a brief that already covers purpose, users, scope and constraints",
          "when": "the author runs the relevant document generator against it",
          "then": "the generator authors the document without an interview, and the produced file contains a "
                  "populated document-control block and at least one catalogue entry per declared area"},
         {"id": "US-DOC-01-S02", "title": "Thin source triggers the gate",
          "given": "a two-sentence brief with no stated users or scope",
          "when": "the author runs the generator",
          "then": "the generator asks its clarifying questions before authoring, one at a time, each with a "
                  "recommended default, and writes no file until every question is answered"},
         {"id": "US-DOC-01-S03", "title": "Gaps become open questions, not invention",
          "given": "a brief that never states a success metric",
          "when": "the document is generated",
          "then": "no metric is fabricated, and the omission appears in the document's open questions"},
     ],
     "verify": ["The document-control block states type, version, status, date, owner and scope.",
                "Sections with no content are absent from the rendered document, not present and empty."]},

    {"id": "US-DOC-02", "title": "Lock decisions before any file is written", "priority": "Must",
     "role": "Specification author", "testLayers": ["e2e", "manual"],
     "narrative": "As a **specification author** I want every fork resolved in one session up front, so that I am "
                  "not interrupted mid-build and the work never proceeds on a wrong assumption.",
     "traces": {"fr": ["FR-DOC-02", "FR-DOC-03", "FR-EXE-08"], "adr": ["ADR-10"]},
     "scenarios": [
         {"id": "US-DOC-02-S01", "title": "Gate precedes authoring",
          "given": "a generator invoked on a source with unresolved forks",
          "when": "the run begins",
          "then": "no file is created until the gate completes, and the run reports which forks it identified"},
         {"id": "US-DOC-02-S02", "title": "Decisions are written down",
          "given": "a completed gate",
          "when": "the generator proceeds",
          "then": "a locked-decisions table of decision, choice and rationale exists in both the document and the "
                  "run ledger before the first content section is authored"},
         {"id": "US-DOC-02-S03", "title": "A locked row is not re-asked",
          "given": "a locked-decisions table containing a resolved fork",
          "when": "a later stage of the same run encounters that fork",
          "then": "the recorded choice is applied without asking, and any contradiction with reality is surfaced "
                  "as a conflict rather than silently re-decided"},
     ]},

    {"id": "US-DOC-03", "title": "Keep functional and technical content separate", "priority": "Must",
     "role": "Specification author", "testLayers": ["unit", "manual"],
     "narrative": "As a **specification author** I want the functional document to stay free of technical "
                  "decisions, so that the two can be reviewed by different people and changed independently.",
     "traces": {"fr": ["FR-DOC-05"], "nfr": ["NFR-ARC-02"]},
     "scenarios": [
         {"id": "US-DOC-03-S01", "title": "Technical implication is deferred",
          "given": "a functional requirement that implies a storage choice",
          "when": "the functional document is authored",
          "then": "the requirement states observable behaviour only, and the storage question appears as an open "
                  "question for the technical document"},
     ]},

    # ---- embedding & rendering ----
    {"id": "US-SPC-01", "title": "One file, readable by people and machines", "priority": "Must",
     "role": "Reviewer", "testLayers": ["unit", "e2e"],
     "narrative": "As a **reviewer** I want to open a document straight from disk and read it, while a tool reads "
                  "the same facts as structured data, so that neither of us needs the other's toolchain.",
     "traces": {"fr": ["FR-SPC-01", "FR-SPC-02", "FR-SPC-03", "FR-SPC-04", "FR-DOC-06"],
                "adr": ["ADR-01", "ADR-02"]},
     "scenarios": [
         {"id": "US-SPC-01-S01", "title": "Opens with no build step",
          "given": "a generated document copied to a machine with no project checkout",
          "when": "it is opened directly from the filesystem",
          "then": "it renders completely, with no console error and no request beyond its web fonts"},
         {"id": "US-SPC-01-S02", "title": "Spec is extractable without executing the page",
          "given": "a generated document",
          "when": "a tool reads the embedded specification block",
          "then": "the block parses as a single valid JSON object carrying its own document type and schema version"},
         {"id": "US-SPC-01-S03", "title": "Prose and data cannot disagree",
          "given": "a document whose embedded specification is edited to change a requirement's title",
          "when": "the document is reloaded",
          "then": "the visible title changes to match, with no separate copy of the old title anywhere in the file"},
     ],
     "verify": ["No fact appears in the file outside the embedded specification.",
                "Copy and download actions return exactly the embedded specification."]},

    {"id": "US-SPC-02", "title": "Find one entry among hundreds", "priority": "Must",
     "role": "Reviewer", "testLayers": ["e2e", "a11y"],
     "narrative": "As a **reviewer** I want to narrow a long catalogue to the handful of entries I care about, so "
                  "that I can review a specific area without reading the whole document.",
     "traces": {"fr": ["FR-SPC-05", "FR-SPC-07", "FR-SPC-09", "FR-SPC-10"], "nfr": ["NFR-PRF-03"]},
     "scenarios": [
         {"id": "US-SPC-02-S01", "title": "Keyword narrows every catalogue",
          "given": "a document containing several catalogues",
          "when": "the reader types a term matching entries in two of them",
          "then": "only matching entries remain visible, groups with no remaining matches are hidden, and the "
                  "count of visible entries reflects the filter"},
         {"id": "US-SPC-02-S02", "title": "Priority toggles compose with keyword",
          "given": "an active keyword filter",
          "when": "the reader switches off one priority band",
          "then": "entries matching the keyword but in the disabled band disappear, and re-enabling the band "
                  "restores them"},
         {"id": "US-SPC-02-S03", "title": "No match is stated, not implied",
          "given": "any catalogue",
          "when": "the reader types a term matching nothing",
          "then": "a plain message states that nothing matched, rather than leaving an empty area"},
     ]},

    {"id": "US-SPC-03", "title": "Cite a single requirement", "priority": "Must",
     "role": "Reviewer", "testLayers": ["e2e"],
     "narrative": "As a **reviewer** I want to send someone a link to one requirement, so that a discussion "
                  "starts on the exact text rather than on a document name.",
     "traces": {"fr": ["FR-SPC-06", "FR-TRC-07"]},
     "scenarios": [
         {"id": "US-SPC-03-S01", "title": "Link opens and reveals the target",
          "given": "a link to an entry inside a collapsed group",
          "when": "the link is opened in a new window",
          "then": "the group expands, the entry scrolls into view, and it is visibly marked for a short moment"},
         {"id": "US-SPC-03-S02", "title": "Cross-document trace resolves",
          "given": "an entry tracing an identifier defined in a companion document",
          "when": "the reader follows that trace",
          "then": "the companion document opens at that identifier"},
     ]},

    {"id": "US-SPC-04", "title": "Track a review pass", "priority": "Should",
     "role": "Reviewer", "testLayers": ["e2e"],
     "narrative": "As a **reviewer** I want to mark entries as I read them and see how far I have got, so that I "
                  "can review a large document across several sittings.",
     "traces": {"fr": ["FR-SPC-08"], "nfr": ["NFR-GEN-07"]},
     "scenarios": [
         {"id": "US-SPC-04-S01", "title": "Progress persists across reloads",
          "given": "a reviewer who has marked several entries",
          "when": "the document is closed and reopened",
          "then": "the same entries are still marked and the progress figure is unchanged"},
         {"id": "US-SPC-04-S02", "title": "Documents do not share review state",
          "given": "two documents from different projects open in the same browser",
          "when": "entries are marked in one",
          "then": "the other document's progress is unaffected"},
         {"id": "US-SPC-04-S03", "title": "Review state is not part of the specification",
          "given": "a document with review marks",
          "when": "the specification is copied out",
          "then": "it contains no review state"},
     ]},

    {"id": "US-SPC-05", "title": "Move around a plan without scrolling through it",
     "priority": "Should", "role": "Operator", "testLayers": ["e2e", "a11y"],
     "narrative": "As an **operator** I want a plan to open on the work I am starting and let me reach any other "
                  "part of it directly, so that finding one task out of a hundred and twenty is not a scroll "
                  "through all of them.",
     "traces": {"fr": ["FR-SPC-09", "FR-SPC-10", "FR-SPC-11", "FR-EXE-15"], "nfr": ["NFR-UX-01"]},
     "verify": ["The same runtime, on a specification document, still opens every group on arrival — the "
                "collapsed default is opted into per section and never applied to a whole set."],
     "scenarios": [
         {"id": "US-SPC-05-S01", "title": "The plan opens on something readable",
          "given": "a plan of several milestones, phases and tasks",
          "when": "one of its documents is opened",
          "then": "the first unit at each level is open, every sibling is shut, and each open unit is the first "
                  "one of its own parent rather than the first one on the page"},
         {"id": "US-SPC-05-S02", "title": "Opening one closes the others beside it",
          "given": "a plan document with the first phase open",
          "when": "another phase is opened",
          "then": "the first phase closes, and the tasks open inside the other phases are left as they were"},
         {"id": "US-SPC-05-S03", "title": "A link into a shut unit still lands on it",
          "given": "a link to a task inside a phase that is not open",
          "when": "the link is followed",
          "then": "every level between the task and the page opens, the task is marked, and it is on screen"},
         {"id": "US-SPC-05-S04", "title": "Every part reaches every other part",
          "given": "a plan written across an index and one document per milestone",
          "when": "a reader arrives on any one of those documents",
          "then": "the document names every other part of the plan as a link and states the part in hand without "
                  "offering it as one"},
         {"id": "US-SPC-05-S05", "title": "A prompt is taken without being read",
          "given": "a unit whose execution instructions are collapsed",
          "when": "the copy control on the collapsed row is used",
          "then": "the instructions are on the clipboard, the row stays collapsed, and the control says so"},
         {"id": "US-SPC-05-S06", "title": "Paper gets what the screen folds away",
          "given": "a plan document printed",
          "when": "the printed output is inspected",
          "then": "every collapsed phase and task is expanded and only the execution instructions are dropped"},
     ]},

    # ---- traceability ----
    {"id": "US-TRC-01", "title": "Prove nothing was dropped", "priority": "Must",
     "role": "Planner", "testLayers": ["unit", "CI"],
     "narrative": "As a **planner** I want the build to fail when a requirement is scheduled nowhere, so that "
                  "scope loss is caught in minutes rather than at release.",
     "traces": {"fr": ["FR-TRC-04", "FR-TRC-05", "FR-TRC-06"], "adr": ["ADR-04"], "nfr": ["NFR-VAL-03"]},
     "scenarios": [
         {"id": "US-TRC-01-S01", "title": "Unclaimed requirement fails generation",
          "given": "a specification containing a requirement no task traces",
          "when": "the plan is generated",
          "then": "generation exits non-zero and names that requirement"},
         {"id": "US-TRC-01-S02", "title": "Explicit exclusion passes with a reason",
          "given": "a requirement recorded as deliberately excluded with a reason",
          "when": "the plan is generated",
          "then": "generation succeeds and the exclusion is listed alongside the coverage matrix"},
         {"id": "US-TRC-01-S03", "title": "Coverage cannot be downgraded",
          "given": "any configuration available to the operator",
          "when": "an uncovered requirement exists",
          "then": "no setting causes the failure to be reported as a warning"},
     ]},

    {"id": "US-TRC-02", "title": "Walk any task back to the problem", "priority": "Must",
     "role": "Reviewer", "testLayers": ["unit", "e2e"],
     "narrative": "As a **reviewer** I want to follow a task upward to the requirement, the story and the "
                  "capability behind it, so that I can judge whether it is worth doing.",
     "traces": {"fr": ["FR-TRC-03", "FR-TRC-07", "FR-TRC-08"], "nfr": ["NFR-DAT-08"]},
     "scenarios": [
         {"id": "US-TRC-02-S01", "title": "Every trace is a working link",
          "given": "any task in the plan",
          "when": "its traces are followed",
          "then": "each resolves to an existing entry in this or a companion document"},
         {"id": "US-TRC-02-S02", "title": "A dangling trace fails validation",
          "given": "a trace referencing an identifier that exists nowhere",
          "when": "validation runs",
          "then": "it exits non-zero and names the offending trace and its owner"},
     ]},

    {"id": "US-TRC-03", "title": "Keep identifiers valid forever", "priority": "Must",
     "role": "Specification author", "testLayers": ["unit"],
     "narrative": "As a **specification author** I want identifiers never to be reused or renumbered, so that "
                  "traces, test names and commit messages stay meaningful for the life of the project.",
     "traces": {"fr": ["FR-TRC-01", "FR-TRC-02", "FR-VAL-03"], "adr": ["ADR-03"]},
     "scenarios": [
         {"id": "US-TRC-03-S01", "title": "Duplicate identifier fails validation",
          "given": "two entries sharing an identifier",
          "when": "validation runs",
          "then": "it exits non-zero naming the duplicate"},
         {"id": "US-TRC-03-S02", "title": "Removal retires in place",
          "given": "a requirement dropped from scope",
          "when": "the document is regenerated",
          "then": "its identifier is still present, marked as retired with a reason, and no later entry has taken "
                  "its number"},
     ]},

    # ---- planning ----
    {"id": "US-PLN-01", "title": "Derive an executable plan", "priority": "Must",
     "role": "Planner", "testLayers": ["unit", "e2e"],
     "narrative": "As a **planner** I want the plan generated from the specifications rather than written "
                  "alongside them, so that the two cannot drift apart.",
     "traces": {"fr": ["FR-PLN-01", "FR-PLN-02", "FR-PLN-03", "FR-PLN-11", "FR-PLN-13"], "adr": ["ADR-04"],
                "nfr": ["NFR-ARC-06"]},
     "scenarios": [
         {"id": "US-PLN-01-S01", "title": "Generation reads the specifications directly",
          "given": "a specification whose requirement titles have changed",
          "when": "the plan is regenerated with no change to plan data",
          "then": "the plan's catalogue shows the new titles"},
         {"id": "US-PLN-01-S02", "title": "Dependency cycle is rejected",
          "given": "plan data in which two milestones depend on each other",
          "when": "generation runs",
          "then": "it exits non-zero naming the cycle, and writes no plan documents"},
         {"id": "US-PLN-01-S03", "title": "Unknown dependency is rejected",
          "given": "a task depending on an identifier that does not exist",
          "when": "generation runs",
          "then": "it exits non-zero naming the task and the missing dependency"},
     ]},

    {"id": "US-PLN-02", "title": "Define every task test-first", "priority": "Must",
     "role": "Planner", "testLayers": ["unit", "manual"],
     "narrative": "As a **planner** I want each task to state the failing test that proves it is needed, so that a "
                  "worker with no context can tell when the task is done.",
     "traces": {"fr": ["FR-PLN-04", "FR-PLN-05", "FR-PLN-06", "FR-PLN-10"], "adr": ["ADR-06"]},
     "scenarios": [
         {"id": "US-PLN-02-S01", "title": "Missing red step fails validation",
          "given": "a task with no stated failing test",
          "when": "the plan is validated",
          "then": "validation exits non-zero naming the task"},
         {"id": "US-PLN-02-S02", "title": "Every task has a machine-checkable criterion",
          "given": "any task without a documented exception",
          "when": "the plan is validated",
          "then": "validation requires at least one machine-checkable acceptance criterion"},
         {"id": "US-PLN-02-S03", "title": "Human-review criteria block the milestone, not the task",
          "given": "a task whose machine criteria all pass but which carries an open human-review criterion",
          "when": "status is rolled up",
          "then": "the task is not blocked, and the milestone cannot close"},
     ]},

    {"id": "US-PLN-03", "title": "Know what can run unattended", "priority": "Must",
     "role": "Planner", "testLayers": ["unit", "e2e"],
     "narrative": "As a **planner** I want each task classified by autonomy, so that an unattended run works "
                  "around human-gated work instead of stopping at it.",
     "traces": {"fr": ["FR-PLN-07", "FR-PLN-12"], "adr": ["ADR-07"], "nfr": ["NFR-SEC-03"]},
     "scenarios": [
         {"id": "US-PLN-03-S01", "title": "Human-gated work is excluded from the ready set",
          "given": "a plan containing human-gated tasks",
          "when": "the ready set is computed",
          "then": "no human-gated task appears in it, and each is listed on the prerequisite checklist"},
         {"id": "US-PLN-03-S02", "title": "Substituted-provider work names its substitute",
          "given": "a task that would otherwise call an external provider",
          "when": "the task is authored",
          "then": "the task names the specific substitution to use, rather than leaving it to the worker"},
     ]},

    {"id": "US-PLN-04", "title": "See what can run in parallel", "priority": "Must",
     "role": "Operator", "testLayers": ["unit", "e2e"],
     "narrative": "As an **operator** I want the plan to show which milestones can run at the same time, so that I "
                  "can judge the shape of the run before starting it.",
     "traces": {"fr": ["FR-PLN-09"], "adr": ["ADR-08"], "nfr": ["NFR-DAT-05"]},
     "scenarios": [
         {"id": "US-PLN-04-S01", "title": "Waves respect dependencies",
          "given": "any generated plan",
          "when": "the wave ordering is inspected",
          "then": "every milestone in a wave depends only on milestones in earlier waves"},
         {"id": "US-PLN-04-S02", "title": "Waves are derived, not authored",
          "given": "plan data with no wave information",
          "when": "the plan is generated",
          "then": "the wave ordering appears in the plan index and changes automatically when a dependency changes"},
     ]},

    # ---- validation ----
    {"id": "US-VAL-01", "title": "Validate the file that ships", "priority": "Must",
     "role": "Planner", "testLayers": ["unit", "CI"],
     "narrative": "As a **planner** I want validation to check the produced document rather than the data it came "
                  "from, so that a generator regression cannot ship silently.",
     "traces": {"fr": ["FR-VAL-02", "FR-VAL-04", "FR-VAL-05", "FR-VAL-06", "FR-VAL-08"], "adr": ["ADR-09"],
                "nfr": ["NFR-VAL-02"]},
     "scenarios": [
         {"id": "US-VAL-01-S01", "title": "Corrupt output is caught",
          "given": "a generated document whose embedded specification has been truncated",
          "when": "validation runs",
          "then": "it exits non-zero naming the file and the parse failure"},
         {"id": "US-VAL-01-S02", "title": "Every failure is reported in one pass",
          "given": "a document set containing several distinct violations",
          "when": "validation runs once",
          "then": "all violations are listed together, grouped by document"},
         {"id": "US-VAL-01-S03", "title": "Warnings never fail the build",
          "given": "a documented exception that raises a warning",
          "when": "validation runs with no other issue",
          "then": "the warning is printed and the exit status is success"},
     ]},

    {"id": "US-VAL-02", "title": "Never claim a check that did not run", "priority": "Must",
     "role": "Operator", "testLayers": ["unit", "manual"],
     "narrative": "As an **operator** I want a skipped check reported as skipped, so that a green summary means "
                  "what it says.",
     "traces": {"fr": ["FR-VAL-07", "FR-GEN-03"], "nfr": ["NFR-VAL-05"]},
     "scenarios": [
         {"id": "US-VAL-02-S01", "title": "Absent browser is reported, not assumed",
          "given": "an environment with no browser available",
          "when": "the rendered-view check is requested",
          "then": "the run states that the check was skipped and why, and the summary does not count it as passed"},
     ]},

    # ---- execution ----
    {"id": "US-EXE-01", "title": "Run the plan unattended", "priority": "Must",
     "role": "Operator", "testLayers": ["e2e", "manual"],
     "narrative": "As an **operator** I want to start the run and walk away, so that work proceeds without me "
                  "answering questions.",
     "traces": {"fr": ["FR-EXE-01", "FR-EXE-02", "FR-EXE-03", "FR-EXE-05", "FR-EXE-08", "FR-EXE-13",
                       "FR-GEN-04"], "adr": ["ADR-08", "ADR-10"]},
     "scenarios": [
         {"id": "US-EXE-01-S01", "title": "Wave order is respected",
          "given": "a plan with three waves",
          "when": "the run executes",
          "then": "no milestone from a later wave starts before every milestone it depends on has completed"},
         {"id": "US-EXE-01-S02", "title": "The run never asks",
          "given": "an ambiguity encountered mid-run",
          "when": "a worker meets it",
          "then": "the worker makes a reasonable call, records it as a decision with its rationale in the ledger, "
                  "and continues without prompting the operator"},
         {"id": "US-EXE-01-S03", "title": "Briefs are self-contained",
          "given": "a worker started with no inherited context",
          "when": "it reads only its brief",
          "then": "it can locate the plan, the locked decisions, the verification gauntlet and the report contract "
                  "without asking for more"},
     ],
     "verify": ["No unattended unit opens an interactive prompt or uses a live credential."]},

    {"id": "US-EXE-02", "title": "Build each task test-first", "priority": "Must",
     "role": "Worker", "testLayers": ["unit", "e2e"],
     "narrative": "As a **worker** I want to write the failing test before the implementation, so that passing is "
                  "evidence rather than opinion.",
     "traces": {"fr": ["FR-EXE-04", "FR-TRC-09"], "adr": ["ADR-06"]},
     "scenarios": [
         {"id": "US-EXE-02-S01", "title": "Red before green",
          "given": "a task with a stated failing test",
          "when": "the worker begins",
          "then": "the test is written first and observed to fail before any implementation is written"},
         {"id": "US-EXE-02-S02", "title": "Test names carry the identifier",
          "given": "a scenario identifier in the acceptance basis",
          "when": "its test is written",
          "then": "the test name contains that identifier"},
     ]},

    {"id": "US-EXE-03", "title": "Survive an interruption", "priority": "Must",
     "role": "Operator", "testLayers": ["e2e"],
     "narrative": "As an **operator** I want a run to resume where it stopped after a crash or a restart, so that "
                  "an interruption costs one unit of work rather than the whole run.",
     "traces": {"fr": ["FR-EXE-09", "FR-LRN-05"], "adr": ["ADR-15"], "nfr": ["NFR-EXE-01", "NFR-EXE-07"]},
     "scenarios": [
         {"id": "US-EXE-03-S01", "title": "Resume recomputes rather than remembers",
          "given": "a run killed mid-wave",
          "when": "it is restarted",
          "then": "it reads the ledger, recomputes the ready set from the plan, and repeats no completed unit"},
         {"id": "US-EXE-03-S02", "title": "Ledger is written before advancing",
          "given": "a completed unit",
          "when": "the orchestrator moves on",
          "then": "the ledger already records that unit's done-state and the exact next step"},
     ]},

    {"id": "US-EXE-04", "title": "Keep going when one unit is stuck", "priority": "Must",
     "role": "Operator", "testLayers": ["e2e"],
     "narrative": "As an **operator** I want a stuck unit to record why and step aside, so that one problem does "
                  "not idle the whole run.",
     "traces": {"fr": ["FR-EXE-07"], "nfr": ["NFR-EXE-05"]},
     "scenarios": [
         {"id": "US-EXE-04-S01", "title": "Bounded retries then blocked",
          "given": "a unit failing repeatedly",
          "when": "the stated attempt limit is reached",
          "then": "the unit is marked blocked with the blocker and the workaround recorded, and the run continues "
                  "with the next ready unit"},
         {"id": "US-EXE-04-S02", "title": "Blocked units are re-evaluated",
          "given": "a unit blocked on a dependency",
          "when": "that dependency later passes",
          "then": "the blocked unit becomes eligible again without operator action"},
     ]},

    {"id": "US-EXE-05", "title": "Never collide on the same files", "priority": "Must",
     "role": "Operator", "testLayers": ["unit", "e2e"],
     "narrative": "As an **operator** I want concurrent work isolated, so that parallelism does not corrupt the "
                  "work it was meant to accelerate.",
     "traces": {"fr": ["FR-EXE-06"], "nfr": ["NFR-EXE-03"], "adr": ["ADR-08"]},
     "scenarios": [
         {"id": "US-EXE-05-S01", "title": "Overlapping write sets are serialised",
          "given": "two ready units that write the same file",
          "when": "dispatch is computed",
          "then": "they are not dispatched together"},
         {"id": "US-EXE-05-S02", "title": "Contention is reported, not retried blindly",
          "given": "an edit that fails because another worker changed the file",
          "when": "the worker retries once and fails again",
          "then": "it reports contention rather than continuing to retry"},
     ]},

    {"id": "US-EXE-06", "title": "Get an honest report from every worker", "priority": "Should",
     "role": "Operator", "testLayers": ["e2e"],
     "narrative": "As an **operator** I want every worker to report what it actually did and verified, so that I "
                  "can trust the run without re-deriving it.",
     "traces": {"fr": ["FR-EXE-10", "FR-GEN-03"], "adr": ["ADR-13"], "nfr": ["NFR-EXE-06"]},
     "scenarios": [
         {"id": "US-EXE-06-S01", "title": "Silence is failure",
          "given": "a worker that finishes without returning a report",
          "when": "the orchestrator collects results",
          "then": "the unit is treated as failed and is not marked complete"},
         {"id": "US-EXE-06-S02", "title": "Reports name their evidence",
          "given": "a report claiming verification passed",
          "when": "it is read",
          "then": "it names the command that produced the result rather than asserting success"},
     ]},

    {"id": "US-EXE-07", "title": "Have someone else check the work", "priority": "Must",
     "role": "Operator", "testLayers": ["unit", "e2e"],
     "narrative": "As an **operator** I want finished work judged by a worker that did not do it and cannot see "
                  "how it was done, so that nothing passes on its own author's say-so.",
     "traces": {"fr": ["FR-EXE-14"], "adr": ["ADR-13"], "nfr": ["NFR-EXE-06"]},
     "scenarios": [
         {"id": "US-EXE-07-S01", "title": "The judge never sees the builder's account",
          "given": "a finished unit and the report its builder returned",
          "when": "the judgement brief is assembled",
          "then": "it carries the acceptance criteria, the verification gauntlet and the work itself, and none of "
                  "the builder's own account of it"},
         {"id": "US-EXE-07-S02", "title": "A failure names one gap",
          "given": "work that does not meet its criteria",
          "when": "the judgement is returned",
          "then": "it names the single largest remaining gap rather than a list, and that gap briefs the retry"},
         {"id": "US-EXE-07-S03", "title": "A judgement that could not look is a failure",
          "given": "a judge that cannot inspect the work",
          "when": "it reports",
          "then": "the unit fails rather than passing unexamined"},
     ]},

    {"id": "US-EXE-08", "title": "Hand over exactly as much work as I mean to", "priority": "Must",
     "role": "Operator", "testLayers": ["unit", "e2e"],
     "narrative": "As an **operator** I want the instructions for one task, one phase, one milestone or the whole "
                  "build, each on its own card and each copyable on its own, so that I decide how much I hand "
                  "over rather than the document deciding for me.",
     "traces": {"fr": ["FR-EXE-15", "FR-EXE-03"], "nfr": ["NFR-UX-04"]},
     "scenarios": [
         {"id": "US-EXE-08-S01", "title": "The instructions are on the card they belong to",
          "given": "a generated plan open in a browser",
          "when": "a task is found in the catalogue",
          "then": "its own instructions are the first thing inside its card, folded shut, with a copy button"},
         {"id": "US-EXE-08-S02", "title": "Four granularities, four buttons",
          "given": "a milestone document",
          "when": "its phases and tasks are read",
          "then": "the milestone, each phase and each task each offer their own instructions to copy"},
         {"id": "US-EXE-08-S03", "title": "Folded shut until asked for",
          "given": "a document carrying many sets of instructions",
          "when": "it is opened",
          "then": "every one of them is closed, so the plan is what the page shows"},
     ]},

    {"id": "US-EXE-09", "title": "Get work that keeps going until it is actually good", "priority": "Must",
     "role": "Operator", "testLayers": ["unit", "e2e"],
     "narrative": "As an **operator** I want a pasted prompt to run the same builder-and-critic loop the "
                  "orchestrator runs, aiming above the acceptance criteria rather than stopping the moment the "
                  "boxes tick, so that handing work over by hand is not a weaker way of doing it.",
     "traces": {"fr": ["FR-EXE-16", "FR-EXE-14", "FR-EXE-02"], "adr": ["ADR-13"],
                "nfr": ["NFR-SEC-04"]},
     "scenarios": [
         {"id": "US-EXE-09-S01", "title": "The work is split by whoever runs it",
          "given": "the instructions for one task",
          "when": "they are read",
          "then": "they ask for the split to be decided by the reader and name no pieces themselves"},
         {"id": "US-EXE-09-S02", "title": "Nothing grades its own work",
          "given": "a piece somebody has built",
          "when": "it is judged",
          "then": "the judge is a fresh reader who did not build it and is shown the work rather than an account "
                  "of it, and a new one judges every retry"},
         {"id": "US-EXE-09-S03", "title": "A higher target that nobody invented",
          "given": "a unit that traces to a requirement, a story and a numbered target",
          "when": "its instructions are generated",
          "then": "those are named as what the work is aiming at, and a unit that traces to nothing is told "
                  "plainly that it has no higher target rather than being given one"},
         {"id": "US-EXE-09-S04", "title": "What it waits on comes first",
          "given": "a task that depends on another",
          "when": "its instructions are read",
          "then": "the dependency is named before the contract, with the instruction to check it is passing "
                  "before starting"},
         {"id": "US-EXE-09-S05", "title": "The stops outrank the loop",
          "given": "instructions that say to keep going",
          "when": "they are read to the end",
          "then": "they name the operations no unit may perform and state that the loop can never approve a "
                  "sign-off, a deploy, a send or a spend"},
     ]},

    {"id": "US-EXE-10", "title": "Stop paying twice for work the run threw away", "priority": "Must",
     "role": "Operator", "testLayers": ["unit", "e2e"],
     "narrative": "As an **operator** I want a run to hand a finished dispatch its own mistake back instead of "
                  "discarding it and briefing somebody new from nothing, and to run the cheap checks before the "
                  "expensive ones, so that the hours I pay for go on building rather than on rebuilding.",
     "traces": {"fr": ["FR-EXE-17", "FR-EXE-20"], "nfr": ["NFR-EXE-12", "NFR-EXE-04"]},
     "scenarios": [
         {"id": "US-EXE-10-S01", "title": "A brief names the checks the unit never asked for",
          "given": "a project whose gauntlet covers the whole repository",
          "when": "a unit that names only some of those layers is briefed",
          "then": "the brief names the rest and their commands, and says the run will run them before the "
                  "dispatch is settled"},
         {"id": "US-EXE-10-S02", "title": "A broken guard goes back to whoever broke it",
          "given": "a worker that has finished and left a whole-repository check failing",
          "when": "the run settles the dispatch",
          "then": "the same worker is asked once, in the dispatch it already worked in, and what it changes is "
                  "committed with the unit rather than lost with a discarded attempt"},
         {"id": "US-EXE-10-S03", "title": "The cheap check that was going to fail goes first",
          "given": "a unit whose gauntlet holds both a static check and an end-to-end suite",
          "when": "the static check fails",
          "then": "the verdict is reached without the end-to-end suite having run at all"},
         {"id": "US-EXE-10-S04", "title": "A failure somebody else caused is somebody else's",
          "given": "a layer that was already failing before the unit was dispatched",
          "when": "the unit's gauntlet fails on it",
          "then": "the unit is charged no attempt and the run says which layer it inherited"},
     ]},
    {"id": "US-EXE-11", "title": "Not lose three units to a bad afternoon on the host", "priority": "Must",
     "role": "Operator", "testLayers": ["unit"],
     "narrative": "As an **operator** I want a run that cannot start a worker to wait and then stop, rather than "
                  "spending three units' budgets in five seconds, and I want to widen a wrong write set without "
                  "regenerating the plan, so that a problem outside the plan is not paid for out of it.",
     "traces": {"fr": ["FR-EXE-18", "FR-EXE-19"], "nfr": ["NFR-EXE-05", "NFR-EXE-03"], "adr": ["ADR-15"]},
     "scenarios": [
         {"id": "US-EXE-11-S01", "title": "A wait between one failure to start and the next",
          "given": "a host on which no worker can be launched",
          "when": "dispatches fail one after another",
          "then": "each wait is longer than the last, and no unit is charged an attempt for any of them"},
         {"id": "US-EXE-11-S02", "title": "A run that stops instead of spinning",
          "given": "a stated number of consecutive dispatches that never started",
          "when": "that number is reached",
          "then": "the run settles what is still in flight, dispatches nothing further and says why"},
         {"id": "US-EXE-11-S03", "title": "A write set corrected without stopping the run",
          "given": "two units the plan declares disjoint that are not",
          "when": "the operator adds the shared path to one of them in the run state",
          "then": "the next scheduling decision keeps them apart, no plan document is regenerated, and the run "
                  "records which correction it acted on"},
     ]},

    # ---- status ----
    {"id": "US-STA-01", "title": "See progress at a glance", "priority": "Must",
     "role": "Operator", "testLayers": ["e2e"],
     "narrative": "As an **operator** I want to open one file and see where the build is, so that I do not have to "
                  "assemble the picture from logs.",
     "traces": {"fr": ["FR-STA-01", "FR-STA-02", "FR-STA-04", "FR-STA-07", "FR-STA-08"], "adr": ["ADR-05"]},
     "scenarios": [
         {"id": "US-STA-01-S01", "title": "Rollup without opening every unit",
          "given": "a plan mid-run",
          "when": "the index is opened",
          "then": "milestone-level status and completed-task counts are visible without expanding anything"},
         {"id": "US-STA-01-S02", "title": "Criterion detail is available on demand",
          "given": "a task in progress",
          "when": "it is expanded",
          "then": "each acceptance criterion shows whether it is satisfied"},
     ]},

    {"id": "US-STA-02", "title": "Record progress without hand-editing", "priority": "Must",
     "role": "Worker", "testLayers": ["unit"],
     "narrative": "As a **worker** I want a command that flips status and ticks criteria, so that recording "
                  "progress cannot corrupt the document.",
     "traces": {"fr": ["FR-STA-03", "FR-STA-06"], "adr": ["ADR-05"]},
     "scenarios": [
         {"id": "US-STA-02-S01", "title": "Only the specification block changes",
          "given": "a plan document",
          "when": "a task's status is written back",
          "then": "the file differs only inside the embedded specification block"},
         {"id": "US-STA-02-S02", "title": "Invalid status is rejected",
          "given": "a status value outside the closed enumeration",
          "when": "write-back is attempted",
          "then": "it fails without modifying the file"},
         {"id": "US-STA-02-S03", "title": "Unknown task is rejected",
          "given": "an identifier not present in the plan",
          "when": "write-back is attempted",
          "then": "it fails naming the identifier, without modifying the file"},
     ]},

    {"id": "US-STA-03", "title": "Read progress as history", "priority": "Must",
     "role": "Reviewer", "testLayers": ["CI", "manual"],
     "narrative": "As a **reviewer** I want progress to appear in version-control history, so that how the project "
                  "went is recoverable later.",
     "traces": {"fr": ["FR-STA-05", "FR-EXE-11", "FR-GEN-07"], "adr": ["ADR-11"], "nfr": ["NFR-GEN-01"]},
     "scenarios": [
         {"id": "US-STA-03-S01", "title": "Status changes are committed with the work",
          "given": "a completed unit",
          "when": "it is committed",
          "then": "the commit contains both the implementation and the plan document status change, and names the "
                  "unit identifier"},
         {"id": "US-STA-03-S02", "title": "Regeneration produces no spurious diff",
          "given": "an unchanged plan",
          "when": "generation is re-run",
          "then": "no file changes"},
     ]},

    # ---- learning & amendment ----
    {"id": "US-LRN-01", "title": "Make later work cheaper than earlier work", "priority": "Must",
     "role": "Worker", "testLayers": ["manual"],
     "narrative": "As a **worker** I want the lessons of earlier milestones before I start, so that I do not pay "
                  "again for a problem already solved.",
     "traces": {"fr": ["FR-LRN-01", "FR-LRN-02", "FR-LRN-03", "FR-LRN-04"], "adr": ["ADR-14"]},
     "scenarios": [
         {"id": "US-LRN-01-S01", "title": "Retrospective written at close",
          "given": "a milestone reaching its exit criteria",
          "when": "it closes",
          "then": "a retrospective exists recording what was learned and what the next milestone should do "
                  "differently"},
         {"id": "US-LRN-01-S02", "title": "Prior retrospectives are read first",
          "given": "a worker starting a later milestone",
          "when": "its brief is assembled",
          "then": "the brief requires reading every prior retrospective before writing code"},
     ]},

    {"id": "US-AMD-01", "title": "Add scope without breaking what shipped", "priority": "Must",
     "role": "Specification author", "testLayers": ["unit", "e2e"],
     "narrative": "As a **specification author** I want to extend a stable specification by addendum, so that new "
                  "scope costs nothing in existing traces.",
     "traces": {"fr": ["FR-AMD-01", "FR-AMD-02", "FR-AMD-03", "FR-AMD-05"], "adr": ["ADR-12"],
                "nfr": ["NFR-EVO-03"]},
     "scenarios": [
         {"id": "US-AMD-01-S01", "title": "Addendum identifiers join the coverage universe",
          "given": "an addendum specification with its own prefix",
          "when": "the plan is generated",
          "then": "its requirements appear in the coverage matrix and must be claimed like any other"},
         {"id": "US-AMD-01-S02", "title": "Absent addendum degrades cleanly",
          "given": "a plan referencing an addendum file that is not present",
          "when": "generation runs",
          "then": "it succeeds, producing the core plan unchanged, and reports the absence"},
         {"id": "US-AMD-01-S03", "title": "Trace links route to the owning document",
          "given": "a task tracing an addendum identifier",
          "when": "the trace is followed",
          "then": "it opens the addendum that defines it, not the core specification"},
     ]},

    {"id": "US-GEN-01", "title": "Look like the product it describes", "priority": "Should",
     "role": "Reviewer", "testLayers": ["e2e", "a11y"],
     "narrative": "As a **reviewer** I want documents styled with the project's own design system, so that they "
                  "read as part of the work rather than as external paperwork.",
     "traces": {"fr": ["FR-GEN-02", "FR-GEN-05", "FR-GEN-06"], "adr": ["ADR-16"],
                "nfr": ["NFR-GEN-03", "NFR-UX-01"]},
     "scenarios": [
         {"id": "US-GEN-01-S01", "title": "Host tokens are adopted",
          "given": "a project declaring a design system",
          "when": "a document is generated",
          "then": "its styling references that system's tokens and hard-codes no colour or font outside the token "
                  "block"},
         {"id": "US-GEN-01-S02", "title": "Neutral fallback when none exists",
          "given": "a project with no declared design system",
          "when": "a document is generated",
          "then": "the neutral theme is used and the run says so"},
         {"id": "US-GEN-01-S03", "title": "Reduced motion is respected",
          "given": "a reader who prefers reduced motion",
          "when": "the document is opened",
          "then": "no animation plays"},
     ]},

    {"id": "US-GEN-03", "title": "See what the documents are styled with, and correct it", "priority": "Must",
     "role": "Reviewer", "testLayers": ["unit", "e2e"],
     "narrative": "As a **reviewer** I want the design the documents adopted written down, with every value "
                  "naming where it was read from, so that I can tell a right match from a wrong one and fix the "
                  "wrong one in a line.",
     "traces": {"fr": ["FR-GEN-11", "FR-GEN-02", "FR-GEN-03"], "adr": ["ADR-16"],
                "nfr": ["NFR-DAT-05", "NFR-GEN-05"]},
     "scenarios": [
         {"id": "US-GEN-03-S01", "title": "Every adopted value names its origin",
          "given": "a project whose design system was read from several files",
          "when": "the record is opened",
          "then": "each value names the file and the name it was read from"},
         {"id": "US-GEN-03-S02", "title": "A correction outranks what was found",
          "given": "a reviewer who has recorded a value by hand",
          "when": "the design is read again",
          "then": "their value is used and is carried through unchanged"},
         {"id": "US-GEN-03-S03", "title": "A source that has moved on is reported",
          "given": "a record whose source file has since changed",
          "when": "a document is generated",
          "then": "the record is still used and the run says which file has changed"},
         {"id": "US-GEN-03-S04", "title": "A value that cannot be written is named",
          "given": "a host value that would close the style block or fetch from elsewhere",
          "when": "the design is read",
          "then": "the value is refused, the neutral value is used in its place, and the refusal names the file "
                  "and the reason"},
     ]},
    {"id": "US-GEN-02", "title": "Explain the work to people who will not read the specification",
     "priority": "Could", "role": "Specification author", "testLayers": ["unit", "manual"],
     "narrative": "As a **specification author** I want a narrative briefing derived from the document set, so "
                  "that stakeholders who will never open a specification still understand what is being built and "
                  "why.",
     "traces": {"fr": ["FR-DOC-09", "FR-GEN-08", "FR-GEN-05"], "nfr": ["NFR-UX-06"]},
     "scenarios": [
         {"id": "US-GEN-02-S01", "title": "The briefing is derived, not written separately",
          "given": "a document set and a generated briefing",
          "when": "a capability is changed in the source documents and the briefing is regenerated",
          "then": "the briefing reflects the change, with no second copy of the fact maintained by hand"},
         {"id": "US-GEN-02-S02", "title": "The method documents itself",
          "given": "the toolchain and the method's own specification set",
          "when": "the set is regenerated by the toolchain",
          "then": "every gate passes against it and no committed file differs, so a toolchain defect would be "
                  "visible in the method's own artefacts"},
     ],
     "verify": ["The briefing contains no term a non-specialist reader would have to look up."]},

    {"id": "US-GEN-04", "title": "Keep each piece of work in its own place", "priority": "Must",
     "role": "Operator", "testLayers": ["unit", "integration"],
     "narrative": "As an **operator** I want each piece of work to have its own specifications, plan and run "
                  "state under the project's shared intent and vocabulary, so that a second capability does "
                  "not have to be appended to the set that described the first.",
     "traces": {"fr": ["FR-GEN-12"], "adr": ["ADR-19"], "nfr": ["NFR-OPS-01"]},
     "scenarios": [
         {"id": "US-GEN-04-S01", "title": "A feature holds its own chain, plan and run state",
          "given": "a project with a feature open",
          "when": "a generator, the plan or the run resolves where it writes",
          "then": "the specifications, the plan and the ledger resolve inside that feature, and the shared "
                  "vocabulary, worker configuration and design record resolve above it"},
         {"id": "US-GEN-04-S02", "title": "Which feature is current is derived, never stored",
          "given": "several feature directories on disk",
          "when": "any tool asks which one is current",
          "then": "the highest-numbered directory is the answer, read from the listing, with no file recording "
                  "it and no argument selecting it"},
         {"id": "US-GEN-04-S03", "title": "A feature is proved on its own",
          "given": "a feature whose requirements are claimed by its own plan",
          "when": "coverage is proved",
          "then": "only that feature's identifiers are in the universe, and nothing in another feature is "
                  "scanned or required"},
         {"id": "US-GEN-04-S04", "title": "A project that has opened none is unchanged",
          "given": "a project with no features directory",
          "when": "the whole set is regenerated",
          "then": "every path resolves as it did before and not one byte of any document differs"},
     ]},

    {"id": "US-GEN-05", "title": "Work on one thing at a time", "priority": "Must",
     "role": "Operator", "testLayers": ["unit", "integration"],
     "narrative": "As an **operator** I want the method to refuse a second open piece of work, so that there "
                  "is never a question about which plan a run is reading or where a document belongs.",
     "traces": {"fr": ["FR-GEN-13"], "adr": ["ADR-19"]},
     "scenarios": [
         {"id": "US-GEN-05-S01", "title": "A second open feature is refused",
          "given": "a project with a feature already open",
          "when": "another is opened",
          "then": "the attempt is refused, the open one is named, and nothing is created"},
         {"id": "US-GEN-05-S02", "title": "A closed feature is not written into",
          "given": "a feature that has been closed",
          "when": "a generator is asked to write into it",
          "then": "it refuses in the same voice a missing prerequisite is refused in, naming the close"},
         {"id": "US-GEN-05-S03", "title": "Something small folds into the open one",
          "given": "a fix that arrives while a feature is open",
          "when": "it is specified",
          "then": "it becomes an addendum inside that feature, and no second feature is opened"},
     ]},

    {"id": "US-GEN-06", "title": "Close a piece of work knowing what was left", "priority": "Must",
     "role": "Operator", "testLayers": ["unit", "integration"],
     "narrative": "As an **operator** I want closing a piece of work to audit it first, so that a clean close "
                  "means something and an unfinished one records exactly what was parked.",
     "traces": {"fr": ["FR-GEN-14"], "adr": ["ADR-19"], "nfr": ["NFR-EVO-01"]},
     "scenarios": [
         {"id": "US-GEN-06-S01", "title": "A close with no reason needs a clean audit",
          "given": "a feature with a unit not passing, a question unanswered or work uncommitted",
          "when": "it is closed with no reason given",
          "then": "the close is refused and every finding is listed, one per line, saying what it is about"},
         {"id": "US-GEN-06-S02", "title": "A close with a reason records what was left",
          "given": "the same feature",
          "when": "it is closed with a reason",
          "then": "the close succeeds and the date, the reason and every finding are written into that "
                  "feature's own first document"},
         {"id": "US-GEN-06-S03", "title": "A clean feature closes with no findings",
          "given": "a feature whose plan is passing, whose questions are answered and whose work is committed",
          "when": "it is closed with no reason given",
          "then": "the close succeeds and records that it completed, with nothing left"},
         {"id": "US-GEN-06-S04", "title": "The closed document is still a generated document",
          "given": "a feature just closed",
          "when": "its first document is regenerated",
          "then": "the file is byte-identical to the one the close wrote"},
     ]},

    # ---- context & ubiquitous language ----
    {"id": "US-CTX-01", "title": "Derive the shared vocabulary from the intent", "priority": "Must",
     "role": "Specification author", "testLayers": ["unit", "e2e"],
     "narrative": "As a **specification author** I want the project's vocabulary harvested from the intent and "
                  "its sources rather than invented, so that the glossary speaks the customer's words and every "
                  "later document can rely on it.",
     "traces": {"fr": ["FR-CTX-01", "FR-CTX-02", "FR-DOC-10"]},
     "scenarios": [
         {"id": "US-CTX-01-S01", "title": "Context requires a completed intent",
          "given": "a repository with no completed intent document",
          "when": "the context generator is invoked",
          "then": "it refuses to run, names the missing intent, and writes nothing"},
         {"id": "US-CTX-01-S02", "title": "Terms come from the sources",
          "given": "a completed intent with a populated source register",
          "when": "the context document is generated",
          "then": "every glossary term is traceable to the intent or a registered source, and any term the "
                  "generator could not source appears as an open question, not an entry"},
         {"id": "US-CTX-01-S03", "title": "One definition per term",
          "given": "a generated context document",
          "when": "its glossary is validated",
          "then": "each term carries exactly one definition, its synonyms are recorded, and exactly one term "
                  "per concept is marked canonical"},
     ],
     "verify": ["The source register travels with the document set and names what each source contributed."]},

    {"id": "US-CTX-02", "title": "Scope colliding meanings to bounded contexts", "priority": "Must",
     "role": "Specification author", "testLayers": ["e2e", "manual"],
     "narrative": "As a **specification author** I want a word that means two things split by context rather "
                  "than fudged, so that a requirement's meaning never depends on who is reading it.",
     "traces": {"fr": ["FR-CTX-03", "FR-CTX-04", "FR-CTX-06"]},
     "scenarios": [
         {"id": "US-CTX-02-S01", "title": "A collision triggers the interview",
          "given": "harvested vocabulary in which one term is used with two incompatible meanings",
          "when": "the context generator reaches that term",
          "then": "it asks the operator through the clarification interview — with a recommended resolution — "
                  "and records the outcome, rather than picking a meaning silently"},
         {"id": "US-CTX-02-S02", "title": "Boundary shifts are visible",
          "given": "a term whose meaning legitimately differs between two bounded contexts",
          "when": "the context document is generated",
          "then": "the term's entry states both scoped meanings and the context map shows the boundary it "
                  "crosses"},
     ]},

    {"id": "US-CTX-03", "title": "Make every later document speak the language", "priority": "Must",
     "role": "Specification author", "testLayers": ["unit", "integration"],
     "narrative": "As a **specification author** I want downstream generators to consult the glossary, so that "
                  "the requirements, stories, plan and tests all use one vocabulary.",
     "traces": {"fr": ["FR-CTX-05"]},
     "scenarios": [
         {"id": "US-CTX-03-S01", "title": "Downstream generators consult the glossary",
          "given": "a completed context document and a downstream generator producing a document",
          "when": "the downstream document is generated",
          "then": "it uses canonical terms where the glossary defines them, and no retired synonym appears"},
         {"id": "US-CTX-03-S02", "title": "A missing term flows back, forward-only",
          "given": "a downstream document that needs a term the glossary lacks",
          "when": "the generator encounters it",
          "then": "the term is added to the context document as a forward-only amendment and then used — never "
                  "defined locally in the downstream document"},
     ]},

    # ---- skill-chain interface ----
    {"id": "US-SKL-01", "title": "Drive the whole method through named commands", "priority": "Must",
     "role": "Operator", "testLayers": ["e2e"],
     "narrative": "As an **operator** I want each step of the method to be one named skill I invoke "
                  "deliberately, so that nothing generates, regenerates or ships unless I asked for it.",
     "traces": {"fr": ["FR-SKL-01", "FR-SKL-02", "FR-SKL-03"]},
     "scenarios": [
         {"id": "US-SKL-01-S01", "title": "Each step has a named entry point",
          "given": "the skill chain is installed",
          "when": "the operator lists available skills",
          "then": "one skill exists per document type, plus init, resume, build, update, ship and "
                  "clarification, each invocable by name"},
         {"id": "US-SKL-01-S02", "title": "Prerequisites are enforced by refusal",
          "given": "a repository whose product requirements document does not exist",
          "when": "the functional-specification skill is invoked",
          "then": "it refuses to run, names the missing prerequisite document, and changes nothing"},
         {"id": "US-SKL-01-S03", "title": "No skill fires on its own",
          "given": "an agent session in which the operator asks an unrelated question",
          "when": "the session proceeds",
          "then": "no chain skill triggers automatically; only the clarification skill may fire unprompted, "
                  "and only when a decision would otherwise be guessed"},
     ]},

    {"id": "US-SKL-02", "title": "Answer questions once, through one interview", "priority": "Must",
     "role": "Operator", "testLayers": ["e2e", "manual"],
     "narrative": "As an **operator** I want every skill's questions to arrive through the same interviewing "
                  "skill — numbered, batched into rounds, each with a recommended answer — so that being "
                  "questioned is predictable and never becomes a mid-build interruption.",
     "traces": {"fr": ["FR-SKL-04", "FR-CTX-04", "FR-DOC-02"]},
     "scenarios": [
         {"id": "US-SKL-02-S01", "title": "All questions flow through the shared skill",
          "given": "any chain skill that reaches a decision it cannot make",
          "when": "it needs the operator's answer",
          "then": "the question arrives through the clarification skill's interview format, with a recommended "
                  "answer marked, and the invoking skill proceeds only on the recorded outcome"},
         {"id": "US-SKL-02-S02", "title": "The interview fires when guessing would otherwise happen",
          "given": "a skill about to resolve an ambiguous fork on its own",
          "when": "the fork is detected",
          "then": "the clarification skill triggers automatically — the only skill permitted to — and the fork "
                  "is answered, not guessed"},
     ]},

    {"id": "US-SKL-03", "title": "Resume from wherever the documents stand", "priority": "Must",
     "role": "Operator", "testLayers": ["e2e"],
     "narrative": "As an **operator** I want one command that works out where the chain stopped and continues "
                  "from there, so that returning to a project after a gap costs minutes, not archaeology.",
     "traces": {"fr": ["FR-SKL-05", "FR-EXE-09"]},
     "scenarios": [
         {"id": "US-SKL-03-S01", "title": "Resume continues mid-chain",
          "given": "a document set with a completed intent, context and product requirements but no functional "
                   "specification",
          "when": "the resume skill is invoked",
          "then": "it reports the furthest completed step and continues by invoking the functional-specification "
                  "skill"},
         {"id": "US-SKL-03-S02", "title": "Resume starts from nothing",
          "given": "a repository with no completed intent",
          "when": "the resume skill is invoked",
          "then": "it starts the chain from the beginning, at the intent skill"},
     ]},

    {"id": "US-SKL-04", "title": "Update documents without destroying history", "priority": "Must",
     "role": "Specification author", "testLayers": ["unit", "integration"],
     "narrative": "As a **specification author** I want additions and changes folded in forward only, so that "
                  "nothing a reader once relied on silently disappears.",
     "traces": {"fr": ["FR-SKL-06", "FR-AMD-01", "FR-AMD-04"]},
     "scenarios": [
         {"id": "US-SKL-04-S01", "title": "An update never deletes",
          "given": "a published document and a requested change to one of its entries",
          "when": "the update skill applies the change",
          "then": "the original entry survives — amended in place with the change and its date, or retired with "
                  "a pointer to its successor — and no published content is deleted or overwritten"},
     ]},

    {"id": "US-SKL-05", "title": "Ship the working branch deliberately", "priority": "Should",
     "role": "Operator", "testLayers": ["e2e"],
     "narrative": "As an **operator** I want one command that commits and pushes the working branch and then "
                  "asks about a pull request, so that shipping is a decision I make, not a side effect.",
     "traces": {"fr": ["FR-SKL-07", "FR-EXE-11", "FR-EXE-12"]},
     "scenarios": [
         {"id": "US-SKL-05-S01", "title": "Commit and push, then ask",
          "given": "uncommitted changes on the current working branch",
          "when": "the ship skill is invoked",
          "then": "the changes are committed and pushed on that branch, and the skill asks whether to open a "
                  "pull request to the upstream branch — creating one only on an explicit yes"},
     ]},

    {"id": "US-SKL-06", "title": "Install the whole chain in one action", "priority": "Should",
     "role": "Operator", "testLayers": ["e2e", "manual"],
     "narrative": "As an **operator** I want the complete skill chain installed from one marketplace "
                  "reference, so that adopting the method on a new machine is a single step.",
     "traces": {"fr": ["FR-SKL-08"]},
     "scenarios": [
         {"id": "US-SKL-06-S01", "title": "One install, whole chain",
          "given": "an agent runtime with the plugin marketplace reference added",
          "when": "the plugin is installed",
          "then": "every skill in the chain becomes invocable by name, at the versions the plugin pins"},
     ]},

    {"id": "US-SKL-07", "title": "Setup happens by itself", "priority": "Must",
     "role": "Operator", "testLayers": ["e2e", "integration"],
     "narrative": "As an **operator** I want every piece of project setup performed by the skills themselves, "
                  "so that adopting and running the method never requires me to type a shell command.",
     "traces": {"fr": ["FR-SKL-09"]},
     "scenarios": [
         {"id": "US-SKL-07-S01", "title": "Init sets up a bare repository",
          "given": "a repository with no method layout",
          "when": "the init skill is invoked",
          "then": "the documented layout exists under `.zero/`, the ignore rules are written, the theme is "
                  "detected and reported, and the verification gauntlet is interviewed for and recorded"},
         {"id": "US-SKL-07-S02", "title": "Any chain skill repairs missing setup first",
          "given": "an uninitialised repository",
          "when": "any chain skill is invoked",
          "then": "the init skill runs first, the missing setup is created, and the invoked skill then "
                  "proceeds — without asking the operator to run anything"},
         {"id": "US-SKL-07-S03", "title": "Init is idempotent",
          "given": "an already-initialised repository",
          "when": "the init skill runs again",
          "then": "the repository is left byte-for-byte unchanged"},
     ]},

    {"id": "US-SKL-08", "title": "Open and close a feature by name", "priority": "Must",
     "role": "Operator", "testLayers": ["e2e", "integration"],
     "narrative": "As an **operator** I want one named command that opens a feature, closes the open one and "
                  "tells me where I stand, so that starting and finishing a piece of work is as deliberate as "
                  "every other step of the method.",
     "traces": {"fr": ["FR-SKL-10", "FR-GEN-13", "FR-GEN-14"], "adr": ["ADR-19"]},
     "scenarios": [
         {"id": "US-SKL-08-S01", "title": "Opening takes a name and nothing else",
          "given": "a project whose intent and vocabulary exist",
          "when": "the feature skill is asked to open a named feature",
          "then": "the next number is allocated, the feature's directories are created, and no argument "
                  "selecting a feature was needed or accepted"},
         {"id": "US-SKL-08-S02", "title": "Status says what a close would find",
          "given": "a feature open with outstanding work",
          "when": "the skill is asked for status",
          "then": "it names the open feature and lists exactly what a close with no reason would refuse over"},
         {"id": "US-SKL-08-S03", "title": "Closing states a date rather than reading a clock",
          "given": "a feature ready to close",
          "when": "the skill is asked to close it",
          "then": "the date is supplied by the operator, and a close naming no date is refused with nothing "
                  "written"},
     ]},
]

USE_CASES = [
    {"id": "UC-01", "title": "Take a project from intent to a stable specification", "priority": "Must",
     "actor": "Specification author",
     "goal": "Produce a complete, validated, traceable specification chain from a rough brief.",
     "trigger": "A new project or a major new capability is approved for definition.",
     "pre": ["A brief, notes or a conversation exists.",
             "The skill chain is installed; the init skill creates the repository layout on first use."],
     "main": ["Invoke the intent skill; answer its decision gate; validate the output.",
              "Invoke the context skill against the intent; resolve vocabulary collisions; validate.",
              "Invoke the product-requirements skill against the context; validate.",
              "Invoke the functional-specification skill; author requirements grouped into areas with "
              "priorities; validate.",
              "Invoke the stories skill; every non-excluded functional requirement gains at least one story.",
              "Invoke the technical-design skill; author technical requirements and architecture decisions; "
              "validate.",
              "Review the set end to end; record open questions rather than resolving them by invention.",
              "Freeze the set for the release and record the freeze in the document control blocks."],
     "alt": ["A rich existing brief lets one or more gates be skipped, recorded as such.",
             "An adversarial review pass is run against the specification before freezing."],
     "exc": ["Validation fails — fix the specification object and regenerate; never edit rendered output.",
             "A fork cannot be resolved — record it as an open question and mark dependent requirements 'Could'."],
     "post": "Six validated documents exist, every identifier unique, every trace resolving.",
     "traces": {"fr": ["FR-DOC-01", "FR-DOC-02", "FR-CTX-01", "FR-VAL-01"],
                "us": ["US-DOC-01", "US-DOC-02", "US-CTX-01"]}},

    {"id": "UC-02", "title": "Derive an executable plan and prove coverage", "priority": "Must",
     "actor": "Planner",
     "goal": "Turn a frozen specification into a milestone plan in which every requirement is scheduled.",
     "trigger": "The specification set is frozen for a release.",
     "pre": ["The specification set validates.", "Canonical plan data and the detail directory exist."],
     "main": ["Author the milestone spine: milestones, dependencies, exit criteria, trace sets.",
              "Author phases and tasks for the first wave, each with red/green/refactor and criteria.",
              "Run the plan generator.",
              "Resolve every coverage failure by scheduling the requirement or recording an explicit exclusion.",
              "Run the rendered-artefact validator.",
              "Review the wave ordering and the prerequisite checklist with the operator.",
              "Commit the generated plan documents."],
     "alt": ["Detail is authored one wave ahead rather than for all milestones at once.",
             "A milestone is split when its task count makes a single worker's brief unwieldy."],
     "exc": ["A dependency cycle is reported — restructure the spine; no documents are written.",
             "A requirement genuinely belongs to a later release — record the exclusion with its reason."],
     "post": "A plan index and one document per milestone exist, coverage is complete, waves are computed.",
     "traces": {"fr": ["FR-PLN-02", "FR-TRC-05"], "us": ["US-PLN-01", "US-TRC-01"]}},

    {"id": "UC-03", "title": "Execute a wave unattended", "priority": "Must",
     "actor": "Operator",
     "goal": "Complete every milestone in the current wave without human intervention.",
     "trigger": "The operator starts the orchestrator against a validated plan.",
     "pre": ["The plan validates.", "Prerequisites owned by humans are cleared or their tasks are human-gated.",
             "The run ledger exists."],
     "main": ["Read the plan index and the ledger; recompute the ready set.",
              "Select units with disjoint write sets, up to the concurrency ceiling.",
              "Dispatch one worker per unit with that unit's generated brief.",
              "Each worker writes the failing test, implements, refactors, runs the gauntlet.",
              "Each worker writes status back, commits, and returns its report.",
              "Update the ledger with done-state, decisions and the next step.",
              "Repeat until the wave is complete, then advance."],
     "alt": ["A unit is human-gated — skip it and leave it blocked for a person.",
             "A worker chooses a substituted provider where the task names one."],
     "exc": ["A worker returns no report — treat the unit as failed and re-dispatch once.",
             "A unit exhausts its retries — mark blocked, record the blocker, continue with the next unit.",
             "Two workers contend on a file — serialise them and report the contention."],
     "post": "Every non-blocked unit in the wave is passing; the ledger records the exact resume point.",
     "traces": {"fr": ["FR-EXE-01", "FR-EXE-02", "FR-EXE-07"], "us": ["US-EXE-01", "US-EXE-04"]}},

    {"id": "UC-04", "title": "Resume after an interruption", "priority": "Must",
     "actor": "Operator",
     "goal": "Continue a run that was stopped, crashed, or lost its working memory, without repeating work.",
     "trigger": "A run is restarted.",
     "pre": ["The plan and the ledger are on disk."],
     "main": ["Read the ledger first, before the plan.",
              "Read the plan and recompute the ready set from stored status.",
              "Compare against the ledger's recorded next step; prefer the plan where they disagree, and record "
              "the discrepancy.",
              "Resume dispatch."],
     "alt": ["The ledger is missing — rebuild it from the plan's status and note the gap."],
     "exc": ["A unit is in progress with no owning worker — reset it to not started and re-dispatch.",
             "The plan fails validation on resume — stop and report; do not execute against an invalid plan."],
     "post": "The run continues from the correct point with no unit executed twice.",
     "traces": {"fr": ["FR-EXE-09"], "us": ["US-EXE-03"]}},

    {"id": "UC-05", "title": "Close a milestone", "priority": "Must",
     "actor": "Operator",
     "goal": "Confirm a milestone genuinely meets its exit criteria and capture what it taught.",
     "trigger": "Every task in a milestone reaches passing or blocked.",
     "pre": ["Automated gates for the milestone are green."],
     "main": ["Check every milestone exit criterion against real evidence.",
              "Clear every outstanding human-review criterion or record why it is deferred.",
              "Write the retrospective.",
              "Set the milestone status and commit the plan document.",
              "Distil any new convention into the shared cheat-sheet."],
     "alt": ["A blocked task is accepted into the next milestone with an explicit note."],
     "exc": ["An exit criterion cannot be evidenced — the milestone does not close; the gap becomes a task."],
     "post": "The milestone is closed, its retrospective exists, and later waves inherit its lessons.",
     "traces": {"fr": ["FR-PLN-08", "FR-LRN-01"], "us": ["US-LRN-01"]}},

    {"id": "UC-06", "title": "Add scope to a shipped specification", "priority": "Must",
     "actor": "Specification author",
     "goal": "Introduce new capability without invalidating existing identifiers, traces or completed work.",
     "trigger": "New scope is approved after the specification set was frozen.",
     "pre": ["The existing set is stable and its plan has been executed at least in part."],
     "main": ["Author an addendum specification with its own identifier prefix.",
              "Register the prefix so trace links route to the addendum.",
              "Add milestones that claim the new identifiers.",
              "Regenerate the plan and clear the coverage gate.",
              "Annotate any superseded requirement in place with the amendment and its date."],
     "alt": ["Small clarifications are made as in-place annotations rather than a new document."],
     "exc": ["The addendum contradicts a locked decision — surface the conflict; do not silently re-decide."],
     "post": "New scope is specified, scheduled and covered; every prior identifier still resolves.",
     "traces": {"fr": ["FR-AMD-01", "FR-AMD-04"], "us": ["US-AMD-01"]}},

    {"id": "UC-07", "title": "Review a specification as a stakeholder", "priority": "Should",
     "actor": "Reviewer",
     "goal": "Read, filter and comment on a specification without any project tooling.",
     "trigger": "A document is shared for review.",
     "pre": ["The reviewer has the file and a browser."],
     "main": ["Open the file directly.",
              "Filter to the area of interest and switch off priorities that are out of scope for the review.",
              "Mark entries reviewed as they are read; progress persists across sittings.",
              "Deep-link specific entries into the review conversation."],
     "alt": ["Print or export the document for offline annotation."],
     "exc": ["A trace points at a companion document the reviewer does not have — request the set, not the file."],
     "post": "The reviewer's findings reference exact identifiers.",
     "traces": {"fr": ["FR-SPC-05", "FR-SPC-06", "FR-SPC-08", "FR-SPC-11"],
                "us": ["US-SPC-02", "US-SPC-03", "US-SPC-04"]}},

    {"id": "UC-08", "title": "Promote a release", "priority": "Should",
     "actor": "Operator",
     "goal": "Move completed, integrated work to production under an explicit human decision.",
     "trigger": "A wave or milestone set is complete on the integration branch.",
     "pre": ["Automated gates are green.", "The integration environment is healthy.",
             "Human-review criteria are signed off."],
     "main": ["Open the promotion request from the integration branch.",
              "Confirm each gate against its live source rather than a remembered result.",
              "Read the change.",
              "Approve and merge as a release.",
              "Confirm the deployment actually happened and is healthy."],
     "alt": ["Promotion is deferred and the integration branch continues to accumulate work."],
     "exc": ["A gate is red — promotion stops; the failure becomes a task.",
             "A deployment succeeds but the live check fails — roll back and record it as a blocker."],
     "post": "Production reflects the integrated work, verified against the live system.",
     "traces": {"fr": ["FR-EXE-12", "FR-GEN-03"], "nfr": ["NFR-OPS-03", "NFR-OPS-05"]}},

    {"id": "UC-09", "title": "Adopt the method in an existing project", "priority": "Should",
     "actor": "Planner",
     "goal": "Introduce the method into a codebase that already exists, without stopping delivery.",
     "trigger": "A team decides to adopt the method.",
     "pre": ["The repository has version control and a working verification command."],
     "main": ["Install the generators and create the repository layout.",
              "Author a functional specification describing what the system does today, marking gaps as open "
              "questions.",
              "Author the technical specification by recording existing decisions as architecture decisions.",
              "Plan only the next release, not the history.",
              "Run the coverage gate against that release's scope.",
              "Adopt the execution layer once one milestone has been planned this way."],
     "alt": ["Adopt the specification chain alone and continue executing by hand."],
     "exc": ["Existing behaviour cannot be described without contradictions — record them as open questions and "
             "schedule a decision, rather than specifying an idealised system."],
     "post": "The next release is specified, planned and covered; earlier history is left alone.",
     "traces": {"fr": ["FR-GEN-01"], "nfr": ["NFR-ARC-05"]}},

    {"id": "UC-10", "title": "Diagnose a false green", "priority": "Should",
     "actor": "Operator",
     "goal": "Establish what actually happened when a unit reports success but the system misbehaves.",
     "trigger": "A passing unit is found not to work.",
     "pre": ["The plan, the ledger and the worker reports are available."],
     "main": ["Read the unit's report and identify which command it claims produced the result.",
              "Re-run that command against the live system and compare.",
              "Check whether the unit's criteria were machine-checkable or asserted.",
              "Reopen the unit, strengthen its criteria, and record the gap as a method lesson."],
     "alt": ["The verification layer itself was wrong — fix the layer and re-verify every unit that relied on it."],
     "exc": ["The report does not name its evidence — treat the unit as unverified and re-execute it."],
     "post": "The unit is genuinely verified and the class of defect is closed at the method level.",
     "traces": {"fr": ["FR-GEN-03", "FR-EXE-10"], "nfr": ["NFR-EXE-10", "NFR-VAL-05"]}},

    {"id": "UC-11", "title": "Open, work and close a feature", "priority": "Must",
     "actor": "Operator",
     "goal": "Take one piece of work through the whole method without disturbing the set that describes the "
             "work already shipped.",
     "trigger": "A new capability is agreed for a project whose intent and vocabulary already exist.",
     "pre": ["The project's intent and shared vocabulary exist.", "No other feature is open."],
     "main": ["Open a named feature; it is given the next number and its own specification, plan and state "
              "directories.",
              "Run the specification chain inside it — its own intent, requirements, stories and technical "
              "design — reading the project's vocabulary rather than writing a second one.",
              "Derive the feature's plan and prove coverage over that feature's identifiers alone.",
              "Execute the plan; status and the run ledger stay inside the feature.",
              "Close the feature; the audit reports every unit not passing, every retired identifier with no "
              "successor, every open question and everything unshipped.",
              "Record the close — its date, its reason and anything left — in the feature's own first "
              "document."],
     "alt": ["Something small arrives mid-feature and is folded in as an addendum rather than opening a "
             "second feature.",
             "The feature is parked before it is finished: it is closed with a reason, and the audit's "
             "findings are recorded as what was left."],
     "exc": ["A second feature is opened while one is open — refused, naming the open one; nothing is created.",
             "A generator is asked to write into a feature already closed — refused as a missing prerequisite.",
             "A close states no date — refused; nothing is written."],
     "post": "The feature's documents, plan and record of closing stand on their own, the project's shared "
             "layer is unchanged, and the next feature can be opened.",
     "traces": {"fr": ["FR-GEN-12", "FR-GEN-13", "FR-GEN-14", "FR-SKL-10"], "adr": ["ADR-19"],
                "us": ["US-GEN-04", "US-GEN-05", "US-GEN-06", "US-SKL-08"]}},
]

GLOBAL_ACCEPTANCE = [
    "Every generated document opens from the filesystem with no console error.",
    "Every identifier referenced by a scenario exists in the specification set.",
    "Every automated test written for a scenario is named for that scenario's identifier.",
    "No scenario asserts on generated prose wording; assertions are on structure, identifiers and presence.",
    "No test uses a live credential or contacts a paid provider.",
    "Every document meets the keyboard, contrast and reduced-motion requirements before its story is closed.",
]
