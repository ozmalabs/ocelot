# IS THE REPRESENTABLE REFUSAL WORTH ANYTHING? — RESULTS

> **LEDGER ROW (for transcription; do NOT edit VISION_PROTOCOL.md):**
> **129000–129999 ALLOCATED; the measurement is a reuse of existing machinery so
> NO Rust and NO new seed were added; Term indices UNCHANGED (ArgminRefusal stays
> 180, NUM_TERM_VARIANTS 181); my measurement file seeds numpy/torch with LITERAL
> in-block integers (data-split 129000, robustness 129020–129022, nets
> 129001–129005, bootstrap 129100/129200), disclosed.** **THE FIRST USEFUL-WEDGE
> NUMBER — CONFIRM.** On Omniglot online-stroke recognition with a cost for
> confident-wrong answers, the substrate's **reconstruction-residual refusal**
> (the EXISTING AbS: `PointSetDist` to the argmax held-codebook winner = the
> mismatch) is a MEASURED differentiator over a net's best refusal on OOD.
> **OOD-detection AUROC 0.975 [0.962, 0.986]** (bootstrap CI) vs the net's
> **standard** refusals net_msp **0.907±0.007** and net_energy **0.902±0.012** —
> and vs the net's **STRONGEST** honest post-hoc detectors (added beyond the
> prereg to avoid strawmanning): Mahalanobis-on-features **0.941±0.004**,
> kNN-on-features **0.889±0.007**. **PAIRED bootstrap on the AUROC difference (same
> inputs — the powered test) is CI-separated in substrate's favour vs MSP/energy/
> kNN on ALL 4 splits, and vs the strongest (Mahalanobis) on 3 of 4 splits
> (positive on all 4).** **Substrate has LOWER expected cost than the best-of-all
> net arms at EVERY point of the (OOD-fraction × C_wrong/C_refuse) surface (21/21
> ρ, every ratio 2…50).** At a matched ~3–4% in-dist false-refuse rate the
> substrate catches **82.2%** of OOD; the net's best detectors catch **~49–59%**.
> **CONFABULATION quantified:** net_answer emits a confident WRONG label on
> **49.6%** of OOD at the matched op-point; **32.7%** of OOD keep MSP > 0.9 and the
> OOD median MSP is **0.79** — softmax stays confident OOD, the known failure,
> measured. **HONEST INVERSION of a registered expectation:** the substrate 1-NN
> WINS in-dist accuracy too (0.980 vs net 0.937/0.908) — the prereg predicted the
> net would win accuracy; it did not, because Omniglot is a distance/NN-friendly
> task. **SCOPE: small (30 classes, 600 test inputs), in-tree, one task, synthetic
> OOD — MECHANISM-proven, NOT benchmark value.** §9 oracle **222/0 before AND
> after**; provenance `own` (`67add13387fa`) re-verified stable; `check_claim`
> CLEAN (verbatim in prereg). **WHAT I GOT WRONG:** two inhomogeneous-array bugs
> (per-stroke + ambiguous trajectory) caught in smoke tests; strawman-averted
> mid-flight by ADDING Mahalanobis/kNN; and the marginal-CI-overlap trap
> (per-arm CIs of substrate vs Mahalanobis touch — the PAIRED test is the right,
> powered one).

Pre-registration: `VISION_REFUSAL_USEFULNESS_PREREG.md`, committed **`8d92f0e45b`**
before any number. The successor to `VISION_REFUSAL_REPRESENTABLE_RESULTS.md`
("a rule can HEAR a refusal") and `VISION_REFUSAL_CAPACITY_RESULTS.md`. Those
proved the refusal is REPRESENTABLE; this asks whether it is WORTH anything.

- **branch (as observed):** `worktree-agent-a27cdb8a64e124f5d`.
- **base SHA (as observed):** `a79b3d5c10573af8b06a0f6b252206bb325ad823`.
- **engine.** This rung adds NO Rust; I built my own anyway (`engine_build.sh`):
  `67add13387fa`, `source_match=own`, re-verified STABLE after all measurement
  (`assert_measuring_engine` → `own`; the measuring process asserts
  `EXPECT_ENGINE=67add13387fa` in `provenance_line()` and aborts on divergence).
- **oracle:** `bash scripts/rung7_vision_bench.sh` → **222 passed, 0 failed**,
  exit 0, `data/` symlinked — BEFORE (`var/oracle_before_129000.log`) AND AFTER
  (`var/oracle_after_129000.log`).
- **seeds:** 129000–129999 ALLOCATED; `check_claim(129000,129999)` **CLEAN** (546
  unresolved sinks tree-wide, priced; verbatim in the prereg §8). Literal in-block
  seeds only; unknown-sink disclosure in the prereg.
