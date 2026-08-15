# -*- coding: utf-8 -*-
"""The trace universe and the coverage gate (M7).

Covers criteria:
  M7-P1-T1-C1  A new requirement appears in the index without any other edit.
  M7-P1-T2-C1  An addendum trace resolves to the addendum.
  M7-P1-T2-C2  Addendum identifiers join the coverage universe.
  M7-P1-T3-C1  Generation succeeds with the addendum absent.
  M7-P1-T3-C2  The absence is reported, never silent.
  M7-P2-T1-C1  Every universe identifier appears in the matrix.
  M7-P2-T2-C1  An unclaimed requirement fails generation and is named.
  M7-P2-T2-C2  No configuration downgrades the failure.
  M7-P2-T3-C1  An exclusion without a reason is rejected.
  M7-P2-T3-C2  Exclusions are reported with the matrix.
  M7-P2-T4-C1  A retired identifier remains reserved.
  M7-P2-T4-C2  Reusing a retired number fails validation.

The documents here are built rather than generated: the point of this module is
that it reads whatever a document says, including things this method's own
generators would never write — an addendum from another project, a requirement
somebody added by hand, a plan half-way through a release.

M7-P2-T2-C3 — no plan file is written when the gate fails — is not here. The
plan generator is M8; what this milestone owes is a gate that answers before a
file is written, and `gate()` writes nothing at all.

Traces: FR-AMD-02, FR-AMD-03, FR-TRC-02, FR-TRC-03, FR-TRC-04, FR-TRC-05,
FR-TRC-06, FR-TRC-07, NFR-EVO-03, NFR-VAL-03, NFR-VAL-05, ADR-03, ADR-04.
"""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import schema
from z2s import trace

ENVELOPE = {"title": "Acme", "slug": "fsd", "type": "Functional specification",
            "version": "1.0", "status": "Draft", "date": "2026-08-14",
            "owner": "Acme"}


def spec(slug, sections, links=None):
    """A specification object, as a document embeds one."""
    block = dict(ENVELOPE, slug=slug, title="Acme %s" % slug.upper())
    built = {"document": block, "schemaVersion": "1.0", "sections": sections}
    if links is not None:
        built["links"] = links
    return built


def catalogue(section_id, entries, areas=None):
    """A requirements catalogue section."""
    built = {"id": section_id, "title": "Catalogue", "type": "requirements",
             "items": entries}
    if areas is not None:
        built["areas"] = areas
    return built


def entry(identifier, title="A requirement", **fields):
    built = {"id": identifier, "title": title, "priority": "Must"}
    built.update(fields)
    return built


def unit(identifier, traces=None, **fields):
    """One unit of the plan: what claims a requirement."""
    built = {"id": identifier, "title": "Some work"}
    if traces is not None:
        built["traces"] = traces
    built.update(fields)
    return built


def rendered(body_spec):
    """A document, as the validator will find one."""
    return ('<!doctype html><html><body><script type="application/json">%s'
            '</script></body></html>'
            % json.dumps(body_spec).replace("</", "<\\/"))


FSD = spec("fsd", [catalogue("requirements", [
    entry("FR-DOC-01", "Documents are generated"),
    entry("FR-DOC-02", "Documents carry their own data"),
], areas=[{"key": "FR-DOC", "title": "Documents"}])])

SDD = spec("sdd", [
    catalogue("decisions", [entry("ADR-01", "One embedded object")]),
    catalogue("requirements", [entry("NFR-ARC-01", "One place per rule")],
              areas=[{"key": "NFR-ARC", "title": "Architecture"}]),
    catalogue("targets", [entry("TG-01", "Under 250 KB")]),
])

PLAN = spec("plan", [catalogue("milestones", [
    unit("M1", traces={"fr": ["FR-DOC-01", "FR-DOC-02"], "adr": ["ADR-01"]}),
    unit("M1-P1-T1", traces={"nfr": ["NFR-ARC-01"]}),
])])


