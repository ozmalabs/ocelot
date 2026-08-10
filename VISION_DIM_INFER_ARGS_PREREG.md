# THE `I` = 17 QUESTION — PRE-REGISTRATION: are the seventeen `DimInfer` invocations seventeen DISTINCT decodes?

*Written and committed **BEFORE** the instrument exists and before any
measurement. Seeds **88000–88999**. This rung answers the discriminating test
that `VISION_IDENTITY_COST_ANATOMY_RESULTS.md` §5.4 specified and deliberately
refused to run in the same rung as building the instrument.*

---

## 0. THE INHERITED POSITION — what is already settled, and is NOT reopened

`VISION_CODEBOOK_AXIS_RESULTS.md` and `VISION_IDENTITY_COST_ANATOMY_RESULTS.md`
between them fixed the identity layer's coefficient as

```
units  =  I × K × ΣP × N × (1+s)
```

with measured/predicted = **1.0000** at every measured point, on **both** paths.
Three of the four factors are closed and this rung **does not reopen them**:

| factor | value | status inherited |
|---|---|---|
| `N`, `(1+s)` | 142, 4 | irreducible — real data, the arithmetic of comparing a signature to a candidate |
| `K` | codebook entries | irreducible at this layer — the count of things the agent has learned |
| `ΣP` = 13 | the length-1 arm | **PROVED non-prunable** by the codebook rung (§8.1): the Occam key's later components discriminate *within* the arm |
| **`I`** | **17 exact / 2 novel** | **never explained.** THIS RUNG'S ONLY SUBJECT |

