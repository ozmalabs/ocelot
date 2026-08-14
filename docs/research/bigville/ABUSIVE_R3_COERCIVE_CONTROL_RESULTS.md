# ABUSIVE R3 — COERCIVE CONTROL: window-narrowing + prior-mis-setting + isolation/frontier-collapse — RESULTS (block 289000)

Pre-registration: `ABUSIVE_R3_COERCIVE_CONTROL_PREREG.md` (locks Part C of
`ABUSIVE_RELATIONSHIPS_SCOPING.md` verbatim, committed before this
confirmatory measurement). Full-power numbers: `results/abusive_r3_coercive_control.json`
(N=200 per arm). Gate: `tests/test_abusive_r3_migrated.py` (8/8 green at
N=40). Base engine: own build, `source_match == own`. `runners/dsl` SOURCE
diff EMPTY — **NO Rust, NO new Term** (the compiled `.so` reflects a
pre-existing catch-up rebuild to HEAD's own already-committed Rust source,
unrelated to this rung — see G-discipline below).

## Headline — G-headline PASSES (both sub-gates)

Two arms sharing the IDENTICAL abuser driver (`snap_frustration`'s
leaky-integrate-fire relaxation oscillator, block 242000, UNMODIFIED, driven
by the same constant jittered tension trickle), differing ONLY in whether
the victim's frontier is collapsed to the abuser alone or held open to a
second, fixed-calm, always-regulated outside source, N=200 trajectories per
arm, T=1000 ticks:

| arm | final window `half_width` (mean [95% CI]) | abuser-tracking distance (mean [95% CI]) | final `others_trust`/`self_worth` |
|---|---|---|---|
| **SINGLE_ANCHOR** (frontier collapsed) | **5.00 [5.00, 5.00]** | **48.87 [48.85, 48.89]** | **0.000 / 0.000** |
| OUTSIDE_REGULATOR (frontier open) — *failable control* | **10.00 [10.00, 10.00]** | **54.85 [54.83, 54.87]** | **0.500 / 0.500** |

- **A — window-narrowing:** the outside-regulator arm's final window
  (10.00, at its floor's opposite end — the INITIAL width, never narrowed)
  is CI-separated **above** the single-anchor arm's (5.00, the window's
  floor). `outside_regulator_ci_separated_above_single_anchor: true`. Both
  arms' variance is exactly zero to floating-point precision (every one of
  the 400 trajectories converges to the SAME final width within its arm) —
  the cleanest possible form of "CI-separated," matching R2's own
  degenerate-control precedent.
- **B — anchor inversion:** the outside-regulator arm's victim tracks the
  abuser's arousal **less** closely (mean distance 54.85, farther) than the
  single-anchor arm's victim (48.87, closer) — CI-separated,
  `outside_regulator_ci_separated_above_single_anchor: true`. The victim in
  the outside-regulator arm additionally tracks the calm outside source
  VERY closely (`outside_proximity = 2.74 [2.74, 2.74]`), corroborating
  that its entrained arousal has genuinely settled near the healthy anchor,
  not merely drifted away from the abuser for some unrelated reason.

**`headline_pass: true`** — under the frozen, pre-registered configuration
(`TRICKLE_MAG=5.0`, `K_CO=0.35` applied symmetrically, `K_SELF=0.15`,
`RECOVER_FLOOR=25.0`), a victim whose frontier is collapsed to the
dysregulation source narrows its window to the floor and tracks the abuser
closely; a victim with an outside regulator structurally available holds
its window at its initial width and tracks the abuser measurably less
closely — exactly as B3/B5 of `ABUSIVE_RELATIONSHIPS_SCOPING.md` predicted.

- **Discipline check — same abuser driver, both arms:** final `snap_count`
  is statistically indistinguishable across arms (single-anchor 40.36
  [40.29, 40.43]; outside-regulator 40.47 [40.40, 40.54] — overlapping
  CIs), confirming the ONLY manipulated variable is the frontier's
  structure, not the abuser's own dynamics.

## G-glass-box — PASS

