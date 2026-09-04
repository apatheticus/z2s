# -*- coding: utf-8 -*-
"""Zero-to-Ship — Narrative briefing. Layered: plain language first, depth after."""

DOC = {
    "title": "Zero-to-Ship — Method Briefing",
    "slug": "brief",
    "kicker": "Briefing",
    "type": "Narrative briefing",
    "version": "2.11",
    "status": "For circulation",
    "date": "2026-09-04",
    "owner": "Zerø Effort",
    "releaseScope": "The method as a whole",
    "summary": "A way of building software where the written specification is the machine's input, the plan is "
               "derived from it rather than written beside it, and the question \"did we build what we said?\" is "
               "answered by running a command.",
    "scopeNote": "Sections 1 to 3 assume no technical background. Section 6 shows the method run for real, on a "
                 "shipped product. The later sections go a layer deeper for readers who will evaluate or "
                 "implement the method, and for whoever decides whether to adopt it.",
    "heroLogo": True,
}

SECTIONS = [
    # ---------------------------------------------------------------- 01
    {"id": "problem", "type": "prose", "title": "The problem, in one page",
     "body": [
         "Every software project starts with someone describing what they want. That description gets written "
         "down, agreed, and then — almost immediately — it starts to drift from what is actually being built. "
         "Not through carelessness. Through structure: the description lives in one place and the work lives in "
         "another, and nothing connects them. Weeks later nobody can say with confidence whether everything that "
         "was agreed has been built, and the honest answer is usually **no, and nobody noticed**.",

         "Handing the building to an AI agent makes this sharper, not softer. An agent given a loose description "
         "will produce something confident, plausible and fast. It will make hundreds of small decisions nobody "
         "sees, and it will report that it is finished. Whether the result is the thing that was wanted remains "
         "unanswerable — because there is nothing to check it against.",

         "Underneath both problems is a single fault, and it is boring: **the same fact is written down in more "
         "than one place.** It is in the specification, and in the plan. In the plan, and in the tracker. In the "
         "tracker, and in someone's memory of a meeting. Every duplicate is a place where the record and the "
         "reality can quietly separate. Discipline does not fix this. Only structure does.",
     ],
     "highlights": [
         {"label": "Today", "title": "The specification rots",
          "text": "Written once, approved, overtaken by the code. Nothing checks, so nobody knows."},
         {"label": "Today", "title": "The plan drifts",
          "text": "Two descriptions of the same intent, maintained separately, diverging from day one."},
         {"label": "Today", "title": "Progress is anecdote",
          "text": "A tracker, a spreadsheet and a stand-up — none of which is the work itself."},
         {"label": "Today", "title": "Speed magnifies ambiguity",
          "text": "Anything vague in the brief becomes a confident, invisible decision in the build."},
     ],
     "note": {"kind": "info", "label": "The claim.",
              "text": "If each fact exists in exactly one place, and everything else is calculated from it, then "
                      "the record and the reality cannot separate — not because people are careful, but because "
                      "there is nowhere for the gap to hide."}},

    # ---------------------------------------------------------------- 02
    {"id": "idea", "type": "flow", "title": "The idea, in one picture",
     "lede": "Write the description once, in a form both a person and a machine can read. Calculate everything "
             "else from it — the plan, the schedule, the work instructions, the proof of coverage. Then let the "
             "work record its own progress in the same document that describes it.",
     "flows": [
         {"name": "The whole method",
          "caption": "Everything to the right of the gate is derived. Nothing in the chain is maintained twice.",
          "steps": [
              {"title": "What you want", "desc": "A brief, notes, a conversation.", "kind": "input"},
              {"title": "One decision session", "desc": "Every open question answered once, and written down.",
               "kind": "gate"},
              {"title": "A shared language", "desc": "Every important word given one agreed meaning."},
              {"title": "The specification", "desc": "Seven linked documents, each narrower than the last."},
              {"title": "The plan", "desc": "Calculated from the specification, not written beside it."},
              {"title": "Coverage check", "desc": "Anything unscheduled stops the build.", "kind": "gate"},
              {"title": "The build", "desc": "Test-first, unattended, progress written back.", "kind": "accent"},
          ]},
     ]},

    # ---------------------------------------------------------------- 03
    {"id": "how", "type": "cards", "title": "How it works, step by step", "cols": "g2",
     "lede": "Seven moves, each one command. The first two are the only ones that need much of your time.",
     "items": [
         {"kicker": "Step one", "title": "Answer everything once, up front",
          "text": "Before anything is written, every open question is put to you — one at a time, each with a "
                  "recommended answer so you can agree rather than compose. The answers go into a table that "
                  "every later step reads. **Nothing interrupts you again**, because the interruptions have "
                  "already happened, in one sitting, at the cheapest possible moment."},
         {"kicker": "Step two", "title": "Agree what the words mean",
          "text": "Before requirements are written, every important word in the project gets exactly one agreed "
                  "meaning, in your words, written into a glossary every later document uses. Where one word "
                  "genuinely means two things in two places, both meanings are recorded and scoped. **Most "
                  "specification defects are two people using one word for two things** — this removes them "
                  "before they cost anything."},
         {"kicker": "Step three", "title": "Write the specification once, for two readers",
          "text": "Each document is a single file. A person opens it and reads a normal document. A machine "
                  "opens the same file and reads structured data. The readable version is **built from** the "
                  "data every time it is opened — so the prose and the data cannot say different things."},
         {"kicker": "Step four", "title": "Let the plan be calculated, not written",
          "text": "Nobody writes the plan by hand. A program reads the specification and the outline of the "
                  "work, and produces the plan. If any requirement has not been scheduled anywhere, **the "
                  "program refuses to produce a plan at all** and tells you which one."},
         {"kicker": "Step five", "title": "Define every job by the test it must pass",
          "text": "Each job in the plan states, before any work starts, the check that currently fails and must "
                  "end up passing. That is what turns \"is it done?\" from an opinion into something a machine "
                  "can answer — and it is what lets a worker with no context know exactly when to stop."},
         {"kicker": "Step six", "title": "Let it build, without asking",
          "text": "The plan knows what depends on what, so it knows what can start now and what can run "
                  "alongside it. Work goes out in batches. If something gets stuck, it writes down why and steps "
                  "aside so everything else keeps going. **Nothing stops to ask a question** — the questions were "
                  "answered in steps one and two."},
         {"kicker": "Step seven", "title": "Progress records itself",
          "text": "As each job finishes it updates its own status inside the plan document. The plan is the "
                  "status board and the history, all at once. You open one file to see where things stand, and "
                  "the record of how it got there is in the project's version history."},
     ]},

    # ---------------------------------------------------------------- 04
    {"id": "guarantees", "type": "cards", "title": "What you actually get", "cols": "g2",
     "lede": "Four promises, each enforced by something that fails loudly rather than by anyone remembering.",
     "items": [
         {"kicker": "Guarantee", "title": "Nothing agreed gets silently dropped",
          "text": "A requirement that nobody scheduled makes the build fail and names itself. Scope loss stops "
                  "being something you discover at the end and becomes something you fix in four minutes."},
         {"kicker": "Guarantee", "title": "The document and the data cannot disagree",
          "text": "There is only one copy of each fact. The readable document is generated from it as you open "
                  "it. There is no second version to fall out of date."},
         {"kicker": "Guarantee", "title": "\"Done\" means a check passed",
          "text": "Not \"the worker says so\". Every job names the checks that prove it, and its status can only "
                  "be set to complete after those checks actually ran and passed."},
         {"kicker": "Guarantee", "title": "You can leave it running",
          "text": "It works around blocked jobs instead of stopping at them, and survives being interrupted — on "
                  "restart it works out where it got to and carries on. An interruption costs one job, not a "
                  "night."},
     ],
     "note": {"kind": "ok", "label": "The honesty rule.",
              "text": "A check that could not run is reported as **skipped**, never counted as passed. In an "
                      "automated system the most expensive failure is not a red result — it is a green one that "
                      "was never earned."}},

    # ---------------------------------------------------------------- 05
    {"id": "build", "type": "flow", "title": "What actually builds it",
     "lede": "The four promises above rest on one piece of machinery: the run that takes a derived plan and "
             "works through it. It is worth seeing in outline before the evidence, because every guarantee on "
             "this page is a property of it.",
     "body": [
         "A unit of the plan is handed to a worker — a command named in the project's own settings, given the "
         "brief and a path to write its report to. When the work comes back, the run executes the verification "
         "checks itself, so what a check returned is something the run watched rather than something it was "
         "told. Then a second worker, who has been shown the work and the criteria and the evidence but no "
         "account of how any of it was made, decides whether it passes.",

         "That last separation is the whole design. **A build that grades its own work has no standard at "
         "all**, however carefully the grading is written down, and the only reliable way to prevent it is to "
         "make sure the grader never receives the builder's account in the first place. The full mechanism — "
         "the return rail when a judgement fails, four workers running at once without colliding, and what "
         "every bound costs when it fires — is on [the build process page](Z2S-Build.html).",
     ],
     "flows": [
         {"name": "One unit of work, start to finish",
          "caption": "Everything after the brief is watched rather than reported. The judge is the piece the "
                     "guarantees rest on.",
          "steps": [
              {"title": "A unit's brief", "kind": "input",
               "desc": "One piece of the plan, with the criteria it must meet and the check that currently "
                       "fails."},
              {"title": "A worker builds",
               "desc": "One command, doing the work and producing the evidence for it."},
              {"title": "The checks run", "kind": "gate",
               "desc": "Run by the build itself, cheapest first, so every exit status is observed rather "
                       "than claimed."},
              {"title": "Somebody else judges", "kind": "accent",
               "desc": "A second worker, shown the work and the evidence and nothing the builder said about "
                       "its own work."},
              {"title": "Committed",
               "desc": "A pass commits the files and writes the status back into the plan document that "
                       "describes the work."},
          ]},
     ]},

    # ---------------------------------------------------------------- 06
    {"id": "proof", "type": "prose", "title": "The method, run for real: Zero Style",
     "body": [
         "Zero-to-Ship was not designed on a whiteboard — it was extracted from a real build. **Zero Style** is "
         "a working web application that pairs a dictionary of graphic-design terminology with a converter that "
         "turns a plain-language description into a proper design brief. It was specified, planned and largely "
         "built by AI agents operating this method, with a person at the gates.",
         "The specification chain came first: an intent, then requirement documents — every one a single "
         "self-contained file carrying its own machine-readable data. The plan was derived from them, the "
         "coverage gate proved every requirement scheduled, and the build ran in dependency waves — agents "
         "working test-first through generated briefs, writing status back into the plan documents as they "
         "went, surviving interruptions through the ledger.",
         "When new scope arrived after the original specification had shipped — an embedding platform, then a "
         "bulk-ingest and curation admin — it came as **addenda with new identifier prefixes**. Not one "
         "existing identifier was renumbered, and the coverage gate simply grew its universe and demanded the "
         "new scope be scheduled too. The product is live in production; its plan documents remain the status "
         "board and the audit trail of how it got there.",
     ],
     "highlights": [
         {"label": "Specified", "title": "72 + 85 requirements",
          "text": "72 functional requirements and 85 technical requirements, plus 17 recorded architecture "
                  "decisions — every one traced and scheduled."},
         {"label": "Planned", "title": "16 milestones · 299 tasks",
          "text": "Twelve original milestones, four added later by addendum — every task defined by its "
                  "failing test before any code existed."},
         {"label": "Built", "title": "295 of 299 passing",
          "text": "Status live in the plan documents themselves: 295 passing, 2 awaiting human review, 1 "
                  "blocked, 1 not started. Real state, not a report."},
         {"label": "Shipped", "title": "In production",
          "text": "Deployed through a staged branch flow, promoted by a person who read the diff — the one "
                  "step the method refuses to automate."},
     ],
     "note": {"kind": "info", "label": "And this document set is the second run.",
              "text": "The eleven documents you are reading were produced by the same discipline they describe — "
                      "generated from embedded data, gated on coverage, validated against the rendered files. "
                      "The gates caught three real defects during their production. That is the point."}},

    # ---------------------------------------------------------------- 07
    {"id": "why", "type": "defs", "title": "Why it holds together",
     "intro": "For readers evaluating the method rather than commissioning it. Each of these is a structural "
              "property, not a practice — it holds whether or not anyone is being careful.",
     "items": [
         {"term": "The readable view is generated from the machine-readable data, at read time",
          "def": "Not built from it once and then maintained separately — regenerated in front of the reader "
                 "every time the file is opened. This removes drift between prose and data as a possibility "
                 "rather than as a risk, which is why it is the first rule and not an optimisation."},
         {"term": "The plan is derived from the specification",
          "def": "The plan generator reads the specifications directly and computes which requirements are "
                 "claimed by which units of work. Because the plan cannot be produced without that computation "
                 "succeeding, coverage is not a review activity — it is a precondition of having a plan."},
         {"term": "Coverage failure is not downgradable",
          "def": "No configuration turns an unscheduled requirement into a warning. A gate that can be softened "
                 "under delivery pressure is a gate that will be softened under delivery pressure."},
         {"term": "Every task carries its failing test, authored before the work",
          "def": "This is what makes a unit of work dispatchable to someone — or something — with no context. "
                 "It also has a useful side effect: a task that resists having a failing test written for it is "
                 "almost always a task that was scoped wrongly, and you find that out during planning."},
         {"term": "Validation runs against the produced file, not the data behind it",
          "def": "A generator can be correct and still emit a broken artefact — a template regression, a bad "
                 "substitution, a truncated write. Checking the inputs proves the inputs were sound. Only "
                 "checking the output proves the deliverable is."},
         {"term": "Status lives inside the plan and is written by a tool",
          "def": "One artefact is the plan, the status board and the audit trail. Because it is a file under "
                 "version control, progress is a diff — attributable, reviewable, and recoverable years later."},
         {"term": "Durable state lives in a ledger, not in memory",
          "def": "Long autonomous runs lose their working memory. Anything held only there does not survive a "
                 "restart. The ledger records done-state, decisions taken and the exact next step, so resuming "
                 "is recomputation rather than recollection."},
         {"term": "Identifiers are permanent",
          "def": "They appear in traces, test names, commit messages and conversations. Renumbering them "
                 "invalidates all of those at once, silently. So numbering has gaps, and that is correct."},
         {"term": "New scope arrives as an addendum",
          "def": "A new document with its own identifier prefix, merged into the coverage universe. Nothing that "
                 "already shipped is edited, so nothing that already resolved stops resolving."},
         {"term": "Every milestone leaves a lesson the next one must read",
          "def": "Retrospectives are inputs, not artefacts. This is the mechanism that makes the fourth wave of "
                 "work meaningfully cheaper than the first, rather than identically expensive."},
     ]},

    # ---------------------------------------------------------------- 08
    {"id": "cost", "type": "table", "title": "What it costs, and what it returns",
     "intro": "Honest accounting. The cost is real, it lands early, and it is mostly one kind of work: deciding "
              "things before building them.",
     "columns": ["", "What it costs", "What it returns"],
     "rows": [
         ["**Deciding**",
          "One focused session per document, before authoring. Every fork closed, with a recommended default "
          "offered for each.",
          "No interruptions during the build. No decision made twice. No decision made by accident."],
         ["**Specifying**",
          "Writing requirements that are atomic, testable and prioritised — slower than prose, and it feels "
          "slower.",
          "Every later artefact is derived from this one, so the effort is spent once instead of re-spent in "
          "every plan, ticket and hand-off."],
         ["**Planning**",
          "Authoring each task's failing test before the task exists. This is the largest single cost.",
          "Work becomes dispatchable to anyone or anything with no context, and completion becomes machine-"
          "checkable rather than reported."],
         ["**Tooling**",
          "A small toolchain: seven generators, a plan generator, validators, a status tool, an orchestrator, "
          "installed as one plugin. No "
          "third-party dependencies, no service to run.",
          "Runs anywhere, offline, unchanged in five years. Nothing to host, nothing to pay for, nothing to "
          "migrate."],
         ["**Discipline**",
          "Generated files are never hand-edited. Gates are never softened. Retrospectives are actually read.",
          "The guarantees stay guarantees. Every one of them fails quietly the moment its rule is treated as "
          "advisory."],
     ],
     "mono": []},

    # ---------------------------------------------------------------- 09
    {"id": "not", "type": "list", "title": "What it deliberately is not",
     "intro": "Recorded as decisions rather than omissions, so they are not revisited by default.",
     "items": [
         "**Not a hosted product.** No server, no accounts, no stored data. Files in a repository; "
         "collaboration through version control.",
         "**Not an issue tracker**, and not synchronised with one. The plan document is the tracker.",
         "**Not project management.** No schedule, no capacity model, no burndown, no estimates used as gates.",
         "**Not a substitute for judgement.** It makes decisions explicit and durable. It does not make them.",
         "**Not a correctness guarantee.** It proves that what was specified was scheduled, built and verified. "
         "It cannot prove that what was specified was a good idea.",
         "**Not tied to any language, framework, domain or vendor.**",
     ]},

    # ---------------------------------------------------------------- 10
    {"id": "start", "type": "list", "title": "How to start", "ordered": True,
     "intro": "Adoption is incremental and each step is useful alone. The minimum that delivers the core promise "
              "is steps one to four.",
     "items": [
         "**Adopt the document format.** One self-contained file per document, with the data embedded and the "
         "readable view generated from it. Immediate benefit: documents stop disagreeing with themselves.",
         "**Adopt the decision gate.** One session, before authoring, with the outcome written into a "
         "locked-decisions table. Immediate benefit: the build stops interrupting people.",
         "**Adopt identifiers and traces.** Stable, permanent, never renumbered. Immediate benefit: any piece of "
         "work can be walked back to the reason it exists.",
         "**Adopt the coverage gate.** Derive the plan and let the build fail when something is unscheduled. "
         "This is the step that converts intention into guarantee — do not skip it.",
         "**Adopt test-first task definition.** Slowest to adopt, largest return, and the precondition for "
         "everything that follows.",
         "**Adopt status write-back.** Progress becomes a diff instead of a report.",
         "**Adopt autonomous execution last**, once at least one milestone has been planned to the standard "
         "above. Automation applied to an ambiguous plan produces confident, plausible, wrong work faster.",
     ]},

    # ---------------------------------------------------------------- 11
    {"id": "reading", "type": "table", "title": "Where to go next",
     "intro": "The rest of the document set, in the order it is usually read.",
     "columns": ["Document", "Answers", "Read it if"],
     "rows": [
         ["[Intent](Z2S-Intent.html)", "What problem this exists to solve, and the principles that constrain "
          "every decision.", "You want the reasoning, not the mechanics."],
         ["[Context](Z2S-Context.html)", "The shared vocabulary — one meaning per term, scoped to bounded "
          "contexts.", "You want to know what any word in this set means, precisely."],
         ["[Product requirements](Z2S-PRD.html)", "What the method must achieve, what it will not do, and how "
          "success is measured.", "You are deciding whether to adopt it."],
         ["[Functional specification](Z2S-FSD.html)", "Exactly what the toolchain does, as prioritised, "
          "testable requirements.", "You are building or evaluating the toolchain."],
         ["[Stories & use cases](Z2S-User-Stories.html)", "How each requirement is verified, as testable "
          "scenarios.", "You are writing the tests."],
         ["[System design](Z2S-SDD.html)", "How it is built: contracts, schemas, algorithms, decisions.",
          "You are implementing it."],
         ["[Development plan](Z2S-Plan.html)", "The buildable plan for the toolchain itself.",
          "You are scheduling the work."],
         ["[Playbook](Z2S-Playbook.html)", "The step-by-step operating manual.",
          "You have the toolchain and want to run the method."],
         ["[The build process](Z2S-Build.html)", "What the run does with a plan: the cycle, the two kinds of "
          "worker, the verification ladder and every bound.",
          "You are judging whether an unattended build can be trusted, or about to operate one."],
     ]},
]
