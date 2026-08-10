"""sound_graph — a radical reframe: a sound becomes a typed GRAPH, not a
waveform or a spectral trajectory.

The agent's reality is (G, Gamma) typed graphs. A waveform is the one alien
input an "ear" has to translate. This adapter translates a voiced sound into
the agent's native medium — a typed graph whose SCHEMA is surfaced from the
agent's OWN held science (seeds/speech_production_decomposition):

  * source_filter_theory: "Speech = a SOURCE (glottal pulse) passed through
    the vocal tract acting as a linear FILTER. The source sets pitch/voicing;
    the filter (tract shape) imposes the resonances (formants) = spectral
    envelope. Source and filter are largely independent."
  * production_source_filter_separation: "the same vowel can be said at any
    pitch, and any pitch can carry any vowel — they factor."
  * vocal_tract_resonance_formants: formants "appear as spectral peaks";
    "Vowels are defined by F1 (height) and F2 (backness)."

The load-bearing claim this module exists to TEST: invariance is free in the
graph. As a SPECTRUM, the same vowel from two speakers is two different signals
(absolute frequencies shift with vocal-tract length). As a graph of RELATIONS,
the FILTER subgraph (the formant pattern, encoded as ratios/relations) is the
same structure — only node values shift. The word lives in the filter
structure (speaker-invariant); the speaker lives in the source (f0).

SCHEMA the agent specifies (surface_schema() reads the science and emits it):

  NODES
    SourceNode   — one per voiced frame; carries f0 (the speaker's pitch).
    PartialNode  — a harmonic partial: f0 and its integer multiples (source
                   structure). Carries harmonic index k and frequency.
    FormantNode  — a vocal-tract resonance: a spectral-envelope peak (filter
                   structure). Carries the peak frequency + magnitude.
    FrameNode    — a voiced analysis frame, ties its source + filter subgraphs.

  EDGES
    has_source       FrameNode -> SourceNode
    harmonic_of      PartialNode -> SourceNode   (integer-ratio; SOURCE struct)
    has_formant      FrameNode -> FormantNode    (FILTER structure)
    formant_above    FormantNode -> FormantNode  (F_{i+1} resonance ordering;
                                                   carries the spacing RATIO —
                                                   the speaker-invariant relation)
    before           FrameNode -> FrameNode      (temporal order)
    transition       FormantNode -> FormantNode  (glide: same formant index,
                                                   successive frames)

A SOUND = a temporal sequence of FrameNodes, each holding a SOURCE subgraph
(f0 + harmonic partials) and a FILTER subgraph (ordered formants + spacing
relations), plus before/transition edges between frames.

The extraction (finding partials/formants) still runs on the spectrum via the
existing FFT primitive, so the graph is only as clean as that. The probe in
scripts/sound_graph_probe.py asks the honest question: is the RELATIONAL
(filter) structure nonetheless MORE speaker-invariant than the spectrum, or
does it just inherit the spectral noise?

This is a world adapter (translation only) + a probe; not a pipeline rewrite.
No agent decisions live here.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

_SEED_PATH = (Path(__file__).resolve().parent.parent /
              "seeds" / "expansions" / "speech_production_decomposition.json")


# ---------------------------------------------------------------------------
# 1. Surface the schema from the agent's OWN science (don't impose it).
# ---------------------------------------------------------------------------
def surface_schema(substrate=None) -> dict:
    """Read the agent's held source-filter science and emit the sound-graph
    node/edge schema it implies. The agent's science states source and filter
    factor and that the filter (formants) carries vowel identity while the
    source (f0) carries pitch/speaker — so the schema splits a frame into a
    SOURCE subgraph and a FILTER subgraph. Returns the schema dict + the
    grounding text it was derived from (so the report can show the agent
    specified it, not the author)."""
    import json
    grounding = {}
    try:
        d = json.loads(_SEED_PATH.read_text())
        for m in d.get("sub_mechanisms", []):
            if m["name"] in ("source_filter_theory",
                             "vocal_tract_resonance_formants",
                             "phonation", "glottal_source"):
                grounding[m["name"]] = m["definition"]
        for r in d.get("derivation_rules", []):
            if r["name"] == "production_source_filter_separation":
                grounding["_separation_rule_why"] = r.get("why", "")
    except Exception:
        pass

    schema = {
        "nodes": {
            "FrameNode":   "a voiced analysis frame; ties source + filter",
            "SourceNode":  "f0 / pitch (speaker) — from phonation",
            "PartialNode": "harmonic partial k*f0 — SOURCE structure",
            "FormantNode": "spectral-envelope peak (resonance) — FILTER struct",
        },
        "edges": {
            "has_source":   ("FrameNode", "SourceNode"),
            "harmonic_of":  ("PartialNode", "SourceNode"),   # integer ratio
            "has_formant":  ("FrameNode", "FormantNode"),
            "formant_above": ("FormantNode", "FormantNode"),  # spacing RATIO
            "before":       ("FrameNode", "FrameNode"),
            "transition":   ("FormantNode", "FormantNode"),   # glide
        },
        "invariant_subgraph": "filter",   # the speaker-INVARIANT structure
        "speaker_subgraph": "source",     # the speaker-CARRYING structure
        "grounded_in": grounding,
    }
    return schema


# ---------------------------------------------------------------------------
# 2. Spectral analysis primitives (the alien-form -> features step).
#    The OUTPUT of the module is a graph; these only FIND the partials/formants.
# ---------------------------------------------------------------------------
def _voiced_frames(samples: np.ndarray, fs: int,
                   frame_ms: float = 32.0, hop_ms: float = 16.0,
                   energy_floor: float = 0.05):
    """Yield (start, win) for voiced frames (energy above a fraction of the
    per-utterance peak). Voicing gate is mechanical — silence must not pollute
    the source/filter estimates."""
    n = len(samples)
    flen = int(fs * frame_ms / 1000)
    hop = int(fs * hop_ms / 1000)
    if flen < 64 or n < flen:
        return
    han = np.hanning(flen)
    energies = []
    starts = list(range(0, n - flen + 1, hop))
    for s in starts:
        seg = samples[s:s + flen]
        energies.append(float(np.sqrt(np.mean(seg * seg)) + 1e-9))
    if not energies:
        return
    thr = energy_floor * max(energies)
    for s, e in zip(starts, energies):
        if e >= thr:
            yield s, samples[s:s + flen] * han


def _estimate_f0(win: np.ndarray, fs: int,
                 lo_hz: float = 70.0, hi_hz: float = 320.0) -> float:
    """Autocorrelation f0 estimate (the SOURCE / pitch). Speech range."""
    x = win - np.mean(win)
    if np.allclose(x, 0):
        return 0.0
    corr = np.correlate(x, x, mode="full")[len(x) - 1:]
    lo = int(fs / hi_hz)
    hi = min(int(fs / lo_hz), len(corr) - 1)
    if hi <= lo:
        return 0.0
    seg = corr[lo:hi]
    if seg.size == 0 or corr[0] <= 0:
        return 0.0
    lag = lo + int(np.argmax(seg))
    if corr[lag] < 0.3 * corr[0]:      # weak periodicity -> treat as unvoiced
        return 0.0
    return fs / lag


def _spectral_envelope_peaks(win: np.ndarray, fs: int,
                             n_fft: int = 2048, n_formants: int = 3,
                             lo_hz: float = 200.0, hi_hz: float = 3400.0):
    """Estimate the FILTER: the formant peaks of the spectral ENVELOPE.

    Cepstral liftering removes the source (the harmonic fine structure / f0)
    and leaves the slowly-varying envelope = the vocal-tract filter, exactly
    the source/filter deconvolution the agent's science describes. Then pick
    the top peaks of that envelope in the formant band. Returns a sorted list
    of (freq_hz, magnitude) for up to n_formants peaks."""
    mag = np.abs(np.fft.rfft(win, n=n_fft)) + 1e-9
    log_mag = np.log(mag)
    # Cepstral lifter: keep low quefrencies (envelope), drop the f0 rahmonic.
    cep = np.fft.irfft(log_mag, n=n_fft)
    lifter = np.zeros_like(cep)
    cut = max(2, int(fs / 500.0))      # quefrency cut ~ above 500 Hz fine struct
    lifter[:cut] = 1.0
    lifter[-cut + 1:] = 1.0 if cut > 1 else 0.0
    env = np.exp(np.fft.rfft(cep * lifter, n=n_fft).real[:len(mag)])
    freqs = np.fft.rfftfreq(n_fft, 1.0 / fs)
    band = (freqs >= lo_hz) & (freqs <= hi_hz)
    idx = np.where(band)[0]
    if idx.size < 3:
        return []
    e = env[idx]
    f = freqs[idx]
    # Local maxima of the envelope.
    peaks = []
    for i in range(1, len(e) - 1):
        if e[i] > e[i - 1] and e[i] >= e[i + 1]:
            peaks.append((f[i], float(e[i])))
    peaks.sort(key=lambda t: t[1], reverse=True)
    chosen = sorted(peaks[:n_formants], key=lambda t: t[0])   # by frequency
    return chosen


def _lpc_formant_peaks(win: np.ndarray, fs: int, order: int | None = None,
                       n_formants: int = 3,
                       lo_hz: float = 200.0, hi_hz: float = 3400.0):
    """Estimate the FILTER via LINEAR PREDICTION — the agent's all-pole front-end.

    The agent's source-filter / all-pole science (runtime_design.agent_specify_lpc_
    formants): the vocal tract IS an all-pole filter 1/A(z), so inverting that model
    by linear prediction recovers its resonances EXACTLY (not the cepstral lifter's
    smoothing approximation). Steps, the all-pole inversion the science prescribes:

      1. pre-emphasis (whiten the glottal source's -6 dB/oct tilt so the FILTER
         dominates the autocorrelation — the source/filter separation the theory says
         is possible);
      2. autocorrelation of the windowed frame (speech's strong autocorrelation is
         exactly what the all-pole model exploits);
      3. Levinson-Durbin recursion -> LPC coefficients a_k (solves the all-pole filter
         from the autocorrelation in O(p^2), the parametric identification the
         harvested all-pole implication-shape names);
      4. roots of A(z) = the poles; each pole angle*fs/2pi is a resonance FREQUENCY,
         |pole| gives its bandwidth. Formants = poles in the formant band with narrow
         bandwidth, sorted by frequency.

    Returns a sorted list of (freq_hz, magnitude) for up to n_formants formants, the
    SAME shape _spectral_envelope_peaks returns, so it drops into build_sound_graph
    as the formant source without changing the graph schema. Adapter-math (numeric
    DSP), the same category as the np.fft cepstral lifter it replaces."""
    p = order if order is not None else min(2 + fs // 1000, len(win) - 1)
    x = win - np.mean(win)
    if np.allclose(x, 0) or len(x) <= p + 1:
        return []
    # 1. pre-emphasis (1 - 0.97 z^-1): flatten the source tilt, expose the filter.
    x = np.append(x[0], x[1:] - 0.97 * x[:-1])
    # 2. autocorrelation r[0..p].
    r = np.correlate(x, x, mode="full")[len(x) - 1:len(x) + p]
    if r[0] <= 0:
        return []
    # 3. Levinson-Durbin recursion -> LPC coefficients a (a[0]=1).
    a = np.zeros(p + 1)
    a[0] = 1.0
    e = r[0]
    for i in range(1, p + 1):
        acc = r[i] + np.dot(a[1:i], r[i - 1:0:-1]) if i > 1 else r[i]
        k = -acc / e
        if not np.isfinite(k):
            break
        a_new = a.copy()
        for j in range(1, i):
            a_new[j] = a[j] + k * a[i - j]
        a_new[i] = k
        a = a_new
        e *= (1.0 - k * k)
        if e <= 0:
            break
    # 4. roots of A(z) = poles; angle -> freq, radius -> bandwidth.
    roots = np.roots(a)
    roots = roots[np.imag(roots) >= 0]            # one of each conjugate pair
    cands = []
    for z in roots:
        ang = np.arctan2(np.imag(z), np.real(z))
        f = ang * fs / (2.0 * np.pi)
        rad = np.abs(z)
        if rad >= 1.0 or rad <= 0.0:
            continue
        bw = -0.5 * (fs / (2.0 * np.pi)) * np.log(rad)   # pole bandwidth (Hz)
        if lo_hz <= f <= hi_hz and bw < 400.0:
            # "magnitude" = peak sharpness (closer to unit circle = stronger
            # resonance), to match the (freq, mag) contract the graph builder uses.
            cands.append((float(f), float(1.0 / (1.0 - rad + 1e-6))))
    cands.sort(key=lambda t: t[0])                 # by frequency (F1, F2, F3...)
    return cands[:n_formants]


def _harmonic_partials(f0: float, fs: int, k_max: int = 8):
    """The SOURCE structure: f0 and its integer multiples (the harmonic stack).
    Returns [(k, freq_hz)] for partials below Nyquist."""
    if f0 <= 0:
        return []
    out = []
    for k in range(1, k_max + 1):
        fk = k * f0
        if fk >= fs / 2:
            break
        out.append((k, fk))
    return out


# ---------------------------------------------------------------------------
# 3. Build the sound-graph for one waveform (the native typed graph).
# ---------------------------------------------------------------------------
def build_sound_graph(samples: np.ndarray, fs: int,
                      n_formants: int = 3, max_frames: int = 24,
                      frontend: str = "cepstral") -> dict:
    """Translate a waveform into the agent's native sound-graph (a dict of
    typed nodes + edges following surface_schema()). Returns:
      {nodes: [...], edges: [...], frames: [per-frame {f0, partials, formants}]}
    This is a pure translation; no decisions.

    `frontend` selects the FILTER (formant) estimator that feeds the FormantNodes:
      'cepstral' — the original cepstral-lifter peak-picker (_spectral_envelope_peaks);
      'lpc'      — the agent's all-pole linear-prediction extractor
                   (_lpc_formant_peaks), the front-end the measurement feedback
                   re-pointed the agent to. Same FormantNode output shape, so the
                   downstream signatures (filter_signature_rich, etc.) are unchanged."""
    _formant_fn = (_lpc_formant_peaks if frontend == "lpc"
                   else _spectral_envelope_peaks)
    nodes: list[dict] = []
    edges: list[tuple] = []
    frames: list[dict] = []
    nid = [0]

    def add(ntype, **attrs):
        i = nid[0]
        nid[0] += 1
        nodes.append({"id": i, "type": ntype, **attrs})
        return i

    prev_frame = None
    prev_formant_ids = None
    for s, win in _voiced_frames(samples, fs):
        if len(frames) >= max_frames:
            break
        f0 = _estimate_f0(win, fs)
        formants = _formant_fn(win, fs, n_formants=n_formants)
        if not formants:
            continue
        fr = add("FrameNode", t_start=s / fs)
        # SOURCE subgraph: f0 + harmonic partials.
        src = add("SourceNode", f0=f0)
        edges.append((fr, "has_source", src))
        for k, fk in _harmonic_partials(f0, fs):
            p = add("PartialNode", k=k, freq=fk)
            edges.append((p, "harmonic_of", src))   # integer ratio relation
        # FILTER subgraph: ordered formants + spacing RATIO relations.
        formant_ids = []
        for (ffreq, fmag) in formants:
            fn = add("FormantNode", freq=ffreq, mag=fmag)
            edges.append((fr, "has_formant", fn))
            formant_ids.append((fn, ffreq))
        for i in range(len(formant_ids) - 1):
            (lo_id, lo_f) = formant_ids[i]
            (hi_id, hi_f) = formant_ids[i + 1]
            # formant_above carries the RATIO — the speaker-invariant relation:
            # vocal-tract length scales all formants ~multiplicatively, so the
            # RATIO F_{i+1}/F_i is (to first order) speaker-independent.
            edges.append((lo_id, "formant_above", hi_id,
                          {"ratio": hi_f / lo_f if lo_f > 0 else 0.0}))
        # temporal edges
        if prev_frame is not None:
            edges.append((prev_frame, "before", fr))
            if prev_formant_ids:
                for (a_id, _), (b_id, _) in zip(prev_formant_ids, formant_ids):
                    edges.append((a_id, "transition", b_id))
        prev_frame = fr
        prev_formant_ids = formant_ids
        frames.append({
            "t": s / fs, "f0": f0,
            "partials": [fk for _, fk in _harmonic_partials(f0, fs)],
            "formants": [ff for ff, _ in formants],
        })
    return {"nodes": nodes, "edges": edges, "frames": frames}


# ---------------------------------------------------------------------------
# 4. Representations for the invariance comparison.
# ---------------------------------------------------------------------------
def filter_signature(sound_graph: dict, n_formants: int = 3) -> np.ndarray:
    """The FILTER subgraph reduced to its speaker-INVARIANT relational form:
    the mean log-ratios between successive formants across frames (the
    `formant_above` ratio relations). Vocal-tract length is a multiplicative
    scale on absolute formant freqs, so it cancels in the ratios — by
    CONSTRUCTION the word's filter structure, not the speaker's tract size.
    Returns a fixed-length vector of mean log(F_{i+1}/F_i)."""
    ratios = [[] for _ in range(n_formants - 1)]
    for fr in sound_graph["frames"]:
        f = fr["formants"]
        for i in range(min(len(f) - 1, n_formants - 1)):
            if f[i] > 0 and f[i + 1] > 0:
                ratios[i].append(math.log(f[i + 1] / f[i]))
    return np.array([np.mean(r) if r else 0.0 for r in ratios], dtype=float)


def filter_signature_rich(sound_graph: dict, n_formants: int = 3,
                          n_slots: int = 6) -> np.ndarray:
    """A RICHER filter-graph signature giving the relational structure
    comparable dimensionality to the spectrum: the formant-ratio TRAJECTORY,
    resampled to n_slots time points. Each slot holds the (n_formants-1)
    log-ratios between successive formants at that point in the word. This is
    still purely the speaker-INVARIANT filter relations (ratios cancel
    vocal-tract length) — just with the temporal/relational detail the
    2-number mean threw away."""
    frames = sound_graph["frames"]
    if not frames:
        return np.zeros(n_slots * (n_formants - 1))
    per_frame = []
    for fr in frames:
        f = fr["formants"]
        row = []
        for i in range(n_formants - 1):
            if i < len(f) - 1 and f[i] > 0 and f[i + 1] > 0:
                row.append(math.log(f[i + 1] / f[i]))
            else:
                row.append(0.0)
        per_frame.append(row)
    arr = np.array(per_frame)                       # [T, n_formants-1]
    # Resample the trajectory to n_slots along time (linear interp per ratio).
    T = arr.shape[0]
    if T == 1:
        out = np.repeat(arr, n_slots, axis=0)
    else:
        xs = np.linspace(0, T - 1, n_slots)
        out = np.stack([np.interp(xs, np.arange(T), arr[:, c])
                        for c in range(arr.shape[1])], axis=1)
    return out.flatten()


def spectrum_signature(samples: np.ndarray, fs: int, n_bins: int = 24,
                       lo_hz: float = 80.0, hi_hz: float = 3800.0) -> np.ndarray:
    """The CURRENT representation: an absolute log-magnitude spectrum (the
    spectral envelope sampled in fixed Hz bins), averaged over voiced frames.
    This is what shifts with vocal-tract length — the thing CMVN/VTLN try to
    fix. Normalised to unit norm so it's a fair shape comparison."""
    acc = np.zeros(n_bins)
    cnt = 0
    edges = np.linspace(lo_hz, hi_hz, n_bins + 1)
    for _, win in _voiced_frames(samples, fs):
        mag = np.abs(np.fft.rfft(win, n=2048)) + 1e-9
        freqs = np.fft.rfftfreq(2048, 1.0 / fs)
        for b in range(n_bins):
            m = (freqs >= edges[b]) & (freqs < edges[b + 1])
            if m.any():
                acc[b] += math.log(float(np.mean(mag[m])) + 1e-9)
        cnt += 1
    if cnt == 0:
        return acc
    v = acc / cnt
    v = v - v.mean()
    nrm = np.linalg.norm(v) + 1e-9
    return v / nrm


