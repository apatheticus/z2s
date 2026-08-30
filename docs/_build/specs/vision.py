# -*- coding: utf-8 -*-
"""Zero-to-Ship — Vision."""

DOC = {
    "title": "Zero-to-Ship — Vision",
    "slug": "vision",
    "kicker": "Vision",
    "type": "Vision document",
    "version": "2.7",
    "status": "For reference",
    "date": "2026-08-30",
    "owner": "Zerø Effort",
    "releaseScope": "The method as a whole",
    "summary": "A way of building software in which the specification is the machine's input, the plan is derived "
               "from it, coverage is a build failure rather than a hope, and progress is a fact recorded in the "
               "same file that describes the work.",
    "scopeNote": "This document states the problem, the change being aimed at, and the principles that constrain "
                 "every later decision. It contains no requirements — those live in the functional and technical "
                 "specifications.",
}

PROBLEM = {
    "body": [
        "Software teams have always written specifications, and specifications have always rotted. The document "
        "is written once, approved, and then diverges from the code within weeks. Nobody notices, because nothing "
        "checks. By the time the gap is visible it is expensive: a capability that was agreed and never built, a "
        "constraint that was recorded and never honoured, a decision that was made twice and differently.",

        "Handing that work to an AI agent does not fix the problem — it accelerates it. An agent will build "
        "confidently from an ambiguous brief, make a hundred small decisions nobody sees, and report success. The "
        "output looks finished. Whether it is the thing that was wanted, and whether it covers everything that "
        "was asked for, remain unanswerable questions, because there is nothing to answer them against.",

        "Underneath both problems sits one structural fault: **the same fact is stored in more than one place.** "
        "It is in the specification and in the plan. In the plan and in the tracker. In the tracker and in "
        "someone's memory of last week's meeting. Every duplicate is a place where reality and record can "
        "quietly separate, and no amount of diligence prevents it — only a structure that makes it impossible.",
    ],
    "highlights": [
        {"label": "Symptom", "title": "Specifications rot",
         "text": "Written once, approved, then overtaken by the code. Nothing checks, so nobody knows."},
        {"label": "Symptom", "title": "Plans drift",
         "text": "The plan and the specification are two descriptions of one intent, maintained separately, "
                 "diverging from day one."},
        {"label": "Symptom", "title": "Progress is anecdote",
         "text": "Status lives in a tracker, a spreadsheet and a stand-up. None of them is the work."},
        {"label": "Symptom", "title": "Autonomy amplifies ambiguity",
         "text": "An agent given a vague brief produces confident, plausible, unverifiable work — fast."},
    ],
}

VISION_STATEMENT = (
    "Write the specification once, in a form both a person and a machine can read. Derive everything else from "
    "it — the plan, the schedule, the work briefs, the coverage proof. Let the machine build against it, "
    "test-first, unattended, recording its progress in the same document that describes the work. Make the "
    "question **\"did we build what we said?\"** answerable by running a command."
)

AMBITION = [
    "A specification that cannot silently disagree with itself, because the readable document is generated from "
    "the machine-readable one at the moment it is read.",
    "A plan nobody writes by hand, because it is derived from the specification and fails to build when any "
    "requirement is scheduled nowhere.",
    "A build an agent can run for hours without asking a question, because every question was answered once, "
    "before the first file was written.",
    "A progress report that is not a report — it is the plan itself, edited by the work as the work completes.",
    "A method that improves from its own operation: every milestone leaves a lesson that the next one is "
    "required to read.",
]

PRINCIPLES = [
    {"name": "One source of truth per fact",
     "desc": "Each fact is stored exactly once. Everything else is computed from it. Duplication is the defect, "
             "not the symptom."},
    {"name": "Derive, never duplicate",
     "desc": "The plan comes from the specification. Coverage comes from the traces. Progress comes from the "
             "tasks. Nothing is maintained in parallel."},
    {"name": "Gates, not intentions",
     "desc": "Every quality claim is enforced by a command that exits non-zero. A claim no command can check is "
             "labelled human judgement, not asserted as fact."},
    {"name": "Decide once, up front",
     "desc": "Every fork is resolved in one session before authoring begins, recorded, and never re-litigated. "
             "Questions asked mid-build arrive when the answer is most expensive."},
    {"name": "Test-first is the contract",
     "desc": "A unit of work is defined by the test that fails before it exists. This is what makes 'done' a "
             "machine fact rather than an opinion."},
    {"name": "Honest reporting above all",
     "desc": "A check that did not run is reported as skipped. A blocked step is reported as blocked. The most "
             "damaging failure in an autonomous system is a confident false green."},
    {"name": "Fail loudly, continue safely",
     "desc": "A stuck unit records why and steps aside so the run continues. Nothing silently degrades; nothing "
             "silently stalls."},
    {"name": "Portable by construction",
     "desc": "Every artefact is a plain file that opens with no build step and no service. If it needs "
             "infrastructure to read, it will not be read."},
    {"name": "Plain language is a requirement",
     "desc": "A document a stakeholder cannot follow has failed, however precise it is. Jargon is defined or "
             "removed."},
]

