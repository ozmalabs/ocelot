"""test_recount_analysis_fluency_migrated -- the ANALYSIS layer's FLUENCY
fix. The surface-event recount already reads fluently (test_recount_fluency_
migrated.py); the ANALYSIS half (what the Jabberwock INFERRED, not just what
happened) still read like a machine dump:

    "... With All Due Respect signalled Express Vs Avoid Social Cost, Oil
    Company reversed Fund Then Oppose, Oil Company revealed Trojan Horse, and
    the reading leaned Weak Deception."

Two named problems: (1) the tension/pair_key SLOTS are raw slugs, naively
title-cased ('express-vs-avoid-social-cost' -> 'Express Vs Avoid Social
Cost'; 'fund|oppose' -> 'Fund Then Oppose'); (2) the temporal-conflict line
and the trope line are REDUNDANT whenever a trope names the pair -- both say
the SAME thing ('reversed Fund Then Oppose' / 'revealed Trojan Horse').

This was first TOLD to the Jabberwock over its own NL interface
(`agent.converse(...)`), which FILED it as a SelfConcern via the pre-existing
gap-awareness faculty (`seeds/gap_awareness.json`'s `note_reported_gap`) --
see `test_the_jabberwock_files_the_analysis_fluency_gap_itself` below, which
reproduces that exact conversation live, BEFORE any of the fix code runs.

The FIX (`seeds/recount_analysis_realization.json` v1.1.0) makes two
ablation-proven, held-DATA decisions -- never a Python literal:

  (a) FLUENT PHRASING codebooks -- `TensionPhrasing{tension, phrase}` /
      `PairPhrasing{pair_key, phrase}` hold a genuinely fluent, already-cased,
      SHORT human phrase ('A Polite Hedge', 'Its Own Funding', ...).
      `analysis_say_conflicting_goals_fluent` / `analysis_say_temporal_
      conflict_fluent` join the reading's own tension/pair_key against the
      codebook and speak the held phrase; the ORIGINAL slug-based rules
      gained a `Not Exists <matching phrasing row>` guard, so the two rules
      per reading type are STRUCTURALLY mutually exclusive. Removing the
      phrasing ROW (not the rule) reverts to the exact prior mechanical
      slug phrasing -- an honest, provable fallback.
  (b) REDUNDANCY SUPPRESSION -- `analysis_suppress_superseded_temporal`
      marks a TemporalConflictReading `analysis_temporal_superseded=1.0` iff
      a HELD TropeReading already names the SAME actor+pair_key; both
      temporal say_* rules gained a `Not superseded` guard. A pair the
      agent's TropeSignature codebook was never taught a name for is NEVER
      suppressed -- it still gets recounted (fluently, if a PairPhrasing row
      exists; in slug form otherwise). Ablating the suppression rule alone
      (the say_* rules untouched) makes BOTH lines return.

Every produced clause is still `LanguageProduction.produce`'s own,
self-monitored `overt_speech` -- nothing here is templated. donkey=0
throughout.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
     tests/test_recount_analysis_fluency_migrated.py -p no:randomly -q
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
from domains import actor_goals as ag                          # noqa: E402
from domains.teach import teach                                # noqa: E402
from domains.language_world import LanguageWorld, teacher_stub  # noqa: E402
from domains.language_production import LanguageProduction     # noqa: E402
from scripts.language_test import training_bank                # noqa: E402

# The task's own fund->oppose article: a NAMED trope (Trojan Horse) fires for
# the SAME actor+pair the temporal-conflict layer also reads -- the
# redundancy case.
ANALYSIS_ARTICLE = ("The technology was funded by the oil company. "
                    "The technology was opposed by the oil company. "
                    "With all due respect, a spokesman called the critics misinformed.")

# A plain article with no goal-layer analysis at all -- the honesty control.
PLAIN_ARTICLE = ("Robert Levy, an attorney at ExxonMobil, will join the Justice Department. "
                 "He promoted the burning of fossil fuels. "
                 "Public Citizen said Big Oil captured the government.")

# An opposing-action pattern with NO named trope -- proves the temporal line
# survives (fluently, via a taught PairPhrasing row) when nothing supersedes it.
NO_TROPE_ARTICLE = ("The manager was hired by the company. "
                    "The manager was fired by the company.")


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
    """Remove a live rule by name -- the SAME helper the sibling recount
    test modules use."""
    live = list(agent.inner.export_rules())
    for i, r in enumerate(live):
        if r.get("name") == name:
            agent.inner.remove_rule(i)
            return True
    return False


def _remove_codebook_row(agent, node_type, **match_attrs):
    """Remove ONE held codebook NODE matching every given attr -- the SAME
    mechanical daemon-style tombstone test_recount_fluency_migrated.py uses,
    proving a fluency DECISION is the codebook ROW's, not a Python literal."""
    sub = agent.s
    for n in sub.nodes(node_type):
        at = sub.node(n)["attrs"]
        if all(at.get(k) == v for k, v in match_attrs.items()):
            agent.inner.remove_node(n)
            return True
    return False


