# -*- coding: utf-8 -*-
"""The plan generator: the specification set turned into work somebody can run.

Last in the chain, and the only generator whose output is executed rather than
read. Everything above it describes the thing being built; this describes the
building, as milestones containing phases containing tasks, where a task is the
smallest piece of work that can be finished and proved on its own (FR-PLN-01).

That difference in purpose is the whole of the difference in behaviour, and it
shows up in one rule: **this generator refuses rather than records** (M8-03).
Every document above it files a silence as an open question and writes the
document anyway, because a reader can see the question and answer it. Nobody
reads a plan — a plan is picked up and acted on. A task with no failing test
stated, a milestone with no exit criteria, a dependency on a unit nobody
defined: each becomes work done wrong rather than a question asked. So the
generator names every hole it found, in one report, and writes nothing.

Four sources, one artefact set:

  * the spine — the brief — carries the milestones, their order, their exit
    criteria and the prerequisites (FR-PLN-02);
  * one detail file per milestone carries its phases, tasks and criteria,
    loaded by identifier so milestones can be authored independently
    (M8-P1-T1);
  * the specification documents above supply the titles behind every identifier
    a task claims, and the universe the coverage gate is computed against;
  * the run ledger supplies the locked decisions every generated prompt repeats
    (FR-EXE-03).

What comes out is an index — waves, coverage, prerequisites, prompts — and one
document per milestone carrying its own phases, tasks, criteria and live status
(NFR-ARC-05). One document per milestone rather than one enormous file: the
published plan for this very project renders thirteen milestones into a single
327 KB page and says in its own words that a working project should split it.

Nothing here derives coverage a second time. The plan is checked by the same
engine that checks the published set (M8-06): a second implementation of
"is everything claimed" is a second answer to the question, which is the defect
ADR-04 exists to prevent.

The brief is a plain dictionary:

    {"title": ..., "owner": ..., "date": "2026-08-14",       # required facts
     "version": ..., "status": ..., "summary": ...,          # optional
     "gauntlet": ["python3 -m unittest discover -s tests"],  # required
     "milestones": [{"id": "M1", "title": ..., "summary": ...,
                     "dependsOn": ["M0"], "exit": ["..."],
                     "detailed": True, "deferred": "..."}],
     "prerequisites": [{"text": ..., "owner": "human",
                        "unblocks": ["M1-P1-T1"]}]}

and one detail file per detailed milestone, at
`.zero/plan/_build/details/<milestone>.json`:

    [{"id": "M1-P1", "title": ..., "summary": ..., "dependsOn": [],
      "completion": ["Phase exit criteria."],
      "tasks": [{"id": "M1-P1-T1", "title": ..., "summary": ...,
                 "priority": "Must", "autonomy": "auto", "layer": "schema",
                 "testLayers": ["unit"], "dependsOn": [], "effort": "small",
                 "tdd": {"red": ..., "green": ..., "refactor": ...},
                 "criteria": [{"id": "M1-P1-T1-C1", "kind": "auto",
                               "text": ..., "done": False}],
                 "exceptions": [{"rule": "layer", "reason": "..."}],
                 "traces": {"fr": ["FR-DOC-01"]}}]}]

Traces: FR-PLN-01, FR-PLN-02, FR-PLN-03, FR-PLN-04, FR-PLN-05, FR-PLN-06,
FR-PLN-07, FR-PLN-08, FR-PLN-09, FR-PLN-10, FR-PLN-11, FR-PLN-12, FR-PLN-13,
FR-EXE-03, FR-DOC-06, FR-DOC-08, FR-TRC-04, NFR-ARC-01, NFR-ARC-05, NFR-ARC-06,
NFR-DAT-04, NFR-DAT-05, NFR-DAT-06, NFR-EXE-04, NFR-GEN-01, NFR-VAL-03,
NFR-VAL-04, ADR-06, ADR-07, ADR-08, ADR-10, US-PLN-01, US-PLN-02, US-PLN-03,
US-PLN-04, US-EXE-01, US-STA-01.
"""

import collections
import json
import os
import re

from z2s import chain, context, fsd, gate, paths, schema, sdd, stories, trace, writer

SLUG = "plan"
TYPE = "Development plan"

INDEX_FILE = "index.html"
INDEX_SPEC_ID = "plan-spec"
MILESTONE_SPEC_ID = "milestone-spec"

REQUIRED_FACTS = ("title", "owner", "date")
DEFAULTS = {"version": "1.0", "status": "Draft for review"}
CARRIED = ("summary",)

#: Where the specification documents sit, seen from the plan directory. The two
#: live in sibling directories, so a trace chip on a task has to climb out of
#: one before it can name the other.
SPECS_PREFIX = "../specs/"

