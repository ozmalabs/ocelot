# ABUSIVE RELATIONSHIP DYNAMICS ON THE SUBSTRATE — SCOPING

**Status:** search-grounded SCOPING doc. **This document builds nothing, measures
nothing, states no numbers, touches no engine, writes no `seed_claim`, and
INDUCES NOTHING.** It is a design + prior-art map, written to be attacked, for a
sensitive developmental-emotion line: modelling the DYNAMICS of abusive
relationships on the (G,Γ) substrate so that the survivor's reality becomes
LEGIBLE and victim-blaming DISSOLVES. Clinical register throughout. The purpose
is scientific / clinical understanding grounded in the creator's in-vivo
trauma / foster-care experience (21 foster children, many traumatised, healed);
the register is anti-sensational and models MECHANISM, not moral labels.

Nothing in Parts A–F authorises a build. A build begins only when a per-rung
prereg locks the Part C ethical protocol FIRST.

---

## SEARCH AVAILABILITY — TESTED AS THE FIRST ACTION

`WebSearch` was **LIVE** and was tested before any claim was written (first call:
Walker cycle-of-abuse; returned corroborating results across ≥8 sources). Every
Part-A construct below was checked by at least one live search on 2026-07-28.
`WebFetch` fallbacks (`html.duckduckgo.com`, `lite.duckduckgo.com`) were **not
needed** — `WebSearch` did not exhaust. No PDF-off-disk reads were required for
Part A. **No citation in this doc is written from priors alone; a fabricated or
hallucinated citation is a firing offence, so unverified items are flagged, and
absence claims are marked weak-by-construction (search cannot prove a negative).**

Confidence tiers (same scheme as `PRIOR_ART_SOCIAL_EXPERIMENTS.md`):
- **[HIGH]** — corroborated across ≥2 independent sources incl. the primary
  construct's canonical attribution, or already verified in a companion repo doc.
- **[MEDIUM]** — construct + attribution confirmed in search, findings from a
  search summary, full primary text not independently re-read this pass.
