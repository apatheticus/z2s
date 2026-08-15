# -*- coding: utf-8 -*-
"""Zero-to-Ship plan detail — M5 to M8."""

DETAIL = {

"M5": [
 {"id": "M5-P1", "title": "Story generator", "dependsOn": [],
  "summary": "Turn functional requirements into goal-level stories whose scenarios are precise enough to name "
             "automated tests after.",
  "completion": ["Every non-excluded functional requirement is covered by at least one story.",
                 "Scenario identifiers are unique and stable."],
  "tasks": [
   {"id": "M5-P1-T1", "title": "Story schema and generator", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Publish the story schema — narrative, role, priority, traces, verification layers and "
               "Given/When/Then scenarios — and the generator that derives stories from a functional "
               "specification.",
    "tdd": {"red": "A test generates stories from a fixture functional specification and asserts the output "
                   "validates and every story traces at least one functional requirement; it fails initially.",
            "green": "Implement the schema and the generator.",
            "refactor": "Reuse the shared catalogue renderer and trace helper."},
    "traces": {"fr": ["FR-DOC-01"], "nfr": ["NFR-ARC-01", "NFR-ARC-02"], "us": ["US-DOC-01"]},
    "criteria": [{"id": "M5-P1-T1-C1", "kind": "auto", "text": "The generated document validates.", "done": True},
                 {"id": "M5-P1-T1-C2", "kind": "auto", "text": "Every story traces at least one functional "
                                                               "requirement.", "done": True}]},
   {"id": "M5-P1-T2", "title": "Scenario identifiers name the tests", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "lint"], "dependsOn": ["M5-P1-T1"],
    "summary": "Each scenario carries a stable identifier derived from its story, and a check confirms automated "
               "tests written for a scenario carry that identifier in their name.",
    "tdd": {"red": "A test asserts scenario identifiers are unique and that a fixture test suite naming no "
                   "identifier is reported; both fail initially.",
            "green": "Derive scenario identifiers and add the naming check.",
            "refactor": "Report unmatched scenarios and unmatched tests as two distinct findings."},
    "traces": {"fr": ["FR-TRC-09", "FR-TRC-01"], "us": ["US-EXE-02"]},
    "criteria": [{"id": "M5-P1-T2-C1", "kind": "auto", "text": "Scenario identifiers are unique across the "
                                                               "document.", "done": True},
                 {"id": "M5-P1-T2-C2", "kind": "auto", "text": "A test not naming its scenario is reported.",
                  "done": True}]},
   {"id": "M5-P1-T3", "title": "Structural assertions for non-deterministic behaviour", "priority": "Must",
    "status": "passing", "autonomy": "auto", "layer": "generator", "testLayers": ["unit", "manual"], "dependsOn": ["M5-P1-T1"],
    "summary": "Where behaviour is non-deterministic, scenarios assert on structure, required fields and links — "
               "never on exact generated wording.",
    "tdd": {"red": "A test flags a scenario asserting on a literal generated sentence; it fails while no such "
                   "check exists.",
            "green": "Add the check and the authoring rule.",
            "refactor": "Record the rule in the global acceptance list so it applies once, not per story."},
    "traces": {"fr": ["FR-DOC-04"], "us": ["US-DOC-01"]},
    "criteria": [{"id": "M5-P1-T3-C1", "kind": "auto", "text": "A scenario asserting on generated wording is "
                                                               "flagged.", "done": True},
                 {"id": "M5-P1-T3-C2", "kind": "human-review", "text": "A reviewer confirms scenarios are testable "
                                                                       "as written.", "done": True}]}]},

 {"id": "M5-P2", "title": "Use cases and global acceptance", "dependsOn": ["M5-P1"],
  "summary": "Actor-centred flows for interactions that span several stories, plus the cross-cutting assertions "
             "that apply to every story rather than being repeated in each.",
  "completion": ["Use cases carry actor, trigger, preconditions, main flow, alternates, exceptions and "
                 "postcondition.",
                 "Global acceptance is stated once and referenced."],
  "tasks": [
   {"id": "M5-P2-T1", "title": "Use-case schema and renderer", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Publish the use-case shape and its renderer, for flows that cross several stories and cannot be "
               "expressed as one goal-level story.",
    "tdd": {"red": "A test asserts a use case missing its exception paths fails validation; it fails with no "
                   "schema.",
            "green": "Publish the schema and require every field.",
            "refactor": "Render use cases through the same card machinery as stories."},
    "traces": {"fr": ["FR-DOC-01"], "nfr": ["NFR-DAT-06"], "us": ["US-DOC-01"]},
    "criteria": [{"id": "M5-P2-T1-C1", "kind": "auto", "text": "A use case missing a required flow fails "
                                                               "validation.", "done": True}]},
   {"id": "M5-P2-T2", "title": "Global acceptance stated once", "priority": "Should", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit"], "dependsOn": ["M5-P2-T1"],
    "summary": "Cross-cutting assertions that apply to every user-facing story are stated once and referenced, "
               "rather than repeated per story where they would drift.",
    "tdd": {"red": "A test asserts a story repeating a global assertion is flagged as redundant; it fails "
                   "initially.",
            "green": "Add the global list and the redundancy check.",
            "refactor": "Let a story opt out explicitly, recording why."},
    "traces": {"fr": ["FR-GEN-05"], "nfr": ["NFR-UX-06"], "us": ["US-DOC-01"]},
    "criteria": [{"id": "M5-P2-T2-C1", "kind": "auto", "text": "A repeated global assertion is flagged.",
                  "done": True}]},
   {"id": "M5-P2-T3", "title": "Plain-language check", "priority": "Should", "autonomy": "auto",
    "status": "passing", "layer": "validator", "testLayers": ["unit", "manual"], "dependsOn": ["M5-P2-T2"],
    "summary": "Reader-facing prose avoids internal tool names and undefined jargon; a term that cannot be "
               "avoided is defined where it first appears.",
    "tdd": {"red": "A test flags a requirement using an internal tool name in reader-facing prose; it fails with "
                   "no check.",
            "green": "Add the vocabulary check with a per-project allowlist.",
            "refactor": "Report the first offending occurrence per term rather than every occurrence."},
    "traces": {"fr": ["FR-GEN-05"], "nfr": ["NFR-UX-04", "NFR-UX-06"]},
    "criteria": [{"id": "M5-P2-T3-C1", "kind": "auto", "text": "An internal tool name in reader-facing prose is "
                                                               "flagged.", "done": True},
                 {"id": "M5-P2-T3-C2", "kind": "human-review", "text": "A reviewer outside the specialism can "
                                                                       "follow the document.", "done": True}]}]}],

