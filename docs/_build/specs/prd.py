# -*- coding: utf-8 -*-
"""Zero-to-Ship — Product Requirements Document."""

DOC = {
    "title": "Zero-to-Ship — Product Requirements",
    "slug": "prd",
    "kicker": "Product requirements",
    "type": "Product Requirements Document (PRD)",
    "version": "2.15",
    "status": "For reference",
    "date": "2026-09-06",
    "owner": "Zerø Effort",
    "releaseScope": "v2 — the complete toolchain as the /zero:* skill chain",
    "summary": "What the method must achieve to be worth adopting, what it deliberately will not do, how success "
               "is measured, and the risks that would make it fail.",
    "scopeNote": "Outcomes and measures, not behaviour. Observable behaviour is specified in the FSD; technical "
                 "constraints in the SDD. Every goal traces to an intent capability.",
}

SUMMARY = [
    "Zero-to-Ship is a documented method plus a small toolchain: seven document generators, a plan generator, a "
    "validator suite, a status write-back tool and an execution orchestrator. Together they turn intent into a "
    "traceable specification, derive an executable plan from it, prove that nothing was dropped, and let that "
    "plan be built — by people, by agents, or by both — with progress recorded in the plan itself.",

    "The value is not in any one tool. It is in the closed loop: because the plan is derived from the "
    "specification and the specification is the only place each fact lives, a gap between what was agreed and "
    "what was built becomes a build failure instead of a discovery.",
]

GOALS = [
    {"id": "G-01", "text": "Make scope loss impossible to ship — a requirement scheduled nowhere fails the build.",
     "traces": {"cap": ["VC-05", "VC-04"]}},
    {"id": "G-02", "text": "Make the readable specification and the machine-readable one structurally incapable "
                           "of disagreeing.", "traces": {"cap": ["VC-01"]}},
    {"id": "G-03", "text": "Concentrate every decision the owner must make into one session before authoring, and "
                           "never re-ask.", "traces": {"cap": ["VC-03"]}},
    {"id": "G-04", "text": "Make 'done' a machine fact by defining every unit of work by the test that fails "
                           "before it exists.", "traces": {"cap": ["VC-06"]}},
    {"id": "G-05", "text": "Let a plan run unattended for hours, working around blockers rather than stalling on "
                           "them.", "traces": {"cap": ["VC-07"]}},
    {"id": "G-06", "text": "Make progress a reviewable fact in version control rather than a report someone "
                           "assembles.", "traces": {"cap": ["VC-08"]}},
    {"id": "G-07", "text": "Make later work cheaper than earlier work by requiring every worker to inherit what "
                           "previous ones learned.", "traces": {"cap": ["VC-09"]}},
    {"id": "G-08", "text": "Let a shipped specification grow without disturbing a single existing identifier, "
                           "trace or test name.", "traces": {"cap": ["VC-10", "VC-02"]}},
]

NON_GOALS = [
    {"id": "NG-01", "text": "Not a hosted product. No server, no accounts, no stored user data — files in a "
                            "repository, collaboration through version control."},
    {"id": "NG-02", "text": "Not an issue tracker, and not synchronised with one. The plan document is the "
                            "tracker."},
    {"id": "NG-03", "text": "Not a project-management or estimation system. It carries no schedule, no capacity "
                            "model and no burndown."},
    {"id": "NG-04", "text": "Not a replacement for judgement. It makes decisions explicit and durable; it does "
                            "not make them for you."},
    {"id": "NG-05", "text": "Not a guarantee of correctness. It proves that what was specified was scheduled, "
                            "built and verified — not that what was specified was wise."},
    {"id": "NG-06", "text": "Not tied to any language, framework, domain or agent vendor."},
    {"id": "NG-07", "text": "Not a documentation site generator. Documents are standalone files, not a published "
                            "web presence."},
]

