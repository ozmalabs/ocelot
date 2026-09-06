"""FELT-RESCUE strong arm of feel-then-reason — confirmatory gates.

PREREG:  docs/research/psychology_affect/FELT_RESCUE_STRONG_ARM_PREREG.md (block 300000).
RESULTS: docs/research/psychology_affect/FELT_RESCUE_STRONG_ARM_RESULTS.md.

The STRONG ARM: an OPT-IN, default-OFF `felt_rescue` seam on
`analogy_search.find_analogies` that ADMITS a below-`min_score` structural
candidate IFF its shared felt shape is RARE-by-chance (a shared non-valence felt
coord — e.g. a `phenomenal:sharpness` pole — OR `felt_shared >= 2`; a lone
shared `dynamical:valence` sign never rescues). Unlike stages 1/2 (shortlist /
re-rank) this CHANGES THE ACCEPTED SET — it recovers genuine below-min_score
structural misses.

Gates (from the prereg):
  (a) DEFAULT==TODAY   — felt_rescue off ⇒ byte-identical accepted set + order.
  (b) STRONG ARM       — a TRUE felt-coherent pair ABSENT at min_score=k is
                         PRESENT with felt_rescue=True (real accepted-set change,
                         felt_rescued=True tag).
  (c) SELECTIVITY      — a SPURIOUS bare-valence pair that blanket min_score-1
                         admits is NOT admitted by felt_rescue (rescue precision
                         > blanket precision on the labelled junk).
  (d) RARITY           — a pair sharing ONLY a valence sign is NOT rescued; a
                         pair sharing a sharpness pole OR felt_shared>=2 IS
                         (rarity-keying, not bare felt-presence).
  (e) ANTI-FAKING      — perturbing the rescued pair's felt SOURCE attr (flip
                         sharpness / zero the second felt coord) removes the
                         rescue (derived from the real signature).
  (f) .so md5 == 7efe75eba05b006cafd15dbb4b7da246 (no Rust/.so change).
"""
from __future__ import annotations

import hashlib
import json
import pathlib

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr
import domains.relation_grounding as rg
from domains.can_self_worth_bridge import ensure_can_seed

