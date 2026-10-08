# RS-069R15 provenance interpretation correction

This is a repository-local correction proposal for the successful R14 operation-1 evidence. It does not change the master runsheet, authorize a retry, or rewrite `var/p5-r0-rs069/operation-ledger.jsonl`.

## Supported evidence

- **Local build/provenance:** verified from the locked local build and provenance digest `sha256:46c113ffac8915cafe78f2ffaf8de5703150ddbe9fc8ee0d88868679754a1cc3`; this remains explicitly local.
- **Remote image identity:** the Artifact Registry digest describe observed `sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c`, matching the candidate digest. The successful R14 push and this remote digest verification remain in the append-only ledger.
- **Remote provenance/attestation:** `unknown` (`null`). The operation performed no remote provenance or attestation lookup, so local provenance cannot be projected as remote provenance. Evidence objects claiming `remote_provenance_verified=true` must carry a corresponding remote lookup reference and digest, otherwise the candidate loader rejects them.
- **Remote immutability:** `unknown` (`null`) in the corrected projection. A digest describe verifies image identity at an immutable digest reference; it does not observe repository immutability policy or prove that overwrites are rejected. The historical R14 `immutable_verified=true` field remains untouched as historical ledger data and is not repeated as a current supported claim.

The corrected candidate binding is `var/p5-r0-rs069r1/candidate-image-binding.json`. The ledger-adjacent interpretation artifact is `var/p5-r0-rs069/r15-provenance-interpretation.json`.

## Boundary and proposed state

R14 remains a successful operation-1 push/digest-verification event, with operations 2–7 skipped. R15 is a local projection/interpretation repair only: no `gcloud`, retry/push, KMS signing, GCS upload, deployment, VM, FreeTSA, task, or supervisor action was performed. Proposed runsheet state is `PASS_REVIEW` pending master review; the master-controlled runsheet itself is intentionally unchanged. The checkout remains dirty, so no clean release provenance or production-readiness claim is made.
