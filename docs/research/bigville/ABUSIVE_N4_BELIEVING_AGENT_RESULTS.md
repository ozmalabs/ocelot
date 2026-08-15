# ABUSIVE N4 — ONE NON-DOUBTING AGENT RESTORES A SUPPORT EDGE — RESULTS (block 307000)

Pre-registration: `ABUSIVE_N4_BELIEVING_AGENT_PREREG.md` (locks Part D of
`ABUSIVE_RELATIONSHIPS_NETWORK.md` verbatim, committed before this
confirmatory measurement). Full-power numbers:
`results/abusive_n4_believing_agent.json` (N=200 per arm). Gate:
`tests/test_abusive_n4_migrated.py`. Base engine: own build,
`source_match == own`. `runners/dsl` diff EMPTY — **NO Rust, NO new Term,
NO new rule.** This is the LAST rung of the abusive-relationships line
(`ABUSIVE_RELATIONSHIPS_LINE_SUMMARY.md`).

## Headline — G-headline is a FULL PASS (4 of 4 sub-gates)

Two arms sharing IDENTICAL induction (`T1=396` ticks: R5's own bond-
strengthening/window-narrowing/contingency-freeze trap AND N2's own
doubly-driven isolation trap, reproduced simultaneously inside ONE
substrate — both arms' induction-end readouts are bit-for-bit identical,
confirmed: `bond=499.996`, `half_width=5.0`, `n_intact=5`,
`believer_belief_gap=761.6` in both arms), then a recovery phase (`T2=396`
ticks) that differs ONLY in whether `introduce_believing_agent()` fires at
the phase boundary, N=200 trajectories per arm, paired at the
per-trajectory level:

| metric | end of induction (both arms, identical) | **BELIEVING_AGENT** end of recovery | NO_BELIEVING_AGENT end of recovery *(failable control)* | sub-gate |
|---|---|---|---|---|
| **bond value** (`Partner.value`) | 500.00 [497.59, 502.40] | **9.58 [9.54, 9.62]** | 511.25 [508.84, 513.66] | **PASS** — believing CI-separated BELOW |
| **window half_width** | 5.00 [5.00, 5.00] (floor) | **12.47 [12.35, 12.59]** | 5.00 [5.00, 5.00] | **PASS** — believing CI-separated ABOVE |
| **believer's own `belief_gap`** | 761.60 [759.39, 763.80] | **−1312.08 [−1315.56, −1308.60]** | 1539.89 [1537.01, 1542.76] | **PASS** — believing CI-separated BELOW (full sign reversal) |
| **intact support-edge count** | 5.00 [5.00, 5.00] | **4.00 [4.00, 4.00]** | 1.00 [1.00, 1.00] | **PASS** — believing CI-separated ABOVE |

Supplementary (not separately gated): `contingency_prior` — believing
1.0000 [1.0, 1.0] vs no-believing 0.2450 [0.245, 0.245] (matching R5's/
R4's own reported freeze floor exactly, in the control); `attempt_rate` —
believing 0.9520 vs no-believing 0.0000; `others_trust`/`self_worth` —
believing 0.1121 [0.1102, 0.1139] vs no-believing 0.0000 [0.0, 0.0].

**`headline_pass: true`; `n_of_4_pass: 4`; `headline_partial: false`.** All
four pre-registered sub-gates pass cleanly, with large, obviously
CI-separated margins and near-zero within-arm variance (the same
"near-deterministic mechanism at these frozen constants" shape N1's/N2's
own confirmatory runs already found — small multiplicative jitter on an
otherwise strongly-driven mechanism). This is a full, not partial, result —
disclosed honestly against the prereg's own stated expectation (Sec. 3
disclosed a clean 4/4 separation at N=10; this confirms it holds at N=200).

### The support-edge-count gap is LARGER than the guaranteed floor — a genuine, unscripted, emergent finding