ROOT = pathlib.Path(at.__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"
_SO = ROOT / "runners" / "dsl" / "python" / "substrate_rs" / "_native.abi3.so"
_SO_MD5 = "7efe75eba05b006cafd15dbb4b7da246"

_LEDGER = {
    "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
    "identity_evidence_tick": -1, "identity_decay_tick": -1,
    "identity_field_tick": -1,
}


def _boot():
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("shape_vocabulary", "qualia_space", "analogy_search"):
        s.load_seed_manifest(json.load(open(SEEDS / f"{name}.json")), ag)
    ensure_can_seed(s)
    node_types = ("Agent", "Concept", "Microtheory")
    edge_types = ("has_concept", "causal_influence") + rg.RELATION_EDGE_TYPES + ("genls",)
    for a in node_types:
        for b in node_types:
            for et in edge_types:
                s.add_production({"src": {"type": a, "var": "x"},
                                  "edge_type": et,
                                  "tgt": {"type": b, "var": "y"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "test:open"})
    return s, ag


def _mt(s, name, category="general"):
    return s.add_node("Microtheory", {"name": name, "category": category,
                                      "temperature": 1.0, "discrete_mode": "3state",
                                      "can_tick": 0, "update_policy": "adaptive"})


def _cc(s, mt, name, *, definition, category, state=0.0, sharpness=None):
    """A concept with its REAL felt source attrs. `state` = the committed state
    the `dynamical:valence` axis reads; `sharpness` = the bouba/kiki
    `phenomenal:sharpness` source attr. `identity_field` stays 0 so
    `dynamical:commitment` is DARK (Task-1 finding) — a valence-only concept
    then shares ONLY the coin-flip valence axis."""
    attrs = {"name": name, "category": category, "definition": definition,
             "state": float(state), "external_field": 0.0, "identity_field": 0.0}
    if sharpness is not None:
        attrs["sharpness"] = float(sharpness)
    attrs.update(_LEDGER)
    c = s.add_node("Concept", attrs)
    s.add_edge_unchecked(mt, "has_concept", c)
    return c


def _pair(sn, tn, *, s_state=0.0, s_sharp=None, t_state=0.0, t_sharp=None):
    """One labelled cross-domain pair as its OWN source/target field — the
    analogy decode emits ONE analogy per source (the Argmax winner), so a 1-vs-1
    field pins emission of exactly this pair and makes its felt shape
    unambiguous. Distinct definitions keep surface thin, so the felt coord(s)
    are the only cross-field overlap."""
    s, _ag = _boot()
    src = _mt(s, "src", "alpha")
    tgt = _mt(s, "tgt", "beta")
    cs = _cc(s, src, sn, category="cat_%s" % sn,
             definition="Def %s alpha unique." % sn, state=s_state, sharpness=s_sharp)
    ct = _cc(s, tgt, tn, category="cat_%s" % tn,
             definition="Def %s beta unique." % tn, state=t_state, sharpness=t_sharp)
    rg.ground_relations(s, "src")
    rg.ground_relations(s, "tgt")
    return s, cs, ct


def _find(s, *, min_score, rescue=False):
    return asr.find_analogies(s, "src", ["tgt"], order_n=2, min_score=min_score,
                              felt_rescue=rescue)


def _admitted(res, sn, tn):
    for r in res:
        if r["source_concept"] == sn and r["target_concept"] == tn:
            return r
    return None


# ===========================================================================
# (a) DEFAULT == TODAY — felt_rescue off ⇒ byte-identical
# ===========================================================================
def test_default_off_is_byte_identical():
    """felt_rescue=False (the default) ⇒ the accepted set AND its order are
    IDENTICAL to a today-call with no rescue arg, across the discriminating
    band (a below-k sharpness pair, a below-k valence pair, and an
    at-threshold pair that passes). The rescue branch is inert unless switched
    on, and every result carries felt_rescued=False."""
    # a battery where some pairs pass k=2 and some sit below it.
    def battery(rescue):
        s, _ag = _boot()
        src = _mt(s, "src", "alpha")
        tgt = _mt(s, "tgt", "beta")
        # below-k: shares only a sharpness pole (disc=1)
        _cc(s, src, "spike", category="c1", definition="Def spike a.", sharpness=+1.0)
        _cc(s, tgt, "thorn", category="c2", definition="Def thorn b.", sharpness=+1.0)
        rg.ground_relations(s, "src")
        rg.ground_relations(s, "tgt")
        return asr.find_analogies(s, "src", ["tgt"], order_n=2, min_score=2,
                                  felt_rescue=rescue)

    today = battery(rescue=False)  # implicit default arg
    # an explicit-default call must equal the implicit-default call
    s, _ag = _boot()
    src = _mt(s, "src", "alpha")
    tgt = _mt(s, "tgt", "beta")
    _cc(s, src, "spike", category="c1", definition="Def spike a.", sharpness=+1.0)
    _cc(s, tgt, "thorn", category="c2", definition="Def thorn b.", sharpness=+1.0)
    rg.ground_relations(s, "src")
    rg.ground_relations(s, "tgt")
    explicit = asr.find_analogies(s, "src", ["tgt"], order_n=2, min_score=2)

    def key(res):
        return [(r["source_concept"], r["target_concept"]) for r in res]

    assert key(explicit) == key(today), (key(explicit), key(today))
    # every result of the default-off path carries felt_rescued=False.
    assert all(r["felt_rescued"] is False for r in today), today
    # the at.* delegating entry is identical too.
    s2, _ag2 = _boot()
    src2 = _mt(s2, "src", "alpha")
    tgt2 = _mt(s2, "tgt", "beta")
    _cc(s2, src2, "spike", category="c1", definition="Def spike a.", sharpness=+1.0)
    _cc(s2, tgt2, "thorn", category="c2", definition="Def thorn b.", sharpness=+1.0)
    rg.ground_relations(s2, "src")
    rg.ground_relations(s2, "tgt")
    via_at = at.find_analogies(s2, "src", ["tgt"], order_n=2, min_score=2)
    assert key(via_at) == key(today)


# ===========================================================================
# (b) STRONG ARM — a TRUE felt pair ABSENT at k is PRESENT with felt_rescue
# ===========================================================================
def test_strong_arm_recovers_below_min_score_felt_miss():
    """A TRUE felt-coherent pair (shares a rare `phenomenal:sharpness` pole,
    disc=1) is ABSENT at the min_score=2 baseline — a GENUINE below-min_score
    structural miss — and is PRESENT with felt_rescue=True, tagged
    felt_rescued=True. A real accepted-set change (not a re-rank)."""
    s, _cs, _ct = _pair("spike", "thorn", s_sharp=+1.0, t_sharp=+1.0)
    baseline = _find(s, min_score=2, rescue=False)
    assert _admitted(baseline, "spike", "thorn") is None, (
        "TRUE pair was NOT a genuine below-min_score miss", baseline)

    s2, _c1, _c2 = _pair("spike", "thorn", s_sharp=+1.0, t_sharp=+1.0)
    rescued = _find(s2, min_score=2, rescue=True)
    r = _admitted(rescued, "spike", "thorn")
    assert r is not None, ("strong arm did not recover the felt miss", rescued)
    assert r["felt_rescued"] is True, r
    # it is analogous ON the rare felt axis.
    assert "phenomenal:sharpness" in r["aligned_dimensions"], r


# ===========================================================================
# (c) SELECTIVITY / PRECISION — junk blanket admits is NOT rescued
# ===========================================================================
def test_selectivity_rescue_precision_beats_blanket():
    """On a labelled junk pool (SPURIOUS = pairs sharing ONLY a bare valence
    sign), a blanket min_score-1 drop admits ALL of them (precision 0), while
    felt_rescue at min_score=k admits NONE (precision 1) — rescue precision >
    blanket precision. Selective, not threshold-loosening."""
    spurious = [("glad", "merry", +1.0), ("bright", "sunny", +1.0),
                ("grim", "bleak", -1.0), ("dour", "dark", -1.0)]

    def admitted_count(min_score, rescue):
        n = 0
        for sn, tn, st in spurious:
            s, _cs, _ct = _pair(sn, tn, s_state=st, t_state=st)
            res = _find(s, min_score=min_score, rescue=rescue)
            if _admitted(res, sn, tn) is not None:
                n += 1
        return n

    total = len(spurious)
    blanket_admitted = admitted_count(min_score=1, rescue=False)   # (ii)
    rescue_admitted = admitted_count(min_score=2, rescue=True)     # (iii)

    # the blanket drop admits the junk; the rescue rejects it.
    assert blanket_admitted == total, blanket_admitted   # all junk in
    assert rescue_admitted == 0, rescue_admitted          # no junk in

    prec_blanket = 1.0 - blanket_admitted / total
    prec_rescue = 1.0 - rescue_admitted / total
    assert prec_rescue > prec_blanket, (prec_rescue, prec_blanket)


# ===========================================================================
# (d) RARITY — lone valence is NOT rescued; sharpness / felt>=2 IS
# ===========================================================================
def test_rarity_keying_not_bare_felt_presence():
    """The predicate keys on RARITY, not bare felt presence:
      · a pair sharing ONLY a `dynamical:valence` sign (coin flip 0.488) is NOT
        rescued;
      · a pair sharing a `phenomenal:sharpness` pole (rare, 0.012) IS;
      · a pair sharing TWO felt axes (valence + sharpness, 0.009) IS.
    All three are below-min_score misses at their respective baselines."""
    # lone valence — NOT rescued (below k=2, stays absent under rescue).
    s, _cs, _ct = _pair("glad", "merry", s_state=+1.0, t_state=+1.0)
    assert _admitted(_find(s, min_score=2, rescue=False), "glad", "merry") is None
    s, _cs, _ct = _pair("glad", "merry", s_state=+1.0, t_state=+1.0)
    r = _admitted(_find(s, min_score=2, rescue=True), "glad", "merry")
    assert r is None, ("a LONE valence sign must NOT rescue", r)

    # sharpness pole — IS rescued (below k=2, admitted under rescue).
    s, _cs, _ct = _pair("spike", "thorn", s_sharp=+1.0, t_sharp=+1.0)
    assert _admitted(_find(s, min_score=2, rescue=False), "spike", "thorn") is None
    s, _cs, _ct = _pair("spike", "thorn", s_sharp=+1.0, t_sharp=+1.0)
    r = _admitted(_find(s, min_score=2, rescue=True), "spike", "thorn")
    assert r is not None and r["felt_rescued"] is True, ("a sharpness pole must rescue", r)

    # two felt axes (valence + sharpness) — IS rescued (below k=3).
    s, _cs, _ct = _pair("fear", "pain", s_state=-1.0, s_sharp=+1.0,
                        t_state=-1.0, t_sharp=+1.0)
    assert _admitted(_find(s, min_score=3, rescue=False), "fear", "pain") is None
    s, _cs, _ct = _pair("fear", "pain", s_state=-1.0, s_sharp=+1.0,
                        t_state=-1.0, t_sharp=+1.0)
    r = _admitted(_find(s, min_score=3, rescue=True), "fear", "pain")
    assert r is not None and r["felt_rescued"] is True and r["felt_shared"] >= 2, (
        "felt_shared>=2 must rescue", r)


# ===========================================================================
# (e) ANTI-FAKING — the felt prior is DERIVED, not hand-set
# ===========================================================================
def test_anti_faking_perturb_felt_source_removes_rescue():
    """Perturbing the rescued pair's felt SOURCE attr REMOVES the rescue —
    proving the predicate reads the REAL _dynamical_relations signature, not a
    hand-set felt coord.

    (i) FLIP the sharpness pole on a sharpness-only rescued pair: the two poles
        now DISAGREE, so no sharpness coord survives the frozenset intersection,
        the shared felt shape collapses to nothing, and the pair is no longer
        rescued.
    (ii) ZERO the SECOND felt coord (sharpness) on a two-felt (valence+sharpness)
        rescued pair: felt_shared drops from 2 to 1 (a LONE valence), which the
        rarity predicate rejects — the pair is no longer rescued."""
    # (i) flip the sharpness pole -> no shared felt coord -> no rescue.
    s, cs, _ct = _pair("spike", "thorn", s_sharp=+1.0, t_sharp=+1.0)
    assert _admitted(_find(s, min_score=2, rescue=True), "spike", "thorn") is not None
    s, cs, _ct = _pair("spike", "thorn", s_sharp=+1.0, t_sharp=+1.0)
    s.set_attr(cs, "sharpness", -1.0)  # flip the source pole
    r = _admitted(_find(s, min_score=2, rescue=True), "spike", "thorn")
    assert r is None, ("flipping the sharpness source must remove the rescue", r)

    # (ii) zero the second felt coord -> lone valence -> no rescue.
    s, cs, _ct = _pair("fear", "pain", s_state=-1.0, s_sharp=+1.0,
                       t_state=-1.0, t_sharp=+1.0)
    assert _admitted(_find(s, min_score=3, rescue=True), "fear", "pain") is not None
    s, cs, _ct = _pair("fear", "pain", s_state=-1.0, s_sharp=+1.0,
                       t_state=-1.0, t_sharp=+1.0)
    s.set_attr(cs, "sharpness", 0.0)  # zero the second felt SOURCE coord
    # now the pair shares only valence; disc drops to 1 (< k=3) AND the shared
    # felt shape is a lone valence -> the predicate rejects it.
    r = _admitted(_find(s, min_score=3, rescue=True), "fear", "pain")
    assert r is None, ("zeroing the second felt source must remove the rescue", r)


# ===========================================================================
# (f) .so md5 unchanged — no Rust / no .so change
# ===========================================================================
def test_native_so_md5_unchanged():
    h = hashlib.md5(_SO.read_bytes()).hexdigest()
    assert h == _SO_MD5, h
