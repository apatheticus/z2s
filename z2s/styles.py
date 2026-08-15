# -*- coding: utf-8 -*-
"""Structural styling: one stylesheet, shared by every document.

This is the half of a document's appearance that never varies. It is never
copied or edited per project (NFR-ARC-04) — a project changes how a document
looks by changing its tokens, not by forking this file.

Every value here resolves through a contract token. No colour, typeface, shadow
or length is written literally (NFR-GEN-03), with one exception the language
forces: a media query's breakpoint, which cannot be a variable.

The accessibility floor lives here rather than in any generator, so no document
can opt out of it: a visible focus outline (NFR-UX-01), motion suppressed on
request (NFR-UX-02), and status carried by words and shape rather than colour
alone (NFR-UX-03).

Traces: FR-GEN-06, FR-SPC-11, NFR-UX-01, NFR-UX-02, NFR-UX-03, NFR-UX-05,
NFR-GEN-03, NFR-ARC-04.
"""

STRUCT = r"""
*, *::before, *::after { box-sizing: border-box }

html { -webkit-text-size-adjust: 100% }

body {
  margin: 0;
  background: var(--z2s-surface-page);
  color: var(--z2s-text-body);
  font-family: var(--z2s-font-sans);
  font-size: var(--z2s-size-body);
  line-height: var(--z2s-line-body);
  overflow-wrap: break-word;
}

/* One visible focus indicator for everything, defined once. An outline is used
   rather than a colour or shadow swap because it survives a dark theme and is
   the one affordance a forced-colours mode preserves (NFR-UX-01). */
:focus-visible {
  outline: var(--z2s-focus-width) solid var(--z2s-focus);
  outline-offset: var(--z2s-focus-offset);
}

a { color: var(--z2s-text-link) }
a:hover { text-decoration-thickness: var(--z2s-focus-offset) }

code, pre { font-family: var(--z2s-font-mono); font-size: var(--z2s-size-mono) }
pre {
  overflow-x: auto;
  padding: var(--z2s-space-3);
  background: var(--z2s-surface-sunken);
  border-radius: var(--z2s-radius-md);
}
pre code { font-size: inherit }

#doc {
  max-width: var(--z2s-measure);
  margin: 0 auto;
  padding: var(--z2s-space-5) var(--z2s-space-3) var(--z2s-space-6);
}

/* ------------------------------------------------------------------- hero */
/* Type, version, status and scope sit above the fold so a reader can place the
   document without scrolling (NFR-UX-04). */

.hero { margin-bottom: var(--z2s-space-5) }
.hero .kicker {
  margin: 0;
  color: var(--z2s-text-secondary);
  font-size: var(--z2s-size-small);
  letter-spacing: var(--z2s-focus-offset);
  text-transform: uppercase;
}
.hero h1 {
  margin: var(--z2s-space-2) 0 0;
  font-size: var(--z2s-size-h1);
  line-height: var(--z2s-line-tight);
}
.hero .lead { margin: var(--z2s-space-3) 0 0; color: var(--z2s-text-secondary) }
.hero .meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--z2s-space-2) var(--z2s-space-4);
  margin: var(--z2s-space-4) 0 0;
  padding: var(--z2s-space-3) 0 0;
  border-top: var(--z2s-rule) solid var(--z2s-border);
  font-size: var(--z2s-size-small);
}
.hero .meta dt { color: var(--z2s-text-muted) }
.hero .meta dd { margin: 0; font-weight: 600 }

/* --------------------------------------------------------------- contents */

.contents {
  margin-bottom: var(--z2s-space-5);
  padding: var(--z2s-space-3);
  background: var(--z2s-surface-card);
  border: var(--z2s-rule) solid var(--z2s-border);
  border-radius: var(--z2s-radius-lg);
}
.contents h2 { margin: 0 0 var(--z2s-space-2); font-size: var(--z2s-size-small);
               text-transform: uppercase; color: var(--z2s-text-muted) }
.contents ol { margin: 0; padding: 0; list-style: none }
.contents a {
  display: flex;
  gap: var(--z2s-space-2);
  padding: var(--z2s-space-1) 0;
  color: var(--z2s-text-body);
  text-decoration: none;
  transition: color var(--z2s-duration) var(--z2s-ease);
}
.contents a:hover { text-decoration: underline }
/* The section in view is marked by weight and a rule as well as by colour, so
   the mark survives a reader who cannot distinguish the two colours. */
.contents a.active { color: var(--z2s-text-link); font-weight: 700 }
.contents a.active .number { text-decoration: underline }
.number { color: var(--z2s-text-muted); font-family: var(--z2s-font-mono);
          font-size: var(--z2s-size-small) }

/* Aggregate review progress, and the tick beside each section. A reviewer's
   own working state, never part of the specification (FR-SPC-08). */
.progress {
  margin: var(--z2s-space-2) 0 0;
  color: var(--z2s-text-muted);
  font-size: var(--z2s-size-small);
}
.review {
  display: inline-flex;
  gap: var(--z2s-space-2);
  align-items: center;
  margin: 0 0 var(--z2s-space-3);
  color: var(--z2s-text-secondary);
  font-size: var(--z2s-size-small);
  cursor: pointer;
}

/* How much of the BUILD is finished, which is a different question from how
   much of the document this reader has read, and is deliberately styled and
   named differently so the two are never mistaken for one another (FR-STA-04).
   Worked out at render time and stored nowhere. */
.rollup {
  display: flex;
  gap: var(--z2s-space-2);
  align-items: center;
  margin: var(--z2s-space-2) 0 var(--z2s-space-3);
  color: var(--z2s-text-muted);
  font-size: var(--z2s-size-small);
}
.rollup .bar {
  flex: none;
  /* Sized in the contract's own spacing steps rather than in a length of its
     own: a host design system with a larger scale gets a proportionally larger
     bar, which is the whole point of the token contract (NFR-GEN-03). */
  width: calc(var(--z2s-space-6) * 3);
  height: var(--z2s-space-2);
  border-radius: var(--z2s-radius-lg);
  background: var(--z2s-border);
  overflow: hidden;
}
.rollup .fill { display: block; height: 100%; background: var(--z2s-text-link) }
.rollup .figures { font-family: var(--z2s-font-mono) }

/* Everything still waiting on a person, gathered at the top of the work it
   belongs to so a reviewer clears it in one pass (FR-STA-08). */
.queue {
  margin: 0 0 var(--z2s-space-4);
  padding: var(--z2s-space-3);
  border: var(--z2s-rule) solid var(--z2s-border);
  border-radius: var(--z2s-radius-md);
}
.queue > summary { cursor: pointer; font-size: var(--z2s-size-small) }
.queue ul { margin: var(--z2s-space-2) 0 0; padding-left: var(--z2s-space-4) }
.queue li { margin: 0 0 var(--z2s-space-1); font-size: var(--z2s-size-small) }
.queue .unit { color: var(--z2s-text-muted); font-family: var(--z2s-font-mono) }

/* --------------------------------------------------------------- sections */

.section { margin: 0 0 var(--z2s-space-6) }
.section > h2 {
  display: flex;
  gap: var(--z2s-space-2);
  align-items: baseline;
  margin: 0 0 var(--z2s-space-3);
  padding-bottom: var(--z2s-space-2);
  border-bottom: var(--z2s-rule) solid var(--z2s-border);
  font-size: var(--z2s-size-h2);
  line-height: var(--z2s-line-tight);
}
/* The section's own count, pushed to the far end of the heading rule so it reads
   as a measurement of the section rather than as part of its name. */
.section > h2 .tally {
  margin-left: auto;
  color: var(--z2s-text-muted);
  font-family: var(--z2s-font-mono);
  font-size: var(--z2s-size-small);
  font-weight: 400;
  white-space: nowrap;
}
.section h3 { font-size: var(--z2s-size-h3); margin: 0 0 var(--z2s-space-1) }
.section p { margin: 0 0 var(--z2s-space-3) }
.section .lede { color: var(--z2s-text-secondary) }
.section ul, .section ol { margin: 0 0 var(--z2s-space-3); padding-left: var(--z2s-space-4) }
.section li { margin-bottom: var(--z2s-space-1) }

.section dl { margin: 0 0 var(--z2s-space-3) }
.section dt { font-weight: 700 }
.section dd { margin: 0 0 var(--z2s-space-2); color: var(--z2s-text-secondary) }

table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  margin: 0 0 var(--z2s-space-3);
  font-size: var(--z2s-size-small);
}
th, td {
  padding: var(--z2s-space-2);
  border-bottom: var(--z2s-rule) solid var(--z2s-border);
  text-align: left;
  vertical-align: top;
}
th { background: var(--z2s-surface-sunken) }

.cards, .stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--z2s-space-3);
  margin: 0 0 var(--z2s-space-3);
}
.card, .stat {
  padding: var(--z2s-space-3);
  background: var(--z2s-surface-card);
  border: var(--z2s-rule) solid var(--z2s-border);
  border-radius: var(--z2s-radius-md);
  box-shadow: var(--z2s-shadow-1);
}
.card p:last-child { margin-bottom: 0 }
.card .kicker {
  margin: 0 0 var(--z2s-space-1);
  color: var(--z2s-text-muted);
  font-size: var(--z2s-size-small);
  text-transform: uppercase;
}
.card ul { margin: 0; padding-left: var(--z2s-space-4) }
.card ul:not(:last-child) { margin-bottom: var(--z2s-space-3) }
.stat dt { color: var(--z2s-text-muted); font-size: var(--z2s-size-small);
           font-weight: 400; order: 2 }
.stat dd { margin: 0; font-size: var(--z2s-size-h2); font-weight: 700; order: 1 }
.stat { display: flex; flex-direction: column }

/* The requirements catalogue. Grouped by area, one entry per requirement, with
   the priority band shown as a word beside its colour: a reader who cannot see
   the colour still reads "Must" (NFR-UX-03). */
.catalogue .area { margin: 0 0 var(--z2s-space-4) }
/* The rule that separates one area from the next belongs to the whole heading
   row, not to the words in it: the heading sits inline beside the fold marker,
   so a border on the heading itself underlines the words and stops. */
.catalogue .area > summary {
  padding-bottom: var(--z2s-space-2);
  border-bottom: var(--z2s-rule) solid var(--z2s-border-strong);
}
.catalogue .key, .catalogue .ident {
  font-family: var(--z2s-font-mono);
  font-size: var(--z2s-size-small);
  color: var(--z2s-text-muted);
}
.catalogue .area-note { color: var(--z2s-text-muted) }
.catalogue .entry {
  padding: var(--z2s-space-3);
  margin: 0 0 var(--z2s-space-2);
  background: var(--z2s-surface-card);
  border: var(--z2s-rule) solid var(--z2s-border);
  border-radius: var(--z2s-radius-md);
}
.catalogue .entry h4 { margin: 0 0 var(--z2s-space-2) }
.catalogue .entry p:last-child { margin-bottom: 0 }
.catalogue .note { color: var(--z2s-text-muted); font-size: var(--z2s-size-small) }
.catalogue .badge {
  display: inline-block;
  padding: 0 var(--z2s-space-2);
  border: var(--z2s-rule) solid var(--z2s-border-strong);
  border-radius: var(--z2s-radius-sm);
  font-size: var(--z2s-size-small);
  text-transform: uppercase;
}
/* A decision's standing sits in the same slot as a priority band and is drawn
   more quietly: a priority is an instruction, a standing is a fact about the
   decision, and the two are never on the same entry. */
.catalogue .badge.standing {
  border-color: var(--z2s-border);
  color: var(--z2s-text-muted);
}
.catalogue .tags {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: var(--z2s-space-2);
  padding-left: 0;
  margin: var(--z2s-space-2) 0 0;
}
.catalogue .tags li {
  font-size: var(--z2s-size-small);
  color: var(--z2s-text-muted);
  background: var(--z2s-surface-sunken);
  border-radius: var(--z2s-radius-sm);
  padding: 0 var(--z2s-space-2);
}

/* The verification layers an entry owes. Outlined rather than filled, so that
   they read as a different kind of thing from the tags immediately above them
   without depending on a reader telling two fills apart (NFR-UX-03). */
.catalogue .layers {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: var(--z2s-space-2);
  padding-left: 0;
  margin: var(--z2s-space-2) 0 0;
}
.catalogue .layers li {
  font-family: var(--z2s-font-mono);
  font-size: var(--z2s-size-small);
  color: var(--z2s-text-muted);
  border: var(--z2s-rule) solid var(--z2s-border);
  border-radius: var(--z2s-radius-sm);
  padding: 0 var(--z2s-space-2);
}

/* A retired entry is still in the document — its number is reserved for the life
   of the project (ADR-03) — so it has to be visibly not live scope without being
   hidden. Dimmed and struck through in the heading, with the reason in full
   underneath: never colour alone (NFR-UX-03), and never invisible. */
.catalogue .entry[data-retired] > h4 .ident,
.catalogue .entry[data-retired] > h4 {
  color: var(--z2s-text-muted);
  text-decoration: line-through;
}
.catalogue .entry[data-retired] > h4 .badge {
  text-decoration: none;
}
.retired-reason {
  color: var(--z2s-text-muted);
  font-size: var(--z2s-size-small);
}

/* A deliberate exclusion, distinct from live scope without being hidden
   (FR-GEN-09, ADR-17). Dimmed rather than struck through: unlike a retired
   entry it was never scope, so there is nothing to show as withdrawn — and the
   reason is set in the body colour, because the reason is the whole point of
   keeping the entry at all. */
.catalogue .entry[data-excluded] > h4 .ident,
.catalogue .entry[data-excluded] > h4 {
  color: var(--z2s-text-muted);
}
.excluded-reason { font-size: var(--z2s-size-small) }

/* --------------------------------------------------------------- traces */
/* What an entry serves, as links upward. Monospaced because an identifier is a
   token a reader copies rather than a word they read, and labelled because a
   row of bare codes with no heading is a row a reader has to guess at. */
.chips {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--z2s-space-2);
  margin: var(--z2s-space-2) 0 0;
}
.chips-label {
  font-size: var(--z2s-size-small);
  color: var(--z2s-text-muted);
}
.chip {
  font-family: var(--z2s-font-mono);
  font-size: var(--z2s-size-small);
  color: var(--z2s-text-muted);
  background: var(--z2s-surface-sunken);
  border-radius: var(--z2s-radius-sm);
  padding: 0 var(--z2s-space-2);
  text-decoration: none;
}
/* A chip that is a link and a chip that is not are different things, and the
   difference has to survive a reader who cannot tell two greys apart: the link
   underlines on approach, the dead one never does (NFR-UX-03). */
a.chip:hover,
a.chip:focus-visible {
  color: var(--z2s-text-body);
  text-decoration: underline;
}

/* ------------------------------------------------------------- scenarios */
/* The Given/When/Then triples, inside the story they belong to. A scenario is
   what a test is named after, so it is addressable in its own right: it carries
   its identifier as an element id, and the fold above it is opened by the same
   routine that opens an area when a link lands inside one. */

.catalogue .scenarios { margin: var(--z2s-space-3) 0 0 }
.catalogue .scenarios > summary {
  cursor: pointer;
  color: var(--z2s-text-muted);
  font-size: var(--z2s-size-small);
  text-transform: uppercase;
}
.catalogue .scenarios ol {
  list-style: none;
  padding-left: 0;
  margin: var(--z2s-space-2) 0 0;
}
.catalogue .scenario {
  padding: 0 0 0 var(--z2s-space-3);
  margin: 0 0 var(--z2s-space-3);
  border-left: var(--z2s-focus-width) solid var(--z2s-border);
}
.catalogue .scenario:last-child { margin-bottom: 0 }
.catalogue .scenario h5 { margin: 0 0 var(--z2s-space-1); font-size: var(--z2s-size-body) }
/* Clause and wording on one row each: the three labels line up down the left,
   so a reader checks that a scenario has all three by looking, not by reading. */
.catalogue .scenario dl {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: var(--z2s-space-1) var(--z2s-space-3);
  margin: 0;
}
.catalogue .scenario dt {
  font-family: var(--z2s-font-mono);
  font-size: var(--z2s-size-small);
  color: var(--z2s-text-muted);
}
.catalogue .scenario dd { margin: 0 }

/* ------------------------------------------------------------------- flows */
/* A use case's actor-centred flow, folded inside its entry exactly as a story's
   scenarios are — same fold, same summary, so a reader who has learned one has
   learned the other. The facts sit in a two-column grid for the same reason the
   clauses do: who performs this is one word, and it should be found by looking
   rather than by reading a paragraph. */

/* A decision's reasoning is the same fold with different parts in it, and it is
   styled by the same rules deliberately: one fold idiom in a catalogue, learned
   once (M6-01). */

/* A task's test-first definition is the third thing to use the fold, and it is
   styled by the same rules for the same reason: a reader who has opened a flow
   or a piece of reasoning already knows how to open this (M8-01). */

.catalogue .flow, .catalogue .reasoning, .catalogue .tdd, .catalogue .criteria {
  margin: var(--z2s-space-3) 0 0;
}
.catalogue .flow > summary, .catalogue .reasoning > summary,
.catalogue .tdd > summary, .catalogue .criteria > summary {
  cursor: pointer;
  color: var(--z2s-text-muted);
  font-size: var(--z2s-size-small);
  text-transform: uppercase;
}
.catalogue .flow .facts, .catalogue .reasoning .facts,
.catalogue .tdd .facts, .catalogue .scheduling {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: var(--z2s-space-1) var(--z2s-space-3);
  margin: var(--z2s-space-2) 0 0;
}
.catalogue .flow .facts dt, .catalogue .reasoning .facts dt,
.catalogue .tdd .facts dt, .catalogue .scheduling dt {
  font-family: var(--z2s-font-mono);
  font-size: var(--z2s-size-small);
  color: var(--z2s-text-muted);
}
.catalogue .flow .facts dd, .catalogue .reasoning .facts dd,
.catalogue .tdd .facts dd, .catalogue .scheduling dd { margin: 0 }
.catalogue .flow h5, .catalogue .reasoning h5 {
  margin: var(--z2s-space-3) 0 var(--z2s-space-1);
  font-size: var(--z2s-size-small);
  color: var(--z2s-text-muted);
  text-transform: uppercase;
}
.catalogue .flow ol, .catalogue .flow ul,
.catalogue .reasoning ul { margin: 0; padding-left: var(--z2s-space-4) }
.catalogue .flow .post { margin: var(--z2s-space-3) 0 0 }

/* ------------------------------------------------------- acceptance criteria */
/* The boxes are the plan's own record and nobody's reading position (M8-02), so
   they are disabled — and a disabled control has to look decided rather than
   broken. A met criterion is dimmed the way a finished item is; the box itself
   keeps full contrast, because the box is the state (NFR-UX-03: never colour
   alone — the tick is a shape, not a hue). */

.catalogue .criteria ul { margin: var(--z2s-space-2) 0 0; padding-left: 0; list-style: none }
.catalogue .criterion {
  display: flex;
  gap: var(--z2s-space-2);
  align-items: baseline;
  margin: 0 0 var(--z2s-space-1);
}
.catalogue .criterion input { flex: none; accent-color: var(--z2s-text-link) }
.catalogue .criterion[data-done] > span { color: var(--z2s-text-muted) }
.catalogue .badge.review {
  background: none;
  border: var(--z2s-rule) solid var(--z2s-border);
  color: var(--z2s-text-muted);
}

/* --------------------------------------------------------- execution waves */
/* Rounds, not a graph. Numbered, because "which wave is this" is the question a
   reader arrives with, and everything in one row may run at the same time. */

.waves { list-style: none; margin: 0; padding-left: 0 }
.waves .wave {
  border-top: var(--z2s-rule) solid var(--z2s-border);
  padding: var(--z2s-space-3) 0;
}
.waves .wave h3 {
  margin: 0 0 var(--z2s-space-2);
  font-size: var(--z2s-size-small);
  color: var(--z2s-text-muted);
  text-transform: uppercase;
}
.waves .wave ul {
  display: flex;
  flex-wrap: wrap;
  gap: var(--z2s-space-2);
  margin: 0;
  padding-left: 0;
  list-style: none;
}
.waves .wave a {
  font-family: var(--z2s-font-mono);
  font-size: var(--z2s-size-small);
  border: var(--z2s-rule) solid var(--z2s-border);
  border-radius: var(--z2s-radius-sm);
  padding: 0 var(--z2s-space-2);
  text-decoration: none;
  color: var(--z2s-text-muted);
}
.waves .wave a:hover, .waves .wave a:focus-visible { color: var(--z2s-text-body) }
.waves .wave .unit {
  font-family: var(--z2s-font-mono);
  font-size: var(--z2s-size-small);
  border: var(--z2s-rule) solid var(--z2s-border);
  border-radius: var(--z2s-radius-sm);
  padding: 0 var(--z2s-space-2);
  color: var(--z2s-text-muted);
}

/* ------------------------------------------------------------------ prompts */
/* Instructions nobody reads on screen. Folded shut, with the copy button beside
   the summary rather than below the block, because reaching it should not mean
   scrolling past the thing you are copying. */

.prompts .prompt { border-top: var(--z2s-rule) solid var(--z2s-border); padding: var(--z2s-space-3) 0 }
.prompts .prompt > summary { cursor: pointer; font-weight: 600 }
.prompts .copy {
  margin: var(--z2s-space-2) 0 0;
  font: inherit;
  font-size: var(--z2s-size-small);
  background: none;
  border: var(--z2s-rule) solid var(--z2s-border);
  border-radius: var(--z2s-radius-sm);
  color: var(--z2s-text-muted);
  padding: 0 var(--z2s-space-2);
  cursor: pointer;
}
.prompts .copy:hover, .prompts .copy:focus-visible { color: var(--z2s-text-body) }
.prompts pre { white-space: pre-wrap; overflow-x: auto }

/* A target's measurement, beside the number rather than under a heading of its
   own: the two are one fact and are read together. */
.catalogue .measured { color: var(--z2s-text-muted); font-size: var(--z2s-size-small) }

/* What an entry owes beyond the checks the document states for every entry, and
   what it is exempt from. The reason travels with the exemption: an exemption
   whose reason is somewhere else is an exemption nobody checks. */
.catalogue .also h5 {
  margin: var(--z2s-space-3) 0 var(--z2s-space-1);
  font-size: var(--z2s-size-small);
  color: var(--z2s-text-muted);
  text-transform: uppercase;
}
.catalogue .also ul { margin: 0; padding-left: var(--z2s-space-4) }
.catalogue .also .why { color: var(--z2s-text-muted); font-size: var(--z2s-size-small) }

/* What a later decision changed about a requirement that had already shipped.
   Ruled off from the wording above it, because the wording above it is what the
   tests and traces were written against and the reader has to be able to tell
   the two apart at a glance (FR-AMD-04, NFR-EVO-05). */
.catalogue .amended {
  margin-top: var(--z2s-space-3);
  padding-left: var(--z2s-space-3);
  border-left: var(--z2s-focus-width) solid var(--z2s-border);
}
.catalogue .amended h5 {
  margin: 0 0 var(--z2s-space-1);
  font-size: var(--z2s-size-small);
  color: var(--z2s-text-muted);
  text-transform: uppercase;
}
.catalogue .amended ul { margin: 0; padding-left: var(--z2s-space-4) }
.catalogue .amended .when {
  color: var(--z2s-text-muted);
  font-family: var(--z2s-font-mono);
  font-size: var(--z2s-size-small);
}

/* An element the runtime has filtered out. Stated once, with weight, because a
   later rule that sets display on any of these selectors would otherwise put a
   hidden entry back on the page. */
[hidden] { display: none !important }

/* ---------------------------------------------------------------- toolbar */
/* The filter, the priority bands and the fold controls, pinned to the top so
   they are reachable from anywhere in a catalogue of several hundred entries.
   Rendered only when the document has a catalogue to control. */

.toolbar {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  flex-wrap: wrap;
  gap: var(--z2s-space-2) var(--z2s-space-4);
  align-items: center;
  margin: 0 0 var(--z2s-space-4);
  padding: var(--z2s-space-3) 0;
  background: var(--z2s-surface-page);
  border-bottom: var(--z2s-rule) solid var(--z2s-border);
}
.toolbar .find {
  flex: 1 1 auto;
  min-width: 0;
  padding: var(--z2s-space-2);
  background: var(--z2s-surface-card);
  color: var(--z2s-text-body);
  border: var(--z2s-rule) solid var(--z2s-border-strong);
  border-radius: var(--z2s-radius-md);
  font: inherit;
}
.toolbar .bands, .toolbar .folds {
  display: flex;
  flex-wrap: wrap;
  gap: var(--z2s-space-2) var(--z2s-space-3);
  align-items: center;
}
.band {
  display: inline-flex;
  gap: var(--z2s-space-1);
  align-items: center;
  font-size: var(--z2s-size-small);
  cursor: pointer;
}
.band .count { font-family: var(--z2s-font-mono); color: var(--z2s-text-muted) }
.toolbar button, .reset {
  padding: var(--z2s-space-1) var(--z2s-space-2);
  background: var(--z2s-surface-card);
  color: var(--z2s-text-body);
  border: var(--z2s-rule) solid var(--z2s-border-strong);
  border-radius: var(--z2s-radius-sm);
  font: inherit;
  font-size: var(--z2s-size-small);
  cursor: pointer;
}
.reset { margin-top: var(--z2s-space-2) }

.catalogue .area > summary { cursor: pointer; margin-bottom: var(--z2s-space-3) }
.catalogue .area > summary h3 { display: inline }
.catalogue .no-match { color: var(--z2s-text-muted) }
.catalogue .tick {
  display: inline-flex;
  gap: var(--z2s-space-2);
  align-items: center;
  margin-top: var(--z2s-space-2);
  color: var(--z2s-text-secondary);
  font-size: var(--z2s-size-small);
  cursor: pointer;
}
/* The entry a deep link landed on. Marked by a rule down its edge as well as by
   its border colour, so the mark survives a reader who cannot tell the two
   colours apart (NFR-UX-03). */
.catalogue .entry.marked {
  border-color: var(--z2s-text-link);
  border-left-width: var(--z2s-focus-width);
}
/* A scenario is linked to as often as the story around it, and it already wears
   a rule down its edge, so the mark is that rule changing colour. */
.catalogue .scenario.marked { border-left-color: var(--z2s-text-link) }

.flow { list-style: none; padding-left: 0 }
.flow .step {
  padding-left: var(--z2s-space-4);
  border-left: var(--z2s-focus-width) solid var(--z2s-border-strong);
  margin-bottom: var(--z2s-space-3);
}

/* A section this document cannot display. Announced in words and set apart by
   its rule, not by colour alone (NFR-UX-03, NFR-GEN-04). */
.placeholder {
  padding: var(--z2s-space-3);
  border-left: var(--z2s-focus-width) solid var(--z2s-note);
  background: var(--z2s-note-bg);
  color: var(--z2s-note);
}

/* --------------------------------------------------------------- narrow */

@media (max-width: 640px) {
  #doc { padding: var(--z2s-space-4) var(--z2s-space-3) var(--z2s-space-5) }
  .cards, .stats { grid-template-columns: minmax(0, 1fr) }
  .hero h1 { font-size: var(--z2s-size-h2) }
}

/* -------------------------------------------------------- reduced motion */
/* Everything, not a named list: a list goes stale the moment a rule is added
   below it (NFR-UX-02). */

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 1ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 1ms !important;
    scroll-behavior: auto !important;
  }
}

/* ------------------------------------------------------------------ print */
/* Paper has no interaction, so collapsed content is expanded and the chrome
   that only exists to be clicked is dropped (FR-SPC-11). */

@media print {
  body { background: var(--z2s-surface-card) }
  #doc { max-width: none }
  /* Two rules for one job: engines that collapse a group by hiding its children
     obey the first, and engines that hide the generated content box obey the
     second. Neither alone expands a closed group everywhere. */
  details > *:not(summary) { display: revert !important }
  details::details-content { content-visibility: visible !important }
  /* Instructions are dropped rather than expanded. Every other fold opens on
     paper because its content is the document; a prompt's content is something
     you copy, and a page cannot be copied from. */
  nav.contents, .toolbar, .review, .tick, .reset, .prompts { display: none }
  .section { break-inside: avoid-page }
  .section > h2 { break-after: avoid-page }
  pre, table { break-inside: avoid }
  a { text-decoration: underline }
}
"""
