# P5-R0 Attested Result Requirements

## 1. Purpose and claim boundary

This document specifies the minimum requirements for producing a cryptographically evidenced P5-R0 result through Google Confidential Space, a FreeTSA-backed RFC 3161 timing bridge, candidate-bound Google IAM/KMS/GCS capabilities, a bounded native worker closure, and a self-custodied evaluator authority.

The target is an **attested, bounded, self-custodied result**, not an independently evaluated result. The project controls the generator, task set, private truth, policies, locks, scoring, receipts, and result seal. Google Confidential Space attests the signed workload execution; FreeTSA supplies timing evidence. Neither supplies tasks, evaluates capability, or creates independent evaluator custody.

There are no externally supplied “production inputs.” The project creates every controlled-run input from the frozen repository generator/control plane and binds its canonical digests to the reviewed execution definition. External or environment-derived facts are execution-boundary facts only: Confidential Space claims, KMS key/signature material, durable object-store state, supervisor observations, and FreeTSA timing evidence. A generated input is not evidence that it was executed, and a fabricated or self-asserted evidence object is never accepted as execution evidence.

This requirements document does not authorize a P5 release, adoption, positive-transfer claim, general-intelligence claim, or physical deployment. A diagnostic result may be published only with its exact evidence scope and limitations. For DISPATCH-063, the required Track A order is explicit: pre-launch provisioning only; real Confidential Space attestation and capability activation; read the exact generated inputs from the attested durable path and fresh-process rehydrate/verify; obtain FreeTSA timing; derive the timing/input seed; execute the selected one-case/`cold_reset`/one-`illegal_action` native task under authenticated supervisor, OOM, and deadline evidence; create the canonical result; persist and verify its result seal; KMS-sign the exact verified seal/result digest; and only then optionally publish the already signed result to GCS.

### 1.1 Evidence classes

| Evidence class | What it can establish | What it cannot establish |
|---|---|---|
| Google Confidential Space / AMD SEV attestation | The named workload executed under the verified Google Confidential Space claims, image/project/zone commitments, Secure Boot/vTPM claims, and declared TEE hardware profile. | Correctness of the evaluator, truth of the task result, independent evaluator custody, or exact worker CPU timing. |
| FreeTSA RFC 3161 plus the project timing bridge | A digest was accepted by FreeTSA under the pinned policy and was incorporated, in order, into a signed bridge record with the committed run/task/event bindings. | Exact CPU start/end, scheduler behavior, process containment, evaluator independence, or result correctness. |
| Self-custodied evaluator authority and receipt chain | The project-controlled lock, manifest, authority binding, result, and receipts satisfy their signatures, digests, schema, sequencing, and closure checks. | Independent review, operator-independent custody, truthful task semantics by itself, or an external release decision. |
| Native closure and resource evidence | The declared worker/image/runtime/seccomp/resource envelope was checked and required execution evidence was produced. | A capability result if the worker, task, controls, or private truth are not validly bound. |

## 2. Definitions

- **Project-generated controlled-run input:** a canonical artifact produced by the frozen project generator/control plane, including the manifest, split, private truth, task set, controls, worker/evaluator contracts, policy, and unsigned lock request. Its generator/version/seed/output digests are provenance and commitment data, not execution evidence.
- **Fabricated evidence:** any claimed timing, attestation, supervisor observation, receipt, KMS signature, worker result, or result seal that was generated locally, supplied by a caller/worker, copied from another run, or otherwise not produced and verified at the required signed execution boundary. A generated input is not automatically fabricated; it is simply not evidence until consumed by signed execution.
- **Signed-environment execution attestation:** verified Confidential Space claims showing that the exact locked workload executed, together with the real KMS signature over the exact lock, timing, supervisor, receipt, and result-seal evidence required by this specification.
- **Self-custodied authority:** a project-controlled signing key, lock, manifest, private store, policy, scorer, receipt chain, or result seal. It may be technically separated from the worker, but is not an independent evaluator.
- **Authority trust binding:** a project-reviewed authority/transport commitment exact-bound to the lock, signer, public key, manifest, and policy. It is an anti-self-assertion and binding check, not a claim of independent custody.
- **Attestation binding:** the redacted, adapter-created commitment derived from verified Google Confidential Space claims. Raw OIDC/JWT/proof material must not appear in public result output.
- **Timing record:** a verified `P5R0IndependentTimingAttestationV3` record containing the FreeTSA evidence digest, bridge authority/key/ledger identity, run/task/event/sequence bindings, payload digest, and previous-record binding. “Independent” in this schema name refers to the separate timing substrate, not independent evaluator authority.
- **Native closure:** the exact content and runtime closure for the worker, host runner, image, `crun`, seccomp profile, argv, policy, and required evidence/seal/rollback paths.
- **Trusted release:** a project-defined gate over frozen artifacts. In this project it is self-custodied and proves only the recorded integrity/containment properties; it is not independent validation.

