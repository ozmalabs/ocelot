# THE CODEBOOK AXIS (K) — RESULTS

*Pre-registration `VISION_CODEBOOK_AXIS_PREREG.md`, committed at **`e22db8dd`**
BEFORE any measurement or implementation. Phase 1 committed at **`e4852dbc`**
BEFORE the fix existed. Runners `scripts/codebook_axis_measure.py`,
`scripts/codebook_axis_identity.py`. Gate `tests/test_codebook_axis_migrated.py`
**15/15**. Raw rows `results/codebook_axis.json` (before),
`results/codebook_axis_AFTER.json` (after),
`results/codebook_axis_identity_OLD.json` / `_NEW.json` (the byte-identity
capture, both engines). Seeds **68000–68999**.*

---

## 0. PROVENANCE — which binaries produced these numbers

| | |
|---|---|
| branch | `gamma-substrate/codebook-axis` |
| base | `152ea76a` |
| prereg commit | **`e22db8dd`** (before any measurement) |
| Phase 1 commit | **`e4852dbc`** (before any implementation) |
| **engine, Phase 1 / pre-fix** | **`02ad951e4e45`** — own build, `scripts/engine_build.sh` |
| **engine, Phase 2 / post-fix** | **`863706852555`** — own build, `scripts/engine_build.sh` |
| provenance gate | `tests/test_engine_provenance_migrated.py` **7 passed**, run as its OWN step before any number, on BOTH engines |
| endpoint guard | `tests/test_provenance_endpoint_guard_migrated.py` **passed** |
| oracle bench | **222 passed, exit 0**, `data/` symlinked — §6 |

**Both engines are this worktree's own builds via `scripts/engine_build.sh`.**
The pre-fix capture was produced by checking `shape_decode.rs` back to
`e4852dbc`, rebuilding, and re-running the identical harness — so the
byte-identity diff is against a **real binary**, not against expectations
written afterwards.

---

## 1. THE HEADLINE

**Three results.**

1. **K is measured for the first time, and it is THREE different numbers — the
   brief's premise is right in form and wrong in magnitude.** On every shipped
   seed, the codebook size that reaches the expensive loop is **ZERO**. The
   largest codebook in the tree (the 263-entry stroke corpus) contributes **no
   `DimInfer` interior work at all.** On the arc's real vision workload the
   operative K is **1–4**, not hundreds.
2. **The loop IS exhaustive, exactly and provably: measured/predicted = 1.0000
   at all 7 N points AND all 7 K points**, against a model declared in the
   pre-registration before measuring.
3. **The fix is exact and lands: 91.16% of `DimInfer`'s interior work removed on
   the recognising path, 0 verdict changes across 2,140 captured values,
   `checked` included — and the property check found the OLD code had
   compute-∝-surprise INVERTED, which the fix corrects rather than merely
   preserves.**

---

## 2. STEP 0 — MY OWN INSTRUMENT, CHECKED ON THIS RUNG'S AXES FIRST

