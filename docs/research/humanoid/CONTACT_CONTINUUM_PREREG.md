# CONTACT IS A WEIGHT, NOT A STATE — prereg

> ## SUPERSEDED 2026-08-09 by `CONTACT_WRENCH_PREREG.md` — BEFORE ANY OF IT RAN
>
> This document treats **support load** as the continuum that replaces the
> category. That is right as far as it goes and it does not go far enough: load
> is ONE SCALAR PROJECTION of the real object. Measured after this was written:
>
> * **Direction is thrown away too.** Every contact publishes `normal_on_b` plus
>   two friction directions and magnitudes, and NOTHING in the tree consumes any
>   of them. Against a flat floor all 228 sampled normals are vertical — a
>   tautology, not evidence — but against the desk box **2 of 2 contacts are
>   non-vertical** (30-60 deg and 60-120 deg), on ARM links the support path does
>   not look at.
> * **Support is not always compression.** A body hung from a constraint is
>   fully held (reaction 400.68 N ~ body weight) and `getContactPoints` reports
>   **ZERO contacts**; `normal_force` is never negative. A sucker pad or a hook
>   has no expressible form as a contact here at all.
> * **The supported set is not the feet.** `_support_link_indices` is literally
>   `distal_links[:2]`, and `_support_code` RAISES on any body that is not
>   bipedal.
>
> So replacing the category with a scalar load would have fixed one projection
> and left three. The successor states the object directly: a contact is a
> DIRECTION, a MAGNITUDE and an ADMISSIBLE WRENCH SET.
>
> Everything measured below remains valid and is carried forward. The site
> enumeration in particular is still correct and still binding — it is why the
> first attempt failed. **This file is kept as the record of a reframe that was
> superseded before it was built, not corrected after it shipped.**


**Status:** design recorded, nothing built. Registered 2026-08-09 before
implementation so the gates below cannot be chosen after seeing results.

A first attempt was made and REVERTED before this document existed; §7 records
what it was and why it does not count as evidence either way.

## The claim

**There is no dichotomy. Moving on the ground is still moving in the air, just
sitting on the ground.** The dynamics do not switch at touchdown: a body is
always moving under gravity plus whatever contact force exists, and standing is
the degenerate case where contact happens to cancel gravity. Contact is a
continuously varying load, and every representation that makes it a category
destroys the quantity that actually distinguishes the situations.

## What is already measured

All of the following is measured on this tree, before any of the work below.

**The load is a continuum.** Total support load over a 600-action walk spans
0 to 3.26 body weights with **15 of 20 histogram bins occupied**. The discrete
labels overlap almost completely:

```
                        n     total load / mg:  min     med     max
  double_support       174                     0.853   1.021   2.875
  support_0            174                     0.022   1.017   2.172
  support_1             88                     0.011   0.994   3.259
  aerial               164                     0.000   0.000   0.000
```

A foot bearing **0.011 mg** is mechanically in flight and is labelled single
support; the same label reaches **2.172 mg** on impact.

**The encoder is a threshold at zero.** `_support_code` returns 1 or 2 for
exactly one foot loaded and **0 otherwise** — so `(True, True)` and
`(False, False)`, the two opposite extremes, share a label. It is infinitely
sensitive at `force > 0` and blind everywhere else.

**The tracker is flawless, and that is the point.** `current_support_phase`
matches the true contact code on **600/600 actions, zero disagreements**. There
is no tracking bug to fix. 24 flight actions were nonetheless filed alongside
468 double-support actions under phase 0. The categories destroy the information
while every mechanism that maintains them works perfectly.

**The continuous metric already exists and already excludes contact.**
`motor_compose.rs::context_distance` is a nondimensionalised sum of squares over
attitude, angular rate, three velocity components and lateral offset — **nothing
in it is contact-conditional**, which is exactly the claim above expressed in
code. It is then confined by `peer.support_phase == model.support_phase`, a hard
categorical filter layered over a continuum metric that was already doing the
work.

**Balance does not stop in the air.** The composer's attitude term
(`predicted_zx² + predicted_zy²`) and both lateral terms run unconditionally;
only `support_preview` is contact-gated, correctly, because a support polygon
genuinely does not exist in flight. So the failure is not that nothing weighs
attitude while airborne — it is that model selection cannot see the regime
changed, and answers "what will this joint do to my attitude" from statistics
gathered with both feet planted, for 27% of a run.

