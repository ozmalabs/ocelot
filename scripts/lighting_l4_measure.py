#!/usr/bin/env python3
"""ADVANCED LIGHTING RUNG L4 — SHADOW vs REFLECTANCE EDGES (confirmatory run).

Pre-registration: VISION_LIGHTING_L4_PREREG.md (committed BEFORE this run at
76f3c9f0 — §3). Every decision — whether an adjacency is an edge, whether that
edge is illuminant or reflectance, and which cells merge into one component — is
a `vision_lighting_l4` RULE. `vision_border_ownership` is used UNMODIFIED and
UNEDITED; L4 only changes what `val` field it is SHOWN.

This runner CONSTRUCTS reflectance × illuminant scenes, READS attrs back
(mechanical I/O, §0) and TALLIES metrics. The ground-truth material/gain layout
is used ONLY here for scoring — NEVER read by a seed rule.

Run from the gamma-substrate dir:
    python scripts/lighting_l4_measure.py
"""
from __future__ import annotations
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import lighting_l4_world as l4w  # noqa: E402
from domains import border_ownership_world as bow  # noqa: E402

# T3/L1/L2/L3's SIX materials, unchanged.
MATERIALS = {
    "a": (10, 20, 30), "b": (40, 15, 25), "c": (12, 44, 8),
    "d": (33, 9, 41), "e": (21, 37, 14), "f": (6, 28, 36),
}
NAMES = ["a", "b", "c", "d", "e", "f"]

# The base illuminant. DELIBERATELY NON-INTEGER so round() is genuinely active:
# on integer gains the cross-product deviation is EXACTLY 0 and arm A is
# unexercised (prereg §3 — a test that cannot round is a test that cannot fail).
G0 = 2.3

SHADOW_JUMPS = [1.5, 1.7, 2.0, 2.6, 3.0, 5.0]
CHROMATIC_GAIN = (4.0, 4.4, 5.2)        # a BLUE-SHIFTED shadow (arm G)
PROPORTIONAL = [((10, 20, 30), (20, 40, 60)), ((10, 20, 30), (15, 30, 45))]
PENUMBRA_RHOS = [1.15, 1.3]

NOISE_BASE, NOISE_N = 45680, 100        # ledger block consumed
LAYOUT_BASE, LAYOUT_N = 45780, 20       # ledger block consumed

H = W = 12
PATCH = (2, 6, 2, 6)                    # rows 2-5 x cols 2-5, material `c`
SHADOW_RECT = (7, 11, 7, 11)            # rows 7-10 x cols 7-10, gain G0*0.4
SHADOW_FACTOR = 0.4


def NEU(reflectance, g):
    """Render under a spectrally NEUTRAL illuminant of scalar strength `g`.
    The adapter takes a 3-vector gain always; this names the flat case."""
    return l4w.render(reflectance, l4w.neutral(g))


def _boot_l4():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting_l4"])
    return s, ag


def _run_row(row_cones, flag=1.0):
    """Build a 1xN L4 field from observed triples and tick to a fixpoint."""
    s, ag = _boot_l4()
    h = l4w.add_field(s, [row_cones])
    l4w.set_flag(s, lighting_l4=flag)
    sweeps = l4w.tick(s)
    return s, h, sweeps


def _row_kinds(s, h, n):
    return [{"adj": f"{c}|{c+1}", "kind": l4w.kind(s, h, 0, c),
             "margin": round(l4w.margin(s, h, 0, c), 6),
             "npairs": l4w.npairs(s, h, 0, c)} for c in range(n - 1)]


# ---------------------------------------------------------------------------
def arm_A_shadow():
    """A: a NEUTRAL cast-shadow boundary reads l4_illuminant. 36 + 1 edges.

    DECLARED ENTAILED BY THE DERIVATION (prereg §6): the envelope is a valid
    upper bound on |D_XY| under the neutral-illuminant hypothesis, so this arm
    cannot fail unless the seed does not compute what the algebra says. It is
    reported as CONSISTENCY; the rung's evidence is the conjunction A∧B∧G∧H.
    """
    rows, ok = [], 0
    for name in NAMES:
        for jump in SHADOW_JUMPS:
            r = MATERIALS[name]
            row = [NEU(r, G0), NEU(r, G0 * jump)]
            s, h, _ = _run_row(row)
            k = l4w.kind(s, h, 0, 0)
            ok += (k == "l4_illuminant")
            rows.append({"material": name, "jump": jump, "kind": k,
                         "margin": round(l4w.margin(s, h, 0, 0), 6),
                         "npairs": l4w.npairs(s, h, 0, 0),
                         "cones": [list(row[0]), list(row[1])]})
    return {"n": len(rows), "illuminant": ok, "rows": rows}


