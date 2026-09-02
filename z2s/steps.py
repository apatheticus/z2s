# -*- coding: utf-8 -*-
"""The chain, declared once: what the steps are, and what each one needs.

Four separate places have to agree about the order of the method — the
prerequisite refusal, the resume skill, the setup probe, and the list of skills
the plugin ships. The M13 plan asks each of them, in its own refactor note, to
"derive it from the chain definition rather than repeating it", and this module
is that definition. Repeated four times it would be four things to keep in step;
declared here it is one.

Two facts about a step are deliberately kept apart:

  * `needs` is what the generator ACTUALLY refuses without, which is what a
    refusal has to name if it is to be actionable (FR-SKL-02, NFR-SKL-02).
  * `after` is the single upstream document the published skill table names, and
    it is what decides reading order — where the chain resumes from, and which
    step comes next (FR-SKL-05).

They differ on purpose. The published table says the functional specification
follows the product requirements, because that is the step a reader takes next.
The generator also needs the context document, because it speaks its glossary.
Reporting only the first would make a refusal wrong; ordering by the second
would make the chain a graph nobody can read as a sequence.

Traces: FR-SKL-01, FR-SKL-02, FR-SKL-05, FR-SKL-09, FR-SKL-08, NFR-SKL-02,
NFR-SKL-04, ADR-18, US-SKL-01, US-SKL-03, US-SKL-07.
"""

import collections
import os
import sys

from z2s import (chain, context, design, fsd, paths, plan, prd, sdd, stories, validate,
                 intent)

#: The plugin every skill ships in, and therefore the prefix an operator types.
#: Claude Code namespaces a plugin's skills under the plugin's own name, so this
#: single word is what makes the invocation `/zero:intent` rather than something
#: longer — see M13-08 in the ledger for why the published `/zero-vision` could
#: not be built as written.
PLUGIN = "zero"


def command(one):
    """What an operator types to invoke a step (FR-SKL-01)."""
    return "/%s:%s" % (PLUGIN, one.name)


#: One step of the method.
#:
#: `module` is the generator this step drives, or None for a step that operates
#: on the set rather than adding to it. `needs` is every document the generator
#: refuses without. `after` is the one upstream document the published skill
#: table names — the reading order, and None for a step that starts the chain
#: or stands outside it.
Step = collections.namedtuple("Step", "name module needs after summary")


def _step(name, module=None, needs=(), after=None, summary=""):
    return Step(name, module, tuple(needs), after, summary)


#: The seven steps that produce a document, in reading order. This ordering is
#: the chain: resume walks it forwards and stops at the first gap.
DOCUMENTS = (
    _step("intent", intent, (), None,
          "Derives the intent from any mix of narrative, documents and web "
          "addresses; maintains the source register."),
    _step("context", context, ("intent",), "intent",
          "Establishes the ubiquitous language: glossary, bounded contexts, "
          "context map."),
    _step("prd", prd, ("context", "intent"), "context",
          "Generates the product requirements."),
    _step("fsd", fsd, ("prd", "context"), "prd",
          "Generates the functional specification."),
    _step("stories", stories, ("fsd", "context"), "fsd",
          "Generates user stories and use cases."),
    _step("sdd", sdd, ("fsd", "context"), "fsd",
          "Generates the technical design."),
    _step("plan", plan, ("fsd", "sdd", "stories", "context"), "sdd",
          "Derives the plan and proves coverage."),
)

