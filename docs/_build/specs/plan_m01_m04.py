# -*- coding: utf-8 -*-
"""Zero-to-Ship plan detail — M1 to M4."""

DETAIL = {

"M1": [
 {"id": "M1-P1", "title": "Repository layout and generation harness", "dependsOn": [],
  "summary": "The directory contract every later tool depends on, and the smallest generator that can turn a "
             "specification object into a file.",
  "completion": ["The layout exists and is documented.",
                 "A hand-written specification object renders to a file that opens in a browser.",
                 "Regenerating unchanged input changes no bytes."],
  "tasks": [
   {"id": "M1-P1-T1", "title": "Repository layout and ignore policy", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "foundation", "testLayers": ["unit", "CI"], "dependsOn": [],
    "summary": "Create the documented locations for specifications, plan data, generated plans, retrospectives "
               "and the run ledger, with the ledger excluded from version control and generated plan documents "
               "deliberately included.",
    "tdd": {"red": "A layout test asserts each documented path exists and that the ledger directory is ignored "
                   "while the generated plan directory is tracked; it fails against an empty repository.",
            "green": "Create the directories, the ignore rules and the generated-file markers.",
            "refactor": "Express the layout as one constant the tests and generators both read, so a path is "
                        "never spelled twice."},
    "traces": {"fr": ["FR-GEN-01"], "nfr": ["NFR-OPS-01", "NFR-OPS-04"], "adr": ["ADR-11"], "us": ["US-STA-03"]},
    "criteria": [{"id": "M1-P1-T1-C1", "kind": "auto", "text": "Every documented path exists.", "done": True},
                 {"id": "M1-P1-T1-C2", "kind": "auto", "text": "The ledger path is ignored; the generated plan "
                                                               "path is tracked.", "done": True}]},
   {"id": "M1-P1-T2", "title": "Minimal generator: specification object to file", "priority": "Must",
    "status": "passing", "autonomy": "auto", "layer": "generator", "testLayers": ["unit"], "dependsOn": ["M1-P1-T1"],
    "summary": "A function that takes a specification object and an element identifier and emits a complete "
               "document with the object embedded and the shared shell inlined.",
    "tdd": {"red": "A test generates a file from a two-field specification and asserts the file contains a "
                   "parseable JSON block under the expected identifier; it fails because no generator exists.",
            "green": "Implement the generator: read the shell, inject tokens, structure, runtime and the "
                     "serialised object.",
            "refactor": "Split shell assembly from serialisation so either can be tested alone."},
    "traces": {"fr": ["FR-SPC-01", "FR-SPC-03"], "nfr": ["NFR-ARC-03"], "adr": ["ADR-01"], "us": ["US-SPC-01"]},
    "criteria": [{"id": "M1-P1-T2-C1", "kind": "auto", "text": "The emitted file contains exactly one embedded "
                                                               "specification block.", "done": True},
                 {"id": "M1-P1-T2-C2", "kind": "auto", "text": "The block parses as a single JSON object.",
                  "done": True}]},
   {"id": "M1-P1-T3", "title": "Deterministic, atomic writes", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit"], "dependsOn": ["M1-P1-T2"],
    "summary": "Generation must produce identical bytes from identical inputs, must not consult the clock or a "
               "random source, and must leave the previous file untouched when it fails.",
    "tdd": {"red": "A test generates twice and compares bytes, and a second test makes serialisation raise "
                   "mid-write and asserts the original file is unchanged; both fail initially.",
            "green": "Sort keys, fix indentation, remove every clock and random-source read, and write via a "
                     "temporary file renamed into place.",
            "refactor": "Centralise the write helper so no generator writes a file directly."},
    "traces": {"fr": ["FR-GEN-07"], "nfr": ["NFR-GEN-01", "NFR-GEN-02"], "us": ["US-STA-03"]},
    "criteria": [{"id": "M1-P1-T3-C1", "kind": "auto", "text": "Two consecutive generations produce identical "
                                                               "bytes.", "done": True},
                 {"id": "M1-P1-T3-C2", "kind": "auto", "text": "A failed generation leaves the previous file "
                                                               "byte-identical.", "done": True}]}]},

 {"id": "M1-P2", "title": "Document runtime and section renderers", "dependsOn": ["M1-P1"],
  "summary": "The browser-side runtime that builds the readable document from the embedded specification, with a "
             "renderer per section type and safe behaviour for anything it does not recognise.",
  "completion": ["Every section type renders from data alone.",
                 "An unknown section type produces a placeholder and does not stop the page.",
                 "All authored content is escaped; only the constrained inline markup expands."],
  "tasks": [
   {"id": "M1-P2-T1", "title": "Render the document from its embedded specification", "priority": "Must",
    "status": "passing", "autonomy": "auto", "layer": "runtime", "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "The runtime reads the embedded object at load time and constructs the hero, the sections and the "
               "contents list. No fact exists in the file outside that object.",
    "tdd": {"red": "An end-to-end test loads a generated file, edits the embedded object's title, reloads, and "
                   "asserts the visible title changed; it fails while markup is static.",
            "green": "Implement the render pass: envelope to hero, section list to sections, section list to "
                     "contents.",
            "refactor": "Extract a renderer registry keyed by section type so adding a type is additive."},
    "traces": {"fr": ["FR-SPC-02"], "nfr": ["NFR-DAT-01"], "adr": ["ADR-02"], "us": ["US-SPC-01"]},
    "criteria": [{"id": "M1-P2-T1-C1", "kind": "auto", "text": "Changing a value in the embedded object changes "
                                                               "the rendered view.", "done": True},
                 {"id": "M1-P2-T1-C2", "kind": "auto", "text": "No content string appears in the file outside the "
                                                               "embedded object.", "done": True}]},
   {"id": "M1-P2-T2", "title": "Section-type registry with graceful degradation", "priority": "Must",
    "status": "passing", "autonomy": "auto", "layer": "runtime", "testLayers": ["unit"], "dependsOn": ["M1-P2-T1"],
    "summary": "Renderers for prose, lists, definitions, tables, cards, statistics, flows and code, plus an "
               "explicit placeholder for any type the runtime does not know.",
    "tdd": {"red": "A test renders a specification containing an invented section type and asserts a placeholder "
                   "appears and later sections still render; it fails because the runtime throws.",
            "green": "Add the registry lookup with a fallback renderer.",
            "refactor": "Give every renderer the same signature so the registry needs no special cases."},
    "traces": {"fr": ["FR-SPC-02"], "nfr": ["NFR-GEN-04", "NFR-EVO-02"], "us": ["US-SPC-01"]},
    "criteria": [{"id": "M1-P2-T2-C1", "kind": "auto", "text": "An unknown section type renders a placeholder and "
                                                               "does not halt rendering.", "done": True}]},
   {"id": "M1-P2-T3", "title": "Escaping and constrained inline markup", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "runtime", "testLayers": ["unit"], "dependsOn": ["M1-P2-T1"],
    "summary": "All authored strings are escaped before insertion; only bold, inline code and links expand, and "
               "nothing else in authored prose is treated as markup.",
    "tdd": {"red": "A test renders content containing angle brackets and a script fragment and asserts it appears "
                   "as literal text; it fails while content is inserted raw.",
            "green": "Escape first, then expand exactly the three permitted inline forms.",
            "refactor": "Make the expansion table data so the permitted set is visible in one place."},
    "traces": {"fr": ["FR-SPC-02"], "nfr": ["NFR-GEN-05", "NFR-DAT-07"]},
    "criteria": [{"id": "M1-P2-T3-C1", "kind": "auto", "text": "Authored markup is rendered as literal text.",
                  "done": True},
                 {"id": "M1-P2-T3-C2", "kind": "auto", "text": "Only bold, inline code and links expand.",
                  "done": True}]},
   {"id": "M1-P2-T4", "title": "Contents list, derived numbering and scroll tracking", "priority": "Should",
    "status": "passing", "autonomy": "auto", "layer": "runtime", "testLayers": ["e2e", "a11y"], "dependsOn": ["M1-P2-T2"],
    "summary": "A contents list built from document order, with numbers computed rather than authored, and the "
               "current section highlighted as the reader scrolls.",
    "tdd": {"red": "A test inserts a section into the middle of a specification and asserts numbering stays "
                   "contiguous and the contents list order matches; it fails against authored numbers.",
            "green": "Compute numbers at render time and observe section visibility to set the active entry.",
            "refactor": "Share one ordering pass between the sections and the contents list."},
    "traces": {"fr": ["FR-SPC-09"], "nfr": ["NFR-GEN-06"], "us": ["US-SPC-02"]},
    "criteria": [{"id": "M1-P2-T4-C1", "kind": "auto", "text": "Numbering is contiguous after inserting a "
                                                               "section.", "done": True},
                 {"id": "M1-P2-T4-C2", "kind": "auto", "text": "The contents entry for the section in view is "
                                                               "marked active.", "done": True}]}]},

 {"id": "M1-P3", "title": "Design-system adoption, accessibility and size", "dependsOn": ["M1-P2"],
  "summary": "Adopt the host project's tokens into the marked style block, fall back to a neutral theme, and hold "
             "the accessibility and size floors.",
  "completion": ["Token-only styling is enforced by a check, not by convention.",
                 "Keyboard, contrast and reduced-motion checks pass.",
                 "A generated document stays inside the size budget."],
  "tasks": [
   {"id": "M1-P3-T1", "title": "Token adoption with neutral fallback", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "lint"], "dependsOn": [],
    "summary": "Detect the host project's design tokens, map them onto the documented token contract, inline them "
               "into the marked style block, and use the neutral theme when no system is found — saying so.",
    "tdd": {"red": "A test generates against a fixture project declaring tokens and asserts those values appear "
                   "in the style block, and a second asserts the neutral theme plus a stated fallback when none "
                   "exists; both fail initially.",
            "green": "Implement detection, mapping and the marked style-block swap.",
            "refactor": "Publish the token contract as one file both the fallback and the mapper satisfy."},
    "traces": {"fr": ["FR-GEN-02"], "nfr": ["NFR-GEN-03", "NFR-ARC-04"], "adr": ["ADR-16"], "us": ["US-GEN-01"]},
    "criteria": [{"id": "M1-P3-T1-C1", "kind": "auto", "text": "Host tokens appear in the generated style block.",
                  "done": True},
                 {"id": "M1-P3-T1-C2", "kind": "auto", "text": "With no host system, the neutral theme is used and "
                                                               "the run reports the fallback.", "done": True},
                 {"id": "M1-P3-T1-C3", "kind": "auto", "text": "No colour, font or shadow literal exists outside "
                                                               "the token block.", "done": True}]},
   {"id": "M1-P3-T2", "title": "Accessibility floor", "priority": "Must", "autonomy": "auto", "layer": "runtime",
    "status": "passing", "testLayers": ["a11y", "e2e"], "dependsOn": ["M1-P3-T1"],
    "summary": "Every control reachable and operable by keyboard with a visible focus indicator, contrast at the "
               "host project's target, status never conveyed by colour alone, and all motion suppressed under a "
               "reduced-motion preference.",
    "tdd": {"red": "An automated accessibility pass over the specimen document reports focus, contrast and "
                   "colour-only violations; a second test asserts no animation runs under reduced motion.",
            "green": "Add focus styling, correct contrast pairs, textual status labels and the motion query.",
            "refactor": "Move the focus and motion rules into the shared structural styling so no document opts "
                        "out."},
    "traces": {"fr": ["FR-GEN-06"], "nfr": ["NFR-UX-01", "NFR-UX-02", "NFR-UX-03"], "us": ["US-GEN-01"]},
    "criteria": [{"id": "M1-P3-T2-C1", "kind": "auto", "text": "The accessibility pass reports no violation.",
                  "done": True},
                 {"id": "M1-P3-T2-C2", "kind": "auto", "text": "No animation plays under a reduced-motion "
                                                               "preference.", "done": True},
                 {"id": "M1-P3-T2-C3", "kind": "human-review", "text": "A reviewer confirms the document is "
                                                                       "comfortable to read at a phone width.",
                  "done": True}]},
   {"id": "M1-P3-T3", "title": "Responsive layout, print output and size budget", "priority": "Should",
    "status": "passing", "autonomy": "auto", "layer": "runtime", "testLayers": ["e2e", "perf"], "dependsOn": ["M1-P3-T2"],
    "summary": "Usable from a narrow phone viewport to a wide desktop with no horizontal scrolling of body "
               "content; printing expands collapsed content and suppresses chrome; the file stays inside budget.",
    "tdd": {"red": "Tests assert no horizontal overflow at a narrow viewport, that collapsed groups are expanded "
                   "in print styling, and that the specimen file is under the size budget; all fail initially.",
            "green": "Add the responsive breakpoints, the print rules and a size assertion in the build.",
            "refactor": "Express the size budget as a named constant shared by the test and the build report."},
    "traces": {"fr": ["FR-SPC-11"], "nfr": ["NFR-UX-05", "NFR-PRF-02"]},
    "criteria": [{"id": "M1-P3-T3-C1", "kind": "auto", "text": "No horizontal overflow of body content at a "
                                                               "narrow viewport.", "done": True},
                 {"id": "M1-P3-T3-C2", "kind": "auto", "text": "Printed output expands collapsed content and hides "
                                                               "interactive chrome.", "done": True},
                 {"id": "M1-P3-T3-C3", "kind": "auto", "text": "The generated file is within the size budget.",
                  "done": True}]}]}],

