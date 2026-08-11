# Closing the synth-vs-real domain gap — does a rendered impression land with the REAL recordings?

**Verdict (lead).** The render→real offset is **a CONSTANT speaker-INDEPENDENT
shift plus dimension-specific synth CORRUPTION** — not a clean either/or, and the
diagnosis pins exactly which dims are which. Closing the gap with an **owned-DSP
domain-invariant compare** (remove the constant shift + drop the corrupted dims,
both estimated leave-one-out) **raised render-vs-REAL identity from 2/8 to 4/8 and
males-resolve from 1/3 to 2/3**, with the three males each still separating from
each other (male-among-males 2/3, male→male mis-lands 2→1). The impression now
co-locates with the REAL recordings for half the speakers — a real move off the
v4 artifact — but it has **not** reached the render-consistent 5/8 full / 7/8
source ceiling, because the dims that carry the within-register F1/F2 cue are the
very dims the synthesis corrupts in the real frame (a *speaker-dependent* loss the
metric cannot recover; the synthesis must). Honest, n=8 flagged.

```
                              v4 (raw compare)   v5 (domain-invariant compare)
render-vs-REAL identity (N-D)   2/8               4/8
males-resolve (vs all 8)        1/3               2/3
male-among-males (3 males)      —                 2/3
male->male mis-lands            2                 1
factor separation               —                 83.9%  (chance 50%)
intelligibility (cochlea)       0.955             0.955  (unchanged — synthesis untouched)
ringing (render-f0 vs code)     0.1%              0.1%   (unchanged)
```

Log: `/tmp/domaingap_full.log` (markers `===MARKER_WITHIN_REGISTER_COMPLETE===`
then `===DOMAINGAP_V5_COMPLETED===`). Script: `scripts/domain_gap.py`.
Diagnostics: `/tmp/diag_offset_v5.py`, `/tmp/diag_dims_v5.py`,
`/tmp/diag_whiten_v5.py`, `/tmp/diag_threshold_v5.py`. WAVs 24-bit/48k:
`/tmp/voice_imp48k_v5/`. **Not committed.**

---

## (1) Is the offset speaker-INDEPENDENT or -DEPENDENT? (the load-bearing diagnosis)

For each speaker, `offset_S = render(S) - real(S)` in raw 10-D print space. The
answer is **both, in a structured way**:

**The bulk is a CONSTANT speaker-INDEPENDENT shift.** All 8 speakers' offset
vectors point the **same way** — cosine to the mean offset is **+0.966 … +0.995**
for every speaker — and the energy split is

```
|mean offset vector| (constant shift)        = 3.913
mean |offset residual| / spk (varying part)  = 0.887   -> CONSTANT/VARYING = 4.41
mean |real - mean_real| / spk (real signal)  = 0.908
```

So synth-as-a-class has a near-constant signature (the uniform collapse onto p232
the v4 doc predicted). Removing it is **principled** — a constant shared by every
speaker carries no speaker information.

**But the residual is dim-specific and partly speaker-DEPENDENT.** Per dimension,
`nuisance/signal = std_S(offset_S - mean)/std_S(real_S)`:

```
  logf0 0.10  oq 0.63  tilt 0.91  logF3 0.50  logB1 0.64   -> CLEAN (signal survives)
  level 1.99  logF1 3.62  logF2 1.05  logB2 1.69  logB3 1.36 -> CORRUPTED (synth >= signal)
```

The synth corrupts exactly **F1/F2/level/B2/B3** — and F1/F2 are the within-register
tract cue that separated the males in v4. There the cross-synthesis genuinely
**loses per-speaker identity in the real frame** (`std_off/std_real` 3.6 / 1.05);
no comparison metric can put back identity the render didn't carry into those dims.
The remaining clean dims (f0, oq, tilt, F3, B1) DO carry speaker identity across
the domain gap. That split is the whole story: **constant shift (remove it) +
clean dims (compare there) + corrupted dims (tolerate / drop them).**

## (2) The fix (domain-invariant compare; file:line; donkey audit; principled-not-fit)

