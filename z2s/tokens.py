# -*- coding: utf-8 -*-
"""The token contract, the neutral theme, and the block a document carries.

A specification that looks foreign to the project it describes reads as external
paperwork and gets consulted less (ADR-16). So a generated document borrows the
project's own design system where the project has one, and uses a plain neutral
theme where it does not — saying which of the two happened, because a silent
fallback reads as adoption (FR-GEN-03).

CONTRACT is the whole agreement, and everything beside it is a column of the
same table: NEUTRAL gives every name a value, TYPES gives every name a grammar,
SYNONYMS gives every name the words a host project might use for it. The
structural styling may use these names and no others. Four lists, one row per
token, so none of them can drift.

What is NOT here is reading a host project: finding files, merging them,
refusing what must not be written, and recording the result all live in
design.py. This module knows what a token is; that one knows where one came
from. The dependency runs one way only.

Traces: FR-GEN-02, NFR-GEN-01, NFR-GEN-03, NFR-ARC-04, ADR-16.
"""

#: Every token the structural styling is allowed to use, in the order they are
#: written into the document. Ordered rather than sorted so related values stay
#: readable together; fixed either way, which is what determinism needs.
CONTRACT = (
    # Surfaces
    "surface-page", "surface-card", "surface-sunken", "surface-accent",
    # Text
    "text-body", "text-secondary", "text-muted", "text-link", "text-link-hover",
    # The brand, kept apart from the link colour. They are the same value in
    # most systems and different in enough that conflating them made the link
    # colour do brand duty in eight places that are not links.
    "accent", "accent-quiet",
    # Lines
    "border", "border-strong", "focus",
    # The one status the runtime can render: a section it cannot display
    "note", "note-bg",
    # Type
    "font-sans", "font-mono", "font-display",
    "size-h1", "size-h2", "size-h3", "size-body", "size-small", "size-mono",
    "weight-normal", "weight-medium", "weight-semibold", "weight-bold",
    "tracking-tight", "tracking-wide",
    "line-tight", "line-body", "measure",
    # Space and shape
    "space-1", "space-2", "space-3", "space-4", "space-5", "space-6",
    "radius-sm", "radius-md", "radius-lg", "radius-pill",
    "rule", "focus-width", "focus-offset",
    # Depth and motion
    "shadow-tint", "shadow-1", "shadow-2", "duration", "ease",
)

#: What kind of value each token holds. Three readers depend on it: the light
#: and dark writer below (only a colour may go through light-dark()), the value
#: allowlist that decides what a host file is allowed to put in the style block,
#: and the design-token dialects that declare a type of their own.
TYPES = {
    "surface-page": "colour", "surface-card": "colour", "surface-sunken": "colour",
    "surface-accent": "colour",
    "text-body": "colour", "text-secondary": "colour", "text-muted": "colour",
    "text-link": "colour", "text-link-hover": "colour",
    "accent": "colour", "accent-quiet": "colour",
    "border": "colour", "border-strong": "colour", "focus": "colour",
    "note": "colour", "note-bg": "colour", "shadow-tint": "colour",
    "font-sans": "family", "font-mono": "family", "font-display": "family",
    "size-h1": "length", "size-h2": "length", "size-h3": "length",
    "size-body": "length", "size-small": "length", "size-mono": "length",
    "weight-normal": "number", "weight-medium": "number",
    "weight-semibold": "number", "weight-bold": "number",
    "tracking-tight": "length", "tracking-wide": "length",
    "line-tight": "number", "line-body": "number", "measure": "length",
    "space-1": "length", "space-2": "length", "space-3": "length",
    "space-4": "length", "space-5": "length", "space-6": "length",
    "radius-sm": "length", "radius-md": "length", "radius-lg": "length",
    "radius-pill": "length",
    "rule": "length", "focus-width": "length", "focus-offset": "length",
    "shadow-1": "shadow", "shadow-2": "shadow",
    "duration": "duration", "ease": "easing",
}

#: Only a colour may be written as light-dark(): the function is defined for
#: colour values and nothing else, so a dark typeface or a dark spacing step is
#: a thing this contract cannot express and does not pretend to.
COLOURS = frozenset(name for name, kind in TYPES.items() if kind == "colour")

