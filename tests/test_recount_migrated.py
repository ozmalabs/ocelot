"""test_recount_migrated -- the "recount what you read" faculty
(domains.recount_faculty): READING IS WRITING REVERSED, applied to a whole
document. The Jabberwock BUILDS comprehend_recount + communicate_what_i_read
via its own self-build composer (reflective_faculty.induce_concern /
ground_concern -- verified live, not assumed) and SPEAKS a genuine recount of
a real short article via LanguageProduction.produce (reverse-comprehension
NLG, self-monitored by re-parsing its own output), never a Python template.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
     tests/test_recount_migrated.py -p no:randomly -q
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
from domains import audience_driven_production as adp          # noqa: E402
from domains.language_world import LanguageWorld, teacher_stub  # noqa: E402
from domains.language_production import LanguageProduction     # noqa: E402
from scripts.language_test import training_bank                # noqa: E402

ARTICLE = ("Robert Levy, an attorney at ExxonMobil, will join the Justice Department. "
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


# --------------------------------------------------------------------------- #
#  ASKING FIRES THE RECOUNT (not the honest "no faculty" gap).
# --------------------------------------------------------------------------- #
def test_asking_to_recount_fires_the_faculty_not_a_gap():
    """Before build_recount_faculty, no comprehend_recount rule exists; a
    'Recount what you read.' directive would mint nothing. After the agent
    BUILDS the faculty (its own composer -- see test_rules_are_composer_
    authored below) and the world receives the instruction, a real
    describe_scene Goal + produce_utterance subgoals are minted -- the
    faculty fired, not an honest gap."""
    a, donkey = _fresh_agent_with_donkey()
    assert not rf.faculty_built(a)
    world, prod = _fresh_voice(a)
    result = rf.recount_what_read(a, world, prod, ARTICLE,
                                  instruction="Recount what you read.")
    assert rf.faculty_built(a)
    assert result["n_goals"] >= 1
    assert result["n_subgoals"] >= 1
    assert len(result["lines"]) >= 1
    assert donkey["n"] == 0


def test_summarize_phrasing_also_fires_it():
    """A different human phrasing ('Summarize the article.') reaches the SAME
    faculty via the documented synonym bridge (see module docstring) -- not
    just the literal 'describe' wording."""
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    result = rf.recount_what_read(a, world, prod, ARTICLE,
                                  instruction="Summarize the article.")
    assert result["n_goals"] >= 1
    assert len(result["lines"]) >= 1
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  THE PROSE NAMES REAL READ CONTENT, GENUINELY PRODUCED.
# --------------------------------------------------------------------------- #
def test_recount_names_read_content_and_round_trips():
    """The produced lines name real content read out of the article (Robert /
    joined / Department / Citizen / said / government) -- not placeholders.
    Both realized events pass LanguageProduction's OWN self-monitor round-
    trip (produce -> re-parse -> frame matches) -- genuine comprehension-
    reversed generation, not an accidental string."""
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    result = rf.recount_what_read(a, world, prod, ARTICLE,
                                  instruction="Recount what you read.", register="formal")
    joined = " ".join(result["lines"])
    for content_word in ("Robert", "joined", "Department", "Citizen", "said"):
        assert content_word in joined, f"missing read content word {content_word!r} in {joined!r}"
    # MULTI-WORD ENTITIES ARE REALIZED IN FULL (not collapsed to their head):
    # the recount_realization.json rules route the WHOLE read entity into the
    # produce-frame noun slot, so the named entities come out whole.
    assert "Justice Department" in joined, f"multi-word entity collapsed to head in {joined!r}"
    assert "Public Citizen" in joined, f"multi-word entity collapsed to head in {joined!r}"
    assert result["accepted"], "no lines were produced"
    assert all(result["accepted"]), f"a produced line failed its own self-monitor round-trip: {result}"
    assert result["prose"].startswith("I observe ")
    assert donkey["n"] == 0


def test_a_genuine_reading_residual_is_named_not_faked():
    """A genuine reading gap (a predicate whose lemma is itself a closed-class
    preposition, not a verb -- the situation-model reader mis-extracted the
    true verb) is reported as a named residual, never force-rendered as a fake
    event. This ARTICLE's second sentence used to be exactly this case ('He
    promoted the burning of fossil fuels.' read `of(...)`, a nested 'of'
    pre-empting the finite verb 'promoted' -- READER_PARSER_MIGRATION.md
    PHASE 1, domains/reading_collapse.py's `_of_yields_to_finite_verb` guard)
    and is FIXED now: the sentence grounds a real 'promoted' event and
    contributes no residual any more (see
    test_recount_names_second_sentence_now_grounds_after_phase1_fix below).
    A DIFFERENT construction Phase 1 deliberately leaves untouched (a gerund
    immediately before 'of' is that phrase's own head, never a competing
    finite verb -- 'burning of fossil fuels' stays a genuine gap) is used
    here instead, so this test keeps exercising a REAL residual."""
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    still_broken_article = (
        "Robert Levy, an attorney at ExxonMobil, will join the Justice "
        "Department. The burning of fossil fuels harmed the planet. "
        "Public Citizen said Big Oil captured the government.")
    result = rf.recount_what_read(a, world, prod, still_broken_article,
                                  instruction="Recount what you read.")
    assert len(result["residuals"]) == 1
    assert result["residuals"][0]["predication"][0] == "of"
    assert donkey["n"] == 0


def test_recount_names_second_sentence_now_grounds_after_phase1_fix():
    """HEADLINE (READER_PARSER_MIGRATION.md PHASE 1): the ARTICLE's second
    sentence -- 'He promoted the burning of fossil fuels.' -- used to be
    dropped from the recount entirely (its only predication was the
    mis-extracted 'of(...)' residual, declined by recount_event_realizable,
    so no line was ever produced for it). It is now grounded as a real
    'promoted' event and RECOVERED into the recount, with ZERO residuals for
    the whole article -- the recount faculty benefits automatically from the
    graph-native fix, no recount_faculty.py change needed (mirrors
    scripts/jabberwock_recounts_article.py)."""
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    result = rf.recount_what_read(a, world, prod, ARTICLE,
                                  instruction="Recount what you read.")
    assert result["residuals"] == [], result["residuals"]
    joined = " ".join(result["lines"])
    assert "promoted" in joined.lower(), joined
    assert "fossil fuels" in joined.lower(), joined
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  THE REALIZATION DECISION IS A GRAPH RULE, NOT PYTHON. Ablating the seed
#  rule that routes a read entity into the noun slot changes the output --
#  the source-level proof that recount_faculty.py decides nothing here
#  (head_surface / is_function_predicate are DELETED; the decisions live in
#  seeds/recount_realization.json).
# --------------------------------------------------------------------------- #
def _ablate_rule(agent, name):
    """Remove a live rule by name (mechanical tombstone -- the daemon's own
    remove_rule path). Returns True iff a rule was removed."""
    live = list(agent.inner.export_rules())
    for i, r in enumerate(live):
        if r.get("name") == name:
            agent.inner.remove_rule(i)
            return True
    return False


def test_multiword_realization_is_a_rule_not_python():
    """With the realization rules present, the multi-word entity 'Justice
    Department' is realized in full. ABLATE recount_say_patient and the same
    read graph produces lines WITHOUT the patient phrase -- proving the
    slot-routing decision is the rule's, not Python's. Then (on a STILL-
    genuinely-residual article -- see test_a_genuine_reading_residual_is_
    named_not_faked's docstring for why the shared ARTICLE no longer supplies
    one after the phase-1 fix) ablate recount_event_realizable and the honest
    'of' residual is no longer declined by the (now absent) skip guard --
    proving the skip is the rule's decision too."""
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    normal = rf.recount_what_read(a, world, prod, ARTICLE,
                                  instruction="Recount what you read.", register="formal")
    assert "Justice Department" in " ".join(normal["lines"])
    assert normal["residuals"] == []      # phase-1 fix: the shared ARTICLE now grounds cleanly

    a2, donkey2 = _fresh_agent_with_donkey()
    assert _ablate_rule(a2, "recount_say_patient")
    world2, prod2 = _fresh_voice(a2)
    ablated = rf.recount_what_read(a2, world2, prod2, ARTICLE,
                                   instruction="Recount what you read.", register="formal")
    joined = " ".join(ablated["lines"])
    assert "Justice Department" not in joined            # patient dropped: the routing was the rule's
    assert "Robert" in joined                            # agent still realized (its rule remains)

    still_broken_article = (
        "Robert Levy, an attorney at ExxonMobil, will join the Justice "
        "Department. The burning of fossil fuels harmed the planet. "
        "Public Citizen said Big Oil captured the government.")
    a3, donkey3 = _fresh_agent_with_donkey()
    world3, prod3 = _fresh_voice(a3)
    with_guard = rf.recount_what_read(a3, world3, prod3, still_broken_article,
                                      instruction="Recount what you read.")
    assert len(with_guard["residuals"]) == 1              # 'of' declined by the rule

    a4, donkey4 = _fresh_agent_with_donkey()
    assert _ablate_rule(a4, "recount_residual_mark")
    world4, prod4 = _fresh_voice(a4)
    no_guard = rf.recount_what_read(a4, world4, prod4, still_broken_article,
                                    instruction="Recount what you read.")
    # The 'of' predication is no longer FLAGGED a residual, because the rule
    # that identifies it (recount_residual_mark, holding the preposition
    # codebook) is gone -- the skip/residual decision was the rule's, not
    # Python's. (The 'of' line is still not realized: recount_event_realizable
    # -- still present -- declines it; the two rules are the two halves of the
    # one graph-native decision that used to be Python's is_function_predicate.)
    assert no_guard["residuals"] == []
    assert "Robert Levy joined Justice Department." in no_guard["lines"]  # coref-resolved full span
    assert (donkey["n"] == 0 and donkey2["n"] == 0
            and donkey3["n"] == 0 and donkey4["n"] == 0)


