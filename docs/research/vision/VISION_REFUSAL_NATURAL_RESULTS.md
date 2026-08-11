# DOES THE REPRESENTABLE REFUSAL SURVIVE THE NET'S HOME TURF? — RESULTS

> **LEDGER ROW (for transcription; do NOT edit VISION_PROTOCOL.md):**
> **130000–130999 ALLOCATED; NO Rust and NO new seed (a measurement reusing the
> existing AbS comparison mechanism — nearest-prototype reconstruction residual);
> Term indices UNCHANGED. Literal in-block seeds (data-split 130000, robustness
> 130020–130021, nets 130001–130003, corruption 130002, bootstrap 130100),
> disclosed.** **VERDICT: DEGRADE — the wedge is REAL but BOUNDED, and 129000's
> wide win WAS substantially raw-distance-friendliness.** On CIFAR-10 natural-image
> OOD (in-dist = 6 classes, near-OOD = 4 held-out classes, far-OOD = SVHN + noise +
> corruption), the honest boundary test 129000 named for itself:
> **(1) END-TO-END, the substrate LOSES decisively.** The mechanism in its OWN raw
> representation (`substrate_residual_raw`) scores AUROC **0.57 near / 0.61 far** and
> is CI-separated BELOW the net's best arm on every split and pool (paired
> raw−bestnet near −0.08…−0.11, far −0.19…−0.25); in-dist accuracy **0.37 vs the
> net's 0.80**. On natural images raw-pixel distance is near-useless — the mechanism
> cannot reach competitive features on its own. **(2) REPRESENTATION-CONTROLLED (the
> decisive arm), the mechanism SURVIVES — weakly, on the discriminating case.** In
> the NET'S OWN learned features the comparison mechanism
> (`substrate_residual_feat`, nearest-prototype residual) beats the STANDARD
> selection detector MSP CI-separated on NEAR-OOD on all 3 splits (paired
> **+0.027…+0.056 SEP+**), and the single best OOD arm in feature space is a
> COMPARISON method (kNN) on every split. **BUT it does not DOMINATE:** vs the
> stronger selection method (energy) the near win is NOT CI-separated (wins 1/3,
> ties 2/3), and on FAR-OOD energy and kNN beat the 1-NN residual on 2/3 splits.
> **(3) The mechanism-vs-representation isolation is the crown number:** holding the
> mechanism FIXED and swapping raw→learned features lifts its AUROC by
> **+0.07…+0.12 (paired SEP+ on every split/pool)** — the representation, not the
> mechanism, does the heavy lifting. **This BOUNDS 129000 precisely:** its Omniglot
> AUROC (0.975) collapses to ~0.57 on natural raw pixels; what survives the hostile
> regime is the narrower claim — *comparison is the right refusal mechanism and
> beats standard selection-confidence even in learned features on near-OOD* — but it
> is NOT proprietary (a net bolts on the same mechanism as kNN/Mahalanobis post-hoc)
> and needs a strong representation it cannot itself produce. §9 oracle **222/0
> before AND after**; provenance `own` (`67add13387fa`) re-verified stable;
> `check_claim` CLEAN. **WHAT I GOT WRONG:** the task's own framing (and mine) called
> Mahalanobis/kNN "the net's detectors" — they are the substrate's COMPARISON
> mechanism in feature space, which is exactly why the substrate can't beat the
> net's full pipeline; the faithful AbS 1-NN is itself beaten by k=5 kNN on far; and
> SVHN is an INVERTED far-OOD detector (residual smaller than in-dist) in both raw
> and feature space.

Pre-registration: `VISION_REFUSAL_NATURAL_PREREG.md`, committed **`2e7bb866ff`**
before any number. The successor to `VISION_REFUSAL_USEFULNESS_RESULTS.md`
(block 129000 — "the first useful-wedge number", CONFIRM on Omniglot). That rung
flagged its own confound (Omniglot is NN/raw-distance-friendly); this rung runs
the test in the regime designed to narrow or invert the wedge.