**`ΣP` = 13 is not reopened here, and the reason is stated rather than assumed:**
the codebook rung's residual §8.1 names the *different argument* a prune there
would need (an exactness proof over the Occam key's later components), and that
argument is about the comparator's semantics, not about invocation scheduling.
It is a different question with a different method. Touching it here would be
scope creep into a proof this rung is not running.

**What `I` costs.** `I` is why compute-∝-surprise sits at a *magnitude* of 1.33
even though the codebook fix corrected its *sign*: the recognising path spends
`17 × 13 = 221` attempt-units against the novel path's `2 × 147 = 294`. The
recognising path spends **8.5× more invocations than the failing one**. `I` caps
the property the architecture wants.

---

## 1. THE HYPOTHESIS, TWO-SIDED

**H0 (irreducible).** A successful decode mints graph state — `Transform` nodes,
status transitions, `codebook_epoch` bumps — which **re-arms rules by design**.
The 17 invocations each see a genuinely changed argument set, are 17 distinct
decodes, and the cost is real work. **`distinct == I`.**

**H1 (re-derivation).** The recognising path does not grow the codebook and does
not change the residual, so the 17 invocations receive **identical** arguments
and 16 of them recompute a value already computed. **`distinct ≪ I`.**

**Both outcomes are full results and are pre-committed as such.** H0 is the
loud one: it says the identity layer's coefficient is irreducible arithmetic at
**94 µs/cell**, that resolution is capped by real work at **~28×28**, and that
the answer must come from **fewer cells decoded, foveation, or a cheaper
recognition path** — not from removing redundancy that is not there.

---

## 2. THE STATISTIC, EXACTLY

### 2.1 The argument tuple — declared from the SOURCE, before measuring

`eval_dim_infer(arena, goal_idx, codebook_type, exclude_idx, generator_type,
max_dims, field, env, ctx)` is a **pure function of five derived quantities**,
and this is read off its own body, not chosen:

| determinant | how it is obtained in the body | what it subsumes |
|---|---|---|
| `parts` | `load_parts(ctx, codebook_type, …)` then `apply_exclude(…)` | `codebook_type`, `exclude_idx`, and the graph's codebook contents |
| `generators` | `load_generators(ctx, generator_type)` | `generator_type` and the graph's `DimensionGenerator` set |
| `goal` | `evaluate(arena, goal_idx, env, ctx)` | `goal_idx`, `env`, and every graph read reachable from the goal term — i.e. **the residual** |
| `max_dims` | argument | — |
| `field` | argument | — |

Everything else the function touches (`arena`, `env`, `ctx`, `extra`,
`extra_rev`, `sorted_o`, `next_id`) is either an input to the five above or is
derived from them. **Two invocations with equal tuples return equal values.**
Therefore the second one's work is redundant *by definition of redundancy*, and
this is the tuple the reducibility question is actually about.

**THE STATISTIC:**

```
dim_infer_arg_calls     — invocations reaching the recording site
dim_infer_arg_distinct  — |{ encode(parts, generators, goal, max_dims, field) }|
```

both over **one `run_rules` fixpoint**, reported against `I` =
`term_eval:DimInfer`.

### 2.2 EXACT ENCODING, NOT A HASH — declared, with its reason

The specified test said *"a hash of `(residual, codebook contents, epoch)`"*.
**This rung records the EXACT canonical byte-encoding of the tuple and stores it
in a set — no hash.** A hash can COLLIDE, and a collision under-counts
`distinct`, which biases the measurement **toward H1 (reducible)** — toward the
more interesting answer. An exact encoding cannot under-count. Memory is
bounded and trivial (17 tuples × a few tens of KB, audit off by default).

### 2.3 TWO DEVIATIONS FROM THE SPECIFIED TUPLE, both declared BEFORE measuring

**(a) `epoch` is EXCLUDED from the primary statistic.** `codebook_epoch` does
not enter `eval_dim_infer` — it is read by the *rules'* `where` guards to decide
whether to fire, never by the decode itself. Two invocations with identical
decode arguments and different epochs return **the same value**, so the second
is redundant work regardless of epoch. Including epoch would inflate `distinct`
for a reason that has nothing to do with whether the computation is redundant,
i.e. it would bias **toward H0**. Excluded, and said so here rather than
discovered later. *(Note that this deviation makes the H0 verdict HARDER to
reach, not easier — the direction §5 cares about.)*

**(b) `distinct` is reported in TWO forms, both pre-declared.**

- **`distinct_ordered` (PRIMARY)** — the encoding preserves the order in which
  `parts` and `generators` were loaded. This is the complete determinant set:
  attempt order genuinely affects the answer, because `best` is selected by `<`
  and **first-seen wins on equality**.
- **`distinct_unordered` (SECONDARY, a LOWER BOUND)** — the same encoding with
  `parts` and `generators` each canonically sorted. Codebook load order is a
  graph-iteration fact and could churn without any semantic change; encoding
  that churn would over-count and bias **toward H0**.

**If the two disagree, both are reported and the verdict is stated as a BOUND,
never as a single number.** Choosing between them after seeing which one gave a
tidier answer is exactly the §5 failure this rung is built to avoid.

---

## 3. STEP 0 — G5 ON MY OWN AXES, BEFORE ANY HEADLINE

**Two predecessors each validated a counter on one axis and each had to check a
second. The cost rung ran G5 on three and reported it as a *checked pass*. This
rung's counter is a NEW KIND — a DISTINCTNESS statistic, not a count — and no
existing axis validates it.** A blind measurement here would repeat precisely
the failure the whole instrument line exists to prevent.

**A distinctness instrument has two opposite failure modes, and each fakes one
of my two hypotheses.** Neither is caught by any gate that asks "is it
non-zero?", and neither is caught by G5 on N/K/P alone:

| failure | what it reads | which hypothesis it FAKES |
|---|---|---|
| the encoding carries something incidental that varies per call (an address, a counter, load order) | `distinct == calls` always | **H0 — IRREDUCIBLE** |
| the encoding collapses a real determinant (e.g. omits `parts`) | `distinct == 1` always | **H1 — REDUCIBLE** |

**So this rung ADDS A FOURTH AXIS — DISTINCTNESS — with ground truth known by
construction, and runs the two exact controls plus a G5 sweep on it.** These are
the sites I had to add; the three inherited axes validate nothing about
discrimination.

| control | construction | **ground truth, declared in advance** |
|---|---|---|
| **D-RED** (collapse detector) | 7 evaluations of the SAME `DimInfer` term against an UNCHANGED graph | `calls` = 7, **`distinct` = 1 EXACTLY** |
| **D-GREEN** (discrimination) | 7 evaluations, each with a DIFFERENT goal | `calls` = 7, **`distinct` = 7 EXACTLY** |
| **D-CODEBOOK** (the decisive one) | 7 evaluations, SAME goal, **codebook grown by one part between each** | `calls` = 7, **`distinct` = 7 EXACTLY** |
| **D-SWEEP** (G5 proper) | `J` distinct-goal evaluations, `J` ∈ {1,…,7} | sweep = 1,2,…,7 ⇒ **RESPONSIVE**; control at `J`=1 ⇒ span 0 |

**D-CODEBOOK is the control that decides whether this rung can rule at all.**
H0's entire content is *"a decode mints graph state and the next invocation
therefore sees something different."* An instrument that encoded only the goal
would pass D-RED and D-GREEN and be **structurally blind to codebook growth** —
it would return `distinct = 1` and I would report H1, confidently and wrongly.
D-CODEBOOK is the positive control for the mechanism H0 names.

**G5 also runs on all three inherited axes** (N, K, PATH) for both new counters,
alongside the existing `term_eval:*` / `term_unit:*` families. Verdicts are
handed to `runners/dsl/src/g5.rs`; the harness does not reimplement them.

**Pre-committed:** if any control returns other than its declared ground truth,
**the instrument is broken, no `distinct` figure is reported as a result, and
the rung reports the instrument failure as its outcome.** A `distinct` count
from an instrument that failed D-RED or D-CODEBOOK is not a weak result — it is
not a result.

### 3.1 CONSERVATION IDENTITY — the site is where I claim it is

`dim_infer_arg_calls` **must equal** `term_eval:DimInfer` on every measured
point. The recording site sits after `load_parts` / `apply_exclude` /
`load_generators` / the goal evaluation, inside a function the invocation
counter wraps at the dispatch point. If the two disagree, the site is not on
the path the invocation counter counts, and the comparison to `I` is
meaningless. Asserted, not assumed.

---

## 4. WORKLOAD — stated completely (the bounds clause)

| field | value |
|---|---|
| generator | deterministic LCG synthetic cells, **seed base 88000** (block 88000–88999) |
| decoys | independent LCG draws, seeds **88100+** |
| N | 12, 20, 37, 58, 93, 123, 142 |
| K | 1, 2, 3, 5, 8, 12, 16 |
| path | `exact` (recognised, short-circuit fires) · `novel` (nothing explained) |
| headline point | **N=142, K=1, `exact`** — the point at which `I` = 17 was measured |
| liveness | every point must return `recognized_transformed`; a floor score from a dead arm is not a measurement (§1.1) |

`n` is not a statistical `n`: these are integer counters on a deterministic
engine (G3). Determinism is nonetheless **measured**, not assumed — the G5
control arm re-runs each configuration 7× and its span must be 0.

---

## 5. DECISION RULE

Read at **N=142, K=1, path `exact`**, with every control in §3 passing:

| outcome | verdict |
|---|---|
| **`distinct_ordered == I`** and `distinct_unordered == I` | **IRREDUCIBLE.** 17 real decodes. The identity coefficient is irreducible arithmetic at 94 µs/cell; ~28×28 stands as a real cap; **the answer must come from fewer cells, foveation, or a cheaper path.** Reported as loudly as reducibility |
| **`distinct_ordered < I`** | **REDUCIBLE.** Up to `(I − distinct)/I` of the remaining `DimInfer` work is re-derivation. **NAME the mechanism. DO NOT FIX IT IN THIS RUNG** |
| the two forms disagree | verdict stated as a **BOUND**, `[distinct_unordered, distinct_ordered]`, with both reported and neither chosen |
| any §3 control fails its declared ground truth | **NO `distinct` FIGURE IS REPORTED.** The rung's result is the instrument failure |

**Why the fix does not happen here.** The predecessor stopped for exactly this
reason and the reasoning applies unchanged one level down: building an
instrument, reading a redundancy fraction off it, and shipping the memoisation
that the fraction justifies — all in one rung — is how an optimisation gets its
own success criterion. If `distinct < I`, the memoisation owes an **exactness
argument** (identical arguments ⇒ identical value ⇒ the cached value is the
value that would have been computed) and that argument must be pre-registered
and gated on its own, against the possibility that some determinant is missing
from §2.1's list.

---

## 6. PREDICTIONS, STATED IN ADVANCE

| | prediction | reasoning, and its proviso |
|---|---|---|
| **P1** | D-RED reads **1**, D-GREEN reads **7**, D-CODEBOOK reads **7** — all exactly | the encoding is built from §2.1's determinant list and nothing else. *Proviso: if D-RED reads 7, some incidental varies per call and §2.1 is incomplete — a finding about the function, not only about the instrument* |
| **P2** | G5 on D-SWEEP: **RESPONSIVE** | distinct is 1..7 by construction |
| **P3** | G5 on N and K for `dim_infer_arg_distinct`: **BLIND** | `I` is invariant on both (17 at all 7 points, over 11.8× and 16×), so a distinct-count that tracks it must be too. **BLIND here is a measurement, not a defect** — the quantity is constant. If it reads RESPONSIVE, the encoding is carrying N or K itself and P1's controls should have caught it |
| **P4** | G5 on PATH: **RESPONSIVE** | `I` moves 17 → 2 |
| **P5** | **`distinct < I`, and specifically `distinct ≤ 3`** | the recognising path does **not** grow the codebook — `sd_mint_quantum` fires only when nothing is explained — so `parts` and `generators` should be constant across the fixpoint, and if the residual is also unchanged then every invocation carries the same tuple. *Proviso, and it is H0 exactly: if the decode's own minted `Transform` nodes or status transitions feed back into `parts` or into the goal term's graph reads, `distinct` will be 17 and I am wrong* |
| **P6** | `dim_infer_arg_calls == term_eval:DimInfer` at every point | §3.1. If not, the site is misplaced |

**P5 is the prediction that can embarrass me, and it is stated before the
instrument exists.** The negative — `distinct == I` — is pre-committed as a full
result in §1 and §5 regardless of which way P5 falls.

---

## 7. SCOPE — what this rung does NOT show

- It measures **one workload family** (synthetic LCG cells, target as `held[0]`,
  K ≤ 16, one decoy family). Codebook *contents* may affect scheduling in ways
  one decoy family cannot show.
- It measures **invocation arguments**, not *why the scheduler runs the rule*
  that many times. A `distinct ≪ I` result localises the redundancy to the
  fixpoint's re-arming; it does not explain the re-arming.
- It changes **no behaviour**. The recording site is gated on the scale audit,
  which is **off by default** (§9), and no seed and no rule is edited.
- It **fixes nothing**, by §5's own reasoning.

---

## 8. GATES

| gate | when |
|---|---|
| provenance (`tests/test_engine_provenance_migrated.py`) | **its OWN step, BEFORE any number**, engine pinned by hash |
| endpoint guard | both endpoints pinned, never `HEAD` |
| oracle bench `scripts/rung7_vision_bench.sh` | **222** with `data/`, 212/10 without |
| sd-layer suites (dimension inference / transform / sdloop / ink / codebook-axis / term-eval / identity-cost) | unchanged |
| §9 byte-identity | the audit is off by default; every committed contract unmoved |
| new gate `tests/test_dim_infer_args_migrated.py` | the four §3 controls, the §3.1 conservation identity, and the encoding's determinant coverage |
