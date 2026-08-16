# -*- coding: utf-8 -*-
"""Zero-to-Ship — System Design Document (NFR-* + ADR-*)."""

DOC = {
    "title": "Zero-to-Ship — System Design Document",
    "slug": "sdd",
    "kicker": "Technical specification",
    "type": "System Design Document (SDD)",
    "version": "2.1",
    "status": "Draft for review",
    "date": "2026-08-15",
    "owner": "Zerø Effort",
    "releaseScope": "v2 — the complete toolchain as the /zero:* skill chain",
    "summary": "How the Zero-to-Ship toolchain is built: its components, data contracts, algorithms, "
               "architecture decisions and non-functional constraints — at the depth needed to implement it "
               "without guessing.",
    "scopeNote": "Technical and non-functional requirements (`NFR-*`) and architecture decisions (`ADR-*`). "
                 "Functional behaviour lives in the FSD as `FR-*` and is referenced, never restated.",
}

PRINCIPLES = [
    {"name": "One source of truth per fact",
     "desc": "Each fact is stored exactly once and everything else is derived from it. The rendered document is "
             "derived from its spec; the plan is derived from the specs; status is stored in the plan alone."},
    {"name": "Derived artefacts are generated, never edited",
     "desc": "If a file is generated, the only supported way to change it is to change its source and regenerate. "
             "Hand-editing generated output is treated as corruption."},
    {"name": "Gates are machine-checkable",
     "desc": "Every quality claim the method makes is enforced by a command that exits non-zero. A claim no "
             "command can check is documented as a human-review item, not asserted."},
    {"name": "Validate the artefact, not the intent",
     "desc": "Checks run against the produced file, extracting what it actually contains. Validating the input "
             "proves only that the input was well formed."},
    {"name": "Fail loudly, continue safely",
     "desc": "A blocked unit stops itself, records why, and lets the run continue elsewhere. Nothing silently "
             "degrades and nothing silently stalls."},
    {"name": "Portable by construction",
     "desc": "Every deliverable is a plain file. No database, no service, no runtime dependency a reader must "
             "install to consume the output."},
]

STACK = [
    {"layer": "Document format", "choice": "Single-file HTML with an embedded JSON specification",
     "role": "The deliverable. Human view and machine view in one artefact that needs no build step."},
    {"layer": "Document runtime", "choice": "Dependency-free browser script, inlined",
     "role": "Renders the document from its embedded specification and provides filter, review, navigation."},
    {"layer": "Styling", "choice": "Host project's design tokens, inlined; neutral fallback theme",
     "role": "Documents look like the project they describe without importing a stylesheet."},
    {"layer": "Generators", "choice": "Scripting-language modules with no third-party dependencies",
     "role": "Read canonical data plus upstream specs, emit documents."},
    {"layer": "Canonical plan data", "choice": "Source-controlled data modules plus per-milestone detail files",
     "role": "The single authoring surface for the plan spine and its detail."},
    {"layer": "Validators", "choice": "Standard-library scripts returning non-zero on failure",
     "role": "Schema, structural, coverage and rendered-artefact checks, wired into the build."},
    {"layer": "Status write-back", "choice": "Command-line tool that edits the embedded specification in place",
     "role": "Flips task status and ticks criteria without disturbing the rest of the file."},
    {"layer": "Agent interface", "choice": "Named, versioned skill definitions the agent loads on demand",
     "role": "Each generator and the orchestrator are invocable by name with a documented contract."},
    {"layer": "Orchestration", "choice": "Wave-ordered fan-out with one worker per unit of work",
     "role": "Executes the plan, respecting dependencies and collision rules."},
    {"layer": "Run ledger", "choice": "Plain text file outside version control",
     "role": "Durable done-state, decisions and resume instructions across context loss."},
    {"layer": "Version control", "choice": "Git, three branch tiers",
     "role": "Feature branches integrate to a shared branch; the shared branch promotes to production."},
    {"layer": "Continuous integration", "choice": "The project's own pipeline, extended with the method's gates",
     "role": "Runs schema, structural, coverage and rendered-artefact validation on every change."},
    {"layer": "Browser verification", "choice": "Headless browser driver, optional",
     "role": "Confirms a generated document actually renders; skipped and reported when unavailable."},
]

COMPONENTS = [
    {"name": "Document generators (seven)", "kind": "Agent skill + template",
     "responsibilities": "One per document type — Vision, Context, PRD, FSD, Stories, SDD, Plan. Each runs its "
                         "decision gate, authors the specification object, injects it into the shared template, "
                         "applies the host design system, and runs the validator. Each enforces its upstream "
                         "prerequisite by refusal. Shares the template and runtime with every other generator."},
    {"name": "Skill chain & plugin", "kind": "Plugin manifest + skill definitions",
     "responsibilities": "The named entry points the method is operated through — one skill per document type "
                         "plus resume, build, update, ship and the shared clarification interview — packaged and "
                         "version-pinned as a single installable plugin. All manual-trigger only except "
                         "clarification."},
    {"name": "Document template", "kind": "Static asset",
     "responsibilities": "The structural markup, styling and runtime shared by every document type. Never forked "
                         "per project; all per-project variation lives in the specification object and the "
                         "swappable style block."},
    {"name": "Plan generator", "kind": "Script",
     "responsibilities": "Reads canonical plan data plus every upstream specification's embedded JSON, builds the "
                         "requirement catalogues, computes coverage and dependency waves, and emits the plan index "
                         "and one document per milestone."},
    {"name": "Validator suite", "kind": "Scripts",
     "responsibilities": "Schema validation per document type; structural validation of rendered plan documents; "
                         "the coverage gate; optional rendered-view check."},
    {"name": "Status write-back tool", "kind": "Command-line tool",
     "responsibilities": "Locates a unit in a plan document's embedded specification, sets its status, ticks named "
                         "criteria, and rewrites only that JSON block."},
    {"name": "Orchestrator", "kind": "Agent skill",
     "responsibilities": "Reads the plan index, walks the waves, dispatches one worker per ready unit with that "
                         "unit's generated prompt, enforces the collision rules, collects reports, and drives the "
                         "retrospective at each milestone close."},
]

DATA_MODEL = [
    {"name": "Document envelope", "points": [
        "Every specification object carries a `document` block: title, slug, type, version, status, date, owner, "
        "release scope, summary, scope note.",
        "`slug` is the namespace for any browser-local state the document stores; it must be unique across the set.",
        "The envelope is identical across all seven document types; everything else varies by type."]},
    {"name": "Catalogue entries", "points": [
        "A catalogue entry is any item bearing an identifier: requirement, story, use case, decision, milestone, "
        "phase, task, criterion.",
        "Identifiers are uppercase, hyphen-separated, and end in a zero-padded ordinal.",
        "Every entry may carry `traces`, a map from upstream kind to a list of upstream identifiers."]},
    {"name": "Plan hierarchy", "points": [
        "Milestone contains phases; phase contains tasks; task contains criteria.",
        "Identifiers nest: a phase identifier extends its milestone's, a task identifier extends its phase's, a "
        "criterion identifier extends its task's.",
        "Status is stored on tasks and milestones; phase and programme status are derived, never stored."]},
    {"name": "Derived data", "points": [
        "Coverage matrix, dependency waves, phase rollups and the ready set are all computed at generation or read "
        "time and never stored as authored data.",
        "Storing a derived value is a defect: it can disagree with what it was derived from."]},
]

CROSSCUTTING = [
    {"name": "Determinism", "points": [
        "Generators must not consult the wall clock or a random source; dates come from authored data.",
        "Key ordering in emitted JSON is stable so that a regeneration diff shows only real change."]},
    {"name": "Failure handling", "points": [
        "Validators collect every failure and report them together; they never stop at the first.",
        "A worker retries a failing unit a bounded number of times, then records a blocker and yields.",
        "A missing optional input degrades to a documented reduced output, never to a silent partial one."]},
    {"name": "Provenance", "points": [
        "Any load-bearing claim in a report names the command, path or address it came from and the date the "
        "source itself reports.",
        "Another worker's output is never treated as a primary source; a verification pass must not read the "
        "artefact it verifies or that artefact's own sources."]},
    {"name": "Secrets", "points": [
        "Secrets are referenced by variable name only, in documents, prompts, ledgers and commits alike.",
        "Units that need a live credential are classified human-gated and excluded from unattended execution."]},
    {"name": "Concurrency", "points": [
        "Two units that write the same path are never dispatched together.",
        "Where isolation is needed, each worker gets its own working copy, discarded if unchanged."]},
    {"name": "Context durability", "points": [
        "The run ledger, not the agent's working memory, is authoritative for done-state and next step.",
        "Any run expected to exceed one hour opens its ledger before the first unit of work, not at the point of "
        "memory pressure."]},
]