def _teach_hire_fire(agent, *, with_phrasing=True):
    """Teach a NEW opposing-action pair the TropeSignature codebook was
    never given a name for -- the 'no trope names it' control. teach()'s
    disk write is blocked for the whole session by tests/conftest.py's
    autouse OZMA_SEED_PERSIST_DISABLED fixture; the in-graph add + category
    decision (never the real seeds/ dir) is what this exercises."""
    teach(agent, "OpposingActionPair",
         {"pair_key": "hire|fire", "note": "hires then fires the same object -- a reversed decision"})
    ag.ensure_opposing_pair_codebook(agent)
    if with_phrasing:
        teach(agent, "PairPhrasing", {"pair_key": "hire|fire", "phrase": "Its Own Hiring"})


# --------------------------------------------------------------------------- #
#  STEP 1 -- THE JABBERWOCK IS TOLD, AND FILES THE GAP ITSELF (over its own
#  NL interface, via the EXISTING gap-awareness faculty -- no new code).
# --------------------------------------------------------------------------- #
def test_the_jabberwock_files_the_analysis_fluency_gap_itself():
    """Tell the Jabberwock, in plain English, that its ANALYSIS prose reads
    slugs literally and repeats itself; it FILES that as a SelfConcern via
    the pre-existing `note_reported_gap` rule (a Mention resolving to a
    deficiency concept -- 'repeat'/'wrong' here -- AND a self-word 'you'/
    'your' is a self-reported deficiency), and SURFACES it when asked --
    BEFORE any of the fluency fix code below runs. This is a DIFFERENT,
    separately-filed gap from the surface-fluency one
    (test_recount_fluency_migrated.py's own gap test) -- distinct content,
    distinct SelfConcern, both held at once."""
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("noted", "acknowledgment")
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])

    report = ("Your analysis reads the tension and pair slugs literally instead of "
              "fluent English, and you repeat the same point twice -- that is wrong.")
    reply = a.converse(report, "statement")
    assert reply is not None
    assert "gap" in reply.lower()

    concerns = [n for n in a.s.nodes("SelfConcern")
               if a.s.node(n)["attrs"].get("source") == "explicit_report"
               and a.s.node(n)["attrs"].get("content") == report]
    assert len(concerns) == 1, "the report was not filed as exactly one SelfConcern"

    surfaced = a.converse("What gaps do you have?", "question")
    assert surfaced is not None
    assert report in surfaced or "slug" in surfaced.lower() or "repeat" in surfaced.lower()
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  (a) FLUENT PHRASING -- TENSION. Ablation-proven: remove the codebook ROW
#      (not the rule) and the SAME rule, now finding no row to join against,
#      reverts to the mechanical slug phrasing.
# --------------------------------------------------------------------------- #
def test_tension_realizes_as_a_fluent_phrase_not_a_raw_slug():
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    joined = " ".join(result["analysis_lines"])
    assert "A Polite Hedge" in joined, joined
    assert "Express Vs Avoid Social Cost" not in joined, joined
    assert all(result["accepted"]), result["accepted"]
    assert donkey["n"] == 0


def test_removing_the_tensionphrasing_row_reverts_to_the_slug():
    a, donkey = _fresh_agent_with_donkey()
    assert _remove_codebook_row(a, "TensionPhrasing", tension="express-vs-avoid-social-cost")
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    joined = " ".join(result["analysis_lines"])
    assert "Express Vs Avoid Social Cost" in joined, joined
    assert "A Polite Hedge" not in joined, joined
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  (a) FLUENT PHRASING -- PAIR_KEY, on the 'no trope names it' article (so the
#      temporal-conflict line is the ONLY thing realized for the pair --
#      isolates the pair-phrasing decision from the suppression decision).
# --------------------------------------------------------------------------- #
def test_pair_key_realizes_as_a_fluent_phrase_when_taught():
    a, donkey = _fresh_agent_with_donkey()
    _teach_hire_fire(a, with_phrasing=True)
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, NO_TROPE_ARTICLE,
                                  instruction="Recount what you read.", register="formal")
    joined = " ".join(result["analysis_lines"])
    assert "Its Own Hiring" in joined, joined
    assert "Hire Then Fire" not in joined, joined
    assert all(result["accepted"]), result["accepted"]
    assert donkey["n"] == 0