## 3. Functional requirements

### 3.1 Authority, custody, and cryptographic binding

**REQ-AUTH-001 — Self-custody declaration.** Every production or diagnostic result must identify the evaluator authority as self-custodied unless a genuinely independent authority is supplied. No result, README, preregistration, or API response may imply that a project-created authority is independent.

**REQ-AUTH-002 — Closed authority metadata.** Authority metadata must use a closed schema with an authority ID, key ID, public key, public-key digest, and transport attestation where the selected authority contract requires it. Unknown or missing fields fail closed.

**REQ-AUTH-003 — Exact authority binding.** The project-controlled authority must match the lock authority, authority digest, key ID, public key, public-key digest, transport-attestation digest, receipt signer, and required manifest/policy commitments. A mismatch must produce an impasse or validation error before task execution.

**REQ-AUTH-004 — Project-generated controlled inputs and no local promotion.** The frozen repository generator/control plane must create the deterministic task set, private truth, manifest, controls, and diagnostic bundle. Their generator/version/seed/output digests must be committed to the bundle and lock before signed-environment execution. Generated local signers, local locks, process-local truth stores, fixtures, or unsigned requests must not be promoted to the production signing authority, durable execution boundary, or evidence. The signed environment must consume the exact generated inputs through the locked durable path.

**REQ-AUTH-005 — Non-exportable evaluator key.** The evaluator signing key must remain in the configured KMS signing boundary or an explicitly controlled signing boundary. Private key material must never be exported into the worker, HTTP caller, result payload, GCS object, or public output.

**REQ-AUTH-006 — Separate timing key.** The timing bridge signing authority must be distinct from the evaluator receipt authority. The timing public-key digest must differ from the evaluator receipt public-key digest, and both identities must be bound in the timing record.

### 3.2 Confidential Space and hardware attestation

**REQ-CS-001 — Signed execution attestation before capability.** The evaluator must verify the Google-signed Confidential Space token and required claims before constructing KMS, GCS, timing, or task-execution capabilities. Failed, expired, malformed, or mismatched attestation produces no capability activation, and a local diagnostic activation is not signed-execution evidence. Pre-launch input provisioning may occur before this verification, but no workload may read, rehydrate, derive, seed, or issue from those inputs until verified attestation and capability activation succeed.

**REQ-CS-002 — Immutable workload and input binding.** The attestation binding must commit to the exact evaluator image digest, project, zone, hardware/TEE profile, Secure Boot/vTPM claims, WIP provider/policy digest, workload identity claims, generated-input commitments, and lock commitments required by the deployment definition.

**REQ-CS-003 — Confidential Space posture.** The production workload must use the locked Confidential Space posture: AMD SEV hardware, Secure Boot/vTPM as required by the lock, no external IP, no host mounts, no privileged mode, no unconfined seccomp, and the declared machine/resource profile.

**REQ-CS-004 — Candidate-bound IAM.** WIF/WIP, service-account impersonation, KMS, GCS, and bridge access must be bound to the exact candidate image/policy/subject commitments. Project-wide viewer grants, operator-wide temporary impersonation, and broad fallback permissions are prohibited.

**REQ-CS-005 — Redacted public evidence.** Public startup and result output may contain only redacted claim digests and committed claim values. Raw JWTs, OIDC tokens, STS tokens, proof bytes, private truth, or private task data must not be emitted.

### 3.3 Timing and bounded-compute requirements

**REQ-TIME-001 — Verified timing before seeded input.** A verified V3 timing record must succeed before any time-seeded input is built or any task is issued. A missing, stale, malformed, replayed, or unverifiable record fails closed.

**REQ-TIME-002 — FreeTSA RFC 3161 evidence.** The timing bridge must send only the canonical SHA-256 payload digest to the pinned FreeTSA endpoint and policy. It must verify the RFC 3161 response, pinned CA/signer identities, CMS signing purpose, message imprint, policy, freshness bounds, and evidence digest before signing the V3 bridge record.

