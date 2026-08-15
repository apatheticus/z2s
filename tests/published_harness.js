/* Test harness only. Drives the PUBLISHED plan — the index and one milestone
   page — in a real browser and reports what the browser actually did.

   These are the questions no amount of reading the generator's data can answer.
   Whether the first phase and the first task really arrive open. Whether
   opening one closes its siblings. Whether the copy button on a shut fold can
   be clicked at all, and whether the clipboard afterwards holds the prompt.
   Whether a deep link to a task buried two levels down lands on something the
   reader can see. Whether paper gets the content the screen folds away.

   Reads one JSON request on stdin, writes one JSON response on stdout:

     {"op": "plan", "dir": "/abs/docs", "index": "Z2S-Plan.html",
      "milestone": "Z2S-Plan-M11.html", "task": "M11-P2-T5"}

   Pages are served from one intercepted https origin rather than opened from
   the filesystem: the clipboard API exists only in a secure context, and a
   check that cannot reach the clipboard cannot prove the copy button works.

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

/* Read straight out of the page, so every answer is what the browser computed
   rather than what the markup said. */
const OPEN = `(function(){
  var ids = function(sel){ return Array.prototype.map.call(
    document.querySelectorAll(sel), function(e){ return e.id; }); };
  return {
    milestones: ids(".ms.open"),
    phases: ids(".ph.open"),
    tasks: ids(".task.open"),
    allPhases: ids(".ph"),
    allTasks: ids(".task")
  };
})()`;

async function open(context, name, width) {
  const page = await context.newPage();
  if (width) await page.setViewportSize({width: width, height: 900});
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.goto(HOST + name, {waitUntil: "load"});
  await page.waitForTimeout(250);
  return {page, errors};
}

