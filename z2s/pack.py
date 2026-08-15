# -*- coding: utf-8 -*-
"""Packaging the chain as one installable plugin, with every skill pinned.

An install is reproducible when the same marketplace reference resolves to the
same skill set (NFR-SKL-03). A version number alone does not make that true —
it is a label somebody types, and a label can be wrong. What makes it true is
recording what each skill actually contained, so that two builds from the same
source produce byte-identical output and a changed skill is visible rather than
silently shipped under an unchanged version.

So the lock is a content hash per skill, generated from the chain definition
rather than maintained by hand: adding a skill to `steps.py` and forgetting the
manifest is not a state this can reach.

The same pass lints the trigger policy, because a definition is the only place a
trigger rule is a contract rather than a request (NFR-SKL-01). Every chain skill
must be marked manual-only; the clarification skill alone must not be. Both
halves are checked — a lint that only catches the missing marking would pass a
build where every skill, interviewer included, had been quietly locked down.

    python3 -m z2s.pack [--check] [--root DIR]

`--check` builds the lock and compares it against the one on disk without
writing, which is what a continuous-integration run wants.

Traces: FR-SKL-01, FR-SKL-03, FR-SKL-04, FR-SKL-08, NFR-SKL-01, NFR-SKL-03,
ADR-18, US-SKL-01, US-SKL-06.
"""

import hashlib
import json
import os
import sys

from z2s import schema, steps, writer

#: Where the plugin's parts live, relative to the plugin root. `skills/` and the
#: manifest directory are Claude Code's layout, not this method's choice.
SKILLS_DIR = "skills"
MANIFEST = ".claude-plugin/plugin.json"
MARKETPLACE = ".claude-plugin/marketplace.json"
LOCK_FILE = "skills.lock.json"
DEFINITION = "SKILL.md"

#: The frontmatter field the agent runtime reads to decide whether a skill may
#: fire on its own. Named here because it is the whole of NFR-SKL-01: a policy
#: stated anywhere else is documentation, and this is the contract.
MANUAL_ONLY = "disable-model-invocation"

FENCE = "---"


class Broken(Exception):
    """Raised when the plugin cannot be built as declared."""


def skill_path(root, one):
    return os.path.join(os.path.abspath(root), SKILLS_DIR, one.name, DEFINITION)


def frontmatter(text):
    """The key/value block a skill definition opens with, as a dictionary.

    A deliberately small parser rather than a dependency (NFR-ARC-03). It reads
    exactly what these definitions contain — one `key: value` per line between
    two fences — and anything richer is not something a skill definition here is
    allowed to need.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != FENCE:
        raise Broken("no frontmatter: a definition must open with %s" % FENCE)
    found = {}
    for line in lines[1:]:
        if line.strip() == FENCE:
            return found
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        found[key.strip()] = value.strip()
    raise Broken("the frontmatter is never closed with %s" % FENCE)


def _manual(header):
    """Whether a definition marks itself manual-only."""
    return header.get(MANUAL_ONLY, "").lower() == "true"


def read_skill(root, one):
    """(text, frontmatter) for one skill, or a refusal naming what is wrong."""
    path = skill_path(root, one)
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        raise Broken("%s ships no definition; expected one at %s"
                     % (one.name, path))
    try:
        header = frontmatter(text)
    except Broken as error:
        raise Broken("%s: %s" % (one.name, error))
    if header.get("name") != one.name:
        raise Broken("%s declares itself %r; the chain calls it %r, and the "
                     "name an operator types comes from the directory"
                     % (one.name, header.get("name"), one.name))
    if schema.is_empty(header.get("description")):
        raise Broken("%s states no description; the runtime has nothing to "
                     "list it by" % one.name)
    return text, header


def triggers(root):
    """Every trigger-policy fault in the set (FR-SKL-03, FR-SKL-04).

    Both directions, in one pass. Reported as a list rather than raised one at a
    time because an operator fixing definitions wants all of them, not the first
    one and then another run.
    """
    faults = []
    for one in steps.CHAIN:
        _, header = read_skill(root, one)
        marked = _manual(header)
        if one.name == steps.INTERVIEWER and marked:
            faults.append(
                "%s is marked %s. It is the one skill that must be able to fire "
                "on its own: a question that arrives too late has already been "
                "answered by a guess." % (one.name, MANUAL_ONLY))
        elif one.name != steps.INTERVIEWER and not marked:
            faults.append(
                "%s is not marked %s: true. Every chain skill runs only when it "
                "is asked for, and a rule stated outside the definition is a "
                "request rather than a contract." % (one.name, MANUAL_ONLY))
    return faults


def version(root):
    """The plugin's stated version, from its manifest."""
    path = os.path.join(os.path.abspath(root), MANIFEST)
    try:
        with open(path, encoding="utf-8") as handle:
            found = json.loads(handle.read())
    except (OSError, ValueError) as error:
        raise Broken("%s could not be read: %s" % (MANIFEST, error))
    stated = found.get("version")
    if schema.is_empty(stated):
        raise Broken("%s states no version; there would be nothing to pin to"
                     % MANIFEST)
    if found.get("name") != steps.PLUGIN:
        raise Broken("%s is named %r; the chain is namespaced under %r, and the "
                     "plugin's name is the prefix an operator types"
                     % (MANIFEST, found.get("name"), steps.PLUGIN))
    return stated


