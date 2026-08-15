# -*- coding: utf-8 -*-
"""Zero-to-Ship plan detail — M9 to M12."""

DETAIL = {

"M9": [
 {"id": "M9-P1", "title": "Rendered-artefact validation", "dependsOn": [],
  "summary": "Check the produced files rather than the data behind them, so a generator regression cannot ship "
             "silently.",
  "completion": ["Validation extracts from rendered output and asserts structure.",
                 "A corrupted output file is caught.",
                 "Documented exceptions report as warnings on every run."],
  "tasks": [
   {"id": "M9-P1-T1", "title": "Validate from the rendered output", "priority": "Must", "autonomy": "auto",
    "layer": "validator", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Open each produced file, extract its embedded specification from the rendered output, and assert "
               "the structural invariants on that — never on the generator's in-memory data.",
    "tdd": {"red": "A test truncates a generated file's specification block and asserts validation fails naming "
                   "the file and the parse error; it fails while validation reads source data.",
            "green": "Point the validator at the output directory and use the shared extraction function.",
            "refactor": "Assert the validator never imports the generator's data modules."},
    "traces": {"fr": ["FR-VAL-02"], "nfr": ["NFR-VAL-02"], "adr": ["ADR-09"], "us": ["US-VAL-01"]},
    "criteria": [{"id": "M9-P1-T1-C1", "kind": "auto", "text": "A truncated output file fails validation.",
                  "done": False},
                 {"id": "M9-P1-T1-C2", "kind": "auto", "text": "The validator reads only produced files.",
                  "done": False}]},
   {"id": "M9-P1-T2", "title": "Plan structural invariants", "priority": "Must", "autonomy": "auto",
    "layer": "validator", "testLayers": ["unit"], "dependsOn": ["M9-P1-T1"],
    "summary": "Assert that every task in a rendered plan has a status and criteria, that every trace resolves in "
               "the document's own catalogue, and that every milestone in the index has its detail document.",
    "tdd": {"red": "Tests seed a task with no status, a trace absent from the catalogue and a missing milestone "
                   "document, asserting three distinct failures; all fail initially.",
            "green": "Implement the assertions over the extracted plan specification.",
            "refactor": "Print a per-document summary line of phases, tasks and criteria counted."},
    "traces": {"fr": ["FR-VAL-04"], "nfr": ["NFR-VAL-01"], "adr": ["ADR-09"], "us": ["US-VAL-01"]},
    "criteria": [{"id": "M9-P1-T2-C1", "kind": "auto", "text": "A task without a status fails validation.",
                  "done": False},
                 {"id": "M9-P1-T2-C2", "kind": "auto", "text": "A trace absent from the catalogue fails "
                                                               "validation.", "done": False},
                 {"id": "M9-P1-T2-C3", "kind": "auto", "text": "A milestone with no detail document fails "
                                                               "validation.", "done": False}]},
   {"id": "M9-P1-T3", "title": "Declared exceptions", "priority": "Must", "autonomy": "auto", "layer": "validator",
    "testLayers": ["unit"], "dependsOn": ["M9-P1-T2"],
    "summary": "An approved exception to a rule lives in the validator with its justification, is scoped as "
               "narrowly as possible, and reports as a warning on every run so it never becomes invisible.",
    "tdd": {"red": "A test asserts an exception is reported on every run and cannot be widened by configuration; "
                   "it fails initially.",
            "green": "Express exceptions as scoped entries carrying a justification.",
            "refactor": "List all active exceptions in the run summary."},
    "traces": {"fr": ["FR-VAL-08"], "nfr": ["NFR-VAL-04"], "us": ["US-VAL-01"]},
    "criteria": [{"id": "M9-P1-T3-C1", "kind": "auto", "text": "Every active exception is reported each run.",
                  "done": False},
                 {"id": "M9-P1-T3-C2", "kind": "auto", "text": "An exception cannot be widened by configuration.",
                  "done": False}]}]},

 {"id": "M9-P2", "title": "Rendered-view check and honest reporting", "dependsOn": ["M9-P1"],
  "summary": "Confirm a document actually renders where a browser exists, and never count a check that did not "
             "run.",
  "completion": ["The render check exercises entries, filter and a priority toggle.",
                 "A skipped check is reported as skipped, with its reason."],
  "tasks": [
   {"id": "M9-P2-T1", "title": "Rendered-view check", "priority": "Should", "autonomy": "auto-with-mock",
    "layer": "validator", "testLayers": ["e2e"], "dependsOn": [],
    "summary": "Where a headless browser is available, load each generated document over a local server and "
               "confirm entries render, the filter narrows, and a priority toggle filters.",
    "tdd": {"red": "A test asserts the check fails against a document whose runtime throws, and passes against a "
                   "sound one; it fails with no check.",
            "green": "Implement the check against a headless browser and a local static server.",
            "refactor": "Reuse one browser session across documents to keep the check fast."},
    "traces": {"fr": ["FR-VAL-07"], "nfr": ["NFR-VAL-06"], "us": ["US-VAL-02"]},
    "criteria": [{"id": "M9-P2-T1-C1", "kind": "auto", "text": "A document whose runtime throws fails the check.",
                  "done": False},
                 {"id": "M9-P2-T1-C2", "kind": "auto", "text": "Entries, filter and priority toggle are all "
                                                               "exercised.", "done": False}]},
   {"id": "M9-P2-T2", "title": "Skipped checks reported honestly", "priority": "Must", "autonomy": "auto",
    "layer": "validator", "testLayers": ["unit"], "dependsOn": ["M9-P2-T1"],
    "summary": "When a check cannot run, report it as skipped with the reason and exclude it from any pass count; "
               "never report an unavailable check as passed.",
    "tdd": {"red": "A test runs with no browser available and asserts the summary says skipped and the pass count "
                   "excludes it; it fails while absence is silent.",
            "green": "Add a skipped severity and thread it through the summary.",
            "refactor": "Make the summary print counts of passed, failed, warned and skipped."},
    "traces": {"fr": ["FR-GEN-03"], "nfr": ["NFR-VAL-05"], "us": ["US-VAL-02"]},
    "criteria": [{"id": "M9-P2-T2-C1", "kind": "auto", "text": "An unavailable check is reported as skipped with "
                                                               "its reason.", "done": False},
                 {"id": "M9-P2-T2-C2", "kind": "auto", "text": "A skipped check is never counted as passed.",
                  "done": False}]},
   {"id": "M9-P2-T3", "title": "Generation and validation time budgets", "priority": "Should", "autonomy": "auto",
    "layer": "ops", "testLayers": ["perf", "CI"], "dependsOn": ["M9-P2-T2"],
    "summary": "Hold generation and validation inside their stated budgets so regeneration is never a reason to "
               "hand-edit output.",
    "tdd": {"red": "A test measures a full generate-and-validate cycle over a representative set and fails when "
                   "either exceeds its budget; it fails until the pipeline is optimised.",
            "green": "Measure, then remove the largest cost.",
            "refactor": "Report both timings in the run summary so regressions are visible."},
    "traces": {"fr": ["FR-DOC-06"], "nfr": ["NFR-PRF-01"], "us": ["US-VAL-01"]},
    "criteria": [{"id": "M9-P2-T3-C1", "kind": "auto", "text": "Generation completes within its budget.",
                  "done": False},
                 {"id": "M9-P2-T3-C2", "kind": "auto", "text": "Validation completes within its budget.",
                  "done": False}]}]},

 {"id": "M9-P3", "title": "Continuous-integration gates and branch policy", "dependsOn": ["M9-P2"],
  "summary": "Wire every gate into the pipeline as blocking, and enforce the branch tiers and the human-approved "
             "promotion.",
  "completion": ["All gates run on every change and block integration on failure.",
                 "Nothing reaches production without an explicit human approval."],
  "tasks": [
   {"id": "M9-P3-T1", "title": "Blocking pipeline gates", "priority": "Must", "autonomy": "auto", "layer": "ops",
    "testLayers": ["CI"], "dependsOn": [],
    "summary": "Schema validation, structural validation, the coverage gate and the secret scan run on every "
               "change and block integration when any fails.",
    "tdd": {"red": "A test asserts a change introducing an uncovered requirement fails the pipeline; it fails "
                   "while gates are advisory.",
            "green": "Add the gates as required checks.",
            "refactor": "Keep one summary check depending on the individual gates so branch protection has a "
                        "stable name when jobs are split."},
    "traces": {"fr": ["FR-VAL-05"], "nfr": ["NFR-OPS-02"], "us": ["US-TRC-01"]},
    "criteria": [{"id": "M9-P3-T1-C1", "kind": "auto", "text": "Each gate runs on every change.", "done": False},
                 {"id": "M9-P3-T1-C2", "kind": "auto", "text": "A failing gate blocks integration.",
                  "done": False}]},
   {"id": "M9-P3-T2", "title": "Branch tiers and generated-file marking", "priority": "Must", "autonomy": "auto",
    "layer": "ops", "testLayers": ["CI", "unit"], "dependsOn": ["M9-P3-T1"],
    "summary": "Work flows from unit branches into one integration branch and reaches production only by "
               "promotion; generated files are marked so reviews collapse them while keeping them in history.",
    "tdd": {"red": "Tests assert a direct write to production is refused and that generated files carry the "
                   "marking; both fail initially.",
            "green": "Configure the branch policy and the file attributes.",
            "refactor": "Document the exception that plan documents are generated yet tracked."},
    "traces": {"fr": ["FR-EXE-12", "FR-STA-05"], "nfr": ["NFR-OPS-03", "NFR-OPS-06"], "us": ["US-STA-03"]},
    "criteria": [{"id": "M9-P3-T2-C1", "kind": "auto", "text": "A direct write to production is refused.",
                  "done": False},
                 {"id": "M9-P3-T2-C2", "kind": "auto", "text": "Generated files are marked as generated.",
                  "done": False}]},
   {"id": "M9-P3-T3", "title": "Human-approved promotion", "priority": "Should", "autonomy": "human-gate",
    "layer": "ops", "testLayers": ["manual"], "dependsOn": ["M9-P3-T2"],
    "summary": "Promotion from the integration branch requires a person to have read the change and approved it, "
               "with each gate confirmed against its live source rather than a remembered result.",
    "tdd": {"red": "A checklist run asserts promotion cannot complete without a recorded human approval; it fails "
                   "while promotion is automatic.",
            "green": "Require review approval on the promotion request.",
            "refactor": "Record in the promotion template which live source each gate was confirmed against."},
    "traces": {"fr": ["FR-GEN-03"], "nfr": ["NFR-OPS-05"], "us": ["US-VAL-02"]},
    "criteria": [{"id": "M9-P3-T3-C1", "kind": "auto", "text": "Promotion is blocked without a recorded approval.",
                  "done": False},
                 {"id": "M9-P3-T3-C2", "kind": "human-review", "text": "The approver confirms each gate against a "
                                                                       "live source, not a remembered result.",
                  "done": False}]}]}],

"M10": [
 {"id": "M10-P1", "title": "Status model", "dependsOn": [],
  "summary": "The closed status vocabulary, its transitions, and the rule that status lives only in the plan "
             "document.",
  "completion": ["The vocabulary is closed and enforced.",
                 "Passing is reachable only after the named verification layers actually ran."],
  "tasks": [
   {"id": "M10-P1-T1", "title": "Closed status vocabulary and transitions", "priority": "Must", "autonomy": "auto",
    "layer": "schema", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Define the six statuses and the legal transitions between them, including that a human-review "
               "criterion blocks the milestone and not the task.",
    "tdd": {"red": "Tests assert an unknown status is rejected, that passing cannot be set directly from not "
                   "started, and that an open human-review criterion blocks milestone closure but not the task; "
                   "all fail initially.",
            "green": "Implement the vocabulary and the transition rules.",
            "refactor": "Generate the rendered legend from the same declaration the checks use."},
    "traces": {"fr": ["FR-STA-01", "FR-PLN-06"], "nfr": ["NFR-DAT-04"], "adr": ["ADR-05"],
               "us": ["US-STA-01", "US-PLN-02"]},
    "criteria": [{"id": "M10-P1-T1-C1", "kind": "auto", "text": "An unknown status is rejected.", "done": False},
                 {"id": "M10-P1-T1-C2", "kind": "auto", "text": "An illegal transition is rejected.",
                  "done": False},
                 {"id": "M10-P1-T1-C3", "kind": "auto", "text": "An open human-review criterion blocks the "
                                                                "milestone, not the task.", "done": False}]},
   {"id": "M10-P1-T2", "title": "Status only after verification actually ran", "priority": "Must",
    "autonomy": "auto", "layer": "orchestration", "testLayers": ["unit", "e2e"], "dependsOn": ["M10-P1-T1"],
    "summary": "A task may be set passing only when the verification layers it names ran and passed in the same "
               "run that is setting it.",
    "tdd": {"red": "A test attempts to set passing without a recorded verification result and asserts refusal; it "
                   "fails while status is unconditional.",
            "green": "Require a verification record naming the command and its result.",
            "refactor": "Store the record with the report rather than in the plan document."},
    "traces": {"fr": ["FR-GEN-03"], "nfr": ["NFR-EXE-10"], "us": ["US-EXE-06", "US-VAL-02"]},
    "criteria": [{"id": "M10-P1-T2-C1", "kind": "auto", "text": "Setting passing without a verification record is "
                                                                "refused.", "done": False},
                 {"id": "M10-P1-T2-C2", "kind": "auto", "text": "The record names the command that produced the "
                                                                "result.", "done": False}]}]},

 {"id": "M10-P2", "title": "Write-back tool", "dependsOn": ["M10-P1"],
  "summary": "The command that edits only the embedded specification, preserving every other byte of the file.",
  "completion": ["Only the specification block changes.",
                 "Invalid input is rejected without modifying the file."],
  "tasks": [
   {"id": "M10-P2-T1", "title": "Byte-preserving in-place edit", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Locate the specification block, parse it, apply the change, and rewrite only that region, leaving "
               "the rest of the file untouched.",
    "tdd": {"red": "A test writes a status back and asserts the file differs only inside the block; it fails "
                   "while the file is regenerated wholesale.",
            "green": "Implement the located, in-place rewrite.",
            "refactor": "Serialise deterministically so unrelated keys never reorder."},
    "traces": {"fr": ["FR-STA-02", "FR-STA-03"], "nfr": ["NFR-GEN-01"], "adr": ["ADR-05"], "us": ["US-STA-02"]},
    "criteria": [{"id": "M10-P2-T1-C1", "kind": "auto", "text": "Only bytes inside the specification block "
                                                                "change.", "done": False},
                 {"id": "M10-P2-T1-C2", "kind": "auto", "text": "Key order is stable across writes.",
                  "done": False}]},
   {"id": "M10-P2-T2", "title": "Reject invalid input without writing", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["unit"], "dependsOn": ["M10-P2-T1"],
    "summary": "An unknown identifier, a status outside the enumeration, or an unknown criterion is rejected "
               "before any write occurs.",
    "tdd": {"red": "Tests attempt each invalid case and assert the file is unchanged and the failure names the "
                   "input; all fail initially.",
            "green": "Validate before writing.",
            "refactor": "Share the enumeration with the schema rather than restating it."},
    "traces": {"fr": ["FR-STA-03"], "nfr": ["NFR-DAT-04"], "us": ["US-STA-02"]},
    "criteria": [{"id": "M10-P2-T2-C1", "kind": "auto", "text": "An unknown identifier leaves the file unchanged.",
                  "done": False},
                 {"id": "M10-P2-T2-C2", "kind": "auto", "text": "An invalid status leaves the file unchanged.",
                  "done": False}]},
   {"id": "M10-P2-T3", "title": "Criterion ticking and status report command", "priority": "Should",
    "autonomy": "auto", "layer": "orchestration", "testLayers": ["unit"], "dependsOn": ["M10-P2-T2"],
    "summary": "Tick named criteria — all machine-checkable ones, or a named subset — and print a status summary "
               "per phase and milestone without opening a browser.",
    "tdd": {"red": "Tests assert ticking all machine-checkable criteria leaves human-review ones untouched, and "
                   "that the report prints counts per phase; both fail initially.",
            "green": "Implement ticking modes and the report command.",
            "refactor": "Compute the report from the same rollup the document renders."},
    "traces": {"fr": ["FR-STA-06", "FR-STA-07"], "us": ["US-STA-01", "US-STA-02"]},
    "criteria": [{"id": "M10-P2-T3-C1", "kind": "auto", "text": "Ticking all machine criteria leaves human-review "
                                                                "criteria untouched.", "done": False},
                 {"id": "M10-P2-T3-C2", "kind": "auto", "text": "The report prints status counts per phase and "
                                                                "milestone.", "done": False}]}]},

 {"id": "M10-P3", "title": "Rollup, review queue and history", "dependsOn": ["M10-P2"],
  "summary": "Derive every aggregate rather than storing it, surface outstanding human review in one place, and "
             "commit status with the work it describes.",
  "completion": ["Rollups are derived, never stored.",
                 "The human-review queue lists every outstanding item across the plan.",
                 "A status change is committed with its work."],
  "tasks": [
   {"id": "M10-P3-T1", "title": "Derived rollup", "priority": "Must", "autonomy": "auto", "layer": "runtime",
    "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Phase, milestone and programme progress are computed from task status at render time, and never "
               "stored where they could disagree.",
    "tdd": {"red": "A test changes one task's status and asserts every rollup updates with no other edit, and "
                   "that no stored aggregate exists in the specification; both fail initially.",
            "green": "Compute rollups at render time.",
            "refactor": "Share one rollup function between the document and the report command."},
    "traces": {"fr": ["FR-STA-04"], "nfr": ["NFR-DAT-05"], "us": ["US-STA-01"]},
    "criteria": [{"id": "M10-P3-T1-C1", "kind": "auto", "text": "A task status change updates every rollup.",
                  "done": False},
                 {"id": "M10-P3-T1-C2", "kind": "auto", "text": "No aggregate is stored in the specification.",
                  "done": False}]},
   {"id": "M10-P3-T2", "title": "Human-review queue", "priority": "Should", "autonomy": "auto", "layer": "runtime",
    "testLayers": ["unit", "e2e"], "dependsOn": ["M10-P3-T1"],
    "summary": "List every outstanding human-review criterion across the whole plan, so a reviewer can clear them "
               "in one pass before a milestone closes.",
    "tdd": {"red": "A test asserts the queue lists exactly the outstanding human-review criteria and empties as "
                   "they are signed off; it fails initially.",
            "green": "Derive the queue from the plan.",
            "refactor": "Link each queue entry to its task."},
    "traces": {"fr": ["FR-STA-08"], "us": ["US-STA-01"]},
    "criteria": [{"id": "M10-P3-T2-C1", "kind": "auto", "text": "The queue lists exactly the outstanding items.",
                  "done": False}]},
   {"id": "M10-P3-T3", "title": "Atomic commit of work and status", "priority": "Should", "autonomy": "auto",
    "layer": "ops", "testLayers": ["unit", "CI"], "dependsOn": ["M10-P3-T2"],
    "summary": "Each unit's implementation and its plan-document status change land in one commit naming the unit "
               "identifier, so history reads as a sequence of completed units.",
    "tdd": {"red": "A test asserts the commit for a unit contains both the implementation and the status change "
                   "and names the identifier; it fails while they are committed separately.",
            "green": "Stage both in the unit's commit.",
            "refactor": "Derive the commit subject from the unit identifier and title."},
    "traces": {"fr": ["FR-EXE-11", "FR-STA-05"], "nfr": ["NFR-EXE-11", "NFR-OPS-04"], "adr": ["ADR-11"],
               "us": ["US-STA-03"]},
    "criteria": [{"id": "M10-P3-T3-C1", "kind": "auto", "text": "One commit contains the work and the status "
                                                                "change.", "done": False},
                 {"id": "M10-P3-T3-C2", "kind": "auto", "text": "The commit message names the unit identifier.",
                  "done": False}]}]}],

"M11": [
 {"id": "M11-P1", "title": "Scheduling", "dependsOn": [],
  "summary": "Ready-set computation, wave-ordered dispatch, the concurrency ceiling and write-set disjointness.",
  "completion": ["The ready set is recomputed every iteration.",
                 "No two concurrently dispatched units write the same path."],
  "tasks": [
   {"id": "M11-P1-T1", "title": "Ready-set computation", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Eligible units are those not started, whose dependencies all pass, which are not human-gated, and "
               "whose milestone is in the current wave — recomputed every iteration, never cached.",
    "tdd": {"red": "Tests assert a human-gated unit never appears, a unit with a failing dependency never "
                   "appears, and that an external status edit between iterations is picked up; all fail "
                   "initially.",
            "green": "Implement the predicate and recompute each iteration.",
            "refactor": "Expose the ready set as data so the report command can print it."},
    "traces": {"fr": ["FR-EXE-01", "FR-PLN-07"], "nfr": ["NFR-EXE-01", "NFR-SEC-03"], "adr": ["ADR-07"],
               "us": ["US-EXE-01", "US-PLN-03"]},
    "criteria": [{"id": "M11-P1-T1-C1", "kind": "auto", "text": "Human-gated units never enter the ready set.",
                  "done": False},
                 {"id": "M11-P1-T1-C2", "kind": "auto", "text": "An external status change is reflected on the "
                                                                "next iteration.", "done": False}]},
   {"id": "M11-P1-T2", "title": "Wave-ordered dispatch with a concurrency ceiling", "priority": "Must",
    "autonomy": "auto", "layer": "orchestration", "testLayers": ["unit", "e2e"], "dependsOn": ["M11-P1-T1"],
    "summary": "Walk the waves in order, run the milestones within a wave concurrently up to the stated ceiling, "
               "and never begin a wave before its dependencies complete.",
    "tdd": {"red": "Tests assert no later-wave unit starts early and that excess work queues rather than being "
                   "refused; both fail initially.",
            "green": "Implement the wave walk and the bounded worker pool.",
            "refactor": "Derive the ceiling from available capacity with an explicit override."},
    "traces": {"fr": ["FR-EXE-02"], "nfr": ["NFR-EXE-09"], "adr": ["ADR-08"], "us": ["US-EXE-01", "US-PLN-04"]},
    "criteria": [{"id": "M11-P1-T2-C1", "kind": "auto", "text": "No unit starts before its wave is eligible.",
                  "done": False},
                 {"id": "M11-P1-T2-C2", "kind": "auto", "text": "Work beyond the ceiling queues rather than "
                                                                "failing.", "done": False}]},
   {"id": "M11-P1-T3", "title": "Write-set disjointness", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["unit", "e2e"], "dependsOn": ["M11-P1-T2"],
    "summary": "Two units that write the same path are never dispatched together; where disjointness cannot be "
               "established, they are serialised or isolated in separate working copies.",
    "tdd": {"red": "A test declares two units writing one path and asserts they are not dispatched together, and "
                   "that an edit conflict is reported rather than retried indefinitely; both fail initially.",
            "green": "Compute declared write sets and serialise on overlap.",
            "refactor": "Fall back to isolated working copies when overlap is unavoidable."},
    "traces": {"fr": ["FR-EXE-06"], "nfr": ["NFR-EXE-02", "NFR-EXE-03"], "us": ["US-EXE-05"]},
    "criteria": [{"id": "M11-P1-T3-C1", "kind": "auto", "text": "Overlapping write sets are never concurrent.",
                  "done": False},
                 {"id": "M11-P1-T3-C2", "kind": "auto", "text": "A second consecutive edit conflict is reported "
                                                                "as contention.", "done": False}]},
   {"id": "M11-P1-T4", "title": "Cost-aware worker selection", "priority": "Could", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["unit"], "dependsOn": ["M11-P1-T2"],
    "summary": "Choose the least capable worker sufficient for each unit, reserving the most capable for "
               "genuinely difficult design work, without changing any correctness guarantee.",
    "tdd": {"red": "A test asserts a mechanical unit selects the cheapest class and that selection never alters "
                   "the verification gauntlet; it fails initially.",
            "green": "Add the selection policy driven by the unit's declared layer and autonomy.",
            "refactor": "Make the policy overridable per unit and record the override."},
    "traces": {"fr": ["FR-EXE-13"], "us": ["US-EXE-01"]},
    "criteria": [{"id": "M11-P1-T4-C1", "kind": "auto", "text": "Selection never changes the verification "
                                                                "gauntlet.", "done": False}]}]},

 {"id": "M11-P2", "title": "Worker contract", "dependsOn": ["M11-P1"],
  "summary": "The brief a worker receives, the test-first discipline it follows, the report it must return, the "
             "safety rules it cannot break, and the separate worker that judges the result.",
  "completion": ["A worker acts correctly from its brief alone.",
                 "A worker returning no report is treated as failed.",
                 "No unattended worker uses a live credential or prompts interactively.",
                 "Nothing passes on the say-so of the worker that built it."],
  "tasks": [
   {"id": "M11-P2-T1", "title": "Self-contained brief assembly", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["unit", "manual"], "dependsOn": [],
    "summary": "Assemble each worker's brief from the plan, the locked decisions, the conventions summary, the "
               "verification gauntlet and the report contract, assuming no inherited context.",
    "tdd": {"red": "A test asserts a brief contains all five elements and references nothing outside the "
                   "repository; it fails initially.",
            "green": "Assemble briefs from the generated prompt plus current conventions.",
            "refactor": "Quote the locked-decisions table verbatim rather than summarising it."},
    "traces": {"fr": ["FR-EXE-03"], "nfr": ["NFR-EXE-04"], "us": ["US-EXE-01"]},
    "criteria": [{"id": "M11-P2-T1-C1", "kind": "auto", "text": "Every brief contains all five required "
                                                                "elements.", "done": False},
                 {"id": "M11-P2-T1-C2", "kind": "human-review", "text": "A reviewer confirms a cold worker could "
                                                                        "act on the brief alone.", "done": False}]},
   {"id": "M11-P2-T2", "title": "Test-first execution", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["e2e"], "dependsOn": ["M11-P2-T1"],
    "summary": "The worker writes the task's stated failing test, observes it fail, implements the minimum change "
               "to pass it, then refactors under a green suite.",
    "tdd": {"red": "An end-to-end run asserts the test file appears in a commit before the implementation and "
                   "that the test was observed failing; it fails while order is unenforced.",
            "green": "Enforce the order in the worker contract and record the observed failure.",
            "refactor": "Include the observed red result in the worker's report."},
    "traces": {"fr": ["FR-EXE-04", "FR-TRC-09"], "adr": ["ADR-06"], "us": ["US-EXE-02"]},
    "criteria": [{"id": "M11-P2-T2-C1", "kind": "auto", "text": "The failing test precedes the implementation.",
                  "done": False},
                 {"id": "M11-P2-T2-C2", "kind": "auto", "text": "The observed red result is recorded.",
                  "done": False}]},
   {"id": "M11-P2-T3", "title": "Mandatory structured report", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["unit", "e2e"], "dependsOn": ["M11-P2-T2"],
    "summary": "Every worker returns changes, verification actually run with the commands that produced it, "
               "blockers, and what the next worker needs to know. Silence is failure.",
    "tdd": {"red": "Tests assert a worker returning nothing is treated as failed and its unit is not marked "
                   "complete, and that a report claiming verification names its command; both fail initially.",
            "green": "Enforce the contract in the harness rather than requesting it in prose.",
            "refactor": "Validate the report shape and reject a malformed one."},
    "traces": {"fr": ["FR-EXE-10", "FR-GEN-03"], "nfr": ["NFR-EXE-06"], "adr": ["ADR-13"], "us": ["US-EXE-06"]},
    "criteria": [{"id": "M11-P2-T3-C1", "kind": "auto", "text": "A worker returning no report fails its unit.",
                  "done": False},
                 {"id": "M11-P2-T3-C2", "kind": "auto", "text": "A verification claim names its command.",
                  "done": False}]},
   {"id": "M11-P2-T4", "title": "Unattended safety guards", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["unit", "e2e"], "dependsOn": ["M11-P2-T3"],
    "summary": "No unattended unit uses a live credential, contacts a paid provider, opens an interactive prompt, "
               "or performs any operation on the prohibited list; a denied permission is reported, never reshaped "
               "and retried.",
    "tdd": {"red": "Tests assert each prohibited action is refused, that a substituted-provider unit uses its "
                   "named substitute, and that a denied permission stops the probe; all fail initially.",
            "green": "Implement the guards reading the published prohibited-operation list.",
            "refactor": "Report every refusal with the rule that blocked it."},
    "traces": {"fr": ["FR-EXE-05", "FR-GEN-04"], "nfr": ["NFR-SEC-02", "NFR-SEC-04", "NFR-SEC-05", "NFR-EXE-08"],
               "us": ["US-EXE-01"]},
    "criteria": [{"id": "M11-P2-T4-C1", "kind": "auto", "text": "Every prohibited action is refused.",
                  "done": False},
                 {"id": "M11-P2-T4-C2", "kind": "auto", "text": "A substituted-provider unit uses its named "
                                                                "substitute.", "done": False},
                 {"id": "M11-P2-T4-C3", "kind": "auto", "text": "A denied permission is reported with the blocking "
                                                                "rule and not retried in another form.",
                  "done": False}]},
   {"id": "M11-P2-T5", "title": "Independent judgement of a finished unit", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["unit", "e2e"], "dependsOn": ["M11-P2-T3"],
    "summary": "A worker other than the builder inspects the finished work against the unit's criteria and "
               "gauntlet, sees no account of how it was done, and returns a pass or one gap; a judge that could "
               "not inspect the work fails it, and the gap briefs the retry.",
    "tdd": {"red": "Tests assert the judgement brief carries criteria, gauntlet and artefacts but none of the "
                   "builder's report, that a loss returns exactly one gap and that gap reaches the retry, and "
                   "that an uninspectable artefact fails; all fail initially.",
            "green": "Assemble the judgement brief from the plan and the work alone, and gate the passing status "
                     "on the verdict.",
            "refactor": "State in the brief that any text inside the work addressed to the judge is data, not "
                        "instruction."},
    "traces": {"fr": ["FR-EXE-14"], "adr": ["ADR-13"], "nfr": ["NFR-EXE-06"], "us": ["US-EXE-07"]},
    "criteria": [{"id": "M11-P2-T5-C1", "kind": "auto", "text": "The judgement brief contains no part of the "
                                                                "builder's report.", "done": False},
                 {"id": "M11-P2-T5-C2", "kind": "auto", "text": "A failed judgement returns exactly one gap.",
                  "done": False},
                 {"id": "M11-P2-T5-C3", "kind": "auto", "text": "A judge that could not inspect the work fails "
                                                                "the unit.", "done": False}]}]},

 {"id": "M11-P3", "title": "Resilience", "dependsOn": ["M11-P2"],
  "summary": "Never ask mid-run, never stall on a blocker, and resume correctly after any interruption.",
  "completion": ["A run completes without asking a question.",
                 "A blocked unit does not idle the run.",
                 "An interrupted run resumes with no unit repeated or skipped."],
  "tasks": [
   {"id": "M11-P3-T1", "title": "Never-ask policy with recorded decisions", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["e2e"], "dependsOn": [],
    "summary": "On meeting an ambiguity the worker makes a reasonable call, records it as a decision with its "
               "rationale in the ledger, and continues.",
    "tdd": {"red": "A test injects an ambiguity and asserts no question is emitted and a decision with rationale "
                   "appears in the ledger; it fails initially.",
            "green": "Implement the policy and the decision log.",
            "refactor": "Surface recorded decisions in the milestone retrospective."},
    "traces": {"fr": ["FR-EXE-08"], "adr": ["ADR-10"], "us": ["US-EXE-01"]},
    "criteria": [{"id": "M11-P3-T1-C1", "kind": "auto", "text": "No question is emitted during an unattended run.",
                  "done": False},
                 {"id": "M11-P3-T1-C2", "kind": "auto", "text": "Each autonomous call is logged with its "
                                                                "rationale.", "done": False}]},
   {"id": "M11-P3-T2", "title": "Bounded retries and blocker policy", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["unit", "e2e"], "dependsOn": ["M11-P3-T1"],
    "summary": "Each retry is briefed with the single gap the last judgement named rather than repeating the "
               "original brief. After the stated number of attempts a unit is marked blocked with its blocker and "
               "chosen workaround recorded, and the run continues with the next ready unit; blocked units are "
               "re-evaluated each iteration.",
    "tdd": {"red": "Tests assert a persistently failing unit becomes blocked without stalling the run, that a "
                   "retry's brief carries the named gap, and that a unit blocked on a dependency becomes eligible "
                   "when that dependency passes; all fail initially.",
            "green": "Implement the retry bound, the gap-carrying brief and re-evaluation.",
            "refactor": "Report blockers in the run summary grouped by cause."},
    "traces": {"fr": ["FR-EXE-07"], "nfr": ["NFR-EXE-05"], "us": ["US-EXE-04"]},
    "criteria": [{"id": "M11-P3-T2-C1", "kind": "auto", "text": "A failing unit blocks rather than stalling the "
                                                                "run.", "done": False},
                 {"id": "M11-P3-T2-C2", "kind": "auto", "text": "A blocked unit becomes eligible when its "
                                                                "dependency passes.", "done": False}]},
   {"id": "M11-P3-T3", "title": "Ledger-backed resume", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["e2e"], "dependsOn": ["M11-P3-T2"],
    "summary": "The ledger records done-state, decisions and the exact next step before the orchestrator "
               "advances; on resume it is read first and the ready set is recomputed from the plan.",
    "tdd": {"red": "A test kills a run mid-wave, restarts it, and asserts no unit is repeated or skipped and that "
                   "the ledger already recorded the next step; it fails initially.",
            "green": "Write the ledger before advancing and read it first on start.",
            "refactor": "Prefer the plan where the two disagree, and record the discrepancy."},
    "traces": {"fr": ["FR-EXE-09", "FR-LRN-05"], "nfr": ["NFR-EXE-07", "NFR-EXE-01"], "adr": ["ADR-15"],
               "us": ["US-EXE-03"]},
    "criteria": [{"id": "M11-P3-T3-C1", "kind": "auto", "text": "A restarted run repeats no completed unit.",
                  "done": False},
                 {"id": "M11-P3-T3-C2", "kind": "auto", "text": "The ledger records the next step before the run "
                                                                "advances.", "done": False},
                 {"id": "M11-P3-T3-C3", "kind": "auto", "text": "A plan-versus-ledger discrepancy is recorded, not "
                                                                "silently resolved.", "done": False}]}]}],

"M12": [
 {"id": "M12-P1", "title": "Compounding memory", "dependsOn": [],
  "summary": "Retrospectives written at every milestone close, read by every later worker, and distilled into a "
             "conventions summary.",
  "completion": ["A milestone cannot close without a retrospective.",
                 "Later briefs require reading all prior retrospectives.",
                 "A theme recurring three times is escalated."],
  "tasks": [
   {"id": "M12-P1-T1", "title": "Retrospective at milestone close", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Closing a milestone writes what was learned, what surprised the run, and what the next milestone "
               "should do differently — including every autonomous decision recorded during the milestone.",
    "tdd": {"red": "A test asserts a milestone cannot be marked closed without a retrospective containing the "
                   "recorded decisions; it fails initially.",
            "green": "Require the retrospective as a closure criterion.",
            "refactor": "Seed the retrospective from the milestone's worker reports and decision log."},
    "traces": {"fr": ["FR-LRN-01"], "adr": ["ADR-14"], "us": ["US-LRN-01"]},
    "criteria": [{"id": "M12-P1-T1-C1", "kind": "auto", "text": "A milestone cannot close without a "
                                                                "retrospective.", "done": False},
                 {"id": "M12-P1-T1-C2", "kind": "auto", "text": "Recorded decisions appear in the retrospective.",
                  "done": False}]},
   {"id": "M12-P1-T2", "title": "Prior retrospectives are required reading", "priority": "Must", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["unit"], "dependsOn": ["M12-P1-T1"],
    "summary": "Every brief for a later milestone requires reading all prior retrospectives before writing code, "
               "and carries the distilled conventions summary.",
    "tdd": {"red": "A test asserts a later brief references every prior retrospective and includes the "
                   "conventions summary; it fails initially.",
            "green": "Assemble both into the brief.",
            "refactor": "Distil the summary automatically from repeated retrospective themes."},
    "traces": {"fr": ["FR-LRN-02", "FR-LRN-03"], "adr": ["ADR-14"], "us": ["US-LRN-01"]},
    "criteria": [{"id": "M12-P1-T2-C1", "kind": "auto", "text": "A later brief references every prior "
                                                                "retrospective.", "done": False},
                 {"id": "M12-P1-T2-C2", "kind": "auto", "text": "The conventions summary is present in the brief.",
                  "done": False}]},
   {"id": "M12-P1-T3", "title": "Recurring-theme escalation", "priority": "Should", "autonomy": "auto",
    "layer": "orchestration", "testLayers": ["unit", "manual"], "dependsOn": ["M12-P1-T2"],
    "summary": "A theme appearing in three or more retrospectives is surfaced as a candidate change to the method "
               "itself, not merely to the next milestone.",
    "tdd": {"red": "A test seeds a theme across three retrospectives and asserts it is surfaced for escalation; "
                   "it fails initially.",
            "green": "Detect repetition and report candidates.",
            "refactor": "Record accepted escalations as versioned method changes."},
    "traces": {"fr": ["FR-LRN-04"], "nfr": ["NFR-EVO-04"], "us": ["US-LRN-01"]},
    "criteria": [{"id": "M12-P1-T3-C1", "kind": "auto", "text": "A theme repeated three times is surfaced.",
                  "done": False},
                 {"id": "M12-P1-T3-C2", "kind": "human-review", "text": "The owner decides whether the escalation "
                                                                        "becomes a method change.", "done": False}]}]},

 {"id": "M12-P2", "title": "Amendment", "dependsOn": ["M12-P1"],
  "summary": "Extend a shipped specification by addendum, annotate superseded requirements in place, and "
             "re-derive the plan so new scope cannot sit unclaimed.",
  "completion": ["New scope is added without disturbing any existing identifier.",
                 "Amendment annotations survive regeneration.",
                 "Re-derivation runs the coverage gate again."],
  "tasks": [
   {"id": "M12-P2-T1", "title": "Addendum authoring", "priority": "Must", "autonomy": "auto", "layer": "generator",
    "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Author new scope as a document with its own identifier prefix rather than by editing or "
               "renumbering the original.",
    "tdd": {"red": "A test adds an addendum and asserts every original identifier still resolves and no original "
                   "file changed; it fails while extension edits the original.",
            "green": "Implement addendum authoring with prefix registration.",
            "refactor": "Reuse the same generators, differing only in prefix and companion links."},
    "traces": {"fr": ["FR-AMD-01"], "adr": ["ADR-12", "ADR-03"], "us": ["US-AMD-01"]},
    "criteria": [{"id": "M12-P2-T1-C1", "kind": "auto", "text": "No original identifier changes when an addendum "
                                                                "is added.", "done": False},
                 {"id": "M12-P2-T1-C2", "kind": "auto", "text": "The addendum prefix is registered for routing.",
                  "done": False}]},
   {"id": "M12-P2-T2", "title": "In-place amendment annotations", "priority": "Should", "autonomy": "auto",
    "layer": "generator", "testLayers": ["unit"], "dependsOn": ["M12-P2-T1"],
    "summary": "Where a later decision changes an earlier requirement, annotate the original in place with the "
               "amendment and its date, and preserve that annotation through every regeneration.",
    "tdd": {"red": "A test annotates a requirement, regenerates, and asserts the annotation and date survive; it "
                   "fails while regeneration overwrites.",
            "green": "Carry annotations in the specification object.",
            "refactor": "Render annotations distinctly from the original text."},
    "traces": {"fr": ["FR-AMD-04"], "nfr": ["NFR-EVO-05"], "us": ["US-AMD-01"]},
    "criteria": [{"id": "M12-P2-T2-C1", "kind": "auto", "text": "An annotation survives regeneration.",
                  "done": False},
                 {"id": "M12-P2-T2-C2", "kind": "auto", "text": "The annotation carries its date.", "done": False}]},
   {"id": "M12-P2-T3", "title": "Re-derivation after amendment", "priority": "Must", "autonomy": "auto",
    "layer": "ops", "testLayers": ["CI"], "dependsOn": ["M12-P2-T2"],
    "summary": "Any specification amendment triggers regeneration and the coverage gate, so a newly added "
               "requirement cannot sit unclaimed.",
    "tdd": {"red": "A test amends a specification without touching plan data and asserts the pipeline fails on "
                   "coverage; it fails while amendment is unwatched.",
            "green": "Trigger regeneration and the gate on any specification change.",
            "refactor": "Report which identifiers are newly unclaimed rather than the whole matrix."},
    "traces": {"fr": ["FR-AMD-05"], "nfr": ["NFR-OPS-02"], "us": ["US-AMD-01", "US-TRC-01"]},
    "criteria": [{"id": "M12-P2-T3-C1", "kind": "auto", "text": "An unclaimed new requirement fails the "
                                                                "pipeline.", "done": False}]}]},

 {"id": "M12-P3", "title": "Packaging, briefing and self-hosting", "dependsOn": ["M12-P2"],
  "summary": "Ship the method: the narrative briefing output, the documented exclusions, the adoption guidance, "
             "and the method's own documentation produced by the method.",
  "completion": ["The method's own document set is generated by the toolchain and passes every gate.",
                 "The adoption guide names the minimum viable subset.",
                 "Deliberate exclusions are recorded, not merely absent."],
  "tasks": [
   {"id": "M12-P3-T1", "title": "Narrative briefing generator", "priority": "Could", "autonomy": "auto",
    "layer": "generator", "testLayers": ["unit", "manual"], "dependsOn": [],
    "summary": "Emit a narrative briefing derived from the document set for readers who will not read the "
               "specifications, layered from plain language to technical depth.",
    "tdd": {"red": "A test asserts the briefing is derived from the set — changing a capability changes the "
                   "briefing — and that it contains no undefined jargon; it fails initially.",
            "green": "Implement the briefing generator over the existing specifications.",
            "refactor": "Share the plain-language check with the story generator."},
    "traces": {"fr": ["FR-DOC-09", "FR-GEN-05"], "nfr": ["NFR-UX-06"], "us": ["US-DOC-01"]},
    "criteria": [{"id": "M12-P3-T1-C1", "kind": "auto", "text": "The briefing changes when the specification "
                                                                "changes.", "done": False},
                 {"id": "M12-P3-T1-C2", "kind": "human-review", "text": "A non-specialist reader can follow the "
                                                                        "briefing unaided.", "done": False}]},
   {"id": "M12-P3-T2", "title": "Record the deliberate exclusions", "priority": "Must", "autonomy": "auto",
    "layer": "docs", "testLayers": ["unit"], "dependsOn": ["M12-P3-T1"],
    "summary": "Capture what the method deliberately does not do — hosted collaboration, external tracker "
               "synchronisation — as recorded exclusions so the decisions are not revisited by default.",
    "tdd": {"red": "A test asserts each exclusion is present with its reason and is absent from the coverage "
                   "universe; it fails initially.",
            "green": "Record the exclusions in the functional specification.",
            "refactor": "Render exclusions distinctly from live scope."},
    "traces": {"fr": ["FR-GEN-09", "FR-GEN-10"], "adr": ["ADR-17"], "us": ["US-TRC-01"]},
    "criteria": [{"id": "M12-P3-T2-C1", "kind": "auto", "text": "Each exclusion is recorded with its reason.",
                  "done": False},
                 {"id": "M12-P3-T2-C2", "kind": "auto", "text": "Exclusions are outside the coverage universe.",
                  "done": False}]},
   {"id": "M12-P3-T3", "title": "Self-hosting: the method documents itself", "priority": "Should",
    "autonomy": "auto", "layer": "docs", "testLayers": ["CI", "e2e"], "dependsOn": ["M12-P3-T2"],
    "summary": "Produce the method's own document set with the toolchain, so a defect in the toolchain is visible "
               "in its own artefacts, and run every gate against it.",
    "tdd": {"red": "A pipeline job regenerates the method's own document set and asserts every gate passes and no "
                   "file differs from what is committed; it fails until the toolchain is complete.",
            "green": "Author the method's own specifications and generate them.",
            "refactor": "Use the self-hosted set as the fixture for future regression tests."},
    "traces": {"fr": ["FR-GEN-08", "FR-GEN-07"], "nfr": ["NFR-GEN-01"], "adr": ["ADR-01"], "us": ["US-STA-03"]},
    "criteria": [{"id": "M12-P3-T3-C1", "kind": "auto", "text": "The method's own set regenerates with no file "
                                                                "difference.", "done": False},
                 {"id": "M12-P3-T3-C2", "kind": "auto", "text": "Every gate passes against the self-hosted set.",
                  "done": False}]},
   {"id": "M12-P3-T4", "title": "Adoption guidance and the minimum viable subset", "priority": "Should",
    "autonomy": "auto", "layer": "docs", "testLayers": ["manual"], "dependsOn": ["M12-P3-T3"],
    "summary": "State how to adopt the method in an existing project and which parts are the irreducible "
               "minimum, so partial adoption is a deliberate choice rather than an accident.",
    "tdd": {"red": "A review checklist asserts the guidance names the minimum subset and the order of adoption; "
                   "it fails while guidance is implicit.",
            "green": "Write the adoption guidance into the playbook.",
            "refactor": "Cross-reference each adoption step to the requirement it satisfies."},
    "traces": {"fr": ["FR-GEN-01"], "nfr": ["NFR-ARC-05", "NFR-PRF-04"], "us": ["US-GEN-01"]},
    "criteria": [{"id": "M12-P3-T4-C1", "kind": "human-review", "text": "A team new to the method can follow the "
                                                                        "adoption order unaided.", "done": False},
                 {"id": "M12-P3-T4-C2", "kind": "auto", "text": "The guidance names the minimum viable subset "
                                                                "explicitly.", "done": False}]}]}],

"M13": [
 {"id": "M13-P1", "title": "Skill entry points and chain rules", "dependsOn": [],
  "summary": "Wrap each toolchain step as a named skill, and enforce the two rules that make the chain safe to "
             "install anywhere: manual triggering only, and prerequisite-by-refusal.",
  "completion": ["Every chain step is invocable by name.",
                 "A skill invoked without its upstream document refuses, names what is missing, and changes "
                 "nothing.",
                 "A chain skill invoked in an uninitialised repository sets itself up and proceeds."],
  "tasks": [
   {"id": "M13-P1-T1", "title": "One named skill per chain step", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Define one skill per document type plus resume, build, update, ship and clarification, each a "
               "thin named wrapper over the finished toolchain step it operates.",
    "tdd": {"red": "A test enumerates the installed skill set and asserts one entry point exists per chain step "
                   "with the expected name; it fails while steps are loose scripts.",
            "green": "Author the skill definitions wrapping each toolchain step.",
            "refactor": "Extract the shared preamble — prerequisite probe, ledger location, report contract — "
                        "into one include every skill definition uses."},
    "traces": {"fr": ["FR-SKL-01"], "adr": ["ADR-18"], "us": ["US-SKL-01"]},
    "criteria": [{"id": "M13-P1-T1-C1", "kind": "auto", "text": "Each chain step is invocable by its documented "
                                                                "name.", "done": True}]},
   {"id": "M13-P1-T2", "title": "Prerequisite enforcement by refusal", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit", "e2e"], "dependsOn": ["M13-P1-T1"],
    "summary": "Each document-generating skill verifies its required upstream document exists and is complete "
               "before any work, with a read-only probe, and refuses by naming exactly what is missing.",
    "tdd": {"red": "A test invokes the functional-specification skill in a set with no product requirements and "
                   "asserts it refuses, names the missing document, and leaves the repository byte-identical; it "
                   "fails initially.",
            "green": "Implement the read-only prerequisite probe in the shared preamble.",
            "refactor": "Derive each skill's prerequisite list from the chain definition rather than repeating "
                        "it per skill."},
    "traces": {"fr": ["FR-SKL-02"], "nfr": ["NFR-SKL-02"], "us": ["US-SKL-01"]},
    "criteria": [{"id": "M13-P1-T2-C1", "kind": "auto", "text": "A refusal names the missing document and leaves "
                                                                "the repository untouched.", "done": True}]},
   {"id": "M13-P1-T3", "title": "Trigger policy in the definitions", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit", "manual"], "dependsOn": ["M13-P1-T1"],
    "summary": "Mark every chain skill manual-invocation only in its definition, and give the clarification "
               "skill — alone — explicit, tuned instructions for firing automatically whenever a decision would "
               "otherwise be guessed.",
    "tdd": {"red": "A test inspects every skill definition and asserts the manual-only marking on all chain "
                   "skills and the auto-trigger instructions on clarification only; it fails while policy is "
                   "documentation-only.",
            "green": "Set the trigger policy in each definition.",
            "refactor": "Add a definition-lint that fails the build when a new skill omits its trigger policy."},
    "traces": {"fr": ["FR-SKL-03", "FR-SKL-04"], "nfr": ["NFR-SKL-01"], "us": ["US-SKL-01", "US-SKL-02"]},
    "criteria": [{"id": "M13-P1-T3-C1", "kind": "auto", "text": "Every chain skill is marked manual-only in its "
                                                                "definition.", "done": True},
                 {"id": "M13-P1-T3-C2", "kind": "auto", "text": "Only the clarification skill carries "
                                                                "auto-trigger instructions.", "done": True}]},
   {"id": "M13-P1-T4", "title": "Init skill and automatic setup", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit", "integration", "e2e"], "dependsOn": ["M13-P1-T1"],
    "summary": "One init skill performs every setup mechanic — the .zero/ layout, ignore rules, theme "
               "detection, gauntlet recording — and every chain skill invokes it automatically, idempotently, "
               "when it finds setup missing, so no method step requires an operator shell command.",
    "tdd": {"red": "Tests invoke init in a bare fixture repository and assert the documented layout, ignore "
                   "rules and recorded gauntlet appear; invoke a chain skill in the same bare state and assert "
                   "init runs first and the skill proceeds; run init twice and assert the second run changes "
                   "no byte. All fail with no init skill.",
            "green": "Implement the init skill and the setup probe in the shared preamble every chain skill "
                     "already uses.",
            "refactor": "Derive the layout and ignore rules from one definition shared with the repository-"
                        "layout documentation, so the two can never drift."},
    "traces": {"fr": ["FR-SKL-09"], "nfr": ["NFR-SKL-04"], "us": ["US-SKL-07"]},
    "criteria": [{"id": "M13-P1-T4-C1", "kind": "auto", "text": "Init creates the documented layout, ignore "
                                                                "rules and gauntlet record in a bare "
                                                                "repository.", "done": True},
                 {"id": "M13-P1-T4-C2", "kind": "auto", "text": "A chain skill invoked without setup runs init "
                                                                "first and proceeds; a second init run changes "
                                                                "nothing.", "done": True}]}]},

 {"id": "M13-P2", "title": "Resume, update and ship", "dependsOn": ["M13-P1"],
  "summary": "The three operating skills around the chain: continue from wherever the set stands, fold changes "
             "in forward-only, and ship the working branch deliberately.",
  "completion": ["Resume continues correctly from every partially complete set.",
                 "An update never deletes or overwrites published content.",
                 "Ship commits and pushes, then asks before opening a pull request."],
  "tasks": [
   {"id": "M13-P2-T1", "title": "Resume skill", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Inspect the document set, determine the furthest completed step, and continue by invoking the "
               "next skill in the chain — from the beginning when no completed vision exists.",
    "tdd": {"red": "Tests present sets stopped at each chain position — including empty — and assert resume "
                   "reports the position and invokes the correct next skill; they fail with no resume logic.",
            "green": "Implement set inspection over the chain definition and dispatch to the next step.",
            "refactor": "Reuse the same completeness probe the prerequisite check uses, so the two can never "
                        "disagree."},
    "traces": {"fr": ["FR-SKL-05"], "us": ["US-SKL-03"]},
    "criteria": [{"id": "M13-P2-T1-C1", "kind": "auto", "text": "Resume continues correctly from every chain "
                                                                "position, including an empty set.",
                  "done": True}]},
   {"id": "M13-P2-T2", "title": "Forward-only update skill", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit", "integration"], "dependsOn": [],
    "summary": "Fold additions and changes into existing documents forward only — amend in place with a date, "
               "append, or retire with a successor pointer — never delete or overwrite published content.",
    "tdd": {"red": "A test applies a change to a published entry and asserts the original survives with its "
                   "amendment and date, and a deletion request is converted to retire-in-place; it fails "
                   "initially.",
            "green": "Implement the amendment paths over the embedded specification.",
            "refactor": "Share the amendment writer with the addendum machinery."},
    "traces": {"fr": ["FR-SKL-06"], "us": ["US-SKL-04"]},
    "criteria": [{"id": "M13-P2-T2-C1", "kind": "auto", "text": "No update path deletes or overwrites published "
                                                                "content.", "done": True}]},
   {"id": "M13-P2-T3", "title": "Ship skill", "priority": "Should", "autonomy": "auto-with-mock",
    "status": "passing", "layer": "orchestration", "testLayers": ["e2e"], "dependsOn": [],
    "summary": "Commit all changes on the current working branch, push it, and ask — never assume — whether to "
               "open a pull request to the upstream branch.",
    "tdd": {"red": "Against a fixture repository, a test asserts ship commits and pushes the working branch and "
                   "stops at the pull-request question, creating one only on an explicit yes; it fails "
                   "initially.",
            "green": "Implement commit, push and the gated pull-request offer.",
            "refactor": "Route branch and remote names through the chain configuration rather than assuming "
                        "them."},
    "traces": {"fr": ["FR-SKL-07"], "us": ["US-SKL-05"]},
    "criteria": [{"id": "M13-P2-T3-C1", "kind": "auto", "text": "A pull request is created only on an explicit "
                                                                "yes.", "done": True}]}]},

 {"id": "M13-P3", "title": "Plugin packaging", "dependsOn": ["M13-P1", "M13-P2"],
  "summary": "One installable, version-pinned plugin carrying the whole chain.",
  "completion": ["A single marketplace install yields every skill at its pinned version."],
  "tasks": [
   {"id": "M13-P3-T1", "title": "Version-pinned plugin manifest", "priority": "Should", "autonomy": "auto",
    "status": "passing", "layer": "ops", "testLayers": ["integration", "CI"], "dependsOn": [],
    "summary": "Package every skill into one plugin with pinned versions, so the same marketplace reference "
               "always resolves to the same skill set.",
    "tdd": {"red": "A test builds the plugin and asserts every chain skill is present with an explicit version "
                   "pin, and that two builds from the same source are identical; it fails with no manifest.",
            "green": "Author the manifest and the packaging step.",
            "refactor": "Generate the manifest's skill list from the chain definition."},
    "traces": {"fr": ["FR-SKL-08"], "nfr": ["NFR-SKL-03"], "adr": ["ADR-18"], "us": ["US-SKL-06"]},
    "criteria": [{"id": "M13-P3-T1-C1", "kind": "auto", "text": "Two builds from the same source produce an "
                                                                "identical plugin.", "done": True},
                 {"id": "M13-P3-T1-C2", "kind": "auto", "text": "Every chain skill is present and version-"
                                                                "pinned.", "done": True}]},
   {"id": "M13-P3-T2", "title": "Install verification", "priority": "Should", "autonomy": "auto-with-mock",
    "status": "passing", "layer": "ops", "testLayers": ["e2e", "manual"], "dependsOn": ["M13-P3-T1"],
    "summary": "Verify that one install action from the marketplace reference yields the complete working chain "
               "on a clean machine.",
    "tdd": {"red": "Against a clean fixture environment, a test installs from the marketplace reference and "
                   "asserts every skill is invocable and the chain's first step runs; it fails until packaging "
                   "works end to end.",
            "green": "Fix whatever the clean-machine install surfaces.",
            "refactor": "Add the install verification to the release pipeline so every plugin version is "
                        "install-tested before publication."},
    "traces": {"fr": ["FR-SKL-08"], "us": ["US-SKL-06"]},
    "criteria": [{"id": "M13-P3-T2-C1", "kind": "auto", "text": "A clean-machine install yields a working "
                                                                "chain.", "done": True},
                 {"id": "M13-P3-T2-C2", "kind": "human-review", "text": "The install instructions are exactly "
                                                                        "two commands.", "done": True}]}]}],
}