#: The documents whose ledgers hold decisions a worker must not re-open, in the
#: order the chain runs them. A slug with no ledger is skipped, not refused:
#: an addendum-only project may never have run some of these.
CHAIN_SLUGS = ("vision", "context", "prd", "fsd", "stories", "sdd")

#: Every part a generated prompt must carry (FR-EXE-03, NFR-EXE-04). Declared as
#: data so the builder and the check that the builder worked read one list.
PROMPT_PARTS = ("Plan document", "Status contract", "Locked decisions",
                "Verification gauntlet", "Report contract")

#: What a worker hands back, whatever the unit was. Method knowledge rather than
#: project data, so it is stated here once instead of being authored into every
#: brief and drifting between them.
REPORT_CONTRACT = (
    "The unit identifier, and the status you are claiming for it.",
    "For every acceptance criterion: its identifier, and whether it is met.",
    "The exact commands you ran from the gauntlet, and what each one printed.",
    "Anything you could not do, and what stopped you — never a silent omission.",
    "Any decision you had to make that the locked decisions did not cover.",
)

#: The three parts of a test-first task definition (FR-PLN-04, ADR-06). All
#: three: the failing test says the work is needed, the minimum change says when
#: to stop, and the clean-up is the step that gets skipped when nobody wrote it
#: down.
TDD_PARTS = ("red", "green", "refactor")

#: Rules a task may be excused from, by name (M8-P1-T3-C3). Only the two the
#: specification itself marks Should: a task with no failing test or no
#: machine-checkable criterion is not an exception, it is an unfinished task.
EXCUSABLE = ("testLayers", "layer")

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")
_DIGITS = re.compile(r"(\d+)")

IncompleteBrief = chain.IncompleteBrief
MissingPrerequisite = chain.MissingPrerequisite


class BrokenGraph(Exception):
    """Raised when the dependency graph cannot be executed as written.

    Separate from an incomplete brief because the two are fixed differently: one
    needs a fact somebody knows, the other needs the order of the work changed.
    """


class Uncovered(Exception):
    """Raised when something the specifications require is claimed by no work.

    Separate again, and for the same reason: the plan is complete and correct on
    its own terms, and the thing that is wrong is what it leaves out.
    """


def _slug(text):
    """A filename fragment from a title. Lower case, hyphens, nothing else."""
    return _SLUG_STRIP.sub("-", str(text or "").lower()).strip("-") or "milestone"


def _order(identifier):
    """Sort key that reads M2 as before M10 rather than after it.

    Plain text order puts M10 between M1 and M2, which is deterministic and
    wrong: a reader looking at the waves sees the second milestone in ninth
    place and stops trusting the ordering.
    """
    return tuple(int(part) if part.isdigit() else part
                 for part in _DIGITS.split(str(identifier)))


def milestone_file(one):
    """The document one milestone is written to. Named from its identifier."""
    return "%s-%s.html" % (one["id"], _slug(one["title"]))


# ------------------------------------------------------------- the detail files

def detail_path(root, milestone):
    return paths.resolve(root, paths.PLAN_DETAILS_DIR, "%s.json" % milestone)


def detail(root, milestone):
    """The phases of one milestone, loaded by identifier (M8-P1-T1).

    Separate files rather than one module, so two people can author two
    milestones without touching the same lines, and adding a milestone's detail
    needs no edit to the spine beyond its own entry (NFR-ARC-06).
    """
    target = detail_path(root, milestone)
    try:
        with open(target, encoding="utf-8") as handle:
            loaded = json.load(handle)
    except OSError:
        raise IncompleteBrief(
            "%s is marked as detailed and there is no detail file at %s; either "
            "write the detail or stop marking the milestone detailed"
            % (milestone, target))
    except ValueError as error:
        raise IncompleteBrief(
            "%s has a detail file at %s that cannot be read (%s)"
            % (milestone, target, error))

    phases = loaded.get("phases") if isinstance(loaded, dict) else loaded
    if not isinstance(phases, list):
        raise IncompleteBrief(
            "%s: the detail file at %s holds no list of phases" % (milestone, target))
    return phases


def milestones(root, brief):
    """The spine with each detailed milestone's phases loaded onto it.

    Every missing detail file is named at once, because an author who fixes one
    and is then told about the next stops running the generator.
    """
    stated = chain.named(brief.get("milestones"), "title", "milestone")
    stated = chain.named(stated, "id", "milestone")

    built, refusals = [], []
    for one in stated:
        entry = dict(one)
        if one.get("detailed"):
            try:
                entry["phases"] = detail(root, one["id"])
            except IncompleteBrief as error:
                refusals.append(str(error))
                entry["phases"] = []
        else:
            entry["phases"] = list(one.get("phases") or ())
        built.append(entry)

    if refusals:
        raise IncompleteBrief("; ".join(refusals))
    return built


