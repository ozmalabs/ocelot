# MOOD AS MOMENTUM (+ SET-POINT) — scoping (the slow layer over the fast affect core)

**Status:** scoping only. No numbers, no build, no measurement, no `seed_claim`. Names the
science (search-verified), the graph-native design onto the REAL emotion-core nodes, the
falsification bar, and a pre-registerable rung ladder. Written to be attacked.

**Search availability (instrument discipline):** `WebSearch` + `WebFetch` were LIVE and used
for every scientific claim below (tested as the first action; the momentum paper's model was
pulled from the PMC full text, not a paraphrase). Confidence is labelled per claim. Nothing in
Part A is asserted from priors alone.

---

## 0. The question under the question

The surface ask — *"add mood to the emotion core"* — smuggles a premise: that **mood is one
thing** (either a running tally of how-it's-going, or a slow set-point). It is not. The honest
question is:

> **What is the minimal graph-native addition that makes MOOD a readable two-layer control
> state — a fast-integrating MOMENTUM and a slow-integrating SET-POINT — such that its ADAPTIVE
> value, its cognitive BIAS, and its DISORDER are each separately measurable behind a control
> that can fail?**

Answer that and "the agent has moods" falls out correctly scoped. Anything that only makes the
agent *seem* moody (a scripted swing, a hand-tuned sine) is out of scope until it earns a gate.

The emotion core already has the **fast** layer: `ModulatorState` computes an instantaneous
`valence` every tick from the active drives, and projects it into `AffectiveState`. What is
missing is the **slow** layer — the thing that is still low tomorrow because yesterday went
badly, and that bends how tomorrow's outcomes are *perceived*. That is mood.

---

## 1. PART A — the science, search-verified

### A1. Mood as momentum (Eldar, Rutledge, Dolan & Niv, *TICS* 2016) — HIGH confidence

Verified against the PMC full text (PMC4703769) and the Cell/TICS record, not a paraphrase.
Citation: Eldar E., Rutledge R.B., Dolan R.J., Niv Y. (2016) "Mood as Representation of
Momentum." *Trends in Cognitive Sciences* 20(1):15–24.

The model, in the paper's own terms:

- **Mood is an exponentially-weighted running average of recent reward prediction errors
  (RPEs).** The paper's happiness model (its Box 1) is
  `Happiness_t = w0 + w1·Σγ^(t−j)·CR_j + w2·Σγ^(t−j)·EV_j + w3·Σγ^(t−j)·RPE_j`, with γ an
  exponential forgetting factor, and the RPE weight `w3` empirically dominant over the
  expected-value weight. So mood ≈ a **leaky integral of the signed surprise stream**.
- **Mood biases perceived outcomes ADDITIVELY**, feeding back into learning. The paper's Box 2
  update is `v^s_{t+1} = v^s_t + η_t·(f_t·m_t + r_t − v^s_t)`: the mood/momentum estimate `m_t`,
  scaled by a sensitivity `f_t`, is *added to the actual reward* before the prediction error is
  formed. Positive mood ⇒ outcomes perceived as better than they are.
- **The momentum estimate itself is a leaky integrator of the RPE:**
  `m_{t+1} = m_t + η'_t·((r_t − v^s_t) − m_t)`. This is the exact shape we reuse in Part B.
- **It is ADAPTIVE when environmental returns are AUTOCORRELATED** — "current changes in reward
  predict later changes in reward … many processes in the natural world have such momentum."
  When many states share general environmental factors, tracking one scalar momentum lets
  expectations *anticipate correlated drift* without modelling the shared cause. This is the
  crux of R1: **in an i.i.d. world momentum carries no information and must not help.**
- **High feedback gain ⇒ instability.** When `f_t` (mood→perception sensitivity) is large
  relative to the habituation of learning, the loop self-reinforces: positive surprise → better
  mood → upward perceptual bias → more positive surprise → optimistic expectations → later
  outcomes (now perceived unbiased) fall short → negative surprise → mood collapses → and the
  cycle inverts. The paper states this "could manifest as oscillatory dynamics, as observed in
  bipolar disorder" (its Figure 2B), *even under constant environmental reward*.

### A2. The competing / complementary view — mood as a SET-POINT / average-reward baseline — MEDIUM-HIGH confidence

Three real, independently-sourced strands, each verified:

- **Average-reward RL & tonic dopamine (Niv, Daw, Dayan & Joel 2007, *Psychopharmacology*
  191:507–520, "Tonic dopamine: opportunity costs and the control of response vigor").** In
  average-reward RL the long-run average reward is a **comparison/baseline term subtracted from
  obtained reward** in the prediction-error rule; tonic dopamine is proposed to report this
  average (the opportunity cost of sloth), setting behavioural vigour. Read as affect, this is a
  **slow expected-value-of-the-environment baseline** — "how good is it here, on average" — a
  *level*, distinct from a *change*. (HIGH confidence on the RL claim; the mood mapping is an
  interpretation the source gestures at, MEDIUM.)
- **Behavioural-ecology mood (Nettle & Bateson 2012, *Current Biology* 22(17):R712–R721, "The
  Evolutionary Origins of Mood and Its Disorders"; and the Trimmer/Higginson line).** Mood
  integrates recent environmental state + physical condition to *tune the allocation of
  behavioural effort*, and is adaptive precisely when costs/rewards are **auto-correlated across
  time AND inter-correlated between sources** (e.g. seasonal). Disorders are adaptive mechanisms
  "dysregulated by the stochastic inputs they receive." (MEDIUM-HIGH — verified via the Current
  Biology record + PMC secondary sources; I did not read the full Trimmer models, so the precise
  equations are MEDIUM.)
- **Core affect as a slow baseline (Russell 2003, *Psychological Review* 110(1):145–172, "Core
  Affect and the Psychological Construction of Emotion").** Core affect is a persistent
  valence×arousal neurophysiological state — a *background feeling* with a slow baseline against
  which discrete emotions are constructed. (HIGH on the definition; "slow baseline" phrasing is
  the standard reading, MEDIUM.)

**What each actually claims, side by side:** the momentum view says mood encodes the *derivative*
of value (getting-better-vs-worse-than-expected, a signed RPE integral). The set-point view says
mood encodes the *level* of value (the average-reward baseline / background core affect). These
are **different quantities**, which is what makes "both" testable rather than a dodge (A3, R4).

### A3. The steer: BOTH, co-present and weighted — with a DISCRIMINATING prediction — HIGH confidence in the logic

Per the program's standing rule ("you don't have to choose — both"), mood is designed as **two
co-present layers**, not either/or:

- a **momentum** layer — a fast-ish leaky EMA of the signed valence-RPE (Eldar/Niv `m`);
- a **set-point** layer — a much slower EMA of obtained value, the average-reward baseline
  (Niv/Daw/Dayan; Russell background affect).

They are weighted, not selected. The honest test that keeps "both" from being a fudge is a
**discriminating experiment where the two layers behave DIFFERENTLY** (built in R4):

> After a **step to a new stable level**, momentum spikes transiently then returns to zero (no
> ongoing change ⇒ no momentum), while set-point slowly climbs to the new level and STAYS. So a
> **flat-high plateau** and a **flat-low plateau** are indistinguishable to momentum (both zero)
> but opposite to set-point; a **steady ramp** is invisible to a sluggish set-point but maximal
> to momentum. An agent whose behaviour is driven by only one layer FAILS one of these two
> worlds. That double-dissociation is the evidence for "both."

### A4. Mood-congruent cognition + the clinical extreme — HIGH / MEDIUM confidence

- **Mood-congruent cognition (Bower 1981, *American Psychologist* 36(2):129–148, "Mood and
  Memory").** People recall material affectively congruent with their current mood; mood biases
  judgment and perception in its own valence direction. **Direction:** positive mood biases
  perception/valuation *upward*, negative *downward* — the same additive sign as Eldar/Niv's
  `f_t·m_t` bonus. (HIGH on existence + direction; the associative-network *mechanism* is one of
  several proposed, MEDIUM.)
- **Clinical extreme (Eldar & Niv 2015, *Nature Communications* 6:6149, "Interaction between
  emotional state and learning underlies mood instability"; corrigendum ncomms14149 2017; and
  Eldar et al. 2018 *Current Biology* "Decodability of Reward Learning Signals Predicts Mood
  Fluctuations").** Self-reported mood instability is associated with a **positive-feedback**
  effect of emotional state on outcome perception; simulations show such positive feedback
  destabilises mood. Bipolar/cyclothymic dynamics are read as this feedback-gain runaway — the
  direct empirical anchor for R3. (HIGH — verified via the Nature Communications record + PMC
  full text PMC5338993.)

---

## 2. PART B — the graph-native design (architecture-rule compliant)

**Reuse, do not rebuild.** The design adds ONE new node type and a handful of rules on top of the
REAL, already-landed emotion core. Every update is a rule; Python stays a mechanical adapter; the
canonical `.so` is unchanged. It is **OFF by default** exactly like `modulators` /
`disorder_glassbox` (a `Mood.enabled` guard; absent the opt-in node every existing path is
byte-identical).

### B1. The node it hangs off (real types, read from the seeds)

- `ModulatorState` (`seeds/modulators.json`) — the fast regulator. Computes `valence` each tick
  as `Sum(pleasure) − Sum(displeasure) − Sum(urge)` over `has_active_drive` neighbours, plus
  `arousal / resolution / sel_threshold / securing / competence / epoch`. **This is the fast
  appraisal layer mood sits ABOVE.**
- `AffectiveState` (`seeds/affective_state_core.json`) — the agent-owned control-state vector;
  `ModulatorState` projects into it via the `projects_affect_to` edge (`psi_project_canonical_affect`).
- `Drive` (`seeds/drives.json`) — carries the reinforcers: `pleasure/displeasure = sign(Δc_d)`,
  `value_progress`, `urge`, `urgency`, and is itself a decaying held quantity via the shared
  half-life atom.
- `HeldDecayParams` + the `staleness_decay` primitive (`seeds/staleness_decay.json`) — the
  **per-feature exponential DECAY LAW**: `freshness = Ashr(C0, IDiv(now − last_refresh, half_life))`
  — the integer-exact `×2^−k` (scale2) decay on the epoch axis. `sd_blend` already does a
  precision-weighted Kalman blend of held-vs-new. **Mood's leaky integrators are this atom with
  a long half-life.**
- `HeldDisorderParams` + `disorder_glassbox` (`seeds/disorder_glassbox.json`) — the SIBLING
  pattern: a mental disorder = a **parametric fault on landed machinery**, an explicit
  graph-resident knob, OFF by default, turning the knob restores health. R3 is the mood member of
  this family.

### B2. The new node and its update rules

A single new node, `Mood`, attached to the `EmotionHub` (or `agent_root`) by a `has_mood` edge —
**a READABLE node**, its whole state legible:

- `Mood.momentum` — a **slow leaky EMA of the signed valence-RPE**. Update reuses the
  `staleness_decay` scale2 leak + the `sd_blend` held-vs-new structure verbatim: decay the held
  momentum toward zero over a long `momentum_half_life`, then blend in this tick's signed
  valence-RPE. This is Eldar/Niv's `m_{t+1} = m_t + η'((r−v) − m_t)` expressed in the atoms the
  engine already has.
- `Mood.setpoint` — a **much slower EMA of obtained value** (the average-reward baseline). Same
  machinery, a *much longer* `setpoint_half_life`. This is the Niv/Daw/Dayan comparison term /
  Russell background level.
- `Mood.gain` — the readable **feedback sensitivity** (Eldar/Niv's `f_t`). The disorder knob.
- `Mood.enabled` — the opt-in guard (OFF by default).

**The valence-RPE stream mood integrates** is the engine's own currency: the signed prediction
error on value. In-frame this is the `Drive`'s `value_progress` / `pleasure − displeasure`
signal, or equivalently the tick-over-tick change in `ModulatorState.valence` — the **order-0
residual against the held value expectation, given a sign**. No new signal is invented; mood is a
second consumer of the residual the substrate computes everywhere.

**The feedback rule** (mood → appraisal): a rule reads `Mood.momentum × Mood.gain` and applies it
as an **additive bonus to the perceived valence-RPE** before the drive reinforcers are formed —
Box 2's `f_t·m_t` term, as a graph edge `Mood -biases_appraisal-> ModulatorState/Drive`. Positive
mood biases perception upward, negative downward (A4 direction). The set-point can enter as an
alternative/additional **baseline shift** on the same appraisal (average-reward subtraction),
which is where R4's two-layer interaction lives.

### B3. Momentum = order-1 "velocity of value" (the reuse to NAME)

The eye already infers motion as **order-N momentum**: `TimeInfer` (`runners/dsl/src/term.rs`,
`seeds/time_axis.json`) reads a sequence as an orbit under one transition generator — **order-1
is constant velocity**, higher orders via the dimension-generic finite-difference pyramid
(`shape_decode.rs::diff_pyramid/pyramid_order`). `Mood.momentum` is *that same order-1 machinery
pointed at the reward signal instead of pixels*: the **velocity of value**. The leaky-EMA update
is the extensional, per-tick form of the first finite difference; the conceptual identity is
"mood = the velocity term of the value stream, the eye's motion-inference one domain over." This
also situates it under the frame/continuum invariant: the RPE stream is stepped (integer epoch
axis); mood's continuous-looking EMA is a **cross-frame map** (the decay/blend), never an
in-frame float.

### B4. Does it need new Rust?

**No new Rust Term is required, and none should be added.** `staleness_decay` + `sd_blend` prove
a leaky, precision-weighted EMA is expressible with the existing atoms (`Ashr / IDiv / Plus /
Times / Minus / Max / IfThenElse`); the drive reinforcers already exist; the feedback bonus is an
`Attr × Attr` added at appraisal. The order-1 momentum reading is *conceptually* `TimeInfer`'s
sibling but does not require invoking the Term — the leaky integrator IS the order-1 form. If a
future rung wanted mood to detect *higher-order* value acceleration (order-≥2 momentum), that is
where `TimeInfer`/`diff_pyramid` would be reused directly — still no new Term. **Any proposal to
add a mood-specific Rust primitive is a smell** (see the falsification bar).

### B5. Where it sits in the program

- **Residual-is-the-currency:** mood integrates the signed valence-RPE — the same residual the
  perception, drive, and modulator layers already compute. Mood adds no new signal, only a slow
  reader of the existing one.
- **Two-timescale:** fast appraisal core (`ModulatorState`, instantaneous) + slow mood
  (`Mood.momentum`, longer half-life) + slower baseline (`Mood.setpoint`). The decay half-life IS
  the timescale knob.
- **Disorder-demo sibling:** R3 is the mood entry in the un-dissipated/runaway-residual family
  alongside seizure (residual recruiting), the `disorder_glassbox` obsession/PTSD knobs, and the
  narcissism/psychosis glass-box demos. A high `Mood.gain` is a **runaway feedback** the way a
  mis-set `half_life` is a non-demoting threat — same family, new member.
- **Glass-box differentiator:** `Mood` is a readable node; `momentum`, `setpoint`, and `gain` are
  readable attrs; the `biases_appraisal` edge is visible. You can **watch a swing form and read
  WHY** — the gain that drove it, the RPE stream that fed it. No confabulated "the agent is sad";
  a mechanically-true, inspectable state.

---

## 3. PART C — the rung ladder (pre-registerable, minimal-first; each control CAN fail)

### R1 (HEADLINE) — the adaptive gate: momentum earns reward IFF returns are autocorrelated

- **Falsifiable headline:** an agent WITH the `Mood.momentum` layer + its appraisal feedback
  earns higher cumulative reward than an otherwise-identical agent WITHOUT it — **only** in a
  world whose reward sources are **autocorrelated / drift with momentum**.
- **World (mechanical adapter):** a foraging/bandit world with two switchable regimes — (i)
  **autocorrelated** returns (reward sources drift with momentum, correlated across sources), (ii)
  an **i.i.d.** control world (same marginal reward, zero autocorrelation). The adapter only
  ingests outcomes and emits actions; every decision is a rule.
- **Metric:** cumulative reward, mood-agent vs no-mood agent, CI-separated, in each regime.
- **THE CONTROL THAT CAN FAIL:** in the **i.i.d.** world the mood agent must **NOT** beat the
  no-mood agent (CI-overlapping or worse). If momentum helps in i.i.d. too, it is not tracking
  environmental momentum — it is optimism/noise, and the headline is FALSE. This is exactly what
  separates mood-as-momentum from mood-as-noise.
- **Synthetic-proven vs benchmark value:** synthetic proof = the autocorrelated-beats-iid
  double result on a designed world (mechanism). Benchmark value = a real task with genuine
  reward autocorrelation; reported separately, never conflated.

### R2 — mood-congruent bias, with a zero-gain control

- **Falsifiable headline:** an induced good/bad mood measurably biases the **perceived** RPE /
  the learning of subsequent outcomes, in the mood's own valence direction (A4).
- **Readout (glass-box):** the gap between the perceived valence-RPE (with the `f·m` bonus) and
  the raw residual is a readable quantity; the induced mood shifts subsequent `Drive` valuations
  congruently.
- **THE CONTROL THAT CAN FAIL:** `Mood.gain = 0` — the bias must vanish (perceived = raw, no
  valuation shift). If bias persists at zero gain, it is leaking from elsewhere and the claim is
  ill-posed.
- **Synthetic-proven vs value:** mechanism = the bias appears/disappears with the gain knob;
  value = whether the bias direction/magnitude matches a human mood-congruence effect qualitatively
  (reported as suggestive, not a fit).

### R3 — the disorder demo: gain sweep → stable → cyclothymia → bipolar oscillation (EMERGENT)

- **Falsifiable headline:** sweeping `Mood.gain` upward, **in a CONSTANT environment**, moves the
  mood trajectory from stable → slow cyclothymic drift → sustained bipolar-like oscillation — the
  swing EMERGING endogenously from the feedback gain, per Eldar/Niv 2015.
- **Metric:** endogenous mood oscillation (amplitude / autocorrelation / period) as a function of
  gain, with the environment held constant so any oscillation is internal, not driven.
- **THE CONTROL THAT CAN FAIL:** the **low-gain** arm must stay **stable** in the same constant
  environment. If it oscillates at low gain too, the swing is not gain-driven — it is scripted or
  an artefact, and the demo FAILS. (Mirror of `disorder_glassbox`: snip the coupling / lower the
  knob → health returns.)
- **Glass-box:** you read the `gain` attr and the momentum trajectory and see the swing being
  produced by the feedback, not authored. **It must not be a scripted sine** — that is the named
  failure mode.
- **Synthetic-proven vs value:** mechanism = gain-driven bifurcation from stable to oscillatory;
  value = qualitative match to bipolar phenomenology (period, self-sustaining under constant
  input), reported as an analogy, not a clinical claim.

### R4 — the set-point layer and the discriminating experiment (the "both" test)

- **Falsifiable headline:** adding the slow `Mood.setpoint` layer buys a capability the momentum
  layer alone cannot — and the two layers **double-dissociate** on the A3 worlds.
- **The discriminating experiment (A3):** run the **flat-high vs flat-low plateau** world (tests
  set-point: momentum is zero in both) and the **steady-ramp** world (tests momentum: a sluggish
  set-point misses it). A momentum-only agent fails the plateau discrimination; a set-point-only
  agent fails the ramp anticipation; the two-layer agent handles both.
- **THE CONTROL THAT CAN FAIL:** if the set-point layer adds nothing beyond momentum in **every**
  world (no world where set-point-off loses, CI-separated), then "both" is FALSIFIED for this
  substrate — momentum alone suffices, and the honest report is one layer, not two. Symmetrically,
  a momentum-off arm must lose the ramp world, or momentum is redundant.
- **Synthetic-proven vs value:** mechanism = the double-dissociation on designed worlds; value =
  whether real environments actually present both plateaus and ramps often enough for the second
  layer to pay, reported separately.

### R5+ (named, not scoped here)

Higher-order value momentum (order-≥2, reusing `TimeInfer`/`diff_pyramid` directly — value
*acceleration*); mood's interaction with the `securing`/`competence` modulators (anxious vs
depressive phenotypes as regions, per the `modulators` region-map); social mood contagion across
the glass-box society (mood as a read/emit-able state between agents). Each earns a gate before
it is built.

---

## 4. Falsification bar (binds EVERY rung)

- **EMERGENT, not scripted.** Mood dynamics (a swing, a bias, an adaptive gain) must arise from
  the decay/blend/feedback rules + the RPE stream, never from Python authoring a trajectory. Any
  `if`/`else` in the adapter that *decides a mood value* is an architecture-rule violation. R3's
  swing especially must be produced by the gain, not a scripted sine.
- **GLASS-BOX / READABLE.** `Mood` is a node; `momentum`, `setpoint`, `gain` are attrs; the
  `biases_appraisal` edge is visible. Every reported mood episode must reconstruct from graph
  data — the *why* is a rule you can read, not a narrative.
- **GATED with a FAILABLE control.** Each rung names a control that CAN fail (i.i.d. world;
  zero gain; low-gain stability; set-point-adds-nothing). Above-baseline is not a result;
  CI-separation from the failable control is.
- **GENERAL machinery, not a mood-specific hack.** Mood reuses `staleness_decay` (the decay law),
  `sd_blend` (the Kalman held-vs-new), the `Drive` reinforcers, the `ModulatorState` valence, and
  the order-1 momentum reading — **no new Rust Term.** A mood-only primitive is a smell to refuse.
- **MEASURE-FIRST.** No swing, bias, or adaptive gain is claimed until it is measured behind its
  control. OFF by default; absent the opt-in `Mood` node every existing path is byte-identical.

## 5. Smuggled premises to REFUSE

- **"Mood is just noise / an epiphenomenon."** R1's i.i.d. control is precisely the refutation:
  noise cannot help in an autocorrelated world *specifically*; momentum can. If it only helps
  everywhere or nowhere, it is noise and we say so.
- **"Momentum XOR set-point — pick one."** Refused by design: A3 makes "both" a testable
  double-dissociation (R4), not a fudge. (And R4's control lets "both" be *falsified* down to one
  layer — the steer is co-presence, not a mandate to keep two.)
- **"Script the swing to demo bipolar."** The whole point of R3 is the swing EMERGING from the
  gain knob; a scripted sine proves nothing and is the named failure mode.
- **"Mood is a new sensory signal."** No — mood is a slow reader of the residual/valence-RPE the
  substrate already computes. Inventing a fresh signal hides where mood actually comes from.
- **"Add a Rust primitive for mood."** Refused unless the existing atoms provably cannot express
  it (they can — decay + blend + a bonus). A mood-specific Term violates GENERAL.
- **"Mood = the current emotion."** No — the emotion core (`ModulatorState` regions) is the FAST
  layer; mood is the SLOW integral over it. Collapsing them erases the two-timescale structure
  that is the contribution.

## 6. Prior art (real citations; situate honestly)

- **Eldar, Rutledge, Dolan & Niv 2016**, *TICS* 20(1):15–24 — mood as momentum (RPE integral +
  additive perceptual feedback). The R1/R2 backbone. [HIGH]
- **Eldar & Niv 2015**, *Nat. Commun.* 6:6149 (corrigendum ncomms14149, 2017) — positive
  emotional-state feedback ⇒ mood instability. The R3 anchor. [HIGH]
- **Eldar et al. 2018**, *Current Biology* — decodability of reward-learning signals predicts
  mood fluctuations. [MEDIUM — record verified, full text not read]
- **Niv, Daw, Dayan & Joel 2007**, *Psychopharmacology* 191:507–520 — average-reward baseline /
  tonic dopamine; the set-point layer's RL grounding. [HIGH on RL, MEDIUM on the mood mapping]
- **Nettle & Bateson 2012**, *Current Biology* 22(17):R712–R721 — evolutionary origins of mood;
  adaptive under auto- and inter-correlated returns. The behavioural-ecology set-point. [MEDIUM-HIGH]
- **Russell 2003**, *Psychological Review* 110(1):145–172 — core affect as a slow valence×arousal
  background. [HIGH on definition, MEDIUM on "slow baseline" reading]
- **Bower 1981**, *American Psychologist* 36(2):129–148 — mood-congruent memory/judgment;
  direction of the bias. The R2 anchor. [HIGH on effect + direction, MEDIUM on mechanism]

## 7. Open questions / where the science is contested (honest)

- **Momentum vs set-point is genuinely unsettled** in the literature — they are complementary
  accounts, not a decided winner. Our "both + a discriminating experiment" (R4) is a *design
  stance*, and R4's failable control admits the outcome that one layer suffices in this substrate.
- **The exact RPE the substrate integrates is a modelling choice** (`Drive.value_progress` vs a
  signed Δ`ModulatorState.valence` vs the raw order-0 residual). These need not coincide; which
  one best plays the role of the paper's `(r − v)` is an empirical question the pre-registration
  must pin BEFORE R1, not after.
- **The feedback locus** — additive bonus on perceived RPE (Box 2) vs a set-point baseline shift —
  are two mechanisms A2/A1 each favour; R4 is where they interact, and it is possible they are not
  cleanly separable in-substrate.
- **Does mood's adaptive value survive when the fast `ModulatorState` already tracks value well?**
  Momentum's benefit assumes the fast layer does NOT already anticipate correlated drift; if the
  drive/modulator layer implicitly does, R1's effect could shrink. This is a real risk to the
  headline, named up front.
- **Clinical mapping is an ANALOGY, not a claim.** R3 demonstrates a gain-driven oscillation that
  *resembles* bipolar dynamics per Eldar/Niv; it is not a model of the disorder and must be
  reported as mechanism-analogy, understanding-not-judgment (the `disorder_glassbox` framing).
- **Bias direction is robust; bias MECHANISM is not.** Bower's associative-network account is one
  of several; R2 tests the *effect and direction*, not Bower's specific mechanism.

---

**Bottom line:** mood is the missing **slow layer** over the fast affect core — a readable
`Mood` node carrying a **momentum** (leaky EMA of the signed valence-RPE, the eye's order-1
"velocity of value" pointed at reward) and a **set-point** (a much slower average-reward
baseline), feeding back on appraisal through a **readable gain**. It reuses the landed decay law,
the Kalman blend, the drive reinforcers, and the modulator valence — **no new Rust**. The ladder
is gated the way the program demands: R1's i.i.d. control separates momentum from noise, R2's
zero-gain control isolates the bias, R3 is the disorder-demo sibling where the swing must EMERGE
from the gain, and R4's double-dissociation makes "both layers" a falsifiable claim, not a dodge.
Build for the failable control, not the mood theatre — the swing is only a result once it is
measured behind a knob you can turn back.
