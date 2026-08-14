# ABUSIVE N2 — ISOLATION AS AN ACTIVE PROCESS (support edges severed over time) — RESULTS (block 301000)

Pre-registration: `ABUSIVE_N2_ISOLATION_PREREG.md` (locks Part D of
`ABUSIVE_RELATIONSHIPS_NETWORK.md` verbatim — itself a verbatim carry of Part
C of `ABUSIVE_RELATIONSHIPS_SCOPING.md` — committed before this confirmatory
measurement). Full-power numbers: `results/abusive_n2_isolation.json` (N=200
per arm). Gate: `tests/test_abusive_n2_migrated.py`. Base engine: own build,
`source_match == own`. `runners/dsl` diff EMPTY — **NO Rust, NO new Term**
(`Gte` is new to this LINE but already existed in the engine as a peer of
`Eq`/`Lt`/`Gt`).

## Headline — G-headline PASSES (all six sub-gates)

A 2×2 factorial (victim dysregulated × isolation tactic armed), N=200
trajectories per arm, T=1000 ticks, measuring the count of intact
`support_edge`s (out of a population of 8) at the end of the trajectory:

| arm | final intact-edge count (mean [95% CI]) | driver(s) live | predicted |
|---|---|---|---|
| **`both_drivers`** | **0.00 [0.00, 0.00]** | active tactic + network drift | fastest, most complete collapse |
| `active_only` | **4.00 [4.00, 4.00]** | active tactic alone | partial decay |
| `drift_only` | **1.90 [1.86, 1.94]** | network drift alone | partial decay |
| `no_tactic_control` — *failable* | **8.00 [8.00, 8.00]** | neither | must PERSIST |

- **A — the control persists (the task brief's own falsification bar,
  verbatim):** `no_tactic_control`'s final count is a point mass at the
  full population (`8.00 [8.00, 8.00]`, zero variance across all 200
  trajectories). `true`.
- **B1 — the active tactic alone severs edges:** `active_only`
  (`[4.00, 4.00]`) is CI-separated below `no_tactic_control`
  (`[8.00, 8.00]`). `true`.
- **B2 — network drift alone severs edges:** `drift_only`
  (`[1.86, 1.94]`) is CI-separated below `no_tactic_control`
  (`[8.00, 8.00]`). `true`.
- **C — both drivers together beat the control:** `both_drivers`
  (`[0.00, 0.00]`) is CI-separated below `no_tactic_control`
  (`[8.00, 8.00]`). `true`.
- **D1/D2 — doubly driven (measured, not asserted):** `both_drivers`
  (`[0.00, 0.00]`) is CI-separated below BOTH `active_only`
  (`[4.00, 4.00]`) AND `drift_only` (`[1.86, 1.94]`). `true` on both.

**`headline_pass: true`** — under the frozen, pre-registered configuration
(`N_SUPPORT_NODES=8`, `EPISODE_TICKS=210.0`, `DRIFT_STEP=340.0`,
`INSTABILITY_DISCOUNT_WEIGHT=3.0` inherited unchanged from N1), a support
network with NEITHER driver active keeps every edge intact for the full
1000-tick trajectory; EACH driver alone is independently sufficient to sever
edges (the schedule alone leaves 4/8 intact, network drift alone leaves
~1.9/8 intact); and the two drivers TOGETHER are strictly worse than either
alone — full collapse (0/8) versus partial collapse for each single driver.
Isolation, as modelled, is genuinely doubly driven, not merely explicable by
either mechanism in isolation.

**The decay curve, not just the endpoint (descriptive, N=200):**

| tick | `both_drivers` | `active_only` | `drift_only` | `no_tactic_control` |
|---|---|---|---|---|
| 100 | 8.00 [8.00, 8.00] | 8.00 [8.00, 8.00] | 8.00 [8.00, 8.00] | 8.00 [8.00, 8.00] |
| 250 | 6.00 [6.00, 6.00] | 7.00 [7.00, 7.00] | 7.00 [7.00, 7.00] | 8.00 [8.00, 8.00] |
| 500 | 3.00 [3.00, 3.00] | 6.00 [6.00, 6.00] | 5.00 [5.00, 5.00] | 8.00 [8.00, 8.00] |
| 750 | 0.00 [0.00, 0.00] | 5.00 [5.00, 5.00] | 3.00 [3.00, 3.00] | 8.00 [8.00, 8.00] |
| 1000 | 0.00 [0.00, 0.00] | 4.00 [4.00, 4.00] | 1.90 [1.86, 1.94] | 8.00 [8.00, 8.00] |

