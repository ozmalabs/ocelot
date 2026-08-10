#!/usr/bin/env python3
"""THE k=1 HOLE IN THE COLOUR REFUSAL BOUND — confirmatory run.

Pre-registration: VISION_COLOUR_BOUND_K1_PREREG.md (committed BEFORE this run at
`d27ba21a`, §3).

The landed rung (VISION_COLOUR_BOUND_RESULTS.md) gave `ci_assign` an admission bound —
the minted codebook's PACKING RADIUS `r_i = 1/2 min_{j!=i} ||c_i-c_j||` — and left it OFF
by default because the radius is UNDEFINED at k=1: with one minted quantum the guard
`Not(Exists(o != winner: ...))` is vacuously true and any colour is admitted.

PART A asks whether a k=1 bound FALLS OUT (§13) or whether none exists, auditing five
rivals and rejecting by MEASUREMENT wherever a measurement can decide it. PART B flips the
default under the three-condition rule fixed in advance (prereg §5).

This runner CONSTRUCTS stimuli, READS attributes back, and TALLIES (mechanical I/O, §0).
Every admit/refuse decision is made by the SEED RULES (`ci_assign` / `ci_refuse`). The
predicates recomputed here in Python (`_packing_admits`, `_r4_admits`, `_r3_bound`) are
INDEPENDENT re-derivations used to MEASURE the graph's decision and to evaluate the rival
candidates; they are never fed back into the graph.

Run from the gamma-substrate dir:
    python scripts/colour_bound_k1_measure.py
"""
from __future__ import annotations
import json
import math
import os
import random
import time

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import colour_bound_world as cbw  # noqa: E402
from domains import colour_identity_world as ciw  # noqa: E402
from scripts import colour_identity_measure as cim  # noqa: E402
from scripts.colour_bound_measure import (  # noqa: E402
    _packing_admits, _packing_radius, _cat_coords, _boot,
    FAR_PROBE, OFF_PROTO_PROBE, A, B, C,
)

# Pre-registered confirmatory blocks. 50000-50199 were consumed by the landed rung
# (VISION_PROTOCOL.md ledger); 50000-50099 is used here ONLY as the already-burned
# §3.3 pilot / cross-check block, never as a confirmatory arm.
SEEDS_DISAGREE = range(50200, 50300)
SEEDS_FLOOR = range(50300, 50400)
SEEDS_PILOT_BURNED = range(50000, 50100)

# The five LANDED scenes, verbatim from the landed rung's delta_on().
_RAMP = [dict(cL=10 + i, cM=10, cS=20) for i in range(36)]
_DISS = [dict(cL=15, cM=5, cS=20) if (1 <= r <= 3 and 1 <= c <= 3)
         else dict(cL=5, cM=15, cS=20) for r in range(6) for c in range(6)]
_SPLIT = [dict(cL=10, cM=10, cS=20) if c < 3 else dict(cL=20, cM=20, cS=40)
          for r in range(6) for c in range(6)]
_FLOOR = [dict(cL=v, cM=v, cS=2 * v) for v in [3 + i for i in range(36)]]

LANDED_SCENES = {
    "colour_identity_E_3clusters": cim._grid([A] * 12 + [B] * 12 + [C] * 12),
    "colour_identity_G_gradient": cim._grid(_RAMP),
    "achromatopsia_DISSOCIATION": cim._grid(_DISS),
    "achromatopsia_SPLIT_CLEAN": cim._grid(_SPLIT),      # k=1
    "achromatopsia_FLOOR": cim._grid(_FLOOR),            # k=1
}
K1_SCENE = LANDED_SCENES["achromatopsia_SPLIT_CLEAN"]


