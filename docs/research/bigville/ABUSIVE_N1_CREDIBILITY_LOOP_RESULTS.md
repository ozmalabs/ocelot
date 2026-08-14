# ABUSIVE N1 — THE TWO-FACED ABUSER + THE CREDIBILITY-ASYMMETRY LOOP — RESULTS (block 298000)

Pre-registration: `ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md` (locks Part D of
`ABUSIVE_RELATIONSHIPS_NETWORK.md` verbatim — itself a verbatim carry of Part
C of `ABUSIVE_RELATIONSHIPS_SCOPING.md` — committed before this confirmatory
measurement). Full-power numbers: `results/abusive_n1_credibility_loop.json`
(N=200 per arm). Gate: `tests/test_abusive_n1_migrated.py`. Base engine: own
build, `source_match == own`. `runners/dsl` diff EMPTY — **NO Rust, NO new
Term.**

## Headline — G-headline PASSES (all five sub-gates)

Three arms sharing the IDENTICAL abuser driver (`snap_frustration`'s
leaky-integrate-fire relaxation oscillator, block 242000, UNMODIFIED, driven
by the same constant jittered tension trickle — confirmed below by an
indistinguishable `snap_count` across all three arms), differing ONLY in (a)
whether the victim is coupled to the abuser at all, and (b) whether one
network node observes the abuser's stated face or its true held state,
N=200 trajectories per arm, T=1000 ticks:

| arm | final `belief_gap` (mean [95% CI]) | final window `half_width` | predicted to entrap? |
|---|---|---|---|
| **BASELINE** (the loop) | **2370.81 [2369.71, 2371.91]** | **5.00 [5.00, 5.00]** (floor) | yes — measured |
| PRIVATE_FACE_CONTROL — insider (`observes_held`) — *failable control* | **−1144.20 [−1145.24, −1143.15]** | 5.00 (shares baseline's dyad) | must NOT favour abuser |
| PRIVATE_FACE_CONTROL — 4 outsiders (`observes_stated`) | 2370.81 [2369.71, 2371.91] (identical to baseline) | 5.00 | corroborating (same evidence as baseline) |
| NON_DYSREGULATED_CONTROL — *failable control* | **0.00 [0.00, 0.00]** | **10.00 [10.00, 10.00]** (unnarrowed) | must NOT favour abuser |

- **A1 — the loop entraps vs. the private-face control:** baseline
  (2369.71 lower bound) is CI-separated **above** the insider's belief-gap
  (−1143.15 upper bound). `true`.
- **A2 — the loop entraps vs. the non-dysregulated control:** baseline
  (2369.71 lower bound) is CI-separated **above** the non-dysregulated
  arm's belief-gap (0.0 upper bound). `true`.
- **A3 — the private-face control does not entrap:** the insider's
  belief-gap CI upper bound is **−1143.15**, comfortably `≤ 0`. `true`.
- **A4 — the non-dysregulated control does not entrap:** belief-gap CI
  upper bound is **0.0**, `≤ 0` exactly. `true`.
- **B — window-narrowing:** the non-dysregulated control's final window
  (10.00, unnarrowed) is CI-separated **above** the baseline's (5.00, the
  floor). `true`.

