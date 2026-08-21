# Decision layer — preregistration: non-mutating proposal construction, then feasible-set selection

**Status: preregistration. No code written for either stage.** This document fixes what
would be built, in what order, what each stage must measure, and what result would make me
stop. It is written before the work so the GO/NO-GO conditions cannot be chosen after
seeing the numbers.

## 0. Why one document for two rungs

The gap review (`docs/research/theory_convergence/GRAPHIC_EQUALISATION_V22_SUBSTRATE_GAP.md`)
lists these separately. They are not independent:

> feasible-set selection is not merely absent as an optional layer (which would be
> compliant) but **structurally unbuildable on top of the current `run_rules`** without
> first fixing the mutate-during-derivation behaviour in `rewrite.rs`.

Selection over a *set* of candidate outcomes presupposes candidates that exist before any
of them is applied. Today the applier mutates the graph per binding and undoes on
no-progress (`rewrite.rs:2196-2207`), and `batch_apply_rule` documents that same-round
bindings observe each other's writes (`:2460-2464`). There is nothing to select *among*.

So: Stage A is a prerequisite, Stage B is conditional on Stage A landing, and there is a
NO-GO gate between them. Sizing them jointly is the honest framing; sizing them separately
would hide the dependency.

---

## 1. What is already measured, and what it does and does not license

Three measurements exist. They are what makes this prereg worth writing now rather than
speculatively.

| measurement | value | source |
|---|---|---|
| selector tie rate, conversational workload | **95/148 = 64.19%** | `ARGMIN_TIE_CENSUS_RESULTS.md` |
| dominant tied site | 90/90, ranks by a hardcoded `salience: 1.0` | ibid., §CORRECTION |
| failed-effect path, same workload | **0 firings** | `effect_audit`, this document §4 |
| Rust unit suite, parallel | 787/787, 8 consecutive runs | `5b57272` |

**What the tie rate licenses:** that order-decided outcomes are common, not hypothetical,
on at least one real workload. That is the case for SET-TIE semantics being worth
specifying.

**What it does not license:** any claim that the ties are producing *wrong answers*. The
instrument counts exact non-uniqueness, not incorrect outcomes. At the dominant site
nothing is ranking, so order decides — but no downstream error has been shown. A rung that
justifies itself by "64% of decisions are broken" would be overstating the evidence, and
this prereg does not.

---

## 2. Stage A — non-mutating proposal construction

### A.1 What would change

`run_rules` derives against an immutable base and produces a proposal, rather than
applying-then-maybe-undoing per binding.

- A `Proposal` value: the accumulated effects of a pass, before application.
- Matching reads a base snapshot plus completed positive proposal facts, never
  same-round writes.
- One application boundary per pass instead of per binding.

The theory's own construction (v22 §`run_rules`) additionally requires monotone positive
accumulation, stratified removal, freshness stratification, and a defined merge
incompatibility relation. **Stage A adopts only the immutability and the single
application boundary.** The rest are Stage B's problem or later; adopting them here would
make the stage unfalsifiable in one step.

### A.2 The prerequisite that already exists

`UndoStep` (`rewrite.rs:930`) is already an inverse-edit list computed on the probe path
and discarded. It is the natural delta carrier and it is already correct enough to roll
back a firing. Stage A is closer to *keeping* something already built than to building it.

### A.3 What Stage A must measure

1. **Regression:** Rust unit suite 787/787 parallel, and the migrated Python bench slice
   used as the guard, both unchanged. Non-negotiable.
2. **Semantic delta:** the number of rule firings whose outcome differs from the committed
   behaviour. Expected non-zero — same-round visibility is load-bearing somewhere in 634
   rule-carrying seeds — and every difference must be enumerated, not summarised.
3. **Fixpoint iterations:** per-pass iteration counts before and after. Removing
   apply-then-undo should reduce wasted passes; if it *increases* them, the model is wrong.

### A.4 NO-GO conditions, fixed now