def arm_B_reflectance():
    """B: a genuine MATERIAL boundary reads l4_reflectance. All 15 pairs."""
    rows, ok = [], 0
    for i in range(len(NAMES)):
        for j in range(i + 1, len(NAMES)):
            row = [NEU(MATERIALS[NAMES[i]], G0),
                   NEU(MATERIALS[NAMES[j]], G0)]
            s, h, _ = _run_row(row)
            k = l4w.kind(s, h, 0, 0)
            ok += (k == "l4_reflectance")
            rows.append({"pair": NAMES[i] + "|" + NAMES[j], "kind": k,
                         "margin": round(l4w.margin(s, h, 0, 0), 6),
                         "npairs": l4w.npairs(s, h, 0, 0)})
    return {"n": len(rows), "reflectance": ok, "rows": rows}


def combined_scene_row():
    """The DISAGREEMENT scene: ONE graph containing exactly ONE reflectance edge
    (5|6) and exactly ONE illuminant edge (8|9)."""
    mats = ["a"] * 6 + ["c"] * 7
    gains = [G0] * 9 + [G0 * SHADOW_FACTOR] * 4
    return [NEU(MATERIALS[mats[i]], gains[i]) for i in range(13)]


def arm_D_prime_disagreement():
    """D′: in ONE scene, ONE tick, the two classes must BOTH be non-empty.

    This is the arm that a refuse-everything build AND an accept-everything
    build both fail — each empties one side. It is why neither floor alone is a
    gate (§1.1, confirmed four times in this arc).
    """
    row = combined_scene_row()
    s, h, sweeps = _run_row(row)
    kinds = _row_kinds(s, h, len(row))
    illum = [k["adj"] for k in kinds if k["kind"] == "l4_illuminant"]
    refl = [k["adj"] for k in kinds if k["kind"] == "l4_reflectance"]
    flat = [k["adj"] for k in kinds if k["kind"] == "l4_flat"]
    return {"sweeps": sweeps, "kinds": kinds,
            "illuminant_adjacencies": illum, "reflectance_adjacencies": refl,
            "flat_adjacencies": flat,
            "l4_val": l4w.val_grid(s, h)[0],
            "components": l4w.n_components(s, h),
            "both_non_empty": bool(illum) and bool(refl)}


def _scene_2d():
    """background `a` at G0; a material patch `c`; a cast-shadow rectangle."""
    r0, r1, c0, c1 = PATCH
    sr0, sr1, sc0, sc1 = SHADOW_RECT
    grid = []
    for r in range(H):
        row = []
        for c in range(W):
            mat = "c" if (r0 <= r < r1 and c0 <= c < c1) else "a"
            g = G0 * SHADOW_FACTOR if (sr0 <= r < sr1 and sc0 <= c < sc1) else G0
            row.append(NEU(MATERIALS[mat], g))
        grid.append(row)
    return grid


