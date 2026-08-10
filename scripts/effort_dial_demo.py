#!/usr/bin/env python3
"""Context-aware EFFORT DIAL — verification demo (world adapter only).

The dial itself lives in Rust (runners/dsl/src/effort_dial.rs + the L6
feedback loop). This script is a pure world adapter: it pushes CONTEXT in
(deadline / thread-mode / cpu / memory / surprise) and reads the trace out
(effort / passes / wall-time / deadline-met). No decisions here.

The effort knob (register_knob_u64 in the L6 RecommendationApplier) scales
TWO real processing parameters:
  * the number of order-N analysis / re-watch PASSES, and
  * the salience THRESHOLD (lower effort raises it -> keep/process less).

Run:  python3 scripts/effort_dial_demo.py
"""
import sys, os, statistics
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                "..", "runners", "dsl", "python"))
import substrate_rs as srs


def measure_per_pass_us(dial, sample, reps=5):
    """Empirically measure cost of one analysis pass — fed back to the
    dial so its deadline channel fits passes to the real budget."""
    dial.set_context("offline")
    dial.turn_dial()                     # offline -> deep -> many passes
    # run several times, divide wall by passes.
    costs = []
    for _ in range(reps):
        r = dial.run(sample, surprise=1.0)   # high surprise -> process
        if r["passes"] > 0:
            costs.append(r["wall_us"] / r["passes"])
    return statistics.median(costs) if costs else 100.0


def trace_line(tag, ctx, r):
    met = r["deadline_met"]
    met_s = "n/a" if met is None else ("MET" if met else "OVERRUN")
    return (f"  {tag:<22} ctx={ctx:<34} "
            f"effort={r['effort']:>2} passes={r['passes']:>1} "
            f"thr={r['salience_threshold']:.2e} "
            f"wall={r['wall_us']:8.1f}us  deadline={met_s}")


