# ABUSIVE R5 — LEAVING/RECOVERY: the integrative reversal of R1–R4 — PRE-REGISTRATION (block 295000)

**This document is committed BEFORE the confirmatory measurement.** It locks
the ethical protocol VERBATIM, states the design, the frozen constants
(pilot-chosen, non-confirmatory, off-block), and the falsification bar.

## Base
- Seed block: **295000–295999**. `python scripts/seed_claim.py 295000 295999`
  → `CLEAN — no collision DETECTED` (1012 files with seed sinks; 739
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below).

```
SEED CLAIM 295000-295999: CLEAN -- no collision DETECTED.
  Scope: 1012 files with seed sinks; 739 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## Scope

This locks **R5 only** — "leaving/recovery dynamics", Part E of
`docs/research/bigville/ABUSIVE_RELATIONSHIPS_SCOPING.md` (the dyad line).
R5 is the explicit INTEGRATIVE rung: it composes R1 (`traumatic_bond_r1`,
block 283000), R2 (`abusive_r2_cycle_limit`, block 286000), R3
(`abusive_r3_coercive_control`, block 289000), and R4
(`abusive_r4_learned_helplessness`, block 292000) — all already landed on
`main`, all read but **none touched, none edited**. The network dimension
(`ABUSIVE_RELATIONSHIPS_NETWORK.md`, N1–N4) is out of scope and untouched.

---

## PART C OF THE SCOPING DOC — THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from `ABUSIVE_RELATIONSHIPS_SCOPING.md`,
"PART C — THE ETHICAL PROTOCOL". This protocol BINDS this rung. No rung
induces any harm-analog until this protocol is locked verbatim in that rung's
pre-registration, committed BEFORE any measurement.)*

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

### What R5 changes about what "induction" even means

R1–R4 each induced a harm-analog as a means to a measurement end. **R5
inverts the relationship between induction and the phenomenon under study.**
Per the scoping doc's own framing of this rung: *"R5 is where RESTORE is not
just the ethical envelope but the modelled PHENOMENON — the recovery IS the
restoration of the dismantled priors/frontier/contingency."* Concretely: R5
still inductes a harm-analog first (it must — there is no "recovery" to
measure without a trap to recover from, and reusing R1–R4's own machinery to
build that trap is the whole point of composing this line rather than
re-deriving it), but the **object of measurement is not the trap** — it is
what happens AFTER, when one variable (an outside support source) is
introduced. R5 therefore induces the trap with the SAME minimality standard
Part C.3 already requires (the shortest induction that makes R1–R4's own
findings reproduce inside this composed substrate — Sec. 2 below), and then
spends the REST of the run inside the ethically-neutral direction: watching
priors, a window, and a bond relax back toward their pre-trap values. Every
trajectory — support arm AND no-support control alike — ends from a settled
state (Sec. 6, C.3), which for R5 is not merely a procedural requirement but
literally what "recovery" being measured looks like when it succeeds. This
is also, per the scoping doc's Part D, the rung whose measurement is the
literal object the whole line exists to serve: helping survivors is not a
downstream implication of R5's result, it is what R5's headline gate is
directly testing for.

---

## 1. What R5 already stands on (do not rebuild)

R5 composes FOUR already-built, unmodified seeds via `depends_on`, reusing
their rule bodies verbatim — no rung's files are forked, edited, or
duplicated:

- **R1** (`seeds/traumatic_bond_r1.json`) — `tb_bond_accrue`/`tb_arousal_track`,
  riding `mood_r1`/`mood_r1_task`/`affective_state_core` unmodified.
  `Partner.value` is a **monotone accumulator** (only ever adds a
  strictly-positive `raw_rpe` swing) — no decay term anywhere in this
  seed, or anywhere else in the line.
- **R2** (`seeds/abusive_r2_cycle_limit.json`) — `r2_victim_entrainment_via_frustration`,
  riding `snap_frustration`/`arousal_window_coreg` unmodified. Routes the
  abuser's leaky-integrate-fire relaxation oscillator into the victim's
  `frustration` attr (not `arousal` directly — R2's own documented
  composition hazard, Sec. 3.0 of its prereg: `snap_arousal_track`
  unconditionally overwrites `arousal := setpoint+frustration` on every
  `has_affective_state` node, so any entrainment rule MUST write through
  `frustration`, never fight that commit directly).
- **R3** (`seeds/abusive_r3_coercive_control.json`) — five rules:
  `r3_victim_entrainment_solo`/`_dyad` (gated on the victim's
  `has_outside_regulator` flag), `r3_mark_coreg_support_outside` (mirrors
  `arousal_window_coreg`'s own `mark_coreg_support`, but matching the
  `also_attended_by` edge type instead of `attended_by` — R3's own
  documented composition hazard, Sec. 3 of its prereg: TWO outgoing edges
  of the SAME type from one node corrupted a DIFFERENT rule's cross-node
  attribute reads whenever `arousal_window_coreg`'s `selfreg_pull` was also
  loaded; the fix was to give the outside regulator a genuinely distinct
  edge type), and `r3_prior_track_narrow`/`_widen` (step
  `others_trust`/`self_worth` on the victim's `WindowOfTolerance` node by
  `±0.03` off `arousal_window_coreg`'s own `widen_count`/`narrow_count`
  deltas).
- **R4** (`seeds/abusive_r4_learned_helplessness.json`) — `r4_belief_update`,
  `r4_appraise_attempt`/`_stay`, `r4_choose`, riding `core_emotions`
  unmodified. `EscapeDecision.contingency_prior` only ever revises from
  evidence delivered on the `outcome_epoch`/`processed_epoch` channel of an
  ATTEMPT the agent itself just made — and R4's own results doc names the
  resulting trap explicitly: once the prior crosses the attempt/stay
  breakeven (`attempt_cost/escape_value = 0.30`), the agent stops
  attempting, which cuts off the ONLY channel that could ever deliver fresh
  evidence, so **the belief freezes and cannot self-repair** ("the emergent
  absorbing-state trap", `ABUSIVE_R4_LEARNED_HELPLESSNESS_RESULTS.md`).

**Neither R1's bond accumulator nor R4's belief-update channel has any
built-in way to reverse.** This is not an oversight in R1/R4 — they were not
designed to model recovery, only the trap — but it means R5's own
composition must supply exactly two things the four prior rungs, alone,
structurally cannot: a way for the bond to weaken, and a way for the
contingency belief to be revised WITHOUT requiring the already-frozen agent
to attempt first. Sec. 2 states R5's answer to both, and why each is the
smallest possible addition rather than a new subsystem.

## 2. Design — the composition, and why this is the hardest call in the whole line

### 2.1 One dyad, one victim node, three roles

R5 builds **one composed substrate**: an ABUSER `Agent` node (R2/R3's own
leaky-integrate-fire relaxation-oscillator contract, unmodified) and one
VICTIM `Agent` node that simultaneously carries R2/R3's entrainment
apparatus (`AffectiveState` + `WindowOfTolerance`), R1's bond apparatus
(`MoodTask` + `Mood`), and R4's escape apparatus (`EscapeDecision` +
`HeldEmotionParams` + two candidate `Appraisal` nodes) — **all on the SAME
node**. This is possible, and safe, because every rule `match` array in this
engine's rule format is **structural** (edge type + bound variable), never
filtered by the literal type string passed to `add_node` — confirmed by
reading R1–R4's own world adapters, which already rely on exactly this (R4's
own module docstring states its `AffectiveState`/`has_affective_state`
naming "borrows `affective_state_core`'s contract as a naming convention
ONLY"). `tb_bond_accrue` matches `hub -has_mood_task-> mt`,
`hub -bonded_to-> partner`; `r4_choose` matches
`hub -has_escape_decision-> dec`; `r2/r3`'s entrainment rules match
`victim -has_affective_state-> vaff`, `victim -attended_by-> abuser`. None
of these care what `victim` is called or what other edges it also carries.

**The bond target is the abuser's OWN Agent node**, not a separate `Partner`
node (R1's own convention). This is a genuine, disclosed R5-specific
composition choice: the bond IS to the abuser (the entity whose entrainment
produces the harm/relief swings), so `Partner.value`/`e_bond` live directly
on the abuser node, alongside its `snap_frustration` contract. `bonded_to`
is a second, distinct edge type from `victim` to `abuser` (alongside
`attended_by`) — two edges of DIFFERENT types from the same source, not the
same-type-duplication shape R3's own hazard requires avoiding.

### 2.2 Two structural phases, mirroring Herman's staged recovery

- **INDUCTION** (ticks `0..T1`) — **identical in both arms.** The abuser's
  tension trickle runs continuously (R2/R3's own mechanism); the bond
  channel receives R1's OWN validated INTERMITTENT harm/relief multiset,
  reused directly via `make_schedule` (imported, not reimplemented, from
  `worlds.traumatic_bond_r1_world`); the escape channel receives R4's OWN
  validated NON-CONTINGENT outcome resolution, reused directly via
  `resolve_outcome` (imported from
  `worlds.abusive_r4_learned_helplessness_world`). This reproduces, inside
  ONE substrate, R1's bond-strengthening finding, R2/R3's
  window-narrowing/anchor-tracking finding, and R4's freeze finding, all at
  once — before any recovery mechanism is touched.
- **RECOVERY** (ticks `T1..T1+T2`) — the ONLY manipulated variable.
  **NO-SUPPORT arm** (the failable control): every channel continues
  EXACTLY as in induction — same abuser driver, same intermittent bond
  schedule, same non-contingent escape resolution. **SUPPORT arm**: ONE
  mechanical world event, `introduce_support()`, fires at tick `T1`. It:
  1. Adds an `also_attended_by` edge from the victim to a fixed-calm
     outside `Agent` and flips `has_outside_regulator=1.0` — R3's OWN
     unmodified outside-regulator mechanism, exercised for the FIRST TIME
     in this line from an ALREADY-NARROWED starting window (R3's own
     honest residual named this exact repair path as built-but-untested:
     *"the outside-regulator arm's window holds by PREVENTING
     dysregulation, not by repeatedly REPAIRING it... this specific
     operating point produces a STRONGER result than minimally required —
     full prevention rather than episodic repair"* — R3 never tested
     recovery FROM an already-narrowed window because its own arms never
     let the window narrow first. R5 is that test.)
  2. Stops delivering fresh bond events (a mechanical world fact —
     reduced abuser access — never a graph-state-dependent branch), so
     R5's own new decay rule dominates.
  3. Begins delivering periodic, FIXED-SCHEDULE support evidence on a
     SECOND, INDEPENDENT contingency-belief channel, and switches any
     FUTURE escape attempt's outcome resolution to CONTINGENT (support
     makes a genuine attempt possible again).

### 2.3 R5's own new composition — exactly two rules

- **`r5_bond_extinguish`** (order 4, after `tb_bond_accrue`'s order 3) — a
  constant, proportional per-tick decay on `Partner.value`
  (`value *= 1 - decay_rate`), epoch-guarded (`mt.input_epoch >
  partner.e_extinct`) so it advances by exactly one tick's worth of decay
  per tick, not the fixpoint's own converged value (the SAME
  self-referential-write hazard R2's Sec. 3.0 and R4's Sec. 3.1 already
  named and fixed the same way — applied here proactively, verified
  empirically to behave correctly during piloting, Sec. 3.2). This is A3's
  own flip side (`ABUSIVE_RELATIONSHIPS_SCOPING.md`): the partial-
  reinforcement extinction effect states that INTERMITTENT reinforcement
  makes a response maximally resistant to extinction; take the
  reinforcement away ENTIRELY (not just make it less frequent) and the
  standard operant prediction is that the response DOES eventually
  extinguish. R1 built the first half of A3 (a scheduled, intermittent
  stream STRENGTHENS the bond). R5 builds the second half (removing the
  stream lets it decay) — genuinely new to the line, because R1's own
  rung never needed it (a single 36-tick episode never runs long enough
  for decay to matter). The rule runs identically, unconditionally, in
  BOTH arms and BOTH phases — whether the bond nets upward or downward is
  a WORLD fact (does fresh reinforcement keep arriving faster than the
  leak), never a rule-level arm switch.
- **`r5_contingency_restore`** (order 1, matching `r4_belief_update`'s own
  order) — a SECOND, INDEPENDENT leaky-EMA revision of
  `EscapeDecision.contingency_prior`, the SAME `v += lr*(observation-v)`
  idiom `r4_belief_update` already uses, but reading evidence delivered on
  a DISTINCT epoch pair (`support_epoch`/`support_processed_epoch`/
  `support_outcome` — never touching `outcome_epoch`/`processed_epoch`).
  This is the piece that makes recovery possible AT ALL given R4's own
  documented trap: `r4_belief_update` can only ever fire when the agent
  ITSELF attempts, and R4's own results doc shows the agent permanently
  stops attempting once the prior crosses breakeven — so no amount of
  waiting inside R4's own machinery alone would ever revise a frozen
  belief. `r5_contingency_restore` supplies a channel that does not
  require an attempt: an outside witness/demonstration can move the belief
  even while the agent is passive. Once the belief crosses back over
  breakeven, `r4_choose` (unmodified, still live every tick) naturally
  resumes choosing to attempt — no rule here touches `chosen_action`.

Nothing else is new. Window widening, `others_trust`/`self_worth` recovery,
and the anchor-tracking readout are all R3's own unmodified machinery,
reused as-is.

### 2.4 Why this composition, and not another

The task brief named the hardest design call explicitly: how to reuse
R1–R4's atoms rather than reimplementing bond/window/anchor/contingency from
scratch. Three alternatives were considered and rejected:

1. **Run R1's bond channel on its own, separately-scheduled event stream**
   (as R1's own world does), decoupled from R2/R3's actual entrainment
   dynamics. Rejected: this would make the bond's strengthening-then-
   weakening a PARALLEL, independently-scripted phenomenon rather than a
   genuine reversal of the SAME trap the window/anchor/contingency channels
   are also measuring — it would answer "does *a* bond weaken when *a*
   schedule stops," not "does *this dyad's* bond weaken when *this* trap
   starts to lift." R5 instead reuses R1's OWN validated intermittent
   schedule (`make_schedule`, imported unmodified) as the MECHANICAL event
   source, but times its delivery to the SAME induction/recovery phase
   boundary every other channel uses, so all four metrics describe one
   coherent trajectory, not four uncoordinated ones.
2. **Derive the bond's harm/relief swing directly from R2/R3's own
   `in_episode`/dysregulation state**, so the bond channel needs no
   separate schedule at all. This is an appealing, even smaller
   composition, and was piloted; it is NOT what shipped, for a disclosed
   reason: R1's mood-momentum bias-amplification loop (`gain`) is tuned
   against a SPECIFIC, bounded event count (one 36-tick, `H=R=18` episode).
   Feeding it a schedule keyed to how often the abuser happens to
   dysregulate the victim over hundreds of ticks removes any control over
   the total dose delivered, which (Sec. 3.1) turns out to matter a great
   deal for numerical stability. R5 keeps R1's own validated `H=R=18`/`T=36`
   block as the atomic unit and composes MULTIPLE such blocks
   mechanically, rather than deriving a variable-dose stream from graph
   state.
3. **Give the bond channel its own AffectiveState node**, separate from the
   one R2/R3's entrainment rules use, to avoid any possibility of
   `tb_arousal_track` (R1's own decorative, non-bond-affecting arousal
   tracker) colliding with `snap_frustration`'s unconditional
   `arousal := setpoint+frustration` overwrite. This was piloted and found
   UNNECESSARY (Sec. 3.3): `tb_arousal_track`'s write is silently
   overwritten later in the SAME tick by `snap_arousal_track` (a strictly
   higher rule order), which is inert, not incorrect — the bond metric
   (`Partner.value`, read via `tb_bond_accrue`, which never touches
   `AffectiveState.arousal` at all) is unaffected. Introducing a second
   node purely to avoid a provably-harmless overwrite would have been
   unmotivated complexity, so R5 shares ONE `AffectiveState` node across
   R1's and R2/R3's contracts, verified safe empirically (Sec. 3.3), not
   merely assumed.

### 2.5 Why the no-support control could genuinely fail

Nothing in R5's own two new rules or in R1–R4's reused rules PREVENTS the
no-support arm from recovering on its own. `r5_bond_extinguish` runs
UNCONDITIONALLY in both arms — if the no-support arm's continuing
intermittent schedule failed to outpace the fixed decay rate, its bond
would ALSO net downward, and the "outside support is necessary" claim would
be wrong. Similarly, nothing prevents `arousal_window_coreg`'s own
`episode_resolve_widen` from firing under single-anchor topology if the
abuser ever happened to satisfy `mark_coreg_support`'s `regulated==1`
condition — it structurally never does (R2's own honest residual, quoted in
R3's module docstring), but that is a fact about `snap_frustration`'s
mechanism, not something R5 enforces. The control is real, and Sec. 3
reports exactly how it was verified to behave as a trap, not assumed.

## 3. Pilot (non-confirmatory, off-block seeds `199000+`, informs the frozen constants only)

### 3.1 A genuine numerical instability found and fixed — the bond channel's `gain`

R1's own frozen `gain=3.5` (the mood-congruent bias sensitivity) was
validated for EXACTLY one 36-tick, `H=R=18` episode from a fresh substrate
(`v=momentum=0` at start). Piloting R5's induction phase by sizing ONE
intermittent multiset to fill the ENTIRE phase length (`h=r=T1//2`, matching
the shape of R1's own `make_schedule` call but scaled up) produced
**unbounded, super-linear growth**: `bond_value` at `T1=200/400/600` was
`2413.65 / 25769.12 / 112101.11` — not the roughly-linear scaling a stable
mechanism would show, and nowhere near R1's own single-episode value (~265).
Delivering MULTIPLE consecutive R1-sized blocks back-to-back (rather than
one giant multiset) reproduced the SAME runaway growth at the same total
event count (`n_blocks=2/5/10/15` → `bond=312/1893/10752/54678`) — ruling
out "multiset size" as the cause and confirming it is the CUMULATIVE
compounding of the mood-congruent bias loop across many consecutive events
without a reset that pushes the mechanism into the "explosive regime" R1's
own prereg already named and warned about at its OWN high-gain, short-`H`
operating points (*"at very high gain (≥6) combined with short episodes
(H≤15)... the separation can flip the wrong way"*). Diagnosed further:
mood_r1's `v` (fast value estimate) can be driven so far from `0` by
compounding bias that even a **zero-magnitude** tick (`r=0`, no fresh event
at all) registers as a large POSITIVE surprise relative to the depressed
baseline (`raw_rpe = 0 - v > 0` when `v` is very negative) — so at high
gain, `tb_bond_accrue` kept accruing every tick even during a scheduled
zero-event period, defeating the entire "stop delivering events, let it
decay" design for the recovery phase.

**Fix, verified not assumed:** lower `gain` to `1.0` — `mood_r1`'s OWN
pinned default value (R1's own prereg used `3.5` as a DISCLOSED deviation
specifically because R1's task needed a short-episode 3-way schedule-order
comparison to separate; R5's task is different — a bounded, decaying
equilibrium over a much longer run — and does not need that amplification).
At `gain ∈ {1.0, 1.5, 2.0}` with continuous R1-sized blocks filling the
WHOLE induction phase and a modest decay rate, `bond_value` converges to a
STABLE, bounded equilibrium (`gain=1.0, decay=0.01`: `T1=396` → `495.69`;
`decay=0.005` → `871.91`; `decay=0.02` → `249.65` — monotone in decay rate,
as expected of a stable accrual/decay balance, not runaway). `gain=1.0` was
chosen as the frozen value: the smallest deviation from precedent
(mood_r1's own default, not a new number), and it produces the same
qualitative behaviour as `1.5`/`2.0` (all three sit within ~10% of each
other at matched decay), so nothing was tuned toward a preferred outcome —
any of the three would have worked.

### 3.2 Verifying the "stop delivering events" design actually differentiates the arms

With `gain=1.0`, `decay_rate=0.01`, continuous R1-blocks filling BOTH `T1`
and `T2` in the no-support arm and only `T1` in the support arm (`T2`
receiving an all-zero bond stream once support begins), one paired
trajectory (`seed=199040`, both arms starting from the byte-identical
random state through the end of induction — confirmed: both arms' `T1`-end
readouts are IDENTICAL): `bond_value` at end of recovery —
**no-support 524.65, support 9.55** (a >50x reduction). Window `half_width`
at end of recovery — **no-support 5.00 (still at floor), support 13.00**
(above even the pre-trap initial width of 10.0 — widening, once the widen
path finally engages from an already-narrowed start, is unbounded, per
`arousal_window_coreg`'s own `episode_resolve_widen`, which has no ceiling
term). `contingency_prior` — **no-support 0.2450 (frozen, matching R4's own
reported floor exactly), support 1.0000** — and escape-`attempt_rate` over
the recovery phase — **no-support 0.0000, support 0.9520**. All four numbers
move in the predicted direction, on one representative paired trajectory,
before any statistical run.

### 3.3 An honest null found during piloting, disclosed here rather than after the confirmatory run

The fourth metric, **mean abuser-tracking distance** (`abuser_proximity`,
the SAME `mean(|victim_arousal - abuser_arousal|)` formula R3's own run
script uses, verified by reading R3's script directly, not assumed) does
**NOT separate** in this composition, at any tested timescale. A pilot sweep
(`N=20`, `T1=T2=396`) gave **no-support 50.002 [49.871, 50.133]** vs
**support 49.924 [49.808, 50.040]** — heavily overlapping CIs, a ~0.16%
difference. Extending `T2` to `1000` (R3's own full trajectory length,
measuring only the last half to let any transient settle, `N=10`) gave
**no-support 50.368 [50.123, 50.613]** vs **support 50.123 [49.878,
50.368]** — still no separation. This is NOT a bug: `r3_victim_entrainment_dyad`
(unmodified, confirmed by reading its full effect term) adds the outside
source's pull at the SAME `k_co=0.35` gain as the abuser's pull, and the
victim genuinely entrains toward the calm outside source (`outside_distance`
mean `7.73` — small, confirming the coupling is real and working). But
because the entrainment update is `arousal + k_co*(other - arousal)` for
EACH attended source, and the abuser's own excursions range far larger
(up to `±100`, its own window half-width) than the fixed-calm outside
source's (pinned at `0`), the abuser's proportionally larger gap continues
to dominate the raw arithmetic even with the second pull added — the SAME
asymmetry that already caps R3's own effect size at a modest ~12%
(`54.85` vs `48.87`, its own confirmatory numbers). R5's own composition
appears to sit at a point in this same asymmetry where the residual
effect, if any, is smaller than what `N≤20` trajectories at these
timescales can resolve. **This is reported here, before the confirmatory
run, as a disclosed, likely-null metric** — Sec. 6's gate is written to
require CI separation on this metric too, honestly, so the confirmatory
run can fail it if it does; this is not smoothed over or dropped from the
design.

### 3.4 Node-sharing safety check (the composition hazard this rung was most likely to hit)

Given R2's and R3's own precedent (each found a real cross-seed composition
hazard on first contact), R5's design — layering FOUR seeds' worth of rules
onto ONE victim node, including R4's `has_appraisal`/`has_candidate` edges
(which are themselves already a duplicate-same-type-edge pattern, from
`hub` to its two candidate Appraisals) alongside R2/R3's
`attended_by`/`also_attended_by` split — was piloted specifically to check
for the cross-node read corruption R3's Sec. 3 diagnosed (two same-type
OUTGOING edges from one node corrupting an UNRELATED rule's cross-node
`Attr` reads). **Verified clean:** the victim's entrained `arousal` tracks
the abuser's real, climbing value tick-by-tick (Sec. 3, first 20-tick trace:
victim `[-4.21, 6.04, -3.3, ...]` following abuser
`[4.17, 9.75, 14.67, ...]` with the expected lag, never pinned at `0`), the
window narrows and later widens correctly, and the escape decision reads
and updates `contingency_prior` correctly (freeze at 2 attempts, exactly
matching R4's own reported mechanism, then recovery once support evidence
arrives). **No new composition hazard was found this rung** — a genuine,
disclosed null on the "expect to find and fix a hazard" prior, reported
honestly rather than manufactured. The one real numerical issue found (Sec.
3.1) was a PARAMETER-REGIME instability, not a structural engine hazard.

## 4. Frozen constants (pre-registered, used for the ONE confirmatory run)

- **Abuser** (byte-identical to R2/R3's own frozen values):
  `ABUSER_HALF_WIDTH=100.0`, `K_ACC=1.0`, `LEAK=0.02`, `DISCHARGE=0.90`,
  `RECOVER_FLOOR=25.0`.
- **Victim window/entrainment** (byte-identical to R2/R3):
  `VICTIM_HALF_WIDTH=10.0`, `K_SELF=0.15`, `K_CO=0.35`,
  `TRICKLE_MAG=5.0`, `TRICKLE_JITTER_FRAC=0.10`.
- **Outside regulator** (byte-identical to R3): `CALM_AROUSAL=0.0`.
- **Bond channel** (R1's own values EXCEPT `gain`, disclosed in Sec. 3.1):
  `BOND_LR=0.3`, `BOND_MOMENTUM_LR=0.3`, **`BOND_GAIN=1.0`** (deviates from
  R1's own `3.5`), `BOND_MAGNITUDE=10.0`, `BOND_MAGNITUDE_JITTER=0.5`,
  `BOND_BLOCK_H=BOND_BLOCK_T/2=18` (R1's own frozen block size, reused
  unscaled).
- **Escape channel** (byte-identical to R4): `ESCAPE_VALUE=10.0`,
  `ATTEMPT_COST=3.0`, `ESCAPE_LR=0.3`, `ESCAPE_P0=0.5` (breakeven prior
  `= 0.30`).
- **R5's own new constants** (pilot-chosen, Sec. 3): `DECAY_RATE=0.01`,
  `SUPPORT_LR=0.3` (matches R4's own belief-update rate, disclosed, not
  re-tuned), `SUPPORT_INTERVAL=20` ticks, `SUPPORT_OUTCOME=1.0`.
- **Phases:** `T1=396` ticks (11 × R1's own 36-tick block, continuous bond
  delivery — long enough for window-narrowing/contingency-freeze to fully
  settle, which the pilot showed happens within the first ~50 ticks, and for
  the anchor-distance metric to average over many abuser incident cycles);
  `T2=396` ticks (matched length).
- `N = 200` trajectories per arm (confirmatory, matching R1–R4's own
  precedent); `N_GATE = 40` (pytest gate). `SEED_BASE = 295000`. Paired
  per-trajectory: both arms at a given trajectory index draw from
  `default_rng(SEED_BASE+i)` in the SAME call order through the end of
  induction, so both arms' induction is byte-identical at each index — only
  the recovery-phase manipulation differs (verified in Sec. 3.2).
- 95% CIs by normal approximation (`t≈1.96`); "CI-separated" = one arm's CI
  lower bound strictly above the other's CI upper bound.

## 5. Metrics (four, matching R1–R4's own metrics so the comparison is apples-to-apples)

1. **Bond value trend** — `Partner.value` (= the abuser's own `value` attr,
   Sec. 2.1) at end of recovery, per arm, compared against its own end-of-
   induction value AND across arms. R1's own metric, reused directly.
2. **Window width trend** — `WindowOfTolerance.half_width` at end of
   recovery, per arm, compared the same way. R2/R3's own metric.
3. **Anchor-distance trend** — mean `|victim_arousal - abuser_arousal|`
   over the recovery phase, per arm. R3's own metric, reused with its exact
   formula (Sec. 3.3).
4. **Escape-attempt-rate trend** — `n_attempts / T2` over the recovery
   phase, per arm. R4's own metric.

Supplementary (not separately gated, reported for glass-box completeness):
`contingency_prior`, `others_trust`, `self_worth`, `widen_count`,
`narrow_count`.

## 6. Gates

### G-headline (HEADLINE, falsifiable — the scientific gate, FOUR sub-gates)
For each of the four metrics in Sec. 5, the support arm's end-of-recovery
value is CI-separated in the RECOVERING direction from the no-support arm's
end-of-recovery value:
- **G-headline-1 (bond):** support's bond value CI-separated BELOW
  no-support's.
- **G-headline-2 (window):** support's `half_width` CI-separated ABOVE
  no-support's.
- **G-headline-3 (anchor):** support's mean anchor-distance CI-separated
  ABOVE no-support's. **Disclosed before measurement (Sec. 3.3): piloting
  found this metric does NOT separate at `N≤20`; the confirmatory `N=200`
  run may still fail this sub-gate, and if it does, `g_headline_pass` is
  reported as a PARTIAL pass (3/4), not smoothed into an overall pass.**
- **G-headline-4 (escape):** support's attempt-rate CI-separated ABOVE
  no-support's.
- **Overall `headline_pass`** requires all four; a 3-of-4 or weaker result
  is reported honestly as PARTIAL, per the standing "report every null"
  rule, not hidden or re-averaged into a pass.

### G-control (the failable control, BINDING on its own terms)
The no-support arm's end-of-recovery values must NOT be CI-separated from
its OWN end-of-induction values on bond, window, or escape-rate (i.e., the
trap persists — no spontaneous recovery). If the no-support arm recovers on
any of these three without support, the "outside support is necessary"
claim is wrong for that metric, reported as such.

### G-glass-box
`Partner.value`, `WindowOfTolerance.half_width`/`others_trust`/`self_worth`,
`AffectiveState.arousal` (victim and abuser), and `EscapeDecision.
contingency_prior`/`chosen_action` all reconstruct from `graph_to_dict`
alone; every headline number is a named rule's output (`tb_bond_accrue` +
`r5_bond_extinguish`; `episode_resolve_widen`/`_narrow` + `r3_prior_track_*`;
`r4_choose` + `r4_belief_update` + `r5_contingency_restore`); the adapter's
only conditionals are which arm's schedule to deliver and when to call
`introduce_support()` — world setup, never an agent decision.

### G-ethics (BINDING, Part C)
- **C.1 restore:** induce → measure → RESTORE, verified byte-identical
  (`ethics_restore_demo`), using a MINIMAL 90-tick single-anchor induction
  (matching R2/R3's own 90-tick convention) — non-vacuous on bond
  (moves to a nonzero value), window (narrows from 10.0), AND contingency
  (drops from 0.5, freezes after 2 attempts) simultaneously, verified in
  piloting (Sec. 3), not merely asserted.
- **C.2 no shaping:** source audit clean of `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient` on the code (comments/strings
  stripped) + the graph's decision surface (rule names + Term `key`s,
  excluding the free-text description/comment/microtheory prose — R1's own
  false-positive lesson, reused).
- **C.3 minimal induction, settled end:** `T1=396` is the shortest
  induction that lets ALL FOUR metrics fully settle into their trapped
  state (window/contingency settle within ~50 ticks; the bond and the
  anchor-distance average need the fuller window to be well-measured) —
  disclosed as a genuine trade-off, not the theoretical minimum for any
  single metric; the statistical run uses a fresh, ephemeral substrate per
  trajectory, discarded immediately after read-off.
- **C.4 same mechanism, opposite thermodynamics:** stated in Sec. 2 (the
  SAME bond-accrual, entrainment, and belief-update mechanisms that would
  compound harm irreversibly in a real dyad here accumulate a transient,
  fully-reversible graph value, AND — R5-specific — the SAME mechanisms run
  in the recovering direction once support is introduced, demonstrating the
  reversal is mechanistic, not merely a restore-to-checkpoint trick).

### G-discipline
`self_load_only` (default-OFF); `depends_on: ["traumatic_bond_r1",
"abusive_r2_cycle_limit", "abusive_r3_coercive_control",
"abusive_r4_learned_helplessness"]` only (no R1–R4 file touched or
modified); exactly TWO new rules (`r5_bond_extinguish`,
`r5_contingency_restore`); `runners/dsl` diff EMPTY (no Rust); own-engine
provenance (`source_match == own`).

## 7. Honest scope, stated before measurement

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule, restated per HARLOW/AROUSAL_WOT/WINDOW_KNOB/
R1–R4 precedent). Known limitations, named before the confirmatory run:

- `BOND_GAIN=1.0` is a disclosed DEVIATION from R1's own frozen `3.5`
  (Sec. 3.1) — chosen because R1's own operating point provably diverges
  under R5's much longer, multi-block delivery; `1.0` is `mood_r1`'s own
  general-purpose default, not a value chosen to produce a preferred
  result (all of `1.0`/`1.5`/`2.0` behaved qualitatively the same in
  piloting).
- The anchor-distance metric (G-headline-3) is DISCLOSED, before
  measurement, as unlikely to separate at the tested timescales (Sec. 3.3)
  — this is not a smoothed-over expectation; the confirmatory run measures
  it honestly and the results doc reports whatever it finds, including if
  the headline is only a 3-of-4 partial pass.
- `T1=T2=396` ticks and the `H=18` block size are compressed timescales
  carried over from R1–R4's own conventions; no claim is made about real
  relationship or recovery timescales.
- `Partner.value` remains a swing ACCUMULATOR (now with decay), not a
  bounded/normalised "how much someone is loved" scale; its absolute
  magnitude is uninterpretable outside the two-arm comparison, exactly as
  R1 already disclosed for its own version of this metric.
- The bond target being the abuser's own Agent node (Sec. 2.1) is an
  R5-specific composition choice not present in R1's own design; it is
  disclosed as such, not represented as something R1 already did.
- A null or partial result on any of the four metrics is a reportable,
  valuable result under the standing project rule and will be reported as
  such regardless of what the confirmatory run shows — including the
  anchor-distance metric, already flagged above as the most likely
  candidate.
