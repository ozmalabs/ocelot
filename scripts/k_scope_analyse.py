#!/usr/bin/env python3
"""PHASE 1 — ARE THE TWO RUNGS' MEASUREMENTS DISTINGUISHABLE AT ALL?

Pre-registration: VISION_K_SCOPE_PREREG.md @ 32e1d62b (committed BEFORE any
number here). This script applies the pre-registered decision rule
MECHANICALLY. It re-analyses committed per-frame rows; it runs no substrate,
draws no calibration seed and consumes NO seed from block 76000-76999.

  G1  reproduce both published contrasts from raw rows (>= 6 dp)   [gate]
  G2  floor-independence of the primary read-out                   [gate, by
      source audit -- see the RESULTS doc; asserted here from the seed]
  D   paired difference-of-differences, primary size-match
  D'  paired difference-of-differences, secondary size-match

Every predicted/published value is read from the pre-registration constants
below, never re-typed from the output.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- values PUBLISHED by the two rungs, quoted from their committed docs ----
# accumulation rung, cp=90, GROWN - RAND_UNIFORM
PUB_ACCUM = {"C1": (0.0360, 0.0086, 0.0635), "C2": (0.0054, -0.0062, 0.0171)}
# cut-mint rung, C-C, NOABSTAIN_SUB - UNIFORM
PUB_CUTMINT = {"C1": (-0.0235, -0.0498, 0.0028), "C2": (-0.0235, -0.0606, 0.0135)}

BOOT_SEED = 20260720          # pre-registered; a bootstrap RNG, not a seed block
BOOT_REPS = 10000
BLOCKS = 5                    # 5 contiguous blocks of 10 held-out frames
T_CRIT_49 = 2.009575234489209  # scipy.stats.t.ppf(0.975, 49)


def paired_t_ci(d):
    """95% paired t-CI on the mean of d (df = n-1). Matches the two rungs'
    own `paired_ci95`, which is why G1 can reproduce their endpoints."""
    d = np.asarray(d, dtype=float)
    n = len(d)
    m = float(d.mean())
    sd = float(d.std(ddof=1))
    hw = T_CRIT_49 * sd / np.sqrt(n) if n == 50 else None
    return {"n": n, "mean": m, "sd": sd, "lo": m - hw, "hi": m + hw,
            "t": m / (sd / np.sqrt(n))}


def block_bootstrap_ci(d, blocks=BLOCKS, reps=BOOT_REPS, seed=BOOT_SEED):
    """Moving-block bootstrap over CONTIGUOUS blocks of held-out frames.

    The held-out set is 5 blocks of 10 consecutive frames; both rungs state
    n=50 overstates the effective n. Resampling whole blocks respects that.
    """
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


def excludes_zero(ci):
    return bool((ci["lo"] > 0.0) or (ci["hi"] < 0.0))


def load():
    out = {}
    cut = json.load(open(os.path.join(ROOT, "results", "cut_mint.json")))
    acc = json.load(open(os.path.join(ROOT, "results", "video_accum.json")))
    assert acc["held"] == cut["held"], "held-out frame lists differ"
    assert acc["train"] == cut["train"], "training frame lists differ"
    for cid in ("C1", "C2"):
        rows = json.load(open(os.path.join(
            ROOT, "results", f"video_accum_rows_{cid}.json")))["90"]
        arms = cut["corpora"][cid]["arms"]
        out[cid] = {
            "GROWN": np.array(rows["GROWN"]["max_rows"], dtype=float),
            "RAND_UNIFORM": np.array(rows["RAND_UNIFORM"]["max_rows"], dtype=float),
            "NOABSTAIN_SUB": np.array(arms["NOABSTAIN_SUB"]["max_rows"], dtype=float),
            "NOABSTAIN_PRE": np.array(arms["NOABSTAIN_PRE"]["max_rows"], dtype=float),
            "UNIFORM": np.array(arms["UNIFORM"]["max_rows"], dtype=float),
            "K_accum": acc["corpora"][cid]["checkpoints"]["90"]["arms"]["GROWN"]["K"],
            "K_cutmint": arms["NOABSTAIN_SUB"]["K"],
        }
    out["_held"] = acc["held"]
    return out


def main():
    D = load()
    R = {"prereg": "32e1d62b",
         "engine_of_data": json.load(open(os.path.join(
             ROOT, "results", "video_accum.json")))["provenance"],
         "held": D["_held"], "corpora": {}}

    # ---------------------------------------------------------------- G1
    g1_ok = True
    for cid in ("C1", "C2"):
        d = D[cid]
        a = paired_t_ci(d["GROWN"] - d["RAND_UNIFORM"])
        c = paired_t_ci(d["NOABSTAIN_SUB"] - d["UNIFORM"])
        pa, pc = PUB_ACCUM[cid], PUB_CUTMINT[cid]
        chk = {
            "accum_mean": (round(a["mean"], 4), pa[0], bool(abs(a["mean"] - pa[0]) < 5e-5)),
            "accum_lo": (round(a["lo"], 4), pa[1], bool(abs(a["lo"] - pa[1]) < 5e-5)),
            "accum_hi": (round(a["hi"], 4), pa[2], bool(abs(a["hi"] - pa[2]) < 5e-5)),
            "cutmint_mean": (round(c["mean"], 4), pc[0], bool(abs(c["mean"] - pc[0]) < 5e-5)),
            "cutmint_lo": (round(c["lo"], 4), pc[1], bool(abs(c["lo"] - pc[1]) < 5e-5)),
            "cutmint_hi": (round(c["hi"], 4), pc[2], bool(abs(c["hi"] - pc[2]) < 5e-5)),
        }
        ok = all(v[2] for v in chk.values())
        g1_ok = g1_ok and ok
        R["corpora"][cid] = {"G1": {"checks": chk, "pass": ok},
                             "accum_contrast": a, "cutmint_contrast": c,
                             "K_accum": d["K_accum"], "K_cutmint": d["K_cutmint"]}
        print(f"[G1 {cid}] reproduce published contrasts: "
              f"{'PASS' if ok else 'FAIL'}")
        for k, v in chk.items():
            print(f"    {k:<14} mine={v[0]:+.4f} published={v[1]:+.4f} "
                  f"{'ok' if v[2] else 'MISMATCH'}")
    R["G1_pass"] = g1_ok
    if not g1_ok:
        print("\nG1 FAILED — the re-analysis path does not reproduce the "
              "numbers it re-analyses. STOPPING per pre-registration §2.")
        json.dump(R, open(os.path.join(ROOT, "results", "k_scope.json"), "w"),
                  indent=1)
        return 1

    # ------------------------------------------------- the Phase-1 statistic
    print()
    for cid in ("C1", "C2"):
        d = D[cid]
        acc_delta = d["GROWN"] - d["RAND_UNIFORM"]
        prim = acc_delta - (d["NOABSTAIN_SUB"] - d["UNIFORM"])   # D
        seco = acc_delta - (d["NOABSTAIN_PRE"] - d["UNIFORM"])   # D'
        ent = R["corpora"][cid]
        for name, vec in (("D_primary", prim), ("D_secondary", seco)):
            t = paired_t_ci(vec)
            b = block_bootstrap_ci(vec)
            verdict = excludes_zero(t) and excludes_zero(b)
            ent[name] = {"t_ci": t, "block_boot": b,
                         "t_excludes_zero": excludes_zero(t),
                         "boot_excludes_zero": excludes_zero(b),
                         "DISTINGUISHABLE": bool(verdict)}
            print(f"[{cid} {name}] mean={t['mean']:+.4f} "
                  f"t-CI [{t['lo']:+.4f}, {t['hi']:+.4f}] t={t['t']:+.2f} "
                  f"excl0={excludes_zero(t)} | "
                  f"block-boot [{b['lo']:+.4f}, {b['hi']:+.4f}] "
                  f"excl0={excludes_zero(b)} "
                  f"=> {'DISTINGUISHABLE' if verdict else 'NOT DISTINGUISHABLE'}")
        # pre-registered: verdicts must agree, else take the conservative one
        p, s = ent["D_primary"], ent["D_secondary"]
        agree = p["DISTINGUISHABLE"] == s["DISTINGUISHABLE"]
        ent["VERDICT"] = bool(p["DISTINGUISHABLE"] and s["DISTINGUISHABLE"])
        ent["size_matches_agree"] = bool(agree)
        print(f"[{cid}] size-matches agree={agree} -> "
              f"VERDICT {'DISTINGUISHABLE' if ent['VERDICT'] else 'NOT DISTINGUISHABLE'}")
        print()

    # ------------------------------- POSITIVE CONTROL ON THE DECIDING GATE
    # The block bootstrap is what issues every NOT-DISTINGUISHABLE verdict
    # above, so PROTOCOL §1 clause 4 applies to IT: an instrument that has
    # never been able to separate is not an instrument. Shift C1's own
    # D_primary by a constant and require the bootstrap to bite; feed it a
    # zero-mean vector and require it not to.
    base = (D["C1"]["GROWN"] - D["C1"]["RAND_UNIFORM"]) - (
        D["C1"]["NOABSTAIN_SUB"] - D["C1"]["UNIFORM"])
    pc = {}
    for shift in (0.05, 0.10, 0.20):
        b = block_bootstrap_ci(base - base.mean() + shift)
        pc[f"shift_{shift}"] = {"lo": b["lo"], "hi": b["hi"],
                                "separates": excludes_zero(b)}
    rng = np.random.RandomState(BOOT_SEED + 1)
    b0 = block_bootstrap_ci(rng.normal(0.0, base.std(ddof=1), size=50))
    pc["null_zero_mean"] = {"lo": b0["lo"], "hi": b0["hi"],
                            "separates": excludes_zero(b0)}
    R["block_bootstrap_positive_control"] = pc
    print("---- POSITIVE CONTROL on the deciding instrument ----")
    for k, v in pc.items():
        print(f"    {k:<18} [{v['lo']:+.4f}, {v['hi']:+.4f}] "
              f"separates={v['separates']}")
    ok_pc = (pc["shift_0.2"]["separates"] and not pc["null_zero_mean"]["separates"])
    R["block_bootstrap_is_able_to_separate"] = bool(ok_pc)
    print(f"    => bootstrap IS able to separate: {ok_pc}")
    print()

    # per-corpus block means, so the reader can see where the variance lives
    for cid in ("C1", "C2"):
        bm = R["corpora"][cid]["D_primary"]["block_boot"]["block_means"]
        print(f"[{cid}] D_primary per-block means (5 blocks of 10 frames): "
              + ", ".join(f"{x:+.4f}" for x in bm))
    print()

    # ------------------------------------------------------------- POST-HOC
    # NOT PRE-REGISTERED. LABELLED POST-HOC. CHANGES NO PHASE-1 VERDICT.
    # If the block bootstrap is the honest instrument for THIS data -- and the
    # pre-registered rule says it is, because both rungs' own bounds state
    # n=50 overstates the effective n -- then intellectual consistency
    # requires disclosing what that same instrument does to the two INPUT
    # contrasts. Suppressing it would be selective reporting.
    print("---- POST-HOC (not pre-registered; changes no verdict) ----")
    R["POSTHOC_inputs_under_block_bootstrap"] = {}
    for cid in ("C1", "C2"):
        d = D[cid]
        ph = {}
        for name, vec in (
                ("accum_GROWN_minus_UNIFORM", d["GROWN"] - d["RAND_UNIFORM"]),
                ("cutmint_C_C", d["NOABSTAIN_SUB"] - d["UNIFORM"])):
            t = paired_t_ci(vec)
            b = block_bootstrap_ci(vec)
            ph[name] = {"t_ci": t, "block_boot": b,
                        "t_excludes_zero": excludes_zero(t),
                        "boot_excludes_zero": excludes_zero(b),
                        "width_ratio": (b["hi"] - b["lo"]) / (t["hi"] - t["lo"])}
            print(f"[{cid} {name}] mean={t['mean']:+.4f} "
                  f"t-CI [{t['lo']:+.4f}, {t['hi']:+.4f}] excl0={excludes_zero(t)} "
                  f"| block-boot [{b['lo']:+.4f}, {b['hi']:+.4f}] "
                  f"excl0={excludes_zero(b)} "
                  f"(boot/t width x{ph[name]['width_ratio']:.2f})")
        R["POSTHOC_inputs_under_block_bootstrap"][cid] = ph
    print()

    # POST-HOC: WHERE BETWEEN 5 AND 50 IS THE EFFECTIVE n?
    # The t-CI treats 50 frames as 50 units (anti-conservative by both rungs'
    # own bounds); the block bootstrap treats them as 5 (conservative). The
    # honest answer lies between, and lag-1 autocorrelation WITHIN blocks
    # estimates where: n_eff = n (1-rho) / (1+rho).
    print("---- POST-HOC: effective n (not pre-registered) ----")
    R["POSTHOC_effective_n"] = {}
    for cid in ("C1", "C2"):
        vec = R["corpora"][cid]["D_primary"]
        d = (D[cid]["GROWN"] - D[cid]["RAND_UNIFORM"]) - (
            D[cid]["NOABSTAIN_SUB"] - D[cid]["UNIFORM"])
        rhos = []
        for b in range(BLOCKS):
            blk = d[b * 10:(b + 1) * 10]
            blk = blk - blk.mean()
            denom = float((blk ** 2).sum())
            if denom > 0:
                rhos.append(float((blk[:-1] * blk[1:]).sum() / denom))
        rho = float(np.mean(rhos))
        n_eff = 50.0 * (1.0 - rho) / (1.0 + rho)
        # THE WITHIN-BLOCK LAG-1 STATISTIC IS BLIND BY CONSTRUCTION: it
        # demeans each block, so it cannot see a BLOCK-LEVEL random effect --
        # which is the dependence that actually matters here. The variance
        # decomposition below is the diagnostic that can see it. If the
        # observed spread of block means exceeds what independent frames
        # would produce (sd_within / sqrt(10)), the BLOCK is the right unit
        # and the block bootstrap is the correct instrument.
        blk_means = np.array([d[b * 10:(b + 1) * 10].mean()
                              for b in range(BLOCKS)])
        sd_within = float(np.mean([d[b * 10:(b + 1) * 10].std(ddof=1)
                                   for b in range(BLOCKS)]))
        sd_blk_obs = float(blk_means.std(ddof=1))
        sd_blk_iid = sd_within / np.sqrt(10.0)
        infl = sd_blk_obs / sd_blk_iid
        R["POSTHOC_effective_n"][cid] = {
            "lag1_rho_within_blocks": rho, "n_eff_from_lag1": n_eff,
            "BLIND_BY_CONSTRUCTION": "lag-1 demeans each block; cannot see a "
                                     "block-level effect",
            "sd_within": sd_within, "sd_block_means_observed": sd_blk_obs,
            "sd_block_means_if_iid": sd_blk_iid,
            "block_effect_inflation": infl,
            "block_is_the_right_unit": bool(infl > 1.5)}
        print(f"    [{cid}] within-block lag-1 rho={rho:+.3f} -> n_eff~{n_eff:.1f} "
              f"[BLIND to block-level effects]")
        print(f"         block-mean sd observed={sd_blk_obs:.4f} vs "
              f"iid-predicted={sd_blk_iid:.4f}  -> inflation x{infl:.2f}  "
              f"block-is-right-unit={infl > 1.5}")
    print()

    n_sep = sum(R["corpora"][c]["VERDICT"] for c in ("C1", "C2"))
    R["n_corpora_distinguishable"] = n_sep
    R["PHASE2_AUTHORISED"] = bool(n_sep >= 1)
    print(f"corpora distinguishable: {n_sep}/2  ->  PHASE 2 "
          f"{'AUTHORISED' if R['PHASE2_AUTHORISED'] else 'NOT AUTHORISED — STOP'}")

    json.dump(R, open(os.path.join(ROOT, "results", "k_scope.json"), "w"),
              indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
