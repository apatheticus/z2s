# -*- coding: utf-8 -*-
"""The document contracts (M2-P1).

Every generated document embeds one JSON object, and every tool in the method
reads it. This file is the contract that object is held to: the envelope each
document carries, the identifier grammar, the closed enumerations, typed traces,
and the rule that a section with nothing in it is absent rather than empty.

The schema is declared as data rather than as code, so the validator, the legend
a reader sees, and these tests all read the same declaration and cannot drift.

Traces: FR-DOC-08, FR-SPC-01, FR-TRC-01, FR-TRC-03, NFR-DAT-01, NFR-DAT-02,
NFR-DAT-03, NFR-DAT-04, NFR-DAT-06, NFR-DAT-08, NFR-EVO-01, ADR-03.
"""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import schema


def envelope(**overrides):
    """A minimal valid specification object, before any per-test damage."""
    spec = {
        "document": {
            "title": "Acme — Functional Specification Document",
            "slug": "fsd",
            "type": "Functional Specification Document (FSD)",
            "version": "1.0",
            "status": "Draft for review",
            "date": "2026-08-14",
            "owner": "Acme Engineering",
        },
        "schemaVersion": schema.SCHEMA_VERSION,
        "sections": [{"id": "requirements", "title": "Requirements", "type": "prose",
                      "body": "One paragraph."}],
    }
    spec.update(overrides)
    return spec


def messages(findings):
    return " | ".join(finding.message for finding in findings)


class TestTheEnvelopeIsRequired(unittest.TestCase):
    """M2-P1-T1-C1. A missing field is named, not merely counted."""

    def test_a_complete_envelope_passes(self):
        self.assertEqual([], schema.check_envelope(envelope()))

    def test_a_missing_owner_is_reported_by_name(self):
        spec = envelope()
        del spec["document"]["owner"]
        found = schema.check_envelope(spec)
        self.assertEqual(1, len(found))
        self.assertIn("owner", found[0].message)

    def test_every_required_field_is_reported_when_several_are_missing(self):
        """A validator that stops at the first missing field makes a reader fix
        one thing, run again, and find the next (NFR-VAL-01)."""
        spec = envelope()
        for name in ("owner", "date", "status"):
            del spec["document"][name]
        found = schema.check_envelope(spec)
        self.assertEqual(3, len(found))
        for name in ("owner", "date", "status"):
            self.assertIn(name, messages(found))

    def test_a_missing_document_block_is_one_finding_not_a_crash(self):
        found = schema.check_envelope({"schemaVersion": schema.SCHEMA_VERSION})
        self.assertTrue(found)
        self.assertIn("document", messages(found))

    def test_an_optional_field_may_be_absent(self):
        spec = envelope()
        self.assertNotIn("releaseScope", spec["document"])
        self.assertEqual([], schema.check_envelope(spec))

    def test_a_field_the_schema_does_not_name_is_allowed(self):
        """M2-02. The published set carries kicker, heroLogo and __specId, none
        of which the envelope names, and a document written against a later
        schema must stay readable by an earlier tool (NFR-EVO-02)."""
        spec = envelope()
        spec["document"]["kicker"] = "Specification"
        spec["heroLogo"] = "<svg/>"
        self.assertEqual([], schema.check_envelope(spec))


class TestTheSchemaIsVersioned(unittest.TestCase):
    """M2-P1-T1-C2 and NFR-EVO-01."""

    def test_the_schema_version_is_required(self):
        spec = envelope()
        del spec["schemaVersion"]
        found = schema.check_envelope(spec)
        self.assertEqual(1, len(found))
        self.assertIn("schemaVersion", found[0].message)

    def test_a_major_difference_is_a_failure_naming_both_versions(self):
        found = schema.check_version("2.0", "Z2S-FSD.html")
        self.assertEqual(1, len(found))
        self.assertEqual(schema.FAILURE, found[0].severity)
        self.assertIn("2.0", found[0].message)
        self.assertIn(schema.SCHEMA_VERSION, found[0].message)

    def test_a_minor_difference_is_a_warning_and_reading_continues(self):
        found = schema.check_version("1.7", "Z2S-FSD.html")
        self.assertEqual(1, len(found))
        self.assertEqual(schema.WARNING, found[0].severity)

    def test_the_same_version_says_nothing(self):
        self.assertEqual([], schema.check_version(schema.SCHEMA_VERSION, "x.html"))

    def test_an_unparseable_version_is_a_failure_rather_than_an_exception(self):
        found = schema.check_version("draft", "x.html")
        self.assertEqual(1, len(found))
        self.assertEqual(schema.FAILURE, found[0].severity)


