# Dynamic integer log-weight quantization for disposition gains — PREREG

## Context

Design-review pass on `AFFECT_COUPLING_SHAPE_*` (Phase 2) named a standing
violation: `seeds/frame_weights.json` already carries a verbatim creator
directive — *"all weights are not vectors, they are edges to other nodes —
weights are relative, order n and log scaled"* — but `psi_resolve_
disposition_gains`'s four gains (`reactivity_gain`/`hostile_gain`/
`warmth_gain`/`spite_gain`) were raw linear `Div` floats, never on a
declared lattice. First review pass rejected "integer log weight" on the
wrong grounds (conflating "integer" with the only in-tree octave-step
precedent, `Ashr`/`scale2`). Corrected per direct user feedback: *"The
minimum step isn't 1.0, I didn't say no mantissa - I said no floating
point... Floating point is a hack to get around insufficient
specification."* — the actual ask is a SCALED FIXED-POINT integer
(`round(SCALE * log(ratio))`), arbitrary declared precision, not a coarse
base-2 step. Second user correction: *"scale should also be dynamic, no
magic numbers"* — even a derived `SCALE=10^4` must not be a baked literal;
it must be computed live from real source/consumer data and stored as a
graph attr.

## Design

- **Canonical form**: `log_<name>_weight` (integer-valued Float, `Round`'d,
  the lattice INDEX — matching `can_register_quantization.json`'s proven
  `register_level_index` precedent) stored alongside the existing derived
  `<name>_gain` cache (`Exp` of the index back to a ratio) — index and
  value both persisted, neither replaces the other.
- **`SCALE` is graph data, computed once, never a `Lit` in the Rule JSON**:
  `_derive_log_weight_scale()` (`worlds/bigville_ocelot_adapter.py`) reads
  two independent live anchors and takes the max:
  - source-precision floor: `10 ** DRAW_CLIP_DECIMALS`, where
    `DRAW_CLIP_DECIMALS` is `bigville_town100_world.py::_draw_clip`'s own
    `round(v, N)` argument (currently 4) — never lose real source
    precision.
  - consumer-precision ceiling: derived from `SPEECH_MENU`'s actual
    smallest `base_value` gap and `_PARAM_SPEC`'s actual `hi/mean` ratio
    across the 4 coupled traits, via
    `ceil(2 * 0.5 * worst_ratio / min_gap)` — `2` (two multiplicative
    factors summed in log space: gain × pathway_gain, structural, not
    tuned) and `0.5` (round-to-nearest's own half-ULP bound, not tuned).
  - Stored on the `AffectCoupler` node as `log_weight_scale`, read by the
    rule via `Attr`, so a future change to either source changes the
    computed SCALE automatically with zero rule edits.
- **Zero-trait absence encoding**: `Gt(trait, 0.0)` guards both the
  canonical `log_*_weight` (placeholder `0.0`, never a real datum in that
  branch) and the derived `*_gain` (honest `0.0`) — avoids ever persisting
  `Log(0) = -inf` (which `persist.rs` cannot round-trip as `Value::Int` and
  silently JSON-nulls as `Value::Float`). ~21% of the real 100-cast has
  `w_spite == 0.0` exactly, so this is not a hypothetical edge.
- **`Exp` resolved once per resident**, inside `psi_resolve_disposition_
  gains` (matching the already-computed-once gain pattern), never inside
  `psi_couple_affect_to_tagged`'s per-target `Sum` — `psi_couple_affect_
  to_tagged` is UNCHANGED, reads `hostile_gain`/`warmth_gain`/
  `reactivity_gain` by name exactly as Phase 2 left it.
- **Reference means read live** from `_PARAM_SPEC` via
  `_param_spec_reference_means()`, replacing three hand-duplicated literals
  in the adapter (opportunistic hygiene fix, first opus review's §2f
  finding #2).

## Predictions (registered before this doc's verification run)

1. `_derive_log_weight_scale()` computes a scale ≥ `10^4` (the source-
   precision floor) purely from live `DRAW_CLIP_DECIMALS`/`SPEECH_MENU`/
   `_PARAM_SPEC` reads — no hardcoded `10000` anywhere in
   `bigville_ocelot_adapter.py` or `_build_affect_coupling_seed.py`.
2. Round-tripping a gain through `log_weight = Round(SCALE * Log(ratio))`
   → `gain = Exp(log_weight / SCALE)` introduces a small, bounded relative
   error (not exact equality) — expected because the whole point is
   declaring the previously-hidden float precision explicitly, not
   preserving float64's undeclared ~1e-15 precision.
3. That bounded error is small enough that **zero** real cast-100
   `chosen_speech_code` decisions flip between the dynamically-derived
   SCALE and a near-continuous reference (SCALE forced enormous,
   quantization error below the noise floor), across a spread of arousal
   levels.
4. Zero-valued traits (e.g. `w_spite == 0.0`) never produce `-inf`/`NaN` in
   either the canonical or derived attr.
5. `psi_couple_affect_to_tagged` and every existing Phase 1/2/3/4 test
   stays green — the redesign is fully contained in `psi_resolve_
   disposition_gains`.

## Does NOT claim

Does not claim this SCALE is calibrated to any external ground truth — it
is a registered derivation from the generator's own drawn precision and
the consumer's own smallest decision gap, a weaker claim than a fit. Does
not extend log-weight quantization to any other subsystem (`fw_update`/
`fw_pool` already do their own in-loop version; untouched here). Does not
address the still-outstanding cred_on rename, w_supergraph plateau fix, or
Phase 4 self-consistency gap named by the first opus review — those remain
separately tracked, not folded into this change.
