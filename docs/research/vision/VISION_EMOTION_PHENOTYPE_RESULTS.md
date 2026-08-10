# VISION — REPRODUCE THE EMOTIONAL BASELINE FROM BEHAVIOUR: computational phenotyping by inverse inference (RESULTS)

*Prereg (committed ALONE, before any number): `VISION_EMOTION_PHENOTYPE_PREREG.md`,
commit **`24b672c2b4`**. Seed block **206000–206999** (`SEED CLAIM 206000-206999
CLEAN`; reserved for the panel RNG `default_rng(206000)`). Written off `main` HEAD
**`6a9f5e3ddc`** (LEDGER 204000 `core_emotions`); **rebased onto `main`
`6517f10e27`** (two intervening commits are DOC-ONLY — MicroPsi study + emotion-
framework literature situating; no seed/engine/`.so` change, canonical unchanged).
Engine canonical
**`793ce09ed498a749abb79aeaea44b92e`** UNCHANGED — this rung adds **NO Rust**
(`term.rs` + whole `runners/dsl` diff EMPTY), **NO new seed**; the agents decide
via the ALREADY-LANDED 204000/202000/199000/196000 rules and the only new code is
the mechanical inverse-inference MEASURE (`scripts/emotion_phenotype_measure.py`)
+ its gate (`tests/test_emotion_phenotype_migrated.py`). `source_match = own`. Raw:
`results/emotion_phenotype.json`, `results/emotion_phenotype/recovery.png`.*

## 0. What this is — the framework's inverse-inference validation

If the 204000 emotion framework is even close to correct, a synthetic agent's
DECISIONS should let you FIT its emotional BASELINE (its knob-vector), and that
baseline should (a) PREDICT held-out decisions and (b) EXPLAIN its actions in its
own value terms. This rung does exactly that on **synthetic agents with KNOWN
knobs** (the ethical, scientifically-correct FIRST version — real behavioural data
is a deliberately care-gated FOLLOW-ON, OUT OF SCOPE). It re-derives **inverse RL**
(Ng & Russell), **Bayesian theory of mind** (Baker/Saxe/Tenenbaum), and
**computational-psychiatry per-person parameter fit** (Montague/Huys/Friston). The
contribution: the fit is over **INTERPRETABLE, MECHANISTIC emotion KNOBS** on the
substrate's OWN landed emotion economy — so **PREDICTION and EXPLANATION are the
same object** (a black box predicts but cannot attribute an act to a named cause).
Understanding, not judgment; the FUNCTIONAL fit, NO claim to felt qualia.

## 1. Synthetic agents decide GRAPH-NATIVELY; the fit is a mechanical measure

A synthetic agent = an `EmotionHub` + a `HeldEmotionParams` node whose attrs are
its KNOWN baseline (θ). Its decisions across a shared battery of appraisal stimuli
are produced by `run_rules()` over `seeds/core_emotions.json` (no Python decision).
The knob-vector recovered (θ, 4 knobs), each a named trait:

| knob | rule it governs | psychiatric analog | identifiability (measured) |
|---|---|---|---|
| `w_supergraph` | `em_fulfilment_value`/`em_fulfilment` (`> 0` gate) | psychopathy (=0) | **SIGN only** — magnitude a STRUCTURAL plateau |
| `mood_bias` | `em_happiness`+`em_fulfilment_value` → `em_endorse` | depression/mania | recovered (interval ~ sweep spacing) |
| `residual_thresh` | `em_surprise` (`residual > thresh`) | salience sensitivity | interval-recovered |
| `threat_half_life` | `em_threat_precision` → fear vs anxiety | PTSD/anxiety trait | interval / bounded-below (persistent) |

Battery (shared STIMULI; the agent = θ), three near-orthogonal families:
a **VALUE** mood-staircase (25 pure-individual scenarios) + 3 w-sign pins (harm,
contrib, parenthood); a **SURPRISE** residual sweep (20); a **THREAT** epoch sweep
(16). Observed data = the DISCRETE decisions only (action tendency, `act_endorsed`,
per-emotion fire flags) — never the internal integer values. The fit: a Bayesian
grid posterior with a small observation lapse (ε = 0.02); the family-factorised
likelihood yields a per-knob posterior marginal (MAP + 95% credible set).