"M6": [
 {"id": "M6-P1", "title": "Technical specification generator", "dependsOn": [],
  "summary": "Technical and non-functional requirements, tracing to the functional requirements that motivate "
             "them, with measurable targets rather than adjectives.",
  "completion": ["A technical specification validates and traces downward correctly.",
                 "Every target is a number with a unit."],
  "tasks": [
   {"id": "M6-P1-T1", "title": "Technical schema and generator", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Publish the technical schema — principles, stack, components, data model, cross-cutting concerns, "
               "requirements, targets, risks — and the generator that produces a validating document.",
    "tdd": {"red": "A test generates from a fixture and asserts the output validates and every technical "
                   "requirement traces at least one functional requirement or decision; it fails initially.",
            "green": "Implement the schema and generator.",
            "refactor": "Share the catalogue renderer with the functional generator."},
    "traces": {"fr": ["FR-DOC-01", "FR-TRC-03"], "nfr": ["NFR-ARC-01"], "us": ["US-DOC-01", "US-TRC-02"]},
    "criteria": [{"id": "M6-P1-T1-C1", "kind": "auto", "text": "The generated document validates.", "done": True},
                 {"id": "M6-P1-T1-C2", "kind": "auto", "text": "Every technical requirement traces upward.",
                  "done": True}]},
   {"id": "M6-P1-T2", "title": "Architecture decision records", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "manual"], "dependsOn": ["M6-P1-T1"],
    "summary": "Each decision carries context, the decision itself, the alternatives considered and the "
               "consequences accepted — so that a later reader can tell whether the reasoning still holds.",
    "tdd": {"red": "A test asserts a decision missing its alternatives fails validation; it fails initially.",
            "green": "Require all four parts and render them distinctly.",
            "refactor": "Let a decision supersede another by identifier rather than by editing it."},
    "traces": {"fr": ["FR-DOC-01", "FR-AMD-04"], "nfr": ["NFR-EVO-05"], "us": ["US-AMD-01"]},
    "criteria": [{"id": "M6-P1-T2-C1", "kind": "auto", "text": "A decision missing alternatives or consequences "
                                                               "fails validation.", "done": True},
                 {"id": "M6-P1-T2-C2", "kind": "human-review", "text": "A reviewer confirms each decision's "
                                                                       "reasoning is recoverable.", "done": True}]},
   {"id": "M6-P1-T3", "title": "Measurable targets", "priority": "Must", "autonomy": "auto", "layer": "generator",
    "status": "passing", "testLayers": ["unit"], "dependsOn": ["M6-P1-T1"],
    "summary": "Every performance, size or quality target is stated as a number with a unit and a note on how it "
               "is measured, so that it can become a machine-checkable criterion later.",
    "tdd": {"red": "A test flags a target stated as an adjective; it fails with no check.",
            "green": "Require a numeric target and a measurement note.",
            "refactor": "Expose targets so plan tasks can cite them directly in criteria."},
    "traces": {"fr": ["FR-PLN-05"], "nfr": ["NFR-PRF-01"], "us": ["US-PLN-02"]},
    "criteria": [{"id": "M6-P1-T3-C1", "kind": "auto", "text": "A non-numeric target is flagged.", "done": True},
                 {"id": "M6-P1-T3-C2", "kind": "auto", "text": "Every target names how it is measured.",
                  "done": True}]}]},

 {"id": "M6-P2", "title": "Safety and secrets constraints", "dependsOn": ["M6-P1"],
  "summary": "The technical document is where the never-do rules are written down: no secret values in artefacts, "
             "no destructive operations unattended.",
  "completion": ["A secret-shaped literal anywhere in a generated artefact fails a check.",
                 "Prohibited operations are enumerated and referenced by the execution layer."],
  "tasks": [
   {"id": "M6-P2-T1", "title": "Secret-literal scanner", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "validator", "testLayers": ["unit", "CI"], "dependsOn": [],
    "summary": "Scan every generated document, prompt, ledger and commit for credential-shaped literals, and fail "
               "when one is found; secrets may appear only as variable names.",
    "tdd": {"red": "A test seeds a token-shaped literal into a fixture document and asserts the scan fails naming "
                   "the file and line; it fails with no scanner.",
            "green": "Implement the scan across all generated artefacts.",
            "refactor": "Share the pattern set with the host project's existing secret scanning where present."},
    "traces": {"fr": ["FR-GEN-04"], "nfr": ["NFR-SEC-01"], "us": ["US-EXE-01"]},
    "criteria": [{"id": "M6-P2-T1-C1", "kind": "auto", "text": "A seeded secret literal fails the scan.",
                  "done": True},
                 {"id": "M6-P2-T1-C2", "kind": "auto", "text": "A variable name referencing a secret passes.",
                  "done": True}]},
   {"id": "M6-P2-T2", "title": "Prohibited-operation list", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "schema", "testLayers": ["unit"], "dependsOn": ["M6-P2-T1"],
    "summary": "Enumerate the operations no unattended run may perform — force-push, history rewrite, deleting "
               "unmerged branches, deleting outside the working area — as data the execution layer reads.",
    "tdd": {"red": "A test asserts each prohibited operation is present in the published list and that the "
                   "execution layer reads it rather than restating it; it fails initially.",
            "green": "Publish the list and reference it from the orchestrator.",
            "refactor": "Make additions to the list automatically covered by the execution guard tests."},
    "traces": {"fr": ["FR-EXE-12"], "nfr": ["NFR-SEC-04"], "us": ["US-EXE-01"]},
    "criteria": [{"id": "M6-P2-T2-C1", "kind": "auto", "text": "The published list contains every prohibited "
                                                               "operation.", "done": True},
                 {"id": "M6-P2-T2-C2", "kind": "auto", "text": "The execution layer reads the list rather than "
                                                               "duplicating it.", "done": True}]}]}],

