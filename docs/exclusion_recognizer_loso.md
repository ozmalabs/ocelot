# Exclusion-calibrated recognizer — FLAT vs EXCLUSION combine (robust SC 40-speaker LOSO)

**Theory** (`ozma_recognition_is_exclusion`): the ear works *backwards*. The positive
question ("is it X?") is fuzzy; the negative ("is it *not*-X?") is sharp — the reliable
information lives in the NOTs. So each cue should be an **excluder**: sharp (→0) only
where it *confidently rules a candidate out*, FLAT (≈1, ABSTAIN) everywhere it can't
tell. Identity = the residue of confident exclusions. The combined-pool failure at
commit `aefe01eb` was diagnosed as miscalibration: the FLAT *positive* product forced a
positive vote even where the manner/voicing cue was uncertain ("maybe" voted as "yes"),
so a weak cue *hurt* the full 10-digit set (0.425 → 0.375, **−0.050**).

**The falsifiable prediction.** Under exclusion-calibration the manner/voicing cue
becomes *free* — it resolves seven↔zero AND costs nothing elsewhere (no more −0.050);
adding any cue can only help or abstain, never hurt.

## The change (donkey-clean — the agent's recognition decision)

`domains/many_settings_recognizer.py`: added `exclusion_likelihood_from_distances` +
`channel_likelihood_exclusion`. Same 1-NN cosine exemplar distances as before; only the
**calibration** changed, from a positive softmax peak to a one-sided exclude-or-abstain:

- For each candidate `w`, excess past the nearest candidate `e_w = (d_w − d_min) / spread`.
  `L = 1` (ABSTAIN) while `e_w ≤ k`; `L = exp(−(e_w − k))` (→0, EXCLUDE) beyond it.
  One-sided: the best match AND every consistent candidate abstain; only the confidently-far decay.
- **Separability gate**: if the candidate-distance robust spread (MAD·1.4826) is below
  `0.05·median` of the cue's own scale, the whole cue can't discriminate this contrast →
  abstains on ALL candidates (contributes ≈1 to the product). No fit, no searched temperature;
  margin `k=2` and the gate are derived from the cue's OWN distance spread.
- Combine = product of these exclusion likelihoods → a candidate survives unless some cue
  confidently excludes it; argmax over survivors. The Bayes product, exclusion-calibrated.

Verified in isolation: a discriminating cue keeps the near word (1.0) and excludes the far
ones (~0); an uninformative cue abstains on all (all 1.0); an excludes-one cue sends only
the confidently-far candidate → 0 and abstains (1.0) on the ambiguous rest.

## The run (`scripts/combined_pool_loso.py`, 120 train / 40 held-out speakers, 20/word, seed 20240609)

Both calibrations run on the **identical** extracted feature banks (apples-to-apples;
only the per-cue likelihood differs). Held-out speakers never banked; LOSO is ungameable.

### Full 10-digit cross-speaker LOSO — the combine ladder

| ladder rung | FLAT (baseline) | EXCLUSION |
|---|---|---|
| COCHLEA alone | 0.290 | 0.158 |
| + SHARP-HF | 0.425 (**+0.135**) | 0.235 (**+0.077**) |
| + MANNER-VOICE | 0.375 (**−0.050**) | 0.235 (**+0.000**) |
| + FRIC-VOICE (full pool) | 0.323 (−0.052) | 0.228 (−0.007) |

### Fricative set {three,four,five,six,seven,zero}

| | FLAT | EXCLUSION |
|---|---|---|
| cochlea+sharp | 0.567 | 0.312 |
| + manner | 0.529 (−0.037) | 0.329 (**+0.017**) |
| full pool (+fric) | 0.492 (−0.075 net) | 0.329 (+0.000) |
| seven↔zero cross-fire (+manner step) | 9 → 12 | 1 → 4 |

### Never-hurt across every added cue (both ladders)

| added cue | FLAT | EXCLUSION |
|---|---|---|
| B: +sharp | +0.135 | +0.077 |
| B: +manner | **−0.050** | **+0.000** |
| B: +fric | −0.052 | −0.007 |
| A: +manner | −0.037 | **+0.017** |
| A: +fric | −0.038 | +0.000 |
| **worst step** | **−0.052** | **−0.007** |

## Verdict — honest, not rescued

**The narrow prediction about the manner/voicing cue is CONFIRMED.** The exact harm the
exclusion frame was built to fix is gone: on the full 10-digit set the manner/voicing rung
goes from **−0.050 (FLAT, hurts) → +0.000 (EXCLUSION, free)**. On the fricative set it goes
from −0.037 → **+0.017**. Under FLAT, *4 of 5* added-cue rungs across the two ladders hurt
(worst −0.052); under EXCLUSION, the worst is −0.007. Exclusion-calibration **does** turn a
forced positive vote into exclude-or-abstain, and a weak cue almost never drags the pool.

**But the strong claims are NOT met, and two things must be said plainly:**

1. **"Adding a cue can NEVER hurt" is not literally true here.** The +fric rung is still
   −0.007 under exclusion (10-digit). It is noise-level, not the −0.05 disasters of FLAT,
   but it is negative — so the *guarantee* fails. A weak cue **can still hurt slightly**
   under exclusion-calibration. The frame is the *right shape* (it removes the large harms)
   but it is **not a strict free-lunch**: a cue that *confidently excludes the wrong
   candidate* on some clips (a bad exclusion, not a noisy positive vote) still subtracts.
   Exclusion converts "noisy yes" into "free abstain", but it does **not** protect against a
   *confident wrong NO* — and a weak cue produces those too.

2. **seven↔zero is NOT resolved** under either calibration on this robust 40-speaker pool
   (FLAT 9→12, EXCLUSION 1→4 cross-fire on the +manner step). The voicing contrast the cue
   was supposed to carry does not survive cross-speaker. (The much smaller absolute
   cross-fire counts under exclusion reflect that argmax-over-survivors fires differently,
   not that the pair is separated — recall stays poor.)

3. **Exclusion lowers the absolute ceiling.** Single-cue argmax collapses under exclusion
   (cochlea 0.290 → 0.158) because abstaining yields near-flat survivors, so argmax is
   near-random when one cue can't discriminate. Combined, EXCLUSION (0.228) sits *below*
   FLAT (0.323) on the full pool. Exclusion fixes the *marginal harm of adding a cue* but
   pays for it in *headroom*: when the pool is mostly abstentions, there is little positive
   signal left to argmax over. Exclusion is a calibration for *robustness of the combine*,
   not a lift of the underlying discrimination.

**Bottom line.** Exclusion-calibration **confirms** the specific prediction it was built to
test — the manner/voicing cue stops hurting (−0.050 → +0.000) and the large add-a-cue harms
vanish (worst −0.052 → −0.007). But it does **not** deliver a strict never-hurt guarantee (a
confident *wrong* exclusion can still cost a little), it does **not** resolve seven↔zero
cross-speaker, and it **lowers the absolute accuracy** because abstention removes positive
signal. The exclusion frame is the right *direction* (it removes the noisy-positive-vote
failure mode) but is **not sufficient** on this pool: the residual is a *perception/feature*
limit (the cues do not separate the voicing contrast across held-out speakers), which no
re-calibration of the combine can manufacture.

Residual (EXCLUSION): fricative LOSO **0.329**, full 10-digit LOSO **0.228**.

Captured run: `/tmp/exclusion_loso.log` (end marker `[MARKER] COMBINED_POOL_LOSO_COMPLETE`).
