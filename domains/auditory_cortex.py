"""A1 / belt cortex seed — pipeline as graph data.

Same architectural shape as cochlear_nucleus / inferior_colliculus:
primitives in Rust, composition in graph. The A1 layer adds two
node kinds:

  A1Patch   — declarative patch definition (centre_hz, sigma,
              duration, kind, slope). Already graph-resident.
  Operation{kind: "patch_evaluate"} — runs one A1Patch against
              all cochlear envelopes.

Wiring per stream:

  [each cochlear envelope op]──┐  (every patch consumes
                                ├── every band's envelope)
                                ▼
                           patch_evaluate
                                │
                                ▼ for_patch ▶ A1Patch
                          (mints A1Response)
                                │
                                ▼ feeds_into
                           schmitt_peaks
                          (mints A1Event,
                           wires from_response)

Every patch is one path; per-patch dispatch is graph data.
"""
from __future__ import annotations


_AC_PRODUCTIONS = [
    ("AudioStream", "has_a1_response", "A1Response",
     "auditory_cortex:stream_response"),
    ("AudioStream", "has_a1_event", "A1Event",
     "auditory_cortex:stream_event"),
    ("A1Response", "for_patch", "A1Patch",
     "auditory_cortex:response_for_patch"),
    ("A1Event", "from_response", "A1Response",
     "auditory_cortex:event_from_response"),
    # The patch_evaluate op carries a for_patch edge to its A1Patch
    # so the runtime can wire the same edge on the A1Response it
    # mints.
    ("Operation", "for_patch", "A1Patch",
     "auditory_cortex:op_for_patch"),
]


# A1 patch library — 25 patches, biology-grounded.
#
# Schädler & Kollmeier 2015 (JASA): canonical engineered cortical
# bank is a 5×5 modulation grid (5 spectral × 5 temporal rates),
# matching biology — Kajikawa & Hackett 2015 measured macaque A1
# at ~1.5 oct mean spectral bandwidth, 79% of cells preferring
# 0-0.4 c/oct, 34% preferring ~8 Hz, only 12% at 40 Hz. Plus a
# minority of signed-rate FM patches per Depireux/Shamma.
#
# Our library covers 5 spectral centres × 5 (sigma, duration, FM)
# variants ≈ 25 patches. Centres log-spaced across the speech
# range; per-centre variants exercise the modulation axes biology
# samples. Named patch_<centre_hz>_<variant> for stable
# alphabetic ordering at lexical_access (the trajectory channel
# layout sort is by name).
#
# Naming convention: `pXXXX_<v>` where XXXX is centre_hz padded
# to 4 digits and v is one of {n=narrow, m=med, b=broad,
# f=fast/burst, u=fm-up, d=fm-down}. Sorts alphabetically =
# stable trajectory channel order across runs.

def _patch(name, kind, centre, sigma, dur, slope=0.0):
    return {"name": name, "kind": kind,
            "centre_hz": float(centre),
            "freq_sigma_hz": float(sigma),
            "duration_ms": float(dur),
            "slope_hz_per_ms": float(slope)}


