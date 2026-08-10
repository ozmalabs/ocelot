"""allpole_spectral_envelope — iter-43: the SHARP all-pole SPECTRAL ENVELOPE front-end.

PROVENANCE — the triply-validated frontier the arc converged on:
  · the agent's order-N derivative (#1 implication, all three turns of
    docs/agent_frontier_selfdiagnosis_postiter40.md) names the FEATURE FRONT-END via
    the harvested shape parametric_allpole__from__IIR_filter ("a FEW feedback poles
    ARE the resonances, recovered by LINEAR PREDICTION rather than read off a blurry
    spectrum");
  · the iter-42 fixed gap-selector (docs/agent_loop_iteration42) PICKS this axis #1
    by measured shortfall (all-pole / levinson / lpc-formant, shortfall 0.314);
  · iter-41 (docs/agent_loop_iteration41) ruled out the alternative — cross-speaker
    CENTROID clustering is a NULL because the strong gammatone channels' per-speaker
    raw-token cloud already IS the discriminative signal; the lever is therefore NOT
    averaging the blurry feature but making the underlying FEATURE SHARPER so the
    existing raw-token discrimination resolves more.

THE BOUND this fixes: the gammatone band-means are BLURRY (the gammatone-wall) — broad
ERB-spaced filters smear the formant resonances. Every channel in the cue-graph that
reads the vocal-tract FILTER reads it through that blur. The all-pole / linear-
prediction estimate is the SHARP alternative: a few feedback poles fit by Levinson-
Durbin recover the smooth resonant envelope at FULL waveform frequency resolution,
BYPASSING the band wall (the agent's own spec note in lpc_formant_representation:
"LPC on the raw WAVEFORM frame, not the already-coarse 32-band gammatone spectrum …
recovers formants at full waveform resolution").

WHAT IS NEW vs the EXISTING LPC cue (lpc_formant_representation / stacked): the existing
cue is only the formant-RELATION — the VTL-invariant SPACING between formant positions
(it throws away everything but the gaps between a handful of pole frequencies). This
module keeps the FULL all-pole SPECTRAL ENVELOPE — the sharp resonance STRUCTURE itself
(peak heights, bandwidths, the whole 1/|A(w)| curve), the sharp analogue of the
gammatone band-means, not just the relation. That is the "richer move" the task names:
the full sharp envelope, not the spacing relation.

NO-DONKEY / NO-FIT: composed entirely from the agent's OWNED operators —
  _autocorr -> _levinson  (its own Levinson-Durbin all-pole fit, the same operators
  the landmark node's _lpc_residual_flatness and the formant-relation cue already use)
  -> evaluate the all-pole magnitude response 1/|A(w)| on a fixed log-frequency grid.
No model fit (Levinson is a closed-form recursion, not gradient descent), no trained
net, no learned weight, no tuning. The ONLY new Python is the I/O-boundary DSP that
evaluates the transfer function on the grid — the SAME category as fft_ear / cochleagram
(np.fft + fixed pooling). It is wired as ONE MORE node in the variadic Argmax-of-product
exactly like fft_ear: a fixed-length L2 descriptor -> cosine 1-NN exemplar evidence ->
softmax by its OWN median distance -> one item in the combine-all product. The
recognition decision Term is UNCHANGED.

The node is built like fft_ear (the complementary-ear template): the per-utterance
readout is the sharp envelope over a few coarse temporal windows (so it carries the
word's spectral shape AND its coarse time course), L2-normalised. fft_ear is the
freq-SHARP FFT ear (linear, all spectral detail incl. the harmonic/source fine
structure); this is the freq-sharp ALL-POLE ear (only the resonant ENVELOPE, source
removed by the all-pole fit) — a different operating point again, orthogonal by
construction to both the blurry gammatone and the harmonic-carrying FFT ear.
"""
from __future__ import annotations

import math

import numpy as np

# The agent's OWNED Levinson-Durbin all-pole fit (its own operators, reused verbatim).
from domains.lpc_formant_representation import _autocorr, _levinson


# ---------------------------------------------------------------------------
# Configuration — the SHARP all-pole envelope readout.
#
# A few coarse temporal windows over the utterance (the fft_ear template), each
# summarised by its all-pole spectral envelope on a fixed log-frequency grid. Log
# spacing matches the perceptual / VTL geometry (VTL = a multiplicative formant scaling
# = a constant shift on the log axis), the same axis every formant cue uses.
# ---------------------------------------------------------------------------

AP_NWIN = 3                 # coarse temporal windows over the utterance (as fft_ear)
AP_NBANDS = 40             # log-frequency grid points the envelope is read on
AP_LO = 150.0             # formant-range floor (Hz)
AP_HI = 3800.0            # formant-range ceiling (Hz)
AP_PRE_EMPH = 0.97        # pre-emphasis (flattens the -6 dB/oct glottal tilt; standard
                          #   LPC practice, the agent's own _lpc_roots_formants uses it)


def _ap_log_edges(nbands: int = AP_NBANDS) -> np.ndarray:
    """Log-spaced frequency grid edges over the formant range (same geometry as
    fft_ear's _fft_log_edges)."""
    return np.exp(np.linspace(math.log(AP_LO), math.log(AP_HI), nbands + 1))


def _lpc_order_for(fs: int) -> int:
    """The agent's own waveform-LPC order rule (lpc_formant_representation /
    landmark node): fs/1000 + 2 -> ~10 at 8 kHz. One pole-pair per ~1 kHz of band
    plus headroom — enough to resolve the 3-4 formants in the speech range, the
    classic linear-prediction order. NOT a tuned hyper-parameter (the agent's fixed
    spec rule)."""
    return int(fs / 1000) + 2


