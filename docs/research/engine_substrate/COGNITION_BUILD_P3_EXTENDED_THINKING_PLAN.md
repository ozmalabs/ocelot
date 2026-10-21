# Cognition build — Phase 3 detailed plan: the extended-thinking executor

Parent plan: `COGNITION_BUILD_PLAN_20261010.md` (§4 Phase 3). The task template, tiering and ground rules are in its §1 and §3. This plan is written so that a **mid-range (T2/T3) model can complete Phase 3 without a frontier model**: every design decision is frozen below, and the few points that need a measurement first are written as **spike tasks** with a stated default.

## 0. State of play (checked 2026-10-10 at `306dfd6a`)

### What the interrupted session left

**Nothing usable.**
- There are no Phase-3 commits on any branch.
- No worktree, stash or untracked file contains Phase-3 work: all 15 worktrees, the stash list, the other clones under `~/ozmadev` and both `origin` branches were checked.
- No `extended_thinking` seed, script or test exists.

Phase 3 therefore starts from zero. If the interrupted session produced work that was never written to disk, it is lost.

### Phase 0–2, as built

Checked against commits `d83fa140`, `5b52a38b` and `1d5e63f9`, and verified by running the tests. All 67 tests across the 14 P0–P2 test files pass.

| Item | Status | P3 relevance |
|---|---|---|
| `tolerance_registry` (SLO, data only) | 5 Tolerance nodes. **No rule reads or writes them** | P3 must not use the commit knobs it lists (below) |
| `thinking_budget` | Generic pending-request contract (`tb_pass_when_disabled`, `tb_debit_request`, `tb_record_exhaustion`, `tb_deny_exhausted_request_after_denial`). **It has no producer yet**: the P1 bridges debit inline instead | P3 is the first producer of the generic contract |
| `SoftWeights` Term | Built, tested, documented in `SOFT_ADMISSIBILITY_RECIPES.md` | Not needed by P3's two targets; available |
| Aperture graded relax and questioning | Built; the pathology test passes | Pattern for "widen, re-check, keep or drop" |
| `ImaginedCandidate` (P1.A4) | **No consumer.** P1 Q1 decided to keep it advisory | Out of P3 scope; recorded in P3.0 |
| P2 results doc and gate evidence | **Missing.** No `COGNITION_BUILD_P2_RESULTS.md`, and no committed record that the P2 gate commands were run | P3.0 adds it |

### Findings that decide P3's design

1. **The parent plan's relax targets are mostly wrong.** From the as-built rules:
   - `settle_tolerance` (motor) is a **depth gate**, not a candidate filter. Raising it means thinking *less* (`mdc_shallow_settle` vs `mdc_residual_authorized_deepen`, `motor_decision_collapse.json:4731,4917`).
   - `conflict_margin` and `minimum_confidence` (dual-process) are **commit-permissiveness** knobs. Relaxing them makes the agent commit more readily, which is exactly the motivated-relaxation pathology.
   - `shape_match_tolerance` only changes a salience ranking and has no exact verifier.
   - `basin_threshold` (`dual_process_score_grounded_default`, `dual_process_core.json:285-336`) is a genuine admission gate. But re-admitting would mean re-opening an already escalated context in a frozen seed. **Deferred.**
2. **Two genuine "unsolvable at default, solvable when widened" targets exist.** Both have exact verifiers and both are already tested:
   - **(T-A) DimInfer grain ladder.** `agent.dim_grains` goes `[0]` → `[0,1]` → `[0,1,2]`. Fixture: `tests/test_geninfer_grain_migrated.py::test_held_generator_recognises_jittered_twin_only_at_coarser_grain`. At `None` the result is `minted`; at `[0,1,2]` it is `recognized_transformed` with `dim_grain == 1`.
   - **(T-B) GenInfer rung.** `agent.gen_infer_enabled` goes 0 → 1. Fixture: `tests/test_gen_infer_migrated.py`. With the flag off, SHEAR_A gives `minted`. With it on, it gives `recognized_transformed` plus a minted `genlin_*` generator, which **persists**, so a second encounter is solved at the default setting.
