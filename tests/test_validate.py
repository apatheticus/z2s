# -*- coding: utf-8 -*-
"""The schema validator (M2-P2).

One command reads a set of finished documents, checks each against the contract
its type declares, and reports everything it finds in a single run. It is meant
to be wired straight into a continuous-integration gate, so its exit status is
the answer and its output is for a person.

Three properties are load-bearing and each has its own tests below:

  * exhaustive — every violation in the set is reported in one run, grouped by
    document, never stopping at the first (NFR-VAL-01);
  * set-wide — duplicates and dangling traces are questions no single document
    can answer, so the validator builds one index across the whole set;
  * honest — a warning never fails a build and a failure never passes as a
    warning, and no flag can move a finding between the two (FR-VAL-06).

Traces: FR-SPC-04, FR-TRC-02, FR-TRC-08, FR-VAL-01, FR-VAL-03, FR-VAL-05,
FR-VAL-06, NFR-DAT-02, NFR-VAL-01, NFR-VAL-06, ADR-03.
"""

import glob
import inspect
import io
import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import document, schema, validate

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE = os.path.join(os.path.dirname(HERE), "z2s")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def spec(slug="fsd", identifier="FR-DOC-01", **overrides):
    """A clean specification object; each test damages its own copy."""
    built = {
        "document": {
            "title": "Acme — %s" % slug.upper(),
            "slug": slug,
            "type": "Functional Specification Document (FSD)",
            "version": "1.0",
            "status": "Draft for review",
            "date": "2026-08-14",
            "owner": "Acme Engineering",
        },
        "schemaVersion": schema.SCHEMA_VERSION,
        "sections": [{"id": "requirements", "title": "Requirements", "type": "catalog",
                      "entries": [{"id": identifier, "priority": "Must",
                                   "title": "Seven document types",
                                   "text": "The system shall …"}]}],
    }
    built.update(overrides)
    return built


def write(folder, name, obj):
    """Render a real document the way a generator would, and save it."""
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(document.render(obj, obj["document"]["slug"] + "-spec"))
    return path


class TestExtraction(unittest.TestCase):
    """M2-P2-T4. FR-SPC-04, NFR-DAT-02."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-extract-")

    def test_extraction_returns_the_object_for_a_valid_file(self):
        original = spec()
        found = validate.extract(read(write(self.folder, "a.html", original)))
        self.assertEqual(original, found)

    def test_a_value_containing_a_closing_tag_survives_the_round_trip(self):
        """The embedding escapes "</" so a specification cannot end its own
        script element. Extraction has to undo exactly that and nothing else."""
        original = spec()
        original["sections"][0]["entries"][0]["text"] = "Write </script> in prose."
        found = validate.extract(read(write(self.folder, "b.html", original)))
        self.assertEqual("Write </script> in prose.",
                         found["sections"][0]["entries"][0]["text"])

    def test_a_truncated_block_produces_a_named_failure_not_an_exception_trace(self):
        html = read(write(self.folder, "c.html", spec()))
        broken = html.replace('"schemaVersion"', '"schemaVersion',  1)
        with self.assertRaises(validate.ExtractionError) as raised:
            validate.extract(broken)
        message = str(raised.exception)
        self.assertIn("line", message.lower())
        self.assertNotIn("Traceback", message)

    def test_a_document_with_no_embedded_block_is_named_not_guessed_at(self):
        with self.assertRaises(validate.ExtractionError) as raised:
            validate.extract("<!doctype html><html><body>Nothing here.</body></html>")
        self.assertIn("no embedded specification", str(raised.exception))

    def test_the_block_is_found_whatever_the_document_type_calls_it(self):
        """NFR-DAT-01: the element identifier is type-specific and stable, so
        extraction keys off the element's type rather than a fixed identifier."""
        for slug in ("plan", "vision", "index"):
            html = document.render(spec(slug=slug), slug + "-spec")
            self.assertEqual(slug, validate.extract(html)["document"]["slug"])

    def test_extraction_exists_in_exactly_one_place(self):
        """T4 refactor: every consumer uses the shared function. A second parser
        elsewhere is a second definition of what a document is.

        `render.py` is exempt and is the only exemption: what it parses is the
        answer its own browser driver hands back on a pipe, which is not a
        document and carries no specification. It never opens a document to read
        the specification inside — the browser does that, by rendering it.
        """
        parsers = []
        for path in sorted(glob.glob(os.path.join(PACKAGE, "*.py"))):
            text = read(path)
            if "json.loads" in text and os.path.basename(path) not in (
                    "validate.py", "render.py"):
                parsers.append(os.path.basename(path))
        self.assertEqual([], parsers)
        self.assertNotIn("BLOCK", read(os.path.join(PACKAGE, "render.py")))