def main():
    # A salient input: a directed, resolving build->peak (the "tada"
    # shape order_n_shape_salience scores high). And a routine flat-ish
    # input that scores low.
    salient = [0.0, 0.5, 1.2, 2.1, 3.0, 3.6, 3.9, 4.0] * 4000
    routine = [1.0, 1.02, 0.99, 1.01, 1.0, 0.98, 1.01, 1.0] * 4000

    s_salient = srs.EffortDial.surprise_of(salient)
    s_routine = srs.EffortDial.surprise_of(routine)
    print(f"surprise(salient) = {s_salient:.4f}   "
          f"surprise(routine) = {s_routine:.4f}")
    print(f"(salient >> routine -> the surprise channel will spend more "
          f"on the salient input)\n")

    # Calibrate the salience GATE + the surprise saturation point to the
    # real surprise range of this world so the dial's thresholds are
    # meaningful: salient input should clear the gate at deep effort,
    # routine should be borderline. (A world adapter calibrating its own
    # signal range — no agent decision here.)
    hi_thr = s_salient * 0.9          # strict (fast path): only the very salient
    lo_thr = s_salient * 0.3          # lax (deep): keep the moderately salient too
    dial = srs.EffortDial(max_effort=10, min_passes=1, max_passes=8,
                          hi_threshold=hi_thr, lo_threshold=lo_thr,
                          salient_at=max(s_salient, 1e-6))

    # Calibrate per-pass cost on real hardware.
    per = measure_per_pass_us(dial, salient)
    print(f"measured per-pass cost ~ {per:.1f} us "
          f"(used by the deadline channel to fit passes)\n")

    print("=" * 92)
    print("SCENARIO 1 — REAL-TIME, single-thread, TIGHT deadline.")
    print("Same salient input as offline below; dial must turn DOWN to fit.")
    print("=" * 92)
    # Budget = ~3 passes worth -> the dial should pick low effort.
    tight_us = int(per * 3)
    dial.set_context("realtime", deadline_us=tight_us, per_pass_us=int(per),
                     surprise=s_salient)
    votes = dial.channel_votes()
    eff = dial.turn_dial()
    print(f"  channel votes (name->effort): {votes}")
    print(f"  blended effort = {eff} (min of all ceilings + surprise demand)")
    r = dial.run(salient, surprise=s_salient, deadline_us=tight_us)
    print(trace_line("realtime/tight", f"deadline={tight_us}us mode=RT", r))
    rt_passes, rt_wall = r["passes"], r["wall_us"]
    assert r["deadline_met"], "real-time path must MEET its deadline"
    print("  -> MET the deadline by dialing effort DOWN.\n")

    print("=" * 92)
    print("SCENARIO 2 — OFFLINE, no deadline. SAME input -> dial turns UP.")
    print("=" * 92)
    dial.set_context("offline", surprise=s_salient)
    votes = dial.channel_votes()
    eff = dial.turn_dial()
    print(f"  channel votes (name->effort): {votes}")
    print(f"  blended effort = {eff}")
    r = dial.run(salient, surprise=s_salient)
    print(trace_line("offline/deep", "deadline=none mode=OFFLINE", r))
    off_passes, off_wall = r["passes"], r["wall_us"]
    print(f"  -> went DEEPER: {off_passes} passes vs {rt_passes} real-time "
          f"({off_wall:.0f}us vs {rt_wall:.0f}us wall).\n")
    assert off_passes > rt_passes, "offline must go deeper than real-time"

    print("=" * 92)
    print("SCENARIO 3 — SURPRISE within budget. Same OFFLINE context,")
    print("salient vs routine input -> more vs less effort.")
    print("=" * 92)
    dial.set_context("offline", surprise=s_salient)
    eff_sal = dial.turn_dial()
    r_sal = dial.run(salient, surprise=s_salient)
    print(trace_line("offline/salient", f"surprise={s_salient:.3f}", r_sal))
    dial.set_context("offline", surprise=s_routine)
    eff_rou = dial.turn_dial()
    r_rou = dial.run(routine, surprise=s_routine)
    print(trace_line("offline/routine", f"surprise={s_routine:.3f}", r_rou))
    print(f"  -> surprise raised effort {eff_rou}->{eff_sal} "
          f"(routine processed={r_rou['processed']}, "
          f"salient processed={r_sal['processed']}).\n")
    assert eff_sal >= eff_rou, "salient must earn >= effort vs routine"

    print("=" * 92)
    print("SCENARIO 4 — DYNAMIC trace: same salient input, context changes,")
    print("the dial tracks (effort / passes / wall / deadline).")
    print("=" * 92)
    contexts = [
        ("offline-idle",     dict(mode="offline", surprise=s_salient)),
        ("realtime-loose",   dict(mode="realtime", deadline_us=int(per*20),
                                  per_pass_us=int(per), surprise=s_salient)),
        ("realtime-tight",   dict(mode="realtime", deadline_us=int(per*2),
                                  per_pass_us=int(per), surprise=s_salient)),
        ("offline-cpu-busy", dict(mode="offline", surprise=s_salient,
                                  cpu_load=0.9)),
        ("offline-mem-press",dict(mode="offline", surprise=s_salient,
                                  working_set_bytes=int(33_554_432*0.95))),
        ("realtime-routine", dict(mode="realtime", deadline_us=int(per*20),
                                  per_pass_us=int(per), surprise=s_routine)),
    ]
    for tag, kw in contexts:
        dial.set_context(**kw)
        dial.turn_dial()
        dl = kw.get("deadline_us")
        inp = routine if kw.get("surprise", 1.0) < 0.1 else salient
        r = dial.run(inp, surprise=kw.get("surprise", 0.0), deadline_us=dl)
        ctx_desc = ",".join(f"{k}={v}" for k, v in kw.items() if k != "mode")
        print(trace_line(tag, ctx_desc[:34], r))
        if r["deadline_met"] is False:
            print("       (deadline could NOT be met even at min effort — "
                  "dial bottomed out, reported honestly, did not fake it)")

    print("=" * 92)
    print("SCENARIO 5 — HONEST FLOOR: deadline below one min-effort pass.")
    print("=" * 92)
    impossible_us = max(1, int(per * 0.2))   # < cost of a single pass
    dial.set_context("realtime", deadline_us=impossible_us,
                     per_pass_us=int(per), surprise=s_salient)
    eff = dial.turn_dial()
    r = dial.run(salient, surprise=s_salient, deadline_us=impossible_us)
    print(trace_line("realtime/impossible", f"deadline={impossible_us}us", r))
    print(f"  blended effort bottomed to {eff} (min). "
          f"deadline_met={r['deadline_met']} — reported honestly, "
          f"not faked.\n")

    print("All scenario assertions passed.")


if __name__ == "__main__":
    main()