3. **`dim_grains` is read from the Agent first** (`sd_infer_dimension`: `ag.dim_grains`, else `has_dim_infer_policy → dim_grains`, else `[0]`). `tolerance_registry` points at `DimInferPolicy`, so writing the policy would be ignored whenever `ag.dim_grains` is set. **P3 writes the Agent attribute.**
4. **Rule effects cannot take an attribute name from data.** `set_attr` names a literal key. A single generic "relax any Tolerance" rule is therefore impossible without new Rust. P3 instead uses **one rule family per ladder**, with the rungs held as graph data. Only ladders declared in P3's own seed can ever be relaxed, which also locks the commit knobs out by construction.
5. **Re-admission is a targeted re-decode, using existing machinery.**
   - `sd_redecode` (frozen `shape_decode_loop.json:9106`) re-arms an Observation whose status is in {minted, recognized, recognized_transformed, recognized_duplicate} and whose `decoded_epoch < agent.codebook_epoch`. It clears `transform_*` and `dim_*` but **not `gen_*`**.
   - The spike found that a re-decode miss ends at `status == "decoded"`, which `sd_redecode` will not re-arm on a later rung. Before each rung's backdate, P3 sets that observation's status to `"minted"`, then sets `decoded_epoch = codebook_epoch - 1`. This re-arms that observation alone and avoids a global epoch bump.
   - The GenInfer ladder must also clear `gen_checked` and `gen_explained` itself.
   - `sd_mint_generator` requires the observation to have no `minted` axis edge. The GenInfer step temporarily moves any existing quantum edge to the episode, then restores it on a hit and marks the quantum axis superseded. This preserves the old candidate while allowing the frozen generator-mint rule to run.
6. **Frozen seeds.** `shape_decode_loop`, `dual_process_core`, `default_mode_core` and `generative_world_model` are in `boot_all._FROZEN_SEED_IDS`, meaning they are non-ablatable and unreachable by self-modification. **P3 edits none of them**. All new behaviour lives in a new seed that writes ordinary attributes those seeds already read.
7. **TimeInfer cannot be a rung yet.** An `Observation` carries one `signature`, not a frame sequence (`time_axis.json` needs `status=="motion_seq"` + `frames`). The time rung moves to Track I / P4. The quadratic GenInfer rung needs the non-default Cargo feature `geninfer_quadratic_map_solver`, so it is an optional decision (P3.D1.3).

## 1. Design (frozen)

### 1.1 New seed `extended_thinking`

The seed is produced by the generator `scripts/gen_extended_thinking_seed.py`.

- Top level: `id: "extended_thinking"`, `version: "1.0.0"`, `self_load_only: true`, `depends_on: ["shape_decode_loop", "thinking_budget"]`. `thinking_budget` brings in `default_mode_core`, which supplies the `NetworkModeState` clock.
- Every rule is `area: "extended_thinking"`, `latency_class: "hard_realtime"`.

**Nodes, all linked from `agent_root`:**

| Node | Attributes | Edge from agent |
|---|---|---|
| `ExtendedThinkingPolicy` | `name:"core_extended_thinking_policy"`, `enabled:0.0`, `step_cost:1.0`, `lease_epochs:4.0` | `has_extended_thinking_policy` |
| `RelaxLadder` (T-A) | `name:"dim_grain_ladder"`, `governs:"agent.dim_grains"`, `rungs:[[0],[0,1],[0,1,2]]`, `rank:1` | `has_relax_ladder` |
| `RelaxLadder` (T-B) | `name:"gen_infer_ladder"`, `governs:"agent.gen_infer_enabled"`, `rungs:[0.0,1.0]`, `rank:2` | `has_relax_ladder` |

**Runtime node types:**
- `ExtendedThinkingEpisode{status, ladder_name, rung_index, steps, opened_epoch, prior_value, from_cache, outcome}`. Status values: `open` → `awaiting_budget` → `probing` → (`hit` | `miss`) → … → `settled`. The terminal outcomes are `hit`, `exhausted`, `denied` and `expired`.
- `ExtendedThinkingStepRequest{status:"pending", cost, requester_kind:"extended_thinking"}`. This is the thinking budget's generic request.
- `ToleranceRelaxLease{governs, prior_value, relaxed_value, rung_index, valid_from_epoch, expires_after_epoch, status:"active"|"restored"|"expired"}`. It is an audit trail that is never deleted. The pattern copies capability_collapse's override leases.
- `ExtendedThinkingCacheEntry{key, ladder_name, rung_index, hits}`.