class TestTypeSpecificSchemasComposeFromTheEnvelope(unittest.TestCase):
    """T1 refactor: a document type adds to the envelope, never repeats it."""

    def test_a_plan_needs_its_legend_and_catalogue(self):
        spec = envelope()
        spec["document"]["slug"] = "plan"
        found = schema.check_document(spec)
        self.assertIn("legend", messages(found))
        self.assertIn("catalog", messages(found))

    def test_a_plan_carrying_both_passes(self):
        spec = envelope()
        spec["document"]["slug"] = "plan"
        spec["legend"] = {"statuses": [{"id": "passing", "label": "Passing"}]}
        spec["catalog"] = {"FR-DOC-01": "Seven document types"}
        self.assertEqual([], schema.check_document(spec))

    def test_a_document_type_the_method_does_not_know_still_needs_the_envelope(self):
        """The toolchain is used on other people's projects, which will invent
        document types this method never heard of."""
        spec = envelope()
        spec["document"]["slug"] = "runbook"
        self.assertEqual([], schema.check_document(spec))
        del spec["document"]["owner"]
        self.assertIn("owner", messages(schema.check_document(spec)))

    def test_no_type_repeats_an_envelope_field(self):
        """The refactor made permanent: if a type ever re-declares a field the
        envelope already requires, the two can disagree."""
        for slug, required in schema.DOCUMENT_TYPES.items():
            overlap = set(required) & set(schema.REQUIRED_TOP_LEVEL)
            self.assertEqual(set(), overlap, "%s repeats %s" % (slug, overlap))


class TestTheIdentifierGrammar(unittest.TestCase):
    """M2-P1-T2-C1. NFR-DAT-03."""

    GOOD = ("FR-DOC-01", "NFR-ARC-03", "US-SPC-04", "US-SPC-04-S01", "ADR-16",
            "UC-04", "BC-01", "UL-25", "PRE-01",
            "NG-01", "MT-15", "RK-04",
            "M2", "M2-P1", "M2-P1-T3", "M2-P1-T3-C2")

    BAD = ("FR-DOC-1",          # ordinal not zero-padded
           "FR-doc-01",         # area not upper case
           "FR-DOCUMENTS-01",   # area too long
           "US-SPC-04-S1",      # scenario ordinal not padded
           "ADR-016",           # three digits
           "MT-7",              # a measure's ordinal not padded
           "NG-001",            # three digits
           "RK-1a",             # not a number at all
           "M2-P1-T3-C2-X1",    # a level the grammar does not define
           "M2-T3")             # a task without its phase

    def test_every_shape_the_published_set_uses_is_accepted(self):
        for identifier in self.GOOD:
            self.assertEqual([], schema.check_identifier(identifier),
                             "rejected a valid identifier: %s" % identifier)

    def test_a_malformed_identifier_fails_with_its_own_value_in_the_message(self):
        for identifier in self.BAD:
            found = schema.check_identifier(identifier)
            self.assertTrue(found, "accepted a malformed identifier: %s" % identifier)
            self.assertIn(identifier, found[0].message)

    def test_a_string_that_is_not_an_identifier_is_not_grammar_checked(self):
        """M2-03. The key `id` is overloaded: section keys and enumeration values
        use it too. A checker that treats `purpose` as a broken identifier is
        unusable, and one that treats nothing as an identifier is pointless."""
        for value in ("purpose", "risks", "Must", "auto", "needs-review", "CI"):
            self.assertIsNone(schema.kind_of(value))
            self.assertEqual([], schema.check_identifier(value))

    def test_the_kind_of_an_identifier_is_recognised(self):
        self.assertEqual("requirement", schema.kind_of("NFR-DAT-03"))
        self.assertEqual("story", schema.kind_of("US-SPC-04"))
        self.assertEqual("decision", schema.kind_of("ADR-16"))
        self.assertEqual("plan", schema.kind_of("M2-P1-T3-C2"))

    def test_identifiers_are_found_wherever_they_are_nested(self):
        spec = envelope()
        spec["sections"] = [{"id": "requirements", "type": "catalog",
                             "groups": [{"id": "FR-DOC", "entries": [
                                 {"id": "FR-DOC-1", "title": "Bad", "text": "…"}]}]}]
        found = schema.check_identifiers(spec)
        self.assertEqual(1, len(found))
        self.assertIn("FR-DOC-1", found[0].message)