- **branch (as observed):** `worktree-agent-a49a32b1fe3effbf5`.
- **base SHA (as observed):** `71ef444d75eb8e5016d7a602245c7f43cd0b136e` (the
  129000 ledger commit).
- **engine.** NO Rust added; I built my own anyway (`engine_build.sh`):
  `67add13387fa`, `source_match=own`, re-verified STABLE after all measurement
  (`assert_measuring_engine` → `own` asserted at import; `provenance_after` in the
  committed JSON matches; `EXPECT_ENGINE=67add13387fa` asserted in-process).
- **oracle:** `bash scripts/rung7_vision_bench.sh` → **222 passed, 0 failed**,
  `data/` symlinked — BEFORE (`var/oracle_before_130000.log`) AND AFTER
  (`var/oracle_after_130000.log`).
- **seeds:** 130000–130999 ALLOCATED; `check_claim(130000,130999)` **CLEAN** (553
  unresolved sinks tree-wide, priced; verbatim in prereg §8). Literal in-block
  seeds only.
- **CPU / cost (data, NOT a verdict):** `torch.set_num_threads(2)`,
  `OMP/MKL_NUM_THREADS=2`; loadavg start `(1.54,1.55,1.38)` → end
  `(1.26,1.71,1.75)`; total wall **1436.8 s**; per-CNN train ~137 s (7 trainings).
  No wall-clock used as a verdict — AUROC/cost is the verdict.
- **all numbers below are read from the committed `results/refusal_natural.json`**
  via `scripts/refusal_natural_report.py` (verify-on-the-product).

---

## THE TASK, STATED EXACTLY

**Dataset:** CIFAR-10 (32×32×3 natural images; `cifar_train` sha `81a44852bc6db324`,
`cifar_test` sha `81b982202ebbf089`, loaded via HuggingFace `uoft-cs/cifar10`,
saved in-tree, NOT committed). **The regime where raw-pixel distance is WEAK and a
net's learned features dominate.**

- **IN-DIST classes** = CIFAR-10 classes 0–5 (airplane, automobile, bird, cat,
  deer, dog). The CNN trains ONLY on these; the substrate codebook holds ONLY these.
- **NEAR-OOD** = CIFAR-10 held-out classes 6–9 (frog, horse, ship, truck) from the
  CIFAR TEST split — natural images, SAME dataset statistics, semantically related
  but NOVEL. **The discriminating case (selection-confidence fails hardest here).**
- **FAR-OOD** (3 sub-kinds, reported separately): **svhn** (SVHN test crops, sha
  `cdce80dfb2a2c4c6` — a different natural-image dataset), **gauss** (Gaussian
  noise in the normalized pixel space), **corrupt** (in-dist test with 4×4 pixel
  blocks shuffled, seed 130002 — same marginals, no object).
- **Per-class split:** train M=1500/class (CIFAR TRAIN → net-train AND
  substrate-codebook exemplars, SAME data both arms); val 200/class (CIFAR TRAIN,
  disjoint → thresholds ONLY, 1200 imgs); test 500/class (CIFAR TEST → 3000 imgs).
  near 500/class (2000); each far sub-kind 2000.
- **The net (not a strawman):** a real 5-conv-block BatchNorm CNN with cosine LR
  and horizontal-flip augmentation, 25 epochs — **in-dist test accuracy 0.80–0.81**
  across splits, given its STRONGEST honest post-hoc detectors (MSP, energy,
  Mahalanobis, kNN).

---

## THE ARMS AND THE FAIRNESS RULE (§13)

