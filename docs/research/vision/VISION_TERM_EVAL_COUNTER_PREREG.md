# TERM-EVAL COUNTER + THE G5 RESPONSIVENESS GATE — PRE-REGISTRATION

*Written and committed BEFORE any implementation (PROTOCOL §3). Seed block
**67000–67999**, verified free before launch; no other block is taken.*

---

## 0. WHY THIS RUNG EXISTS — a new failure class

`VISION_VIDEO_PROBE_RERUN_RESULTS.md` §3.1 (merged `a67afe4f`) recorded a failure
that **no gate in this arc catches**:

> Arm A8 pre-registered a counted-operation exponent for the sd/identity layer.
> **Every `scale_audit` counter was BYTE-IDENTICAL across an 11.8× range of N**
> (`cand_enum` 21, `rule_enumerations` 68, `ffi_calls` 1, `leaf_visits` 4, at
> every point) **while wall-clock grew 13×**. All four pre-declared gates —
> G1 zero-when-off, G2 liveness, G3 determinism, G4 N-varies — **PASSED**, and
> the pre-registered rule read literally returned *"the sd/identity layer is NOT
> the binding term; the wall FELL."* A fluent, gated, entirely wrong answer.

The diagnosis is architectural, not a bug: **a signature is an ATTRIBUTE, not a
subgraph.** All N cells live in one node's attribute list, so the graph the rule
engine matches over is constant in N. The whole cost is inside `ShapeDecode` /
`TransformDecode` **Term evaluation**, which `scale_audit` does not count and was
never built to count.

Two consequences, and the second is larger than the first:

1. **The entire scale toolkit of the last three rungs is structurally blind to the
   sd/identity layer.** Each of those rungs closed with "the sd/identity layer is
   NOT measured" while holding an instrument that *could not* have measured it.
2. **This is a NEW failure class.** The arc's eleven previously-caught inert
   instruments were all **dead** — a counter reading zero, a hook on the wrong
   store, a path that never ran. This one is **ALIVE, DETERMINISTIC, CONSERVED,
   AND INSENSITIVE.** Every existing gate is satisfied by an instrument that is
   measuring something else entirely.

This rung builds (Part 1) a statistic that can see Term evaluation, and (Part 2)
the gate that would have caught the failure — **applied retroactively to every
existing counter**, because if others are also insensitive then landed
conclusions rest on them.

**Part 2 is the more important half.** A counter is a tool; a gate is a policy.

---

## 1. WHAT THIS RUNG DOES NOT DO

**It does NOT measure the sd/identity layer's scaling.** That is the next rung and
it is explicitly blocked on this one. Building an instrument and then using it in
the same rung is how a statistic gets defined to suit the answer (§5).

To make that boundary *structural* rather than promised, every sweep here runs on
**SYNTHETIC** signatures generated from a declared seed — never on real frames.
A synthetic sweep cannot be mistaken for, or quoted as, the sd/identity
measurement, and no exponent for real-workload sd cost appears in this rung's
results. The one continuous quantity reported (ρ, §4.3) is a **responsiveness
diagnostic of the INSTRUMENT on synthetic input**, never used to pass or fail
anything, and explicitly not a cost exponent.

---

## 2. PART 1 — THE COUNTED STATISTIC

### 2.1 The choke point

`term.rs::evaluate(arena, idx, env, ctx)` is the **single** dispatch point for
every Term evaluation in the engine — one `match node { … }` over
`TermNode`'s 175 variants, recursive, with every sub-term routed back through it.
Instrumenting there makes coverage **structural rather than remembered**, which is
`scale_audit.rs`'s own stated reason for process-global atomics and the direct
lesson of eleven inert instruments (§12, §12.1).

### 2.2 PER VARIANT, NOT PRE-AGGREGATED

A `Plus` and a `ShapeDecode` are not the same cost, and aggregating them hides
exactly the class of thing that just went wrong. A single total would have told
A8 "the number went up" without telling it *where*, which is the question the
next rung must answer.

`TermNode::variant_index() -> u16` and `TERM_VARIANT_NAMES` are **GENERATED** from
the enum body by `tools/gen_term_variants.py`, committed, and guarded by a test
that fails if the table drifts from the enum. `NUM_TERM_VARIANTS` is therefore the
enum's own arity — **a number that falls out** (§13), not a chosen constant.

### 2.3 TWO COUNTER FAMILIES — and the second is the one that matters

**This is the crux of the design, and it is stated in advance because it is the
part most likely to be wrong.**

