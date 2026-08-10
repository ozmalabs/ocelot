# PEER COMPETITION — RESULTS: the peer competition IS the refusal mass and is NOT the size blocker. **NO MECHANISM IS WARRANTED HERE.** The ceiling is the component field: its median member is ONE CELL.

*Pre-registration: `VISION_PEER_COMPETITION_PREREG.md`, committed **`1a02db002e12cef87163d172a6794bf42faf26e3`** BEFORE any
number. Nothing in it was edited after the first number. **This rung reports the outcome
it pre-registered as outcome 1 (CEILING-BOUND), and it builds nothing** — the
containment rung's own lesson, taken as an instruction rather than as a compliment.*

**ENGINE PROVENANCE (§10)** — printed from **inside** the measuring process into
`results/peer_competition.json` and `results/peer_competition.log`:

```
engine a1d350bbd23b @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so
  [1 other tree build(s) shadowed]
```

Branch `worktree-agent-a37faa572b1a469f0`, base
**`77e932f12d6f64a735775b0083c137f9d5df532b`**. Engine built in-tree by
`scripts/engine_build.sh`; **no Rust change in this rung**. Migrated provenance gate run
as **its own step, first: 7 passed**. `data/` is a symlink to canonical (§10.2), never a
copy. The run aborts on `WRONG ENGINE` / `DIVERGED`.

---

## 1. THE HEADLINE

**The containment rung's finding is confirmed and its lever is priced — and the price is
that the lever is not worth pulling.**

| | C1 cartoon | C2 live-action |
|---|---|---|
| enclosed components (224 tiles, 18×18) | 5,047 | 3,978 |
| refused by `G_own_lost` against a peer | **4,357 (86.3%)** | **3,181 (80.0%)** |
| **median peer count** | **3** | **3** |
| components passing, ARMED (v1.2.0 standing) | 152 | 299 |
| components passing, **PEER COMPETITION REMOVED ENTIRELY** | **224** | **398** |
| **median size of what passes — armed → no-peer** | **1 → 1** | **1 → 1** |
| **max size of what passes — armed → no-peer** | **13 → 13** | **15 → 15** |
| **median size of the COMPONENTS THEMSELVES** | **1** | **1** |
| largest component in a tile (median / max) | 11 / 66 cells | 11 / 50 cells |
| largest component as a fraction of the 324-cell tile (median) | **3.4%** | **3.4%** |

**The peer competition really does carry the refusal mass — 80–86% of all components,
exactly as the containment rung predicted.** Lifting it entirely buys **+47% (C1) /
+33% (C2) more objects and ZERO change in the median size, and not one cell of change in
the maximum.** By the brief's own standing instruction — *"a rung that reports N went from
7.1 to 4.2 while the median stays at 2 has produced fragments, more slowly"* — this is
that rung's mirror image, and it is a **null for the mechanism and a positive finding
about where the constraint lives.**

**Why no predicate over these components can produce few-and-large: the components ARE
the fragments.** Minting is a *selection*; the median enclosed component is **one cell**,
p90 is 4–5 cells, and the biggest component anywhere in 224 tiles is 66 cells = 20% of one
tile. The proto-size distribution has been pinned at median 1–2 in every rung of this arc
because **the size distribution it selects from is pinned there.**

---

## 2. THE PEER COMPETITION, CHARACTERISED WITH NO MECHANISM (the brief's first instruction)

### 2a. How many peers does a typical component face? — **three**

| | all components | components refused by `G_own_lost` |
|---|---|---|
| C1 median / mean / p90 / max | 3 / 3.10 / 5 / **22** | 3 / 3.39 / 5 / 22 |
| C2 median / mean / p90 / max | 3 / 2.85 / 5 / **17** | 3 / 3.29 / 5 / 17 |

`G_own_lost` is a **universal quantifier**: R must beat *every* abutting rival. At a
median of 3 rivals that is three independent chances to lose, and the refused population
faces slightly *more* rivals than the general one (3.39 vs 3.10) — as it must.

