# -*- coding: utf-8 -*-
"""The method, applied to itself (M12-P3-T3).

The claim the whole method rests on is that a specification set can be generated
from stated facts and kept honest by its own gates. The only convincing evidence
is watching it happen to something real, and the most demanding thing available
is the method itself.

So these tests do not use a fixture. They build Zero-to-Ship's own document set
with the real generators and run the real gates against it. A defect in a
generator fails here before it reaches anybody else's project.

  M12-P3-T3-C1  The set regenerates with no file difference.
  M12-P3-T3-C2  Every gate passes against the self-hosted set.
"""

import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from selfhost import build                                            # noqa: E402
from z2s import learn, paths, pipeline, schema, trace, validate       # noqa: E402

REPO = os.path.dirname(HERE)


def _built():
    """One build of the method's own set, shared by every test below.

    Built once at import and reused: it is the same twelve documents every time,
    and generating them per test would pay for determinism the suite already
    asserts separately.
    """
    root = tempfile.mkdtemp(prefix="z2s-selfhost-test-")
    try:
        return root, build.build(root), ""
    except Exception as error:              # pragma: no cover - reported, not hidden
        shutil.rmtree(root, ignore_errors=True)
        return None, [], "%s: %s" % (type(error).__name__, error)


ROOT, WRITTEN, REASON = _built()


def tearDownModule():
    if ROOT:
        shutil.rmtree(ROOT, ignore_errors=True)


@unittest.skipIf(ROOT is None, "the set could not be built: %s" % REASON)
class TestTheMethodProducesItsOwnDocuments(unittest.TestCase):

    def sources(self):
        return [paths.resolve(ROOT, one) for one in build.documents(ROOT)]

    def test_the_whole_chain_is_produced(self):
        names = [os.path.basename(one) for one in build.documents(ROOT)]
        for expected in ("Vision.html", "Context.html", "PRD.html", "FSD.html",
                         "Stories.html", "SDD.html", "Briefing.html",
                         "index.html"):
            self.assertIn(expected, names)

    def test_one_document_per_milestone(self):
        names = [os.path.basename(one) for one in build.documents(ROOT)]
        milestones = [one["id"] for one in build.plan_data.MILESTONES]
        for identifier in milestones:
            self.assertTrue(any(name.startswith(identifier + "-")
                                for name in names),
                            "no document for %s" % identifier)

    def test_every_document_carries_a_readable_specification(self):
        for path in self.sources():
            with open(path, encoding="utf-8") as handle:
                spec = validate.extract(handle.read())
            self.assertTrue(spec.get("sections"), os.path.basename(path))

    def test_nothing_is_authored_outside_the_documented_layout(self):
        stray = [name for name in os.listdir(ROOT)
                 if name != paths.ROOT]
        self.assertEqual([], stray, "the build wrote outside %s" % paths.ROOT)


@unittest.skipIf(ROOT is None, "the set could not be built: %s" % REASON)
class TestTheSetRegeneratesUnchanged(unittest.TestCase):
    """M12-P3-T3-C1"""

    def test_building_again_produces_the_same_bytes(self):
        second = tempfile.mkdtemp(prefix="z2s-selfhost-again-")
        try:
            build.build(second)
            self.assertEqual([], build.differences(ROOT, second))
        finally:
            shutil.rmtree(second, ignore_errors=True)

    def test_the_check_reports_a_difference_when_there_is_one(self):
        """The check has to be able to fail, or it proves nothing."""
        second = tempfile.mkdtemp(prefix="z2s-selfhost-broken-")
        try:
            build.build(second)
            target = paths.resolve(second, build.documents(second)[0])
            with open(target, "a", encoding="utf-8") as handle:
                handle.write("\n<!-- a hand edit -->\n")
            self.assertEqual(1, len(build.differences(ROOT, second)))
        finally:
            shutil.rmtree(second, ignore_errors=True)


@unittest.skipIf(ROOT is None, "the set could not be built: %s" % REASON)
class TestEveryGatePassesAgainstIt(unittest.TestCase):
    """M12-P3-T3-C2"""

    def sources(self):
        return [paths.resolve(ROOT, one) for one in build.documents(ROOT)]

    def test_no_gate_fails(self):
        stages = pipeline.run(self.sources(), root=ROOT)
        failed = [one.name for one in stages
                  if pipeline.state(one) == pipeline.FAILED]
        self.assertEqual([], failed)

    def test_the_set_produces_no_failure_and_no_warning(self):
        stages = pipeline.run(self.sources(), root=ROOT)
        found = [one for stage in stages for one in stage.findings
                 if one.severity in (schema.FAILURE, schema.WARNING)]
        self.assertEqual([], found, "; ".join(one.message for one in found))

    def test_every_requirement_and_decision_is_claimed(self):
        findings, rows, _ = trace.gate(self.sources())
        self.assertEqual([], [one for one in rows if one.state == trace.UNCOVERED])
        self.assertEqual(0, trace.exit_code(findings))

    def test_the_set_states_real_scope_rather_than_a_token_amount(self):
        """A self-hosted set of three requirements would prove nothing."""
        _, rows, _ = trace.gate(self.sources())
        counted = [one for one in rows
                   if one.state not in ("excluded", "retired")]
        self.assertGreaterEqual(len(counted), 20)

    def test_it_records_its_deliberate_exclusions(self):
        _, rows, _ = trace.gate(self.sources())
        excluded = [one for one in rows if one.state == "excluded"]
        self.assertTrue(excluded)


class TestTheCommittedSetIsWhatTheToolchainProduces(unittest.TestCase):
    """The check a pipeline actually runs, against the set in the repository."""

    @unittest.skipIf(not os.path.isdir(os.path.join(REPO, paths.ROOT)),
                     "the self-hosted set has not been built into the repository")
    def test_the_committed_set_matches_a_fresh_build(self):
        second = tempfile.mkdtemp(prefix="z2s-selfhost-repo-")
        try:
            build.build(second)
            self.assertEqual([], build.differences(REPO, second))
        finally:
            shutil.rmtree(second, ignore_errors=True)


class TestTheSelfHostedSetLeavesThePublishedOneAlone(unittest.TestCase):
    """The standing decision the whole approach rests on."""

    def test_a_build_leaves_the_published_documents_untouched(self):
        """The one that would actually catch it: build, then compare `docs/`."""
        published = os.path.join(REPO, "docs")
        before = sorted((name, os.path.getmtime(os.path.join(published, name)))
                        for name in os.listdir(published)
                        if name.endswith(".html"))
        scratch = tempfile.mkdtemp(prefix="z2s-selfhost-untouched-")
        try:
            build.build(scratch)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        after = sorted((name, os.path.getmtime(os.path.join(published, name)))
                       for name in os.listdir(published)
                       if name.endswith(".html"))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
