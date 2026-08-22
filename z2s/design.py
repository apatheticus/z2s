# -*- coding: utf-8 -*-
"""Reading a host project's design system, and refusing what must not be written.

A generated document inlines values read from files this method does not own,
straight into a <style> block, in a file people open from disk. That is a trust
boundary, and it had no control on it: a value of `#fff}</style><script>...`
executed, and a value of `url(https://...)` fetched, in every document generated
from that project.

**Escaping is not available here.** There is no html.escape for a CSS
declaration value: `}` cannot be escaped and still end a declaration, and `url(`
cannot be escaped at all. So the control is refusal at reading rather than
escaping at writing — the value never enters the pipeline, instead of entering it
disguised. NFR-GEN-05 is amended to say so, because a requirement that says
"escape it" would be asking for something the language cannot give.

Refused, never stripped. A stripped value is one nobody wrote and nobody can
review: it renders, so it looks adopted, and it is not what the host's design
system says. A refusal falls back to the neutral value for that token and is
named in the run report and in the record, so the operator can see the file, the
name and the reason and fix the source.

Two stated ceilings:

  * The grammars below accept more than each token strictly allows. They are
    written to keep hostile *shapes* out, not to be a CSS parser — a length that
    is nonsense but harmless renders as nothing and is a design bug, while a
    length that closes the style block is a security bug. Only the second is
    this module's job.
  * A host value that references a variable is accepted only when the variable
    is one of ours. An unresolved reference to the host's own name would point
    at a variable the document does not carry, which renders as nothing.

Traces: NFR-GEN-05, NFR-SEC-01, FR-GEN-02, FR-GEN-03, ADR-16.
"""

import collections
import hashlib
import json
import os
import re

from . import paths, tokens, writer

#: A file is a design system only if it declares at least this many of the
#: tokens the contract asks for. One stray custom property in an ordinary
#: stylesheet is not a design system.
THRESHOLD = 4

#: And more than that to FILL a system somebody else is the base of. A fill
#: source is contributing values into a palette it did not set, so a wrong guess
#: there is the failure that costs most: a document that looks like a broken
#: version of the product reads worse than a neutral one. A file the operator
#: named is exempt — they pointed at it, which is the strongest signal there is.
FILL_THRESHOLD = 6

#: Directories never searched. Vendored copies of somebody else's design system
#: are not this project's design system.
SKIP = frozenset((".git", "node_modules", "vendor", "dist", "build", "__pycache__",
                  ".venv", "venv", ".zero", ".claude"))

#: Long enough for the longest legitimate value anyone writes — a font stack
#: with six fallbacks, or a two-layer shadow — and short enough that a payload
#: has nowhere to hide.
MAX_LENGTH = 200

#: Refused in any token, whatever its type. Two families: characters that can
#: leave the declaration, the block or the style element, and functions that
#: reach the network or the parser. Matched against the lowered value, so a
#: capitalised URL( is not a way through.
FORBIDDEN = (
    # Leaving the declaration, the rule or the element.
    "<", ">", ";", "{", "}", "@",
    # A CSS escape can encode any of the above, so the escape itself goes.
    "\\",
    # A comment can hide the rest of a line from a reviewer reading the file.
    "/*", "*/",
    # Anything that fetches. A document that beacons when opened is a document
    # that tells somebody else who reviewed it and when.
    "url(", "image-set(", "expression(",
)

#: What a value of each kind may be built from. Deliberately a character class
#: plus a shape rather than a grammar: the question being asked is "could this
#: escape", not "is this valid CSS".
SHAPES = {
    "colour": re.compile(
        r"^(#[0-9a-f]{3,8}"
        r"|(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix)\([^()]*\)"
        r"|[a-z]+)$", re.I),
    "length": re.compile(
        r"^(0"
        r"|-?\d*\.?\d+(?:px|rem|em|ch|ex|cap|ic|lh|rlh|pt|pc|in|cm|mm|q|%"
        r"|vw|vh|vmin|vmax|svw|svh|lvw|lvh|dvw|dvh)"
        r"|(?:calc|clamp|min|max)\([^()]*(?:\([^()]*\))?[^()]*\))$", re.I),
    "number": re.compile(r"^(-?\d*\.?\d+|normal|bold|bolder|lighter)$", re.I),
    "family": re.compile(r'^[\w\s,.\'"()-]+$'),
    "shadow": re.compile(r"^(none|[\w\s,.%#()/-]+)$"),
    "duration": re.compile(r"^\d*\.?\d+m?s$", re.I),
    "easing": re.compile(
        r"^(linear|ease|ease-in|ease-out|ease-in-out|step-start|step-end"
        r"|(?:cubic-bezier|steps|linear)\([^()]*\))$", re.I),
}

#: A value may reference a token of ours, because that is how a shadow keeps its
#: geometry in one place and its colour in another. It may not reference anything
#: else: the host's own variable names do not exist inside a generated document.
_OURS = re.compile(r"var\(\s*--z2s-[a-z0-9-]+\s*\)")

#: One refusal, with everything a person needs to fix it at the source. The
#: value is carried so the record can show it; the report prints the reason and
#: the name, never a value nobody asked to see.
Refusal = collections.namedtuple("Refusal", "token source value why")


def accepts(token, value):
    """May this value be written into a document as this token?

    Returns (True, None) or (False, reason). The reason is a sentence for a
    person, because it is going into a report somebody has to act on.
    """
    if not isinstance(value, str) or not value.strip():
        return False, "the value is empty"
    value = value.strip()

    if len(value) > MAX_LENGTH:
        return False, ("the value is %d characters, past the %d a design token "
                       "has any use for" % (len(value), MAX_LENGTH))

    lowered = value.lower()
    for mark in FORBIDDEN:
        if mark in lowered:
            return False, ("the value contains %r, which cannot appear in a "
                           "value written into a style block" % mark)
    # Checked apart from the list above so the reason names the real problem: a
    # newline inside a declaration is how a second declaration gets smuggled in.
    if "\n" in value or "\r" in value:
        return False, "the value spans more than one line"

    # var() survives the forbidden list because it opens no network and closes
    # no block, so the reference itself is judged here.
    stripped = _OURS.sub("", value)
    if "var(" in stripped.lower():
        return False, ("the value refers to a variable the document does not "
                       "carry; only this method's own tokens can be referenced")

    kind = tokens.TYPES.get(token)
    if kind is None:
        return False, "%s is not a token this method's contract defines" % token
    shape = SHAPES[kind]
    if not shape.match(stripped.strip() or value):
        return False, "the value does not read as a %s" % kind
    return True, None


def sift(mapped, source=""):
    """Split adopted values into what may be written and what may not.

    Returns (kept, refused). Iterated in contract order so two runs over the
    same project refuse in the same order and the record does not churn
    (NFR-GEN-01).
    """
    kept, refused = {}, []
    for token in tokens.CONTRACT:
        if token not in mapped:
            continue
        value = mapped[token]
        ok, why = accepts(token, value)
        if ok:
            kept[token] = value.strip()
        else:
            refused.append(Refusal(token, source, value, why))
    return kept, refused


