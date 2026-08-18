# -*- coding: utf-8 -*-
"""Progress, recorded in the plan document itself.

The plan, the status board and the audit trail are one artefact (ADR-05): a
unit's status and each criterion's tick live in the specification embedded in
the plan document, and there is no tracker anywhere else. That makes this the
one tool in the method that edits a document somebody has already read, so it
is built around two refusals rather than around its writes:

  * **Nothing is written unless it is earned.** A status of the kind that claims
    verification is set only when the layers the task names actually ran and
    passed, evidenced by a record the checker left behind (NFR-EXE-10). The
    evidence is written by whatever ran the check — `ran` executes a command and
    records its exit status — so it is an observation, never a claim.
  * **Nothing else in the file moves.** A write replaces exactly the bytes of the
    embedded specification and leaves every other byte alone (FR-STA-03), and the
    result is byte-for-byte what regenerating the document would produce, because
    the same deterministic serialiser writes both (NFR-GEN-01). A refusal writes
    nothing at all: it is raised before the file is opened for writing.

Concurrency is settled by LD-03 rather than by a lock: one writer per run, plus
a re-read before writing that refuses if the file changed underneath us, which
is what catches the stray hand edit. Schema drift is settled by LD-08: the
writer refuses any difference at all, because rewriting a document it only
partly understands can corrupt the single artefact holding recorded progress.

    python3 -m z2s.status set M1-P1-T1 in-progress
    python3 -m z2s.status ran unit -- python3 -m unittest discover -s tests
    python3 -m z2s.status tick M1-P1-T1
    python3 -m z2s.status report
    python3 -m z2s.status review
    python3 -m z2s.status commit M1-P1-T1 z2s/status.py tests/test_status.py

Traces: FR-STA-01, FR-STA-02, FR-STA-03, FR-STA-04, FR-STA-06, FR-STA-07,
FR-STA-08, FR-PLN-06, FR-EXE-11, FR-GEN-03, NFR-DAT-04, NFR-DAT-05, NFR-EXE-10,
NFR-EXE-11, NFR-GEN-01, NFR-OPS-04, ADR-05, ADR-11, US-STA-01, US-STA-02,
US-STA-03.
"""

import collections
import glob
import json
import os
import subprocess
import sys

from z2s import document, paths, safety, schema, validate, writer

#: Where a run's evidence lives. Under the ledger directory deliberately: it is
#: transient run state, excluded from version control (NFR-OPS-04), because it
#: describes one run rather than the project.
#:
#: ponytail: one entry per layer, latest wins, and a new run is expected to
#: clear it. Two runs sharing a working copy would share evidence; the day that
#: matters, key the file by run identifier rather than adding a lock.
RECORD = paths.LEDGER_DIR + "/verification.json"

USAGE = """usage:
  python3 -m z2s.status set <unit> <status> [--root <path>]
  python3 -m z2s.status tick <unit> [<criterion> ...] [--root <path>]
  python3 -m z2s.status ran <layer> -- <command> ... [--root <path>]
  python3 -m z2s.status clear [--root <path>]
  python3 -m z2s.status report [--root <path>]
  python3 -m z2s.status review [--root <path>]
  python3 -m z2s.status commit <unit> [<path> ...] [--root <path>]"""


class Refused(Exception):
    """A named refusal. Nothing was written, and the message says why."""


# ------------------------------------------------------------------- the model

def known(state):
    """Whether this is one of the documented statuses (FR-STA-01)."""
    return state in {one["id"] for one in schema.ENUMS["statuses"]}


def may_become(current, wanted):
    """Whether a unit carrying `current` may be moved to `wanted` (M10-05).

    Re-recording the status a unit already carries is always allowed: it is not
    a transition, and refusing it would make an interrupted run unable to say
    again what it already said.
    """
    if not known(current) or not known(wanted):
        return False
    return current == wanted or wanted in schema.TRANSITIONS[current]