# --------------------------------------------------------------------------- #
#  REGISTER differentiates lead/join.
# --------------------------------------------------------------------------- #
def test_register_differs_formal_vs_casual():
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    formal = rf.recount_what_read(a, world, prod, ARTICLE,
                                  instruction="Recount what you read.", register="formal")
    a2, donkey2 = _fresh_agent_with_donkey()
    world2, prod2 = _fresh_voice(a2)
    casual = rf.recount_what_read(a2, world2, prod2, ARTICLE,
                                  instruction="Recount what you read.", register="casual")
    assert formal["prose"] != casual["prose"]
    assert formal["prose"].startswith("I observe ")
    assert not casual["prose"].startswith("I ")
    assert donkey["n"] == 0 and donkey2["n"] == 0


# --------------------------------------------------------------------------- #
#  TARGET (audience design): a grounded interlocutor who already knows some
#  of the content gets a SHORTER recount than an ungrounded one.
# --------------------------------------------------------------------------- #
def test_target_audience_design_skips_already_known_content():
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    friend = adp.audience_model(
        a, {"id": "friend", "observed": True,
            "known_concepts": ["Robert Levy", "joined", "Justice Department"]})
    stranger_result = rf.recount_what_read(a, world, prod, ARTICLE,
                                           instruction="Recount what you read.",
                                           register="neutral")
    a2, donkey2 = _fresh_agent_with_donkey()
    world2, prod2 = _fresh_voice(a2)
    friend2 = adp.audience_model(
        a2, {"id": "friend", "observed": True,
            "known_concepts": ["Robert Levy", "joined", "Justice Department"]})
    targeted_result = rf.recount_what_read(a2, world2, prod2, ARTICLE,
                                           instruction="Recount what you read.",
                                           register="neutral", audience=friend2)
    assert len(targeted_result["lines"]) < len(stranger_result["lines"])
    assert len(targeted_result["skipped_known_to_audience"]) >= 1
    assert donkey["n"] == 0 and donkey2["n"] == 0
    assert friend["grounded"] is True


