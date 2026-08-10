# TERM-EVAL COUNTER + THE G5 RESPONSIVENESS GATE — RESULTS

*Pre-registration `VISION_TERM_EVAL_COUNTER_PREREG.md`, committed at **`7c382089`**
BEFORE any implementation. Runner `scripts/g5_responsiveness_sweep.py`. Gate
`tests/test_term_eval_counter_migrated.py` **13/13**. Raw rows
`results/g5_responsiveness.json`. Seeds **67000–67999** (only 67000 consumed).*

---

## 0. PROVENANCE — which binary produced these numbers

| | |
|---|---|
| branch | `gamma-substrate/term-eval-counter` |
| base | `581a88e6` |
| prereg commit | **`7c382089`** (before any implementation) |
| **engine** | **`02ad951e4e45`** — this worktree's OWN build, via `scripts/engine_build.sh` |
| provenance gate | `tests/test_engine_provenance_migrated.py` **7 passed** |
| oracle bench | `scripts/rung7_vision_bench.sh` — see §7 |

**THIS RUNG ADDS RUST** (`term_variants.rs`, `g5.rs`, `scale_audit.rs`'s T
section, one choke point in `term.rs::evaluate`, two unit sites in
`shape_decode.rs`, two PyO3 readouts), so §10.1 rule 4 bites and provenance
reads **own**, not shared.

### 0.1 ⚠️ THE FIRST MEASUREMENT RAN ON THE WRONG ENGINE, AND IT ALMOST DID SO SILENTLY

The brief warned that a counter-only rung would measure the wrong engine **in
silence**. It happened, on the first run, and is recorded here rather than
quietly fixed:

I ran `cargo build --release` directly instead of `scripts/engine_build.sh`. The
build succeeded; the `.so` was **never installed** into
`runners/dsl/python/substrate_rs/`. The sweep then loaded engine `4d451d8f6ed0`
— the pre-rung binary — and the provenance line said so
(**`STALE — 7 .rs newer than the binary`**), which the script printed and I did
not stop on.

**It failed loudly only because this rung happens to add Python-visible methods**
(`scale_audit_g5_verdict`), which raised `AttributeError`. Had the rung added
counters only — which was the plan for most of its surface — the run would have
completed, every gate would have passed, and the entire per-variant profile would
have read as absent (`term_evals=None`, printed and unremarked) against an engine
that did not contain the instrument.

**Two lessons, both cheap:**
1. `scripts/engine_build.sh` is not a convenience wrapper. `cargo build` alone
   leaves the tree in exactly the state §10 exists to prevent.
2. **The provenance system WORKED** — it printed `STALE` — and a printed warning
   in a scrolling log is not a gate. The stale marker should refuse to proceed,
   not narrate. *Named, not built: this rung does not edit
   `domains/engine_provenance.py` (§11 rule 4, not my file).*

---

## 1. THE HEADLINE

**Two results, and the second is the larger one.**

1. **Term evaluation is now countable, per variant** — and the instrument's
   FIRST family is blind to the sd/identity layer exactly as pre-registered
   (P1). The family that sees it is the second one, `term_unit`, which moves
   **120,048 → 1,420,568** across the same 11.8× range of N over which every
   existing counter is byte-identical.
2. **The retroactive G5 sweep of all 27 existing counters is nearly clean on
   their own axes — 22 RESPONSIVE, 3 INERT, 2 BLIND — and the 2 BLIND are MY
   pre-registration error, not a counter defect.** But the cross-table carries
   the sharper fact: **on the sd/identity axis, 27 of 27 existing counters are
   BLIND or INERT. Not one of them can see that layer.** The A8 failure was not
   a fluke of one arm; it is the toolkit's structural boundary, now measured
   rather than argued.

**And G5 caught a dead instrument on its first firing — MINE.** See §4.

---

## 2. PART 1 — THE COUNTER

### 2.1 What was built

| piece | where |
|---|---|
| choke point | `term.rs::evaluate` — one site, all 175 variants, recursive |
| variant table | `term_variants.rs`, **GENERATED** by `tools/gen_term_variants.py` |
| counters | `scale_audit.rs` T section — `TERM_EVALS[175]`, `TERM_UNITS[175]` |
| attribution | innermost-variant RAII guard (early `return`s in `evaluate` make a manual restore silently wrong) |
| unit sites | `shape_decode.rs`: `covers_relation`, `shape_fit`, **`build_candidate`** (×2 loops) |
| readout | `snapshot()` — non-zero cells as `term_eval:<V>` / `term_unit:<V>`, totals always |
| gate | `g5.rs`, exposed through `py.rs`; the harness does not reimplement it |