- **CPU / cost (data, NOT a verdict):** `torch.set_num_threads(2)`,
  `OMP/MKL_NUM_THREADS=2`; loadavg start `(0.60,0.71,2.03)` → end
  `(1.93,1.36,1.97)`; total wall **272.9 s**; net train cost recorded per model
  (MLP ~0.5 s, CNN ~4 s). No wall-clock used as a verdict.
- **all numbers below are read from the committed
  `results/refusal_usefulness.json`.**

---

## THE TASK, STATED EXACTLY

Omniglot online-stroke recognition (`domains/omniglot_world.py`,
`domains/recognition_graph.py`), background split, 30 alphabets, 20 drawers/char.

- **In-dist classes:** K=30 characters sampled (data-split seed 129000) from the
  first 15 (sorted) background alphabets (the KNOWN alphabets).
- **Drawer split per class:** drawers 0–11 → net training AND substrate codebook
  exemplars (BOTH arms see the SAME in-dist data); 12–14 → in-dist VALIDATION
  (threshold-setting only, 90 imgs); 15–19 → in-dist TEST (150 imgs).
- **OOD (450 total, ~150 each), exactly:**
  - **novel-class** — drawings of characters from the last 15 (OOD) alphabets:
    classes the codebook does NOT hold and the net never trained on.
  - **noise** — a normalized random-walk (cumulative-Gaussian) trajectory
    resampled by the SAME pipeline as a real drawing: a valid pen path matching no
    held class.
  - **ambiguous** — two DISTINCT in-dist-test drawings' strokes overlaid into one
    figure: no defined single label.
- **Inputs are IDENTICAL for the fair comparison:** the substrate and the PRIMARY
  net (an MLP) both read the same 48×2 whole-trajectory arc-length resampling. A
  SECONDARY net (small CNN on a 28×28 stroke raster — the net's natural modality)
  is reported so the net is not handicapped by representation.

---

## THE ARMS AND THE FAIRNESS RULE (§13)

| arm | signal | refusal machinery |
|---|---|---|
| **substrate_residual** | `PointSetDist(query, held-codebook argmax winner)` = the reconstruction mismatch | GRAPH-NATIVE — the EXISTING AbS Term (`predict_pointset_term` + `pointset_error_term`) |
| **net_answer** | — (never refuses) | structurally cannot refuse (softmax argmax) |
| **net_msp** | 1 − max-softmax (Hendrycks 2017) | net's STANDARD post-hoc refusal |
| **net_energy** | −logsumexp(logits) (Liu 2020) | net's stronger post-hoc refusal |
| **net_maha** | min-class Mahalanobis on penultimate features (Lee 2018) | net's STRONGEST post-hoc refusal (added beyond prereg) |
| **net_knn** | k-th-NN distance on penultimate features (Sun 2022) | net's distance-based post-hoc refusal (added beyond prereg) |

**FAIRNESS:** every threshold — the substrate residual tolerance AND every net
cut — is the α-quantile of that arm's OWN signal on the 90 in-dist VALIDATION
images (a matched in-dist false-refuse rate), chosen on in-dist data ONLY, never
on OOD. Every feature detector is fit on TRAIN (in-dist) features ONLY. AUROC/AUPR
are threshold-free. **The strongest net detectors (Mahalanobis, kNN) were added
AFTER the prereg specifically to make the test HARDER for my own claim — a
harder test for one's own hypothesis is always admissible.**

---

## 1 — OOD-DETECTION AUROC (the core calibration comparison)

Main split 129000 (substrate deterministic; nets = mean ± std over 5 seeds
129001–5; per-arm bootstrap CI, 1000 resamples):

| arm | AUROC (mlp / matched input) | AUROC (cnn) |
|---|---|---|
| **substrate_residual** | **0.975  [0.962, 0.986]**  (AUPR 0.992) | — (single modality) |
| net_msp | 0.907 ± 0.007 | 0.798 ± 0.008 |
| net_energy | 0.902 ± 0.012 | 0.640 ± 0.025 |
| net_maha (strongest) | 0.941 ± 0.004 | 0.887 ± 0.012 |
| net_knn | 0.889 ± 0.007 | 0.805 ± 0.006 |

Substrate by OOD-kind: novel **0.963**, noise **0.989**, ambiguous **0.972**.

**The powered test — PAIRED bootstrap on the AUROC difference (same test+OOD
inputs; 2000 resamples; net seed 129001):** the marginal per-arm CIs of substrate
[0.962, 0.986] and Mahalanobis (mean CI-hi 0.966) TOUCH — so the honest,
POWER-THE-GATE test is the paired one:

| substrate − net arm (mlp) | 129000 | 129020 | 129021 | 129022 |
|---|---|---|---|---|
| − net_msp | +0.067 SEP+ | +0.170 SEP+ | +0.110 SEP+ | +0.112 SEP+ |
| − net_energy | +0.070 SEP+ | +0.208 SEP+ | +0.117 SEP+ | +0.113 SEP+ |
| − net_knn | +0.084 SEP+ | +0.105 SEP+ | +0.156 SEP+ | +0.079 SEP+ |
| − **net_maha (strongest)** | **+0.028 SEP+** | **+0.027 (CI −0.004..+0.059)** | **+0.064 SEP+** | **+0.039 SEP+** |

`SEP+` = the 95% paired-bootstrap CI of the difference is entirely > 0. Substrate
beats MSP/energy/kNN CI-separated on ALL 4 splits, and the net's STRONGEST detector
(Mahalanobis) with a POSITIVE point delta on all 4 and CI-separated on 3 of 4 (the
lone marginal split 129020 has CI [−0.004, +0.059] — still positive-centred).

---

## 2 — EXPECTED-COST SURFACE AND THE CROSSOVER (the "useful" claim's home)

Cost per input = P(answer∧wrong)·C_wrong + P(refuse)·C_refuse, C_refuse=1. On
in-dist an answer is wrong iff the classifier is wrong; on OOD every answer is
wrong (true class absent). Swept over OOD-fraction ρ ∈ [0,1] (21 pts) and
C_wrong/C_refuse ∈ {2,5,10,20,50}, at the matched α=0.10 operating point, mlp:

**Substrate_residual has LOWER expected cost than the best-of-all net arms
(min over msp/energy/maha/knn/answer) at EVERY (ρ, ratio) — 21/21 ρ for every
cost ratio.** The substrate is the global argmin across the entire surface.

Why it wins even at ρ=0 (all in-dist): at the matched op-point the substrate ALSO
has higher raw accuracy (§4), so it answers-wrong less; the refusal advantage then
compounds as ρ grows.

**Matched op-point (α target 0.10; empirical in-dist refuse-rates comparable
across arms, 0.033–0.073):**

| arm | in-dist refuse | OOD refuse (detection) |
|---|---|---|
| **substrate_residual** | 0.033 | **0.822** |
| net_energy | 0.047 | 0.587 |
| net_msp | 0.033 | 0.504 |
| net_knn | 0.073 | 0.500 |
| net_maha | 0.040 | 0.491 |

At comparable in-dist false-refuse, the substrate catches **82%** of OOD; the
net's best post-hoc detectors catch **~50–59%**. (Note: Mahalanobis has the best
threshold-free AUROC among the net arms but not the best low-FPR operating-point
detection — AUROC ranks the whole curve, not this specific point.)