**Edges** (declare a `production` for each):
- `obs -has_extended_thinking_episode-> ep`
- `agent -has_extended_thinking_episode-> ep`
- `ep -relaxes_ladder-> ladder`
- `ep -has_step_request-> req`
- `req -draws_on_thinking_budget-> budget`
- `ep -has_relax_lease-> lease`
- `agent -has_extended_thinking_cache-> entry`

`ExtendedThinkingStepRequest -draws_on_thinking_budget-> ThinkingBudget` needs its own production, because the existing one is typed for `SystemTwoEscalation`.

### 1.2 Rules

Let **`unexplained(obs)`** mean:
- `obs.dim_checked == 1`, `obs.dim_explained != 1` and `obs.gen_explained != 1`;
- `obs.status` ∈ {`minted`, `decoded`, `recognized_duplicate`};
- `Count(obs.dim_types) > 0`.

The exact terminal status after a re-decode miss is confirmed by spike P3.A6.1.

Let **`settled_now(obs)`** mean `obs.et_settled_epoch == agent.codebook_epoch`.

Rules marked (T-B) have a T-A twin with the same shape, and vice versa.

| # | Rule | Fires when | Effects |
|---|---|---|---|
| 1 | `et_open_dim_episode` | `policy.enabled == 1`; `unexplained(obs)`; not `settled_now(obs)`; no `has_extended_thinking_episode` with `status != "settled"` on `obs`; no cache entry whose `key == ToJsonString(obs.key)` and `ladder_name == "dim_grain_ladder"` | Mint `ep{status:"open", ladder_name:"dim_grain_ladder", rung_index:0, steps:0, opened_epoch: mode.epoch, prior_value: ag.dim_grains, from_cache:0}`, plus the edges |
| 2 | `et_open_dim_episode_from_cache` | Same, but a matching cache entry `ce` exists | Same, with `rung_index: ce.rung_index - 1` and `from_cache:1`, so the first step lands on the cached rung. Set `ce.hits += 1` |
| 3 | `et_open_gen_episode` (T-B) | `policy.enabled == 1`; `unexplained(obs)`; `ag.gen_infer_enabled != 1`; the obs has a **settled** dim episode with `outcome == "exhausted"` and **no** gen episode | Mint `ep{ladder_name:"gen_infer_ladder", rung_index:0, prior_value: ag.gen_infer_enabled, …}` |
| 4 | `et_request_step` | `ep.status == "open"`; `ep.rung_index < Count(ladder.rungs) - 1` | Mint `req{status:"pending", cost: policy.step_cost, requester_kind:"extended_thinking"}`, add `ep -has_step_request-> req`, `req -draws_on_thinking_budget-> budget`; set `ep.status = "awaiting_budget"` |
| 5 | `et_apply_dim_step` | `ep.status == "awaiting_budget"`; `ep.ladder_name == "dim_grain_ladder"`; `req.status == "approved"` | Mint `lease{governs:"agent.dim_grains", prior_value: ep.prior_value, relaxed_value: IndexAt(ladder.rungs, ep.rung_index + 1), rung_index: ep.rung_index + 1, valid_from_epoch: mode.epoch, expires_after_epoch: mode.epoch + policy.lease_epochs, status:"active"}`. Set `ag.dim_grains = lease.relaxed_value`, mark the one observation `minted` to re-arm frozen `sd_redecode`, then set `obs.decoded_epoch = Minus(ag.codebook_epoch, 1)`. Set `ep.rung_index += 1`, `ep.steps += 1`, `ep.status = "probing"`, `req.status = "consumed"` |
| 6 | `et_apply_gen_step` (T-B) | As 5, for `gen_infer_ladder` | As 5, but set `ag.gen_infer_enabled = IndexAt(rungs, rung+1)`, temporarily move the existing `obs -minted-> CapabilityAxis` edge onto the episode so frozen `sd_mint_generator` can run, and **also** set `obs.gen_checked = 0`, `obs.gen_explained = 0` (finding 5) |
| 7 | `et_observe_hit` | `ep.status == "probing"`; `obs.status == "recognized_transformed"` | `ep.status = "hit"`, `ep.outcome = "hit"`. Set `obs.accepted_at_relaxed = ep.ladder_name` and `obs.accepted_rung = ep.rung_index` (provenance, so a relaxed acceptance is never passed off as a default-tolerance one). For every `obs -minted-> ax`, set `ax.superseded_by_extended_thinking = 1` |
| 8 | `et_observe_miss` | `ep.status == "probing"`; `unexplained(obs)`; `obs.decoded_epoch >= ag.codebook_epoch` (the re-decode has run) | `ep.status = "miss"` |
| 9 | `et_continue_after_miss` | `ep.status == "miss"`; `ep.rung_index < Count(rungs) - 1` | `ep.status = "open"` |
| 10 | `et_exhaust` | `ep.status == "miss"`; `ep.rung_index >= Count(rungs) - 1` | `ep.status = "exhausted"`, `ep.outcome = "exhausted"` |
| 11 | `et_budget_denied` | `ep.status == "awaiting_budget"`; `req.status == "denied"` | `ep.status = "denied"`, `ep.outcome = "denied"` |
| 12 | `et_settle_dim` (A7) | `ep.ladder_name == "dim_grain_ladder"`; `ep.status` ∈ {hit, exhausted, denied, expired} | Set `ag.dim_grains = IfThenElse(Eq(ep.prior_value, null), Attr(Pick(Neighbours(ag, has_dim_infer_policy)), dim_grains), ep.prior_value)`. For every active lease of `ep`, set `lease.status = "restored"`. Set `ep.status = "settled"` and `obs.et_settled_epoch = ag.codebook_epoch` |
| 13 | `et_settle_gen` (T-B) | As 12, for `gen_infer_ladder` | Restore `ag.gen_infer_enabled = IfThenElse(Eq(ep.prior_value, null), 0.0, ep.prior_value)`, and the rest as 12 |
| 14 | `et_cache_hit` (A7) | `ep.status == "settled"`; `ep.outcome == "hit"`; `ep.ladder_name == "dim_grain_ladder"` | `add_node_if_absent ExtendedThinkingCacheEntry{key: ToJsonString(obs.key), ladder_name, rung_index: ep.rung_index}` with `hits` left at its default, plus `agent -has_extended_thinking_cache-> entry`. The T-B ladder needs no cache: the minted generator already is the cache |
| 15 | `et_expire_lease` | `lease.status == "active"`; `mode.epoch > lease.expires_after_epoch`; `ep.status` ∉ {settled} | `ep.status = "expired"`, `ep.outcome = "expired"`. Rule 12 or 13 then restores |

