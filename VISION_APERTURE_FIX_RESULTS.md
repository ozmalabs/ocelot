# THE TRUNCATED APERTURE — results

**Pre-registration `VISION_APERTURE_FIX_PREREG.md`, committed at
`f48ef9944fe9134e148e279185ebfd30ebabf8de` BEFORE any measurement.**
Fix + gate `514cf6afe65f0b4b36df7ad1fcd2f7821379fe4a`.
Engine **`5b7eb7ff9ecd`**, built with `scripts/engine_build.sh` in this
worktree. Provenance gate run as **its own step before any number**: 627
passed, exit 0. Bench oracle **222 passed, exit 0** (exit code checked, log
timestamp verified fresh — §"a redirect target is not evidence").
Seeds consumed: **71000–71199**. No Rust, no Term, no seed change.

---

## THE HEADLINE, in one line

**The defect is real, reachable, and was NEVER REACHED by any landed
invariant-comparator number — 0 short windows in 427,392 landed windows, with
3,000/20,000 in a positive control that proves the instrument was alive.** The
fix therefore corrects no published figure. But the truncation IS a systematic
**selection** bias where it can bite (synthetic: +0.0125 [+0.0036, +0.0214],
CI-separated toward the interior) — and that bias **does not replicate on real
photographs** (BSDS: −0.0010 [−0.0091, +0.0070], null). And the incumbent's own
guard is confirmed **blind to it: score agreement 1.0000 on 480 rows the fix
proves wrong.**

---

## 1. The fix

`domains/invariant_comparator_world.py::orbit_windows` takes an explicit `pad`
(defaulting to `rho`, so the index expression at the default is
character-for-character the original) and **raises** on any window that is not
exactly `region × region`. `scripts/invariant_comparator_measure.py::run_cell`
pads by `rho + max|displacement|` instead of `rho`.

numpy clips an out-of-range slice silently. That is the whole defect: a window
taken at `origin + d` from a source padded by `rho` alone runs off the end at
the trailing-edge regions and comes back with 4 columns where 6 were expected.

## 2. H2 — the d=0 no-op, RE-ESTABLISHED, NOT INHERITED

The verdict rung stated this fix is a no-op at zero displacement. This rung did
not take that on trust. `tests/test_aperture_fix_migrated.py` keeps a **frozen
verbatim copy of the pre-fix function** and compares tiles **element-wise**:

| rho | comparisons | identical |
|---|---|---|
| 0 | 384 | all |
| 1 | 3,456 | all |
| 2 | 9,600 | all |
| 3 | 18,816 | all |

(24 sources × 16 origins × (2ρ+1)² shifts.) **The no-op reproduced
independently.** Its proviso is also gated: `pad_edge` is asserted semantically
unchanged, because the no-op holds *only* because the fix touched the index
arithmetic and not the padding.

## 3. H3 — THE BLAST RADIUS, ENUMERATED AND INSTRUMENTED

Every landed call site, run at its own geometry with the **pre-fix**
arithmetic, counting windows whose shape is not `(6,6)`:

| call site | windows | short | unaffected because | is it the d=0 argument? |
|---|---|---|---|---|
| **C3** (`run_c3`, BSDS, d ∈ {0,1,2,3,4,6} axis **and** diagonal) | 387,072 | **0** | the source is the **full 321×481 photo** with the 24×24 grid at the centre; the photo's own ~150 px margin — not `pad_edge` — bounds every window | **NO.** C3 displaces heavily. It escapes on **source size**, a completely different argument |
| **video C1/C2** (`run_video`, genuine 24×24 frames) | 13,440 | **0** | 24×24 frames, so the padding **is** binding here — but every probe is presented at offset `(0,0)` | **YES**, this one is the d=0 case |
| **replay** (`run_replay`) | — | **0** | a strict subset of the C3 configuration | inherits C3's argument |
| **`tests/test_invariant_comparator_migrated.py`** (`_present_shifted`, d ∈ {0..3}, pads by ρ — the defective combination) | 26,880 | **0** | 42×42 random source with the 24×24 grid centred (margin 9) | **NO** — source size again |
| **POSITIVE CONTROL** — 24×24 source **with** displacement | 20,000 | **3,000** | — | the configuration the defect bites in |

**427,392 landed windows, zero truncated.** The control fires at 15%, so the
three zeros are not an inert instrument (§12.3 — a check that has never been
able to fail has not been tested).

**The prediction stated in the pre-registration was correct, including its
reason:** the incumbent escapes on *source size* for C3 and the tests, and on
*zero displacement* only for video. Had I inherited the verdict rung's "no-op
at d=0" argument, I would have reached the right conclusion for C3 **by the
wrong route** — C3 displaces by up to 6 and diagonally, and the d=0 argument
does not cover it at all.

