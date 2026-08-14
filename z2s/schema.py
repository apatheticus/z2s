# -*- coding: utf-8 -*-
"""The document contracts, declared once as data.

Every generated document embeds one JSON object, and every other tool in the
method reads it (FR-SPC-01). This module is the agreement that object is held
to: the envelope, the schema version, the identifier grammar, the closed
enumerations, typed traces, and the rule that a section with nothing in it is
absent rather than present and empty.

The declarations are data, not code, so the three things that must agree — the
validator, the legend a reader is shown, and the tests — all read the same
tables. A hand-written legend drifts from the rules it describes silently, and
a reader trusts the legend.

Two properties every check here keeps:

  * it reports everything it finds rather than stopping at the first problem
    (NFR-VAL-01), because a reader who fixes one field and runs again to find
    the next stops running the checker;
  * it never modifies the object it is given. A report that edits its input is
    a mutation nobody asked for.

What is deliberately NOT here: anything that needs more than one document.
Duplicate identifiers and dangling traces are set-wide questions and belong to
the validator (M2-P2), which builds an index across the whole set.

Traces: FR-DOC-08, FR-SPC-01, FR-TRC-01, FR-TRC-03, NFR-DAT-01, NFR-DAT-02,
NFR-DAT-03, NFR-DAT-04, NFR-DAT-06, NFR-DAT-08, NFR-EVO-01, ADR-03.
"""

import collections
import re

#: A single reported problem. `severity` decides the exit status, `code` groups
#: findings of the same rule, `where` locates it, `message` explains it to a
#: person. Severity is a property of the rule; nothing configures it (FR-VAL-06).
Finding = collections.namedtuple("Finding", "severity code where message")

FAILURE = "failure"
WARNING = "warning"

#: The method-wide schema version. A major change invalidates existing readers;
#: a minor one does not (NFR-EVO-01). The ten published documents carry "1.0".
SCHEMA_VERSION = "1.0"

#: The envelope, present in every specification object whatever its type.
REQUIRED_TOP_LEVEL = ("document", "schemaVersion", "sections")
REQUIRED_DOCUMENT_FIELDS = ("title", "slug", "type", "version", "status", "date", "owner")
OPTIONAL_DOCUMENT_FIELDS = ("releaseScope", "summary", "scopeNote")

#: What each document type adds to the envelope. A type never repeats an
#: envelope field — the two could then disagree about whether it is required.
#: A type this method does not know still owes the envelope and nothing more:
#: the toolchain runs on other people's projects, which invent their own.
DOCUMENT_TYPES = {
    "vision": (),
    "context": (),
    "prd": (),
    "fsd": (),
    "stories": (),
    "sdd": (),
    "plan": ("legend", "catalog"),
}

#: The closed enumerations (NFR-DAT-04), declared once here and rendered into a
#: reader's legend by legend() below.
ENUMS = {
    "priorities": (
        {"id": "Must", "label": "Must", "desc": "Without it the release does not ship."},
        {"id": "Should", "label": "Should", "desc": "Important; a release can ship without it."},
        {"id": "Could", "label": "Could", "desc": "Desirable if the work is cheap."},
        {"id": "Won't", "label": "Won't", "desc": "Explicitly out of scope for this release."},
    ),
    "statuses": (
        {"id": "not-started", "label": "Not started",
         "desc": "No work begun. Eligible once every dependency is passing."},
        {"id": "in-progress", "label": "In progress",
         "desc": "Actively being worked; red, green, refactor under way."},
        {"id": "passing", "label": "Passing",
         "desc": "Every named verification layer actually ran and passed in this run."},
        {"id": "failing", "label": "Failing", "desc": "Attempted; one or more gates are red."},
        {"id": "blocked", "label": "Blocked",
         "desc": "A dependency is not passing, a prerequisite is missing, or retries were exhausted."},
        {"id": "needs-review", "label": "Needs review",
         "desc": "Machine gates pass; a human-review criterion is outstanding."},
    ),
    "autonomy": (
        {"id": "auto", "label": "Autonomous",
         "desc": "Runs unattended — code and tests only, no external provider."},
        {"id": "auto-with-mock", "label": "Autonomous, substituted",
         "desc": "Runs unattended only against the substitution the task names."},
        {"id": "human-gate", "label": "Human gate",
         "desc": "Requires a person: a credential, a paid provider, or a judgement call."},
    ),
    "criterionKinds": (
        {"id": "auto", "label": "Automated", "desc": "Machine-checkable without a human."},
        {"id": "human-review", "label": "Human review",
         "desc": "Subjective; must be signed off before the milestone closes."},
    ),
    "decisionStatuses": (
        {"id": "Proposed", "label": "Proposed", "desc": "Written down; not yet agreed."},
        {"id": "Accepted", "label": "Accepted", "desc": "Agreed and in force."},
        {"id": "Superseded", "label": "Superseded",
         "desc": "Replaced by a later decision, which names it."},
        {"id": "Rejected", "label": "Rejected",
         "desc": "Considered and turned down; kept so the reasoning survives."},
    ),
    "testLayers": (
        {"id": "unit", "label": "Unit"},
        {"id": "integration", "label": "Integration"},
        {"id": "e2e", "label": "End-to-end"},
        {"id": "a11y", "label": "Accessibility"},
        {"id": "perf", "label": "Performance"},
        {"id": "lint", "label": "Static analysis"},
        {"id": "CI", "label": "CI gate"},
        {"id": "manual", "label": "Human review"},
    ),
}