# ------------------------------------------------------------------- the graph

def units(built):
    """Every unit of work, in reading order, with what it waits for.

    Milestones, phases and tasks together (FR-PLN-03). One flat map, because a
    dependency crosses levels — a task may wait on a task in another milestone —
    and a per-level check would not see the edge that closes the loop.
    """
    found = collections.OrderedDict()
    duplicated = []

    def add(one):
        unit = one.get("id")
        if unit in found:
            duplicated.append(unit)
        found[unit] = list(one.get("dependsOn") or ())

    for milestone in built:
        add(milestone)
        for phase in milestone.get("phases") or ():
            add(phase)
            for task in phase.get("tasks") or ():
                add(task)

    if duplicated:
        raise BrokenGraph(
            "two units share one identifier: %s. An identifier names one piece of "
            "work; two pieces sharing one cannot both be reported on"
            % ", ".join(sorted(set(duplicated))))
    return found


def cycles(graph):
    """Every dependency cycle, each as the full path around it (M8-P1-T2-C1).

    The full path rather than one member: told only that M4 is in a cycle, an
    author has to rediscover the other three edges before they can decide which
    one to cut.
    """
    colour = dict.fromkeys(graph, "unvisited")
    found, stack = [], []

    def walk(node):
        colour[node] = "open"
        stack.append(node)
        for other in graph.get(node) or ():
            if other not in graph:
                continue
            if colour[other] == "open":
                found.append(stack[stack.index(other):] + [other])
            elif colour[other] == "unvisited":
                walk(other)
        stack.pop()
        colour[node] = "closed"

    for node in graph:
        if colour[node] == "unvisited":
            walk(node)
    return found


def check_graph(graph):
    """Refuse a graph that cannot be executed as written.

    Both failures at once. They are usually the same mistake — an identifier
    typed wrong points at nothing, and an identifier typed wrong the other way
    points back at itself.
    """
    dangling = ["%s waits for %s, which no unit of this plan defines" % (unit, other)
                for unit in graph for other in graph[unit] if other not in graph]
    looping = [" → ".join(path) for path in cycles(graph)]

    if dangling or looping:
        raise BrokenGraph(
            "this plan cannot be executed as written. "
            + "; ".join(dangling + ["dependency cycle: %s" % path for path in looping])
            + ". Nothing was written.")


def waves(built):
    """The order the milestones may be run in, derived from their edges.

    Every milestone in a wave waits only on milestones in earlier waves, so the
    members of one wave may run at the same time (FR-PLN-09, ADR-08). Sorted
    within a wave, so the same graph produces the same ordering on every run
    (NFR-GEN-01) — the ordering is derived on every read and stored nowhere
    (NFR-DAT-05).
    """
    remaining = collections.OrderedDict(
        (one["id"], set(one.get("dependsOn") or ())) for one in built)
    known = set(remaining)
    for unit in remaining:
        remaining[unit] &= known

    done, ordered = set(), []
    while remaining:
        ready = sorted((unit for unit, waits in remaining.items() if waits <= done),
                       key=_order)
        if not ready:
            raise BrokenGraph(
                "dependency cycle among the milestones: %s. Nothing was written."
                % ", ".join(sorted(remaining, key=_order)))
        ordered.append(ready)
        done |= set(ready)
        for unit in ready:
            del remaining[unit]
    return ordered


# ----------------------------------------------------------- the task contract

def _excused(task, rule):
    """Whether this task carries a documented exception to one rule.

    An exception is narrow and it is written down: it names the rule it excuses
    and says why (M8-P1-T3-C3). It never reaches the two rules that make a task
    a task at all.
    """
    for one in task.get("exceptions") or ():
        if one.get("rule") == rule and not schema.is_empty(one.get("reason")):
            return one
    return None


