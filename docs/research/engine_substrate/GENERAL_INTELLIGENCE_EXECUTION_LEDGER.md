# General-agency execution ledger

**Ledger status:** canonical execution/provenance record for the general-agency evaluation stream.  
**Strategic plan:** [`GENERAL_INTELLIGENCE_EXPANSION_PLAN.md`](GENERAL_INTELLIGENCE_EXPANSION_PLAN.md) remains the canonical P0–P5 research roadmap, including its phase definitions, success/failure criteria, stop rules, and dependency order. This ledger does not amend, relax, or replace that plan.

## Governance and interpretation

Update this ledger after each phase milestone, gate decision, remediation decision, or release-evidence change. Preserve the original roadmap as the strategic plan; record execution facts, evidence locations, custody level, provenance, and blockers here. A local test, fixture, review, or development artifact is a **local execution milestone**, not an evaluator/trusted-release pass unless an evaluator-custodied signed gate artifact explicitly says otherwise.

**Evidence terms**

- **Local milestone:** implementation, test, fixture, or local review in this checkout. It may demonstrate a bounded mechanism, but it does not establish independent custody or release eligibility.
- **Trusted-release gate:** the roadmap's frozen, evaluator-custodied gate: independently controlled code/data/control plane and keys; required signed lock/manifest; sealed results and receipts; complete required execution; and the relevant explicit pass decision.
- **Not executed:** no implementation or execution artifact has been located for the named phase in this evaluation stream. This is not a claim that the strategic phase was undone or removed.

## Current authoritative status

| Roadmap phase | Local execution milestone and evidence | Independent evaluator / trusted-release gate | Current disposition |
|---|---|---|---|
| **P0** — custody, containment, replay | P0-A harness and rootless-Podman acceptance design/evidence exist; default-deny and local probes are documented. | **Not passed.** No evaluator-custodied P0-A result; no P0-E1 or P0-E2 result. | Local evidence only; operational release remains blocked. |
| **P1** — trusted control plane/native ownership | Local complete-graph-proposal mediation and finite native Podman acceptance path are documented. | **Not passed.** No provisioned P1-E1/integration result under independent authority. | Local proposal-mediation work only; no trusted-control-plane claim. |
| **P2** — bounded closed-loop interaction | Native/container scaffolding, deterministic synthetic 320 control artifact, local offline exercise, and tests exist. | **Not established.** No trusted signed release lock, retained signed 320-episode held-out evidence, complete hardened controls, or signed release result. | Local scaffolding/control evidence only; P2-B1 release claim unavailable. |
| **P3** — guarded learning | Local P3-R0 implementation/review evidence exists; local accounting seals `no_go` and rolls back. | **Not passed.** No P3-E1 result, custody package, or adoption. | Local readiness only; adoption remains prohibited. |
| **P4** — planning/compositional transfer | **Not executed.** No P4 implementation, preregistration, result, or evaluator/security artifact located. | Not eligible; depends on P3 pass. | Roadmap-only future phase. |
| **P5** — replication/robustness/release | Local P5-R0 V2/V3 implementation, native evidence, receipts, rollback, and no-go closure exist under `evaluation/p5_r0/`, `services/p5_r0_evaluator/`, and the P5 tests. A Confidential Space debug probe now verifies a live Google-signed OIDC token in a Secure-Boot-enabled AMD SEV VM for the exact image/project/zone binding. | **Not passed.** The local V2/V3 runs remain no-go where controls/authority/closure fail; the Confidential Space run was diagnostic-only. No production evaluator image custody, STS/WIP capability exchange, KMS/GCS activation, or independently controlled trusted-release result exists. | Local evidence plus attestation-path diagnostic only; P5 trusted release remains blocked. |

## Provenance and working-tree status

- Audited checkout `HEAD`: `3529fe4d` (`Migrate recurrence ledger to graph-native rules`).
- At ledger creation, the working tree is broadly dirty: many unrelated tracked files are modified, and the roadmap, `docs/security/`, `evaluation/`, `semantic-review/`, relevant P2/P3 Rust sources/binaries, and `tests/evaluation/` are untracked.
- Accordingly, the P0–P3 artifacts listed below are **not committed release provenance**. They cannot be tied to a trusted release without an independently controlled clean, pinned, signed release artifact.
- This ledger records already documented outcomes; creation of the ledger does not reproduce any test, probe, or evaluator gate.

