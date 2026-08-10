"""Thin world adapter for the cochlear-nucleus pipeline.

No DSP, no decisions — translates between external numpy buffers
and the substrate's PyBytes convention, attaches a default
pipeline to a stream if absent, and hands the rest to the Rust
runtime.

The pipeline itself is graph data (see
``domains/cochlear_nucleus.py``); this adapter just runs it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .cochlear_nucleus import attach_default_pipeline


def _rust(sub):
    return sub._inner if hasattr(sub, "_inner") else sub


@dataclass
class CnParams:
    """Tunable cochlear-nucleus knobs. Used only by the convenience
    ``process_audio`` helper to build the default pipeline; the
    pipeline itself is graph-resident, so the agent edits the
    Operation node attrs directly when it wants to tune."""
    envelope_lp_hz: float = 50.0
    onset_threshold_db: float = 6.0
    onset_refractory_ms: float = 30.0
    broadband_coincidence: float = 0.4
    broadband_window_ms: float = 25.0


def process_audio(
    sub,
    audio_stream_nid,
    samples: np.ndarray,
    sample_rate: int,
    band_centres_hz: Iterable[float],
    params: CnParams | None = None,
) -> dict:
    """Wire the default pipeline onto ``audio_stream_nid`` if no
    pipeline ops are attached yet, then run it. Returns the Rust
    summary dict."""
    p = params or CnParams()
    # Check if a pipeline is already attached. If not, wire the
    # default one. Either way the run is the same.
    has_pipeline = any(True for _ in sub.neighbours(
        audio_stream_nid, "has_pipeline_entry"))
    if not has_pipeline:
        attach_default_pipeline(
            sub, audio_stream_nid,
            band_centres_hz=list(band_centres_hz),
            envelope_cutoff_hz=p.envelope_lp_hz,
            onset_threshold_db=p.onset_threshold_db,
            onset_refractory_ms=p.onset_refractory_ms,
            broadband_window_ms=p.broadband_window_ms,
            broadband_coincidence=p.broadband_coincidence,
            sample_rate=int(sample_rate),
        )
    raw = np.ascontiguousarray(samples, dtype=np.float32).tobytes()
    return _rust(sub).run_audio_pipeline(
        audio_stream_nid, raw, int(sample_rate),
    )


__all__ = ["CnParams", "process_audio"]
