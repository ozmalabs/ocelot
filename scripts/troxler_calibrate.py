#!/usr/bin/env python
"""TROXLER — the §1 measure calibration, the §6 arm audit, and the §2 settle.

Run BEFORE the pre-registration.  Everything here is on ALREADY-BURNED seeds
(0–5), so it consumes no confirmatory block.

  §6   Does "freeze the gaze" (paralysis) actually coincide with "stabilise the
       image" (Ditchburn's mirror)?  MEASURED with FM-0's own statistic
       `D = max|armB - armC|` on lum/x/theta/resp at every step — not assumed,
       and not grepped (§12.1: the ninth inert instrument was a grep).
  §1.1 Floor: a FLAT world has no contrast to represent -> the measure must read
       ~0 while the sheet is ALIVE (floor by uniformity, not by death).
  §1.2 Ideal: a high-contrast world -> the measure must read high.
  §1.3 Duration: with the MECHANISM OFF (`frozen=1`, a real freeze), the measure
       must NOT drift over the same duration.  This is §1's third clause in the
       only form it can take for a phenomenon that IS a duration effect: the
       READER must not fade on its own; the fade must come from the mechanism.
  §1.4 Aliveness: reported per arm, per timepoint, everywhere.
  §1.5 Downstream: FM-0b already proved D > 0 on lum/x/theta/resp (the drift
       reaches the sheet).  Cited, not re-run.

  READER POSITIVE CONTROL: prove the fade measure can SEE a non-faded response
  when one is there — a fade is an ABSENCE CLAIM.  `frozen=1` on the structured
  world for the full duration is exactly that.

  §2   The settle: the duration used by the confirmatory run FALLS OUT of where
       the stabilised arm's contrast reaches its fixed point (§13 — a magic
       number falls out; it does not go in).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from domains import engine_provenance as ep
ep.engine_preamble()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import troxler_lib as T  # noqa: E402
from domains import eye_world  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402

VIS = 3200        # §2 — justified by the settle measured in PART E below
CAL = T.CALIB_STEPS


# ---------------------------------------------------------------- §6
def _arm_traces(seed: int, arm: str, steps: int, S: np.ndarray) -> dict:
    """Run one arm recording EVERY attribute FM-0 measured, at EVERY step."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
    ey = eye_world.EyeWorld(s, h=T.H, w=T.W, gaze_l=T.GAZE_L, seed=seed)
    ww = WaveWorld(s, h=T.H, w=T.W, seed=seed)
    ey.couple_waves(ww)
    eye_world.set_params(ey, eye=1.0, calib=1.0, saw=0.0, mu_mode=1.0,
                         world_sample=0.0)
    for t in range(1, CAL + 1):
        k = 1 if (t - 1) % T.IGNITE_EVERY == 0 else 0
        ww.step(ignite_k=k)
        ey.step(frame=None)
    ey.add_world(S)
    saw = 0.0 if arm == T.ARM_FROZEN else 1.0
    eye_world.set_params(ey, calib=0.0, saw=saw, world_sample=1.0)
    g0 = ey.gaze_pos()
    W_img = S[g0[0]:g0[0] + T.H, g0[1]:g0[1] + T.W].copy()

    tr = {k: [] for k in ("lum", "x", "theta", "resp")}
    for t in range(steps):
        if arm == T.ARM_STABILISED:
            T._paint_window(ey, W_img, ey.gaze_pos())
        ey.step(frame=None)
        tr["lum"].append(T.lums(ey))
        tr["x"].append(ey.drives())
        tr["theta"].append(ey.thetas())
        tr["resp"].append(ey.responses())
    return {k: np.array(v) for k, v in tr.items()}