#: The neutral theme. Used whole when a project has no design system, and per
#: token when its design system leaves one undefined.
NEUTRAL = {
    "surface-page": "#f4f4f1",
    "surface-card": "#ffffff",
    "surface-sunken": "#e9e9e4",
    "surface-accent": "#eaeff7",
    "text-body": "#171716",
    "text-secondary": "#4a4a47",
    "text-muted": "#676763",
    "text-link": "#2c4d7a",
    "text-link-hover": "#1e3a5f",
    "accent": "#2c4d7a",
    "accent-quiet": "#4a6892",
    "border": "#d5d5cf",
    "border-strong": "#b4b4ad",
    "focus": "#2c4d7a",
    "note": "#7a4a12",
    "note-bg": "#fbf1e0",
    "font-sans": '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif',
    "font-mono": 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
    # A project with no display face sets its headings in its body face, which
    # is what a neutral theme should do rather than reach for a second one.
    "font-display": '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif',
    "size-h1": "2rem",
    "size-h2": "1.375rem",
    "size-h3": "1.0625rem",
    "size-body": "1rem",
    "size-small": "0.8125rem",
    "size-mono": "0.875rem",
    "weight-normal": "400",
    "weight-medium": "500",
    "weight-semibold": "600",
    "weight-bold": "700",
    "tracking-tight": "-0.02em",
    "tracking-wide": "0.08em",
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
    "radius-pill": "999px",
    "rule": "1px",
    "focus-width": "3px",
    "focus-offset": "2px",
    # The shadow's geometry is one thing and its colour is another. Split so a
    # dark theme can darken the tint without restating the offsets, which is
    # the only way a shadow survives light-dark(): the function takes colours.
    "shadow-tint": "rgba(0,0,0,.06)",
    "shadow-1": "0 1px 2px var(--z2s-shadow-tint), 0 4px 12px var(--z2s-shadow-tint)",
    "shadow-2": "0 2px 4px var(--z2s-shadow-tint), 0 12px 32px var(--z2s-shadow-tint)",
    "duration": "180ms",
    "ease": "cubic-bezier(.22,1,.36,1)",
}

