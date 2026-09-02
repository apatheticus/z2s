# -*- coding: utf-8 -*-
"""The context generator: one vocabulary, agreed once, used everywhere after.

This document sits between the intent and the product requirements, and it
exists because of a specific failure: two people read the same requirement,
each substitutes their own meaning for one word, and both believe they agree
until something is built. The cure is domain-driven design's oldest rule — one
word, one meaning — written down where every later generator can read it.

Four rules shape everything below.

  * There is nothing to harvest until an intent exists. Invoked without one the
    generator names what is missing and leaves the project exactly as it found
    it (FR-CTX-01, US-CTX-01-S01).
  * A term comes from the intent or from a source the intent registered. A word
    the generator cannot trace back is an open question, never an entry
    (US-CTX-01-S02) — the same refusal to invent that governs the intent.
  * A word carrying two meanings is asked about, never settled quietly
    (FR-CTX-04). The answer may be to keep both, each scoped to its bounded
    context, and then the context map shows the boundary that word crosses
    (FR-CTX-03, FR-CTX-06).
  * Everything downstream speaks this language. `consult` replaces a retired
    synonym with its canonical term, and `amend` adds a missing word here
    rather than letting a later document define it locally (FR-CTX-05).

The brief is a plain dictionary:

    {"title": ..., "owner": ..., "date": "2026-08-14",       # required facts
     "version": ..., "status": ..., "summary": ...,          # optional
     "overview": "paragraph" | ["paragraph", ...],
     "contexts": [{"name": ..., "body": ...,
                   "feeds": ["another context", ...]}],
     "terms":    [{"term": ..., "definition": ...,
                   "source": "the intent" | <a registered source> | "VC-01",
                   "context": <a declared context>,
                   "synonyms": [...]}],
     "sources":  [{"kind": ..., "name": ..., "origin": ...,
                   "contributed": ...}]}

Traces: FR-CTX-01, FR-CTX-02, FR-CTX-03, FR-CTX-04, FR-CTX-05, FR-CTX-06,
FR-DOC-04, FR-DOC-08, FR-DOC-10, NFR-ARC-01, NFR-DAT-03, NFR-DAT-06,
NFR-GEN-01, US-CTX-01, US-CTX-02, US-CTX-03.
"""

import collections
import re

from z2s import chain, gate, paths, schema, intent

SLUG = "context"
TYPE = "Context document"
FILENAME = "Context.html"
SPEC_ID = SLUG + "-spec"

REQUIRED_FACTS = ("title", "owner", "date")
DEFAULTS = {"version": "1.0", "status": "Draft for review"}
CARRIED = ("summary",)

#: What a term may cite when it came from the intent itself rather than from
#: one of the sources the intent registered.
INTENT_SOURCE = "the intent"

#: What the same citation was called before the first document was renamed.
#: A context brief written against a Vision still cites it this way, and the
#: toolchain never asks a project to rewrite what it already wrote.
LEGACY_SOURCE = "the vision"

MAP_COLUMNS = ("From", "To", "What crosses", "How the meaning changes")

#: Said in the map where nothing about the meaning changes. A blank cell reads
#: as an oversight; this reads as an answer.
UNCHANGED = "—"

#: Keys whose contents a reader reads. `consult` speaks the language inside
#: these and nowhere else, so a slug, an identifier or a trace is never
#: rewritten into prose.
SPOKEN = ("title", "text", "body", "items", "definition", "term", "rows", "columns")

IncompleteBrief = chain.IncompleteBrief
MissingPrerequisite = chain.MissingPrerequisite


class UnresolvedCollision(Exception):
    """Raised when a collision's answer matches none of the options offered.

    The gate lets an owner answer in their own words, which is right for a
    question about scope or phrasing. A collision is not that kind of question:
    the options are the meanings on the table, and an answer outside them
    leaves the generator with no meaning to write down. Refusing and repeating
    the answer back is the only move that is not a silent pick (FR-CTX-04).
    """


# -------------------------------------------------------------- the collisions

#: One word that cannot be written down until somebody chooses. `kind` is
#: "duplicate" (the same word defined twice) or "overlap" (a word defined on
#: its own and also claimed as another term's synonym). `indices` point into
#: the brief's own term list, so the resolution and the question cannot drift
#: apart: both are computed from this one function.
Collision = collections.namedtuple("Collision", "kind id word indices")

_MEANING = re.compile(r"^meaning-(\d+)$")
_UL = re.compile(r"^UL-(\d+)$")