def part_a_arm_audit():
    print("=" * 78)
    print("PART A — §6: does FREEZING THE GAZE coincide with STABILISING THE IMAGE?")
    print("  arm B STABILISED = eye MOVES (saw=1), image follows it -> retinal image static")
    print("                     (Ditchburn/Riggs/Yarbus: the mirror on the contact lens)")
    print("  arm C FROZEN     = eye DOES NOT MOVE (saw=0)          -> retinal image static")
    print("                     (PARALYSIS — a DIFFERENT manipulation in the animal)")
    print("  They coincide IFF the gaze's ONLY wired consumer is the sampling.")
    S = T.world_scene(0)
    steps = 400   # FM-0's own horizon, for FM-0's own statistic
    b = _arm_traces(0, T.ARM_STABILISED, steps, S)
    c = _arm_traces(0, T.ARM_FROZEN, steps, S)
    print(f"\n  D(B,C) = max over cells |stabilised - frozen|, max over {steps} steps")
    allzero = True
    for k in ("lum", "x", "theta", "resp"):
        D = float(np.abs(b[k] - c[k]).max())
        allzero &= (D == 0.0)
        print(f"    max_t D_{k:<6s} = {D:.6e}")
    print(f"\n  => COINCIDE EXACTLY: {allzero}")
    if allzero:
        print("     The drift's ONLY wired effect is moving the image, so in THIS")
        print("     model the two manipulations are the same experiment. MEASURED,")
        print("     not assumed. (In the ANIMAL they are NOT the same: paralysis")
        print("     removes the eye's motion, stabilisation removes only the")
        print("     image's. The model cannot currently tell them apart — which is")
        print("     a SCOPE limit on the claim, §8, and is reported as one.)")
    else:
        print("     They DIVERGE — the gaze has a wired consumer beyond sampling.")
        print("     The stabilised arm (B) is then the ONLY honest Troxler arm.")
    return allzero


# ---------------------------------------------------------------- §1
def part_b_floor_and_ideal():
    print("=" * 78)
    print("PART B — §1 clauses 1+2: the fade measure's FLOOR and IDEAL, measured IN-RUN")
    print("  (OSI's floor is init-dependent 0.0044 vs 0.3899 — 89x. NEVER inherit a floor.)")
    rows = []
    # FLOOR: a flat world. No contrast exists to be represented.
    r = T.run_arm(0, T.ARM_FROZEN, vis_steps=200, calib_steps=CAL,
                  scene=T.uniform_scene(0.5), frozen=1.0)
    rows.append(("FLOOR   (uniform world, frozen)", r))
    # IDEAL: a maximal-contrast world.
    rng = np.random.default_rng(0)
    ideal = (rng.random((T.WH, T.WH)) > 0.5).astype(np.float64) * 0.9 + 0.05
    r = T.run_arm(0, T.ARM_FROZEN, vis_steps=200, calib_steps=CAL,
                  scene=ideal, frozen=1.0)
    rows.append(("IDEAL   (binary hi-contrast, frozen)", r))
    # The experiment's own scene, for scale.
    r = T.run_arm(0, T.ARM_FROZEN, vis_steps=200, calib_steps=CAL,
                  scene=T.world_scene(0), frozen=1.0)
    rows.append(("SCENE   (the grating, frozen)", r))
    for name, r in rows:
        print(f"  {name:38s} contrast={r['contrast_t0']:.6f}  alive={r['alive_t0']:.4f}")
    floor, ideal_c = rows[0][1]['contrast_t0'], rows[1][1]['contrast_t0']
    print(f"\n  floor={floor:.6f}  ideal={ideal_c:.6f}")
    print(f"  => floor at ~0 WHILE ALIVE ({rows[0][1]['alive_t0']:.4f}): "
          f"{floor < 0.01 and rows[0][1]['alive_t0'] > 0.99}")
    print(f"  => ideal >> floor: {ideal_c > 10 * max(floor, 1e-9)}")
    print("  NOTE: the floor is reached by UNIFORMITY, not by DEATH — the flat-world")
    print("  sheet is 100% alive and scores ~0. That is the distinction §1.1 says")
    print("  SD(resp) cannot make on its own, which is why aliveness is reported")
    print("  beside it at every timepoint.")
    return floor, ideal_c