def test_pair_key_falls_back_to_slug_without_a_taught_phrasing():
    a, donkey = _fresh_agent_with_donkey()
    _teach_hire_fire(a, with_phrasing=False)
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, NO_TROPE_ARTICLE,
                                  instruction="Recount what you read.", register="formal")
    joined = " ".join(result["analysis_lines"])
    assert "Hire Then Fire" in joined, joined
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  (b) REDUNDANCY SUPPRESSION -- suppressed when a trope names the pair;
#      ablating the SUPPRESSION rule alone (not the realization rules)
#      brings BOTH lines back.
# --------------------------------------------------------------------------- #
def test_temporal_line_suppressed_when_a_trope_names_the_pair():
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    joined = " ".join(result["analysis_lines"])
    assert "Trojan Horse" in joined, joined
    assert "Its Own Funding" not in joined, joined
    assert "Fund Then Oppose" not in joined, joined
    assert len(result["analysis_lines"]) == 3          # conflicting-goals, trope, epistemic
    # the agent still HOLDS the temporal reading -- suppression is a
    # RENDERING decision, never a belief deletion.
    assert ag.held_temporal_conflicts(a)
    assert donkey["n"] == 0


def test_ablating_the_suppression_rule_returns_both_lines():
    a, donkey = _fresh_agent_with_donkey()
    assert _ablate_rule(a, "analysis_suppress_superseded_temporal")
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    joined = " ".join(result["analysis_lines"])
    assert "Trojan Horse" in joined, joined
    assert "Its Own Funding" in joined, joined          # the temporal line is BACK (fluent)
    assert len(result["analysis_lines"]) == 4
    assert all(result["accepted"]), result["accepted"]
    assert donkey["n"] == 0


def test_temporal_line_survives_when_no_trope_names_the_pair():
    """The suppression is KEYED on a trope existing for the SAME actor+pair --
    an opposing-action pattern the TropeSignature codebook was never taught a
    name for is never suppressed; it still gets recounted."""
    a, donkey = _fresh_agent_with_donkey()
    _teach_hire_fire(a, with_phrasing=True)
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, NO_TROPE_ARTICLE,
                                  instruction="Recount what you read.", register="formal")
    joined = " ".join(result["analysis_lines"])
    assert "Its Own Hiring" in joined, joined
    assert result["n_readings"] == 1
    assert len(result["analysis_lines"]) == 1
    assert ag.held_trope_readings(a) == []
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  HONESTY -- a plain article with no fired goal-layer analysis produces NO
#  analytical sentence, unaffected by any of the above.
# --------------------------------------------------------------------------- #
def test_plain_article_still_produces_no_analytical_sentences():
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, PLAIN_ARTICLE,
                                  instruction="Recount what you read.", register="formal")
    assert result["analysis_lines"] == []
    assert result["n_readings"] == 0
    assert result["analysis_prose"] == ""
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  PRODUCE-GENERATED, SELF-MONITOR ACCEPTED, donkey == 0.
# --------------------------------------------------------------------------- #
def test_fluent_analysis_lines_are_genuine_produce_output():
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    result = rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE,
                                  instruction="Recount what you read.", register="formal",
                                  actor_classes={"oil_company": "corporation"})
    n_surface = len(result["surface_lines"])
    analysis_productions = result["productions"][n_surface:]
    assert len(analysis_productions) == len(result["analysis_lines"]) == 3
    for line, production in zip(result["analysis_lines"], analysis_productions):
        assert production["overt_speech"] == line
        assert production["accepted"] is True
    assert donkey["n"] == 0


def test_donkey_zero_across_the_analysis_fluency_layer():
    a, donkey = _fresh_agent_with_donkey()
    world, prod = _fresh_voice(a)
    rf.analyse_what_read(a, world, prod, ANALYSIS_ARTICLE, instruction="Recount what you read.",
                         register="formal", actor_classes={"oil_company": "corporation"})
    _teach_hire_fire(a, with_phrasing=True)
    rf.analyse_what_read(a, world, prod, NO_TROPE_ARTICLE, instruction="Recount what you read.",
                         register="formal")
    rf.analyse_what_read(a, world, prod, PLAIN_ARTICLE, instruction="Recount what you read.",
                         register="casual")
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  NO TEMPLATING -- the new/changed Python (project_analysis_scene's codebook
#  wiring + bridging) is in the SAME function the existing audit already
#  covers; re-run it here for this module's own record, plus a source-level
#  check that the fluent phrase surfaces never appear as Python literals.
# --------------------------------------------------------------------------- #
def test_no_templated_sentence_construction_in_analysis_fluency_code():
    for fn in (rf.project_analysis_scene, rf.analyse_what_read):
        src = inspect.getsource(fn)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            assert not isinstance(node, ast.JoinedStr), \
                f"an f-string was found in {fn.__name__}"
        assert "say_agent'] +" not in src and 'say_agent"] +' not in src
        assert "say_patient'] +" not in src and 'say_patient"] +' not in src
    src = inspect.getsource(rf)
    tree = ast.parse(src)
    assert not any(isinstance(n, ast.JoinedStr) for n in ast.walk(tree))
    for literal in ("A Polite Hedge", "Its Own Funding", "Its Own Hiring"):
        assert literal not in src, \
            f"a fluent analysis phrase appears as a Python literal in recount_faculty.py: {literal!r}"