def _key(word):
    return (word or "").strip().casefold()


def _slug(word):
    return re.sub(r"[^a-z0-9]+", "-", _key(word)).strip("-") or "term"


def collisions(terms):
    """Every word the brief cannot settle on its own, in the order stated.

    A word repeated with the *same* definition is not a collision — there is no
    meaning to choose between, and asking about it would train an operator to
    answer without reading. It collapses into one entry instead.
    """
    terms = list(terms or ())
    found, order = collections.OrderedDict(), []

    for index, one in enumerate(terms):
        found.setdefault(_key(one.get("term")), []).append(index)
        if _key(one.get("term")) not in order:
            order.append(_key(one.get("term")))

    out = []
    for word in order:
        indices = found[word]
        stated = []
        for index in indices:
            if terms[index].get("definition") not in [terms[i].get("definition")
                                                      for i in stated]:
                stated.append(index)
        if len(stated) > 1:
            out.append(Collision("duplicate", "term:" + _slug(word),
                                 terms[stated[0]]["term"], tuple(stated)))
            continue

        # A word defined on its own that another term also claims as a synonym
        # is an overlap: one of the two claims has to go (FR-CTX-04).
        owner = _owner_of(terms, word, indices)
        if owner is not None:
            out.append(Collision("overlap", "overlap:" + _slug(word),
                                 terms[indices[0]]["term"], (indices[0], owner)))
    return tuple(out)


def _owner_of(terms, word, indices):
    """The term that claims `word` as one of its synonyms, if any."""
    for index, one in enumerate(terms):
        if index in indices:
            continue
        if word in [_key(synonym) for synonym in one.get("synonyms") or ()]:
            return index
    return None


def _fork(collision, terms):
    if collision.kind == "duplicate":
        return _duplicate_fork(collision, terms)
    return _overlap_fork(collision, terms)


def _duplicate_fork(collision, terms):
    contexts = [terms[index].get("context") for index in collision.indices]
    scoped = all(contexts) and len(set(contexts)) == len(contexts)

    options = []
    if scoped:
        options.append(gate.option(
            "scope", "Keep both, scoped to their bounded contexts",
            "The entry states both meanings, each named with the context it holds in, "
            "and the context map shows the boundary the word crosses.",
            recommended=True))
    for number, index in enumerate(collision.indices, start=1):
        options.append(gate.option(
            "meaning-%d" % number,
            "Meaning %d — %s" % (number, contexts[number - 1] or "stated without a context"),
            "“%s” means: %s Everywhere. The other meanings are not written down."
            % (collision.word, terms[index]["definition"]),
            recommended=not scoped and number == 1))

    return gate.fork(collision.id,
                     "The term “%s” is defined %d different ways. Which meaning does this "
                     "project use?" % (collision.word, len(collision.indices)),
                     options)


def _overlap_fork(collision, terms):
    standalone, owner = collision.indices
    other = terms[owner]["term"]
    return gate.fork(
        collision.id,
        "“%s” is defined on its own and is also listed as a synonym of “%s”. Which is it?"
        % (collision.word, other),
        [gate.option("synonym", "Retire “%s”; it is another word for “%s”"
                     % (collision.word, other),
                     "One word, one meaning: “%s” keeps the definition and “%s” is "
                     "recorded on it as a synonym a reader may still meet."
                     % (other, collision.word),
                     recommended=True),
         gate.option("term", "Keep “%s” as a term in its own right" % collision.word,
                     "The two are different things. “%s” keeps its own definition and "
                     "stops being listed as a synonym of “%s”."
                     % (collision.word, other))])


def forks(brief):
    """Every fork this brief opens: how to file silence, plus one per collision."""
    terms = brief.get("terms") or ()
    return (chain.gaps_fork("brief"),) + tuple(_fork(one, list(terms))
                                               for one in collisions(terms))


def open_gate(brief, root=None):
    """The gate this generator runs, over whatever is already known."""
    decisions = gate.load(root, SLUG) if root is not None else ()
    return gate.Gate(SLUG, forks(brief), source=brief, decisions=decisions)


# ---------------------------------------------------------------- the harvest

def sourced(upstream):
    """Everything a term is allowed to cite, from the intent and its register.

    The set is the whole of FR-CTX-01 in one place: the intent itself, anything
    it registered as a source, and any identifier it assigned. A citation
    outside it is not provenance, it is a claim.
    """
    allowed = {_key(INTENT_SOURCE), _key(LEGACY_SOURCE)}
    block = upstream.get("document") or {}
    if block.get("title"):
        allowed.add(_key(block["title"]))
    for source in upstream.get("sources") or ():
        if source.get("name"):
            allowed.add(_key(source["name"]))
    for _, entry in schema.entries(upstream):
        if schema.kind_of(entry.get("id")):
            allowed.add(_key(entry["id"]))
    return allowed


