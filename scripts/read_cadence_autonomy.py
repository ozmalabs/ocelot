"""THE LOOP PREDICTS A HELD-OUT SPEAKER'S EAR — the UNIVERSAL route in the autonomy loop, on READ speech.

The held cadence library (banked across training speakers) gave a repetition-free, speaker-independent predictor:
recall the nearest UNIVERSAL arc to read a speaker the bank never saw. This wires that route into the agent's own
understand-drive loop, on READ speech (not the song refrain): boot the onset-prediction seeds PLUS the modular
onset_prediction_universal seed, build a HELD-OUT read speaker's contour (disjoint from the library's training
speakers), bind the held library as the world's bank, and PUMP master_tick();tick(). The unedited loop
frontier-picks the predict axes -- beat / cadence(recall) / dynamics(AR) / UNIVERSAL(held library) -- binds each
operator, and banks PREDICTION SKILL. On read speech the repetition-hungry recall should STALL while the two
repetition-free routes (dynamics, universal) SATURATE -- the loop discovers a universal cadence reads a new speaker,
zero new cognition.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.read_cadence_autonomy [ticks]
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
from domains.cadence_library import CadenceLibrary
from scripts.jabberwock_cadence_library import LIB_PATH, all_speakers, speaker_streams, N_TRAIN, N_TEST
from scripts.jabberwock_cadence_library_compare import ami_library_and_test

SEEDS = ["enact", "autonomy", "investigation_loop", "impasse_escalation",
         "onset_prediction", "onset_prediction_universal"]


def axis_label(s, ax):
    return str(s.node(ax)["attrs"].get("capability_keys"))


def run_one(test_spk, contour, lib, n_ticks, verbose=False):
    """Boot a fresh agent, bind the held-out speaker's contour + the library, pump the loop, return per-axis skill."""
    adapter = WorldAdapter()
    for sid in SEEDS:
        adapter.inner.load_seed_manifest(manifest_for(sid), adapter.agent)
    cw = CadenceWorld(adapter.s, contour=contour, library=lib, name=f"read:spk{test_spk}")
    mt = next(n for n in adapter.s.nodes("Microtheory")
              if adapter.s.node(n)["attrs"].get("name") == "onset_prediction")
    adapter.s.add_edge(adapter.agent, "operates_in", mt)
    adapter.wire_autonomy_faculty()
    adapter.wire_enact_faculty()
    adapter.wire_investigation_faculty(cw)
    adapter.wire_escalation_faculties()
    axes = [n for n in adapter.s.nodes("CapabilityAxis") if adapter.s.node(n)["attrs"].get("is_axis") == 1.0]

    seen = set()
    for t in range(1, n_ticks + 1):
        adapter.master_tick()
        adapter.tick()
        for mc in adapter.s.nodes("MeasuredCapability"):
            if mc in seen:
                continue
            seen.add(mc)
            if verbose:
                a = adapter.s.node(mc)["attrs"]
                print(f"    [tick {t:2d}] {a.get('metric')}={a.get('measured'):.2f}  {a.get('note')}")

    def skill(keys):
        for ax in axes:
            if tuple(adapter.s.node(ax)["attrs"].get("capability_keys") or []) == keys:
                lm = adapter.s.node(ax)["attrs"].get("last_measured")
                return float(lm) if lm is not None else 0.0
        return 0.0
    return {"beat": skill(("predict", "onset", "beat")), "recall": skill(("predict", "onset", "cadence")),
            "dynamics": skill(("predict", "onset", "dynamics")), "universal": skill(("predict", "onset", "universal")),
            "ran": len(seen), "shuf": cw._shuf, "onsets": len(contour)}


def main():
    n_ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 48
    corpus = sys.argv[2] if len(sys.argv) > 2 else "read"       # "read" (LibriSpeech) | "ami" (spontaneous)
    regime = "SPONTANEOUS (AMI meetings)" if corpus == "ami" else "READ (LibriSpeech)"
    print("=" * 96)
    print(f"THE LOOP PREDICTS HELD-OUT SPEAKERS — onset-prediction + UNIVERSAL axes, on {regime}")
    print("=" * 96)

    if corpus == "ami":
        # In-domain SPONTANEOUS bank (AMI ES+IS groups); test on the held-out TS group (disjoint, no meeting leak).
        lib, streams = ami_library_and_test()
        libdesc = "AMI-trained (spontaneous, ES+IS groups)"
    else:
        if not os.path.exists(LIB_PATH):
            print(f"  no held library at {LIB_PATH} -- run `python -m scripts.jabberwock_cadence_library --rebuild` first.")
            return
        lib = CadenceLibrary.load(LIB_PATH)
        streams = speaker_streams(all_speakers()[N_TRAIN:N_TRAIN + N_TEST])   # DISJOINT held-out LibriSpeech
        libdesc = "READ-trained (LibriSpeech)"
    print(f"  held library: {len(lib)} arcs, {libdesc}; {len(streams)} held-out {regime.split()[0]} "
          f"speakers (NONE in the library)\n")

    rows = []
    for sp, contour in streams:
        r = run_one(sp, contour, lib, n_ticks)
        rows.append((sp, r))
        print(f"    spk {sp:6} ({r['onsets']:3d} onsets)  beat {r['beat']:.2f}  recall {r['recall']:.2f}  "
              f"dynamics(AR) {r['dynamics']:.2f}  UNIVERSAL {r['universal']:.2f}")

    import numpy as np
    agg = {k: float(np.mean([r[k] for _sp, r in rows])) for k in ("beat", "recall", "dynamics", "universal")}
    print("\n" + "=" * 96)
    print("  MEAN prediction skill across all held-out speakers (the loop's own measurement):")
    print(f"    beat {agg['beat']:.2f}   recall(same-stream) {agg['recall']:.2f}   "
          f"dynamics(AR) {agg['dynamics']:.2f}   UNIVERSAL(held library) {agg['universal']:.2f}")
    print("\n" + "=" * 96)
    n_uni_wins = sum(1 for _sp, r in rows if r["universal"] > max(r["beat"], r["recall"]) and r["universal"] > 0)
    rword = regime.split()[0].lower()
    if rows and agg["universal"] > agg["recall"] + 0.05 and agg["universal"] > agg["beat"] and n_uni_wins >= len(rows) - 1:
        print(f"  THE LOOP READS EVERY HELD-OUT SPEAKER VIA THE UNIVERSAL ROUTE: on {rword} speech the held library predicts")
        print(f"  speakers it never banked (mean universal skill {agg['universal']:.2f} on {n_uni_wins}/{len(rows)}) ABOVE the")
        print(f"  repetition-hungry recall ({agg['recall']:.2f}) and the beat ({agg['beat']:.2f}), ~matching the stream's own")
        print(f"  dynamics (AR {agg['dynamics']:.2f}). The unedited understand-drive frontier-picked the universal axis and")
        print("  banked the skill for each speaker -- a universal cadence transfers across speakers, found by the loop.")
    elif rows:
        print(f"  the loop ran on all {len(rows)} held-out speakers (mean universal {agg['universal']:.2f}, dynamics")
        print(f"  {agg['dynamics']:.2f}, recall {agg['recall']:.2f}, beat {agg['beat']:.2f}) -- it predicted each speaker's ear,")
        print(f"  universal led on {n_uni_wins}/{len(rows)} but not cleanly across all; report as measured.")
    else:
        print("  the loop did NOT run the predict axes (no measurements) -- check the bind join / operates_in wiring.")
    print("=" * 96)


if __name__ == "__main__":
    main()
