"""FEEL-THEN-REASON two-stage analogical matcher — confirmatory gates.

PREREG: docs/research/psychology_affect/FEEL_THEN_REASON_PREREG.md (block 299000).

Two OPT-IN, default-OFF seams on `analogy_search.find_analogies`:
  · STAGE 1 `felt_shortlist_k` — cheap felt sub-signature prunes each probe's
    decode scope to the k nearest-felt target parts (fewer AntiUnify firings +
    fewer full edge-enumerating signature builds).
  · STAGE 2 `felt_bias` — a felt-aware RANK_KEY variant surfaces a felt
    (dynamical:/phenomenal:) correspondence above a merely surface one among
    matches tied on the deeper structural tiers.

Gates (from the prereg):
  (a) DEFAULT==TODAY — both off ⇒ byte-identical find_analogies (same analogy
      list + same order) as a k=None / felt_bias=False baseline.
  (b) SPEED — felt_shortlist_k<M yields a SMALLER firing proxy than k=None while
      the top true analogy is still found (firings drop AND recall retained).
  (c) POWER — felt_bias=True ranks a real felt cross-domain analogy ABOVE where
      felt_bias=False puts it (a genuine below-rank miss lifted).
  (d) ANTI-FAKING — perturbing a concept's felt SOURCE attr changes BOTH the
      felt shortlist AND the felt rank (the prior is DERIVED from the real
      _dynamical_relations signature, not hand-set).
  (e) .so md5 == 7efe75eba05b006cafd15dbb4b7da246 (no Rust/.so change).
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
from domains.self_improvement_loop import relax

ROOT = pathlib.Path(at.__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"
_SO = ROOT / "runners" / "dsl" / "python" / "substrate_rs" / "_native.abi3.so"
_SO_MD5 = "7efe75eba05b006cafd15dbb4b7da246"

_LEDGER = {
    "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
    "identity_evidence_tick": -1, "identity_decay_tick": -1,
    "identity_field_tick": -1,
}


class _Agent:
    def __init__(self, sub):
        self.s = sub
        self.agent = sub.nodes("Agent")[0]


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


def _cc(s, mt, name, *, definition, category, external_field=0.0):
    attrs = {"name": name, "category": category, "definition": definition,
             "state": 0.0, "external_field": float(external_field),
             "identity_field": 0.0}
    attrs.update(_LEDGER)
    c = s.add_node("Concept", attrs)
    s.add_edge_unchecked(mt, "has_concept", c)
    return c


def _couple(s, a, b, w):
    s.add_edge(a, "causal_influence", b, {"weight": float(w)})
    s.add_edge(b, "causal_influence", a, {"weight": float(w)})


def _relax(s, mt, *, ticks=16):
    relax(s, mt)
    for i in range(ticks):
        s.set_attr(mt, "can_tick", i + 1)
        asr.crystallize(_Agent(s))


def _order_key(results):
    """The identity of a result list = the ORDERED sequence of (source, target)
    pairs. Byte-identity of the analogy verdict, insensitive to the extra
    felt_shared bookkeeping key."""
    return [(r["source_concept"], r["target_concept"]) for r in results]


# --- battery builders -------------------------------------------------------
def _speed_battery():
    """A source with one distinctive shape + a felt-spread target battery, so
    the true structural match sits among felt-distant distractors."""
    s, _ag = _boot()
    src = _mt(s, "src_field", "engineering")
    valve = _cc(s, src, "valve", category="control",
                definition="A valve regulates the flow in a pipe.",
                external_field=-4.0)
    pipe = _cc(s, src, "pipe", category="conduit",
               definition="A pipe carries the flow.")
    _couple(s, valve, pipe, +0.4)
    tgt = _mt(s, "tgt_field", "systems")
    battery = [
        ("governor", "control", "A governor regulates the engine.", -4.0),
        ("brake", "control", "A brake regulates the wheel.", -3.0),
        ("beacon", "signal", "A beacon shines a light.", +4.0),
        ("festival", "event", "A festival is a joyful gathering.", +5.0),
        ("garden", "place", "A garden is a pleasant plot.", +3.0),
        ("alarm", "signal", "An alarm warns of danger.", -5.0),
        ("ledger", "record", "A ledger records accounts.", 0.0),
        ("melody", "art", "A melody is a sweet tune.", +4.0),
        ("engine", "machine", "An engine drives the wheel.", 0.0),
        ("wheel", "part", "A wheel turns on the axle.", 0.0),
        ("reward", "event", "A reward is a welcome prize.", +5.0),
        ("penalty", "event", "A penalty is a harsh cost.", -5.0),
    ]
    nodes = {}
    for nm, cat, defn, ef in battery:
        nodes[nm] = _cc(s, tgt, nm, category=cat, definition=defn, external_field=ef)
    _couple(s, nodes["governor"], nodes["engine"], +0.4)
    _couple(s, nodes["engine"], nodes["wheel"], +0.4)
    rg.ground_relations(s, "src_field")
    rg.ground_relations(s, "tgt_field")
    _relax(s, src)
    _relax(s, tgt)
    return s, len(battery)


def _power_battery():
    """A surface pair and a felt pair that TIE on the deeper structural tiers
    (order/corroboration/struct_shared) but differ on felt overlap. The surface
    source is created FIRST so, under the felt-blind key, the felt pair genuinely
    ranks BELOW it (rank>0)."""
    s, _ag = _boot()
    src = _mt(s, "affect_src", "psychology")
    gear = _cc(s, src, "gear", category="mechpart",
               definition="Ccc ddd drives eee.", external_field=0.0)
    sprk = _cc(s, src, "sprk", category="fillerx", definition="Fff ggg.")
    _couple(s, gear, sprk, +0.4)
    chill = _cc(s, src, "chill", category="qualecold",
                definition="Zzz aaa bbb.", external_field=-5.0)
    tgt = _mt(s, "world_tgt", "phenomena")
    motor = _cc(s, tgt, "motor", category="mechpart",
                definition="Kkk lll drives mmm.", external_field=0.0)
    rotr = _cc(s, tgt, "rotr", category="fillery", definition="Nnn ooo.")
    _couple(s, motor, rotr, +0.4)
    frost = _cc(s, tgt, "frost", category="qualewet",
                definition="Hhh iii jjj.", external_field=-5.0)
    rg.ground_relations(s, "affect_src")
    rg.ground_relations(s, "world_tgt")
    _relax(s, src)
    _relax(s, tgt)
    return s, chill, frost


def _rank_of(results, sc, tc):
    for i, r in enumerate(results):
        if r["source_concept"] == sc and r["target_concept"] == tc:
            return i
    return None


# ===========================================================================
# (a) DEFAULT == TODAY — byte-identical when both opt-ins are off
# ===========================================================================
def test_default_off_is_byte_identical():
    """Both opt-ins off ⇒ the analogy list AND its order are IDENTICAL to a
    k=None / felt_bias=False baseline, on a fixed battery. The felt seams are
    inert unless explicitly switched on."""
    s, _M = _speed_battery()
    baseline = asr.find_analogies(s, "src_field", ["tgt_field"], order_n=4, min_score=1)
    # explicit-defaults call == implicit-defaults call
    explicit = asr.find_analogies(s, "src_field", ["tgt_field"], order_n=4,
                                  min_score=1, felt_shortlist_k=None, felt_bias=False)
    assert _order_key(explicit) == _order_key(baseline), (
        _order_key(explicit), _order_key(baseline))
    # and the at.* delegating entry point is identical too
    via_at = at.find_analogies(s, "src_field", ["tgt_field"], order_n=4, min_score=1)
    assert _order_key(via_at) == _order_key(baseline)
    # k=None firing proxy is the FULL N*M count (no pruning happened)
    _ = asr.find_analogies(s, "src_field", ["tgt_field"], order_n=4, min_score=1)
    counts = asr.last_firing_counts()
    assert counts["antiunify_firings"] == 24, counts  # 2 source probes * 12 parts


# ===========================================================================
# (b) SPEED — felt_shortlist_k<M shrinks firings while retaining the top match
# ===========================================================================
def test_felt_shortlist_cuts_firings_and_retains_top():
    """A k<M felt shortlist yields a strictly SMALLER firing proxy than k=None
    AND fewer full edge-enumerating signature builds, WHILE the top true
    structural analogy (found at k=None) is still returned."""
    s, M = _speed_battery()
    base = asr.find_analogies(s, "src_field", ["tgt_field"], order_n=4, min_score=1)
    base_c = asr.last_firing_counts()
    assert base, "baseline found no analogies"
    top = (base[0]["source_concept"], base[0]["target_concept"])
    assert top == ("valve", "governor"), top

    # k=3 is the honest frontier (see the measure script): fewer firings, top
    # retained.
    k = 3
    res = asr.find_analogies(s, "src_field", ["tgt_field"], order_n=4,
                             min_score=1, felt_shortlist_k=k)
    c = asr.last_firing_counts()
    # SPEED: strictly fewer AntiUnify firings AND fewer full signature builds.
    assert c["antiunify_firings"] < base_c["antiunify_firings"], (c, base_c)
    assert c["edge_enumerations"] < base_c["edge_enumerations"], (c, base_c)
    # firing proxy is ~ N*k, not N*M.
    assert c["antiunify_firings"] <= 2 * k, c
    # RECALL: the top true match survives the prune.
    assert any((r["source_concept"], r["target_concept"]) == top for r in res), \
        [(r["source_concept"], r["target_concept"]) for r in res]


def test_felt_shortlist_k_none_no_pruning():
    """felt_shortlist_k=None leaves the firing proxy at the FULL N*M count —
    the seam is off."""
    s, M = _speed_battery()
    asr.find_analogies(s, "src_field", ["tgt_field"], order_n=4, min_score=1,
                       felt_shortlist_k=None)
    c = asr.last_firing_counts()
    assert c["antiunify_firings"] == 2 * M, (c, M)


# ===========================================================================
# (c) POWER — felt_bias lifts a real felt analogy above its structural rank
# ===========================================================================
def test_felt_bias_surfaces_below_rank_felt_analogy():
    """A felt pair (shares ONLY the two PRODUCED felt axes) ties a surface pair
    on the deeper structural tiers and thus ranks BELOW it under felt_bias=False
    — a genuine below-rank miss. felt_bias=True deterministically lifts it
    ABOVE. The min_score gate is unchanged (both pairs are accepted in both
    runs); only the ORDER changes."""
    s, _chill, _frost = _power_battery()
    struct = asr.find_analogies(s, "affect_src", ["world_tgt"], order_n=2, min_score=1)
    felt = asr.find_analogies(s, "affect_src", ["world_tgt"], order_n=2,
                              min_score=1, felt_bias=True)

    r_struct = _rank_of(struct, "chill", "frost")
    r_felt = _rank_of(felt, "chill", "frost")
    assert r_struct is not None and r_felt is not None, (struct, felt)
    # GENUINE MISS: below the structurally-equal surface pair under felt-blind.
    assert r_struct > 0, ("not a below-rank miss", _order_key(struct))
    # SURFACED: felt_bias raises its rank.
    assert r_felt < r_struct, (r_struct, r_felt, _order_key(felt))
    assert r_felt == 0, _order_key(felt)
    # the min_score-accepted SET is identical (same analogies, only reordered).
    assert set(_order_key(struct)) == set(_order_key(felt))
    # the surfaced pair really is analogous on FELT dimensions.
    top = felt[0]
    assert top["felt_shared"] >= 2, top
    assert any(d.startswith("dynamical:") for d in top["aligned_dimensions"]), top


# ===========================================================================
# (d) ANTI-FAKING — the felt prior is DERIVED, not hand-set
# ===========================================================================
def test_felt_prior_derived_from_real_signature():
    """Perturbing a concept's felt SOURCE attr (external_field) and re-relaxing
    CHANGES both the felt shortlist AND the felt rank — proving the prior is the
    real _dynamical_relations signature, not a tuned score.

    chill/frost share a strongly-negative felt shape. Flip chill's
    external_field to strongly POSITIVE, re-relax: chill's produced valence
    inverts, the felt overlap with frost collapses, so (i) the cheap felt
    sub-signature used for the shortlist changes, and (ii) chill~frost's
    felt_shared drops so felt_bias no longer surfaces it."""
    s, chill, frost = _power_battery()
    schema = asr._qualia_schema(s)

    # felt sub-signatures BEFORE the flip (the CHEAP shortlist read).
    felt_chill_before = frozenset(asr._dynamical_relations(s, chill, schema, False))
    felt_frost = frozenset(asr._dynamical_relations(s, frost, schema, False))
    dist_before = len(felt_chill_before ^ felt_frost)

    felt_rank_before = _rank_of(
        asr.find_analogies(s, "affect_src", ["world_tgt"], order_n=2,
                           min_score=1, felt_bias=True), "chill", "frost")
    assert felt_rank_before == 0, felt_rank_before  # surfaced before

    # PERTURB the felt SOURCE attr and re-relax (produce a new felt coordinate).
    s.set_attr(chill, "external_field", +5.0)
    s.set_attr(chill, "state", 0.0)
    s.set_attr(chill, "identity_field", 0.0)
    _relax(s, _find_src_mt(s))

    felt_chill_after = frozenset(asr._dynamical_relations(s, chill, schema, False))
    dist_after = len(felt_chill_after ^ felt_frost)

    # (i) the CHEAP felt sub-signature CHANGED (the shortlist input moved).
    assert felt_chill_after != felt_chill_before, (felt_chill_before, felt_chill_after)
    # chill's valence flipped sign -> it is now FARTHER from frost in felt space.
    assert dist_after > dist_before, (dist_before, dist_after)

    # (ii) the felt RANK changed accordingly: chill~frost is no longer surfaced
    # to the top (its felt overlap with frost collapsed).
    felt_after = asr.find_analogies(s, "affect_src", ["world_tgt"], order_n=2,
                                    min_score=1, felt_bias=True)
    felt_rank_after = _rank_of(felt_after, "chill", "frost")
    assert felt_rank_after != 0, (
        "felt rank did not move after perturbing the felt source",
        _order_key(felt_after))


def _find_src_mt(s):
    for mt in s.nodes("Microtheory"):
        if s.node(mt)["attrs"].get("name") == "affect_src":
            return mt
    raise AssertionError("affect_src not found")


# ===========================================================================
# (e) .so md5 unchanged — no Rust / no .so change
# ===========================================================================
def test_native_so_md5_unchanged():
    h = hashlib.md5(_SO.read_bytes()).hexdigest()
    assert h == _SO_MD5, h
