"""order_n_frequency_frame — the agent's OWN order-N operator aimed down the
FREQUENCY axis of the cochleagram, as a soft-admissibility frame.

THE MOVE (ozma_every_frame_is_order_n_over_a_dimension): every frame in the
multi-frame weighted-admissibility collapse is the agent's ONE order-N operator
(domains/order_n_concepts.nth_order_terms = recursive Minus) pointed at a
different axis. The running syllable build aims it down TIME-energy; HERE we aim
the SAME operator down FREQUENCY:

  · order-1 over frequency = spectral TILT
  · order-2 over frequency = spectral CURVATURE — a formant PEAK is a local
    NEGATIVE-curvature extreme (the band sits above its neighbours, so the second
    difference there is strongly negative). The order-2-freq pattern IS the
    vowel/place (formant) structure of the frame.

DONKEY BOUNDARY (audited):
  · The order-N differencing is the AGENT'S OWN operator: domains/order_n_concepts
    .nth_order_terms composes the order-N finite-difference Term-tree (recursive
    Minus over the band-axis samples); each difference Term is EVALUATED NATIVELY
    by the substrate (substrate.evaluate), NOT by numpy. This is the identical
    donkey-clean pattern domains/agent_frontend._vtl_formant_dynamic uses for
    order-N-over-TIME — same operator, frequency axis instead of time.
  · The cochleagram is the agent's owned front-end (domains/filter_settings
    .cochleagram, gammatone). The 1-NN DTW + soft-exclude collapse are v1/v2 owned
    ops. NO net, NO fit, NO gradient, NO sweep-and-keep.

CAVEAT (the gammatone wall, honest up front): the cochleagram bands are coarse
(~32 log-bands, ERB-spaced); the order-2-freq curvature peak is therefore a
QUANTISED formant estimate (one of ~32 band positions), the same blur the
_vtl_formant cue suffers. Whether the curvature pattern is a reliable
cross-speaker invariant — or merely re-describes the raw band energy the acoustic
frame already reads — is exactly what the harness measures.
"""
from __future__ import annotations

import numpy as np

from domains.filter_settings import cochleagram
from domains.order_n_concepts import nth_order_terms
import domains.feature_generator as FG
from substrate_rs import Substrate, Attr, Var


# A dedicated band substrate (the order-N Term-tree reads attrs b_0..b_{nb-1}).
_SUB = None
_SIGN = None


def _band_substrate():
    global _SUB, _SIGN
    if _SUB is None:
        _SUB = Substrate()
        _SIGN = _SUB.add_node("BandFrame", {"probe": 1.0})
    return _SUB, _SIGN


def _order_n_freq_terms(nb: int, order: int):
    """The agent's OWN order-N finite-difference Term-trees down the FREQUENCY axis.
    Samples are the per-BAND attrs b_0..b_{nb-1} (the frequency dimension); the
    differences are composed by domains.order_n_concepts.nth_order_terms (recursive
    Minus) — the agent's operator. Returns a list of evaluatable _Pred Terms (the
    order-N curvature at each band position), length nb-order."""
    sv = Var("s")
    samples = [Attr(sv, f"b_{j}") for j in range(nb)]
    return [FG._Pred(d.to_dict()) for d in nth_order_terms(samples, order)]


def order_n_freq_repr(x, fs, order: int = 2, env_cut: float = 30.0,
                      dur_cut: float = 50.0, n_frames: int = 24,
                      log: bool = True) -> np.ndarray:
    """The order-N-over-FREQUENCY representation of clip x.

    1. cochleagram (frames x bands), the agent's gammatone front-end (a SHARP-FREQ
       setting — cleaner per-frame spectrum, the right tradeoff for reading spectral
       curvature; the uncertainty principle).
    2. for EACH time frame, apply the agent's order-N operator DOWN THE BAND AXIS
       (recursive Minus, evaluated natively): order-2 = spectral curvature whose
       negative extrema are the formant peaks.
    Returns (n_frames x (nb-order)) — the per-frame order-N-freq (curvature) pattern,
    ready for DTW 1-NN exactly like the acoustic formant trajectory.

    The differencing runs in the SUBSTRATE (the agent's Term-tree), not numpy."""
    M = cochleagram(np.asarray(x, dtype=np.float64), fs, env_cut=env_cut,
                    dur_cut=dur_cut, n_frames=n_frames)
    if M.shape[0] == 0:
        return np.zeros((0, 0), dtype=np.float64)
    if log:
        M = np.log(np.clip(M, 1e-6, None))                # log-energy: a peak ratio is a diff
    nb = M.shape[1]
    diff_terms = _order_n_freq_terms(nb, order)
    sub, sign = _band_substrate()
    rows = []
    for r in range(M.shape[0]):
        for j in range(nb):
            sub.set_attr(sign, f"b_{j}", float(M[r, j]))
        vals = []
        for dt in diff_terms:
            try:
                v = sub.evaluate(dt, {"s": sign})
                vals.append(float(v) if isinstance(v, (int, float)) else 0.0)
            except Exception:
                vals.append(0.0)
        rows.append(vals)
    return np.asarray(rows, dtype=np.float64)             # frames x (nb-order)


def donkey_audit() -> dict:
    """Confirm the order-N differencing is the agent's OWN operator evaluated
    natively (NOT a reinvented numpy extractor): build the order-2-freq Term over a
    band curve with a known peak, evaluate via the substrate, and check it matches
    the finite-difference recurrence (the negative-curvature extreme locates the
    peak). Returns the evidence dict."""
    band = [1.0, 3.0, 6.0, 5.0, 2.0, 1.0]                 # peak at index 2
    sub, sign = _band_substrate()
    terms = _order_n_freq_terms(len(band), 2)
    for j, v in enumerate(band):
        sub.set_attr(sign, f"b_{j}", float(v))
    native = [float(sub.evaluate(t, {"s": sign})) for t in terms]
    ref = list(np.diff(band, 2))
    peak_band = int(np.argmin(native)) + 1                # +1: order-2 index -> centre band
    return {
        "operator": "domains.order_n_concepts.nth_order_terms (recursive Minus)",
        "evaluated_by": "substrate.evaluate (native, not numpy)",
        "native_curvature": native,
        "numpy_recurrence": [float(v) for v in ref],
        "match": bool(np.allclose(native, ref, atol=1e-9)),
        "peak_band_from_neg_curvature": peak_band,
        "true_peak_band": int(np.argmax(band)),
    }


__all__ = ["order_n_freq_repr", "donkey_audit", "_order_n_freq_terms"]
