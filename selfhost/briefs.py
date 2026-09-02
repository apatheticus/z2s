# -*- coding: utf-8 -*-
"""Zero-to-Ship, described in its own briefs (M12-P3-T3).

The method claims that a specification set can be generated from a brief and
kept honest by its own gates. The only way to believe that is to watch it happen
to something real, and the most demanding thing available is the method itself:
a defect in a generator shows up in the method's own documents before it shows
up in anybody else's.

So this file is data, not code. It is the brief for each document in the chain,
plus the plan that claims every requirement and decision those documents state.
`selfhost/build.py` feeds them to the real generators and runs the real gates.

Two things it deliberately is NOT:

* **Not a copy of `docs/`.** The published document set under `docs/` is built
  by a separate, older generator and is the project's public face. It is left
  alone (a standing decision, 2026-08-14). This set is smaller, freshly written,
  and complete in its own right — one maintained set is worth more than two that
  drift.
* **Not exhaustive.** It states what the method IS, at a size a person will
  actually read and keep true. The published set is the long form.

Every date in here is written down, never taken from a clock (NFR-GEN-01).
"""

DATE = "2026-08-15"
OWNER = "Zerø Effort"

#: Where every document in this set says it came from. One conversation and one
#: repository — which is the truth, and a register that named more would be the
#: first false line in the set.
SOURCES = [
    {"kind": "narrative", "name": "The method's own design notes",
     "origin": "Written down as the toolchain was built, 2026-08-13 to "
               "2026-08-15.",
     "contributed": "Everything the method claims to do, and why each part of "
                    "it exists."},
    {"kind": "document", "name": "The published document set",
     "origin": "The rendered documents this project publishes.",
     "contributed": "The long form of every requirement summarised here."},
]


# ---------------------------------------------------------------------- intent

def intent():
    return {
        "title": "Zero-to-Ship — Intent",
        "owner": OWNER, "date": DATE,
        "summary": "A build method in which the specification is the input to "
                   "the build rather than a description of it.",
        "problem": [
            "A specification and the thing it describes start out agreeing and "
            "then stop. Nobody decides to let them diverge; it happens one "
            "unrecorded change at a time, and by the time anybody notices, the "
            "written record is something people have learned to ignore.",
            "The usual answer is discipline — review the document, update it "
            "after every change. Discipline is exactly the thing that runs out "
            "under deadline, so the answer has to be structural instead."],
        "statement": [
            "The written specification is what the build reads. Work is derived "
            "from it, every piece of work names the requirement it satisfies, "
            "and a requirement nothing claims stops the build. Divergence "
            "becomes a failed check rather than a discovery made months later."],
        "principles": [
            {"title": "Say it once",
             "body": "Every fact has one home. A fact stated twice is a fact "
                     "that will eventually be two different facts."},
            {"title": "Refuse rather than guess",
             "body": "Where the input is silent, the output says so. Inventing "
                     "the missing half is the failure this exists to prevent."},
            {"title": "Check the thing, not the account of it",
             "body": "A check that reads a report of the work has checked the "
                     "report. Evidence is what a tool watched happen."},
            {"title": "Permanent names",
             "body": "An identifier means one thing for the life of the "
                     "project. Growth is by addition; nothing is renumbered."}],
        "stakeholders": [
            {"name": "The owner", "kind": "decides",
             "need": "To settle the open questions once and see them applied "
                     "everywhere, rather than being asked again mid-build."},
            {"name": "The builder", "kind": "builds",
             "need": "A brief that says what to build, what proves it, and what "
                     "has already been decided."},
            {"name": "The reviewer", "kind": "reviews",
             "need": "To see which requirement each change serves, and what is "
                     "still unclaimed."},
            {"name": "The newcomer", "kind": "reads",
             "need": "One narrative reading of the whole set, in plain words."}],
        "personas": [
            {"title": "The owner who has been burned",
             "body": "Has watched a written specification go stale twice, and "
                     "will not maintain a third by hand."},
            {"title": "The builder working unattended",
             "body": "Picks up a unit of work with nobody to ask, and needs "
                     "everything already settled in front of them."}],
        "capabilities": [
            {"title": "Generate every document from a brief",
             "body": "Each document in the chain is produced from stated facts, "
                     "refuses to run without the document above it, and records "
                     "what its brief left out."},
            {"title": "Settle the open questions before authoring",
             "body": "Every fork is put to the owner once, before a word is "
                     "written, and the answers are kept where every later step "
                     "reads them."},
            {"title": "Compute coverage from the documents themselves",
             "body": "What exists, who owns it and who claims it are read out "
                     "of the documents, so no list has to be maintained."},
            {"title": "Run the plan",
             "body": "Work is dispatched in dependency order, proved by checks "
                     "the runner watched, and judged by somebody who did not "
                     "build it."},
            {"title": "Remember what each round taught",
             "body": "A milestone closes by writing down what it learned, and "
                     "every later brief has read all of them."}],
        "scenarios": [
            {"title": "A requirement arrives with nothing to build it",
             "body": "Somebody adds a requirement and forgets the work. The "
                     "next check names it and stops.",
             "traces": {"cap": ["VC-03"]}},
            {"title": "A build finishes with nobody at the desk",
             "body": "Every unit of work is built, proved and judged overnight, "
                     "and the morning report says exactly what was decided "
                     "without asking.",
             "traces": {"cap": ["VC-04"]}}],
        "constraints": [
            "No third-party runtime dependency: the standard library and what a "
            "browser already provides.",
            "Documents open from a file, with no server and no build step.",
            "Generation is repeatable: unchanged input produces unchanged "
            "output, byte for byte."],
        "sources": SOURCES,
    }