class TestTheClosedEnumerations(unittest.TestCase):
    """M2-P1-T2-C2. NFR-DAT-04."""

    def test_a_priority_outside_the_set_fails_and_the_message_lists_the_set(self):
        spec = envelope()
        spec["sections"] = [{"id": "s", "entries": [
            {"id": "FR-DOC-01", "priority": "Critical", "title": "x", "text": "y"}]}]
        found = schema.check_enumerations(spec)
        self.assertEqual(1, len(found))
        self.assertIn("Critical", found[0].message)
        self.assertIn("Must", found[0].message)

    def test_every_closed_value_in_use_is_accepted(self):
        spec = envelope()
        spec["sections"] = [{"id": "s", "tasks": [
            {"id": "M2-P1-T1", "priority": "Must", "status": "needs-review",
             "autonomy": "auto-with-mock", "testLayers": ["unit", "CI"],
             "criteria": [{"id": "M2-P1-T1-C1", "kind": "human-review",
                           "text": "x", "done": False}]}]}]
        self.assertEqual([], schema.check_enumerations(spec))

    def test_a_test_layer_outside_the_set_fails(self):
        spec = envelope()
        spec["sections"] = [{"id": "s", "tasks": [
            {"id": "M2-P1-T1", "testLayers": ["unit", "telepathy"]}]}]
        self.assertIn("telepathy", messages(schema.check_enumerations(spec)))

    def test_the_envelope_status_is_free_text_not_the_task_enumeration(self):
        """`status` means two different things. On a task it is the closed run
        state; on the document it is editorial ("Draft for review")."""
        spec = envelope()
        spec["document"]["status"] = "Approved for build"
        self.assertEqual([], schema.check_enumerations(spec))

    def test_the_legend_is_generated_from_the_same_declaration(self):
        """T2 refactor. A hand-written legend drifts from the rules silently,
        and a reader trusts the legend."""
        legend = schema.legend()
        self.assertEqual(sorted(schema.ENUMS), sorted(legend))
        for name, values in schema.ENUMS.items():
            self.assertEqual([value["id"] for value in values],
                             [entry["id"] for entry in legend[name]])
            for entry in legend[name]:
                self.assertTrue(entry["label"])


class TestKindsTheMethodActuallyUses(unittest.TestCase):
    """Gaps the first run against the ten published documents exposed.

    Every case here was a false failure: the rule was incomplete, not the
    document. They are tests rather than a widened table alone, so a later
    tidy-up of the grammar cannot quietly drop one again.
    """

    def test_a_capability_a_goal_and_a_journey_are_identifiers(self):
        for identifier, kind in (("VC-03", "capability"), ("VS-01", "statement"),
                                 ("G-02", "goal"), ("J-05", "journey")):
            self.assertEqual(kind, schema.kind_of(identifier))
            self.assertEqual([], schema.check_identifier(identifier))

    def test_what_the_product_requirements_assign_is_registered_too(self):
        """M3-01. A non-goal, a measure and a risk are identifiers the PRD
        generator hands out, so they are the method's identifiers and not the
        PRD's private business. Left unregistered they are not a lighter
        contract but no contract: `kind_of` returns None, so the grammar skips
        them and the set-wide index never sees them."""
        for identifier, kind in (("NG-02", "nongoal"), ("MT-07", "measure"),
                                 ("RK-01", "risk")):
            self.assertEqual(kind, schema.kind_of(identifier))
            self.assertEqual([], schema.check_identifier(identifier))

    def test_every_registered_prefix_has_a_shape_to_be_checked_against(self):
        """A prefix registered without a grammar entry raises rather than
        reports — check_identifier indexes GRAMMAR by the kind this map
        returns."""
        for prefix in sorted(schema.PREFIXES):
            self.assertIn(schema.PREFIXES[prefix], schema.GRAMMAR,
                          "%s maps to a kind the grammar does not define" % prefix)

    def test_a_capability_trace_and_a_goal_trace_are_typed_kinds(self):
        """The Intent traces to capabilities and the PRD to goals. Neither is a
        loose key: both are declared kinds with entries to point at."""
        for kind in ("cap", "goal"):
            self.assertIn(kind, schema.TRACE_KINDS)

    def test_a_decision_status_is_its_own_closed_set(self):
        """`status` means three things in the method: a task's run state, a
        decision's standing, and the document's editorial state. Checking a
        decision against the task states rejects every accepted decision."""
        spec = envelope()
        spec["sections"] = [{"id": "decisions", "items": [
            {"id": "ADR-03", "title": "Identifiers are permanent",
             "status": "Accepted", "text": "…"}]}]
        self.assertEqual([], schema.check_enumerations(spec))

        spec["sections"][0]["items"][0]["status"] = "not-started"
        self.assertIn("not-started", messages(schema.check_enumerations(spec)))

    def test_a_task_status_is_still_the_run_state(self):
        spec = envelope()
        spec["sections"] = [{"id": "s", "tasks": [
            {"id": "M2-P1-T1", "status": "Accepted"}]}]
        self.assertIn("Accepted", messages(schema.check_enumerations(spec)))


