# P1 dynamic-native Podman acceptance

This is a test-only, same-user local acceptance path. It retains the P0A rootless Podman profile and does not change Bubblewrap-only production launching. It proves a finite native rule is evaluated twice from sealed bytes; it does **not** establish independent evaluator custody across users or machines.

## Finite closure

`NativeGraphClosureV1` names and SHA-256-digests exactly five regular, non-symlink files: `substrate_rs/__init__.py`, `substrate_rs/_native.abi3.so`, `native_graph_proposal_seed.json`, `native_sealed_graph_action_fact.json`, and `native_graph_entrypoint.py`. The closure digest is the manifest `agent_build_digest`; the sealed-facts file digest is the evaluation manifest `input_snapshot_digest`. The launcher copies only those paths into `site-packages/substrate_rs` and `/agent`, records every resulting context digest, and uses no source-tree copy, bind mount, package sweep, pull, compilation, or network.

Before a worker runs, the derived pinned image must import the staged native package at the exact expected paths and run the seed/facts load plus bounded native tick. Missing files, symlinks, changed digests, an unexpected loaded path, ABI import failure, or failed native execution is a failed gate. The P1 image/container names are nonce-scoped `localhost/p1-native-acceptance:<nonce>` and `p1-native-<nonce>`; cleanup inventories and removes only that exact pair.

## Data flow

1. The evaluator validates every closure byte and starts two fresh isolated native interpreters. Each creates a new `substrate_rs.Substrate`, loads the seed and sealed facts, and ticks at most 16 native rule applications.
2. The one seed rule matches the sealed root-to-fact edge with `phase: sealed` and uses native `add_node_if_absent` to emit its sole `GraphActionProposalV1`. It copies the ten proposal fields already sealed in the fact; it does not generate IDs, canonicalize JSON, or hash proposal data.
3. The evaluator rejects an exhausted fixed point, zero/multiple/invalid outputs, or byte disagreement between the two canonical proposal lists. Otherwise it builds `NativeGraphEvidenceExportV1` from its own capture and signs `NativeGraphExportAttestationV1`.
4. Only then does `evaluation_mode` validate the run/build/control/input attestation bindings and start the hardened worker. The worker independently loads the same staged seed/facts, executes the native rule, and emits exactly one existing `submit_native_graph_proposal` candidate frame.
5. `NativeGraphProvenanceVerifier` mediates only exact candidate equality with the evaluator export. It never attests a worker-export byte stream. The existing projector seals any matching request; P0 remains default-deny, so the accepted candidate gets signed `method_not_enabled` with zero effects.

The signed attestation binds `run_id`, `export_digest`, `agent_build_digest`, `control_plane_digest`, `input_snapshot_digest`, `capture_sequence`, `captured_at_unix_ms`, and the evaluator signing key/signature.

## Fail-closed outcomes

Closure validation failure prevents export creation and worker start (`native_closure_unavailable`). Native reconstruction disagreement, fixed-point exhaustion, or invalid proposal extraction prevents attestation/start (`native_capture_disagreement` or `invalid_native_capture`). A candidate substitution receives the existing signed `forged_graph_provenance` denial; a duplicate gets `replay` after the ordinary P0 denial. A worker attempt to carry an export or attestation is an extra forbidden protocol field and terminates with `sandbox_protocol_violation`. Stale, altered, or differently-bound exports remain rejected by the prelaunch attestation verifier.

Run the provisioned gate only with local prerequisites already present:

```bash
P0_RUN_OS_ISOLATION_TESTS=1 P0_OS_ISOLATION_PROVISIONED=1 \
pytest -q tests/evaluation/test_os_isolation_integration.py
```

A missing cached base image or failed native health probe fails this requested gate; it never falls back to a Python graph, host worker, precomputed candidate, opaque proposal ID, or action enablement.
