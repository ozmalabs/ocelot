# DOES THE REPRESENTABLE REFUSAL SURVIVE THE NET'S HOME TURF? — PRE-REGISTRATION

**The HONEST BOUNDARY TEST that `VISION_REFUSAL_USEFULNESS_RESULTS.md` (block
129000) named for itself.** 129000 CONFIRMED, on Omniglot, that the substrate's
reconstruction-residual refusal (a COMPARISON — analysis-by-synthesis) beats a
net's best post-hoc OOD detectors (MSP / energy / Mahalanobis / kNN, all
SELECTION-derived or feature-distance). **But it flagged its own confound:**
Omniglot is NN / raw-distance-friendly (the substrate 1-NN even won in-dist
accuracy), so the win could be about the REPRESENTATION (raw-space distance
works) rather than the MECHANISM (comparison vs selection). This rung runs the
test in **the regime designed to narrow or invert the wedge: natural images,
where raw-pixel distance is WEAK and a net's LEARNED features dominate.**

- **branch (as observed):** `worktree-agent-a49a32b1fe3effbf5`.
- **base SHA (as observed):** `71ef444d75eb8e5016d7a602245c7f43cd0b136e` (the
  129000 ledger commit).
- **seed block:** **130000–130999.**

---

## 0 — THE CLAIM UNDER TEST (register a direction BEFORE any number)

To separate MECHANISM from REPRESENTATION, run TWO comparisons on a natural-image
OOD-detection task:

1. **END-TO-END (the practical number).** A properly-trained CNN's full OOD
   pipeline (learned features + MSP / energy / Mahalanobis / kNN) vs the
   substrate's full reconstruction-residual pipeline in RAW pixel space. The
   honest "who wins on the net's home turf."
