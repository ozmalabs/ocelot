"""MULTILINGUAL HUMAN-EQUIVALENT SPEECH UNDERSTANDING — the target.

Seed ONE goal (the understand drive) over FOUR languages (en/fr/de/es). The agent hears piper
speech in each language through its OWN ear, recognises it, and is scored by AGREEMENT with
multilingual whisper (the human-equivalent reference; target 0.9). The understand-drive ranks
the four languages; the agent works the one it is furthest below human on, learning (banking
heard exemplars under the human label) and — when it stalls — escalating and authoring its ear.

The frontier reported is the per-language gap to human. Whisper is the measurable proxy; the
conceptual target is human-level understanding (whisper itself errs, so closing to it is the
floor, not the ceiling).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.multilingual_understanding [ticks]
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
from scripts.autonomous_speech import _teacher

SEP = "=" * 84
SEEDS = ["enact", "discourse", "autonomy", "speech_capability", "investigation_loop",
         "investigation_teacher", "impasse_escalation", "multilingual_understanding"]
LANGS = ["en", "fr", "de", "es"]


def boot():
    adapter = WorldAdapter()
    for sid in SEEDS:
        adapter.inner.load_seed_manifest(manifest_for(sid), adapter.agent)
    sw = SpeechWorld(adapter.s, source_world=SourceWorld(include_jellyfin=False))
    sw.register_affordances()
    mt = next((n for n in adapter.s.nodes("Microtheory")
               if adapter.s.node(n)["attrs"].get("name") == "speech_world"), None)
    adapter.s.add_edge(adapter.agent, "operates_in", mt)
    # wire the understand operators into the world (applies_in the speech_world Microtheory).
    for op in adapter.s.nodes("Operator"):
        if adapter.s.node(op)["attrs"].get("runner") == "understand":
            try:
                adapter.inner.add_edge_unchecked(op, "applies_in", mt)
            except Exception:
                pass
    # PARK the toy axes (recognise/segment) so the frontier is the four LANGUAGES.
    for ax in adapter.s.nodes("CapabilityAxis"):
        a = adapter.s.node(ax)["attrs"]
        if a.get("is_axis") == 1.0 and not a.get("lang"):
            adapter.inner.set_attr(ax, "is_axis", 0.0)
    adapter.wire_autonomy_faculty(); adapter.wire_enact_faculty()
    adapter.wire_investigation_faculty(sw)
    adapter.wire_teacher_resolution(); adapter.wire_escalation_faculties()
    adapter.set_self_teacher(_teacher())
    return adapter, sw


def lang_axes(adapter):
    out = {}
    for ax in adapter.s.nodes("CapabilityAxis"):
        a = adapter.s.node(ax)["attrs"]
        if a.get("lang") in LANGS and a.get("from_teacher") != 1.0 and a.get("is_axis") == 1.0:
            out.setdefault(a["lang"], ax)
    return out


def main():
    n_ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    print(SEP)
    print("MULTILINGUAL HUMAN-EQUIVALENT SPEECH UNDERSTANDING — seed one goal, the agent drives.")
    print(SEP)
    adapter, sw = boot()
    print(f"  target: human-equivalent (whisper-agreement >= 0.90) across {LANGS}; teacher="
          f"{os.environ.get('SPEECH_TEACHER','real')}\n")

    seen = set()
    for t in range(1, n_ticks + 1):
        adapter.master_tick(); adapter.tick()
        for mc in adapter.s.nodes("MeasuredCapability"):
            a = adapter.s.node(mc)["attrs"]
            if a.get("metric") != "understanding":
                continue
            key = (mc, a.get("note"))
            if key in seen:
                continue
            seen.add(key)
            print(f"  [tick {t:3d}] understanding {a.get('note')}")

    print("\n" + SEP)
    print("WHAT THE JABBERWOCK UNDERSTANDS — per language (held-out recognition vs human):")
    # read the understanding measurements directly (the recognition rate), not the axis
    # saturation (which the escalation re-binding perturbs).
    rate = {}
    for mc in adapter.s.nodes("MeasuredCapability"):
        a = adapter.s.node(mc)["attrs"]
        if a.get("metric") != "understanding":
            continue
        lang = next((k for k in (a.get("capability_keys") or []) if k in LANGS), None)
        if lang:
            rate[lang] = float(a.get("measured", 0.0))
    behind = []
    for lang in LANGS:
        r = rate.get(lang)
        if r is None:
            print(f"  {lang}: (not investigated)"); continue
        print(f"  {lang}: held-out recognition = {r*100:.0f}%  ({'human-equivalent' if r >= 0.9 else 'below human'})")
        if r < 0.9:
            behind.append(lang)
    print(f"\n  FRONTIER — below human-equivalent in: {behind or 'none'} "
          f"(reached via shared-lexicon compounding: continuous learning -> recognition lifts in-loop).")
    print(SEP)


if __name__ == "__main__":
    main()