---

## 3 — THE CONFABULATION (silent confident-wrong) MEASUREMENT

On OOD, net_answer MUST answer and every answer is wrong. At the matched op-point
(mlp, α=0.10):

- **net_answer confident-wrong fraction of OOD = 0.496** — MSP fails to flag HALF
  of the OOD inputs the net answers wrongly.
- **OOD median MSP = 0.79**; **32.7% of OOD keep MSP > 0.9.** Softmax stays
  confident on novel inputs — the known miscalibration, quantified here.
- Even the net's feature-distance detectors MISS at this op-point:
  net_energy 0.413, net_maha 0.509, net_knn 0.500 of OOD un-flagged.
- **substrate misses only 0.178 of OOD** — it refuses what matches nothing it
  holds, by construction.

This is the failure the representable refusal is meant to prevent, and it is
real: a net answers confidently on half of what it should decline; the
reconstruction residual declines it.

---

## 4 — IN-DIST ACCURACY (reported honestly; a registered expectation INVERTED)

| arm | in-dist test accuracy (main split) |
|---|---|
| **substrate_residual (1-NN)** | **0.980** |
| net (mlp) | 0.937 ± (5 seeds) |
| net (cnn) | 0.908 |

**The prereg predicted the net would win raw in-dist accuracy. It did NOT.** On
Omniglot — few clean classes, a distance/NN-friendly regime — the 1-NN
reconstruction in the native stroke space beats a small net on accuracy AND on OOD
refusal. This is honest and it MATTERS for scope (§6): the task itself favours
distance-based methods, which is part of why the wedge is so wide here.

Robustness splits (substrate / best-net-AUROC / substrate-acc / net-acc):
129020 → 0.940 / 0.755(msp) / 0.900 / 0.823; 129021 → 0.958 / 0.859 / 0.940 /
0.873; 129022 → 0.976 / 0.852 / 0.973 / 0.877. The direction holds on every split.

