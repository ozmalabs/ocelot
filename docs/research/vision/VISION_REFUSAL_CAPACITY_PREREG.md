# REFUSAL CAPACITY — WHICH OF THE EYE'S MECHANISMS CAN DECLINE, AND WHAT DOES IT COST?

*Pre-registration. Written and COMMITTED before any confirmatory number (§3).*

- **branch (as observed):** `worktree-agent-a041ad6a5be1b42ae`
- **base SHA (as observed):** `91e367f0c332ae29793609c6816f5ba42971d6eb`
- **engine:** `9931e144d19b`, built IN THIS TREE by `scripts/engine_build.sh`
  (`own`). Rust source verified byte-identical to canonical before the build
  (only an untracked `py.rs.selfmod.bak` differs, which is not `.rs` source in
  this tree), so a shared build would also have been legitimate under §10.1;
  the build was done anyway. **THIS RUNG ADDS NO RUST.**
- **provenance gate, its OWN step, before any number:**
  `pytest tests/test_engine_provenance_migrated.py -q` → **7 passed**, and
  `provenance_line()` printed from a fresh process agrees:
  `engine 9931e144d19b @ …/agent-a041ad6a5be1b42ae/…/_native.abi3.so`.
  The confirmatory runner ALSO prints it from inside the measuring process and
  **aborts on divergence** (a green gate in a different process is not
  provenance).
- **`data/`:** symlinked to canonical (§10.2), so the oracle reading is the
  **with-corpus** case.
- **seed block:** 106000–106999.
- **oracle:** `bash scripts/rung7_vision_bench.sh` → **222 passed, 0 failed**, exit 0 (with `data/` symlinked, the §10.2 with-corpus case), measured BEFORE this rung changed anything.

## §3 clause 8 — `check_claim` OUTPUT, VERBATIM