**REQ-TIME-003 — Durable bridge ledger.** Production timing records must be written to a durable, generation-checked ledger. An in-memory ledger is test-only and cannot set timing certification.

**REQ-TIME-004 — Timing chain binding.** Each timing record must bind run ID, task ID, event (`task_issued` or `result_received`), monotonic sequence, previous digest, payload digest, bridge authority/key/ledger identity, and RFC 3161 evidence digest. Replays, sequence gaps, conflicting idempotency reuse, and previous-digest mismatches fail closed.

**REQ-TIME-005 — No caller timing.** Runner-supplied timestamps, durations, timeout flags, CPU times, or seeds must never be accepted as timing observations. The service or verified bridge must be the source of timing evidence.

**REQ-TIME-006 — Coarse bound semantics.** Timing evidence may establish freshness/order and a provider-observed interval. It must not be described as exact CPU time. A bounded-compute claim additionally requires the locked CPU, memory, process-count, wall-deadline, runtime, and supervisor evidence.

**REQ-TIME-007 — OOM and deadline behavior.** The locked resource profile must define memory and wall-time ceilings. If a worker exceeds a ceiling, OOMs, cannot be reaped, or loses supervisor/receipt connectivity, the run must produce no trusted result, perform required process-group cleanup/rollback, and seal an impasse. A successful result may claim bounded resource use only when corresponding runtime evidence is present.

### 3.4 Time-seeded inputs and evidence binding

**REQ-SEED-001 — Explicit timing-derived input algorithm.** After verifying the V3 FreeTSA-backed timing record, compute `timing_record_digest = sha256(canonical_json(timing_record))`. Compute `input_seed_digest = sha256(canonical_json({schema: P5R0TimeSeedV1, timing_record_digest, run_id, namespace, sequence}))`; pass only that digest to the input builder. Compute `input_digest = sha256(canonical_json(input_value))`. The builder must not receive an unverified wall-clock value or caller-provided seed as authority.

**REQ-SEED-002 — Commitment chain.** Every time-seeded execution evidence object must bind exactly:

```text
timing_record_digest
input_seed_digest
input_digest
```

The task, result, receipt, and final seal must preserve these bindings or a digest path to them. The public name is `input_seed_digest`; an internal variable may use another name only if the canonical public field is this name.

**REQ-SEED-003 — Deterministic reconstruction.** Given the verified timing record, locked namespace, run identity, sequence, and committed input-builder version, the input seed and input digest must reconstruct deterministically. The lock, manifest, and every production V2 evidence object must also disclose the builder implementation identity, version, source digest, and the time-seed algorithm source digest. Any source or binding mismatch is an impasse.

**REQ-SEED-004 — No pre-timing work.** No evaluator-private task input, challenge, worker task, or result-producing computation may be derived from the time seed before REQ-TIME-001 succeeds.

### 3.5 Bundle, lock, closure, and worker execution

**REQ-CLOSE-001 — Immutable bundle commitments.** The lock must bind the generated public manifest, generated private case store/truth digest, policy, worker contract, evaluator contract, image digest, runtime digest, seccomp digest, closure digest, resource profile, and receipt/timing authority commitments.

**REQ-CLOSE-002 — Exact native closure.** Before native execution, the runner must verify the exact image, rootless Podman/crun runtime, worker source/closure files, seccomp profile and allowed syscalls, hardened argv, no-network policy, no-pull policy, process/resource limits, and host evidence/seal/rollback paths.

**REQ-CLOSE-003 — Native worker mandatory.** A production or trusted-release result must execute the locked native worker. A local callback, Python fallback, non-native harness, or omitted worker is diagnostic only and must remain no-go.

**REQ-CLOSE-004 — One seam for all cases.** Primary tasks, held-out tasks, controls, mechanics contrasts, and negative controls must use the same worker/evaluator seam, task schema, receipt path, resource profile, and closure checks.

**REQ-CLOSE-005 — Private truth isolation.** Private truth, target actions, secret seeds, domain-family labels, split information, evaluator keys, and private store contents must not enter worker-visible task frames except through explicitly committed opaque protocol fields.

**REQ-CLOSE-006 — Closure recheck.** The exact closure must be rechecked before each native invocation or at the locked invocation boundary. Any image, runtime, seccomp, worker, policy, or host-evidence mismatch fails closed before invoking the worker.