## The design

Replace the categorical bucket with the quantity it thresholds.

1. **`context_distance` gains a load term**, nondimensionalised by body weight
   exactly as velocities are by `velocity_scale` and lateral offset by `height`:
   `(anchor_support_load − (state_support_0_force + state_support_1_force)) / (body_mass·g)`.
2. **The `support_phase` equality filter is removed** from model activation, so
   the metric may rank a 0.011 mg context against a flight context directly.
3. **`anchor_support_load` is captured with the other anchors**, from the
   outcome's `pre_support_{0,1}_force`, at the moment a context grounds.

A body publishing no support forces reads 0 on both sides and the term
contributes nothing, so this is inert wherever contact is not a meaningful
quantity.

### THE SITE ENUMERATION IS PART OF THE DESIGN

The reverted attempt failed because it was partial. The distance metric is
computed in **two languages** and the anchors are written by **four rules**; a
change to any subset leaves the deciding path and the graph-side path
disagreeing. Every site, enumerated so a partial migration cannot recur:

| # | site | what |
|---|---|---|
| 1 | `motor_compose.rs::context_distance` | Rust metric — add load term |
| 2 | `motor_compose.rs` activation loop | remove `support_phase` filter |
| 3 | `motor_compose.rs` model cache key | add `anchor_support_load` or the anchor never invalidates |
| 4 | `gen_humanoid_adaptation_seed.py:~236` | graph-side distance mirror |
| 5 | `gen_humanoid_adaptation_seed.py:~303` | graph-side distance mirror |
| 6 | `gen_humanoid_adaptation_seed.py:~4206` | graph-side distance mirror (`PI0` variant) |
| 7 | `ha_specialize_surprising_support_phase_context` | anchor write |
| 8 | `ha_learn_support_phase_consequence_online` | anchor write |
| 9 | `ha_select_learned_walking_primary` | anchor write |
| 10 | `ha_reground_invalidated_local_phase_prediction` | anchor write |
| 11 | seed `support_phase` filters (~400, ~464, ~1292) | the same bucket, graph-side |

**A run against a partial set measures the partiality, not the hypothesis.**
The reverted attempt covered 1, 2, 3, 7, 8 and produced a 42-minute measurement
of a bias it had introduced.

## BLOCK 0 — ESTABLISH THE NULL DISTRIBUTION FIRST

**Nothing below may be attributed until this is done.**

> **CORRECTED 2026-08-09: the motivating figure here was WRONG.** This section
> claimed "two runs of the SAME protocol produced 164 and 24 aerial actions".
> They are not comparable measurements: **164** is a count of trace rows with
> `support_pattern == "aerial"` (recorded AFTER each action), **24** is a count
> of episode reads with neither support force loaded (sampled at the TOP of the
> loop, before the action). Different sources, different sampling points. The
> figure establishes nothing about determinism, and I quoted it as if it did.
>
> No clean same-protocol repeat measurement exists yet. Block 0 is therefore
> still REQUIRED — not because nondeterminism is established, but because it is
> UNKNOWN, and a before/after pair means nothing until the spread is known.

Protocol: run the unmodified experiment **N ≥ 8 times**, changing nothing.
Report per-run `first_fall_action`, `directed_progress`, `lateral_offset`,
`aerial_samples_per_locomotor_cycle`, `support_alternations`, and the five
evaluation flags. Establish the spread of each.

**If the source of the 164 vs 24 spread is found and removable, remove it before
proceeding** — a deterministic instrument is worth more than any result measured
on a noisy one. If it is irreducible, Block 0's spread becomes the yardstick and
every later claim must clear it.

At ~43 min per run under the change (~16 min without), this is the dominant cost
of the whole arc and is not optional.

## Registered predictions

1. **Grounded behaviour changes.** Unlike the F-16's "seven scenarios
   byte-identical" blocks, nothing here will be byte-identical: removing the
   filter changes which model is active on **every** action, double support
   included. A run that reproduces the baseline exactly means the change did
   not reach the deciding path.
2. **Aerial actions get their own nearest contexts.** After the change, the
   context selected during flight must differ from the context selected during
   double support at comparable attitude and velocity. This is the mechanism,
   and it is checkable directly by instrumenting the selected `context_id`
   against the live load — **cheaper than any behavioural run, and it should be
   measured first.**