_DEFAULT_PATCHES = (
    # Centre 1: ~400 Hz (low formant / F1 range / voicing fundamentals)
    [
        _patch("p0400_n", "sustained", 400, 150, 80),
        _patch("p0400_m", "sustained", 400, 300, 80),
        _patch("p0400_b", "sustained", 400, 500, 80),
        _patch("p0400_f", "burst",     400, 300, 20),
        _patch("p0400_u", "fm",        400, 200, 60, slope=12.0),
    ]
    # Centre 2: ~800 Hz (vowel F1 / low-mid)
    + [
        _patch("p0800_n", "sustained", 800, 200, 80),
        _patch("p0800_m", "sustained", 800, 400, 80),
        _patch("p0800_b", "sustained", 800, 700, 80),
        _patch("p0800_d", "fm",        800, 300, 60, slope=-15.0),
        _patch("p0800_u", "fm",        800, 300, 60, slope=15.0),
    ]
    # Centre 3: ~1500 Hz (F2 mid / consonant transitions)
    + [
        _patch("p1500_n", "sustained", 1500, 300,  80),
        _patch("p1500_m", "sustained", 1500, 500,  80),
        _patch("p1500_b", "sustained", 1500, 900,  80),
        _patch("p1500_u", "fm",        1500, 400,  60, slope=20.0),
        _patch("p1500_d", "fm",        1500, 400,  60, slope=-20.0),
    ]
    # Centre 4: ~3000 Hz (F3 / consonant onsets)
    + [
        _patch("p3000_n", "sustained", 3000, 500,  80),
        _patch("p3000_m", "sustained", 3000, 900,  80),
        _patch("p3000_b", "sustained", 3000, 1500, 80),
        _patch("p3000_f", "burst",     3000, 1200, 20),
        _patch("p3000_u", "fm",        3000, 700,  60, slope=25.0),
    ]
    # Centre 5: ~5500 Hz (sibilant range; clamped under 8kHz Nyquist
    # at FSDD so synthesis stays safe; analysis benefits from
    # high-frequency coverage either way).
    + [
        _patch("p5500_n", "sustained", 5500, 800,  80),
        _patch("p5500_m", "sustained", 5500, 1500, 80),
        _patch("p5500_b", "sustained", 5500, 2500, 80),
        _patch("p5500_f", "burst",     5500, 2000, 20),
        _patch("p5500_u", "fm",        5500, 1200, 60, slope=30.0),
    ]
)


def install_auditory_cortex(substrate) -> None:
    """Install A1 productions + the default patch library. The
    pipeline ops themselves are wired per-stream by
    attach_a1_pipeline (same shape as cochlear / IC seeds)."""
    for src_t, et, tgt_t, prov in _AC_PRODUCTIONS:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass
    for patch in _DEFAULT_PATCHES:
        substrate.add_node("A1Patch", patch)


def attach_a1_pipeline(
    substrate, audio_stream_nid,
    *,
    peak_threshold_db: float = 4.0,
    peak_refractory_ms: float = 50.0,
) -> dict:
    """Wire one patch_evaluate Operation per A1Patch onto an audio
    stream's existing cochlear envelope ops, with a downstream
    schmitt_peaks for A1Event minting. Returns NodeIDs of the per-
    patch chains.
    """
    # 1. Gather cochlear envelope ops on this stream.
    envelopes = []
    for entry in substrate.neighbours(audio_stream_nid, "has_pipeline_entry"):
        ea = substrate.node(entry)["attrs"]
        if ea.get("kind") != "gammatone":
            continue
        for env in substrate.neighbours(entry, "feeds_into"):
            if substrate.node(env)["attrs"].get("kind") == "envelope":
                envelopes.append(env)
                break

    # 2. Per A1Patch, create patch_evaluate + schmitt_peaks chain.
    chains = []
    for patch_nid in substrate.nodes("A1Patch"):
        pa = substrate.node(patch_nid)["attrs"]
        pe_nid = substrate.add_node("Operation", {
            "kind": "patch_evaluate",
            "patch_name": pa["name"],
            "patch_kind": pa["kind"],
            "centre_hz": float(pa["centre_hz"]),
            "freq_sigma_hz": float(pa["freq_sigma_hz"]),
            "duration_ms": float(pa["duration_ms"]),
            "slope_hz_per_ms": float(pa.get("slope_hz_per_ms", 0.0)),
        })
        substrate.add_edge(pe_nid, "for_patch", patch_nid)
        for env in envelopes:
            substrate.add_edge(env, "feeds_into", pe_nid)

        sp_nid = substrate.add_node("Operation", {
            "kind": "schmitt_peaks",
            "threshold_db": float(peak_threshold_db),
            "refractory_ms": float(peak_refractory_ms),
            "patch_name": pa["name"],
            "output_node_type": "A1Event",
        })
        substrate.add_edge(pe_nid, "feeds_into", sp_nid)
        chains.append({
            "patch": patch_nid,
            "patch_evaluate": pe_nid,
            "schmitt_peaks": sp_nid,
        })

    return {"chains": chains}


__all__ = [
    "install_auditory_cortex",
    "attach_a1_pipeline",
    "_AC_PRODUCTIONS",
    "_DEFAULT_PATCHES",
]
