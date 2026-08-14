/* Test harness only. Drives a generated catalogue in a real browser and reports
   what a reader would actually be looking at — which entries are on screen,
   which groups are folded, what the band counts say, whether a deep link opened
   what it landed in, and whether a reviewer's ticks survive a reload.

   None of this is answerable outside a browser: a closed <details> hides its
   content by a mechanism that is not display, storage needs a real origin, and
   a frame budget needs a real clock.

   The document is served over an intercepted https URL rather than set as page
   content. A blank page has an opaque origin, where localStorage throws, so the
   persistence check would silently test nothing.

   Reads one JSON request on stdin, writes one JSON response on stdout:

     {"op": "catalogue", "html": "...", "bulk": "...", "bulkWord": "..."}

   Exits 3 when Playwright or its browsers are not installed, so the Python
   suite reports the check as skipped rather than passed (LD-04, FR-GEN-03). */

"use strict";

function loadPlaywright() {
  try {
    return require("playwright");
  } catch (first) {
    try {
      const globals = require("child_process")
        .execSync("npm root -g", {encoding: "utf8"}).trim();
      return require(require("path").join(globals, "playwright"));
    } catch (second) {
      process.stderr.write("playwright is not installed: " + first.message + "\n");
      process.exit(3);
    }
  }
}

const ORIGIN = "https://z2s.test/document.html";

async function open(browser, html) {
  const context = await browser.newContext({viewport: {width: 1280, height: 900}});
  const page = await context.newPage();
  await page.route("https://z2s.test/**", (route) =>
    route.fulfill({contentType: "text/html; charset=utf-8", body: html}));
  await page.goto(ORIGIN, {waitUntil: "load"});
  return {context, page};
}

/* What the reader can see, asked of the browser rather than inferred from a
   style: a closed <details> hides its content without changing display. */
const VISIBLE = () => Array.from(document.querySelectorAll(".catalogue .entry"))
  .filter((el) => el.checkVisibility()).map((el) => el.id);

const STATE = () => ({
  visible: Array.from(document.querySelectorAll(".catalogue .entry"))
    .filter((el) => el.checkVisibility()).map((el) => el.id),
  groups: Array.from(document.querySelectorAll(".catalogue .area"))
    .map((el) => ({area: el.dataset.area, open: el.open, shown: el.checkVisibility()})),
  counts: Object.fromEntries(Array.from(document.querySelectorAll("[data-count]"))
    .map((el) => [el.dataset.count, el.textContent])),
  noMatch: Array.from(document.querySelectorAll(".catalogue .no-match"))
    .map((el) => ({shown: el.checkVisibility(), text: el.textContent})),
  progress: (document.querySelector("[data-progress]") || {}).textContent || "",
});

async function filter(page, word) {
  await page.fill("[data-filter]", word);
  return page.evaluate(STATE);
}

