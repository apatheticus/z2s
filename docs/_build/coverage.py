# -*- coding: utf-8 -*-
"""Coverage engine — the gate that makes 'nothing was dropped' a fact.

universe  = every FSD requirement that is not an explicit exclusion
          + every SDD requirement + every SDD decision
claimed   = every identifier appearing in any milestone or task trace
uncovered = universe - claimed        -> non-empty means generation fails
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from specs import fsd, sdd, stories, plan_spine          # noqa: E402
from specs import plan_m01_m04, plan_m05_m08, plan_m09_m12  # noqa: E402
from specs import plan_m13_m14, plan_m15, plan_m16, plan_m17, plan_m18  # noqa: E402

DETAIL = {}
for mod in (plan_m01_m04, plan_m05_m08, plan_m09_m12, plan_m13_m14, plan_m15,
            plan_m16, plan_m17, plan_m18):
    DETAIL.update(mod.DETAIL)


def universe():
    """Identifiers that must be claimed by some unit of work."""
    u, excluded = {}, {}
    for r in fsd.REQUIREMENTS:
        if r["priority"] == "Won't":
            excluded[r["id"]] = r["title"]
        else:
            u[r["id"]] = ("fr", r["title"])
    for r in sdd.REQUIREMENTS:
        u[r["id"]] = ("nfr", r["title"])
    for d in sdd.DECISIONS:
        u[d["id"]] = ("adr", d["title"])
    return u, excluded


def claims():
    """id -> sorted list of unit identifiers that claim it."""
    out = {}

    def add(ids, unit):
        for i in ids or []:
            out.setdefault(i, [])
            if unit not in out[i]:
                out[i].append(unit)

    for m in plan_spine.MILESTONES:
        for k, v in (m.get("traces") or {}).items():
            add(v, m["id"])
        for ph in DETAIL.get(m["id"], []):
            for k, v in (ph.get("traces") or {}).items():
                add(v, ph["id"])
            for t in ph.get("tasks", []):
                for k, v in (t.get("traces") or {}).items():
                    add(v, t["id"])
    return out


def story_matrix():
    """FSD requirement id -> stories covering it (derived, never stored)."""
    out = {}
    for s in stories.STORIES:
        for i in (s.get("traces") or {}).get("fr", []):
            out.setdefault(i, []).append(s["id"])
    for u in stories.USE_CASES:
        for i in (u.get("traces") or {}).get("fr", []):
            out.setdefault(i, []).append(u["id"])
    return out


def report():
    u, excluded = universe()
    c = claims()
    uncovered = sorted(i for i in u if i not in c)
    # A trace to an explicitly excluded requirement is legitimate — a task may exist
    # solely to record the exclusion. Only an identifier defined nowhere is dangling.
    dangling = sorted(i for i in c
                      if i not in u and i not in excluded and not i.startswith(("US-", "UC-")))
    sm = story_matrix()
    unstoried = sorted(r["id"] for r in fsd.REQUIREMENTS
                       if r["priority"] != "Won't" and r["id"] not in sm)

    print("universe: %d  (fsd %d · nfr %d · adr %d)  excluded: %d" % (
        len(u),
        len([1 for v in u.values() if v[0] == "fr"]),
        len([1 for v in u.values() if v[0] == "nfr"]),
        len([1 for v in u.values() if v[0] == "adr"]),
        len(excluded)))
    ntasks = sum(len(ph.get("tasks", [])) for ms in DETAIL.values() for ph in ms)
    nphases = sum(len(ms) for ms in DETAIL.values())
    ncrit = sum(len(t.get("criteria", [])) for ms in DETAIL.values() for ph in ms
                for t in ph.get("tasks", []))
    print("plan: %d milestones · %d phases · %d tasks · %d criteria" % (
        len(plan_spine.MILESTONES), nphases, ntasks, ncrit))
    print("stories: %d · use cases: %d" % (len(stories.STORIES), len(stories.USE_CASES)))

    ok = True
    if uncovered:
        ok = False
        print("\nUNCOVERED (%d):" % len(uncovered))
        for i in uncovered:
            print("   X %-14s %s" % (i, u[i][1]))
    if dangling:
        ok = False
        print("\nDANGLING TRACES (%d):" % len(dangling))
        for i in dangling:
            print("   X %-14s claimed by %s" % (i, ", ".join(c[i])))
    if unstoried:
        print("\nWARN — functional requirements with no story or use case (%d):" % len(unstoried))
        print("   " + ", ".join(unstoried))
    if ok:
        print("\nOK: every requirement and decision is claimed by at least one unit of work.")
    return ok


if __name__ == "__main__":
    sys.exit(0 if report() else 1)