class TestExhaustiveReporting(unittest.TestCase):
    """M2-P2-T1. NFR-VAL-01."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-set-")
        missing_owner = spec(slug="fsd")
        del missing_owner["document"]["owner"]

        malformed = spec(slug="sdd")
        malformed["sections"][0]["entries"][0]["id"] = "NFR-ARC-3"

        dangling = spec(slug="prd")
        # A distinct identifier: two fixtures sharing one would seed a fourth
        # violation, and this test is about counting exactly the three seeded.
        dangling["sections"][0]["entries"][0]["id"] = "FR-PLN-01"
        dangling["sections"][0]["entries"][0]["traces"] = {"fr": ["FR-NOPE-99"]}

        self.paths = [write(self.folder, "a.html", missing_owner),
                      write(self.folder, "b.html", malformed),
                      write(self.folder, "c.html", dangling)]

    def test_three_seeded_violations_produce_three_failures_in_one_run(self):
        grouped = validate.validate_set(self.paths)
        failures = [f for found in grouped.values() for f in found
                    if f.severity == schema.FAILURE]
        self.assertEqual(3, len(failures))

    def test_the_failures_are_grouped_by_document(self):
        grouped = validate.validate_set(self.paths)
        self.assertEqual([os.path.basename(p) for p in self.paths],
                         [os.path.basename(k) for k in grouped])
        for found in grouped.values():
            self.assertEqual(1, len(found))

    def test_exit_status_is_non_zero_when_any_failure_exists(self):
        self.assertNotEqual(0, validate.exit_code(validate.validate_set(self.paths)))

    def test_a_clean_set_exits_zero_and_says_so(self):
        folder = tempfile.mkdtemp(prefix="z2s-clean-")
        paths = [write(folder, "a.html", spec(slug="fsd")),
                 write(folder, "b.html", spec(slug="sdd", identifier="NFR-ARC-01"))]
        grouped = validate.validate_set(paths)
        self.assertEqual(0, validate.exit_code(grouped))
        self.assertIn("OK", validate.format_report(grouped))

    def test_collection_is_separate_from_formatting(self):
        """T1 refactor. The same results are printed by the command and returned
        to a caller; only one of the two may exist as a string."""
        grouped = validate.validate_set(self.paths)
        for found in grouped.values():
            for finding in found:
                self.assertIsInstance(finding, schema.Finding)
        self.assertIsInstance(validate.format_report(grouped), str)

    def test_every_failure_is_named_in_the_printed_report(self):
        grouped = validate.validate_set(self.paths)
        report = validate.format_report(grouped)
        for name in ("owner", "NFR-ARC-3", "FR-NOPE-99"):
            self.assertIn(name, report)

    def test_a_document_that_cannot_be_read_is_a_failure_not_a_crash(self):
        path = os.path.join(self.folder, "empty.html")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("<html><body>no block</body></html>")
        grouped = validate.validate_set([path])
        self.assertEqual(1, len(grouped[path]))
        self.assertEqual(schema.FAILURE, grouped[path][0].severity)

    def test_a_document_whose_major_version_is_unreadable_is_refused_not_guessed(self):
        """FR-VAL-01. Checking a document you do not understand produces
        findings about a contract that may not apply to it."""
        future = spec(slug="fsd", schemaVersion="9.0")
        del future["document"]["owner"]
        path = write(self.folder, "future.html", future)
        found = validate.validate_set([path])[path]
        self.assertEqual(1, len(found))
        self.assertIn("9.0", found[0].message)
        self.assertNotIn("owner", found[0].message)


class TestDuplicateAndDanglingIdentifiers(unittest.TestCase):
    """M2-P2-T2. FR-TRC-02, FR-TRC-08, FR-VAL-03, ADR-03."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-index-")

    def test_a_duplicate_identifier_is_reported_with_both_locations(self):
        first = write(self.folder, "one.html", spec(slug="fsd"))
        second = write(self.folder, "two.html", spec(slug="sdd"))
        grouped = validate.validate_set([first, second])
        failures = [f for found in grouped.values() for f in found]
        self.assertEqual(1, len(failures))
        self.assertIn("one.html", failures[0].message)
        self.assertIn("two.html", failures[0].message)
        self.assertIn("FR-DOC-01", failures[0].message)

    def test_a_duplicate_within_one_document_is_reported_too(self):
        twice = spec(slug="fsd")
        twice["sections"][0]["entries"].append(
            {"id": "FR-DOC-01", "priority": "Must", "title": "Again", "text": "…"})
        path = write(self.folder, "one.html", twice)
        self.assertEqual(1, len(validate.validate_set([path])[path]))

    def test_a_measure_declared_in_two_documents_is_a_duplicate(self):
        """M3-01. The index skips any identifier the prefix map does not know,
        so an unregistered prefix is silently exempt from the one check that
        makes an identifier permanent. Registering MT is what makes this fail."""
        for slug, name in (("prd", "one.html"), ("fsd", "two.html")):
            carrying = spec(slug=slug)
            carrying["sections"].append(
                {"id": "measures", "title": "Measures", "type": "cards",
                 "items": [{"id": "MT-01", "title": "MT-01 · Unscheduled work",
                            "body": "Target: zero."}]})
            write(self.folder, name, carrying)

        failures = [f for found in validate.validate_set(
            [os.path.join(self.folder, "one.html"),
             os.path.join(self.folder, "two.html")]).values() for f in found]
        collisions = [f for f in failures if f.code == "duplicate-identifier"
                      and "MT-01" in f.message]
        self.assertEqual(1, len(collisions))
        self.assertIn("one.html", collisions[0].message)
        self.assertIn("two.html", collisions[0].message)

    def test_a_dangling_trace_names_the_trace_and_its_owner(self):
        dangling = spec(slug="fsd")
        dangling["sections"][0]["entries"][0]["traces"] = {"adr": ["ADR-99"]}
        path = write(self.folder, "one.html", dangling)
        found = validate.validate_set([path])[path]
        self.assertEqual(1, len(found))
        self.assertIn("ADR-99", found[0].message)
        self.assertIn("FR-DOC-01", found[0].message)

    def test_a_trace_reaching_another_document_in_the_set_is_not_dangling(self):
        """The whole reason the index spans the set: a trace across documents is
        the normal case, not an error."""
        upstream = spec(slug="sdd")
        upstream["sections"][0]["entries"][0]["id"] = "ADR-04"
        downstream = spec(slug="fsd")
        downstream["sections"][0]["entries"][0]["traces"] = {"adr": ["ADR-04"]}
        paths = [write(self.folder, "one.html", upstream),
                 write(self.folder, "two.html", downstream)]
        self.assertEqual(0, validate.exit_code(validate.validate_set(paths)))

    def test_an_entry_naming_an_area_that_does_not_exist_fails(self):
        stray = spec(slug="fsd")
        stray["sections"][0]["entries"][0]["area"] = "FR-GHOST"
        path = write(self.folder, "one.html", stray)
        found = validate.validate_set([path])[path]
        self.assertEqual(1, len(found))
        self.assertIn("FR-GHOST", found[0].message)

    def test_an_area_declared_as_a_legend_key_is_accepted(self):
        """A catalogue declares its areas in a legend beside the entries, where
        each carries a `key` rather than an `id`. Looking only for identifiers
        made every requirement in a real document name a missing area."""
        declared = spec(slug="fsd")
        declared["sections"][0]["areas"] = [{"key": "FR-DOC", "name": "Documents"}]
        declared["sections"][0]["entries"][0]["area"] = "FR-DOC"
        path = write(self.folder, "one.html", declared)
        self.assertEqual(0, validate.exit_code(validate.validate_set([path])))

    def test_an_area_key_declared_in_one_document_covers_another(self):
        catalogue = spec(slug="fsd")
        catalogue["sections"][0]["areas"] = [{"key": "FR-DOC", "name": "Documents"}]
        user = spec(slug="prd", identifier="G-01")
        user["sections"][0]["entries"][0]["area"] = "FR-DOC"
        paths = [write(self.folder, "one.html", catalogue),
                 write(self.folder, "two.html", user)]
        self.assertEqual(0, validate.exit_code(validate.validate_set(paths)))

    def test_a_declared_area_is_accepted(self):
        declared = spec(slug="fsd")
        declared["sections"][0]["groups"] = [{"id": "FR-DOC", "title": "Documents"}]
        declared["sections"][0]["entries"][0]["area"] = "FR-DOC"
        path = write(self.folder, "one.html", declared)
        self.assertEqual(0, validate.exit_code(validate.validate_set([path])))

    def test_the_index_is_exposed_for_later_tools_to_reuse(self):
        """T2 refactor. The traceability matrix and the coverage gate need the
        same index; rebuilding it in each tool is where the two drift."""
        index = validate.build_index({"one.html": spec(slug="fsd")})
        self.assertIn("FR-DOC-01", index)
        self.assertEqual(["one.html"], [where for where, _ in index["FR-DOC-01"]])


