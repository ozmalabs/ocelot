# MERE-EXPOSURE × INITIAL-VALENCE — results (block 293000)

Pre-registration: `MERE_EXPOSURE_SOCIAL_PREREG.md`, committed BEFORE any
measurement (this arc). World adapter: `domains/mere_exposure_world.py`.
Confirmatory measure: `scripts/mere_exposure_social_measure.py` →
`results/mere_exposure_social/results.json` (RNG seeded once at 293000, N=60
agents/cohort, bootstrap 95% CI, 2000 reps; the mechanism is deterministic, so the
CI cohort jitters the per-agent belief-plasticity `alpha` within a personality band
to obtain a crossing-latency distribution — mirroring marshmallow / trait-anxiety).

**Headline: the substrate REPRODUCES the Zajonc mere-exposure × initial-valence
INTERACTION, expressed as CROSSING LATENCY on the discrete 3-state regard unit.
Repeated POSITIVE contact warms a NEUTRAL prior in 2 encounters, while every
NEGATIVE prior RESISTS — crossing to `regard > 0` only after strictly more
encounters (4, 12, 26), and a deep-enough negative prior does NOT cross within the
30-encounter budget. The produced regard-sign + qualia-valence grid EQUALS the
analytic oracle at EVERY cell. The felt-quality (`dynamical:valence`) TRACKS the
produced regard at every step. The effect depends on the belief update (freezing it
collapses every crossing). This is a genuine reproduction of the interaction PLUS a
squarely-reported representational limit — reported as such, not forced to a clean
pass.**

This is a CAPABILITY / mechanism demonstration (the interaction falls out of the
grounded CAN belief-update law + discrete relaxation), NOT an empirical claim about
real humans.

## The mechanism (named)

The LIKING is the graph's own read-off. An EXPOSURE is one positive encounter:
`hate_attribution.record_hate_incident(negative=False)` mints an IncidentReport,
lets the seeded rules derive the attribution, then applies the CAN belief-update
primitive `concept_apply_evidence(regard_for, +1.0, alpha)` and `run_rules()`. The
regard STATE is the discrete `{−1, 0, +1}` marginal ⟨σ⟩ of the tracked `regard_for`
Concept, relaxed by the native `can_native_update_3state`
(`seeds/can_native_reimplementation.json`) — the ENGINE produces it. The FELT
QUALITY is the `dynamical:valence` coordinate of the Concept's `concept_signature`
(`seeds/qualia_space.json`). INITIAL VALENCE is seeded by the SAME path (harm
encounters, `negative=True`). The adapter only DRIVES encounters and READS
`regard_for.state` / its qualia coordinates. **No Python computes the liking; no
Rust; no reward/punishment shaping.**

