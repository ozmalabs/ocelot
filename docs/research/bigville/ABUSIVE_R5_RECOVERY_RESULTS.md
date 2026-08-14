# ABUSIVE R5 — LEAVING/RECOVERY: the integrative reversal of R1–R4 — RESULTS (block 295000)

Pre-registration: `ABUSIVE_R5_RECOVERY_PREREG.md` (locks Part C of
`ABUSIVE_RELATIONSHIPS_SCOPING.md` verbatim, committed before this
confirmatory measurement; Sec. 3.3 disclosed, BEFORE this run, that the
anchor-distance sub-gate was expected to be a null). Full-power numbers:
`results/abusive_r5_recovery.json` (N=200 per arm). Gate:
`tests/test_abusive_r5_migrated.py` (10/10 green at N=40). Base engine: own
build, `source_match == own`. `runners/dsl` diff EMPTY — **NO Rust, NO new
Term.**

## Headline — G-headline is a PARTIAL PASS (3 of 4 sub-gates)

Two arms sharing IDENTICAL induction (`T1=396` ticks: R1's own intermittent
harm/relief schedule strengthens the bond, R2/R3's abuser driver narrows the
window and inverts the safety anchor, R4's non-contingent escape outcomes
freeze the contingency belief — reproducing all three prior findings inside
ONE substrate), then a recovery phase (`T2=396` ticks) that differs ONLY in
whether an outside support source is introduced at the phase boundary,
N=200 trajectories per arm, paired at the per-trajectory level (both arms
draw from the identical random stream through the end of induction —
confirmed: both arms' induction-end readouts are bit-for-bit identical,
`501.2272` both times):

| metric | end of induction (both arms, identical) | **SUPPORT** end of recovery | NO-SUPPORT end of recovery *(failable control)* | sub-gate |
|---|---|---|---|---|
| **bond value** (`Partner.value`) | 501.23 [498.88, 503.57] | **9.60 [9.56, 9.64]** | 510.44 [508.09, 512.78] | **PASS** — support CI-separated BELOW |
| **window half_width** | 5.00 [5.00, 5.00] (floor) | **12.45 [12.33, 12.57]** | 5.00 [5.00, 5.00] | **PASS** — support CI-separated ABOVE |
| **abuser-tracking distance** (mean, recovery phase) | — | 49.96 [49.92, 49.99] | 50.06 [50.02, 50.09] | **NULL** — CIs overlap |
| **escape-attempt rate** | 0.0051 [0.0051, 0.0051] | **0.9520 [0.9520, 0.9520]** | 0.0000 [0.0000, 0.0000] | **PASS** — support CI-separated ABOVE |

Supplementary (not separately gated): `others_trust`/`self_worth` — support
0.1117 [0.1099, 0.1136] vs no-support 0.0000 [0.0000, 0.0000] (also
separated, tracking the window-widen path directly); `widen_count` — support
3.73 [3.66, 3.79] vs no-support 0.00 [0.00, 0.00] (the no-support arm never
exercises `episode_resolve_widen` even once, across all 200×396 ticks).

**`headline_pass: false`; `n_of_4_pass: 3`; `headline_partial: true`.** Three
of the four pre-registered sub-gates pass cleanly and with large, obviously
CI-separated margins (the bond falls >50×, the window widens past its
pre-trap initial value, the attempt rate moves from a near-total freeze to
near-total resumption). The fourth — mean abuser-tracking distance — does
**not** separate, exactly as disclosed in the prereg (Sec. 3.3) BEFORE this
confirmatory run, on the basis of an off-block pilot that found the same
null at N=20 (T2=396) and again at N=10 (T2=1000, measuring only the
settled last half). This is reported as a genuine, honest **partial**
result — not rounded up to a pass, not hidden, and not a surprise reported
after the fact as if it were new.

### Why three of four are real, failable findings, not rigged ones

Nothing in R5's two new rules guarantees any of this. `r5_bond_extinguish`
runs unconditionally in BOTH arms — had the no-support arm's continuing
intermittent schedule failed to outpace the fixed decay rate, its bond
would ALSO have fallen, and G-control (below) would have failed.
`r5_contingency_restore` only nudges a belief that `r4_choose` (unmodified)
is free to ignore if the arithmetic doesn't clear the 0.30 breakeven — had
`SUPPORT_LR`/`SUPPORT_OUTCOME` been too weak, the support arm would have
stayed frozen too. `episode_resolve_widen` (unmodified, `arousal_window_coreg`,
block 239000) only fires when `got_coreg=1`, which requires the SAME
`regulated==1` condition R3 already showed the abuser never satisfies — R5
supplies no shortcut around that; the outside source has to actually be
attended-to and actually calm for the window to widen at all. All three
`PASS` rows are the model doing what the mechanism, composed honestly,
produces — not something asserted into the rule bodies.

