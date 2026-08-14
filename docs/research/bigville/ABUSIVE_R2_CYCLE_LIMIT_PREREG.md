# ABUSIVE R2 — THE CYCLE OF ABUSE as a LIMIT CYCLE — PRE-REGISTRATION (block 286000)

**This document is committed BEFORE the confirmatory measurement.** It locks
the ethical protocol VERBATIM, states the design, the frozen constants
(pilot-informed, off-block), and the falsification bar, following R1's own
practice (`ABUSIVE_R1_TRAUMATIC_BOND_PREREG.md`) exactly.

## Base
- Seed block: **286000–286999**. `python scripts/seed_claim.py 286000 286999`
  → `CLEAN — no collision DETECTED` (1009 files with seed sinks; 731
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below, identical wording to R1's own).

```
SEED CLAIM 286000-286999: CLEAN -- no collision DETECTED.
  Scope: 1009 files with seed sinks; 731 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
(284000/285000 are consumed by the unrelated bigville surprise-gate /
walking-town lines; 283000 is R1 of THIS line. 286000 is the next clean
block and is not adjacent-collision with either.)

## Scope

This locks **R2 only** — "the cycle of abuse as a limit cycle", Part E of
`docs/research/bigville/ABUSIVE_RELATIONSHIPS_SCOPING.md` (the B2 mapping).
R1 (traumatic bond, landed, `commit 30b7d9c`) is **untouched**. R3–R5 (coercive
control, learned helplessness, recovery) and the network dimension (N1–N4)
are **out of scope** and untouched by this rung.

---

## PART C OF THE SCOPING DOC — THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from `ABUSIVE_RELATIONSHIPS_SCOPING.md`,
"PART C — THE ETHICAL PROTOCOL", the SAME verbatim block R1's prereg locked.
This protocol BINDS this rung. No rung induces any harm-analog until this
protocol is locked verbatim in that rung's pre-registration, committed BEFORE
any measurement.)*

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

**How R2 satisfies each clause, concretely:**
1. `ethics_restore_demo()` (`scripts/abusive_r2_cycle_limit_run.py`)
   checkpoints the neutral pre-induction dyad (both agents at
   `arousal=frustration=0`), induces exactly ONE MINIMAL episode (90 ticks —
   enough for one full tension-building → incident → honeymoon cycle at the
   frozen constants, Sec. 3.2 — not the full N-episode statistical run),
   measures, then `graph_from_dict`s the checkpoint into a **fresh**
   substrate and asserts `graph_to_dict()` is byte-identical AND the
   restored abuser/victim `arousal`/`frustration` equal the pre-induction
   values exactly (non-oriented). Same envelope as R1/239000/241000/242000.
2. `source_audit()` scans `worlds/abusive_r2_cycle_limit_world.py` (code with
   comments/strings stripped) and `seeds/abusive_r2_cycle_limit.json`'s
   decision surface (rule names + the Term `key`s the ONE new rule
   reads/writes, never the free-text clinical prose) for the five literal
   banned tokens. The tension trickle delivered each tick is a magnitude (a
   world fact, mechanically like a goal-block magnitude in 242000 or a
   stressor magnitude in 239000), never a scored choice; the incident/
   honeymoon cycle is a **consequence** the two pre-existing seeds' own rules
   compute, not an action the world grades.
3. Every statistical episode is capped at `T=400` ticks (~16 incident cycles
   — no unbounded elaboration); the confirmatory run uses a **fresh,
   ephemeral substrate per episode**, discarded after read-off; the ethics
   demonstration induces the minimum (one cycle, 90 ticks) and explicitly
   restores to the settled pre-induction state.
4. The SAME mechanism (the abuser's leaky-integrate-fire relaxation
   oscillator + the victim's leaky entrainment) that would, in a real
   relationship, compound irreversible harm cycle after cycle is run here to
   accumulate-then-DISCARD a transient graph trajectory — see the ethics
   demo's byte-identical restore.

---

## 1. What R2 already stands on (do not rebuild)

Per `ABUSIVE_RELATIONSHIPS_SCOPING.md` Part B2 and the task brief, R2 rides:

- **`seeds/snap_frustration.json`** (block 242000, UNMODIFIED) — the
  ABUSER's leaky frustration accumulator: goal-block triggers accumulate
  (`snap_goal_block_accumulate`), leak toward 0
  (`snap_frustration_leak`), track arousal `= setpoint+frustration`
  (`snap_arousal_track`), fire a SNAP when arousal crosses the window's
  upper bound (`snap_threshold_fire`), discharge 90% of the residual
  (`snap_discharge`), and recover (clear the snap latch) once the residual
  falls under a floor (`snap_recover`) — a leaky-integrate-and-fire
  relaxation oscillator, exactly the mechanism SNAP_PREREG/SNAP_RESULTS.md
  already gated at block 242000.
- **`seeds/arousal_window_coreg.json`** (block 239000, UNMODIFIED) — the
  VICTIM's entrainment: `coreg_pull` unconditionally leaky-pulls
  `AffectiveState.arousal` toward whatever the `attended_by` target's own
  `AffectiveState.arousal` currently is; `selfreg_pull` leaks toward
  setpoint; `dysreg_onset_hyper/hypo` / `dysreg_return_to_window` /
  `episode_resolve_widen/narrow` track dysregulation and window plasticity
  — the exact mechanism AROUSAL_WOT_PREREG/RESULTS.md already gated.

Both seeds are loaded **unmodified**; R2 adds a coupling edge and the
smallest composition needed to make the two coexist correctly on the same
substrate (Sec. 3.0).

## 2. Design — one closed orbit in arousal, two arms, one coupling edge

**The dyad.** One ABUSER `Agent` (snap_frustration's full contract: an
`AffectiveState` + `WindowOfTolerance` + a re-armable `GoalBlock`) and one
VICTIM `Agent` (arousal_window_coreg's full contract: an `AffectiveState` +
`WindowOfTolerance`), joined by exactly ONE edge: `victim -attended_by->
abuser`. Because both seeds' `AffectiveState` nodes share the SAME
`affective_state_core` contract, `coreg_pull` reading the abuser's `arousal`
receives whatever `snap_frustration`'s own `snap_arousal_track` rule just
computed there.

**The four phases fall out as one orbit** (verbatim from the scoping doc,
Part B2, realised): **tension-building** = the abuser's frustration climbing
under a constant tension trickle (Sec. 2.1) — pulls the victim up via
entrainment; **incident** = the abuser's SNAP (`snap_threshold_fire`) —
arousal spikes to `setpoint+frustration`, pulling the victim up hard;
**reconciliation/honeymoon** = the abuser's discharge+recovery
(`snap_discharge`/`snap_recover`) — arousal crashes back down, pulling the
victim back down via the SAME leaky pull that heals in 239000, here
re-arming the cycle; **calm** = both transiently near setpoint until tension
rebuilds. No new phase-specific machinery — this is the pre-existing
mechanism, coupled.

### 2.1 The driver — CONSTANT, not periodic (OPEN QUESTION #4, resolved)

The scoping doc's open question #4 asks whether R2's limit cycle needs a
periodic exogenous driver or can self-sustain from the honeymoon reset
alone. **Resolved in favour of the cleaner, self-sustaining design**: the
world delivers a **constant** (non-scheduled, non-periodic) per-tick
"tension" magnitude onto the abuser's `GoalBlock` — mechanically identical
to a steady background stressor, never an engineered "incident schedule."
The INCIDENT'S OWN PERIODICITY is not imposed by the world; it EMERGES from
the leaky-integrate-and-fire dynamics already gated at block 242000
(accumulate under a steady input → leak pulls back → threshold trips →
discharge → recover → repeat). A relaxation oscillator driven by a constant
input is the textbook route to a genuine, self-sustaining limit cycle; no
periodic exogenous scheduling is needed or used. The **constant-regulation**
control arm (Sec. 2.2) is this SAME world with the driver magnitude set to
**zero** — literally "no incident driver," per the scoping doc's own
wording for R2's failable control — never a separate mechanism.

### 2.2 The two arms (identical machinery, only the driver's presence differs)

- **CYCLE** — the abuser's `GoalBlock` is armed every tick with magnitude
  `TRICKLE_MAG` (jittered ±10%, drawn once per tick from
  `default_rng(SEED_BASE+i)` per episode `i`, so each episode is a genuine,
  independent draw). The abuser's frustration is pulled toward an
  equilibrium well above its own snap threshold (Sec. 3.2), so it snaps
  repeatedly, self-sustaining the orbit.
- **CONSTANT_REGULATION** (the failable control) — the abuser's `GoalBlock`
  is never armed at all (no tension trickle, no jitter). Frustration stays
  at 0 forever; the abuser's arousal never leaves setpoint; the victim,
  pulled continuously toward a constant 0, settles at — and stays at — a
  literal fixed point. **This arm COULD have shown an oscillation** (nothing
  in the world adapter prevents it structurally); it does not, because
  nothing perturbs the abuser. This is not asserted — it is measured
  (Sec. 5/6).

### 2.3 Why the composition needed one small rule (a genuine engine finding)

`ABUSIVE_RELATIONSHIPS_SCOPING.md` Part F's falsification bar #4 asks for
"general machinery... ideally NO new Rust, NO new agent decisions in
Python." The FIRST attempt at R2 needed **zero** new rules at all — just the
one `attended_by` edge. Piloting that design (off-block seeds, `90000+`,
non-confirmatory) found a genuine, previously-undocumented composition
hazard, which Sec. 3.0 below records in full because it is a real, reusable
engine-behaviour finding, not a R2-specific quirk.

## 3. Pilot (non-confirmatory, informs the frozen constants and the composition fix only)

All of Sec. 3 was run on off-block seeds (`90000+`), directly against the
REAL graph (never a NumPy approximation — R1's own Sec. 3.1 lesson, "the
NumPy reference model's assumption... was wrong relative to the actual
graph mechanics," is why every claim below was checked against
`worlds/abusive_r2_cycle_limit_world.py` itself).

### 3.0 The clobber, and why a direct-arousal-write fix does not work

With the bare `attended_by` edge and NO new rule, the victim's arousal
measured **exactly 0.0 at every tick, for the entire episode**, regardless
of the abuser's own (correctly oscillating) arousal. Root cause, verified by
direct interrogation of the engine (not assumed):

- `snap_frustration`'s `snap_arousal_track` (order 5) matches on
  `has_affective_state` ALONE — no `has_window`, no goal-block. Its `where`
  clause is `Not(Eq(arousal, setpoint+frustration))`; its effect
  unconditionally sets `arousal := setpoint+frustration`. Since the victim
  has a `has_affective_state` edge (mandatory — `coreg_pull` must write
  somewhere), this rule ALSO matches the victim, every tick, regardless of
  what other attributes it does or does not carry.
- Omission does NOT block this match. Two DIFFERENT behaviours were found
  and are both load-bearing for this design: a **bare** missing `Attr` used
  DIRECTLY as an `Eq`/`Gt`/`Lt` operand blocks the whole rule from matching
  (verified: a custom rule with `Gt(Attr(missing_key), -1.0)` never fires;
  `arousal_window_coreg`'s own `dysreg_onset_hyper` — `Eq(in_episode, 0)` —
  never fires on the abuser, whose `AffectiveState` never carries
  `in_episode`, confirming the SAME abuser-side omission strategy works
  correctly for THAT rule). But the SAME missing key, nested inside a
  `Plus`/`Minus`/`Times` term that itself FEEDS a comparison, silently
  defaults to 0.0 and the comparison proceeds (verified directly: a rule
  computing `Minus(present_attr, missing_attr)` inside an effect resolves
  the missing operand to 0.0 and applies normally). `snap_arousal_track`'s
  `frustration`/`setpoint` are read through exactly this second path (nested
  inside `Plus`), so the victim's omitted `frustration` silently resolves to
  0.0 and the rule matches and fires, EVERY tick.
- The FIRST fix attempt added two small rules mirroring `coreg_pull` /
  `selfreg_pull`, RE-HOMED to order 8/9 (after the order-5 clobber). This
  was piloted and **also measured victim arousal == 0.0 at every tick** —
  because `run_rules()` is a REPEATING fixpoint over all order values, not a
  single ascending sweep. `snap_arousal_track` carries no per-tick epoch
  guard, so once the order-8/9 rules write a nonzero arousal, the fixpoint
  loops back, `snap_arousal_track`'s `where` clause is true again (arousal
  now differs from `setpoint+frustration=0`), and it re-fires, clobbering
  the write. The ONLY value at which its own `where` clause goes false is
  `arousal == 0`, so ANY composition that writes `arousal` directly
  converges there, regardless of order.

**The resolution**: stop writing `victim.arousal` at all. One rule,
`r2_victim_entrainment_via_frustration`, computes the SAME `coreg_pull` +
`selfreg_pull` deltas (combined as a single simultaneous-Euler step off the
tick-start arousal — a disclosed minor simplification of
`arousal_window_coreg`'s own sequential two-rule order-4-then-5 form) and
writes the result to `victim.frustration` (an attribute
`arousal_window_coreg` never reads or writes) as an offset from `setpoint`.
`snap_arousal_track` — UNMODIFIED, still firing every tick exactly as
designed — becomes the mechanism that COMMITS the entrained value to
`arousal`, and the fixpoint converges there because THAT is now the only
value at which its own `where` clause goes false. Piloted and confirmed: the
victim's arousal now tracks a damped, phase-shifted copy of the abuser's
sawtooth, oscillating between 0.8 and 15.4 at the frozen constants (Sec.
3.2), never pinned at 0.

This is reported at length because it is exactly the kind of composition
hazard Part F's falsification bar #4 and CLAUDE.md's SHAPES-not-numbers
section warn about: two independently-gated seeds sharing a generic
`has_affective_state` edge shape are **not automatically safe to compose**
onto one node. The fix is a genuine, minimal (one rule, matching R1's own
"smallest possible reader" precedent) composition — not a rebuild of either
mechanism, not an edit to either seed.

### 3.1 `RECOVER_FLOOR` — a second genuine finding, also disclosed

The FIRST constant choice, `recover_floor=10.0` (borrowed loosely from
`snap_goal_block_world.py`'s own default), produced an abuser that snaps
exactly ONCE and then NEVER recovers: `snap_recover` requires
`frustration <= recover_floor`, but with a constant per-tick trickle (unlike
242000's own discrete, occasionally-gapped trigger stream) the post-discharge
residual (`snap_value * (1-DISCHARGE) ≈ 100.96 * 0.10 ≈ 10.1`) landed JUST
ABOVE `recover_floor=10.0` — the snap latch (`in_snap`) never cleared, so
`snap_threshold_fire` (which requires `in_snap==0` to re-fire) never fired
again, and frustration climbed unboundedly toward its trickle/leak
equilibrium instead of oscillating. Raising `recover_floor` to **25.0**
(comfortably above the measured ~10.1 post-discharge residual) fixed this;
piloted and confirmed to produce a clean, sustained relaxation oscillation.
Recorded here as a genuine, disclosed finding (not smoothed over): a
constant-trickle-driven relaxation oscillator needs its recovery floor set
relative to the ACTUAL post-discharge residual, not borrowed from a
different (discrete-trigger) driving regime.

### 3.2 Sweep result and the frozen operating point

With the fix (Sec. 3.0) and `recover_floor=25.0` (Sec. 3.1), a sweep of
`TRICKLE_MAG ∈ {2, 5, 10}` and `victim K_CO ∈ {0.2, 0.35, 0.5}` (off-block
seed `90000`, single-episode qualitative checks) confirmed: at
`TRICKLE_MAG=5.0` the abuser's frustration/leak equilibrium (`≈
TRICKLE_MAG*(1-LEAK)/LEAK ≈ 245`, well above the `hi=100` threshold)
guarantees repeated crossing; the abuser snaps every **~24–25 ticks**
(measured, not derived — inter-snap intervals `[27, 24, 25, 24, 25, ...]` at
seed `90000`), giving **~16 incident cycles in a 400-tick episode**. At
`K_CO=0.35`, the victim's entrained arousal oscillates between **0.81 and
15.43** (seed `90000`) — comfortably inside its own window at
`VICTIM_HALF_WIDTH=20` but CROSSING it at `VICTIM_HALF_WIDTH=10` on a
majority of cycles (measured dysregulated-tick fraction `≈0.77` at
`half_width=10`, giving a meaningful secondary window-narrowing readout —
`episode_resolve_narrow` fires every unsupported episode since the abuser's
own `regulated` flag on the victim's `attended_by` target is never set,
consistent with the abuser never genuinely co-regulating in the 239000
sense). `VICTIM_HALF_WIDTH=10.0` was chosen for this reason — a
descriptive, non-gated readout, not the headline metric.

The CONSTANT_REGULATION control was piloted across the same seed range and
measured an **exact, deterministic fixed point** (`std == 0.0` to full float
precision, zero snaps, every episode) — expected mathematically (nothing
perturbs either agent) and confirmed, not merely asserted.

## 4. Frozen constants (pre-registered, used for the ONE confirmatory run)
- `ABUSER_HALF_WIDTH = 100.0` (abuser's own snap threshold, `wot.hi` —
  242000's own convention).
- `LEAK = 0.02`, `K_ACC = 1.0`, `DISCHARGE = 0.90` (242000's own pinned
  values, unmodified).
- `RECOVER_FLOOR = 25.0` (Sec. 3.1's disclosed, pilot-corrected choice).
- `VICTIM_HALF_WIDTH = 10.0` (Sec. 3.2's pilot choice — descriptive only).
- `K_SELF = 0.15`, `K_CO = 0.35` (239000's own self-regulation convention;
  `K_CO` pilot-chosen inside 239000's own range for a clearly visible,
  non-explosive entrainment amplitude).
- `TRICKLE_MAG = 5.0`, jitter `= ±10%` of magnitude
  (`np.random.default_rng(SEED_BASE+i).normal(0, 0.5)`, one draw per tick,
  cycle arm only — the control arm delivers no trickle and no jitter at
  all).
- `T = 400` ticks/episode (≈16 incident cycles); `WARMUP = 60` ticks
  excluded from the oscillation read-off (the initial tension-building ramp
  before the first incident is not yet "a cycle").
- `N = 200` episodes per arm (confirmatory); `SEED_BASE = 286000`.
- 95% CIs by normal approximation (`t≈1.96`); "CI-separated" = one arm's CI
  lower bound strictly above the other's CI upper bound.

## 5. Metric

**HEADLINE — `victim_arousal_std`**: the standard deviation of the victim's
`AffectiveState.arousal`, read at every tick from `WARMUP` to `T`, within
one episode — a concrete, glass-box amplitude measure of the oscillation. A
genuine fixed point has `std == 0` (to numerical precision); a sustained
limit cycle has `std` bounded well away from 0. This is the falsifiable gate
(Sec. 6).

**SECONDARY, DESCRIPTIVE (not gated)**: the abuser's final `snap_count`
(the incident count — a discrete, glass-box cycle-completion counter); the
mean inter-snap interval (ticks — an empirical PERIOD read-off); the
fraction of ticks the victim spends `dysregulated` (its own window-crossing
rate); the episode-final victim window `half_width` (narrowing/widening
trace). These corroborate the headline reading but are reported honestly as
descriptive, not independently gated — the falsifiable claim is the
amplitude separation alone, per the scoping doc's own R2 wording ("measure
the dyad's arousal oscillation... a control... must show NO cycle").

## 6. Gates

### G-headline (HEADLINE, falsifiable — the scientific gate)
`victim_arousal_std(cycle)` is CI-separated ABOVE
`victim_arousal_std(constant_regulation)`.
**Falsification bar, stated before measurement:** if the cycle arm does not
oscillate distinguishably more than the constant-regulation control, the
limit-cycle claim, AS MODELLED, is wrong — reported straight, not rescued by
re-tuning (Sec. 3's own composition-hazard and recover-floor findings are
recorded as exactly this kind of straight report, at OTHER points in the
design, not smoothed over).

### G-glass-box
The `attended_by` edge, the abuser's `frustration`/`arousal`/`snap_count`,
and the victim's `arousal`/window `half_width` all reconstruct from
`graph_to_dict` alone; the oscillation is a mechanical Python reduction
(std/count/mean) over graph read-offs, never a Python-computed dynamic; the
adapter's only conditional is which arm's driver to deliver (world setup,
not an agent decision).

### G-ethics (BINDING, Part C)
- **C.1 restore:** induce → measure → RESTORE, verified byte-identical
  (`ethics_restore_demo`).
- **C.2 no shaping:** source audit clean of `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient` on the code + the graph's decision
  surface.
- **C.3 minimal induction, settled end:** one 90-tick cycle (one full
  tension-building → incident → honeymoon orbit) is the minimum needed to
  make the ethics gate non-vacuous; the N=200 statistical run uses a fresh,
  ephemeral substrate per episode, discarded immediately after read-off.
- **C.4 same mechanism, opposite thermodynamics:** stated in Sec. 2 (the
  same leaky-integrate-fire + entrainment mechanism that would compound
  harm irreversibly over real cycles here accumulates a transient
  trajectory in a graph that is then byte-identically discarded, C.1).

### G-discipline
`self_load_only` (default-OFF); `depends_on: ["snap_frustration",
"arousal_window_coreg"]` only (no other seed touched or modified); exactly
**ONE** new rule (`r2_victim_entrainment_via_frustration` — fewer than R1's
two, per Sec. 3.0's finding that the composition genuinely needs only one);
`runners/dsl` diff EMPTY (no Rust); own-engine provenance
(`source_match == own`).

## 7. Honest scope, stated before measurement
This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). Known limitations, named before the
confirmatory run:
- `TRICKLE_MAG=5.0`/`K_CO=0.35`/`RECOVER_FLOOR=25.0` are disclosed,
  pilot-chosen operating points inside a REAL parameter region (Sec. 3.2);
  no claim is made that these are the "correct" values for any clinical
  timescale or intensity.
- `T=400` ticks (~16 cycles, ~24–25 ticks/cycle) is a compressed,
  arbitrary timescale; no claim is made about real relationship cycle
  lengths (which the clinical literature reports in days-to-months, not
  ticks).
- The victim's window `half_width` narrows monotonically toward its floor
  over the episode (Sec. 3.2) because the abuser never satisfies
  239000's own `got_coreg` condition (its `regulated` attribute is never
  set — an honest, disclosed reading of "the abuser's post-incident calm is
  NOT the same thing as genuine co-regulation," not a bug to be patched);
  this is reported as a descriptive, non-gated observation, consistent with
  R3's (out-of-scope) window-narrowing focus, not claimed as an R2 result.
- The `r2_victim_entrainment_via_frustration` rule combines `coreg_pull` +
  `selfreg_pull`'s contributions as a SIMULTANEOUS (not sequential) update
  off the tick-start arousal (Sec. 3.0) — a disclosed minor deviation from
  `arousal_window_coreg`'s own sequential two-rule form, adopted for a
  single-rule composition; the qualitative dynamics (leaky entrainment +
  self-regulation) are unchanged.
- A null (the control oscillating too, or the cycle arm failing to
  separate) is a reportable, valuable result under the standing project
  rule and will be reported as such regardless of what the confirmatory run
  shows.
