# -*- coding: utf-8 -*-
"""Zero-to-Ship plan detail — M18.

M18 came from using the method on a second piece of work in a project that had
already shipped one. Two things broke, and neither was a defect in any single
tool.

The first was the name. The chain's first document was called the Vision, and
in practice it is read as a slogan rather than as the thing that says what a
piece of work is FOR. It is renamed to the Intent. A rename is cheap to write
and expensive to ship: every project that already holds a `Vision.html` would
be told its prerequisite is missing, and every link published to the old name
would break. So the rename comes with two compatibilities — a prerequisite that
falls back to the old filename under its old slug, and, in a published set, a
redirect page left at the retired name (NFR-OPS-07).

The second was the shape. One repository held one Intent, one plan and one
coverage universe, so a second capability had to be appended to the set that
described the first. Its requirements joined a universe spanning work that
shipped months earlier, and the coverage gate re-proved the whole history to
accept one new requirement. The alternative — forking the set — gives the
project two answers to what a word means.

So a project gains a level. A shared layer holds what a project has once (its
Intent, its Context, its workers, its design record), and each feature holds
its own specifications, plan and run state beneath it (FR-GEN-12, ADR-19).
Exactly three directory names move with a feature; everything else is resolved
above it, which is what keeps the seam small enough to hold. Which feature is
current is DERIVED from the listing rather than stored, because a stored answer
disagrees with the directories the first time somebody makes one by hand. One
is open at a time (FR-GEN-13), and closing is audited (FR-GEN-14).

A project that has opened no feature must be byte-identical to what it was.
That is not a nice-to-have here — it is the proof that the seam is where it is
claimed to be, and it is a criterion of P2 rather than a note.
"""

