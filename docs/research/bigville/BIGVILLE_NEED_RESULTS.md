# BIGVILLE R2 — NEEDS → GOALS + PREFERENCE / satisficing (block 250000) — RESULTS

**Status: built + gated, graph-native, ZERO new Rust. 2026-07-29.** Builds ON R1
(movement+energy, 249000) by IMPORT. Every pre-registered gate
(`BIGVILLE_NEED_PREREG.md`) is GREEN. Synthetic model on a small cast + the compact
town grid; mechanism-proven ≠ benchmark value.

## What landed

A DRIVE above threshold mints a spatial GOAL, and WHICH good the goal targets is the
substrate's own `decision_value` Argmax over REACHABLE satisfiers:

    value(good) = preference[villager][good] · need_urgency − cost_on · travel_cost

reusing the SAME Argmax family as 245's `ss_choose_burn`. The chosen good's source
cell becomes the R1 navigation target. Files (all additive, `bigville_need_`-prefixed):

- `seeds/bigville_need_drive_goal.json` — `nd_arbitrate` (competing-drives Argmax),
  `nd_form_sustenance_goal` / `nd_form_rest_goal` (the winning need mints its goal).
- `seeds/bigville_need_choice.json` — `nd_seed_here` / `nd_relax` / `nd_source_cost`
  (the choice-distance BFS flood over the walkable map-belief, a distinct `cdist`
  field so R1's `gdist` is untouched) + `nd_choose_good` (the preference/satisficing
  Argmax).
- `worlds/bigville_need_world.py` — the world adapter: subclasses R1's
  `BigvilleMoveWorld`, loads the reused 207000 `drives` seed + the two new seeds,
  registers goods/sources/prefs/drives as graph data, runs the rule fixpoint in R1's
  proven TWO PHASES (flood to fixpoint, THEN arm the pick), and mechanically wires
  the rule-chosen source cell as the R1 `seeks` target. No agent decision in Python.
- `tests/test_bigville_need_migrated.py` — 10 gates (below).
- `scripts/bigville_need_run.py` — the glass-box oracle → `results/bigville_need/need_gates.json`.

The urge `|v_d − c_d|` is computed by the REUSED `drives` seed's own `drive_urge`
rule (genuine import-reuse, not a re-implementation).

## G-preference-satisficing (HEADLINE — the flip on distance alone)

Apple-preferring villager (`pref: apple=5, bread=4, ale=1`), preference **HELD
CONSTANT**, at the town square. Only the orchard MOVES:

| orchard | source travel-costs (BFS) | value(apple) | value(bread) | value(ale) | **chosen** |
|---|---|---|---|---|---|
| **NEAR** (11,8) | apple 3, bread 3, ale 3 | 10·5−3 = **47** | 10·4−3 = 37 | 10·1−3 = 7 | **apple** |
| **FAR** (29,17) | apple 24, bread 3, ale 3 | 10·5−24 = 26 | 10·4−3 = **37** | 10·1−3 = 7 | **bread** |

**The choice flips APPLE → BREAD on travel-cost alone, preference unchanged.**
Satisficing EMERGES: the far orchard's travel_cost dominates so the reachable bread
wins despite the lower preference. Glass-box: *wanted apples, took bread — the orchard
was across town.*

### Failing controls (each MUST change the outcome — all confirmed)