# --- scene construction --------------------------------------------------------
def _scene(cells, *, bound=None):
    """Build + settle a scene. `bound=None` uses the SEED DEFAULT (so the flip is
    actually exercised); a float writes the flag explicitly."""
    s, ag = _boot()
    h = cbw.add_field(s, cells=cells)
    if bound is None:
        ciw.set_flag(s, identity=1.0)      # does NOT write `bound` -> seed default
    else:
        cbw.set_flags(s, identity=1.0, bound=bound)
    cbw.tick(s)
    return s, h


def _probe_scene(s, h, spec, *, bound=None):
    n = cbw.add_region(s, h, dict(**spec, rrow=9, rcol=0))
    if bound is None:
        ciw.set_flag(s, identity=1.0)
    else:
        cbw.set_flags(s, identity=1.0, bound=bound)
    cbw.tick(s)
    return cbw.probe_readout(s, n)


def _distinct_obs(s, h):
    return sorted(set(zip(cbw.read_attr(s, h, "crg"), cbw.read_attr(s, h, "cby"))))


def _seed_default_bound():
    seed = json.load(open(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "seeds", "vision_colour_identity.json")))
    return float(seed["nodes"][0]["attrs"]["bound"])


# --- the RIVAL candidate predicates, re-derived independently ------------------
def _r3_bound(distinct_obs):
    """R3 — the scene's measured dynamic range (T3's anchor idiom): half the maximum
    pairwise distance among DISTINCT OBSERVED colour values."""
    return max([0.0] + [math.dist(p, q) for p in distinct_obs for q in distinct_obs]) / 2.0


def _r3_admits(obs, cats, distinct_obs):
    winner = min(cats, key=lambda c: (math.dist(obs, c), c))
    return math.dist(obs, winner) <= _r3_bound(distinct_obs)


def _r4_gap(obs, cats, distinct_obs):
    """R4 — observed-separation: min distance from the winner to another DISTINCT
    OBSERVED colour value, excluding the observation's own value and the winner
    itself. None = UNDEFINED (the k=1 failure mode this arm measures)."""
    winner = min(cats, key=lambda c: (math.dist(obs, c), c))
    others = [v for v in distinct_obs
              if tuple(v) != tuple(obs) and tuple(v) != tuple(winner)]
    return min((math.dist(winner, o) for o in others), default=None)


def _r4_admits(obs, cats, distinct_obs):
    winner = min(cats, key=lambda c: (math.dist(obs, c), c))
    gap = _r4_gap(obs, cats, distinct_obs)
    return True if gap is None else (2.0 * math.dist(obs, winner) <= gap)


# ---- A: the k=1 DEFECT REPRODUCED (flag ON) -----------------------------------
def arm_A():
    """RISKED. With the bound ARMED and a single-quantum codebook, a probe 276 units
    away is still admitted — the hole, reproduced on the armed build."""
    s, h = _scene(K1_SCENE, bound=1.0)
    cats = _cat_coords(s)
    r = _probe_scene(s, h, FAR_PROBE, bound=1.0)
    d = math.dist((r["crg"], r["cby"]), cats[0]) if cats else None
    ok = (len(cats) == 1 and r["ci_refused"] == 0.0 and r["sign_dist"] > 0.0
          and abs(r["sign_dist"] - 276.4797) < 1e-3)
    return {"k": len(cats), "categories": cats,
            "packing_radius": _packing_radius(cats),
            "probe": r, "probe_dist": round(d, 4) if d is not None else None,
            "admitted": int(r["ci_refused"] == 0.0), "PASS": bool(ok)}