3. **`bounded_lateral_drift` stays fixed.** It was fixed by the balance term
   (commit `65b8eb9def`) and is independent of model selection. If it regresses,
   the change is reaching further than intended.
4. **Direction on `upright` and `bounded_aerial_occupancy` is NOT
   preregistered.** The hypothesis is that flight contexts stop being answered
   with ground statistics; whether that is enough to keep a body upright is not
   claimed. "Still falls" does NOT falsify the representation claim.
5. **Performance regresses and must be recovered.** The removed filter was a
   ~3× prefilter on both the outer skip and the inner peer scan; measured 2.7×
   slower end-to-end (956 s → 2572 s) in the reverted attempt. A per-token
   candidate index, or any equivalent, must restore this before the change
   lands. **A correct change that triples the cost of every experiment in the
   tree is not landable.**

## What would falsify it

* **Prediction 2 fails.** If flight and double-support states still select the
  same contexts once load is in the metric, then load does not separate them and
  the categorical filter was not what was discarding the information. This is
  the decisive test and it is cheap.
* **The metric is dominated by the new term.** If load's squared error swamps
  attitude and velocity (load/mg ranges over 0–3.26 while the others are O(0.1)),
  selection becomes contact-matching with the rest as noise. Report the per-term
  contributions; a term that dominates has replaced one category with another.
* **Block 0 shows the spread exceeds any effect.** If the null distribution of
  `first_fall_action` covers the whole range observed, no realistic N can
  attribute a change and the behavioural claim must be abandoned in favour of
  the mechanism claim (prediction 2) alone.

### Named in advance: the most likely falsifier

**That the models are keyed by `context_id` and the buckets were never the
binding constraint.** Model activation is one-per-token, and if `context_id`
already partitions contexts finely enough that same-token cross-phase
comparisons never actually change the winner, then removing the filter is a
no-op dressed as a fix — and the 2.7× cost buys nothing. Prediction 2 tests
exactly this and must be run before any of the rest.

## Honest scope, declared in advance

* **This does not claim to make the body walk, or to keep it upright.** It
  claims that flight contexts should stop being answered with ground statistics.
  Gate 7 of `EFFECTOR_COMPENSATION_PREREG.md` remains unanswered and is not
  addressed here.
* **`_support_code` itself is not changed.** The enum stays (other consumers
  read it); the claim is that model SELECTION must not be gated on it. Removing
  the enum entirely is a larger change and is not proposed.
* **One body, one protocol, one asset.** Nothing here establishes anything about
  bodies with different sensor counts, and `support_load()` sums exactly two
  sensors because this body has two.
* **The load term's form is one monotone choice among many.** A squared
  nondimensionalised error matches the existing terms; it was not selected
  against alternatives, and per the F-16's generalisation — *"every value that
  held was a declared ratio; every value that failed was a rule inferring what
  should have been declared"* — if a weight is needed on this term it must be
  DECLARED by the operator, not tuned into the metric.

## §7 — the reverted attempt, recorded so it is not repeated

Attempted 2026-08-09, reverted the same session. Covered sites 1, 2, 3, 7, 8 of
the eleven above; left the three graph-side distance mirrors and the three
graph-side filters inconsistent with the Rust path.

Measured `anchor_support_load` present on only **41 of 162 models**, so every
unanchored model compared 0 against a live load of ~400 N and carried a constant
`(400/392)² ≈ 1.04` penalty — **a systematic bias against unanchored models with
nothing to do with contact.** The 42-minute walking run taken on it moved the
gate from 2 differing flags to 3 and is NOT evidence about the hypothesis; it
measured the bias.

The engine rebuild is cheap and is not a blocker: `CARGO_BUILD_JOBS=4 maturin
build --release` completed in **1m20s** warm, and the F-16 worktree carries its
own `.so`, so its 50 green tests are unaffected until the change is deliberately
ported. `motor_compose.rs` is otherwise byte-identical across the two branches
and any change here should be assumed to be a change there.

The lesson the attempt paid for, which is the F-16 thread's own
(`7099c47402`, `§74 patched five filters without establishing which decided`):
**enumerate every site that computes the thing before changing any of them, and
verify the change is live before measuring its effect.**
