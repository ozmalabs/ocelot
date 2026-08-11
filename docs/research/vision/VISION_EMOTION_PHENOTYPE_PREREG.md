# VISION — REPRODUCE THE EMOTIONAL BASELINE FROM BEHAVIOUR: computational phenotyping by inverse inference (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement
(PROTOCOL §3). Isolated worktree off `main` HEAD **`6a9f5e3ddc`** (LEDGER 204000
`core_emotions` — the emotion knobs + appraisal→action-tendency rules; on 202000
`learning_progress_curiosity`, 199000 `disorder_glassbox`, 196000
`staleness_decay`). Engine canonical **`793ce09ed498a749abb79aeaea44b92e`**
(`_native.abi3.so`, shared build; Rust source identical to this worktree —
`source_match` to be reported). This rung adds **NO Rust** (`term.rs` diff EMPTY,
whole `runners/dsl` diff EMPTY) and **NO new seed** — the synthetic agents decide
via the ALREADY-LANDED 204000/202000/199000/196000 rules; the only new code is a
mechanical inverse-inference MEASURE. Seed block **206000–206999** (reserved for
the panel RNG; `default_rng(206000)`).*

Seed-claim check (verbatim, run before any number):

```
$ python scripts/seed_claim.py 206000 206999
SEED CLAIM 206000-206999: CLEAN -- no collision DETECTED.
  Scope: 905 files with seed sinks; 613 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

---

## 0. FRAMING — the framework's inverse-inference validation; understanding, not judgment

If the 204000 emotion framework is correct — or even close — then a person's
DECISIONS should let you FIT their emotional BASELINE (their knob-vector), and
that baseline should (a) provide a MANIFOLD that PREDICTS their decisions and
(b) EXPLAIN their actions in their own value terms. This is **computational
phenotyping via inverse inference**. It re-derives:

- **Inverse reinforcement learning** (Ng & Russell 2000): recover the objective
  from observed behaviour.
- **Bayesian theory of mind** (Baker, Saxe, Tenenbaum 2009/2017): infer latent
  mental parameters (here the emotion knobs) as a posterior from actions.
- **Computational psychiatry / per-person parameter fit** (Montague, Huys,
  Friston; Huys, Maia, Frank 2016): fit a mechanistic model's parameters to one
  agent's behaviour as a *computational phenotype*, and treat *identifiability*
  as a first-class result — some parameters are constrained by behaviour, others
  only bounded.

**The contribution is not the method.** It is that the fit is over
**INTERPRETABLE, MECHANISTIC emotion KNOBS** on the substrate's OWN landed
emotion economy — so **PREDICTION and EXPLANATION are the same object** (a black
box can predict but cannot attribute an action to a named cause). It extends the
tree's goal-reverse-engineering / abductive-ToM line (LEDGER: goal reverse
engineering) from GOALS to the full emotional baseline.

**Ethical scope, held explicitly.** The **ethical + scientifically-correct FIRST
version is PARAMETER RECOVERY ON SYNTHETIC AGENTS WITH KNOWN KNOBS.** No real
behavioural data is used. Real-behaviour phenotyping is dual-use and a
deliberately **care-gated FOLLOW-ON, OUT OF SCOPE here**. We emulate the
FUNCTIONAL fit (parameters → decisions → recovered parameters); we make NO claim
to felt qualia and pass NO clinical judgment. The graph-native AGENT-SIDE version
(an agent phenotyping ANOTHER agent live, in-graph) is a NAMED follow-on, not
this rung — this rung's fit is a mechanical model-fitting MEASURE (admissible: it
validates the model, like parameter recovery in any modelling study; it is NOT an
agent decision, and it adds no agent logic to Python).

---

## 1. The synthetic agents — KNOWN knob-vectors → GRAPH-NATIVE decisions

A synthetic agent is an `EmotionHub` + a `HeldEmotionParams` node whose attributes
are its **known emotional baseline** — the 204000 knobs. Its DECISIONS across a
battery of appraisal scenarios are produced **graph-natively** by `run_rules()`
over the landed `seeds/core_emotions.json` (which itself reuses the 196000
freshness atom, the 199000 present readout, and the 202000 learning-progress /
value atoms). **The agents deciding is RULES, not Python** (CLAUDE.md): the
measure only sets attrs, ticks, and reads attrs.

**The knob-vector to recover (θ), 4 knobs**, each a named baseline trait:

| knob | 204000 role | governs (rule) | psychiatric analog |
|---|---|---|---|
| `w_supergraph` | supergraph-value weight | `em_fulfilment_value`/`em_fulfilment`/`em_pride` (`> 0` gate) | psychopathy / callousness (knob at 0) |
| `mood_bias` | additive value offset | `em_happiness` + `em_fulfilment_value` (both add it) → `em_total_value` → `em_endorse` | depression (≪0) / mania (≫0) |
| `residual_thresh` | surprise/salience threshold | `em_surprise` (`residual > residual_thresh`) | salience / orienting sensitivity |
| `threat_half_life` | threat-precision persistence | `em_threat_precision` + 199000 present readout → fear (`hit_fear`/AVOID) vs anxiety (`hit_anxiety`/VIGILANCE) | PTSD / anxiety trait |

`w_supergraph`, `mood_bias`, `residual_thresh` live on `HeldEmotionParams` (the
per-agent EP). `threat_half_life` is a trait the generator applies to the agent's
threat appraisals (the 204000 measure sets it per-`Appraisal`); it is the agent's
threat-processing baseline, held constant across that agent's threat stimuli.

**The battery (shared STIMULI; the agent = θ).** Three near-orthogonal scenario
families, each family constraining a disjoint subset of θ (an intentionally
factorial design — the factorisation is itself an identifiability statement):

- **VALUE family** — a sweep of (individual_benefit, individual_cost,
  supergraph_contribution, collective_success) configurations, including the pure
  individual, pure supergraph, the supergraph-harmful-but-individually-good act,
  and the parenthood act (individual-costly, supergraph-beneficial). Observable
  DECISIONS: `act_endorsed` (0/1) and which of {joy, fulfilment, pride, sadness}
  fire. These constrain `w_supergraph` (sign) and `mood_bias` (via the endorse
  threshold `total_value ≥ 0`).
- **SURPRISE family** — a graded sweep of `residual` at fixed `appraised=0`.
  Observable DECISION: does `hit_surprise` fire. Constrains `residual_thresh`.
- **THREAT family** — a fixed threat appraised at a graded sweep of
  `threat_now_epoch` (the per-sensor epoch). Observable DECISION: the action
  tendency (AVOID=fear vs VIGILANCE=anxiety). Constrains `threat_half_life`.

**Observed data per agent** = the vector of DISCRETE decisions over the battery
(action tendency ∈ {1..11}; act_endorsed ∈ {0,1}; per-emotion fire flags). We
observe DECISIONS, never the internal integer values — the realistic
inverse-inference setting.

---

## 2. The fit — a mechanical Bayesian inverse-inference MEASURE

For a candidate θ we **simulate the same graph-native decisions** (build a hub
with EP=θ, run the identical landed rules, read the decisions) and score the
match to the observed decisions. With a small per-decision **lapse rate ε** (a
standard observation-noise term making the posterior smooth, not a delta):

    P(observed_i | θ) = (1 − ε) if predicted_i == observed_i else ε

the log-posterior is `Σ_i log P(observed_i | θ) + log prior(θ)`. Because the
families are near-orthogonal the likelihood FACTORISES
(`L(θ) = L_value(w, mood) · L_surprise(res_thresh) · L_threat(half_life)`), so the
fit is a modest grid: a 2-D grid over (`w_supergraph`, `mood_bias`) against the
VALUE decisions, a 1-D grid over `residual_thresh` against SURPRISE, a 1-D grid
over `threat_half_life` against THREAT. We report the **posterior marginal per
knob** (MAP + a credible interval / spread), never a bare point.

Everything on the AGENT side is integer (knobs, scenario attrs, decisions); the
fit's probability arithmetic is the cross-frame MEASUREMENT layer (the
model-fitting metric), as the SC+TPS/DTW verdict is continuous — the invariant is
respected. Measure module IMPORT-INERT (`main()` only entry).

---

## 3. GATES (pre-registered BEFORE any number)

### G1 — PARAMETER RECOVERY (headline) + the IDENTIFIABILITY map

On a **panel of ≥ 30 synthetic agents** with independently-drawn true knobs
(`default_rng(206000)`), the fitted knob-vector RECOVERS the true knobs.
**PASS iff:** per-knob recovery holds where the design constrains it —
- `mood_bias`: recovered (Pearson `r(true, MAP) ≥ 0.9`, and the true value inside
  the reported credible interval on ≥ 90% of the panel);
- `residual_thresh`: recovered to its interval (MAP within one sweep-step of true
  on ≥ 90% of the panel);
- `threat_half_life`: recovered to its identifiable interval (the fear/anxiety
  boundary correctly located on ≥ 90% of the panel);
- `w_supergraph`: **SIGN recovered** (healthy `> 0` vs psychopathic `= 0`
  classified at ≥ 95%).

**AND the identifiability honesty (equally load-bearing):** report WHICH knobs
recover well vs which are UNDER-IDENTIFIED, as a genuine posterior spread.
**Pre-registered prediction of the identifiability structure:** `mood_bias` is the
best-identified knob (a graded threshold sweep pins it to a tight interval);
`residual_thresh` and `threat_half_life` are threshold knobs identified only to an
INTERVAL (magnitude beyond the crossing is not constrained); **`w_supergraph` is
identified only in SIGN — its magnitude is FLAT (a plateau in the posterior),
because `em_fulfilment_value` gates on `w_supergraph > 0` and does NOT scale by
it, so every positive value produces byte-identical decisions.** This flat
plateau is the correct, honest result — an ill-posed magnitude reported, not
hidden. If a knob we predicted would recover does NOT, that is reported straight
(G4).

### G2 — PREDICTION / THE MANIFOLD (held-out)

Split the battery into TRAIN and HELD-OUT scenarios (the held-out set the fit
never saw). The fitted baseline (MAP θ) PREDICTS the held-out decisions.
**PASS iff** held-out decision accuracy under the fitted θ EXCEEDS both controls:
(a) the **population-mean** knobs (the panel-mean θ, a single "average person")
and (b) **random** θ (drawn from the prior). Report held-out accuracy for fitted
vs both controls, per agent and panel-mean, with the fitted strictly higher.

### G3 — EXPLANATION (interpretable attribution)

The fitted knobs ATTRIBUTE actions to the right causes in the agent's OWN value
terms, shown by **counterfactual on the fitted knob**. **PASS iff:**
- a low-`w_supergraph` (psychopathic) agent's ENDORSEMENT of the
  supergraph-harmful-but-individually-good act is attributed to `w_supergraph`:
  under the fitted θ the act is endorsed, and flipping ONLY the fitted
  `w_supergraph` to healthy flips the decision to DECLINE (ties 204000
  psychopathy);
- a high-supergraph-valuing ("parent") agent's endorsement of the
  individually-costly, supergraph-beneficial act is attributed to its supergraph
  valuing: under the fitted θ the act is endorsed, and zeroing the fitted
  `w_supergraph` flips it to DECLINE (the "irrational" supergraph-costly act
  explained BY the knob).
The fitted model assigns each distinctive action to the CORRECT knob (the
counterfactual isolates it).

### G4 — THE FALSIFICATION TEST (framed honestly)

This rung IS the framework's test. If recovery (G1) + held-out prediction (G2)
hold, the emotional-baseline model is validated as a per-agent phenotype. If a
knob does NOT recover, or prediction FAILS, or the identifiability structure
differs from the pre-registered prediction, it is reported STRAIGHT — a null is
valuable evidence about the framework's identifiability/limits. Specifically we
will state, per knob: recovered / interval-recovered / sign-only / ill-posed, and
whether the pre-registered identifiability prediction held.

### G5 — INTEGER-NATIVE + DEFAULT-OFF byte-identity

The AGENT side is integer-native (knobs, scenario attrs, and every decision the
rules produce are exact integers; no float Term enters an emotion rule — inherits
204000 G5). Default-OFF: this rung adds NO seed, NO rule, NO Rust; the substrate
is byte-identical with the rung absent (canonical `.so` untouched; `term.rs` +
whole `runners/dsl` diff EMPTY; oracle `rung7_vision_bench` BEFORE == AFTER).

---

## 4. DISCIPLINE (declared here, enforced at report)

- **Prefer graph-data + EXISTING Terms.** NO new Rust, NO new seed. `term.rs` diff
  EMPTY; whole `runners/dsl` diff EMPTY. The agents' decisions are the landed
  204000/202000/199000/196000 RULES; the fit is a Python MEASURE (mechanical
  model-fitting — sets attrs, ticks, reads attrs, scores; no agent decision).
- **Measure module IMPORT-INERT** (nothing at import; `main()` only entry; scoped
  context only).
- **Engine-semantics gate set (lesson 12)** — this rung touches NO engine, but the
  gate set is run anyway (adapter-only): `test_incremental_match`,
  `test_empty_match_proof`, `test_per_sensor_epoch`, `test_per_area_settlement`,
  `test_eye_binding_projection`, `test_staleness_decay`, `test_demotion_hierarchy`,
  `test_disorder_glassbox`, `test_learning_progress`, `test_core_emotions`, the eye
  suite, and `held_surface`. All green. (The pre-existing `test_eye_timing`
  wall-clock-ratio flake ~1.75–1.8 vs >2.0 is the KNOWN flake — loads none of
  these seeds, not in the oracle; if seen, reported as the known flake, not
  chased.)
- **Canonical `.so`** stays `793ce09e…` (seed/Python-only; verify md5 untouched).
- **Oracle** `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER.
  **`source_match` own/shared** reported. **Commit before report.** Do NOT merge to
  main; do NOT touch `VISION_PROTOCOL.md`.

## 5. What would falsify / an honest negative

- A knob predicted to recover (`mood_bias`, `residual_thresh`, `threat_half_life`)
  that does NOT recover on the panel — reported straight, not tuned.
- Held-out prediction under the fitted θ that does NOT beat the population-mean /
  random controls — would falsify the manifold claim.
- The counterfactual attribution FAILING to isolate the right knob (flipping the
  fitted `w_supergraph` does NOT flip the psychopath's/parent's decision) — would
  falsify the explanation claim.
- An identifiability structure DIFFERENT from the pre-registered prediction (e.g.
  `w_supergraph` magnitude turns out identifiable, or `mood_bias` turns out
  ill-posed) — reported straight.

An honest measured negative on any of these is a valid, valuable landing; the
deliverable is the MEASUREMENT behind a protected gate, not a green light.
