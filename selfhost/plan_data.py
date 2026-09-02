# -*- coding: utf-8 -*-
"""The plan that builds Zero-to-Ship, claiming everything it specifies.

Two halves, exactly as the layout contract says (`FR-PLN-05`): the spine — which
milestones exist, in what order, and what each is done when — and one detail
file per milestone holding its phases, tasks and acceptance criteria.

The claim rule is what makes this file honest rather than decorative: every
requirement and every decision the functional and technical specifications state
is traced to by at least one task below. Adding a requirement without adding a
task fails the coverage gate, which is the point.
"""

MILESTONES = [
    {"id": "M1", "title": "The documents and the gate",
     "dependsOn": [], "detailed": True,
     "summary": "Every document in the chain, generated from stated facts, "
                "with the gate that settles the open questions before any of "
                "it is authored.",
     "exit": ["A document set is produced from a brief, and refuses to run "
              "without the document above it.",
              "No fork is left open when a document is authored.",
              "Generating twice from unchanged input produces identical "
              "bytes."]},

    {"id": "M2", "title": "Coverage",
     "dependsOn": ["M1"], "detailed": True,
     "summary": "What exists, who owns it and who claims it, read out of the "
                "documents on every run and stored nowhere.",
     "exit": ["The matrix is computed from the documents themselves.",
              "An unclaimed requirement fails and is named.",
              "A deliberate exclusion passes with its reason and is not "
              "counted."]},

    {"id": "M3", "title": "Running the plan",
     "dependsOn": ["M2"], "detailed": True,
     "summary": "Ordered work turned into finished work, proved by checks the "
                "runner watched and judged by somebody who did not build it.",
     "exit": ["A plan runs end to end with nobody asked anything.",
              "No unit passes on the say-so of whoever built it.",
              "An interrupted run resumes without repeating or skipping."]},

    {"id": "M4", "title": "Memory and growth",
     "dependsOn": ["M3"], "detailed": True,
     "summary": "What each round learned, carried into the next, and new scope "
                "added without disturbing anything already named.",
     "exit": ["A milestone cannot close without a retrospective.",
              "Every later brief carries every earlier lesson.",
              "New scope is added by addendum with no identifier moved."]},

    {"id": "M5", "title": "One feature at a time",
     "dependsOn": ["M4"], "detailed": True,
     "summary": "Each round of work in its own place with its own coverage, "
                "one open at a time, and a close that audits what it is "
                "leaving behind.",
     "exit": ["A feature holds its own specifications, plan and run state, and "
              "a project with no features is laid out exactly as before.",
              "Opening a second feature while one is open is refused, naming "
              "the open one.",
              "A close with no reason refuses over anything the audit finds, "
              "and a close with a reason records it."]},
]

PREREQUISITES = [
    {"id": "PRE-01", "owner": "human",
     "text": "A repository with version control."},
    {"id": "PRE-02", "owner": "human",
     "text": "A scripting runtime wherever the checks run."},
    {"id": "PRE-03", "owner": "human",
     "text": "A check command for the host project that fails loudly."},
]

from z2s import schema

GAUNTLET = ["python3 -m unittest discover -s tests",
            "python3 -m z2s.validate .zero/specs/*.html"]


def _task(identifier, title, summary, traces, red, green, refactor,
          criteria, **extra):
    made = {"id": identifier, "title": title, "summary": summary,
            "priority": "Must", "autonomy": "auto", "layer": "generator",
            "testLayers": ["unit"], "dependsOn": [],
            "tdd": {"red": red, "green": green, "refactor": refactor},
            "traces": traces,
            "criteria": [{"id": "%s-C%d" % (identifier, index + 1),
                          "kind": "auto", "text": text, "done": False}
                         for index, text in enumerate(criteria)]}
    made.update(extra)
    # A unit that names a verification layer writes tests, and its declared
    # write set has to say where: the orchestrator schedules concurrent units
    # from this list, so tests left out of it are two workers turned loose on
    # one test file. Derived from the module written, because this repository
    # has one convention and spelling it out thirty times is thirty chances to
    # spell it differently. A unit whose proof lives somewhere else says so
    # itself, and the derivation then leaves it alone.
    declared = list(made.get("writes") or ())
    if declared and not any(schema.names_a_test(one) for one in declared):
        made["writes"] = declared + sorted(
            {"tests/test_%s" % one.split("/")[-1]
             for one in declared if one.startswith("z2s/") and one.endswith(".py")})
    return made