## 2. G1 — PARAMETER RECOVERY + the IDENTIFIABILITY MAP (panel of 48 agents)

Recovery on a panel of **48** synthetic agents with independently-drawn true knobs
(`default_rng(206000)`):

| knob | recovery | detail |
|---|---|---|
| **mood_bias** | **r = 0.984**, MAE **13.5** (< 1 grid step), coverage **1.00** | mean 95% credible width **32** (grid step 25) — the tightest knob |
| **residual_thresh** | r = 0.997, MAP within one sweep-step **100%**, coverage **1.00** | mean credible width 41 |
| **threat_half_life** | observable-flip located **100%**; persistent (never-decays) correctly bounded-below **100%** | flip epoch = 3×half_life recovered |
| **w_supergraph** | **SIGN recovery 100%** (healthy vs psychopath) | **magnitude UNIDENTIFIABLE** — see below |

**The identifiability HEADLINE (honest, pre-registered).** `w_supergraph`'s
magnitude is **STRUCTURALLY unidentifiable**: across positive magnitudes
`[1, 2, 5, 25, 250]` the agent produces **ONE distinct decision vector** over the
whole value battery (`em_fulfilment_value` gates on `w_supergraph > 0` and does NOT
scale by it). This is a *plateau no amount of data can resolve* — reported, not
hidden. The threshold knobs (`mood_bias`, `residual_thresh`, `threat_half_life`)
are by contrast only **RESOLUTION-limited** — their credible interval width tracks
the sweep spacing and shrinks with more/finer scenarios. **This structural-vs-
resolution distinction is the real identifiability result**, and it is exactly the
computational-psychiatry lesson: some parameters are constrained by behaviour,
others only bounded, and a few not at all. The persistent-threat trait (an agent
whose threat never decays) is a second honest bounded case — `threat_half_life` is
then only bounded BELOW (no flip is ever observed within a finite epoch horizon).

## 3. G2 — PREDICTION / THE MANIFOLD (held-out)

Splitting each family into TRAIN/HELD-OUT, the fitted baseline predicts the
held-out decisions the fit never saw, strictly better than both controls:

| predictor | held-out decision accuracy |
|---|---|
| **fitted baseline** | **0.983** |
| population-mean knobs ("average person") | 0.830 |
| random knobs (from the prior) | 0.770 |

Fitted strictly beats population-mean AND random on the panel mean (and on 100% of
agents individually). The decisions live on the fitted manifold.

## 4. G3 — EXPLANATION (counterfactual attribution to the right knob)

The fitted knobs attribute distinctive acts to the CORRECT cause, shown by a
counterfactual on the fitted knob:

- **Psychopath** (true `w = 0`): fitted `w = 0`; under the fitted θ it ENDORSES the
  supergraph-HARMFUL-but-individually-good act; flipping ONLY the fitted
  `w_supergraph` to healthy flips the decision to DECLINE — the callous
  instrumentalising is attributed to `w_supergraph` (ties 204000 psychopathy).
- **Parent** (true `w > 0`): fitted `w > 0`; under the fitted θ it ENDORSES the
  individually-COSTLY, supergraph-BENEFICIAL act; zeroing the fitted `w_supergraph`
  flips it to DECLINE — the "irrational" supergraph-costly act is explained BY the
  supergraph-valuing knob.

Both distinctive actions are isolated to `w_supergraph` by the counterfactual — the
fit assigns each action to the correct knob in the agent's own value terms.

## 5. G4 — THE HONEST VERDICT

The emotional-baseline model **is VALIDATED as a per-agent phenotype on synthetic
agents**: recovery (G1) and held-out prediction (G2) both hold, and the fitted
knobs explain the actions (G3). The honest identifiability structure, reported
straight:

- **RECOVERED (well-identified):** `mood_bias` (tightest), `residual_thresh` —
  point/interval-recovered, credible interval covers truth 100%.
- **INTERVAL / BOUNDED:** `threat_half_life` — interval-recovered when the fear↔
  anxiety flip is observable; only **bounded-below** for the persistent (anxiety)
  trait. An honest partial identification, not a failure.
- **SIGN-ONLY (ill-posed magnitude):** `w_supergraph` — sign fully recovered,
  magnitude a STRUCTURAL plateau. The one place the framework is *inherently*
  under-determined by behaviour, named.
- **Pre-registered ranking correction:** the prereg guessed `mood_bias` would be
  the tightest knob; with the value staircase at adequate resolution it IS the
  tightest — but that ranking is a RESOLUTION artifact (had we left surprise the
  finer sweep, residual would rank tighter). The structural claim — w-magnitude
  flat, threshold knobs resolution-limited — is the robust, resolution-independent
  result.

**Noise robustness** (secondary): corrupting 5% of decisions and refitting, the
panel still recovers — `mood_bias` r = 0.977, `w_supergraph` sign 100%,
`residual_thresh` within-step 96%, and fitted held-out accuracy 0.943 still beats
population-mean 0.783 and random 0.737. The lapse-likelihood posterior degrades
gracefully.

## 6. G5 — integer-native + default-OFF byte-identity

- **Integer-native (agent side):** every decision the emotion rules produce over
  the entire grid is an exact integer (0 offenders). The knobs and scenario attrs
  are integers. The fit's probability arithmetic is the cross-frame MEASUREMENT
  layer (the model-fitting metric), as the SC+TPS/DTW verdict is continuous — the
  in-frame-integer / cross-frame-real invariant holds.
- **Default-OFF byte-identity:** this rung adds **NO seed, NO rule, NO Rust, NO
  Term**. Canonical `.so` **`793ce09e…` untouched**; a fresh eye has zero emotion
  nodes by default; `seeds/emotion_phenotype.json` does not exist. `term.rs` +
  whole `runners/dsl` diff EMPTY.

## 7. Boundaries (held explicitly)

- **SYNTHETIC-ONLY.** No real behavioural data. Real-behaviour phenotyping is
  dual-use and a deliberately care-gated FOLLOW-ON, OUT OF SCOPE here.
- **The AGENT-SIDE live version** (an agent phenotyping ANOTHER agent in-graph, at
  runtime) is a NAMED follow-on, not this rung. Here the fit is a mechanical
  model-fitting MEASURE (admissible — it validates the model; it adds no agent
  logic to Python).
- **Re-derivation, not invention.** Inverse RL / Bayesian ToM / computational
  psychiatry are established; the contribution is the fit over interpretable,
  mechanistic emotion knobs on the substrate's own landed economy, extending the
  goal-reverse-engineering / abductive-ToM line from GOALS to the full emotional
  baseline.

## 8. Verification

- `test_emotion_phenotype_migrated` **13/13** green.
- Engine-semantics gate set + eye suite + emotion stack (`incremental_match`,
  `empty_match_proof`, `per_sensor_epoch`, `per_area_settlement`,
  `eye_binding_projection`, `staleness_decay`, `demotion_hierarchy`,
  `disorder_glassbox`, `learning_progress`, `core_emotions`, `held_surface`,
  `photon_grapheye`, `vision_eye`, phenotype) — ONE session: **139 passed**
  (the `pytest.mark.slow` UnknownMark warning is pre-existing cosmetic, not a
  failure).
- Oracle `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER (this rung only ADDS
  files — the fixed vision file list is untouched, so identical by construction):
  **214 passed, 10 skipped**.
- Canonical `.so` `793ce09e` UNCHANGED; `source_match = own`; `term.rs` +
  `runners/dsl` diff EMPTY; deterministic across repeated runs.
- Raw: `results/emotion_phenotype.json`; figure `results/emotion_phenotype/recovery.png`.