class TestWarningsAreNotFailures(unittest.TestCase):
    """M2-P2-T3. FR-VAL-06, NFR-VAL-06."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-warn-")

    def warning_only(self):
        older = spec(slug="fsd", schemaVersion="1.0")
        older["schemaVersion"] = "1." + str(int(schema.SCHEMA_VERSION.split(".")[1]) + 7)
        return write(self.folder, "older.html", older)

    def test_a_warning_only_run_exits_zero(self):
        grouped = validate.validate_set([self.warning_only()])
        findings = [f for found in grouped.values() for f in found]
        self.assertTrue(findings)
        self.assertTrue(all(f.severity == schema.WARNING for f in findings))
        self.assertEqual(0, validate.exit_code(grouped))

    def test_the_summary_states_a_count_for_each_severity(self):
        """T3 refactor. A reader needs to know a run had warnings even though it
        passed, or the warnings are never read."""
        grouped = validate.validate_set([self.warning_only()])
        summary = validate.format_report(grouped).strip().splitlines()[-1]
        self.assertIn("0 failures", summary)
        self.assertIn("1 warning", summary)

    def test_no_configuration_downgrades_a_failure(self):
        """Severity is a property of the rule. If any entry point accepted a
        knob for it, a red build could be made green without fixing anything."""
        knobs = re.compile(r"sever|strict|ignore|downgrade|lenient|warn_only|force")
        for name in ("validate_set", "validate_document", "exit_code",
                     "format_report", "main"):
            signature = inspect.signature(getattr(validate, name))
            for parameter in signature.parameters:
                self.assertIsNone(knobs.search(parameter),
                                  "%s accepts %r" % (name, parameter))

    def test_the_command_accepts_no_flag_that_moves_a_finding(self):
        source = read(os.path.join(PACKAGE, "validate.py"))
        for flag in ("--no-fail", "--warn-only", "--ignore", "--severity", "--soft"):
            self.assertNotIn(flag, source)

    def test_a_failure_and_a_warning_in_one_run_still_fails(self):
        broken = spec(slug="sdd")
        del broken["document"]["owner"]
        paths = [self.warning_only(), write(self.folder, "broken.html", broken)]
        grouped = validate.validate_set(paths)
        self.assertNotEqual(0, validate.exit_code(grouped))


class TestTheCommand(unittest.TestCase):
    """FR-VAL-05: wired directly into a CI gate, so the exit status is the answer."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-cli-")

    def test_the_command_returns_non_zero_on_a_failing_set(self):
        broken = spec(slug="fsd")
        del broken["document"]["owner"]
        path = write(self.folder, "a.html", broken)
        self.assertNotEqual(0, validate.main([path], out=io.StringIO()))

    def test_the_command_returns_zero_on_a_clean_set(self):
        path = write(self.folder, "a.html", spec(slug="fsd"))
        self.assertEqual(0, validate.main([path], out=io.StringIO()))

    def test_the_command_reports_a_path_that_does_not_exist(self):
        missing = os.path.join(self.folder, "nope.html")
        self.assertNotEqual(0, validate.main([missing], out=io.StringIO()))

    def test_the_command_with_no_arguments_explains_itself(self):
        self.assertNotEqual(0, validate.main([], out=io.StringIO()))


