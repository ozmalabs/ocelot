# THE IDENTITY-COST ANATOMY — RESULTS: the 55× coefficient is now 7.4×, and what remains is one unexplained multiplier

*Pre-registration `VISION_IDENTITY_COST_ANATOMY_PREREG.md`, committed at
**`9d7195da`** BEFORE the harness existed and before any measurement. Runner
`scripts/identity_cost_anatomy.py`. Gate
`tests/test_identity_cost_anatomy_migrated.py` **12/12**. Raw rows
`results/identity_cost_anatomy.json` (post-fix) and
`results/identity_cost_anatomy_PREFIX.json` (pre-fix, a real rebuilt binary).
Seeds **78000–78999**.*

---

## 0. PROVENANCE — which binaries produced these numbers

| | |
|---|---|
| branch | **`worktree-agent-aed6c309dbd0f4e2c`** — *not* the intended `gamma-substrate/identity-cost-anatomy`; reported as seen, per the brief |
| base | `6b50b97a` |
| prereg commit | **`9d7195da`** (before the harness existed) |
| **engine, post-fix (the current tree)** | **`d6097900e8b5`** — own build, `scripts/engine_build.sh` |
| **engine, pre-fix (rebuilt for the two-engine arm)** | **`fe3b74943606`** — own build, `scripts/engine_build.sh` |
| provenance gate | `tests/test_engine_provenance_migrated.py` **7 passed**, run as its OWN step before any number, on BOTH engines |
| endpoint guard | `tests/test_provenance_endpoint_guard_migrated.py` **passed**; both endpoints pinned, never `HEAD` |
| oracle bench | **222 passed, exit 0** (`scripts/rung7_vision_bench.sh`, `data/` symlinked) |
| machine | AMD Ryzen 5 9600X, 12 logical cores |
| **concurrent load** | **A concurrent rung was running.** `load1` is a FIELD on every timing row. The post-fix timing arm ran at **`load1` 0.66**; the pre-fix arm at **`load1` 1.79** — reported, and handled in §3.2 rather than waved at |

**The post-fix engine hash is byte-identical before and after the two-engine
detour** (`d6097900e8b5` → `fe3b74943606` → `d6097900e8b5`), and
`git status` on `shape_decode.rs` is clean against `HEAD`. The round-trip is
exact; no probe source survives in the tree.

---

## 1. THE HEADLINE

**Three results.**

1. **THE 698 µs/cell COEFFICIENT IS STALE, AND THE 55× IS NOW 7.4×.** It was
   measured on engine `4d451d8f6ed0`, which **predates the codebook fix**, on
   **exactly the recognising path that fix improved**. Re-measured on two real
   binaries with one variable changed: **731 µs/cell → 94 µs/cell**, a
   **7.36×** fall (load-robust minimum; 7.81× on medians). Against the drive's
   12.6 µs/cell the identity layer is now **7.4× per cell, not 55×**, and the
   real-time affordance moves from **~10×10 to ~28×28** at K=1.
2. **THE PROFILE DID NOT DIVERSIFY — IT CONCENTRATED.** Post-fix, `DimInfer`
   owns **99.10%** of interior units (pre-fix: 99.92%) at **4.0% of
   invocations**. And the coverage test says the profile **is** the coefficient:
   the fixed cost outside Term evaluation is **3.4%** of wall. **My own P5 —
   that this fraction would be large — is WRONG, and being wrong about it is
   what licenses the attribution.**
3. **THE LARGEST REMAINING TERM IS AN INVOCATION COUNT NOBODY HAS EXPLAINED.**
   The closed form is `I × K × 13 × N × 4`. Every factor but one is either real
   data or was **proved non-prunable** by the codebook rung. The exception is
   **`I` = 17**, measured **invariant across a 11.8× range of N and a 16× range
   of K** — and **2, not 17, on the novel path.** **The recognising path spends
   8.5× more invocations than the failing one**, which is precisely why
   compute-∝-surprise, whose *sign* the codebook fix corrected, is stuck at a
   *magnitude* of 1.33. **Named as the reducibility candidate; deliberately NOT
   measured in this rung** (§5).