**`NUM_TERM_VARIANTS = 175` FALLS OUT** (§13): it is the enum's own arity, read
by a generator, guarded by a table-integrity test. No constant was chosen.

### 2.2 THE PER-VARIANT PROFILE

The sd/identity workload (synthetic, N=142, K=1), one `run_rules` fixpoint:

| variant | `term_eval` (invocations) | `term_unit` (interior units) |
|---|---|---|
| Var | 91 | 0 |
| Attr | 89 | 0 |
| Lit | 78 | 0 |
| Eq | 60 | 0 |
| Not | 19 | 0 |
| And | 18 | 0 |
| Count | 18 | 0 |
| **DimInfer** | **17** | **1,419,432** |
| Gt | 10 | 0 |
| Filter | 5 | 0 |
| Lt | 5 | 0 |
| NodesOfType | 5 | 0 |
| **TransformDecode** | **2** | **1,136** |
| Neighbours | 2 | 0 |
| StringConcat | 2 | 0 |
| Gte / IfThenElse / Or | 1 each | 0 |
| **TOTAL** | **424** | **1,420,568** |

**This table is the argument for not pre-aggregating.** `DimInfer` is **17 of
424 invocations — 4.0%** — and **99.92% of the interior work.** A single total
would have said "the number went up." The profile says *where*, which is the
question the next rung must answer, and it says it in one column.

**The retina drive, for contrast** (g=32, 20 ticks): **7,382,375** Term
evaluations and **0** interior units — a workload made entirely of cheap
variants, where invocations *are* the cost. The two families are doing different
jobs on the two workloads, which is why both exist.

### 2.3 THE OVERHEAD, AND WHAT THE DEFAULT FOLLOWS (§13)

Wall-clock, ON vs OFF, alternated within one process, median of 5. **This is the
only wall-clock number in the rung and it is CONTAMINABLE** (this machine swings
1.66× on load alone, measured); it decides what is *reported*, never a verdict.

| workload | OFF | ON | overhead |
|---|---|---|---|
| retina drive, g=32 (7.4M Term evaluations) | 67.9 ms | 83.6 ms | **+23.08%** |
| sd decode, N=142 (424 evaluations, 1.4M units) | 108.5 ms | 107.8 ms | **−0.60%** |

**Which precedent does it resemble?** **Neither, and the honest answer is "both,
on different workloads."**

- The **winner-value instrument** measured **81.41%** and ships OFF.
- The **fallback trace** measured **0.000%** and was honestly reported as free
  *because it never fires*.

This instrument is **+23.08%** where `evaluate` traffic is heavy and **free**
(−0.60%, inside noise) where the work it was actually built to measure lives.
**The cost is proportional to the number of Term EVALUATIONS, which is not the
quantity it is measuring** — the interior units cost nothing because they are
charged once per loop rather than once per iteration. That is precisely
backwards from ideal, and it is the reason the default is not a judgement call.

**DEFAULT: OFF** (§9). Gated by `test_zero_when_off_on_a_LIVE_workload` —
every counter reads 0 with the audit off on a workload proven live by re-running
it with the audit on.

---

## 3. PART 2 — G5, AND ITS OWN CONTROLS

### 3.1 The criterion, restated with its measured control

**PASS iff `span(sweep) > span(control)`**, control = the same counter, same
repetition count, axis held FIXED at the sweep's first value.

**Every control span measured EXACTLY 0** (G3 determinism: byte-identical
across repeat runs, verified). So on this data the criterion reduces to *"did it
move at all"* — which is what `VISION_VIDEO_PROBE_RERUN_RESULTS.md` named as the
missing gate. The criterion is nevertheless written against the **measured**
control, not the assumed zero, so it stays correct if a counter ever becomes
non-deterministic. **No threshold was chosen. No constant entered.**

### 3.2 G5's POSITIVE CONTROLS — both directions, both declared in advance

| control | counter | axis | expected | got |
|---|---|---|---|---|
| **RED** | `epochs` | SWEEP-G | BLIND | **BLIND** ✅ |
| **GREEN** | `cand_enum` | SWEEP-G | RESPONSIVE | **RESPONSIVE** ✅ |