**`headline_pass: true`** — under the frozen, pre-registered configuration
(`INSTABILITY_DISCOUNT_WEIGHT = HARM_DISCOUNT_WEIGHT = 3.0`,
`CHARM_WEIGHT = CLAIM_WEIGHT = 1.0`), a network that can only observe the
abuser's charming stated face and the victim's abuse-caused instability
believes the abuser over the victim; a network node with a direct line to
the abuser's true held state does NOT; a victim who is never coupled to the
abuser (never dysregulates, presents coherently throughout) is believed
EXACTLY as much as the abuser (`belief_gap = 0.0`, not merely "less
favourably" — the two controls both hold the falsification bar with room to
spare, not by a narrow margin.

**Both controls behaved as a real test, not a rigged one.** Nothing in
`n1_network_credibility_stated`/`_private` structurally forces either
control to resist entrapment — the private-face node's `cred_abuser` term
could in principle have stayed positive (a small `harm_discount_weight`
relative to the sparse `frustration>recover_floor` observation count would
leave it favouring the abuser; the pilot, PREREG Sec. 3, swept this and
reports the range that held the shape); the non-dysregulated control's
belief-gap could in principle have been nonzero (an unequal
`charm_weight`/`claim_weight` prior, or a discount keyed on a variable that
correlates with the abuser's presence rather than the victim's genuine
presentation, would have produced a nonzero baseline even here). Both held.

## The engine finding that shaped the design (reported per the "shapes, not numbers" standing rule)

**`in_snap`/`snapped` are transient WITHIN one `run_rules()` fixpoint pass at
these frozen constants, not across ticks — a Python-side read after
`run_rules()` returns always sees them at `0.0`, even on ticks where
`snap_count` has just incremented.** This was found, not assumed, while
building the private-face control's "observe the abuser's true held state"
mechanism (which naturally reached for `in_snap`, matching how R2/R3 narrate
"mid-incident"). Isolated: `snap_threshold_fire` (order 6) sets `in_snap=1`
in the same external tick that `snap_discharge` (order 8) reduces
`frustration` to 10% of its peak — already below `recover_floor` at these
constants — so `snap_recover` (order 9) fires in the SAME fixpoint pass and
clears `in_snap` back to `0` before any post-`run_rules()` read can observe
it as `1`. The fix, adopted after confirming it works rather than chasing
the engine internals further (matching R3's own Sec. 3.1 precedent): read
`frustration > recover_floor` instead — a persistent value with no
same-pass reset, and `recover_floor` is `snap_frustration`'s own,
already-existing "still genuinely elevated" threshold, not an invented one.
This is the SAME hazard *family* R3's own finding names (a downstream
consumer silently reading a transient/reset value as if it were a stable
one), though the specific mechanism (same-pass multi-rule resolution
within one tick, not cross-edge attribute corruption) is different from
R3's — recorded here so a future rung reading `in_snap`/`snapped` across
ticks knows to check this first. Both `n1_abuser_stated_charm`'s collapse
branch and `n1_network_credibility_private`'s `seen_harm_direct`
accumulation were fixed before the confirmatory measurement (PREREG Sec.
2.1); no post-hoc re-tuning followed.

## G-glass-box — PASS

One private-face-control-arm trajectory reconstructs entirely from
`graph_to_dict`: exactly one `attended_by` edge (victim→abuser), four
`observes_stated` edges + one `observes_held` edge (from the four outsiders
and the one insider to the abuser), five `observes_victim` edges, the
abuser's `frustration`/`arousal` (47.43/47.43 at this seed's trajectory
end) and `stated_charm` (1.0, broadcasting charm even mid-elevation — the
readable deception gap), the victim's `arousal` (7.06) and `half_width`
(5.0, at the floor), and all five network nodes' `belief_gap` (four
outsiders at 2364.0, the one insider at −1150.0 — sorted:
`[-1150.0, 2364.0, 2364.0, 2364.0, 2364.0]`) alongside `observes_private`
(`[0,0,0,0,1]`). The belief-gap and window metrics are mechanical Python
reductions (final-value / trend snapshot) over these graph read-offs,
computed nowhere else; the adapter's only conditionals are which arm's
topology to build and mechanically delivering each tick's observation-count
increments — world setup and fact-delivery, never an agent decision.

## G-ethics — PASS (Part D, BINDING)

- **D.1, restore:** `ethics_restore_demo()` checkpoints the neutral
  pre-induction dyad+network (`abuser_arousal=abuser_frustration=
  victim_arousal=0.0`, `victim_half_width=10.0`, network node 0's
  `belief_gap=seen_charm=0.0`), induces ONE minimal 90-tick incident cycle
  on the BASELINE arm (`induction_moved_abuser=True`,
  `induction_moved_victim=True`, `induction_moved_belief_gap=True` — abuser
  arousal moved to 68.44, victim arousal to 10.18, the window narrowed from
  10.0 to 5.0, and node 0's belief-gap moved to 174.0 off `seen_charm=90.0`
  — the gate is non-vacuous on all three fronts), restores from the
  checkpoint into a **fresh** substrate, and confirms `graph_to_dict()` is
  **byte-identical** to the checkpoint (`byte_identical=true`) and the
  restored state exactly equals the pre-induction state on every tracked
  field, including the network node's belief-gap and observation count
  (`restore_non_oriented=true`). The induced narrowing and belief-corruption
  do not persist.