def _unsourced(terms, allowed):
    """Which terms cannot be traced back, and what to ask about each."""
    missing, gaps = set(), []
    for index, one in enumerate(terms):
        stated = one.get("source")
        if schema.is_empty(stated):
            missing.add(index)
            gaps.append("where the term “%s” came from" % one["term"])
        elif _key(stated) not in allowed:
            missing.add(index)
            gaps.append("how the term “%s” traces to the intent or one of its sources"
                        % one["term"])
    return missing, gaps


# ------------------------------------------------------------- the resolution

def _resolve(terms, run, missing):
    """Apply what the gate settled. Returns (kept, definitions, meanings, retired).

    `kept` is the surviving indices in the brief's own order; the rest describe
    what the answers changed about them.
    """
    # The same word with the same definition, stated twice, is one entry: there
    # is nothing to choose between them, and keeping both would put one term in
    # the glossary under two identifiers (FR-CTX-02).
    kept, said = [], set()
    for index, one in enumerate(terms):
        signature = (_key(one.get("term")), one.get("definition"))
        if index in missing or signature in said:
            continue
        said.add(signature)
        kept.append(index)

    definitions, meanings, retired, crossings = {}, {}, {}, []

    for one in collisions(terms):
        live = [index for index in one.indices if index not in missing]
        if len(live) < 2:
            # Whatever the answer was, there is no longer a choice to apply.
            continue
        answer = chain.choice(run, one.id)

        if one.kind == "duplicate":
            _apply_duplicate(one, live, terms, answer, kept,
                             definitions, meanings, crossings)
        elif answer == "synonym":
            kept.remove(live[0])
        elif answer == "term":
            retired.setdefault(live[1], set()).add(_key(one.word))
        else:
            raise UnresolvedCollision(_refusal(one, answer))
    return kept, definitions, meanings, retired, crossings


def _apply_duplicate(collision, live, terms, answer, kept,
                     definitions, meanings, crossings):
    first = live[0]

    if answer == "scope":
        stated = [{"context": terms[index].get("context") or "",
                   "definition": terms[index]["definition"]} for index in live]
        meanings[first] = stated
        definitions[first] = " ".join(
            ("In %s: %s" % (one["context"], one["definition"])) if one["context"]
            else one["definition"] for one in stated)
        for other in stated[1:]:
            if stated[0]["context"] and other["context"]:
                crossings.append([stated[0]["context"], other["context"],
                                  "the term “%s”" % collision.word,
                                  "In %s: %s In %s: %s"
                                  % (stated[0]["context"], stated[0]["definition"],
                                     other["context"], other["definition"])])
        for index in live[1:]:
            kept.remove(index)
        return

    chosen = _MEANING.match(answer or "")
    number = int(chosen.group(1)) if chosen else 0
    if not 1 <= number <= len(collision.indices):
        raise UnresolvedCollision(_refusal(collision, answer))

    survivor = collision.indices[number - 1]
    if survivor not in live:
        raise UnresolvedCollision(
            "the answer to %r chose a meaning of “%s” that could not be traced to the "
            "intent; nothing was written" % (collision.id, collision.word))
    for index in live:
        if index != survivor:
            kept.remove(index)


def _refusal(collision, answer):
    return ("the term “%s” was answered %r, which is not one of the meanings offered; "
            "a collision is resolved by choosing between them, and picking one for you "
            "is the failure this question exists to prevent" % (collision.word, answer))


# --------------------------------------------------------------- the glossary

def _entry(index, terms, definitions, meanings, retired):
    one = terms[index]
    word = one["term"].strip()
    synonyms = [synonym for synonym in one.get("synonyms") or ()
                if _key(synonym) not in retired.get(index, set())]

    definition = definitions.get(index, one["definition"])
    if synonyms:
        definition = "%s Also called %s." % (
            definition, ", ".join("“%s”" % synonym for synonym in synonyms))

    entry = {"canonical": word, "definition": definition,
             "source": one.get("source") or ""}
    if synonyms:
        entry["synonyms"] = list(synonyms)
    if one.get("context") and index not in meanings:
        entry["context"] = one["context"]
    if index in meanings:
        entry["meanings"] = [dict(stated) for stated in meanings[index]]
    return entry


