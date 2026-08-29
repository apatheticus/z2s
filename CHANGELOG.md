# Changelog

Every released version of the `zero` plugin, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

A release is the version in `.claude-plugin/marketplace.json`. That number is what a
runtime compares to decide an update exists, so a change to `z2s/` alone never reaches
an installed copy until a version moves — which is why several entries below exist only
to publish work already on `main`.

## [1.2.10] - 2026-08-29

### Added

- A stopped dispatch now reports what it left running on the host. A database container
  outlived a timed-out dispatch by two and a half hours, and four later units ran their
  checks against a service the run believed was gone. The run asks `docker ps` and names
  what is still up in the same sentence that says the worker was stopped. It reports; it
  never removes, and every failure — no Docker, a refused command, a non-zero exit — is
  silence rather than noise.
- Continuous integration. The full test suite, a byte-identical-regeneration gate, the
  self-hosted document set, the plugin lock and the pipeline now run on every push and
  every pull request. Chromium is installed in the job and the browser harness is
  asserted live before the suite starts, so a browser test that silently skips fails the
  run instead of passing quietly.
- A screenshot harness, `tests/shot_harness.js`, for looking at the published pages. It
  makes no assertion on purpose: the gate is a reader.
- Marketplace metadata — `displayName`, `homepage`, `repository`, `license` and a
  `spec-driven` tag — so the listing says what the plugin is before it is installed.

### Fixed

- A timed-out unit is no longer told that no dispatch of it ever started. Both a timeout
  and a host that could not launch a worker route through the same path, and it explained
  itself with one sentence written for the second case. A run introduced that
  contradiction in 1.2.9; the two now say what actually happened.

### Changed

- The published specification and the shipped `/zero:build` text now describe 1.2.9's
  collision behaviour, which neither did. A write-set collision costs the unit no attempt
  and is remembered, so the same pairing is never scheduled together again. The risk
  mitigation in the PRD and the SDD still said contention was "reported rather than
  retried".
- `/zero:build` states the worst case. Neither a timeout nor a write-set clash spends an
  attempt, so a unit is re-dispatched until it has misfired three times: at the defaults
  that is nine hours for one unit before it blocks. The arithmetic was never written down
  anywhere an operator would read it.
- The published document set moves to version 2.5, dated 2026-08-29, and its plan summary
  stops describing sixteen milestones as fourteen.

## [1.2.9] - 2026-08-28

### Fixed

- A collision the run scheduled is no longer the unit's to pay for. A shared append-only
  file — a route manifest every unit must add a line to — is in nobody's per-unit write
  list, because no per-unit list can own it. The scheduler read two such units as
  disjoint, dispatched them together, then charged the clash to one of them; three of
  those and it was blocked for doing the only thing that ships a working route. The clash
  now spends a misfire rather than an attempt, and the stray path is remembered so the
  pair is never scheduled together again. Measured on the project that found it: 46 units
  declared a route and not the manifest.

## [1.2.8] - 2026-08-28

Four orchestrator defects a twelve-hour production run charged to individual units.

### Fixed

- A failed gauntlet layer is re-run once before it charges the unit. Two of seven layers
  were non-deterministic; one unit lost an attempt to an exit 1 that exited 0 seventeen
  minutes later on an untouched tree. Both runs failing keeps the original message
  verbatim. There is no setting for this — a layer that needs three goes is broken in a
  way a knob would hide.
- A dispatched brief now tells the worker that the run owns the verification gauntlet. Six
  of eleven builders ended their turn believing they still had to establish it, and the
  process exited underneath a plan that thought it was waiting.
- What a report names is checked against what the unit declared it would write. Three of
  eight units wrote a file no list named, and nothing in the run read the answer.
- A unit whose work already landed can pass. It may name the commit in `landed`, which the
  run verifies with `git show` rather than believing.

## [1.2.7] - 2026-08-22

Four control-flow defects found by a real build of another project.

### Added

- A dispatch is bounded. A builder once sat idle for two hours and twenty-two minutes with
  the work already finished on disk. The default ceiling is 5400 seconds, settable per
  project and per worker, `null` for none.
- Every dispatch writes its own log, named on the line that announces it. A verdict had
  taken 51 minutes to appear in a tee'd log, so an operator could not tell a working unit
  from a wedged one.

### Fixed

- The recovery turn is reachable from the only case it exists for. It read the exit status
  first, and anything killed exits non-zero — so a finished build was discarded and rebuilt
  over five builder rounds and twelve judgements.
- A unit whose work already landed can report the commit instead of an empty change list.

## [1.2.6] - 2026-08-21

### Added

