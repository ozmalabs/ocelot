# STRESS COMPRESSES APERTURE — results (block 366000)

Pre-registration: `STRESS_COMPRESSES_APERTURE_PREREG.md`, committed before any measurement
(`f5e809c`), base sha `3da4e0c`. Measure: `scripts/stress_aperture_measure.py`. Engine built from
the measuring tree's own source in an isolated worktree; the live `.so` was not rebuilt.

**Headline: every registered gate passes, and the load-bearing one passes decisively — evidence at
42× the horizon does not move a compressed agent at all.** Stress does not make this agent wrong. It
makes it unable to tell, which is a different failure with a different cure.

## The manifold half — measured

The escape lives in dimension 1, which is the dimension stress removes.

| arm | `loss` | `information_loss` | `resolved` | `retained_width` | selection |
|---|---|---|---|---|---|
| **regulated** | **1.0** — sees the escape | 0.0 | 1.0 | 1.0 | feasible 1, selected 1 |
| **dysregulated** | **0.0** — sees nothing | 3.0 | 0.0 | 1.0 | unestablished 2, feasible 0, **withheld 0** |

`retained_width` is `1.0` in *both* arms and that is correct rather than a wash: dimension 0 is
resolved and stays in the tube, so its retention genuinely is established. The compressed agent is
partially blind, not globally blind, and the record says so.

> **CONDITIONED, one rung later — read this before quoting the table below.**
> "Stress compresses aperture" names **two** mechanically different things, and this document
> measured only one:
>
> * **A — DIMENSIONAL.** A dimension you could resolve is removed. **Stipulated**: something must
>   supply the mask, and nothing in the substrate derives it. *This is what was measured here.*
> * **B — TEMPORAL.** How far ahead you can audit shortens. **Derived**: the projection budget is
>   already a represented resource.
>
> Both raise `information_loss`, both zero `resolved`, and from outside they present as one deficit.
> But **`G-evidence-is-inert` is a property of A, and would have FAILED under B** — measured:
> dimensional compression is still unresolved at 64× budget, while temporal compression recovers
> completely at 8× and sees the escape. The headline below is therefore about a stipulated mechanism,
> not about stress.
>
> They are separable in the record without any intervention (`retained_width`: A leaves other
> dimensions retained, B establishes nothing) and graded differently (B's deficit moves with the
> resource, A's is flat). See `COMPRESSION_MODELS_RESULTS.md`; gate
> `tests/test_compression_models_migrated.py` 5/5.

## G-evidence-is-inert — the gate the claim lives on

| evidence strength | 1.0 | 3.0 | 8.0 | 32.0 | 128.0 |
|---|---|---|---|---|---|
| `resolved` | 0 | 0 | 0 | 0 | 0 |
| `loss` | 0 | 0 | 0 | 0 | 0 |
| `information_loss` | 5 | 3 | 3 | 3 | **3** |

**A gain is a thing more evidence overcomes. This is not.** At 128 — 42× the horizon — nothing has
moved. The plateau at 3 is the aperture's own contribution and it is not reducible by exposure at
any strength, because the distinction is not resolvable at any exposure.

The `1.0` column is the more informative one, and it was not registered. `information_loss = 5`
decomposes exactly: 2 unaudited ticks × 1 resolvable dimension, plus 3 ticks × 1 blind dimension.
**The two ways a cell goes unassessed — the budget never reached its tick, the aperture never
resolved its dimension — are one quantity, and the arithmetic shows it.** That is why the earlier
rung's `resolved = information_loss == 0` is the right definition rather than a tick count.

## The other gates

* **G-stupid-not-wrong** — PASS. `information_loss > 0` with `loss == 0`. Compression never registers
  as failure; an agent believing it saw a failure it could not see would be worse than the bug fixed.
* **G-not-the-other-two** — PASS. `withheld_minimal` empty (not stubborn), family non-empty (not
  ignorant). All three present identically from outside; the record separates them.
* **G-regulation-recovers** — PASS. The regulated arm resolves, sees the escape, and selects. Without
  this control, *"nothing helps a stressed agent"* would pass trivially for an agent that is broken.
* **G-byte-identity** — PASS, in Rust: an all-ones mask is byte-identical to no mask, and a
  wrong-length mask is ignored rather than half-applied (fail **safe**, not closed — a malformed mask
  must never silently blind a dimension).

Gates: `tests/test_stress_aperture_migrated.py` 10/10; `future_manifold` Rust 18/18; Rust lib 804
passed with one pre-existing flaky failure (`framebuffer::seqlock_read_races`, ~50% with and without
these changes, measured six runs each way); manifold Python suites 42 passed.

## The learning half — NOT measured, and why the argument is still worth recording

`learning_progress_curiosity` gates curiosity and attention on
`learning_progress = residual_prev − residual` — a **difference of residuals**. A residual that
cannot be *established* has no difference to take. So the prediction is that a compressed aperture
does not slow the learning signal, it **removes** it, and that the same crossover applies: more
exposure cannot restore a signal that is undefined rather than small.

**This was not run.** That seed's residual is a held-surface temporal surprise, not the manifold
residual, and wiring one to the other is real work. Asserting the connection because the two both
contain the word "residual" would be exactly the kind of claim this line of work keeps catching. It
is registered as a prediction with its reason and nothing more.

## Honest bounds

Everything in prereg §5 stands. One fixture, hand-set masks, deterministic arms, n=1, no CI.
`arousal_window_coreg`'s own caveat (an authored affect model, not a clinical one) is inherited in
full and is not discharged by this pass.

**The load-bearing weakness, restated because a pass makes it easier to forget: the compression is
STIPULATED, not derived.** Nothing in the substrate explains why stress should compress these
particular dimensions — the rule applies a mask the fixture supplies. What is demonstrated is that
the affect subsystem and the manifold audit **compose**, and that the composition yields a
distinguishable, evidence-proof deficit. That is not evidence they compose this way in nature, and
this document does not claim it.
