"""Legacy compatibility persistence for Python cortex wrappers.

.. warning::
   This module is quarantined compatibility code.  ``save_session`` and
   ``load_session`` preserve Python scheduler/cortex counters and can therefore
   reconstitute the pre-graph-native cognitive architecture.  New cognition
   must persist through the substrate graph itself, using
   :mod:`domains.graph_snapshot_io` for mechanical disk I/O.

The substrate already serialises its graph state via
`substrate.graph_to_dict()` / `graph_from_dict()`. What it can't
serialise is the Python-side cortex wrappers (SpeechCortex,
IntentCortex, MotorCortex) — those are runtime objects that POINT
at graph nodes.

The trick: the cortex node IDs + their config (period, lexicon
name, etc.) ARE graph data. On resume:

  1. Load the graph dict back into a fresh substrate.
  2. For each `SpeechCortex` / `IntentCortex` / `MotorCortex` node
     in the graph, construct a wrapper bound to that existing
     node. The wrapper's install() is idempotent; it finds and
     uses the existing graph nodes without re-creating them.
  3. Register the wrappers with a fresh CortexScheduler. Hooks
     re-attach.

`save_session(sub, path)` writes the graph + a sidecar manifest
listing which cortices to rehydrate. `load_session(path)` reads
both back and returns (substrate, scheduler, cortices_dict).

This is the substrate's lived experience persisting across runs:
the lexicon, the learned signatures, the taught teachings, the
impasses-and-their-resolutions, the planned utterances —
everything graph-resident persists. The agent resumes mid-life.
"""
from __future__ import annotations

import json
import warnings

from .graph_snapshot_io import load_graph_snapshot, save_graph_snapshot


LEGACY_COMPATIBILITY_ONLY = True


def _warn_legacy() -> None:
    warnings.warn(
        "domains.cortex_persistence rehydrates legacy Python cognitive "
        "wrappers; graph-native systems should use graph_snapshot_io",
        DeprecationWarning,
        stacklevel=3,
    )


def save_session(substrate, path: str,
                    cortex_objs: list | None = None) -> dict:
    """Save the substrate's graph dict to `<path>.graph.json` and
    a session manifest to `<path>.session.json`. The manifest
    records cortex configurations so resume can rebuild the
    Python wrappers."""
    _warn_legacy()
    graph_path = path + ".graph.json"
    graph_info = save_graph_snapshot(substrate, graph_path)
    manifest = {
        "cortices": [],
    }
    for cx in (cortex_objs or []):
        # The cortex's NodeID isn't directly JSON-serialisable
        # across runs (it's an opaque handle in this process), so
        # we record what we need to FIND the same cortex node
        # after load_session rebuilds the graph: its type + lexicon
        # (for SpeechCortex). The graph's own type + name attrs
        # disambiguate on resume.
        cls = type(cx).__name__
        entry: dict = {
            "class": cls,
            "tick_period_ms": int(cx.tick_period_ms),
            "tick_count": int(cx._tick_count),
            "wake_count": int(cx._wake_count),
        }
        if cls == "SpeechCortex":
            entry["lexicon_name"] = cx.lexicon_name
        manifest["cortices"].append(entry)
    session_path = path + ".session.json"
    with open(session_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return {
        "graph_path": graph_path,
        "session_path": session_path,
        "graph_size": graph_info["graph_size"],
        "n_cortices": len(manifest["cortices"]),
    }


def load_session(substrate, path: str,
                    pipe=None) -> dict:
    """Restore the substrate from `<path>.graph.json` and rebuild
    cortex wrappers from `<path>.session.json`. The substrate
    must be freshly constructed. `pipe` is the STTPipeline the
    MotorCortex's synthesise callable will bind to (None means
    the motor cortex resumes WITHOUT a synthesiser — useful for
    inspection sessions). Returns:

        {
          "substrate": ...,         # the loaded substrate
          "scheduler": ...,         # fresh CortexScheduler
          "speech": SpeechCortex,   # rehydrated wrappers
          "intent": IntentCortex,
          "motor":  MotorCortex,
        }
    """
    _warn_legacy()
    graph_path = path + ".graph.json"
    session_path = path + ".session.json"
    load_graph_snapshot(substrate, graph_path)
    with open(session_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    from .cortex_scheduler import CortexScheduler
    from .speech_cortex import SpeechCortex
    from .intent_cortex import IntentCortex
    from .motor_cortex import MotorCortex

    scheduler = CortexScheduler()
    out: dict = {"substrate": substrate, "scheduler": scheduler}

    for entry in manifest["cortices"]:
        cls = entry["class"]
        period = int(entry["tick_period_ms"])
        if cls == "SpeechCortex":
            cx = SpeechCortex(substrate,
                                  lexicon_name=entry.get(
                                      "lexicon_name", "stt"),
                                  tick_period_ms=period).install()
            cx._tick_count = int(entry.get("tick_count", 0))
            cx._wake_count = int(entry.get("wake_count", 0))
            scheduler.register(cx)
            out["speech"] = cx
        elif cls == "IntentCortex":
            cx = IntentCortex(substrate,
                                  tick_period_ms=period).install()
            cx._tick_count = int(entry.get("tick_count", 0))
            cx._wake_count = int(entry.get("wake_count", 0))
            scheduler.register(cx)
            out["intent"] = cx
        elif cls == "MotorCortex":
            synth = None
            re_ingest = None
            if pipe is not None:
                synth = lambda w, _p=pipe, _s=substrate: (
                    _p.speak(_s, w, duration_s=0.4))
                def _re_ingest(audio, _p=pipe, _s=substrate):
                    _p.ingest(_s, audio)
                    _s.tick(50000)
                re_ingest = _re_ingest
            cx = MotorCortex(substrate, synthesise=synth,
                                  re_ingest=re_ingest,
                                  tick_period_ms=period).install()
            cx._tick_count = int(entry.get("tick_count", 0))
            cx._wake_count = int(entry.get("wake_count", 0))
            scheduler.register(cx)
            out["motor"] = cx
    return out


__all__ = [
    "LEGACY_COMPATIBILITY_ONLY",
    "load_session",
    "save_session",
]
