# Rung 1 — Self-Generated Spontaneous Activity (the plan)

*2026-07-16. Branch: `gamma-substrate/developmental-vision`. Follows the 105-agent
verified developmental research (see `VISION_DEVELOPMENT_ARC.md`). Supersedes the
L0 "grow kernels from natural image patches" approach, which the research shows was
the wrong experiment.*

## Why this rung, and why it is rung 1

The directive: **vision needs the full from-scratch treatment to FORCE THE PARADIGM.**
Bolting vision onto good cognition hides the bolt-on; vision from photons cannot hide
one. Vision is the forcing function, not the deliverable.

The research forces the ordering:

- **Orientation is NOT created by learning on natural images** (3-0). Ferret maps
  emerge P31–36 with no correlation to eye opening; dark-reared ferrets have maps;
  cat orientation emerges *before* eye opening. The L0 null was the PREDICTED result.
- **Before eye opening, V1's training data is WAVE statistics** (3-0) — self-generated,
  retina → SC → V1. **Tabula rasa is not blank + external data; it is blank +
  self-generated structured activity, then refined by experience.**
- **The local rule is measured and implementable** (3-0): burst-based Hebbian, ~1 s
  window (NOT ms-STDP): coincident **+21.3 ± 5.1%**, non-overlapping **−5.9 ± 1.4%**
  (Butts/Kanold/Shatz 2007).

## The paradigm-forcing split (the whole point)

**The adapter supplies UNSTRUCTURED entropy only. The STRUCTURE is made by the
agent's own rules.** Biology's wave initiation is stochastic (spontaneous
depolarisation); its *structure* — local propagation, refractoriness, spatiotemporal
correlation — is the retina's own circuit. So:

- the adapter injects random ignition seeds (mechanical I/O, the thermal-noise
  analogue) and advances a clock;
- `vision_waves` rules do propagation / refractoriness / burst learning;
- **the `noise` arm uses the SAME entropy source with propagation DISABLED.**

Same entropy, different structure ⇒ any difference between arms is produced by the
graph, not handed to it. This is what makes the rung a test of the paradigm rather
than a demonstration of numpy.

## What is explicitly NOT assumed

The research **refuted 0-3** the claim that sparsity/ICA rather than Hebbian/Oja is
the load-bearing ingredient, and refuted "same algorithm + different input
distribution suffices". Olshausen & Field / Atick & Redlich / Barlow / Földiák /
Rao & Ballard / Coates & Ng produced **zero** surviving verified claims. Only
licensed: ICA on *simulated* waves yields Gabor-like RFs *in silico*
(Albert/Schnabel/Field 2012).

⇒ **This plan does NOT assume waves+Hebbian will produce orientation.** That is the
open question it measures. A null here is a real result and gets reported as one —
it would say the input statistics are not sufficient and the objective carries the
weight, which is precisely what verification refused to license either way.

## The build

**Rung 1a — the agent generates its own waves.**
`seeds/vision_waves.json`:
- `RetinaCell{row, col, state ∈ rested|active|refractory, phase}` on a laid-out grid
  (`neighbour` edges: mechanical geometry, like `VisionWorld`'s patch slicing).
- `wv_propagate` — an active cell recruits its RESTED neighbours (this is the rule
  that makes structure out of noise).
- `wv_refract` / `wv_recover` — an active cell becomes refractory; recovers after
  `refractory_steps`. Refractoriness is what makes waves *travel* instead of
  saturating.
- `WaveParams{refractory_steps, enhance_rate: 0.213, depress_rate: 0.059, ...}` — all
  knobs graph data, the measured constants from Butts 2007.

**Rung 1b — burst-based Hebbian on synapses as NODES.**
A synapse is a `Synapse{weight}` node (`RetinaCell -pre-> Synapse -post-> Unit`), NOT
a weight vector — this sidesteps the engine's missing `Zip` (no way to pair `w[i]`
with `x[i]` by index) and is more biological: a synapse *is* an edge-like object with
its own state.
- `bh_potentiate` — pre burst ∧ post burst (coincident) → `weight *= 1 + enhance_rate`
- `bh_depress` — pre burst ∧ ¬post burst → `weight *= 1 − depress_rate`
- unit activation = `Fold` over its synapses (verified expressible: vector/scalar
  accumulation works).

**Rung 1c — the gate (4 arms, mapped to the actual experiments).**
NOTE the correction that matters: **dark rearing does NOT remove waves** — dark-reared
ferrets have maps *because* waves continue. So the arms are:

| arm | drive | biology | prediction |
|---|---|---|---|
| `none` | no waves, no vision | β2-nAChR-KO-like (waves disrupted) | no structure |
| `waves` | waves only | **dark-reared** | maps form; tuning immature |
| `waves+video` | waves + real structured experience | **normal** | best; mature tuning |
| `waves+noise` | waves + unstructured drive | **lid-sutured** | **WORSE than `waves`** |

**The discriminating comparison is `waves+noise` < `waves`** — unstructured drive must
be *actively destructive*, not merely uninformative. A model where noise merely fails
to help has NOT reproduced the biology (White/Coppola/Fitzpatrick 2001).

## Gates

1. **Structure is real, not asserted:** the wave arm's activity must be
   spatiotemporally correlated — correlation decaying with distance — and the noise
   arm's must not, from the SAME entropy. Measured, with the noise arm as control.
2. **The measure is calibrated first** (the standing lesson): spectral anisotropy vs
   random and vs an ideal Gabor. Never the sign classifiers (they pass noise ~50–75%
   and fail an ideal Gabor).
3. **Rule constants are the measured ones** (+21.3% / −5.9%) and live in graph data.
4. **donkey=0**, all decisions in rules, adapter supplies only entropy + clock.
5. **Powered**: n per arm large enough that a delta within ~3× the per-unit step is
   not reported as a result. Permutation tests, CIs.
6. No new Rust expected (`Fold`/`MapList`/`VecAdd`/`IfThenElse` verified sufficient).

## Honest scope

`preprocess_patches` (DC removal + contrast normalisation) is a **bolted-on retina**
and is demoted to a control arm only. The rest of `vision_floor`'s hand-authored
content (`SamplingGeometry` thresholds, figure-ground / region-as-belief rules) is
named as bolt-on too, and is not depended on here.

Rung 1 is the *scaffold*. Experience-as-refinement (and the dorsal/motion front, which
the research shows is EARLY and parallel — not a later rung) follow only once the
scaffold measurably exists.
