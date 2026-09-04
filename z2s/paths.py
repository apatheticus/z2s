# -*- coding: utf-8 -*-
"""The repository layout, declared once.

Every tool in the method and every test that checks the method reads its paths
from this module. A path spelled in two places is a path that will eventually
disagree with itself.

Traces: FR-GEN-01, NFR-OPS-01, NFR-OPS-04, ADR-11, US-STA-03.
"""

import glob
import os
import re

from z2s import writer

#: Everything the method owns lives under this one directory in a host project.
ROOT = ".zero"

SPECS_DIR = ROOT + "/specs"
PLAN_DIR = ROOT + "/plan"
PLAN_BUILD_DIR = PLAN_DIR + "/_build"
PLAN_DETAILS_DIR = PLAN_BUILD_DIR + "/details"
LEDGER_DIR = ROOT + "/state"

#: Where a project's features live, one directory each, numbered from 001. A
#: feature is a piece of work with its own specifications, plan and run state;
#: the project's Intent, Context, workers and design stay SHARED above it.
FEATURES_DIR = ROOT + "/features"

#: The directories that belong to a piece of work rather than to the project.
#: While a feature is open these resolve under it; everything else never moves.
SCOPED = (SPECS_DIR, PLAN_DIR, LEDGER_DIR)

#: What a feature directory is called: three digits, a dash, a slug. The
#: listing IS the derivation — no document is parsed to find the open feature,
#: and a directory not shaped like this is not a feature.
FEATURE_NAME = re.compile(r"^(\d{3})-([a-z0-9]+(?:-[a-z0-9]+)*)$")

#: Created by setup, in this order. Parents before children.
DIRECTORIES = (
    ROOT,
    SPECS_DIR,
    PLAN_DIR,
    PLAN_BUILD_DIR,
    PLAN_DETAILS_DIR,
    LEDGER_DIR,
)

#: A document type that was renamed, keyed by the slug it goes by now: the
#: filename it used to carry, and the slug it was recorded under. A project
#: written before the rename keeps its files AND its decision ledger, and both
#: are read through the old name wherever the new one is absent (NFR-OPS-07);
#: nothing is moved on disk and new writes go to the new name only.
#:
#: It lives here rather than beside either reader because two of them consult
#: it — the prerequisite check in `chain.require` and the decision ledger in
#: `gate.load` — and a rename spelled twice is a rename that will eventually
#: disagree with itself. That is not hypothetical: the ledger half was missed
#: when the map lived in `chain`, and a project written before the rename kept
#: every decision on disk while handing none of them to a worker.
#:
#: Only the first document has ever been renamed and nothing else gets a
#: fallback: an old project-level document must never satisfy a feature's need
#: for its own.
FORMERLY = {"intent": ("Vision.html", "vision")}

#: Where the ignore rules — and the reasoning behind them — live.
IGNORE_FILE = ROOT + "/.gitignore"

#: What a project's workers are, and how a unit is proved. Configuration rather
#: than run state, so it sits beside the documents and is committed with them.
WORKERS_FILE = ROOT + "/workers.json"

#: What the project's design system resolved to, and where every value came
#: from. Configuration for the same reason workers.json is: it carries operator
#: decisions — an override, a mapping they confirmed — that no re-reading of the
#: host project can reproduce. It sits beside the documents and is committed
#: with them, which is what makes an adopted theme reviewable rather than a
#: thing that happened.
DESIGN_FILE = ROOT + "/design.json"

#: Retrospectives sit beside the milestone documents they belong to.
LESSONS_TEMPLATE = PLAN_DIR + "/M%s-lessons-learned.md"

IGNORE_BODY = """\
# ---------------------------------------------------------------------------
# Everything the Zero-to-Ship method owns lives under this directory.
#
# state/ is transient run state: the ledger for a run in progress. It is
# rewritten constantly, it means nothing to anyone who was not present for that
# run, and it is excluded from version control here (NFR-OPS-04).
#
# specs/ and plan/ are GENERATED, and they are committed anyway. That is a
# deliberate exception to the usual rule about generated files (ADR-11): plan
# documents carry live status, and the history of that status is the record of
# how the project actually went. Committed, it is diffable, reviewable and
# attributable. Regenerated on demand, it is gone.
#
# Do not hand-edit a generated document under specs/ or plan/. Edit the source
# data and regenerate. A hand edit is silently overwritten on the next run, and
# until then it splits one fact across two artefacts, which is the exact defect
# this method exists to prevent.
# ---------------------------------------------------------------------------

state/
"""


