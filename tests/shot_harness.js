/* Manual tool, not a test. Writes PNG screenshots of the published
   documentation set so a person can look at the pages.

   No assertion is made here on purpose: a check that only writes images proves
   nothing, and wiring it into the Python suite would be a gate that always
   passes. The gate is a reader.

     node tests/shot_harness.js [outDir] [document ...]

   Pages are served from one intercepted https origin rather than opened from
   the filesystem — the same mechanism published_harness.js uses. A file:// page
   has an opaque origin where localStorage throws and nothing is a secure
   context, and both ports this repo would otherwise serve on are occupied.

   Light only: the published set defines no dark palette (shell.py:119), so
   light plus print is the whole mode set. The widths straddle the two real
   breakpoints, 980px and 720px (shell.py:628, shell.py:290).

   Nine shots a document: seven VIEWPORT captures, one at each width, plus one
   full-length capture at 1280 and one full-length print capture. The width
   shots are deliberately not full-page — a reader opens these at a fixed
   display size, and a several-thousand-pixel-tall image scales down until the
   type is unreadable, which shows nothing about a page. Above the fold at each
   breakpoint is where layout defects live; the two full-length shots keep the
   whole flow on record.

   Every shot waits for the page to stop moving first. The hero logo paints
   itself over about 1.73 seconds and the art below it lands in a stagger, so an
   early capture shows a half-drawn ghost rather than the page a reader sees.

   Exits 3 when Playwright or its browsers are not installed, so the caller can
   tell "no browser" from "failed" — a skip is never a pass (LD-04, NFR-VAL-05).
   Anything else is a failure and is reported as one. */

"use strict";

const fs = require("fs");
const path = require("path");

const HOST = "https://z2s.test/";
const DOCS = path.join(__dirname, "..", "docs");

const OUT = "/private/tmp/claude-501/-Volumes-Data-dev-zero-to-ship/" +
            "8eb8dea7-9e94-408e-b527-54223fa78f62/scratchpad/shots";

/* Either side of 980 and either side of 720, plus a phone, a laptop and a wide
   desktop. A width that only sits between breakpoints tests nothing the next
   one does not. */
const WIDTHS = [360, 719, 721, 979, 981, 1280, 1600];
const FULL_WIDTH = 1280;
const PRINT_WIDTH = 1280;
const VIEWPORT_HEIGHT = 900;

/* Long enough for the slowest finite animation in the published set — the logo's
   second stroke ends 1.73s in (.38s duration after a 1.35s delay,
   shell.py:108) — with room for a slower machine. A surprise animation that
   outlasts it degrades the shot to the old behaviour rather than wedging the
   run, and is counted and reported rather than passing quietly. */
const SETTLE_LIMIT = 5000;

/* A capture this tall is called out so nobody opens one expecting to read it:
   at a fixed display width it scales down until the type is gone.

   NOT a truncation check, though it was written as one. This Chromium stitches
   a full-page capture rather than taking one texture, and the two tallest shots
   here came back byte-for-byte the height of the page —
   Z2S-User-Stories 35573px and Z2S-SDD 30092px, each exactly the
   document.documentElement.scrollHeight measured in the same browser. Height
   alone cannot prove truncation either way; what would is a capture SHORTER
   than the page, which is why the number is reported rather than judged. */
const TALL = 30000;

/* index.html first: no browser test has ever opened it. */
const SAMPLE = [
  "index.html",
  "Z2S-Brief.html",
  "Z2S-Intent.html",
  "Z2S-PRD.html",
  "Z2S-FSD.html",
  "Z2S-User-Stories.html",
  "Z2S-SDD.html",
  "Z2S-Plan.html",
  "Z2S-Plan-M11.html"
];

function loadPlaywright() {
  try {
    return require("playwright");
  } catch (first) {
    try {
      const globals = require("child_process")
        .execSync("npm root -g", {encoding: "utf8"}).trim();
      return require(path.join(globals, "playwright"));
    } catch (second) {
      process.stderr.write("playwright is not installed: " + first.message + "\n");
      process.exit(3);
    }
  }
}

