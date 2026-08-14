/* Test harness only. Loads the document runtime the way a browser would not —
   as a module — so the pure part of it can be exercised without a browser.

   Reads one JSON request on stdin, writes one JSON response on stdout:

     {"op": "document",  "spec": {...}}   -> {hero, contents, sections}
     {"op": "outline",   "spec": {...}}   -> [{id, title, number}, ...]
     {"op": "rich",      "value": "..."}  -> string
     {"op": "esc",       "value": "..."}  -> string
     {"op": "types"}                      -> ["cards", "code", ...]

   The DOM half of the runtime (mount, scroll tracking) is not reachable here
   and is covered by the browser pass. */

"use strict";

const path = require("path");
const Z2S = require(path.join(__dirname, "..", "z2s", "runtime.js"));

const OPS = {
  document: (req) => Z2S.renderDocument(req.spec),
  outline: (req) => Z2S.outline(req.spec),
  rich: (req) => Z2S.rich(req.value),
  esc: (req) => Z2S.esc(req.value),
  types: () => Object.keys(Z2S.renderers).sort(),
  version: () => Z2S.schemaVersion,

  /* The parts of the catalogue that need no browser: what a keyword is matched
     against, which bands a document has, and what the toolbar offers. */
  catalogue: (req) => ({
    searchable: Z2S.catalogue.searchable(req.item || {}),
    items: Z2S.catalogue.items(req.spec || {}).map((item) => item.id),
    bands: Z2S.catalogue.bandsOf(Z2S.catalogue.items(req.spec || {})),
    toolbar: Z2S.catalogue.toolbar(req.spec || {}),
    reviewable: Z2S.review.reviewable(req.spec || {}),
    shows: (req.cases || []).map((one) =>
      Z2S.catalogue.shows(one.entry, one.keyword || "", one.off || {})),
  }),

  compatible: (req) => Z2S.compatible(req.document, req.runtime),

  /* One mark-and-reload cycle against a store held in memory, so the storage
     rules can be exercised without a browser. The browser pass covers the part
     only a browser has: two documents open in one profile. */
  review: (req) => {
    const memory = Object.assign({}, req.stored || {});
    const store = {
      getItem: (key) => (key in memory ? memory[key] : null),
      setItem: (key, value) => { memory[key] = String(value); },
    };
    const key = Z2S.review.namespace(req.spec);
    const before = Z2S.review.read(store, key);
    const marks = Object.assign({}, before, req.mark || {});
    const written = Z2S.review.write(store, key, marks);
    const after = Z2S.review.read(store, key);
    return {
      key, before, after, written, stored: memory,
      spec: req.spec,
      reviewable: Z2S.review.reviewable(req.spec),
      progress: Z2S.review.progress(Z2S.review.reviewable(req.spec), after),
    };
  },

  /* The wiring itself, against a host and a store standing in for the browser's.
     The browser pass proves it works in a browser; this proves what it must not
     do — touch the specification object it was handed. */
  apply: (req) => {
    const memory = Object.assign({}, req.stored || {});
    const store = {
      getItem: (key) => (key in memory ? memory[key] : null),
      setItem: (key, value) => { memory[key] = String(value); },
    };
    const boxes = Z2S.review.reviewable(req.spec).map((id) => ({
      id,
      checked: false,
      listeners: [],
      getAttribute: () => id,
      addEventListener(name, handler) { this.listeners.push(handler); },
    }));
    const counter = {textContent: ""};
    const host = {
      querySelector: (selector) => (selector === "[data-progress]" ? counter : null),
      querySelectorAll: () => boxes,
    };

    Z2S.review.apply(req.spec, host, store);
    if (req.tick && boxes.length) {
      boxes[0].checked = true;
      boxes[0].listeners.forEach((handler) => handler());
    }

    return {
      spec: req.spec,
      stored: memory,
      progress: counter.textContent,
      restored: boxes.filter((box) => box.checked).map((box) => box.id),
    };
  },
};

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  const request = JSON.parse(input);
  const op = OPS[request.op];
  if (!op) {
    process.stderr.write("unknown op: " + request.op + "\n");
    process.exit(2);
  }
  process.stdout.write(JSON.stringify(op(request)));
});