def check_task(task, autonomies, layers, priorities):
    """Everything one task must state before a worker can be sent at it.

    Returns (refusals, warnings). A refusal stops the run; a warning is a rule
    the task carries a written exception to, which is a decision somebody made
    rather than a hole somebody left.
    """
    refusals, warnings = [], []
    unit = task.get("id") or "a task with no identifier"

    for one in task.get("exceptions") or ():
        if one.get("rule") not in EXCUSABLE:
            refusals.append("%s claims an exception to %r; the rules a task may be "
                            "excused from are %s"
                            % (unit, one.get("rule"), ", ".join(EXCUSABLE)))
        elif schema.is_empty(one.get("reason")):
            refusals.append("%s claims an exception to %s and gives no reason"
                            % (unit, one.get("rule")))

    if schema.is_empty(task.get("title")):
        refusals.append("%s states no title" % unit)

    # ---- test-first, in three parts (FR-PLN-04)
    stated = task.get("tdd") or {}
    for part in TDD_PARTS:
        if schema.is_empty(stated.get(part)):
            refusals.append(
                "%s states no %s step; a task without one is a task nobody can tell "
                "is finished" % (unit, part))

    # ---- acceptance criteria (FR-PLN-05, FR-PLN-06)
    criteria = [one for one in task.get("criteria") or () if isinstance(one, dict)]
    if not criteria:
        refusals.append("%s carries no acceptance criterion" % unit)
    machine = 0
    for index, one in enumerate(criteria):
        called = one.get("id") or "%s criterion %d" % (unit, index + 1)
        if schema.is_empty(one.get("id")):
            refusals.append("%s is not individually identified; a criterion nobody "
                            "can name is a criterion nobody can tick" % called)
        if schema.is_empty(one.get("text")):
            refusals.append("%s states nothing to check" % called)
        kind = one.get("kind")
        if kind not in [value["id"] for value in schema.ENUMS["criterionKinds"]]:
            refusals.append("%s is classified %r; a criterion is %s"
                            % (called, kind,
                               " or ".join(value["id"]
                                           for value in schema.ENUMS["criterionKinds"])))
        elif kind == "auto":
            machine += 1
    if criteria and not machine:
        refusals.append(
            "%s carries no machine-checkable criterion; every one of its criteria "
            "needs a human, so nothing about it can be proved unattended" % unit)

    # ---- classification (FR-PLN-07, FR-PLN-10, FR-PLN-11)
    if task.get("priority") not in priorities:
        refusals.append("%s carries priority %r; a priority is one of %s"
                        % (unit, task.get("priority"), ", ".join(priorities)))
    if task.get("autonomy") not in autonomies:
        refusals.append(
            "%s declares autonomy %r; an unattended run has to know whether it may "
            "attempt this at all, and %s are the answers"
            % (unit, task.get("autonomy"), ", ".join(autonomies)))

    named = [one for one in task.get("testLayers") or () if one in layers]
    unknown = [one for one in task.get("testLayers") or () if one not in layers]
    if unknown:
        refusals.append("%s names verification layers %s, which are not in %s"
                        % (unit, ", ".join(map(str, unknown)), ", ".join(layers)))
    elif not named:
        excused = _excused(task, "testLayers")
        message = "%s names no verification layer, so “passing” has no meaning for it" % unit
        (warnings if excused else refusals).append(
            "%s (excepted: %s)" % (message, excused["reason"]) if excused else message)

    if schema.is_empty(task.get("layer")):
        excused = _excused(task, "layer")
        message = ("%s declares no implementation layer, so it cannot be scheduled "
                   "apart from work that collides with it" % unit)
        (warnings if excused else refusals).append(
            "%s (excepted: %s)" % (message, excused["reason"]) if excused else message)

    return refusals, warnings


def check_work(built):
    """The whole three-level contract: tasks, phase exits, milestone exits.

    One pass, every hole named. Exit criteria are checked here rather than
    beside the graph because they are the same kind of fact as a task's criteria
    — what has to be true before this is called done (FR-PLN-08).
    """
    autonomies = [value["id"] for value in schema.ENUMS["autonomy"]]
    layers = [value["id"] for value in schema.ENUMS["testLayers"]]
    priorities = [value["id"] for value in schema.ENUMS["priorities"]]

    refusals, warnings = [], []
    for milestone in built:
        if schema.is_empty(milestone.get("exit")):
            refusals.append(
                "%s declares no exit criteria; without them nobody can say the "
                "milestone is finished, only that its tasks stopped" % milestone["id"])
        for phase in milestone.get("phases") or ():
            unit = phase.get("id") or "a phase of %s" % milestone["id"]
            if schema.is_empty(phase.get("title")):
                refusals.append("%s states no title" % unit)
            if schema.is_empty(phase.get("completion")):
                refusals.append("%s declares no exit criteria" % unit)
            if not (phase.get("tasks") or ()):
                refusals.append("%s contains no tasks" % unit)
            for task in phase.get("tasks") or ():
                found, excused = check_task(task, autonomies, layers, priorities)
                refusals.extend(found)
                warnings.extend(excused)
    return refusals, warnings


# ----------------------------------------------------------- the prerequisites

