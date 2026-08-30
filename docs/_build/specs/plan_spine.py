# -*- coding: utf-8 -*-
"""Zero-to-Ship — Development plan: legend and milestone spine."""

DOC = {
    "title": "Zero-to-Ship — Development Plan",
    "slug": "plan",
    "kicker": "Execution plan",
    "type": "Execution plan (milestone → phase → task)",
    "version": "2.6",
    "status": "For execution",
    "date": "2026-08-29",
    "owner": "Zerø Effort",
    "releaseScope": "v2 — the complete toolchain as the /zero:* skill chain",
    "summary": "The buildable plan for the Zero-to-Ship toolchain itself: seventeen milestones, each decomposed "
               "into phases and test-first tasks, every one tracing to the requirements and decisions it "
               "satisfies.",
    "scopeNote": "This document is generated from canonical plan data plus the specifications' own embedded JSON. "
                 "Status lives in this file's specification block and is written by the status tool — never by "
                 "hand. Every requirement in the FSD and SDD is claimed by at least one task below; generation "
                 "fails otherwise.",
}

LEGEND = {
    "statuses": [
        {"id": "not-started", "label": "Not started", "tone": "",
         "desc": "No work begun. Eligible once every dependency is passing."},
        {"id": "in-progress", "label": "In progress", "tone": "info",
         "desc": "Actively being worked; red → green → refactor under way."},
        {"id": "passing", "label": "Passing", "tone": "ok",
         "desc": "Every named verification layer actually ran and passed in this run."},
        {"id": "failing", "label": "Failing", "tone": "err",
         "desc": "Attempted; one or more gates are red."},
        {"id": "blocked", "label": "Blocked", "tone": "warn",
         "desc": "A dependency is not passing, an external prerequisite is missing, or retries were exhausted."},
        {"id": "needs-review", "label": "Needs review", "tone": "warn",
         "desc": "Machine gates pass; a human-review criterion is outstanding. Blocks the milestone, not the task."},
    ],
    "priorities": [
        {"id": "Must", "label": "Must"}, {"id": "Should", "label": "Should"}, {"id": "Could", "label": "Could"},
    ],
    "autonomy": [
        {"id": "auto", "label": "Autonomous",
         "desc": "A worker runs this unattended — code and tests only, no external provider, no interactive tool."},
        {"id": "auto-with-mock", "label": "Autonomous · substituted",
         "desc": "Runs unattended only against the substitution the task names — never a live credential."},
        {"id": "human-gate", "label": "Human gate",
         "desc": "Requires a person: a live credential, a paid provider, a judgement call, or an interactive tool."},
    ],
    "layers": [
        {"id": "foundation", "label": "Foundation"}, {"id": "schema", "label": "Schema / contract"},
        {"id": "generator", "label": "Generator"}, {"id": "runtime", "label": "Document runtime"},
        {"id": "validator", "label": "Validator"}, {"id": "orchestration", "label": "Orchestration"},
        {"id": "ops", "label": "Ops / CI"}, {"id": "docs", "label": "Documentation"},
    ],
    "testLayers": [
        {"id": "unit", "label": "Unit"}, {"id": "integration", "label": "Integration"},
        {"id": "e2e", "label": "End-to-end"}, {"id": "a11y", "label": "Accessibility"},
        {"id": "perf", "label": "Performance"}, {"id": "lint", "label": "Static analysis"},
        {"id": "CI", "label": "CI gate"}, {"id": "manual", "label": "Human review"},
    ],
    "criterionKinds": [
        {"id": "auto", "label": "Automated", "desc": "Machine-checkable; the loop verifies it without a human."},
        {"id": "human-review", "label": "Human review",
         "desc": "Subjective; non-blocking at task level, must be signed off before the milestone closes."},
    ],
}

