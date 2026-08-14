/* Test harness only. Opens a generated document in a real browser and reports
   what the browser actually computed — focus indicators, contrast ratios,
   motion, overflow at a phone width, and print styling.

   These are the criteria that cannot be checked by reading the stylesheet: a
   contrast ratio depends on which background an element really sits on, and an
   outline is only visible if the browser draws one.

   Reads one JSON request on stdin, writes one JSON response on stdout:

     {"op": "audit", "html": "<!doctype html>..."}  -> {focus, contrast, ...}

   Exits 3 when Playwright or its browsers are not installed, so the Python
   suite can report the check as skipped rather than passed (LD-04, FR-GEN-03).

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

/* WCAG relative luminance and contrast, computed in the page against the
   background the element really sits on rather than the one it declares. */
const PAGE_HELPERS = `
  function channel(v) {
    v = v / 255;
    return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  }
  function luminance(rgb) {
    return 0.2126 * channel(rgb[0]) + 0.7152 * channel(rgb[1]) + 0.0722 * channel(rgb[2]);
  }
  function parse(colour) {
    const parts = colour.match(/[\\d.]+/g) || [];
    return {rgb: parts.slice(0, 3).map(Number),
            alpha: parts.length > 3 ? Number(parts[3]) : 1};
  }
  function backgroundOf(node) {
    for (let el = node; el; el = el.parentElement) {
      const found = parse(getComputedStyle(el).backgroundColor);
      if (found.alpha > 0) return found.rgb;
    }
    return [255, 255, 255];
  }
  function ratio(node) {
    const front = parse(getComputedStyle(node).color).rgb;
    const back = backgroundOf(node);
    const a = luminance(front), b = luminance(back);
    const light = Math.max(a, b), dark = Math.min(a, b);
    return Math.round(((light + 0.05) / (dark + 0.05)) * 100) / 100;
  }
`;

