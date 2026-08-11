# SEIZURE SCIENCE — turning the glass-box tool toward the literature

Read-only science on the LANDED engine seizure capability
(`seeds/seizure_dynamics.json` + `scripts/seizure_engine_lattice.py`, the
default-off tunable settlement rule that reproduces PMC5550430's
standing→persist/die→traveling bifurcation from a give-dial). **No engine
changes.** Every number is the real (G,Γ) engine settling a 41×41
`CognitiveArea` lattice via `run_rules` + `fold_clock_edge`. Probes:
`scripts/seizure_science_probes.py`; data: `results/seizure_science.json`.

**Provenance / reproduction check.** These probes were run on this worktree's
engine (which shares the seizure DSL Terms with the base). Before trusting any
new number, the published seed-5 give sweep was reproduced **to the digit**
(give=0.5 → final_active 64.8, rank-1 0.821; give=0.575 → 8.3; give=0.55 → 18.6
— identical to `results/seizure_engine.json`). The engine here is
settlement-equivalent for this model.

**What this model is (the bounds that gate every claim below).** A REDUCED,
HOMOGENEOUS square lattice with UNIFORM nearest-neighbour coupling and a
HARNESS-DRIVEN async clock; the seizure capacity is carried by a
positive-feedback term `alpha` that was ADDED for the capability (not derived —
see Thread 3). Faithfulness to the paper is **bracketing, not a fit** (front
speed brackets 0.48 mm/s; standing rank-1 0.73–0.87 vs the paper's 0.94). So:
mechanistic predictions about the DIRECTION and STRUCTURE of the bifurcation are
in scope; quantitative thresholds (give*≈0.55) are model-internal and are
reported as ratios/signs, never as neural units.

---

## THREAD 1 — Predictions extracted from the model

### P1 (headline) — The persist/die outcome is set by a DISSIPATION-RATE readout, NOT by onset morphology. *[answers the paper's own open question]*

The paper (PMC5550430) states its open question: seizures and interictal events
begin as an identical standing wave; *what makes one persist and one die
"remains to be determined."* The model gives a sharp, falsifiable answer.

Sweeping the give across the fold (central 3×3 onset, D=6, seed 5), measured in
the STANDING window (drive removed → +40 substeps, i.e. before any traveling
transition):

| give | outcome | standing-wave rank-1 (morphology) | peak active | **standing-phase decay slope of total residual** |
|---|---|---|---|---|
| 0.500 | PERSIST | 0.845 | 37 | **−4.29** |
| 0.5375 | PERSIST | 0.840 | 28 | **−5.38** |
| 0.575 | DIE | 0.836 | 25 | **−5.89** |
| 0.650 | DIE | 0.827 | 20 | **−6.78** |

**Claim.** The standing wave's SPATIAL PROFILE (rank-1 fraction: 0.827–0.845,
essentially flat) and peak amplitude do **not** discriminate persist from die.
The **decay RATE of the standing-wave amplitude** in the first ~40 substeps does
— monotonically, with the persist/die boundary sitting at a slope threshold
(~−5.6 here). A standing wave that sheds its residual more slowly is the one that
will go on to persist. This is a within-onset measurement available BEFORE the
traveling transition (before clinical onset), and it is **independent of what the
onset looks like spatially**.

Falsifiable form: *In calcium/LFP recordings of the ~300 ms onset standing wave,
the early amplitude-decay rate predicts persist-vs-die over and above the wave's
spatial profile and peak amplitude.* If outcome is fully predicted by the spatial
profile / peak (morphology), or by anatomy/E-I with no residue for a decay-rate
term, the model's reframe adds nothing.

### P2 (strongest clinically-pointed) — HYSTERESIS: aborting an established seizure needs MORE dissipation restored than preventing onset.

Two thresholds, measured separately on the real engine:

- **Onset threshold** (fresh lattice, does a standing wave persist?): seizes for
  give ≤ ~0.55, **dies for give ≥ 0.575**.
- **Abort threshold** (a running seizure at give=0.30, restore give mid-event at
  t=120): still persists when restored to give=0.575 (final 53), give=0.60
  (final 10); **aborts only when restored to give ≥ 0.625** (final 0).

So there is a **bistable window give ∈ [0.575, 0.625)**: in it, a resting lattice
will NOT spontaneously seize, yet an already-running seizure will NOT stop.