class TestTheProjectsOwnVocabulary(unittest.TestCase):
    """M5-P2-T3, M5-07: every project has words its own readers follow perfectly
    well, and a rule with no way to say so is a rule that gets switched off."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-allow-")

    def jargon(self, **overrides):
        return spec(sections=[{"id": "purpose", "type": "prose", "title": "Purpose",
                               "body": ["The report is written to summary.md."]}],
                    **overrides)

    def warnings(self, argv):
        report = io.StringIO()
        validate.main(argv, out=report)
        return [line for line in report.getvalue().splitlines() if "WARNING" in line]

    def test_an_internal_name_in_reader_facing_prose_is_reported(self):
        """M5-P2-T3-C1."""
        path = write(self.folder, "a.html", self.jargon())
        self.assertTrue(self.warnings([path]))

    def test_a_named_term_is_silenced_by_the_allowlist(self):
        path = write(self.folder, "a.html", self.jargon())
        self.assertEqual([], self.warnings(["--allow", "summary.md", path]))

    def test_the_allowlist_also_reads_as_one_argument(self):
        path = write(self.folder, "a.html", self.jargon())
        self.assertEqual([], self.warnings(["--allow=summary.md,other.md", path]))

    def test_a_comma_separated_allowlist_silences_each_of_them(self):
        sources, allowed = validate.allowlist(["--allow", "a.py, b.js", "doc.html"])
        self.assertEqual(["doc.html"], sources)
        self.assertEqual(["a.py", "b.js"], allowed)

    def test_the_flag_is_never_mistaken_for_a_document(self):
        sources, _ = validate.allowlist(["--allow", "a.py", "doc.html"])
        self.assertEqual(["doc.html"], sources)

    def test_a_run_of_nothing_but_the_flag_still_explains_itself(self):
        self.assertNotEqual(0, validate.main(["--allow", "a.py"], out=io.StringIO()))

    def test_the_warning_alone_does_not_fail_the_run(self):
        """M5-08, FR-VAL-06: a Should must not turn a build red."""
        path = write(self.folder, "a.html", self.jargon())
        self.assertEqual(0, validate.main([path], out=io.StringIO()))

    def crossref(self, target):
        return spec(sections=[{"id": "purpose", "type": "prose", "title": "Purpose",
                               "body": ["The decisions behind it are in %s." % target]}])

    def test_a_document_naming_its_sibling_is_not_naming_jargon(self):
        """A cross-reference is how a reader reaches the next document; the set
        it belongs to is what says so."""
        one = write(self.folder, "one.html", self.crossref("two.html"))
        two = write(self.folder, "two.html", self.crossref("one.html"))
        self.assertEqual([], self.warnings([one, two]))

    def test_a_name_the_set_does_not_publish_is_still_reported(self):
        """The pass is granted by the set, not by looking like a filename."""
        one = write(self.folder, "one.html", self.crossref("elsewhere.html"))
        self.assertTrue(self.warnings([one]))

    def test_a_document_checked_alone_knows_of_no_siblings(self):
        """Nothing in a lone document tells a reader where that name leads, so
        saying so is honest rather than a gap in the rule."""
        one = write(self.folder, "one.html", self.crossref("two.html"))
        write(self.folder, "two.html", self.crossref("one.html"))
        self.assertTrue(self.warnings([one]))

    def test_the_set_is_read_from_the_names_given_not_the_folder(self):
        """The run is the set. A file sitting beside them that nobody asked to
        check grants nothing."""
        self.assertEqual(["a.html", "b.html"],
                         validate.published_names(["docs/a.html", "/tmp/b.html"]))


# ----------------------------------------------- the finished plan document (M9)

def task_entry(identifier="M1-P1-T1", **overrides):
    """One task, shaped as a rendered plan document carries it."""
    entry = {"id": identifier, "area": "M1-P1", "priority": "Must",
             "status": "not-started", "autonomy": "auto", "layer": "validator",
             "title": "Validate from the rendered output",
             "text": "Open each produced file and check what it says.",
             "testLayers": ["unit"],
             "tdd": {"red": "A truncated file is not caught.",
                     "green": "Read the produced files.",
                     "refactor": "Assert no generator is imported."},
             "criteria": [{"id": identifier + "-C1", "kind": "auto",
                           "text": "A truncated output file fails validation.",
                           "done": False}],
             "traces": {"fr": ["FR-VAL-02"]}}
    entry.update(overrides)
    return entry


def milestone_spec(items=None, **overrides):
    """A milestone document: one phase, one task, and a catalogue to claim from."""
    built = {
        "document": {"title": "Acme — M1", "slug": "plan", "type": "Development plan",
                     "version": "1.0", "status": "Draft for review",
                     "date": "2026-08-14", "owner": "Acme Engineering",
                     "milestone": "M1"},
        "schemaVersion": schema.SCHEMA_VERSION,
        "legend": schema.legend(),
        "catalog": {"FR-VAL-02": "Validate the deliverable"},
        "sections": [{"id": "work", "type": "requirements",
                      "title": "Phases, tasks and acceptance criteria",
                      "areas": [{"key": "M1-P1", "name": "Rendered-artefact validation",
                                 "description": "Check the produced files."}],
                      "items": [task_entry()] if items is None else items}],
    }
    built.update(overrides)
    return built


def index_spec(files=None, waves=(("M1",),), **overrides):
    """A plan index: which milestones run when, and which file each is in."""
    built = {
        "document": {"title": "Acme — Plan", "slug": "plan", "type": "Development plan",
                     "version": "1.0", "status": "Draft for review",
                     "date": "2026-08-14", "owner": "Acme Engineering",
                     "milestone": ""},
        "schemaVersion": schema.SCHEMA_VERSION,
        "legend": schema.legend(),
        "catalog": {"FR-VAL-02": "Validate the deliverable"},
        "sections": [{"id": "waves", "type": "waves",
                      "title": "Parallel execution waves",
                      "files": {"M1": "M1-toolchain.html"} if files is None else files,
                      "waves": [list(one) for one in waves]}],
    }
    built.update(overrides)
    return built


class PlanCase(unittest.TestCase):
    """Each test writes its own damaged plan and reads what the run says."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-plan-doc-")

    def findings(self, *documents, **kwargs):
        """Every finding from a run of this plan and the specification it claims.

        The requirement document is always in the run: a plan claims what the
        specifications state, and a set missing them reports every claim as
        dangling, which is a true finding about the set and no help at all here.
        """
        sources = [write(self.folder, "FSD.html", spec(identifier="FR-VAL-02"))]
        sources += [write(self.folder, name, obj) for name, obj in documents]
        grouped = validate.validate_set(sources, kwargs.get("allowed", ()))
        return [finding for found in grouped.values() for finding in found]

    def codes(self, *documents, **kwargs):
        return sorted(set(one.code for one in self.findings(*documents, **kwargs)))

    def failures(self, *documents, **kwargs):
        return [one for one in self.findings(*documents, **kwargs)
                if one.severity == schema.FAILURE]