**Ordering.** Use the `order` field: rules 1–3 = 10, 4 = 11, 5–6 = 13, 7–11 = 14, 12–13 = 15, 14 = 16, 15 = 9. The `thinking_budget` rules run at order 8–12 and approve the request between rules 4 and 5.

**Guards that must hold** (each one gets a test):
- (G1) **Only ladders in this seed can be relaxed.** No rule writes `conflict_margin`, `minimum_confidence`, `settle_tolerance`, `shape_match_tolerance` or `basin_threshold`.
- (G2) **Every step is funded.** No `ag.dim_grains` or `ag.gen_infer_enabled` write happens without an approved request.
- (G3) **Default tolerance is always restored after a terminal outcome.**
- (G4) **Disabled means byte-identical.** With `policy.enabled == 0`, no `ExtendedThinking*` node is ever minted.
- (G5) **Relaxed acceptances keep their provenance** (`accepted_at_relaxed`).
- (G6) **There is a bound.** Steps per episode ≤ `Count(rungs) - 1`, and there is at most one open episode per (obs, ladder).

**Known caveat (documented, not fixed in P3).** Restoring `ag.dim_grains` after a hit means a *later* global codebook growth re-decodes the observation at the default grain. That re-decode fails, and the obs re-opens an episode, which the cache then resolves in one step. This is intended, because default tolerance stays the default, but it costs a little each time.

### 1.3 Test fixtures to copy

