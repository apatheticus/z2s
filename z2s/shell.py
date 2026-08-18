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
#: the answer is to split it, not to weaken the limit — so the number lives
#: here, in code, rather than in a project's configuration (NFR-PRF-02).
#:
#: Raised from 250 KB to 1024 KB and then to 2048 KB by the owner, both on
#: 2026-08-15 (M14-05, M14-12). The 250 was never a decision anybody made; it
#: was the first plausible figure written down, and it had stood as a standing
#: warning on the published plan ever since.
#:
#: The second raise was made against a measurement rather than a feeling. A plan
#: that carries its own execution instructions at four granularities carries
#: several hundred KB of quoted prompt by design — the published one is 173
#: prompts at about 5.7 KB each — and at that shape 1024 KB was a target the
#: method could not meet while doing what it says it does. The alternative was
#: to split the published plan per milestone, which is what the technical design
#: prescribes and what the toolchain already does; the owner chose to keep one
#: file and move the number, knowing the cost is a large version-control diff.
#: Measured at the time: 1464 KB raw, 113 KB over the wire, 1.2s to load.
#:
#: NFR-PRF-02 names no number, so nothing frozen has moved through any of this —
#: only the target row in the technical specification, and this constant.
SIZE_BUDGET = 2048 * 1024

#: Of that, the most the shared chrome — tokens, structural styling, runtime —
#: may take. What is left is the space a specification actually has to grow in.
#:
#: Raised from 64 KB when the plan documents arrived (M8-07, 2026-08-14). This
#: divides the budget above differently; it does not weaken it. The rule that
#: matters is still one document under the size budget above, still enforced,
#: still not downgradable by configuration.
#:
#: What was rejected, and why: shipping the runtime and the stylesheet with
#: their comments stripped would have saved about 25 KB and cost more than it
#: saved. It needs a comment stripper written by hand — there is no third-party
#: dependency to reach for (NFR-ARC-03) — and a hand-rolled one mistakes a
#: pattern or a string for a comment sooner or later. It also makes what ships
#: stop being what anyone read.
#:
#: Raised again from 96 KB by the owner, 2026-08-17 (M16-06), when the token
#: contract widened from 39 names to 52 and the theme learned to state a dark
#: counterpart. 1,127 bytes of headroom was not headroom; it was a number one
#: comment away from being a decision made by accident. NFR-PRF-02 names no
#: number, so nothing frozen moved — only this constant, exactly as the three
#: raises above it.
CHROME_BUDGET = 128 * 1024

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

    The token slot is checked before it is filled. It is not the real control —
    that is refusal at reading, in design.py, because a CSS declaration value
    cannot be escaped — but this is the boundary the value crosses, and the
    check is here so the NEXT caller to source tokens from somewhere else gets
    it too. A style block that can be closed from inside a declaration is a
    script tag in a file people open from disk.
    """
    if "<" in tokens:
        raise ValueError(
            "the token block contains '<', which can close the style element: "
            "the value has to be refused where it was read, not written here")
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
    # No severity word in the sentence: the caller carries the severity, and a
    # message that states its own is a message that disagrees with its finding
    # the day somebody re-uses it (M14-05, when the pipeline started reporting
    # these as warnings).
    # Rounded UP, both figures. Rounding down reported a document ten bytes
    # over as "1024 KB exceeds the 1024 KB budget by 0 KB", which reads as a
    # bug in the checker rather than a fact about the document.
    return Budget(False, size,
                  "%s: %d KB exceeds the %d KB budget by %d KB; split it"
                  % (name, -(-size // 1024), SIZE_BUDGET // 1024,
                     -(-(size - SIZE_BUDGET) // 1024)))