async function catalogue(request) {
  const {chromium} = loadPlaywright();
  const browser = await chromium.launch();
  const out = {};

  const {context, page} = await open(browser, request.html);

  out.initial = await page.evaluate(STATE);

  /* --- the keyword filter, one field at a time ---------------------------- */
  out.fields = {};
  for (const [field, word] of Object.entries(request.words || {})) {
    out.fields[field] = (await filter(page, word)).visible;
  }

  out.narrowed = await filter(page, request.narrow || "");
  out.nothing = await filter(page, request.absent || "zzzznothing");

  /* --- the two filters composing ----------------------------------------- */
  await page.fill("[data-filter]", request.shared || "");
  out.sharedOnly = await page.evaluate(VISIBLE);
  await page.uncheck('[data-band="' + (request.band || "Must") + '"]');
  out.composed = await page.evaluate(STATE);
  await page.check('[data-band="' + (request.band || "Must") + '"]');
  await page.fill("[data-filter]", "");

  /* --- folding ------------------------------------------------------------ */
  await page.click("[data-collapse]");
  out.collapsed = await page.evaluate(STATE);
  await page.click("[data-expand]");
  out.expanded = await page.evaluate(STATE);

  /* --- a deep link into a folded group ------------------------------------ */
  /* Asked of the routine directly, with no navigation involved. Chromium opens
     a <details> around a fragment target by itself, so the link check below
     cannot tell whether the runtime did the work or the browser did. */
  await page.click("[data-collapse]");
  out.revealed = await page.evaluate((id) => {
    const target = document.getElementById(id);
    window.Z2S.catalogue.reveal(target);
    return {
      groupOpen: target.closest("details").open,
      stillFolded: Array.from(document.querySelectorAll(".catalogue .area"))
        .filter((el) => !el.open).map((el) => el.dataset.area),
    };
  }, request.target);

  /* The hash is set in the page rather than navigated to, because a fresh load
     starts every group open and the fold this is meant to open would not
     exist. */
  await page.click("[data-collapse]");
  await page.evaluate((id) => { window.location.hash = "#" + id; }, request.target);
  out.deepLink = await page.evaluate((id) => {
    const target = document.getElementById(id);
    const group = target && target.closest("details");
    const box = target && target.getBoundingClientRect();
    return {
      found: !!target,
      marked: !!target && target.classList.contains("marked"),
      groupOpen: !!group && group.open,
      visible: !!target && target.checkVisibility(),
      onScreen: !!box && box.top >= 0 && box.top <= window.innerHeight,
    };
  }, request.target);

  /* Only the group holding the target opened. Without this the check would pass
     on a runtime that simply expanded everything. */
  out.stillFolded = await page.evaluate(() =>
    Array.from(document.querySelectorAll(".catalogue .area"))
      .filter((el) => !el.open).map((el) => el.dataset.area));

  /* --- review ticks, across a reload -------------------------------------- */
  await page.goto(ORIGIN, {waitUntil: "load"});
  for (const id of request.tick || []) {
    await page.check('[data-review="' + id + '"]');
  }
  out.ticked = await page.evaluate(STATE);
  await page.reload({waitUntil: "load"});
  out.reloaded = await page.evaluate(() => ({
    checked: Array.from(document.querySelectorAll("[data-review]"))
      .filter((box) => box.checked).map((box) => box.dataset.review),
    progress: document.querySelector("[data-progress]").textContent,
  }));
  await page.click("[data-reset]");
  out.reset = await page.evaluate(() => ({
    checked: Array.from(document.querySelectorAll("[data-review]"))
      .filter((box) => box.checked).map((box) => box.dataset.review),
    progress: document.querySelector("[data-progress]").textContent,
  }));
  await page.reload({waitUntil: "load"});
  out.afterReset = await page.evaluate(() =>
    Array.from(document.querySelectorAll("[data-review]"))
      .filter((box) => box.checked).length);
  await context.close();

  /* --- the frame budget, at the stated catalogue size ---------------------- */
  const bulk = await open(browser, request.bulk);
  out.bulk = await bulk.page.evaluate((word) => {
    const box = document.querySelector("[data-filter]");
    const runs = [];
    /* Measured around the work the reader's keystroke actually causes, and read
       back afterwards so an engine cannot defer the layout past the clock. */
    for (let i = 0; i < 5; i++) {
      box.value = i % 2 ? word : word.slice(0, -1);
      const started = performance.now();
      box.dispatchEvent(new Event("input", {bubbles: true}));
      runs.push(performance.now() - started);
    }
    box.value = word;
    box.dispatchEvent(new Event("input", {bubbles: true}));
    return {
      entries: document.querySelectorAll(".catalogue .entry").length,
      matched: Array.from(document.querySelectorAll(".catalogue .entry"))
        .filter((el) => !el.hidden).length,
      worst: Math.max.apply(null, runs),
      runs: runs,
    };
  }, request.bulkWord);
  await bulk.context.close();

  await browser.close();
  return out;
}

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", async () => {
  const request = JSON.parse(input);
  if (request.op !== "catalogue") {
    process.stderr.write("unknown op: " + request.op + "\n");
    process.exit(2);
  }
  try {
    process.stdout.write(JSON.stringify(await catalogue(request)));
  } catch (error) {
    process.stderr.write(String(error && error.stack || error) + "\n");
    process.exit(/Executable doesn't exist|browserType.launch/.test(String(error)) ? 3 : 1);
  }
});