- `python3 -m z2s.restyle` re-renders a document set that already exists. A generated
  document inlines its own stylesheet and nothing re-read it, so two Must requirements
  were true of a first generation and false of every project that already had documents:
  documents adopted the host design system on the day they were written, and a set could
  not be re-rendered from the specification each document carries. `/zero:design` now
  writes the record and then restyles what is already on disk.

## [1.2.5] - 2026-08-21

### Fixed

- A dark theme declared for part of a palette is no longer treated as a dark theme. As soon
  as one colour had a dark counterpart the document declared `color-scheme: light dark`,
  while every colour the host had not declared kept its light value — dark text on a dark
  background, invisible code blocks. Measured on the reporting project's real output: 17
  plan documents affected, 14 of 30 text-on-surface combinations below the 4.5:1 contrast
  floor, worst 1.12:1. A partial declaration now keeps the light document and the run names
  every colour still missing, so a project that wants dark mode gets a checklist instead of
  silence.

## [1.2.4] - 2026-08-19

Publishes two orchestrator fixes already on `main`.

### Fixed

- A worker that stopped without its report is asked for it once, in the same live dispatch
  directory, before the attempt is spent. A unit ran 23 minutes, did the work, passed two
  independent critics and exited 0, and was charged an attempt for returning no report. The
  report contract now states *when* to write the file, not only what goes in it.
- A write set that omits its tests is not a write set. Five keys the plan generator reads —
  `writes`, `status`, `deferred`, `provider` and `worker` — appeared in no schema anywhere,
  so all 191 units in 16 generated milestones declared a write set and not one named a test
  path. A second, worse defect was found beside it: overlap compared whole strings, so
  `src/storage/**` did not collide with `src/storage/client.ts`, and the disjointness
  guarantee was void on every plan whose author used a glob.

## [1.2.3] - 2026-08-19

Publishes three orchestrator fixes found by a real 191-unit build.

### Fixed

- A recorded denial no longer fails the attempt before the gauntlet runs. A worker that
  respected a boundary and disclosed it lost to one that stayed quiet, and the unit
  exhausted its budget without a single check ever running.
- Workers no longer inherit a wall-clock ceiling that discards finished work — thirty-three
  minutes of completed work had been reported as "no report". An operator who wants a
  ceiling still sets one.
- A worker that never started no longer costs the unit an attempt. No API, no network, a
  missing binary: the state of the host was charged to the unit, and one DHCP change took a
  whole wave down.

## [1.2.2] - 2026-08-19

### Fixed

- A unit whose commit was refused is failed and retried with what git actually said. `git
  add` aborts before staging anything if one reported path cannot be found or tracked, so a
  single bad name took the work, the plan document and the status change down together —
  and the run wrote the refusal into a ledger nobody reads, then recorded the unit as
  passing.

## [1.2.1] - 2026-08-18

Two runtime fixes, both in the orchestrator, neither reachable from a skill file.

### Fixed

- A unit a stopped run was still holding is taken back on the next run, rather than sitting
  in progress for ever, invisible to the ready set. The attempt is not charged, because a
  run that dies never reaches the code that counts it.
- A dispatch that repeats an attempt no longer reads the report the previous one left in the
  same directory. A worker that wrote nothing at all had the earlier answer read as its own.

## [1.2.0] - 2026-08-18

### Added

- The pipeline gains a sixth gate, `design`, so a design record that has fallen behind the
  files it was read from is reported by a gate a project already runs. Three states, three
  answers: behind its sources is a warning, unreadable is a failure, and absent is *not
  run* rather than a pass. A project with no design record therefore reads
  `gates: 5 passed · 0 failed · 1 skipped`, which is correct and not a regression.

### Fixed

- The contract a worker is handed is the contract the machine enforces. The Report contract
  in a brief and the checker that validated against it were two different documents: the
  brief named no key at all, the checker read six by name, two of which appeared in no brief
  anywhere. A worker could satisfy every stated word and be rejected every time — the
  reporting project lost seven of nine attempts to it. Both halves now render from one
  definition, held together by a test in both directions.
- A builder can no longer grade itself. Every brief said to set the status, and builders did,
  including setting themselves verified; the unit then kept its own verdict, left the ready
  set and was never tried again. A dispatched brief and a pasted prompt are now told
  different things, because only one of them has a run behind it.

## [1.1.2] - 2026-08-18

### Fixed

- A worker's criteria no longer take the whole run down with them. The report contract asks
  for "its identifier, and whether it is met" and names no shape, so a list of `{id, met}` is
  a faithful reading of it — and it raised an `AttributeError` out of the settle path that
  killed every in-flight unit, not just its own.

### Changed