def dark_clause(values, dark):
    """What the run report says about the dark half of a host's palette.

    A count on its own reads as success — "declared for 5 of them" sounds like
    five arrived and did something. Dark is all or nothing (tokens.dual), so
    five arriving means none were used, and saying that without naming the gap
    leaves an operator with a scheme that will not turn on and no way to find
    out why. Every missing colour is listed, in the same never-silent style as
    the refusals below.
    """
    if not dark:
        return ""
    missing = tokens.missing_dark(dark)
    if not missing:
        return ("; a dark counterpart was declared for every colour%s"
                % ("" if tokens.dual(values, dark)
                   else ", but every one repeats its light value, so dark mode"
                        " was not used"))
    return ("; a dark counterpart was declared for %d of %d colours, so dark"
            " mode was not used — declare one for %s to use it"
            % (len(dark), len(tokens.COLOURS), ", ".join(missing)))


def refusal_lines(refused):
    """The run report's account of what was turned away.

    Every refusal is named. A value silently dropped back to neutral would be
    reported as adoption, which FR-GEN-03 forbids — and would leave the operator
    wondering why one colour in their palette never arrived.
    """
    return ["design tokens: refused %s from %s — %s"
            % (item.token, item.source or "the host design system", item.why)
            for item in refused]


# ------------------------------------------------------- reading a stylesheet

_DECLARATION = re.compile(r"--([a-zA-Z0-9_-]+)\s*:\s*([^;{}]+)")
_REFERENCE = re.compile(r"var\(\s*--([a-zA-Z0-9_-]+)\s*(?:,[^)]*)?\)")
_SCSS = re.compile(r"\$([a-zA-Z0-9_-]+)\s*:\s*([^;{}!]+)")
_COMMENT = re.compile(r"/\*.*?\*/", re.S)

#: Selectors whose declarations are the document's own values rather than one
#: component's. A design system states its tokens on the root, and a rule for
#: .sidebar states one component's, which is not this document's business.
_ROOT = re.compile(r"^(:root|html|body|\*|:where\(\s*:root\s*\)|:host)$", re.I)

#: What makes a block the DARK half of a system. Three spellings because three
#: are in common use and a system that uses the one this misses reads as having
#: no dark theme at all, which is reported rather than guessed at.
_DARK = re.compile(r"""(prefers-color-scheme\s*:\s*dark
                       |\[\s*data-theme\s*[~^|$*]?=\s*['"]?dark
                       |(?<![\w-])\.dark(?![\w-])
                       |(?<![\w-])\.theme-dark(?![\w-]))""",
                   re.I | re.X)

#: At-rules a token declaration may sit inside. @theme is where Tailwind v4 puts
#: a whole design system, which is why that generation of the framework needs no
#: reader of its own.
_AT_OK = re.compile(r"^@(media|supports|layer|theme|scope)\b", re.I)


def _segments(text):
    """Every run of declarations in a stylesheet, with the block it sits in.

    Yields (context, chunk) where context is the tuple of preludes enclosing the
    chunk, outermost first. A brace-depth walk rather than a regex, because the
    flat regex this replaces was blind to selectors: a [data-theme="dark"] block
    declaring the same names as the :root above it simply overwrote the light
    values, and every document generated from such a project came out dark with
    no dark theme declared anywhere.
    """
    text = _COMMENT.sub(" ", text)
    stack, buf, out = [], [], []
    for ch in text:
        if ch == "{":
            stack.append("".join(buf).strip())
            buf = []
        elif ch == "}":
            if buf:
                out.append((tuple(stack), "".join(buf)))
            buf = []
            if stack:
                stack.pop()
        elif ch == ";":
            buf.append(ch)
            out.append((tuple(stack), "".join(buf)))
            buf = []
        else:
            buf.append(ch)
    if buf:
        out.append((tuple(stack), "".join(buf)))
    return out


def _scheme(context):
    """"light", "dark", or None for a block whose values are not the document's.

    Discarding is the default. A declaration under .sidebar is that component's
    and not this document's, and adopting it produces a document coloured by an
    accident — the failure this method exists to prevent.
    """
    dark = False
    for part in context:
        if not part:
            continue
        if part.startswith("@"):
            if not _AT_OK.match(part):
                return None
            dark = dark or bool(_DARK.search(part))
            continue
        pieces = [one.strip() for one in part.split(",") if one.strip()]
        if not pieces:
            return None
        for one in pieces:
            if _DARK.search(one):
                dark = True
                # A dark selector qualifies a root, and both spellings are used:
                # `.dark` on its own, and `.dark :root` / `:root.dark`.
                continue
            if not _ROOT.match(one):
                return None
    return "dark" if dark else "light"


def harvest(text):
    """(light, dark): the custom properties a stylesheet declares under each.

    Later declarations win within one scheme, which is what the cascade does.
    Across schemes they never meet, which is the whole point.
    """
    light, dark = {}, {}
    for context, chunk in _segments(text):
        scheme = _scheme(context)
        if scheme is None:
            continue
        target = dark if scheme == "dark" else light
        for name, value in _DECLARATION.findall(chunk):
            target[name] = value.strip()
        if not context:
            # SCSS variables live at file scope and have no block to sit in.
            # setdefault, so a custom property of the same name is not displaced
            # by a preprocessor variable that may not even be emitted.
            for name, value in _SCSS.findall(chunk):
                light.setdefault(name, value.strip())
    return light, dark


def _resolve(value, declared, depth=0):
    """Follow var() references within one stylesheet to a literal value.

    A design system that defines --color-text as var(--gray-900) should hand the
    document the grey, not a reference to a variable the document never carries.
    """
    if depth > 8:                       # a cycle: give up rather than hang
        return value
    match = _REFERENCE.search(value)
    if not match or match.group(1) not in declared:
        return value
    replaced = value[:match.start()] + declared[match.group(1)] + value[match.end():]
    return _resolve(replaced, declared, depth + 1)


_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _kebab(name):
    """One project's spelling of a name, in the one the synonym table uses.

    A stylesheet writes --color-background and a token module writes
    colorBackground, and they mean the same thing. Normalising here rather than
    in each reader means a reader added later gets it without asking.

    Spelling is normalised for the two words that actually turn up in a palette.
    The synonym table is written one way, and a brand book written in British
    English is not a design system this method should fail to read.
    """
    spelling = _CAMEL.sub("-", name).replace("_", "-").replace(".", "-").lower()
    return spelling.replace("colour", "color").replace("grey", "gray")


def _map_onto_contract(declared):
    """Translate one project's token names into contract names."""
    lowered = {}
    for name in sorted(declared):
        lowered.setdefault(name.lower(), name)
        spelling = _kebab(name)
        lowered.setdefault(spelling, name)
        # A role written as prose reads the other way round from a variable
        # name: a swatch table says "Page background" where a stylesheet says
        # --color-background. Registering the reverse costs one line and is what
        # lets a brand book's own words reach the contract.
        parts = spelling.split("-")
        if len(parts) == 2:
            lowered.setdefault("-".join(reversed(parts)), name)
    found, names = {}, {}
    for token in tokens.CONTRACT:
        for candidate in tokens.SYNONYMS.get(token, ()):
            if candidate in lowered:
                found[token] = _resolve(declared[lowered[candidate]], declared)
                names[token] = lowered[candidate]
                break
    return found, names


