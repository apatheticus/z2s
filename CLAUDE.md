# Z2S — Zero-to-Ship

Spec-driven build method + toolchain. Spec = machine input. Plan derived from spec.
Uncovered scope = build failure.

## Editing this file

Terse. Drop articles, use abbrevs, grammar irrelevant. Facts + cmds only, no narrative.
NOT a changelog: no shas, dates, counts, per-milestone history, "what a past session
did" — that's git + the ledger. Persist the RULE, never the episode.
Omit anything derivable from repo/git. Shorter beats complete.

## Source of truth

`docs/_build/specs/*.py` → `generate.py` → `docs/*.html`

NEVER hand-edit generated `.html` (ADR-02). Edit specs, regen.

`docs/` doubles as GitHub Pages source (`main` branch, `/docs` folder). Paths in
build scripts are relative to `_build/` — no abs/repo-relative path hardcoded.
**Push to `main` = publish.** Any commit touching `docs/` republishes the live site.

## Cmds

```
cd docs/_build && python3 generate.py   # regen rendered docs + coverage gate
cd docs/_build && python3 check.py      # validate RENDERED html + determinism
python3 -m unittest discover -s tests   # from repo root
python3 -m z2s.validate docs/*.html
python3 -m z2s.trace docs/*.html
python3 -m z2s.pipeline docs/*.html     # every gate in one run
python3 -m selfhost.build --check
python3 -m z2s.pack --check
```

Playwright IS installed globally on this machine, so the browser tests really run
Chromium (`test_browser` `test_catalogue` `test_trace` `test_plan` `test_render`
`test_status` `test_navigation`); each launches it once at import. Absent →
skipped, and a skip is never a pass. A browser-harness CRASH must fail the class,
never read as "no browser available" (LD-04 / NFR-VAL-05).

## Repo

github.com/apatheticus/z2s · public · MIT · `main`
GitHub acct → personal `apatheticus`
`.claude/` gitignored, incl ledger
Live: https://apatheticus.github.io/z2s/ — Pages, `main` + `/docs`, `.nojekyll`
(no Jekyll; `docs/_build/*.py` served raw, deliberate).

Locked decisions (LD-01…, M<n>-nn): `.claude/state/decisions.md`. **Read before
deciding anything**; not auto-loaded when cwd is `docs/`. Run ledger is per-branch,
`.claude/state/<branch>.md` — the M1–M16 one (`z2s.md`) was retired 2026-08-30 and
its decisions lifted into that file; git and `docs/` hold the rest of its history.

## Two codebases, deliberately

1. `docs/_build/` — renders the PUBLISHED specification set (`docs/*.html`).
2. `z2s/` — the toolchain a project uses. Plus `selfhost/` (the method's own set in
   `.zero/`, `python3 -m selfhost.build [--check]`), `skills/` (one SKILL.md per
   chain step), `reference/chain-rules.md`, `skills.lock.json`, `tests/`.

`docs/_build/` is NOT rewired onto `z2s/` — owner declined; FR-GEN-08 is satisfied
by the self-hosted set alongside, not by reversing it. Two renderers, two runtimes:
anything cross-cutting must be wired into BOTH, and each has its own gotchas below.

`generate.py` takes exactly ONE import from the toolchain — `z2s.gauntlet` (a leaf:
safety + schema only) — because what a prompt SAYS must not be spelled twice.
`tests/test_published.py` greps `generate.py`/`shell.py` for any loop sentence and
fails if one appears.

## Toolchain map (`z2s/`)

paths · shell · document · writer · runtime.js · tokens · styles · schema · validate
· gate · chain · vision · context · prd · fsd · stories · sdd · safety · trace ·
gauntlet · plan · render (+render.js) · pipeline · status · execute · learn ·
briefing · steps · author · project · update · ship · pack · design · restyle ·
dispatch · layers

Roles worth knowing before editing:

- `chain.py` — everything every generator BELOW the vision shares: prerequisite
  refusal (`chain.require`), envelope, identifiers, source register, gap phrasing,
  render/write, `chain.regenerate`, areas, addenda, amendments. A new generator
  brings only its own schema, forks and rules (NFR-ARC-01).