/* The report currently being filled. Listeners are registered ONCE per page and
   write into it, following z2s/render.js:79-95 — registering them per shot would
   charge one console error to every shot taken afterwards. */
let filling = null;

function listen(page) {
  page.on("pageerror", (error) => {
    if (filling) filling.pageErrors.push(String(error.message || error));
  });
  page.on("console", (message) => {
    if (!filling || message.type() !== "error") return;
    /* Only a resource this tool served is this document's business. The
       published documents pull two web fonts from a content delivery network
       that really does 404 sometimes, and how the page looks is not decided by
       whether somebody else's server answered. */
    const where = (message.location() || {}).url || "";
    if (where && where.lastIndexOf(HOST, 0) !== 0) return;
    filling.consoleErrors.push(String(message.text()));
  });
}

/* The body is built at load from inlined JSON: #main is empty in the markup and
   buildSections() appends one <section class="block"> per section. Waiting on
   that element is waiting on the runtime having actually run, which a fixed
   sleep is not. */
async function settled(page) {
  await page.waitForSelector("#main section.block", {state: "attached", timeout: 15000});
  await page.evaluate(() => document.fonts && document.fonts.ready);
  /* Two frames, so a relayout after a viewport change has been painted. */
  await page.evaluate(() => new Promise(
    (done) => requestAnimationFrame(() => requestAnimationFrame(done))));

  /* Then let whatever is still moving finish. The hero logo paints itself with
     two staggered stroke animations and is not done until about 1.73s
     (shell.py:107-108); a shot taken before that shows a half-drawn ghost.

     Asked AFTER the frame pair and after EVERY viewport change, not once after
     goto, because .heroArt is display:none below 720px (shell.py:290) — so
     going from 719 to 721 puts it back on screen and RESTARTS its animations.
     A wait that only happened at load would miss every width above the
     breakpoint.

     Dropping the infinite filter would hang the harness rather than fix it:
     .gloss runs `zsart-sheen 7.5s ... infinite` (shell.py:502) and its
     `finished` promise never resolves. */
  const done = await page.evaluate((limit) => {
    const running = document.getAnimations()
      .filter((a) => a.effect && a.effect.getComputedTiming().iterations !== Infinity)
      .map((a) => a.finished.catch(() => {}));
    return Promise.race([
      Promise.all(running).then(() => true),
      new Promise((stop) => setTimeout(() => stop(false), limit))
    ]);
  }, SETTLE_LIMIT);
  if (!done && filling) filling.stalled++;
}

/* PNG holds width and height as big-endian 32-bit integers at bytes 16 and 20,
   inside the IHDR chunk, which is always the first one. Reading them off the
   buffer beats a dependency and beats shelling out, and the height is the
   number that decides whether a capture is readable or was truncated. */
function measure(buffer, name) {
  return {name: name, width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20)};
}

async function shootDocument(context, name, outDir) {
  const report = {name: name, shots: 0, stalled: 0, tall: [],
                  pageErrors: [], consoleErrors: []};
  const stem = name.replace(/\.html$/, "");
  const page = await context.newPage();
  listen(page);
  filling = report;

  await page.goto(HOST + name, {waitUntil: "load"});
  await settled(page);

  /* Viewport only, not the full page. Above the fold at each breakpoint is
     where layout defects live, and it is the only capture a person can read at
     a fixed display size — a several-thousand-pixel-tall image arrives scaled
     down until the type is gone, which is a picture of grey stripes rather than
     a picture of a page. */
  for (const width of WIDTHS) {
    await page.setViewportSize({width: width, height: VIEWPORT_HEIGHT});
    await settled(page);
    await page.screenshot({
      path: path.join(outDir, stem + "-" + width + ".png"),
      fullPage: false
    });
    report.shots++;
  }

  /* One full-length capture, so the whole flow is still on record. Kept to a
     single width: the same content reflowed seven times is seven times the
     pixels and no more information. */
  await page.setViewportSize({width: FULL_WIDTH, height: VIEWPORT_HEIGHT});
  await settled(page);
  report.tall.push(measure(await page.screenshot({
    path: path.join(outDir, stem + "-full.png"),
    fullPage: true
  }), stem + "-full"));
  report.shots++;

  /* Paper, full length on purpose. Everything the accordion folds is expanded
     here, so this is the one shot that shows the whole document at once — and
     its height against the -full shot at the same width is the proof that
     emulateMedia really took effect rather than silently falling back. */
  await page.setViewportSize({width: PRINT_WIDTH, height: VIEWPORT_HEIGHT});
  await page.emulateMedia({media: "print"});
  await settled(page);
  report.tall.push(measure(await page.screenshot({
    path: path.join(outDir, stem + "-print.png"),
    fullPage: true
  }), stem + "-print"));
  report.shots++;

  filling = null;
  await page.close();
  return report;
}

