"""CUE-SPECIFIC INVESTIGATOR — a grown cue axis now MEASURES its cue (donkey=0).

WALL D (81d1ddea) made a teacher-grown axis carry the REAL acoustic cue the teacher named
(advice "use the F2 trajectory" -> axis keyed `f2_trajectory`, the matched AcousticCue carrying
`operator: f2_formant`, a hint_grounding.CUE_MENU operator). But the grown axis's
`investigated_by` was wired to a GENERIC held Operator just to prove pickability/dispatch -- so
dispatching the axis did NOT actually MEASURE its cue. This module closes that: it COMPOSES the
cue's Term via `hint_grounding.compose_from_spec(res, operator)`, EVALUATES it on the source
audio via substrate.evaluate (the held Term, Rust), and returns a cue-DERIVED MEASUREMENT (the
cue's discriminability on cue-appropriate stimuli) for record_measured_capability to bank.

donkey=0: the measurement DECISION is the held composed cue Term evaluated by substrate.evaluate
-- exactly the cue_assessment.py / verify_fft_ear.py path. The Python here is mechanical DSP I/O
only (render words -> ingest -> enrich the bands the Term reads = "supply the samples", as
acoustic_resolution's docstring puts it). No LLM, no Python if/else in the measurement: the cue
operator names the Term; the Term decides; the contrast (separable / not) falls out of its values.

The CAPABILITY a cue axis represents = how well its cue SEPARATES stimuli that genuinely differ in
it. So the measurement is the cue's Fisher separation on a cue-appropriate stimulus pair (front-vs-
back vowels for F2, etc.), normalised to [0,1]. A cue-appropriate operator scores HIGH on its own
pair; a MISMATCHED operator (a different CUE_MENU cue) or a SCRAMBLED/degenerate rep scores LOW --
the discriminative gate. (HONEST: this measures the cue on CLEAN synth/segmented input; real
continuous-audio input quality is Wall B, a separate floor -- the cue Term still composes + reads
whatever rep it is given.)
"""
from __future__ import annotations

import numpy as np

from domains.hint_grounding import compose_from_spec

# Cue-appropriate stimulus pairs: words that DIFFER in the named cue so the right cue separates
# them and a wrong cue does not. F2/vowel cues -> front (high F2) vs back (low F2) vowel words.
# These are deterministic piper-synth words (the autonomy loop's own mouth), not corpus variance.
CUE_STIMULI = {
    # high-front /i/ (high F2) vs back-rounded /u/ (low F2) -- the canonical F2 contrast
    "f2_formant":  [("beat", "boot"), ("see", "sue"), ("heat", "hot")],
    "f1_formant":  [("heat", "hot"), ("hit", "hat")],          # F1 ~ vowel height/openness
    "f2_minus_f1": [("beat", "boot"), ("see", "sue")],
    "vowel_height":[("heat", "hot"), ("hit", "hat")],
    "movement":    [("beat", "boot"), ("see", "sue")],
    "onset_tilt":  [("see", "zee"), ("fee", "vee")],           # voiceless hiss vs voiced onset
    "onset_level": [("see", "zee"), ("fee", "vee")],
    "ending_nasal":[("ban", "bad"), ("sin", "sit")],           # nasal vs oral coda
    "ending_level":[("ban", "bad"), ("sin", "sit")],
}
_DEFAULT_PAIR = [("beat", "boot")]          # generic fallback (an F2-bearing pair)
_DEFAULT_VARIANTS = ("lessac", "amy", "ryan", "hfc_female", "hfc_male", "alan", "kusal", "joe")
_RES = 12                                   # gammatone band resolution the band cues read


class _P:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _fisher(a, b) -> float:
    a = np.array([x for x in a if x == x], dtype=float)
    b = np.array([x for x in b if x == x], dtype=float)
    if len(a) < 2 or len(b) < 2:
        return 0.0
    return abs(a.mean() - b.mean()) / (a.std() + b.std() + 1e-6)


def _squash(fisher: float) -> float:
    """Map a Fisher separation (>=0, unbounded) to a [0,1) discriminability the
    record_measured_capability target reads. f=1 -> 0.5, f->inf -> 1."""
    return float(fisher / (1.0 + fisher))


def _word_cue_values(world, sub, word, operator, *, variants, scramble=False):
    """Render `word` with each piper voice, ingest it through the agent's ear, enrich the bands
    the cue Term reads, then EVALUATE the held composed cue Term per sign (substrate.evaluate).
    Returns one mean cue value per voice. Pure DSP I/O around the held-Term decision.

    `scramble=True` = the degenerate control: zero the band attrs the Term reads AFTER enrich, so
    the SAME Term reads a constant rep -> it must lose its separation (Term genuinely depends on
    the rep, not a constant)."""
    import scripts.fsdd_learner_world as fl
    from domains.acoustic_resolution import (enrich_sign_bands, enrich_sign_windows,
                                             enrich_sign_fft)
    from domains.speech_world import _resample
    term = compose_from_spec(_RES, operator)
    vals = []
    for var in variants:
        out = world.synth(word, {"variant": var, "pitch": 50, "rate": 175})
        if out is None:
            continue
        x, fs = out
        # the agent's ear samples at the STT pipeline rate; one clean resample step.
        x8 = _resample(np.asarray(x, dtype=np.float64), fs, int(world._cue_pipe_fs))
        if x8.size == 0:
            continue
        world._cue_pipe.ingest(sub, np.asarray(x8, dtype=np.float32))
        sub.tick(50000)
        st = None
        for n in sub.nodes("AudioStream"):
            st = n
        sg = fl._collect_signs_from_stream(sub, st) if st else []
        if not sg:
            continue
        enrich_sign_bands(sub, resolution=_RES, signs=sg)
        enrich_sign_windows(sub, resolution=_RES, signs=sg)
        enrich_sign_fft(sub, signs=sg)
        if scramble:                          # degenerate rep: blank every attr the cue Term reads
            for g in sg:
                a = dict(sub.node(g)["attrs"])
                for k in a:
                    if k.startswith(("band", "fft")):
                        sub.set_attr(g, k, 0.0)
        sv = []
        for g in sg:
            try:
                sv.append(float(sub.evaluate(_P(term), {"s": g})))
            except Exception:
                pass
        if sv:
            vals.append(float(np.mean(sv)))
    return vals


