# -*- coding: utf-8 -*-
"""Zero-to-Ship (Z2S) — Functional Specification Document (FR-*)."""

DOC = {
    "title": "Zero-to-Ship — Functional Specification Document",
    "slug": "fsd",
    "kicker": "Functional specification",
    "type": "Functional Specification Document (FSD)",
    "version": "2.4",
    "status": "Draft for review",
    "date": "2026-08-18",
    "owner": "Zerø Effort",
    "releaseScope": "v2 — the complete toolchain as the /zero:* skill chain",
    "summary": "What the Zero-to-Ship toolchain must do: generate a traceable chain of specification documents, "
               "establish a shared language, derive an executable plan, prove coverage, drive an autonomous build, "
               "and keep progress visible — every artefact both human-readable and machine-readable.",
    "scopeNote": "Functional requirements only — the observable behaviour of the toolchain. Technical, "
                 "architectural, performance and security constraints live in the SDD as `NFR-*` and `ADR-*`. "
                 "Where a functional requirement implies a technical one it is cross-referenced, never restated.",
}

AREAS = [
    {"key": "FR-DOC", "name": "Document chain",
     "description": "Authoring the seven specification document types and the gate that precedes each."},
    {"key": "FR-CTX", "name": "Context & ubiquitous language",
     "description": "Establishing one shared vocabulary — derived from the vision, scoped to bounded contexts, "
                    "and used consistently by every later document."},
    {"key": "FR-SKL", "name": "Skill-chain interface",
     "description": "The named, separately invocable entry points the method is operated through, and the rules "
                    "governing when each may run."},
    {"key": "FR-SPC", "name": "Spec embedding & rendering",
     "description": "Every document is one self-contained file that renders itself from its own embedded JSON."},
    {"key": "FR-TRC", "name": "Identity & traceability",
     "description": "Stable IDs, trace links, and the coverage matrix that proves nothing was dropped."},
    {"key": "FR-PLN", "name": "Plan derivation",
     "description": "Turning a stable specification into a milestone → phase → task plan that can be executed."},
    {"key": "FR-VAL", "name": "Validation & gates",
     "description": "The machine checks that must pass before a document, a plan, or a unit of work is accepted."},
    {"key": "FR-EXE", "name": "Autonomous execution",
     "description": "Computing what is ready, dispatching it, and building it test-first without a human in the loop."},
    {"key": "FR-STA", "name": "Status & progress",
     "description": "Recording, rolling up and displaying the state of every unit of work."},
    {"key": "FR-LRN", "name": "Retrospectives & compounding memory",
     "description": "Capturing what each unit of work taught, so later work inherits it."},
    {"key": "FR-AMD", "name": "Amendment & addenda",
     "description": "Extending a shipped specification without rewriting or renumbering it."},
    {"key": "FR-GEN", "name": "Cross-cutting behaviour",
     "description": "Rules every document, tool and surface in the method obeys."},
]

DIMENSIONS_META = {
    "title": "Canonical analysis dimensions",
    "intro": "Every document the method produces is checked against these eleven dimensions before it is "
             "declared stable. A dimension with nothing to say becomes an explicit open question, never silence.",
}
DIMENSIONS = [
    {"name": "Purpose", "desc": "Why the thing exists, stated so a non-specialist can repeat it back."},
    {"name": "Actors & roles", "desc": "Who acts on the system, and what each is permitted to do."},
    {"name": "Scope boundary", "desc": "What is in, what is out, and what is deliberately deferred."},
    {"name": "Behaviour", "desc": "Observable actions and outputs, stated without implementation."},
    {"name": "Data & state", "desc": "What is stored, what is derived, and what is the source of truth."},
    {"name": "Interfaces", "desc": "Every boundary crossed: files, commands, providers, humans."},
    {"name": "Failure & degradation", "desc": "What happens when a step, provider, or gate fails."},
    {"name": "Constraints", "desc": "Hard limits — legal, technical, budgetary, organisational."},
    {"name": "Verification", "desc": "How each claim will be proven, and by which layer of test."},
    {"name": "Provenance", "desc": "Where each fact came from, and how it will be re-checked."},
    {"name": "Evolution", "desc": "How the artefact is amended once it is in use."},
]

FLOWS = [
    {"name": "Flow A — Specification chain",
     "caption": "Each document is gated before authoring and validated after. Nothing proceeds on an unanswered fork.",
     "steps": [
         {"title": "Intent", "desc": "A brief, a conversation, or rough notes.", "kind": "input"},
         {"title": "Decision gate", "desc": "Every fork resolved and written down before authoring starts.", "kind": "gate"},
         {"title": "Vision", "desc": "Problem, principles, personas, capabilities."},
         {"title": "Context", "desc": "Ubiquitous language and bounded contexts — the shared vocabulary."},
         {"title": "PRD", "desc": "Goals, non-goals, journeys, metrics, risks."},
         {"title": "FSD", "desc": "Functional requirements, prioritised and testable."},
         {"title": "Stories & use cases", "desc": "Acceptance criteria precise enough to drive tests."},
         {"title": "SDD", "desc": "Technical requirements and architecture decisions.", "kind": "accent"},
     ]},
    {"name": "Flow B — Plan derivation",
     "caption": "The plan is derived, never hand-written. A requirement no milestone claims fails the build.",
     "steps": [
         {"title": "Stable specification", "desc": "FSD + SDD validated and frozen for the release.", "kind": "input"},
         {"title": "Author the spine", "desc": "Milestones, dependencies, exit criteria."},
         {"title": "Author the detail", "desc": "Phases and tasks with red/green/refactor and criteria."},
         {"title": "Generate", "desc": "Read the specs' JSON; render plan documents."},
         {"title": "Coverage gate", "desc": "Every requirement claimed by at least one task.", "kind": "gate"},
         {"title": "Executable plan", "desc": "Waves, ready set, per-unit prompts.", "kind": "accent"},
     ]},
    {"name": "Flow C — Autonomous execution",
     "caption": "One loop iteration. It repeats until no unit is ready and every exit criterion is met.",
     "steps": [
         {"title": "Read status", "desc": "From the plan's own embedded JSON.", "kind": "input"},
         {"title": "Compute ready set", "desc": "Not started, dependencies passing, not human-gated."},
         {"title": "Dispatch one unit", "desc": "A fresh worker with the unit's own prompt."},
         {"branch": [
             {"title": "Red", "desc": "Write the failing test named in the task."},
             {"title": "Green", "desc": "Minimum code to pass it."},
             {"title": "Refactor", "desc": "Clean up under a green suite."},
         ]},
         {"title": "Verify", "desc": "Run the gauntlet named by the task's test layers.", "kind": "gate"},
         {"title": "Write status back", "desc": "Tick criteria, set status, commit.", "kind": "accent"},
     ]},
]