"M2": [
 {"id": "M2-P1", "title": "Document contracts", "dependsOn": [],
  "summary": "Publish the envelope, the catalogue-entry shape, the identifier grammar and the closed enumerations "
             "that every document type shares.",
  "completion": ["Every schema is published and versioned.",
                 "Enumerations are defined once and referenced by identifier everywhere else."],
  "tasks": [
   {"id": "M2-P1-T1", "title": "Document envelope and schema version", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "schema", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Define the envelope required in every specification object — title, slug, type, version, status, "
               "date, owner, scope — plus the schema version that lets a reader detect an incompatible document.",
    "tdd": {"red": "A test validates a specification missing its owner and asserts a named failure, and a second "
                   "asserts the schema version is required; both fail with no schema.",
            "green": "Publish the envelope schema and require it in every document type.",
            "refactor": "Compose type-specific schemas from the envelope rather than repeating it."},
    "traces": {"fr": ["FR-DOC-08", "FR-SPC-01"], "nfr": ["NFR-DAT-01", "NFR-DAT-02", "NFR-EVO-01"],
               "us": ["US-DOC-01"]},
    "criteria": [{"id": "M2-P1-T1-C1", "kind": "auto", "text": "A missing envelope field is reported by name.",
                  "done": True},
                 {"id": "M2-P1-T1-C2", "kind": "auto", "text": "Every document type carries a schema version.",
                  "done": True}]},
   {"id": "M2-P1-T2", "title": "Identifier grammar and closed enumerations", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "schema", "testLayers": ["unit"], "dependsOn": ["M2-P1-T1"],
    "summary": "Define the identifier patterns per document type and the closed sets for priority, status, "
               "criterion kind, autonomy class and verification layer, each declared once in a legend.",
    "tdd": {"red": "Tests assert that a malformed identifier and an out-of-set priority each fail validation with "
                   "a specific message; both fail initially.",
            "green": "Publish the patterns and the enumerations and enforce them.",
            "refactor": "Generate the human-readable legend from the same declaration the validator uses."},
    "traces": {"fr": ["FR-TRC-01"], "nfr": ["NFR-DAT-03", "NFR-DAT-04"], "adr": ["ADR-03"], "us": ["US-TRC-03"]},
    "criteria": [{"id": "M2-P1-T2-C1", "kind": "auto", "text": "A malformed identifier fails validation.",
                  "done": True},
                 {"id": "M2-P1-T2-C2", "kind": "auto", "text": "A value outside a closed enumeration fails "
                                                               "validation.", "done": True}]},
   {"id": "M2-P1-T3", "title": "Typed traces and omitted-not-empty sections", "priority": "Must",
    "status": "passing", "autonomy": "auto", "layer": "schema", "testLayers": ["unit"], "dependsOn": ["M2-P1-T2"],
    "summary": "Traces are a map keyed by upstream kind rather than a flat list, and any section with no content "
               "is absent from the object rather than present and empty.",
    "tdd": {"red": "A test asserts a flat trace list is rejected and that an empty section key is rejected; both "
                   "fail initially.",
            "green": "Require the typed trace map and forbid empty section containers.",
            "refactor": "Share one emptiness predicate between the schema and the renderer."},
    "traces": {"fr": ["FR-DOC-04", "FR-TRC-03"], "nfr": ["NFR-DAT-06", "NFR-DAT-08"], "us": ["US-TRC-02"]},
    "criteria": [{"id": "M2-P1-T3-C1", "kind": "auto", "text": "An untyped trace list is rejected.", "done": True},
                 {"id": "M2-P1-T3-C2", "kind": "auto", "text": "An empty optional section is rejected in the "
                                                               "object and omitted in the render.", "done": True}]}]},

 {"id": "M2-P2", "title": "Schema validator", "dependsOn": ["M2-P1"],
  "summary": "The command that validates any document against its type's schema, reports everything it finds in "
             "one pass, and exits non-zero.",
  "completion": ["Every violation in a set is reported in a single run.",
                 "Exit status is non-zero on failure and zero when only warnings exist."],
  "tasks": [
   {"id": "M2-P2-T1", "title": "Exhaustive single-pass validation", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "validator", "testLayers": ["unit"], "dependsOn": [],
    "summary": "Collect every violation across every document and report them grouped by document, rather than "
               "stopping at the first failure.",
    "tdd": {"red": "A test validates a fixture set containing three distinct violations and asserts all three are "
                   "reported in one run; it fails against a fail-fast validator.",
            "green": "Accumulate failures and report at the end.",
            "refactor": "Separate collection from formatting so the same results can be printed or returned."},
    "traces": {"fr": ["FR-VAL-01", "FR-VAL-05"], "nfr": ["NFR-VAL-01"], "us": ["US-VAL-01"]},
    "criteria": [{"id": "M2-P2-T1-C1", "kind": "auto", "text": "Three seeded violations produce three reported "
                                                               "failures in one run.", "done": True},
                 {"id": "M2-P2-T1-C2", "kind": "auto", "text": "Exit status is non-zero when any failure exists.",
                  "done": True}]},
   {"id": "M2-P2-T2", "title": "Duplicate and dangling identifier detection", "priority": "Must",
    "status": "passing", "autonomy": "auto", "layer": "validator", "testLayers": ["unit"], "dependsOn": ["M2-P2-T1"],
    "summary": "Fail on any duplicate identifier within the set, on any entry referencing an area that does not "
               "exist, and on any trace pointing at an identifier defined nowhere.",
    "tdd": {"red": "Tests seed a duplicate identifier, an unknown area and a dangling trace and assert three "
                   "distinct, correctly attributed failures; they fail initially.",
            "green": "Build the identifier index across the set and check membership.",
            "refactor": "Expose the index so later tools reuse it rather than rebuilding it."},
    "traces": {"fr": ["FR-TRC-02", "FR-TRC-08", "FR-VAL-03"], "us": ["US-TRC-02", "US-TRC-03"]},
    "criteria": [{"id": "M2-P2-T2-C1", "kind": "auto", "text": "A duplicate identifier is reported with both "
                                                               "locations.", "done": True},
                 {"id": "M2-P2-T2-C2", "kind": "auto", "text": "A dangling trace names the trace and its owner.",
                  "done": True}]},
   {"id": "M2-P2-T3", "title": "Warnings distinct from failures", "priority": "Should", "autonomy": "auto",
    "status": "passing", "layer": "validator", "testLayers": ["unit", "CI"], "dependsOn": ["M2-P2-T1"],
    "summary": "Advisory findings are reported as warnings that never change the exit status, and no failure can "
               "be downgraded to a warning by configuration.",
    "tdd": {"red": "A test asserts a warning-only run exits zero and that no flag downgrades a failure; it fails "
                   "while both share one channel.",
            "green": "Split the two channels and make severity a property of the rule, not of configuration.",
            "refactor": "Print a summary line stating counts of each severity."},
    "traces": {"fr": ["FR-VAL-06"], "nfr": ["NFR-VAL-06"], "us": ["US-VAL-01"]},
    "criteria": [{"id": "M2-P2-T3-C1", "kind": "auto", "text": "A warning-only run exits zero.", "done": True},
                 {"id": "M2-P2-T3-C2", "kind": "auto", "text": "No configuration downgrades a failure.",
                  "done": True}]},
   {"id": "M2-P2-T4", "title": "Specification extraction interface", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "validator", "testLayers": ["unit"], "dependsOn": ["M2-P2-T1"],
    "summary": "One shared function extracts a document's embedded specification from a rendered file, used by "
               "every validator and generator so extraction logic exists once.",
    "tdd": {"red": "A test extracts from a generated file and from a truncated one, expecting success and a named "
                   "parse failure; the second fails while extraction assumes well-formed input.",
            "green": "Implement extraction with an explicit failure for a missing or unparseable block.",
            "refactor": "Make every consumer use it; forbid direct parsing elsewhere."},
    "traces": {"fr": ["FR-SPC-04"], "nfr": ["NFR-DAT-02", "NFR-VAL-01"], "us": ["US-SPC-01"]},
    "criteria": [{"id": "M2-P2-T4-C1", "kind": "auto", "text": "Extraction returns the object for a valid file.",
                  "done": True},
                 {"id": "M2-P2-T4-C2", "kind": "auto", "text": "A truncated block produces a named failure, not "
                                                               "an exception trace.", "done": True}]}]},

 {"id": "M2-P3", "title": "Reader-local state and forward compatibility", "dependsOn": ["M2-P2"],
  "summary": "Namespaced review state that never enters the specification, and rendering that tolerates documents "
             "authored against an earlier minor schema.",
  "completion": ["Two documents in one browser do not share state.",
                 "An older document renders under a newer runtime without error."],
  "tasks": [
   {"id": "M2-P3-T1", "title": "Namespaced review state", "priority": "Should", "autonomy": "auto",
    "status": "passing", "layer": "runtime", "testLayers": ["e2e"], "dependsOn": [],
    "summary": "Review marks persist per document, keyed by method and document slug, and never appear in the "
               "specification object.",
    "tdd": {"red": "A test marks entries in one document, opens a second, and asserts the second shows no "
                   "progress and that the copied specification contains no review state; it fails with a shared "
                   "key.",
            "green": "Namespace the storage key and keep review state outside the object.",
            "refactor": "Read the namespace from the envelope so it cannot drift from the document identity."},
    "traces": {"fr": ["FR-SPC-08"], "nfr": ["NFR-GEN-07"], "us": ["US-SPC-04"]},
    "criteria": [{"id": "M2-P3-T1-C1", "kind": "auto", "text": "Two documents keep separate review state.",
                  "done": True},
                 {"id": "M2-P3-T1-C2", "kind": "auto", "text": "The copied specification contains no review "
                                                               "state.", "done": True}]},
   {"id": "M2-P3-T2", "title": "Backward-compatible rendering", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "runtime", "testLayers": ["unit"], "dependsOn": ["M2-P3-T1"],
    "summary": "A document authored against an earlier minor version of the schema renders without error under a "
               "later runtime.",
    "tdd": {"red": "A test renders a fixture authored against the previous minor version and asserts no error and "
                   "no missing section; it fails when the runtime assumes current fields.",
            "green": "Treat absent newer fields as optional and render what is present.",
            "refactor": "Record the compatibility rule beside the schema version so it is checked on every bump."},
    "traces": {"fr": ["FR-SPC-02"], "nfr": ["NFR-EVO-01", "NFR-EVO-02"]},
    "criteria": [{"id": "M2-P3-T2-C1", "kind": "auto", "text": "An earlier-minor-version document renders without "
                                                               "error.", "done": True}]}]}],