Per-encounter law (the engine's, read verbatim): `external_field ← external_field +
alpha·evidence`; state flips to `sign(external_field)` once `|external_field| >
0.366` (this engine's 3-state threshold at `temperature=1.5`), else `0`. At the
default `alpha=0.3`, each positive encounter adds `+0.3`.

## Produced-vs-oracle grid — MATCHES PREREG EXACTLY

Produced regard `state` (graph ⟨σ⟩) with produced `dynamical:valence` in
parentheses (`∅` = valence axis absent). `matches_oracle = True` at all cells
(state sign, qualia valence, AND crossing latency, for all five conditions).

| initial valence (ext0) | n=1 | n=2 | n=4 | n=5 | n=12 | n=26 | n=30 | **crossing latency** |
|---|---|---|---|---|---|---|---|---|
| **neutral** (0.0)                     | 0 (∅) | **+1 (+1)** | +1 | +1 | +1 | +1 | +1 | **2** |
| **negative_noncryst** (−0.6)          | −1 (−1) | 0 (∅) | **+1 (+1)** | +1 | +1 | +1 | +1 | **4** |
| **negative_cryst / mid** (−3.0)       | −1 | −1 | −1 | −1 | **+1 (+1)** | +1 | +1 | **12** |
| **negative_cryst / deep** (−7.2)      | −1 | −1 | −1 | −1 | −1 | **+1 (+1)** | +1 | **26** |
| **negative_cryst / very deep** (−9.0) | −1 | −1 | −1 | −1 | −1 | 0 | 0 | **None (>30)** |

Zero mismatches. The dynamics PRODUCED the pre-registered crossings — they were not
hand-set. (Note: `negative_noncryst` at ext0=−0.6 crosses at n=4, matching the
prior-stage measurement; the pre-reg §5's separate −0.9 "shallow" row was a distinct
recipe point and is not one of the five conditions swept here.)

## G-interaction (crossing latency, with CIs) — the headline numbers

Crossing latency = number of positive encounters to first reach `regard > 0`.
Deterministic single-agent latency at `alpha=0.3`, plus a jittered-alpha cohort
(N=60, bootstrap 95% CI) for the CI machinery. Non-crossing recorded as budget+1=31.

| condition | deterministic latency | cohort mean [95% CI] | CI-separated ABOVE neutral? |
|---|---|---|---|
| **neutral**                   | **2**  | 2.00 [2.00, 2.00]   | (reference) |
| **negative_noncryst**         | **4**  | 3.66 [3.53, 3.78]   | **YES** |
| **negative_cryst / mid**      | **12** | 11.93 [11.50, 12.37] | **YES** |
| **negative_cryst / deep**     | **26** | 26.5 [25.63, 27.47] | **YES** |
| **negative_cryst / very deep**| **None** | 30.2 [29.87, 30.60] | **YES** (never-crosses floor) |

`verdict_interaction = True`: neutral crosses fastest; every negative condition is
CI-separated strictly ABOVE neutral; latency is monotone in prior depth up to
never-within-budget. **This is the mere-exposure × initial-valence INTERACTION
expressed as latency — initial valence sets HOW MANY exposures liking takes — not a
bare main effect of exposure.** (The jittered-alpha cohort exists only to feed the
CI machinery; the deterministic latencies above are the exact primary result.)

## G-qualia-tracks-state — PASS (the felt-quality coupling)

At EVERY step of EVERY condition the produced `dynamical:valence` sign equals
`sign(regard_state)` (+1 / −1, or absent at state 0): steps checked across all five
trajectories, `n_mismatches = 0`, `verdict_qualia_tracks_state = True`. The felt
quality is coupled to the produced dynamics — `dynamical:valence` reads `−1` while a
seeded negative sits at state −1, is ABSENT while state is 0, and flips to `+1` at
the same encounter the state crosses. This is the genuinely-qualia part: the felt
valence is not a decorative label, it is grounded in the produced attitude dynamics.

## G-crystallized (the boundary outcome) — DELAY, not permanent immunity

The crystallized-negative behaviour EXACTLY as the prior stage measured:
`identity_field_all_zero = True`, `depth_scales_latency = True`,
`verydeep_never_crosses_within_budget = True`, `outcome = DELAY_NOT_PERMANENT_IMMUNITY`.

| crystallized recipe | ext0 | identity_field | `crystallized` flag | crossing latency |
|---|---|---|---|---|
| mid       | −3.0 | **0.0** | True | 12 |
| deep      | −7.2 | **0.0** | True | 26 |
| very deep | −9.0 | **0.0** | True | **None (>30)** |

The crux the prior stage resolved holds under measurement: `record_hate_incident` →
`concept_apply_evidence` writes `external_field` ONLY; the hate seed never touches
`identity_field`, and the native engine only READS `h_eff = external + identity`. So
a `negative_cryst` target reaches `crystallized == 1` (a `has_hate` node minted)
while its regard `identity_field` STAYS `0.0`. **What a "crystallized negative" has
is a DEEP accumulated negative `external_field`, not an identity-level lock.** The
boundary condition therefore manifests as a *depth-scaled latency* (12 → 26 → never
within budget) — the substrate models negativity bias as **DELAY**, not permanent
immunity. A true identity-level permanent block is NOT reachable through the
confirmed attitude API.

## G-personality (warm/hostile) — PASS

Belief-plasticity `alpha` rescales the per-encounter step and thus the crossing
latency. From a NEUTRAL prior:

| personality | alpha | deterministic latency | cohort mean [95% CI] |
|---|---|---|---|
| **warm**    | 0.6  | **1** | 1.00 [1.00, 1.00] |
| **default** | 0.3  | **2** | 2.00 [2.00, 2.00] |
| **hostile** | 0.15 | **3** | 3.00 [3.00, 3.00] |

`verdict_personality = True`: warm crosses in strictly fewer encounters than hostile
(CI-separated) — distinct crossing latencies by personality.

## G-ablation-falsifier (freeze the update) — PASS

Freezing the belief update (`alpha = 0` on the positive encounters, per §7): the
regard `external_field` never climbs, so regard NEVER crosses in ANY condition —
neutral never warms, every negative never recovers. `any_condition_crosses = False`,
`verdict_falsifier = True`. The exposure effect comes from the belief-update
pathway; with it frozen the effect vanishes in every condition. If a crossing had
survived, the claim would be false.

## G-glass-box — PASS

Regard `state` / `external_field` / `identity_field` / qualia coordinates read
straight off `graph_to_dict`:

- neutral after 2 exposures: state=**+1**, external_field=**0.6**, identity_field=**0.0**, qualia_valence=**+1**
- negative_cryst pre-exposure: state=**−1**, external_field=**−3.0**, identity_field=**0.0**, qualia_valence=**−1**
- negative_cryst after 12 exposures: state=**+1**, external_field=**0.6**, identity_field=**0.0**, qualia_valence=**+1**

Adapter source-audit clean: zero `graph_rewrite.run`/`gr.run`/`_match`/`_apply`/
`make_rule`; zero shaping tokens (`reward_signal`/`punish`/`reinforce`/`backprop`/
`gradient`). `verdict_glass_box = True`.

## G-discipline — PASS

Canonical `_native.abi3.so` md5 **a32ed336662eaa9eb6df27b7112541ac** — UNCHANGED
(NO Rust; `runners/dsl` untouched; toolbox solvers untouched; the frozen seeds
`can_native_reimplementation.json` / `shared_arousal.json` loaded read-only). **No
new seed authored** — `seeds/mere_exposure_social.json` does not exist and nothing
named `mere_exposure` is in `load_all_seeds`, so the base tree is byte-identical when
the adapter is absent. The produced discrete regard state is integer at every step.
`verdict_discipline = True`.

## THE VERDICT (three honest parts)

### (1) REPRODUCED — the exposure × initial-valence interaction as crossing latency

The substrate reproduces the Zajonc mere-exposure × initial-valence INTERACTION.
A NEUTRAL prior warms to liking in **2** positive encounters; a NEGATIVE prior
RESISTS, crossing only after **4, 12, 26** encounters as the prior deepens, and a
DEEP negative prior does **NOT cross within 30** — each negative CI-separated
strictly above neutral, monotone in prior depth. Familiarity/accumulation rises in
every condition (the `external_field` climbs `+0.3`/encounter everywhere), but
LIKING (the discrete state / qualia valence) crosses fast for neutral and
slowly-or-never for negative. That is an INTERACTION, not a bare main effect of
exposure — the boundary condition expressed discretely as latency.

### (2) The FELT-QUALITY coupling holds — the genuinely-social + genuinely-qualia part

At every step in every condition the `dynamical:valence` qualia coordinate tracks
the produced regard state sign (0 mismatches). The felt valence is `−1` while the
attitude sits negative, absent while neutral, and flips to `+1` at the exact
encounter the state crosses. This is the part the prior single-agent psi/CAN
experiment lacked: the effect is measured on a *social* regard-for-a-target unit,
and the *felt quality* is coupled to the produced attitude dynamics rather than
asserted. The qualia mapping is grounded, not decorative.

### (3) The REVEALED LIMIT/FLAW — discrete regard, and delay-not-immunity

Two honest limits, reported as valid results rather than smoothed over:

- **Discrete 3-state regard ⇒ NO graded liking magnitude / decelerating curve.**
  The regard unit is a discrete `{−1, 0, +1}` marginal, not a scalar. Once enough
  positive evidence accumulates the state jumps to `+1` and SATURATES flat. So the
  substrate CANNOT produce the graded, positive-decelerating exposure→affect
  magnitude curve the wet literature reports; it produces only the *sign crossing*
  and its *latency*. This is a genuine representational limit of the attitude
  substrate. (The underlying `external_field` accumulator IS graded and linear — but
  it is a flat-slope linear climb, so it does not model the decelerating curve
  either, and the FELT quantity, liking sign, is the discrete state.)

- **A crystallized negative EVENTUALLY warms ⇒ negativity bias is modelled as
  DELAY, not PERMANENT immunity — a PARTIAL reproduction.** Diagnosed against the
  CAN relaxation: `record_hate_incident` writes only `external_field`, and positive
  exposure accumulates `+0.3` linearly and eventually overwhelms any *finite*
  accumulated negative field. The one quantity that could produce permanent
  immunity — `identity_field`, which enters as `h_eff = external + identity` and
  does not decay like accumulated evidence — is unreachable through the confirmed
  attitude API (it stays `0.0`). So the deepest crystallized negative resists only
  *longer* (up to exceeding a fixed budget), not *forever*. The wet boundary
  condition's strong form (genuinely unpleasant stimuli do not warm at all) is
  reproduced only as *latency exceeding the budget*, not as categorical immunity.
  A future rung that wires `identity_field` directly could test the strong form;
  **this rung does not claim it.** Per §2b, this rung claims only the WEAK (latency)
  form of the boundary condition, not a slope-asymmetric negativity bias.

## Test result

`tests/test_mere_exposure_social_migrated.py` — **11 passed**. Full
social/emotion/trait/qualia surface GREEN: with
`test_trait_anxiety_interpretation_migrated + test_bigville_theory_of_mind +
test_bigville_disposition_apply + test_bigville_ocelot_adapter +
test_qualia_space_migrated + test_trait_modulator_bridge + test_disposition +
test_emotion_phenotype_migrated + test_marshmallow_migrated` → **96 passed**.

## Honest residuals & claim separation

- **Capability vs empirical.** Synthetic MECHANISM demonstration: the substrate
  reproduces the mere-exposure × initial-valence interaction (and its negative
  boundary) as a consequence of its grounded belief-update + discrete relaxation. It
  is NOT a validation against real human liking and says nothing about actual people.
- **The mechanism is deterministic** (the per-encounder step + threshold are engine
  constants; no mechanism noise). The reported CIs come from a jittered per-agent
  plasticity cohort, not from mechanism stochasticity — the CI-separation reflects
  that initial valence dominates within-cohort plasticity jitter, exactly as a
  latency-interaction claim should. Individual-cell states/latencies are exact and
  reproduce the analytic oracle.
- **regard-for-a-target ↔ liking and positive-encounter ↔ mere-exposure are the
  honest substrate stand-ins** named in the prereg (§2). The claim is about the
  DYNAMICS (a flat additive accumulator against a discrete threshold, gated by
  initial valence), not that the regard unit IS human liking.
- **Triviality confound (§2b).** The neutral fast-crossing is NOT a biased-baseline
  artefact: a fresh `regard_for` reads true-zero (`external_field = identity_field =
  state = 0`, no log-odds attribute) and the accumulator is symmetric (2 positive →
  +0.6/state +1 mirrors 2 negative → −0.6/state −1). But the "negative resists"
  result is, mechanically, a mirror-symmetric linear climb from further below the
  threshold — the WEAK latency form, NOT a slope-asymmetric negativity bias. That
  scope is stated plainly so no reader mistakes the linear-latency result for the
  strong form.