#: The steps that operate on the set rather than extending it. They
#: produce no document, so nothing here has an `after`: none of them has a place
#: in the reading order, and resume must never propose one as the next thing to
#: write.
OPERATIONS = (
    _step("init", summary="Sets the project up: the .zero/ layout, ignore "
                          "rules, design-token detection, the verification "
                          "gauntlet. Idempotent; every chain skill runs it "
                          "automatically when setup is missing."),
    _step("design", design,
          summary="Reads the project's design system — stylesheets, token "
                  "documents, a brand book, a DESIGN.md — and records what the "
                  "documents will be styled with, naming every value's source. "
                  "Asks before adopting anything a document states only in "
                  "prose."),
    _step("build", summary="Works through the plan's build prompts, wave by "
                           "wave."),
    _step("prompt", summary="Prints the instructions for one unit of the plan — "
                            "a task, a phase, a milestone, or the whole build — "
                            "so it can be handed to whoever is doing the work."),
    _step("action", summary="Resumes from wherever the set stands; starts from "
                            "the beginning if no Intent."),
    _step("update", summary="Folds additions and changes in, forward-only — "
                            "never deletes or overwrites."),
    _step("feature", summary="Opens the next feature, or closes the open one "
                             "after an audit. One feature is open at a time; "
                             "its documents, plan and run state live under "
                             ".zero/features/."),
    _step("ship", summary="Commits and pushes the working branch; asks before "
                          "opening a pull request."),
    _step("questions", summary="The shared clarification interview every other "
                               "skill routes questions through. The only skill "
                               "that may trigger automatically."),
)

#: Setting a project up. Two steps, not one, and deliberately so: `init` is
#: idempotent and every chain skill runs it blindly because of that ("a second
#: run changes no byte"), while `design` REWRITES the design record and so
#: cannot live inside a promise of idempotence.
SETUP = OPERATIONS[:2]

#: Every skill the plugin ships. The order is the published table's order:
#: setup, then the documents in reading order, then the operating skills.
CHAIN = SETUP + DOCUMENTS + OPERATIONS[2:]

#: The one skill exempt from manual-only triggering (FR-SKL-03, FR-SKL-04). It
#: is named here rather than in each definition so the lint has one thing to
#: check against, and widening it means editing this line where a reviewer sees
#: it — not adding a quiet second exception in a fourteenth file.
INTERVIEWER = "questions"

BY_NAME = collections.OrderedDict((one.name, one) for one in CHAIN)
BY_SLUG = collections.OrderedDict(
    (one.module.SLUG, one) for one in DOCUMENTS)


class UnknownStep(Exception):
    """Raised when something asks for a step the chain does not define."""


def step(name):
    """The step a skill name or a document slug refers to.

    Both spellings are accepted because both are in daily use: an operator says
    `/zero:fsd` and the toolchain says `fsd`, and making a caller convert
    between them is how the two drift apart.
    """
    if name in BY_NAME:
        return BY_NAME[name]
    if name in BY_SLUG:
        return BY_SLUG[name]
    raise UnknownStep(
        "%r is not a step of the chain. The chain is: %s."
        % (name, ", ".join(one.name for one in CHAIN)))


def document_path(root, one):
    """Where a step's document lives, or None for a step that writes none.

    The plan is the exception the layout already declares: it is one document
    split across files, so its index sits in the plan directory rather than
    beside the specifications.
    """
    if one not in DOCUMENTS:
        # Keyed off membership rather than off carrying a module. `design`
        # carries one — it writes a record and rides the same interview driver
        # every generator uses — and it writes no document at all.
        return None
    if one.module is plan:
        return paths.resolve(root, paths.PLAN_DIR, plan.INDEX_FILE)
    if one.module is context:
        # The one document a feature never writes: it is the project's.
        return paths.shared(root, paths.SPECS_DIR, one.module.FILENAME)
    return paths.resolve(root, paths.SPECS_DIR, one.module.FILENAME)


def completed(root, one):
    """Whether this step's document exists and carries a readable specification.

    Existence alone is not completion: a half-written file, or one whose
    embedding was damaged, is exactly the state an operator most needs told
    apart from a finished document. Read-only throughout (NFR-SKL-02).
    """
    target = document_path(root, one)
    if target is None:
        return False
    if one.module is not plan:
        # The same read every generator makes of the document above it, so a
        # document that satisfies a generator is one resume calls written —
        # including an old name the chain still reads (`chain.FORMERLY`).
        try:
            chain.require(root, one.module.FILENAME, one.module.SLUG, "resume",
                          shared=one.module is context)
        except chain.MissingPrerequisite:
            return False
        return True
    if not os.path.exists(target):
        return False
    try:
        with open(target, encoding="utf-8") as handle:
            found = validate.extract(handle.read())
    except (OSError, validate.ExtractionError):
        return False
    block = found.get("document") if isinstance(found, dict) else None
    return isinstance(block, dict) and block.get("slug") == one.module.SLUG