# -------------------------------------------------- reading a token document

#: Aliases in the W3C design-token format, which point at another token by its
#: path: {color.brand.500}. Style Dictionary spells them the same way.
_ALIAS = re.compile(r"^\{([^{}]+)\}$")


def _flatten(node, trail, out):
    """Every token in a design-token document, as name -> value.

    Both published dialects are read at once because they differ in two keys and
    nothing else: the W3C format writes $value and $type, Style Dictionary
    writes value and type. Recognising them apart would buy a distinction with
    no consequence.

    Each token is filed under two names — its full path and its leaf — so a
    system that groups `color.primary` and one that names `primary` outright are
    both reachable. The full path is written first and the leaf with setdefault,
    so two groups sharing a leaf resolve to the first in sorted order rather
    than to whichever the file happened to list last.
    """
    if not isinstance(node, dict):
        return
    value = node.get("$value", node.get("value"))
    if value is not None and not isinstance(value, dict):
        name = "-".join(trail)
        out[name] = str(value)
        if trail:
            out.setdefault(trail[-1], str(value))
        return
    for key in sorted(node):
        if key.startswith("$") or key in ("value", "type", "comment",
                                          "description"):
            continue
        _flatten(node[key], trail + [key], out)


def _dealias(declared, depth=0):
    """Point every alias at the value it names, within one document."""
    if depth > 8:
        return declared
    out, moved = {}, False
    for name in sorted(declared):
        match = _ALIAS.match(declared[name].strip())
        if match:
            target = match.group(1).replace(".", "-")
            if target in declared and target != name:
                out[name] = declared[target]
                moved = True
                continue
        out[name] = declared[name]
    return _dealias(out, depth + 1) if moved else out


def read_tokens_document(text):
    """A design-token document's tokens, in either published dialect."""
    flat = {}
    _flatten(json.loads(text), [], flat)
    return _dealias(flat), {}


# ------------------------------------------ reading a literal object in code

_KEY = re.compile(r"""(?:['"]([^'"]+)['"]|([A-Za-z_$][\w$-]*))\s*:\s*""")

#: Constructs this scanner will not guess at. Meeting one abandons the whole
#: key it appeared under: a half-read palette is a design system nobody has, and
#: is worse than no adoption because it looks like one.
_OPAQUE = re.compile(r"(require\s*\(|\.\.\.|=>|function\s*\(|`|\[[^\]]*\]\s*:)")


def _object_at(text, start):
    """The literal object beginning at `start`, as name -> value, or None.

    One scanner, used for both a Tailwind configuration and a token module: the
    thing being read is a literal object in either case, and writing it twice is
    how the two drift. Nested objects flatten to dashed paths, so a theme's
    `colors.brand.500` arrives as `colors-brand-500` and meets the same synonym
    table a stylesheet's names meet.
    """
    depth, i, out, trail = 0, start, {}, []
    pending = None
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
            if pending is not None:
                trail.append(pending)
                pending = None
            i += 1
            continue
        if ch == "}":
            depth -= 1
            if trail:
                trail.pop()
            i += 1
            if depth == 0:
                return out
            continue
        if ch in "\"'":
            close = text.find(ch, i + 1)
            if close < 0:
                return None
            if pending is not None:
                out.setdefault("-".join(trail + [pending]), text[i + 1:close])
                out.setdefault(pending, text[i + 1:close])
                pending = None
            i = close + 1
            continue
        match = _KEY.match(text, i)
        if match:
            if _OPAQUE.match(text, match.end()):
                return None
            pending = match.group(1) or match.group(2)
            i = match.end()
            continue
        if _OPAQUE.match(text, i):
            return None
        if pending is not None and not ch.isspace() and ch not in ",{":
            # A bare value: a number, or an identifier this scanner does not
            # need to understand beyond where it ends.
            end = i
            while end < len(text) and text[end] not in ",}\n":
                end += 1
            out.setdefault("-".join(trail + [pending]), text[i:end].strip())
            out.setdefault(pending, text[i:end].strip())
            pending = None
            i = end
            continue
        i += 1
    return None


#: Where a design system hides in code. Only these keys are read: scanning every
#: object in a file would harvest a component's props as though they were tokens.
_ROOTS = (re.compile(r"\btheme\s*:\s*\{"),
          re.compile(r"\b(?:export\s+const|const|let|var)\s+\w*[Tt]okens?\w*\s*"
                     r"(?::[^=]+)?=\s*\{"),
          re.compile(r"\bexport\s+default\s*\{"),
          re.compile(r"\bmodule\.exports\s*=\s*\{"))


def read_code_object(text):
    """The design tokens a JavaScript or TypeScript module states, if any."""
    found = {}
    for pattern in _ROOTS:
        for match in pattern.finditer(text):
            values = _object_at(text, match.end() - 1)
            if values:
                for name in sorted(values):
                    found.setdefault(name, values[name])
    return found, {}


def read_stylesheet(text):
    """(light, dark) for a stylesheet. Named for symmetry with the others."""
    return harvest(text)


# --------------------------------------------- reading a reference document

#: A brand book and a DESIGN.md state a design system three ways at once, and
#: all three are read (M16-11):
#:
#:   T1  code the document embeds — a <style> block, a fenced ```css block. It
#:       is CSS, so the reader above already handles it and this is extraction.
#:   T2  a table of swatches, where one column holds the value and another says
#:       what it is for. The second column is the role signal; without it the
#:       values are recorded as unclaimed rather than assigned to a guess.
#:   T3  the prose, which no parser should attempt. An agent reads it, proposes
#:       a mapping for what T1 and T2 left empty, and the operator confirms it
#:       through /zero:questions before it is recorded. That half lives in the
#:       gate below, not here.

_STYLE_ELEMENT = re.compile(r"<style[^>]*>(.*?)</style>", re.I | re.S)
_LINK = re.compile(r"""<link\b[^>]*\bhref\s*=\s*['"]([^'"]+)['"][^>]*>""", re.I)
_FENCE = re.compile(r"^[ \t]*(?:```+|~~~+)[ \t]*(\w+)?[ \t]*$(.*?)"
                    r"^[ \t]*(?:```+|~~~+)[ \t]*$",
                    re.M | re.S)
_TAG = re.compile(r"<[^>]+>")
_ROW = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.I | re.S)
_CELL = re.compile(r"<t[hd]\b[^>]*>(.*?)</t[hd]>", re.I | re.S)

#: Absolute destinations. Recorded and reported, NEVER fetched: no module in
#: this package imports anything that could open a socket, and a test asserts
#: it. A document's design system is not decided by whether somebody else's
#: server answered.
_ABSOLUTE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:)?//|^[a-z][a-z0-9+.-]*:", re.I)