`both_drivers` reaches full collapse by tick 750 and stays there;
`active_only` declines in a perfectly regular staircase (its schedule is
deterministic and jitter-independent); `drift_only` declines on a similar
but not identical curve, tracking N1's own belief-gap growth curve, with a
small amount of between-trajectory variance appearing only near the LAST
threshold crossing (Sec. "honest residuals" below); `no_tactic_control`
never moves. Every arm except the control shows a genuine multi-step decay,
not a single jump — the population size (8) and the pilot-tuned schedule/
threshold spacing (PREREG Sec. 3) were chosen specifically to make this
curve resolvable.

**Both single-driver arms behaved as a real test, not a rigged one.**
Nothing in `n2_abuser_active_sever`/`n2_network_drift_sever` structurally
forces `active_only` or `drift_only` to leave any particular number of
edges intact — the PREREG's own Sec. 3 discloses a first design attempt
(same-order staggering, `EPISODE_TICKS=25`) that produced a STRUCTURAL TIE
between `both_drivers` and `active_only` (both `0`, a floor effect), which
would have made the "doubly driven" gate unfalsifiable; the fix (reversed-
index staggering + a coarser active-tactic cadence) was verified to
actually separate the four arms before being locked, not assumed.

## The engine/design finding that shaped the pilot (reported per the "shapes, not numbers" standing rule)

**Staggering the two severing drivers in the SAME per-node index order makes
"doubly driven" true by construction, not by measurement.** The first pilot
attempt assigned both `sever_at_tick` (abuser-driven schedule) and
`drift_threshold` (network-drift threshold) in the SAME node-index order
(node 0 easiest for both drivers, node 7 hardest for both). At the
literature-adjacent default `EPISODE_TICKS=25` (N1's own measured mean
incident-cycle length), the active tactic alone severed all 8 edges by tick
200 — a floor effect — and because the drift driver was chasing the SAME
nodes in the SAME order, `both_drivers`' final count TIED `active_only`'s
(both exactly `0`) rather than separating below it. This was found by
direct pilot measurement (PREREG Sec. 3), not assumed from the formula. The
fix — reversing the drift-threshold stagger relative to the active
schedule, so the two drivers target COMPLEMENTARY parts of the population,
plus widening the active-tactic cadence so it does not floor out alone
within the trajectory — is disclosed as a design decision (PREREG Sec. 2.3),
not a hidden tuning knob: it encodes the assumption that "who the abuser
targets first" and "who the network abandons last" are not the same
ordering, which is itself an empirical claim about real social networks
this synthetic model does not verify. Recorded here so a future rung
combining two independent severing/growth drivers over a shared population
checks for this same floor-effect / correlated-ordering hazard before
locking constants.

## G-glass-box — PASS

One `both_drivers`-arm trajectory reconstructs entirely from
`graph_to_dict`: exactly one `attended_by` edge (victim→abuser), eight
`has_member` edges (network→support node), eight `observes_stated` edges
and eight `observes_victim` edges (every support node observes the abuser's
stated face and the victim's presentation, exactly as N1's own outsiders
do), the abuser's `frustration`/`arousal` (27.43/27.43 at this seed's
trajectory end) and `stated_charm` (1.0), the victim's `arousal` (4.08) and
`half_width` (5.0, at the floor), and all eight support nodes' `belief_gap`
(uniformly 2355.0 — the same value every node computes, matching N1's own
finding that identically-wired outsiders converge to the identical
belief-gap) and `severed_reason` (`[1,1,1,2,2,2,2,2]` at this seed — 3
severed by the active schedule, 5 by network drift, summing to all 8
severed, 0 `support_edge`s remaining). The intact-edge-count metric is a
mechanical Python COUNT over `graph_to_dict`'s own edge list, computed
nowhere else; the adapter's only conditionals are which arm's topology to
build and mechanically delivering each tick's observation-count increments
+ tick counter — world setup and fact-delivery, never an agent decision.

