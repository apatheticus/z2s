# -*- coding: utf-8 -*-
"""The token contract, the neutral theme, and adoption of a host design system.

A specification that looks foreign to the project it describes reads as external
paperwork and gets consulted less (ADR-16). So a generated document borrows the
project's own colours and typefaces where the project has them, and uses a plain
neutral theme where it does not — saying which of the two happened, because a
silent fallback reads as adoption (FR-GEN-03).

CONTRACT is the whole agreement. The structural styling may use these names and
no others; the neutral theme defines all of them; a host design system is mapped
onto them. One list, three users, so none of the three can drift.

Traces: FR-GEN-02, NFR-GEN-01, NFR-GEN-03, NFR-ARC-04, ADR-16.
"""

import os
import re

#: Every token the structural styling is allowed to use, in the order they are
#: written into the document. Ordered rather than sorted so related values stay
#: readable together; fixed either way, which is what determinism needs.
CONTRACT = (
    # Surfaces
    "surface-page", "surface-card", "surface-sunken",
    # Text
    "text-body", "text-secondary", "text-muted", "text-link", "text-inverse",
    # Lines
    "border", "border-strong", "focus",
    # The one status the runtime can render: a section it cannot display
    "note", "note-bg",
    # Type
    "font-sans", "font-mono",
    "size-h1", "size-h2", "size-h3", "size-body", "size-small", "size-mono",
    "line-tight", "line-body", "measure",
    # Space and shape
    "space-1", "space-2", "space-3", "space-4", "space-5", "space-6",
    "radius-sm", "radius-md", "radius-lg",
    "rule", "focus-width", "focus-offset",
    # Depth and motion
    "shadow-1", "duration", "ease",
)

#: The neutral theme. Used whole when a project has no design system, and per
#: token when its design system leaves one undefined.
NEUTRAL = {
    "surface-page": "#f4f4f1",
    "surface-card": "#ffffff",
    "surface-sunken": "#e9e9e4",
    "text-body": "#171716",
    "text-secondary": "#4a4a47",
    "text-muted": "#6b6b67",
    "text-link": "#2c4d7a",
    "text-inverse": "#ffffff",
    "border": "#d5d5cf",
    "border-strong": "#b4b4ad",
    "focus": "#2c4d7a",
    "note": "#7a4a12",
    "note-bg": "#fbf1e0",
    "font-sans": '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif',
    "font-mono": 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
    "size-h1": "2rem",
    "size-h2": "1.375rem",
    "size-h3": "1.0625rem",
    "size-body": "1rem",
    "size-small": "0.8125rem",
    "size-mono": "0.875rem",
    "line-tight": "1.2",
    "line-body": "1.6",
    "measure": "68ch",
    "space-1": "0.25rem",
    "space-2": "0.5rem",
    "space-3": "1rem",
    "space-4": "1.5rem",
    "space-5": "2rem",
    "space-6": "3rem",
    "radius-sm": "3px",
    "radius-md": "6px",
    "radius-lg": "12px",
    "rule": "1px",
    "focus-width": "3px",
    "focus-offset": "2px",
    "shadow-1": "0 1px 2px rgba(0,0,0,.06), 0 4px 12px rgba(0,0,0,.06)",
    "duration": "180ms",
    "ease": "cubic-bezier(.22,1,.36,1)",
}