- **T-A.**
  - Copy `tests/test_geninfer_grain_migrated.py` lines 70–100 (`DT3`, `_L`, `BLOCK`, `JIT`, `_rot`, `_dim_run`) and lines 103–109 (the expectations).
  - Boot: `s, ag = boot_core()`, `n = rf._native_eval2(s)`, `rf._ensure_shape_decode_loop(s, n, ag)`, then `n.load_seed_manifest(manifest_for("thinking_budget"), ag)` and `n.load_seed_manifest(manifest_for("extended_thinking"), ag)`. Alternatively boot `WorldAdapter(seeds=("extended_thinking",))` and set `agent.codebook_epoch = 0` by hand.
  - Feed a `NetworkModeSample` at epoch 1 so the clock exists. Copy `_sample` from `tests/test_default_mode_core_migrated.py:34-46`.
- **T-B.** Copy `tests/test_gen_infer_migrated.py` lines 44–92 (`DT`, `BASE`, `_lin`, `SHEAR_A`, `_boot`, `_run`), but leave `gen_infer_enabled` **unset**.

## 2. Tasks

Execute in order. Each task's acceptance must be green before the next starts. "Verify" means the task's own tests plus `scripts/cognition_gate_suite.txt` with no new failures (`.venv/bin/python -m pytest $(cat scripts/cognition_gate_suite.txt) -q -p no:cacheprovider`).

### P3.0 — Housekeeping (T3)

| Task | Goal | Touch | Acceptance |
|---|---|---|---|
| P3.0.1 | Write the missing P2 results doc. Run and record the P2 gate: `scripts/engine_cargo_test.sh --lib -- --test-threads=4` (known failure only: `graph_rule_patch_node_receives_durable_commit_receipt`), `tests/test_engine_provenance_migrated.py`, the gate suite, and the 14 P0–P2 test files. Record the as-built deviations from §0 | new `docs/research/engine_substrate/COGNITION_BUILD_P2_RESULTS.md` | The doc lists every command, its result and the commit |
| P3.0.2 | Record the open P1 decisions as deferrals. The `ImaginedCandidate` consumer moves to P5.E4 or Track I5. The parent-completion rule for `child_mean_saturation` moves to P5. The bridges' inline budget debit stays; P3 is the first user of the generic pending contract | `COGNITION_BUILD_P1_RESULTS.md` (append a "Deferred" section) | Committed |

### P3.A6 — Executor (relax, re-admit, re-verify)

**Spike P3.A6.1 result:** a targeted re-decode miss ends with `status="decoded"`, `dim_checked=1`, `dim_explained=false`, and `gen_checked=1`. The observation is reset to `minted` before that re-decode, so `decoded` is the post-miss status. `set_attr(..., None)` is stored and matches a rule's `Eq(Attr, Lit null)` predicate. The `unexplained()` set already includes `decoded`; no status expansion was needed.

