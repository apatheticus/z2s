# -*- coding: utf-8 -*-
"""M4-P2 — catalogue interaction.

Covers criteria:
  M4-P2-T1-C1  Filtering matches identifier, title, body and tags.
  M4-P2-T1-C2  A no-match state is stated explicitly.
  M4-P2-T1-C3  Filtering five hundred entries completes within one animation
               frame.
  M4-P2-T2-C1  Keyword and priority filters compose.
  M4-P2-T2-C2  Each band shows its entry count.
  M4-P2-T3-C1  A deep link expands its container and marks the entry.
  M4-P2-T3-C2  Expand-all and collapse-all affect every group.
  M4-P2-T4-C1  Marks and progress survive a reload.
  M4-P2-T4-C2  Reset clears both.

Almost all of it needs a real browser. Whether a reader can see an entry inside
a closed group is not a question about `display`; storage needs a real origin;
and a frame budget needs a real clock. The two checks that do not — what a
keyword is matched against, and which bands a document has — run under Node
with the rest of the runtime's pure half.

The browser module is skipped, loudly, when no browser is installed. A skipped
check is never counted as a pass (LD-04, FR-GEN-03, NFR-VAL-05).

Locked decisions this file holds to (M4-P2, 2026-08-14): the controls sit in one
pinned toolbar (M4-03); band counts follow the keyword rather than the document
total (M4-04); entries and sections are one review pool with one figure (M4-05);
whole areas fold and load open (M4-06, FR-SPC-10).

Traces: FR-SPC-05, FR-SPC-06, FR-SPC-07, FR-SPC-08, FR-SPC-10, NFR-PRF-03.
"""

import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from z2s import document, runtime, shell, styles, tokens

NODE = shutil.which("node")
RENDER_HARNESS = os.path.join(HERE, "render_harness.js")
HARNESS = os.path.join(HERE, "catalogue_harness.js")

#: One animation frame at 60Hz. The budget NFR-PRF-03 states, in milliseconds.
FRAME = 16.0

AREAS = [{"key": "FR-DOC", "name": "Document chain",
          "description": "How a document is produced and refused."},
         {"key": "FR-CTX", "name": "Vocabulary"}]

ENTRIES = [
    {"id": "FR-DOC-01", "area": "FR-DOC", "priority": "Must",
     "title": "Chain refusal",
     "text": "The generator shall refuse to run without its prerequisite.",
     "tags": ["gate"]},
    {"id": "FR-DOC-02", "area": "FR-DOC", "priority": "Should",
     "title": "Gap recording",
     "text": "An unusable statement shall become an open question.",
     "notes": "Sifted, never silently dropped.",
     "tags": ["provenance"]},
    {"id": "FR-CTX-01", "area": "FR-CTX", "priority": "Must",
     "title": "Canonical terms",
     "text": "Every term shall cite the intent that introduced it.",
     "tags": ["glossary"]},
    {"id": "FR-CTX-02", "area": "FR-CTX", "priority": "Won't",
     "title": "Automatic translation",
     "text": "The toolchain shall not translate a specification.",
     "notes": "Excluded: no reviewer could check the result.",
     "tags": ["excluded"]},
]

SPEC = {
    "document": {"title": "Interaction Specimen", "kicker": "Specification",
                 "slug": "interaction", "type": "FSD", "version": "1.0",
                 "status": "Draft", "date": "2026-08-14", "owner": "The toolchain",
                 "summary": "A catalogue small enough to read and large enough to filter."},
    "sections": [
        {"id": "purpose", "title": "Purpose", "type": "prose",
         "body": ["Why this document exists."]},
        {"id": "requirements", "title": "Requirements catalogue",
         "type": "requirements", "areas": AREAS, "items": ENTRIES},
    ],
}

#: Every tickable thing: two sections and four entries, one pool (M4-05).
POOL = 6

#: The size NFR-PRF-03 names. Ten areas so the group tally is exercised too.
BULK_AREAS = ["FR-DOC", "FR-CTX", "FR-GEN", "FR-SPC", "FR-TRC",
              "FR-VAL", "FR-PLN", "FR-COV", "FR-CHN", "FR-OUT"]
BULK_BANDS = ["Must", "Should", "Could", "Won't"]


def bulk_spec(per_area=50):
    """Five hundred entries, half of which carry the word the test filters on."""
    items = []
    for area in BULK_AREAS:
        for number in range(1, per_area + 1):
            index = len(items)
            items.append({
                "id": "%s-%02d" % (area, number),
                "area": area,
                "priority": BULK_BANDS[index % len(BULK_BANDS)],
                "title": "Requirement %d" % (index + 1),
                "text": ("The toolchain shall keep the register up to date."
                         if index % 2 else
                         "The toolchain shall report what it could not place."),
                "tags": ["generated"],
            })
    return {
        "document": dict(SPEC["document"], title="Bulk Specimen", slug="bulk"),
        "sections": [{"id": "requirements", "title": "Requirements catalogue",
                      "type": "requirements",
                      "areas": [{"key": key, "name": key} for key in BULK_AREAS],
                      "items": items}],
    }


