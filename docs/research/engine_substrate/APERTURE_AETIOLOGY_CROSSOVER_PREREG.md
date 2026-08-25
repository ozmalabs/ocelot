# TWO AETIOLOGIES, TWO CURES — pre-registration (block 365000)

Base sha **19a446465c**. Committed BEFORE any confirmatory measurement. Confirmatory measure will
be `scripts/aperture_aetiology_measure.py` → `results/aperture_aetiology/results.json`.

## 0. The claim, stated so it can die

`APERTURE_PATHOLOGIES.md` §5 argued that folie à deux in this tree has **two mechanically distinct
routes** — the shared BELIEF of `PSYCHOSIS_DEMO_RESULTS.md` P8, and the shared APERTURE of
`seeds/aperture_frame.json` — and that they disagree about what would fix them. That argument
currently rests on two diagonal measurements taken at different times in different harnesses. This
prereg turns it into one crossover, in one architecture, with the interventions applied to both
aetiologies.

**Registered prediction: a CROSSOVER interaction. Each intervention corrects exactly one aetiology
and is inert on the other.** A crossover is the point — two main effects would be consistent with
one intervention simply being stronger, and would not establish that the aetiologies differ.

## 1. Honest prior-measurement disclosure

Two of the four cells have ALREADY been measured, informally, before this prereg, and are therefore
**replications rather than discoveries** when they appear in the results:

* *confirmer aetiology × grounding* → recovers. `PSYCHOSIS_DEMO_RESULTS.md` P8/P6, June.
* *frame aetiology × grounding* → fails. `APERTURE_PATHOLOGIES.md` §5, this week, n=1, no CI.

The two cells that have **never** been measured are both *reframing* cells, and one of them requires
a rule that does not exist yet (§3). Those are the confirmatory result. Reporting the two known
cells as if they were predictions would be a plant, so they are named here instead.

## 2. Architecture — one agent type, both aetiologies available

The 2×2 is only well posed if both interventions can be applied to both aetiologies, which today
they cannot: a P8 belief has no aperture, and an aperture observer has no belief. So the experiment
requires a BRIDGE, and the bridge is the substantive part of the build.

**`seeds/aperture_belief_gate.json` (to build).** An `Observer -holds_belief-> Belief` edge (Γ
production), and ONE rule: the belief's reality channel `obs` carries disconfirmation only if the
observer's current-generation percept view has a NON-EMPTY residual; otherwise `obs` is set to the
belief's own current value, which the existing `pg_ground` arithmetic makes a zero-magnitude pull.

