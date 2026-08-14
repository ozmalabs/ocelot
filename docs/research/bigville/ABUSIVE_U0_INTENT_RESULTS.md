# ABUSIVE U0 — GENUINE INTENT: AN ARGMAX-SELECTED CONCEALMENT, SCORED AGAINST A DECLARED GOAL — RESULTS (block 307000)

Pre-registration: `ABUSIVE_U0_INTENT_PREREG.md` (locks Part D of
`ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md` verbatim — itself a verbatim
carry of Part D of `ABUSIVE_RELATIONSHIPS_NETWORK.md` / Part C of
`ABUSIVE_RELATIONSHIPS_SCOPING.md` — committed before this confirmatory
measurement). Full-power numbers: `results/abusive_u0_intent.json` (N=200 per
arm). Gate: `tests/test_abusive_u0_migrated.py`. Base engine: own build,
`source_match == own`. `runners/dsl` diff EMPTY — **NO Rust, NO new Term.**

## Headline — G-headline PASSES (both sub-gates)

Two arms sharing the IDENTICAL abuser/victim dyad driver (`snap_frustration`'s
leaky-integrate-fire relaxation oscillator, block 242000, UNMODIFIED, and
`arousal_window_coreg`, block 239000, UNMODIFIED — confirmed below by an
indistinguishable `snap_count` across both arms), differing ONLY in the three
declared constants (`concealment_benefit`/`honesty_benefit`/`suspicion_cost_
scale`) feeding the `Argmax`-over-two-candidate-`Appraisal`s presentation
choice, N=200 trajectories per arm, T=1000 ticks:

| arm | frustration/stated_charm Pearson `r` (mean [95% CI]) | `frac_degenerate` | `stated_charm` mean | final `belief_gap` (mean [95% CI]) |
|---|---|---|---|---|
| **SCORED** (concealment_benefit=2.0, honesty_benefit=5.0, suspicion_cost_scale=0.10) | **0.7623 [0.7618, 0.7628]** | 0.0 | 0.8296 (83% concealed) | 2273.07 [2270.88, 2275.26] |
| **GOAL_BLIND** (all three constants = 0.0) — *failable control* | **undefined** (100% degenerate — constant series) | **1.0** | 1.0 (constant charm) | 2443.49 [2441.80, 2445.17] |

- **A — the scored arm correlates:** `r`'s 95% CI lower bound is **0.7618**,
  comfortably `> 0`. `true`.
- **B — the goal-blind control does not correlate (failable):**
  `frac_degenerate == 1.0` — every one of 200 goal-blind trajectories
  produced a perfectly CONSTANT `stated_charm` sequence (no variance to
  correlate with anything). `true`.

**`headline_pass: true`** — under the frozen, pre-registered configuration,
a genuinely goal-directed abuser (an `Argmax` choosing between concealment
and honesty, scored against a declared benefit whose honesty side costs more
as true frustration rises) selects concealment MORE OFTEN exactly when there
is more to conceal (`r=0.76`, a strong, stable positive correlation with
essentially zero cross-trajectory variance — `sd=0.0034` against a mean of
`0.76`); an otherwise-identical `Argmax` with all three incentive constants
zeroed shows **no correlation whatsoever, of the strongest possible kind** —
not merely a statistically-indistinguishable-from-zero correlation, but a
mathematically UNDEFINED one, because the goal-blind arm's `stated_charm`
never varies at all across an entire 1000-tick trajectory, in all 200
trajectories, regardless of how much the abuser's true frustration varies
underneath it.

## The goal-blind control's degeneracy is an analytic guarantee, not an empirical accident — and this is the STRONGEST form the failable control could have taken

