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
        elsewhere is a second definition of what a document is."""
        parsers = []
        for path in sorted(glob.glob(os.path.join(PACKAGE, "*.py"))):
            text = read(path)
            if "json.loads" in text and os.path.basename(path) != "validate.py":
                parsers.append(os.path.basename(path))
        self.assertEqual([], parsers)


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


if __name__ == "__main__":
    unittest.main()