- Generator chain, each refusing without its prerequisites: vision → context → prd
  → fsd → stories → sdd → plan. Uniform driver `author.py`
  (`run <slug>` exit 3 = asking, 0 = written; `answer <slug> <fork> <choice>`).
- `schema.py` says what a document may CONTAIN; `safety.py` says what a run may DO.
  The dependency runs one way only (`validate` imports `safety`).
- `gauntlet.py` — the ONE place the execution contract is written down. Both doors
  render from it: the pasted prompt and the dispatched brief.
- `steps.py` — the one chain definition (steps, documents, prerequisites). `needs`
  (what a generator really refuses without) and `after` (published reading order)
  are kept APART on purpose.
- `trace.py` — universe, claims, coverage; read from DOCUMENTS, never a maintained
  list (ADR-04). Nothing it computes is stored (NFR-DAT-05).
- `layers.py` — a LEAF: the one cost order (`COST`, cheapest first, no config
  knob), which layers need infrastructure, the guards a unit never named, and the
  gauntlet loop itself. Imports `schema` and nothing else in the package — `status`
  wants `KNOWN` from it, so an import back would cycle. A caller hands in
  `runner(layer, command) -> int`.
- `status.py` — the only tool that edits a finished document; an edited document is
  byte-identical to a regenerated one. `execute.py` — the orchestrator.
  `dispatch.py` — the one launcher (workers, recovery turn, `status.ran`).
- `plan.py` — a plan is one document per milestone (index + `M<n>-*.html`).

## Standing invariants — do not "tidy" these away

- Web sources are RECORDED, never fetched. A test asserts no `z2s` module imports a
  network library.
- No module reads the clock or a random source except `pipeline.py` (it measures
  elapsed time and builds no document). `tests/test_writer.py` bans `import time` in
  every `z2s/*.py` but that one.
- Only the writer opens files for writing. `dispatch.py` is the ONE named exemption
  (it needs a live descriptor a child writes into WHILE it runs), pinned to a single
  `open`.
- `test_extraction_exists_in_exactly_one_place` has six NAMED exemptions —
  `render.py` `status.py` `execute.py` `author.py` `pack.py` `design.py` — each
  parsing something that is not a document. A new module parsing a document outside
  `validate.extract` is a defect, not a seventh exemption.
- Rules spelled TWICE on purpose, because a browser cannot import a Python module:
  trace routing, status rollup/queue, `Won't` = excluded. Both halves are tested
  against the same cases; changing one alone is the bug.
- Same-word collisions kept apart deliberately: trace `namespace` vs review
  `namespace` (the trace one is `owner` internally — it was silently shadowed once);
  `rollup` vs review `progress`; `auto` as an autonomy class vs a criterion kind;
  `AUTONOMOUS` and `AUTOMATED` holding the same string.
- `z2s/render.js` drives the WHOLE set on one page, so: `pageerror`/`console`
  listeners are registered ONCE in `main()` (registering them inside `inspect()`
  charges one event to every document already driven), and a console error whose
  `url` is outside `HOST` is IGNORED (the published docs pull web fonts from a CDN
  that really does 404 sometimes).
- Judge separation (FR-EXE-14) is structural: `judgement()` never receives the
  builder's report. Do not route it one.
- `reclaim()` / `abandoned()` and `dispatch.launch`'s three properties
  (`start_new_session=True`; output to a FILE never a pipe; grace via
  `popen.wait(timeout=GRACE)` never `time.sleep`) are load-bearing — see Constraints.
- Identifier grammar in `schema.GRAMMAR`/`PREFIXES`; trace universe = FR + NFR + ADR
  only. Two doors out of the universe: `priority: "Won't"` + a reason, or a `retired`
  reason (number reserved forever).
- Every gate is the same implementation wherever it is reached from: the plan
  generator checks coverage by calling `trace.py` against in-memory specs; `status`,
  `execute` and `ship` all judge a command through `safety.refusal`.

