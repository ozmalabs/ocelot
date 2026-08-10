"""Thin IC world adapter — attaches the IC pipeline on top of the
cochlear pipeline (if not already attached), then runs the
substrate's `run_audio_pipeline`. No DSP."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .cochlear_nucleus import attach_default_pipeline as attach_cochlear_pipeline
from .inferior_colliculus import attach_ic_pipeline


def _rust(sub):
    return sub._inner if hasattr(sub, "_inner") else sub


DEFAULT_MOD_RATES_HZ = [2.0, 4.0, 8.0, 16.0, 32.0, 64.0]


@dataclass
class IcParams:
    envelope_lp_hz: float = 50.0
    mod_q: float = 2.0
    peak_threshold_db: float = 4.0
    peak_refractory_ms: float = 80.0
    syllable_coincidence: float = 0.4
    syllable_window_ms: float = 60.0
    syllable_low_hz: float = 4.0
    syllable_high_hz: float = 8.0


def process_audio(
    sub,
    audio_stream_nid,
    samples: np.ndarray,
    sample_rate: int,
    band_centres_hz: Iterable[float],
    modulation_rates_hz: Iterable[float] = None,
    params: IcParams | None = None,
) -> dict:
    """Wire the cochlear + IC pipelines onto this stream if absent,
    then run. Returns the runtime summary dict."""
    p = params or IcParams()
    has_cochlear = any(True for _ in sub.neighbours(
        audio_stream_nid, "has_pipeline_entry"))
    if not has_cochlear:
        attach_cochlear_pipeline(
            sub, audio_stream_nid,
            band_centres_hz=list(band_centres_hz),
            envelope_cutoff_hz=p.envelope_lp_hz,
            sample_rate=int(sample_rate),
        )
    # Detect whether IC ops are already attached by looking for a
    # syllable_coincidence op feeding off this stream's envelope ops.
    has_ic = False
    for entry in sub.neighbours(audio_stream_nid, "has_pipeline_entry"):
        for env in sub.neighbours(entry, "feeds_into"):
            for downstream in sub.neighbours(env, "feeds_into"):
                a = sub.node(downstream)["attrs"]
                if a.get("kind") == "bandpass":
                    has_ic = True
                    break
            if has_ic:
                break
        if has_ic:
            break
    if not has_ic:
        attach_ic_pipeline(
            sub, audio_stream_nid,
            modulation_rates_hz=list(modulation_rates_hz
                                        or DEFAULT_MOD_RATES_HZ),
            mod_q=p.mod_q,
            peak_threshold_db=p.peak_threshold_db,
            peak_refractory_ms=p.peak_refractory_ms,
            syllable_coincidence=p.syllable_coincidence,
            syllable_window_ms=p.syllable_window_ms,
            syllable_low_hz=p.syllable_low_hz,
            syllable_high_hz=p.syllable_high_hz,
        )
    raw = np.ascontiguousarray(samples, dtype=np.float32).tobytes()
    summary = _rust(sub).run_audio_pipeline(
        audio_stream_nid, raw, int(sample_rate),
    )
    # The old IC adapter returned {channels, modulation_events,
    # syllables} keys; preserve those names.
    return {
        "channels": _count_nodes_of_type_on_stream(sub, audio_stream_nid,
                                                      "ModulationChannel",
                                                      "has_modulation_channel"),
        "modulation_events": _count_nodes_of_type_on_stream(
            sub, audio_stream_nid, "ModulationEvent",
            "has_modulation_event"),
        "syllables": summary["syllables"],
        "_runtime_summary": summary,
    }


def _count_nodes_of_type_on_stream(sub, stream_nid, node_type, edge_type) -> int:
    return sum(1 for _ in sub.neighbours(stream_nid, edge_type))


__all__ = ["IcParams", "DEFAULT_MOD_RATES_HZ", "process_audio"]