DETAIL = {

"M18": [
 {"id": "M18-P1", "title": "The first document is the Intent, and the old name keeps resolving", "dependsOn": [],
  "summary": "Rename the chain's first document from Vision to Intent everywhere it is written down, and pay "
             "the two compatibility debts a rename owes: a prerequisite check that reads the old filename "
             "under its old slug when the new one is absent, and a redirect left at the retired name in a "
             "published set.",
  "completion": ["Every surface of the method calls the first document the Intent.",
                 "A project holding only the old file is read, not refused, and nothing on disk is moved.",
                 "A link published to the retired name still arrives at the new document."],
  "tasks": [
   {"id": "M18-P1-T1", "title": "The rename, through the chain", "priority": "Must", "autonomy": "auto",
    "status": "not-started", "layer": "generator", "testLayers": ["unit", "integration"], "dependsOn": [],
    "summary": "Rename the generator, its filename, its slug and its skill so the first document is the "
               "Intent throughout — one name for one thing, rather than a new name with the old one still "
               "readable in half the surfaces. Touches the intent generator and the shared chain module.",
    "tdd": {"red": "A test generates the first document into an empty project and asserts the filename and "
                   "slug are the Intent's; it fails while both are the Vision's.",
            "green": "Rename the module, the filename constant and the slug, and repoint every caller.",
            "refactor": "Leave exactly one place naming the first document, so the next rename is one edit."},
    "traces": {"fr": ["FR-DOC-01"], "us": ["US-SKL-03"]},
    "criteria": [{"id": "M18-P1-T1-C1", "kind": "auto",
                  "text": "A fresh project's first document is written as the Intent, under the Intent's slug.",
                  "done": False},
                 {"id": "M18-P1-T1-C2", "kind": "auto",
                  "text": "No module, skill body or generated document names the first document by its old "
                          "name except the two compatibilities.", "done": False}]},
   {"id": "M18-P1-T2", "title": "The old filename is still read", "priority": "Must", "autonomy": "auto",
    "status": "not-started", "layer": "generator", "testLayers": ["unit"], "dependsOn": ["M18-P1-T1"],
    "summary": "Give the prerequisite check a declared map from new filename to former filename and slug, so "
               "a project written before the rename is read under the old name when the new one is absent, "
               "with nothing moved on disk and new writes going to the new name only.",
    "tdd": {"red": "A test puts only the old file in a project and asks for the document below it; it fails "
                   "with a missing prerequisite.",
            "green": "Fall back to the former filename when the new one does not exist, and report the "
                     "document under its former slug.",
            "refactor": "Keep the map narrow — only a document that was actually renamed gets an entry — so "
                        "no other missing prerequisite is silently satisfied by a differently named file."},
    "traces": {"nfr": ["NFR-OPS-07"], "fr": ["FR-SKL-02"], "us": ["US-SKL-01"]},
    "criteria": [{"id": "M18-P1-T2-C1", "kind": "auto",
                  "text": "A project holding only the retired filename generates the next document without "
                          "refusing, and nothing on disk is moved or renamed.", "done": False},
                 {"id": "M18-P1-T2-C2", "kind": "auto",
                  "text": "A new write goes to the new filename even where the old one exists.", "done": False},
                 {"id": "M18-P1-T2-C3", "kind": "auto",
                  "text": "No filename other than the renamed one has a fallback.", "done": False}]},
   {"id": "M18-P1-T3", "title": "The retired name is a redirect, not a gap", "priority": "Must",
    "autonomy": "auto", "status": "not-started", "layer": "generator", "testLayers": ["unit", "e2e"],
    "dependsOn": ["M18-P1-T1"],
    "summary": "Generate a redirect page at the retired filename of the published set, carrying a refresh and "
               "a canonical link to the new document, and check it the way every other generated page is "
               "checked. Touches the published set's generator and its rendered-document check, and the "
               "pipeline that reports what a set contains.",
    "tdd": {"red": "A check asserts the retired filename exists and points at the new one; it fails because "
                   "the file is gone.",
            "green": "Emit the redirect from the same declared map the fallback uses.",
            "refactor": "Let the pipeline report a moved document as moved, so a redirect is never mistaken "
                        "for a specification that failed to parse."},
    "traces": {"nfr": ["NFR-OPS-07"], "fr": ["FR-SPC-01", "FR-GEN-07"], "us": ["US-SPC-01"]},
    "criteria": [{"id": "M18-P1-T3-C1", "kind": "auto",
                  "text": "The retired filename exists in the published set and resolves to the new document "
                          "by both refresh and canonical link.", "done": False},
                 {"id": "M18-P1-T3-C2", "kind": "auto",
                  "text": "The redirect is byte-identical on a second generation and is not validated as a "
                          "specification document.", "done": False}]}]},

 {"id": "M18-P2", "title": "The layout follows the open feature, and the Context stays the project's",
  "dependsOn": ["M18-P1"],
  "summary": "Give a project a level: a shared layer holding what it has once, and a numbered directory per "
             "feature holding that feature's specifications, plan and run state. Put the whole of that "
             "behaviour in one path-resolving seam, derive the current feature from the listing, and prove "
             "that a project with no features is unchanged byte for byte. Touches the paths module, the "
             "shared chain, the step definitions, the context generator, the plan generator, the briefing, "
             "the trace engine, the update tool, the chain driver and their tests.",
  "completion": ["Exactly three documented locations move with a feature; every other one is resolved above "
                 "it and held once.",
                 "Which feature is current is read from the directories and stored nowhere.",
                 "A project with no features regenerates byte-identically to what it produced before."],
  "tasks": [
   {"id": "M18-P2-T1", "title": "One seam, three scoped locations", "priority": "Must", "autonomy": "auto",
    "status": "not-started", "layer": "foundation", "testLayers": ["unit", "lint"], "dependsOn": [],
    "summary": "Declare the feature directory grammar and the list of locations that follow a feature — the "
               "specifications, the plan and the run state, and nothing else — and resolve every documented "
               "path through the one function that consults it.",
    "tdd": {"red": "A test opens a feature and asks where the specifications and the workers configuration "
                   "resolve to; it fails because both answer the same, above the feature.",
            "green": "Rewrite the path resolver to redirect a scoped head into the current feature and leave "
                     "everything else alone.",
            "refactor": "Keep the plain join available as its own function, so a caller wanting the shared "
                        "answer asks for it rather than reconstructing a path by hand."},
    "traces": {"fr": ["FR-GEN-12"], "nfr": ["NFR-OPS-01"], "adr": ["ADR-19"], "us": ["US-GEN-04"]},
    "criteria": [{"id": "M18-P2-T1-C1", "kind": "auto",
                  "text": "The specifications, the plan and the run state resolve inside the current feature; "
                          "every other documented location resolves above it.", "done": False},
                 {"id": "M18-P2-T1-C2", "kind": "auto",
                  "text": "A directory not matching the declared grammar is not a feature.", "done": False},
                 {"id": "M18-P2-T1-C3", "kind": "auto",
                  "text": "No file, key or argument records which feature is current; it is derived from the "
                          "listing every time it is asked for.", "done": False}]},
   {"id": "M18-P2-T2", "title": "The vocabulary belongs to the project", "priority": "Must", "autonomy": "auto",
    "status": "not-started", "layer": "generator", "testLayers": ["unit", "integration"],
    "dependsOn": ["M18-P2-T1"],
    "summary": "Make the shared reading explicit at the call sites that need it, so every feature's chain "
               "reads the project's Context and no feature writes one of its own, and so the set a gate sees "
               "is the feature's documents plus every shared one no feature document stands in for.",
    "tdd": {"red": "A test opens a feature, writes its own first document, and asks which documents are in "
                   "force; it fails because the project's vocabulary is not among them.",
            "green": "Read the Context from the shared layer at its call sites, and union the feature's "
                     "documents with the shared ones it does not stand in for.",
            "refactor": "Name the shared reading in one option rather than in each caller's own path "
                        "arithmetic."},
    "traces": {"fr": ["FR-CTX-01", "FR-CTX-05"], "adr": ["ADR-19"], "us": ["US-GEN-04", "US-CTX-01"]},
    "criteria": [{"id": "M18-P2-T2-C1", "kind": "auto",
                  "text": "A feature's chain reads the project's Context, and no feature writes one.",
                  "done": False},
                 {"id": "M18-P2-T2-C2", "kind": "auto",
                  "text": "A feature that has written its own first document is read from that one, not the "
                          "project's.", "done": False}]},
   {"id": "M18-P2-T3", "title": "A feature is proved on its own", "priority": "Must", "autonomy": "auto",
    "status": "not-started", "layer": "validator", "testLayers": ["unit", "integration"],
    "dependsOn": ["M18-P2-T1"],
    "summary": "Scope the trace universe, the coverage gate and the plan derivation to the documents in "
               "force, so a feature's requirements are proved against that feature's plan and nothing in "
               "another feature is scanned or required.",
    "tdd": {"red": "A test gives two features contradictory identifiers and proves coverage in the second; it "
                   "fails because the first feature's requirements are reported uncovered.",
            "green": "Build the universe from the documents in force rather than from every document under "
                     "the project root.",
            "refactor": "Leave the gate itself untouched — it is the same implementation wherever it is "
                        "reached from; only what it is pointed at changes."},
    "traces": {"fr": ["FR-GEN-12", "FR-TRC-04"], "adr": ["ADR-19"], "us": ["US-GEN-04"]},
    "criteria": [{"id": "M18-P2-T3-C1", "kind": "auto",
                  "text": "Coverage over one feature names only that feature's identifiers.", "done": False},
                 {"id": "M18-P2-T3-C2", "kind": "auto",
                  "text": "No cross-feature scan happens, and a second feature's plan is never read to prove "
                          "the first.", "done": False},
                 {"id": "M18-P2-T3-C3", "kind": "auto",
                  "text": "The coverage gate cannot be downgraded or scoped away by configuration.",
                  "done": False}]},
   {"id": "M18-P2-T4", "title": "A project with no features is unchanged", "priority": "Must",
    "autonomy": "auto", "status": "not-started", "layer": "ops", "testLayers": ["e2e", "CI"],
    "dependsOn": ["M18-P2-T1", "M18-P2-T2", "M18-P2-T3"],
    "summary": "Prove the seam is where it is claimed to be by regenerating a real project that has opened no "
               "feature and requiring not one byte to differ. This is the whole back-compatibility promise, "
               "stated as a check rather than as a paragraph.",
    "tdd": {"red": "The self-hosted set is regenerated in check mode and any difference fails the run.",
            "green": "Resolve every path through the seam so a project with no features takes the plain join "
                     "on every call.",
            "refactor": "Run the check in the gauntlet, so a later change that quietly scopes a shared "
                        "location is caught by the same command."},
    "traces": {"fr": ["FR-GEN-07", "FR-GEN-12"], "nfr": ["NFR-OPS-01"], "us": ["US-GEN-04"]},
    "criteria": [{"id": "M18-P2-T4-C1", "kind": "auto",
                  "text": "Regenerating a project that has opened no feature produces byte-identical output, "
                          "proved by the self-hosted set's own check rather than asserted.", "done": False},
                 {"id": "M18-P2-T4-C2", "kind": "auto",
                  "text": "Every documented location a project holds once still resolves above any feature.",
                  "done": False}]}]},

 {"id": "M18-P3", "title": "One feature is open at a time, and closing it is audited", "dependsOn": ["M18-P2"],
  "summary": "Add the operations a feature needs and nothing more: open the next one by name, refuse a second "
             "while one is open, refuse to write into one already closed, audit what a close would leave, and "
             "record the close in the feature's own first document. Expose all of it as one named skill with "
             "three operations and no selector. Touches the feature module, its skill body, the step "
             "definitions, the orchestrator and their tests.",
  "completion": ["A second feature cannot be opened while one is open, and a closed one cannot be written "
                 "into.",
                 "A close with no reason needs a clean audit; a close with a reason records what was left.",
                 "The document a close writes is byte-identical to a regeneration of it."],
  "tasks": [
   {"id": "M18-P3-T1", "title": "Opening the next feature, and refusing the second", "priority": "Must",
    "autonomy": "auto", "status": "not-started", "layer": "orchestration", "testLayers": ["unit"],
    "dependsOn": [],
    "summary": "Allocate the next number, create the feature's own directories, and refuse — naming the open "
               "feature and what to do instead — when one is already open. Refuse in the chain's own voice "
               "when the project's intent or vocabulary is missing, because that is the document to write "
               "first.",
    "tdd": {"red": "A test opens a feature and opens a second; it fails because the second is created.",
            "green": "Refuse while the derived feature exists and carries no closed record, and create "
                     "nothing on a refusal.",
            "refactor": "Read the closed record through the shared extraction, so nothing here parses a "
                        "document."},
    "traces": {"fr": ["FR-GEN-13", "FR-GEN-12"], "adr": ["ADR-19"], "us": ["US-GEN-05"], "uc": ["UC-11"]},
    "criteria": [{"id": "M18-P3-T1-C1", "kind": "auto",
                  "text": "Opening a second feature while one is open is refused, names the open one, and "
                          "creates nothing.", "done": False},
                 {"id": "M18-P3-T1-C2", "kind": "auto",
                  "text": "A name that is not a valid feature name is refused before anything is created.",
                  "done": False},
                 {"id": "M18-P3-T1-C3", "kind": "auto",
                  "text": "Opening without the project's intent or vocabulary refuses in the same voice a "
                          "missing prerequisite is refused in.", "done": False}]},
   {"id": "M18-P3-T2", "title": "A closed feature is not written into", "priority": "Must", "autonomy": "auto",
    "status": "not-started", "layer": "generator", "testLayers": ["unit"], "dependsOn": ["M18-P3-T1"],
    "summary": "Record a close in the feature's own first document, and teach every generator to refuse to "
               "write into a feature that carries one — as a kind of missing prerequisite, so every caller "
               "already reports it the same way. Something arriving afterwards opens the next feature; "
               "something arriving while one is open folds into it as an addendum.",
    "tdd": {"red": "A test closes a feature and asks a generator to write into it; it fails because the "
                   "write succeeds.",
            "green": "Raise the closed refusal from the shared prerequisite check.",
            "refactor": "Derive the refusal from the missing-prerequisite type rather than adding a second "
                        "error path through every generator."},
    "traces": {"fr": ["FR-GEN-13"], "adr": ["ADR-19"], "us": ["US-GEN-05"], "uc": ["UC-11"]},
    "criteria": [{"id": "M18-P3-T2-C1", "kind": "auto",
                  "text": "A generator asked to write into a closed feature refuses, and every caller reports "
                          "it as a missing prerequisite.", "done": False},
                 {"id": "M18-P3-T2-C2", "kind": "auto",
                  "text": "A feature with no first document yet is open, not closed.", "done": False}]},
   {"id": "M18-P3-T3", "title": "The audit, and the two doors out of it", "priority": "Must",
    "autonomy": "auto", "status": "not-started", "layer": "orchestration",
    "testLayers": ["unit", "integration"], "dependsOn": ["M18-P3-T2"],
    "summary": "Ask four questions of the feature — is every unit of its plan passing, does every retired "
               "identifier name a successor, is every question its documents raised answered, is everything "
               "it built shipped — and let a close with no reason through only on a clean answer. A close "
               "with a reason succeeds and records the findings beside it as what was left.",
    "tdd": {"red": "A test closes a feature holding a not-started unit with no reason and asserts a refusal "
                   "listing it; it fails because the close succeeds.",
            "green": "Run the audit before writing, refuse without a reason, and record the findings with "
                     "one.",
            "refactor": "Write the close through the same status writer every other status change uses, so a "
                        "closed document stays byte-identical to a regenerated one."},
    "traces": {"fr": ["FR-GEN-14"], "nfr": ["NFR-EVO-01"], "adr": ["ADR-19"], "us": ["US-GEN-06"],
               "uc": ["UC-11"]},
    "criteria": [{"id": "M18-P3-T3-C1", "kind": "auto",
                  "text": "A close with no reason over any finding is refused and lists every finding, each "
                          "saying what it is about.", "done": False},
                 {"id": "M18-P3-T3-C2", "kind": "auto",
                  "text": "A close with a reason records the date, the reason and every finding in the "
                          "feature's own first document.", "done": False},
                 {"id": "M18-P3-T3-C3", "kind": "auto",
                  "text": "A close states its date; a close naming none is refused and writes nothing.",
                  "done": False},
                 {"id": "M18-P3-T3-C4", "kind": "auto",
                  "text": "The document a close writes is byte-identical to a regeneration of it.",
                  "done": False}]},
   {"id": "M18-P3-T4", "title": "One skill, three operations, no selector", "priority": "Must",
    "autonomy": "auto", "status": "not-started", "layer": "docs", "testLayers": ["unit", "manual"],
    "dependsOn": ["M18-P3-T3"],
    "summary": "Expose opening, closing and status as one named skill, register it among the method's "
               "operations so the published set lists it, and give it no argument naming which feature to act "
               "on — the feature acted on is always the one the project derives.",
    "tdd": {"red": "A check asserts the skill exists, is registered among the operations and accepts no "
                   "feature selector; it fails on all three.",
            "green": "Write the skill body against the three operations and register its summary once.",
            "refactor": "Take the summary the published set prints from the one place the operations are "
                        "declared, so the table cannot drift from the skill."},
    "traces": {"fr": ["FR-SKL-10", "FR-SKL-01", "FR-SKL-03"], "adr": ["ADR-19"], "us": ["US-SKL-08"],
               "uc": ["UC-11"]},
    "criteria": [{"id": "M18-P3-T4-C1", "kind": "auto",
                  "text": "The skill offers exactly open, close and status, and accepts no argument naming a "
                          "feature.", "done": False},
                 {"id": "M18-P3-T4-C2", "kind": "auto",
                  "text": "Status names the open feature and lists exactly what a close with no reason would "
                          "refuse over.", "done": False},
                 {"id": "M18-P3-T4-C3", "kind": "human-review",
                  "text": "The skill body reads as an operator instruction, not as a description of the "
                          "module behind it.", "done": False}]}]},

 {"id": "M18-P4", "title": "Every surface that describes the method, and the release",
  "dependsOn": ["M18-P1", "M18-P2", "M18-P3"],
  "summary": "Bring every surface that describes the method up to what it now does — the published "
             "specification set, the self-hosted set the method keeps of itself, the changelog, and the "
             "plugin the chain ships as — and release it. Touches the self-hosted briefs and plan data, the "
             "changelog and both plugin manifests.",
  "completion": ["No published or self-hosted surface describes the first document by its retired name or "
                 "omits the feature layout.",
                 "The plugin's version is bumped in both manifests and the bundle is repinned."],
  "tasks": [
   {"id": "M18-P4-T1", "title": "The self-hosted set says what the method now does", "priority": "Must",
    "autonomy": "auto", "status": "not-started", "layer": "docs", "testLayers": ["unit", "CI"],
    "dependsOn": [],
    "summary": "Rewrite the method's own specification set — the set it keeps of itself — against the rename "
               "and the feature layout, and regenerate it under the check that requires byte-identical "
               "output.",
    "tdd": {"red": "The self-hosted set is regenerated in check mode after the source is updated; it fails on "
                   "the difference.",
            "green": "Update the self-hosted briefs and plan data and regenerate.",
            "refactor": "Leave the two renderers separate, as they are, and wire the change into both rather "
                        "than into one."},
    "traces": {"fr": ["FR-GEN-08", "FR-DOC-01"], "nfr": ["NFR-OPS-01"], "us": ["US-GEN-02"]},
    "criteria": [{"id": "M18-P4-T1-C1", "kind": "auto",
                  "text": "The self-hosted set regenerates byte-identically and every gate passes against it.",
                  "done": False},
                 {"id": "M18-P4-T1-C2", "kind": "auto",
                  "text": "No self-hosted document names the first document by its retired name.",
                  "done": False}]},
   {"id": "M18-P4-T2", "title": "The release", "priority": "Must", "autonomy": "auto",
    "status": "not-started", "layer": "ops", "testLayers": ["lint", "CI", "manual"],
    "dependsOn": ["M18-P4-T1"],
    "summary": "Record the change where an adopter reads it, bump the plugin's version in both places a "
               "runtime compares, and repin the bundle so the published lock and the skill bodies agree.",
    "tdd": {"red": "A check asserts both manifests carry the same new version and the lock pins every skill "
                   "at it; it fails on the old version.",
            "green": "Bump both manifests, repin the bundle, and write the changelog entry.",
            "refactor": "Take the version from the manifest rather than restating it, so the two cannot "
                        "disagree."},
    "traces": {"fr": ["FR-SKL-08", "FR-SKL-10"], "nfr": ["NFR-EVO-01"], "us": ["US-SKL-06"]},
    "criteria": [{"id": "M18-P4-T2-C1", "kind": "auto",
                  "text": "Both manifests carry the same new version and the bundle pins every skill at it.",
                  "done": False},
                 {"id": "M18-P4-T2-C2", "kind": "auto",
                  "text": "The changelog names the rename, its two compatibilities, and the feature layout.",
                  "done": False},
                 {"id": "M18-P4-T2-C3", "kind": "human-review",
                  "text": "An adopter reading only the changelog entry knows whether anything of theirs has "
                          "to move. It does not.", "done": False}]}]}],

}
