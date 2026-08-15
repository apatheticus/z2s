# -*- coding: utf-8 -*-
"""Zero-to-Ship (Z2S) — Context & Ubiquitous Language (BC-*, UL-*).

This document is self-demonstrating: it applies the method's context step to the
method's own domain, so the glossary below is the vocabulary every other document
in this set uses. In a real project the glossary holds the customer's domain
terms instead.
"""

DOC = {
    "title": "Zero-to-Ship — Context & Ubiquitous Language",
    "slug": "context",
    "kicker": "Context",
    "type": "Context & Ubiquitous Language",
    "version": "2.0",
    "status": "Draft for review",
    "date": "2026-08-13",
    "owner": "Zerø Effort",
    "releaseScope": "v2 — the complete toolchain as the /zero:* skill chain",
    "summary": "One shared vocabulary for everything the method touches: every term defined once, scoped to a "
               "bounded context, and used identically by every later document, generator and worker. A word that "
               "means two things is two words.",
    "scopeNote": "Derived from the Vision and its source register, after a completed Vision exists and before the "
                 "product requirements are written. Amended forward only: a downstream document that needs a "
                 "missing term adds it here, never defines it locally.",
}

PURPOSE = [
    "Most specification defects are not logic errors — they are two people, or two documents, using the same "
    "word for different things. This document removes that failure mode before requirements are written: it "
    "establishes a **ubiquitous language**, one agreed definition per term, written down where every later "
    "generator and every worker can consult it.",
    "The idea is borrowed from domain-driven design. Vocabulary is **derived**, never invented: candidate terms "
    "are harvested from the vision and its source register, collisions and ambiguities are resolved by asking "
    "the operator through the clarification interview, and the surviving definitions are published here. From "
    "this point on, every document in the chain speaks this language — the requirements, the stories, the plan, "
    "the test names, even the commit messages.",
    "Where one word genuinely must mean different things in different parts of the domain, the meaning is "
    "**scoped to a bounded context** rather than fudged. The map below shows where each boundary sits and which "
    "terms change meaning as they cross one.",
]

DERIVATION_FLOW = {
    "name": "How the language is derived",
    "caption": "Every step consumes the previous one's output; nothing is invented. Questions flow through the "
               "shared clarification interview, one round at a time, each with a recommended answer.",
    "steps": [
        {"title": "Harvest", "desc": "Pull every candidate term from the vision, its source register, and any "
                                     "supplied material.", "kind": "input"},
        {"title": "Cluster", "desc": "Group synonyms and near-duplicates; flag terms used inconsistently."},
        {"title": "Interview", "desc": "Resolve every collision and ambiguity by asking — never by picking "
                                       "silently.", "kind": "gate"},
        {"title": "Canonicalise", "desc": "One term wins per concept; the others are recorded as synonyms."},
        {"title": "Scope", "desc": "Where one word must mean two things, bound each meaning to its context."},
        {"title": "Publish", "desc": "The glossary and context map below. Amended forward only from here on.",
         "kind": "accent"},
    ],
}

CONTEXTS = [
    {"id": "BC-01", "name": "Specification",
     "desc": "Where the document chain is authored: vision, context, product requirements, functional "
             "specification, stories, technical design. Everything here is a statement of intent — what the "
             "system must do and why.",
     "owns": ["Requirement", "Priority", "Trace", "Identifier", "Decision gate", "Locked decision",
              "Open question", "Addendum", "Source register"]},
    {"id": "BC-02", "name": "Planning",
     "desc": "Where intent becomes schedulable work: the derived plan, its coverage proof, and its dependency "
             "ordering. Everything here is computed from the Specification context's artefacts — authored "
             "content stops at the boundary.",
     "owns": ["Milestone", "Phase", "Task", "Criterion", "Wave", "Coverage", "Exclusion"]},
    {"id": "BC-03", "name": "Execution",
     "desc": "Where the plan is built: workers, dispatch, verification, status, and the run's memory. "
             "Everything here happens after the plan is frozen and is recorded back into it.",
     "owns": ["Worker", "Ready set", "Status", "Gauntlet", "Ledger", "Retrospective", "Autonomy class"]},
    {"id": "BC-04", "name": "Presentation",
     "desc": "Where artefacts meet readers: the rendered, self-contained document and its embedded data. "
             "Everything here is derived at load time from the machine-readable specification.",
     "owns": ["Rendered document", "Embedded specification", "Review state", "Self-contained"]},
]

