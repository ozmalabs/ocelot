# TRAIT-ANXIETY NEGATIVE INTERPRETATION BIAS — results (block 292000)

Pre-registration: `TRAIT_ANXIETY_INTERPRETATION_PREREG.md`, committed BEFORE any
measurement (prior arc). Base sha **63953984**. World adapter:
`domains/trait_anxiety_world.py`. Confirmatory measure:
`scripts/trait_anxiety_interpretation_measure.py` →
`results/trait_anxiety_interpretation/results.json` (RNG seeded once at 292000,
N=60 agents/cohort, bootstrap 95% CI, 2000 reps; deterministic mapping, jittered
exploration_urge cohort for the CI machinery).

**Headline: the substrate REPRODUCES the MacLeod & Mathews trait × ambiguity
dissociation. The SKEPTICISM trait bends the interpretation of the AMBIGUOUS
threat stimulus ONLY (safe → threat as trait-anxiety rises), while the SAFE band
(all "none") and the THREAT band (all "anxiety") are personality-INVARIANT. The
produced grid EQUALS the analytic oracle at every one of the 15 cells. The
interaction depends on the bias hook — forcing `skepticism_bias = 0` collapses it.
This is a genuine reproduction of the interaction, NOT a main effect, and NOT a
revealed flaw.**

This is a CAPABILITY / mechanism demonstration (the dissociation falls out of the
grounded affect rules), NOT an empirical claim about real humans.

## The mechanism (named)

The anxiety LABEL is the graph's own read-off. The REAL region predicate
**`emx_anxiety`** (`tools/build_modulator_seeds.py`, order 10) fires iff all of
`d.appraised==1`, `ms.valence<0`, `d.threat==1`, `d.threat_persists==1`,
`ms.competence<ms.competence_lo`, and **`ms.securing > ms.securing_hi` (=50)**;
`emx_readoff` (order 13) writes `ms.emotion` (anxiety = code 3). Securing is the
graph formula **`mod_securing`** (order 6):
`securing = d.exploration_urge + (competence_full − competence) − sec_k·weight
+ ms.skepticism_bias`. With the fixed §3 threat context, every non-securing
conjunct holds identically in every cell, so `ms.securing` is the SINGLE
personality-moved quantity. **AMBIGUITY** is the stimulus `d.exploration_urge`;
**trait-anxiety** is the SKEPTICISM trait, which
`trait_modulator_bridge.sync_traits_to_modulator` maps (STEP=15) onto
`ms.skepticism_bias`. The adapter only SETS the stimulus + seeds the trait +
syncs the bias, runs the rules, and READS `ms.emotion`/`ms.securing`. **No Python
computes the emotion; no Rust; no reward/punishment shaping.**

With the pre-registered constants `K = (20−20) − 1·10 = −10`, anxiety fires iff
`exploration_urge + 15·skep_level > 60`.

## Produced-vs-oracle grid — MATCHES PREREG EXACTLY

Produced anxiety label (graph `ms.emotion==3`), produced `ms.securing` in
parentheses. `labels_match_oracle = True`, `securing_matches_oracle = True`
(all 15 cells).

| ambiguity \ skep | −4 | −2 | 0 | +2 | +4 |
|---|---|---|---|---|---|
| **SAFE** (eu=0)       | none (−70) | none (−40) | none (−10) | none (20)  | none (50)  |
| **AMBIGUOUS** (eu=60) | none (−10) | none (20)  | none (50)  | **anxiety (80)** | **anxiety (110)** |
| **THREAT** (eu=130)   | anxiety (60) | anxiety (90) | anxiety (120) | anxiety (150) | anxiety (180) |

Zero mismatches. The dynamics PRODUCED the pre-registered labels — they were not
hand-set. The AMBIGUOUS row flips at the skepticism sign (0→0→0→1→1); the SAFE row
is all "none" and the THREAT row is all "anxiety".

## G-interaction (personality effect per band, with CIs) — the three numbers

Personality effect = high-skepticism anxiety RATE − low-skepticism RATE, measured
SEPARATELY in each band (jittered-exploration_urge cohort, N=60, bootstrap 95%
CI). Low-skep cohort = `{−4, −2}`, high-skep = `{+2, +4}`.

| band | low-skep rate [CI] | high-skep rate [CI] | personality effect | CI-separated? |
|---|---|---|---|---|
| **SAFE**      | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | **0.00** | no |
| **AMBIGUOUS** | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | **+1.00** | **YES** |
| **THREAT**    | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | **0.00** | no |

The effect is **present ONLY in the AMBIGUOUS band** (high CI-separated above
low), and **~0 at both endpoints**. `verdict_interaction_shape = True`. This is
the trait × ambiguity INTERACTION.

