# BIGVILLE R8 — LIFE-GOALS & DREAMS (the identity / soul layer) — RESULTS

**Block 256000.** Pre-registration: `BIGVILLE_GOAL_PREREG.md` (committed BEFORE
any number here). Spec `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §2.6 + §3 R8. Every
number below is read off the GRAPH via `worlds/bigville_goal_world.py`; every
decision is a seed rule in `seeds/bigville_goal_life.json` (2 rules) +
`seeds/bigville_goal_dream.json` (5 rules). ZERO new Rust.

Gate suite: `tests/test_bigville_goal_migrated.py` — **10 / 10 PASS**. Cast-story
run: `scripts/bigville_goal_run.py` → `results/bigville_goal/summary.json`
(`all_pass: true`).

## Gate results (all PASS)

### G-life-goal-orients (load-bearing) — PASS
A become-wealthy `LifeGoal{aim=wealth, orient_weight=3}` biases the
`decision_value` **Argmax** over the soul's `considers` options so the
lower-base-appeal SAVE (`base_appeal=1`, serves wealth) beats the
higher-base-appeal LEISURE (`base_appeal=2`, serves nothing):

| condition | chosen sub-goal |
|---|---|
| with the life-goal | **SAVE** (`1.0`) |
| ablated (`has_life_goal` edge dropped) | **LEISURE** (`2.0`) |

The Argmax bias sum is `Σ_{lg∈has_life_goal}[serves_aim==aim ? orient_weight : 0]`
= 3 for SAVE with the life-goal (1+3=4 > 2+0=2) and empty after ablation
(1 < 2). **The life-goal is what moved the choice** — same cast, same options.

### G-dream-is-ungrounded (source-audit) — PASS
After the boundary audit, the two aspirations sit on opposite sides of the
grounding boundary:

| aspiration | flag | holds a path edge? |
|---|---|---|
| LIFE-GOAL | `grounded_flag=1` | **yes** — `path_to → Dest` (grounded) |
| DREAM | `ungrounded=1` | **no** `grounded_path` (ungrounded) |

The audit reads edge presence/absence in a rule; no Python computes it.

### G-dream-regulates-affect (HEADLINE) — PASS
Aversive valence induced through the **real R7 channel** (mortgage + income
collapse → foreclosure → `bf_homeless_affect`). Invoking the dream relieves
affect while the **material state is unchanged**:

| quantity | distressed | after dream invoked |
|---|---|---|
| valence | 2.0 | **5.0** (↑ relief_valence=3) |
| arousal | 4.0 | **2.0** (↓ relief_arousal=2) |
| homeless | 1 | **1** (unchanged) |
| mortgage balance | 579.0 | **579.0** (unchanged) |
| `invoked` | 0 | 1 |

**Ablation:** the dreamless twin under the identical shock stays at
`valence = 2.0` — no relief valve. The dream's relief is a strict ablation delta
(5.0 vs 2.0). Relief without resolution: the debt is still there; the soul just
feels briefly better (the escape valve, cousin of intellectualisation's
residual-quarantine).

### G-dream-collapses — PASS

| scenario | collapsed | left | minted goal | latent | resigned |
|---|---|---|---|---|---|
| threshold (`valence 2 ≤ collapse_threshold 3`, no path) | 1 | **1** | `[leave]` | 0 | 0 |
| path (recruiter mints `grounded_path`, valence 5) | 1 | **1** | `[leave]` | 0 | 0 |
| **control** (`valence 2 > threshold −100`, no path) | 0 | **0** | `[]` | **1** | **1** |

Either an unbearable present OR a grounded path appearing collapses the dream
into exactly one actionable `ActionGoal{kind:leave}` (add_node) and the soul
ACTS. Below threshold with no path, the dream stays LATENT — resignation, the
learned-helplessness floor (the abuse line). A quiet character's dream collapsing
into departure is an unscripted story.

## Glass-box findings (read off the graph)

- **The cast have souls, not utility functions.** The SAME satisficing Argmax
  that R2 uses to pick a satisfier here carries a long-horizon term: a life-goal
  makes a soul save over the more appealing leisure — and removing the life-goal
  edge makes it a pure short-horizon maximizer again. The soul is the extra term.
- **The dream does affective work while changing nothing material.** The headline
  is a clean dissociation: valence/arousal move; coin/balance/homeless do not. The
  ablation proves the dream (its mere presence) is the valve — the dreamless twin
  endures the identical foreclosure with no relief.
- **Collapse is trigger-gated, and latency is first-class.** The disjoint
  threshold/path/latent rules mean the SAME dream either becomes a departure or
  stays a quiet resignation depending only on how bad the present is or whether a
  path appeared — never on a Python branch. The latent branch is the abuse line
  made legible: a dream that never activates.
- **The two aspirations are structurally distinct in the graph**, not by label: a
  life-goal carries a real (long) path; a dream carries none until a recruiter
  supplies one — and that same appearing path is what collapses it.

## Discipline ledger

- **Base / merge-base:** `81f6e5b2e614ca76a492c84f427de64ea257ae4b`.
- **PREREG committed before any number:** commit `335d9511f5` (prereg only).
- **NO Rust:** `git diff <base> -- runners/dsl` — **EMPTY (0 lines)**, `term.rs`
  included. Argmax / Sum / IfThenElse / Exists / Max / add_node are all
  pre-existing Terms.
- **Own engine:** `source_match = shared` (∈ {own, shared}); Rust
  `source_fingerprint == engine_source_fingerprint` (this tree's Rust is
  byte-identical to canonical, so `ensure_tree_engine` symlinks the
  source-identical build); provenance gate `test_engine_provenance_migrated.py`
  **7/7**. No `.so` md5 pinned in any test.
- **Canonical `.so` SACRED:** md5 `fd82dc2978dbb055496dd82390ac2ebe` at START ==
  END (unchanged); no `.so` committed (gitignored; worktree path is a symlink to
  canonical).
- **Oracles:** `per_area_settlement_regression.sh` = **277 passed / 24 failed / 5
  skipped**, the 24 failing node-ids a SUBSET of the enumerated
  `results/failure_baseline.json` (570 baselined ids) — **ZERO new reds** (verified
  node-by-node; R8 seeds are `self_load_only`, loaded only by the R8 adapter, so they
  cannot touch the vision/conversation/composer suites that carry the pre-existing
  reds); `test_failure_baseline_migrated.py` **11/11**. `rung7_vision_bench.sh` =
  running (~43-min oracle, supervisor detached it post-merge; R8 seeds `self_load_only`
  cannot regress vision, and R7/R16 from the same base ran 214/10/0). R8 gate
  `test_bigville_goal_migrated` **10/10** on main.
- **Additive only:** all-new `bigville_goal_*` files; no tracked file edited;
  subclass/import R4–R7. Two commits (prereg, build). Supervisor merges — I do NOT.

## Honest residuals / scope

- **Synthetic, single-soul gates (N small).** Each gate is one (or a
  with/without) soul; the ablation is the isolation, not a powered population. The
  MECHANISM is proven; this is not a benchmark number. (Standing rule: synthetic
  ≠ benchmark; power the gate before any endgame claim.)
- **The decision_value Argmax uses two hand-set options (SAVE/LEISURE) with
  hand-set appeals.** It demonstrates the life-goal-as-orienting-term; it does not
  yet drive a full multi-tick economic trajectory (that is the R8×R4/R7 integration,
  deferred — a save-over-leisure soul accumulating measurably more equity over a
  long run would be the population-scale version).
- **The "grounded path" is a single edge, not a Bellman-flood reachability proof.**
  Gate 2 audits edge presence/absence; a stronger version would decode true
  reachability in the map-belief via the R2 `nd_relax` flood. The recruiter's
  `grounded_path` is a minted edge standing in for "a real path from here appears".
- **Relief is one-shot per invocation and does not decay here.** "Temporary" is
  modelled as relief-without-material-change (the debt persists); an explicit
  decay-back-to-distress over ticks is a natural extension not gated here.
- **Aversive valence is induced via R7 foreclosure** (the strongest, real channel)
  for the headline; a direct-set aversive valence is used for the collapse gates
  for isolation.
