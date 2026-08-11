# VISION — THE DEMOTION HIERARCHY: decay DEMOTES, it does not DELETE (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement
(PROTOCOL §3). Isolated worktree off `main` HEAD **`0657c63ba8`** (LEDGER 197000
— DISSIPATION IS INFERENCE). Engine canonical
**`793ce09ed498a749abb79aeaea44b92e`** (`_native.abi3.so`, shared build, Rust
source identical to this worktree — `source_match=shared`). This rung adds **NO
Rust**, `term.rs` diff EMPTY. Seed block **198000–198999**.*

Seed-claim check (verbatim, run before any number):

```
$ python scripts/seed_claim.py 198000 198999
SEED CLAIM 198000-198999: CLEAN -- no collision DETECTED.
  Scope: 897 files with seed sinks; 609 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

---

## 0. The claim — decay DEMOTES, it does not DELETE

Block 196000 (`seeds/staleness_decay.json`) established the shared integer
half-life DECAY ATOM: a trace carries integer `freshness = Ashr(C0, IDiv(now −
last_refresh, half_life))` — the `scale2` (x·2⁻ᵏ) halving read on the per-sensor
epoch axis. Today that freshness only FLAGS staleness (foveation) and
precision-weights a blend. It does not yet DO anything to the trace's
representation.

This rung adds the **DEMOTION HIERARCHY** on top of that atom. As freshness
decays WITHOUT refresh, a held trace does not vanish — it falls DOWN through
tiers to a COARSER representation and STAYS present and retrievable:

- **FRESH** (high freshness) — full detail / full precision.
- **GIST** (mid) — a COARSER summary: detail is SHED to a low-resolution code
  (bit-plane shedding — the integer-native LOD demotion), NOT zeroed.
- **LATENT** (low, incl. freshness→0) — a minimal presence marker: "something
  was here", still present, still promotable.

This is one mechanism wearing three names: the memory hierarchy
(registers→L1→…→disk), biological consolidation (episodic detail → semantic
gist), and cache eviction. **Re-observation PROMOTES a trace back UP** (DRAM
refresh / recall / re-attending), reversibly, recovering full detail *if the
incoming data supports it*. **Deletion is ONLY the fall off the bottom** — a
SEPARATE, high-order, rarely-fired faculty gated at the LATENT tier, **never
wired into the decay atom.**

The load-bearing invariant: **the decay/demote atom ONLY EVER DEMOTES. It never
deletes. freshness→0 leaves a LATENT trace, not an empty cell.**

## 1. Integer-native tier structure (C0 = 1024)

`freshness = Ashr(1024, IDiv(Δ, half_life))` (from 196000; integer, in-frame).
Tier is an integer code read off integer freshness thresholds:

| tier | code | freshness band | Δ/hl | stored representation | cost (bits) |
|---|---|---|---|---|---|
| FRESH | 2 | `freshness ≥ 256` | 0–2 | `detail` (full 8-bit, 0–255) | `BITS_FULL = 8` |
| GIST | 1 | `16 ≤ freshness < 256` | 3–6 | `Ashr(detail, 4)` (4-bit LOD code, 0–15) | `BITS_GIST = 4` |
| LATENT | 0 | `freshness < 16` (incl. 0) | ≥7 | `0` + `present=1` (presence marker) | `BITS_LATENT = 1` |

`T_FRESH = 256`, `T_GIST = 16`. All thresholds, the tier code, the stored
representation, and the bit costs are **integers** computed by integer Terms
(`Ashr`, `IDiv`, `IfThenElse`, `Gte`, `Eq`, `Lit`, `Attr`, `Var`). The GIST
coarsening `Ashr(detail, 4)` is a genuine **bit-plane shed** — an 8-bit detail
becomes a 4-bit low-resolution code; the low 4 bits (the detail) are shed. This
is the in-frame integer LOD demotion.

Reconstruction (a CROSS-FRAME render, allowed to be lossy/approximate):
`FRESH → detail` exactly; `GIST → Shl(stored, 4)` (coarse reconstruction, error
≤ 15); `LATENT → unknown, presence only`. The reconstruction is the only place a
value crosses frames; in-frame the stored code is integer.

## 2. The rules — all in `seeds/demotion_hierarchy.json`, default-OFF

The seed depends on `staleness_decay`. Every rule is gated on a `HeldTierParams`
node with `enabled == 1`, created ONLY by the opt-in measure adapter. Absent that
node, NO rule fires and every existing path is byte-identical. Rules operate on
`HierTrace` nodes (a decaying trace carrying `detail` + the 196000 freshness
bookkeeping fields).

**THE DECAY / DEMOTE ATOM (contains NO `del_node`):**

1. `dh_freshness` (order 2) — `freshness = Ashr(c0, IDiv(now_epoch −
   last_refresh_epoch, half_life))`. The 196000 atom, reused byte-structurally
   (same `Ashr` op tree as `sd_freshness_generic`).
2. `dh_tier` (order 3) — `tier = IfThenElse(freshness ≥ T_FRESH, 2,
   IfThenElse(freshness ≥ T_GIST, 1, 0))`. The integer tier ladder.
3. `dh_demote` (order 4) — the DEMOTION atom:
   - `stored = IfThenElse(tier==2, detail, IfThenElse(tier==1, Ashr(detail,4), 0))`
   - `bits   = IfThenElse(tier==2, BITS_FULL, IfThenElse(tier==1, BITS_GIST, BITS_LATENT))`
   - `present = 1`  ← **ALWAYS. This atom never deletes. freshness→0 ⇒ tier=0 ⇒
     present=1, stored=0, bits=1 — a LATENT trace, not an empty cell.**

**PROMOTE (the refresh — reversible recall):**

4. `dh_promote` (order 1) — on a NEW observation (`obs_epoch > last_refresh_epoch`):
   `last_refresh_epoch := obs_epoch`, `detail := obs_detail`. This resets the
   innovation clock (196000 `sd_gate` pattern) so the next `dh_freshness` →
   `freshness = C0` → `dh_tier` → FRESH → `dh_demote` → `stored = detail` (full
   detail recovered FROM the incoming observation). Reversible iff the data
   supports the detail.

**THE SEPARATE ORDER-N DELETION FACULTY (its own section, own flag, own high
order — the ONLY rule with `del_node`):**

5. `dh_delete_latent` (order 9) — `del_node HierTrace` **iff** `tier == 0`
   (LATENT) **AND** `HeldTierParams.delete_enabled == 1` **AND** an eviction
   condition (`now_epoch − last_refresh_epoch > evict_age`). Gated at the BOTTOM
   tier only; a separate flag (`delete_enabled`, default 0); a separate high
   order. Deletion is the fall off the bottom, never the decay itself.

## 3. Gates (pre-registered BEFORE any number)

**G1 — DEMOTION (headline).** Drive ONE trace, never refreshed, over increasing
Δ. Assert: `tier` steps 2→1→0 tracking the freshness thresholds; the stored
representation COARSENS (bits 8→4→1; reconstruction error grows monotonically as
detail is shed to gist then to a marker). **Assert freshness→0 leaves the trace
LATENT — `present == 1`, node still exists, `stored == 0` — NOT deleted.** Able
to fail if any transition is out of order, if bits do not shed, or if the node
disappears / present flips to 0 at freshness 0.

**G2 — PROMOTE-ON-REFRESH (reversibility).** Demote a trace to LATENT, then
re-observe it with its true detail. Assert it promotes back up (tier → 2) and
RECOVERS full detail (`stored == detail`, reconstruction error → 0). Measure and
report the full demote→promote→recover cycle (tier + fidelity trace). Able to
fail if promotion does not restore FRESH or does not recover detail.

**G3 — ORDER-N-DELETION SEPARATENESS + the delete-on-decay FALSIFIER.**
(a) Source-audit: `dh_freshness`, `dh_tier`, `dh_demote`, `dh_promote` contain
NO `del_node`; only `dh_delete_latent` (separate rule, separate `delete_enabled`
flag, order 9, LATENT-gated) does. (b) FALSIFIER: build an ALTERNATE atom
`dh_demote_DELETE_ON_DECAY` that wires deletion INTO decay (`freshness→0 ⇒
del_node`). Run a trace to LATENT, then re-observe it. Under the true hierarchy
the trace is present and PROMOTES (detail recovered); under delete-on-decay the
trace is GONE (node removed) and the promote→recover is impossible. Assert the
observables DIVERGE (recovered detail present under hierarchy, absent under
delete-on-decay; node-count drop). Proves demotion≠deletion is load-bearing.

**G4 — THE PAYOFF (capacity / graceful degradation at matched budget).** A
population of M traces observed once at staggered epochs, queried at a common
epoch (so freshness/tier spans FRESH..LATENT). At a MATCHED total storage budget
B (bits), compare:
- **FLAT keep-or-delete baseline** — a trace is either kept at FULL detail
  (`BITS_FULL` bits, retrievable) or deleted (0 bits, NOT retrievable, NOT
  promotable). Under B, keep the ⌊B/BITS_FULL⌋ freshest; delete the rest.
- **HIERARCHY** — each trace occupies `bits(tier)` (8/4/1) from the graph-native
  `dh_demote` output; if the sum exceeds B, evict from the LATENT tier upward.

Report retrievable-count and fidelity-weighted recall for BOTH across a budget
SWEEP (a real Pareto, not one point). Pre-registered success: at matched budget
the hierarchy RETAINS MORE retrievable/promotable content than flat-delete
(cheap coarse traces kept instead of deleted). **A measured null (hierarchy does
NOT beat flat at matched budget) is a valid honest landing and will be reported
straight.**

**INTEGER-NATIVE audit.** All decay/tier/demote/promote bookkeeping Terms lie in
the integer set `{Ashr, Shl, IDiv, Abs, Minus, Plus, Max, Min, Mod, IfThenElse,
Lt, Gt, Gte, Lte, Eq, And, Or, Not, Attr, Lit, Var}`; ZERO `{Div, Times, Exp,
Log, Sqrt}` in the bookkeeping. (The cross-frame reconstruction `Shl` is
integer; there is no float anywhere in this rung.) Assert 0 offending cells.

**DEFAULT-OFF byte-identity.** With no `HeldTierParams` node, no rule fires:
assert the 196000 staleness measure and the held surface are byte-identical
with vs without the `demotion_hierarchy` seed loaded, and the oracle
(`scripts/rung7_vision_bench.sh`) is BEFORE == AFTER.

## 4. Discipline

- **NO Rust; `term.rs` diff EMPTY.** Reuse `Ashr` / `Shl` / `IDiv` /
  `IfThenElse` / `Gte` / `Eq` and `del_node`; all exist. Canonical `.so`
  `793ce09e…` stays untouched (seed + Python-only). No Rust changes.
- **Python is a mechanical measure-adapter only** — builds the opt-in params
  node, submits observations, ticks, reads graph-native tier/stored/bits/present
  attributes. Every DECISION (freshness, tier, demote, promote, delete) is a
  graph RULE under `run_rules()`. No agent decisions in Python (CLAUDE.md).
- **Measure module IMPORT-INERT** — no top-level shared-state mutation; a scoped
  helper only.
- **Engine-semantics gate set** (lesson 12) green in one session; eye suite +
  `held_surface` + `staleness_decay` green. Oracle BEFORE == AFTER.
  `source_match` own/shared. Commit before report. Do NOT merge to main or touch
  VISION_PROTOCOL.md — the supervisor merges the ledger row.

## 5. Deliverables

Prereg hash; the tier structure + demote/promote rules + the separate order-N
deletion faculty; G1 demotion curve (tier transitions vs freshness; freshness→0
⇒ latent-not-deleted); G2 demote→promote→recover cycle; G3 separateness audit +
delete-on-decay falsifier divergence; G4 hierarchy-vs-flat capacity/recall at
matched budget (with sweep); integer-native audit (0 offenders); term.rs-EMPTY;
full engine-semantics gate + eye suite results; oracle BEFORE == AFTER;
default-OFF byte-identity; canonical-untouched; source_match. Raw numbers in
`VISION_DEMOTION_HIERARCHY_RESULTS.md` + `results/demotion_hierarchy/`.