DECISIONS = [
    {"id": "ADR-01", "title": "One self-contained file per document", "status": "Accepted",
     "context": "Specifications are read by people who do not have the project checked out, and by tools that do. "
                "A format needing a build step or a server is read by neither at the moment it matters.",
     "decision": "Every document is a single file that carries its own styling, its own runtime and its own data, "
                 "and functions when opened directly from a filesystem.",
     "alternatives": ["A static-site generator producing a documentation site — adds a build step and a host.",
                      "Plain text or lightweight markup — human-readable but not reliably machine-parseable.",
                      "A wiki or hosted document tool — loses version control and offline access."],
     "consequences": ["Documents can be emailed, archived, and opened years later without the toolchain.",
                      "Each file repeats its styling and runtime — a size cost accepted deliberately.",
                      "Shared changes to the template require regenerating every document."],
     "traces": {"fr": ["FR-SPC-03", "FR-SPC-01"]}},

    {"id": "ADR-02", "title": "The human view is rendered from the embedded specification", "status": "Accepted",
     "context": "Documents that carry both prose and structured data invariably drift: someone edits the prose and "
                "not the data, and downstream tools then act on stale facts.",
     "decision": "The specification object is the only content store. The readable document is constructed from it "
                 "in the browser at load time; there is no second copy of any fact.",
     "alternatives": ["Generate static markup from the data at build time — reintroduces a build step and lets "
                      "someone edit the output.",
                      "Keep prose authoritative and extract data from it — extraction is lossy and fragile."],
     "consequences": ["Drift between the two views becomes structurally impossible.",
                      "Reading the document requires a script-capable viewer.",
                      "Every visual change is a change to one shared runtime, not to N documents."],
     "traces": {"fr": ["FR-SPC-02", "FR-DOC-06"]}},

    {"id": "ADR-03", "title": "Identifiers are permanent", "status": "Accepted",
     "context": "Identifiers appear in traces, test names, commit messages, prompts and external references. Any "
                "renumbering invalidates all of them at once, silently.",
     "decision": "Identifiers are allocated once and never reused or renumbered. Removed items are retired in "
                 "place with a reason; gaps in numbering are expected and acceptable.",
     "alternatives": ["Renumber on each release for tidiness — breaks every existing reference.",
                      "Use opaque generated identifiers — stable, but unusable in conversation."],
     "consequences": ["Numbering becomes non-contiguous over time; this is a feature, not untidiness.",
                      "Traces remain valid across the whole life of the project.",
                      "Retired items must be rendered distinctly so they are not mistaken for live scope."],
     "traces": {"fr": ["FR-TRC-01", "FR-TRC-02"]}},

    {"id": "ADR-04", "title": "The plan is derived from the specifications", "status": "Accepted",
     "context": "A hand-written plan and a specification are two descriptions of the same intent, and they diverge "
                "from the first day. The divergence is invisible until something ships without being built.",
     "decision": "The plan generator reads the specifications' embedded JSON directly and fails if any requirement "
                 "is claimed by no unit of work. The plan cannot be produced from data that does not cover its "
                 "own inputs.",
     "alternatives": ["Maintain a separate traceability spreadsheet — a third artefact to keep in sync.",
                      "Review coverage manually at milestone boundaries — catches the gap after the cost."],
     "consequences": ["Coverage becomes a build failure rather than a review finding.",
                      "Adding a requirement forces an explicit scheduling decision.",
                      "The generator depends on the specifications' format, so the schema must be versioned."],
     "traces": {"fr": ["FR-PLN-02", "FR-TRC-04", "FR-TRC-05"]}},

    {"id": "ADR-05", "title": "Status lives inside the plan document", "status": "Accepted",
     "context": "Progress data usually lives in a tracker separate from the plan, so the plan describes intent and "
                "the tracker describes reality, and neither is complete.",
     "decision": "The plan document's embedded specification holds task status and criterion state. A small "
                 "command-line tool writes to it. There is no external tracker.",
     "alternatives": ["Synchronise to an issue tracker — two sources of truth and an integration to maintain.",
                      "Keep status in a side file — the rendered plan then shows stale state."],
     "consequences": ["The plan, the status board and the audit trail are one artefact.",
                      "Progress is reviewable as a change in version control.",
                      "Concurrent writers must be serialised; the write-back tool is not a database."],
     "traces": {"fr": ["FR-STA-02", "FR-STA-03"]}},

    {"id": "ADR-06", "title": "Every task states its failing test before any code exists", "status": "Accepted",
     "context": "A worker with no context cannot judge whether a task is done. 'Implement search' has no edge; "
                "'this named test currently fails and must pass' has a hard one.",
     "decision": "Every task is authored as a red/green/refactor triple during planning, and workers are required "
                 "to write the red test first and confirm it fails before writing the implementation.",
     "alternatives": ["Describe the desired behaviour and let the worker choose verification — inconsistent and "
                      "unverifiable after the fact.",
                      "Write tests after implementation — tests then encode the bug rather than the requirement."],
     "consequences": ["Planning is more expensive and execution is far cheaper and more reliable.",
                      "A task's completion is a machine fact, not a judgement call.",
                      "Tasks that resist a red step are usually badly scoped and get split."],
     "traces": {"fr": ["FR-PLN-04", "FR-EXE-04"]}},

    {"id": "ADR-07", "title": "Autonomy is classified per task", "status": "Accepted",
     "context": "Unattended runs die on the first prompt for a credential or a paid provider, and a run that "
                "cannot distinguish safe work from unsafe work either stalls or does something dangerous.",
     "decision": "Each task declares one of three autonomy classes: fully autonomous, autonomous against a "
                 "substituted provider, or human-gated. Unattended execution skips human-gated tasks and leaves "
                 "them blocked for a person.",
     "alternatives": ["Attempt everything and prompt when blocked — no one is there to answer.",
                      "Require human approval for everything — abandons the autonomy the method exists to provide."],
     "consequences": ["Unattended runs proceed to completion around human-gated work rather than stopping at it.",
                      "Human-gated work is visible up front as a prerequisite checklist.",
                      "Substituted providers must be maintained alongside the real ones."],
     "traces": {"fr": ["FR-PLN-07", "FR-EXE-05"]}},

    {"id": "ADR-08", "title": "Dependencies produce waves; waves produce parallelism", "status": "Accepted",
     "context": "Executing a plan strictly in order wastes the independence the dependency graph already "
                "describes; executing it greedily collides on shared files.",
     "decision": "The generator computes a topological wave ordering. Units inside a wave run concurrently; the "
                 "next wave begins only when the previous one is complete.",
     "alternatives": ["Fully greedy scheduling on the task graph — maximum parallelism, frequent collisions.",
                      "Strictly serial execution — safe, and needlessly slow."],
     "consequences": ["A simple, auditable schedule a human can read at a glance.",
                      "Some idle capacity at wave boundaries, accepted in exchange for collision safety.",
                      "A badly grouped wave shows up as file contention, which is the signal to re-group."],
     "traces": {"fr": ["FR-PLN-09", "FR-EXE-02", "FR-EXE-06"]}},

    {"id": "ADR-09", "title": "Validate the rendered artefact, not the source data", "status": "Accepted",
     "context": "A generator can be correct and still emit a broken file — a template regression, a bad "
                "substitution, a truncated write. Source-side validation cannot see any of it.",
     "decision": "Validators open the produced file, extract its embedded specification from the rendered output, "
                 "and assert structural invariants on that. Source-side schema checks are additional, not "
                 "sufficient.",
     "alternatives": ["Trust the generator and validate only its inputs — proves nothing about the deliverable.",
                      "Snapshot-test the whole file — brittle against every cosmetic change."],
     "consequences": ["The check proves the deliverable, which is what ships.",
                      "Validation runs after generation, so the build has two ordered stages.",
                      "Structural assertions must be written against the rendered shape, not the authored one."],
     "traces": {"fr": ["FR-VAL-02", "FR-VAL-04"]}},

    {"id": "ADR-10", "title": "One decision gate, before authoring", "status": "Accepted",
     "context": "Questions asked mid-build arrive when the answer is expensive: work already exists in the shape "
                "of the wrong assumption. Questions not asked at all become rework.",
     "decision": "Every fork is resolved in a single gate phase before any file is written, one question at a "
                 "time with a recommended default, and the outcome is written to a locked-decisions table that is "
                 "quoted verbatim into every worker's brief.",
     "alternatives": ["Ask as questions arise — cheap to implement, expensive in rework and interruptions.",
                      "Let the agent decide everything — produces confident answers to questions the owner cared "
                      "about."],
     "consequences": ["The owner's attention is concentrated in one short, high-value session.",
                      "Locked rows are closed: a worker that disagrees must surface a conflict, not re-decide.",
                      "A fork discovered mid-run is handled by the never-ask policy and recorded as a decision."],
     "traces": {"fr": ["FR-DOC-02", "FR-DOC-03", "FR-EXE-08"]}},

    {"id": "ADR-11", "title": "Generated plan documents are committed", "status": "Accepted",
     "context": "Generated files are normally excluded from version control. But these files carry status, and "
                "status history is the record of how the project actually went.",
     "decision": "Plan documents are committed on every status change, as a deliberate exception to the "
                 "usual rule, and the exception is documented where the ignore rules live.",
     "alternatives": ["Regenerate on demand and commit only the source data — loses the rendered history and "
                      "makes progress invisible in review.",
                      "Store status in a side file that is committed — splits one fact across two artefacts."],
     "consequences": ["Progress is diffable, reviewable and attributable.",
                      "Regeneration noise must be controlled by deterministic output, or diffs become unreadable.",
                      "Contributors must be told not to hand-edit these files."],
     "traces": {"fr": ["FR-STA-05", "FR-GEN-07"]}},

    {"id": "ADR-12", "title": "Extend by addendum, never by rewrite", "status": "Accepted",
     "context": "Scope arrives after a specification is stable. Editing the original invalidates published "
                "identifiers, traces and completed work.",
     "decision": "New scope is a new document with its own identifier prefix. The plan generator merges addendum "
                 "identifiers into the coverage universe and routes each trace link to the document that owns it. "
                 "Generation still succeeds when an addendum is absent.",
     "alternatives": ["Amend the original documents in place — breaks identifier stability.",
                      "Start a new document set per release — loses cross-release traceability."],
     "consequences": ["The specification set grows by accretion and stays readable.",
                      "Trace routing needs a prefix-to-document map, which must be maintained.",
                      "Readers must be told which document owns which prefix."],
     "traces": {"fr": ["FR-AMD-01", "FR-AMD-02", "FR-AMD-03"]}},

    {"id": "ADR-13", "title": "A worker that reports nothing has failed", "status": "Accepted",
     "context": "A dispatched worker that finishes quietly is indistinguishable from one that did nothing, and "
                "the orchestrator cannot tell the difference without re-deriving the work itself.",
     "decision": "Every worker brief specifies a mandatory structured report — changes, verification actually run, "
                 "blockers, and what the next worker must know. A worker returning no report is treated as failed "
                 "and its unit is not marked complete.",
     "alternatives": ["Infer completion from file changes — cannot distinguish partial from complete.",
                      "Trust the worker's own status write-back — a worker that failed may still write success."],
     "consequences": ["The orchestrator can act on reports rather than re-inspecting the repository.",
                      "Reports become the raw material for retrospectives.",
                      "The report contract must be enforced by the harness, not merely requested."],
     "traces": {"fr": ["FR-EXE-10", "FR-GEN-03"]}},

    {"id": "ADR-14", "title": "Retrospectives are inputs, not artefacts", "status": "Accepted",
     "context": "Retrospectives written and filed are ceremony. The same lesson then recurs in the next milestone "
                "at full cost.",
     "decision": "Each milestone writes a retrospective at close, and every subsequent worker is required to read "
                 "all prior retrospectives before starting. Recurring themes escalate to a change in the method.",
     "alternatives": ["Retrospective only at project end — too late to change anything.",
                      "No retrospectives — every wave repeats the previous wave's mistakes."],
     "consequences": ["Later waves are measurably cheaper than earlier ones.",
                      "Worker briefs grow over time and need periodic distillation into a conventions summary.",
                      "The method improves from its own operation."],
     "traces": {"fr": ["FR-LRN-01", "FR-LRN-02", "FR-LRN-04"]}},

    {"id": "ADR-15", "title": "The ledger outranks working memory", "status": "Accepted",
     "context": "Long autonomous runs lose context — compaction, restarts, crashes. State held only in an agent's "
                "working memory does not survive, and a resumed run that trusts memory repeats or skips work.",
     "decision": "A plain-text ledger outside version control records done-state, autonomous decisions, the exact "
                 "next step and how to resume. On any resume the ledger is read first and the ready set is "
                 "recomputed from the plan.",
     "alternatives": ["Rely on the agent's context — fails at the first interruption.",
                      "Store run state in the plan document — mixes durable specification with transient run detail."],
     "consequences": ["Interruption costs one iteration, not a run.",
                      "The ledger must be updated after every unit, which is a discipline cost.",
                      "Run state stays out of the repository, where it would be noise."],
     "traces": {"fr": ["FR-EXE-09", "FR-LRN-05"]}},

    {"id": "ADR-16", "title": "Documents adopt the host design system", "status": "Accepted",
     "context": "Specifications that look foreign to the project they describe read as external paperwork and are "
                "consulted less; documents with ad-hoc styling drift visually as they accumulate.",
     "decision": "Generators detect the host project's design tokens and inline them into a marked style block, "
                 "falling back to a neutral theme when none exists. Structural styling is shared and is never "
                 "edited per project.",
     "alternatives": ["One fixed house style for all projects — visually consistent, contextually foreign.",
                      "Free-form styling per document — immediate drift."],
     "consequences": ["Documents look like part of the product.",
                      "A design-system change requires regenerating documents to pick it up.",
                      "The token contract must be documented so any system can be mapped onto it."],
     "traces": {"fr": ["FR-GEN-02"]}},

    {"id": "ADR-17", "title": "No hosted service in this release", "status": "Accepted",
     "context": "Collaboration features — comments, presence, permissions — are the natural next request, and each "
                "one pulls the method toward a product with an operational burden.",
     "decision": "The method ships as files and scripts in a repository. Collaboration happens through version "
                 "control. No server, no accounts, no hosted state.",
     "alternatives": ["A hosted document portal — better reading experience, an operational commitment.",
                      "An editor plug-in — narrower audience, another surface to maintain."],
     "consequences": ["Zero operational cost and no data-residency question.",
                      "Review happens in pull requests rather than in the document.",
                      "Reader-local state, such as review ticks, cannot be shared between people."],
     "traces": {"fr": ["FR-GEN-09", "FR-GEN-10"]}},

    {"id": "ADR-18", "title": "The method is operated through named skills, shipped as one plugin",
     "status": "Accepted",
     "context": "The toolchain is a set of generators, validators and an orchestrator. Left as loose scripts, "
                "every adopter wires them differently, agents invoke them at the wrong moments, and the method's "
                "sequencing rules live only in documentation nobody re-reads.",
     "decision": "Each step is wrapped as a named, separately invocable agent skill. Skills are manual-trigger "
                 "only — the sole exception is the shared clarification skill, which may fire automatically when "
                 "a decision would otherwise be guessed. Each skill enforces its own upstream prerequisite by "
                 "refusal. The whole chain is distributed as a single installable plugin from a marketplace "
                 "reference.",
     "alternatives": ["Loose scripts plus a README — no sequencing enforcement, per-adopter wiring drift.",
                      "One monolithic skill with modes — a single entry point, but every invocation carries the "
                      "whole method's context and the steps cannot be versioned independently.",
                      "Automatic triggering by intent detection — convenient until a skill fires mid-task and "
                      "regenerates a document nobody asked for."],
     "consequences": ["Adoption is one install action; the chain's order is enforced by the skills themselves.",
                      "An operator can always answer 'what do I do next' by listing skill names.",
                      "The plugin becomes a versioned release artefact of the method, with a changelog.",
                      "Skill definitions must be kept in lock-step with the toolchain they wrap."],
     "traces": {"fr": ["FR-SKL-01", "FR-SKL-02", "FR-SKL-03", "FR-SKL-08", "FR-SKL-09"]}},
]

