# Changelog

Every released version of the `zero` plugin, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

A release is the version in `.claude-plugin/marketplace.json`. That number is what a
runtime compares to decide an update exists, so a change to `z2s/` alone never reaches
an installed copy until a version moves — which is why several entries below exist only
to publish work already on `main`.

## [1.9.0] - 2026-09-06

From the same project again, and the finding is about what a brief does not say.
A unit's declared write set is stated as a fence, correctly — the orchestrator
schedules concurrent work from it — but a worker reads a fence in both
directions. Given one, it declared a job kind, left the handler out of
`src/workers/run.ts` because that path was not on its list, and offered the gap
as scope rather than as unfinished work. Nothing in the brief said the wiring a
unit's own work implies is part of that unit. Now it does. Doc set 2.14.

### Added

- **A project can name its ambient paths, and every brief carries them.**
  `ambient` in `.zero/workers.json` is a list of the paths a unit's own work
  implies — a migration, a route table, a job handler. Each brief states them
  straight after the write set, as writes that are always permitted and are
  never an exception to raise, and tells the worker not to narrow what it builds
  to avoid them (FR-EXE-03, amended). Read at run time like the gauntlet and the
  families, so a running build absorbs the list with no regeneration, and a
  project that names none is told about none.
- `ambient` is what a brief says, not what the scheduler reads. It changes no
  collision and no stray verdict: a path that must also escape those is an
  `appendable` one, and a project that wants both says both.

## [1.8.0] - 2026-09-05

One more round from the same 191-unit project, now on 1.7.0, and both findings
are one thing: **the run tells the operator what to do and then cannot act on
it.** The stray notice offered the `overlay` door while a run was going, which is
the only time the run holds the ledger in memory and overwrites the file at every
save — so the edit it asked for was lost, silently. And a red the run had rightly
ruled another unit's was still re-dispatched three times to sample one unchanged
fact, then blocked with the words "out of attempts" over a unit that had been
charged none. Doc set 2.13.

### Fixed

- **A write-list correction made while a run is going is kept.** `overlay` is
  the one key in the run ledger an operator writes, and the run now re-reads it
  from disk before every write it makes to the file and before every scheduling
  decision. Disk wins for that key; nothing in the run writes it, so replacing it
  loses no run state. A ledger that cannot be read — an editor part-way through
  its write, most often — is said once and the cached copy kept; the run does not
  end over it. The "correction was applied" note now appears when the notice
  said it would (FR-EXE-19, honoured as written).
- **A block is called a block.** The summary header read "out of attempts" over
  units the run had charged none, because a misfire bound reached spends the
  whole attempt budget in one step. The header is now `blocked`, and a block
  reached that way says how many dispatches were spent and that none was charged
  as an attempt.

### Changed

- **A red that belongs to a sibling still building holds the unit instead of
  costing it a dispatch.** Where the files a failure names are declared by
  another unit that has not yet passed or stopped, the unit is parked: it leaves
  the ready set, is charged neither an attempt nor a misfire, and is offered
  again with both intact once every such owner has settled (FR-EXE-20, amended).
  The console names the owner, `ready` says who the unit waits for, and the
  summary lists it under *held on another unit's work*. This covers the
  inherited path too — a layer already red at the opening survey never named an
  owner before. Where no moving unit declares the files, the misfire bound
  stands as it did. A unit is never held on an owner that itself waits for that
  unit; the check is the direct edge only, and a cycle through a third unit is
  the stated ceiling. Not shipped, as before: a checkout per dispatch, which is
  what it would take to stop the overlap rather than the charge.

## [1.7.0] - 2026-09-04

Two rounds of findings from a 191-unit project running four workers at a time,
and both of the new ones are the same thing from opposite ends: **the run owns
the tree and the host, and neither is partitioned per unit.** Concurrency is
scheduled on what a unit declares it writes, but a check reads the whole
repository and a signal reaches one process group. Two units each lost an attempt
to twelve type errors in files a third unit was at that moment writing, and a
`kill -TERM` on the orchestrator left four workers alive, still editing the tree
the operator had stopped the run in order to read. Doc set 2.12.

### Fixed