# ---- MONO: the derivation — the radius is NON-INCREASING under codebook growth --
def arm_MONO():
    """RISKED. r_i(S') <= r_i(S) for S subset S' (a min over a superset cannot
    increase), so the k=1 radius upper-bounds every radius reachable by growth. That
    supremum is UNBOUNDED, hence r(k=1) = +inf: admit everything. Any FINITE k=1
    candidate r0 is exceeded by an exhibited extension, which is what kills it."""
    chain = [[(0, 0)], [(0, 0), (100, 0)], [(0, 0), (100, 0), (20, 0)]]
    radii = []
    for cb in chain:
        r = _packing_radius(cb)["(0, 0)"]
        radii.append(r)
    # non-increasing, reading undefined (k=1) as +inf
    seq = [math.inf if r is None else r for r in radii]
    monotone = all(seq[i] >= seq[i + 1] for i in range(len(seq) - 1))

    # For every finite candidate r0, exhibit an extension whose radius EXCEEDS r0.
    exceeded = {}
    for r0 in (0.0, math.sqrt(2) / 2, 1.0, 138.24):
        d = 4.0 * r0 + 1.0                      # extension distance
        r_ext = _packing_radius([(0, 0), (d, 0)])["(0, 0)"]
        exceeded[str(round(r0, 4))] = {"extension_at": round(d, 4),
                                       "extension_radius": r_ext,
                                       "exceeds_candidate": bool(r_ext > r0)}
    all_exceeded = all(v["exceeds_candidate"] for v in exceeded.values())

    # The GRAPH's own decision must show the shrink, not just the algebra: one fixed
    # observation, admitted at k=1, refused once the codebook grows around it.
    s1, h1 = _scene(K1_SCENE, bound=1.0)
    r_k1 = _probe_scene(s1, h1, FAR_PROBE, bound=1.0)
    s2, h2 = _scene(cim._grid([A] * 12 + [B] * 12 + [C] * 12), bound=1.0)
    r_k3 = _probe_scene(s2, h2, FAR_PROBE, bound=1.0)
    graph_shrinks = (r_k1["ci_refused"] == 0.0 and r_k3["ci_refused"] == 1.0)

    ok = bool(monotone and all_exceeded and graph_shrinks and radii[0] is None)
    return {"growth_chain": [str(c) for c in chain],
            "radii_of_c1": radii, "monotone_non_increasing": bool(monotone),
            "finite_candidates_exceeded": exceeded,
            "all_finite_candidates_exceeded": bool(all_exceeded),
            "graph_k1_admits": int(r_k1["ci_refused"] == 0.0),
            "graph_k3_refuses": int(r_k3["ci_refused"] == 1.0),
            "graph_shows_the_shrink": bool(graph_shrinks),
            "k1_radius_is_undefined": radii[0] is None,
            "PASS": ok}


# ---- NONLOCAL: R3 (the scene dynamic range) REJECTED BY MEASUREMENT ------------
def arm_NONLOCAL():
    """RISKED. R3 is the only rival that is finite, non-zero and defined at k=1 in a
    scene with >=2 distinct values. It is rejected on TWO measurements: (a) it is 0.0
    in BOTH landed k=1 scenes, so it degenerates to R1 exactly where the hole is; and
    (b) NON-LOCALITY — the same observation against the same codebook flips verdict
    when an UNRELATED patch is added elsewhere in the field."""
    # (a) R3 on the landed k=1 scenes
    landed_k1 = {}
    for name in ("achromatopsia_SPLIT_CLEAN", "achromatopsia_FLOOR"):
        s, h = _scene(LANDED_SCENES[name], bound=1.0)
        dob = _distinct_obs(s, h)
        landed_k1[name] = {"k": len(_cat_coords(s)), "n_distinct_obs": len(dob),
                           "r3_bound": round(_r3_bound(dob), 4)}
    degenerate = all(v["r3_bound"] == 0.0 for v in landed_k1.values())

    # (b) the NON-LOCALITY probe: same codebook {(0,0)}, same observation (30,0)
    cats, obs = [(0, 0)], (30, 0)
    without = [(0, 0), obs]
    with_patch = [(0, 0), obs, (400, 0)]        # an UNRELATED far patch elsewhere
    a_admits = _r3_admits(obs, cats, without)
    b_admits = _r3_admits(obs, cats, with_patch)
    flips = (a_admits != b_admits)

    ok = bool(degenerate and flips and not a_admits and b_admits)
    return {"r3_on_landed_k1_scenes": landed_k1,
            "r3_degenerates_to_zero_at_k1": bool(degenerate),
            "nonlocality": {
                "codebook": cats, "observation": list(obs),
                "scene_without_patch": {"distinct": [list(x) for x in without],
                                        "r3_bound": round(_r3_bound(without), 4),
                                        "admits": bool(a_admits)},
                "scene_with_unrelated_patch": {
                    "patch": [400, 0], "distinct": [list(x) for x in with_patch],
                    "r3_bound": round(_r3_bound(with_patch), 4),
                    "admits": bool(b_admits)},
                "verdict_flips": bool(flips)},
            "PASS": ok}