| arm | representation | mechanism | signal |
|---|---|---|---|
| **substrate_residual_raw** | RAW pixels | COMPARISON (AbS) | nearest-held-exemplar L2 residual — END-TO-END substrate |
| **substrate_residual_feat** | net penult. features | COMPARISON (AbS) | nearest-held-prototype L2 residual — REPRESENTATION-CONTROLLED |
| **…_feat_centroid** | net features | COMPARISON | nearest-class-centroid residual (prototype-set check) |
| **net_msp** | net logits | SELECTION | 1 − max-softmax (Hendrycks 2017) |
| **net_energy** | net logits | SELECTION | −logsumexp(logits) (Liu 2020) |
| **net_maha** | net features | comparison-in-features | min-class Mahalanobis (Lee 2018) |
| **net_knn** | net features | comparison-in-features | k=5-NN distance (Sun 2022) |
| **net_answer** | net logits | SELECTION (cannot refuse) | softmax argmax; MUST answer |

The substrate COMPARISON mechanism is `r(x)=min_p ‖x−p‖` (nearest-prototype
reconstruction residual = the AbS the arc built), realized host-side IDENTICALLY
across the raw and feature representations, so between `_raw` and `_feat` the ONLY
thing that varies is the representation. **FAIRNESS:** every threshold — every net
cut AND both substrate tolerances — is the α-quantile of that arm's OWN signal on
the 1200 in-dist VALIDATION images, on in-dist data ONLY, never on OOD. Feature
detectors fit on TRAIN features only. AUROC/AUPR are threshold-free.

---

## 1 — OOD AUROC (near and far reported SEPARATELY; net = mean±std over seeds)

Main split 130000 (substrate deterministic; nets mean±std over 3 seeds; per-arm
bootstrap 1000×). **Every arm's AUROC, NEAR-OOD | FAR-OOD:**

| arm | AUROC near | AUROC far |
|---|---|---|
| **substrate_residual_raw** (end-to-end) | 0.567 [0.550,0.583] | 0.615 |
| **substrate_residual_feat** (repr-controlled) | 0.649 ± 0.008 | 0.741 ± 0.016 |
| substrate_residual_feat_centroid | 0.605 ± 0.003 | 0.798 ± 0.013 |
| net_msp (standard selection) | 0.617 ± 0.013 | 0.682 ± 0.036 |
| net_energy (strong selection) | 0.659 ± 0.020 | 0.613 ± 0.023 |
| net_maha (comparison-in-features) | 0.562 ± 0.014 | 0.706 ± 0.010 |
| **net_knn (comparison-in-features)** | **0.680 ± 0.012** | **0.809 ± 0.005** |

Robustness (130020 / 130021) reproduce the ordering: near — knn 0.681/0.649 top,
feat 0.657/0.649, energy 0.674/0.649, msp 0.629/0.618, maha 0.567/0.568, raw
0.570/0.569. **On NEAR-OOD the COMPARISON methods (knn ≈ feat) are top and the
SELECTION-MSP is consistently below them; the best single arm in feature space is a
comparison method (kNN) on every split.** Mahalanobis is the WORST feature method
on near (its Gaussian class-conditional assumption breaks on near-OOD classes).

**FAR-OOD by sub-kind (split 130000):** the pooled far number hides structure —
**svhn** is an INVERTED detector (raw 0.212, feat-s0 0.351, maha-s0 0.321 — all
< 0.5: SVHN digits sit CLOSER than in-dist test in both raw and feature space, a
known hard CIFAR-vs-SVHN case), **gauss** trivial (raw 0.969, feat 0.970), **corrupt**
mid (raw 0.663, feat 0.875). far is dominated by which arm best separates SVHN.

---

## 2 — THE PAIRED BOOTSTRAP (the powered test; first net seed, 2000×)

Marginal CIs under-power the comparison; the paired bootstrap on the AUROC
difference (SAME resampled inputs) is the gate. `SEP+`/`SEP-` = 95% CI entirely
above/below 0. Per split (130000 / 130020 / 130021):

**REPRESENTATION-CONTROLLED, the decisive contrast — comparison vs SELECTION in the
SAME net features:**

