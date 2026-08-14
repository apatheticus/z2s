# -*- coding: utf-8 -*-
"""The only place in the toolchain that writes a file.

A document is written completely or not at all (NFR-GEN-02). The content goes to
a temporary file beside the target and is renamed into place, because a rename
within one directory is the closest thing a filesystem offers to an instant
swap. If anything fails on the way, the previous file is still the file that is
there.

Traces: FR-GEN-07, NFR-GEN-01, NFR-GEN-02, US-STA-03.
"""

import os

#: Deliberately fixed rather than randomised. LD-03 settles that the orchestrator
#: is the only writer in a run, so writes are serialised by construction and two
#: temporary files can never contend. A predictable name is also a name a human
#: can recognise and delete if a process is killed outright.
TEMP_SUFFIX = ".z2s-tmp"


def write(path, text, encoding="utf-8"):
    """Write `text` to `path` atomically. Returns the path written.

    Newlines are fixed at "\\n" so the same input produces the same bytes on
    every platform (NFR-GEN-01).
    """
    path = os.path.abspath(path)
    temporary = path + TEMP_SUFFIX

    try:
        with open(temporary, "w", encoding=encoding, newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        _discard(temporary)
        raise

    return path


def _discard(path):
    """Remove a temporary file, never masking the error that got us here."""
    try:
        os.remove(path)
    except OSError:
        pass
