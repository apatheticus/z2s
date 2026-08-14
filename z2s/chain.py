# -*- coding: utf-8 -*-
"""What every generator below the vision does the same way.

The vision needs nothing above it. Everything after it does: the context
document needs a completed vision, the product requirements need both, and so
on down the chain. That shared position brings shared obligations — refuse
without the document above, keep a source register, record what the brief was
silent about, number what later documents will cite — and each of them is the
sort of rule that goes wrong quietly when it is written out a second time.

So the rules live here once, and a generator brings only what is actually its
own: its schema, its gate questions, its validator rules (NFR-ARC-01).

Nothing here reaches the network or the clock. A generator that fetched a
recorded web address, or stamped the day it ran onto a document, would break
the guarantee that unchanged input regenerates unchanged bytes (NFR-GEN-01).

Traces: FR-DOC-04, FR-DOC-08, FR-DOC-10, FR-CTX-01, NFR-ARC-01, NFR-DAT-03,
NFR-DAT-06, NFR-GEN-01.
"""

import collections

from z2s import document, gate, paths, runtime, schema, styles, tokens, validate, writer

#: What a source may be (FR-DOC-10). A web address is a recorded origin, never
#: a fetch: this package opens no socket, which is why it imports nothing that
#: could.
SOURCE_KINDS = ("narrative", "document", "web")
SOURCE_COLUMNS = ("Kind", "Source", "Where it came from", "What it contributed")

#: The most a two-digit identifier can count to. Past this the grammar cannot
#: express the identifier, and a silently malformed one is worse than a stop.
MAX_IDENTIFIED = 99


class IncompleteBrief(Exception):
    """Raised when the brief omits something that cannot be defaulted or invented."""


class MissingPrerequisite(Exception):
    """Raised when the document above this one does not exist, or cannot be read.

    Separate from `IncompleteBrief` because the two are fixed differently: one
    needs a fact, the other needs a document generated first.
    """


# ------------------------------------------------------------- the chain above

def require(root, filename, slug, needed_by):
    """The specification of the document above this one, or a refusal.

    The refusal names the missing document and where it was looked for, because
    "generation failed" tells an operator nothing about what to do next
    (FR-CTX-01, US-CTX-01-S01). It happens before any path is created, so a
    refused run leaves the project exactly as it found it.
    """
    target = paths.resolve(root, paths.SPECS_DIR, filename)

    try:
        with open(target, encoding="utf-8") as handle:
            html = handle.read()
    except OSError:
        raise MissingPrerequisite(
            "%s needs a completed %s document; there is none at %s. Generate the %s "
            "first. Nothing was written." % (needed_by, slug, target, slug))

    try:
        found = validate.extract(html)
    except validate.ExtractionError as error:
        raise MissingPrerequisite(
            "%s needs a completed %s document; %s carries no readable specification "
            "(%s). Nothing was written." % (needed_by, slug, target, error))

    block = found.get("document") if isinstance(found, dict) else None
    stated = block.get("slug") if isinstance(block, dict) else None
    if stated != slug:
        raise MissingPrerequisite(
            "%s needs a completed %s document; %s is a %r document. Nothing was written."
            % (needed_by, slug, target, stated))
    return found


# -------------------------------------------------------------- the envelope

def envelope(brief, slug, type, required, defaults, carried=()):
    """The document block, from facts only (FR-DOC-08).

    Every missing fact is named at once. A caller who supplies one, runs again
    and is told about the next stops running the generator.
    """
    missing = [name for name in required if schema.is_empty(brief.get(name))]
    if missing:
        raise IncompleteBrief(
            "the brief states no %s; a %s cannot be authored without it, and inventing "
            "one is the failure this method exists to prevent" % (", ".join(missing), slug))

    block = {"title": brief["title"], "slug": slug, "type": type,
             "date": brief["date"], "owner": brief["owner"]}
    for name, default in sorted(defaults.items()):
        block[name] = brief.get(name) or default
    for name in carried:
        if not schema.is_empty(brief.get(name)):
            block[name] = brief[name]
    return block


# ------------------------------------------------------------- identifiers