"M3": [
 {"id": "M3-P1", "title": "The decision gate", "dependsOn": [],
  "summary": "The shared gate every generator runs before authoring: identify forks, ask one at a time with a "
             "recommended default, and record the outcome durably.",
  "completion": ["No file is written before the gate completes.",
                 "The locked-decisions table exists in both the document and the ledger."],
  "tasks": [
   {"id": "M3-P1-T1", "title": "Fork detection and single gate phase", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Assess a source for unresolved forks and run exactly one gate phase before authoring, asking one "
               "question at a time, each with a recommended default.",
    "tdd": {"red": "A test runs a generator against a thin source and asserts no file is written until the gate "
                   "completes, and that each question offers a recommended default; it fails initially.",
            "green": "Implement the fork assessment and the gate phase ahead of authoring.",
            "refactor": "Share one gate implementation across all six generators."},
    "traces": {"fr": ["FR-DOC-02"], "adr": ["ADR-10"], "us": ["US-DOC-02"]},
    "criteria": [{"id": "M3-P1-T1-C1", "kind": "auto", "text": "No file is created before the gate completes.",
                  "done": True},
                 {"id": "M3-P1-T1-C2", "kind": "auto", "text": "Every question carries exactly one recommended "
                                                               "default.", "done": True}]},
   {"id": "M3-P1-T2", "title": "Locked-decisions record", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit"], "dependsOn": ["M3-P1-T1"],
    "summary": "Write the gate outcome as a decision, choice and rationale table into the document and the run "
               "ledger, and treat every row as closed thereafter.",
    "tdd": {"red": "A test asserts the table exists in both places before the first content section is authored, "
                   "and that a later stage encountering a locked fork applies the recorded choice without asking; "
                   "it fails initially.",
            "green": "Emit the table to both destinations and consult it before any question is asked.",
            "refactor": "Make the table the only source the generator consults for a resolved fork."},
    "traces": {"fr": ["FR-DOC-03", "FR-EXE-08"], "nfr": ["NFR-EXE-04"], "adr": ["ADR-10"], "us": ["US-DOC-02"]},
    "criteria": [{"id": "M3-P1-T2-C1", "kind": "auto", "text": "The table exists in the document and the ledger "
                                                               "before authoring.", "done": True},
                 {"id": "M3-P1-T2-C2", "kind": "auto", "text": "A locked fork is not re-asked.", "done": True}]},
   {"id": "M3-P1-T3", "title": "Skip the interview on a rich source", "priority": "Should", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit"], "dependsOn": ["M3-P1-T1"],
    "summary": "When the supplied material already answers every fork, proceed directly to authoring and record "
               "that the interview was skipped and why.",
    "tdd": {"red": "A test runs against a complete brief and asserts no questions are asked and the skip is "
                   "reported; it fails while the gate always interviews.",
            "green": "Assess sufficiency before interviewing.",
            "refactor": "Express sufficiency as a checklist against the canonical dimensions."},
    "traces": {"fr": ["FR-DOC-07"], "us": ["US-DOC-01"]},
    "criteria": [{"id": "M3-P1-T3-C1", "kind": "auto", "text": "A complete brief produces no questions.",
                  "done": True},
                 {"id": "M3-P1-T3-C2", "kind": "auto", "text": "The skip and its reason are reported.",
                  "done": True}]}]},

 {"id": "M3-P2", "title": "Vision generator", "dependsOn": ["M3-P1"],
  "summary": "The first document in the chain: problem, principles, stakeholders, personas, capabilities and "
             "scenarios, each capability identified so later documents can trace to it.",
  "completion": ["A vision document generated from a brief validates.",
                 "Capabilities carry identifiers that later documents can reference."],
  "tasks": [
   {"id": "M3-P2-T1", "title": "Vision schema and generator", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Publish the vision schema and the generator that produces a validating vision document, with "
               "identified capabilities that downstream documents trace to.",
    "tdd": {"red": "A test generates from a fixture brief and asserts the output validates and every capability "
                   "carries a unique identifier; it fails with no generator.",
            "green": "Implement the schema, the section list and the generator.",
            "refactor": "Reuse the shared envelope and gate rather than duplicating them."},
    "traces": {"fr": ["FR-DOC-01"], "nfr": ["NFR-ARC-01"], "us": ["US-DOC-01"]},
    "criteria": [{"id": "M3-P2-T1-C1", "kind": "auto", "text": "The generated vision validates.", "done": True},
                 {"id": "M3-P2-T1-C2", "kind": "auto", "text": "Every capability has a unique identifier.",
                  "done": True}]},
   {"id": "M3-P2-T2", "title": "Gaps become open questions", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit"], "dependsOn": ["M3-P2-T1"],
    "summary": "Where the source is silent, record an open question or an assumption; never fabricate content to "
               "fill a section, and omit sections with nothing real to say.",
    "tdd": {"red": "A test generates from a brief with no stated constraints and asserts the constraints section "
                   "is absent and an open question exists; it fails while sections are always emitted.",
            "green": "Emit only populated sections and route silence to open questions.",
            "refactor": "Apply the same rule in every generator through the shared authoring helper."},
    "traces": {"fr": ["FR-DOC-04"], "nfr": ["NFR-DAT-06"], "us": ["US-DOC-01"]},
    "criteria": [{"id": "M3-P2-T2-C1", "kind": "auto", "text": "An unsupported section is absent rather than "
                                                               "empty.", "done": True},
                 {"id": "M3-P2-T2-C2", "kind": "auto", "text": "The gap appears in open questions.", "done": True}]},
   {"id": "M3-P2-T3", "title": "Source register", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "integration"], "dependsOn": ["M3-P2-T1"],
    "summary": "Accept narrative, documents and web addresses as vision input, and maintain a register of every "
               "source consulted — what it was, where it came from, what it contributed — carried with the set.",
    "tdd": {"red": "A test generates a vision from a mixed bundle of narrative and two source files and asserts "
                   "the register lists each source with origin and contribution; it fails with no register.",
            "green": "Record each consulted source into the register as it is used.",
            "refactor": "Make the register a first-class part of the vision specification object."},
    "traces": {"fr": ["FR-DOC-10"], "us": ["US-CTX-01"]},
    "criteria": [{"id": "M3-P2-T3-C1", "kind": "auto", "text": "Every consulted source appears in the register "
                                                               "with origin and contribution.", "done": True}]}]},

 {"id": "M3-P4", "title": "Context generator — ubiquitous language", "dependsOn": ["M3-P2"],
  "summary": "Between vision and product requirements: derive one shared vocabulary from the vision and its "
             "source register, resolve collisions by interview, scope meanings to bounded contexts, and make "
             "every downstream generator speak it.",
  "completion": ["A context document generated from a completed vision validates, with one definition per term.",
                 "Invoked without a completed vision, the generator refuses and writes nothing."],
  "tasks": [
   {"id": "M3-P4-T1", "title": "Context schema and generator", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Publish the context schema — bounded contexts and glossary — and the generator that derives "
               "candidate terms from the vision and its source register, refusing to run without a completed "
               "vision.",
    "tdd": {"red": "One test invokes the generator with no vision present and asserts it refuses, names the "
                   "missing document and writes nothing; a second generates from a fixture vision and asserts "
                   "every glossary term is sourced and carries exactly one definition; both fail initially.",
            "green": "Implement the prerequisite check, the harvest step and the glossary emission.",
            "refactor": "Share the prerequisite-refusal helper with every downstream generator."},
    "traces": {"fr": ["FR-CTX-01", "FR-CTX-02"], "us": ["US-CTX-01"]},
    "criteria": [{"id": "M3-P4-T1-C1", "kind": "auto", "text": "Without a completed vision the generator refuses "
                                                               "and writes nothing.", "done": True},
                 {"id": "M3-P4-T1-C2", "kind": "auto", "text": "Every glossary term has exactly one definition "
                                                               "and a recorded source.", "done": True}]},
   {"id": "M3-P4-T2", "title": "Bounded contexts and the collision interview", "priority": "Must",
    "status": "passing", "autonomy": "auto", "layer": "generator", "testLayers": ["unit", "e2e"], "dependsOn": ["M3-P4-T1"],
    "summary": "Partition the domain into named bounded contexts, scope colliding meanings to their contexts, "
               "route every collision through the clarification interview, and render the context map.",
    "tdd": {"red": "A test feeds vocabulary in which one term carries two incompatible meanings and asserts the "
                   "generator raises an interview question with a recommended resolution rather than choosing "
                   "silently, and that the resolved entry shows both scoped meanings; it fails initially.",
            "green": "Implement collision detection, the interview hand-off and context scoping.",
            "refactor": "Express collision detection as data-driven rules over the harvested cluster."},
    "traces": {"fr": ["FR-CTX-03", "FR-CTX-04", "FR-CTX-06"], "us": ["US-CTX-02"]},
    "criteria": [{"id": "M3-P4-T2-C1", "kind": "auto", "text": "A collision produces an interview question, "
                                                               "never a silent choice.", "done": True},
                 {"id": "M3-P4-T2-C2", "kind": "auto", "text": "A scoped term shows its meaning per bounded "
                                                               "context and appears on the context map.",
                  "done": True}]},
   {"id": "M3-P4-T3", "title": "Downstream generators speak the language", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "integration"], "dependsOn": ["M3-P4-T1"],
    "summary": "Every generator downstream of the context document consults its glossary, uses canonical terms, "
               "and routes any missing term back as a forward-only amendment instead of defining it locally.",
    "tdd": {"red": "A test generates a downstream document against a glossary containing a retired synonym and "
                   "asserts the canonical term is used and the synonym absent; a second asserts a needed missing "
                   "term is appended to the context document, not defined locally; both fail initially.",
            "green": "Add glossary consultation and the forward-only amendment path to the shared authoring "
                     "helper.",
            "refactor": "Surface glossary consultation as one helper every generator calls."},
    "traces": {"fr": ["FR-CTX-05"], "us": ["US-CTX-03"]},
    "criteria": [{"id": "M3-P4-T3-C1", "kind": "auto", "text": "No retired synonym appears in a downstream "
                                                               "document.", "done": True},
                 {"id": "M3-P4-T3-C2", "kind": "auto", "text": "A missing term is added to the context document, "
                                                               "never defined locally.", "done": True}]}]},

 {"id": "M3-P3", "title": "Product-requirements generator", "dependsOn": ["M3-P4"],
  "summary": "Goals, non-goals, journeys, measurable outcomes and risks, each tracing to the vision capabilities "
             "it serves.",
  "completion": ["A product-requirements document validates and traces upward to the vision.",
                 "Regeneration from an edited specification produces the updated document with no manual edit."],
  "tasks": [
   {"id": "M3-P3-T1", "title": "Product-requirements schema and generator", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Publish the schema and generator covering goals, non-goals, journeys, measurable outcomes, "
               "dependencies, assumptions and risks, each tracing to vision capabilities.",
    "tdd": {"red": "A test asserts the output validates and that every goal traces to at least one capability; it "
                   "fails with no generator.",
            "green": "Implement the schema, the section list and trace requirements.",
            "refactor": "Extract the shared trace-rendering helper for reuse by later generators."},
    "traces": {"fr": ["FR-DOC-01", "FR-TRC-03"], "nfr": ["NFR-ARC-01", "NFR-ARC-02"], "us": ["US-DOC-01"]},
    "criteria": [{"id": "M3-P3-T1-C1", "kind": "auto", "text": "The generated document validates.", "done": True},
                 {"id": "M3-P3-T1-C2", "kind": "auto", "text": "Every goal traces to a capability that exists.",
                  "done": True}]},
   {"id": "M3-P3-T2", "title": "Regeneration without loss", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit"], "dependsOn": ["M3-P3-T1"],
    "summary": "Editing a document's embedded specification and regenerating produces the updated document with "
               "every other value preserved, so no update requires touching rendered output.",
    "tdd": {"red": "A test extracts a specification, changes one value, regenerates and asserts only that value "
                   "differs; it fails while regeneration rebuilds from the original source only.",
            "green": "Accept an existing embedded specification as generator input.",
            "refactor": "Make round-tripping the default path for every generator."},
    "traces": {"fr": ["FR-DOC-06"], "nfr": ["NFR-GEN-01"], "us": ["US-SPC-01"]},
    "criteria": [{"id": "M3-P3-T2-C1", "kind": "auto", "text": "A round trip changes only the edited value.",
                  "done": True}]}]}],

