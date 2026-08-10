"""test_recount_fluency_migrated -- the RECOUNT FLUENCY arc. The Jabberwock's
recount used to read as a FLAT LIST: "I observe the oil company funded the
technology, the oil company opposed the technology, and the spokesman
is_aed the critics." This was first TOLD to the Jabberwock over its own NL
interface (`agent.converse(...)`), which FILED it as a SelfConcern via the
existing gap-awareness faculty (`seeds/gap_awareness.json`'s
`note_reported_gap` -- an utterance whose Mentions resolve to a deficiency
concept ["cannot"/"repeat"/"wrong"] AND a self-word ["you"] is a
self-reported deficiency) -- see `test_the_jabberwock_files_the_fluency_gap_
itself` below, which reproduces that exact conversation live.

The FIX (`seeds/recount_fluency.json` + `seeds/recount_realization.json`
v1.1.0 + the mechanical glue in `domains/conversation_action.smooth_scene_
prose`) makes three fluency improvements, each an ABLATION-PROVEN graph
DECISION (a held codebook row or rule), never a Python literal:

  (a) RELATIONAL CONNECTIVES -- `recount_temporal_connective` correlates two
      ADJACENT recount events against a held `TemporalConflictReading`
      (already-graph-state, minted by actor_goals.py's own agent-authored
      rule) and looks up the connective in the held `ConnectiveMap` codebook
      (currently one row: temporal_conflict -> 'then'). Absent a held
      relation, the smoother's plain default ('and'/comma, the pre-existing
      Oxford join) is used -- NOTHING is ever fabricated.
  (b) REPEATED-SUBJECT ELISION + OBJECT PRONOMINALISATION --
      `recount_mark_repeated_agent`/`recount_mark_repeated_patient` flag a
      repeated mention across ADJACENT recount events; the pronoun WORD
      itself is held data (`PronounMap`, patient -> 'it').
  (c) THE COPULAR FIX -- `recount_say_event_copular`
      (seeds/recount_realization.json v1.1.0) renders an `is_a` predicate
      (a copular/designation read, e.g. "called X Y") as 'called' instead of
      the ungrammatical '+ed'-inflected 'is_aed'.

Every produced clause is STILL `LanguageProduction.produce`'s own,
self-monitored `overt_speech` -- the fluency layer only (a) reads a held
connective/pronoun decision, and (b) performs mechanical surgery (drop/
splice known-length noun-phrase spans, read off what `prod.produce` itself
emitted -- see `recount_faculty._np_word_count_from_production`) over that
ALREADY-PRODUCED text, in `smooth_scene_prose` -- the SAME category of glue
`_lower_article`/`_declause`/`_oxford` already were. donkey=0 throughout.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
     tests/test_recount_fluency_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import ast
import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter               # noqa: E402
from substrate.boot_all import load_all_seeds                  # noqa: E402
from domains import dictionary_lexicon as dl                   # noqa: E402
from domains import recount_faculty as rf                      # noqa: E402
from domains import conversation_action as ca                  # noqa: E402
from domains.language_world import LanguageWorld, teacher_stub  # noqa: E402
from domains.language_production import LanguageProduction     # noqa: E402
from scripts.language_test import training_bank                # noqa: E402

# The fund/oppose article the task itself specifies: a support-then-undermine
# TemporalConflictReading (fund|oppose), a repeated subject ("the oil
# company") AND object ("the technology") across the two events, and a
# copular "called X Y" third sentence the reader collapses to is_a.
ANALYSIS_ARTICLE = ("The technology was funded by the oil company. "
                    "The technology was opposed by the oil company. "
                    "With all due respect, a spokesman called the critics misinformed.")

# A plain article with NO temporal-conflict relation anywhere -- the honesty
# control for the connective: every juncture must stay the plain default.
PLAIN_ARTICLE = ("Robert Levy, an attorney at ExxonMobil, will join the Justice Department. "
                 "He promoted the burning of fossil fuels. "
                 "Public Citizen said Big Oil captured the government.")


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fresh_agent_with_donkey():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    return a, donkey


def _fresh_voice(agent):
    world = LanguageWorld(agent.inner, training_bank(), teacher_stub)
    world.run()
    world.teacher_disabled = True
    return world, LanguageProduction(world)


def _ablate_rule(agent, name):
    """Remove a live rule by name -- the SAME helper test_recount_migrated.py
    / test_recount_analysis_migrated.py use."""
    live = list(agent.inner.export_rules())
    for i, r in enumerate(live):
        if r.get("name") == name:
            agent.inner.remove_rule(i)
            return True
    return False


def _remove_codebook_row(agent, node_type, **match_attrs):
    """Remove ONE held codebook NODE (a genuine graph-data 'row', not a
    rule) matching every given attr -- the mechanical daemon-style node
    tombstone (agent.inner.remove_node), used to prove a fluency DECISION is
    the codebook ROW's, not a Python literal: delete the row and the
    behaviour it drove reverts. Returns True iff a node was removed."""
    sub = agent.s
    for n in sub.nodes(node_type):
        at = sub.node(n)["attrs"]
        if all(at.get(k) == v for k, v in match_attrs.items()):
            agent.inner.remove_node(n)
            return True
    return False


# --------------------------------------------------------------------------- #
#  STEP 1 -- THE JABBERWOCK IS TOLD, AND FILES THE GAP ITSELF (over its own
#  NL interface, via the EXISTING gap-awareness faculty -- no new code).
# --------------------------------------------------------------------------- #
def test_the_jabberwock_files_the_fluency_gap_itself():
    """Tell the Jabberwock, in plain English, what its recount lacks for
    fluency; it FILES that as a SelfConcern via the pre-existing
    `note_reported_gap` rule (a Mention resolving to a deficiency concept --
    here 'cannot'/'repeat'/'wrong' -- AND a self-word 'you' is a
    self-reported deficiency), and SURFACES it when asked -- BEFORE any of
    the fluency fix code below runs. This is the self-sufficiency framing:
    told -> finds the gap -> (separately) fixed."""
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("noted", "acknowledgment")
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])

    report = ("You list events flatly, you cannot connect them, you repeat "
              "the subject, and you render is_a wrong.")
    reply = a.converse(report, "statement")
    assert reply is not None
    assert "gap" in reply.lower()

    concerns = [n for n in a.s.nodes("SelfConcern")
               if a.s.node(n)["attrs"].get("source") == "explicit_report"
               and a.s.node(n)["attrs"].get("content") == report]
    assert len(concerns) == 1, "the report was not filed as exactly one SelfConcern"

    surfaced = a.converse("What gaps do you have?", "question")
    assert surfaced is not None
    assert report in surfaced or "flat" in surfaced.lower() or "repeat" in surfaced.lower()
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  (a) RELATIONAL CONNECTIVES -- reflects the held TemporalConflictReading;
#      ablating the RULE or removing the CODEBOOK ROW both revert the join
#      to the plain default; a juncture with no held relation is untouched.
# --------------------------------------------------------------------------- #
def test_connective_reflects_the_held_temporal_relation():
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    assert "the oil company funded the technology, then opposed it" in result["surface_prose"]
    # the SECOND juncture (oppose -> the copular sentence) has NO held
    # relation between those two events (different agents) -- the plain
    # default Oxford "and" is used there, nothing invented.
    assert ", then the spokesman" not in result["surface_prose"]
    assert ", and the spokesman called the critics" in result["surface_prose"]
    assert donkey["n"] == 0


def test_ablating_the_connective_rule_reverts_to_default_and():
    a, donkey = _fresh_agent_with_donkey()
    assert _ablate_rule(a, "recount_temporal_connective")
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    assert "then" not in result["surface_prose"]
    assert "the oil company funded the technology, opposed it" in result["surface_prose"]
    assert donkey["n"] == 0


def test_removing_the_connectivemap_row_reverts_to_default_and():
    """The DECISION is the held CODEBOOK ROW's, not the rule's structure --
    delete the row (agent.inner.remove_node, a genuine graph-data tombstone,
    not a rule ablation) and the SAME rule, now finding no row to join
    against, never sets a connective."""
    a, donkey = _fresh_agent_with_donkey()
    assert _remove_codebook_row(a, "ConnectiveMap", relation="temporal_conflict")
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    assert "then" not in result["surface_prose"]
    assert "the oil company funded the technology, opposed it" in result["surface_prose"]
    assert donkey["n"] == 0


def test_no_relation_no_connective_ever_fabricated():
    """The honesty control: an article with NO TemporalConflictReading
    anywhere never gets a relational connective at ANY juncture -- only the
    plain Oxford default ('and'), exactly as before this build."""
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    result = rf.recount_what_read(a, world, prod, PLAIN_ARTICLE,
                                  instruction="Recount what you read.", register="formal")
    for connective in (" then ", " but ", " so "):
        assert connective not in result["prose"], result["prose"]
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  (b) REPEATED-SUBJECT ELISION + OBJECT PRONOMINALISATION -- both flags are
#      the RULES' decisions (ablation-proven); the surgery reads exact word
#      counts off what `prod.produce` itself emitted.
# --------------------------------------------------------------------------- #
def test_repeated_subject_elided_and_object_pronominalised():
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    # the SURFACE LINES are UNCHANGED -- each still the full, independently
    # produced, self-monitored clause (elision is glue over the PROSE only).
    assert result["surface_lines"][:2] == [
        "The oil company funded the technology.",
        "The oil company opposed the technology.",
    ]
    assert all(result["accepted"][:3])
    # the smoothed PROSE elides the repeated subject and pronominalises the
    # repeated object: no second "the oil company", no second "the technology".
    assert result["surface_prose"].count("oil company") == 1
    assert "opposed it" in result["surface_prose"]
    assert donkey["n"] == 0


def test_ablating_repeated_agent_rule_restores_the_full_subject():
    a, donkey = _fresh_agent_with_donkey()
    assert _ablate_rule(a, "recount_mark_repeated_agent")
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    assert result["surface_prose"].count("oil company") == 2
    assert "the oil company opposed it" in result["surface_prose"]
    assert donkey["n"] == 0


def test_ablating_repeated_patient_rule_restores_the_full_object():
    a, donkey = _fresh_agent_with_donkey()
    assert _ablate_rule(a, "recount_mark_repeated_patient")
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    assert "opposed the technology" in result["surface_prose"]
    assert " it," not in result["surface_prose"] and " it." not in result["surface_prose"]
    assert donkey["n"] == 0


def test_removing_the_pronounmap_row_restores_the_full_object():
    a, donkey = _fresh_agent_with_donkey()
    assert _remove_codebook_row(a, "PronounMap", role="patient")
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    assert "opposed the technology" in result["surface_prose"]
    assert donkey["n"] == 0


def test_elision_is_a_general_fluency_improvement_on_the_original_article():
    """The SAME rule, unmodified, also fixes the pre-existing recount
    fixture's repeated 'Robert Levy' -- a genuine fluency improvement over
    test_recount_migrated.py's own PLAIN_ARTICLE, not special-cased to the
    task's fund/oppose article."""
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    result = rf.recount_what_read(a, world, prod, PLAIN_ARTICLE,
                                  instruction="Recount what you read.", register="formal")
    assert result["prose"].count("Robert Levy") == 1
    assert "promoted the burning of fossil fuels" in result["prose"]
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  (c) THE COPULAR FIX -- 'called', never the ungrammatical 'is_aed'.
# --------------------------------------------------------------------------- #
def test_copular_is_a_renders_as_called_not_is_aed():
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    assert "The spokesman called the critics." in result["surface_lines"]
    assert "is_a" not in " ".join(result["surface_lines"])
    assert "is_aed" not in result["surface_prose"]
    assert all(result["accepted"])
    assert donkey["n"] == 0