def _numbered(entries):
    """Assign UL identifiers, and carry each one where a reader can see it."""
    out = []
    for index, entry in enumerate(entries):
        identifier = chain.identifier("UL", index)
        entry["id"] = identifier
        # Said twice from one assignment, as the intent does with its
        # capabilities: the data carries the identifier so a later document can
        # trace to it, and the term carries it because the runtime renders a
        # definition list's term and definition, not its identifier.
        entry["term"] = "%s · %s" % (identifier, entry["canonical"])
        out.append(entry)
    return out


def glossary_section(entries):
    return {"id": "glossary", "type": "definitions", "title": "The ubiquitous language",
            "items": entries}


# -------------------------------------------------------- the bounded contexts

def _context_cards(contexts):
    cards = []
    for index, one in enumerate(contexts):
        identifier = chain.identifier("BC", index)
        cards.append({"id": identifier,
                      "title": "%s · %s" % (identifier, one["name"]),
                      "body": one["body"]})
    return {"id": "contexts", "type": "cards", "title": "Bounded contexts",
            "items": cards}


def _map_rows(contexts, crossings):
    """Which context feeds which, and where a word changes meaning (FR-CTX-06)."""
    rows = []
    for one in contexts:
        for fed in one.get("feeds") or ():
            rows.append([one["name"], fed,
                         "Everything %s produces" % one["name"], UNCHANGED])
    return rows + crossings


def _declared(contexts, terms):
    """Every context named must be a context the document declares."""
    names = {_key(one["name"]) for one in contexts}
    for one in contexts:
        for fed in one.get("feeds") or ():
            if _key(fed) not in names:
                raise IncompleteBrief(
                    "the context %r feeds %r, which this brief does not declare; a map "
                    "cannot show a boundary that has no side" % (one["name"], fed))
    for one in terms:
        named = one.get("context")
        if named and _key(named) not in names:
            raise IncompleteBrief(
                "the term %r is scoped to the bounded context %r, which this brief does "
                "not declare; scoping a word to a context nobody defined is the "
                "invention this document exists to prevent" % (one["term"], named))
    return [one["name"] for one in contexts]


# ------------------------------------------------------------------ generation

def envelope(brief):
    """The document block, from facts only (FR-DOC-08)."""
    return chain.envelope(brief, SLUG, TYPE, REQUIRED_FACTS, DEFAULTS, CARRIED)


def generate(brief, run, root="."):
    """The context specification object. Authors nothing; writes nothing.

    The gate is checked before the intent is even looked for: an open fork
    stops the run whatever else is wrong, and an operator told about a missing
    file when the real problem is an unanswered question fixes the wrong thing.
    """
    run.require_closed()
    upstream = chain.require(root, intent.FILENAME, intent.SLUG,
                             "the context generator")

    block = envelope(brief)
    contexts = list(brief.get("contexts") or ())
    terms = list(brief.get("terms") or ())
    _declared(contexts, terms)

    sections, gaps = [], []

    overview = brief.get("overview")
    if schema.is_empty(overview):
        gaps.append("what this domain is and where its edges are")
    else:
        sections.append({"id": "overview", "type": "prose", "title": "The domain",
                         "body": [overview] if isinstance(overview, str) else list(overview)})

    if contexts:
        sections.append(_context_cards(contexts))
    else:
        gaps.append("which bounded contexts this domain divides into")

    missing, term_gaps = _unsourced(terms, sourced(upstream))
    gaps.extend(term_gaps)
    kept, definitions, meanings, retired, crossings = _resolve(terms, run, missing)

    entries = _numbered([_entry(index, terms, definitions, meanings, retired)
                         for index in kept])
    if entries:
        sections.append(glossary_section(entries))
    else:
        gaps.append("what words this project uses and what they mean")

    rows = _map_rows(contexts, crossings)
    if rows:
        sections.append({"id": "context-map", "type": "table", "title": "Context map",
                         "columns": list(MAP_COLUMNS), "rows": rows})

    sources, source_gaps = chain.register(brief)
    gaps.extend(source_gaps)
    if sources:
        sections.append(chain.register_section(sources))
    else:
        gaps.append("what material this vocabulary was harvested from")

    locked = run.section()
    if locked is not None:
        sections.append(locked)

    trailing = chain.gap_section(gaps, chain.choice(run, "gaps"))
    if trailing is not None:
        sections.append(trailing)

    spec = {"document": block,
            "schemaVersion": schema.SCHEMA_VERSION,
            "sections": sections}
    if sources:
        spec["sources"] = sources
    return spec


