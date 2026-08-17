# Affect-coupling hygiene (Phase C) — PREREG

## Context

The first opus design-review pass named two remaining hygiene items from
`AFFECT_COUPLING_SHAPE`'s build order, beyond the cred_on/w_supergraph
questions: a `resolution_bins` float-coercion bug at `_can_params`, and an
unguarded `_AFFECT_CHANNELS`/`CHANNEL_ROWS` hand-duplicated table.

## Item 1 — `resolution_bins` float-coercion: investigated, NOT a live bug

`_can_params` does `"resolution_bins": float(p.get("resolution_bins", 7.0))`
— conceptually a bin COUNT, coerced to Python float. Traced every real
consumer before touching anything:

- `worlds/bigville_can_beliefs.py::effective_resolution_bins` — takes the
  float, computes `round(...)`, returns `max(2, int(bins))` — already a
  safe int internally.
- `worlds/bigville_can_beliefs.py::quantize_j`'s `bins` parameter is
  ALWAYS called with `eff_bins` (the safe `int()` output above), never the
  raw float (`build_resident_can_mt:187`) — confirmed by reading the call
  site, not assumed.
- `domains/bigville_register_backend.py::decode_band` does its OWN
  `"resolution_bins": int(resolution_bins)` at the actual graph-write
  boundary, defensively, regardless of the caller's input type.
- Every real drawn value in `seeds/bigville_cast100.json` (100 residents)
  is already integer-valued (`8, 4, 7, 3, ...`, no fractional values).

**Prediction**: no consumer of `resolution_bins` crashes or silently
truncates data on a Python float input — every path already applies its
own safe `int()`/`round()` cast before the value does anything
resolution-sensitive. This matches the codebase's own established
convention (`can_register_quantization.json`'s precedent: integer-valued
Floats, not `Value::Int`) rather than violating it. **No fix registered for
this item** — it does not hold up as a defect under direct tracing.

## Item 2 — `_AFFECT_CHANNELS`/`CHANNEL_ROWS`: a real, fixed duplication risk

`worlds/bigville_ocelot_adapter.py`'s `_AFFECT_CHANNELS` was a hand-written
Python tuple, explicitly commented as "byte-identical to
scripts/_build_affect_coupling_seed.py's own CHANNEL_ROWS — the single
source of truth for the channel table is that builder script" — but with
no mechanism enforcing that identity. An edit to one without the other
would silently desync the seed's own `AffectChannel` shape from what the
adapter mints per-resident.

**Fix**: `_AFFECT_CHANNELS` deleted; the adapter imports `CHANNEL_ROWS`
directly from `scripts._build_affect_coupling_seed` (an established,
already-precedented import pattern — several `domains/*.py` files already
import from `scripts/`). `CHANNEL_ROWS`'s dict keys (`name`, `affinity_key`,
`state_key`, `bias_key`, `gain_key`, `pathway_gain_key`) already match
`AffectChannel`'s node attrs 1:1, so the consumer loop simplifies to
`self.s.add_node("AffectChannel", dict(row))` — no second table, no
transform, one source of truth enforced by the import itself rather than a
comment.

## Predictions

1. `tests/test_affect_coupling.py`, `test_target_scoped_coupling.py`,
   `test_disposition_transport.py`, `test_bigville_ocelot_adapter.py` all
   pass unmodified, unchanged count — confirming byte-identical behavior
   after the dedup.
2. The full Phase A+B+C touched-consumer regression list stays at its
   established baseline (4 pre-existing, unrelated stale-`.so`-hash
   failures, everything else green).

## Does NOT claim

Does not claim `resolution_bins`'s float-vs-int representation is
"cleaner" in some abstract sense — only that it is behaviorally safe
everywhere it is actually read, verified by tracing every real consumer
rather than asserting it. Does not address Phase D (Phase 4's own
target-scoped self-consistency gap).