---

## 2. STEP 0 — G5 ON MY OWN AXES, BEFORE ANY HEADLINE

Two predecessors each validated `term_unit` on one axis and **each had to check
the second**. My workload varies a **third** quantity (PATH) and reads the
profile **post-fix**, where the formerly dominant term has been cut 11×. A
counter validated when `DimInfer` carried 99.92% of the work is not thereby
validated on the profile that replaced it.

**So G5 ran on all three axes, on every `term_unit:*` and `term_eval:*` counter
— not only the two the predecessors reported.** The verdict is handed off to
`runners/dsl/src/g5.rs`; the harness does not reimplement it.

| axis | counter | verdict | series |
|---|---|---|---|
| **SWEEP-N** (K=1, exact) | `term_unit:DimInfer` | **RESPONSIVE** | 10,608 → 125,528 |
| **SWEEP-N** | `term_unit:TransformDecode` | **RESPONSIVE** | 96 → 1,136 |
| **SWEEP-N** | `term_eval:DimInfer` | **BLIND** | **17 at all 7 points** |
| **SWEEP-K** (N=58, exact) | `term_unit:DimInfer` | **RESPONSIVE** | 51,272 → 820,352 |
| **SWEEP-K** | `term_unit:TransformDecode` | **RESPONSIVE** | 464 → 7,424 |
| **SWEEP-K** | `term_eval:DimInfer` | **BLIND** | **17 at all 7 points** |
| **SWEEP-P** (N=58, K=1) | `term_unit:DimInfer` | **RESPONSIVE** | 51,272 → 68,208 |
| **SWEEP-P** | `term_eval:DimInfer` | **RESPONSIVE** | **17 → 2** |
| all three | `term_units_unattributed` | INERT | identically 0 — the diagnostic that **should** stay 0 |

**No charging sites had to be added.** Reported as a *checked pass*: prereg §1
committed me to adding them and saying so had any reported counter come back
INERT or BLIND on an axis I vary, and I would have.

**The two BLIND readings are not a defect — they are a measurement**, and they
are the rung's most important single fact. `term_eval:DimInfer` is BLIND on N
and K because **the invocation count genuinely does not vary with problem
size**; it is RESPONSIVE on P because it genuinely does vary with path. A
counter that reads BLIND where the quantity is constant and RESPONSIVE where it
moves is behaving correctly. §5 rests on this.

### 2.1 THE CROSS-RUNG CONTROL — the chain verified against a published number

`VISION_TERM_EVAL_COUNTER_RESULTS.md` §2.2 committed, at N=142/K=1:
`term_unit:DimInfer` = **1,419,432** and `term_evals_total` = **424**.

**This rung's harness is independently written, on a different seed block
(78000 vs 67000), with a different synthetic generator seed. On the rebuilt
pre-fix engine it reproduces BOTH values EXACTLY.**

| quantity | committed by the term-eval rung | measured here, pre-fix engine |
|---|---|---|
| `term_unit:DimInfer` @ N=142, K=1 | 1,419,432 | **1,419,432** |
| `term_evals_total` | 424 | **424** |

A profile that could not reproduce a number published before this rung existed
would not be readable. This one can, and it is gated
(`test_prefix_harness_reproduces_the_term_eval_rungs_committed_counters`).

---

## 3. THE COEFFICIENT, RE-MEASURED

### 3.1 THE WORKLOAD — stated completely (the bounds clause)

The accumulation line's lesson is that **"K=4" is not a complete description of
a codebook**, so every field is given:

| field | value |
|---|---|
| generator | deterministic LCG synthetic cells, **seed base 78000** |
| N (signature cells) | 12, 20, 37, 58, 93, 123, 142 |
| K (codebook entries) | 1, 2, 3, 5, 8, 12, 16 |
| **codebook contents** | held[0] = the target itself (path `exact`); held[1..] = independent LCG draws, seeds 78100+ |
| path | `exact` = recognised (short-circuit FIRES) · `novel` = nothing explained (short-circuit CANNOT fire) |
| liveness | every point returns `recognized_transformed` — no number is scored at the floor |

