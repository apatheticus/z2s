# -*- coding: utf-8 -*-
"""Generate the Zero-to-Ship document set.

Reads the specification modules, computes everything derivable (coverage, waves,
traceability matrix, rollups), and emits ten self-contained HTML documents.

    python3 generate.py

Nothing here is authored twice: each fact lives in exactly one module and every
cross-document view is computed at generation time.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import shell                                                    # noqa: E402
import coverage as COV                                          # noqa: E402
from specs import vision, context, prd, fsd, stories, sdd      # noqa: E402
from specs import plan_spine, brief, playbook                   # noqa: E402

DETAIL = COV.DETAIL

FILES = {
    "index":     "index.html",
    "brief":     "Z2S-Brief.html",
    "playbook":  "Z2S-Playbook.html",
    "vision":    "Z2S-Vision.html",
    "context":   "Z2S-Context.html",
    "prd":       "Z2S-PRD.html",
    "stories":   "Z2S-User-Stories.html",
    "fsd":       "Z2S-FSD.html",
    "sdd":       "Z2S-SDD.html",
    "plan":      "Z2S-Plan.html",
}

NAV = [
    ("index", "Overview"), ("brief", "Brief"), ("playbook", "Playbook"), ("vision", "Vision"),
    ("context", "Context"), ("prd", "PRD"), ("fsd", "FSD"), ("stories", "Stories"),
    ("sdd", "SDD"), ("plan", "Plan"),
]

# Prefix -> the document that defines identifiers with that prefix. Two-segment
# prefixes are tried first, then one-segment (so ADR-01 routes via "ADR").
LINKS = {
    "FR": FILES["fsd"], "NFR": FILES["sdd"], "ADR": FILES["sdd"],
    "US": FILES["stories"], "UC": FILES["stories"],
    "VC": FILES["vision"], "VS": FILES["vision"], "SH": FILES["vision"],
    "BC": FILES["context"], "UL": FILES["context"],
    "G": FILES["prd"], "NG": FILES["prd"], "MT": FILES["prd"], "J": FILES["prd"], "RK": FILES["prd"],
}


def siblings(current):
    return [{"label": lbl, "href": FILES[k], "current": k == current} for k, lbl in NAV]


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
# Vision
# ---------------------------------------------------------------------------
def build_vision():
    S = [
        {"id": "problem", "type": "prose", "title": "The problem", **vision.PROBLEM},
        {"id": "vision", "type": "prose", "title": "Vision statement",
         "body": [vision.VISION_STATEMENT],
         "note": {"kind": "ok", "label": "In short.",
                  "text": "Store each fact once. Derive everything else. Let the build prove it."}},
        {"id": "ambition", "type": "list", "title": "What that makes possible",
         "items": vision.AMBITION},
        {"id": "principles", "type": "defs", "title": "Principles",
         "intro": "These constrain every later decision. Where a principle and a convenience conflict, the "
                  "principle wins or is explicitly amended — never quietly set aside.",
         "items": [{"term": p["name"], "def": p["desc"]} for p in vision.PRINCIPLES]},
        {"id": "stakeholders", "type": "table", "title": "Stakeholders",
         "columns": ["ID", "Stakeholder", "Type", "What they need", "Their role"],
         "mono": [0],
         "rows": [[s["id"], "**%s**" % s["name"], s["type"], s["interest"], s["role"]]
                  for s in vision.STAKEHOLDERS]},
        {"id": "personas", "type": "cards", "title": "Personas", "cols": "g2",
         "items": [{"kicker": p["tier"], "title": p["name"], "text": p["desc"],
                    "items": ["**Wants:** " + "; ".join(p["goals"]), "**Hurts:** " + "; ".join(p["pains"])]}
                   for p in vision.PERSONAS]},
        {"id": "capabilities", "type": "cards", "title": "Capabilities", "cols": "g2",
         "lede": "The ten things the method must be able to do. Every goal in the product requirements traces to "
                 "one of these.",
         "items": [{"id": c["id"], "title": c["name"], "text": c["desc"]} for c in vision.CAPABILITIES]},
        {"id": "scenarios", "type": "cards", "title": "Scenarios", "cols": "g2",
         "lede": "What it looks like when it works.",
         "items": [{"id": s["id"], "kicker": s["persona"], "title": s["title"], "text": s["narrative"],
                    "traces": {"cap": s["touches"]}} for s in vision.SCENARIOS]},
        {"id": "constraints", "type": "list", "title": "Constraints and limits",
         "intro": "Including the ones that are uncomfortable.", "items": vision.CONSTRAINTS},
        machine(),
    ]
    return envelope(vision.DOC, "vision", S)


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
                  "text": "Generated after the [Vision](Z2S-Vision.html) and before the "
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
         "lede": "Each goal traces to the vision capability it serves.",
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


def build_plan():
    W = waves()
    uni, excluded = COV.universe()
    claims = COV.claims()
    kind_label = {"fr": "Functional", "nfr": "Technical", "adr": "Decision"}
    cov_rows = []
    for i in sorted(uni, key=lambda x: (uni[x][0], x)):
        kind, title = uni[i]
        cov_rows.append([
            "[%s](%s#%s)" % (i, LINKS[i.split("-")[0]], i),
            kind_label[kind], title,
            " ".join("[%s](#%s)" % (u, u) for u in claims.get(i, [])) or "**none**",
        ])
    for i in sorted(excluded):
        cov_rows.append(["[%s](%s#%s)" % (i, FILES["fsd"], i), "Excluded", excluded[i],
                         "_deliberate exclusion, recorded with its reason_"])

    ms_items = []
    for m in plan_spine.MILESTONES:
        item = dict(m)
        phases = []
        for ph in DETAIL.get(m["id"], []):
            ph = dict(ph)
            # Schema default, materialised into the artefact: a task with no authored
            # status is "not-started". Status must be PRESENT in the rendered
            # specification — it is the field the write-back tool edits.
            ph["tasks"] = [dict(t, status=t.get("status", "not-started")) for t in ph.get("tasks", [])]
            phases.append(ph)
        item["phases"] = phases
        ms_items.append(item)

    ntasks = sum(len(p.get("tasks", [])) for ms in DETAIL.values() for p in ms)
    ncrit = sum(len(t.get("criteria", [])) for ms in DETAIL.values() for p in ms for t in p.get("tasks", []))
    nauto = sum(1 for ms in DETAIL.values() for p in ms for t in p.get("tasks", [])
                for c in t.get("criteria", []) if c.get("kind") == "auto")

    S = [
        {"id": "howto", "type": "prose", "title": "How to read this plan",
         "body": [
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
         "note": {"kind": "info", "label": "Two honest deviations, recorded rather than hidden.",
                  "text": "**One:** every unit reads not started, because this plan has not been executed — that "
                          "is the true state, and it is what the status model is for. **Two:** the method "
                          "prescribes one document per milestone, and this renders all thirteen in a single file "
                          "so the document set stays portable. That is why this file exceeds the 250 KB size "
                          "target in the [technical specification](Z2S-SDD.html#targets); in a working "
                          "project, split it."}},

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
         "waves": W},

        {"id": "prerequisites", "type": "table", "title": "Prerequisites",
         "intro": "Human-owned work, held separately from the plan. Each must be cleared, or its dependent tasks "
                  "classed human-gated, before an unattended run starts.",
         "columns": ["ID", "Prerequisite", "Owner"], "mono": [0],
         "rows": [[p["id"], p["text"], p["owner"]] for p in plan_spine.PREREQUISITES]},

        {"id": "milestones", "type": "milestones", "title": "Milestones, phases and tasks",
         "badge": "%d tasks" % ntasks,
         "lede": "Click a milestone to expand it. Every task carries its failing-test definition, its acceptance "
                 "criteria and the requirements it claims.",
         "statuses": {s["id"]: {"label": s["label"], "tone": s["tone"]}
                      for s in plan_spine.LEGEND["statuses"]},
         "items": ms_items},

        {"id": "coverage", "type": "table", "title": "Coverage matrix",
         "intro": "Computed at generation time from the tasks' own traces. A row with no claiming unit fails "
                  "generation — this table cannot show one.",
         "badge": "%d identifiers" % (len(uni) + len(excluded)),
         "columns": ["Identifier", "Kind", "Title", "Claimed by"], "mono": [0],
         "rows": cov_rows},

        machine("Includes every milestone, phase, task and criterion with its live status. This block is what "
                "the status tool edits and what the orchestrator reads."),
    ]
    spec = envelope(plan_spine.DOC, "plan", S)
    spec["legend"] = plan_spine.LEGEND
    spec["waves"] = W
    spec["catalog"] = catalog()
    return spec


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
        "version": "2.0",
        "status": "Complete",
        "date": "2026-08-13",
        "owner": "Zerø Effort",
        "releaseScope": "Ten documents",
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
        {"id": "start", "type": "cards", "title": "Start here", "cols": "g3",
         "lede": "Three ways in, depending on what you need.",
         "items": [
             {"kicker": "Understand it", "title": "Method Brief", "href": "Z2S-Brief.html",
              "text": "The narrative explanation. Plain language first, technical depth after — including the "
                      "method run for real on a shipped product. Read this if you are deciding whether the "
                      "method is worth adopting, or explaining it to someone else."},
             {"kicker": "Run it", "title": "Operating Playbook", "href": "Z2S-Playbook.html",
              "text": "Six phases, numbered steps, one skill invocation per step, a gate and a stop condition "
                      "for each. Read this if the chain is installed and you need to operate the method."},
             {"kicker": "Build it", "title": "The specification chain", "href": "Z2S-FSD.html",
              "text": "Vision, context, product requirements, functional specification, stories, technical "
                      "specification and plan — everything needed to build the toolchain itself."},
         ]},
        {"id": "stats", "type": "stats", "title": "The set at a glance",
         "items": [
             {"value": "10", "label": "documents", "note": "Each self-contained, each rendering itself from its "
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
        {"id": "chain", "type": "flow", "title": "How the documents relate",
         "lede": "Each document answers a question the previous one raised. Traces run upward only, so changing "
                 "a downstream document can never invalidate an upstream one.",
         "flows": [
             {"name": "The specification chain",
              "caption": "The plan is derived from the functional and technical specifications, and fails to "
                         "generate if either contains a requirement it does not schedule.",
              "steps": [
                  {"title": "Vision", "desc": "Problem, principles, capabilities.", "kind": "input"},
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
        {"id": "skills", "type": "table", "title": "The skill chain",
         "intro": "The method is operated through named skills, installed as one plugin: "
                  "`/plugin marketplace add apatheticus/z2s`, then "
                  "`/plugin install zero@apatheticus` "
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
             ["/zero:vision", "Derives the vision from any mix of narrative, documents and web addresses; "
              "maintains the source register.", "Nothing — start here"],
             ["/zero:context", "Establishes the ubiquitous language: glossary, bounded contexts, context map.",
              "Completed Vision"],
             ["/zero:prd", "Generates the product requirements.", "Completed Context"],
             ["/zero:fsd", "Generates the functional specification.", "Completed PRD"],
             ["/zero:stories", "Generates user stories and use cases.", "Completed FSD"],
             ["/zero:sdd", "Generates the technical design.", "Completed FSD"],
             ["/zero:plan", "Derives the plan and proves coverage.", "Completed Stories, FSD and SDD"],
             ["/zero:build", "Works through the plan's build prompts, wave by wave.", "A validated plan"],
             ["/zero:action", "Resumes from wherever the set stands; starts from the beginning if no Vision.",
              "Nothing"],
             ["/zero:update", "Folds additions and changes in, forward-only — never deletes or overwrites.",
              "The document it updates"],
             ["/zero:ship", "Commits and pushes the working branch; asks before opening a pull request.",
              "A working branch"],
             ["/zero:questions", "The shared clarification interview every other skill routes questions "
              "through. The only skill that may trigger automatically.", "—"],
         ]},
        {"id": "documents", "type": "table", "title": "The ten documents",
         "columns": ["Document", "Type", "Answers", "Identifiers"], "mono": [3],
         "rows": [
             ["[Overview](index.html)", "Index", "Where to start and how the set fits together.", "—"],
             ["[Method Brief](Z2S-Brief.html)", "Briefing",
              "What problem this solves, how it works, what it costs.", "—"],
             ["[Operating Playbook](Z2S-Playbook.html)", "Manual",
              "How to run the method, step by step, with gates and stop conditions.", "S-A1 … S-F3"],
             ["[Vision](Z2S-Vision.html)", "Vision",
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
              "The buildable plan for the toolchain, with live status.", "M\\*-P\\*-T\\*"],
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
             {"term": "Nothing here is hand-edited",
              "def": "All ten documents are generated from source modules. To change one, change its source and "
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
        ("vision", build_vision, "Vision", "Why the Zero-to-Ship method exists and the principles behind it."),
        ("context", build_context, "Context", "The Zero-to-Ship ubiquitous language: bounded contexts and the "
                                              "glossary every document in the set speaks."),
        ("prd", build_prd, "PRD", "What the Zero-to-Ship method must achieve and how success is measured."),
        ("fsd", build_fsd, "FSD", "Functional requirements for the Zero-to-Ship toolchain."),
        ("stories", build_stories, "Stories", "User stories, use cases and acceptance criteria."),
        ("sdd", build_sdd, "SDD", "Technical design, contracts, algorithms and architecture decisions."),
        ("plan", build_plan, "Plan", "The development plan for the Zero-to-Ship toolchain."),
    ]
    spec_ids = {"index": "index-spec", "brief": "brief-spec", "playbook": "playbook-spec",
                "vision": "vision-spec", "context": "context-spec", "prd": "prd-spec", "fsd": "fsd-spec",
                "stories": "stories-spec", "sdd": "sdd-spec", "plan": "plan-spec"}
    total = 0
    for key, fn, kind, desc in builders:
        spec = fn()
        html = shell.page(spec, spec_ids[key], kind, desc)
        path = os.path.join(OUT, FILES[key])
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        total += len(html)
        print("  %-28s %3d sections · %6.1f KB" % (FILES[key], len(spec["sections"]), len(html) / 1024.0))
    print("\nWrote %d documents to %s (%.1f KB total)" % (len(builders), OUT, total / 1024.0))


if __name__ == "__main__":
    main()
