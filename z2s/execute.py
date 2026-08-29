# -*- coding: utf-8 -*-
"""The orchestrator — the plan, actually run.

Everything above this module produces documents. This one reads them and does
the work they describe: it computes what is eligible, hands each unit to a
worker, has the result judged by somebody who did not build it, records what
actually happened, and keeps going when one unit gets stuck.

The shape of a cycle, for one unit:

    brief -> BUILD -> gauntlet -> JUDGE -> passing, or one named gap
                                              |
                                              +-> re-briefed with that gap,
                                                  judged by a fresh worker,
                                                  bounded, then blocked

Four things about it are worth stating plainly, because each is a decision that
could reasonably have gone the other way (M11-01..M11-04):

* **A worker is a command**, named in the project's own settings and given two
  file paths — where its brief is, and where its report must go. Nothing here
  knows or cares whether that command is an agent, a script or a person at a
  terminal. That is what makes the whole module testable without one.
* **Nothing passes on its author's say-so** (FR-EXE-14). The gauntlet is run by
  this module, so the exit status is observed rather than reported, and a second
  worker inspects the result having been shown no account of how it was made.
* **A retry is briefed with the single gap the last judgement named**, and a
  fresh judge sees it — otherwise a judge grades improvement instead of the bar.
  Attempts are still bounded: FR-EXE-07 is worth more here than an unbounded
  loop, because one impossible unit must not idle a whole run.
* **A unit that declares no write set runs alone.** Guessing the other way means
  two workers editing one file, which is the failure concurrency was supposed to
  be worth risking.

Concurrency is deliberately narrow: worker processes run at the same time, up to
the stated ceiling, and everything that WRITES — the gauntlet, the judgement,
the status write-back, the ledger, the commit — happens one at a time on this
thread. LD-03 says a run has one writer, and `z2s/writer.py` is built on that
promise. Running the gauntlet concurrently would break something subtler as
well: the verification record is keyed by layer, so two units proving "unit"
at once would each be trusting the other's evidence.

Traces: FR-EXE-01..FR-EXE-14, NFR-EXE-01..NFR-EXE-09, NFR-SEC-02..NFR-SEC-05,
ADR-07, ADR-08, ADR-10, ADR-13, ADR-15, US-EXE-01..US-EXE-07.
"""

import collections
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys

from z2s import gauntlet as loop
from z2s import dispatch, learn, paths, plan, safety, schema, status, writer

#: Where a project says what its workers are. Not transient: this is committed
#: configuration, not run state, so it does not live under `state/`.
SETTINGS = paths.WORKERS_FILE

#: What this run has done, and what it was about to do. Transient by design
#: (NFR-OPS-04) — the plan documents are the record, this is the bookmark.
LEDGER = paths.LEDGER_DIR + "/run.json"

#: Where briefs go out and reports come back.
WORK = paths.LEDGER_DIR + "/work"

#: The two paths every worker command must name. A command that names neither
#: has no way to be told what to do or to say what it did.
BRIEF_PLACEHOLDER = "{brief}"
REPORT_PLACEHOLDER = "{report}"

#: The second brief a dispatch may carry: written beside the first, never over
#: it, because it names the first as the place the contract is stated.
RECOVERY_BRIEF = "recovery.md"

#: Where the recovery turn's output goes. Named apart from the first log of the
#: same dispatch: the two turns are two accounts of one unit, and a run that
#: overwrote the first would lose the only record of what went quiet.
RECOVERY_LOG = "recovery.log"

BUILD = "build"
JUDGE = "judge"

#: Optional (M12-04). A milestone closes with a drafted retrospective whether or
#: not anybody is configured to turn it into prose, so a project with no such
#: worker is a project that still remembers — just more plainly.
RETROSPECTIVE = "retrospective"

ROLES = (BUILD, JUDGE, RETROSPECTIVE)

#: The roles a run cannot start without. Without a builder nothing is made;
#: without a judge nothing may pass (FR-EXE-14).
REQUIRED_ROLES = (BUILD, JUDGE)

PASS = "pass"
FAIL = "fail"

#: Four, because NFR-EXE-09 says four and LD-05 says why: the binding constraint
#: is review capacity, not machine capacity. This read 2 from M11 until M14
#: noticed, which made the published requirement and the code disagree about a
#: number a project inherits by saying nothing.
DEFAULT_CEILING = 4
DEFAULT_ATTEMPTS = 3

#: How long one dispatch gets, in seconds, unless the project says otherwise.
#: Ninety minutes is generous against the longest builder anybody has watched
#: finish, and the number matters far less than there being one: a bound that
#: waits to be asked for rescues nobody, because the run that needed it is the
#: run whose operator had not yet learned they needed it. `None` means no bound,
#: which a project may ask for and must ask for in as many words.
#:
#: The arithmetic is worth doing before choosing a number, because it is not one
#: bound per unit: a dispatch that runs out of time is asked once for its
#: account, so one dispatch can cost twice this, and a timeout is a misfire
#: rather than an attempt, so a thoroughly wedged worker is re-dispatched until
#: the misfire count reaches `attempts`. At the defaults that is three
#: dispatches of up to three hours each before the unit is blocked. Bounded,
#: which is the whole point — but not small, and a project that wants it small
#: says a smaller number here rather than expecting one.

DEFAULT_TIMEOUT = 5400

#: The judge's contract and its injection guard, defined in `z2s/gauntlet.py`
#: and named here so every caller that already reads them from this module keeps
#: working (M14-01). A pasted prompt appoints its own critic and this module
#: spawns one; both must read the same sentences or the separation only holds in
#: one of the two.
#:
#: The module is imported as `loop`, not under its own name: this module already
#: has a function called `gauntlet` — the commands one unit must pass — and the
#: two words would mean different things one line apart.
GUARD = loop.GUARD
JUDGE_CONTRACT = loop.JUDGE_CONTRACT

#: The parts a judgement brief must carry, checked the same way prompts are.
JUDGE_PARTS = ("Unit", "Acceptance criteria", "Verification already run",
               "The work", "The higher target", "How to judge")

#: What only a run can tell a worker: it will not be appointing the critic that
#: decides this unit. A pasted prompt's reader appoints every critic themselves;
#: here the orchestrator appoints the last one, and a builder that does not know
#: that writes its report as though its own verdict counted.
JUDGED = (
    "Split this unit and appoint critics for the pieces exactly as described "
    "below — that judgement is yours to organise.",
    "The unit itself is judged by a worker this run starts, in its own context, "
    "which is never shown your report (FR-EXE-14). Your report is read by the "
    "run, not by that judge.",
    "So do not write your report to persuade anybody. State what you did, what "
    "you ran, and what it printed.",
)

#: A builder's brief is a generated prompt plus the memory of every milestone
#: that closed before it (FR-LRN-02, FR-LRN-03), plus what only a run knows.
#: One list, read by the thing that builds a brief and by the thing that checks
#: one — the same reason `PROMPT_PARTS` exists.
BRIEF_PARTS = (tuple(plan.PROMPT_PARTS) + loop.LOOP_PARTS
               + ("Prior retrospectives", "Conventions", "How this unit is judged",
                  loop.RUN_GAUNTLET))


class Refused(Exception):
    """A run that will not start, or a dispatch that will not be attempted."""


# ------------------------------------------------------------------ settings

def _commanded(command):
    """Whether a command names both the brief it reads and the report it writes."""
    joined = " ".join(command)
    return BRIEF_PLACEHOLDER in joined and REPORT_PLACEHOLDER in joined


def settings(root):
    """The project's worker configuration, checked before anything is dispatched.

    Every refusal here happens before a single process starts. A run that
    discovers halfway through that it has no judge has already written half a
    milestone's worth of status it cannot justify.
    """
    path = paths.resolve(root, SETTINGS)
    if not os.path.exists(path):
        raise Refused("%s does not exist; a run needs to be told what its "
                      "workers are" % SETTINGS)
    try:
        with open(path, encoding="utf-8") as handle:
            held = json.loads(handle.read())
    except (OSError, ValueError) as error:
        raise Refused("%s could not be read: %s" % (SETTINGS, error))
    if not isinstance(held, dict):
        raise Refused("%s must hold an object" % SETTINGS)

    found = held.get("workers")
    if not isinstance(found, list) or not found:
        raise Refused("%s names no workers" % SETTINGS)
    for one in found:
        if not isinstance(one, dict) or not one.get("name"):
            raise Refused("every worker in %s needs a name" % SETTINGS)
        if one.get("role") not in ROLES:
            raise Refused("worker %s has role %r; a worker is a %s"
                          % (one.get("name"), one.get("role"), " or a ".join(ROLES)))
        command = one.get("command")
        if not isinstance(command, list) or not command:
            raise Refused("worker %s states no command" % one["name"])
        if not _commanded(command):
            raise Refused("worker %s must name %s and %s in its command, so it "
                          "can be told what to do and say what it did"
                          % (one["name"], BRIEF_PLACEHOLDER, REPORT_PLACEHOLDER))
    for role in REQUIRED_ROLES:
        if not [one for one in found if one["role"] == role]:
            raise Refused("%s names no %s worker; nothing would %s the work"
                          % (SETTINGS, role, role))

    layers = [one["id"] for one in schema.ENUMS["testLayers"]]
    gauntlet = held.get("gauntlet") or {}
    if not isinstance(gauntlet, dict) or not gauntlet:
        raise Refused("%s states no verification gauntlet; there would be "
                      "nothing to prove a unit with" % SETTINGS)
    for layer, command in gauntlet.items():
        if layer not in layers:
            raise Refused("%s is not a verification layer; the documented set "
                          "is %s" % (layer, ", ".join(layers)))
        if not isinstance(command, list) or not command:
            raise Refused("the %s gauntlet states no command" % layer)

    held.setdefault("ceiling", DEFAULT_CEILING)
    held.setdefault("attempts", DEFAULT_ATTEMPTS)
    for name in ("ceiling", "attempts"):
        if not isinstance(held[name], int) or held[name] < 1:
            raise Refused("%s must be a whole number of at least one" % name)
    held.setdefault("substitutes", {})

    # A wall-clock bound on one dispatch. Checked for every worker as well as
    # for the project, and here rather than at the dispatch, for the reason
    # every other refusal in this function is here: a run that discovers its
    # settings are unreadable halfway through has already spent an hour.
    held.setdefault("timeout", DEFAULT_TIMEOUT)
    for stated in [held] + list(found):
        if stated.get("timeout") is None:
            continue
        if not isinstance(stated["timeout"], int) or stated["timeout"] < 1:
            raise Refused("timeout must be a whole number of seconds of at "
                          "least one, or null for no bound at all")

    # One more thing a project may name, and the reason it is not called
    # `ceiling`: that word is already taken here by how many workers may run at
    # once. Two meanings one line apart is the collision this codebase keeps
    # having to document, so the higher target is `aim` (M14-02).
    aim = held.setdefault("aim", None)
    if aim is not None and not isinstance(aim, str):
        raise Refused("aim must be one named thing a critic can open, as text")
    return held