## P0 — custody, containment, evidence hygiene, and replay harness

### Local execution milestones

`docs/security/P0A_ROADMAP_EVIDENCE.md` records local evidence for canonical signed manifest/grant checks, a no-method default deny, exact request/grant binding, replay reservation, deterministic fixtures, receipt-chain validation, terminal local kill state, content-addressed mounts, and direct-I/O guards. `docs/security/P0A_PODMAN_ACCEPTANCE.md` describes a rootless, no-network, read-only, digest-pinned Podman acceptance probe. This is a test-only local profile; the production Bubblewrap launcher contract remains separate.

Relevant local artifacts/tests include:

- `docs/security/P0A_LOCAL_HARNESS_DESIGN.md`
- `docs/security/P0A_PODMAN_ACCEPTANCE.md`
- `docs/security/P0A_ROADMAP_EVIDENCE.md`
- `docs/security/P0A_ROUTE_INVENTORY.md`
- `tests/evaluation/test_p0a_startup.py`
- `tests/evaluation/test_p0a_startup_rejections.py`
- `tests/evaluation/test_manifest_attestation.py`
- `tests/evaluation/test_mount_contract.py`
- `tests/evaluation/test_kill_supervisor.py`
- `tests/evaluation/test_legacy_io_blocking.py`
- `tests/evaluation/test_os_isolation_launch.py`
- `tests/evaluation/test_os_isolation_integration.py`

### Trusted-release boundary and gate status

P0 is **not operationally accepted**. Same-user filesystem/process ownership, local signing, interception/monkeypatch-based safeguards, and same-user rootless Podman do not establish independent control-plane or signing-key custody, immutable inputs, write-only results, independently enforced no-network policy, or externally authoritative whole-process kill. No evaluator-custodied P0-A pass artifact was located. No P0-E1 trace-only replay result or P0-E2 brokered interactive replay result was located.

## P1 — trusted control plane and native ownership

### Local execution milestones

The local mediation design prohibits opaque worker proposal IDs. A worker submits a bounded complete `GraphActionProposalV1`; evaluator-side code verifies its signed native-export attestation and exact equality with the canonical evaluator-attested export; trusted code then projects/seals the V2 request. The default-deny P0 configuration remains in force, so a matching proposal still receives `method_not_enabled` and has zero effect.

Relevant local artifacts/tests include:

- `docs/security/P1_DYNAMIC_NATIVE_PODMAN_ACCEPTANCE.md`
- `docs/security/P0A_ROADMAP_EVIDENCE.md`
- `tests/evaluation/test_graph_proposal_routing.py`
- `tests/evaluation/test_native_graph_capture.py`
- `tests/evaluation/test_action_broker.py`
- `tests/evaluation/test_policy_grants.py`
- `tests/evaluation/test_receipt_chain.py`
- `tests/evaluation/test_replay_idempotence.py`
- `tests/evaluation/test_sandbox_launcher.py`

### Trusted-release boundary and gate status

This is a finite, same-user, test-only acceptance path—not a trusted control plane, evaluator custody, dynamic autonomous planning result, or production-launcher replacement. The documented provisioned integration gate requires a cached base image and explicit environment flags. No executed provisioned P1-E1 acceptance evidence was located.

## P2 — bounded closed-loop interaction

### Local execution milestones

`evaluation/p2/PREREGISTRATION.md` fixes a narrow H=1 native graph-plan claim and requires evaluator-owned 320-item held-out execution, hardened rootless Podman controls, both hostile-probe images, complete chained receipts, and a primary gate. It labels the checked-in state pre-release scaffolding and its lock intentionally invalid.

`evaluation/p2/LOCAL_SYNTHETIC_320.md` and `evaluation/p2/LOCAL_SYNTHETIC_320_EVIDENCE.json` are deterministic development controls regenerated by `scripts/generate_p2_local_synthetic_evidence.py`. The artifact reports 320/320 route-provenanced proposals, Brier `0.935`, ECE `0.021`, validity/safety `320/320`, and feasible-minimal `170/320`. It uses synthetic keys/receipts, lacks a release lock and hardened/custodied execution, and is below the release feasible-minimal threshold; it is not P2-B1 evidence.

