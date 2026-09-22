# General-agency execution ledger

**Ledger status:** canonical execution/provenance record for the general-agency evaluation stream.  
**Strategic plan:** [`GENERAL_INTELLIGENCE_EXPANSION_PLAN.md`](GENERAL_INTELLIGENCE_EXPANSION_PLAN.md) remains the canonical P0–P5 research roadmap, including its phase definitions, success/failure criteria, stop rules, and dependency order. **Requirements baseline:** [`P5_ATTESTED_RESULT_REQUIREMENTS.md`](P5_ATTESTED_RESULT_REQUIREMENTS.md) defines the detailed self-custodied attestation, timing, input, closure, evidence, failure, resource/OOM, and claim-boundary requirements for the P5-R0 external path. **Blocker-completion plan:** [`P5_BLOCKER_COMPLETION_PLAN.md`](P5_BLOCKER_COMPLETION_PLAN.md) defines the dependency-ordered execution path and stop conditions. **Master runsheet:** [`P5_MASTER_RUNSHEET.md`](P5_MASTER_RUNSHEET.md) is the authoritative operational state and must be read after every context compaction. This ledger does not amend, relax, or replace those documents.

## Governance and interpretation

Update this ledger after each phase milestone, gate decision, remediation decision, or release-evidence change. Preserve the original roadmap as the strategic plan; record execution facts, evidence locations, custody level, provenance, and blockers here. A local test, fixture, review, or development artifact is a **local execution milestone**, not a project evaluation/trusted-release pass unless a signed project-controlled gate artifact explicitly says otherwise.

**Authority boundary:** no separately controlled evaluator authority is claimed. The evaluator role, locks, manifests, policy/scoring keys, private stores, held-out release, result seals, and timing bridge operated by this project are self-custodied. Separate processes and keys provide technical separation and tamper evidence only. Google Confidential Space and FreeTSA are external authorities for attestation/timestamp facts; they do not validate capability or make project-authored results independent.

**Evidence terms**

- **Local milestone:** implementation, test, fixture, or local review in this checkout. It may demonstrate a bounded mechanism, but it does not establish external custody or release eligibility.
- **Self-custodied trusted-release gate:** the roadmap's frozen, project-controlled gate: separated code/data/control-plane components and keys; required signed lock/manifest; sealed results and receipts; complete required execution; and the relevant explicit pass decision. It proves the recorded integrity and containment properties only; it is not independent evaluator validation.
- **Not executed:** no implementation or execution artifact has been located for the named phase in this evaluation stream. This is not a claim that the strategic phase was undone or removed.

## Current authoritative status

| Roadmap phase | Local execution milestone and evidence | Self-custodied evaluation / trusted-release gate | Current disposition |
|---|---|---|---|
| **P0** — custody, containment, replay | P0-A harness and rootless-Podman acceptance design/evidence exist; default-deny and local probes are documented. | **Not passed.** No self-custodied P0-A result; no P0-E1 or P0-E2 result. | Local evidence only; operational release remains blocked. |
| **P1** — trusted control plane/native ownership | Local complete-graph-proposal mediation and finite native Podman acceptance path are documented. | **Not passed.** No provisioned P1-E1/integration result under the project-controlled authority. | Local proposal-mediation work only; no trusted-control-plane claim. |
| **P2** — bounded closed-loop interaction | Native/container scaffolding, deterministic synthetic 320 control artifact, local offline exercise, and tests exist. | **Not established.** No trusted signed release lock, retained signed 320-episode held-out evidence, complete hardened controls, or signed release result. | Local scaffolding/control evidence only; P2-B1 release claim unavailable. |
| **P3** — guarded learning | Local P3-R0 implementation/review evidence exists; local accounting seals `no_go` and rolls back. | **Not passed.** No P3-E1 result, custody package, or adoption. | Local readiness only; adoption remains prohibited. |
| **P4** — planning/compositional transfer | Local P4-R0 implementation, fixtures, preregistration, results, container/seccomp artifacts, and tests exist; they remain local readiness/no-go evidence. | Not eligible; no P4-E1/E2 trusted-release result and depends on upstream gates. | Roadmap-only future phase; local artifacts are not promoted. |
| **P5** — replication/robustness/release | Local P5-R0 V2/V3 implementation, native evidence, receipts, rollback, and no-go closure exist under `evaluation/p5_r0/`, `services/p5_r0_evaluator/`, and the P5 tests. The later same-project Confidential Space/FreeTSA diagnostic path also verified attestation, STS/WIF exchange, software-key KMS/GCS capability activation, bridge authentication, V3 timing evidence, and a durable timing-ledger object; a normal `smoke=0` service boot was verified. | **Not passed.** The local V2/V3 runs remain no-go where controls/authority/closure fail; the external path has no authorized normal evaluator task, no P5-E1/E2 execution, and no self-custodied trusted-release result. | Local evidence plus bounded external diagnostic infrastructure; P5 trusted release remains blocked. |