#: Which field carries which enumeration, wherever it appears. A list value has
#: every element checked, so `testLayers` needs no separate machinery.
#:
#: `kind` is the one overloaded name here, and it reaches every identified entry.
#: A measure carrying `kind: "Outcome"` would be checked against criterionKinds
#: and rejected — which is why the PRD generator states a measure's kind in its
#: body rather than as a field. Constraining measure kinds is a separate decision
#: (a closed set of its own in ENUM_FIELDS_BY_KIND), not something to reach by
#: accident.
ENUM_FIELDS = {
    "priority": "priorities",
    "autonomy": "autonomy",
    "kind": "criterionKinds",
    "testLayers": "testLayers",
}

#: `status` means three different things in this method, and only the thing
#: carrying it says which: on a plan entry it is the run state, on a decision it
#: is the decision's standing, and on the document itself it is editorial
#: ("Draft for review"). One shared set would reject every accepted decision.
#: The envelope carries no identifier, so it is never reached by these at all.
ENUM_FIELDS_BY_KIND = {
    "plan": {"status": "statuses"},
    "decision": {"status": "decisionStatuses"},
}

#: The identifier grammar (NFR-DAT-03), by kind. An identifier is recognised by
#: its leading prefix and then must match one of its kind's shapes.
#:
#: The area key of a group ("FR-DOC") is an identifier in its own right — it is
#: what an entry's `area` field and the document's `links` map point at — so it
#: is listed beside the entry shape rather than treated as a malformed entry.
GRAMMAR = {
    "requirement": (r"^(?:FR|NFR)-[A-Z]{2,4}$",
                    r"^(?:FR|NFR)-[A-Z]{2,4}-\d{2}$"),
    "story": (r"^US-[A-Z]{2,4}$",
              r"^US-[A-Z]{2,4}-\d{2}$",
              r"^US-[A-Z]{2,4}-\d{2}-S\d{2}$"),
    "decision": (r"^ADR-\d{2}$",),
    "usecase": (r"^UC-\d{2}$",),
    "context": (r"^BC-\d{2}$",),
    "term": (r"^UL-\d{2}$",),
    "prerequisite": (r"^PRE-\d{2}$",),
    "capability": (r"^VC-\d{2}$",),
    "statement": (r"^VS-\d{2}$",),
    "goal": (r"^G-\d{2}$",),
    "journey": (r"^J-\d{2}$",),
    "nongoal": (r"^NG-\d{2}$",),
    "measure": (r"^MT-\d{2}$",),
    "risk": (r"^RK-\d{2}$",),
    "plan": (r"^M\d+$", r"^M\d+-P\d+$", r"^M\d+-P\d+-T\d+$", r"^M\d+-P\d+-T\d+-C\d+$"),
}

#: Prefix to kind. A string whose prefix is not here is not an identifier and is
#: not grammar-checked: the key `id` is overloaded across the method, carrying
#: section keys ("purpose") and enumeration values ("Must") as well.
#:
#: Being absent from here is not a lighter contract, it is no contract at all —
#: the validator's set-wide index skips anything this map does not recognise, so
#: an unregistered prefix is neither grammar-checked nor duplicate-checked, and a
#: trace to it reads as dangling. Every prefix a generator assigns belongs here.
PREFIXES = {
    "FR": "requirement", "NFR": "requirement", "US": "story", "ADR": "decision",
    "UC": "usecase", "BC": "context", "UL": "term", "PRE": "prerequisite",
    "VC": "capability", "VS": "statement", "G": "goal", "J": "journey",
    "NG": "nongoal", "MT": "measure", "RK": "risk",
}