# --------------------------------------------------------------------- context

def context():
    return {
        "title": "Zero-to-Ship — Context and shared language",
        "owner": OWNER, "date": DATE,
        "summary": "The words this method uses, each with one meaning.",
        "overview": [
            "Every document below this one uses these words and no synonyms. A "
            "word with two meanings is where two people agree in a meeting and "
            "build different things."],
        "contexts": [
            {"name": "Authoring", "body": "Turning stated facts into a document.",
             "feeds": ["Planning"]},
            {"name": "Planning",
             "body": "Turning the documents into ordered units of work.",
             "feeds": ["Execution"]},
            {"name": "Execution",
             "body": "Building each unit of work and proving it."}],
        "terms": [
            {"term": "brief", "context": "Authoring",
             "definition": "The stated facts a document is generated from. "
                           "Everything a document says comes from its brief or "
                           "from the document above it.",
             "source": "the intent"},
            {"term": "document set", "context": "Authoring",
             "definition": "The chain of documents, from the intent down to the "
                           "plan, each refusing to run without the one above.",
             "source": "VC-01"},
            {"term": "gate", "context": "Authoring",
             "definition": "The step that puts every open question to the owner "
                           "before anything is authored.",
             "source": "VC-02", "synonyms": ["interview"]},
            {"term": "locked decision", "context": "Authoring",
             "definition": "An answer the gate settled, recorded once and "
                           "carried into every later step unchanged.",
             "source": "VC-02"},
            {"term": "unit of work", "context": "Planning",
             "definition": "The smallest thing the plan schedules: one task, "
                           "with its own checks and its own acceptance.",
             "source": "the intent", "synonyms": ["ticket"]},
            {"term": "coverage universe", "context": "Planning",
             "definition": "Every requirement and decision that has to be "
                           "claimed by a unit of work.",
             "source": "VC-03"},
            {"term": "gauntlet", "context": "Execution",
             "definition": "The checks a unit of work must pass, run by the "
                           "runner itself so the result is watched rather than "
                           "reported.",
             "source": "VC-04"},
            {"term": "judge", "context": "Execution",
             "definition": "A second worker that inspects finished work having "
                           "been shown no account of how it was made.",
             "source": "VC-04"},
            {"term": "retrospective", "context": "Execution",
             "definition": "What a milestone writes down as it closes, and what "
                           "every later brief has to have read.",
             "source": "VC-05"},
            {"term": "addendum", "context": "Authoring",
             "definition": "New scope published as its own document under its "
                           "own prefix, leaving every existing name untouched.",
             "source": "the intent"}],
        "sources": SOURCES,
    }


# ------------------------------------------------------------------------- prd

