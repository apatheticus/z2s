# -*- coding: utf-8 -*-
"""The context generator: what it refuses, what it asks, and what it hands on.

Four claims are load-bearing here, each checked against the thing that would
actually break rather than against a description of it:

  · without a completed vision the generator refuses, names what is missing and
    leaves the project untouched (FR-CTX-01, US-CTX-01-S01)
  · every glossary term is traceable to the vision or one of its registered
    sources, carries exactly one definition, and names one canonical word;
    a term that cannot be sourced becomes an open question, not an entry
    (FR-CTX-02, US-CTX-01-S02, US-CTX-01-S03)
  · a word carrying two meanings is asked about, never decided silently, and
    when the answer is to scope it the entry states both meanings and the
    context map shows the boundary it crosses (FR-CTX-03, FR-CTX-04, FR-CTX-06)
  · a downstream document speaks the language: retired synonyms are replaced by
    the canonical term, and a term the glossary lacks is added to the context
    document rather than defined where it was needed (FR-CTX-05, US-CTX-03)

Traces: FR-CTX-01, FR-CTX-02, FR-CTX-03, FR-CTX-04, FR-CTX-05, FR-CTX-06,
NFR-DAT-03, NFR-DAT-06, NFR-GEN-01, US-CTX-01, US-CTX-02, US-CTX-03.
"""

import ast
import copy
import inspect
import os
import re
import shutil
import tempfile
import unittest

from z2s import chain, context, gate, paths, schema, validate, vision

#: Anything that could read the clock, which would make two runs of unchanged
#: input differ (NFR-GEN-01).
CLOCK = ("time", "datetime", "calendar", "random", "uuid")


def imports(source):
    """Every module name a source file imports, wherever the import sits."""
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split(".")[0])
            found.update(alias.name for alias in node.names)
    return found


# ------------------------------------------------------------------ fixtures

def vision_brief(**extra):
    made = {"title": "Kestrel", "owner": "A. Owner", "date": "2026-08-14",
            "statement": "Every document in one voice.",
            "capabilities": [{"title": "Record a source", "body": "Keep what was consulted."}],
            "sources": [{"kind": "narrative", "name": "Kick-off conversation",
                         "origin": "Recorded 2026-08-01",
                         "contributed": "The problem and the vocabulary."}]}
    made.update(extra)
    return made


def context_brief(**extra):
    made = {"title": "Kestrel — the domain", "owner": "A. Owner", "date": "2026-08-14",
            "overview": "What the words in this project mean.",
            "contexts": [{"name": "Authoring", "body": "Where documents are written.",
                          "feeds": ["Validation"]},
                         {"name": "Validation", "body": "Where documents are checked."}],
            "terms": [{"term": "Brief", "definition": "The material a generator is handed.",
                       "source": "Kick-off conversation", "context": "Authoring",
                       "synonyms": ["input pack"]},
                      {"term": "Gate", "definition": "The one phase in which forks are closed.",
                       "source": "the vision", "context": "Authoring"}],
            "sources": [{"kind": "narrative", "name": "Kick-off conversation",
                         "origin": "Recorded 2026-08-01",
                         "contributed": "The vocabulary."}]}
    made.update(extra)
    return made


def closed(run, **answers):
    """Close every open fork, taking the recommendation where the test is silent."""
    while True:
        question = run.question()
        if question is None:
            return run
        run.answer(question.id, answers.get(question.id, question.recommended.id),
                   "Chosen by the test.")


def gate_for(brief, **answers):
    return closed(gate.Gate(context.SLUG, context.forks(brief), source=brief), **answers)


def sections(spec):
    return dict((section["id"], section) for section in spec["sections"])


def terms_of(spec):
    """The glossary entries, by canonical word."""
    found = sections(spec).get("glossary")
    return dict((item["canonical"], item) for item in found["items"]) if found else {}


def strings(node):
    """Every string anywhere in a specification object."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key in sorted(node):
            for found in strings(node[key]):
                yield found
    elif isinstance(node, list):
        for item in node:
            for found in strings(item):
                yield found


class Sandbox(unittest.TestCase):
    """A project root that starts genuinely empty."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-context-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def author_vision(self, **extra):
        run = gate.Gate(vision.SLUG, vision.FORKS, source=vision_brief(**extra))
        closed(run)
        return vision.author(self.root, vision_brief(**extra), run)[0]

    def generate(self, brief=None, **answers):
        made = context_brief() if brief is None else brief
        return context.generate(made, gate_for(made, **answers), self.root)