def _border_ownership(grid):
    """Run the UNMODIFIED vision_border_ownership seed on a val grid. Its
    aggregates are global NodesOfType('Cell') grabs, so this MUST be its own
    graph — two fields in one graph would contaminate each other."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    h = bow.add_field(s, grid)
    bow.set_flag(s, bown=1.0)
    sweeps = bow.tick(s)
    return {"sweeps": sweeps, "n_protos": bow.n_protos(s),
            "protos": bow.protos(s)}


def arm_C_object_boundary():
    """C1 / C2: a SHADOW boundary must NOT become an OBJECT boundary, while a
    MATERIAL boundary must.

    C1 is the POSITIVE CONTROL that the defect is real — if the shadow rectangle
    did not mint under RAW luminance, C2 would be demonstrating nothing.
    """
    s, ag = _boot_l4()
    h = l4w.add_field(s, _scene_2d())
    l4w.set_flag(s, lighting_l4=1.0)
    sweeps = l4w.tick(s)
    raw_grid = l4w.luminance_grid(s, h)
    l4_grid = l4w.val_grid(s, h)
    patch_root = float(PATCH[0] * W + PATCH[2])
    shadow_root = float(SHADOW_RECT[0] * W + SHADOW_RECT[2])
    # the four sides of each rectangle, as the graph classified them
    r0, r1, c0, c1 = PATCH
    sr0, sr1, sc0, sc1 = SHADOW_RECT
    patch_edges = ([l4w.kind(s, h, r, c0 - 1, "h") for r in range(r0, r1)]
                   + [l4w.kind(s, h, r0 - 1, c, "v") for c in range(c0, c1)])
    shadow_edges = ([l4w.kind(s, h, r, sc0 - 1, "h") for r in range(sr0, sr1)]
                    + [l4w.kind(s, h, sr0 - 1, c, "v") for c in range(sc0, sc1)])
    raw = _border_ownership(raw_grid)
    l4 = _border_ownership(l4_grid)
    return {
        "l4_sweeps": sweeps,
        "raw_distinct_vals": sorted({v for r in raw_grid for v in r}),
        "l4_distinct_vals": sorted({v for r in l4_grid for v in r}),
        "l4_components": l4w.n_components(s, h),
        "patch_root": int(patch_root), "shadow_root": int(shadow_root),
        "patch_boundary_kinds": sorted(set(patch_edges)),
        "shadow_boundary_kinds": sorted(set(shadow_edges)),
        "patch_boundary_all_reflectance": set(patch_edges) == {"l4_reflectance"},
        "shadow_boundary_all_illuminant": set(shadow_edges) == {"l4_illuminant"},
        "C1_RAW": raw,
        "C2_L4": l4,
        "C1_shadow_minted_on_raw":
            any(p["root"] == int(shadow_root) for p in raw["protos"]),
        "C2_shadow_minted_on_l4":
            any(p["root"] == int(shadow_root) for p in l4["protos"]),
        "C2_patch_minted_on_l4":
            any(p["root"] == int(patch_root) for p in l4["protos"]),
    }


def arm_E_penumbra():
    """E: a SOFT/gradual shadow edge. Prediction stated in advance: every ramp
    adjacency that CLEARS the lattice reads l4_illuminant; the sub-lattice tail
    is correctly NOT an edge (a penumbra is a SEQUENCE of sub-edges)."""
    out = []
    for rho in PENUMBRA_RHOS:
        r = MATERIALS["a"]
        row = [NEU(r, G0 * rho ** k) for k in range(8)]
        s, h, _ = _run_row(row)
        kinds = _row_kinds(s, h, len(row))
        edges = [k for k in kinds if k["kind"] != "l4_flat"]
        out.append({"rho": rho, "kinds": kinds,
                    "n_edges": len(edges),
                    "n_flat": len(kinds) - len(edges),
                    "n_illuminant": sum(1 for k in edges
                                        if k["kind"] == "l4_illuminant"),
                    "all_edges_illuminant":
                        all(k["kind"] == "l4_illuminant" for k in edges)})
    return {"conditions": out,
            "all_edges_illuminant": all(o["all_edges_illuminant"] for o in out)}


def arm_F_noise():
    """F: the NOISE FLOOR — FRESH seeds 45680–45779, 13 random triples each.

    F-alive (§1.1 clause 4): a classifier that fires on NOTHING scores a perfect
    floor while measuring nothing, so the number of adjacencies that got ANY
    classification is recorded beside the leak.
    """
    illum = refl = flat = unclassified = tot = 0
    leaks = []
    for sd in range(NOISE_BASE, NOISE_BASE + NOISE_N):
        rng = random.Random(sd)
        row = [tuple(rng.randint(0, 120) for _ in range(3)) for _ in range(13)]
        s, h, _ = _run_row(row)
        for c in range(12):
            k = l4w.kind(s, h, 0, c)
            tot += 1
            illum += (k == "l4_illuminant")
            refl += (k == "l4_reflectance")
            flat += (k == "l4_flat")
            unclassified += (k == "")
            for _ in range(int(k == "l4_illuminant")):
                leaks.append({"seed": sd, "adj": f"{c}|{c+1}",
                              "cR": list(row[c]), "cQ": list(row[c + 1]),
                              "margin": round(l4w.margin(s, h, 0, c), 6)})
    return {"seeds": [NOISE_BASE, NOISE_BASE + NOISE_N - 1],
            "adjacencies": tot, "illuminant": illum, "reflectance": refl,
            "flat": flat, "unclassified": unclassified,
            "classified_frac": round((tot - unclassified) / max(tot, 1), 6),
            "illuminant_frac": round(illum / max(tot, 1), 6),
            "leaks": leaks}


def arm_G_chromatic():
    """G: a CHROMATIC (spectrally non-neutral) shadow. PREDICTED NEGATIVE — the
    ratio cue is simply WRONG there, and this is the rung's real bound."""
    rows, illum = [], 0
    for name in NAMES:
        r = MATERIALS[name]
        row = [NEU(r, G0), l4w.render(r, CHROMATIC_GAIN)]
        s, h, _ = _run_row(row)
        k = l4w.kind(s, h, 0, 0)
        illum += (k == "l4_illuminant")
        rows.append({"material": name, "kind": k,
                     "margin": round(l4w.margin(s, h, 0, 0), 6),
                     "npairs": l4w.npairs(s, h, 0, 0)})
    return {"gain": list(CHROMATIC_GAIN), "n": len(rows),
            "illuminant": illum, "rows": rows}