#: A column heading that says what a value is FOR. This is the role signal, and
#: a table without one is a table this reader will not guess the meaning of.
_ROLE_COLUMN = re.compile(
    r"^(usage|use|used for|used as|role|purpose|token|variable|name|applies to"
    r"|meaning|where)$", re.I)

#: A column heading that says what the value IS.
#: Not "swatch": that column holds the chip or its nickname, and reading it as
#: the value adopted the word "Parchment" as a colour. Found by a test against a
#: brand book in the shape a real one is written in.
_VALUE_COLUMN = re.compile(
    r"^(value|hex|hex code|code|css|size|measurement|token value)$", re.I)

_LOOKS_LIKE_VALUE = re.compile(
    r"^(#[0-9a-f]{3,8}"
    r"|(?:rgba?|hsla?|oklch|oklab|lab|lch)\([^()]*\)"
    r"|-?\d*\.?\d+(?:px|rem|em|ch|%|pt|ms|s)?)$", re.I)


def _slug(text):
    """A cell's words as a name the synonym table might recognise."""
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def read_table(rows):
    """Tokens a swatch table states, as name -> value.

    Rows are lists of cell strings, the first possibly a heading. A role column
    is REQUIRED: with one, a row's value is filed under the role it names; with
    none, the value is filed under a name that can match nothing, so it reaches
    the record as unclaimed instead of being assigned to a role somebody guessed
    (M16-11). A swatch called "Ink" might be body text or it might be a brand
    black, and the difference is a document that looks like a broken version of
    the product.
    """
    if not rows:
        return {}
    heading = [cell.strip() for cell in rows[0]]
    role = value = None
    for index, cell in enumerate(heading):
        if role is None and _ROLE_COLUMN.match(cell):
            role = index
        if value is None and _VALUE_COLUMN.match(cell):
            value = index
    body = rows[1:] if (role is not None or value is not None) else rows

    out = {}
    for cells in body:
        if value is not None and value < len(cells):
            held = cells[value].strip()
        else:
            found = [cell.strip() for cell in cells
                     if _LOOKS_LIKE_VALUE.match(cell.strip())]
            held = found[0] if found else ""
        if not held:
            continue
        if role is not None and role < len(cells):
            name = _slug(cells[role])
        else:
            words = [cell.strip() for cell in cells
                     if cell.strip() and not _LOOKS_LIKE_VALUE.match(cell.strip())]
            # Prefixed so it can match no synonym: the table did not say what
            # this is for, and this reader does not decide that on its own.
            name = "unnamed-" + _slug(words[0]) if words else ""
        if name:
            out.setdefault(name, held)
    return out


def _markdown_tables(text):
    """Every pipe table in a Markdown document, as lists of rows of cells."""
    tables, current = [], []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if all(set(cell) <= set(" -:") and cell for cell in cells):
                continue                       # the rule under the heading
            current.append(cells)
            continue
        if current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables


def _html_tables(text):
    """Every table in an HTML document, as lists of rows of cells."""
    tables = []
    for block in re.findall(r"<table\b.*?</table>", text, re.I | re.S):
        rows = [[_TAG.sub(" ", cell).replace("&nbsp;", " ").strip()
                 for cell in _CELL.findall(row)]
                for row in _ROW.findall(block)]
        rows = [row for row in rows if row]
        if rows:
            tables.append(rows)
    return tables


def read_markdown(text):
    """(light, dark) for a Markdown reference document.

    Fenced blocks are routed to the reader their language names; everything else
    a parser can honestly take is a table. The prose is left for the interview.
    """
    light, dark = {}, {}
    for language, body in _FENCE.findall(text):
        language = (language or "").lower()
        if language in ("css", "scss", "sass", "less"):
            found, found_dark = harvest(body)
        elif language in ("json", "jsonc", "json5"):
            try:
                found, found_dark = read_tokens_document(body)
            except ValueError:
                continue
        else:
            continue
        for name, value in found.items():
            light.setdefault(name, value)
        for name, value in found_dark.items():
            dark.setdefault(name, value)
    for rows in _markdown_tables(text):
        for name, value in read_table(rows).items():
            light.setdefault(name, value)
    return light, dark


def read_brand_book(text, path=""):
    """(light, dark) for an HTML reference document.

    Style blocks first, because a brand book that carries its palette as CSS has
    said it precisely; then the swatch tables. A stylesheet linked with a
    relative path is read as a file — it is inside the project the operator
    pointed at. An absolute one is recorded and reported and never fetched: this
    package opens no socket, and what a reader can do with a document is not
    decided by whether somebody else's server answered.
    """
    light, dark, remote = {}, {}, []
    for body in _STYLE_ELEMENT.findall(text):
        found, found_dark = harvest(body)
        for name, value in found.items():
            light.setdefault(name, value)
        for name, value in found_dark.items():
            dark.setdefault(name, value)

    for href in _LINK.findall(text):
        if _ABSOLUTE.match(href.strip()):
            remote.append(href.strip())
            continue
        beside = os.path.normpath(
            os.path.join(os.path.dirname(path), href.split("?")[0].split("#")[0]))
        if not beside.lower().endswith((".css", ".scss")):
            continue
        try:
            with open(beside, encoding="utf-8") as handle:
                found, found_dark = harvest(handle.read())
        except (OSError, UnicodeDecodeError):
            continue
        for name, value in found.items():
            light.setdefault(name, value)
        for name, value in found_dark.items():
            dark.setdefault(name, value)

    for rows in _html_tables(text):
        for name, value in read_table(rows).items():
            light.setdefault(name, value)
    return light, dark, remote


def remote_lines(paths):
    """What to say about a stylesheet this will not go and get."""
    return ["design tokens: %s links a stylesheet at %s, which was recorded and "
            "not fetched — this method opens no network connection; copy the "
            "file into the project if its values belong in the design system"
            % (document, href) for document, href in paths]


#: A file's extension and name decide which reader sees it, and the kind decides
#: which source outranks which when two disagree. Ordered best first: a document
#: written to say what the design system IS beats a stylesheet that happens to
#: contain it, which beats a preprocessor variable that may never be emitted.
KINDS = ("tokens", "css", "scss", "tailwind", "code", "brandbook", "markdown")
KIND_RANK = {name: number for number, name in enumerate(KINDS)}

#: Names that mean "this file is the design system", used where an extension is
#: not enough. Reading every .json in a project would parse its lockfiles; every
#: .js would harvest a component's props as though they were tokens.
_TOKEN_NAMES = ("tokens", "theme", "design-tokens", "designtokens",
                "design-system", "palette", "variables")

#: Names that mean "this document describes the design system in prose".
_REFERENCE_NAMES = ("design", "design-system", "designsystem", "brand",
                    "brand-book", "brandbook", "brand-guidelines", "styleguide",
                    "style-guide", "tokens", "theme")

#: Refused by name, and by name only (M16-09). There is no YAML reader in the
#: standard library and NFR-ARC-03 forbids reaching for one, and a partial
#: parser written by hand misreads anchors, block scalars and nesting quietly —
#: which is the exact failure this method exists to prevent. Saying so beats
#: reading it wrong, and beats saying nothing.
_YAML = (".yaml", ".yml")