class Sandbox(unittest.TestCase):
    """A throwaway folder holding a small set of documents."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-trace-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def written(self, name, body_spec):
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(rendered(body_spec))
        return path


# ------------------------------------------------------- what the set defines

class TestTheIndexIsBuiltFromTheDocuments(unittest.TestCase):
    """M7-P1-T1-C1. No maintained list of requirements exists anywhere."""

    def test_every_identifier_a_document_declares_is_in_the_index(self):
        index = trace.defines({"Z2S-FSD.html": FSD, "Z2S-SDD.html": SDD})
        self.assertEqual(sorted(index),
                         ["ADR-01", "FR-DOC-01", "FR-DOC-02", "NFR-ARC-01", "TG-01"])

    def test_a_new_requirement_needs_no_other_edit(self):
        """The whole of adding a requirement is adding it to the document."""
        before = trace.defines({"Z2S-FSD.html": FSD})
        self.assertNotIn("FR-DOC-03", before)

        grown = spec("fsd", [catalogue("requirements",
                                       FSD["sections"][0]["items"] +
                                       [entry("FR-DOC-03", "A third")],
                                       areas=[{"key": "FR-DOC", "title": "Documents"}])])
        after = trace.defines({"Z2S-FSD.html": grown})
        self.assertIn("FR-DOC-03", after)
        self.assertIn("FR-DOC-03", trace.universe({"Z2S-FSD.html": grown}))

    def test_the_index_says_where_each_identifier_was_found(self):
        index = trace.defines({"Z2S-FSD.html": FSD, "Z2S-SDD.html": SDD})
        self.assertEqual(index["ADR-01"][0].source, "Z2S-SDD.html")
        self.assertEqual(index["FR-DOC-01"][0].entry["title"], "Documents are generated")

    def test_an_area_key_is_not_an_allocation(self):
        """An area carries `key`; only an entry carries `id`."""
        self.assertNotIn("FR-DOC", trace.defines({"Z2S-FSD.html": FSD}))

    def test_nothing_is_cached_between_runs(self):
        """Two calls with different documents give two different answers."""
        self.assertNotEqual(sorted(trace.defines({"a.html": FSD})),
                            sorted(trace.defines({"a.html": SDD})))


# ------------------------------------------------------------------- namespaces

class TestWhoOwnsAnIdentifier(unittest.TestCase):
    """M7-01: the namespace is the area code, not the kind."""

    def test_an_area_code_is_the_namespace_where_there_is_one(self):
        self.assertEqual(trace.namespace("FR-DOC-01"), "FR-DOC")
        self.assertEqual(trace.namespace("US-DOC-01-S01"), "US-DOC")

    def test_a_flat_identifier_is_owned_by_its_kind(self):
        self.assertEqual(trace.namespace("ADR-04"), "ADR")
        self.assertEqual(trace.namespace("TG-01"), "TG")
        self.assertEqual(trace.namespace("UC-02"), "UC")

    def test_routing_is_derived_from_the_documents_not_configured(self):
        routes = trace.links({"Z2S-FSD.html": FSD, "Z2S-SDD.html": SDD})
        self.assertEqual(routes["FR-DOC"], "Z2S-FSD.html")
        self.assertEqual(routes["ADR"], "Z2S-SDD.html")
        self.assertEqual(routes["NFR-ARC"], "Z2S-SDD.html")

    def test_a_plan_identifier_is_not_routed(self):
        """A plan is one document split across files; M1 has no single owner."""
        routes = trace.links({"Z2S-Plan.html": PLAN})
        self.assertEqual(routes, {})

    def test_two_documents_owning_one_namespace_fails_naming_both(self):
        """FR-AMD-02, NFR-EVO-03, LD-02."""
        rival = spec("addendum", [catalogue("requirements",
                                            [entry("FR-DOC-09", "A rival")])])
        _, found = trace.owners({"Z2S-FSD.html": FSD, "Addendum.html": rival})
        self.assertEqual([one.code for one in found], ["prefix-collision"])
        self.assertIn("Z2S-FSD.html", found[0].message)
        self.assertIn("Addendum.html", found[0].message)
        self.assertIn("FR-DOC", found[0].message)
        self.assertEqual(found[0].severity, schema.FAILURE)

    def test_one_collision_is_reported_once_not_once_per_identifier(self):
        rival = spec("addendum", [catalogue("requirements", [
            entry("FR-DOC-09", "A rival"), entry("FR-DOC-10", "Another")])])
        _, found = trace.owners({"Z2S-FSD.html": FSD, "Addendum.html": rival})
        self.assertEqual(len(found), 1)

    def test_an_addendum_with_its_own_area_is_no_collision(self):
        """M7-P1-T2-C1: the whole point of an addendum."""
        addendum = spec("addendum", [catalogue("requirements", [
            entry("FR-NEW-01", "Something later")])])
        routes, found = trace.owners({"Z2S-FSD.html": FSD,
                                      "Addendum.html": addendum})
        self.assertEqual(found, [])
        self.assertEqual(routes["FR-NEW"], "Addendum.html")
        self.assertEqual(routes["FR-DOC"], "Z2S-FSD.html")

    def test_an_addendum_identifier_joins_the_universe(self):
        """M7-P1-T2-C2."""
        addendum = spec("addendum", [catalogue("requirements", [
            entry("FR-NEW-01", "Something later")])])
        counted = trace.universe({"Z2S-FSD.html": FSD, "Addendum.html": addendum})
        self.assertIn("FR-NEW-01", counted)
        self.assertEqual(counted["FR-NEW-01"].source, "Addendum.html")


# ----------------------------------------------------------- reading a set

class TestAnAbsentDocumentIsReportedNotFatal(Sandbox):
    """M7-P1-T3. FR-AMD-03, NFR-VAL-05."""

    def test_the_run_succeeds_and_produces_the_core_answer(self):
        core = self.written("Z2S-FSD.html", FSD)
        missing = os.path.join(self.root, "Addendum.html")
        specs, found = trace.read([core, missing])
        self.assertEqual(list(specs), [core])
        self.assertEqual(sorted(trace.universe(specs)), ["FR-DOC-01", "FR-DOC-02"])

    def test_the_absence_is_reported_never_silent(self):
        core = self.written("Z2S-FSD.html", FSD)
        missing = os.path.join(self.root, "Addendum.html")
        _, found = trace.read([core, missing])
        self.assertEqual([one.code for one in found], ["skipped"])
        self.assertEqual(found[0].severity, schema.WARNING)
        self.assertIn("Addendum.html", found[0].message)

    def test_a_skipped_document_is_never_counted_as_read(self):
        """A summary that cannot tell a partial run from a whole one is a lie."""
        core = self.written("Z2S-FSD.html", FSD)
        missing = os.path.join(self.root, "Addendum.html")
        findings, rows, specs = trace.gate([core, missing])
        report = trace.format_report(findings, rows, specs, [core, missing])
        self.assertIn("1 read, 1 skipped", report)

    def test_a_corrupted_document_is_a_failure_not_an_absence(self):
        broken = os.path.join(self.root, "Z2S-FSD.html")
        with open(broken, "w", encoding="utf-8") as handle:
            handle.write("<html><body>no specification here</body></html>")
        _, found = trace.read([broken])
        self.assertEqual([one.severity for one in found], [schema.FAILURE])
        self.assertEqual(found[0].code, "unreadable")


# ------------------------------------------------------------ what is claimed

class TestTheCoverageMatrix(unittest.TestCase):
    """M7-P2-T1-C1. FR-TRC-04."""

    def setUp(self):
        self.specs = {"Z2S-FSD.html": FSD, "Z2S-SDD.html": SDD,
                      "Z2S-Plan.html": PLAN}

    def test_every_universe_identifier_appears_in_the_matrix(self):
        rows = trace.matrix(self.specs)
        self.assertEqual(sorted(row.id for row in rows),
                         ["ADR-01", "FR-DOC-01", "FR-DOC-02", "NFR-ARC-01"])

    def test_a_target_is_not_in_the_universe(self):
        """M7-02: a target is how you check scope, not scope."""
        self.assertNotIn("TG-01", [row.id for row in trace.matrix(self.specs)])

    def test_the_matrix_names_the_units_that_claim_each_identifier(self):
        rows = dict((row.id, row) for row in trace.matrix(self.specs))
        self.assertEqual(rows["FR-DOC-01"].claimants, ["M1"])
        self.assertEqual(rows["NFR-ARC-01"].claimants, ["M1-P1-T1"])
        self.assertEqual(rows["NFR-ARC-01"].state, "claimed")

    def test_only_a_unit_of_work_counts_as_a_claim(self):
        """A story describes a requirement; only a task schedules it."""
        story = spec("stories", [catalogue("stories", [
            entry("US-DOC-01", "A story", traces={"fr": ["FR-DOC-01"]})])])
        rows = dict((row.id, row) for row in
                    trace.matrix({"Z2S-FSD.html": FSD, "Z2S-Stories.html": story}))
        self.assertEqual(rows["FR-DOC-01"].state, trace.UNCOVERED)

    def test_nothing_computed_here_is_written_into_a_document(self):
        """NFR-DAT-05: coverage is derived, and derived data has no home."""
        before = json.dumps(self.specs, sort_keys=True)
        trace.matrix(self.specs)
        trace.check(self.specs)
        self.assertEqual(json.dumps(self.specs, sort_keys=True), before)


class TestTheGateBlocks(unittest.TestCase):
    """M7-P2-T2. FR-TRC-05, NFR-VAL-03."""

    def unclaimed(self):
        thin = spec("plan", [catalogue("milestones", [
            unit("M1", traces={"fr": ["FR-DOC-01"]})])])
        return {"Z2S-FSD.html": FSD, "Z2S-Plan.html": thin}

    def test_an_unclaimed_requirement_fails_and_is_named(self):
        found = [one for one in trace.check(self.unclaimed())
                 if one.code == "uncovered"]
        self.assertEqual([one.where for one in found], ["FR-DOC-02"])
        self.assertEqual(found[0].severity, schema.FAILURE)
        self.assertIn("FR-DOC-02", found[0].message)

    def test_the_message_names_the_area_so_the_fix_is_obvious(self):
        """Named as the area, not merely as the first half of the identifier."""
        found = [one for one in trace.check(self.unclaimed())
                 if one.code == "uncovered"]
        self.assertIn("(FR-DOC)", found[0].message)

    def test_the_command_exits_non_zero(self):
        self.assertEqual(trace.exit_code(trace.check(self.unclaimed())), 1)

    def test_no_argument_downgrades_the_failure(self):
        """M7-P2-T2-C2: severity is a property of the rule, not of a caller."""
        for name in ("severity", "warn", "allow", "downgrade", "ignore"):
            self.assertNotIn(name, trace.USAGE)
        found = trace.check(self.unclaimed())
        self.assertTrue(any(one.severity == schema.FAILURE for one in found))

    def test_a_full_set_passes(self):
        specs = {"Z2S-FSD.html": FSD, "Z2S-SDD.html": SDD, "Z2S-Plan.html": PLAN}
        self.assertEqual(trace.exit_code(trace.check(specs)), 0)


class TestDeferredWorkPassesAndStaysVisible(unittest.TestCase):
    """LD-01, M7-05. FR-TRC-05: the failure condition is 'scheduled nowhere'."""

    def specs(self):
        later = spec("plan", [catalogue("milestones", [
            unit("M1", traces={"fr": ["FR-DOC-01"]}),
            unit("M9", deferred="moved to v3 on 2026-08-14"),
            unit("M9-P1-T1", traces={"fr": ["FR-DOC-02"]}),
        ])])
        return {"Z2S-FSD.html": FSD, "Z2S-Plan.html": later}

    def test_a_deferred_claim_is_still_a_claim(self):
        self.assertEqual(trace.exit_code(trace.check(self.specs())), 0)

    def test_it_is_reported_as_a_warning_naming_the_milestone(self):
        found = [one for one in trace.check(self.specs()) if one.code == "deferred"]
        self.assertEqual([one.where for one in found], ["FR-DOC-02"])
        self.assertEqual(found[0].severity, schema.WARNING)
        self.assertIn("M9", found[0].message)
        self.assertIn("moved to v3", found[0].message)

    def test_a_task_under_a_deferred_milestone_is_deferred_too(self):
        rows = dict((row.id, row) for row in trace.matrix(self.specs()))
        self.assertEqual(rows["FR-DOC-02"].state, trace.DEFERRED_ONLY)
        self.assertEqual(rows["FR-DOC-02"].deferred, ["M9-P1-T1"])

    def test_one_live_claim_is_enough_to_be_ordinary(self):
        specs = self.specs()
        specs["Z2S-Plan.html"]["sections"][0]["items"][0]["traces"]["fr"].append(
            "FR-DOC-02")
        rows = dict((row.id, row) for row in trace.matrix(specs))
        self.assertEqual(rows["FR-DOC-02"].state, trace.CLAIMED)


class TestLeavingTheUniverse(unittest.TestCase):
    """M7-P2-T3, M7-P2-T4, M7-03. FR-TRC-06, FR-TRC-02, ADR-03."""

    def excluded(self, **fields):
        return {"Z2S-FSD.html": spec("fsd", [catalogue("requirements", [
            entry("FR-DOC-01", "Kept", **{}),
            entry("FR-DOC-02", "Dropped", priority="Won't", **fields)])]),
            "Z2S-Plan.html": spec("plan", [catalogue("milestones", [
                unit("M1", traces={"fr": ["FR-DOC-01"]})])])}

    def test_an_exclusion_with_a_reason_needs_no_unit_of_work(self):
        found = trace.check(self.excluded(notes="Out of scope for v2."))
        self.assertEqual([one for one in found if one.severity == schema.FAILURE], [])

    def test_an_exclusion_without_a_reason_is_rejected(self):
        """M7-P2-T3-C1."""
        found = [one for one in trace.check(self.excluded())
                 if one.code == "excluded-without-reason"]
        self.assertEqual([one.where for one in found], ["FR-DOC-02"])
        self.assertEqual(found[0].severity, schema.FAILURE)

    def test_exclusions_are_reported_with_the_matrix(self):
        """M7-P2-T3-C2."""
        specs = self.excluded(notes="Out of scope for v2.")
        rows = dict((row.id, row) for row in trace.matrix(specs))
        self.assertEqual(rows["FR-DOC-02"].state, "excluded")
        report = trace.format_report(trace.check(specs), trace.matrix(specs),
                                     specs, list(specs))
        self.assertIn("excluded: 1", report)

    def test_a_retired_identifier_is_still_declared(self):
        """M7-P2-T4-C1: reserved, not deleted. Every trace to it still means it."""
        specs = {"Z2S-FSD.html": spec("fsd", [catalogue("requirements", [
            entry("FR-DOC-01", "Gone", retired="Replaced by FR-DOC-04.")])])}
        self.assertIn("FR-DOC-01", trace.defines(specs))
        self.assertEqual(trace.universe(specs)["FR-DOC-01"].state, "retired")
        self.assertEqual([one for one in trace.check(specs)
                          if one.severity == schema.FAILURE], [])

    def test_retiring_without_a_reason_is_rejected(self):
        specs = {"Z2S-FSD.html": spec("fsd", [catalogue("requirements", [
            entry("FR-DOC-01", "Gone", retired="")])])}
        found = [one for one in trace.check(specs)
                 if one.code == "retired-without-reason"]
        self.assertEqual([one.where for one in found], ["FR-DOC-01"])

    def test_reusing_a_retired_number_fails(self):
        """M7-P2-T4-C2. The number belongs to the thing that had it."""
        specs = {"Z2S-FSD.html": spec("fsd", [catalogue("requirements", [
            entry("FR-DOC-01", "Gone", retired="Replaced by FR-DOC-04.")])]),
            "Addendum.html": spec("addendum", [catalogue("requirements", [
                entry("FR-DOC-01", "Something new")])])}
        found = [one for one in trace.check(specs)
                 if one.code == "retired-identifier-reused"]
        self.assertEqual([one.where for one in found], ["FR-DOC-01"])
        self.assertEqual(found[0].severity, schema.FAILURE)

    def test_a_retired_requirement_needs_no_unit_of_work(self):
        specs = {"Z2S-FSD.html": spec("fsd", [catalogue("requirements", [
            entry("FR-DOC-01", "Gone", retired="Replaced.")])])}
        self.assertEqual(trace.exit_code(trace.check(specs)), 0)


# ------------------------------------------------------------------ the command

class TestTheCommand(Sandbox):

    def run_command(self, argv):
        out = io.StringIO()
        code = trace.main(argv, out)
        return code, out.getvalue()

    def test_no_arguments_asks_for_some(self):
        code, said = self.run_command([])
        self.assertEqual(code, 2)
        self.assertIn("usage", said)

    def test_a_covered_set_passes_and_says_what_it_read(self):
        sources = [self.written("Z2S-FSD.html", FSD),
                   self.written("Z2S-SDD.html", SDD),
                   self.written("Z2S-Plan.html", PLAN)]
        code, said = self.run_command(sources)
        self.assertEqual(code, 0, said)
        self.assertIn("3 read, 0 skipped", said)
        self.assertIn("universe: 4", said)
        self.assertIn("OK:", said)

    def test_an_uncovered_set_fails_and_names_it(self):
        thin = spec("plan", [catalogue("milestones", [
            unit("M1", traces={"fr": ["FR-DOC-01"]})])])
        sources = [self.written("Z2S-FSD.html", FSD),
                   self.written("Z2S-Plan.html", thin)]
        code, said = self.run_command(sources)
        self.assertEqual(code, 1)
        self.assertIn("FR-DOC-02", said)
        self.assertIn("1 failure", said)

    def test_a_warning_alone_never_fails_the_run(self):
        later = spec("plan", [catalogue("milestones", [
            unit("M1", traces={"fr": ["FR-DOC-01"]}),
            unit("M9", deferred="moved to v3"),
            unit("M9-P1-T1", traces={"fr": ["FR-DOC-02"]})])])
        sources = [self.written("Z2S-FSD.html", FSD),
                   self.written("Z2S-Plan.html", later)]
        code, said = self.run_command(sources)
        self.assertEqual(code, 0)
        self.assertIn("0 failures, 1 warning", said)


# --------------------------------------------------------------- routing a set

class TestWritingTheRoutingMapBack(Sandbox):
    """FR-TRC-07: a trace shown to a reader is a working link."""

    def project(self):
        from z2s import paths
        paths.ensure_layout(self.root)
        directory = paths.resolve(self.root, paths.SPECS_DIR)
        for name, body in (("Z2S-FSD.html", FSD), ("Z2S-SDD.html", SDD)):
            with open(os.path.join(directory, name), "w", encoding="utf-8") as handle:
                handle.write(rendered(body))
        return directory

    def test_every_document_learns_where_its_siblings_live(self):
        directory = self.project()
        written, found = trace.route(self.root)
        self.assertEqual(len(written), 2)

        from z2s import validate
        for path in written:
            with open(path, encoding="utf-8") as handle:
                carried = validate.extract(handle.read())
            self.assertEqual(carried["links"]["FR-DOC"], "Z2S-FSD.html")
            self.assertEqual(carried["links"]["ADR"], "Z2S-SDD.html")

    def test_the_document_itself_is_unchanged_apart_from_the_map(self):
        self.project()
        trace.route(self.root)
        from z2s import validate
        path = os.path.join(self.root, ".zero", "specs", "Z2S-FSD.html")
        with open(path, encoding="utf-8") as handle:
            carried = validate.extract(handle.read())
        carried.pop("links")
        self.assertEqual(carried["sections"], FSD["sections"])


# ------------------------------------------------ the set, in a real browser

def page(body_spec):
    """One published document, assembled the way a project publishes one."""
    from z2s import document, runtime, shell, styles, tokens
    block = body_spec["document"]
    return shell.assemble(
        spec_id="%s-spec" % block["slug"], spec_json=document.serialise(body_spec),
        title=block["title"], description=block.get("summary", ""),
        tokens=tokens.render(tokens.NEUTRAL), struct=styles.STRUCT,
        runtime=runtime.SOURCE)


AREA = [{"key": "FR-DOC", "name": "Documents"}]
NEW_AREA = [{"key": "FR-NEW", "name": "Later scope"}]

SET_FSD = spec("fsd", [catalogue("requirements", [
    entry("FR-DOC-01", "Documents are generated", area="FR-DOC"),
    entry("FR-DOC-02", "Documents carry their own data", area="FR-DOC"),
], areas=AREA)])

SET_ADDENDUM = spec("addendum", [catalogue("requirements", [
    entry("FR-NEW-01", "Scope that arrived later", area="FR-NEW"),
], areas=NEW_AREA)])

SET_STORIES = spec("stories", [catalogue("stories", [
    entry("US-DOC-01", "A reader follows a trace", area="US-DOC",
          traces={"fr": ["FR-DOC-02", "FR-NEW-01"], "us": ["US-DOC-02"]}),
    entry("US-DOC-02", "Another story", area="US-DOC"),
], areas=[{"key": "US-DOC", "name": "Documents"}])])


def drive_browser():
    """One browser run, shared by every check below."""
    import subprocess
    if shutil.which("node") is None:
        return None, "node is not installed"

    specs = {"Z2S-FSD.html": SET_FSD, "Addendum.html": SET_ADDENDUM,
             "Z2S-Stories.html": SET_STORIES}
    routes = trace.links(specs)
    pages = {}
    for name in specs:
        carried = dict(specs[name], links=routes)
        pages[name] = page(carried)

    request = {"op": "trace", "pages": pages, "start": "Z2S-Stories.html",
               "away": "FR-NEW-01", "local": "US-DOC-02"}
    harness = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "trace_harness.js")
    finished = subprocess.run([shutil.which("node"), harness],
                              input=json.dumps(request),
                              capture_output=True, text=True)
    if finished.returncode == 3:
        return None, finished.stderr.strip()
    if finished.returncode != 0:
        raise AssertionError("trace harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout), None


SEEN, REASON = drive_browser()


@unittest.skipIf(SEEN is None, "no browser available: %s" % REASON)
class TestFollowingATraceInABrowser(unittest.TestCase):
    """M7-P1-T2-C1, against a real set in a real browser.

    A skipped check here is reported as skipped and never counted as a pass
    (LD-04, FR-GEN-03, NFR-VAL-05).
    """

    @classmethod
    def setUpClass(cls):
        cls.seen = SEEN

    def chip(self, identifier):
        for one in self.seen["chips"]:
            if one["id"] == identifier:
                return one
        raise AssertionError("no chip for %s in %s" % (identifier, self.seen["chips"]))

    def test_a_trace_to_another_document_is_a_link_to_that_document(self):
        self.assertEqual(self.chip("FR-DOC-02")["href"], "Z2S-FSD.html#FR-DOC-02")
        self.assertEqual(self.chip("FR-NEW-01")["href"], "Addendum.html#FR-NEW-01")

    def test_a_trace_to_this_document_is_a_local_link(self):
        self.assertEqual(self.chip("US-DOC-02")["href"], "#US-DOC-02")

    def test_following_an_addendum_trace_lands_in_the_addendum(self):
        self.assertEqual(self.seen["away"]["file"], "Addendum.html")
        self.assertEqual(self.seen["away"]["hash"], "#FR-NEW-01")

    def test_the_entry_it_lands_on_is_open_and_marked(self):
        """It lands inside a fold, so arriving is not the same as being read."""
        self.assertTrue(self.seen["away"]["found"])
        self.assertTrue(self.seen["away"]["visible"])
        self.assertTrue(self.seen["away"]["marked"])

    def test_a_local_trace_does_not_leave_the_page(self):
        self.assertEqual(self.seen["local"]["file"], "Z2S-Stories.html")
        self.assertTrue(self.seen["local"]["visible"])
        self.assertTrue(self.seen["local"]["marked"])


if __name__ == "__main__":
    unittest.main()