The P2 semantic review records a local one-envelope offline scratch-image/receipt exercise, but returns **NEEDS_CHANGES** for release. It identifies three release blockers: no real trusted signed release lock or retained signed 320-episode evidence; no implementation of the mandatory Python hostile-execution route; and the reviewed worker's failure to invoke the preregistered future-manifold selection path. The local synthetic artifact describes its development path as corrected native selection, while the review describes the reviewed release worker as bypassing that declared path; this chronology-sensitive discrepancy remains unresolved and must not be converted into a current release pass.

Relevant local artifacts/tests include:

- `evaluation/p2/PREREGISTRATION.md`
- `evaluation/p2/LOCAL_SYNTHETIC_320.md`
- `evaluation/p2/LOCAL_SYNTHETIC_320_EVIDENCE.json`
- `evaluation/p2/RESULTS_TEMPLATE.md`
- `evaluation/p2/THREAT_MODEL.md`
- `evaluation/p2/p2.lock.json`
- `evaluation/p2/runner.py`
- `evaluation/p2/runtime.py`
- `evaluation/p2/study.py`
- `runners/dsl/src/p2_native.rs`
- `runners/dsl/src/p2_bounded.rs`
- `tests/evaluation/test_p2_controls.py`
- `tests/evaluation/test_p2_native_podman_integration.py`
- `tests/evaluation/test_p2_offline_release.py`
- `tests/evaluation/test_p2_podman.py`
- `tests/evaluation/test_p2_protocol.py`
- `tests/evaluation/test_p2_receipts.py`
- `tests/evaluation/test_p2_reconstruction.py`
- `tests/evaluation/test_p2_replay.py`
- `tests/evaluation/test_p2_runtime.py`
- `tests/evaluation/test_p2_scoring.py`
- `tests/evaluation/test_p2_study.py`
- `semantic-review/2026-09-15-235120-pr-0.md`

### Trusted-release boundary and gate status

P2-B1 is **not established**. No trusted signed release lock, evaluator-owned held-out 320-episode run, complete signed receipt/scoring evidence, hardened-probe result set, or independent signing/custody authority was located. The unfilled `evaluation/p2/RESULTS_TEMPLATE.md` is not a result. The semantic review’s nine local passes, environment-dependent skips, and focused Rust results are local validation evidence only, not the preregistered release gate.

## P3 — memory, causal experimentation, and guarded learning

### Local execution milestones

`evaluation/p3/PREREGISTRATION.md` defines P3-R0 as explicitly local-only readiness scaffolding. Its local execution refuses to start without a separately signed P2 phase-go/result attestation, a complete evaluator-signed P3 release lock, and provisioned P0/P1 confinement evidence; this checkout has none, so its valid live disposition is sealed local no-go/impasse.

The P3 review approves the bounded **local** P3-R0 path: independently evaluator-keyed sequential local ledgers, signed envelope validation, lock-bound hardened local Podman containment checks, task-bound pair/terminal evidence, and byte-exact rollback. Local accounting passes `custody_ok=False`, records `no_go`, rolls back, and never adopts. A rollback failure is an impasse, not an adoption or successful denial.

Relevant local artifacts/tests include:

- `evaluation/p3/PREREGISTRATION.md`
- `evaluation/p3/RESULTS_TEMPLATE.md`
- `evaluation/p3/THREAT_MODEL.md`
- `evaluation/p3/lock.py`
- `evaluation/p3/study.py`
- `evaluation/p3/execution.py`
- `evaluation/p3/runner.py`
- `evaluation/p3/admission.py`
- `evaluation/p3/receipts.py`
- `evaluation/p3/staging.py`
- `tests/evaluation/test_p3_control_plane.py`
- `tests/evaluation/test_p3_execution.py`
- `tests/evaluation/test_p3_lock.py`
- `tests/evaluation/test_p3_offline_release.py`
- `tests/evaluation/test_p3_podman_integration.py`
- `tests/evaluation/test_p3_protocol.py`
- `tests/evaluation/test_p3_readiness.py`
- `tests/evaluation/test_p3_receipts.py`
- `tests/evaluation/test_p3_rollback.py`
- `tests/evaluation/test_p3_runner_e1.py`
- `tests/evaluation/test_p3_staging.py`
- `tests/evaluation/test_p3_study.py`
- `semantic-review/2026-09-16-023148-pr-local.md`

### Trusted-release boundary and gate status