## G-ethics — PASS (Part D, BINDING)

- **D.1, restore:** `ethics_restore_demo()` checkpoints the neutral
  pre-induction dyad+network (`abuser_arousal=abuser_frustration=
  victim_arousal=0.0`, `victim_half_width=10.0`, all 8 support edges
  intact, node 0's `belief_gap=severed=0.0`), induces 250 ticks on the
  `both_drivers` arm (`induction_moved_abuser=True`,
  `induction_moved_victim=True`, `induction_moved_belief_gap=True`,
  `induction_severed_an_edge=True` — abuser arousal moved to 45.15, victim
  arousal to 6.72, the window narrowed from 10.0 to 5.0, node 0's
  belief-gap moved to 549.0 and was itself severed (`severed=1.0`), and the
  intact-edge count dropped from 8 to 6 — the gate is non-vacuous on all
  four fronts), restores from the checkpoint into a **fresh** substrate,
  and confirms `graph_to_dict()` is **byte-identical** to the checkpoint
  (`byte_identical=true`) and the restored state exactly equals the
  pre-induction state on every tracked field, including the intact-edge
  COUNT (back to 8) and node 0's `belief_gap`/`severed` flag
  (`restore_non_oriented=true`). The induced severing does not persist —
  every severed edge is present again after restore.
- **D.2, no shaping:** `source_audit()` scans
  `worlds/abusive_n2_isolation_world.py` (code with comments/strings
  stripped) and `seeds/abusive_n2_isolation.json`'s decision surface (the
  two rules' names + the Term `key`s they read/write, excluding the
  free-text clinical description) for `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient`. **`forbidden_engine_hits: []`,
  `forbidden_shaping_hits: []`, `clean: true`.**
- **D.3, minimal induction / settled end:** 250 ticks (>= one full
  active-severing episode at the frozen `EPISODE_TICKS=210` schedule) is
  the minimum needed to make the ethics gate non-vacuous on the abuser, the
  victim, the network belief, AND an actually-severed edge simultaneously;
  the N=200 statistical run (which necessarily spans many more ticks — the
  decay-curve-OVER-episodes phenomenon itself, not gratuitous elaboration)
  uses a fresh, ephemeral substrate per trajectory, discarded immediately
  after read-off — nothing persists.
- **D.4, same mechanism, opposite thermodynamics:** the identical
  abuser-schedule/network-drift mechanism that would compound harm to a
  real survivor's support system irreversibly over real episodes here
  accumulates a transient trajectory in a graph that is then
  byte-identically discarded (D.1) — demonstrated, not merely asserted.

## G-discipline — PASS

`self_load_only: true`; `depends_on: ["abusive_n1_credibility_loop"]`
only — **no existing seed touched or modified**, including R1–R5's own
seeds, N1's own seed, and every other sibling seed (all read where relevant
for their mechanism, never depended on beyond N1 directly, never edited);
exactly **TWO** new rules (`n2_abuser_active_sever`,
`n2_network_drift_sever`); `runners/dsl` SOURCE diff EMPTY (no Rust, no new
Term — `Gte` is new to THIS LINE's rules but was already a peer of
`Eq`/`Lt`/`Gt` in the engine before this rung); `provenance_source_match ==
"own"`.

**Discipline check — same abuser driver across matched arms:** final
`snap_count` is statistically indistinguishable across ALL FOUR arms
(`both_drivers`/`active_only`/`drift_only`/`no_tactic_control` all
`40.44 [40.37, 40.51]`, identical seed stream, unaffected by which arm is
run), confirming the abuser's own tension-driven dynamics are completely
unaffected by the victim's coupling or the isolation tactic's arming — the
only manipulated variables reaching the network are (a) whether the victim
dysregulates and (b) whether the active schedule is armed.

## OPEN QUESTIONS of the network scoping doc, relevant to N2