# ---- UNDEF: R4 (observed separation) — CONSISTENT BUT UNDEFINED ---------------
def arm_UNDEF():
    """RISKED. R4 is the ONLY rival consistent with the landed k>=2 bound (0
    disagreements over the 100 already-burned probes) — and it is UNDEFINED in exactly
    the k=1 cases that matter. The rivals that are DEFINED at k=1 are INCONSISTENT;
    the one that is CONSISTENT is UNDEFINED."""
    # (a) agreement with the packing predicate at k>=2, over the BURNED pilot block
    s, h = _scene(cim._grid([A] * 12 + [B] * 12 + [C] * 12), bound=1.0)
    cats = _cat_coords(s)
    base = _distinct_obs(s, h)
    dis, n_int = 0, 0
    for sd in SEEDS_PILOT_BURNED:
        rng = random.Random(sd)
        s2, h2 = _scene(cim._grid([A] * 12 + [B] * 12 + [C] * 12), bound=1.0)
        r = _probe_scene(s2, h2, dict(cL=rng.randint(0, 60), cM=rng.randint(0, 60),
                                      cS=rng.randint(0, 60)), bound=1.0)
        obs = (r["crg"], r["cby"])
        n_int += int(float(obs[0]).is_integer() and float(obs[1]).is_integer())
        dis += int(_packing_admits(obs, cats) != _r4_admits(obs, cats, set(base) | {obs}))

    # (b) definedness at k=1 — the landed k=1 scenes AND the k=1 defect scene
    undefined = {}
    for name in ("achromatopsia_SPLIT_CLEAN", "achromatopsia_FLOOR"):
        s3, h3 = _scene(LANDED_SCENES[name], bound=1.0)
        c3, d3 = _cat_coords(s3), _distinct_obs(s3, h3)
        undefined[name] = {"k": len(c3), "n_distinct_obs": len(d3),
                           "r4_gap": _r4_gap(c3[0], c3, d3)}
    s4, h4 = _scene(K1_SCENE, bound=1.0)
    c4 = _cat_coords(s4)
    r4p = _probe_scene(s4, h4, FAR_PROBE, bound=1.0)
    d4 = _distinct_obs(s4, h4)
    obs4 = (r4p["crg"], r4p["cby"])
    undefined["k1_defect_scene_with_far_probe"] = {
        "k": len(c4), "n_distinct_obs": len(d4),
        "r4_gap": _r4_gap(obs4, c4, d4)}
    all_undef = all(v["r4_gap"] is None for v in undefined.values())

    ok = bool(dis == 0 and all_undef and n_int == len(SEEDS_PILOT_BURNED))
    return {"agreement_with_packing_at_k_ge_2": {
                "n": len(SEEDS_PILOT_BURNED), "disagreements": dis,
                "seeds": [SEEDS_PILOT_BURNED.start, SEEDS_PILOT_BURNED.stop - 1],
                "note": "already-burned pilot block, NOT a confirmatory arm"},
            "integer_opponent_coords": f"{n_int}/{len(SEEDS_PILOT_BURNED)}",
            "r1prime_sqrt2_over_2_indistinguishable_from_0": bool(
                n_int == len(SEEDS_PILOT_BURNED)),
            "undefined_at_k1": undefined, "r4_undefined_everywhere_at_k1": all_undef,
            "PASS": ok}