def render(spec, root="."):
    """The finished document text, styled with the host project's tokens."""
    return chain.render(spec, SPEC_ID, root)


def write(root, spec):
    """Write the rendered context document into the project."""
    return chain.write(root, FILENAME, spec, SPEC_ID)


def regenerate(root, spec=None):
    """Re-render this document from its own embedded specification (FR-DOC-06)."""
    return chain.regenerate(root, FILENAME, SLUG, SPEC_ID, spec)


def author(root, brief, run):
    """Gate, intent, ledger, document — in that order. Returns (path, spec)."""
    spec = generate(brief, run, root)

    paths.ensure_layout(root)
    run.record(root)
    return write(root, spec), spec


# ------------------------------------------------------- speaking the language

class Glossary:
    """The agreed vocabulary, as every generator downstream consults it."""

    def __init__(self, entries):
        self.entries = tuple(entries)
        self._canonical, self._identifiers, retired = {}, {}, []
        for entry in self.entries:
            word = entry["canonical"]
            self._canonical[_key(word)] = word
            self._identifiers[_key(word)] = entry.get("id")
            for synonym in entry.get("synonyms") or ():
                self._canonical[_key(synonym)] = word
                retired.append((synonym, word))
        # Longest first: a synonym that contains a shorter one must be replaced
        # whole, or the shorter match rewrites its middle and leaves debris.
        self._retired = tuple(sorted(retired, key=lambda pair: (-len(pair[0]), pair[0])))

    def __len__(self):
        return len(self.entries)

    def canonical(self, word):
        """The agreed word for `word`, whether it is canonical or retired."""
        return self._canonical.get(_key(word))

    def knows(self, word):
        return self.canonical(word) is not None

    def identifier(self, word):
        agreed = self.canonical(word)
        return self._identifiers.get(_key(agreed)) if agreed else None

    @property
    def retired(self):
        """Every synonym that should not appear, with the word that replaces it."""
        return self._retired

    def speak(self, text):
        """The same sentence in the agreed words (FR-CTX-05)."""
        for synonym, word in self._retired:
            text = re.sub(r"\b%s\b" % re.escape(synonym), word, text, flags=re.IGNORECASE)
        return text


def glossary(spec):
    """The glossary of an already-generated context document."""
    for section in spec.get("sections") or ():
        if section.get("id") == "glossary":
            return Glossary(section.get("items") or ())
    return Glossary(())


def read(root):
    """The project's agreed vocabulary, or a refusal naming what is missing."""
    return glossary(chain.require(root, FILENAME, SLUG, "a downstream generator"))


def consult(spec, book):
    """The same document, said in the agreed words (FR-CTX-05, US-CTX-03-S01).

    A new object is returned rather than the given one edited: a generator that
    silently rewrote the specification it was handed would make the document a
    caller thought it had built unrecoverable.
    """
    return _spoken(spec, book, False)


def _spoken(node, book, inside):
    if isinstance(node, str):
        return book.speak(node) if inside else node
    if isinstance(node, dict):
        return dict((key, _spoken(value, book, inside or key in SPOKEN))
                    for key, value in node.items())
    if isinstance(node, list):
        return [_spoken(item, book, inside) for item in node]
    return node


def amend(root, word, definition, needed_by):
    """Add a term the glossary lacks (FR-CTX-05, US-CTX-03-S02).

    Forward-only: nothing already defined is renumbered or reworded, and a word
    the glossary already knows — under its own name or as a retired synonym —
    is returned as it stands rather than defined a second time. A downstream
    generator that needs a word calls this and then uses the answer; defining
    it locally is what this exists to prevent.
    """
    spec = chain.require(root, FILENAME, SLUG, "an amendment from %s" % needed_by)
    book = glossary(spec)

    known = book.identifier(word)
    if known is not None:
        return known

    section = None
    for one in spec.get("sections") or ():
        if one.get("id") == "glossary":
            section = one
    if section is None:
        section = glossary_section([])
        spec["sections"].append(section)

    highest = 0
    for entry in section["items"]:
        found = _UL.match(entry.get("id") or "")
        if found:
            highest = max(highest, int(found.group(1)))

    identifier = chain.identifier("UL", highest)
    section["items"].append({"id": identifier, "term": "%s · %s" % (identifier, word),
                             "canonical": word, "definition": definition,
                             "source": "Needed by %s." % needed_by, "amended": True})
    write(root, spec)
    return identifier