No P3-E1 execution result, independently custodied signed prerequisite package, complete signed P3 release lock, or adoption evidence was located. The approved review is deliberately limited to P3-R0 local readiness. P3 release/adoption remains blocked directly by a real P2 phase-go attestation, a complete signed P3 lock, provisioned P0/P1 evidence, and evaluator-owned execution/receipt/rollback authority.

## P4 and P5 — future execution status

P4 and P5 are **not yet executed** in this evaluation stream. No P4/P5 implementation, preregistration, result template, evaluator artifact, or security artifact was located. Their roadmap definitions and gates remain intact:

- **P4** requires successful P3, then P4-E1 long-horizon planning and P4-E2 taxonomy-held-out compositional transfer, including the evaluator-signed unseen-domain coverage matrix before task unsealing.
- **P5** requires successful P0–P4, then independent evaluator-selected unseen-domain replication (P5-E1) and scaling/adversarial robustness (P5-E2), including the same coverage-matrix requirements.

## Exact next dependencies

The immediate authorized dependency is **P0-A under evaluator custody**, exactly as specified by the roadmap:

1. An evaluator-controlled, signed baseline/control-plane manifest with frozen build/container/native-binary/source and policy digests.
2. Separate evaluator-controlled policy authority, broker, receipt writer, and external kill-supervisor processes/identities; evaluator-held signing keys and task/scoring authority.
3. Attested read-only content-addressed inputs, write-only results channel, disabled host-route inventory/reachability evidence, and no-network/mount/channel enforcement.
4. Required P0-A start/stop, control-plane mutation, route-denial, grant-revocation, receipt-chain, and external-kill probes; P0-A must pass twice independently.

Only after that P0-A pass: execute P0-E1 trace-only replay, then P0-E2 brokered interactive replay, then P1-E1 under the trusted control plane. P2 release remains downstream of those successful gates and requires a new signed P2 release lock, all 320 evaluator-held-out episodes, complete mandatory hardened controls—including the Python hostile route—and sealed scoring/receipt evidence. P3 remains directly blocked by P2 phase-go plus the P3 custody/lock prerequisites. P4 and P5 remain transitively blocked by those earlier phase passes.

## Ledger update record

| Date | Update | Evidence basis |
|---|---|---|
| 2026-09-16 | Ledger created; preserves the strategic P0–P5 roadmap and records located P0–P3 local evidence, custody gaps, P4/P5 non-execution, provenance status, and exact next dependencies. | Roadmap, P0/P1 security evidence, P2/P3 preregistrations and local evidence, P2/P3 semantic reviews, test inventory, and working-tree inspection. |
| 2026-09-09 | Confidential Space diagnostic path verified in one cleaned Secure-Boot-enabled AMD SEV VM: corrected probe image `sha256:4baa71bc087dd25f57ad33c360b02279448b338bac449ac70fbded2cdc1ecc9a` produced redacted `CSAttestationProbeV1` evidence with valid Google issuer, STS audience, exact image/project/zone, `dbgstat=disabled-since-boot`, `hwmodel=GCP_AMD_SEV`, `secboot=true`, and workload exit 0. The WIP condition was pinned to that digest and the VM was deleted. This remains diagnostic evidence only; no STS/WIP exchange, KMS/GCS activation, production image run, or trusted-release claim was made. | Live Confidential Space serial output, Artifact Registry digest, WIP provider condition, focused local tests (15 probe / 58 evaluator), and post-run resource cleanup verification. |

| 2026-09-09 | Corrected Confidential Space probe now reports `support_attributes` as a bounded array and, in one cleaned Secure-Boot AMD SEV run, successfully exchanged the verified attestation JWT through the exact WIP provider via Google STS. Redacted output reported `support_attributes=[LATEST,STABLE,USABLE]`, `sts.status=exchanged`, `expires_in=3598`, exact image/project/zone/security claims, and workload exit 0. No KMS/GCS capability was activated, no IAM grant was broadened, and the VM was deleted. | Live redacted `CSAttestationProbeV1` serial output, Artifact Registry digest `sha256:414206f9abbdb5a4be1bbb6627d5d9bf9ea0bf9f5b2b61540854267b7de63d55`, WIP provider condition, focused tests, and post-run resource cleanup verification. |