def build(root):
    """The lock, as text. Pure: same source in, same bytes out.

    No clock and no random source, like every other module here — which is what
    makes "two builds from the same source are identical" a property rather than
    a hope (M13-P3-T1-C1).
    """
    faults = triggers(root)
    if faults:
        raise Broken("\n".join(faults))

    skills = {}
    for one in steps.CHAIN:
        text, _ = read_skill(root, one)
        skills[one.name] = {
            "command": steps.command(one),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }

    reference = {"plugin": steps.PLUGIN, "version": version(root),
                 "skills": skills}
    return json.dumps(reference, indent=2, sort_keys=True) + "\n"


def lock_path(root):
    return os.path.join(os.path.abspath(root), LOCK_FILE)


def write(root):
    """Build the lock and store it. Returns the path written."""
    target = lock_path(root)
    writer.write(target, build(root))
    return target


def check(root):
    """What differs between the lock on disk and the one this source produces.

    Returns the sentences to report, empty when they agree. Nothing is written,
    which is what makes this safe to run in a gate.
    """
    wanted = build(root)
    try:
        with open(lock_path(root), encoding="utf-8") as handle:
            held = handle.read()
    except OSError:
        return ["%s is missing. Run python3 -m z2s.pack to write it."
                % LOCK_FILE]
    if held == wanted:
        return []
    return ["%s does not match the skills it locks. A skill changed and the "
            "lock did not, so the same reference would resolve to a different "
            "skill set. Run python3 -m z2s.pack." % LOCK_FILE]


def main(argv, out=sys.stdout):
    """The command. Its exit status is the answer (FR-VAL-05)."""
    argv = list(argv)
    root = "."
    if "--root" in argv:
        at = argv.index("--root")
        if at + 1 >= len(argv):
            out.write("--root needs a value\n")
            return 2
        root = argv[at + 1]
        del argv[at:at + 2]
    checking = "--check" in argv
    if checking:
        argv.remove("--check")
    if argv:
        out.write("usage: python3 -m z2s.pack [--check] [--root DIR]\n")
        return 2

    try:
        if checking:
            differs = check(root)
            for line in differs:
                out.write(line + "\n")
            if not differs:
                out.write("%s: %d skills, all pinned and unchanged\n"
                          % (LOCK_FILE, len(steps.CHAIN)))
            return 1 if differs else 0
        out.write("wrote %s: %d skills pinned\n"
                  % (write(root), len(steps.CHAIN)))
        return 0
    except Broken as error:
        out.write("%s\n" % error)
        return 1


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
