/* The rendered-view check (M9-P2-T1). Opens each finished document in a real
   browser and reports what a reader can actually do with it.

   Everything above this check reads the document as data. A document can hold a
   sound specification, satisfy every structural rule, and still show a reader
   nothing at all — a runtime that throws on the first section leaves a page
   with a heading and no content, and no amount of reading the JSON says so.

   Reads one JSON request on stdin, writes one JSON response on stdout:

     {"pages": {"index.html": "<html>...", ...},
      "documents": ["index.html", ...]}

       -> {"documents": [{"name", "errors", "entries", "filtered",
                          "toggled", "band", "exercised"}, ...]}

   Every page is served from one intercepted origin, so relative links between
   documents resolve as they will on a static host, and no port has to be free.

   Exits 3 when Playwright or its browsers are not installed, so the caller
   reports the check as skipped rather than passed (LD-04, FR-GEN-03,
   NFR-VAL-05).

   Playwright is a development tool. Nothing it provides reaches a generated
   document, so the zero-runtime-dependency rule is untouched (NFR-ARC-03). */

"use strict";

function loadPlaywright() {
  try {
    return require("playwright");
  } catch (first) {
    /* Not installed in this project. A global install is normal and fine. */
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

const HOST = "https://z2s.test/";

/* What a reader can see. An entry hidden by the filter is hidden by the
   `hidden` property rather than by a class, so this asks for the state the
   runtime actually sets. */
const VISIBLE = () =>
  Array.prototype.filter.call(
    document.querySelectorAll(".catalogue .entry"),
    (el) => !el.hidden).length;

/* The band to switch off: the first one a visible entry belongs to that the
   toolbar actually offers. Not simply the first entry's, because a catalogue of
   decisions carries a standing where a requirement carries a priority, and a
   document holding both would otherwise be judged on the half with no band. */
const BANDED = () => {
  const offered = Array.prototype.map.call(
    document.querySelectorAll("[data-band]"), (el) => el.getAttribute("data-band"));
  const entries = Array.prototype.filter.call(
    document.querySelectorAll(".catalogue .entry"), (el) => !el.hidden);
  for (const entry of entries) {
    const band = entry.getAttribute("data-priority");
    if (band && offered.indexOf(band) !== -1) return band;
  }
  return null;
};

/* The report currently being filled. One page drives the whole set, so the
   listeners below are registered once and write into whichever document is
   being driven. Registering them per document left every earlier listener live,
   so one console error landed in the report of every document already driven —
   which is why the failure count varied from run to run.

   Ceiling, stated: an error that arrives after a document is finished with is
   recorded against the next one. Unavoidable while one page drives the set, and
   far smaller than counting the same error once per document. */
let filling = null;

function listen(page) {
  page.on("pageerror", (error) => {
    if (filling) filling.errors.push(String(error.message || error));
  });
  page.on("console", (message) => {
    if (!filling || message.type() !== "error") return;
    /* Only a resource this check served is this document's business. The
       published documents fetch two web fonts from a content delivery network,
       and what a reader can do with the document is not decided by whether
       somebody else's server answered. */
    const where = (message.location() || {}).url || "";
    if (where && where.lastIndexOf(HOST, 0) !== 0) return;
    filling.errors.push(String(message.text()));
  });
}

async function inspect(page, name) {
  const report = {name: name, errors: [], sections: 0, entries: 0,
                  filtered: null, toggled: null, band: null, exercised: []};
  filling = report;

  await page.goto(HOST + name, {waitUntil: "load"});

  /* What the runtime produced at all. A page with no sections is a page whose
     runtime gave up, whatever the specification behind it says. */
  report.sections = await page.evaluate(
    () => document.querySelectorAll("main section").length);

  report.entries = await page.evaluate(VISIBLE);
  if (!report.entries) return report;                 /* no catalogue to drive */
  report.exercised.push("entries");

  /* An entry's own identifier is the one keyword guaranteed to match exactly
     one entry, whatever the document is about. */
  const keyword = await page.$eval(".catalogue .entry:not([hidden])", (el) => el.id);
  const filter = await page.$("[data-filter]");
  if (filter) {
    await filter.fill(keyword);
    report.filtered = await page.evaluate(VISIBLE);
    await filter.fill("");
    report.exercised.push("filter");
  }

  /* Switching a band off has to remove at least the entries in it, so the
     check cannot pass against a dead toggle. */
  report.band = await page.evaluate(BANDED);
  const box = report.band ? await page.$('[data-band="' + report.band + '"]') : null;
  if (box) {
    await box.uncheck();
    report.toggled = await page.evaluate(VISIBLE);
    await box.check();
    report.exercised.push("band");
  }
  return report;
}

async function main(request) {
  const {chromium} = loadPlaywright();
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const pages = request.pages || {};

  await context.route(HOST + "**", (route) => {
    const name = decodeURIComponent(route.request().url().slice(HOST.length))
      .split("#")[0].split("?")[0];
    if (!Object.prototype.hasOwnProperty.call(pages, name)) {
      return route.fulfill({status: 404, contentType: "text/html", body: "missing"});
    }
    return route.fulfill({status: 200, contentType: "text/html", body: pages[name]});
  });

  const page = await context.newPage();
  listen(page);
  const documents = [];
  for (const name of request.documents || Object.keys(pages)) {
    documents.push(await inspect(page, name));
  }
  await browser.close();
  return {documents: documents};
}

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  main(JSON.parse(input)).then((answer) => {
    process.stdout.write(JSON.stringify(answer));
  }).catch((error) => {
    process.stderr.write(String(error && error.stack ? error.stack : error) + "\n");
    process.exit(1);
  });
});
