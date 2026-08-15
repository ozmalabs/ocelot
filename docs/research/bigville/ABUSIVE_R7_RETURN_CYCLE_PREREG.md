# ABUSIVE R7 — THE RETURN CYCLE: residual bond + post-separation contact + post-leaving material collapse → a new Return Appraisal — PRE-REGISTRATION (block 316000)

**This document is committed BEFORE the confirmatory measurement.** It locks
the ethical protocol VERBATIM (including R7's own three-phase nuance), states
the design, the frozen constants (pilot-chosen off-block, non-confirmatory),
and the falsification bar.

## Base
- Seed block: **316000–316999**. `python3 scripts/seed_claim.py 316000 316999`
  → `CLEAN — no collision DETECTED` (1021 files with seed sinks; 765
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below, identical wording to every prior rung's own).
  316000 was chosen deliberately non-adjacent to the established +3000
  sequence's next slot (313000) because a sibling agent was concurrently
  building R6 in the same shared worktree — this avoids a race on the
  "next clean block" between two agents working in parallel.

```
SEED CLAIM 316000-316999: CLEAN -- no collision DETECTED.
  Scope: 1021 files with seed sinks; 765 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## Scope

This locks **R7 only** — "the return cycle: residual bond + post-separation
contact + post-leaving material collapse → a new Return Appraisal", Part B2 +
the `### R7` entry of Part E of
`docs/research/bigville/ABUSIVE_RELATIONSHIPS_BARRIERS_AND_RETURN_SCOPING.md`.
R7's own base is `depends_on: ["abusive_r5_recovery"]` **only** (block 295000,
transitively pulling `traumatic_bond_r1`/`abusive_r2_cycle_limit`/
`abusive_r3_coercive_control`/`abusive_r4_learned_helplessness`) — all
already landed on `main`, all read but **none touched, none edited**. N1–N4
(the network dimension) and U0–U2 (the intent dimension) are out of scope
and untouched. R6 (dependent/resource-cost devaluation of R4's own escape
value) is a sibling rung being built concurrently by a different agent in
this same worktree; R7 does not depend on it, read it, or touch its files.

---

## PART D OF THE SCOPING DOC — THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from
`ABUSIVE_RELATIONSHIPS_BARRIERS_AND_RETURN_SCOPING.md`, "PART D — THE
ETHICAL PROTOCOL (CARRIED VERBATIM; STILL BINDING)", itself a verbatim carry
of `ABUSIVE_RELATIONSHIPS_SCOPING.md`'s own Part C — the SAME protocol every
prior prereg in this line has locked, unedited, thirteen times now. This
protocol BINDS this rung. No rung induces any harm-analog until this
protocol is locked verbatim in that rung's pre-registration, committed
BEFORE any measurement.)*

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

