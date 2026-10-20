# Cognition build — Phase 0 detailed plan: baseline and guardrails

Parent plan: `COGNITION_BUILD_PLAN_20261010.md` (§4 Phase 0). Task template and tiering are defined in the parent plan's §3. Phase 0 makes **no behaviour change**: no seed, Rust or boot-path edits, except P0.G1's single comment/list fix.

## Findings that shape this phase

These were read from the tree on 2026-10-10.

- **The baseline must be a list, not a count.** `scripts/failure_baseline.py` (`build` and `verify` subcommands; artifact `results/failure_baseline.json`) enforces "a list of node ids with last-green commits". `tests/test_failure_baseline_migrated.py` pins that discipline. P0.H1 uses this tool and does not invent a new format.
- **The full migrated suite is expensive.** The last full run took 3h09m with `-n 4` and stalled a worker (`GAMMA_REFLECTION_WIRING_RESULTS.md`). An earlier run at `-n 12` OOMed the machine. `pytest-xdist` is not installed in `.venv`. The phase gates use a targeted suite (§P0.H1) plus `failure_baseline.py verify`, not a full sweep per task.
- **`tests/conftest.py` already sets `OZMA_SEED_PERSIST_DISABLED=1`** through a session autouse fixture, so tasks do not need to export it.
- **Reads and writes can be extracted mechanically.**
  - Writes: `set_attr` / `add_edge` / `add_node` effects.
  - Reads: `match` triples, plus `Attr.key`, `Neighbours.edge_type`, `InNeighbours.edge_type` and `NodesOfType.node_type` inside `where` and inside `__term__` values.
  - Rust reads names through `interner.intern("…")`, which occurs about 1912 times in `runners/dsl/src`.
  - Python reads through `.get("…")`, `["attrs"]["…"]`, `.nodes("…")` and `neighbours(…, "…")`.
- **Known orphan-signal cases to assert in tests.**
  - `synthesis_requested` (`capability_collapse`) is an orphan.
  - `needs_decomposition`, both the edge from `impasse_escalation` and the attr from `repair_escalation`, is an orphan.
  - `needs_tool` is read by `self_extension.json:36`, so it is not an orphan.
  - `obs_established` is an orphan, but it is redundant with `obs_unassessable`, which `learning_progress_curiosity` does read. See P1 for that correction.

## Work items and tasks

### P0.H1 — Pin the regression baseline

**Targeted gate suite.** These files cover every seed that Phases 1–2 touch.

```
tests/test_frozen_core_invariant.py
tests/test_cognitive_architecture_integration_migrated.py
tests/test_dual_process_core_migrated.py
tests/test_default_mode_core_migrated.py
tests/test_generative_world_model_migrated.py
tests/test_episodic_working_memory_migrated.py
tests/test_capability_collapse_migrated.py
tests/test_capability_control_fabric_migrated.py
tests/test_counterfactual_experiment_migrated.py
tests/test_capkey_backfill_migrated.py
tests/test_arc_decompose_migrated.py
tests/test_cognitive_supervision_migrated.py
tests/test_aperture_frame_migrated.py
tests/test_learning_aperture_migrated.py
tests/test_cognitive_pareto_migrated.py
tests/test_arousal_horizon_migrated.py
tests/test_staleness_decay_migrated.py
tests/test_demotion_hierarchy_migrated.py
tests/test_core_emotions_migrated.py
tests/test_engine_provenance_migrated.py
```