# ------------------------------------------------------- the document above

class TestTheVisionComesFirst(Sandbox):
    """M3-P4-T1-C1: without a completed vision the generator refuses."""

    def test_an_empty_project_is_refused_by_name(self):
        with self.assertRaises(chain.MissingPrerequisite) as caught:
            self.generate()
        said = str(caught.exception)
        self.assertIn("vision", said)
        self.assertIn(vision.FILENAME, said)

    def test_the_refusal_writes_nothing(self):
        brief = context_brief()
        with self.assertRaises(chain.MissingPrerequisite):
            context.author(self.root, brief, gate_for(brief))
        self.assertEqual(os.listdir(self.root), [])

    def test_a_document_of_the_wrong_kind_is_not_a_vision(self):
        target = paths.resolve(self.root, paths.SPECS_DIR, vision.FILENAME)
        os.makedirs(os.path.dirname(target))
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("<script type=\"application/json\">"
                         "{\"document\": {\"slug\": \"prd\"}}</script>")
        with self.assertRaises(chain.MissingPrerequisite) as caught:
            self.generate()
        self.assertIn("prd", str(caught.exception))

    def test_a_document_with_no_specification_is_refused(self):
        target = paths.resolve(self.root, paths.SPECS_DIR, vision.FILENAME)
        os.makedirs(os.path.dirname(target))
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("<html><body>a vision, allegedly</body></html>")
        with self.assertRaises(chain.MissingPrerequisite):
            self.generate()

    def test_the_gate_refuses_before_the_vision_is_looked_for(self):
        # An open fork stops the run whatever else is wrong, so a half-answered
        # project cannot be told its problem is a missing file.
        brief = context_brief()
        run = gate.Gate(context.SLUG, context.forks(brief), source=brief)
        with self.assertRaises(gate.GateNotClosed):
            context.generate(brief, run, self.root)

    def test_a_completed_vision_is_enough(self):
        self.author_vision()
        spec = self.generate()
        self.assertEqual(spec["document"]["slug"], context.SLUG)


# ------------------------------------------------------------- the glossary

class TestEveryTermIsSourced(Sandbox):
    """M3-P4-T1-C2: one definition, one recorded source, no invention."""

    def setUp(self):
        Sandbox.setUp(self)
        self.author_vision()

    def test_a_term_from_a_registered_source_is_an_entry(self):
        self.assertIn("Brief", terms_of(self.generate()))

    def test_a_term_naming_the_vision_is_an_entry(self):
        self.assertIn("Gate", terms_of(self.generate()))

    def test_a_term_naming_a_capability_is_an_entry(self):
        brief = context_brief(terms=[{"term": "Source", "definition": "Material consulted.",
                                      "source": "VC-01", "context": "Authoring"}])
        self.assertIn("Source", terms_of(self.generate(brief)))

    def test_a_term_from_nowhere_is_a_question_not_an_entry(self):
        brief = context_brief(terms=[{"term": "Widget", "definition": "Nobody said.",
                                      "context": "Authoring"}])
        spec = self.generate(brief)
        self.assertNotIn("Widget", terms_of(spec))
        asked = " ".join(sections(spec)["open-questions"]["items"])
        self.assertIn("Widget", asked)

    def test_a_term_from_an_unknown_source_is_a_question_not_an_entry(self):
        brief = context_brief(terms=[{"term": "Widget", "definition": "Nobody said.",
                                      "source": "A conversation nobody recorded",
                                      "context": "Authoring"}])
        spec = self.generate(brief)
        self.assertNotIn("Widget", terms_of(spec))
        self.assertIn("Widget", " ".join(sections(spec)["open-questions"]["items"]))

    def test_every_entry_carries_exactly_one_definition_and_a_source(self):
        for entry in sections(self.generate())["glossary"]["items"]:
            self.assertTrue(entry["definition"].strip())
            self.assertTrue(entry["source"].strip())
            self.assertEqual(1, len([key for key in entry if key == "definition"]))

    def test_one_word_per_entry_is_canonical(self):
        entry = terms_of(self.generate())["Brief"]
        self.assertEqual(entry["canonical"], "Brief")
        self.assertEqual(entry["synonyms"], ["input pack"])

    def test_a_synonym_is_never_also_a_canonical_term(self):
        spec = self.generate()
        canonical = set(terms_of(spec))
        for entry in sections(spec)["glossary"]["items"]:
            for word in entry.get("synonyms", ()):
                self.assertNotIn(word, canonical)

    def test_the_same_definition_stated_twice_is_one_entry(self):
        said = {"term": "Brief", "definition": "The material a generator is handed.",
                "source": "Kick-off conversation", "context": "Authoring"}
        brief = context_brief(terms=[said, dict(said)])
        entries = sections(self.generate(brief))["glossary"]["items"]
        self.assertEqual(1, len([one for one in entries if one["canonical"] == "Brief"]))

    def test_an_entry_carries_its_identifier_where_a_reader_can_see_it(self):
        entry = terms_of(self.generate())["Brief"]
        self.assertEqual(entry["id"], "UL-01")
        self.assertIn("UL-01", entry["term"])

    def test_a_glossary_of_nothing_is_absent_rather_than_empty(self):
        spec = self.generate(context_brief(terms=[]))
        self.assertNotIn("glossary", sections(spec))
        self.assertIn("what words this project uses",
                      " ".join(sections(spec)["open-questions"]["items"]))