def spectrum_signature_traj(samples: np.ndarray, fs: int, n_bins: int = 16,
                            n_slots: int = 6, lo_hz: float = 80.0,
                            hi_hz: float = 3800.0) -> np.ndarray:
    """Spectrum as a TRAJECTORY (the current-representation analogue of the
    rich filter signature): per-voiced-frame log-spectrum in fixed Hz bins,
    resampled to n_slots time points. Absolute frequency bins — the thing that
    shifts with vocal-tract length. Matches filter_signature_rich's
    dimensionality for a fair comparison."""
    rows = []
    edges = np.linspace(lo_hz, hi_hz, n_bins + 1)
    for _, win in _voiced_frames(samples, fs):
        mag = np.abs(np.fft.rfft(win, n=2048)) + 1e-9
        freqs = np.fft.rfftfreq(2048, 1.0 / fs)
        row = []
        for b in range(n_bins):
            m = (freqs >= edges[b]) & (freqs < edges[b + 1])
            row.append(math.log(float(np.mean(mag[m])) + 1e-9) if m.any()
                       else -20.0)
        rows.append(row)
    if not rows:
        return np.zeros(n_slots * n_bins)
    arr = np.array(rows)
    T = arr.shape[0]
    if T == 1:
        out = np.repeat(arr, n_slots, axis=0)
    else:
        xs = np.linspace(0, T - 1, n_slots)
        out = np.stack([np.interp(xs, np.arange(T), arr[:, c])
                        for c in range(arr.shape[1])], axis=1)
    v = out.flatten()
    v = v - v.mean()
    return v / (np.linalg.norm(v) + 1e-9)


__all__ = ["surface_schema", "build_sound_graph", "filter_signature",
           "filter_signature_rich", "spectrum_signature",
           "spectrum_signature_traj", "_lpc_formant_peaks"]