| Task | Tier | Goal | Touch | Acceptance / verify |
|---|---|---|---|---|
| P0.H1.1 | T3 | Write the gate suite list as data | new `scripts/cognition_gate_suite.txt` (one test path per line, the list above) | File exists. Every path exists (`ls $(cat …)`) |
| P0.H1.2 | T3 | Run the gate suite at HEAD and record node-id results | none committed except the output in P0.H1.3 | `.venv/bin/python -m pytest $(cat scripts/cognition_gate_suite.txt) -q -rfE -p no:cacheprovider > /tmp/cog_gate_baseline.txt` completes |
| P0.H1.3 | T3 | Build the baseline list with the existing tool | `results/failure_baseline.json` only if the tool's `build` is designed to extend it; otherwise a new `results/cognition_gate_baseline.json` via the same `build` subcommand (read the `failure_baseline.py` docstring and argparse first) | `scripts/failure_baseline.py verify` on the new list reports 0 NEW and 0 STALE |
| P0.H1.4 | T3 | Rust baseline | doc only | `scripts/engine_cargo_test.sh --lib -- --test-threads=4` results recorded. Known: 836 pass, 1 fail (`substrate::tests::graph_rule_patch_node_receives_durable_commit_receipt`, which also fails at `2cd46a6a`) |
| P0.H1.5 | T3 | Baseline doc | new `docs/research/engine_substrate/COGNITION_BUILD_BASELINE.md` with commit, the commands, each failing node id with its class (known / pre-existing at commit X), and the Rust result | Doc lists node ids, not only counts |

- **Non-goals:** do not fix any failing test, and do not run the full `-k migrated` sweep.
- **Done when:** the baseline doc and list are committed, and `verify` is clean.

### P0.H2 — Orphan-signal lint

**Spec, written by the P0.H2.1 task.** The lint loads every `seeds/*.json` and collects:

- **WRITES:** `(kind, name)`, where kind is `attr`, `edge` or `node_type`. Sources:
  - `set_attr` effects: `attr` = arg 2.
  - `add_edge` effects: `edge` = arg 2.
  - `add_node` / `add_node_if_absent` effects: `node_type` = arg 2, plus `attr` for every key in arg 3.
- **READS** in seeds:
  - match triples: `edge` = middle element;
  - every `{"type":"Attr","key":K}` anywhere in `where` and in effect `__term__` values;
  - `Neighbours` / `InNeighbours` / `MapNeighbours` `edge_type`;
  - `NodesOfType` `node_type`.
- **READS** in code, by regex over `runners/dsl/src/**/*.rs`, `domains/**/*.py` and `substrate/**/*.py`:
  - `intern\("([A-Za-z_][A-Za-z0-9_]*)"\)`
  - `\.get\("…"\)`
  - `\["attrs"\]\["…"\]`
  - `\.nodes\("…"\)`
  - `neighbours\([^,]+,\s*"…"\)`
- **Orphan:** a WRITE whose name never appears as a READ. A rule reading its own write counts as a read, and that choice is documented in the script.
- **Output:** JSON `{name: {kind, writers: [seed:rule], reason?}}`, plus a human table.
- **Allowlist:** `scripts/orphan_signal_allowlist.json`, holding `{name: reason}` for known terminal or provenance-only attributes such as `provenance_kind` or `terminal_reason`.

| Task | Tier | Goal | Touch | Acceptance / verify |
|---|---|---|---|---|
| P0.H2.1 | T1 | Write the spec above into the script docstring and design the allowlist policy | `scripts/lint_orphan_signals.py` (docstring + skeleton `main()`) | Spec reviewed |
| P0.H2.2 | T3 | Write the test first | new `tests/test_lint_orphan_signals.py`: assert `synthesis_requested` and `needs_decomposition` are flagged; `needs_tool`, `has_memory_cycle` (read by EWM) and `obs_unassessable` are not; output is deterministic (run twice, compare) | Test fails (script not implemented) |
| P0.H2.3 | T3 | Implement seed read/write extraction | `scripts/lint_orphan_signals.py` | Seed-only part of the test passes |
| P0.H2.4 | T3 | Implement code-read regex scan | same file | Full test passes; runtime under 60 s |
| P0.H2.5 | T3 | Seed the allowlist with reasons and commit the first report | `scripts/orphan_signal_allowlist.json`, `docs/research/engine_substrate/ORPHAN_SIGNALS_20261010.md` (top 50 non-allowlisted orphans) | Report committed. Every allowlist entry has a reason |

