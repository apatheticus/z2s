# -*- coding: utf-8 -*-
"""Deliberate exclusions, recorded rather than merely absent (M12-P3-T2).

The two criteria — an exclusion carries its reason, and an exclusion is outside
the coverage universe — were built with the functional-specification generator
in M4 and the coverage engine in M7, and are tested where they were built
(`test_fsd.py`, `test_trace.py`). What M12 adds is the refactor those tasks left
open: an exclusion has to READ as a decision, not as an entry somebody has not
got round to yet.

So this file tests the seam between the three: an exclusion authored through the
real generator, counted by the real coverage engine, and rendered by the real
runtime — and asserts the rendered form says what it is.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from z2s import fsd, gate, paths, schema, trace                        # noqa: E402
from test_fsd import excluded_requirement                              # noqa: E402
from test_plan import build_chain, closed                              # noqa: E402
from test_stories import covering_fsd                                  # noqa: E402

RENDER_HARNESS = os.path.join(HERE, "render_harness.js")
NODE = shutil.which("node")


def rendered(request):
    finished = subprocess.run([NODE, RENDER_HARNESS], input=json.dumps(request),
                              capture_output=True, text=True)
    if finished.returncode != 0:
        raise AssertionError("runtime harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout)


class Excluded(unittest.TestCase):
    """One real document carrying one real exclusion beside live scope."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-excl-")
        build_chain(self.root)
        brief = covering_fsd()
        brief["requirements"].append(excluded_requirement())
        self.path, self.spec = fsd.author(
            self.root, brief,
            closed(gate.Gate(fsd.SLUG, fsd.forks(brief), source=brief)))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def entry(self, identifier):
        for section in self.spec["sections"]:
            for one in section.get("items") or ():
                if isinstance(one, dict) and one.get("id") == identifier:
                    return one
        raise AssertionError("%s is not in the document" % identifier)

    def excluded_id(self):
        _, excluded = fsd.universe(self.spec)
        self.assertEqual(1, len(excluded))
        return list(excluded)[0]


class TestAnExclusionIsRecordedNotOmitted(Excluded):

    def test_the_exclusion_is_still_an_entry_in_the_catalogue(self):
        """FR-GEN-09: absent scope and refused scope are different facts."""
        self.assertEqual(fsd.EXCLUDED, self.entry(self.excluded_id())["priority"])

    def test_the_exclusion_carries_its_reason_where_the_engine_reads_it(self):
        """M12-P3-T2-C1, at the seam: the generator writes what trace reads."""
        entry = self.entry(self.excluded_id())
        self.assertTrue(entry.get(trace.REASON))

    def test_the_coverage_engine_asks_no_unit_of_work_to_claim_it(self):
        """M12-P3-T2-C2, through the engine rather than the generator."""
        specs = {"FSD.html": self.spec}
        item = trace.universe(specs)[self.excluded_id()]
        self.assertEqual("excluded", item.state)
        self.assertTrue(item.reason)
        self.assertEqual([], [one for one in trace.check(specs)
                              if one.where == self.excluded_id()])

    def test_an_exclusion_that_loses_its_reason_fails_the_gate(self):
        """The rule bites: it is the reason, not the band, that makes it a decision."""
        entry = self.entry(self.excluded_id())
        del entry[trace.REASON]
        found = [one for one in trace.check({"FSD.html": self.spec})
                 if one.code == "excluded-without-reason"]
        self.assertEqual(1, len(found))


@unittest.skipIf(NODE is None, "node is not installed")
class TestAnExclusionReadsAsADecision(Excluded):

    def markup(self):
        return "".join(rendered({"op": "document",
                                 "spec": self.spec})["sections"])

    def test_the_rendered_exclusion_is_marked_apart_from_live_scope(self):
        self.assertIn('id="%s" data-priority="%s" data-excluded="true"'
                      % (self.excluded_id(),
                         fsd.EXCLUDED.replace("'", "&#39;")), self.markup())

    def test_live_scope_is_not_marked_as_excluded(self):
        markup = self.markup()
        self.assertIn('id="FR-DOC-01"', markup)
        self.assertNotIn('id="FR-DOC-01" data-priority="Must" data-excluded',
                         markup)

    def test_the_reason_is_labelled_as_the_argument_for_not_building_it(self):
        markup = self.markup()
        self.assertIn("excluded-reason", markup)
        self.assertIn("Not building this, because:", markup)

    def test_a_live_entrys_note_is_not_labelled_that_way(self):
        self.assertNotIn('class="excluded-reason">%s'
                         % self.entry("FR-DOC-01").get("notes", "?"),
                         self.markup())

    def test_the_exclusion_band_is_still_one_the_toolbar_offers(self):
        """Marked distinctly is not the same as taken out of the filter."""
        answer = rendered({"op": "catalogue", "spec": self.spec})
        self.assertIn(fsd.EXCLUDED, answer["bands"])

    def test_a_keyword_in_the_reason_still_finds_the_exclusion(self):
        entry = self.entry(self.excluded_id())
        answer = rendered({"op": "catalogue", "item": entry})
        self.assertIn(entry[trace.REASON].split()[0].lower(),
                      answer["searchable"])


class TestTheRuleIsStatedOnceOnEachSide(unittest.TestCase):
    """`Won't` is spelled in Python and in JavaScript, and only there."""

    def sources(self):
        package = os.path.join(os.path.dirname(HERE), "z2s")
        for name in sorted(os.listdir(package)):
            if name.endswith((".py", ".js")):
                with open(os.path.join(package, name), encoding="utf-8") as fh:
                    yield name, fh.read()

    def test_no_module_hides_the_band_inside_a_condition(self):
        allowed = {"fsd.py", "trace.py", "runtime.js", "schema.py"}
        offenders = [name for name, text in self.sources()
                     if "Won't" in text and name not in allowed]
        self.assertEqual([], offenders,
                         "the exclusion band is a named constant, not a literal "
                         "sprinkled through the toolchain")


class TestThePublishedRendererReadsTheSameBand(unittest.TestCase):
    """The scanner above covers `z2s/` and stops there.

    `docs/_build/shell.py` is a second, complete renderer of the same document
    format, and it carried the four priority names as a bare literal in its
    filter legend. Renaming the band in `z2s/trace.py` would have passed every
    test in this repository and left the published site filtering on a word the
    method no longer used. Legitimate interface, unguarded — so this is the
    guard, not a rewrite.
    """

    def rendered(self):
        path = os.path.join(os.path.dirname(HERE), "docs", "_build", "shell.py")
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def test_the_band_is_named_once_and_only_in_the_constant(self):
        body = self.rendered()
        self.assertEqual(body.count(trace.EXCLUDED), 1,
                         "the exclusion band is a named constant in the "
                         "published renderer too, not a literal in a legend")
        self.assertIn('var BANDS = ', body)

    def test_the_published_band_is_the_method_s_band(self):
        """Rename it in the toolchain and this fails, which is the whole point."""
        held = re.search(r"var BANDS = \[(.*?)\];", self.rendered())
        self.assertIsNotNone(held, "the published renderer states no band")
        named = [one.strip().strip('"') for one in held.group(1).split(",")]
        self.assertEqual(named, [one["id"] for one in schema.ENUMS["priorities"]],
                         "the published filter and the method's vocabulary have "
                         "come apart")
        self.assertIn(trace.EXCLUDED, named)


if __name__ == "__main__":
    unittest.main(verbosity=2)
