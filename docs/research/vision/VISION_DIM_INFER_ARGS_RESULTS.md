# `I` = 17 — RESULTS: **it is not a scheduling constant, it is a COUNT OF TERM SITES IN A JSON FILE**, and the seventeen invocations are ONE decode computed seventeen times

*Pre-registration `VISION_DIM_INFER_ARGS_PREREG.md`, committed at **`a04758ee`**
BEFORE the instrument existed and before any measurement. Headline pinned at
**`37510dff`**, BEFORE the diagnostic that explains it existed. Runners
`scripts/dim_infer_args.py` (measurement) and
`scripts/dim_infer_args_diagnose.py` (diagnostic). Gate
`tests/test_dim_infer_args_migrated.py` **11/11**. Raw rows
`results/dim_infer_args.json` and `results/dim_infer_args_diagnose.json`.
Seeds **88000–88999**.*

---

## 0. PROVENANCE — which binaries produced these numbers

| | |
|---|---|
| branch | **`worktree-agent-a35988cad8213aa72`** — reported as seen, per the brief |
| base | **`e8bf3987`** |
| prereg commit | **`a04758ee`** (before the instrument existed) |
| headline commit | **`37510dff`** (before the diagnostic existed) |
| **engine, headline run** | **`58008033c66d`** — own build, `scripts/engine_build.sh` |
| **engine, final (adds two diagnostic accessors)** | **`87a8ab4f650b`** — own build, `scripts/engine_build.sh` |
| provenance gate | `tests/test_engine_provenance_migrated.py` **7 passed**, run as its OWN step BEFORE any number, on BOTH engines |
| endpoint guard | `tests/test_provenance_endpoint_guard_migrated.py` **passed**; both endpoints pinned, never `HEAD` |
| oracle bench | **212 passed / 10 skipped, exit 0** (`scripts/rung7_vision_bench.sh`, no `data/` in this worktree — the documented 212/10 form) |
| machine | AMD Ryzen 5 9600X, 12 logical cores |
| **concurrent load** | **Four other rungs were running.** `load1` was **2.21** at the headline run and **0.88** at the confirmation run. **Every number in this document is a COUNT** — load-independent by construction. No wall-clock figure is reported or relied on anywhere |

**The headline is identical on both engines** (`I` = 17, `distinct` = 10 on
`58008033c66d` and again on `87a8ab4f650b`), so nothing here depends on the
diagnostic accessors that distinguish them.

**Seeds — MEASURED, not declared.** The static auditor
(`scripts/seed_audit.py`) returns **empty** for this rung's files: the LCG is
hand-rolled rather than a `default_rng`/`seed=` call, which is one of that
tool's own recorded blind spots. So the draws were measured directly, by
spying on `synth_cells` across **every arm the harness runs**:

```
88000, 88100–88115   — 17 distinct seed integers, all inside 88000–88999
```

`check_block(…, 88000, 88999)` also returns `ok: true, outside: []`, but that
is a vacuous pass given the tool saw nothing; the enumeration above is the
real report.

---

## 1. THE HEADLINE

**Three results, and the third supersedes the question.**

1. **THE PRE-REGISTERED ANSWER: `distinct` = 10 against `I` = 17.** Neither
   pre-committed extreme. By the prereg's own decision rule (§5), `distinct < I`
   ⇒ **REDUCIBLE**. Ordered and unordered forms agree exactly, at every point,
   so no bound is needed.
2. **THE MECHANISM, NAMED: `I` = 17 IS NOT A SCHEDULING CONSTANT. IT IS THE
   NUMBER OF `DimInfer` TERM SITES IN `seeds/shape_decode_loop.json`** — and
   `distinct` = 10 is the number of DISTINCT `field` selectors among those 17
   sites. The per-field site census and the per-tuple call-count trace are the
   **same multiset**, `[3,2,2,2,2,2,1,1,1,1]`, reconciled exactly.