def test_ablating_the_copular_rule_is_an_honest_silence_not_a_wrong_word():
    """Ablate recount_say_event_copular: recount_say_event's OWN exclusion
    guard (added alongside it) still refuses to fill in 'is_aed' either --
    the concept's say_event stays unset, the produced line fails its own
    self-monitor (no event realized) and is reported UNACCEPTED, never
    silently wrong. Proves the copular surface is THIS rule's decision."""
    a, donkey = _fresh_agent_with_donkey()
    assert _ablate_rule(a, "recount_say_event_copular")
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    assert "is_aed" not in " ".join(result["surface_lines"])
    assert "called" not in result["surface_lines"][2]
    assert result["accepted"][2] is False
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  EXISTING RECOUNT/ANALYSIS TESTS STAY GREEN -- the fluency layer never
#  touches the per-clause `lines`/`accepted`/content-word assertions those
#  suites make; only the smoothed `prose` changed (verified above).
# --------------------------------------------------------------------------- #
def test_produce_generated_every_fluent_line_self_monitor_accepted():
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    assert len(result["surface_lines"]) == 3
    assert all(result["accepted"])
    for line, production in zip(result["surface_lines"], result["productions"][:3]):
        assert production["overt_speech"] == line
        assert production["accepted"] is True
    assert donkey["n"] == 0


