# Linear P10 results

Status: **executed and classified with limits**. The V1 held-out run is invalidated because the runner disabled `ProcessSchemaPolicy`, leaving runnable task graphs without domain-linked process schemas. V1 raw SHA-256: `db3767818b4d1149c2381354721762cb89a1947affc650fdf63d166445c0e217`; analyzer SHA-256: `eef45f361840a55d6bc17bc535824ab72dcf37d4bedd064c5e7da1287926c713`. Its all-zero action result is not used as capability evidence. V2 corrected the policy and added an affordance-installation gate, froze a separate protocol and fresh allocations, then ran the registered draw. V1 is retained as an invalidated protocol history, not silently replaced.

## Frozen V2 and artifacts

- Preregistration: [`COGNITION_LINEAR_P10_PREREG_V2.md`](COGNITION_LINEAR_P10_PREREG_V2.md), frozen before V2 held-out execution.
- Runner / analyzer hashes: `58bde4d96d109e68891b0ffd1ad9a01651841c016adf900536a3c280049f2a41` / `63754c428c912b939e22a958c2e39acd501959f2a43b89f6bb51dd2338a20a5b`.
- Agent/world/profile bundle: `21e3722b6ae56702fbe1ee68a599eed3f4b94ffd516b85e69e7ee7539f6544ea`.
- Native engine source / extension: `98c2cf56e92aaa73aedd6b8d36d55cd412f95152a51521c418b23810acbb14e6` / `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5`.
- V2 held-out runtime commit: `77fc64b34e71e58693b699c578e2ce20e346d8dc`; limits were 20 ticks, 1,000 rule steps per tick and 10 shared budget units per runnable task.
- Raw held-out scorecard: `/tmp/linear-p10-v2-heldout.json`, SHA-256 `6d8df15a512f5cb51e717e85bed43f6e1a2d512cb9fe7ae3df4ff23fa1f7df4d`.
- Analyzer output: `/tmp/linear-p10-v2-heldout-analysis.json`, SHA-256 `9ad57419490d10bfd96b5b9ac44bbf19218c6f1646b0d95e3d137e2517185e49`.

The held-out scorecard contains 4,100 rows: 200 tasks per arm in each of five world families (4,000 rows), plus 100 controls. Outcomes are:

| Family | Greedy | Discovered strategy | Other registered arms |
|---|---:|---:|---|
| Loopover 3×3 | 0/200 solved | 0/200 solved | Baseline and primitive search: 200 `UNSUPPORTED` each |
| Loopover 4×4 | 0/200 | 0/200 | Baseline and primitive search: 200 `UNSUPPORTED` each |
| Tool-goal composition | 128/200 | 128/200 | Baseline and primitive search: 200 `UNSUPPORTED` each |
| 2×2×2 cube | 0/200 | 0/200 | Baseline and primitive search: 200 `UNSUPPORTED` each |
| 3×3 sliding | `UNSUPPORTED` | `UNSUPPORTED` | All four arms unsupported because blank-adjacency preconditions are not enforced |
| Misleading-precondition controls | — | 100/100 passed | All emitted `needs_tool`; zero targeted ProcessSchema candidates |

Across the 800 supported paired tasks, each runnable arm solved 128/800 (16%). The paired discovered-strategy gain was **0 percentage points**, below the preregistered ≥20-point criterion: **FAIL**. All 128 successes were tool-goal cases, with exactly the same 128 cases solved by greedy. There is no evidence of a strategy-driven improvement. The discovered-strategy arm recorded 128 graph-held task traces after those tasks had already solved; its exact-context replay rule did not improve held-out solve rate.

The scorecard has 256 `COMPLETED` solved rows across both arms, 1,344 `FAILED` unsolved rows, 2,400 `UNSUPPORTED` rows and 100 completed controls. There were no timeouts or null statuses. The registered baseline cannot provide a Track-I-free native process solver; the primitive-search planner has no receipt-backed transition adapter for these worlds; sliding execution lacks a state-dependent legality check. These are unavailable comparisons, not zero-score baselines.

## Work, controls and limits

Each runnable arm executed 1,635 graph-selected process steps across its 800 tasks (mean 2.044 steps per task) and averaged two native ticks. Mean elapsed time, including world construction, graph boot and ticking, was 54.7 ms per greedy task and 62.5 ms per discovered-strategy task. Aggregate graph growth was 10,200 nodes for greedy and 13,016 for discovered strategy. The discovered arm recorded 128 task strategies; greedy recorded none. The per-task budget ceiling was 10 units, but remaining balance/debit was not serialized in the frozen scorecard. Separate boot-only timing and allocator memory are unavailable. The step counts refer to graph-internal simulator transitions; no external action sink or physical receipt was used.

All 100 controls ended `COMPLETED` with `needs_tool` and zero targeted candidates. The V2 audit found zero answer/scramble/strategy input leaks, zero missing primitive schemas in supported runnable graphs, zero trace nodes outside the graph, and zero native replay mismatches. Greedy and discovered-strategy arms received identical world-access hashes within each task. Tool-goal tasks contain only the initial state, goal and primitive tools; their generated witness sequences are discarded before graph installation.

Mechanism acceptance remains distinct from this outcome: bounded unseen-size lifting and goal-directed inverse invention pass their focused tests, and exact-context trace replay passes its graph tests. P10 did not establish general strategy transfer, an advantage over greedy, sliding legality, a primitive-search comparator, a Track-I-free solver baseline, human parity, or a whole L-level. The P10 held-out advantage criterion is `FAIL`, and those limits are retained for later phases.

## Verification and phase transition

After the frozen draw, the P10 acceptance/regression bundle passed **82 tests**:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest \
  tests/test_goal_invention.py tests/test_extended_thinking_migrated.py \
  tests/test_process_lifting.py tests/test_process_invention.py \
  tests/test_strategy_discovery.py tests/test_invariant_walls.py \
  tests/test_pmb_puzzle_worlds.py tests/test_linear_p10_v2_contract.py \
  tests/test_track_i_foundation.py tests/test_cognition_profile_integration.py \
  -q -p no:cacheprovider
```

P11 is authorized for its registered representation-proposal and cross-domain-map mechanisms using only verified ProcessSchema effects, exact source/epoch identity, and acquired P7 episode distinctions. P11 must retain the P10 zero-gain result and must not treat exact-context trace storage as transferable strategy evidence. No broad L2/L5 or human-level claim is authorized.