def arm_H_proportional():
    """H: two materials that ARE scalar multiples. PREDICTED NEGATIVE — a genuine
    reflectance edge misread as a shadow. Irreducible to ANY local ratio cue."""
    rows, illum = [], 0
    for r1, r2 in PROPORTIONAL:
        row = [NEU(r1, G0), NEU(r2, G0)]
        s, h, _ = _run_row(row)
        k = l4w.kind(s, h, 0, 0)
        illum += (k == "l4_illuminant")
        rows.append({"materials": [list(r1), list(r2)], "kind": k,
                     "margin": round(l4w.margin(s, h, 0, 0), 6),
                     "npairs": l4w.npairs(s, h, 0, 0)})
    return {"n": len(rows), "illuminant": illum, "rows": rows}


def arm_J_layouts():
    """J: RANDOMISED material layouts — FRESH seeds 45780–45799."""
    tot = ok = 0
    rows = []
    for sd in range(LAYOUT_BASE, LAYOUT_BASE + LAYOUT_N):
        rng = random.Random(sd)
        mats = [rng.choice(NAMES) for _ in range(13)]
        row = [NEU(MATERIALS[m], G0) for m in mats]
        s, h, _ = _run_row(row)
        n_ok = n = 0
        for c in range(12):
            different = mats[c] != mats[c + 1]
            n += int(different)
            n_ok += int(different and l4w.kind(s, h, 0, c) == "l4_reflectance")
        tot += n
        ok += n_ok
        rows.append({"seed": sd, "boundaries": n, "reflectance": n_ok})
    return {"seeds": [LAYOUT_BASE, LAYOUT_BASE + LAYOUT_N - 1],
            "boundaries": tot, "reflectance": ok,
            "frac": round(ok / max(tot, 1), 6), "per_seed": rows}


