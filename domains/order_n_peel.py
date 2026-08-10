"""order_n_peel — the ORDER-N FIND-PROCESS-SUBTRACT loop (iterated predictive peeling).

The user's spec: "order n find signal in noise, process and subtract." Each pass of
the loop strips the next-most-PREDICTABLE layer of the waveform:

    for pass in 1..n:
        FIND    = the strongest / most-predictable structure in the current residual
        PROCESS = an ADAPTIVE predictor that forms the EXPECTED signal — minimises the
                  residual ON THIS signal (linear prediction; NOT a static synth, which
                  the physics-model/iter-40 gap proved subtracts to noise)
        SUBTRACT= residual = current - expected

The PROCESS step is LINEAR PREDICTION — the agent's OWNED primitive (the SAME
autocorrelation + Levinson-Durbin recursion the LPC formant representation derived
and uses, domains.lpc_formant_representation._autocorr / _levinson). An order-p linear
predictor predicts each sample x[t] from the previous p samples as the
least-squares-optimal linear combination (the all-pole inverse filter A(z) applied to
x); the residual e[t] = x[t] - x_hat[t] is x passed through A(z) — exactly "subtract
the predicted waveform". This is adaptive (the coefficients minimise the residual
energy on THIS frame's autocorrelation), NOT a fixed synth.

THE PEEL ORDER (why iterating peels the speaker). Each LPC pass whitens the part of
the spectrum the current predictor can model:

  pass 1  — a SHORT-order predictor (p≈2-4) captures the slowest / strongest spectral
            tilt + the dominant resonance: the gross vocal-tract CARRIER (the spectral
            envelope shared across the utterance). Its residual is the source +
            finer structure.
  pass 2  — a LONGER-order predictor (p≈8-12) on that residual captures the remaining
            all-pole resonance structure — the full formant envelope, the bulk of the
            SPEAKER's vocal-tract signature (constant within the utterance, so
            predictable). Its residual is the glottal source + the word's fast moves.
  pass 3  — a still-longer predictor (p≈16-24) on that residual reaches the PITCH-period
            (glottal source) structure — the F0 / voice-quality, the rest of the
            speaker. Its residual is what is NOT predictable from the signal's own past
            at any of these scales: the fast, word-specific articulatory excitation.

The SPEAKER (vocal-tract envelope + glottal source) is roughly CONSTANT within an
utterance => maximally predictable => it lands in the PEEL. The WORD is the fast
articulatory MOTION => least predictable => it survives in the RESIDUAL. So
recognising on the residual after n passes should LOSE the speaker and KEEP the word —
cross-speaker invariance as a BYPRODUCT, not a bolted-on normaliser.

DONKEY BOUNDARY. The peel = the agent's order-N operator (iterate FIND-PROCESS-
SUBTRACT n times) over its OWNED linear-prediction primitive (autocorrelation +
Levinson-Durbin = owned linear algebra, no fit, no net, no learned weight — the
coefficients are the closed-form least-squares solution to THIS frame's normal
equations). The frame-by-frame windowing + overlap-add is mechanical I/O DSP, the
SAME category as the gammatone / np.fft front end. Recognition stays the agent's
(DtwTo trajectory / blind_guess). No tuning to a target: the per-pass orders are read
off the peel-order science above (short->long->longer), the n is swept {1,2,3} and
reported honestly.
"""
from __future__ import annotations

import numpy as np

from domains.lpc_formant_representation import _autocorr, _levinson


# ---------------------------------------------------------------------------
# One FIND-PROCESS-SUBTRACT pass = the LPC residual (the prediction-error signal).
#
# Framed analysis: per analysis frame, fit the order-p all-pole predictor to the
# frame's own autocorrelation (the ADAPTIVE predictor — least-squares-optimal on THIS
# frame), apply the inverse filter A(z) to get the residual e[t] = x[t] - x_hat[t],
# and overlap-add the per-frame residuals back to a full-length residual signal. The
# inverse filter A(z) = 1 - sum_k a_k z^-k IS "predict each sample from the previous p,
# subtract"; the agent's _levinson returns a[0]=1, a[1..p] = -(predictor coeffs) in the
# convention A(z), so e = conv(a, x) directly (no sign juggling).
# ---------------------------------------------------------------------------