def prerequisites(brief, graph):
    """The human-owned checklist, held apart from the work (FR-PLN-12).

    Numbered here rather than authored, and each one may name the work it holds
    up, so a blocked task leads back to the person who can unblock it rather
    than to a list somebody has to read in full.
    """
    built, refusals = [], []
    for index, one in enumerate(brief.get("prerequisites") or ()):
        if schema.is_empty(one.get("text")):
            refusals.append("prerequisite %d states nothing" % (index + 1))
            continue
        entry = {"id": chain.identifier("PRE", index),
                 "text": one["text"],
                 "owner": one.get("owner") or "human"}
        unblocks = [unit for unit in one.get("unblocks") or ()]
        unknown = [unit for unit in unblocks if unit not in graph]
        if unknown:
            refusals.append("%s says it unblocks %s, which this plan does not define"
                            % (entry["id"], ", ".join(map(str, unknown))))
        elif unblocks:
            entry["unblocks"] = unblocks
        built.append(entry)
    return built, refusals


# ---------------------------------------------------------------- the prompts

def locked(root):
    """Every decision the chain has already settled, from the run ledger.

    Read from the ledger rather than re-authored into the plan brief: the gate
    wrote them down once, and a second copy is a copy that disagrees. A worker
    that never saw the gate invents its own answers, which is the failure
    FR-EXE-03 exists to prevent.
    """
    found = []
    for slug in CHAIN_SLUGS:
        for settled in gate.load(root, slug) or ():
            found.append((slug, settled))
    return found


def _statuses():
    return ["%s — %s" % (value["label"], value["desc"])
            for value in schema.ENUMS["statuses"]]


def _block(title, lines):
    return "%s\n%s" % (title, "\n".join("  - %s" % line for line in lines))


def prompt(heading, opening, filename, decisions, gauntlet, closing=()):
    """One execution prompt, carrying all five parts (M8-P2-T3).

    One builder for the orchestrator's prompt and every milestone's, so the two
    cannot come to say different things about the same contract.
    """
    parts = [heading, "", opening, "",
             _block("Plan document", [filename]),
             "",
             _block("Status contract",
                    _statuses() + ["Status lives in the plan document itself. Set it "
                                   "with the status command; never by hand."]),
             "",
             _block("Locked decisions",
                    ["%s · %s: %s" % (slug, settled.question, settled.choice)
                     for slug, settled in decisions]
                    + ["These are settled. Apply them; do not re-open them."]),
             "",
             _block("Verification gauntlet", list(gauntlet)),
             "",
             _block("Report contract", list(REPORT_CONTRACT))]
    if closing:
        parts.extend(["", _block("This unit", list(closing))])
    return "\n".join(parts)


def prompts(built, filenames, index_file, decisions, gauntlet):
    """The orchestrator's prompt, and one per milestone."""
    ordered = waves(built)
    overall = prompt(
        "You are running a Zero-to-Ship build.",
        "Work through the milestones wave by wave. Everything in one wave may run "
        "at the same time; nothing in a wave may start before the wave above it "
        "has finished. Open the plan document for a milestone before starting it.",
        index_file, decisions, gauntlet,
        closing=["Wave %d: %s" % (index + 1, ", ".join(wave))
                 for index, wave in enumerate(ordered)])

    each = collections.OrderedDict()
    for milestone in built:
        each[milestone["id"]] = prompt(
            "You are building %s: %s." % (milestone["id"], milestone["title"]),
            "Everything you need is in the document named below. Read it first. Work "
            "the tasks in dependency order, and write the failing test before the "
            "code that satisfies it.",
            filenames[milestone["id"]], decisions, gauntlet,
            closing=[milestone.get("summary") or milestone["title"]]
                    + ["Done when: %s" % line for line in milestone.get("exit") or ()])
    return overall, each


def check_prompt(text):
    """Which of the five required parts a prompt is missing (M8-P2-T3-C1)."""
    return [part for part in PROMPT_PARTS if part not in text]


# ----------------------------------------------------------------- the sections