### 3.6 Result, receipt, and provenance evidence

**REQ-EVID-001 — Canonical evidence.** Tasks, results, execution evidence, receipts, locks, manifests, timing records, and seals must use the closed canonical schema and deterministic digest rules. Unknown required fields, duplicate keys, non-canonical bytes, sequence gaps, and digest mismatches fail closed.

**REQ-EVID-002 — Execution evidence.** Each execution evidence record must bind task/input/result/image/runtime/resource/closure commitments, verified signed-environment attestation, KMS signature over the exact lock, authenticated supervisor evidence, hardware/attestation status, run/task/sequence identity, timing-record digest, input-seed digest, input digest, and applicable coarse duration/resource observations.

**REQ-EVID-003 — Append-only receipt chain.** Every task issuance, worker outcome, control outcome, timing event, rollback, impasse, and run closure must be represented in the signed append-only chain. The final chain digest must be recomputed and verified; receipt references in results must resolve to chain members.

**REQ-EVID-004 — Redacted result and seal.** Public output may expose only the result schema, status/disposition, run and chain digests, persisted verified result-seal digest, startup/attestation binding digest, KMS lock-signature binding, timing-record digest, input-seed digest, input digest, and explicitly permitted claim flags. It must not expose private truth, raw credentials, or generated artifacts as if they were execution evidence.

**REQ-EVID-007 — Seal before final signing.** After execution and receipt-chain verification, the evaluator must create the canonical result, persist its result seal to the approved durable path, read back and verify the persisted seal and the exact canonical seal/result digest, and only then request or accept the final KMS signature over that exact verified digest. An unpersisted, unverified, caller-supplied, or differently digested seal cannot be signed as the Track A result.

**REQ-EVID-005 — No score fabrication.** A caller, worker, generated artifact, or local adapter boolean must not upgrade native verification, timing certification, closure status, controls, authority binding, supervisor status, or bounded-compute status. These values must be derived from verified signed-environment evidence.

**REQ-EVID-006 — Reproducible provenance.** The result must record exact source, image, native binary, runtime, policy, seed/input-builder, authority, timing, resource-profile, and closure digests sufficient to reconstruct the claim boundary.

### 3.7 Failure and release behavior

**REQ-FAIL-001 — Fail closed.** Missing signed Confidential Space execution attestation, real KMS signature, verified timing/FreeTSA proof, durable ledger, generated bundle/lock, exact closure, native worker, authenticated supervisor evidence, signed receipts, or persisted verified result seal must yield no task result and a typed impasse.

**REQ-FAIL-002 — No unsafe fallback.** Failure may not trigger a local signer, local timing clock, network retry outside the allowlist, image pull, privileged execution, Python worker fallback, fabricated task/result/evidence, or placeholder caller identity.

**REQ-FAIL-003 — Cleanup and rollback.** Deadline, OOM, malformed task/result, receipt failure, replay, sequence conflict, authority mismatch, or closure mismatch must terminate the worker process group as applicable, restore exact pre-run state, append rollback/impasse evidence, and close the chain.

**REQ-FAIL-004 — Token and expiry handling.** Federated and impersonated credentials must be bounded by their effective expiry. The evaluator must not start or continue a run after the credential, attestation, task, or timing validity window has expired.

**REQ-FAIL-005 — No partial GO.** A result is not GO merely because attestation, KMS, GCS, timing, or a normal VM boot succeeded. GO requires signed-environment execution attestation, exact KMS signing, verified timing-before-seed, native closure, authenticated supervisor/resource evidence, all locked tasks/controls, signed receipts, rollback handling, and a persisted verified result seal.

**REQ-FAIL-006 — Redacted impasse.** An impasse response must identify only a bounded error category and relevant public digests. It must not expose raw tokens, private truth, proof bytes, or sensitive infrastructure details.

### 3.8 Claims and reporting

**REQ-CLAIM-001 — Narrow claim language.** A result may claim only the exact verified properties listed in its evidence. At minimum, the report must separately identify: (1) signed Google hardware/runtime attestation status; (2) FreeTSA timing/order evidence status; (3) real KMS signature and self-custodied authority/receipt-integrity status; (4) native closure/resource/authenticated-supervisor status; and (5) task/control/result execution and seal status.