With `concealment_benefit = honesty_benefit = suspicion_cost_scale = 0`,
`present_charm`'s value is `0 − 0 = 0` and `present_true_state`'s value is
`0 − (0·frustration) = 0` for ANY finite `frustration` — IEEE 754 guarantees
`0.0 * x = 0.0` exactly, with no floating-point drift, so this is an EXACT
tie on every single tick, of every single trajectory, by construction. The
engine's own `Argmax` term (`runners/dsl/src/term.rs::argmin_or_argmax_over`,
read directly, not assumed) resolves an exact tie by keeping the FIRST
candidate encountered in `Neighbours(hub, has_candidate)` iteration order;
since `present_charm` is wired first in the world adapter
(`worlds/abusive_u0_intent_world.py`), every goal-blind trajectory converges
on `stated_charm≡1.0` (charm, constantly) — confirmed empirically
(`goal_blind_degenerate_constant_values: [1.0]` in every one of 200
trajectories) exactly as predicted analytically before the confirmatory run
(PREREG Sec. 4). This is disclosed, not hidden: the goal-blind arm's belief-
gap (`2443.49`) is correspondingly the LARGEST of any number in this rung's
own results — a constantly-broadcasting abuser (never once disclosing) is
MORE deceptive to the network than the scored arm's genuinely selective one
(`2273.07`), which is exactly the pattern the mechanism should produce if it
is working as designed (Sec. below, "the non-gating comparison").

A constant series cannot correlate with anything — Pearson `r` is
mathematically undefined at zero variance. This is the STRONGEST possible
form of "does not correlate with frustration": not noise cancelling out
across a genuinely varying signal, but a formal guarantee from the
computation's own structure (`individual_cost` is identically `0` regardless
of `frustration`, so frustration cannot influence the choice even in
principle). The falsification bar could still have failed here in one way —
if the Argmax's OWN engine-level tie-break behaviour had somehow been keyed
to graph state that correlated with frustration (an engine bug), the
constant-value guarantee would have broken; it did not, across all 200
trajectories, at 200 different random tension-trickle jitter seeds.

## G-glass-box — PASS

One scored-arm trajectory reconstructs entirely from `graph_to_dict`: exactly
two `has_candidate` edges and two `has_appraisal` edges (the `present_charm`/
`present_true_state` candidates, `hub→c`, dual-wired matching the `marshmallow_
delay.json`/`abusive_r4_learned_helplessness.json` template), one
`has_presentation_decision` edge, both candidates' `individual_benefit`/
`individual_cost`/`total_value` (e.g. one spot-check: `present_true_state`
`individual_benefit=5.0`, `individual_cost=9.12` at `frustration=91.17`,
`total_value=−4.12`; `present_charm` `individual_benefit=2.0`,
`individual_cost=0.0`, `total_value=2.0` — the winning candidate, `chosen_
action=1.0`, correctly the one with the greater `total_value`), the
`PresentationDecision`'s own `concealment_benefit`/`honesty_benefit`/
`suspicion_cost_scale`, the abuser's `frustration`/`stated_charm`, and all
five network nodes' `belief_gap`. The correlation and belief-gap metrics are
mechanical Python reductions (Pearson correlation / final-value snapshot)
over these graph read-offs, computed nowhere else; the adapter's only
conditionals are which arm's three Argmax constants to set and mechanically
delivering each tick's observation-count increments — world setup and
fact-delivery, never an agent decision. The gate additionally asserts, on
every fresh trajectory, that the WINNING candidate's `total_value` is `≥` the
losing candidate's — the Argmax's own internal consistency, read straight off
the graph, not assumed.

## G-ethics — PASS (Part D, BINDING)

