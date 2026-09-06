# -*- coding: utf-8 -*-
"""Zero-to-Ship — Operating manual. Numbered steps, literal commands, gates, stop conditions."""

DOC = {
    "title": "Zero-to-Ship — Operating Playbook",
    "slug": "playbook",
    "kicker": "Operating manual",
    "type": "Step-by-step playbook",
    "version": "2.14",
    "status": "For use",
    "date": "2026-09-06",
    "owner": "Zerø Effort",
    "releaseScope": "Full method, from intent to promoted release",
    "summary": "Run the method start to finish. Each step states what to do, what it produces, the gate that must "
               "pass before moving on, and the condition that means stop.",
    "scopeNote": "The method is operated through the /zero:* skill chain, installed as one plugin (step A1). "
                 "Every skill is invoked deliberately — none fires on its own except /zero:questions, the shared "
                 "clarification interview the others route their questions through. You never type a shell "
                 "command: every skill executes its own mechanics, and /zero:init repairs missing setup whenever "
                 "a chain skill finds it. Where a step says STOP, it means stop — the failure it names cannot be "
                 "worked around without breaking a guarantee.",
}

SECTIONS = [
    {"id": "before", "type": "prose", "title": "Before you start",
     "body": [
         "This playbook has six phases: **set up**, **specify**, **plan**, **execute**, **promote**, **amend**. "
         "Phases A to C are done by people. Phase D can be run by people, by agents, or by both — every unit "
         "of the plan carries its own pasteable instructions, so handing one over by hand and letting a run "
         "dispatch it are the same contract delivered two ways. Phases E and F always involve a person.",
         "Two rules override everything below. First: **generated files are never hand-edited** — to change one, "
         "change its source and regenerate. Second: **a gate is never softened** — if a gate fails, the fix is "
         "the content, never the gate.",
     ],
     "note": {"kind": "info", "label": "Notation.",
              "text": "`/zero:…` is a skill invoked in the agent session — the only kind of command in this "
                      "playbook; the skills run every shell-level mechanic themselves. **Do** is the action. "
                      "**Gate** is what must be true before the next step. **Stop if** is the condition under "
                      "which you must not continue. Whenever a skill needs an answer, the question arrives "
                      "through `/zero:questions` — numbered, in rounds, each with a recommended answer."}},

    {"id": "steps", "type": "steps", "title": "The procedure", "flush": True,
     "groups": [

# ---------------------------------------------------------------- A
{"key": "A", "title": "Phase A — Set up", "intro": "Once per project.",
 "steps": [
  {"id": "S-A1", "n": "A1", "title": "Install the skill chain", "owner": "Planner",
   "body": ["One install action brings in the whole chain — every generator, the plan generator, the validators, "
            "the status tool, the orchestrator, init, the design step and the clarification interview, at "
            "pinned versions."],
   "commands": ["/plugin marketplace add apatheticus/z2s",
                "/plugin install zero@z2s"],
   "produces": ["The complete /zero:* skill chain, invocable by name."],
   "gate": ["Every /zero:* skill is invocable by name."],
   "stopif": ["The install does not resolve to pinned versions — an unpinned chain drifts under you between "
              "sessions."]},

  {"id": "S-A2", "n": "A2", "title": "Initialise the project", "owner": "Planner",
   "body": ["`/zero:init` performs every setup mechanic itself: it creates the documented `.zero/` layout — "
            "specifications, plan data, generated plans, retrospectives, ledger — writes the ignore rules, and "
            "detects the host project's design system so documents adopt its tokens. If there is no design "
            "system, the neutral theme is used — a valid outcome, not a failure. Every chain skill runs init "
            "automatically when it finds setup missing; invoking it here just lets you review the result before "
            "anything else happens.",
            "What init detects is a starting point, not the whole design system. `/zero:design` is the step that "
            "reads the documents you name — a brand book, a design guide, a stylesheet, a token file — merges "
            "what they state, and writes the result down: every adopted value beside the file and the name it "
            "came from. Anything a document states only in prose is asked about before it is adopted, never "
            "guessed. Run it whenever the design system changes; correcting a value it read wrongly is one edit "
            "to that record, not a bug report.",
            "The two are separate on purpose. Init promises that running it twice changes nothing, which is what "
            "lets every other skill run it unasked. A refresh rewrites the record by definition, so it needs its "
            "own door."],
   "commands": ["/zero:init   # idempotent — safe to run at any time",
                "/zero:design brand-book.html DESIGN.md   # any mix of documents, stylesheets, token files"],
   "produces": ["The `.zero/` directory layout.",
                "Ignore rules: the ledger excluded, generated plan documents included.",
                "A resolved token set, or an explicit statement that the neutral fallback is in use.",
                "A design record naming every adopted value's source — reviewable, correctable, committed."],
   "gate": ["Every documented path exists under `.zero/`.",
            "The ledger directory is ignored; the generated plan directory is tracked.",
            "The resolved theme is reported by name; no colour, font or shadow value is hard-coded outside the "
            "token block.",
            "Every value in the design record names where it was read from."],
   "stopif": ["You cannot commit generated plan documents — without them, progress has no history and the status "
              "model does not work.",
              "The theme detection silently produces a theme you did not expect — find out which source it read "
              "before generating anything.",
              "A value was adopted from prose you were never asked about. Nothing a document only describes may "
              "be taken without your answer."],
   "why": "The ledger is transient run state and does not belong in history. The plan documents carry status, "
          "so they do — this is a deliberate exception to the usual rule against committing generated output."},

  {"id": "S-A3", "n": "A3", "title": "Name the verification gauntlet", "owner": "Planner",
   "body": ["The init interview asks for the exact commands that constitute 'verified' in this project — unit, "
            "integration, end-to-end, static analysis, build. Every task will name a subset of them. You supply "
            "each command as an answer; `/zero:init` records the gauntlet where every worker brief can quote "
            "it, and verifies each command exits non-zero on a seeded failure before accepting it."],
   "produces": ["The gauntlet, recorded where every worker brief can quote it — each entry verified against a "
                "seeded failure."],
   "gate": ["Every command exits non-zero on a seeded failure — verified by init, never assumed."],
   "stopif": ["Any command reports success on a seeded failure. A gauntlet that cannot fail cannot verify "
              "anything, and every downstream guarantee rests on it."],
   "why": "Every 'passing' status in the entire project ultimately means 'these commands ran and exited zero'. "
          "If one of them lies, the whole record lies."}]},

# ---------------------------------------------------------------- B
{"key": "B", "title": "Phase B — Specify", "intro": "Once per release. The order matters: each document answers "
                                                    "a question the previous one raised.",
 "steps": [
  {"id": "S-B1", "n": "B1", "title": "Run the decision gate", "owner": "Owner + author",
   "body": ["Before authoring anything, surface every unresolved fork and close it. One question at a time, each "
            "with a recommended default so the owner can agree rather than compose. Grill the premise too, not "
            "only the options — constraint collisions found here are free, and found later are expensive."],
   "prompt": "Identify every fork in this brief that would change what gets built. For each, ask me one question\n"
             "with 2-4 concrete options, exactly one marked (Recommended), and state what each option means in\n"
             "terms of what will actually exist. Do not write any file until every fork is closed. Then write a\n"
             "locked-decisions table (# | Decision | Choice | Rationale) into the document and the ledger.",
   "produces": ["A locked-decisions table in the document and in `.zero/state/<slug>.md`."],
   "gate": ["Every identified fork has a recorded decision, choice and rationale.",
            "No file has been written yet."],
   "stopif": ["A fork cannot be resolved — record it as an open question and mark anything depending on it as "
              "lowest priority. Do not resolve it by guessing.",
              "Two question batches in a row are rejected — stop asking, draw the model you are asking about, "
              "get agreement on it, then resume."],
   "why": "A question asked after authoring begins arrives when work already exists in the shape of the wrong "
          "assumption. The gate concentrates the owner's attention into the cheapest moment."},

  {"id": "S-B2", "n": "B2", "title": "Derive the intent", "owner": "Author",
   "body": ["Start of the chain. `/zero:intent` accepts any combination of narrative, source documents and web "
            "addresses, derives the problem, principles, personas and capabilities, and asks — through "
            "`/zero:questions` — whatever it needs to confirm direction, fill gaps or resolve ambiguity. It "
            "maintains a register of every source it consulted."],
   "commands": ["/zero:intent brief.md notes/ https://…   # any mix of narrative, documents, URLs"],
   "produces": ["A validating intent document with identified capabilities.",
                "The source register: every consulted source, its origin and what it contributed."],
   "gate": ["The intent validates and every capability carries an identifier.",
            "Every fact in the intent is traceable to a source or recorded as an assumption.",
            "Sections with no real content are absent, not empty."],
   "stopif": ["The skill has invented a metric, persona or constraint the sources never stated — that is a "
              "defect, not a convenience. Remove it and record an open question instead."]},

  {"id": "S-B3", "n": "B3", "title": "Establish the shared language", "owner": "Author + owner",
   "body": ["Before any requirement is written, `/zero:context` derives the project's vocabulary from the intent "
            "and its source register: one definition per term, synonyms retired, colliding meanings scoped to "
            "named bounded contexts. Every collision is resolved by asking, never by picking silently — this is "
            "the one step where arguing about words is the work."],
   "commands": ["/zero:context   # requires a completed Intent; refuses otherwise"],
   "produces": ["The context document: bounded contexts, the glossary, the context map.",
                "The ubiquitous language every later document, test name and commit message uses."],
   "gate": ["Every glossary term has exactly one definition and a recorded source.",
            "Every collision was resolved through the interview, and scoped terms appear on the context map.",
            "The owner has read the glossary and agrees these are their words."],
   "stopif": ["Two stakeholders still disagree on what a core term means. That disagreement is a requirements "
              "conflict wearing a vocabulary costume — resolve it here, where it costs a conversation, not in "
              "the build, where it costs a rewrite."],
   "why": "Most specification defects are two people using one word for two things. Ten minutes of glossary "
          "argument here removes a class of defect no test suite can catch later."},

  {"id": "S-B4", "n": "B4", "title": "Generate the product requirements", "owner": "Author",
   "body": ["Goals, non-goals, journeys, measures and risks, each tracing to a capability, all speaking the "
            "language established in B3."],
   "commands": ["/zero:prd   # requires a completed Context; refuses otherwise"],
   "produces": ["A validating product-requirements document tracing upward to the intent."],
   "gate": ["The document validates.", "Every goal traces to a capability that exists.",
            "Only canonical glossary terms appear — no retired synonym survives."],
   "stopif": ["A goal has no measurable outcome. An unmeasurable goal cannot fail, and a goal that cannot fail "
              "is decoration."]},

  {"id": "S-B5", "n": "B5", "title": "Generate the functional specification", "owner": "Author",
   "body": ["The document the whole chain traces to. Requirements are atomic, testable and prioritised, grouped "
            "into six to twelve areas. Deliberate exclusions are recorded as lowest-priority entries with a "
            "reason — never dropped."],
   "commands": ["/zero:fsd   # requires a completed PRD; refuses otherwise"],
   "produces": ["Prioritised functional requirements with stable identifiers."],
   "gate": ["Every requirement belongs to a declared area and carries a priority.",
            "No requirement names a technology or an implementation.",
            "Every deliberate exclusion is present with its reason."],
   "stopif": ["A requirement cannot be stated as observable behaviour — it is probably a technical requirement. "
              "Move it to the technical specification rather than weakening it."],
   "why": "Identifiers allocated here appear in stories, tasks, test names and commit messages for the life of "
          "the project. They are never renumbered, so allocate them carefully once."},

  {"id": "S-B6", "n": "B6", "title": "Generate stories and use cases", "owner": "Author",
   "body": ["Turn each functional requirement into a goal-level story with Given/When/Then scenarios, plus "
            "actor-centred use cases for flows that span several stories. Scenario identifiers become test "
            "names."],
   "commands": ["/zero:stories   # requires a completed FSD; refuses otherwise"],
   "produces": ["Stories, use cases, and the derived requirement-to-story matrix."],
   "gate": ["Every non-excluded functional requirement is covered by at least one story or use case.",
            "Scenario identifiers are unique.",
            "No scenario asserts on generated wording — structure only."],
   "stopif": ["A requirement cannot be given a testable scenario. Either it is not really a requirement, or it "
              "is two requirements. Split it or drop it; do not write an untestable acceptance criterion."]},

  {"id": "S-B7", "n": "B7", "title": "Generate the technical specification", "owner": "Author",
   "body": ["Technical requirements, architecture decisions with context, alternatives and consequences, and "
            "targets stated as numbers with units. Runs from the FSD, in parallel with the stories if you "
            "like — neither depends on the other."],
   "commands": ["/zero:sdd   # requires a completed FSD; refuses otherwise"],
   "produces": ["Technical requirements, decision records and measurable targets."],
   "gate": ["Every technical requirement traces upward.",
            "Every decision carries context, alternatives and consequences.",
            "Every target is a number with a unit and a note on how it is measured."],
   "stopif": ["A target is an adjective. 'Fast' cannot become an acceptance criterion; a number can."]},

  {"id": "S-B8", "n": "B8", "title": "Review the set", "owner": "Owner + reviewer",
   "body": ["Read the set end to end. Run an independent adversarial pass — a reviewer who did not author it. "
            "Record disagreements as open questions rather than resolving them by editing quietly. The freeze "
            "itself is mechanical and happens in the next phase: `/zero:plan` strictly validates and freezes "
            "the set as its first act."],
   "produces": ["A reviewed specification set with every open question dispositioned."],
   "gate": ["An adversarial pass by a non-author has happened.",
            "Every open question is either closed or explicitly accepted as open."],
   "stopif": ["You are tempted to proceed with a known contradiction 'to be resolved during the build'. It will "
              "be resolved during the build — by whoever hits it first, invisibly, in whichever direction is "
              "convenient."]}]},

# ---------------------------------------------------------------- C
{"key": "C", "title": "Phase C — Plan", "intro": "Once per release, then extended one wave ahead as the build "
                                                 "proceeds.",
 "steps": [
  {"id": "S-C1", "n": "C1", "title": "Derive the plan", "owner": "Planner",
   "body": ["One skill runs the whole phase. `/zero:plan` strictly validates and freezes the specification set, "
            "then interviews you — through `/zero:questions` — for the shape of the build: milestones, their "
            "dependencies, their exit criteria and the requirement sets each claims. It authors phases and "
            "tasks test-first for the next wave only — each task stating its failing test, minimum change, "
            "clean-up, autonomy class, verification layers and at least one machine-checkable criterion — then "
            "computes coverage and dependency waves, emits the plan index and one document per milestone, "
            "validates the rendered output, and commits the result."],
   "commands": ["/zero:plan   # requires completed Stories, FSD and SDD; refuses otherwise"],
   "produces": ["A frozen, validated specification set.",
                "The milestone spine with dependency edges and exit criteria.",
                "Phases and tasks for the next wave, each defined test-first.",
                "The plan index with coverage matrix, waves and prompts; one document per milestone — "
                "committed, the starting point of the progress history."],
   "gate": ["Every milestone has exit criteria and the dependency graph is acyclic.",
            "Every task has a red, green and refactor step, an autonomy class, and at least one "
            "machine-checkable criterion; every task touching a live credential or paid provider is classed "
            "human-gated.",
            "Every requirement and decision appears in the coverage matrix with at least one claiming unit.",
            "The rendered-artefact validator passes, and regenerating produces no diff."],
   "stopif": ["Any requirement is reported uncovered. Answer the interview — schedule it, or record an explicit "
              "exclusion with a reason. **Never edit the generated HTML**, and never look for a way to make the "
              "gate quieter.",
              "A task resists having a failing test written for it. That almost always means it is scoped "
              "wrongly — have the interview split it until each part has an edge.",
              "You are asked to detail every milestone at once. Author one wave ahead; later waves will be "
              "rewritten by what earlier ones learn."],
   "why": "The red step is the entire mechanism that lets a worker with no context know when to stop — the most "
          "expensive part of planning and the reason execution is cheap. And the coverage gate is the method's "
          "central claim: a coverage failure is not an obstacle to generating the plan, it is the plan "
          "generator correctly refusing to produce a plan that loses scope."},

  {"id": "S-C2", "n": "C2", "title": "Review the shape with the operator", "owner": "Planner + operator",
   "body": ["Open `.zero/plan/index.html` in a browser and read the derived wave ordering and the prerequisite "
            "checklist together. Prerequisites are human-owned work — accounts, credentials, provisioned "
            "services — and every one of them must be cleared or explicitly classed human-gated before an "
            "unattended run starts."],
   "produces": ["An agreed execution shape and a cleared prerequisite list."],
   "gate": ["Every prerequisite is either done or has its dependent tasks classed human-gated.",
            "The wave ordering is understood and accepted."],
   "stopif": ["A wave contains two milestones that obviously write the same files. Re-group them now; discovering "
              "it as file contention at three in the morning is more expensive."]}]},

# ---------------------------------------------------------------- D
{"key": "D", "title": "Phase D — Execute", "intro": "Repeated per wave until the release is built.",
 "steps": [
  {"id": "S-D1", "n": "D1", "title": "Start the run", "owner": "Operator",
   "body": ["`/zero:build` opens the ledger as its very first act — before the first unit of work, not at the "
            "point of memory pressure. The ledger — not anyone's working memory — is the authority on "
            "done-state, decisions and the next step. Then it reads the plan, recomputes the ready set, and "
            "works through the build prompts wave by wave. Leave it alone — the questions were answered in "
            "phase B. Its orchestration contract is the prompt below, and what the run does with it — "
            "the cycle, the separated judge, the bounds and what each one costs when it fires — is "
            "set out in full on [the build process page](Z2S-Build.html)."],
   "commands": ["/zero:build   # requires a generated, validated plan; refuses otherwise"],
   "prompt": "Open the ledger .zero/state/<slug>.md — create it first if absent — then read\n"
             ".zero/plan/index.html. Walk the waves in order. For each wave, dispatch one worker per ready\n"
             "milestone using that milestone's own generated prompt. A unit is ready when it is not started,\n"
             "every dependency is passing, and it is not human-gated. Never dispatch two units with\n"
             "overlapping write sets. Fully autonomous: never ask a question — make the reasonable call, log\n"
             "it under DECISIONS in the ledger, and continue. After each unit: write status back, commit,\n"
             "update the ledger. Stop when no unit is ready and every exit criterion is met.",
   "produces": ["`.zero/state/<slug>.md` with status, decisions, next step and lessons sections — before the "
                "first unit starts.",
                "Completed units, commits, status write-backs and ledger entries."],
   "gate": ["The ledger exists and names the plan it tracks before the first unit starts.",
            "No question is emitted during the run.",
            "Every completed unit has a status change committed alongside its work.",
            "The ledger records the next step before each advance."],
   "stopif": ["The run asks a question — that is a gate defect. Answer it, record it as a locked decision, and "
              "fix the gate for the next release.",
              "A unit uses a live credential or opens an interactive prompt. Stop the run: the autonomy "
              "classification is wrong and everything it produced under that assumption is suspect.",
              "A run is somehow more than one unit in with no ledger — that is a defect in the build skill; "
              "stop the run and record it."]},

  {"id": "S-D0", "n": "D0", "title": "Hand one unit over by hand", "owner": "Operator",
   "body": ["Phase D does not have to be autonomous. Every unit of the plan — the whole build, a milestone, a "
            "phase, a single task — carries its own complete instructions, folded shut on that unit's own card "
            "in the plan document. Open the card, press **Copy prompt**, paste it into a fresh session. You "
            "choose the size of the handover; nothing about the contract changes with it.",
            "`/zero:prompt` prints the same text at a terminal if that is easier. It prints what the document "
            "already carries, so the two cannot say different things.",
            "What comes out is not a to-do list. It names what the unit waits on, the acceptance criteria as "
            "the floor, the requirements and stories the work is aiming at above that floor, and the loop: "
            "split it yourself, have a **separate** reader in fresh context judge each piece against the "
            "criteria and never against your account of them, take the one gap a failure returns, and go "
            "again. No number of rounds — the bar decides when it is done."],
   "commands": ["/zero:prompt M1-P1-T1   # one task",
                "/zero:prompt M1-P1      # one phase",
                "/zero:prompt M1         # one milestone",
                "/zero:prompt plan       # the whole build"],
   "produces": ["One self-contained prompt, ready to paste, at the granularity you chose."],
   "gate": ["The prompt names what the unit waits on, and you have checked those are passing.",
            "Whoever runs it understands that they appoint the critic and that the critic never sees their "
            "account of the work."],
   "stopif": ["You are about to edit the prompt before pasting it. A prompt somebody improved on the way past "
              "is a prompt nobody can reproduce — fix the plan and regenerate instead.",
              "The prompt says the unit has no higher target and you are tempted to supply one. Do not. A "
              "ceiling nobody decided is an invented standard, and it will be graded as though somebody had."],
   "why": "An unattended run and a pasted prompt are the same contract delivered two ways. Neither is the "
          "weaker option, and choosing between them is a question about how much you want to watch — not "
          "about how carefully the work gets done."},

  {"id": "S-D2", "n": "D2", "title": "Each unit, test-first", "owner": "Worker",
   "body": ["The loop every worker follows, whether human or agent. It is short by design. The status "
            "write-back and the commit are performed by the worker's own tooling — part of the unit, never a "
            "separate manual chore."],
   "commands": ["1. Read the brief, the plan, and every prior retrospective.",
                "2. Write the task's stated failing test. Run it. Confirm it fails.",
                "3. Write the minimum change that makes it pass.",
                "4. Refactor under a green suite.",
                "5. Run the verification layers the task names.",
                "6. Write the status back: task passing, criteria ticked.",
                "7. Commit, with the task identifier in the subject.",
                "8. Return the structured report."],
   "produces": ["The implementation, its tests, a status change, a commit and a report."],
   "gate": ["The failing test was observed failing before the implementation existed.",
            "The named verification layers actually ran and passed in this run.",
            "The report names the command that produced each result."],
   "stopif": ["The test passes before the implementation is written — the test is wrong, or the work is already "
              "done. Find out which.",
              "Status would be set to passing without the verification having run. Never do this; a false green "
              "is more expensive than any red."],
   "why": "Steps 2 and 5 are what make the status trustworthy. Everything else in the method is bookkeeping "
          "around them."},

  {"id": "S-D3", "n": "D3", "title": "Handle a blocked unit", "owner": "Worker",
   "body": ["Bounded retries, then step aside. The worker records the unit blocked — the blocker, what was "
            "tried, the workaround chosen — and the run continues with the next ready unit. A run that stalls "
            "on one problem has converted a small failure into a large one."],
   "produces": ["A blocked unit with its blocker and chosen workaround recorded."],
   "gate": ["The blocker names what was tried and why it failed.",
            "The run continued with the next ready unit."],
   "stopif": ["The same unit has been retried beyond its stated limit. Record and move on — repeated identical "
              "attempts are not persistence.",
              "A permission or policy denial is being reshaped into a different command to slip past it. Report "
              "the gate; do not route around it."]},

  {"id": "S-D4", "n": "D4", "title": "Close the milestone", "owner": "Operator",
   "body": ["At each milestone boundary `/zero:build` reports every exit criterion with its evidence, lists the "
            "outstanding human-review criteria, and drafts the retrospective. Your job is the part no machine "
            "performed: check each exit criterion against real evidence — the live system, the actual command "
            "output, not a remembered result or another worker's report — and read and sign off (or "
            "explicitly defer) each human-review item. Only then does the milestone close."],
   "produces": ["A closed milestone and its retrospective."],
   "gate": ["Every exit criterion is evidenced against a live source.",
            "Every human-review criterion is signed off or explicitly deferred with a reason.",
            "The retrospective exists and includes the decisions recorded during the milestone."],
   "stopif": ["An exit criterion cannot be evidenced. The milestone does not close; the gap becomes a task.",
              "You are about to sign off human-review items in bulk without reading them. That is the one check "
              "no machine performed."]},

  {"id": "S-D5", "n": "D5", "title": "Resume after an interruption", "owner": "Operator",
   "body": ["Runs are interrupted. This is routine, not an incident. `/zero:action` works out where everything "
            "stands — ledger first, then the plan — and continues from there; it works at any point in the "
            "method, from a half-finished specification chain to a half-finished wave. With no completed intent "
            "at all, it starts the chain from the beginning. A missing ledger is recreated from the plan's "
            "recorded status."],
   "commands": ["/zero:action   # inspects the set and the ledger, resumes from wherever you left off"],
   "produces": ["A resumed run continuing from the correct point."],
   "gate": ["No completed unit is repeated.", "No pending unit is skipped.",
            "Any disagreement between ledger and plan is recorded, with the plan preferred."],
   "stopif": ["The plan fails validation on resume. Do not execute against an invalid plan — fix it first.",
              "A unit is marked in progress with no owning worker. Reset it to not started and re-dispatch; "
              "half-finished work claiming to be in flight is how duplicates happen."]}]},

# ---------------------------------------------------------------- E
{"key": "E", "title": "Phase E — Promote", "intro": "Per release. Always involves a person.",
 "steps": [
  {"id": "S-E1", "n": "E1", "title": "Ship the working branch", "owner": "Owner + operator",
   "body": ["`/zero:ship` runs the phase. First the preflight: it re-runs every recorded gate against the live "
            "system — the gauntlet, the pipeline, deployment health — now, and reports each result with the "
            "date its source states; not a remembered result, not a badge seen earlier, not another agent's "
            "report. Then it presents the change log and diff for a person to read — no amount of green "
            "automation replaces that — commits and pushes the working branch, and asks, never assumes, "
            "whether to open the promotion request."],
   "commands": ["/zero:ship   # preflight gates live and dated → present the diff → commit, push → ask about "
                "the pull request"],
   "produces": ["A dated, sourced confirmation of each gate.",
                "A pushed working branch and, on an explicit yes, an open promotion request."],
   "gate": ["Each gate confirmed against the system itself, with the date the source reports; anything older "
            "than the current work re-fetched before it is relied on.",
            "A person has read the diff."],
   "stopif": ["A gate's status is being asserted from memory or from a summary. Re-derive it or mark the claim "
              "unverified and say so out loud.",
              "Nobody has read the diff. The automation proves the work matches the specification; only a "
              "person can judge whether the specification was right."]},

  {"id": "S-E2", "n": "E2", "title": "Promote", "owner": "Owner",
   "body": ["The merge itself stays a human click, made in the forge's interface. This is the one action in "
            "the whole method that is deliberately manual."],
   "produces": ["A promoted release."],
   "gate": ["A human approval is recorded.", "The merge preserves each unit as a distinct commit."],
   "stopif": ["Anything or anyone proposes automating this click. The method's guarantees end at proving the "
              "work matches the specification; promotion is a judgement."]},

  {"id": "S-E3", "n": "E3", "title": "Verify the deployment actually happened", "owner": "Operator",
   "body": ["A merge is not a deployment and a deployment is not a working system. Run `/zero:ship` again after "
            "the merge: with a clean tree and a promoted release it switches to verification — confirming the "
            "deployment is present and querying the live endpoint — and reports what the real system says."],
   "commands": ["/zero:ship   # after the merge: verifies the deployment is present and the live endpoint "
                "healthy"],
   "produces": ["Evidence that the release is live and healthy."],
   "gate": ["The deployment is confirmed present and healthy against the live system."],
   "stopif": ["The deployment succeeded but the live check fails. Roll back and record it as a blocker — a "
              "successful deploy of a broken system is still a broken system."]}]},

# ---------------------------------------------------------------- F
{"key": "F", "title": "Phase F — Amend", "intro": "Whenever scope arrives after the specification was frozen.",
 "steps": [
  {"id": "S-F1", "n": "F1", "title": "Author an addendum, never edit the original", "owner": "Author",
   "body": ["New scope is a new document with its own identifier prefix, folded in through `/zero:update` — the "
            "forward-only update skill. The originals are not touched, so every existing identifier, trace, "
            "test name and commit reference keeps resolving."],
   "commands": ["/zero:update   # describe the new scope; it authors the addendum, forward-only"],
   "produces": ["Addendum documents with registered identifier prefixes."],
   "gate": ["No original file changed.", "The new prefix routes trace links to the addendum.",
            "Generation still succeeds when the addendum is absent."],
   "stopif": ["You are about to renumber or reuse an identifier. This silently invalidates every existing trace, "
              "test name and reference. Retire in place instead; gaps in numbering are correct."]},

  {"id": "S-F2", "n": "F2", "title": "Annotate anything superseded, in place", "owner": "Author",
   "body": ["Where a new decision changes an earlier requirement, annotate the original with the amendment and "
            "its date. Do not quietly rewrite it — the earlier text is the reason earlier work looks the way it "
            "does. `/zero:update` applies amendments this way by construction: it never deletes or overwrites "
            "published content."],
   "commands": ["/zero:update   # name the entry and the change; it amends in place, dated"],
   "produces": ["An in-place, dated amendment annotation that survives regeneration."],
   "gate": ["The annotation and its date survive a regeneration.",
            "The original text remains readable alongside it."]},

  {"id": "S-F3", "n": "F3", "title": "Re-derive and re-prove coverage", "owner": "Planner",
   "body": ["New requirements are unclaimed by definition. Re-run `/zero:plan` so the coverage gate forces an "
            "explicit scheduling decision."],
   "commands": ["/zero:plan   # regenerates; the coverage gate names every new unclaimed identifier"],
   "produces": ["An updated plan in which the new scope is scheduled or explicitly excluded."],
   "gate": ["The coverage gate passes.",
            "Every new identifier is claimed by a unit of work or excluded with a reason."],
   "stopif": ["The new scope is 'obviously' going to be picked up later. That is exactly the assumption the "
              "coverage gate exists to refuse."]},

  {"id": "S-F4", "n": "F4", "title": "Give a whole new piece of work its own feature", "owner": "Planner",
   "body": ["Scope large enough to have its own requirements, its own plan and its own definition of done is "
            "a **feature**, not an addendum. `/zero:feature open <name>` gives it its own specifications, plan "
            "and run state, numbered in the order they were opened, underneath the project's intent, "
            "vocabulary, workers and design — which stay shared and are never copied into it. Then run the "
            "chain from B2 inside it: it writes its own intent, requirements, stories and technical design, "
            "reads the project's vocabulary rather than writing a second one, and proves coverage over its "
            "own identifiers alone.",
            "One feature is open at a time. Anything small that arrives while one is open goes into it as an "
            "addendum (F1) — never as a second feature. When the work is done, `/zero:feature close` audits "
            "it first: every unit of its plan not passing, every retired identifier naming no successor, "
            "every question its documents left open, and everything built but not shipped. With no reason "
            "given, that audit must come back clean or the close is refused and lists what is open. Parking "
            "it unfinished is allowed and is a decision you have to state: close it with a reason, and the "
            "findings are recorded as what was left."],
   "commands": ["/zero:feature status                 # which feature is open, and what a close would find",
                "/zero:feature open <name>            # opens the next one; refused while one is open",
                "/zero:feature close --date YYYY-MM-DD          # needs a clean audit",
                "/zero:feature close \"<why it is unfinished>\" --date YYYY-MM-DD   # records what was left"],
   "produces": ["A feature with its own specification chain, plan and run state, and a closing record naming "
                "the date, the reason and anything left."],
   "gate": ["The project's vocabulary is read by the feature and is not rewritten inside it.",
            "Coverage over the feature names the feature's own identifiers and nothing else.",
            "A close with no reason came back with a clean audit."],
   "stopif": ["You are about to open a second feature to get around something the open one has left. Two "
              "open features means two answers to where a document goes and which plan the run reads. Close "
              "the first — with a reason if it is unfinished — or fold the work in as an addendum.",
              "You are about to hand-edit a closed feature's documents to make its audit look clean. The "
              "record of what was left is the point of the audit."]}]},
     ]},

    {"id": "antipatterns", "type": "list", "title": "Failure modes, and what they actually mean",
     "intro": "Each of these looks like a small pragmatic shortcut and removes one of the method's guarantees "
              "entirely.",
     "groups": [
      {"label": "Symptom", "title": "\"I'll just fix the generated file\"",
       "items": ["The change is lost at the next regeneration.",
                 "The file now disagrees with its source and nothing will detect it.",
                 "**Fix**: change the source and regenerate. If that is hard, that is the bug."]},
      {"label": "Symptom", "title": "\"The coverage gate is too strict for now\"",
       "items": ["The one gate that converts intention into guarantee has been switched off.",
                 "Scope loss returns immediately and invisibly.",
                 "**Fix**: schedule the requirement, or record an explicit exclusion with a reason. Both take "
                 "minutes."]},
      {"label": "Symptom", "title": "\"The tests pass\" with no command named",
       "items": ["An unverifiable claim, indistinguishable from a false one.",
                 "**Fix**: name the command and quote its result, or mark the claim unverified."]},
      {"label": "Symptom", "title": "\"I'll ask the owner when I get there\"",
       "items": ["The question arrives when the answer is most expensive, and interrupts the person who was "
                 "promised they would not be interrupted.",
                 "**Fix**: make the reasonable call, record it as a decision with rationale, continue. Take it "
                 "to the next gate."]},
      {"label": "Symptom", "title": "\"This task is too big to write a failing test for\"",
       "items": ["It is not too big to test; it is too big to be one task.",
                 "**Fix**: split it until each part has an edge a machine can detect."]},
      {"label": "Symptom", "title": "\"Retrospectives are overhead\"",
       "items": ["Every wave then pays full price for every lesson the previous wave already bought.",
                 "**Fix**: require reading them in the brief. Unread retrospectives genuinely are overhead — "
                 "that is an argument for reading them, not for skipping them."]},
      {"label": "Symptom", "title": "\"The run stalled overnight\"",
       "items": ["Something asked a question, hit an interactive prompt, or retried forever.",
                 "**Fix**: check the autonomy classification of the unit it stopped on, and the retry bound. Both "
                 "are planning defects, not runtime ones."]},
      {"label": "Symptom", "title": "\"The agent helpfully regenerated a document nobody asked for\"",
       "items": ["A chain skill fired without being invoked — the manual-trigger rule has been lost.",
                 "Whatever the regeneration overwrote is now a diff nobody planned.",
                 "**Fix**: every chain skill is manual-invocation only, enforced in its definition. The only "
                 "skill allowed to fire on its own is the clarification interview."]},
     ]},

    {"id": "minimum", "type": "list", "title": "The minimum viable subset", "ordered": True,
     "intro": "If you adopt nothing else, adopt these four. Together they deliver the core promise; each one "
              "alone delivers something useful. Each names the requirement it satisfies, so partial adoption is "
              "a decision you can point at rather than a gap you discover later (`NFR-ARC-05`).",
     "items": [
         "**One file per document, readable view generated from embedded data.** Removes drift between prose and "
         "data. — `FR-DOC-01`, `ADR-01`, `ADR-02`",
         "**A decision gate before authoring, with a locked-decisions table.** Removes mid-build interruptions "
         "and decisions made twice. — `FR-SPC-01`, `ADR-10`",
         "**Stable identifiers and upward traces.** Makes any piece of work explicable. — `FR-TRC-01`, `ADR-03`",
         "**A derived plan with a blocking coverage gate.** Converts \"we think we covered everything\" into a "
         "command that fails when you have not. — `FR-TRC-04`, `ADR-04`",
     ],
     "note": {"kind": "ok", "label": "Everything else is amplification.",
              "text": "Test-first task definition, status write-back and autonomous execution each multiply the "
                      "value of the four above. None of them substitutes for any of them."}},

    {"id": "adoption", "type": "list", "title": "Adopting this in a project that already exists",
     "ordered": True,
     "intro": "The order below is the whole of the advice. Every step pays for itself before the next one "
              "starts, every step is usable on its own, and no step needs the one after it — which is what "
              "`NFR-ARC-05` means by separable. A project that stops after step 3 has stopped somewhere sensible. "
              "Adopting them in a different order is the common way this fails: coverage before identifiers has "
              "nothing to count, and execution before a plan has nothing to run.",
     "items": [
         "**Write the intent and the context document. Nothing else.** Two documents, generated, in the "
         "repository. You now have one agreed statement of what the thing is for and one agreed meaning per "
         "word. Cost: an afternoon. Pays for itself the first time two people were about to build different "
         "things. — `FR-DOC-01`, `FR-CTX-01`",
         "**Put the decision gate in front of the next document you write.** Every fork answered once, before "
         "authoring, in a table nobody re-opens. This is the step that stops a build being interrupted, and it "
         "works whether or not you ever generate another document. — `FR-SPC-01`, `ADR-10`",
         "**Give every requirement a permanent identifier and an upward trace.** Existing requirements keep the "
         "numbers they have; new ones are added, never renumbered. From here on, any change can be explained by "
         "pointing at what it serves. — `FR-TRC-01`, `FR-TRC-03`, `ADR-03`",
         "**Derive the plan from the specifications, and turn the coverage gate on.** The first run will fail. "
         "That failure is the value: it is the list of things nobody was building. Schedule them or exclude them "
         "with a reason — both take minutes, and neither is negotiable afterwards. — `FR-TRC-04`, `FR-PLN-01`, "
         "`ADR-04`",
         "**Move status into the plan document and write it back with the tool.** Progress stops living in "
         "somebody's head or in a second system that disagrees. — `FR-STA-01`, `ADR-05`",
         "**Only then, hand a unit of work to a worker.** Autonomous execution needs everything above it to be "
         "true; adopted earlier it dispatches confident work against an unagreed specification. — `FR-EXE-01`, "
         "`FR-EXE-14`",
         "**Close each milestone with a retrospective, and require reading them.** The last step because it is "
         "the one that compounds: it is worth least in month one and most in month six. — `FR-LRN-01`, "
         "`FR-LRN-02`, `ADR-14`",
     ],
     "note": {"kind": "info", "label": "Where a large existing catalogue makes step 3 look impossible.",
              "text": "It usually is not. Identify only what you are about to change, and let the rest acquire "
                      "identifiers as it is touched. A catalogue of several hundred entries is a rendering "
                      "problem the document runtime already solves (`NFR-PRF-04`), not a reason to skip the step "
                      "that makes every later one work."}},
]
