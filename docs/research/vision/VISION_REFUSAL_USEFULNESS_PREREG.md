# IS THE REPRESENTABLE REFUSAL WORTH ANYTHING? — PRE-REGISTRATION

**The first "useful-wedge" measurement of the arc.** Not "can the substrate
see / refuse?" (measured: `VISION_REFUSAL_REPRESENTABLE_RESULTS.md`,
`VISION_REFUSAL_CAPACITY_RESULTS.md`) but: **is the substrate's representable
refusal a MEASURED differentiator over a NET's best refusal on a task with a cost
for being confidently WRONG?**

- **branch (as observed):** `worktree-agent-a27cdb8a64e124f5d`.
- **base SHA (as observed):** `a79b3d5c10573af8b06a0f6b252206bb325ad823`.
- **seed block:** **129000–129999.**

---

## 0 — THE CLAIM UNDER TEST (register a direction BEFORE any number)

On a recognition task with a cost for confident-wrong answers, the substrate's
**representable refusal** — a **reconstruction-residual / analysis-by-synthesis**
signal (reconstruct the best-matching held codebook quantum, residual = the
mismatch, refuse if residual exceeds a tolerance) — beats a **net's** refusal
options **on OUT-OF-DISTRIBUTION inputs**, because a net's softmax confidence is
MISCALIBRATED OOD (overconfident on novel inputs) while the reconstruction
residual is calibrated by construction (a thing that matches NOTHING you hold has
a large residual).

The governing prior fact (measured, not assumed):
**"a comparison can be FALSE, a selection cannot"** — the earned refuser decides
by exact comparison against a RECONSTRUCTION; a softmax head is a SELECTION and is
structurally forced to answer. This rung asks whether that asymmetry is WORTH
anything.

**Registered expectation:** CONFIRM is plausible but NOT assumed. FALSIFY is
first-class and fine — modern net OOD detectors (MSP, energy) are strong, and the
substrate residual is itself a distance-to-nearest-exemplar that can be
miscalibrated. I register that I will report whichever way it falls, will NOT tune
to win, and will NOT weaken the net.

---

## 1 — THE TASK, STATED EXACTLY (fixed before measuring)

**Recognition task:** Omniglot online stroke recognition — the arc's natural
held-codebook task (`omniglot_one_shot.py`; the SC+TPS / AbS line; real human ink;
`domains/omniglot_world.py`, `domains/recognition_graph.py`). Background split, 30
alphabets, 20 drawers per character.

**Class split (fixed by data-split seed 129000; robustness over 129020–129022):**
- **KNOWN alphabets** = the first 15 background alphabets (sorted).
- **OOD alphabets** = the last 15 background alphabets (disjoint).
- **In-distribution classes** = **K = 30** characters sampled from the KNOWN
  alphabets (each has 20 drawings). These are the classes the net is trained on
  and the codebook holds.

**Drawer split per in-dist class (20 drawings each):**
- drawers 0–11 (12) → **net training set** AND **substrate codebook exemplars**
  (BOTH arms see the SAME in-dist training data — fairness).
- drawers 12–14 (3) → **in-dist VALIDATION** (threshold-setting ONLY; 90 images).
- drawers 15–19 (5) → **in-dist TEST** (150 images).

**OOD construction (three kinds, ~150 each, stated exactly):**
- **novel-class** — drawings of characters from the OOD alphabets (classes the
  codebook does NOT hold and the net was never trained on).
- **noise** — pen-like but meaningless trajectories: a normalized random-walk
  (cumulative Gaussian steps) resampled + normalized by the SAME pipeline as a
  real drawing, so it is a valid trajectory of the same shape/scale that matches
  no held class.
- **ambiguous** — two DISTINCT in-dist-test drawings' strokes concatenated into
  one figure (two characters overlaid): a genuinely ambiguous input whose true
  single label is undefined.

**Evaluation pool:** 150 in-dist-test (is-OOD=0) + ~450 OOD (is-OOD=1).

---

## 2 — THE ARMS (all four; the net given its BEST honest refusal)

1. **net_answer** — a properly-trained small classifier, softmax argmax, MUST
   answer. The structurally-cannot-refuse baseline.
2. **net_msp** — the SAME net + max-softmax-probability threshold (Hendrycks &
   Gimpel 2017 — the STANDARD OOD baseline; the fair "net can refuse" arm).
3. **net_energy** — the SAME net + energy score `E = -T·logsumexp(logits/T)`
   (Liu et al. 2020; T=1), a stronger modern OOD detector.
4. **substrate_residual** — the graph-native reconstruction-residual refusal:
   evaluate the substrate's held distance Term (`PointSetDist`, order-invariant
   Modified-Hausdorff — the EXISTING AbS machinery in `recognition_graph.py`) over
   the held codebook, take the argmax winner (`predict_pointset_term`), and read
   the residual = `PointSetDist(query, winner)` = the min mismatch. Refuse if the
   residual exceeds tolerance. This IS "reconstruct the best-matching held quantum,
   residual = mismatch, refuse if residual > tolerance." No new refusal mechanism.

**Net representation (fairness note, registered):** the PRIMARY net is an MLP on
the SAME 48×2 trajectory the substrate consumes (identical inputs — the only
difference is softmax-selection vs reconstruction-residual, which is the wedge). A
SECONDARY net is a small CNN on a 28×28 raster of the strokes (the net's natural
best modality) so the net is not handicapped by representation. Both nets reported.