| pair | near | far |
|---|---|---|
| `feat − net_msp` | **+0.056 / +0.042 / +0.027 — SEP+ 3/3** | +0.092 SEP+ / −0.033 SEP− / −0.096 SEP− |
| `feat − net_energy` | +0.026 SEP+ / −0.012 ns / −0.011 ns | +0.152 SEP+ / −0.135 SEP− / −0.130 SEP− |

**comparison vs comparison, same features:**

| pair | near | far |
|---|---|---|
| `feat − net_maha` | +0.097 / +0.090 / +0.081 — SEP+ 3/3 | +0.024 / +0.030 / +0.040 — SEP+ 3/3 |
| `feat − net_knn` | −0.009 / −0.013 / −0.003 — ns 3/3 (tied) | −0.071 / −0.132 / −0.154 — SEP− 3/3 |

**END-TO-END and the isolation:**

| pair | near | far |
|---|---|---|
| `raw − best-net-arm` | −0.099 / −0.110 / −0.083 — **SEP− 3/3** | −0.188 / −0.245 / −0.243 — **SEP− 3/3** |
| `feat − raw` (mechanism fixed, repr swapped) | **+0.091 / +0.096 / +0.073 — SEP+ 3/3** | **+0.118 / +0.110 / +0.089 — SEP+ 3/3** |

**Reading:** (a) the comparison mechanism beats the STANDARD selection detector
(MSP) CI-separated on NEAR-OOD on every split; (b) it does NOT beat the STRONG
selection detector (energy) — near it ties (2/3), far energy wins (2/3); (c) the
faithful 1-NN residual is itself beaten by k=5 kNN on far; (d) END-TO-END the raw
substrate loses CI-separated everywhere; (e) `feat − raw` = +0.07…+0.12 SEP+
quantifies that swapping raw→learned features (mechanism FIXED) is what moves the
number — **the representation, not the mechanism, is doing the work.**

---

## 3 — EXPECTED-COST SURFACE (matched α=0.10; substrate vs the BEST net arm)

Fraction of the (C_wrong/C_refuse ∈ {2..50} × ρ ∈ [0,1], 105 points) surface where
the substrate has strictly lower expected cost than the min-over-net-arms:

| split | near: feat beats best-net | near: raw beats best-net | far: feat beats best-net | far: raw beats best-net |
|---|---|---|---|---|
| 130000 | 0.26 | 0.00 | 0.79 | 0.00 |
| 130020 | 0.45 | 0.00 | 0.63 | 0.00 |
| 130021 | 0.00 | 0.00 | 0.00 | 0.00 |

**`substrate_residual_raw` never owns any point of the cost surface** (0/105 on
every split/pool). `substrate_residual_feat` owns a MINORITY of the near surface
and a variable share of far — **because the "best net arm" includes kNN and
Mahalanobis, which ARE the substrate's comparison mechanism in feature space.**
Against the net's FULL post-hoc arsenal the feature-space comparison is roughly
tied, not dominant — the opposite of 129000, where the substrate owned 21/21 of the
Omniglot surface. (Contrast is the point: on Omniglot the mechanism's cheap
representation was enough; here it is not.)

Matched op-point (α=0.10, split 130000, in-dist refuse / near-OOD detection):
substrate_feat 0.107/0.234, net_knn 0.095/0.209, net_energy 0.101/0.217,
net_msp 0.096/0.156, net_maha 0.089/0.122, substrate_raw 0.104/0.121. At low FPR
**no arm is a strong near-OOD refuser** (all ~0.12–0.24 detection) — near-OOD on
natural images is hard for everyone; the AUROC differences, not absolute detection,
are the signal.

---

## 4 — CONFABULATION (silent confident-wrong) ON NEAR-OOD (α=0.10)

The SELECTION failure the representable refusal is meant to prevent is real and
severe on near-OOD (split 130000 / 130020 / 130021):

- **net_answer confident-wrong fraction of near-OOD = 0.844 / 0.834 / 0.820** — the
  net emits a confident WRONG label on ~83% of held-out natural classes.