| family | what it counts | charged where |
|---|---|---|
| `term_eval:<Variant>` | **invocations** — times `evaluate` dispatched to that variant | the single choke point, all 175 variants |
| `term_unit:<Variant>` | **interior comparison units** — elementary work performed *inside* one evaluation | the interior loops of variants that loop |

**Why two.** For a leaf variant (`Plus`, `Attr`, `Var`) interior work is O(1), so
invocations *are* the cost and `term_unit` is legitimately zero. For an aggregate
variant (`ShapeDecode`) **one invocation performs O(N·K) work**, so an invocation
count is *itself insensitive to N* — it would reproduce the exact disease this
rung treats, at a finer granularity.

**I therefore predict my own first family FAILS G5 on the sd axis (P1 below), and
that is not a defect to be hidden — it is the measurement that proves why the
second family is necessary.** If only `term_eval` were built and shipped, this
rung would have replaced a blind instrument with a blind instrument.

`term_unit` is attributed by an **innermost-variant stack**: `evaluate` pushes the
dispatching variant on entry and pops on exit (RAII guard, so early returns are
safe), and any unit charged anywhere below is charged to the innermost Term
variant currently evaluating. Attribution is therefore structural too — a new
interior loop is attributed correctly without its author remembering to name a
variant.

Initial unit-charging sites (named exhaustively; anything not listed charges
nothing and its `term_unit` is legitimately 0):

- `shape_decode.rs::covers_relation` — one unit per held-relation `step` examined
  against one goal relation. This is the O(N_residual × N_part) core of decode.
- `shape_decode.rs::shape_fit` — one unit per relation position anti-unified.

### 2.4 Cost, and the default FOLLOWS the number (§13)

Overhead is **measured and stated**, and the default is derived from it, not
hand-set. The two precedents in the tree are quoted so the comparison is explicit:

- the winner-value instrument measured **81.41%** and ships **OFF**;
- the fallback trace measured **0.000%** and was honestly reported as free
  *because it never fires*.

This rung states which of those its instrument resembles, with the number.
Independently of the number, it ships **OFF by default** (§9 — defaults preserve
committed results), gated by a zero-when-off test on a live workload.

---

## 3. PART 2 — THE G5 RESPONSIVENESS GATE

### 3.1 The failure signature, stated as a shape

From §3.1 of the rerun results, the observed signature is:

> the counter is **constant** across a range over which an independent cost proxy
> varies by more than 10×.

A gate built from that shape must ask: **did the counter MOVE with the swept
quantity** — not "is it non-zero", which is what every existing liveness gate
asks and which A8 satisfied.

### 3.2 The criterion, and where it FALLS OUT (§13)

The threshold is **not chosen**. It is measured, per counter, per sweep, from a
control:

- **Sweep** — the counter is read at `m` points as the claimed axis varies over
  ≥10× (the fold-range at which the A8 failure was observed and therefore the
  range the gate must be sensitive at).
- **Control** — the counter is read at `m` points with the axis held **FIXED** at
  the sweep's first value. Same process, same machine, same counter, same
  repetition count.
- `span(S) = max(S) − min(S)`.

> **G5 PASS (RESPONSIVE / GREEN)** iff `span(sweep) > span(control)`.
> **G5 FAIL (BLIND / RED)** iff `span(sweep) ≤ span(control)` and the counter is
> exercised.
> **G5 N/A (INERT ON THIS WORKLOAD)** iff `max(sweep) == 0` — the counter is not
> exercised at all, so this workload cannot rule on it.

**The derivation:** `span(control)` is the counter's own noise under exactly the
conditions of the sweep, measured rather than assumed. G3 (determinism) predicts
it is **exactly 0** for these integer counters, in which case G5 reduces to *"did
it move at all"* — which is what the rerun results named as the missing gate. But
the criterion is written against the **measured** control, not the assumed zero,
so it stays correct if any counter ever becomes non-deterministic. Nothing is
hand-set; no constant enters.

**The three-way verdict is pre-registered NOW, before any result is seen,**
specifically so that "the counter was never exercised" cannot be argued after the
fact as if it were a pass. An INERT verdict is *not* a pass — it is an explicit
statement that the counter remains unvalidated.

### 3.3 The responsiveness diagnostic ρ — REPORTED, NEVER GATED

`ρ = log(max C / min C) / log(max x / min x)` on the sweep, where `x` is the
claimed axis, computed only when `min C > 0`. ρ ≈ 0 ⇒ blind; ρ ≈ 1 ⇒ proportional.
**ρ never passes or fails anything** — gating on it would require choosing a
threshold, which is the §13 violation this design exists to avoid. It is reported
so the next rung knows how strongly each counter tracks its axis.

