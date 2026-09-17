# Number-Qualia Experiment — Design Document (DESIGN ONLY, not implemented)

> **Status:** design/spec only. No code, no seeds, no `.so`, nothing under `/applications`, no edits to protected/read-only files, conceptualizer untouched. Everything proposed below is *additive* and Python/JSON-only. Build guards restated in the final section.

---

## 0. Overview

**Theory under test.** A number's *quale* is the **felt compression of its intrinsic structural relationships** — primality; multiplicative isolation within a set; full-length repeating-decimal cycle (e.g. `1/7 = 0.142857…`); modular/residue behavior; how it divides/tiles. The quale is **notation-independent** and **substrate-independent**. The **glyph's** outlier shape (7 "looking unlike" the other digits) is **downstream** of the quale, not its cause.

Canonical instance: within 1–10, people pick 7 as "most random/distinct" because 7 is the *structural* outlier — the only prime in the set with neither a proper factor nor a multiple inside 1–10, a maximal 6-digit decimal cycle, an awkward modulus — and its glyph inherits that outlierness.

**What this document is.** A rigorous, non-circular experiment *design* that tests this theory using **only existing substrate features** plus a small, additive, structure-only seed. It specifies six sub-experiments (a–f), each with a seed-mapping, a readout, a falsifiable prediction, a control arm, and an honest negative. It is skeptical and mechanism-first: every claim maps to a concrete callable and a concrete number.

**The single most important discipline — non-circularity.** 7's outlierness must **emerge** from *neutral, per-number structural properties* fed through `concept_signature` + a real distance metric. It must **never be planted**. To make the emergent result *credible*, we run a deliberately **circular control arm** (a hand-coded `special=1` flag / a hand-set field spike on 7) side by side, so the reader can see exactly what circularity would look like — and see that the theory arm does not do it.

**Steering honored (see note at end).** "Qualia and connection are already defined within the substrate, so the shape should fall out." The design seeds **only neutral structural connections** (edges) and lets the **qualia coordinates fall out** of the CAN fields via `concept_signature`; the **glyph/shape is never seeded** — it is read downstream from the emergent signature geometry.

---

## 1. The non-circularity discipline (stated up front, before any sub-experiment)

Circularity is the failure mode that would make this whole exercise worthless: if we tell the substrate that "7 is special" and then it reports that 7 is special, we have measured our own input. To prevent that, the design binds itself to five rules. Every sub-experiment must satisfy all five.

1. **Type-uniform seeding.** Every number gets the *same edge types and attr keys*. Only the **fillers** differ (7 has different divisors than 6). No number — least of all 7 — carries an attr key or edge type the others lack. Concretely: `divides` / `has_factor` edges, `residue_mod_k` edges for `k ∈ {2,3,4,5}`, one neutral scalar attr `decimal_cycle_length`, and `is_a number`. Nothing named `special`, `distinct`, `outlier`, `random`, or `salient`.

2. **No hand-set felt fields in the theory arm.** We do **not** write `identity_field`/`state`/`external_field` on 7 to encode salience. The felt (dynamical) coordinates must be **produced** — either by letting the CAN dynamics relax, or by deriving a felt scalar from a **neutral structural quantity** computed uniformly for all numbers (e.g. divisor-count deficit; see §3). The derivation function is identical for every number; it does not contain the token "7" or a hand-tuned per-number table.

3. **Shape is read, never written.** No `sharpness` field, no `vocab:shape` keyword, no glyph attr is seeded on any number in the theory arm. The "shape axis" only ever appears as a **downstream read** or an *added* axis whose correlation with structure is the thing being measured (§ sub-exp g / claim 3).

4. **Provenance proof.** Wrap all reads with an `AskSpy`-style guard (from the capability harness) asserting zero external-answerer calls, and assert via the qualia-schema invariants (`dynamical_is_produced_not_hand_set`, `no_can_bookkeeping`) that no felt coordinate on any number was hand-set. If Arm 1 ever reads a tuple that traces to a planted flag, the run is void.

5. **The contrast control is mandatory.** Every "7 is the outlier" result from Arm 1 must be reported *next to* the Arm 2 (circular) result on the identical harness. The emergent finding is only credible as the difference between the two arms.

**Operational definition of "planted."** A property is *planted* if (i) it appears as a distinct attr key/edge type on 7 but not on other numbers, OR (ii) it is a felt-field value written directly onto a number node rather than produced by dynamics/derived by a uniform structural function. Everything else is *structural seeding* and is allowed.

---

## 2. Substrate features used (from the survey; all confirmed callable)

| Feature | Callable / artifact | Role in this design |
|---|---|---|
| Multi-axis signature | `domains/analogy_search.py::concept_signature(substrate, node, *, overlay=False, observer=None)` (L442) → frozenset of `(dimension, predicate, value)` | Primary readout: a number → its coordinates in qualia space |
| Qualia codebook | `seeds/qualia_space.json` (16 QualiaDimension, 34 DimensionEdgeRole, 1 QualiaSchema) + `domains/qualia_schema.validate_qualia_space` | Defines the axes the felt coordinates fall onto; invariants police non-circularity |
| CAN field → dynamical axis | field attrs `state`/`identity_field`/`external_field`/…; `_dynamical_relations` (L299) | How a felt coordinate lights up — **produced/derived, never planted** |
| Observer aperture + grain | `_observer_aperture(substrate, observer)` (L140); `substrate_runner.observer(s, name, grain)`; `FINE`/`COARSE` grain maps | "Mathematical taste": existence-gate axes and re-quantize; sub-exp (e) |
| Signature distance metrics | `substrate_rs`: `l2_signature_distance`, `categorical_signature_distance`, `shape_signature_distance` + neighbour thresholds; project via `substrate_runner.item_signature_vector` | Quantify outlierness/similarity numerically |
| Relational edges | `add_edge_unchecked(src, type, tgt, attrs)` (write); `neighbours`/`in_neighbours` (read); edge-type→dimension role table | Carry primality / factor / multiple / residue structure into `relational:` and lexical axes |
| Gated dimension-minting | `domains/minting_train_of_thought.py::run_minting_train_of_thought(...)` (L120); `domains/reflective_faculty.py::induce_concern(...)` (L1318) | Sub-exp (d): coin a structural axis mid-reasoning — the graph owns the mint decision |
| Analogy loop | `find_analogies(...)` (L1069) | Sub-exp (b): which numbers "feel alike" |
| Harness / cost | `tests/capability/minting/runners/substrate_runner.py`: `build_category`, `build_multi_category`, `observer`, `item_signature_vector`, `item_distance_from_setpoint`, `capture_minting_cost`, `AskSpy` | Copy this harness shape; measure minting cost; assert teacher-free |

**Additive pieces that must be built (thin, Python/JSON only; no `.so` rebuild, no edits to existing axes):**

- **A. Number-corpus builder** — one `Concept` per integer with **neutral structural edges/attrs only** (rule 1). Mirrors `build_category`'s shape (loads VOCAB+QUALIA seeds, clears `_QUALIA_SCHEMA_CACHE`).
- **B. Structural→felt derivation** — a single uniform function mapping a neutral structural scalar to a field value so a `dynamical:` axis becomes a *produced* coordinate (rule 2). Plus a deterministic tokenizer→int map so token-valued relational tuples can be projected to a fixed integer vector for the native L2/categorical metrics (or route similarity through the analogy set-intersection instead).
- **C. Circular control arm** — a hand-set `special=1` attr and/or a hand-set `identity_field` spike on 7 (rule 5).
- **D. Set/grain driver** — sweep `{1–6, 1–10, 1–12}` (via `build_multi_category` shape) × `{FINE, COARSE}` observers.

---

## 3. Shared seed (arm-agnostic structure) and the derivation of felt coordinates

**The neutral structural facts, per number `n` in the working set `S`:**

- **Divisors within S:** `has_factor` edge `n → d` for each proper divisor `d ∈ S`. (7 in 1–10: none. 6 in 1–10: 2, 3.)
- **Multiples within S:** `divides` edge `n → m` for each `m ∈ S` with `n | m`, `m ≠ n`. (7 in 1–10: none. 2 in 1–10: 4,6,8,10.)
- **Residues:** `residue_mod_k` edge `n → R_{k,r}` to a shared residue-class node, for `k ∈ {2,3,4,5}`. (Same four edges for every number; only the target class differs.)
- **Decimal cycle length:** neutral scalar attr `decimal_cycle_length = period(1/n)` (7 → 6; 3 → 1; 2,5 → 0; 6 → 1). A plain integer attr, identical key for all.
- **Type:** `is_a number`.

None of these encodes "distinctness." *Multiplicative isolation* is **not** a seeded attr — it is the **emergent** fact that 7 has zero `has_factor` and zero `divides` edges inside 1–10, which the signature/metric must *discover*.

**Deriving a produced felt coordinate (rule 2).** Define one uniform scalar for all `n`:

```
connectivity(n) = (#has_factor edges of n within S) + (#divides edges of n within S)
deficit(n)      = max_conn(S) - connectivity(n)        # neutral, same formula for all n
```

Then set the field that feeds a **graded** dynamical axis (e.g. `identity_field` → `dynamical:commitment`, or the neutral `abstraction_field` layer) from `deficit(n)` through a **monotone, per-number-blind** transform — exactly the discipline `_typicality_to_field` already models (monotone in a rank, exact constants do not leak). Two acceptable options:

- **(pref) Relaxation:** seed all fields neutral (0.0) and let `can_native_identity_field_feedback` move them under the structural edges, then read `concept_signature`. Purest "falls out" path.
- **(fallback) Uniform derivation:** `identity_field(n) = affine(deficit(n))` with the *same* affine for all `n`. This is *structural seeding*, not planting, because `deficit` is computed identically for every number and contains no salience token.

Under either path, `connectivity(7) = 0` in 1–10 ⇒ maximal `deficit` ⇒ 7 lands at the far edge of the graded axis **as a consequence of structure**, not because we typed "7 is special."

---

## 4. Two arms (run on the identical harness)

- **ARM 1 — THEORY / EMERGENT.** Shared neutral seed (§3). Felt coordinates produced/derived. Read `concept_signature(n, observer=FINE)`, project, measure distance. 7's outlierness must **emerge**.
- **ARM 2 — CIRCULAR CONTROL.** Identical harness, but additionally plant `attr:special=1` on 7 (and/or a hand-set `identity_field` spike). 7's outlierness now appears *trivially*. This is the visible contrast. `AskSpy` + schema invariants prove Arm 1 read **no** planted flag; Arm 2's separation is attributable to the flag (drop the flag → separation collapses in the control's own sub-check).

---

## 5. Sub-experiments (a–f) + the glyph-downstream test (g)

For each: **seed-map → readout → prediction (support vs refute) → control → honest-negative.**

### (a) Outlier / pick — "which number is most distinct?" (working set 1–10)

- **Seed-map:** shared neutral seed (§3). No felt planting.
- **Readout:** for each `n`, `v_n = item_signature_vector(s, n, obs_FINE, axis_keys)` over an ordered `axis_keys` list (the graded dynamical axes + tokenized relational axes). Compute centroid `c = mean(v_n)`; **outlierness(n) = l2_signature_distance(v_n, c)** (or distance to the multiplicative-cluster centroid). Rank descending.
- **Prediction (support):** in Arm 1, **7 ranks #1** (1 typically #2, as the unit with no proper divisors). If 7 is top only in Arm 2 (with the flag) but middling in Arm 1, **theory refuted**. If 7 is top in Arm 1 **only when a glyph/shape axis is included**, **theory refuted** (falsifiable core #1).
- **Control:** Arm 2 makes 7 trivially top via `special=1`; report side by side.
- **Honest-negative:** distance magnitudes are substrate-quantized (commitment saturates to ±4; valence is sign-only). We can rank order and separate clusters; we **cannot** claim the numeric distance equals a human "randomness rating." We report *ordinal* agreement, not calibrated magnitude.

### (b) Similarity / analogy — "which numbers feel alike?"

- **Seed-map:** shared neutral seed. Squares (4,9) share a `has_factor`-to-own-root pattern; `2·prime` numbers (6,10) share divisor structure; primes (2,3,5,7) share *absence* of proper divisors.
- **Readout:** `find_analogies(number_field, [number_field])` for self-analogy, and pairwise `categorical_signature_distance(v_a, v_b)` with `categorical_neighbour_threshold` to declare "feels alike." Cluster.
- **Prediction (support):** 4↔9 group (squares) on constitutive/relational axes; 6↔10 group (2·prime); 6 reads as "friendly/highly-composite" (many divisor edges → low deficit → central); **7 finds no structural analogue** → high isolation, no neighbour under threshold. Refute if 7 pairs tightly with a composite, or if squares/primes don't separate.
- **Control:** Arm 2 — the `special` flag distorts 7's categorical bucket; show it forces spurious (non)grouping.
- **Honest-negative:** `find_analogies` writes `implements` edges (mutates the graph) — run it on a throwaway copy or after snapshotting. "Feels alike" here means *signature-neighbour under a Hamming threshold*, not a psychological similarity rating.

### (c) Calculation-flavored task — "does 7 feel harder to multiply?"

- **Seed-map:** add a `×` relation sub-field: `product` edges `a → (a·b)` where the target is in `S` (times-table regularity lives in edge density). 7's multiplicative isolation = few in-neighbours on `has_factor` / sparse in-set products.
- **Readout:** compare 7's signature vector against composite anchors (2,4,6,8) on the relational/constitutive axes; quantify "felt difficulty" as signature-distance from the dense-times-table cluster. Optionally route through the aperture: does a coarse observer *lose* 7's product structure faster (fewer regular edges to hold)?
- **Prediction (support):** 7 sits far from the regular-times-table cluster (sparse, irregular product edges) → a distinct, "harder/carrying-heavy" signature; 2 and 5 (regular, terminating) sit central. Refute if 7's product signature is indistinguishable from 2/5.
- **Control:** Arm 2 — planting `special` on 7 makes it "hard" for the wrong reason; contrast.
- **Honest-negative:** the substrate has **no arithmetic executor and no notion of subjective effort/time**. "Felt difficulty" is *operationalized purely as signature-distance from a regularity cluster*. We are explicitly **not** claiming the substrate experiences carrying; we claim the structural signature of 7 is an outlier in the multiplication graph. State this loudly.

### (d) Mid-reasoning axis-minting — coin the structural dimension that explains 7

- **Seed-map:** shared neutral seed. Critically, **no axis for primality / multiplicative-isolation / cycle-length is held** at the start. The setpoint observer resolves only the pre-existing axes.
- **Readout:** run `run_minting_train_of_thought(wa, setpoint_observer=obs_FINE, topic=<number-corpus>, mint_after_quanta=3, ...)`. Each segment computes residual = `concept_signature(reached) − admitted_signature(setpoint)`; a residual **predicate** that recurs (the isolation/cycle coordinate no held axis covers) should persist ≥3 segments and the **graph** mints a new axis. Verify via returned `minted_axes` / `mint_events`. Cross-check with `induce_concern(agent, observation_of_7)` where 7's residual relation-system, uncovered by any held `ShapeSignature`, mints a `CapabilityAxis` (status `minted`). Measure with `capture_minting_cost`.
- **Prediction (support):** the system **coins a new structural/phenomenal axis** (e.g. "felt-isolation" / "cycle-length") from the *recurring residual driven by 7 (and other primes)* — the very dimension that explains 7 — **without it being seeded**. That is "deeper math reasoning with qualia": the substrate invents the coordinate. Refute if the residual never persists / nothing mints, or if the minted axis is unrelated to isolation/cycle structure.
- **Control:** Arm 2 — with `special=1` planted, the residual is dominated by the flag and the mint (if any) is about "specialness," not structure; contrast shows the theory arm mints *structure*.
- **Honest-negative:** minting is **graph-owned and threshold-dependent** (`mint_after_quanta`); Python never mints. A null mint is not by itself a refutation of the *quale* theory — it may mean the residual didn't clear the persistence bar under the chosen aperture. Report mint/no-mint with the counters, and treat mint as *supporting evidence*, not a load-bearing proof.

### (e) Aperture / "taste" manipulation — is the quale aperture-relative but structurally grounded?

- **Seed-map:** shared neutral seed (unchanged across the sweep).
- **Readout:** build observers with `grain` and `resolves`: `FINE = {commitment:0.125, valence:1.0, …}`, `COARSE = {commitment:4.0, …}`, and an existence-gated observer that `resolves` only the structural axes. Recompute (a)'s outlierness ranking under each observer.
- **Prediction (support):** **COARSE grain collapses 7 into the crowd** (over-compression — distinct field values round to the same step, signatures merge); **FINE grain restores 7's outlierness**; resolving *only structural axes* keeps 7 top (its outlierness is carried by structure, not by incidental axes). This shows the quale is **aperture-relative** ("mathematical taste") yet **structurally grounded**. Refute if fine vs coarse makes no difference (then the outlier is an artifact, not a compressed structure), or if gating out structural axes leaves 7 top anyway (then something non-structural is doing the work).
- **Control:** Arm 2 — the `special` flag survives coarsening (a single hand-set spike resists grain collapse differently), exposing the plant.
- **Honest-negative:** grain behavior is discretization; we show *which axes carry the outlierness under compression*, not a continuous psychophysical curve.

### (f) Set-dependence (notation-independence's structural half) — the outlier MOVES with the set

- **Seed-map:** rebuild the same neutral seed over `{1–6}`, `{1–10}`, `{1–12}` (via the `build_multi_category` shape). Structure is recomputed *within each set* (divisors/multiples are set-relative).
- **Predict-from-structure FIRST, then test:**
  - **1–6:** 7 is **absent**. Predicted outlier = the in-set prime with least connectivity — **5** (prime, no multiple in set; 2,3 have multiples; 4,6 composite). Secondary: 1.
  - **1–10:** predicted outlier = **7** (zero in-set factors/multiples, 6-digit cycle).
  - **1–12:** now 6,12 tie the set together (12 = 2²·3), and **11** enters (prime, no in-set factor or multiple, cycle length 2 under... note: `1/11=0.\overline{09}`, period 2). Competition: **7 vs 11**. Structural prediction: **11** becomes at least co-outlier (it is the new "isolated prime with no multiple ≤12"), while 7 gains a multiple? No — 14 ∉ 1–12, so 7 still has no in-set multiple; 7's cycle (period 6) is *longer/awkward-er* than 11's (period 2). **Prediction: 7 and 11 are the two co-outliers in 1–12, with 7 retaining the longer-cycle edge; the ranking must show BOTH separating from the composite bulk.** State this exact prediction before running.
- **Readout:** the (a) outlierness ranking, per set.
- **Prediction (support):** the top-outlier **tracks the structural prediction** as the set changes (5 in 1–6; 7 in 1–10; {7,11} in 1–12). This is the **strongest test**: the theory says the outlier is *relational and set-determined*, not an absolute property of the glyph "7." Refute if 7 stays the outlier in 1–6 (where it doesn't exist — impossible, but a proxy: if 5 doesn't top 1–6, the relational claim fails), or if 11 fails to compete in 1–12.
- **Control:** Arm 2 — `special=1` on 7 keeps 7 "top" even in 1–12 (or is nonsensical in 1–6), demonstrating that a planted flag is *set-blind* whereas structure is *set-sensitive*.
- **Honest-negative:** this tests **notation-independence only in its structural form** (same structure, different set). See §6 for the label-swap check, which is the closest the substrate gets to full notation-independence.

### (g) Glyph-downstream test — structure predicts shape (falsifiable core #3)

- **Seed-map:** shared neutral seed (no shape). Then, in a *separate, additive* read, introduce a shape coordinate two ways and compare:
  - **(g1) shape as read:** treat the emergent signature geometry (the outlierness ranking from (a)) as the predictor; obtain an independent shape-outlierness score for the glyphs 0–9 (e.g. `shape_signature`/`shape_signature_distance` over a glyph feature encoding supplied as data, **not** seeded onto the number concepts).
  - **(g2) correlation test:** does structural-outlierness (a) **predict** glyph-outlierness (g1)? Report rank correlation.
- **Prediction (support):** structural-outlier rank **correlates** with glyph-outlier rank (7 high on both). This is consistent with "glyph downstream." Refute if the glyph adds separation *independently* of structure (i.e. structure fed in alone fails, but adding the shape axis rescues it — that would make shape an *input*, not a consequence; ties back to core #1).
- **Control:** Arm 2 contrast as above.
- **Honest-negative — the biggest one:** **the substrate can show correlation, not causation.** We can show structural-outlierness predicts glyph-outlierness; we **cannot** run the counterfactual "give 7 a rounded glyph and watch the quale stay put" inside this substrate. The causal-direction claim ("shape is downstream") is supported by (i) the fact that removing the shape axis does **not** remove 7's outlierness in Arm 1, and (ii) the notation/label-swap invariance (§6) — but it remains **correlational + invariance evidence**, not a manipulation of the glyph. State this explicitly in results.

---

## 6. Notation-independence & substrate-independence check

Because the neutral seed carries **no glyph and no notation**, re-seed the *identical structural graph* under an **alternate label set** (Roman numerals; binary strings; nonsense tokens). Requirement: **`concept_signature` frozensets and all pairwise distances are byte-identical** across label sets (modulo the label string itself, which lives only in `lexical:formal is_a`/name and can be excluded from the axis_keys). If identical → the quale is label/notation-independent and the glyph is downstream, **as far as the substrate can demonstrate**.

**Honest boundary:** this shows independence from *the label we attach*, which is the substrate-expressible form of "notation-independence." It does **not** prove independence from *all possible* human notations (a claim outside the substrate's reach). Substrate figures (quantum/half_width values, saturation of `commitment`) are taken **as given** from `seeds/qualia_space.json`; we do not tune them to get a result — tuning them would be a form of planting.

---

## 7. Proposed metric / scoring

Reuse `scoring/metrics.py` where it applies; add only thin wrappers.

- **Outlierness(n):** `l2_signature_distance(item_signature_vector(n), centroid)` — primary. Secondary: `categorical_signature_distance` + `categorical_neighbour_threshold` for cluster membership; `item_distance_from_setpoint` (presence-only) as a saturating cross-check.
- **Ranking agreement:** Spearman/Kendall rank correlation (via `scoring/metrics.py` if a rank metric exists there; else a thin additive helper) between (i) Arm-1 outlierness ranks and the *pre-registered structural prediction*, and (ii) structural-outlier ranks vs glyph-outlier ranks (sub-exp g). Report the **ordinal** correlation, never a calibrated magnitude.
- **Arm contrast:** report Arm 1 vs Arm 2 ranks together; define **"emergence delta"** = (does 7 top Arm 1 *without* any planted flag?) as a boolean gate, plus the rank gap between 7 and the composite bulk in each arm.
- **Minting cost:** `capture_minting_cost(...)` → `{counter_ops_total, wall_seconds, minted_axes, n_minted, ask_spy, rule_count}`; assert `ask_spy` external calls == 0 (teacher-free).
- **Pre-registration:** the structural predictions in (a) and (f) (5→1–6, 7→1–10, {7,11}→1–12; 4↔9, 6↔10 groupings) are **written into the harness as expected values before running**, so the test cannot be retrofit to whatever comes out.

---

## 8. What would falsify the whole theory

The theory is **refuted** (not merely "unsupported") if any of these hold in the clean theory arm (Arm 1), teacher-free, with schema invariants passing:

1. **7 is not the structural outlier in 1–10** from neutral structure alone (fails core #1 / sub-exp a).
2. **7 only separates when a glyph/shape axis is fed in** — remove the shape axis and 7 rejoins the crowd (shape is an *input*, not downstream; cores #1 & #3).
3. **The outlier does not move with the set** — e.g. 5 fails to top 1–6, or 11 fails to compete in 1–12 (fails core #4 / sub-exp f). This is the strongest single falsifier.
4. **Structural-outlierness does not predict glyph-outlierness** (fails core #3 / sub-exp g), i.e. no rank correlation.
5. **Label-swap changes the signatures/distances** (fails notation-independence / §6).
6. **Arm 1 == Arm 2** — the emergent result is indistinguishable from the planted one, meaning we cannot show non-circularity (the design's own integrity check fails).

A **null mint** (sub-exp d) is *not* on this list: it weakens the "qualia coined mid-reasoning" flourish but does not by itself refute the compression-of-structure thesis.

**Sub-experiment (h) — feel-then-verify — adds these falsifiers (all in the clean theory arm, teacher-free, arithmetic-spy == 0 during the felt window):**

7. **Composition carries no information** — the composed felt region's hit-rate (h1) is indistinguishable from the shuffled-operand baseline (its CI overlaps chance). Tier-2 composition is refuted.
8. **No "feels-wrong" faculty** — the felt region admits plausible decoys as readily as truths (h2 rejection precision/recall at chance). The error-detection value is refuted.
9. **No compute economy** — the felt path is not materially cheaper than verification in native counters (h4), so "feel most, compute rarely" is empty.
10. **Arm 1 needs the hand-coded transform** — Arm-1 (minted) composition collapses to chance and only Arm-2's hand-coded `T_op` succeeds, meaning the transform could not be learned from structure (the (h) analogue of falsifier #6 / circularity).

A **null transform-mint** in (h) is likewise *not* a refuter: it leaves Tier-2 unsupported *for that run* but does not touch Tier-1 or the feel-then-verify architecture. A **failed search-guidance** (h3) is an expected honest-negative, not a falsifier of the thesis.

**Sub-experiment (i) — polynomial qualia — adds these falsifiers (all in the clean theory arm, teacher-free, with the felt-window arithmetic-spy `poly-multiply == root-finder == factor == discriminant == 0`):**

11. **Polynomial composition carries no information** — the composed felt region's hit-rate (i1) for `p·q` / `p+q` / `p'` is indistinguishable from the shuffled-operand baseline (its CI overlaps chance). Tier-2 structural composition is refuted for polynomials.
12. **No "feels-wrong" faculty for polynomials** — the felt region admits off-degree / off-parity / off-end-behavior decoys as readily as truths (i2 rejection precision/recall at chance).
13. **Search-guidance (the flagship) does not beat chance** — none of the felt priors steers hard compute above a naive baseline: the felt root-region does not cut solver iterations and misses roots at chance (i-guide-1), the factorability feel does not beat base-rate (i-guide-2), and the discriminant-sign feel does not beat chance (i-guide-3). Because search-guidance is the *flagship* for polynomials (unlike scalar (h)'s h3), an across-the-board null here **refutes the polynomial payoff claim** (it does not, however, retroactively refute (h)).
14. **No compute economy for polynomials** — the felt path is not materially cheaper than verification in native counters (i4), so "feel most, solve rarely" is empty *even though root-finding/factoring is expensive*.
15. **Arm 1 needs the hand-coded transforms** — Arm-1 (minted) polynomial composition collapses to chance and only Arm-2's hand-coded `degree-adds`/`parity-XORs`/`steeper-wins`/`deg−1` tables succeed, meaning the structural transforms could not be learned from residual (the (i) analogue of falsifiers #6 / #10 / circularity).

A **null transform-mint** in (i) is *not* a refuter (parallel to the (h) clause): it leaves Tier-2 unsupported *for that run* but does not touch Tier-1 or the feel-then-verify architecture. A **single** failed guide test (e.g. only i-guide-3 nulls) is an honest-negative, not a falsifier; only the *across-the-board* guide null (#13) bears on the polynomial payoff claim.

---

## 9. Honesty boundaries (explicit)

- **Correlation, not causation** for glyph-downstream (§5g): we show structure predicts shape and that shape is *removable without losing the outlier*, plus label invariance — we do **not** manipulate a glyph and observe the quale, because the substrate has no such lever.
- **Notation-independence is testable here only structurally** (§6): independence from the *attached label*, not from all human notations.
- **No arithmetic / no subjective effort** (§5c): "felt difficulty" is operationalized as signature-distance from a regularity cluster; the substrate does not compute products or experience effort.
- **Substrate figures as-given** (§6): quanta, half-widths, and `commitment` saturation come from the seed unchanged; results are reported as ordinal, within the substrate's discretization, and we do not tune constants to manufacture separation.
- **Minting is graph-owned** (§5d): Python never mints; thresholds gate it; report mint/no-mint honestly with counters.
- **`find_analogies` mutates the graph** (§5b): run on a snapshot/copy.
- **Feel-then-verify — Tier-3 wall by design** (§9b.6): no exact value from feel; the feel yields a *region*, verification yields the *point*. Lossiness is why the read is cheap, not a shortfall to fix.
- **Composition fidelity is the unproven, load-bearing step** (§9b.6): that operand qualia compose into a faithful result region is exactly where (h) can break; gated by hit-rate-vs-baseline and region-tightness, not asserted.
- **The operation-transform must be minted, never hand-coded** (§9b.3): a hand-written `T_op` is the (h) form of planting/circularity; the Arm-2 hand-coded control exists to show the hollow version by contrast.
- **No arithmetic in the felt path** (§9b.4): proven by an extended spy that must read 0 arithmetic-executor calls during the felt window; the exact op runs only in the separate verification step. "Feels wrong" is region-exclusion, not subjective experience.
- **Polynomial feel is a stronger structural fit, but composition is still unproven** (§9c): a polynomial *is* a shape, so operand qualia are richer and the transforms are structural (degree-adds / parity-XORs / steeper-wins / differentiation-smooths) rather than arithmetic — yet Tier-2 fidelity is still the load-bearing, unproven step, gated by (i1) hit-rate-vs-baseline and region-tightness.
- **Polynomial Tier-3 wall is wider, by design** (§9c.0/§9c.7): no exact roots, no exact factorization, no exact `p·q` coefficient vector, no exact equality of two feels-identical polynomials — the feel yields a region, verification the point; wider than the scalar wall precisely because root-finding/factoring is hard.
- **Polynomial transforms must be minted, never hand-coded** (§9c.3): a hand-written `degree-adds`/`parity-XORs`/`steeper-wins`/`deg−1` table is the (i) form of planting; the Arm-2 hand-coded control shows the hollow version by contrast.
- **No polynomial algebra in the felt path** (§9c.4): the extended spy must read 0 poly-multiply / 0 root-finder / 0 factorization / 0 discriminant-eval during the felt window; exact ops run only in verification.
- **Bounded quanta vs unbounded polynomial structure** (§9c.6): degree-band and coefficient-magnitude-band saturate into a deliberately coarse top band; embraced lossiness, not tuned away.
- **Polynomial search-guidance is a scored flagship but a heuristic gate** (§9c.5 i-guide): the felt priors that steer root-finding/factoring/real-vs-complex are reported as *net compute pruned above chance* with CIs, not as decision procedures; honest-negatives reported per-guide where a prior does not beat baseline.

---

## 9b. Sub-experiment (h): The FEEL of an equation — expression-qualia by composition, feel-then-verify

This is a new major capability, distinct from (a–g). Where (a–g) ask *what is the quale of a number*, (h) asks: **can the substrate obtain the quale of a composed expression** (`a·b`, `a+b`, "is `n` prime?", "roughly how big?") **by COMPOSING the qualia of its parts — without evaluating the expression** — and then *optionally* verify that felt read against the exact math as a **separate** step? This is analysis-by-synthesis with a fast-path: a cheap felt prior first; an expensive exact audit only when it's worth it. The whole discipline of §1 carries over unchanged; the one *new* crux (§9b.3) is that the **composition/operation-transform must be minted or learned from structure, never hand-coded** — otherwise the demonstration is hollow.

### 9b.0 The three tiers (graded honestly)

- **Tier 1 — magnitude/shape feel (strongest, closest to demonstrable).** "big/small, round/jagged, near a landmark" as a **direct signature read** of a single number, no arithmetic. This is essentially (a)/(b) re-scored on magnitude-band and roundness axes; it is the floor the composition tier must beat.
- **Tier 2 — relational/structural feel via COMPOSITION (load-bearing; the direct answer to the question).** The felt result of an *operation* obtained by applying a **felt operation-TRANSFORM** to the operand qualia on shared axes — `even·even→even`, `prime·prime→composite`, `small·small→still-smallish`, `·→magnitude-bands add` — producing a **RESULT QUALE (a region)** *without producing the RESULT VALUE*. This is where the thesis lives or dies.
- **Tier 3 — exact value from feel (OUT OF SCOPE; a hard, principled wall).** Not a limitation to overcome. **Qualia are lossy by definition, and that lossiness is *why* they are cheap.** If the quale contained the exact value, it would contain the full computation and would not be cheap. The feel narrows to a **region**; verification recovers the **point**. We state this as a design boundary, not a failure.

### 9b.1 Seed-map — operand structural axes + the (minted) operation-transform

Reuse the **shared neutral seed** of §3 verbatim (`has_factor`/`divides`/`residue_mod_k` edges, neutral `decimal_cycle_length`, `is_a number`, and the uniform `deficit(n)`-derived produced field). No new per-number planting. On top of the existing signature, the felt read for an expression composes on a fixed set of **operand structural axes**, each of which is either already present or a uniform read of the neutral seed:

- **parity-feel** — read from the `residue_mod_2` edge target (structural, type-uniform; not a `special` flag).
- **magnitude-band** — a coarse read of the produced/derived field ordering (Tier-1 quantity), banded by the observer grain (e.g. ones / teens / "the-50s" / hundreds). This is the same graded axis (e), read at COARSE grain.
- **roundness** — read from `residue_mod_{5,10}` structure (terminating/`decimal_cycle_length==0`), uniform for all `n`.
- **primality-feel** — the *emergent* divisor-absence coordinate from (a)/(d): zero `has_factor` edges within `S`. Never a seeded `is_prime` attr.

The **operation-transform** is a map `T_op: (quale(a), quale(b)) → region(quale(a op b))` **on these shared axes**. It is the only genuinely new object, and §9b.3 governs how it is *acquired* — it must **fall out of the substrate**, not be typed in.

### 9b.2 Two tiers of readout (Tier 1 direct; Tier 2 composed)

- **Tier 1 read (no arithmetic):** `item_signature_vector(s, n, obs_COARSE, magnitude_roundness_axes)` → a band + roundness bit. Score against ground truth of `n` (which we know at seed time, uniformly, for all `n`). This is a sanity floor.
- **Tier 2 read (composed, no evaluation):** given operands `a, b` and operator `op`, apply `T_op` to `(v_a, v_b)` on the shared axes to obtain a **result region** `R = T_op(v_a, v_b)` — a set of admissible `(parity, band, roundness, primality)` tuples. **`R` is produced without ever computing `a op b`.** The verification step (§9b.4) is what later computes the exact value and checks `truth ∈ R`.

### 9b.3 The central non-circularity crux — the transform is MINTED, not hand-coded (make-or-break)

If we hand-write `T_×: even·even→even`, we have simply re-encoded the arithmetic and the demonstration is **hollow/circular** — the exact mirror of planting `special=1` on 7. So the operation-transform itself must **emerge**. Mirroring §5(d) and the §1 "operational definition of planted," the transform is acquired thus:

- **Acquisition (theory arm):** feed the system a stream of **composed expressions** whose *result-feel has no held axis*. Each segment computes `residual = concept_signature(reached_result_feel) − admitted_signature(setpoint)`. When the system **repeatedly** encounters `even·even` pairs and the *result feel* consistently lands in the even band with no held axis to name that regularity, the recurring residual persists ≥ `mint_after_quanta` segments and the **graph mints a felt operation-axis** (a `CapabilityAxis` / new `QualiaDimension`) — a coined "product-parity" or "band-addition" coordinate — via `run_minting_train_of_thought(...)` / `induce_concern(...)`. The transform `T_op` is then **read off the minted axis**, not authored. Python never writes the rule; the graph coins it. Verify via returned `minted_axes` / `mint_events` and `capture_minting_cost`.
- **Operational definition of "hand-coded transform" (extends §1's "planted"):** `T_op` is *hand-coded* if (i) it appears as an explicit Python/JSON rule table mapping operand-axis values to a result region, OR (ii) its result-region constants were tuned per-operator to match known arithmetic. A transform is *learned/minted* only if it is **read off an axis the graph itself coined** from a recurring, unnamed residual. Anything else voids the Tier-2 result.
- **Circular control (Arm 2, mandatory, mirrors §4):** run the identical harness with `T_op` **hand-coded** as an explicit rule table (`even·even→even`, etc.). This is the **hollow** version: the result region will be trivially correct because we wrote the arithmetic into it. Report Arm-1 (minted) vs Arm-2 (hand-coded) side by side. The Tier-2 claim is only credible as the difference: **Arm 1 composes correctly using a transform it was never handed.** If Arm 1 cannot compose without the hand-coded table, the composition thesis is unsupported.

### 9b.4 Arithmetic-free felt path — provable separation (extends the teacher-free guard)

The felt read must be shown to **not execute the expression to produce the feeling**. We extend the existing `AskSpy` teacher-free guard into a **compute-audit guard** that wraps the felt path and asserts **zero** invocations of the exact operators: no multiply, no add, no factorization is called while `R = T_op(v_a, v_b)` is produced. Concretely:

- The felt path may touch only: `concept_signature`, `item_signature_vector`, the minted-axis read, and signature-distance metrics. Any call into an arithmetic executor during the felt window increments a spy counter that **must stay 0** (alongside `ask_spy == 0`).
- The exact op (`a·b`, `a+b`, trial-division primality) is run **only afterward**, inside the *verification* step, and only to **check** `truth ∈ R`. The harness enforces the ordering by clearing/reading the arithmetic-spy counter at the felt/verify boundary, exactly as `capture_minting_cost` clears counters at the build/think boundary. A run where the arithmetic-spy is nonzero during the felt window is **void** (the fast-path secretly computed).

### 9b.5 Falsifiable readouts + predictions

For each: **seed-map → readout/metric → prediction (support vs refute) → circular control → honest-negative.** All scoring reuses `scoring/metrics.py` (`bootstrap_ci`, `spearman_rho`, `pearson`) and `capture_minting_cost`; predictions are **pre-registered** into the harness before running (per §7).

**(h1) COMPOSITION VALIDITY — does the felt region contain the truth?**
- **Seed-map:** shared neutral seed; operand axes (§9b.1) + minted `T_op` (§9b.3). For many `(a,b)`, compose `v_a, v_b → R` on `{parity-feel, magnitude-band, roundness, primality-feel}`.
- **Readout/metric:** compute true `a·b` (and `a+b`) in the **verify** step; score `hit = [truth ∈ R]`. Report **hit-rate + 95% CI** via `bootstrap_ci`, against a **shuffled/chance baseline** (regions drawn from mismatched operands). Support requires hit-rate CI **above** the shuffled baseline CI.
- **Prediction (support):** minted-transform regions contain the truth **more often than chance** on parity and magnitude-band especially (the most structurally regular axes). **Refute** if Arm-1 hit-rate is indistinguishable from the shuffled baseline (composition carries no information).
- **Circular control:** Arm 2's hand-coded `T_op` will hit near-perfectly by construction — the *gap-to-Arm-1* is the honest measure of how much real composition the minted transform achieved.
- **Honest-negative:** a region that is *too wide* trivially contains the truth; we therefore also report **region tightness** (fraction of the axis-space admitted). A wide-but-correct region is weak evidence, reported as such.

**(h2) DECOY REJECTION — the "feels wrong" faculty (error-detection value).**
- **Seed-map:** as (h1). For each `(a,b)`, form the truth and a **plausible-but-wrong decoy** (off-by-parity, or off-by-one-magnitude-band).
- **Readout/metric:** does `R` **admit the truth and exclude the decoy**? Report **precision/recall of rejection** (decoy correctly excluded = true positive for the "feels wrong" detector).
- **Prediction (support):** off-parity decoys are rejected with high precision (parity-feel is the crispest axis); magnitude-band decoys rejected at above-chance recall. **Refute** if `R` admits decoys as readily as truths (no discriminative "feels-wrong" faculty).
- **Circular control:** Arm 2 rejects decoys trivially (it encoded the arithmetic); contrast shows whether the *minted* transform earned its rejection.
- **Honest-negative:** **"feels wrong" is operationalized strictly as region-exclusion**, not a subjective experience of wrongness. We claim a sanity-check faculty, not felt discomfort.

**(h3) SEARCH GUIDANCE (optional, harder; honest-negative if not shown).**
- **Seed-map:** as (h1), on a harder task, e.g. "which of these candidate factorizations *feels* closest?"
- **Readout/metric:** does the felt **gradient** (signature-distance of each candidate's composed feel to the target feel) **rank the true/worth-computing step first**? Report rank-of-truth and `spearman_rho` between felt-distance rank and true-closeness rank.
- **Prediction (support):** the felt gradient steers toward the exact step worth computing (truth in top-k by felt distance). **Refute / honest-negative:** if the gradient does not beat random ordering, report it as a **clean negative** — search-guidance is the least-supported claim and we do not dress it up.
- **Circular control:** Arm 2 as above.
- **Honest-negative:** this is explicitly the **hardest, most likely-to-null** readout; a null here does **not** touch (h1)/(h2).

**(h4) COST — "feel most, compute rarely" as a real compute-economy claim.**
- **Seed-map:** as (h1); measure both paths on the identical corpus.
- **Readout/metric:** `capture_minting_cost(...)` for the **felt path** (`counter_ops_total` should sit in the signature-read regime — the same ~55-op scale as the existing minting-cost baseline) vs the **verify path** (exact op, invoked selectively). Report felt-path ops vs verify-path ops; assert `ask_spy == 0` and the §9b.4 arithmetic-spy `== 0` for the felt window.
- **Prediction (support):** felt read is **cheap** (signature-read regime), verification is the **expensive** step invoked only on the fraction of cases that fail (h2)'s sanity check or need Tier-3 exactness — so aggregate compute drops when most reads never trigger a verify. **Refute** if the felt path is not materially cheaper than verification (then there is no economy to the fast-path).
- **Circular control:** Arm 2's hand-coded transform is *also* cheap but *hollow*; cost alone does not rescue a circular transform — cost is reported **jointly** with (h1) validity.
- **Honest-negative:** cost is in the substrate's **native counters**, not wall-clock arithmetic FLOPs; we claim an *ops-regime* economy, not a calibrated speedup.

### 9b.6 Honesty boundaries specific to (h)

- **Tier-3 wall is by design, not limitation:** no exact value from feel — the feel narrows to a region; verification recovers the point. Stated as a principled boundary (lossiness is *why* it's cheap).
- **Composition fidelity is UNPROVEN and is exactly where it can break** — mirroring §5(d)/distillation-fidelity reasoning: that the parts' qualia compose into a *faithful* result region is the load-bearing, unproven step, gated by (h1)'s hit-rate-vs-baseline and region-tightness.
- **A null transform-mint weakens but does not refute** the feel-then-verify thesis (parallel to §8's null-mint clause): if nothing mints, Tier-2 is unsupported *in this run*, but Tier-1 (h-magnitude/roundness) and the feel-then-verify *architecture* stand.
- **"Feels wrong" = region-exclusion**, not subjective experience (§9b.5-h2).
- **No arithmetic executor in the felt path**, proven by the extended spy (§9b.4); the exact op runs only in verification.
- **Substrate figures/quanta as-given** (§6): bands, grain quanta, saturation come from the seed unchanged; we do not tune them to widen/narrow regions into a result.
- **Correlation not causation** where applicable (h3 gradient): a felt-distance ranking that tracks truth is correlational evidence of guidance, not a proof the feel *caused* the right search.

---

## 9c. Sub-experiment (i): Polynomial qualia — the feel of a polynomial (equation) via structural composition, feel-then-verify

This is sub-experiment (h) **generalized from scalars to polynomials**, and it is a **stronger fit** for the compression-of-structure thesis: a polynomial is a *structural object* — a shape — not a point. Where (h) had to squeeze a felt "region" out of two numbers whose only interesting structure was parity/magnitude/primality, a polynomial *is* its structure (degree, parity, end-behavior, root layout, convexity), so the operand qualia are richer and the operation-transforms are **genuinely structural rather than arithmetic** (degree adds under `·`; parity XORs; the steeper term wins a sum; differentiation lowers degree by one). The entire §1 non-circularity discipline, the §9b.3 minted-not-hand-coded crux, and the §9b.4 arithmetic-free felt path carry over unchanged; only the operands, transforms, and the (widened) Tier-3 wall change.

**The capability under test.** Can the substrate obtain the **quale of a polynomial** and of **composed polynomial expressions** (`p·q`, `p+q`, `p'`, `p∘q`, "does `p` factor?", "real vs complex roots?", "roughly where/how many roots?") by *reading/composing structural qualia* — **without evaluating, root-finding, or factoring** — yielding the **feeling of the polynomial equation** (a lossy region), and then *optionally* **verify** that felt read against exact root-finding/factorization as a **separate, expensive** step? The feel-then-verify economy is **more valuable here than for scalar arithmetic**, because verification for polynomials (root-finding, factorization) is genuinely *expensive* — so "feel most, solve rarely" buys real compute, and **search-guidance is promoted from an honest-negative (h3) to the flagship readout (i-guide).**

### 9c.0 The three tiers (graded honestly)

- **Tier 1 — the shape-quale of one polynomial (strongest, closest to demonstrable).** "Rises-both-ends / falls-then-rises, one hump or two, roots-near-origin-or-spread, gentle or steep" as a **direct signature read** of a single seeded polynomial `p`, no root-finding. This is (a)/(b) re-scored on the polynomial's neutral structural axes; the floor Tier-2 must beat.
- **Tier 2 — the feel of a composed expression via COMPOSITION (load-bearing).** The felt result of a polynomial *operation* obtained by applying a **minted felt operation-transform** to the operand qualia on shared structural axes — `deg(p·q)=deg p+deg q` felt as *short·long→longer*; leading-sign multiplies under `·`; end-behavior of `p+q` dominated by the higher-degree term (*steeper wins*); parity XORs under `·` (even·even→even, odd·odd→even) and composes under `∘`; differentiation lowers degree by one and drops at most one real root with interlacing (*smoothing*) — producing a **RESULT REGION** (a set of admissible shape-tuples) **without producing the RESULT VALUE** (no coefficient vector, no roots). This is where the thesis lives or dies, and it is the strong case: these transforms are structural, so they should mint cleanly and compose faithfully.
- **Tier 3 — exact roots / exact factorization / exact coefficients from feel (OUT OF SCOPE; a hard, principled wall, WIDER here than for scalars).** Not a limitation to overcome. **Qualia are lossy by design, and that lossiness is *why* they are cheap.** The feel yields "one real root near the origin, one large positive" — a root-**region**, never `x = 2.3178…`. It cannot yield the exact coefficient vector of `p·q` (that is the convolution = arithmetic), nor the exact roots/factorization, nor the exact equality of two feels-identical polynomials (two polynomials can share degree, parity, end-behavior and root-band yet differ in exact coefficients — the feel is lossy *precisely* there; verification disambiguates). The wall is **wider and more valuable than for scalars** because what lies past it (root-finding, factoring) is *hard*, so the cheap felt prior in front of it saves more.

### 9c.1 Seed-map — polynomials as Concepts with neutral structural axes + the (minted) operation-transforms

Seed each polynomial `p` as **one `Concept`** carrying **only type-uniform neutral structural attrs/edges** (rule 1) — the *same* axis set for every polynomial, only the fillers differ; **no** `this-polynomial-is-special` / `factors` / `irreducible` attr is ever planted. Mirrors `build_category`'s shape (loads VOCAB+QUALIA seeds, then `asr._QUALIA_SCHEMA_CACHE.clear()`). The neutral operand axes, and how each maps to the substrate:

- **degree-band** — a scalar attr `degree = deg(p)` feeding a **graded dynamical axis** via the §3 produced/derived discipline (the uniform `deficit`-analogue transform, per-polynomial-blind), banded into `{const, linear, quadratic, cubic, quartic, higher}`. The `higher` band is **deliberately coarse** (see the §9c.6 quantization hazard). Never a raw "this is degree 17" salience token.
- **leading-coefficient sign** — an edge `p → SIGN_pos` / `p → SIGN_neg` to a **shared class node** (type-uniform, same edge type for all `p`; only the target differs), exactly as `residue_mod_k` targets a shared residue-class node.
- **parity** — an edge `p → PARITY_even` / `PARITY_odd` / `PARITY_neither` to a shared class node (read from the coefficient-support pattern at seed time, uniformly; not an arithmetic call).
- **end-behavior** — **derived**, not separately seeded: a uniform read of `(degree-parity, leading-sign)` (even+pos → rises/rises; even+neg → falls/falls; odd+pos → falls/rises; odd+neg → rises/falls). Same derivation function for every polynomial.
- **root-count band** — a coarse `{none, one, few, many}` real-root-count band, seeded as a graded read of neutral structural facts available without solving (degree parity forces odd-degree reals ≥ 1; sign-change/Descartes-style coefficient-sign-alternation count as a *structural* upper-band cue). Banded, never the exact count.
- **coefficient-magnitude band** — `{tiny, small, moderate, large}` coarse band of coefficient height, feeding a second graded axis; **saturates** at the top band (§9c.6).
- **dominant-term feel** — a read of which term dominates (highest degree with nonzero coefficient), carried on the constitutive/relational axes.
- **convexity feel** — `{convex, concave, mixed}` read from `(degree-parity, leading-sign)` for the low-degree bands and from sign-of-leading + degree for higher, uniform.

All eight are **uniform neutral reads** (rule 1): identical keys/edge types for every polynomial, fillers differ. Outlierness/feel must **EMERGE** through the §3 shared-seed derivation discipline (a uniform, per-polynomial-blind function; the `connectivity`/`deficit` analogue here is e.g. *root-band deficit* / *structural-regularity deficit* computed identically for all `p`) — never planted.

The **operation-transforms** `T_op: (quale(p), quale(q)) → region(quale(p op q))` on these shared axes (for `op ∈ {·, +, ', ∘}`) are the only genuinely new objects, and §9c.3 governs how they are *acquired* — they must **fall out of the substrate**, not be typed in.

### 9c.2 Two tiers of readout (Tier 1 direct; Tier 2 composed)

- **Tier 1 read (no root-finding):** `item_signature_vector(s, p, obs_FINE, poly_axis_keys)` over the eight neutral axes → a shape-quale tuple `(degree-band, leading-sign, parity, end-behavior, root-band, coeff-mag-band, dominant-term, convexity)`. Score against the ground-truth structural facts of `p` (known at seed time, uniformly, for all `p`). Sanity floor.
- **Tier 2 read (composed, no evaluation):** given operands `p, q` and operator `op`, apply the minted `T_op` to `(v_p, v_q)` on the shared axes to obtain a **result region** `R = T_op(v_p, v_q)` — a set of admissible shape-tuples for `p op q`. **`R` is produced without ever computing `p op q`, without multiplying coefficients, without finding a root.** The verification step (§9c.4) later computes the exact result and checks `truth ∈ R`.

### 9c.3 The central non-circularity crux — the transforms are MINTED, not hand-coded (make-or-break)

Hand-writing `T_×: deg(p·q)=deg p+deg q` (or `parity XORs`, or `steeper wins`, or `differentiation lowers degree`) simply **re-encodes the polynomial algebra** and the demonstration is **hollow/circular** — the polynomial form of planting `special=1` on 7. So each operation-transform must **emerge**. Mirroring §5(d), §9b.3, and the §1 "operational definition of planted":

- **Acquisition (theory arm):** feed the system a stream of **composed polynomial expressions** whose *result-feel has no held axis*. Each segment computes `residual = concept_signature(reached_result_feel) − admitted_signature(setpoint)`. When the system **repeatedly** meets products whose result-feel lands one degree-band longer with no held axis to name that regularity — or sums whose end-feel is consistently the steeper operand's, or derivatives whose degree-feel is consistently one lower — the recurring residual persists ≥ `mint_after_quanta` segments and the **graph mints a felt operation-axis** (a `CapabilityAxis` / new `QualiaDimension`): a coined "degree-adds", "parity-XORs", "steeper-wins", or "differentiation-smooths" coordinate, via `run_minting_train_of_thought(...)` / `induce_concern(...)`. Each `T_op` is then **read off the minted axis**, not authored. Python never writes the rule; the graph coins it. Verify via returned `minted_axes` / `mint_events` and `capture_minting_cost`.
- **Operational definition of "hand-coded transform" (extends §1's "planted" and §9b.3, applied to the polynomial operators):** a polynomial `T_op` is *hand-coded* if (i) it appears as an explicit Python/JSON rule table mapping operand structural-axis values to a result region (e.g. a literal `deg_out = deg_p + deg_q`, a `parity_out = xor(parity_p, parity_q)` table, a `end_behavior_out = argmax_degree(...)` rule, or a `deg_out = deg_p − 1` differentiation rule), OR (ii) its result-region constants were tuned per-operator to match known polynomial algebra. A transform is *learned/minted* only if it is **read off an axis the graph itself coined** from a recurring, unnamed residual. Anything else voids the Tier-2 result.
- **Circular control (Arm 2, mandatory, mirrors §4 / §9b.3):** run the identical harness with every `T_op` **hand-coded** as an explicit rule table (`degree adds`, `parity XORs`, `steeper wins`, `deg−1`). This is the **hollow** version: the result region is trivially correct because we wrote the polynomial algebra into it. Report Arm-1 (minted) vs Arm-2 (hand-coded) side by side. The Tier-2 claim is credible only as the difference: **Arm 1 composes correctly using transforms it was never handed.** If Arm 1 cannot compose without the hand-coded tables, the composition thesis is unsupported.

### 9c.4 Arithmetic-free felt path — provable separation (extends the §9b.4 compute-audit guard)

The felt read must be shown to **not solve/evaluate/factor the polynomial to produce the feeling**. Extend the §9b.4 compute-audit guard so that, during the felt window, the spy asserts **zero** invocations of every exact polynomial operator:

- **0 polynomial-multiply (coefficient-convolution) calls, 0 root-finder calls, 0 factorization calls, 0 discriminant-evaluation calls** while `R = T_op(v_p, v_q)` is produced. The felt path may touch only: `concept_signature`, `item_signature_vector`, the minted-axis read, and signature-distance metrics. Any call into an exact polynomial executor during the felt window increments a spy counter that **must stay 0** (alongside `ask_spy == 0`).
- The exact ops (coefficient convolution for `p·q`, a real/complex root-finder, a factorization routine, discriminant evaluation) run **only afterward**, inside the *verification* step, and only to **check** `truth ∈ R` (or to spend the compute the felt prior recommended). The harness enforces the ordering by clearing/reading the arithmetic-spy counter at the **felt/verify boundary**, exactly as `capture_minting_cost` clears counters at the build/think boundary. A run where any of these counters is nonzero during the felt window is **void** (the fast-path secretly solved).

### 9c.5 Falsifiable readouts + predictions

For each: **seed-map → readout/metric → prediction (support vs refute) → circular control → honest-negative.** All scoring reuses `scoring/metrics.py` (`bootstrap_ci`, `spearman_rho`, `pearson`) and `capture_minting_cost`; predictions are **pre-registered** into the harness before running (per §7).

**(i1) COMPOSITION VALIDITY — does the composed felt region contain the true structural properties?**
- **Seed-map:** shared neutral seed (§9c.1); operand axes + minted `T_op` (§9c.3). For many operand pairs `(p,q)`, compose `v_p, v_q → R` for `p·q`, `p+q`, and `p'` on `{degree-band, leading-sign, parity, end-behavior, root-band, convexity}`.
- **Readout/metric:** in the **verify** step compute the true structural properties of `p·q` / `p+q` / `p'` (degree, parity, end-behavior, real-root-band via a root-finder); score `hit = [truth-tuple ∈ R]`. Report **hit-rate + 95% CI** via `bootstrap_ci`, against a **shuffled baseline** (regions composed from mismatched operands). Support requires the Arm-1 hit-rate CI **above** the shuffled baseline CI.
- **Prediction (support):** minted-transform regions contain the truth **more often than chance**, especially on degree-band (`deg(p·q)=deg p+deg q` banded), parity (XOR), and end-behavior-under-`+` (steeper wins) — the most structurally regular axes. **Refute** if the Arm-1 hit-rate is indistinguishable from the shuffled baseline (composition carries no information).
- **Circular control:** Arm 2's hand-coded `T_op` hits near-perfectly by construction — the *gap-to-Arm-1* is the honest measure of how much real composition the minted transform achieved.
- **Honest-negative:** a region that is *too wide* trivially contains the truth; we also report **region tightness** (fraction of the shape-tuple space admitted). A wide-but-correct region is weak evidence, reported as such. Also: differentiation's "drops at most one real root with interlacing" is a band claim, not exact — scored on the band, never on a count.

**(i2) DECOY REJECTION — the "feels wrong" faculty (error-detection value).**
- **Seed-map:** as (i1). For each composed result, form the truth and a **plausible-but-wrong decoy** (off-degree by one band, off-parity, or off-end-behavior).
- **Readout/metric:** does `R` **admit the truth and exclude the decoy**? Report **precision/recall of rejection** (decoy correctly excluded = true positive for "feels wrong").
- **Prediction (support):** off-parity and off-end-behavior decoys are rejected with high precision (parity-XOR and steeper-wins are the crispest axes); off-degree-band decoys rejected at above-chance recall. **Refute** if `R` admits decoys as readily as truths (no discriminative "feels-wrong" faculty).
- **Circular control:** Arm 2 rejects decoys trivially (it encoded the algebra); contrast shows whether the *minted* transform earned its rejection.
- **Honest-negative:** **"feels wrong" is region-exclusion**, not subjective experience. Near a band boundary (a degree that saturates into `higher`, §9c.6) a genuinely-different decoy can fall in the same coarse band and be (correctly, by design) admitted — we report these as expected lossy-band admissions, not detector failures.

**(i-guide) SEARCH GUIDANCE — the FLAGSHIP (promoted from honest-negative; three scored tests).**
For polynomials the felt read *guiding hard computation* is the main event, so it is designed as a real scored test, not a flagged null.

- **(i-guide-1) Felt root-region as root-finder initial guess.**
  - **Seed-map:** as (i1); the felt read yields a real-root **region** ("one real root near origin, one large positive").
  - **Readout/metric:** seed a Newton/root-finder from the **felt region's** representative vs a **naive start** (e.g. 0 or a fixed constant); in the verify step count iterations-to-convergence for each. Report **fraction of true roots whose bracket the felt region contains** (hit-rate + `bootstrap_ci`) and **iterations-saved** (naive − felt-guided), with a paired CI.
  - **Prediction (support):** the felt region **contains/steers toward** the true root and **cuts solver iterations** vs the naive start. **Refute / honest-negative:** if the felt-guided start saves no iterations and the region misses the root at chance, report a clean negative.
  - **Circular control:** Arm 2 (hand-coded transforms) gives a trivially good region; the Arm-1 gap is the earned guidance.
  - **Honest-negative:** iterations-saved is in the verify step's own iteration counter, not wall-clock; a felt region that is correct-but-wide saves fewer iterations and is reported as such.

- **(i-guide-2) FACTORIZATION FEEL — the flagship of the flagship (the polynomial analogue of 7 feeling prime/isolated).**
  - **Seed-map:** as (i1). The felt "factorability" read composes from neutral structural cues available without factoring: rational-root feel (small-integer coefficient structure + low-degree band), low-coefficient-height feel (`coeff-mag-band ∈ {tiny,small}`), symmetry feel (parity/palindromic coefficient structure) → "feels like it factors"; vs high coefficient height, no symmetry, prime-degree band → "feels irreducible/prickly."
  - **Readout/metric:** the felt prior decides **whether to attempt factoring** (and optionally which strategy) *before* spending compute. In the verify step, actually factor; score the felt prior as a binary classifier of factorability — **precision/recall + hit-rate with `bootstrap_ci`** — against a **chance/naive baseline** (always-attempt, or attempt-at-base-rate). Report **compute pruned** = factorization attempts avoided on true-irreducibles × cost-per-attempt.
  - **Prediction (support):** "a product of two linear-with-rational-roots" **feels like it factors**; "a generic prime-ish quintic with large coprime coefficients" **feels irreducible/prickly**; the felt prior **beats the baseline** at deciding when to spend factoring compute. **Refute / honest-negative:** if the factorability feel does not beat base-rate, report a clean negative — this is the sharpest claim and we do not dress it up.
  - **Circular control:** Arm 2 with a hand-coded factorability rule table; contrast the earned Arm-1 prior against the hollow one.
  - **Honest-negative:** the felt prior is a *heuristic gate*, not a decision procedure — it will wave through some irreducibles and balk at some factorables; the value is the **net compute pruned above chance**, reported with the CI, not a claim of correctness.

- **(i-guide-3) DISCRIMINANT-SIGN feel → "real vs complex roots" without computing the discriminant.**
  - **Seed-map:** as (i1); the "real-vs-complex" feel composes from `(degree-parity, root-band, end-behavior, convexity)` — never from an exact discriminant.
  - **Readout/metric:** felt "has real roots" vs "roots are complex" as a binary read; verify by actually computing the discriminant/roots; report **hit-rate + `bootstrap_ci`** vs chance.
  - **Prediction (support):** odd-degree real polynomials feel **"has ≥1 real root"** (they must); `x²+1` feels **"no real roots / complex"**; even-degree positive-leading feels **"may have no real roots."** The felt sign-of-discriminant read **beats chance**. **Refute / honest-negative:** at-chance → clean negative.
  - **Circular control:** Arm 2 hand-codes the discriminant-sign rule; contrast.
  - **Honest-negative:** for even degree the feel is honestly *uncertain* ("may have none") — we score it as a calibrated band, not a crisp bit, and count an honest "unsure" as neither hit nor false-claim.

**(i4) COST — "feel most, solve rarely" as a real compute-economy claim (the payoff is bigger here).**
- **Seed-map:** as (i1); measure both paths on the identical polynomial corpus.
- **Readout/metric:** `capture_minting_cost(...)` for the **felt path** (`counter_ops_total` should sit in the signature-read regime — the same ~55-op scale as the existing minting-cost baseline) vs the **verify path** (coefficient convolution + root-finding + factorization, invoked selectively). Report felt-path ops vs verify-path ops; assert `ask_spy == 0` and the §9c.4 arithmetic-spy (`poly-multiply == 0`, `root-finder == 0`, `factor == 0`, `discriminant == 0`) for the felt window.
- **Prediction (support):** the felt read is **cheap** (signature-read regime), while verification is the **expensive** step (root-finding/factoring is far costlier than the scalar multiply in (h)) invoked only on the fraction of cases that fail (i2)'s sanity check, that (i-guide-2) says are worth factoring, or that need Tier-3 exactness — so aggregate compute drops **more sharply than in (h)** when most reads never trigger a solve. **Refute** if the felt path is not materially cheaper than verification (no economy to the fast-path).
- **Circular control:** Arm 2's hand-coded transforms are *also* cheap but *hollow*; cost is reported **jointly** with (i1) validity — cost alone never rescues a circular transform.
- **Honest-negative:** cost is in the substrate's **native counters**, not wall-clock FLOPs; we claim an *ops-regime* economy. The verify-path cost is a *count of exact-operator invocations*, a proxy for real root-finder/factorizer expense, not a benchmarked runtime.

### 9c.6 Honest new hazard specific to polynomials — unbounded structure vs bounded quanta (must state)

The polynomial structural axes are **unbounded/continuous** — degree is any natural number; coefficients are reals — but the substrate works in **discrete quanta with bounded half-widths** (commitment saturates at ±4, per §5a/§6). So **degree-band and coefficient-magnitude-band SATURATE**: very high degree and very large coefficients collapse into the top band. Concretely we band degree as `{const, linear, quadratic, cubic, quartic, higher}` with the **`higher` band deliberately coarse** (everything ≥ quintic), and coefficient height as `{tiny, small, moderate, large}` with `large` saturating.

This is **fine for the feel** — the feel is *supposed* to be lossy/banded, and this is the *same* saturation the whole design embraces (it is why the read is cheap). But it is a **real design constraint** we state explicitly and keep consistent with the lossy-by-design premise: near the top band, `deg(p·q)=deg p+deg q` **saturates** (`quartic·quartic` and `quintic·quintic` both read `higher`), so the composed region is correctly coarse there rather than wrong — and (i2)/(i-guide) score band-membership, never exact degree. We do **not** widen quanta to escape saturation (that would be tuning constants to manufacture a result, per §6/§9b.6); we report the coarse top band as an honest consequence of the substrate's bounded aperture.

### 9c.7 Honesty boundaries specific to (i)

- **Tier-3 wall is WIDER by design, not a limitation:** no exact roots, no exact factorization, no exact `p·q` coefficient vector, no exact equality of two feels-identical polynomials — the feel narrows to a region; verification recovers the point. The wall is more valuable than the scalar (h) wall precisely because root-finding/factoring is hard (lossiness is *why* it's cheap, and the cheapness buys more here).
- **Composition fidelity is UNPROVEN and is exactly where it can break** — that operand shape-qualia compose into a *faithful* result region is the load-bearing, unproven step, gated by (i1)'s hit-rate-vs-baseline and region-tightness, not asserted. It is more *plausible* here (the transforms are structural, not arithmetic) but still must be earned.
- **The operation-transforms must be minted, never hand-coded** (§9c.3): a hand-written `degree-adds` / `parity-XORs` / `steeper-wins` / `deg−1` table is the (i) form of planting/circularity; the Arm-2 hand-coded control exists to show the hollow version by contrast.
- **No polynomial algebra in the felt path** (§9c.4), proven by the extended spy: 0 poly-multiply / 0 root-finder / 0 factorization / 0 discriminant-eval during the felt window; the exact ops run only in verification.
- **Bounded quanta vs unbounded structure** (§9c.6): degree-band and coefficient-magnitude-band saturate into a deliberately coarse top band; this is embraced lossiness, and we do not widen quanta to escape it.
- **Search-guidance is now a scored flagship, not a null** (§9c.5 i-guide), but it remains a *heuristic gate above chance* (net compute pruned with CI), not a decision procedure; honest-negatives are reported where the felt prior does not beat baseline.
- **Cost is native-ops regime**, not benchmarked runtime (§9c.5 i4); the verify-path cost is a count of exact-operator invocations as a proxy for real root-finder/factorizer expense.
- **"Feels wrong" = region-exclusion**, not subjective experience; near-band-boundary admissions are expected lossy behavior, not detector failures.

---

## 10. Build guards to respect when this is later implemented

- `.so` md5 **frozen** `7efe75eba05b006cafd15dbb4b7da246` — **Python/JSON only**, no native rebuild.
- **Protected / READ-ONLY files** must not be edited; **conceptualizer untouched**; **nothing under `/applications`**.
- **Additive only** — new number-corpus builder, control arm, set/grain driver, and scoring wrappers are new files; existing axes in `seeds/qualia_space.json` and existing runners are **not modified**.
- Remember `asr._QUALIA_SCHEMA_CACHE.clear()` after loading the seed into a fresh Substrate (the `build_category` gotcha).
- Enforce `AskSpy` (teacher-free) and `validate_qualia_space` invariants (`dynamical_is_produced_not_hand_set`, `no_can_bookkeeping`) on every run.

---

### Appendix — pre-registered structural predictions (write into harness before running)

| Set | Predicted top outlier(s) | Reason (structure) |
|---|---|---|
| 1–6 | **5** (then 1) | prime, no in-set multiple; 2,3 have multiples; 4,6 composite |
| 1–10 | **7** (then 1) | zero in-set factors AND multiples; 6-digit decimal cycle; awkward mod |
| 1–12 | **7 and 11** (co-outliers) | 11 = new isolated prime (no in-set factor/multiple); 7 keeps longer cycle (period 6 > 11's period 2), 14∉set so 7 still multiple-free |
| Similarity | 4↔9 (squares); 6↔10 (2·prime); 2,3,5,7 share divisor-absence; 6 central (highly composite) | shared/absent divisor structure |
| (h) composition | `even·even`→even band; `prime·prime`→composite (divisor-present) band; `small·small`→still-smallish magnitude-band; `·`→magnitude-bands add | result-region on shared axes from a **minted** `T_op`; felt region must contain truth above shuffled baseline (h1) and exclude off-parity/off-band decoys (h2) |
| (i) polynomial composition | `deg(p·q)=deg p+deg q` (banded, saturating into `higher`); leading-sign multiplies under `·`; parity XORs under `·` (even·even→even, odd·odd→even); end-behavior of `p+q` = steeper (higher-degree) term wins; `p'` lowers degree one band and drops ≤1 real root (interlacing/smoothing) | result-region on shared shape-axes from **minted** structural `T_op`; region must contain the true (degree, parity, end-behavior, root-band) tuple above shuffled baseline (i1) and exclude off-degree/off-parity/off-end decoys (i2) |
| (i) shape-quale (Tier 1) | odd-degree real poly feels **"has ≥1 real root"**; even-degree positive-leading feels **"may have no real roots"**; `x²+1` feels **"no real roots / complex"** | direct signature read of the neutral shape-axes; scored vs ground-truth structure (i-guide-3) |
| (i) factorability feel (flagship) | product of two linear-with-rational-roots feels **"factors"** (rational-root / low-height / symmetry cues); generic prime-ish quintic with large coprime coefficients feels **"irreducible/prickly"** | felt prior gates whether to spend factoring compute; must beat base-rate at pruning attempts (i-guide-2); polynomial analogue of 7 feeling prime/isolated |
| (i) root-region guidance | felt "one real root near origin, one large positive" **brackets** the true roots and **cuts root-finder iterations** vs a naive start | felt region as solver initial guess; hit-rate + iterations-saved above naive baseline (i-guide-1) |

[STEERING steer-7fe214d9-775f-4b2c-8979-2a98745a5350: Applied throughout. The design seeds ONLY neutral structural connections (divides/has_factor/residue edges + a neutral decimal_cycle_length attr) and lets the qualia coordinates FALL OUT of the CAN fields via concept_signature (either by relaxation or a uniform, per-number-blind structural derivation) — never hand-set. The glyph/shape is never seeded; it is read strictly downstream (sub-exp g) and its correlation with the emergent structural signature is what gets measured. This is stated up front in §0/§1 and enforced by the non-circularity rules and schema invariants.]
