# Two compressions, not one — and they need opposite cures

Follow-up to `STRESS_COMPRESSES_APERTURE_RESULTS.md`, which is conditioned in place by this.

Not a pre-registered experiment, and it should not be dressed as one: the predictions follow
directly from code written in the preceding rungs, so this is **verification of a conditionality**,
not a discovery. It is recorded because it limits a claim already published.

## The two models

| | **A — dimensional** | **B — temporal** |
|---|---|---|
| what stress does | removes a dimension you could resolve | shortens how far ahead you can audit |
| where it comes from | **stipulated** — something must supply the mask | **derived** — the projection budget is a represented resource |
| measured deficit | `information_loss` > 0, `resolved` = 0 | `information_loss` > 0, `resolved` = 0 |

From the outside they are the same deficit, which is why they were conflated.

## Measured

Escape at t=3 in dimension 1; horizon 3.

| arm | budget | `loss` | `information_loss` | `resolved` | `retained_width` |
|---|---|---|---|---|---|
| healthy | 8 | **1** | 0 | 1 | 1 |
| A — blind to d1 | 8 | 0 | 3 | 0 | **1** |
| B — budget 1 | 1 | 0 | 4 | 0 | **0** |
| B — budget 2 | 2 | 0 | 2 | 0 | 0 |
| **B — budget 8** | 8 | **1** | **0** | **1** | 1 |
| **A — budget 64** | 64 | 0 | **3** | **0** | 1 |

**Two discriminators, neither needing an intervention:**

* **`retained_width`.** A blinds one dimension and leaves the others genuinely established (`1`).
  B establishes *nothing* (`0`), because retention over the requested horizon is unknowable once any
  tick in it went unaudited.
* **Gradedness.** B's `information_loss` moves with the resource — 4, 2, 0 as budget rises. A's is
  flat at 3 across 8, 16, 64. **A deficit that responds to a resource is a resource deficit**; that
  is what makes B the derivable model.

## What this conditions

`STRESS_COMPRESSES_APERTURE_RESULTS.md`'s headline — *evidence at 42× the horizon does not move a
compressed agent* — is **a property of model A**, which that rung stipulated. Under model B the same
gate recovers completely: at budget 8 the agent resolves and sees the escape it was blind to at
budget 1.

The result is not wrong and is not retracted. What is wrong is reading it as *"stress makes evidence
inert"*. It shows that **dimensional** compression makes evidence inert. Whether stress is
dimensional, temporal, or both is **not established**, and the substrate cannot currently say,
because neither model is derived — A is a stipulated mask and B is a stipulated budget.

## Why this is useful rather than merely deflationary

The two need **opposite cures**, which is the same crossover shape found twice before in this line
of work:

| | more resource / time | restore the dimension |
|---|---|---|
| temporal | **recovers** | inert |
| dimensional | inert | **recovers** |

And an observer can tell which it has *before* trying either, from `retained_width` alone. For a
stressed agent that is the difference between "give it more time" and "give it something it cannot
give itself" — and getting it wrong wastes the intervention entirely.

## Honest bounds

One fixture, two dimensions, horizon 3, deterministic. Both models remain **stipulated**: nothing in
the substrate derives a mask from arousal, and nothing derives a budget from arousal either.
Deriving *either* is the open work, and until one is derived, "stress compresses aperture" is a
statement about what the substrate can represent, not about what stress does.

Gate: `tests/test_compression_models_migrated.py` 5/5, including
`test_the_published_inertness_result_is_specific_to_the_dimensional_model`, which asserts both
halves of the conditionality so it cannot be quietly lost.