### 3.1 Consequence for the landed results

| landed result | status |
|---|---|
| `VISION_INVARIANT_COMPARATOR_RESULTS.md` C3 (all comparators, all displacements) | **UNAFFECTED, by measurement** (0/387,072) |
| C3 diagonal secondary (Q0, Q2) | **UNAFFECTED** — included in the 387,072 |
| Video C1/C2 (all deltas, all comparators) | **UNAFFECTED** (0/13,440; d=0 path, and byte-identity gated) |
| Replay determinism check | **UNAFFECTED** (C3 subset) |
| **The 1 → 2 → 3 horizon headline** | **UNAFFECTED** — twice over, see §5 |
| `VISION_VERDICT_RESULTS.md` | already fixed in its own rung at `64a9641b`; its treatment is **complete** (explicit `pad`, loud guard, callers pass `rho + |d|`) and this rung's copy is now identical in construction |
| `scripts/salience_rescore_field.py` | imports `invariant_comparator_world` but calls **neither** `pad_edge` nor `orbit_windows` — not in scope |

No re-run was needed anywhere. Nothing to correct in the record.

## 4. H4 — THE POSITIONAL SELECTION BIAS

Measured where truncation IS reachable: 24×24 source, `pad = rho`, ρ=2,
d ∈ {1,2,3,4,6}, axis displacement. TRUNC (pre-fix) vs FULL (post-fix) on
identical sources and codebooks. Unit of analysis is the **source**, never the
trial. 40 synthetic fields (seeds 71100–71139) and 24 BSDS centre crops.

### S1 — score change (reported separately, as instructed)

| | synthetic | BSDS crops |
|---|---|---|
| mean cells compared, TRUNC | 33.60 | 33.60 |
| mean cells compared, FULL | 36.00 | 36.00 |
| trials containing ≥1 short window | 25.0% | 25.0% |
| paired score Δ (FULL − TRUNC) | **+0.335 [+0.312, +0.359]** | **+0.630 [+0.587, +0.672]** |

The truncated arm scores systematically lower, CI-separated on both corpora —
the mechanical consequence of a lower ceiling.

### S2 — SELECTION disagreement

| | synthetic | BSDS crops |
|---|---|---|
| trials where argmax differs | **8.13% [7.41, 8.84]** | **3.39% [2.02, 4.75]** |

**This is the part invisible to a score-agreement check.** One trial in twelve
(synthetic) picks a *different region* under the truncation.

### S3 — DIRECTIONAL bias: **THE CORPORA SPLIT**

`P(TRUNC picks interior | FULL picked edge) − P(TRUNC picks edge | FULL picked
interior)`; positive = the truncation drags the answer **inward**.

| | synthetic | BSDS crops |
|---|---|---|
| P(interior \| FULL=edge) | 0.0597 (n=1,440) | 0.0142 (n=634) |
| P(edge \| FULL=interior) | 0.0261 (n=1,760) | 0.0086 (n=1,286) |
| **directional bias** | **+0.0125 [+0.0036, +0.0214]** — CI-separated positive | **−0.0010 [−0.0091, +0.0070]** — **NULL** |

**The pre-registered prediction is CONFIRMED on synthetic fields and NULL on
real photographs.** The ceiling argument — a 24-cell window cannot win an
argmax against a 36-cell one — is correct as mechanism and produces a
measurable inward pull on random fields, and **does not survive contact with
natural image statistics**. The corpora take different answers, for the fourth
time in this arc; they are reported per-corpus and **never pooled**.

Accuracy split by whether the TRUE region is a trailing-edge one:

| | synthetic | BSDS crops |
|---|---|---|
| edge-truth acc, TRUNC → FULL | 0.4521 → 0.4900, Δ **+0.0379 [+0.0216, +0.0541]** | 0.3274 → 0.3107, Δ **−0.0167 [−0.0313, −0.0020]** |
| interior-truth acc, TRUNC → FULL | 0.4172 → 0.4172, Δ **+0.0000 exactly** | 0.3398 → 0.3398, Δ **+0.0000 exactly** |

Two things to read here, and the second is the more interesting:

1. **The interior is untouched to the last digit on both corpora.** The effect
   is confined precisely to the regions whose windows truncate — which is what
   a positional bias should look like, and is the strongest single piece of
   evidence that the effect is the truncation and not noise.