REQ_AREAS = [
    {"key": "NFR-ARC", "name": "Architecture & structure",
     "description": "How the toolchain is decomposed and what each part may depend on."},
    {"key": "NFR-DAT", "name": "Data contracts",
     "description": "The shape and rules of every specification object the method reads or writes."},
    {"key": "NFR-GEN", "name": "Generation & rendering",
     "description": "Constraints on the generators and the shared document runtime."},
    {"key": "NFR-VAL", "name": "Validation",
     "description": "What the validators must check, and how they must behave when they fail."},
    {"key": "NFR-EXE", "name": "Execution & orchestration",
     "description": "Constraints on the autonomous run: scheduling, isolation, recovery, reporting."},
    {"key": "NFR-SEC", "name": "Safety & secrets",
     "description": "What must never leave the machine, and what must never run unattended."},
    {"key": "NFR-PRF", "name": "Performance & size",
     "description": "Budgets for generation time, validation time and artefact size."},
    {"key": "NFR-UX", "name": "Document usability & accessibility",
     "description": "The floor for readability, keyboard access and assistive-technology support."},
    {"key": "NFR-OPS", "name": "Repository & operations",
     "description": "How the method lives inside a project: layout, branches, continuous integration."},
    {"key": "NFR-EVO", "name": "Versioning & evolution",
     "description": "How schemas, templates and the method itself change without breaking existing artefacts."},
    {"key": "NFR-SKL", "name": "Skill packaging & interface",
     "description": "Constraints on how the chain's named entry points are defined, triggered and distributed."},
]