- The specification catches up with the toolchain: five requirements amended in place and
  dated, one genuinely new, and a milestone in the published plan naming the units of work
  that claim them.

## [1.1.1] - 2026-08-17

### Changed

- The specification stops describing a chain of fourteen. The index had named
  `/zero:design` since M16, but the documents behind it had not: the functional
  specification still enumerated the chain without it, the technical design's component
  list named every entry point except setup and design, and the repository layout showed
  neither `workers.json` nor `design.json`. Two dated amendments carry it forward-only,
  originals untouched. No requirement was added and none rewritten.

## [1.1.0] - 2026-08-17

### Added

- `/zero:design`, the fifteenth skill. It shipped in M16, but neither manifest moved, so
  every installed copy compared 1.0.0 against 1.0.0 and reported itself current. The work
  shipped; the signal that it had did not.

### Changed

- The test that pinned the version to a constant is gone. It asserted a literal, so every
  release would have had to edit a test to pass, and it never asked the question that
  matters. It now checks that `plugin.json` and `marketplace.json` state the *same*
  version — the runtime reads one to decide an update exists and the other to record what
  it installed, so a disagreement either hides a release or misreports the one in hand.

## [1.0.0] - 2026-08-15

First release. Every step of the finished toolchain is wrapped as a named, separately
invocable skill, and the chain is packaged as one version-pinned plugin.

### Added

- The skill chain: `/zero:init`, `/zero:vision` through `/zero:plan`, `/zero:build`,
  `/zero:prompt`, `/zero:action`, `/zero:update`, `/zero:ship`, and the shared
  `/zero:questions` interview that every other skill routes through. One chain definition
  holds the steps, their documents and their prerequisites; a refusal names the earliest
  gap in the whole chain rather than the step's own nearest prerequisite, so an operator is
  not walked backwards one document per round trip.
- Forward-only editing. An amendment appends a dated note below text that is never touched,
  a retirement keeps the entry and reserves its number for ever, and `delete`, `remove` and
  `drop` are refused *by name* rather than being absent — an operator will ask, and a
  missing command teaches nothing.
- `/zero:ship`, which commits, pushes and only ever offers a pull request. The consent check
  runs before the branch is read, and every git command is judged first.
- A version-pinned lock generated from the chain definition, with a trigger-policy lint that
  runs in both directions: exactly one skill is model-visible, and a chain whose interview
  cannot fire is a chain that guesses.

### Changed

- The plugin is named `zero`. Claude Code always namespaces a plugin's skills as
  `<plugin>:<skill>`, so the published `/zero-vision` was never buildable. Install is
  `/plugin marketplace add apatheticus/z2s` then `/plugin install zero@z2s`.

## [0.1.0] - 2026-08-14

### Added

- The manifest, published ahead of the skills it would carry. The specification set was
  complete and live at [apatheticus.github.io/z2s](https://apatheticus.github.io/z2s/), the
  skill chain was scheduled and not yet built, and the description said so: installing it
  added no skills.

Links are commit ranges rather than tag comparisons: this repository carried no tags
until 1.2.10, so a tag link would resolve to nothing for every version below it.

[1.2.10]: https://github.com/apatheticus/z2s/compare/89ae2f8...main
[1.2.9]: https://github.com/apatheticus/z2s/compare/c62a687...89ae2f8
[1.2.8]: https://github.com/apatheticus/z2s/compare/f1e29c4...c62a687
[1.2.7]: https://github.com/apatheticus/z2s/compare/179d670...f1e29c4
[1.2.6]: https://github.com/apatheticus/z2s/compare/07b82a9...179d670
[1.2.5]: https://github.com/apatheticus/z2s/compare/ad162a4...07b82a9
[1.2.4]: https://github.com/apatheticus/z2s/compare/4df59a6...ad162a4
[1.2.3]: https://github.com/apatheticus/z2s/compare/28bccc6...4df59a6
[1.2.2]: https://github.com/apatheticus/z2s/compare/1111311...28bccc6
[1.2.1]: https://github.com/apatheticus/z2s/compare/e097fde...1111311
[1.2.0]: https://github.com/apatheticus/z2s/compare/b0e2dd8...e097fde
[1.1.2]: https://github.com/apatheticus/z2s/compare/5509473...b0e2dd8
[1.1.1]: https://github.com/apatheticus/z2s/compare/da46fc1...5509473
[1.1.0]: https://github.com/apatheticus/z2s/compare/132bb4c...da46fc1
[1.0.0]: https://github.com/apatheticus/z2s/compare/19aabdb...132bb4c
[0.1.0]: https://github.com/apatheticus/z2s/commit/19aabdb