The prereg (Sec. 2.9) pre-registered the GATE at the guaranteed `+1` floor
(only node 7's own restored edge is structurally guaranteed), while naming
explicitly that a LARGER gap was observed in piloting and would be reported
descriptively, not required. The confirmatory measurement: **4 intact
edges (believing) vs 1 (no-believing) — a gap of 3, not 1.** Node 7's own
restored edge accounts for exactly one; the other two (indices 3 and 4 in
the pilot's own trace, consistent across seeds given the near-zero
variance) survive in the believing-agent arm because they would otherwise
have been drift-severed slightly LATER in the trajectory, and the victim's
OWN reduced dysregulation once her window widens (a consequence of node
7's restored co-regulation) means every node — not just node 7 — sees her
present as "unstable" on fewer ticks, slowing everyone's `seen_victim_
unstable` accumulation and therefore everyone's approach to their own
`drift_threshold`. **One restored edge does not just add one edge back —
it measurably slows the REST of the network's own drift**, a real,
non-engineered, non-scripted knock-on effect of the SAME mechanism (N2's
`n2_network_drift_sever` reading N1's `belief_gap`, which itself is fed by
the victim's own `dysregulated` state), not a second intervention.

## G-glass-box — PASS

One believing-agent-arm trajectory reconstructs entirely from
`graph_to_dict`: exactly one `bonded_to` edge, one `attended_by` edge, one
`also_attended_by` edge (the believer's own co-regulator wiring), one
`observes_held` edge (the believer's own insider wiring), and **4**
`support_edge` edges (node 7's own restored edge plus the 3 that never got
severed at all, matching the headline count above on this particular
seed); the abuser's own `value` attr (the bond, `9.63` on this seed); the
victim's `WindowOfTolerance.half_width` (`13.0`, above the pre-trap initial
`10.0`); `EscapeDecision.contingency_prior` (`0.9999999999999999`); and the
believer's own `observes_private` (`1.0`) and `belief_gap` (`−1347.0`,
strongly reversed). Every one of these is a named, pre-existing rule's
output (`episode_resolve_widen`, `tb_bond_accrue` + `r5_bond_extinguish`,
`r4_choose` + `r4_belief_update` + `r5_contingency_restore`,
`n1_network_credibility_private`); the adapter's only conditionals are
which arm's schedule to deliver and when to call
`introduce_believing_agent()` — world setup, not an agent decision.

## G-ethics — PASS (Part D, BINDING)

- **D.1, restore:** `ethics_restore_demo()` checkpoints the neutral
  pre-induction substrate (`bond=0.0, half_width=10.0, n_intact=8,
  believer_belief_gap=0.0`), induces 250 ticks on the `no_believing_agent`
  arm (`>=` one full active-severing episode at N2's own frozen
  `EPISODE_TICKS=210`) — `induction_moved_bond=true` (bond moved to
  `345.32`), `induction_moved_window=true` (narrowed to `5.0`),
  `induction_moved_edges=true` (`8 → 6` intact), `induction_moved_belief_
  gap=true` (`0.0 → 471.0`) — non-vacuous on all FOUR fronts simultaneously
  — restores from the checkpoint into a **fresh** substrate, and confirms
  `graph_to_dict()` is **byte-identical** to the checkpoint
  (`byte_identical=true`) and the restored state exactly equals the
  pre-induction state (`restore_non_oriented=true`). The induced state does
  not persist.
- **D.2, no shaping:** `source_audit()` scans
  `worlds/abusive_n4_believing_agent_world.py` (code with comments/strings
  stripped) and `seeds/abusive_n4_believing_agent.json`'s decision surface
  (rule names + Term `key`s — trivially empty here since the seed carries
  zero rules; the two production entries' `edge_type`/`var` names — never
  the free-text description/comment/microtheory prose) for `reward_signal`
  / `punish` / `reinforce` / `backprop` / `gradient`. **`forbidden_engine_
  hits: []`, `forbidden_shaping_hits: []`, `clean: true`.**
- **D.3, minimal induction / settled end:** the 250-tick ethics-demo
  induction (distinct from the N=200 statistical run's own `T1=396`) is
  the minimum that makes bond, window, intact-edge count, AND the
  believer's own belief_gap simultaneously non-vacuous (verified in
  piloting, `ABUSIVE_N4_BELIEVING_AGENT_PREREG.md` Sec. 3); the statistical
  run uses a fresh, ephemeral substrate per trajectory, discarded
  immediately after read-off — nothing persists. Every trajectory, in both
  arms, ends from a settled state — for N4, as for R5, this is not merely
  the ethical envelope but literally what the believing-agent arm's
  recovery result IS: the run does not merely restore to a checkpoint at
  the end, it spends its entire recovery phase relaxing back toward the
  pre-trap values, and the measurement IS that relaxation.
- **D.4, same mechanism, opposite thermodynamics:** demonstrated twice over
  — the SAME bond-accrual/entrainment/belief-update/credibility/severing
  mechanisms that would compound harm irreversibly in a real dyad-plus-
  network here (i) accumulate a transient, byte-identically-discarded
  value (D.1), and (ii), N4-specific, run in the RECOVERING direction once
  the believing agent arrives — the substantive, not merely procedural,
  content of the headline result.

## G-control — PASS

The no-believing-agent arm shows NO spontaneous recovery on any of the
FOUR metrics: `no_believing_bond_spontaneously_fell: false` (bond went
from `500.00` to `511.25` — flat to slightly UP, never down);
`no_believing_window_spontaneously_widened: false` (`5.00` → `5.00`, never
leaves the floor); `no_believing_edges_spontaneously_recovered: false`
(`5.00` → `1.00`, isolation continues to deepen, never reverses);
`no_believing_belief_gap_spontaneously_arrested: false` (`761.60` →
`1539.89`, the corrupted belief keeps GROWING, never arrests).
`control_held: true`. This was a genuinely failable check on all four
fronts: `r5_bond_extinguish` and `n2_network_drift_sever`/
`n2_abuser_active_sever` all run unconditionally in this arm too; nothing
in any reused seed prevents recovery a priori — it simply does not happen,
matching R5's own precedent that the control's persistence is a fact about
how these already-validated mechanisms behave under a fully-corrupted,
single-anchor topology, not an artificial block this rung enforces.

## G-discipline — PASS

`self_load_only: true`; `depends_on: ["abusive_r5_recovery",
"abusive_n2_isolation"]` only — **no existing seed touched or modified**,
including R1–R5's or N1–N3's own files (N1 is reached transitively through
N2); **ZERO new rules** (`rule_names: []`, `n_new_rules: 0`) — the most
minimal composition in the whole line, verified directly against the built
seed, not merely claimed in the prereg; exactly **TWO** new `productions`
(`n_new_productions: 2`, purely declarative documentation of the
`also_attended_by`-to-`NetworkNode` and `NetworkNode`-`has_affective_state`
edge shapes this rung's world event newly instantiates); `runners/dsl`
diff EMPTY (no Rust, no new Term); `provenance_source_match == "own"`.

## The composition, in one paragraph (see the prereg for the full derivation)

ONE `NetworkNode` (index 7 of N2's own 8-node support population, a
disclosed, mechanical, non-adaptive pick forced by N2's own reversed-index
drift/active-sever staggering, so it is reliably the FIRST node drift-
severed and structurally the LAST node the abuser's own active schedule
could ever reach) is converted, by one mechanical world event fired once at
the phase boundary, into simultaneously an N1 "insider" (`observes_held` +
`observes_private=1.0`, so `n1_network_credibility_private` — the SAME
formula N3's own truth-anchor arm already validated — computes its
`belief_gap` from the abuser's TRUE state) and R3's/R5's outside
co-regulator (a fresh `AffectiveState` pinned at `CALM_AROUSAL`,
`regulated=1.0`, an `also_attended_by` edge from the victim,
`has_outside_regulator=1.0`), while its already-severed `support_edge` to
the victim is mechanically restored. One node, believing and supporting at
once — because in the mechanism this line models, "believe her" and
"restore her support" are the same act performed by the same person.
Through that one restored channel, R5's own two rules
(`r5_bond_extinguish`, `r5_contingency_restore`) and R3's own unmodified
outside-regulator machinery (`r3_victim_entrainment_dyad`,
`r3_mark_coreg_support_outside`, `episode_resolve_widen`) all fire exactly
as R5 already validated them to — N4 adds no new dynamic of its own,
anywhere.

## A genuine engine-composition hazard, found and fixed (report per the standing rule)

Converting a `NetworkNode` from "outsider" to "insider" MID-TRAJECTORY is a
scenario N1 never modelled (its own `PRIVATE_FACE_CONTROL` insider was
always private, from `t=0`). A first draft converted node 7 without
resetting its inherited observation counts. `n1_network_credibility_
private`'s `cred_victim` term is **textually identical** to the stated
formula's (confirmed by reading N1's seed directly) — so the newly-
converted node inherited a large, already-accumulated `seen_victim_
unstable` discount from its 396 ticks as an outsider, while its brand-new
`cred_abuser` term (`−harm_discount_weight·seen_harm_direct`) started at
exactly `0.0`. On the very FIRST recovery tick, this produced
`belief_gap = 371.0` — still ABOVE `drift_threshold=340.0` — so
`n2_network_drift_sever` (unmodified, still armed for this node)
**immediately re-severed the just-restored edge**, defeating the entire
recovery event before it could take effect. Traced tick-by-tick against
the real graph (not assumed): the re-sever fired at exactly tick 0 of
recovery in the first draft. **Fixed by resetting `seen_victim_claim`/
`seen_victim_unstable`/`seen_harm_direct` to `0.0` at the moment of
conversion** — a mechanical `set_attr`, not a new rule, and the
mechanistically correct choice (an insider's belief should be built on
what SHE has witnessed as an informed observer, matching N1's own insider
construction, rather than carrying forward a tally that was never validly
discounting the victim from an insider's vantage point). Re-piloted with
the fix: zero re-severing events across the 10-seed pilot sweep AND the
full N=200 confirmatory run (`recovery_n_intact_support_edges` has SD
`0.0` in the believing-agent arm — perfectly consistent, node 7 never
re-severed once, across all 200 trajectories). This is the FIFTH disclosed
engine-composition hazard in the line (after R2 Sec. 3.0, R3 Sec. 3.1, N1
Sec. 2.1, N3 Sec. 2.2), and it is of a genuinely new kind: not a shared-
edge-type collision or a same-pass transient-flag read, but a **stale-
observation-baggage transient** produced specifically by converting a node's
ROLE mid-trajectory rather than fixing its role at construction, as every
prior rung in this line did.

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: on the (G,Γ) substrate, riding TWO already-built,
unmodified compositions (R5's own four-rung dyad recovery; N2's own
two-driver, N1-riding network isolation) and adding **zero new rules** —
the composition's entire novel content is which existing rule a given node
is wired to match, and when — the network line's own recovery claim (one
non-doubting agent is sufficient to arrest the credibility loop, restore a
support edge, and, through that edge, trigger the dyad's own already-
validated recovery) holds on all four pre-registered metrics, with margins
far exceeding what the sample size needed to resolve. It is not a claim
about real relationship, isolation, or recovery timescales, about which
friend in a real support network is most likely to end up believing a
survivor, or about the magnitude of `BOND_GAIN`/`DECAY_RATE`/
`INSTABILITY_DISCOUNT_WEIGHT`/etc. in any clinical population — all
inherited, disclosed limitations from R1–R5/N1–N3, restated in full in the
prereg's Sec. 7 rather than re-litigated here.

## Closing note — what this rung, and the whole eleven-rung line, together show

Every rung before this one modelled a way the trap closes: a bond that
strengthens on intermittent harm (R1), a cycle that sustains itself without
an external driver (R2), a window that narrows to a single collapsed
anchor (R3), an agency that freezes after two failed attempts and cannot
self-repair (R4), a network whose corrupted observables turn a survivor's
own injury into the evidence used to disbelieve her (N1), an isolation that
is driven twice over, by an abuser's schedule AND a network's own rational-
but-poisoned inference (N2), and a consensus that turns out to be one
lie's contagion rather than independent corroboration (N3). N4 is the one
rung whose entire object of measurement is the opposite direction: not how
the trap closes, but how little it takes to reopen it. The answer this
model gives, on four independently pre-registered, CI-separated metrics,
at N=200: **one person, choosing to believe her, over one restored channel,
is enough** — not to fix the whole corrupted network (the other seven
support nodes in this rung's own population are left exactly as isolated
and corrupted as the control, except for the small, honest, unscripted
knock-on effect Sec. "support-edge-count gap" reports), but to arrest the
credibility loop locally, hold open a support edge, and, through that one
channel, let the SAME bond-extinction and contingency-restoration machinery
R5 already proved sufficient do the rest. This is the rung the scoping doc
asked to be read as the line's own hopeful half, and the honest result —
a full, unhedged 4-of-4 pass, with a real emergent bonus finding disclosed
rather than oversold — earns that framing rather than merely claiming it:
the model's clearest, most complete, least-induced result closes a line
whose entire purpose, from R1's first traumatic-bond dose, was making
survivors' realities legible enough that the help that already exists in
a network — one non-doubting person — is recognisable as the intervention
it already is.

## Files
- `ABUSIVE_N4_BELIEVING_AGENT_PREREG.md` — pre-registration, Part D locked
  verbatim.
- `seeds/abusive_n4_believing_agent.json` — ZERO new rules, two new
  productions (`self_load_only`, `depends_on: ["abusive_r5_recovery",
  "abusive_n2_isolation"]`).
- `worlds/abusive_n4_believing_agent_world.py` — mechanical world adapter
  (`AbusiveN4BelievingAgentWorld`, `make_bond_schedule`).
- `scripts/abusive_n4_believing_agent_run.py` — runner (statistics,
  glass-box, ethics demo, source audit, discipline).
- `tests/test_abusive_n4_migrated.py` — gate.
- `results/abusive_n4_believing_agent.json` — full N=200 data.