#: Names a host design system might use for each contract token, best first.
#: Only these are adopted: a system that names nothing recognisable is not being
#: rejected, it is simply not a design system this mapper can read, and saying
#: so beats guessing.
SYNONYMS = {
    "surface-page": ("surface-page", "color-background", "background", "bg",
                     "page-background", "body-bg", "background-color"),
    "surface-card": ("surface-card", "color-surface", "surface", "card",
                     "panel", "card-background"),
    "surface-sunken": ("surface-sunken", "surface-muted", "sunken", "subtle",
                       "muted-background"),
    "text-body": ("text-body", "color-text", "text", "foreground", "fg",
                  "body-color", "ink", "text-primary"),
    "text-secondary": ("text-secondary", "color-text-secondary", "secondary",
                       "muted-foreground"),
    "text-muted": ("text-muted", "color-muted", "muted", "text-subtle"),
    "text-link": ("text-link", "color-link", "link", "color-primary",
                  "primary", "accent", "color-accent"),
    "text-inverse": ("text-inverse", "color-text-inverse", "on-primary",
                     "text-on-dark"),
    "border": ("border", "color-border", "border-default", "divider",
               "border-color"),
    "border-strong": ("border-strong", "border-hover", "border-emphasis"),
    "focus": ("focus", "color-focus", "border-focus", "focus-ring", "ring",
              "outline-color"),
    "note": ("note", "color-warning", "warning", "status-warning", "caution"),
    "note-bg": ("note-bg", "color-warning-bg", "warning-background",
                "status-warning-bg"),
    "font-sans": ("font-sans", "font-family", "font-body", "font-base", "font"),
    "font-mono": ("font-mono", "font-code", "font-family-mono"),
    "radius-sm": ("radius-sm", "border-radius-sm", "rounded-sm"),
    "radius-md": ("radius-md", "border-radius", "radius", "rounded"),
    "radius-lg": ("radius-lg", "border-radius-lg", "rounded-lg"),
    "shadow-1": ("shadow-1", "shadow-sm", "box-shadow", "shadow", "elevation-1"),
    "duration": ("duration", "duration-base", "transition-duration", "motion-duration"),
    "ease": ("ease", "ease-out", "easing", "transition-timing-function"),
}

#: A file is a design system only if it declares at least this many of the
#: tokens the contract asks for. One stray custom property in an ordinary
#: stylesheet is not a design system.
THRESHOLD = 4

#: Directories never searched. Vendored copies of somebody else's design system
#: are not this project's design system.
SKIP = frozenset((".git", "node_modules", "vendor", "dist", "build", "__pycache__",
                  ".venv", "venv", ".zero", ".claude"))

_DECLARATION = re.compile(r"--([a-zA-Z0-9_-]+)\s*:\s*([^;{}]+)")
_REFERENCE = re.compile(r"var\(\s*--([a-zA-Z0-9_-]+)\s*(?:,[^)]*)?\)")


def _harvest(text):
    """Every custom property a stylesheet declares, as name -> value."""
    return {name: value.strip() for name, value in _DECLARATION.findall(text)}


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


def _map_onto_contract(declared):
    """Translate one project's token names into contract names."""
    lowered = {name.lower(): name for name in sorted(declared)}
    found = {}
    for token in CONTRACT:
        for candidate in SYNONYMS.get(token, ()):
            if candidate in lowered:
                found[token] = _resolve(declared[lowered[candidate]], declared)
                break
    return found


def _candidates(root):
    """Stylesheets worth reading, in a fixed order (NFR-GEN-01)."""
    out = []
    for folder, subfolders, names in os.walk(root):
        subfolders[:] = sorted(name for name in subfolders if name not in SKIP)
        for name in sorted(names):
            if name.endswith((".css", ".scss")):
                out.append(os.path.join(folder, name))
    return out


def detect(root):
    """Find the host project's design tokens.

    Returns (tokens, source): a complete contract-satisfying token set, and the
    path adopted from, or None when the neutral theme was used. The file that
    maps the most contract tokens wins; ties break on path, so the answer does
    not depend on the order the filesystem happens to return.
    """
    best, best_source = {}, None
    for path in _candidates(root):
        try:
            with open(path, encoding="utf-8") as handle:
                declared = _harvest(handle.read())
        except (OSError, UnicodeDecodeError):
            continue
        mapped = _map_onto_contract(declared)
        if len(mapped) >= THRESHOLD and len(mapped) > len(best):
            best, best_source = mapped, path

    resolved = dict(NEUTRAL)
    resolved.update(best)
    return resolved, best_source


def report(source):
    """One line for the run report, naming what actually happened."""
    if source is None:
        return ("design tokens: no design system found; the neutral theme was used")
    return "design tokens: adopted from %s" % source


def render(values):
    """The token block, ready for the document's marked style slot.

    This block is the only place a literal colour, typeface, length or shadow is
    allowed to appear (NFR-GEN-03).
    """
    lines = ["  --z2s-%s: %s;" % (name, values[name]) for name in CONTRACT]
    return ":root {\n" + "\n".join(lines) + "\n}\n"
