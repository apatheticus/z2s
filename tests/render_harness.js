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
