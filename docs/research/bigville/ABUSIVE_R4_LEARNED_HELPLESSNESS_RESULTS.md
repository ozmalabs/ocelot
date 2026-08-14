# ABUSIVE R4 — LEARNED HELPLESSNESS: blocked escape → non-contingency → mis-set agency/contingency prior — RESULTS (block 292000)

Pre-registration: `ABUSIVE_R4_LEARNED_HELPLESSNESS_PREREG.md` (locks Part C of
`ABUSIVE_RELATIONSHIPS_SCOPING.md` verbatim, committed before this
confirmatory measurement, and states plainly why this rung's pilot was an
analytic + deterministic-trace derivation rather than R1/R2's off-block
statistical sweep). Full-power numbers: `results/abusive_r4_learned_helplessness.json`
(N=200 per arm). Gate: `tests/test_abusive_r4_migrated.py`. Base engine: own
build, `source_match == own`. `runners/dsl` diff EMPTY — **NO Rust, NO new
Term.**

## Headline — G-headline PASSES (both metrics)

N=200 episodes per arm, 60-tick episodes, paired per-episode initial-belief
jitter (both arms draw the SAME `contingency_prior` starting point at a given
episode index; only the outcome-resolution function — contingent vs
non-contingent — differs):

| arm | final `contingency_prior` (mean [95% CI]) | escape-attempt RATE (mean [95% CI]) |
|---|---|---|
| **CONTINGENT-ESCAPE** (attempt always succeeds) | **0.99999999964 [0.99999999963, 0.99999999964]** | **1.000 [1.000, 1.000]** |
| NON-CONTINGENT (attempt always blocked) — *failable control* | 0.2560 [0.2527, 0.2592] | 0.0314 [0.0306, 0.0323] |

- Contingent-arm prior is CI-separated **above** the non-contingent arm's
  (0.99999999963 > 0.2592). ✓
- Contingent-arm attempt rate is CI-separated **above** the non-contingent
  arm's (1.000 > 0.0323). ✓ — the contingent arm's rate is exactly 1.0 with
  zero variance (every one of 200 episodes attempts on every one of 60
  ticks); the non-contingent arm's rate sits at ~3% (2 attempts out of 60
  ticks, then permanent passivity — see "the emergent trap" below).

**`headline_pass: true`** — under the frozen, pre-registered configuration
(`escape_value=10.0`, `attempt_cost=3.0`, `lr=0.3`, `p0_mean=0.5`,
`T=60`), a contingent escape recovers the agency/contingency prior and
sustains near-total attempt behaviour; a non-contingent escape drives the
prior down and attempts cease almost immediately — exactly as B4 of
`ABUSIVE_RELATIONSHIPS_SCOPING.md` predicted, and exactly as the
prereg's Sec. 3 closed-form analysis predicted BEFORE this run.

### The control was genuinely failable, not rigged

Nothing in the value-economy composition guarantees the contingent arm
recovers: the decision is a plain Argmax over
`contingency_prior · escape_value − attempt_cost` vs `0`. Had
`attempt_cost/escape_value` been set above the initial-prior mean (0.5), or
had `lr` been too small to climb back over the 0.30 breakeven within the
episode, the contingent arm would ALSO have stalled in passivity, and the
non-contingency mechanism (as modelled) would have been wrong — reported as
such, per the prereg's own falsification bar. The chosen operating point is a
disclosed, analytically-derived point (prereg Sec. 3), not an inevitability of
the Argmax-over-a-prior-as-node template.

## The emergent absorbing-state trap (the rung's most interesting finding — predicted in the prereg, confirmed here)

The non-contingent arm does not decay smoothly toward a low prior over the
full 60-tick episode. It attempts exactly **twice**, is blocked both times,
and then — because the belief has by then crossed below the 0.30 breakeven —
the Argmax switches permanently to `stay`. Once passive, no further attempts
occur, so no further evidence ever arrives, so the belief can never recover:
it FREEZES at whatever value the first two blocked attempts left it at
(≈0.245 in the deterministic trace; the N=200 statistical spread,
0.2527–0.2592, reflects only the per-episode jitter in the STARTING belief,
not any further evidence-driven movement). **This is not a separately
hand-coded "give up" rule** — it falls straight out of composing the
Argmax-over-current-belief decision with the evidence-only-arrives-when-you-
try belief update: passivity is self-reinforcing once it starts, because it
also switches off the only channel (attempting) that could ever disconfirm
it. This is the glass-box mechanism behind "why don't they even try any
more" (Part D of the scoping doc): not diminishing willpower, but a rational
belief update that, once it crosses a threshold, structurally cuts off its
own future evidence supply.

