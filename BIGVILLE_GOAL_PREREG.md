# BIGVILLE R8 — LIFE-GOALS & DREAMS (the identity / soul layer) — PRE-REGISTRATION

**Block 256000. Pre-registered BEFORE any recorded number.** Spec:
`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §2.6 (IDENTITY, LIFE-GOALS & DREAMS — why the
cast are not utility-maximizers) and §3 R8 (this gate). Builds ON R4
`bigville_econ_world` (coin / the debt + creditor-affect channel), R5
`bigville_loop_world`, R6 `bigville_skill_world`, R7 `bigville_fin_world`
(mortgage / foreclosure / homeless-distress — the channel that drives valence
aversive), the 204000/239000 affect seeds, and the substrate's `decision_value`
Argmax + grounding-boundary + collapse machinery. Reuse ALL by import; edit no
tracked file.

R8 gives each character two mental objects beyond the multi-tick goals of §2 —
both graph-native, both what stop a villager being a bare utility function:
a long-horizon GROUNDED **life-goal** at the goal-hierarchy root that ORIENTS
sub-goal selection, and an ungrounded high-valence **dream** (an ESCAPE fantasy)
whose function is AFFECT REGULATION and which may one day COLLAPSE into leaving.
Every decision — which sub-goal, the ungrounded audit, the dream-invoked relief,
the collapse-into-leaving, the latent resignation — is a seed RULE; the adapter
only arms one-shots, wires edges, ticks and reads.

## Seed-claim (run before anything; block 256 CLEAN)

```
SEED CLAIM 256-256: CLEAN -- no collision DETECTED.
  Scope: 973 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(The full block `seed_claim.py 256000 256999` is also CLEAN. R8 uses no
`default_rng` — it is deterministic — so it registers no measured draw.)

## What R8 adds (graph-native, ZERO new Rust)

Two additive seeds, composing ONLY existing DSL Terms (`Argmax`, `Sum`,
`IfThenElse`, `Neighbours`, `Exists`, `Max`, `Plus`/`Minus`, the comparators,
`add_node`). No new primitive.

- **`seeds/bigville_goal_life.json`** (2 rules) — the LIFE-GOAL layer.
  - **`gg_lifegoal_grounded`** — a life-goal is GROUNDED: a soul with
    `has_life_goal → LifeGoal → path_to → Dest` (a real, if long, path in the
    map-belief) and `audit_armed=1`, `grounded_flag==0` → `grounded_flag = 1`.
    One-shot via the done-guard (no disarm, so it never races the dream audit on
    the shared `audit_armed`). This is the grounded side of the boundary.
  - **`gg_orient_choice`** — G-life-goal-orients. On `orient_armed=1`, the chosen
    sub-goal is the substrate's `decision_value` **Argmax** (the SAME family as R2
    `nd_choose_good` / the drama's `ss_choose_burn`) over the soul's `considers`
    sub-options of
    `base_appeal(opt) + Σ_{lg ∈ has_life_goal} [opt.serves_aim==lg.aim ? lg.orient_weight : 0]`;
    write `chosen_subgoal = Argmax.code`; disarm.