**REQ-CLAIM-002 — Prohibited claims.** Unless a genuinely independent party supplies and operates the relevant authority, the result must not claim independent evaluator validation, operator-independent custody, unbiased scoring, exact CPU timing, unrestricted containment, general intelligence, P5 release, adoption, or positive transfer.

**REQ-CLAIM-003 — Diagnostic status.** A generated manifest/task set/private store, normal Confidential Space boot, timing-ledger object, KMS request, local signature, or smoke result must be labelled generated/local diagnostic evidence only unless the full signed-execution gates pass. No generated input is proof that execution occurred.

**REQ-CLAIM-004 — Negative evidence.** Reports must include failed, skipped, impassed, OOM, timeout, cleanup, and credential-expiry events. They must not average away a failed gate or relabel a no-go as a capability result.

### 3.9 Required Track A order

Track A is a strict dependency order, not a set of interchangeable gates:

1. **Pre-launch provisioning only:** generate and bind the exact project-controlled inputs, selected one-case/`cold_reset`/one-`illegal_action` contract, candidate closure, policy, provenance, and immutable lock; provision the exact public/private bytes to the approved durable path. Provisioning is not input consumption or execution evidence.
2. **Attestation and capability activation:** perform the real Confidential Space launch, verify the Google-signed attestation and bindings, and activate capabilities only after verification. No input read, rehydration, seed, or task work occurs before this point.
3. **Post-attestation input read and rehydration:** read the exact generated bytes from the attested durable path, verify access/canonical bytes/digests, and rehydrate the private store in a fresh process. A local fixture or process-local truth fallback fails closed.
4. **Timing and seed:** obtain and verify the FreeTSA/RFC-3161 timing record, then derive the timing/input seed and canonical input digest. No task input or task issuance precedes timing verification.
5. **Bounded native execution:** execute the selected one-case/`cold_reset` task and one `illegal_action` control through the authenticated supervisor with OOM, deadline, lifecycle, exit, and cleanup evidence.
6. **Canonical result and verified seal:** create the canonical result, persist its result seal, and verify the persisted seal and exact seal/result digest.
7. **Final KMS signing:** only after seal verification, KMS-sign the exact verified seal/result digest and all required commitments. A pre-run lock signature is conditional: if selected it must be a real, verified KMS signature over the exact lock; if omitted, the final signature must bind the exact immutable lock representation/digest. Neither branch replaces final-result signing.
8. **Optional publication:** only after final signature verification may the already signed result be published to GCS. Track B hardening and P5-E1/E2/release qualification remain separate and are not executed or waived by Track A.



| ID group | Required acceptance evidence | Current repository status |
|---|---|---|
| REQ-AUTH | Project-generated canonical inputs, exact lock/signer/transport binding, real non-exportable KMS path, explicit self-custody claim | Generator/materializer and software KMS path exist; no independent evaluator claim is made; no signed lock exists. |
| REQ-CS | Verified Google token, exact generated-input/lock/image/WIP/IAM claim binding, Secure Boot/AMD SEV posture | Attestation, STS/WIF, candidate-bound IAM, and normal `smoke=0` boot are represented/tested; no signed task execution. |
| REQ-TIME | Verified FreeTSA RFC 3161 proof, pinned identities, separate bridge key, durable ledger, V3 sequence/previous/payload binding | Bridge, ledger, and tests exist; no normal task has consumed a verified live record. |
| REQ-SEED | Timing-first algorithm and `timing_record_digest`/`input_seed_digest`/`input_digest` chain | Algorithm is implemented and disclosed; no signed-environment result using it exists. |
| REQ-CLOSE | Signed lock, durable generated bundle, exact native image/runtime/seccomp/host closure, native worker and supervisor evidence | Local contracts and closure checks exist; no authorized signed-environment closure has executed. |
| REQ-EVID | Canonical schemas, KMS-bound signed lock or exact final-lock binding, signed receipt chain, canonical result with persisted verified result seal before final signing, redacted result, reconstructible provenance | Local/service contracts and tests pass; no trusted normal-task seal exists. |
| REQ-FAIL | Impasse, no fallback, cleanup/rollback, expiry and resource/OOM handling | Fail-closed behavior and tests exist; full production supervisor/OOM evidence remains unexecuted. |
| REQ-CLAIM | Narrow report separating attestation, timing, KMS/self-custody, closure/supervisor, and task/result/seal claims | Documentation is reconciled; no P5-E1/P5-E2 or trusted-release claim is made. |