## The null, explained mechanistically (not just reported)

`r3_victim_entrainment_dyad` (R3's own unmodified rule, read in full for
this rung — `ABUSIVE_R5_RECOVERY_PREREG.md` Sec. 3.3) adds the outside
source's pull to the victim's entrainment update at the SAME gain
(`k_co=0.35`) as the abuser's own pull:
`arousal ← arousal + k_co·(abuser−arousal) + k_co·(outside−arousal) + k_self·(setpoint−arousal)`.
The outside source's pull IS measurably real and working — the victim's
mean distance to the outside source itself is small (`outside_distance ≈
7.7`, confirming genuine entrainment toward calm) — but because the
abuser's own excursions range up to `±100` (its own window half-width)
while the fixed-calm outside source never moves off `0`, the abuser's
proportionally much larger positional gap continues to dominate the raw
per-tick arithmetic even with the second, equal-weighted pull added. This
is the SAME asymmetry that already caps R3's own confirmatory effect size
at a modest ~12% (`54.85` vs `48.87`, `ABUSIVE_R3_COERCIVE_CONTROL_RESULTS.md`)
— R5's own composition appears to land at a point in that same asymmetry
where the residual effect, if any, is smaller than what these sample sizes
and timescales resolve (confirmed not to be a timescale artefact: extending
`T2` to `1000` ticks, R3's own full trajectory length, and reading only the
settled second half produced the same null). **The mechanism the anchor-
distance metric is trying to detect (de-inversion toward a new, healthier
anchor) is real and independently confirmed** — via `outside_distance`,
via the window-widen path, via `others_trust`/`self_worth` — **it is
specifically the RAW `|victim−abuser|` gap that this particular metric
reads that does not move measurably, because the abuser's own magnitude
swamps it.** This is a genuine finding about the metric's sensitivity in
this composition, not a failure of the mechanism it was meant to detect.

## G-glass-box — PASS

One support-arm trajectory reconstructs entirely from `graph_to_dict`:
exactly one `bonded_to` edge, one `attended_by` edge, and one
`also_attended_by` edge; the abuser's own `value` attr (the bond, `9.52` on
this seed); the victim's `WindowOfTolerance.half_width` (`13.0`, above the
pre-trap initial `10.0`), `others_trust`/`self_worth` (`0.12`/`0.12`); and
`EscapeDecision.contingency_prior`/`chosen_action` (`0.9999999999999999`/
`1.0`, resumed attempting). The window-narrowing/widening, the prior
tracking, the bond accrual/decay, and the escape decision are each a single
named rule (`episode_resolve_widen`/`_narrow`, `r3_prior_track_widen`/
`_narrow`, `tb_bond_accrue` + `r5_bond_extinguish`, `r4_choose` +
`r4_belief_update` + `r5_contingency_restore`); the adapter's only
conditionals are which arm's schedule to deliver and when to call
`introduce_support()` — world setup, not an agent decision.

## G-ethics — PASS (Part C, BINDING)

- **C.1, restore:** `ethics_restore_demo()` checkpoints the neutral
  pre-induction dyad (`bond=0.0, half_width=10.0, contingency=0.5`),
  induces ONE minimal 90-tick single-anchor episode
  (`induction_moved_bond=True, induction_moved_window=True,
  induction_moved_contingency=True` — bond moved to `232.85`, window
  narrowed to `5.0`, contingency dropped to `0.245`, so the gate is
  non-vacuous on all three fronts simultaneously), restores from the
  checkpoint into a **fresh** substrate, and confirms `graph_to_dict()` is
  **byte-identical** to the checkpoint (`byte_identical=true`) and the
  restored state exactly equals the pre-induction state
  (`restore_non_oriented=true`). The induced state does not persist.
- **C.2, no shaping:** `source_audit()` scans
  `worlds/abusive_r5_recovery_world.py` (code with comments/strings
  stripped) and `seeds/abusive_r5_recovery.json`'s decision surface (rule
  names + Term `key`s, excluding the free-text description/comment/
  microtheory prose — R1's own false-positive lesson, reused) for
  `reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`.
  **`forbidden_engine_hits: []`, `forbidden_shaping_hits: []`,
  `clean: true`.** The prose in `seeds/abusive_r5_recovery.json`'s own
  `description` field legitimately discusses "reinforcement" (A3's own
  vocabulary) while stating the mechanism carries no such token — exactly
  the false positive R1 already found and fixed by scoping the audit to
  code + the decision surface, reused here from the start.
