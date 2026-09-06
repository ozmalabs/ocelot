#!/usr/bin/env python3
"""FELT-RESCUE strong arm — the 3-run precision-at-recall measurement.

PREREG: docs/research/psychology_affect/FELT_RESCUE_STRONG_ARM_PREREG.md (block 300000).
RESULTS: docs/research/psychology_affect/FELT_RESCUE_STRONG_ARM_RESULTS.md.

Builds ONE labelled below-threshold battery of cross-domain candidate pairs and
runs `find_analogies` THREE ways on the SAME battery:

  (i)   min_score = k                      BASELINE  (the genuine-miss reference)
  (ii)  min_score = k - 1                   BLANKET   (loosen the floor for everyone)
  (iii) min_score = k + felt_rescue=True    RESCUE    (the strong arm)

The battery is LABELLED:
  · TRUE     — cross-domain pairs sharing a RARE felt shape (a shared
               `phenomenal:sharpness` pole, or `felt_shared >= 2`) whose
               DISCRIMINATIVE structural count sits BELOW min_score=k. GENUINE
               misses: each is VERIFIED ABSENT from the accepted set at the (i)
               baseline.
  · SPURIOUS — pairs sharing ONLY a bare `dynamical:valence` sign (the coin flip,
               ~0.49 by chance) — the junk pool. Also below k.

WHY 1-vs-1 RUNS. The analogy decode emits exactly ONE analogy per source concept
(the single Argmax-best target partner; ap_decode/ap_emit in
seeds/analogy_search.json). Packing many same-pole concepts into one field would
collapse them onto one arbitrary Argmax winner and confound the labels. So each
labelled pair is run as its OWN source-field (one concept) vs target-field (one
concept) `find_analogies` call — emission of exactly that pair is guaranteed and
its felt shape is unambiguous. The three runs use the SAME battery of pairs.

CLAIM HOLDS IFF run (iii) recovers the TRUE pairs at recall ~ run (ii) (recovers
the felt misses) AND run (iii) admits FAR FEWER SPURIOUS than run (ii)
(precision >> blanket). If (iii) admits junk at ~the blanket rate, the strong arm
FAILED (threshold-loosening, not selective) — reported honestly.

The felt priors are the REAL `_dynamical_relations` signature: valence from the
committed `state` field, sharpness from the bouba/kiki `sharpness` source attr —
NOT a tuned score. Source-audited: no graph_rewrite.run/_match/_apply/make_rule.
"""
from __future__ import annotations

import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "runners" / "dsl" / "python"))

from substrate_rs import _native  # noqa: E402

import domains.analogical_thinking as at  # noqa: E402
import domains.analogy_search as asr  # noqa: E402
import domains.relation_grounding as rg  # noqa: E402
from domains.can_self_worth_bridge import ensure_can_seed  # noqa: E402

SEEDS = _ROOT / "seeds"

#: The CAN identity/evidence ledger every relaxed concept carries (matches the
#: migrated test harness). Present so the concept looks exactly like a relaxed
#: one; excluded from the signature as bookkeeping noise.
_LEDGER = {
    "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
    "identity_evidence_tick": -1, "identity_decay_tick": -1,
    "identity_field_tick": -1,
}

#: The acceptance floor whose below-threshold band this battery probes. At k=2,
#: a pair sharing ONE discriminative felt coord (disc=1; the trivial is_a type
#: coord never counts) is a MISS. A shared sharpness pole (rare) and a shared
#: bare valence sign (coin flip) both sit at disc=1 — the discriminating band.
K = 2


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


def _cc(s, mt, name, *, definition, category, state=0.0, sharpness=None):
    """A concept with its REAL felt source attrs: `state` (the committed state
    the `dynamical:valence` axis reads) and, optionally, `sharpness` (the
    bouba/kiki `phenomenal:sharpness` source attr the crossmodal extractor
    writes). `identity_field` stays 0 so `dynamical:commitment` is DARK (as
    Task 1 measured on the real relaxed corpus) — a valence-only concept then
    shares ONLY the coin-flip valence axis, never a spurious second felt coord.
    A UNIQUE definition keeps surface thin/distinct so a shared FELT coord is
    the only thing that can lift a pair — the band this battery probes."""
    attrs = {"name": name, "category": category, "definition": definition,
             "state": float(state), "external_field": 0.0, "identity_field": 0.0}
    if sharpness is not None:
        attrs["sharpness"] = float(sharpness)
    attrs.update(_LEDGER)
    c = s.add_node("Concept", attrs)
    s.add_edge_unchecked(mt, "has_concept", c)
    return c