- **Non-goals:** do not fix orphans in this phase.
- **Pattern to copy:** argparse plus a JSON-out script shape, as in `scripts/failure_baseline.py`.

### P0.H3 — Seed boot-status report

**Classification**, computed per seed id:

- **C:** in `substrate/boot_core.CORE_SEEDS`, or in the `depends_on` closure of CORE_SEEDS.
- **OPT:** in `OPTIONAL_CORE_SEEDS`.
- **Prof:** in `substrate/boot_profiles.CONVERSATION_SEED_ANCHORS`, or in its `depends_on` closure.
- **SLO:** `self_load_only: true`. Note that `load_all_seeds` skips SLO seeds even when they are explicitly selected (see `boot_all.py` load loop `if … d.get("self_load_only"): continue`). Only `boot_core` / `WorldAdapter(seeds=…)` / `manifest_for` load them.
- **Bulk:** everything else.

**Columns:** id, class, `depends_on`, executable rules (those with `match`), productions, declarative principles (head/body or if/then), concepts, guard hint (any `where` Eq on `enabled`, `*_on`, or a `Held*Params` / `*Policy` type), and broken deps (a dep with no seed file).

| Task | Tier | Goal | Touch | Acceptance / verify |
|---|---|---|---|---|
| P0.H3.1 | T3 | Implement the report | new `scripts/report_seed_boot_status.py` (stdout table + `--json`) | Runs in under 30 s over the ~854 seeds |
| P0.H3.2 | T3 | Test | new `tests/test_report_seed_boot_status.py`: `episodic_working_memory_core`→C; `dual_process_core`→OPT; `self_account_reply`→Prof; `core_emotions`→SLO; `compositional_plan`→Bulk; `llvm_passes` lists broken dep `llvm_ir_vocabulary` | Passes |
| P0.H3.3 | T3 | Commit the report and cross-check the assessment §4 table | `docs/research/engine_substrate/SEED_BOOT_STATUS_20261010.md`; note discrepancies against `COGNITION_CAPABILITY_ASSESSMENT_20261010.md` §4 | Each discrepancy is listed. Corrections go to the assessment in a separate T3 doc task |

**Known finding to carry forward.** `seeds/llvm_passes.json` and `seeds/llvm_ir.json` depend on `llvm_ir_vocabulary`, which has no seed file. That breaks the closure of `goal_derivation`: `goal_derivation` → `beta_evidence_threshold` → `causal_attitude_networks` → `compiler_theory` → `llvm_passes`. P1.H7 handles it.

### P0.G1 — Reconcile dual_process status

**Facts.**
- `substrate/boot_core.py:27-33` makes `dual_process_core` OPTIONAL.
- `runners/dsl/src/cognitive_cycle.rs` `run_unlabelled_legacy` doc comment says "`dual_process_core` is a core seed, so every default boot takes this plan", which is false.
- `boot_all._FROZEN_SEED_IDS` lists it as frozen, which means non-ablatable, not booted.

| Task | Tier | Goal | Touch | Acceptance / verify |
|---|---|---|---|---|
| P0.G1.1 | T1 | Decide: keep optional (recommended for Phase 0, because making it core switches every default boot to `CyclePlan::DualProcess` and changes scheduling for all unlabelled rules) or promote it. Record the decision with that reason | `docs/research/engine_substrate/COGNITION_BUILD_BASELINE.md` (decision section) | Decision recorded |
| P0.G1.2 | T3 | If kept optional, correct the Rust comment only (no code change) | `runners/dsl/src/cognitive_cycle.rs` comment above `run_unlabelled_legacy` — **blocked by parent-plan rule 4 only if engine files are dirty; a comment-only edit still needs `scripts/engine_build.sh` because `_native.build.json` hashes source** | `scripts/engine_build.sh --lib-only` then `tests/test_engine_provenance_migrated.py` green |

## Phase 0 gate

- All P0 tests pass.
- `failure_baseline.py verify` on the gate list is clean.
- The baseline, orphan and boot-status docs are committed.
- No seed or behaviour change except the P0.G1.2 comment.