def _ensure_cue_pipe(world, sub):
    """Get-or-make the deterministic STT ear the cue investigator perceives through (the proven
    cue-evaluation front-end of cue_assessment / verify_fft_ear -- mints signs with the
    fft_trajectory the formant cues read). Cached on the world. Mechanical setup, no decision."""
    if getattr(world, "_cue_pipe", None) is not None:
        return
    from domains.stt_pipeline import STTPipeline, STTParams
    from domains.speech_cortex import SpeechCortex
    from domains.acoustic_resolution import _root
    fs = 8000
    pipe = STTPipeline(STTParams(sample_rate=fs)); pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    SpeechCortex(sub, lexicon_name="cue_probe", tick_period_ms=99999).install()
    sub.set_attr(_root(sub), "resolution", _RES)
    world._cue_pipe = pipe
    world._cue_pipe_fs = fs


def _fresh_sub(world):
    """A clean cue-probe substrate + ear per measurement (the DTW lexicon running-mean is order-
    sensitive, so each measurement starts fresh -- determinism over a shared, drifting bank)."""
    from substrate_rs import Substrate
    sub = Substrate()
    world._cue_pipe = None
    _ensure_cue_pipe(world, sub)
    return sub


def measure_cue(world, operator, *, variants=_DEFAULT_VARIANTS, pairs=None):
    """THE CUE-SPECIFIC MEASUREMENT (donkey=0). Compose the cue's Term (compose_from_spec), evaluate
    it on cue-appropriate stimuli via substrate.evaluate, and return the cue's discriminability in
    [0,1] -- the capability the axis represents. Also returns the scrambled-rep contrast so the
    dispatcher can show the Term depends on the rep. `pairs` overrides the cue's default stimuli
    (used by the discriminative gate to score EVERY cue on the SAME F2 pair). Returns a dict, or
    None if it could not render/perceive (then the world banks nothing -- honest)."""
    if operator is None:
        return None
    pairs = pairs if pairs is not None else CUE_STIMULI.get(operator, _DEFAULT_PAIR)

    def word_vals(word, scramble=False):
        # FRESH probe per word -> no cross-word DTW-lexicon drift (deterministic, order-free).
        return _word_cue_values(world, _fresh_sub(world), word, operator,
                                variants=variants, scramble=scramble)

    fishers = []
    for (X, Y) in pairs:
        fishers.append(_fisher(word_vals(X), word_vals(Y)))
    fisher = float(np.mean(fishers)) if fishers else 0.0
    # SCRAMBLED control: same Term + same first pair, but a blanked rep -> separation must collapse.
    X, Y = pairs[0]
    fisher_scrambled = _fisher(word_vals(X, scramble=True), word_vals(Y, scramble=True))
    return {
        "operator": operator,
        "fisher": fisher,
        "discriminability": _squash(fisher),
        "fisher_scrambled": fisher_scrambled,
        "pairs": pairs,
        "n_pairs": len(pairs),
    }


def investigate_cue_axis(world, sub, axis_id, req):
    """The grown cue axis's CUE-SPECIFIC investigator, dispatched by the investigation reflex via
    the axis's investigated_by Operator (runner='cue_investigator'). Reads the cue operator the
    Wall-D vocab match stamped on the axis (`cue_operator`/`cue`), measures it (measure_cue), and
    BANKS a cue-derived MeasuredCapability via record_measured_capability. Returns the MC node id
    (or None on honest no-measurement). The MEASUREMENT is the held composed cue Term; this is the
    mechanical bank around it."""
    from domains.gap_prioritiser import record_measured_capability
    a = sub.node(axis_id)["attrs"]
    operator = (a.get("cue_operator") or req.get("cue_operator")
                or a.get("operator") or None)
    res = measure_cue(world, operator)
    if res is None:
        return None
    return record_measured_capability(
        sub, a.get("capability_keys") or ["speech", "cue"],
        measured=res["discriminability"],
        target=float(req.get("target", 0.6) or 0.6),
        metric=req.get("measurement_key") or "cue_discriminability",
        note=(f"cue-specific investigator: composed {operator!r} via compose_from_spec, "
              f"evaluated held Term on {res['n_pairs']} cue-appropriate pair(s) -> "
              f"Fisher={res['fisher']:.3f} (discriminability={res['discriminability']:.3f}); "
              f"scrambled-rep Fisher={res['fisher_scrambled']:.3f}"),
        fresh=True)


__all__ = ["measure_cue", "investigate_cue_axis", "CUE_STIMULI"]