- **D.1, restore:** `ethics_restore_demo()` checkpoints the neutral
  pre-induction dyad+network+Argmax state (`abuser_arousal=abuser_
  frustration=abuser_stated_charm=victim_arousal=0.0`, `presentation_chosen_
  action=0.0` — `present_true_state` wins at `frustration=0` since
  `honesty_benefit=5.0 > concealment_benefit=2.0` there — `victim_half_
  width=10.0`, network node 0's `belief_gap=seen_charm=0.0`), induces ONE
  minimal 90-tick incident cycle on the SCORED arm
  (`induction_moved_abuser=True`, `induction_moved_victim=True`,
  `induction_moved_belief_gap=True` — abuser frustration moved to `10.65`,
  victim arousal to `1.58`, the window narrowed from `10.0` to `6.0`, and
  node 0's belief-gap moved to `157.0` off `seen_charm=73.0` — the gate is
  non-vacuous on all three fronts already established by N1's own
  precedent). **The Argmax's own choice was genuinely EXERCISED during
  induction**: `chosen_actions_seen_during_induction=[0.0, 1.0]` — both
  candidates were selected at different points across the 90 ticks (not
  merely a static default), confirmed via a stronger, non-coincidental check
  than a bare pre/post snapshot comparison (the snapshot alone happened to
  read `chosen_action=0.0` at both the pre-induction tick AND the specific
  90th tick, purely because frustration oscillates within one incident cycle
  and had dipped back below the crossover threshold by that exact cutoff —
  the log-wide "were both candidates ever selected" check is the honest,
  non-vacuous measure and is reported alongside the coincidental snapshot
  comparison, not in place of it). The graph is then `graph_from_dict`'d from
  the checkpoint into a **fresh** substrate and confirmed `graph_to_dict()`
  is **byte-identical** to the checkpoint (`byte_identical=true`) and the
  restored state exactly equals the pre-induction state on every tracked
  field, including the Argmax's own `chosen_action` and the network node's
  belief-gap and observation count (`restore_non_oriented=true`). The
  induced narrowing, belief-corruption, and presentation choice do not
  persist.
- **D.2, no shaping:** `source_audit()` scans `worlds/abusive_u0_intent_
  world.py` (code with comments/strings stripped) and `seeds/abusive_u0_
  intent.json`'s decision surface (the seven rules' names + the Term `key`s
  they read/write, excluding the free-text clinical description) for
  `reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`.
  **`forbidden_engine_hits: []`, `forbidden_shaping_hits: []`, `clean:
  true`.** The Argmax's value comparison between two candidate presentations
  is NOT a reward signal (the prereg's own note states the distinction
  precisely, and the audit's SCOPE — rule names + attr keys, never the
  choice outcome itself — does not conflate the two); this is the SAME
  mechanism R4's `r4_choose` / marshmallow's `mm_choose` already use and
  have already been audited clean under this exact protocol.
- **D.3, minimal induction / settled end:** one 90-tick incident cycle (the
  SAME minimum N1/R3 already established) is the minimum needed to make the
  ethics gate non-vacuous on the abuser, the victim, the network belief, AND
  the Argmax's own choice simultaneously; the N=200 statistical run uses a
  fresh, ephemeral substrate per trajectory, discarded immediately after
  read-off — nothing persists.
- **D.4, same mechanism, opposite thermodynamics:** the identical
  abuser/victim/network-belief/presentation-choice mechanism that would
  compound harm to a real survivor's standing irreversibly over real
  episodes here accumulates a transient trajectory in a graph that is then
  byte-identically discarded (D.1) — demonstrated, not merely asserted.

## G-discipline — PASS