3. **EVERY DETERMINANT OF THE DECODE IS CONSTANT ACROSS ALL SEVENTEEN
   INVOCATIONS.** The codebook, the generators, the goal and `max_dims` do not
   move; only `field` does — and `field` is applied by
   `shape_decode.rs::finish` to an **already-computed result**, so it cannot
   affect one unit of the decode's work. **The seventeen invocations are ONE
   decode, computed seventeen times, read off ten different ways.**

**So the redundancy is not 41.2% — it is 16 of 17, 94.1%.** And the
pre-registered statistic UNDER-STATED it, which is the direction that makes it
safe to report: `field` is a genuine determinant of the RETURN VALUE, so
including it was correct and conservative, and it was fixed in §2.1 before any
of this was visible.

---

## 2. STEP 0 — G5 ON MY OWN AXES, BEFORE ANY HEADLINE

**The inherited axes cannot validate this counter, and that is a fact about the
axes, not a shortcut.** On N and K the honest answer for both `I` and `distinct`
is a **constant**, so a counter that always returned `calls` and a counter that
always returned `1` would read **identically** to a correct one there. Two
predecessors found their own counters inert on a new axis; the cost rung ran G5
on three axes and reported a checked pass. **A distinctness statistic needs a
distinctness axis, and none existed.**

**The two failure modes, and why each is dangerous here:**

| failure | what it reads | which hypothesis it FAKES |
|---|---|---|
| encoding carries something incidental (an address, a call counter, load order) | `distinct == calls` always | **IRREDUCIBLE** |
| encoding collapses a real determinant | `distinct == 1` always | **RE-DERIVATION** |

### 2.1 WHAT I HAD TO ADD — the DISTINCTNESS axis, ground truth by construction

| control | construction | ground truth (declared in prereg §3) | **measured** |
|---|---|---|---|
| **D-RED** | 7 evaluations, SAME decode, UNCHANGED graph | calls 7, distinct **1** | **7 / 1 / 1** ✓ |
| **D-GREEN** | 7 evaluations, DIFFERENT goals | calls 7, distinct **7** | **7 / 7 / 7** ✓ |
| **D-CODEBOOK** | 7 evaluations, SAME goal, codebook GROWN between each | calls 7, distinct **7** | **7 / 7 / 7** ✓ |
| **D-SWEEP** | `J` distinct-goal decodes, `J` ∈ 1..7 | series 1..7, G5 **RESPONSIVE** | **[1,2,3,4,5,6,7]**, **RESPONSIVE** ✓ |

**D-CODEBOOK is the control that licenses the reading, and it deserves its own
sentence.** The irreducibility hypothesis's entire content is *"a decode mints
graph state, so the next invocation sees something different."* An encoder that
covered only the goal would have passed D-RED and D-GREEN and been
**structurally blind to exactly that mechanism** — it would have read
`distinct = 1` and this rung would have reported sweeping re-derivation,
confidently and wrongly. It is the positive control for the hypothesis the rung
was trying to refute, which is the only kind worth building.

**Every control passes at BOTH levels** — `shape_decode.rs::dim_infer_tests`
(Rust) and `tests/test_dim_infer_args_migrated.py` (the shipped engine).

### 2.2 G5 ON ALL FOUR AXES

| axis | counter | verdict | series |
|---|---|---|---|
| **N** (K=1 exact, 11.8×) | `dim_infer_arg_distinct_ordered` | **BLIND** | 10 at all 7 points |
| **N** | `dim_infer_arg_calls` / `term_eval:DimInfer` | **BLIND** | 17 at all 7 points |
| **N** | `term_unit:DimInfer` | RESPONSIVE | 10,608 → 125,528 |
| **K** (N=58 exact, 16×) | `dim_infer_arg_distinct_ordered` | **BLIND** | 10 at all 7 points |
| **K** | `term_eval:DimInfer` | **BLIND** | 17 at all 7 points |
| **K** | `term_unit:DimInfer` | RESPONSIVE | 51,272 → 820,352 |
| **P** (path) | `dim_infer_arg_distinct_ordered` | **RESPONSIVE** | **10 → 2** |
| **P** | `term_eval:DimInfer` | **RESPONSIVE** | **17 → 2** |
| **D** (distinctness) | `dim_infer_arg_distinct_ordered` | **RESPONSIVE** | **1,2,3,4,5,6,7** |
| all | `term_units_unattributed` | INERT | identically 0 — the diagnostic that **should** stay 0 |

