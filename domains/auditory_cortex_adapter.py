"""Thin A1 world adapter — attaches the cochlear + A1 pipelines if
absent, then runs the substrate's `run_audio_pipeline`. No DSP."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .cochlear_nucleus import attach_default_pipeline as attach_cochlear_pipeline
from .auditory_cortex import attach_a1_pipeline


def _rust(sub):
    return sub._inner if hasattr(sub, "_inner") else sub


@dataclass
class AcParams:
    envelope_lp_hz: float = 50.0
    peak_threshold_db: float = 4.0
    peak_refractory_ms: float = 50.0


def process_audio(
    sub,
    audio_stream_nid,
    samples: np.ndarray,
    sample_rate: int,
    band_centres_hz: Iterable[float],
    params: AcParams | None = None,
) -> dict:
    """Wire the cochlear + A1 pipelines onto this stream if absent,
    then run."""
    p = params or AcParams()
    has_cochlear = any(True for _ in sub.neighbours(
        audio_stream_nid, "has_pipeline_entry"))
    if not has_cochlear:
        attach_cochlear_pipeline(
            sub, audio_stream_nid,
            band_centres_hz=list(band_centres_hz),
            envelope_cutoff_hz=p.envelope_lp_hz,
            sample_rate=int(sample_rate),
        )
    # Check whether A1 ops are already attached.
    has_a1 = any(
        sub.node(op)["attrs"].get("kind") == "patch_evaluate"
        for op in sub.nodes("Operation")
    )
    if not has_a1:
        attach_a1_pipeline(
            sub, audio_stream_nid,
            peak_threshold_db=p.peak_threshold_db,
            peak_refractory_ms=p.peak_refractory_ms,
        )
    raw = np.ascontiguousarray(samples, dtype=np.float32).tobytes()
    runtime = _rust(sub).run_audio_pipeline(
        audio_stream_nid, raw, int(sample_rate),
    )
    # Preserve the old summary shape (responses, events).
    n_responses = sum(1 for _ in sub.neighbours(
        audio_stream_nid, "has_a1_response"))
    n_events = sum(1 for _ in sub.neighbours(
        audio_stream_nid, "has_a1_event"))
    return {
        "responses": n_responses,
        "events": n_events,
        "_runtime_summary": runtime,
    }


__all__ = ["AcParams", "process_audio"]
