# -*- coding: utf-8 -*-
"""The decision gate every generator runs before it authors anything.

A question asked after authoring begins arrives when the answer is already
expensive: work exists in the shape of the wrong assumption (ADR-10). So every
fork is closed in one phase, before the first file, and the outcome is written
down — because a decision held only in a conversation is lost at the first
context reset (FR-DOC-03).

This module does not conduct the interview. It works out what needs asking,
holds the answers, and refuses to let a caller write while anything is open. The
asking belongs to whoever is talking to the owner; a module that reads a
terminal cannot run unattended (NFR-EXE-08, FR-EXE-08), and one that asks its
own questions cannot be tested without faking a keyboard.

Traces: FR-DOC-02, FR-DOC-03, FR-DOC-07, FR-EXE-08, NFR-EXE-04, NFR-EXE-08,
NFR-DAT-06, ADR-10, US-DOC-01, US-DOC-02.
"""

import collections
import os

from z2s import paths, schema, writer

#: The heading the table lives under, in the document and in the ledger alike.
#: Spelled once: a caller looking for the block and the writer emitting it must
#: agree, and two spellings of one heading is how a round trip quietly stops
#: round-tripping.
TABLE_HEADING = "## Locked decisions — do not re-litigate"

COLUMNS = ("#", "Decision", "Choice", "Rationale")

#: Said in the rationale column when the source answered the fork itself, so a
#: reader can tell an owner's choice from material that was already sufficient
#: (FR-DOC-07).
FROM_SOURCE = "stated in the source"

#: A cell holding one of these would end the row early. Escaped, never dropped —
#: the answer a reader gave is the answer the table has to show back.
_ESCAPES = (("\\", "\\\\"), ("|", "\\|"), ("\n", " "))

Option = collections.namedtuple("Option", "id label meaning recommended")
Fork = collections.namedtuple("Fork", "id question dimension options")
Decision = collections.namedtuple("Decision", "fork question choice rationale")


class GateNotClosed(Exception):
    """Raised when something would happen before every fork is resolved."""


class LockedForkConflict(Exception):
    """Raised when a locked row is contradicted rather than applied.

    Surfaced rather than silently re-decided (US-DOC-02-S03): the recorded
    choice may be right and reality wrong, and only a person can tell.
    """


def option(id, label, meaning="", recommended=False):
    """One answer a fork offers, in terms of what will actually exist."""
    return Option(id=id, label=label, meaning=meaning, recommended=bool(recommended))


def fork(id, question, options, dimension=None):
    """Declare one fork: a question, and the answers it offers.

    `dimension` names the key a source would have to carry to answer this fork
    without asking; it defaults to the fork's own identifier, which is the case
    everywhere so far.
    """
    options = tuple(options)

    if not question.strip().endswith("?"):
        raise ValueError("a fork must be phrased as a question, ending in '?': %r" % question)
    if len(options) < 2:
        raise ValueError("a fork with fewer than two options is not a fork: %r" % id)

    recommended = [one for one in options if one.recommended]
    if not recommended:
        raise ValueError("fork %r offers no recommended default; exactly one is required" % id)
    if len(recommended) > 1:
        raise ValueError("fork %r marks %d options recommended; exactly one is required"
                         % (id, len(recommended)))

    return Fork(id=id, question=question, dimension=dimension or id, options=options)


def _recommended(self):
    """The single option a fork recommends. Guaranteed to exist by `fork`."""
    return [one for one in self.options if one.recommended][0]


Fork.recommended = property(_recommended)