def prd():
    return {
        "title": "Zero-to-Ship — Product requirements",
        "owner": OWNER, "date": DATE,
        "summary": "Which goals this method is trying to meet, and how anyone "
                   "would know whether it did.",
        "purpose": [
            "The intent says what the world looks like when this works. This "
            "document says which goals the first release is judged against, and "
            "what would count as meeting each one."],
        "goals": [
            {"text": "A complete document set can be produced from stated facts "
                     "alone, with nothing invented.",
             "traces": {"cap": ["VC-01"]}},
            {"text": "Every open question is settled once, before authoring, and "
                     "never asked again.",
             "traces": {"cap": ["VC-02"]}},
            {"text": "Nothing in the specification can go unclaimed by the work "
                     "without the build failing.",
             "traces": {"cap": ["VC-03"]}},
            {"text": "A plan can be worked end to end with nobody asked anything "
                     "mid-run.",
             "traces": {"cap": ["VC-04"]}},
            {"text": "What one round of work learns is carried into the next "
                     "without anybody remembering to carry it.",
             "traces": {"cap": ["VC-05"]}}],
        "nonGoals": [
            {"text": "Hosting the documents, or editing them together in a "
                     "browser."},
            {"text": "Keeping an external issue tracker in step with the plan."},
            {"text": "Choosing what a project should build. The method carries "
                     "decisions; it does not make them."}],
        "journeys": [
            {"title": "From an idea to a plan", "persona": "The owner",
             "steps": ["States what the thing is for, in a brief.",
                       "Answers every fork the gate raises, once.",
                       "Receives a document set and a plan whose every unit of "
                       "work names what it satisfies."],
             "traces": {"cap": ["VC-01", "VC-02"]}},
            {"title": "From a plan to finished work", "persona": "The builder",
             "steps": ["Takes the next unit of work with its brief.",
                       "Writes the failing check, then the smallest change that "
                       "passes it.",
                       "Has the result proved and judged, and the status "
                       "written back into the plan."],
             "traces": {"cap": ["VC-04"]}}],
        "measures": [
            {"name": "Nothing invented", "kind": "count",
             "target": "Zero facts in any document that the brief or the "
                       "document above it does not state.",
             "traces": {"goal": ["G-01"]}},
            {"name": "Questions asked twice", "kind": "count",
             "target": "Zero: a settled fork is never re-opened by a later step.",
             "traces": {"goal": ["G-02"]}},
            {"name": "Unclaimed scope", "kind": "count",
             "target": "Zero requirements or decisions claimed by no unit of "
                       "work, on any passing build.",
             "traces": {"goal": ["G-03"]}},
            {"name": "Questions asked mid-run", "kind": "count",
             "target": "Zero: a run either decides and records, or stops.",
             "traces": {"goal": ["G-04"]}},
            {"name": "Retrospectives unread", "kind": "count",
             "target": "Zero: every brief carries every earlier one.",
             "traces": {"goal": ["G-05"]}}],
        "dependencies": [
            "A repository with version control.",
            "A scripting runtime available wherever the checks run.",
            "A check command for the host project that fails loudly."],
        "assumptions": [
            "The owner is available to answer the gate once, and not "
            "continuously afterwards."],
        "risks": [
            {"risk": "The gate asks so much that nobody finishes it.",
             "mitigation": "A brief that already states a fact answers that "
                           "fork; only real silence is asked about.",
             "traces": {"goal": ["G-02"]}},
            {"risk": "Coverage becomes a list somebody maintains by hand.",
             "mitigation": "It is computed from the documents on every run and "
                           "stored nowhere.",
             "traces": {"goal": ["G-03"]}}],
        "sources": SOURCES,
    }


# ------------------------------------------------------------------------- fsd