And, in the gate itself, **G5 is run against A8's actual numbers** — the seven
253s across 11.8× — and returns **BLIND**. *The gate is tested on the failure
that created it.*

Plus pure-function controls: movement equal to a non-zero noise floor ⇒ BLIND;
movement beyond it ⇒ RESPONSIVE; all-zero ⇒ INERT; empty ⇒ INERT. **A gate that
has never been able to fail has not been tested**, and this one fails on demand
in four distinct ways.

---

## 4. ⚠️ G5's FIRST FIRING CAUGHT A DEAD INSTRUMENT, AND IT WAS MINE

**This is reported in full because it is the rung validating itself against its
own subject matter.**

The first build charged interior units in `covers_relation` and `shape_fit`
only — the two sites named in prereg §2.3. Measured result on SWEEP-S:

```
term_units_total : 0, 0, 0, 0, 0, 0, 0     ⇒ G5 verdict INERT
```

**P2 falsified on the first attempt.** The instrument built specifically to see
the sd/identity layer was **dead on it** — the twelfth inert instrument in this
arc, caught within minutes by the gate the same rung had just built.

**The diagnosis is in the per-variant profile, which is what made it a
two-minute fix instead of a rung-ending failure.** The snapshot showed
`term_eval:TransformDecode = 2` and `term_eval:DimInfer = 17` and **no
`ShapeDecode` at all**. The sd workload never touches the composer path; it runs
the transform/dimension path, and both reduce to `build_candidate`'s aligned-pair
loops. **A single aggregated total would have said only "zero" and diagnosed
nothing.**

**Is this §5 metric surgery? No, and the distinction matters.** §5 forbids
rescuing a **failed gate** by changing the **measure**. Here the gate *worked* —
it went red on my instrument. The statistic's definition ("interior comparison
units per variant") is **unchanged**; its *implementation* was incomplete,
missing the sites where the swept workload actually spends its time. Fixing a
charging site is a bug fix. Redefining what counts as a unit to make the number
move would have been surgery, and was not done.

**Both measurements are committed**, so a successor can check the claim rather
than take it: `results/g5_responsiveness_PREFIX_inert.json` is the pre-fix run
(engine `5feec18e8a2e`, `term_units_total` identically 0, verdict INERT) and
`results/g5_responsiveness.json` is the reported one (engine `02ad951e4e45`).
**Every other counter is byte-identical between the two files** — the fix added
charging sites and changed nothing else.

**The standing lesson: a per-variant profile is not a nicety, it is the
diagnostic.** The aggregate says "blind." The profile says "blind *because you
instrumented a path this workload never takes*, and here is the path it does."

---

## 5. THE RETROACTIVE SWEEP — every existing counter

### 5.1 On each counter's OWN pre-registered axis

Claim table fixed in prereg §4.1 **before** measurement and **not edited
afterwards** (asserted by `test_every_counter_was_judged_on_its_PRE_REGISTERED_axis`).

| verdict | n | counters |
|---|---|---|
| **RESPONSIVE** | **22** | `cand_enum`, `cand_enum_scan`, `cand_enum_local`, `cand_enum_first`, `cand_enum_repeat`, `cand_tested`, `where_evals`, `where_evals_first`, `where_evals_repeat`, `where_rejects`, `pushdown_evals`, `pushdown_prunes`, `leaf_visits`, `bindings_cloned`, `apply_probe_rollbacks`, `epochs`, `epochs_apply_once`, `cand_enum_apply_once`, `ffi_calls`, `ffi_items`, `ffi_pyobjects`, `graph_writes` |
| **INERT** | **3** | `cand_enum_hinted`, `cand_reject_bound`, `var_collisions` |
| **BLIND** | **2** | `rule_enumerations`, `rule_enumerations_repeat` |

ρ (reported, never gated) is **0.97–1.01 for 18 of the 22 RESPONSIVE** — near-
proportional tracking. Two track sub-proportionally and are correctly flagged as
responsive rather than proportional: `apply_probe_rollbacks` **ρ=0.595** and
`where_evals_repeat` **ρ=0.568**.

### 5.2 THE 2 BLIND ARE MY ERROR, AND THE FIX IS NOT TO EDIT THE CLAIM