2. **REPRESENTATION-CONTROLLED (the decisive one).** Hold the representation
   FIXED — take the NET'S OWN learned penultimate features — and compare the two
   REFUSAL MECHANISMS in that SAME feature space:
   - the substrate's COMPARISON mechanism: **reconstruction-residual /
     distance-to-nearest-held-prototype** (`substrate_residual_feat`), vs
   - the net's SELECTION-derived confidence: **MSP / energy**
     (`net_msp` / `net_energy`).

   Same features, different refusal mechanism. This isolates whether the wedge is
   **mechanism-deep** (comparison beats selection even in the net's own features)
   or was **representation-luck** (it evaporates once features are learned).

**The governing prior fact (measured, not assumed):** "a comparison can be
FALSE, a selection cannot" — the earned refuser decides by exact comparison
against a RECONSTRUCTION; a softmax head is a SELECTION structurally forced to
answer. 129000 showed that asymmetry is worth something in a distance-friendly
regime. This rung asks whether it is mechanism-deep or representation-bound.

**Registered expectation:** genuinely open. On natural images I EXPECT
`substrate_residual_raw` (raw-pixel distance) to be WEAK — that is the hostile
representation. The decisive question is `substrate_residual_feat` vs MSP/energy.
The OOD literature suggests feature-distance methods (kNN / Mahalanobis) often
beat MSP/energy on near-OOD, which would support CONFIRM at the mechanism level —
but the substrate needing the NET'S features to compete would be a DEGRADE
(bounded). FALSIFY is first-class, EXPECTED-plausible and FINE. I register that I
will report whichever way it falls, will NOT tune to win, and will NOT weaken the
net (it gets its STRONGEST honest features + detectors).

---

## 1 — THE TASK, STATED EXACTLY (fixed before measuring)

**Dataset:** CIFAR-10 (`var/ood_data/cifar-10-python.tar.gz`, the canonical
32×32×3 natural-image benchmark; SHA recorded in results). Downloaded in-tree
(not committed — `data/`-class artifact); the limitation (constructed in-tree,
not a packaged loader) is stated in the results §scope.

**Class split (fixed; robustness over data-split seeds 130020–130022):**
- **IN-DIST classes** = CIFAR-10 classes **0–5** (airplane, automobile, bird,
  cat, deer, dog). The CNN is trained ONLY on these; the substrate codebook holds
  ONLY these.
- **NEAR-OOD classes** = CIFAR-10 held-out classes **6–9** (frog, horse, ship,
  truck) — natural images, SAME dataset low-level statistics, semantically
  related but NOVEL. **This is where selection-confidence fails hardest and is
  the discriminating case.**

**Per-class split (in-dist):**
- **train** = M=2000 images/class sampled from the CIFAR TRAIN split (data-split
  seed 130000) → net training AND substrate codebook exemplars (BOTH arms see the
  SAME in-dist data).
- **val** = 200 images/class from a DISJOINT slice of the CIFAR TRAIN split →
  in-dist VALIDATION (threshold-setting ONLY; 1200 images).
- **test** = 500 images/class from the CIFAR TEST split → in-dist TEST (3000
  images).

**OOD pools (reported near vs far SEPARATELY):**
- **NEAR-OOD** (≈2000): CIFAR-10 held-out classes 6–9 from the CIFAR TEST split.
- **FAR-OOD** (three sub-kinds, reported separately AND pooled):
  - **svhn** — SVHN test crops (`var/ood_data/svhn_test_32x32.mat`), a DIFFERENT
    natural-image dataset (street-view digits): the canonical CIFAR far-OOD.
  - **gauss** — Gaussian-noise images in the SAME normalized pixel space.
  - **corrupt** — in-dist TEST images destroyed by a severe corruption
    (pixel-block shuffle, seed 130002): same marginal pixel statistics, no object.

**Net representation (fairness note, registered):** the net is a real CNN on the
32×32×3 image — the natural modality; there is NO handicapped alternative
representation to add (unlike Omniglot's trajectory-vs-raster). The net gets its
strongest honest features and detectors.

---

## 2 — THE ARMS (the net given its BEST honest refusal)

| arm | representation | mechanism | signal |
|---|---|---|---|
| **net_answer** | net logits | SELECTION (cannot refuse) | softmax argmax; MUST answer |
| **net_msp** | net logits | SELECTION | 1 − max-softmax (Hendrycks 2017) |
| **net_energy** | net logits | SELECTION | −logsumexp(logits) (Liu 2020) |
| **net_maha** | net penult. features | comparison-in-features | min-class Mahalanobis (Lee 2018) |
| **net_knn** | net penult. features | comparison-in-features | k-th-NN distance (Sun 2022) |
| **substrate_residual_raw** | RAW pixels | COMPARISON (AbS) | nearest-held-exemplar L2 residual — the END-TO-END substrate arm |
| **substrate_residual_feat** | net penult. features | COMPARISON (AbS) | nearest-held-prototype L2 residual — the REPRESENTATION-CONTROLLED arm |

**The substrate's COMPARISON mechanism = "nearest-prototype reconstruction
residual":** `r(x) = min over held prototypes p of ‖x − p‖` — reconstruct the
query by its nearest held exemplar, residual = the mismatch, refuse if residual >
tolerance. This is the SAME analysis-by-synthesis the arc built and 129000
measured (`predict_pointset_term` + `pointset_error_term`; `PointSetDist` is its
trajectory realization — the ORDER-INVARIANT distance to the argmin held
codebook winner). For non-trajectory image/feature vectors the faithful
realization is the L2-nearest-prototype residual (the degenerate single-vector
case of the same argmin-distance-then-residual op; the DSL already grades
numeric-vector leaves by Euclidean distance — `term.rs::feature_distance`). It is
computed host-side IDENTICALLY across the raw and feature representations, so the
ONLY thing that varies between `substrate_residual_raw` and
`substrate_residual_feat` is the representation — which is the whole point of the
rung. Primary prototype set = the held TRAIN exemplars (1-NN, exactly the AbS
reconstruction residual = kNN with k=1); nearest-class-centroid residual also
reported as a check.

**`net_maha` / `net_knn` are, honestly, comparison-in-feature-space methods** —
they are the net's STRONGEST post-hoc detectors AND they are the substrate's own
comparison mechanism transplanted into learned features (`net_knn` ≈
`substrate_residual_feat` at k>1). This is not hidden: it is the crux. The
DECISIVE contrast is COMPARISON-in-features (residual_feat / kNN / Maha) vs
SELECTION-in-features (MSP / energy) in the SAME net.

---

## 3 — FAIRNESS: THE MATCHED OPERATING POINT (§13; the whole ballgame)

**Every refusal threshold — every net cut AND the substrate residual tolerance
(raw and feat) — is set by ONE rule: a matched in-distribution false-refuse
rate.** For target α, each arm's threshold τ = the (1−α) quantile of that arm's
OWN signal on the 1200 in-dist VALIDATION images, so each arm refuses exactly α
of held-out IN-DIST inputs. **Thresholds are chosen on in-dist VAL data ONLY,
NEVER on OOD.** Primary α = 0.10; cost surface swept over α ∈ {0.05, 0.10, 0.20}.
Every feature detector (Maha, kNN) and every prototype set is fit on TRAIN
(in-dist) features ONLY. A threshold picked to win voids the result.
**AUROC / AUPR are threshold-free** (a ranking of the refusal signal against the
is-OOD label), so fairness there is automatic.

---

## 4 — METRICS (fixed before measuring; same rigor as 129000)

1. **OOD-detection AUROC and AUPR** of every arm for the binary is-OOD label,
   **NEAR-OOD and FAR-OOD reported SEPARATELY** (and far broken by sub-kind).
   Bootstrap 95% CIs (1000 resamples, seeded from the block).
2. **PAIRED bootstrap on the AUROC DIFFERENCE** (same inputs — the powered test;
   2000 resamples). Decisive pairs, near AND far:
   - `substrate_residual_feat − net_msp`, `− net_energy` (the
     representation-controlled decisive test),
   - `substrate_residual_feat − net_maha`, `− net_knn` (comparison vs comparison,
     same features),
   - `substrate_residual_raw − best-net-arm` (end-to-end).
   Marginal per-arm CIs UNDER-power the comparison; the paired test is the gate.
3. **Expected-cost surface:** cost = P(answer∧wrong)·C_wrong + P(refuse)·C_refuse,
   C_refuse=1. In-dist wrong iff classifier wrong; OOD every answer wrong. Swept
   over OOD-fraction ρ ∈ [0,1] (21 pts) × C_wrong/C_refuse ∈ {2,5,10,20,50}, at
   the matched op-point. Best-net arm vs `substrate_residual_raw` AND vs
   `substrate_residual_feat`, near and far.
4. **Confident-wrong (silent confabulation) rate:** on NEAR-OOD, the fraction
   `net_answer` emits a confident wrong label at the matched op-point; and the
   OOD MSP distribution (median, frac > 0.9).
5. **In-dist accuracy** of every arm (net argmax; substrate 1-NN raw; substrate
   1-NN feat). **Reported HONESTLY — I EXPECT the net to WIN in-dist accuracy on
   natural images** (the inverse of Omniglot, where the 1-NN won). The claim is
   about refusal, not accuracy.

---

## 5 — THE DISCRIMINATOR (registered BEFORE any number)

- **CONFIRM** = the comparison-based refusal beats selection-based refusal EVEN
  IN THE NET'S OWN LEARNED FEATURE SPACE (`substrate_residual_feat` >
  `net_msp`/`net_energy`, paired-bootstrap CI-separated), AND is
  competitive/better end-to-end on natural images → the wedge is MECHANISM-DEEP,
  survives the hostile regime. The strongest possible result.
- **DEGRADE** = it wins on far-OOD but not near-OOD, OR wins in-feature-space but
  `substrate_residual_raw` can't reach competitive features end-to-end (so the
  substrate needs the NET'S features to compete) → the wedge is real but BOUNDED;
  state exactly where.
- **FALSIFY** (first-class, honest, EXPECTED-plausible, FINE) = in learned
  feature space the net's selection-derived detectors (MSP/energy) match or beat
  `substrate_residual_feat` → 129000's win WAS raw-distance-friendliness, and the
  useful wedge is CONFINED to distance-friendly regimes. If so I say it plainly,
  quantify the confinement, and state what it means for the "useful" claim (it
  narrows to tasks where a held reconstruction in a cheap representation is
  meaningful — still a real class, but bounded). I will NOT rescue by weakening
  the net or tuning.

---

## 6 — ARCHITECTURE (project core rule)

The substrate's refusal is GRAPH-NATIVE: the reconstruction-residual /
nearest-prototype-residual COMPARISON is the EXISTING AbS mechanism (the same one
`recognition_graph.py` + `PointSetDist` realize for trajectories; the L2 leaf
distance is `term.rs::feature_distance`). Realizing the identical mechanism in
two representations (raw pixels, net features) is mechanical host I/O measuring a
MECHANISM — no new agent decision in Python. The NET and its feature extractor
are measured BASELINES (host-side comparison models — admissible, they are being
measured against, not agent logic). **Expected: NO Rust, NO new seed** (a
measurement reusing existing machinery). If I find I need Rust I will STOP and
report why.

---

## 7 — DISCIPLINE (registered commitments)

- **PROVENANCE its own step; build my own engine (`scripts/engine_build.sh`);
  re-verify the fingerprint after; print `provenance_line()` from inside the
  measuring process; assert `source_match in ("own","shared")` — never pin a
  literal hash.** ORACLE `rung7_vision_bench.sh` = **222/0 BEFORE and AFTER**
  (`data/` symlinked).
- **§13:** every threshold falls out of the matched-in-dist-FPR rule; nothing
  tuned on OOD. CPU ≤2 workers (`torch.set_num_threads(2)`,
  `OMP/MKL_NUM_THREADS=2`); record `os.getloadavg()`; **NO wall-clock verdict**
  (this is NOT a timing rung — AUROC/cost is the verdict; net train cost recorded
  as data only).
- Fix RNG seeds from block 130000–130999: data-split 130000 (robustness
  130020–130022); net seeds 130001–130005; corruption 130002; bootstrap 130100.
  Report per-seed variance and bootstrap CIs. **POWER THE GATE** — deltas within
  the per-episode step are not results; the paired bootstrap is the powered test.
- VERIFY ON THE PRODUCT — every number read from committed
  `results/refusal_natural.json`; `native.evaluate()` returns TUPLES not lists;
  check every read-back.
- Report what I got WRONG. State scope honestly: small, in-tree, one dataset — a
  synthetic/small-scale-proven mechanism is not benchmark value; report BOTH.

---

## 8 — `check_claim` VERBATIM (§3 clause 8 — GATED, before any number)

```
$ python3 scripts/seed_claim.py 130000 130999
SEED CLAIM 130000-130999: CLEAN -- no collision DETECTED.
  Scope: 837 files with seed sinks; 553 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**Unknown sinks in my measurement file:** my script seeds numpy/torch with
LITERAL elements of 130000–130999 (data-split 130000; net seeds 130001–130005;
corruption 130002; bootstrap 130100; robustness 130020–130022). Any
`default_rng(seed)` in a loop form the static tool cannot resolve is disclosed
here, not buried; the values are literal in-block integers.