def fsd():
    return {
        "title": "Zero-to-Ship — Functional specification",
        "owner": OWNER, "date": DATE,
        "summary": "What the method must do, as requirements that can be tested "
                   "one at a time.",
        "purpose": [
            "Every requirement below is individually testable, belongs to one "
            "area, and carries the band that decides whether a release can ship "
            "without it. Nothing here says how any of it is built."],
        "areas": [
            {"key": "FR-DOC", "name": "The documents",
             "description": "Generating each document in the chain, and what "
                            "each one owes its reader."},
            {"key": "FR-GAT", "name": "The decision gate",
             "description": "Settling every open question before a word is "
                            "authored."},
            {"key": "FR-TRC", "name": "Coverage",
             "description": "What exists, who owns it, and who claims it."},
            {"key": "FR-RUN", "name": "Running the plan",
             "description": "Turning ordered work into finished work."},
            {"key": "FR-MEM", "name": "Memory and growth",
             "description": "Carrying what was learned, and adding scope "
                            "without disturbing what is there."}],
        "requirements": [
            {"area": "FR-DOC", "priority": "Must",
             "title": "Every document is generated",
             "text": "The system shall produce each document in the chain from "
                     "stated facts, and shall refuse to run without the "
                     "document above it, naming what is missing.",
             "traces": {"goal": ["G-01"]}},
            {"area": "FR-DOC", "priority": "Must",
             "title": "A document carries its own specification",
             "text": "The system shall embed each document's specification "
                     "inside the document, so that the document is the source "
                     "it is regenerated from.",
             "notes": "This is what makes an update an edit to the "
                      "specification rather than to the rendered page.",
             "traces": {"goal": ["G-01"]}},
            {"area": "FR-DOC", "priority": "Must",
             "title": "Silence is recorded, never filled",
             "text": "Where the brief says nothing, the system shall record the "
                     "silence as an open question and shall not supply a value "
                     "in its place.",
             "traces": {"goal": ["G-01"]}},
            {"area": "FR-DOC", "priority": "Should",
             "title": "One narrative reading of the set",
             "text": "The system shall produce a plain-language briefing "
                     "derived from the document set, for a reader who will not "
                     "read the specifications.",
             "traces": {"goal": ["G-01"]}},
            {"area": "FR-DOC", "priority": "Won't",
             "title": "Hosted, multi-person editing",
             "text": "The system will not host the documents or provide "
                     "simultaneous editing.",
             "notes": "Documents are files in a repository; working together on "
                      "them is what version control is already for. Building a "
                      "second answer to that would be the largest part of the "
                      "method and the least of its value.",
             "traces": {"goal": ["G-01"]}},

            {"area": "FR-GAT", "priority": "Must",
             "title": "Nothing is authored past an open question",
             "text": "The system shall put every fork to the owner and shall "
                     "refuse to author any document while one is unanswered.",
             "traces": {"goal": ["G-02"]}},
            {"area": "FR-GAT", "priority": "Must",
             "title": "Settled decisions are recorded once",
             "text": "The system shall record each settled fork with the choice "
                     "and the reason, in one place that every later step reads.",
             "traces": {"goal": ["G-02"]}},
            {"area": "FR-GAT", "priority": "Should",
             "title": "A sufficient brief is not interviewed",
             "text": "Where the brief already states the fact a fork asks "
                     "about, the system shall treat that fork as settled.",
             "traces": {"goal": ["G-02"]}},

            {"area": "FR-TRC", "priority": "Must",
             "title": "Coverage is read from the documents",
             "text": "The system shall compute what exists and what claims it "
                     "from the documents themselves, and shall keep no "
                     "separate list.",
             "traces": {"goal": ["G-03"]}},
            {"area": "FR-TRC", "priority": "Must",
             "title": "An unclaimed requirement stops the build",
             "text": "The system shall fail, and shall name the identifier, "
                     "when a requirement or decision is claimed by no unit of "
                     "work.",
             "traces": {"goal": ["G-03"]}},
            {"area": "FR-TRC", "priority": "Must",
             "title": "An exclusion carries its argument",
             "text": "The system shall keep a deliberate exclusion in the "
                     "document with the reason it was excluded, and shall not "
                     "count it as scope to be claimed.",
             "traces": {"goal": ["G-03"]}},

            {"area": "FR-RUN", "priority": "Must",
             "title": "Work is dispatched in dependency order",
             "text": "The system shall offer for work only those units whose "
                     "dependencies have passed, and shall never idle a run "
                     "because one unit is stuck.",
             "traces": {"goal": ["G-04"]}},
            {"area": "FR-RUN", "priority": "Must",
             "title": "Nothing passes on its author's say-so",
             "text": "The system shall run each unit's checks itself, and shall "
                     "have the result inspected by a second party that is shown "
                     "no account of how the work was made.",
             "traces": {"goal": ["G-04"]}},
            {"area": "FR-RUN", "priority": "Must",
             "title": "A run decides rather than asking",
             "text": "The system shall ask nobody anything while a run is in "
                     "progress, and shall record every decision it took "
                     "instead.",
             "traces": {"goal": ["G-04"]}},
            {"area": "FR-RUN", "priority": "Should",
             "title": "An interrupted run resumes",
             "text": "The system shall resume an interrupted run without "
                     "repeating a finished unit or skipping an unfinished one.",
             "traces": {"goal": ["G-04"]}},
            {"area": "FR-RUN", "priority": "Won't",
             "title": "Keeping an external tracker in step",
             "text": "The system will not synchronise its plan with an outside "
                     "issue tracker.",
             "notes": "Two systems holding the same status is the divergence "
                      "this method exists to remove, reintroduced at a "
                      "different layer. The plan is the record.",
             "traces": {"goal": ["G-03"]}},

            {"area": "FR-MEM", "priority": "Must",
             "title": "A milestone closes by writing what it learned",
             "text": "The system shall refuse to close a milestone without a "
                     "retrospective, and that retrospective shall account for "
                     "every decision the run took without asking.",
             "traces": {"goal": ["G-05"]}},
            {"area": "FR-MEM", "priority": "Must",
             "title": "Every later brief has read every earlier lesson",
             "text": "The system shall carry every earlier retrospective, and a "
                     "summary of what they agree on, into every brief it "
                     "afterwards writes.",
             "traces": {"goal": ["G-05"]}},
            {"area": "FR-MEM", "priority": "Must",
             "title": "New scope arrives without disturbing what is there",
             "text": "The system shall add new scope as a document with its own "
                     "prefix, leaving every existing identifier and every "
                     "existing file untouched.",
             "traces": {"goal": ["G-03"]}}],
        "assumptions": [
            "A reader has a browser; nothing else has to be installed to read a "
            "document."],
        "sources": SOURCES,
    }


