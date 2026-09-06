"""FEEL-THEN-REASON measure — the firing-vs-quality frontier + the power demo.

PREREG: docs/research/psychology_affect/FEEL_THEN_REASON_PREREG.md (block 299000).

Two experiments, GLASS-BOX (every firing count is read from the real
instrumentation `analogy_search.last_firing_counts()`, never asserted):

  (A) SPEED FRONTIER — a battery of felt-distinct target concepts (M large),
      one source. Sweep felt_shortlist_k from small..M and vs k=None. Record the
      AntiUnify-firing proxy (Σ|probe_scope|), the edge-enumerations (# FULL
      concept_signature builds), and whether the TOP structural analogy found at
      k=None is RETAINED at each k. Report the honest frontier: the smallest k
      at which quality is retained.

  (B) POWER DEMO — a cross-domain pair sharing a FELT shape (dynamical:valence
      + commitment, PRODUCED by native relaxation) but thin surface structure,
      that felt_bias=False ranks BELOW other matches (a GENUINE miss — verified
      by showing it is not top under structural-only ranking), and felt_bias=
      True surfaces it into the top.

Source-audit: uses ONLY analogy_search.find_analogies / relation_grounding /
native relax+crystallize. No graph_rewrite.run/_match/_apply/make_rule.
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr
import domains.relation_grounding as rg
from domains.can_self_worth_bridge import ensure_can_seed
from domains.self_improvement_loop import relax

ROOT = pathlib.Path(at.__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"

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
                                  "provenance": "measure:open"})
    return s, ag


def _mt(s, name, category="general"):
    return s.add_node("Microtheory", {"name": name, "category": category,
                                      "temperature": 1.0, "discrete_mode": "3state",
                                      "can_tick": 0, "update_policy": "adaptive"})


def _can_concept(s, mt, name, *, definition, category, external_field=0.0):
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


def _pair(results, sc, tc):
    for i, r in enumerate(results):
        if r["source_concept"] == sc and r["target_concept"] == tc:
            return i, r
    return None, None


# ===========================================================================
# (A) SPEED FRONTIER
# ===========================================================================
def experiment_speed():
    print("=" * 74)
    print("(A) SPEED FRONTIER — firing proxy + edge-enumerations vs felt_shortlist_k")
    print("=" * 74)
    s, _ag = _boot()

    # SOURCE field: one concept with a distinctive felt+structural shape.
    src = _mt(s, "src_field", "engineering")
    valve = _can_concept(s, src, "valve", category="control",
                         definition="A valve regulates the flow in a pipe.",
                         external_field=-4.0)
    pipe = _can_concept(s, src, "pipe", category="conduit",
                        definition="A pipe carries the flow.")
    _couple(s, valve, pipe, +0.4)

    # TARGET field: a BATTERY of concepts across a felt spectrum (external_field
    # from strongly negative to strongly positive) so their felt sub-signatures
    # (dynamical:valence/commitment, PRODUCED by relaxation) genuinely DIFFER —
    # the true structural match ('governor', a regulator, negative felt shape)
    # sits among many felt-distant distractors.
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
        nodes[nm] = _can_concept(s, tgt, nm, category=cat, definition=defn,
                                 external_field=ef)
    # a couple of structural couplings so 'governor'/'engine' carry edges
    _couple(s, nodes["governor"], nodes["engine"], +0.4)
    _couple(s, nodes["engine"], nodes["wheel"], +0.4)

    rg.ground_relations(s, "src_field")
    rg.ground_relations(s, "tgt_field")
    _relax(s, src)
    _relax(s, tgt)

    M = len(battery)  # target part count seen by the 'valve' probe (minus none;
                      # cross-field so no own-part removal)
    # k=None baseline — full scope, the reference for firings AND quality.
    base = asr.find_analogies(s, "src_field", ["tgt_field"], order_n=4, min_score=1)
    base_counts = asr.last_firing_counts()
    base_top = base[0] if base else None
    top_pair = (base_top["source_concept"], base_top["target_concept"]) if base_top else None
    print(f"\nM (target parts) = {M}")
    print(f"k=None baseline: firings={base_counts['antiunify_firings']}, "
          f"edge_enums={base_counts['edge_enumerations']}, "
          f"top analogy = {top_pair}, n_results={len(base)}")
    if top_pair:
        print(f"  (top analogy is the TRUE structural match to be retained)")

    print(f"\n{'k':>4} | {'firings':>8} | {'edge_enums':>10} | {'n_res':>5} | "
          f"{'top_retained':>12} | top_pair")
    print("-" * 74)
    rows = []
    for k in [1, 2, 3, 4, 6, 8, M]:
        res = asr.find_analogies(s, "src_field", ["tgt_field"], order_n=4,
                                 min_score=1, felt_shortlist_k=k)
        c = asr.last_firing_counts()
        retained = top_pair is not None and any(
            (r["source_concept"], r["target_concept"]) == top_pair for r in res)
        this_top = (res[0]["source_concept"], res[0]["target_concept"]) if res else None
        rows.append((k, c["antiunify_firings"], c["edge_enumerations"],
                     len(res), retained, this_top))
        print(f"{k:>4} | {c['antiunify_firings']:>8} | {c['edge_enumerations']:>10} | "
              f"{len(res):>5} | {str(retained):>12} | {this_top}")
    print(f"{'None':>4} | {base_counts['antiunify_firings']:>8} | "
          f"{base_counts['edge_enumerations']:>10} | {len(base):>5} | "
          f"{'(baseline)':>12} | {top_pair}")

    # honest frontier: smallest k that retains the top true match
    retained_ks = [k for (k, _f, _e, _n, ret, _t) in rows if ret]
    frontier_k = min(retained_ks) if retained_ks else None
    print(f"\nHONEST FRONTIER: smallest k retaining the top true match = {frontier_k}")
    if frontier_k is not None:
        fr = next(r for r in rows if r[0] == frontier_k)
        print(f"  at k={frontier_k}: firings={fr[1]} (vs {base_counts['antiunify_firings']} "
              f"at k=None), edge_enums={fr[2]} (vs {base_counts['edge_enumerations']})")
        pareto = (fr[1] < base_counts["antiunify_firings"])
        print(f"  fewer firings than k=None while retaining top match? {pareto}")
    return {"M": M, "base": base_counts, "top_pair": top_pair, "rows": rows,
            "frontier_k": frontier_k}


# ===========================================================================
# (B) POWER DEMO
# ===========================================================================
def experiment_power():
    print("\n" + "=" * 74)
    print("(B) POWER DEMO — felt_bias surfaces a real below-rank felt analogy")
    print("=" * 74)
    s, _ag = _boot()

    # A field with TWO competing matches that TIE on every deeper structural
    # tier (order / corroboration / struct_shared) but differ on FELT overlap:
    #   · a SURFACE pair (gear~motor): shares a category + a telic edge, felt-
    #     NEUTRAL (felt_shared=0);
    #   · a FELT pair (chill~frost): shares ONLY the two PRODUCED felt axes
    #     (dynamical:valence + commitment, from native relaxation), DIFFERENT
    #     category + prose, so it ties the surface pair on struct_shared but has
    #     felt_shared=2.
    # Under structural-only (felt_bias=False) the felt pair ranks BELOW the
    # surface pair (a genuine below-rank miss — the felt tier does not exist).
    # Under felt_bias=True the felt tier deterministically LIFTS it above.
    src = _mt(s, "affect_src", "psychology")
    # surface source FIRST so, on a deeper-tier tie, it sorts ahead of the felt
    # pair under structural-only (the miss is not an artefact of input order —
    # it is genuinely below on the felt-blind key).
    gear = _can_concept(s, src, "gear", category="mechpart",
                        definition="Ccc ddd drives eee.", external_field=0.0)
    sprk = _can_concept(s, src, "sprk", category="fillerx",
                        definition="Fff ggg.")
    _couple(s, gear, sprk, +0.4)
    chill = _can_concept(s, src, "chill", category="qualecold",
                         definition="Zzz aaa bbb.", external_field=-5.0)

    tgt = _mt(s, "world_tgt", "phenomena")
    motor = _can_concept(s, tgt, "motor", category="mechpart",
                         definition="Kkk lll drives mmm.", external_field=0.0)
    rotr = _can_concept(s, tgt, "rotr", category="fillery",
                        definition="Nnn ooo.")
    _couple(s, motor, rotr, +0.4)
    frost = _can_concept(s, tgt, "frost", category="qualewet",
                         definition="Hhh iii jjj.", external_field=-5.0)

    rg.ground_relations(s, "affect_src")
    rg.ground_relations(s, "world_tgt")
    _relax(s, src)
    _relax(s, tgt)
    # sanity: the felt coords were PRODUCED (not hand-set)
    assert s.node(chill)["attrs"]["identity_field"] < 0
    assert s.node(frost)["attrs"]["identity_field"] < 0

    # STRUCTURAL-ONLY (felt_bias=False) — the reference ranking.
    struct = asr.find_analogies(s, "affect_src", ["world_tgt"], order_n=2, min_score=1)
    print("\nSTRUCTURAL-ONLY ranking (felt_bias=False):")
    for i, r in enumerate(struct):
        print(f"  [{i}] {r['source_concept']}~{r['target_concept']}  "
              f"felt_shared={r['felt_shared']} struct={r['struct_shared']} "
              f"corr={r['corroboration']} dims={r['aligned_dimensions']}")
    i_struct, _r = _pair(struct, "chill", "frost")
    print(f"\n  chill~frost rank under structural-only: "
          f"{i_struct if i_struct is not None else 'ABSENT'}")

    # FELT-BIASED (felt_bias=True) — same matches, felt-aware ranking.
    felt = asr.find_analogies(s, "affect_src", ["world_tgt"], order_n=2,
                              min_score=1, felt_bias=True)
    print("\nFELT-BIASED ranking (felt_bias=True):")
    for i, r in enumerate(felt):
        print(f"  [{i}] {r['source_concept']}~{r['target_concept']}  "
              f"felt_shared={r['felt_shared']} struct={r['struct_shared']} "
              f"corr={r['corroboration']} dims={r['aligned_dimensions']}")
    i_felt, _r = _pair(felt, "chill", "frost")
    print(f"\n  chill~frost rank under felt_bias: "
          f"{i_felt if i_felt is not None else 'ABSENT'}")

    genuine_miss = (i_struct is not None and i_struct > 0)
    surfaced = (i_felt is not None and i_struct is not None and i_felt < i_struct)
    print(f"\n  genuine below-rank miss under structural-only (rank>0)? {genuine_miss}")
    print(f"  felt_bias raised its rank? {surfaced} "
          f"(struct rank {i_struct} -> felt rank {i_felt})")

    # ANTI-FAKING: perturb chill's felt SOURCE attr (external_field flips to
    # strongly POSITIVE), re-relax, and show the felt shortlist AND the felt
    # rank CHANGE — the prior is DERIVED from the real _dynamical_relations
    # signature, not hand-set.
    print("\n  ANTI-FAKING: flip chill's external_field -5 -> +5, re-relax:")
    s.set_attr(chill, "external_field", +5.0)
    s.set_attr(chill, "state", 0.0)
    s.set_attr(chill, "identity_field", 0.0)
    _relax(s, src)
    felt2 = asr.find_analogies(s, "affect_src", ["world_tgt"], order_n=2,
                               min_score=1, felt_bias=True)
    i_felt2, r_felt2 = _pair(felt2, "chill", "frost")
    fs2 = r_felt2["felt_shared"] if r_felt2 is not None else None
    print(f"    chill~frost after flip: rank={i_felt2 if i_felt2 is not None else 'ABSENT'}, "
          f"felt_shared={fs2} "
          f"(chill now +valence, frost still -valence => felt overlap should DROP)")
    return {"struct_rank": i_struct, "felt_rank": i_felt,
            "genuine_miss": genuine_miss, "surfaced": surfaced,
            "flip_rank": i_felt2, "flip_felt_shared": fs2}


if __name__ == "__main__":
    a = experiment_speed()
    b = experiment_power()
    print("\n" + "=" * 74)
    print("SUMMARY")
    print("=" * 74)
    print(f"SPEED: M={a['M']}, k=None firings={a['base']['antiunify_firings']}, "
          f"frontier_k={a['frontier_k']}")
    print(f"POWER: chill~frost struct_rank={b['struct_rank']} -> "
          f"felt_rank={b['felt_rank']} "
          f"(genuine_miss={b['genuine_miss']}, surfaced={b['surfaced']}); "
          f"anti-faking flip -> rank={b['flip_rank']}, felt_shared={b['flip_felt_shared']}")