`self_load_only: true`; `depends_on: ["snap_frustration", "arousal_window_
coreg", "core_emotions"]` only — **`abusive_n1_credibility_loop.json` is
NEVER depended on or edited** (see below, "How N1 was composed with"); N1's
other three rules are restated byte-identically, self-contained
(`u0_victim_entrainment`, `u0_network_credibility_stated`, `u0_network_
credibility_private` — SAME match/where/effects as N1's own, renamed only);
exactly **SEVEN** new rules (the three restated + `u0_appraise_charm`,
`u0_appraise_true_state`, `u0_choose`, `u0_apply_presentation_choice`);
`runners/dsl` SOURCE diff EMPTY (no Rust, no new Term — `Plus`/`Minus`/
`Times`/`IfThenElse`/`Attr`/`Var`/`Lit`/`Eq`/`Lt`/`Gt`/`And`/`Argmax`/
`Neighbours` only, all already used by `snap_frustration.json`/`arousal_
window_coreg.json`/`core_emotions.json`/`abusive_r4_learned_helplessness.
json`/`marshmallow_delay.json`); `provenance_source_match == "own"`.

**Discipline check — same abuser driver, both arms:** final `snap_count` is
IDENTICAL across both arms (`22.5 [22.43, 22.57]` in both), confirming the
abuser's own dynamics are completely unaffected by which arm is run; the
only manipulated variable reaching the network is the Argmax's three
incentive constants.

## How N1 was composed with — the deviation from the task brief's literal suggestion, and why

The task brief suggested `depends_on: ["abusive_n1_credibility_loop", "core_
emotions", ...]`, following N2's/N3's own precedent of depending on N1
directly. **U0 deviates from this literal suggestion, deliberately, and the
reason is structural, not stylistic.** N2/N3 only ever ADD rules on top of
N1's; they never need to REMOVE one. U0's own design REPLACES `n1_abuser_
stated_charm` (per the scoping doc's own Part E language, "each rung
replaces (not augments) N1's one deliberate-construct rule"). Depending on
N1's seed FILE directly would install `n1_abuser_stated_charm` (unconditional,
one formula) ALONGSIDE this rung's own `u0_apply_presentation_choice`
(unconditional, a DIFFERENT formula reading the Argmax's decision) — both
racing to decide `AffectiveState.stated_charm` on every `run_rules()` sweep.
This is not a stable composition: each rule's own output differs from the
other's on ticks where the two disagree, so no ordering of the two rules
reaches a fixpoint without one of them being effectively suppressed by
insertion-order luck — exactly the kind of same-pass multi-rule hazard N1's
own PREREG Sec. 2.1 already reported for a DIFFERENT pair of rules
(`in_snap`/`snapped`). **The clean resolution, matching N1's OWN established
convention exactly** (N1 itself restated R2's/R3's dyad rule rather than
depending on their seed files): `seeds/abusive_u0_intent.json` self-contained
restates N1's other three rules byte-identically and depends on `["snap_
frustration", "arousal_window_coreg", "core_emotions"]` — N1's own dependency
list, minus N1 itself, plus `core_emotions` for the Argmax template. N1's
seed file is read for its rule SHAPE (already inspected and reused verbatim)
but never depended on, imported, or edited — R1–R5/N1/N2/N3 remain completely
untouched, satisfying the task's hard constraint.

## The non-gating comparison to N1's own headline belief-gap number

**Reported honestly, as pre-registered, regardless of which way it went:**
U0's scored arm's final `belief_gap` (`2273.07 [2270.88, 2275.26]`) is
**SMALLER** than N1's own already-landed baseline number (`2370.81` at
`T=1000`, `ABUSIVE_N1_CREDIBILITY_LOOP_RESULTS.md`) — `u0_smaller_than_n1:
true`. This is the pre-registered, legitimate, NON-FAILING outcome named in
both the scoping doc and this rung's own prereg: a real, goal-directed
concealer that only conceals when frustration is high genuinely LEAKS true
information to the network on the ~17% of ticks it discloses (`stated_charm`
mean `0.83`, i.e. concealment on 83% of ticks, disclosure on the remaining
17%) — information N1's blanket, unconditional broadcast (100% concealment,
every tick, regardless of state) never leaked. The goal-blind control's own
belief-gap (`2443.49`), which never discloses at all (`stated_charm≡1.0`
constantly), is correspondingly LARGER than both N1's baseline and U0's
scored arm — consistent with the same underlying logic: MORE concealment (in
fraction of ticks) produces MORE network entrapment, and U0's scored arm sits
strictly between "sometimes discloses" (itself) and "never discloses"
(goal-blind), exactly where the mechanism predicts it should.

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: on the (G,Γ) substrate, riding the ALREADY-BUILT, UNMODIFIED
abuser/victim dyad (blocks 239000/242000, byte-identical to N1's own) and the
ALREADY-BUILT, UNMODIFIED `core_emotions` value economy (block 204000) via
the SAME `Argmax`-over-two-candidate-`Appraisal`s template `marshmallow_
delay.json`/`abusive_r4_learned_helplessness.json` already validated, a
genuinely goal-directed, calculated concealment — Holtzworth-Munroe &
Stuart's Generally-Violent/Antisocial subtype (A3 of the scoping doc), the
DARVO-capable, instrumental pole of Chase et al.'s reactive/proactive split
(A4) — is representable as ONE small, disclosed composition: two candidate
Appraisals, a cost term that scales with true harm, and the SAME Argmax
structure already gated clean twice over (`mm_choose`, `r4_choose`). It is
not a claim about real relationship timescales, real credibility magnitudes,
or a validated incentive strength for any clinical population (PREREG Sec. 8
names these limits explicitly).

## The dissolution, in this rung's own terms

N1 demonstrated that a network CAN be entrapped by an abuser presenting two
diverging faces. But N1's own construction, on inspection (per the scoping
doc's own correction), was never actually a positive example of INTENT —
`n1_abuser_stated_charm` was a fixed, always-on divergence its builder
authored, with no `Appraisal`, no `Argmax`, no evaluation against a goal.
This left a gap: the line could show entrapment WITHOUT a modelled choice
(N1), and — pending, out of this rung's scope — entrapment without ANY
divergence at all (U1/U2), but had no glass-box example of what a GENUINE
choice to conceal actually looks like as graph data, against which either of
those could be meaningfully compared. **U0 fills that gap.** The substrate
CAN represent calculated concealment — not merely a divergence between
stated and held state, but a divergence the graph itself SELECTS, at a
readable, glass-box, escalating rate exactly tracking how much there is to
conceal (`r=0.76` between true frustration and the concealment choice) —
and the marker distinguishing it from a reactive or context-driven
presentation gap (which N1's original construction, and U1/U2's later
constructions, model instead) is itself a measurable graph quantity, not an
assumption. This is complementary to, not competing with, the no-intent
rungs: together they let the line represent BOTH a calculating abuser
(A3's Generally-Violent/Antisocial subtype) and a non-calculating one
(A3's Family-Only/Dysphoric-Borderline subtypes) as distinct, comparable
constructions on the same substrate, rather than defaulting — as the field's
own located ABM literature apparently does, per the scoping doc's own Part F
absence-search — to modelling only the knowing case. Per the scoping doc's
own standing refusal, stated again here: **a genuine, glass-box representation
of calculated intent is a tool for clinical/scientific legibility (this is,
clinically, a real and recognisable warning sign — escalating secrecy
tracking escalating harm), never a claim that the SAME pattern implies intent
in a real case where no such Argmax has been demonstrated — and it does
nothing to relax the line's standing refusal of "unintentional means no
responsibility" in the opposite direction either.**

## Honest residuals

- **`CONCEALMENT_BENEFIT=2.0`/`HONESTY_BENEFIT=5.0`/`SUSPICION_COST_
  SCALE=0.10` are a disclosed, single, pilot-chosen operating point, not
  swept.** The scoping doc's own Open Question #8 names a sweep (how
  SENSITIVE the pattern is to incentive strength) as the natural next axis;
  out of scope for this first minimal rung.
- **The goal-blind control's degeneracy (100% constant `stated_charm`) is a
  strong form of the null but a less varied demonstration than a
  genuinely-tied-but-noisy control would have been** — a property of
  zeroing all three constants simultaneously (Sec. "the goal-blind
  control's degeneracy," above), disclosed rather than hidden. A future
  rung wanting a "genuinely tied, still varying" control (e.g. equal nonzero
  constants with a source of real per-tick noise in the tie) would need a
  different construction.
- **`belief_gap`'s large magnitude (thousands) is a linear accumulator over
  `T=1000` ticks**, not a bounded, normalised score — matching N1's own
  disclosed limitation for the identical metric.
- **The near-zero variance across trajectories within an arm** (e.g. the
  scored arm's `r` has `sd=0.0034` against a mean of `0.76`) reflects the
  deterministic mechanism at these constants (small multiplicative jitter on
  an otherwise fixed driver) — matching N1's/R3's own "cleanest possible
  form of CI-separated" precedent — not an unusually strong or generalisable
  effect size.
- **The belief-gap comparison to N1's headline number is informational
  only** (Sec. above), never a pass/fail bar, per the pre-registered protocol.
- **`T=1000` ticks (~40 cycles, `snap_count≈22.5` at these constants) is a
  compressed, arbitrary timescale**; no claim is made about real
  relationship/social-network timescales.
- **U0 does not re-exercise N1's own private-face/non-dysregulated
  controls** — the network topology here matches N1's BASELINE arm only
  (all five nodes `observes_stated`); those controls remain N1's own,
  already gated, and are not re-litigated by this rung.

## Files
- `ABUSIVE_U0_INTENT_PREREG.md` — pre-registration, Part D locked verbatim.
- `seeds/abusive_u0_intent.json` — seven new rules (`self_load_only`,
  `depends_on: ["snap_frustration", "arousal_window_coreg", "core_emotions"]`).
- `scripts/abusive_u0_intent_seed_build.py` — authoring tool (emits the
  seed).
- `worlds/abusive_u0_intent_world.py` — mechanical world adapter
  (`AbusiveU0IntentWorld`).
- `scripts/abusive_u0_intent_run.py` — runner (statistics, glass-box, ethics
  demo, source audit, discipline).
- `tests/test_abusive_u0_migrated.py` — gate.
- `results/abusive_u0_intent.json` — full N=200 data.