**Claim.** The dissipation-capacity you must restore to ABORT an established
seizure strictly exceeds the capacity that would have PREVENTED it (here a
~10–13% overshoot in the give scale). A closed-loop therapy tuned to the
prevention threshold is under-dosed for termination; abort dosing must scale with
how established the event is.

### P3 — A full desynchronization aborts at essentially ANY time; what gates abort is MAGNITUDE, not timing.

Restoring give=1.0 (full graceful shed) on a running seizure aborts at desync
times t = 30, 60, 90, 120, 160, 200, and 260 (the lone `t=260` "failure" in the
first sweep is a **recording-window artifact** — a 420-substep rerun confirms it
too aborts to 0). A **sub-threshold** restoration (give ≤ 0.60) never aborts, at
any time. **Claim.** For an intervention above the (hysteretic) abort threshold
there is NO intrinsic point-of-no-return; below it, timing is irrelevant because
it never works. The actionable variable is the strength of restored dissipation,
not the latency of the intervention.

### P4 (a REFUTATION / limit — reported loudly) — In this model, MORE lateral coupling is PROTECTIVE (give* falls as coupling g rises).

| lateral coupling g | give* (seizure regime = give < give*) |
|---|---|
| 0.40 | 0.65 |
| 0.60 | 0.60 |
| 0.80 | 0.55 |
| 1.00 | 0.50 |

Higher coupling **shrinks** the seizure regime. This is the OPPOSITE sign to the
mainstream connectivity→epileptogenicity result, and it is the model telling on
itself: the lattice's `projects_to` coupling `g` is a **symmetric diffusive
channel** (it carries both lateral shed-OUT and recruitment-IN, which for a
uniform field roughly cancel and at the front net toward faster leakage). It is
NOT the excitatory, recruitment-biased coupling the epilepsy literature means by
"hyperconnectivity." See adjudication — this is a genuine model LIMIT, not a
neural prediction.

### P5 (a NULL / limit) — No spatial onset-locus effect in the homogeneous lattice.

give* for an identical 3×3 onset placed at the center (0.55), a mid-edge (0.575),
and a corner (0.55) differs by at most one grid step — no clean gradient. The
reduced lattice is HOMOGENEOUS; it has no hubs, so "where the give fails first"
has no structural answer here. A locus prediction requires heterogeneous coupling
the model does not carry (named extension: a degree-heterogeneous lattice).

---

## THREAD 2 — Adjudication against the literature

| Pred | Class | Verdict |
|---|---|---|
| P1 decay-rate discriminates persist/die, morphology does not | **NOVEL-AND-TESTABLE** | mechanism corroborated; the specific discriminator is open |
| P2 abort-threshold > onset-threshold (hysteresis gap) | **NOVEL-AND-TESTABLE** (direction confirmed) | bistability confirmed; the intervention asymmetry is the contribution |
| P3 full desync aborts anytime; magnitude not timing | **CONFIRMED / consistent** | corroborated by coordinated-reset + RNS findings |
| P4 more coupling → protective | **SOFT REFUTATION → model limit** | contradicts connectivity literature; resolved as wrong-kind-of-coupling |
| P5 no onset-locus effect | **REFUTED-as-tested → model limit** | literature has a strong hub-onset effect the homogeneous lattice can't show |