class TestTheFinishedPlanHoldsUp(PlanCase):
    """M9-P1-T2. FR-VAL-04, NFR-VAL-01, ADR-09.

    The plan is the one document written back to after it is generated, so what
    it says about a task has to be checked in the finished file rather than
    trusted from the run that produced it.
    """

    def test_a_sound_plan_produces_nothing(self):
        """A check that fires on everything proves nothing when it fires."""
        self.assertEqual([], self.findings(("M1-toolchain.html", milestone_spec()),
                                           ("index.html", index_spec())))

    def test_a_task_without_a_status_fails(self):
        """M9-P1-T2-C1: a task the plan cannot state the state of is a task
        nothing can be scheduled behind."""
        without = task_entry()
        del without["status"]
        found = self.failures(("M1-toolchain.html", milestone_spec([without])))
        self.assertEqual(["plan-status"], sorted(set(one.code for one in found)))
        self.assertIn("M1-P1-T1", found[0].where)

    def test_a_task_with_no_acceptance_criteria_fails(self):
        found = self.failures(("M1-toolchain.html",
                               milestone_spec([task_entry(criteria=[])])))
        self.assertIn("plan-criteria", [one.code for one in found])

    def test_a_claim_the_plans_catalogue_does_not_list_fails(self):
        """M9-P1-T2-C2: the catalogue written into the document is the list of
        everything that plan was ever shown."""
        entry = task_entry(traces={"fr": ["FR-VAL-02", "FR-NEVER-99"]})
        found = self.failures(("M1-toolchain.html", milestone_spec([entry])))
        self.assertIn("plan-claim", [one.code for one in found])
        self.assertIn("FR-NEVER-99", " ".join(one.message for one in found))

    def test_a_milestone_with_no_detail_document_fails(self):
        """M9-P1-T2-C3: a plan that schedules work nobody can read is not a plan."""
        found = self.failures(("index.html", index_spec()))
        self.assertEqual(["plan-detail"], sorted(set(one.code for one in found)))
        self.assertIn("M1-toolchain.html", found[0].message)

    def test_a_scheduled_milestone_left_out_of_the_file_map_fails(self):
        found = self.failures(("index.html",
                               index_spec(files={"M2": "M2-later.html"})))
        self.assertIn("plan-detail", [one.code for one in found])

    def test_a_plan_that_is_one_document_is_not_asked_for_a_second_one(self):
        """A plan small enough to be one file schedules nothing outside itself,
        and there is no second file for a milestone to be missing from. The
        published set is exactly this shape."""
        single = index_spec()
        del single["sections"][0]["files"]
        self.assertEqual([], self.failures(("index.html", single)))

    def test_waiting_on_a_unit_no_document_defines_fails(self):
        entry = task_entry(dependsOn=["M1-P1-T9"])
        found = self.failures(("M1-toolchain.html", milestone_spec([entry])),
                              ("index.html", index_spec()))
        self.assertIn("plan-dependency", [one.code for one in found])

    def test_waiting_on_a_unit_in_a_milestone_this_run_does_not_hold_is_not_blamed(self):
        """A plan is one document split across files. A milestone document read
        on its own genuinely cannot see the milestone before it."""
        entry = task_entry(dependsOn=["M4-P2-T1"])
        self.assertEqual([], self.failures(("M1-toolchain.html", milestone_spec([entry]))))

    def test_the_checks_reach_a_plan_by_what_the_document_says_it_is(self):
        """Not by filename, and not by asking a generator (ADR-09)."""
        ordinary = spec()
        self.assertEqual({}, validate.plan_specs({"a.html": ordinary}))
        self.assertEqual(["b.html"],
                         list(validate.plan_specs({"a.html": ordinary,
                                                   "b.html": milestone_spec()})))

    def test_every_hole_in_one_plan_is_reported_in_one_run(self):
        """NFR-VAL-01: three round trips is where a reader stops running it."""
        broken = task_entry(criteria=[], traces={"fr": ["FR-NEVER-99"]})
        del broken["status"]
        found = set(one.code for one in
                    self.failures(("M1-toolchain.html", milestone_spec([broken]))))
        self.assertLessEqual({"plan-claim", "plan-criteria", "plan-status"}, found)