REQUIREMENTS = [
    # NFR-ARC
    {"id": "NFR-ARC-01", "area": "NFR-ARC", "priority": "Must", "title": "One generator per document type",
     "text": "Each document type shall be produced by its own independently invocable generator, sharing the "
             "template and runtime but owning its schema, its gate questions and its validator rules.",
     "traces": {"fr": ["FR-DOC-01"], "adr": ["ADR-01"]}},
    {"id": "NFR-ARC-02", "area": "NFR-ARC", "priority": "Must", "title": "Downstream-only dependencies",
     "text": "A generator may read documents earlier in the chain and shall never read documents later in it. The "
             "plan generator reads specifications; no specification generator reads the plan.",
     "notes": "A cycle here would make the coverage gate unfalsifiable.",
     "traces": {"fr": ["FR-DOC-01", "FR-PLN-02"]}},
    {"id": "NFR-ARC-03", "area": "NFR-ARC", "priority": "Must", "title": "No third-party runtime dependencies",
     "text": "Generators and validators shall use only their language's standard library, and the document runtime "
             "shall use only browser built-ins.",
     "notes": "A dependency-free toolchain still runs in five years and inside a restricted environment.",
     "traces": {"fr": ["FR-SPC-03", "FR-GEN-01"], "adr": ["ADR-01"]}},
    {"id": "NFR-ARC-04", "area": "NFR-ARC", "priority": "Must", "title": "Template is never forked",
     "text": "The shared document template shall not be copied or modified per project; all per-project variation "
             "shall live in the specification object and the marked style block.",
     "traces": {"fr": ["FR-GEN-02"], "adr": ["ADR-16"]}},
    {"id": "NFR-ARC-05", "area": "NFR-ARC", "priority": "Should", "title": "Separable adoption",
     "text": "A project shall be able to adopt the specification chain without the autonomous execution layer, and "
             "the execution layer shall function against any plan matching the plan schema.",
     "traces": {"fr": ["FR-GEN-01"]}},
    {"id": "NFR-ARC-06", "area": "NFR-ARC", "priority": "Should", "title": "Canonical plan data separated from detail",
     "text": "The plan spine — milestones, dependencies, exit criteria, legend — shall live in one canonical "
             "module, and per-milestone detail shall live in separate files loaded by identifier, so that "
             "milestones can be authored independently.",
     "traces": {"fr": ["FR-PLN-01", "FR-PLN-02"]}},

    # NFR-DAT
    {"id": "NFR-DAT-01", "area": "NFR-DAT", "priority": "Must", "title": "Stable embedding contract",
     "text": "Each document type shall embed its specification under a documented, type-specific element "
             "identifier that does not change between versions of the toolchain.",
     "notes": "Every downstream reader keys off this identifier.",
     "traces": {"fr": ["FR-SPC-01"], "adr": ["ADR-02"]}},
    {"id": "NFR-DAT-02", "area": "NFR-DAT", "priority": "Must", "title": "Valid, self-describing JSON",
     "text": "The embedded specification shall be a single valid JSON object carrying its own document type and "
             "schema version, extractable without executing the document.",
     "traces": {"fr": ["FR-SPC-01", "FR-SPC-04"]}},
    {"id": "NFR-DAT-03", "area": "NFR-DAT", "priority": "Must", "title": "Identifier grammar",
     "text": "Identifiers shall match a documented pattern per type: requirement and story identifiers as prefix, "
             "area and zero-padded ordinal; plan identifiers nesting milestone, phase, task and criterion.",
     "traces": {"fr": ["FR-TRC-01"], "adr": ["ADR-03"]}},
    {"id": "NFR-DAT-04", "area": "NFR-DAT", "priority": "Must", "title": "Closed enumerations",
     "text": "Priority, status, criterion kind, autonomy class and verification layer shall each be a closed "
             "enumeration defined once in the legend and referenced by identifier everywhere else.",
     "traces": {"fr": ["FR-STA-01", "FR-PLN-06", "FR-PLN-07"]}},
    {"id": "NFR-DAT-05", "area": "NFR-DAT", "priority": "Must", "title": "No derived data stored",
     "text": "Coverage, waves, rollups and ready sets shall be computed and never stored in an authored document, "
             "so that stored data cannot disagree with what it was derived from.",
     "traces": {"fr": ["FR-TRC-04", "FR-PLN-09", "FR-STA-04"]}},
    {"id": "NFR-DAT-06", "area": "NFR-DAT", "priority": "Should", "title": "Optional sections omitted, not empty",
     "text": "A section with no content shall be absent from the specification object rather than present and "
             "empty, and the renderer shall omit its heading entirely.",
     "traces": {"fr": ["FR-DOC-04"]}},
    {"id": "NFR-DAT-07", "area": "NFR-DAT", "priority": "Should", "title": "Constrained inline markup",
     "text": "Authored prose shall support only bold, inline code and links as inline markup; all other structure "
             "shall be expressed as data.",
     "notes": "Keeps prose parseable and prevents markup from becoming a second, informal schema.",
     "traces": {"fr": ["FR-SPC-02"]}},
    {"id": "NFR-DAT-08", "area": "NFR-DAT", "priority": "Should", "title": "Traces are typed",
     "text": "A trace map shall key upstream references by kind, so a consumer can distinguish a functional trace "
             "from a technical one without parsing identifier prefixes.",
     "traces": {"fr": ["FR-TRC-03", "FR-TRC-07"]}},

    # NFR-GEN
    {"id": "NFR-GEN-01", "area": "NFR-GEN", "priority": "Must", "title": "Deterministic output",
     "text": "Generating twice from unchanged inputs shall produce byte-identical files; generators shall not read "
             "the clock, a random source, or unordered collection iteration order.",
     "traces": {"fr": ["FR-GEN-07"], "adr": ["ADR-11"]}},
    {"id": "NFR-GEN-02", "area": "NFR-GEN", "priority": "Must", "title": "Generation is atomic per file",
     "text": "A document shall be written completely or not at all; a failed generation shall leave the previous "
             "file untouched.",
     "traces": {"fr": ["FR-VAL-05"]}},
    {"id": "NFR-GEN-03", "area": "NFR-GEN", "priority": "Must", "title": "Token-only styling",
     "text": "Generated styling shall reference design tokens exclusively; no colour, font, shadow or spacing "
             "value shall be hard-coded outside the token block.",
     "traces": {"fr": ["FR-GEN-02"], "adr": ["ADR-16"]}},
    {"id": "NFR-GEN-04", "area": "NFR-GEN", "priority": "Must", "title": "Renderer degrades on unknown sections",
     "text": "The runtime shall render an explicit placeholder for a section type it does not recognise, and shall "
             "continue rendering the rest of the document.",
     "notes": "A newer specification opened in an older document must not produce a blank page.",
     "traces": {"fr": ["FR-SPC-02"]}},
    {"id": "NFR-GEN-05", "area": "NFR-GEN", "priority": "Must", "title": "Escaping",
     "text": "All authored content shall be escaped before insertion into the document, with only the constrained "
             "inline markup expanded.",
     "traces": {"fr": ["FR-SPC-02"], "nfr": ["NFR-DAT-07"]}},
    {"id": "NFR-GEN-06", "area": "NFR-GEN", "priority": "Should", "title": "Section numbering is derived",
     "text": "Section numbers shall be computed from document order at render time and never authored, so that "
             "inserting a section cannot produce a duplicate or missing number.",
     "traces": {"fr": ["FR-SPC-09"]}},
    {"id": "NFR-GEN-07", "area": "NFR-GEN", "priority": "Should", "title": "Reader state is namespaced",
     "text": "Browser-local reader state shall be namespaced by method and document slug, so that several "
             "documents from several projects can coexist in one browser.",
     "traces": {"fr": ["FR-SPC-08"]}},

    # NFR-VAL
    {"id": "NFR-VAL-01", "area": "NFR-VAL", "priority": "Must", "title": "Exhaustive failure reporting",
     "text": "A validator shall report every failure it finds in a single run, grouped by document, and shall not "
             "stop at the first.",
     "traces": {"fr": ["FR-VAL-01", "FR-VAL-05"]}},
    {"id": "NFR-VAL-02", "area": "NFR-VAL", "priority": "Must", "title": "Extract from the rendered file",
     "text": "Structural validation shall read the produced file and extract its embedded specification from the "
             "rendered output, never from the generator's in-memory data.",
     "traces": {"fr": ["FR-VAL-02"], "adr": ["ADR-09"]}},
    {"id": "NFR-VAL-03", "area": "NFR-VAL", "priority": "Must", "title": "Coverage gate is blocking",
     "text": "The coverage gate shall fail generation, listing every unclaimed identifier, and shall not be "
             "downgradable to a warning by configuration. An identifier claimed only by a deferred milestone shall "
             "pass and be listed as a warning; deferral is a property of the claiming milestone, not a "
             "configuration of the gate.",
     "traces": {"fr": ["FR-TRC-05"], "adr": ["ADR-04"]}},
    {"id": "NFR-VAL-04", "area": "NFR-VAL", "priority": "Must", "title": "Exceptions are declared in code",
     "text": "Any approved exception to a validation rule shall be expressed in the validator itself with its "
             "justification, scoped as narrowly as possible, and reported as a warning on every run.",
     "traces": {"fr": ["FR-VAL-08"]}},
    {"id": "NFR-VAL-05", "area": "NFR-VAL", "priority": "Must", "title": "Honest reporting of skipped checks",
     "text": "A check that could not run shall be reported as skipped with the reason, and shall never be counted "
             "as passed in any summary.",
     "traces": {"fr": ["FR-VAL-07", "FR-GEN-03"]}},
    {"id": "NFR-VAL-06", "area": "NFR-VAL", "priority": "Should", "title": "Validation is fast enough to be habitual",
     "text": "Validating a complete document set shall finish quickly enough to run on every save without "
             "friction — a small number of seconds, not minutes.",
     "traces": {"fr": ["FR-VAL-01"]}},

    # NFR-EXE
    {"id": "NFR-EXE-01", "area": "NFR-EXE", "priority": "Must", "title": "Ready set recomputed, never cached",
     "text": "The ready set shall be recomputed from the plan at the start of every iteration, so that an "
             "interruption or an external edit cannot leave the run acting on stale eligibility.",
     "traces": {"fr": ["FR-EXE-01", "FR-EXE-09"], "adr": ["ADR-15"]}},
    {"id": "NFR-EXE-02", "area": "NFR-EXE", "priority": "Must", "title": "One unit per worker",
     "text": "A dispatched worker shall own exactly one unit of work and shall not opportunistically complete "
             "adjacent units.",
     "notes": "Keeps status truthful and keeps collisions predictable.",
     "traces": {"fr": ["FR-EXE-03", "FR-EXE-06"]}},
    {"id": "NFR-EXE-03", "area": "NFR-EXE", "priority": "Must", "title": "Write-set disjointness",
     "text": "Units dispatched concurrently shall have disjoint write sets; where disjointness cannot be "
             "established, the units shall be serialised or isolated in separate working copies.",
     "traces": {"fr": ["FR-EXE-06"], "adr": ["ADR-08"]}},
    {"id": "NFR-EXE-04", "area": "NFR-EXE", "priority": "Must", "title": "Self-contained briefs",
     "text": "A worker brief shall contain everything needed to act — plan path, unit identifier, locked "
             "decisions, conventions, verification gauntlet, report contract — and shall assume no inherited "
             "context.",
     "traces": {"fr": ["FR-EXE-03"], "adr": ["ADR-10"]}},
    {"id": "NFR-EXE-05", "area": "NFR-EXE", "priority": "Must", "title": "Bounded retries",
     "text": "A worker shall attempt a failing unit a bounded, stated number of times before recording a blocker "
             "and yielding; unbounded retry is prohibited.",
     "traces": {"fr": ["FR-EXE-07"]}},
    {"id": "NFR-EXE-06", "area": "NFR-EXE", "priority": "Must", "title": "Report contract enforced",
     "text": "The absence of a structured worker report shall be treated as failure by the harness, not merely "
             "noted, and the unit shall not be marked complete.",
     "traces": {"fr": ["FR-EXE-10"], "adr": ["ADR-13"]}},
    {"id": "NFR-EXE-07", "area": "NFR-EXE", "priority": "Must", "title": "Ledger written before advancing",
     "text": "The ledger shall be updated with done-state, decisions and the exact next step before the "
             "orchestrator advances to the next unit.",
     "traces": {"fr": ["FR-LRN-05", "FR-EXE-09"], "adr": ["ADR-15"]}},
    {"id": "NFR-EXE-08", "area": "NFR-EXE", "priority": "Must", "title": "No interactive prompts unattended",
     "text": "No unattended unit shall invoke a command that waits for terminal input, opens an interactive "
             "authentication flow, or requires an approval the run cannot grant.",
     "traces": {"fr": ["FR-EXE-05", "FR-EXE-08"], "adr": ["ADR-07"]}},
    {"id": "NFR-EXE-09", "area": "NFR-EXE", "priority": "Should", "title": "Concurrency ceiling",
     "text": "Concurrent workers shall be capped at four by default, configurable per project and further bounded "
             "by available machine capacity, with excess work queued rather than refused.",
     "notes": "The binding constraint is review capacity, not machine capacity: four workers produce a wave one "
              "person can read in one sitting. A higher cap turns review into rubber-stamping, which voids the "
              "human-gate guarantees the method depends on.",
     "traces": {"fr": ["FR-EXE-02"]}},
    {"id": "NFR-EXE-10", "area": "NFR-EXE", "priority": "Should", "title": "Verification before status change",
     "text": "A unit's status shall be set to passing only after the verification layers it names have actually "
             "run and passed in the run that is setting it.",
     "traces": {"fr": ["FR-STA-03", "FR-GEN-03"]}},
    {"id": "NFR-EXE-11", "area": "NFR-EXE", "priority": "Should", "title": "Atomic commits per unit",
     "text": "Each unit's work shall be committed as one commit naming the unit identifier, with generated plan "
             "documents included in the same commit as the work they describe.",
     "traces": {"fr": ["FR-EXE-11", "FR-STA-05"], "adr": ["ADR-11"]}},

    # NFR-SEC
    {"id": "NFR-SEC-01", "area": "NFR-SEC", "priority": "Must", "title": "No secret values in any artefact",
     "text": "No document, plan, prompt, ledger, report or commit shall contain a credential value; secrets shall "
             "appear only as variable names.",
     "traces": {"fr": ["FR-GEN-04"]}},
    {"id": "NFR-SEC-02", "area": "NFR-SEC", "priority": "Must", "title": "Substituted providers unattended",
     "text": "Unattended work that would otherwise call an external provider shall run against a substitute, and "
             "the substitution shall be named in the task rather than improvised by the worker.",
     "traces": {"fr": ["FR-EXE-05"], "adr": ["ADR-07"]}},
    {"id": "NFR-SEC-03", "area": "NFR-SEC", "priority": "Must", "title": "Human-gated work is never attempted",
     "text": "A human-gated unit shall be skipped and left blocked; an unattended run shall not attempt it, and "
             "shall not mark it complete on any basis.",
     "traces": {"fr": ["FR-PLN-07", "FR-EXE-05"]}},
    {"id": "NFR-SEC-04", "area": "NFR-SEC", "priority": "Must", "title": "No destructive operations unattended",
     "text": "Unattended runs shall not force-push, rewrite shared history, delete branches with unmerged work, or "
             "delete files outside their own working area.",
     "traces": {"fr": ["FR-EXE-12"]}},
    {"id": "NFR-SEC-05", "area": "NFR-SEC", "priority": "Should", "title": "Denied permission stops the probe",
     "text": "A permission denial shall be reported as a gate with the rule that blocked it, and shall not be "
             "retried in a different form.",
     "notes": "Reshaping a denied action to slip past a gate is prohibited, not merely discouraged.",
     "traces": {"fr": ["FR-GEN-03"]}},

    # NFR-PRF
    {"id": "NFR-PRF-01", "area": "NFR-PRF", "priority": "Should", "title": "Generation time budget",
     "text": "Generating a complete document set shall complete in seconds on ordinary hardware, so that "
             "regeneration is never a reason to hand-edit output.",
     "traces": {"fr": ["FR-DOC-06"]}},
    {"id": "NFR-PRF-02", "area": "NFR-PRF", "priority": "Should", "title": "Document size budget",
     "text": "A generated document shall stay small enough to open instantly from a filesystem and to review in a "
             "version-control diff; a document exceeding the budget shall be split.",
     "traces": {"fr": ["FR-SPC-03"]}},
    {"id": "NFR-PRF-03", "area": "NFR-PRF", "priority": "Should", "title": "Interaction responsiveness",
     "text": "Filtering, expanding and navigating shall respond within one animation frame for catalogues of "
             "several hundred entries.",
     "traces": {"fr": ["FR-SPC-05"]}},
    {"id": "NFR-PRF-04", "area": "NFR-PRF", "priority": "Could", "title": "Large-catalogue strategy",
     "text": "Beyond roughly a thousand catalogue entries the renderer could virtualise its lists rather than "
             "rendering every entry.",
     "traces": {"fr": ["FR-SPC-05"]}},

    # NFR-UX
    {"id": "NFR-UX-01", "area": "NFR-UX", "priority": "Must", "title": "Keyboard operable",
     "text": "Every interactive control shall be reachable and operable by keyboard, with a visible focus "
             "indicator that meets the host project's contrast target.",
     "traces": {"fr": ["FR-GEN-06"]}},
    {"id": "NFR-UX-02", "area": "NFR-UX", "priority": "Must", "title": "Respect reduced motion",
     "text": "All animation shall be suppressed when the reader has expressed a reduced-motion preference.",
     "traces": {"fr": ["FR-GEN-06"]}},
    {"id": "NFR-UX-03", "area": "NFR-UX", "priority": "Must", "title": "Contrast floor",
     "text": "Body text, identifiers and status indicators shall meet the contrast level the host project targets, "
             "and status shall never be conveyed by colour alone.",
     "traces": {"fr": ["FR-GEN-06"]}},
    {"id": "NFR-UX-04", "area": "NFR-UX", "priority": "Should", "title": "Readable at one glance",
     "text": "A reader shall be able to determine a document's type, version, status and scope without scrolling.",
     "traces": {"fr": ["FR-DOC-08"]}},
    {"id": "NFR-UX-05", "area": "NFR-UX", "priority": "Should", "title": "Responsive layout",
     "text": "Documents shall remain usable from a narrow phone viewport to a wide desktop one, with no horizontal "
             "scrolling of body content.",
     "traces": {"fr": ["FR-SPC-03"]}},
    {"id": "NFR-UX-06", "area": "NFR-UX", "priority": "Should", "title": "Plain-language floor",
     "text": "Reader-facing prose shall avoid internal tool names and undefined jargon; any unavoidable term shall "
             "be defined where it first appears.",
     "traces": {"fr": ["FR-GEN-05"]}},

    # NFR-OPS
    {"id": "NFR-OPS-01", "area": "NFR-OPS", "priority": "Must", "title": "Documented repository layout",
     "text": "The method shall define where specifications, plan data, generated plans, retrospectives and the "
             "ledger live, and shall not scatter them across the tree.",
     "traces": {"fr": ["FR-GEN-01"]}},
    {"id": "NFR-OPS-02", "area": "NFR-OPS", "priority": "Must", "title": "Gates run in continuous integration",
     "text": "Schema validation, structural validation and the coverage gate shall run on every change, and shall "
             "block integration on failure.",
     "traces": {"fr": ["FR-VAL-05"]}},
    {"id": "NFR-OPS-03", "area": "NFR-OPS", "priority": "Must", "title": "Three branch tiers",
     "text": "Work shall flow from short-lived unit branches into one shared integration branch, and from there to "
             "production by an explicit promotion; nothing shall be committed directly to production.",
     "traces": {"fr": ["FR-EXE-12"]}},
    {"id": "NFR-OPS-04", "area": "NFR-OPS", "priority": "Must", "title": "Ledger excluded from version control",
     "text": "The run ledger shall be excluded from version control as transient run state, while plan documents "
             "shall be included despite being generated.",
     "traces": {"fr": ["FR-STA-05", "FR-LRN-05"], "adr": ["ADR-11", "ADR-15"]}},
    {"id": "NFR-OPS-05", "area": "NFR-OPS", "priority": "Should", "title": "Promotion is human-approved",
     "text": "Promotion from the integration branch to production shall require a human to have read the change "
             "and approved it, regardless of how green the automated gates are, and shall additionally require "
             "that the rendered-view check has actually run and passed on the documents being promoted.",
     "notes": "The render check is optional in everyday integration (NFR-VAL-05 governs how a skip is reported) "
              "and mandatory here, where a person and a browser are both already in the loop.",
     "traces": {"fr": ["FR-PLN-06", "FR-VAL-07"]}},
    {"id": "NFR-OPS-06", "area": "NFR-OPS", "priority": "Should", "title": "Generated files marked",
     "text": "Generated files shall be marked as generated in version-control metadata so that reviews collapse "
             "them by default while keeping them in history.",
     "traces": {"fr": ["FR-STA-05"]}},

    # NFR-EVO
    {"id": "NFR-EVO-01", "area": "NFR-EVO", "priority": "Must", "title": "Versioned schemas, enforced on read",
     "text": "Every specification schema shall carry a version, and a change that invalidates existing documents "
             "shall increment the major component. A tool that reads a document whose schema major differs from "
             "its own shall refuse, naming both versions and the document; a minor difference shall be reported as "
             "a warning and reading shall continue. A tool that rewrites a document — the status write-back tool — "
             "shall refuse on any version difference, major or minor.",
     "notes": "The asymmetry is deliberate: reading a document you only partly understand costs a warning, while "
              "rewriting one can corrupt the single artefact holding all recorded progress. Document runtimes are "
              "governed separately by NFR-EVO-02 and NFR-GEN-04, which require rendering rather than refusal.",
     "traces": {"fr": ["FR-AMD-01", "FR-VAL-01"], "adr": ["ADR-12"]}},
    {"id": "NFR-EVO-02", "area": "NFR-EVO", "priority": "Must", "title": "Backward-compatible rendering",
     "text": "The runtime shall render documents authored against any earlier minor version of its schema without "
             "error.",
     "traces": {"fr": ["FR-SPC-02"], "nfr": ["NFR-GEN-04"]}},
    {"id": "NFR-EVO-03", "area": "NFR-EVO", "priority": "Must", "title": "Prefix routing for addenda",
     "text": "The plan generator shall map identifier prefixes to the documents that define them, so a trace link "
             "resolves to the right addendum, shall generate successfully when an addendum is absent, and shall "
             "fail — naming both documents and the prefix — when two documents declare the same prefix.",
     "notes": "The map must be injective. A shared prefix makes ownership unresolvable, so it is rejected at "
              "generation rather than resolved by precedence.",
     "traces": {"fr": ["FR-AMD-02", "FR-AMD-03"], "adr": ["ADR-12"]}},
    {"id": "NFR-EVO-04", "area": "NFR-EVO", "priority": "Should", "title": "Method changes are versioned",
     "text": "A change to the method itself shall be released as a version of the toolchain with its own "
             "retrospective-driven rationale, not applied silently to running projects.",
     "traces": {"fr": ["FR-LRN-04"], "adr": ["ADR-14"]}},
    {"id": "NFR-EVO-05", "area": "NFR-EVO", "priority": "Should", "title": "Amendment annotations preserved",
     "text": "When a requirement is amended in place, the annotation and its date shall be preserved through every "
             "subsequent regeneration.",
     "traces": {"fr": ["FR-AMD-04"]}},

    # NFR-SKL
    {"id": "NFR-SKL-01", "area": "NFR-SKL", "priority": "Must", "title": "Trigger policy lives in the definition",
     "text": "Each skill's definition shall declare its trigger policy where the agent runtime enforces it: every "
             "chain skill marked manual-invocation only, and the clarification skill alone carrying explicit, "
             "tuned instructions for when it must fire automatically.",
     "notes": "A trigger rule stated only in documentation is a request; one stated in the definition is a "
              "contract.",
     "traces": {"fr": ["FR-SKL-03", "FR-SKL-04"], "adr": ["ADR-18"]}},
    {"id": "NFR-SKL-02", "area": "NFR-SKL", "priority": "Must", "title": "Prerequisite probes are read-only",
     "text": "A skill's prerequisite check shall read the document set without side effects, and a refusal shall "
             "leave the repository byte-for-byte untouched.",
     "traces": {"fr": ["FR-SKL-02"], "adr": ["ADR-18"]}},
    {"id": "NFR-SKL-03", "area": "NFR-SKL", "priority": "Should", "title": "The plugin pins versions",
     "text": "The plugin shall pin the version of every skill it ships, and an install from the marketplace "
             "reference shall be reproducible: the same reference resolves to the same skill set.",
     "traces": {"fr": ["FR-SKL-08"], "adr": ["ADR-18"]}},
    {"id": "NFR-SKL-04", "area": "NFR-SKL", "priority": "Must", "title": "No manual shell steps",
     "text": "Every shell-level mechanic a method step needs — creating directories, writing ignore rules, "
             "recording status, committing generated output, running live checks — shall be executed by the "
             "skill that needs it. The operator's whole interface is skill invocations and interview answers.",
     "notes": "A step whose instructions ask the operator to type a shell command is a defect in that step, "
              "not a convenience.",
     "traces": {"fr": ["FR-SKL-09"], "adr": ["ADR-18"]}},
]

