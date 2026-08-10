#!/usr/bin/env python3
"""RE-ANALYSE EVERY PUBLISHED VIDEO-LINE CONTRAST AT THE BLOCK UNIT.

Pre-registration: VISION_BLOCK_UNIT_PREREG.md @ 5c75bc39 (committed BEFORE any
contrast number here). This script applies the pre-registered classification
rule MECHANICALLY. It re-analyses committed per-frame rows; it runs no
substrate, draws no calibration seed and consumes NO seed from block
77000-77999.

  G1  reproduce every published t-CI endpoint from raw rows        [gate]
  G2  the block bootstrap is positive-controlled PER VECTOR        [gate]
  G3  bootstrap width >= t-CI width for every vector (one-way)     [gate]
  G4  no seed consumed from 77000-77999 (AST walk, in the tests)   [gate]

Every published value is read from the constant block below, quoted from the
two committed RESULTS docs, never re-typed from this script's own output.

The block bootstrap is INHERITED VERBATIM from scripts/k_scope_analyse.py.
Re-deriving or re-tuning it would be PROTOCOL Section 5.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOOT_SEED = 20260720          # inherited from the K-scope rung, unchanged
BOOT_REPS = 10000
BLOCKS = 5
T_CRIT_49 = 2.009575234489209  # scipy.stats.t.ppf(0.975, 49)

# The pre-registered floor grid and the pre-registered classification boundary.
FLOOR_GRID = [round(0.005 * i, 3) for i in range(1, 61)]   # 0.005 .. 0.300
AMBIGUOUS_FRACTION = 0.5       # fixed in the prereg; not moved


# ---------------------------------------------------------------------------
# PUBLISHED values, quoted from the two committed RESULTS docs.
# (mean, lo, hi) of the frame-unit paired t-CI, as printed there.
# ---------------------------------------------------------------------------
PUBLISHED = {
    # --- VISION_VIDEO_ACCUMULATION_RESULTS.md Section 3.1 (gate 1) ---
    ("accum", "C1", "GROWN-UNIFORM@10"): (0.0742, 0.0611, 0.0873),
    ("accum", "C1", "GROWN-UNIFORM@25"): (0.0450, 0.0111, 0.0789),
    ("accum", "C1", "GROWN-UNIFORM@45"): (0.0268, -0.0003, 0.0539),
    ("accum", "C1", "GROWN-UNIFORM@65"): (0.0802, 0.0586, 0.1018),
    ("accum", "C1", "GROWN-UNIFORM@90"): (0.0360, 0.0086, 0.0635),
    ("accum", "C2", "GROWN-UNIFORM@10"): (0.0535, 0.0457, 0.0613),
    ("accum", "C2", "GROWN-UNIFORM@25"): (-0.0321, -0.0523, -0.0119),
    ("accum", "C2", "GROWN-UNIFORM@45"): (0.0076, -0.0062, 0.0214),
    ("accum", "C2", "GROWN-UNIFORM@65"): (-0.0008, -0.0212, 0.0196),
    ("accum", "C2", "GROWN-UNIFORM@90"): (0.0054, -0.0062, 0.0171),
    # --- Section 3.2, the decomposition, at cp=90 ---
    ("accum", "C1", "GROWN-CUTMATCHED@90"): (0.0625, 0.0575, 0.0675),
    ("accum", "C2", "GROWN-CUTMATCHED@90"): (0.0475, 0.0369, 0.0580),
    ("accum", "C1", "CUTMATCHED-UNIFORM@90"): (-0.0265, -0.0513, -0.0017),
    ("accum", "C2", "CUTMATCHED-UNIFORM@90"): (-0.0420, -0.0552, -0.0288),
    # --- Section 3.3, the accept-rate co-primary ---
    ("accum", "C1", "accept_GROWN-UNIFORM@90"): (0.1000, 0.0683, 0.1317),
    ("accum", "C2", "accept_GROWN-UNIFORM@90"): (-0.0138, -0.0212, -0.0063),
    # --- Section 8, the order arm (NOT size-matched; confound is the rung's own) ---
    ("accum", "C1", "SHUFFLED-INORDER"): (0.0228, 0.0078, 0.0378),
    ("accum", "C2", "SHUFFLED-INORDER"): (-0.0090, -0.0307, 0.0128),
    # --- VISION_CUT_MINT_POLICY_RESULTS.md Section 3 ---
    ("cutmint", "C1", "C-A"): (0.0272, 0.0049, 0.0494),
    ("cutmint", "C2", "C-A"): (0.0001, -0.0340, 0.0341),
    ("cutmint", "C1", "C-B"): (0.0507, 0.0444, 0.0569),
    ("cutmint", "C2", "C-B"): (0.0236, 0.0171, 0.0300),
    ("cutmint", "C1", "C-C"): (-0.0235, -0.0498, 0.0028),
    ("cutmint", "C2", "C-C"): (-0.0235, -0.0606, 0.0135),
    ("cutmint", "C1", "C-D"): (0.0138, 0.0088, 0.0187),
    ("cutmint", "C2", "C-D"): (0.0127, 0.0060, 0.0194),
    # --- Section 3.4, the accept-rate co-primary ---
    ("cutmint", "C1", "accept_ABSTAIN-UNIFORM"): (0.0450, 0.0244, 0.0656),
    ("cutmint", "C2", "accept_ABSTAIN-UNIFORM"): (0.1200, 0.0731, 0.1669),
}

# Contrasts that exist in the committed raw JSON but were NOT printed in the
# doc's tables. G1 checks these against the rung's OWN stored contrast entry
# (still an independent check of my arithmetic, just not a doc quote).
RAW_ONLY = {
    ("cutmint", "C1", "accept_ABSTAIN-NOABSTAIN_SUB"):
        ("accept_ABSTAIN_minus_NOABSTAIN_SUB", "C1"),
    ("cutmint", "C2", "accept_ABSTAIN-NOABSTAIN_SUB"):
        ("accept_ABSTAIN_minus_NOABSTAIN_SUB", "C2"),
}


def paired_t_ci(d):
    """95% paired t-CI on the mean of d. Matches both rungs' `paired_ci95`,
    which is why G1 can reproduce their endpoints."""
    d = np.asarray(d, dtype=float)
    n = len(d)
    m = float(d.mean())
    sd = float(d.std(ddof=1))
    hw = T_CRIT_49 * sd / np.sqrt(n)
    return {"n": n, "mean": m, "sd": sd, "lo": m - hw, "hi": m + hw,
            "t": m / (sd / np.sqrt(n)), "width": 2 * hw}


def block_bootstrap_ci(d, blocks=BLOCKS, reps=BOOT_REPS, seed=BOOT_SEED):
    """INHERITED VERBATIM from scripts/k_scope_analyse.py. Do not modify."""
    d = np.asarray(d, dtype=float)
    per = len(d) // blocks
    chunks = [d[i * per:(i + 1) * per] for i in range(blocks)]
    rng = np.random.RandomState(seed)
    means = np.empty(reps)
    for r in range(reps):
        pick = rng.randint(0, blocks, size=blocks)
        means[r] = np.concatenate([chunks[p] for p in pick]).mean()
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {"lo": float(lo), "hi": float(hi), "reps": reps, "blocks": blocks,
            "block_means": [float(c.mean()) for c in chunks]}


def ci_width(ci):
    """Width, derived at the CALL SITE. Deliberately NOT a key added to
    `block_bootstrap_ci`'s return dict: that function is inherited VERBATIM
    from the K-scope rung and must stay AST-identical to it, gated by
    `test_the_block_bootstrap_is_INHERITED_VERBATIM_not_re_derived`. That gate
    caught exactly this convenience edit on its first firing."""
    return float(ci["hi"] - ci["lo"])


def excludes_zero(ci):
    return bool((ci["lo"] > 0.0) or (ci["hi"] < 0.0))


def resolution_floor(d, grid=FLOOR_GRID):
    """Smallest shift on the fixed grid at which THIS vector separates.

    The K-scope positive control, applied per vector rather than once
    globally. Returns None if the vector does not separate anywhere on the
    grid (which is itself reportable: the instrument is blind on it)."""
    d = np.asarray(d, dtype=float)
    centred = d - d.mean()
    for delta in grid:
        if excludes_zero(block_bootstrap_ci(centred + delta)):
            return float(delta)
    return None


def block_stats(d):
    """Where the variance lives: the K-scope decomposition, per vector."""
    d = np.asarray(d, dtype=float)
    bm = np.array([d[b * 10:(b + 1) * 10].mean() for b in range(BLOCKS)])
    sd_within = float(np.mean([d[b * 10:(b + 1) * 10].std(ddof=1)
                               for b in range(BLOCKS)]))
    sd_blk_obs = float(bm.std(ddof=1))
    sd_blk_iid = sd_within / np.sqrt(10.0)
    return {"sd_within": sd_within,
            "sd_block_means_observed": sd_blk_obs,
            "sd_block_means_if_iid": sd_blk_iid,
            "block_effect_inflation": (sd_blk_obs / sd_blk_iid
                                       if sd_blk_iid > 0 else float("inf")),
            "block_means": [float(x) for x in bm]}


def classify(mean, boot, floor):
    """THE PRE-REGISTERED RULE (prereg Section 4). Fixed before any number."""
    if excludes_zero(boot):
        return "SURVIVES"
    if floor is None:
        # instrument blind on this vector anywhere on the grid
        return "BELOW RESOLUTION"
    if abs(mean) >= AMBIGUOUS_FRACTION * floor:
        return "AMBIGUOUS"
    return "BELOW RESOLUTION"


# ---------------------------------------------------------------------------


def load():
    acc = json.load(open(os.path.join(ROOT, "results", "video_accum.json")))
    cut = json.load(open(os.path.join(ROOT, "results", "cut_mint.json")))
    assert acc["held"] == cut["held"], "held-out frame lists differ"
    assert acc["train"] == cut["train"], "training frame lists differ"
    V = {}
    for cid in ("C1", "C2"):
        rows = json.load(open(os.path.join(
            ROOT, "results", f"video_accum_rows_{cid}.json")))
        arms = cut["corpora"][cid]["arms"]
        shuf = acc["corpora"][cid]["shuffled"]["eval"]

        def a(cp, arm, key="max_rows"):
            return np.array(rows[cp][arm][key], dtype=float)

        for cp in ("10", "25", "45", "65", "90"):
            V[("accum", cid, f"GROWN-UNIFORM@{cp}")] = (
                a(cp, "GROWN") - a(cp, "RAND_UNIFORM"))
        V[("accum", cid, "GROWN-CUTMATCHED@90")] = (
            a("90", "GROWN") - a("90", "RAND_CUTMATCHED"))
        V[("accum", cid, "CUTMATCHED-UNIFORM@90")] = (
            a("90", "RAND_CUTMATCHED") - a("90", "RAND_UNIFORM"))
        V[("accum", cid, "accept_GROWN-UNIFORM@90")] = (
            a("90", "GROWN", "acc_rows") - a("90", "RAND_UNIFORM", "acc_rows"))
        V[("accum", cid, "SHUFFLED-INORDER")] = (
            np.array(shuf["max_rows"], dtype=float) - a("90", "GROWN"))

        def b(arm, key="max_rows"):
            return np.array(arms[arm][key], dtype=float)

        V[("cutmint", cid, "C-A")] = b("ABSTAIN") - b("UNIFORM")
        V[("cutmint", cid, "C-B")] = b("ABSTAIN") - b("NOABSTAIN_SUB")
        V[("cutmint", cid, "C-C")] = b("NOABSTAIN_SUB") - b("UNIFORM")
        V[("cutmint", cid, "C-D")] = b("ABSTAIN") - b("NOABSTAIN_PRE")
        V[("cutmint", cid, "accept_ABSTAIN-UNIFORM")] = (
            b("ABSTAIN", "acc_rows") - b("UNIFORM", "acc_rows"))
        V[("cutmint", cid, "accept_ABSTAIN-NOABSTAIN_SUB")] = (
            b("ABSTAIN", "acc_rows") - b("NOABSTAIN_SUB", "acc_rows"))
    return V, acc, cut


def episode_design_spec(sigmas, deltas):
    """HOW MANY INDEPENDENT EPISODES to resolve an effect of size delta.

    A DESIGN PROJECTION, NOT A MEASUREMENT. Assumes future episodes are
    exchangeable with these five and share sigma_b -- estimated from FIVE
    blocks, so it is itself uncertain.

    Two-sided, 80% power, unit = the episode:
        delta >= (t(.975, B-1) + t(.80, B-1)) * sigma_b / sqrt(B)
    """
    try:
        from scipy.stats import t as tdist
    except ImportError:
        return {"UNAVAILABLE": "scipy not installed"}
    out = {}
    for sname, sigma in sigmas.items():
        row = {}
        for delta in deltas:
            need = None
            for B in range(2, 100001):
                crit = (tdist.ppf(0.975, B - 1) + tdist.ppf(0.80, B - 1))
                if delta >= crit * sigma / np.sqrt(B):
                    need = B
                    break
            row[f"{delta:.2f}"] = need
        out[sname] = {"sigma_b": float(sigma), "episodes_needed": row}
    return out


def main():
    V, acc, cut = load()
    R = {"prereg": "5c75bc39",
         "engine_of_data": acc["provenance"],
         "boot_seed": BOOT_SEED, "boot_reps": BOOT_REPS, "blocks": BLOCKS,
         "ambiguous_fraction": AMBIGUOUS_FRACTION,
         "held": acc["held"], "contrasts": {}}

    g1_all, g3_all = True, True
    rows_out = []

    for key in sorted(V.keys(), key=lambda k: (k[0], k[2], k[1])):
        rung, cid, name = key
        d = V[key]
        t = paired_t_ci(d)
        boot = block_bootstrap_ci(d)
        floor = resolution_floor(d)
        bs = block_stats(d)
        cls = classify(t["mean"], boot, floor)

        # ---- G1: reproduce what is published (or what the rung stored) ----
        if key in PUBLISHED:
            pm, plo, phi = PUBLISHED[key]
            g1 = bool(abs(round(t["mean"], 4) - pm) < 5e-5 and
                      abs(round(t["lo"], 4) - plo) < 5e-5 and
                      abs(round(t["hi"], 4) - phi) < 5e-5)
            g1_src = "doc"
            g1_ref = [pm, plo, phi]
        elif key in RAW_ONLY:
            field, _ = RAW_ONLY[key]
            st = cut["corpora"][cid]["contrast"][field]
            g1 = bool(abs(t["mean"] - st["mean"]) < 5e-9 and
                      abs(t["lo"] - st["lo"]) < 5e-9 and
                      abs(t["hi"] - st["hi"]) < 5e-9)
            g1_src = "raw"
            g1_ref = [st["mean"], st["lo"], st["hi"]]
        else:
            g1, g1_src, g1_ref = None, "none", None
        if g1 is False:
            g1_all = False

        # ---- G3: the correction is one-directional (it only widens) ----
        boot_w = ci_width(boot)
        g3 = bool(boot_w >= t["width"])
        g3_all = g3_all and g3

        ent = {"rung": rung, "corpus": cid, "contrast": name,
               "t_ci": t, "block_boot": boot,
               "t_excludes_zero": excludes_zero(t),
               "boot_excludes_zero": excludes_zero(boot),
               "resolution_floor_delta_star": floor,
               "boot_width": boot_w, "t_width": t["width"],
               "width_ratio": boot_w / t["width"],
               "block_stats": bs,
               "CLASS": cls,
               "G1_reproduces": g1, "G1_source": g1_src, "G1_reference": g1_ref,
               "G3_widens": g3,
               # Section 4.1: gated -- below resolution is NOT absence.
               "reading": ("this corpus cannot resolve an effect of this size "
                           "in EITHER direction; it is NOT a demonstration "
                           "that the effect is zero or absent")
               if cls == "BELOW RESOLUTION" else None}
        R["contrasts"]["|".join(key)] = ent
        rows_out.append(ent)

        print(f"[{rung:8s} {cid} {name:26s}] mean={t['mean']:+.4f} "
              f"t[{t['lo']:+.4f},{t['hi']:+.4f}]{'*' if excludes_zero(t) else ' '} "
              f"boot[{boot['lo']:+.4f},{boot['hi']:+.4f}]"
              f"{'*' if excludes_zero(boot) else ' '} "
              f"floor={('%.3f' % floor) if floor else '  >0.300'} "
              f"x{ent['width_ratio']:.2f}  => {cls}"
              f"  G1={'ok' if g1 else ('MISMATCH' if g1 is False else '-')}")

    R["G1_all_reproduce"] = g1_all
    R["G3_correction_is_one_directional"] = g3_all

    # ---- G2: positive control on the deciding instrument, PER VECTOR ----
    # A floor was found for every vector => the bootstrap is ABLE to separate
    # on each. Plus the null control: a zero-mean vector must NOT separate.
    rng = np.random.RandomState(BOOT_SEED + 1)
    nulls = {}
    for key in [("accum", "C1", "GROWN-CUTMATCHED@90"),
                ("accum", "C1", "GROWN-UNIFORM@90"),
                ("cutmint", "C1", "C-B")]:
        sd = float(np.asarray(V[key]).std(ddof=1))
        b0 = block_bootstrap_ci(rng.normal(0.0, sd, size=50))
        nulls["|".join(key)] = {"lo": b0["lo"], "hi": b0["hi"],
                                "separates": excludes_zero(b0)}
    R["G2_null_controls"] = nulls
    R["G2_every_vector_has_a_floor"] = all(
        e["resolution_floor_delta_star"] is not None for e in rows_out)
    R["G2_no_null_separates"] = not any(v["separates"] for v in nulls.values())

    print()
    print(f"G1 all published endpoints reproduce : {g1_all}")
    print(f"G2 every vector has a measured floor : {R['G2_every_vector_has_a_floor']}")
    print(f"G2 no zero-mean null separates       : {R['G2_no_null_separates']}")
    print(f"G3 correction only ever widens       : {g3_all}")

    tally = {}
    for e in rows_out:
        tally[e["CLASS"]] = tally.get(e["CLASS"], 0) + 1
    R["tally"] = tally
    print(f"\nCLASSIFICATION over {len(rows_out)} contrasts: {tally}")

    # ---- the forward-looking half: the episode-count design spec ----
    sigmas = {
        "gate1_GROWN-UNIFORM@90_C1": R["contrasts"][
            "accum|C1|GROWN-UNIFORM@90"]["block_stats"]["sd_block_means_observed"],
        "priority_GROWN-CUTMATCHED@90_C1": R["contrasts"][
            "accum|C1|GROWN-CUTMATCHED@90"]["block_stats"]["sd_block_means_observed"],
        "priority_GROWN-CUTMATCHED@90_C2": R["contrasts"][
            "accum|C2|GROWN-CUTMATCHED@90"]["block_stats"]["sd_block_means_observed"],
        "policy_C-B_C1": R["contrasts"][
            "cutmint|C1|C-B"]["block_stats"]["sd_block_means_observed"],
        "typical_0.08": 0.08,
        "typical_0.11": 0.11,
    }
    spec = episode_design_spec(sigmas, [0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20])
    R["EPISODE_DESIGN_SPEC"] = {
        "LABEL": "DESIGN PROJECTION, NOT A MEASUREMENT",
        "assumption": "future episodes exchangeable with these five, same "
                      "sigma_b; sigma_b is itself estimated from FIVE blocks "
                      "and is correspondingly uncertain",
        "criterion": "two-sided 95% CI excludes zero with 80% power, unit = "
                     "the episode",
        "table": spec}
    print("\n---- EPISODE-COUNT DESIGN SPEC (projection, not a measurement) ----")
    for sname, row in spec.items():
        if sname == "UNAVAILABLE":
            print("   scipy unavailable")
            break
        print(f"   sigma_b={row['sigma_b']:.4f}  ({sname})")
        print("      " + "  ".join(
            f"d={k}:B={v}" for k, v in row["episodes_needed"].items()))

    json.dump(R, open(os.path.join(ROOT, "results", "block_unit.json"), "w"),
              indent=1)
    return 0 if (g1_all and g3_all) else 1


if __name__ == "__main__":
    sys.exit(main())