# ------------------------------------------------------------ worker selection

def _pool(config, role):
    return [one for one in config["workers"] if one["role"] == role]


def bound(config, worker):
    """How long this dispatch gets, in seconds, or None for as long as it likes.

    A worker may state its own — an agent that thinks for an hour and a linter
    that answers in a second are both workers — and a worker that states `null`
    has said something, so its silence is not filled in from the project.
    """
    if "timeout" in (worker or {}):
        return worker["timeout"]
    return config.get("timeout")


def suits(worker, entry):
    """Whether this worker is allowed to take this unit.

    A worker that names no `suits` takes anything; one that names some takes
    only those implementation layers.
    """
    named = worker.get("suits")
    return not named or entry.get("layer") in named


def choose(config, entry, role=BUILD):
    """The least capable worker sufficient for this unit (FR-EXE-13).

    `cost` is the project's own number and means nothing to this module beyond
    "smaller first"; ties break on the name so the same plan chooses the same
    worker every time (NFR-GEN-01). A unit may name one outright, and the
    override is recorded by being in the document.
    """
    pool = _pool(config, role)
    named = entry.get("worker") if role == BUILD else None
    if named:
        for one in pool:
            if one["name"] == named:
                return one
        raise Refused("%s asks for worker %s, which is not configured"
                      % (entry.get("id"), named))
    fit = [one for one in pool if suits(one, entry)]
    if not fit:
        raise Refused("no %s worker suits %s, whose layer is %s"
                      % (role, entry.get("id"), entry.get("layer") or "unstated"))
    return sorted(fit, key=lambda one: (one.get("cost", 0), one["name"]))[0]


def gauntlet(config, entry):
    """The checks this unit must pass, by layer.

    Read from the configuration and from the unit's own declared layers, and
    from nothing else. Which worker was chosen cannot reach this (M11-P1-T4-C1):
    a cheaper builder does not get an easier bar.
    """
    stated = config["gauntlet"]
    return collections.OrderedDict(
        (layer, list(stated[layer])) for layer in entry.get("testLayers") or ()
        if layer in stated)


def unproved_layers(config, entry):
    """Layers the unit names that the project has no command for."""
    return [layer for layer in entry.get("testLayers") or ()
            if layer not in config["gauntlet"]]


# ------------------------------------------------------------------ the units

Unit = collections.namedtuple("Unit", "id entry document milestone")


def units(root):
    """Every unit of work in the project, read fresh from the plan documents.

    Called on every iteration and cached nowhere, which is the whole of
    M11-P1-T1-C2: a status somebody changed by hand between iterations is read
    on the next one because there is nothing else to read.
    """
    found = collections.OrderedDict()
    for path in status.documents(root):
        _, spec = status.read(path)
        milestone = status.milestone_of(spec)
        for entry in status.tasks(spec):
            found[entry["id"]] = Unit(entry["id"], entry, path, milestone)
    return found


def catalog(root):
    """Identifier to title, for everything a unit is allowed to be aiming at.

    Read from the plan documents' own embedded `catalog` map, which the plan
    generator wrote there from the specifications above it. A run that went and
    read those specifications again would be answering a question the document
    it is already holding has answered (ADR-04).
    """
    found = {}
    for path in status.documents(root):
        _, spec = status.read(path)
        held = spec.get("catalog")
        if isinstance(held, dict):
            found.update(held)
    return found


def state(unit):
    return unit.entry.get("status") or schema.NOT_STARTED


def satisfied(found, identifier):
    """Whether the thing this unit waits on is passing.

    A dependency may name a task, a phase or a milestone. A task is looked up; a
    phase or milestone is every unit beneath it, which must all be passing. A
    name nothing defines is not satisfied — the unit waits rather than running
    against something that may not exist.
    """
    one = found.get(identifier)
    if one is not None:
        return state(one) == schema.PASSING
    beneath = [other for key, other in found.items()
               if key.startswith(identifier + "-")]
    return bool(beneath) and all(state(other) == schema.PASSING
                                 for other in beneath)


def waiting(found, unit):
    """Which of this unit's dependencies are not yet passing."""
    return [one for one in unit.entry.get("dependsOn") or ()
            if not satisfied(found, one)]


def exhausted(ledger, identifier, limit):
    return (ledger["attempts"].get(identifier) or 0) >= limit


def ready(found, ledger, config, wave=None):
    """The units eligible to be dispatched right now.

    Recomputed every iteration, deliberately. A cached ready set is a ready set
    that disagrees with the documents, which is the one thing the plan is for.
    """
    out = []
    for unit in found.values():
        if state(unit) in (schema.PASSING, schema.IN_PROGRESS):
            continue
        if unit.entry.get("autonomy") == schema.HUMAN_GATE:
            continue                                    # M11-P1-T1-C1
        if exhausted(ledger, unit.id, config["attempts"]):
            continue
        if waiting(found, unit):
            continue
        if wave is not None and unit.milestone not in wave:
            continue
        out.append(unit)
    return out


# ------------------------------------------------------------------ the waves

def order(root):
    """The wave order, read from the plan index rather than derived again.

    The index document already states it, computed from the milestone graph when
    the plan was generated. Deriving it a second time here would be a second
    answer to one question (ADR-04).
    """
    for path in status.documents(root):
        _, spec = status.read(path)
        for section in spec.get("sections") or ():
            if isinstance(section, dict) and section.get("type") == "waves":
                return [list(one) for one in section.get("waves") or ()]
    return []


def current(rounds, found, ledger, config):
    """The earliest wave with work left in it, or None when there is none.

    A milestone whose units are all finished — passing, human-gated or out of
    attempts — no longer holds its wave open, so a run is never stalled by work
    that is never going to move (FR-EXE-02, and the other half of FR-EXE-07).
    """
    for wave in rounds or []:
        for unit in found.values():
            if unit.milestone not in wave:
                continue
            if state(unit) == schema.PASSING:
                continue
            if unit.entry.get("autonomy") == schema.HUMAN_GATE:
                continue
            if exhausted(ledger, unit.id, config["attempts"]):
                continue
            return wave
    return None


# ------------------------------------------------------------ write-set safety

def _norm(path):
    return os.path.normpath(str(path)).replace(os.sep, "/").lstrip("./")


def writes(entry):
    return [_norm(one) for one in entry.get("writes") or ()]


def strays(entry):
    """Paths an earlier report named that this unit's declared list does not.

    Kept beside the declared list rather than folded into it, because two
    questions want the same paths and different answers. `strayed` must go on
    reporting the write every time it happens — a shared manifest is still not
    this unit's to own, and silencing the notice would lose the only record
    that the plan cannot express it. `collides` must stop reading these two
    units as disjoint, because reality has now said otherwise.
    """
    return [_norm(one) for one in entry.get("strays") or ()]


#: The characters that make a path segment a pattern rather than a name.
GLOB = "*?["


def within(path):
    """A declared path reduced to the literal directory it cannot escape.

    Plans declare `src/storage/**`, not `src/storage`, and this check compared
    whole strings — so the two forms of one claim meant different things and the
    glob form matched nothing. `src/storage/**` and `src/storage/client.ts` were
    computed as disjoint and dispatched side by side, which is the exact failure
    the write-set rule exists to prevent, on every plan whose author used a
    pattern. Reducing to the prefix rather than matching the pattern widens the
    claim, and widening is the safe direction here: the cost of a collision this
    reports and reality would not is one unit waiting its turn, and the cost of
    the reverse is two workers overwriting each other.
    """
    kept = []
    for one in _norm(path).split("/"):
        if any(mark in one for mark in GLOB):
            break
        kept.append(one)
    return "/".join(kept)