def _task_entry(task, phase):
    """One task, as the catalogue shows it (M8-01).

    Through the same catalogue the requirements and the stories use, so the
    search box, the priority bands, the folding, the deep links and the trace
    chips all reach the plan without one line of new interaction code.
    """
    entry = {"id": task["id"], "area": phase["id"],
             "priority": task["priority"],
             "status": task.get("status") or "not-started",
             "autonomy": task["autonomy"],
             "title": task["title"]}
    for name in ("summary", "layer", "effort"):
        if not schema.is_empty(task.get(name)):
            entry["text" if name == "summary" else name] = task[name]
    if not schema.is_empty(task.get("testLayers")):
        entry["testLayers"] = list(task["testLayers"])
    if not schema.is_empty(task.get("dependsOn")):
        entry["dependsOn"] = list(task["dependsOn"])
    if not schema.is_empty(task.get("tdd")):
        entry["tdd"] = {part: task["tdd"][part] for part in TDD_PARTS
                        if not schema.is_empty(task["tdd"].get(part))}
    entry["criteria"] = [
        {"id": one["id"], "kind": one["kind"], "text": one["text"],
         "done": bool(one.get("done"))}
        for one in task.get("criteria") or ()]
    if not schema.is_empty(task.get("deferred")):
        entry["deferred"] = task["deferred"]
    found = chain.traces(task)
    if found:
        entry["traces"] = found
    return entry


def _work_section(milestone):
    """The milestone's phases and tasks, as one catalogue of areas and entries."""
    phases = list(milestone.get("phases") or ())
    entries = [_task_entry(task, phase)
               for phase in phases for task in phase.get("tasks") or ()]
    return {"id": "work", "type": "requirements",
            "title": "Phases, tasks and acceptance criteria",
            "badge": "%d tasks" % len(entries),
            "lede": "Every task states the failing test that proves it is needed "
                    "before any code exists, and the criteria that decide when it "
                    "is done. A tick is the plan's own record, written by the "
                    "status command.",
            "areas": [{"key": phase["id"], "name": phase["title"],
                       "description": phase.get("summary") or ""}
                      for phase in phases],
            "items": entries}


def _prompt_section(entries):
    return {"id": "prompt", "type": "prompts",
            "title": "Execution instructions",
            "lede": "Generated from this plan and the locked decisions already "
                     "recorded. Everything a worker needs is here; nothing outside "
                     "this repository is assumed.",
            "items": [{"id": "prompt-%s" % unit, "title": title, "body": body}
                      for unit, title, body in entries]}


def _milestone_sections(milestone, prompt_text):
    sections = [
        {"id": "overview", "type": "prose", "title": "What this milestone is",
         "body": [milestone.get("summary") or milestone["title"]]},
        {"id": "exit", "type": "list", "title": "Done when",
         "items": list(milestone.get("exit") or ())},
    ]
    if milestone.get("dependsOn"):
        sections.append({"id": "waits-for", "type": "list", "title": "Waits for",
                         "items": list(milestone["dependsOn"])})
    sections.append(_work_section(milestone))
    sections.append(_prompt_section(
        [(milestone["id"], "Instructions for %s" % milestone["id"], prompt_text)]))
    return sections