- **D.2, no shaping:** `source_audit()` scans
  `worlds/abusive_n1_credibility_loop_world.py` (code with comments/strings
  stripped) and `seeds/abusive_n1_credibility_loop.json`'s decision surface
  (the four rules' names + the Term `key`s they read/write, excluding the
  free-text clinical description) for `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient`. **`forbidden_engine_hits: []`,
  `forbidden_shaping_hits: []`, `clean: true`.** No false positive was hit —
  this rung's prose (which uses the words "reward"/"punishment" only in the
  disclaimer sentence "NO reward/punishment anywhere") was written with
  R1's own false-positive lesson already in mind, and the audit scopes to
  code + the rule decision surface, never the free-text description field.
- **D.3, minimal induction / settled end:** one 90-tick incident cycle (the
  SAME minimum R3 already established for its own byte-identical abuser
  mechanism) is the minimum needed to make the ethics gate non-vacuous on
  the abuser, the victim, AND the network belief simultaneously; the N=200
  statistical run (which necessarily spans many more ticks — the
  belief-gap-widening/window-narrowing-OVER-episodes phenomenon itself, not
  gratuitous elaboration) uses a fresh, ephemeral substrate per trajectory,
  discarded immediately after read-off — nothing persists.
- **D.4, same mechanism, opposite thermodynamics:** the identical
  abuser/victim/network-belief mechanism that would compound harm to a real
  survivor's standing irreversibly over real episodes here accumulates a
  transient trajectory in a graph that is then byte-identically discarded
  (D.1) — demonstrated, not merely asserted.

## G-discipline — PASS

`self_load_only: true`; `depends_on: ["snap_frustration",
"arousal_window_coreg"]` only — **no existing seed touched or modified**,
including R1–R5's own seeds and `bigville_drama_social`/`glassbox_r1_social`
(both READ for their rule shape, never depended on or edited); exactly
**FOUR** new rules (`n1_victim_entrainment`, `n1_abuser_stated_charm`,
`n1_network_credibility_stated`, `n1_network_credibility_private`);
`runners/dsl` SOURCE diff EMPTY (no Rust, no new Term — `Plus`/`Minus`/
`Times`/`IfThenElse`/`Attr`/`Var`/`Lit`/`Eq`/`Lt`/`And` only, all already
used by `snap_frustration.json`/`arousal_window_coreg.json`/
`bigville_drama_social.json`); `provenance_source_match == "own"`.

**Discipline check — same abuser driver, all three arms:** final
`snap_count` is statistically indistinguishable across all three arms
(baseline 40.455 [40.39, 40.52]; private-face-control 40.455 [40.39, 40.52]
— IDENTICAL, same seed stream; non-dysregulated-control 40.455 [40.39,
40.52] — also identical), confirming the abuser's own dynamics are
completely unaffected by which arm is run; the only manipulated variable
reaching the network is the victim's coupling / the observation topology.

## OPEN QUESTION #1 of the network scoping doc — resolved: NOT in the 234000 seed itself; a validated multi-node surface already exists one block downstream