CONTEXT_MAP = {
    "name": "Context map",
    "caption": "Specification feeds Planning; Planning feeds Execution; Execution writes status back into "
               "Planning's artefact. Presentation sits beside all three — every context publishes through it. "
               "Terms that cross a boundary and change meaning are flagged in the glossary.",
    "steps": [
        {"title": "Specification", "desc": "Authored intent. BC-01.", "kind": "input"},
        {"title": "Planning", "desc": "Derived work. BC-02."},
        {"title": "Execution", "desc": "Verified build, status written back. BC-03.", "kind": "accent"},
        {"title": "Presentation", "desc": "Rendered artefacts for every context. BC-04."},
    ],
}

GLOSSARY = [
    # ---- BC-01 Specification ----
    {"id": "UL-01", "term": "Document", "bc": "BC-01",
     "definition": "One artefact in the specification chain — Vision, Context, PRD, FSD, Stories, SDD or Plan — "
                   "with its own identity scheme and control block.",
     "notes": ["**Boundary shift:** in Presentation (BC-04) the same word means the rendered, self-contained "
               "file. The specification is what it says; the rendered document is what a reader opens."]},
    {"id": "UL-02", "term": "Requirement", "bc": "BC-01",
     "definition": "A single prioritised, individually testable statement of what the system shall do "
                   "(functional) or how it must be built (technical).",
     "notes": ["**Synonyms retired:** feature, capability (reserved for the Vision), spec item."]},
    {"id": "UL-03", "term": "Priority", "bc": "BC-01",
     "definition": "One of four bands — Must, Should, Could, Won't — where Won't is a recorded exclusion, not "
                   "an absence."},
    {"id": "UL-04", "term": "Identifier", "bc": "BC-01",
     "definition": "The permanent, human-typable name of one item — never reused, never renumbered. A retired "
                   "item keeps its number forever."},
    {"id": "UL-05", "term": "Trace", "bc": "BC-01",
     "definition": "A downstream item's recorded claim that it satisfies a named upstream identifier. Traces "
                   "run upward only.",
     "notes": ["**Not to be confused with:** a hyperlink. Every trace renders as a link, but a trace is a "
               "semantic claim the coverage gate counts."]},
    {"id": "UL-06", "term": "Decision gate", "bc": "BC-01",
     "definition": "The single interviewing pass, before any authoring, in which every unresolved fork is asked "
                   "as a question with a recommended answer.",
     "notes": ["**Synonyms retired:** grilling, kickoff questions."]},
    {"id": "UL-07", "term": "Locked decision", "bc": "BC-01",
     "definition": "A gate outcome recorded as decision, choice and rationale — closed for the rest of the "
                   "build and never re-litigated by a worker."},
    {"id": "UL-08", "term": "Open question", "bc": "BC-01",
     "definition": "A gap recorded instead of filled. The method's alternative to inventing content."},
    {"id": "UL-09", "term": "Addendum", "bc": "BC-01",
     "definition": "A separate document extending a shipped specification under its own identifier prefixes, "
                   "leaving the original untouched."},
    {"id": "UL-10", "term": "Source register", "bc": "BC-01",
     "definition": "The maintained record of every source material the vision consulted — what it was, where "
                   "it came from, what it contributed."},
    # ---- BC-02 Planning ----
    {"id": "UL-11", "term": "Milestone", "bc": "BC-02",
     "definition": "The largest unit of planned work: a coherent goal with declared dependencies and exit "
                   "criteria, containing phases."},
    {"id": "UL-12", "term": "Task", "bc": "BC-02",
     "definition": "The smallest independently verifiable unit of work: one failing test, one minimum change, "
                   "one clean-up, with its own acceptance criteria.",
     "notes": ["**Synonyms retired:** ticket, story (reserved for acceptance), work item."]},
    {"id": "UL-13", "term": "Criterion", "bc": "BC-02",
     "definition": "One individually tickable acceptance condition on a task, classified machine-checkable or "
                   "human-review."},
    {"id": "UL-14", "term": "Wave", "bc": "BC-02",
     "definition": "A set of milestones whose dependencies all lie in earlier waves, and which may therefore "
                   "run concurrently. Computed, never authored."},
    {"id": "UL-15", "term": "Coverage", "bc": "BC-02",
     "definition": "The computed proof that every requirement and decision is claimed by at least one task. "
                   "Its failure is a build failure, not a warning."},
    {"id": "UL-16", "term": "Exclusion", "bc": "BC-02",
     "definition": "An explicit, reasoned record that one identifier is deliberately not scheduled. The only "
                   "way past the coverage gate without a claiming task."},
    # ---- BC-03 Execution ----
    {"id": "UL-17", "term": "Worker", "bc": "BC-03",
     "definition": "A fresh execution context dispatched with one unit's self-contained prompt. It knows only "
                   "what its brief tells it, which is why the brief must contain everything.",
     "notes": ["**Synonyms retired:** agent (ambiguous), subprocess, builder."]},
    {"id": "UL-18", "term": "Ready set", "bc": "BC-03",
     "definition": "The computed set of units eligible to start now: not started, every dependency passing, "
                   "not human-gated."},
    {"id": "UL-19", "term": "Status", "bc": "BC-03",
     "definition": "The single live value recording where a unit stands, from a closed six-value vocabulary, "
                   "stored in the plan document itself.",
     "notes": ["**Boundary shift:** in Planning (BC-02) status is a schema field with a default; in Execution "
               "it is the value the write-back tool changes as work proceeds."]},
    {"id": "UL-20", "term": "Gauntlet", "bc": "BC-03",
     "definition": "The full verification run a unit must survive — the test layers its tasks name, executed "
                   "for real, with results reported as they actually happened."},
    {"id": "UL-21", "term": "Ledger", "bc": "BC-03",
     "definition": "The durable run record: done-state, autonomous decisions, next step, how to resume. "
                   "Authoritative over any worker's working memory."},
    {"id": "UL-22", "term": "Retrospective", "bc": "BC-03",
     "definition": "The record written when a milestone closes: what was learned, what surprised, what the "
                   "next milestone should do differently."},
    # ---- BC-04 Presentation ----
    {"id": "UL-23", "term": "Embedded specification", "bc": "BC-04",
     "definition": "The complete machine-readable content of a document, carried as one JSON object inside the "
                   "rendered file itself — the single source the human view is built from."},
    {"id": "UL-24", "term": "Self-contained", "bc": "BC-04",
     "definition": "Opens and functions as one file: no build step, no server, no installation, no network "
                   "beyond optional web fonts."},
    {"id": "UL-25", "term": "Review state", "bc": "BC-04",
     "definition": "A reader's private ticked-off progress through a document, stored in their browser under "
                   "the document's namespace. Never part of the specification."},
]

RULES = [
    {"title": "One term per concept", "text": "Where two terms compete, one is canonical and the rest are "
     "recorded as retired synonyms. Retired synonyms never appear in later documents."},
    {"title": "The glossary is upstream", "text": "Every document downstream of this one uses these terms with "
     "these meanings. A downstream document that needs a missing term adds it here first, as a forward-only "
     "amendment — it never defines a term locally."},
    {"title": "Boundary shifts are explicit", "text": "A term that changes meaning across a context boundary "
     "says so in its glossary entry. If a shift is discovered later, it is recorded here, not worked around."},
    {"title": "Test names speak the language", "text": "Automated tests, commit messages and worker reports use "
     "canonical terms, so a failing test names its concept unambiguously."},
    {"title": "Additions are cheap, renames are not", "text": "Adding a term is a normal amendment. Renaming a "
     "published term requires retiring it in place with a pointer to its successor — the same rule as for "
     "identifiers."},
]