**The BLIND readings on N and K are a measurement, not a defect** — and §2.1's
controls are what entitle me to say so. Without them, "BLIND because the
quantity is constant" and "BLIND because the instrument is broken" are the same
reading.

### 2.3 THE CONSERVATION IDENTITY — the site is where I claim it is

`dim_infer_arg_calls == term_eval:DimInfer` at **all 37 measured points**
(prereg §3.1, gated). The recording site is on the path the invocation counter
counts, so the comparison to `I` is meaningful rather than assumed.

### 2.4 THE CROSS-RUNG CONTROL — reproduced on a different seed block

This rung's harness is independently written on seeds **88000** where the
identity-cost rung used **78000**. It reproduces that rung's published counters
**exactly**:

| quantity | committed by the identity-cost rung | measured here |
|---|---|---|
| `term_unit:DimInfer` @ N=142, K=1 exact | 125,528 | **125,528** |
| `term_unit:DimInfer` @ N=58, K=16 exact | 820,352 | **820,352** |
| `term_eval:DimInfer` (`I`) | 17 | **17** |
| `I` on the novel path | 2 | **2** |

---

## 3. THE MEASUREMENT

### 3.1 THE READ — N=142, K=1, path `exact`

| quantity | value |
|---|---|
| `I` = `term_eval:DimInfer` | **17** |
| `dim_infer_arg_calls` | **17** |
| **`distinct_ordered`** | **10** |
| **`distinct_unordered`** | **10** |
| liveness | `recognized_transformed` — not a floor score from a dead arm |
| **verdict, by the pre-registered rule** | **REDUCIBLE** |

Ordered and unordered agree at every point, so **codebook load order contributes
nothing** and the §2.3-registered bound case does not arise.

### 3.2 THE NOVEL PATH HAS NO REDUNDANCY AT ALL

| path | `I` | `distinct` | redundancy |
|---|---|---|---|
| `exact` (recognised) | 17 | 10 | 7 repeats |
| `novel` (nothing explained) | **2** | **2** | **none** |

**The redundancy is a property of RECOGNITION specifically** — which is exactly
the wrong way round for compute-∝-surprise, and is why that property is capped.

### 3.3 INVARIANCE, RE-MEASURED HERE

`(I, distinct)` = **(17, 10)** at every one of the 7 N points and every one of
the 7 K points. `distinct` is as insensitive to problem size as `I` is — the
first hint, before the diagnostic, that neither is a quantity about the problem.

---

## 4. THE MECHANISM — named, and NOT fixed

*The headline was committed at `37510dff` before any of this section's tooling
existed, so nothing below can have shaped the number it explains.*

### 4.1 WHICH INVOCATIONS REPEAT

The call-order trace of distinct-tuple indices at N=142, K=1, `exact`:

```
[0, 1, 2, 2, 3, 4, 5, 6, 7, 3, 8, 9, 6, 7, 3, 8, 4]
```

17 calls, 10 distinct tuples, **7 repeat events**. Per-tuple call counts:
`[3,2,2,2,2,2,1,1,1,1]`.

### 4.2 WHICH DETERMINANT MOVES — and it is the one that costs nothing

Diffing the 10 recorded encodings field by field:

| determinant | across the 10 distinct tuples | length |
|---|---|---|
| `parts` (the codebook) | **CONSTANT** | 13,841 bytes |
| `gens` (the generators) | **CONSTANT** | 343 bytes |
| `goal` (the residual) | **CONSTANT** | 7,907 bytes |
| `max_dims` | **CONSTANT** | — |
| **`field`** | **VARIES — 10 values** | 8–10 bytes |

**`field` is a pure post-hoc projection.** `shape_decode.rs::finish` is
`finish(result, field, …)` — it selects a key from an **already-computed**
result `Dict`, and `eval_dim_infer` calls it on its **last line**. It cannot
affect the decode loop, and the counted work confirms it: `term_unit:DimInfer`
= 125,528 = **17 × 13 × 142 × 4**, i.e. **all seventeen invocations each perform
the FULL interior decode.**

### 4.3 WHERE THE 17 COMES FROM — an AST walk over the seed's own structure

Counting every `{"type": "DimInfer", …}` node in
`seeds/shape_decode_loop.json` by its `field` (an AST walk over the JSON, never
a substring selector):

| `field` | sites |
|---|---|
| `k` | 3 |
| `base`, `latent_name`, `generator`, `generators`, `ks` | 2 each |
| *(none — whole dict)*, `explained`, `dims`, `transforms` | 1 each |
| **total** | **17 sites, 10 distinct fields** |

**`[3,2,2,2,2,2,1,1,1,1]` — the same multiset as the trace's per-tuple call
counts, reconciled exactly** (gated in
`test_I_is_the_seed_s_own_DimInfer_SITE_COUNT`).

> **`I` = 17 IS A COUNT OF TERM SITES IN A JSON FILE.** Its invariance across
> 11.8× of N and 16× of K — which the identity-cost rung measured and called a
> "scheduling constant" — is invariance because it is a **static property of how
> the seed's rules were AUTHORED**. Its value of 2 on the novel path is the
> number of those sites reachable when nothing is explained.

### 4.4 THE MECHANISM, IN ONE LINE

> **The seed decodes ONCE PER RULE-TERM SITE instead of once per observation.**
> Seventeen sites each re-run the entire `O(K × ΣP × N × (1+s))` decode in order
> to read **one field** off a result that ten of them have already computed.

### 4.5 WHAT IT WOULD BE WORTH — stated as an arithmetic consequence, NOT a result

A per-fixpoint memoisation keyed on the four constant determinants, with
`field` applied to the cached `result`, would take the recognising path from 17
decodes to **1**:

| | now | with one decode |
|---|---|---|
| `term_unit:DimInfer`, N=142 K=1 exact | 125,528 | **7,384** (17×) |
| recognised attempt-units | 17 × 13 = 221 | **13** |
| novel attempt-units | 2 × 147 = 294 | **147** |
| **compute-∝-surprise ratio** | **1.33** | **11.3** |

**This is arithmetic on measured counters, not a measured speedup, and it is
NOT claimed as one.** The exactness argument is available — `finish` is a pure
projection of `result`, and §4.2 measures the other four determinants constant —
but availability is not the same as having been proved and gated, and the
identity-cost rung's own reasoning applies unchanged one level down: **building
an instrument, reading a redundancy fraction off it, and shipping the
optimisation that fraction justifies, all in one rung, is how an optimisation
gets to write its own success criterion.** Handed on with the exactness argument
pre-specified (prereg §5).

---

## 5. GATES

| gate | result |
|---|---|
| provenance (run FIRST, own step, both engines) | **PASS** — 7/7 each |
| endpoint guard | **PASS** — both endpoints pinned, never `HEAD` |
| **oracle bench** `scripts/rung7_vision_bench.sh` (no `data/`) | **212 passed / 10 skipped, exit 0** |
| sd-layer suites (dimension-inference / transform / sdloop-vision / ink / codebook-axis / term-eval / identity-cost / scale-split) | **125 passed** |
| **new gate** `tests/test_dim_infer_args_migrated.py` | **11/11** |
| **Rust suite** `cargo test --lib -- --test-threads=1` | **620 passed / 0 failed / 4 ignored** |
| G5 on all four axes | as tabulated in §2.2; `term_units_unattributed` INERT throughout |
| §9 default preservation | the audit is OFF by default; the site is one relaxed atomic load when off, gated by `test_the_site_is_silent_while_the_audit_is_off` at both levels |
| no behaviour changed | **no seed and no rule edited**; the only `.rs` changes are the gated recording site, its encoder, and two diagnostic accessors |

