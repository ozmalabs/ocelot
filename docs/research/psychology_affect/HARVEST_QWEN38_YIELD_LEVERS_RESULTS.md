# Harvest Qwen3.8 — Yield Levers on the Same Elicitation Channel (DIRECTION 1)

## Goal

Recover the fidelity lost at open-vocabulary scale (block 337: **0.272** valid
is-a on 6000 WordNet nouns, coverage 5772) by using signal the single-template
argmax harvest discards, and measure the recovery honestly against that baseline.

Validity = the object is an **any-level WordNet ancestor** of the subject
(same check across all levers). Elicited on a **reproducible subset of 1200**
of the same 6000 subjects (SEED_RNG=0 inventory, first 1200), 8162
candidate hypernyms.

## Baseline reproduced on the subset

| metric | value |
|---|---|
| coverage (forward argmax edges) | 1152 |
| valid-rate (any-level ancestor) | **0.257** |
| exact immediate-parent | 0.099 |

This tracks the block-337 full-run numbers (0.272 valid / 0.108 exact), so the
subset is a faithful stand-in.

## Lever 1 — confidence-weighting (logit margin threshold)

Keep the top1-top2 margin over the candidate set per edge; sweep a threshold.
Validity-vs-coverage (precision/recall-style):

| margin >= | coverage | coverage-frac | valid-rate |
|---|---|---|---|
| 0.0 | 1152 | 1.000 | 0.257 |
| 0.5 | 636 | 0.552 | 0.318 |
| 1.0 | 312 | 0.271 | 0.359 |
| 1.5 | 167 | 0.145 | 0.431 |
| 2.0 | 70 | 0.061 | 0.529 |
| 3.0 | 12 | 0.010 | 0.667 |
| 4.0 | 0 | 0.000 | nan |
| 5.0 | 0 | 0.000 | nan |
| 6.0 | 0 | 0.000 | nan |
| 8.0 | 0 | 0.000 | nan |
| 10.0 | 0 | 0.000 | nan |

Signal separation (mean over valid vs wrong edges):

- margin:  valid=1.009  wrong=0.679
- entropy: valid=3.870  wrong=4.753

## Lever 2 — multi-frame corroboration