#: The kinds of upstream reference a trace map may key by (NFR-DAT-08). The
#: chain starts above the requirements: a capability and a goal are traced to
#: from the PRD and the FSD, so both are kinds rather than loose keys.
TRACE_KINDS = ("cap", "goal", "fr", "nfr", "adr", "us", "uc", "bc")

#: Named products and platforms, which a functional requirement does not get to
#: choose (FR-DOC-05). A functional document says what must be observable; which
#: product delivers it is the technical document's decision, and a functional
#: requirement that has already made it silently closes that decision.
#:
#: Products only, deliberately. The wider reading — flagging "cache", "database",
#: "endpoint" — catches more implementation detail and also catches a great deal
#: of honest functional wording, and every false alarm turns a real requirement
#: into an open question nobody asked for (M4-02).
#:
#: Names short enough to appear inside ordinary words, or to be ordinary words
#: themselves, are left out: matching "Go" or "Spring" costs more than it finds.
TECHNOLOGY_NAMES = (
    "SQLite", "PostgreSQL", "Postgres", "MySQL", "MongoDB", "DynamoDB", "Redis",
    "Elasticsearch", "Kafka", "RabbitMQ", "GraphQL", "Firebase", "Supabase",
    "React", "Vue", "Angular", "Svelte", "Next.js", "Node.js", "jQuery",
    "Tailwind", "Bootstrap", "Django", "Flask", "Rails", "Laravel",
    "Docker", "Kubernetes", "Terraform", "Nginx", "Apache", "Jenkins",
    "AWS", "Azure", "GCP", "Cloudflare", "Vercel", "Netlify", "Heroku",
    "Python", "JavaScript", "TypeScript", "Ruby", "Kotlin", "Swift",
)

#: The fields of a requirement a reader reads, and therefore the fields the
#: boundary rule has to look at. A technology named in a note is named.
BOUNDARY_FIELDS = ("title", "text", "notes")

#: File suffixes that make a word a filename rather than a sentence. Listed
#: rather than matched loosely, because "e.g" and "i.e" end in letters too.
INTERNAL_SUFFIXES = ("py", "js", "ts", "tsx", "jsx", "json", "html", "css",
                     "md", "sh", "yml", "yaml", "toml", "ini", "cfg", "sql")

#: What makes a word code rather than English (FR-GEN-05, NFR-UX-06). Three
#: shapes, each of which is unambiguous on its own:
#:
#:   * a word joined by underscores — `open_gate`
#:   * a dotted name being called — `chain.require(`
#:   * a filename — `runtime.js`
#:
#: Code shapes only, deliberately (M5-07). The wider reading — every capitalised
#: term the glossary does not define — catches real jargon and also catches a
#: great deal of honest prose, and a check that cries wolf is a check authors
#: switch off. A term this misses is still caught by a reader; a term this
#: invents costs a good sentence.
_INTERNAL = re.compile(
    r"(?<![\w.])(?:"
    r"[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+"
    r"|[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+(?=\s*\()"
    r"|[\w-]+\.(?:%s)"
    r")(?![\w])" % "|".join(INTERNAL_SUFFIXES))

#: Where a reader actually reads. A field not listed here holds a value — an
#: identifier, an area key, a priority band — and a value is not prose.
PROSE_FIELDS = ("title", "text", "notes", "summary", "lede", "intro", "desc",
                "body", "term", "definition", "narrative", "role",
                "given", "when", "then",
                "actor", "goal", "trigger", "pre", "main", "alt", "exc", "post",
                "items", "verify")

#: Section types whose content is quoted material rather than prose. A sample
#: of a specification object is meant to name files and call functions; that is
#: what a sample is.
QUOTED_TYPES = ("code",)

#: The document type the boundary applies to. A technical document names
#: technologies for a living; that is what it is for.
FUNCTIONAL_SLUG = "fsd"

#: Fields whose emptiness is meaningful. `dependsOn: []` states that a task
#: depends on nothing; omitting it would make "nothing" and "not stated" the
#: same answer.
MAY_BE_EMPTY = ("dependsOn",)