TARGETS = [
    {"metric": "Requirements unclaimed by any unit of work", "target": "Zero", "notes": "Enforced by the coverage gate; a non-zero count fails generation."},
    {"metric": "Traces resolving to a non-existent identifier", "target": "Zero", "notes": "Enforced by validation."},
    {"metric": "Tasks without a machine-checkable criterion", "target": "Zero", "notes": "Documented exceptions only, reported as warnings."},
    {"metric": "Full document-set generation", "target": "Under 10 seconds", "notes": "Ordinary developer hardware, cold start."},
    {"metric": "Full validation pass", "target": "Under 10 seconds", "notes": "So it can run on save and in every commit hook."},
    {"metric": "Single document size", "target": "Under 2048 KB", "notes": "Raised from 250 KB, then to 2048 KB, by the owner on 2026-08-15. The old figure was never a decision anybody made. A plan that carries its own execution instructions at four granularities is several hundred KB of quoted prompt by design — the plan below is 173 prompts — and the alternative was to split it into one document per milestone, which was weighed and declined in favour of keeping one file. Beyond this, split the document rather than compress it."},
    {"metric": "Filter response on 500 entries", "target": "Under 16 ms", "notes": "One animation frame."},
    {"metric": "Unattended units needing human rescue", "target": "Under 1 in 20", "notes": "Higher rates indicate tasks scoped too large or autonomy misclassified."},
    {"metric": "Retrospective themes recurring three times", "target": "Escalated to a method change", "notes": "Tracked per run."},
    {"metric": "Documents hand-edited after generation", "target": "Zero", "notes": "Detected by regenerating and diffing in continuous integration."},
]