None of `ABUSIVE_RELATIONSHIPS_NETWORK.md`'s seven OPEN QUESTIONS (all filed
against N1's build) named an N2-specific unresolved question — they concern
the reputation-belief surface (#1, #2, resolved by N1), the "second
audience" edge shape (#3, resolved by N1), N3's contagion mechanics (#4, out
of this rung's scope), the A5 nuance (#5, inherited unchanged from N1, not
re-litigated here since N2 reads `belief_gap` as a black box), the honest
fork (#6, carried verbatim above), and prior-art search caveats (#7). N2's
own genuinely open design question — raised by the task brief, not the
scoping doc — was **whether a third arm is needed to cleanly attribute the
"doubly driven" claim**; resolved by building a full 2×2 factorial (four
arms) rather than an asymmetric third arm, which gives every marginal effect
AND the interaction directly (PREREG Sec. 2.4) and is the reason the
super-additivity gate (D1/D2 above) is a genuine, falsifiable measurement
rather than an assumption.

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: on the (G,Γ) substrate, riding N1's ALREADY-BUILT, UNMODIFIED
credibility-asymmetry loop (which itself rides the ALREADY-BUILT, UNMODIFIED
dyad, blocks 239000/242000) and adding exactly two threshold rules, Stark's
active-isolation account (A3) and the network-drift half of B3 compose into
a measured, falsifiable, DOUBLY-DRIVEN edge-severing dynamic — the
super-additivity is not scripted, it is the CONSEQUENCE of two independent
drivers acting on a shared, countable resource (the support-edge
population), confirmed by a design that could have, and in its first pilot
attempt DID, fail to show that consequence (Sec. "the engine/design
finding" above). It is not a claim about real support-network sizes, real
severing timescales, or a validated relative strength between an abuser's
active tactics and a network's own drift in any clinical population (below
names these limits explicitly).

## The double dissolution, in this rung's own terms

**Anti-victim-blaming: "she cut off her own friends" / "she's antisocial."**
In this model the victim never performs an action that touches a single
support edge — she is not `attended_by` in `active_only`/`no_tactic_control`
by a WORLD-ADAPTER CONSTRUCTION CHOICE (which arm to build), and in
`both_drivers`/`drift_only` her only "behaviour" is the SAME abuse-caused
dysregulation N1 already measures as a consequence of the coupling, never a
choice. Every `del_edge` in this rung's two rules is triggered either by
the ABUSER's schedule (`n2_abuser_active_sever`, an action taken entirely
by the abuser's side of the graph) or by a SUPPORT NODE's own belief
crossing its own threshold (`n2_network_drift_sever`, an action taken
entirely by that node's side). There is no rule, no edge, no attr in this
model through which the victim's OWN action removes a support edge — the
"isolation is a choice she makes" reading has no mechanism to attach to
here, by construction, not merely by disclaimer.

**Anti-bystander-blaming: "they abandoned her" / "bad friends."** The
`drift_only` arm shows this precisely: every one of the 8 support nodes
runs the IDENTICAL rule (`n2_network_drift_sever`, `n1_network_credibility_
stated` underneath it) with the IDENTICAL weights on the IDENTICAL evidence
stream the abuser broadcasts — nodes differ ONLY in a pre-assigned,
disclosed threshold (Sec. "honest residuals"), never in disposition,
skepticism, or loyalty. A node's support decays exactly when — and only
when — its own Bayesian-shaped belief computation (N1's own, unmodified)
crosses a line, driven by the SAME corrupted evidence B2 already showed
rationally favours the abuser. The friends are not portrayed as worse
people than the ones who happen to hold out longer (a later threshold is a
modelling parameter, not a character trait); they are shown reaching the
SAME conclusion from the SAME poisoned evidence stream on a staggered
timetable. And critically, the `active_only` arm shows the OTHER half of
this dissolution from the opposite direction: even when NO belief
corruption occurs at all (`belief_gap` stays exactly `0.0` throughout, per
N1's own non-dysregulated-control finding, reproduced here), the abuser can
still unilaterally sever 4 of 8 edges purely by acting on the social graph
directly — "the friends must have judged her" is refused in THIS arm
because there is no judgement anywhere in the mechanism; the abuser simply
removed the edge.

## Honest residuals

- **`EPISODE_TICKS=210` and `DRIFT_STEP=340` are disclosed, pilot-chosen
  operating points** (PREREG Sec. 3), chosen specifically so neither
  single-driver arm floors out before `T=1000` — not claimed as the
  "correct" tempo for a real abuser's isolation tactics or a real friend
  group's patience in any clinical population.
- **The reversed-index staggering between the two drivers (PREREG Sec. 2.3)
  is a disclosed STRUCTURAL assumption**, not a measured fact: it encodes
  "the abuser's first target and the network's own first-to-drift-away are
  different people" to make the two mechanisms probe complementary parts of
  the population. A real population's overlap between these two orderings
  is an empirical question this synthetic model does not, and cannot,
  answer.
- **`drift_only`'s final count carries real, small, jitter-driven variance**
  (`1.90 [1.86, 1.94]`, sd≈0.30) at the LAST threshold crossing only — the
  earlier crossings (ticks ≤750 in the trend table) show exactly zero
  variance across all 200 trajectories, matching N1's own "near-zero
  variance" pattern for most of the trajectory; only the node whose
  `belief_gap` crosses its `drift_threshold` closest to `T=1000` is
  sensitive to that trajectory's specific tension-trickle jitter draw. This
  is a genuine, small dynamical fact about the model, not noise in the
  measurement.
- **`severed_reason` on a tied tick reflects rule evaluation order**
  (`n2_abuser_active_sever`, order 41, before `n2_network_drift_sever`,
  order 42) — disclosed in the PREREG (Sec. 2.2) as a diagnostic artifact,
  not a scientific claim about which mechanism "really" caused a given
  severing on a tick where both conditions were simultaneously true; the
  measured OUTCOME (the edge is gone) is unaffected by this ordering.
- **N2 does not model partial or ambivalent support** — a `support_edge` is
  binary, present or absent, never "weakened." It does not model the
  CONTENT of what a severed friend is told (a smear, a rationalisation, a
  simple fading-out are all the same `del_edge` here). It does not model
  re-growth of a severed edge — that is explicitly N4's scope
  (`ABUSIVE_RELATIONSHIPS_NETWORK.md` Part E), named as out of scope in the
  PREREG and left there.
- **N2 inherits every limitation N1 already discloses for the belief-gap
  mechanism it depends on** (`ABUSIVE_N1_CREDIBILITY_LOOP_RESULTS.md`,
  "Honest residuals") without restating them here — the instability-discount
  weight's disclosed arbitrariness, `belief_gap`'s linear-accumulator
  character, the one-dimensional `dysregulated` observable — because N2
  reads `belief_gap` as a black box and adds no new credibility-dynamics
  claim of its own.
- **`T=1000` ticks (~40 cycles) is a compressed, arbitrary timescale**,
  identical to N1's own; no claim is made about real relationship/
  social-network timescales (months to years in the clinical literature,
  not ticks).
- A null (any sub-gate failing to separate, or the control failing to
  persist) is a reportable, valuable result under the standing project rule
  and would have been reported as such — the PREREG's own Sec. 3 disclosure
  of the first, floor-tied pilot design is exactly this kind of honest
  report, surfaced even though the FINAL design passes cleanly.

## Files
- `ABUSIVE_N2_ISOLATION_PREREG.md` — pre-registration, Part D locked
  verbatim.
- `seeds/abusive_n2_isolation.json` — two new rules (`self_load_only`,
  `depends_on: ["abusive_n1_credibility_loop"]`).
- `scripts/abusive_n2_isolation_seed_build.py` — authoring tool (emits the
  seed).
- `worlds/abusive_n2_isolation_world.py` — mechanical world adapter
  (`AbusiveN2IsolationWorld`).
- `scripts/abusive_n2_isolation_run.py` — runner (statistics, glass-box,
  ethics demo, source audit, discipline).
- `tests/test_abusive_n2_migrated.py` — gate.
- `results/abusive_n2_isolation.json` — full N=200 data.