- Any semantic delta that cannot be enumerated rule-by-rule. A count is not an enumeration
  (this repo's own retracted-baseline lesson).
- More than **20** rules whose behaviour changes. Above that the change is a seed-corpus
  migration wearing an engine change's clothes, and it needs its own prereg.
- Any regression in the 787 that is not itself a pre-existing flake, demonstrated by
  reverting.

---

## 3. Stage B — feasible-set selection and SET-TIE

**Conditional on Stage A landing.** If Stage A is NO-GO, Stage B does not start.

### B.1 What would change

- A feasible family over *subsets* of ready candidates, with joint admissibility — the
  theory's point that pairwise compatibility is necessary but not sufficient.
- A represented valuation frozen at epoch opening.
- `argmax` over the family; a non-unique maximum is a **represented SET-TIE**, not a
  first-wins pick.

### B.2 What already exists and must not be rebuilt

- `argmin_tie.rs` already implements exact non-uniqueness detection with **no epsilon**,
  and `ArgminUnique`/`ArgminRefusal` already refuse. What is missing is that a refusal
  returns `Value::None` rather than a represented tied set, and that it is opt-in per
  Term.
- `admissible_moves` (`substrate.rs:1887`) already enumerates a Γ-admissible set with
  additive weights.
- `future_manifold::reachable_deformation_set` (`e636daa`) already returns a candidate set
  as records rather than a score.

### B.3 What Stage B must measure

1. The tie rate under set-level selection, on the same workload as the census, so the
   figures are comparable.
2. **How many SET-TIEs are terminal** — i.e. how often the boundary makes no progress
   because a tie cannot be broken. The theory permits indefinite blocking; a system that
   deadlocks in practice is a different result from one that ties rarely.
3. Whether refusing on non-uniqueness reproduces the committed bench. `argmin_tie`'s
   `refuse_min`/`refuse_all` modes exist precisely to answer this and **have never been
   run** — that measurement is cheap and should precede any building.

### B.4 NO-GO conditions, fixed now

- If `refuse_all` on the current engine shows that refusing ties breaks a large fraction of
  the bench, the seed corpus depends on order-decided outcomes far more than the census
  suggests, and the honest response is to report that and stop — not to build selection on
  top of a corpus that needs the old semantics.
- If terminal SET-TIEs exceed **5%** of boundary epochs on the census workload, the
  selection layer is a liveness hazard and needs a represented tie-resolution rule before
  it is worth having.

---

## 4. Cheap measurement to run BEFORE either stage

Two measurements would sharpen this prereg and neither requires building anything:

1. **`refuse_all` against the bench. RUN — and the result is decisive.**

   | mode | firings | ties | refusals | replies differing |
   |---|---|---|---|---|
   | `count` | 148 | 95 | 0 | — |
   | `refuse_all` | 64 | 36 | **36** | **0 of 5** |

   Refusing every non-unique extremum produced **byte-identical replies** on the census
   workload. Firings drop 148→64, so the run genuinely takes a different internal path —
   36 selections refused outright, and downstream rules that depended on those winners
   never fire — and the observable output does not move.

   **B.4's first NO-GO is therefore not triggered, and §5's falsifier is supported.** On
   this workload the ties are not consequential: nothing downstream depended on which
   tied candidate won. That is evidence *against* the value of Stage B, not for it, and
   it was obtained for the cost of running a mode that already existed.

   Limits, stated because the result is strong enough to be over-read: five replies, one
   workload, conversation paths only, and reply-equality is a coarse equivalence — the
   firings delta proves internal state differs even where output does not. It shows no
   observable difference on this workload, not the absence of difference.
2. **`effect_audit` across a rule-heavy slice. RUN — clean.** 47 tests across
   `quanta_navigation`, `gap_awareness`, `elaboration`, `dimension_inference` and
   `transform_decode`, 5m34s, all passing:

   ```
   failed_edge_inserts: 0
   false_progress     : 0
   first_row          : null
   ```

   Zero on both the conversational workload and this rule-heavy slice. The
   discarded-`Result` path at `rewrite.rs` does not fire in practice, so the correction —
   withholding `progressed` and the undo step on a failed insert — costs nothing to
   enable. Enabling it removes a source of spurious fixpoint iteration *before* Stage A
   tries to measure iteration counts, which is the right order: otherwise Stage A's
   headline number would carry a known contaminant.

   This does not prove the path is unreachable. It has a constructed red test
   (`rewrite.rs::effect_audit_tests`) proving it fires on real machinery when an earlier
   effect deletes an endpoint. It proves no exercised seed rule does that today.

Both are hours, not weeks, and both could change what this prereg says. That is the point
of running them first.

---

## 5. What would falsify the premise of this document

That the decision layer is worth building at all rests on order-decided outcomes being
*consequential*. The census establishes they are *common* and explicitly does not
establish they are consequential.

**If a follow-up shows that the 64% of ties are overwhelmingly between genuinely
interchangeable candidates — as the corrected dominant site now looks, five episodes all
minted with the same literal salience — then the right rung is not a selection layer at
all.** It is fixing the rules that rank by constants, which is a seed-data change costing
days rather than an engine change costing weeks.

That possibility is no longer merely likely: **the `refuse_all` run in §4 supports it
directly.** Refusing all 36 ties changed no reply. If a broader slice reproduces that, the
selection layer is solving a problem this corpus does not have.

**RETRACTION, same session.** This paragraph originally continued: *"and the rung to run
instead is fixing rules that rank by constants — a seed-data change costing days rather
than an engine change costing weeks."* That recommendation rested on a single instance and
**does not survive a census of the corpus**
(`CONSTANT_RANKING_SELECTOR_CENSUS.md`): of 1491 selectors, the 68 literal-ranked ones are
a deliberate "pick any element" idiom, **zero** rank an attribute that every writer sets
literally, and the 8 ranking attributes no seed rule writes are all written by world
adapters and at least one discriminates correctly. The `salience` case is path-dependent
rather than structural, and therefore not statically detectable at all. There is no
constant-ranking rung to run. The measurement that would actually extend this finding is a
*runtime* tie census across non-conversational workloads — hours, not days. Stage A is defensible on its own terms
regardless (immutable derivation is correctness, not optimisation). Stage B is not yet
justified by measurement, and this prereg does not claim it is.