| Task | Tier | Goal | Read first | Touch | Acceptance |
|---|---|---|---|---|---|
| P3.A6.1 | T3 | **Spike: terminal status after a targeted re-decode miss, and null attributes.** Using the T-A fixture with `dim_grains` unset: tick until `minted`, then set `obs.decoded_epoch = codebook_epoch - 1` and tick again with no grain change. Record the resulting `status`, `dim_checked`, `dim_explained` and `gen_checked`. Also confirm that `set_attr(ag, "x", None)` stores a None that a rule's `Eq(Attr, Lit null)` matches | `seeds/shape_decode_loop.json` rules `sd_redecode` (9106), `sd_dedup_existing` (8884), `sd_mint_quantum` (8319) | new `tests/test_extended_thinking_spikes.py` (two tests asserting the observed values) | Tests pass. If the observed miss status is not in {minted, decoded, recognized_duplicate}, add it to `unexplained()` in §1.2 and note the change in this doc |
| P3.A6.2 | T3 | **Tests first** (they will fail until P3.A6.3). (a) disabled ⇒ no `ExtendedThinking*` nodes and status `minted` (G4); (b) T-A: enabled ⇒ ends `recognized_transformed` with `dim_grain == 1`, exactly 1 step, `accepted_at_relaxed == "dim_grain_ladder"`, the original quantum axis has `superseded_by_extended_thinking == 1`, `ag.dim_grains` restored to its prior/default, and one lease with status `restored` (G3, G5); (c) scrambled control (random cells, same count as JIT, seeded) ⇒ the dim episode is `exhausted` after 2 steps, then the gen episode is `exhausted`, the obs stays unexplained, and the defaults are restored (G6); (d) T-B: enabled ⇒ the dim ladder is exhausted, the gen ladder hits after 1 step, a `genlin_*` generator is minted, and `ag.gen_infer_enabled` is restored; (e) budget: `ThinkingBudget.enabled = 1` with `remaining = 0` and `refill_per_epoch = 0` ⇒ episode `denied` with no grain write (G2); (f) G1: scan the generated seed JSON and assert that no `set_attr` names `conflict_margin`, `minimum_confidence`, `settle_tolerance`, `shape_match_tolerance` or `basin_threshold`; (g) re-ticking a settled episode changes nothing (fixpoint) | §1.3 fixtures; `tests/test_impasse_simulation_bridge_migrated.py:156-280` (structure) | new `tests/test_extended_thinking_migrated.py` | The tests exist and fail only for "seed missing" |
| P3.A6.3 | T2 | **Generator plus seed.** Implement §1.1 and rules 1–11 and 15. Builder idioms: copy the import block of `scripts/gen_impasse_simulation_bridge_seed.py:8-60` (it imports from `gen_capability_collapse_seed` and adds `Times`/`Minus`/`Lt`). Write a `main()` that writes `seeds/extended_thinking.json` with `json.dumps(…, indent=1)` | `scripts/gen_impasse_simulation_bridge_seed.py`, `seeds/thinking_budget.json` (request contract), `seeds/shape_decode_loop.json:405-810` (`sd_infer_dimension`) | new `scripts/gen_extended_thinking_seed.py`, new `seeds/extended_thinking.json` | P3.A6.2 (a)–(f) pass, except the settle parts of (b)–(d), which belong to A7. Add a regeneration test (copy `test_generator_reproduces_committed_seed_exactly` from the impasse test file) |
| P3.A6.4 | T3 | Profile wiring: add `extended_thinking` to `COGNITION_ON_SEEDS` (`substrate/boot_profiles.py:769-784`). Add an enabled `ExtendedThinkingPolicy` to `seeds/cognition_on_params.json`: copy the node with `enabled:1.0`, and add an `agent_root -has_extended_thinking_policy->` edge | `seeds/cognition_on_params.json` | those two files | `tests/test_cognition_profile_integration.py` green. Add one test there: under `boot_cognition_on()`, a T-A instance is solved and the budget is debited by exactly `step_cost` |

### P3.A7 — Settle back and cache

| Task | Tier | Goal | Touch | Acceptance |
|---|---|---|---|---|
| P3.A7.1 | T3 | Implement rules 12–14 in the generator and regenerate | generator + seed | P3.A6.2 (b)–(d) and (g) fully pass |
| P3.A7.2 | T3 | **Second-encounter tests.** (h) T-A: present the same `obs.key` and shape again as a fresh Observation ⇒ the episode opens `from_cache == 1` and hits in exactly 1 step at `rung_index == 1`, and `hits == 1` on the cache entry; (i) T-B: present SHEAR_A again on the same agent ⇒ it is recognised with **zero** episodes, because the minted generator is held and DimInfer explains it at default; (j) cache Occam check: a cached rung that is too fine for a new shape with the same key ⇒ the episode continues up the ladder from the cached rung and still terminates within the bound | `tests/test_extended_thinking_migrated.py` (append) | Tests pass |
| P3.A7.3 | T3 | Lint and status: run `scripts/lint_orphan_signals.py`. The new attributes `accepted_at_relaxed`, `accepted_rung` and `superseded_by_extended_thinking` will show as orphans (they are provenance only). Add them to `scripts/orphan_signal_allowlist.json` with reason "provenance; read by evaluation and audit". Run `scripts/report_seed_boot_status.py` and confirm `extended_thinking` is classed SLO | allowlist | Lint test green |

### P3.D1 — Inference ladder (re-scoped)

The DimInfer → GenInfer escalation is now delivered by the executor's two ladders (T-A, then T-B), with the minted generator as the persistent cache. What remains:

| Task | Tier | Goal | Touch | Acceptance |
|---|---|---|---|---|
| P3.D1.1 | T3 | **Ladder readout.** A new seed `inference_ladder_record` (generator `scripts/gen_inference_ladder_record_seed.py`, `depends_on: ["shape_decode_loop"]`, SLO). It contains one rule per terminal: for an obs whose `status` is `recognized_transformed`, write `obs.ladder_winner` = `"gen_linear"` if the obs has a `gen_minted` edge, else `"dim_grain"` if `dim_grain > 0`, else `"dim"`. For `status == "minted"` with no `gen_minted` edge, write `"quantum"`. Each rule is guarded by `ladder_winner == null` | new generator, seed and test | Tests on the four fixture cases (held rotation, JIT at `[0,1]`, SHEAR_A with gen on, scrambled) give `dim`, `dim_grain`, `gen_linear` and `quantum` |
| P3.D1.2 | T3 | Add `inference_ladder_record` to `COGNITION_ON_SEEDS` | `substrate/boot_profiles.py` | Integration test green |
| P3.D1.3 | T2 (optional) | **Quadratic rung decision.** Build with `--features geninfer_quadratic_map_solver` in a scratch target dir (`CARGO_TARGET_DIR=runners/dsl/target/quad`). Write the first quadratic2 test (`r'=r, c'=c+r²` on `BASE`, with `ag.gen_quadratic_enabled = 1`) and measure the full gate suite with that engine. Record "enable in default features: yes/no" with the evidence. **Do not change `Cargo.toml` defaults in P3**; that is a separate engine decision | test file `tests/test_gen_infer_quadratic_migrated.py` marked `skipif` when the feature is absent | Decision recorded in this doc |
| P3.D1.4 | — | **Time rung: deferred** to Track I (I4.2 latent-state invention) or P4, because Observations carry no frame sequence (finding 7). Record this in the parent plan | parent plan | Recorded |

### P3.H9 — Pre-registered held-out evaluation

These are randomised held-out instances, not fixtures. They are evidence about the *mechanism* on synthetic families, not about human-level capability. Name every artifact `extended_thinking_*` to avoid clashing with the unrelated `evaluation/p3/`.

