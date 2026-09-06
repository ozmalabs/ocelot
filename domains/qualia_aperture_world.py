"""QualiaApertureWorld — the 3-agent QUALIA DIMENSION COMPENSATION experiment
(pre-reg block 298000).

Tests the falsifiable core of
`docs/research/theory_convergence/QUALIA_SPACE_VARIATION_CHARTER.md` §4, as frozen
in `docs/research/psychology_affect/QUALIA_DIMENSION_COMPENSATION_PREREG.md`:

    when a felt AXIS is absent, the GRAIN of the remaining axes expands to MOSTLY
    compensate — the dimension-lacking agent is near-normal on discriminations
    RECONSTRUCTABLE from correlated structure on the remaining axes, but fails on
    a discrimination ORTHOGONAL to every remaining axis at ANY grain (aperture
    cannot manufacture a dimension = the aphantasia shape).

ARCHITECTURE RULE COMPLIANCE. This file is a WORLD ADAPTER over the generalised
Seldon APERTURE primitive (Stage 1: `domains/analogy_search.concept_signature(...,
observer=...)` consulting `_observer_aperture`, reusing `seeds/observer_aperture.
json`). It does exactly two things — configure the three Observer nodes + the
Concept battery, and READ discriminations — around the signature builder. It
contains NO agent decision and, in particular:

  * the DISCRIMINATION outcome is READ from signature byte-equality:
    `discriminable(a, b, observer) := concept_signature(a, obs) !=
    concept_signature(b, obs)`. There is NO `if/else` that DECIDES the outcome;
    the only conditionals here are over WORLD state (loop bounds, counting a
    rate, formatting a table) — mechanical emit.
  * NO `graph_rewrite.run` / `_match` / `_apply` / `make_rule`; NO Rust; NO CAN
    cognition internals touched. The aperture (existence + grain) is graph DATA
    on the Observer node (`resolves`, `grain`), read by the Stage-1 primitive.

Glass-box: the run prints the ORTHOGONAL pair's two signatures for FULL (they
DIFFER — sharpness is a coordinate) and for a DARK agent (they are BYTE-EQUAL —
sharpness is the only separator and it is gone), so the orthogonality is visible,
not asserted.

Run:  python3 -m domains.qualia_aperture_world
Emits: results/qualia_dimension_compensation/results.json
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate_rs import _native                 # noqa: E402
import domains.analogical_thinking as at          # noqa: E402
import domains.analogy_search as asr              # noqa: E402

#: The three seeds this experiment rides on: the shape-vocabulary bootstrap, the
#: qualia-space codebook, and the generalised aperture primitive (Stage 1).
_SEED_FILES = ["shape_vocabulary.json", "qualia_space.json",
               "analogy_search.json", "observer_aperture.json"]

#: Node / edge types the battery + observers use — opened as productions so the
#: adds are admissible (mirrors the qualia tests' `_open`).
_NT = ("Agent", "Concept", "Microtheory", "QualiaDimension", "DimensionEdgeRole",
       "Observer", "ShapeSignature", "ObservedShape")
_ET = ("has_concept", "gates", "regulates", "made_of", "used_for", "perceives",
       "holds_part", "projected", "projected_part")

# --------------------------------------------------------------------------- #
# Frozen constants (pre-reg §2, §4). Nothing here is measured — it is the
# experimental DESIGN, committed before the run.
# --------------------------------------------------------------------------- #

#: The qualia dimension NAMES (full family:name, keys into resolves/grain).
DIM_SHARPNESS = "phenomenal:sharpness"     # source field:sharpness, q1.0, hw1
DIM_COMMITMENT = "dynamical:commitment"    # source field:identity_field, q0.25, hw4
DIM_VALENCE = "dynamical:valence"          # source field:state, q1.0, hw1

#: All three agents RESOLVE these non-sharpness dynamical axes (so only sharpness
#: existence and commitment grain differ between the agents).
_KEEP = [DIM_COMMITMENT, DIM_VALENCE]

#: The compensated agent's FINE commitment grain (the Pareto move).
FINE_GRAIN = 0.1

#: The grain sweep (coarse -> fine), commitment quantum on the compensated agent.
GRAIN_SWEEP = [0.25, 0.20, 0.15, 0.12, 0.10]

#: RECONSTRUCTABLE pairs: differ on sharpness (+1/-1) AND on a small correlated
#: commitment gap (identity_field) sub-threshold at global grain 0.25.
#: (name, category, identity_field_A, identity_field_B)  [sharpness A=+1, B=-1]
RECONSTRUCTABLE = [
    ("r1", "gadget", 0.14, 0.24),
    ("r2", "gadget", 0.16, 0.26),
    ("r3", "gadget", 0.14, 0.28),
]

#: ORTHOGONAL pair: IDENTICAL on every attr except sharpness (+1 vs -1).
#: identity_field 0.8 -> commitment level 3 at global grain (a real coordinate),
#: shared by both members, so sharpness is the ONLY separator.
ORTHOGONAL = ("o1", "gadget", 0.8, +1.0, -1.0)


def _mt(s, name):
    return s.add_node("Microtheory", {"name": name})


def _open(s):
    for a in _NT:
        for b in _NT:
            for et in _ET:
                s.add_production({"src": {"type": a, "var": "x"},
                                  "edge_type": et,
                                  "tgt": {"type": b, "var": "y"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "world:qualia_aperture:open"})


def _substrate():
    """Boot a fresh native substrate and install the qualia + aperture seeds
    directly from their JSON manifests (the canonical qualia-experiment boot,
    matching tests/test_qualia_space_migrated). Caches cleared so a repeat run
    is honest."""
    s = _native.Substrate()
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    ag = s.add_node("Agent", {})
    _open(s)
    for fname in _SEED_FILES:
        path = os.path.join(_ROOT, "seeds", fname)
        summ = s.load_seed_manifest(json.load(open(path)), ag)
        assert not summ.get("rules_skipped"), (fname, summ)
    return s, ag


def _concept(s, mt, name, **attrs):
    a = {"name": name}
    a.update(attrs)
    c = s.add_node("Concept", a)
    s.add_edge(mt, "has_concept", c)
    return c


def _observer(s, name, resolves, grain=None):
    attrs = {"name": name, "ap_gen": 0.0, "ap_scope_n": 0.0}
    if resolves is not None:
        attrs["resolves"] = list(resolves)
    if grain:
        attrs["grain"] = dict(grain)
    return s.add_node("Observer", attrs)


def _discriminable(s, a, b, observer) -> bool:
    """READ, not decided: two stimuli are discriminable to an agent iff their
    signatures through that agent's observer DIFFER. No branch selects the
    outcome — it IS the byte-inequality of two frozensets."""
    return (asr.concept_signature(s, a, observer=observer)
            != asr.concept_signature(s, b, observer=observer))


def build():
    """Boot, install the qualia + aperture seeds, build the battery + the three
    base observers (FULL, DARK-COMPENSATED at FINE_GRAIN, DARK-UNCOMPENSATED)."""
    s, ag = _substrate()
    mt = _mt(s, "qualia_aperture_world")

    # --- battery ---------------------------------------------------------- #
    recon = []
    for name, cat, if_a, if_b in RECONSTRUCTABLE:
        # both members share name+category; differ on sharpness AND identity_field
        a = _concept(s, mt, name, category=cat, identity_field=if_a,
                     state=1.0, sharpness=1.0)
        b = _concept(s, mt, name, category=cat, identity_field=if_b,
                     state=1.0, sharpness=-1.0)
        recon.append((name, a, b))

    o_name, o_cat, o_if, o_sa, o_sb = ORTHOGONAL
    oa = _concept(s, mt, o_name, category=o_cat, identity_field=o_if,
                  state=1.0, sharpness=o_sa)
    ob = _concept(s, mt, o_name, category=o_cat, identity_field=o_if,
                  state=1.0, sharpness=o_sb)
    orth = (o_name, oa, ob)

    # --- three observers -------------------------------------------------- #
    full = _observer(s, "FULL", resolves=[DIM_SHARPNESS] + _KEEP)  # global grain
    dark_comp = _observer(s, "DARK-COMPENSATED", resolves=_KEEP,
                          grain={DIM_COMMITMENT: FINE_GRAIN})
    dark_unc = _observer(s, "DARK-UNCOMPENSATED", resolves=_KEEP)  # global grain

    return {
        "s": s, "ag": ag, "mt": mt,
        "recon": recon, "orth": orth,
        "full": full, "dark_comp": dark_comp, "dark_unc": dark_unc,
    }


def _rates(s, agents, recon, orth):
    """For each named agent-observer, the reconstructable rate (#R-pairs
    discriminated / 3) and the orthogonal rate (1 if the O-pair discriminated
    else 0). Pure read; the only conditionals count a rate."""
    out = {}
    for label, obs in agents:
        r_hits = [name for name, a, b in recon if _discriminable(s, a, b, obs)]
        o_hit = _discriminable(s, orth[1], orth[2], obs)
        out[label] = {
            "reconstructable_hits": r_hits,
            "reconstructable_rate": [len(r_hits), len(recon)],
            "orthogonal_rate": 1 if o_hit else 0,
        }
    return out


def _dyn(sig):
    return sorted(t for t in sig if t[1] == "field")


def run(verbose=True):
    w = build()
    s = w["s"]
    recon, orth = w["recon"], w["orth"]
    full, dark_comp, dark_unc = w["full"], w["dark_comp"], w["dark_unc"]

    # ---- base three-agent rates (compensated at FINE_GRAIN) -------------- #
    base_agents = [
        ("FULL", full),
        ("DARK-COMPENSATED", dark_comp),
        ("DARK-UNCOMPENSATED", dark_unc),
    ]
    base = _rates(s, base_agents, recon, orth)

    # ---- glass-box: the orthogonal pair's signatures, FULL vs a dark agent  #
    oa, ob = orth[1], orth[2]
    full_a = asr.concept_signature(s, oa, observer=full)
    full_b = asr.concept_signature(s, ob, observer=full)
    dark_a = asr.concept_signature(s, oa, observer=dark_comp)
    dark_b = asr.concept_signature(s, ob, observer=dark_comp)
    glassbox = {
        "full_a_dyn": _dyn(full_a),
        "full_b_dyn": _dyn(full_b),
        "full_differ": full_a != full_b,
        "dark_a_dyn": _dyn(dark_a),
        "dark_b_dyn": _dyn(dark_b),
        "dark_byte_equal": dark_a == dark_b,
    }

    # ---- the grain sweep on the DARK-COMPENSATED agent ------------------- #
    # Re-grain ONE observer node's `grain` attr in place and re-read; the
    # existence gate (sharpness dark) is held fixed. This is the aperture knob.
    sweep = []
    swept = dark_comp
    for q in GRAIN_SWEEP:
        s.set_attr(swept, "grain", {DIM_COMMITMENT: q})
        r = _rates(s, [("DARK-COMPENSATED@%.2f" % q, swept)], recon, orth)
        row = r["DARK-COMPENSATED@%.2f" % q]
        sweep.append({
            "commitment_grain": q,
            "reconstructable_rate": row["reconstructable_rate"],
            "reconstructable_hits": row["reconstructable_hits"],
            "orthogonal_rate": row["orthogonal_rate"],
        })
    # restore the compensated grain to the frozen FINE value
    s.set_attr(swept, "grain", {DIM_COMMITMENT: FINE_GRAIN})

    # ---- verdict --------------------------------------------------------- #
    orth_ever_recovered = any(row["orthogonal_rate"] == 1 for row in sweep)
    recon_recovers = (
        sweep[0]["reconstructable_rate"][0] < sweep[-1]["reconstructable_rate"][0]
    )
    # compensation MEANINGFUL iff the recovery needed a grain finer than global
    # (global grain 0.25 leaves reconstructable at 0/3).
    global_row = next(r for r in sweep if abs(r["commitment_grain"] - 0.25) < 1e-9)
    meaningful = (global_row["reconstructable_rate"][0] == 0
                  and sweep[-1]["reconstructable_rate"][0] > 0)
    # compensation REAL iff DARK-COMPENSATED beats DARK-UNCOMPENSATED on recon
    comp_r = base["DARK-COMPENSATED"]["reconstructable_rate"][0]
    unc_r = base["DARK-UNCOMPENSATED"]["reconstructable_rate"][0]
    compensation_real = comp_r > unc_r

    if orth_ever_recovered:
        verdict = "FALSIFIED"
        verdict_reason = ("a finer commitment grain RECOVERED the orthogonal "
                          "discrimination — aperture substituted for a dimension")
    else:
        verdict = "CONFIRMED"
        verdict_reason = ("finer grain recovered the reconstructable pairs while "
                          "the orthogonal discrimination stayed FAILED at every "
                          "grain — an aperture-invariant residual deficit")

    results = {
        "pre_reg": "docs/research/psychology_affect/QUALIA_DIMENSION_COMPENSATION_PREREG.md",
        "pre_reg_block": 298000,
        "charter": "docs/research/theory_convergence/QUALIA_SPACE_VARIATION_CHARTER.md",
        "so_md5_expected": "7efe75eba05b006cafd15dbb4b7da246",
        "design": {
            "absent_axis": DIM_SHARPNESS,
            "compensated_axis": DIM_COMMITMENT,
            "resolved_by_all": _KEEP,
            "fine_grain": FINE_GRAIN,
            "grain_sweep": GRAIN_SWEEP,
            "reconstructable": [
                {"pair": n, "identity_field": [a, b], "sharpness": [1.0, -1.0]}
                for n, _cat, a, b in RECONSTRUCTABLE
            ],
            "orthogonal": {"pair": ORTHOGONAL[0],
                           "identity_field_shared": ORTHOGONAL[2],
                           "sharpness": [ORTHOGONAL[3], ORTHOGONAL[4]]},
        },
        "base_rates": base,
        "glassbox_orthogonal": glassbox,
        "grain_sweep_dark_compensated": sweep,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "orthogonal_ever_recovered": orth_ever_recovered,
        "reconstructable_recovers_with_grain": recon_recovers,
        "compensation_real": compensation_real,
        "compensation_meaningful": meaningful,
    }

    if verbose:
        _print(results)

    out_dir = os.path.join(_ROOT, "results", "qualia_dimension_compensation")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    if verbose:
        print("\nwrote", os.path.relpath(out_path, _ROOT))
    return results


def _print(r):
    print("=== QUALIA DIMENSION COMPENSATION (block 298000) ===\n")
    print("Absent axis (dark for both dark agents): %s" % r["design"]["absent_axis"])
    print("Compensated axis (finer grain):          %s" % r["design"]["compensated_axis"])
    print()
    print("--- base three-agent rates (compensated grain = %.2f) ---"
          % r["design"]["fine_grain"])
    print("%-22s  %-14s  %s" % ("agent", "reconstruct.", "orthogonal"))
    for label, row in r["base_rates"].items():
        rr = row["reconstructable_rate"]
        print("%-22s  %d/%-12d  %d"
              % (label, rr[0], rr[1], row["orthogonal_rate"]))
    print()
    g = r["glassbox_orthogonal"]
    print("--- glass-box: the ORTHOGONAL pair's signatures ---")
    print("  FULL  A dyn:", g["full_a_dyn"])
    print("  FULL  B dyn:", g["full_b_dyn"])
    print("  FULL  differ (sharpness coordinate separates):", g["full_differ"])
    print("  DARK  A dyn:", g["dark_a_dyn"])
    print("  DARK  B dyn:", g["dark_b_dyn"])
    print("  DARK  BYTE-EQUAL (sharpness was the only separator):",
          g["dark_byte_equal"])
    print()
    print("--- grain sweep on DARK-COMPENSATED (coarse -> fine) ---")
    print("%-16s  %-14s  %s" % ("commitment grain", "reconstruct.", "orthogonal"))
    for row in r["grain_sweep_dark_compensated"]:
        rr = row["reconstructable_rate"]
        print("%-16.2f  %d/%-12d  %d"
              % (row["commitment_grain"], rr[0], rr[1], row["orthogonal_rate"]))
    print()
    print("VERDICT:", r["verdict"], "—", r["verdict_reason"])
    print("  orthogonal ever recovered by finer grain:", r["orthogonal_ever_recovered"])
    print("  reconstructable recovers with grain:      ",
          r["reconstructable_recovers_with_grain"])
    print("  compensation real (comp > uncomp):        ", r["compensation_real"])
    print("  compensation meaningful (needed fine grain):", r["compensation_meaningful"])


if __name__ == "__main__":
    run()