def arm_I_bound_occupancy():
    """I: process rule 7 — the bound's OCCUPANCY on BOTH sides.

    A bound whose illuminant side sits at margin 0 and whose reflectance side
    sits at 0.001 is a bound that never binds (rung L1b measured exactly that,
    invisible because only the winner was ever reported). Both distributions,
    plus literal counts.
    """
    def stats(xs):
        xs = sorted(xs)
        return {"n": len(xs),
                "min": round(xs[0], 6) if xs else None,
                "median": round(xs[len(xs) // 2], 6) if xs else None,
                "max": round(xs[-1], 6) if xs else None}
    illum, refl = [], []
    for name in NAMES:
        for jump in SHADOW_JUMPS:
            r = MATERIALS[name]
            s, h, _ = _run_row([NEU(r, G0), NEU(r, G0 * jump)])
            illum.append(l4w.margin(s, h, 0, 0))
    for i in range(len(NAMES)):
        for j in range(i + 1, len(NAMES)):
            s, h, _ = _run_row([NEU(MATERIALS[NAMES[i]], G0),
                                NEU(MATERIALS[NAMES[j]], G0)])
            refl.append(l4w.margin(s, h, 0, 0))
    return {"illuminant_margins": stats(illum), "reflectance_margins": stats(refl),
            "bound": 1.0,
            "separation": round(min(refl) / max(illum), 4) if illum and refl else None}


def arm_X_offday():
    """X: the flag at its DEFAULT 0 — L4 fully inert."""
    row = combined_scene_row()
    s, h, sweeps = _run_row(row, flag=0.0)
    return {"l4_attrs_written_when_off": l4w.written_l4_attrs(s, h),
            "kinds": [l4w.kind(s, h, 0, c) for c in range(12)],
            "l4_val": l4w.val_grid(s, h)[0],
            "components": l4w.n_components(s, h),
            "sweeps": sweeps}


def main():
    t0 = time.time()
    res = {
        "rung": "L4 — SHADOW vs REFLECTANCE EDGES",
        "prereg": "VISION_LIGHTING_L4_PREREG.md (76f3c9f0)",
        "engine": provenance_line(),
        "base_gain": G0,
        "A_shadow_edge_classified": arm_A_shadow(),
        "B_reflectance_edge_classified": arm_B_reflectance(),
        "C_not_an_object_boundary": arm_C_object_boundary(),
        "D_prime_disagreement": arm_D_prime_disagreement(),
        "E_penumbra": arm_E_penumbra(),
        "F_noise_floor": arm_F_noise(),
        "G_chromatic_shadow_PREDICTED_NEGATIVE": arm_G_chromatic(),
        "H_proportional_materials_PREDICTED_NEGATIVE": arm_H_proportional(),
        "I_bound_occupancy": arm_I_bound_occupancy(),
        "J_randomised_layouts": arm_J_layouts(),
        "X_off_day": arm_X_offday(),
        "elapsed_s": None,
    }
    res["elapsed_s"] = round(time.time() - t0, 1)
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "lighting_l4_measure.json")
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")

    A, B, C = (res["A_shadow_edge_classified"],
               res["B_reflectance_edge_classified"],
               res["C_not_an_object_boundary"])
    D, E, F = (res["D_prime_disagreement"], res["E_penumbra"],
               res["F_noise_floor"])
    G, Hh = (res["G_chromatic_shadow_PREDICTED_NEGATIVE"],
             res["H_proportional_materials_PREDICTED_NEGATIVE"])
    I, J = res["I_bound_occupancy"], res["J_randomised_layouts"]
    print(res["engine"])
    print(f"A  shadow     : {A['illuminant']}/{A['n']} read l4_illuminant")
    print(f"B  reflectance: {B['reflectance']}/{B['n']} read l4_reflectance")
    print(f"C1 RAW        : {C['C1_RAW']['n_protos']} protos {C['C1_RAW']['protos']}"
          f"   shadow minted={C['C1_shadow_minted_on_raw']}")
    print(f"C2 L4         : {C['C2_L4']['n_protos']} protos {C['C2_L4']['protos']}"
          f"   shadow minted={C['C2_shadow_minted_on_l4']}"
          f"  patch minted={C['C2_patch_minted_on_l4']}")
    print(f"D' disagree   : illuminant={D['illuminant_adjacencies']} "
          f"reflectance={D['reflectance_adjacencies']} components={D['components']}")
    print(f"E  penumbra   : all-edges-illuminant={E['all_edges_illuminant']} "
          + " ".join(f"rho={o['rho']}:{o['n_illuminant']}/{o['n_edges']}edges,"
                     f"{o['n_flat']}flat" for o in E["conditions"]))
    print(f"F  noise floor: {F['illuminant']}/{F['adjacencies']} illuminant "
          f"({100*F['illuminant_frac']:.3f}%)  classified="
          f"{100*F['classified_frac']:.1f}%  refl={F['reflectance']} flat={F['flat']}")
    print(f"G  chromatic  : {G['illuminant']}/{G['n']} illuminant "
          f"(PREDICTED 0 — the cue FAILS on a chromatic shadow)")
    print(f"H  proportion : {Hh['illuminant']}/{Hh['n']} illuminant "
          f"(PREDICTED {Hh['n']} — irreducibly ambiguous)")
    print(f"I  occupancy  : illuminant margins {I['illuminant_margins']}")
    print(f"                reflectance margins {I['reflectance_margins']}"
          f"   separation x{I['separation']}")
    print(f"J  layouts    : {J['reflectance']}/{J['boundaries']} "
          f"({100*J['frac']:.2f}%)")
    print(f"X  off-day    : wrote {res['X_off_day']['l4_attrs_written_when_off']}")
    print("wrote", out, f"({res['elapsed_s']}s)")


if __name__ == "__main__":
    main()
