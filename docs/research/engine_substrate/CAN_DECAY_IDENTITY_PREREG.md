# Decay + identity dynamics, native — PREREG

Base `main @ 299ace3` ("Merge can-consumer-migration: 1/7 migrated (Bigville),
6/7 honestly blocked, GO"). Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-decay-identity`, branch
`can-decay-identity`.

This is one of three parallel rungs unblocking
`CAN_CONSUMER_MIGRATION_RESULTS.md` §1 row 6
(`domains/self_improvement_loop.py`)'s three independent blockers on
`self_improvement_step`: (a) decay, (b) Hebbian materialization (a SIBLING
rung's exact scope — not attempted here), (c) identity dynamics. This rung
builds (a) and (c) only.

---

## 0. What is real, quoted precisely, read before any design

**The blocker** (`CAN_CONSUMER_MIGRATION_RESULTS.md` row 6): *"decay —
confirmed, across all three prior rungs, to have NO native analog proposed
anywhere, and explicitly out of this rung's scope to build"*; *"identity
dynamics — never one of the five claims the spike mapped, no native design
exists at all."*

**The continuous mechanisms, read from source** (`domains/
self_improvement_loop.py`):

- `maybe_decay_h`/`maybe_decay_J` (`:80-91`) wrap `substrate.mt_decay_h`/
  `mt_decay_J`, each gated by `mt_allows(substrate, mt, "allow_Hebbian_J")`
  (J) or `"allow_h_drift"` (h).
- `maybe_update_identity` (`:179-188`): `h_id ← h_id + α·σ − β·h_id`,
  gated by `allow_h_drift`.
- `nudge_identity_on_flipped` (`:191-218`): on insight consolidation,
  `identity_field ← identity_field + α_eff·σ_target` per flipped node,
  `α_eff = base_alpha·(1 + ln(max(1, recurrence_count)))` — log-scaled so
  recurrence doesn't blow up the nudge. Gated by `allow_h_drift`.

**The Rust continuous mechanism** (`runners/dsl/src/can_ops.rs`):
- `decay_J` (`:735-765`): `J_ij ← (1−λ)·J_ij`, every `causal_influence`
  edge.
- `decay_h` (`:835-854`): `h_i ← (1−γ)·h_i`, every Concept's
  `external_field`.
- `update_identity_dynamics` (`:782-802`): `identity_field ← identity_field
  + α·σ − β·identity_field`, per Concept — the leaky integrator, docstring
  states explicitly: *"Sustained positive σ → identity grows positive...
  Flipping σ averages to near zero → identity decays toward zero."*
- `nudge_identity` (`:813-827`): `identity_field ← identity_field +
  α·target_sigma`, single-Concept, called by the Python wrapper above.

**The native mechanism this rung extends** (`seeds/
can_native_reimplementation.json`, v1.1.0, unmodified by this rung):
`can_native_update_3state`/`_2state` read `Attr(c,"external_field")` +
`Attr(c,"identity_field")` + `Sum(Edges(c,"causal_influence"))` as FLOAT
summands feeding an `IfThenElse` threshold that commits an INTEGER `state`
— i.e. `external_field`/`identity_field`/edge `weight` are MAP parameters
(the local-field computation is the cross-frame map from current joint
state to next discrete state), not in-frame observed data themselves; this
is the same footing `weight` already stands on (fixed `1.0` at mint,
real-valued, never questioned as a frame-invariant violation). Hebbian's
native half (`can_native_note_coactivation`/`_hebbian_mint`/`_reweight`)
holds exactly two real IN-FRAME integer counters per `Coactivation` node:
`evidence_confirm`/`evidence_disconfirm`, stepped by ordinary `Plus`/
`IfThenElse` rule-effect arithmetic, epoch-gated by `can_tick >
evidence_tick`/`noted_tick` (strictly-later-external-tick idiom). The
cross-frame log-odds RENDER (`Log(Div(Plus(confirm,1),Plus(disconfirm,1)))`,
`LOGODDS_GENERATOR_RESULTS.md` §2) is evaluated live via `Substrate.
evaluate`, deliberately never written back onto the node — the counts are
in-frame, the render is between frames.

**The generator-step precedent** (`runners/dsl/src/shape_decode.rs:786-820`,
`apply_translate_once`): `v -> v + offset[j]` per coordinate slot, integer
offset, NO wrap (unlike `modular`), NO origin-normalization (unlike every
rotation/scale kind — translation is about POSITION, re-basing would erase
what it expresses). `LOGODDS_GENERATOR_RESULTS.md` §1 already established
that `evidence_confirm` stepping `+1` per confirming tick is `translate` at
`offset=[1]` — declared as `DimensionGenerator{kind:"translate",
offset:[1]}` (`seeds/inference_knowledge.json` local_id 13), documentation
only, never literally invoked at runtime (the actual stepping is ordinary
`Plus`/`IfThenElse` inside a rule effect — `apply_translate_once` is a
private fn, only called from inside `ShapeDecode`/`TransformDecode`/
`DimInfer`/`TimeInfer`'s own eval bodies, confirmed by grep in that rung).

---

## 1. Decay — the design decision, registered before building

**Question posed by the task**: does "decay toward zero" for a signed
integer evidence count mean (a) periodically decrementing `|count|` by 1
toward zero (linear/geometric integer analog), or (b) something that better
matches `translate`'s own step semantics (`v -> v ± 1` toward a target)?

**Decision, registered**: **(b), and (a) turns out to be the SAME answer
once decay is required to preserve integrality.** The continuous mechanism's
own formula, `h ← (1−γ)·h`, is inherently MULTIPLICATIVE/proportional — it
needs a real-valued rate `γ` and produces a real-valued result even from an
integer input (`7·(1−0.001) = 6.993`, not an integer). Applied to an
in-frame integer count, a proportional decay is a category error under this
project's own frame/continuum invariant (`CLAUDE.md`, "BASE-AS-DIMENSION"):
an in-frame quantity's own rule must keep it in-frame. The only decay shape
that preserves integrality every step is a fixed-quantum LINEAR decrement —
exactly `translate`'s own `v -> v + offset[j]` step, with `offset = -1`
(toward zero rather than away from it) — this is answer (a) and answer (b)
collapsing onto the same operation once integrality is enforced, not two
competing designs.

**One deviation from plain `translate`, registered up front, not discovered
mid-build**: `translate` itself has NO wrap and NO clamp (`shape_decode.
rs:790-791`, an unbounded orbit by design). A decaying evidence count must
NOT go negative (an `evidence_confirm` of −1 has no meaning — it is a
COUNT). So the native decay rule is `translate` at `offset=-1` PLUS an
absorbing boundary at 0 — the rule fires (decrements) only while the count
is `> 0`, and leaves it at 0 once reached (an `IfThenElse` guard, the SAME
idiom `can_native_hebbian_reweight`'s own confirm/disconfirm branch already
uses, not a new primitive). This is registered as a genuine, explicit
difference from the DOCUMENTED `translate` shape (which the design still
cites as the closest existing primitive, matching `LOGODDS_GENERATOR_
RESULTS.md`'s own "declared but not literally invoked" convention) — NOT
smoothed over as if it were a bare, unmodified `translate` application.

**Target**: the SAME two counters (`evidence_confirm`/`evidence_disconfirm`
on a `Coactivation` node) the Hebbian mechanism already holds — the ONE
in-frame integer quantity this native mechanism actually has that plays the
role `external_field`/`causal_influence.weight` play for the continuous
mechanism ("evidence loses weight over time unless reinforced" —
`can_ops.rs:829-834`'s own docstring for `decay_h`). Gated the SAME axis the
continuous `maybe_decay_h` uses: `mt_allows(mt, "allow_h_drift")` — the
policy check itself will be re-expressed as a `where`-clause Term (see §3),
not a Python decision, since this is a graph-native rule.

**Prediction, registered**: a `Coactivation` with `evidence_confirm=4,
evidence_disconfirm=1` under an ADAPTIVE Mt, decayed across several
successive external ticks, will step `(4,1) → (3,0) → (2,0) → (1,0) → (0,0)`
(both counters decrement independently, in the SAME rule firing, each only
while `>0`) and then FREEZE at `(0,0)` — no negative counts, ever. Under a
FROZEN Mt (or a HYBRID Mt with `allow_h_drift=0`), the SAME sequence of
external ticks must leave the counters completely unchanged.

---

## 2. Identity dynamics — the investigation, registered before building

**Question posed by the task**: is a Concept's "identity" just another
evidence-accumulation dimension (own confirm/disconfirm-shaped ledger,
`σ=+1` reading as a confirm-like event, `σ=-1` as a disconfirm-like event),
so the ALREADY-BUILT evidence-axis mechanism (counters + non-materializing
log-odds render) gives a graded "how committed" reading for free — or does
`nudge_identity_on_flipped`'s recurrence-boost behaviour need something that
mechanism doesn't provide?

**Registered expectation, stated before building, checked against the
result in §4/§5**: the REUSE claim will hold for the READING half
(producing a graded, growing-with-consistency, decaying-with-inconsistency
"commitment" signal is structurally identical to the causal-strength axis —
same shape, `Log(Div(Plus(confirm,1),Plus(disconfirm,1)))`, same
non-materializing discipline) but will NOT cleanly hold for the FEEDBACK
half: `identity_field` is read by `can_native_update_3state`'s own local-
field sum as a STORED, materialized float that participates in the NEXT
tick's state decision — a genuinely different role from the Hebbian log-odds
render, which is a pure external comparator that no native rule ever reads
back into a decision. Writing the identity log-odds render INTO
`identity_field` (materializing it, so the discrete update rule's local
field actually feels it) would be a NEW decision this rung has not been
asked to make and is not positioned to make safely (it changes
`can_native_update_3state`'s own observable dynamics, a rule this rung is
explicitly told to extend around, not modify) — expected outcome: **the
READING mechanism reuses the evidence-axis primitive with zero new
machinery; whether/how to MATERIALIZE that reading back into
`identity_field`'s feedback role is named as a real, separate, un-sized
follow-on, not built.**

**Design, registered**: a per-Concept evidence ledger, stored directly as
Concept attrs (no separate node — identity is a property of ONE Concept,
not a pair, unlike Hebbian's `Coactivation`): `identity_evidence_confirm`,
`identity_evidence_disconfirm`, `identity_evidence_tick`. One consolidated
rule (`can_native_identity_evidence_sample`, mirroring `can_native_
hebbian_reweight`'s own already-proven starvation-avoidance shape — ONE
rule computing which counter to bump via `IfThenElse`, not a confirm/
disconfirm sibling pair) fires when `state != 0` and `can_tick >
identity_evidence_tick` (the SAME strictly-later-tick epoch-gate idiom):
bump `identity_evidence_confirm` if `state > 0`, `identity_evidence_
disconfirm` if `state < 0`. The reading is the SAME log-odds Term shape,
evaluated live, never written back.

**Registered prediction for the recurrence-boost question (§3 of the
task)**: the continuous `nudge_identity_on_flipped`'s `α_eff = base_alpha·
(1 + ln(max(1, recurrence_count)))` and the log-odds render's own natural
shape `ln(confirm+1)` (when `disconfirm=0`) are BOTH natural-log-scaled
functions of a repetition count — same qualitative shape (sub-linear,
diminishing marginal return per additional repetition, unbounded growth) —
predicted to hold structurally, NOT numerically identically, because the
counts being log-scaled are DIFFERENT signals in origin: `recurrence_count`
in the continuous mechanism is basin-level (how many times THIS SPECIFIC
recurring insight/basin configuration has recurred, tracked in
`insight_naming.py`/`insight_detection.py`, out of this rung's scope to
touch), while `identity_evidence_confirm` here is tick-level (how many
successive nonzero-state ticks this Concept has been sampled). Reported
honestly whichever way the numbers land — analogy in SHAPE is not claimed
to be identity in SOURCE.

---

## 3. Native policy-gate re-expression — registered

`mt_allows(substrate, mt, axis)` (Python, `self_improvement_loop.py:44-56`):
`FROZEN → False`; `ADAPTIVE → True`; `HYBRID → bool(attrs.get(axis, True))`
(default True when the per-axis attr is absent). Both new rules must encode
this AS A TERM (a graph decision, not a Python one) in their own `where`
clause:

```
allow_h_drift_native =
  Or(
    Eq(Attr(mt,"update_policy"), Lit("adaptive")),
    And(
      Eq(Attr(mt,"update_policy"), Lit("hybrid")),
      Not(Eq(Attr(mt,"allow_h_drift"), Lit(0)))
    )
  )
```

Checked before registering: `Attr` on a missing key evaluates to
`Value::None` (`term.rs:4677-4699`); `Eq` uses `eq_with_string_coercion`
(`term.rs:4501-4512`), which is `a == b` on `Value`'s derived `PartialEq` —
`None != Str("adaptive")` and `None != Int(0)`, so a Concept/Mt with no
`update_policy` at all defaults to the FROZEN behaviour (matches Python's
`DEFAULT_POLICY = FROZEN`), and a HYBRID Mt with no `allow_h_drift` attr
correctly defaults to allowed (`Not(Eq(None, 0))` = `Not(false)` = `true`).
`Gt`/`cmp_bool` (`term.rs:7787-7809`) falls back to a type-tag comparison
when comparing mismatched variants (`value.rs:461-478`, `tag(None)=0 <
tag(Int)=2`), so `Gt(can_tick, missing_epoch_attr)` is `true` — a missing
epoch-gate attr behaves as `-infinity`, i.e. "eligible on the very first
check" rather than silently never firing. Both facts are load-bearing for
the rule design and are confirmed by direct source read here, not assumed.

---

## 4. What will NOT be built, registered up front

- No change to `can_ops.rs`, `causal_attitude_networks.json`, `seeds/
  can_native_reimplementation.json`, `seeds/evidence_axis_infer.json`, or
  `seeds/inference_knowledge.json` — this rung ADDS a new, self-contained
  seed layered on top (`seeds/can_decay_identity.json`), matching the
  established per-rung-own-seed-file idiom (`evidence_axis_infer.json`'s own
  precedent) and minimizing collision risk with the sibling Hebbian rung
  (named risk: both rungs may touch `can_native_reimplementation.json` — a
  new, separate file sidesteps that for this rung's own scope).
- No `maybe_hebbian`/Hebbian-materialization work of any kind (sibling
  rung's exact scope).
- No edit to `domains/self_improvement_loop.py`, `domains/insight_
  propagation.py`, or `domains/sparseness_signal.py` (final coordinated
  migration rung's job).
- No materialization of the identity log-odds render back into
  `identity_field`'s feedback role in `can_native_update_3state` — named as
  the real open question in §2, not resolved here.
- No new Rust Term. If the design above turns out to need one, this rung
  stops and reports why before writing any Rust.

---

## 5. Regression plan

`tests/test_can_native_reimplementation.py` run unchanged (must stay
green, byte-identical) + a new `tests/test_can_decay_identity.py` with the
three registered live demonstrations. Full scoped CAN regression re-run
before and after.