def overlap(left, right):
    """Whether two declared paths can touch the same bytes."""
    one, other = within(left), within(right)
    if not one or not other:
        # A claim on everything, or a pattern from the first segment. Either way
        # nothing can be said to lie outside it.
        return True
    return one == other or one.startswith(other + "/") or other.startswith(one + "/")


def strayed(unit, changed, beside=()):
    """What a report named that its declared write set does not cover.

    Returns the out-of-set paths, and the subset of them that a unit running
    BESIDE this one had declared. Both from `writes`, `within` and `overlap` —
    the same three helpers `collides` reads, so the promise the scheduler made
    and the check that it held are one implementation of one claim.

    Two lists rather than one severity, because the two are different facts
    (E2-05). Writing outside the list is usually the only thing possible: a
    route absent from a shared manifest is unreachable, and no per-unit list can
    own a shared manifest — every occurrence observed was legitimate and
    declared. What was actually broken is narrower: two units were dispatched
    together on the strength of lists that did not describe them.

    A unit that declared nothing has no set to be outside of, and it ran alone
    (`collides`), so there was no guarantee to break.
    """
    declared = writes(unit.entry)
    if not declared:
        return [], []
    outside = [one for one in (_norm(path) for path in changed)
               if not any(overlap(one, claim) for claim in declared)]
    clashes = [(one, other.id) for one in outside for other in beside
               if any(overlap(one, claim) for claim in writes(other.entry))]
    return outside, clashes


def collides(first, second):
    """Whether two units may not run at the same time (FR-EXE-06).

    A unit that declares nothing collides with everything, on purpose (M11-04).
    The alternative reading — silence means safe — is a guess, and being wrong
    about it means two workers overwriting each other's edits.
    """
    left, right = writes(first.entry), writes(second.entry)
    if not left or not right:
        return True
    # Declared decides whether there is a claim at all; declared plus strayed
    # decides whether the two claims touch. A unit already seen writing a shared
    # file must not be put beside the next unit that needs the same file.
    left, right = left + strays(first.entry), right + strays(second.entry)
    return any(overlap(one, other) for one in left for other in right)


def recall(ledger, found):
    """Put what earlier attempts actually wrote back in front of the scheduler.

    A declared write set is a prediction made before the code existed, and the
    plan is the owner's document — a run cannot edit it to say otherwise. When
    a report names a path outside the list, the prediction was wrong in the one
    way that matters here: `collides` read two units as disjoint and dispatched
    them together. Remembering the path means the next wave does not re-form
    the same collision, which is the difference between not charging a unit for
    a clash and not doing it to that unit again.
    """
    for identifier, paths in (ledger.get("strays") or {}).items():
        unit = found.get(identifier)
        if unit is not None:
            unit.entry["strays"] = paths


def dispatchable(candidates, running, ceiling):
    """As many ready units as may safely start beside what is already running."""
    picked = []
    for unit in candidates:
        if len(running) + len(picked) >= ceiling:
            break
        if any(collides(unit, other) for other in list(running) + picked):
            continue
        picked.append(unit)
    return picked


# ----------------------------------------------------------------- the ledger

def _ledger_path(root):
    return paths.resolve(root, LEDGER)


def blank():
    return {"next": "", "attempts": {}, "misfires": {}, "done": [],
            "unfinished": {}, "gaps": {}, "standing": {}, "decisions": [],
            "discrepancies": [], "notes": [], "conflicts": {}, "strays": {}}


def load(root):
    """This run's bookmark, or a fresh one. Read before anything else happens."""
    path = _ledger_path(root)
    if not os.path.exists(path):
        return blank()
    try:
        with open(path, encoding="utf-8") as handle:
            held = json.loads(handle.read())
    except (OSError, ValueError) as error:
        raise Refused("the run ledger could not be read: %s" % error)
    if not isinstance(held, dict):
        raise Refused("the run ledger must hold an object")
    fresh = blank()
    fresh.update({key: held[key] for key in fresh if key in held})
    return fresh


def save(root, ledger):
    """Write the ledger. Always called BEFORE the thing it describes happens."""
    directory = os.path.dirname(_ledger_path(root))
    if not os.path.isdir(directory):
        os.makedirs(directory)
    writer.write(_ledger_path(root),
                 json.dumps(ledger, indent=1, sort_keys=True, ensure_ascii=False) + "\n")


def reconcile(root, ledger, found):
    """Where the ledger and the plan disagree, believe the plan and say so.

    The plan document is what a person reads and what the status command wrote;
    the ledger is this run's own note to itself. A note that has drifted is
    corrected, never allowed to correct the thing it was taken from — and the
    drift is recorded, because silently resolving it hides the only evidence
    that something went wrong (M11-P3-T3-C3).
    """
    noted = []
    for identifier in list(ledger["done"]):
        unit = found.get(identifier)
        if unit is None or state(unit) != schema.PASSING:
            noted.append("the ledger records %s as done; the plan does not say "
                         "it is passing — the plan is believed" % identifier)
            ledger["done"].remove(identifier)
    for identifier, unit in found.items():
        if state(unit) == schema.PASSING and identifier not in ledger["done"]:
            noted.append("the plan says %s is passing; this run's ledger never "
                         "recorded it — the plan is believed" % identifier)
            ledger["done"].append(identifier)
    if noted:
        ledger["discrepancies"].extend(noted)
        save(root, ledger)
    return noted


def abandoned(root, ledger, found):
    """Take back the units a previous run was still holding when it stopped.

    In progress means a run is dispatching this unit right now, and a run that
    is starting is dispatching nothing — so a unit reading in progress here was
    left there by a run that did not finish. Nothing else rescued it: `ready`
    skips in progress exactly as it skips passing, `reconcile` reads the done
    list rather than the status, and `stall` looks only at not started and
    blocked. One killed run took its units out of the plan for good.

    Failing rather than not started, and not to be unkind: not started is not
    reachable from in progress in `schema.TRANSITIONS`, and the unit really was
    attempted. The attempt itself was never counted — `short` writes the count
    and a run that dies never reaches it — so coming back costs the unit none of
    its attempts.
    """
    noted = []
    for identifier, unit in found.items():
        if state(unit) != schema.IN_PROGRESS:
            continue
        refused = _write(root, ledger, unit, schema.FAILING)
        if refused:
            ledger["notes"].append("%s: %s" % (identifier, refused))
            continue
        noted.append("the plan says %s is in progress and no run is holding it; "
                     "a run that stopped early left it there — it is taken back"
                     % identifier)
    if noted:
        ledger["discrepancies"].extend(noted)
        save(root, ledger)
    return noted


# ------------------------------------------------------------------ the briefs

def _lines(entry, gap=None):
    """What this unit is, as the builder needs to be told it.

    Through `gauntlet.unit_lines` rather than beside it (M14-01) — the paths
    this unit may write are normalised here, because only a run knows where the
    project root is.
    """
    return loop.unit_lines(entry, gap, writes(entry))


def history(root, milestone):
    """The two memory blocks every brief carries, whether or not there is any.

    Stated even when empty, deliberately: "nothing has closed yet" is a fact a
    builder can act on, and a block that disappears when it has nothing to say
    is a block nobody notices is missing.
    """
    found = learn.prior(root, milestone)
    read = ["%s — %s%s" % (one.milestone,
                           os.path.relpath(one.path, os.path.abspath(root)),
                           " (themes: %s)" % ", ".join(one.tags) if one.tags else "")
            for one in found]
    if read:
        read.append("Read every one of these before you write any code.")
    else:
        read.append("(no milestone has closed yet; there is nothing to read)")
    return [("Prior retrospectives", read),
            ("Conventions", learn.conventions(root))]


def standing_work(standing):
    """What the last attempt left on the working tree, as its successor is told.

    A retry used to arrive at a tree its predecessor had already changed and be
    given no account of it. One attempt rebuilt that inventory by hand and then
    refused to put it in `changes`, on the honest ground that naming it would
    claim work it had not done — and was rejected for naming no file, while the
    next attempt claimed the same files as its own and passed. The rule as
    written rewarded the looser claim, so the run says out loud what `changes`
    is actually for: not authorship, but what gets committed.

    Nothing is asked of a worker for this and no key joins the report contract
    (E2-02) — the run is already holding the report it rejected.
    """
    if not standing or not standing.get("changes"):
        return []
    return (["Attempt %s left these files already standing on the working "
             "tree, uncommitted. You did not write them:"
             % standing.get("attempt", "before this one")]
            + ["  %s" % one for one in standing["changes"]]
            + ["Read them before you start: they are the state you are "
               "continuing from, not a clean tree.",
               "Name the ones your finished work keeps in `changes`. That is "
               "not a claim of authorship — `changes` is the list the run "
               "commits from, and a file left out of it does not land."])