## Constraints

- A design record is only half of `/zero:design`. `design.author` writes exactly
  ONE file (`.zero/design.json`) and a generated document inlines its stylesheet,
  so nothing already written changes until `python3 -m z2s.restyle --root .` runs.
  The skill sequences the two; `design.author` must NEVER call the restyle, or it
  stops being the one-file write its tests rest on. `restyle` re-checks the design
  the way a first generation does — `design.forget()` then `design.theme` — because
  the theme is cached per root and the caller has usually just written the record.
- `restyle` re-renders, it does NOT re-route. `trace.route` injects a `links` map;
  running it here would add ~608 bytes to every specification document on every
  run and break `selfhost.build --check`. Measured 2026-08-21: a pure re-render of
  this repo's own 12-document `.zero/` set is byte-identical.
- A plan document's element id is `plan-spec` (index) or `milestone-spec`, NEVER
  the slug-derived `<slug>-spec` — every level of a plan carries the slug "plan".
  `validate.BLOCK` matches the embedding element by TYPE, so the id cannot be read
  back out of a file; anything re-rendering a set dispatches on the directory.
  `pipeline.regenerate` uses the slug form safely only because it discards output.
- `z2s.restyle --check` is a PREVIEW and exits 0 either way — unlike
  `selfhost.build --check` and `z2s.pack --check`. Never wire it into a gauntlet
  expecting a pending restyle to fail the run.