### 3.4 G5 MUST BE POSITIVE-CONTROLLED — declared in advance

*A gate that has never been able to fail has not been tested*, and this arc has
paid for that lesson repeatedly. Both controls are named now:

- **RED demonstration (must go RED):** `epochs` on SWEEP-G. The graph-size sweep
  makes exactly one rule-running call per point, so `epochs` is constant **by
  construction** — a real, live, deterministic, conserved counter that is
  insensitive to *this* axis. If G5 does not flag it, G5 does not work.
- **GREEN demonstration (must go GREEN):** `cand_enum` on SWEEP-G — the counter
  whose entire purpose is to track candidates enumerated as the graph grows.
- **Pure-function unit tests:** the G5 decision is a pure function of
  `(sweep, control, axis)` and is unit-tested in Rust on synthetic series —
  constant ⇒ RED, monotone ⇒ GREEN, all-zero ⇒ N/A.

---

## 4. THE RETROACTIVE SWEEP — every existing counter

### 4.1 The claim table — declared BEFORE measuring

**G5 is only meaningful against the axis a counter CLAIMS to track**, so the claim
is fixed here, in advance, from each counter's own doc comment in
`scale_audit.rs`. A counter tested on an axis it never claimed would fail unfairly;
a counter allowed to pick its axis afterwards would pass unfairly.

| counter | claimed axis | sweep |
|---|---|---|
| `ffi_calls`, `ffi_items`, `ffi_pyobjects` | Python→Rust boundary crossings and items marshalled | **SWEEP-B** |
| `graph_writes` | attribute writes performed via the boundary | **SWEEP-B** |
| `cand_enum`, `cand_enum_scan`, `cand_enum_local`, `cand_enum_hinted` | candidate pairs enumerated by rule matching | **SWEEP-G** |
| `cand_enum_first`, `cand_enum_repeat` | …split by first/repeat enumeration | **SWEEP-G** |
| `cand_tested`, `cand_reject_bound` | candidates tested / rejected on the bound filter | **SWEEP-G** |
| `where_evals`, `where_evals_first`, `where_evals_repeat`, `where_rejects` | where-clause evaluations at the leaf | **SWEEP-G** |
| `pushdown_evals`, `pushdown_prunes` | pushdown conjunct evaluations / prunes | **SWEEP-G** |
| `leaf_visits` | bindings surviving every filter | **SWEEP-G** |
| `var_collisions` | bindings dropped on a two-var collision | **SWEEP-G** |
| `bindings_cloned` | binding clones pushed into the collect-all vector | **SWEEP-G** |
| `apply_probe_rollbacks` | non-progressing applications rolled back | **SWEEP-G** |
| `rule_enumerations`, `rule_enumerations_repeat` | rule enumerations begun / repeated | **SWEEP-G** |
| `epochs`, `epochs_apply_once` | Python→Rust entries into a rule-running method | **SWEEP-E** |
| `cand_enum_apply_once` | candidates enumerated inside `apply_rule_once` epochs | **SWEEP-E** |
| **`term_eval:<V>`** (new) | Term-evaluation invocations per variant | **SWEEP-S** |
| **`term_unit:<V>`** (new) | interior comparison units per variant | **SWEEP-S** |

### 4.2 The sweeps

| sweep | independent variable | range |
|---|---|---|
| **SWEEP-G** | number of edges of the matched type in the graph | ≥10× |
| **SWEEP-B** | number of boundary calls / items marshalled | ≥10× |
| **SWEEP-E** | number of Python→Rust rule-running calls | ≥10× |
| **SWEEP-S** | cells in a **synthetic** signature ATTRIBUTE (the A8 shape) | ≥10× |

Every counter is additionally read on **SWEEP-S** — not as its claimed axis, but
to reproduce and quantify the A8 blindness systematically rather than anecdotally.
Those cells are reported as a separate table and are **not** counted as G5
failures for counters that never claimed the sd axis. Conflating "blind to its own
axis" with "blind to somebody else's axis" would inflate the finding, and this
rung's whole subject is instruments that report more than they measured.

`m = 7` points per sweep, 7 control repeats. **No power analysis is offered and
none is meaningful**: these are deterministic integer counters, G3 pins their
run-to-run variation at exactly zero, and the control span *is* the noise estimate.
Stating a p-value on a deterministic integer would be a statistic wearing a lab
coat.

### 4.3 What each outcome MEANS — fixed in advance