def brief(root, config, unit, gap=None, found=None, titles=None, standing=None):
    """The builder's brief — the same prompt the plan document carries.

    Built through `gauntlet.assemble` rather than beside it, so a brief
    assembled at run time and a prompt written into the plan document cannot
    drift into saying different things about the same unit (FR-EXE-03, M14-01).
    It carries three blocks a plan-time prompt cannot: the retrospectives of the
    milestones that have closed since the plan was written, and what this run
    alone knows — that an independent judge, not this worker, has the last word.
    """
    lines = ["%s %s" % (layer, " ".join(command))
             for layer, command in gauntlet(config, unit.entry).items()]
    waits = list(unit.entry.get("dependsOn") or ())
    return loop.assemble(
        "task",
        os.path.relpath(unit.document, os.path.abspath(root)),
        plan.locked(root), lines or ["(none stated for this unit's layers)"],
        unit=unit.id, title=unit.entry["title"],
        waits=waits,
        unresolved=waiting(found, unit) if found else (),
        bar=loop.criteria_lines(unit.entry),
        aiming=loop.ceiling(unit.entry, titles, (config or {}).get("aim")),
        entry=unit.entry,
        closing=_lines(unit.entry, gap),
        extra=(history(root, unit.milestone)
               + [("How this unit is judged", JUDGED)]
               + ([("Work already on the tree", standing_work(standing))]
                  if standing_work(standing) else [])),
        records_status=True)


def check_brief(text):
    """Which required parts a builder's brief is missing."""
    return [part for part in BRIEF_PARTS if part not in text]


def judgement(root, unit, proved, changed, titles=None):
    """The judge's brief.

    Note what this function is not given: the builder's report. It cannot leak
    what it never receives, which is the whole of M11-P2-T5-C1 and the reason
    the signature looks the way it does rather than taking a result object and
    picking bits out of it.
    """
    criteria = ["%s (%s): %s" % (one.get("id"), one.get("kind"), one.get("text"))
                for one in unit.entry.get("criteria") or ()]
    ran = ["%s — %s exited %s" % (layer, held.get("command"), held.get("code"))
           for layer, held in sorted(proved.items())]
    work = sorted(changed) or ["(the worker named no changed file)"]
    aiming = loop.ceiling(unit.entry, titles)
    return "\n".join([
        "You are judging finished work. You did not build it and you are not "
        "being shown how it was built.",
        "",
        plan.block("Unit", ["%s — %s" % (unit.id, unit.entry["title"]),
                             unit.entry.get("text") or unit.entry["title"]]),
        "",
        plan.block("Acceptance criteria", criteria or ["(none stated)"]),
        "",
        plan.block("Verification already run", ran or ["(nothing was run)"]),
        "",
        plan.block("The work", work + [
            "The plan document: %s"
            % os.path.relpath(unit.document, os.path.abspath(root))]),
        "",
        plan.block("The higher target", aiming or [loop.NO_CEILING]),
        "",
        plan.block("How to judge", list(JUDGE_CONTRACT)),
        "",
        plan.block("Report contract",
                    ['Write JSON to the report path: {"verdict": "pass"} or '
                     '{"verdict": "fail", "gap": "the single largest gap"}.']),
    ])


def check_judgement(text):
    """Which required parts a judgement brief is missing."""
    return [part for part in JUDGE_PARTS if part not in text]


# ---------------------------------------------------------------- the dispatch

def place(root, identifier, attempt, role):
    """Where one dispatch's brief and report live."""
    return paths.resolve(root, WORK, "%s-%d-%s" % (identifier, attempt, role))


def _dispatched(root, directory):
    """Is this a dispatch directory of this project's, and nothing else?

    Asked before the only recursive delete in the method. The path is built by
    `place` from an identifier the plan states, so it cannot reach outside the
    working area — but a delete that trusts its caller is a delete that stops
    being safe the first time somebody gives it a different one.
    """
    area = paths.resolve(root, WORK) + os.sep
    return os.path.abspath(directory).startswith(area)


#: Settings a worker gets unless the operator states otherwise. The worker is
#: told not to stop waiting on its own background work, because a worker that
#: abandons the critics it dispatched ends its turn having thrown away most of
#: what it did.
#:
#: That is not an argument against a bound, and it used to be written here as
#: one. The objection was that a harness which stops waiting kills the worker
#: before it can write its report, so finished work is reported as "no report" —
#: and that is exactly what `recover` now answers: a dispatch that runs out of
#: time is asked once for its account, from the evidence it left on disk, and is
#: charged no attempt for the interruption. The bound and the recovery turn are
#: one mechanism. Neither is safe to have without the other.
#:
#: `setdefault`, so an operator who wants a different ceiling can still export
#: one.
WORKER_DEFAULTS = {"CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0"}


def environment(config, entry):
    """The environment a worker gets: no live credential, and its substitute.

    Every variable whose NAME says it holds a credential is removed, whatever it
    holds (NFR-SEC-02) — the judgement is made on the name because reading the
    value to decide would mean handling it. A unit that runs only against a
    substitution gets exactly the one it names, and nothing else (FR-EXE-05).
    """
    clean = {key: value for key, value in os.environ.items()
             if not safety.names_a_secret(key)}
    for key, value in WORKER_DEFAULTS.items():
        clean.setdefault(key, value)
    if entry.get("autonomy") != schema.AUTO_WITH_MOCK:
        return clean
    named = entry.get("provider")
    if not named:
        raise Refused("%s runs only against a substitution but names none"
                      % entry.get("id"))
    stated = (config.get("substitutes") or {}).get(named)
    if stated is None:
        raise Refused("%s needs the substitute %s, which %s does not configure"
                      % (entry.get("id"), named, SETTINGS))
    clean[named] = stated
    return clean


#: `ran` is false only when the worker never got as far as an account of itself:
#: no API, no network, a missing binary, a host out of memory. That says nothing
#: whatever about the unit, and the unit does not pay an attempt for it.
#:
#: `spent` is what the budget actually went on, for the branch that knows. Empty
#: means the default in `misfired` is the right sentence; a branch that would
#: make that default read false says so here rather than leaving the operator a
#: contradiction to reconcile.
Result = collections.namedtuple("Result", "worker report reason ran spent")
Result.__new__.__defaults__ = (True, "")

#: What the budget went on when every dispatch ran out of time. `misfired`'s own
#: default is written for a worker that never started, and telling an operator no
#: dispatch has started — directly after saying one was stopped for running too
#: long — is two halves of one sentence disagreeing with each other.
OVER_BOUND = "and no dispatch of it has finished within that bound"