REQUIREMENTS = [
    # ---------------- FR-DOC ----------------
    {"id": "FR-DOC-01", "area": "FR-DOC", "priority": "Must", "title": "Seven document types",
     "text": "The system shall produce seven specification document types — Vision, Context, PRD, FSD, User "
             "stories & use cases, SDD, and Plan — each a distinct artefact with its own identity scheme, and each "
             "generated by a dedicated, separately invocable generator.",
     "notes": "The chain is deliberately narrow-to-narrower: each document answers a question the previous one raised.",
     "tags": ["chain"]},
    {"id": "FR-DOC-02", "area": "FR-DOC", "priority": "Must", "title": "Decision gate before authoring",
     "text": "Before authoring any document, the system shall run a single decision gate that surfaces every "
             "unresolved fork, asks one question at a time with a recommended default for each, and refuses to "
             "begin authoring until all forks are resolved.",
     "notes": "Constrained by NFR-EXE-08. A question asked after authoring begins is a defect, not diligence.",
     "tags": ["gate", "authoring"]},
    {"id": "FR-DOC-03", "area": "FR-DOC", "priority": "Must", "title": "Locked-decisions record",
     "text": "The system shall write the gate's outcome to a durable locked-decisions table — decision, choice, "
             "rationale — inside the document it governs and inside the run ledger, and shall treat any row in that "
             "table as closed for the remainder of the build.",
     "notes": "A decision held only in conversation is lost at the first context reset.",
     "tags": ["gate", "memory"]},
    {"id": "FR-DOC-04", "area": "FR-DOC", "priority": "Must", "title": "Never invent content",
     "text": "The system shall not fabricate requirements, personas, metrics or constraints to fill a section. Any "
             "gap shall be recorded as an explicit open question or assumption, and any section with no real "
             "content shall be omitted from the rendered document entirely.",
     "tags": ["integrity"]},
    {"id": "FR-DOC-05", "area": "FR-DOC", "priority": "Must", "title": "Separation of what and how",
     "text": "The system shall keep functional content (the FSD) free of technical, architectural, performance and "
             "security content, and shall record any technical implication it encounters as an assumption or an "
             "open question for the SDD rather than resolving it in place.",
     "tags": ["separation"]},
    {"id": "FR-DOC-06", "area": "FR-DOC", "priority": "Must", "title": "Regeneration from source",
     "text": "The system shall allow any document to be regenerated from its own machine-readable spec without "
             "loss, so that an update is made by editing the spec and re-rendering, never by editing rendered markup.",
     "tags": ["regeneration"]},
    {"id": "FR-DOC-07", "area": "FR-DOC", "priority": "Should", "title": "Intake from existing material",
     "text": "The system shall accept an existing brief, notes document, transcript or prior specification as the "
             "input to a document generator, and shall skip the clarifying interview when the supplied material is "
             "already sufficient to author a complete, non-fabricated document.",
     "tags": ["intake"]},
    {"id": "FR-DOC-08", "area": "FR-DOC", "priority": "Should", "title": "Document control block",
     "text": "Every document shall carry a control block stating title, type, version, status, date, owner, release "
             "scope, a one-line summary, a scope note, and links to its companion documents.",
     "tags": ["metadata"]},
    {"id": "FR-DOC-09", "area": "FR-DOC", "priority": "Could", "title": "Narrative briefing output",
     "text": "The system should be able to emit a narrative briefing derived from the document set, aimed at "
             "readers who will not read the specifications themselves.",
     "tags": ["comms"]},
    {"id": "FR-DOC-10", "area": "FR-DOC", "priority": "Must", "title": "Source register",
     "text": "The vision generator shall accept any combination of narrative, source documents and web addresses "
             "as input, and shall maintain a register of every source material consulted — what it was, where it "
             "came from, and what it contributed — carried forward with the document set.",
     "notes": "Provenance is what lets a later reader distinguish a stated fact from an assumed one.",
     "tags": ["intake", "provenance"]},

    # ---------------- FR-CTX ----------------
    {"id": "FR-CTX-01", "area": "FR-CTX", "priority": "Must", "title": "Context derived from the vision",
     "text": "The system shall generate a Context document only after a completed Vision exists, deriving its "
             "candidate vocabulary from the vision, its source register, and any supplied material — never from "
             "invention.",
     "tags": ["chain", "core"]},
    {"id": "FR-CTX-02", "area": "FR-CTX", "priority": "Must", "title": "Ubiquitous language glossary",
     "text": "The Context document shall define a ubiquitous language: every domain term carrying exactly one "
             "agreed definition, written in the customer's words, with known synonyms recorded and one term "
             "designated canonical.",
     "notes": "The principle is borrowed from domain-driven design: one word, one meaning, everywhere.",
     "tags": ["language", "core"]},
    {"id": "FR-CTX-03", "area": "FR-CTX", "priority": "Must", "title": "Bounded contexts",
     "text": "The Context document shall partition the domain into named bounded contexts, and shall scope each "
             "term's definition to its context wherever the same word carries different meanings in different "
             "parts of the domain.",
     "tags": ["language", "core"]},
    {"id": "FR-CTX-04", "area": "FR-CTX", "priority": "Must", "title": "Collisions resolved by asking",
     "text": "Where candidate terms collide, overlap or remain ambiguous, the system shall resolve them by "
             "questioning the operator through the clarification interview, and shall never pick a meaning "
             "silently.",
     "notes": "Constrained by FR-SKL-04 — the questions flow through the shared clarification skill.",
     "tags": ["language", "gate"]},
    {"id": "FR-CTX-05", "area": "FR-CTX", "priority": "Must", "title": "Downstream documents speak the language",
     "text": "Every generator downstream of the Context document shall consult its glossary and use its canonical "
             "terms; a downstream document that needs a term the glossary lacks shall add it to the Context "
             "document as a forward-only amendment, never define it locally.",
     "tags": ["language", "chain"]},
    {"id": "FR-CTX-06", "area": "FR-CTX", "priority": "Should", "title": "Context map",
     "text": "The Context document shall present a map of how its bounded contexts relate — which contexts feed "
             "which, and where a term crosses a boundary and changes meaning.",
     "tags": ["language"]},

    # ---------------- FR-SKL ----------------
    {"id": "FR-SKL-01", "area": "FR-SKL", "priority": "Must", "title": "Named entry point per step",
     "text": "The system shall expose each step of the method as a named, separately invocable skill — one per "
             "document type, plus init, resume, build, update, ship and clarification — so that an operator "
             "drives the method entirely through named commands.",
     "amendments": [
         {"date": "2026-08-17",
          "text": "The list above names the steps that existed when it was written; it is not a closed set. A "
                  "design step has since joined the chain, which reads the design system a project already has "
                  "— stylesheets, token documents, a brand book, a design guide — and records what the "
                  "documents are styled with. The rule the addition follows: a step whose work is not "
                  "repeatable without effect shall be named as its own skill rather than folded into one that "
                  "is."}],
     "tags": ["interface", "core"]},
    {"id": "FR-SKL-02", "area": "FR-SKL", "priority": "Must", "title": "Prerequisite enforcement",
     "text": "Each document-generating skill shall verify that its required upstream document exists and is "
             "complete before doing any work, and shall refuse to run — naming exactly what is missing — when it "
             "is not.",
     "notes": "Vision needs nothing; Context needs Vision; PRD needs Context; FSD needs PRD; Stories and SDD each "
              "need the FSD; the Plan needs Stories, FSD and SDD.",
     "tags": ["interface", "gate", "core"]},
    {"id": "FR-SKL-03", "area": "FR-SKL", "priority": "Must", "title": "Manual triggering only",
     "text": "No skill in the chain shall trigger automatically, with a single exception: the clarification skill. "
             "Every other skill runs only when invoked deliberately — by the operator, or by another skill that "
             "was itself invoked deliberately.",
     "notes": "An agent that helpfully regenerates a specification unasked is a defect, not initiative.",
     "tags": ["interface", "safety", "core"]},
    {"id": "FR-SKL-04", "area": "FR-SKL", "priority": "Must", "title": "One shared clarification skill",
     "text": "All skills shall route their questions through a single shared clarification skill that interviews "
             "the operator in rounds — each question numbered, each carrying a recommended answer — and it shall "
             "be the only skill permitted to trigger automatically, under explicit instructions tuned to fire "
             "whenever a decision would otherwise be guessed.",
     "tags": ["interface", "gate", "core"]},
    {"id": "FR-SKL-05", "area": "FR-SKL", "priority": "Must", "title": "Resume from wherever the set stands",
     "text": "The system shall provide a resume skill that inspects the document set, determines the furthest "
             "completed step, and continues from there — starting from the beginning when no completed Vision "
             "exists.",
     "tags": ["interface", "resilience"]},
    {"id": "FR-SKL-06", "area": "FR-SKL", "priority": "Must", "title": "Forward-only updates",
     "text": "The system shall provide an update skill that folds additions and changes into existing documents "
             "forward only — amending, appending and superseding in place — and never deletes or overwrites "
             "published content.",
     "notes": "The document-side counterpart of FR-AMD-01: history is part of the specification.",
     "tags": ["interface", "evolution"]},
    {"id": "FR-SKL-07", "area": "FR-SKL", "priority": "Should", "title": "Ship skill",
     "text": "The system shall provide a ship skill that commits all changes on the current working branch, pushes "
             "it, and offers — never assumes — the creation of a pull request to the upstream branch.",
     "tags": ["interface", "vcs"]},
    {"id": "FR-SKL-08", "area": "FR-SKL", "priority": "Should", "title": "Installable as one plugin",
     "text": "The complete skill chain shall be distributable as a single installable plugin from a marketplace "
             "reference, so that adopting the method is one install action, not a per-skill setup.",
     "tags": ["interface", "distribution"]},
    {"id": "FR-SKL-09", "area": "FR-SKL", "priority": "Must", "title": "Self-initialising setup",
     "text": "The system shall provide an init skill that performs every setup mechanic the method needs — "
             "creating the documented directory layout, writing the ignore rules, detecting the design-system "
             "theme and recording the verification gauntlet — and every chain skill shall invoke it "
             "automatically, idempotently, whenever it finds that setup missing, so that no step of the method "
             "requires the operator to run a shell command.",
     "amendments": [
         {"date": "2026-08-17",
          "text": "Detecting a design system stays part of setup, so no project is left unstyled by omission. "
                  "Reading the documents an operator names, asking about anything a document states only in "
                  "prose, and recording the result belong to the separate design step instead. Init promises "
                  "that a second run changes no byte, and every chain skill leans on that promise when it "
                  "invokes init unasked; a refresh that rewrites the record cannot keep it."}],
     "notes": "Running it explicitly is allowed and harmless; on an already-initialised repository it changes "
              "nothing.",
     "tags": ["interface", "setup", "core"]},

    # ---------------- FR-SPC ----------------
    {"id": "FR-SPC-01", "area": "FR-SPC", "priority": "Must", "title": "Embedded machine-readable spec",
     "text": "Every generated document shall embed its complete specification as a single JSON object inside the "
             "document itself, under a stable, document-type-specific element identifier.",
     "notes": "Traced by NFR-DAT-01. This is the contract every other tool in the method reads.",
     "tags": ["json", "core"]},
    {"id": "FR-SPC-02", "area": "FR-SPC", "priority": "Must", "title": "Human view rendered from the spec",
     "text": "The system shall render the human-readable view of a document from that same embedded JSON at load "
             "time, so that the readable document and the machine-readable one cannot diverge.",
     "notes": "This single rule removes the entire class of 'the doc says X, the data says Y' defects.",
     "tags": ["json", "core"]},
    {"id": "FR-SPC-03", "area": "FR-SPC", "priority": "Must", "title": "Self-contained file",
     "text": "Each document shall be a single file that opens and functions with no build step, no server, no "
             "package installation, and no network access beyond optional web fonts.",
     "tags": ["portability"]},
    {"id": "FR-SPC-04", "area": "FR-SPC", "priority": "Must", "title": "Spec extraction",
     "text": "The system shall expose the embedded spec for extraction by an automated consumer, and shall offer a "
             "human reader a copy-to-clipboard and a download action for the same content.",
     "tags": ["interop"]},
    {"id": "FR-SPC-05", "area": "FR-SPC", "priority": "Must", "title": "Live filter",
     "text": "Each document shall provide a keyword filter that narrows every catalogue entry it contains in real "
             "time, matching across identifier, title, body and tags, and shall state plainly when a filter matches "
             "nothing.",
     "tags": ["interactive"]},
    {"id": "FR-SPC-06", "area": "FR-SPC", "priority": "Must", "title": "Deep links",
     "text": "Every catalogue entry shall be individually addressable by a stable fragment link that, when "
             "followed, expands any collapsed container around the target and visibly marks it.",
     "tags": ["interactive"]},
    {"id": "FR-SPC-07", "area": "FR-SPC", "priority": "Should", "title": "Priority filtering",
     "text": "Documents containing prioritised entries shall let a reader toggle each priority band on and off, and "
             "shall show the count of entries in each band.",
     "tags": ["interactive"]},
    {"id": "FR-SPC-08", "area": "FR-SPC", "priority": "Should", "title": "Review tracking",
     "text": "Requirement-bearing documents shall let a reviewer mark each entry reviewed, shall show aggregate "
             "review progress, and shall persist that state locally to the reader's browser under a namespace "
             "unique to the document.",
     "notes": "Review state is a reader's private working state, never part of the spec.",
     "tags": ["review"]},
    {"id": "FR-SPC-09", "area": "FR-SPC", "priority": "Should", "title": "Contents navigation",
     "text": "Each document shall present a contents list with automatic section numbering that highlights the "
             "section currently in view and lets the reader jump to any section.",
     "amendments": [
         {"date": "2026-08-15",
          "text": "A document written across several files shall also let a reader reach every other part of it, "
                  "and return to its index, from any part — with the part they are on stated and not offered as "
                  "a link. A contents list that reaches only the sections of the file in hand is not navigation "
                  "of the document; it is navigation of a fragment."}],
     "tags": ["navigation"]},
    {"id": "FR-SPC-10", "area": "FR-SPC", "priority": "Should", "title": "Expand and collapse",
     "text": "Documents that group entries into collapsible containers shall offer expand-all and collapse-all "
             "controls, and shall default to a state that reveals content rather than hiding it.",
     "amendments": [
         {"date": "2026-08-15",
          "text": "A document that is **navigated** rather than read end to end may default to collapsed, "
                  "provided it reveals the first unit at each level and opening one unit closes its siblings at "
                  "that level. A collapsed container shall name what it holds and read as a control. A plan is "
                  "the case this carves out: a specification is read through, and hiding its contents hides its "
                  "contents, but a plan of a hundred and twenty tasks rendered open is an endless scroll nobody "
                  "can find a task in. The default is opted into per section, never applied to a whole document "
                  "set."}],
     "tags": ["interactive"]},
    {"id": "FR-SPC-11", "area": "FR-SPC", "priority": "Could", "title": "Print and export",
     "text": "Each document should print legibly on paper or to a portable document format, with all collapsed "
             "content expanded and interactive chrome suppressed.",
     "tags": ["output"]},

    # ---------------- FR-TRC ----------------
    {"id": "FR-TRC-01", "area": "FR-TRC", "priority": "Must", "title": "Stable identifiers",
     "text": "Every requirement, story, use case, decision, milestone, phase, task and criterion shall carry an "
             "identifier that is unique within the document set, human-typable, and never reused for a different "
             "subject.",
     "tags": ["identity", "core"]},
    {"id": "FR-TRC-02", "area": "FR-TRC", "priority": "Must", "title": "Identifiers are never renumbered",
     "text": "The system shall not renumber an identifier once it has been published. Removed items shall be "
             "retired in place with a recorded reason; new items shall take the next free number.",
     "notes": "Renumbering silently breaks every existing trace, test name and commit reference.",
     "tags": ["identity", "core"]},
    {"id": "FR-TRC-03", "area": "FR-TRC", "priority": "Must", "title": "Upward traces",
     "text": "Each downstream item shall record the upstream identifiers it satisfies, so that any item can be "
             "walked back to the capability and the problem statement that justify it.",
     "tags": ["traceability"]},
    {"id": "FR-TRC-04", "area": "FR-TRC", "priority": "Must", "title": "Coverage matrix",
     "text": "The system shall compute, and present in the plan, a coverage matrix listing every functional and "
             "technical requirement and every architecture decision alongside the units of work that claim it.",
     "tags": ["coverage", "core"]},
    {"id": "FR-TRC-05", "area": "FR-TRC", "priority": "Must", "title": "Uncovered requirements fail the build",
     "text": "Generation of the plan shall fail, with the offending identifiers listed, if any requirement or "
             "decision is claimed by no unit of work and has not been explicitly excluded. A requirement claimed "
             "only by a milestone deferred out of the current release shall pass the gate and be reported as a "
             "warning naming the deferring milestone.",
     "notes": "This is the gate that makes coverage a fact rather than an intention. The failure condition is "
              "'scheduled nowhere'; a deferred milestone is somewhere, so the warning keeps deferred scope visible "
              "without forcing an edit to a published requirement.",
     "tags": ["coverage", "gate"]},
    {"id": "FR-TRC-06", "area": "FR-TRC", "priority": "Must", "title": "Explicit exclusion",
     "text": "The system shall allow a requirement to be excluded from coverage only by an explicit, recorded "
             "exclusion carrying a reason, and shall report all exclusions alongside the coverage matrix.",
     "tags": ["coverage"]},
    {"id": "FR-TRC-07", "area": "FR-TRC", "priority": "Should", "title": "Trace links resolve",
     "text": "Every trace shown to a reader shall be a working link to the referenced item, resolving within the "
             "same document where possible and to the correct companion document otherwise.",
     "tags": ["traceability"]},
    {"id": "FR-TRC-08", "area": "FR-TRC", "priority": "Should", "title": "Unresolvable traces fail validation",
     "text": "Validation shall fail if any trace references an identifier that exists in no document in the set.",
     "tags": ["traceability", "gate"]},
    {"id": "FR-TRC-09", "area": "FR-TRC", "priority": "Should", "title": "Test names carry identifiers",
     "text": "The system shall require that automated tests written for a scenario are named for that scenario's "
             "identifier, so that a failing test names the requirement it defends.",
     "tags": ["verification"]},

    # ---------------- FR-PLN ----------------
    {"id": "FR-PLN-01", "area": "FR-PLN", "priority": "Must", "title": "Three-level work breakdown",
     "text": "The system shall express the plan as milestones containing phases containing tasks, where a task is "
             "the smallest independently verifiable unit of work.",
     "tags": ["structure", "core"]},
    {"id": "FR-PLN-02", "area": "FR-PLN", "priority": "Must", "title": "Plan is derived, not authored",
     "text": "The system shall generate every plan document from a single canonical data source plus the "
             "specifications' own embedded JSON, and shall never accept hand-edited plan markup as input.",
     "tags": ["generation", "core"]},
    {"id": "FR-PLN-03", "area": "FR-PLN", "priority": "Must", "title": "Dependency edges",
     "text": "Milestones, phases and tasks shall each declare the units they depend on, and the system shall reject "
             "a plan containing a dependency cycle or a reference to a unit that does not exist.",
     "tags": ["dependencies"]},
    {"id": "FR-PLN-04", "area": "FR-PLN", "priority": "Must", "title": "Test-first task definition",
     "text": "Every task shall state, before any code exists, the failing test that proves the work is needed, the "
             "minimum change that makes it pass, and the clean-up to perform under a green suite.",
     "notes": "Authoring the red step first is what makes a task verifiable by a worker that has no context.",
     "tags": ["tdd", "core"]},
    {"id": "FR-PLN-05", "area": "FR-PLN", "priority": "Must", "title": "Acceptance criteria per task",
     "text": "Every task shall carry at least one machine-checkable acceptance criterion, and each criterion shall "
             "be individually identified and individually tickable.",
     "tags": ["criteria", "core"]},
    {"id": "FR-PLN-06", "area": "FR-PLN", "priority": "Must", "title": "Criterion kinds",
     "text": "Each criterion shall be classified as machine-checkable or human-review; human-review criteria shall "
             "not block a task but shall block the milestone that contains them.",
     "tags": ["criteria"]},
    {"id": "FR-PLN-07", "area": "FR-PLN", "priority": "Must", "title": "Autonomy classification",
     "text": "Every task shall declare whether it can be executed unattended, executed unattended only against a "
             "substituted provider, or requires a human because it touches a live credential, a paid provider, or "
             "an interactive tool.",
     "notes": "This is what lets an unattended run proceed safely instead of stalling on an approval prompt.",
     "tags": ["autonomy", "core"]},
    {"id": "FR-PLN-08", "area": "FR-PLN", "priority": "Must", "title": "Exit criteria",
     "text": "Every phase and every milestone shall declare explicit exit criteria that are checked before the unit "
             "is considered complete.",
     "tags": ["gates"]},
    {"id": "FR-PLN-09", "area": "FR-PLN", "priority": "Must", "title": "Parallel waves",
     "text": "The system shall compute, from the dependency graph, an ordered set of waves in which every milestone "
             "in a wave depends only on milestones in earlier waves, and shall present that ordering in the plan.",
     "tags": ["scheduling"]},
    {"id": "FR-PLN-10", "area": "FR-PLN", "priority": "Should", "title": "Verification layers per task",
     "text": "Each task shall name the verification layers that prove it — unit, integration, end-to-end, "
             "accessibility, performance, quality evaluation, static analysis, or human review.",
     "tags": ["verification"]},
    {"id": "FR-PLN-11", "area": "FR-PLN", "priority": "Should", "title": "Implementation layer tagging",
     "text": "Each task should declare which layer of the system it touches, so that work colliding on the same "
             "layer can be scheduled apart.",
     "tags": ["scheduling"]},
    {"id": "FR-PLN-12", "area": "FR-PLN", "priority": "Should", "title": "Prerequisite checklist",
     "text": "The plan shall carry a checklist of external prerequisites — accounts, credentials, provisioned "
             "services — separated from the work itself and marked as human-owned.",
     "tags": ["prerequisites"]},
    {"id": "FR-PLN-13", "area": "FR-PLN", "priority": "Could", "title": "Effort signal",
     "text": "Tasks could carry a coarse effort or risk signal to help a human judge sequencing, provided it is "
             "never used as an automated gate.",
     "tags": ["estimation"]},

    # ---------------- FR-VAL ----------------
    {"id": "FR-VAL-01", "area": "FR-VAL", "priority": "Must", "title": "Schema validation",
     "text": "The system shall validate every document's embedded spec against the schema for its document type, "
             "reporting every violation in one pass rather than stopping at the first, and shall refuse to process "
             "a document whose schema version it does not support, naming both versions rather than guessing at "
             "the difference.",
     "notes": "Which differences are refusable and which are warnings is set by NFR-EVO-01.",
     "tags": ["validation", "core"]},
    {"id": "FR-VAL-02", "area": "FR-VAL", "priority": "Must", "title": "Validate the rendered artefact",
     "text": "The system shall validate the generated file itself — extracting its embedded spec from the rendered "
             "output and asserting structural invariants on it — not merely the source data it was built from.",
     "notes": "Validating only the source proves the input was sound; it does not prove the deliverable is.",
     "tags": ["validation", "core"]},
    {"id": "FR-VAL-03", "area": "FR-VAL", "priority": "Must", "title": "Identifier uniqueness and format",
     "text": "Validation shall fail on any duplicate identifier, any identifier not matching its document type's "
             "pattern, and any entry referencing a group that does not exist.",
     "tags": ["validation"]},
    {"id": "FR-VAL-04", "area": "FR-VAL", "priority": "Must", "title": "Plan structural invariants",
     "text": "Validation of a plan shall fail if any task lacks a status, lacks acceptance criteria, or lacks at "
             "least one machine-checkable criterion, and if any milestone in the index is missing its detail document.",
     "tags": ["validation"]},
    {"id": "FR-VAL-05", "area": "FR-VAL", "priority": "Must", "title": "Non-zero exit on failure",
     "text": "Every validator shall exit with a failing status code and a list of failures when any check fails, so "
             "it can be wired directly into a continuous-integration gate.",
     "tags": ["validation", "ci"]},
    {"id": "FR-VAL-06", "area": "FR-VAL", "priority": "Should", "title": "Warnings distinct from failures",
     "text": "Validators shall distinguish advisory warnings from blocking failures, and shall never let a warning "
             "fail a build or a failure pass as a warning.",
     "tags": ["validation"]},
    {"id": "FR-VAL-07", "area": "FR-VAL", "priority": "Should", "title": "Rendered-view check",
     "text": "Where a browser is available, the system shall confirm that a generated document actually renders — "
             "entries visible, filter narrowing, a priority toggle working — and shall say plainly that the check "
             "was skipped when no browser is available. The check shall not block ordinary integration, but shall "
             "have run and passed before a release is promoted to production.",
     "notes": "Never report a render check as passed when it did not run. Optional in everyday integration keeps "
              "the pipeline fast and dependency-light; mandatory at promotion means nothing unrendered ever ships.",
     "tags": ["validation", "visual"]},
    {"id": "FR-VAL-08", "area": "FR-VAL", "priority": "Should", "title": "Documented exceptions",
     "text": "Where a validation rule has an approved exception, the exception shall be recorded in the validator "
             "itself with its justification, and reported as a warning on every run.",
     "tags": ["validation"]},

    # ---------------- FR-EXE ----------------
    {"id": "FR-EXE-01", "area": "FR-EXE", "priority": "Must", "title": "Ready-set computation",
     "text": "The system shall compute the set of units eligible to start as those not yet started, whose every "
             "declared dependency has passed, and which are not human-gated.",
     "tags": ["orchestration", "core"]},
    {"id": "FR-EXE-02", "area": "FR-EXE", "priority": "Must", "title": "Wave-ordered dispatch",
     "text": "The orchestrator shall walk the waves in order, dispatching the milestones within a wave "
             "concurrently, and shall not begin a wave until every milestone it depends on has completed.",
     "tags": ["orchestration"]},
    {"id": "FR-EXE-03", "area": "FR-EXE", "priority": "Must", "title": "Self-contained unit prompts",
     "text": "The system shall generate, for every milestone, a complete execution prompt that a worker with no "
             "prior context can follow — naming the plan file, the status contract, the locked decisions, the "
             "verification gauntlet, and the report it must return.",
     "notes": "A worker that never saw the decision gate will otherwise invent its own answers.",
     "tags": ["orchestration", "core"]},
    {"id": "FR-EXE-04", "area": "FR-EXE", "priority": "Must", "title": "Test-first execution",
     "text": "A worker shall implement each task by writing the task's stated failing test first, confirming it "
             "fails, making it pass with the minimum change, then refactoring under a green suite.",
     "tags": ["tdd", "core"]},
    {"id": "FR-EXE-05", "area": "FR-EXE", "priority": "Must", "title": "No live credentials in unattended work",
     "text": "A unit marked as executable only against a substituted provider shall be executed with that provider "
             "substituted, and no unattended worker shall use a live credential, incur provider cost, or open an "
             "interactive prompt.",
     "notes": "Constrained by NFR-SEC-02 and NFR-SEC-03.",
     "tags": ["safety", "core"]},
    {"id": "FR-EXE-06", "area": "FR-EXE", "priority": "Must", "title": "Collision-free concurrency",
     "text": "The system shall not dispatch concurrently two units that write the same files, and shall serialise "
             "them or isolate each in its own working copy.",
     "tags": ["concurrency"]},
    {"id": "FR-EXE-07", "area": "FR-EXE", "priority": "Must", "title": "Blocker policy",
     "text": "A worker that cannot complete a unit after a stated number of attempts shall record the blocker and "
             "the workaround chosen, mark the unit blocked, and move to the next ready unit rather than stalling "
             "the run.",
     "tags": ["resilience", "core"]},
    {"id": "FR-EXE-08", "area": "FR-EXE", "priority": "Must", "title": "Never ask mid-run",
     "text": "During an unattended run the system shall not ask the operator a question; it shall make the "
             "reasonable call, record it as a decision with its rationale, and continue.",
     "notes": "The place to ask is the decision gate — see FR-DOC-02.",
     "tags": ["autonomy", "core"]},
    {"id": "FR-EXE-09", "area": "FR-EXE", "priority": "Must", "title": "Resumable after interruption",
     "text": "The system shall recover from an interruption, a restart, or a loss of working memory by re-reading "
             "the plan and the run ledger and recomputing the ready set, without repeating completed work.",
     "tags": ["resilience", "core"]},
    {"id": "FR-EXE-10", "area": "FR-EXE", "priority": "Should", "title": "Mandatory worker report",
     "text": "Every dispatched worker shall return a structured report — what it changed, what it verified, what it "
             "could not do, and what the next worker needs to know — and a worker that returns no report shall be "
             "treated as failed.",
     "tags": ["orchestration"]},
    {"id": "FR-EXE-11", "area": "FR-EXE", "priority": "Should", "title": "Commit per unit",
     "text": "The system shall commit the work for each unit atomically, with a message naming the unit identifier, "
             "so that history reads as a sequence of completed units.",
     "tags": ["vcs"]},
    {"id": "FR-EXE-12", "area": "FR-EXE", "priority": "Should", "title": "Integration branch discipline",
     "text": "The system shall integrate completed units on a shared integration branch and shall never write "
             "directly to the production branch or rewrite shared history.",
     "tags": ["vcs"]},
    {"id": "FR-EXE-13", "area": "FR-EXE", "priority": "Could", "title": "Cost-aware model selection",
     "text": "The orchestrator could select the least capable model sufficient for each unit, reserving the most "
             "capable for genuinely difficult design work.",
     "tags": ["cost"]},
    {"id": "FR-EXE-14", "area": "FR-EXE", "priority": "Must", "title": "Independent judgement of a finished unit",
     "text": "Before a unit is recorded as passing, a worker other than the one that built it shall inspect the "
             "work itself against the unit's acceptance criteria and verification gauntlet, receiving no account "
             "of how the work was done; it shall return a pass or a failure, and on a failure the single largest "
             "remaining gap. A judgement that could not inspect the work is a failure. A retry shall be briefed "
             "with that gap and judged by a further worker that has not seen the attempt it follows.",
     "notes": "Refines ADR-13 rather than contradicting it: the report remains the bookkeeping, but the pass "
              "comes from an inspection. A builder grading its own work is the failure every other guarantee "
              "here rests on.",
     "tags": ["orchestration", "core"]},
    {"id": "FR-EXE-15", "area": "FR-EXE", "priority": "Must",
     "title": "A prompt at every level of the plan",
     "text": "The plan shall carry a complete execution prompt for the build as a whole, for every milestone, for "
             "every phase and for every task, each on the card of the unit it belongs to and each able to be "
             "copied on its own, so that whoever is running the work chooses how much of it to hand over at once.",
     "notes": "Extends FR-EXE-03, which requires one prompt per milestone and remains true as written. A "
              "milestone is the wrong unit for somebody handing a single task to a colleague, and the whole plan "
              "is the wrong unit for somebody handing it to an unattended run.",
     "amendments": [
         {"date": "2026-08-15",
          "text": "A reader shall be able to take any of those prompts **without first revealing it**, and a "
                  "collapsed prompt shall say which unit it belongs to. Copying a prompt is the common use and "
                  "reading one on screen is the rare one, so a control that requires the second before it allows "
                  "the first has the two the wrong way round."}],
     "tags": ["orchestration", "core"]},
    {"id": "FR-EXE-16", "area": "FR-EXE", "priority": "Must",
     "title": "Every prompt runs a builder-and-critic loop against a higher target",
     "text": "Every generated prompt shall instruct whoever receives it to split the unit into separately "
             "judgeable pieces of their own choosing, to have each piece judged by somebody who did not build it "
             "and has not seen how it was built, to return exactly one gap on a failure and re-brief against "
             "that gap, and to keep going without a stated number of rounds. It shall state the unit's "
             "acceptance criteria as the floor and, above them, the requirements, stories and numbered targets "
             "the unit already traces to as the target it is aiming at — naming none where the unit traces to "
             "nothing. It shall state what the unit waits on before anything else, and the operations no unit "
             "may perform whatever it is asked.",
     "notes": "The same contract the orchestrator applies in code (FR-EXE-14), stated in words for a prompt "
              "nobody is orchestrating. A ceiling invented to fill an empty block is an invented standard, "
              "graded as though somebody had decided it — which is the failure the whole method exists to "
              "prevent.",
     "tags": ["orchestration", "core"]},

    # ---------------- FR-STA ----------------
    {"id": "FR-STA-01", "area": "FR-STA", "priority": "Must", "title": "Status vocabulary",
     "text": "Every unit of work shall carry exactly one status from a fixed, documented set covering not started, "
             "in progress, passing, failing, blocked, and awaiting human review.",
     "tags": ["status", "core"]},
    {"id": "FR-STA-02", "area": "FR-STA", "priority": "Must", "title": "Status lives in the plan document",
     "text": "The plan document's own embedded JSON shall be the single source of truth for status; no separate "
             "tracker shall hold authoritative state.",
     "notes": "One artefact is the plan, the status board and the audit trail.",
     "tags": ["status", "core"]},
    {"id": "FR-STA-03", "area": "FR-STA", "priority": "Must", "title": "Programmatic status write-back",
     "text": "The system shall provide a command that sets a unit's status and ticks named acceptance criteria in "
             "the plan document, preserving the rest of the file byte-for-byte.",
     "tags": ["status", "core"]},
    {"id": "FR-STA-04", "area": "FR-STA", "priority": "Must", "title": "Rollup",
     "text": "The system shall roll task status up to phase, milestone and programme level and display the rollup "
             "without a reader having to open every unit.",
     "tags": ["status"]},
    {"id": "FR-STA-05", "area": "FR-STA", "priority": "Must", "title": "Generated plan documents are committed",
     "text": "The system shall keep generated plan documents under version control despite being generated, so "
             "that progress is a reviewable change in history.",
     "notes": "This is a deliberate exception to the usual rule against committing generated output — see ADR-11.",
     "tags": ["vcs", "status"]},
    {"id": "FR-STA-06", "area": "FR-STA", "priority": "Should", "title": "Status report command",
     "text": "The system shall provide a command that prints a status summary per phase and per milestone without "
             "opening a browser.",
     "tags": ["status", "cli"]},
    {"id": "FR-STA-07", "area": "FR-STA", "priority": "Should", "title": "Criterion-level progress",
     "text": "The rendered plan shall show which acceptance criteria are satisfied and which remain, per task.",
     "tags": ["status"]},
    {"id": "FR-STA-08", "area": "FR-STA", "priority": "Should", "title": "Human-review queue",
     "text": "The system shall list every outstanding human-review criterion across the plan so a reviewer can "
             "clear them in one pass before a milestone closes.",
     "tags": ["status", "review"]},

    # ---------------- FR-LRN ----------------
    {"id": "FR-LRN-01", "area": "FR-LRN", "priority": "Must", "title": "Retrospective per milestone",
     "text": "On closing a milestone the system shall write a retrospective recording what was learned, what "
             "surprised it, and what the next milestone should do differently, as prose readable on its own, "
             "carrying a header that lists the themes it raises as tags drawn from a growing, shared tag set.",
     "notes": "The body stays prose because the useful observations are the ones that do not fit a field; the tag "
              "header exists only so recurrence can be counted rather than noticed. See FR-LRN-04.",
     "tags": ["learning", "core"]},
    {"id": "FR-LRN-02", "area": "FR-LRN", "priority": "Must", "title": "Read prior retrospectives first",
     "text": "Before beginning any milestone, a worker shall read every prior retrospective in the run and apply "
             "its conclusions.",
     "notes": "This is what makes later waves cheaper than earlier ones.",
     "tags": ["learning", "core"]},
    {"id": "FR-LRN-03", "area": "FR-LRN", "priority": "Should", "title": "Conventions cheat-sheet",
     "text": "The system shall maintain a growing conventions summary distilled from retrospectives, and shall "
             "include it in every worker's brief.",
     "tags": ["learning"]},
    {"id": "FR-LRN-04", "area": "FR-LRN", "priority": "Should", "title": "Recurring-theme escalation",
     "text": "The system shall count theme tags across every retrospective in the run and surface any theme "
             "recurring across three or more milestones as a candidate change to the method itself, not merely to "
             "the next milestone.",
     "notes": "Detection is a count over the tag headers required by FR-LRN-01, not a human noticing a pattern.",
     "tags": ["learning"]},
    {"id": "FR-LRN-05", "area": "FR-LRN", "priority": "Should", "title": "Run ledger",
     "text": "The system shall maintain a durable run ledger recording done-state, autonomous decisions, the exact "
             "next step, and how to resume, and shall treat that ledger rather than working memory as authoritative.",
     "tags": ["learning", "resilience"]},

    # ---------------- FR-AMD ----------------
    {"id": "FR-AMD-01", "area": "FR-AMD", "priority": "Must", "title": "Addendum documents",
     "text": "The system shall support extending a shipped specification with addendum documents carrying their "
             "own identifier prefixes, rather than by editing or renumbering the original.",
     "tags": ["evolution", "core"]},
    {"id": "FR-AMD-02", "area": "FR-AMD", "priority": "Must", "title": "Merged trace universe",
     "text": "The plan generator shall merge addendum identifiers into the coverage universe so that later work can "
             "trace to them, and shall route each trace link to the document that defines it. Two documents "
             "declaring the same identifier prefix shall fail generation, naming both documents and the prefix.",
     "notes": "A prefix is an identity namespace. Two owners makes every trace to it ambiguous, and a link that "
              "silently resolves to the wrong document is worse than one that does not resolve at all.",
     "tags": ["evolution", "traceability"]},
    {"id": "FR-AMD-03", "area": "FR-AMD", "priority": "Must", "title": "Degrade gracefully without addenda",
     "text": "Generation shall succeed when an addendum document is absent, producing the core plan unchanged.",
     "tags": ["evolution"]},
    {"id": "FR-AMD-04", "area": "FR-AMD", "priority": "Should", "title": "Amendment notes in place",
     "text": "Where a later decision changes an earlier requirement, the system shall annotate the original in "
             "place with the amendment and its date rather than silently rewriting it.",
     "tags": ["evolution", "provenance"]},
    {"id": "FR-AMD-05", "area": "FR-AMD", "priority": "Should", "title": "Re-derivation after amendment",
     "text": "After any specification amendment the system shall re-run generation and the coverage gate, so that "
             "newly added requirements cannot sit unclaimed.",
     "tags": ["evolution", "coverage"]},

    # ---------------- FR-GEN ----------------
    {"id": "FR-GEN-01", "area": "FR-GEN", "priority": "Must", "title": "Project-agnostic",
     "text": "Every generator shall work in any repository, adopting that project's conventions from its own "
             "configuration, and shall carry no assumption about domain, language or framework.",
     "tags": ["portability", "core"]},
    {"id": "FR-GEN-02", "area": "FR-GEN", "priority": "Must", "title": "Adopt the host design system",
     "text": "Generated documents shall adopt the host project's design system where one exists, applying its "
             "tokens rather than ad-hoc styling, and shall fall back to a neutral theme when none is found.",
     "amendments": [
         {"date": "2026-08-18",
          "text": "A design system is rarely one stylesheet. Every readable source a project states its design "
                  "in — stylesheets, token documents, a framework's theme block, a brand book, a design guide — "
                  "shall be read and merged into a single result, and a document an operator names shall outrank "
                  "anything found by searching. Adoption shall cover colour, type scale, spacing, shape, "
                  "elevation, motion and both colour schemes, not colour alone: a system that lends only its "
                  "palette leaves every project rendering at the same size, rhythm and density, which is how two "
                  "very different design systems came to produce documents that looked alike. A value recorded "
                  "by an operator outranks any value detected. Where a host declares no dark counterpart for a "
                  "value, none shall be invented — inventing one guesses at contrast, which is the one thing "
                  "this requirement exists to take from the host rather than decide."}],
     "tags": ["design"]},
    {"id": "FR-GEN-03", "area": "FR-GEN", "priority": "Must", "title": "Report what was actually checked",
     "text": "Every tool shall report the checks it actually ran and their real results, and shall never report a "
             "skipped, blocked or unavailable check as passed.",
     "notes": "The most damaging failure mode in an autonomous system is a confident false green.",
     "tags": ["integrity", "core"]},
    {"id": "FR-GEN-04", "area": "FR-GEN", "priority": "Must", "title": "No secrets in artefacts",
     "text": "No generated document, plan, prompt, ledger or commit shall contain a credential, token or other "
             "secret value; secrets shall be referenced by name only.",
     "tags": ["security", "core"]},
    {"id": "FR-GEN-05", "area": "FR-GEN", "priority": "Should", "title": "Plain language",
     "text": "Documents shall be written so that a reader outside the specialism can follow them: no unexplained "
             "jargon, no internal tool names in reader-facing prose, and any unavoidable term defined on first use.",
     "tags": ["voice"]},
    {"id": "FR-GEN-06", "area": "FR-GEN", "priority": "Should", "title": "Accessible documents",
     "text": "Generated documents shall be keyboard-navigable, shall meet contrast requirements at the level the "
             "host project targets, and shall respect a reader's reduced-motion preference.",
     "tags": ["accessibility"]},
    {"id": "FR-GEN-07", "area": "FR-GEN", "priority": "Should", "title": "Deterministic generation",
     "text": "Generating twice from unchanged inputs shall produce byte-identical output, so that a change in "
             "version control always means a change in content.",
     "tags": ["determinism"]},
    {"id": "FR-GEN-08", "area": "FR-GEN", "priority": "Should", "title": "Method documents itself",
     "text": "The method's own documentation shall be produced by the method, so that a defect in the toolchain is "
             "visible in its own artefacts.",
     "tags": ["dogfood"]},
    {"id": "FR-GEN-09", "area": "FR-GEN", "priority": "Won't", "title": "Hosted collaborative editing",
     "text": "The system will not provide a hosted service, multi-user editing, comment threads or authentication. "
             "Documents are files in a repository; collaboration happens through version control.",
     "notes": "Recorded as an explicit exclusion so the decision is not revisited by default.",
     "tags": ["exclusion"]},
    {"id": "FR-GEN-10", "area": "FR-GEN", "priority": "Won't", "title": "Issue-tracker synchronisation",
     "text": "The system will not synchronise plan status into an external issue tracker in this release. The plan "
             "document is the tracker.",
     "notes": "Recorded as an explicit exclusion so the decision is not revisited by default. A second place to "
              "record status is a second answer to what is done, and the plan document is derived from the "
              "specification set while a tracker is maintained by hand.",
     "tags": ["exclusion"]},
    {"id": "FR-GEN-11", "area": "FR-GEN", "priority": "Must", "title": "The adopted design is recorded",
     "text": "The system shall write the design it resolved to a reviewable record in the project, naming the "
             "source file and the source name of every adopted value, and shall treat a value recorded by an "
             "operator as outranking any value detected.",
     "notes": "Kept apart from adopting a design system rather than folded into it, because the two have "
              "different subjects: that one is about how a document looks, this one about an artefact in the "
              "repository and who wins when two answers exist. Delete the record and documents still adopt a "
              "design system, which is what makes this independently testable.",
     "tags": ["design", "provenance"]},
]

ASSUMPTIONS = [
    "The team owning a project can run a scripting runtime and a version-control client locally.",
    "An agent capable of following a written brief, editing files and running commands is available.",
    "Work is done in a repository whose history is the audit trail; there is no separate document store.",
    "A reader of a generated document has a modern browser; no other software is required.",
    "The host project can express its verification gauntlet as commands that exit non-zero on failure.",
]

OPEN_QUESTIONS = []