`rule_enumerations` is **constant at 650** across a 64× graph-size sweep — the
A8 signature exactly. But the cross-table (§5.4) shows it is **RESPONSIVE with
ρ = 1.0000 on SWEEP-E**:

| | SWEEP-G (64×) | SWEEP-E (64×) |
|---|---|---|
| `rule_enumerations` | 650, 650, … 650 → **BLIND** | 130 … 8376 → **RESPONSIVE ρ=1.0** |
| `rule_enumerations_repeat` | 150, 150, … 150 → **BLIND** | 30 … 1976 → **RESPONSIVE ρ=1.0** |

Its doc comment says *"one per `match_rule_each` from the fixpoint"* — an
**epoch-scaled** quantity, not a graph-size-scaled one. **I assigned it to
SWEEP-G in the claim table. That was wrong, and the wrongness is mine.**

**I have NOT edited the claim table.** Doing so after seeing the verdict is
exactly the "counter picks its axis afterwards" unfairness the prereg forbids,
and a gate asserts the assignments are unchanged. The pre-registered verdict
stands as BLIND-on-G, with the diagnosis reported beside it.

**The substantive fact that survives the error, and it is real:**
`rule_enumerations` **is genuinely blind to graph size.** It counts enumerations
*begun*, not work done, so it is constant while `cand_enum` grows 63×. **Any
argument that treats an enumeration count as a proxy for enumeration COST is
invalid**, and `VISION_SCALE_SPLIT_RESULTS.md` §1 already found this
independently from the other direction — the locality rung measured that "an
enumeration COUNT is not a scan count" because a per-rule cursor can make an
enumeration enumerate zero candidates. **Two rungs, two methods, one conclusion,
arrived at without either knowing of the other.**

### 5.3 THE 3 INERT — never exercised, therefore unvalidated

`cand_enum_hinted`, `cand_reject_bound`, `var_collisions` are **identically zero
on ALL FOUR sweeps**. **P4 confirmed.** INERT is **not a pass**: these three
remain unvalidated by any workload in this suite. `cand_enum_hinted = 0
everywhere` was already declared as a known gap by
`VISION_SCALE_SPLIT_RESULTS.md` ("the indexed branch is untested"); this rung
confirms it and adds two more.

### 5.4 THE CROSS-TABLE — and the finding that is larger than any single cell

Every counter on every sweep. **The last column is the point.**

| counter | G | B | E | **S (sd/identity)** |
|---|---|---|---|---|
| `cand_enum` and its 5 splits | RESPONSIVE | INERT | RESPONSIVE | **BLIND / INERT** |
| `where_evals` ×4 | RESPONSIVE | INERT | RESPONSIVE | **BLIND** |
| `pushdown_evals`, `pushdown_prunes` | RESPONSIVE | INERT | RESPONSIVE | **INERT** |
| `leaf_visits`, `bindings_cloned`, `cand_tested` | RESPONSIVE | INERT | RESPONSIVE | **BLIND** |
| `apply_probe_rollbacks` | RESPONSIVE | INERT | RESPONSIVE | **BLIND** |
| `rule_enumerations` ×2 | **BLIND** | INERT | RESPONSIVE | **BLIND** |
| `epochs`, `epochs_apply_once` | BLIND | INERT | RESPONSIVE | **BLIND / INERT** |
| `ffi_*` ×3, `graph_writes` | RESPONSIVE | RESPONSIVE | RESPONSIVE | **BLIND / INERT** |
| `cand_enum_hinted`, `cand_reject_bound`, `var_collisions` | INERT | INERT | INERT | **INERT** |
| **`term_eval:*` (new)** | — | — | — | **BLIND (all 18 variants)** |
| **`term_unit:*` (new)** | INERT | INERT | INERT | **RESPONSIVE ρ=1.0** |

> **NOT ONE of the 27 existing counters is RESPONSIVE on the sd/identity axis.
> 27 of 27 are BLIND or INERT.**

**This does not accuse those counters of anything** — none claimed the sd axis,
and a counter blind to somebody else's axis is not a defective counter.
Conflating the two would inflate the finding, and this rung's whole subject is
instruments reporting more than they measured. What it establishes is the
**scope boundary, measured**: the last three rungs' shared closing sentence *"the
sd/identity layer is NOT measured"* was not a caveat about coverage. **It was a
structural fact about the instrument, and it now has a table behind it.**

