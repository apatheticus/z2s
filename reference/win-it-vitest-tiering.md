# Handoff — tiering win-it's verification, and giving each worker its own database

This is a note for the **win-it** repository, not for this one. It is here rather
than under `docs/` because everything under `docs/` is GitHub Pages source, and
another project's backlog does not belong on the method's public site. It is not
a requirement either: `coverage.universe()` sweeps in every FSD and SDD
requirement, and one about another repo's vitest config would need a claiming
task in a plan that cannot build it.

## What was measured

A live build of win-it was instrumented against z2s 1.2.10: 70 of 191 units, about
171 hours. Seventy-seven per cent of that was the builder dispatch. Of the twelve
gauntlet failures, one finding belongs entirely to this repository and one belongs
entirely to win-it.

The z2s half is fixed in 1.3.0 (FR-EXE-17, NFR-EXE-12): the layers now run
cheapest first, and the whole-repository checks a unit never named are run before
the dispatch is settled rather than after everything else.

The win-it half is this document. **A red layer took 25.4 minutes to reach a
verdict of "no"** because win-it's gauntlet is one undifferentiated vitest run
that stands up a database before it can answer anything at all. Ordering the
layers helps only if the cheap layer is genuinely cheap.

## 1. Split the suite into a static tier and a database tier

Two vitest projects, not one:

- **static** — everything that imports and asserts. No database, no server, no
  fixtures that need either. This is the tier z2s's preflight will call, and the
  split is precisely what makes the preflight pay off: a tier that needs nothing
  can be run at any moment, against any tree, before anything is settled.
- **database** — everything that does need one.

Map them onto the method's layers as `lint` and `unit` for the static tier and
`integration` for the database tier. `z2s/layers.py` treats `lint` and `unit` as
infrastructure-free and `integration` as not, which is what routes them.

The value is not that the static tier is faster in total. It is that a failure in
it is reachable in seconds rather than after a database has come up.

## 2. A database per worker, named from the worker's identity

Four builders sharing one database is four builders sharing one set of rows.
Give each worker its own, named from its own identity so the name is derivable
rather than coordinated.

**The project tears them down, never the run.** z2s reports what is still up on
the host after a stopped dispatch and removes nothing — `execute.CONTAINERS` is
`docker ps` and nothing else, deliberately. Tearing down a live database is not
reliably a ten-second job, and a container an operator started for their own
reasons is not the run's to destroy. So the teardown is win-it's: a script the
project runs between builds, or a compose profile whose lifetime the operator
owns.

## 3. Pin serial only the one file that actually conflicts

One file in win-it genuinely cannot run beside itself. Pin that file serial. Do
not pin the suite — a suite pinned serial to solve one file's problem is the
25.4 minutes back again, paid on every unit.

## 4. Parallelism per file, never per test

Tests inside one win-it file share a database, run in declaration order, and
depend on rows a previous test left. Splitting *within* a file breaks all three
at once, and the failures look like flakes rather than like a configuration
mistake — which is the expensive kind. `fileParallelism` yes; per-test
concurrency no.

## What not to do

- **Do not raise z2s's concurrency ceiling to compensate.** Four is a
  review-capacity number, not a machine number: it is how many finished units a
  person can actually judge, and NFR-EXE-09 says so. A slow gauntlet is not a
  reason to widen it.
- **Do not put a shell line in a `workers.json` gauntlet command.** A gauntlet
  command is a list of words, run with no shell — a glob, a pipe, `&&` or `$VAR`
  never expands. `execute.settings` refuses a string outright. Two vitest
  projects means two entries, not one string with a `&&` in it.
- **Do not solve this with a longer timeout.** A bound that has to grow to fit a
  gauntlet is measuring the gauntlet, and the gauntlet is the thing to fix.