async function plan(request) {
  const {chromium} = loadPlaywright();
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: {width: 1280, height: 900},
    permissions: ["clipboard-read", "clipboard-write"]
  });
  await context.route(HOST + "**", (route) => {
    const name = decodeURIComponent(new URL(route.request().url()).pathname.slice(1));
    const file = path.join(request.dir, name);
    if (!fs.existsSync(file)) return route.fulfill({status: 404, body: "not here"});
    route.fulfill({status: 200, contentType: "text/html; charset=utf-8",
                   body: fs.readFileSync(file, "utf8")});
  });

  const out = {errors: []};

  /* ---- the milestone page: the accordion, the prompt row, print ---- */
  let {page, errors} = await open(context, request.milestone);
  out.errors = out.errors.concat(errors);

  out.arrival = await page.evaluate(OPEN);
  out.tasksPerPhase = await page.evaluate(`(function(){
    return Array.prototype.map.call(document.querySelectorAll(".ph"), function(p){
      return Array.prototype.filter.call(p.querySelectorAll(".task"), function(t){
        return t.classList.contains("open"); }).map(function(t){ return t.id; });
    });
  })()`);

  /* Opening one closes its siblings — asked of the LAST phase and of a task
     that is not the one already open, so a false pass needs two coincidences. */
  await page.locator(".ph").last().locator("> .phh").click();
  out.afterLastPhase = await page.evaluate(OPEN);
  await page.locator(".ph.open .task").nth(1).locator("> .thd > .hd").click();
  out.afterSecondTask = await page.evaluate(OPEN);
  /* The only open one, clicked again, shuts. */
  await page.locator(".ph.open .task.open > .thd > .hd").click();
  out.afterSameTaskAgain = await page.evaluate(OPEN);

  /* Expand all, then one header click puts the accordion back. */
  await page.click("#expandAll");
  out.afterExpandAll = await page.evaluate(OPEN);
  await page.locator(".ph").first().locator("> .phh").click();
  out.afterHeaderPostExpand = await page.evaluate(OPEN);
  await page.click("#collapseAll");
  out.afterCollapseAll = await page.evaluate(OPEN);

  /* Collapse-all shut the milestone too, and its body is where the folds are. */
  await page.locator(".ms > .mh").click();

  /* The prompt row: what it says, and whether it copies while shut. */
  out.prompt = await page.evaluate(`(function(){
    var fold = document.querySelector("details.pf");
    var button = fold.querySelector(".copy");
    var box = button.getBoundingClientRect();
    return {id: fold.id, label: fold.querySelector(".pft").textContent,
            openOnArrival: fold.open,
            copyInsideSummary: button.closest("summary") !== null,
            copyVisibleWhileShut: box.width > 0 && box.height > 0,
            body: fold.querySelector("pre").textContent};
  })()`);
  /* Whether the click's default action was cancelled, watched from the fold
     itself so the reading happens after the button's own handler has run.
     Chromium happens not to toggle a fold when an interactive descendant of its
     summary is clicked, so "is it still shut" cannot see a missing guard —
     other engines do toggle, and this is the mechanism that stops them. */
  await page.evaluate(`(function(){
    window.__cancelled = null;
    /* On the BUTTON, not on the fold: the copy handler stops the event
       propagating, so a listener further up would never run at all. Registered
       after it, so it sees the decision that handler made. */
    document.querySelector("details.pf .copy").addEventListener("click", function (event) {
      window.__cancelled = event.defaultPrevented;
    });
  })()`);
  await page.click("details.pf .copy");
  await page.waitForTimeout(300);
  out.afterCopy = await page.evaluate(`(async function(){
    var fold = document.querySelector("details.pf");
    var held = "";
    try { held = await navigator.clipboard.readText(); }
    catch (e) { held = "UNREADABLE: " + e.message; }
    return {stillShut: !fold.open, label: fold.querySelector(".copy").textContent,
            cancelled: window.__cancelled, held: held};
  })()`);

  /* The keyword box opens what it matches, and clearing it restores arrival. */
  out.filtered = await page.evaluate(`(function(){
    var box = document.getElementById("filter");
    box.value = ${JSON.stringify(request.keyword)};
    box.dispatchEvent(new Event("input"));
    var open = function(sel){ return Array.prototype.map.call(
      document.querySelectorAll(sel), function(e){ return e.id; }); };
    var out = {tasks: open(".task.open"), phases: open(".ph.open"),
               visible: Array.prototype.filter.call(document.querySelectorAll(".task"),
                 function(t){ return !t.classList.contains("hidden"); })
                 .map(function(t){ return t.id; })};
    box.value = "";
    box.dispatchEvent(new Event("input"));
    out.cleared = open(".task.open");
    return out;
  })()`);

  /* Paper. Everything the accordion folds is expanded; instructions are not. */
  await page.emulateMedia({media: "print"});
  await page.waitForTimeout(150);
  out.printed = await page.evaluate(`(function(){
    var shut = function(sel){ return Array.prototype.filter.call(
      document.querySelectorAll(sel), function(e){
        return getComputedStyle(e).display === "none"; }).length; };
    return {taskBodies: document.querySelectorAll(".task > .tb").length,
            taskBodiesHidden: shut(".task > .tb"),
            phaseBodies: document.querySelectorAll(".ph > .phb").length,
            phaseBodiesHidden: shut(".ph > .phb"),
            prompts: document.querySelectorAll("details.pf").length,
            promptsHidden: shut("details.pf")};
  })()`);
  await page.close();

  /* ---- a deep link into something two levels down ---- */
  ({page, errors} = await open(context, request.milestone + "#" + request.task));
  out.errors = out.errors.concat(errors);
  await page.waitForTimeout(600);
  out.deepLink = await page.evaluate(`(function(){
    var t = document.getElementById(${JSON.stringify(request.task)});
    if (!t) return {found: false};
    var box = t.getBoundingClientRect();
    return {found: true, taskOpen: t.classList.contains("open"),
            phase: t.closest(".ph").id,
            phaseOpen: t.closest(".ph").classList.contains("open"),
            milestoneOpen: t.closest(".ms").classList.contains("open"),
            openPhases: Array.prototype.map.call(document.querySelectorAll(".ph.open"),
              function(p){ return p.id; }),
            onScreen: box.top > -20 && box.top < window.innerHeight};
  })()`);
  await page.close();

  /* ---- a phone-width read of the same page ---- */
  ({page, errors} = await open(context, request.milestone, 360));
  out.errors = out.errors.concat(errors);
  out.narrow = await page.evaluate(
    "document.documentElement.scrollWidth - document.documentElement.clientWidth");
  await page.close();

  /* The index at a phone width too. It is the page that carries the widest
     things — a five-column milestones table and the whole coverage matrix —
     and it is the one that regressed: its section count reads "15 milestones ·
     135 tasks", which is `white-space: nowrap` on a heading row that could not
     wrap, and it pushed the page 51px sideways. */
  ({page, errors} = await open(context, request.index, 360));
  out.errors = out.errors.concat(errors);
  out.narrowIndex = await page.evaluate(
    "document.documentElement.scrollWidth - document.documentElement.clientWidth");
  await page.close();

  /* ---- the index: what it offers, and where it goes ---- */
  ({page, errors} = await open(context, request.index));
  out.errors = out.errors.concat(errors);
  out.index = await page.evaluate(`(function(){
    var chips = document.querySelectorAll("#docnav .docnav");
    return {promptSection: document.querySelector("#prompt h2").textContent,
            promptRows: document.querySelectorAll("details.pf").length,
            firstPromptId: document.querySelector("details.pf").id,
            milestoneRows: document.querySelectorAll("#milestones tbody tr").length,
            railBlocks: chips.length,
            railParts: chips[0].children.length,
            railCurrent: document.querySelector("#docnav .chip.accent").textContent,
            waveHref: document.querySelector(".wave .chip").getAttribute("href"),
            claimHref: document.querySelector("#coverage tbody td:last-child a")
              .getAttribute("href"),
            noWorkHere: document.querySelectorAll(".task").length};
  })()`);
  await page.click("#milestones a[href='" + request.jumpTo + "']");
  await page.waitForLoadState("load");
  await page.waitForTimeout(400);
  out.jumped = await page.evaluate(`(function(){
    return {file: location.pathname.replace(/^\\//, ""),
            title: document.title,
            railCurrent: document.querySelector("#docnav .chip.accent").textContent,
            backToIndex: document.querySelector("#docnav .docnav a").getAttribute("href")};
  })()`);
  await page.close();

  /* ---- an amended requirement, on the document that states it ---- */
  ({page, errors} = await open(context, request.amended.file + "#" + request.amended.id));
  out.errors = out.errors.concat(errors);
  out.amended = await page.evaluate(`(function(){
    var entry = document.getElementById(${JSON.stringify(request.amended.id)});
    var block = entry ? entry.querySelector(".amended") : null;
    return {found: Boolean(entry),
            rendered: Boolean(block),
            heading: block ? block.querySelector("b").textContent : null,
            date: block ? block.querySelector(".when").textContent : null,
            amendments: block ? block.querySelectorAll("li").length : 0,
            /* The original is what every existing trace was written against, so
               it has to still be there, above the amendment, word for word. */
            original: entry ? entry.querySelector(".tx").textContent : ""};
  })()`);
  await page.close();

  await browser.close();
  return out;
}

let input = "";
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  const request = JSON.parse(input);
  plan(request)
    .then((out) => process.stdout.write(JSON.stringify(out)))
    .catch((error) => {
      process.stderr.write(String((error && error.stack) || error) + "\n");
      process.exit(/Executable doesn't exist|browserType.launch/.test(String(error)) ? 3 : 1);
    });
});
