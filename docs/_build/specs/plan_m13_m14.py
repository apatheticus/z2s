# -*- coding: utf-8 -*-
"""Zero-to-Ship plan detail — M13 and M14.

M13's detail moved here from `plan_m09_m12` when M14 arrived: it had been
sitting in a module whose name said it held M9 to M12, which is exactly the
kind of quiet untruth this method exists to stop. Nothing in it changed.
"""

DETAIL = {

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

"M14": [
 {"id": "M14-P1", "title": "One definition of the loop", "dependsOn": [],
  "summary": "Put the execution contract in one module and have both doors read it: the prompt written into a "
             "plan document, and the brief the orchestrator hands a worker.",
  "completion": ["The critic contract, the report contract and the block builder each exist in exactly one "
                 "place.",
                 "A prompt exists for the whole build, every milestone, every phase and every task.",
                 "The document prompt and the runner brief say the same thing about the same unit."],
  "tasks": [
   {"id": "M14-P1-T1", "title": "Gather the contract into one module", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Move the critic contract and its guard out of the orchestrator, and the block builder, the "
               "prompt builder and the report contract out of the plan generator, leaving named aliases so no "
               "existing caller changes.",
    "tdd": {"red": "A test asserts the orchestrator and the plan generator read their contract from one module; "
                    "it fails while each defines its own.",
            "green": "Move the definitions and leave aliases behind.",
            "refactor": "Run the whole suite before and after the move and prove the count is unchanged."},
    "traces": {"fr": ["FR-EXE-03"], "nfr": ["NFR-ARC-01"], "us": ["US-EXE-01"]},
    "criteria": [{"id": "M14-P1-T1-C1", "kind": "auto", "text": "The critic contract is defined in exactly one "
                                                                "module.", "done": True},
                 {"id": "M14-P1-T1-C2", "kind": "auto", "text": "The move changed no behaviour: the suite reads "
                                                                "the same before and after.", "done": True}]},
   {"id": "M14-P1-T2", "title": "The loop, the higher target and the stops", "priority": "Must",
    "autonomy": "auto", "status": "passing", "layer": "generator", "testLayers": ["unit"],
    "dependsOn": ["M14-P1-T1"],
    "summary": "State the cycle, ask for a split the reader decides, derive the higher target from what the "
               "unit already traces to, and read the prohibited operations from the one place that defines "
               "them.",
    "tdd": {"red": "Tests assert a prompt asks for a reader-decided split, names what the unit traces to, says "
                    "plainly when it traces to nothing, and states no number of rounds; all fail initially.",
            "green": "Add the loop, the ceiling and the stops to the shared module.",
            "refactor": "Read the prohibitions from the safety module rather than restating them."},
    "traces": {"fr": ["FR-EXE-16"], "nfr": ["NFR-SEC-04"], "adr": ["ADR-13"], "us": ["US-EXE-09"]},
    "criteria": [{"id": "M14-P1-T2-C1", "kind": "auto", "text": "A unit that traces to nothing is told not to "
                                                                "invent a higher target.", "done": True},
                 {"id": "M14-P1-T2-C2", "kind": "auto", "text": "No prompt at any level states a number of "
                                                                "rounds.", "done": True},
                 {"id": "M14-P1-T2-C3", "kind": "auto", "text": "A rule added to the prohibited operations "
                                                                "reaches every prompt with no further edit.",
                  "done": True}]},
   {"id": "M14-P1-T3", "title": "Four levels, and what each waits on", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit"], "dependsOn": ["M14-P1-T2"],
    "summary": "Generate a prompt for the whole build, every milestone, every phase and every task, each one "
               "naming its own prerequisites before anything else.",
    "tdd": {"red": "A test asserts a prompt exists for a task, a phase, a milestone and the whole plan, and "
                    "that a dependency is named before the contract; it fails while only milestones have one.",
            "green": "Generate all four levels and carry them onto the units they belong to.",
            "refactor": "Derive a container's higher target from the units beneath it."},
    "traces": {"fr": ["FR-EXE-15", "FR-EXE-02"], "us": ["US-EXE-08"]},
    "criteria": [{"id": "M14-P1-T3-C1", "kind": "auto", "text": "Every task, phase and milestone of a generated "
                                                                "plan carries its own complete prompt.",
                  "done": True},
                 {"id": "M14-P1-T3-C2", "kind": "auto", "text": "A unit that waits on something names it before "
                                                                "the contract.", "done": True}]},
   {"id": "M14-P1-T4", "title": "The two doors say one thing", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit"], "dependsOn": ["M14-P1-T3"],
    "summary": "Have the orchestrator build its brief from the same module, and assert block by block that it "
               "matches the prompt the plan document carries for the same unit.",
    "tdd": {"red": "A test compares the document prompt and the runner brief for one unit and asserts every "
                    "block describing that unit is identical; it fails while only one is consulted.",
            "green": "Build the brief through the shared module.",
            "refactor": "Assert the only blocks the run adds are the ones only a run knows."},
    "traces": {"fr": ["FR-EXE-03", "FR-EXE-14"], "nfr": ["NFR-EXE-04"], "us": ["US-EXE-01", "US-EXE-09"]},
    "criteria": [{"id": "M14-P1-T4-C1", "kind": "auto", "text": "Every block describing the unit is the same "
                                                                "bytes in the document and in the brief.",
                  "done": True},
                 {"id": "M14-P1-T4-C2", "kind": "auto", "text": "A worker is told an independent judge, not it, "
                                                                "decides the unit.", "done": True}]},
   {"id": "M14-P1-T5", "title": "Print one unit's instructions", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit", "e2e"], "dependsOn": ["M14-P1-T3"],
    "summary": "One command that prints what the plan already carries for a named unit, so the text handed over "
               "is the text on the page rather than a second rendering of it.",
    "tdd": {"red": "A test asserts the command prints exactly what the document carries and refuses by name "
                    "with no plan; it fails before the command exists.",
            "green": "Read the prompt out of the plan documents and print it.",
            "refactor": "Accept the whole build under a name an operator would guess."},
    "traces": {"fr": ["FR-EXE-15", "FR-SKL-01"], "us": ["US-EXE-08"]},
    "criteria": [{"id": "M14-P1-T5-C1", "kind": "auto", "text": "The command prints the same bytes the document "
                                                                "carries.", "done": True},
                 {"id": "M14-P1-T5-C2", "kind": "auto", "text": "With no plan it refuses by name rather than "
                                                                "generating one.", "done": True}]}]},

 {"id": "M14-P2", "title": "On the page, and inside the budget", "dependsOn": ["M14-P1"],
  "summary": "Render every level's instructions on the card they belong to, and start measuring the document "
             "size budget that had been stated and never checked.",
  "completion": ["Every task, phase and milestone card offers its own instructions to copy.",
                 "Instructions are folded shut on load and dropped from print.",
                 "A document over the size budget is reported."],
  "tasks": [
   {"id": "M14-P2-T1", "title": "A fold on every card", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "runtime", "testLayers": ["unit", "e2e", "a11y"], "dependsOn": [],
    "summary": "Render a task's and a phase's instructions in the same markup the prompts section already used, "
               "so the stylesheet and the copy handler reach them with no new code.",
    "tdd": {"red": "A browser test asserts a task card's first element is a shut fold with a working copy "
                    "button; it fails while only the milestone has one.",
            "green": "Emit the existing prompt markup on the task and the phase.",
            "refactor": "Extract the markup so the section and the card cannot drift."},
    "traces": {"fr": ["FR-EXE-15", "FR-SPC-10"], "nfr": ["NFR-UX-04", "NFR-UX-05"], "us": ["US-EXE-08"]},
    "criteria": [{"id": "M14-P2-T1-C1", "kind": "auto", "text": "A task's instructions are the first element in "
                                                                "its card and are folded shut.", "done": True},
                 {"id": "M14-P2-T1-C2", "kind": "auto", "text": "Every level's copy button works and the "
                                                                "clipboard holds the prompt.", "done": True},
                 {"id": "M14-P2-T1-C3", "kind": "auto", "text": "A word only a prompt uses returns no entries, "
                                                                "so the keyword box still narrows.",
                  "done": True}]},
   {"id": "M14-P2-T2", "title": "Measure the size budget", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "validator", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Fold the document size measurement into the pipeline's budgets gate, where every other check "
               "already reads the produced files, and raise the figure to one this method's own output fits.",
    "tdd": {"red": "A test puts an oversized document through the gate and asserts it is reported; it fails "
                    "while the measurement exists but nothing calls it.",
            "green": "Measure each source in the budgets stage and report a warning.",
            "refactor": "Round the overage up so a small excess never reports as zero."},
    # No trace to TG-06, the target row this measures: docs/_build/coverage.py
    # knows only requirements and decisions, so a target identifier reads as
    # dangling there. The toolchain's own trace engine does accept one (M6-02).
    "traces": {"fr": ["FR-GEN-03"], "nfr": ["NFR-PRF-02"], "us": ["US-VAL-01"]},
    "criteria": [{"id": "M14-P2-T2-C1", "kind": "auto", "text": "A document over the budget is reported by the "
                                                                "pipeline.", "done": True},
                 {"id": "M14-P2-T2-C2", "kind": "auto", "text": "The budget is not readable from a project's "
                                                                "configuration.", "done": True}]}]},

 {"id": "M14-P3", "title": "The skill, and the published set", "dependsOn": ["M14-P2"],
  "summary": "Give an operator a named way to ask for one unit's instructions, and put the new promises and the "
             "raised budget into the published specification.",
  "completion": ["The chain ships a skill that prints one unit's instructions and nothing else.",
                 "The published specification states both new promises and they are claimed by work.",
                 "The published plan and playbook show the four granularities."],
  "tasks": [
   {"id": "M14-P3-T1", "title": "A named way to ask for one unit", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "orchestration", "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Add the skill to the chain definition so the published table, the lock and the plugin all "
               "follow from one place, and prove the command runs from a foreign install.",
    "tdd": {"red": "A test asserts the chain lists the new step and the lock pins it; it fails before the "
                    "definition exists.",
            "green": "Add the step and author the skill definition.",
            "refactor": "Prove the command from a copy with nothing but the plugin on the path."},
    "traces": {"fr": ["FR-SKL-01", "FR-SKL-08"], "nfr": ["NFR-SKL-04"], "us": ["US-SKL-01"]},
    "criteria": [{"id": "M14-P3-T1-C1", "kind": "auto", "text": "The lock pins every skill the chain declares, "
                                                                "with no manifest to remember.", "done": True},
                 {"id": "M14-P3-T1-C2", "kind": "auto", "text": "The command runs from a foreign install with "
                                                                "nothing but the plugin on the path.",
                  "done": True}]},
   {"id": "M14-P3-T2", "title": "Say it in the published set", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "spec", "testLayers": ["unit", "CI"], "dependsOn": ["M14-P3-T1"],
    "summary": "State both new promises as requirements with stories behind them, claim them with this "
               "milestone, correct the size target, and show the four granularities on the published plan.",
    "tdd": {"red": "Generation fails while a new requirement is claimed by no unit of work, which is the "
                    "coverage gate doing its job.",
            "green": "Write the requirements, the stories and this milestone's claims.",
            "refactor": "Show a real prompt on the published plan rather than describing one."},
    "traces": {"fr": ["FR-EXE-15", "FR-EXE-16", "FR-TRC-01"], "nfr": ["NFR-PRF-02"], "us": ["US-EXE-08"]},
    "criteria": [{"id": "M14-P3-T2-C1", "kind": "auto", "text": "Every new requirement is claimed by a unit of "
                                                                "work.", "done": True},
                 {"id": "M14-P3-T2-C2", "kind": "auto", "text": "The published plan shows a real prompt at each "
                                                                "of the four levels.", "done": True},
                 {"id": "M14-P3-T2-C3", "kind": "human-review", "text": "An operator can tell at a glance which "
                                                                        "prompt to copy for the amount of work "
                                                                        "they mean to hand over.",
                  "done": True}]}]}],
}