def identifier(prefix, index):
    """The identifier for the nth entry of a series, counting from zero.

    Two digits, always, because the grammar says two (NFR-DAT-03) and a trace
    written to "VC-3" finds nothing.
    """
    if index + 1 > MAX_IDENTIFIED:
        raise IncompleteBrief(
            "more than %d %s entries; the identifier grammar cannot express %s-%d, and a "
            "malformed identifier breaks every trace to it"
            % (MAX_IDENTIFIED, prefix, prefix, index + 1))
    return "%s-%02d" % (prefix, index + 1)


def traces(item):
    """An entry's upward links, with empty kinds dropped.

    An empty trace list is a heading over nothing in a machine's reading of the
    document, and the emptiness rule applies to data as much as to prose
    (NFR-DAT-06).
    """
    return {kind: list(values) for kind, values in sorted(item.get("traces", {}).items())
            if not schema.is_empty(values)}


def identified(spec, kind):
    """Every identifier of one kind the given document assigned.

    What a document below is allowed to cite: the chain's rule is that scope
    arrives from the document above or not at all, and this is the set of things
    "above" actually contains.
    """
    return {entry["id"] for _, entry in schema.entries(spec)
            if schema.kind_of(entry.get("id")) == kind}


# ------------------------------------------------------------------ the sifting

#: What a part of a document must trace to before it can be written down.
#:
#: `above` finishes the sentence when a citation names something that does not
#: exist, because "unknown identifier" leaves an author guessing which document
#: was supposed to contain it. Declared as data so that the parts of a document
#: cannot quietly grow several different answers to the same question.
Rule = collections.namedtuple("Rule", "kind upstream noun verb name above")


def named(items, key, noun):
    """Every entry says what it is. A nameless one is a malformed brief.

    This is not a gap: a gap names the thing the brief is silent about, and an
    entry with no words in it leaves nothing to name and nothing to ask.
    """
    items = list(items or ())
    for index, one in enumerate(items):
        if schema.is_empty(one.get(key)):
            raise IncompleteBrief(
                "%s %d states no %s; there is nothing to write down and nothing to ask "
                "about" % (noun, index + 1, key))
    return items


def traced(items, rule, known):
    """Entries whose upward citations all exist, and a gap for each that does not.

    An entry citing nothing and an entry citing something imaginary are the same
    failure at different stages of confidence, so both leave the document by the
    same door: recorded as a question, never written down as fact (FR-TRC-03).
    """
    kept, gaps = [], []
    for one in items:
        cited = list((one.get("traces") or {}).get(rule.kind) or ())
        unknown = [target for target in cited if target not in known]
        asked = "which %s the %s “%s” %s" % (rule.upstream, rule.noun,
                                             one[rule.name], rule.verb)
        if not cited:
            gaps.append(asked)
        elif unknown:
            gaps.append("%s; it cites %s, which %s"
                        % (asked, ", ".join(unknown), rule.above))
        else:
            kept.append(one)
    return kept, gaps


def complete(items, field, key, phrasing):
    """Entries that state `field`, and a gap naming each that does not."""
    kept, gaps = [], []
    for one in items:
        if schema.is_empty(one.get(field)):
            gaps.append(phrasing % one[key])
        else:
            kept.append(one)
    return kept, gaps


def card(item):
    """One card: a title, a body, and whatever it traces to."""
    built = {"title": item["title"], "body": item["body"]}
    found = traces(item)
    if found:
        built["traces"] = found
    return built


# ------------------------------------------------------------ source register

def register(brief):
    """Every source consulted, in the order the brief lists them (FR-DOC-10).

    A source with nothing recorded about what it contributed is not rejected —
    it was still consulted, and dropping it would lose the provenance the
    register exists for. It becomes a gap instead.
    """
    entries, gaps = [], []
    for index, source in enumerate(brief.get("sources", ()) or ()):
        kind = source.get("kind")
        if kind not in SOURCE_KINDS:
            raise IncompleteBrief(
                "source %d has kind %r; a source is one of %s"
                % (index + 1, kind, ", ".join(SOURCE_KINDS)))

        name = source.get("name") or ""
        entry = {"kind": kind, "name": name,
                 "origin": source.get("origin") or "",
                 "contributed": source.get("contributed") or ""}
        entries.append(entry)

        called = name or "source %d" % (index + 1)
        if schema.is_empty(entry["origin"]):
            gaps.append("where %s came from" % called)
        if schema.is_empty(entry["contributed"]):
            gaps.append("what %s contributed" % called)
    return entries, gaps