| outcome | what it licenses | what it does NOT |
|---|---|---|
| **All existing counters GREEN on their claimed axes** | the toolkit is sound *within its declared scope*; the A8 failure was a scope error, not a correctness error | it licenses nothing about the sd axis, where the toolkit remains blind by construction |
| **Some existing counter RED on its OWN claimed axis** | **the largest finding available in this rung** — any landed conclusion resting on that counter is called into question | it does NOT re-litigate those rungs; the conclusions and their results files are **NAMED**, and sequencing is the supervisor's |
| **Some counter INERT across the whole suite** | that counter is unvalidated — never exercised by any workload here | it is not evidence the counter is broken |
| **`term_unit:ShapeDecode` GREEN on SWEEP-S** | the sd/identity layer is measurable by counted operations for the first time; the next rung is unblocked | it is **not** the sd/identity scaling result — synthetic input, instrument test only |
| **`term_unit:ShapeDecode` RED on SWEEP-S** | **the rung has FAILED and reports so.** An instrument that cannot see the thing it was built for is the exact disease being treated | shipping it anyway would be worse than shipping nothing; it would be committed as a negative and left OFF |

---

## 5. PREDICTIONS, STATED IN ADVANCE (§3.7)

Two-sided where a direction is predicted; each with the proviso that would break it.

- **P1 — `term_eval:ShapeDecode` is BLIND (RED) on SWEEP-S.** The number of
  `ShapeDecode` *invocations* does not depend on how many cells its operand holds.
  *Proviso that would break it:* if the sd rule loop re-decodes a number of times
  that depends on N (e.g. residual splitting mints per-cell quanta), invocations
  would rise and P1 fails — which would itself be informative about the loop.
- **P2 — `term_unit:ShapeDecode` is RESPONSIVE (GREEN) on SWEEP-S, with ρ between
  1 and 2.** `covers_relation` scans the held signature once per residual
  relation ⇒ quadratic-flavoured in N at fixed K; the exploratory wall-clock arm
  measured ρ≈1 on *real* frames, so a synthetic ρ near 1 would not surprise me and
  near 2 would mean the synthetic input exercises a denser path than real frames
  do. *Proviso:* if decode short-circuits early on self-identity (the K=1 literal
  case), the scan may terminate on the first step and ρ could fall well below 1
  while still being > 0 — GREEN but weakly responsive.
- **P3 — the majority of C/R counters are GREEN on SWEEP-G**, and `epochs` is RED
  on SWEEP-G by construction (it is the declared RED control, §3.4).
- **P4 — at least one existing counter is INERT across the whole retroactive
  suite.** Several are conditioned on constructs (`IndexJoinHint`, pushdown,
  `apply_rule_once`, probe rollback) that a plain sweep need not exercise.
- **P5 — the ON-overhead is small enough to resemble the fallback trace more than
  the winner-value instrument**, because the added work is one relaxed atomic load
  plus one add per `evaluate`. *Proviso:* `evaluate` is the hottest function in the
  engine and is called at enormous frequency, so if the guard's push/pop is not
  optimised away when disabled, the number could be much larger than intuition
  suggests. **The default ships OFF regardless of which way this lands** — the
  number decides what is *reported*, not what is *defaulted* (§9 fixes the default
  independently).

**Being right in advance is the only evidence the model is understood; a proviso
that breaks tells me what I did not understand.** Both are reported.

---

## 6. GATES ON THIS RUNG ITSELF

| gate | criterion |
|---|---|
| **G1 zero-when-off** | every counter, including all 350 new per-variant cells, reads 0 with the audit OFF on a LIVE workload |
| **G2 byte-identity** | the oracle bench `scripts/rung7_vision_bench.sh` → **222 passed, exit 0**, unchanged, with the audit off by default |
| **G3 determinism** | two identical runs produce byte-identical counters |
| **G4 table integrity** | `NUM_TERM_VARIANTS` equals the enum's arity; a variant added without regenerating fails a test |
| **G5 responsiveness** | this rung's subject — §3, applied to every counter per §4 |
| **provenance** | engine built in THIS worktree by `scripts/engine_build.sh`, hash pinned in the results; both endpoints of every provenance diff pinned (§12.3) |

---

## 7. SEEDS

Block **67000–67999**. This rung has no RNG-seeded experimental arms — every
workload is deterministic. Seeds are used only to generate synthetic sweep inputs:

- **67000** — SWEEP-S synthetic signature generator
- **67001** — SWEEP-G synthetic graph generator

No other seed from the block is consumed. Recorded in the burned-seed ledger on
completion.