STAKEHOLDERS = [
    {"id": "SH-01", "name": "Product owner", "type": "Decision-maker",
     "interest": "That what ships is what was agreed, and that scope loss is visible early.",
     "role": "Answers the decision gate; approves promotion."},
    {"id": "SH-02", "name": "Engineering lead", "type": "Practitioner",
     "interest": "That the plan is real work with real verification, not a wish list.",
     "role": "Authors the plan spine and milestone detail; resolves coverage failures."},
    {"id": "SH-03", "name": "Delivery team", "type": "Practitioner",
     "interest": "That a unit of work is unambiguous and independently verifiable.",
     "role": "Executes units; writes retrospectives."},
    {"id": "SH-04", "name": "Autonomous agent", "type": "Machine consumer",
     "interest": "That the brief is complete, so no judgement has to be invented.",
     "role": "Executes exactly one unit at a time and reports honestly."},
    {"id": "SH-05", "name": "Reviewer or auditor", "type": "Oversight",
     "interest": "That every requirement can be traced to the work that satisfied it and the test that proves it.",
     "role": "Reads documents and diffs; signs off human-review items."},
    {"id": "SH-06", "name": "Future maintainer", "type": "Inheritor",
     "interest": "That a decision made years earlier is recoverable, with its reasoning intact.",
     "role": "Reads the record; extends by addendum."},
]

PERSONAS = [
    {"tier": "Primary", "name": "The owner who cannot watch",
     "desc": "Responsible for the outcome, unavailable during the build. Needs every decision that matters "
             "concentrated into one short session, and needs to trust what happened while they were away.",
     "goals": ["Answer the questions that only they can answer, once.",
               "See real progress without attending a meeting.",
               "Know that nothing agreed was quietly dropped."],
     "pains": ["Being interrupted mid-week for a decision that could have been asked up front.",
               "Discovering at release that a capability was never built.",
               "Reports that say complete when the thing does not work."]},
    {"tier": "Primary", "name": "The lead who has to make it real",
     "desc": "Turns intent into work other people — and machines — can execute. Lives with the consequences of "
             "every ambiguity left in the specification.",
     "goals": ["Decompose scope into units that are independently verifiable.",
               "Prove coverage rather than argue about it.",
               "Reuse what earlier work learned instead of rediscovering it."],
     "pains": ["Plans that describe intent but not verification.",
               "Traceability maintained by hand in a spreadsheet.",
               "The same mistake repeating in every workstream."]},
    {"tier": "Secondary", "name": "The agent with no memory",
     "desc": "Executes one unit of work, having never seen the conversation that produced it, and will lose its "
             "context entirely between units.",
     "goals": ["Receive a brief that answers every question it could have.",
               "Know exactly what 'done' means before starting.",
               "Record what it did so the next worker inherits it."],
     "pains": ["Briefs that assume context it never had.",
               "Ambiguity with no policy for resolving it.",
               "Losing the run's state when its memory is compacted."]},
]