RISKS = [
    {"risk": "Planning depth is front-loaded and can feel disproportionate before any code exists.",
     "mitigation": "Author milestone detail one wave ahead rather than all at once; the spine and the first wave "
                   "are enough to start."},
    {"risk": "A specification defect propagates into every derived artefact.",
     "mitigation": "The decision gate plus adversarial review of the specification before the plan is generated; "
                   "amendment by addendum keeps the correction cheap."},
    {"risk": "Autonomous workers report success on work that does not function.",
     "mitigation": "Status may only be set after the named verification layers actually run; reports must state "
                   "which command produced which result."},
    {"risk": "Coverage becomes a formality — requirements claimed by a token task.",
     "mitigation": "Every task carries a failing-test definition; a claim with no red step is visible in review."},
    {"risk": "Generated plan documents create noisy version-control diffs.",
     "mitigation": "Deterministic generation and stable key ordering; generated files marked so reviews collapse "
                   "them."},
    {"risk": "The template accumulates project-specific special cases.",
     "mitigation": "Per-project variation is confined to the specification object and the style block; changes to "
                   "structural styling require a method version."},
    {"risk": "Concurrency causes silent file collisions that corrupt work.",
     "mitigation": "Write-set disjointness is checked before dispatch; contention is reported rather than retried."},
    {"risk": "The method is adopted partially — documents without gates — and blamed for the resulting drift.",
     "mitigation": "The gates are the method; adoption guidance names the minimum viable subset explicitly."},
]