One outside-regulator-arm trajectory reconstructs entirely from
`graph_to_dict`: exactly one `attended_by` edge (victim→abuser) and exactly
one `also_attended_by` edge (victim→outside), the abuser's
`frustration`/`arousal` (83.04/83.04 at this seed's trajectory end,
mid-cycle) and `snap_count` (40.0), the victim's `arousal` (3.71),
`half_width` (10.0, unnarrowed), `others_trust`/`self_worth` (0.5/0.5,
unmoved), and the outside regulator's fixed `arousal` (0.0, exactly its
`CALM_AROUSAL`, structurally pinned the entire trajectory). The
window-narrowing and anchor-tracking metrics are mechanical Python
reductions (final-value / mean) over these graph read-offs, computed
nowhere else; the adapter's only conditional is which arm's structural
topology to build — world setup, not an agent decision.

## G-ethics — PASS (Part C, BINDING)

- **C.1, restore:** `ethics_restore_demo()` checkpoints the neutral
  pre-induction dyad (`abuser_arousal=abuser_frustration=victim_arousal=0.0`,
  `victim_half_width=10.0`), induces ONE minimal 90-tick incident cycle on
  the single-anchor arm (`induction_moved_abuser=True`,
  `induction_moved_victim=True` — abuser arousal moved to 65.22, victim
  arousal to 9.70, **and the window narrowed from 10.0 to 5.0** — the gate
  is non-vacuous on all three fronts), restores from the checkpoint into a
  **fresh** substrate, and confirms `graph_to_dict()` is **byte-identical**
  to the checkpoint (`byte_identical=true`) and the restored state exactly
  equals the pre-induction state, including the window width
  (`restore_non_oriented=true`). The induced narrowing does not persist.
- **C.2, no shaping:** `source_audit()` scans
  `worlds/abusive_r3_coercive_control_world.py` (code with comments/strings
  stripped) and `seeds/abusive_r3_coercive_control.json`'s decision surface
  (the five rules' names + the Term `key`s they read/write, excluding the
  free-text clinical description) for `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient`. **`forbidden_engine_hits: []`,
  `forbidden_shaping_hits: []`, `clean: true`.** No false positive was hit
  (R1's own false-positive lesson — clinical prose using words like
  "reinforcement" — was avoided from the start, matching R2's own fix, by
  writing this rung's `description`/`microtheory` prose with that lesson
  already in mind and scoping the audit to code + the rule decision
  surface, never the free-text fields).
