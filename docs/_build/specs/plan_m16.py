# -*- coding: utf-8 -*-
"""Zero-to-Ship plan detail — M16.

M16 came from a question, not from a review: hand the toolchain a complete
design system and would the documents look like the product? They did not. The
palette arrived and nothing else did, because eighteen of the thirty-nine tokens
the contract declared had no way of ever being filled, and because one file won
outright and the rest were discarded unread.

Two live defects surfaced on the way and are fixed here rather than filed: a
value read from a host file was copied into the style block unescaped, so a
document generated from a hostile project executed script when a reviewer opened
it from disk; and a dark block later in a stylesheet silently overwrote the light
values it duplicated, because the harvest was a flat search that could not see a
selector.

The requirements this changes are amended in place and dated. One is genuinely
new: FR-GEN-11, because the record is an artefact in the repository and a rule
about who wins, which is a different subject from how a document looks.
"""

DETAIL = {

"M16": [
 {"id": "M16-P1", "title": "A contract a design system can actually fill", "dependsOn": [],
  "summary": "Widen the token contract to everything that carries a project's identity, delete the token "
             "nothing referenced, take both colour schemes from one declaration, and prove in both directions "
             "that every token declared is a token the styling reads.",
  "completion": ["Every token the contract declares is referenced by the structural styling, and every token "
                 "the styling references is declared.",
                 "Light and dark are declared once, and a reader who forces either gets it.",
                 "A project that declares no dark values produces exactly the document it produced before."],
  "tasks": [
   {"id": "M16-P1-T1", "title": "Every token the contract declares can be reached, and is used",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "schema",
    "testLayers": ["unit", "lint"], "dependsOn": [],
    "summary": "Widen the contract to cover the display face, the weight scale, letter spacing, the accent "
               "colours, the pill radius and the second elevation, delete the token nothing referenced, and "
               "give every added token a real consumption site in the shared styling.",
    "tdd": {"red": "A test asserts every token the contract declares is reached by the structural styling; it "
                   "fails on the token declared, given a neutral value, written into every document and "
                   "referenced by nothing.",
            "green": "Delete that token and let the styling consume the widened contract, replacing the literal "
                     "weights, letter spacings and radii it had been carrying.",
            "refactor": "State the check in both directions from one place, so widening the contract without "
                        "using it fails as loudly as using a token without declaring it."},
    "traces": {"fr": ["FR-GEN-02"], "nfr": ["NFR-GEN-03", "NFR-ARC-04"], "adr": ["ADR-16"],
               "us": ["US-GEN-01"]},
    "criteria": [{"id": "M16-P1-T1-C1", "kind": "auto",
                  "text": "Every token the contract declares is referenced by the shared styling, and every "
                          "token the styling references is declared.", "done": True},
                 {"id": "M16-P1-T1-C2", "kind": "auto",
                  "text": "No token is declared that a host project has no way of filling.", "done": True}]},
   {"id": "M16-P1-T2", "title": "Light and dark from one declaration, and never invented",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "runtime",
    "testLayers": ["unit", "e2e", "a11y"], "dependsOn": ["M16-P1-T1"],
    "summary": "Carry both schemes in a single token block, let a reader force either one, print on light "
               "whatever the screen shows, and emit nothing at all where the host declares no dark values.",
    "tdd": {"red": "A browser test asks for a dark preference and asserts the page computes the host's dark "
                   "value, then forces light against it; it fails while a document has one scheme.",
            "green": "Pair each token's two values in one declaration and let a forced scheme override the "
                     "preference.",
            "refactor": "Drop the pairing entirely when no source declared a dark value, so a project without "
                        "one produces the bytes it produced before."},
    "traces": {"fr": ["FR-GEN-02", "FR-GEN-06"], "nfr": ["NFR-UX-03", "NFR-GEN-03"], "adr": ["ADR-16"],
               "us": ["US-GEN-01"]},
    "criteria": [{"id": "M16-P1-T2-C1", "kind": "auto",
                  "text": "A reader preferring dark gets the host's dark values, and a reader forcing a scheme "
                          "gets the one they forced.", "done": True},
                 {"id": "M16-P1-T2-C2", "kind": "auto",
                  "text": "A printed document is light whatever the screen showed.", "done": True},
                 {"id": "M16-P1-T2-C3", "kind": "auto",
                  "text": "A project declaring no dark values produces output identical to before this "
                          "milestone.", "done": True}]},
   {"id": "M16-P1-T3", "title": "The chrome budget is measured before it is raised",
    "priority": "Should", "autonomy": "auto", "status": "passing", "layer": "foundation",
    "testLayers": ["unit", "perf"], "dependsOn": ["M16-P1-T1", "M16-P1-T2"],
    "summary": "Raise the shared styling budget once, deliberately, and print the real figure on every run so "
               "the next raise is a decision somebody takes rather than a wall somebody hits.",
    "tdd": {"red": "A test asserts the shared styling fits the budget and reports the headroom; it fails "
                   "against the old ceiling once both schemes are carried.",
            "green": "Raise the constant, in one place, with the measurement written beside it.",
            "refactor": "Report the measured figure rather than a pass, so headroom is a number in the run "
                        "output and not something anybody has to go and compute."},
    "traces": {"fr": ["FR-GEN-02"], "nfr": ["NFR-PRF-02"], "us": ["US-GEN-01"]},
    "criteria": [{"id": "M16-P1-T3-C1", "kind": "auto",
                  "text": "The shared styling fits the stated budget and the run prints the headroom left.",
                  "done": True}]}]},

 {"id": "M16-P2", "title": "Read every source, not the best one", "dependsOn": ["M16-P1"],
  "summary": "Make the reader see selectors rather than search text, teach it the shapes a design system is "
             "actually written in, merge what it finds into one coherent result, and say plainly what it will "
             "not read.",
  "completion": ["A dark block no longer overwrites the light values it duplicates.",
                 "A design system split across a token document and a stylesheet is adopted from both.",
                 "A format the toolchain does not read is named, with the formats it does read."],
  "tasks": [
   {"id": "M16-P2-T1", "title": "The harvest reads selectors, not text",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit"], "dependsOn": [],
    "summary": "Scan a stylesheet by brace depth so every declaration is read with the rule that holds it, "
               "keeping root-level values as light, values under a dark preference or a dark theme as dark, "
               "and discarding everything a component happens to declare about itself.",
    "tdd": {"red": "A test declares a token twice, once at the root and once under a dark preference, and "
                   "asserts the light value survives; it fails while the last match wins.",
            "green": "Track the prelude of every block and classify what it holds.",
            "refactor": "Read preprocessor variables through the same scanner, so file scope means the same "
                        "thing in both dialects."},
    "traces": {"fr": ["FR-GEN-02"], "nfr": ["NFR-GEN-03"], "adr": ["ADR-16"], "us": ["US-GEN-01"]},
    "criteria": [{"id": "M16-P2-T1-C1", "kind": "auto",
                  "text": "A dark block later in a file does not overwrite the light values it duplicates.",
                  "done": True},
                 {"id": "M16-P2-T1-C2", "kind": "auto",
                  "text": "A value a component declares about itself is not read as the project's design "
                          "system.", "done": True}]},
   {"id": "M16-P2-T2", "title": "Token documents, in both published dialects",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit"], "dependsOn": ["M16-P2-T1"],
    "summary": "Read a token document in either of the two dialects the industry publishes, following an alias "
               "to the value it names and flattening a group into the name the contract knows.",
    "tdd": {"red": "A test reads one document in each dialect and asserts both reach the contract; it fails "
                   "while only stylesheets are read.",
            "green": "Parse the document and walk it into flat names.",
            "refactor": "Resolve aliases through the same routine the stylesheet reader uses, so a reference "
                        "means one thing across the module."},
    "traces": {"fr": ["FR-GEN-02"], "nfr": ["NFR-ARC-03"], "adr": ["ADR-16"], "us": ["US-GEN-01"]},
    "criteria": [{"id": "M16-P2-T2-C1", "kind": "auto",
                  "text": "A token document in either published dialect is adopted, aliases included.",
                  "done": True},
                 {"id": "M16-P2-T2-C2", "kind": "auto",
                  "text": "A file that merely ends in the same extension is not read as a design system.",
                  "done": True}]},
   {"id": "M16-P2-T3", "title": "One scanner for every design system written as code",
    "priority": "Should", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit"], "dependsOn": ["M16-P2-T2"],
    "summary": "Read the literal object a framework configuration or a token module declares with a single "
               "tolerant scanner, and abandon a whole key rather than guess at a construct it cannot read.",
    "tdd": {"red": "A test reads a framework configuration and a token module and asserts both reach the "
                   "contract from the same routine; it fails while neither is read.",
            "green": "Scan the literal object by brace depth and flatten it.",
            "refactor": "Give the two callers one scanner, because two scanners for one grammar drift."},
    "traces": {"fr": ["FR-GEN-02"], "nfr": ["NFR-ARC-03"], "adr": ["ADR-16"], "us": ["US-GEN-01"]},
    "criteria": [{"id": "M16-P2-T3-C1", "kind": "auto",
                  "text": "A framework configuration and a token module are both read, by one routine.",
                  "done": True},
                 {"id": "M16-P2-T3-C2", "kind": "auto",
                  "text": "A construct the scanner cannot read abandons its key rather than contributing half "
                          "a palette.", "done": True}]},
   {"id": "M16-P2-T4", "title": "What is not read is said, not skipped",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit"], "dependsOn": ["M16-P2-T1"],
    "summary": "Name a design system written in a format the toolchain will not read, say which formats it "
               "does read and how to record the values by hand, and never guess at it — a half-read palette is "
               "a design system nobody has.",
    "tdd": {"red": "A test puts a design system in the unread format and asserts the run names the file and "
                   "the formats it reads instead; it fails while the file is passed over in silence.",
            "green": "Report the file and the alternatives.",
            "refactor": "Say it once, from the same list the readers are chosen from."},
    "traces": {"fr": ["FR-GEN-03", "FR-GEN-02"], "nfr": ["NFR-ARC-03"], "us": ["US-GEN-01"]},
    "criteria": [{"id": "M16-P2-T4-C1", "kind": "auto",
                  "text": "A design system in an unread format is named, with what is read instead.",
                  "done": True},
                 {"id": "M16-P2-T4-C2", "kind": "auto",
                  "text": "An unrelated file in that format is not mentioned.", "done": True}]},
   {"id": "M16-P2-T5", "title": "One base, then fill — and a scale that stays legible",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit"], "dependsOn": ["M16-P2-T2", "M16-P2-T3"],
    "summary": "Let the richest source set the palette and the rest fill only what it left empty, break every "
               "tie the same way on every machine, and hold an adopted scale inside a range a document can be "
               "read at, saying so whenever a value is held.",
    "tdd": {"red": "A test gives two sources with an equal claim and asserts the same one wins twice running; "
                   "it fails while the order is whatever the file system returned.",
            "green": "Order the sources by what they map, then by kind, then by path.",
            "refactor": "Hold the scale after the merge rather than inside each reader, so one rule covers "
                        "every source."},
    "traces": {"fr": ["FR-GEN-02", "FR-GEN-03"], "nfr": ["NFR-GEN-01", "NFR-UX-03"], "adr": ["ADR-16"],
               "us": ["US-GEN-01"]},
    "criteria": [{"id": "M16-P2-T5-C1", "kind": "auto",
                  "text": "A design system split across two files is adopted from both, and the merge is the "
                          "same on every run.", "done": True},
                 {"id": "M16-P2-T5-C2", "kind": "auto",
                  "text": "A scale outside the readable range is held and every hold is reported.",
                  "done": True}]}]},

 {"id": "M16-P3", "title": "The record, and a door to it", "dependsOn": ["M16-P2"],
  "summary": "Write the resolved design to a reviewable file naming where every value came from, let an "
             "operator's value outrank anything detected, read it at render time instead of walking the tree "
             "again, and give the refresh its own named skill.",
  "completion": ["Every adopted value names the file and the name it was read from.",
                 "A value an operator records survives a refresh unchanged and wins.",
                 "Every run says which of the four states it is in, and never a fifth silently."],
  "tasks": [
   {"id": "M16-P3-T1", "title": "The design that was resolved is written down",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit"], "dependsOn": [],
    "summary": "Write the resolved design beside the project's other configuration, carrying each value's "
               "origin, the operator's own values, the answers they confirmed, the sources and their contents, "
               "what was refused and what nobody claimed.",
    "tdd": {"red": "A test resolves a design, writes the record, reads it back and asserts every value names "
                   "its origin; it fails while the values are detected and discarded.",
            "green": "Build the record and write it.",
            "refactor": "State the authority order once, so the resolver and the writer cannot disagree about "
                        "who wins."},
    "traces": {"fr": ["FR-GEN-11", "FR-GEN-02"], "nfr": ["NFR-DAT-05"], "adr": ["ADR-16"],
               "us": ["US-GEN-03"]},
    "criteria": [{"id": "M16-P3-T1-C1", "kind": "auto",
                  "text": "Every adopted value names the file and the name it was read from.", "done": True},
                 {"id": "M16-P3-T1-C2", "kind": "auto",
                  "text": "A value an operator recorded outranks anything detected and survives a refresh "
                          "unchanged.", "done": True}]},
   {"id": "M16-P3-T2", "title": "A source that has moved on is noticed by its contents",
    "priority": "Should", "autonomy": "auto", "status": "in-progress", "layer": "validator",
    "testLayers": ["unit", "CI"], "dependsOn": ["M16-P3-T1"],
    "summary": "Hold the contents of every source the record was built from, so a design system that has "
               "changed since is detected without asking a clock, and surface it as a warning on the run's own "
               "gate rather than a failure.",
    "tdd": {"red": "A test changes a source after the record is written and asserts exactly one finding names "
                   "that file; it fails while nothing compares them.",
            "green": "Hold each source's contents in the record and compare on read.",
            "refactor": "Report it as a warning on the gate the project already runs, because a stale theme is "
                        "a document that looks slightly old, not a broken one."},
    "traces": {"fr": ["FR-GEN-03", "FR-GEN-11"], "nfr": ["NFR-DAT-05"], "us": ["US-GEN-03"]},
    "criteria": [{"id": "M16-P3-T2-C1", "kind": "auto",
                  "text": "A changed source is detected by its contents, never by a timestamp, and a file "
                          "merely touched is not reported.", "done": True},
                 {"id": "M16-P3-T2-C2", "kind": "auto",
                  "text": "The run's own gate reports a stale record as a warning rather than a failure.",
                  "done": False}]},
   {"id": "M16-P3-T3", "title": "The refresh gets its own door",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "orchestration",
    "testLayers": ["unit", "lint"], "dependsOn": ["M16-P3-T1"],
    "summary": "Add a named skill that reads the documents an operator hands it and records the result, "
               "leaving setup to write the record only when it is absent — because setup promises that a "
               "second run changes no byte and every other skill leans on that promise.",
    "tdd": {"red": "A test asserts the chain ships a design step, invocable by its documented name and "
                   "manual-only like every other; it fails while the chain has fourteen steps.",
            "green": "Add the step, its definition and its place in the chain.",
            "refactor": "Ask whether a step produces a document by looking at the document list rather than "
                        "at whether it carries code, which is the truer question and the one that survives a "
                        "step that carries code and writes no document."},
    "traces": {"fr": ["FR-SKL-01", "FR-SKL-03", "FR-SKL-04", "FR-SKL-09"],
               "nfr": ["NFR-SKL-01", "NFR-SKL-03", "NFR-SKL-04"], "adr": ["ADR-18"],
               "us": ["US-SKL-01", "US-SKL-06"]},
    "criteria": [{"id": "M16-P3-T3-C1", "kind": "auto",
                  "text": "The design step ships, is invocable by its documented name, and is pinned in the "
                          "manifest with the rest.", "done": True},
                 {"id": "M16-P3-T3-C2", "kind": "auto",
                  "text": "Running setup twice still changes no byte.", "done": True}]},
   {"id": "M16-P3-T4", "title": "Four states, four sentences, never a silent one",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit"], "dependsOn": ["M16-P3-T1", "M16-P3-T2"],
    "summary": "Read the record once per project rather than walking the tree for every document, and say "
               "which of the four states the run is in — recorded, recorded but moved on, detected and not "
               "recorded, or unreadable and therefore neutral.",
    "tdd": {"red": "A test damages the record and asserts the run uses the neutral theme and says so; it fails "
                   "while a damaged record falls through to detection and reports success.",
            "green": "Give each state its own sentence.",
            "refactor": "Resolve the theme once per project root, because rendering a plan of sixteen files "
                        "walked the whole tree sixteen times and threw the answer away each time."},
    "traces": {"fr": ["FR-GEN-03", "FR-GEN-11", "FR-GEN-02"], "nfr": ["NFR-DAT-05"], "adr": ["ADR-16"],
               "us": ["US-GEN-03"]},
    "criteria": [{"id": "M16-P3-T4-C1", "kind": "auto",
                  "text": "Each of the four states is reported in its own words, and a damaged record yields "
                          "the neutral theme rather than a silent re-detection.", "done": True},
                 {"id": "M16-P3-T4-C2", "kind": "auto",
                  "text": "The design is resolved once per project, not once per document.", "done": True}]}]},

 {"id": "M16-P4", "title": "Nothing hostile reaches the style block", "dependsOn": ["M16-P1"],
  "summary": "Refuse a host value that does not match the grammar of the token it fills, name every refusal, "
             "assert the boundary the values cross, and amend the requirements to say that the control is "
             "refusal at reading rather than escaping at writing.",
  "completion": ["A value that could close the style block or fetch from elsewhere never enters the pipeline.",
                 "Every refusal names the file, the token and the reason, and falls back to the neutral value.",
                 "The published specification says what was actually built."],
  "tasks": [
   {"id": "M16-P4-T1", "title": "A value is checked against the token it fills",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit", "lint"], "dependsOn": [],
    "summary": "Check every host value against the grammar of the token it would fill, refuse what does not "
               "match rather than stripping it, fall back to the neutral value, and name the file, the token "
               "and the reason in the report and in the record.",
    "tdd": {"red": "A test seeds a value that closes the style element and asserts it never reaches the "
                   "rendered block; it fails while host values are copied in unchecked.",
            "green": "Refuse what does not match the token's grammar, and report it.",
            "refactor": "Score a source by what survives the check rather than by what was read, so a file of "
                        "refusals cannot win the right to set the palette."},
    "traces": {"fr": ["FR-GEN-02", "FR-GEN-03", "FR-GEN-04"], "nfr": ["NFR-GEN-05", "NFR-SEC-01"],
               "adr": ["ADR-16"], "us": ["US-GEN-03"]},
    "criteria": [{"id": "M16-P4-T1-C1", "kind": "auto",
                  "text": "A value that could close the style block, fetch from elsewhere, or smuggle a second "
                          "declaration is refused and never rendered.", "done": True},
                 {"id": "M16-P4-T1-C2", "kind": "auto",
                  "text": "Every refusal names the file, the token and the reason, and the neutral value is "
                          "used in its place.", "done": True}]},
   {"id": "M16-P4-T2", "title": "The boundary the values cross asserts what crosses it",
    "priority": "Should", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit"], "dependsOn": ["M16-P4-T1"],
    "summary": "Refuse to assemble a document whose token block could close the element it sits in — not the "
               "real control, which is the check at reading, but the place the values actually cross, and "
               "therefore the thing that catches the next caller who gets tokens from somewhere else.",
    "tdd": {"red": "A test hands the assembler a token block containing markup and asserts it refuses; it "
                   "fails while the assembler trusts whatever it is given.",
            "green": "Assert it at the boundary.",
            "refactor": "Leave an ordinary block untouched, so the assertion costs nothing on every real run."},
    "traces": {"fr": ["FR-GEN-04"], "nfr": ["NFR-GEN-05", "NFR-SEC-01"], "us": ["US-GEN-03"]},
    "criteria": [{"id": "M16-P4-T2-C1", "kind": "auto",
                  "text": "A token block that could close the element it sits in is refused at assembly.",
                  "done": True}]},
   {"id": "M16-P4-T3", "title": "The specification says what was built",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "docs",
    "testLayers": ["unit", "CI"], "dependsOn": ["M16-P2-T5", "M16-P3-T1", "M16-P4-T1"],
    "summary": "Amend in place and date the five requirements this milestone changed, add the one requirement "
               "that is genuinely new because its subject is different, and regenerate the published set with "
               "the coverage gate green at the larger universe.",
    "tdd": {"red": "The coverage gate is run against the widened universe and fails, naming the new "
                   "requirement as claimed by nothing.",
            "green": "Amend the five, add the one, and give it a claiming task.",
            "refactor": "Amend rather than rewrite, so every trace written against the original still means "
                        "what it meant, and no identifier is retired."},
    "traces": {"fr": ["FR-GEN-11", "FR-AMD-04", "FR-AMD-05"], "nfr": ["NFR-EVO-05"], "adr": ["ADR-16"],
               "us": ["US-GEN-03"]},
    "criteria": [{"id": "M16-P4-T3-C1", "kind": "auto",
                  "text": "Every requirement this milestone changed is amended in place and dated, with the "
                          "original left as written and no identifier retired.", "done": True},
                 {"id": "M16-P4-T3-C2", "kind": "auto",
                  "text": "The coverage gate passes at the widened universe with nothing unclaimed.",
                  "done": True}]}]},

 {"id": "M16-P5", "title": "The documents an operator names", "dependsOn": ["M16-P2", "M16-P3"],
  "summary": "Read a design system where it is actually written down — a brand book, a design guide — from its "
             "embedded code, from its tables, and where neither can reach, by asking; and let a document "
             "somebody pointed at outrank anything found by searching.",
  "completion": ["A palette that lives only in a brand book's own style block is adopted.",
                 "A swatch table with a column saying what each value is for is adopted from that column.",
                 "A value stated only in prose is adopted only after the operator confirms it."],
  "tasks": [
   {"id": "M16-P5-T1", "title": "Code embedded in a reference document is code",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit"], "dependsOn": [],
    "summary": "Pull the style blocks out of a brand book and the fenced blocks out of a design guide and hand "
               "them to the readers that already exist, following a stylesheet the document links to when it "
               "is a file in the project, and recording rather than fetching one that is not.",
    "tdd": {"red": "A test puts a palette in a brand book's own style block and asserts it is adopted; it "
                   "fails while only stylesheets and token documents are read.",
            "green": "Extract the embedded code and route it to the reader for its language.",
            "refactor": "Record an absolute link and never fetch it, keeping the guarantee that no part of "
                        "this toolchain opens a socket."},
    "traces": {"fr": ["FR-GEN-02", "FR-DOC-07"], "nfr": ["NFR-ARC-03"], "adr": ["ADR-16"],
               "us": ["US-GEN-01"]},
    "criteria": [{"id": "M16-P5-T1-C1", "kind": "auto",
                  "text": "A palette that lives only in a reference document's embedded code is adopted.",
                  "done": True},
                 {"id": "M16-P5-T1-C2", "kind": "auto",
                  "text": "A linked stylesheet outside the project is recorded and reported, never fetched.",
                  "done": True}]},
   {"id": "M16-P5-T2", "title": "A swatch table says what each value is for",
    "priority": "Should", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit"], "dependsOn": ["M16-P5-T1"],
    "summary": "Read a table of values where a column says what each one is used for, taking that column as "
               "the signal and nothing else — a table with no such column claims nothing and its values are "
               "recorded as unclaimed rather than assigned to a guessed role.",
    "tdd": {"red": "A test reads a swatch table with a usage column and asserts the values reach the contract; "
                   "it fails while a table is prose to the reader.",
            "green": "Read the rows and take the role from the column that names one.",
            "refactor": "Use one row reader for both table dialects, since a pipe table and a markup table are "
                        "the same table."},
    "traces": {"fr": ["FR-GEN-02", "FR-DOC-07"], "adr": ["ADR-16"], "us": ["US-GEN-01"]},
    "criteria": [{"id": "M16-P5-T2-C1", "kind": "auto",
                  "text": "A table whose column says what each value is for is adopted from that column.",
                  "done": True},
                 {"id": "M16-P5-T2-C2", "kind": "auto",
                  "text": "A table with no such column claims nothing, and its values are recorded as "
                          "unclaimed.", "done": True}]},
   {"id": "M16-P5-T3", "title": "What only prose says is asked, never assumed",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "orchestration",
    "testLayers": ["unit"], "dependsOn": ["M16-P5-T2", "M16-P3-T1"],
    "summary": "Where a reference document states a value only in prose, put a proposal to the operator "
               "through the same interview every other step uses, record only what they confirm and record it "
               "with its provenance, and report an unanswered token as unanswered rather than as adopted.",
    "tdd": {"red": "A test puts a palette in prose alone and asserts nothing is adopted and the run says so; "
                   "it fails while a proposal is taken as an answer.",
            "green": "Open a question per proposal and adopt only confirmed answers.",
            "refactor": "Ride the interview driver every generator already uses, rather than building a second "
                        "one for this step."},
    "traces": {"fr": ["FR-GEN-02", "FR-GEN-03", "FR-GEN-11", "FR-SKL-03", "FR-SKL-04"],
               "nfr": ["NFR-SKL-04", "NFR-GEN-05"], "adr": ["ADR-16", "ADR-18"],
               "us": ["US-GEN-03", "US-SKL-02"]},
    "criteria": [{"id": "M16-P5-T3-C1", "kind": "auto",
                  "text": "A value stated only in prose is adopted only after the operator confirms it, and "
                          "carries where it came from.", "done": True},
                 {"id": "M16-P5-T3-C2", "kind": "auto",
                  "text": "An unconfirmed token stays neutral and is reported as unanswered, not as adopted.",
                  "done": True},
                 {"id": "M16-P5-T3-C3", "kind": "auto",
                  "text": "Prose carried to the reader is marked as material to read, so an instruction "
                          "written inside a reference document is not followed.", "done": True}]},
   {"id": "M16-P5-T4", "title": "A document somebody named outranks one nobody did",
    "priority": "Must", "autonomy": "auto", "status": "passing", "layer": "generator",
    "testLayers": ["unit"], "dependsOn": ["M16-P5-T1", "M16-P2-T5"],
    "summary": "Let the documents an operator hands the design step contribute everything they yield before "
               "anything found by searching, with discovery filling only what they left empty — pointing at a "
               "file is the strongest signal of intent there is.",
    "tdd": {"red": "A test names a sparse document and hides a richer stylesheet in the tree, then asserts the "
                   "named one sets the palette; it fails while the richest source wins.",
            "green": "Resolve named sources first and let discovery fill the gaps.",
            "refactor": "State the whole authority order in one place, so the record, the resolver and the "
                        "report cannot disagree about who won."},
    "traces": {"fr": ["FR-GEN-02", "FR-GEN-11"], "nfr": ["NFR-GEN-01"], "adr": ["ADR-16"],
               "us": ["US-GEN-03"]},
    "criteria": [{"id": "M16-P5-T4-C1", "kind": "auto",
                  "text": "A named document outranks a discovered one that maps more tokens.", "done": True},
                 {"id": "M16-P5-T4-C2", "kind": "auto",
                  "text": "A discovered source still fills what the named documents left empty.",
                  "done": True}]}]},
],

}