### 3.2 THE TWO-ENGINE ARM — a ratio against a real binary

**And the workload caveat I pre-registered dissolved.** Prereg §2 warned that my
synthetic cells are not the video-probe rung's Jellyfin frames, so my µs/cell
would be only indicative. **On the pre-fix engine my workload reads 632–734
µs/cell against that rung's published 698 µs/cell on real video.** The
comparison is closer than I was entitled to assume, and I record it as a
caveat that *measurement retired*, not one I quietly dropped.

| N | pre-fix ms (median) | post-fix ms (median) | **pre-fix µs/cell** | **post-fix µs/cell** | median × | **min × (load-robust)** |
|---|---|---|---|---|---|---|
| 12 | 7.58 | 1.46 | 632.0 | 121.9 | 5.19 | 5.25 |
| 20 | 13.08 | 2.16 | 654.1 | 107.8 | 6.07 | 6.15 |
| 37 | 24.85 | 3.71 | 671.7 | 100.3 | 6.70 | 6.78 |
| 58 | 42.57 | 5.53 | 734.0 | 95.3 | 7.70 | 7.08 |
| 93 | 64.00 | 8.76 | 688.1 | 94.2 | 7.30 | 7.32 |
| 123 | 84.63 | 11.74 | 688.0 | 95.4 | 7.21 | 7.36 |
| **142** | 103.86 | **13.29** | 731.4 | **93.6** | 7.81 | **7.36** |

**LOAD, HANDLED RATHER THAN CAVEATED.** The pre-fix arm ran at `load1` **1.79**,
the post-fix arm at **0.66**. Higher load inflates the pre-fix side and would
**overstate** the ratio. So the load-bearing wall figure is the **minimum**
sample per point (least interference), giving **7.36×** rather than the
medians' 7.81×. The pre-fix medians carry 20–44% spread; the minima carry the
signal. **And the counted ratio below is load-independent and settles it
regardless.**

| quantity, N=142 K=1 exact | pre-fix | post-fix | ratio |
|---|---|---|---|
| **`term_unit:DimInfer`** (counted, load-independent) | 1,419,432 | **125,528** | **11.308** |
| `147 / 13` — the length-1 share, from the seed | | | **11.308** |
| wall (min) | 97.33 ms | 13.22 ms | **7.36** |

**The counted saving is exactly `A / ΣP` to three decimals — the arm that was
removed, not an average.** The wall/counted gap (7.36 vs 11.31) is the fixed
cost outside `DimInfer`, and the codebook rung independently measured that same
gap as 7.32 vs 11.3 on a different workload.

### 3.3 WHAT THE NEW COEFFICIENT MEANS FOR RESOLUTION

| | drive | sd/identity, **as published** | sd/identity, **as re-measured** |
|---|---|---|---|
| per-cell cost | 12.6 µs | 698 µs | **93.6 µs** |
| ratio to drive | 1× | **55×** | **7.4×** |
| real-time affordable cells | 3,305 | 60 | **445** |
| ≈ grid at 55% fill | 57×57 | ~10×10 | **~28×28** |