class TestDeclaredExceptions(PlanCase):
    """M9-P1-T3. FR-VAL-08, NFR-VAL-04.

    An exception is a decision somebody made rather than a hole somebody left,
    so it warns rather than fails — and it is stated on every run, because an
    exception granted once and never mentioned again stops being a decision and
    becomes the way things are.
    """

    def excused(self, rule="layer", reason="This task writes no code.", **extra):
        entry = task_entry(exceptions=[dict({"rule": rule, "reason": reason}, **extra)])
        entry.pop("layer", None)
        return ("M1-toolchain.html", milestone_spec([entry]))

    def test_an_active_exception_is_reported_on_every_run(self):
        """M9-P1-T3-C1."""
        for _ in range(3):
            found = self.findings(self.excused())
            self.assertEqual(["plan-exception"], sorted(set(one.code for one in found)))
            self.assertIn("This task writes no code.", found[0].message)

    def test_an_active_exception_does_not_fail_the_run(self):
        self.assertEqual([], self.failures(self.excused()))
        self.assertEqual(schema.WARNING, self.findings(self.excused())[0].severity)

    def test_an_exception_to_a_rule_that_cannot_be_excused_fails(self):
        """M9-P1-T3-C2: the narrow set is the whole mechanism. A task with no
        failing test is not an exception, it is an unfinished task."""
        found = self.failures(self.excused(rule="tdd"))
        self.assertEqual(["plan-exception"], sorted(set(one.code for one in found)))
        self.assertIn("testLayers", found[0].message)

    def test_an_exception_with_no_reason_fails(self):
        found = self.failures(self.excused(reason=""))
        self.assertEqual(["plan-exception"], sorted(set(one.code for one in found)))

    def test_no_argument_widens_the_set_of_excusable_rules(self):
        """M9-P1-T3-C2. The allowlist silences a project's own vocabulary; it is
        not a way to grant an exception nobody approved."""
        for allowed in (("tdd",), ("plan-exception",), ("M1-P1-T1",)):
            self.assertTrue(self.failures(self.excused(rule="tdd"), allowed=allowed),
                            "%r silenced an unapproved exception" % (allowed,))

    def test_a_document_cannot_declare_its_own_excusable_rules(self):
        """The set is a constant in the validator. A document that carries one
        is carrying data, and data does not change what the rules are."""
        name, plan = self.excused(rule="tdd")
        plan["excusable"] = ["tdd"]
        self.assertTrue(self.failures((name, plan)))


