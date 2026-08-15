# -*- coding: utf-8 -*-
"""Forward-only updates (M13-P2-T2).

M13-P2-T2-C1 is one sentence — no update path deletes or overwrites published
content — and it is a claim about every path, not about the two that are meant
to be safe. So the tests below check the original text survives each operation
byte for byte, and that the one operation an operator will certainly ask for is
refused by name rather than being absent.

Traces: FR-SKL-06, FR-AMD-01, FR-AMD-04, NFR-EVO-03, ADR-12, US-SKL-04.
"""

import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from z2s import chain, document, paths, status, update, writer

from tests.test_validate import spec

ORIGINAL = "The system shall refuse to run when its upstream document is absent."


def entry(identifier="FR-DOC-01", **extra):
    made = {"id": identifier, "title": "Prerequisite enforcement",
            "text": ORIGINAL, "priority": "Must"}
    made.update(extra)
    return made


def catalogue(*entries):
    """A document carrying a requirements catalogue, the way the FSD does."""
    made = spec(slug="fsd")
    made["sections"] = [{"id": "requirements", "type": "requirements",
                         "title": "Requirements", "items": list(entries)}]
    return made


class Project(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="z2s-update-")
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)
        paths.ensure_layout(self.folder)
        self.place(catalogue(entry()))

    def place(self, made, filename="FSD.html"):
        self.path = paths.resolve(self.folder, paths.SPECS_DIR, filename)
        writer.write(self.path, document.render(made, "fsd-spec"))
        return self.path

    def held(self):
        _, found = status.read(self.path)
        return found["sections"][0]["items"][0]

    def invoke(self, *argv):
        out = io.StringIO()
        code = update.main(list(argv) + ["--root", self.folder], out)
        return code, out.getvalue()


class TestAmending(Project):
    """The entry is still scope, and something about it changed."""

    def test_the_original_text_survives_word_for_word(self):
        update.amend(self.folder, "FR-DOC-01", "Widened to cover addenda.",
                     "2026-08-15")
        self.assertEqual(ORIGINAL, self.held()["text"])

    def test_the_amendment_is_recorded_with_its_date(self):
        update.amend(self.folder, "FR-DOC-01", "Widened to cover addenda.",
                     "2026-08-15")
        self.assertEqual([{"date": "2026-08-15",
                           "text": "Widened to cover addenda."}],
                         self.held()["amendments"])

    def test_amendments_accumulate_rather_than_replace(self):
        """The second change does not erase the record of the first; the
        history of a specification is part of the specification."""
        update.amend(self.folder, "FR-DOC-01", "First change.", "2026-08-15")
        update.amend(self.folder, "FR-DOC-01", "Second change.", "2026-08-16")
        self.assertEqual(["First change.", "Second change."],
                         [one["text"] for one in self.held()["amendments"]])

    def test_an_amendment_with_no_date_is_refused_in_its_own_words(self):
        """This module has no clock, by the same rule every other module here
        follows, and an undated amendment cannot be placed against the decision
        that caused it.

        The exact wording is asserted, not merely that something was refused.
        The renderer would also reject an undated amendment, further down and
        after the entry had been read and changed in memory — so a test that
        only checked "it refused" would pass with this guard removed, and the
        operator would get the renderer's message about a document instead of a
        plain sentence about the thing they just typed.
        """
        for missing in (None, "", "   "):
            with self.assertRaises(update.Refused) as caught:
                update.amend(self.folder, "FR-DOC-01", "Something changed.",
                             missing)
            self.assertEqual("an amendment states no date; nothing was written",
                             str(caught.exception))

    def test_the_date_is_refused_before_the_document_is_even_opened(self):
        """Which is why the message can be that plain: at that point nothing has
        been located, read or changed."""
        with self.assertRaises(update.Refused) as caught:
            update.amend(self.folder, "FR-DOC-99", "Something changed.", None)
        self.assertIn("no date", str(caught.exception))
        self.assertNotIn("FR-DOC-99", str(caught.exception))

    def test_an_amendment_with_no_text_is_refused(self):
        with self.assertRaises(update.Refused):
            update.amend(self.folder, "FR-DOC-01", "", "2026-08-15")

    def test_a_refused_amendment_leaves_the_document_untouched(self):
        with open(self.path, "rb") as handle:
            before = handle.read()
        with self.assertRaises(update.Refused):
            update.amend(self.folder, "FR-DOC-01", "Something.", None)
        with open(self.path, "rb") as handle:
            self.assertEqual(before, handle.read())

    def test_what_is_written_is_what_regeneration_would_produce(self):
        """The splice reuses the generators' own serialiser, so an edited
        document and a regenerated one are the same bytes."""
        update.amend(self.folder, "FR-DOC-01", "Widened.", "2026-08-15")
        with open(self.path, encoding="utf-8") as handle:
            edited = handle.read()
        _, found = status.read(self.path)
        self.assertEqual(edited, document.render(found, "fsd-spec"))

    def test_an_amendment_the_renderer_would_refuse_is_refused_first(self):
        """Otherwise it reaches the reader as a generation failure rather than
        as a note."""
        self.place(catalogue(entry(amendments=[{"text": "undated"}])))
        with self.assertRaises(update.Refused):
            update.amend(self.folder, "FR-DOC-01", "Another.", "2026-08-15")