# --------------------------------------------------------------------- stories

def stories():
    return {
        "title": "Zero-to-Ship — Stories, use cases and acceptance",
        "owner": OWNER, "date": DATE,
        "summary": "What each requirement looks like from the outside, and what "
                   "would prove it.",
        "purpose": [
            "Every requirement the specification counts is covered below by at "
            "least one story or use case, and every scenario is named so a "
            "check can carry the name."],
        "acceptance": [
            "Nothing is written down that the input does not state.",
            "Running the same input twice produces the same bytes.",
            "A failure names the identifier it is about."],
        "areas": [
            {"key": "US-DOC", "name": "Producing the documents"},
            {"key": "US-GAT", "name": "Settling the questions"},
            {"key": "US-TRC", "name": "Keeping coverage honest"},
            {"key": "US-RUN", "name": "Working the plan"},
            {"key": "US-MEM", "name": "Remembering and growing"}],
        "stories": [
            {"area": "US-DOC", "priority": "Must", "role": "owner",
             "title": "Get a document set from what I already know",
             "narrative": "As an owner, I want each document produced from the "
                          "facts I have stated, so that I am not asked to write "
                          "the same thing twice.",
             "testLayers": ["unit", "e2e"],
             "traces": {"fr": ["FR-DOC-01", "FR-DOC-02", "FR-DOC-03"]},
             "scenarios": [
                 {"title": "The document above is missing",
                  "given": "no document above this one has been produced",
                  "when": "the generator is asked to author",
                  "then": "it names the missing document and writes nothing"},
                 {"title": "The brief is silent about something",
                  "given": "a brief that says nothing about one required fact",
                  "when": "the document is authored",
                  "then": "the silence appears as an open question and no value "
                          "is supplied for it"}]},
            {"area": "US-DOC", "priority": "Should", "role": "newcomer",
             "title": "Read one plain account of the whole thing",
             "narrative": "As a newcomer, I want one narrative reading of the "
                          "set, so that I can understand the work without "
                          "reading five specifications.",
             "testLayers": ["unit", "manual"],
             "traces": {"fr": ["FR-DOC-04"]},
             "scenarios": [
                 {"title": "A capability changes",
                  "given": "a briefing produced from the set",
                  "when": "a requirement is added and the briefing is produced "
                          "again",
                  "then": "the briefing says so"}]},
            {"area": "US-GAT", "priority": "Must", "role": "owner",
             "title": "Answer each question once",
             "narrative": "As an owner, I want every fork put to me before "
                          "authoring and never again, so that a build cannot "
                          "stop halfway to ask me something.",
             "testLayers": ["unit"],
             "traces": {"fr": ["FR-GAT-01", "FR-GAT-02", "FR-GAT-03"]},
             "scenarios": [
                 {"title": "A fork is left open",
                  "given": "one unanswered fork",
                  "when": "authoring is attempted",
                  "then": "it refuses and names the fork"},
                 {"title": "The brief already answers it",
                  "given": "a brief stating the fact a fork asks about",
                  "when": "the gate is opened",
                  "then": "that fork is not put to the owner"}]},
            {"area": "US-TRC", "priority": "Must", "role": "reviewer",
             "title": "See what nothing is building",
             "narrative": "As a reviewer, I want a requirement no work claims "
                          "to fail the build, so that scope cannot go quiet.",
             "testLayers": ["unit", "CI"],
             "traces": {"fr": ["FR-TRC-01", "FR-TRC-02", "FR-TRC-03"]},
             "scenarios": [
                 {"title": "A requirement nothing claims",
                  "given": "a specification set and a plan that claims all but "
                           "one requirement",
                  "when": "the coverage check runs",
                  "then": "it fails and names that requirement"},
                 {"title": "A deliberate exclusion",
                  "given": "a requirement marked as deliberately not built, "
                           "with its reason",
                  "when": "the coverage check runs",
                  "then": "it passes, and the exclusion is still in the "
                          "document"}]},
            {"area": "US-RUN", "priority": "Must", "role": "builder",
             "title": "Work the plan without being asked anything",
             "narrative": "As a builder, I want each unit dispatched with "
                          "everything already settled and proved by checks the "
                          "runner watched, so that finishing does not depend on "
                          "anybody being awake.",
             "testLayers": ["unit", "e2e"],
             "traces": {"fr": ["FR-RUN-01", "FR-RUN-02", "FR-RUN-03"]},
             "verify": ["No unit reaches a passing status without a second "
                        "party having inspected it."],
             "scenarios": [
                 {"title": "A unit whose dependency has not passed",
                  "given": "a unit waiting on unfinished work",
                  "when": "the ready set is computed",
                  "then": "that unit is not offered, and the reason is stated"},
                 {"title": "A worker reports a pass it cannot show",
                  "given": "a report claiming a criterion is met and naming no "
                           "command",
                  "when": "the result is settled",
                  "then": "the unit does not pass"}]},
            {"area": "US-RUN", "priority": "Should", "role": "builder",
             "title": "Pick a run back up where it stopped",
             "narrative": "As a builder, I want an interrupted run to resume "
                          "exactly where it was, so that a lost machine costs "
                          "minutes rather than a milestone.",
             "testLayers": ["unit"],
             "traces": {"fr": ["FR-RUN-04"]},
             "scenarios": [
                 {"title": "A run stopped part-way",
                  "given": "a run killed while one unit was in flight",
                  "when": "it is started again",
                  "then": "no finished unit is repeated and no unfinished one is "
                          "skipped"}]},
            {"area": "US-MEM", "priority": "Must", "role": "owner",
             "title": "Have each round teach the next one",
             "narrative": "As an owner, I want a milestone to close by writing "
                          "down what it learned and every later brief to carry "
                          "it, so that the same mistake is not made twice.",
             "testLayers": ["unit", "e2e"],
             "traces": {"fr": ["FR-MEM-01", "FR-MEM-02"]},
             "scenarios": [
                 {"title": "A milestone with no retrospective",
                  "given": "a finished milestone and no lessons written down",
                  "when": "it is closed",
                  "then": "closing refuses and says what is missing"},
                 {"title": "A later brief",
                  "given": "two milestones that have already closed",
                  "when": "a brief for a later one is built",
                  "then": "it names both of the earlier lessons"}]},
            {"area": "US-MEM", "priority": "Must", "role": "owner",
             "title": "Add scope without renaming anything",
             "narrative": "As an owner, I want new scope published beside what "
                          "shipped rather than edited into it, so that every "
                          "name somebody has already used still means what it "
                          "meant.",
             "testLayers": ["unit", "e2e"],
             "traces": {"fr": ["FR-MEM-03"]},
             "scenarios": [
                 {"title": "An addendum is added",
                  "given": "a shipped specification and new scope",
                  "when": "the new scope is authored as an addendum",
                  "then": "every original identifier still resolves and the "
                          "original file is unchanged"}]}],
        "sources": SOURCES,
    }