def assemble(spec):
    return shell.assemble(
        spec_id="spec", spec_json=document.serialise(spec),
        title=spec["document"]["title"], description=spec["document"]["summary"],
        tokens=tokens.render(tokens.NEUTRAL), struct=styles.STRUCT,
        runtime=runtime.SOURCE)


def call(op, **payload):
    """One operation through the runtime's pure half, under Node."""
    payload["op"] = op
    finished = subprocess.run([NODE, RENDER_HARNESS], input=json.dumps(payload),
                              capture_output=True, text=True)
    if finished.returncode != 0:
        raise AssertionError("runtime harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout)


REQUEST = {
    "op": "catalogue",
    "words": {"identifier": "FR-CTX-02", "title": "canonical",
              "body": "prerequisite", "tags": "glossary", "notes": "sifted"},
    "narrow": "prerequisite",
    "absent": "zzzznothing",
    "shared": "shall",
    "band": "Must",
    "target": "FR-CTX-01",
    "tick": ["FR-DOC-01", "purpose"],
    "bulkWord": "register",
}


def run_catalogue():
    """Drive the browser once and share the result across every check here."""
    request = dict(REQUEST, html=assemble(SPEC), bulk=assemble(bulk_spec()))
    finished = subprocess.run([NODE, HARNESS], input=json.dumps(request),
                              capture_output=True, text=True)
    if finished.returncode == 3:
        return None, finished.stderr.strip()
    if finished.returncode != 0:
        raise AssertionError("catalogue harness failed:\n" + finished.stderr)
    return json.loads(finished.stdout), None


SEEN, REASON = ((None, "node is not installed") if NODE is None else run_catalogue())


@unittest.skipIf(NODE is None, "node is not installed; the runtime cannot be exercised")
class RuntimeTest(unittest.TestCase):
    pass


@unittest.skipIf(SEEN is None, "no browser available: %s" % REASON)
class BrowserTest(unittest.TestCase):
    """Base: every check below reads the one browser run."""

    @classmethod
    def setUpClass(cls):
        cls.seen = SEEN


class TestWhatAKeywordIsMatchedAgainst(RuntimeTest):
    """M4-P2-T1-C1, without a browser: the string, before anything reads it."""

    def searchable(self, item):
        return call("catalogue", item=item)["searchable"]

    def test_every_field_a_reader_would_search_is_in_it(self):
        found = self.searchable(ENTRIES[1])
        for expected in ("fr-doc-02", "gap recording", "open question",
                         "sifted", "provenance"):
            self.assertIn(expected, found)

    def test_it_is_folded_once_rather_than_at_every_keystroke(self):
        """NFR-PRF-03 refactor. Lower case here means no case work per key."""
        self.assertEqual(self.searchable(ENTRIES[0]).lower(),
                         self.searchable(ENTRIES[0]))

    def test_an_entry_with_nothing_but_an_identifier_still_matches_on_it(self):
        self.assertEqual("fr-doc-09", self.searchable({"id": "FR-DOC-09"}))

    def test_absent_fields_leave_no_gaps_to_match_by_accident(self):
        """Joining undefined fields would make every entry match 'undefined'."""
        self.assertNotIn("undefined", self.searchable({"id": "FR-DOC-09"}))


class TestTheBandsAToolbarOffers(RuntimeTest):
    """M4-P2-T2-C2, the half that needs no browser."""

    def test_only_the_bands_the_document_actually_uses_are_offered(self):
        self.assertEqual(["Must", "Should", "Won't"],
                         call("catalogue", spec=SPEC)["bands"])

    def test_bands_are_offered_in_the_order_a_reader_thinks_about_them(self):
        shuffled = {"sections": [dict(SPEC["sections"][1],
                                      items=list(reversed(ENTRIES)))]}
        self.assertEqual(["Must", "Should", "Won't"],
                         call("catalogue", spec=shuffled)["bands"])

    def test_a_band_this_runtime_has_never_heard_of_is_still_offered(self):
        """NFR-EVO-02 — a later vocabulary is still the document's vocabulary."""
        invented = {"sections": [dict(SPEC["sections"][1], items=[
            dict(ENTRIES[0], priority="Must"),
            dict(ENTRIES[1], priority="Someday")])]}
        self.assertEqual(["Must", "Someday"], call("catalogue", spec=invented)["bands"])

    def test_a_document_with_no_catalogue_gets_no_toolbar(self):
        """A pinned bar controlling nothing is chrome for its own sake."""
        prose = {"sections": [SPEC["sections"][0]]}
        self.assertEqual("", call("catalogue", spec=prose)["toolbar"])

    def test_a_document_with_a_catalogue_gets_one(self):
        toolbar = call("catalogue", spec=SPEC)["toolbar"]
        self.assertIn("data-filter", toolbar)
        self.assertIn('data-band="Must"', toolbar)
        self.assertIn("data-expand", toolbar)
        self.assertIn("data-collapse", toolbar)


class TestVisibilityIsOnePredicate(RuntimeTest):
    """M4-P2-T2-T1 refactor: both filters read one rule, so a third is a clause
    rather than another pass over the entries."""

    def shows(self, *cases):
        return call("catalogue", cases=list(cases))["shows"]

    def test_the_two_filters_are_applied_together(self):
        entry = {"text": "the register of sources", "band": "Must"}
        self.assertEqual(
            [True, False, False, False],
            self.shows({"entry": entry, "keyword": "register", "off": {}},
                       {"entry": entry, "keyword": "register", "off": {"Must": True}},
                       {"entry": entry, "keyword": "absent", "off": {}},
                       {"entry": entry, "keyword": "absent", "off": {"Must": True}}))

    def test_an_empty_keyword_hides_nothing(self):
        self.assertEqual([True], self.shows(
            {"entry": {"text": "anything", "band": "Could"}, "keyword": "", "off": {}}))


class TestTheReviewPool(RuntimeTest):
    """M4-05 — one pool, so one figure covers the whole document."""

    def test_sections_and_entries_are_both_tickable(self):
        pool = call("catalogue", spec=SPEC)["reviewable"]
        self.assertEqual(["purpose", "requirements", "FR-DOC-01", "FR-DOC-02",
                          "FR-CTX-01", "FR-CTX-02"], pool)

    def test_a_document_with_no_catalogue_keeps_its_review_tracking(self):
        prose = {"sections": [SPEC["sections"][0]]}
        self.assertEqual(["purpose"], call("catalogue", spec=prose)["reviewable"])


class TestTheKeywordFilter(BrowserTest):
    """M4-P2-T1-C1, M4-P2-T1-C2 / FR-SPC-05."""

    def test_the_catalogue_starts_whole(self):
        self.assertEqual(["FR-DOC-01", "FR-DOC-02", "FR-CTX-01", "FR-CTX-02"],
                         self.seen["initial"]["visible"])

    def test_every_group_is_open_on_arrival(self):
        """FR-SPC-10 — the default state reveals content."""
        self.assertTrue(all(group["open"] for group in self.seen["initial"]["groups"]))

    def test_it_matches_the_identifier(self):
        self.assertEqual(["FR-CTX-02"], self.seen["fields"]["identifier"])

    def test_it_matches_the_title(self):
        self.assertEqual(["FR-CTX-01"], self.seen["fields"]["title"])

    def test_it_matches_the_body(self):
        self.assertEqual(["FR-DOC-01"], self.seen["fields"]["body"])

    def test_it_matches_the_tags(self):
        self.assertEqual(["FR-CTX-01"], self.seen["fields"]["tags"])

    def test_it_matches_the_notes(self):
        """Not in the criterion, but a note is where an exclusion states its
        reason; a filter that could not reach one would hide the answer."""
        self.assertEqual(["FR-DOC-02"], self.seen["fields"]["notes"])

    def test_a_group_that_loses_every_entry_leaves_the_page(self):
        groups = {group["area"]: group for group in self.seen["narrowed"]["groups"]}
        self.assertTrue(groups["FR-DOC"]["shown"])
        self.assertFalse(groups["FR-CTX"]["shown"],
                         "an empty group stayed on the page as a bare heading")

    def test_a_filter_matching_nothing_says_so(self):
        """M4-P2-T1-C2 — an empty page is not an answer."""
        self.assertEqual([], self.seen["nothing"]["visible"])
        stated = [one for one in self.seen["nothing"]["noMatch"] if one["shown"]]
        self.assertEqual(1, len(stated))
        self.assertIn("Nothing in this catalogue matches", stated[0]["text"])

    def test_the_message_is_absent_while_anything_matches(self):
        """Otherwise it would pass by always being on the page."""
        for state in ("initial", "narrowed"):
            with self.subTest(state=state):
                self.assertEqual([], [one for one in self.seen[state]["noMatch"]
                                      if one["shown"]])


class TestThePriorityBands(BrowserTest):
    """M4-P2-T2-C1, M4-P2-T2-C2 / FR-SPC-07."""

    def test_each_band_shows_a_count(self):
        self.assertEqual({"Must": "2", "Should": "1", "Won't": "1"},
                         self.seen["initial"]["counts"])

    def test_the_counts_follow_the_keyword(self):
        """M4-04 — the count answers what is matching now, not what the document
        holds in total."""
        self.assertEqual({"Must": "1", "Should": "0", "Won't": "0"},
                         self.seen["narrowed"]["counts"])

    def test_keyword_and_band_compose(self):
        """M4-P2-T2-C1 — only what matches both survives."""
        self.assertEqual(["FR-DOC-01", "FR-DOC-02", "FR-CTX-01", "FR-CTX-02"],
                         self.seen["sharedOnly"])
        self.assertEqual(["FR-DOC-02", "FR-CTX-02"], self.seen["composed"]["visible"])

    def test_switching_a_band_off_does_not_zero_its_own_count(self):
        """The count is the one number that says what switching it back on would
        bring; zeroing it strands the reader (M4-04)."""
        self.assertEqual("2", self.seen["composed"]["counts"]["Must"])


class TestFolding(BrowserTest):
    """M4-P2-T3-C2 / FR-SPC-10."""

    def test_collapse_all_folds_every_group(self):
        self.assertEqual([], [group for group in self.seen["collapsed"]["groups"]
                              if group["open"]])

    def test_a_folded_group_hides_its_entries(self):
        """The pair is what proves the fold did the work rather than the entries
        having gone somewhere else."""
        self.assertEqual([], self.seen["collapsed"]["visible"])

    def test_expand_all_opens_every_group(self):
        self.assertEqual([], [group for group in self.seen["expanded"]["groups"]
                              if not group["open"]])
        self.assertEqual(4, len(self.seen["expanded"]["visible"]))


class TestDeepLinks(BrowserTest):
    """M4-P2-T3-C1 / FR-SPC-06."""

    def test_following_a_link_finds_the_entry(self):
        self.assertTrue(self.seen["deepLink"]["found"])

    def test_the_routine_that_opens_a_fold_opens_it(self):
        """Asked of the routine on its own. Chromium expands a group around a
        fragment target by itself, so the whole-journey check below passes
        whether or not the runtime does anything — this is the one that fails
        if the runtime stops opening folds."""
        self.assertTrue(self.seen["revealed"]["groupOpen"])

    def test_opening_one_fold_leaves_the_others_folded(self):
        self.assertEqual(["FR-DOC"], self.seen["revealed"]["stillFolded"])

    def test_it_opens_the_group_the_entry_was_folded_inside(self):
        self.assertTrue(self.seen["deepLink"]["groupOpen"])
        self.assertTrue(self.seen["deepLink"]["visible"])

    def test_it_opens_only_that_group(self):
        """Without this the check would pass on a runtime that gave up and
        expanded the whole document."""
        self.assertEqual(["FR-DOC"], self.seen["stillFolded"])

    def test_it_marks_the_entry(self):
        self.assertTrue(self.seen["deepLink"]["marked"])

    def test_it_brings_the_entry_on_screen(self):
        self.assertTrue(self.seen["deepLink"]["onScreen"])


class TestReviewTracking(BrowserTest):
    """M4-P2-T4-C1, M4-P2-T4-C2 / FR-SPC-08."""

    def test_an_entry_can_be_ticked(self):
        self.assertEqual("2 of %d reviewed" % POOL, self.seen["ticked"]["progress"])

    def test_the_marks_survive_a_reload(self):
        """M4-P2-T4-C1"""
        self.assertEqual(["purpose", "FR-DOC-01"],
                         sorted(self.seen["reloaded"]["checked"], reverse=True))

    def test_the_progress_survives_a_reload(self):
        self.assertEqual("2 of %d reviewed" % POOL, self.seen["reloaded"]["progress"])

    def test_reset_clears_the_marks(self):
        """M4-P2-T4-C2"""
        self.assertEqual([], self.seen["reset"]["checked"])

    def test_reset_clears_the_progress(self):
        self.assertEqual("0 of %d reviewed" % POOL, self.seen["reset"]["progress"])

    def test_reset_reaches_the_stored_state_not_only_the_screen(self):
        """A reset that only unticked the boxes would come back on reload."""
        self.assertEqual(0, self.seen["afterReset"])


class TestTheFrameBudget(BrowserTest):
    """M4-P2-T1-C3 / NFR-PRF-03."""

    def test_the_specimen_really_is_the_stated_size(self):
        """A frame budget met over fifty entries is not the claim."""
        self.assertEqual(500, self.seen["bulk"]["entries"])

    def test_the_filter_actually_narrowed_something(self):
        """Timing a filter that matched everything measures nothing."""
        self.assertEqual(250, self.seen["bulk"]["matched"])

    def test_filtering_five_hundred_entries_stays_within_one_frame(self):
        self.assertLessEqual(
            self.seen["bulk"]["worst"], FRAME,
            "the slowest of %d keystrokes took %.2fms against a %.0fms frame"
            % (len(self.seen["bulk"]["runs"]), self.seen["bulk"]["worst"], FRAME))


if __name__ == "__main__":
    unittest.main(verbosity=2)