OPEN_QUESTIONS = []

SCHEMAS = [
    {"title": "Document envelope — present in every specification object", "code": """{
  "document": {
    "title":        "Acme — Functional Specification Document",   // required
    "slug":         "fsd",              // required · namespace for reader-local state
    "type":         "Functional Specification Document (FSD)",    // required
    "version":      "1.0",              // required
    "status":       "Draft for review", // required
    "date":         "YYYY-MM-DD",       // required
    "owner":        "name or role",     // required
    "releaseScope": "v1 (MVP)",         // optional
    "summary":      "One-line lead shown under the title.",       // optional
    "scopeNote":    "What this document does and does not cover." // optional
  },
  "schemaVersion": "1.0",               // required · major change invalidates readers
  "sections":  [ /* ordered render instructions — see below */ ],
  "siblings":  [ { "label": "FSD", "href": "Z2S-FSD.html", "current": true } ],
  "links":     { "FR-DOC": "Z2S-FSD.html", "NFR-ARC": "Z2S-SDD.html" }
}"""},
    {"title": "Requirement entry — FSD and SDD catalogues", "code": """{
  "id":       "FR-DOC-01",     // required · unique · <PREFIX>-<AREA>-<NN>
  "area":     "FR-DOC",        // required · must match a declared area key
  "priority": "Must",          // required · Must | Should | Could | Won't
  "title":    "Seven document types",        // required · short label
  "text":     "The system shall …",          // required · observable behaviour
  "notes":    "Cross-references and caveats.",           // optional
  "tags":     ["chain"],                                 // optional
  "traces":   { "fr": ["FR-SPC-01"], "adr": ["ADR-04"] } // optional · typed upward links
}"""},
    {"title": "Context document — bounded contexts and the glossary", "code": """{
  "contexts": [                        // BC-* · the domain's named boundaries
    { "id": "BC-01", "name": "…", "desc": "…",
      "owns": [ "Term", "Term" ] }     // canonical terms this context owns
  ],
  "glossary": [                        // UL-* · one entry per canonical term
    { "id": "UL-01",
      "term": "…",                     // the canonical term, in the customer's words
      "bc": "BC-01",                   // required · owning bounded context
      "definition": "…",               // required · exactly one agreed meaning
      "notes": [ "Synonyms retired: …",// optional · synonyms, boundary shifts,
                 "Boundary shift: …" ] //   'not to be confused with' warnings
    }
  ]
  // Rules: one canonical term per concept; downstream documents never define
  // terms locally; amendments are forward-only (add or retire — never delete).
}""",
     "note": "Derived from the Vision and its source register; collisions resolved through the clarification "
             "interview, never silently."},

    {"title": "Story and use-case entries", "code": """// Story — Gherkin acceptance, one per functional goal
{
  "id": "US-DOC-01", "title": "Generate a functional specification",
  "priority": "Must", "role": "Specification author",
  "narrative": "As a … I want … so that …",
  "traces": { "fr": ["FR-DOC-01"], "nfr": ["NFR-ARC-01"] },
  "testLayers": ["unit", "end-to-end"],
  "scenarios": [
    { "id": "US-DOC-01-S01", "title": "Happy path",
      "given": "…", "when": "…", "then": "…" }
  ],
  "verify": ["Cross-cutting assertions that apply to every scenario."]
}

// Use case — actor-centred flow, for interactions a story cannot carry
{
  "id": "UC-04", "title": "Resume an interrupted run", "priority": "Must",
  "actor": "Orchestrator", "goal": "…", "trigger": "…",
  "pre":  ["Preconditions that must hold."],
  "main": ["Numbered main flow."],
  "alt":  ["Alternate paths."],
  "exc":  ["Exception paths."],
  "post": "Guaranteed postcondition.",
  "traces": { "fr": ["FR-EXE-09"] }
}"""},
    {"title": "Plan specification — the executable artefact", "code": """{
  "milestone": { "id": "M3", "title": "…", "status": "in-progress",
                 "dependsOn": ["M1", "M2"], "exit": ["Milestone exit criteria."] },
  "legend": { "statuses": [...], "priorities": [...], "autonomy": [...],
              "testLayers": [...], "criterionKinds": [...] },
  "catalog": { "FR-DOC-01": "Seven document types", "NFR-ARC-01": "One generator per type" },
  "phases": [{
    "id": "M3-P1", "title": "…", "dependsOn": [], "summary": "…",
    "completion": ["Phase exit criteria."],
    "tasks": [{
      "id":        "M3-P1-T1",          // required · nests the phase id
      "title":     "…",                 // required
      "status":    "not-started",       // required · closed enumeration
      "priority":  "Must",              // required
      "autonomy":  "auto",              // required · auto | auto-with-mock | human-gate
      "layer":     "service",           // optional · scheduling hint
      "testLayers":["unit", "e2e"],     // required · how it is proven
      "dependsOn": ["M3-P1-T0"],        // required · may be empty
      "summary":   "…",
      "tdd": { "red":      "The test that fails before the work exists.",
               "green":    "The minimum change that makes it pass.",
               "refactor": "The clean-up performed under a green suite." },
      "traces":  { "fr": ["FR-DOC-01"], "nfr": [], "adr": [], "us": [] },
      "criteria":[{ "id": "M3-P1-T1-C1", "kind": "auto",
                    "text": "Machine-checkable statement.", "done": false }]
    }]
  }]
}"""},
    {"title": "Plan index — the orchestrator's entry point", "code": """{
  "milestones": [{ "id": "M1", "title": "…", "file": "M1-foundation.html",
                   "dependsOn": [], "status": "passing", "detailed": true }],
  "waves":     [["M1"], ["M2", "M3"], ["M4"]],   // derived · topological
  "coverage":  { "fr":  [{ "id": "FR-DOC-01", "ms": ["M2"], "excluded": false }],
                 "nfr": [...], "adr": [...] },
  "execution": { "orchestratorPrompt": "…",
                 "milestonePrompts": { "M1": "…", "M2": "…" } },
  "prerequisites": [{ "id": "PRE-01", "text": "…", "owner": "human", "done": false }]
}"""},
]

