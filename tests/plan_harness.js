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
    /* A navigated catalogue makes an entry a fold, so its heading is inside a
       <summary> and the prompt is the first thing in the BODY rather than the
       first thing after the heading. Both shapes are asked for: the question is
       where in the card it sits, not which element the card happens to be. */
    promptIsFirst: Boolean(task && task.querySelector("h4 + .prompts, summary + .prompts")),
    copyButtons: document.querySelectorAll(".prompts .copy").length,
    /* Every file this document is written across, and which one the reader is
       holding. A plan is one document in several files (FR-SPC-09). */
    parts: Array.from(document.querySelectorAll(".parts li")).map((li) => ({
      label: li.textContent,
      here: li.className === "here",
      href: li.querySelector("a") ? li.querySelector("a").getAttribute("href") : null,
    })),
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

  /* The accordion, and the plan's own navigation (M15). Read before anything is
     clicked, because "what a reader is given on arrival" is the whole of the
     first half of the rule. */
  const OPEN = () => ({
    areas: Array.from(document.querySelectorAll(".catalogue .area"))
      .map((el) => [el.getAttribute("data-area"), el.open === true]),
    entries: Array.from(document.querySelectorAll(".catalogue .entry"))
      .map((el) => [el.id, el.open === true]),
    tag: (document.querySelector(".catalogue .entry") || {}).tagName || null,
    parts: Array.from(document.querySelectorAll(".parts li")).map((li) => ({
      label: li.textContent,
      here: li.className === "here",
      href: li.querySelector("a") ? li.querySelector("a").getAttribute("href") : null,
    })),
  });
  const arrival = await page.evaluate(OPEN);

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

  /* Opening one closes its siblings at the same level. Asked of a phase and
     then of a task, so a false pass needs the same coincidence twice. */
  await page.click(".catalogue .area:not([open]) > summary");
  await page.waitForTimeout(120);
  const afterArea = await page.evaluate(OPEN);
  await page.click(".catalogue .area[open] .entry:not([open]) > summary");
  await page.waitForTimeout(120);
  const afterEntry = await page.evaluate(OPEN);

  /* Paper. Every fold opens except the instructions, which cannot be copied
     from a printed page. Asked of what the browser computed: the rule that
     expands folds and the rule that drops instructions both apply to the same
     element once an entry is a fold, and only one of them can win. */
  await page.emulateMedia({media: "print"});
  await page.waitForTimeout(120);
  const printed = await page.evaluate(() => {
    const shut = (nodes) => nodes.filter((el) => getComputedStyle(el).display === "none");
    const bodies = Array.from(
      document.querySelectorAll(".catalogue .entry > *:not(summary)"));
    const prompts = Array.from(document.querySelectorAll(".prompts"));
    return {bodies: bodies.length, bodiesHidden: shut(bodies).length,
            prompts: prompts.length, promptsHidden: shut(prompts).length};
  });
  await page.emulateMedia({media: "screen"});
  await page.waitForTimeout(120);

  /* Back to the phase the claim check needs. The accordion has just shut it,
     which is the point of the accordion — so the check that follows a chip has
     to open what it wants to click, exactly as a reader would. */
  await page.click(".catalogue .area:not([open]) > summary");
  await page.waitForTimeout(120);

  /* Follow the task's claim up into the specification that states it. */
  await page.click('#' + request.task + ' a.chip:text-is("' + request.claim + '")');
  await page.waitForTimeout(200);
  const claimed = await page.evaluate((id) => {
    const el = document.getElementById(id);
    const areas = Array.from(document.querySelectorAll(".catalogue .area"));
    return {
      file: location.pathname.replace(/^\//, ""),
      hash: location.hash,
      found: Boolean(el),
      visible: Boolean(el && el.checkVisibility()),
      marked: Boolean(el && el.classList.contains("marked")),
      /* The same runtime, on a document that did not opt in: a specification is
         read rather than navigated, so nothing here folds or closes (M15-06). */
      navigated: Boolean(document.querySelector(".catalogue[data-navigate]")),
      entryTag: (document.querySelector(".catalogue .entry") || {}).tagName || null,
      areas: areas.length,
      areasOpen: areas.filter((one) => one.open).length,
    };
  }, request.claim);

  await browser.close();
  return {index, milestone, claimed, searched, arrival, afterArea, afterEntry,
          printed, copy: {before, after, clipboard}};
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