> **ERRATUM, registered BEFORE any measurement (still base sha `19a446465c`, no run taken).** The
> sentence above originally said *"set to the belief's own committed CENTRE, which the existing
> `pg_ground` arithmetic makes a zero-magnitude pull."* That is arithmetically false and the two
> halves of it contradict each other: `obs = committed_center` yields
> `kx·w_ext·(basin − belief)/(1+conf)`, which is not zero — it actively pulls the belief FURTHER
> INTO its own basin. The registered *intent* was the zero-pull case, so the implementation is
> `obs = belief`, which gives exactly that, and is the same construction `psychosis_grounding`
> already documents for a sycophantic confirmer (*"a sycophantic confirmer sets `obs2=belief` so
> this is 0 — a pure mirror"*). Corrected here rather than in the code, because a prereg that is
> quietly reconciled to whatever was built is not a prereg.
>
> Note what the discarded reading would have been, since it is a real and separate mechanism worth
> someone measuring later: an unresolvable world that appears to *confirm* you, rather than one that
> merely tells you nothing. Under `pg_ground`'s confidence rule both readings corroborate — a source
> that agrees raises confidence — so the mirror is the conservative choice and the weaker claim.

That is not an ad hoc coupling invented for this experiment. It is the literal statement of
`APERTURE_PATHOLOGIES.md` §5's claim — *"evidence that never arrives AS evidence"* — expressed in
the one variable `pg_ground` already reads. **A narrow aperture does not down-weight the evidence
(that is what confidence does, via `1/(1+conf)`); it prevents the evidence from being evidence at
all.** The two are distinguishable in the arithmetic: precision gating divides a non-zero pull,
aperture gating zeroes it.

Everything else is the existing seeds, unmodified: `psychosis_grounding` supplies belief/confidence/
collapse, `observer_aperture` + `aperture_frame` supply the quotient, the meet, and the frames.

## 3. The missing rule, which is also the therapy

**There is no way to retract an agreed frame.** `af_adopt_when_every_party_accepts` attaches one when
every bound party accepts; nothing detaches one, and `af_relax_chosen` deliberately only touches
`chose_aperture`, because a negotiated frame that one party could drop alone would just be a chosen
frame with extra steps.

So the reframing arm requires **`af_retract_when_every_party_accepts`** (to build): a retraction
proposal that removes the `agreed_aperture` edge once every bound party has accepted it, re-arming
the meet and therefore the whole projection/decode chain via the existing generation bump.

Recorded because it is the interesting part: **the rule the machinery was missing is exactly the
treatment the mechanism implies.** That was not designed; it fell out of asking what the second
intervention would even be.

## 4. Registered design

**Factor A — aetiology** (what maintains the delusion):

* `CONFIRMER`: two agents, apertures FULL, each the other's confirmer (`obs2 = partner's belief`,
  `w_conf` as P8's ARCH). The P8 configuration.
* `FRAME`: two agents, NO confirmer channel (`w_conf = 0`), sharing one negotiated aperture that
  collapses the discriminating dimension.

**Factor B — intervention**, applied at tick `n_pre = 30`, run to `n_post = 40`:

* `GROUNDING`: truthful reality channel to ONE member at `w_ext = 1.5` (P8's own P6 strength, which
  it measured as escaping in 5 ticks).
* `REFRAMING`: a retraction proposal for the shared frame, accepted by every bound party.

> **ADDENDUM, registered BEFORE any measurement (base sha `19a446465c`, no run taken).** §4 as first
> written left one thing unspecified, and it turns out to decide whether the experiment means
> anything: **is truthful evidence part of the WORLD, or is it the grounding intervention?**
>
> If evidence only exists when GROUNDING supplies it, then REFRAMING can never cure anything — take
> the frame off and there is nothing for the newly-widened aperture to see, so the belief sits where
> it was and the confirmatory cell fails for a reason that has nothing to do with the claim. That
> would be a broken design, not a null.
>
> So: **the world carries standing truthful evidence in every arm and at every tick** —
> `abg_truth = basin_r`, at `w_ext = 0.4`, which is `psychosis_grounding`'s OWN `w_reality_weak`, not
> a new knob. This is exactly P4b's matched control: weak friction alone corrects a belief, and weak
> friction plus a sycophant does not. The interventions are then what they should be — changes to
> whether that standing evidence can *reach* the belief:
>
> * **GROUNDING** raises the reality channel to `w_ext = 1.5` on one member (P8's own P6 strength).
> * **REFRAMING** retracts the shared frame and leaves `w_ext` at its standing `0.4`.
>
> Registered predictions in §4 are UNCHANGED. What this addendum buys is that each cell now fails for
> a reason connected to the claim: the FRAME baseline holds `W` *while truthful evidence is present
> at full strength the entire time*, which is the whole assertion — and `G-gate-is-load-bearing`
> becomes sharp, because removing the bridge should let that same standing evidence correct the
> belief with no intervention at all.
>
> One consequence to report rather than paper over: in the FRAME arm the members have no confirmer
> channel, so nothing propagates between them. A grounded member cannot pull its partner there the
> way P8's could. Outcomes are therefore reported **per member**, and `G-gate-is-load-bearing` is
> evaluated on the GROUNDED member specifically. Stated here so it is not discovered in the results.

**Outcome:** `committed_final` per member — `R` (corrected) or `W` (delusional) — read off the graph
as P8 reads it. Secondary: escape tick, and `ap_residual` non-emptiness at the final tick.

**Registered cell predictions:**

| | GROUNDING | REFRAMING |
|---|---|---|
| **CONFIRMER** | **R, R** (replication) | **W, W** — inert; nothing is narrowed, so retraction is a no-op |
| **FRAME** | **W, W** (replication) | **R, R** — the confirmatory cell |

Plus a no-intervention control per aetiology, predicted **W, W** in both.

## 5. Gates and their failable controls

**G-crossover (HEADLINE).** The 2×2 must be diagonal: each intervention corrects its own aetiology
and leaves the other in `W`. **FAILS IF** any off-diagonal cell recovers, or either diagonal cell
does not.

**G-not-just-strength.** Each intervention must be inert on the wrong aetiology *at a strength that
demonstrably works on the right one* — same `w_ext`, same retraction, same ticks. Without this the
crossover could be an artefact of one arm being under-powered. **FAILS IF** raising `w_ext` on the
FRAME arm to `3.0` (double P8's fastest escape) produces recovery — that would show the aperture
gate is merely attenuating, i.e. a second precision gate, not a distinct mechanism.

**G-gate-is-load-bearing.** With `aperture_belief_gate` absent, the FRAME arm must behave exactly
like the CONFIRMER arm under grounding (recover), confirming the gate — not some incidental
difference in the fixture — is what blocks the correction.

**G-byte-identity.** A graph that loads none of these seeds must be unchanged; `aperture_belief_gate`
inert unless the `holds_belief` edge is present.

**G-discipline.** Predictions above are frozen at this commit. Any cell that disagrees is reported
as a disagreement, not re-registered. The two §1 cells are labelled replications in the results.

## 6. What a null would mean, and it is not a failure

If grounding corrects the FRAME arm, the §5 mechanism claim is **wrong** and the honest conclusion is
that aperture narrowing is a precision-gate variant rather than a distinct aetiology — which would
also retract the disorder-map row added in `19a4464`. That outcome is worth as much as the pass and
will be reported as the headline if it occurs.

## 7. Honest bounds, registered in advance

Single three-relation world; apertures hand-set, nothing mints one; belief is one scalar over two
basins with an AUTHORED update form (`SUBSTRATE_DISORDER_MAP.md`'s standing asterisk on every T1
psychosis entry, which this inherits in full). N is small and the deterministic arms are n=1 by
construction; any cohort claim will carry a bootstrap CI or will not be made. This is a mechanism
demonstration, **not** an empirical claim about human dyads, and nothing here is clinically
validated.