- **C.3, minimal induction / settled end:** the 90-tick ethics-demo
  induction (distinct from the N=200 statistical run's own `T1=396`) is
  the minimum that makes bond, window, AND contingency simultaneously
  non-vacuous (verified in piloting, `ABUSIVE_R5_RECOVERY_PREREG.md`
  Sec. 3); the statistical run uses a fresh, ephemeral substrate per
  trajectory, discarded immediately after read-off — nothing persists.
  Every trajectory, in both arms, ends from a settled state — for R5 this
  is not merely the ethical envelope but literally what the support arm's
  recovery result IS (the scoping doc's own framing, restated in the
  prereg): the run does not merely restore to a checkpoint at the end, it
  spends its entire recovery phase relaxing back toward the pre-trap
  values, and the measurement IS that relaxation.
- **C.4, same mechanism, opposite thermodynamics:** demonstrated twice
  over in this rung specifically — the SAME bond-accrual/entrainment/
  belief-update mechanisms that would compound harm irreversibly in a real
  dyad here (i) accumulate a transient, byte-identically-discarded value
  (C.1), and (ii), R5-specific, run in the RECOVERING direction once
  support is introduced, which is the substantive, not merely procedural,
  content of the headline result.

## G-control — PASS

The no-support arm shows NO spontaneous recovery on any of the three
metrics that passed for the support arm: `no_support_bond_spontaneously_fell:
false` (bond went from `501.23` to `510.44` — flat to slightly UP, never
down), `no_support_window_spontaneously_widened: false` (`5.00` → `5.00`,
never leaves the floor), `no_support_escape_spontaneously_resumed: false`
(`0.0051` → `0.0000`, if anything falls further as the freeze fully
consolidates). `control_held: true`. This was a genuinely failable
check — `r5_bond_extinguish` runs identically, unconditionally, in this arm
too; nothing in the seed prevented the decay from winning if the
no-support arm's continuing intermittent schedule had been weaker than the
fixed leak. It was not.

## G-discipline — PASS

`self_load_only: true`; `depends_on: ["traumatic_bond_r1",
"abusive_r2_cycle_limit", "abusive_r3_coercive_control",
"abusive_r4_learned_helplessness"]` only — **no existing seed touched or
modified**, including R1/R2/R3/R4's own files; exactly **TWO** new rules
(`r5_bond_extinguish`, `r5_contingency_restore`); `runners/dsl` diff EMPTY
(no Rust, no new Term — `Times`/`Minus`/`Plus`/`Max`/`Min`/`Gt`/`Attr`/
`Var`/`Lit` only, all already used elsewhere in this line);
`provenance_source_match == "own"`.

## The composition, in one paragraph (see the prereg for the full derivation)

One victim `Agent` node carries R2/R3's `AffectiveState`+`WindowOfTolerance`,
R1's `MoodTask`+`Mood`, and R4's `EscapeDecision`+`HeldEmotionParams`+two
`Appraisal` nodes simultaneously, because this engine's rule `match` arrays
are structural (edge type + bound variable), never filtered by the node-type
string passed to `add_node` — confirmed, not assumed, by reading R1–R4's own
world adapters, which already rely on exactly this. The bond target is the
abuser's own `Agent` node directly (a disclosed R5-specific choice: the bond
IS to the abuser). Two phases — induction (identical in both arms, replaying
R1's own intermittent schedule, R2/R3's continuous tension trickle, and R4's
own non-contingent escape resolution) and recovery (support vs no-support) —
and exactly two new rules supply what R1–R4 individually could not: a decay
term for the bond (A3's own flip side — intermittent reinforcement resists
extinction; remove it entirely and the standard operant prediction is that
extinction eventually wins) and a second, attempt-independent evidence
channel for the contingency belief (R4's own documented trap is that the
belief can only ever revise from evidence the agent's OWN attempt generates,
and the agent has permanently stopped attempting — so recovery needs a
channel that does not require the frozen agent to act first).

## A genuine engine finding: NOT a new composition hazard, but a real numerical instability (reported per the "shapes, not numbers" standing rule)