class TestTheValidatorReadsOnlyProducedFiles(unittest.TestCase):
    """M9-P1-T1. ADR-09, NFR-VAL-02.

    Validating the input proves the input was sound. Only reading the produced
    file proves the deliverable is.
    """

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-produced-")

    def test_a_truncated_output_file_fails_and_names_it(self):
        """M9-P1-T1-C1."""
        path = write(self.folder, "a.html", spec())
        with open(path, encoding="utf-8") as handle:
            html = handle.read()
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(html.replace('"schemaVersion"', '"schemaVersion', 1))
        report = io.StringIO()
        self.assertEqual(1, validate.main([path], out=report))
        self.assertIn("a.html", report.getvalue())
        self.assertIn("could not be parsed", report.getvalue())

    def test_the_validator_imports_no_generator(self):
        """M9-P1-T1-C2. A validator that can reach the generator's data will
        eventually check that instead, and then it is checking the input again."""
        source = read(os.path.join(PACKAGE, "validate.py"))
        imported = set()
        for line in source.splitlines():
            found = re.match(r"from z2s import (.+)$", line.strip())
            if found:
                imported.update(name.strip() for name in found.group(1).split(","))
        self.assertEqual(set(), imported & {"chain", "context", "fsd", "gate", "plan",
                                            "prd", "sdd", "stories", "vision", "writer"},
                         "the validator can reach a generator's data")


if __name__ == "__main__":
    unittest.main()