# ---- EXTENT: R1 characterised (ENTAILED, reported NOT banked) ------------------
def arm_EXTENT():
    """ENTAILED (§13.1), declared unrisked in advance: ci_mint_category clusters by
    EXACT value, so a quantum's members all sit at distance 0 and the empirical
    cluster extent is identically 0. Reported as the structural root of the null —
    every length scale in this seed lives BETWEEN prototypes."""
    out = {}
    for name, cells in LANDED_SCENES.items():
        s, h = _scene(cells, bound=1.0)
        cats = _cat_coords(s)
        obs = list(zip(cbw.read_attr(s, h, "crg"), cbw.read_attr(s, h, "cby")))
        ext = 0.0
        for c in cats:
            ext = max([ext] + [math.dist(o, c) for o in obs if tuple(o) == tuple(c)])
        out[name] = {"k": len(cats), "cluster_extent": ext}
    return {"per_scene": out,
            "max_cluster_extent": max(v["cluster_extent"] for v in out.values()),
            "ENTAILED_not_banked": True}


# ---- NOREG: NO REGRESSION — THE CONJUNCTION (default FLIPPED) -----------------
def arm_NOREG():
    """RISKED, and it is THE GATE (process rule 5): a refuse-everything build scores a
    perfect floor on the refusal arms and is caught HERE. Everything runs on the SEED
    DEFAULT (bound=None), so this arm exercises the flip itself."""
    # (a) the 36-cell k=3 field
    s, h = _scene(cim._grid([A] * 12 + [B] * 12 + [C] * 12))
    dists = cbw.read_attr(s, h, "sign_dist")
    refs = cbw.refusals(s, h)
    a = {"n_assigned": sum(1 for d in dists if d >= 0.0),
         "n_refused": sum(1 for x in refs if x > 0.5),
         "all_dist_zero": bool(all(abs(d) < 1e-9 for d in dists)),
         "signs_correct": bool(cim._all_signs_correct(s, h))}
    a["PASS"] = bool(a["n_assigned"] == 36 and a["n_refused"] == 0
                     and a["all_dist_zero"] and a["signs_correct"])

    # (b) the landed dist-4 off-prototype probe — 3.81 INSIDE the risk region
    s2, h2 = _scene(cim._grid([A] * 12 + [B] * 12 + [C] * 12))
    rb = _probe_scene(s2, h2, OFF_PROTO_PROBE)
    b = {**rb, "PASS": bool(rb["ci_refused"] == 0.0
                            and abs(rb["sign_dist"] - 4.0) < 1e-9
                            and rb["sign_rg"] == 10.0 and rb["sign_by"] == 0.0)}

    # (c) recognize-not-re-mint
    s3, h3 = _scene(cim._grid([A] * 12 + [B] * 12 + [C] * 12))
    k_before = cbw.n_categories(s3)
    rc = _probe_scene(s3, h3, A)
    k_after = cbw.n_categories(s3)
    c = {**rc, "n_cats_before": k_before, "n_cats_after": k_after,
         "PASS": bool(rc["ci_refused"] == 0.0 and abs(rc["sign_dist"]) < 1e-9
                      and k_before == k_after == 3)}

    # (d) THE k=1 FIELD — the regime the bound does not reach must still assign
    s4, h4 = _scene(K1_SCENE)
    d4 = cbw.read_attr(s4, h4, "sign_dist")
    r4 = cbw.refusals(s4, h4)
    d = {"k": cbw.n_categories(s4),
         "n_assigned": sum(1 for x in d4 if x >= 0.0),
         "n_refused": sum(1 for x in r4 if x > 0.5),
         "all_dist_zero": bool(all(abs(x) < 1e-9 for x in d4))}
    d["PASS"] = bool(d["k"] == 1 and d["n_assigned"] == 36 and d["n_refused"] == 0
                     and d["all_dist_zero"])

    return {"seed_default_bound_in_force": _seed_default_bound(),
            "a_k3_field": a, "b_off_prototype_probe": b,
            "c_recognize_not_remint": c, "d_k1_field": d,
            "PASS": bool(a["PASS"] and b["PASS"] and c["PASS"] and d["PASS"])}