## Latest blocker-completion execution status

The repository-side blocker-completion plan is [`P5_BLOCKER_COMPLETION_PLAN.md`](P5_BLOCKER_COMPLETION_PLAN.md). Its Phase A and repository-side B–D steps have now run: the complete P5/service slice passed `232` tests, project virtualenv compilation passed, and `git diff --check` passed. The read-only GCP checks confirmed Cloud Run timing bridge revision `p5-timing-bridge-00004-872` is Ready and the committed durable ledger object exists.

The newly implemented private-store rehydration, checkpoint rollback, timing outbox/recovery, fresh timing-chain restoration, supervisor boundary, and mandatory task-commitment paths are repository-side milestones. They do not satisfy B1/B2/B3/B5: no reviewed production bundle/private truth package, actual locked native closure, authenticated supervisor/OOM evidence, or authorized normal task set has been supplied. No VM, IAM mutation, task request, native production run, P5-E1/E2 execution, or release claim was made.


- Audited checkout `HEAD`: `3529fe4d` (`Migrate recurrence ledger to graph-native rules`).
- At ledger creation, the working tree is broadly dirty: many unrelated tracked files are modified, and the roadmap, `docs/security/`, `evaluation/`, `semantic-review/`, relevant P2/P3 Rust sources/binaries, and `tests/evaluation/` are untracked.
- Accordingly, the P0–P3 artifacts listed below are **not committed release provenance**. They cannot be tied to a trusted release without a clean, pinned, signed project-controlled release artifact; that artifact would still be self-custodied, not independently validated.
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

P0 is **not operationally accepted**. Same-user filesystem/process ownership, local signing, interception/monkeypatch-based safeguards, and same-user rootless Podman do not establish a hardened control-plane boundary, immutable inputs, write-only results, enforced no-network policy, or externally authoritative whole-process kill. No self-custodied P0-A pass artifact was located. No P0-E1 trace-only replay result or P0-E2 brokered interactive replay result was located.

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

This is a finite, same-user, test-only acceptance path—not a trusted control plane, self-custodied release gate, dynamic autonomous planning result, or production-launcher replacement. The documented provisioned integration gate requires a cached base image and explicit environment flags. No executed provisioned P1-E1 acceptance evidence was located.

## P2 — bounded closed-loop interaction

### Local execution milestones

`evaluation/p2/PREREGISTRATION.md` fixes a narrow H=1 native graph-plan claim and requires project-controlled 320-item held-out execution, hardened rootless Podman controls, both hostile-probe images, complete chained receipts, and a primary gate. It labels the checked-in state pre-release scaffolding and its lock intentionally invalid.

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

P2-B1 is **not established**. No trusted signed release lock, project-held-out 320-episode run, complete signed receipt/scoring evidence, hardened-probe result set, or self-custodied signing/custody package was located. The unfilled `evaluation/p2/RESULTS_TEMPLATE.md` is not a result. The semantic review’s nine local passes, environment-dependent skips, and focused Rust results are local validation evidence only, not the preregistered release gate.

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

No P3-E1 execution result, self-custodied signed prerequisite package, complete signed P3 release lock, or adoption evidence was located. The approved review is deliberately limited to P3-R0 local readiness. P3 release/adoption remains blocked directly by a real P2 phase-go attestation, a complete signed P3 lock, provisioned P0/P1 evidence, and project-controlled execution/receipt/rollback authority.

## P4 and P5 — future execution status

P4-E1/P4-E2 and P5-E1/P5-E2 are **not executed self-custodied trusted-release phases** in this evaluation stream. They remain transitively blocked by the upstream project-controlled P0–P3 gates. This does not erase the local implementations or diagnostics that now exist.

- **P4:** no self-custodied P4-E1/E2 result, project custody package, or release authorization was located.
- **P5:** local P5-R0 V2/V3 implementation, native evidence, receipts, rollback, and explicit no-go closure exist under `evaluation/p5_r0/`, `services/p5_r0_evaluator/`, and their tests. The later Confidential Space/FreeTSA work proves a bounded diagnostic attestation/timing path, including a successful smoke and normal `smoke=0` boot, but it is not a P5-E1/E2 trusted-release result. No authorized normal evaluator task was submitted, and no P5 release claim is made.

The roadmap definitions and thresholds remain unchanged in substance: P4 still requires project-selected long-horizon planning and held-out compositional transfer; P5 still requires fresh unseen-domain replication and scaling/adversarial robustness after P0–P4 pass. The thought-manifold production workstream is subordinate to those gates and is documented in `docs/research/psychology_affect/THOUGHT_MANIFOLD_PRODUCTION_PLAN.md`.