#: The labelled battery. Each spec is (name, label, source_attrs, target_attrs)
#: where *_attrs = {state, sharpness}. Every pair is thin/distinct on surface,
#: so its ONLY cross-field overlap is the felt coordinate(s) listed.
#:   TRUE  = shares a phenomenal:sharpness POLE (rare, ~0.012 by chance).
#:   SPUR  = shares ONLY a dynamical:valence sign (coin flip, ~0.488 by chance).
#: (A `felt_shared >= 2` TRUE variant — shared valence AND sharpness — is
#: covered in the test suite; here the below-k TRUE band is the sharpness-pole
#: misses, which is the cleanest disc=1 rare-felt case.)
_BATTERY = [
    # TRUE — shared sharpness pole only
    ("spike_thorn", "TRUE", dict(sharpness=+1.0), dict(sharpness=+1.0)),
    ("blade_shard", "TRUE", dict(sharpness=+1.0), dict(sharpness=+1.0)),
    ("jag_spur", "TRUE", dict(sharpness=+1.0), dict(sharpness=+1.0)),
    ("round_pebble", "TRUE", dict(sharpness=-1.0), dict(sharpness=-1.0)),
    ("dome_bubble", "TRUE", dict(sharpness=-1.0), dict(sharpness=-1.0)),
    ("orb_blob", "TRUE", dict(sharpness=-1.0), dict(sharpness=-1.0)),
    # SPURIOUS — shared bare valence sign only
    ("glad_merry", "SPURIOUS", dict(state=+1.0), dict(state=+1.0)),
    ("bright_sunny", "SPURIOUS", dict(state=+1.0), dict(state=+1.0)),
    ("keen_avid", "SPURIOUS", dict(state=+1.0), dict(state=+1.0)),
    ("grim_bleak", "SPURIOUS", dict(state=-1.0), dict(state=-1.0)),
    ("dour_dark", "SPURIOUS", dict(state=-1.0), dict(state=-1.0)),
    ("sour_harsh", "SPURIOUS", dict(state=-1.0), dict(state=-1.0)),
]


def _run_pair(name, s_attrs, t_attrs, *, min_score, rescue):
    """One labelled pair as its OWN 1-vs-1 find_analogies call. Returns the
    single verdict dict (or None if the pair was not admitted)."""
    s, _ag = _boot()
    src = _mt(s, "src", "alpha")
    tgt = _mt(s, "tgt", "beta")
    sn, tn = name.split("_")
    _cc(s, src, sn, category="cat_%s" % sn,
        definition="Def %s alpha unique." % sn, **s_attrs)
    _cc(s, tgt, tn, category="cat_%s" % tn,
        definition="Def %s beta unique." % tn, **t_attrs)
    rg.ground_relations(s, "src")
    rg.ground_relations(s, "tgt")
    res = asr.find_analogies(s, "src", ["tgt"], order_n=2, min_score=min_score,
                             felt_rescue=rescue)
    return res[0] if res else None


def _run_battery(*, min_score, rescue):
    """Run every labelled pair under one config. Returns {name -> verdict|None}."""
    return {name: _run_pair(name, s_attrs, t_attrs, min_score=min_score, rescue=rescue)
            for name, _label, s_attrs, t_attrs in _BATTERY}