### 5.5 LANDED CONCLUSIONS THIS CALLS INTO QUESTION — named, not re-litigated

Per prereg §4.3, the conclusions are **named** and sequencing is the
supervisor's. **No rung is re-litigated here and no number above is disputed.**

1. **`VISION_SCALE_SPLIT_RESULTS.md`, `VISION_BATCH_APPLY_RESULTS.md`,
   `VISION_LOCALITY_INDEX_RESULTS.md` — the three-way F/C/R split, the
   architectural/computational verdict, and the locality-index ceiling.**
   Their counters are RESPONSIVE on the axes they used (§5.1), so **nothing in
   them is impeached by this sweep.** What is now measured rather than assumed
   is their **scope**: every one of them is a statement about the retina-drive
   workload, and all three closed by saying so. This rung supplies the evidence
   that the caveat was mandatory rather than modest.
2. **Any use of `rule_enumerations` as a proxy for enumeration WORK.** It is
   blind to graph size (§5.2). I found no landed conclusion that does this —
   `VISION_SCALE_SPLIT_RESULTS.md`'s only reference is to the instrument's own
   half-inert first build, and the locality rung uses `rule_costs()`, a
   different readout, and reached the same conclusion independently. **Named as
   a hazard, with no conclusion currently resting on it.**
3. **`VISION_VIDEO_PROBE_RERUN_RESULTS.md` §3.1 arm A8 — already withdrawn by
   its own author as UNINTERPRETABLE.** This rung supplies the missing gate and
   confirms the diagnosis quantitatively. Nothing further to retract.

---

## 6. PREDICTIONS — 3 right, 1 half, 1 wrong

| | prediction | outcome |
|---|---|---|
| **P1** | `term_eval:ShapeDecode` BLIND on SWEEP-S | **RIGHT**, and stronger than stated: **all 18** exercised `term_eval` cells are BLIND, `term_evals_total` constant at 424 across 11.8×. *The named proviso (per-cell quantum minting would raise invocations) did not occur — the workload recognises, so no minting happens.* Note the variant I named does not appear: the path is `TransformDecode`/`DimInfer`, not `ShapeDecode`. |
| **P2** | `term_unit:ShapeDecode` RESPONSIVE, ρ between 1 and 2 | **HALF.** RESPONSIVE ✅ — but only after the dead-instrument fix (§4), so the first measurement **falsified it outright**. And **ρ = 1.0000 exactly**, not "between 1 and 2": the "quadratic-flavoured" reasoning was wrong for the same reason A8's was — I reasoned about the composer path the workload never takes. |
| **P3** | most C/R counters GREEN on SWEEP-G; `epochs` RED by construction | **RIGHT** (20/22 of the SWEEP-G-claiming counters responsive; `epochs` BLIND as the declared control). |
| **P4** | at least one existing counter INERT across the suite | **RIGHT** — three, and all four sweeps. |
| **P5** | overhead resembles the fallback trace more than the winner-value instrument | **WRONG on the workload I did not name and RIGHT on the one I did.** +23.08% on the retina drive is not "fallback-trace-like"; it is a quarter of the way to the winner-value instrument. *The named proviso — "`evaluate` is the hottest function in the engine … the number could be much larger than intuition suggests" — is exactly what happened, and it broke in the direction I flagged.* The default was fixed independently of the number (§9), as pre-registered. |

**⚠️ ρ = 1.0000 IS FORCED, AND IS NOT EVIDENCE ABOUT sd COST (§13.1).** Interior
units land at **exactly 10,004 per cell at every one of the seven points**.
`build_candidate` charges one unit per aligned pair and is called a fixed number
of times at K=1, so **linearity in N is a property of the charging scheme, not a
discovery about decode.** It is a *consistency check that the counter tracks N*
and nothing more. The model could not have produced a non-linear ρ here, which
by §13.1's test makes it construction, not evidence.

---

## 7. GATES

| gate | result |
|---|---|
| **G1 zero-when-off** on a LIVE workload | **PASS** — all counters 0 while off; same workload gives 424 evals / 1.4M units while on |
| **G2 byte-identity** — oracle bench | **PASS — 222 passed, exit 0** |
| **G3 determinism** | **PASS** — byte-identical across repeat runs; every control span exactly 0 |
| **G4 table integrity** | **PASS** — 175 names, unique, non-empty, arrays agree; generator committed |
| **G5 responsiveness** | **the rung's subject** — §3, §5; positive-controlled both ways |
| provenance | **PASS** — 7/7, engine `02ad951e4e45`, own build |
| new gate | `tests/test_term_eval_counter_migrated.py` **13/13** |

