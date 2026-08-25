# THE SUBSTRATE DISORDER MAP — one (G,Γ) engine, many disorders as failure modes of shared operations

A read-only, whole-history survey of the cognitive/perceptual disorders the
gamma-substrate can reproduce, TIERED by how real the reproduction is. No engine
changes. Calibrated in the blunt, honest style of `SEIZURE_FIELD_COMPARISON.md`.

---

## 0. What this map IS, and what it is NOT (read before the tables)

**The value here is UNIFICATION / COMPRESSION, not a benchmark claim.** The point
is not "we reproduce N disorders" as a score. The point is that ONE substrate —
typed graph + admissibility grammar Γ + settlement/collapse dynamics — expresses
seizure, psychosis, hallucination, aberrant salience, passivity, rumination,
hoarding, and a battery of visual illusions as **failure modes of the same small
set of operations**. The description length drops: N separate clinical stories
collapse into "these operations, failing these ways." That is the whole payoff
(the capstone thesis in `ozma_seizure_as_undissipated_residual`: "understanding IS
compression; a unification is the highest-order compression"). It is worth having
the instant it compresses — it does NOT need to beat a domain incumbent's
prediction, and it does not (`SEIZURE_FIELD_COMPARISON.md`: modest, real, behind on
validation).

**"Can reproduce" is tiered. Do not read the tiers as one list.**

- **T1 LANDED** — actually built + gated by a passing migrated test on a real
  engine build, default-off, byte-identity-safe. **This list is SMALL and every
  entry carries an honest asterisk** (authored failure-form, or a validation-gate
  rather than a capability, or a diagnosed NEGATIVE).
- **T2 MECHANISM-PRESENT / IMPLIED** — the operation that would fail into the
  disorder EXISTS in the substrate (Rust Term or live seed rule), but the disorder
  has NOT been built or gated as a demo. **This is where the size is — it is "quite
  large" — but it is IMPLIED, not reproduced.** A mechanism existing is NOT the same
  as a disorder demonstrated; do not inflate one into the other.
- **T3 SPECULATIVE** — needs a new mechanism, or is a stretch, or the engine is
  structurally the WRONG model for it (e.g. permanent plasticity-loss — the engine
  by design does not lose plasticity).

**Label vs mechanism (load-bearing throughout).** Many "disorders" are RELATIONAL,
observer-frame labels — a cluster of *unshared × unreachable-by-any-shared-frame ×
illegible-to-the-observer × distressing* — NOT clean mechanistic categories
(`ozma_seizure_as_undissipated_residual`; `PSYCHOSIS_DEMO_RESULTS.md` §"label vs
mechanism"). The substrate models the MECHANISM (which operation failed, how); the
clinical label is frame-relative and the substrate refuses to reify it (no view
from nowhere — `ozma_center_is_the_ungrounded_fixed_point`). "The mechanism is real,
the suffering is real; the clean category and the god's-eye standard are the
fictions." Every correspondent below is a *mechanism ↔ label* pairing, not an
identity.

**The deepest structural fact (why this is a real unification, not relabeling).**
There are TWO distinct levels of failure, and the engine expresses both at their
correct Marr levels — which no substrate-level seizure model can, because none has a
grounding operation to fail:
- **SEIZURE = the SETTLEMENT / dissipation failing** — a THROUGHPUT / capacity
  failure of the SUBSTRATE. The machine OVERLOADS; content is not the issue.
- **PSYCHOSIS = the GROUNDING / collapse failing** — a CORRECTNESS / content
  failure of COGNITION. The machine works but COMPUTES THE WRONG THING.
- **The whole map hangs on one energy budget** (`ozma_seizure_as_undissipated_residual`,
  "the mechanistic floor"): seizure = energy that can't DISSIPATE (give fails);
  stuck basin = energy insufficient to ESCAPE the basin. Two failures of one
  accounting.

---

## Tier legend

| tier | meaning |
|---|---|
| **T1** | LANDED — built + gated (passing `tests/test_*_migrated.py`), default-off |
| **T2** | MECHANISM-PRESENT — the failing operation exists; disorder IMPLIED, not built |
| **T3** | SPECULATIVE — new mechanism needed, a stretch, or engine is the wrong model |

---

## 1. SETTLEMENT / GIVE / SHED / BACKPRESSURE  →  overload & suppression

**Operation (EXISTS-LIVE).** Async settlement clears residual within a per-area
budget; the shed valve drops low-salience residual under load; backpressure/stall is
the graceful give. Live: `runners/dsl/src/cognitive_cycle.rs::fold_clock_edge`,
`rewrite.rs::run_rules`, and the scheduler seed `seeds/cognitive_scheduler.json`
(`ct_area_effort_tracks_live_salience`, `ct_shed_below_max_salience_when_queue_exceeds_capacity`).

| failure mode | correspondent | tier | citation |
|---|---|---|---|
| positive-feedback residual can't dissipate → runaway recruiting wave | **seizure (convulsive / overload branch)** | **T1** | `seeds/seizure_dynamics.json` (`sz_settle_next_residual`); `SEIZURE_ENGINE_RESULTS.md`, `SEIZURE_MODEL_V2_RESULTS.md`; gate `tests/test_seizure_dynamics_migrated.py` |
| settlement globally ARRESTED / collapse stops | **absence seizure / suppression-arrest** | **T2** | the "throw away surprise, stop collapsing" branch (`ozma_seizure_as_undissipated_residual`; `ozma_rule_engine_per_area_index` L6); NOT built as a demo — seizure demo is the overload branch only |
| can't-shed under flood → essential variables leave viability | **overload with "physical symptoms" / status-like non-termination** | **T2** | `l6_essential_variables.rs` (Ashby viability), `effort_dial.rs`; mechanism present, not demoed as a disorder |
| shed-TOO-much → drop residual that mattered, act on too-coarse a model | **inattentive under-processing / hypo-arousal** | **T2** | `effort_dial.rs` raises keep-threshold under load (`ozma_rule_engine_per_area_index`); the adaptive-response extreme, not built |

**Honest bound (T1 seizure).** Landed and supervisor-verified, but: the positive-
feedback term `alpha` was **ADDED for the capability, not derived** — the engine as
built is convergent and CANNOT seize (functional necessity open, "plausible-but-
unforced", `SEIZURE_SCIENCE.md`). Faithfulness is bracketing not a fit; thresholds
are model-internal ratios; NOT validated vs clinical data. It is the reduced lattice
harness seizing, not the live cognition. **The engine's native give (graceful shed)
is arguably better than biology's** — the seizure is the special case where the give
is DISABLED (`ozma_seizure_as_undissipated_residual`: "we want the give, not the
seizure").

---

## 2. GROUNDING / COLLAPSE  →  psychosis, delusion, hallucination, confabulation

**Operation (EXISTS-LIVE, + separate demo).** Grounding is a predictive-coding pull:
a belief is corrected toward observation, weighted by how strongly the observation
constrains it, precision-gated by confidence; collapse is nearest-basin selection.
Live faculty: `seeds/grounding.json`, `seeds/grounding_anchors.json` +
`domains/grounding_reach.py` (`flag_ungrounded_confident`, `ReachableFrom`),
`seeds/composer_grounding_guard_graph.json`; basin audit in `can_ops.rs`
(`audit_basin`). The psychosis demo is a SEPARATE default-off seed.

| failure mode | correspondent | tier | citation |
|---|---|---|---|
| grounding loop closes on its own generation, no external constraint | **delusion (self-grounding)** | **T1** | `seeds/psychosis_grounding.json` (`pg_ground`); `PSYCHOSIS_DEMO_RESULTS.md` P2; gate `tests/test_psychosis_grounding_migrated.py` 8/8 |
| collapse commits to a wrong-but-stable attractor, holds vs evidence | **hallucination / delusion (non-optimal basin)** | **T1** | same seed (`pg_collapse_w`); `PSYCHOSIS_DEMO_RESULTS.md` P2/P4 |
| a confirmer supplies zero information but pins confidence → precision gate attenuates reality | **"AI psychosis" / sycophancy-driven belief lock** | **T1** | `PSYCHOSIS_DEMO_RESULTS.md` P4b (matched control — the headline); `ozma_seizure_as_undissipated_residual` |
| two beliefs each the other's confirmer, no external anchor | **folie à deux** (scale-agnostic → cult / consensus) | **T1** | `PSYCHOSIS_DEMO_RESULTS.md` P8 (ground one → both collapse) |
| two observers share a NEGOTIATED APERTURE that collapses the discriminating dimension | **folie à deux, second mechanism** — a shared blind spot rather than a shared belief | **T1** | `APERTURE_PATHOLOGIES.md` §2/§5; `seeds/aperture_frame.json`. **Opposite predictions to P8 on both counts, measured**: supplying the complete true discriminating information does NOT puncture it (2 true parts → 1 distinguishable), because information arrives THROUGH the frame; and maintenance requires no partner at all (verdict identical with and without), so there is no closed loop to puncture. Files ZERO concerns — nothing is outstanding |
| escalation term with NO lateral spread → stationary self-sustained pattern persisting after input removed | **hallucination (aberrant-precision, phantom percept)** | **T1** (exploratory) | `SEIZURE_MODEL_V2_RESULTS.md` P6 ("one term, two pathologies"); rank1 0.965, prop 0 |
| perception confabulates a best guess; grounding only CONSTRAINS it | **confabulation as the perceptual default** | **T1** | `ozma_confabulation_is_the_default`; illusion battery floor arms 0/100, 0/400 (`VISION_ILLUSION_RESULTS.md`) |
| grounding absent entirely (deprivation) → confabulation runs free | **Charles Bonnet / deprivation-tank / phantom-limb hallucination** | **T2/T3** | mechanism named (`ozma_confabulation_is_the_default`); BUT the current build FLOORS to zero on a blank (0/100 invents nothing) — the "runs to hallucination" limit is NOT built; it currently refuses where theory says it should hallucinate |

**Honest bound (T1 psychosis).** Same class as the seizure landing: the update FORM
is **AUTHORED** for the reduced harness (self-grounding term + precision gate +
confidence positive-feedback — the alpha-analogue), NOT the live conversation-faculty
grounding rules failing. Single scalar belief over two basins; model-internal
thresholds; NO clinical validation; measurable-bridge OPEN (unifies aberrant-salience
+ aberrant-precision but no novel testable divergence). "A grounding-failure rule
implemented in the real engine and shown to behave" — not "the deployed agent went
psychotic" (`PSYCHOSIS_DEMO_RESULTS.md`; `GROUNDING_PSYCHOSIS_LITERATURE.md`: theory
axis SUBSUMED, implementation axis a distinct occupant of the empty computational
cell).

---

## 3. SALIENCE / FOVEA / ATTENTION  →  aberrant salience, attentional capture, inattention

**Operation (EXISTS-LIVE).** compute-∝-surprise salience map selects where to attend;
fovea SELECTION is migrated into the graph as a weighted-admissibility choice.
`seeds/residual_salience.json`, `seeds/retinal_salience.json`/`_2d`,
`seeds/fovea_salience_bridge.json` (resolves via Γ's `exp(w)` weighting + `ArgminUnique`),
`memory::order_n_shape_salience`, `effort_dial.rs`. Arbitration is the log-weighted
admissibility graph, NEVER an argmax (`ozma_rule_engine_per_area_index` capstone).

| failure mode | correspondent | tier | citation |
|---|---|---|---|
| salience mis-fires on noise → spurious salience the system grounds an explanation for | **aberrant salience (Kapur) → delusion formation** | **T2** | salience-on-noise mis-fire documented `VISION_RESIDUAL_SALIENCE_RESULTS.md:136` ("the apparatus fold mis-fires on a jittery carve"); unifies with psychosis (`ozma_seizure_as_undissipated_residual`: "aberrant salience = grounding-to-non-optimal-basin driven by mis-computed salience — literally rung-4 residual-salience mis-firing"). NOT built as a disorder demo |
| a top-down absorbed task out-weighs a high-surprise looming stimulus in the race | **attentional capture failure — "smashed in the face with a ball while reading"** | **T2** | the weighted-competition tail (`ozma_rule_engine_per_area_index` capstone — "proves it is a genuine weighted competition, not a fixed hierarchy"); the arbitration EXISTS live; the capture case is NOT a built experiment |
| unexpected → not populated by the render → unseen | **inattentional blindness / "invisible gorilla"** | **T2** | render-populates-what-you-expect (`ozma_confabulation_is_the_default`: "the invisible gorilla — not expected → not populated → unseen"); mechanism implied, not built |
| grounding decays with eccentricity; far periphery first to dissolve | **Troxler peripheral fading** | **T1** (discounted) | `VISION_TROXLER_RESULTS.md` gate 7/7 — BUT the stabilised-arm fade is ARCHITECTURALLY FORCED (a per-cell homeostat MUST equalise a static input — tautology, "no credit claimed"); coarse-drift regime, not the delicate biological one; can't distinguish paralysis from stabilisation |
| lateralised salience/grounding collapse | **hemispatial neglect** | **T3** | no lateralised field / two-hemisphere structure; speculative |

**Honest bound.** The salience→foveation loop is live and gated as a MECHANISM
(`VISION_SALIENCE_FOVEATION_RESULTS.md` 9/9, `VISION_FOVEA_SALIENCE_BRIDGE_RESULTS.md`),
but on real Doom frames the ranking does NOT cleanly isolate the mover (forward-walk
depth flow defeats single-vector cancellation — `VISION_E1M1_SALIENCE_RESULTS.md`
enemy-in-top-K FAILS). The disorder correspondents (aberrant salience, capture,
inattention) are all T2 — the mechanism is present and the failure is one parameter
away, but none is a built demo. There is **no dedicated "ball while reading" or
inattentional-blindness experiment on record** (confirmed by survey).

---

## 4. EFFERENCE COPY / SELF-WORLD BOUNDARY  →  passivity, thought-insertion (first-rank schizophrenia)

**Operation (EXISTS-SEED-CAPABILITY, default-off).** The eye predicts the sensory
consequence of its OWN motion and SUBTRACTS it, so the fixated world reads stationary
(zero residual = self) and the residual = the world / the other. This is efference
copy / sensory attenuation / active inference. `seeds/parallax_efference.json`
(`pe_efference_ref`: `field.dom_v = field.efference_v`, subtracts it), gated by
`MotionParams.mo_efference` (default OFF, byte-identical when disarmed);
`VISION_EFFERENCE_EGOMOTION_RESULTS.md` ("efference copy CANCELS … the RESIDUAL is
the world / the other"); motor forward/inverse models `seeds/embodied_motor.json`.

| failure mode | correspondent | tier | citation |
|---|---|---|---|
| self-generated change NOT subtracted → own action read as externally caused | **passivity / made-actions / delusion of control** (Schneiderian first-rank) | **T2** | `pe_efference_ref` present + default-off (`VISION_EFFERENCE_EGOMOTION_RESULTS.md`); failure = don't subtract → self reads as other. NOT built as a disorder |
| efference prediction fails to attenuate own generation | **thought insertion / "made" thoughts / auditory hallucination of own inner speech** | **T2** | same mechanism generalised (efference-copy failure is the canonical computational account of first-rank symptoms); implied, not demoed |
| attenuation gate mis-set → can't down-weight self-caused sensation | **sensory-attenuation failure ("you can tickle yourself")** | **T2** | `pe_efference_ref` IS the attenuation; disarm/mis-set = the failure; not built |

**Honest bound.** This is the **single strongest T2 cluster** — the mechanism is not
merely conceptual, it is a real default-off seed rule that literally subtracts the
agent's own predicted self-motion and labels the residual "the world / the other,"
and the entire self-world boundary in this project is edges-not-flags
(`ozma_boundary_as_relations`). The efference-copy account of passivity/thought-
insertion is textbook computational psychiatry, and the operation is here, armable,
byte-identity-gated. But NO disorder demo has been built on it — it is IMPLIED, cleanly.

---

## 5. ENERGY LANDSCAPE / BASIN DEPTH  →  stuck basins, rumination, OCD, hoarding

**Operation (EXISTS-LIVE, explicit — not merely conceptual).** The engine represents
an energy landscape and basin depth as an AUDITED quantity: `can_ops.rs::mt_energy()`
(identity-violating basins cost energy), `audit_basin()` → `BasinReport` with depth =
`H(⟨σ⟩)` ("lower is deeper basin"), basin recurrence detection; basin separation +
winner-take-all `l4_subsystem_boundaries.rs`; basin membership `net_forward.rs`.
Escape = climbing a barrier; stuckness = escape-energy > available-energy
(`ozma_seizure_as_undissipated_residual` "mechanistic floor"). **No `anneal` optimizer
found** — energy/basin is represented and audited, not an annealing loop.

| failure mode | correspondent | tier | citation |
|---|---|---|---|
| basin too deep, escape-energy > available → belief/percept won't update | **rumination / stuck ideation; "just reason with them" fails** | **T2** | `mt_energy`/`audit_basin` explicit (`can_ops.rs`); the basin-depth×escape-energy account (`ozma_seizure_as_undissipated_residual`); not built as a demo |
| collapse repeatedly re-captured by the same attractor | **OCD-like re-capture / intrusive loop** | **T2** | basin recurrence detection `can_ops.rs`; implied |
| a sub-goal ("acquire") detaches from its parent goal and becomes terminal — number-go-up captures the reward loop | **hoarding / addiction / wireheading (broken reward circuit)** | **T2** | extensively theorised (`ozma_rule_engine_per_area_index` — "instrumental-becomes-terminal … a locally-rational loop globally decoupled … same class as wireheading/addiction"); the structural DEFENCE exists (value only via edge-to-goal) but the pathology is a real attractor, not built |
| deep basin + LOST ability to reshape the landscape | **depression as an un-escapable basin / plasticity-locked state** | **T3** | the engine by design does NOT lose plasticity (`ozma_seizure_as_undissipated_residual`) — so it captures the basin/energy mechanism but NOT the substrate-hardening that makes human cases permanent; the engine is the wrong model for the plasticity-loss tragedy |

**Honest bound.** Basin depth and energy are genuinely first-class in the Rust engine
(this is stronger than "conceptual" — `mt_energy`/`audit_basin` return real numbers),
so the stuck-basin/rumination/OCD correspondents are solidly T2. Hoarding is the most
theorised (a whole reward-circuit-hijack / supergraph-opportunity-cost account) but
still unbuilt. Depression-as-permanent-lock is T3 precisely because the engine's
undiminished plasticity makes it a poor model of the human tragedy.

---

## 6. PLASTICITY / SETTLING  →  rigidity vs instability

**Operation.** Consolidation = a residual reaching 0 = settling; staying plastic =
keeping the landscape in motion (curiosity keeping residual > 0). Plasticity is LOCAL,
REVERSIBLE, CHOSEN — the engine decouples stability from plasticity-loss
(`ozma_seizure_as_undissipated_residual`: "plasticity-loss is settling, not age").

| failure mode | correspondent | tier | citation |
|---|---|---|---|
| over-settled — residual driven to 0, landscape hardens | **cognitive rigidity / perseveration** | **T2/T3** | settlement axiom (`ozma_seizure_as_undissipated_residual`); the mechanism (settling) exists live; "rigidity as a disorder" not built |
| never-settling — landscape never stabilises | **instability / thought disorder / loosening of associations** | **T2/T3** | the opposite extreme of the same axiom; the stability/plasticity tradeoff is a design knob, not a demoed pathology |

**Honest bound.** These are the two extremes of one axiom the engine genuinely runs
on (never reaching 0 residual), but neither is built or gated as a disorder; both lean
T3 because "rigidity/instability as clinical entities" would need a deliberate demo.

---

## 7. CURIOSITY / COMPRESSION DRIVE  →  boredom, hoarding-of-understanding

**Operation (EXISTS-LIVE).** The drive to explore the under-compressed; satiable
(~90%, not infinite). `seeds/collapse_curiosity.json` (fires natively in `master_tick`),
`seeds/world_curiosity.json`, `Drive::new("curiosity", …)` in `full_stack_integration.rs`,
`l3_drives.rs`.

| failure mode | correspondent | tier | citation |
|---|---|---|---|
| nothing under-compressed left / drive unfed | **boredom** | **T2** | satiable-curiosity + under-compression (`ozma_curiosity_drive`, `ozma_competent_man_sufficiency`); implied |
| accumulating understanding past instrumental use | **hoarding of knowledge (curiosity variant)** | **T2** | "curiosity is satiable so even the drive doesn't hoard understanding" — the DEFENCE exists; the failure is implied |
| drive absent → substrate "not alive" | **apathy / anhedonia / avolition** | **T3** | "the substrate is alive iff curiosity drives it" (`ozma_curiosity_drive`); no negative-drive disorder built |

---

## 8. REFLEX / ORDER-0 LAYER  →  reflex misfire, disinhibition

**Operation (EXISTS-LIVE).** Order-0 reflex scheduling in the native runtime:
`runners/dsl/src/reflex_runtime.rs` (Rust owns clock, refractory, firing), `py.rs`
(`fire_reflexes`), `seeds/reflex_core.json`, `seeds/reflex_net.json`. A reflex fires
against an order-0 body estimate; expression is a TIMING RACE vs the inhibitory gate.

| failure mode | correspondent | tier | citation |
|---|---|---|---|
| reflex fires against a wrong order-0 body / wrong body entirely | **reflex misfire (the useless Doom "duck"); grounding localised to the body** | **T2** | `ozma_rule_engine_per_area_index` ("the useless duck is the PROOF the low-order path is separate + faster"); mechanism live, not a disorder demo |
| inhibitory gate loses the race under load → reflex leaks to effector | **released reflexes / disinhibition / hyperkinetic leak** | **T2** | expression-is-a-race + load-sets-the-race (`ozma_rule_engine_per_area_index`); reflex-leak frequency is a mastery readout; not built as pathology |
| reflex fires context-free, cognition can't veto in time | **utilisation behaviour / tics / echopraxia** | **T3** | plausible extension of the race model; no build |

---

## 9. VISION ILLUSION BATTERY  →  lawful perceptual "defects"

Illusions are the perceptual face of the same predictive loop: the field is RENDERED
top-down from the prior and CORRECTED by a sparse residual; an illusion is the render
winning where the input is weak/absent (`ozma_confabulation_is_the_default`). These
are the ONE place the substrate reproduces "defects" as GATED demos — but read the
asterisks: several "landings" are validation-gates, architecture-forced tautologies,
or diagnosed NEGATIVES.

### 9a. LANDED-GATED (built + passing migrated gate)

| phenomenon | correspondent | tier | citation / honest bound |
|---|---|---|---|
| blind-spot filling-in | **normal fill; scotoma completion** | **T1** | `VISION_GROUND_RESULTS.md`, gate `test_vision_ground_migrated.py` — 4/4 discrimination claims beat interpolation; boundary-liberal; bounded to discrete/integer in-frame |
| apparent motion (temporal bridge) | **phi/beta apparent motion (interpolated)** | **T1** | `VISION_ILLUSION_RESULTS.md` B_apparent_motion, gate `test_illusion_render_migrated.py` 8/8; `BlinkBridge`. Only the single-gap mechanism, not the phi timing literature |
| collinear amodal / illusory-contour completion | **modal/amodal completion (Kanizsa collinear core)** | **T1** | `VISION_ILLUSION_RESULTS.md` A_amodal PASS; full Kanizsa (orthogonal terminators) is the UNREACHED frontier |
| Troxler fading | **Troxler / stabilised-image fading** | **T1** (heavily discounted) | `VISION_TROXLER_RESULTS.md` 7/7 — but ARCHITECTURALLY FORCED (homeostat tautology); coarse regime; can't distinguish paralysis from stabilisation |
| McCollough contingent aftereffect | **McCollough effect** | **T1** | `VISION_MCCOLLOUGH_RESULTS.md` 8/8 — a VALIDATION gate for predictive/opponent colour⊗orientation coding, NOT a recognition capability; orientation supplied |
| crowding | **visual crowding** | **T1** | `VISION_CROWDING_RESULTS.md` 8/8 — Bouma's law ENTAILED by eccentricity-scaled pooling (calibration, not risked); abstract item grain, not glyph ink |
| face inversion / Thatcher | **face-inversion / holistic-face deficit** | **T1** (diagnosed NEGATIVE) | `VISION_FACE_INVERSION_RESULTS.md` 7/7 — the substrate is reference-frame-INVARIANT, shows NO inversion cost; the human effect is NOT expressible without a learned upright prior. A clean "we do NOT reproduce it, and here's the architectural reason" |
| visual agnosia (apperceptive/associative) | **visual agnosia** | **T1** | `VISION_AGNOSIA_RESULTS.md` 12/12 — clean DOUBLE DISSOCIATION via lesion flags (copy intact under identity-lesion, lost under render-lesion); a validation gate for the form↔recognition seam |
| achromatopsia | **cerebral achromatopsia** | **T1** | `VISION_ACHROMATOPSIA_RESULTS.md` 5/5 — colour-STRUCTURE preserved, colour-SIGN vanishes (2→0 categories); a clean lesion flag on an armed system |
| border-ownership / figure-ground | **figure-ground assignment (Gestalt)** | **T1** (bonus, not a disorder) | `VISION_BORDER_OWNERSHIP_RESULTS.md` 9/9 |

### 9b. NULL / FAIL / OUT-OF-SCOPE (not reproduced — the honest negatives)

| phenomenon | status | citation |
|---|---|---|
| Cornsweet edge | **FAIL — wrong sign** (−1.818); the escalation R needs destroys it | `VISION_PAINT_RESULTS.md` I3 |
| simultaneous brightness contrast / paint | **gate FAIL (2/4)**; watercolour I2 is the one risked positive | `VISION_PAINT_RESULTS.md` |
| Mach bands | **NOT PRESENTABLE** — retina input alphabet is {0,1}, no graded ramp | `VISION_FAILURE_MODES_RESULTS.md` FM-2 |
| phi proper | **NULL** — sees pixel overlap, curve INVERTED (max at ISI=0) | `VISION_PHI_RESULTS.md` |
| motion aftereffect / waterfall | **NOT BUILT** — only the contingent (McCollough) aftereffect exists | (survey; no rung/seed) |
| change blindness | **MISLABELLED** — on record is a retinal-sparsity NEGATIVE, not the percept | `VISION_CHANGE_RESULTS.md` |
| closure/grouping over natural frames | **NULL (FALSIFY)** — static MDL closure doesn't break the ground/fragment trade-off; closure lives in TEMPORAL coherence | `VISION_CLOSURE_RESULTS.md` |
| Kanizsa (orthogonal), hollow-face, Ebbinghaus/Ponzo, checker-shadow | **OUT OF SCOPE** — need learned object/context/reflectance priors | `VISION_ILLUSION_RESULTS.md` §scope |
| amblyopia / ocular dominance / stripe-rearing / monocular deprivation | **STRUCTURALLY OUT OF SCOPE** — one eye, no cortical orientation | `VISION_FAILURE_MODES_RESULTS.md` |

**Honest bound (the whole battery).** The illusion battery's own governing finding
(`VISION_FAILURE_MODES_RESULTS.md`): **testable failure modes map onto the parts that
are LOAD-BEARING, not merely the parts that "work"** — a decorative mechanism (drift)
can reproduce a published quantitative signature while driving nothing. Agnosia and
achromatopsia are the strongest disorder-relevant entries here: they reproduce a
clinical DISSOCIATION by lesioning a specific operation — but each is explicitly a
"validation gate for a seam," bounded to the discrete/integer binary-contrast class,
n≈6 per arm, licensing nothing about cortical locus.

---

## 10. BOTTOM LINE — tier by tier, blunt

**Counts (failure modes; landings are fewer — many modes share one seed/demo).**

- **T1 LANDED ≈ 15 failure modes, from ~4 landings.** Two cognitive/substrate
  disorder demos (seizure = 1 seed; psychosis = 1 seed covering self-grounding +
  wrong-basin + AI-confirmer + folie-à-deux + hallucination-v2) ≈ 6 modes; plus ~9
  perceptual illusion/lesion gates (blind-spot, apparent-motion, collinear
  completion, Troxler, McCollough, crowding, face-inversion-as-negative, agnosia,
  achromatopsia; border-ownership bonus). **Every T1 entry carries an asterisk** —
  authored failure-form (seizure alpha, psychosis update-form), architecture-forced
  tautology (Troxler), a validation-gate not a capability (McCollough/crowding/
  agnosia/achromatopsia), or a diagnosed NEGATIVE (face-inversion, phi). None is "the
  live deployed faculty failing on its own."

- **T2 MECHANISM-PRESENT ≈ 15+ failure modes — this is where the size is, and it is
  IMPLIED.** aberrant salience, attentional capture ("ball while reading"),
  inattentional blindness, passivity/made-actions, thought-insertion, sensory-
  attenuation failure, stuck-basin/rumination, OCD re-capture, hoarding/reward-
  hijack, absence/arrest, can't-shed overload, shed-too-much, reflex misfire,
  disinhibition-leak, boredom. For every one, the failing operation genuinely EXISTS
  in the substrate (a Rust Term or a live seed rule) — but NOT ONE is built or gated
  as a disorder. Mechanism-present ≠ disorder-reproduced.

- **T3 SPECULATIVE ≈ 6.** hemineglect, depression-as-permanent-plasticity-lock (the
  engine is the WRONG model — it doesn't lose plasticity), tics/utilisation-behaviour,
  rigidity/instability-as-entities, apathy/avolition, mania/dissociation. New
  mechanism or a structural mismatch.

**The 3–5 most compelling T2 (mechanism clearly present, disorder clearly implied):**

1. **Efference-copy failure → passivity / made-actions / thought-insertion
   (first-rank schizophrenia).** THE strongest. `pe_efference_ref` is a real
   default-off seed rule that predicts the agent's own self-motion, subtracts it, and
   labels the residual "the world / the other." Failure = don't subtract → self reads
   as alien. This is the textbook computational account of first-rank symptoms, and
   the operation is here, armable, byte-identity-gated. `VISION_EFFERENCE_EGOMOTION_RESULTS.md`.
2. **Aberrant salience → delusion formation.** The residual-salience map is live and
   its noise mis-fire is DOCUMENTED (`VISION_RESIDUAL_SALIENCE_RESULTS.md:136`), and
   the project itself already names this as literally "rung-4 residual-salience
   mis-firing" and unifies Kapur's aberrant salience with psychosis.
3. **Stuck basin / rumination / OCD re-capture.** Basin depth and energy are
   first-class AUDITED quantities in the Rust engine (`can_ops.rs::mt_energy`,
   `audit_basin` with depth = `H(⟨σ⟩)`, recurrence detection) — this is stronger than
   "conceptual"; the escape-energy > available-energy account is the mechanistic floor.
4. **Attentional capture — "ball in the face while reading."** The log-weighted
   admissibility arbitration is the live resolver, and the project explicitly cites
   this failure tail as PROOF the competition is genuinely weighted (not a fixed
   hierarchy). The mechanism is exactly there; the experiment is not.
5. **Hoarding / reward-circuit hijack.** The most theorised (instrumental-becomes-
   terminal, supergraph opportunity cost) with a real structural defence in place —
   but the pathology is a genuine attractor for any goal-directed system and is unbuilt.

**Things reproduced that the brief did not name:** **visual agnosia** and **cerebral
achromatopsia** are BOTH landed-gated clinical disorders — reproduced as clean lesion
double-dissociations (`VISION_AGNOSIA_RESULTS.md` 12/12, `VISION_ACHROMATOPSIA_RESULTS.md`
5/5), guarding specific operations (the sd-loop recognize rules; the colour-category
mint). **Border-ownership/figure-ground** (Gestalt) is also gated. And **McCollough**
(a contingent aftereffect) and **crowding** are landed. Conversely, several things one
would ASSUME are landed are NOT: **phi proper** is a NULL (inverted curve), **Cornsweet**
FAILS (wrong sign), **Mach bands / simultaneous contrast** are not presentable, the
classic **motion aftereffect/waterfall** was never built, and **"change blindness"** on
disk is a mislabelled retinal-sparsity negative.

**The blunt one-paragraph verdict.** The honest list is **small where it is real and
large where it is implied.** Genuinely LANDED (built + gated): ~4 landings covering
~15 failure modes — two authored cognitive-disorder demos (seizure, psychosis) and a
handful of perceptual illusion/lesion gates — every one bounded, several as validation-
gates or diagnosed negatives, NONE the live faculty failing on its own. The "quite
large" claim is TRUE but lives entirely in T2: ~15+ disorders whose failing operation
demonstrably EXISTS in the substrate (efference copy, residual salience, basin-depth
energy, the settlement/shed give, the reflex race, the grounding loop) but which have
NOT been reproduced — mechanism-present, disorder-implied. The value of the whole map
is not the count; it is the COMPRESSION — one settlement/grounding/salience/energy
architecture generating seizure AND psychosis AND aberrant salience AND passivity AND
rumination AND a battery of illusions as failure modes of shared operations, at their
correct distinct Marr levels (throughput vs content). That unification is real and
worth having on its own terms; it is NOT a clinical claim, NOT validated against
patient data, and the clinical labels it maps to are frame-relative observer
constructs, not the mechanisms themselves.