(The jitter is bounded by each band's own pre-registered margin to the boundary:
SAFE jitters downward-only, THREAT upward-only, AMBIGUOUS straddles the 50
crossing symmetrically — the only band where jitter can yield an intermediate
rate, which is exactly where the human interaction lives. The deterministic grid
above is the exact primary result; the jittered cohort exists only to feed the CI
machinery, mirroring marshmallow's deterministic-mapping-with-jittered-cohort.)

## G-dissociation (personality invariance at the endpoints) — PASS

Deterministic, exact: SAFE band all "none" across the whole skep sweep
(`safe_all_none = True`); THREAT band all "anxiety" (`threat_all_anxiety = True`);
AMBIGUOUS band contains BOTH labels (`ambiguous_flips_with_trait = True`).
`verdict_dissociation = True`. Overt-safe and overt-threat stimuli are interpreted
identically by every temperament — the proof that this is an INTERACTION, not a
main effect of skepticism.

## G-ablation-falsifier (bias forced to 0) — PASS

Re-running with `ms.skepticism_bias` forced to 0 after the sync (§7 falsifier):
every ambiguous cell collapses to the no-bias securing `eu + K = 50` = "none"
(`all_cells_collapse_to_no_bias = True`); the jittered high vs low cohorts are NO
LONGER CI-separated (low [0.28, 0.52] vs high [0.30, 0.57] — overlapping),
`interaction_survives = False`, `ablated_personality_effect ≈ 0.03` (jitter noise
straddling the now-trait-independent 50 boundary equally for both cohorts).
`verdict_falsifier = True`. The interaction comes from the trait → set-point
pathway; with the hook removed it vanishes.

## G-glass-box — PASS

`skep_level` / `exploration_urge` / `skepticism_bias` / `securing` / `emotion`
read straight off `graph_to_dict`:

- ambiguous @ skep −4: exploration_urge=60, skepticism_bias=**−60**, securing=**−10**, emotion=0 (none)
- ambiguous @ skep +4: exploration_urge=60, skepticism_bias=**+60**, securing=**110**, emotion=**3** (anxiety)
- threat @ skep −4:    exploration_urge=130, skepticism_bias=−60, securing=**60**, emotion=**3** (anxiety)

Adapter source-audit clean: zero `graph_rewrite.run`/`gr.run`/`_match`/`_apply`/
`make_rule`; zero shaping tokens (`reward_signal`/`punish`/`reinforce`/`backprop`/
`gradient`). `verdict_glass_box = True`.

## G-discipline — PASS

Canonical `_native.abi3.so` md5 **a32ed336662eaa9eb6df27b7112541ac** — UNCHANGED
(NO Rust; `runners/dsl` untouched; toolbox solvers untouched; the canonical
emotion regions in `tools/build_modulator_seeds.py` read-only reference). **No new
seed authored** — `seeds/trait_anxiety_interpretation.json` does not exist and
nothing named `trait_anxiety` is in `load_all_seeds`, so the base tree is
byte-identical when the adapter is absent. Integer-native: every produced (and
oracle) securing value is an integer. Pinned rule names present on the spine
(`mod_securing`, `emx_anxiety`, `emx_readoff`). `verdict_discipline = True`.

## THE VERDICT

**REPRODUCED — genuine reproduction of the MacLeod & Mathews dissociation, no
flaw.** Personality bends ONLY the ambiguous interpretation (effect +1.00,
CI-separated); the SAFE band stays all-"none" and the THREAT band stays
all-"anxiety" across the entire skepticism sweep (effect 0.00, invariant). The
produced grid equals the analytic oracle at every cell; the interaction depends
on the bias hook (ablation collapses it). Personality did NOT leak into the
safe/threat bands (no main effect), the ambiguous band DID move, and the produced
labels did NOT diverge from the oracle. The substrate reproduces the trait ×
ambiguity interaction as an emergent consequence of its own grounded affect rules
— one additive set-point offset written by a trait, bending the single
personality-moved conjunct of `emx_anxiety`, with no bespoke bias parameter and no
Python deciding the emotion.

**Why no leak (the modulator geometry that made it work).** The bias magnitude
(±60 at full-scale skepticism, STEP=15 over levels ±4) is exactly the ±60
personality swing the bands were separated against: the SAFE ceiling sits at
securing=50 at skep=+4 (never `>50`) and the THREAT floor at securing=60 at
skep=−4 (always `>50`), each on the correct side of the boundary by construction
with margin ≥0 at the extreme. Because `skepticism_bias` is a CONSTANT ADDITIVE
offset on `mod_securing` and the band gaps (60, 70) each ≥ the full swing, the
offset can only decide the label inside the AMBIGUOUS band, where skep=0 lands
exactly on the boundary and the sign of skepticism is the sole decider. The
additive-offset structure is what confines the effect to the interaction term.

## Test result

`tests/test_trait_anxiety_interpretation_migrated.py` — **10 passed**. Full
emotion/trait/qualia surface GREEN: with
`test_trait_modulator_bridge + test_personality_homeostasis +
test_emotion_phenotype_migrated + test_doom_emotion_narration_migrated +
test_marshmallow_migrated + test_modulator_emergence_migrated + test_disposition +
test_trait_vector + test_qualia_space_migrated` → **133 passed**.

## Honest residuals & claim separation

- **Capability vs empirical.** Synthetic MECHANISM demonstration: the substrate
  reproduces the trait × ambiguity DISSOCIATION as a consequence of its grounded
  affect rules. It is NOT a cognitive-clinical validation and says nothing about
  real anxious people's interpretations.
- **The mapping is deterministic** (integer arithmetic, zero mechanism noise). The
  reported CIs come from a JITTERED exploration_urge cohort, not from mechanism
  stochasticity — the CI-separation reflects that the personality offset dominates
  the within-band jitter, exactly as an interaction claim should. Individual-cell
  labels/securings are exact and reproduce the analytic grid.
- **Trait-anxiety ↔ SKEPTICISM and ambiguity ↔ exploration_urge are the honest
  substrate stand-ins** named in the prereg (§2). The claim is about the DYNAMICS
  (an additive set-point offset confined to the interaction term), not that
  skepticism IS clinical trait-anxiety.
- **Prior-art posture.** The interpretation-bias phenomenon is MacLeod & Mathews';
  interpretive-bias computational models exist. The delta is the dissociation
  falling out of an ALREADY-GROUNDED, glass-box affect substrate with no bespoke
  bias parameter — a mechanism claim on this substrate, not a novelty claim about
  bias modelling in general.
