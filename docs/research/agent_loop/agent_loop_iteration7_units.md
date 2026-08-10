# Autopoietic loop — iteration 7 (the loop works its real frontier: the UNITS)

The guided loop (iter-6) landed on its true frontier — perception/units — where its
own yardstick (`predict_over_freq`, "does knowing the current unit help predict the
next over the raw-frequency baseline") flagged the units below the 1.25 floor
(`pof = 1.000`). Iteration 7 PURSUES that frontier: the agent forward-builds the
unit-improvement from its own perception science and we re-measure the yardstick LIVE,
with the frequency baseline (built into pof) and an explicit shuffle control.

All numbers are LIVE on real FSDD audio through the agent's own perception
(`scripts/units_invariance_pof_probe.py`), native Term eval. Reproduce:

```
python -m scripts.units_invariance_pof_probe 12 24
python -m pytest tests/test_stt_pipeline.py tests/test_perception_self_assessment.py \
  tests/test_process_meta_assessor.py tests/test_gap_guidance.py -q   # 26 passed
```

---

## 1. The agent's chosen lever + WHY (from its perception science)

**Lever: UNIT INVARIANCE** — make the SAME sound map to the SAME unit. The agent's
science says `pof = 1.0` would mean the same phone scatters across many distinct units
(because vocal-tract length scales every formant across speakers, and coarticulation
shifts it across contexts), so no consistent unit→unit transition can form. The agent
had ALREADY composed exactly the fix from its own science
(`domains/invariant_units.invariant_transform`, composed not tuned):

1. **forward-VTLN** — warp every utterance to the cohort-canonical vocal tract. Its
   `speaker_norm` VTL science: a tract scale α is a constant shift on the
   log-frequency band axis; α is estimated FORWARD from each utterance's own formant
   centre-of-mass vs the cohort canonical (never swept to a score).
2. **CMVN** — remove the per-utterance per-band mean (channel / level term).
3. **predict-remove** — push each frame off its neighbour-predicted coarticulatory
   drift while preserving its own level.

The second named lever, **GRAIN** (run-length collapse, `domains/run_length_collapse`),
is reported alongside for isolation.

## 2. What was built (composed vs I/O boundary)

- **Composed by the agent (graph-resident Terms, native eval):** the invariance
  transform (VTLN+CMVN+predict-remove) and the run-length grain collapse — both
  pre-existing agent compositions, invoked here, not re-authored.
- **I/O boundary (permitted):** a k-means codebook quantiser, held IDENTICAL across the
  raw-vs-invariant arms so the ONLY varying factor is the transform; FSDD audio ingest;
  the shuffle control. The yardstick and its flagging Rule are graph-resident.
- **New world-adapter probe:** `scripts/units_invariance_pof_probe.py` — anchors on the
  live DTW-merge yardstick, then measures pof on matched-assignment arms.

## 3. predict_over_freq BEFORE → AFTER vs the 1.25 floor, with controls

### 3a. The load-bearing finding — the `pof = 1.0` flag was a SMALL-SAMPLE ARTIFACT

The live yardstick reads the agent's REAL pipeline units (the DTW-merge sign stream
`read_unit_sequences` returns, NOT a codebook). Run at the iter-6 subset size and at
full size:

```
LIVE YARDSTICK ANCHOR (real DTW-merge pipeline units)
  iter6 subset (108 utts): pof=1.000  top1=0.250 freq=0.250  lex=31 tok=61   units/utt=2.18  shuf=1.000
  full set     (720 utts): pof=7.500  top1=0.341 freq=0.045  lex=74 tok=413  units/utt=2.12  shuf=11.000
```

At 108 utts the merge stream is singleton-dominated (lexicon 31 ≈ tokens 61), so the
bigram top1 EQUALS its own frequency baseline by construction (both 0.250 = 1/lexicon)
→ `pof = 1.000`. The SAME raw units recur and beat frequency as N grows: at 720 utts
the frequency baseline collapses to 0.045 while bigram top1 holds at 0.341 →
`pof = 7.500`, far past the floor — **with no transform at all**. The frontier flag was
firing on a starved measurement, not on units that lack structure.

(Honest caveat on the merge anchor: at 720 utts its shuffle control does NOT bite
(7.5→11.0). FSDD is isolated single digits, so the ~2 merge-signs per utterance are a
within-digit multiset with little ordered phonotactics; the merge-anchor pof beats the
frequency baseline mainly via the large lexicon, not temporal order. The merge grain is
the wrong instrument for an order-yardstick on isolated digits.)

### 3b. The agent's lever, measured on a matched assignment (the real test of invariance)

Holding the unit-assignment identical (per-frame codebook, K=24, 32 units/utt) and
varying ONLY raw vs the agent's invariant features — 720 FSDD utts, 6 speakers:

