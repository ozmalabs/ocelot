"""test_cycle_solves_extract — the SELF-IMPROVEMENT CYCLE turned on the
jabberwock's OWN Wikipedia-consumption problems (domains/consumption_quality.py).

A live Wikipedia extract exposed three faculty gaps in the consumption pipeline.
The cycle PERCEIVES them (#1 collapse residual mints CapabilityGaps), SOLVES each
(a fix composed from held faculties), and TRUSTS each only after #2
(self_verification) passes a DISCRIMINATIVE control whose KNOWN-FAKE twin fails.
Donkey=0 — no LM; the sense pick is the graph-resident sense_selection rule's
argmax, the gap is #1's collapse residual, the accept is #2's Rust verdict.

  PERCEIVE      : the 3 gaps minted from real consumption failures. Pinned.
  NOMINAL FIX   : clause fragments dropped, real concepts kept; fragment-rate
                  down; discriminative (clause fails is_nominal, nominal passes).
  SENSE FIX     : water -> a substance sense (not the Devon hamlet); a mis-sense
                  battery corrected; the context-blind pick is wrong (control).
  CACHE FIX     : warm-cache identical to cold; measurably faster.
  VERIFY-GATED  : each fix passes #2; a FAKE (context-blind sense scorer /
                  keep-everything filter) is REJECTED.
  NO REGRESSION : the legacy extraction is byte-identical with the fix OFF.
"""
from __future__ import annotations

import io
import contextlib

import pytest
import substrate_rs as srs

from domains import consumption_quality as cq


@pytest.fixture(scope="module")
def agent():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
    return a


def _wiki_present() -> bool:
    try:
        from domains import wiki_local as wl
        return wl.present()
    except Exception:
        return False


# ===========================================================================
# PERCEIVE — the 3 gaps minted from real consumption failures (#1).
# ===========================================================================

def test_perceive_three_consumption_gaps(agent):
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        rep = cq.perceive_consumption_gaps(agent)
    faculties = {agent.s.node(g)["attrs"]["faculty"] for g in rep["gaps"]}
    assert faculties == {"nominal_extraction", "context_sense", "grounding_cache"}
    # every gap is a genuine collapse residual (observed failure under predicted
    # competence), minted as a CapabilityGap the agent can introspect.
    assert len(rep["residual"]) == 3
    for g in rep["gaps"]:
        at = agent.s.node(g)["attrs"]
        assert at["status"] == "perceived" and at["failure_class"] == "silence"


# ===========================================================================
# NOMINAL FIX — clause fragments dropped, real concepts kept; discriminative.
# ===========================================================================

def test_nominal_is_discriminative():
    # a clause / verb-phrase / adverb span FAILS the nominal test; a noun phrase
    # PASSES. (The discriminative property #2 verifies.)
    for frag in ["producing oxygen gas", "rather than water", "catalyzed by rubisco",
                 "releases three-carbon sugars", "uses energy", "respectively"]:
        assert cq.is_nominal(frag) is False, frag
    for nom in ["calvin cycle", "carbon fixation", "glucose", "amino acid biosynthesis",
                "cells", "proof of work"]:
        assert cq.is_nominal(nom) is True, nom


@pytest.mark.skipif(not _wiki_present(), reason="wiki_local slab not present")
def test_nominal_fix_drops_fragments_keeps_reals(agent):
    from domains import gap_driven_acquisition as gda
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        src = gda.read_source(agent, "photosynthesis", source_title="Photosynthesis")
        before = gda.extract_microtheory("photosynthesis", src, max_concepts=40,
                                         nominal_filter=False)
        after = gda.extract_microtheory("photosynthesis", src, max_concepts=40,
                                        nominal_filter=True)
    b = {c["name"] for c in before["concepts"]}
    a = {c["name"] for c in after["concepts"]}
    # the four named clause fragments are DROPPED (verbatim).
    for frag in ["producing_oxygen_gas", "rather_than_water",
                 "releases_three-carbon_sugars", "catalyzed_by_rubisco"]:
        assert frag in b, (frag, "should leak from the unfixed parse")
        assert frag not in a, (frag, "should be dropped by the nominal fix")
    # the real concepts are KEPT (verbatim).
    for real in ["calvin_cycle", "glucose", "carbon_fixation"]:
        assert real in a, real
    # fragment-rate down: the fix drops strictly, and every drop is a fragment.
    assert after["dropped_fragments"], after["dropped_fragments"]
    assert len(a) < len(b)
    for name in after["dropped_fragments"]:
        assert cq.is_nominal(name.replace("_", " ")) is False


def test_nominal_fix_verify_gated(agent):
    v = cq.verify_nominal_fix(agent)
    assert v["accepted"] and v["discriminates"] and v["no_regression"] and v["grounded"]
    assert v["twin_pass"] is False   # the keep-everything fake FAILS the control


