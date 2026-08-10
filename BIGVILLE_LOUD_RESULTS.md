# BIGVILLE R19 — UTTERANCE LOUDNESS & THE OBSERVE-vs-HEAR SPLIT (block 267000) — RESULTS

Measured build. Every number below is a graph read-off from the isolated comm
substrate; every DECISION is a seed rule (`seeds/bigville_loud_comm.json` +
`seeds/bigville_loud_class.json`). The adapter (`worlds/bigville_loud_world.py`)
only computes raw geometry (Chebyshev distance + occlusion via the scaffold's
imported `_line`/`OCCLUDERS` gate), ingests it, runs the rules, and reads state.
Loudness parametrizes the EXISTING earshot query — **no new Rust.**

Base SHA (merge-base): `a6bb0c0b623a44b6b37b2c12685e057cad2182ad`
Prereg: `BIGVILLE_LOUD_PREREG.md` (committed first).
Gate: `tests/test_bigville_loud_migrated.py` — **11 passed**.
Machine read-off: `results/bigville_loud/summary.json` (via
`python scripts/bigville_loud_run.py`).

## G-loudness-sets-hearing-radius — PASS

Speaker at (14,8) on the open east-west path; hearers at Chebyshev distances
{1,2,4,6,8,12} on the same clear row (no occluders → geometry isolates loudness).
`eff_loudness` (the rule-chosen radius) equals the chosen L; CONTENT reaches only
hearers within it:

| chosen L | eff (radius) | content reaches distances |
|---|---|---|
| 1 (whisper) | 1 | {1} |
| 3 | 3 | {1, 2} |
| 6 (normal) | 6 | {1, 2, 4, 6} |
| 12 (shout) | 12 | {1, 2, 4, 6, 8, 12} |

The received-set is monotone non-decreasing in L; a whisper reaches the nearest
hearer only, a shout reaches the whole row.

**Ablation (the falsifier) — `loudness_on = 0`:** every utterance uses the same
FLAT radius (6), so the content-set is `{1,2,4,6}` for EVERY L — independent of
loudness (flat earshot = the pre-change baseline). Loudness is load-bearing for
the radius.

## G-observe-vs-hear-split (HEADLINE) — PASS

A whispered exchange (L=1). `near` at d1 (inside the radius); `witness` at d5
(within sight range 7, clear LOS, outside the radius):

| perceiver | dist | observed_act | got_content |
|---|---|---|---|
| near | 1 | 1 | 1 |
| witness | 5 | **1** | **0** |

The distant witness mints the COMMUNICATION ACT (`observed_act==1`, a `CommAct`
node it `observes` — verified graph-native in
`test_commact_node_is_minted_graph_native`) but ingests NO content. Moving the
same witness inside radius(L) flips `got_content` to 1
(`test_observe_vs_hear_control_move_into_radius`). **Knowing-a-conversation-
happens is a first-class, separate fact from knowing-what-was-said.**

## G-loudness-is-seed-plus-choice — PASS

BASE + MAX are per-character seed axes (`eff` = the rule-chosen loudness):

| character | base | max | whisper (chosen 1) | SHOUT (chosen 100) | choice ablated |
|---|---|---|---|---|---|
| quiet child | 3 | 5 | 1 | **5** (capped) | 3 (= base) |
| booming publican | 8 | 15 | 1 | **15** (capped) | 8 (= base) |

A chosen shout is capped at the character's OWN max — no one exceeds their
ceiling. The **child shouting (5) still carries less far than the publican
speaking normally (8)** — population variation is real and load-bearing.
Ablating the choice (`choice_on=0`) returns each character to their seed base.

## G-privacy-is-physical (corollary) — PASS

Counsel spoken quietly (L=1). `confidant` at d1 (in the huddle); `witness` at d3
(sees the meeting, clear LOS, outside the whisper radius):