class TestRetiring(Project):
    """The entry is no longer scope. It stays; its number stays reserved."""

    def test_the_entry_is_not_removed(self):
        update.retire(self.folder, "FR-DOC-01", "Superseded by the addendum.")
        self.assertEqual(ORIGINAL, self.held()["text"])
        self.assertEqual("FR-DOC-01", self.held()["id"])

    def test_the_reason_is_recorded_where_the_trace_engine_reads_it(self):
        """Spelled as the field that module already reads, so a retirement this
        module writes is a retirement that module reports."""
        update.retire(self.folder, "FR-DOC-01", "Superseded.")
        self.assertEqual("Superseded.", self.held()[update.RETIRED])

    def test_a_successor_is_recorded_as_a_link_not_a_sentence(self):
        update.retire(self.folder, "FR-DOC-01", "Superseded.", "FR-DOC-14")
        self.assertEqual("FR-DOC-14", self.held()[update.SUCCESSOR])

    def test_retiring_with_no_reason_is_refused(self):
        """A withdrawn requirement with no reason is indistinguishable from one
        that was lost."""
        with self.assertRaises(update.Refused) as caught:
            update.retire(self.folder, "FR-DOC-01", "")
        self.assertIn("reason", str(caught.exception))

    def test_retiring_something_already_retired_is_refused(self):
        update.retire(self.folder, "FR-DOC-01", "Superseded.")
        with self.assertRaises(update.Refused):
            update.retire(self.folder, "FR-DOC-01", "Superseded again.")


class TestNothingIsEverRemoved(Project):
    """M13-P2-T2-C1, stated as the claim it actually is."""

    def test_deleting_is_refused_by_name_rather_than_being_absent(self):
        """An operator will ask. A command that does not exist teaches them
        nothing; one that refuses tells them what to do instead."""
        code, said = self.invoke("delete", "FR-DOC-01")
        self.assertEqual(1, code)
        self.assertIn("retire", said)
        self.assertIn("FR-DOC-01", said)

    def test_every_spelling_of_removal_is_refused(self):
        for word in ("delete", "remove", "drop"):
            code, said = self.invoke(word, "FR-DOC-01")
            self.assertEqual(1, code, word)
            self.assertIn("retire", said)

    def test_a_refused_removal_changes_nothing(self):
        with open(self.path, "rb") as handle:
            before = handle.read()
        self.invoke("delete", "FR-DOC-01")
        with open(self.path, "rb") as handle:
            self.assertEqual(before, handle.read())

    def test_no_path_through_the_module_shortens_the_entry_list(self):
        """The claim is about every path, not the two that are meant to be
        safe. Both operations run, and the catalogue is the same length."""
        update.amend(self.folder, "FR-DOC-01", "Changed.", "2026-08-15")
        update.retire(self.folder, "FR-DOC-01", "Then withdrawn.")
        _, found = status.read(self.path)
        self.assertEqual(1, len(found["sections"][0]["items"]))


class TestFindingTheEntry(Project):

    def test_an_unknown_identifier_refuses_and_says_where_it_looked(self):
        code, said = self.invoke("amend", "FR-DOC-99", "Changed.",
                                 "--date", "2026-08-15")
        self.assertEqual(1, code)
        self.assertIn("FR-DOC-99", said)
        self.assertIn(paths.ROOT, said)

    def test_an_identifier_in_two_documents_is_a_collision_not_an_edit(self):
        """Amending one of two would leave the other saying something else, and
        a reader has no way to tell which they are holding."""
        writer.write(paths.resolve(self.folder, paths.SPECS_DIR, "SDD.html"),
                     document.render(catalogue(entry()), "fsd-spec"))
        with self.assertRaises(update.Refused) as caught:
            update.amend(self.folder, "FR-DOC-01", "Changed.", "2026-08-15")
        self.assertIn("more than one document", str(caught.exception))

    def test_the_command_explains_itself_when_given_nothing(self):
        code, said = self.invoke()
        self.assertEqual(2, code)
        self.assertIn("never deleted", said)


if __name__ == "__main__":
    unittest.main()