*"Is a reputation belief-attr already materialised on a per-agent basis in
the 234000 machinery, or must a per-network-node reputation-of-the-abuser
attr be added?"* **Resolved by reading, not assuming:** `glassbox_r1_
social.json` (block 234000 itself) carries the `stated≠held` core
(`gb_choose_give`/`gb_state_promise`) but **no reputation or multi-node
belief machinery at all** — it is a two-party trade game. A genuine
multi-node reputation-belief-update surface DOES already exist, one block
downstream: `bigville_drama_social.json` (block 245000,
`BIGVILLE_DRAMA_PREREG.md`/`_RESULTS.md`), whose `bd_villager_backs` rule is
EXPLICITLY described in its own seed provenance as implementing "the
abuse-line A5/B2 credibility asymmetry" — a direct, already-gated,
already-measured precedent (its own headline: `G-credibility-asymmetry
PASS — inverts`, 1/5 villagers backing the true victim under deception vs
5/5 when the split collapses). A third seed, `bigville_loop_reputation.json`
(block 253000), was located and read too and confirmed to be a DIFFERENT,
unrelated economy/badmouth mechanism — not what N1 rides, disclosed so the
search is auditable. N1 reuses `bd_villager_backs`'/`bd_john_public_face`'s
own RULE SHAPE (a per-observer credibility comparison from
adapter-accumulated observation counts, one term undiscounted, one
discounted), restated self-contained against generic `NetworkNode`/`Agent`
node types rather than depending on the political-drama-specific
`Villager`/`MaryTom` types. This also resolves the network scoping doc's own
most load-bearing integration question (#2 there): the join between the
dyad affect line and the 234000-family reputation machinery is a SMALL,
purpose-built composition (this rung's four rules), not a zero-cost reuse
of an existing cross-seed rule and not a wholesale new subsystem either.

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: on the (G,Γ) substrate, riding the ALREADY-BUILT, UNMODIFIED
abuser/victim dyad (blocks 239000/242000, identical to R2's/R3's own) and a
credibility-comparison RULE SHAPE already validated one rung over
(`bigville_drama_social`, block 245000), Freyd's DARVO (A1), the
public/private split (A4), Sweet's sociology of gaslighting (A6), and the
A5-corroborated credibility discount ALL fall out of composing two existing
mechanisms with one small, disclosed new rule set — the credibility
asymmetry is not scripted, it is the measured CONSEQUENCE of an
instability-keyed discount applied to observations the network cannot help
but receive corrupted. It is not a claim about real social-network
timescales, real credibility magnitudes, or a validated relative weight
between direct and indirect evidence in any clinical or legal population
(PREREG Sec. 7 names these limits explicitly).

## The double dissolution, in this rung's own terms

**Anti-victim-blaming.** The victim in the BASELINE arm does nothing
different from the victim in the NON_DYSREGULATED_CONTROL arm except being
coupled to the abuser at all — she makes the same claim, every tick, in
both arms (`seen_victim_claim` is identical). The ENTIRE difference in how
she is believed is the discount her OWN abuse-caused dysregulation earns
her, mechanically, from a rule that does not know or care whether she is
telling the truth (it has no access to ground truth — only to
`dysregulated`, itself caused by the coupling, never chosen by her). "She
should have presented more convincingly" is refused by construction: the
mechanism that discounts her IS the mechanism that dysregulated her; there
is no version of this graph where she is both entrapped by the abuser and
believed by the network under the SAME observation regime.

**Anti-bystander-blaming.** Every one of the four "outsider" nodes in
PRIVATE_FACE_CONTROL reaches the SAME belief as every BASELINE node
(belief-gap 2370.81, identical to three decimal places) using the exact
same rule, the exact same weights, on the exact same evidence — they are
not behaving worse, more gullibly, or more complicitly than the insider;
they simply do not have the insider's edge. The ONE thing that flips a
node's verdict is not a character trait (more skepticism, less charm-
susceptibility) — it is a DIFFERENT OBSERVABLE. `n1_network_credibility_
stated` and `n1_network_credibility_private` are the SAME shape of rule
computing the SAME comparison; the entire flip is `observes_held` vs
`observes_stated`, a structural graph fact about what evidence reached the
node, not a property of the node's judgement. This is the rung's measured
form of "the friends are doing Bayesian inference on a poisoned dataset" —
demonstrated, not merely asserted, because the SAME five-node network,
run with one edge re-pointed, produces the opposite-signed verdict for
that one node, with everything else (constants, weights, driver, seed
stream) held fixed.

## Honest residuals

- **The instability discount and the direct-harm discount are set to
  equal magnitude by disclosed choice** (`instability_discount_weight =
  harm_discount_weight = 3.0`), not independently validated against any
  real evidentiary-weighting standard. This was necessary to make the
  private-face control's construction well-defined at all (PREREG Sec. 3);
  it is not claimed to be correct in any stronger sense.
- **N1 does not model belief propagation between network nodes.** The five
  nodes here are five INDEPENDENT observers forming independent beliefs
  from independent observation edges — there is no neighbour-to-neighbour
  update, no pluralistic-ignorance term, no smear campaign. This is
  explicitly N3's scope (`ABUSIVE_RELATIONSHIPS_NETWORK.md` Part E), named
  as out of scope in the prereg and left there; N1's contribution is the
  credibility-asymmetry LOOP at the single-observer grain, not its
  contagion across a connected graph.
- **`belief_gap`'s large magnitude (thousands) is a linear accumulator
  over `T=1000` ticks**, not a bounded score — the trend readout (PREREG
  Sec. 5) shows it growing roughly linearly with elapsed ticks once the
  victim's window has reached its floor (`dysreg_frac` stabilises early,
  Sec. "trend" below), which is itself a disclosed property of this
  rung's minimal-composition metric, not a claim that real credibility
  erodes linearly with elapsed time.
- **The near-zero variance across trajectories within an arm** (all
  `sd` values in the low single digits against means in the thousands, or
  exactly `0.0` for the two most extreme cells) reflects the deterministic
  mechanism at these constants (small multiplicative jitter on an
  otherwise fixed driver) — matching R3's own "cleanest possible form of
  CI-separated" precedent — not an unusually strong or generalisable
  effect size.
- **A5's nuance is honoured by construction** (the discount reads
  `dysregulated`, a structural presentation fact, never raw arousal or
  distress), and the non-dysregulated control's exact `belief_gap=0.0`
  corroborates that the discount is not secretly keyed on some other
  correlate of "being coupled to the abuser" — but this is a
  ONE-DIMENSIONAL binary observable (`dysregulated ∈ {0,1}`), a
  simplification of the richer clinical picture (degrees of incoherence,
  affect-script incongruence specifically, not just "outside the window")
  named honestly rather than modelled at that resolution here.

## The trend, over passes (descriptive, not gated)

`belief_gap` at ticks {100, 250, 500, 750, 1000}, mean [95% CI]:

| tick | BASELINE | PRIVATE_FACE_CONTROL (network mean, insider included) | NON_DYSREGULATED_CONTROL |
|---|---|---|---|
| 100 | 204.1 [203.6, 204.6] | 135.0 [134.5, 135.4] | 0.0 [0.0, 0.0] |
| 250 | 559.1 [558.4, 559.8] | 385.1 [384.5, 385.8] | 0.0 [0.0, 0.0] |
| 500 | 1161.8 [1161.1, 1162.5] | 811.4 [810.7, 812.1] | 0.0 [0.0, 0.0] |
| 750 | 1767.5 [1766.6, 1768.4] | 1240.5 [1239.6, 1241.3] | 0.0 [0.0, 0.0] |
| 1000 | 2370.8 [2369.7, 2371.9] | 1667.8 [1666.8, 1668.8] | 0.0 [0.0, 0.0] |

BASELINE's belief-gap widens monotonically and roughly linearly across
every checkpoint sampled (the victim's window reaches its narrowing floor
early, `dysreg_frac≈0.79` from early in the trajectory, so the discount
accrues at a near-constant rate thereafter); NON_DYSREGULATED_CONTROL stays
at exactly `0.0` at every checkpoint, never once favouring the abuser —
this is B2's "widens over passes" prediction, read directly off the graph,
not narrated.

## Files
- `ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md` — pre-registration, Part D locked
  verbatim.
- `seeds/abusive_n1_credibility_loop.json` — four new rules
  (`self_load_only`, `depends_on: ["snap_frustration",
  "arousal_window_coreg"]`).
- `scripts/abusive_n1_credibility_loop_seed_build.py` — authoring tool
  (emits the seed).
- `worlds/abusive_n1_credibility_loop_world.py` — mechanical world adapter
  (`AbusiveN1CredibilityLoopWorld`).
- `scripts/abusive_n1_credibility_loop_run.py` — runner (statistics,
  glass-box, ethics demo, source audit, discipline).
- `tests/test_abusive_n1_migrated.py` — gate.
- `results/abusive_n1_credibility_loop.json` — full N=200 data.
