# EFFECTOR AUTHORITY IS A WEIGHTED COLLAPSE — prereg

**Status:** design recorded, nothing built. Registered before implementation so
the gates below cannot be chosen after seeing results.

## The correction chain that produced this

Three framings were tried and discarded in one session. Recording them because
each failure names a constraint the design has to satisfy.

1. **"Fill the dark channels."** An audit found 4,122 of 5,688 rule-read
   attributes (72%) carried by nothing in a live 13-hour graph, including the
   whole physical-state vocabulary — orientation quaternion, velocities,
   support forces — and `specified_maximum_position_change_per_action` (7,196
   reads, 0 writes), the amplitude ceiling that reads as 0 through the
   `Plus[Attr, Lit 0]` idiom. Filling them all is the wrong ask: a missing
   reading is only a defect where something depends on it.
2. **"Default to compliance."** Release the effector on unexpected load, low
   tonic by default. REJECTED: it would also make the agent fail to smash
   through a wall it needs to pass. A safety reflex is not a decision.
3. **"Goal instrumentality, binary."** Split the effector space into
   task-relevant and an uncontrolled manifold; ignore deviation in the
   manifold. REJECTED: **it is not zero.** The hand is not ignored during a
   turn — it carries a LOW weight, which rises when damage becomes likely.
   A human does not smash their hand because damage weighs, not because the
   goal suddenly cares about the hand.

## The design

Per-effector authority is a **collapse over incomparable axes**, evaluated
continuously. Not a binary split, not a scalar reward, and **never zero**.

