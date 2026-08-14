# -*- coding: utf-8 -*-
"""The shared document shell: one skeleton, filled once.

The skeleton carries no project, product or domain assumption (FR-GEN-01) and is
never forked per project (NFR-ARC-04). Everything that varies arrives as a slot
value: the styling tokens, the structural styling, the runtime, and the embedded
specification itself.

Traces: FR-SPC-03, NFR-ARC-03, NFR-ARC-04, ADR-01.
"""

import collections
import html as _html
import re

#: The most a single generated document may weigh. A document past this stops
#: opening instantly and stops being reviewable in a version-control diff, and
#: the answer is to split it, not to raise the limit — so the number lives here,
#: in code, rather than in a project's configuration (NFR-PRF-02).
SIZE_BUDGET = 250 * 1024

#: Of that, the most the shared chrome — tokens, structural styling, runtime —
#: may take. What is left is the space a specification actually has to grow in.
CHROME_BUDGET = 64 * 1024

#: One line for the run report, plus the verdict a check can act on.
Budget = collections.namedtuple("Budget", "within size text")

#: Slots are substituted in a single pass. A value is never rescanned, so a
#: specification whose own text happens to contain "__RUNTIME__" is safe.
SLOT = re.compile(r"__([A-Z_]+)__")

SKELETON = """<!doctype html>
<html lang="__LANG__">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>__TITLE__</title>
<meta name="description" content="__DESCRIPTION__" />
<style>
/* Design tokens. Everything visual resolves through these; no colour, font or
   shadow literal belongs below this block (NFR-GEN-03). */
__TOKENS__
/* Structural styling, shared by every document and never edited per project. */
__STRUCT__
</style>
</head>
<body>
<main id="doc"></main>
<script type="application/json" id="__SPEC_ID__">
__SPEC_JSON__
</script>
<script>
__RUNTIME__
</script>
</body>
</html>
"""


def assemble(spec_id, spec_json, title, description,
             tokens="", struct="", runtime="", lang="en"):
    """Build the complete document text from its parts.

    Kept deliberately separate from serialisation so either half can be tested
    alone. Substitution is one pass over the skeleton: slot values are copied
    into the output verbatim and are never themselves searched for slots.
    """
    values = {
        "LANG": _html.escape(lang, quote=True),
        "TITLE": _html.escape(title),
        "DESCRIPTION": _html.escape(description, quote=True),
        "TOKENS": tokens,
        "STRUCT": struct,
        "RUNTIME": runtime,
        "SPEC_ID": _html.escape(spec_id, quote=True),
        "SPEC_JSON": spec_json,
    }

    missing = []

    def fill(match):
        name = match.group(1)
        if name not in values:
            missing.append(name)
            return match.group(0)
        return values[name]

    out = SLOT.sub(fill, SKELETON)
    if missing:
        raise KeyError("shell skeleton has unfilled slots: %s"
                       % ", ".join(sorted(set(missing))))
    return out


def budget_report(name, text):
    """Measure one finished document against the budget.

    Reports the real number either way. A document over budget is named, with
    the amount it is over by and what to do about it — never rounded down to a
    pass (FR-GEN-03).
    """
    size = len(text.encode("utf-8"))
    if size <= SIZE_BUDGET:
        return Budget(True, size, "%s: %d KB, within the %d KB budget"
                      % (name, size // 1024, SIZE_BUDGET // 1024))
    return Budget(False, size,
                  "WARN — %s: %d KB exceeds the %d KB budget by %d KB; split it"
                  % (name, size // 1024, SIZE_BUDGET // 1024,
                     (size - SIZE_BUDGET) // 1024))