*(Budget held at the drive's own: 3,305 cells × 12.6 µs = 41.6 ms. The
published 60-cell figure reproduces from it exactly, so the comparison is on
the video-probe rung's own arithmetic, not a new one.)*

**Recognition is still the binding constraint — it is 7.4× the drive, not
1×.** But the gap the brief was written against has already closed by an order
of magnitude, and no rung had noticed.

---

## 4. THE ATTRIBUTION

### 4.1 THE COVERAGE TEST FIRST — because a share is unreadable without it

Prereg §1.1 declared this **before** measuring, because `term_unit` counts work
*inside* Term evaluation and the codebook rung's own residual says cost exists
outside it. Quoting per-variant shares without checking coverage would be the
A8 failure in a new costume.

Fit of wall against `term_units_total` across SWEEP-N (7 points):

| | |
|---|---|
| slope | **0.1015 µs per counted unit** |
| intercept | **0.45 ms** |
| r² | **0.9994** |
| **intercept as fraction of wall at N=142** | **3.4%** |

**P5 IS WRONG.** I predicted the intercept would be ≥25%. It is 3.4%.
**Interior Term work dominates, so the per-variant profile IS the coefficient**
— which is the finding that makes §4.2 quotable. Being wrong here was the good
outcome: the check was worth running precisely because I expected it to
complicate the answer, and it did not.

### 4.2 THE PER-VARIANT PROFILE, POST-FIX — never aggregated

N=142, K=1, path `exact`, one `run_rules` fixpoint, engine `d6097900e8b5`:

| variant | `term_eval` (invocations) | `term_unit` (interior units) | **unit share** | **µs @ 0.1015 µs/unit** | **share of the 13.29 ms** |
|---|---|---|---|---|---|
| **DimInfer** | **17** | **125,528** | **99.10%** | **12,746** | **95.9%** |
| TransformDecode | 2 | 1,136 | 0.90% | 115 | 0.87% |
| Var | 91 | 0 | 0 | — | — |
| Attr | 89 | 0 | 0 | — | — |
| Lit | 78 | 0 | 0 | — | — |
| Eq | 60 | 0 | 0 | — | — |
| Not / And / Count | 19 / 18 / 18 | 0 | 0 | — | — |
| Gt / NodesOfType / Lt / Filter | 10 / 5 / 5 / 5 | 0 | 0 | — | — |
| Neighbours / StringConcat | 2 / 2 | 0 | 0 | — | — |
| IfThenElse / Gte / Or | 1 each | 0 | 0 | — | — |
| **TOTAL** | **424** | **126,664** | | | |
| *(fixed cost outside Term evaluation — §4.1 intercept)* | — | — | — | 453 | **3.4%** |
| | | | | | **sum 100.2%** ✓ |

**THE ANSWER TO "WHERE DOES IT GO NOW": `DimInfer` owns 95.9% of the
coefficient, TransformDecode 0.87%, everything outside Term evaluation 3.4%.**

**The fix did not spread the cost — it concentrated it.** `DimInfer` went from
99.92% to 99.10% of interior units while *everything* got 11.3× cheaper. The
term-eval rung's argument for not pre-aggregating holds exactly as before:
`DimInfer` is **17 of 424 invocations — 4.0%** — and essentially all of the
work. A single total would still have said only "the number went down."

### 4.3 THE CLOSED FORM HOLDS EXACTLY, ON BOTH PATHS

The codebook rung fixed `units = I × K_eligible × A × N × (1+s)` with
measured/predicted = 1.0000. It still holds — **and now with a different `A`
per path**, which is what makes the path axis a measurement rather than a
label:

| path | `I` (read, not assumed) | attempts | closed form | **measured** |
|---|---|---|---|---|
| `exact` (recognised) | **17** | `ΣP` = **13** | 17 × 1 × 13 × 142 × 4 | **125,528** ✓ |
| `novel` (nothing explained) | **2** | `A` = **147** | 2 × 1 × 147 × 142 × 4 | **166,992** ✓ |
| `exact` @ K=16, N=58 | 17 | 13 | 17 × 16 × 13 × 58 × 4 | **820,352** ✓ |

Exact to the unit at every point. `A` = 147 and `ΣP` = 13 **fall out** of the
shipped seed's own `params` `[3,2,2,3,3]` (PROTOCOL §13) and are gated
(`test_attempt_model_falls_out_of_the_shipped_seed`).

---

## 5. THE REDUCIBILITY QUESTION — the candidate, and why it is NAMED and NOT MEASURED

### 5.1 Factor by factor

The remaining coefficient is `I × K × ΣP × N × (1+s)`. Taking each factor:

| factor | value | reducible? |
|---|---|---|
| `N` = cells, `(1+s)` = slots/relation | 142, 4 | **Irreducible.** Real data. This is the arithmetic of comparing a signature to a candidate |
| `K` = codebook entries | 1 | **Irreducible at this layer.** It is the count of things the agent has learned |
| `ΣP` = 13, the length-1 arm | 13 | **PROVED non-prunable by the codebook rung** (its residual §8.1): the Occam key's later components (`residual_dims`, `base_name`, `ks`) *do* discriminate within the arm, so a later attempt can beat an earlier one. A prune here would need a different argument and would **not** be exact |
| **`I` = 17, the invocation count** | **17** | **THE CANDIDATE — unexplained** |

**Three of four factors are irreducible arithmetic or proved non-prunable. The
fourth is the one the codebook rung explicitly recorded as never explained**
(its residual §8.4: *"`I` was read, never explained… why it takes those values
is fixpoint-scheduling behaviour this rung did not investigate"*).

### 5.2 What is MEASURED about `I`

Everything here comes from counters that existed **before this rung began**:

1. **`I` is invariant in N** — 17 at all 7 points over an 11.8× range (G5 BLIND).
2. **`I` is invariant in K** — 17 at all 7 points over a 16× range (G5 BLIND).
3. **`I` is 2 on the novel path** — G5 RESPONSIVE on P, 17 → 2.

**(1) and (2) say `I` is not a function of problem size — it is a scheduling
constant.** (3) says **two invocations are sufficient to reach a fixpoint when
nothing is explained, and seventeen are spent when something is.**

### 5.3 THE SHARPEST FORM — `I` is what caps compute-∝-surprise

The codebook rung's most valuable find was that the old code had
compute-∝-surprise **inverted**, and that the fix corrected it to 1.33. **This
rung can say why it is only 1.33:**

| path | invocations × attempts | total attempt-units |
|---|---|---|
| `novel` (surprising) | 2 × 147 | **294** |
| `exact` (recognised) | 17 × 13 | **221** |
| ratio | | **1.33** |

**The fix made each recognising invocation 11.3× cheaper; the recognising path
then spends 8.5× more invocations.** The property's **sign** was corrected by
the codebook fix; its **magnitude** is held down almost entirely by `I`. A
recognised observation still costs 75% of what a surprising one costs, and the
whole of that is the invocation count.

### 5.4 THE VERDICT — and the discipline that stops it here

**Is the largest remaining term work re-derived that need not be?**

> **NAMED, NOT MEASURED — and deliberately so.** The evidence is strong enough
> to make `I` the single named candidate and too weak to call it redundant.

**What would make it redundant:** if the 17 invocations receive identical
`(residual, codebook, epoch)` arguments, then 15 of them are re-derivation and
up to **88% of the remaining `DimInfer` work** is removable — the batch-apply /
codebook shape exactly, and it would take the recognising path a further ~8.5×.

**What would make it irreducible:** a successful decode **mints graph state**
(Transform nodes, status transitions, `codebook_epoch` bumps) which **re-arms
rules by design**. The 17 invocations may each see a genuinely changed graph, in
which case they are 17 distinct decodes and the cost is real work.

**I cannot distinguish these without an instrument that records each
invocation's arguments — and building that instrument and quoting a redundancy
fraction from it in this same rung is exactly how a statistic gets defined to
suit the answer.** Prereg §4 fixed this before I knew which way it would fall.
It is handed to a successor with the test pre-specified:

> **THE DISCRIMINATING TEST (for a separate rung).** Charge a counter at
> `eval_dim_infer`'s entry recording a hash of `(residual, codebook contents,
> epoch)`. Report **distinct argument-tuples per fixpoint** against `I`.
> `distinct == I` ⇒ irreducible, 17 real decodes, and **the answer must come
> from elsewhere — fewer cells decoded, foveation, or a cheaper recognition
> path.** `distinct ≪ I` ⇒ re-derivation, with the exactness argument then
> owed on the memoisation. **Build the instrument, G5 it on the P axis, and
> only then read it.**

**A negative here is a full result and is pre-committed as one.** If that test
returns `distinct == I`, the identity layer's coefficient is irreducible
arithmetic at 94 µs/cell, resolution is capped by real work at ~28×28, and that
is worth knowing before anyone tries to optimise it.

---

## 6. GATES

| gate | result |
|---|---|
| provenance (run FIRST, own step, both engines) | **PASS** — 7/7 each |
| endpoint guard | **PASS** — both endpoints pinned, never `HEAD` |
| **oracle bench** `scripts/rung7_vision_bench.sh`, `data/` symlinked | **222 passed, exit 0** |
| sd-layer suites (dimension inference / transform / sdloop / ink / codebook-axis / term-eval) | **95 passed** |
| **new gate** `tests/test_identity_cost_anatomy_migrated.py` | **12/12** |
| G5 on all three axes | RESPONSIVE / BLIND as tabulated in §2; unattributed INERT throughout |
| engine round-trip | `d6097900e8b5` → `fe3b74943606` → **`d6097900e8b5`** byte-identical; `shape_decode.rs` clean vs `HEAD` |
| no behaviour changed | this rung adds a harness, a gate, and two documents — **no `.rs` and no seed edit survives** |

---

## 7. PREDICTIONS — 4 right, 2 wrong, and both wrongs are load-bearing

| | prediction | outcome |
|---|---|---|
| **P1** | the 698 µs/cell is STALE; post-fix ≥5× lower on two real binaries | **RIGHT** — **7.36×** (load-robust), 731 → 94 µs/cell |
| **P2** | `term_unit:DimInfer` RESPONSIVE on N and K with no new charging sites | **RIGHT** — checked, not assumed |
| **P3** | `term_unit:DimInfer` comes back INERT or BLIND on SWEEP-P | **WRONG** — **RESPONSIVE** (51,272 → 68,208). I expected the counter to aggregate over both arms and hide the path; it separates them cleanly, which is what turned the path axis into a measurement instead of a label |
| **P4** | `DimInfer` still owns >80% of interior units post-fix | **RIGHT** — **99.10%** |
| **P5** | the coverage intercept is LARGE (≥25% of wall) | **WRONG** — **3.4%**. The good kind of wrong: it means `term_unit` covers 96.6% of the coefficient and the per-variant profile IS the attribution. Had I not declared the check I would have had to assume this |
| **P6** | the reducibility candidate is INVOCATION-level, not interior-arithmetic | **RIGHT in direction, and explicitly NOT CLOSED** — `I` is the named candidate on measured invariance (§5.2), and §5.4 refuses to call it redundant without the instrument |

---

## 8. HONEST RESIDUALS — named, not fixed

1. **`I` = 17 is still unexplained.** This rung measured that it is invariant in
   N and K and differs by path; it did not measure *why* the scheduler runs it
   17 times. That is §5.4's handoff and is the single highest-value open
   question in the layer.
2. **The wall-clock arms ran under different load** (1.79 pre-fix vs 0.66
   post-fix). Mitigated by reporting minima and by the load-independent counted
   ratio, but a solo re-run of the two-engine arm would tighten §3.2. The
   counted 11.31× is not affected.
3. **`ΣP` = 13 remains exhaustive**, inherited from the codebook rung's residual
   §8.1 and **not** reopened here. If `I` turns out irreducible, this arm is the
   next place to look — but it needs the different argument that rung named, not
   this one.
4. **One workload, one path pair.** Everything is measured on synthetic LCG
   cells at K ≤ 16 with the target as held[0]. The video-probe rung's Jellyfin
   agreement (§3.2) is reassuring but is a single cross-check, not a corpus. The
   identity layer's cost may still depend on codebook *contents* in ways one
   decoy family cannot show — the accumulation line's grown-codebook noise-floor
   finding is unexercised here.
5. **`TransformDecode` at 0.87% was not investigated.** It is second in the
   profile and three orders of magnitude below first; it is named as measured
   and left alone.