def _stem(name):
    return name.rsplit(".", 1)[0].lower()


def _reader_for(name):
    """(kind, reader) for a filename, or (None, None)."""
    lower = name.lower()
    stem = _stem(lower)
    if lower.endswith(".css"):
        return "css", read_stylesheet
    if lower.endswith((".scss", ".sass")):
        return "scss", read_stylesheet
    if lower.endswith(".json"):
        if stem in _TOKEN_NAMES or stem.endswith(".tokens") \
                or lower.endswith(".tokens.json"):
            return "tokens", read_tokens_document
        return None, None
    if lower.endswith((".js", ".ts", ".cjs", ".mjs", ".cts", ".mts")):
        if stem.startswith("tailwind.config") or stem == "tailwind":
            return "tailwind", read_code_object
        if stem in _TOKEN_NAMES:
            return "code", read_code_object
    # A reference document is read when the operator names it, and when its name
    # says plainly what it is. Reading every .md and .html in a project would
    # harvest its changelog and its rendered output.
    if lower.endswith((".md", ".markdown")):
        if stem in _REFERENCE_NAMES:
            return "markdown", read_markdown
    if lower.endswith((".html", ".htm")):
        if stem in _REFERENCE_NAMES:
            return "brandbook", read_brand_book
    return None, None


def reader_for_named(path):
    """(kind, reader) for a file the operator handed over.

    A named document is read on its extension alone. They pointed at it, which
    settles what it is meant to be — a brand book called `2026-refresh.html` is
    still a brand book, and refusing it for its name would be this method
    telling the operator they misfiled their own design system (M16-12).
    """
    kind, reader = _reader_for(os.path.basename(path))
    if reader is not None:
        return kind, reader
    lower = path.lower()
    if lower.endswith((".html", ".htm")):
        return "brandbook", read_brand_book
    if lower.endswith((".md", ".markdown")):
        return "markdown", read_markdown
    if lower.endswith(".json"):
        return "tokens", read_tokens_document
    if lower.endswith((".js", ".ts", ".cjs", ".mjs")):
        return "code", read_code_object
    return None, None


def _candidates(root):
    """Files worth reading, in a fixed order (NFR-GEN-01).

    Returns (path, kind, reader) triples, and separately the YAML files found,
    which are reported rather than read.
    """
    out, yaml = [], []
    for folder, subfolders, names in os.walk(root):
        subfolders[:] = sorted(name for name in subfolders if name not in SKIP)
        for name in sorted(names):
            path = os.path.join(folder, name)
            if name.lower().endswith(_YAML) and _stem(name) in _TOKEN_NAMES:
                yaml.append(path)
                continue
            kind, reader = _reader_for(name)
            if reader is not None:
                out.append((path, kind, reader))
    return out, yaml


def yaml_lines(paths):
    """What to say about a design system written in a format nothing reads."""
    return ["design tokens: %s looks like a design system, and YAML is not read "
            "— this method reads CSS, SCSS, design-token JSON and literal "
            "objects in JavaScript or TypeScript, and an operator value in the "
            "design record outranks all of them" % path
            for path in paths]


# ------------------------------------------------------------- staying legible

#: The range each scale token is held to, in rem for a length and bare for a
#: ratio (M16-08). A host's scale is adopted, and then held inside the range a
#: document can still be read at: product rhythm is worth having and a body size
#: of 4rem is not rhythm, it is a document nobody finishes.
#:
#: Colour, shape, elevation, motion and typeface are NOT clamped. They carry the
#: identity and none of them can make a document unreadable — the contrast floor
#: is a separate duty (NFR-UX-03) and belongs to the values, not to a range.
CLAMPS = {
    "size-h1": (1.5, 4.0), "size-h2": (1.25, 2.75), "size-h3": (1.0, 2.0),
    "size-body": (0.875, 1.5), "size-small": (0.6875, 1.25),
    "size-mono": (0.75, 1.25),
    "space-1": (0.0625, 0.75), "space-2": (0.125, 1.25), "space-3": (0.25, 2.0),
    "space-4": (0.5, 3.0), "space-5": (0.75, 4.0), "space-6": (1.0, 6.0),
    "line-tight": (0.9, 1.6), "line-body": (1.2, 2.2),
}

#: How many CSS pixels a rem is taken to be. A reader who has changed their
#: browser's base size gets a document that scales with them, so this is only
#: ever used to compare one written value against a range.
_PER_REM = 16.0

_SCALAR = re.compile(r"^(-?\d*\.?\d+)(rem|em|px)?$", re.I)

#: One value held back, and what it was held to. Reported like a refusal,
#: because a value silently moved is a value the operator cannot find the
#: reason for (FR-GEN-03).
Clamp = collections.namedtuple("Clamp", "token source was now")


def clamp(token, value):
    """(value, Clamp or None). A value outside its range is held at the edge.

    A value this cannot read — calc(), clamp(), a unit nobody scales in — is
    passed through untouched and unreported. Stated ceiling: a responsive size
    written as clamp() is already bounded by its author, and guessing at the
    range it resolves to would be worse than trusting it.
    """
    limits = CLAMPS.get(token)
    if limits is None:
        return value, None
    match = _SCALAR.match(str(value).strip())
    if not match:
        return value, None
    number, unit = float(match.group(1)), (match.group(2) or "").lower()
    scaled = number / _PER_REM if unit == "px" else number
    low, high = limits
    held = min(max(scaled, low), high)
    if abs(held - scaled) < 1e-9:
        return value, None
    written = "%g" % held if not unit else "%grem" % held
    return written, Clamp(token, "", value, written)


def clamp_lines(clamped):
    """What was held back, named one per line."""
    return ["design tokens: held %s at %s (the host states %s, which is outside "
            "the range a document stays legible in)"
            % (one.token, one.now, one.was) for one in clamped]


# ------------------------------------------------------------------ the merge

#: One file, read. Kept whole rather than merged as it is read, because the
#: merge has to see every source at once to choose which of them is the base.
Source = collections.namedtuple(
    "Source", "path kind light dark declared remote names")


def read_source(path, kind, reader):
    """One file's contribution, or None if it could not be read."""
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return None
    remote = []
    try:
        if reader is read_brand_book:
            declared, dark_declared, hrefs = reader(text, path)
            remote = [(path, href) for href in hrefs]
        else:
            declared, dark_declared = reader(text)
    except (ValueError, RecursionError):
        # A malformed token document or an object this scanner will not guess
        # at. Not an error: the file simply is not a design system this can
        # read, and the run says which files it did read.
        return None
    if not isinstance(declared, dict):
        return None
    light, names = _map_onto_contract(declared)
    dark = _map_onto_contract(dark_declared)[0] if dark_declared else {}
    return Source(path, kind, light, dark, declared, remote, names)


def _order(source):
    """Sort key: better kind first, then path, so nothing depends on the order
    the filesystem happens to return (NFR-GEN-01)."""
    return (KIND_RANK.get(source.kind, len(KINDS)), source.path)


