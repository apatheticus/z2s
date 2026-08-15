# -*- coding: utf-8 -*-
"""The narrative briefing — the document for the reader who reads no others.

Most people who need to know what a thing does will never open a functional
specification, and a specification written so that they would is a specification
that has stopped being precise. So the method produces both: the documents that
bind the build, and one narrative reading of them for everybody else.

Two properties make it worth GENERATING rather than writing (FR-DOC-09):

* **It is derived.** Every line came from a document above it. Change a
  capability, add an exclusion, take a decision, and the briefing says so on the
  next run. A briefing typed by hand is accurate the week it is written and
  quietly wrong afterwards — which is worse than having none, because it is
  believed (M12-P3-T1-C1).
* **It is layered.** Plain language first, technical depth last, so a reader
  stops where their interest stops rather than at the first word they do not
  know (FR-GEN-05, NFR-UX-06). The order of `LAYERS` is that promise.

It defines no identifier of its own and it is not part of the coverage universe.
It is a reading of the set, not a member of it — nothing traces to a briefing,
and nothing should.

The brief is three facts, because everything else is read from the documents:

    {"title": ..., "owner": ..., "date": "2026-08-15",
     "summary": ...}                                       # optional

Traces: FR-DOC-09, FR-DOC-06, FR-DOC-08, FR-GEN-05, NFR-UX-06, NFR-ARC-01,
NFR-GEN-01, US-DOC-01.
"""

import collections

from z2s import chain, context, fsd, gate, paths, prd, schema, sdd, vision

SLUG = "briefing"
TYPE = "Narrative briefing"
FILENAME = "Briefing.html"
SPEC_ID = SLUG + "-spec"

REQUIRED_FACTS = ("title", "owner", "date")
DEFAULTS = {"version": "1.0", "status": "Derived from the document set"}
CARRIED = ("summary", "scopeNote", "releaseScope")

#: The documents this reads, and the slug each must actually be. Read in this
#: order, so a set missing its vision is told about the vision first.
ABOVE = ((vision.FILENAME, vision.SLUG),
         (prd.FILENAME, prd.SLUG),
         (fsd.FILENAME, fsd.SLUG),
         (sdd.FILENAME, sdd.SLUG),
         (context.FILENAME, context.SLUG))

#: Section identifiers, named rather than spelled at each use so the layering
#: test and the builder read one set.
SHORTLY = "shortly"
FOR_WHOM = "for-whom"
DOES = "does"
EXCLUSIONS = "not-doing"
BUILT = "built"

Layer = collections.namedtuple("Layer", "id title lede")

#: The layers, in the order a reader meets them: what it is, who it is for, what
#: it does, what it deliberately does not do, and only then how it is built.
#: The order IS the requirement — a briefing that opens with its architecture
#: has answered the question its reader asked last (NFR-UX-06).
LAYERS = (
    Layer(SHORTLY, "In short",
          "The whole of it in a paragraph, for somebody who will read no "
          "further."),
    Layer(FOR_WHOM, "Who it is for, and what changes for them",
          "The people this is being built for, and what each of them gets."),
    Layer(DOES, "What it does",
          "Every capability the specification requires, grouped the way the "
          "specification groups them."),
    Layer(EXCLUSIONS, "What it deliberately does not do",
          "Decisions, not omissions. Each one carries the argument that "
          "settled it, so it is not re-argued by default."),
    Layer(BUILT, "How it is put together",
          "The shape of the thing and the decisions that shaped it. The last "
          "layer, and the only one a reader can safely skip."),
)

IncompleteBrief = chain.IncompleteBrief
MissingPrerequisite = chain.MissingPrerequisite


def forks(brief):
    """None. Every word in this document is read from another one.

    A fork is a question only the owner can answer. This generator asks nothing,
    because it invents nothing — so the gate closes the moment it opens, and it
    still runs, because a document authored outside the gate would be a document
    with no locked-decisions record behind it.
    """
    return ()


def open_gate(brief, root=None):
    """The gate this generator runs, over whatever is already known."""
    decisions = gate.load(root, SLUG) if root is not None else ()
    return gate.Gate(SLUG, forks(brief), source=brief, decisions=decisions)


# -------------------------------------------------------------- reading the set

def _sections(spec):
    return collections.OrderedDict(
        (one["id"], one) for one in spec.get("sections") or ()
        if isinstance(one, dict) and one.get("id"))


def _prose(spec, section_id):
    """The paragraphs of a prose section, or an empty list."""
    found = _sections(spec).get(section_id) or {}
    body = found.get("body")
    if isinstance(body, str):
        return [body]
    return [one for one in body or () if isinstance(one, str)]


def _items(spec, section_id):
    found = _sections(spec).get(section_id) or {}
    return [one for one in found.get("items") or () if isinstance(one, dict)]


def _rows(spec, section_id):
    found = _sections(spec).get(section_id) or {}
    return [list(one) for one in found.get("rows") or ()]


def _catalogue(spec, section_id):
    """One catalogue's entries, in document order."""
    found = _sections(spec).get(section_id) or {}
    if found.get("type") != "requirements":
        return []
    return [one for one in found.get("items") or () if isinstance(one, dict)]


def _area_names(spec, section_id):
    found = _sections(spec).get(section_id) or {}
    return collections.OrderedDict(
        (one["key"], one.get("name") or one["key"])
        for one in found.get("areas") or () if isinstance(one, dict))


# ---------------------------------------------------------------- the layers

