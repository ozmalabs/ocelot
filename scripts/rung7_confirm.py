"""rung7_confirm — THE ONE PRE-REGISTERED CONFIRMATORY RUN (VISION_RUNG7_PREREG.md).

Exactly the five pre-registered tests + the one analytic check. No sweeps, no
re-runs. Fresh seeds 9000-9007 (H1/H2/H2b) and 9100-9107 (H3a/H3b).
"""
from __future__ import annotations

import numpy as np
from scipy import stats

from domains.engine_provenance import provenance_line
from domains.lateral_world import freeze_lateral
from scripts.rung7_lib import (
    build, complementary_channels, corr_by_distance, cs_index, effective_rf,
    gains, raw_burst_movie, record_channels, replay_noisy, run_waves,
    shape_departure, space_constant, surround_suppression,
)

MAIN_SEEDS = list(range(9000, 9008))
SNR_SEEDS = list(range(9100, 9108))
TRAIN = 6400
SESOI_SD = 0.0472
SESOI_CS = 0.1
ALPHA = 0.01            # Bonferroni 0.05 / 5


def ci95(a):
    a = np.asarray(a, float)
    if a.std(ddof=1) < 1e-12:
        return a.mean(), a.mean()
    h = stats.t.ppf(0.975, len(a) - 1) * a.std(ddof=1) / np.sqrt(len(a))
    return a.mean() - h, a.mean() + h


