# Feedback result provenance audit (2026-09-28)

## Scope

This audit checks the existing JSBSim F-16 Pareto result packet, since it is the strongest integrated feedback/control evidence linked from the capability inventory. It distinguishes replaying the saved outcomes from reproducing the simulator run. No test suite or flight simulation was run.

## Saved-result analysis replay

Command:

```sh
python3 scripts/analyse_f16_gate_block.py \
  --baseline results/jsbsim_f16_paper_replication_10hz_matrix_v3 \
  --candidate results/jsbsim_f16_paper_replication_10hz_pareto_frontier_v2
```

The analyzer reproduces the published table exactly from the eight retained JSON files. Each arm has 100 episodes in each of four scenarios, for 800 episodes per arm. The baseline and candidate use identical per-scenario seed ranges:

| Scenario | Frozen seeds |
|---|---:|
| nominal | 241102975–241103074 |
| jammed rudder | 241112975–241113074 |
| saturated elevator | 241132975–241133074 |
| damaged wing | 241172975–241173074 |

Replayed crash rates and Wilson 95% intervals:

| Scenario | v3 baseline | Pareto candidate | Replayed verdict |
|---|---:|---:|---|
| nominal | 0/100 [0.000, 0.037] | 0/100 [0.000, 0.037] | null |
| jammed rudder | 4/100 [0.016, 0.098] | 65/100 [0.553, 0.736] | candidate worse |
| saturated elevator | 16/100 [0.101, 0.244] | 73/100 [0.636, 0.807] | candidate worse |
| damaged wing | 42/100 [0.328, 0.518] | 73/100 [0.636, 0.807] | candidate worse |

The raw data also reproduce the reported tracking means and regime-engagement counts. This establishes the arithmetic/result-document consistency of the saved data, not the validity of the original simulator execution.

## Run-provenance findings

The saved scenario JSON records model, controller description, protocol parameters, scenario definitions, episode seeds, initial conditions, and outcomes. It does not record a source-tree hash, Python runner hash, native binary hash, dependency lock, or per-run source/runtime lock. The preregistration records the intended stack and frozen seed policy but likewise does not bind the powered run to exact source or binary digests. Therefore the original simulation run is not independently reproducible from its evidence packet as recorded.

Follow-up inventory enumerated all eight retained scenario files (four per arm): each contains 100 episode rows, and none contains an `episode_spec` or `manifest_hash`. The common numeric seed ranges therefore do not recover the exact historical exogenous input records needed for byte-identical replay.

The current checkout's engine build record reports binary SHA-256 `137358f8e6cdff8f89fc327091a76635c3d78f76df0d7d5b98ea8a10f1cc637d`, and the binary matches that record. However, the source has since moved: four recorded inputs differ from their current contents (`access_trace.rs`, `py.rs`, `scale_audit.rs`, and `substrate.rs`). The current artifact must not be used to claim a current-source reproduction until rebuilt. The result packet does not prove that this artifact was used for the historical run either.

The async cognitive-core result has a different provenance boundary: it names source/engine revisions `851fd92fb26a` and `04e5b0f43b50`, but those commit objects are absent from the current local Git object database. Its 3.11× speedup remains a historical reported result, not a current-checkout reproduction.

## Artifact digests

| Artifact | SHA-256 |
|---|---|
| Analysis runner `scripts/analyse_f16_gate_block.py` (current) | `25e8129359da84e2c1f2364a1dcad17e264ba5756659cb060b956d41177a9ca8` |
| Flight runner `scripts/jabberwock_jsbsim_f16_paper_replication.py` (current) | `292f50914839a5c0ebc1f6b84c4b8fd3d774b0b61973af066078bd0cc51b609e` |
| Preregistration | `7c1c9de88faa56866920d54a61d8d2ef5bf6350fa1e42f7f4240d986760cc9ca` |
| Results narrative | `9c9e8203ab42351b17a6c93d2bc1344ae78df74e829e7b1a1bb0f107e67c5a26` |
| Current native binary | `137358f8e6cdff8f89fc327091a76635c3d78f76df0d7d5b98ea8a10f1cc637d` |

The eight raw scenario file digests are:

| Arm / scenario | SHA-256 |
|---|---|
| v3 nominal | `3f4f30d55c1fd7a09d919293319e1364bf581caa9cc498606b73c6d8bc246046` |
| v3 jammed rudder | `63bb72eabe9841010dcc27d926fd8bc157be13e49eef04d469c6703bbe0df8a3` |
| v3 saturated elevator | `d83a5fa1b848d1a226fb24c9b8c4ad4d949b4b0e71b63867349f1baa1a90aa4b` |
| v3 damaged wing | `817284878508b67ded43227ecce5833430103bfb9b1a037419bb035785ac1f84` |
| Pareto nominal | `e1c03a21e0fd49f96d0c0f1a1fd149dd428558a74d85ef315529dcc48744ace1` |
| Pareto jammed rudder | `08a1eb51d7c85d59b9975484da8d8ca5fae1bc921d696e3da3c3028ff37f2bd4` |
| Pareto saturated elevator | `75440d482d04c1c240c844d92bce4dea781cc2918afa7cd4d13d738d640c40d3` |
| Pareto damaged wing | `e54c2b25bb6005ef2f0ef6f4b5f989b16c3b909c5f68cfbf2be706f0aa2e1bab` |

The digests can be rechecked with `sha256sum results/jsbsim_f16_paper_replication_10hz_matrix_v3/*.json results/jsbsim_f16_paper_replication_10hz_pareto_frontier_v2/*.json`.

## Interpretation and next gate

- **Verified:** the documented F-16 crash intervals, tracking means, and regime counts recompute from retained raw JSON under the current analysis script.
- **Not verified:** exact source/runtime that produced those JSON files; current-source simulator reproduction; whether the native binary at the time matched the described stack.
- **Retained result:** the saved candidate is clearly worse on all three fault cases at n=100 and null on nominal. Do not relabel this negative result as a standalone LQR/MPC/Kalman evaluation.
- **Next reproduction gate:** rebuild the native extension from the exact current source using `scripts/engine_build.sh`; freeze hashes for the binary, all source/config inputs, runner, dependency versions, preregistration, and manifests; then run a separately labeled pilot before any powered confirmation. Reuse the same frozen episode manifests across arms. The historical result remains separate and immutable.
