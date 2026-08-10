"""ear_composition — the agent COMPOSES ITS OWN EAR.

The raw 128-bin linear FFT spectrum (each AcousticSign's `fft_trajectory`) is the
agent's frequency-sharp sense. A UNIFORM 32-band layout (acoustic_resolution
.enrich_sign_fft) spends resolution evenly across 0..nyquist. But the agent does not
confuse every word in every frequency region — its confusions live in specific bands
(F1/F2 for vowel pairs, the high frequencies for fricatives). An ear the AGENT
composes is a NON-uniform band layout over those 128 raw bins that the agent DESIGNS
from its OWN confusions: fine bands where its confused words actually differ in
frequency, coarse bands where they do not. It is the agent designing its own
perceptual resolution map.

Same pattern as runtime_design (the agent decides WHAT, a mechanical generator emits
HOW) and acoustic_resolution (resolution is a dial the agent owns). Here the agent
reads its Confusion nodes, measures per-raw-bin informativeness from the confused
words' own spectra, and lays out `res_out` bands by EQUAL-INFORMATION binning. The
layout is stored as a graph Concept (`ComposedEar`); the enrichment + cues are
mechanical emission over it.

How the agent derives informativeness (the exact formula):
  Per confused pair (X, Y), per raw bin k:
      fisher_k(X,Y) = |meanX_k - meanY_k| / (stdX_k + stdY_k + eps)
  where meanX_k / stdX_k are the mean / std of bin k of the per-clip mean spectra of
  word X (each clip's spectrum = its fft_trajectory averaged over the 8 frames).
  Aggregated across pairs, weighted by confusion count:
      info_k = sum_over_pairs  count(X,Y) * fisher_k(X,Y)
  info_k is the agent reading, from its OWN confusions, where in frequency it needs
  resolution. Equal-information binning then cuts a band boundary each time the
  cumulative info crosses total/res_out, giving FINE bands where info is high.
"""
from __future__ import annotations

import numpy as np

from domains.acoustic_resolution import _fft_frames

_EPS = 1e-9


# --- 1. the agent specifies its ear from its own confusions -----------------

def _per_word_spectra(substrate, pipe, test_set):
    """Ingest the test clips; for each word build the matrix of per-clip mean
    spectra (each row = one clip's fft_trajectory averaged over its 8 frames, a
    128-vector). Returns {word: np.ndarray(n_clips, n_bins)} and n_bins."""
    import scripts.fsdd_learner_world as fl
    byword: dict = {}
    n_bins = None
    for path, digit, sp, idx in test_set:
        s, fs = fl.load_wav(path)
        pipe.ingest(substrate, s)
        substrate.tick(50000)
        st = None
        for n in substrate.nodes("AudioStream"):
            st = n
        sg = fl._collect_signs_from_stream(substrate, st) if st else []
        for g in sg:
            frames = _fft_frames(substrate, g)
            if frames is None:
                continue
            spec = frames.mean(axis=0)                  # 128-vector, this clip
            if n_bins is None:
                n_bins = spec.shape[0]
            byword.setdefault(fl._DIGITS[digit], []).append(spec)
    out = {w: np.asarray(rows, dtype=float) for w, rows in byword.items()
           if len(rows) >= 2}
    return out, (n_bins or 0)


def _confusion_pairs(substrate):
    """Read Confusion nodes -> [(X, Y, count)] sorted by count desc."""
    pairs = []
    for c in substrate.nodes("Confusion"):
        a = substrate.node(c)["attrs"]
        X, Y, n = a.get("true_word"), a.get("pred_word"), int(a.get("count", 0))
        if X and Y and n > 0:
            pairs.append((X, Y, n))
    pairs.sort(key=lambda t: -t[2])
    return pairs