def merge(sources, named=()):
    """Resolve many sources into one theme.

    Named sources — the files an operator handed to /zero:design — are resolved
    first and are never displaced (M16-12). You named it, so it is the intended
    system, and a thorough component stylesheet elsewhere in the tree must not
    outvote the brand book you pointed at.

    Among the rest: the source mapping the most tokens becomes the BASE and
    contributes everything it has; the others FILL only what is still empty.
    Base-then-fill rather than a flat per-token race because mixing one
    product's greys with another's blues produces a document that looks like
    neither, and the coherence of one system is worth more than coverage across
    several. Fill still gets the case that matters: a token document for colour
    beside a stylesheet for spacing.

    Returns (light, dark, chosen, order, origin) where `chosen` is the base
    source or None, `order` is every source that contributed best first, and
    `origin` maps each token to the file and the host name it came from — a
    reviewer cannot approve #0b0b0f without being told which of their own
    variables it is.
    """
    light, dark, contributed, origin = {}, {}, [], {}

    for source in sorted(named, key=_order):
        before = len(light)
        for token, value in source.light.items():
            if token not in light:
                light[token] = value
                origin[token] = (source.path, source.names.get(token, token))
        for token, value in source.dark.items():
            dark.setdefault(token, value)
        if len(light) > before or source.dark:
            contributed.append(source)

    # A palette is a whole. Once one is established — by the documents the
    # operator NAMED, or by the base source below — a later source may fill the
    # scale, the shape and the motion, because those compose across systems. It
    # may never fill a colour: half of one palette plus half of another is
    # neither, and the result is a document that looks like a BROKEN version of
    # the product, which reads worse than a plainly neutral one.
    #
    # Found by driving a real project rather than by reasoning: a decoy
    # stylesheet under src/ filled surface-card with #111111 into a parchment
    # palette, and every card in the document went near-black.
    def without_colour(source):
        return source._replace(light={
            token: value for token, value in source.light.items()
            if token not in tokens.COLOURS})

    settled = any(token in tokens.COLOURS for token in light)
    rest = [one for one in sources if one not in named]
    scored = sorted(rest, key=lambda one: (-len(one.light), _order(one)))
    chosen = None
    for source in scored:
        if len(source.light) >= THRESHOLD:
            chosen = source
            break

    if chosen is not None:
        if settled:
            chosen = without_colour(chosen)
        before = len(light)
        for token, value in chosen.light.items():
            if token not in light:
                light[token] = value
                origin[token] = (chosen.path, chosen.names.get(token, token))
        for token, value in chosen.dark.items():
            dark.setdefault(token, value)
        if len(light) > before or chosen.dark:
            contributed.append(chosen)

    settled = settled or any(token in tokens.COLOURS for token in light)

    for source in sorted(rest, key=_order):
        if source.path == (chosen.path if chosen else None) \
                or len(source.light) < FILL_THRESHOLD:
            continue
        if settled:
            source = without_colour(source)
        before = len(light)
        for token, value in source.light.items():
            if token not in light:
                light[token] = value
                origin[token] = (source.path, source.names.get(token, token))
        for token, value in source.dark.items():
            dark.setdefault(token, value)
        if len(light) > before or (source.dark and source not in contributed):
            contributed.append(source)

    return light, dark, chosen, contributed, origin


#: The most unclaimed names to carry into the record. Enough to grow the synonym
#: table from a real project, few enough that the record stays a thing somebody
#: reads rather than a dump of every variable in a codebase.
NAMED_UNMAPPED = 24


def unmapped(sources, light):
    """Names the host declared that no contract token claimed.

    The feedback loop: what turns up here across real projects is what the
    synonym table should learn next. Sorted and capped, so the record does not
    churn and does not become a listing.
    """
    claimed = set()
    for token in light:
        claimed.update(tokens.SYNONYMS.get(token, ()))
    seen = set()
    for source in sources:
        for name in source.declared:
            if name.lower() not in claimed:
                seen.add(name)
    return sorted(seen)[:NAMED_UNMAPPED]


#: What one run of detection concluded. A record rather than a tuple because the
#: refusals travel with the values: a caller that can reach the theme without
#: reaching what was turned away is a caller that reports a fallback as an
#: adoption (FR-GEN-03).
Adoption = collections.namedtuple(
    "Adoption",
    "values dark source refused clamped sources unmapped unread remote origin")


def detect(root, named=()):
    """Find the host project's design tokens.

    A complete contract-satisfying token set, its dark counterpart where the
    host declares one, the path the theme is mostly from, and everything that
    was refused, held back, or found in a format nothing reads.

    `named` is a list of paths the operator handed over. They outrank anything
    discovered (M16-12) and are read even when their extension would not have
    been walked to.
    """
    walked, yaml = _candidates(root)
    found = [one for one in
             (read_source(path, kind, reader) for path, kind, reader in walked)
             if one is not None]

    chosen_named = []
    for path in named:
        kind, reader = reader_for_named(path)
        if reader is None:
            continue
        already = [one for one in found if os.path.abspath(one.path)
                   == os.path.abspath(path)]
        source = already[0] if already else read_source(path, kind, reader)
        if source is not None:
            chosen_named.append(source)

    light, dark, chosen, contributed, origin = merge(found, chosen_named)

    kept, refused = sift(light, chosen.path if chosen else "")
    kept_dark, refused_dark = sift(dark, chosen.path if chosen else "")
    refused = refused + [one for one in refused_dark
                         if one.token not in [two.token for two in refused]]

    clamped = []
    for token in tokens.CONTRACT:
        for holder in (kept, kept_dark):
            if token in holder:
                held, note = clamp(token, holder[token])
                if note is not None:
                    holder[token] = held
                    clamped.append(note)

    resolved = dict(tokens.NEUTRAL)
    resolved.update(kept)
    # A dark counterpart is used only where the host states one. Where it does
    # not, tokens.render writes the light value for both schemes rather than
    # inventing a dark one — the whole of "never synthesise".
    dark_theme = {name: value for name, value in kept_dark.items()
                  if name in tokens.COLOURS}
    origin.update({token: (chosen.path if chosen else "", token)
                   for token in light if token not in origin})
    remote = sorted(set(sum((one.remote for one in found + chosen_named), [])))
    origin = {token: origin[token] for token in kept if token in origin}
    if not kept and not dark_theme:
        return Adoption(resolved, {}, None, refused, clamped, [], [], yaml,
                        remote, {})
    source = chosen_named[0].path if chosen_named else (
        chosen.path if chosen else None)
    return Adoption(resolved, dark_theme, source, refused, clamped,
                    contributed, unmapped(contributed, kept), yaml, remote,
                    origin)


def report(found):
    """One line for the run report, naming what actually happened.

    Accepts an Adoption or a bare source path, because the second is what a
    project record stores and re-reading the whole tree to print one line would
    be a walk for a sentence.
    """
    source = found.source if isinstance(found, Adoption) else found
    if source is None:
        line = "design tokens: no design system found; the neutral theme was used"
    else:
        line = "design tokens: adopted from %s" % source
    if not isinstance(found, Adoption):
        return line
    if source is not None and len(found.sources) > 1:
        line += " and %d more" % (len(found.sources) - 1)
    line += dark_clause(found.values, found.dark)
    return "\n".join([line] + refusal_lines(found.refused)
                     + clamp_lines(found.clamped) + yaml_lines(found.unread)
                     + remote_lines(found.remote))