# ---- DISAGREE: pointwise agreement, n=100, seeds 50200-50299 -------------------
def arm_DISAGREE():
    """RISKED. The graph's admit/refuse decision vs the independently re-derived
    packing predicate, at k>=2 AND at k=1, on the SEED DEFAULT. Non-degenerate both
    ways at k>=2, so neither a refuse-everything nor an admit-everything build passes."""
    out = {}
    for label, cells in (("k3", cim._grid([A] * 12 + [B] * 12 + [C] * 12)),
                         ("k1", K1_SCENE)):
        s0, h0 = _scene(cells)
        cats = _cat_coords(s0)
        dis, n_adm, n_ref, rows = 0, 0, 0, []
        for sd in SEEDS_DISAGREE:
            rng = random.Random(sd)
            s, h = _scene(cells)
            r = _probe_scene(s, h, dict(cL=rng.randint(0, 60), cM=rng.randint(0, 60),
                                        cS=rng.randint(0, 60)))
            graph_admits = (r["ci_refused"] < 0.5)
            derived = _packing_admits((r["crg"], r["cby"]), cats)
            dis += int(graph_admits != derived)
            n_adm += int(graph_admits)
            n_ref += int(not graph_admits)
            rows.append({"seed": sd, "obs": [r["crg"], r["cby"]],
                         "graph_admits": int(graph_admits), "derived": int(derived)})
        out[label] = {"k": len(cats), "n": len(rows), "disagreements": dis,
                      "n_admitted": n_adm, "n_refused": n_ref, "rows": rows}
    ok = (out["k3"]["disagreements"] == 0 and out["k1"]["disagreements"] == 0
          and out["k3"]["n_admitted"] >= 1 and out["k3"]["n_refused"] >= 1)
    return {"seeds": [SEEDS_DISAGREE.start, SEEDS_DISAGREE.stop - 1],
            **out, "PASS": bool(ok)}


# ---- FLOOR: iid colour noise, n=100, seeds 50300-50399 ------------------------
def arm_FLOOR():
    """RISKED. Noise must mint nothing and sign nothing, on the SEED DEFAULT."""
    minted, signed = 0, 0
    for sd in SEEDS_FLOOR:
        rng = random.Random(sd)
        cells = cim._grid([dict(cL=rng.randint(0, 99), cM=rng.randint(0, 99),
                                cS=rng.randint(0, 99)) for _ in range(36)])
        s, h = _scene(cells)
        minted += int(cbw.n_categories(s) > 0)
        signed += int(any(d >= 0.0 for d in cbw.read_attr(s, h, "sign_dist")))
    ok = (minted == 0 and signed == 0)
    return {"n": len(SEEDS_FLOOR), "fields_minting": minted,
            "fields_with_signs": signed,
            "seeds": [SEEDS_FLOOR.start, SEEDS_FLOOR.stop - 1], "PASS": bool(ok)}


