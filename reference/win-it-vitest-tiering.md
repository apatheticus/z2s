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

## From the 1.3.0 re-check (2026-09-02)

The build was measured again on 1.3.0. The z2s half of what it found ships in
1.4.0 (FR-EXE-06, FR-EXE-07, FR-EXE-17 and FR-DOC-06, each amended in place).
What is left is win-it's, and it is smaller than section 3 above made it sound.

**Pin serial only the pair that actually conflicts.** `vitest.config.ts` sets
`fileParallelism: false` for the whole suite — every file in `tests/integration`
runs one after another to protect a handful of them. The files that genuinely
cannot run beside anything are the ones that drive the migration runner against
the live schema — `migrate-check.test.ts`, `migrations-forward-only.test.ts` and
`migrations-no-rollback.test.ts` in `tests/integration`. Put those in their own
vitest project with `fileParallelism: false`, and let the rest of the database
tier run per-file in parallel as section 4 says. Confirm by reading each of the
three that it really touches the migration table; a file that only reads its own
rows belongs in the parallel tier.

**A second builder makes the migration bundle a live collision until a family
is declared.** With one builder the shared files every migration touches were
only ever strays — reported, never a clash. With two or more they are a
collision the plan cannot express, because no per-unit write list owns
`drizzle/migrations/meta/_journal.json`. z2s 1.4.0 reads write families from
`.zero/workers.json`; add this to win-it's, beside the gauntlet:

```json
"families": [
  {"when": "drizzle/migrations/**",
   "also": ["drizzle/migrations/meta/**", "drizzle/migrations.sha256",
            "drizzle/drizzle.config.ts"]}
],
"appendable": ["CLAUDE.md"]
```

Every path above is one the run ledger recorded as a stray on the 1.3.0 build
(`.zero/state/run.json`, `strays`, read 2026-09-02). Checked against a copy of
that ledger and the real plan documents the same day: `M7-P1-T1`, which
declares `drizzle/**`, gains the three implied paths; `CLAUDE.md` stops being a
stray on the two units that wrote it. No regeneration: a running orchestrator
reads both on its next scheduling decision.

**A family widens a declared claim; it cannot invent one.** The other strays
the ledger holds — `src/server/paths/retrieval.ts` (written by three units in
two milestones), `src/server/outward.ts`, `src/models/client.ts`,
`src/ingestion/extract.ts`, and `M4-P3-T1`'s whole migration bundle — came from
units that declared no path anywhere near them, so no family reaches them. Those
are `overlay` entries in `.zero/state/run.json`, keyed by unit, or corrected
write lists in the plan detail files (a regeneration now keeps status). The
stray notice on the console names both doors.

**Every M7 unit declares `tests/integration/**` and `tests/e2e/**`, so no two
M7 units ever run together.** All nine M7 units carry those two globs, and
`collides` reads any shared claim as a collision — correctly. That is the plan's
write lists, not the orchestrator: a unit that adds one test file should declare
that file, not the directory. Until the detail files are narrowed, the ceiling
of four buys M7 nothing.

**The dispatch log is written live, but a `claude -p` worker prints nothing
until it exits.** So `build.log` sits empty for the whole of a dispatch and is
not a liveness signal; the build skill now says so and points at modification
times instead. The worker command can fix that on its own side: the Claude Code
CLI reference says plain text output prints only on completion, and that adding
`--output-format stream-json --verbose` emits messages as the run progresses
(https://code.claude.com/docs/en/cli-reference, checked 2026-09-02). Add those
two flags to the `command` list in `workers.json` — two more list entries, not a
shell line — and the log fills as the worker works. Nothing in z2s changes; the
report is still the JSON file the brief names, and the log stays a log.