| control | setup | chosen | proves |
|---|---|---|---|
| **preference ablated** (equal weights `3,3,3`) | far orchard | **bread** (a nearest, cost 3) — NEVER the far orchard | with preference flat, the NEAREST satisfier wins regardless |
| **travel-cost ablated** (`cost_on=0`) | far orchard | **apple** (top pref, at dist 24) | travel-cost is LOAD-BEARING — without it, top preference always wins |
| **ale-preferrer** (`pref: ale=6, bread=3, apple=1`) | same town, near orchard | **ale** (vs the apple-preferrer's **apple**) | preference is PER-VILLAGER, not global |

## G-drive-forms-goal

- A hungry villager (SUSTENANCE drive, `v_d=10, c_d=0` → urge 10 ≥ threshold 5) forms
  a **`get_food`** goal; the `drives` seed computed urge = 10.
- **Ablate the drive** (remove the Drive node, à la Harlow 233000) → no drive above
  threshold → arbitration finds nothing → **goal is `None`**.
- **Two competing drives → the higher wins** (the same Argmax family, `nd_arbitrate`):
  `SUSTENANCE.urge 10 > FATIGUE.urge 4` → **`get_food`**; invert to `SUSTENANCE.urge 3
  < FATIGUE.urge 9` → **`go_home`**. The higher drive's goal is the one formed.

## Coupling to R1

`test_chosen_source_becomes_the_r1_nav_target`: after the choice, the chosen orchard
cell is wired as the R1 `seeks` target and R1's proven flood+hop moves the villager
toward it (Chebyshev distance to the orchard strictly decreases). R2 sits ON R1.

## Gate ledger (`tests/test_bigville_need_migrated.py`)

**10/10 GREEN** — headline flip; pref-ablated; cost-ablated; ale-preferrer;
drive→goal; ablate-drive-no-goal; two-drives-higher-wins; chosen-source→R1-target;
source-audit (no rule engine / no Python decision in the adapter; the choice is an
Argmax rule; the arbitration is the same Argmax/MaxOver family); no-new-Rust +
engine-invariant (`source_match ∈ {own, shared}`, Term-vocabulary all standard).

## Discipline ledger

| item | value |
|---|---|
| base merge-base | `0bc0c206f95915b27385588ad978b26306e2d255` |
| prereg commit | `884b6af1` (separate, before any number) |
| seed block | 250000-250999, `check_claim` CLEAN (verbatim in prereg) |
| own engine md5 | `10f65be659e0d9a9290aff39f7f5b92a` (REAL file, not a symlink) |
| `source_match` | `shared` (Rust source identical to canonical — expected, since ZERO Rust change; invariant `{own, shared}` holds) |
| `runners/dsl` diff | **EMPTY** (no Rust; incl. `term.rs`) |
| canonical shared `.so` md5 | `fd82dc2978dbb055496dd82390ac2ebe` — **UNCHANGED start == end** (never touched) |
| rung7 vision oracle | **214 passed, 10 skipped, 0 red** (incl. `test_engine_provenance_migrated` GREEN in-worktree) |
| per-area settlement oracle | **278 passed, 23 failed, 5 skipped — all 23 failing node ids ⊆ enumerated `failure_baseline.json` (ZERO new reds)**; failing files are the pre-existing no-`data/`-symlink reds (topic_route_selfheal, gap_awareness, elaboration, composer_driver, cortices_tick) |
| new test | `test_bigville_need_migrated` 10/10 green; `test_failure_baseline_migrated` green |
| new reds | **ZERO** (fail-set ⊆ enumerated `results/failure_baseline.json`) |
| worktree | NON-nested (the supplied isolated worktree; no self-created nested worktree) |
| files | additive only, all `bigville_need_`-prefixed; no existing tracked file edited |

## Honest residuals

- **`conflicting_goals_default` is mislabeled for this use.** The spec/task named it
  for the two-drives arbitration, but it is a text-**disclaimer** codebook with NO
  rules (its "conflicting goals" = express-vs-avoid-social-cost in prose, not competing
  drives). The load-bearing directive — "reuse the SAME Argmax family, do NOT invent a
  parallel chooser" — is honored: `nd_arbitrate` is an Argmax/MaxOver over the
  villager's drives. The mislabeled seed is NOT loaded. Recorded, not hidden.
- **`goal_construction` reused by PATTERN, not by manifest load.** The drive→goal
  minting follows the create-visit-goal shape (a threshold-gated node-mint rule) but
  is authored as a self-contained R2 rule rather than loading `goal_construction.json`
  (whose rules key off a different node vocabulary). The genuine manifest-reuse is the
  `drives` seed (urge computation).
- **Two-phase decide (flood-then-pick) is an adapter sequencing choice**, not a
  decision: the delta-engine does not re-fire a rule whose only changing input is read
  in its EFFECT (not its match/where), so the choice is armed after the flood settles —
  exactly R1's proven flood-to-fixpoint-then-pick pattern. The DECISION is still the
  rule's Argmax.
- **Ablate-drive-no-goal is demonstrated on a FRESH villager** (drive removed before
  any decide). A villager that already minted a goal keeps that goal edge when its
  drive is later removed — correct (a formed goal is not un-formed by satisfying the
  need mid-flight); the load-bearing claim is "no drive above threshold ⇒ no NEW goal."
- **Integer-native travel-cost.** `cdist` is BFS hop-count (in-frame integer, per the
  frame/continuum invariant); the preference/urgency/cost arithmetic is integer. No
  float lives in a frame coordinate.
- Synthetic; N-scope = a handful of villagers, three goods, one 30×18 town. No claim
  about real economics. PRICE is deferred to R4.