## G-glass-box — PASS

One contingent-arm episode reconstructs entirely from `graph_to_dict`: the
single `has_escape_decision` edge, `EscapeDecision.contingency_prior`
(0.99999999969 on this seed) and `chosen_action` (1.0 = attempting), and the
victim's harm-analog `AffectiveState.arousal` (19.9986, climbing toward its
own leaky-EMA steady state under repeated relief pushes — see the honest
residual below). The belief update is a single named rule
(`r4_belief_update`); the attempt/stay decision is a single named rule
(`r4_choose`); the adapter's only conditional is which arm's
`resolve_outcome` function to apply — world setup, not an agent decision.

## G-ethics — PASS (Part C, BINDING)

- **C.1, restore:** `ethics_restore_demo()` checkpoints the neutral
  pre-induction victim (`contingency_prior=0.5, arousal=0.0`), induces one
  20-tick non-contingent episode (`induction_moved_prior=True,
  induction_moved_arousal=True` — prior moved to 0.245, arousal to −9.25, so
  the gate is non-vacuous), restores from the checkpoint into a **fresh**
  substrate, and confirms `graph_to_dict()` is **byte-identical** to the
  checkpoint (`byte_identical=true`) and the restored state exactly equals
  the pre-induction state (`restore_non_oriented=true`). The induced state
  does not persist.
- **C.2, no shaping:** `source_audit()` scans
  `worlds/abusive_r4_learned_helplessness_world.py` (code with
  comments/strings stripped) and `seeds/abusive_r4_learned_helplessness.json`'s
  decision surface (rule names + Term `key`s, excluding the free-text
  clinical description) for `reward_signal` / `punish` / `reinforce` /
  `backprop` / `gradient`. **`forbidden_engine_hits: []`,
  `forbidden_shaping_hits: []`, `clean: true`.** The mechanism satisfies the
  task brief's specific concern for this rung directly: the outcome delivered
  by the world (`EscapeDecision.outcome`, 0.0 or 1.0) is a plain STATE FACT —
  mechanically identical to a harm/relief magnitude (block 283000) or a
  stressor magnitude (block 239000/286000) — and `r4_belief_update` is a
  leaky EMA STATE FILTER over that fact, never a value assigned to grade the
  agent's choice to attempt or stay. The decision (`r4_choose`) reads only
  the CURRENT belief, never the raw outcome directly; the belief update never
  reads or reacts to `chosen_action`. Nothing in the composition scores a
  choice.
- **C.3, minimal induction / settled end:** one 20-tick episode is the
  minimum needed to move the prior and the harm-analog arousal measurably
  (the non-contingent trap is already reached by tick 3, prereg Sec. 3.2);
  the N=200 statistical run uses a fresh, ephemeral substrate per episode,
  discarded immediately after read-off — nothing persists.
- **C.4, same mechanism, opposite thermodynamics:** the identical
  contingency-belief-formation mechanism that would compound irreversible
  passivity in a real relationship here accumulates a transient value in a
  graph that is then byte-identically discarded (C.1) — demonstrated, not
  merely asserted.

## G-discipline — PASS