- **A unit is no longer charged for a sibling's half-written work.** Every
  verification layer's output is now kept beside the dispatch it belongs to, and
  the run reads the files a failure names out of it. Where the plan's own
  declared write sets give the unit none of them, the red is not the unit's: it
  charges a misfire rather than an attempt, and the worker is not handed the
  failure back (FR-EXE-20, amended). This is the case the two existing guards
  could not reach — the red did not exist at the opening survey, so it was not
  inherited, and a sibling still building has committed nothing, so history had
  nothing to say. It is the ordinary case rather than an unusual one, because a
  unit told to write its failing test first puts that test on the tree before the
  module it imports. Stated as a ceiling: this stops the unit being charged for
  the overlap and does not stop the overlap.
- **Stopping a run now stops the workers it started.** Ctrl-C or `kill -TERM`
  ends every worker and everything those workers started, then exits having
  settled nothing and charged nothing (FR-EXE-09, amended). It starts nothing
  further either — including the turn the run would otherwise use to ask a
  stopped worker what it built, which meant a stop that ended four workers
  started four more. A second signal is an ordinary kill. Each worker still runs
  in a session of its own so its test runner cannot signal the operator's shell;
  the run is now the one thing that can reach across that.
- **A report the contract will not read costs no attempt.** A missing observed
  failure, unreadable criteria, or a `landed` commit that is not in history says
  nothing about the work, so it is a misfire — counted, still blocking a unit
  whose every dispatch comes back unreadable, and carrying the exact complaint
  into the next brief.
- **A worker that says it did not finish is heard.** Nothing read the criteria on
  a report that was otherwise well formed, so an honest account of getting
  part-way and a claim of having finished were the same line in the log. The run
  now says so on its own line and in the ledger. Not a verdict — only the judge
  passes a unit.

### Changed

- **The grace period a stopped process gets is twenty seconds, not ten.** A
  worker's checks stand up real infrastructure, and a container holding an open
  database connection is not reliably a ten-second teardown. The run still only
  reports what it finds still running; it removes nothing.

## [1.6.1] - 2026-09-04

The chain's first document was renamed from the Vision to the Intent in doc set
2.9, and a project written before that keeps its files under the old name — which
the chain has always read. Its recorded DECISIONS were the half nobody wired up.
A 191-unit project regenerated its plan on 1.6.0 and `plan.locked` returned eight
decisions where the committed documents had carried ten; the two that stopped
being restated said the build was one release, feature complete and production
ready, and that a silence in the brief is an open question rather than an
assumption. One milestone document alone lost forty-four restatements of them.
Both answers were on disk the whole time, in `.zero/state/vision.md`, and nothing
read them. Doc set 2.11.

### Fixed

- **A renamed document's decisions are read under its former slug**, the same
  fallback `chain.require` has always applied to the document itself
  (NFR-OPS-07). `gate.load` now consults the rename map, so every generator that
  reads its own ledger recovers what a pre-rename project settled — and so does
  `plan.locked`, which restates the whole chain's decisions into every embedded
  worker prompt. That was the surface it showed on: a worker briefed without them
  re-decides what its owner already closed, which is the silence FR-EXE-03 exists
  to prevent. Existence decides the fallback, not content, so a project that has
  answered the new gate keeps its own answers and never reaches back; new writes
  still go to the new name only, and nothing on a host's disk is moved.

### Changed

- **The rename map moved to `z2s/paths.py` and is keyed by the current slug.** It
  had lived in `chain.py`, which the ledger reader cannot import — `chain`
  imports `gate`, so the edge only runs one way — which is why the ledger half
  was missed rather than merely forgotten. One map, two readers, and no second
  spelling of a rename to disagree with the first. `chain.FORMERLY` re-exports
  it; every existing caller is unchanged, and the map is as narrow as it was:
  one entry, and no other document gets a fallback.
- **NFR-OPS-07 amended** (2026-09-04) to say what the fallback covers: every read
  keyed by the document's slug, its recorded decisions as well as its
  prerequisite check.

## [1.6.0] - 2026-09-04