Axes, each a separate objective (this tree refuses scalarisation — "energy and
load remain separate objectives; no reward scalar is invented"):

| axis | reads |
|---|---|
| goal relevance | does moving this effector change the active task variable |
| urgency | how soon the goal needs it |
| potential damage | irreversible cost of a deviation here |
| energy cost | continuous spend of holding it, against the ledger |
| recoverability | can a bad outcome here be undone |

The collapse allocates authority — tonic strength, correction gain, and
priority for scarce sensor resolution. Because no axis is ever zero, an
effector the goal ignores still responds when another axis rises.

### The three cases this must get right, with no case-specific rule

* **Turning; the hand meets a desk.** Goal relevance of hand position is low.
  Potential damage rises as load spikes. The collapse yields or re-routes the
  hand. Not because the turn cares where the hand is — it does not — but
  because damage weighed in. The turn continues.
* **Advancing; a wall blocks the way.** Goal relevance and urgency are high and
  outweigh damage and energy. The agent spends and goes through — admissible
  only while the thermodynamic option margin covers the spend.

* **Falling.** The forward model projects support loss to a crossing. Limbs
  promote by route (b), before contact. A very short `crossing` IS enormous
  urgency — the axis is read off the order-N clock, not hand-tuned — and
  potential damage is high, so the arresting candidates outrank whatever the
  body was doing. **Nothing in the graph knows what a fall is.**

  This completes the phase-change correction: a phase change moves the GOALS,
  and this is the mechanism by which it does — promotion re-populates the
  candidate set and the collapse re-decides.

  Two consequences that fall out rather than being modelled: a depleted body
  CANNOT afford the catch (the ledger gates the spend, which is true of a
  fatigued human); and the catch produces a receipt, so the protective response
  and the acquisition of the recovery capability are the same event — you
  cannot learn recovery without leaving support.

Same machinery, three outcomes, no special case for any of them. A fall
handler, a contact reflex, or a "smash mode" appearing anywhere in the
implementation is a design failure, not a feature.

### SURPRISE IS THE PROMOTION MECHANISM (the resolution)

There is no standing per-effector authority allocation, and no channel carries a
persistent weight.  **A channel is not a candidate until the model is surprised
about it**, by either route:

* **(a) detected** — a measurement contradicts the expectation (the efference
  copy said the hand would sweep free space; contact says otherwise);
* **(b) predicted** — the forward model projects the channel to a boundary
  crossing before it happens.  This is exactly `crossing` from `time_axis`
  v1.2.0 run on the approach stream; `time_to_contact_seconds` is its name in
  the existing rule vocabulary.

Surprise mints a candidate action for that effector, and the EXISTING collapse
(`hdc_collapse_somatomotor_wave_to_one_compound_outcome`,
`smw_collapse_current_wavefront_to_single_program`) decides among candidates on
the axes above.  Nothing new arbitrates.

This is why "not zero" holds without a standing weight: anything can BECOME a
candidate.  The hand is uncontested during a turn because nothing about it is
surprising — not because it was assigned a low priority.

### The consequence that makes the dark-channel audit load-bearing

**A dark channel cannot surprise you.**  With no measurement and no expectation
there is no prediction error, so nothing promotes, so the effector is never
rescued.  Today the humanoid would smash its hand BY BLINDNESS, NOT BY
DECISION: `state_support_0_force` / `state_support_1_force` (351 reads, 0
writes) and `time_to_contact_seconds` (758 reads, 0 writes) are dark.

So the resolution chain is not hygiene — it is what makes surprise possible at
all, and therefore what makes the collapse reachable.  A channel needs
resolution exactly when something could be surprising about it.

## How the three layers compose

| layer | decides |
|---|---|
| authority collapse | whether a deviation is worth anything, and to whom |
| thermodynamic ledger | whether the spend the goal demands is affordable |
| efference default | what is assumed when an instrumental sensor is silent |

"We expect to turn, we assume we have": a silent sensor on a high-weight
channel resolves measured → expected (efference copy) → declared prior →
honest failure, carrying a `_measured` provenance flag throughout, after the
F16 pattern (`state_remaining_fuel_kg_measured`, `channel_reserve_measured`) so
a missing reading is never confusable with a zero one.

Dark channels are resolved **where the collapse gives them weight**, not
globally. A channel nothing weighs is correctly dark; that is not a debt.

## What it lands on (existing, not new)

* collapse: `hdc_collapse_somatomotor_wave_to_one_compound_outcome`,
  `smw_collapse_current_wavefront_to_single_program`,
  `ha_hold_deliberate_task_controller_authority`
* redundancy substrate: `synergy_candidate` (×750), `has_humanoid_synergy_model`
  (×144), `redundancy_kind`
* relevance: `relevance_weight` / `has_relevance_weight`
* ledger: `energy_cost_units` (223 live writes), `peak_load_units` (341); the
  stock term is the one genuinely missing quantity
* order-N clocks: `time_axis` v1.2.0 `TemporalProjection{order_fit, crossing}`
* held theory the agent already carries: `energy_balance` ("Intake =
  expenditure + storage"), `energy_conservation`, first/second laws

## Gates, registered before building

1. **Desk.** Turning with a hand obstructed: the turn completes, the hand
   yields, and no rule drives the hand to setpoint against the obstruction.
2. **Wall.** Advancing with the path obstructed and the ledger in surplus: the
   agent spends and passes. With the ledger short, it does not — and says so.
3. **Not zero.** With goal relevance at its floor for an effector, raising
   potential damage alone changes its allocated authority. A binary
   instrumentality design fails this by construction; that is the point.
3a. **Promotion by surprise, both routes.** An effector no goal is using
   becomes a candidate when a measurement contradicts its expectation
   (detected), AND separately when the forward model projects it to a crossing
   before contact (predicted). The predicted route must fire with no contact
   having occurred — anticipation, not reaction.
3b. **Blindness is a gate failure, not a decision.** With the contact channel
   dark, the desk case must FAIL LOUDLY rather than silently continue into the
   obstruction. A run that smashes the hand because nothing could surprise it
   is the defect this whole line exists to remove.
3c. **The fall, anticipated.** A body losing support promotes arresting
   candidates BEFORE ground contact, and urgency is read off `crossing` rather
   than any authored constant. Measured today this cannot fire at all:
   `standing_reference_z` (2,215 reads / 0 writes), the orientation quaternion
   `state_q{x,y,z,w}`, and `time_to_contact_seconds` (758 / 0) are all dark, so
   there is no channel a fall could be predicted from.
3d. **Affordability binds the catch.** With the ledger depleted, the arresting
   candidate is not affordable and the agent does not take it — and says so.
   A catch that succeeds regardless of the ledger means the ledger is
   decorative.
4. **No scalar.** The collapse exposes its axes separately; no rule reduces
   them to one number before the collapse.
5. **Provenance.** Every value consumed by an authority decision carries
   whether it was measured, expected, or declared. A silent zero anywhere in
   the path is a gate failure.
6. **Ledger honesty.** The affordability test reads a stock that something
   actually writes; a template-only stock fails the gate.

## Honest scope

The dark-channel audit is one checkpoint, one run configuration
(`--seeds embodied`, PyBullet humanoid): a different adapter lights different
channels. `results/dark_channel_runtime_audit.json` carries the list, and the
list is the artifact — never the count.
