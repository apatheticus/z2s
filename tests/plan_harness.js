/* Test harness only. Drives a generated plan — the index and one milestone
   document — in a real browser, and reports what a reader can actually do with
   it: follow a wave into the milestone it names, read a task's failing test,
   see which acceptance criteria are met and that none of them can be ticked by
   hand, follow a task's claim up into the specification that states it, and
   take a copy of the execution instructions.

   A set again, and for the same reason as the trace harness: the questions here
   are about links between files. A plan whose waves point nowhere and whose
   claims point at a document the reader cannot reach is a plan that reads
   correctly on one page and fails as a set.

   Every page is served from one intercepted origin, so the relative links
   between the plan and the specifications resolve as they will on a static
   host. Two directories, because that is the documented layout: the plan lives
   in `plan/` and the specifications in `specs/` beside it.

   Reads one JSON request on stdin, writes one JSON response on stdout:

     {"op": "plan", "pages": {"plan/index.html": "<html>", ...},
      "index": "plan/index.html", "milestone": "M1",
      "task": "<id>", "claim": "<id>", "met": "<criterion id>",
      "unmet": "<criterion id>"}

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

/* Where the reader is, and what is on screen there. Asked of the browser rather
   than inferred: an entry inside a closed fold is hidden by a mechanism that is
   not display, and a disabled control is disabled in the DOM or not at all. */
const WHERE = (ids) => {
  const at = (id) => document.getElementById(id);
  /* One folded block of instructions: is it there, is it a fold, and is it
     shut? A prompt that renders open buries the document it sits in. */
  const fold = (within, id) => {
    const el = within ? within.querySelector("#" + CSS.escape(id)) : null;
    return el ? {tag: el.tagName.toLowerCase(), open: el.open,
                 copy: Boolean(el.querySelector("button[data-copy]"))} : null;
  };
  const task = at(ids.task);
  const met = at(ids.met);
  const unmet = at(ids.unmet);
  const box = (el) => {
    const input = el ? el.querySelector("input") : null;
    return input ? {checked: input.checked, disabled: input.disabled} : null;
  };
  const chip = task
    ? Array.from(task.querySelectorAll("a.chip"))
        .filter((a) => a.textContent === ids.claim)[0]
    : null;
  return {
    file: location.pathname.replace(/^\//, ""),
    hash: location.hash,
    task: Boolean(task),
    taskVisible: Boolean(task && task.checkVisibility()),
    tdd: task ? Array.from(task.querySelectorAll(".tdd dt")).map((d) => d.textContent)
              : [],
    tddOpen: Boolean(task && task.querySelector(".tdd") &&
                     task.querySelector(".tdd").open),
    criteria: task ? task.querySelectorAll(".criterion").length : 0,
    met: box(met),
    unmet: box(unmet),
    claim: chip ? chip.getAttribute("href") : null,
    waves: Array.from(document.querySelectorAll(".waves .wave")).map((wave) =>
      Array.from(wave.querySelectorAll("a")).map((a) => ({
        unit: a.textContent, href: a.getAttribute("href"),
      }))),
    prompts: Array.from(document.querySelectorAll(".prompts .prompt"))
      .map((one) => one.id),
    /* M14: every granularity carries its own instructions, and every one of
       them is shut until somebody asks for it. Asked of the browser because
       "closed" is a property of the element, not of the markup we generated. */
    firstSection: (document.querySelector(".section") || {}).id || null,
    unitPrompt: fold(task, "prompt-" + ids.task),
    phasePrompt: fold(document.querySelector('[data-area="' + ids.phase + '"]'),
                      "prompt-" + ids.phase),
    milestonePrompt: fold(document, "prompt-" + ids.milestone),
    /* Where in the card it sits. A prompt a reader has to scroll past the whole
       task to find is a prompt they will not use (M14-04). */
    promptIsFirst: Boolean(task && task.querySelector("h4 + .prompts")),
    copyButtons: document.querySelectorAll(".prompts .copy").length,
  };
};

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
  /* Without it the copy button reports the refusal rather than the copy, which
     is correct behaviour and proves nothing about the copy. */
  try {
    await context.grantPermissions(["clipboard-read", "clipboard-write"],
                                   {origin: HOST.replace(/\/$/, "")});
  } catch (error) {
    /* Some builds do not know the permission name; the button is still checked
       for having done something, just not for what. */
  }

  const page = await context.newPage();
  await page.route(HOST + "**", (route) => {
    const name = new URL(route.request().url()).pathname.replace(/^\//, "");
    const body = request.pages[name];
    if (body === undefined) return route.fulfill({status: 404, body: "no such page"});
    return route.fulfill({contentType: "text/html; charset=utf-8", body});
  });

  await page.goto(HOST + request.index, {waitUntil: "load"});
  const index = await page.evaluate(WHERE, request);

  /* The copy button, on the instructions for this milestone. */
  const button = 'details#prompt-' + request.milestone + " .copy";
  await page.click("details#prompt-" + request.milestone + " > summary");
  const before = await page.textContent(button);
  await page.click(button);
  await page.waitForTimeout(150);
  const after = await page.textContent(button);
  let clipboard = null;
  try {
    clipboard = await page.evaluate(() => navigator.clipboard.readText());
  } catch (error) {
    clipboard = null;
  }

  /* Follow the wave into the milestone it names. */
  await page.click('.waves .wave a:text-is("' + request.milestone + '")');
  await page.waitForTimeout(150);
  const milestone = await page.evaluate(WHERE, request);

  /* A word that appears ONLY inside a prompt body must not bring every task
     back. The whole keyword box stops working the day prompt text is folded
     into what a search reads (M14). */
  await page.fill("input[data-filter]", request.promptWord);
  await page.waitForTimeout(150);
  const searched = await page.evaluate(() => ({
    showing: Array.from(document.querySelectorAll(".catalogue .entry"))
      .filter((one) => one.checkVisibility()).length,
    noMatch: Boolean(document.querySelector(".no-match") &&
                     document.querySelector(".no-match").checkVisibility()),
  }));
  await page.fill("input[data-filter]", "");
  await page.waitForTimeout(150);

  /* Follow the task's claim up into the specification that states it. */
  await page.click('#' + request.task + ' a.chip:text-is("' + request.claim + '")');
  await page.waitForTimeout(200);
  const claimed = await page.evaluate((id) => {
    const el = document.getElementById(id);
    return {
      file: location.pathname.replace(/^\//, ""),
      hash: location.hash,
      found: Boolean(el),
      visible: Boolean(el && el.checkVisibility()),
      marked: Boolean(el && el.classList.contains("marked")),
    };
  }, request.claim);

  await browser.close();
  return {index, milestone, claimed, searched,
          copy: {before, after, clipboard}};
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
