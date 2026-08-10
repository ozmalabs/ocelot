# VISION — THE DEMOTION HIERARCHY: decay DEMOTES, it does not DELETE (RESULTS)

*Prereg: `VISION_DEMOTION_HIERARCHY_PREREG.md` (committed ALONE first, commit
`3438ac025a`). Worktree off `main` HEAD `0657c63ba8`. Engine canonical
`793ce09ed498a749abb79aeaea44b92e` — **UNTOUCHED** (no Rust; `term.rs` /
`runners/dsl/src/` diff EMPTY). `source_match = shared`. Seed block 198000.*

Raw numbers: `results/demotion_hierarchy.json`; figure
`results/demotion_hierarchy/demotion_hierarchy.png`. Measure:
`scripts/demotion_hierarchy_measure.py` (import-inert; `main()` is the only
entry). Seed builder: `scripts/build_demotion_hierarchy_seed.py`. Gate:
`tests/test_demotion_hierarchy_migrated.py` (8/8).

---

## The build — tiers + demote/promote atom + a SEPARATE deletion faculty

`seeds/demotion_hierarchy.json` (depends on `staleness_decay`), all rules gated
on an opt-in `HeldTierParams.enabled == 1`, operating on `HierTrace` nodes:

| rule | order | role | deletes? |
|---|---|---|---|
| `dh_freshness` | 2 | `freshness = Ashr(c0, IDiv(now − last_refresh, half_life))` (the 196000 atom, reused) | NO |
| `dh_tier` | 3 | `tier = ite(freshness≥256, 2, ite(freshness≥16, 1, 0))` | NO |
| `dh_demote` | 4 | **the demote atom** — `stored`/`bits`/`recon`/`present` per tier | **NO** |
| `dh_promote` | 1 | on new observation: reset `last_refresh_epoch`, restore `detail` | NO |
| `dh_delete_latent` | 9 | **the SEPARATE deletion faculty** — `del_node` iff `tier==0 ∧ delete_enabled ∧ age>evict_age` | YES (only this) |

Tier structure (C0=1024, integer):

| tier | code | freshness band | stored | cost |
|---|---|---|---|---|
| FRESH | 2 | ≥256 | `detail` (8-bit) | 8 bits |
| GIST | 1 | 16–255 | `Ashr(detail,4)` (4-bit LOD code) | 4 bits |
| LATENT | 0 | <16 (incl. 0) | `0` + `present=1` | 1 bit |

## G1 — DEMOTION (headline): coarsen, never delete

One trace (`detail=173`, `half_life=1`), never refreshed, over rising epoch:

| epochs since refresh | freshness | tier | stored | bits | recon | recon err | present | node exists |
|---|---|---|---|---|---|---|---|---|
| 0–2 | 1024→256 | **2 FRESH** | 173 | 8 | 173 | 0 | 1 | yes |
| 3–6 | 128→16 | **1 GIST** | 10 | 4 | 160 | 13 | 1 | yes |
| 7–11 | 8→**0** | **0 LATENT** | 0 | 1 | — | (marker) | **1** | **yes** |

Tier steps FRESH→GIST→LATENT tracking the freshness thresholds; the stored
representation COARSENS (bits 8→4→1; the GIST code `173>>4 = 10` reconstructs to
`10<<4 = 160`, a genuine 13-LSB shed, error ≤ 15). **At `freshness = 0` the trace
is LATENT — `present=1`, node still exists, `stored=0` — NOT deleted.** The atom
demotes; it never deletes. ✅ (`g1_tier_monotone_down`, `g1_bits_shed`,
`g1_coarsens`, `g1_zero_is_latent_not_deleted`)

## G2 — PROMOTE-ON-REFRESH (reversibility)

Decay the trace to LATENT (`tier=0`, `stored=0`), then re-observe with its true
detail at a later epoch. It PROMOTES straight back to FRESH and RECOVERS full
detail: `tier 0→2`, `freshness→1024`, `stored = recon = 173` (the incoming data
supported the detail). A full demote→promote→recover cycle. ✅

## G3 — ORDER-N-DELETION SEPARATENESS + delete-on-decay FALSIFIER

**(a) Source audit.** `dh_freshness`, `dh_tier`, `dh_demote`, `dh_promote`
contain **NO `del_node`** (`atom_has_delete = {all False}`). The ONLY rule with
`del_node` is `dh_delete_latent` — order 9, behind its own `delete_enabled`
flag, gated at `tier==0`. Deletion is a separate faculty, never the decay. ✅

**(b) Falsifier.** An alternate atom `dh_demote_DELETE_ON_DECAY` (order 4, gated
only on `enabled`, `del_node` when `tier==0` — deletion WIRED INTO decay) run on
the identical decay→re-observe scenario:

| | reaches LATENT | trace before re-observe | HierTrace count | recovered on re-observe |
|---|---|---|---|---|
| **hierarchy (demote)** | yes | **present** | 1 | **173** |
| **falsifier (delete-on-decay)** | yes | **GONE** | 0 | **None** |

The observables DIVERGE: the hierarchy promotes and recovers the detail; the
delete-on-decay variant destroyed the trace before it could be promoted. Proving
demotion ≠ deletion is load-bearing. ✅

## G4 — THE PAYOFF: capacity at matched budget (+ honest fidelity tradeoff)

64 traces observed once at staggered ages, queried at a common epoch
(`half_life=8`), tiers read from the graph rules — histogram at the matched
budget: **8 FRESH / 10 GIST / 46 LATENT**.

**Matched budget = 150 bits** (the hierarchy's natural footprint to keep ALL 64):

| scheme | retrievable / promotable | fidelity-sum |
|---|---|---|
| **hierarchy (demote-not-delete)** | **64** | 17.49 |
| **flat keep-or-delete** | **18** | 18.0 |

At equal storage the hierarchy keeps **3.5× more traces retrievable and
promotable** — the 46 LATENT markers cost 1 bit each and CAN be promoted when
relevant again; the flat baseline deleted those 46 and can never recover them.
The hierarchy dominates flat on retrievable-count across the ENTIRE budget sweep
(64 vs 8 at B=64; 64 vs 24 at B=196; …) and is strictly greater over the
constrained regime. ✅ (`g4_hier_retains_more`, `g4_dominates_across_sweep`,
`g4_strict_somewhere`)

**Honest reported nuance (NOT gated).** Fidelity-SUM is a near-tie at the matched
budget (17.49 vs 18.0) and favours flat when budget is abundant: flat
concentrates its bits into few FULL-detail copies, while the hierarchy spreads
across full + coarse + markers. A flat "keep-few-at-full" scheme achieves
comparable fidelity-sum **only by concentration**, and only wins outright once
budget ≥ `BITS_FULL·M = 512` — i.e. when there is enough room that no hierarchy
is needed. **The demotion payoff is CAPACITY + promotability (graceful
degradation), not fidelity-sum.** This is the "leave the unresolved" point made
quantitative: a demoted-not-deleted trace is a cheap, promotable option the flat
baseline threw away.

## Integer-native audit

Every decay/tier/demote/promote/delete bookkeeping rule uses ONLY integer Terms;
`dh_demote` ops = `{Ashr, Attr, Eq, IfThenElse, Lit, Shl, Var}`. ZERO of
`{Div, Times, Exp, Log, Sqrt}` anywhere. `offender_count = 0`. In-frame integer;
the only shift-to-float-scale (`Shl` in `recon`) is the cross-frame LOD
reconstruction, itself integer. ✅

## Default-OFF byte-identity

With the `demotion_hierarchy` seed loaded but NO `HeldTierParams` node, no rule
can match: an eye ticked on identical photons is byte-identical with vs without
the seed — `node_count = 269`, every `RetinalColumn` cell's full attribute set
identical, `HierTrace` count 0. The opt-in is the only switch. ✅

## Discipline ledger

- **Prereg committed ALONE first** — `3438ac025a`, before any implementation or
  number.
- **NO Rust; `term.rs` / `runners/dsl/src/` diff EMPTY.** Reused `Ashr` / `Shl`
  / `IDiv` / `IfThenElse` / `Gte` / `Eq` / `del_node`; no new Term.
- **Canonical `.so` `793ce09e…` UNTOUCHED** (verified before/after). No rebuild
  needed on merge.
- **`source_match = shared`** (engine is the shared build, Rust source identical).
- **Python is a mechanical measure-adapter / seed-builder only** — every
  decision is a graph rule under `run_rules()`.
- **Engine-semantics gate set + eye suite** — see below.
- **Oracle BEFORE == AFTER** — see below.

### Engine-semantics gate set (ONE session)

`incremental_match`, `empty_match_proof`, `dirty_precision`, `per_sensor_epoch`,
`per_area_settlement`, `predicate_retraction`, `eye_binding_projection`,
`staleness_decay`, `dissipation_inference`, `held_surface`, +
`demotion_hierarchy`: **91 passed** in 273.51s (one synchronous session).

### Oracle (`scripts/rung7_vision_bench.sh`, data-less)

- BEFORE: **214 passed, 10 skipped** (159.36s).
- AFTER:  **214 passed, 10 skipped** (157.53s). **BEFORE == AFTER.**
