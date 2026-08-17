# w_supergraph magnitude fix — PREREG

## Context

Opus design-review pass on `AFFECT_COUPLING_SHAPE_*`'s cred_on/w_supergraph
sub-question found `em_fulfilment_value` (`seeds/core_emotions.json`) was a
SIGN GATE — `IfThenElse(Gt(w_supergraph,0), supergraph_contribution, 0)` —
not a weighting: any positive `w_supergraph`, however small, read the full
unscaled `supergraph_contribution`. In bigville's drawn population
(`_PARAM_SPEC` `w_supergraph`: mean 0.5, sd 0.2, clip [0,1]), ~99.4% of
residents behave identically regardless of how much they actually value the
collective. First attempt (`Times(w,contribution)`) was REJECTED live:
`tests/test_core_emotions_migrated.py::test_G5_integer_native` hard-enforces
this seed's integer-native-only invariant (`Div/Times/Exp/Log/Sqrt/Sin/Cos`
AST-denylisted; every output must be an exact integer every appraisal) — this
is CLAUDE.md's "in-frame is integer" rule, actively tested, not just
documented. A follow-up `Ashr`-only attempt was also wrong as first written:
bigville's real `w_supergraph` is a continuous `[0,1]` float, and `Ashr`'s
shift argument truncates via `.as_i64()`, collapsing any `w<1.0` to shift=0.

A dispatched opus design pass (steered explicitly toward psychological
realism over test-passing — the actual goal is a substrate "fundamentally
capable of replicating human level emotions and social behaviour," not a
substrate that merely "can do X") found: (1) `core_emotions.json` is a
SHARED seed with 11 real consumers, not just bigville, and every one of them
except bigville uses `w ∈ {0} ∪ [1,∞)` — so an attenuation-only lattice
(clamp above the reference weight `w=1.0`) is byte-identical everywhere
except bigville; (2) bigville's own live `record_action_outcome` path
publishes `supergraph_contribution` as a bare 0/1 flag, which — under a
strict integer-output constraint — caps `fulfilment_value`'s codomain at
`{0,1}` regardless of formula, so grading the RULE without also grading
bigville's own CONTRIBUTION SIGNAL would make bigville strictly worse, not
merely unchanged; (3) a real, already-computed graded signal already exists
in bigville's own data — `physical_object_observations` reach-delta, the
same "public mechanics, agent's own w values it" contract
`domains/harvest_world.py` already documents for its own commons.

## Design

- **`weighted_contribution`** (new rule, `em_weighted_contribution`, order 1):
  `Ashr(Times(w_supergraph_q, supergraph_contribution), w_scale_bits)` —
  fixed-point integer multiply-then-shift. `Times(Int,Int)` is exactly
  integer-closed (same closure property as `Plus`/`Minus`/`Ashr`, confirmed
  against `term.rs`'s `numeric_variadic`), so it was moved OUT of
  `integer_audit`'s AST denylist (that denylist tested the op NAME, not the
  property it claimed) — `integer_values_audit` was WIDENED in the same
  change to check the real property (exact-integer output) across every live
  caller's actual `w`/contribution range, so the gate is net stronger, not
  weaker.
- **`w_supergraph_q`/`w_scale_bits`**: the integer lattice rendering of the
  continuous `[0,1]` trait — computed ONCE at each consumer's
  `HeldEmotionParams` construction site (`domains/core_emotions_weight.py`,
  the shared, dynamically-derived quantizer), never a `Lit` baked into the
  rule. CLAUDE.md's BASE-AS-DIMENSION invariant applied literally: in-frame
  is integer, the continuum lives in the map that produces the step.
- **`B` (bits) derived from two live anchors, min not max**: source-precision
  ceiling (bits to represent a population drawn to `DRAW_CLIP_DECIMALS`
  decimal places, bigville's own named constant where importable) vs.
  consumer-resolution ceiling (bits needed so no live caller's own
  contribution range is quantized coarser than that caller's own integer
  magnitude already is — read from each real consumer's own named constant:
  `harvest_world.K`, `glassbox_r1_world.G_CONTRIB`,
  `langsim_world.G_CONTRIB`, plus the measure harness's own 800-magnitude
  fixtures). Never a hand-picked literal.
- **Attenuation-only above `w=1.0`**: `quantize_weight` clamps, so every
  existing consumer (`w ∈ {0} ∪ [1,∞)`) is unaffected; only bigville's own
  `w ∈ (0,1)` — previously indistinguishable from `w=1` — now varies.
- **`em_fulfilment`/`em_pride`** (firing gates) and `arousal_mux` all read
  `weighted_contribution` instead of the raw contribution+sign-gate
  conjunction — `Gt(weighted,0) == Gt(contribution,0) AND Gt(w,0)` exactly
  for every `w ∈ {0} ∪ [1,∞)`, so byte-identical everywhere except bigville.
- **Bigville's own `supergraph_contribution` graded** (`bigville` repo,
  `held_board_games.py::_room_tick`): the signed reach-delta this action
  caused to every OTHER participant's own `physical_object_observations`
  count (excludes self by construction), plus `collective_success` as the
  room's real total reach. `worlds/bigville_ocelot_adapter.py`'s
  `record_action_outcome` accepts both as optional kwargs, falling back to
  today's bare success flag when absent — independently landable, every
  prior caller unaffected.

## Predictions

1. `Times(Int,Int)` never produces a non-integer `Value` across every live
   caller's real `w`/contribution range (checked at the VALUE level inside
   `integer_values_audit`, not just the AST-name level).
2. Byte-identity: every non-bigville consumer's own migrated test suite
   passes with ZERO test edits (`harvest_commons`, `spite_skill`,
   `spite_to_succeed`, `glassbox_r1`, `langsim`, `langsim_syntax`,
   `marshmallow`, `abusive_{r4,r5,r6,r7,n4,u0}`, `modulator_emergence`).
3. `test_G1_w_magnitude_is_unidentifiable_plateau` stays green unedited —
   `W_MAG_PROBE ⊂ [1,∞)`, entirely above the clamp.
4. A NEW sweep — `w ∈ {0.1,0.25,0.5,0.75,0.9,1.0}` at
   `supergraph_contribution=300` — yields 6+ DISTINCT `fulfilment_value`s,
   strictly monotone in `w`.
5. On the real flagship 4-player scenario (`bigville`'s
   `monopoly_four_players`): opening the shared game box publishes a large
   positive `supergraph_contribution` to the other 3 participants (measured,
   not asserted in advance to a specific number); moving it to one's own
   name first (hoarding) publishes a negative one.
6. Zero new Rust; zero hand-picked uncited constants (`B` computed live via
   `domains/core_emotions_weight.py::derive_scale_bits()`, never a literal
   anywhere in the touched files).

## Does NOT claim

Does not claim `B=10` (whatever it derives to on a given tree state) is
calibrated to anything external — a registered derivation, not a fit. Does
not fix `ss_decision_value`'s own `w_spite` sign gate (`seeds/spite_skill.json`)
— the identical defect, one rule over, named as an honest residual because
every current consumer of `w_spite` also only ever draws `{0.0,1.0}`, but
bigville's own cast (`w_spite=0.45` for at least one authored character)
will hit it once spite reaches bigville. Does not claim graded fulfilment
changes any bigville behavioral OUTCOME end-to-end (a full cast-100
`decide_speech` flip sweep, mirroring `LOG_WEIGHT_QUANTIZATION_RESULTS.md`'s
falsifier harness with its pass criterion inverted, was NOT run in this
pass — named as deferred, not silently skipped). Does not touch `cred_on`'s
own naming collision (Phase B, separately tracked).