# ------------------------------------------------------------- the record

#: The record's own format version, separate from the document schema version
#: and from the plugin's. Nothing gates on it today; it exists so a later change
#: to the shape has a place to say so rather than guessing from the keys.
RECORD_VERSION = 1

#: The authority order, highest first. Written down here because it is the one
#: thing about this file somebody has to know before editing it, and a rule that
#: lives only in code is a rule nobody reads before overwriting a decision:
#:
#:   overrides  what an operator wrote in this file by hand. Always wins, and is
#:              copied through every refresh untouched.
#:   confirmed  what an operator approved when an agent read a reference
#:              document's prose and proposed a mapping (M16-11, tier three).
#:   tokens     what was read from files, named documents before discovered.
#:   NEUTRAL    the theme this method ships, for everything still unanswered.
AUTHORITY = ("overrides", "confirmed", "tokens")


def digest(path):
    """A file's contents, as a hash. Content rather than a timestamp, because
    this method has no clock by design and a modification time says a file was
    touched rather than that it changed."""
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return ""


def record_path(root):
    return os.path.join(root, *paths.DESIGN_FILE.split("/"))


def build_record(found, root, keep=None):
    """The record this run would write, as a plain structure.

    `keep` is the record already on disk, if any. Its `overrides` and
    `confirmed` blocks are copied through VERBATIM: they are the operator's
    decisions, and re-reading the host project cannot reproduce them. A refresh
    that quietly discarded them would report success while undoing a choice
    somebody made deliberately.
    """
    keep = keep or {}
    tokens_block = {}
    for name in tokens.CONTRACT:
        if name not in found.origin:
            continue
        path, host = found.origin[name]
        entry = {"light": found.values[name],
                 "from": "%s %s" % (os.path.relpath(path, root), host)
                         if path else host}
        if name in found.dark:
            entry["dark"] = found.dark[name]
        tokens_block[name] = entry

    return {
        "version": RECORD_VERSION,
        "scheme": "light-dark" if found.dark else "light",
        "tokens": tokens_block,
        "overrides": keep.get("overrides", {}),
        "confirmed": keep.get("confirmed", {}),
        "sources": [{"path": os.path.relpath(one.path, root),
                     "kind": one.kind,
                     "sha256": digest(one.path),
                     "mapped": len(one.light),
                     "role": "base" if one.path == found.source else "fill"}
                    for one in found.sources],
        "refused": [{"token": one.token,
                     "from": os.path.relpath(one.source, root)
                             if one.source else "",
                     "why": one.why}
                    for one in found.refused],
        "clamped": [{"token": one.token, "was": one.was, "now": one.now}
                    for one in found.clamped],
        "unmapped": found.unmapped,
    }


def read_record(root):
    """The record on disk, or None. Raises ValueError on one it cannot read.

    A DAMAGED record is not quietly re-detected. It means the operator's
    overrides are unreadable, and adopting a freshly detected theme would
    discard a deliberate decision and report success — which is exactly what
    FR-GEN-03 forbids. The caller falls back to the neutral theme and says so.
    """
    path = record_path(root)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        held = json.loads(handle.read())
    if not isinstance(held, dict) or not isinstance(held.get("tokens"), dict):
        raise ValueError("the design record has no tokens block")
    return held


def write_record(root, record):
    """Write the record. Sorted and indented, because it is read by people."""
    path = record_path(root)
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    writer.write(path, json.dumps(record, indent=2, sort_keys=True) + "\n")
    return path


def resolve_record(record):
    """(values, dark) from a record, applying the authority order.

    Every token the record does not answer keeps its neutral value, which is
    what makes a partial record safe: a project that has confirmed four colours
    is not a project with a half-styled document.
    """
    values, dark = dict(tokens.NEUTRAL), {}
    for block in reversed(AUTHORITY):
        held = record.get(block) or {}
        for name in tokens.CONTRACT:
            entry = held.get(name)
            if entry is None:
                continue
            if isinstance(entry, str):
                entry = {"light": entry}
            if entry.get("light"):
                values[name] = entry["light"]
            if entry.get("dark") and name in tokens.COLOURS:
                dark[name] = entry["dark"]
    return values, dark


def stale(root, record):
    """Source files the record was built from that have changed since.

    Content-based, never time-based: `skills/update/SKILL.md` says this method
    has no clock by design, and a modification time reports that a file was
    touched rather than that it changed.
    """
    moved = []
    for entry in record.get("sources", []):
        path = os.path.join(root, entry.get("path", ""))
        held = entry.get("sha256", "")
        if held and digest(path) != held:
            moved.append(entry.get("path", ""))
    return sorted(moved)


# ------------------------------------------------------- what a document uses

#: The theme one document is rendered with, and the one line the run reports.
Theme = collections.namedtuple("Theme", "values dark note")

#: Resolved once per project root rather than once per document. Before this,
#: rendering a plan of sixteen files walked the whole project tree sixteen times
#: and threw the answer away each time.
_RESOLVED = {}


def forget():
    """Drop the per-root cache. For a caller that has just written a record."""
    _RESOLVED.clear()


def theme(root):
    """The values to style a document with, and what to say about them.

    Record first, then detection, then neutral — and always with a line saying
    which of the three happened, because a silent fallback reads as adoption
    (FR-GEN-03). Four states, four sentences:

      record present, sources unchanged  use it
      record present, sources changed    use it anyway, and say which file moved
      record absent                      detect, write nothing, say so
      record damaged                     NEUTRAL, loudly

    The damaged case deliberately does not fall through to detection. A record
    that cannot be read is a record whose overrides cannot be read, and adopting
    a detected theme instead would quietly discard a decision somebody made and
    then report success.
    """
    key = os.path.abspath(root)
    if key in _RESOLVED:
        return _RESOLVED[key]

    try:
        held = read_record(root)
    except (ValueError, OSError, UnicodeDecodeError) as trouble:
        answer = Theme(dict(tokens.NEUTRAL), {},
                       "design tokens: %s could not be read (%s); the neutral "
                       "theme was used, and any operator values in it were NOT "
                       "applied" % (paths.DESIGN_FILE, trouble))
        _RESOLVED[key] = answer
        return answer

    if held is not None:
        values, dark = resolve_record(held)
        counted = len(held.get("tokens", {}))
        note = "design tokens: adopted from %s (%d values)" % (
            paths.DESIGN_FILE, counted)
        if held.get("overrides"):
            note += ", %d of them an operator's own" % len(held["overrides"])
        moved = stale(root, held)
        if moved:
            note += ("; %s has changed since it was recorded — run /zero:design "
                     "to read it again" % ", ".join(moved))
        answer = Theme(values, dark, note)
        _RESOLVED[key] = answer
        return answer

    found = detect(root)
    note = report(found)
    if found.source is not None:
        note += ("\ndesign tokens: nothing is recorded — run /zero:design to "
                 "write %s, so this is reviewable and correctable"
                 % paths.DESIGN_FILE)
    answer = Theme(found.values, found.dark, note)
    _RESOLVED[key] = answer
    return answer