### 5.1 A PREDECESSOR'S RECORDED LIMITATION IS ESCAPABLE — `cargo test` RUNS

`VISION_SCALE_SPLIT_RESULTS.md` §1.2, `VISION_TERM_EVAL_COUNTER_RESULTS.md`
§7.2 and `VISION_INK_VENTRAL_RESULTS.md` each record that pyo3's
`extension-module` is set unconditionally so **`cargo test` cannot link this
crate**, leaving the `#[cfg(test)]` tests in `g5.rs` and `scale_audit.rs` as
"executable documentation". That is accurate about the default invocation and I
hit it identically. **It is escapable on a box whose Python is a shared
library** (`Py_ENABLE_SHARED=1`), by linking the test binary against it:

```
RUSTFLAGS="-C link-arg=-L/usr/lib -C link-arg=-lpython3.14" \
    cargo test --lib -- --test-threads=1
```

**620 passed, 0 failed, 4 ignored** — the whole Rust suite, including the g5 and
scale_audit tests three rungs recorded as unrunnable. **Environment-only: no
`Cargo.toml`, `.cargo/config.toml` or source change**, so the shipped engine is
built exactly as before (`scripts/engine_build.sh`, no `RUSTFLAGS`) and the
provenance gate passes unchanged. Offered as a **reproducible recipe, not a
protocol amendment** (§11 — I did not edit `VISION_PROTOCOL.md`).

**`--test-threads=1` is REQUIRED and that is a finding of its own:** the scale
audit is process-global, `cargo test` is parallel by default, and my first run
failed with `calls` = 15 where the ground truth was 7 and the audit-OFF test
reading 10 — two tests reading each other's counters. It is PROTOCOL §11's
shared-mutable-state hazard **inside one process**. The tests now take an
explicit lock so they are correct under either invocation.

---

## 6. PREDICTIONS — 5 right, 1 WRONG, and the wrong one is the interesting one

| | prediction | outcome |
|---|---|---|
| **P1** | D-RED 1, D-GREEN 7, D-CODEBOOK 7, all exactly | **RIGHT** — all three exact, at both levels |
| **P2** | G5 on D-SWEEP RESPONSIVE | **RIGHT** — [1..7] |
| **P3** | G5 on N and K BLIND | **RIGHT** — 10 at all 14 points, and §2.1's controls are what make "BLIND because constant" a claim rather than a hope |
| **P4** | G5 on PATH RESPONSIVE | **RIGHT** — 10 → 2 |
| **P5** | **`distinct < I`, specifically `distinct ≤ 3`** | **WRONG on the number, right on the direction.** `distinct` = **10**. My reasoning — "the recognising path does not grow the codebook, so every invocation carries the same tuple" — was **correct about the codebook and wrong about the tuple**: `parts`, `gens`, `goal` and `max_dims` ARE all constant, exactly as I argued, and I simply failed to notice that the `field` selector I had myself put in the tuple would separate them. **Had I predicted 1 and measured 1, I would have concluded "one decode, sixteen re-derivations" and been RIGHT BY ACCIDENT, with no idea that the 17 was a seed-authoring fact.** Being wrong is what sent me to the trace, and the trace is where the real answer was |
| **P6** | `calls == term_eval:DimInfer` everywhere | **RIGHT** — 37/37 points |

---

## 7. HONEST RESIDUALS — named, not fixed

