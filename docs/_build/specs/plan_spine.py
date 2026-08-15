# -*- coding: utf-8 -*-
"""Zero-to-Ship — Development plan: legend and milestone spine."""

DOC = {
    "title": "Zero-to-Ship — Development Plan",
    "slug": "plan",
    "kicker": "Execution plan",
    "type": "Execution plan (milestone → phase → task)",
    "version": "2.0",
    "status": "Draft for execution",
    "date": "2026-08-13",
    "owner": "Zerø Effort",
    "releaseScope": "v2 — the complete toolchain as the /zero-* skill chain",
    "summary": "The buildable plan for the Zero-to-Ship toolchain itself: thirteen milestones, each decomposed "
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
     "file": "plan#M1", "dependsOn": [], "status": "not-started",
     "goal": "Establish the repository layout and the one shared document shell every generator will use: "
             "structural styling, the JSON-driven runtime, design-system adoption and the neutral fallback.",
     "exit": ["A document generated from a hand-written specification opens from the filesystem and renders "
              "every section type with no console error.",
              "Structural styling references design tokens exclusively; no hard-coded colour or font exists "
              "outside the token block.",
              "Generating twice from unchanged input produces byte-identical files.",
              "Keyboard navigation, contrast and reduced-motion checks pass on the specimen document."]},

    {"id": "M2", "title": "Specification contracts and the schema validator",
     "file": "plan#M2", "dependsOn": ["M1"], "status": "not-started",
     "goal": "Define the document envelope, the catalogue-entry contract and the identifier grammar, and build "
             "the validator that enforces them across every document type.",
     "exit": ["Every schema is versioned and published.",
              "The validator reports every violation in one pass and exits non-zero on failure.",
              "A document set containing a duplicate identifier, a malformed identifier and a dangling trace "
              "produces three distinct, correctly attributed failures."]},

    {"id": "M3", "title": "Vision, context and product-requirements generators",
     "file": "plan#M3", "dependsOn": ["M2"], "status": "not-started",
     "goal": "Build the first three generators in the chain — vision, context and product requirements — "
             "including the decision gate and locked-decisions record they share with every later generator, "
             "and the ubiquitous-language glossary every downstream document speaks.",
     "exit": ["All three generators produce validating documents from a thin brief and from a rich one.",
              "The gate refuses to author anything until every fork is resolved.",
              "A locked-decisions table exists in the document and the ledger before content is authored.",
              "The context generator refuses to run without a completed vision, and downstream generators use "
              "its canonical terms."]},

    {"id": "M4", "title": "Functional specification generator",
     "file": "plan#M4", "dependsOn": ["M2"], "status": "not-started",
     "goal": "Build the generator for the functional specification — the document the whole downstream chain "
             "traces to — with priority handling, area grouping and the separation of functional from technical.",
     "exit": ["A functional specification generated from a brief validates and contains no technical requirement.",
              "Priorities, areas, tags and notes render and filter correctly.",
              "Gaps appear as open questions; nothing is fabricated."]},

    {"id": "M5", "title": "Stories and use-case generator",
     "file": "plan#M5", "dependsOn": ["M4"], "status": "not-started",
     "goal": "Turn functional requirements into goal-level stories with Given/When/Then scenarios and "
             "actor-centred use cases, with identifiers precise enough to name tests after.",
     "exit": ["Every non-excluded functional requirement is covered by at least one story.",
              "Scenario identifiers are stable and unique, and are the names automated tests will carry.",
              "Non-deterministic behaviour is asserted structurally, never by generated wording."]},

    {"id": "M6", "title": "Technical specification generator",
     "file": "plan#M6", "dependsOn": ["M4"], "status": "not-started",
     "goal": "Build the generator for technical requirements and architecture decisions, including the decision "
             "record format and the performance and safety target tables.",
     "exit": ["A technical specification validates and every decision carries context, alternatives and "
              "consequences.",
              "Technical requirements trace to the functional requirements that motivate them.",
              "Targets are stated as measurable numbers, not adjectives."]},

    {"id": "M7", "title": "Traceability and coverage engine",
     "file": "plan#M7", "dependsOn": ["M4", "M6"], "status": "not-started",
     "goal": "Build the shared machinery that reads every document's embedded specification, resolves the trace "
             "universe across core documents and addenda, and computes the coverage matrix.",
     "exit": ["The coverage matrix is computed from the documents themselves, not from a maintained list.",
              "An unclaimed requirement fails the gate and is named.",
              "Prefix routing resolves an addendum trace to the document that defines it.",
              "Generation succeeds with an addendum absent and reports the absence."]},

    {"id": "M8", "title": "Plan generator",
     "file": "plan#M8", "dependsOn": ["M7"], "status": "not-started",
     "goal": "Generate the plan index and one document per milestone from canonical plan data plus the "
             "specifications, including dependency validation, wave computation and per-unit execution prompts.",
     "exit": ["A plan is produced from data alone; no plan markup is hand-authored anywhere.",
              "Dependency cycles and unknown dependencies are rejected before any file is written.",
              "Wave ordering is derived and every milestone in a wave depends only on earlier waves.",
              "Every milestone carries a self-contained execution prompt."]},

    {"id": "M9", "title": "Rendered-artefact validation and continuous-integration gates",
     "file": "plan#M9", "dependsOn": ["M8"], "status": "not-started",
     "goal": "Validate the produced files rather than the data behind them, and wire schema, structural and "
             "coverage checks into the project's pipeline as blocking gates.",
     "exit": ["Validation extracts each document's specification from the rendered output and asserts structure.",
              "A truncated or corrupted output file is caught.",
              "All gates run on every change and block integration on failure.",
              "A skipped check is reported as skipped and never counted as passed."]},

    {"id": "M10", "title": "Status model and write-back",
     "file": "plan#M10", "dependsOn": ["M8"], "status": "not-started",
     "goal": "Implement the status vocabulary, the write-back tool that edits only the embedded specification, "
             "the rollup, and the human-review queue.",
     "exit": ["Write-back changes only the specification block; every other byte is preserved.",
              "An invalid status or unknown identifier is rejected without modifying the file.",
              "Rollup and the human-review queue are derived, never stored.",
              "A status change is committed together with the work it describes."]},

    {"id": "M11", "title": "Autonomous execution",
     "file": "plan#M11", "dependsOn": ["M9", "M10"], "status": "not-started",
     "goal": "Build the orchestrator: ready-set computation, wave-ordered dispatch, collision-free concurrency, "
             "the worker brief and report contract, blocker policy, and resumability through the ledger.",
     "exit": ["A plan executes end to end with no human question asked mid-run.",
              "An interrupted run resumes without repeating or skipping a unit.",
              "A worker returning no report is treated as failed.",
              "No unit passes on the say-so of the worker that built it.",
              "No unattended unit uses a live credential, prompts interactively, or performs a destructive "
              "operation."]},

    {"id": "M12", "title": "Retrospectives, amendment and self-hosting",
     "file": "plan#M12", "dependsOn": ["M11", "M3", "M5"], "status": "not-started",
     "goal": "Close the loop: retrospectives that feed the next wave, amendment by addendum, the narrative "
             "briefing output, and regenerating the method's own documentation with the method.",
     "exit": ["A milestone close writes a retrospective, and later briefs require reading all prior ones.",
              "New scope is added by addendum with no existing identifier disturbed.",
              "The method's own document set is produced by the toolchain and passes every gate.",
              "The adoption guide states the minimum viable subset explicitly."]},

    {"id": "M13", "title": "Skill chain and plugin distribution",
     "file": "plan#M13", "dependsOn": ["M12"], "status": "not-started",
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