JOURNEYS = [
    {"id": "J-01", "title": "Intent to stable specification", "persona": "Specification author",
     "steps": ["Bring a brief, notes or a conversation.",
               "Answer the decision gate once — one question at a time, each with a recommended default.",
               "Generate intent, product requirements, functional specification, stories and technical "
               "specification, validating each.",
               "Record gaps as open questions rather than inventing content.",
               "Freeze the set for the release."],
     "traces": {"goal": ["G-02", "G-03"], "cap": ["VC-01", "VC-02", "VC-03"]}},

    {"id": "J-02", "title": "Specification to executable plan", "persona": "Planner",
     "steps": ["Author the milestone spine with dependencies and exit criteria.",
               "Author phases and tasks, each with its failing test and acceptance criteria.",
               "Generate the plan; the coverage gate names anything unscheduled.",
               "Schedule it or record an explicit exclusion with a reason.",
               "Review the derived wave ordering and the prerequisite checklist."],
     "traces": {"goal": ["G-01", "G-04"], "cap": ["VC-04", "VC-05", "VC-06"]}},

    {"id": "J-03", "title": "Plan to built software", "persona": "Operator",
     "steps": ["Start the orchestrator and leave.",
               "Workers take one unit each, write the failing test, implement, verify, commit.",
               "Status is written back into the plan; the ledger records the resume point.",
               "Blocked units record why and step aside.",
               "Each milestone closes with a retrospective the next wave must read."],
     "traces": {"goal": ["G-05", "G-06", "G-07"], "cap": ["VC-07", "VC-08", "VC-09"]}},

    {"id": "J-04", "title": "Reviewing without the toolchain", "persona": "Reviewer",
     "steps": ["Open a single file from disk.",
               "Filter to the area under review and switch off out-of-scope priorities.",
               "Mark entries reviewed; progress persists across sittings.",
               "Deep-link exact identifiers into the review conversation."],
     "traces": {"goal": ["G-02"], "cap": ["VC-01"]}},

    {"id": "J-05", "title": "Growing after release", "persona": "Specification author",
     "steps": ["Author new scope as an addendum with its own identifier prefix.",
               "Register the prefix so traces route correctly.",
               "Add milestones claiming the new identifiers.",
               "Re-derive the plan; the coverage gate proves the new scope is scheduled."],
     "traces": {"goal": ["G-08"], "cap": ["VC-10"]}},
]

METRICS = [
    {"id": "MT-01", "name": "Unscheduled requirements reaching a release", "kind": "Outcome", "target": "Zero",
     "traces": {"goal": ["G-01"]}},
    {"id": "MT-02", "name": "Time from adding a requirement to the build naming it as unscheduled",
     "kind": "Outcome", "target": "Under one build cycle", "traces": {"goal": ["G-01"]}},
    {"id": "MT-03", "name": "Facts stored in more than one place", "kind": "Structural", "target": "Zero",
     "traces": {"goal": ["G-02"]}},
    {"id": "MT-04", "name": "Owner interruptions during a build", "kind": "Experience", "target": "Zero",
     "traces": {"goal": ["G-03"]}},
    {"id": "MT-05", "name": "Forks resolved in the gate rather than mid-build", "kind": "Experience",
     "target": "Above 90%", "traces": {"goal": ["G-03"]}},
    {"id": "MT-06", "name": "Tasks with no machine-checkable acceptance criterion", "kind": "Quality",
     "target": "Zero, documented exceptions aside", "traces": {"goal": ["G-04"]}},
    {"id": "MT-07", "name": "Units marked passing that later prove not to work", "kind": "Quality",
     "target": "Under 1 in 50", "traces": {"goal": ["G-04"]}},
    {"id": "MT-08", "name": "Unattended units needing human rescue", "kind": "Autonomy", "target": "Under 1 in 20",
     "traces": {"goal": ["G-05"]}},
    {"id": "MT-09", "name": "Work lost to an interruption", "kind": "Autonomy", "target": "At most one unit",
     "traces": {"goal": ["G-05"]}},
    {"id": "MT-10", "name": "Questions asked by the system during an unattended run", "kind": "Autonomy",
     "target": "Zero", "traces": {"goal": ["G-05"]}},
    {"id": "MT-11", "name": "Progress reports assembled by hand", "kind": "Outcome", "target": "Zero",
     "traces": {"goal": ["G-06"]}},
    {"id": "MT-12", "name": "Cost per unit of work, later waves against earlier", "kind": "Learning",
     "target": "Declining across waves", "traces": {"goal": ["G-07"]}},
    {"id": "MT-13", "name": "Retrospective themes recurring three or more times", "kind": "Learning",
     "target": "Escalated to a method change", "traces": {"goal": ["G-07"]}},
    {"id": "MT-14", "name": "Existing identifiers disturbed by new scope", "kind": "Evolution", "target": "Zero",
     "traces": {"goal": ["G-08"]}},
    {"id": "MT-15", "name": "Generated documents hand-edited after generation", "kind": "Structural",
     "target": "Zero, detected by regenerating in the pipeline", "traces": {"goal": ["G-02", "G-06"]}},
]