#: The neutral theme's dark counterpart. Written, not derived: inverting a
#: palette by arithmetic guesses at contrast, and NFR-UX-03 pins contrast to a
#: floor rather than to whatever an inversion happens to produce. Every pair
#: here was measured against its own background before it was written down.
#:
#: Nothing in the generator reads this. It is the reference a host system is
#: measured against and the worked example of a COMPLETE dark palette — a
#: project with no design system stays light in a dark browser, deliberately,
#: because a scheme nobody chose is not an improvement on the one they have.
#:
#: It is never used to fill a host's gaps either. Where a system declares dark
#: counterparts for only some colours, tokens.render writes no dark block at
#: all: patching the rest from here would ship a palette half measured against
#: this method's surfaces and half against the project's.
NEUTRAL_DARK = {
    "surface-page": "#1a1a18",
    "surface-card": "#232320",
    "surface-sunken": "#131312",
    "surface-accent": "#1e2a3d",
    "text-body": "#ececea",
    "text-secondary": "#b8b8b3",
    "text-muted": "#93938e",
    "text-link": "#8fb8f0",
    "text-link-hover": "#b8d4ff",
    "accent": "#8fb8f0",
    "accent-quiet": "#7095ca",
    "border": "#383834",
    "border-strong": "#55554f",
    "focus": "#8fb8f0",
    "note": "#e0b077",
    "note-bg": "#2e2415",
    "shadow-tint": "rgba(0,0,0,.5)",
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
    "surface-accent": ("surface-accent", "color-accent-bg", "accent-background",
                       "primary-subtle", "primary-bg", "accent-subtle"),
    "text-body": ("text-body", "color-text", "text", "foreground", "fg",
                  "body-color", "ink", "text-primary"),
    "text-secondary": ("text-secondary", "color-text-secondary", "secondary",
                       "muted-foreground"),
    "text-muted": ("text-muted", "color-muted", "muted", "text-subtle"),
    "text-link": ("text-link", "color-link", "link", "color-primary",
                  "primary", "accent", "color-accent"),
    "text-link-hover": ("text-link-hover", "color-link-hover", "link-hover",
                        "color-primary-hover", "primary-hover", "accent-hover"),
    # Deliberately overlapping with text-link: in most systems the brand IS the
    # link colour, and both tokens taking the same value is the right answer.
    # They are two tokens because in the systems where they differ, conflating
    # them puts a button fill on a paragraph of prose.
    "accent": ("accent", "color-accent", "color-primary", "primary", "brand",
               "color-brand", "brand-primary"),
    "accent-quiet": ("accent-quiet", "accent-muted", "primary-muted",
                     "brand-muted", "color-primary-soft", "primary-soft"),
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
    "font-display": ("font-display", "font-heading", "font-headings",
                     "font-title", "font-family-heading", "font-serif"),
    # The type scale. Until these existed a host could satisfy the whole colour
    # half of the contract and still get the neutral theme's sizes, which is why
    # two very different design systems used to render at identical size.
    "size-h1": ("size-h1", "font-size-h1", "font-size-4xl", "text-4xl",
                "font-size-xxl", "heading-1", "font-size-xxxl"),
    "size-h2": ("size-h2", "font-size-h2", "font-size-2xl", "text-2xl",
                "font-size-xl", "heading-2"),
    "size-h3": ("size-h3", "font-size-h3", "font-size-xl", "text-xl",
                "font-size-lg", "heading-3"),
    "size-body": ("size-body", "font-size-body", "font-size-base", "text-base",
                  "font-size-md", "font-size"),
    "size-small": ("size-small", "font-size-small", "font-size-sm", "text-sm",
                   "font-size-xs"),
    "size-mono": ("size-mono", "font-size-mono", "font-size-code"),
    "weight-normal": ("weight-normal", "font-weight-normal", "font-weight-regular",
                      "weight-regular", "font-weight-400"),
    "weight-medium": ("weight-medium", "font-weight-medium", "font-weight-500"),
    "weight-semibold": ("weight-semibold", "font-weight-semibold",
                        "font-weight-600", "weight-demibold"),
    "weight-bold": ("weight-bold", "font-weight-bold", "font-weight-700"),
    "tracking-tight": ("tracking-tight", "letter-spacing-tight",
                       "letter-spacing-tighter"),
    "tracking-wide": ("tracking-wide", "letter-spacing-wide",
                      "letter-spacing-wider", "tracking-widest"),
    "line-tight": ("line-tight", "line-height-tight", "leading-tight",
                   "line-height-heading"),
    "line-body": ("line-body", "line-height-body", "line-height-base",
                  "leading-normal", "line-height-normal", "line-height"),
    "measure": ("measure", "measure-body", "max-width-prose", "content-width",
                "prose-width", "container-text"),
    # The spacing scale, the other half of what made two systems look alike.
    # Two naming families are read: numbered steps and t-shirt sizes.
    "space-1": ("space-1", "spacing-1", "space-xs", "spacing-xs", "space-025"),
    "space-2": ("space-2", "spacing-2", "space-sm", "spacing-sm"),
    "space-3": ("space-3", "spacing-3", "space-md", "spacing-md", "space-base"),
    "space-4": ("space-4", "spacing-4", "space-lg", "spacing-lg"),
    "space-5": ("space-5", "spacing-5", "space-xl", "spacing-xl"),
    "space-6": ("space-6", "spacing-6", "space-2xl", "spacing-2xl", "space-xxl"),
    "radius-sm": ("radius-sm", "border-radius-sm", "rounded-sm"),
    "radius-md": ("radius-md", "border-radius-md", "border-radius", "radius",
                  "rounded"),
    "radius-lg": ("radius-lg", "border-radius-lg", "rounded-lg"),
    "radius-pill": ("radius-pill", "radius-full", "border-radius-full",
                    "rounded-full", "radius-round", "border-radius-pill"),
    "rule": ("rule", "border-width", "border-width-1", "hairline",
             "border-width-thin"),
    "focus-width": ("focus-width", "focus-ring-width", "ring-width",
                    "outline-width"),
    "focus-offset": ("focus-offset", "focus-ring-offset", "ring-offset",
                     "outline-offset"),
    "shadow-tint": ("shadow-tint", "shadow-color", "color-shadow",
                    "shadow-colour"),
    "shadow-1": ("shadow-1", "shadow-sm", "box-shadow", "shadow", "elevation-1"),
    "shadow-2": ("shadow-2", "shadow-md", "shadow-lg", "elevation-2",
                 "box-shadow-lg"),
    "duration": ("duration", "duration-base", "transition-duration", "motion-duration"),
    "ease": ("ease", "ease-out", "easing", "transition-timing-function"),
}