# ------------------------------------------------------------- the collisions

class TestACollisionIsAskedAboutNeverDecided(Sandbox):
    """M3-P4-T2-C1: a collision produces a question, never a silent choice."""

    def setUp(self):
        Sandbox.setUp(self)
        self.author_vision()
        self.brief = context_brief(terms=[
            {"term": "Source", "definition": "Material the author consulted.",
             "source": "Kick-off conversation", "context": "Authoring"},
            {"term": "Source", "definition": "The upstream document a check reads.",
             "source": "the vision", "context": "Validation"}])

    def fork(self):
        return [one for one in context.forks(self.brief) if one.id != "gaps"][0]

    def test_the_collision_opens_a_fork(self):
        run = gate.Gate(context.SLUG, context.forks(self.brief), source=self.brief)
        self.assertIn("Source", " ".join(one.question for one in run.open_forks))

    def test_the_generator_refuses_while_the_collision_is_open(self):
        run = gate.Gate(context.SLUG, context.forks(self.brief), source=self.brief)
        run.answer("gaps", "question", "Asking beats assuming.")
        with self.assertRaises(gate.GateNotClosed):
            context.generate(self.brief, run, self.root)

    def test_both_meanings_are_offered(self):
        offered = " ".join(one.label + " " + one.meaning for one in self.fork().options)
        self.assertIn("Authoring", offered)
        self.assertIn("Validation", offered)

    def test_the_fork_recommends_exactly_one_resolution(self):
        self.assertEqual(1, len([one for one in self.fork().options if one.recommended]))

    def test_scoping_is_the_recommendation_when_the_contexts_differ(self):
        self.assertEqual(self.fork().recommended.id, "scope")

    def test_an_answer_nobody_offered_is_refused_rather_than_guessed(self):
        run = gate.Gate(context.SLUG, context.forks(self.brief), source=self.brief)
        run.answer("gaps", "question", "Asking beats assuming.")
        run.answer(self.fork().id, "whatever you think", "A vague answer.")
        with self.assertRaises(context.UnresolvedCollision) as caught:
            context.generate(self.brief, run, self.root)
        self.assertIn("Source", str(caught.exception))

    def test_the_answer_is_recorded_in_the_locked_table(self):
        spec = self.generate(self.brief)
        rows = sections(spec)["locked-decisions"]["rows"]
        self.assertIn(self.fork().id, [row[0] for row in rows])


