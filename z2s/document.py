# -*- coding: utf-8 -*-
"""Turn a specification object into a self-contained document.

The embedded object is the contract every other tool in the method reads
(FR-SPC-01); the human-readable view is rendered from that same object at load
time, which is what makes the two unable to drift apart (FR-SPC-02).

Traces: FR-SPC-01, FR-SPC-02, FR-SPC-03, NFR-GEN-01, ADR-01, ADR-02.
"""

import json

from z2s import shell


def serialise(spec):
    """Serialise a specification object deterministically.

    Stable key order and fixed indentation, so regenerating unchanged input
    produces unchanged bytes (NFR-GEN-01) and a real change stays legible in a
    diff rather than drowning in reordering noise (ADR-11).
    """
    text = json.dumps(spec, indent=1, sort_keys=True, ensure_ascii=False)
    # A literal "</" anywhere in the data would end the embedding element early,
    # truncating the specification. "\/" is a valid JSON escape for "/", so this
    # is lossless — a parser sees the original characters back.
    return text.replace("</", "<\\/")


def render(spec, spec_id, title=None, description="", **shell_parts):
    """Render one complete, self-contained document.

    `title` defaults to the specification's own title when it carries one, so a
    caller never has to state the same fact twice.
    """
    if title is None:
        title = spec.get("title") or spec.get("document", {}).get("title") or ""
    return shell.assemble(spec_id=spec_id,
                          spec_json=serialise(spec),
                          title=title,
                          description=description,
                          **shell_parts)