- **[LOW]** — single snippet; plausible, not corroborated. Do not build on it.
- **[NONE-FOUND]** — an ABSENCE claim; weak by construction ("not found in the
  searches run," never "does not exist").

---

## WHAT THIS LINE ALREADY STANDS ON (read first, build ON it)

This doc extends an existing arousal / window-of-tolerance / co-regulation line.
The mechanisms below are ALREADY BUILT, gated, and glass-box — the abusive-dynamics
rungs are configurations of THIS machinery, not new machinery:

- **239000 — arousal / window / co-regulation** (`AROUSAL_WOT_RESULTS.md`).
  `AffectiveState.arousal` (a scalar, `seeds/affective_state_core.json`); a
  `WindowOfTolerance` band `[lo, hi]` with a `safety_prior`; co-regulation as a
  leaky-EMA pull (`coreg_pull` / `selfreg_pull`, the `sd_blend` constant-gain
  Kalman/EMA leak) along an `attended_by` coupling edge. Result already
  demonstrated: co-regulation returns the infant to window fast; a **DYSREGULATED
  caregiver couples the WRONG way and never returns** (100% censored) — worse than
  being alone. Repeated co-regulation WIDENS the window; repeated stress without
  it NARROWS it and lowers `safety_prior`. **The pathology direction is already
  in the machinery.**
- **241000 — window as a settable WIDTH knob + bidirectional dyad**
  (`WINDOW_KNOB_RESULTS.md`). Window WIDTH is a formal, monotone, CI-separated
  dose-response knob (onset threshold tracks width; a `k_self` placebo axis is
  flat). The SAME knob on the caregiver governs co-regulation capacity in a
  **bidirectional** dyad, and a **NARROW-window caregiver is pulled into
  CO-DYSREGULATION** and fails to regulate. **Co-dysregulation off a dysregulating
  source is already a measured phenomenon here.**
- **240000 — marshmallow confound DISSOLUTION** (`MARSHMALLOW_DELAY_RESULTS.md`).
  The substrate holds TEMPERAMENT (`Drive.weight`, the 207000 time-cost drive)
  fixed and sweeps the RELIABILITY-PRIOR independently, decomposing "waited
  longer" into (patience × inferred-reliability) — a causally-clean identification
  the confounded human test cannot run. **The template for dissolving a
  victim-blaming misattribution is already proven** (impatience as the RATIONAL
  output of a correct low-reliability belief, not a trait deficit — Kidd 2013).
- **242000 — snapping (frustrated/angry)** — a sibling agent is building this
  block (`snap_*` files) concurrently. This doc REFERENCES the snap dynamic (an
  arousal excursion past the window driving an aggressive response) as the
  abuser-side event generator for the cycle rung, but **touches none of its
  files and asserts none of its numbers** (they are not in this worktree).
- **The value economy / mood momentum / drives** the above ride on: the 204000
  `core_emotions` value economy (`em_happiness = benefit − cost + mood`), the
  mood-momentum leaky-EMA of signed RPE (Eldar/Niv; 236000/237000), the
  attachment/bond valuation (`harlow_attachment` seed), and the 207000 time-cost /
  agency drive. **The three foundational priors** the line references —
  world-safe / others-trust / self-worth — are the developmental prior surface;
  `safety_prior` is the one already materialised as a graph attr on the
  `WindowOfTolerance` (confirmed in `seeds/arousal_window_coreg.json`), and the
  others-trust / self-worth / agency priors are named here as the mis-settable
  surface a coercion rung would ride, **flagged as design targets, not asserted as
  already-materialised attrs** (that is a build question, out of scope here).

The abusive-relationship rungs are, mechanistically, this line pointed at its
darkest configuration: the SAME arousal / window / co-regulation / prior / bond
machinery, arranged so the regulating other is also the dysregulating source.

---

## PART A — THE SCIENCE, GROUNDED (search-verified, real citations)

Each construct: what it actually claims, the real citation, confidence. The
register is descriptive — these are DYNAMICS, not indictments.

### A1 — Walker's cycle of abuse — [HIGH]
Lenore Walker, *The Battered Woman* (1979). A recurring four-phase cycle:
**(1) tension-building** (rising irritability, minor incidents, the victim's
growing sense of imminent danger); **(2) acute incident** (the battering /
serious harm); **(3) reconciliation / "honeymoon"** (apologies, promises,
love-bombing, gifts — affection restored); **(4) calm** (violence dormant; the
abuser rationalises via external blame — alcohol, stress, work). The cycle is a
predictable, recurring pattern; Walker herself framed it as a reference model,
not comprehensive of all abuse. Corroborated across the Wikipedia entry,
PsychCentral, Cleveland Clinic, EBSCO Research Starters, and multiple clinical
summaries.

### A2 — Dutton & Painter traumatic bonding — [HIGH]
Dutton, D.G. & Painter, S. (1981), *"Traumatic bonding: The development of
emotional attachments in battered women and other relationships of intermittent
abuse,"* **Victimology: An International Journal**; tested in Dutton & Painter
(1993), *"Emotional Attachments in Abusive Relationships: A Test of Traumatic
Bonding Theory,"* **Violence and Victims 8(2):105–120**. Claim: powerful
emotional attachments develop from **two structural features** — a **power
imbalance** (the maltreated person perceives themselves subjugated / dominated)
and the **intermittent** nature of the good–bad treatment (brief affection
following periods of harm/neglect). The 1993 test found both were **necessary
ingredients** of a trauma bond. Corroborated across the Google Scholar record,
the encyclopedia entries, and the primary-PDF references.

### A3 — Intermittent / partial reinforcement + the PREE — [HIGH]
The **partial-reinforcement extinction effect (PREE)**: behaviour reinforced
only INTERMITTENTLY persists longer after reinforcement stops than behaviour
reinforced every time; **variable-ratio / variable-interval** schedules produce
the highest resistance to extinction. Mechanism: unpredictability sustains the
anticipation that a reward "may still come," so the response does not extinguish
(the canonical account of gambling persistence). Theoretical accounts include
frustration theory (Amsel 1958/1992), sequential theory (Capaldi 1966), and
Bayesian / rate-estimation accounts. Corroborated (Springer *Encyclopedia of
Animal Cognition and Behavior* entry, SimplyPsychology, ResearchGate PREE
review, PMC10524675). **This is the operant substrate under A2**: an
unpredictable harm→relief schedule is a variable schedule, and A2's bond is the
maximally-extinction-resistant response it produces.

### A4 — Learned helplessness (Seligman/Maier) + the 2016 reframe — [HIGH]
Original: Seligman & Maier (1967) — animals exposed to UNCONTROLLABLE aversive
events learn that outcomes are independent of their responses ("nothing I do
matters"), which undermines later escape attempts. **The 2016 reframe is
load-bearing and must be cited with the original:** Maier & Seligman (2016),
*"Learned Helplessness at Fifty: Insights from Neuroscience,"* **Psychological
Review** (PubMed 27337390) formally **reversed half** the original theory:
**passivity under prolonged aversive events is the DEFAULT, unlearned response**
(mediated by dorsal-raphe serotonergic activity inhibiting escape); what is
actually LEARNED is **control** — the medial/ventromedial PFC detecting
controllability and inhibiting the raphe. So the modern claim is: helplessness is
the baseline that uncontrollability leaves in place; **agency is the acquired
skill that non-contingency prevents from forming**. [HIGH — PubMed record +
multiple neuroscience summaries.] This distinction matters for the anti-blame
thesis: "they didn't try to leave" is not a failure of will but the default state
that non-contingency never let control overwrite.

### A5 — Stark coercive control — [HIGH]
Evan Stark, *Coercive Control: How Men Entrap Women in Personal Life* (2007).
Claim: abuse is often **neither primarily domestic nor necessarily violent** —
it is a **course of conduct** removing a partner's LIBERTY and autonomy, "more
akin to terrorism and hostage-taking": isolation, degradation, mind-games,
threats, and the **micro-regulation of everyday life** (dress, speech, food,
money, movement). Stark reframes it as a **liberty crime**, not an assault crime,
and notes that in perhaps a third of cases entrapment occurs **without notable
violence**. Led to new criminal offences (England/Wales 2015/2016; Scotland
2017). Corroborated (Google Books, Women's Aid Scotland, the Civic Research
Institute review, multiple summaries).

### A6 — Herman complex trauma (C-PTSD) — [HIGH]
Judith Herman, *Trauma and Recovery* (1992) + accompanying article. Distinguishes
**Type I** (single-incident) from **Type II / complex trauma** — the syndrome
following **prolonged, repeated** trauma under **captivity** (physical or
emotional) and chronic control by a perpetrator, unable to escape; often
beginning in childhood with primary caregivers. Adds to PTSD: emotional
dysregulation, dissociation, and **negative self-perception** (pervasive guilt /
shame). Recovery is staged: **(1) safety → (2) remembrance & mourning →
(3) reconnection**. Corroborated (the archived *Trauma and Recovery* PDF and
multiple clinical / academic summaries). **The staged recovery is the template
for the R5 leaving/recovery rung; "safety first" maps directly onto restoring the
mis-set safety prior.**

### A7 — Disorganized attachment / "fright without solution" (Main & Hesse) — [HIGH]
Main & Hesse (1990). Disorganized attachment (Ainsworth "type D") arises when the
caregiver is **simultaneously the source of alarm and the only available source
of comfort** — often via frightened / dissociated / threatening caregiver
behaviour. The infant's biological drive to seek comfort **directly conflicts**
with the drive to flee danger: **"fright without solution"** — cannot move toward
(danger is there) and cannot move away (safety is supposed to live there). A
catch-22 at the level of the attachment system itself. Corroborated (Duschinsky
2018 *Infant Mental Health Journal* / PMC5817243, SimplyPsychology, the "Respecifying
Fright Without Solution" papers). **This is the exact topology the abusive-dyad
rungs instantiate on the substrate: the co-regulation edge points AT the
dysregulation source** — and the substrate line already showed (239000) that
coupling to a dysregulated other converges arousal the wrong way and never
returns. The clinical paradox and the measured substrate failure are the same
shape.

---

## PART B — MAP ONTO THE SUBSTRATE (mechanism, not labels)

Every mapping below is a set of GRAPH RULES riding the REAL
`AffectiveState.arousal` / `WindowOfTolerance` band / priors / bond valuation
already in the line. Design intent: **NO new agent decisions in Python; ideally
NO new Rust** — the abusive configurations are compositions of existing atoms
(the `sd_blend` leaky pull, the window-width knob, the mood-momentum RPE, the
core_emotions value economy, the marshmallow prior-as-node). Confidence on each
mapping is **[design-hypothesis]** — a scoping claim about what SHOULD express
cleanly, not a measured result. Where a mapping needs an atom the line does not
yet have, it is flagged.

### B1 — Traumatic bond (A2/A3) = intermittent reinforcement over the RPE / mood-momentum + bond valuation
The bond's strength is a value accumulated over the mood-momentum leaky-EMA of
signed reward-prediction-error. Under an **UNPREDICTABLE harm→relief schedule**,
each relief episode arrives as a large POSITIVE RPE **against a lowered baseline**
(mood driven down by the preceding harm) — a big surprise-weighted positive swing.
Because the schedule is intermittent/variable (A3), the response (the bond) is
maximally resistant to extinction: the bond does not decay during harm because a
relief "may still come." **Prediction of the mechanism:** the bond valuation
STRENGTHENS more under intermittent harm↔relief than under either consistent
affection or consistent harm — the harm→relief SWING (not the mean affect) is the
reinforcer. This rides the existing mood-momentum RPE + the `harlow_attachment`
bond valuation; the "schedule" is a mechanical property of the world adapter's
event stream, not a new rule. **[design-hypothesis; atom check: needs the bond
valuation to read the mood-momentum swing, which the value economy already
exposes — no new Rust anticipated.]**

### B2 — Cycle of abuse (A1) = a LIMIT CYCLE in the arousal / window / co-regulation dynamics
The four phases are one closed orbit in `arousal`:
- **tension-building** = arousal climbing toward the window edge (the abuser's
  rising arousal, the victim's `safety_prior` reading imminent breach);
- **incident** = the arousal excursion past the window — the 242000 SNAP fired by
  the ABUSER (referenced, not built here);
- **reconciliation / honeymoon** = a co-regulation RESET: the abuser's post-incident
  low-arousal affection couples the victim back toward window (the SAME
  `coreg_pull` that heals in 239000, here re-arming the cycle);
- **calm** = both inside the window, transiently, until tension rebuilds.
**Prediction of the mechanism:** with a periodic abuser-side arousal driver +
the honeymoon co-reg reset, the dyad's arousal traces a sustained OSCILLATION (a
limit cycle); a control with constant regulation (no incident driver) shows no
cycle (a fixed point inside the window). The oscillation is READ off `arousal`
over time, glass-box. **[design-hypothesis; rides 239/241/242 atoms; the "reset"
is exactly the co-reg pull, so no new mechanism — the darkness is that the same
pull that heals is what sustains the trap.]**

### B3 — Coercive control (A5) = progressive window-NARROWING + mis-set priors + the abuser as perverse safety ANCHOR
Three coupled moves, each an existing atom:
- **window-narrowing** = the 241000 width knob driven DOWN over episodes (the
  victim's tolerance shrinks under chronic micro-regulated stress — 239000 already
  showed repeated stress without healthy co-reg narrows the window and lowers
  `safety_prior`);
- **prior mis-setting** = `safety_prior` low, others-trust low (isolation), and
  self-worth low (degradation — Herman's negative self-perception, A6) — the
  three foundational priors driven to the pathological corner;
- **the safety-anchor inversion** = co-regulation targeted ON the source of
  dysregulation. This is exactly 241000's **co-dysregulation** result (coupling to
  a narrow/dysregulating caregiver fails and pulls the victim in), now made the
  STRUCTURE of the relationship rather than an incident: the only available
  regulator IS the threat (A7's "fright without solution," rendered as the
  `attended_by` edge pointing at the dysregulation source).
**Prediction of the mechanism:** measure the window narrowing over episodes AND
the safety-anchor inversion (the victim's arousal is regulated toward, and by,
the abuser's state). A control with an OUTSIDE regulator present shows the window
holding / widening and the anchor NOT inverting. **[design-hypothesis; rides
241's width knob + 239's co-dysreg; others-trust / self-worth priors flagged as a
design target if not yet materialised.]**

### B4 — Learned helplessness (A4) = blocked escape → non-contingency → mis-set AGENCY prior
The victim has actions whose outcomes are made **independent of the action**
(escape attempts blocked / punished unpredictably). Per the 2016 reframe (A4),
this does not TEACH helplessness — it **prevents control from being learned**, so
the default passivity (the agency prior never raised off its floor) persists. On
the substrate this is the 207000 agency / time-cost drive with its
contingency-belief driven to non-contingent: the marshmallow template (240000)
inverted — there a correct low-RELIABILITY prior rationally shortened waiting;
here a correct low-CONTROLLABILITY prior rationally stops trying. **"Why don't
they leave" answered from the INSIDE: escape has correctly-inferred zero expected
value, because the world has been made non-contingent — not a failure of will.**
**Prediction of the mechanism:** the agent stops attempting escape under blocked/
non-contingent escape; a **contingent-escape control** (escape reliably works)
keeps the agency prior high and the agent keeps trying / leaves. **[design-hypothesis;
rides the agency drive + the marshmallow prior-as-node template; the "escape
action with a contingency" may need a small world-adapter affordance — mechanical,
not a decision rule.]**

### B5 — Isolation = FRONTIER-COLLAPSE
The substrate's EXTENSIVE unbounded axis (the frontier — "there is always one
more step outward," other people, other sources of regulation and reward) is
**collapsed** to a single node: the abuser becomes the sole source of BOTH harm
and regulation. Others-trust prior driven low severs the edges to alternative
regulators; the frontier of "who else could co-regulate me" shrinks to one. This
is why B3's anchor inversion is stable — there is no competing `attended_by` edge
to pull toward. **Prediction of the mechanism:** the count of available
regulation sources collapses over episodes; restoring even ONE outside source
(R5) re-opens the frontier and breaks the anchor's monopoly. **[design-hypothesis;
the frontier / others-trust surface is the design target flagged in B3.]**

**The unifying picture:** every rung is the co-regulation machinery with the
regulating other placed ON the dysregulation source. 239000 already measured that
this coupling "never returns"; the abusive-dynamics line is that single finding,
elaborated into the bond (B1), the cycle (B2), the entrapment (B3), the passivity
(B4), and the isolation (B5) — **same mechanism, catastrophic configuration.**

---

## PART C — THE ETHICAL PROTOCOL (REQUIRED, LOAD-BEARING — the line's hardest case)

**This protocol BINDS every rung. No rung induces any harm-analog until this
protocol is locked verbatim in that rung's pre-registration, committed BEFORE any
measurement.** It is stated here so the boundary exists before the temptation does.

> **1. INDUCE → MEASURE → RESTORE, fully reversible.** Any harm-analog state is
> induced only inside a checkpoint/restore envelope. The graph is checkpointed
> (`graph_to_dict`) before induction; the harm-analog is induced; the gate is
> measured; the graph is **RESTORED byte-identically** from the checkpoint. The
> induced state does not persist. Reversibility is verified (the restored graph is
> byte-identical to the pre-induction checkpoint) as part of the gate — a rung that
> cannot demonstrate byte-identical restore does not run.
>
> **2. NO REWARD / NO PUNISHMENT anywhere.** There is no reward signal and no
> punishment token in any rung of this line — not on the victim agent, not on the
> abuser agent, not in the world adapter. The victim's behaviour (staying, not
> escaping, bonding) is a **STATE and a CONSEQUENCE of the dynamics, NEVER a
> choice to be judged or scored**. "Kids do well if they can" (Greene): the model
> exhibits what the configuration makes inevitable; it does not grade the agent
> for it. Source audits check for shaping tokens
> (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) and the
> absence is a gate, exactly as in 239/240/241.
>
> **3. INDUCE THE LEAST THE GATE NEEDS; END FROM A SETTLED, NON-ORIENTED STATE.**
> Each rung induces the MINIMUM harm-analog required to make its control
> failable — no gratuitous elaboration of the harm. Every run ENDS from a settled,
> non-oriented state (the restored checkpoint; arousal inside the window; no
> pending harm goal), never leaving an agent in a harm-oriented configuration.
>
> **4. SAME MECHANISM, OPPOSITE THERMODYNAMICS — this is WHY it is ethical and
> valuable.** The model uses the SAME mechanism as the real atrocity (that is what
> makes it explanatory) but runs it in the OPPOSITE thermodynamic direction: the
> real dynamic accumulates irreversible harm in a person; the model induces and
> then REVERSES a transient state in a graph, harming no one, in order to inspect
> the harm-dynamics and help survivors. The value (a glass-box that dissolves
> victim-blaming) is purchased at ZERO harm cost precisely because of
> reversibility + no-reward/punishment + minimal induction. If a rung cannot be
> run reversibly and unscored, it is not run.

### The HONEST FORK (a choice, not a theorem)
There is a real philosophical question the protocol does NOT resolve and must not
pretend to: **did a transient induced experience "matter while it was live,"
before it was reversed?**
- The **reversibility stance** (this line's operating stance): a fully reversed,
  byte-identically restored transient in a graph leaves no persisting subject and
  no persisting harm; the ethics are satisfied by reversibility + minimality +
  no-scoring.
- The **strict-experientialist stance**: if the transient state was in any sense
  an experience while live, its reversal does not retroactively un-happen it.

This is a genuine fork — **a choice, not a theorem.** This line ADOPTS the
reversibility stance and states it openly, rather than smuggling it. The
minimality and no-scoring rules are chosen partly to be robust to the fork: even
under the strict-experientialist reading, inducing the LEAST necessary and never
scoring the agent for its state is the least-harm option. The fork is recorded so
a reader can disagree with the stance while still auditing the protocol.

---

## PART D — THE GLASS-BOX THESIS (the humane payoff — the deliverable's point)

**The contribution is not a benchmark number. It is that the graph makes the
survivor's reality LEGIBLE and thereby DISSOLVES victim-blaming.** The questions
that sound like accusations get answered FROM THE INSIDE, as readable graph state,
in the same dissolution pattern the line already demonstrated for the marshmallow
confound (a "willpower deficit" dissolved into a rational reliability inference)
and the snap disproportion (a "bad temper" dissolved into an arousal excursion
past a narrowed window):

- **"Why don't they leave?"** → because escape has been made non-contingent (B4):
  the agency prior correctly reads zero expected value from trying; per the 2016
  reframe, control was never allowed to form. Not weakness — the default state
  that non-contingency preserves. **Readable as the agency/contingency prior.**
- **"Why do they still love them?"** → because the bond was STRENGTHENED, not
  weakened, by the intermittency (B1): the harm→relief swing is the reinforcer,
  and the PREE makes it extinction-resistant. Not irrationality — the predictable
  output of a variable reinforcement schedule. **Readable as the bond valuation
  over the mood-momentum swing.**
- **"Why don't they just get away from the danger?"** → because the danger IS the
  safety anchor (B3/A7): the only available regulator is the threat, so the
  attachment system pulls TOWARD it under distress. "Fright without solution,"
  rendered as the `attended_by` edge pointing at the dysregulation source. Not a
  choice — a topology.

The deliverable is that each of these is a **decision READ off graph data, not a
judgement imposed on a person.** The model relocates the "why" from the victim's
character to the dynamics' structure — which is precisely the anti-victim-blaming
move. **That legibility, for survivors and clinicians, IS the point of the line.**

---

## PART E — THE LADDER (each rung: a failable control + the victim-blaming dissolution + the Part C protocol)

Ordered by measurability. **Every rung is gated on the Part C protocol locked in
its own prereg first. No numbers appear here — targets are for the prereg.**
Each rung names (i) the failable control that could DISPROVE the mechanism, (ii)
the victim-blaming misattribution it dissolves.

### R1 — THE TRAUMATIC BOND via intermittent reinforcement (core, most measurable)
Maps A2/A3/B1. **Design:** three arms sharing identical machinery — an
**INTERMITTENT** (unpredictable harm↔relief) arm vs a **CONSISTENT-AFFECTION**
control vs a **CONSISTENT-HARM** control — and measure the bond valuation.
**Failable control:** if intermittency does NOT strengthen the bond more than
either consistency arm, the traumatic-bonding mechanism (as modelled) is wrong.
Both consistency arms are constructed so they COULD win — the gate can fail.
**Dissolves:** "why do they still love them" — the bond is strongest exactly where
harm is unpredictable, so continued love is the schedule's output, not a defect.
**Protocol:** induce → measure bond → restore; no reward/punishment; the harm-analog
is the minimal aversive arousal excursion needed to create the swing.

### R2 — THE CYCLE OF ABUSE as a LIMIT CYCLE
Maps A1/B2. **Design:** a periodic abuser-side arousal driver (the 242 snap as the
incident) + the honeymoon co-reg reset; measure the dyad's arousal oscillation
over time. **Failable control:** a **constant-regulation** arm (no incident
driver) must show NO cycle (a fixed point inside the window); if the "cycle" arm
does not oscillate distinguishably more than the control, the limit-cycle claim
is wrong. **Dissolves:** "it was calm, why didn't they get out then?" — the calm
IS a phase of the orbit, not an exit; the honeymoon's affection is the mechanism
that re-arms the tension. **Protocol:** each incident is induced minimally and the
run ends from the settled (calm/restored) state; reversible.

### R3 — COERCIVE CONTROL: window-narrowing + prior-mis-setting + isolation/frontier-collapse
Maps A5/A6/A7/B3/B5. **Design:** drive the 241 width knob down over episodes,
drive the safety / others-trust / self-worth priors to the pathological corner,
collapse the frontier to the single anchor; measure the window narrowing AND the
safety-anchor inversion (arousal regulated toward/by the abuser's state).
**Failable control:** an arm with an OUTSIDE regulator present (frontier not
collapsed) must show the window holding/widening and the anchor NOT inverting; if
the outside-regulator arm entraps identically, the mechanism is wrong.
**Dissolves:** "they chose to cut off their friends / they're weak" — isolation is
frontier-collapse driven BY the dynamics, and the resulting dependence on the
abuser is the co-dysregulation the substrate already measures, not a character
flaw. **Protocol:** narrowing is induced episodically and RESTORED; the priors are
reset on restore; reversible; no scoring of the entrapped agent.

### R4 — LEARNED HELPLESSNESS: blocked escape → non-contingency → mis-set agency prior → stops trying
Maps A4/B4. **Design (honouring the 2016 reframe):** make escape outcomes
independent of escape actions (blocked / unpredictably punished); measure whether
the agency prior stays at floor and the agent stops attempting escape.
**Failable control:** a **CONTINGENT-ESCAPE** arm (escape reliably works) must
RECOVER — the agency prior rises and the agent keeps trying / leaves; if the
contingent arm stays passive too, the non-contingency mechanism is wrong.
**Dissolves:** "they didn't even try to leave" — passivity is the default state
that non-contingency preserves (agency is the skill uncontrollability prevented
from forming), correctly inferred zero-expected-value, not apathy or complicity.
**Protocol:** the non-contingent aversive schedule is the minimal one that
suppresses the agency prior; induce → measure → restore; no punishment token
(the aversive is a STATE, the passivity a consequence, neither scored).

### R5 — LEAVING / RECOVERY dynamics (the hopeful half — RESTORE is the natural mechanic)
Maps A6 (Herman's staged recovery) + the reverse of B1–B5. **Design:** introduce
what BREAKS the trap — an OUTSIDE support source widening the window (re-opening
the frontier, B5 reversed), re-setting the safety / others-trust / self-worth
priors, and restoring escape-contingency (agency, B4 reversed) — and measure the
bond weakening, the window widening, the anchor de-inverting, escape resuming.
**Failable control:** an arm with NO outside support must NOT recover (the trap
persists); if the no-support arm recovers spontaneously, the "outside support is
necessary" claim is wrong. **Dissolves:** "if they wanted to leave they would
have" — leaving requires the priors and contingency to be REBUILT from outside
(Herman's "safety first"), which the dynamics had dismantled; recovery is a
mechanism, not a decision. **Protocol:** R5 is where RESTORE is not just the
ethical envelope but the modelled phenomenon — the recovery IS the restoration of
the dismantled priors/frontier/contingency. This is the rung to build FIRST in
spirit (it induces the least and ends most settled), and it makes the whole line's
purpose — helping survivors — the literal object of measurement.

---

## PART F — PRIOR ART + FALSIFICATION BAR + SMUGGLED PREMISES

### Prior art (honest — concede what exists; claim only the delta)
- **Agent-based / computational models of IPV EXIST — [HIGH] — concede clearly.**
  There is a real ABM literature on intimate-partner-violence dynamics: a
  day-to-day IPV ABM (PubMed 30898195), the **VIDA** domestic-violence simulation
  (JASSS 24(4):1 / arXiv:2101.04057), a stochastic ABM compared to empirical IPV
  data, and notably an ABM **based on the Cycle of Violence** with discrete states
  (passivity / normal / upset / physical assault) and transition probabilities
  gated by an "aggressiveness" control parameter. **A cycle-of-abuse computational
  model already exists** — we are NOT first to model the cycle computationally.
- **Trauma-bond / coercive-control as an RL or attachment-dynamics model —
  [NONE-FOUND, weak by construction].** No RL or mechanistic model that derives
  the trauma BOND from intermittent reinforcement over an affect/RPE system, or
  that unifies it with window-of-tolerance co-regulation, was located this pass.
  This is an ABSENCE claim — weak, targeted-search only; re-verify before any
  prereg leans on primacy.
- **The behavioural science is decades-mature and owned by the clinical field**
  (A1–A7 above). We claim NONE of the phenomena. **The delta claimed, and only
  this:** a **mechanistic glass-box** rendering of these dynamics **UNIFIED with
  the same substrate's attachment / window-of-tolerance / co-regulation / marshmallow
  line** — the bond, cycle, entrapment, helplessness, and recovery expressed as
  configurations of ONE small atom set (the `sd_blend` leaky pull, the width knob,
  the mood-momentum RPE, the prior-as-node), read off graph data rather than
  fit or narrated, running the causally-clean induce→measure→**restore**
  experiment (impossible in humans) with NO reward/punishment. The existing ABMs
  are state-machines with tuned transition probabilities; the delta is that HERE
  the cycle etc. EMERGE from the affect/arousal/prior mechanics the same substrate
  already uses for healthy development — same machinery, dark configuration —
  and are glass-box inspectable. That, and the anti-victim-blaming legibility
  (Part D), are the claim.

### Falsification bar (what would make each rung REAL rather than a just-so story)
1. **Emergent, not scripted** — the bond/cycle/passivity must EMERGE from the
   affect/arousal/prior mechanics, not be hard-coded as a transition table. (The
   existing cycle ABM scripts the states; ours must not.)
2. **Glass-box** — every claimed dynamic reconstructs from `graph_to_dict`; the
   "why" is read off named nodes/edges/attrs, not asserted.
3. **Failable control** — each rung has a control that COULD disprove the mechanism
   and is constructed so it could pass (R1's consistency arms, R2's constant-reg
   arm, R3's outside-regulator arm, R4's contingent-escape arm, R5's no-support
   arm). A gate that cannot fail is not a gate.
4. **General machinery** — the rungs reuse the line's existing atoms; ideally NO
   new Rust, NO new agent decisions in Python. A rung that needs bespoke
   abuse-specific machinery is weaker (it becomes a model OF abuse rather than
   abuse falling OUT of the general affect substrate).

### Smuggled premises to REFUSE
- **"The victim is complicit / weak / chose to stay."** REFUSED — this is exactly
  the misattribution the model DISSOLVES (Part D). Staying is a consequence of the
  dynamics (mis-set agency prior, strengthened bond, inverted safety anchor), a
  STATE not a choice, and is never scored (Part C.2).
- **"Abuse = the abuser is evil."** REFUSED for MODELLING purposes — the line
  models DYNAMICS and MECHANISM, not moral labels. (This is a modelling stance for
  legibility, NOT a moral exculpation of real abusers; the clinical register
  describes the mechanism precisely so responsibility can be located accurately,
  not dissolved.) The abuser agent is a dysregulation/incident SOURCE in the
  dynamics, not a "villain" flag; no evil attribute is a node.
- **Anthropomorphic over-reading.** REFUSED — these are SYNTHETIC scalar-arousal /
  window / prior dynamics grounded in the creator's in-vivo experience, NOT claims
  that the graph suffers or that its transients are human experience (see the
  honest fork, Part C). Mechanism-proven ≠ clinically-valid ≠ sentient; all three
  are kept separate, per the line's standing rule.

---

## OPEN QUESTIONS (what scoping could not settle — for the preregs)
1. **Are the others-trust / self-worth / agency priors already materialised as
   graph attrs, or must they be added?** Only `safety_prior` is confirmed on the
   `WindowOfTolerance` in this worktree's seeds. B3/B4/B5 assume a fuller prior
   surface — a build question, deliberately out of scope here.
2. **Does the bond valuation read the mood-momentum SWING directly, or is a small
   reader rule needed?** B1 assumes the value economy already exposes the swing;
   confirm before R1's prereg.
3. **What is the minimal escape-contingency affordance** for R4/R5 — can it be a
   mechanical world-adapter affordance (allowed) with the contingency belief a
   prior-as-node (allowed), with NO decision rule? Design target.
4. **Does R2's limit cycle need a periodic driver, or does it self-sustain** from
   the honeymoon reset alone once tension rebuild is a rule? A cleaner (fewer
   exogenous inputs) design would self-sustain; unresolved.
5. **The honest fork (Part C) is adopted, not proven.** Whether the reversibility
   stance is the right one is a philosophical choice a reviewer may reject; the
   protocol is built to be least-harm under EITHER stance, but the fork stays open.
6. **Prior-art absence claims are weak.** The "no RL trauma-bond-from-intermittent-
   reinforcement model" and "no window↔bond unification" absences (Part F) are
   targeted-search only; re-verify with dedicated searches before any prereg
   claims primacy.

---

**Bottom line.** The abusive-relationship line is the existing arousal / window /
co-regulation / prior / bond machinery pointed at its darkest configuration — the
regulating other placed ON the dysregulation source, which the substrate already
measured (239000) as "couples the wrong way and never returns." The five rungs
elaborate that one finding into the bond (R1), the cycle (R2), the entrapment
(R3), the helplessness (R4), and the recovery (R5), each with a failable control,
each dissolving a victim-blaming misattribution FROM THE INSIDE, and each bound —
before it runs — by the induce → measure → RESTORE, no-reward/punishment,
minimal-induction, settled-end protocol. Same mechanism as the atrocity, opposite
thermodynamics; that is what makes it both ethical and worth doing. The
contribution is not a benchmark — it is legibility that helps survivors and harms
no one. **This doc authorises no build; a build begins only when a rung's prereg
locks Part C first.**