| perceiver | dist | observed_act | got_content |
|---|---|---|---|
| confidant | 1 | 1 | 1 |
| witness | 3 | 1 | **0** |

The witness SEES the meeting but never HEARS it — privacy is a PHYSICAL fact of
the hearing model (low loudness), not an honour promise. Secrecy (two conspire in
public by whispering) and private counsel are the SAME intent-neutral primitive.

## G-classroom-chatter (SCOPED PROXY; acquisition DEFERRED) — PASS (as scoped)

**HONEST SCOPE.** R18 (the school) is NOT built. This gate is built on a minimal,
self-contained teacher/child proxy using ONLY this rung's loudness machinery. The
`attending` scalar is a PROXY sink for the R17/R18 attention-gate; the true
acquisition/learning coupling ("learning proceeds / acquisition drops") is
**DEFERRED, needs R18**, and is NOT claimed here.

Teacher at (14,6); four children in a row at y=8 (`peer_pull=1`, `base=3, max=5`).

1. **Chatter** — each child whispers (L=1) to its peers. Content carries between
   adjacent children (distance 1 ≤ radius 1) → every child is distracted
   (`attending: 1 → 0` for all four). The teacher, at distance 2, receives the
   chatter reception `observed_act=1, got_content=0` — she **OBSERVES that the
   children are talking by line of sight but does not hear what they say.**
2. **Control (shout)** — the teacher emits a HIGH-loudness control utterance
   (L=12, `is_control=1`). It carries to every child (`got_content=1` for all) →
   `attending` returns to 1 for all four.
3. **Ablated control (whisper) — the falsifier** — the teacher's control at L=1
   does NOT carry to the (distance-2) children (`got_content=0` for all) →
   `attending` stays 0 for all four. **Chatter persists; classroom management
   fails.** The teacher's LOUDNESS is load-bearing — management EMERGES from the
   loudness model, it is not scripted.

## Discipline ledger

- `git diff a6bb0c0b62 -- runners/dsl` — **EMPTY** (no Rust, incl. `term.rs`).
- Canonical shared `.so` md5 START == END == `fd82dc2978dbb055496dd82390ac2ebe`
  (UNCHANGED; never committed). Engine resolved via the shared `.pth`;
  `test_engine_provenance_migrated` — **7 passed**, `source_match == shared`
  (no pinned-md5 assertion anywhere).
- `test_failure_baseline_migrated` — **11 passed** (additive `self_load_only`
  rung; enumerated baseline unchanged; ZERO new reds). The 43-min oracles
  (`per_area_settlement_regression.sh` / `rung7_vision_bench.sh`) were NOT run,
  per the 2026-07-29 directive — an additive `self_load_only` rung cannot regress
  another suite; the fast baseline gate + additive discipline are sufficient.
- Additive-only, ONE prefix `bigville_loud_`; no existing tracked file edited;
  `VISION_PROTOCOL.md` / `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` untouched. Both seeds
  `self_load_only`; adapter decision-free (source-audit gate green).

## Honest residuals
- **Classroom acquisition is a PROXY, not R18.** `attending` is a stand-in; the
  learning/acquisition coupling is deferred to R18. The first four gates are the
  full deliverable; this is the loudness-mechanism slice of the fifth.
- **Loudness → radius is a linear map** (loudness = the Chebyshev earshot radius
  in cells). Physical amplitude falloff / inverse-square is a modelling choice,
  not a claim; the mechanism (a seeded+chosen scalar parametrizing the earshot
  query, capped at a per-character max) is the point.
- **Occlusion is shared between sight and hearing** (same `OCCLUDERS` set on the
  Bresenham line); loudness scales only the RANGE, not the occlusion. A separate
  wall-muffle-attenuation model (partial hearing through a thin wall) is not
  built — occlusion is binary, as in the scaffold.
- **Synthetic small-cast model** on the imported 30×18 grid. Mechanism-proven ≠
  benchmark; N-scale is out of scope.