`self_load_only: true`; `depends_on: ["core_emotions"]` only — **no existing
seed touched or modified** (`seeds/agency.json` and `seeds/marshmallow_delay.json`
were read as design precedent only, never loaded; R3's files were read once,
for the convention check below, and never modified); exactly **FIVE** new
rules (`r4_belief_update`, `r4_appraise_attempt`, `r4_appraise_stay`,
`r4_choose`, `r4_arousal_track` — more than R1's two or R2's one, because
this mechanism genuinely needs both a belief-UPDATE rule and the
Argmax-DECISION rules, unlike marshmallow's fixed-belief template);
`runners/dsl` diff EMPTY (no Rust, no new Term —
`Plus`/`Minus`/`Times`/`Max`/`Min`/`Gt`/`Eq`/`And`/`IfThenElse`/`Argmax`/
`Attr`/`Var`/`Lit`/`Neighbours` only, all already used elsewhere in this
line); `provenance_source_match == "own"`.

## R3 convention check — R3 had landed (partially); no prior-as-node convention to inherit

At build time, R3's seed/world/seed-builder files existed in the working tree
but its prereg/results/test docs had not. R3's prior-mis-setting mechanism
(`others_trust`/`self_worth`) attaches DIRECTLY as new attrs on the victim's
existing `WindowOfTolerance` node, stepped by a fixed clamp01 increment — not
a prior-as-node pattern. Per the task brief's own explicit fallback, this rung
therefore used `seeds/marshmallow_delay.json`'s own prior-as-node template
(a dedicated node carrying the belief, `EscapeDecision` here) directly, which
is what `ABUSIVE_RELATIONSHIPS_SCOPING.md` B4 names for R4 regardless. No R3
file was modified or built upon.

## The `seeds/agency.json` ambiguity — resolved, not followed literally

The task brief names `seeds/agency.json` as "the existing agency drive."
That seed, read in full, is the unrelated vision-domain `arc3_game`
`ControlledElement` (body-control-detection) microtheory — not a drive or a
psychological prior. `ABUSIVE_RELATIONSHIPS_SCOPING.md` B4's own text
resolves this: it names "the 207000 agency / time-cost drive" — the SAME
generic `Drive`-node primitive `marshmallow_delay.json` already rides for
TEMPERAMENT, reused under an "agency" framing. This rung follows the scoping
doc's text and marshmallow's own template; `seeds/agency.json` is not loaded
or referenced anywhere in this rung's rules.

## Honest residual — the harm-analog arousal channel is sparse, not continuous, by design

`r4_arousal_track` only fires on ticks where a FRESH outcome was just
delivered (guarded on `outcome_epoch > arousal_epoch`, the fix for the
composition hazard in Sec. 3.1 of the prereg) — so between outcome-delivery
ticks, arousal does not visibly leak at all (it is frozen, not gradually
decaying). This is a disclosed, deliberate simplification (this channel is
explicitly NOT the headline metric, exists solely for the G-ethics
demonstration) rather than a continuously-ticking arousal model; it is
reported here rather than left implicit, matching R1's own disclosed
"arousal is still a scalar, last-tick readout" residual.

## A genuine engine finding surfaced en route (reported per the "shapes, not numbers" standing rule)

The prereg's Sec. 3.1 records a real composition hazard found and fixed while
building this rung, independently reproducing the SAME CLASS of finding
`ABUSIVE_R2_CYCLE_LIMIT_PREREG.md` Sec. 3.0 reported for a different rule:
`run_rules()` is a REPEATING fixpoint, and an UNGUARDED rule whose effect
writes an attribute as a function of THAT SAME attribute's own current value
(rather than purely re-deriving it from other, unrelated attributes) is not
idempotent across repeated passes within one call — it converges to the fixed
point of its own recurrence relation instead of advancing one step. The first
`r4_arousal_track` draft hit this (converging to `push/k_self` in a single
`run_rules()` call instead of leaking by one tick); the fix was the SAME
epoch-guard idiom `r4_belief_update` already used correctly from the start.
Recorded here because — like R2's own finding — this is a general, reusable
fact about the engine, not an R4-specific quirk: **any future rule whose
effect is self-referential needs a one-shot guard; a rule that only
re-derives its output from other, unrelated attributes does not.**

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: on the (G,Γ) substrate, riding the ALREADY-BUILT, UNMODIFIED
core_emotions value economy (block 204000) and the marshmallow prior-as-node
TEMPLATE (block 240000), five new rules compose a contingency-belief that
updates from observed action–outcome evidence (never a scored choice) and a
plain Argmax decision over that belief — and Maier & Seligman's 2016 reframe
(A4) falls out of the composition exactly as stated: passivity is what the
value economy defaults to at a low prior, not a separately hand-coded
"helplessness" rule, and a genuinely contingent world recovers the prior and
sustains trying. It is not a claim about real relationship timescales, real
victims' actual starting beliefs, or a validated value for `attempt_cost`/
`escape_value`/`lr` in any clinical population (the prereg's Sec. 7 names
these limits explicitly, including the disclosed choice of deterministic
"blocked" over noisy "unpredictably punished" non-contingency).

## Files
- `ABUSIVE_R4_LEARNED_HELPLESSNESS_PREREG.md` — pre-registration, Part C
  locked verbatim.
- `seeds/abusive_r4_learned_helplessness.json` — five new rules
  (`self_load_only`, `depends_on: ["core_emotions"]`).
- `worlds/abusive_r4_learned_helplessness_world.py` — mechanical world
  adapter (`AbusiveR4LearnedHelplessnessWorld`, `resolve_outcome`).
- `scripts/abusive_r4_learned_helplessness_run.py` — runner (statistics,
  glass-box, ethics demo, source audit, discipline).
- `tests/test_abusive_r4_migrated.py` — gate.
- `results/abusive_r4_learned_helplessness.json` — full N=200 data.