def missing_dark(dark):
    """The colours a host would still have to declare to get a dark scheme, in
    contract order. Empty when the set is complete."""
    return [name for name in CONTRACT
            if name in COLOURS and not (dark and name in dark)]


def dual(values, dark):
    """Whether a document written from these values carries both schemes.

    Dark is all or nothing. A set covering some of the palette flips those
    tokens and leaves the rest light, so a reader on a dark screen gets
    near-black text on a near-black page — measured on a real project at 5 of
    17 colours declared: 14 text-on-surface combinations below the 4.5:1 floor,
    worst 1.12:1.

    Named here rather than inline in render() because the run report has to say
    the same thing the style block does, and a rule spelled in two places is a
    rule that will eventually be spelled two ways.

    Coverage is judged on what the host DECLARED, not on what differs: a system
    that deliberately carries one colour across both schemes has answered for
    it. At least one colour must actually differ, though — declaring the light
    palette twice is declaring no dark theme.
    """
    if missing_dark(dark):
        return False
    return any(dark[name] != values[name] for name in COLOURS)


def render(values, dark=None):
    """The token block, ready for the document's marked style slot.

    This block is the only place a literal colour, typeface, length or shadow is
    allowed to appear (NFR-GEN-03).

    With no dark values the output is exactly the block this generator has always
    written: one :root, plain values, no colour scheme declared. That is not a
    convenience, it is the promise — a project whose design system says nothing
    about dark gets a document that behaves exactly as it did, because the
    alternative is a dark theme nobody chose and nobody checked the contrast of.

    The same promise decides a PARTIAL set: dark is all or nothing. Unless the
    host declares a counterpart for every colour, this writes the light block
    alone — because a scheme covering some of the palette flips those tokens
    and leaves the rest light, which is a dark theme nobody checked the contrast
    of arriving one colour at a time.

    Given a complete set of dark values, three more things are written:

      * the light block above, unchanged, as the fallback;
      * a light-dark() block guarded by @supports, so a browser that does not
        know the function keeps the plain values rather than dropping the whole
        declaration and rendering an unstyled page;
      * [data-theme] rules, which cost two lines because color-scheme is already
        declared and give a reader a way to force one scheme.

    Only colours are written as pairs: light-dark() is defined for colour values
    and nothing else. A dark value on any other token is not written here, and
    the caller that read it is the one that reports so.
    """
    lines = ["  --z2s-%s: %s;" % (name, values[name]) for name in CONTRACT]
    block = ":root {\n" + "\n".join(lines) + "\n}\n"

    if not dual(values, dark):
        return block

    paired = [name for name in CONTRACT
              if name in COLOURS and dark[name] != values[name]]
    pairs = ["  --z2s-%s: light-dark(%s, %s);" % (name, values[name], dark[name])
             for name in paired]
    return block + (
        "@supports (color: light-dark(#000, #fff)) {\n"
        ":root {\n  color-scheme: light dark;\n" + "\n".join(pairs) + "\n}\n"
        "[data-theme=\"light\"] { color-scheme: light }\n"
        "[data-theme=\"dark\"] { color-scheme: dark }\n"
        "}\n"
        # Paper is light. Without this a reader on a dark screen prints a page
        # of black ink, which is a real cost to a real person and is the sort of
        # thing only a browser tells you (M16).
        "@media print { :root { color-scheme: light } }\n")