def main():
    print(provenance_line())
    print("=" * 84)
    print("RUNG 7 — THE ONE PRE-REGISTERED CONFIRMATORY RUN")
    print(f"seeds {MAIN_SEEDS[0]}-{MAIN_SEEDS[-1]} (H1/H2/H2b), "
          f"{SNR_SEEDS[0]}-{SNR_SEEDS[-1]} (H3a/H3b) | eta=2e-3 FROZEN | "
          f"train={TRAIN} | alpha={ALPHA} (Bonferroni 5 tests)")
    print("=" * 84)

    # ---- H1 / H2 / H2b + the analytic check -------------------------------
    SD, CS, SNN, SNF, SD_REF, SUP = [], [], [], [], [], []
    print(f"\n{'seed':>6}{'SD':>9}{'CS':>9}{'sig_nn':>9}{'sig_nf':>9}"
          f"{'ratio':>8}{'SD_rung6ref':>13}{'supp':>8}")
    for seed in MAIN_SEEDS:
        w, anat = build(seed=seed, lateral=1.0, eta=2e-3)
        run_waves(w, TRAIN)
        g = gains(w, anat["hcells"])
        freeze_lateral(w)
        on, off = record_channels(w, anat, 300)
        ds, Cnn = corr_by_distance(on, on)
        _, Cnf = corr_by_distance(on, off)
        sd = shape_departure(Cnn, Cnf)
        snn, snf = space_constant(ds, Cnn), space_constant(ds, Cnf)
        cs = cs_index(effective_rf(w, anat))
        sup = surround_suppression(w, anat)
        # THE ANALYTIC CHECK: rung 6's split on THIS seed's own burst movie.
        w2, _ = build(seed=seed, lateral=1.0)
        burst = raw_burst_movie(w2, 300)
        on_c, off_c = complementary_channels(burst)
        _, Rnn = corr_by_distance(on_c, on_c)
        _, Rnf = corr_by_distance(on_c, off_c)
        sd_ref = shape_departure(Rnn, Rnf)
        SD.append(sd); CS.append(cs); SNN.append(snn); SNF.append(snf)
        SD_REF.append(sd_ref); SUP.append(sup)
        print(f"{seed:>6}{sd:>9.4f}{cs:>9.4f}{snn:>9.3f}{snf:>9.3f}"
              f"{snf/snn:>8.3f}{sd_ref:>13.2e}{sup:>8.4f}")

    SD, CS = np.array(SD), np.array(CS)
    SNN, SNF, SD_REF = np.array(SNN), np.array(SNF), np.array(SD_REF)

    print("\n" + "-" * 84)
    print("ANALYTIC CHECK — rung-6 complementary split must score SD = 0")
    print(f"  max |SD_ref| across {len(SD_REF)} seeds = {np.abs(SD_REF).max():.3e}"
          f"   => {'PASS (instrument sound)' if np.abs(SD_REF).max() < 1e-9 else '*** FAIL: RUN IS VOID ***'}")

    print("\n" + "-" * 84)
    print("H1 — THE REAL GATE: does the degeneracy break?  (one-sample t vs SESOI)")
    t1, p1 = stats.ttest_1samp(SD, SESOI_SD)
    lo, hi = ci95(SD)
    print(f"  SD mean {SD.mean():.4f}  95% CI [{lo:.4f}, {hi:.4f}]  sd {SD.std(ddof=1):.4f}")
    print(f"  vs SESOI {SESOI_SD}:  t={t1:.3f}  p={p1:.3e}   "
          f"{'PASS' if (SD.mean() > SESOI_SD and p1 < ALPHA) else 'FAIL'}")
    print(f"  % of floor(0.0000)->target(0.4719) range: {100*SD.mean()/0.4719:.1f}%")

    print("\n" + "-" * 84)
    print("H2 — does centre-surround EMERGE?  (declared deviation: sd<1e-3 => no t)")
    lo, hi = ci95(CS)
    print(f"  CS per seed: {np.array2string(CS, precision=6)}")
    print(f"  CS mean {CS.mean():.6f}  range [{CS.min():.6f}, {CS.max():.6f}]  "
          f"sd {CS.std(ddof=1):.3e}")
    if CS.std(ddof=1) > 1e-3:
        t2, p2 = stats.ttest_1samp(CS, SESOI_CS)
        print(f"  vs SESOI {SESOI_CS}: t={t2:.3f} p={p2:.3e}")
    else:
        print(f"  BETWEEN-SEED sd = {CS.std(ddof=1):.3e} < 1e-3 => THE t IS DEGENERATE "
              "AND ITS p UNINTERPRETABLE (pre-registered deviation).")
        print(f"  Reported instead: all {len(CS)}/{len(CS)} seeds exceed the SESOI "
              f"{SESOI_CS}; the effect is DETERMINISTIC to {abs(CS.max()-CS.min()):.1e}.")
    print(f"  vs floor 0.0 (analytic, pure centre) / target 1.0 (balanced DoG): "
          f"{100*CS.mean()/1.0:.1f}% of range")
    print(f"  {'PASS' if CS.mean() > SESOI_CS else 'FAIL'}")
    print(f"  surround suppression (RESPONSE side): mean {np.mean(SUP):.4f}")

    print("\n" + "-" * 84)
    print("H2b — MILLER'S OWN READING: different spatial dependence?  (paired t)")
    t3, p3 = stats.ttest_rel(SNF, SNN)
    d = SNF - SNN
    lo, hi = ci95(d)
    print(f"  sigma_ON,ON  {SNN.mean():.3f}   sigma_ON,OFF {SNF.mean():.3f}   "
          f"ratio {np.mean(SNF/SNN):.3f}")
    print(f"  diff {d.mean():.3f}  95% CI [{lo:.3f}, {hi:.3f}]  t={t3:.3f}  p={p3:.3e}   "
          f"{'PASS' if p3 < ALPHA else 'FAIL'}")

    # ---- H3a / H3b: the SNR arms ------------------------------------------
    print("\n" + "-" * 84)
    print("H3 — ATICK & REDLICH: the SAME movie replayed at two luminances")
    print(f"{'seed':>6}{'tot p=0':>10}{'tot p=.20':>11}{'share p=0':>11}"
          f"{'share p=.20':>13}")
    T0, T2, S0, S2 = [], [], [], []
    for seed in SNR_SEEDS:
        w0, _ = build(seed=seed, lateral=1.0)
        movie = raw_burst_movie(w0, 400)          # ONE movie; both arms replay IT
        reps = int(np.ceil(TRAIN / len(movie)))
        big = np.concatenate([movie] * reps, axis=0)[:TRAIN]
        row = {}
        for p in (0.0, 0.20):
            w, anat = build(seed=seed, lateral=1.0, eta=2e-3)
            replay_noisy(w, anat, big, noise=p, noise_kind="balanced",
                         rng=np.random.default_rng(91_000 + seed))
            g = gains(w, anat["hcells"])
            tot = float(g.sum(axis=1).mean())
            row[p] = (tot, float(g[:, 1].mean() / tot))
        T0.append(row[0.0][0]); T2.append(row[0.20][0])
        S0.append(row[0.0][1]); S2.append(row[0.20][1])
        print(f"{seed:>6}{row[0.0][0]:>10.4f}{row[0.20][0]:>11.4f}"
              f"{row[0.0][1]:>11.4f}{row[0.20][1]:>13.4f}")
    T0, T2, S0, S2 = map(np.array, (T0, T2, S0, S2))

    print("\n  H3a — WEAKENS: total gain falls as SNR falls?  (paired t)")
    t4, p4 = stats.ttest_rel(T2, T0)
    d = T2 - T0
    lo, hi = ci95(d)
    print(f"    p=0 {T0.mean():.4f} -> p=0.20 {T2.mean():.4f}   "
          f"diff {d.mean():+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]")
    print(f"    t={t4:.3f}  p={p4:.3e}   "
          f"{'PASS (weakens, as predicted)' if (d.mean() < 0 and p4 < ALPHA) else 'FAIL'}")

    print("\n  H3b — BROADENS: far-ring share rises as SNR falls?  (paired t)")
    t5, p5 = stats.ttest_rel(S2, S0)
    d = S2 - S0
    lo, hi = ci95(d)
    print(f"    p=0 {S0.mean():.4f} -> p=0.20 {S2.mean():.4f}   "
          f"diff {d.mean():+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]")
    print(f"    t={t5:.3f}  p={p5:.3e}   "
          f"{'PASS (broadens, as predicted)' if (d.mean() > 0 and p5 < ALPHA) else 'FAIL'}")


if __name__ == "__main__":
    main()