- Every dispatch is BOUNDED. `z2s/dispatch.py` is the one launcher — workers,
  the recovery turn, and `status.ran`. `execute.DEFAULT_TIMEOUT` 5400s; project
  `"timeout"` in `workers.json`, per-worker override, `null` = unbounded;
  `execute.bound(config, worker)` resolves it. Three things in `dispatch.launch`
  are load-bearing and must not be tidied apart: `start_new_session=True` (a
  worker's test runner outlives a kill of the direct handle), output to a FILE
  never a pipe (orphans holding the write end block the reaper, which is exactly
  why `subprocess.run(timeout=)` is NOT used), and the grace period is
  `popen.wait(timeout=GRACE)` never `time.sleep` — `tests/test_writer.py` bans
  `import time` in every `z2s/*.py` but `pipeline.py`.
- `dispatch.py` is the ONE exemption to "only the writer opens files for
  writing": it needs a live descriptor a child writes into WHILE it runs, and a
  log that appears only afterwards answers none of the questions a log is for.
  Named in `tests/test_writer.py`, with a second test pinning it to one `open`.
- `recover()` runs whatever the worker exited with. Reading the exit status
  first made it unreachable from the only case it exists for — anything killed
  or timed out exits non-zero — and a finished build was discarded and rebuilt.
  A timed-out or non-zero dispatch carries `ran=False`, so `misfired` charges
  the unit no attempt. The bound and the recovery turn are ONE mechanism;
  neither is safe without the other.
- A report may carry `landed: "<sha>"` when an earlier attempt already committed
  the work and `changes` is therefore empty. `execute.in_history` checks the
  SHAPE (`^[0-9a-f]{7,40}$`) BEFORE git sees it — worker text at a trust
  boundary — then `git show --name-only`. `settle` reads `report.get("landed")`
  itself so the bidirectional key test in `tests/test_gauntlet.py` needs no
  edit. The judge is shown `changed | landed`; `status.commit` is shown
  `changed` alone (the landed files are in history already).
- Anything said to a DISPATCHED worker only goes through the `records_status`
  door in `gauntlet.prompt` — `RUN_STATUS` (Status contract) and `RUN_GAUNTLET`
  (Verification gauntlet). NEVER into `LOOP`/`FANOUT`: those are carried by every
  published plan document, so a line there rewrites `docs/` and republishes the
  live site, and it would tell a pasted-prompt reader something untrue of them
  (they ARE the run). Gate: `git status docs/` empty after `generate.py`.
  Adding a new BLOCK to a brief instead breaks
  `test_the_run_adds_what_only_a_run_knows_and_nothing_else` — extend an
  existing block.
- A failed gauntlet layer is re-run ONCE (`execute.prove`) before it charges the
  unit; both runs failing keeps the original message verbatim. `status.ran` is
  latest-wins per layer, so the second run supersedes with no plumbing. No config
  knob — a layer needing three goes is broken in a way a knob hides.
  Disagreements go to `ledger["notes"]` and the run's line.
- `execute.strayed` checks a report's `changes` against the unit's declared
  `writes` through the SAME `writes`/`within`/`overlap` helpers `collides` uses.
  Records every out-of-set path in `ledger["strays"]`. Overlap w/ a unit that
  ran BESIDE it routes to `misfired()`, never `short()` — no attempt charged,
  one misfire spent, blocks at `attempts`. Writing outside the list is usually
  the only thing possible (a shared manifest no per-unit list can own);
  concurrency is the hazard. `recall()` puts `strays` back on `unit.entry` each
  round and `collides()` unions them w/ declared `writes`, so a pair that
  clashed once never pairs again. Who ran beside whom is recorded at DISPATCH
  (`run`'s `beside` map), never derived at settle: by the time the second of a
  pair returns the first is gone from `running`.
- `ledger["standing"][unit]` carries a rejected attempt's `changes` into the
  next brief ("Work already on the tree"), dropped only on a pass. NO
  `REPORT_SHAPE` key — the run already holds the report it rejected. The block
  says naming those files in `changes` is correct and not a claim of authorship,
  because `changes` is what the run commits from.
- A run REPORTS containers and never removes one. `execute.CONTAINERS` is
  `docker ps` and nothing else — no `rm`, `kill`, `stop`, `prune`, `down`,
  `remove`, ever, in any module. Tearing down a live database is not reliably a
  ten-second job, and a container an operator started for their own reasons is
  not the run's to destroy. A test asserts the word list.
- The recovery turn shares the BUILD timeout, and the published nine-hour figure
  depends on it. One dispatch of a wedged worker costs up to twice
  `execute.DEFAULT_TIMEOUT` — once building, once being asked what it built —
  and a timeout is a misfire rather than an attempt, so a project's `attempts`
  multiplies it. Give recovery its own (larger, or unbounded) bound and every
  arithmetic in `skills/build/SKILL.md` becomes a lie.
- A failure to START is bounded by `execute.LAUNCH_HALT` (consecutive, any unit)
  and NOT by the unit's counters. `misfired(charged=False)` is the whole of
  FR-EXE-18: it charges nothing, so the streak is the only brake — remove or
  weaken `halted()` and a host that can launch nothing loops for ever.
  `dispatch.pause` is `threading.Event().wait`; `time.sleep` is banned package-wide
  and there is no eighth exemption to ask for.
- Zero 3rd-party runtime deps (NFR-ARC-03). Py stdlib + browser built-ins only.
- IDs permanent. Addendum-only growth, never renumber.
- New FR/NFR joins coverage universe → needs claiming plan task or gate fails.
  Prefer extending existing req.
- Coverage gate not downgradable by config.
- Doc-set version/date (the `DOC` block's `version`+`date`, 9 spec modules +
  `generate.py` = 10 files) is the OWNER's call — offer it as a fork, never bump silently.
  Standing precedent: bump + redate whenever a dated amendment lands, else the
  control block reads older than an "Amended since" row on the same page.
- Plugin release = bump `version` in BOTH `.claude-plugin/plugin.json` and
  `marketplace.json`, then `python3 -m z2s.pack` (the lock pins the version).
  The marketplace one is what a runtime compares to decide an update exists;
  code changes alone never surface as an update.
- Plugin name is `zero`, marketplace name is `z2s` — the MARKETPLACE name is the
  `name` field in `.claude-plugin/marketplace.json`, NOT the repo path, and a
  collision silently replaces another repo's registration. Install is
  `/plugin marketplace add apatheticus/z2s` then `/plugin install zero@z2s`.
  Claude Code always namespaces a plugin's skills, so the chain reads `/zero:vision`
  … `/zero:build`. Exactly one skill (`questions`) is model-visible; the rest carry
  `disable-model-invocation`, and `z2s.pack`'s lint checks BOTH directions.
- NEVER spell a design-token key `token` in any JSON a project holds (brief,
  record, config). `safety.py` reads `token: "<literal>"` as a credential and
  fails the scan — correct everywhere else, wrong only here. Use `name`.
  `.zero/design.json`'s `refused[]`/`clamped[]` may keep `"token": one.token`:
  never a literal, so never flagged.
- A gauntlet command in `workers.json` is a LIST OF WORDS, never a shell line.
  `execute.settings` refuses a string; `status.ran` runs the list with no shell,
  so a glob, a pipe, `&&` or `$VAR` never expands. Two modules, one rule — the
  reason `project.DEFAULT_GAUNTLET` shipped a string nothing would accept.
- A worker's report has ONE schema, `gauntlet.REPORT_SHAPE`: it renders the
  brief's Report contract AND `execute.check_report` validates against it.
  Adding a key to either half alone is the defect the bidirectional test in
  `tests/test_gauntlet.py` exists to catch. Its example values must never look
  like a real plan identifier — that block rides in EVERY brief, so a plausible
  one appears in every unit's brief and a worker may copy it back.
- The "Status contract" block is the one part of a prompt that must NOT be
  identical in both doors, which is why it is absent from
  `TestTheDocumentAndTheRunnerAgree.SHARED`. A pasted prompt has no run and its
  reader sets the status (`gauntlet.OWN_STATUS`); a brief this orchestrator
  dispatched is graded by the run (`RUN_STATUS`), and telling that worker to set
  its own status is an instruction to grade its own work.

## Known

- A plan is one document per milestone in BOTH renderers: `Z2S-Plan.html` is the
  index (prompts, waves, prerequisites, coverage) plus `Z2S-Plan-M<n>.html` flat
  beside the other documents. The index lists milestones as TABLE ROWS, never
  entries — every phase/task/criterion is declared on its own page, and repeating
  them declares each id twice and FAILS `z2s.validate` on duplicate identifiers.
  `SIZE_BUDGET` 2048 KB; lowering it is the owner's call, not a side effect.
- **Measure `CHROME_BUDGET` headroom before adding ANY css/js** to `z2s/styles.py`
  or `z2s/runtime.js` — never trust a number written down here:
  `python3 -c "from tests import test_styles; from z2s import document, shell;
  print(shell.CHROME_BUDGET - (len(test_styles.specimen().encode()) -
  len(document.serialise(test_styles.SPEC).encode())))"`. Condense comments first;
  raising the budget is the owner's call.
- `z2s.pipeline` has SIX gates since M16; the sixth (`design`) reports
  **`not run: design`** on any project with no `.zero/design.json`. Both the
  published set and the self-hosted set are such projects, so
  `gates: 5 passed · 0 failed · 1 skipped` is the CORRECT steady state there —
  not a regression. A record that exists but cannot be parsed is a FAILURE, a
  record behind its sources is a WARNING.
- `docs/_build/shell.py` has ONE renderer per catalogue (`R.requirements`,
  `R.stories`, `R.usecases`, `R.decisions`) — unlike `z2s/runtime.js`, which has
  one generic `requirement()`. So anything cross-cutting (amendments, chips,
  search text) must be wired into EACH renderer; wiring one leaves the others
  silently dropping the data. `amended()` was on requirements only until M16;
  `R.usecases` still has no `amended()` call (no use case carries one yet).
- Section key `intro` is DEAD in `z2s/runtime.js` — only `lede` renders — while the
  PUBLISHED `docs/_build/shell.py` runtime renders `intro`. The two codebases
  genuinely differ here. `intro` stays in `schema.PROSE_FIELDS` so plain-language
  checks still cover the key. A new toolchain section uses `lede`.
- `check.py` render check = SKIPPED w/o browser. To run: serve over HTTP
  (`python3 -m http.server <port> --directory docs`), never `file://`.
  Port 8765 already in use on this machine.
