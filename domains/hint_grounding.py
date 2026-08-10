"""Ground a teacher's hint into a feature the agent COMPOSES.

When the agent asked a peer how to tell two words apart, the peer answered in the
agent's own grounded terms — WHERE to listen (the beginning) and WHAT (a hiss in the
high bands vs a low hum). Grounding is the last link of the language loop: turning
that hint into a feature the agent builds from its OWN primitives and adds to how it
tells the pair apart. The teacher's words, re-expressed as a Term-tree the agent
evaluates — the language-bootstrap step ([[ozma_language_bootstrap]]).

Peer assists (it gave WHERE+WHAT); the agent's generator emits the HOW — the same
runtime_design pattern it used for ArgMax. No number chased: success is whether the
grounded feature separates the pair its whole-word averages could not.
"""
from __future__ import annotations


def _A(res: int, i: int, win: str) -> dict:
    return {"type": "Attr", "node": {"type": "Var", "name": "s"},
            "key": f"band{res}_{i}_{win}"}


# --- the frequency-sharp SECOND EAR (linear-bin FFT formant cues) --------
# Sign attrs `fft<R>_<j>` are linear bands over 0..nyquist Hz (R contiguous
# slices). The agent reads peaks in the F1 / F2 regions to estimate formant
# frequency — the cue the log-spaced gammatone blurs. R + sample_rate are the
# sharp-FFT resolution + audio rate (defaults match the Rust ear / FSDD).
FFT_RES = 32           # fft<R>_<j> band count (acoustic_resolution._FFT_RESOLUTION)
FFT_SR = 8000.0        # FSDD sample rate; nyquist = FFT_SR/2
F1_LO_HZ, F1_HI_HZ = 200.0, 900.0     # F1 region
F2_LO_HZ, F2_HI_HZ = 900.0, 2500.0    # F2 region


def _fft_band_range(res: int, lo_hz: float, hi_hz: float,
                    sample_rate: float = FFT_SR):
    """Inclusive-exclusive [lo,hi) band indices of fft<res>_<j> whose linear
    centre frequency falls in [lo_hz, hi_hz)."""
    nyq = sample_rate / 2.0
    idx = [j for j in range(res)
           if lo_hz <= (j + 0.5) * nyq / res < hi_hz]
    if not idx:
        return 0, 0
    return idx[0], idx[-1] + 1


def _F(res: int, j: int) -> dict:
    """Whole-word sharp-FFT band j attr (fft<res>_<j>)."""
    return {"type": "Attr", "node": {"type": "Var", "name": "s"},
            "key": f"fft{res}_{j}"}


def _fft_formant(res: int, lo_hz: float, hi_hz: float,
                 sample_rate: float = FFT_SR) -> dict:
    """ArgMax over the sharp-FFT bands in [lo_hz,hi_hz) — the peak bin index =
    the formant-frequency proxy. Same ArgMax(items) form the agent designed
    (dynamics_features._formant_freq); index is relative to the region start,
    which is monotone in Hz so it works as a discriminative formant feature."""
    lo, hi = _fft_band_range(res, lo_hz, hi_hz, sample_rate)
    if hi <= lo:
        # degenerate region (shouldn't happen at FSDD rates); fall back to a
        # constant 0 so assessment just sees no separation.
        return {"type": "Lit", "value": 0.0}
    return {"type": "ArgMax", "items": [_F(res, j) for j in range(lo, hi)]}