class TestEmptyMeansAnEmptyContainer(unittest.TestCase):
    """What NFR-DAT-06 actually forbids, narrowed by the same first run.

    "A section with no content shall be absent rather than present and empty."
    A container with nothing in it renders as a heading over blank space. A
    blank string used as a value — a table's first column heading, a status
    with no colour — is a value, not an absent section, and flagging it made
    the rule fire on correct documents.
    """

    def test_a_blank_column_heading_is_a_value_not_an_empty_section(self):
        spec = envelope()
        spec["sections"] = [{"id": "matrix", "type": "table",
                             "columns": ["", "Now", "Next"],
                             "rows": [["Cost", "high", "low"]]}]
        self.assertEqual([], schema.check_emptiness(spec))

    def test_a_blank_attribute_is_a_value_too(self):
        spec = envelope()
        spec["sections"] = [{"id": "s", "type": "table", "mono": "",
                             "rows": [["a"]]}]
        self.assertEqual([], schema.check_emptiness(spec))

    def test_a_content_field_that_is_blank_is_still_a_heading_over_nothing(self):
        for key in ("body", "text", "title"):
            spec = envelope()
            spec["sections"] = [{"id": "s", "type": "prose", key: "  "}]
            self.assertIn(key, messages(schema.check_emptiness(spec)),
                          "a blank %s was not reported" % key)

    def test_a_glossary_entry_with_no_notes_omits_the_list(self):
        spec = envelope()
        spec["sections"] = [{"id": "glossary", "items": [
            {"id": "UL-01", "term": "Wave", "definition": "…", "items": []}]}]
        self.assertIn("items", messages(schema.check_emptiness(spec)))


class TestTracesAreTyped(unittest.TestCase):
    """M2-P1-T3-C1. NFR-DAT-08."""

    def entry(self, traces):
        spec = envelope()
        spec["sections"] = [{"id": "s", "entries": [
            {"id": "FR-DOC-01", "title": "x", "text": "y", "traces": traces}]}]
        return spec

    def test_a_typed_trace_map_passes(self):
        spec = self.entry({"fr": ["FR-SPC-01"], "adr": ["ADR-04"]})
        self.assertEqual([], schema.check_traces(spec))

    def test_a_flat_trace_list_is_rejected(self):
        found = schema.check_traces(self.entry(["FR-SPC-01", "ADR-04"]))
        self.assertEqual(1, len(found))
        self.assertIn("FR-DOC-01", found[0].message)

    def test_a_trace_kind_the_schema_does_not_define_is_rejected(self):
        """Free-form keys would put the consumer back to guessing from prefixes,
        which is the thing typed traces exist to stop."""
        found = schema.check_traces(self.entry({"vibes": ["FR-SPC-01"]}))
        self.assertIn("vibes", messages(found))

    def test_a_trace_value_that_is_not_a_list_of_identifiers_is_rejected(self):
        self.assertTrue(schema.check_traces(self.entry({"fr": "FR-SPC-01"})))