CAPABILITIES = [
    {"id": "VC-01", "name": "One artefact, two readers",
     "desc": "Every document is a single file that a person reads and a machine parses, with the readable view "
             "generated from the machine-readable data so the two cannot disagree."},
    {"id": "VC-02", "name": "A chain from problem to test",
     "desc": "Seven document types, each narrower than the last, each tracing upward, so any line of code can be "
             "walked back to the problem that justifies it."},
    {"id": "VC-03", "name": "Decide once",
     "desc": "A single gate resolves every fork before authoring begins and records the outcome where every "
             "later worker will read it."},
    {"id": "VC-04", "name": "Derived planning",
     "desc": "The plan is generated from the specification, not written beside it, so the two cannot drift."},
    {"id": "VC-05", "name": "Coverage as a build failure",
     "desc": "A requirement scheduled nowhere fails the build and is named. Scope loss becomes a compile error."},
    {"id": "VC-06", "name": "Work defined by its failing test",
     "desc": "Every task states the test that fails before it exists, so completion is evidence rather than "
             "judgement."},
    {"id": "VC-07", "name": "Unattended execution",
     "desc": "The plan computes what is ready, dispatches it in dependency waves, isolates concurrent work, and "
             "never asks a question mid-run."},
    {"id": "VC-08", "name": "Progress as a fact",
     "desc": "Status lives in the plan document itself and is written by the work, so progress is reviewable in "
             "version-control history."},
    {"id": "VC-09", "name": "Compounding memory",
     "desc": "Every milestone leaves a retrospective the next is required to read, so later work is cheaper than "
             "earlier work."},
    {"id": "VC-10", "name": "Growth by addendum",
     "desc": "New scope arrives as a new document with its own identifiers, so nothing that shipped is disturbed."},
]

SCENARIOS = [
    {"id": "VS-01", "title": "The Friday decision session",
     "persona": "The owner who cannot watch",
     "narrative": "The owner spends forty minutes answering questions — one at a time, each with a recommended "
                  "default. Every fork that would otherwise have interrupted the next three weeks is closed and "
                  "written into a table. The owner does not need to be available again until there is something "
                  "to review.",
     "touches": ["VC-03"]},
    {"id": "VS-02", "title": "The requirement that would have been lost",
     "persona": "The lead who has to make it real",
     "narrative": "A requirement is added to the specification late in the week. Nobody schedules it. The next "
                  "build fails, names the requirement, and refuses to produce a plan. The omission is fixed in "
                  "four minutes instead of surfacing at release.",
     "touches": ["VC-05", "VC-04"]},
    {"id": "VS-03", "title": "The overnight wave",
     "persona": "The agent with no memory",
     "narrative": "Three independent milestones run concurrently overnight. Each worker receives a brief that "
                  "assumes nothing, writes its failing test first, implements, verifies, records its status in "
                  "the plan and commits. One unit hits an unavailable dependency, records the blocker, and steps "
                  "aside. The run continues.",
     "touches": ["VC-06", "VC-07"]},
    {"id": "VS-04", "title": "The interruption",
     "persona": "The agent with no memory",
     "narrative": "The run is killed mid-wave. On restart it reads its ledger, recomputes what is ready from the "
                  "plan's stored status, and continues. Nothing is repeated; nothing is skipped. The "
                  "interruption cost one unit of work.",
     "touches": ["VC-07", "VC-08"]},
    {"id": "VS-05", "title": "Monday morning, no meeting",
     "persona": "The owner who cannot watch",
     "narrative": "The owner opens one file. Milestone-level progress, task counts and outstanding human-review "
                  "items are visible without expanding anything. The history of how it got there is in the "
                  "repository, commit by commit.",
     "touches": ["VC-08", "VC-01"]},
    {"id": "VS-06", "title": "The lesson that only costs once",
     "persona": "The lead who has to make it real",
     "narrative": "The second wave hits a problem the first wave already solved — except it does not, because "
                  "every worker in the second wave was required to read the first wave's retrospectives before "
                  "writing a line. The third wave is cheaper still.",
     "touches": ["VC-09"]},
    {"id": "VS-07", "title": "The capability nobody planned for",
     "persona": "The lead who has to make it real",
     "narrative": "Six months after release, new scope arrives. It is authored as an addendum with its own "
                  "identifier prefix. Every existing identifier, trace and test name still resolves. The plan is "
                  "re-derived and the coverage gate makes sure the new scope is actually scheduled.",
     "touches": ["VC-10", "VC-05"]},
]

CONSTRAINTS = [
    "Every deliverable is a plain file in a repository. No service, no database, no hosted state.",
    "No third-party runtime dependency in the generators, validators or document runtime.",
    "The method must work in any domain, language or framework; nothing is assumed about the system being built.",
    "Nothing unattended may use a live credential, incur provider cost, or perform a destructive operation.",
    "Planning depth is front-loaded by design; teams unwilling to plan test-first will not get the benefit.",
    "The method cannot make a bad specification good. It can only make a bad specification visible sooner.",
]