| Task | Tier | Goal | Touch | Acceptance |
|---|---|---|---|---|
| P3.H9.1 | T3 | **Instance generators** (pure functions with a seeded RNG): **Family A** (grain): a random base made of 2×2 blocks from a random tetromino or pentomino; a random held transform (rotation90 with k ∈ {1,2,3}, or a reflection); 1–2 cells removed **inside** blocks, so grain-1 requantisation is unchanged (check this per instance and resample if it fails). **Family B** (gen): random integer 2×2 matrices with entries in [-2,2], det ±1, excluding the 8 dihedral matrices, applied to `BASE`. **Controls:** for A, random cell sets of equal count; for B, value-noise recolourings (`tests/test_gen_infer_migrated.py::test_value_noise_never_mints_a_generator` recipe) and the quadratic warp | new `evaluation/substrate_capability/extended_thinking_instances_v1.py` | Unit test: generators are deterministic per seed; every Family-A instance fails at grain 0 and passes at grain ≤ 2 (verified with the `DimInfer` Term directly) |
| P3.H9.2 | T3 | **Runner.** Usage `<this> <prereg_hash> <first> <end>`. Draw i uses seed `int(prereg_hash[:8],16) + 7919*i`. Arms: `et_on` (policy enabled, budget enabled with `capacity 16`, `refill 2`) and `et_off`. For each instance, boot a fresh agent, run to fixpoint (max 20 ticks, feeding one `NetworkModeSample` per tick), and record: solved (`recognized_transformed`), steps, budget spent, `accepted_at_relaxed`, false accept on controls. For the second-encounter metric, present the same instance again on the same agent and record steps. Write the output to `evaluation/reports/extended_thinking_heldout_v1_<hash8>_d<first>-<end>.json` (not committed). Structure: copy `evaluation/substrate_capability/prediction_world_heldout_v9.py:33-192` | new `evaluation/substrate_capability/extended_thinking_heldout_v1.py` | Runs a 10-instance smoke test in under 5 minutes |
| P3.H9.3 | T3 | **Analysis.** Exact McNemar test (paired on/off per instance) and a Wilson 95% interval for every rate. Copy the Wilson helper from `evaluation/substrate_capability/analyze_ls20_mapnav_current_source_scale_v1_2.py:70-74`, and copy the sign-test style from `evaluation/substrate_capability/prediction_world_sequential_analysis_v10.py:24-30`. It applies the decision rules of P3.H9.4 mechanically | new `evaluation/substrate_capability/extended_thinking_analysis_v1.py` | Unit test on a synthetic report |
| P3.H9.4 | T3 | **Pre-registration, committed alone before any draw.** Format: copy `PREDICTION_WORLD_HELDOUT_PROTOCOL_V10_20261010.md` (sections Why / What changed / Frozen at this commit / Procedure / Hypotheses / What this does and does not test). Draws: 200 Family-A, 200 Family-B, 100 of each control. The hypotheses are fixed in advance: **H1** (A) the solve-rate gain on−off ≥ 0.5, with McNemar p < 0.01; **H2** (B) the same; **H3** (guard) the false-accept rate on controls in `et_on` ≤ 0.05 (Wilson upper bound ≤ 0.10) and ≤ the `et_off` rate + 0.02; **H4** (cache) on solved Family-A, second-encounter steps < first-encounter steps in ≥ 90%; on solved Family-B, second-encounter steps == 0 in ≥ 95%; **H5** (budget) 0 steps applied without an approved request, and total spend ≤ total funding. List frozen files: the two seeds, the generator, the instances module, the runner and the analysis | new `docs/research/engine_substrate/COGNITION_BUILD_P3_PREREG.md` | Committed in its own commit; its hash seeds the draws |
| P3.H9.5 | T3 | Run, analyse and write up. Report every hypothesis plainly, including failures. Note that a Family-A false accept means coarse grain explained a random set, i.e. relaxation dissolved a real residual: the motivated-relaxation failure | new `docs/research/engine_substrate/COGNITION_BUILD_P3_RESULTS.md` (numbers inline, cite the prereg hash and the analysis command) | Committed |

**Execution result:** P3 implementation is committed as `32143620`; preregistration was committed alone as `eb34efb3` before the 0–200 draw. Results and gate evidence are in `COGNITION_BUILD_P3_RESULTS.md`. H1/H2/H3/H5 passed; H4 passed for Family B and failed for Family A because every generated Family-A case wins at rung 1, making the cached replay one step like the initial solve. The pre-registered criterion was not changed after observing results. The quadratic default-feature decision is **no**: keep the optional solver off pending a dedicated engine benchmark; no default features changed. TimeInfer remains deferred.

## 3. Phase-3 gate

- All P3 tests pass: spikes, executor, cache, ladder readout, and the integration addition.
- The gate suite shows no new failures against `results/cognition_gate_baseline.json` (`scripts/failure_baseline.py verify --list results/cognition_gate_baseline.json`).
- A default `WorldAdapter()` boot installs no `extended_thinking` or `inference_ladder_record` rules (assert this in the integration test).
- None of the frozen seeds have changed: `git diff --stat <P3 start>.. -- seeds/shape_decode_loop.json seeds/dual_process_core.json seeds/default_mode_core.json seeds/generative_world_model.json` is empty.
- The P3 pre-registration and results docs are committed. H1–H5 are reported whatever the outcome.
- `COGNITION_CAPABILITY_ASSESSMENT_20261010.md` §5 is updated: the request object, shared budget, graded relax (two ladders), re-admission (targeted re-decode) and settle-back/cache rows move from No to Yes, with the scope stated (grain and GenInfer ladders only).

## 4. What Phase 3 deliberately does not do

These are recorded so that later phases do not assume them:
- It does not relax commit knobs (finding 1).
- It does not re-admit dual-process candidates (frozen seed; this needs a re-open contract, and is P5 work).
- It has no time rung (finding 7).
- It makes no default engine change for quadratic GenInfer (P3.D1.3 is a decision only).
- It does not consume `ImaginedCandidate` (deferred).
- It has no Rust changes at all. Phase 3 is seed-, script- and test-only.
