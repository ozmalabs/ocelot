# RUNG 5 — the transport residual is ONE-SIDED, and zero capability means UNMEASURED

**Status:** registered 2026-08-10, before the run. Rung 3 (`9d068551d2`) and
rung 4 (`b1a6280861`) are committed; Block 0's 8-run null is `first_fall_action`
201 / `directed_progress` +0.09524 / `com_min` 0.1262, 8/8 identical.

## The diagnosis

Rung 3 fixed loss of upright and lost travel: `directed_progress`
+0.09524 → −0.01574, 43 support alternations going nowhere. The term is

```
residual = (predicted_translation − energy × capability_rate) / height
cost    += residual²
```

Two structural facts, both measured, not inferred:

1. **`translation_per_joule` seeds at `0.0`**
   (`gen_embodied_motor_priors_seed.py:698`) and is learned by EMA from
   observed travel. At rate 0 the term reads: *any* predicted translation is an
   error of exactly that magnitude. The body declines to translate; the EMA
   therefore observes no travel; the rate stays 0. **The loop is
   self-confirming**, and 600 actions of stepping in place is what it looks
   like from outside.

2. **The residual is SYMMETRIC.** Travelling further than the estimate is
   punished exactly as hard as falling short. A body that could outperform its
   own prior is penalised for doing so — the F-16 arc's *"a surrendered axis is
   scored a flat 0.0 while a kept axis is scored unbounded-below, so the corner
   that gives up the most wins"* (`regime_pareto_frontier_results.md`), here in
   algebraic form.

**And the guard is the wrong guard.** `matched_capability_translation_per_joule`
returns `Option`, so *absent* capability disables the term — but a node
carrying `0.0` is PRESENT, and applies at full strength. "Never measured" and
"measured as incapable" are the same value. This is the `P0` absent-vs-zero
conflation (`612f04164d`) one level up, in the semantics rather than the
arithmetic.

## The change

The residual becomes **shortfall-only**: charge when the plan predicts LESS
translation than the capability says that energy buys, and charge nothing when
it predicts more. Cost of transport is about not wasting energy; the error is
"spent energy, went nowhere," not "went further than expected."

At rate 0 this is **inert by construction** — capability_translation is 0,
predicted translation is ≥ 0, so there is no shortfall — which breaks the
bootstrap loop without needing an evidence guard at all. Nothing is gated on
`experience_count`; the algebra disarms itself.

## Registered predictions

1. **`directed_progress` rises above rung 3's −0.01574.** This is the point of
   the change. If it does not, the transport term was not what suppressed
   travel and the diagnosis above is wrong.
2. **It does NOT reach Block 0's +0.09524 by itself.** Block 0 travelled by
   falling forward (fall at 201, 144 aerial actions). A body that stays upright
   and travels is a different solution, not a restored one, and I do not
   predict this term alone produces it.
3. **Upright is RETAINED** — `first_fall_action` stays None, `com_min` stays
   near 0.8379. The change only removes a penalty; it adds no incentive to
   fall. If upright is lost, the term was load-bearing for posture in a way not
   understood here.
4. **`bounded_lateral_drift` is NOT predicted to recover.** Lateral drift
   (−0.2346) has no term addressed by this change.
5. **Cost falls or is unchanged** in CPU-seconds against rung 3's 7,044. The
   change removes work (a branch that skips the squaring), and if the body
   spends less time in double support the simulator does less contact solving.

## What would falsify it

* **Prediction 1 fails** — travel stays at or below −0.0157. Then the
  suppressor is elsewhere among the nine terms, and the honest next step is the
  per-term decomposition this prereg does not build (see below).
* **Prediction 3 fails** — the body falls again. Then upright in rung 3 was
  bought by the symmetric penalty specifically, and the two are not separable
  the way this change assumes.
* **Both 1 and 3 hold but `directed_progress` gates False anyway.** A dimension
  can improve without passing; report the number, not the gate.

## Declared limits

* **n = 1**, justified only by Block 0's 8/8 determinism. Rung 3 and rung 4
  landed 1 CPU-second apart on identical metrics, so the machinery is
  deterministic; the *protocol* being an easy subset is a separate question this
  does not address.
* **The per-term decomposition is still unpaid.** `CONTACT_WRENCH_PREREG.md`
  committed to *"report per-term contributions; a measure with one live
  component has replaced one category with another"*, and the nine terms are
  still summed and never individually published. This rung acts on a diagnosis
  of ONE term without having measured the other eight. That is a real weakness
  and it is why prediction 1 is stated as a falsifier rather than an
  expectation.
* **This does not make the body walk.** It removes a penalty on travelling. The
  fixpoint problem — a flat scalar objective having exactly one optimum,
  measured independently on the F-16 as *"THE FRONTIER HAS STOPPED CHOOSING"* —
  is untouched by anything here.