MILESTONES = [
    {"id": "M1", "title": "Foundation — repository, template and shared runtime",
     "file": "plan#M1", "dependsOn": [], "status": "passing",
     "goal": "Establish the repository layout and the one shared document shell every generator will use: "
             "structural styling, the JSON-driven runtime, design-system adoption and the neutral fallback.",
     "exit": ["A document generated from a hand-written specification opens from the filesystem and renders "
              "every section type with no console error.",
              "Structural styling references design tokens exclusively; no hard-coded colour or font exists "
              "outside the token block.",
              "Generating twice from unchanged input produces byte-identical files.",
              "Keyboard navigation, contrast and reduced-motion checks pass on the specimen document."]},

    {"id": "M2", "title": "Specification contracts and the schema validator",
     "file": "plan#M2", "dependsOn": ["M1"], "status": "passing",
     "goal": "Define the document envelope, the catalogue-entry contract and the identifier grammar, and build "
             "the validator that enforces them across every document type.",
     "exit": ["Every schema is versioned and published.",
              "The validator reports every violation in one pass and exits non-zero on failure.",
              "A document set containing a duplicate identifier, a malformed identifier and a dangling trace "
              "produces three distinct, correctly attributed failures."]},

    {"id": "M3", "title": "Vision, context and product-requirements generators",
     "file": "plan#M3", "dependsOn": ["M2"], "status": "passing",
     "goal": "Build the first three generators in the chain — vision, context and product requirements — "
             "including the decision gate and locked-decisions record they share with every later generator, "
             "and the ubiquitous-language glossary every downstream document speaks.",
     "exit": ["All three generators produce validating documents from a thin brief and from a rich one.",
              "The gate refuses to author anything until every fork is resolved.",
              "A locked-decisions table exists in the document and the ledger before content is authored.",
              "The context generator refuses to run without a completed vision, and downstream generators use "
              "its canonical terms."]},

    {"id": "M4", "title": "Functional specification generator",
     "file": "plan#M4", "dependsOn": ["M2"], "status": "passing",
     "goal": "Build the generator for the functional specification — the document the whole downstream chain "
             "traces to — with priority handling, area grouping and the separation of functional from technical.",
     "exit": ["A functional specification generated from a brief validates and contains no technical requirement.",
              "Priorities, areas, tags and notes render and filter correctly.",
              "Gaps appear as open questions; nothing is fabricated."]},

    {"id": "M5", "title": "Stories and use-case generator",
     "file": "plan#M5", "dependsOn": ["M4"], "status": "passing",
     "goal": "Turn functional requirements into goal-level stories with Given/When/Then scenarios and "
             "actor-centred use cases, with identifiers precise enough to name tests after.",
     "exit": ["Every non-excluded functional requirement is covered by at least one story.",
              "Scenario identifiers are stable and unique, and are the names automated tests will carry.",
              "Non-deterministic behaviour is asserted structurally, never by generated wording."]},

    {"id": "M6", "title": "Technical specification generator",
     "file": "plan#M6", "dependsOn": ["M4"], "status": "passing",
     "goal": "Build the generator for technical requirements and architecture decisions, including the decision "
             "record format and the performance and safety target tables.",
     "exit": ["A technical specification validates and every decision carries context, alternatives and "
              "consequences.",
              "Technical requirements trace to the functional requirements that motivate them.",
              "Targets are stated as measurable numbers, not adjectives."]},

    {"id": "M7", "title": "Traceability and coverage engine",
     "file": "plan#M7", "dependsOn": ["M4", "M6"], "status": "passing",
     "goal": "Build the shared machinery that reads every document's embedded specification, resolves the trace "
             "universe across core documents and addenda, and computes the coverage matrix.",
     "exit": ["The coverage matrix is computed from the documents themselves, not from a maintained list.",
              "An unclaimed requirement fails the gate and is named.",
              "Prefix routing resolves an addendum trace to the document that defines it.",
              "Generation succeeds with an addendum absent and reports the absence."]},

    {"id": "M8", "title": "Plan generator",
     "file": "plan#M8", "dependsOn": ["M7"], "status": "passing",
     "goal": "Generate the plan index and one document per milestone from canonical plan data plus the "
             "specifications, including dependency validation, wave computation and per-unit execution prompts.",
     "exit": ["A plan is produced from data alone; no plan markup is hand-authored anywhere.",
              "Dependency cycles and unknown dependencies are rejected before any file is written.",
              "Wave ordering is derived and every milestone in a wave depends only on earlier waves.",
              "Every milestone carries a self-contained execution prompt."]},

    {"id": "M9", "title": "Rendered-artefact validation and continuous-integration gates",
     "file": "plan#M9", "dependsOn": ["M8"], "status": "blocked",
     "goal": "Validate the produced files rather than the data behind them, and wire schema, structural and "
             "coverage checks into the project's pipeline as blocking gates.",
     "exit": ["Validation extracts each document's specification from the rendered output and asserts structure.",
              "A truncated or corrupted output file is caught.",
              "All gates run on every change and block integration on failure.",
              "A skipped check is reported as skipped and never counted as passed."]},

    {"id": "M10", "title": "Status model and write-back",
     "file": "plan#M10", "dependsOn": ["M8"], "status": "passing",
     "goal": "Implement the status vocabulary, the write-back tool that edits only the embedded specification, "
             "the rollup, and the human-review queue.",
     "exit": ["Write-back changes only the specification block; every other byte is preserved.",
              "An invalid status or unknown identifier is rejected without modifying the file.",
              "Rollup and the human-review queue are derived, never stored.",
              "A status change is committed together with the work it describes."]},

    {"id": "M11", "title": "Autonomous execution",
     "file": "plan#M11", "dependsOn": ["M9", "M10"], "status": "passing",
     "goal": "Build the orchestrator: ready-set computation, wave-ordered dispatch, collision-free concurrency, "
             "the worker brief and report contract, blocker policy, and resumability through the ledger.",
     "exit": ["A plan executes end to end with no human question asked mid-run.",
              "An interrupted run resumes without repeating or skipping a unit.",
              "A worker returning no report is treated as failed.",
              "No unit passes on the say-so of the worker that built it.",
              "No unattended unit uses a live credential, prompts interactively, or performs a destructive "
              "operation."]},

    {"id": "M12", "title": "Retrospectives, amendment and self-hosting",
     "file": "plan#M12", "dependsOn": ["M11", "M3", "M5"], "status": "needs-review",
     "goal": "Close the loop: retrospectives that feed the next wave, amendment by addendum, the narrative "
             "briefing output, and regenerating the method's own documentation with the method.",
     "exit": ["A milestone close writes a retrospective, and later briefs require reading all prior ones.",
              "New scope is added by addendum with no existing identifier disturbed.",
              "The method's own document set is produced by the toolchain and passes every gate.",
              "The adoption guide states the minimum viable subset explicitly."]},

    {"id": "M13", "title": "Skill chain and plugin distribution",
     "file": "plan#M13", "dependsOn": ["M12"], "status": "passing",
     "goal": "Wrap every step of the finished toolchain as a named, separately invocable skill — one per "
             "document type plus init, resume, build, update, ship and the shared clarification interview — "
             "enforce the trigger and prerequisite rules in the skill definitions themselves, and package the "
             "chain as one version-pinned installable plugin.",
     "exit": ["Every chain step is invocable by name and refuses to run when its upstream prerequisite is "
              "missing, naming exactly what is absent.",
              "A chain skill invoked in an uninitialised repository sets itself up and proceeds; no step of "
              "the method requires an operator shell command.",
              "No skill triggers automatically except the clarification interview, whose firing rules live in "
              "its definition.",
              "One marketplace install action yields the complete chain at pinned versions.",
              "The resume skill continues correctly from every partially complete document set."]},
    {"id": "M14", "title": "Gauntlet-loop prompts at every level",
     "file": "plan#M14", "dependsOn": ["M13"], "status": "passing",
     "goal": "Carry a complete execution prompt on every unit of the plan — the whole build, each milestone, "
             "each phase and each task — and make every one of them run the same builder-and-critic loop the "
             "orchestrator runs, aiming above the acceptance criteria rather than stopping the moment the boxes "
             "tick.",
     "exit": ["The whole build, every milestone, every phase and every task each carry their own complete "
              "prompt, on their own card, each copyable on its own.",
              "Every prompt states the split as the reader's to make, an independent critic per piece, one gap "
              "on a failure, and no number of rounds.",
              "Every prompt names the higher target the unit already traces to, and says plainly when there is "
              "none rather than inventing one.",
              "The prompt a plan document carries and the brief the orchestrator hands a worker say the same "
              "thing about the same unit.",
              "A named skill prints one unit's instructions and does nothing else.",
              "The stated document size budget is measured on every run."]},
    {"id": "M15", "title": "A plan you can navigate",
     "file": "plan#M15", "dependsOn": ["M14"], "status": "passing",
     "goal": "Make a plan something an operator moves around in rather than scrolls through: one document per "
             "milestone with navigation between them, everything shut except the first unit at each level, "
             "opening one unit closing its siblings, and an execution prompt that says what it holds and can be "
             "taken without being opened.",
     "exit": ["The plan is one document written across an index and one file per milestone, and every part of it "
              "reaches every other part.",
              "No identifier is declared twice across the set, and every scheduled milestone names a document "
              "that was actually written.",
              "A plan document opens with the first unit at each level open and every sibling shut, and opening "
              "one unit closes its siblings at that level.",
              "A collapsed execution prompt names the unit it belongs to and can be copied without being "
              "opened.",
              "A printed plan expands every folded phase and task, and drops only the instructions.",
              "The same runtime leaves every specification catalogue exactly as it was: open on arrival, "
              "nothing closing anything else.",
              "The requirements this changes are amended in place and dated, with the original left as written "
              "and no identifier retired."]},
    {"id": "M16", "title": "Documents that look like the product", "dependsOn": ["M15"],
     "file": "plan#M16", "status": "passing",
     "goal": "Make a generated document actually look like a page of the project it describes — its palette, "
             "type scale, density, shape, elevation and both colour schemes — by reading every source a design "
             "system is written in rather than the single best file, writing what was adopted to a record "
             "anybody can review and correct, and refusing any host value that could not be written safely.",
     "exit": ["A document generated in a project with a real design system carries that project's colour, type "
              "scale, spacing, shape and elevation, in light and in dark.",
              "Every token the contract declares can be filled by a host project and is used by the styling; "
              "no token is declared that nothing reads.",
              "A design system split across several files, or written in a brand book rather than a "
              "stylesheet, is adopted from all of it, and a document the operator names outranks anything "
              "found by searching.",
              "A value stated only in prose is adopted only after the operator confirms it, and an unanswered "
              "one is reported as unanswered rather than as adopted.",
              "The design that was adopted is recorded with every value naming the file and the name it came "
              "from, and a value recorded by an operator outranks anything detected.",
              "A host value that could close the style block or fetch from elsewhere is refused, reported, and "
              "replaced by the neutral value — never stripped and used.",
              "A project that declares no dark values produces exactly the document it produced before."]},
    {"id": "M17", "title": "The hours the orchestrator threw away", "dependsOn": ["M16"],
     "file": "plan#M17", "status": "not-started",
     "goal": "Stop the run discarding finished work. Name every check a unit will be held to in its brief, run "
             "them cheapest first, hand a broken whole-repository check back to the worker that broke it "
             "instead of briefing somebody new from nothing, charge no unit for a host that cannot start a "
             "worker or for a failure another unit landed, and let an operator correct a wrong write list "
             "without regenerating the plan the run is holding open.",
     "exit": ["Every gauntlet runs cheapest first, in an order the method publishes and no project configures.",
              "A brief names every whole-repository check the unit will be held to, with its command.",
              "A red whole-repository check reaches the worker that broke it, once, in the dispatch it already "
              "worked in, and what that turn changes is committed with the unit.",
              "A dispatch that never started charges the unit neither an attempt nor a misfire, waits longer "
              "each time, and stops the run once nothing at all is starting.",
              "A layer already failing before a unit was dispatched charges it nothing, and every stated layer "
              "is run at each milestone boundary.",
              "Whether another unit landed a failing file is read from version control, never asserted by a "
              "worker, and the report contract gains no key for it.",
              "An operator widens a declared write set in the run's own state and the next scheduling decision "
              "uses it, with no document regenerated.",
              "No prose surface states a retry bound the code no longer produces."]},
]

PREREQUISITES = [
    {"id": "PRE-01", "text": "A repository with version control and a branch policy allowing an integration branch.",
     "owner": "human"},
    {"id": "PRE-02", "text": "A scripting runtime available on every developer and CI machine.", "owner": "human"},
    {"id": "PRE-03", "text": "An agent runtime able to load named skills, edit files and run commands.",
     "owner": "human"},
    {"id": "PRE-04", "text": "A verification command for the host project that exits non-zero on failure.",
     "owner": "human"},
    {"id": "PRE-05", "text": "Optional: a headless browser for the rendered-view check. Absence is reported, "
                             "never silently skipped.", "owner": "human"},
    {"id": "PRE-06", "text": "A design system or token file to adopt; the neutral fallback is used when absent.",
     "owner": "human"},
]