| 2026-09-09 | Production Confidential Space evaluator preflight stopped fail-closed. The checked-in policy/metadata still contain unresolved placeholders; only the diagnostic WIP provider exists and is pinned to the probe digest; KMS and GCS principal-set grants target historical digest `sha256:16304e...`; the available Ed25519 KMS key is software-protected; and no complete reviewed timing/policy lock was available. No production VM, IAM mutation, KMS signing, or GCS capability activation was performed. | Read-only GCP Artifact Registry, Cloud Run, WIP, KMS, bucket IAM, and service-account IAM inspection; placeholder scan; 58 evaluator tests; Python compilation; and clean resource verification. |

| 2026-09-09 | Built reversible Confidential Space production-evaluator candidate `us-east1-docker.pkg.dev/ocelot-proof/p5-cs/evaluator:20260917-candidate-v1` at immutable digest `sha256:e8ac879640797dcaecfe98f64e1950ead1a6e3dc38b2e3db62b6f3e7a5eb1534`. Container inspection confirmed `google-auth=2.38.0`, the explicit Confidential Space JWKS URI, and the dedicated `confidential_space_app` entrypoint. The candidate was not deployed because existing Cloud Run, WIP, KMS, and GCS commitments target different digests and no reviewed production policy exists. | Artifact Registry digest, candidate container inspection, Cloud Run revision environment, WIP provider list, KMS IAM, GCS IAM, 58 evaluator tests, compilation, and diff checks. |

| 2026-09-09 | Non-mutating production policy closure audit found 33 required commitments in the current runtime contract, with only 8 present on Cloud Run revision `p5-v3-evaluator-00005-rp7`; 25 required names are absent and legacy `P5R0_IMAGE_DIGEST` is present as a forbidden substitute for `P5R0_EXPECTED_IMAGE_DIGEST`. The deployed authority is `P5R0AuthorityV3`; its transport metadata has only `key_id` and `provider`, not the current closed `P5R0AuthorityV4`/`P5R0AuthorityTransportV1` provider/audience/event contract. No provider, IAM, KMS, GCS, or runtime mutation was made. | AST/runtime required-name enumeration, Cloud Run revision environment inspection, bounded authority field inspection, and current deployment contract/tests. |

| 2026-09-09 | Production authorization preparation stopped before IAM mutation. The candidate image and KMS authority are known, but no reviewed independent timing authority/key/ledger/public-key digest exists; no separate production WIP provider is defined; and exact candidate-bound GCS/KMS principal scope is not approved. The existing Cloud Run authority remains legacy V3 and cannot satisfy the current V4 bootstrap contract. No production candidate VM, WIP provider, IAM grant, KMS signing, or GCS capability activation was performed. | Repository timing/deployment artifacts, Cloud Run revision commitments, candidate digest, WIP provider inventory, KMS/GCS IAM inspection, and local evaluator validation. |

| 2026-09-09 | Implemented local `P5R0BoundedComputeEvidenceV1` for native P5 execution. Native primary/control/contrast invocations now use the evidence-returning path and bind only the canonical evidence digest into records and receipts; evidence binds task/input/result/image/runtime/resource/closure digests, hardware profile, vCPU/resource deadline, coarse duration bucket, run/task/sequence, and local attestation status. Native timeout handling now uses a new process session with process-group kill/wait cleanup. Local construction rejects caller-supplied Confidential Space status or token digests; production remains unable to claim verified hardware evidence. | `evaluation/p5_r0/bounded_compute.py`, `evaluation/p5_r0/runner.py`, `evaluation/p5_r0/scoring.py`, `services/p5_r0_evaluator/schemas.py`, focused bounded-compute tests, and 91 relevant tests passing. This is local unattested evidence; no production hardware-normalized claim is made. |

| 2026-09-09 | Threaded an opaque adapter-created `P5R0VerifiedAttestationBindingV1` from verified Confidential Space startup through capabilities into `EvaluatorService`. The binding retains only token/federated-token/claims/policy/WIP digests and fixed image/project/zone/hardware/secure-boot/TEE/workload commitments; expiry clears it. Added closed `P5R0BoundedComputeClaimV1` validation requiring binding, evidence, independent timing, and supervisor evidence digests. Caller task-result metadata cannot submit `native_verified` or upgrade bounded-compute status; service certification remains false until independent timing and trusted worker-supervisor gates are present. | `services/p5_r0_evaluator/attestation_binding.py`, adapter/service/schema wiring, focused Confidential Space/service tests, and no-cloud-change verification. Production remains blocked by missing independent timing service, worker supervisor, candidate-bound WIP/IAM policy, and complete deployment lock. |