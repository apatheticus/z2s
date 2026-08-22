# -*- coding: utf-8 -*-
"""Token adoption with a neutral fallback (M1-P3-T1).

A generated document should look like part of the project it describes, so the
generator reads that project's design tokens and inlines them. When the project
has no design system the document uses a neutral theme and the run says so —
never silently, because a silent fallback reads as adoption (FR-GEN-03).

Traces: FR-GEN-02, NFR-GEN-03, NFR-ARC-04, ADR-16.
"""

import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import design, styles, tokens


def project(**files):
    """Build a throwaway project directory and return its path."""
    root = tempfile.mkdtemp(prefix="z2s-tokens-")
    for name, body in sorted(files.items()):
        path = os.path.join(root, name)
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(body)
    return root


HOST_CSS = """
:root {
  --color-background: #101014;
  --color-surface: #1b1b22;
  --color-text: #f2f2f5;
  --color-muted: #9b9ba6;
  --color-primary: #7cc4ff;
  --color-border: #2f2f3a;
  --font-family: "Host Grotesk", sans-serif;
  --font-mono: "Host Mono", monospace;
}
"""


class TestTheContractIsOneDeclaredThing(unittest.TestCase):
    """M16-P1-T1. The refactor step: fallback and mapper satisfy the same
    published list, in both directions."""

    def test_the_neutral_theme_supplies_every_contract_token(self):
        missing = [name for name in tokens.CONTRACT if name not in tokens.NEUTRAL]
        self.assertEqual([], missing)

    def test_the_neutral_theme_supplies_nothing_outside_the_contract(self):
        extra = [name for name in tokens.NEUTRAL if name not in tokens.CONTRACT]
        self.assertEqual([], extra)

    def test_every_token_the_structural_styling_uses_is_in_the_contract(self):
        """Structural styling may not invent a token the contract does not define,
        or a host project could satisfy the contract and still get a broken page."""
        used = set(re.findall(r"var\((--z2s-[a-z0-9-]+)", styles.STRUCT))
        declared = set("--z2s-" + name for name in tokens.CONTRACT)
        self.assertEqual(set(), used - declared)

    def test_every_token_the_contract_declares_is_used_by_the_structural_styling(self):
        """The other direction, and the one that keeps the contract honest.

        Without it a token can be declared, given a neutral value, written into
        every document ever generated, and referenced by nothing. It costs bytes
        in every file, and worse: a host project's value adopted onto it changes
        nothing a reader can see, so adoption is reported and nothing happens.
        Widening the contract without this check manufactures that defect once
        per token added.

        Reachability is transitive, because one token may be spent inside
        another's value: a shadow's geometry is written once and its colour is a
        token of its own, so that a dark theme can restate the colour without
        restating the offsets. shadow-tint is therefore reached through shadow-1
        rather than directly, and that is a real use. What the check refuses is
        a token nothing reaches at all, by any route.
        """
        declared = set("--z2s-" + name for name in tokens.CONTRACT)
        reached = set(re.findall(r"var\((--z2s-[a-z0-9-]+)", styles.STRUCT))
        # Close over the token values themselves, which ship in every document.
        # Bounded by the contract's own size: each pass adds at least one name
        # or stops.
        for _ in range(len(tokens.CONTRACT)):
            grown = set(reached)
            for name in reached:
                value = tokens.NEUTRAL.get(name[len("--z2s-"):], "")
                grown.update(re.findall(r"var\((--z2s-[a-z0-9-]+)", value))
            if grown == reached:
                break
            reached = grown
        self.assertEqual(set(), declared - reached)


    def test_every_contract_token_can_actually_be_adopted(self):
        """The defect this milestone exists to fix, as a check.

        A token with no entry in SYNONYMS is pinned to the neutral value for the
        life of the project: no host design system, however complete, can ever
        reach it. Eighteen of thirty-nine were in that state, and among them were
        the whole type scale and the whole spacing scale — which is why a
        Swiss-minimal system and a brutalist one used to render at identical
        size, rhythm and density while the run reported adoption.
        """
        unreachable = [name for name in tokens.CONTRACT
                       if not tokens.SYNONYMS.get(name)]
        self.assertEqual([], unreachable)

    def test_every_token_states_what_kind_of_value_it_holds(self):
        """TYPES is read by the light-and-dark writer and by the value
        allowlist. A token missing from it has no grammar, so nothing can say
        whether what a host file offered is even the right sort of thing."""
        self.assertEqual(sorted(tokens.CONTRACT), sorted(tokens.TYPES))