def _index_sections(built, filenames, ordered, rows, checklist, overall, each):
    counts = collections.Counter(row.state for row in rows)
    tasks = sum(len(phase.get("tasks") or ())
                for one in built for phase in one.get("phases") or ())

    return [
        {"id": "howto", "type": "prose", "title": "How to read this plan",
         "body": [
             "This plan was **generated**, not written. Its source is the milestone "
             "spine, one detail file per milestone, and the specification "
             "documents' own embedded data. It is regenerated by changing that "
             "source, never by editing a document.",
             "Generation fails if anything the specifications require is claimed by "
             "no unit of work, so the coverage table below is a proof rather than a "
             "summary — it cannot show a row with nothing against it.",
             "**Status lives in the milestone documents.** Each task's status and "
             "each criterion's state are stored in the specification embedded in "
             "the document and written by the status command.",
         ]},

        {"id": "statuses", "type": "table", "title": "Status vocabulary",
         "lede": "A closed set. A value outside it is refused without the file "
                  "being modified.",
         "columns": ["Status", "Meaning"],
         "rows": [[value["label"], value["desc"]] for value in schema.ENUMS["statuses"]]},

        {"id": "classes", "type": "table",
         "title": "Autonomy classes and verification layers",
         "lede": "Autonomy decides what an unattended run may attempt. Verification "
                  "layers decide what “passing” means for a given task.",
         "columns": ["Class or layer", "Kind", "Meaning"],
         "rows": ([[value["label"], "Autonomy", value["desc"]]
                   for value in schema.ENUMS["autonomy"]]
                  + [[value["label"], "Criterion", value["desc"]]
                     for value in schema.ENUMS["criterionKinds"]]
                  + [[value["label"], "Verification", "Named by the tasks it proves."]
                     for value in schema.ENUMS["testLayers"]])},

        {"id": "waves", "type": "waves", "title": "Parallel execution waves",
         "files": dict(filenames),
         "lede": "Derived from the dependency graph on every run. Every milestone "
                  "in a wave waits only on milestones in earlier waves, so the "
                  "members of one wave may run at the same time.",
         "waves": ordered},

        {"id": "milestones", "type": "table", "title": "Milestones",
         "badge": "%d milestones · %d tasks" % (len(built), tasks),
         "columns": ["Milestone", "Title", "Waits for", "Detail"],
         "rows": [[one["id"],
                   "[%s](%s)" % (one["title"], filenames[one["id"]]),
                   ", ".join(one.get("dependsOn") or ()) or "nothing",
                   "%d tasks" % sum(len(phase.get("tasks") or ())
                                    for phase in one.get("phases") or ())]
                  for one in built]},

        {"id": "coverage", "type": "table", "title": "Coverage",
         "lede": "Computed at generation time from the tasks' own traces. A row "
                  "claimed by nothing fails generation, so this table cannot show "
                  "one.",
         "badge": "%d identifiers" % len(rows),
         "columns": ["Identifier", "Kind", "Title", "Claimed by"],
         "rows": [[row.id, row.kind, row.title,
                   ", ".join(row.claimants) or "_deliberately excluded_"]
                  for row in rows]},

        {"id": "prerequisites", "type": "table", "title": "Prerequisites",
         "lede": "Human-owned, and held apart from the work. Each must be cleared, "
                  "or the tasks it holds up classed as needing a person, before an "
                  "unattended run starts.",
         "columns": ["ID", "Prerequisite", "Owner", "Unblocks"],
         "rows": [[one["id"], one["text"], one["owner"],
                   ", ".join(one.get("unblocks") or ()) or "—"]
                  for one in checklist]},

        {"id": "summary", "type": "statistics", "title": "Where this stands",
         "items": [{"label": "milestones", "value": str(len(built))},
                   {"label": "tasks", "value": str(tasks)},
                   {"label": "waves", "value": str(len(ordered))},
                   {"label": "claimed", "value": str(counts.get(trace.CLAIMED, 0))},
                   {"label": "excluded", "value": str(counts.get("excluded", 0))}]},

        _prompt_section(
            [("orchestrator", "For whoever is running the whole build", overall)]
            + [(unit, "Instructions for %s" % unit, each[unit]) for unit in each]),
    ]


# ------------------------------------------------------------------ generation

def forks(brief):
    """Every fork this generator opens. None (M8-03).

    A plan is acted on rather than read, so its silences are refusals rather than
    questions, and there is nothing left for a gate to settle. The decisions a
    worker must honour were settled by the documents above and are repeated into
    every prompt from the ledger.
    """
    return ()


def open_gate(brief, root=None):
    """The gate this generator runs, over whatever is already known."""
    decisions = gate.load(root, SLUG) if root is not None else ()
    return gate.Gate(SLUG, forks(brief), source=brief, decisions=decisions)


def envelope(brief):
    return chain.envelope(brief, SLUG, TYPE, REQUIRED_FACTS, DEFAULTS, CARRIED)


def catalog(above):
    """Identifier to title, for everything the plan is allowed to claim."""
    found = {}
    for spec in above.values():
        for _, entry in schema.entries(spec):
            unit = entry.get("id")
            if isinstance(unit, str) and schema.kind_of(unit) not in (None, "plan"):
                found[unit] = entry.get("title") or ""
    return found


def upstream(root):
    """The specification documents this plan is derived from, keyed by filename."""
    needed_by = "the plan generator"
    return collections.OrderedDict(
        (one.FILENAME, chain.require(root, one.FILENAME, one.SLUG, needed_by))
        for one in (fsd, sdd, stories, context))