"M7": [
 {"id": "M7-P1", "title": "Trace universe", "dependsOn": [],
  "summary": "Read every document's embedded specification, build the identifier index across core documents and "
             "addenda, and resolve every trace to the document that defines it.",
  "completion": ["The index is built from the documents themselves.",
                 "Every trace resolves or is reported.",
                 "An absent addendum is reported and does not stop the build."],
  "tasks": [
   {"id": "M7-P1-T1", "title": "Build the identifier index from documents", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "validator", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Extract each document's specification and build one index of every identifier it defines, so that "
               "no maintained list of requirements exists anywhere.",
    "tdd": {"red": "A test adds a requirement to a fixture document and asserts it appears in the index with no "
                   "other change; it fails while the index is hand-maintained.",
            "green": "Build the index by extraction at run time.",
            "refactor": "Cache within a run only, never across runs."},
    "traces": {"fr": ["FR-TRC-03", "FR-TRC-04"], "nfr": ["NFR-DAT-05"], "adr": ["ADR-04"], "us": ["US-TRC-02"]},
    "criteria": [{"id": "M7-P1-T1-C1", "kind": "auto", "text": "A new requirement appears in the index without "
                                                               "any other edit.", "done": True}]},
   {"id": "M7-P1-T2", "title": "Prefix routing for addenda", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "validator", "testLayers": ["unit", "e2e"], "dependsOn": ["M7-P1-T1"],
    "summary": "Map identifier prefixes to the documents that define them so a trace link opens the right file, "
               "and merge addendum identifiers into the coverage universe.",
    "tdd": {"red": "A test traces an addendum identifier and asserts the link resolves to the addendum, and that "
                   "the identifier joins the coverage universe; both fail initially.",
            "green": "Implement prefix-to-document routing and universe merging.",
            "refactor": "Derive the routing table from the documents present rather than configuring it."},
    "traces": {"fr": ["FR-AMD-02", "FR-TRC-07"], "nfr": ["NFR-EVO-03"], "adr": ["ADR-12"], "us": ["US-AMD-01"]},
    "criteria": [{"id": "M7-P1-T2-C1", "kind": "auto", "text": "An addendum trace resolves to the addendum.",
                  "done": True},
                 {"id": "M7-P1-T2-C2", "kind": "auto", "text": "Addendum identifiers join the coverage universe.",
                  "done": True}]},
   {"id": "M7-P1-T3", "title": "Graceful degradation without an addendum", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "validator", "testLayers": ["unit"], "dependsOn": ["M7-P1-T2"],
    "summary": "When an addendum file is absent, generation still succeeds, produces the core output unchanged, "
               "and reports the absence explicitly.",
    "tdd": {"red": "A test removes an addendum and asserts generation succeeds, output matches the core baseline, "
                   "and the absence is reported; it fails while absence raises.",
            "green": "Guard each addendum read and report what was skipped.",
            "refactor": "Use one guarded-read helper for every optional input."},
    "traces": {"fr": ["FR-AMD-03", "FR-GEN-03"], "nfr": ["NFR-VAL-05"], "us": ["US-AMD-01", "US-VAL-02"]},
    "criteria": [{"id": "M7-P1-T3-C1", "kind": "auto", "text": "Generation succeeds with the addendum absent.",
                  "done": True},
                 {"id": "M7-P1-T3-C2", "kind": "auto", "text": "The absence is reported, never silent.",
                  "done": True}]}]},

 {"id": "M7-P2", "title": "Coverage gate", "dependsOn": ["M7-P1"],
  "summary": "Compute the coverage matrix from the trace universe and the plan, and fail the build when anything "
             "is unclaimed.",
  "completion": ["An unclaimed requirement fails and is named.",
                 "An explicit exclusion passes and is reported.",
                 "No configuration downgrades the failure."],
  "tasks": [
   {"id": "M7-P2-T1", "title": "Coverage matrix computation", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "validator", "testLayers": ["unit"], "dependsOn": [],
    "summary": "For every requirement and decision, compute the set of units that claim it, and present the "
               "matrix in the plan index.",
    "tdd": {"red": "A test asserts the matrix lists every identifier in the universe with its claiming units; it "
                   "fails with no computation.",
            "green": "Compute claims from task and milestone traces.",
            "refactor": "Return the matrix as data so both the gate and the renderer consume it."},
    "traces": {"fr": ["FR-TRC-04"], "nfr": ["NFR-DAT-05"], "adr": ["ADR-04"], "us": ["US-TRC-01"]},
    "criteria": [{"id": "M7-P2-T1-C1", "kind": "auto", "text": "Every universe identifier appears in the matrix.",
                  "done": True}]},
   {"id": "M7-P2-T2", "title": "Blocking coverage gate", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "validator", "testLayers": ["unit", "CI"], "dependsOn": ["M7-P2-T1"],
    "summary": "Fail generation, listing every unclaimed identifier, and make the failure non-downgradable.",
    "tdd": {"red": "Tests seed an unclaimed requirement and assert generation exits non-zero naming it, and that "
                   "no flag turns the failure into a warning; both fail initially.",
            "green": "Add the gate before any file is written.",
            "refactor": "Report unclaimed identifiers grouped by area so the fix is obvious."},
    "traces": {"fr": ["FR-TRC-05"], "nfr": ["NFR-VAL-03"], "adr": ["ADR-04"], "us": ["US-TRC-01"]},
    "criteria": [{"id": "M7-P2-T2-C1", "kind": "auto", "text": "An unclaimed requirement fails generation and is "
                                                               "named.", "done": True},
                 {"id": "M7-P2-T2-C2", "kind": "auto", "text": "No configuration downgrades the failure.",
                  "done": True},
                 {"id": "M7-P2-T2-C3", "kind": "auto", "text": "No plan file is written when the gate fails.",
                  "done": True}]},
   {"id": "M7-P2-T3", "title": "Exclusions with recorded reasons", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "validator", "testLayers": ["unit"], "dependsOn": ["M7-P2-T2"],
    "summary": "A requirement may leave the coverage universe only through an explicit exclusion carrying a "
               "reason, and every exclusion is reported alongside the matrix.",
    "tdd": {"red": "A test asserts an exclusion without a reason is rejected and that a valid exclusion is listed "
                   "in the report; both fail initially.",
            "green": "Require the reason and render the exclusion list.",
            "refactor": "Show exclusions in the matrix rather than in a separate place."},
    "traces": {"fr": ["FR-TRC-06"], "us": ["US-TRC-01"]},
    "criteria": [{"id": "M7-P2-T3-C1", "kind": "auto", "text": "An exclusion without a reason is rejected.",
                  "done": True},
                 {"id": "M7-P2-T3-C2", "kind": "auto", "text": "Exclusions are reported with the matrix.",
                  "done": True}]},
   {"id": "M7-P2-T4", "title": "Retired identifiers", "priority": "Should", "autonomy": "auto", "layer": "schema",
    "status": "passing", "testLayers": ["unit"], "dependsOn": ["M7-P2-T3"],
    "summary": "A dropped requirement is retired in place with a reason, keeping its identifier reserved, and is "
               "rendered distinctly so it is never mistaken for live scope.",
    "tdd": {"red": "A test asserts a retired identifier is still present, is excluded from coverage, and that "
                   "reusing its number fails validation; all fail initially.",
            "green": "Add the retired marker and the reuse check.",
            "refactor": "Render retired entries with a distinct treatment."},
    "traces": {"fr": ["FR-TRC-02"], "adr": ["ADR-03"], "us": ["US-TRC-03"]},
    "criteria": [{"id": "M7-P2-T4-C1", "kind": "auto", "text": "A retired identifier remains reserved.",
                  "done": True},
                 {"id": "M7-P2-T4-C2", "kind": "auto", "text": "Reusing a retired number fails validation.",
                  "done": True}]}]}],