# ------------------------------------------------------------------------- sdd

def sdd():
    return {
        "title": "Zero-to-Ship — Technical specification",
        "owner": OWNER, "date": DATE,
        "summary": "How the method is put together, and the decisions that "
                   "shaped it.",
        "principles": [
            {"name": "One home per rule",
             "desc": "A rule shared by several generators lives in the shared "
                     "module they all use, not copied into each."},
            {"name": "Refusal before writing",
             "desc": "Every check that can refuse a run happens before the "
                     "first file is written, so a refused run leaves the "
                     "project as it found it."},
            {"name": "Derived, never stored",
             "desc": "Progress, coverage and ordering are computed on every "
                     "run. A stored figure is right once."}],
        "stack": [
            {"layer": "Generators", "choice": "Python standard library",
             "role": "Turn briefs into document objects and render them."},
            {"layer": "Document runtime", "choice": "Plain JavaScript",
             "role": "Render the embedded specification in the reader's "
                     "browser, with no build step."},
            {"layer": "Checks", "choice": "Python standard library",
             "role": "Validate, compute coverage, and drive the rendered view."}],
        "components": [
            {"name": "The chain", "kind": "module",
             "responsibilities": "What every generator below the intent shares: "
                                 "refusal, envelope, identifiers, gaps, "
                                 "writing."},
            {"name": "The coverage engine", "kind": "module",
             "responsibilities": "Reads every document, resolves ownership, and "
                                 "computes the matrix."},
            {"name": "The runner", "kind": "module",
             "responsibilities": "Computes what is ready, dispatches it, proves "
                                 "it, has it judged, and records the result."}],
        "dataModel": [
            {"name": "Document", "points": [
                "An envelope of facts, a list of sections, and a schema "
                "version.",
                "Embedded in the rendered file, which is therefore its own "
                "source."]},
            {"name": "Run state", "points": [
                "What the run has finished and what it was about to do.",
                "Transient: the plan documents are the record."]}],
        "crosscutting": [
            {"name": "Determinism", "points": [
                "No clock and no random source anywhere in generation.",
                "Keys are ordered before they are written."]},
            {"name": "Safety", "points": [
                "Every command is checked against the refused list before it "
                "runs.",
                "Names that say they hold a credential are removed from a "
                "worker's environment."]}],
        "decisions": [
            {"title": "The document is its own source", "status": "Accepted",
             "context": "An update has to change one thing, not a rendered page "
                        "and a separate data file that can disagree.",
             "decision": "Each rendered document embeds the specification it "
                         "was rendered from, and regeneration reads it back.",
             "alternatives": ["Keep the data beside the document.",
                              "Keep the data in a database."],
             "consequences": ["A document can be regenerated with nothing else "
                              "present.",
                              "The rendered file is larger than it would "
                              "otherwise be."]},
            {"title": "Identifiers are permanent; growth is by addition",
             "status": "Accepted",
             "context": "Every trace, check name and commit message that used "
                        "an identifier still means it.",
             "decision": "Nothing is ever renumbered. New scope is published as "
                         "an addendum under its own prefix, and a withdrawn "
                         "identifier is retired in place.",
             "alternatives": ["Renumber on each release.",
                              "Reuse the numbers of withdrawn entries."],
             "consequences": ["Numbers have gaps, which is the visible cost of "
                              "the guarantee.",
                              "Ownership has to be resolved by prefix rather "
                              "than by file."]},
            {"title": "Coverage is computed, never maintained",
             "status": "Accepted",
             "context": "A maintained coverage list is accurate until the first "
                        "time somebody is in a hurry.",
             "decision": "Coverage is read out of the documents on every run "
                         "and stored nowhere.",
             "alternatives": ["A maintained matrix.",
                              "Coverage annotations in the work items only."],
             "consequences": ["The check is slower than reading a stored file.",
                              "There is nothing to forget to update."]},
            {"title": "A worker is a command", "status": "Accepted",
             "context": "The runner has to be testable without an agent, a "
                        "network or a paid provider.",
             "decision": "A worker is a command named in the project's "
                         "settings, given the path to its brief and the path "
                         "its report must go to.",
             "alternatives": ["Speak to one provider directly.",
                              "Require a particular agent runtime."],
             "consequences": ["Anything that can be run can be a worker.",
                              "The contract is a file format rather than an "
                              "interface."]},
            {"title": "A builder never grades its own work",
             "status": "Accepted",
             "context": "A builder asked whether it finished will say yes, and "
                        "an account of the work is not the work.",
             "decision": "The checks are run by the runner, and a second worker "
                         "inspects the result without being shown any account "
                         "of how it was made.",
             "alternatives": ["Trust the builder's own report.",
                              "Have a person review every unit."],
             "consequences": ["Every unit costs a second worker.",
                              "A unit that cannot be inspected does not pass."]},
            {"title": "Lessons are required reading", "status": "Accepted",
             "context": "Advice that is available but not carried is advice "
                        "nobody reads.",
             "decision": "A milestone cannot close without a retrospective, and "
                         "every later brief carries every earlier one.",
             "alternatives": ["Keep a wiki page.",
                              "Mention lessons in the closing report only."],
             "consequences": ["Briefs grow as a project goes on.",
                              "A theme that keeps recurring can be counted "
                              "rather than noticed."]}],
        "areas": [
            {"key": "NFR-ARC", "name": "Architecture",
             "description": "How the parts are arranged and what they may "
                            "depend on."},
            {"key": "NFR-GEN", "name": "Generation",
             "description": "What must be true of every generated artefact."},
            {"key": "NFR-VAL", "name": "Validation",
             "description": "What a check owes the person reading its output."},
            {"key": "NFR-SEC", "name": "Safety",
             "description": "What an unattended run may never do."}],
        "requirements": [
            {"area": "NFR-ARC", "priority": "Must",
             "title": "A generator brings only its own rules",
             "text": "Everything shared by the generators shall live in one "
                     "shared place, so a new generator is its own schema, its "
                     "own forks and its own rules and nothing else.",
             "traces": {"fr": ["FR-DOC-01"]}},
            {"area": "NFR-ARC", "priority": "Must",
             "title": "No third-party runtime dependency",
             "text": "The method shall run on the standard library and what a "
                     "browser already provides.",
             "traces": {"adr": ["ADR-01"]}},
            {"area": "NFR-GEN", "priority": "Must",
             "title": "Unchanged input regenerates unchanged output",
             "text": "Generating twice from unchanged input shall produce "
                     "identical bytes.",
             "traces": {"fr": ["FR-DOC-02"]}},
            {"area": "NFR-GEN", "priority": "Must",
             "title": "Nothing reads the clock or a random source",
             "text": "No part of generation shall depend on the time of day or "
                     "on randomness; every date is stated by the caller.",
             "traces": {"fr": ["FR-DOC-02"]}},
            {"area": "NFR-VAL", "priority": "Must",
             "title": "Every violation is reported in one pass",
             "text": "A check shall report every violation it finds in one run "
                     "rather than stopping at the first.",
             "traces": {"fr": ["FR-TRC-02"]}},
            {"area": "NFR-VAL", "priority": "Must",
             "title": "A skipped check is reported as skipped",
             "text": "A check that could not run shall be reported as skipped "
                     "and shall never be counted as passed.",
             "traces": {"fr": ["FR-TRC-01"]}},
            {"area": "NFR-SEC", "priority": "Must",
             "title": "No live credential in an unattended run",
             "text": "An unattended unit of work shall run with every "
                     "credential removed from its environment, and shall "
                     "receive only the substitute it names.",
             "traces": {"fr": ["FR-RUN-03"]}},
            {"area": "NFR-SEC", "priority": "Must",
             "title": "A destructive operation is refused",
             "text": "The system shall refuse any command that would discard "
                     "work irrecoverably, and shall report which rule refused "
                     "it.",
             "traces": {"fr": ["FR-RUN-03"]}}],
        "targets": [
            {"title": "Document weight",
             "target": "Under 2048 kilobytes for a rendered document.",
             "measured": "The size of the written file, measured by the "
                         "pipeline's budget gate on every run.",
             "traces": {"fr": ["FR-DOC-02"]}},
            {"title": "Generation time",
             "target": "Under ten seconds for a whole document set.",
             "measured": "Elapsed time around the generation step of the check "
                         "run.",
             "traces": {"fr": ["FR-DOC-01"]}}],
        "risks": [
            {"risk": "The embedded specification makes documents large.",
             "mitigation": "A weight target is stated and checked on every "
                           "run."},
            {"risk": "A shared rule changes behaviour for every generator at "
                     "once.",
             "mitigation": "The shared rules carry the heaviest tests in the "
                           "suite, and each generator asserts its own use of "
                           "them."}],
        "assumptions": [
            "The host project has a check command that fails loudly."],
        "sources": SOURCES,
    }


# ---------------------------------------------------------------------- briefing

def briefing():
    return {"title": "Zero-to-Ship — Briefing", "owner": OWNER, "date": DATE,
            "summary": "The method in plain words, derived from its own "
                       "document set."}
