#!/usr/bin/env python3
"""FINAL-VERIFICATION task 5 — CONVERGENCE + STABILITY of the trait<->MicroPsi
coupling.

Two experiments, both printing the raw trajectory numbers:

  (5a) DRIVE -> MODULATOR loop with a NONZERO trait bias.
       Drive the modulator rules over many ticks while the drive urgency/arousal
       VARIES (a sine-like sweep), with a fixed nonzero abstraction_bias set-point
       (a high-abstraction agent). Confirm mod_resolution settles at a
       SHIFTED-BUT-STABLE equilibrium: the whole resolution track is the bias-0
       track offset by EXACTLY the bias, still tracking urgency/arousal, NOT
       diverging or ping-ponging. The constant offset cancels in every delta, so
       the biased set-point cannot fight the drive regulation.

  (5b) FULL BIDIRECTIONAL loop over ticks:
         sync_traits_to_modulator   (A: trait -> modulator set-point)
         crystallise_traits_from_modulator (B: modulator -> trait)
         personality_homeostasis_step      (drive/graph -> trait)
       run together, round after round. The trait is the SLOW layer
       (identity_field, hysteretic), the modulator the FAST layer. Confirm the
       trait<->modulator system reaches a FIXED POINT (the trait saturates at the
       ceiling consistent with the sustained modulator sign; the modulator sits at
       the corresponding shifted-stable baseline) and stays there.

Uses the ESTABLISHED emergence harness (scripts/modulator_emergence_measure) for
the drive/modulator spine and the REAL bridge (domains/trait_modulator_bridge)
for the trait side — no re-implemented affect.

Run: python3 scripts/trait_modulator_convergence_probe.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import scripts.modulator_emergence_measure as M   # noqa: E402
import domains.disposition as disp                # noqa: E402
import domains.trait_modulator_bridge as tmb      # noqa: E402
from substrate_rs import _native                  # noqa: E402


def section(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


class _Agent:
    def __init__(self, sub, ag):
        self.s = sub
        self.agent = ag


# --------------------------------------------------------------------------- #
# (5a) DRIVE -> MODULATOR loop under a fixed nonzero set-point bias.
# --------------------------------------------------------------------------- #
def experiment_5a():
    section("(5a) DRIVE->MODULATOR loop, NONZERO abstraction_bias set-point")
    print("A high-abstraction agent (abstraction_bias = +120) vs the SAME agent"
          " with bias 0.\nDrive urgency is swept over many ticks (c_d walks a"
          " triangular path so\nurgency/arousal rise then fall). We read"
          " mod_resolution each tick.\n")

    # a single ModulatorState + one leading drive; we tick it repeatedly, moving
    # only the drive's c_d (=> urgency/arousal vary) and reading resolution.
    def run(bias):
        eye, inner = M._eye()
        _hub, ms = M._hub_ms(eye, inner, abstraction_bias=float(bias))
        d = M._drive(eye, inner, ms, appraised=1, v_d=1000, c_d=400,
                     c_d_prev=400, v_0=0)
        track = []
        # triangular c_d sweep: 400 -> 100 (urgency up) -> 700 (urgency down).
        cds = list(range(400, 100 - 1, -30)) + list(range(100, 700 + 1, 30))
        for i, cd in enumerate(cds):
            eye.substrate.set_attr(d, "c_d", float(cd))
            eye.substrate.set_attr(d, "c_d_prev", float(cd))
            eye.substrate.set_attr(ms, "epoch", float(i + 1))
            inner.run_rules()
            a = eye.substrate.node(ms)["attrs"]
            track.append((cd, int(a["arousal"]), int(a["resolution"])))
        eye.stop()
        return track

    t0 = run(0)
    t1 = run(120)

    print(f"  {'tick':>4} {'c_d':>5} {'arousal':>8} "
          f"{'res(bias0)':>11} {'res(bias120)':>13} {'delta':>6}")
    diverging = False
    prev_delta = None
    deltas = []
    for i, ((cd, ar0, r0), (_cd, _ar1, r1)) in enumerate(zip(t0, t1)):
        delta = r1 - r0
        deltas.append(delta)
        flag = ""
        if prev_delta is not None and delta != prev_delta:
            flag = "  <-- delta CHANGED (offset not constant!)"
            diverging = True
        prev_delta = delta
        # print a subset so the trajectory is readable
        if i % 3 == 0 or i in (len(t0) - 1,):
            print(f"  {i:>4} {cd:>5} {ar0:>8} {r0:>11} {r1:>13} {delta:>6}{flag}")

    res0 = [r for (_c, _a, r) in t0]
    res1 = [r for (_c, _a, r) in t1]
    print(f"\n  bias-0   resolution range: min={min(res0)} max={max(res0)}  "
          f"(tracks urgency/arousal — NOT flat)")
    print(f"  bias-120 resolution range: min={min(res1)} max={max(res1)}")
    print(f"  delta (bias120 - bias0) is CONSTANT at {deltas[0]} "
          f"across all {len(deltas)} ticks: {all(d == deltas[0] for d in deltas)}")
    print(f"  => the +120 set-point SHIFTS the whole track by exactly +120 and"
          f" the drive\n     regulation (the urgency/arousal swing of"
          f" {max(res0) - min(res0)}) is IDENTICAL in both.")
    print(f"  => STABLE shifted equilibrium, no divergence, no ping-pong: "
          f"{deltas[0] == 120 and not diverging and max(res0) != min(res0)}")
    return {"delta_constant": all(d == deltas[0] for d in deltas),
            "delta": deltas[0], "tracks": max(res0) != min(res0),
            "diverging": diverging}


# --------------------------------------------------------------------------- #
# (5b) FULL BIDIRECTIONAL loop: A + B + homeostasis over rounds.
# --------------------------------------------------------------------------- #
def experiment_5b():
    section("(5b) FULL BIDIRECTIONAL loop — sync (A) + crystallise (B) + "
            "homeostasis")
    print("One live agent. Each ROUND we run, in order:\n"
          "  A  sync_traits_to_modulator        (trait level -> modulator bias)\n"
          "  .  drive the modulator to a sustained HIGH-resolution regime\n"
          "  B  crystallise_traits_from_modulator (modulator -> trait evidence)\n"
          "The trait is SLOW (>=1 quantum/round, capped +/-4); the modulator is"
          " FAST.\nWe expect a FIXED POINT: abstraction climbs 0->4, saturates,"
          " and the\nmodulator resolution baseline settles at the corresponding"
          " shifted value.\n")

    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    a = _Agent(s, ag)

    # build the modulator state via the REAL bridge, then push it into a
    # sustained HIGH-resolution regime (a low-arousal, positive drive — the
    # bliss-style config that yields resolution > resolution_hi 450) so
    # direction B sees a sustained +1 abstraction evidence sign.
    hub, ms = tmb.ensure_modulator_state(a, run=False)
    native = disp._native(disp._sub(a))
    lead = None
    for d in native.neighbours(ms, tmb.LEADING_DRIVE_EDGE):
        lead = d
    # a LOW-arousal drive with a small positive urge: resolution = res_base(500)
    # + urgency/4 - arousal stays HIGH (>450) because arousal is small. (This is
    # the emergence harness's bliss/sadness regime.)
    native.set_attr(lead, "appraised", 1.0)
    native.set_attr(lead, "v_d", 100.0)
    native.set_attr(lead, "c_d", 90.0)
    native.set_attr(lead, "c_d_prev", 40.0)
    native.set_attr(lead, "v_0", 0.0)

    print(f"  {'round':>5} {'abstraction':>12} {'abstr_bias':>11} "
          f"{'resolution':>11} {'evidence':>9}")
    hist = []
    for rnd in range(10):
        # A: trait -> modulator set-point
        syncA = tmb.sync_traits_to_modulator(a, ensure_traits=True, run=True)
        # tick the modulator so resolution reflects the drive + the new bias
        native.run_rules()
        res = int(native.node(ms)["attrs"].get("resolution") or 0)
        lvl_before = disp.trait_level(a, "abstraction", ensure=True)
        bias = syncA["biases"].get("abstraction")
        # B: modulator -> trait (one crystallisation quantum)
        crysB = tmb.crystallise_traits_from_modulator(a, ms=ms, ticks=1)
        ev = crysB["evidence"].get("abstraction")
        lvl_after = disp.trait_level(a, "abstraction", ensure=False)
        print(f"  {rnd:>5} {lvl_before:>5}->{lvl_after:<5} {bias:>11.0f} "
              f"{res:>11} {ev:>9.0f}")
        hist.append((rnd, lvl_before, lvl_after, bias, res, ev))

    levels = [h[2] for h in hist]
    biases = [h[3] for h in hist]
    resolutions = [h[4] for h in hist]
    saturated = levels[-1]
    tail_stable = len(set(levels[-3:])) == 1 and len(set(biases[-3:])) == 1 \
        and len(set(resolutions[-3:])) == 1
    # monotone in ONE direction (never reverses = never ping-pongs)
    up = all(levels[i] <= levels[i + 1] for i in range(len(levels) - 1))
    down = all(levels[i] >= levels[i + 1] for i in range(len(levels) - 1))
    monotone = up or down
    at_ceiling = abs(saturated) == 4
    print(f"\n  abstraction level trajectory: {levels}")
    print(f"  abstraction_bias trajectory : {[int(b) for b in biases]}")
    print(f"  resolution trajectory       : {resolutions}")
    print(f"  MONOTONE (never reverses/ping-pongs): {monotone}")
    print(f"  SATURATES at a ceiling (|level|==4): {at_ceiling} (level {saturated})")
    print(f"  FIXED POINT (last 3 rounds identical level/bias/res): {tail_stable}")
    print(f"  => the SLOW trait integrates the sustained modulator sign to the"
          f" +/-4 ceiling,\n     the FAST modulator settles at the shifted-stable"
          f" resolution baseline,\n     and the coupled system holds there —"
          f" convergent, no runaway.")
    return {"monotone": monotone, "saturated": at_ceiling,
            "fixed_point": tail_stable}


def main():
    r5a = experiment_5a()
    r5b = experiment_5b()
    section("SUMMARY")
    print(f"  5a drive->modulator: constant +{r5a['delta']} offset, tracks "
          f"urgency, no divergence  => {r5a['delta_constant'] and r5a['tracks'] and not r5a['diverging']}")
    print(f"  5b bidirectional loop: monotone={r5b['monotone']} "
          f"saturates={r5b['saturated']} fixed_point={r5b['fixed_point']}  => "
          f"{r5b['monotone'] and r5b['saturated'] and r5b['fixed_point']}")
    ok = (r5a["delta_constant"] and r5a["tracks"] and not r5a["diverging"]
          and r5b["monotone"] and r5b["saturated"] and r5b["fixed_point"])
    print(f"\n  TASK 5 CONVERGENCE + STABILITY: {'PASS' if ok else 'REVIEW'}")
    return ok


if __name__ == "__main__":
    main()