async function audit(request) {
  const {chromium} = loadPlaywright();
  const browser = await chromium.launch();
  const out = {};

  /* --- focus, contrast, status: ordinary reading conditions --------------- */
  let context = await browser.newContext({viewport: {width: 1280, height: 900}});
  let page = await context.newPage();
  await page.setContent(request.html, {waitUntil: "load"});

  out.focus = [];
  for (let i = 0; i < 14; i++) {
    await page.keyboard.press("Tab");
    const stop = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el || el === document.body) return null;
      const style = getComputedStyle(el);
      const box = el.getBoundingClientRect();
      return {
        tag: el.tagName.toLowerCase(),
        label: (el.textContent || "").trim().slice(0, 40),
        outlineStyle: style.outlineStyle,
        outlineWidth: parseFloat(style.outlineWidth) || 0,
        boxShadow: style.boxShadow,
        onScreen: box.width > 0 && box.height > 0,
      };
    });
    if (!stop) break;
    out.focus.push(stop);
  }

  out.contrast = await page.evaluate(new Function(PAGE_HELPERS + `
    const targets = {
      "body text": ".section p",
      "section heading": ".section > h2",
      "section number": ".section > h2 .number",
      "lede": ".section .lede",
      "hero title": ".hero h1",
      "hero kicker": ".hero .kicker",
      "hero summary": ".hero .lead",
      "meta label": ".hero .meta dt",
      "contents link": ".contents a",
      "contents number": ".contents a .number",
      "table heading": "th",
      "table cell": "td",
      "definition body": ".section dd",
      "placeholder": ".placeholder",
      "link": ".section p a",
      "review label": ".review span",
      "review progress": ".progress"
    };
    const report = {};
    for (const name of Object.keys(targets).sort()) {
      const node = document.querySelector(targets[name]);
      if (node) report[name] = ratio(node);
    }
    return report;
  `));

  out.status = await page.evaluate(() => {
    const node = document.querySelector(".placeholder");
    if (!node) return null;
    const style = getComputedStyle(node);
    return {
      text: (node.textContent || "").trim(),
      role: node.getAttribute("role"),
      borderLeftWidth: parseFloat(style.borderLeftWidth) || 0,
    };
  });

  out.active = await page.evaluate(() => {
    const node = document.querySelector(".contents a");
    node.classList.add("active");
    const style = getComputedStyle(node);
    const plain = getComputedStyle(document.querySelectorAll(".contents a")[1]);
    return {
      weight: style.fontWeight,
      plainWeight: plain.fontWeight,
      decoration: getComputedStyle(node.querySelector(".number")).textDecorationLine,
    };
  });
  await context.close();

  /* --- reduced motion ----------------------------------------------------- */
  context = await browser.newContext({reducedMotion: "reduce"});
  page = await context.newPage();
  await page.setContent(request.html, {waitUntil: "load"});
  out.motion = await page.evaluate(() => {
    let longest = 0, culprit = null;
    for (const el of document.querySelectorAll("*")) {
      const style = getComputedStyle(el);
      for (const value of (style.transitionDuration + "," + style.animationDuration).split(",")) {
        const seconds = parseFloat(value) || 0;
        if (seconds > longest) { longest = seconds; culprit = el.tagName; }
      }
    }
    return {longestSeconds: longest, culprit: culprit};
  });
  await context.close();

  /* --- a phone-width viewport --------------------------------------------- */
  context = await browser.newContext({viewport: {width: 360, height: 740}});
  page = await context.newPage();
  await page.setContent(request.html, {waitUntil: "load"});
  out.narrow = await page.evaluate(() => {
    const root = document.documentElement;
    /* Content inside a box that scrolls on its own does not widen the page —
       that is the intended treatment for a wide table or a long code line, not
       an overflow. Only content that pushes the page itself counts. */
    const scrolls = (node) => {
      for (let el = node.parentElement; el; el = el.parentElement) {
        if (/(auto|scroll)/.test(getComputedStyle(el).overflowX)) return true;
      }
      return false;
    };
    const wide = [];
    for (const el of document.querySelectorAll("#doc *")) {
      const box = el.getBoundingClientRect();
      if (box.right > root.clientWidth + 1 && !scrolls(el)) {
        wide.push(el.tagName + "." + el.className);
      }
    }
    return {scrollWidth: root.scrollWidth, clientWidth: root.clientWidth,
            overflowing: wide.slice(0, 5)};
  });
  await context.close();

  /* --- print --------------------------------------------------------------- */
  context = await browser.newContext();
  page = await context.newPage();
  await page.setContent(request.html, {waitUntil: "load"});
  /* No section type produces collapsible content yet, so the element the print
     rule exists for is added here. The rule under test is the shipped one. */
  await page.evaluate(() => {
    const box = document.createElement("details");
    box.innerHTML = "<summary>Group</summary><p id='inside'>Collapsed content.</p>";
    document.querySelector("#doc").appendChild(box);
  });
  /* Whether a closed <details> shows its content is not a display question —
     the browser hides it another way, and a hidden child still reports a box —
     so this asks the browser directly whether the reader can see it. */
  const visibility = () => page.evaluate(() => ({
    collapsedContentShown: document.querySelector("#inside").checkVisibility(),
    contentsShown: document.querySelector("nav.contents").checkVisibility(),
  }));
  await page.emulateMedia({media: "print"});
  out.print = await visibility();
  await page.emulateMedia({media: "screen"});
  out.screen = await visibility();
  await context.close();

  await browser.close();
  return out;
}

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", async () => {
  const request = JSON.parse(input);
  if (request.op !== "audit") {
    process.stderr.write("unknown op: " + request.op + "\n");
    process.exit(2);
  }
  try {
    process.stdout.write(JSON.stringify(await audit(request)));
  } catch (error) {
    process.stderr.write(String(error && error.stack || error) + "\n");
    process.exit(/Executable doesn't exist|browserType.launch/.test(String(error)) ? 3 : 1);
  }
});
