# -*- coding: utf-8 -*-
"""The repository layout, declared once.

Every tool in the method and every test that checks the method reads its paths
from this module. A path spelled in two places is a path that will eventually
disagree with itself.

Traces: FR-GEN-01, NFR-OPS-01, NFR-OPS-04, ADR-11, US-STA-03.
"""

import glob
import os

from z2s import writer

#: Everything the method owns lives under this one directory in a host project.
ROOT = ".zero"

SPECS_DIR = ROOT + "/specs"
PLAN_DIR = ROOT + "/plan"
PLAN_BUILD_DIR = PLAN_DIR + "/_build"
PLAN_DETAILS_DIR = PLAN_BUILD_DIR + "/details"
LEDGER_DIR = ROOT + "/state"

#: Created by setup, in this order. Parents before children.
DIRECTORIES = (
    ROOT,
    SPECS_DIR,
    PLAN_DIR,
    PLAN_BUILD_DIR,
    PLAN_DETAILS_DIR,
    LEDGER_DIR,
)

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


def resolve(root, *parts):
    """Absolute path to a documented location inside a project."""
    return os.path.join(os.path.abspath(root), *parts)


def documents(root):
    """Every document the method has written in a project, in a stable order.

    Specifications and plan alike, which is what a gate over "this project's
    documents" means. `status.documents` answers a narrower question — the plan
    documents a unit's status could live in — and is deliberately left alone.
    """
    return sorted(glob.glob(resolve(root, SPECS_DIR, "*.html"))
                  + glob.glob(resolve(root, PLAN_DIR, "*.html")))


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