ALGORITHMS = [
    {"title": "Status state machine", "code": """not-started ──start──▶ in-progress ──gauntlet green──▶ passing
                    │                   │
                    │                   └─gauntlet red──▶ failing ──retry──▶ in-progress
                    │
                    ├─dependency not passing──▶ blocked ──dependency passes──▶ not-started
                    ├─attempts exhausted─────▶ blocked   (blocker + workaround recorded)
                    └─auto criteria green,
                      human criterion open──▶ needs-review ──sign-off──▶ passing

Rules
  · passing is reachable only from in-progress, and only after the task's named
    verification layers have actually run and passed in this run.
  · blocked is never terminal; the orchestrator re-evaluates it each iteration.
  · needs-review does not block the task, but blocks its milestone from closing.
  · a status is written only by the write-back tool, never by hand."""},
    {"title": "Ready-set computation", "code": """ready(plan) =
  { t ∈ tasks(plan) :
        t.status = "not-started"
      ∧ ∀ d ∈ t.dependsOn : status(d) = "passing"
      ∧ t.autonomy ≠ "human-gate"
      ∧ phase(t).dependsOn all passing
      ∧ milestone(t) ∈ currentWave }

dispatch(plan):
  loop:
    R ← ready(plan)                      # recomputed every iteration, never cached
    if R = ∅ and currentWave complete:
        advance wave; if no wave remains: exit
    W ← select from R such that write-sets are pairwise disjoint
        and |W| ≤ concurrencyCeiling
    for each t ∈ W: dispatch worker with brief(t)
    await reports; apply status write-back; update ledger"""},
    {"title": "Coverage gate", "code": """universe ← { r.id : r ∈ FSD.requirements, r.priority ≠ "Won't" }
          ∪ { r.id : r ∈ SDD.requirements }
          ∪ { d.id : d ∈ SDD.decisions }
          ∪ ⋃ addenda            # merged by prefix, absent addenda skipped

claimed  ← { id : id ∈ task.traces[*], task ∈ tasks(plan) }
         ∪ { id : id ∈ milestone.traces[*] }

excluded ← { e.id : e ∈ plan.exclusions }        # each carries a recorded reason
deferred ← { id ∈ claimed : every claiming milestone is deferred }

uncovered ← universe − claimed − excluded
if uncovered ≠ ∅:
    report every id in uncovered
    exit non-zero                                # generation fails; not downgradable

for id ∈ deferred:
    warn id + " claimed only by deferred " + claimingMilestones(id)
                                                 # passes: scheduled later ≠ scheduled
                                                 # nowhere. Warned so it stays visible."""},
    {"title": "Topological wave ordering", "code": """waves(M):                       # M = milestones with dependsOn edges
  done ← ∅; waves ← []
  while done ≠ M:
      w ← { m ∈ M − done : m.dependsOn ⊆ done }
      if w = ∅: fail "dependency cycle: " + (M − done)
      waves.append(sort(w))     # sorted for deterministic output
      done ← done ∪ w
  return waves

Guarantee: every milestone in wave N depends only on milestones in waves < N,
so the members of a wave may run concurrently."""},
    {"title": "Status write-back", "code": """write_back(planFile, taskId, status, criteria):
  html  ← read(planFile)
  digest← hash(html)                            # what we are editing against
  block ← locate <script type="application/json" id="plan-spec"> … </script>
  spec  ← parse(block)                          # fail loudly if absent or invalid
  if spec.schemaVersion ≠ tool.schemaVersion:   # exact match — this tool rewrites
      fail "schema " + spec.schemaVersion + " ≠ tool " + tool.schemaVersion
  task  ← find(spec, taskId)                    # fail if not found
  task.status ← status                          # must be in the closed enumeration
  for c ∈ task.criteria where c.id ∈ criteria: c.done ← true
  if hash(read(planFile)) ≠ digest:             # changed under us — refuse
      fail "plan document modified since read: " + planFile
  write(planFile, html[..block.start] + serialise(spec) + html[block.end..])

Invariants
  · only the JSON block changes; every other byte of the file is preserved
  · serialisation is deterministic — stable key order, fixed indentation
  · one writer per run: the orchestrator is the only caller, so writes are
    serialised by construction — there is no lock file to leave stale
  · the digest check is the guard against the stray writer, not a lock; it
    fails the write rather than merging, because the tool is a file editor,
    not a database"""},
    {"title": "Repository layout", "code": """.zero/                     # everything the method owns, in one place — created by /zero:init
  specs/                     # the specification chain — generated, committed
    Vision.html  Context.html  PRD.html  FSD.html  User-Stories.html  SDD.html
    <Addendum>-FSD.html  <Addendum>-SDD.html
  plan/
    index.html               # plan index: waves, coverage, prompts — generated
    M<n>-<slug>.html         # one per milestone — generated, holds live status
    M<n>-lessons-learned.md  # retrospective, written at milestone close
    _build/
      plan_data.py           # canonical spine: legend, milestones, dependencies
      details/M<n>.json      # per-milestone phases → tasks → criteria
      generate_plan.py       # reads specs' embedded JSON; emits plan documents
      check_html.py          # validates the RENDERED plan documents
  state/<slug>.md            # run ledger — NOT in version control (ignored)

# The /zero:* skills themselves live in the agent runtime (plugin install),
# never inside the repository."""},
]