## Exact next dependencies

The immediate authorized dependency is **P0-A under project-controlled, self-custodied custody**, exactly as specified by the roadmap:

1. A project-controlled, signed baseline/control-plane manifest with frozen build/container/native-binary/source and policy digests. The manifest is an auditable project artifact, not independent authority.
2. Separate project-controlled policy authority, broker, receipt writer, and kill-supervisor processes/identities; project-held signing keys and task/scoring authority. Process/key separation is technical containment only.
3. Attested read-only content-addressed inputs, write-only results channel, disabled host-route inventory/reachability evidence, and no-network/mount/channel enforcement.
4. Required P0-A start/stop, control-plane mutation, route-denial, grant-revocation, receipt-chain, and kill-supervisor probes; P0-A must pass in two fresh reruns.

Only after that P0-A pass: execute P0-E1 trace-only replay, then P0-E2 brokered interactive replay, then P1-E1 under the separated project-controlled boundary. P2 release remains downstream of those successful gates and requires a new signed P2 release lock, all 320 project-held-out episodes, complete mandatory hardened controls—including the Python hostile route—and sealed scoring/receipt evidence. P3 remains directly blocked by P2 phase-go plus the P3 custody/lock prerequisites. P4 and P5 remain transitively blocked by those earlier phase passes. None of these steps creates an independent evaluator claim.

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

| 2026-09-09 | Added standalone digest-only RFC 3161 timing evidence via `services/p5_r0_evaluator/rfc3161.py`. It builds SHA-256 MessageImprint queries, uses the fixed DigiCert endpoint, rejects redirects/oversize/malformed responses, requires pinned CA and TSA certificate identities, verifies CMS/signing purpose through OpenSSL, bounds `genTime`, and chains run/task/event sequence and previous digest. Evidence retains only token/response/certificate digests and explicitly sets `bridge_required=true` for the existing Ed25519 `P5R0IndependentTimingAttestationV2`; it cannot set `timing_certified` alone. Fixed public-payload probe succeeded; 14 RFC3161 tests and 76 evaluator tests passed. | RFC 3161 adapter/tests, official DigiCert/Sigstore documentation, fixed-data TSA probe, local test/compile validation. No cloud/IAM mutation. |

| 2026-09-09 | Added the RFC 3161-to-independent-ledger bridge contract. `P5R0IndependentTimingAttestationV3` preserves V2 fields and adds a signed `rfc3161_evidence_digest`; the validator enforces Ed25519 authority/key/ledger/run/task/event/sequence/previous/payload bindings. `timing_bridge.py` provides a bounded HTTPS client that sends only public IDs and payload digest, rejects redirects/noncanonical/oversized responses, and validates returned V3 records. The bridge is independent only when backed by a separately operated endpoint and pinned authority; no endpoint, bridge key, WIP, IAM, KMS, or GCS resources were provisioned. | 94 evaluator tests, compilation, and scoped diff checks passed; V2 compatibility retained and RFC3161 adapter remains explicitly separate until bridge deployment. |

| 2026-09-09 | Added explicit FreeTSA RFC 3161 provider support at `https://freetsa.org/tsr` with numeric policy OID `1.2.3.4.1`; endpoint allowlisting and CA/TSA certificate pins remain mandatory. A fixed public-payload probe returned `Granted`, displayed policy alias `tsa_policy1`, and was DER-resolved to `1.2.3.4.1`. FreeTSA is a timing provider option, not the independent Ed25519 bridge; no FreeTSA CA/signer pins or production bridge endpoint have been provisioned. | Official FreeTSA service page, fixed-digest probe, DER policy extraction, RFC3161 tests (16), evaluator tests (96), compilation, and diff checks. No cloud/IAM mutation. |

| 2026-09-09 | Retrieved FreeTSA’s official `files/cacert.pem` and `files/tsa.crt`; OpenSSL verified the TSA signer chain (`tsa.crt: OK`), validity, and `Time Stamp signing: Yes`. Reviewable pins are CA PEM `sha256:2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438` and TSA signer DER `sha256:32e841a95cc1164101ffde41298ef2fc75c1c4372ef095e88a6bbd47dfb191fc`. These are documented/allowlisted but not activated in production policy; certificate rotation requires renewed review. | FreeTSA official certificate artifacts, OpenSSL chain/purpose/validity output, FreeTSA fixed-digest probe, and 16 RFC3161/96 evaluator tests. No cloud/IAM mutation. |