RELEASE_SHAPE = [
    {"id": "R-01", "name": "Foundation", "goal": "The shared document shell, the contracts and the validator.",
     "includes": "M1, M2", "moscow": "Must"},
    {"id": "R-02", "name": "The specification chain", "goal": "All seven document generators and the decision gate.",
     "includes": "M3, M4, M5, M6", "moscow": "Must"},
    {"id": "R-03", "name": "Derived planning",
     "goal": "Traceability, the coverage gate and the plan generator.", "includes": "M7, M8", "moscow": "Must"},
    {"id": "R-04", "name": "Proof and progress",
     "goal": "Rendered-artefact validation, pipeline gates, the status model and write-back.",
     "includes": "M9, M10", "moscow": "Must"},
    {"id": "R-05", "name": "Autonomy", "goal": "The orchestrator, the worker contract and resumability.",
     "includes": "M11", "moscow": "Should"},
    {"id": "R-06", "name": "Compounding and growth",
     "goal": "Retrospectives, amendment by addendum, briefing output and self-hosting.",
     "includes": "M12", "moscow": "Should"},
]

DEPENDENCIES = [
    "A version-control system whose history can serve as the audit trail.",
    "A scripting runtime available to every developer and to the pipeline.",
    "An agent runtime able to load named skills, edit files, and run commands — for the execution layer only.",
    "A verification command in the host project that exits non-zero on failure.",
    "Optionally, a headless browser for the rendered-view check; its absence is reported, never assumed away.",
    "Optionally, a design system to adopt; a neutral theme is used when none exists.",
]

ASSUMPTIONS = [
    "The team is willing to front-load planning: authoring a task's failing test before writing the task.",
    "Requirements are stable enough within a release that amendment is the exception, not the norm.",
    "Someone is accountable for answering the decision gate and is available for one session.",
    "The host project's verification suite is trustworthy; the method inherits its quality, it does not improve it.",
    "Reviewers will read diffs. The method makes progress reviewable; it cannot make anyone review it.",
]

RISKS = [
    {"id": "RK-01", "risk": "The planning cost is felt immediately and the benefit only later, so adoption stalls "
                            "at the first milestone.",
     "mitigation": "Author milestone detail one wave ahead rather than all at once; the spine plus the first wave "
                   "is enough to start, and the coverage gate pays back on the first amendment.",
     "traces": {"goal": ["G-04"]}},
    {"id": "RK-02", "risk": "Coverage becomes theatre — requirements claimed by token tasks that do nothing.",
     "mitigation": "Every task must state a failing test; a claim with no red step is visible in review and "
                   "fails validation.", "traces": {"goal": ["G-01", "G-04"]}},
    {"id": "RK-03", "risk": "Agents report success on work that does not function, and the method certifies it.",
     "mitigation": "Status may only be set after the named verification actually ran; reports must name the "
                   "command that produced each result.", "traces": {"goal": ["G-04", "G-06"]}},
    {"id": "RK-04", "risk": "Partial adoption — documents without gates — produces the drift the method exists "
                            "to prevent, and gets blamed for it.",
     "mitigation": "Adoption guidance names the minimum viable subset explicitly; the gates are the method.",
     "traces": {"goal": ["G-01"]}},
    {"id": "RK-05", "risk": "Generated plan documents flood version-control diffs and reviewers stop reading them.",
     "mitigation": "Deterministic generation, stable key ordering, and generated-file marking so reviews collapse "
                   "them by default.", "traces": {"goal": ["G-06"]}},
    {"id": "RK-06", "risk": "A defect in a shared template or runtime propagates into every document at once.",
     "mitigation": "Validation runs against rendered artefacts, and the method's own document set is regenerated "
                   "in the pipeline as a canary.", "traces": {"goal": ["G-02"]}},
    {"id": "RK-07", "risk": "Concurrency corrupts work through undetected file collisions.",
     "mitigation": "Write-set disjointness is checked before dispatch; a collision is reported, costs the unit "
                   "no attempt, and is remembered so the same pairing is not scheduled again.",
     "traces": {"goal": ["G-05"]}},
]

OPEN_QUESTIONS = [
    "Should the method ship an optional exporter for teams contractually required to use an external tracker, "
    "given NG-02?",
]
