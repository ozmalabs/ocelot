# Pre-registration — does the burst-latency mechanism make the agent sensitive to temporal order?

*Written 2026-07-16, BEFORE the confirmatory run. Fixed in advance; deviations must be
recorded as deviations.*

## Why a pre-registration exists for this

Three prior attempts produced a small ordered-vs-shuffled difference that repeatedly
failed to survive scrutiny: an n=60 p=0.013 that did not replicate; a p=0.0016 whose
own control (a condition with **no temporal mechanism at all**) showed the same effect;
and ~15+ comparisons run across windows × burst-durations × scaling states with the
significant ones reported — a forking-paths garden. Two further errors were found in
the analysis itself:

1. **Wrong test.** The simple effect (ordered vs shuffled) is confounded: the
   no-mechanism control is not null, so a simple-effect difference cannot be
   attributed to the mechanism. **The test must be the INTERACTION.**
2. **Wrong unit of analysis.** Units within a run share one movie and compete under
   winner-take-all, so they are not independent. Reporting n=80 *units* inflated every
   p-value. **The unit of analysis is the SEED.**

## Hypothesis

**H1 (two-sided):** the temporal mechanism changes the agent's sensitivity to the
temporal order of its own waves, relative to an otherwise-identical agent with no
temporal mechanism.

Two-sided deliberately: the predicted direction has been wrong twice already
(orientation ↑ failed; refinement ↑ failed), so a directional prediction is not
credible here.

**H0:** interaction = 0 — the mechanism adds nothing to temporal-order sensitivity.

## Design (2×2, fully within-seed / paired)

- **Factor A — mechanism:** `OFF` = `window_steps=0 ∧ unit_burst_steps=1` (both sides
  instantaneous: the true no-temporal-mechanism condition). `ON` = `window_steps=2 ∧
  unit_burst_steps=3` (pre-side latency window + post-side burst duration).
- **Factor B — order:** `ordered` = the wave movie as generated; `shuffled` = the SAME
  frames, temporal order destroyed. Spatial marginals identical by construction.
- All four cells use the **same movie** within a seed (paired), removing
  movie-to-movie variance.
- Everything else fixed: 16×16 retina, 10 units, rf=7, 200 frames, `propagate=0`
  during replay, homeostasis ON in all cells.

## Test statistic

Per seed *i*:

```
d_ON_i   = mean_anisotropy(ordered, ON)_i  − mean_anisotropy(shuffled, ON)_i
d_OFF_i  = mean_anisotropy(ordered, OFF)_i − mean_anisotropy(shuffled, OFF)_i
interaction_i = d_ON_i − d_OFF_i
```
Each cell value = the mean anisotropy over that run's 10 units.

**Test:** one-sample, two-sided **sign-flip (randomisation) test** on
`{interaction_i}`, 20,000 permutations, α = 0.05. Reported with a bootstrap 95% CI.

## Sample size — FIXED IN ADVANCE

**n = 80 seeds.** From a pilot on exploratory seeds 0–5 (variance estimate only, no
test): per-seed SD of the interaction = **0.133**. n=80 gives ~80% power at α=0.05
(two-sided) for |δ| ≈ 0.042, and ~90% for |δ| = 0.05. The exploratory point estimate
was ≈ +0.031–0.052; n=80 is therefore adequate for the upper part of that range and
**underpowered for δ ≈ 0.03 — which is stated in advance**, so a null must be reported
as "no effect detected at this power", not as "no effect exists".

## Seeds

**Confirmatory seeds: 100–179.** Never used for anything: all exploration used seeds
0–13, and the pilot used 0–5.

## Decision rule

- **PASS** iff p < 0.05. The sign of the interaction is then reported as observed
  (two-sided: either direction is a real finding about the mechanism).
- **FAIL** otherwise → *the temporal mechanism is not demonstrated to affect
  temporal-order sensitivity at n=80*, and the latency axis + post-side extent are
  scaffolding with no earned result.

## Analyses permitted

**Exactly one hypothesis test: the interaction above.** Nothing else.

The four cell means and the two simple effects may be reported as **descriptive only**,
explicitly labelled non-inferential. **No** window sweeps, **no** additional
mechanism variants, **no** re-running with different n, **no** post-hoc measures
(concentration/sparsity or otherwise). If this fails, the next step is a *new*
pre-registration, not another pass over these data.

## Sanity check (not a hypothesis test)

`d_OFF` is expected to be non-zero (the no-mechanism condition already showed
ordered≠shuffled, most likely path-dependence in winner-take-all under contiguous
input). That is exactly why the interaction — not the simple effect — is the test.

---

# OUTCOME (run 2026-07-16, exactly as specified above)

```
INTERACTION (d_ON − d_OFF): +0.0532   95% CI [+0.0296, +0.0763]   p < 0.0001
n = 80 seeds (100–179), 20,000 sign-flips, two-sided
```

## **DECISION: PASS.**

The temporal mechanism (pre-side latency window + post-side burst duration) **does**
change the agent's sensitivity to the temporal order of its own waves. The effect is
positive: with the mechanism on, temporally-ordered waves produce more anisotropic
receptive fields than the same frames shuffled.

**Descriptive only (NOT tests), reported as pre-committed:**

| cell | mean anisotropy |
|---|---|
| ordered, mechanism ON | 0.343 |
| shuffled, mechanism ON | 0.276 |
| ordered, mechanism OFF | 0.322 |
| shuffled, mechanism OFF | 0.308 |

- simple effect with mechanism **ON**: **d_ON = +0.068** (SD 0.071)
- simple effect with mechanism **OFF**: **d_OFF = +0.015** (SD 0.069) — **near null**
- per-seed interaction SD **0.108** (pilot predicted 0.133 ⇒ slightly *more* power than
  planned; no deviation, n was fixed at 80 regardless)

**No deviations from the plan.** One test, as specified. No sweeps, no post-hoc
measures, no re-runs.

## What this resolves — and what it does not

**Resolves:** the exploratory 2×2 had suggested the no-mechanism control was NOT null
(d_OFF = +0.063, p=0.054), which is what killed the previous attempt. That was an
artifact of the two analysis errors this pre-registration was written to fix —
counting non-independent units as n=80, and n=8 seeds. Analysed correctly (paired,
seed as unit, n=80 fresh seeds), **d_OFF = +0.015 is essentially null and the
interaction is solid.** The mechanism creates the order-sensitivity; it does not ride
on a pre-existing one.

**Does NOT resolve — and must not be read as:**
- **Not** "orientation emerges." ordered-ON anisotropy is 0.343 against an ideal
  Gabor's 0.867 — *partial structure*, and no orientation *map* is demonstrated.
- **Not** a claim about which biological mechanism is correct. The verified research
  refuted 0-3 the Hebbian-vs-sparsity question; this shows only that *this*
  implementation of the Butts latency geometry produces temporal-order sensitivity in
  *this* substrate.
- The effect is small (~0.05 on a 0–1 scale) and was **undetectable** in every
  underpowered, mis-analysed pass that preceded it. That is a statement about the
  earlier method, not a licence to inflate this result.