def transition(current, wanted):
    """`wanted`, or a refusal naming the move that was turned down."""
    if not known(wanted):
        raise Refused("%s is not a status; the documented set is %s"
                      % (wanted, ", ".join(one["id"]
                                           for one in schema.ENUMS["statuses"])))
    if not known(current):
        raise Refused("%s currently carries %s, which is not a status" % (current,))
    if not may_become(current, wanted):
        raise Refused("%s cannot become %s; from %s a unit may become %s"
                      % (current, wanted, current,
                         ", ".join(schema.TRANSITIONS[current])))
    return wanted


# ---------------------------------------------------------------- the evidence

def _record_path(root):
    return paths.resolve(root, RECORD)


def evidence(root):
    """Everything this run has actually proved, by layer."""
    path = _record_path(root)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            held = json.loads(handle.read())
    except (OSError, ValueError) as error:
        raise Refused("the verification record could not be read: %s" % error)
    return held if isinstance(held, dict) else {}


def record(root, layer, command, code):
    """Record that `command` ran for `layer` and what came of it.

    The exit status is the result. Nobody is asked whether the check passed,
    because the answer to that question is what the check itself returned.
    """
    layers = [one["id"] for one in schema.ENUMS["testLayers"]]
    if layer not in layers:
        raise Refused("%s is not a verification layer; the documented set is %s"
                      % (layer, ", ".join(layers)))
    held = evidence(root)
    held[layer] = {"command": command, "code": int(code), "passed": int(code) == 0}
    # The ledger directory only. Recording a test result is not the moment to
    # lay out a whole project: a mistyped root would leave a method's worth of
    # empty directories somewhere nobody asked for one.
    directory = os.path.dirname(_record_path(root))
    if not os.path.isdir(directory):
        os.makedirs(directory)
    writer.write(_record_path(root),
                 json.dumps(held, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    return held[layer]


def clear(root):
    """Forget this run's evidence. A new run starts having proved nothing."""
    path = _record_path(root)
    if os.path.exists(path):
        os.remove(path)


def ran(root, layer, command):
    """Run a check and record what happened. Returns its exit status.

    The command is a list of words, not a shell line, so nothing here expands a
    variable or chains a second command behind a semicolon.
    """
    written = " ".join(command)
    broken = safety.refusal(written, area=root)
    if broken:
        raise Refused("refused to run this check: %s" % " ".join(broken))
    finished = subprocess.run(list(command), cwd=os.path.abspath(root), check=False)
    record(root, layer, written, finished.returncode)
    return finished.returncode


def unproved(root, layers):
    """The named layers this run cannot show a passing result for."""
    held = evidence(root)
    return [layer for layer in layers
            if not (held.get(layer) or {}).get("passed")]


# ---------------------------------------------------------------- the document

def read(path):
    """A plan document as (text, specification). The text is what is on disk."""
    try:
        with open(path, encoding="utf-8") as handle:
            html = handle.read()
    except OSError as error:
        raise Refused("%s could not be read: %s" % (path, error))
    try:
        return html, validate.extract(html)
    except validate.ExtractionError as error:
        raise Refused("%s: %s" % (path, error))


def documents(root):
    """Every plan document in the project, in a stable order."""
    return sorted(glob.glob(paths.resolve(root, paths.PLAN_DIR, "*.html")))


def tasks(spec):
    """Every unit of work the document carries, in document order."""
    found = []
    for section in spec.get("sections") or ():
        if isinstance(section, dict) and section.get("type") == "requirements":
            for item in section.get("items") or ():
                if isinstance(item, dict) and schema.plan_level(item.get("id")) == "task":
                    found.append(item)
    return found


def find(spec, unit):
    """The unit of work with this identifier, or None."""
    for one in tasks(spec):
        if one.get("id") == unit:
            return one
    return None


def locate(root, unit):
    """(path, text, specification) for the document that defines `unit`."""
    for path in documents(root):
        html, spec = read(path)
        if find(spec, unit) is not None:
            return path, html, spec
    raise Refused("no plan document in %s defines %s"
                  % (paths.resolve(root, paths.PLAN_DIR), unit))


def _writable(spec, path):
    """LD-08: the writer refuses any schema difference, however small."""
    carried = spec.get("schemaVersion")
    if carried != schema.SCHEMA_VERSION:
        raise Refused("%s carries schema version %s and this tool writes %s; "
                      "regenerate it before recording progress in it"
                      % (path, carried, schema.SCHEMA_VERSION))


def apply(spec, unit, wanted):
    """Move a unit to `wanted` in this specification. Returns the unit."""
    entry = find(spec, unit)
    if entry is None:
        raise Refused("%s is not a unit of work in this document" % unit)
    entry["status"] = transition(entry.get("status") or schema.NOT_STARTED, wanted)
    return entry


def mark(spec, unit, names=None):
    """Tick criteria on a unit. Named ones, or every machine-checkable one.

    Ticking by kind never reaches a human-review criterion: a machine saying a
    human signed something off is the one tick that would make every other tick
    worthless (FR-PLN-06).
    """
    entry = find(spec, unit)
    if entry is None:
        raise Refused("%s is not a unit of work in this document" % unit)
    criteria = list(entry.get("criteria") or ())
    if names is None:
        chosen = [one for one in criteria if one.get("kind") == schema.AUTOMATED]
    else:
        held = {one.get("id"): one for one in criteria}
        unknown = [name for name in names if name not in held]
        if unknown:
            raise Refused("%s has no criterion %s"
                          % (unit, ", ".join(sorted(unknown))))
        chosen = [held[name] for name in names]
    for one in chosen:
        one["done"] = True
    return chosen


def rewrite(path, html, spec):
    """Write the specification back into the document it came from.

    Only the bytes between the embedding element's tags change. The replacement
    comes from the same serialiser the generators use, so the file this leaves
    behind is exactly the file regeneration would produce.
    """
    match = validate.BLOCK.search(html)
    if match is None:
        raise Refused("%s has no embedded specification to write to" % path)
    # LD-03: one writer per run, and this is what catches the hand edit that
    # arrived while we were deciding. Refusing costs a re-run; overwriting costs
    # somebody's work with no trace that it was ever there.
    with open(path, encoding="utf-8") as handle:
        if handle.read() != html:
            raise Refused("%s changed while this change was being prepared; "
                          "nothing was written" % path)
    # The whitespace around the specification is the embedding element's, not
    # the specification's, so it is carried over rather than re-invented: a
    # written document has to be byte-identical to a regenerated one.
    held = match.group(1)
    opening = held[:len(held) - len(held.lstrip())]
    closing = held[len(held.rstrip()):]
    writer.write(path, html[:match.start(1)] + opening + document.serialise(spec)
                 + closing + html[match.end(1):])
    return path


# ---------------------------------------------------------------- the commands

def set_status(root, unit, wanted):
    """Record a unit's status, if it is a move that may be made and is proved."""
    if not known(wanted):
        raise Refused("%s is not a status; the documented set is %s"
                      % (wanted, ", ".join(one["id"]
                                           for one in schema.ENUMS["statuses"])))
    path, html, spec = locate(root, unit)
    _writable(spec, path)
    entry = find(spec, unit)

    if wanted == schema.PASSING:
        missing = unproved(root, list(entry.get("testLayers") or ()))
        if missing:
            raise Refused(
                "%s names %s and this run has no passing result for %s; run the "
                "check and record it before claiming the status"
                % (unit, ", ".join(entry.get("testLayers") or ()),
                   ", ".join(missing)))

    apply(spec, unit, wanted)
    rewrite(path, html, spec)
    return path


def tick(root, unit, names=None):
    """Tick criteria on a unit and write the document back."""
    path, html, spec = locate(root, unit)
    _writable(spec, path)
    marked = mark(spec, unit, names)
    rewrite(path, html, spec)
    return [one.get("id") for one in marked]


def _counts(entries):
    """How many units sit in each status. Every status, including the zeroes."""
    held = collections.OrderedDict(
        (one["id"], 0) for one in schema.ENUMS["statuses"])
    for one in entries:
        state = one.get("status") or schema.NOT_STARTED
        if state in held:
            held[state] += 1
    return held


def _outstanding(entries):
    """Human-review criteria still open across these units (FR-PLN-06)."""
    return [one for entry in entries for one in entry.get("criteria") or ()
            if one.get("kind") == schema.HUMAN_REVIEW and not one.get("done")]


def _state(entries):
    """What a group of units adds up to.

    A human-review criterion never holds its own task back — the task's machine
    gates are what the task is judged on — but it does hold back the thing that
    contains it, which is the rule FR-PLN-06 states.
    """
    if not entries:
        return schema.NOT_STARTED
    states = [one.get("status") or schema.NOT_STARTED for one in entries]
    if schema.BLOCKED in states:
        return schema.BLOCKED
    if schema.FAILING in states:
        return schema.FAILING
    if all(state in (schema.PASSING, schema.NEEDS_REVIEW) for state in states):
        if all(state == schema.PASSING for state in states) \
                and not _outstanding(entries):
            return schema.PASSING
        return schema.NEEDS_REVIEW
    if all(state == schema.NOT_STARTED for state in states):
        return schema.NOT_STARTED
    return schema.IN_PROGRESS


def rollup(spec):
    """Progress at every level, computed here and stored nowhere (NFR-DAT-05)."""
    entries = tasks(spec)
    grouped = collections.OrderedDict()
    for one in entries:
        grouped.setdefault(one.get("area") or "", []).append(one)
    return {
        "id": milestone_of(spec, entries),
        "tasks": len(entries),
        "counts": _counts(entries),
        "state": _state(entries),
        "review": len(_outstanding(entries)),
        "phases": collections.OrderedDict(
            (key, {"tasks": len(items), "counts": _counts(items),
                   "state": _state(items), "review": len(_outstanding(items))})
            for key, items in grouped.items()),
    }


def milestone_of(spec, entries=None):
    """Which milestone this document is. Its own envelope says so."""
    stated = (spec.get("document") or {}).get("milestone")
    if stated:
        return stated
    entries = tasks(spec) if entries is None else entries
    return entries[0]["id"].split("-", 1)[0] if entries else ""


def review(spec):
    """Every outstanding human-review criterion, each naming its unit."""
    found = []
    for entry in tasks(spec):
        for one in entry.get("criteria") or ():
            if one.get("kind") == schema.HUMAN_REVIEW and not one.get("done"):
                found.append({"id": one.get("id"), "unit": entry.get("id"),
                              "title": entry.get("title"), "text": one.get("text")})
    return found


def label(name, value):
    """The word a reader sees for an enumerated id. Public because the
    orchestrator reports a status it was not expecting to find, and a raw id in
    a sentence meant for a person is the thing this method keeps fixing."""
    for one in schema.ENUMS[name]:
        if one["id"] == value:
            return one["label"]
    return value


def _line(identifier, figures):
    stated = ["%d %s" % (count, label("statuses", state).lower())
              for state, count in figures["counts"].items() if count]
    return "%-12s %-13s %d tasks · %s" % (
        identifier, label("statuses", figures["state"]).lower(),
        figures["tasks"], " · ".join(stated) or "nothing recorded")


def format_report(root):
    """Progress per phase and per milestone, without opening a browser."""
    lines = []
    for path in documents(root):
        _, spec = read(path)
        if not tasks(spec):
            continue
        figures = rollup(spec)
        lines.append(_line(figures["id"], figures))
        for key, phase in figures["phases"].items():
            lines.append("  " + _line(key, phase))
        if figures["review"]:
            lines.append("  %d human-review criteri%s outstanding"
                         % (figures["review"],
                            "on" if figures["review"] == 1 else "a"))
    return "\n".join(lines) if lines else "no plan documents with units of work"


def format_review(root):
    """The whole plan's outstanding human review, in one list (FR-STA-08)."""
    lines = []
    for path in documents(root):
        _, spec = read(path)
        for one in review(spec):
            lines.append("%-16s %-14s %s" % (one["id"], one["unit"], one["text"]))
    if not lines:
        return "nothing is waiting on human review"
    lines.append("%d outstanding" % len(lines))
    return "\n".join(lines)


def _within(root, relative):
    """A path inside the working area, or a refusal. Nothing else is ours."""
    base = os.path.abspath(root)
    full = os.path.abspath(os.path.join(base, relative))
    if full != base and not full.startswith(base.rstrip(os.sep) + os.sep):
        raise Refused("%s is outside %s; this run owns its own area and nothing "
                      "else" % (relative, base))
    return os.path.relpath(full, base)


def commit(root, unit, files=()):
    """One commit holding a unit's work and its status change (NFR-EXE-11).

    Both together, because a status recorded in a separate commit is a status
    that can be true of a tree nobody ever had. Publishing the result to a
    remote is not done here and never has been: that is the operator's call.
    """
    path, _, spec = locate(root, unit)
    entry = find(spec, unit)
    staged = [_within(root, one) for one in files]
    staged.append(_within(root, path))

    subject = "%s: %s" % (unit, entry.get("title") or "unit of work")
    body = "Status: %s." % label("statuses",
                                  entry.get("status") or schema.NOT_STARTED)
    for command in (["git", "add", "--"] + staged,
                    ["git", "commit", "-m", subject, "-m", body]):
        broken = safety.refusal(" ".join(command), area=root)
        if broken:
            raise Refused("refused: %s" % " ".join(broken))
        finished = subprocess.run(["git", "-C", os.path.abspath(root)] + command[1:],
                                  capture_output=True, text=True, check=False)
        if finished.returncode != 0:
            raise Refused("%s failed: %s" % (" ".join(command),
                                             finished.stderr.strip()))
    return subject


# ----------------------------------------------------------------- the command

def _root(argv):
    """The project directory, and the arguments with that option removed."""
    rest, root = [], "."
    skip = False
    for index, word in enumerate(argv):
        if skip:
            skip = False
            continue
        if word == "--root":
            if index + 1 >= len(argv):
                raise Refused("--root needs a directory")
            root, skip = argv[index + 1], True
        else:
            rest.append(word)
    return root, rest


def main(argv, out=sys.stdout):
    """The command. Its exit status is the answer (FR-VAL-05)."""
    if not argv:
        out.write(USAGE + "\n")
        return 2
    try:
        root, rest = _root(list(argv))
        return _dispatch(rest, root, out)
    except Refused as refusal:
        out.write("refused: %s\n" % refusal)
        return 1


def _dispatch(rest, root, out):
    name, arguments = rest[0], rest[1:]

    if name == "set":
        if len(arguments) != 2:
            out.write(USAGE + "\n")
            return 2
        written = set_status(root, arguments[0], arguments[1])
        out.write("%s is now %s in %s\n"
                  % (arguments[0], arguments[1], os.path.basename(written)))
        return 0

    if name == "tick":
        if not arguments:
            out.write(USAGE + "\n")
            return 2
        marked = tick(root, arguments[0], arguments[1:] or None)
        out.write("ticked %s\n" % (", ".join(marked) or "nothing"))
        return 0

    if name == "ran":
        if len(arguments) < 2:
            out.write(USAGE + "\n")
            return 2
        command = arguments[1:]
        if command and command[0] == "--":
            command = command[1:]
        code = ran(root, arguments[0], command)
        out.write("%s: %s (exit %d)\n"
                  % (arguments[0], "passed" if code == 0 else "failed", code))
        return 0

    if name == "clear":
        clear(root)
        out.write("this run has proved nothing\n")
        return 0

    if name == "report":
        out.write(format_report(root) + "\n")
        return 0

    if name == "review":
        out.write(format_review(root) + "\n")
        return 0

    if name == "commit":
        if not arguments:
            out.write(USAGE + "\n")
            return 2
        out.write(commit(root, arguments[0], arguments[1:]) + "\n")
        return 0

    out.write(USAGE + "\n")
    return 2


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