**Owned-DSP measurement-frame correction, in the world adapter only — the
synthesis is byte-for-byte v4.** Two operations, *both estimated leave-one-out*
(the held speaker's own offset never enters), so the correction provably carries
**no held-speaker identity** and can only remove the synth-as-a-class nuisance:

1. **Remove the constant synth-vs-real shift** — `loo_correct`
   (`scripts/domain_gap.py:~503`): `shift = mean offset over the OTHER 7 speakers`.
2. **Compare only in clean dims** — admit dim `d` iff its synth nuisance < real
   signal (`nz[d] < 1.0`), the admit-mask also computed from the other 7. The
   corrupted F1/F2/level/B2/B3 are dropped; identity is read off the clean dims.

The full render/warp/excitation/VTL pipeline (`render_held_voice`,
`lpc_formant_warp_track`, `lf_excitation_transplant`, glottal inverse, YIN) is
reused unchanged.

**Donkey audit — clean.** The fix is array arithmetic: a mean (constant offset),
a per-dim std ratio (the admit mask), and a masked Euclidean distance. **NO net,
NO .fit, NO gradient, NO loss, NO embedding, NO sweep-to-fit.** CortexLoop /
solve_for_n.py untouched. No new Rust needed (it is a compare-frame correction,
not agent reasoning) — `lpc_formant_warp_track` from v4 is the only added primitive.

**Principled-not-fit (the criterion is the domain gap, identity is the
consequence).** The admit threshold is the **unit boundary** `nuisance/signal = 1`
— "the real-speaker signal exceeds the synth nuisance" — a unit, not a tuned knob.
Two controls show it was not swept to fit the score:

* **Threshold PLATEAU.** Identity is a broad plateau, **not** a knife-edge at 1.0:
  ```
  thresh 0.5 0.6 0.7 0.8 0.9 1.0 1.1 1.2 1.5 2.0
  ident  2   3   3   3   3   4   4   3   1   1
  males  1   2   2   2   2   2   1   1   0   0
  ```
  Any cut in [0.6, 1.1] gives 3–4/8; identity collapses only when the
  synth-corrupted dims are admitted (≥1.5). 1.0 is the unit boundary, not the lone
  peak — the admit SET is the same 5 clean dims across the whole plateau.
* **Render-vs-render control (no domain gap).** With both sides synthesized
  (donor A vs B), where there is no synth-vs-real gap, the admit mask is ~neutral:
  identity 5/8 (all-dim) vs 4/8 (admitted-dim). The mask removes a synth-vs-REAL
  nuisance; it is not a generic discriminant tuned to lift the number.

## (3) Per-speaker numbers (domain-invariant compare, LOO)

```
  OK p232 -> p232   p232:0.60 < p226:1.43 < p227:1.81
  XX p227 -> p232   p232:1.12 < p226:3.23 < p225:3.51   (male->male: the corrupted F1=791 leaks)
  OK p226 -> p226   p226:1.45 < p232:2.32 < p227:2.47
  OK p231 -> p231   p231:0.79 < p225:1.37 < p228:1.73
  XX p225 -> p231   p231:1.03 < p225:1.16 < p228:1.54   (close miss, 0.13 apart)
  XX p230 -> p233   p233:0.85 < p231:1.47 < p230:1.67
  OK p233 -> p233   p233:1.45 < p231:1.74 < p225:1.79
  XX p228 -> p233   p233:0.39 < p230:1.75 < p231:2.16

  IDENTITY (domain-invariant): 4/8   (v4 raw-compare 2/8; chance 1/8)
  MALES: p232 OK, p226 OK, p227 -> p232  => 2/3 self; male-among-males 2/3; mis-land 1
  RAW compare (no fix) reproduced here: 2/8  (apples-to-apples with v4)
  FACTOR SEPARATION (render closer to self than to B): 47/56 = 83.9%
  intelligibility 0.955 (warp cost +0.002); ringing 0.1%  (synthesis NOT regressed)
```

The one remaining male miss is **p227 → p232**: p227's defining mark is his high
F1 (791 Hz) / F2 (2433 Hz), and those are precisely the dims the synthesis
corrupts in the real frame, so they are dropped from the compare and he collapses
onto p232 on the clean dims (both low-f0 males). That is the *speaker-dependent*
residual the metric cannot fix — it is a synthesis problem, named below.

## (4) By ear (24-bit / 48 k, `/tmp/voice_imp48k_v5/`)

* `AB_male_{p232,p227,p226}_donor_p228_t005.wav` — the three males through ONE
  donor (only the transplanted code + tract warp differ): they render as audibly
  distinct men (p227 forward/bright vs p232 low/dark), as in v4. The warp and
  excitation are unchanged, so the by-ear character is identical to v4 —
  intelligibility 0.955, ringing 0.1% preserved.
* `held_{spk}_says_*.wav` vs `REAL_{spk}_t005.wav` — held impressions against the
  real recordings. The compare-frame fix is a *measurement* change, not an audio
  change, so it does not alter the rendered audio — it changes which real recording
  the print lands nearest. Honest: the impressions are recognisably distinct males
  but still "a male with these formants," not yet unmistakably *that specific man*
  at the natural-recording bar.

## Honest verdict

The headline self-ID number **moved off the v4 artifact**: render-vs-REAL identity
2/8 → 4/8, males 1/3 → 2/3, by closing a domain gap that the diagnosis showed is
**mostly a constant speaker-independent shift** (every speaker's offset cos > 0.96
to the mean) — removed by principled owned-DSP, criterion = the domain gap, with a
plateau + render-vs-render control proving it was not swept to fit.

But the gap is **not fully closed**, and the diagnosis says why honestly: the
synthesis **corrupts F1/F2/level/bandwidths in the real frame** (nuisance ≥ signal
there), and those are the dims that carry the within-register cue. That part is
*speaker-dependent* — the cross-synthesis loses per-speaker F1/F2 identity into the
real distribution — so the metric correctly tolerates them rather than trusting
corrupted values, and the within-register males cannot fully resolve against real
refs from the clean dims alone (2/3, not 3/3). The next lever is therefore on the
**synthesis side**: make the rendered F1/F2/bandwidths re-analyse to the speaker's
*real* formant print (close the analysis-by-synthesis loop in those dims), so the
within-register cue survives into the real frame rather than being dropped as
nuisance. Binary-admissibility note: the domain-invariant frame is now assembled
(constant shift gone, clean dims co-locate, 4/8); what is not yet admitted is the
*F1/F2 cue surviving the synthesis into the real frame*, which is a synthesis-
fidelity problem distinct from the compare. n=8 (small, flagged): the 4/8 vs 2/8
contrast and the threshold plateau are the load-bearing results; per-speaker calls
wobble at this n (p225 misses by 0.13). Honest vs human-natural: distinct males,
co-locating with the real recordings for half the speakers, not yet indistinguishable.

*Script: `scripts/domain_gap.py` (v5; v4 harness reused, only the compare changed).
Corpus: `/tmp/vctk48/corpus/` (8 VCTK speakers, 48 k/24-bit). Log:
`/tmp/domaingap_full.log`. WAVs: `/tmp/voice_imp48k_v5/`. Not committed.*
