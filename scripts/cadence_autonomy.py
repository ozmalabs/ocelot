"""THE LOOP PREDICTS ITS OWN EAR — wire the cadence predictor into the autonomy loop, and test it.

No new cognition: the SAME understand-drive / investigation loop the agent runs on its capabilities, pointed at
the signal. Boot enact + autonomy + investigation_loop + impasse_escalation + onset_prediction (the predict-onset
BEAT and CADENCE axes), register the CadenceWorld executor, point the agent at the onset_prediction microtheory,
and PUMP master_tick();tick(). The loop frontier-picks the predict axes, binds the predictor operators, runs them
(the measurement is PREDICTION SKILL, not recognition), and banks -- the beat axis should STALL (cadence is not a
beat) while the cadence axis SATURATES (the shape predicts). That contrast, produced by the unedited loop, is the
ear becoming a frontier the agent's own cognition reduces.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.cadence_autonomy [refrain.wav] [ticks]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import manifest_for
from domains.cadence_world import CadenceWorld

SEEDS = ["enact", "autonomy", "investigation_loop", "impasse_escalation", "onset_prediction"]


def axis_label(s, ax):
    return str(s.node(ax)["attrs"].get("capability_keys"))


def main():
    refrain = sys.argv[1] if len(sys.argv) > 1 else "/tmp/nursery/baabaa.wav"
    n_ticks = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    print("=" * 92)
    print(f"THE LOOP PREDICTS ITS EAR — onset-prediction axes in the autonomy loop ({os.path.basename(refrain)})")
    print("=" * 92)
    adapter = WorldAdapter()
    for sid in SEEDS:
        adapter.inner.load_seed_manifest(manifest_for(sid), adapter.agent)
    cw = CadenceWorld(adapter.s, refrain)
    mt = next(n for n in adapter.s.nodes("Microtheory")
              if adapter.s.node(n)["attrs"].get("name") == "onset_prediction")
    adapter.s.add_edge(adapter.agent, "operates_in", mt)
    adapter.wire_autonomy_faculty()
    adapter.wire_enact_faculty()
    adapter.wire_investigation_faculty(cw)
    adapter.wire_escalation_faculties()
    axes = [n for n in adapter.s.nodes("CapabilityAxis") if adapter.s.node(n)["attrs"].get("is_axis") == 1.0]
    print(f"  booted: {len(axes)} predict axes, contour {len(cw.contour)} onsets, shuffled-chance err {cw._shuf:.3f}\n")

    seen = set()
    for t in range(1, n_ticks + 1):
        adapter.master_tick()
        adapter.tick()
        for mc in adapter.s.nodes("MeasuredCapability"):
            a = adapter.s.node(mc)["attrs"]
            if mc in seen:
                continue
            seen.add(mc)
            print(f"  [tick {t:2d}] {a.get('metric')}={a.get('measured'):.2f}  {a.get('note')}")

    print("\n" + "=" * 92)
    print("  WHAT THE LOOP LEARNED ABOUT ITS OWN EAR (saturation = how well its model predicts the signal):")
    for ax in axes:
        a = adapter.s.node(ax)["attrs"]
        print(f"    {axis_label(adapter.s, ax):<28} saturation={float(a.get('saturation',0)):.2f}  "
              f"last={a.get('last_measured')}  attempts={int(a.get('mf_stall',0))}")
    def skill(keys):
        for ax in axes:
            if tuple(adapter.s.node(ax)["attrs"].get("capability_keys") or []) == keys:
                lm = adapter.s.node(ax)["attrs"].get("last_measured")
                return float(lm) if lm is not None else 0.0
        return 0.0
    beat_sk = skill(("predict", "onset", "beat"))
    cad_sk = skill(("predict", "onset", "cadence"))
    ran = len(seen)
    print("\n" + "=" * 92)
    if ran and cad_sk > beat_sk * 1.2 and cad_sk > 0:
        print(f"  THE LOOP PREDICTS ITS EAR -- and CADENCE beats BEAT, measured by the loop itself: cadence prediction")
        print(f"  skill {cad_sk:.2f} >> beat skill {beat_sk:.2f} (the SHAPE predicts the signal ~{cad_sk/max(beat_sk,1e-9):.1f}x better than the period).")
        print("  The UNEDITED understand-drive frontier-picked the predict axes, bound the predictor operators, and")
        print("  banked PREDICTION SKILL as the measurement -- no recognition, no new cognition. The ear became a")
        print("  frontier the agent's own loop predicts; cadence-beats-beat is now the loop's own finding, not a probe.")
    elif ran:
        print(f"  the loop ran the predictors (cadence skill {cad_sk:.2f}, beat skill {beat_sk:.2f}) -- it predicted the ear")
        print("  in the loop, but cadence did not clearly beat beat here; check the contour / operator binding.")
    else:
        print("  the loop did NOT run the predict axes (no measurements) -- check the bind join / operates_in wiring.")
    print("=" * 92)


if __name__ == "__main__":
    main()
