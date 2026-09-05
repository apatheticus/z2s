# -*- coding: utf-8 -*-
"""Generate the Zero-to-Ship document set.

Reads the specification modules, computes everything derivable (coverage, waves,
traceability matrix, rollups), and emits eleven self-contained HTML documents.

    python3 generate.py

Nothing here is authored twice: each fact lives in exactly one module and every
cross-document view is computed at generation time.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.dirname(OUT)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import collections                                              # noqa: E402

import shell                                                    # noqa: E402
import coverage as COV                                          # noqa: E402

# The ONE import this generator takes from the toolchain, and the reason it is
# not a duplication of `docs/_build` onto `z2s/` (which the owner declined,
# 2026-08-14). What a prompt says is the one thing that must not be spelled
# twice: a published prompt and a generated one that disagree would each be
# claiming to be the method. `z2s/gauntlet.py` is a leaf — it imports the
# safety rules and the schema and nothing else — so nothing about this
# generator's independence changes (M14-01).
from z2s import gauntlet                                        # noqa: E402
from specs import intent, context, prd, fsd, stories, sdd      # noqa: E402
from specs import plan_spine, brief, playbook, build             # noqa: E402

DETAIL = COV.DETAIL

FILES = {
    "index":     "index.html",
    "brief":     "Z2S-Brief.html",
    "playbook":  "Z2S-Playbook.html",
    "intent":    "Z2S-Intent.html",
    "context":   "Z2S-Context.html",
    "prd":       "Z2S-PRD.html",
    "stories":   "Z2S-User-Stories.html",
    "fsd":       "Z2S-FSD.html",
    "sdd":       "Z2S-SDD.html",
    "plan":      "Z2S-Plan.html",
    "build":     "Z2S-Build.html",
}

#: Pages that used to exist under another name. Each is GENERATED as a redirect
#: to its successor (ADR-02: nothing under docs/ is hand-written), so a link
#: published before the rename keeps resolving. The first document was called
#: Vision until set 2.9.
MOVED = {"Z2S-Vision.html": FILES["intent"]}

REDIRECT = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
            '<meta http-equiv="refresh" content="0; url=%(to)s">\n'
            '<link rel="canonical" href="%(to)s">\n<title>Moved to %(to)s</title></head>\n'
            '<body><p>This document is now <a href="%(to)s">%(to)s</a>.</p></body></html>\n')

NAV = [
    ("index", "Overview"), ("brief", "Brief"), ("playbook", "Playbook"), ("intent", "Intent"),
    ("context", "Context"), ("prd", "PRD"), ("fsd", "FSD"), ("stories", "Stories"),
    ("sdd", "SDD"), ("plan", "Plan"), ("build", "Build"),
]

#: How many files the plan is written across: the index, plus one page per
#: milestone. Derived rather than written down, because it was written down —
#: "fifteen" in three separate sentences, already wrong at sixteen milestones
#: and wrong again at seventeen. A number in prose that nothing computes is a
#: number that goes stale the next time the thing it counts changes.
PLAN_FILES = len(plan_spine.MILESTONES) + 1

#: The plan is ONE document written across an index and one page per milestone
#: (FR-SPC-09) — a count nobody has to maintain, since it comes from the spine. It used to be a single file, which the "how to
#: read this plan" section apologised for in writing; the apology is gone
#: because the thing it apologised for is gone.
#:
#: Flat filenames beside the other nine, deliberately: no new directory means no
#: relative-path class of bug and nothing to configure in Pages (M15-02).
PLAN_PAGES = {m["id"]: "Z2S-Plan-%s.html" % m["id"] for m in plan_spine.MILESTONES}

# Prefix -> the document that defines identifiers with that prefix. Two-segment
# prefixes are tried first, then one-segment (so ADR-01 routes via "ADR").
LINKS = {
    "FR": FILES["fsd"], "NFR": FILES["sdd"], "ADR": FILES["sdd"],
    "US": FILES["stories"], "UC": FILES["stories"],
    "VC": FILES["intent"], "VS": FILES["intent"], "SH": FILES["intent"],
    "BC": FILES["context"], "UL": FILES["context"],
    "G": FILES["prd"], "NG": FILES["prd"], "MT": FILES["prd"], "J": FILES["prd"], "RK": FILES["prd"],
}
# Every plan identifier at every level routes to the page that carries it, with
# no new code: the runtime tries the two-segment prefix and then the one-segment
# one, so M3-P2-T4 falls back to M3, and an identifier defined on the page the
# reader is already holding still wins and stays a local anchor.
LINKS.update(PLAN_PAGES)


def siblings(current):
    return [{"label": lbl, "href": FILES[k], "current": k == current} for k, lbl in NAV]


def plan_parts(current):
    """The plan's own parts, for the left-hand rail (FR-SPC-09).

    Kept apart from `siblings`, which is the eleven-document set. Putting fourteen
    milestones into that list would put them into every other document's
    navigation too, where they mean nothing.
    """
    parts = [{"label": "Plan index", "href": FILES["plan"], "current": current is None}]
    for m in plan_spine.MILESTONES:
        parts.append({"label": m["id"], "href": PLAN_PAGES[m["id"]],
                      "current": m["id"] == current})
    return parts


# A key whose empty value is a statement rather than an omission: "this task
# waits for nothing" is a fact, and dropping it makes it look unanswered.
KEEP_EMPTY = ("dependsOn",)

# Closed-set values are stored as ids and read as words. Every document carries
# the maps so a chip reads the same as the legend table that defines it — one
# source, derived here, never retyped in the runtime. Kept as separate sets on
# purpose: "auto" is an autonomy class and a criterion kind, and it means a
# different word in each.
LABELS = {name: {one["id"]: one["label"] for one in plan_spine.LEGEND[name]}
          for name in ("autonomy", "layers", "testLayers", "criterionKinds")}


def prune(value):
    """Drop every empty list or dict from a spec, at any depth.

    NFR-DAT-06: a heading over nothing is absent, never present and empty. The
    rule used to be applied to whole sections only, which left an empty `items`
    on a card and an empty `mono` on a table — both a promise of content the
    reader never gets.

    Only containers are dropped. An empty string stays: a table's first column
    heading is deliberately blank, and removing it would shift every column.
    """
    def hollow(child):
        return child is None or (isinstance(child, (list, dict)) and not child)

    if isinstance(value, dict):
        kept = {}
        for key, child in value.items():
            if key in KEEP_EMPTY:
                kept[key] = child
                continue
            child = prune(child)
            if not hollow(child):
                kept[key] = child
        return kept
    if isinstance(value, list):
        return [child for child in (prune(one) for one in value) if not hollow(child)]
    return value


def envelope(doc, current, sections):
    # NFR-DAT-06: a section with no content is absent, never present and empty.
    sections = [s for s in sections
                if not any(k in s and not s[k] for k in ("items", "rows", "groups"))]
    sections = prune(sections)
    spec = {"document": doc, "schemaVersion": "1.0", "sections": sections,
            "siblings": siblings(current), "links": LINKS, "labels": LABELS}
    return spec


def machine(intro=None):
    s = {"id": "machine", "type": "machine", "title": "Machine-readable specification"}
    if intro:
        s["intro"] = intro
    return s


# ---------------------------------------------------------------------------
# Intent
# ---------------------------------------------------------------------------
def build_intent():
    S = [
        {"id": "problem", "type": "prose", "title": "The problem", **intent.PROBLEM},
        {"id": "intent", "type": "prose", "title": "Intent statement",
         "body": [intent.INTENT_STATEMENT],
         "note": {"kind": "ok", "label": "In short.",
                  "text": "Store each fact once. Derive everything else. Let the build prove it."}},
        {"id": "ambition", "type": "list", "title": "What that makes possible",
         "items": intent.AMBITION},
        {"id": "principles", "type": "defs", "title": "Principles",
         "intro": "These constrain every later decision. Where a principle and a convenience conflict, the "
                  "principle wins or is explicitly amended — never quietly set aside.",
         "items": [{"term": p["name"], "def": p["desc"]} for p in intent.PRINCIPLES]},
        {"id": "stakeholders", "type": "table", "title": "Stakeholders",
         "columns": ["ID", "Stakeholder", "Type", "What they need", "Their role"],
         "mono": [0],
         "rows": [[s["id"], "**%s**" % s["name"], s["type"], s["interest"], s["role"]]
                  for s in intent.STAKEHOLDERS]},
        {"id": "personas", "type": "cards", "title": "Personas", "cols": "g2",
         "items": [{"kicker": p["tier"], "title": p["name"], "text": p["desc"],
                    "items": ["**Wants:** " + "; ".join(p["goals"]), "**Hurts:** " + "; ".join(p["pains"])]}
                   for p in intent.PERSONAS]},
        {"id": "capabilities", "type": "cards", "title": "Capabilities", "cols": "g2",
         "lede": "The ten things the method must be able to do. Every goal in the product requirements traces to "
                 "one of these.",
         "items": [{"id": c["id"], "title": c["name"], "text": c["desc"]} for c in intent.CAPABILITIES]},
        {"id": "scenarios", "type": "cards", "title": "Scenarios", "cols": "g2",
         "lede": "What it looks like when it works.",
         "items": [{"id": s["id"], "kicker": s["persona"], "title": s["title"], "text": s["narrative"],
                    "traces": {"cap": s["touches"]}} for s in intent.SCENARIOS]},
        {"id": "constraints", "type": "list", "title": "Constraints and limits",
         "intro": "Including the ones that are uncomfortable.", "items": intent.CONSTRAINTS},
        machine(),
    ]
    return envelope(intent.DOC, "intent", S)


# ---------------------------------------------------------------------------
# Context & ubiquitous language
# ---------------------------------------------------------------------------
def build_context():
    by_bc = {}
    for t in context.GLOSSARY:
        by_bc.setdefault(t["bc"], []).append(t)
    bc_name = {c["id"]: c["name"] for c in context.CONTEXTS}
    S = [
        {"id": "purpose", "type": "prose", "title": "Purpose", "body": context.PURPOSE,
         "highlights": [
             {"label": "Glossary", "title": "%d terms" % len(context.GLOSSARY),
              "text": "Across %d bounded contexts — each term one definition, in the reader's words."
                      % len(context.CONTEXTS)},
             {"label": "Scope", "title": "Self-demonstrating",
              "text": "This set applies the context step to the method's own domain, so this glossary is the "
                      "vocabulary every other document here uses."},
         ],
         "note": {"kind": "info", "label": "Position in the chain.",
                  "text": "Generated after the [Intent](Z2S-Intent.html) and before the "
                          "[product requirements](Z2S-PRD.html). Every downstream document consults this "
                          "glossary; a term it lacks is added here first, forward-only."}},
        {"id": "derivation", "type": "flow", "title": "How the language is derived",
         "flows": [context.DERIVATION_FLOW]},
        {"id": "contexts", "type": "cards", "title": "Bounded contexts", "cols": "g2",
         "badge": "%d contexts" % len(context.CONTEXTS),
         "lede": "Where the same word may carry different meanings, the boundary between meanings is drawn "
                 "here — explicitly, once.",
         "items": [{"id": c["id"], "title": c["name"], "text": c["desc"],
                    "items": ["**Owns:** " + ", ".join(c["owns"])]} for c in context.CONTEXTS]},
        {"id": "map", "type": "flow", "title": "Context map", "flows": [context.CONTEXT_MAP]},
        {"id": "glossary", "type": "cards", "title": "Ubiquitous language", "cols": "g2",
         "badge": "%d terms" % len(context.GLOSSARY),
         "lede": "Filter with the box in the header, or press the slash key. Each term links to its owning "
                 "bounded context.",
         "items": [{"id": t["id"], "kicker": bc_name[t["bc"]], "title": t["term"],
                    "text": t["definition"], "items": t.get("notes", []),
                    "traces": {"bc": [t["bc"]]}} for t in context.GLOSSARY]},
        {"id": "rules", "type": "defs", "title": "Rules of use",
         "intro": "What keeps the language ubiquitous once it is published.",
         "items": [{"term": r["title"], "def": r["text"]} for r in context.RULES]},
        machine(),
    ]
    return envelope(context.DOC, "context", S)


# ---------------------------------------------------------------------------
# Product requirements
# ---------------------------------------------------------------------------
def build_prd():
    S = [
        {"id": "summary", "type": "prose", "title": "Summary", "body": prd.SUMMARY},
        {"id": "goals", "type": "cards", "title": "Goals", "cols": "g2",
         "lede": "Each goal traces to the intent capability it serves.",
         "items": [{"id": g["id"], "title": g["text"], "traces": g["traces"]} for g in prd.GOALS]},
        {"id": "nongoals", "type": "list", "title": "Non-goals",
         "intro": "Recorded as decisions, not omissions, so they are not revisited by default.",
         "items": [{"title": n["id"], "text": n["text"]} for n in prd.NON_GOALS]},
        {"id": "journeys", "type": "cards", "title": "Journeys", "cols": "g2",
         "items": [{"id": j["id"], "kicker": j["persona"], "title": j["title"], "items": j["steps"],
                    "traces": j["traces"]} for j in prd.JOURNEYS]},
        {"id": "metrics", "type": "table", "title": "How success is measured",
         "intro": "Every measure is either a count that should be zero or a trend that should move. None of them "
                  "is a subjective assessment.",
         "columns": ["ID", "Measure", "Kind", "Target", "Goal"], "mono": [0],
         "rows": [[m["id"], "**%s**" % m["name"], m["kind"], m["target"],
                   " ".join("[%s](%s#%s)" % (g, FILES["prd"], g) for g in m["traces"]["goal"])]
                  for m in prd.METRICS]},
        {"id": "shape", "type": "table", "title": "Release shape",
         "intro": "The order in which the toolchain becomes useful. Each block delivers value before the next "
                  "begins.",
         "columns": ["ID", "Block", "Delivers", "Milestones", "Priority"], "mono": [0, 3],
         "rows": [[r["id"], "**%s**" % r["name"], r["goal"], r["includes"], r["moscow"]]
                  for r in prd.RELEASE_SHAPE]},
        {"id": "dependencies", "type": "list", "title": "Dependencies", "items": prd.DEPENDENCIES},
        {"id": "assumptions", "type": "list", "title": "Assumptions",
         "intro": "If one of these is false for your team, the method will underperform in a predictable way.",
         "items": prd.ASSUMPTIONS},
        {"id": "risks", "type": "table", "title": "Risks",
         "columns": ["ID", "Risk", "Mitigation"], "mono": [0],
         "rows": [[r["id"], r["risk"], r["mitigation"]] for r in prd.RISKS]},
        {"id": "questions", "type": "list", "title": "Open questions",
         "intro": "Recorded rather than answered by invention.", "items": prd.OPEN_QUESTIONS},
        machine(),
    ]
    return envelope(prd.DOC, "prd", S)


# ---------------------------------------------------------------------------
# Functional specification
# ---------------------------------------------------------------------------
def build_fsd():
    counts = {}
    for r in fsd.REQUIREMENTS:
        counts[r["priority"]] = counts.get(r["priority"], 0) + 1
    S = [
        {"id": "purpose", "type": "prose", "title": "Purpose",
         "body": [
             "This document states what the Zero-to-Ship toolchain must do, as prioritised, individually "
             "testable requirements. It is the document every downstream artefact traces to: each story covers "
             "one or more requirements here, each technical requirement is motivated by one, and each unit of "
             "work in the plan claims one. A requirement that appears in no plan task fails the build.",
             "Priorities follow the usual four bands. **Must** is required for this release; **Should** is "
             "important but not vital; **Could** is desirable if time allows; **Won't** records a deliberate "
             "exclusion so the decision survives and is not revisited by default.",
         ],
         "highlights": [
             {"label": "Catalogue", "title": "%d requirements" % len(fsd.REQUIREMENTS),
              "text": "Across %d areas — %d Must, %d Should, %d Could, %d deliberately excluded."
                      % (len(fsd.AREAS), counts.get("Must", 0), counts.get("Should", 0),
                         counts.get("Could", 0), counts.get("Won't", 0))},
             {"label": "Traces", "title": "Upward only",
              "text": "Each requirement is claimed by plan tasks and covered by stories; it never references "
                      "them, so downstream change cannot invalidate it."},
         ]},
        {"id": "dimensions", "type": "defs", "title": fsd.DIMENSIONS_META["title"],
         "intro": fsd.DIMENSIONS_META["intro"],
         "items": [{"term": d["name"], "def": d["desc"]} for d in fsd.DIMENSIONS]},
        {"id": "flows", "type": "flow", "title": "Key flows", "flows": fsd.FLOWS},
        {"id": "requirements", "type": "requirements", "title": "Requirements catalogue", "flush": False,
         "badge": "%d entries" % len(fsd.REQUIREMENTS),
         "lede": "Filter with the box in the header, or press the slash key. Toggle a priority band to narrow "
                 "further. Tick an entry to track a review pass — that state stays in your browser and never "
                 "enters the specification.",
         "areas": fsd.AREAS, "items": fsd.REQUIREMENTS},
        {"id": "assumptions", "type": "list", "title": "Assumptions", "items": fsd.ASSUMPTIONS},
        {"id": "questions", "type": "list", "title": "Open questions", "items": fsd.OPEN_QUESTIONS},
        machine(),
    ]
    return envelope(fsd.DOC, "fsd", S)


# ---------------------------------------------------------------------------
# Stories & use cases
# ---------------------------------------------------------------------------
def build_stories():
    matrix = COV.story_matrix()
    fr_title = {r["id"]: r["title"] for r in fsd.REQUIREMENTS}
    rows = []
    for r in fsd.REQUIREMENTS:
        covers = matrix.get(r["id"], [])
        rows.append([
            "[%s](%s#%s)" % (r["id"], FILES["fsd"], r["id"]),
            fr_title[r["id"]],
            r["priority"],
            " ".join("[%s](#%s)" % (c, c) for c in covers) if covers
            else ("_excluded_" if r["priority"] == "Won't" else "**none**"),
        ])
    S = [
        {"id": "howto", "type": "prose", "title": "How to use this document",
         "body": [
             "This document turns the functional requirements into stories with acceptance criteria precise "
             "enough to drive automated tests. It does not restate the functional or technical specifications — "
             "it **traces** to them.",
             "**As a developer or tester:** pick a story, implement to its scenarios, and name each test for the "
             "scenario identifier it verifies. The story is done when every scenario and every 'also verify' "
             "check passes.",
             "**As an agent:** each scenario is a Given/When/Then triple with a stable identifier. Treat the "
             "'then' clause as the assertion. Where behaviour is non-deterministic, assert on structure and "
             "required elements — never on exact generated wording.",
         ],
         "note": {"kind": "info", "label": "Coverage.",
                  "text": "The [traceability matrix](#matrix) maps every functional requirement to the stories "
                          "and use cases that cover it. Nothing except an explicit exclusion is left uncovered."}},
        {"id": "roles", "type": "table", "title": "Roles",
         "columns": ["Role", "Summary", "Can"],
         "rows": [["**%s**" % r["name"], r["summary"], r["can"]] for r in stories.ROLES]},
        {"id": "global", "type": "list", "title": "Global acceptance",
         "intro": "These apply to every story unless it explicitly opts out with a recorded reason. Verify once "
                  "per surface; do not re-author them per story.",
         "items": stories.GLOBAL_ACCEPTANCE},
        {"id": "stories", "type": "stories", "title": "User stories",
         "badge": "%d stories" % len(stories.STORIES), "items": stories.STORIES},
        {"id": "usecases", "type": "usecases", "title": "Use cases",
         "badge": "%d use cases" % len(stories.USE_CASES),
         "lede": "Actor-centred flows that span several stories, where the interaction — not the capability — is "
                 "what needs specifying.",
         "items": stories.USE_CASES},
        {"id": "matrix", "type": "table", "title": "Traceability matrix",
         "intro": "Derived at generation time from the stories' own traces. Never maintained by hand — which is "
                  "why it cannot be out of date.",
         "columns": ["Requirement", "Title", "Priority", "Covered by"], "mono": [0],
         "rows": rows},
        machine(),
    ]
    return envelope(stories.DOC, "stories", S)


# ---------------------------------------------------------------------------
# System design
# ---------------------------------------------------------------------------
def build_sdd():
    S = [
        {"id": "principles", "type": "defs", "title": "Design principles",
         "intro": "Six rules that decide every ambiguous technical question below.",
         "items": [{"term": p["name"], "def": p["desc"]} for p in sdd.PRINCIPLES]},
        {"id": "stack", "type": "table", "title": "Composition",
         "intro": "Deliberately small. Every choice below is either a plain file or a script with no third-party "
                  "dependency.",
         "columns": ["Layer", "Choice", "Role"],
         "rows": [[s["layer"], "**%s**" % s["choice"], s["role"]] for s in sdd.STACK]},
        {"id": "components", "type": "cards", "title": "Components", "cols": "g2",
         "items": [{"kicker": c["kind"], "title": c["name"], "text": c["responsibilities"]}
                   for c in sdd.COMPONENTS]},
        {"id": "data", "type": "cards", "title": "Data model", "cols": "g2",
         "items": [{"title": d["name"], "items": d["points"]} for d in sdd.DATA_MODEL]},
        {"id": "schemas", "type": "code", "title": "Data contracts",
         "intro": "The complete shape of every specification object the toolchain reads or writes. An "
                  "implementation that satisfies these contracts is interoperable with the rest of the method.",
         "blocks": sdd.SCHEMAS},
        {"id": "algorithms", "type": "code", "title": "Algorithms and layout",
         "intro": "The behaviour that must be reproduced exactly, stated as pseudocode rather than as prose so "
                  "there is nothing to interpret.",
         "blocks": sdd.ALGORITHMS},
        {"id": "crosscutting", "type": "cards", "title": "Cross-cutting concerns", "cols": "g2",
         "items": [{"title": c["name"], "items": c["points"]} for c in sdd.CROSSCUTTING]},
        {"id": "decisions", "type": "decisions", "title": "Architecture decisions",
         "badge": "%d decisions" % len(sdd.DECISIONS),
         "lede": "Each records the context that forced a choice, the choice, what was rejected, and what was "
                 "accepted as a consequence — so a future reader can judge whether the reasoning still holds.",
         "items": sdd.DECISIONS},
        {"id": "requirements", "type": "requirements", "title": "Technical requirements",
         "badge": "%d entries" % len(sdd.REQUIREMENTS),
         "areas": sdd.REQ_AREAS, "items": sdd.REQUIREMENTS},
        {"id": "targets", "type": "table", "title": "Targets",
         "intro": "Numbers, not adjectives — so each can become a machine-checkable acceptance criterion.",
         "columns": ["Metric", "Target", "Notes"], "mono": [1],
         "rows": [[t["metric"], "**%s**" % t["target"], t["notes"]] for t in sdd.TARGETS]},
        {"id": "risks", "type": "table", "title": "Technical risks",
         "columns": ["Risk", "Mitigation"],
         "rows": [[r["risk"], r["mitigation"]] for r in sdd.RISKS]},
        {"id": "questions", "type": "list", "title": "Open questions", "items": sdd.OPEN_QUESTIONS},
        machine(),
    ]
    return envelope(sdd.DOC, "sdd", S)


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------
def waves():
    """Topological wave ordering — derived, never authored."""
    done, out = set(), []
    remaining = {m["id"]: set(m["dependsOn"]) for m in plan_spine.MILESTONES}
    while remaining:
        w = sorted(i for i, deps in remaining.items() if deps <= done)
        if not w:
            raise SystemExit("dependency cycle among: %s" % ", ".join(sorted(remaining)))
        out.append(w)
        done |= set(w)
        for i in w:
            del remaining[i]
    return out


def catalog():
    c = {}
    for r in fsd.REQUIREMENTS:
        c[r["id"]] = r["title"]
    for r in sdd.REQUIREMENTS:
        c[r["id"]] = r["title"]
    for d in sdd.DECISIONS:
        c[d["id"]] = d["title"]
    for s in stories.STORIES:
        c[s["id"]] = s["title"]
    for u in stories.USE_CASES:
        c[u["id"]] = u["title"]
    return c


#: What every published prompt states as settled. The real locked decisions for
#: this project live in a run ledger nobody publishes, so the prompts point at
#: what a reader actually has: the architecture decisions, which ARE published,
#: with their identifiers. Naming all nineteen in full would add about 4.5 KB to
#: each of the 173 prompts and say nothing the linked document does not.
Settled = collections.namedtuple("Settled", "question choice")


def settled():
    return [("sdd", Settled(
        "Where the decisions you must not re-open are written down",
        "Every ADR in %s, and every locked decision recorded in this project's "
        "run ledger. Read them before deciding anything they cover: %s."
        % (FILES["sdd"], ", ".join(d["id"] for d in sdd.DECISIONS))))]


#: The commands a unit must pass, as this project actually runs them.
GAUNTLET = [
    "unit  python3 -m unittest discover -s tests",
    "CI    python3 -m z2s.pipeline --record .",
    "lint  python3 docs/_build/check.py",
]


def plan_prompts():
    """One prompt for the build, and one for every milestone, phase and task.

    Real ones, generated by the same module the toolchain generates a project's
    own with (M14-01, M14-04) — so what this site publishes as the method is the
    method, rather than a description of it that drifted.
    """
    titles = catalog()
    decisions = settled()
    found = collections.OrderedDict()

    every = [dict(t, id=t["id"]) for ms in DETAIL.values() for ph in ms
             for t in ph.get("tasks", [])]
    found[gauntlet.WHOLE] = gauntlet.assemble(
        "plan", FILES["plan"], decisions, GAUNTLET,
        bar=["Every milestone reaches passing, and the coverage gate passes."],
        aiming=gauntlet.ceiling({"traces": gauntlet.merged_traces(every)}, titles),
        closing=["Wave %d: %s" % (n + 1, ", ".join(w)) for n, w in enumerate(waves())])

    for m in plan_spine.MILESTONES:
        phases = DETAIL.get(m["id"], [])
        within = [t for ph in phases for t in ph.get("tasks", [])]
        found[m["id"]] = gauntlet.assemble(
            "milestone", FILES["plan"], decisions, GAUNTLET,
            unit=m["id"], title=m["title"],
            waits=list(m.get("dependsOn") or ()),
            bar=["Done when: %s" % line for line in m.get("exit") or ()],
            aiming=gauntlet.ceiling({"traces": gauntlet.merged_traces(within)}, titles),
            closing=[m.get("goal") or m["title"]])
        for ph in phases:
            tasks = ph.get("tasks", [])
            found[ph["id"]] = gauntlet.assemble(
                "phase", FILES["plan"], decisions, GAUNTLET,
                unit=ph["id"], title=ph["title"],
                waits=list(ph.get("dependsOn") or ()),
                bar=["Done when: %s" % line for line in ph.get("completion") or ()],
                aiming=gauntlet.ceiling({"traces": gauntlet.merged_traces(tasks)}, titles),
                closing=[ph.get("summary") or ph["title"]])
            for t in tasks:
                found[t["id"]] = gauntlet.assemble(
                    "task", FILES["plan"], decisions, GAUNTLET,
                    unit=t["id"], title=t["title"],
                    waits=list(t.get("dependsOn") or ()),
                    bar=gauntlet.criteria_lines(t),
                    aiming=gauntlet.ceiling(t, titles),
                    entry=t,
                    closing=gauntlet.unit_lines(
                        dict(t, text=t.get("summary") or t["title"])))
    return found


def unit_link(unit):
    """A plan identifier, linked to the milestone page that carries it."""
    return "[%s](%s#%s)" % (unit, PLAN_PAGES.get(unit.split("-")[0], FILES["plan"]), unit)


def milestone_doc(m):
    """One milestone page's envelope — the plan's own, narrowed to this part."""
    doc = dict(plan_spine.DOC)
    doc.update({
        "title": "Zero-to-Ship — %s: %s" % (m["id"], m["title"]),
        "kicker": "Plan · %s of %d" % (m["id"], len(plan_spine.MILESTONES)),
        "releaseScope": "One milestone of the development plan",
        "summary": m.get("goal") or m["title"],
        "scopeNote": "This is one part of the [development plan](%s), which is a single document "
                     "written across %d files. Use the plan navigation on the left to reach "
                     "any other milestone, or the index for the waves, the prerequisites and the "
                     "coverage matrix." % (FILES["plan"], PLAN_FILES),
        # Read by nothing in the runtime; it is here so a reader of the raw
        # specification can tell which part of the plan they are holding.
        "milestone": m["id"],
    })
    return doc


def build_plan():
    """The plan: an index and one document per milestone.

    Returns a list of pages rather than one specification, because the method
    prescribes one document per milestone and the published site now obeys it
    (FR-SPC-09). They share a slug, a legend and a catalogue: it is one document
    split for reading, not %d documents.
    """ % PLAN_FILES
    W = waves()
    PROMPTS = plan_prompts()
    uni, excluded = COV.universe()
    claims = COV.claims()
    kind_label = {"fr": "Functional", "nfr": "Technical", "adr": "Decision"}
    cov_rows = []
    for i in sorted(uni, key=lambda x: (uni[x][0], x)):
        kind, title = uni[i]
        cov_rows.append([
            "[%s](%s#%s)" % (i, LINKS[i.split("-")[0]], i),
            kind_label[kind], title,
            " ".join(unit_link(u) for u in claims.get(i, [])) or "**none**",
        ])
    for i in sorted(excluded):
        cov_rows.append(["[%s](%s#%s)" % (i, FILES["fsd"], i), "Excluded", excluded[i],
                         "_deliberate exclusion, recorded with its reason_"])

    ms_items = []
    for m in plan_spine.MILESTONES:
        item = dict(m, prompt=PROMPTS[m["id"]])
        phases = []
        for ph in DETAIL.get(m["id"], []):
            ph = dict(ph, prompt=PROMPTS[ph["id"]])
            # Schema default, materialised into the artefact: a task with no authored
            # status is "not-started". Status must be PRESENT in the rendered
            # specification — it is the field the write-back tool edits.
            ph["tasks"] = [dict(t, status=t.get("status", "not-started"),
                                prompt=PROMPTS[t["id"]])
                           for t in ph.get("tasks", [])]
            phases.append(ph)
        item["phases"] = phases
        ms_items.append(item)

    ntasks = sum(len(p.get("tasks", [])) for ms in DETAIL.values() for p in ms)
    ncrit = sum(len(t.get("criteria", [])) for ms in DETAIL.values() for p in ms for t in p.get("tasks", []))
    nauto = sum(1 for ms in DETAIL.values() for p in ms for t in p.get("tasks", [])
                for c in t.get("criteria", []) if c.get("kind") == "auto")

    status_label = {s["id"]: s["label"] for s in plan_spine.LEGEND["statuses"]}
    statuses = {s["id"]: {"label": s["label"], "tone": s["tone"]}
                for s in plan_spine.LEGEND["statuses"]}

    S = [
        {"id": "prompt", "type": "prompts", "title": "Copy a prompt to run this plan",
         "intro": "Every prompt here is complete: generated from this plan and the decisions already settled "
                  "above it, with nothing outside this repository assumed. Take the first one to hand over the "
                  "whole build in one go, or a milestone's to hand over that much. Prompts for a single phase or "
                  "a single task ride on that unit's own card, inside its milestone's page.",
         # `prompt-M1`, not `M1`: an item id IS an identifier declaration, and
         # M1 is declared by the page that carries the milestone. The unit each
         # prompt belongs to rides in `unit`, which declares nothing.
         "items": ([{"id": "prompt-%s" % gauntlet.WHOLE, "unit": gauntlet.WHOLE,
                     "title": "Run the entire plan in one go",
                     "body": PROMPTS[gauntlet.WHOLE]}] +
                   [{"id": "prompt-%s" % m["id"], "unit": m["id"],
                     "title": "Run %s — %s" % (m["id"], m["title"]),
                     "body": PROMPTS[m["id"]]} for m in plan_spine.MILESTONES])},

        {"id": "howto", "type": "prose", "title": "How to read this plan",
         "body": [
             "This is the index. Each milestone is its own page, listed in the plan navigation on the left and "
             "in the [milestones table](#milestones) below; the phases, tasks, failing tests and acceptance "
             "criteria live there. What stays here is everything that is about the plan as a whole: the "
             "execution prompts, the dependency waves, the prerequisites and the coverage proof.",
             "This plan was **generated**, not written. Its source is the milestone spine plus per-milestone "
             "detail files, combined with the functional and technical specifications' own embedded data. "
             "Generation fails if any requirement or decision is claimed by no unit of work — so the "
             "[coverage matrix](#coverage) below is a proof, not a summary.",
             "**Status lives in this file.** Each task's status and each criterion's state are stored in the "
             "embedded specification and written by the status tool. Nothing here is edited by hand: to change "
             "the plan, change its source and regenerate; to change status, run the status command.",
             "Every task states the failing test that proves it is needed before any code exists. That is what "
             "lets a worker with no context know exactly when the task is done.",
         ],
         "highlights": [
             {"label": "Scale", "title": "%d milestones · %d tasks" % (len(plan_spine.MILESTONES), ntasks),
              "text": "In %d dependency waves, with %d acceptance criteria (%d machine-checkable)."
                      % (len(W), ncrit, nauto)},
             {"label": "Coverage", "title": "%d of %d claimed" % (len(uni), len(uni)),
              "text": "Every functional requirement, technical requirement and architecture decision is claimed "
                      "by at least one unit of work. %d exclusions are recorded with reasons." % len(excluded)},
         ],
         "note": {"kind": "info", "label": "One honest deviation, recorded rather than hidden.",
                  "text": "Status here is the true state of the toolchain build, written by the status tool "
                          "rather than asserted — so a milestone reading **needs review** means a human-review "
                          "criterion is genuinely outstanding, and one reading **blocked** means work was "
                          "deliberately deferred. Nothing is marked done to make the page look finished."}},

        {"id": "legend", "type": "table", "title": "Status vocabulary",
         "intro": "A closed set. A value outside it is rejected by the write-back tool without modifying the "
                  "file.",
         "columns": ["Status", "Meaning"],
         "rows": [["**%s**" % s["label"], s["desc"]] for s in plan_spine.LEGEND["statuses"]]},

        {"id": "autonomy", "type": "table", "title": "Autonomy classes and verification layers",
         "intro": "Autonomy decides what an unattended run may attempt. Verification layers decide what "
                  "'passing' means for a given task.",
         "columns": ["Class or layer", "Kind", "Meaning"],
         "rows": ([["**%s**" % a["label"], "Autonomy", a["desc"]] for a in plan_spine.LEGEND["autonomy"]] +
                  [["**%s**" % k["label"], "Criterion", k["desc"]] for k in plan_spine.LEGEND["criterionKinds"]] +
                  [["**%s**" % t["label"], "Verification", "Named by tasks it proves."]
                   for t in plan_spine.LEGEND["testLayers"]])},

        {"id": "waves", "type": "waves", "title": "Parallel execution waves",
         "intro": "Derived from the dependency graph. Every milestone in a wave depends only on milestones in "
                  "earlier waves, so the members of a wave may run concurrently.",
         # Each scheduled milestone names the document that carries it. The
         # renderer does not read this map — every chip is already routed by the
         # links table — but the validator does: a plan split across files that
         # schedules a milestone with no readable document is a failure, and
         # this is the field that makes that check real rather than dormant.
         "files": dict(PLAN_PAGES),
         "waves": W},

        {"id": "prerequisites", "type": "table", "title": "Prerequisites",
         "intro": "Human-owned work, held separately from the plan. Each must be cleared, or its dependent tasks "
                  "classed human-gated, before an unattended run starts.",
         "columns": ["ID", "Prerequisite", "Owner"], "mono": [0],
         "rows": [[p["id"], p["text"], p["owner"]] for p in plan_spine.PREREQUISITES]},

        # A table of rows, never a catalogue of entries. Every phase, task and
        # criterion is declared on its own milestone page; repeating them here
        # would declare each identifier twice across the set, which the
        # validator reports as a duplicate — correctly.
        {"id": "milestones", "type": "table", "title": "Milestones",
         "badge": "%d milestones · %d tasks" % (len(plan_spine.MILESTONES), ntasks),
         "intro": "One page each. Open a milestone to read its phases, its tasks, the failing test that defines "
                  "each one, its acceptance criteria and its execution instructions.",
         "columns": ["ID", "Milestone", "Status", "Tasks passing", "Waits for"], "mono": [0, 3],
         "rows": [["[%s](%s)" % (m["id"], PLAN_PAGES[m["id"]]),
                   "[**%s**](%s)" % (m["title"], PLAN_PAGES[m["id"]]),
                   status_label.get(m.get("status", "not-started"), m.get("status", "not-started")),
                   "%d / %d" % (sum(1 for ph in DETAIL.get(m["id"], [])
                                    for t in ph.get("tasks", []) if t.get("status") == "passing"),
                                sum(len(ph.get("tasks", [])) for ph in DETAIL.get(m["id"], []))),
                   ", ".join(m.get("dependsOn") or ()) or "—"]
                  for m in plan_spine.MILESTONES]},

        {"id": "coverage", "type": "table", "title": "Coverage matrix",
         "intro": "Computed at generation time from the tasks' own traces. A row with no claiming unit fails "
                  "generation — this table cannot show one.",
         "badge": "%d identifiers" % (len(uni) + len(excluded)),
         "columns": ["Identifier", "Kind", "Title", "Claimed by"], "mono": [0],
         "rows": cov_rows},

        machine("The index carries the waves, the prerequisites and the coverage proof. Every milestone, phase, "
                "task and criterion — with its live status, which the status tool edits and the orchestrator "
                "reads — is in the specification block of that milestone's own page."),
    ]
    index = envelope(plan_spine.DOC, "plan", S)
    index["legend"] = plan_spine.LEGEND
    index["waves"] = W
    index["catalog"] = catalog()
    index["parts"] = plan_parts(None)

    pages = [(FILES["plan"], "plan-spec", index)]
    for m, item in zip(plan_spine.MILESTONES, ms_items):
        tasks = sum(len(ph.get("tasks", [])) for ph in DETAIL.get(m["id"], []))
        sections = [
            {"id": "milestones", "type": "milestones", "title": "Phases and tasks",
             "badge": "%d phases · %d tasks" % (len(item["phases"]), tasks),
             "lede": "Take the instructions at the top to hand this whole milestone over, or a phase's or a "
                     "task's to hand over less. Every task carries the failing test that defines it, its "
                     "acceptance criteria and the requirements it claims.",
             "statuses": statuses, "items": [item]},
            machine("This milestone, with every phase, task and criterion at its live status. This block is "
                    "what the status tool edits and what the orchestrator reads."),
        ]
        spec = envelope(milestone_doc(m), "plan", sections)
        spec["legend"] = plan_spine.LEGEND
        spec["catalog"] = index["catalog"]
        spec["parts"] = plan_parts(m["id"])
        pages.append((PLAN_PAGES[m["id"]], "plan-spec", spec))
    return pages


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------
def build_index():
    uni, excluded = COV.universe()
    ntasks = sum(len(p.get("tasks", [])) for ms in DETAIL.values() for p in ms)
    doc = {
        "title": "Zero-to-Ship — Document Set",
        "slug": "index",
        "kicker": "Overview",
        "type": "Document set index",
        "version": "2.13",
        "status": "Complete",
        "date": "2026-09-05",
        "owner": "Zerø Effort",
        "releaseScope": "Eleven documents",
        "summary": "The Zero-to-Ship (Z2S) Method, by Zerø Effort: a way of building software in which the "
                   "specification is the machine's input, the plan is derived from it, coverage is a build "
                   "failure rather than a hope, and progress is recorded in the same file that describes the "
                   "work.",
        "scopeNote": "Start with the Brief if you want to understand the method, the Playbook if you want to run "
                     "it, and the specification chain if you want to build the toolchain. The method is operated "
                     "through the /zero:* skill chain listed below.",
        "heroLogo": True,
    }
    S = [
        {"id": "summary", "type": "flow", "title": "Executive summary",
         "body": [
             "Zero-to-Ship exists to close the gap between what an organisation agreed to build and what it "
             "received. The specification is written once, in a form a person and a machine can both read. The "
             "plan is calculated from that specification rather than written alongside it. Progress is recorded "
             "in the document that describes the work, so there is no second record to fall out of date.",

             "All of it comes from one rule. Every fact belongs in exactly one place, and anything that needs "
             "that fact derives it. Drift between a specification and a build is the structural consequence of "
             "writing the same fact twice, and no amount of care prevents it, because the two copies are "
             "maintained by different people at different times. A coverage gate applies the rule while the plan "
             "is being generated. A requirement that no task schedules stops generation, and nothing is produced "
             "until somebody decides where that work belongs.",

             "For a leadership team the change is in which questions have answers. Whether everything agreed has "
             "been scheduled, and how much of it is finished, are commands that return a count. Today both come "
             "from asking people, and what comes back is an estimate. Expensive human attention moves to the "
             "front of the project, into the session where the open decisions are settled and written down. What "
             "follows is largely machine time, and it can run with little supervision because the standard it "
             "will be held to was fixed before it started.",

             "This document set is the method applied to itself: %d identifiers, every one claimed by a planned "
             "task, proved by the same gate any other project would face. Zero-to-Ship itself was extracted from "
             "the build of Zero Style, a web application specified, planned and largely built by AI agents "
             "working this way, and now in production. Read the [Method Brief](Z2S-Brief.html) to judge whether "
             "to adopt it, the [Operating Playbook](Z2S-Playbook.html) to run it, and [the build "
             "process](Z2S-Build.html) for the machinery that turns a finished plan into working "
             "software." % len(uni),
         ],
         "flows": [
             {"name": "Where the effort goes",
              "caption": "Only the first two steps take much of anyone's time. Everything after them is "
                         "calculated from what those two settled.",
              "steps": [
                  {"title": "What the business wants",
                   "desc": "A brief, a conversation, documents that already exist — in whatever form it arrives.",
                   "kind": "input"},
                  {"title": "Decisions taken once",
                   "desc": "Every open question put to the people who can answer it, and each answer written "
                           "down where the build will read it.", "kind": "gate"},
                  {"title": "One specification",
                   "desc": "Seven linked documents, each narrower than the last, with every fact recorded in "
                           "exactly one place."},
                  {"title": "A plan, derived",
                   "desc": "Milestones, phases and test-first tasks calculated from the specification, so the "
                           "two cannot disagree."},
                  {"title": "Coverage proved",
                   "desc": "A requirement no task schedules stops generation. Nothing falls off the list "
                           "quietly.", "kind": "gate"},
                  {"title": "Delivered, with evidence",
                   "desc": "The work runs largely unattended and writes its own status back into the plan that "
                           "describes it.", "kind": "accent"},
              ]},
         ]},
        {"id": "start", "type": "cards", "title": "Start here", "cols": "g4",
         "lede": "Four ways in, depending on what you need.",
         "items": [
             {"kicker": "Understand it", "title": "Method Brief", "href": "Z2S-Brief.html",
              "text": "The narrative explanation. Plain language first, technical depth after — including the "
                      "method run for real on a shipped product. Read this if you are deciding whether the "
                      "method is worth adopting, or explaining it to someone else."},
             {"kicker": "Run it", "title": "Operating Playbook", "href": "Z2S-Playbook.html",
              "text": "Six phases, numbered steps, one skill invocation per step, a gate and a stop condition "
                      "for each. Read this if the chain is installed and you need to operate the method."},
             {"kicker": "Look inside", "title": "The build process", "href": "Z2S-Build.html",
              "text": "The orchestrator in full: one unit from brief to commit, four workers running at once "
                      "without colliding, the verification layers in cost order, and what every bound costs "
                      "when it fires. Read this if you need to trust the run before you leave it alone."},
             {"kicker": "Build the toolchain", "title": "The specification chain", "href": "Z2S-FSD.html",
              "text": "Intent, context, product requirements, functional specification, stories, technical "
                      "specification and plan — everything needed to build the toolchain itself."},
         ]},
        {"id": "chain", "type": "flow", "title": "How the documents relate",
         "lede": "Each document answers a question the previous one raised. Traces run upward only, so changing "
                 "a downstream document can never invalidate an upstream one.",
         "flows": [
             {"name": "The specification chain",
              "caption": "The plan is derived from the functional and technical specifications, and fails to "
                         "generate if either contains a requirement it does not schedule.",
              "steps": [
                  {"title": "Intent", "desc": "Problem, principles, capabilities.", "kind": "input"},
                  {"title": "Context", "desc": "One shared vocabulary, scoped to bounded contexts."},
                  {"title": "PRD", "desc": "Goals, non-goals, measures."},
                  {"title": "FSD", "desc": "Functional requirements."},
                  {"branch": [
                      {"title": "Stories & use cases", "desc": "How each is verified."},
                      {"title": "SDD", "desc": "Technical requirements, decisions."},
                  ]},
                  {"title": "Plan", "desc": "Milestones, phases, tasks, status.", "kind": "accent"},
              ]},
         ]},
        {"id": "stats", "type": "stats", "title": "The set at a glance",
         "items": [
             {"value": "11", "label": "documents", "note": "Each self-contained, each rendering itself from its "
                                                           "own embedded data."},
             {"value": str(len(fsd.REQUIREMENTS)), "label": "functional requirements",
              "note": "Across %d areas, prioritised." % len(fsd.AREAS)},
             {"value": str(len(sdd.REQUIREMENTS)), "label": "technical requirements",
              "note": "Plus %d architecture decisions." % len(sdd.DECISIONS)},
             {"value": "%d / %d" % (len(stories.STORIES), len(stories.USE_CASES)),
              "label": "stories / use cases", "note": "Every requirement covered by at least one."},
             {"value": str(ntasks), "label": "planned tasks",
              "note": "In %d milestones, each defined by its failing test." % len(plan_spine.MILESTONES)},
             {"value": "%d/%d" % (len(uni), len(uni)), "label": "identifiers claimed",
              "note": "The coverage gate passes: nothing is scheduled nowhere."},
         ]},
        {"id": "skills", "type": "table", "title": "The skill chain",
         "intro": "The method is operated through named skills, installed as one plugin: "
                  "`/plugin marketplace add apatheticus/z2s`, then "
                  "`/plugin install zero@z2s` "
                  "(also at [github.com/apatheticus/z2s](https://github.com/apatheticus/z2s)). "
                  "Every skill is invoked deliberately — none fires on its own except `/zero:questions`, the "
                  "shared clarification interview. And no step asks you to run a shell command: every skill "
                  "performs its own mechanics, and `/zero:init` repairs missing setup whenever a chain skill "
                  "finds it.",
         "columns": ["Skill", "Does", "Requires"], "mono": [0],
         "rows": [
             ["/zero:init", "Sets the project up: the `.zero/` layout, ignore rules, theme detection, the "
              "verification gauntlet. Idempotent; every chain skill runs it automatically when setup is "
              "missing.", "Nothing — optional to run yourself"],
             ["/zero:design", "Reads the project's design system — stylesheets, token documents, a brand book, "
              "a `DESIGN.md` — and records what the documents are styled with, naming every value's source. "
              "Asks before adopting anything a document states only in prose.", "Nothing — optional to run "
              "yourself"],
             ["/zero:intent", "Derives the intent from any mix of narrative, documents and web addresses; "
              "maintains the source register.", "Nothing — start here"],
             ["/zero:context", "Establishes the ubiquitous language: glossary, bounded contexts, context map.",
              "Completed Intent"],
             ["/zero:prd", "Generates the product requirements.", "Completed Context"],
             ["/zero:fsd", "Generates the functional specification.", "Completed PRD"],
             ["/zero:stories", "Generates user stories and use cases.", "Completed FSD"],
             ["/zero:sdd", "Generates the technical design.", "Completed FSD"],
             ["/zero:plan", "Derives the plan and proves coverage.", "Completed Stories, FSD and SDD"],
             ["/zero:build", "Works through the plan's build prompts wave by wave: dispatches a worker per "
              "ready unit, runs the verification gauntlet itself rather than believing a report, and has a "
              "second worker judge the result without ever seeing how it was made.", "A validated plan"],
             ["/zero:prompt", "Prints the instructions for one unit of the plan — a task, a phase, a "
              "milestone, or the whole build — so they can be pasted into a fresh session or handed to "
              "somebody else. Read-only.", "A generated plan"],
             ["/zero:action", "Resumes from wherever the set stands; starts from the beginning if no Intent.",
              "Nothing"],
             ["/zero:update", "Folds additions and changes in, forward-only — never deletes or overwrites.",
              "The document it updates"],
             # Text copied verbatim from `steps.OPERATIONS`'s `feature` summary in
             # z2s/steps.py — copied rather than imported, because this generator
             # takes exactly one import from the toolchain (see the note above the
             # gauntlet import) and a second one would make the published set
             # depend on the thing it describes.
             ["/zero:feature", "Opens the next feature, or closes the open one after an audit. One feature "
              "is open at a time; its documents, plan and run state live under .zero/features/.",
              "Completed Intent and Context"],
             ["/zero:ship", "Commits and pushes the working branch; asks before opening a pull request.",
              "A working branch"],
             ["/zero:questions", "The shared clarification interview every other skill routes questions "
              "through. The only skill that may trigger automatically.", "—"],
         ]},
        {"id": "documents", "type": "table", "title": "The eleven documents",
         "columns": ["Document", "Type", "Answers", "Identifiers"], "mono": [3],
         "rows": [
             ["[Overview](index.html)", "Index", "Where to start and how the set fits together.", "—"],
             ["[Method Brief](Z2S-Brief.html)", "Briefing",
              "What problem this solves, how it works, what it costs.", "—"],
             ["[Operating Playbook](Z2S-Playbook.html)", "Manual",
              "How to run the method, step by step, with gates and stop conditions.", "S-A1 … S-F4"],
             ["[Intent](Z2S-Intent.html)", "Intent",
              "Why the method exists and the principles that constrain it.", "VC-\\*, VS-\\*, SH-\\*"],
             ["[Context](Z2S-Context.html)", "Context",
              "What every term means — one definition, scoped to bounded contexts.", "BC-\\*, UL-\\*"],
             ["[Product requirements](Z2S-PRD.html)", "PRD",
              "What it must achieve, what it will not do, how success is measured.", "G-\\*, NG-\\*, MT-\\*"],
             ["[Functional specification](Z2S-FSD.html)", "FSD",
              "Exactly what the toolchain does, as testable requirements.", "FR-\\*"],
             ["[Stories & use cases](Z2S-User-Stories.html)", "Acceptance",
              "How each requirement is proven.", "US-\\*, UC-\\*"],
             ["[System design](Z2S-SDD.html)", "SDD",
              "How it is built — contracts, schemas, algorithms, decisions.", "NFR-\\*, ADR-\\*"],
             ["[Development plan](Z2S-Plan.html)", "Plan",
              "The buildable plan for the toolchain, with live status. One document, written across an index "
              "and one page per milestone.", "M\\*-P\\*-T\\*"],
             ["[The build process](Z2S-Build.html)", "Process reference",
              "What the orchestrator does with a plan once it is derived, and what every bound in it costs.",
              "—"],
         ]},
        {"id": "conventions", "type": "defs", "title": "Conventions used throughout",
         "items": [
             {"term": "Identifiers are permanent",
              "def": "Never reused, never renumbered. Gaps in numbering are expected — a retired item keeps its "
                     "number so that every existing trace, test name and reference stays valid."},
             {"term": "Traces run upward",
              "def": "A downstream item names what it satisfies. Upstream items never reference downstream ones, "
                     "so downstream change cannot invalidate them."},
             {"term": "Every document embeds its own data",
              "def": "The readable view you are looking at was generated from it when you opened the file. Use "
                     "the copy or download action in any document's final section to extract it."},
             {"term": "Priorities",
              "def": "**Must** — required for this release. **Should** — important, not vital. **Could** — "
                     "desirable if time allows. **Won't** — deliberately excluded, recorded so the decision is "
                     "not revisited by default."},
             {"term": "A document may be written across several files",
              "def": "The plan is one document in %d files — an index and one page per milestone — because "
                     % PLAN_FILES +
                     "a plan is navigated rather than read end to end. It shares one vocabulary, one legend and "
                     "one coverage proof; the plan navigation on the left of any of its pages reaches all the "
                     "others."},
             {"term": "Nothing here is hand-edited",
              "def": "All eleven documents are generated from source modules. To change one, change its source and "
                     "regenerate."},
         ]},
        {"id": "provenance", "type": "prose", "title": "Where the method comes from",
         "body": [
             "Zero-to-Ship was extracted from the build of **Zero Style**, a working web application — a "
             "design-terminology dictionary paired with a plain-language-to-design-brief converter — specified, "
             "planned and largely built by AI agents operating this method: 72 functional and 85 technical "
             "requirements with 17 recorded architecture decisions, a derived plan that grew to 16 milestones "
             "and 299 test-first tasks (295 passing at the time of writing), later scope arriving as addenda "
             "with no identifier ever renumbered, and the result live in production. The "
             "[Brief](Z2S-Brief.html#proof) tells that story in full.",
             "This document set is the second run of the same discipline: generated from embedded data, gated "
             "on coverage, validated against its own rendered files.",
         ]},
        machine("This index carries the document map and the derived counts shown above."),
    ]
    return envelope(doc, "index", S)


# ---------------------------------------------------------------------------
def main():
    if not COV.report():
        raise SystemExit("\nCOVERAGE GATE FAILED — no documents written.")
    print()
    builders = [
        ("index", build_index, "index", "Zero-to-Ship document set: method brief, playbook and full "
                                        "specification chain."),
        ("brief", lambda: envelope(brief.DOC, "brief", brief.SECTIONS + [machine()]), "Brief",
         "Narrative briefing on the Zero-to-Ship method: the problem, how it works, what it costs."),
        ("playbook", lambda: envelope(playbook.DOC, "playbook", playbook.SECTIONS + [machine()]), "Playbook",
         "Step-by-step operating manual for the Zero-to-Ship method, with gates and stop conditions."),
        ("intent", build_intent, "Intent", "Why the Zero-to-Ship method exists and the principles behind it."),
        ("context", build_context, "Context", "The Zero-to-Ship ubiquitous language: bounded contexts and the "
                                              "glossary every document in the set speaks."),
        ("prd", build_prd, "PRD", "What the Zero-to-Ship method must achieve and how success is measured."),
        ("fsd", build_fsd, "FSD", "Functional requirements for the Zero-to-Ship toolchain."),
        ("stories", build_stories, "Stories", "User stories, use cases and acceptance criteria."),
        ("sdd", build_sdd, "SDD", "Technical design, contracts, algorithms and architecture decisions."),
        ("plan", build_plan, "Plan", "The development plan for the Zero-to-Ship toolchain."),
        ("build", lambda: envelope(build.DOC, "build", build.SECTIONS + [machine()]), "Build",
         "How a Zero-to-Ship build run works: the cycle, the workers, the gauntlet and every bound."),
    ]
    spec_ids = {"index": "index-spec", "brief": "brief-spec", "playbook": "playbook-spec",
                "intent": "intent-spec", "context": "context-spec", "prd": "prd-spec", "fsd": "fsd-spec",
                "stories": "stories-spec", "sdd": "sdd-spec", "plan": "plan-spec",
                "build": "build-spec"}
    total, written = 0, 0
    for key, fn, kind, desc in builders:
        built = fn()
        # A builder returns one specification, or — where the method prescribes
        # one document per part, as it does for the plan — the list of files
        # that document is written across.
        pages = built if isinstance(built, list) else [(FILES[key], spec_ids[key], built)]
        for name, spec_id, spec in pages:
            html = shell.page(spec, spec_id, kind, desc)
            with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
                fh.write(html)
            total += len(html)
            written += 1
            print("  %-28s %3d sections · %6.1f KB" % (name, len(spec["sections"]), len(html) / 1024.0))
    for name, to in sorted(MOVED.items()):
        html = REDIRECT % {"to": to}
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(html)
        total += len(html)
        written += 1
        print("  %-28s redirect -> %s" % (name, to))
    print("\nWrote %d files to %s (%.1f KB total)" % (written, OUT, total / 1024.0))


if __name__ == "__main__":
    main()