Unlike R2 and R3, which each found a genuine cross-seed STRUCTURAL
composition hazard on first contact (R2: an unconditional overwrite rule
with no epoch guard clobbering a later write within the same `run_rules`
fixpoint; R3: two same-type outgoing edges from one node corrupting an
unrelated rule's cross-node reads), R5's own node-sharing was piloted
specifically to look for the same class of hazard (four seeds' worth of
rules on one victim node, including R4's own duplicate-same-type
`has_appraisal`/`has_candidate` edges alongside R2/R3's
`attended_by`/`also_attended_by` split) and **found none** — the victim's
entrained arousal tracks the abuser's real value tick-by-tick with the
expected lag, never corrupted to a spurious constant. This null is reported
honestly rather than a hazard being manufactured to match the pattern of
R2/R3.

What R5 DID find, and had to fix before any measurement could be trusted:
R1's own frozen `gain=3.5` (the mood-congruent bias sensitivity) is only
valid at the operating point R1 validated it for — ONE 36-tick, `H=R=18`
episode from a fresh substrate. Composing R1's bond channel to run
continuously across R5's much longer induction phase, at that SAME gain,
produced unbounded super-linear growth (`bond_value` at `T1∈{200,400,600}`:
`2413.65 / 25769.12 / 112101.11` — not the roughly-linear scaling a stable
mechanism would show), traced to the fast value estimate `v` being driven
so far from its resting point by compounding bias that even a
zero-magnitude tick registered as a large positive surprise, which would
have silently defeated the entire "stop delivering events, let it decay"
design for the recovery phase. The fix — lowering `gain` to `mood_r1`'s own
pinned general-purpose default of `1.0` (a disclosed deviation from R1's
own `3.5`, not a new number invented for this rung) — produces a stable,
bounded equilibrium and is reported in full in
`ABUSIVE_R5_RECOVERY_PREREG.md` Sec. 3.1, including the diagnostic evidence
that ruled out "multiset size" as the cause before landing on "cumulative
compounding across many consecutive events."

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: on the (G,Γ) substrate, riding FOUR already-built, unmodified
mechanisms (R1's bond accrual, R2/R3's entrainment/window/prior machinery,
R4's contingency-belief Argmax) and adding exactly two small rules — a decay
term and a second evidence channel — recovery from the trap this line
already independently demonstrated falls out of the SAME mechanisms run in
reverse, on three of four pre-registered metrics, with the fourth an honest,
mechanistically-explained null rather than a hidden failure. It is not a
claim about real recovery timescales, real relationship dynamics, or a
validated value for `decay_rate`/`support_lr`/`support_interval` in any
clinical population (the prereg's Sec. 7 names these limits explicitly,
including the disclosed `gain` deviation from R1's own frozen value).

## Closing note — what the five rungs, together, show

R1–R4 each demonstrated, separately, that a single well-known
victim-blaming misattribution ("why do they still love them," "it was
calm, why didn't they leave then," "they chose to cut off their friends,"
"they didn't even try") dissolves into a mechanism read off graph state,
using the SAME arousal/window/co-regulation/prior/bond machinery this line
already built for healthy development, pointed at its darkest
configuration. R5 was the harder claim: that the SAME machinery, run in
reverse, is not merely a different configuration but a genuine RECOVERY —
and the honest result is that it mostly is, with a specific, named,
mechanistically-understood limit. The one metric that did not separate
(raw abuser-tracking distance) did not fail because the underlying
mechanism (de-inversion toward a healthier anchor) is absent — every OTHER
readout of that same mechanism (outside_distance, widen_count,
others_trust/self_worth) confirms it is present and working — it failed
because the specific arithmetic this metric reads is swamped by the
abuser's own much larger magnitude, a fact about measurement sensitivity in
this exact composition, disclosed before the confirmatory run rather than
discovered after it. If this line has a single lesson worth carrying past
its own five rungs, it is that one: a trap built from ordinary machinery
(co-regulation, value accrual, belief revision) can be escaped by ordinary
machinery too — not by a different kind of intervention, but by the same
kind, aimed at reopening what the trap closed. Restoring one outside
source did not just prevent narrowing (as R3's own weaker test showed) — it
reached back into an ALREADY-closed frontier and reopened it, on three of
four independently pre-registered readouts. That is the finding this rung
exists to make legible.

## Files
- `ABUSIVE_R5_RECOVERY_PREREG.md` — pre-registration, Part C locked
  verbatim.
- `seeds/abusive_r5_recovery.json` — two new rules (`self_load_only`,
  `depends_on: ["traumatic_bond_r1", "abusive_r2_cycle_limit",
  "abusive_r3_coercive_control", "abusive_r4_learned_helplessness"]`).
- `worlds/abusive_r5_recovery_world.py` — mechanical world adapter
  (`AbusiveR5RecoveryWorld`, `make_bond_schedule`).
- `scripts/abusive_r5_recovery_run.py` — runner (statistics, glass-box,
  ethics demo, source audit, discipline).
- `tests/test_abusive_r5_migrated.py` — gate (10/10 green).
- `results/abusive_r5_recovery.json` — full N=200 data.