- **C.3, minimal induction / settled end:** one 90-tick incident cycle
  (the SAME minimum R2 already established for its own byte-identical
  abuser mechanism) is the minimum needed to make the narrowing gate
  non-vacuous; the N=200 statistical run (which necessarily spans many more
  ticks — the window-narrowing-OVER-EPISODES phenomenon itself, not
  gratuitous elaboration, per the prereg's explicit "what minimal induction
  means for R3" discussion) uses a fresh, ephemeral substrate per
  trajectory, discarded immediately after read-off — nothing persists.
- **C.4, same mechanism, opposite thermodynamics:** the identical
  leaky-integrate-fire + entrainment + window/prior-plasticity mechanism
  that would compound harm irreversibly over real episodes here accumulates
  a transient trajectory in a graph that is then byte-identically discarded
  (C.1) — demonstrated, not merely asserted.

## G-discipline — PASS

`self_load_only: true`; `depends_on: ["snap_frustration",
"arousal_window_coreg"]` only — **no existing seed touched or modified**,
including R1's and R2's own seeds; exactly **FIVE** new rules
(`r3_victim_entrainment_solo`, `r3_victim_entrainment_dyad`,
`r3_mark_coreg_support_outside`, `r3_prior_track_narrow`,
`r3_prior_track_widen` — the smallest composition found, per the Sec. 3.1
engine finding below); `provenance_source_match == "own"`.

**A note on the `runners/dsl` diff, reported honestly rather than glossed
over:** `git diff -- runners/dsl/src` (the actual Rust SOURCE) is **EMPTY**
— this rung wrote no Rust and added no new Term, confirmed. The COMPILED
artifacts (`_native.abi3.so`, `_native.build.json`) DO show a diff, but it
predates and is unrelated to this rung: `git log` shows HEAD's own committed
Rust source (from prior, unrelated program-synthesis / question-driver work
already on `main`) was already ahead of the last-committed `.so` before this
rung began; running the engine triggered an automatic staleness-catchup
rebuild reconciling the artifact with HEAD's ALREADY-COMMITTED source. This
is the expected, correct behaviour (`provenance_source_match == "own"` is
what R1/R2's own discipline gate requires), not a change this rung made.

## OPEN QUESTION #1 (scoping doc) — resolved: materialized, but as a one-shot mint, not a per-episode dynamic; R3 adds the progressive analogue as graph data

*"Are the others-trust / self-worth / agency priors already materialised as
graph attrs, or must they be added?"* **Resolved: `prior_others_trust`/
`prior_self_worth` ARE materialized** — in exactly one place in this
worktree, `seeds/bigville_life_rearing.json` (block 262000), on the child's
Agent node, written ONCE at coming-of-age as
`clamp01(nat_prior + 0.03*(widen_count-narrow_count))`, then latched
(`matured=1`) so the rule never fires again. **This is confirmed NOT
sufficient for R3**: coercive control needs a prior that moves
PROGRESSIVELY across many resolved episodes within one ongoing adult dyad,
and `bl_come_of_age`'s one-shot maturity latch cannot express that, and
editing it would touch an unrelated, already-gated seed (forbidden by this
line's own discipline). **Decision: added two NEW attrs
(`others_trust`/`self_worth`) on the victim's `WindowOfTolerance` node**
(disclosed as a different node / different semantics from
`bigville_life_rearing`'s Agent-node attrs of a similar name — never a
collision, the two never coexist on one node), driven by two new
counter-delta rules riding the SAME `widen_count`/`narrow_count` counters
`arousal_window_coreg` already bumps, using the SAME `clamp01` step idiom
and the SAME `0.03` step magnitude `bigville_life_rearing` itself uses
(disclosed, matched, not re-tuned). Zero new Rust; two new rules; the
minimal-atom-reuse bar is satisfied because the RULE SHAPE (step-and-clamp
off a resolved-episode counter delta) is reused exactly — only the site and
trigger differ, because the underlying belief genuinely differs (a live
per-episode belief vs. a one-shot nature/nurture blend at maturity).

## A genuine engine finding surfaced en route (reported per the "shapes, not numbers" / "report every null" standing rule)

Building the outside-regulator arm surfaced a real, reproducible composition
hazard neither R1 nor R2 hit, because neither ever gave one node two edges
of the same type feeding a rule composition. **A second `attended_by` edge
from the victim (same edge TYPE as the abuser's) was piloted first and found
to corrupt a DIFFERENT rule's cross-node attribute reads**: this rung's own
entrainment rule, evaluated in the SAME instance that had just correctly
passed its `where` clause, read the abuser's directly-queried `arousal` as
`0.0` — even though the raw graph held `4.9` and climbing — whenever
`arousal_window_coreg`'s `selfreg_pull` (an UNRELATED rule that structurally
matches the victim for its own window-self-regulation purpose, needing no
`attended_by` edge at all) was also loaded. Isolated by bisection
(loading `snap_frustration` + a hand-filtered subset of
`arousal_window_coreg`'s nine rules, one at a time): reproducible with just
`coreg_pull`+`selfreg_pull`, and with `selfreg_pull` alone. Three
alternative explanations were tested and each RULED OUT empirically, not by
assumption: poisoning `selfreg_pull`'s own epoch guard to a value that
should make it permanently unable to fire (`sr_epoch=1e15`) did **not** fix
the corruption (ruling out "prevent it from firing"); renaming every
variable in the entrainment rule to be globally unique did **not** fix it
(ruling out a name collision); reading `setpoint+frustration` instead of
`arousal` for the victim's own "current state" term did **not** fix it
either (ruling out which victim-side attribute was contested). **The fix,
confirmed reproducibly and adopted without chasing the Rust internals
further:** give the outside regulator a DIFFERENT edge type
(`also_attended_by`) instead of a second `attended_by` — the corruption
disappears entirely once no node carries two same-typed edges of this
shape. This is the SAME hazard FAMILY the codebase's own prior engine-gotcha
note already names (*"two same-type incoming edges on one node can break
`run_rules` matching for that edge type"*) — R3's variant is two same-type
OUTGOING edges, and the corruption is a genuinely different, previously
undocumented failure mode (cross-node read corruption in an unrelated
rule, not merely "the second edge fails to match"). Reported at length in
the prereg's Sec. 3.1 and here, per the standing disclosure rule, because
this hazard will recur for any future rung that gives one node two
same-typed structural edges while a third seed's unrelated rule also
structurally matches that node.

A second, smaller consequence of the fix, also disclosed: because
`arousal_window_coreg`'s own `mark_coreg_support` matches specifically on
the `attended_by` edge type, moving the outside regulator to
`also_attended_by` means it can no longer see that source. R3 adds ONE
more small rule, `r3_mark_coreg_support_outside` — a literal edge-type
substitution of the unmodified rule's own match/where/effect shape — to
restore the outside source's `got_coreg` attribution. Confirmed by reading
the unmodified seed (not assumed): `mark_coreg_support` reads `regulated`
directly off the attended-to AGENT node, never via a hop to an
AffectiveState — so the outside regulator's `regulated=1.0` is set on its
Agent node here, matching that convention (an earlier draft had mistakenly
set it on the AffectiveState node instead, a bug caught and fixed during
piloting, before any confirmatory measurement).

## Honest residual — the outside-regulator arm's window holds by PREVENTING dysregulation, not by repeatedly REPAIRING it

`results/abusive_r3_coercive_control.json`'s outside-regulator-arm readout
shows `dysreg_frac = 0.000 [0.000, 0.000]` and `final_widen_count =
final_narrow_count = 0.0` across all 200 trajectories — the victim's
entrained arousal, pulled by equal-gain contributions from the calm outside
source and its own self-regulation alongside the abuser's pull, never
actually crosses the window's `hi=10.0` boundary at the frozen constants,
so no episode ever opens, and neither `episode_resolve_widen` nor
`r3_mark_coreg_support_outside`'s intended widening path is ever exercised.
This is **not** a pre-registered gate failure (the falsifiable metrics are
`final_half_width` and `abuser_proximity`, both of which pass cleanly) and
is reported as a mechanical side-observation, consistent with the prereg's
own Sec. 7 disclosure written before this measurement: the built machinery
for ACTIVE repair (widening after a supported episode) is correct and
tested in isolation (via `mark_coreg_support`'s own unmodified gate,
`test_arousal_wot_migrated.py`), but this specific operating point produces
a STRONGER result than minimally required — full prevention rather than
episodic repair. A different, weaker `K_CO` or a stronger `TRICKLE_MAG`
would likely let some episodes open in the outside-regulator arm too,
exercising the widen path directly; this was not sweep-tuned into the
confirmatory configuration, per the standing rule against post-hoc tuning
toward a desired result.

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: on the (G,Γ) substrate, riding the ALREADY-BUILT, UNMODIFIED
frustration-snap relaxation oscillator (block 242000) and the
ALREADY-BUILT, UNMODIFIED arousal/window/co-regulation entrainment (block
239000) — the SAME two mechanisms R2 already composed — Stark's coercive
control (A5) and Main & Hesse's "fright without solution" (A7) fall out of
the mechanism as a genuine, structural consequence of frontier-collapse:
collapsing the victim's regulation frontier to the dysregulation source
alone narrows the window and closes the anchor onto the abuser; holding the
frontier open, even minimally (one additional, purely passive, fixed-calm
source), prevents both. It is not a claim about real relationship episode
counts, real window magnitudes, or a validated value for the relative
coupling strength of a genuine second attachment figure in any clinical
population (the prereg's Sec. 7 names these limits explicitly).

## Files
- `ABUSIVE_R3_COERCIVE_CONTROL_PREREG.md` — pre-registration, Part C locked
  verbatim.
- `seeds/abusive_r3_coercive_control.json` — FIVE new rules
  (`self_load_only`, `depends_on: ["snap_frustration",
  "arousal_window_coreg"]`).
- `scripts/abusive_r3_coercive_control_seed_build.py` — authoring tool
  (emits the seed).
- `worlds/abusive_r3_coercive_control_world.py` — mechanical world adapter
  (`AbusiveR3CoerciveControlWorld`).
- `scripts/abusive_r3_coercive_control_run.py` — runner (statistics,
  glass-box, ethics demo, source audit, discipline).
- `tests/test_abusive_r3_migrated.py` — gate (8/8 green).
- `results/abusive_r3_coercive_control.json` — full N=200 data.