def run():
    true_names = [n for n, lab, _s, _t in _BATTERY if lab == "TRUE"]
    spur_names = [n for n, lab, _s, _t in _BATTERY if lab == "SPURIOUS"]

    baseline = _run_battery(min_score=K, rescue=False)       # (i)
    blanket = _run_battery(min_score=K - 1, rescue=False)     # (ii)
    rescue = _run_battery(min_score=K, rescue=True)           # (iii)

    def admitted(run_map, names):
        return [n for n in names if run_map[n] is not None]

    def rescued(run_map, names):
        return [n for n in names if run_map[n] is not None and run_map[n].get("felt_rescued")]

    # --- genuine-miss verification: every TRUE ABSENT at the baseline --------
    true_absent = [n for n in true_names if baseline[n] is None]
    true_present = [n for n in true_names if baseline[n] is not None]

    print("=" * 78)
    print("FELT-RESCUE STRONG ARM — 3-run precision-at-recall (k=%d)" % K)
    print("=" * 78)
    print("\nBattery: %d TRUE (rare felt shape) + %d SPURIOUS (bare valence) pairs, "
          "run 1-vs-1" % (len(true_names), len(spur_names)))

    print("\n--- GENUINE-MISS VERIFICATION (run FIRST) ---")
    print("TRUE pairs ABSENT at baseline min_score=%d (genuine misses): %d/%d"
          % (K, len(true_absent), len(true_names)))
    for n in true_absent:
        print("    MISS  %s" % n)
    if true_present:
        print("  WARNING — TRUE pairs already present at baseline (NOT genuine misses):")
        for n in true_present:
            print("    (present) %s" % n)

    print("\n--- 3-RUN TABLE ---")
    print("%-30s | recall_TRUE | spurious_admitted | precision_on_junk" % "run")
    print("-" * 92)
    runs = [
        ("(i)   baseline  min_score=%d" % K, baseline),
        ("(ii)  blanket   min_score=%d" % (K - 1), blanket),
        ("(iii) rescue    min_score=%d+R" % K, rescue),
    ]
    table = {}
    for label, rm in runs:
        rt = len(admitted(rm, true_names))
        spa = len(admitted(rm, spur_names))
        prec = 1.0 - (spa / len(spur_names) if spur_names else 0.0)
        table[label] = (rt, spa, prec)
        print("%-30s |    %d/%d      |       %d/%d         |     %.2f"
              % (label, rt, len(true_names), spa, len(spur_names), prec))

    print("\n--- GLASS-BOX (rescue run; each labelled pair) ---")
    print("%-14s %-9s felt_shared shared_felt_axes         admitted rescued" % ("pair", "label"))
    for name, label, _s, _t in _BATTERY:
        r = rescue[name]
        if r is None:
            print("%-14s %-9s    -        %-24s %-8s %s" % (name, label, "-", False, False))
        else:
            axes = ",".join(a.split(":")[1] for a in sorted(
                asr._shared_felt_axes(r["transform_key"]))) or "-"
            print("%-14s %-9s    %d        %-24s %-8s %s"
                  % (name, label, r["felt_shared"], axes, True, bool(r.get("felt_rescued"))))

    # --- verdict ---
    rt_base, _spa_base, _pb = table["(i)   baseline  min_score=%d" % K]
    rt_blank, spa_blank, prec_blank = table["(ii)  blanket   min_score=%d" % (K - 1)]
    rt_resc, spa_resc, prec_resc = table["(iii) rescue    min_score=%d+R" % K]

    recovers = rt_resc >= rt_blank and rt_resc > rt_base
    selective = spa_resc < spa_blank and prec_resc > prec_blank
    confirmed = recovers and selective

    print("\n--- VERDICT ---")
    print("recall_TRUE:        baseline=%d  blanket=%d  rescue=%d" % (rt_base, rt_blank, rt_resc))
    print("spurious_admitted:  blanket=%d   rescue=%d" % (spa_blank, spa_resc))
    print("precision_on_junk:  blanket=%.2f  rescue=%.2f" % (prec_blank, prec_resc))
    print("recovers felt misses (rescue recall >= blanket AND > baseline): %s" % recovers)
    print("selective (rescue admits fewer junk AND precision > blanket):   %s" % selective)
    if confirmed:
        print("\nSTRONG ARM CONFIRMED: rescue recovers the TRUE felt misses at recall")
        print("  >= blanket (%d >= %d) WHILE rejecting the spurious valence-coincidence"
              % (rt_resc, rt_blank))
        print("  pairs the blanket drop admits (precision %.2f >> %.2f). SELECTIVE, not"
              % (prec_resc, prec_blank))
        print("  threshold-loosening.")
    else:
        print("\nSTRONG ARM FAILED: rescue behaves like a blanket threshold drop")
        print("  (recovers=%s, selective=%s). Reported honestly." % (recovers, selective))

    return {
        "k": K,
        "true_total": len(true_names),
        "spurious_total": len(spur_names),
        "true_absent_at_baseline": true_absent,
        "recall": {"baseline": rt_base, "blanket": rt_blank, "rescue": rt_resc},
        "spurious_admitted": {"baseline": table["(i)   baseline  min_score=%d" % K][1],
                              "blanket": spa_blank, "rescue": spa_resc},
        "precision_on_junk": {"blanket": prec_blank, "rescue": prec_resc},
        "confirmed": confirmed,
    }


if __name__ == "__main__":
    summary = run()
    print("\nJSON:", json.dumps(summary))
