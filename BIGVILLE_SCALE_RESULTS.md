# BIGVILLE SCALE-VERIFICATION — RESULTS (block 248000)

Pre-registered in `BIGVILLE_SCALE_PREREG.md` (committed BEFORE any number).
Base SHA `611bf0464f`. Own engine built in-worktree from committed Rust source
(zero Rust added). **N ≤ 30 is a FIRST scale probe — NOT the north-star's
200-inhabitant real-time claim; nothing here extrapolates past N = 30.**

Two deliverables: (1) 30 Bigville townspeople seeded once with heterogeneous
params + history (`seeds/bigville_townspeople_30.json`); (2) the scale probe
(`scripts/bigville_scale_run.py` over `worlds/bigville_scale_world.py`,
`results/bigville_scale/results.json`).

---

## HEADLINE

Realized interaction-ops per tick grow **LINEARLY (sub-quadratically)** in N.

| arm | fitted log-log slope | 95% CI | interpretation |
|---|---|---|---|
| **sparse** (realized, proximity/LOS-gated) | **1.162** | **[1.077, 1.253]** | linear / bounded-degree |
| **all_pairs** (control, gate removed) | **2.104** | [2.104, 2.104]* | quadratic (by construction) |

\* the all-pairs control is deterministic (`ops = N·(N−1)`), so its bootstrap CI
is degenerate.

**The two arms are CI-separated**: sparse 95%-CI upper `1.253` < all_pairs
`2.104`. The instrument demonstrably distinguishes linear from quadratic (the
all-pairs falsifier measures ≈ 2), and realized interaction lands firmly on the
linear side.

### Sparse realized-ops (mean over 30 placements × 12 ticks)

| N | mean ops | per-capita (ops/N) | wall-clock/tick |
|---|---|---|---|
| 5  | 5.27  | 1.053 | 1.18 ms |
| 10 | 13.23 | 1.323 | 1.64 ms |
| 15 | 21.20 | 1.413 | 2.18 ms |
| 20 | 29.53 | 1.477 | 2.33 ms |
| 25 | 35.00 | 1.400 | 2.88 ms |
| 30 | 42.30 | 1.410 | 3.23 ms |

Per-capita degree **saturates around ~1.4** — it does NOT climb toward `N−1` (the
all-pairs signature, which at N=30 would be 29). Bounded local degree, measured.

---

## GATES (all PASS)

- **G-linear (HEADLINE): PASS.** Fitted sparse slope `1.162 < 1.5` (and even the
  CI upper `1.253 < 1.5`). Sub-quadratic, as pre-registered.
- **G-instrument-can-detect-quadratic: PASS.** The all-pairs control slope
  `2.104 ∈ [1.8, 2.2]` — the instrument CAN measure a quadratic. The sparse arm
  is CI-separated below it (`1.253 < 2.104`). The sparse arm did **not** come out
  ≈ 2 ⇒ **no accidental all-pairs bug** in the scaffold/census.
- **G-population-not-cloned: PASS.** Every one of the 11 drawn params has non-zero
  sd at σ=1 (min sd = `0.0361`, w_spite); the σ→0 clone control has max sd
  `2.3e-16` (float noise = identical agents). Per-param sd (σ=1):

  | param | sd | param | sd |
  |---|---|---|---|
  | charm_weight | 1.551 | mood_bias | 0.278 |
  | w_supergraph | 0.993 | prior_world_safe | 0.145 |
  | w_spite | 0.036 | prior_others_trust | 0.175 |
  | cred_on | 0.131 | prior_self_worth | 0.136 |
  | claim_weight | 0.833 | difficulty_penalty | 0.393 |
  | hostile_weight | 0.452 | | |

- **G-discipline: PASS** (ledger below).

---

## FINITE-N HONESTY (load-bearing)

The **asymptotic** sparse slope is ~1.0, not 1.16. `ops = k·(N−1)` (each of N
agents perceives ~k local others; the `−1` is self-exclusion), so `ops ∝ (N−1)`,
whose log-log slope over N∈[5,30] is **1.105** — a pure finite-N artifact of the
small range, present in BOTH arms identically (it lifts all_pairs to `1+1.105 =
2.10` too). A small additional rise comes from per-capita climbing from 1.05
(N=5) to ~1.41 (N=30) as the perception window becomes a smaller fraction of the
growing torus and semi-saturation at N=5 relaxes. Net measured sparse slope
`1.162`. **The robust, artifact-free signal is the ≈1.0 GAP between the arms and
their CI separation**, not the absolute value of either slope. Reported, not
hidden.

## SECONDARY READ — wall-clock

Per-tick wall-clock for the full loop (`run_rules` over N Villager nodes +
realized-ops census + N nightly journals + the drama snapshot) grows from
**1.18 ms (N=5) to 3.23 ms (N=30)** — ~2.7× over a 6× population increase, i.e.
sub-linear-to-linear on this range; nothing blows up quadratically. This is the
observable that would fall behind first at true scale (a commodity-hardware,
N≤30 first read; NOT a 200-agent real-time claim).

---

## THE 30 TOWNSPEOPLE (Deliverable 1)

`seeds/bigville_townspeople_30.json` — 30 ORIGINAL characters in the **Terry
Pratchett / Discworld register** (the archetypal ANTI-NPC town = our "no NPCs"
thesis): guild/institutional politics, working people with dignity, comedy
grounded in real ethics, the Watch ("the law must apply even to the powerful" —
the constable role-slot; enforcement RULES are left to the sibling 247000 law
rung, NOT depended on here), the town paper (the "The Truth" archetype), and a
coldly-**COMPETENT** Town Clerk as a foil to John-the-malicious-mayor (competence
vs malice makes the psychopath seed legible). Original names + personalities in
the register — **no lifted named characters or place names**.