### 2b. What is the distribution of `perim` among them? — **it is the size distribution, and its median is 1**

`rim` (the rule's perimeter statistic) over all components: C1 median **1**, mean 1.97,
p90 4, max 51; C2 median **1**, mean 2.23, p90 5, max 32. For a component of ≤ 4 cells
every cell is a contour cell, so **`rim` ≡ size over most of the field**, and
`perim(R) < perim(Q)` is a size comparison in all but name.

### 2c. When `perim(R) < perim(Q)` refuses, what would have had to be true? — **usually nothing at all: it is a TIE**

Margin = `min_rivals rim(Q) − rim(R)`, ≤ 0 by construction of a block:

| | refusals | **TIE-ONLY** (every blocker exactly equal) | strict loss | median margin |
|---|---|---|---|---|
| C1 | 4,357 | **2,965 = 68.1% [66.7, 69.4]** | 1,392 | **0** |
| C2 | 3,181 | **1,950 = 61.3% [59.6, 63.0]** | 1,231 | **0** |

**The modal refusal is a tie between two singletons.** Median margin 0; median
blocker-size ratio 1.0 — the typical blocker is *the same size as the component it
blocks*. This is not a defect in the predicate. It is what a competition on a field of
one-cell components must look like, and the rule holding a tie open is the behaviour it
was derived to have.

Priced separately, since it is the cheapest conceivable change: **allowing ties**
(refuse only on a strict loss) moves C1 152 → 197 and C2 299 → 356 passes, and moves the
median size **1 → 1**. It also moves the *mean* size **down** (1.59 → 1.51 C1), because
what it admits is overwhelmingly more singletons.

### 2d. Is there a component that should win and doesn't? — **YES, and here it is**

The **largest** enclosed component in each tile — median 11 cells, up to 66:

| | tiles | largest passes | refused by `G_own_lost` | refused by `G_gnd2` | **median size of its smallest blocker** |
|---|---|---|---|---|---|
| C1 | 111 | **4 = 3.6% [1.4, 8.9]** | **97** | 10 | **1 cell** |
| C2 | 112 | **9 = 8.0% [4.3, 14.6]** | **94** | 9 | **1 cell** |

**An 11-to-66-cell region is vetoed by a ONE-CELL neighbour, in 86% of tiles.** That is
the size prior pointing the wrong way, measured at the peer level and pointed at, exactly
as the surface rung diagnosed it one level up. The gate histogram is **identical under all
four arms** (`incumbent` refuses the same 97 by `G_figadj`) — **no committed predicate in
this seed, including both derivations this rung was told to compose with, changes the fate
of the largest component in a tile.**

### 2e. And yet lifting the whole competition rescues at most ONE of them

This is the number that decides the rung. Under the NO-PEER ablation, C1's passing sizes
are `{1:144, 2:53, 3:16, 4:3, 5:3, 7:1, 8:1, 9:1, 10:1, 13:1}` — **exactly one component
of size ≥ 11 passes, across 111 tiles**, while ~56 of those tiles have a largest component
of ≥ 11 cells. **Removing the entire peer competition rescues at most one large component
in 111 tiles.** The rest are then refused by the gates *downstream* of the competition —
ill-posedness and single-ground-closure — which are not size tests and behave like one on
this material.

**⇒ Answering the brief's question directly: the peer competition is where the refusals
ARE, and it is not where the size failure IS. Those are different questions, and the
containment rung's measurement answered the first.**

---

## 3. THE DECISION: NO MECHANISM IS WARRANTED — stated explicitly, as the brief required

Pre-registered outcome **1, CEILING-BOUND** (`PREREG §0.3`, decision rule §5). Two
independent ceilings sit above anything a peer mechanism could reach:

1. **THE REPRESENTATIONAL CEILING.** The component field's median member is **1 cell**;
   its largest member is 3.4% of a tile at the median. No selection over these components
   can emit a few-and-large object, because none is present to select. This is prior to
   every predicate and unaffected by all four arms.
2. **THE DOWNSTREAM-GATE CEILING.** With the peer gate lifted entirely, the maximum
   passing size is **unchanged** (13 / 15 cells) and the yield is ~2 components per tile.
   A peer mechanism cannot exceed its own ablation.

**A mechanism here would be a rule change whose entire reachable effect is a 33–47%
count increase on objects whose median size is one cell.** That is fragments, faster.
Building it would repeat this rung's predecessor's error one level along: a derivation
composed correctly with the two standing ones, gated, injection-controlled, default-off —
and inert against the thing the arc is actually after.

**THE NAMED NEXT LEVER IS UPSTREAM, AND IT IS THE GROUPING, NOT THE MINT.** Components
are formed by `bo_bgflood` / `bo_label` flooding through **exactly-equal** quantized
values at k=16. Exact-value equality on a 16-level per-frame quantization of natural video
produces a field of singletons — measured here, 5,047 components in 224 tiles with median
size 1. Any rung that wants large objects must change **what makes two cells the same
region**, not **which region wins**. That is a different pre-registration with a different
mechanism-level hypothesis (§3 clause 6), and this rung deliberately does not start it.

---

## 4. THE FLOOR THAT DID **NOT** RE-EARN — and it is the standing arm's own registered control

**Instructed to re-earn speckle 0/100. I measure 2/100, and the failure is real,
reproducible, and diagnosable.**

| speckle draw | incumbent | replacement | **wellposed (standing)** | nested |
|---|---|---|---|---|
| **96700 (mine, fresh)** | 0/100 | 26/100 | **2/100** | **2/100** |
| 89900 (wellposed rung's registered M-A) | 0/100 | **22/100** | **0/100** | 0/100 |
| 36000–36099 (incumbent block) | 0/100 | 27/100 | **0/100** | 0/100 |
| 92700 (nesting rung, 20 fields) | 0/20 | 3/20 | **0/20** | 0/20 |

**My harness reproduces both published numbers to the unit** — the wellposed rung's
`replacement 22/100` and `wellposed 0/100` at seed 89900, and 0/100 at 36000–36099 — so
the 2/100 is **the draw, not the instrument**. Pooled in-tree: **2/320 = 0.63%
[0.17, 2.25]**. A 0/100 observation never licensed "zero"; its own 95% upper bound is
**3.7%**, and 0.63% sits comfortably inside it. Two committed 0/100s were **compatible
with the rate I measured all along.**

**The two survivors, characterised — and they are precisely the case the derivation's own
table shows it cannot separate.** Both are single-cell noise components with `rim = 1`
facing **exactly ONE distinct enclosed rival** and one ground component. The published
discriminator table reads *"distinct surrounding enclosed components: **2, 3 or 4 — never
≤ 1**"*, measured over **n = 31 observed false protos** — and its own next column records
that the case that must survive (*two abutting figures*) faces **exactly 1**. So a noise
singleton that happens to face exactly one rival is, to the predicate, **identical to a
genuine figure**, and no amount of the same conjunct separates them.

**This is the recorded standing rule firing again, on a committed gate: a detector built
from observed instances covers observed instances.** 31 false protos all faced 2–4
rivals; that felt like a discriminator and was a sample. **It retracts nothing about the
well-posedness derivation** — the conjunct removes 24 of 26 speckle false mints, which is
what it was built to do and what it still does — but **"0/100" must be restated as
"≈0.6% [0.2, 2.3], not zero"**, and any future gate asserting `== 0` on a fresh draw is
asserting something this measurement says will eventually fail.

---

## 5. GATES — every other floor RE-EARNED IN THIS TREE, ON THIS ENGINE, NOTHING INHERITED

| gate | result |
|---|---|
| **Oracle** `bash scripts/rung7_vision_bench.sh`, **before** | **222 passed / 0 failed** (with `data/`) |
| **Oracle, after** | **222 passed / 0 failed** |
| Provenance gate, its own step, first | **7 passed** |
| `test_border_ownership_migrated` + `_wellposed_` + `_nesting_` | **31 passed** |
| Synthetic D1 12×12 figure, all four arms | **reproduces (1 proto, 24 members) × 4** |
| Dead-instrument arm D2b, all four arms | **fired × 4** |
| **A genuine single-cell figure still mints** | **all four arms** |
| Speckle 0/100 | **FAILED — 2/100, §4** |

**THE COST TABLE RE-EARNS TO THE DIGIT — every published number of both predecessor
rungs, reproduced in this tree on this engine:**

| corpus | arm | components/frame | protos/frame | **multicell/frame** | published |
|---|---|---|---|---|---|
| C1 | incumbent | 721.0 | 7.7 | **3.3** | 7.7 / **3.3** ✅ |
| C1 | replacement | 721.0 | 49.0 | **10.0** | 49.0 / **10.0** ✅ |
| C1 | **wellposed** | 721.0 | 21.7 | **7.1** | 21.7 / **7.1** ✅ |
| C2 | incumbent | 568.3 | 24.6 | **10.7** | 24.6 / **10.7** ✅ |
| C2 | replacement | 568.3 | 69.6 | **17.1** | 69.6 / **17.1** ✅ |
| C2 | **wellposed** | 568.3 | 42.7 | **14.4** | 42.7 / **14.4** ✅ |

`nested` (v1.3.0) is byte-identical to `wellposed` on every real-frame row, independently
re-confirming the containment rung's `D = 0` on a wholly separate read-out.

**§9** — this rung adds **no** Rust, **no** seed, **no** rule, **no** node and **no**
flag. `git diff --stat -- seeds/ runners/` is **empty**; byte-identity is by construction,
and the oracle is 222/0 either side.

### 5.1 The instrument checks that had to fire, and did

- **READ-OUT RECONCILIATION `G_pass == n_protos`: TRUE on every row, every arm, both
  corpora (56 rows).** The classification in §2 is therefore measuring the *rules*, not
  this Python.
- **`rim` RECONCILIATION: 0 mismatches on every armed row.** The one quantity the whole
  competition turns on is recomputed from the settled graph and agrees with the attribute
  the rule wrote — *a diagnostic must not be computed by the component it checks.*
  (Under `incumbent`, `bo_rim` is not armed and `rim` is never written; its non-zero
  mismatch count is that absence and is **not** a failure. Stated rather than hidden.)
- **ABLATION LIVENESS.** NO-PEER changes the pass count on all three ownership arms
  (`LIVE = True`). Under `incumbent` it is **`LIVE = False` BY CONSTRUCTION** — that arm
  has no ownership competition to lift — and is reported as **structurally inert, not as
  a null**. Exposure counted everywhere: no statistic in this document is computed over
  zero triggers.
- **Settling**: every real-frame row reached the fixpoint; no unsettled graph was read.
- **Pins verified in-run**: C1 `08630d4b`, C2 `119eca43`; a mismatch voids the run.

---

## 6. SCOPE — WHAT IS NOT SHOWN (§8)

- **The NO-PEER and TIES-ALLOWED ablations are READ-OUT ablations, not rules.** No rule
  exists that behaves that way, so they are not reconciled against one. What licenses them
  is that the *armed* path of the same code reconciles exactly against the rules' minted
  output on all 56 rows; the ablations are that identical gate chain with one conjunct
  lifted. They are an **upper bound on a mechanism, not a measurement of a mechanism.**
- **ONE GRAIN.** G72, `REGION=18`, `k=16`, the incumbent per-frame min/max quantizer, two
  corpora. The resolution rung already measured that component structure changes sharply
  with tile size, so **the ceiling claim is specific to this configuration** and is exactly
  the kind of claim that should be expected to move when the grain does. That is not a
  hedge — it is why §3's named lever is the grouping.
- **No claim that a grouping change would work.** §3 names where the constraint lives; it
  does not show that anything fixes it. "The lever is upstream" is a diagnosis.
- **No mechanism was built, so no mechanism is validated.** There is no AST §13 gate and
  no injection control in this rung, because there is no conjunct to gate — stated so that
  their absence is not read as an omission.
- **The 66-cell maximum component is 20% of a tile, not an object.** Nothing here says any
  component corresponds to a thing in the world; the ceiling argument is about sizes only.
- **`nested`'s agreement with `wellposed` on real frames is a re-confirmation at ONE
  grain**, inheriting the containment rung's own scope note that it may not hold at others.

---

## 7. WHAT I GOT WRONG — in full

1. **PREDICTION 1 WAS RIGHT IN DIRECTION AND WRONG IN MAGNITUDE, AND THE MAGNITUDE WAS
   THE POINT.** I predicted the component field was "already fragments — median ≈ 2". It
   is **1**. I had anchored on the brief's "median size 2 cells" — which is the **proto**
   median from previous rungs — and assumed the components it selects from were similar.
   They are smaller. Being off by one cell would not matter if the ceiling argument did
   not turn on exactly how small; it does, and I should have predicted the quantity I was
   actually going to reason from.
2. **I DID NOT PREDICT THE SECOND CEILING AT ALL.** My prereg framed one ceiling (the
   component field). The measurement found a second, independent one — the downstream
   gates cap the max passing size at 13/15 **even with the peer competition entirely
   removed**, and under `replacement` the same ablation admits up to 37. That means the
   **well-posedness conjunct (v1.2.0) is itself size-capping once the peer gate is
   lifted**, a cost nobody has priced, and I found it by accident rather than by design.
   I am recording it as an observation, **not** as a claim about v1.2.0 — testing it is a
   prospective pre-registration, not a reinterpretation of this data (§5).
3. **PREDICTION 3 WAS HALF WRONG.** I predicted ties would be "a large share" of blocks
   and that removing them "leaves most refusals standing". Ties are **68% / 61%** — not
   "a share", the **majority** — and removing them leaves 32%/39%. The direction held;
   I understated the dominance of the tie case, which is the single most informative
   number about what this competition actually is.
4. **THE SPECKLE FLOOR CAUGHT ME BELIEVING A ZERO.** I copied "re-earn speckle 0/100" into
   my prereg §3.4 as a floor to be re-earned, i.e. **as a fact**, without noticing that
   0/100 bounds a rate at 3.7% and cannot establish zero. Had my draw also returned 0 I
   would have written "re-earned ✅" and propagated a false certainty. **I got the right
   answer from an unlucky draw, not from having thought about it** — the diagnosis in §4
   was written after the number, not before it.
5. **PREDICTIONS 1 AND 2 WERE THE SAME BET AND I SAID SO IN ADVANCE — which limits, and
   does not rescue, the evidence.** They cannot independently confirm each other. What
   carries §3 is not the pair of predictions but §2e, which was not predicted at all.
6. **I very nearly reported P6 without checking it across arms.** The 4/111 is identical
   under all four arms; had I read only the primary arm I would have written "the
   ownership competition refuses the largest component" when the correct statement is
   "**every** committed predicate refuses it, including the one that has no ownership
   competition" — a materially stronger and differently-directed finding.

---

## 8. SEEDS — 96000–96999

**Measured, `unknown_sinks: 0`, none outside the block:**

| seed | consumed by | status |
|---|---|---|
| **96700** | `peer_competition_measure.floors` — 100-field speckle control × 4 arms | **BURNED** |
| 96701 | reserved (prereg §6) for a speckle superset check | **not drawn** |

```
$ python3 scripts/seed_audit.py --check 96000 96999 scripts/peer_competition_measure.py
{"declared": [96000, 96999], "ok": true, "outside": []}      unknown_sinks: 0
```

**DISCLOSED OUT-OF-BLOCK DRAWS:** the §4 reproduction control deliberately re-drew
**89900**, **36000–36099** and **92700** — all **already-burned** seeds of the wellposed,
incumbent and nesting rungs — for the sole purpose of reproducing their *published*
controls in this tree. They carry **no confirmatory weight** in this rung and consume no
new seed; recorded here rather than left to inference. The verbatim `check_claim` output
for 96000–96999, **including its 497 unresolved sinks**, is in PREREG §0.1.

---

## 9. LEDGER ROW (carried here — `VISION_PROTOCOL.md` NOT edited)

| **96000–96999 (1 draw measured — 96700; unknown_sinks 0, none outside block; 3 disclosed re-draws of ALREADY-BURNED predecessor seeds for reproduction only)** | **THE PEER COMPETITION IS THE REFUSAL MASS AND IS NOT THE SIZE BLOCKER — NO MECHANISM WARRANTED, AND THE RUNG BUILDS NOTHING.** Instructed to price the lever the containment rung named, and to run the cheap diagnostic BEFORE any derivation (that rung's own sharpest self-criticism). **The diagnostic killed the mechanism, which is what a cheap diagnostic is for.** **CONFIRMED: `G_own_lost` refuses 4,357/5,047 (86.3%) of components in C1 and 3,181/3,978 (80.0%) in C2, against a MEDIAN OF 3 PEERS (max 22) — the containment rung's 17/17 generalises.** **REFUTED AS A LEVER: lifting the ENTIRE peer competition (read-out ablation, armed path reconciled `G_pass == n_protos` on 56/56 rows) moves the count 152→224 (C1, +47%) and 299→398 (C2, +33%) and moves the MEDIAN PASSING SIZE 1→1 AND THE MAXIMUM 13→13 / 15→15 — NOT ONE CELL.** **THE CEILING, MEASURED: THE COMPONENT FIELD'S MEDIAN MEMBER IS ONE CELL** (p90 4–5; largest component anywhere in 224 tiles 66 cells = 20% of a tile; median largest-per-tile 11 cells = 3.4% of a tile). **Minting is a SELECTION, so the component-size distribution is a HARD UPPER BOUND on the proto-size distribution — the arc's median-2 fragments are pinned by what is available to select, not by which predicate selects it.** **AND A SECOND, INDEPENDENT CEILING, UNPREDICTED: with the peer gate lifted the max passing size is UNCHANGED because the downstream gates cap it — under `replacement` the same ablation admits up to 37 cells, so the v1.2.0 WELL-POSEDNESS CONJUNCT IS ITSELF SIZE-CAPPING once the peer gate is gone (recorded as an OBSERVATION, not a claim; testing it needs its own prereg, §5).** **THE COMPONENT THAT SHOULD WIN AND DOESN'T, POINTED AT: the LARGEST component in a tile (median 11, max 66 cells) passes 4/111 = 3.6% [1.4, 8.9] (C1) and 9/112 = 8.0% [4.3, 14.6] (C2); 97/94 of the refusals are `G_own_lost` and THE MEDIAN SMALLEST BLOCKER IS A SINGLE CELL — an 11-to-66-cell region vetoed by one cell. THE GATE HISTOGRAM IS IDENTICAL UNDER ALL FOUR ARMS, so NO committed predicate — including BOTH derivations this rung was told to compose with — changes the fate of the largest component; and lifting the whole competition rescues AT MOST ONE of them in 111 tiles.** **THE MODAL REFUSAL IS A TIE BETWEEN TWO SINGLETONS: 68.1% [66.7, 69.4] (C1) / 61.3% [59.6, 63.0] (C2) of refusals are TIE-ONLY, median margin 0, median blocker-size-ratio 1.0 — and `rim` ≡ size over most of the field, so `perim(R) < perim(Q)` is a size comparison in all but name.** **THE SPECKLE FLOOR DID NOT RE-EARN AND THE FAILURE IS DIAGNOSED: 2/100 at fresh seed 96700 under the STANDING wellposed arm (and nested), where the committed claim is 0/100 — MY HARNESS REPRODUCES BOTH PUBLISHED NUMBERS TO THE UNIT at their own seeds (replacement 22/100 and wellposed 0/100 at 89900; 0/100 at 36000–36099), so IT IS THE DRAW, NOT THE INSTRUMENT. Pooled in-tree 2/320 = 0.63% [0.17, 2.25] — and a 0/100 observation's OWN 95% UPPER BOUND IS 3.7%, so the two committed zeros were compatible with this rate all along. BOTH SURVIVORS ARE SINGLE-CELL NOISE FACING EXACTLY ONE ENCLOSED RIVAL — the configuration the derivation's OWN published table lists for `two abutting figures`, i.e. THE CASE IT CANNOT SEPARATE BY CONSTRUCTION. The discriminator was fitted to n=31 observed false protos that all faced 2–4 rivals: A DETECTOR BUILT FROM OBSERVED INSTANCES COVERS OBSERVED INSTANCES, firing here on a COMMITTED GATE. Retracts nothing about the derivation (it still removes 24 of 26) but `0/100` must be restated as `≈0.6% [0.2, 2.3], NOT ZERO`.** **EVERY OTHER FLOOR RE-EARNED IN-TREE, NOTHING INHERITED: oracle 222/0 BEFORE AND AFTER; provenance its own step 7 passed; border-ownership migrated 31 passed; D1 reproduces and D2b fires on ALL FOUR ARMS; a GENUINE SINGLE-CELL FIGURE STILL MINTS on all four; `rim` reconciliation 0 mismatches on every armed row; AND THE FULL COST TABLE OF BOTH PREDECESSOR RUNGS REPRODUCED TO THE DIGIT — 7.7/3.3, 49.0/10.0, 21.7/7.1, 24.6/10.7, 69.6/17.1, 42.7/14.4, comps 721.0/568.3 — with `nested` byte-identical to `wellposed` on every real-frame row, independently re-confirming the containment rung's `D=0` on a separate read-out.** §9 trivial: NO Rust, NO seed, NO rule, NO flag; `git diff -- seeds/ runners/` EMPTY. **NAMED NEXT LEVER — UPSTREAM, AND IT IS THE GROUPING NOT THE MINT: components are formed by flooding through EXACTLY-EQUAL quantized values at k=16, and exact-value equality on natural video yields a field of singletons. A rung that wants large objects must change WHAT MAKES TWO CELLS THE SAME REGION, never WHICH REGION WINS. Not started here — that is its own pre-registration with its own mechanism-level hypothesis.** **WHAT IT GOT WRONG: PREDICTED THE COMPONENT MEDIAN AS 2, IT IS 1 — I anchored on the PROTO median from the brief and reasoned from a quantity I had not predicted; DID NOT PREDICT THE SECOND CEILING AT ALL and found the v1.2.0 size-cap by accident; UNDERSTATED TIES as `a large share` when they are the MAJORITY; COPIED `speckle 0/100` INTO MY OWN PREREG AS A FACT TO RE-EARN without noticing 0/100 cannot establish zero — had my draw also returned 0 I would have propagated the false certainty, so I got the right answer from an unlucky draw rather than from thinking; DECLARED IN ADVANCE that predictions 1 and 2 were the same bet, which limits rather than rescues them (what carries the rung is §2e, which I did not predict); and NEARLY REPORTED P6 FROM THE PRIMARY ARM ALONE, which would have said `the ownership competition refuses the largest component` instead of the true and stronger `EVERY committed predicate does, including the one with no ownership competition`.** |