def generate(brief, run, root="."):
    """The plan index and one specification per milestone. Writes nothing.

    Returns (index, {milestone: spec}, {milestone: filename}). Everything is
    built and checked in memory first, so a refused run leaves the project
    exactly as it found it (M8-P1-T2-C2).
    """
    run.require_closed()
    above = upstream(root)

    if schema.is_empty(brief.get("gauntlet")):
        raise IncompleteBrief(
            "the brief states no verification gauntlet; every generated prompt has "
            "to name the commands that decide whether the work passed, and a worker "
            "left to choose them chooses differently every time")

    built = milestones(root, brief)
    graph = units(built)
    check_graph(graph)

    refusals, warnings = check_work(built)
    checklist, found = prerequisites(brief, graph)
    refusals.extend(found)
    if refusals:
        raise IncompleteBrief(
            "this plan is not ready to be executed:\n  - "
            + "\n  - ".join(refusals) + "\nNothing was written.")

    block = envelope(brief)
    legend = schema.legend()
    known = catalog(above)
    ordered = waves(built)
    filenames = collections.OrderedDict((one["id"], milestone_file(one)) for one in built)

    routes = {space: SPECS_PREFIX + name
              for space, name in trace.links(above).items()}

    specs = collections.OrderedDict()
    for milestone in built:
        document = dict(block)
        document["title"] = "%s — %s" % (milestone["id"], milestone["title"])
        document["milestone"] = milestone["id"]
        if not schema.is_empty(milestone.get("summary")):
            document["summary"] = milestone["summary"]
        spec = {"document": document,
                "schemaVersion": schema.SCHEMA_VERSION,
                "legend": legend, "catalog": known, "links": routes,
                "sections": _milestone_sections(milestone, "")}
        specs[milestone["id"]] = spec

    decisions = locked(root)
    if not decisions:
        raise IncompleteBrief(
            "the run ledger records no locked decisions; a worker sent at this plan "
            "would have nothing to apply and would settle every fork again, "
            "differently. Run the documents above through their decision gates first")

    overall, each = prompts(built, filenames, INDEX_FILE, decisions, brief["gauntlet"])
    for milestone in built:
        unit = milestone["id"]
        specs[unit]["sections"] = _milestone_sections(milestone, each[unit])

    rows = coverage(above, specs)

    index = {"document": dict(block, milestone=""),
             "schemaVersion": schema.SCHEMA_VERSION,
             "legend": legend, "catalog": known, "links": routes,
             "waves": ordered,
             "sections": _index_sections(built, filenames, ordered, rows,
                                         checklist, overall, each)}

    locked_section = run.section()
    if locked_section is not None:
        index["sections"].append(locked_section)

    words = context.glossary(above[context.FILENAME])
    index = context.consult(index, words)
    for unit in specs:
        specs[unit] = context.consult(specs[unit], words)
    return index, specs, filenames


def coverage(above, specs):
    """The coverage matrix, and a refusal if anything is claimed by nothing.

    The same engine the published set is checked with (M8-06), run against the
    plan before it exists as a file — so a plan that fails the gate is never
    written, rather than written and then reported on.
    """
    together = collections.OrderedDict(above)
    for unit in specs:
        together["%s (in memory)" % unit] = specs[unit]

    findings = trace.check(together)
    failures = [one for one in findings if one.severity == schema.FAILURE]
    if failures:
        raise Uncovered(
            "this plan does not cover what the specifications require:\n  - "
            + "\n  - ".join(one.message for one in failures)
            + "\nNothing was written.")
    return trace.matrix(together)


# --------------------------------------------------------------------- writing

def render(spec, spec_id, root="."):
    return chain.render(spec, spec_id, root)


def write(root, filename, spec, spec_id):
    """Write one rendered plan document. Returns the path written."""
    target = paths.resolve(root, paths.PLAN_DIR, filename)
    writer.write(target, render(spec, spec_id, root))
    return target


def regenerate(root, filename=INDEX_FILE, spec=None):
    """Re-render a plan document from its own embedded specification (FR-DOC-06)."""
    if spec is None:
        target = paths.resolve(root, paths.PLAN_DIR, filename)
        try:
            with open(target, encoding="utf-8") as handle:
                spec = validate_extract(handle.read(), target)
        except OSError:
            raise MissingPrerequisite(
                "there is no plan document at %s. Nothing was written." % target)
    spec_id = INDEX_SPEC_ID if filename == INDEX_FILE else MILESTONE_SPEC_ID
    return write(root, filename, spec, spec_id)


def validate_extract(html, source):
    from z2s import validate
    try:
        return validate.extract(html)
    except validate.ExtractionError as error:
        raise MissingPrerequisite("%s carries no readable plan (%s)." % (source, error))


def author(root, brief, run):
    """Gate, chain, checks, ledger, documents — in that order.

    Returns (paths, index, specs). Every refusal above has already happened, so
    reaching this point means every document in the set can be written.
    """
    index, specs, filenames = generate(brief, run, root)

    paths.ensure_layout(root)
    run.record(root)

    written = [write(root, INDEX_FILE, index, INDEX_SPEC_ID)]
    for unit in specs:
        written.append(write(root, filenames[unit], specs[unit], MILESTONE_SPEC_ID))
    return written, index, specs


def written(root):
    """Every plan document currently in the project, in reading order."""
    folder = paths.resolve(root, paths.PLAN_DIR)
    if not os.path.isdir(folder):
        return []
    found = sorted((name for name in os.listdir(folder) if name.endswith(".html")),
                   key=_order)
    return [name for name in found if name == INDEX_FILE] + \
           [name for name in found if name != INDEX_FILE]