- **near median MSP = 0.907 / 0.903 / 0.904; ~51% / 50% / 50% of near-OOD keep
  MSP > 0.9.** Softmax is badly overconfident on novel natural classes.
- But at the matched op-point every REFUSER misses most near-OOD too:
  substrate_feat misses 0.766/0.734/0.790, substrate_raw 0.879/0.876/0.884,
  net_maha 0.878/0.852/0.886. The comparison-in-features arm catches the MOST
  (misses least) but still only ~21–27%. **The confabulation is real; no refuser
  on natural near-OOD at low FPR is a strong guard — a much narrower picture than
  Omniglot (there the substrate caught 82%).**

---

## 5 — IN-DIST ACCURACY (a registered expectation CONFIRMED — the Omniglot inverse)

| arm | in-dist test accuracy (per split 130000 / 130020 / 130021) |
|---|---|
| net (CNN) | 0.796 / 0.811 / 0.811 |
| **substrate_residual_feat (1-NN in net features)** | 0.787 / 0.798 / 0.788 |
| substrate_residual_raw (1-NN in raw pixels) | **0.373 / 0.382 / 0.371** |

**The net WINS in-dist accuracy (0.80 vs raw 0.37) — the exact INVERSE of Omniglot,
where the raw 1-NN won 0.980 vs the net 0.937.** Raw-pixel 1-NN is near-useless on
CIFAR; 1-NN in the net's features ≈ the net. This is the representation confound
made concrete: 129000's substrate won BOTH accuracy and refusal because the task's
cheap representation was strong; here the cheap representation is weak and the
mechanism must borrow the net's features to be competitive at either.

---

## 6 — VERDICT: **DEGRADE** — real but BOUNDED (and it shades toward the FALSIFY edge)

The registered discriminator resolves to DEGRADE, via its exact second clause
("wins in-feature-space but the substrate can't reach competitive features
end-to-end → the wedge is real but BOUNDED"):

1. **The mechanism SURVIVES into learned features on the discriminating case.** In
   the net's OWN features the comparison mechanism beats the STANDARD selection
   detector (MSP) CI-separated on NEAR-OOD on all 3 splits, and the best single OOD
   arm in feature space is a comparison method (kNN) on every split. "Comparison ≥
   selection in learned features" holds — on near-OOD.
2. **But it does NOT dominate (the FALSIFY-leaning edge, reported loudly).** vs the
   STRONG selection method (energy) the near win is not CI-separated (1/3 win, 2/3
   tie) and on far energy beats the 1-NN residual (2/3). The faithful AbS 1-NN is
   also beaten by k=5 kNN on far. Against the net's FULL post-hoc arsenal (which
   includes kNN/Maha — the comparison mechanism itself) the substrate is roughly
   tied, owning a minority of the cost surface, not 21/21.
3. **END-TO-END the substrate LOSES decisively.** `substrate_residual_raw` scores
   ~0.57 near / ~0.61 far, CI-separated below the net's best arm on every split and
   pool, with in-dist accuracy 0.37 vs 0.80. On natural images raw-pixel distance
   is near-useless; the mechanism cannot reach competitive features on its own.
4. **`feat − raw` = +0.07…+0.12 (SEP+ everywhere)** isolates the cause: with the
   mechanism held FIXED, the LEARNED representation supplies the entire advantage.

**Therefore 129000's wide Omniglot wedge (AUROC 0.975 vs ≤0.941, cost surface 21/21)
WAS substantially raw-distance-friendliness.** The mechanism's raw-space AUROC
collapses from 0.975 (Omniglot) to ~0.57 (CIFAR near). What survives the hostile
regime is the narrower, still-real claim: **comparison is the right refusal
mechanism, and beats standard selection-confidence (MSP) even in learned features
on near-OOD** — but (a) it does not beat a strong selection method (energy), (b) it
is NOT proprietary to the substrate (a net bolts on the identical mechanism as
kNN/Mahalanobis post-hoc), and (c) it needs a strong representation it cannot itself
produce.