def informativeness_vector(spectra, pairs, n_bins):
    """The agent reads, from its OWN confusions, WHERE in frequency it needs
    resolution. For each confused pair, per raw bin k:
        fisher_k = |meanX_k - meanY_k| / (stdX_k + stdY_k + eps)
    aggregated across pairs weighted by confusion count -> info vector (n_bins).
    Returns (info, used_pairs)."""
    info = np.zeros(n_bins, dtype=float)
    used = []
    for X, Y, n in pairs:
        if X not in spectra or Y not in spectra:
            continue
        ax, ay = spectra[X], spectra[Y]
        mx, my = ax.mean(axis=0), ay.mean(axis=0)
        sx, sy = ax.std(axis=0), ay.std(axis=0)
        fisher = np.abs(mx - my) / (sx + sy + _EPS)
        info += float(n) * fisher
        used.append((X, Y, n))
    return info, used


def equal_information_layout(info, res_out):
    """Lay out res_out contiguous bands over the raw bins by EQUAL-INFORMATION
    binning: walk the bins accumulating info, cut a boundary each time the
    cumulative crosses total/res_out. FINE bands where info is high, COARSE where
    low. Returns boundaries: a list of res_out+1 bin indices [0, ..., n_bins]."""
    n_bins = len(info)
    total = float(info.sum())
    if total <= 0 or res_out <= 1:
        # no information signal — fall back to uniform.
        return list(np.linspace(0, n_bins, res_out + 1).round().astype(int))
    step = total / res_out
    boundaries = [0]
    cum = 0.0
    target = step
    for k in range(n_bins):
        cum += info[k]
        # once the running sum crosses the next target, close a band after bin k.
        while cum >= target - 1e-12 and len(boundaries) < res_out:
            boundaries.append(k + 1)
            target += step
    # ensure exactly res_out bands ending at n_bins, strictly increasing.
    while len(boundaries) < res_out:
        # pad with single-bin bands near the end if info ran out early.
        nxt = min(boundaries[-1] + 1, n_bins)
        if nxt <= boundaries[-1]:
            break
        boundaries.append(nxt)
    boundaries.append(n_bins)
    # de-duplicate / enforce monotonicity (info can be 0 over long stretches).
    fixed = [0]
    for b in boundaries[1:]:
        b = max(b, fixed[-1] + 1)
        if b >= n_bins:
            b = n_bins
        fixed.append(b)
        if b >= n_bins:
            break
    if fixed[-1] != n_bins:
        fixed.append(n_bins)
    # collapse if we overshot res_out bands
    if len(fixed) > res_out + 1:
        fixed = fixed[:res_out] + [n_bins]
    return fixed


def agent_specify_ear(sub, pipe, test_set, res_out=16):
    """The agent composes its own ear: read its Confusions, measure per-raw-bin
    informativeness from the confused words' spectra, and design a non-uniform
    res_out-band layout by equal-information binning. Stores a `ComposedEar`
    Concept node (boundaries, res_out, origin='agent') and returns the boundaries
    (list of res_out+1 bin indices)."""
    spectra, n_bins = _per_word_spectra(sub, pipe, test_set)
    if n_bins == 0:
        raise RuntimeError("no fft spectra collected — signs lack fft_trajectory")
    pairs = _confusion_pairs(sub)
    info, used = informativeness_vector(spectra, pairs, n_bins)
    boundaries = equal_information_layout(info, res_out)
    # store the layout as a graph Concept the agent owns.
    node = sub.add_node("ComposedEar", {
        "name": f"composed_ear_{res_out}",
        "boundaries": [int(b) for b in boundaries],
        "res_out": int(res_out),
        "n_bins": int(n_bins),
        "origin": "agent",
        "from_pairs": ";".join(f"{X}/{Y}:{n}" for X, Y, n in used),
        "description": ("A non-uniform FFT band layout the agent composed from its "
                        "own confusions: fine bands where confused words differ in "
                        "frequency, coarse where they do not (equal-information "
                        "binning over the 128 raw linear FFT bins)."),
    })
    sub.set_attr(node, "info_vector", [float(x) for x in info])
    return [int(b) for b in boundaries]


