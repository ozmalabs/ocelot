"""MULTI-RELATIONAL graph G: the SAME node held by FOUR relations at once —
SHAPE (shares_shape, existing) + TIMBRE + AFFECT + FUNCTION.

The thesis ("it's a graph, not an index"): a memory/percept is a NODE held by
MANY edges. Order-N SHAPE is ONE relation; this wires three more, each with its
OWN per-node signature, OWN Γ-declared edge type, and — crucially — its OWN
PROPER METRIC + scale-derived threshold (NOT tuned). The held spread() walks
every edge type, so recall = spreading activation across ALL of them — plural,
BY RELATION. The PROOF is the contrast: the SAME nodes have DIFFERENT
neighbours under DIFFERENT relations.

PER-RELATION METRICS (the fix): ordinal rank is right for a TRAJECTORY (shape)
but WRONG for a heterogeneous feature vector (affect) or a category (function).
  - SHAPE / TIMBRE : ordinal-rank shape_distance (gain-invariant, a SHAPE).
  - AFFECT         : PER-FEATURE z-score normalise across the clip population,
    THEN L2 (a POINT in normalised arousal/valence space). Heterogeneous units
    (onset-rate ~0.4 vs pitch ~100s Hz vs centroid ~1000s Hz) made ordinal rank
    collapse them + raw L2 dominated by the big-unit features.
  - FUNCTION       : CATEGORICAL Hamming match on the bucketed role vector
    (same structural role), NOT a trajectory distance.

METHOD: replicate ONE cognitive edge -> ISOLATE it -> MEASURE with controls.
Each edge is tested in isolation (does it link the RIGHT neighbours + exclude
controls?) and reported HONESTLY as RIGOROUS (timbre, held audio), PROXY
(affect, coarse acoustic correlates), or WEAK (function, most-derived).

THE THREE SIGNATURES (world-adapter DSP feeding the per-relation metric):
  1. TIMBRE  (rigorous) — gammatone-band log-energy envelope over the salient
     region (held srs.gammatone_band across a centre-freq bank) -> a
     fixed-length spectral-envelope vector -> ordinal-rank (gain-invariant).
     Cartoon/synth clips are timbre-near each other; orchestral Grieg is
     timbre-FAR -> the multi-relational proof (shape links tada<->Grieg).
  2. AFFECT  (proxy)    — arousal/valence acoustic correlates: arousal =
     onset-rate + energy + pitch-height; valence = spectral brightness +
     a major-ish/minor-ish band-balance proxy (held stft/f0). Coarse.
  3. FUNCTION (weak)    — structural ROLE from the salient build: a rise->hit
     with a directed shape = "climax/reveal"; flat = "background"; abrupt =
     "accent". The most-derived; reported honestly.

Run:  python -m scripts.multi_relational_demo
"""
from __future__ import annotations
import os, sys
import numpy as np

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
from substrate_rs import Substrate, _native as srs
from scripts.pitch_rhythm_frontend import (
    _load, locate_build, _flux_density, _resample, CHAN, _WIN, _HOP, _HALF,
)

# --- world-adapter feature extractors (DSP -> fixed-length vectors) -------
# All hand the vector to the HELD Substrate.shape_signature (ordinal rank),
# so every relation reuses ONE gain-invariant metric. No ML, no tuning.

N_BANDS = 12          # timbre: log-spaced gammatone bank size
GT_ORDER = 4


def _erb_centres(lo=120.0, hi=7000.0, n=N_BANDS):
    """Log-spaced centre freqs (an ERB-ish bank) for the timbre profile."""
    return np.exp(np.linspace(np.log(lo), np.log(hi), n))


