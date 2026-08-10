"""eye_confirm — THE ONE CONFIRMATORY RUN. Exactly the tests VISION_EYE_PREREG.md
lists, on the seeds it allocates. No sweeps. No re-runs.

Pre-registration: `VISION_EYE_PREREG.md`, committed at 26cb7c6be3 BEFORE this ran.
Seeds: 11000-11999 (fresh, appended to the ledger). Phase 0 burns none — it
stopped at the convergence gate.
"""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.eye_world import (EyeWorld, set_params, freeze, walk,  # noqa: E402
                               diffusion_exponent, anisotropy)
from domains.engine_provenance import provenance_line  # noqa: E402

H = W = 8
ADAPT = 20_000          # fixed by §1.1 convergence, not tuned per arm
N = 12                  # fixed in advance by the pilot on burned seeds
SEED0 = 11000           # the allocated confirmatory block
KS = (100.0, 1000.0, 10000.0)   # all above the dark light i0=1


def scene(sd):
    return (np.random.default_rng(sd).random((H, W)) + 0.1)


def adapt_freeze_probe(*, logr, k, probe, env_seed):
    """PROTOCOL: adapt to the ENVIRONMENT'S STATISTICS at illumination k (a
    stream), FREEZE (a real freeze — every learning AND adaptation rule gated),
    then PROBE with a held-out scene. A per-cell reference on a STATIC scene
    erases the image (measured: mean == max == mu exactly); the eye must
    calibrate to the ensemble, and light then arrives as a perturbation."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
    w = EyeWorld(s, h=H, w=W, gaze_l=5, seed=0)
    set_params(w, eye=1.0, eye_open=1.0, logr=logr, homeo=1.0, saw=0.0,
               phase0=0.0)
    rng = np.random.default_rng(env_seed)
    for _ in range(ADAPT):
        w.step(frame=(rng.random((H, W)) + 0.1) * k)
    freeze(w)
    w.step(frame=probe * k)
    return w.responses()


def h1_illumination_invariance():
    print("=" * 72)
    print("H1 — ILLUMINATION INVARIANCE (the decisive one)")
    print("  statistic: patdiff(k) = max_i |resp_i(k) - resp_i(k=100)|")
    print("  floor:     patdiff between two DIFFERENT probe scenes at same k")
    print("  SESOI:     10% of the floor")
    print("  gate:      CONJUNCTIVE — log arm < SESOI at EVERY k")
    print("             AND linear arm > SESOI (so the measure is not inert)")
    print("=" * 72)
    out = {}
    for logr, nm in ((1.0, "LOG"), (0.0, "LINEAR")):
        pds = {k: [] for k in KS[1:]}
        floors = []
        for i in range(N):
            sd = SEED0 + i
            probe = scene(sd)
            other = scene(sd + 500)
            base = adapt_freeze_probe(logr=logr, k=KS[0], probe=probe, env_seed=sd)
            floors.append(float(np.max(np.abs(
                adapt_freeze_probe(logr=logr, k=KS[0], probe=other, env_seed=sd)
                - base))))
            for k in KS[1:]:
                r = adapt_freeze_probe(logr=logr, k=k, probe=probe, env_seed=sd)
                pds[k].append(float(np.max(np.abs(r - base))))
            print(f"  {nm:>6} seed {sd}: "
                  + " ".join(f"k={k:<6.0f} patdiff={pds[k][-1]:.5f}" for k in KS[1:])
                  + f"  floor={floors[-1]:.5f}", flush=True)
        fl = np.array(floors)
        print(f"  --- {nm}: FLOOR mean={fl.mean():.5f} sd={fl.std(ddof=1):.5f} "
              f"-> SESOI={0.1*fl.mean():.5f}")
        for k in KS[1:]:
            a = np.array(pds[k])
            ci = 1.96 * a.std(ddof=1) / np.sqrt(len(a))
            print(f"  --- {nm}: patdiff(k={k:.0f}) mean={a.mean():.5f} "
                  f"sd={a.std(ddof=1):.5f} CI95=[{a.mean()-ci:.5f}, {a.mean()+ci:.5f}] "
                  f"= {100*a.mean()/fl.mean():.2f}% of floor")
        out[nm] = (pds, fl)
    return out


def h2_weber_fechner():
    print()
    print("=" * 72)
    print("H2 — WEBER-FECHNER: slope of drive vs ln I over 4 decades above i0")
    print("  prediction (stated in advance): slope = 1.000 +/- 0.05 for logr=1")
    print("=" * 72)
    for logr, nm in ((1.0, "LOG"), (0.0, "LINEAR")):
        s, ag = boot_core()
        load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
        w = EyeWorld(s, h=H, w=W, gaze_l=5, seed=0)
        set_params(w, eye=1.0, eye_open=1.0, logr=logr, homeo=0.0, saw=0.0,
                   phase0=0.0)
        ks = [1e2, 1e3, 1e4, 1e5, 1e6]
        xs = []
        for k in ks:
            w.step(frame=np.full((H, W), 1.0) * k)
            xs.append(float(np.mean(w.drives())))
        sl = float(np.polyfit(np.log(ks), xs, 1)[0])
        print(f"  {nm:>6}: drive vs ln(I) slope = {sl:.4f}   drives={np.round(xs,3)}")
        if logr > 0.5:
            print(f"          per-decade step = {np.round(np.diff(xs),4)} "
                  f"(ln10 = {np.log(10):.4f})")


def h3_engbert_drift():
    print()
    print("=" * 72)
    print("H3 — ENGBERT DRIFT STATISTICS (Engbert 2011 PNAS 108:E765)")
    print("  model: alpha_s=1.32+/-0.02, alpha_l=0.71+/-0.06")
    print("  expt : alpha_s=1.38+/-0.05, alpha_l=0.79+/-0.11")
    print("  CONJUNCTIVE gate: alpha_s > 1 AND alpha_l < 1 AND alpha_s > alpha_l")
    print("                    AND anisotropy < 0.25 (no cardinal artifact)")
    print("=" * 72)
    for lam, nm in ((1.0, "SAW (full)"), (0.0, "ABLATED (saw_lam=0, no potential)")):
        A_s, A_l, AN = [], [], []
        for i in range(N):
            s, ag = boot_core()
            load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
            w = EyeWorld(s, h=H, w=W, gaze_l=51, seed=SEED0 + 100 + i)
            set_params(w, eye=1.0, eye_open=0.0, saw=1.0, saw_lam=lam,
                       phase0=0.0)
            t = walk(w, 2000)
            A_s.append(diffusion_exponent(t, 1, 10))
            A_l.append(diffusion_exponent(t, 10, 50))
            AN.append(anisotropy(t))
        A_s, A_l, AN = np.array(A_s), np.array(A_l), np.array(AN)
        for lbl, a in (("alpha_short", A_s), ("alpha_long", A_l),
                       ("anisotropy", AN)):
            ci = 1.96 * a.std(ddof=1) / np.sqrt(len(a))
            print(f"  {nm:<34} {lbl:>11}: mean={a.mean():.4f} "
                  f"CI95=[{a.mean()-ci:.4f}, {a.mean()+ci:.4f}]")


def h4_theta_placement():
    print()
    print("=" * 72)
    print("H4 — theta OUTSIDE (GCAL) vs theta INSIDE (BCM)")
    print("  statistic: ||w||/||w0|| at 40k (burn-in >=20k, fixed by §1.2)")
    print("  CONJUNCTIVE gate: an arm counts as STABLE only if it is ALIVE")
    print("                    (meanrate > 0 AND max|dw| > 0). Frozen != stable.")
    print("=" * 72)
    for tm, nm in ((0.0, "theta OUTSIDE (GCAL)"), (1.0, "theta INSIDE (BCM)")):
        rel, rate, dws = [], [], []
        for i in range(N):
            sd = SEED0 + 200 + i
            s, ag = boot_core()
            load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
            w = EyeWorld(s, h=H, w=W, gaze_l=5, seed=sd)
            set_params(w, eye=1.0, eye_open=1.0, logr=1.0, saw=0.0,
                       theta_mode=tm, eta=5e-4, phase0=0.0)
            us = w.add_units(4, rf=5, seed=sd)
            rng = np.random.default_rng(sd)
            w0 = np.array([np.linalg.norm(w.weights(u)) for u in us])
            for _ in range(20_000):
                w.step(frame=(rng.random((H, W)) + 0.1))
            prev = np.concatenate([w.weights(u) for u in us])
            rs = []
            for _ in range(20_000):
                w.step(frame=(rng.random((H, W)) + 0.1))
                rs.append(np.mean([float(w.s.node(u)["attrs"]["rate"]) for u in us]))
            cur = np.concatenate([w.weights(u) for u in us])
            nrm = np.array([np.linalg.norm(w.weights(u)) for u in us])
            # unit of analysis is the SEED: mean over that seed's units
            rel.append(float(np.mean(nrm / w0)))
            rate.append(float(np.mean(rs)))
            dws.append(float(np.max(np.abs(cur - prev))))
            print(f"  {nm:<22} seed {sd}: ||w||/||w0||={rel[-1]:.4f} "
                  f"meanrate={rate[-1]:.6f} max|dw|={dws[-1]:.3e}", flush=True)
        for lbl, a in (("||w||/||w0||", np.array(rel)),
                       ("meanrate", np.array(rate)),
                       ("max|dw|", np.array(dws))):
            a = np.asarray(a)
            ci = 1.96 * a.std(ddof=1) / np.sqrt(len(a))
            print(f"  --- {nm:<22} {lbl:>13}: mean={a.mean():.6f} "
                  f"CI95=[{a.mean()-ci:.6f}, {a.mean()+ci:.6f}]")
        alive = (np.array(rate) > 0).all() and (np.array(dws) > 0).all()
        print(f"  --- {nm:<22} ALIVE (rate>0 AND dw>0 on every seed): {alive}")


def main():
    print(provenance_line())
    print(f"commit {os.popen('git rev-parse HEAD').read().strip()[:12]}")
    print(f"prereg VISION_EYE_PREREG.md @ 26cb7c6be3 (committed BEFORE this run)")
    print(f"seeds  {SEED0}-{SEED0+999} (confirmatory block), n={N}")
    print()
    h1_illumination_invariance()
    h2_weber_fechner()
    h3_engbert_drift()
    h4_theta_placement()


if __name__ == "__main__":
    main()