1. **The optimisation is NOT built and NOT measured.** §4.5 is arithmetic on
   counters. The 17× and the 1.33 → 11.3 are consequences of measured integers,
   not a measured speedup, and are not claimed as one.
2. **The exactness argument is AVAILABLE, not PROVED.** `finish` is a pure
   projection and the other four determinants are measured constant on this
   workload — but "constant on this workload" is not "constant in general". A
   memoisation would owe a proof that no reachable graph state makes two sites'
   decode determinants differ within one fixpoint, and that proof is a rung of
   its own.
3. **`ΣP` = 13 was NOT reopened**, per prereg §0, and the reason stands: a prune
   there needs the different argument the codebook rung named. **It is now the
   next place to look only AFTER the site redundancy is removed** — with 17
   decodes collapsed to 1, `ΣP` becomes the largest remaining factor.
4. **One workload family.** Synthetic LCG cells, target as `held[0]`, K ≤ 16,
   one decoy family. The site count is a static seed fact and cannot vary with
   the workload, but WHICH sites are reachable per fixpoint can — the novel
   path's 2 already demonstrates that, and other graph states may reach other
   subsets.
5. **The rung does not explain WHY the seed was authored with 17 sites.**
   Re-reading one decode's result ten ways is the natural thing to write when
   the Term is the only way to reach the value; whether the rule language offers
   a way to bind the result once and project from it is a question about the
   DSL, not about `DimInfer`, and it is not investigated here.
6. **`distinct` counts tuples, not cost.** Two invocations with different
   `field` are "distinct" by the registered statistic and identical in work.
   That is precisely why §4 exists and why the registered number under-states
   the redundancy — recorded as the statistic's own bound, not as a defect.

---

## 8. PROPOSED BURNED-SEED LEDGER ROW — for the supervisor to apply

**This rung did NOT edit `VISION_PROTOCOL.md`** (§11, and the brief said so
explicitly). The row below is the one this rung's result earns, written out here
so it is not lost; applying it is the supervisor's call, as a separate commit in
the predecessors' pattern (cf. `097ced4c`).