"M8": [
 {"id": "M8-P1", "title": "Plan data model", "dependsOn": [],
  "summary": "The canonical spine and the per-milestone detail files, plus dependency validation before anything "
             "is written.",
  "completion": ["A plan is produced from data alone.",
                 "Cycles and unknown dependencies are rejected before any file is written."],
  "tasks": [
   {"id": "M8-P1-T1", "title": "Canonical spine and detail separation", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "schema", "testLayers": ["unit"], "dependsOn": [],
    "summary": "One module holds the legend, milestones, dependencies and exit criteria; per-milestone detail "
               "lives in separate files loaded by identifier, so milestones can be authored independently.",
    "tdd": {"red": "A test adds a milestone detail file and asserts it is picked up with no change to the spine "
                   "beyond its entry; it fails while detail is inline.",
            "green": "Split the spine from the detail and load detail by identifier.",
            "refactor": "Fail loudly when a spine entry has no detail file and is marked detailed."},
    "traces": {"fr": ["FR-PLN-01", "FR-PLN-02"], "nfr": ["NFR-ARC-06"], "us": ["US-PLN-01"]},
    "criteria": [{"id": "M8-P1-T1-C1", "kind": "auto", "text": "A new detail file is picked up automatically.",
                  "done": True},
                 {"id": "M8-P1-T1-C2", "kind": "auto", "text": "A milestone marked detailed with no detail file "
                                                               "fails.", "done": True}]},
   {"id": "M8-P1-T2", "title": "Dependency validation", "priority": "Must", "autonomy": "auto", "layer": "validator",
    "status": "passing", "testLayers": ["unit"], "dependsOn": ["M8-P1-T1"],
    "summary": "Reject a dependency cycle or a reference to a unit that does not exist, before any file is "
               "written.",
    "tdd": {"red": "Tests seed a cycle and an unknown dependency and assert generation exits non-zero naming each "
                   "and writing nothing; both fail initially.",
            "green": "Validate the graph before generation.",
            "refactor": "Report the full cycle path, not just one member."},
    "traces": {"fr": ["FR-PLN-03"], "us": ["US-PLN-01"]},
    "criteria": [{"id": "M8-P1-T2-C1", "kind": "auto", "text": "A cycle is reported with its full path.",
                  "done": True},
                 {"id": "M8-P1-T2-C2", "kind": "auto", "text": "No file is written when the graph is invalid.",
                  "done": True}]},
   {"id": "M8-P1-T3", "title": "Task contract: test-first, criteria, classification", "priority": "Must",
    "status": "passing", "autonomy": "auto", "layer": "schema", "testLayers": ["unit"], "dependsOn": ["M8-P1-T1"],
    "summary": "Every task must carry a red/green/refactor triple, at least one machine-checkable criterion, an "
               "autonomy class, its verification layers and an implementation layer.",
    "tdd": {"red": "Tests seed a task with no red step, one with no machine-checkable criterion and one with no "
                   "autonomy class, asserting three distinct failures; all fail initially.",
            "green": "Require each field in the schema and the validator.",
            "refactor": "Allow a documented, narrowly scoped exception that reports as a warning."},
    "traces": {"fr": ["FR-PLN-04", "FR-PLN-05", "FR-PLN-06", "FR-PLN-07", "FR-PLN-10", "FR-PLN-11"],
               "nfr": ["NFR-VAL-04"], "adr": ["ADR-06", "ADR-07"], "us": ["US-PLN-02", "US-PLN-03"]},
    "criteria": [{"id": "M8-P1-T3-C1", "kind": "auto", "text": "A task without a red step fails validation.",
                  "done": True},
                 {"id": "M8-P1-T3-C2", "kind": "auto", "text": "A task without a machine-checkable criterion "
                                                               "fails validation.", "done": True},
                 {"id": "M8-P1-T3-C3", "kind": "auto", "text": "A documented exception reports as a warning, not "
                                                               "a failure.", "done": True}]},
   {"id": "M8-P1-T4", "title": "Exit criteria and prerequisites", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "schema", "testLayers": ["unit"], "dependsOn": ["M8-P1-T3"],
    "summary": "Every phase and milestone declares exit criteria, and external prerequisites are held in a "
               "separate human-owned checklist rather than mixed into the work.",
    "tdd": {"red": "Tests assert a milestone without exit criteria fails and that prerequisites render "
                   "separately, marked human-owned; both fail initially.",
            "green": "Require exit criteria and add the prerequisite list.",
            "refactor": "Link each prerequisite to the tasks it unblocks."},
    "traces": {"fr": ["FR-PLN-08", "FR-PLN-12"], "us": ["US-PLN-03"]},
    "criteria": [{"id": "M8-P1-T4-C1", "kind": "auto", "text": "A milestone without exit criteria fails "
                                                               "validation.", "done": True},
                 {"id": "M8-P1-T4-C2", "kind": "auto", "text": "Prerequisites are listed separately and marked "
                                                               "human-owned.", "done": True}]}]},

 {"id": "M8-P2", "title": "Generation, waves and prompts", "dependsOn": ["M8-P1"],
  "summary": "Emit the plan index and one document per milestone, with the wave ordering derived from the "
             "dependency graph and a self-contained execution prompt for every unit.",
  "completion": ["Waves are derived and correct.",
                 "Every milestone carries a prompt a worker with no context can follow."],
  "tasks": [
   {"id": "M8-P2-T1", "title": "Topological wave ordering", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Compute an ordered set of waves in which every milestone depends only on earlier waves, sorted "
               "for deterministic output, and render it in the index.",
    "tdd": {"red": "A test asserts every milestone in a wave depends only on earlier waves, and that changing a "
                   "dependency changes the ordering with no other edit; both fail initially.",
            "green": "Implement the ordering and render it.",
            "refactor": "Sort within a wave so output is stable across runs."},
    "traces": {"fr": ["FR-PLN-09"], "nfr": ["NFR-DAT-05", "NFR-GEN-01"], "adr": ["ADR-08"], "us": ["US-PLN-04"]},
    "criteria": [{"id": "M8-P2-T1-C1", "kind": "auto", "text": "Every wave member depends only on earlier waves.",
                  "done": True},
                 {"id": "M8-P2-T1-C2", "kind": "auto", "text": "Wave ordering is stable across runs.",
                  "done": True}]},
   {"id": "M8-P2-T2", "title": "Plan index and milestone documents", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "e2e"], "dependsOn": ["M8-P2-T1"],
    "summary": "Emit the index carrying milestones, waves, coverage and prerequisites, and one document per "
               "milestone carrying its own phases, tasks, criteria and live status.",
    "tdd": {"red": "A test asserts the index lists every milestone and that each milestone document embeds its "
                   "own specification with matching identifier; it fails initially.",
            "green": "Implement both renderers over the shared shell.",
            "refactor": "Share the catalogue and status renderers between the two."},
    "traces": {"fr": ["FR-PLN-01", "FR-PLN-02"], "nfr": ["NFR-ARC-05"], "us": ["US-PLN-01", "US-STA-01"]},
    "criteria": [{"id": "M8-P2-T2-C1", "kind": "auto", "text": "The index lists every milestone.", "done": True},
                 {"id": "M8-P2-T2-C2", "kind": "auto", "text": "Each milestone document's embedded identifier "
                                                               "matches its file.", "done": True}]},
   {"id": "M8-P2-T3", "title": "Self-contained execution prompts", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "manual"], "dependsOn": ["M8-P2-T2"],
    "summary": "Generate an orchestrator prompt and a per-milestone prompt naming the plan file, the status "
               "contract, the locked decisions, the verification gauntlet and the report contract.",
    "tdd": {"red": "A test asserts every generated prompt contains all five elements and references no context "
                   "outside the repository; it fails initially.",
            "green": "Generate prompts from plan data and the locked-decisions table.",
            "refactor": "Emit prompts into both the index and each milestone document from one builder."},
    "traces": {"fr": ["FR-EXE-03"], "nfr": ["NFR-EXE-04"], "adr": ["ADR-10"], "us": ["US-EXE-01"]},
    "criteria": [{"id": "M8-P2-T3-C1", "kind": "auto", "text": "Every prompt names plan, status contract, locked "
                                                               "decisions, gauntlet and report contract.",
                  "done": True},
                 {"id": "M8-P2-T3-C2", "kind": "human-review", "text": "A reviewer confirms a worker could act on "
                                                                       "the prompt with no other context.",
                  "done": True}]},
   {"id": "M8-P2-T4", "title": "Coarse effort signal", "priority": "Could", "autonomy": "auto", "layer": "schema",
    "status": "passing", "testLayers": ["unit"], "dependsOn": ["M8-P2-T2"],
    "summary": "An optional effort or risk signal per task, for human sequencing judgement only, never consulted "
               "by any automated gate.",
    "tdd": {"red": "A test asserts the signal renders when present, is optional, and is referenced by no gate; it "
                   "fails initially.",
            "green": "Add the optional field and render it.",
            "refactor": "Assert in the gate tests that the field is never read."},
    "traces": {"fr": ["FR-PLN-13"], "us": ["US-PLN-01"]},
    "criteria": [{"id": "M8-P2-T4-C1", "kind": "auto", "text": "The signal is optional and renders when present.",
                  "done": True},
                 {"id": "M8-P2-T4-C2", "kind": "auto", "text": "No gate reads the signal.", "done": True}]}]}],
}