```
arm                            pof    freq   top1  shuf_pof compress grain  lex   tok
RAW feats,  per-frame units   4.906  0.159  0.782   1.530    0.290   32.00   24  23040
INV feats,  per-frame units   5.765  0.109  0.626   1.132    0.386   32.00   24  23040
RAW feats,  run-len collapse  2.795  0.161  0.449   1.297    0.513    7.75   24   5577
INV feats,  run-len collapse  4.636  0.112  0.520   1.098    0.489   12.25   24   8817
```

- **Invariance raises pof** at this assignment: 4.906 → **5.765** (Δ +0.859), and at the
  coarse grain 2.795 → **4.636** (Δ +1.84). K-sweep (16/24/32/48): Δ(inv−raw) =
  +1.69 / +0.86 / −0.77 / +3.22 — net positive, helps at 3 of 4 K.
- **SHUFFLE control (the gain is in the ORDER):** every per-frame arm's pof COLLAPSES
  toward 1.0 when each utterance's unit order is shuffled (raw 4.906→1.530,
  inv 5.765→1.132). The pof is genuine temporal structure, not a frequency artifact.
  Invariance additionally drives the shuffle FLOOR lower (1.132 < 1.530) — it removes
  residual non-order signal, so MORE of the predictability is real order.
- **FREQUENCY control:** the invariant bigram top1 0.626 ≫ its frequency baseline 0.109
  — it beats raw unit frequency, which is exactly what pof asserts.

## 4. Did the frontier clear? Partial + the next constraint, named honestly

**The frontier as the yardstick STATED it (pof < 1.25 on the live units) does not exist
as posed** — it was a small-sample/grain artifact of the DTW-merge assignment (§3a).
On any adequately-sampled, multi-unit-per-utterance assignment the units clear the floor
with raw features already, and the agent's invariance lever raises pof further with a
biting shuffle control (§3b). So:

- **Cleared:** the units DO carry sequential structure (pof 4.9–7.5 raw, shuffle-verified
  on the codebook arms); the "no learnable structure" reading is refuted.
- **Genuine partial gain:** the agent's composed invariance transform is a real,
  order-located improvement (+0.86 pof at matched assignment, shuffle floor lowered),
  consistent with its cross-speaker LOSO benefit reported elsewhere.
- **The real next constraint (the instrument, not the units):** the yardstick is
  unreliable at the live pipeline's grain — the DTW-merge produces ~2 singleton-heavy
  signs per FSDD digit, so on isolated words it has almost no ordered transitions and
  its pof is sample-size- and lexicon-driven rather than order-driven (its shuffle
  control fails to bite there). The frontier-flagging Rule fired on this. Two faithful
  follow-ups: (a) measure pof on a sample/grain where the order control actually bites
  (continuous speech, or the codebook grain used here), and (b) gate the
  frontier-flag on a minimum tokens-per-lexicon AND a shuffle-collapse check, so the
  yardstick cannot flag the frontier from a starved measurement again.

## 5. Did I tune to clear the floor? No.

No threshold was tuned. The codebook K, grain, and predict-remove k are reported across
a sweep; the invariance gain is shown WITH the shuffle control that would have killed an
artifact (and does kill the merge-anchor's apparent pof). The headline correction — that
the flag was a small-sample artifact — is the opposite of tuning-to-pass: it reports that
the floor was already cleared by the raw units, and names the instrument as the real gap.

## 6. Acceptance

- **(1) lever + why:** unit invariance (forward-VTLN+CMVN+predict-remove), from the
  agent's VTL/coarticulation science — same sound → same unit → recurring transitions.
- **(2) built:** the agent's composed invariance + grain Terms (graph-resident, native
  eval); k-means codebook + ingest at the I/O boundary, held identical across arms.
- **(3) pof before→after + controls:** matched-assignment 4.906 → 5.765 (Δ +0.859),
  coarse 2.795 → 4.636; shuffle collapses both toward 1.0 (gain in the order); top1
  0.626 ≫ freq 0.109. The live-anchor pof=1.0→7.5 with sample size, no transform.
- **(4) frontier:** the posed frontier was a small-sample/grain artifact (refuted with
  numbers); the genuine partial gain from invariance is real and shuffle-verified; the
  next constraint is the YARDSTICK's reliability at the live merge grain, named.
- **Tests:** `test_stt_pipeline` + `test_perception_self_assessment` +
  `test_process_meta_assessor` + `test_gap_guidance` — **26 passed**.
- **Not committed; left in the working tree:** `scripts/units_invariance_pof_probe.py`,
  this doc.

### One-line finding

Pursuing the perception/units frontier showed two true things at once: the agent's own
invariance transform is a real, order-located lift to unit predictability
(pof 4.9→5.8 at matched assignment, shuffle-verified), AND the `pof=1.0` that flagged
the frontier was a small-sample artifact of the DTW-merge grain — so the deepest
remaining gap is the YARDSTICK's reliability on isolated-word units, not the units
themselves.
