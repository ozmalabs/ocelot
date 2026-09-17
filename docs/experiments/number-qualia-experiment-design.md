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

---

## 9. Honesty boundaries (explicit)

- **Correlation, not causation** for glyph-downstream (§5g): we show structure predicts shape and that shape is *removable without losing the outlier*, plus label invariance — we do **not** manipulate a glyph and observe the quale, because the substrate has no such lever.
- **Notation-independence is testable here only structurally** (§6): independence from the *attached label*, not from all human notations.
- **No arithmetic / no subjective effort** (§5c): "felt difficulty" is operationalized as signature-distance from a regularity cluster; the substrate does not compute products or experience effort.
- **Substrate figures as-given** (§6): quanta, half-widths, and `commitment` saturation come from the seed unchanged; results are reported as ordinal, within the substrate's discretization, and we do not tune constants to manufacture separation.
- **Minting is graph-owned** (§5d): Python never mints; thresholds gate it; report mint/no-mint honestly with counters.
- **`find_analogies` mutates the graph** (§5b): run on a snapshot/copy.

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

[STEERING steer-7fe214d9-775f-4b2c-8979-2a98745a5350: Applied throughout. The design seeds ONLY neutral structural connections (divides/has_factor/residue edges + a neutral decimal_cycle_length attr) and lets the qualia coordinates FALL OUT of the CAN fields via concept_signature (either by relaxation or a uniform, per-number-blind structural derivation) — never hand-set. The glyph/shape is never seeded; it is read strictly downstream (sub-exp g) and its correlation with the emergent structural signature is what gets measured. This is stated up front in §0/§1 and enforced by the non-circularity rules and schema invariants.]
