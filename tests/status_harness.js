/* Test harness only. Opens plan documents in a real browser and reports what a
   reader can actually see of progress: the rollup figures at milestone and
   phase level, how far each bar is filled, and the queue of human-review
   criteria still waiting on somebody.

   The question this answers and no amount of reading the data can: whether the
   figures a reader sees are DERIVED at load time. A stored total renders
   identically until the day it disagrees with the tasks beneath it, so the
   Python side drives this twice — once, then again after a status is written
   back — and the difference is the proof (M10-P3-T1-C1).

   Every page is served from one intercepted origin, the same trick the plan and
   trace harnesses use: no port, no server, and the links between documents
   resolve the way they will on a static host.

   Reads one JSON request on stdin, writes one JSON response on stdout:

     {"op": "status", "pages": {"M1.html": "<html>"}, "documents": ["M1.html"]}

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

const HOST = "https://z2s.test/";

/* Read off the rendered page rather than off the specification: the whole claim
   under test is that what the reader sees was computed from the tasks. */
const SEEN = () => {
  const rollups = {};
  const fills = {};
  Array.from(document.querySelectorAll("[data-rollup]")).forEach((one) => {
    const name = one.getAttribute("data-rollup");
    const figures = one.querySelector(".figures");
    const fill = one.querySelector(".fill");
    rollups[name] = figures ? figures.textContent : "";
    fills[name] = fill ? fill.style.width : "";
  });
  const queue = document.querySelector("[data-queue]");
  return {
    rollups,
    fills,
    queueShown: Boolean(queue && queue.checkVisibility()),
    queueOpen: Boolean(queue && queue.open),
    queue: queue
      ? Array.from(queue.querySelectorAll("li a")).map((a) => a.textContent)
      : [],
    /* A queue entry has to lead somewhere: an outstanding item a reviewer
       cannot reach is a list, not a queue. */
    targets: queue
      ? Array.from(queue.querySelectorAll("li a")).map((a) => a.getAttribute("href"))
      : [],
    entries: document.querySelectorAll(".catalogue .entry").length,
    errors: [],
  };
};

async function drive(request) {
  const {chromium} = loadPlaywright();
  let browser;
  try {
    browser = await chromium.launch();
  } catch (error) {
    process.stderr.write("no browser is installed: " + error.message + "\n");
    process.exit(3);
  }
  const context = await browser.newContext();
  await context.route(HOST + "**", (route) => {
    const name = new URL(route.request().url()).pathname.replace(/^\//, "");
    const body = request.pages[name];
    if (body === undefined) return route.fulfill({status: 404, body: "absent"});
    return route.fulfill({status: 200, contentType: "text/html", body});
  });

  const reports = [];
  for (const name of request.documents) {
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(String(error.message)));
    await page.goto(HOST + name, {waitUntil: "load"});
    const seen = await page.evaluate(SEEN);
    seen.name = name;
    seen.errors = errors;
    reports.push(seen);
    await page.close();
  }

  await browser.close();
  return {documents: reports};
}

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  drive(JSON.parse(input)).then((answer) => {
    process.stdout.write(JSON.stringify(answer));
  }).catch((error) => {
    process.stderr.write(String(error && error.stack ? error.stack : error) + "\n");
    process.exit(1);
  });
});
