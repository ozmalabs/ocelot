"""LOCALITY INDEX — re-derive the payoff on the POST-BATCH engine.

*** THIS IS A MEASURING INSTRUMENT. IT CHANGES NO BEHAVIOUR. ***

Pre-registration: `VISION_LOCALITY_INDEX_PREREG.md`, committed at `38283565`
BEFORE this file existed and before any measurement.

THE QUESTION, AND WHY IT IS NOT THE PREDECESSOR'S QUESTION.
`VISION_SCALE_SPLIT_RESULTS.md` recommended a locality index on the strength of
a survival log-slope of -0.9928 ("99.93% of candidates could never have won").
`VISION_BATCH_APPLY_RESULTS.md` then measured that same slope at -0.0002 once
the re-derivation loop was removed, flipping hypothesis (a) ARCHITECTURAL ->
COMPUTATIONAL, and concluded: A SURVIVAL SLOPE IS NOT A CENTRALIZATION DETECTOR
WHILE A RE-DERIVATION LOOP IS IN THE PATH. Its §9.2 instructs the next rung to
re-derive the payoff from the post-batch numbers. That is this script.

THE SAME INSTRUMENT, DELIBERATELY. Everything that defines a measurement -- the
grid list, WARMUP/TICKS, the sweep point, the bucket definition, the log-log
fit, the liveness gate and the conservation asserts -- is IMPORTED from
`scale_split_measure.py` rather than reimplemented, on the batch rung's
precedent (its §1: "a before/after claim is worth nothing if the before is not
the thing that was measured before"). Only the ANALYSIS is new.

THE THREE THINGS MEASURED, and why each is the shape it is:

  1. HUB PURITY (exact, no model). Every hot edge type is minted from the ONE
     Retina node. A locality index replaces `edges_by_type(t)` with
     `neighbours(hub, t)` -- and on a perfect star those are THE SAME SET. This
     measures the purity rather than asserting it, because the whole
     recommendation turns on it.

  2. ATTRIBUTION (exact, no model). `rule_costs()` gives a per-rule enumeration
     COUNT. For a scan-path rule each enumeration enumerates exactly
     |edges_by_type(first_edge)| candidates, so `cand_enum_scan` must reproduce
     as an integer combination of (count x cardinality). This is strictly
     stronger than the predecessor's divisibility gate: it says WHICH rules,
     not merely that the total divides. If it does not reproduce, the residual
     is a THIRD mechanism wearing the star's shape and the rung stops here.

  3. THE CEILING (exact, no model). The pre-registered headroom is
     (S - A_ideal)/T for some ideal index output A_ideal >= 0. Its SUPREMUM
     over every conceivable index is S/T, at A_ideal = 0 -- i.e. an index that
     removes the ENTIRE scan term for free. Evaluating the pre-registered
     decision rule at that supremum is the most generous reading available and
     needs no model of the index at all. If S/T fails the rule, every index
     fails it, and that is a theorem rather than an estimate.

     The pre-registered attribute-index model (A_attr) is reported ALONGSIDE
     it, never instead of it: A_attr >= 0 implies saving(A_attr) <= S, so the
     ceiling DOMINATES it logically. Both are reported because the prereg fixed
     both, and reporting only the ceiling would hide the shape of the loss.

USAGE
    python scripts/locality_index_measure.py --out results/locality_index.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3 -- a non-pytest entrypoint pins its OWN tree's engine.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402

# THE INSTRUMENT, IMPORTED WHOLE. Not a reimplementation (see the docstring).
from scripts.scale_split_measure import (  # noqa: E402
    AUDIT, SIZES, TICKS, WARMUP, _boot_eye, _frames, _load_state, _machine,
    _run, buckets, counters, fit,
)
from domains.wave_world import WaveWorld  # noqa: E402
from domains.lateral_world import add_lateral_retina, set_lat_params  # noqa: E402

# The hot edge types, read off the WORLD BUILDERS rather than chosen: every one
# of these is minted from `self.retina` / `world.retina` (wave_world.py:158,463;
# lateral_world.py:93,100). PROTOCOL §13 -- this list falls out of the adapter's
# own construction, it is not a parameter.
HUB_EDGE_TYPES = ["has_cell", "has_unit", "has_hcell", "has_lbipolar"]

# The rules whose FIRST match-edge (after `reorder_match_edges`) is a hub edge,
# i.e. the ones that can reach the `(None, None)` scan branch at all. Read off
# the seeds, not chosen.
STAR_RULES = ["wv_propagate", "wv_refract", "wv_recover",
              "lat_pool", "lat_residual", "lat_learn_gain", "lat_bipolar"]

# --- A CORRECTION I MADE TO MY OWN INSTRUMENT, BEFORE REPORTING ANYTHING -----
#
# My FIRST implementation of the attribution test asserted a per-rule model:
# every star rule scans its full edge set on every enumeration, so
# `cand_enum_scan == sum over rules of enumerations x cardinality`. THAT TEST
# FAILED (measured 55,040 against a predicted 85,760 at 256 cells), and the
# failure is informative rather than fatal:
#
#   `Substrate` keeps a PER-RULE, PER-EDGE-TYPE CURSOR (`rule_cursors`,
#   substrate.rs:1560) and an incremental path that drives only edges added
#   since the last visit. A rule whose cursor is still valid and whose driving
#   edge type gained no edges enumerates ZERO candidates -- while
#   `rule_cost_count` still increments. So an enumeration COUNT is not a scan
#   count, and WHICH enumerations fall back to a full re-match is decided by
#   cursor validity, not by the topology.
#
# THE PRE-REGISTERED TEST WAS NEVER THE PER-RULE ONE. Prereg §3 fixes H1's
# statistic as: "`cand_enum_scan` is exactly reproduced as a NON-NEGATIVE
# INTEGER COMBINATION of hot edge-type cardinalities." My script was STRICTER
# than my pre-registration -- it demanded a per-rule assignment H1 never
# claimed. Correcting the implementation to compute the statistic actually
# pre-registered is not metric surgery (PROTOCOL §5): the measure is unchanged,
# the code that computed it was wrong. Both the failure and the correction are
# reported in the results rather than quietly fixed, and the per-rule
# attribution is recorded as a BOUND that this rung does NOT establish.


def hub_purity(s):
    """For each hot edge type: does ONE node own every edge of that type?

    `max_hub_outdegree / |edges_by_type|` == 1.0 is a perfect star, and on a
    perfect star `neighbours(hub, t)` IS `edges_by_type(t)` -- so a locality
    restriction skips exactly zero candidates. Exact, integer, no model."""
    out = {}
    for et in HUB_EDGE_TYPES:
        src_counts = {}
        total = 0
        for nid in s.nodes():
            for tgt in s.neighbours(nid, et) or []:
                src_counts[nid] = src_counts.get(nid, 0) + 1
                total += 1
        if not total:
            out[et] = {"edges": 0, "distinct_srcs": 0, "max_hub_outdegree": 0,
                       "purity": None, "locality_saving": 0}
            continue
        mx = max(src_counts.values())
        out[et] = {
            "edges": total,
            "distinct_srcs": len(src_counts),
            "max_hub_outdegree": mx,
            "purity": mx / total,
            # What a locality index would SAVE on this edge type, exactly:
            # the scan enumerates `edges`, the hub traversal enumerates the
            # hub's own out-degree. On a perfect star the difference is 0.
            "locality_saving": total - mx,
        }
    return out


def state_histogram(s, world):
    """Node-state counts -- the input to the pre-registered A_attr model.

    A real attribute index on `(RetinaCell, state)` returns every cell in the
    probed state; the where-clause's REMAINING conjuncts then reject some of
    those. So this is the index's OUTPUT, not the survivor count, which is
    exactly what an index-then-verify probe would have to enumerate."""
    hist = {}
    for n in world.cells.values():
        st = s.node(n)["attrs"].get("state")
        hist[str(st)] = hist.get(str(st), 0) + 1
    return hist


def measure_point(g):
    """One grid of the PRIMARY arm -- assembled eye, frame-driven.

    Byte-for-byte `scale_split_measure.counted_point(g, "constant",
    driven=True, arm="eye")`, with two additions that read state and CHANGE
    NOTHING: a per-tick state histogram, and `rule_costs()` afterwards."""
    s, ag, _ = _boot_eye(g)
    world = WaveWorld(s, h=g, w=g, seed=0, fovea_radius=0)
    add_lateral_retina(world)
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    for cp in s.nodes("ChangeParams"):
        s.set_attr(cp, "change", 1.0)
        s.set_attr(cp, "sustain", 1.0)
    set_lat_params(world, lateral=1.0)

    frames = _frames(g)
    _run(world, WARMUP, g, "constant", frames)

    purity = hub_purity(s)

    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    s._inner.reset_rule_costs()
    hists = []
    for i in range(TICKS):
        hists.append(state_histogram(s, world))
        f = frames[i % len(frames)]
        world.step(ignite_k=1 if i % 5 == 0 else 0, frame=f)
    AUDIT.scale_audit_set_enabled(False)
    c = counters()
    costs = {name: {"micros_CONTAMINABLE": mic, "enumerations": cnt,
                    "progress": prog}
             for name, mic, cnt, prog in s._inner.rule_costs()}

    # §6.4 CONSERVATION, inherited verbatim -- a split that does not add up is
    # a broken split.
    assert c["cand_enum_first"] + c["cand_enum_repeat"] == c["cand_enum"], (g, c)
    assert (c["cand_enum_scan"] + c["cand_enum_local"] + c["cand_enum_hinted"]
            == c["cand_enum"]), (g, c)
    if c["cand_enum"] == 0:
        raise SystemExit(f"DEAD INSTRUMENT at g={g}: zero candidates enumerated.")

    b = buckets(c)
    edge_card = {et: purity[et]["edges"] for et in HUB_EDGE_TYPES}

    # --- H1 ATTRIBUTION: the PRE-REGISTERED statistic, exactly ---------------
    # "cand_enum_scan is exactly reproduced as a non-negative integer
    # combination of hot edge-type cardinalities."
    #
    # Every hot cardinality here is an integer multiple of the cell count (a
    # measured fact, asserted below, not an assumption), so the combination
    # exists iff `scan` is an exact multiple of the cell count. The quotient
    # `q` is then the number of FULL-SET scans performed, and it must fit
    # inside the star rules' enumeration budget -- a scan that no star-rule
    # enumeration could have produced would be the third mechanism H1 is
    # looking for.
    scan = c["cand_enum_scan"]
    cells = g * g
    for et, m in edge_card.items():
        if m:
            assert m % cells == 0, (et, m, cells)
    q_exact = (scan % cells == 0)
    q = scan // cells
    budget = sum(costs.get(r, {}).get("enumerations", 0) for r in STAR_RULES)
    # Each full-set scan costs at least `cells` candidates (has_cell / has_hcell)
    # and at most max_card; so q counted in units of cells must not exceed the
    # budget scaled by the largest hub cardinality.
    max_mult = max((m // cells) for m in edge_card.values() if m) if edge_card else 1
    within_budget = q <= budget * max_mult

    mean_hist = {}
    for h in hists:
        for k_, v_ in h.items():
            mean_hist[k_] = mean_hist.get(k_, 0) + v_
    for k_ in mean_hist:
        mean_hist[k_] /= max(len(hists), 1)

    # --- A_attr: the pre-registered attribute-index model, MOST GENEROUS -----
    # Per-rule attribution is NOT established (see the correction note above),
    # so the assignment is chosen in the direction that FAVOURS BUILDING:
    # assume EVERY full-set scan is index-eligible on the SPARSEST state, i.e.
    # every scan gets the best reduction any of these rules could get. A real
    # mixture can only do worse. `lat_*`'s guards are step-relative and admit
    # no equality index at all (prereg §1.3), so charging them the sparsest
    # state is strictly generous.
    sparsest = min((v for k_, v in mean_hist.items() if k_ != "None"),
                   default=0.0)
    a_attr = int(round(q * sparsest))
    per_rule = {r: {"enumerations": costs.get(r, {}).get("enumerations", 0)}
                for r in STAR_RULES}

    row = {
        "grid": g, "cells": g * g,
        "counters": c, "buckets": b,
        "rule_costs": costs,
        "hub_purity": purity,
        "mean_state_histogram": mean_hist,
        "attribution": {
            "cand_enum_scan_measured": scan,
            "cells": cells,
            "edge_cardinalities": edge_card,
            "all_hub_cards_are_multiples_of_cells": True,   # asserted above
            "quotient_full_set_scans": q,
            "is_exact_integer_combination": q_exact,
            "star_rule_enumeration_budget": budget,
            "within_enumeration_budget": within_budget,
            "exact": bool(q_exact and within_budget),
            "star_rule_enumerations": per_rule,
        },
        "S_scan": scan,
        "T_total_ops": b["total"],
        "V_survivors": c["leaf_visits"],
        "A_attr": a_attr,
        # THE CEILING: the supremum of the pre-registered headroom over every
        # conceivable index (A_ideal = 0, an index that removes the whole scan
        # term for free).
        # The PREDECESSOR'S denominator, carried for continuity: the batch rung
        # reported the residual as 34.3% of `cand_enum`. Reported alongside the
        # whole-system share so the two are never confused -- 34.3% of
        # enumeration is NOT 34.3% of the system.
        "scan_share_of_cand_enum": scan / max(c["cand_enum"], 1),
        "headroom_ceiling": scan / max(b["total"], 1),
        "headroom_A_attr": (scan - a_attr) / max(b["total"], 1),
        "locality_saving_total": sum(p["locality_saving"] for p in purity.values()),
    }
    del world, s, ag
    return row


def verdict(rows):
    """The decision rule, EXACTLY as fixed in prereg §4, evaluated at the
    largest grid. Not adjustable after the fact (PROTOCOL §5)."""
    last = rows[-1]
    fit_S = fit(rows, "S_scan")
    fit_A = fit(rows, "A_attr")
    fit_T = fit(rows, "T_total_ops")
    d_e = fit_S["exponent"] - fit_A["exponent"]
    r2_ok = fit_S["r2"] >= 0.95 and fit_A["r2"] >= 0.95

    def decide(headroom):
        if headroom >= 0.20 and d_e >= 0.30 and r2_ok:
            return "GO — asymptotic"
        if headroom >= 0.40:
            return "GO — constant factor"
        if headroom < 0.20 and d_e < 0.30:
            return "STOP"
        return "INDETERMINATE (resolves to STOP by PROTOCOL §9)"

    return {
        "fit_S_scan": fit_S, "fit_A_attr": fit_A, "fit_T_total": fit_T,
        "delta_exponent": d_e, "both_r2_ok": r2_ok,
        "headroom_ceiling_at_largest_grid": last["headroom_ceiling"],
        "headroom_A_attr_at_largest_grid": last["headroom_A_attr"],
        "verdict_at_ceiling": decide(last["headroom_ceiling"]),
        "verdict_at_A_attr": decide(last["headroom_A_attr"]),
        "decision_rule": (
            "GO-asymptotic iff headroom>=0.20 AND d_exponent>=0.30 (both r2>=0.95); "
            "GO-constant iff headroom>=0.40; STOP iff headroom<0.20 AND "
            "d_exponent<0.30; else INDETERMINATE -> STOP (PROTOCOL §9)"),
        "note": ("The CEILING verdict dominates: A_attr >= 0 for every index, so "
                 "saving(any index) <= S. A STOP at the ceiling is a STOP for "
                 "every index that could be built."),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    sizes = [int(x) for x in a.sizes.split(",")] if a.sizes else SIZES

    prov = provenance_line()
    print(prov, flush=True)
    print(_machine(), flush=True)

    res = {"provenance": prov, "machine": _machine(), "sizes": sizes,
           "ticks": TICKS, "warmup": WARMUP,
           "prereg": "VISION_LOCALITY_INDEX_PREREG.md @ 38283565",
           "load_state_at_start": _load_state()}

    rows = []
    print("== PRIMARY SWEEP: assembled eye, frame-driven (post-batch engine) ==",
          flush=True)
    for g in sizes:
        r = measure_point(g)
        rows.append(r)
        at = r["attribution"]
        print(f"  g={g:3d} cells={g*g:6d} | S={r['S_scan']:12,d} "
              f"T={r['T_total_ops']:12,d} | S/T={r['headroom_ceiling']:.4f} "
              f"| A_attr={r['A_attr']:11,d} headroom={r['headroom_A_attr']:.4f} "
              f"| scan/cand={r['scan_share_of_cand_enum']:.4f} "
              f"| H1 exact={at['exact']} q={at['quotient_full_set_scans']} "
              f"| locality_saving={r['locality_saving_total']}", flush=True)
    res["rows"] = rows
    res["verdict"] = verdict(rows)
    res["attribution_exact_all_grids"] = all(
        r["attribution"]["exact"] for r in rows)
    res["locality_saving_all_grids"] = [r["locality_saving_total"] for r in rows]
    res["load_state_at_end"] = _load_state()

    v = res["verdict"]
    print(f"\n  H1 attribution exact at every grid: "
          f"{res['attribution_exact_all_grids']}", flush=True)
    print(f"  H2 locality saving per grid: {res['locality_saving_all_grids']}",
          flush=True)
    print(f"  exponent S={v['fit_S_scan']['exponent']:.4f} "
          f"(r2 {v['fit_S_scan']['r2']:.5f})  "
          f"A_attr={v['fit_A_attr']['exponent']:.4f} "
          f"(r2 {v['fit_A_attr']['r2']:.5f})  delta={v['delta_exponent']:.4f}",
          flush=True)
    print(f"  headroom CEILING = {v['headroom_ceiling_at_largest_grid']:.4f} "
          f"-> {v['verdict_at_ceiling']}", flush=True)
    print(f"  headroom A_attr  = {v['headroom_A_attr_at_largest_grid']:.4f} "
          f"-> {v['verdict_at_A_attr']}", flush=True)

    if a.out:
        d = os.path.dirname(a.out)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(a.out, "w") as f:
            json.dump(res, f, indent=2, default=str)
        print("wrote", a.out, flush=True)


if __name__ == "__main__":
    main()