def allpole_envelope_window(seg: np.ndarray, fs: int, edges: np.ndarray,
                            order: int, pre_emph: float = AP_PRE_EMPH) -> np.ndarray:
    """The SHARP all-pole spectral envelope of ONE waveform segment, sampled on the
    log-frequency grid `edges` (len = len(edges)-1 bands).

    The agent's derived "all-pole model fit by LINEAR PREDICTION; evaluate 1/A(z)":
      pre-emphasise + window -> _autocorr -> _levinson (all-pole coeffs a_k, gain) ->
      evaluate the all-pole magnitude response |H(w)| = sqrt(gain)/|A(e^{jw})| at each
      grid frequency -> log-magnitude (the domain the gammatone trajectory uses).

    Pure adapter-math DSP (same category as fft_ear / cochleagram); no fit, no learned
    weight, no tuning. Returns a log-magnitude envelope vector, one value per band."""
    nbands = len(edges) - 1
    x = np.asarray(seg, dtype=np.float64)
    if x.size < order + 4 or np.allclose(x, 0.0):
        return np.full(nbands, -18.0, dtype=np.float64)
    # pre-emphasis + Hamming window (the agent's _lpc_roots_formants recipe).
    x = np.append(x[0], x[1:] - pre_emph * x[:-1])
    x = x * np.hamming(x.size)
    r = _autocorr(x, order)
    if r[0] <= 0.0:
        return np.full(nbands, -18.0, dtype=np.float64)
    a, gain = _levinson(r, order)               # A(z) = 1 - sum a_k z^-k, gain = e
    # Evaluate the all-pole transfer on each grid band's CENTRE frequency (geometric
    # centre of the log band). w = 2*pi*f/fs is the digital angular frequency.
    centres = np.sqrt(edges[:-1] * edges[1:])
    w = 2.0 * np.pi * centres / fs
    p = len(a) - 1
    k = np.arange(p + 1)
    # |A(e^{jw})| for every band centre: rows = bands, cols = coeffs.
    Z = np.exp(-1j * np.outer(w, k))            # (nbands, p+1)
    Amag = np.abs(Z @ a) + 1e-9
    env = np.sqrt(max(gain, 1e-12)) / Amag
    return np.log(np.clip(env, 1e-8, None))


def allpole_ear(x, fs: int, nbands: int = AP_NBANDS, nwin: int = AP_NWIN,
                order: int = None) -> np.ndarray:
    """The SHARP all-pole ear's per-utterance readout: for each of `nwin` equal
    temporal windows, the all-pole spectral ENVELOPE on `nbands` log-spaced frequency
    bands (the sharp resonance structure at full waveform frequency resolution —
    the complementary operating point to the BLURRY gammatone band-means and to the
    harmonic-carrying FFT ear). Returns a flat (nwin*nbands,) descriptor.

    Built like fft_ear (the agent's complementary-ear node), but the per-window
    spectrum is the all-pole ENVELOPE (source-removed sharp resonances), not the raw
    FFT magnitude. Mechanical DSP; no fit, no learned filter, no tuning."""
    x = np.asarray(x, dtype=np.float64)
    if order is None:
        order = _lpc_order_for(fs)
    try:
        from substrate_rs import _native
        return np.asarray(_native.allpole_ear(x.tolist(), int(fs), int(nbands), int(nwin), int(order)),
                          dtype=np.float64)
    except Exception:
        pass
    edges = _ap_log_edges(nbands)
    out = np.full((nwin, nbands), -18.0, dtype=np.float64)
    n = len(x)
    if n < 32:
        return out.flatten()
    bounds = np.linspace(0, n, nwin + 1).astype(int)
    for wi in range(nwin):
        lo, hi = bounds[wi], max(bounds[wi] + 1, bounds[wi + 1])
        seg = x[lo:hi]
        if seg.size < order + 4:
            continue
        out[wi] = allpole_envelope_window(seg, fs, edges, order)
    return out.flatten()


def compose_allpole_envelope(substrate, nbands: int = AP_NBANDS,
                             nwin: int = AP_NWIN) -> list:
    """Record the agent's iter-43 SHARP all-pole front-end as a Concept (feature_kind=
    allpole_spectral_envelope) carrying its provenance. Idempotent. World-adapter I/O
    (a graph note of what was composed); no decision over graph state."""
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind")
                == "allpole_spectral_envelope"}
    created = []
    name = "allpole_spectral_envelope_ear"
    if name not in existing:
        c = substrate.add_node("Concept", {
            "name": name, "feature_kind": "allpole_spectral_envelope",
            "origin": "allpole_spectral_envelope", "composed_by": "agent",
            "nbands": int(nbands), "nwin": int(nwin),
            "derived_gap": (
                "parametric_allpole__from__IIR_filter: a FEW feedback poles ARE the "
                "resonances, recovered by LINEAR PREDICTION rather than read off a "
                "blurry spectrum — the FULL sharp all-pole envelope, not just the "
                "formant-RELATION spacing"),
            "science": (
                "the vocal tract is an all-pole filter; Levinson-Durbin fits its few "
                "poles at full waveform frequency resolution, bypassing the gammatone "
                "ERB-bandwidth blur. The all-pole magnitude response 1/|A(w)| sampled "
                "on a log-frequency grid is the SHARP resonant envelope — the sharp "
                "analogue of the blurry gammatone band-means, source removed.")})
        created.append((c, name))
    return created


__all__ = ["allpole_ear", "allpole_envelope_window", "compose_allpole_envelope",
           "AP_NBANDS", "AP_NWIN", "AP_LO", "AP_HI"]
