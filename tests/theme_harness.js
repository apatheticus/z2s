/* Drives one generated document in a real browser under both colour schemes.

   The only way to know that light-dark() RESOLVED rather than merely appearing
   in the text of the style block. A document whose token block reads correctly
   and whose @supports guard is malformed renders unstyled, and every check that
   reads the file rather than the page passes anyway.

   Served from one intercepted origin rather than set as content: the page has
   to be same-origin for computed styles to read the way they will for a reader
   opening the file.

   Exits 3 when Playwright or its browsers are not installed, so the Python
   suite reports the check as skipped rather than passed (LD-04, NFR-VAL-05).
   Anything else is a failure and is reported as one. */

"use strict";

const fs = require("fs");
const path = require("path");

const HOST = "https://z2s.test/";

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

const READ = `(function(){
  var body = getComputedStyle(document.body);
  var root = getComputedStyle(document.documentElement);
  return {background: body.backgroundColor, colour: body.color,
          scheme: root.colorScheme,
          border: root.getPropertyValue('--z2s-border').trim()};
})()`;

async function main() {
  const request = JSON.parse(fs.readFileSync(0, "utf8"));
  const text = fs.readFileSync(request.file, "utf8");
  const {chromium} = loadPlaywright();

  let browser;
  try {
    browser = await chromium.launch();
  } catch (error) {
    process.stderr.write("no browser binary: " + error.message + "\n");
    process.exit(3);
  }

  const seen = {errors: []};
  for (const scheme of ["light", "dark"]) {
    const context = await browser.newContext({colorScheme: scheme});
    const page = await context.newPage();
    page.on("pageerror", e => seen.errors.push(String(e)));
    await page.route(HOST + "**", route =>
      route.fulfill({contentType: "text/html", body: text}));
    await page.goto(HOST + "doc.html");

    seen[scheme] = await page.evaluate(READ);

    /* A reader who has chosen a scheme outranks the one their system reports. */
    for (const forced of ["dark", "light"]) {
      await page.evaluate(
        one => document.documentElement.setAttribute("data-theme", one), forced);
      seen[scheme + ":" + forced] =
        (await page.evaluate(READ)).background;
    }
    await page.evaluate(() => document.documentElement.removeAttribute("data-theme"));

    /* Paper is light, whatever the screen is. Without this a reader on a dark
       screen prints a page of black ink. */
    await page.emulateMedia({media: "print"});
    seen[scheme + ":print"] = (await page.evaluate(READ)).background;

    await context.close();
  }

  process.stdout.write(JSON.stringify(seen));
  await browser.close();
}

main().catch(error => {
  process.stderr.write(String(error && error.stack || error) + "\n");
  process.exit(1);
});