class TestLightAndDark(unittest.TestCase):
    """M16-P1-T2. The scheme is adopted, never invented."""

    def test_no_dark_values_means_the_block_is_exactly_what_it_always_was(self):
        """The promise that makes this safe to ship. A project whose design
        system says nothing about dark gets a document that behaves precisely as
        it did — no colour scheme declared, no light-dark(), same bytes."""
        plain = tokens.render(tokens.NEUTRAL)
        self.assertNotIn("light-dark(", plain)
        self.assertNotIn("color-scheme", plain)
        self.assertEqual(plain, tokens.render(tokens.NEUTRAL, {}))
        self.assertEqual(plain, tokens.render(tokens.NEUTRAL, None))

    def test_a_dark_value_equal_to_the_light_one_is_not_a_dark_theme(self):
        """Never synthesise: a host that declares the same value for both has
        declared no dark counterpart, and pairing it would claim otherwise."""
        same = {name: tokens.NEUTRAL[name] for name in tokens.COLOURS}
        self.assertEqual(tokens.render(tokens.NEUTRAL),
                         tokens.render(tokens.NEUTRAL, same))

    def test_dark_values_produce_a_guarded_block_and_a_print_rule(self):
        block = tokens.render(tokens.NEUTRAL, tokens.NEUTRAL_DARK)
        self.assertIn("@supports (color: light-dark(#000, #fff))", block)
        self.assertIn("color-scheme: light dark", block)
        self.assertIn('[data-theme="dark"] { color-scheme: dark }', block)
        self.assertIn("@media print { :root { color-scheme: light } }", block)

    def test_the_plain_values_survive_as_the_fallback(self):
        """A browser that does not know light-dark() drops the declaration, so
        the unguarded block above it has to carry a complete theme or the page
        renders unstyled."""
        block = tokens.render(tokens.NEUTRAL, tokens.NEUTRAL_DARK)
        first = block.split("@supports")[0]
        for name in tokens.CONTRACT:
            self.assertIn("--z2s-%s:" % name, first)

    def test_only_colours_are_written_as_pairs(self):
        """light-dark() is defined for colour values and nothing else, so a dark
        typeface or a dark spacing step is silently unrepresentable — and has to
        be dropped here rather than written into a declaration browsers void."""
        dark = dict(tokens.NEUTRAL_DARK)
        dark["size-h1"] = "4rem"
        dark["font-sans"] = "Some Dark Face"
        block = tokens.render(tokens.NEUTRAL, dark)
        self.assertNotIn("light-dark(2rem", block)
        self.assertNotIn("Some Dark Face", block)

    def test_the_written_dark_theme_names_only_colours(self):
        outside = [name for name in tokens.NEUTRAL_DARK
                   if name not in tokens.COLOURS]
        self.assertEqual([], outside)

    def test_the_dark_theme_covers_every_colour_the_contract_has(self):
        """A half-covered dark theme is worse than none: the covered tokens
        flip and the rest stay light, so a dark reader gets black text on a
        black card."""
        missing = [name for name in tokens.COLOURS
                   if name not in tokens.NEUTRAL_DARK]
        self.assertEqual([], missing)

    def test_a_partial_dark_set_is_not_a_dark_theme(self):
        """The rule this generator is here to keep. Declaring a dark
        counterpart for SOME colours used to hand the whole root to
        color-scheme: light dark while every unpaired colour kept its light
        value, so a dark reader got near-black text on a near-black page.
        Measured on a real project: 5 of 17 colours declared, 14 text-on-surface
        combinations below the 4.5:1 floor, worst 1.12:1."""
        partial = {name: tokens.NEUTRAL_DARK[name]
                   for name in ("surface-page", "surface-card", "text-body",
                                "accent-quiet", "note")}
        self.assertEqual(tokens.render(tokens.NEUTRAL),
                         tokens.render(tokens.NEUTRAL, partial))

    def test_one_missing_colour_is_still_a_partial_set(self):
        """All or nothing means all. Sixteen of seventeen leaves one token
        light on a dark page — the same defect at a smaller size, and the size
        is not what makes it a defect."""
        nearly = dict(tokens.NEUTRAL_DARK)
        del nearly["shadow-tint"]
        self.assertEqual(tokens.render(tokens.NEUTRAL),
                         tokens.render(tokens.NEUTRAL, nearly))

    def test_a_colour_reused_in_both_schemes_still_counts_as_declared(self):
        """Coverage is judged on what the host DECLARED, not on what differs.
        A system that deliberately carries one colour across both schemes has
        answered for it, and reading that as a gap would refuse a theme that is
        complete."""
        dark = dict(tokens.NEUTRAL_DARK)
        dark["shadow-tint"] = tokens.NEUTRAL["shadow-tint"]
        block = tokens.render(tokens.NEUTRAL, dark)
        self.assertIn("color-scheme: light dark", block)
        self.assertNotIn("--z2s-shadow-tint: light-dark(", block)