# --------------------------------------------------------------- the interview

#: Tier three (M16-11). What T1 and T2 could not take from a reference document
#: is its prose, and no parser should attempt prose. The agent running
#: /zero:design reads it, proposes a mapping for what is still empty, and the
#: operator confirms each one here before it is written.
#:
#: The brief the agent leaves behind:
#:
#:     {"documents": ["brand-book.html", "DESIGN.md"],
#:      "proposed": [{"name": "font-display",
#:                    "value": "Acme Display, Georgia, serif",
#:                    "why": "DESIGN.md, Typography - headings are set in
#:                            Acme Display"}]}
#:
#: The key is `name` rather than `token` for a reason worth stating: the secret
#: scanner (FR-GEN-04) treats "token" given a quoted literal as a credential,
#: which is correct of every other file in a project and wrong of exactly this
#: one. Renaming the key here means an operator's brief never trips it, rather
#: than every project learning to ignore one line of a security report.
#:
#: Nothing in `proposed` is adopted until its fork is answered. An unanswered
#: token keeps its neutral value AND is reported as unanswered, never as
#: adopted — a proposal is an agent's reading of a sentence, and a document that
#: adopts one unasked has taken a design decision nobody made.
SLUG = "design"

#: The guard that travels with any prose handed to an agent. Reused from the
#: execution contract rather than written a second time: M11-07 established the
#: sentence, and a second one would be a second policy nobody keeps in step.
def guard():
    from . import gauntlet
    return gauntlet.GUARD


class IncompleteProposal(Exception):
    """A proposal that names no token, no value, or no place it came from."""


def _proposals(brief):
    """The proposals in a brief, refused rather than guessed at when malformed.

    A proposal with no `why` is the one that matters: it is an agent asserting a
    value with no sentence of the operator's own document behind it, which is
    indistinguishable from an invention.
    """
    out = []
    for one in brief.get("proposed") or ():
        if not isinstance(one, dict):
            raise IncompleteProposal("a proposal is not a record of fields")
        token, value, why = (one.get("name"), one.get("value"), one.get("why"))
        if token not in tokens.TYPES:
            raise IncompleteProposal(
                "%r is not a token this method's contract defines" % token)
        if not value or not str(value).strip():
            raise IncompleteProposal("%s is proposed with no value" % token)
        if not why or not str(why).strip():
            raise IncompleteProposal(
                "%s is proposed with no place in the document it came from; a "
                "proposal with no sentence behind it cannot be reviewed" % token)
        ok, refused = accepts(token, str(value).strip())
        if not ok:
            raise IncompleteProposal("%s cannot be written: %s" % (token, refused))
        out.append((token, str(value).strip(), str(why).strip()))
    return out


def forks(brief):
    """One question per proposal, and none otherwise.

    The forks are DYNAMIC because the questions are: what a brand book leaves to
    prose differs per brand book. What is fixed is that each one is asked.
    """
    from . import gate
    out = []
    for token, value, why in _proposals(brief):
        out.append(gate.Fork(
            id="confirm:%s" % token,
            question=("%s is not stated as code anywhere in the documents you "
                      "named. Reading the prose, %s looks like %s. Is that "
                      "right?" % (token, token, value)),
            dimension="confirmed:%s" % token,
            options=(
                gate.Option("yes", "Yes, use %s" % value, why, True),
                gate.Option("no", "No, leave %s at the neutral value" % token,
                            "The document does not settle this, and a value "
                            "nobody chose is worse than one plainly not "
                            "adopted", False))))
    return tuple(out)


def open_gate(brief, root=None):
    """The gate this step runs, over whatever is already known."""
    from . import gate
    decisions = gate.load(root, SLUG) if root is not None else ()
    return gate.Gate(SLUG, forks(brief), source=brief, decisions=decisions)


def confirmed(brief, run):
    """The proposals the operator approved, as a record block.

    An answer that is not the yes option is a refusal, whatever it says. The
    operator is allowed an answer no fork predicted, and the safe reading of one
    here is "not confirmed": adopting on an unrecognised answer would be
    adopting on a shrug.
    """
    from . import chain
    out = {}
    for token, value, why in _proposals(brief):
        if chain.choice(run, "confirm:%s" % token) != "yes":
            continue
        out[token] = {"light": value, "from": why + " — confirmed by operator"}
    return out


def unanswered(brief, run):
    """Proposals the operator did not approve. Reported, never adopted."""
    from . import chain
    return [token for token, _, _ in _proposals(brief)
            if chain.choice(run, "confirm:%s" % token) != "yes"]


def author(root, brief, run):
    """Read the named documents, resolve, and write the record.

    Returns (path, record). Writes exactly one file, and only after the gate has
    closed — so a run that is still asking has changed nothing.
    """
    from . import gate
    if not run.closed:
        raise gate.GateNotClosed(
            "%s still has open questions; nothing was written" % SLUG)

    named = [os.path.join(root, one) if not os.path.isabs(one) else one
             for one in brief.get("documents") or ()]
    missing = [one for one in named if not os.path.exists(one)]
    if missing:
        from . import chain
        raise chain.IncompleteBrief(
            "named as a design reference but not found: %s"
            % ", ".join(sorted(missing)))

    found = detect(root, named=named)
    try:
        held = read_record(root)
    except (ValueError, OSError, UnicodeDecodeError):
        held = None
    record = build_record(found, root, held)
    record["confirmed"] = confirmed(brief, run)

    paths.ensure_layout(root)
    run.record(root)
    written = write_record(root, record)
    forget()
    return written, record


def summary(root, record, brief=None, run=None):
    """What the operator is told after a refresh. Every state, named."""
    lines = ["design: %d values recorded in %s"
             % (len(record.get("tokens", {})), paths.DESIGN_FILE)]
    if record.get("confirmed"):
        lines.append("design: %d confirmed from a document's prose"
                     % len(record["confirmed"]))
    if record.get("overrides"):
        lines.append("design: %d operator values carried through untouched"
                     % len(record["overrides"]))
    if record.get("scheme") == "light-dark":
        lines.append("design: a dark counterpart was declared and is used; "
                     "where the host states none the light value is used in "
                     "both schemes, never a value this method invented")
    for one in record.get("refused", ()):
        lines.append("design: refused %s — %s" % (one["token"], one["why"]))
    for one in record.get("clamped", ()):
        lines.append("design: held %s at %s (stated as %s)"
                     % (one["token"], one["now"], one["was"]))
    if brief is not None and run is not None:
        for token in unanswered(brief, run):
            lines.append("design: %s was proposed from prose and NOT confirmed, "
                         "so it keeps the neutral value — this is unanswered, "
                         "not adopted" % token)
    if record.get("unmapped"):
        lines.append("design: %d names nobody claimed, listed in the record"
                     % len(record["unmapped"]))
    return "\n".join(lines)