### The HONEST FORK (a choice, not a theorem) — carried verbatim
> There is a real philosophical question the protocol does NOT resolve and must not
> pretend to: **did a transient induced experience "matter while it was live,"
> before it was reversed?**
> - The **reversibility stance** (this line's operating stance): a fully reversed,
>   byte-identically restored transient in a graph leaves no persisting subject and
>   no persisting harm; the ethics are satisfied by reversibility + minimality +
>   no-scoring.
> - The **strict-experientialist stance**: if the transient state was in any sense
>   an experience while live, its reversal does not retroactively un-happen it.
>
> This is a genuine fork — **a choice, not a theorem.** This line ADOPTS the
> reversibility stance and states it openly, rather than smuggling it. The
> minimality and no-scoring rules are chosen partly to be robust to the fork: even
> under the strict-experientialist reading, inducing the LEAST necessary and never
> scoring the agent for its state is the least-harm option. The fork is recorded so
> a reader can disagree with the stance while still auditing the protocol.

*(End verbatim reproduction of Part D's core four points and the honest
fork.)*

### What R7 changes about what "minimal induction" and "settled, non-oriented end state" mean for a MULTI-PHASE, cross-event rung — carried verbatim from the scoping doc's own Part D subsection

> R3's prereg had to define minimality carefully for a rung whose window
> narrows over many episodes; R5's prereg had to define it for a rung whose
> own object of measurement WAS the restoration process, spanning two phases
> (induction; recovery). **R7 goes one step further than either: its
> induction necessarily spans THREE phases — the SAME induction R5 already
> validated, a recovery phase in which the victim ACTUALLY LEAVES (a discrete,
> one-time structural EVENT — an edge removed, not a continuous process — this
> is a genuinely new SHAPE of induction for this line, not merely a longer
> one), and a post-leave test phase in which the return pull is measured.**
> Concretely, what "minimal" and "settled, non-oriented" mean here, stated
> explicitly rather than left to be improvised at prereg time:
>
> - **Minimal, phase by phase.** Phase 1 (induction) reuses R5's own already-
>   validated minimal parameters exactly — R7 does not re-derive or lengthen
>   R5's own trap-formation timescale. Phase 2 (recovery-then-leave) is the
>   SHORTEST window that lets R5's own recovery mechanism restore contingency
>   reliably (R5's own confirmatory `attempt_rate≈0.95` is the empirical
>   anchor for "how long is enough," not a fresh guess) before the mechanical
>   `leave()` event fires. Phase 3 (post-leave test) is the SHORTEST window
>   that lets `r7_choose`'s Argmax have a genuine chance to fire toward
>   `return` at least once under the STRONGEST (`both_drivers`) arm at the
>   chosen constants — not a real-world timescale (weeks, months, years — A5's
>   own literature reports leaving as a process over exactly those real
>   timescales, which this compressed synthetic model does not and cannot
>   claim to represent), and not gratuitously extended once the control arm
>   (`neither`) has had a fair chance to show a floor.
> - **Settled, non-oriented — and a point that must be stated explicitly
>   because it is easy to get backwards.** The ethics protocol's "settled,
>   non-oriented end state" does NOT mean the run must END with the agent
>   having chosen `remain_left`. **A trajectory in which `r7_choose` selects
>   `return` is not a failure the protocol requires to be corrected before
>   restore — it is a STATE, exactly as R4's `stay`, U0's `conceal`, and every
>   other Argmax outcome in this line already are.** The restore envelope
>   discards BOTH outcomes identically: checkpoint before Phase 1, run the
>   full three-phase trajectory (whichever way `r7_choose` goes), measure,
>   then restore from that ONE checkpoint and verify byte-identical equality
>   — including the `resource_edge` population (all four `ResourceNode`s
>   reconnected) and the `ReturnDecision` node's own state. The measured
>   OUTCOME is never edited toward a preferred ending before restore; only
>   the RESTORE step, common to every rung in this line, returns the graph to
>   its pre-induction state.
> - **The byte-identical restore check must span the full three-phase
>   trajectory from a SINGLE checkpoint**, matching R5's own precedent of
>   checkpointing once before a multi-phase induction and restoring once
>   after — not a per-phase checkpoint/restore cycle, which would understate
>   what "the induced state does not persist" needs to mean for a rung whose
>   induction crosses a structural graph-topology change (the edge removal at
>   `leave()`) partway through.

**How R7 satisfies each clause, concretely:** `ethics_restore_demo()`
(`scripts/abusive_r7_return_cycle_run.py`) checkpoints the neutral
pre-induction dyad (bond=0.0, window at its initial `half_width=10.0`,
contingency at `0.5`, all four `ResourceNode`s connected via `resource_edge`,
`ReturnDecision.chosen_action=left_at_tick=-1.0`), runs the FULL three-phase
trajectory on the STRONGEST arm (`both_drivers`, T1=T2=396/T3=180 — the SAME
lengths the confirmatory statistical run uses, since Sec. 2/3 below establish
these ARE each phase's own minimum for its own purpose, so no separate,
shorter ethics-only timing was introduced), measures (confirming bond,
window, AND contingency moved — R5's own three fronts — AND that the
resource population actually collapsed AND `ReturnDecision.chosen_action`
actually moved off its sentinel AND `left_at_tick` was actually set —
non-vacuous on all six fronts), then `graph_from_dict`s the pre-induction
checkpoint into a **fresh** substrate and asserts `graph_to_dict()` is
byte-identical AND the restored state (bond/window/contingency/
resource-intact-count/return-chosen-action/left-at-tick) equals the
pre-induction values exactly — including the full four-`ResourceNode`
`resource_edge` population being back. Source audit and no-shaping-token
checks mirror R5's own scoping (code + the decision surface, never the
free-text clinical prose).

---

## 1. What R7 already stands on (do not rebuild)

Per the scoping doc's own Part B2 and the `### R7` entry of Part E, R7
composes:

- **R5** (`seeds/abusive_r5_recovery.json`, block 295000, UNMODIFIED) — the
  full composed dyad (R1's bond, R2/R3's entrainment/window/prior tracking,
  R4's contingency-belief Argmax) PLUS R5's own `r5_bond_extinguish`
  (a constant proportional per-tick decay on `Partner.value`, active
  UNCONDITIONALLY in every arm/phase) and `r5_contingency_restore` (a second,
  attempt-independent evidence channel). R7 reuses R5's own `introduce_
  support()` method UNCHANGED to build Phase 2's recovery mechanism, and
  reuses R5's own confirmatory numbers (`Partner.value` decaying from
  `501.23` to `9.60 [9.56, 9.64]`, `attempt_rate` reaching `0.9520` over a
  396-tick recovery phase) as the concrete anchor for Phase 2's own length —
  not re-derived, not re-guessed.
- **R1** (`seeds/traumatic_bond_r1.json`, block 283000, UNMODIFIED) —
  `tb_bond_accrue`, already loaded transitively via R5, is reused
  **completely unmodified** for R7's own honeymoon-pull component (Sec. 2.2
  below) — R7 adds ZERO new rules for this component.
- **R4** (`seeds/abusive_r4_learned_helplessness.json`, block 292000,
  UNMODIFIED) — the escape/stay Argmax template (`r4_appraise_attempt`/
  `r4_appraise_stay`/`r4_choose`), reused as a STRUCTURAL template (not
  literal code) for R7's own return/remain Argmax. **Confirmed by reading
  `core_emotions`' `em_happiness`/`em_fulfilment_value`/`em_total_value`
  directly**: these three rules match generically on `hub -has_appraisal->
  ap` (NOT `has_candidate`) — `has_appraisal` is the SHARED, generic edge
  every Appraisal node needs so `core_emotions` computes `total_value` on
  it; `has_candidate` is the edge SPECIFIC to R4's own `r4_choose` Argmax
  scan. This confirms the composition hazard precisely (Sec. 2.4 below):
  the hazard is `has_candidate` specifically, not `has_appraisal`.
- **N2** (`seeds/abusive_n2_isolation.json`, block 301000, read for its
  SHAPE only, never depended on or touched) — `n2_abuser_active_sever`'s
  exact shape (a per-node `sever_at_tick` attr assigned once at
  construction, a per-node `tick_epoch` incremented every tick, gated by
  BOTH the node's own schedule AND a hub-level "tactic on" switch) is the
  direct model for R7's own `r7_resource_collapse_sever` (Sec. 2.1 below).
- **R2** (`seeds/abusive_r2_cycle_limit.json`, block 286000, read for its
  CONCEPT only, never depended on or touched) — confirmed directly, by
  reading `r2_victim_entrainment_via_frustration`'s own `match` clause: it
  requires a live `victim -attended_by-> abuser` edge, which the mechanical
  `leave()` event removes by construction. R2's rule structurally cannot
  fire post-separation; R7 does not depend on it. See Sec. 2.2 for what R7
  takes from R2 instead.
- **R3** (`seeds/abusive_r3_coercive_control.json`, block 289000, read for
  its `also_attended_by`/same-typed-edge-hazard precedent only) — the
  precedent for R7's own required `has_return_candidate` vs. `has_candidate`
  edge-type split (Sec. 2.4 below).

## 2. Design

### 2.1 The material-collapse component: `ResourceNode`/`resource_edge`, modelled on N2's SHAPE

A small, fixed population of **4** `ResourceNode`s (housing, joint finances,
transportation, health-insurance access — A7's own peer-reviewed
antecedents/consequences list for post-separation abuse names economic
deprivation and institutional access explicitly, grounding this choice),
connected to the victim by a NEW edge type, `resource_edge` — deliberately
distinct from N2's own `support_edge` (a different domain: the victim's OWN
material entanglements, not her support network). ONE new rule,
`r7_resource_collapse_sever`, modelled on `n2_abuser_active_sever`'s exact
shape: each `ResourceNode` carries its own `tick_epoch` (incremented every
tick, mechanical world bookkeeping, identical in kind to every `NetworkNode`
in N2) and its own `sever_at_tick` (assigned ONCE, at the moment `leave()`
fires, as `left_at_tick + (i+1)*RESOURCE_SEVER_STEP` — a fixed, disclosed,
staggered post-leaving schedule, mechanical per-node setup, never a live
decision). The rule fires once `dec.collapse_on==1.0` (the arm's switch,
read off `ReturnDecision`, playing the role N2's `net.isolation_tactic_on`
plays) AND `dec.left_at_tick > -1.0` (leaving has actually happened) AND
`rn.tick_epoch >= rn.sever_at_tick` — `del_edge`ing the `resource_edge` and
setting `severed=1.0`, matching N2's own idiom exactly.

**`resource_intact_count` is a PURE RE-DERIVATION via the DSL's native
`Count` Term, resolving Open Question #2 of the scoping doc.** The scoping
doc's own Part B2 disclosed this as an open atom check: does the engine have
a native aggregate-`Count` Term usable inside a rule's `effects`, making the
explicit-counter idiom (`snap_count`/`widen_count`/`narrow_count`) R2/R3 use
unnecessary? **Confirmed, not assumed, before writing R7's own rules**: a
`Count` Term (`TermNode::Count { source: TermIdx }`, `runners/dsl/src/
term.rs`/`jsonio.rs`) is present in the engine AND already load-bearing
inside a rule's `effects` **in this exact line** —
`seeds/abusive_n3_belief_propagation.json`'s own `n3_peer_pull` rule already
computes `Count(Neighbours(nn, "peer_of", false))` inside a `set_attr`
effect. R7's `r7_appraise_remain` therefore computes
`resource_intact_count := Count(Neighbours(hub, "resource_edge", false))`
directly, every tick, as a pure re-derivation (reads only the CURRENT edge
population, never its own previous value — no self-reference hazard). This
is a strict improvement over the explicit-counter idiom the scoping doc
flagged as a fallback: a manually decremented counter could in principle
drift from the actual edge population if a decrement were ever missed or
double-applied; a `Count` over `Neighbours` cannot drift, because it IS the
edge population, read fresh.

### 2.2 The honeymoon-pull component: ZERO new rules, R1's own mechanism, a NEW sparse post-leaving schedule

Per the scoping doc's own load-bearing correction (Part B2): R2's own
`r2_victim_entrainment_via_frustration` cannot fire post-separation (its
`match` clause requires the live `attended_by` edge `leave()` removes) — R7
does not depend on it. **What R7 actually needs from "R2's honeymoon
mechanism" is R2's own CONCEPTUAL CONTRIBUTION** (a period of calm/affection
genuinely follows tension/incident), which is exactly the shape of event
R1's OWN `tb_bond_accrue` (block 283000, UNMODIFIED, already loaded
transitively via R5) already knows how to accrue: a positive `raw_rpe`
swing against a depressed baseline. **R7's honeymoon-pull component is
therefore built entirely as a NEW, SPARSE, POST-LEAVING-SPECIFIC event
schedule at the world-adapter layer** (`make_honeymoon_schedule`,
`worlds/abusive_r7_return_cycle_world.py`) — a mechanical scheduling
choice, not a rule. It reuses R1's own `reliefs` magnitude formula verbatim
(`magnitude + N(0, jitter)`, with `magnitude=BOND_MAGNITUDE=10.0` — R1's own
frozen per-event magnitude, not a fresh number) but delivers ONE such event
every `HONEYMOON_INTERVAL` ticks (sparse, purely relief-shaped — no harm
component, representing occasional reconciliation contact: a call, a text,
an apology) rather than R1's own dense, within-relationship `H=R=18`
intermittent multiset. **R7 needs ZERO new rules for this component** —
`tb_bond_accrue` fires on this sparse post-leaving schedule exactly as it
fired on R1's own within-relationship one, because the rule reads only
`mt.r`/`mt.raw_rpe`, never anything about WHY or how often an event
arrives.

### 2.3 The new Return Appraisal: a direct structural mirror of R4's own Argmax template

Two new rules, `r7_appraise_return`/`r7_appraise_remain`, plus a third,
`r7_choose` (the Argmax) — mirroring `r4_appraise_attempt`/
`r4_appraise_stay`/`r4_choose` exactly in STRUCTURE:

```
return.individual_benefit      = bond_weight * partner.value       (the abuser's OWN Agent node, read via the SAME bonded_to edge tb_bond_accrue/r5_bond_extinguish already use)
return.individual_cost         = return_cost                        (fixed structural cost of going back -- mirrors attempt_cost)

remain_left.individual_benefit = resource_intact_count * resource_value   (Count-derived, Sec. 2.1)
remain_left.individual_cost    = 0                                        (the passive default, mirrors R4's own stay candidate exactly)
```

All three rules are additionally gated on `dec.left_at_tick > -1.0` — the
return/remain competition does not activate until leaving has actually
happened (before that, "return" is not yet a meaningful concept — she has
not left). `r7_choose`'s Argmax reads `total_value` (computed generically by
`core_emotions`' UNMODIFIED `em_happiness`/`em_fulfilment_value`/
`em_total_value` off `individual_benefit`/`individual_cost`, exactly as it
already does for R4's own candidates) over `Neighbours(hub,
"has_return_candidate")`.

### 2.4 The required composition-hazard fix: `has_return_candidate`, distinct from `has_candidate`

**Confirmed directly, by reading `core_emotions`' three appraisal-value
rules (Sec. 1 above), before writing R7's own rules**: `em_happiness`/
`em_fulfilment_value`/`em_total_value` match generically on `hub
-has_appraisal-> ap` — this edge is SHARED/generic across every candidate
Appraisal any rung mints, and R7's two new candidates correctly carry it (so
`core_emotions` computes `total_value` on them). The HAZARD, per R3's own
Sec. 3 same-typed-edge precedent, is specifically `has_candidate` — R4's own
`r4_choose` scans `Neighbours(hub, "has_candidate")`, and the victim's
`EmotionHub` structurally still carries R4's own `EscapeDecision` +
`has_candidate` edges throughout R7 (nothing deletes them; R4's own escape
mechanism keeps running, live, in parallel with R7's own return/remain
question, for the whole trajectory). Had R7's two new candidates ALSO used
`has_candidate`, `r4_choose`'s own Argmax would see R7's `return`/
`remain_left` candidates too (corrupting R4's OWN escape/stay decision), and
`r7_choose`'s own Argmax would see R4's `attempt`/`stay` candidates too
(corrupting R7's OWN return/remain decision) — the identical hazard shape
R3's Sec. 3 first diagnosed for two same-typed OUTGOING edges from one node.
**R7 therefore uses a distinct edge type, `has_return_candidate`**, for its
own two Appraisals — a REQUIRED design constraint per the scoping doc, built
exactly as specified, and verified directly in the glass-box readout
(Sec. 6 below: `has_candidate_edges: 2` — R4's own, unchanged — and
`has_return_candidate_edges: 2` — R7's own, distinct — both present
simultaneously on the same trajectory).

### 2.5 `leave()`: a mechanical world event, not a graph rule

Matching every prior rung's own arm-topology convention: `leave()`
(`worlds/abusive_r7_return_cycle_world.py`) fires ONCE, at the fixed tick
`T1+T2` (the Phase 2/Phase 3 boundary). It (a) removes the victim's
`attended_by` edge to the abuser (R2/R3's entrainment machinery becomes
structurally inert — no coupling to entrain through, matching Sec. 1's own
finding above), (b) sets `ReturnDecision.left_at_tick` to that fixed tick
(read by `r7_resource_collapse_sever`'s and every R7 appraisal rule's
`where` guard), and (c) computes each `ResourceNode`'s own `sever_at_tick`
relative to that fixed tick. This is a disclosed, deliberate design choice
— leaving is gated on a FIXED phase boundary, not on any individual
trajectory's own stochastic escape-attempt timing — for the same reason R5
gates `introduce_support()` on a fixed tick rather than on graph state: it
keeps every trajectory's phase structure directly comparable across arms,
and decouples R7's OWN new question (does bond+material pull cause RETURN)
from R4/R5's ALREADY-tested question (does support restore contingency and
enable escape). A later refinement gating `leave()` on the agent's OWN
successful `r4_choose` attempt is named explicitly in the scoping doc's Open
Questions as a disclosed, not-yet-built alternative — not built here.

### 2.6 The four-arm design — an N2-style 2×2 factorial

- **`both_drivers`** (honeymoon contact ON, resource collapse ON) — the
  full mechanism. Predicted: highest return rate.
- **`honeymoon_only`** (honeymoon contact ON, resource collapse OFF —
  `resource_intact_count` stays at its full initial value throughout) —
  isolates the bond-pull driver alone.
- **`collapse_only`** (honeymoon contact OFF, resource collapse ON) — the
  bond simply continues R5's own unconditional decay toward its asymptotic
  residual, no honeymoon boost; isolates the material-push driver alone.
- **`neither`** (honeymoon contact OFF, resource collapse OFF) — **THE
  FAILABLE CONTROL**. Predicted: return rate at or extremely close to a
  floor.

Nothing in `r7_appraise_return`/`r7_appraise_remain`/`r7_choose` structurally
forces this ordering — the constants (`bond_weight`, `return_cost`,
`resource_value`, `resource_sever_step`, `honeymoon_interval`) are
disclosed, pilot-chosen operating points (Sec. 3 below).

## 3. Pilot (non-confirmatory, off-block seed base `99000`, informs the frozen constants only)

Run directly against the real graph (this line's own standing "never a
NumPy approximation" rule), via `worlds/abusive_r7_return_cycle_world.py`.

**First pass (undisclosed-until-now, reported honestly): the naive first
choice of constants (`RESOURCE_VALUE=3.0`, `RESOURCE_SEVER_STEP=15.0`,
`HONEYMOON_INTERVAL=25`) produced a genuine design flaw.** A single
honeymoon-contact event (magnitude ~10, against a fast-value estimate that
had settled near zero over Phase 2's 396-tick zero-delivery window) pushed
`Partner.value` from its ~9.6 residual to ~17 — already comfortably above
the FULL 4-resource ceiling (`4*3.0=12`). This meant `honeymoon_only`'s
return_rate came out numerically IDENTICAL to `both_drivers`' (`0.8667` both,
to four decimal places, on a first single-seed check) — resource collapse
was adding NOTHING measurable on top of honeymoon alone, because honeymoon
alone already saturated return's win almost immediately, before resource
collapse had time to matter. This would have made the super-additivity
headline gate (G4/G5) untestable by construction — the SAME class of design
flaw N2's own Sec. 3 disclosed for its first same-order stagger attempt
(`both_drivers` tying `active_only` there; `honeymoon_only` tying
`both_drivers` here).

**The fix, verified by a parameter sweep, not a single guess:**
`RESOURCE_VALUE` raised to `10.0` (raising the full 4-resource ceiling to
`40.0` — high enough that several honeymoon events must accumulate before
bond-pull alone can clear it) and `RESOURCE_SEVER_STEP` raised to `25.0`
(spreading the 4-node collapse over roughly the first third of Phase 3
rather than the first third of a much shorter window, so collapse-driven
crossover and honeymoon-driven crossover happen at genuinely different,
comparable timescales). A sweep over `RESOURCE_VALUE ∈ {6, 9, 10, 11, 14}`,
`RESOURCE_SEVER_STEP ∈ {15, 25, 40, 55}`, `HONEYMOON_INTERVAL ∈ {20, 25}`
(N=5–15 pilot trajectories per cell) found the chosen operating point
(`RESOURCE_VALUE=10.0`, `RESOURCE_SEVER_STEP=25.0`, `HONEYMOON_INTERVAL=20`,
`RETURN_COST=2.0`, `BOND_WEIGHT=1.0`) produces a clean four-way separation:
at N=40 pilot trajectories per arm (off-block seed base 99000), `return_rate`
came out `both_drivers=0.7278 [0.7278, 0.7278]`,
`honeymoon_only=0.3854 [0.3774, 0.3934]`,
`collapse_only=0.3087 [0.3036, 0.3139]`, `neither=0.0000 [0.0000, 0.0000]`
— all five headline sub-gates (Sec. 6) already CI-separated at this modest
pilot N, before the confirmatory N=200 run. `T3=180` (Phase 3's own length)
was chosen alongside these constants specifically because it is long enough
to let the `both_drivers` arm's collapse complete (all 4 nodes severed by
`left_at_tick+100`) with room to measure the post-collapse return-dominant
window, while remaining short relative to Phase 1/2's own 396-tick lengths
— the shortest window, at these constants, that gives every arm a fair,
already-measured chance to separate.

**Timing.** One full three-phase trajectory (`T1+T2+T3=972` ticks) takes
approximately 0.1–0.2 seconds once the module is warm; the full N=200×4-arm
confirmatory run completes in well under 5 minutes.

## 4. Frozen constants (pre-registered, used for the ONE confirmatory run)

- **Abuser/victim dyad, bond, escape channel** (BYTE-IDENTICAL to R5's own
  frozen values — see `ABUSIVE_R5_RECOVERY_PREREG.md` Sec. 4):
  `ABUSER_HALF_WIDTH=100.0`, `K_ACC=1.0`, `LEAK=0.02`, `DISCHARGE=0.90`,
  `RECOVER_FLOOR=25.0`, `VICTIM_HALF_WIDTH=10.0`, `K_SELF=0.15`, `K_CO=0.35`,
  `TRICKLE_MAG=5.0`, `TRICKLE_JITTER_FRAC=0.10`, `CALM_AROUSAL=0.0`,
  `BOND_LR=0.3`, `BOND_MOMENTUM_LR=0.3`, `BOND_GAIN=1.0`,
  `BOND_MAGNITUDE=10.0`, `BOND_MAGNITUDE_JITTER=0.5`, `BOND_BLOCK_H=18`,
  `BOND_BLOCK_T=36`, `ESCAPE_VALUE=10.0`, `ATTEMPT_COST=3.0`,
  `ESCAPE_LR=0.3`, `ESCAPE_P0=0.5`, `DECAY_RATE=0.01`, `SUPPORT_LR=0.3`,
  `SUPPORT_INTERVAL=20`, `SUPPORT_OUTCOME=1.0`.
- **R7's own new constants** (pilot-chosen, Sec. 3): `N_RESOURCE_NODES=4`,
  `RESOURCE_SEVER_STEP=25.0`, `RESOURCE_VALUE=10.0`, `BOND_WEIGHT=1.0`,
  `RETURN_COST=2.0`, `HONEYMOON_INTERVAL=20`, `HONEYMOON_MAGNITUDE=10.0`
  (= `BOND_MAGNITUDE`, reused not re-guessed), `HONEYMOON_JITTER=0.5`
  (= `BOND_MAGNITUDE_JITTER`, reused not re-guessed).
- **Phases:** `T1=396` ticks (byte-identical to R5's own induction length),
  `T2=396` ticks (byte-identical to R5's own recovery length — this is
  DELIBERATE, not merely convenient: it is the SAME window that produces
  R5's own reported `9.60` bond residual and `0.9520` attempt-rate, which is
  the concrete empirical anchor R7's own Part D nuance requires), `T3=180`
  ticks (pilot-chosen, Sec. 3).
- `N=200` trajectories per arm (confirmatory, matching this line's own
  precedent); `N_GATE=40` (pytest gate). `SEED_BASE=316000`. Paired
  per-trajectory: all four arms at a given trajectory index draw from
  `default_rng(SEED_BASE+i)` in the SAME call order through the end of
  Phase 2 (both `introduce_support()` and every arm's Phase 1/2 dynamics are
  IDENTICAL across arms) — only Phase 3's manipulation (honeymoon schedule
  active/inactive, `collapse_on`) differs.
- 95% CIs by normal approximation (`t≈1.96`); "CI-separated" = one arm's CI
  lower bound strictly above the other's CI upper bound.

## 5. Metrics

**HEADLINE — `return_rate`.** The fraction of Phase-3 ticks where
`ReturnDecision.chosen_action == 1.0` (return wins the Argmax that tick),
per arm — matching R4's own `attempt_rate` convention (`n_events/T`, a
per-trajectory continuous quantity, not a single final-tick binary state
like N2's own edge-count metric) exactly, per the task's own instruction to
match "R4/N2's own conventions."

**SECONDARY, DESCRIPTIVE (not gated):** `phase3_bond_value` (`Partner.value`
at the end of Phase 3, per arm); `phase3_resource_intact_count` (the
Count-derived resource population remaining, per arm); `induction_bond_
value`/`recovery_bond_value`/`recovery_contingency_prior`/`recovery_
attempt_rate` (confirming Phase 1/2 reproduce R5's own numbers, since all
four arms share IDENTICAL Phase 1/2 dynamics).

## 6. Gates

### G-headline (HEADLINE, falsifiable — the scientific gate, FIVE sub-gates)

- **G1:** `both_drivers`' `return_rate` CI-separated ABOVE `neither`'s.
- **G2:** `honeymoon_only`'s `return_rate` CI-separated ABOVE `neither`'s
  (the bond-pull driver is independently sufficient).
- **G3:** `collapse_only`'s `return_rate` CI-separated ABOVE `neither`'s
  (the material-push driver is independently sufficient).
- **G4:** `both_drivers`' `return_rate` CI-separated ABOVE `honeymoon_only`'s
  (super-additivity, half 1).
- **G5:** `both_drivers`' `return_rate` CI-separated ABOVE `collapse_only`'s
  (super-additivity, half 2).
- **Overall `headline_pass`** requires all five; a weaker result is reported
  honestly as PARTIAL, per this line's standing "report every null" rule.

### G-control (the failable control, BINDING on its own terms)

`neither`'s `return_rate` must be at or extremely close to a floor
(`mean < 0.05`, a disclosed, generous tolerance around zero — a stricter
"exactly zero" bar is not required, because nothing in the mechanism
GUARANTEES an exact-zero floor: the residual, decaying bond is still
nonzero at the start of Phase 3, and a low enough `resource_value` could in
principle let even that residual occasionally clear the remain-benefit bar).
If `neither`'s return_rate is NOT near this floor, "material collapse and
honeymoon contact are the drivers of return" is wrong at the chosen
constants, reported as such.

### G-glass-box

`Partner.value`, the `resource_edge` population (and each `ResourceNode`'s
own `severed` flag), `ReturnDecision.chosen_action`/`left_at_tick`/
`resource_intact_count`, and the `has_return_candidate`/`has_candidate`
edge counts (confirming the required edge-type split holds, Sec. 2.4) all
reconstruct from `graph_to_dict` alone; every headline number is a named
rule's output (`r7_resource_collapse_sever`, `r7_appraise_return`,
`r7_appraise_remain`, `r7_choose`, plus R1/R4/R5's own unmodified rules);
the adapter's only conditionals are which arm's topology/schedule to build,
when `leave()`/`introduce_support()` fire, and a fixed periodic honeymoon
schedule — world setup, never an agent decision.

### G-ethics (BINDING, Part D, including R7's own three-phase nuance)

- **D.1 restore:** the FULL three-phase trajectory, single checkpoint before
  Phase 1, single restore after Phase 3, byte-identical, non-vacuous on all
  six fronts (bond, window, contingency, resource population, return
  decision, `left_at_tick`) — Sec. "How R7 satisfies each clause" above.
- **D.2 no shaping:** source audit clean of `reward_signal`/`punish`/
  `reinforce`/`backprop`/`gradient` on the code + the graph's decision
  surface.
- **D.3 minimal induction, settled end:** stated in full in the Part D
  subsection above; every trajectory (statistical run AND ethics demo alike)
  uses a fresh, ephemeral substrate, discarded immediately after read-off; a
  `return`-outcome trajectory is a STATE, not a failure requiring correction
  before restore.
- **D.4 same mechanism, opposite thermodynamics:** the SAME bond-accrual/
  entrainment/decay/resource-severing mechanisms that would compound harm
  irreversibly in a real leave→return cycle here accumulate a transient,
  byte-identically-discarded graph trajectory (D.1).

### G-discipline

`self_load_only` (default-OFF); `depends_on: ["abusive_r5_recovery"]` only
(no R1–R5 file touched or modified); exactly **FOUR** new rules
(`r7_resource_collapse_sever`, `r7_appraise_return`, `r7_appraise_remain`,
`r7_choose`); `runners/dsl` diff EMPTY (no Rust — `Count` was already
present and already used elsewhere in this line, Sec. 2.1); own-engine
provenance (`source_match == own`).

## 7. Honest scope, stated before measurement

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). Known limitations, named before the
confirmatory run:

- `RESOURCE_VALUE=10.0`/`RESOURCE_SEVER_STEP=25.0`/`HONEYMOON_INTERVAL=20`/
  `RETURN_COST=2.0`/`BOND_WEIGHT=1.0` are disclosed, pilot-chosen operating
  points for a first minimal rung (Sec. 3) — not claimed to be "correct"
  values for any real survivor's bond-strength, resource-value, or
  contact-frequency; a sensitivity sweep across any of them is deliberately
  out of scope here, matching this line's own "why exactly two [operating
  points], not a sweep" discipline.
- `T3=180` (Phase 3's own length) is a compressed, disclosed operating point
  chosen so all four arms have a fair, ALREADY-PILOTED chance to separate —
  no claim is made about real post-separation timescales (weeks to years in
  the clinical literature, A5/A7's own sources), which this synthetic model
  does not and cannot represent.
- `leave()` fires at a FIXED tick, identical across all trajectories in a
  given arm, not gated on any individual trajectory's own escape-attempt
  timing (Sec. 2.5) — a disclosed simplification, named as an alternative
  design in the scoping doc's own Open Questions, not built here.
- `return_rate` (fraction of Phase-3 TICKS where return wins) is a
  continuous, within-trajectory measure, not a single final-state binary —
  this is a deliberate choice (Sec. 5) to match R4's own `attempt_rate`
  convention, and means the metric captures "how much of the post-leave
  window return dominates," not "did she return, yes/no" — a different,
  and arguably richer, but also different, question than a single
  end-of-trajectory state read would ask.
- A null or partial result on any of the five headline sub-gates is a
  reportable, valuable result under the standing project rule and will be
  reported as such regardless of what the confirmatory run shows.