def timbre_vector(x, sr, t0, t1):
    """TIMBRE = the spectral-envelope profile = per-band RMS energy of the
    salient region, in dB. Held srs.gammatone_band per centre freq. The shape
    (relative band balance) is the timbre; absolute level is removed by the
    ordinal rank downstream, so it is gain-invariant by construction."""
    i0, i1 = int(t0 * sr), int(t1 * sr)
    seg = x[i0:i1] if i1 > i0 + sr // 4 else x       # fall back to whole clip
    seg = seg.astype("float32")
    prof = []
    for fc in _erb_centres():
        band = np.array(srs.gammatone_band(list(seg), sr, float(fc), GT_ORDER))
        rms = float(np.sqrt(np.mean(band * band)) + 1e-9)
        prof.append(float(20.0 * np.log10(rms)))
    return prof


def affect_vector(x, sr, t0, t1):
    """AFFECT (proxy) = [arousal cues || valence cues], coarse acoustic
    correlates with HETEROGENEOUS UNITS. Arousal: onset-rate (~0.4),
    energy (dB), pitch-height (~100s Hz). Valence: spectral brightness /
    centroid (~1000s Hz) + a low/high band-balance proxy. Because the units
    differ by orders of magnitude, the RAW vector is handed to the affect
    metric (wire_relation_affect), which PER-FEATURE z-score normalises across
    the clip population THEN takes L2 — a point in normalised arousal/valence
    space, NOT an ordinal-rank trajectory.

    Honest: this is a PROXY. Valence especially (brightness != musical mode)
    is a loose stand-in, reported as such."""
    i0, i1 = int(t0 * sr), int(t1 * sr)
    seg = x[i0:i1] if i1 > i0 + sr // 4 else x
    seg = seg.astype("float32")

    # held stft over the salient region.
    flat = srs.stft(list(seg), _WIN, _HOP)
    spec = np.array(flat, dtype=np.float64).reshape(-1, _HALF) if flat else np.zeros((1, _HALF))
    freqs = np.arange(_HALF) * sr / _WIN
    mag = spec + 1e-9

    # AROUSAL cues
    raw_flux = np.maximum(np.diff(spec, axis=0), 0.0).sum(axis=1) if spec.shape[0] > 1 else np.array([0.0])
    onset_rate = float((raw_flux > 0.3 * (raw_flux.max() + 1e-9)).mean())  # frac active frames
    energy = float(20.0 * np.log10(np.sqrt(np.mean(seg * seg)) + 1e-9))
    # pitch height: held f0_yin, voiced median.
    frame, fhop, f0s = 2048, 512, []
    j = 0
    while j + frame <= len(seg):
        v = srs.f0_yin(list(seg[j:j + frame]), sr, 65.0, 1200.0, 0.15)
        if v > 0:
            f0s.append(v)
        j += fhop
    pitch_height = float(np.median(f0s)) if f0s else 0.0

    # VALENCE cues (PROXY)
    centroid = float((mag * freqs).sum() / mag.sum())             # brightness
    lo_e = float(mag[:, freqs < 500].sum())
    hi_e = float(mag[:, freqs >= 500].sum())
    band_balance = float(hi_e / (lo_e + 1e-9))                    # bright/dark balance

    return [onset_rate, energy, pitch_height, centroid, band_balance]


def function_signature(x, sr, t0, t1, ramp):
    """FUNCTION = the structural/narrative ROLE, derived from the salient
    build, as a SMALL CATEGORICAL bucket vector. A category, NOT a trajectory
    — so it is wired by the CATEGORICAL (Hamming) metric, not ordinal rank.
    Same-role clips (same buckets) become function-neighbours.

    Roles (structural, no TV-Tropes name lookup wired here — honest):
      climax/reveal : directed rise -> hit (high salience, rising ramp)
      accent/sting  : short abrupt event (high salience, brief)
      background    : low salience / flat
    The signature = [is_rising, salience_bucket, span_bucket, peak_late]."""
    if ramp is None:
        return ["background", [0, 0, 0, 0]]
    sal = Substrate.shape_salience(list(ramp))
    rng = float(np.max(ramp) - np.min(ramp))
    rising = ramp[-1] > ramp[0] and rng > 0.1
    span_s = t1 - t0
    peak_idx = int(np.argmax(ramp))
    peak_late = peak_idx >= 0.6 * (len(ramp) - 1)

    if sal > 0.5 and rising:
        role = "climax/reveal"
    elif sal > 0.5 and span_s < 1.5:
        role = "accent/sting"
    else:
        role = "background"

    sig = [
        1 if rising else 0,
        int(min(3, sal * 4)),                 # salience bucket 0..3
        int(min(3, span_s)),                  # span bucket 0..3 (seconds)
        1 if peak_late else 0,
    ]
    return [role, sig]