#: The fields that hold what a reader actually reads. Blank in one of these is
#: a heading over nothing, which is what NFR-DAT-06 forbids. A blank anywhere
#: else — a table's first column heading, a status with no colour — is a value.
CONTENT_KEYS = ("body", "text", "title")

_PLAN_PREFIX = re.compile(r"^M\d+(?:-|$)")
_VERSION = re.compile(r"^(\d+)\.(\d+)$")


# --------------------------------------------------------------- primitives

def is_empty(value):
    """The one emptiness rule, shared by the schema and the renderer.

    False and 0 are values, not absences — `done: false` is the commonest value
    in a plan document, and treating it as empty would erase every unfinished
    criterion.
    """
    if value is None:
        return True
    if isinstance(value, bool) or isinstance(value, (int, float)):
        return False
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) == 0
    return False


def kind_of(identifier):
    """The kind an identifier belongs to, or None if it is not an identifier."""
    if not isinstance(identifier, str) or not identifier:
        return None
    if _PLAN_PREFIX.match(identifier):
        return "plan"
    return PREFIXES.get(identifier.split("-", 1)[0])


def legend():
    """The reader-facing legend, generated from the same tables the checks use."""
    return {name: [dict(value) for value in values] for name, values in ENUMS.items()}


def entries(node, path="spec"):
    """Every dictionary in the object, with a readable path to it.

    Public because the validator walks the same object to build its set-wide
    identifier index, and two different walks would disagree about what counts
    as an entry.
    """
    if isinstance(node, dict):
        yield path, node
        for key in sorted(node):
            for found in entries(node[key], "%s.%s" % (path, key)):
                yield found
    elif isinstance(node, list):
        for index, item in enumerate(node):
            for found in entries(item, "%s[%d]" % (path, index)):
                yield found


def _named(entry, path):
    """What to call a place in a report: its identifier if it has one."""
    identifier = entry.get("id")
    if isinstance(identifier, str) and identifier:
        return identifier
    return path


# ------------------------------------------------------------------ envelope

def check_envelope(spec):
    """The fields every document carries, whatever its type (FR-DOC-08)."""
    if not isinstance(spec, dict):
        return [Finding(FAILURE, "envelope", "spec",
                        "the specification is not a JSON object")]

    found = []
    for name in REQUIRED_TOP_LEVEL:
        if is_empty(spec.get(name)):
            found.append(Finding(FAILURE, "envelope", "spec",
                                 "the specification has no %s" % name))

    document = spec.get("document")
    if isinstance(document, dict):
        for name in REQUIRED_DOCUMENT_FIELDS:
            if is_empty(document.get(name)):
                found.append(Finding(FAILURE, "envelope", "spec.document",
                                     "the document block has no %s" % name))
    return found


def check_version(version, source):
    """Compare a document's schema version with this toolchain's (NFR-EVO-01).

    A major difference means the reader does not understand the document, and
    guessing at the difference is worse than refusing. A minor one is reported
    and reading continues.
    """
    match = _VERSION.match(version or "")
    if not match:
        return [Finding(FAILURE, "schema-version", source,
                        "%s: schema version %r cannot be read; expected <major>.<minor>"
                        % (source, version))]

    ours = _VERSION.match(SCHEMA_VERSION)
    if match.group(1) != ours.group(1):
        return [Finding(FAILURE, "schema-version", source,
                        "%s: schema %s cannot be read by this tool, which speaks %s"
                        % (source, version, SCHEMA_VERSION))]
    if match.group(2) != ours.group(2):
        return [Finding(WARNING, "schema-version", source,
                        "%s: schema %s differs in its minor version from this tool's %s; "
                        "reading continues" % (source, version, SCHEMA_VERSION))]
    return []


def check_document(spec):
    """The envelope plus whatever this document's type adds to it."""
    found = check_envelope(spec)
    document = spec.get("document") if isinstance(spec, dict) else None
    slug = document.get("slug") if isinstance(document, dict) else None
    for name in DOCUMENT_TYPES.get(slug, ()):
        if is_empty(spec.get(name)):
            found.append(Finding(FAILURE, "document-type", "spec",
                                 "a %s document has no %s" % (slug, name)))
    return found


# ---------------------------------------------------------------- identifiers