Independent framings fused: **F** forward ("A {s} is a kind of ___", argmax),
**V** verification ("Is a {s} a kind of {o}? yes/no", P(yes)>=0.5), **R**
reverse ("Examples of {o} include ___", does s appear in o's top-3?).

| frames agreeing | coverage | coverage-frac | valid-rate |
|---|---|---|---|
| F only (baseline) | 1152 | 1.000 | 0.257 |
| F & V | 563 | 0.489 | 0.496 |
| F & R | 66 | 0.057 | 0.485 |
| F & V & R | 48 | 0.042 | 0.646 |
| >=2 of 3 | 581 | 0.504 | 0.482 |
| all 3 | 48 | 0.042 | 0.646 |

## Lever 3 — verification-scoring over generation

(a) Threshold the verification P(yes) on the forward edge:

| P(yes) >= | coverage | coverage-frac | valid-rate |
|---|---|---|---|
| 0.00 | 1152 | 1.000 | 0.257 |
| 0.50 | 563 | 0.489 | 0.496 |
| 0.60 | 493 | 0.428 | 0.538 |
| 0.70 | 398 | 0.345 | 0.588 |
| 0.80 | 257 | 0.223 | 0.646 |
| 0.90 | 55 | 0.048 | 0.764 |
| 0.95 | 4 | 0.003 | 1.000 |

(b) Re-rank the forward top-5 candidate shortlist by verification P(yes) and
pick the argmax, vs the top-1 generation pick (sample=200):

| read | valid-rate |
|---|---|
| top-1 generation | 0.265 |
| verification re-rank | 0.390 |

(c) **LLM-generated per-edge weight** (steering idea: ask the LLM for a weight
per edge — realized as the logit-readable verification P(yes) in [0,1], used
directly as trust instead of flat 0.5):

| read | validity |
|---|---|
| flat 0.5 (unweighted valid-rate) | 0.257 |
| P(yes)-trust-weighted validity | 0.409 |

mean generated weight: valid=0.777, wrong=0.389.

## Combination

margin >= 2.0 AND >=2 frames agree: coverage=43
(coverage-frac 0.037), valid-rate **0.860**.

## Honest reading — which levers help, by how much, and is it real?

**Ranking (all against the same any-level-ancestor check, baseline 0.257 / cov 1152):**

1. **Verification-scoring (Lever 3) is the clear winner.** Reading P(yes) from
   the yes/no prompt gives the best precision/coverage tradeoff of any single
   lever: **0.496 valid at 0.489 coverage** (≈2× baseline, half the edges kept),
   0.588 at 0.345, 0.646 at 0.223. And as a **re-rank it beats generation
   head-to-head at equal coverage**: on the 200-subject sample, picking the
   shortlist candidate that maximizes P(yes) scores **0.390 vs 0.265** for top-1
   argmax generation (+47% relative, *no coverage cost*). Verification asks a
   sharper question ("is THIS edge true?") than open generation ("what word is
   next?").

2. **Confidence-weighting (Lever 1) helps but is weaker.** Margin separates
   valid from wrong (1.009 vs 0.679; entropy 3.87 vs 4.75) and thresholding
   lifts validity monotonically, but the tradeoff is steep — reaching 0.53 keeps
   only **6%** of edges vs verification holding ~49% coverage at 0.50.
   Verification dominates margin point-for-point.

3. **P(yes) as a generated per-edge weight (Lever 3c, the steering idea) works.**
   Used directly as trust instead of flat 0.5, trust-weighted validity is
   **0.409 vs 0.257** flat; mean generated weight is 0.777 on valid edges vs
   0.389 on wrong. This is the same P(yes) signal as Lever 3, repackaged as soft
   per-edge trust — the natural way to feed the recovered signal into the
   substrate's corroborate-before-assert band *without discarding coverage*.

4. **Multi-frame corroboration (Lever 2) helps mostly through the verification
   frame.** F&V (0.496) ≈ V-thresholding alone, because V does the work. The
   **reverse frame R is weak** (F&R keeps only 66 edges at 0.485): a hypernym has
   many valid members, so the specific subject rarely wins the top-3. Adding the
   reverse frame buys precision only at severe coverage cost.

**Combination** (margin≥2.0 AND ≥2 frames) reaches 0.860 valid but only 43 edges
(3.7% coverage) — high precision bought with collapsed coverage, not a better
operating point.

**Real or artifact?** Both, and separable:

- **Real:** verification *re-rank* beats generation at **identical coverage**
  (0.390 vs 0.265) — no edges dropped, so it cannot be a selection artifact. The
  margin/entropy/P(yes) means also separate valid from wrong, so the confidence
  signal carries genuine correctness information.
- **Artifact risk:** the eye-catching rates at tight thresholds (P(yes)≥0.95 →
  1.000; combo → 0.860) are precision bought with collapsed coverage. Reporting
  those as headline validity would be dishonest. The honest operating point is
  coverage-preserving: verification recovers roughly **half** the lost fidelity
  (0.26 → ~0.50) while keeping ~half the edges, or feeds P(yes) as soft trust
  (**0.41** weighted) with **no coverage loss**.

**Bottom line:** the discarded verification signal is worth using — it ~doubles
validity at half coverage, is a strictly cleaner read than argmax generation at
equal coverage, and yields a principled per-edge trust to replace flat 0.5.
Margin is a useful secondary signal; reverse-membership corroboration is not
worth its cost. None of this overturns the block-337 lesson that the 4B model is
simply wrong about much of the WordNet long tail — these levers **recover and
rank the model's correct beliefs; they do not add knowledge the model lacks.**

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python/JSON only).
- Protected READ-ONLY files untouched; model/venv/nltk under /applications not
  committed; run log under var/ only; nothing committed by this script.