**The boundary, stated exactly:** the useful wedge from 129000 is confined to
regimes where a held reconstruction in a CHEAP, GIVEN (not learned) representation
is meaningful — distance-friendly tasks like Omniglot online strokes. On
natural images the wedge as an INDEPENDENT capability evaporates; it persists only
as a mechanism-choice statement (prefer comparison over selection for refusal) that
is realized just as well by a net's own kNN/Mahalanobis detector on learned
features.

---

## 7 — SCOPE: MECHANISM vs BENCHMARK VALUE (report BOTH)

- **Mechanism-level (what survives):** comparison ≥ selection SURVIVES into learned
  features on near-OOD, CI-separated over the standard MSP baseline on all splits;
  the best in-feature OOD detector is a comparison method. The mechanism choice
  (comparison over selection) is vindicated even on the net's home turf — narrowly.
- **Benchmark value (what does NOT hold):** the substrate as a STANDALONE
  natural-image OOD detector is NOT competitive (raw AUROC ~0.57, acc 0.37, owns
  0/105 of the cost surface). It is competitive ONLY as a post-hoc detector on the
  NET'S features — which is precisely what kNN/Mahalanobis already are. Small (6
  classes, one CNN family, 3 splits, CPU, 25 epochs); one dataset; SVHN far-OOD is
  an inverted detector. **A mechanism result, bounded; not benchmark value, and
  not a standalone capability.**
- **What this means for the project's central "useful" claim:** it NARROWS.
  129000's "first useful-wedge number" is real but regime-bound to cheap-representation
  / distance-friendly tasks. On the net's home turf the wedge does not confer an
  independent advantage.

---

## 8 — WHAT I GOT WRONG

1. **The Mahalanobis/kNN mislabel (the crux).** The task's framing (and my prereg)
   grouped Mahalanobis/kNN with energy as "the net's selection-derived detectors."
   They are NOT selection-derived — they are the substrate's COMPARISON mechanism
   (distance-to-held-prototype) transplanted into learned features. Getting this
   right is load-bearing: it means the net's OWN strongest OOD detector already IS
   the substrate's mechanism, which is exactly why the substrate does not beat the
   net's full pipeline. I report the contrast as comparison-vs-selection, and
   report that the net can simply ADOPT the comparison mechanism post-hoc — rather
   than claiming a clean substrate win over "the net."
2. **The faithful 1-NN is not the best comparison detector.** `substrate_residual_feat`
   (k=1, the exact AbS reconstruction residual) is beaten by k=5 kNN on far-OOD
   (SEP− 3/3) — k=1 is noisier on far. I report both k and do not cherry-pick.
3. **SVHN is an inverted far-OOD detector.** AUROC ~0.21 raw / ~0.25–0.35 feat —
   SVHN crops sit CLOSER (smaller residual) than in-dist CIFAR test in both raw and
   feature space (low pixel complexity, plain backgrounds), a known hard
   CIFAR-vs-SVHN case. It drags the pooled far number down; I report far by
   sub-kind so it is visible, not hidden.
4. **A registered expectation was RIGHT but under-stated.** I predicted the net
   would win in-dist accuracy (it did, 0.80 vs 0.37 — the Omniglot inverse). I did
   NOT pre-commit to how sharply the raw-space mechanism would collapse (0.975 →
   0.57 near, near-chance): the confound 129000 flagged is larger than "narrower" —
   the raw mechanism is essentially non-functional on natural images.
5. **The cost-surface accounting cuts against my own hypothesis and I kept it.**
   Because "best net arm" includes kNN/Maha (comparison methods), the substrate_feat
   owns only a minority of the surface. A hypothesis-friendly framing would have
   compared feat only against the SELECTION arms (msp/energy), where it looks
   better. I report against the net's FULL arsenal — the honest, harder test.