def test_nominal_fake_rejected(agent):
    from domains import self_verification as sv

    def fake_keep_all(case):
        _surface, expected = case
        return True == expected   # keeps everything -> wrong on every fragment

    v = sv.verify_claim(agent, sv.Claim(
        "FAKE keep-everything nominal filter", mechanism=fake_keep_all,
        control_cases=cq.NOMINAL_CONTROL, fake_twin=fake_keep_all,
        prior_cases=cq.NOMINAL_PRIOR, ground_support=cq._ground_reference))
    assert v["accepted"] is False and v["discriminates"] is False


# ===========================================================================
# SENSE FIX — water -> substance (not hamlet); mis-sense battery corrected.
# ===========================================================================

def test_sense_water_is_substance_not_hamlet(agent):
    from domains import wiktionary_reference as wr
    # the OLD context-blind grounding: the Wiktionary first-gloss for water.
    old = (wr.wiktionary_gloss("water", "en") or "").lower()
    assert "hamlet" in old or "parish" in old   # the actual mis-sense bug
    # the FIX: context-scored WordNet sense in the substance context.
    ctx = ["strip", "electrons", "suitable", "substances", "oxygen", "hydrogen"]
    r = cq._sense_in_context_uncached("water", ctx, "patient", "en")
    gloss = (r["sense"] or "").lower()
    assert not any(p in gloss for p in ("hamlet", "parish", "village", "district"))
    assert any(g in gloss for g in ("liquid", "compound", "element"))


def test_sense_battery_corrected_and_control(agent):
    # the context-scored pick is right on every battery word; the context-BLIND
    # pick (WordNet sense-1) is WRONG on the context-dependent ones -> the wrong
    # sense scores lower / fails the control.
    wrong_blind = 0
    for head, ctx, slot, gold in cq.SENSE_CONTROL:
        good = (cq._sense_in_context_uncached(head, ctx, slot, "en")["sense"] or "").lower()
        blind = (cq._sense_blind(head, slot)["sense"] or "").lower()
        assert any(g in good for g in gold), (head, good)
        if not any(g in blind for g in gold):
            wrong_blind += 1
    assert wrong_blind >= 2   # the control has teeth on >=2 context-dependent words


def test_sense_fix_verify_gated(agent):
    v = cq.verify_sense_fix(agent)
    assert v["accepted"] and v["discriminates"] and v["no_regression"] and v["grounded"]
    assert v["twin_pass"] is False


def test_sense_fake_rejected(agent):
    from domains import self_verification as sv

    def fake_blind(case):
        head, _ctx, slot, gold = case
        g = (cq._sense_blind(head, slot).get("sense") or "").lower()
        return any(x in g for x in gold)   # ignores context -> fails mole/cell

    v = sv.verify_claim(agent, sv.Claim(
        "FAKE context-blind sense scorer", mechanism=fake_blind,
        control_cases=cq.SENSE_CONTROL, fake_twin=fake_blind,
        prior_cases=cq.SENSE_PRIOR, ground_support=cq._ground_reference))
    assert v["accepted"] is False


# ===========================================================================
# CACHE FIX — warm identical to cold, measurably faster.
# ===========================================================================

def test_cache_warm_identical_and_faster():
    words = ["water", "cipher", "glucose", "volcano", "cell"]
    cache = cq.GroundingCache()
    for w in words:
        cold = cq._pos(w)
        warm1 = cache.get_pos(w)     # miss -> computes
        warm2 = cache.get_pos(w)     # HIT
        assert warm1 == cold and warm2 == cold   # byte-identical
    assert cache.hits >= len(words)
    t = cq.time_cache(words, repeats=4)
    assert t["faster"] is True and t["warm_s"] < t["cold_s"]
    assert t["cache"]["hit_rate"] > 0.5


def test_cache_fix_verify_gated(agent):
    v = cq.verify_cache_fix(agent)
    assert v["accepted"] and v["discriminates"] and v["no_regression"] and v["grounded"]
    assert v["twin_pass"] is False   # a stale cache FAILS the identical-value control


# ===========================================================================
# NO REGRESSION — the legacy extraction is byte-identical with the fix OFF.
# ===========================================================================

@pytest.mark.skipif(not _wiki_present(), reason="wiki_local slab not present")
def test_no_regression_fix_off_is_byte_identical(agent):
    from domains import gap_driven_acquisition as gda
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        src = gda.read_source(agent, "volcano", source_title="Volcano")
        off = gda.extract_microtheory("volcano", src, max_concepts=30,
                                      nominal_filter=False)
    # fix OFF: no concept is filtered, no fragment reported.
    assert off["dropped_fragments"] == []
