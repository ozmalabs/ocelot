"""AUTONOMOUS SPEECH — the agent develops its own ear+speech engine. A PUMP, nothing more.

Seed ONE goal (the understand drive, in seeds/autonomy.json) and let the jabberwock decide
EVERYTHING after. The loop body is `master_tick(); tick()` — no Python decision, no
_runnable_pick, no RUNNERS dispatch. Each tick, graph-natively, the agent:

  frontier pick (drive Term) -> mint plan -> bind faculty (the JOIN) -> run it (reflex,
  against piper / whisper / the children's-video + jellyfin corpus) -> measure -> bank ->
  the frontier re-ranks and SHIFTS; on a stall the agent formulates an Impasse from its own
  frontier and consults the LLM teacher on METHOD (claude -p, off-thread), grounding the
  advice as a NEW investigation to TEST.

This file is a world adapter: boot the seeds, register the affordances, enter the world,
wire the seed runners, set the teacher channel, then pump. It makes no decisions.

Run (project .venv python — piper + faster_whisper live there):
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python -m scripts.autonomous_speech [ticks]

  SPEECH_TEACHER=stub  -> use a canned teacher (no claude -p) for a fast offline run.
  SPEECH_LOCAL_ONLY=1  -> corpus = local children's videos only (skip jellyfin).
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
from scripts.source_world import SourceWorld

SEP = "=" * 84
SEEDS = ["enact", "discourse", "autonomy", "speech_capability",
         "investigation_loop", "investigation_teacher", "impasse_escalation",
         "ear_control"]   # the agent owns its ear: detect under-sampling + raise its own rate (ask_jabberwock_ear)


def _teacher():
    """The METHOD teacher channel. Real (claude -p) by default; a canned stand-in when
    SPEECH_TEACHER=stub (fast offline runs). The agent decides WHEN/WHAT to ask; this is
    only the channel."""
    if os.environ.get("SPEECH_TEACHER", "real").lower() == "stub":
        return lambda q: ("Contrast the onset transient against the steady-state formants; "
                          "a per-band delta over the first 30 ms is the distinguishing cue.")
    from scripts.claude_teacher import make_ask
    return make_ask()


def boot(exclude=()):
    """Boot an ear+speech-capable, autonomy-capable agent on the seed set, register the
    speech-world affordances, enter the world, and wire the seed runners + teacher. All
    mechanical adapter/seed work — no decisions. `exclude` drops named seeds (e.g. the
    authoring demo boots without 'impasse_escalation' to author it fresh)."""
    adapter = WorldAdapter()
    for sid in SEEDS:
        if sid in exclude:
            continue
        adapter.inner.load_seed_manifest(manifest_for(sid), adapter.agent)
    local_only = os.environ.get("SPEECH_LOCAL_ONLY", "") == "1"
    sw = SpeechWorld(adapter.s, source_world=SourceWorld(include_jellyfin=not local_only))
    sw.register_affordances()
    mt = next((n for n in adapter.s.nodes("Microtheory")
               if adapter.s.node(n)["attrs"].get("name") == "speech_world"), None)
    adapter.s.add_edge(adapter.agent, "operates_in", mt)
    adapter.wire_autonomy_faculty()
    adapter.wire_enact_faculty()
    adapter.wire_investigation_faculty(sw)
    adapter.wire_teacher_resolution()
    adapter.wire_escalation_faculties()   # order-4 author + order-6 rethink (the impasse_escalation seed's reflexes)
    adapter.set_self_teacher(_teacher())
    return adapter, sw


def understanding(adapter):
    """Read back what the agent UNDERSTANDS about its ear+speech engine (not a score):
    each capability axis it has, how saturated its model of it is, its last measurement,
    how hard it found it (mf_stall), and which axes it grew from teacher advice."""
    out = []
    for ax in adapter.s.nodes("CapabilityAxis"):
        a = adapter.s.node(ax)["attrs"]
        if a.get("is_axis") != 1.0:
            continue
        out.append({"keys": a.get("capability_keys"),
                    "saturation": round(float(a.get("saturation", 0.0)), 2),
                    "last_measured": a.get("last_measured"),
                    "mf_stall": int(a.get("mf_stall", 0)),
                    "from_teacher": a.get("from_teacher") == 1.0})
    return out


def main():
    n_ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    print(SEP)
    print("AUTONOMOUS SPEECH — seed ONE goal (understand drive), then pump. The jabberwock "
          "decides everything.")
    print(SEP)
    adapter, sw = boot()
    print(f"  booted: {len([n for n in adapter.s.nodes('CapabilityAxis') if adapter.s.node(n)['attrs'].get('is_axis')==1.0])} "
          f"ear/speech axes, {len(adapter.s.nodes('Operator'))} faculties, teacher="
          f"{os.environ.get('SPEECH_TEACHER','real')}\n")

    seen_mc, consults = set(), 0
    for t in range(1, n_ticks + 1):
        adapter.master_tick()
        adapter.tick()
        for mc in adapter.s.nodes("MeasuredCapability"):
            a = adapter.s.node(mc)["attrs"]
            key = (mc, a.get("note"))
            if key in seen_mc:
                continue
            seen_mc.add(key)
            print(f"  [tick {t:2d}] {a.get('metric')}={a.get('measured')}  {a.get('note')!r}")
        c = len([n for n in adapter.s.nodes("Impasse")
                 if adapter.s.node(n)["attrs"].get("kind") == "frontier_stall"])
        if c > consults:
            consults = c
            print(f"  [tick {t:2d}] stalled -> consulted the method-teacher ({consults} total)")

    # SETTLE: keep pumping until in-flight (real, off-thread) teacher calls drain and their
    # advice grounds into new investigations. Bounded — the loop, not a blocking wait.
    for _ in range(40):
        if not getattr(adapter, "_teacher_threads", []):
            break
        adapter.master_tick()
        adapter.tick()

    print("\n" + SEP)
    print("WHAT THE AGENT UNDERSTANDS (its self-built ear+speech model + frontier):")
    for u in understanding(adapter):
        tag = " [grew from teacher advice]" if u["from_teacher"] else ""
        print(f"  {str(u['keys']):<42} saturation={u['saturation']}  "
              f"last={u['last_measured']}  attempts={u['mf_stall']}{tag}")
    teacher_axes = sum(1 for u in understanding(adapter) if u["from_teacher"])
    print(f"\n  {len(seen_mc)} measurements, {consults} teacher consults, "
          f"{teacher_axes} teacher-grown frontiers — all self-selected, dispatched, "
          f"measured, banked. The next hill is whichever axis still has shortfall.")
    print(SEP)


if __name__ == "__main__":
    main()
