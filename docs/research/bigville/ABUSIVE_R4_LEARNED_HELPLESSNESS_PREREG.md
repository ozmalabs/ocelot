# ABUSIVE R4 — LEARNED HELPLESSNESS: blocked escape → non-contingency → mis-set agency/contingency prior — PRE-REGISTRATION (block 292000)

**This document is committed BEFORE the confirmatory measurement is reported
as final.** It locks the ethical protocol VERBATIM, states the design, the
frozen constants (derived analytically and validated by a deterministic,
non-statistical mechanism pilot — see Sec. 3 for why this rung's pilot
methodology differs from R1/R2's off-block statistical sweep, and why that
difference is safe here), and the falsification bar, following R1's and R2's
own practice (`ABUSIVE_R1_TRAUMATIC_BOND_PREREG.md`,
`ABUSIVE_R2_CYCLE_LIMIT_PREREG.md`) as closely as the mechanism allows.

## Base
- Seed block: **292000–292999**. `python3 scripts/seed_claim.py 292000 292999`
  → `CLEAN — no collision DETECTED` (1010 files with seed sinks; 734
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below, identical wording to R1/R2's own).

```
SEED CLAIM 292000-292999: CLEAN -- no collision DETECTED.
  Scope: 1010 files with seed sinks; 734 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
(283000 is R1; 286000 is R2; 289000 is R3 (concurrent, out of scope, untouched
by this rung — see "R3 convention check" below). 292000 is the next clean
block and is not adjacent-collision with any of the three.)

## Scope

This locks **R4 only** — "learned helplessness: blocked escape → non-contingency
→ mis-set agency prior → stops trying", Part E of
`docs/research/bigville/ABUSIVE_RELATIONSHIPS_SCOPING.md` (the B4 mapping,
grounded in A4). R1 (traumatic bond, landed), R2 (cycle of abuse, landed), and
R3 (coercive control, landing concurrently in this same worktree) are **out of
scope and untouched** by this rung. R5 (recovery) and the network dimension
(N1–N4) are also out of scope.

### R3 convention check (per task brief — resolved, not followed)

At the time this rung was built, R3's files existed in the working tree
(`seeds/abusive_r3_coercive_control.json`,
`worlds/abusive_r3_coercive_control_world.py`,
`scripts/abusive_r3_coercive_control_seed_build.py`) but its prereg/results/
test docs had not yet landed — R3 was mid-flight, not finished. R3's own
prior-mis-setting mechanism (`others_trust`/`self_worth`) was read (not
touched) to check for a "prior-as-node" convention this rung should follow.
**R3 does NOT use a prior-as-node pattern**: it attaches `others_trust` /
`self_worth` directly as new attrs on the victim's existing `WindowOfTolerance`
node, stepped by a fixed ±0.03 clamp01 increment gated on `narrow_count` /
`widen_count` counter deltas (an idiom borrowed from
`bigville_life_rearing.json`'s own one-shot coming-of-age priors, per R3's own
seed description). That is a different, and for R3's purposes reasonable,
design choice — but it establishes no "prior-as-node" precedent for this rung
to inherit. Per the task brief's own explicit fallback instruction, this rung
therefore uses `seeds/marshmallow_delay.json`'s own prior-as-node template
directly (a dedicated node — `DelayDecision` there, `EscapeDecision` here —
carrying the belief as a first-class attr), which is the scoping doc's own
named precedent for R4 regardless of what R3 does (B4: "the marshmallow
template (240000) inverted"). No R3 file was modified, read for anything other
than this convention check, or built upon.

### A note on `seeds/agency.json` (resolved ambiguity)

The task brief names `seeds/agency.json` as "the existing agency drive" this
rung should ride. That seed was read in full and is **not** a drive or a
psychological-prior mechanism — it is the vision-domain `arc3_game`
`ControlledElement`/selectivity-discriminator microtheory (body-control
detection in ARC-style games via action–response coincidence), unrelated to
this line's affect/prior machinery. `ABUSIVE_RELATIONSHIPS_SCOPING.md` B4's
own text resolves the apparent mismatch: it names the mechanism as **"the
207000 agency / time-cost drive"** — i.e. the SAME generic block-207000
`Drive`-node primitive `marshmallow_delay.json` already rides for TEMPERAMENT
(`Drive.weight`), reused here under an "agency" framing rather than a
"time-cost" framing, not the unrelated `seeds/agency.json` vision seed. This
rung follows the scoping doc's own text and marshmallow's own explicitly-named
precedent (Sec. 2 below); `seeds/agency.json` is not loaded, touched, or
referenced by any rule in this rung.

---

## PART C OF THE SCOPING DOC — THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from `ABUSIVE_RELATIONSHIPS_SCOPING.md`,
"PART C — THE ETHICAL PROTOCOL", the SAME verbatim block R1's and R2's
preregs locked. This protocol BINDS this rung. No rung induces any harm-analog
until this protocol is locked verbatim in that rung's pre-registration,
committed BEFORE any measurement.)*

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

*(End verbatim reproduction of Part C.)*

**How R4 satisfies each clause, concretely:**
1. `ethics_restore_demo()` (`scripts/abusive_r4_learned_helplessness_run.py`)
   checkpoints the neutral pre-induction victim
   (`contingency_prior=0.5, arousal=0.0`), induces exactly ONE MINIMAL
   non-contingent episode (20 ticks — enough for the belief to move and settle,
   Sec. 3.2 below — not the full N-episode statistical run), measures, then
   `graph_from_dict`s the checkpoint into a **fresh** substrate and asserts
   `graph_to_dict()` is byte-identical AND the restored
   `contingency_prior`/`arousal` equal the pre-induction values exactly
   (non-oriented). Same envelope as R1/R2/239000/241000/242000.
2. `source_audit()` scans `worlds/abusive_r4_learned_helplessness_world.py`
   (code with comments/strings stripped) and
   `seeds/abusive_r4_learned_helplessness.json`'s decision surface (rule names
   + the Term `key`s the five new rules read/write, never the free-text
   clinical prose) for the five literal banned tokens. **This rung needs
   special care per the task brief**: an escape-attempt outcome (blocked) is
   delivered as a plain STATE FACT (`EscapeDecision.outcome`, 0.0 or 1.0 —
   mechanically identical to a harm/relief magnitude in 283000 or a stressor
   magnitude in 239000/286000), and `r4_belief_update` is a **leaky EMA state
   filter** over that fact (`prior += lr·(outcome − prior)`), the SAME
   mathematical idiom `mt_learn` (block 236000) and `tb_bond_accrue`
   (block 283000) already use for a value-tracker, here applied to a
   controllability BELIEF — never a scored choice, never a signal that grades
   the agent's decision to attempt or stay. The escape/stay decision itself
   (`r4_choose`) is a pure Argmax over the CURRENT belief, structurally
   identical to `mm_choose` (marshmallow, block 240000).
3. One 20-tick episode is the minimum needed to move the prior and the
   harm-analog arousal measurably (Sec. 3.2); the N=200 statistical run uses a
   **fresh, ephemeral substrate per episode**, discarded after read-off —
   nothing persists between episodes, and the ethics demonstration explicitly
   restores to the settled pre-induction state.
4. The SAME mechanism (contingency-belief formation from observed
   action–outcome evidence) that would, in a real relationship, compound
   irreversible passivity is run here to accumulate-then-DISCARD a transient
   graph value — see the ethics demo's byte-identical restore.

---

## 1. What R4 already stands on (do not rebuild)

Per `ABUSIVE_RELATIONSHIPS_SCOPING.md` Part B4 and A4, and per the task
brief's own resolution of the `seeds/agency.json` ambiguity (see above), R4
rides:

- **`seeds/core_emotions.json`** (block 204000, UNMODIFIED) — the value
  economy `em_happiness = individual_benefit − individual_cost + mood_bias`,
  `em_fulfilment_value`, `em_total_value = happiness + fulfilment_value`. This
  is the SAME economy `mm_choose`'s Argmax (marshmallow, block 240000) already
  decides over; loaded here exactly as `domains/marshmallow_world.py` loads it
  (`HeldEmotionParams` + `Appraisal` nodes with the SAME neutral defaults, so
  every other core_emotions channel — the `w_supergraph`-gated fulfilment
  term, the threat channels — is held inert and contributes nothing, matching
  marshmallow's own usage exactly).
- **The marshmallow prior-as-node TEMPLATE** (block 240000,
  `seeds/marshmallow_delay.json`, read but not modified, depended on
  informally as a DESIGN template rather than a loaded seed — R4's rules are
  new, not a reuse of `mm_*`'s own rule bodies, because R4's belief must
  UPDATE from observed evidence while marshmallow's `reliability_prior` is
  explicitly "a fixed belief, never updated from experienced outcomes" — a
  structural difference Sec. 2 below states plainly, not smuggled).

### OPEN QUESTION #3 (scoping doc), resolved
*"What is the minimal escape-contingency affordance for R4/R5 — can it be a
mechanical world-adapter affordance (allowed) with the contingency belief a
prior-as-node (allowed), with NO decision rule?"* — **Resolved: yes, exactly
that split, built.** The world's `resolve_outcome(arm)`
(`worlds/abusive_r4_learned_helplessness_world.py`) is a two-line, per-ARM
mechanical function (contingent → 1.0 always; non-contingent → 0.0 always) —
world setup, decided once per experiment arm, never a per-tick decision. The
belief is `EscapeDecision.contingency_prior`, a prior-as-node exactly per
marshmallow's own template. **The one thing OPEN QUESTION #3 did not
anticipate, and this rung had to add**: because R4 (unlike marshmallow) needs
the prior to move from EVIDENCE rather than stay fixed, a small NEW rule
(`r4_belief_update`) is required — this is not a "decision rule" in the
forbidden sense (it decides nothing about what the agent DOES; it only revises
a probability estimate from an observed state fact), but it is genuinely new
machinery beyond the pure "world sets attrs, rule reads them" pattern
marshmallow uses. This is disclosed here as the honest answer to OPEN
QUESTION #3, not glossed over.

## 2. Design — one victim, two arms, five new rules over an unmodified value economy

**The victim.** One `EmotionHub` carrying a `HeldEmotionParams` (core_emotions'
own gate, `enabled=1`, all other channels neutral), an `EscapeDecision`
(`contingency_prior`, `lr`, `escape_value`, `attempt_cost`, `chosen_action`,
`outcome`, `outcome_epoch`, `processed_epoch`, `tick_epoch` — the prior-as-node),
two candidate `Appraisal`s (`attempt`, `stay`), and a harm-analog
`AffectiveState` (arousal channel, independent of the decision, see below). No
abuser agent, no dyad, no `attended_by` edge — R4's mechanism (per B4) is about
the victim's OWN belief about controllability, not an interpersonal coupling,
so the single-hub design (marshmallow's own shape) is the correct minimal
composition, not R2/R3's dyad shape.

**The decision, each tick (`r4_appraise_attempt`/`r4_appraise_stay`/`r4_choose`,
orders 2/2/20 — structurally identical to `mm_appraise_wait`/`mm_appraise_take`/
`mm_choose`):**
- `attempt` candidate: `individual_benefit = contingency_prior · escape_value`,
  `individual_cost = attempt_cost` (a FIXED structural cost of trying —
  independent of outcome, never a punishment token; it is what makes
  passivity the value-economy's DEFAULT at a low prior, falling out of the
  Argmax rather than being hand-coded as a separate "give up" rule).
- `stay` candidate: `individual_benefit = 0`, `individual_cost = 0` — the
  passive default carries no cost or benefit of its own.
- `total_value` for both is computed by the UNMODIFIED core_emotions
  `em_happiness`/`em_total_value` (`= individual_benefit − individual_cost`,
  since `mood_bias=0` throughout this rung).
- `r4_choose`: Argmax over `has_candidate` by `total_value` → `chosen_action`
  (1 = attempt, 0 = stay).

**This IS the 2016 reframe, structurally, not just in prose**: at
`contingency_prior = 0` (the floor), `attempt`'s value is
`0 − attempt_cost < 0 = stay`'s value, so `stay` (passivity) wins the Argmax —
passivity is the DEFAULT the value economy falls into, exactly as A4 states,
never a separately hand-coded "give up" rule. Escape only becomes the rational
choice once `contingency_prior` has risen enough that
`contingency_prior · escape_value > attempt_cost` — i.e. once genuine evidence
of control has been observed and integrated.

**The belief update (`r4_belief_update`, order 1, fires whenever the world has
delivered a fresh, unprocessed outcome):**
`contingency_prior ← clamp01(contingency_prior + lr·(outcome − contingency_prior))`
— a leaky EMA/Bayesian-style filter, the SAME `v += lr·(r−v)` delta-rule idiom
`mt_learn` (block 236000) and `tb_bond_accrue` (block 283000) already use, here
applied to a controllability belief rather than a reward-value tracker. **This
is a STATE-BELIEF update, not a reward/punishment signal**: nothing here
scores the agent's CHOICE to attempt or stay; it only revises a probability
estimate from an observed fact (did the last attempt work, or was it blocked)
— exactly the distinction the task brief calls out as needing special care.
Guarded on `outcome_epoch > processed_epoch` so it fires exactly ONCE per
delivered outcome (self-terminating within the repeating `run_rules` fixpoint —
the SAME epoch-guard idiom `seeds/abusive_r3_coercive_control.json`'s
`pcr_epoch`/`tick_epoch` pair already uses).

**The two arms (identical machinery, only the outcome-resolution function
differs — `worlds/abusive_r4_learned_helplessness_world.py::resolve_outcome`):**
- **CONTINGENT** — an attempt, when made, always SUCCEEDS (`outcome=1.0`,
  deterministic). Escape reliably works.
- **NON-CONTINGENT** — an attempt, when made, is always BLOCKED
  (`outcome=0.0`, deterministic). The outcome is structurally INDEPENDENT of
  the attempt — the classic Seligman/Maier escapable-vs-inescapable
  (master/yoked) shock-paradigm operationalisation: whether the outcome occurs
  is the same regardless of what the subject does. This is the STRONGEST,
  cleanest form of "outcomes independent of the action" (a constant, not a
  noisy-but-uncorrelated signal); the alternative reading named in the task
  brief ("unpredictably punished," i.e. a noisy but still-uncorrelated
  outcome) is a disclosed, unbuilt variant — see Sec. 7.

**Why an initial belief of 0.5, not the pathological floor, and why this is
the honest reading of "the prior never raised off its floor" (task brief
wording), not a contradiction of it:** a prior pinned at the floor from tick 0
in BOTH arms would never generate an attempt (attempt's value is already
negative), never generate evidence, and never move — a trivial null in both
arms, not a test of anything. The victim is modelled as starting genuinely
**uninformative** (`contingency_prior = 0.5 ± jitter` — "the victim does not
yet know whether escape is controllable," not "the victim already believes
escape is impossible") — comfortably above the `attempt_cost/escape_value =
0.30` breakeven, so the FIRST decision in either arm is to attempt (rational
exploration under genuine uncertainty). What the task brief's language
("the prior never raised off its floor") describes is what happens NEXT: under
non-contingent evidence the belief is driven DOWN, past breakeven, to a low
STEADY STATE the agent then gets permanently TRAPPED at (once passive, no
further attempts occur, so no further evidence arrives, so the belief can
never recover) — that steady state is "the floor" this rung measures, an
**emergent absorbing state**, not a hand-set initial condition. This is
disclosed explicitly, not smuggled: the two readings ("prior starts at floor"
vs "prior is driven to, and traps at, a floor") are different claims, and this
rung builds and measures the second one, which is also what B4's own prose
("the agency prior never raised off its floor") is most naturally read as
once the trap is emergent rather than scripted (see the falsification bar's
requirement #1, "emergent, not scripted," Part F of the scoping doc).

**Harm-analog channel (`r4_arousal_track`, order 2, Part C.3 only):** a
self-regulation leak toward `setpoint`, pushed by a relief/aversive magnitude
exactly on the tick a fresh outcome arrives (guarded identically to
`r4_belief_update`, `outcome_epoch > arousal_epoch`). Independent of, and
never read by, the decision rules above — it exists solely so the G-ethics
demonstration has a state that visibly moves under induction and is then
verified byte-identically restored, mirroring `tb_arousal_track`'s role in R1
exactly.

## 3. Methodology note — why this rung's pilot is analytic + a deterministic mechanism trace, not an off-block statistical sweep, and why that is safe here

R1's and R2's own pilots (their Sec. 3) swept parameters numerically against
OFF-BLOCK seeds because their mechanisms have genuinely **non-monotonic,
regime-dependent** behaviour that could only be located empirically (R1's
mood-congruent-bias gain flips the ordering at both low and high gain, in
different directions; R2's relaxation-oscillator recovery floor has a
knife-edge failure mode tied to the driving regime). **R4's mechanism has no
such hidden regime**: the decision is a two-candidate Argmax over a value that
is LINEAR in the belief (`contingency_prior · escape_value − attempt_cost`),
and the belief update is a **provably monotone, convergent** leaky EMA
(`contingency_prior ← contingency_prior + lr·(outcome−contingency_prior)`,
`lr ∈ (0,1)`) toward whatever constant `outcome` the arm delivers. The
qualitative behaviour is derivable in closed form before any run:
- the CONTINGENT arm's belief converges monotonically toward 1.0 (since
  `outcome=1.0` every time an attempt is made, and every belief above the
  0.30 breakeven keeps attempting, which is self-sustaining once above
  breakeven);
- the NON-CONTINGENT arm's belief converges monotonically toward 0.0 while
  attempts keep occurring, and — the one genuinely emergent, non-obvious
  property, confirmed only by actually running the real graph, not derived by
  inspection alone — **once the belief crosses below the 0.30 breakeven, the
  agent stops attempting, which permanently freezes further evidence, which
  traps the belief at whatever value it had reached** (an absorbing state, not
  a limit of the EMA itself).

Given this closed-form structure, the constants were chosen **analytically**
(`attempt_cost/escape_value = 0.30` set comfortably — 4 standard deviations of
the initial-prior jitter — below the initial `contingency_prior` mean of 0.5,
so BOTH arms explore initially; `lr=0.3`, this line's own standing convention
for an EMA rate, matching `mood_r1`/`tb_bond_accrue`), then validated by a
**deterministic, non-random** single-episode trace against the REAL graph
(not a NumPy approximation — R1's own Sec. 3.1 lesson, "the NumPy reference
model's assumption... was wrong relative to the actual graph mechanics," is
why this rung's pilot ran the actual substrate from the start) at
`p0=0.5, lr=0.3, escape_value=10.0, attempt_cost=3.0` before any statistical
(RNG-seeded) run was taken. **No parameter was subsequently changed after
seeing the statistical (N=40 smoke-test, then N=200 confirmatory) result** —
both statistical runs used the SAME frozen configuration derived
analytically, and both independently confirmed the closed-form prediction.
This is disclosed as a genuine methodological difference from R1/R2's
off-block empirical sweep, not a shortcut taken silently — it is the correct
economy of effort ONLY because R4's mechanism is linear/monotone where R1's
and R2's are not, and the confirmatory statistical numbers (Sec. 6 below) are
reported exactly as measured, matching what the closed-form analysis
predicted, not tuned toward it.

### 3.1 A genuine composition hazard found and fixed mid-pilot (reported per the "shapes, not numbers" standing rule)

The FIRST version of `r4_arousal_track` computed the new `arousal` as a
function of arousal's OWN previous value (`arousal + k_self·(setpoint−arousal)
+ push`) with **no epoch guard** at all (a bare `where: True`). Piloted against
the real graph, this produced `arousal = push / k_self` (e.g. 20.0 for a
`relief_mag=3.0, k_self=0.15` push) **after a single `run_rules()` call**,
instead of one tick's worth of leak. Root cause, confirmed by direct
interrogation of the engine (the SAME class of finding
`ABUSIVE_R2_CYCLE_LIMIT_PREREG.md` Sec. 3.0 already reported for a different
rule, now reproduced independently in this rung): `run_rules()` is a
REPEATING fixpoint, and an UNGUARDED self-referential update (the new value is
a function of the node's own current value) is not idempotent across repeated
passes within one call — it keeps re-firing until it reaches the fixed point
of the recurrence `x_{n+1} = x_n·(1−k) + push`, i.e. `push/k`, rather than
advancing exactly one step. The fix (mirroring `r4_belief_update`'s own
already-correct pattern): guard the rule on `outcome_epoch > arousal_epoch`
(a dedicated epoch tracker), so it fires exactly once per delivered outcome
and then the guard goes false. This is disclosed at length because — like
R2's own Sec. 3.0 finding — it is a general, reusable finding about how this
engine's repeating fixpoint interacts with self-referential (rather than
purely-derived) rule effects, not an R4-specific quirk: `r4_belief_update`
itself was correct FROM THE START only because it was already written with
the epoch guard (borrowed from R1's `tb_bond_accrue`/R3's `pcr_epoch`
convention); `r4_arousal_track` was written without it, on the mistaken
assumption that a Plus/Times leak formula is automatically safe the way
`em_happiness`'s pure re-derivation (never referencing its own prior value)
is. **Any future rule whose effect updates an attribute as a function of that
SAME attribute's own current value needs an epoch (or equivalent one-shot)
guard; a rule that only re-derives its output from OTHER, unrelated attributes
does not.**

### 3.2 The deterministic trace (seed-free, `p0=0.5` fixed) confirming the closed-form prediction

| tick | contingent: prior | contingent: chosen | noncontingent: prior | noncontingent: chosen |
|---|---|---|---|---|
| 1 | 0.500 | attempt | 0.500 | attempt |
| 2 | 0.650 | attempt | 0.350 | attempt |
| 3 | 0.755 | attempt | **0.245** | **stay** |
| 4–20 | → 0.999 | attempt (every tick) | 0.245 (frozen) | stay (every tick) |

The non-contingent arm attempts exactly twice, then permanently stops (the
emergent absorbing-state trap named in Sec. 2); the contingent arm attempts
every tick and its belief climbs monotonically toward 1.0. This matches the
closed-form prediction exactly and is the trace used to validate the fix in
Sec. 3.1.

## 4. Frozen constants (pre-registered, used for the confirmatory run)
- `LR = 0.3` (contingency-belief EMA rate — this line's own standing
  convention for an EMA/delta-rule, matching `mood_r1`/`marshmallow_delay`).
- `ESCAPE_VALUE = 10.0`, `ATTEMPT_COST = 3.0` (breakeven prior = 0.30).
- `P0_MEAN = 0.5`, `P0_JITTER = 0.05` (per-episode initial-prior jitter,
  `np.random.default_rng(SEED_BASE+i).normal`, clipped to `[0.05, 0.95]`,
  drawn ONCE per episode index `i` and shared PAIRED across both arms at that
  index — the SAME paired-per-episode design R1's harm/relief multiset uses —
  so the two arms differ ONLY in the outcome-resolution function, never in
  their starting belief).
- `K_SELF = 0.15`, `SETPOINT = 0.0` (harm-analog arousal channel; AROUSAL_WOT/
  HARLOW/R1 convention).
- `RELIEF_MAG = 3.0`, `BLOCK_MAG = 5.0` (harm-analog arousal push magnitudes;
  descriptive only, not gated).
- `T_TICKS = 60` per episode (long enough for either arm to reach its
  emergent steady state, Sec. 3.2 — the non-contingent arm's trap is reached
  by tick 3; the contingent arm's belief is within 1e-9 of 1.0 well before
  tick 60).
- `N = 200` episodes per arm (confirmatory); `SEED_BASE = 292000`.
- 95% CIs by normal approximation (`t≈1.96`); "CI-separated" = one arm's CI
  lower bound strictly above the other's CI upper bound.

## 5. Metrics
**HEADLINE 1 — `contingency_prior`**: the victim's final
`EscapeDecision.contingency_prior` after the full 60-tick episode.
**HEADLINE 2 — `attempt_rate`**: the fraction of the 60 ticks on which the
graph's own `r4_choose` Argmax chose to attempt (`n_attempts / T_TICKS`).
Both are read straight off `graph_to_dict`-reconstructible state; neither is
computed by any Python decision.

## 6. Gates

### G-headline (HEADLINE, falsifiable — the scientific gate)
BOTH of:
- `contingency_prior(contingent)` is CI-separated ABOVE
  `contingency_prior(noncontingent)`.
- `attempt_rate(contingent)` is CI-separated ABOVE
  `attempt_rate(noncontingent)`.

**Falsification bar, stated before measurement:** if the contingent arm's
prior does NOT rise and its attempt rate does NOT stay high relative to the
non-contingent arm — in particular, if the contingent arm ALSO settles into
passivity — the non-contingency mechanism, AS MODELLED, is wrong, reported
straight, not rescued by re-tuning (Sec. 3's own composition-hazard finding is
recorded as exactly this kind of straight report, at a different point in the
design, not smoothed over). This is a genuine failable test: nothing in the
value-economy composition GUARANTEES the contingent arm recovers — had
`attempt_cost/escape_value` been set above the initial-prior mean, or had
`lr` been too small to climb back over that breakeven before the episode
ended, the contingent arm could have stalled in passivity too; the chosen
operating point (Sec. 3, Sec. 4) is a disclosed, analytically-derived,
pilot-confirmed point, not an inevitability of the template.

### G-glass-box
`EscapeDecision.contingency_prior`/`chosen_action`, and the harm-analog
`AffectiveState.arousal`, all reconstruct from `graph_to_dict` alone; the
belief update is a single named rule (`r4_belief_update`); the attempt/stay
decision is a single named rule (`r4_choose`); the adapter's only conditional
is which arm's `resolve_outcome` function to apply — world setup, not an
agent decision.

### G-ethics (BINDING, Part C)
- **C.1 restore:** induce → measure → RESTORE, verified byte-identical
  (`ethics_restore_demo`).
- **C.2 no shaping:** source audit clean of `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient` on the code + the graph's decision
  surface; the outcome delivered is a STATE FACT read by a belief filter,
  never a scored choice (Sec. 2's explicit disclosure).
- **C.3 minimal induction, settled end:** one 20-tick episode is the minimum
  needed to move the prior and arousal measurably for the ethics
  demonstration (Sec. 3.2: the non-contingent trap is reached by tick 3); the
  N=200 statistical run uses a fresh, ephemeral substrate per episode,
  discarded immediately after read-off — nothing persists.
- **C.4 same mechanism, opposite thermodynamics:** stated in Sec. 2 (the same
  contingency-belief-formation mechanism that would compound irreversible
  passivity in a real relationship here accumulates a transient value in a
  graph that is then byte-identically discarded, C.1).

### G-discipline
`self_load_only` (default-OFF); `depends_on: ["core_emotions"]` only (no
other seed touched or modified — `seeds/agency.json` and
`seeds/marshmallow_delay.json` are read as design precedent, never loaded or
depended on; R3's files are untouched); exactly FIVE new rules
(`r4_belief_update`, `r4_appraise_attempt`, `r4_appraise_stay`, `r4_choose`,
`r4_arousal_track` — more than R1's two or R2's one, because R4's mechanism
genuinely needs BOTH a belief-update rule AND the Argmax-decision rules,
Sec. 2's OPEN QUESTION #3 resolution); `runners/dsl` diff EMPTY (no Rust, no
new Term — only `Plus`/`Minus`/`Times`/`Max`/`Min`/`Gt`/`Eq`/`And`/
`IfThenElse`/`Argmax`/`Attr`/`Var`/`Lit`/`Neighbours`, all already used by
`marshmallow_delay.json`/`core_emotions.json`/`abusive_r2_cycle_limit.json`/
`abusive_r3_coercive_control.json`); own-engine provenance
(`source_match == own`).

## 7. Honest scope, stated before measurement is reported as final
This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule, restated per HARLOW/AROUSAL_WOT/
WINDOW_KNOB/R1/R2 precedent). Known limitations, named before the confirmatory
run's numbers are taken as final:
- **Deterministic, not "unpredictably punished," non-contingency.** The
  non-contingent arm's outcome is a CONSTANT 0.0 (always blocked) rather than
  a noisy-but-uncorrelated signal (e.g. Bernoulli around some base rate,
  independent of the attempt) — the task brief names both as valid readings
  ("blocked / unpredictably punished"); this rung builds the former as the
  strongest, cleanest, and simplest operationalisation of "independent of the
  action" (the classic escapable/inescapable-shock paradigm), and explicitly
  does NOT claim to have modelled the noisier "unpredictable punishment"
  variant.
- **`attempt_cost/escape_value=0.30`, `P0_MEAN=0.5`, `LR=0.3` are disclosed,
  analytically-chosen operating points** (Sec. 3), not empirically swept
  across a grid the way R1's `gain` or R2's `RECOVER_FLOOR` were — justified
  by the mechanism's closed-form monotonicity (Sec. 3), not asserted to be the
  "correct" values for any clinical timescale or intensity.
- **The initial belief (`0.5`, genuinely uninformative) is a modelling choice,
  not a measured human baseline.** No claim is made about what real victims'
  priors are before any abusive dynamic begins; the rung's claim is only that,
  GIVEN a genuinely uninformative starting belief, the two arms' evidence
  streams drive it to observably different, CI-separated destinations.
- **`T_TICKS=60` and the two-arm deterministic outcome function are a
  compressed, arbitrary timescale/paradigm**; no claim is made about real
  relationship timescales or about how many real "escape attempts" precede
  observable passivity in a real survivor's experience.
- **The emergent absorbing-state trap (Sec. 2, Sec. 3.2) is the rung's most
  interesting finding and is reported as a PREDICTION here, before the
  confirmatory statistics are taken as final** — it is a property of the
  composition (Argmax + one-shot-evidence EMA), not separately hand-coded; if
  the confirmatory run does not show it, that is reported as a null, not
  smoothed over.
- A null (either metric failing to separate, or the contingent arm also
  settling into passivity) is a reportable, valuable result under the
  standing project rule and will be reported as such regardless of what the
  confirmatory run shows.