def check_identifier(identifier):
    """One identifier against its kind's shape (NFR-DAT-03)."""
    kind = kind_of(identifier)
    if kind is None:
        return []
    for pattern in GRAMMAR[kind]:
        if re.match(pattern, identifier):
            return []
    return [Finding(FAILURE, "identifier-grammar", identifier,
                    "%r is not a well-formed %s identifier; expected %s"
                    % (identifier, kind, " or ".join(GRAMMAR[kind])))]


def check_identifiers(spec):
    """Every identifier in the object, wherever it is nested."""
    found = []
    for _, entry in entries(spec):
        found.extend(check_identifier(entry.get("id")))
    return found


# --------------------------------------------------------------- enumerations

def check_enumerations(spec):
    """Closed sets, checked only on entries that carry an identifier."""
    found = []
    for path, entry in entries(spec):
        kind = kind_of(entry.get("id"))
        if kind is None:
            continue
        fields = dict(ENUM_FIELDS)
        fields.update(ENUM_FIELDS_BY_KIND.get(kind, {}))
        for field, name in sorted(fields.items()):
            if field not in entry:
                continue
            allowed = [value["id"] for value in ENUMS[name]]
            value = entry[field]
            for one in (value if isinstance(value, list) else [value]):
                if one not in allowed:
                    found.append(Finding(
                        FAILURE, "enumeration", _named(entry, path),
                        "%s: %s %r is outside the closed set (%s)"
                        % (_named(entry, path), field, one, ", ".join(allowed))))
    return found


# --------------------------------------------------------------------- traces

def check_traces(spec):
    """Traces are a map keyed by upstream kind, never a flat list (NFR-DAT-08).

    A flat list puts the consumer back to reading identifier prefixes to tell a
    functional trace from a technical one, which is the thing typing prevents.
    """
    found = []
    for path, entry in entries(spec):
        if "traces" not in entry:
            continue
        where = _named(entry, path)
        traces = entry["traces"]
        if not isinstance(traces, dict):
            found.append(Finding(FAILURE, "trace-shape", where,
                                 "%s: traces must be a map keyed by upstream kind (%s), "
                                 "not a %s" % (where, ", ".join(TRACE_KINDS),
                                               type(traces).__name__)))
            continue
        for key in sorted(traces):
            if key not in TRACE_KINDS:
                found.append(Finding(FAILURE, "trace-shape", where,
                                     "%s: %r is not a trace kind (%s)"
                                     % (where, key, ", ".join(TRACE_KINDS))))
            elif not isinstance(traces[key], list) or \
                    not all(isinstance(one, str) for one in traces[key]):
                found.append(Finding(FAILURE, "trace-shape", where,
                                     "%s: traces.%s must be a list of identifiers"
                                     % (where, key)))
    return found


# ----------------------------------------------------- the functional boundary

def _boundary_pattern(names):
    """One expression over every prohibited name, whole words only.

    Whole words matter more than it looks: "reactionary" contains "React", and a
    validator that refuses a requirement for a word inside another word is a
    validator authors learn to ignore.
    """
    return re.compile(r"(?<![\w.])(?:%s)(?![\w])"
                      % "|".join(re.escape(name) for name in names), re.IGNORECASE)


def names_technology(text, names=TECHNOLOGY_NAMES):
    """Every prohibited product name this wording uses, in the order it uses them."""
    if not isinstance(text, str) or not text:
        return []
    found, seen = [], set()
    for match in _boundary_pattern(names).finditer(text):
        canonical = match.group(0)
        if canonical.lower() not in seen:
            seen.add(canonical.lower())
            found.append(canonical)
    return found


def check_boundary(spec, names=TECHNOLOGY_NAMES):
    """A functional document names no technology (FR-DOC-05, M4-P1-T2-C1).

    Enforced here as well as at authoring because a document is edited after it
    is generated: the specification embedded in it is the source, and an editor
    reaching for a product name has no generator in the way.
    """
    document = spec.get("document") if isinstance(spec, dict) else None
    slug = document.get("slug") if isinstance(document, dict) else None
    if slug != FUNCTIONAL_SLUG:
        return []

    found = []
    for path, entry in entries(spec):
        if kind_of(entry.get("id")) != "requirement":
            continue
        for field in BOUNDARY_FIELDS:
            for name in names_technology(entry.get(field), names):
                found.append(Finding(
                    FAILURE, "functional-boundary", _named(entry, path),
                    "%s: %s names %s; a functional requirement states observable "
                    "behaviour, and the technology that delivers it belongs in the "
                    "technical specification"
                    % (_named(entry, path), field, name)))
    return found


