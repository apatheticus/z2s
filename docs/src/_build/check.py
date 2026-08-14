# -*- coding: utf-8 -*-
"""Validate the RENDERED documents (run after generate.py).

Per ADR-09 this reads the produced files and extracts each document's embedded
specification from the rendered output — it never imports the generator's data.
Validating the input proves the input was sound; only this proves the deliverable is.

    python3 check.py        # exits non-zero, listing every failure, if any fail
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, ".."))

DOCS = ["index.html", "Z2S-Brief.html", "Z2S-Playbook.html", "Z2S-Vision.html", "Z2S-Context.html",
        "Z2S-PRD.html", "Z2S-FSD.html", "Z2S-User-Stories.html", "Z2S-SDD.html",
        "Z2S-Plan.html"]

ID_RE = re.compile(r"^(FR|NFR|ADR|US|UC|VC|VS|SH|BC|UL|G|NG|MT|J|RK|R|PRE|M)[A-Z0-9-]*$")
SECRETISH = re.compile(r"(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{12,}"
                       r"|-----BEGIN [A-Z ]*PRIVATE KEY-----)")

FAILS, WARNS, SKIPS = [], [], []


def fail(m):
    FAILS.append(m)


def warn(m):
    WARNS.append(m)


def extract(path):
    """The one shared extraction routine — a missing or unparseable block is a named failure."""
    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    m = re.search(r'<script type="application/json" id="([a-z-]+-spec|index-spec)">(.*?)</script>', html, re.S)
    if not m:
        return html, None, "no embedded specification block found"
    try:
        return html, json.loads(m.group(2)), None
    except Exception as e:                                        # noqa: BLE001
        return html, None, "embedded specification failed to parse: %s" % e


def walk_ids(spec):
    """Every identifier the document defines, and every identifier it references."""
    defined, referenced = set(), set()

    def visit(node):
        if isinstance(node, dict):
            if isinstance(node.get("id"), str) and ID_RE.match(node["id"]):
                defined.add(node["id"])
            tr = node.get("traces")
            if isinstance(tr, dict):
                for v in tr.values():
                    if isinstance(v, list):
                        referenced.update(x for x in v if isinstance(x, str))
            for v in node.values():
                visit(v)
        elif isinstance(node, list):
            for v in node:
                visit(v)

    visit(spec)
    return defined, referenced


def check_document(path):
    name = os.path.basename(path)
    if not os.path.exists(path):
        fail("%s: missing" % name)
        return None
    html, spec, err = extract(path)
    if err:
        fail("%s: %s" % (name, err))
        return None

    doc = spec.get("document", {})
    for f in ("title", "slug", "type", "version", "status", "date", "owner"):
        if not doc.get(f):
            fail("%s: document envelope missing '%s'" % (name, f))
    if not spec.get("schemaVersion"):
        fail("%s: no schemaVersion" % name)

    sections = spec.get("sections") or []
    if not sections:
        fail("%s: no sections" % name)
    seen = set()
    for s in sections:
        for f in ("id", "type", "title"):
            if not s.get(f):
                fail("%s: a section is missing '%s'" % (name, f))
        if s.get("id") in seen:
            fail("%s: duplicate section id '%s'" % (name, s.get("id")))
        seen.add(s.get("id"))
    if sections and sections[-1].get("type") != "machine":
        warn("%s: final section is not the machine-readable block" % name)

    # the file must be self-contained: no external script/style/image
    for pat, what in ((r'<script[^>]+src=', "external script"),
                      (r'<link[^>]+rel="stylesheet"[^>]*href="(?!https://fonts\.)', "external stylesheet"),
                      (r'<img[^>]+src="http', "remote image")):
        if re.search(pat, html):
            fail("%s: contains an %s — the document must be self-contained" % (name, what))

    if SECRETISH.search(html):
        fail("%s: contains a credential-shaped literal" % name)

    if len(html) > 250 * 1024:
        warn("%s: %.0f KB exceeds the 250 KB target (SDD targets)" % (name, len(html) / 1024.0))

    defined, referenced = walk_ids(spec)
    return {"name": name, "spec": spec, "defined": defined, "referenced": referenced, "bytes": len(html)}


def check_plan(info):
    """Plan-specific structural invariants — the assertions that make status trustworthy."""
    spec = info["spec"]
    ms_section = next((s for s in spec["sections"] if s.get("type") == "milestones"), None)
    if not ms_section:
        fail("Z2S-Plan.html: no milestones section")
        return
    statuses = set(spec.get("legend", {}).get("statuses", []) and
                   [s["id"] for s in spec["legend"]["statuses"]])
    ntask = ncrit = nauto = 0
    for m in ms_section.get("items", []):
        if not m.get("exit"):
            fail("Z2S-Plan.html: milestone %s has no exit criteria" % m.get("id"))
        if not m.get("phases"):
            fail("Z2S-Plan.html: milestone %s has no phases" % m.get("id"))
        for ph in m.get("phases", []):
            if not ph.get("completion"):
                warn("Z2S-Plan.html: phase %s has no exit criteria" % ph.get("id"))
            for t in ph.get("tasks", []):
                ntask += 1
                tid = t.get("id", "?")
                if not tid.startswith(ph.get("id", "")):
                    fail("Z2S-Plan.html: task %s does not nest under phase %s" % (tid, ph.get("id")))
                if t.get("status") not in statuses:
                    fail("Z2S-Plan.html: task %s has invalid status %r" % (tid, t.get("status")))
                if not t.get("autonomy"):
                    fail("Z2S-Plan.html: task %s has no autonomy class" % tid)
                if not t.get("testLayers"):
                    fail("Z2S-Plan.html: task %s names no verification layer" % tid)
                tdd = t.get("tdd") or {}
                for k in ("red", "green", "refactor"):
                    if not tdd.get(k):
                        fail("Z2S-Plan.html: task %s has no '%s' step" % (tid, k))
                crits = t.get("criteria") or []
                if not crits:
                    fail("Z2S-Plan.html: task %s has no acceptance criteria" % tid)
                if not any(c.get("kind") == "auto" for c in crits):
                    fail("Z2S-Plan.html: task %s has no machine-checkable criterion" % tid)
                for c in crits:
                    ncrit += 1
                    if c.get("kind") == "auto":
                        nauto += 1
                    if "done" not in c or not c.get("id", "").startswith(tid):
                        fail("Z2S-Plan.html: criterion %r malformed on %s" % (c.get("id"), tid))

    cov = next((s for s in spec["sections"] if s.get("id") == "coverage"), None)
    if not cov:
        fail("Z2S-Plan.html: no coverage matrix")
    else:
        unclaimed = [r[0] for r in cov["rows"] if r[3].strip() == "**none**"]
        if unclaimed:
            fail("Z2S-Plan.html: coverage matrix has unclaimed rows: %s" % ", ".join(unclaimed))

    waves = spec.get("waves") or []
    seen = set()
    deps = {m["id"]: set(m.get("dependsOn", [])) for m in ms_section["items"]}
    for i, w in enumerate(waves):
        for mid in w:
            if not deps.get(mid, set()) <= seen:
                fail("Z2S-Plan.html: %s in wave %d depends on a later wave" % (mid, i + 1))
        seen |= set(w)
    if seen != set(deps):
        fail("Z2S-Plan.html: wave ordering does not cover every milestone")

    print("  plan: %d tasks · %d criteria (%d machine-checkable) · %d waves"
          % (ntask, ncrit, nauto, len(waves)))


def check_determinism():
    """Generating twice from unchanged inputs must produce byte-identical files."""
    before = {}
    for d in DOCS:
        p = os.path.join(OUT, d)
        if os.path.exists(p):
            before[d] = open(p, "rb").read()
    r = subprocess.run([sys.executable, os.path.join(HERE, "generate.py")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail("regeneration failed: %s" % (r.stderr.strip().splitlines() or ["?"])[-1])
        return
    changed = [d for d in before if open(os.path.join(OUT, d), "rb").read() != before[d]]
    if changed:
        fail("generation is not deterministic — changed on regeneration: %s" % ", ".join(changed))
    else:
        print("  determinism: regeneration produced byte-identical output")


def main():
    print("Validating rendered documents in", OUT)
    infos = [check_document(os.path.join(OUT, d)) for d in DOCS]
    infos = [i for i in infos if i]

    all_defined = set()
    for i in infos:
        all_defined |= i["defined"]
    for i in infos:
        dangling = sorted(r for r in i["referenced"] if r not in all_defined)
        if dangling:
            fail("%s: traces reference identifiers defined nowhere in the set: %s"
                 % (i["name"], ", ".join(dangling)))

    plan = next((i for i in infos if i["name"] == "Z2S-Plan.html"), None)
    if plan:
        check_plan(plan)

    print("  documents: %d · total %.0f KB" % (len(infos), sum(i["bytes"] for i in infos) / 1024.0))
    check_determinism()

    SKIPS.append("rendered-view check: run separately with a browser; not attempted here")
    for s in SKIPS:
        print("  SKIPPED —", s)
    for w in WARNS:
        print("  WARN —", w)
    if FAILS:
        print("\nVALIDATION FAILED (%d):" % len(FAILS))
        for f in FAILS:
            print("   X", f)
        return 1
    print("\nOK: every rendered document parses and satisfies its structural invariants.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