"M4": [
 {"id": "M4-P1", "title": "Functional specification generator", "dependsOn": [],
  "summary": "The document the whole downstream chain traces to: prioritised, area-grouped, testable functional "
             "requirements with no technical content.",
  "completion": ["A functional specification validates and contains no technical requirement.",
                 "Areas, priorities, tags and notes all render and filter."],
  "tasks": [
   {"id": "M4-P1-T1", "title": "Functional schema and generator", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "e2e"], "dependsOn": [],
    "summary": "Publish the functional schema — areas, requirements, priorities, tags, notes, assumptions, open "
               "questions — and the generator that produces a validating document from a brief.",
    "tdd": {"red": "A test generates from a fixture brief and asserts the output validates, every requirement "
                   "belongs to a declared area, and every requirement carries a priority; it fails initially.",
            "green": "Implement the schema and the generator.",
            "refactor": "Share the catalogue renderer with the technical generator rather than duplicating it."},
    "traces": {"fr": ["FR-DOC-01"], "nfr": ["NFR-ARC-01"], "us": ["US-DOC-01"]},
    "criteria": [{"id": "M4-P1-T1-C1", "kind": "auto", "text": "The generated document validates.", "done": True},
                 {"id": "M4-P1-T1-C2", "kind": "auto", "text": "Every requirement has a declared area and a "
                                                               "priority.", "done": True}]},
   {"id": "M4-P1-T2", "title": "Enforce the functional/technical boundary", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit", "manual"], "dependsOn": ["M4-P1-T1"],
    "summary": "Keep technical, architectural, performance and security content out of the functional document, "
               "routing any technical implication to an open question for the technical specification.",
    "tdd": {"red": "A test feeds a brief containing an explicit storage choice and asserts no requirement names a "
                   "technology and an open question records the deferral; it fails initially.",
            "green": "Add the boundary check to authoring and the validator.",
            "refactor": "Express the prohibited vocabulary as data so it can be tuned per project."},
    "traces": {"fr": ["FR-DOC-05"], "nfr": ["NFR-ARC-02"], "us": ["US-DOC-03"]},
    "criteria": [{"id": "M4-P1-T2-C1", "kind": "auto", "text": "No functional requirement names a technology.",
                  "done": True},
                 {"id": "M4-P1-T2-C2", "kind": "human-review", "text": "A reviewer confirms requirements describe "
                                                                       "observable behaviour, not implementation.",
                  "done": True}]},
   {"id": "M4-P1-T3", "title": "Explicit exclusions recorded, not dropped", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "generator", "testLayers": ["unit"], "dependsOn": ["M4-P1-T1"],
    "summary": "A deliberate exclusion is recorded as a lowest-priority requirement with its reason rather than "
               "omitted, so the decision survives and is not revisited by default.",
    "tdd": {"red": "A test asserts an exclusion appears in the catalogue with its reason and is excluded from the "
                   "coverage universe; it fails while exclusions are dropped.",
            "green": "Represent exclusions as entries and mark them excluded from coverage.",
            "refactor": "Make the coverage engine read the same marker rather than a separate list."},
    "traces": {"fr": ["FR-TRC-06"], "us": ["US-TRC-01"]},
    "criteria": [{"id": "M4-P1-T3-C1", "kind": "auto", "text": "An exclusion is present with its reason.",
                  "done": True},
                 {"id": "M4-P1-T3-C2", "kind": "auto", "text": "An exclusion is not counted in the coverage "
                                                               "universe.", "done": True}]}]},

 {"id": "M4-P2", "title": "Catalogue interaction", "dependsOn": ["M4-P1"],
  "summary": "Filtering, priority toggles, deep links and review tracking over a catalogue of several hundred "
             "entries.",
  "completion": ["Filter, priority toggle and deep link all work together.",
                 "Interaction stays within one animation frame at the stated catalogue size."],
  "tasks": [
   {"id": "M4-P2-T1", "title": "Keyword filter across every catalogue", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "runtime", "testLayers": ["e2e", "perf"], "dependsOn": [],
    "summary": "One filter narrows every catalogue in the document, matching identifier, title, body and tags, "
               "hiding groups that lose all their entries and stating plainly when nothing matches.",
    "tdd": {"red": "Tests assert matching across all four fields, that emptied groups hide, that a no-match "
                   "message appears, and that filtering five hundred entries stays within one frame; all fail.",
            "green": "Index each entry's searchable text at render time and filter against it.",
            "refactor": "Precompute the searchable string once per entry rather than per keystroke."},
    "traces": {"fr": ["FR-SPC-05"], "nfr": ["NFR-PRF-03"], "us": ["US-SPC-02"]},
    "criteria": [{"id": "M4-P2-T1-C1", "kind": "auto", "text": "Filtering matches identifier, title, body and "
                                                               "tags.", "done": True},
                 {"id": "M4-P2-T1-C2", "kind": "auto", "text": "A no-match state is stated explicitly.",
                  "done": True},
                 {"id": "M4-P2-T1-C3", "kind": "auto", "text": "Filtering five hundred entries completes within "
                                                               "one animation frame.", "done": True}]},
   {"id": "M4-P2-T2", "title": "Priority toggles composing with the filter", "priority": "Should",
    "status": "passing", "autonomy": "auto", "layer": "runtime", "testLayers": ["e2e"], "dependsOn": ["M4-P2-T1"],
    "summary": "Each priority band can be switched off and on, showing its entry count, and composes with the "
               "keyword filter rather than replacing it.",
    "tdd": {"red": "A test applies a keyword, disables a band, and asserts only entries matching both remain; it "
                   "fails while the two filters are independent.",
            "green": "Apply both predicates in one pass.",
            "refactor": "Express visibility as a single predicate so a third filter is additive."},
    "traces": {"fr": ["FR-SPC-07"], "us": ["US-SPC-02"]},
    "criteria": [{"id": "M4-P2-T2-C1", "kind": "auto", "text": "Keyword and priority filters compose.",
                  "done": True},
                 {"id": "M4-P2-T2-C2", "kind": "auto", "text": "Each band shows its entry count.", "done": True}]},
   {"id": "M4-P2-T3", "title": "Deep links and expand/collapse", "priority": "Must", "autonomy": "auto",
    "status": "passing", "layer": "runtime", "testLayers": ["e2e"], "dependsOn": ["M4-P2-T1"],
    "summary": "Every entry is addressable; following a link expands any collapsed container, scrolls the entry "
               "into view and marks it briefly. Expand-all and collapse-all act on every group.",
    "tdd": {"red": "A test opens a link to an entry inside a collapsed group and asserts the group expands and "
                   "the entry is marked; it fails while collapsed content stays hidden.",
            "green": "Resolve the fragment, open ancestors, scroll and mark.",
            "refactor": "Reuse the same open-ancestors routine for search results."},
    "traces": {"fr": ["FR-SPC-06", "FR-SPC-10"], "us": ["US-SPC-03"]},
    "criteria": [{"id": "M4-P2-T3-C1", "kind": "auto", "text": "A deep link expands its container and marks the "
                                                               "entry.", "done": True},
                 {"id": "M4-P2-T3-C2", "kind": "auto", "text": "Expand-all and collapse-all affect every group.",
                  "done": True}]},
   {"id": "M4-P2-T4", "title": "Review tracking and progress", "priority": "Should", "autonomy": "auto",
    "status": "passing", "layer": "runtime", "testLayers": ["e2e"], "dependsOn": ["M4-P2-T3"],
    "summary": "A reviewer can mark each entry reviewed and see aggregate progress, persisted locally and "
               "resettable.",
    "tdd": {"red": "A test marks entries, reloads, and asserts the marks and the progress figure survive; it "
                   "fails with no persistence.",
            "green": "Persist marks under the document namespace and paint the progress meter.",
            "refactor": "Derive the meter from the marks rather than tracking a separate count."},
    "traces": {"fr": ["FR-SPC-08"], "us": ["US-SPC-04"]},
    "criteria": [{"id": "M4-P2-T4-C1", "kind": "auto", "text": "Marks and progress survive a reload.",
                  "done": True},
                 {"id": "M4-P2-T4-C2", "kind": "auto", "text": "Reset clears both.", "done": True}]}]}],
}