A 191-unit build ran at a mean of 1.05 concurrent workers against a ceiling of
four, for 124 hours. Raising the ceiling to eight changed nothing. Turning off
the wave order changed nothing. Turning off the write-set check took it to 3.02.
One declaration did all of it — `tests/integration/**`, held by 180 of the 191
units, which makes every pair of them collide. Nothing in the toolchain was
wrong and nothing said a word. This release makes the number visible before a
build spends it, and says the half of the write-set rule that was missing.
Doc set 2.10.

### Added

- **`python3 -m z2s.forecast`** — what a plan costs in concurrency, from the plan
  alone, before anything is dispatched. It reports the rounds the plan takes at
  the project's ceiling, the mean units per round, the units nothing will ever
  pick up and why, and the paths most of the plan is claiming
  (`tests/integration/** — declared by 180 of 191 units`). Everything it knows it
  asks the orchestrator: `settings`, `units`, `order`, `current`, `ready`,
  `dispatchable`, `collides`, `recall`, `writes` and `implied` are imported, never
  restated, so a forecast cannot drift from the run it is forecasting. A project
  with no `.zero/workers.json` yet — which is every project at the moment its plan
  is written — is forecast against the defaults and told so.
- **It is a preview and never a gate.** It exits `0` whatever it finds, like
  `z2s.restyle --check`, and it is deliberately NOT a seventh `z2s.pipeline` gate.
  A plan that can only run serially is a legitimate plan, and only its author can
  say whether a claim is wider than the work. The number is structural — every
  unit costs one round, and a round ends when all of its units end — so it
  compares one plan with another and with the ceiling, never with a clock. At plan
  time there are no durations, and a test pins that it never prints one.
- **`FR-EXE-06` says so**, in a dated amendment beside the 2026-09-02 families
  one: a declared write set is what actually bounds concurrency, so the system
  shall be able to report from a plan alone how much concurrency that plan can
  reach and which declarations are bounding it, advisory and refusing nothing. No
  new identifier; the universe stays 206.

### Changed

- **The write-set rule now says NARROW as well as complete.** `z2s/plan.py` has
  always refused a task that names a verification layer and declares no test path,
  and its docstring argued at length that a short list is a hazard. Both are
  right, and both were alone: nothing pushed the other way, so an author under any
  doubt satisfied "leave nothing out" with a directory glob, which is always
  complete, always accepted, and sometimes the single largest cost in the plan.
  The refusal is untouched. The docstring now carries the other half beside it —
  complete and narrow are both required and they pull against each other on
  purpose — with the measurement that shows what a wide claim costs.
- **`/zero:plan` says the same rule where the brief is written**, and runs the
  forecast before handing a plan to `/zero:build`. **`/zero:build` says what the
  ceiling actually is**: an upper bound, not a prediction, and raising it against
  a plan bound by its write sets changes nothing at all. Tooling cannot make this
  call — a plan whose author hedges every declaration is worse than one nobody
  narrowed — so the guidance ships with the command and is half the fix, not a
  note beside it.

## [1.5.1] - 2026-09-03

A re-read of every document after 1.5.0, against the code. The changelog and the
published set held; the preamble every skill reads had not caught up. Nothing the
orchestrator does changes.

### Fixed

- **The chain rules know about features.** `reference/chain-rules.md` is read at
  the head of every skill run, and it still counted fifteen skills and placed
  specifications, plan and run state at the project root without exception. It now
  counts sixteen and says that an open feature moves those three under
  `.zero/features/NNN-slug/` while the Context, `workers.json` and `design.json`
  stay the project's — the layout 1.5.0 introduced. Installed copies only receive
  this file when the version moves, which is why this release exists.
- **The README says what two reference documents are.** It described
  `docs/reference/gauntlet-loop-reference.md` as "the loop the orchestrator runs"
  and `designing-better-skills.md` as "the practices behind `skills/`". Both are
  third-party material — the industry pattern the loop draws on, and a case study in
  skill design — and are now introduced as such.

### Removed

- **The Word extract of the document set.** `docs/Zero-to-Ship.docx` was a
  snapshot of set 2.1 that nothing linked, nothing rebuilt, and that still called
  the first document the Vision. The rendered pages are the published set.

## [1.5.0] - 2026-09-02