async function main() {
  const argv = process.argv.slice(2);
  const outDir = argv.length ? argv[0] : OUT;
  const names = argv.length > 1 ? argv.slice(1) : SAMPLE;

  const missing = names.filter((n) => !fs.existsSync(path.join(DOCS, n)));
  if (missing.length) {
    process.stderr.write("not in " + DOCS + ": " + missing.join(", ") + "\n");
    process.exit(1);
  }

  fs.mkdirSync(outDir, {recursive: true});

  const {chromium} = loadPlaywright();
  const browser = await chromium.launch();
  const context = await browser.newContext({viewport: {width: 1280, height: 900}});

  /* Only this origin is intercepted; the web fonts are left to the real network
     so the shots show the typography a reader gets. */
  await context.route(HOST + "**", (route) => {
    const name = decodeURIComponent(new URL(route.request().url()).pathname.slice(1));
    const file = path.join(DOCS, name);
    if (!fs.existsSync(file)) return route.fulfill({status: 404, body: "not here"});
    route.fulfill({status: 200, contentType: "text/html; charset=utf-8",
                   body: fs.readFileSync(file, "utf8")});
  });

  let shots = 0, failed = 0, tall = 0, stalled = 0;
  for (const name of names) {
    const report = await shootDocument(context, name, outDir);
    shots += report.shots;
    failed += report.pageErrors.length + report.consoleErrors.length;
    process.stdout.write(
      report.name.padEnd(24) + " " + String(report.shots).padStart(2) + " shots · " +
      report.tall.map((t) => t.name.replace(/^.*-/, "") + " " + t.height + "px").join(" · ") +
      " · " + report.pageErrors.length + " page errors · " +
      report.consoleErrors.length + " console errors\n");
    stalled += report.stalled;
    if (report.stalled) {
      process.stdout.write("    STALLED:   " + report.stalled + " of this document's " +
                           "waits hit the " + SETTLE_LIMIT + "ms animation limit — " +
                           "those shots may show motion mid-flight\n");
    }
    report.tall.filter((t) => t.height > TALL).forEach((t) => {
      tall++;
      process.stdout.write("    VERY TALL: " + t.name + ".png is " + t.height +
                           "px — complete, but unreadable at any sane display size\n");
    });
    report.pageErrors.forEach((e) => process.stdout.write("    pageerror: " + e + "\n"));
    report.consoleErrors.forEach((e) => process.stdout.write("    console:   " + e + "\n"));
  }

  await browser.close();
  process.stdout.write("\n" + shots + " shots in " + outDir +
                       " · " + failed + " errors across " + names.length + " documents" +
                       (tall ? " · " + tall + " very tall" : "") +
                       " · " + stalled + " animation waits timed out\n");
  /* A page error is a defect worth a non-zero exit even though nothing here
     asserts: the caller is a person, and a silent 0 hides it. A very tall
     capture is NOT — it is a complete picture of a long document, and failing
     the run for it would train the reader to ignore the exit status. */
  if (failed) process.exit(1);
}

main().catch((error) => {
  process.stderr.write(String((error && error.stack) || error) + "\n");
  process.exit(/Executable doesn't exist|browserType\.launch/.test(String(error)) ? 3 : 1);
});