# --- 2. mechanical emission: enrich signs with the composed ear's bands ------

def emit_ear_enrichment(sub, signs, boundaries, sr):
    """Mechanical: for each sign write `ear_<j>` = mean of fft_trajectory bins in
    band j (over ALL frames), plus `ear_<j>_e` / `ear_<j>_l` early/late. The
    composed ear's bands. Returns count of signs enriched."""
    n_bands = len(boundaries) - 1
    enriched = 0
    for g in signs:
        frames = _fft_frames(sub, g)
        if frames is None:
            continue
        nf = frames.shape[0]
        h = max(1, nf // 2)
        windows = (("", frames), ("_e", frames[:h]), ("_l", frames[h:]))
        for tag, win in windows:
            if win.shape[0] == 0:
                continue
            bins = win.mean(axis=0)                       # n_bins energies
            for j in range(n_bands):
                lo, hi = boundaries[j], boundaries[j + 1]
                if hi <= lo:
                    val = 0.0
                else:
                    val = float(bins[lo:hi].mean())
                sub.set_attr(g, f"ear_{j}{tag}", val)
        enriched += 1
    return enriched


def ear_band_centre_hz(boundaries, j, sr):
    """Centre frequency (Hz) of composed band j: the Hz midpoint of its bin range
    over the linear 0..nyquist axis (bin k -> [k*nyq/n_bins,(k+1)*nyq/n_bins))."""
    n_bins = boundaries[-1]
    nyq = sr / 2.0
    lo, hi = boundaries[j], boundaries[j + 1]
    lo_hz = lo * nyq / n_bins
    hi_hz = hi * nyq / n_bins
    return 0.5 * (lo_hz + hi_hz)


def ear_band_edges_hz(boundaries, j, sr):
    """(lo_hz, hi_hz) of composed band j."""
    n_bins = boundaries[-1]
    nyq = sr / 2.0
    return (boundaries[j] * nyq / n_bins, boundaries[j + 1] * nyq / n_bins)


# --- 3. the agent's cues over its OWN composed ear ---------------------------

def _ear(j, tag=""):
    return {"type": "Attr", "node": {"type": "Var", "name": "s"},
            "key": f"ear_{j}{tag}"}


def compose_ear_cues(boundaries, sr):
    """Return Term-trees over the composed `ear_<j>` attrs:
      ear_peak : ArgMax over all ear_<j> — the dominant band of the agent's
                 designed layout (where its energy peaks in its own resolution map).
      ear_tilt : (sum of high bands) - (sum of low bands) — the spectral tilt of
                 the composed ear.
      ear_f2_peak : ArgMax over the bands whose centre falls in the F2 region
                 (~900-2500 Hz) — the formant cue, but read off the agent's OWN
                 fine bands rather than the uniform layout.
    Returns {cue_name: term_dict}."""
    n_bands = len(boundaries) - 1
    half = max(1, n_bands // 2)
    ear_peak = {"type": "ArgMax", "items": [_ear(j) for j in range(n_bands)]}
    high = {"type": "Plus", "items": [_ear(j) for j in range(half, n_bands)]}
    low = {"type": "Plus", "items": [_ear(j) for j in range(half)]}
    ear_tilt = {"type": "Minus", "a": high, "b": low}
    # F2-region peak over the composed bands.
    f2 = [j for j in range(n_bands)
          if 900.0 <= ear_band_centre_hz(boundaries, j, sr) < 2500.0]
    if len(f2) >= 1:
        ear_f2_peak = {"type": "ArgMax", "items": [_ear(j) for j in f2]}
    else:
        ear_f2_peak = {"type": "Lit", "value": 0.0}
    return {"ear_peak": ear_peak, "ear_tilt": ear_tilt, "ear_f2_peak": ear_f2_peak}


__all__ = ["agent_specify_ear", "emit_ear_enrichment", "compose_ear_cues",
           "informativeness_vector", "equal_information_layout",
           "ear_band_centre_hz", "ear_band_edges_hz"]
