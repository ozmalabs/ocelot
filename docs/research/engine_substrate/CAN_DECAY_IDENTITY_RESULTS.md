# Decay + identity dynamics, native — RESULTS

Prereg: `CAN_DECAY_IDENTITY_PREREG.md`, same worktree/branch, base
`main @ 299ace3` ("Merge can-consumer-migration: 1/7 migrated (Bigville),
6/7 honestly blocked, GO"). Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-decay-identity`, branch
`can-decay-identity`.

One of three parallel rungs unblocking `CAN_CONSUMER_MIGRATION_RESULTS.md`
§1 row 6 (`domains/self_improvement_loop.py`)'s three independent
blockers. **This rung builds (a) decay and (c) identity dynamics only.**
(b) Hebbian materialization is a sibling rung's exact scope and is not
touched anywhere in this branch (confirmed by the diff itself, §6).

**Verdict, up front.** Both (a) and (c) are BUILT and PROVEN on the real
engine, zero new Rust, zero edits to any existing file — a single new,
self-contained seed (`seeds/can_decay_identity.json`, 3 rules) layered on
top of `seeds/can_native_reimplementation.json`, matching the established
per-rung-own-seed-file idiom (`seeds/evidence_axis_infer.json`'s own
precedent). **Decay** is a linear (not multiplicative) integer decrement —
the continuity-preserving translation of the continuous `(1−γ)·h` formula,
justified precisely by the frame/continuum invariant, not merely asserted.
**Identity dynamics**: the READING half (a graded "how committed" signal
that grows under sustained agreement and reads neutral under flip-flopping,
mirroring `can_ops.rs`'s own docstring) is a clean, zero-new-machinery reuse
of the evidence-axis mechanism — confirmed, not assumed, by building it and
measuring the result. The FEEDBACK half (materializing that reading back
into `identity_field` so it participates in `can_native_update_3state`'s
own local-field sum) is honestly NOT resolved — named as a real, separate,
un-sized follow-on, exactly as the PREREG predicted before any code was
written. **A real design defect was found and corrected live** while
sanity-checking against the real engine, before the test suite was written
(§3) — reported, not smoothed over.

---

## 1. Decay — the design, and why it is linear, not multiplicative

**The continuous mechanisms** (`domains/self_improvement_loop.py:80-91`,
`runners/dsl/src/can_ops.rs:735-854`): `maybe_decay_h`/`maybe_decay_J` wrap
`h ← (1−γ)·h` / `J ← (1−λ)·J` — proportional decay, gated by
`mt_allows(mt, "allow_h_drift")` / `"allow_Hebbian_J")`.

**The decision, registered before building (PREREG §1) and unchanged after
building**: a proportional decay is a category error applied to an
in-frame integer count — `7 · 0.999 = 6.993`, not an integer, and this
project's own frame/continuum invariant (`CLAUDE.md`, "BASE-AS-DIMENSION")
requires an in-frame quantity's own update to keep it in-frame. The only
decay shape that preserves integrality every single step is a
**fixed-quantum linear decrement toward zero** — exactly `translate`'s own
`v -> v + offset[j]` step (`shape_decode.rs:786-820`, `apply_translate_once`)
at `offset=-1`. This is not a weaker substitute for the continuous formula;
it is the unique shape an in-frame integer decay CAN take without leaving
the frame. **One explicit, registered deviation from plain `translate`**:
`translate` itself has no clamp (an unbounded orbit by design, `:790-791`);
this rule adds an absorbing floor at 0 (an evidence count can never be
negative) — named as a deviation up front, not silently added.

**Target**: `evidence_confirm`/`evidence_disconfirm` on a `Coactivation`
ledger — the one in-frame integer quantity the native Hebbian mechanism
(`seeds/can_native_reimplementation.json` v1.1.0, unmodified by this rung)
actually holds, playing the SAME role `external_field`/`causal_influence.
weight` play for the continuous mechanism ("evidence loses weight over time
unless reinforced" — `can_ops.rs:829-834`'s own docstring for `decay_h`).

**`DimensionGenerator{name:"evidence_decay", kind:"translate", offset:[-1]}`**
(`seeds/can_decay_identity.json` local_id 1) documents this shape
declaratively, exactly matching `LOGODDS_GENERATOR_RESULTS.md` §1's own
"declared but never literally invoked" convention — the actual stepping is
ordinary `Plus`/`IfThenElse` rule-effect arithmetic
(`can_native_evidence_decay`), not a call into `apply_translate_once`.

---

## 2. Identity dynamics — the investigation, and what it found

**The question** (PREREG §2): is a Concept's "identity" just another
evidence-accumulation dimension — σ readings as confirm/disconfirm-shaped
evidence about the Concept's own typical state — so the ALREADY-BUILT
evidence-axis mechanism (counters + non-materializing log-odds render)
gives a graded "how committed" reading for free?

**The registered expectation, checked against the build**: YES for the
READING half, NO (not yet resolved) for the FEEDBACK half. Confirmed
exactly as predicted:

- **Reading half — reuse holds, zero new machinery.** A per-Concept ledger
  (`identity_evidence_confirm`/`_disconfirm`/`_tick`, plain Concept attrs —
  identity is a property of ONE Concept, so no separate ledger node like
  `Coactivation` is needed) is sampled by `can_native_identity_evidence_
  sample`, ONE consolidated rule mirroring `can_native_hebbian_reweight`'s
  own already-proven starvation-avoidance shape exactly (`IfThenElse`-
  branched, not a confirm/disconfirm sibling pair). The graded reading is
  the SAME `Log(Div(Plus(confirm,1),Plus(disconfirm,1)))` Term, evaluated
  live, never written back — literally the same Term shape
  `_log_odds_term()` in `tests/test_can_native_reimplementation.py` already
  builds for the Hebbian axis, generalised to a different attr pair.
- **Feedback half — genuinely open, correctly not forced.**
  `can_native_update_3state`'s own local-field sum
  (`seeds/can_native_reimplementation.json:112-123`) reads `identity_field`
  as a STORED, materialized float that participates in the NEXT tick's
  discrete state decision — a fundamentally different role from the
  Hebbian log-odds render, which no native rule anywhere reads back into a
  decision (`LOGODDS_GENERATOR_RESULTS.md` §2's own "never materializing"
  design, confirmed live there and unchanged here). Writing the identity
  render into `identity_field` would change `can_native_update_3state`'s
  own observable dynamics — a rule this task explicitly says to extend
  around, not modify. This rung does not build that wiring. Named
  precisely, not smoothed over: **whether/how to materialize the identity
  reading into the feedback loop is a separate, un-sized design question**,
  exactly as the PREREG predicted before any code was written.

---

## 3. The live correction — found and fixed before the test suite was
written, reported not smoothed over

**First sanity check against the real engine** (before writing any
assertions): a Concept committed to `state=1.0` for 5 ticks, sampled by
`can_native_identity_evidence_sample` and decayed by a first-draft
`can_native_identity_evidence_decay` gated ONLY on `can_tick > own_tick`
(no reinforcement check), produced `identity_evidence_confirm = 0` after
5 ticks of PURE reinforcement — the opposite of the intended behaviour.

**Root cause**: `can_native_hebbian_reweight` (and, in the first draft, my
own sample rule) fires on EVERY tick a pair/Concept stays committed. A
decay rule gated only on "the clock advanced" is therefore eligible on the
SAME tick as reinforcement, every time a Concept stays persistently
committed — and a same-magnitude `+1`/`-1` pair of effects cancels exactly,
net zero growth under PERSISTENT reinforcement. This directly contradicts
`decay_J`'s own docstring (`can_ops.rs:733`: *"With Hebbian + decay running
together, persistent co-activation maintains J; transient co-activation
fades"*) — the continuous mechanism only gets that property because
`decay_rate` (0.001) is numerically tiny relative to `eta`, a magnitude
relationship a 1-quantum integer decrement cannot reproduce by choosing a
smaller rate (there is no "smaller than 1" integer quantum).

**The fix, registered as a design principle, not a patch**: decay reads
whether reinforcement ALREADY happened on this exact tick
(`coact.evidence_tick == mt.can_tick`, an attr `can_native_hebbian_mint`/
`_reweight` already maintain — a pure READ, zero coupling or edit to that
sibling-scoped rule) and skips decay when it did. This implements *"old
evidence fades UNLESS reinforced"* (`can_ops.rs:833`'s own `decay_h`
docstring) **literally**, rather than only asymptotically as the continuous
mechanism's rate ratio does. Confirmed live, §4 below
(`test_evidence_decay_never_races_reinforcement_in_the_same_tick`): 5
ticks of persistent reinforcement now produce `evidence_confirm=5`, not 0.

---

## 4. Live demonstrations — all three, on the real engine, real numbers

`tests/test_can_decay_identity.py`, run via `PYTHONPATH=".:runners/dsl/
python" python3 -m pytest tests/test_can_decay_identity.py -q -s`:

### (a) Decay of a real evidence count, gated by the policy check

**Adaptive — decays, floors at zero**
(`test_evidence_decay_erodes_toward_zero_when_adaptive_and_unreinforced`):
mint + reinforce to `(confirm=4, disconfirm=0)` (ticks 0-4, the SAME
trajectory `test_hebbian_reweight_end_to_end_unblocks_v1_graded_
reweighting` establishes), then stop reinforcing (one Concept's `state`
set to 0) and advance 7 more ticks:

```
decay trajectory (adaptive, unreinforced from tick 5): confirm=[3, 2, 1, 0, 0, 0, 0]
```

Exactly one quantum per tick, floored at 0, never negative.

**Frozen — blocked completely**
(`test_evidence_decay_blocked_when_frozen`): the SAME setup, `update_
policy="frozen"`. Mint/reweight are NOT policy-gated in the existing
`can_native_reimplementation.json` (a pre-existing fact this rung does not
touch), so evidence still accrues to `(4,0)` — but once reinforcement
stops, 7 more ticks leave it completely unchanged:

```
frozen, unreinforced through tick 11: confirm=4 disconfirm=0 decay_tick=None
```

`decay_tick` is never even written — the rule never fires at all under
`frozen`, not merely "fires and no-ops."

**Hybrid, both directions**
(`test_evidence_decay_hybrid_axis_explicit_and_default`): explicit
`allow_h_drift=0` blocks decay (`confirm` stays `4`); `allow_h_drift`
attr ABSENT defaults to allowed (matches Python's `.get(axis, True)`)
and decays fully to `0` over 4 ticks:

```
hybrid allow_h_drift=0: confirm=4 (must stay 4)
hybrid allow_h_drift absent (default True): confirm=0 (must reach 0)
```

**The regression guard for §3's fix**
(`test_evidence_decay_never_races_reinforcement_in_the_same_tick`):

```
persistent reinforcement through tick 5: evidence_confirm=5 (must be 5, not 0 or 1)
```

### (b) Identity as a graded, per-Concept commitment reading

`test_identity_evidence_consistent_state_reads_stronger_than_flipping_
state`: one Concept held at `state=+1.0` for 10 ticks, one Concept
alternating `+1.0`/`-1.0` every tick, same Mt, same 10 ticks:

```
consistent: confirm=10 disconfirm=None -> identity_reading=2.3979
flipper:    confirm=5 disconfirm=5     -> identity_reading=0.0000
```

(`disconfirm=None` on the consistent Concept is the accurately-reported
raw attr state — it was never written because the sample rule's `disconfirm`
branch never fired; `Plus`'s own arithmetic treats a never-set attr as `0`
for the render, giving the correct `ln(11/1)=2.3979`, confirmed live and
noted here rather than silently tidied — real test fixtures in this file
explicitly pre-initialize both counters to `0` to avoid relying on this.)

`10` consecutive confirms render strictly positive and strictly higher than
the perfectly-split `5`-vs-`5` flipper, which renders EXACTLY `0.0` —
**mirroring `can_ops.rs:774`'s own stated continuous behaviour verbatim**:
*"Flipping σ averages to near zero → identity decays toward zero."* The
render never writes back onto either Concept (confirmed byte-for-byte,
same guard `test_log_odds_render_ranks_evidence_and_never_writes_back`
already established for the Hebbian axis).

**Identity ledger decay, both policy cases**
(`test_identity_evidence_decays_toward_zero_when_unreinforced_and_policy_
allows`, `test_identity_evidence_decay_blocked_when_frozen`):

```
identity decay trajectory (unreinforced from tick 5): confirm=[4, 3, 2, 1, 0, 0, 0]
frozen identity ledger before stopping reinforcement: confirm=0
frozen identity ledger after 7 unreinforced ticks: confirm=0 (must be unchanged)
```

**An honest asymmetry with the Hebbian frozen case, reported precisely**:
`can_native_identity_evidence_sample` is gated by `allow_h_drift` too
(matching `maybe_update_identity`'s OWN full gating in the continuous
mechanism — identity never updates AT ALL under frozen, not merely "grows
but doesn't decay"). So under `frozen`, the identity ledger never leaves
`(0,0)` in the first place — a DIFFERENT, but equally correct,
demonstration of policy respect than the Hebbian case (where mint/reweight
are ungated, so evidence accrues and only decay is blocked). Both are
real; they differ because the underlying mint/reweight rules they extend
differ in whether they themselves are policy-gated — not because of an
inconsistency in this rung's own design.

### (c) The recurrence-boost investigation

`test_recurrence_boost_is_log_scaled_like_the_continuous_nudge_but_not_
identical`:

```
n     identity_render=ln(n+1)   continuous_alpha_eff=base*(1+ln(n))
1     0.6931                     0.0500
5     1.7918                     0.1305
20    3.0445                     0.1998
identity_render marginal gain per additional recurrence, by interval: [0.2747, 0.0835]
```

**Confirmed**: both quantities are strictly increasing and CONCAVE
(diminishing marginal return) in the recurrence count — the render's own
marginal gain per additional recurrence shrinks from `0.2747` (n:1→5) to
`0.0835` (n:5→20), the SAME qualitative shape `nudge_identity_on_flipped`'s
hand-rolled `α_eff = base_alpha·(1+ln(recurrence))` has by construction
(`self_improvement_loop.py:207`). **Reported precisely, not overclaimed**:
this is a structural resemblance (both natural-log-scaled, both
sub-linear, both unbounded), NOT a numeric identity — the two formulas
never coincide at any tested `n` (asserted live, `readings[n] !=
continuous_boost[n]` for all three checkpoints), and — more importantly —
**the counts being log-scaled are different signals in origin**:
`recurrence_count` in `nudge_identity_on_flipped` is BASIN-level (how many
times this specific recurring insight/basin configuration has recurred,
tracked in `insight_naming.py`/`insight_detection.py`, out of this rung's
scope to touch), while `identity_evidence_confirm` here is TICK-level (how
many successive nonzero-state samples this Concept has taken). **Verdict:
the recurrence-boost SHAPE is already provided for free by the SAME
evidence-axis mechanism, with zero new weighting rule needed; the specific
basin-recurrence SIGNAL `nudge_identity_on_flipped` reacts to is a
different, unconnected count this rung does not wire in.**

---

## 5. What was built, precisely

`seeds/can_decay_identity.json` (v1.0.0, `self_load_only: true`, depends on
`can_native_reimplementation`), 3 rules, 0 productions (no new edge types —
every rule only reads existing `has_concept`/`coactivated_with`/
`coactivation_of` edges and writes `set_attr`), 3 declarative
`DimensionGenerator`/`LatentDimension` nodes (documentation only, matching
`LOGODDS_GENERATOR_RESULTS.md`'s own "declared, never literally invoked"
convention — confirmed by the same style of grep this arc always runs
before claiming a declaration is inert, §7 point 1 below):

1. **`can_native_evidence_decay`** — linear decrement toward zero of
   `evidence_confirm`/`evidence_disconfirm` on a `Coactivation` ledger, ONE
   rule (not a sibling pair, reusing `CAN_NATIVE_REIMPLEMENTATION_RESULTS.
   md` §3's starvation-fix lesson pre-emptively), epoch-gated
   (`decay_tick`), policy-gated (`allow_h_drift`, re-expressed as a Term),
   and gated against racing same-tick reinforcement (§3's live fix).
2. **`can_native_identity_evidence_sample`** — per-Concept σ-reading
   evidence accumulation, the SAME `IfThenElse`-branched shape as
   `can_native_hebbian_reweight`, applied to one Concept's own state
   instead of a pair's product-of-signs.
3. **`can_native_identity_evidence_decay`** — the SAME decay shape as
   rule 1, applied to the identity ledger, demonstrating decay is a
   REUSABLE RULE SHAPE across both evidence axes this rung builds, not a
   bespoke mechanism re-derived per axis.

`scripts/_build_can_decay_identity_seed.py` — a one-off authoring script
(the `tools/*`-class precedent `CLAUDE.md` names explicitly: "one-off
authoring/capture scripts that EMIT seed manifests") that constructs the
Term-tree JSON programmatically rather than by hand, to avoid a hand-typo
in a nested tree; not agent runtime.

Zero new Rust Terms — `Attr`/`EdgeAttr`/`Eq`/`Not`/`And`/`Or`/`Gt`/`Lt`/
`Plus`/`IfThenElse`/`Log`/`Div` all pre-existed and are reused exactly as
`can_native_reimplementation.json`/`LOGODDS_GENERATOR` already use them.
Confirmed by the diff itself:

```
$ git diff --stat main -- '*.rs'
(empty)
```

---

## 6. What was explicitly NOT touched, confirmed by the diff

```
$ git status --short
?? docs/research/engine_substrate/CAN_DECAY_IDENTITY_PREREG.md
?? docs/research/engine_substrate/CAN_DECAY_IDENTITY_RESULTS.md
?? scripts/_build_can_decay_identity_seed.py
?? seeds/can_decay_identity.json
?? tests/test_can_decay_identity.py
```

Zero existing files modified — `seeds/can_native_reimplementation.json`,
`seeds/evidence_axis_infer.json`, `runners/dsl/src/can_ops.rs`,
`runners/dsl/src/shape_decode.rs`, and `domains/self_improvement_loop.py`
are all byte-unchanged. No Hebbian-materialization logic (`maybe_hebbian`,
`causal_influence.weight` write-back) is touched anywhere in this branch —
that is the sibling rung's exact, separate scope, and nothing in this
seed's rules reads or writes `causal_influence.weight`.

---

## 7. Regression

**New test file, all live demonstrations, one run:**
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_decay_identity.py -q -s
8 passed in 0.22s
```

**Scoped CAN regression + the new file, one run, 115/115 passed:**
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_causal_attitude_networks.py tests/test_can_ops.py \
  tests/test_can_migration.py tests/test_can_crossover_point.py \
  tests/test_can_native_reimplementation.py tests/test_evidence_axis_infer.py \
  tests/test_bigville_can_native_migration.py \
  tests/test_identity_field.py tests/test_self_improvement_loop.py \
  tests/test_can_decay_identity.py -q
115 passed in 8.36s
```

**`tests/test_can_native_reimplementation.py` alone — byte-identical to
its pre-branch state**, confirmed both by the diff (§6, untouched) and by
re-running it: `11 passed in 0.61s` — the SAME 11/11 count `LOGODDS_
GENERATOR_RESULTS.md` §6 documented, no rename, no assertion changed. No
paired failing-node-id lists to report — zero failures, before or after,
across every file in the scoped set.

**Full boot regression** (`load_all_seeds` on a fresh `WorldAdapter`):
identical **8 pre-existing failures** to the documented baseline
(`acoustic_cue_vocab`, `character_tom`, `reading_constructions`,
`conceptual_categories`, `cue_investigator`, `named_compound_heads`,
`reading_skeleton`, `vision_change`, all `ValueError: seed node missing
local_id`), **0 rules_skipped** — `can_decay_identity.json` is correctly
excluded from the sweep (`self_load_only: true`, matching `can_native_
reimplementation.json`/`evidence_axis_infer.json`'s own precedent).

**No Rust build was needed or run** — `git diff --stat main -- '*.rs'` is
empty; zero `.rs` files touched anywhere in this branch.

---

## 8. What this rung does NOT establish

1. **Identity's FEEDBACK half remains unbuilt** (§2) — the identity
   log-odds render is never written into `identity_field`, so
   `can_native_update_3state`'s own local-field sum does not yet feel this
   rung's ledger at all. This is the real, honest residual: the READING
   mechanism is proven; whether/how to wire it into the discrete update
   rule's own feedback loop is a separate design decision, deliberately
   not made here (it would change `can_native_update_3state`'s own
   observable dynamics, a rule this task named as "extend around, don't
   modify").
2. **The recurrence-boost SHAPE match is structural, not a claim of
   equivalence** (§4c) — `nudge_identity_on_flipped`'s own basin-level
   `recurrence_count` is never connected to this rung's tick-level
   `identity_evidence_confirm`; doing so would require touching
   `insight_naming.py`/`insight_detection.py`, out of this rung's scope.
3. **Blocker B (Hebbian materialization) is untouched**, confirmed by the
   diff (§6) — this rung says nothing about it, positively or negatively.
4. **`domains/self_improvement_loop.py` itself is unmodified** — the
   coordinated final migration rung that wires `maybe_decay_h`/`maybe_
   decay_J`/`maybe_update_identity`/`nudge_identity_on_flipped` over to
   these native rules (alongside whatever the sibling Hebbian rung
   produces) is separate, later work, matching the task's own explicit
   scope boundary.
5. **The decay rate (1 quantum per external tick) is not claimed to be
   THE correct cadence** — it is the natural, integrality-preserving
   translation of "one `self_improvement_step` call = one decay
   application," matching the continuous mechanism's own call frequency
   (once per step, not sub-stepped); whether a coarser cadence (e.g. every
   K ticks) would better match some specific domain's dynamics is untested.
6. **Whether any of this reflects real human belief/identity-formation
   dynamics** remains exactly as open as every prior rung in this arc left
   it — this document is about this SUBSTRATE's own best-fitted mechanism.

---

## 9. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/can-decay-identity
git log --oneline -1 main   # 299ace3, verified before branching

# The new seed's own live demonstrations, with printed numbers
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_decay_identity.py -q -s

# Scoped CAN regression, including the pre-existing native suite unchanged
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_causal_attitude_networks.py tests/test_can_ops.py \
  tests/test_can_migration.py tests/test_can_crossover_point.py \
  tests/test_can_native_reimplementation.py tests/test_evidence_axis_infer.py \
  tests/test_bigville_can_native_migration.py \
  tests/test_identity_field.py tests/test_self_improvement_loop.py \
  tests/test_can_decay_identity.py -q

# Full boot regression (8 pre-existing failures only, unrelated to this rung)
PYTHONPATH=".:runners/dsl/python" python3 -c "
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
a = WorldAdapter(seeds=())
rep = load_all_seeds(a)
print('failed:', len(rep['failed']), 'rules_skipped:', len(rep['rules_skipped']))
for f in rep['failed']: print(' ', f)
"

# Zero Rust/existing-file touched
git status --short
git diff --stat main -- '*.rs'
```
