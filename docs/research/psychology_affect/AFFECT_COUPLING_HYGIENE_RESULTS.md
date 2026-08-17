# Affect-coupling hygiene (Phase C) — RESULTS

Registered design: `AFFECT_COUPLING_HYGIENE_PREREG.md`. **Both predictions
confirmed; item 1 registered as investigated-not-a-bug, item 2 fixed.**

## 1. Live measurements

```
$ python3 -m pytest tests/test_affect_coupling.py tests/test_target_scoped_coupling.py \
    tests/test_disposition_transport.py tests/test_bigville_ocelot_adapter.py -q
30 passed   (unchanged count, unchanged from before the CHANNEL_ROWS dedup)

$ python3 -m pytest <full Phase A+B+C touched-consumer list, 22 files> -q
195 passed, 4 pre-existing failures (stale .so hash pins -- the same
                                      exact baseline established in
                                      LOG_WEIGHT_QUANTIZATION_RESULTS.md
                                      and unchanged since)
```

## 2. Item 1 — resolution_bins: no fix, traced and confirmed safe

Every real consumer already applies its own defensive `int()`/`round()`
cast before treating `resolution_bins` as a discrete count:
`effective_resolution_bins` (`worlds/bigville_can_beliefs.py:87`,
`return max(2, int(bins))`), `quantize_j`'s `bins` param (only ever called
with the already-int `eff_bins`, `build_resident_can_mt:187`), and
`decode_band`'s own `"resolution_bins": int(resolution_bins)`
(`domains/bigville_register_backend.py:78`). All 100 real cast100 residents
already draw integer values. **No change made** — the original design
review's characterization did not survive tracing to the actual consumers.

## 3. Item 2 — CHANNEL_ROWS dedup: fixed

`worlds/bigville_ocelot_adapter.py`'s `_AFFECT_CHANNELS` (a hand-written
4-row tuple, explicitly commented as needing to stay byte-identical to
`scripts/_build_affect_coupling_seed.py`'s `CHANNEL_ROWS`) is deleted.
The adapter now imports `CHANNEL_ROWS` directly — an established pattern
already used by several `domains/*.py` files importing from `scripts/`.
`CHANNEL_ROWS`'s dict keys match `AffectChannel`'s node attrs 1:1, so the
per-resident mint loop is now `self.s.add_node("AffectChannel", dict(row))`
— one source of truth, enforced by the import, not a comment.

## 4. Honesty notes

**Does establish**: the channel-table duplication risk named by the
original design review is real and now closed by construction (an import,
not a promise). Does establish that the `resolution_bins` finding, while a
reasonable thing to flag on first read (a bin-count attr conceptually
wanting to be an int), does not correspond to an actual defect anywhere in
the current codebase — reported honestly as a non-finding rather than
patched for the sake of closing the item.

**Does NOT establish**: that no OTHER hand-duplicated table exists
elsewhere in the tree (this rung only searched the two named items). Does
NOT address Phase D (Phase 4's own target-scoped self-consistency gap —
`affect_bias`/`spite_gain` have no real production consumer either).

## 5. Files

- `docs/research/psychology_affect/AFFECT_COUPLING_HYGIENE_{PREREG,RESULTS}.md` (new)
- `worlds/bigville_ocelot_adapter.py` (edited: `_AFFECT_CHANNELS` removed,
  `CHANNEL_ROWS` imported from `scripts._build_affect_coupling_seed`,
  the per-resident mint loop simplified)