## 5. Traceability to current implementation

| Requirement area | Primary implementation locations |
|---|---|
| Project-controlled generation/materialization | `evaluation/p5_r0/diagnostic_generator.py`, `services/p5_r0_evaluator/deploy/controlled_run_materializer.py`, `services/p5_r0_evaluator/deploy/bundle_definition.py` |
| Authority binding and KMS signing | `services/p5_r0_evaluator/signing.py`, `services/p5_r0_evaluator/service.py`, `evaluation/p5_r0/preregister.py`, `evaluation/p5_r0/repair.py` |
| Confidential Space attestation and WIF | `services/p5_r0_evaluator/confidential_space.py`, `services/p5_r0_evaluator/confidential_space_app.py`, `services/p5_r0_evaluator/auth.py` |
| FreeTSA/RFC 3161 and timing bridge | `services/p5_r0_evaluator/rfc3161.py`, `services/p5_r0_evaluator/timing.py`, `services/p5_r0_evaluator/timing_bridge.py`, `services/p5_r0_evaluator/timing_bridge_service.py`, `services/p5_r0_evaluator/timing_bridge_production.py` |
| Time-seeded inputs | `services/p5_r0_evaluator/time_seed.py`, `services/p5_r0_evaluator/one_shot.py`, `services/p5_r0_evaluator/schemas.py` |
| Native closure and bounded worker execution | `evaluation/p5_r0/native.py`, `evaluation/p5_r0/native_worker.py`, `evaluation/p5_r0/runner.py`, `evaluation/p5_r0/rebuild.py`, `evaluation/p5_r0/repair.py` |
| Receipts, seals, evidence, rollback | `evaluation/p5_r0/receipts.py`, `evaluation/p5_r0/evidence.py`, `evaluation/p5_r0/rollback.py`, `services/p5_r0_evaluator/service.py` |
| Normal signed execution orchestration | `services/p5_r0_evaluator/production_runner.py`, `services/p5_r0_evaluator/one_shot.py`, `services/p5_r0_evaluator/client.py` |

## 6. Current blockers

These are project-controlled generation/binding or real signed-execution blockers. There is no external task provider and its absence is not a blocker:

1. No generated, digest-bound self-custodied diagnostic bundle/lock/private-truth package has been bound to a real KMS signature and the signed-environment durable path.
2. Repository-side rehydration is implemented and tested; process-local `_PRIVATE_STORES` remains test-only compatibility state. The generated private-truth package still must be consumed by signed execution.
3. Typed native closure/supervisor adapters are implemented and tested; no signed-environment native worker/closure/supervisor execution evidence has been produced.
4. No project-generated and project-authorized diagnostic task set has been consumed by the locked native worker.
5. No verified FreeTSA timing record has been consumed before a real task, and no signed receipt chain/result seal exists for a normal run.
6. No P5-E1/P5-E2 execution or trusted-release result exists. Software-protected KMS authorities remain explicitly non-HSM and self-custodied.

Until these blockers are resolved, the strongest supported output is a self-custodied, redacted attestation/timing diagnostic—not a P5 capability result.

## 7. Completion definition

The requirement set is complete only when:

1. the project generator creates a self-custodied manifest, private store, task set, worker/evaluator contracts, closure, and resource profile with frozen generator/version/seed/output digests;
2. the exact generated inputs are provisioned to the approved durable path before launch, read only after verified attestation/capability activation, and bound either to a real KMS-signed lock (when the conditional pre-run lock-signing mode is selected) or to the exact immutable lock representation/digest in the final signing request;
3. signed Confidential Space attestation activates only the exact candidate-bound capabilities and input/lock commitments;
4. a verified FreeTSA/bridge timing record exists before input derivation, using the disclosed algorithm;
5. `timing_record_digest`, `input_seed_digest`, and `input_digest` are bound through task, execution evidence, receipts, and final seal;
6. for Track A, the selected one-case/`cold_reset` task and one `illegal_action` control execute through the native worker with authenticated supervisor, OOM/deadline behavior, receipts, rollback, canonical result, and persisted verified result seal under the locked profile; broader controls/contrasts remain separate Track B or future release scope;
7. all required evidence is durable, canonical, signed, and reconstructible as data (without claiming an independent evaluator); and
8. the final report states the narrowest supported claim and all failures/limitations.

A failure of any item is a no-go and must not be converted into a partial GO.