class TestAScopedTermShowsBothMeanings(Sandbox):
    """M3-P4-T2-C2: scoped meanings, and the boundary on the map."""

    def setUp(self):
        Sandbox.setUp(self)
        self.author_vision()
        self.brief = context_brief(terms=[
            {"term": "Source", "definition": "Material the author consulted.",
             "source": "Kick-off conversation", "context": "Authoring"},
            {"term": "Source", "definition": "The upstream document a check reads.",
             "source": "the vision", "context": "Validation"}])
        self.fork_id = [one.id for one in context.forks(self.brief) if one.id != "gaps"][0]

    def test_both_scoped_meanings_reach_the_entry(self):
        entry = terms_of(self.generate(self.brief))["Source"]
        self.assertIn("Authoring", entry["definition"])
        self.assertIn("Validation", entry["definition"])
        self.assertEqual(["Authoring", "Validation"],
                         [one["context"] for one in entry["meanings"]])

    def test_the_boundary_appears_on_the_context_map(self):
        rows = sections(self.generate(self.brief))["context-map"]["rows"]
        crossing = [row for row in rows if "Source" in row[2]]
        self.assertEqual(1, len(crossing))
        self.assertIn("Authoring", crossing[0][0])
        self.assertIn("Validation", crossing[0][1])

    def test_choosing_one_meaning_leaves_the_other_out(self):
        answers = {self.fork_id: "meaning-1"}
        entry = terms_of(self.generate(self.brief, **answers))["Source"]
        self.assertIn("Material the author consulted.", entry["definition"])
        self.assertNotIn("upstream document", entry["definition"])
        self.assertNotIn("meanings", entry)

    def test_a_chosen_meaning_crosses_no_boundary(self):
        answers = {self.fork_id: "meaning-2"}
        spec = self.generate(self.brief, **answers)
        rows = sections(spec).get("context-map", {}).get("rows", [])
        self.assertEqual([], [row for row in rows if "Source" in row[2]])


class TestAWordThatIsAlsoSomeoneElsesSynonym(Sandbox):
    """FR-CTX-04 covers overlap as well as collision."""

    def setUp(self):
        Sandbox.setUp(self)
        self.author_vision()
        self.brief = context_brief(terms=[
            {"term": "Brief", "definition": "The material a generator is handed.",
             "source": "Kick-off conversation", "context": "Authoring",
             "synonyms": ["Source material"]},
            {"term": "Source material", "definition": "Anything the author read.",
             "source": "the vision", "context": "Authoring"}])
        self.fork_id = [one.id for one in context.forks(self.brief) if one.id != "gaps"][0]

    def test_the_overlap_is_asked_about(self):
        self.assertTrue(self.fork_id.startswith("overlap:"))

    def test_retiring_the_word_leaves_one_entry_that_records_it(self):
        entry = terms_of(self.generate(self.brief))
        self.assertNotIn("Source material", entry)
        self.assertIn("Source material", entry["Brief"]["synonyms"])

    def test_keeping_the_word_stops_it_being_a_synonym_too(self):
        entries = terms_of(self.generate(self.brief, **{self.fork_id: "term"}))
        self.assertIn("Source material", entries)
        self.assertNotIn("Source material", entries["Brief"].get("synonyms", []))

    def test_an_answer_nobody_offered_is_refused_here_too(self):
        run = gate.Gate(context.SLUG, context.forks(self.brief), source=self.brief)
        run.answer("gaps", "question", "Asking beats assuming.")
        run.answer(self.fork_id, "leave it with me", "A vague answer.")
        with self.assertRaises(context.UnresolvedCollision):
            context.generate(self.brief, run, self.root)


# -------------------------------------------------------- the bounded contexts

class TestBoundedContexts(Sandbox):

    def setUp(self):
        Sandbox.setUp(self)
        self.author_vision()

    def test_each_context_is_numbered_in_the_order_stated(self):
        cards = sections(self.generate())["contexts"]["items"]
        self.assertEqual(["BC-01", "BC-02"], [one["id"] for one in cards])
        self.assertIn("BC-01", cards[0]["title"])

    def test_a_term_scoped_to_an_undeclared_context_is_refused(self):
        brief = context_brief(terms=[{"term": "Brief", "definition": "Handed over.",
                                      "source": "the vision", "context": "Shipping"}])
        with self.assertRaises(chain.IncompleteBrief) as caught:
            self.generate(brief)
        self.assertIn("Shipping", str(caught.exception))
        self.assertIn("Brief", str(caught.exception))

    def test_no_contexts_means_no_section_and_a_recorded_gap(self):
        brief = context_brief(contexts=[], terms=[
            {"term": "Brief", "definition": "Handed over.", "source": "the vision"}])
        spec = self.generate(brief)
        self.assertNotIn("contexts", sections(spec))
        self.assertNotIn("context-map", sections(spec))
        self.assertIn("bounded context",
                      " ".join(sections(spec)["open-questions"]["items"]))

    def test_the_map_shows_which_context_feeds_which(self):
        rows = sections(self.generate())["context-map"]["rows"]
        self.assertIn(["Authoring", "Validation"], [row[:2] for row in rows])