| 2026-09-09 | Added `timing_bridge_service.py`, the server-side FreeTSA-to-`P5R0IndependentTimingAttestationV3` bridge seam. It accepts canonical digest-only requests, requires injected RFC3161 adapter/authority/signer/ledger, rejects replay/event/sequence conflicts, binds verified FreeTSA evidence digest and `gen_time` into the signed V3 record, and refuses non-durable ledgers in production mode. The in-memory ledger is explicitly test-only. No HTTPS endpoint, authentication, bridge key custody, durable ledger, cloud resource, IAM, WIP, KMS, or GCS provisioning was performed. | 103 evaluator tests, compilation, scoped diff checks, FreeTSA evidence adapter and V3 timing validation. |

| 2026-09-09 | Added `timing_bridge_app.py`, a fail-closed authenticated WSGI boundary for the FreeTSA timing bridge. It exposes only `POST /v1/timing`, requires canonical JSON and `application/json`, bounds body reads, authenticates through an injected deployment authenticator, returns generic redacted error categories, validates signed V3 response shape, and has a locked one-time-injection default. Production construction requires `production_ready=true` and a durable ledger. | 12 bridge-app tests, 115 evaluator tests, compilation, and diff checks passed. Endpoint authentication, bridge key custody, durable ledger, HTTPS deployment, and cloud provisioning remain external requirements. |

| 2026-09-09 | Provisioned the confirmed same-project worker-independent bridge architecture: private Cloud Run `p5-timing-bridge` (Ready at `https://p5-timing-bridge-b4slnqayga-ue.a.run.app`), separate `p5-timing-bridge@ocelot-proof.iam.gserviceaccount.com`, private `p5-timing-ledger-ocelot-proof-141633828616` bucket, separate software Ed25519 KMS key `p5-timing-bridge` version 1, FreeTSA CA Secret Manager version, production WIP provider `p5-cs-production`, candidate-bound KMS/GCS/token-creator IAM, and stale digest-grant removal. Published evaluator candidate v3 `sha256:c949b275023b7dc3b1065f18cd0b357fe2cc1d1c84c659c54f27720676a42ecd` with exact v3 policy. A Secure-Boot AMD SEV VM successfully refreshed the Google attestation token and started the production evaluator workload; it was deleted cleanly. No authenticated evaluator task request was issued, so timing ledger/KMS/GCS capability activation remains unproven. | GCP resource/IAM state, Cloud Run Ready status/logs, Confidential Space serial output, candidate digest/policy render, and cleanup verification. Worker-independent same-project deployment is established; operator-independent custody is not claimed. |

| 2026-09-09 | Provisioned and exercised the same-project worker-independent production bridge stack: Cloud Run bridge Ready, separate bridge SA/KMS key/private GCS ledger/FreeTSA secret, production WIP provider, candidate-bound KMS/GCS/token-creator IAM with stale grant rotation, and evaluator smoke images. The corrected evaluator parser and VM-subject-prefix path reached Confidential Space `/v1/token` and passed hardware/claim/WIP launch gating. The one-shot smoke then failed closed at evaluator KMS public-key access (`KMSConfigurationError` / `kms_public_key_unavailable`) before timing bridge invocation; temporary VMs were deleted and no broad project-level viewer grant was retained. No timing ledger object, FreeTSA bridge call, KMS signing, or GCS capability activation was proven. | GCP resource/IAM state, serial redacted smoke output, candidate-bound WIP condition, 143 local evaluator tests, candidate builds, and cleanup verification. |



### Subsequent status clarification — thought-manifold and external substrate

The later thought-manifold blocks 348–351 and capability-suite tracks T1–T5 are landed local research artifacts, not P0–P5 trusted-release results. Their local PASS results demonstrate bounded mechanism behavior under declared fixtures; they do not establish project custody, native ownership, cross-domain transfer, production deployment, or a general-intelligence claim. The dedicated integration plan is `docs/research/psychology_affect/THOUGHT_MANIFOLD_PRODUCTION_PLAN.md`.

The external software-key Confidential Space/timing work also remains subordinate diagnostic infrastructure: the smoke path produced a V3 timing record and the normal `smoke=0` service booted, but no authorized normal evaluator task was submitted. P5-E1/P5-E2 therefore remain unexecuted and the P5 trusted-release disposition remains blocked by the roadmap’s upstream custody, containment, held-out, native-closure, controls, and project-controlled authority requirements.


### Latest upstream gate audit

`docs/research/engine_substrate/P5_UPSTREAM_GATE_AUDIT.md` records a read-only reconciliation of P0-A/P0-E1/P0-E2/P1–P4. The blocked decisions remain accurate. The P4 inventory wording is corrected: local P4-R0 implementation, preregistration, fixtures, results, container/seccomp artifacts, and tests exist, but no P4-E1/E2 trusted-release result or eligibility exists. No local or historical P4 artifact is promoted.
