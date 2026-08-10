# synthesize_gaps ON THE AUDIO — open the hole at the speaker, read the residual

**Spec (the user):** run the gap-synthesizer's OPERATION (open a hole in Γ = subtract
the admitted/expected, READ THE RESIDUAL) one scale down on the SIGNAL: the hole is
opened at the SPEAKER (the admitted = what is CONSTANT within the utterance), the
residual is the WORD. Perception = gap-synthesis = the same operation. The
cognition-driven FIND (the fix over the failed LPC peel, `docs/order_n_peel_loso.md`):
target what is **constant-over-time** (the speaker), NOT per-frame structure (the
word). KILL if it reduces to CMVN or over-peels like LPC.

## (1) Which machinery — faithful reproduction + donkey audit

**Checked the literal machinery first.** `order_n_postulates.synthesize_gaps` /
`gap_prioritiser` operate on the POSTULATE-GRAPH: `differentiate()` takes a postulate's
structural-property text, transfers an implication-SHAPE, and the SELECTOR reads the
RESIDUAL (= the implication not yet covered = the gap). Its open-a-hole-read-residual
semantics are intrinsically text/graph over Concepts — they cannot be invoked directly
on an audio-derived numeric state.

So I **faithfully reproduced the operation on the signal**, instantiating the exact
implication-shape that already lives in the catalog —
`context_dependence_is_a_removable_function`: *"if a quantity is a smooth FUNCTION of
its known context, that context-effect can be MODELLED and SUBTRACTED — predict the
shift and remove it to recover the context-free target."* On the audio-state: the
CONTEXT/admitted = the SPEAKER (the within-utterance CONSTANT), the residual = the
WORD. Built as `domains/agent_frontend.speaker_residual_track`.

**The cognition-driven FIND (why this is not the LPC peel that failed):** the speaker
is modelled as the **within-utterance CONSISTENT subspace** of the cochleagram — the
per-utterance MEAN frame plus the top-(k−1) principal directions of the (frames×bands)
matrix (the band-space directions consistent ACROSS frames). That is *constant-over-
time*, not *per-frame predictable*. Subtract that subspace from each frame; the
residual = the per-frame deviation = the articulatory word motion. The LPC peel
whitened per-frame all-pole structure and so took the word's own vowel resonances with
the speaker; this FIND aims at the across-frame consistent structure instead.

**Donkey audit:**
- speaker-template estimate + subtraction = **owned linear algebra**: per-utterance mean
  + the utterance's OWN top-k `np.linalg.svd` + projection-subtract. No fit, no net, no
  learned weight — the SVD is the closed-form principal subspace of this utterance's own
  frames.
- **per-utterance, UNSUPERVISED, no speaker labels**; computed and applied
  per-utterance, so NO cross-utterance / train→held leakage.
- the open-a-hole-read-residual is the agent's gap operation (the implication-shape).
- recognition = the agent's GRAPH-RESIDENT `DtwTo` recognizer (`Argmin MinOver DtwTo`),
  reused unchanged from `dtw_trajectory_loso`.
- SC load + the 40-speaker split = world-adapter mechanics; LOSO ungameable; held-out
  speakers' clips NEVER banked.

`tests/test_frontend_effect_gate.py` green after the edit.

## (2) Run to completion — RAW vs CMVN vs RESIDUAL vs LPC-peel

Robust SC 40-speaker LOSO, 120 train / 40 held speakers, 20/word, seed 20240608;
chance 0.100. All four regimes recognised by the SAME `DtwTo` trajectory recognizer on
the same split (only the trajectory the speaker is/ isn't subtracted from differs).
Captured: `/tmp/synth_gaps_audio_loso.log` (ends `[MARKER]
SYNTHESIZE_GAPS_ON_AUDIO_LOSO_COMPLETE`).

| regime        | seen  | LOSO  | seen−LOSO gap | vs RAW  | vs CMVN |
|---------------|-------|-------|---------------|---------|---------|
| RAW           | 0.310 | 0.328 | −0.018        | +0.000  | −0.242  |
| **CMVN**      | 0.625 | **0.570** | +0.055    | +0.242  | +0.000  |
| RESIDUAL-k1   | 0.625 | **0.570** | +0.055    | +0.242  | **+0.000** |
| RESIDUAL-k2   | 0.565 | 0.542 | +0.022        | +0.215  | −0.027  |
| RESIDUAL-k3   | 0.440 | 0.367 | +0.073        | +0.040  | −0.202  |
| RESIDUAL-k4   | 0.330 | 0.305 | +0.025        | −0.023  | −0.265  |
| LPC-PEEL      | 0.565 | 0.482 | +0.082        | +0.155  | −0.087  |

## (3) VERDICT — PARTIAL: keeps the word, beats the LPC peel, but REDUCES TO CMVN

- **It keeps the word where the LPC peel destroyed it.** Every RESIDUAL setting beats
  RAW (best +0.242), and the best (k=1, 0.570) cleanly beats the failed LPC peel (0.482)
  — the cognition-driven FIND does NOT over-peel the way the bottom-up per-frame
  whitening did. The diagnostic ("target the constant, not the per-frame") is vindicated
  in the negative: by aiming at across-frame structure the residual retains word
  information the LPC whitening stripped.

- **But it REDUCES TO CMVN — this is the KILL condition, stated plainly.** At k=1 the
  residual op is *bit-identical* to CMVN (0.570 / 0.570 / +0.055 gap): removing the
  within-utterance MEAN frame on the variance-normalised cochleagram IS CMVN. Widening
  the hole (k≥2, subtracting the top SVD directions) does NOT separate more speaker — it
  *monotonically degrades* cross-speaker LOSO (0.570 → 0.542 → 0.367 → 0.305). The
  dominant principal directions consistent across an utterance's frames are not a clean
  speaker template; they carry the word's own sustained spectral structure (vowel
  formant bands held across the utterance), so subtracting them peels word information —
  the same failure mode as the LPC peel, just reached via the across-frame consistent
  subspace instead of the per-frame all-pole one. The gap does NOT tighten beyond CMVN
  either (k=1 gap +0.055 = CMVN's).

- **Conclusion — DEEPER: the speaker is not separable from the word by a within-
  utterance linear subtract.** The constant-LEVEL part of the speaker (per-band mean) IS
  removable and is exactly the CMVN lift already banked; the speaker structure *beyond*
  the constant level is entangled with the word's own sustained resonances and is NOT
  captured by a low-rank consistent-subspace subtract within one utterance. Separating it
  needs the full learned forward model (an explicit speaker model the loop runs and
  inverts — order-N analysis-by-synthesis), not a within-utterance linear hole. No
  rescue: the within-utterance-subtract lever for cross-speaker invariance is at CMVN,
  and that is the wall.

**Net:** the synthesize_gaps operation transfers faithfully to the signal and the
cognition-driven FIND avoids the LPC peel's over-peeling (keeps the word, beats the
peel), but it does NOT advance the cross-speaker frontier — it *reduces to the existing
CMVN 0.570 baseline*. The constant-over-time speaker is exactly the per-band mean CMVN
already removes; the rest of the speaker is not linearly separable from the word inside
one utterance. Deeper = the learned forward model.

Captured: `/tmp/synth_gaps_audio_loso.log` (end `[MARKER]
SYNTHESIZE_GAPS_ON_AUDIO_LOSO_COMPLETE`); `pgrep` verified no process remained.
Not committed.
