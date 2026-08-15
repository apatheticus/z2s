/* Test harness only. Drives a SET of documents in a real browser and reports
   what happens when a reader follows a trace: which file they land in, whether
   the entry they were sent to is actually on screen, and whether it is marked.

   A set is the point. Routing cannot be checked one document at a time — the
   question is whether a reference in one file opens the right entry in another,
   and a single page can only ever answer "the link had an href".

   Every page is served from one intercepted origin, so relative links between
   them resolve the way they will on a static host (FR-TRC-07).

   Reads one JSON request on stdin, writes one JSON response on stdout:

     {"op": "trace", "pages": {"<name>.html": "<html>", ...},
      "start": "<name>.html", "away": "<id>", "local": "<id>"}

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

/* What a reader can actually see and where they are, asked of the browser
   rather than inferred: an entry inside a closed fold is hidden by a mechanism
   that is not display, and a marked entry is marked in the DOM or not at all. */
const LANDED = (id) => {
  const el = document.getElementById(id);
  return {
    file: location.pathname.replace(/^\//, ""),
    hash: location.hash,
    found: Boolean(el),
    visible: Boolean(el && el.checkVisibility()),
    marked: Boolean(el && el.classList.contains("marked")),
  };
};

async function follow(page, id) {
  await page.click('a.chip[href$="#' + id + '"]');
  await page.waitForTimeout(120);
  return page.evaluate(LANDED, id);
}

async function main(request) {
  const {chromium} = loadPlaywright();
  let browser;
  try {
    browser = await chromium.launch();
  } catch (error) {
    process.stderr.write("no browser: " + error.message + "\n");
    process.exit(3);
  }

  const context = await browser.newContext({viewport: {width: 1280, height: 900}});
  const page = await context.newPage();
  await page.route(HOST + "**", (route) => {
    const name = new URL(route.request().url()).pathname.replace(/^\//, "");
    const body = request.pages[name];
    if (body === undefined) return route.fulfill({status: 404, body: "no such page"});
    return route.fulfill({contentType: "text/html; charset=utf-8", body});
  });

  await page.goto(HOST + request.start, {waitUntil: "load"});
  const chips = await page.evaluate(() =>
    Array.from(document.querySelectorAll("a.chip, span.chip")).map((el) => ({
      id: el.textContent,
      href: el.getAttribute("href"),
      link: el.tagName.toLowerCase() === "a",
    })));

  const away = await follow(page, request.away);

  await page.goto(HOST + request.start, {waitUntil: "load"});
  const local = await follow(page, request.local);

  await browser.close();
  return {chips, away, local};
}

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  const request = JSON.parse(input);
  main(request).then((answer) => {
    process.stdout.write(JSON.stringify(answer));
  }).catch((error) => {
    process.stderr.write(String(error && error.stack || error) + "\n");
    process.exit(1);
  });
});