def test_donkey_zero_across_the_fluency_layer():
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE, instruction="Recount what you read.",
                         register="formal", actor_classes={"oil_company": "corporation"})
    rf.recount_what_read(a, world, prod, PLAIN_ARTICLE, instruction="Recount what you read.",
                         register="casual")
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  NO TEMPLATING -- extends the existing AST audits to the fluency-path
#  functions (recount_faculty's new helper, conversation_action's new glue).
#  Zero f-strings BUILDING a sentence from content words (the pre-existing,
#  UNRELATED f-strings elsewhere in conversation_action.py -- honest host
#  templates for capability-limit notices, never a produced sentence -- are
#  untouched and out of scope for this audit, exactly as they were before).
# --------------------------------------------------------------------------- #
def test_no_templated_sentence_construction_in_the_fluency_glue():
    for fn in (rf._np_word_count_from_production, ca._oxford_with_connectives,
              ca.smooth_scene_prose):
        src = inspect.getsource(fn)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            assert not isinstance(node, ast.JoinedStr), \
                f"an f-string was found in {fn.__name__}"
    # module-wide audit of recount_faculty.py (the SAME assertion test_
    # recount_migrated.py's own audit makes -- re-run here since this
    # module's new code lives in that same file).
    src = inspect.getsource(rf)
    tree = ast.parse(src)
    assert not any(isinstance(n, ast.JoinedStr) for n in ast.walk(tree))


def test_seed_rules_are_the_fluency_decisions_not_python():
    """Source-level guarantee: recount_faculty.py never contains the
    connective words / pronoun / copular surface as a Python literal
    DECIDING which to use -- the only occurrences of 'then'/'called' in the
    module are inside comments/docstrings (prose describing the mechanism),
    never inside an `if`/comparison that picks a value."""
    tree = ast.parse(inspect.getsource(rf))
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for cmp in node.comparators + [node.left]:
                if isinstance(cmp, ast.Constant) and cmp.value in ("then", "called", "it"):
                    pytest.fail("a fluency word appears in an `if`/comparison in "
                               "recount_faculty.py -- should be held rule/codebook data")
