"""Cochlear nucleus seed — pipeline as graph data.

Per CLAUDE.md (primitives in Rust + composition in graph): this
seed installs the *pipeline definition* — Operation nodes wired
by feeds_into edges. The Rust runtime
(``runners/dsl/src/pipeline_runtime.rs``) walks that graph and
calls the matching primitive for each op.

The default pipeline for cochlear nucleus is:

    audio
      ├─ gammatone(fc=200) ─ envelope ─ onset_detect ─┐
      ├─ gammatone(fc=400) ─ envelope ─ onset_detect ─┤
      ├─ gammatone(fc=800) ─ envelope ─ onset_detect ─┼─ broadband_coincidence
      ├─ gammatone(fc=1500) ─ envelope ─ onset_detect─┤
      ├─ gammatone(fc=3000) ─ envelope ─ onset_detect─┤
      └─ gammatone(fc=6000) ─ envelope ─ onset_detect─┘

Every node + edge above is graph data. The agent can:

* Read the pipeline:  ``sub.nodes("Operation")`` ; walk feeds_into.
* Add a band:         create a new gammatone Operation, attach
                       envelope + onset_detect downstream, wire to
                       broadband_coincidence.
* Retune a band:      change the fc attr on an existing gammatone op.
* Splice a new stage: insert an Operation between two existing
                       ones, redirect feeds_into.

Adding op kinds = add a primitive + dispatch arm in the Rust
runtime; this Python file just describes the wiring.
"""
from __future__ import annotations


_CN_PRODUCTIONS = [
    # Output node types (unchanged from before — the runtime mints them).
    ("AudioStream", "has_onset_event", "OnsetEvent",
     "cochlear_nucleus:stream_onset"),
    ("AudioStream", "has_envelope", "EnvelopeChannel",
     "cochlear_nucleus:stream_envelope"),
    ("AudioStream", "has_broadband_onset", "BroadbandOnset",
     "cochlear_nucleus:stream_broadband"),
    ("BroadbandOnset", "contributed_by", "OnsetEvent",
     "cochlear_nucleus:broadband_member"),
    # Pipeline-graph edges.
    ("AudioStream", "has_pipeline_entry", "Operation",
     "cochlear_nucleus:stream_pipeline_entry"),
    ("Operation", "feeds_into", "Operation",
     "cochlear_nucleus:operation_feeds_into"),
]


# Default band centres in Hz — 32 log-spaced bands from 80 Hz to
# 7500 Hz. Sample-rate-agnostic upper bound; world adapters can
# clamp under their Nyquist if needed.
#
# Why 32: MelHuBERT (Lin/Lee/Tang 2022) found 40 mel-style channels
# is the empirical sweet spot — 80 did not improve PER/spk-ID/ASR.
# 32 is a touch under, leaving 8 bits of room for the dispatcher,
# DTW, and the trajectory store. Log spacing approximates mel /
# bark / ERB scales over the speech-relevant range and matches
# the cochlea's log-tonotopic layout.
import math as _math
_LOG_LO = _math.log(80.0)
_LOG_HI = _math.log(7500.0)
_DEFAULT_BAND_CENTRES = [
    _math.exp(_LOG_LO + (_LOG_HI - _LOG_LO) * i / 31.0)
    for i in range(32)
]


def install_cochlear_nucleus(substrate) -> None:
    """Install productions + the default cochlear-nucleus pipeline
    as Operation nodes wired by feeds_into edges.

    Idempotent on the productions; the pipeline ops will accumulate
    if called twice. World adapters that want a fresh pipeline
    should remove existing cochlear-nucleus ops first.
    """
    # Productions.
    for src_t, et, tgt_t, prov in _CN_PRODUCTIONS:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass

    # The seed builds the default pipeline at install time. Each
    # AudioStream the world adapter creates downstream uses
    # `attach_default_pipeline` to wire this template against the
    # stream. The seed itself doesn't know about specific streams.


def attach_default_pipeline(substrate, audio_stream_nid,
                              band_centres_hz=None,
                              envelope_cutoff_hz: float = 50.0,
                              onset_threshold_db: float = 6.0,
                              onset_refractory_ms: float = 30.0,
                              broadband_window_ms: float = 25.0,
                              broadband_coincidence: float = 0.4,
                              sample_rate: int = 22050) -> dict:
    """Wire the canonical cochlear-nucleus pipeline onto an
    AudioStream. Returns NodeIDs of the entry gammatone ops + the
    terminal broadband_coincidence op. The pipeline is graph data;
    the agent can introspect or edit it.
    """
    bands = list(band_centres_hz or _DEFAULT_BAND_CENTRES)
    gammatone_ops = []
    onset_ops = []

    # The broadband_coincidence op sits at the end of the pipeline.
    bb_nid = substrate.add_node("Operation", {
        "kind": "broadband_coincidence",
        "window_ms": broadband_window_ms,
        "coincidence_frac": broadband_coincidence,
    })

    for band_i, fc in enumerate(bands):
        gt_nid = substrate.add_node("Operation", {
            "kind": "gammatone",
            "fc": fc,
            "order": 4.0,
            "band_index": float(band_i),
        })
        env_nid = substrate.add_node("Operation", {
            "kind": "envelope",
            "cutoff_hz": envelope_cutoff_hz,
        })
        onset_nid = substrate.add_node("Operation", {
            "kind": "onset_detect",
            "threshold_db": onset_threshold_db,
            "refractory_ms": onset_refractory_ms,
        })
        # Stream → gammatone → envelope → onset_detect → broadband_coincidence
        substrate.add_edge(audio_stream_nid, "has_pipeline_entry", gt_nid)
        substrate.add_edge(gt_nid, "feeds_into", env_nid)
        substrate.add_edge(env_nid, "feeds_into", onset_nid)
        substrate.add_edge(onset_nid, "feeds_into", bb_nid)
        gammatone_ops.append(gt_nid)
        onset_ops.append(onset_nid)

    return {
        "gammatone_ops": gammatone_ops,
        "onset_ops": onset_ops,
        "broadband_op": bb_nid,
    }


__all__ = [
    "install_cochlear_nucleus",
    "attach_default_pipeline",
    "_CN_PRODUCTIONS",
    "_DEFAULT_BAND_CENTRES",
]