```
| **88000–88999 CONSUMED (17 draws MEASURED: 88000, 88100–88115; zero outside block)** | **`I` = 17 IS NOT A SCHEDULING CONSTANT — IT IS A COUNT OF `DimInfer` TERM SITES IN A JSON FILE, AND THE SEVENTEEN INVOCATIONS ARE ONE DECODE COMPUTED SEVENTEEN TIMES.** Prereg `VISION_DIM_INFER_ARGS_PREREG.md` @ **`a04758ee`** (before the instrument existed); headline pinned @ **`37510dff`** (before the diagnostic that explains it existed); results `VISION_DIM_INFER_ARGS_RESULTS.md`; runners `scripts/dim_infer_args{,_diagnose}.py`; gate `tests/test_dim_infer_args_migrated.py` **11/11**. Base `e8bf3987`. Engines **`58008033c66d`** (headline) and **`87a8ab4f650b`** (final, adds two diagnostic accessors) — **headline identical on both**. Answers the discriminating test `VISION_IDENTITY_COST_ANATOMY_RESULTS.md` §5.4 specified and deliberately refused to run in the same rung as building the instrument. **PRE-REGISTERED ANSWER: `distinct` = 10 against `I` = 17** (ordered AND unordered agreeing at every point) — **neither pre-committed extreme**, and REDUCIBLE by the prereg's own decision rule. **THE MECHANISM: every determinant of the DECODE — codebook, generators, goal, `max_dims` — is CONSTANT across all seventeen invocations; the only thing that moves is `field`, which `finish` applies to an ALREADY-COMPUTED result on `eval_dim_infer`'s last line and which therefore cannot affect one unit of work.** `term_unit:DimInfer` = 125,528 = **17 × 13 × 142 × 4** confirms all seventeen each perform the FULL interior decode. **AN AST WALK OVER `seeds/shape_decode_loop.json` FINDS EXACTLY 17 `DimInfer` TERM SITES WITH 10 DISTINCT `field` SELECTORS, per-field multiset `[3,2,2,2,2,2,1,1,1,1]` — THE SAME MULTISET AS THE TRACE'S PER-TUPLE CALL COUNTS.** So `I`'s invariance across 11.8× of N and 16× of K is invariance because it is a **static property of how the seed's rules were AUTHORED**, and its value of 2 on the novel path is the number of sites reachable when nothing is explained. **THE SEED DECODES ONCE PER RULE-TERM SITE INSTEAD OF ONCE PER OBSERVATION. Redundancy is therefore 16 of 17, not the registered 7 of 17 — and the registered statistic UNDER-STATED it, the safe direction: `field` is a real determinant of the RETURN VALUE, so including it was correct and conservative, and it was fixed BEFORE any of this was visible.** **STEP 0 NEEDED A NEW AXIS AND THAT IS THE REUSABLE LESSON: a DISTINCTNESS statistic has two OPPOSITE failure modes — an encoding carrying something incidental reads `distinct == calls` and FAKES IRREDUCIBLE; one collapsing a real determinant reads `distinct == 1` and FAKES RE-DERIVATION — and NEITHER is caught by G5 on the inherited N/K/PATH axes, because on N and K the honest answer is a CONSTANT and a broken counter reads identically to a correct one there.** Added D-RED (7 calls/1 distinct), D-GREEN (7/7), **D-CODEBOOK (7/7 — the control that LICENSES the reading: it is the positive control for the very mechanism the irreducibility hypothesis names, and an encoder covering only the goal would have passed D-RED and D-GREEN while being structurally blind to it)** and D-SWEEP (1..7, RESPONSIVE), all exact at BOTH the Rust and shipped-engine level. Conservation `dim_infer_arg_calls == term_eval:DimInfer` at **37/37** points; cross-rung control reproduces the identity-cost rung's 125,528 / 820,352 / 17 / 2 EXACTLY on a different seed block. **NOT FIXED, same reasoning the predecessor applied to itself** — §4.5's 17× (and compute-∂-surprise 1.33 → 11.3) is **arithmetic on measured counters, NOT a measured speedup**, and the exactness argument is **AVAILABLE, not PROVED**. **WHAT IT GOT WRONG: P5 predicted `distinct ≤ 3` and measured 10 — and the wrongness is LOAD-BEARING: the reasoning ('the recognising path does not grow the codebook') was CORRECT about the codebook and simply failed to notice that the `field` selector it had itself put in the tuple would separate them. Had it predicted 1 and measured 1 it would have been RIGHT BY ACCIDENT and never learned the 17 was a seed-authoring fact; being wrong is what sent it to the trace.** **ALSO: `cargo test` DOES link this crate** — `RUSTFLAGS="-C link-arg=-L/usr/lib -C link-arg=-lpython3.14" cargo test --lib -- --test-threads=1` gives **620 passed / 0 failed**, including the `g5.rs` and `scale_audit.rs` tests **three predecessor rungs recorded as unrunnable in this tree**; environment-only, no `Cargo.toml`/`.cargo`/source change, engine still built by `scripts/engine_build.sh`. Offered as a recipe, **NOT a protocol amendment** (§11 — this file was not edited by that rung, only this row appended). **`--test-threads=1` is REQUIRED and is itself a finding: the scale audit is process-global, so two parallel tests read each other's counters (first run: `calls` 15 where ground truth was 7) — §11's shared-mutable-state hazard INSIDE ONE PROCESS.** `ΣP` = 13 NOT reopened (prereg §0) but is now the largest remaining factor once the site redundancy goes. No Rust behaviour change (the recording site is one relaxed atomic load when the audit is off, gated at both levels), **no seed and no rule edited**; provenance gate its OWN step (7/7, both engines); oracle **212 passed / 10 skipped**; sd-layer suites **125 passed**. |
```