# --- the demo -------------------------------------------------------------

def _ensure_controls():
    import wave
    sr = 16000

    def mkwav(p, xx):
        w = wave.open(p, "w"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(xx, -1, 1) * 32767).astype("int16").tobytes()); w.close()
    if not os.path.exists("/tmp/mr_flat.wav"):
        mkwav("/tmp/mr_flat.wav", 0.2 * np.sin(2 * np.pi * 440 * np.arange(int(4 * sr)) / sr))
    if not os.path.exists("/tmp/mr_random.wav"):
        rng = np.random.default_rng(0)
        mkwav("/tmp/mr_random.wav", 0.2 * rng.standard_normal(int(4 * sr)))


def extract(path):
    """Extract ALL four signatures for a clip. Returns a dict or {'reason'}."""
    x, sr = _load(path)
    t0, t1, ramp = locate_build(x, sr)
    if ramp is None:
        # still extract timbre/affect over the whole clip for controls
        t0, t1 = 0.0, len(x) / sr
    shape_sig = Substrate.shape_signature(list(ramp)) if ramp is not None else None
    timbre_raw = timbre_vector(x, sr, t0, t1)
    timbre_sig = Substrate.shape_signature(timbre_raw)
    affect_raw = affect_vector(x, sr, t0, t1)
    # affect_sig (ordinal rank) is kept ONLY for the BEFORE comparison; the
    # proper metric normalises affect_raw per-feature across the population.
    affect_sig = Substrate.shape_signature(affect_raw)
    role, func_sig = function_signature(x, sr, t0, t1, ramp)
    return {
        "win": (t0, t1),
        "shape_sig": list(shape_sig) if shape_sig is not None else None,
        "timbre_raw": [round(v, 1) for v in timbre_raw], "timbre_sig": list(timbre_sig),
        "affect_raw": [float(v) for v in affect_raw], "affect_sig": list(affect_sig),
        "role": role, "func_sig": list(func_sig),
        "has_build": ramp is not None,
    }


def _pairwise(built, info, key, thr, label, distfn=None):
    """Pairwise distances under a given metric. distfn(sa, sb) -> int;
    defaults to the ordinal-rank shape distance. sigs come from info[name][key]
    unless key is a callable producing the per-name signature."""
    distfn = distfn or Substrate.shape_signature_distance
    print(f"\n  {label} pairwise distances (threshold={thr}):")
    names = list(built)
    links = 0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            sa = key(a) if callable(key) else info[a][key]
            sb = key(b) if callable(key) else info[b][key]
            if sa is None or sb is None:
                continue
            d = distfn(sa, sb)
            linked = d < thr
            links += int(linked)
            mark = "  <== LINK" if linked else ""
            print(f"    {a:<15} <-> {b:<15} : {d:>6}{mark}")
    print(f"    -> {links} undirected links of {len(names)*(len(names)-1)//2} pairs")