def onset_tilt_term(res: int, win: str = "e") -> dict:
    """'Listen to the beginning: hiss in the high bands vs a low hum' = the spectral
    TILT in the EARLY window: (energy in the high bands) − (energy in the low bands).
    Positive = hiss (high-band energy dominates); negative = low hum. Composed from
    the agent's windowed-band primitives (Plus / Minus / Attr)."""
    half = max(1, res // 2)
    low = {"type": "Plus", "items": [_A(res, i, win) for i in range(half)]}
    high = {"type": "Plus", "items": [_A(res, i, win) for i in range(half, res)]}
    return {"type": "Minus", "a": high, "b": low}


def ground_onset_hint(substrate, res: int, positive_word: str,
                      negative_word: str) -> "NodeID":
    """The agent grounds the peer's hint as a Concept carrying the onset-tilt
    Term-tree: positive tilt (a hiss) → positive_word, negative (a low hum) →
    negative_word. Its own composed, taught feature."""
    c = substrate.add_node("Concept", {
        "name": f"onset_tilt_{positive_word}_v_{negative_word}",
        "feature_kind": "onset_tilt", "predicate": onset_tilt_term(res), "res": res,
        "positive_word": positive_word, "negative_word": negative_word,
        "origin": "phonology", "composed_by": "agent", "taught": 1})
    return c


def compose_from_spec(res: int, cue: str) -> dict:
    """Emit the feature Term-tree for a teacher's cue — the agent's generator turning
    a peer's WHERE+WHAT into something it composes from its own primitives. The Term
    is POSITIVE for the peer's word `a`, negative/low for `b`:
      onset_tilt   : (high − low bands) in the EARLY window  — hiss(a) vs hum(b)
      ending_nasal : (low − high bands) in the LATE window   — nasal hum at end(a)
      movement     : ArgMax(high)@late − ArgMax(high)@early  — a peak rising(a) vs steady
    """
    half = max(1, res // 2)
    if cue == "onset_tilt":
        hi = {"type": "Plus", "items": [_A(res, i, "e") for i in range(half, res)]}
        lo = {"type": "Plus", "items": [_A(res, i, "e") for i in range(half)]}
        return {"type": "Minus", "a": hi, "b": lo}
    if cue == "ending_nasal":
        hi = {"type": "Plus", "items": [_A(res, i, "l") for i in range(half, res)]}
        lo = {"type": "Plus", "items": [_A(res, i, "l") for i in range(half)]}
        return {"type": "Minus", "a": lo, "b": hi}
    if cue == "movement":
        e = {"type": "ArgMax", "items": [_A(res, i, "e") for i in range(half, res)]}
        l = {"type": "ArgMax", "items": [_A(res, i, "l") for i in range(half, res)]}
        return {"type": "Minus", "a": l, "b": e}
    # whole-word band (no window suffix) cues — the middle / overall
    def W(i):
        return {"type": "Attr", "node": {"type": "Var", "name": "s"},
                "key": f"band{res}_{i}"}
    if cue == "vowel_height":               # overall high-vs-low spectral balance
        hi = {"type": "Plus", "items": [W(i) for i in range(half, res)]}
        lo = {"type": "Plus", "items": [W(i) for i in range(half)]}
        return {"type": "Minus", "a": hi, "b": lo}
    if cue == "onset_level":                # how much energy at the beginning
        return {"type": "Plus", "items": [_A(res, i, "e") for i in range(res)]}
    if cue == "ending_level":               # how much energy at the end
        return {"type": "Plus", "items": [_A(res, i, "l") for i in range(res)]}
    # --- frequency-sharp SECOND-EAR formant cues (linear FFT bands) ------
    # These read fft<FFT_RES>_<j> attrs (NOT band<res>_<i>); they are
    # independent of the gammatone `res`, using the sharp linear ear.
    if cue == "f1_formant":                 # F1 peak bin (~200-900 Hz)
        return _fft_formant(FFT_RES, F1_LO_HZ, F1_HI_HZ)
    if cue == "f2_formant":                 # F2 peak bin (~900-2500 Hz)
        return _fft_formant(FFT_RES, F2_LO_HZ, F2_HI_HZ)
    if cue == "f2_minus_f1":                # vowel-space cue: F2 - F1
        return {"type": "Minus",
                "a": _fft_formant(FFT_RES, F2_LO_HZ, F2_HI_HZ),
                "b": _fft_formant(FFT_RES, F1_LO_HZ, F1_HI_HZ)}
    raise ValueError(f"unknown cue: {cue}")


# the hint the agent is given — the vocabulary of things to listen for. It assesses
# them itself, per pair, and keeps whichever actually separates the words.
CUE_MENU = ["onset_tilt", "ending_nasal", "movement", "vowel_height",
            "onset_level", "ending_level",
            # frequency-sharp second-ear formant cues (linear FFT bands)
            "f1_formant", "f2_formant", "f2_minus_f1"]


__all__ = ["onset_tilt_term", "ground_onset_hint", "compose_from_spec"]