class TestEmptyIsAbsent(unittest.TestCase):
    """M2-P1-T3-C2. NFR-DAT-06."""

    def test_an_empty_section_container_is_rejected(self):
        spec = envelope()
        spec["sections"] = [{"id": "risks", "title": "Risks", "type": "table",
                             "rows": []}]
        found = schema.check_emptiness(spec)
        self.assertEqual(1, len(found))
        self.assertIn("rows", found[0].message)

    def test_an_empty_string_is_rejected(self):
        spec = envelope()
        spec["sections"][0]["body"] = ""
        self.assertIn("body", messages(schema.check_emptiness(spec)))

    def test_a_field_declared_able_to_be_empty_is_left_alone(self):
        """`dependsOn: []` is the honest way to say a task depends on nothing.
        Omitting it would make "no dependencies" and "not stated" the same."""
        spec = envelope()
        spec["sections"] = [{"id": "s", "tasks": [{"id": "M2-P1-T1", "dependsOn": []}]}]
        self.assertEqual([], schema.check_emptiness(spec))

    def test_false_and_zero_are_not_empty(self):
        """`done: false` is the most common value in a plan; dropping it would
        erase every unfinished criterion."""
        self.assertFalse(schema.is_empty(False))
        self.assertFalse(schema.is_empty(0))
        self.assertTrue(schema.is_empty(None))
        self.assertTrue(schema.is_empty([]))
        self.assertTrue(schema.is_empty({}))
        self.assertTrue(schema.is_empty("   "))

    def test_the_emptiness_rule_is_one_predicate(self):
        """T3 refactor: schema and renderer share one rule. This half asserts
        the checker has no second opinion of its own; the renderer's half lives
        in the runtime tests."""
        spec = envelope()
        spec["sections"] = [{"id": "s", "items": []}]
        self.assertTrue(schema.check_emptiness(spec))
        spec["sections"] = [{"id": "s", "items": [{"id": "x", "text": "y"}]}]
        self.assertEqual([], schema.check_emptiness(spec))


class TestTheDeclarationIsOneThing(unittest.TestCase):
    """Static guards, so the pieces cannot drift apart in a later change."""

    def test_the_published_documents_carry_the_declared_schema_version(self):
        """A version bump that forgets the published set is a silent break; the
        ten documents in docs/ all carry 1.0 today."""
        self.assertEqual("1.0", schema.SCHEMA_VERSION)

    def test_every_enumeration_entry_has_an_identifier_and_a_label(self):
        for name, values in schema.ENUMS.items():
            self.assertTrue(values, "%s is empty" % name)
            for value in values:
                self.assertTrue(value.get("id"))
                self.assertTrue(value.get("label"))

    def test_every_enum_bearing_field_names_a_declared_enumeration(self):
        for field, name in schema.ENUM_FIELDS.items():
            self.assertIn(name, schema.ENUMS, "%s names unknown %s" % (field, name))

    def test_a_finding_states_its_severity_its_place_and_what_is_wrong(self):
        spec = envelope()
        del spec["document"]["owner"]
        finding = schema.check_envelope(spec)[0]
        self.assertIn(finding.severity, (schema.FAILURE, schema.WARNING))
        self.assertTrue(finding.code)
        self.assertTrue(finding.where)
        self.assertTrue(finding.message)

    def test_the_specification_object_is_never_modified_by_a_check(self):
        """Checks are read-only; a validator that edits its input turns a report
        into a mutation nobody asked for."""
        spec = envelope()
        spec["sections"] = [{"id": "s", "entries": [
            {"id": "FR-DOC-1", "priority": "Critical", "traces": ["FR-SPC-01"]}]}]
        before = copy.deepcopy(spec)
        for check in (schema.check_envelope, schema.check_identifiers,
                      schema.check_enumerations, schema.check_traces,
                      schema.check_emptiness, schema.check_document,
                      schema.check_plain_language):
            check(spec)
        self.assertEqual(before, spec)


# ------------------------------------------------------------- plain language

class TestRecognisingATestPath(unittest.TestCase):
    """The one fact the plan generator and the validator both need, and neither
    can ask a project for. A heuristic, so what it knows is written down."""

    def test_the_conventions_it_claims_to_know(self):
        for path in ("tests/integration/db.test.ts", "tests/test_storage.py",
                     "src/storage/client.test.ts", "internal/store/store_test.go",
                     "spec/models/user_spec.rb", "__tests__/render.js",
                     "tests/**", "tests", "app/testing/probe.py"):
            self.assertTrue(schema.names_a_test(path), path)

    def test_ordinary_source_and_prose_are_not_tests(self):
        for path in ("src/db/schema.ts", "docker-compose.yml", "Dockerfile",
                     "docs/install.md", "src/thing/**", "", None, 7):
            self.assertFalse(schema.names_a_test(path), path)

    def test_a_word_that_merely_contains_test_is_not_a_test(self):
        """Substring matching would read `latest`, `contest` and `attestation`
        as test directories, and a check that fires on good plans is a check
        somebody switches off."""
        for path in ("src/latest.py", "src/contest/entry.py",
                     "lib/attestation/verify.go", "src/protester.ts"):
            self.assertFalse(schema.names_a_test(path), path)

    def test_the_way_out_is_a_rule_a_unit_may_be_excused_from(self):
        """A project whose layout it cannot know is not stuck with a short list
        and is not asked to rename anything."""
        self.assertIn("writes", schema.EXCUSABLE_RULES)


