# -*- coding: utf-8 -*-
"""The document runtime, as text a generator can embed.

The runtime lives in runtime.js rather than in a string literal here, so it is
an ordinary JavaScript file: an editor highlights it, a test runner loads it
directly, and a reader can read it without unpicking Python quoting.

Traces: FR-SPC-02, NFR-ARC-03, ADR-02.
"""

import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runtime.js")

with open(PATH, encoding="utf-8") as _handle:
    #: The runtime source, ready to be passed to shell.assemble(runtime=...).
    SOURCE = _handle.read()