### 7.1 ORACLE BENCH

`bash scripts/rung7_vision_bench.sh` with `data/` symlinked, on THIS rung's own
engine `02ad951e4e45`:

```
222 passed in 153.45s        exit 0
```

**Identical to the committed oracle** (222 / exit 0 — the figure that superseded
the old 200 when the paint gate joined the named list at `581a88e6`). The
**sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` is UNMOVED**
(`test_the_sd_orbit_law_is_UNMOVED` + `test_sdloop_vision_migrated` 9/9).

The instrument is DEFAULT OFF and asserted so against the shipped binary, so §9
holds by construction: no committed result can move unless the audit is
explicitly enabled.

### 7.2 WHERE THE RUST-LEVEL GATES COULD NOT RUN — declared, not hidden

`runners/dsl/Cargo.toml` sets pyo3's `extension-module` **unconditionally**, so
`cargo test` cannot link this crate. **PRE-EXISTING** — recorded in
`VISION_SCALE_SPLIT_RESULTS.md` §1.2 and `VISION_INK_VENTRAL_RESULTS.md`, and
confirmed here (undefined `PyErr_Restore` &c. at link). The `#[cfg(test)]` tests
in `g5.rs` and `scale_audit.rs` are **unrunnable in this tree** and are kept as
executable documentation. **Every one of them has a twin in
`tests/test_term_eval_counter_migrated.py` asserting the same series against the
SHIPPED ENGINE** — the stronger location, since it tests the binary that produced
the numbers.

---

## 8. BOUNDS — what is NOT shown

- **This rung does NOT measure the sd/identity layer's scaling.** It is the next
  rung and remains blocked on this one. Every sd number here is **SYNTHETIC**
  (seed 67000) and is an instrument reading, not a cost result. The per-cell
  10,004 is forced by the charging scheme (§6) and must never be quoted as a
  decode cost.
- **K = 1 throughout.** The codebook axis — which the exploratory arm measured as
  linear and named as the second multiplicative term — is **not swept here**.
  `term_unit`'s responsiveness to K is **untested**.
- **`ShapeDecode` itself is untested.** The sd workload runs
  `TransformDecode`/`DimInfer`. The `covers_relation` / `shape_fit` unit sites
  are **committed but never exercised by any sweep in this rung** — they are, by
  this rung's own standard, **INERT and unvalidated**. Stated plainly because
  the alternative is the disease.
- **157 of 175 variants are never exercised** by these four workloads. The
  choke point makes coverage structural, so they will count when reached — but
  "will count" is an argument, and this rung measured 18.
- **The three INERT existing counters remain unvalidated**, not vindicated.
- **G5 is a gate on RESPONSIVENESS, not on CORRECTNESS.** A counter that moves
  with its axis for the wrong reason passes G5. It rules out insensitivity; it
  does not rule out mis-attribution.
- **The overhead numbers are wall-clock and contaminable**, median of 5 on a
  shared machine, and are the only such numbers here.
- **One workload per axis.** SWEEP-G/E use the committed retina drive; a
  different rule topology could exercise `var_collisions` or the hinted branch
  and turn an INERT into a verdict.

---

## 9. FOR THE NEXT RUNG

1. **The sd/identity layer is now measurable.** `term_unit` sees it; the profile
   says `DimInfer` holds 99.92% of the interior work at 4.0% of the invocations.
   The N × K product named by the exploratory arm can now be counted rather than
   timed.
2. **Sweep K.** `term_unit`'s K-responsiveness is untested and K is the axis the
   exploratory arm identified as the real wall.
3. **Exercise `ShapeDecode`.** Its two unit sites are committed and unvalidated.
4. **G5 belongs on every future counted statistic**, with its claimed axis
   declared before measurement. It cost one function and it caught a dead
   instrument on its first firing.
5. **Named, not built** (§11 rule 4 — not my files): the provenance `STALE`
   marker should refuse, not narrate (§0.1); and `rule_enumerations`' doc comment
   would be clearer if it said which axis it scales with.