# --------------------------------------------------------------------------- #
#  THE RULES WERE COMPOSER-AUTHORED, not hand-written.
# --------------------------------------------------------------------------- #
def test_rules_are_composer_authored_not_hand_written():
    """`build_recount_faculty` calls ONLY `induce_concern`/`ground_concern` to
    obtain its two rules -- it contains no `add_rule` call of its own. This
    is the source-level guarantee that the comprehend/communicate rule
    BODIES are the composer's authorship, not this module's."""
    src = inspect.getsource(rf.build_recount_faculty)
    tree = ast.parse(src)
    calls = [n.func.attr for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    assert "add_rule" not in calls
    call_names = [n.func.id for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
    assert "induce_concern" in call_names
    assert "ground_concern" in call_names


def test_faculty_built_reports_the_two_composed_rule_names():
    a, donkey = _fresh_agent_with_donkey()
    report = rf.build_recount_faculty(a)
    assert report["already_built"] is False
    assert report["comprehend_ground"]["served_by"] == "graph"
    assert report["communicate_ground"]["served_by"] == "graph"
    assert rf.faculty_built(a)
    # idempotent: a second call does not re-author.
    report2 = rf.build_recount_faculty(a)
    assert report2 == {"already_built": True}
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  NO TEMPLATING -- the recount pipeline never string-builds a sentence from
#  content words (f-string / .format / str concatenation of the frame's own
#  agent/event/patient values). Every produced string comes from
#  `prod.produce(...)["overt_speech"]`.
# --------------------------------------------------------------------------- #
def test_no_templated_sentence_construction_in_recount_faculty():
    src = inspect.getsource(rf)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        assert not isinstance(node, ast.JoinedStr), "an f-string was found in recount_faculty.py"
    assert "produce" in src
    # the only string built from say_agent/say_event/say_patient is the GOAL
    # dict handed to prod.produce -- never a sentence.
    assert "say_agent'] +" not in src and 'say_agent"] +' not in src


def test_donkey_zero_across_the_whole_module():
    """Every public entry in this module is LLM-free by construction (no
    teacher call anywhere in the recount path)."""
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    rf.recount_what_read(a, world, prod, ARTICLE, instruction="Recount what you read.",
                         register="formal")
    rf.recount_what_read(a, world, prod, ARTICLE, instruction="Recount what you read.",
                         register="casual")
    assert donkey["n"] == 0