**P1 — mechanism corroborated, discriminator novel.** The model's functional
story (persist = a dissipative restraint fails to shed the residual; the
traveling wave is *recruitment*, not computation) is exactly the
**inhibitory-restraint / collapse-of-inhibition** account: feed-forward
inhibition ahead of the ictal wavefront restrains propagation, and its **collapse
is the key event** recruiting the pyramidal population
([Schevon et al. 2012, *evidence of an inhibitory restraint*](https://pmc.ncbi.nlm.nih.gov/articles/PMC3658011/);
[Parrish et al. 2019, *feed-forward inhibition ahead of ictal wavefronts*](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6462485/);
[the ictal wavefront is the source of discharges, *Nat Commun* 2016](https://www.nature.com/articles/ncomms11098)).
So the model's "give" is an information-theoretic gloss on inhibitory restraint —
which means the *mechanism* is corroboration, not novelty (and it tempers the
memory's older note that "escape from inhibition" is untested: it is
well-supported in the broader literature, just not in PMC5550430's own dataset).
What IS novel is the specific discriminator P1 names — that the standing wave's
**decay rate**, not its morphology, forecasts the outcome — which PMC5550430
explicitly left open and which, notably, is **distinct from critical slowing
down**: the model has no slow drift variable, so it predicts a decay-RATE
separator, not rising variance/autocorrelation. That distinction matters because
the CSD precursor is itself **contested** — supported as a susceptibility
biomarker by [Maturana et al. 2020, *Nat Commun*](https://www.nature.com/articles/s41467-020-15908-3)
but **not found** before seizures by
[Wilkat et al. 2019, *no evidence for critical slowing down*](https://www.researchgate.net/publication/336009531_No_evidence_for_critical_slowing_down_prior_to_human_epileptic_seizures).
The model sits on the side that says the useful early-warning is a
dissipation-rate readout, not an autocorrelation one — a clean, falsifiable fork.

**P2 — bistability confirmed; the intervention asymmetry is the contribution.**
Seizure termination is a documented **discontinuous critical transition with
hysteresis / bistability**: ictal and postictal states coexist, and a system
driven in reverse shows hysteresis
([Kramer et al. 2012, *human seizures self-terminate via a critical transition*](https://pmc.ncbi.nlm.nih.gov/articles/PMC3529091/);
[*Multistability in Seizure Dynamics*](https://link.springer.com/rwe/10.1007/978-1-0716-1006-0_302)).
The model reproduces this from its own settlement dynamics (a give-carried fold),
and adds the practical corollary the clinical literature has not quantified: the
**abort threshold exceeds the onset threshold**, so prevention-strength and
termination-strength are different doses. This is consistent with the surprising
RNS finding that the device works largely **inter-ictally rather than by acute
abort**
([*Unearthing the mechanisms of RNS*, Nat Commun Med 2023](https://www.nature.com/articles/s43856-023-00401-x)) —
aborting an established event is genuinely hard, which is what a hysteresis gap
predicts.

**P3 — confirmed.** Desynchronizing an ongoing seizure by restoring
phase-diversity/dissipation is exactly **coordinated-reset** neuromodulation,
shown to desynchronize networks in an in-vivo **status epilepticus** model
([Ehrens/Tass et al. 2025, *electrical coordinated reset desynchronization*](https://pubmed.ncbi.nlm.nih.gov/40020596/);
[Tass, *demand-controlled coordinated reset*](https://link.springer.com/article/10.1007/s00422-003-0425-7)).
The model's "magnitude not timing" reading aligns with the RNS mechanism story
above.

**P4 — soft refutation, resolved as a model limit.** The mainstream is that
global connectivity strength and excitability are the phase-transition control
parameters and higher connectivity **promotes** seizure spread
([Epileptor / Virtual Epileptic Patient, Jirsa et al.](https://www.sciencedirect.com/science/article/pii/S1053811916300891);
[*Bifurcations and bursting in the Epileptor*, PLoS Comput Biol](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1011903);
[*Critical dynamics in the spread of focal seizures*, PLoS One](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0272902)).
The model's opposite sign is honest evidence that its lateral `g` is a **symmetric
diffusive** term (dissipation-dominant), not the excitatory recruitment coupling
those models use. The model as built therefore **cannot** speak to epileptogenic
hyperconnectivity; doing so would require an asymmetric, recruitment-biased
coupling term it does not have. Reported as a limit, not a neural claim.

**P5 — refuted as tested; a homogeneous-lattice limit.** The literature is clear
that **hub / high-connectivity tissue is preferential** for onset: preictal
high-connectivity states rise near onset and track the seizure-onset zone
([*Preictal high-connectivity states*, J. Neural Eng. 2025](https://iopscience.iop.org/article/10.1088/1741-2552/adf097);
[*interictal epileptic network hubs localize the epileptogenic zone*](https://www.medrxiv.org/content/10.1101/2024.01.25.24301659.full.pdf)).
The homogeneous lattice has no hubs and shows no locus effect — a structural
limit, and a concrete next experiment (heterogeneous-degree lattice) rather than a
prediction.

---

## THREAD 3 — Does the escalation term `alpha` earn its place in normal cognition?

**Verdict: PLAUSIBLE-BUT-UNFORCED.** The seizure is NOT forced by the
architecture. But the *ingredient* it corrupts — escalation toward the
unexplained — is a real, arguably necessary feature of the engine's cognition.
The two facts sit together and neither may be dropped.

**Why UNFORCED (the engine's escalation is dissipation-directed by
construction).** Reading the live scheduler rules (`seeds/cognitive_scheduler.json`):

- `ct_area_effort_tracks_live_salience` sets an area's **effort** to the *max
  salience over its tasks* — unresolved residual drives MORE effort to CLEAR it.
  That is **negative feedback** on residual (the escalation feeds the SINK).
- `ct_expand_workers_while_backpressure_clean` escalates **capacity** (workers)
  while the queue is clean — again escalating the dissipation side.
- `ct_shed_below_max_salience_when_queue_exceeds_capacity` is the give (shed).
- `ct_broadcast_residual_once_per_destination_epoch` propagates residual **once
  per destination epoch** — an explicit anti-runaway guard, not amplification.
- The curiosity loop (`collapse_curiosity.json`) scores a region by
  *same-kind-unknowns covered* and attends the biggest group **to collapse it** —
  a MINIMIZING loop. `mark_feature_salience` computes salience as a bounded
  structural readout (`mover=10 − count of same-value features`), not a
  self-amplifying quantity.

Nowhere does residual (or its driver, salience) grow as a function of itself. The
engine's whole escalation apparatus points at the SINK. `alpha`
(residual-above-threshold regenerates *more* residual) is the same escalation
**mis-wired to the SOURCE**. It is genuinely ADDED, and the convergent design is
deliberate: this confirms the supervisor's earlier engine read and the
completeness framing — the engine reaches overload and sheds gracefully; it
**cannot seize as built**, which is a correct-and-better-than-biology null, not a
defect.

**Why PLAUSIBLE (the ingredient is real, and its pathology is a known one).**
Predictive processing does require precision-weighting of prediction error — gain
turned UP on the unexplained — and its pathological form is exactly a
positive-feedback runaway: **aberrant precision** is the standard account of
phantom perception / tinnitus as "maladaptive compensation of aberrant predictive
coding"
([Friston, free-energy / precision](https://arxiv.org/pdf/2107.00140);
[prior precision modulates prediction-error minimization](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6385564/)).
So `alpha` is not arbitrary: it is the specific mis-direction of a real mechanism
(precision/effort toward the unexplained), pointed at the source instead of the
sink. Notably there is still **no established free-energy/predictive-coding model
of epilepsy** — this remains under-explored, which is where a functional layer
could contribute, but that is a reason for humility, not a claim.

**The argument in one line.** The engine PROVES you can have
surprise-driven escalation *without* the seizure (by directing it to the sink) —
which is evidence AGAINST "seizure is inherent to any escalating cognition" and
FOR the completeness view (a graceful give beats a biological seizure). The
escalation is necessary; wiring it to the source (`alpha`) is a free — and
specifically pathological — choice. A FORCED verdict would need a demonstration
that the engine's dissipation-directed escalation is not enough for some
cognitive function and that only source-escalation closes the gap. No such
demonstration exists. Hence PLAUSIBLE-BUT-UNFORCED.

---

## Bottom line (honest)

This model is **scientifically useful, not merely internally consistent — with a
sharply bounded reach.** It earns "useful" on three counts: (1) it answers
PMC5550430's own open question with a *falsifiable, morphology-independent*
discriminator (P1) that is testable on the very data the paper reports; (2) it
reproduces documented bistability (Kramer) and adds a quantified,
clinically-pointed corollary (P2, the abort>onset hysteresis gap); (3) it *tells
on itself* where it is wrong (P4/P5), and those failures are structural and
name their own fixes. It earns "bounded" because it is a reduced homogeneous
lattice with a harness clock and an ADDED escalation term: it cannot speak to
hub structure (P5) or excitatory hyperconnectivity (P4), its thresholds are
model-internal ratios not neural units, and — Thread 3 — its seizure capacity is
a plausible-but-unforced side rig, not an inherent property of the cognition.
That is a hypothesis platform that emits real, killable predictions, which is
exactly the useful thing a glass box is for — and it is one severe-test NODE, not
a QED.