def _frame_lpc_residual(frame: np.ndarray, order: int, pre_emph: float) -> np.ndarray:
    """The order-p LPC prediction-error (residual) of ONE frame. e = A(z) x, where
    A(z) is the all-pole inverse filter fit to the frame by the agent's owned
    autocorrelation + Levinson-Durbin. Owned linear algebra; no fit beyond the closed-
    form normal-equations solution."""
    x = np.asarray(frame, dtype=np.float64)
    if len(x) < order + 2:
        return np.zeros_like(x)
    if pre_emph:
        x = np.append(x[0], x[1:] - pre_emph * x[:-1])
    r = _autocorr(x, order)
    if r[0] <= 0.0:
        return np.zeros_like(x)
    a, _ = _levinson(r, order)            # a = [1, -a_1, ..., -a_p] (A(z) coeffs)
    # residual e[t] = sum_k a[k] x[t-k] = x filtered by A(z) = x - prediction.
    e = np.convolve(x, a, mode="full")[: len(x)]
    return e


def lpc_residual(x: np.ndarray, fs: float, order: int,
                 frame_ms: float = 25.0, hop_ms: float = 10.0,
                 pre_emph: float = 0.97) -> np.ndarray:
    """ONE peel pass over the whole signal: framed order-p LPC residual, overlap-added
    (Hann window) back to a full-length residual waveform. This is the
    FIND(dominant all-pole structure)-PROCESS(adaptive linear predictor)-SUBTRACT
    (residual = x - prediction) pass.

    Owned linear algebra (autocorrelation + Levinson-Durbin); the windowing +
    overlap-add is mechanical I/O DSP (same category as the gammatone front end)."""
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    if n < order + 4:
        return x.copy()
    win = max(int(frame_ms * fs / 1000.0), order + 4)
    hop = max(1, int(hop_ms * fs / 1000.0))
    w = np.hanning(win)
    out = np.zeros(n, dtype=np.float64)
    wsum = np.zeros(n, dtype=np.float64)
    for a0 in range(0, max(1, n - win + 1), hop):
        seg = x[a0:a0 + win]
        if len(seg) < order + 2:
            break
        e = _frame_lpc_residual(seg, order, pre_emph)
        L = len(e)
        out[a0:a0 + L] += e * w[:L]
        wsum[a0:a0 + L] += w[:L]
    # also cover the tail (last partial frame) if the hop loop missed it.
    if wsum[-1] == 0.0 and n > win:
        seg = x[n - win:]
        e = _frame_lpc_residual(seg, order, pre_emph)
        out[n - win:] += e * w[: len(e)]
        wsum[n - win:] += w[: len(e)]
    nz = wsum > 1e-9
    out[nz] /= wsum[nz]
    return out


# the per-pass predictor ORDERS, read off the peel-order science (short->long->longer:
# carrier -> vocal-tract envelope/speaker -> pitch-period/glottal source). NOT tuned to
# a target; a fixed schedule the n-sweep walks down.
_PASS_ORDERS = (2, 10, 20)


def peel(x, fs, n_passes: int, orders=None, pre_emph: float = 0.97) -> np.ndarray:
    """The ORDER-N FIND-PROCESS-SUBTRACT loop: iterate the LPC-residual pass n times,
    each pass with a progressively LONGER-order predictor (peeling progressively
    slower / longer-context structure — carrier, then the speaker's vocal-tract
    envelope, then the pitch-period source). Returns the residual waveform after n
    passes — the part of the signal NOT predictable from its own past at any peeled
    scale (the fast, word-specific articulatory excitation, speaker peeled away).

    n_passes=0 returns the raw signal (the RAW baseline). The agent's order-N operator
    (iterate the owned predict-subtract n times) over owned linear algebra."""
    x = np.asarray(x, dtype=np.float64)
    if n_passes <= 0:
        return x.copy()
    ords = list(orders) if orders is not None else list(_PASS_ORDERS)
    res = x
    for p in range(n_passes):
        order = ords[min(p, len(ords) - 1)]
        # pre-emphasis only on the FIRST pass (the raw signal's spectral tilt); the
        # residual of a later pass is already roughly white, so re-pre-emphasising it
        # would just amplify the highest-frequency noise.
        pe = pre_emph if p == 0 else 0.0
        res = lpc_residual(res, fs, order, pre_emph=pe)
        # renormalise the residual to unit RMS so each pass operates at a consistent
        # level (the autocorrelation predictor is scale-equivariant; this only keeps
        # downstream front-end level sane). Mechanical I/O.
        rms = float(np.sqrt(np.mean(res ** 2)))
        if rms > 1e-9:
            res = res / rms
    return res


__all__ = ["lpc_residual", "peel", "_frame_lpc_residual", "_PASS_ORDERS"]