def register_section(entries):
    return {"id": "sources", "type": "table", "title": "Source register",
            "columns": list(SOURCE_COLUMNS),
            "rows": [[one["kind"], one["name"], one["origin"], one["contributed"]]
                     for one in entries]}


# -------------------------------------------------------------------- the gaps

#: How a gap reads under each answer to the `gaps` fork. Both say the same thing
#: about the same silence; they differ in what is being asked of the reader —
#: answer this, or confirm this.
GAP_PHRASING = {
    "question": ("open-questions", "Open questions",
                 "The brief says nothing about %s. What should it say?"),
    "assumption": ("assumptions", "Assumptions",
                   "Nothing was stated about %s; it is taken to be absent until a later "
                   "document says otherwise. Confirm before the next document."),
}

def gaps_fork(subject):
    """The fork that decides how this document files what its source omits.

    Declared here rather than in each generator because both answers have to
    keep matching GAP_PHRASING above; a fork offering an option the phrasing
    does not know would fall back to the recommendation and look like it had
    been ignored.
    """
    return gate.fork(
        "gaps",
        "Where the %s is silent, should the document ask, or state an assumption?" % subject,
        [gate.option("question", "Ask an open question",
                     "The silence appears under Open questions, unanswered, for someone "
                     "to answer before the next document.",
                     recommended=True),
         gate.option("assumption", "State an assumption",
                     "The silence appears under Assumptions, as something taken to be "
                     "true and flagged for confirmation.")])


def gap_section(gaps, choice):
    """The gaps, filed where the gate said to file them (FR-DOC-04)."""
    if not gaps:
        return None
    section_id, title, phrasing = GAP_PHRASING.get(choice, GAP_PHRASING["question"])
    return {"id": section_id, "type": "list", "title": title,
            "items": [phrasing % gap for gap in gaps]}


# ------------------------------------------------------------- the gate's answers

def decision(run, fork_id):
    """What the gate settled one fork on, or None if it never saw that fork."""
    for settled in run.decisions:
        if settled.fork == fork_id:
            return settled
    return None


def choice(run, fork_id):
    """A settled fork, matched back to the identifier of the option chosen.

    An answer nobody offered is returned as given rather than forced onto an
    option: the owner is allowed an answer the fork did not predict, and the
    caller decides what to do with one it does not recognise.
    """
    settled = decision(run, fork_id)
    if settled is None:
        return None
    for one in run.forks:
        if one.id != fork_id:
            continue
        for offered in one.options:
            if settled.choice in (offered.id, offered.label):
                return offered.id
    return settled.choice


# ------------------------------------------------------------------ the writing

def render(spec, spec_id, root="."):
    """The finished document text, styled with the host project's tokens."""
    values, _ = tokens.detect(root)
    return document.render(spec, spec_id,
                           description=spec["document"].get("summary", ""),
                           tokens=tokens.render(values),
                           struct=styles.STRUCT,
                           runtime=runtime.SOURCE)


def write(root, filename, spec, spec_id):
    """Write a rendered document into the project. Returns the path written."""
    target = paths.resolve(root, paths.SPECS_DIR, filename)
    writer.write(target, render(spec, spec_id, root))
    return target


def regenerate(root, filename, slug, spec_id, spec=None):
    """Re-render a document from its own embedded specification (FR-DOC-06).

    The document is its own source: an update is made by editing the
    specification inside it and re-rendering, never by editing rendered markup
    (ADR-02). Given no specification this reads the one already in the file, so
    regenerating an untouched document is a no-op rather than a rebuild from a
    brief nobody kept.
    """
    if spec is None:
        spec = require(root, filename, slug, "regeneration")
    return write(root, filename, spec, spec_id)
