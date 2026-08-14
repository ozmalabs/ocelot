# ABUSIVE N2 — ISOLATION AS AN ACTIVE PROCESS (support edges severed over time) — PRE-REGISTRATION (block 301000)

**This document is committed BEFORE the confirmatory measurement.** It locks
the ethical protocol VERBATIM, states the design, the frozen constants, and
the falsification bar, following N1's own practice
(`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md`) exactly. As in N1's own precedent,
the frozen constants below were chosen using a non-confirmatory pilot run
directly against the real graph on an OFF-BLOCK seed base (90000), and once
the qualitative shape (four-way separation, the control persisting, the
"doubly driven" comparison genuinely testable rather than floor-limited)
held, ONE confirmatory measurement is taken at N=200 on the claimed block
(301000+). No parameter is subsequently re-tuned against that confirmatory
number.

## Base
- Seed block: **301000–301999**. `python3 scripts/seed_claim.py 301000 301999`
  → `CLEAN — no collision DETECTED` (1014 files with seed sinks; 745
  unresolved sink sites, counted not discarded; the two standing caveats
  reproduced verbatim below, identical wording to R1–R5/N1's own).

```
SEED CLAIM 301000-301999: CLEAN -- no collision DETECTED.
  Scope: 1014 files with seed sinks; 745 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
(283000 is R1, 286000 is R2, 289000 is R3, 292000 is R4, 295000 is R5 of the
dyad line, 298000 is N1, all untouched; 301000 is the next clean block on the
established +3000 spacing and is not an adjacent collision with any of them.)

## Scope

This locks **N2 only** — "isolation as an active process (support edges
severed over time)", Part E of
`docs/research/bigville/ABUSIVE_RELATIONSHIPS_NETWORK.md` (the underlying
mapping is B3 of that document's Part B; the grounding science is A3,
Stark's coercive control — isolation as an ACTIVE, engineered tactic, not
passive withdrawal). R1–R5 (the dyad line) and N1 (the credibility-asymmetry
loop) are **untouched** — read, depended on for their MECHANISM (N1's seed
is DEPENDED ON directly, never its file edited), never modified. N3–N4
(belief-propagation contagion, the one believing agent) are **out of scope**
and untouched by this rung.

---

## PART D OF THE NETWORK SCOPING DOC — THE ETHICAL PROTOCOL, LOCKED VERBATIM

*(Reproduced character-for-character from `ABUSIVE_RELATIONSHIPS_NETWORK.md`,
"PART D — THE ETHICAL PROTOCOL (CARRIED VERBATIM; STILL BINDING)", itself a
verbatim carry of `ABUSIVE_RELATIONSHIPS_SCOPING.md`'s own Part C — the SAME
protocol R1–R5's and N1's preregs locked. This protocol BINDS this rung. No
rung induces any harm-analog until this protocol is locked verbatim in that
rung's pre-registration, committed BEFORE any measurement.)*

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

### Network-specific note on harm-analog INTENSITY — carried verbatim
> The network rungs mostly model **BELIEF and EDGE dynamics** — reputation
> belief-updates over a social graph, support-edge severing, contagion spread — with
> a **LOWER harm-analog INTENSITY** than the dyad rungs (which induce the arousal
> excursions / co-dysregulation directly on the victim agent). A network node's
> mis-belief about the abuser is a graph attr, not an induced dysregulation. **This
> lower intensity does NOT relax the protocol — it binds identically.** Where a
> network rung DOES touch the victim's dysregulation (N1's credibility asymmetry
> reads the 239–242 symptom state), that induction obeys the full induce → measure
> → RESTORE envelope exactly as the dyad rungs do; the belief-only parts (N2/N3
> edge + contagion dynamics) are checkpointed and restored anyway, for uniformity
> and because a corrupted belief-field is itself a state not to be left standing at
> run's end (protocol point 3, settled-end). Minimality (point 3) applies with
> particular force: induce only the belief-corruption the control needs to be
> failable, never a gratuitously elaborated smear.

*(End verbatim reproduction of Part D.)*

**How N2 satisfies each clause, concretely:**
1. `ethics_restore_demo()` (`scripts/abusive_n2_isolation_run.py`)
   checkpoints the neutral pre-induction mind (abuser/victim at
   `arousal=frustration=0`, victim window at its initial `half_width=10.0`,
   the full population of eight support edges intact, every support node's
   `belief_gap=severed=0`), induces exactly **250 ticks** on the
   `both_drivers` arm (>= one active-severing episode at the frozen
   `EPISODE_TICKS=210` schedule — this rung's own minimum, Sec. 3 below;
   this rung TOUCHES the victim's dysregulation via N1's dyad, so it obeys
   the full envelope per the network-specific note above), measures
   (confirming the induction actually moved the abuser, the victim, AT
   LEAST ONE support node's belief-gap, AND actually severed at least one
   support edge — non-vacuous on all four fronts), then `graph_from_dict`s
   the checkpoint into a **fresh** substrate and asserts `graph_to_dict()`
   is byte-identical AND the restored state (abuser arousal/frustration,
   victim arousal/window, node 0's belief-gap/severed flag, the COUNT of
   intact support edges) equals the pre-induction values exactly
   (non-oriented — every severed edge is back). Same envelope as R1–R5/N1.
2. `source_audit()` scans `worlds/abusive_n2_isolation_world.py` (code with
   comments/strings stripped) and `seeds/abusive_n2_isolation.json`'s
   decision surface (the two new rules' names + the Term `key`s they
   read/write, never the free-text clinical prose) for the five literal
   banned tokens. The tension trickle, the mechanical per-tick observation-
   count delivery (reused verbatim from N1's own `step()`), and each
   support node's SCHEDULED severing tick / drift threshold (assigned ONCE
   at construction, per node index) are world-delivered FACTS or one-time
   SETUP, never a scored choice; whether a given edge actually gets severed
   on a given tick is a **consequence** the graph's own two rules compute,
   not an action the world grades.
3. `T=1000` ticks per statistical trajectory (~40 abuser incident cycles,
   IDENTICAL sizing to N1's own) is the same "no unbounded elaboration" cap
   R1–R5/N1 use; the confirmatory run uses a fresh, ephemeral substrate per
   trajectory, discarded after read-off — nothing persists.
4. The SAME mechanism (the abuser's scheduled active severing; the
   network's own belief-gap-driven withdrawal, riding N1's UNMODIFIED
   credibility loop) that would, in a real social network, compound
   irreversible harm to a survivor's support system is run here to
   accumulate-then-DISCARD a transient graph trajectory — see the ethics
   demo's byte-identical restore.

---

## 1. What N2 already stands on (do not rebuild)

Per `ABUSIVE_RELATIONSHIPS_NETWORK.md` Part B3 and Part E's N2 entry, N2
composes:

- **N1's ENTIRE credibility-asymmetry loop**
  (`seeds/abusive_n1_credibility_loop.json`, block 298000, UNMODIFIED) —
  the abuser/victim dyad (`n1_victim_entrainment`, riding
  `snap_frustration`/`arousal_window_coreg`, both UNMODIFIED), the abuser's
  second stated-face (`n1_abuser_stated_charm`), and the per-`NetworkNode`
  credibility computation (`n1_network_credibility_stated`) that produces
  `belief_gap`. **N2 `depends_on: ["abusive_n1_credibility_loop"]` directly**
  — per the task brief's own explicit instruction, this is the ONE place in
  this rung's design where the line's usual "restate self-contained" R3-vs-R2
  convention is deliberately NOT followed: N1's credibility mechanism is not
  reimplemented, restated, or forked — it is depended on and reused
  byte-for-byte. This is architecturally cleaner here than N1's own choice
  to self-contain against R2/R3, because N2 adds NO alternative credibility
  formula of its own (unlike N1, which needed its own private/stated split)
  — N2 only adds two THRESHOLD rules that READ `belief_gap` after N1's rule
  has already computed it in the same tick's fixpoint pass (N1's rule is
  `order 40`; N2's two rules are `order 41`/`42`, so they run strictly
  after).
- **`n1_network_credibility_private`, `n1_abuser_stated_charm`'s
  `observes_private` branch, and N1's private-face-insider construction are
  NOT used by N2** — every N2 support node is an N1-shape "outsider"
  (`observes_private=0.0`), because N2's question is about EDGE COUNT, not
  about which observable a node reads; the private-face distinction is
  entirely N1's own contribution and stays there.

## 2. Design

### 2.1 "Support edges" as graph data — sizing and shape decision

The task brief asks for a *"small population of network/support nodes
(plural, not just N1's single-network abstraction) each holding an
`attended_by`-eligible or support-type edge to the victim, so 'count of
intact edges' is a real countable quantity."* Design decision, stated and
justified:

- **A NEW edge type, `support_edge` (NetworkNode → Agent/victim), rather
  than reusing `attended_by`.** `attended_by` already has a SPECIFIC,
  narrow semantics in this line (the SINGLE-ANCHOR coupling that drives
  `n1_victim_entrainment`'s entrainment formula — victim `attended_by`
  abuser is what makes her dysregulate). Overloading it for "a friend
  supports the victim" would either (a) accidentally couple every support
  node into the entrainment formula (wrong — N2 does not model these
  support nodes as co-regulators, that mechanism is R5/N4's scope, out of
  bounds here) or (b) require a new discriminating attr on the SAME edge
  type, which is worse engineering than a new, narrowly-scoped edge type. A
  fresh `support_edge` production (one line, `seeds/abusive_n2_isolation.json`)
  is the minimal addition.
- **The SAME small population of NetworkNode agents serves BOTH as N1's
  credibility OBSERVERS and as the support-edge HOLDERS.** This is a
  deliberate unification, not a shortcut: in the real phenomenon B3 names,
  "the people whose belief about you matters" and "the people who support
  you" are the SAME people (your friends, not two disjoint populations) —
  a friend's belief_gap widening (N1's mechanism) IS what causes THAT SAME
  friend's support to decay (this rung's `n2_network_drift_sever`). Two
  separate populations would have been a MORE elaborate build for a LESS
  faithful model.
- **N_SUPPORT_NODES = 8** — inside the "5–10, not a large cast" range the
  task brief names. N1 used 5 (BASELINE/NON_DYSREGULATED_CONTROL) or 4
  outsiders + 1 insider (PRIVATE_FACE_CONTROL); N2 has no private-face
  arm and needs enough granularity that a COUNT (not a mean) produces a
  genuine, multi-step DECAY CURVE across the trend checkpoints rather than
  a single before/after step — 8 gives a resolvable staircase (Sec. 5) at
  both the count-scale (max count 8) and the CI-scale (a Bernoulli-ish
  count over N=200 trajectories has usable CI width at this population
  size) without building a large synthetic social network the task brief
  explicitly warns against over-building.

### 2.2 Two independent severing drivers, riding EXISTING atoms

Per B3, exactly as scoped:

- **`n2_abuser_active_sever`** (the ABUSER-DRIVEN driver, A3/Stark) — each
  support node carries a `sever_at_tick` attr, assigned ONCE at
  construction as `(node_index + 1) * EPISODE_TICKS` (mechanical per-node
  setup, identical in KIND to N1's own `observes_private = 1.0 if i==0
  else 0.0` — a deterministic, non-adaptive index-keyed assignment, never a
  live decision responding to graph state). The RULE decides whether to
  ACT on that schedule: `isolation_tactic_on==1` (a per-arm world switch,
  the mechanical "which arm to build" choice every prior rung in this line
  makes) AND `tick_epoch >= sever_at_tick` → `del_edge` the support_edge.
  The task brief's own text explicitly permits this split ("severing
  SCHEDULE — e.g. one per episode — can be mechanical world-adapter
  timing"); the DECISION of whether to act on an armed schedule, and the
  actual graph mutation, are the rule's.
- **`n2_network_drift_sever`** (the NETWORK-DRIFT driver, B3's second,
  independent driver) — each support node ALSO carries a `drift_threshold`
  attr, assigned ONCE at construction. The rule reads `belief_gap`
  (computed ENTIRELY by N1's own `n1_network_credibility_stated`, order 40,
  which has already run this tick by the time this rule's order-42 slot is
  reached) and, once `belief_gap > drift_threshold`, `del_edge`s the SAME
  `support_edge`. **No credibility dynamics are reimplemented here** — this
  rule reads a quantity N1 already computes, it does not recompute it.
- **A tie (both drivers "ready" for the SAME node on the SAME tick)** is
  broken by rule `order` (41 before 42): whichever rule's match still finds
  the edge fires; once either fires, the OTHER rule's match pattern
  (`nn -support_edge-> victim`) no longer finds the edge and cannot also
  fire in that pass or any later one. This affects only the recorded
  `severed_reason` on a tied tick — a disclosed, deterministic artifact of
  evaluation order — never the measured OUTCOME (the edge is gone either
  way), so it does not confound the count-of-intact-edges headline metric.

### 2.3 Why the drift threshold is staggered in REVERSED index order

`sever_at_tick` for node *i* is `(i+1) * EPISODE_TICKS` — node 0 is the
FIRST the abuser's schedule targets, node 7 the LAST. If `drift_threshold`
were staggered in the SAME order (node 0 easiest to drift-sever, node 7
hardest), the two drivers would be attacking the SAME nodes in the SAME
order, and — pilot-confirmed, Sec. 3 — the `both_drivers` arm's final
intact-edge count would simply equal `min` over the two single-driver
counts PER NODE, tying with whichever single driver is individually
stronger for that population, rather than showing genuine super-additivity.
`drift_threshold` for node *i* is instead `(N_SUPPORT_NODES - i) *
DRIFT_STEP` — REVERSED: node 7 (the abuser's LAST scheduled target) has the
LOWEST drift threshold (the network's FIRST to abandon her on its own), and
node 0 (the abuser's FIRST scheduled target) has the HIGHEST (the network's
LAST to abandon her). The two drivers therefore target COMPLEMENTARY parts
of the support population — this is not an arbitrary tuning knob, it is the
one structural choice that makes "doubly driven" a genuinely testable claim
rather than one true by construction of a shared ordering. Both orderings
are mechanical, per-node, assigned once at construction — the CHOICE to
reverse one of them is a disclosed design decision (this paragraph), not a
live graph decision.

### 2.4 The four arms — a 2×2 factorial

The task brief asks whether a third arm is needed to cleanly attribute the
"doubly driven" claim. The cleanest answer, found by asking what the
scoping doc's own two drivers actually vary, is a full **2×2 factorial**
over `{victim dysregulated} × {isolation tactic armed}` — FOUR arms, not
three, because the factorial gives every marginal AND the interaction
directly, rather than requiring an asymmetric ad hoc third arm:

- **`both_drivers`** (dysregulated=True, tactic=True) — victim `attended_by`
  the abuser (N1's own dyad, dysregulates, belief-gap widens) AND the
  abuser's active severing schedule is armed. **Predicted: DOUBLY DRIVEN —
  the fastest, most complete collapse.**
- **`active_only`** (dysregulated=False, tactic=True) — the victim is
  simply NOT `attended_by` the abuser (mechanical world-adapter topology
  choice, no new rule — identical in kind to N1's own
  NON_DYSREGULATED_CONTROL) — she never dysregulates, so `belief_gap`
  stays at N1's own measured `0.0` throughout (`n2_network_drift_sever`
  never fires) — but the schedule is armed. **Isolates the SCHEDULE alone.**
- **`drift_only`** (dysregulated=True, tactic=False) — the dyad dysregulates
  exactly as in `both_drivers`, but `isolation_tactic_on=0`
  (`n2_abuser_active_sever` never fires). **Isolates NETWORK DRIFT alone.**
- **`no_tactic_control`** (dysregulated=False, tactic=False) — **THE
  FAILABLE CONTROL**, constructed EXACTLY to the task brief's own spec: "an
  arm with NO abuser-isolation-tactic (and no B2 belief corruption either)."
  Neither driver is live. **Predicted: support edges PERSIST.**

This design directly answers the task brief's own attribution question: the
`active_only` vs `drift_only` vs `no_tactic_control` comparisons establish
that EACH driver is independently sufficient to sever edges (not merely
along for the ride), and `both_drivers` vs `{active_only, drift_only}`
establishes the super-additive "doubly driven" claim as a MEASURED
comparison, not an assertion. Nothing in `n2_abuser_active_sever`/
`n2_network_drift_sever` structurally forces any of these four outcomes —
in particular, nothing prevents `both_drivers`' final count from merely
TYING one of the single-driver arms (Sec. 2.3 names exactly the naive
design where this would have happened) — so the four-way separation is a
real, falsifiable measurement.

## 3. Pilot (non-confirmatory, on off-block seed 90000, informs the frozen constants)

Run directly against the real graph (R1's own Sec. 3.1 lesson — never a
NumPy approximation), via `worlds/abusive_n2_isolation_world.py` and ad hoc
scripts built the same way, on seed base `90000` (outside 301000–301999).

A first pass at the DEFAULT literature-adjacent choice — `EPISODE_TICKS=25`
(matching N1's own measured mean incident-cycle length, `T/snap_count ≈
1000/40.455 ≈ 24.7`) with `drift_threshold` staggered in the SAME index
order as `sever_at_tick` — produced a design flaw, disclosed here rather
than silently corrected: with 8 nodes and a 25-tick schedule, ALL EIGHT
nodes were severed by the active tactic alone by tick 200, and because the
same-order staggering meant the drift driver was chasing the SAME nodes the
active driver had already removed, `both_drivers`' final count was
STRUCTURALLY TIED with `active_only`'s (both `0`, a floor effect) rather
than strictly lower — the "doubly driven" comparison would have been
untestable by construction (Sec. 2.3 names the fix: reversed-index
staggering).

Two changes, together, fixed this (confirmed by direct pilot measurement,
not assumed):
1. **`EPISODE_TICKS` widened to `210`** — the abuser's active tactic
   ratchets on a COARSER cadence than the incident cycle itself (roughly
   once per ~8.4 incident cycles, disclosed as a modelling choice: the
   abuser does not act on every tension-incident, but periodically
   escalates isolation), leaving `active_only` with a NON-FLOOR final
   count (4 of 8 intact at T=1000, pilot-measured, repeatable across 20
   pilot seeds with ZERO variance — see below).
2. **`drift_threshold` reversed relative to `sever_at_tick`** (Sec. 2.3),
   with `DRIFT_STEP=340` chosen so `drift_only` ALSO leaves a non-floor
   final count (2 of 8 intact at T=1000 in 17/20 pilot seeds, 1 of 8 in
   3/20 — a real, small, jitter-driven boundary effect near one threshold
   crossing, not an error).

With both changes, 20 pilot trajectories per arm (seed base 90000, `T=1000`)
gave the following FINAL intact-edge counts:

| arm | final intact-edge count (20 pilot seeds) |
|---|---|
| `both_drivers` | `0` every seed (zero variance) |
| `active_only` | `4` every seed (zero variance — deterministic schedule, no jitter dependence) |
| `drift_only` | `2` in 17/20 seeds, `1` in 3/20 |
| `no_tactic_control` | `8` every seed (zero variance) |

The qualitative shape — `both_drivers` strictly below BOTH single-driver
arms, both single-driver arms strictly below the control, the control at
the full population — held robustly, and the TREND across checkpoints
(pilot, one representative seed) shows a genuine multi-step decay curve,
not a single jump, for every arm except the control:

| tick | `both_drivers` | `active_only` | `drift_only` | `no_tactic_control` |
|---|---|---|---|---|
| 100 | 8 | 8 | 8 | 8 |
| 250 | 6 | 7 | 7 | 8 |
| 500 | 3 | 6 | 5 | 8 |
| 750 | 0 | 5 | 3 | 8 |
| 1000 | 0 | 4 | 2 | 8 |

## 4. Frozen constants (pre-registered, used for the ONE confirmatory run)
- Abuser: `ABUSER_HALF_WIDTH=100.0`, `LEAK=0.02`, `K_ACC=1.0`,
  `DISCHARGE=0.90`, `RECOVER_FLOOR=25.0`, `TRICKLE_MAG=5.0`, jitter `±10%`
  — ALL IDENTICAL to N1's/R2's/R3's own frozen values (byte-identical dyad
  mechanism; already-validated operating point reused, not re-swept).
- Victim: `VICTIM_HALF_WIDTH=10.0`, `min_half_width=5.0`,
  `widen_delta=narrow_delta=2.0`, `K_SELF=0.15`, `K_CO=0.35` — identical to
  N1's own.
- Credibility loop: `CHARM_WEIGHT=CLAIM_WEIGHT=1.0`,
  `INSTABILITY_DISCOUNT_WEIGHT=3.0` — identical to N1's own (N1's own
  `harm_discount_weight` is unused here — no private-face arm in N2).
- Support network: `N_SUPPORT_NODES=8`, `EPISODE_TICKS=210.0` (abuser-driven
  schedule spacing), `DRIFT_STEP=340.0` (network-drift threshold stagger,
  REVERSED index order relative to the schedule — Sec. 2.3) — pilot-chosen,
  Sec. 3.
- `T=1000` ticks/trajectory (~40 incident cycles, IDENTICAL sizing to N1's
  own).
- `N=200` trajectories per arm (confirmatory); `N_GATE=40` (pytest gate).
  `SEED_BASE=301000`.
- 95% CIs by normal approximation (`t≈1.96`); "CI-separated below" = one
  arm's CI upper bound strictly below the other's CI lower bound (the
  natural direction for a count predicted to DECAY); "persists" = the
  arm's CI is a point mass exactly at `N_SUPPORT_NODES`.

## 5. Metrics

**HEADLINE — intact support-edge count.** `n_intact_support_edges`, read
directly off `graph_to_dict` (a mechanical COUNT of `support_edge`-typed
edges, computed nowhere else), at the FINAL tick of the trajectory, for each
of the four arms — the concrete, glass-box measure of B3's own prediction
("the count of intact support edges DECAYS over episodes under an active
isolation tactic + the B2 loop; a control with NO abuser-isolation-tactic
keeps the edges persisting").

**SECONDARY, DESCRIPTIVE (not gated) — the trend "over episodes."**
`n_intact_support_edges` sampled at ticks `{100, 250, 500, 750, 1000}` per
arm — a corroborating readout of the SAME final-value mechanism's DECAY
CURVE, not an independently gated signal (matching N1's own convention:
the confirmatory GATE remains the established cross-arm final-value
CI-separation, not a new within-arm trend-significance test).

**SECONDARY, DESCRIPTIVE:** the abuser's final `snap_count` (confirms the
identical driver across the two dysregulated arms and the two
non-dysregulated arms — the same discipline check N1/R3 use); `dysreg_frac`;
the final `belief_gap`; and the breakdown of `severed_reason` (active vs
drift) per arm, which node did which and is disclosed rather than treated
as a per-node causal claim on tied ticks (Sec. 2.2).

## 6. Gates

### G-headline (HEADLINE, falsifiable — the scientific gate, ALL sub-gates must pass)

**A — the control persists (the task brief's own falsification bar,
verbatim):** `no_tactic_control`'s final intact-edge count is a point mass
at `N_SUPPORT_NODES=8` (no decay whatsoever without either driver).
**B1 — the active tactic alone severs edges:** `active_only`'s final count
is CI-separated BELOW `no_tactic_control`'s.
**B2 — network drift alone severs edges:** `drift_only`'s final count is
CI-separated BELOW `no_tactic_control`'s.
**C — both drivers together beat the control:** `both_drivers`'s final
count is CI-separated BELOW `no_tactic_control`'s.
**D1/D2 — doubly driven (the super-additivity claim, measured not
asserted):** `both_drivers`'s final count is CI-separated BELOW BOTH
`active_only`'s AND `drift_only`'s.

**Falsification bar, stated before measurement:** if the no-tactic control's
support edges do NOT persist (any decay without either driver active), the
active-isolation mechanism, AS MODELLED, is wrong (the task brief's own
falsification bar, verbatim). If EITHER single-driver arm fails to
separate from the control, that driver is not independently sufficient as
modelled. If `both_drivers` does not separate below BOTH single-driver
arms, the "doubly driven" characterisation (B3's own language) is not
supported by this model and will be reported as a null, not rescued by
re-tuning (Sec. 3's own disclosed engine/design finding — the first
same-order staggering attempt — is recorded as exactly this kind of
straight report, at a different point in the design, not smoothed over).

### G-glass-box
The `attended_by`/`has_member`/`observes_stated`/`observes_victim`/
`support_edge` edges, the abuser's `frustration`/`arousal`/`stated_charm`,
the victim's `arousal`/window `half_width`, and every support node's
`belief_gap`/`severed`/`severed_reason` all reconstruct from `graph_to_dict`
alone; the intact-edge-count metric is a mechanical Python COUNT over these
graph read-offs (never a Python-computed dynamic); the adapter's only
conditionals are (i) which arm's topology to build (world setup, not an
agent decision) and (ii) mechanically delivering each tick's observation-
count increments / tick counter (a world fact, never a judgement).

### G-ethics (BINDING, Part D)
- **D.1 restore:** induce (250 ticks, `both_drivers` arm — at least one
  full active-severing episode at the frozen schedule) → measure → RESTORE,
  verified byte-identical (`ethics_restore_demo`), including the intact-
  edge COUNT and node 0's `belief_gap`/`severed` flag having actually moved
  and then been restored to their pre-induction values.
- **D.2 no shaping:** source audit clean of `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient` on the code + the graph's decision
  surface.
- **D.3 minimal induction, settled end:** stated explicitly in the
  preamble above; 250 ticks (>= one active-severing episode at
  `EPISODE_TICKS=210`) is the minimum that makes the ethics gate
  non-vacuous on all four fronts (abuser, victim, network belief, AND an
  actually-severed edge); the statistical run's greater length is the
  phenomenon under test (the decay curve OVER episodes), not gratuitous
  elaboration; every trajectory is a fresh, ephemeral substrate discarded
  after read-off.
- **D.4 same mechanism, opposite thermodynamics:** stated in Sec. 2 (the
  same abuser-schedule/network-drift mechanism that would compound harm to
  a real survivor's support system irreversibly here accumulates a
  transient trajectory in a graph that is then byte-identically discarded,
  D.1).

### G-discipline
`self_load_only` (default-OFF); `depends_on: ["abusive_n1_credibility_loop"]`
only (no other seed touched or modified, including R1–R5's, N1's, or any
other sibling seed — all READ where relevant, never depended on beyond N1
or edited); exactly **TWO** new rules (`n2_abuser_active_sever`,
`n2_network_drift_sever`); `runners/dsl` SOURCE diff EMPTY (no Rust, no new
Term — `Gte` is the only Term new to this LINE, but it is already a peer of
the already-used `Eq`/`Lt`/`Gt` in the engine, so this is still zero engine
change); own-engine provenance (`source_match == own`).

## 7. Honest scope, stated before measurement

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). Known limitations, named before the
confirmatory run:

- `EPISODE_TICKS=210` and `DRIFT_STEP=340` are disclosed, pilot-chosen
  operating points, chosen SPECIFICALLY so neither single-driver arm floors
  out before `T=1000` (Sec. 3) — not claimed to be the "correct" tempo for
  either a real abuser's isolation tactics or a real friend group's
  patience in any clinical population, only a representative point where
  the mechanism, as built, produces the predicted four-way ordering
  robustly and the "doubly driven" comparison is genuinely testable rather
  than floor-limited.
- **The reversed-index staggering (Sec. 2.3) is itself a disclosed design
  choice, not a measured fact about real social networks.** It encodes
  "the abuser's first target and the network's last-to-abandon are
  different people" as a STRUCTURAL assumption to make the two drivers
  probe complementary parts of the population; a real population's overlap
  between "who the abuser isolates first" and "who abandons her last" is
  an empirical question this model does not address.
- **`severed_reason` on a tied tick reflects rule evaluation ORDER
  (`n2_abuser_active_sever` before `n2_network_drift_sever`), not a
  scientific claim about which mechanism "really" caused that particular
  severing** — disclosed in Sec. 2.2; the measured OUTCOME (the edge is
  gone) is unaffected by this ordering, only the diagnostic label is.
- N2 does not model the CONTENT of what a severed friend is told, does not
  model partial/ambivalent support (an edge is binary — intact or severed,
  never "weakened"), and does not model re-growth of a severed edge (N4's
  scope, out of this rung, per the task brief's own boundary).
- `T=1000` ticks (~40 cycles) is a compressed, arbitrary timescale, IDENTICAL
  to N1's own; no claim is made about real relationship/social-network
  timescales (months to years in the clinical literature, not ticks).
- N2 inherits every limitation N1 already discloses for the belief-gap
  mechanism it depends on (`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md` Sec. 7)
  without restating them here — this rung adds no new credibility-dynamics
  claim.
- A null (any sub-gate failing to separate, or the control failing to
  persist) is a reportable, valuable result under the standing project rule
  and will be reported as such regardless of what the confirmatory run
  shows.