---

## 5 — VERDICT: **CONFIRM** (with an honest nuance vs the strongest net detector)

- vs the net's STANDARD refusals (MSP, energy) and vs kNN: **CONFIRM** —
  CI-separated (paired) on all 4 splits, and the substrate owns the whole
  expected-cost surface.
- vs the net's STRONGEST honest post-hoc detector (Mahalanobis on features): the
  substrate STILL wins (positive delta on all 4 splits, CI-separated on 3 of 4) —
  but the AUROC gap narrows from ~0.07 (vs MSP) to ~0.03. **The differentiator is
  DISTANCE/RECONSTRUCTION-based refusal.** The net only approaches the substrate
  when you BOLT ON a distance detector — i.e. reproduce, post-hoc and on learned
  features, the very thing the substrate does NATIVELY and while ALSO recognising.
  That is the wedge, sharpened rather than blunted: a softmax head cannot refuse;
  its owner must add a second mechanism; the substrate's ONE mechanism recognises
  and refuses.

---

## 6 — SCOPE: MECHANISM-PROVEN, NOT BENCHMARK VALUE (the arc's standing rule)

- **Small and in-tree:** 30 classes, 150 in-dist-test + 450 OOD, one task, one
  engine, commodity CPU. This is a MECHANISM measurement, not a benchmark result.
- **The task favours the mechanism.** Omniglot is the canonical regime where
  nearest-exemplar / Modified-Hausdorff distances are strong for BOTH accuracy and
  OOD. On a high-dimensional natural-image task where a net's learned features
  dominate raw-space distance, the ordering could change — UNRUN here.
- **Synthetic OOD.** noise and ambiguous are constructed; novel-class is real but
  from the same corpus. A harder, more natural OOD distribution is unrun.
- **The net is small.** A larger net, heavier augmentation, or a better feature
  space would raise net accuracy and could raise Mahalanobis AUROC further — the
  vs-Mahalanobis margin is where that pressure would land first.
- **What DID transfer:** the substrate's refusal signal is the EXISTING
  graph-native AbS residual (no new mechanism), and it is a measured, CI-separated
  differentiator over the standard net refusals at a matched operating point on a
  cost-sensitive task. That is the first useful number of the arc.

**The regime that WOULD narrow or invert it (named, per the prereg):** a task
where (a) raw-space distance is a WEAK feature (natural images, large intra-class
variation) so the substrate's 1-NN residual is poorly calibrated, AND (b) the net
learns a strong feature space where Mahalanobis/kNN OOD detection is near-perfect.
There the substrate would need to refuse in a LEARNED space (its own codebook over
learned features), not raw strokes — a different rung.

---

## 7 — WHAT I GOT WRONG

1. **Two inhomogeneous-array bugs.** `per_stroke=True` trajectories are
   variable-length (48±3 points) → `np.array` raised; and the ambiguous
   `to_trajectory_strokes` on two figures returned off-by-rounding lengths. Both
   caught in a pre-run smoke test (not in the committed numbers). Fixed to
   `per_stroke=False` whole-trajectory resample (also the FAIRER choice — identical
   fixed-length input for both arms) and to a concat-points resample for ambiguous.
2. **I nearly STRAWMANNED the net.** My first design gave the net only MSP +
   energy. That is exactly the "do NOT strawman the net" trap: a distance-based
   OOD detector (Mahalanobis/kNN on features) is the net's strongest honest
   post-hoc refusal and closest to the substrate's own mechanism. I added both
   BEFORE writing any verdict. It narrowed the gap (vs Mahalanobis 3/4 splits
   separated, not 4/4) — a more honest and more interesting result.
3. **The marginal-CI-overlap trap.** The per-arm bootstrap CIs of substrate and
   Mahalanobis TOUCH ([0.962,0.986] vs mean-CI-hi 0.966). Comparing marginal CIs
   is the WRONG, under-powered test when both signals are on the SAME inputs. The
   right test is a PAIRED bootstrap on the difference — which I then computed
   (SEP+ vs Mahalanobis on 3/4 splits). POWER THE GATE, per the arc's standing
   rule.
4. **A registered EXPECTATION was wrong.** I pre-registered that the net would win
   raw in-dist accuracy. It did not (substrate 0.980 vs 0.937) — the task is
   NN-friendly. Reported plainly rather than buried, because it is load-bearing
   for scope: part of why the wedge is wide here is that the task favours the
   mechanism.
5. **A cosmetic dead loop** (`for ci in range(K): pass`) and an unused int-key
   class-lookup path survive in `substrate_residuals` (the winner's class is read
   from its node name, which is what drives the 0.980 accuracy). Harmless, not
   load-bearing, disclosed.