# --------------------------------------------------------------- the document

class TestTheGeneratedContextValidates(Sandbox):

    def setUp(self):
        Sandbox.setUp(self)
        self.author_vision()
        self.spec = self.generate()

    def test_it_passes_the_validator_the_published_set_is_held_to(self):
        found = validate.validate_document(self.spec, "Context.html")
        self.assertEqual([], [one for one in found if one.severity == schema.FAILURE])

    def test_every_identifier_is_well_formed(self):
        self.assertEqual([], schema.check_identifiers(self.spec))

    def test_no_section_is_present_but_empty(self):
        self.assertEqual([], schema.check_emptiness(self.spec))

    def test_the_source_register_travels_with_the_document(self):
        self.assertEqual(["Kick-off conversation"],
                         [one["name"] for one in self.spec["sources"]])

    def test_the_same_brief_produces_the_same_bytes(self):
        again = self.generate()
        self.assertEqual(context.render(self.spec, self.root),
                         context.render(again, self.root))

    def test_the_generator_never_reads_the_clock(self):
        self.assertEqual(self.spec["document"]["date"], "2026-08-14")
        reachable = imports(inspect.getsource(context))
        for name in CLOCK:
            self.assertNotIn(name, reachable, name)


class TestWhatAuthoringLeavesBehind(Sandbox):

    def setUp(self):
        Sandbox.setUp(self)
        self.author_vision()
        brief = context_brief()
        self.path, self.spec = context.author(self.root, brief, gate_for(brief))

    def test_the_document_is_written_where_the_layout_says(self):
        self.assertEqual(self.path,
                         paths.resolve(self.root, paths.SPECS_DIR, context.FILENAME))
        self.assertTrue(os.path.isfile(self.path))

    def test_the_written_document_carries_the_specification_back(self):
        with open(self.path, encoding="utf-8") as handle:
            self.assertEqual(validate.extract(handle.read())["document"]["slug"],
                             context.SLUG)

    def test_the_decisions_are_in_the_ledger(self):
        with open(gate.ledger_path(self.root, context.SLUG), encoding="utf-8") as handle:
            self.assertIn(gate.TABLE_HEADING, handle.read())


# ------------------------------------------------- the language, downstream

def downstream():
    """A document from further down the chain, in the wrong words."""
    return {"document": {"title": "Requirements", "slug": "prd", "type": "PRD",
                         "version": "1.0", "status": "Draft", "date": "2026-08-14",
                         "owner": "A. Owner"},
            "schemaVersion": schema.SCHEMA_VERSION,
            "sections": [{"id": "goals", "type": "list", "title": "Goals",
                          "items": ["Every input pack is recorded."]},
                         {"id": "notes", "type": "prose", "title": "Notes",
                          "body": ["The input pack arrives before the gate."]}]}