2. **On real photographs the truncation makes edge-truth accuracy slightly
   BETTER** (−0.0167, interval excluding zero on the negative side). The
   pre-registration named this exact possibility in advance as the two-sided
   alternative: *"a truncated window also has fewer tuples to MISS, so its
   overlap FRACTION can rise even as its count falls."* On a natural image,
   where neighbouring 6×6 tiles are correlated, the cells a short window drops
   are disproportionately the ones that would have mismatched.

### S4 — THE BLINDNESS DEMONSTRATION

The real substrate, run on truncated windows (480 rows, seeds 71160–71169):

| statistic | value |
|---|---|
| **score agreement `icg_max` == outside reference `nn_score`** | **1.0000** |
| accuracy on those truncated windows | 0.3813 |

**The incumbent rung's central cross-check passes PERFECTLY on data this rung
proves wrong.** Both sides count over the *same* short window, so the check
cannot see the defect — by construction and now by measurement. This is the
answer to "why did it go unreported for so long": not carelessness, but a guard
that is blind to this failure mode by design. **A set-overlap verdict cannot
audit its own aperture; a norm can.**

## 5. H5 — the 1 → 2 → 3 horizon

**Unaffected, and for two independent reasons — the second of which was not
anticipated.**

1. H3: the C3 path never truncated at all (0/387,072).
2. **Even in the reachable configuration, the horizon would not move.** The
   per-displacement breakdown shows the selection is *completely* unchanged
   while `d ≤ ρ`:

| d (ρ=2) | sel. differs, synthetic | acc TRUNC | acc FULL |
|---|---|---|---|
| 1 | **0.0000** | 1.0000 | 1.0000 |
| 2 | **0.0000** | 1.0000 | 1.0000 |
| 3 | 0.1047 | 0.0984 | 0.1172 |
| 4 | 0.1234 | 0.0516 | 0.0625 |
| 6 | 0.1781 | 0.0125 | 0.0656 |

The horizon is the largest `d` at which the arm separates from its floor, and
separation survives only while the orbit contains the exact translate, i.e.
`d ≤ ρ` — **exactly the region where the truncation changes nothing at all.**
The bias appears only past the horizon, where accuracy has already collapsed to
near chance (1/16 = 0.0625). The truncation deepens a failure; it cannot
manufacture or move a success.

## 6. The two-sided gate

`tests/test_aperture_fix_migrated.py` — 46 passed, 1 skipped.

- **IDENTICAL**: d=0 array-by-array vs the frozen pre-fix function (§2); every
  landed call-site configuration byte-identical pre/post; with a sufficient pad
  the two functions are the *same function* on every interior origin — the fix
  narrows nothing.
- **CHANGED**: at trailing-edge origins with d>0 the pre-fix window is **not**
  the ground-truth window and the fixed one **is**, element-wise against a
  window cut from a source padded far beyond reach. `n_wrong_before > 0` is
  asserted, so a fix that changed nothing would go RED.
- **LOUD + POSITIVE-CONTROLLED**: the same test asserts the frozen pre-fix
  function returned the short array **silently** on exactly the input that now
  raises, and asserts that control non-vacuous.

## 7. Scope, and what is NOT shown

- The H4 displacement is **axis-only** `(0, d)`, matching C3's A1 probe form.
  Only the 4 column-trailing regions can truncate, while the pre-registered
  edge/interior partition contains 7 regions (row- *or* column-trailing). The
  reported S3 is therefore **diluted** by 3 regions that never truncate; the
  bias *among regions that actually truncate* is larger than the figure quoted.
  Stated as a scope limit and **not re-cut after the fact** (§5).
- ρ is held at 2 (the measured knee) and **not swept**.
- This rung measures the incumbent's `covered_count` comparator only. It says
  nothing about how truncation behaves under the verdict rung's norms beyond
  what that rung already reported.
- The synthetic/BSDS split in S3 is **reported, not explained**. The
  correlated-neighbour account in §4 is a hypothesis, not a measurement.

## 8. What I got wrong

- **`excludes_zero` in `scripts/aperture_fix_measure.py` is coded one-sided**
  (`lo > 0.0`). It therefore reports `false` for the BSDS edge-accuracy
  interval `[−0.0313, −0.0020]`, which *does* exclude zero — negatively. The
  raw interval is in the JSON and is quoted correctly above, but the derived
  flag is wrong for negative effects and should not be trusted on its own. Left
  in place and disclosed rather than silently patched after seeing the result.
- I initially reached for the verdict rung's "no-op at d=0" as the reason C3 is
  safe. It is not: C3 displaces by up to 6, diagonally. The right answer is
  source size, and only instrumenting the call site produced it. **The inherited
  claim would have given the right conclusion by the wrong argument** — which
  is precisely the failure mode the task warned about, and it caught me first.