The first document is now called what the playbook calls it, ongoing work has a
place to go, and finishing a piece of work is a checked act rather than a feeling.
Doc set 2.9.

### Changed

- **Vision is Intent.** The generator (`z2s/intent.py`), the skill (`/zero:intent`),
  the file (`Intent.html`), the published page (`Z2S-Intent.html`) and every live
  sentence that named the document. Identifiers are untouched (`VC`, `VS`, `SH`),
  and so is history: the M1–M17 plan pages and the entries below still say what was
  true when they were written. The published `Z2S-Vision.html` is a GENERATED
  redirect to the new page, so a link printed before the rename still lands; the
  pipeline sets a redirect page aside by name instead of failing on it.
- **A project written before the rename is never asked to rename anything.** A
  missing `Intent.html` is read from `Vision.html` (`chain.FORMERLY`); a context
  brief may still cite "the vision" as a term's source. Nothing on disk moves; new
  writes go to the new name. The interview state under `.zero/state/vision.md` and
  `state/briefs/vision.json` is not migrated — it is transient, and the next run of
  `/zero:intent` writes `intent.md` and reads `briefs/intent.json`.
- **The FSD's input-kind flow step formerly labelled "Intent" is "Purpose"**, so
  exactly one thing on the site is called Intent.

### Added