# ---- DELTA_ON_FLIPPED: the enumerated §9 delta --------------------------------
def delta_on_flipped():
    """RISKED. Every changed field across the five landed scenes with the default
    FLIPPED (bound=None reads the seed) vs the pre-flip behaviour (bound=0.0)."""
    def stats(cells, *, bound):
        s, h = _scene(cells, bound=bound)
        dists = cbw.read_attr(s, h, "sign_dist")
        return {"n_categories": cbw.n_categories(s), "categories": cbw.categories(s),
                "n_assigned": sum(1 for d in dists if d >= 0.0),
                "n_refused": sum(1 for x in cbw.refusals(s, h) if x > 0.5),
                "signs": cbw.signs(s, h), "max_sign_dist": max(dists),
                "epoch": cbw.scene_epoch(s, h)}

    out, n_changed = {}, 0
    for name, cells in LANDED_SCENES.items():
        pre = stats(cells, bound=0.0)        # the committed pre-flip behaviour
        post = stats(cells, bound=None)      # the SEED DEFAULT, i.e. flipped
        changed = {k: [pre[k], post[k]] for k in pre if pre[k] != post[k]}
        n_changed += len(changed)
        cats = [(c["crg"], c["cby"]) for c in pre["categories"]]
        out[name] = {"k": pre["n_categories"], "packing_radius": _packing_radius(cats),
                     "pre_flip": pre, "post_flip": post, "changed": changed}

    # The k=1 dead zone: ON must be byte-identical to OFF (flip condition 3).
    k1_on = stats(K1_SCENE, bound=1.0)
    k1_off = stats(K1_SCENE, bound=0.0)
    k1_identical = (k1_on == k1_off)
    s, h = _scene(K1_SCENE, bound=1.0)
    p_on = _probe_scene(s, h, FAR_PROBE, bound=1.0)
    s2, h2 = _scene(K1_SCENE, bound=0.0)
    p_off = _probe_scene(s2, h2, FAR_PROBE, bound=0.0)
    probe_identical = (p_on == p_off)

    return {"n_changed_fields_across_landed_scenes": n_changed, "scenes": out,
            "k1_dead_zone": {"scene_stats_identical_on_vs_off": bool(k1_identical),
                             "far_probe_identical_on_vs_off": bool(probe_identical),
                             "probe_on": p_on, "probe_off": p_off},
            "PASS": bool(n_changed == 0 and k1_identical and probe_identical)}


def main():
    t0 = time.time()
    res = {
        "rung": "the k=1 hole in the colour refusal bound",
        "prereg": "VISION_COLOUR_BOUND_K1_PREREG.md",
        "prereg_commit": "d27ba21a",
        "engine": provenance_line(),
        "seed_default_bound": _seed_default_bound(),
        "seeds_burned": {"disagree": [50200, 50299], "floor": [50300, 50399],
                         "pilot_already_burned": [50000, 50099]},
        "A_k1_defect_reproduced": arm_A(),
        "MONO_derivation": arm_MONO(),
        "NONLOCAL_r3_rejected": arm_NONLOCAL(),
        "UNDEF_r4_rejected": arm_UNDEF(),
        "EXTENT_r1_characterised": arm_EXTENT(),
        "NOREG_no_regression": arm_NOREG(),
        "DISAGREE_pointwise": arm_DISAGREE(),
        "FLOOR_noise": arm_FLOOR(),
        "DELTA_ON_FLIPPED": delta_on_flipped(),
    }
    gated = ["A_k1_defect_reproduced", "MONO_derivation", "NONLOCAL_r3_rejected",
             "UNDEF_r4_rejected", "NOREG_no_regression", "DISAGREE_pointwise",
             "FLOOR_noise", "DELTA_ON_FLIPPED"]
    res["ALL_GATED_ARMS_PASS"] = all(res[k]["PASS"] for k in gated)
    res["elapsed_s"] = round(time.time() - t0, 1)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "results", "colour_bound_k1_measure.json")
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")

    print(res["engine"])
    print(f"seed default bound = {res['seed_default_bound']}")
    for k in gated:
        print(f"  {k:26s} PASS={res[k]['PASS']}")
    print(f"  EXTENT (entailed) max cluster extent = "
          f"{res['EXTENT_r1_characterised']['max_cluster_extent']}")
    print(f"ALL_GATED_ARMS_PASS = {res['ALL_GATED_ARMS_PASS']}  ({res['elapsed_s']}s)")
    print("wrote", out)


if __name__ == "__main__":
    main()