The predecessor validated `term_unit` with G5 on an **N sweep at K=1 only**, and
recorded `ShapeDecode`'s own unit sites as **INERT**. A counter validated on one
axis is not validated on another — that is the exact error G5 exists to catch,
and it has already caught one instrument in this arc (the predecessor's own).

**So G5 ran on both axes before any headline.** The verdict is handed off to
`runners/dsl/src/g5.rs`; it is not reimplemented in Python.

| sweep | counter | verdict | series |
|---|---|---|---|
| **SWEEP-N** (K=1) | `term_unit:DimInfer` | **RESPONSIVE** | 119,952 → 1,419,432 |
| **SWEEP-N** | `term_unit:TransformDecode` | **RESPONSIVE** | 96 → 1,136 |
| **SWEEP-K** (N=58) | `term_unit:DimInfer` | **RESPONSIVE** | 579,768 → 9,276,288 over 16× |
| **SWEEP-K** | `term_unit:TransformDecode` | **RESPONSIVE** | 464 → 7,424 |
| both | `term_units_unattributed` | INERT | identically 0 — the diagnostic that **should** stay 0 |

**P1 RIGHT: no charging sites had to be added.** `build_candidate` already sits
inside the part loop, so K flowed through it. This is reported as a *checked
pass*, not as an assumption — had it come back INERT, §1 of the prereg committed
me to fixing the instrument and saying so, and I would have.

**The instrument remains RESPONSIVE on both axes after the fix** (§5.3), so the
post-fix numbers are readable by the same standard as the pre-fix ones.

---

## 3. PHASE 1 — THE MEASUREMENTS

### 3.1 THE LOOP IS EXHAUSTIVE, AND THE MODEL IS EXACT RATHER THAN FITTED

Declared in prereg §2 **before** measuring:

> `term_unit:DimInfer = I × K_eligible × A × N × (1 + s)`,
> `A = ΣP + ((ΣP)² − ΣP²) = 13 + 134 = 147`

`A` **falls out** of the shipped generator seed's own `params` `[3,2,2,3,3]`
(PROTOCOL §13) — no constant was chosen. `I` is **read** from
`term_eval:DimInfer`, never assumed, so the ratio tests loop *structure* and not
invocation count.

| axis | points | measured/predicted |
|---|---|---|
| **N** (12 → 142, K=1) | 7 | **1.0000 at every point** |
| **K** (1 → 16, N=58) | 7 | **1.0000 at every point** |

**Every observation is compared against every codebook entry × every generator ×
every k, with no early exit anywhere. Nothing prunes. P2 RIGHT, P3 RIGHT.**

The model also reproduces the predecessor's committed figure exactly
(`17 × 1 × 147 × 142 × 4 = 1,419,432`), which is why it was declared in advance
rather than proposed here.

### 3.2 K — THREE DIFFERENT NUMBERS, AND REPORTING ONLY THE FIRST TWO WOULD HAVE BEEN THE WHOLE ERROR

The static census forced a distinction the brief did not contain.
**`dim_types` alone does not reach the generator loops**: `dims_are_coord`
(`shape_decode.rs:535`) requires the **`coord:` prefix** at the generator's
`coord_dims` slots.

| seed | K_total | K_eligible | **K_attempting** |
|---|---|---|---|
| `stroke_shapes.json` | **263** | **263** | **0** |
| `character_shapes.json` | 54 | 0 | 0 |
| `reading_constructions.json` | 22 | 0 | 0 |
| `math_capability_shapes.json` | 17 | 0 | 0 |
| `code_*`, `inference_knowledge`, +3 | 41 | 0 | 0 |
| **LIVE `boot_core`** | **0** | 0 | 0 |

> **`K_attempting` is ZERO on every shipped seed.** The largest codebook in the
> tree is loaded, walked, and contributes **zero** `DimInfer` interior work,
> because its `dim_types` are `['pred','idx','val','val','val']`.

**No shipped seed produces coord-typed signatures at all** — they are minted at
runtime by the vision world adapters (`agnosia_world`, `crossframe_world`,
`sdloop_vision`, `invariant_comparator_world`). So the only place a real K on
this axis exists is a live vision run:

| `sdloop_vision`, n_thetas | 2 | 3 | 4 | 6 | 12 |
|---|---|---|---|---|---|
| K_total (live) | 18 | 19 | 19 | 19 | 21 |
| **K_attempting (minted quanta)** | **1** | **2** | **2** | **2** | **4** |

**That column is the sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` exactly**, so the
census is measuring the live loop and not a boot artefact.

**P5 SCORED HONESTLY — HALF RIGHT, AND WRONG WHERE IT MATTERED.** I predicted
`K_eligible ≪ K_total` because `dim_types` is optional. Measured: the seed that
dominates the corpus carries `dim_types` on **all 263** entries, so
`K_eligible/K_total` is **69%, not small**. What is actually small is
**`K_attempting`** — a category my prediction did not contain. I got the right
conclusion for the wrong reason, and the right reason is a distinction I did not
anticipate.

**The correction to the brief:** "the binding quantity is N×K" is right in form,
but K on the axis that binds is **1–4 today**, not hundreds. The "real time
affords ~10×10 at K=1, divided by K thereafter" projection is therefore far less
severe than stated — while remaining a real growth axis, since K_attempting is
precisely the count of things the agent has *learned*.

### 3.3 WHERE THE WORK GOES INSIDE `DimInfer` — the profile, not the total

| arm | count per eligible part | share |
|---|---|---|
| length 1 (single generator × k) | `ΣP` = **13** | 8.84% |
| **length 2 (ordered distinct pairs)** | `(ΣP)² − ΣP²` = **134** | **91.16%** |
| **A** | **147** | |

**P4's predicted 91.2% split is confirmed.** The cost is not in K and not in N
individually — it is in the **composition arm**, which is a function of the
**generator** codebook and is paid in full on every observation regardless of
whether a single generator already explains it.

---

## 4. THE DECISION, ON THE RECORD

Against the rule fixed in prereg §4 **before** any of §3 was measured:

| clause | required | measured | |
|---|---|---|---|
| **G-a** | exhaustive, ratio ≥ 0.99 | **1.0000** at 14/14 points | ✅ |
| **G-b** | ≥50% provably skippable | **91.16%**, with the comparator's own definition as the proof | ✅ |
| **S-c** | STOP if K_attempting ~1 **AND** non-K terms small | K_attempting **is** 1–4 — but `A` = 147 is **not** small | ✗ (conjunction fails) |

**GO — and the stop rule earned its keep by NOT firing for the wrong reason.**
S-c's first conjunct is *satisfied*: the brief's K premise really is overstated.
Had the rule been written as "stop if K is small" I would have stopped here and
missed a 91% saving that has nothing to do with K. The second conjunct is what
caught it: **the work is on the generator-composition axis, not the K axis the
brief pointed at, and it is there at K=1.**

---

## 5. PHASE 2 — THE FIX

### 5.1 WHAT CHANGED, AND WHY SKIPPING IS EXACT

`eval_dim_infer`'s two arms became **two passes over `parts`** instead of one
interleaved pass, with one short-circuit between them:

```rust
for part in &parts { /* LENGTH 1, unchanged in attempts and order */ }
let explained_at_length_1 = !successes.is_empty();
for part in &parts { /* LENGTH 2: `checked += 1;` then `if explained… continue;` */ }
```

**The proof is the comparator's own definition, in one line, and it was already
written in this function's committed comment** ("Occam (length strict-primary,
below) guarantees a length-2 attempt NEVER beats a length-1 one"):

> `key = (steps.len(), residual_dims, base_name, ks)` is compared as a **tuple**,
> so `steps.len()` is **strict primary**. Every length-1 attempt has
> `steps.len() == 1`; every length-2 has `2`. Therefore
> `key(any length-1 success) < key(any length-2 success)` **unconditionally** —
> no tie is possible at the primary component, so no later component is ever
> consulted between the arms.

**The quantifier is GLOBAL, not per-part — which is exactly why the passes had to
be split.** A length-1 success on the *last* part still forbids every length-2
winner on the *first*. An interleaved loop cannot see that and would have had to
keep going. **Every skipped candidate is provably unable to win.** This changes
*which work happens*, never *which answer is produced* — the batch-apply shape.

### 5.2 THE PREREG'S DECLARED HAZARD WAS REAL, AND IT WAS AVOIDABLE

Prereg §4.1 named one hazard **before the fix existed**: `checked` is a
**returned field** of the result dict, so a naive skip shrinks it, and
byte-identity on it "will FAIL by construction."

**It did not have to.** `checked`'s value depends only on the **outer**
`apply_generator_k` (`ΣP` = 13 calls per part), not on the inner work. So the
skip is placed **after `checked += 1`** and after that outer call. The expensive
part — the inner `apply_generator_k` + `build_candidate`, the entire
`O(N × slots)` cost — is what gets skipped.

**`checked` is byte-identical, and units still fall by the full 91.16%.** I am
recording this as a prediction that was *pessimistic and avoidable* rather than
quietly dropping it: the hazard was correctly identified, and the right response
was to engineer around it, not to wave it through as expected noise. `checked`
was **not** redefined (§5). A structural gate asserts the ordering so a future
edit cannot silently reintroduce the shrink.

### 5.3 BYTE-IDENTITY — 2,140 VALUES, TWO REAL BINARIES, BOTH BRANCHES

80 cases across `{exact, rot1, rot2, novel} × N ∈ {12,20,37,58} × K ∈
{1,2,3,5,8}`, dumping **every** field of every `DimInfer` verdict plus the
derived graph state. **Both branches are exercised deliberately** — a
byte-identity pass on a grid where the short-circuit never fires would prove
nothing about the skip.

| | |
|---|---|
| engines compared | `02ad951e4e45` (pre-fix) → `863706852555` (post-fix) |
| cases | **80** — 60 explained at length 1, 20 explained by nothing |
| values diffed | **2,140** |
| **verdict record diffs** | **0** |
| **`checked` diffs** | **0** |

### 5.4 THE SAVING — COUNTED, AND IT IS EXACTLY THE PREDICTED CONSTANT

`term_unit:DimInfer`, post-fix / pre-fix:

| path | pre-fix | post-fix | ratio |
|---|---|---|---|
| `exact` (identity) | 24,120,348 | 2,133,092 | **0.0884** |
| `rot1` | 24,120,348 | 2,133,092 | **0.0884** |
| `rot2` | 24,120,348 | 2,133,092 | **0.0884** |
| **`novel` (nothing explained)** | 2,837,688 | 2,837,688 | **1.0000** |

**0.0884 is `13/147` = the length-1 share of attempts, to four places** — the
saving is exactly the arm that was removed, at **all 14 sweep points on both
axes** (`results/codebook_axis_AFTER.json`), not an average.

### 5.5 ⚠️ THE PROPERTY CHECK — AND IT FOUND SOMETHING THE BYTE-IDENTITY DIFF COULD NOT

Prereg §6 declared this check in advance because **batch-apply held verdict
byte-identity over 235,200 values and still destroyed compute-∝-surprise,
unnoticed for two rungs. Byte-identity is not property-identity.**

The unexplained path is **bit-for-bit unchanged** (ratio 1.0000) — the
short-circuit cannot fire where nothing was explained, by construction. So the
saving accrues to **recognised** observations only. Then:

| | unexplained : explained cost |
|---|---|
| **pre-fix** | 2,837,688 : 24,120,348 = **0.118 — INVERTED** |
| **post-fix** | 2,837,688 : 2,133,092 = **1.330 — correct direction** |

> **The OLD code had compute-∝-surprise BACKWARDS on this op: a RECOGNISED
> observation cost 8.5× MORE than a surprising one.** Every observation paid the
> full 147-attempt composition search, and a recognised one paid it across more
> fixpoint passes. **The fix does not merely preserve the property — it corrects
> a standing inversion of it**, and the inversion was invisible to every gate in
> this arc until the property check was run as a separate step from
> byte-identity.

This is the concrete vindication of separating the two checks. A rung that had
declared "byte-identity green, ship it" would have shipped the right answer, at
the right cost, and never learned that the cost had been pointing the wrong way.

### 5.6 WALL-CLOCK — reported, decides nothing

**CONTAMINABLE.** Load average was **higher** during the post-fix run (`load1`
**2.01**) than the pre-fix run (**1.22**), so this understates the change.

| point | pre-fix | post-fix | |
|---|---|---|---|
| SWEEP-N, N=142 | 97.7 ms | 13.4 ms | 7.32× |
| SWEEP-K, K=16 | 611.6 ms | 83.1 ms | 7.36× |

**7.3× wall against 11.3× counted** — the gap is the fixed rule-matching cost
outside `DimInfer`, which this fix does not touch. Counted operations decide;
this table is reported only because §12 asks for it with load state beside it.

---

## 6. GATES

| gate | result |
|---|---|
| provenance (run FIRST, both engines) | **PASS** — 7/7 |
| endpoint guard | **PASS** — both endpoints pinned, never `HEAD` |
| **oracle bench** `scripts/rung7_vision_bench.sh`, `data/` symlinked | **222 passed, exit 0** |
| **sd orbit law `{2:1,3:2,4:2,6:2,12:4}`** | **UNMOVED** — reproduced live in §3.2 and gated |
| sd-layer suites (dimension inference / transform / sdloop / ink) | **67 passed** |
| **new gate** `tests/test_codebook_axis_migrated.py` | **15/15** |
| G5 on both axes, before and after | **RESPONSIVE** throughout |
| byte-identity | **0 diffs / 2,140 values / 2 real binaries** |

---

## 7. PREDICTIONS — 4 right, 1 half, 1 right-for-the-wrong-reason

| | prediction | outcome |
|---|---|---|
| **P1** | instrument RESPONSIVE on SWEEP-K with no new sites | **RIGHT** — checked, not assumed |
| **P2** | model ratio 1.0000 at every point | **RIGHT** — 14/14 |
| **P3** | loop is exhaustive, no early exit | **RIGHT** |
| **P4** | length-2 is 91.2%; fix removes ~91% on the recognising path and 0% where nothing is explained | **RIGHT** — 0.0884 and 1.0000 measured exactly |
| **P5** | `K_eligible ≪ K_total` | **HALF / right-for-the-wrong-reason.** K_eligible is 69% of K_total, not small. The small quantity is **K_attempting**, a category the prediction did not contain (§3.2) |
| **P6** | wall-clock uninformative | **RIGHT** — reported with load state, decides nothing; and the post-fix run ran under *higher* load |
| *(prereg §4.1 hazard)* | `checked` byte-identity fails by construction | **AVOIDABLE, and avoided** (§5.2) — recorded rather than dropped |

---

## 8. HONEST RESIDUALS — named, not fixed

1. **The length-1 arm itself is still exhaustive.** `ΣP` = 13 attempts per part
   run in full even after a length-1 success. Skipping *those* is **NOT** exact:
   the Occam key's later components (`residual_dims`, `base_name`, `ks`) do
   discriminate within the arm, so a later attempt can beat an earlier one. **A
   prune there would need a different argument and is deliberately not
   attempted.**
2. **`K_attempting = 0` on every shipped seed means the stroke corpus never
   reaches rung 2.** Whether that is intended or is a latent capability gap
   (263 held shapes that can never be recognised under rotation) is **outside
   this rung's pre-registration** and is named for a successor, not answered.
3. **The composition arm is `O(G²)` in generators.** At G=5 it is 134 attempts;
   a sixth generator with 3 params takes it to 214. The short-circuit removes
   this on the recognising path but **the mint path still pays it in full** —
   correctly, since that is where the search is genuinely needed, but it is the
   growth axis a successor should watch.
4. **`I` (DimInfer invocations per fixpoint) was read, never explained.** It is
   17 on the synthetic sweep and 2 on the identity grid. Why it takes those
   values is fixpoint-scheduling behaviour this rung did not investigate.
