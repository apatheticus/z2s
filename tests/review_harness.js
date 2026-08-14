/* Test harness only. Opens two generated documents in one browser profile and
   reports what actually persisted between them.

   Two documents sharing one browser is the whole point of NFR-GEN-07, and it is
   not reachable outside a browser: it needs a real origin, a real localStorage
   and a real reload. Both documents are served from one host so they share that
   storage — which is exactly the condition under which a shared key would let
   one document overwrite the other's progress.

   Reads one JSON request on stdin, writes one JSON response on stdout:

     {"op": "review", "pages": {"a.html": "<!doctype html>…", …}}

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

const ORIGIN = "https://documents.test/";

/* What a reader can see, and what the document is carrying. */
const state = (page) => page.evaluate(() => {
  const boxes = Array.from(document.querySelectorAll("[data-review]"));
  const block = document.querySelector('script[type="application/json"]');
  return {
    progress: (document.querySelector("[data-progress]") || {}).textContent || "",
    checked: boxes.filter((box) => box.checked).map((box) => box.getAttribute("data-review")),
    boxes: boxes.length,
    storage: Object.fromEntries(Object.keys(localStorage)
      .map((key) => [key, localStorage.getItem(key)])),
    embedded: block ? block.textContent : "",
  };
});

async function review(request) {
  const {chromium} = loadPlaywright();
  const browser = await chromium.launch();
  const context = await browser.newContext();

  await context.route("**/*", (route) => {
    const name = route.request().url().slice(ORIGIN.length);
    const body = request.pages[name];
    if (body === undefined) return route.abort();
    return route.fulfill({status: 200, contentType: "text/html; charset=utf-8", body});
  });

  const names = Object.keys(request.pages);
  const page = await context.newPage();
  const out = {};

  /* Mark the first section of the first document. */
  await page.goto(ORIGIN + names[0]);
  await page.locator("[data-review]").first().check();
  out.firstAfterMarking = await state(page);

  /* The second document, in the same profile, must know nothing about it. */
  await page.goto(ORIGIN + names[1]);
  out.second = await state(page);

  /* And the first must still remember when the reader returns. */
  await page.goto(ORIGIN + names[0]);
  out.firstOnReturn = await state(page);

  /* Unticking is a change too: it has to survive a reload the same way. */
  await page.locator("[data-review]").first().uncheck();
  await page.goto(ORIGIN + names[0]);
  out.firstAfterClearing = await state(page);

  await context.close();
  await browser.close();
  return out;
}

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", async () => {
  const request = JSON.parse(input);
  if (request.op !== "review") {
    process.stderr.write("unknown op: " + request.op + "\n");
    process.exit(2);
  }
  try {
    process.stdout.write(JSON.stringify(await review(request)));
  } catch (error) {
    process.stderr.write(String(error && error.stack || error) + "\n");
    process.exit(/Executable doesn't exist|browserType.launch/.test(String(error)) ? 3 : 1);
  }
});
