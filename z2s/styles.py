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
  nav.contents, .toolbar, .review, .tick, .reset { display: none }
  .section { break-inside: avoid-page }
  .section > h2 { break-after: avoid-page }
  pre, table { break-inside: avoid }
  a { text-decoration: underline }
}
"""
