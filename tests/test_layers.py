# -*- coding: utf-8 -*-
"""The cost order, the guards, and the one place a gauntlet is sequenced."""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from z2s import layers, schema                                  # noqa: E402


GAUNTLET = {"unit": ["pytest"], "lint": ["ruff", "check"],
            "e2e": ["playwright", "test"], "integration": ["pytest", "-m", "db"]}


class TestTheOrderIsPublishedNotConfigured(unittest.TestCase):

    def test_every_layer_the_method_knows_has_a_place_in_it(self):
        self.assertEqual(sorted(layers.COST), sorted(layers.KNOWN),
                         "a layer with no cost would sort last by accident "
                         "rather than by anybody's decision")

    def test_the_vocabulary_is_read_from_the_schema_not_written_again(self):
        self.assertEqual(list(layers.KNOWN),
                         [one["id"] for one in schema.ENUMS["testLayers"]])

    def test_the_cheapest_layers_are_the_ones_that_need_nothing(self):
        free = [one for one in layers.COST if one not in layers.INFRASTRUCTURE]
        self.assertEqual(free, list(layers.COST[:len(free)]),
                         "a check that needs no database, browser or person is "
                         "cheaper than every check that needs one")

    def test_a_person_is_the_most_expensive_thing_there_is(self):
        self.assertEqual(layers.COST[-1], "manual")

    def test_the_order_is_the_same_however_the_project_wrote_it_down(self):
        self.assertEqual(layers.order(["e2e", "lint", "unit"]),
                         layers.order(["unit", "e2e", "lint"]))
        self.assertEqual(layers.order(["e2e", "lint", "unit"]),
                         ["lint", "unit", "e2e"])

    def test_a_layer_named_twice_is_run_once(self):
        self.assertEqual(layers.order(["unit", "unit"]), ["unit"])

    def test_nothing_configures_it(self):
        """NFR-EXE-12: a configured order is a configured way of getting it
        wrong, and `run` reads the order from nowhere but this module."""
        self.assertNotIn("order", GAUNTLET)
        seen = []
        layers.run(GAUNTLET, list(GAUNTLET),
                   lambda layer, command: seen.append(layer) or 0)
        self.assertEqual(seen, layers.order(GAUNTLET))


class TestTheGuardsAUnitNeverHeardOf(unittest.TestCase):

    def test_a_guard_is_stated_by_the_project_and_not_by_the_unit(self):
        self.assertEqual(layers.guards(GAUNTLET, ["unit"]), ["lint"])

    def test_a_layer_the_unit_names_is_its_own_and_not_a_guard(self):
        self.assertEqual(layers.guards(GAUNTLET, ["unit", "lint"]), [])

    def test_every_cheap_layer_is_preflighted_whoever_named_it(self):
        """`guards` is the naming half, for the brief; `cheap` is what runs."""
        self.assertEqual(layers.cheap(GAUNTLET), ["lint", "unit"])
        for one in layers.INFRASTRUCTURE:
            self.assertNotIn(one, layers.cheap(GAUNTLET))

    def test_a_check_that_needs_a_database_is_never_a_guard(self):
        """A preflight runs at a moment the run chose, against whatever tree is
        there. Nothing that needs infrastructure can promise that."""
        self.assertNotIn("integration", layers.guards(GAUNTLET, []))
        self.assertNotIn("e2e", layers.guards(GAUNTLET, []))

    def test_the_brief_names_them_with_the_command(self):
        said = layers.lines(GAUNTLET, ["unit"])
        self.assertIn(layers.PREAMBLE, said)
        self.assertTrue([one for one in said if "ruff check" in one],
                        "a worker told a guard exists and not what it runs "
                        "cannot check it before it finishes")

    def test_a_project_with_no_guards_says_nothing(self):
        self.assertEqual(layers.lines({"unit": ["pytest"]}, ["unit"]), [])


class TestRunningThem(unittest.TestCase):

    def runner(self, codes):
        seen = []

        def run(layer, command):
            seen.append(layer)
            held = codes.get(layer, 0)
            return held.pop(0) if isinstance(held, list) else held
        return run, seen

    def test_a_passing_gauntlet_returns_nothing(self):
        run, seen = self.runner({})
        self.assertEqual(layers.run(GAUNTLET, list(GAUNTLET), run), ("", ""))
        self.assertEqual(seen, layers.order(GAUNTLET))

    def test_the_cheapest_red_is_reached_before_the_expensive_green(self):
        """F2: a red layer used to cost 25.4 minutes to reach a verdict of no."""
        run, seen = self.runner({"lint": 1})
        layer, why = layers.run(GAUNTLET, list(GAUNTLET), run)
        self.assertEqual(layer, "lint")
        self.assertIn("ruff check exited 1", why)
        self.assertEqual(seen, ["lint", "lint"],
                         "nothing more expensive than the failure ran at all")

    def test_a_red_layer_is_run_once_more_before_it_costs_anything(self):
        run, seen = self.runner({"lint": [1, 0]})
        disagreed = []
        self.assertEqual(layers.run(GAUNTLET, list(GAUNTLET), run, disagreed),
                         ("", ""))
        self.assertEqual(seen.count("lint"), 2)
        self.assertEqual(len(disagreed), 1)
        self.assertIn("not deterministic", disagreed[0])

    def test_one_re_run_and_no_more(self):
        run, seen = self.runner({"lint": [1, 1, 0]})
        layer, _ = layers.run(GAUNTLET, list(GAUNTLET), run)
        self.assertEqual(layer, "lint")
        self.assertEqual(seen.count("lint"), 2,
                         "a layer that needs three goes is broken in a way a "
                         "third go would hide")

    def test_a_layer_the_project_states_no_command_for_is_skipped(self):
        run, seen = self.runner({})
        layers.run(GAUNTLET, ["unit", "perf"], run)
        self.assertEqual(seen, ["unit"])

    def test_whatever_the_runner_raises_belongs_to_the_caller(self):
        def run(layer, command):
            raise ValueError("refused")
        with self.assertRaises(ValueError):
            layers.run(GAUNTLET, ["unit"], run)


class TestThisStaysALeaf(unittest.TestCase):

    def test_it_imports_nothing_from_the_package_but_the_vocabulary(self):
        """`status` wants KNOWN from here; importing it back would cycle."""
        with open(os.path.join(os.path.dirname(HERE), "z2s", "layers.py"),
                  encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn("from z2s import schema", body)
        for name in ("status", "execute", "dispatch", "gauntlet", "safety"):
            self.assertNotIn("import %s" % name, body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