def _report(path):
    """A worker's report, or None. Silence, absence and nonsense are all silence."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            held = json.loads(handle.read())
    except (OSError, ValueError):
        return None
    return held if isinstance(held, dict) and held else None


def recover(root, worker, unit, directory, brief_path, report_path, environ,
            timeout=None):
    """Ask once for the report a worker stopped without, and read what it wrote.

    A worker that stops without writing a report has usually done the work: the
    dispatch directory is full of evidence and the tree is changed. It read its
    own summary as the end of the task, or it was stopped for running out of
    time. Its account is the one thing the run cannot reconstruct, so it is
    asked for once before the attempt is spent — re-dispatching the brief would
    throw the work away and build it a second time, against evidence the first
    build left behind.

    Asked whatever the worker exited with, and that is the fix rather than a
    detail of it: this used to be reached only after a clean exit, so a worker
    that was killed — or timed out, which is now every hang — could never get
    here, and the one case recovery exists for was the one case it could not
    serve.

    In the SAME dispatch directory, deliberately: that evidence is what the
    recovery turn is pointed at, so nothing here goes back through `place` and
    nothing is cleared. Every role, not builders only — a judge that stops
    without a verdict has the same problem and the same cheap remedy.

    Once per dispatch and never a loop. A second silence is the silence the unit
    pays for, and is reported exactly as one silence was before this existed.

    Bounded like the first turn, and by the same number. A worker that wedged
    once can wedge again, and an unbounded recovery would hand back exactly the
    hang the bound was added to end. The ceiling that follows is worth stating
    rather than discovering: one dispatch of a thoroughly stuck worker can cost
    up to twice the bound — once building, once being asked what it built.
    """
    path = os.path.join(directory, RECOVERY_BRIEF)
    writer.write(path, loop.RECOVERY % {"unit": unit.id, "brief": brief_path,
                                        "report": report_path})
    command = [word.replace(BRIEF_PLACEHOLDER, path)
                   .replace(REPORT_PLACEHOLDER, report_path)
               for word in worker["command"]]
    # Vetted again although only one path in it has changed. A command is judged
    # as it will be run, and a check skipped because the difference looked small
    # is a check that has stopped being a check.
    broken = safety.refusal(" ".join(command), area=root)
    if broken:
        raise Refused(" ".join(broken))
    try:
        dispatch.launch(command, root, environ, timeout,
                        os.path.join(directory, RECOVERY_LOG))
    except OSError:
        # The first dispatch ran, so the report is what is missing, not the
        # worker. Nothing more is known than was known before recovery.
        return None
    return _report(report_path)


def run_worker(root, config, unit, role, text, attempt):
    """Write a brief, run the worker that answers it, read what it left behind.

    The only part of a cycle that runs concurrently, and the only part that
    writes nothing shared: a brief and a report, in a directory named for this
    one dispatch.
    """
    try:
        worker = choose(config, unit.entry, role)
        environ = environment(config, unit.entry)
    except Refused as error:
        return Result("", None, str(error))
    directory = place(root, unit.id, attempt, role)
    if os.path.isdir(directory) and _dispatched(root, directory):
        # A dispatch directory is named for the attempt, so an attempt that runs
        # twice reuses the one before it — which is exactly what a run that died
        # before it could count the attempt comes back to. NOTHING in there
        # belongs to this dispatch yet: last time's report is read as this one's
        # answer, last time's working notes are read as this one's account, and
        # last time's scratch trees are picked up by any check whose argument is
        # a filter rather than a path. Emptied, not tidied key by key.
        shutil.rmtree(directory)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    brief_path = os.path.join(directory, "brief.md")
    report_path = os.path.join(directory, "report.json")
    writer.write(brief_path, text)

    command = [word.replace(BRIEF_PLACEHOLDER, brief_path)
                   .replace(REPORT_PLACEHOLDER, report_path)
               for word in worker["command"]]
    broken = safety.refusal(" ".join(command), area=root)
    if broken:
        # Reported with the rule that blocked it, and not attempted in some
        # other shape (M11-P2-T4-C3). A refusal worked around is not a refusal.
        return Result(worker["name"], None, " ".join(broken))

    limit = bound(config, worker)
    try:
        code, expired = dispatch.launch(command, root, environ, limit,
                                        os.path.join(directory, "%s.log" % role))
    except OSError as error:
        return Result(worker["name"], None,
                      "the worker could not be run: %s" % error, False)
    held = _report(report_path)
    if held is None:
        # Asked for its account whatever it exited with, which is the whole of
        # the fix. The exit status used to be read first, and a worker that was
        # killed — or timed out, which is now every hang — exits non-zero, so
        # the one turn that exists to rescue finished work was unreachable from
        # the only case that needed rescuing. The OSError above already caught
        # the worker that never started, so anything arriving here ran.
        try:
            held = recover(root, worker, unit, directory, brief_path,
                           report_path, environ, limit)
        except Refused as error:
            return Result(worker["name"], None, str(error))
    if held is None:
        if expired:
            # `ran` false: a bound is wall-clock, so this says the worker took
            # too long and nothing at all about the unit. The unit is not
            # charged for it (see `misfired`), and a host that can finish no
            # dispatch still stops the run rather than looping.
            #
            # What the dispatch started is asked about here and nowhere else,
            # because this is the one moment the run knows a worker was ended
            # before it could put its own checks away (R2-09). One sentence
            # folded into the reason already being composed: it then rides
            # `settle`, `misfired` and `summary` with nothing new to plumb.
            up = containers(root)
            return Result(worker["name"], None,
                          "the worker did not finish within %d seconds and was "
                          "stopped; what it printed is in %s%s"
                          % (limit, os.path.join(directory, "%s.log" % role),
                             ("; still up on this host: %s" % up) if up else ""),
                          False, OVER_BOUND)
        if code != 0:
            return Result(worker["name"], None,
                          "the worker did not run: exit %d" % code, False)
        return Result(worker["name"], None, "the worker returned no report")
    return Result(worker["name"], held, "")


# ------------------------------------------------------------------- the cycle

def prove(root, config, unit, disagreed=None):
    """Run the unit's gauntlet and record what each check actually returned.

    Run here rather than trusted from the report: an exit status this module
    watched is evidence, and a worker's account of one is a claim.

    A layer that fails is run once more before it costs the unit anything. A
    check that fails and then passes on a tree nothing has touched in between is
    evidence about the check, not about the work — and charging an attempt for
    it threw away two hours of finished work that never reached a judge. Both
    runs failing means what it always meant, and the message is unchanged.

    One re-run, not a configured number: a layer that needs three goes is broken
    in a way a knob would hide rather than fix. `status.ran` records evidence
    keyed by layer with the latest winning, so the second run supersedes the
    first with nothing else to plumb. Every disagreement is appended to
    `disagreed`, because a flake nobody can see is a flake nobody fixes.
    """
    missing = unproved_layers(config, unit.entry)
    if missing:
        return "the project states no command for %s" % ", ".join(missing)
    for layer, command in gauntlet(config, unit.entry).items():
        try:
            code = status.ran(root, layer, command, config.get("timeout"))
            if code != 0:
                again = status.ran(root, layer, command, config.get("timeout"))
        except status.Refused as error:
            return str(error)
        if code == 0:
            continue
        if again != 0:
            return "%s failed: %s exited %s" % (layer, " ".join(command), code)
        if disagreed is not None:
            disagreed.append(
                "the %s layer exited %s and then passed on a second run of the "
                "same command over a tree nothing touched in between: %s — the "
                "check is not deterministic and the unit was not charged for it"
                % (layer, code, " ".join(command)))
    return ""


def verdict(result):
    """What a judge's report means. Anything unclear is a failure, by design.

    A judgement that could not be read is a judgement that did not happen, and a
    unit that was not judged has not passed (FR-EXE-14, M11-P2-T5-C3).
    """
    if result.report is None:
        return FAIL, result.reason or "the judge returned no report"
    said = result.report.get("verdict")
    if said == PASS:
        return PASS, ""
    gap = result.report.get("gap") or "the judge failed the work but named no gap"
    return FAIL, gap


#: What a commit identifier looks like, and nothing else does. Checked before
#: the name reaches git, because it arrives in a worker's report: it is the one
#: value in this module that comes from outside the run.
SHA = re.compile(r"^[0-9a-f]{7,40}$")


def in_history(root, sha):
    """The files a commit changed, or why the run will not take the word for it.

    A unit re-dispatched after a previous attempt already committed its work has
    nothing left to put in `changes`, and used to be refused for having nothing
    to say. It may name the commit instead — and this looks the commit up rather
    than believing it, so what reaches the judge is evidence the run observed.
    """
    named = str(sha or "").strip()
    if not SHA.match(named):
        return [], ("landed names %r, which is not a commit identifier"
                    % named)
    command = ["git", "-C", os.path.abspath(root), "show", "--name-only",
               "--format=", named]
    broken = safety.refusal(" ".join(command), area=root)
    if broken:
        return [], " ".join(broken)
    try:
        finished = subprocess.run(command, cwd=os.path.abspath(root),
                                  check=False, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
    except OSError as error:
        return [], ("landed names %s, which could not be looked up: %s"
                    % (named, error))
    if finished.returncode != 0:
        return [], ("landed names %s, which is not in this repository's history"
                    % named)
    files = [line.strip() for line
             in finished.stdout.decode("utf-8", "replace").splitlines()
             if line.strip()]
    if not files:
        return [], "landed names %s, which changed no file" % named
    return files, ""


#: What is up on this host, asked for in docker's own words. `{{.Status}}` is
#: rendered by docker and reads `Up 2 hours`, so the one number an operator needs
#: — how long it has been there — arrives without this package reading the clock
#: (NFR-GEN-01, and `tests/test_writer.py` holds every module to it).
#:
#: A list of words, never a shell line, for the same reason a gauntlet command is
#: one: nothing here expands a glob, a pipe or a variable. Read-only by
#: construction, and that is the whole design — see `containers`.
CONTAINERS = ["docker", "ps", "--format",
              "{{.ID}} {{.Image}} {{.Status}} {{.Names}}"]

#: How long the question above is worth waiting for. Not configurable on purpose.
ASKING = 10


def containers(root):
    """What is still up on the host, or nothing at all. Said, never touched.

    A dispatch that runs out of time is stopped, and whatever its checks started
    is not: a database container outlived one such dispatch by two and a half
    hours, and four later units ran their checks against a service the run
    believed was gone (R2-09).

    This only says what is there. Ending it here was the other option and is the
    wrong one twice over: tearing down a live database is not reliably a
    ten-second job, so the run would be trading one hang for another; and a run
    that removes a container an operator started for their own reasons has
    destroyed something it was never asked to own. A host with legitimate
    long-lived containers lists them with docker's own `Up 3 weeks`, which is the
    disambiguation, and every judgement about what to do is the operator's.

    Silence on every failure, deliberately. No docker, no daemon, or a host that
    has never heard of a container is not a fact about the unit, and a run that
    turned it into one would be reporting on itself.

    Bounded, because of WHERE it is asked. This runs while the run is recovering
    from a dispatch that already stopped moving, so a docker CLI that hangs
    instead of failing would wedge the run at the one moment it is trying to get
    itself out of a wedge. `ASKING` is not a knob and must not become one: a
    listing that cannot be produced in seconds is one the operator is better off
    without.
    """
    broken = safety.refusal(" ".join(CONTAINERS), area=root)
    if broken:
        return ""
    try:
        finished = subprocess.run(CONTAINERS, cwd=os.path.abspath(root),
                                  check=False, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, timeout=ASKING)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if finished.returncode != 0:
        return ""
    listed = [line.strip() for line
              in finished.stdout.decode("utf-8", "replace").splitlines()
              if line.strip()]
    return "; ".join(listed)


def check_report(report, unit=None, landed=()):
    """What is wrong with a worker's report, if anything.

    Enforced here rather than requested in prose, because a contract requested
    politely is a contract that erodes (ADR-13). A report must show a check that
    was seen FAILING before the work existed — that is as close as this module
    can get to policing test-first order without re-deriving the work, and the
    ceiling is stated: it proves a failure was observed, not that no code was
    written before it. A report claiming a criterion is met must name the
    command that showed it, and must name the files it changed — or, where an
    earlier attempt already committed them and there is nothing left to name,
    the commit that holds them, which `settle` looks up before calling this.

    Every key read here is rendered into the brief from `loop.REPORT_SHAPE`, and
    a test in `tests/test_gauntlet.py` holds the two together in both
    directions. That test exists because this function and the contract grew
    apart once: the contract named no key at all while this read six, so a
    worker could satisfy every stated word and be rejected every time.
    """
    wrong = []
    named = report.get("unit")
    if unit is not None and named and str(named) != str(unit):
        wrong.append("this report is for %s and the brief was for %s"
                     % (named, unit))
    red = report.get("red")
    if not isinstance(red, dict) or not red.get("command"):
        wrong.append("no observed failing test: name the command that failed "
                     "before the implementation existed")
    elif int(red.get("code") or 0) == 0:
        wrong.append("the reported failing test exited zero, so nothing was "
                     "seen failing")
    criteria = report.get("criteria") or {}
    if isinstance(criteria, list):
        # The contract asks for "its identifier, and whether it is met" and
        # never names a shape, so a list of {id, met} is a faithful reading of
        # it. Refusing that would burn every attempt on a brief that would
        # produce the same shape again.
        criteria = {one.get("id"): one.get("met")
                    for one in criteria if isinstance(one, dict) and one.get("id")}
        # A list of bare identifiers says who, never whether — unreadable, and
        # emptied here so the sentence below names it.
        criteria = criteria or None
    if not isinstance(criteria, dict):
        wrong.append("the criteria are not readable: state each criterion's "
                     "identifier and whether it is met")
        criteria = {}
    claimed = sorted(str(key) for key, met in criteria.items() if met)
    ran = [one for one in report.get("commands") or ()
           if isinstance(one, dict) and one.get("command")]
    if claimed and not ran:
        wrong.append("claims %s met but names no command that showed it"
                     % ", ".join(claimed))
    changed = [str(one) for one in report.get("changes") or () if str(one).strip()]
    if claimed and not changed and not landed:
        # The list is taken at its word rather than derived from the working
        # tree, and the ceiling is worth stating: units run beside each other,
        # so every one of their files is uncommitted at once and `git status`
        # here would sweep in a neighbour's work. What the worker names is the
        # only account of its own changes that is its own. `landed` is the one
        # exception and is the opposite kind of thing: not a claim taken at its
        # word but a commit the run looked up for itself.
        wrong.append("claims %s met but names no changed file; work left out "
                     "of `changes` is not committed, and if it is already "
                     "committed name that commit in `landed`"
                     % ", ".join(claimed))
    return wrong


def _write(root, ledger, unit, wanted):
    """Set a status. Returns "" or why it could not — naming contention on a repeat.

    Only an outside editor can cause this: a run has one writer (LD-03), and
    everything here that writes runs on one thread. Once is a race worth trying
    again on the next iteration. Twice in a row is somebody else working in the
    same files, and reporting "conflict" a second time would be pretending that
    was news (M11-P1-T3-C2).
    """
    try:
        status.set_status(root, unit.id, wanted)
    except status.Refused as error:
        seen = (ledger["conflicts"].get(unit.id) or 0) + 1
        ledger["conflicts"][unit.id] = seen
        if seen >= 2:
            return ("contention: %s changed underneath this run twice in a row; "
                    "another writer is active" % os.path.basename(unit.document))
        return str(error)
    ledger["conflicts"].pop(unit.id, None)
    return ""


def decisions(ledger, unit, report):
    """Carry a worker's own calls into the ledger, with the reasoning.

    FR-EXE-08 is two obligations, not one: do not ask, AND write down what you
    decided instead. A run that only does the first is a run nobody can audit.
    """
    kept = []
    for one in report.get("decisions") or ():
        if not isinstance(one, dict):
            continue
        held = {"unit": unit.id,
                "decision": one.get("decision") or one.get("choice") or "",
                "why": one.get("why") or one.get("rationale") or ""}
        ledger["decisions"].append(held)
        kept.append(held)
    return kept


def reclaim(root, ledger, unit):
    """Take a unit back from a worker that recorded its own status.

    A run sets a unit in-progress before dispatching it, so anything else when
    the worker returns was written by the worker. That defeated FR-EXE-14 twice
    over: the run's own write of the same status is allowed straight through as
    a repeat rather than a move, and the demote the run needs when the work
    falls short is not a move the claimed status may make — so a unit that set
    itself as verified stayed that way, dropped out of the ready set, and was
    never attempted again.

    In-progress is reachable from every status in `schema.TRANSITIONS`, which is
    how a run takes a unit back without that table having to be weakened. The
    claim itself is still a failure of the unit: what the run wants back is the
    ability to say so.

    Returns why the unit was reclaimed, or "" if nobody touched it.
    """
    try:
        _, _, spec = status.locate(root, unit.id)
    except status.Refused as error:
        return str(error)
    found = status.find(spec, unit.id) or {}
    carried = found.get("status") or schema.NOT_STARTED
    if carried == schema.IN_PROGRESS:
        return ""
    refused = _write(root, ledger, unit, schema.IN_PROGRESS)
    if refused:
        return refused
    return ("the worker recorded this unit as %s itself; a unit is graded by "
            "the run and by a critic that never saw the worker's report, never "
            "by the worker that built it (FR-EXE-14)"
            % status.label("statuses", carried).lower())


def short(root, config, ledger, unit, reason, attempt):
    """A unit that did not make it this time. Bounded, then blocked, never stalled.

    The reason is kept as the next attempt's gap even when it came from a failed
    check rather than a judge — a builder told "the unit layer failed: … exited
    1" is better briefed than one handed its original instructions again.
    """
    ledger["attempts"][unit.id] = attempt
    ledger["gaps"][unit.id] = reason
    if attempt >= config["attempts"]:
        ledger["unfinished"][unit.id] = reason
        refused = _write(root, ledger, unit, schema.BLOCKED)
    else:
        refused = _write(root, ledger, unit, schema.FAILING)
    if refused:
        ledger["notes"].append("%s: %s" % (unit.id, refused))
    save(root, ledger)
    return reason


def misfired(root, config, ledger, unit, reason,
             spent="and no dispatch of it has started"):
    """A dispatch that never became the unit's own attempt. It does not pay.

    Two things arrive here and share one counter, because they are one fact:
    the unit was denied a fair go by something outside itself.

    A worker that could not start — no API, no network, a binary that is not
    there — has said nothing about the unit, and charging an attempt for it is
    charging the unit for the state of the host.

    A report that collided with work running beside it is that same claim one
    step along (R2-07 follow-up). A shared append-only file is in nobody's
    declared write set, so `collides` reads two units that must both add a line
    to it as disjoint and dispatches them together. The unit did the only thing
    that ships the work; the run chose who it ran beside. `spent` says which of
    the two exhausted the budget — the sentences are not interchangeable.

    Counted all the same, and against the same bound: a host that can start no
    worker at all, or a wave that keeps re-forming the same collision, would
    otherwise keep this unit in the ready set for ever, and a run that never
    ends is worse than one that stops and says why.
    """
    missed = (ledger["misfires"].get(unit.id) or 0) + 1
    ledger["misfires"][unit.id] = missed
    if missed >= config["attempts"]:
        # The whole budget at once, because the attempt count is the only brake
        # the ready set has: a blocked unit is still dispatchable, and a unit
        # nothing has charged comes straight back round.
        return short(root, config, ledger, unit,
                     "%s, %s" % (reason, spent),
                     config["attempts"])
    refused = _write(root, ledger, unit, schema.FAILING)
    if refused:
        ledger["notes"].append("%s: %s" % (unit.id, refused))
    ledger["notes"].append("%s: %s — the unit was not charged an attempt"
                           % (unit.id, reason))
    save(root, ledger)
    return reason


def announce(out, text):
    """Say something, now rather than whenever the buffer feels like it.

    Workers write straight to the same console, so a buffered line from the run
    lands after output from a process it started and the order reads as a lie.
    """
    if out is None:
        return
    out.write(text + "\n")
    try:
        out.flush()
    except (AttributeError, ValueError):
        pass


def settle(root, config, ledger, unit, result, attempt, out=None, beside=()):
    """Everything that happens once a builder returns. All of it on one thread.

    `beside` is every unit whose dispatch overlapped this one's in time, which
    only the run knows and only it can hand over.
    """
    def say(text):
        announce(out, text)

    # Before anything else, and before the report is even looked at: every path
    # out of here writes a status, and none of them can while the worker still
    # holds one it wrote itself.
    seized = reclaim(root, ledger, unit)
    if seized:
        say("  %s attempt %d — %s" % (unit.id, attempt, seized))
        return short(root, config, ledger, unit, seized, attempt)

    if result.report is None:
        say("  %s attempt %d — %s" % (unit.id, attempt, result.reason))
        if not result.ran:
            # `misfired`'s default says no dispatch has started, which is true of
            # a worker that never ran and false of one that was stopped for
            # running too long. The branch that knows which of the two happened
            # is the one that composed the reason, so it says so and this passes
            # it on rather than guessing from the wording.
            if result.spent:
                return misfired(root, config, ledger, unit, result.reason,
                                spent=result.spent)
            return misfired(root, config, ledger, unit, result.reason)
        return short(root, config, ledger, unit, result.reason, attempt)

    decisions(ledger, unit, result.report)
    # Kept before anything can reject the report, and dropped only on a pass:
    # every path out of here below this line leaves these files on the tree.
    left = [str(one) for one in result.report.get("changes") or () if str(one).strip()]
    if left:
        ledger["standing"][unit.id] = {"attempt": attempt, "changes": left}
    denied = result.report.get("denied") or []
    if denied:
        stated = "; ".join(
            "%s (blocked by %s)" % (one.get("action"), one.get("rule"))
            if isinstance(one, dict) else str(one) for one in denied)
        # Recorded with the rule that blocked it (NFR-SEC-05), and that is all.
        # A denial is what the plan would not let the unit do, not evidence about
        # the work: whether the criteria are met is a separate question, and the
        # gauntlet and the critic below are the things that answer it. Failing
        # the attempt here made the honest answer the losing one — `denied` is a
        # required key whose own contract asks for the disclosure, so a worker
        # that respected a boundary and said so was beaten by one that stayed
        # quiet, and the unit exhausted without its gauntlet ever running.
        say("  %s attempt %d — permission denied: %s" % (unit.id, attempt, stated))
        ledger["notes"].append("%s: a permission was denied: %s"
                               % (unit.id, stated))

    # Looked up before the report is judged, because whether the report is
    # complete depends on what the commit holds. `result.report.get` and not a
    # helper: the test in `tests/test_gauntlet.py` that keeps the contract and
    # the reader in step reads this function for the keys it names.
    landed = []
    stated = str(result.report.get("landed") or "").strip()
    if stated:
        landed, why = in_history(root, stated)
        if why:
            say("  %s attempt %d — %s" % (unit.id, attempt, why))
            return short(root, config, ledger, unit, why, attempt)

    malformed = check_report(result.report, unit.id, landed)
    if malformed:
        say("  %s attempt %d — %s" % (unit.id, attempt, "; ".join(malformed)))
        return short(root, config, ledger, unit, "; ".join(malformed), attempt)

    outside, clashes = strayed(unit, result.report.get("changes") or (), beside)
    for path in outside:
        note = ("wrote %s, which its declared write set does not cover — other "
                "units are scheduled beside this one on the strength of that "
                "list" % path)
        say("  %s attempt %d — %s" % (unit.id, attempt, note))
        ledger["notes"].append("%s: %s" % (unit.id, note))
    if outside:
        # Recorded before the clash below decides anything, so the memory
        # survives the dispatch that is about to be thrown away.
        seen = ledger.setdefault("strays", {}).setdefault(unit.id, [])
        seen.extend(one for one in outside if one not in seen)
    if clashes:
        broke = "; ".join("%s is declared by %s, which was running beside it"
                          % (path, other) for path, other in clashes)
        note = ("wrote outside its declared write set into work running at the "
                "same time: %s" % broke)
        say("  %s attempt %d — %s" % (unit.id, attempt, note))
        return misfired(root, config, ledger, unit, note,
                        spent="and the run keeps scheduling it into that clash")

    disagreed = []
    failed = prove(root, config, unit, disagreed)
    for line in disagreed:
        say("  %s attempt %d — %s" % (unit.id, attempt, line))
        ledger["notes"].append("%s: %s" % (unit.id, line))
    if failed:
        say("  %s attempt %d — %s" % (unit.id, attempt, failed))
        return short(root, config, ledger, unit, failed, attempt)

    proved = {layer: held for layer, held in status.evidence(root).items()
              if layer in (unit.entry.get("testLayers") or ())}
    changed = [str(one) for one in result.report.get("changes") or ()]
    # Two lists, and keeping them apart is deliberate. The judge is shown the
    # landed files as well, because those files ARE the work and a critic handed
    # "(the worker named no changed file)" is judging nothing. `status.commit`
    # below is shown only `changed`: the landed files are in history already,
    # and staging them again says a second time what git already recorded.
    judged = run_worker(root, config, unit, JUDGE,
                        judgement(root, unit, proved,
                                  sorted(set(changed) | set(landed)),
                                  catalog(root)),
                        attempt)
    kind, gap = verdict(judged)
    if kind == FAIL:
        say("  %s attempt %d — judged short: %s" % (unit.id, attempt, gap))
        return short(root, config, ledger, unit, gap, attempt)

    refused = _write(root, ledger, unit, schema.PASSING)
    if refused:
        say("  %s attempt %d — %s" % (unit.id, attempt, refused))
        return short(root, config, ledger, unit, refused, attempt)
    status.tick(root, unit.id)
    if config.get("commit", True):
        try:
            status.commit(root, unit.id, changed)
        except status.Refused as error:
            # A note in the ledger was not enough. The commit is one thing, so a
            # single unstageable path — one the report named that git can
            # neither find nor track — takes the work and the plan document down
            # with it, and passing on top of that records a status true of a
            # tree nobody has (NFR-EXE-11). It is the report that was wrong, and
            # the next attempt is told exactly what git said about it.
            say("  %s attempt %d — nothing was committed: %s"
                % (unit.id, attempt, error))
            _write(root, ledger, unit, schema.IN_PROGRESS)
            return short(root, config, ledger, unit,
                         "the work was proved but none of it was committed: %s"
                         % error, attempt)
    ledger["attempts"][unit.id] = attempt
    ledger["gaps"].pop(unit.id, None)
    ledger["standing"].pop(unit.id, None)
    if unit.id not in ledger["done"]:
        ledger["done"].append(unit.id)
    save(root, ledger)
    say("  %s attempt %d — passing" % (unit.id, attempt))
    return ""


def stopped(found, ledger, config, identifier):
    """Whether the thing a unit waits on has stopped moving of its own accord."""
    if exhausted(ledger, identifier, config["attempts"]):
        return True
    one = found.get(identifier)
    if one is None:
        return False
    return state(one) in (schema.FAILING, schema.BLOCKED)


def stall(root, found, ledger, config):
    """Say so in the plan when a unit is waiting on something that has stopped.

    Without this, a unit whose dependency failed just quietly never appears in
    the ready set, and a person reading the plan sees "not started" with no
    explanation. Blocked is not terminal: when the dependency passes the unit is
    eligible again on the next iteration, with nobody asked (M11-P3-T2-C2).
    """
    marked = []
    for unit in found.values():
        held = state(unit)
        if held == schema.NOT_STARTED:
            if any(stopped(found, ledger, config, one)
                   for one in waiting(found, unit)):
                status.set_status(root, unit.id, schema.BLOCKED)
                marked.append(unit.id)
        elif held == schema.BLOCKED and _free(found, ledger, config, unit):
            # The other half of "blocked is not terminal", and it was missing:
            # dispatch never filtered on blocked, so the run carried on, but the
            # plan a person opens went on saying a unit was waiting on something
            # that had long since passed. A document that is wrong about what is
            # holding work up is the one thing a plan is for.
            status.set_status(root, unit.id, schema.NOT_STARTED)
            marked.append(unit.id)
    return marked


def _free(found, ledger, config, unit):
    """Whether a blocked unit is only blocked by history now.

    A unit blocked by its own exhausted attempts stays blocked: nothing about it
    has changed. That is asked as one question rather than two — `short` writes
    `ledger["unfinished"]` and the attempt count together, always, so checking
    both would mean two guards no test could tell apart and one of them free to
    rot.
    """
    if exhausted(ledger, unit.id, config["attempts"]):
        return False
    return not any(stopped(found, ledger, config, one)
                   for one in waiting(found, unit))


# ------------------------------------------------------------- the retrospective

#: What a retrospective worker is asked for. It is handed the draft — the facts
#: the run already recorded — and asked to answer the three questions, not to
#: reinvent the facts.
RETRO_CONTRACT = (
    "Below is a drafted retrospective for a milestone that has just finished. "
    "Every fact in it came from the run itself.",
    "Answer the three questions it leaves open. Be specific: a lesson nobody "
    "could act on is not a lesson.",
    "Keep every decision line exactly as it stands. They are the record of "
    "what was decided without asking, and a milestone does not close without "
    "them.",
    "State the themes on the '%s' line. Reuse a theme an earlier retrospective "
    "already used where it fits; a new word for an old problem hides the "
    "repetition." % learn.TAG_HEADER,
    'Write JSON to the report path: {"text": "the finished retrospective, in '
    'markdown"}.',
    GUARD,
)


def complete(found):
    """Milestones every one of whose units is passing, with their entries."""
    grouped = collections.OrderedDict()
    for unit in found.values():
        grouped.setdefault(unit.milestone, []).append(unit)
    return collections.OrderedDict(
        (key, [one.entry for one in held]) for key, held in grouped.items()
        if held and all(state(one) == schema.PASSING for one in held))


def polish(root, config, ledger, milestone):
    """Hand the draft to a retrospective worker, if the project names one.

    The draft already closes the milestone. So a polished version that does not
    is thrown away and the draft kept: prose is worth having, but not at the
    price of the record it was supposed to be prose about (M12-04).
    """
    if not _pool(config, RETROSPECTIVE):
        return ""
    target = learn.path(root, milestone)
    with open(target, encoding="utf-8") as handle:
        drafted = handle.read()
    unit = Unit(milestone, {"id": milestone, "title": "retrospective"},
                target, milestone)
    result = run_worker(root, config, unit, RETROSPECTIVE,
                        "\n".join(list(RETRO_CONTRACT) + ["", drafted]), 1)
    if result.report is None:
        return result.reason
    text = result.report.get("text")
    if not isinstance(text, str) or not text.strip():
        return "the retrospective worker returned no text"
    writer.write(target, text if text.endswith("\n") else text + "\n")
    try:
        learn.close(root, milestone, ledger)
    except learn.Refused as error:
        writer.write(target, drafted)
        return "the polished retrospective was not kept: %s" % error
    return ""


def remember(root, config, ledger, date, out=None):
    """Write a retrospective for every milestone that finished (FR-LRN-01).

    Only for a milestone that actually closed. A milestone still in progress has
    nothing to look back on, and writing one early would mean the next run reads
    a retrospective of work that had not happened yet.

    An existing retrospective is never overwritten: it may have been written by
    hand or polished by a worker, and this run has no better claim on it.
    """
    written = []
    for milestone, entries in complete(units(root)).items():
        if os.path.exists(learn.path(root, milestone)):
            continue
        learn.record(root, milestone, ledger, date, entries)
        note = polish(root, config, ledger, milestone)
        if note:
            ledger["notes"].append("%s retrospective: %s" % (milestone, note))
        try:
            learn.close(root, milestone, ledger)
        except learn.Refused as error:
            ledger["notes"].append(str(error))
            continue
        written.append(milestone)
        announce(out, "%s closed — retrospective written" % milestone)
    return written


# -------------------------------------------------------------------- the run

def run(root, out=sys.stdout, date=""):
    """Work the plan until nothing else can move, asking nobody anything."""
    config = settings(root)
    ledger = load(root)
    opening = units(root)
    for line in (reconcile(root, ledger, opening)
                 + abandoned(root, ledger, opening)):
        announce(out, "ledger: %s" % line)
    rounds = order(root)
    running = {}
    # Who overlapped whom in time, recorded at dispatch rather than derived at
    # settle: by the time the second of a pair returns, the first is gone from
    # `running`, and half of every concurrent pair would go unchecked.
    beside = {}

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=config["ceiling"]) as pool:
        # Read once: the identifier-to-title map comes from the specifications
        # above the plan and cannot change while a run is in flight. The unit
        # set below is deliberately the opposite — re-read every iteration.
        titles = catalog(root)
        while True:
            found = units(root)
            recall(ledger, found)
            wave = current(rounds, found, ledger, config) if rounds else None
            candidates = [] if (rounds and wave is None) \
                else ready(found, ledger, config, wave)
            picked = dispatchable(candidates,
                                  [one for one, _ in running.values()],
                                  config["ceiling"])
            for unit in picked:
                attempt = (ledger["attempts"].get(unit.id) or 0) + 1
                # Written before the work starts, not after it finishes: a run
                # killed mid-dispatch has to come back knowing what it was in
                # the middle of (M11-P3-T3-C2).
                ledger["next"] = "dispatch %s, attempt %d" % (unit.id, attempt)
                save(root, ledger)
                refused = _write(root, ledger, unit, schema.IN_PROGRESS)
                if refused:
                    # Retried once against a fresh read, and no further: a second
                    # failure is another writer, not a race (US-EXE-05-S02).
                    refused = _write(root, ledger, unit, schema.IN_PROGRESS)
                if refused:
                    ledger["notes"].append("%s: %s" % (unit.id, refused))
                    announce(out, "held %s — %s" % (unit.id, refused))
                    continue
                announce(out, "dispatch %s (attempt %d)" % (unit.id, attempt))
                # Named at dispatch rather than streamed to the console: four
                # workers interleaving on one terminal is not a record of any of
                # them, and the file is what the operator, the recovery turn and
                # anybody reading afterwards can all open. `place` is
                # deterministic, so this needs nothing from the dispatch itself.
                announce(out, "         log %s"
                         % os.path.join(place(root, unit.id, attempt, BUILD),
                                        "%s.log" % BUILD))
                for other, _ in running.values():
                    beside.setdefault(other.id, []).append(unit)
                    beside.setdefault(unit.id, []).append(other)
                running[pool.submit(run_worker, root, config, unit, BUILD,
                                    brief(root, config, unit,
                                          ledger["gaps"].get(unit.id),
                                          found, titles,
                                          ledger["standing"].get(unit.id)),
                                    attempt)] = (unit, attempt)
            if not running:
                break
            done, _ = concurrent.futures.wait(
                running, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                unit, attempt = running.pop(future)
                settle(root, config, ledger, unit, future.result(), attempt,
                       out, beside.pop(unit.id, ()))
            stall(root, units(root), ledger, config)

    remember(root, config, ledger, date, out)
    ledger["next"] = ""
    save(root, ledger)
    return ledger


# ----------------------------------------------------------------- the reports

def summary(root, ledger):
    """What the run came to, grouped so a person can act on it."""
    found = units(root)
    counts = collections.OrderedDict(
        (one["id"], 0) for one in schema.ENUMS["statuses"])
    for unit in found.values():
        counts[state(unit)] = counts.get(state(unit), 0) + 1
    lines = ["units: %d · %s" % (len(found), " · ".join(
        "%d %s" % (number, name) for name, number in counts.items() if number))]
    if ledger["unfinished"]:
        lines.append("")
        lines.append("out of attempts (%d):" % len(ledger["unfinished"]))
        lines.extend("  %-14s %s" % (key, value)
                     for key, value in sorted(ledger["unfinished"].items()))
    if ledger["decisions"]:
        lines.append("")
        lines.append("decisions taken without asking (%d):"
                     % len(ledger["decisions"]))
        lines.extend("  %-14s %s — %s" % (one["unit"], one["decision"], one["why"])
                     for one in ledger["decisions"])
    raised = learn.escalations(root)
    if raised:
        # FR-LRN-04: at this point it has stopped being advice to the next
        # milestone. Reported here rather than only in the retrospectives,
        # because nobody re-reads eleven files looking for a pattern.
        lines.append("")
        lines.append("themes raised in %d or more milestones — candidate "
                     "changes to the method itself (%d):"
                     % (learn.ESCALATION, len(raised)))
        lines.extend("  %-24s %s" % (one["tag"], ", ".join(one["milestones"]))
                     for one in raised)
    for name, title in (("discrepancies", "plan and ledger disagreed"),
                        ("notes", "notes")):
        if ledger[name]:
            lines.append("")
            lines.append("%s (%d):" % (title, len(ledger[name])))
            lines.extend("  %s" % one for one in ledger[name])
    return "\n".join(lines) + "\n"


def format_ready(root):
    """The ready set, as data a person can read (the M11-P1-T1 refactor)."""
    config = settings(root)
    ledger = load(root)
    found = units(root)
    rounds = order(root)
    wave = current(rounds, found, ledger, config) if rounds else None
    eligible = ready(found, ledger, config, wave)
    lines = ["wave: %s" % (", ".join(wave) if wave else "(none stated)")]
    if not eligible:
        lines.append("nothing is ready")
    for unit in eligible:
        lines.append("  %-14s %-12s %s" % (unit.id, state(unit),
                                           unit.entry["title"]))
    held = [unit for unit in found.values()
            if unit not in eligible and state(unit) != schema.PASSING]
    for unit in held:
        why = waiting(found, unit)
        if unit.entry.get("autonomy") == schema.HUMAN_GATE:
            reason = "human gate"
        elif exhausted(ledger, unit.id, config["attempts"]):
            reason = "out of attempts"
        elif why:
            reason = "waits for %s" % ", ".join(why)
        elif wave is not None and unit.milestone not in wave:
            reason = "a later wave"
        else:
            reason = "in flight"
        lines.append("  %-14s %-12s held: %s" % (unit.id, state(unit), reason))
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------- the command line

USAGE = ("usage: python3 -m z2s.execute [--root DIR] [--date YYYY-MM-DD] "
         "run | ready | report | brief UNIT")


def _root(argv):
    """The project directory, the date it was given, and the rest.

    The date is an argument because nothing in the method reads the clock
    (NFR-GEN-01). A run given none writes a retrospective that says its date is
    not stated, which is true, rather than one that guesses.
    """
    rest = list(argv)
    root, date = ".", ""
    for flag, default in (("--root", root), ("-C", root), ("--date", date)):
        if flag in rest:
            at = rest.index(flag)
            if at + 1 >= len(rest):
                raise Refused("%s needs a value" % flag)
            if flag == "--date":
                date = rest[at + 1]
            else:
                root = rest[at + 1]
            del rest[at:at + 2]
    return rest, root, date


def main(argv, out=sys.stdout):
    try:
        rest, root, date = _root(argv)
    except Refused as error:
        out.write("%s\n%s\n" % (error, USAGE))
        return 2
    if not rest:
        out.write(USAGE + "\n")
        return 2

    action, rest = rest[0], rest[1:]
    try:
        if action == "run":
            ledger = run(root, out, date)
            out.write("\n" + summary(root, ledger))
            return 1 if ledger["unfinished"] else 0
        if action == "ready":
            out.write(format_ready(root))
            return 0
        if action == "report":
            out.write(summary(root, load(root)))
            return 0
        if action == "brief":
            if not rest:
                out.write("brief needs a unit identifier\n")
                return 2
            config = settings(root)
            found = units(root)
            unit = found.get(rest[0])
            if unit is None:
                out.write("%s is not a unit in this plan\n" % rest[0])
                return 2
            out.write(brief(root, config, unit, load(root)["gaps"].get(unit.id),
                            found, catalog(root)))
            out.write("\n")
            return 0
    except (Refused, status.Refused) as error:
        out.write("%s\n" % error)
        return 1

    out.write("%s is not a command\n%s\n" % (action, USAGE))
    return 2


if __name__ == "__main__":                                  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