- **Features.** A feature is a piece of work with its own specifications, plan and
  run state under `.zero/features/NNN-slug/` (001 first), beside the project's shared
  Intent, Context, `workers.json` and `design.json`. Which feature is open is derived —
  the highest-numbered directory — never configured, never stored, and there is
  exactly one. Every generator keeps its code and follows it: `paths.resolve` is
  feature-aware for the specs, plan and state directories and nothing else, and a
  project with no `features/` directory resolves every path byte for byte as before
  (`selfhost.build --check` proves it on this repository's own set). The Context is
  the one document the chain reads and writes beside the project whatever is open;
  a feature's plan links to it three directories up.
- **`/zero:feature`**, the sixteenth skill. `open <slug>` creates the next feature
  and refuses while one is open, or without the shared Intent and Context. `close
  --date` runs the audit — every unit of the feature's plan passing, every retired
  identifier succeeded, every open question answered, nothing unshipped in the run
  ledger or the working tree — and closes as `complete` only when it is clean, else
  refuses and lists what is open. `close "<why>" --date` records those findings as
  `left` instead. The close is written into the feature's own Intent
  (`document.closed`, now an optional envelope field) through the same writer every
  status change uses. A closed feature refuses generation and building. `status`
  prints the open feature and its audit. Something small while a feature is open
  goes in by addendum, never as a second open feature.
- **Published scope for all of it**: FR-GEN-12, FR-GEN-13, FR-GEN-14, FR-SKL-10,
  NFR-OPS-07, ADR-19, their stories and use case, and milestone M18 claiming them;
  FR-DOC-01, FR-CTX-01 and the layout requirement amended in place and dated. The
  self-hosted set grows the same way (an `FR-FEA` area and milestone M5).

### Not in this release

- No `--feature` flag, no parallel features, no migration of an existing
  project-level set into a feature — the project set is the shared layer plus
  history. No `/zero:vision` alias skill: the README and `/zero:action` name the new
  command.

## [1.4.1] - 2026-09-02

The one live dispatch 1.4.0 was owed ran, on the same build, and passed. Two small
lies it surfaced, both fixed here; nothing the orchestrator does changes.

### Fixed

- **The build skill no longer promises a single-unit run.** Its argument hint offered
  "a single unit identifier to run", and `execute run` takes none — the only way to
  honour "exactly one dispatch" was to stop the run by hand after the second one
  started. The hint now says `[nothing]`, which is what the command accepts.
- **The stray notice stops offering a door that does not open.** It told every
  stray "declare a family", including a unit that declares no path any family is
  keyed on — where a family reaches nothing, because a family widens a declared
  claim and cannot invent one. The notice now says when the family door applies;
  `overlay` is named first, as the door that always does.

## [1.4.0] - 2026-09-02

The same live build was measured again on 1.3.0. Of nine findings, two were already
fixed and one was a mechanism that existed and nobody found. The rest were the
orchestrator being wrong about what a red check, a failing dependency or a regenerated
document means — and every one cost finished work.

### Added

- **A write family and an appendable path are declared once, in `workers.json`.**
  A migration is never one file: the SQL, the snapshot, the journal and the generated
  types move together, and a plan that declared the first alone reported the other
  four as strays on every migration the build made. `families` states that once —
  a unit whose declared writes touch `when` is read as writing every path in `also`,
  for the stray check and the collision check alike. `appendable` names the paths
  every unit adds a line to and none owns, which are neither. Both are read at run
  time like the gauntlet, so a running build absorbs them with no regeneration.
  (FR-EXE-06, amended)
- **The console says when a dispatch is a redispatch, and what is left.** A misfire
  charges no attempt, so the second dispatch of a unit printed `attempt 1` again and
  read as a first try. It now reads `dispatch M7-P1-T1 (attempt 1; redispatch after
  2 misfires, 1 left)`. The zero-misfire line is unchanged.

### Fixed

- **A red in a unit's own cheap layer is handed back, not thrown away.** The
  hand-back introduced in 1.3.0 ran only the checks a unit had not named, and a red
  in a unit's own unit tests discarded a finished forty-minute dispatch — which the
  worker that wrote those tests was the one person placed to fix. Every layer that
  needs no database, browser or person is now run before a dispatch is settled,
  declared or not, and handed back once. A layer already red before the dispatch is
  not handed back and charges nothing. (FR-EXE-17, amended)
- **A failing dependency with attempts left no longer blocks its dependents.** A
  misfire writes `failing` and the unit is dispatched again next iteration, but every
  dependent was marked blocked for that one iteration and cleared the next — a wave
  of `blocked` on the console for units nothing was wrong with. Only an exhausted or
  itself-blocked dependency blocks anything now, and a chain of blocked units clears
  in one pass when what it waited on passes. (FR-EXE-07, amended)
- **Regenerating a plan keeps every status and tick a run recorded.** Status lives in
  the document and nowhere else, and `plan.author` wrote a fresh one over it, so
  correcting a write list was a stop-the-run operation that left the build eleven
  units behind its own plan. Regeneration now carries each task's status and ticked
  criteria from the document on disk; only what the brief and detail files changed
  changes. (FR-DOC-06, amended)
- **The stray notice names the door.** The `overlay` correction shipped in 1.3.0 and
  a whole build ran without anybody finding it, because the notice named the problem
  and not the fix. It now names the ledger path, the family setting, and that neither
  needs a regeneration.
- **The build skill named a liveness tell that does not exist.** The dispatch log is
  written live, but a `claude -p` worker prints nothing until it exits, so an empty
  log is not a stopped worker. The skill now points at modification times under the
  dispatch directory and the repository — the signal the timeout already watches.

### Changed

- The published specification set is 2.8, dated 2026-09-02: four requirements
  amended in place, no new identifiers.

## [1.3.0] - 2026-08-29

A live build of a real project was instrumented against 1.2.10: 70 of 191 units, about
171 hours. Seventy-seven per cent of that was the builder dispatch — and **thirty-five
per cent of that was discarded on retries**, 46.8 hours across 36 superseded dispatches.
None of the causes were worker quality. Every one was something the orchestrator did.

### Added

- **The checks a unit never heard of are now in its brief, and are run before its
  dispatch is thrown away.** Seven of twelve gauntlet failures were whole-repository
  invariants no unit had been told existed — a package-wide scanner, a determinism
  check, a budget summed over files the unit never opened. Each discarded a finished
  dispatch and briefed a fresh worker from nothing, which began by rebuilding what was
  already on disk. A brief now names every such check and its command, the run runs
  them once the worker reports, and a red one goes back to the worker that broke it,
  once, in the dispatch it already worked in. What that turn changes is committed with
  the unit. (FR-EXE-17)
- **One published cost order for the verification layers**, cheapest first: static
  analysis, unit, integration, accessibility, end-to-end, performance, the CI gate,
  human review. A red layer took 25.4 minutes to reach a verdict of "no" because an
  end-to-end suite ran ahead of the static check that was going to fail. Not
  configurable, on the precedent the re-run rule already sets: a number that lets
  somebody hide a broken check is a number this method does not offer. (NFR-EXE-12)
- **A write list can be corrected without regenerating the plan.** Add paths to
  `overlay` in the run ledger, keyed by unit identifier; the next scheduling decision
  uses them. Widening only — narrowing a declared set would be a way of switching the
  disjointness check off — and the run records which correction it acted on.
  (FR-EXE-19)

### Fixed

- **A dispatch that never started no longer costs the unit anything.** Three failures
  to launch, seconds apart with no wait anywhere, spent a unit's whole misfire budget
  and blocked three units for the state of the host. Each failure now waits longer
  than the last, charges neither counter, and three in a row with nothing starting in
  between stops the run — which settles what is in flight and dispatches nothing
  further. Both routes into it, the launch that raised and the process that exited
  leaving no report, share one branch, so neither can be fixed while the other goes on
  doing it. (FR-EXE-18)
- **A unit is no longer retried for a failure another unit caused.** Two units were,
  and both retries were spent discovering exactly that. The run now records which
  layers are already failing before it dispatches anything, runs every stated layer at
  each milestone boundary so a latent failure surfaces near its cause, and reads from
  version-control history — never from a worker's assertion — whether another unit
  landed the file a failure names. No key joins the report contract for it: a claim
  the run can check for itself is a claim it should not be taking. (FR-EXE-20)
- **The published renderer dropped an amendment on the floor.** `R.usecases` had no
  `amended()` call, so the first amended use case would have rendered without it and
  nothing would have said so. Fixed, with a test asserting all four catalogue
  renderers make the call — the published renderer has one function per catalogue
  where the toolchain runtime has one generic path, so anything cross-cutting has to
  be wired into each.
- **The priority band was a bare literal in the published filter legend.** Renaming it
  in the toolchain would have passed every test and silently desynchronised the live
  site. It is a named constant now, and a test asserts the two agree.

### Changed

- **`main` is protected.** A pull request and a passing `gates` check are required,
  force-push and deletion are blocked, and `docs/*.html` is marked
  `linguist-generated`. This closes `M9-P3`, deferred since 2026-08-14 pending the
  owner's authorisation, and clears the three coverage warnings
  (`NFR-OPS-03`, `NFR-OPS-05`, `NFR-OPS-06`) that had printed on every run since.
- **`NFR-OPS-05` is amended and dated** for the single-maintainer case. GitHub forbids
  self-approval, so a requirement for a second person's review on every promotion is a
  requirement that nothing may ever be promoted — a rule that gets switched off rather
  than followed, and a rule switched off protects nothing. The obligation is read as
  the promotion request itself instead.
- Specification set 2.5 → 2.6. Five new identifiers, five dated amendments
  (`NFR-EXE-03`, `NFR-EXE-04`, `NFR-EXE-05`, `NFR-EXE-10`, `ADR-15`), a seventeenth
  milestone claiming every new one, and two new stories. No new decision for the
  alternative the owner rejected — `ADR-05` and `ADR-15` already record it.

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

[1.2.10]: https://github.com/apatheticus/z2s/compare/v1.2.9...v1.2.10
[1.2.9]: https://github.com/apatheticus/z2s/compare/v1.2.8...v1.2.9
[1.2.8]: https://github.com/apatheticus/z2s/compare/v1.2.7...v1.2.8
[1.2.7]: https://github.com/apatheticus/z2s/compare/v1.2.6...v1.2.7
[1.2.6]: https://github.com/apatheticus/z2s/compare/v1.2.5...v1.2.6
[1.2.5]: https://github.com/apatheticus/z2s/compare/v1.2.4...v1.2.5
[1.2.4]: https://github.com/apatheticus/z2s/compare/v1.2.3...v1.2.4
[1.2.3]: https://github.com/apatheticus/z2s/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/apatheticus/z2s/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/apatheticus/z2s/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/apatheticus/z2s/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/apatheticus/z2s/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/apatheticus/z2s/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/apatheticus/z2s/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/apatheticus/z2s/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/apatheticus/z2s/releases/tag/v0.1.0