- **`seeds/bigville_goal_dream.json`** (5 rules) — the DREAM layer.
  - **`gg_dream_ungrounded`** — the dream is on the UNGROUNDED side: a
    `has_dream → Dream` with `audit_armed=1`, `ungrounded==0`, and **no**
    `grounded_path` out-edge → `ungrounded = 1`. (A life-goal has `path_to`; a
    dream has none — the source-audited distinction.)
  - **`gg_dream_relief` (HEADLINE)** — AFFECT REGULATION. On `relief_armed=1`,
    dream not collapsed, and `aff.valence < dream.aversive_threshold` (the present
    is aversive): `aff.valence += relief_valence`, `aff.arousal = max(0, arousal −
    relief_arousal)`, `dream.invoked += 1`, disarm. **It writes ONLY affect attrs —
    NO material attr (coin / balance / homeless) is touched.**
  - **`gg_dream_collapse_threshold`** — present UNBEARABLE: `collapse_armed=1`,
    not collapsed, `aff.valence ≤ collapse_threshold`, and **no** `grounded_path`
    → `collapsed=1`, `latent=0`, `add_node ActionGoal{kind:leave, trigger:1}`,
    `add_edge has_goal`, `left=1`, disarm.
  - **`gg_dream_collapse_path`** — a recruiter minted a `grounded_path` (a real
    path from here appears): `collapse_armed=1`, not collapsed, `grounded_path`
    exists → `collapsed=1`, `latent=0`, `add_node ActionGoal{kind:leave,
    trigger:2}`, `add_edge has_goal`, `left=1`, disarm.
  - **`gg_dream_latent`** — the CONTROL: `collapse_armed=1`, not collapsed,
    `aff.valence > collapse_threshold`, and **no** `grounded_path` → `latent=1`,
    `resigned=1`, disarm (held, NOT acted — resignation / the learned-helplessness
    floor, the abuse line).
  - The three collapse/latent rules are DISJOINT (threshold: `valence≤thr` &
    no path; path: path present; latent: `valence>thr` & no path) — exactly ONE
    fires per collapse arm.

The adapter (`worlds/bigville_goal_world.py`) subclasses `BigvilleFinWorld` by
import (so aversive valence is induced through the REAL R7 foreclosure/homeless
distress), holds NO decision: it registers LifeGoal / Dream / SubOption /
ChoicePoint / Dest graph data + wires `has_life_goal` / `has_dream` / `considers`
/ `weighs` / `path_to` / `grounded_path` edges (ingest), ARMS one-shots (orient /
audit / relief / collapse), runs the Rust `run_rules` fixpoint, reads state back.

## Pre-registered gates (numbers filled in RESULTS after the run)

- **G-life-goal-orients (load-bearing):** a become-wealthy life-goal (high
  `orient_weight` on the SAVE aim) tips the decision_value Argmax so the
  lower-base-appeal SAVE (`base_appeal=1`, `serves_aim=wealth`) beats the
  higher-base-appeal LEISURE (`base_appeal=2`, `serves_aim=0`). **Ablation:** drop
  the `has_life_goal` edge → the Σ is empty → base appeal decides → LEISURE wins.
  PASS ⟺ `chosen_subgoal == SAVE` with the life-goal AND `chosen_subgoal ==
  LEISURE` after ablation (same cast, same options).

- **G-dream-is-ungrounded (source-audit):** after the boundary audit the DREAM
  carries `ungrounded=1` and holds **no** `grounded_path` edge, while the LIFE-GOAL
  carries `grounded_flag=1` and **holds** a `path_to` edge — the dream is on the
  ungrounded side of the grounding boundary, the life-goal on the grounded side.
  PASS ⟺ `dream.ungrounded==1 ∧ ¬dream.has_grounded_path` AND
  `lifegoal.grounded_flag==1 ∧ lifegoal.has_path`.

- **G-dream-regulates-affect (HEADLINE):** induce aversive valence via the REAL
  R7 channel (mortgage + income collapse → foreclosure → `bf_homeless_affect`
  drops valence, raises arousal). Invoking the dream gives TEMPORARY RELIEF
  (valence rises by `relief_valence`, arousal falls by `relief_arousal`) while the
  MATERIAL state is UNCHANGED (`homeless`, mortgage `balance` identical before and
  after the invocation). **Ablation:** a dreamless twin under the identical shock
  has NO relief valve (valence stays at the distressed floor). PASS ⟺ with-dream
  `valence_after > valence_before ∧ arousal_after < arousal_before ∧ invoked==1 ∧
  homeless/balance unchanged` AND dreamless `valence` stays at the distressed
  value (strictly lower than the with-dream post-relief valence).

- **G-dream-collapses:** (a) push `valence ≤ collapse_threshold` (present
  unbearable) → the dream COLLAPSES: `collapsed=1`, exactly one minted
  `ActionGoal{kind:leave}`, `left=1`. (b) a recruiter mints a `grounded_path` (any
  valence) → the dream COLLAPSES the same way (`trigger=2`). **Control:** below
  threshold (`valence > collapse_threshold`) + no path → the dream stays LATENT
  (`collapsed=0`, `left=0`, `latent=1`, `resigned=1`, no ActionGoal) — resignation.
  PASS ⟺ threshold-collapse leaves, path-collapse leaves, control stays latent
  (no leave-goal, `left==0`).