class TestReaderFacingProseIsReadable(unittest.TestCase):
    """M5-P2-T3-C1, M5-07, M5-08 — FR-GEN-05, NFR-UX-06."""

    def language(self, section, **kw):
        return schema.check_plain_language(envelope(sections=[section]), **kw)

    def prose(self, text):
        return {"id": "s", "type": "prose", "title": "A section", "body": text}

    def test_a_word_joined_by_underscores_is_code(self):
        self.assertEqual(["open_gate"], schema.names_internals("call open_gate first"))

    def test_a_dotted_name_being_called_is_code(self):
        self.assertEqual(["chain.require"],
                         schema.names_internals("chain.require() runs first"))

    def test_a_filename_is_code(self):
        self.assertEqual(["runtime.js"], schema.names_internals("it lives in runtime.js"))

    def test_an_ordinary_sentence_is_not(self):
        """Every false alarm turns a good sentence into an open question (M4-02)."""
        for said in ("The decision gate runs first, e.g. before any file is written.",
                     "A source register records what each source contributed.",
                     "Given, When and Then — all three, or it is not a scenario.",
                     "Version 1.0 of the schema. See section 2.1 for the rest."):
            self.assertEqual([], schema.names_internals(said), said)

    def test_a_term_is_reported_once_however_often_it_appears(self):
        found = self.language(self.prose(["We ran generate.py.", "Then generate.py."]))
        self.assertEqual(1, len(found))
        self.assertIn("named in 2 places", found[0].message)

    def test_the_report_names_the_first_place_it_appears(self):
        """The refactor this rule asked for: the first occurrence, not the last
        and not all of them. A reader fixes the first and finds the rest."""
        found = self.language({"id": "s", "type": "prose", "title": "A section",
                               "body": ["Nothing here.", "But check_gate here.",
                                        "And check_gate here as well."]})
        self.assertEqual(1, len(found))
        self.assertIn("body[1]", found[0].where)
        self.assertNotIn("body[2]", found[0].where)

    def test_a_finding_is_a_warning_and_never_a_failure(self):
        """M5-08: plain language is a Should in both documents that ask for it, and
        a Should that turns a build red is a Must by the back door (FR-VAL-06)."""
        found = self.language(self.prose(["It reads from settings_file."]))
        self.assertTrue(found)
        for finding in found:
            self.assertEqual(schema.WARNING, finding.severity)

    def test_a_project_can_silence_a_term_it_uses_everywhere(self):
        section = self.prose(["The report is written to summary.md."])
        self.assertTrue(self.language(section))
        self.assertEqual([], self.language(section, allowed=["summary.md"]))

    def test_a_product_name_in_reader_facing_prose_is_flagged_too(self):
        found = self.language(self.prose(["Everything is stored in PostgreSQL."]))
        self.assertEqual(1, len(found))
        self.assertIn("PostgreSQL", found[0].message)

    def test_a_sample_of_a_specification_is_quoted_material_not_prose(self):
        """A code sample is meant to name files and call functions; that is what
        a sample is."""
        self.assertEqual([], self.language(
            {"id": "s", "type": "code", "title": "A sample",
             "body": '{"id": "UC-01"}  // see generate.py'}))

    def test_a_value_is_not_prose(self):
        """An identifier, an area key and a priority band are values, and a rule
        about how prose reads has nothing to say about any of them."""
        self.assertEqual([], self.language(
            {"id": "requirements", "type": "requirements", "title": "Requirements",
             "areas": [{"key": "FR-DOC", "name": "Documents"}],
             "items": [{"id": "FR-DOC-01", "area": "FR-DOC", "priority": "Must",
                        "title": "A requirement", "text": "It shall do the thing."}]}))


if __name__ == "__main__":
    unittest.main()