def shortly(seen):
    """What this is, in the words the vision already used."""
    said = _prose(seen[vision.SLUG], "statement") \
        or _prose(seen[vision.SLUG], "problem")
    summary = (seen[vision.SLUG].get("document") or {}).get("summary")
    if not said and summary:
        said = [summary]
    return {"body": said}


def for_whom(seen):
    """Who has a stake, and what each of them needs."""
    stakeholders = _rows(seen[vision.SLUG], "stakeholders")
    goals = _items(seen[prd.SLUG], "goals")
    items = ["%s — %s" % (row[0], row[-1]) for row in stakeholders if row]
    items.extend("%s %s" % (one.get("id", ""), one.get("text") or one.get("term") or "")
                 for one in goals)
    return {"items": [one.strip() for one in items if one.strip()]}


def does(seen):
    """Every capability the specification requires, grouped as it groups them."""
    names = _area_names(seen[fsd.SLUG], "requirements")
    grouped = collections.OrderedDict((key, []) for key in names)
    for entry in _catalogue(seen[fsd.SLUG], "requirements"):
        if entry.get("priority") == fsd.EXCLUDED:
            continue
        grouped.setdefault(entry.get("area") or "", []).append(entry)
    items = []
    for key, entries in grouped.items():
        if not entries:
            continue
        items.append({"term": names.get(key, key),
                      "definition": "; ".join(one.get("title", "")
                                              for one in entries)})
    return {"items": items}


def not_doing(seen):
    """The deliberate exclusions, each with the argument that settled it."""
    items = []
    for entry in _catalogue(seen[fsd.SLUG], "requirements"):
        if entry.get("priority") != fsd.EXCLUDED:
            continue
        items.append({"term": entry.get("title", ""),
                      "definition": entry.get("notes") or ""})
    return {"items": items}


def built(seen):
    """The shape of the thing, and the decisions that shaped it."""
    items = [{"term": one.get("term") or one.get("title", ""),
              "definition": one.get("definition") or one.get("text", "")}
             for one in _items(seen[sdd.SLUG], "principles")]
    items.extend({"term": one.get("title", ""),
                  "definition": one.get("decision") or one.get("text") or ""}
                 for one in _catalogue(seen[sdd.SLUG], "decisions"))
    return {"items": items}


#: Which builder fills which layer. Data rather than a chain of conditions, so a
#: sixth layer is one entry here and one entry in LAYERS, and a layer with no
#: builder is a failure at import rather than a silently empty section.
BUILDERS = {SHORTLY: shortly, FOR_WHOM: for_whom, DOES: does,
            EXCLUSIONS: not_doing, BUILT: built}

#: What each layer renders as. A paragraph is prose; everything else is a pair
#: of a name and what it means, which is what `definitions` is for.
TYPES = {SHORTLY: "prose", FOR_WHOM: "list"}


# ------------------------------------------------------------------ generation

def envelope(brief):
    """The document block, from facts only (FR-DOC-08)."""
    return chain.envelope(brief, SLUG, TYPE, REQUIRED_FACTS, DEFAULTS, CARRIED)


def _register(seen):
    """The set this briefing was read from, as the source register (FR-DOC-10).

    Every source is a document, and every one is named. A derived document that
    did not say what it was derived from would be indistinguishable from one
    somebody wrote by hand and called derived.
    """
    return [{"kind": "document", "name": filename,
             "origin": paths.SPECS_DIR,
             "contributed": (seen[slug].get("document") or {}).get("type") or slug}
            for filename, slug in ABOVE]


def generate(brief, run, root="."):
    """The briefing specification object. Writes nothing.

    Refuses before it reads anything if the gate is open, and before it builds
    anything if a document it summarises is missing — a briefing assembled from
    half a set is a briefing that is wrong about the half it could not see.
    """
    run.require_closed()
    seen = collections.OrderedDict(
        (slug, chain.require(root, filename, slug, "the briefing generator"))
        for filename, slug in ABOVE)

    block = envelope(brief)
    sections = []
    for layer in LAYERS:
        built_layer = BUILDERS[layer.id](seen)
        if not any(built_layer.values()):
            continue
        section = {"id": layer.id, "type": TYPES.get(layer.id, "definitions"),
                   "title": layer.title, "lede": layer.lede}
        section.update(built_layer)
        sections.append(section)

    sources = _register(seen)
    sections.append(chain.register_section(sources))

    locked = run.section()
    if locked is not None:
        sections.append(locked)

    spec = {"document": block,
            "schemaVersion": schema.SCHEMA_VERSION,
            "sections": sections,
            "sources": sources}

    # Said in this project's own words last, one pass, exactly as every other
    # generator does it (FR-CTX-05).
    return context.consult(spec, context.glossary(seen[context.SLUG]))


def render(spec, root="."):
    """The finished document text, styled with the host project's tokens."""
    return chain.render(spec, SPEC_ID, root)


def write(root, spec):
    """Write the rendered briefing into the project."""
    return chain.write(root, FILENAME, spec, SPEC_ID)


def regenerate(root, spec=None):
    """Re-render this document from its own embedded specification (FR-DOC-06)."""
    return chain.regenerate(root, FILENAME, SLUG, SPEC_ID, spec)


def author(root, brief, run):
    """Gate, chain, ledger, document — in that order. Returns (path, spec)."""
    spec = generate(brief, run, root)

    paths.ensure_layout(root)
    run.record(root)
    return write(root, spec), spec
