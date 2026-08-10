"""SPEECH AUTONOMY — the zero-Python-decision vertical slice.

Proves the headline property: SEED ONE GOAL (the understand drive), then the jabberwock
decides EVERYTHING after, graph-natively. The Python loop body is literally
`master_tick(); tick()` — no _runnable_pick, no RUNNERS dispatch, no conditional over
graph state. Each tick the agent:

  _frontier_advance (reflex)   -> picks the top ear/speech CapabilityAxis (the drive's Term)
  mint_goal_from_frontier      -> wants it ;  select_active_goal -> active
  mint_investigation_plan      -> a PlanAct themed on the axis
  bind_investigation_faculty   -> the JOIN binds the act to the axis's faculty (investigates_op)
  _run_investigation_reflex    -> runs that faculty's executor (piper/whisper/ingest) -> measures_axis
  bank_measurement_to_axis     -> updates saturation/shortfall -> the frontier RE-RANKS -> SHIFTS

Assertion: after N ticks, >=1 MeasuredCapability exists from the executor AND the agent
measured >=2 DISTINCT axes (it picked -> ran -> measured -> shifted) with zero Python
decision in the loop body.

Run:
  cd experiments/gamma-substrate
  ulimit -v 12582912
  PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python -m scripts.speech_autonomy_slice
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import manifest_for
from domains.speech_world import SpeechWorld

SEP = "=" * 80
SEEDS = ["enact", "discourse", "autonomy", "speech_capability",
         "investigation_loop", "investigation_teacher"]


def _stub_teacher(question):
    """A deterministic stand-in for the LLM teacher (claude -p) so the test proves the
    GRAPH machinery (stall -> impasse -> consult -> ground) without a network round-trip.
    The real driver uses scripts.claude_teacher.make_ask(). Returns the payload shape the
    drain expects."""
    return {"answer": "Try contrasting the onset transient against the steady-state "
                      "formants; a per-band delta over the first 30 ms is the cue.",
            "learn": []}


def _axis_keys(adapter, ax):
    return adapter.s.node(ax)["attrs"].get("capability_keys")


def _frontier_pick(adapter):
    picks = adapter.inner.neighbours(adapter.agent, "frontier_pick")
    return picks[0] if picks else None


def main():
    n_ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 28
    print(SEP)
    print("SPEECH AUTONOMY SLICE — seed ONE goal (understand drive), then tick. No Python decisions.")
    print(SEP)

    # ---- BOOT: core seeds + the autonomy/enact machinery + the speech capability map.
    adapter = WorldAdapter()
    for sid in SEEDS:
        adapter.inner.load_seed_manifest(manifest_for(sid), adapter.agent)

    # ---- AFFORDANCES (mechanical): register the speech-world nodes the agent reaches.
    sw = SpeechWorld(adapter.s)
    sw.register_affordances()

    # ---- ENTER the speech world (mechanical): the agent operates_in speech_world, so the
    #      faculty JOIN (operator applies_in == agent operates_in) can fire.
    mt = next((n for n in adapter.s.nodes("Microtheory")
               if adapter.s.node(n)["attrs"].get("name") == "speech_world"), None)
    assert mt is not None, "speech_world Microtheory not loaded"
    adapter.s.add_edge(adapter.agent, "operates_in", mt)

    # ---- WIRE the reflexes (the seed runners): frontier materializer, enact, investigation.
    adapter.wire_autonomy_faculty()
    adapter.wire_enact_faculty()
    adapter.wire_investigation_faculty(sw)
    # ---- WIRE the teacher loop (graph-native): the gate reflex + the method-teacher channel.
    adapter.wire_teacher_resolution()
    adapter.set_self_teacher(_stub_teacher)

    axes = [n for n in adapter.s.nodes("CapabilityAxis")
            if adapter.s.node(n)["attrs"].get("is_axis") == 1.0]
    print(f"  booted: {len(axes)} ear/speech axes, "
          f"{len(adapter.s.nodes('Operator'))} faculties, drive='understand'")
    for ax in axes:
        a = adapter.s.node(ax)["attrs"]
        print(f"    axis {a.get('capability_keys')}  shortfall={a.get('shortfall')}")
    print()

    # ---- THE LOOP: master_tick(); tick().  Nothing else. The agent decides everything.
    measured_axes = []        # ordered axes the agent measured (via the executor)
    pick_history = []
    seen_mc = set()
    seen_imp = set()
    for t in range(1, n_ticks + 1):
        adapter.master_tick()         # reflexes: frontier pick, enact, run investigation, teacher
        adapter.tick()                # run_rules: mint goal/plan, bind faculty, bank, shift

        pick = _frontier_pick(adapter)
        pick_keys = _axis_keys(adapter, pick) if pick is not None else None
        pick_history.append(pick)
        # any new MeasuredCapability the executor wrote this tick?
        for mc in adapter.s.nodes("MeasuredCapability"):
            if mc in seen_mc:
                continue
            seen_mc.add(mc)
            mca = adapter.s.node(mc)["attrs"]
            tgt = adapter.inner.neighbours(mc, "measures_axis")
            ax_keys = _axis_keys(adapter, tgt[0]) if tgt else None
            measured_axes.append(tuple(ax_keys) if ax_keys else None)
            print(f"  [tick {t:2d}] MEASURED {mca.get('metric')}={mca.get('measured')} "
                  f"on axis {ax_keys}  note={mca.get('note')!r}")
        # teacher path: any new stall-impasse or teacher-grounded axis this tick?
        for imp in adapter.s.nodes("Impasse"):
            ia = adapter.s.node(imp)["attrs"]
            if ia.get("kind") == "frontier_stall" and imp not in seen_imp:
                seen_imp.add(imp)
                print(f"  [tick {t:2d}] STALL -> Impasse minted on {ia.get('for_frontier')} "
                      f"-> consulting teacher")
        print(f"  [tick {t:2d}] frontier_pick -> {pick_keys}")

    # ---- ASSERTIONS: picked -> ran -> measured -> shifted; stalled -> teacher -> grounded.
    distinct_measured = {m for m in measured_axes if m}
    distinct_picks = {p for p in pick_history if p is not None}
    impasses = [n for n in adapter.s.nodes("Impasse")
                if adapter.s.node(n)["attrs"].get("kind") == "frontier_stall"]
    grounded = [n for n in adapter.s.nodes("Impasse")
                if adapter.s.node(n)["attrs"].get("grounded") == 1]
    teacher_axes = [n for n in adapter.s.nodes("CapabilityAxis")
                    if adapter.s.node(n)["attrs"].get("from_teacher") == 1.0]
    print(f"\n{SEP}")
    print(f"  measurements: {len(measured_axes)}  | distinct axes measured: "
          f"{len(distinct_measured)} -> {[list(m) for m in distinct_measured]}")
    print(f"  distinct frontier picks across run: {len(distinct_picks)}")
    print(f"  stall-impasses minted: {len(impasses)}  | grounded: {len(grounded)}  "
          f"| from_teacher axes created: {len(teacher_axes)}")
    ok_measured = len(measured_axes) >= 1
    ok_shift = len(distinct_measured) >= 2
    ok_stall = len(impasses) >= 1
    ok_ground = len(teacher_axes) >= 1
    allok = ok_measured and ok_shift and ok_stall and ok_ground
    print(f"  ran+measured={ok_measured}  shifted(>=2 axes)={ok_shift}  "
          f"stalled->teacher={ok_stall}  grounded-new-investigation={ok_ground}")
    print(f"  SLICE {'PASS' if allok else 'FAIL'} — the agent self-drove the loop "
          f"(pick/run/measure/shift) AND reached for the teacher on stall, no Python "
          f"decision in the body.")
    print(SEP)
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