---

## 3 — FAIRNESS: THE MATCHED OPERATING POINT (§13; the whole ballgame)

**Every refusal threshold — net MSP cut, net energy cut, substrate residual
tolerance — is set by ONE principled rule: a matched in-distribution false-refuse
rate.** For a target α, each arm's threshold τ is the α-quantile of that arm's own
refusal signal on the 90 in-dist VALIDATION images, so each arm refuses exactly
α of held-out IN-DIST inputs. **Thresholds are chosen on in-dist VAL data ONLY,
NEVER on OOD.** Primary α = 0.10; the cost surface is also swept over
α ∈ {0.05, 0.10, 0.20} for robustness. A threshold picked to win is a §13
violation and voids the result — registered.

The core **AUROC / AUPR** comparison is THRESHOLD-FREE (a ranking of the refusal
signal against the is-OOD label), so fairness there is automatic.

---

## 4 — METRICS (the useful numbers, fixed before measuring)

1. **OOD-detection AUROC and AUPR** of each refusal signal (substrate residual,
   net MSP, net energy) for the binary is-OOD label — overall and per OOD-kind.
   Bootstrap 95% CIs (1000 resamples, seeded from the block).
2. **Selective risk / expected cost:** per input, cost = P(answer∧wrong)·C_wrong +
   P(refuse)·C_refuse, with C_refuse < C_wrong. On in-dist an answer is wrong if
   the classifier is wrong; on OOD every answer is wrong (true class absent).
   SWEEP OOD-fraction ρ ∈ [0,1] × C_wrong/C_refuse ∈ {2,5,10,20,50}; report each
   arm's expected-cost surface and the CROSSOVER region where refusal wins.
3. **Confident-wrong (silent confabulation) rate:** on OOD, the fraction
   net_answer emits at MSP ≥ the matched operating point (a confident wrong
   label); report whether MSP/energy actually catches it (per-kind AUROC).
4. **In-dist accuracy** of every arm (net argmax; substrate 1-NN). Reported
   HONESTLY — the net likely wins raw in-dist accuracy; the claim is about refusal
   calibration where wrong is costly, not accuracy.

---

## 5 — THE DISCRIMINATOR (registered)

- **CONFIRM** = substrate_residual has higher OOD AUROC than net_msp (and ideally
  net_energy) at the matched operating point, AND lower expected cost across a
  realistic C_wrong/C_refuse × ρ range. A measured differentiator — the first
  useful number.
- **DEGRADE** = wins only in part of the cost/OOD space, or beats MSP but not
  energy. Report the exact region and which net baseline it fails to beat.
- **FALSIFY** = net_msp/energy matches or beats the substrate residual → on this
  task the net's post-hoc refusal is good enough; the wedge is NARROWER than
  believed. Diagnose WHY (OOD too easy? residual also miscalibrated? task not one
  where AbS helps?) and name the OOD regime that WOULD separate them. A FALSIFY is
  a real, valuable finding — I will NOT rescue it by tuning or weakening the net.

---

## 6 — ARCHITECTURE (project core rule)

The substrate's refusal is GRAPH-NATIVE: it reuses the EXISTING held distance Term
(`PointSetDist`) + argmax + residual read (`recognition_graph.py`), the same AbS
the arc built. NO new agent decision in Python. The NET is a measured BASELINE (a
host-side comparison model — admissible, it is being measured against, not agent
logic). The comparison harness is mechanical host I/O. **Expected: NO Rust, NO new
seed** (a measurement reusing existing machinery). If I find I need Rust I will
STOP and report why.

---

## 7 — DISCIPLINE (registered commitments)

- **PROVENANCE its own step; build my own engine (`scripts/engine_build.sh`);
  re-verify the fingerprint after; print `provenance_line()` from inside the
  measuring process; assert `source_match in ("own","shared")` — never pin a
  literal hash.** ORACLE `rung7_vision_bench.sh` = 222/0 BEFORE and AFTER.
- **§13:** every threshold falls out of the matched-in-dist-FPR rule; nothing
  tuned on OOD. CPU ≤2 workers (torch threads=2); record `os.getloadavg()`; NO
  wall-clock verdict (net train/infer cost recorded as data only).
- Fix RNG seeds from block 129000–129999 (data-split 129000; nets 129001–129005;
  bootstrap 129100; robustness splits 129020–129022). Report per-seed variance and
  Wilson/bootstrap CIs. POWER THE GATE — deltas within the per-episode step are
  not results.
- VERIFY ON THE PRODUCT — every number read from committed JSON; remember
  `native.evaluate()` returns TUPLES not lists; check every read-back.
- Report what I got WRONG. State scope honestly: small, in-tree, one task — a
  synthetic-proven mechanism is not benchmark value; report BOTH.

---

## 8 — `check_claim` VERBATIM (§3 clause 8 — GATED, before any number)

```
$ python3 scripts/seed_claim.py 129000 129999
SEED CLAIM 129000-129999: CLEAN -- no collision DETECTED.
  Scope: 836 files with seed sinks; 546 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**Unknown sinks in my measurement file:** my script seeds numpy/torch with LITERAL
elements of 129000–129999 (data-split 129000; net seeds 129001–129005; bootstrap
129100; robustness 129020–129022). Any `default_rng(seed)` in a loop form the
static tool cannot resolve is disclosed here, not buried; the values are literal
in-block integers.
