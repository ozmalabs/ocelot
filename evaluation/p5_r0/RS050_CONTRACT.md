# RS-050 local evidence contract

`RS050_CONTRACT.json` and `rs050_contract.py` define the smallest re-runnable repository-side contract for authenticated supervisor/resource evidence. The validator is offline and has no GCP or `gcloud` path.

## Contract

A candidate evidence object must be canonical/digest-bound and contain:

- run, lock, closure, and committed resource-profile digests;
- a supervisor identity commitment with an allowed authentication method;
- the existing closed `P5R0SupervisorEvidenceV1` aggregate;
- a non-empty, one-based, contiguous per-worker ledger binding task ID and sequence;
- worker exit, timeout, OOM, process-group kill, cleanup, and observed flags;
- per-invocation resource-observation commitments and evidence digests.

The validator requires every invocation to be observed and cleanup-verified. Timeout or OOM requires a nonzero exit, process-group kill, and verified cleanup. Aggregate count and lifecycle flags must equal the ledger; task IDs must be unique; all bindings and digests are recomputed.

## Claim boundary

`validate_rs050_evidence()` is intentionally structural only. It always returns `authenticated=false` and `promotable=false`. A digest is not an authenticated observation. `validate_authenticated_rs050_evidence()` requires the existing `NativeSupervisor` seam with `trusted=true`, `independent=true`, and both execution-evidence and bounded-compute validators. No repository fixture can satisfy that boundary by self-digesting its own evidence.

This contract does not create a supervisor identity, resource evidence, native result, production closure, release, adoption, independent evaluation, or promotion claim. A separately operated supervisor must provide and authenticate the ledger before any caller may use the authenticated validation path.

## Re-run

For a local artifact, run:

```text
python -m evaluation.p5_r0.rs050_contract --evidence /path/to/supervisor-resource-evidence.json
```

The command validates structure and prints a redacted report. It does not authenticate or promote the evidence. Missing or malformed evidence exits `2`. No cloud mutation is performed.