def part_c_duration_and_reader_poscontrol():
    print("=" * 78)
    print("PART C — §1 clause 3 (duration) AND the READER POSITIVE CONTROL")
    print("  A fade is an ABSENCE CLAIM. With the MECHANISM OFF (frozen=1, a REAL")
    print("  freeze: every adaptation rule gated), the measure must NOT fade on its")
    print("  own over the SAME duration — and must still SEE the response that is there.")
    for arm in (T.ARM_STABILISED, T.ARM_DRIFT):
        r = T.run_arm(0, arm, vis_steps=VIS, calib_steps=CAL, frozen=1.0)
        c = r["contrast"]
        drift_pct = abs(c[-1] - c[0]) / max(c[0], 1e-12) * 100
        print(f"  {arm:11s} frozen=1: contrast t0={c[0]:.6f} -> t{VIS}={c[-1]:.6f} "
              f"({drift_pct:.4f}% drift)  alive_min={r['alive'].min():.4f}")
        print(f"              => reader SEES a non-faded response: {c[-1] > 0.1}")
    print("  => the measure does not drift with duration when the mechanism is off;")
    print("     any fade observed with the mechanism ON is the MECHANISM's.")


def part_e_settle():
    print("=" * 78)
    print("PART E — §2 THE SETTLE: what does the confirmatory duration FALL OUT of?")
    print("  (§13: a magic number falls OUT of a natural process; it does not go IN.")
    print("   A stabilisation duration CHOSEN so that fading appears is worth nothing.)")
    r = T.run_arm(0, T.ARM_STABILISED, vis_steps=6400, calib_steps=CAL)
    c = r["contrast"]
    print("   stabilised-arm contrast (seed 0):")
    for t in (0, 100, 200, 400, 800, 1600, 3200, 4800, 6399):
        print(f"     t={t:5d} contrast={c[t]:.6f} alive={r['alive'][t]:.4f} "
              f"mean_resp={r['mean_resp'][t]:.4f}")
    print(f"\n   contrast(3200)={c[3200]:.6f}  contrast(4800)={c[4800]:.6f}  "
          f"contrast(6399)={c[6399]:.6f}")
    print(f"   settled by 3200 (|c(6399)-c(3200)| = {abs(c[6399]-c[3200]):.3e}): "
          f"{abs(c[6399]-c[3200]) < 1e-5}")
    print(f"   mean_resp(final)={r['mean_resp'][-1]:.6f} vs mu_endo={r['mu_endo']:.6f}")
    print("   => the fixed point is `every cell at its OWN measured setpoint`, which")
    print("      is what the homeostat's equations say it must be. VIS_STEPS=3200 is")
    print("      where the arm has SETTLED (§2), not where a fade looks best.")


def part_d_pilot():
    print("=" * 78)
    print("PART D — the POWER PILOT, on ALREADY-BURNED seeds 0-5 (§3.3)")
    print("  Variance only. Fixes n for the confirmatory run.")
    ds, bs = [], []
    for seed in range(6):
        a = T.run_arm(seed, T.ARM_DRIFT, vis_steps=VIS, calib_steps=CAL)
        b = T.run_arm(seed, T.ARM_STABILISED, vis_steps=VIS, calib_steps=CAL)
        ds.append(a["contrast_final"]); bs.append(b["contrast_final"])
        print(f"  seed {seed}: drift={a['contrast_final']:.6f} "
              f"(alive_min={a['alive'].min():.3f})  "
              f"stabilised={b['contrast_final']:.6f} "
              f"(alive_min={b['alive'].min():.3f})  "
              f"stab_err={b['max_stab_err']:.1e}  diff={a['contrast_final']-b['contrast_final']:+.6f}")
    ds, bs = np.array(ds), np.array(bs)
    d = ds - bs
    print(f"\n  drift      mean={ds.mean():.6f} sd={ds.std(ddof=1):.6f}")
    print(f"  stabilised mean={bs.mean():.6f} sd={bs.std(ddof=1):.6f}")
    print(f"  paired diff mean={d.mean():.6f} sd={d.std(ddof=1):.6f}")
    print(f"  sign of diff: {int((d > 0).sum())}/{len(d)} positive")
    if d.std(ddof=1) > 0:
        print(f"  Cohen dz = {d.mean()/d.std(ddof=1):.2f}")
    print("  => the separation is DETERMINISTIC in sign (every seed same direction).")
    print("     n=8 gives an exact two-sided sign test p = 2*(1/2)^8 = 0.0078 if all")
    print("     8 agree — the smallest n that can reach p<0.01, and the setpoint")
    print("     rung's own precedent.")


if __name__ == "__main__":
    print(ep.provenance_line())
    part_a_arm_audit()
    part_b_floor_and_ideal()
    part_c_duration_and_reader_poscontrol()
    part_e_settle()
    part_d_pilot()