```
SEED CLAIM 106000-106999: CLEAN -- no collision DETECTED.
  Scope: 807 files with seed sinks; 497 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**The unresolved-sink count is 497, tree-wide, and it is priced here rather
than waved past:** the claim is clean against 807 scanned files, and the 497
unresolvable sinks are the declared blind spots (CLI/env values, data-derived
seeds, cross-module constants, generator streams). A clean result means *no
collision detected*, never *no collision exists*.

---

## 0 — WHY THIS RUNG EXISTS

Three rungs in two waves independently measured the same shape without looking
for it:

1. the block-matching motion sensor **confabulates rather than abstains** —
   confidently wrong 10.67%, and the wrong vector is well-formed and
   indistinguishable downstream from a true one;
2. `TimeInfer`'s `BlinkBridge` **implements confabulate-always**, with
   confidence decaying `support/(support+gap)`;
3. `GapAbduce` **has no discriminative power** — *"the substrate did not lack
   this operator by oversight; it lacked the operator that cannot refuse."*

And this project holds a recorded position that **confabulation is the
default**: perception always produces a best guess and grounding only
CONSTRAINS it.

So the question is not how to stop confabulating. It is: **which mechanisms CAN
refuse, what does each refusal cost, and where is a refusal even admissible?**

---

## 1 — THE THREE FAILURE MODES, AND WHY THEY LOOK IDENTICAL FROM OUTSIDE

| mode | definition | the fix it implies |
|---|---|---|
| **CANNOT REFUSE** | no admissible null exists in the mechanism's output TYPE | a representation change |
| **DOES NOT REFUSE** | an admissible null exists and the mechanism never takes it on a non-degenerate input | a constraint the search can fail |
| **REFUSES VACUOUSLY** | it emits the null at a GUARD, before any search runs | nothing — the refusal decided nothing; it is a §13 negative |

A fourth outcome must be reported separately because it *scores like* the best
one and is worthless:

| **DEAD** | it refuses EVERYTHING, including what it should accept | §1.1 in refusal form: a mechanism that never accepts scores a perfect refusal arm |

---

## 2 — WHAT I AM COUNTING, AND WHY IT IS THE RIGHT UNIT

**A refusal capacity is not a refusal RATE.** `P(null)` is a property of the
stimulus DISTRIBUTION, not of the mechanism: feed a refuser more garbage and its
rate rises without its capacity changing. This arc has a recorded failure where
a rung pre-registered the right discriminator and measured it on the wrong
quantity, and got no protection from having pre-registered at all. So the unit
is declared here, in advance, with its justification.

### 2.1 The primary statistic — MATCHED-PAIR VERDICT SEPARATION

For mechanism `M`, over `n` matched stimulus pairs `(E, U)`:

> **Δ_M = P(null | U) − P(null | E)**

where `E` is EXPLAINABLE by `M`'s own stated competence and `U` is NOT, and
**`E` and `U` are identical in every guard-visible property** — same arity, same
frame count, same cell count, same non-emptiness, same types, same field
lengths. Only the *structure the mechanism claims to test* differs.

**Why Δ and not the rate.** Δ is invariant to how much unexplainable input you
feed. A mechanism refusing 90% of both arms scores **0**; a mechanism refusing
2% of `U` and 0% of `E` scores **+2%**. That is exactly the asymmetry the brief
names: the 90% refuser may be vacuous and the 2% refuser may be the only one
whose refusals are earned. **Δ measures whether the null is a FUNCTION OF THE
STIMULUS, which is the whole content of "did it decide anything".**

**Why not `checked`.** The engine exposes a candidate counter (`checked`) on
seven of these Terms, and `checked == 0` is tempting as "it never looked". **It
is the wrong quantity and I am recording that in advance:** `checked` counts
CODEBOOK candidates only. A Term can compare frames, find them inconsistent and
refuse without ever consulting the codebook — a refusal that is fully
stimulus-determined and reads `checked = 0`. `checked` is therefore reported as
a **COST** measurement (§2.3), never as the classifier.

### 2.2 The two arms that make Δ interpretable — both mandatory

- **A_M (the POSITIVE CONTROL, §1.1):** does `M` emit a NON-null on at least one
  input? **A mechanism you have not made ACCEPT is one whose refusals mean
  nothing.** If `A_M` is false, `M` is **DEAD** and its Δ is 0 by saturation.
- **G_M (the GUARD ARM):** does `M` emit its null on a DEGENERATE input (empty /
  malformed / wrong arity)? A null that appears ONLY here is **vacuous** — the
  mechanism returned whatever it was told.

**Classification decision rule, fixed in advance:**

| | `n_null` on non-degenerate input | Δ_M CI | verdict |
|---|---|---|---|
| a | 0 | — | **CANNOT REFUSE** |
| b | 0, but `G_M` fires | — | **REFUSES VACUOUSLY** |
| c | > 0 | includes 0 | **DOES NOT REFUSE** |
| d | > 0 | excludes 0, Δ > 0 | **DOES REFUSE (earned)** |
| e | > 0 | excludes 0, **Δ < 0** | **ANTI-CORRELATED** — refuses, but not because of the truth |
| f | `A_M` false | — | **DEAD** (reported separately, Δ void) |

Row **e** is included because the pilot suggests it is reachable, and a
classification scheme that cannot express "it refuses the true thing and accepts
the false one" would silently score that as row d's opposite.

### 2.3 The COST measurement — what would each refusal cost to make earned?

For every mechanism, three numbers, reported whatever the classification:

- **`checked`** on the refusing call — the candidates actually examined. This is
  the price the mechanism ALREADY pays to reach its verdict.
- **wall-time per call**, `E` and `U` arms separately.
- **the named representation change** required to move it up the ladder, with
  the quantity that would have to become falsifiable.

`GapAbduce`'s predecessor named its own answer (*check the emitted intermediates
against the scene*) and a concurrent rung is testing exactly that. **It is used
here as the worked example of what a good answer looks like and is NOT
re-measured.**

### 2.4 n, FIXED IN ADVANCE

`n = 200` matched pairs per mechanism, stimuli drawn from **seeds
106000–106199** (confirmatory, never used for anything). Wilson 95% CIs. At
`p = 0.5` a 200-pair arm gives ±6.9pp; at the extremes (`p ≥ 0.97`) it gives
±2.4pp, which is the regime every prediction below lands in. Pairs are the unit
of analysis, not individual calls (§4: the two calls in a pair share a stimulus
family and are not independent).

Seeds **106200–106399** are reserved for the `DepthInfer` two-layer stimulus
family (a separate construction), **106400–106599** for the `BlinkBridge` gap
family. Deterministic arms draw no seeds at all.

---

## 3 — THE MECHANISM SET, AND HOW IT WAS CHOSEN

Chosen by an **engine-defined** criterion wherever one exists, not by taste:

**Group 1 — every verdict-emitting Term in `runners/dsl/src/shape_decode.rs`**
(the decode/infer family; enumerated from the evaluator list, not from a doc):
`ShapeDecode`, `TransformDecode`, `DimInfer`, `GenInfer`, `TimeInfer`,
`BlinkBridge`, `GapAbduce`, `DepthInfer`.

**Group 2 — the vision primitives** that return a bare value with no verdict
dict: `ChangeDetect`, `TemporalDiff`, `Foveate`.

**Group 3 — the SELECTORS**, included because they are what the seed layer's
refusal guards are BUILT FROM, so their capacity bounds every rule above them:
`Argmin`, `PickUnique`.

**Group 4 — a measured quantity with no verdict at all:** `EnclosedCount`.

**Group 5 — the through-line's own type specimen:** the block-matching motion
sensor (`scripts/motion_sensor_lib.py`), included because the brief names it and
because it is the clearest instance of a mechanism whose OUTPUT TYPE has no null.

**DECLARED OUT OF SCOPE, with reasons** (§8):

- **The SEED-RULE layer** (`bo_mint_*`, `li_mint`, `ci_assign`/`ci_refuse`,
  `uq_admit`/`uq_refuse_ambiguous`, `l3_corroborate`, `gr_fill`, the `sd_*`
  ladder). A rule's refusal is a DIFFERENT unit — non-firing — and needs its own
  matched-pair design and its own pre-registration. **This rung measures the
  TERMS the rules are built from; a rule can be no more refusable than its
  Terms, so this is the lower layer of the same question and the bound it
  establishes propagates upward.**
- **`GapAbduce`'s named fix** (checking emitted intermediates) — a concurrent
  rung owns it.
- **`space_quantize`, `StrokeQuantize`** — not driven by any vision measurement
  path this rung can exercise without building a new harness.

---

## 4 — HYPOTHESES AND PREDICTIONS, STATED IN ADVANCE (§3.7)

**HONESTY DECLARATION, made before the confirmatory run and load-bearing for how
these should be read:** an exploratory pilot (`scripts/refusal_probe.py`,
DETERMINISTIC, **zero seeds drawn**) was run before this file was written, to
discover the engine's field vocabulary — because the alternative was writing the
runner against a doc comment, and four comment-vs-engine divergences have been
recorded in this arc in one week. **The pilot showed me the verdict on the
deterministic single-stimulus case for 8 of the 13 mechanisms.** Predictions
P1, P4, P6, P7, P8 are therefore **PILOT-INFORMED and carry REDUCED evidential
weight** — they are confirmations that the deterministic reading survives 200
fresh adversarial pairs, not discoveries. **The weight of this rung sits on P2,
P3, P5, P9–P13 and C1, which the pilot did NOT settle.**

| # | mechanism | predicted class | prediction, with its proviso | at risk? |
|---|---|---|---|---|
| **P1** | `TimeInfer` | **EARNED** | Δ ≈ 1.0. Proviso: its refusal reads `checked = 0`, so if `checked` were the classifier it would be mislabelled vacuous — the pilot's single case says the verdict flips with structure at constant guard-visible properties. | pilot-informed |
| **P2** | `DepthInfer` | **EARNED** | It refused all six pilot stimuli (`single_velocity` / `non_constant_velocity` / `insufficient_frames`). **I predict `A_M` is TRUE — a genuine TWO-LAYER stimulus will be ACCEPTED.** If it is not, `DepthInfer` is **DEAD** on every stimulus this arc can build, and its five named reasons are decoration. | **YES** |
| **P3** | `BlinkBridge` | **DOES NOT REFUSE** | Across a REAL gap it confabulates always; `kind = "freeze"` is emitted BOTH at the guard and after a failed search, so the output type **conflates guard-refusal with search-failure** and Δ ≈ 0 on the gap arm. Proviso: at gap = 0 it does separate (`explained` flips), so a Δ > 0 on the NO-gap arm would NOT falsify this — the claim is specifically about the gap regime, where the mechanism is actually used. | **YES** |
| **P4** | `GapAbduce` | **DOES NOT REFUSE** | Its only null is `no_gap_structure`, a degenerate-input guard. Δ ≈ 0. Proviso: `identity` and `indivisible` are also nulls; if either is stimulus-determined on matched pairs, Δ > 0 and the class is EARNED-but-orthogonal. | pilot-informed |
| **P5** | `ShapeDecode` | **ANTI-CORRELATED (Δ < 0)** | The pilot authored a plan for an ALIEN cell set and refused a pure TRANSLATE of a held part. **I predict Δ ≤ 0** — its null fires more on explainable input than on unexplainable input. This is the strongest claim in the file and the one most likely to be wrong. | **YES** |
| **P6** | `TransformDecode` | **EARNED** | Δ ≈ 1.0, and it reports `residual_unexplained` — it says WHAT it could not explain. Proviso: `checked` is constant across arms (`= |codebook|`), so its search EXTENT is stimulus-independent while its OUTCOME is not; this is the cleanest demonstration that `checked` is the wrong classifier. | pilot-informed |
| **P7** | `DimInfer` | **EARNED** | Δ ≈ 1.0. Refuses out-of-generator-class images, accepts held-class ones. | pilot-informed |
| **P8** | `GenInfer` | **EARNED** | Δ ≈ 1.0, at the highest cost in the family (`checked` ~2.6 × 10⁵ on a refusal). **The most expensively earned refusal measured here.** | pilot-informed |
| **P9** | `ChangeDetect`, `TemporalDiff`, `Foveate` | **REFUSES VACUOUSLY** | Each returns a bare `Value::None` on a shape/arity mismatch and NEVER on image content. Δ = **0.0 exactly** on matched pairs of well-formed images. | **YES** |
| **P10** | `Argmin` | **CANNOT REFUSE** | On any non-empty source it returns a winner. `n_null = 0` on every non-empty input; no threshold exists in it. **Consequence to be checked, not assumed: every seed guard of the form `Eq(R, Argmin{…})` is satisfiable by an arbitrary tie-break.** | **YES** |
| **P11** | `PickUnique` | **CANNOT REFUSE (it ESCALATES)** | 0 candidates → `None`; >1 → **raises**. It has no verdict-refusal at all: ambiguity is a crash, not a decline. Predicted the only mechanism here that escalates rather than swallowing. | **YES** |
| **P12** | `EnclosedCount` | **CANNOT REFUSE** | Always returns a numeric dict. Degeneracy is a SENTINEL (`holes = 0` with `grid_w = 0`) that is **indistinguishable from a measured zero** unless the caller reads a second field. `n_null = 0`. | **YES** |
| **P13** | motion sensor | **CANNOT REFUSE** | Output type is a 2-vector; `(0,0)` means "no motion", not "I don't know". `n_null = 0` by construction, on every input including pure noise. | **YES** |

### C1 — THE CROSS-CUTTING PREDICTION (mechanism-independent)

`shape_decode.rs`'s `select_field` returns `Value::None` for a field absent from
the returned dict, and `ShapeDecode`'s two refusal walls carry only
`authored`/`reason`.

> **C1: a `field:"explained"` read of a WALLED `ShapeDecode` returns `None`, not
> `False`.** Therefore a seed rule of the shape
> `Not(Eq(ShapeDecode{…, field:"explained"}, true))` behaves differently from
> one testing `Eq(…, false)`, and **a structured refusal is ERASED to a bare
> shrug at the field boundary.** If confirmed, refusal capacity present at the
> Term boundary is **not** refusal capacity available to the graph — which would
> be a defect in the plumbing every Group-1 mechanism shares.

**A null means:** C1 is false, `select_field` preserves the verdict, and the
Group-1 refusals are usable by rules as measured. That is a perfectly good
result and will be reported as one (§7).

---

## 5 — EXACTLY THE TESTS TO BE RUN. NO SWEEPS. NO RE-RUNS.

1. **G-arm** (deterministic, 0 seeds): every mechanism × degenerate input. Record
   whether the null fires and its `checked`.
2. **A-arm** (deterministic, 0 seeds): every mechanism × its best-case
   explainable input. Record acceptance. **A mechanism failing A is DEAD and is
   reported as such.**
3. **Δ-arm** (seeds 106000–106199): 200 matched `(E, U)` pairs per mechanism,
   guard-visible properties held identical. Record Δ with Wilson CI.
4. **DepthInfer two-layer arm** (seeds 106200–106399): the P2 construction.
5. **BlinkBridge gap arm** (seeds 106400–106599): the P3 construction, gap ≥ 1.
6. **C1 arm** (deterministic, 0 seeds): field-selection on a walled refusal.
7. **Cost arm**: `checked` and wall-time, both arms, every mechanism.

A further attempt needs a NEW pre-registration with a NEW mechanism-level
hypothesis — never a parameter search.

## 6 — WHAT A NULL MEANS

- **All mechanisms EARNED** ⇒ the through-line is about three specific
  mechanisms, not about the eye, and the brief's premise is over-generalised.
  Reported as a negative (§7), and it would be the most useful outcome for the
  ladder.
- **Δ = 0 everywhere** ⇒ either the stimulus construction failed (caught by the
  A-arm) or the matched-pair design is not matched (caught by the G-arm).
- **A-arm failures** ⇒ DEAD mechanisms, reported first-class and NOT folded into
  the refusal classification.

## 7 — §13

No number enters this rung. Every verdict is read from the engine as an exact
value (`explained`, `authored`, `reason`, `Value::None` identity); Δ is a
difference of proportions with a Wilson CI, and the CI is the only inferential
object. **There is no threshold anywhere in the classification rule** — rows a–f
are decided by exact counts and CI overlap, and there is nowhere to put a
tolerance.

## 8 — SCOPE

- These are TERM-level mechanisms. Nothing here measures the seed-rule layer's
  refusals directly; it BOUNDS them from below.
- Stimuli are SYNTHETIC cell sets and dot sequences, not natural images. A
  mechanism that refuses correctly here may not on natural input.
- `n = 200` pairs bounds Δ to roughly ±7pp at worst; a true |Δ| below that is
  not resolvable by this rung.
- Classification is per (mechanism × stimulus family). A Term with no
  explainable stimulus in this family is DEAD **here**, not in general.
