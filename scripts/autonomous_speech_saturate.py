"""AUTONOMOUS SPEECH — keep authoring until RECOGNITION SATURATES.

The escalation run authored ONE ear faculty and recognition jumped on some words (0->1) but not all. This
keeps the loop pumping: every time recognition still has shortfall, the agent stalls -> climbs the ladder ->
AUTHORS another ear extension (effect-gated cue growth / a designed convolution), re-measures, and the cycle
repeats UNTIL recognition saturates (a sustained high recognition rate) or clearly plateaus (many ticks with
no further authoring and no further gain). The agent decides what to author; this only pumps, tracks the
recognition trajectory, and stops when it saturates.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  SPEECH_TEACHER=stub SPEECH_LOCAL_ONLY=1 PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.autonomous_speech_saturate [maxticks]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.autonomous_speech import boot, understanding, SEP

WIN = 3               # each measurement is now a full-pool recognition RATE; smooth over a few trials
SAT = 0.85           # recognition rate that counts as SATURATED (run to the true ceiling, not the 0.6 bar)
PLATEAU = 110        # ticks with no new authoring AND no gain -> declare plateau


def main():
    maxticks = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    print(SEP)
    print("AUTONOMOUS SPEECH — keep authoring until RECOGNITION SATURATES. The agent decides what to build.")
    print(SEP)
    adapter, sw = boot()
    s = adapter.s

    def recog_axis_sat():
        best = 0.0
        for ax in s.nodes("CapabilityAxis"):
            a = s.node(ax)["attrs"]
            if a.get("is_axis") == 1.0 and (a.get("capability_keys") or [None])[0] == "recognise":
                best = max(best, float(a.get("saturation", 0.0)))
        return best

    seen_mc, authored_seen = set(), set()
    matches = []                                 # abs_recognition_match values, in order
    last_author_tick, best_rate = 0, 0.0
    print(f"  pumping up to {maxticks} ticks (stop on recognition rate >= {SAT})\n", flush=True)
    for t in range(1, maxticks + 1):
        adapter.master_tick(); adapter.tick()
        for mc in s.nodes("MeasuredCapability"):
            a = s.node(mc)["attrs"]; key = (mc, a.get("note"))
            if key in seen_mc:
                continue
            seen_mc.add(key)
            if a.get("metric") == "abs_recognition_match":
                try:
                    matches.append(float(a.get("measured")))
                except (TypeError, ValueError):
                    pass
        for op in s.nodes("Operator"):
            a = s.node(op)["attrs"]
            if a.get("authored_by_escalation") == 1.0 and op not in authored_seen:
                authored_seen.add(op); last_author_tick = t
                rate = sum(matches[-WIN:]) / max(len(matches[-WIN:]), 1)
                print(f"  [tick {t:3d}] AUTHORED #{len(authored_seen)}: {a.get('name')!r}  "
                      f"approach={(a.get('approach') or '')[:54]!r}  recog~{rate*100:.0f}%")
        rate = sum(matches[-WIN:]) / max(len(matches[-WIN:]), 1)
        best_rate = max(best_rate, rate)
        if t % 25 == 0:
            print(f"  [tick {t:3d}] recognition rate ~{rate*100:.0f}% (best {best_rate*100:.0f}%), "
                  f"{len(authored_seen)} authored, {len(matches)} trials", flush=True)
        if len(matches) >= WIN and rate >= SAT:
            print(f"\n  [tick {t:3d}] RECOGNITION SATURATED: rolling rate {rate*100:.0f}% over last {WIN} "
                  f"({len(authored_seen)} faculties authored)")
            break
        if t - last_author_tick > PLATEAU and len(authored_seen) > 0:
            print(f"\n  [tick {t:3d}] PLATEAU: no new authoring for {PLATEAU} ticks; recognition rate {rate*100:.0f}% "
                  f"(best {best_rate*100:.0f}%)")
            break

    final_rate = sum(matches[-WIN:]) / max(len(matches[-WIN:]), 1)
    print("\n" + SEP)
    print(f"WHAT THE AGENT BUILT — {len(authored_seen)} ear faculties self-authored under escalation:")
    for op in s.nodes("Operator"):
        a = s.node(op)["attrs"]
        if a.get("authored_by_escalation") == 1.0:
            print(f"  {a.get('name')!r}  runner={a.get('runner')}  approach={(a.get('approach') or '')[:70]!r}")
    print(f"\n  recognition: rolling rate {final_rate*100:.0f}% (best {best_rate*100:.0f}%), "
          f"recognise-axis saturation {recog_axis_sat():.2f}, {len(matches)} recognition trials.")
    print(f"  {'SATURATED' if final_rate >= SAT else 'plateaued'} after {len(authored_seen)} self-authored faculties.")
    print(SEP)


if __name__ == "__main__":
    main()
