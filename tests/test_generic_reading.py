"""test_generic_reading — READING WITHOUT SEEDED CODEBOOKS (the reader learns a
story's categories FROM the story, via the sd loop).

Two levers make the recognition absolutely generic:

  1. CHANGE-OF-STATE -> GENERIC EVENTIVE. A predication whose verb is EVENTIVE (a
     dynamic action/change) mints an SmEvent; a STATIVE does not. The decision is
     WordNet's OWN verb lexicographer-file classification (`eventive_membership`),
     NOT a seeded verb list. So the mercy/rescue verbs of 'The Lion and the Mouse'
     (caught/let/gnawed/freed) mint events -> the per-episode arcs FILL.
  2. TROPE/THEME -> GENERIC (sd-loop LEARNING). An arc OUTSIDE every seeded trope,
     yet carrying structural signal tokens, MINTS a LEARNED ShapeSignatureTrope
     quantum FROM its residual structure (the sd_mint_quantum precedent, one level
     up) + a GENERIC abstracted theme. tropes_teacher NAMES it (a label lookup);
     the RECOGNITION/MINT is generic.

HONEST partial (recorded in the report, not hidden): a GOALLESS tale (L&M) fills
its arcs with a generic event-sequence backbone -> setup + action roles (the full
setup/problem/action/resolution shape needs a goal/contrast/remedy signal a
goalless mercy fable does not emit); a LEARNED structural trope may be un-named /
coarse (the honest label + coarse structural theme say so).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_generic_reading.py -p no:randomly -q -s
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

from substrate.boot_core import boot_core                               # noqa: E402
from domains import dictionary_lexicon as dl                            # noqa: E402
from domains import reading_drive as rd                                # noqa: E402
from domains import situation_model_reader as smr                       # noqa: E402
from domains import trope_theme as tt                                   # noqa: E402
from domains import comprehension_reader as cr                          # noqa: E402
import jabberwock_produces_analysis_from_goal as jpafg                  # noqa: E402
import jabberwock_reads_generically as jrg                              # noqa: E402
import tests.test_order_n_nested_story as t2b                           # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  1. GENERIC EVENTIVE — the eventive/stative split is WordNet's, not a list.
# --------------------------------------------------------------------------- #
def test_eventive_vs_stative_is_wordnet_not_a_seeded_list():
    ag = _fresh()
    # mercy/rescue ACTION verbs (in NO seeded COS class) are EVENTIVE.
    for v in ("caught", "let", "gnawed", "freed", "spared", "begged"):
        m = smr.eventive_membership(ag, v)
        assert m["eventive"] is True, "%r should be eventive (WordNet %r)" % (v, m["lexname"])
    # a copular/existential STATIVE (WordNet verb.stative) is NOT eventive.
    for v in ("is", "resembles", "exists", "matters"):
        m = smr.eventive_membership(ag, v)
        assert m["stative"] is True and m["eventive"] is False and m["lexname"] == "verb.stative"


def test_generic_eventive_mints_events_stative_mints_nothing():
    ag = _fresh()
    # an eventive non-COS verb mints a GENERIC SmEvent (no canonical state delta).
    ing = smr.ingest_predication(ag, ["freed", "mouse", "lion"], t=1)
    assert ing["cos"] is False and ing["kind"] == "generic_event"
    assert any(ag.s.node(n)["attrs"].get("surface") == "freed"
               and ag.s.node(n)["attrs"].get("generic") == 1
               for n in ag.s.nodes("SmEvent"))
    # a STATIVE verb mints NO event at all.
    before = len(ag.s.nodes("SmEvent"))
    st = smr.ingest_predication(ag, ["resembles", "glass", "ice"], t=2)
    assert st["kind"] == "non_change_of_state"
    assert len(ag.s.nodes("SmEvent")) == before, "a stative minted a spurious event"


def test_generic_event_is_idempotent_across_rereads():
    # the streaming harness re-reads the grown prefix; a generic event must be held
    # ONCE (else Count(SmEvent) inflates and the material-triggered re-collapse breaks).
    ag = _fresh()
    smr.ingest_predication(ag, ["gnawed", "mouse", "ropes"], t=1)
    smr.ingest_predication(ag, ["gnawed", "mouse", "ropes"], t=1)
    n = [x for x in ag.s.nodes("SmEvent")
         if ag.s.node(x)["attrs"].get("surface") == "gnawed"]
    assert len(n) == 1, "a re-read duplicated the generic event"


# --------------------------------------------------------------------------- #
#  1b. LION & MOUSE — the per-episode arcs FILL from the real events (VERBATIM).
# --------------------------------------------------------------------------- #
def test_lion_mouse_per_episode_arcs_fill_from_generic_events():
    out = jrg.read_lion_mouse()
    assert out["depth"] == 2 and len(out["units"]) == 2
    ep1, ep2 = out["units"]
    r1 = [(r.get("role"), r.get("order")) for r in ep1["narrative_roles"]]
    r2 = [(r.get("role"), r.get("order")) for r in ep2["narrative_roles"]]
    # HONEST partial: a goalless mercy/rescue tale fills its arc with a generic
    # event-sequence backbone -> setup + action (NOT the full problem/resolution
    # shape, which needs a goal/contrast/remedy signal L&M does not emit). But the
    # arcs are NO LONGER EMPTY -- they carry real roles read off the real events.
    assert r1 == [("setup", 0), ("action", 1)]
    assert r2 == [("setup", 1), ("action", 2)]
    # each episode's protagonist is the event AGENT (ep1 lion acts; ep2 mouse acts).
    assert {r.get("entity") for r in ep1["narrative_roles"]} == {"lion"}
    assert {r.get("entity") for r in ep2["narrative_roles"]} == {"mouse"}
    # the cross-episode reciprocity spanning theme still composes.
    assert out["spanning_theme"]["theme"] == "reciprocity"
    assert out["spanning_theme"]["token"] == "RETURN_ACTION"


# --------------------------------------------------------------------------- #
#  2. NOVEL FABLE — comprehended + a LEARNED trope/theme minted from structure.
# --------------------------------------------------------------------------- #
def test_novel_fable_learns_a_trope_from_structure():
    nov = jrg.read_novel_fable(jrg.FOX_HEN)
    # comprehended: generic events + a real arc (the goal + problem role form).
    assert ("problem", 1, "fox") in nov["roles"] and ("setup", 0, "fox") in nov["roles"]
    res = nov["trope_theme"]
    assert res, "the novel fable produced no trope/theme result"
    fox = next(r for r in res if r["entity"] == "fox")
    # it instantiates NO seeded trope (outside every seeded codebook) -> LEARNED.
    assert fox["tokens"] == ["TROPE_PROBLEM"]
    learned = fox.get("learned")
    assert learned is not None and learned.get("minted") is True
    names = [tr.get("name") for tr in fox["tropes"]]
    assert names == ["LEARNED_PROBLEM"], "the learned trope was not minted from structure"
    # HONEST quality: the learned structural trope's LABEL is self-authored/coarse
    # (tropes_teacher supplies a citable name only when its corpus hits) and the
    # theme is an ABSTRACTED structural pattern, not a hand-authored moral.
    lab = fox["tropes"][0]["label"]
    assert lab["source"] in ("self_authored", "tvtropes")
    assert fox["theme"] is not None
    line = fox["theme"]["lines"][0]
    assert "learned from this story" in line and "coarse" in line


def test_learned_trope_is_a_persistent_codebook_quantum():
    # dynamic quantization: the mint GROWS the ShapeSignatureTrope codebook (a new
    # quantum whose signature IS the residual structure) -- the sd_mint_quantum
    # precedent, one level up. It is minted ONCE (idempotent codebook growth).
    ag = _fresh()
    tt.ensure_codebook(ag)
    sub, native = tt._resolve(ag)
    before = len(ag.s.nodes("ShapeSignatureTrope"))
    a = tt._mint_learned_trope(ag, sub, native, ["TROPE_PROBLEM", "TROPE_RESOLUTION"])
    assert a["minted"] is True and len(ag.s.nodes("ShapeSignatureTrope")) == before + 1
    b = tt._mint_learned_trope(ag, sub, native, ["TROPE_PROBLEM", "TROPE_RESOLUTION"])
    assert b["minted"] is False and len(ag.s.nodes("ShapeSignatureTrope")) == before + 1


# --------------------------------------------------------------------------- #
#  3. CROW — byte-identical (COS canon + seeded tropes still fully cover it).
# --------------------------------------------------------------------------- #
def test_crow_report_byte_identical():
    rep = jpafg.analyse(jrg.CROW)["report"]
    assert rep == t2b._CROW_REPORT, (
        "generic eventive / sd-loop trope learning changed the crow report -- the "
        "crow's COS verbs must still resolve to their canon delta rules and its arc "
        "must stay fully covered by the seeded tropes (nothing learned)")


# --------------------------------------------------------------------------- #
#  4. GRAPH-NATIVE AUDIT — no seeded COS/trope verb literal drives the mint; the
#  eventive test is WordNet; the trope mint is the sd_mint_quantum precedent;
#  no import re; donkey = 0.
# --------------------------------------------------------------------------- #
def test_eventive_mint_is_wordnet_not_a_hardcoded_verb_literal():
    # the eventive-vs-stative gate is WordNet's lexname (eventive_membership ->
    # _verb_lexname reads wn.synsets(...).lexname()), NOT a Python verb list.
    lex_src = inspect.getsource(smr._verb_lexname)
    assert "wordnet" in lex_src and "lexname()" in lex_src
    ev_src = inspect.getsource(smr.eventive_membership)
    assert "_verb_lexname" in ev_src and "verb.stative" in ev_src
    # the generic-event mint in ingest_predication is GATED on eventive_membership,
    # never on a literal action-verb comparison.
    ing_src = inspect.getsource(smr.ingest_predication)
    assert "eventive_membership(agent, rel)" in ing_src
    for banned in ("caught", "gnawed", "freed", "spared", "mercy", "rescue"):
        assert banned not in ing_src, "ingest_predication names a fable verb literal %r" % banned


def test_learned_trope_mint_is_sd_mint_quantum_not_a_trope_literal():
    # the learned trope is the sd_mint_quantum precedent (a residual mints a codebook
    # quantum); its NAME is DERIVED from the residual tokens, never a hardcoded trope.
    mint_src = inspect.getsource(tt._mint_learned_trope)
    assert 'add_node(_CODEBOOK_TYPE' in mint_src and '"learned": 1' in mint_src
    name_src = inspect.getsource(tt._learned_trope_name)
    # the driver never compares against / returns a hardcoded trope NAME.
    drv_src = inspect.getsource(tt.recognize_tropes_and_theme) + inspect.getsource(tt._decode_and_mint)
    for banned in ("INGENUITY_OVER_STRENGTH", "PERSISTENCE_PAYS", "NECESSITY_INVENTION"):
        assert banned not in drv_src and banned not in mint_src and banned not in name_src


def test_source_audit_no_regex_no_donkey():
    for mod in (smr, tt, cr, jrg):
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                assert not any(a.name == "re" for a in n.names), "import re in %s" % mod.__name__
            if isinstance(n, ast.ImportFrom):
                assert n.module != "re", "from re import ... in %s" % mod.__name__
        for banned in ("openai", "anthropic", "requests.post", "call_model", "self_teacher"):
            assert banned not in src, "donkey token %r in %s" % (banned, mod.__name__)


def test_reading_is_driven_by_cognitive_tick():
    # the reading path rides the agent's cognitive tick (no hand-called run_rules /
    # fire_reflexes in the driver) -- the generic changes did not add a Python loop.
    for fn in (rd.run_reading_flow, rd.run_nested_reading_flow):
        drv = inspect.getsource(fn)
        assert "_tick_reading(" in drv
        assert "run_rules(" not in drv and "fire_reflexes(" not in drv