- **G-no-python-decision (source-audit):** the SEVEN soul-layer decisions are the
  seven rule names above; the adapter runs no Python rule engine
  (`graph_rewrite`/`gr._match`/`gr._apply`/`make_rule` absent) and never branches
  on a decision parameter (`chosen_subgoal`/`collapsed`/`invoked`/`ungrounded`/
  `left` do not appear in an adapter `if`). The Argmax/collapse verdicts live in
  seed `where`/`effects`, not executable adapter code.

- **G-discipline:** base/prereg on merge-base `81f6e5b2e6`; own-engine
  `source_match ∈ {own, shared}` (7/7 provenance); `runners/dsl` diff EMPTY (no
  Rust, incl `term.rs`); canonical `.so` md5 UNCHANGED start==end
  (`fd82dc2978dbb055496dd82390ac2ebe`); oracles `rung7_vision_bench.sh` (~214
  passed / 10 skipped / 0 failed) + `per_area_settlement_regression.sh` fail-set ⊆
  enumerated `results/failure_baseline.json` (ZERO new reds),
  `test_failure_baseline_migrated` green (11/11); all-new additive `bigville_goal_*`
  files, no tracked file edited; PREREG committed BEFORE any recorded number, BUILD
  committed after. Honest scope: synthetic model; single-soul gates (N small);
  mechanism-proven ≠ benchmark; the ablations are the isolation.

## Abandon / narrow criteria (pre-registered)

- **G-life-goal-orients** — if the Argmax picks SAVE **even after ablation** (the
  bias is not what moved it), or picks LEISURE **with** the life-goal, ABANDON the
  headline: the choice is not life-goal-driven. NARROW only if the effect holds for
  the become-wealthy aim but not a second aim — report it as aim-specific, not
  general orientation.
- **G-dream-regulates-affect (HEADLINE)** — if the with-dream invocation changes
  ANY material attr (`coin`/`balance`/`homeless`), ABANDON: it is not
  affect-regulation-without-resolution but a material intervention. If the
  dreamless twin's valence also recovers (no ablation delta), ABANDON: the relief
  is not the dream's doing.
- **G-dream-collapses** — if the LATENT control ALSO leaves (`left==1` with
  `valence > collapse_threshold` and no path), ABANDON: collapse is not
  trigger-gated. If a collapse mints ≠ 1 ActionGoal, NARROW and report the mint
  count.
- **Global** — any NEW red in the per-area oracle beyond the enumerated baseline,
  or a `runners/dsl` diff, or a changed canonical `.so` md5 → STOP and report; do
  not paper over.

## Discipline pre-commitments

- **Isolated worktree**; build + oracles here; supervisor merges (I do NOT merge).
- **NO Rust:** `runners/dsl` (incl `term.rs`) diff EMPTY. Every gate composes
  pre-existing DSL Terms — no new primitive.
- **Own engine:** the tree's engine is installed here (source-identical to
  canonical → `ensure_tree_engine` links it); assert `source_match ∈ {own,
  shared}`. NEVER pin a `.so` md5 in a test. Canonical `.so` untouched.
- **Additive only:** all-new `bigville_goal_*` files
  (`seeds/bigville_goal_life.json`, `seeds/bigville_goal_dream.json`,
  `scripts/bigville_goal_gen_seeds.py`, `worlds/bigville_goal_world.py`,
  `scripts/bigville_goal_run.py`, `tests/test_bigville_goal_migrated.py`,
  `BIGVILLE_GOAL_PREREG.md`, `BIGVILLE_GOAL_RESULTS.md`,
  `results/bigville_goal/summary.json`). No tracked file edited; subclass/import
  R4–R7. Explicit `git add <path>`. Two commits: (1) prereg, (2) build.