def luminance(colour):
    """Relative luminance, WCAG 2.x. Twelve lines rather than a dependency:
    NFR-ARC-03 allows the standard library and browser built-ins, and this is
    arithmetic out of a published formula."""
    hexed = colour.lstrip("#")
    channels = [int(hexed[at:at + 2], 16) / 255.0 for at in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
              for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(one, other):
    """The ratio between two colours, lighter over darker."""
    first, second = sorted((luminance(one), luminance(other)), reverse=True)
    return (first + 0.05) / (second + 0.05)


class TestTheContrastFloor(unittest.TestCase):
    """NFR-UX-03 pins contrast to a floor. The floor is checked here, on the
    values themselves, because that is the only place it can be checked without
    a browser and the palettes are what drift."""

    #: Every token that ends up as text, and every token that ends up behind
    #: it. Checked as a full cross-product rather than against the stylesheet's
    #: current pairings: a usage map goes stale the next time a rule is added,
    #: and a colour that clears the floor everywhere can be used anywhere.
    TEXT = ("text-body", "text-secondary", "text-muted", "text-link",
            "text-link-hover", "accent", "accent-quiet", "note")
    SURFACES = ("surface-page", "surface-card", "surface-sunken",
                "surface-accent", "note-bg")
    FLOOR = 4.5

    def check(self, palette, label):
        failures = ["%s: %s on %s is %.2f:1"
                    % (label, ink, ground, contrast(palette[ink], palette[ground]))
                    for ink in self.TEXT for ground in self.SURFACES
                    if contrast(palette[ink], palette[ground]) < self.FLOOR]
        self.assertEqual([], failures)

    def test_the_neutral_theme_clears_the_floor(self):
        self.check(tokens.NEUTRAL, "NEUTRAL")

    def test_the_dark_theme_clears_the_floor(self):
        self.check(tokens.NEUTRAL_DARK, "NEUTRAL_DARK")


class TestHostTokensAreAdopted(unittest.TestCase):
    """M1-P3-T1-C1."""

    def setUp(self):
        self.root = project(**{"styles/theme.css": HOST_CSS})
        found = design.detect(self.root)
        self.tokens, self.source = found.values, found.source

    def test_the_host_values_reach_the_style_block(self):
        block = tokens.render(self.tokens)
        self.assertIn("#f2f2f5", block)          # its text colour
        self.assertIn("#101014", block)          # its page colour
        self.assertIn("Host Grotesk", block)     # its typeface

    def test_the_run_names_the_file_it_adopted(self):
        self.assertIsNotNone(self.source)
        self.assertIn("theme.css", design.report(self.source))

    def test_a_token_the_host_does_not_define_falls_back_individually(self):
        """Adoption is per token. A host system that defines colour but no shadow
        gets its colours, not a half-styled document."""
        self.assertEqual(tokens.NEUTRAL["shadow-1"], self.tokens["shadow-1"])

    def test_the_result_still_satisfies_the_whole_contract(self):
        missing = [name for name in tokens.CONTRACT if name not in self.tokens]
        self.assertEqual([], missing)


class TestTheNeutralFallbackIsAnnounced(unittest.TestCase):
    """M1-P3-T1-C2."""

    def setUp(self):
        self.root = project(**{"README.md": "A project with no design system.\n"})
        found = design.detect(self.root)
        self.tokens, self.source = found.values, found.source

    def test_no_design_system_means_the_neutral_theme(self):
        self.assertIsNone(self.source)
        self.assertEqual(tokens.NEUTRAL, self.tokens)

    def test_the_run_says_it_fell_back(self):
        line = design.report(self.source)
        self.assertIn("neutral", line.lower())
        self.assertNotIn("adopted", line.lower())

    def test_a_stylesheet_with_no_recognisable_token_is_not_claimed_as_adoption(self):
        """A file full of ordinary CSS rules is not a design system. Claiming it
        would report a fallback as an adoption, which FR-GEN-03 forbids."""
        root = project(**{"site.css": "body { margin: 0 }\n.header { display: flex }\n"})
        adopted = design.detect(root)
        found, source = adopted.values, adopted.source
        self.assertIsNone(source)
        self.assertEqual(tokens.NEUTRAL, found)

    def test_one_stray_custom_property_is_not_a_design_system(self):
        """The harder case: a stylesheet that does declare a variable or two.
        Below the threshold this is one developer's shortcut, and adopting it
        would produce a document coloured by an accident."""
        root = project(**{"site.css": ":root { --border: #ccc; --radius: 4px }\n"})
        adopted = design.detect(root)
        found, source = adopted.values, adopted.source
        self.assertIsNone(source)
        self.assertEqual(tokens.NEUTRAL["border"], found["border"])

    def test_a_system_that_clears_the_threshold_is_adopted(self):
        """The pair that makes the test above mean something: the same shape of
        file, with enough of the contract named, is adopted."""
        root = project(**{"site.css": ":root { --color-background: #fff; --color-text: #111;"
                                      " --color-border: #ccc; --color-primary: #05f }\n"})
        adopted = design.detect(root)
        found, source = adopted.values, adopted.source
        self.assertIsNotNone(source)
        self.assertEqual("#111", found["text-body"])


class TestDetectionIsDeterministic(unittest.TestCase):
    """NFR-GEN-01: two runs over the same project produce the same document."""

    def test_two_candidate_stylesheets_resolve_the_same_way_every_time(self):
        root = project(**{"a/one.css": HOST_CSS,
                          "b/two.css": HOST_CSS.replace("#f2f2f5", "#eeeeee")})
        first = design.detect(root)
        for _ in range(5):
            self.assertEqual(first, design.detect(root))


class TestNoLiteralsOutsideTheTokenBlock(unittest.TestCase):
    """M1-P3-T1-C3 / NFR-GEN-03. Enforced by a check, not by convention."""

    def body_of_the_stylesheet(self):
        """Everything a document's <style> holds except the token block itself,
        with media-query conditions removed — a breakpoint cannot be a variable,
        so its pixel value is not a hard-coded style."""
        text = styles.STRUCT
        return re.sub(r"@media[^{]*", "@media ", text)

    def test_no_colour_literal(self):
        text = self.body_of_the_stylesheet()
        found = re.findall(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(", text)
        self.assertEqual([], found)

    def test_no_typeface_literal(self):
        text = self.body_of_the_stylesheet()
        found = [value for value in re.findall(r"font-family\s*:\s*([^;}]+)", text)
                 if "var(" not in value and value.strip() != "inherit"]
        self.assertEqual([], found)

    def test_no_shadow_literal(self):
        text = self.body_of_the_stylesheet()
        found = [rule for rule in re.findall(r"box-shadow\s*:\s*([^;}]+)", text)
                 if "var(" not in rule and rule.strip() != "none"]
        self.assertEqual([], found)

    def test_no_hard_coded_length(self):
        """NFR-GEN-03 names spacing alongside colour, so lengths go through the
        contract too. Zero needs no unit and is therefore not a literal."""
        text = self.body_of_the_stylesheet()
        found = re.findall(r"(?<![\w-])\d*\.?\d+(?:px|rem|em|ch)\b", text)
        self.assertEqual([], found)

    def test_the_check_notices_a_literal_that_is_introduced(self):
        """The guard above is only worth having if it fails when it should."""
        text = "@media print { .card { color: #ff0000; padding: 4px } }"
        stripped = re.sub(r"@media[^{]*", "@media ", text)
        self.assertTrue(re.findall(r"#[0-9a-fA-F]{3,8}\b", stripped))
        self.assertTrue(re.findall(r"(?<![\w-])\d*\.?\d+(?:px|rem|em|ch)\b", stripped))


if __name__ == "__main__":
    unittest.main()