def shared(root, *parts):
    """Absolute path to a documented location in the project's shared layer.

    The plain join: what `resolve` was before features existed, and what it
    still is for everything the project holds once — the Context, the workers,
    the design record, the ignore rules.
    """
    return os.path.join(os.path.abspath(root), *parts)


def feature_dir(number, slug):
    """The directory a feature lives in, relative to the project root."""
    return "%s/%03d-%s" % (FEATURES_DIR, number, slug)


def features(root):
    """Every feature the project has opened, as (number, slug), lowest first."""
    try:
        names = os.listdir(shared(root, FEATURES_DIR))
    except OSError:
        return []
    found = []
    for name in names:
        match = FEATURE_NAME.match(name)
        if match and os.path.isdir(shared(root, FEATURES_DIR, name)):
            found.append((int(match.group(1)), match.group(2)))
    return sorted(found)


def feature(root):
    """The current feature's directory, relative to the root, or None.

    The highest-numbered one. Whether it is still open or has been closed is
    a fact its own Intent records, and this module reads no document: the
    feature module answers that question.
    """
    found = features(root)
    return feature_dir(*found[-1]) if found else None


def resolve(root, *parts):
    """Absolute path to a documented location inside a project.

    A location that belongs to a piece of work — a specification, the plan,
    run state — follows the current feature when there is one (FR-GEN-12). A
    project with no features resolves every path exactly as it always did.
    """
    current = feature(root) if parts else None
    if current:
        head = parts[0]
        for scoped in SCOPED:
            if head == scoped or head.startswith(scoped + "/"):
                parts = (current + head[len(ROOT):],) + tuple(parts[1:])
                break
    return shared(root, *parts)


def toward(root, start, *parts, **options):
    """A relative href from the directory `start` names to the location `parts`
    names — in the shared layer when `shared=True`, else wherever `resolve`
    puts it. What a document embeds so a link survives being opened from a
    feature's plan or the project's own."""
    target = (shared if options.get("shared") else resolve)(root, *parts)
    return os.path.relpath(target, resolve(root, start)).replace(os.sep, "/")


def specs(root):
    """Every specification document in force, in a stable order.

    The current feature's own, plus every shared one no feature document
    stands in for: a feature that has written its Intent reads its Intent,
    and the Context — which no feature writes — is always the project's.
    """
    found = glob.glob(resolve(root, SPECS_DIR, "*.html"))
    if feature(root):
        held = {os.path.basename(one) for one in found}
        found += [one for one in glob.glob(shared(root, SPECS_DIR, "*.html"))
                  if os.path.basename(one) not in held]
    return sorted(found)


def documents(root):
    """Every document the method has written in a project, in a stable order.

    Specifications and plan alike, which is what a gate over "this project's
    documents" means. `status.documents` answers a narrower question — the plan
    documents a unit's status could live in — and is deliberately left alone.
    """
    return sorted(specs(root) + glob.glob(resolve(root, PLAN_DIR, "*.html")))


def ensure_layout(root):
    """Create the documented layout and ignore rules under `root`.

    Re-runnable: an existing directory is left alone, and an existing ignore
    file is never overwritten, because it may carry a project's own additions.
    Returns what was created and what was already present, so a caller can
    report honestly instead of claiming work it did not do (FR-GEN-03).
    """
    created, existed = [], []

    for relative in DIRECTORIES:
        target = resolve(root, relative)
        if os.path.isdir(target):
            existed.append(relative)
        else:
            os.makedirs(target)
            created.append(relative)

    ignore = resolve(root, IGNORE_FILE)
    if os.path.exists(ignore):
        existed.append(IGNORE_FILE)
    else:
        writer.write(ignore, IGNORE_BODY)
        created.append(IGNORE_FILE)

    return {"created": created, "existed": existed}
