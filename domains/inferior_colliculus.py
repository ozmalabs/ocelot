"""Inferior colliculus seed — modulation-rate analysis as graph pipeline.

Same architectural shape as the refactored cochlear_nucleus:
primitives in Rust (bandpass, rectified_lpf, schmitt_peaks),
composition in graph (Operation nodes wired by feeds_into edges).

The IC pipeline ATTACHES on top of the cochlear_nucleus pipeline.
Each cochlear envelope Operation gets:

  envelope_op ─┬─ bandpass(fc=4 Hz)  ─ rectified_lpf ─ schmitt_peaks  → ModulationChannel + ModulationEvent
               ├─ bandpass(fc=8 Hz)  ─ rectified_lpf ─ schmitt_peaks  → ...
               ├─ bandpass(fc=16 Hz) ─ rectified_lpf ─ schmitt_peaks  → ...
               ├─ ... (6 mod rates total)
               └─ schmitt_peaks (envelope itself) ────────────────────┐
                                                                       ▼
                                                          syllable_coincidence
                                                          (cross-band cluster)
                                                          → SyllableNucleus

Reading the pipeline: ``sub.nodes("Operation")`` shows every step.
Retuning: edit attrs on a bandpass / rectified_lpf / schmitt_peaks
op. Adding modulation rates: add new Operation nodes wired the same
way.
"""
from __future__ import annotations


_IC_PRODUCTIONS = [
    # Terminal-event productions (unchanged).
    ("AudioStream", "has_modulation_channel", "ModulationChannel",
     "ic:stream_mod_channel"),
    ("AudioStream", "has_modulation_event", "ModulationEvent",
     "ic:stream_mod_event"),
    ("AudioStream", "has_syllable_nucleus", "SyllableNucleus",
     "ic:stream_syllable"),
    ("ModulationEvent", "from_channel", "ModulationChannel",
     "ic:event_from_channel"),
    ("SyllableNucleus", "contributed_by", "ModulationEvent",
     "ic:syllable_member"),
    # Pipeline-graph edges (Operation ↔ Operation) — already
    # declared by cochlear_nucleus's `feeds_into` production; the
    # IC's ops live on the same graph.
]


# Default modulation rates the IC bank covers. Six log-spaced rates
# spanning word rhythm (2 Hz) to high pitch (64 Hz).
_DEFAULT_MOD_RATES_HZ = [2.0, 4.0, 8.0, 16.0, 32.0, 64.0]


def install_inferior_colliculus(substrate) -> None:
    """Install IC productions onto a substrate. The pipeline itself
    is wired per-stream by `attach_ic_pipeline` — same pattern as
    cochlear_nucleus."""
    for src_t, et, tgt_t, prov in _IC_PRODUCTIONS:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass


def attach_ic_pipeline(
    substrate, audio_stream_nid,
    *,
    modulation_rates_hz=None,
    mod_q: float = 2.0,
    peak_threshold_db: float = 4.0,
    peak_refractory_ms: float = 80.0,
    syllable_coincidence: float = 0.4,
    syllable_window_ms: float = 60.0,
    syllable_low_hz: float = 4.0,
    syllable_high_hz: float = 8.0,
) -> dict:
    """Wire IC ops onto an audio stream's existing cochlear envelope
    ops. Returns NodeIDs for the modulation chains + the syllable
    coincidence op.

    Idempotent: re-running with an existing IC pipeline appends
    duplicate ops. Don't do that.
    """
    mod_rates = list(modulation_rates_hz or _DEFAULT_MOD_RATES_HZ)

    # 1. Find each cochlear envelope op + the band's gammatone op
    # (for centre_hz + band_index metadata).
    cochlear_envelopes: list[tuple] = []  # (envelope_nid, band_index, centre_hz)
    for entry in substrate.neighbours(audio_stream_nid, "has_pipeline_entry"):
        ea = substrate.node(entry)["attrs"]
        if ea.get("kind") != "gammatone":
            continue
        band_index = int(ea.get("band_index", 0))
        centre_hz = float(ea.get("fc", 0.0))
        for env in substrate.neighbours(entry, "feeds_into"):
            if substrate.node(env)["attrs"].get("kind") == "envelope":
                cochlear_envelopes.append((env, band_index, centre_hz))
                break

    # 2. For each (band envelope, mod_rate) chain bandpass →
    #    rectified_lpf → schmitt_peaks. Each terminal schmitt_peaks
    #    mints a ModulationEvent per peak; the rectified_lpf mints a
    #    ModulationChannel summary.
    modulation_chains: list[dict] = []
    for env_nid, band_index, centre_hz in cochlear_envelopes:
        for rate_hz in mod_rates:
            bp_nid = substrate.add_node("Operation", {
                "kind": "bandpass",
                "fc": float(rate_hz),
                "q": float(mod_q),
            })
            lpf_cutoff = max(rate_hz * 0.25, 1.0)
            rlp_nid = substrate.add_node("Operation", {
                "kind": "rectified_lpf",
                "cutoff_hz": float(lpf_cutoff),
                # Metadata for the runtime to use when minting
                # ModulationChannel.
                "output_node_type": "ModulationChannel",
                "band_index": float(band_index),
                "centre_hz": float(centre_hz),
                "modulation_rate_hz": float(rate_hz),
            })
            sp_nid = substrate.add_node("Operation", {
                "kind": "schmitt_peaks",
                "threshold_db": float(peak_threshold_db),
                "refractory_ms": float(peak_refractory_ms),
                "band_index": float(band_index),
                "centre_hz": float(centre_hz),
                "modulation_rate_hz": float(rate_hz),
                "output_node_type": "ModulationEvent",
            })
            substrate.add_edge(env_nid, "feeds_into", bp_nid)
            substrate.add_edge(bp_nid, "feeds_into", rlp_nid)
            substrate.add_edge(rlp_nid, "feeds_into", sp_nid)
            modulation_chains.append({
                "band_index": band_index,
                "modulation_rate_hz": rate_hz,
                "bandpass": bp_nid,
                "rectified_lpf": rlp_nid,
                "schmitt_peaks": sp_nid,
            })

    # 3. Syllable detection: schmitt_peaks on each cochlear band
    # envelope (the "syllable candidate" detector) → one
    # syllable_coincidence op that aggregates them into
    # SyllableNucleus events. This is the simpler / less-gated
    # version of the original IC's syllable detector; biological
    # gating by 4-8 Hz channel activity is a future graph Rule.
    syll_candidate_ops: list = []
    for env_nid, band_index, centre_hz in cochlear_envelopes:
        sp_nid = substrate.add_node("Operation", {
            "kind": "schmitt_peaks",
            "threshold_db": float(peak_threshold_db),
            "refractory_ms": float(peak_refractory_ms),
            "band_index": float(band_index),
            "centre_hz": float(centre_hz),
            # No output_node_type → these events stay transient
            # (don't mint a graph node directly), they feed the
            # syllable_coincidence op.
        })
        substrate.add_edge(env_nid, "feeds_into", sp_nid)
        syll_candidate_ops.append(sp_nid)

    syll_op = substrate.add_node("Operation", {
        "kind": "syllable_coincidence",
        "window_ms": float(syllable_window_ms),
        "coincidence_frac": float(syllable_coincidence),
        "output_node_type": "SyllableNucleus",
        # Range attrs are not used by the runtime yet — kept here
        # as documentation + for future gating rules.
        "syllable_low_hz": float(syllable_low_hz),
        "syllable_high_hz": float(syllable_high_hz),
    })
    for sp_nid in syll_candidate_ops:
        substrate.add_edge(sp_nid, "feeds_into", syll_op)

    return {
        "modulation_chains": modulation_chains,
        "syllable_candidate_ops": syll_candidate_ops,
        "syllable_coincidence": syll_op,
    }


__all__ = [
    "install_inferior_colliculus",
    "attach_ic_pipeline",
    "_IC_PRODUCTIONS",
    "_DEFAULT_MOD_RATES_HZ",
]