def main():
    print("=" * 78)
    print("MULTI-RELATIONAL G: shape | timbre | affect | function on ONE node set")
    print("=" * 78)
    _ensure_controls()

    clips = [
        ("tada_storybots", "/tmp/storybots.ogg"),
        ("mountain_king",  "/tmp/mtnking.wav"),
        ("twinkle",        "/tmp/salient_twinkle.wav"),
        ("bingo",          "/tmp/salient_bingo.wav"),
        ("flat_tone",      "/tmp/mr_flat.wav"),
        ("random_noise",   "/tmp/mr_random.wav"),
    ]
    clips = [(n, p) for n, p in clips if os.path.exists(p)]

    info = {}
    print("\n  Per-clip signatures (DSP world-adapter -> held ordinal-rank op):\n")
    for name, path in clips:
        r = extract(path)
        info[name] = r
        t0, t1 = r["win"]
        print(f"    {name:<15} build@{t0:5.1f}-{t1:5.1f}s  role={r['role']}")
        print(f"        shape_sig  {r['shape_sig']}")
        print(f"        timbre_raw {r['timbre_raw']}")
        print(f"        timbre_sig {r['timbre_sig']}")
        print(f"        affect_raw {[round(v, 2) for v in r['affect_raw']]}  (onset,energy,pitch,centroid,balance)")
        print(f"        func_sig   {r['func_sig']}")

    built = list(info)

    # --- POPULATION-NORMALISED affect signatures (the proper affect metric).
    # Per-feature z-score across the EXACT clip set being linked, in the core.
    affect_raws = [info[n]["affect_raw"] for n in built]
    affect_normed = Substrate.affect_normalize(affect_raws)
    affect_norm = {n: list(affect_normed[i]) for i, n in enumerate(built)}
    for n in built:
        info[n]["affect_norm"] = affect_norm[n]

    # --- ISOLATED per-edge pairwise distances + thresholds ---------------
    thr_shape = Substrate.shape_neighbour_threshold(CHAN)
    thr_timbre = Substrate.shape_neighbour_threshold(N_BANDS)
    n_aff = len(affect_raws[0]) if affect_raws else 5
    thr_affect_rank = Substrate.shape_neighbour_threshold(n_aff)   # WRONG metric
    thr_affect = Substrate.affect_neighbour_threshold(n_aff)            # PROPER metric
    thr_func_rank = Substrate.shape_neighbour_threshold(4)         # WRONG metric
    thr_func = Substrate.categorical_neighbour_threshold(4)             # PROPER metric

    _pairwise(built, info, "shape_sig", thr_shape, "SHAPE  (existing, ordinal rank)")
    _pairwise(built, info, "timbre_sig", thr_timbre, "TIMBRE (RIGOROUS, ordinal rank)")

    print("\n" + "-" * 78)
    print("  AFFECT — BEFORE (ordinal rank, WRONG) vs AFTER (normalised L2, PROPER)")
    print("-" * 78)
    _pairwise(built, info, "affect_sig", thr_affect_rank,
              "AFFECT BEFORE (ordinal-rank shape — over-links)")
    _pairwise(built, info, "affect_norm", thr_affect,
              "AFFECT AFTER  (per-feature z-norm + L2)",
              distfn=Substrate.l2_signature_distance)

    print("\n" + "-" * 78)
    print("  FUNCTION — BEFORE (ordinal rank, WRONG) vs AFTER (categorical, PROPER)")
    print("-" * 78)
    _pairwise(built, info, "func_sig", thr_func_rank,
              "FUNCTION BEFORE (ordinal-rank shape — over-links)")
    _pairwise(built, info, "func_sig", thr_func,
              "FUNCTION AFTER  (categorical / Hamming match)",
              distfn=Substrate.categorical_signature_distance)

    # --- WIRE all four relations onto ONE node set -----------------------
    print("\n" + "=" * 78)
    print("  WIRING: the SAME node carries all four signatures + edge types")
    print("=" * 78)
    s = Substrate()
    s.declare_shares_shape()
    s.declare_relation_edge("timbre_kin", "timbre (spectral-envelope neighbour)")
    s.declare_relation_edge("affect_kin", "affect (arousal/valence proxy neighbour)")
    s.declare_relation_edge("function_kin", "function (structural role neighbour)")

    nodes = {}
    for name in built:
        # node carries the SHAPE signature; falls back to a flat sig if no build.
        ssig = info[name]["shape_sig"] or [0] * CHAN
        nid, shape_linked = s.add_salient_shape(name, ssig)
        nodes[name] = nid
    # TIMBRE keeps the ordinal-rank metric (a spectral-envelope SHAPE — rank
    # is correct there). FUNCTION uses the CATEGORICAL metric. AFFECT uses the
    # population-normalised L2 metric (batch, needs the whole node set).
    for name in built:
        nid = nodes[name]
        s.wire_relation(nid, "timbre_kin", "timbre_sig", info[name]["timbre_sig"],
                        "timbre (spectral-envelope neighbour)")
        s.wire_relation_categorical(nid, "function_kin", "function_sig",
                        info[name]["func_sig"],
                        "function (structural role — categorical match)")
    # AFFECT: per-feature normalised L2 over the population, wired in one call.
    node_list = [nodes[name] for name in built]
    raw_list = [info[name]["affect_raw"] for name in built]
    s.wire_relation_affect(node_list, "affect_kin", "affect_norm", raw_list,
                    "affect (arousal/valence — normalised L2)")

    def neigh(name, et):
        out = []
        for x in s.neighbours(nodes[name], et):
            out.append(s.node(x)["attrs"].get("label", "?"))
        return sorted(out)

    print("\n  Per-node neighbours BY RELATION (same node, different edges):\n")
    for name in built:
        print(f"    {name}")
        print(f"        shares_shape : {neigh(name, 'shares_shape')}")
        print(f"        timbre_kin   : {neigh(name, 'timbre_kin')}")
        print(f"        affect_kin   : {neigh(name, 'affect_kin')}")
        print(f"        function_kin : {neigh(name, 'function_kin')}")

    # --- THE MULTI-RELATIONAL CONTRAST ----------------------------------
    print("\n  KEY CONTRAST (same nodes, different neighbours per relation):")
    if "tada_storybots" in nodes and "mountain_king" in nodes:
        t, m = nodes["tada_storybots"], nodes["mountain_king"]
        for et in ("shares_shape", "timbre_kin", "affect_kin", "function_kin"):
            linked = s.has_edge(t, et, m)
            print(f"    tada <-{et:>14}-> mountain_king : {linked}")

    # --- SPREAD: plural recall BY RELATION -------------------------------
    if "tada_storybots" in nodes:
        print("\n  SPREAD from tada (each neighbour labelled by the edge that surfaced it):")
        seen = {}
        for x, et, hop in s.spread(nodes["tada_storybots"], 1):
            lbl = s.node(x)["attrs"].get("label", "?")
            seen.setdefault(lbl, []).append(et)
        for lbl, ets in sorted(seen.items()):
            print(f"    {lbl:<15} via {sorted(set(ets))}")

    # --- over-link / control check + memory bound -----------------------
    print("\n  CONTROL / over-link check (flat_tone, random_noise should NOT link):")
    for ctrl in ("flat_tone", "random_noise"):
        if ctrl in nodes:
            tot = sum(len(s.neighbours(nodes[ctrl], et))
                      for et in ("shares_shape", "timbre_kin", "affect_kin", "function_kin"))
            print(f"    {ctrl:<15} total edges across all relations: {tot}")

    nn = len(s.nodes("SalientShape"))
    for et in ("shares_shape", "timbre_kin", "affect_kin", "function_kin"):
        ne = sum(len(s.neighbours(n, et)) for n in s.nodes("SalientShape"))
        print(f"  {et:<14}: {ne} directed edges  (all-to-all would be {nn*(nn-1)})")

    print("\n" + "=" * 78)
    print("  PER-RELATION METRICS: shape/timbre = ordinal rank (a SHAPE); affect =")
    print("  per-feature z-norm + L2 (a heterogeneous POINT); function = categorical")
    print("  Hamming (a CATEGORY). Affect separates + excludes both controls. Function")
    print("  separates + excludes flat; random_noise's coarse role bucket spuriously")
    print("  matches the build role (the METRIC is right, the FEATURE is too coarse).")
    print("=" * 78)


if __name__ == "__main__":
    main()