class TestDownstreamDocumentsSpeakTheLanguage(Sandbox):
    """M3-P4-T3-C1: canonical terms in, retired synonyms out."""

    def setUp(self):
        Sandbox.setUp(self)
        self.author_vision()
        brief = context_brief()
        context.author(self.root, brief, gate_for(brief))
        self.glossary = context.read(self.root)

    def test_a_retired_synonym_becomes_the_canonical_term(self):
        spoken = context.consult(downstream(), self.glossary)
        self.assertIn("Brief", " ".join(strings(spoken["sections"][0])))

    def test_no_retired_synonym_survives_anywhere_in_the_document(self):
        spoken = context.consult(downstream(), self.glossary)
        for text in strings(spoken):
            self.assertNotIn("input pack", text.lower())

    def test_consulting_leaves_the_document_it_was_given_alone(self):
        original = downstream()
        untouched = copy.deepcopy(original)
        context.consult(original, self.glossary)
        self.assertEqual(untouched, original)

    def test_an_identifier_is_not_prose_and_is_left_alone(self):
        spoken = context.consult(downstream(), self.glossary)
        self.assertEqual(spoken["document"]["slug"], "prd")
        self.assertEqual([one["id"] for one in spoken["sections"]], ["goals", "notes"])

    def test_the_glossary_answers_what_a_word_should_be(self):
        self.assertEqual(self.glossary.canonical("input pack"), "Brief")
        self.assertEqual(self.glossary.canonical("BRIEF"), "Brief")
        self.assertIsNone(self.glossary.canonical("kestrel"))

    def test_reading_a_project_with_no_context_document_is_refused(self):
        empty = tempfile.mkdtemp(prefix="z2s-context-")
        try:
            with self.assertRaises(chain.MissingPrerequisite):
                context.read(empty)
        finally:
            shutil.rmtree(empty, ignore_errors=True)


class TestSpeakingWithoutTheDocument(unittest.TestCase):
    """The glossary on its own, where the substitution rules are visible."""

    def test_a_longer_synonym_is_replaced_whole(self):
        # "pack" sits inside "pack of inputs", and sorts before it. Replaced
        # shortest-first the sentence becomes "the Brief of inputs" — the debris
        # a word-by-word pass leaves behind, in the order that provokes it.
        book = context.Glossary([{"canonical": "Brief", "id": "UL-01",
                                  "synonyms": ["pack", "pack of inputs"]}])
        self.assertEqual(book.speak("The pack of inputs arrives."),
                         "The Brief arrives.")

    def test_a_word_the_glossary_never_heard_of_is_left_alone(self):
        book = context.Glossary([{"canonical": "Brief", "id": "UL-01",
                                  "synonyms": ["input pack"]}])
        self.assertEqual(book.speak("The kestrel stoops."), "The kestrel stoops.")

    def test_a_synonym_inside_a_longer_word_is_not_a_match(self):
        book = context.Glossary([{"canonical": "Gate", "id": "UL-01",
                                  "synonyms": ["fork"]}])
        self.assertEqual(book.speak("A forklift is not a fork."),
                         "A forklift is not a Gate.")


class TestAMissingTermFlowsBack(Sandbox):
    """M3-P4-T3-C2: added to the context document, never defined locally."""

    def setUp(self):
        Sandbox.setUp(self)
        self.author_vision()
        brief = context_brief()
        self.path, _ = context.author(self.root, brief, gate_for(brief))

    def glossary_now(self):
        with open(self.path, encoding="utf-8") as handle:
            return terms_of(validate.extract(handle.read()))

    def test_the_term_is_appended_to_the_context_document(self):
        identifier = context.amend(self.root, "Ledger",
                                   "The running record of one build.",
                                   "the product requirements")
        self.assertEqual(identifier, "UL-03")
        self.assertIn("Ledger", self.glossary_now())

    def test_nothing_already_defined_is_renumbered(self):
        before = dict((word, entry["id"]) for word, entry in self.glossary_now().items())
        context.amend(self.root, "Ledger", "The running record.", "the requirements")
        after = self.glossary_now()
        for word, identifier in before.items():
            self.assertEqual(after[word]["id"], identifier)

    def test_a_word_the_glossary_already_knows_is_not_added_twice(self):
        identifier = context.amend(self.root, "input pack", "Whatever this is.",
                                   "the requirements")
        self.assertEqual(identifier, self.glossary_now()["Brief"]["id"])
        self.assertNotIn("input pack", self.glossary_now())

    def test_an_amendment_says_where_it_came_from(self):
        context.amend(self.root, "Ledger", "The running record.",
                      "the product requirements")
        entry = self.glossary_now()["Ledger"]
        self.assertIn("the product requirements", entry["source"])
        self.assertTrue(entry["amended"])

    def test_the_amended_document_still_validates(self):
        context.amend(self.root, "Ledger", "The running record.", "the requirements")
        with open(self.path, encoding="utf-8") as handle:
            spec = validate.extract(handle.read())
        found = validate.validate_document(spec, "Context.html")
        self.assertEqual([], [one for one in found if one.severity == schema.FAILURE])


if __name__ == "__main__":
    unittest.main()