class Gate:
    """One gate phase over a declared set of forks.

    Construct it with whatever is already known — the source material, and any
    decisions recovered from an earlier run — then take questions one at a time
    until it closes.
    """

    def __init__(self, slug, forks, source=None, decisions=()):
        self.slug = slug
        self.forks = tuple(forks)
        self._by_id = collections.OrderedDict((one.id, one) for one in self.forks)
        self._decisions = collections.OrderedDict()

        for recovered in decisions:
            if recovered.fork in self._by_id:
                self._decisions[recovered.fork] = recovered

        self._from_source = self._harvest(source or {})
        self._resumed = bool(self._decisions) and not self._from_source

    def _harvest(self, source):
        """Close every fork the source already answers (FR-DOC-07).

        Sufficiency is a checklist against the declared forks rather than a
        judgement about the prose: a fork is answered when the source carries a
        real value under its dimension. `schema.is_empty` decides what real
        means, so the emptiness rule is defined in exactly one place.
        """
        answered = []
        for one in self.forks:
            if one.id in self._decisions:
                continue
            value = source.get(one.dimension)
            if schema.is_empty(value):
                continue
            self._decisions[one.id] = Decision(fork=one.id, question=one.question,
                                               choice=_text(value), rationale=FROM_SOURCE)
            answered.append(one.id)
        return tuple(answered)

    # -- what is still open ---------------------------------------------------

    @property
    def open_forks(self):
        """Every fork with no decision yet, in declaration order."""
        return tuple(one for one in self.forks if one.id not in self._decisions)

    @property
    def closed(self):
        return not self.open_forks

    @property
    def decisions(self):
        """Every decision, in declaration order."""
        return tuple(self._decisions[one.id] for one in self.forks if one.id in self._decisions)

    @property
    def skipped(self):
        """True when the source was rich enough that nothing had to be asked."""
        return bool(self._from_source) and self.closed and not self._resumed

    @property
    def skip_reason(self):
        if not self.skipped:
            return None
        return ("the source already answers every fork: " + ", ".join(self._from_source))

    def question(self):
        """The next fork to ask about, or None. One at a time (FR-DOC-02)."""
        still_open = self.open_forks
        return still_open[0] if still_open else None

    # -- answering ------------------------------------------------------------

    def answer(self, fork_id, choice, rationale):
        """Record one answer. `choice` may be an option identifier or free text.

        Anything outside the offered options is kept verbatim: the owner is
        allowed an answer nobody thought to offer, and rewriting it would lose
        the only part of the record that was not predicted.
        """
        one = self._by_id[fork_id]

        if not rationale or not rationale.strip():
            raise ValueError("fork %r needs a rationale; a choice without one is not a decision"
                             % fork_id)

        offered = {o.id: o.label for o in one.options}
        settled = Decision(fork=fork_id, question=one.question,
                           choice=offered.get(choice, choice), rationale=rationale.strip())

        already = self._decisions.get(fork_id)
        if already is not None:
            if already.choice != settled.choice:
                raise LockedForkConflict(
                    "fork %r is locked to %r; %r contradicts it. A locked row is applied, not "
                    "re-decided — resolve the conflict before continuing."
                    % (fork_id, already.choice, settled.choice))
            return already

        self._decisions[fork_id] = settled
        return settled

    def require_closed(self):
        """Raise unless every fork is resolved. Called before anything is written."""
        still_open = self.open_forks
        if still_open:
            raise GateNotClosed(
                "the gate is still open on %s; no file is written until every fork is resolved"
                % ", ".join(repr(one.id) for one in still_open))

    # -- the record -----------------------------------------------------------

    def table(self):
        """The locked-decisions table, as Markdown."""
        self.require_closed()
        lines = ["| " + " | ".join(COLUMNS) + " |",
                 "|" + "---|" * len(COLUMNS)]
        for decision in self.decisions:
            lines.append("| " + " | ".join(_cell(value) for value in
                                           (decision.fork, decision.question,
                                            decision.choice, decision.rationale)) + " |")
        return "\n".join(lines)

    def section(self):
        """The same table as a document section, or None when there is nothing
        to show. An empty section is absent, never present and empty
        (NFR-DAT-06)."""
        self.require_closed()
        if not self._decisions:
            return None
        return {"id": "locked-decisions", "type": "table",
                "title": "Locked decisions", "columns": list(COLUMNS),
                "rows": [[d.fork, d.question, d.choice, d.rationale] for d in self.decisions]}

    def record(self, root):
        """Write the table into the run ledger. Returns the path written.

        Refuses while a fork is open, which is what makes "no file before the
        gate completes" true of the filesystem and not merely of a flag.
        """
        self.require_closed()
        target = ledger_path(root, self.slug)

        folder = os.path.dirname(target)
        if not os.path.isdir(folder):
            os.makedirs(folder)

        writer.write(target, _merge(_existing(target), self.table(), self.slug))
        return target


def ledger_path(root, slug):
    """Where a run's ledger lives inside a project (SDD repository layout)."""
    return paths.resolve(root, paths.LEDGER_DIR, slug + ".md")


def load(root, slug):
    """Decisions recorded by an earlier run, or an empty tuple.

    This is the path that makes a locked row survive a lost conversation, so it
    tolerates a project with no ledger at all rather than treating that as an
    error (FR-EXE-09).
    """
    return read(_existing(ledger_path(root, slug)))


def read(text):
    """Parse a locked-decisions table back into decisions.

    Rows outside the table are ignored: a ledger is a running document and the
    table is one block inside it.
    """
    found = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if len(cells) != len(COLUMNS) or cells[0] in (COLUMNS[0], ""):
            continue
        if set(cells[0]) <= set("-: "):
            continue
        found.append(Decision(fork=cells[0], question=cells[1],
                              choice=cells[2], rationale=cells[3]))
    return tuple(found)


# -- text handling ------------------------------------------------------------

def _text(value):
    """A source value as the table will show it."""
    if isinstance(value, (list, tuple)):
        return "; ".join(str(item) for item in value)
    return str(value)


def _cell(value):
    """Escape one cell so its content cannot end the row it sits in."""
    text = _text(value)
    for character, replacement in _ESCAPES:
        text = text.replace(character, replacement)
    return text


def _cells(line):
    """Split one table row, honouring the escapes `_cell` writes."""
    out, current, escaped = [], [], False
    for character in line.strip().strip("|"):
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "|":
            out.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    out.append("".join(current).strip())
    return out


def _existing(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return ""


def _merge(existing, table, slug):
    """Put the table into the ledger, replacing any copy already there.

    Whatever else the ledger says is preserved: it is the run's own record and
    this module owns exactly one block of it.
    """
    block = TABLE_HEADING + "\n\n" + table + "\n"

    if TABLE_HEADING in existing:
        before, _, rest = existing.partition(TABLE_HEADING)
        after = ""
        for index, line in enumerate(rest.splitlines(True)):
            if index and line.startswith("#"):
                after = "".join(rest.splitlines(True)[index:])
                break
        return before.rstrip("\n") + "\n\n" + block + ("\n" + after if after else "")

    header = existing if existing else "# Ledger: %s\n" % slug
    return header.rstrip("\n") + "\n\n" + block