# ------------------------------------------------------------- plain language

def names_internals(text, allowed=()):
    """Every code-shaped word this wording uses, in the order it uses them.

    Public for the same reason `names_technology` is: the rule is worth checking
    outside the validator too, and a second expression written somewhere else
    would be a second definition of what counts as jargon.
    """
    if not isinstance(text, str) or not text:
        return []
    silenced = {name.lower() for name in allowed}
    found, seen = [], set()
    for match in _INTERNAL.finditer(text):
        word = match.group(0)
        if word.lower() in silenced or word.lower() in seen:
            continue
        seen.add(word.lower())
        found.append(word)
    return found


def _prose(node, path="spec"):
    """Every reader-facing string in the object, with where it was found.

    Walks by field name rather than by taking every string: a document is full
    of strings that are values — an identifier, a priority band, a column
    heading — and a rule about how prose reads has nothing to say about those.
    """
    if isinstance(node, dict):
        if node.get("type") in QUOTED_TYPES:
            return
        for key in sorted(node):
            value = node[key]
            if key in PROSE_FIELDS:
                if isinstance(value, str):
                    yield path, key, value
                elif isinstance(value, list):
                    for index, item in enumerate(value):
                        if isinstance(item, str):
                            yield "%s.%s[%d]" % (path, key, index), key, item
            for found in _prose(value, "%s.%s" % (path, key)):
                yield found
    elif isinstance(node, list):
        for index, item in enumerate(node):
            for found in _prose(item, "%s[%d]" % (path, index)):
                yield found


def _mentions(count):
    return "" if count < 2 else "; named in %d places" % count


def check_plain_language(spec, allowed=(), names=TECHNOLOGY_NAMES):
    """Reader-facing prose names nothing only an insider can follow.

    A warning, never a failure (M5-08). Plain language is a Should in both
    documents that ask for it (FR-GEN-05, NFR-UX-06), and a Should that turns a
    build red is a Should being enforced as a Must by the back door — which
    FR-VAL-06 exists to prevent.

    Reported once per term, at the first place it appears, with a count of how
    many other places name it. Every occurrence of `runtime.js` in a document
    about generating documents is the same decision, and reporting it forty
    times buries the thirty-nine other terms.
    """
    silenced = {name.lower() for name in allowed}
    first, tally = collections.OrderedDict(), collections.Counter()
    for where, field, value in _prose(spec):
        found = names_internals(value, allowed) + [
            name for name in names_technology(value, names)
            if name.lower() not in silenced]
        for word in found:
            key = word.lower()
            tally[key] += 1
            first.setdefault(key, (word, where, field))

    return [Finding(WARNING, "plain-language", where,
                    "%s: %s names %s, which a reader outside the specialism cannot "
                    "follow; say it in words, or define it where it first appears%s"
                    % (where, field, word, _mentions(tally[key])))
            for key, (word, where, field) in first.items()]


# ------------------------------------------------------------------ emptiness

def _is_container(value):
    return isinstance(value, (list, tuple, dict, set))


def check_emptiness(spec, path="spec"):
    """A section with no content is absent, not present and empty (NFR-DAT-06).

    An empty container renders as a heading with nothing under it, which reads
    to a reviewer as an unanswered question rather than as an absent one. A
    blank string is only reported where it is content — a table's first column
    heading is deliberately blank, and reporting it made this rule fire on
    documents that were correct.
    """
    found = []
    if isinstance(spec, dict):
        for key in sorted(spec):
            value = spec[key]
            if key in MAY_BE_EMPTY:
                continue
            reportable = _is_container(value) or value is None or key in CONTENT_KEYS
            if is_empty(value) and reportable:
                found.append(Finding(FAILURE, "empty-section", path,
                                     "%s.%s is present but empty; omit it instead"
                                     % (path, key)))
            else:
                found.extend(check_emptiness(value, "%s.%s" % (path, key)))
    elif isinstance(spec, list):
        for index, item in enumerate(spec):
            where = "%s[%d]" % (path, index)
            if is_empty(item) and (_is_container(item) or item is None):
                found.append(Finding(FAILURE, "empty-section", path,
                                     "%s is present but empty; omit it instead" % where))
            else:
                found.extend(check_emptiness(item, where))
    return found