def missing(root, one):
    """Which of a step's prerequisites are absent, in the chain's own order.

    The order matters to the operator: the first name in the list is the one to
    generate next, because every later one is downstream of it.
    """
    return tuple(need for need in
                 sorted(one.needs, key=lambda slug: list(BY_SLUG).index(slug))
                 if not completed(root, BY_SLUG[need]))


def refusal(root, one):
    """The sentences a skill refuses with, or None when it may proceed.

    Named rather than counted (FR-SKL-02): "prerequisites not met" tells an
    operator nothing about what to do next, and the whole point of refusing
    early is that the next action is obvious.

    The command it names is the earliest gap in the WHOLE chain, not this step's
    own nearest prerequisite. The plan needs the functional specification, which
    needs the product requirements, which needs the context: naming the nearest
    one sends the operator to a step that will refuse in turn, one document per
    round trip. So the instruction comes from `following` — the same probe the
    resume skill reads, which is what keeps the two from ever disagreeing about
    where the chain actually stands.
    """
    absent = missing(root, one)
    if not absent:
        return None
    names = [BY_SLUG[slug].module.FILENAME for slug in absent]
    return ("%s needs %s, and %s missing from %s. Run %s first. Nothing has "
            "been written and nothing has been changed."
            % (command(one),
               " and ".join(names),
               "it is" if len(names) == 1 else "they are",
               paths.resolve(root, paths.SPECS_DIR),
               command(following(root) or BY_SLUG[absent[0]])))


# ------------------------------------------------------------------- position

#: What a set with no completed intent reports as. Named because three callers
#: compare against it and a bare empty string in three places is a fourth
#: spelling waiting to happen.
NOTHING = None


def position(root):
    """The furthest step the document set has completed, or None for an empty set.

    Furthest, not "last that exists": the walk stops at the first gap, so a
    stray downstream document left over from an abandoned run does not persuade
    resume that the chain got further than it did.
    """
    furthest = NOTHING
    for one in DOCUMENTS:
        if not completed(root, one):
            break
        furthest = one
    return furthest


def following(root):
    """The step to run next — the first with no completed document.

    Returns the intent step for an empty set, which is FR-SKL-05's "starting
    from the beginning when no completed Intent exists", and None when the whole
    chain is written and there is nothing left to generate.
    """
    at = position(root)
    if at is NOTHING:
        return DOCUMENTS[0]
    index = DOCUMENTS.index(at) + 1
    return DOCUMENTS[index] if index < len(DOCUMENTS) else None


def format_position(root):
    """Where the set stands and what comes next, for the resume skill.

    Both facts, always, and in that order: an operator returning to a project
    after a gap needs to know what is already written before being told what to
    do, or the instruction has nothing to stand on (US-SKL-03).
    """
    at, next_one = position(root), following(root)
    lines = []
    for one in DOCUMENTS:
        lines.append("  %-9s %s" % (one.name,
                                    "written" if completed(root, one) else "—"))
    if at is NOTHING:
        lines.insert(0, "the set is empty; no intent has been completed")
    else:
        lines.insert(0, "the chain reaches %s" % at.name)
    if next_one is None:
        lines.append("")
        lines.append("every document is written. Nothing left to generate; "
                     "%s works through the plan." % command(BY_NAME["build"]))
    else:
        lines.append("")
        lines.append("next: %s" % command(next_one))
    return "\n".join(lines)


def main(argv, out=sys.stdout):
    """Report where the document set stands. Read-only (NFR-SKL-02)."""
    argv = list(argv)
    root = "."
    if "--root" in argv:
        at = argv.index("--root")
        if at + 1 >= len(argv):
            out.write("--root needs a value\n")
            return 2
        root = argv[at + 1]
        del argv[at:at + 2]
    if argv:
        out.write("usage: python3 -m z2s.steps [--root DIR]\n")
        return 2
    out.write(format_position(root) + "\n")
    return 0


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