Mechanistic resonance, leaned into: Pratchett's *"sin is treating people as
things"* IS the psychopath seed — `w_supergraph → 0` = zero weight on others'
welfare. John draws the cast's **lowest** `w_supergraph` (0.16); the constable
and the competent Clerk draw high prosociality with low charm-susceptibility;
the pompous scrivener draws a high charm weight (flatterable). Params are drawn
`~Normal` (log-normal for positive scale params, logit-normal for [0,1] priors —
no clipped-tail artifact), scaled by `sigma_scale` (=0 ⇒ grand-mean clones). A
sparse relationship/history graph (22 edges over 30 people ⇒ mean degree ~1.5)
carries the feuds/loyalties/kin (Mary ↔ the Watch; the Clerk's & the Bugle's cold
war with the mayor; carpenters-vs-masons; butcher-vs-herbalist; the Cloot farm
family; John's charm already worked on the credulous councillors). Roles: mayor,
pastor, reporter, constable, Town Clerk (foil), 4 council, and the trades/
citizenry. Every inhabitant is a FULL agent (added as a real `Villager` graph
node processed by `run_rules`); no John/Mary special-casing in the machinery.

---

## DISCIPLINE LEDGER

- **Base SHA:** `611bf0464f` (merge-base verified; == origin/main).
- **Prereg SHA:** `ef5be45f1e` (prereg committed alone, before any number).
- **No Rust:** `runners/dsl` diff EMPTY (verified `git diff --stat` clean).
- **Own engine md5:** `10f65be659e0d9a9290aff39f7f5b92a` — **byte-identical to the
  block-245000/246000 own engine** ⇒ `source_match = own`, zero Rust added.
- **Canonical shared `.so`** (`runners/dsl/python/substrate_rs/_native.abi3.so`):
  md5 START `fd82dc2978dbb055496dd82390ac2ebe` == END (never written through;
  `engine_build.sh` uses `cp --remove-destination`).
- **Oracles:** `test_failure_baseline_migrated` GREEN (11 passed — the ENUMERATED
  node-id baseline, the authoritative "fail-set unchanged" gate per the CLAUDE.md
  retraction). Change is purely ADDITIVE (new files only; zero tracked-file
  modifications) ⇒ existing test outcomes cannot change.
  - **rung7 vision regression: 222 passed, 2 failed** (280 s;
    `results/bigville_scale/rung7_after.txt`). All 220 vision/paint tests GREEN;
    the 2 reds are the `engine_provenance` nodes only (below).
  - **The ONLY worktree reds in `rung7`/`per_area` are the 2
    `test_engine_provenance_migrated` nodes** (`test_loaded_engine_is_a_build_
    _of_THIS_TREES_rust_source`, `test_provenance_record_is_reportable`). These
    are a **worktree + venv `.pth` artifact**, NOT a regression: the venv ships a
    `substrate_rs.pth` pointing at the CANONICAL tree, so under the venv-`python`
    the provenance record's `this_tree` (worktree) mismatches the test's `ROOT`
    (resolved to canonical). This node is NOT in the main-tree enumerated
    baseline (it passes there, where worktree == canonical) and is independent of
    this additive change. **My measurements verifiably ran on the OWN worktree
    engine** (md5 `10f65be659…`, path under `bigville-scale-248000`, confirmed by
    loading `substrate_rs._native` through the runner's import chain) — the
    headline census is pure Python geometry anyway, engine-independent.
  - `rung7` completed cleanly (222 passed / 2 provenance-failed). A clean full
    `per_area_settlement_regression` re-run was blocked by heavy CONCURRENT
    PEER-SESSION bench contention this session (multiple pytest processes from
    sibling worktrees observed — the memory `ozma_instrument_discipline_lessons`
    "isolate bg agents" hazard); its earlier partial run showed exactly the SAME
    2 `engine_provenance` reds and no others (it shares rung7's file list + the
    provenance meta-test). The authoritative fail-set gate remains the ENUMERATED
    `test_failure_baseline_migrated` (GREEN).
- **Additive only:** all-new files, prefixed `bigville_scale_` / `bigville_town_`
  / `bigville_townspeople_` + the two `BIGVILLE_SCALE_*.md`. No existing tracked
  file edited; the scaffold `bigville_sim_world` / `bigville_drama_world` are
  imported/composed, never modified.
- **Gate test:** `tests/test_bigville_scale_migrated.py` — 8 passed.

---

## HONEST RESIDUALS / SCOPE

- **N ≤ 30 is a FIRST probe, NOT the 200-real-time claim.** The deliverable is
  the fitted exponent over 5→30 + the sparse-vs-all-pairs separation. No
  extrapolation to 200 is made; the wall-clock read is a first commodity-hardware
  observation, not a real-time guarantee.
- **Torus + constant density is a modelling choice** stated in the prereg (the
  correct bounded-degree model of a village), not a result. A walled bounded-grid
  would add perimeter/edge effects; the torus isolates the N-scaling.
- The measured sparse slope carries a **finite-N (N−1)/N lift (~0.1)** shared by
  both arms; the artifact-free signal is the ~1.0 inter-arm gap.
- **The scale census and the drama are on separate stages:** the seed-crystal
  political drama (John/Mary/reporter) runs on the scaffold's own 30×18 town each
  tick, while the N-population realized-interaction census runs on the constant-
  density torus. The townspeople are full `Villager` agents that back John/Mary
  and write journals; they do not yet drive their own spatial drama (a natural
  next rung).
- A synthetic MODEL of realized-interaction geometry; not a claim about real
  social networks and not new social science.