DETAILS = {

    "M1": [
        {"id": "M1-P1", "title": "The document chain", "dependsOn": [],
         "summary": "Each generator, and the shared rules all of them keep.",
         "completion": ["Every document authors from a brief and refuses "
                        "without the one above it."],
         "tasks": [
             _task("M1-P1-T1", "The shared chain rules",
                   "Refusal, envelope, identifiers, gaps, register and "
                   "writing, in one place every generator uses.",
                   {"fr": ["FR-DOC-01"], "nfr": ["NFR-ARC-01"]},
                   "A test asserts a generator refuses without the document "
                   "above it and writes nothing; it fails initially.",
                   "Implement the shared refusal and the envelope.",
                   "Move each rule out of the generators that grew it.",
                   ["A generator refuses without the document above it.",
                    "A refused run leaves the project unchanged."],
                   # Proved through the generators that use it: the red step
                   # above is a generator refusing, so that is where its test
                   # is written. There is no tests/test_chain.py to derive.
                   layer="foundation",
                   writes=["z2s/chain.py", "tests/test_fsd.py"]),
             _task("M1-P1-T2", "The document is its own source",
                   "Each rendered document embeds the specification it was "
                   "rendered from, and regenerates from it.",
                   {"fr": ["FR-DOC-02"], "nfr": ["NFR-GEN-01"],
                    "adr": ["ADR-01"]},
                   "A test regenerates a document from itself and asserts the "
                   "bytes are identical; it fails initially.",
                   "Embed the specification and read it back.",
                   "Share one serialiser between authoring and regeneration.",
                   ["A document regenerates from itself.",
                    "Two generations produce identical bytes."],
                   layer="generator", writes=["z2s/document.py", "z2s/writer.py"]),
             _task("M1-P1-T3", "Silence is recorded, never filled",
                   "Where the brief says nothing, the document says so instead "
                   "of supplying a value.",
                   {"fr": ["FR-DOC-03"]},
                   "A test authors from a brief missing one fact and asserts "
                   "the document records the silence; it fails initially.",
                   "Record every gap as a question.",
                   "Merge gaps into the section they belong beside.",
                   ["A silent brief produces a recorded question.",
                    "No value is invented for a missing fact."],
                   layer="generator", writes=["z2s/fsd.py", "z2s/prd.py"]),
             _task("M1-P1-T4", "Nothing reads the clock",
                   "No part of generation depends on the time of day or on "
                   "randomness.",
                   {"nfr": ["NFR-GEN-02"]},
                   "A test scans every module for a clock or a random source; "
                   "it fails while one is present.",
                   "Take every date from the caller.",
                   "Keep the guard as a test rather than as a convention.",
                   ["No module reads the clock.",
                    "Every date in a document came from its brief."],
                   layer="foundation", writes=["tests/test_writer.py"]),
             _task("M1-P1-T5", "The narrative briefing",
                   "One plain-language reading of the set, derived from it.",
                   {"fr": ["FR-DOC-04"]},
                   "A test asserts the briefing changes when the specification "
                   "changes; it fails initially.",
                   "Derive the briefing from the documents.",
                   "Layer it from plain language to technical depth.",
                   ["The briefing changes when the specification changes.",
                    "The briefing states no fact of its own."],
                   priority="Should", layer="generator",
                   writes=["z2s/briefing.py"])]},

        {"id": "M1-P2", "title": "The decision gate", "dependsOn": ["M1-P1"],
         "summary": "Every fork settled once, before authoring, and recorded "
                    "where every later step reads it.",
         "completion": ["No document is authored while a fork is open."],
         "tasks": [
             _task("M1-P2-T1", "Nothing is authored past an open question",
                   "The gate refuses to let a generator author while a fork is "
                   "unanswered.",
                   {"fr": ["FR-GAT-01"]},
                   "A test authors with one fork open and asserts a refusal "
                   "naming it; it fails initially.",
                   "Refuse until every fork is settled.",
                   "Share the refusal with every generator.",
                   ["An open fork refuses authoring.",
                    "The refusal names the fork."],
                   layer="foundation", writes=["z2s/gate.py"]),
             _task("M1-P2-T2", "Settled decisions are recorded once",
                   "Each settled fork is written down with its choice and its "
                   "reason, in the one place later steps read.",
                   {"fr": ["FR-GAT-02"], "nfr": ["NFR-ARC-02"]},
                   "A test settles a fork and asserts a later brief carries it; "
                   "it fails initially.",
                   "Record the decisions in the run ledger.",
                   "Read them back from the ledger rather than re-authoring.",
                   ["A settled fork appears in the ledger.",
                    "A later brief carries the settled choice."],
                   layer="foundation", writes=["z2s/gate.py"]),
             _task("M1-P2-T3", "A sufficient brief is not interviewed",
                   "A fork whose fact the brief already states counts as "
                   "settled.",
                   {"fr": ["FR-GAT-03"], "adr": ["ADR-02"]},
                   "A test opens the gate over a complete brief and asserts no "
                   "question is asked; it fails initially.",
                   "Treat a stated fact as an answer.",
                   "Derive the forks from the brief in one place.",
                   ["A complete brief raises no question.",
                    "A partial brief raises only the forks it left open."],
                   priority="Should", layer="foundation",
                   writes=["z2s/gate.py"])]}],

    "M2": [
        {"id": "M2-P1", "title": "The coverage engine", "dependsOn": [],
         "summary": "The matrix, computed from the documents on every run.",
         "completion": ["Unclaimed scope fails and is named."],
         "tasks": [
             _task("M2-P1-T1", "Coverage is read from the documents",
                   "What exists, who owns it and who claims it, all read out of "
                   "the rendered documents.",
                   {"fr": ["FR-TRC-01"], "adr": ["ADR-03"]},
                   "A test computes the matrix from documents alone and asserts "
                   "nothing else was consulted; it fails initially.",
                   "Read the embedded specifications and resolve ownership.",
                   "Store nothing the run computed.",
                   ["The matrix is computed from the documents.",
                    "Nothing the run computed is written down."],
                   layer="validator", writes=["z2s/trace.py"]),
             _task("M2-P1-T2", "An unclaimed requirement stops the build",
                   "A requirement or decision no unit of work claims fails the "
                   "check, by name.",
                   {"fr": ["FR-TRC-02"], "nfr": ["NFR-VAL-01"]},
                   "A test leaves one requirement unclaimed and asserts a "
                   "failure naming it; it fails initially.",
                   "Fail on any uncovered identifier.",
                   "Report which identifiers are newly unclaimed.",
                   ["An unclaimed requirement fails the check.",
                    "The failure names the identifier."],
                   layer="validator", writes=["z2s/trace.py"]),
             _task("M2-P1-T3", "An exclusion carries its argument",
                   "A deliberate exclusion stays in the document with its "
                   "reason, and is not counted as scope.",
                   {"fr": ["FR-TRC-03"]},
                   "A test marks a requirement as deliberately not built and "
                   "asserts it is outside the universe; it fails initially.",
                   "Split the universe on the exclusion band.",
                   "Render an exclusion distinctly from live scope.",
                   ["An exclusion is outside the coverage universe.",
                    "An exclusion with no reason fails the check."],
                   layer="validator", writes=["z2s/fsd.py"]),
             _task("M2-P1-T4", "A skipped check says so",
                   "A check that could not run is reported as skipped and never "
                   "counted as passed.",
                   {"nfr": ["NFR-VAL-02"]},
                   "A test runs the set with the browser absent and asserts the "
                   "view check reads as skipped; it fails initially.",
                   "Report skipped as a third outcome.",
                   "Count gates and findings separately.",
                   ["A skipped check is reported as skipped.",
                    "A skipped check is not counted as passed."],
                   layer="ops", testLayers=["unit", "CI"],
                   writes=["z2s/pipeline.py"])]}],

    "M3": [
        {"id": "M3-P1", "title": "The runner", "dependsOn": [],
         "summary": "Ready set, dispatch, proof and judgement.",
         "completion": ["A plan runs end to end with nobody asked anything."],
         "tasks": [
             _task("M3-P1-T1", "Work is dispatched in dependency order",
                   "Only units whose dependencies have passed are offered, and "
                   "one stuck unit never idles the run.",
                   {"fr": ["FR-RUN-01"], "adr": ["ADR-04"]},
                   "A test holds one dependency back and asserts the dependent "
                   "unit is not offered; it fails initially.",
                   "Compute the ready set on every iteration.",
                   "State why each held unit is held.",
                   ["A unit whose dependency has not passed is not offered.",
                    "A stuck unit does not stop the rest of the run."],
                   layer="orchestration", testLayers=["unit", "e2e"],
                   writes=["z2s/execute.py"]),
             _task("M3-P1-T2", "Nothing passes on its author's say-so",
                   "The checks are run by the runner, and a second worker "
                   "inspects the result unaware of how it was made.",
                   {"fr": ["FR-RUN-02"], "adr": ["ADR-05"]},
                   "A test has a builder claim a pass it cannot show and "
                   "asserts the unit does not pass; it fails initially.",
                   "Run the checks here and judge with a second worker.",
                   "Give the judge a brief that cannot carry the builder's "
                   "account.",
                   ["A claim with no command behind it does not pass.",
                    "No unit passes without being judged."],
                   layer="orchestration", testLayers=["unit", "e2e"],
                   writes=["z2s/execute.py"]),
             _task("M3-P1-T3", "A run decides rather than asking",
                   "Nobody is asked anything mid-run, and every decision the "
                   "run took instead is written down.",
                   {"fr": ["FR-RUN-03"], "nfr": ["NFR-SEC-01", "NFR-SEC-02"]},
                   "A test drives a whole run and asserts nothing was asked and "
                   "every decision was recorded; it fails initially.",
                   "Record decisions in the ledger and never prompt.",
                   "Refuse a destructive command before it runs.",
                   ["A run asks nothing.",
                    "Every decision taken without asking is recorded.",
                    "A refused command is reported with the rule that "
                    "refused it."],
                   layer="orchestration", testLayers=["unit", "e2e"],
                   writes=["z2s/execute.py", "z2s/safety.py"]),
             _task("M3-P1-T4", "An interrupted run resumes",
                   "A run picks up where it stopped, repeating nothing and "
                   "skipping nothing.",
                   {"fr": ["FR-RUN-04"]},
                   "A test kills a run mid-flight, restarts it and asserts no "
                   "unit is repeated or skipped; it fails initially.",
                   "Write the ledger before the work it describes.",
                   "Believe the plan where the two disagree, and say so.",
                   ["A restarted run repeats no finished unit.",
                    "A disagreement between plan and ledger is recorded."],
                   priority="Should", layer="orchestration",
                   writes=["z2s/execute.py"])]}],

    "M4": [
        {"id": "M4-P1", "title": "Memory", "dependsOn": [],
         "summary": "What each milestone learned, and who has to read it.",
         "completion": ["A milestone cannot close without a retrospective."],
         "tasks": [
             _task("M4-P1-T1", "A milestone closes by writing what it learned",
                   "Closing refuses without a retrospective, and the "
                   "retrospective accounts for every decision the run took "
                   "without asking.",
                   {"fr": ["FR-MEM-01"], "adr": ["ADR-06"]},
                   "A test closes a milestone with no lessons written and "
                   "asserts a refusal; it fails initially.",
                   "Require the retrospective at the close.",
                   "Seed it from what the run already recorded.",
                   ["A milestone with no retrospective cannot close.",
                    "Recorded decisions appear in the retrospective."],
                   layer="orchestration", testLayers=["unit", "e2e"],
                   writes=["z2s/learn.py"]),
             _task("M4-P1-T2", "Every later brief has read every earlier lesson",
                   "Each brief carries every earlier retrospective and the "
                   "summary of what they agree on.",
                   {"fr": ["FR-MEM-02"]},
                   "A test builds a later brief and asserts it names every "
                   "earlier lesson; it fails initially.",
                   "Assemble both into the brief.",
                   "Distil the summary from repeated themes.",
                   ["A later brief names every earlier retrospective.",
                    "The distilled summary is in the brief."],
                   layer="orchestration", writes=["z2s/execute.py"])]},

        {"id": "M4-P2", "title": "Growth", "dependsOn": ["M4-P1"],
         "summary": "Adding scope without moving anything already named.",
         "completion": ["An addendum disturbs no existing identifier."],
         "tasks": [
             _task("M4-P2-T1", "New scope arrives by addendum",
                   "New scope is published as its own document under its own "
                   "prefix, and the original is not opened.",
                   {"fr": ["FR-MEM-03"]},
                   "A test adds an addendum and asserts the original file is "
                   "unchanged; it fails initially.",
                   "Author the addendum into its own file.",
                   "Reuse the same generators, differing only in prefix.",
                   ["The original file is not written to.",
                    "Every original identifier still resolves.",
                    "The addendum prefix routes to the addendum."],
                   layer="generator", testLayers=["unit", "e2e"],
                   writes=["z2s/chain.py"])]}],

    "M5": [
        {"id": "M5-P1", "title": "The seam", "dependsOn": [],
         "summary": "Where a feature's own specifications, plan and run state "
                    "live, and which document stays the project's.",
         "completion": ["A project with no features is laid out exactly as it "
                        "was before."],
         "tasks": [
             _task("M5-P1-T1", "A feature keeps its own set",
                   "Resolution takes the open feature into account for the "
                   "specifications, the plan and the run state, and leaves the "
                   "shared document shared.",
                   {"fr": ["FR-FEA-01"], "nfr": ["NFR-GEN-03"],
                    "adr": ["ADR-07"], "us": ["US-FEA-01"]},
                   "A test resolves both paths with a feature open and asserts "
                   "the shared one did not move; it fails initially.",
                   "Resolve the three per-feature places against the open "
                   "feature, and derive which one that is from the numbering.",
                   "Keep the derivation in one place, so nothing else has to "
                   "know how a feature is numbered.",
                   ["A project with no features resolves every path exactly as "
                    "before.",
                    "The open feature is the highest-numbered one, and nothing "
                    "records it.",
                    "The shared document resolves to the project whichever "
                    "feature is open.",
                    "A set written under the earlier name for its first "
                    "document is still read, and nothing is renamed."],
                   layer="foundation",
                   writes=["z2s/paths.py", "z2s/chain.py",
                           "tests/test_paths.py"])]},

        {"id": "M5-P2", "title": "Open and close", "dependsOn": ["M5-P1"],
         "summary": "Opening one feature at a time, and closing it against an "
                    "audit.",
         "completion": ["A second opening is refused, and a close either comes "
                        "up clean or writes down what it left."],
         "tasks": [
             _task("M5-P2-T1", "Only one feature is open at a time",
                   "Opening a second while one is open is refused by name, and "
                   "small work joins the open one as an addendum.",
                   {"fr": ["FR-FEA-02"], "us": ["US-FEA-02"]},
                   "A test opens a second feature over an open one and asserts "
                   "a refusal naming the open one; it fails initially.",
                   "Refuse the second opening, and say which feature is in the "
                   "way.",
                   "Read the open feature through the same derivation the seam "
                   "already uses.",
                   ["A second opening is refused.",
                    "The refusal names the feature already open.",
                    "Nothing is written by a refused opening."],
                   writes=["z2s/feature.py"]),
             _task("M5-P2-T2", "Closing a feature is audited",
                   "The four audit questions are asked before a close; a close "
                   "with no reason refuses over what they find, and a close "
                   "with a reason records it.",
                   {"fr": ["FR-FEA-03"], "us": ["US-FEA-03"]},
                   "A test closes a feature holding one unfinished unit and "
                   "asserts a refusal listing it; it fails initially.",
                   "Audit the units, the retired identifiers, the open "
                   "questions and the unshipped work, then refuse or record.",
                   "Write the record into the feature's own first document, so "
                   "no second register has to be kept.",
                   ["A close with no reason refuses over anything the audit "
                    "finds, and lists every one of them.",
                    "A close with a reason records the findings as what was "
                    "left behind.",
                    "The record is in the feature's own first document.",
                    "Authoring or building in a closed feature is refused."],
                   writes=["z2s/feature.py"])]}],
}
