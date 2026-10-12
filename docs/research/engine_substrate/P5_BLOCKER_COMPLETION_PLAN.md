# P5-R0 Blocker Completion Plan

**Status:** active DISPATCH-063 correction plan; no P5 release or capability result is claimed.

**Requirements:** [`P5_ATTESTED_RESULT_REQUIREMENTS.md`](P5_ATTESTED_RESULT_REQUIREMENTS.md)

**Controlled-run input and execution gate:** [`P5_PRODUCTION_INPUT_HANDOFF.md`](P5_PRODUCTION_INPUT_HANDOFF.md) records the project-generated inputs, Track A gates, optional Track B hardening, and evidence boundaries. It is not a human-supplied production-input checklist.

**Master runsheet:** [`P5_MASTER_RUNSHEET.md`](P5_MASTER_RUNSHEET.md) is the authoritative operational state. This plan does not mutate runsheet state or its event log.

**Roadmap:** [`GENERAL_INTELLIGENCE_EXPANSION_PLAN.md`](GENERAL_INTELLIGENCE_EXPANSION_PLAN.md)

**Execution ledger:** [`GENERAL_INTELLIGENCE_EXECUTION_LEDGER.md`](GENERAL_INTELLIGENCE_EXECUTION_LEDGER.md)

## 1. Objective and two-track scope

DISPATCH-063 separates the next work into two non-interchangeable tracks:

- **Track A — minimal self-custodied attested diagnostic.** Produce at most one narrow, bounded diagnostic result from canonical project-generated inputs, one real Confidential Space launch/attestation, the exact candidate image/closure, timing before seed derivation, authenticated native/resource evidence, canonical receipts, and a real KMS-signed final result. Track A is diagnostic only and remains self-custodied. It does not establish independent evaluator custody, a P5 release, adoption, positive transfer, general intelligence, or exact CPU timing.
- **Track B — optional hardening/release qualification.** Add durability, operational hardening, broader controls/contrasts, least-privilege cleanup, and any later release-qualification work only after Track A is separately complete. Track B is non-blocking for Track A.

Track A’s mandatory acceptance surface is deliberately limited to:

1. canonical, reproducible project-generated inputs, mandatory pre-run delivery/rehydration, and exact digest commitments;
2. an explicit immutable MVP selection of one task, `cold_reset` arm, and one `illegal_action` control, with no implicit full P5 catalog;
3. the exact candidate image and native closure, including runtime, seccomp, argv, host/resource profile, and rollback/evidence paths;
4. one real Confidential Space launch with verified Google-signed attestation before capability activation;
5. a verified FreeTSA/RFC-3161-backed timing record before any seed, input, or task is derived;
6. bounded native-worker evidence with authenticated supervisor identity/lifecycle, including bounded OOM/deadline behavior and cleanup evidence;
7. canonical append-only receipts for the executed path and any failure/rollback/impasse; and
8. a real KMS signature over the final result whose exact binding covers the immutable lock representation/digest, all generated/provisioned/read/rehydrated inputs, the selected task/control contract, candidate image/closure, attestation binding, timing/input chain, supervisor/resource evidence, receipt chain, canonical result, persisted verified result seal, and result disposition.

A pre-run KMS signature over a lock is **optional for Track A**. It may be used, but it is not an acceptance prerequisite when the final KMS-signed result binds the exact immutable lock representation/digest and all required commitments. If exact final binding cannot be demonstrated, Track A fails closed. GCS persistence is **optional after final signing** and is never evidence merely because an object exists. Separate GCS-only least-privilege cleanup is **optional Track B hardening**, not a Track A gate.

P5-E1, P5-E2, and their P0-A/P0-E1/P0-E2/P1–P4 upstream gates are **out of scope for DISPATCH-063 and for Track A**. This plan neither runs nor waives those gates; any future release qualification must reopen them under Track B/the master runsheet.

There are no externally supplied production inputs and no external task provider. The project generator/control plane creates the manifest, split, private truth, task set, controls, contracts, policy, provenance, and lock representation. Generation/materialization is provenance and commitment data, never execution evidence. Environment-derived facts remain separate: attestation, KMS, timing, supervisor, receipts, and final result signature.

### Track A MVP task/control contract

Track A selects a deliberately small contract; it does not inherit the full P5 arm, control, or contrast catalog merely because those definitions exist in the generator. The selected contract must be written into the immutable lock and final-result binding before execution:

| Surface | Selected MVP contract | Explicitly not selected |
|---|---|---|
| Task set | Exactly **one** canonical project-generated case, identified by `case_id`, `case_digest`, and ordinal; one `P5R0WorkerTaskV3` envelope; one native invocation through the locked worker/evaluator seam. The case’s split is metadata only and creates no held-out claim. | The remaining generated cases, repeated episodes, replication, or a full train/development/held-out run. |
| Arm/session | `cold_reset` only, with the locked task budget (`max_steps`, frame bytes, and wall deadline); no adaptive or persistent-session claim. | Other arms, warm/adaptive state, learning, transfer, or adoption. |
| Control | Exactly one selected `illegal_action` protocol-boundary control using the same task schema, native seam, supervisor, receipt path, and lock. Expected outcome is a verified rejection/protocol error; an unexpected legal action fails closed. | The other memorization, permutation, semantic, safety, leakage, containment, resource, and negative-transfer controls unless separately selected and rebound. |
| Contrasts and scoring | No mechanics contrast matrix and no aggregate capability score. The result reports only the selected task outcome, selected control outcome, evidence status, and disposition. | Full P5 arms, controls, contrasts, held-out completeness, generalization, or release scoring. |

The locked native run must still produce authenticated lifecycle, bounded resource, OOM/deadline, and cleanup evidence. Those are execution-boundary safety checks for the selected invocation—not an implicit addition of P5 arms or controls. An intentional, correctly evidenced `illegal_action` rejection is a control receipt; it is not a capability or release result.

### Input delivery boundary

The exact generated public inputs and private case store must be provisioned to the approved durable boundary before launch, but pre-launch is provisioning only: no workload may read, rehydrate, derive, seed, or issue a task from those inputs before verified Confidential Space attestation and capability activation. After attestation, the locked workload must read the exact generated bytes from that attested durable path, verify access, canonical bytes, and digests, and rehydrate the private store in a fresh process. This post-attestation read/rehydration is a mandatory Track A execution prerequisite; a local `var/` fixture, process-local truth store, unsigned request, or post-sign publication cannot substitute for it. If GCS is chosen as the approved pre-run delivery boundary, provisioning occurs before launch but the input read is permitted only after attestation and capability activation, and it remains distinct from optional post-sign publication. No task may be issued when delivery, digest verification, or rehydration is incomplete.

The optional post-sign GCS step is only publication/transport of an already verified canonical result, persisted result seal, and final KMS signature, plus permitted public metadata. It is not the input-delivery gate, not an authority, and not evidence merely because an object exists.

## 2. Current baseline

Completed repository-side capabilities include:

- durable private-store injection and evaluator-engine checkpoint rehydration;
- fail-closed restart, rollback, receipt, timing, and evidence persistence boundaries;
- service-owned timing-first seed issuance;
- durable timing outbox recovery and external recorder chain-head restoration;
- the canonical `timing_record_digest` / `input_seed_digest` / `input_digest` chain;
- deterministic controlled-run materialization with explicit non-fabricated-evidence boundaries;
- native closure preflight and a typed supervisor-evidence boundary;
- mandatory authorized-task and lock/manifest/worker commitment validation in one-shot orchestration; and
- a redacted diagnostic result path that cannot promote a callback, local observation, or local signer into production authority.

These are implementation milestones only. They are not signed-environment execution or a P5 gate pass. In particular, the current repository-only KMS lock-signing adapter is request/response validation and does not itself call KMS or create a signature; the real signature must come from the approved signed boundary.

## 3. Blockers and exit criteria

| ID | Track | Blocker | Exit criteria | Current status |
|---|---|---|---|---|
| **B1** | A | Canonical generated inputs, mandatory delivery, and exact binding | The frozen generator produces canonical manifest, private case store/truth, the selected one-task/one-control MVP contract, worker/evaluator contracts, policy, provenance, and lock representation. The exact bytes are provisioned through the approved pre-launch durable boundary, then read only after verified attestation/capability activation, freshly rehydrated, and generator/version/seed/output/delivery digests are exact-bound to the candidate and final result. Local fixtures, local authorities, and unsigned requests are never execution evidence. | **Open.** Diagnostic inputs exist locally; no approved signed-workload delivery, fresh-process rehydration, or signed task consumption. |
| **B2** | A | Exact candidate image and native closure | The exact candidate image digest, native worker, runtime/crun, seccomp, argv, no-pull/no-network/no-mount/no-privilege posture, host closure, resource profile, and evidence/seal/rollback paths are verified at the locked invocation boundary. | **Open.** Closure contracts/preflight exist; no authorized signed-environment invocation has passed. |
| **B3** | A | Real Confidential Space launch and attestation | One real launch returns verified Google-signed Confidential Space claims bound to the exact candidate image, project/zone, TEE/hardware, Secure Boot/vTPM posture, WIP/IAM policy, generated-input commitments, and lock representation. Capabilities activate only after verification. | **Open.** Diagnostic smoke/boot evidence is not a task-run attestation. |
| **B4** | A | Timing before seed and task | A V3 FreeTSA/RFC-3161-backed record is verified through the pinned bridge and durable ledger before input seed, private task input, or task issuance. `timing_record_digest`, `input_seed_digest`, and `input_digest` survive through evidence, receipts, and final result. | **Partially complete.** Bridge and tests exist; no normal signed task has consumed the path. |
| **B5** | A | Authenticated native/resource evidence | A real supervisor supplies authenticated lifecycle evidence bound to run/task/sequence, closure, invocation count, worker exit, OOM/deadline status, process-group cleanup, and evidence digest. Native execution and bounded OOM/deadline behavior are evidenced; self-digested observations are invalid. | **Open.** Typed validation exists; no signed-environment supervisor evidence exists. |
| **B6** | A | Canonical receipts, result seal, and KMS-signed final result | The executed path appends canonical signed receipts for start/timing/task/result/rollback/impasse/closure as applicable. After the receipt chain is verified, the canonical result seal is persisted and read back/verified; only then does a real KMS signature cover the exact verified seal/result digest and all required commitments. A pre-run lock signature is optional only under the exact-final-binding rule; final-result signing is mandatory. | **Open.** No trusted normal-task result, receipt chain, persisted verified seal, or final KMS signature exists. |
| **B7** | B | Optional post-sign persistence and cleanup hardening | If used, persist the already signed result/bundle after signing through the exact durable boundary; separately prove GCS-only least-privilege cleanup and rollback. Object presence never promotes evidence, and this work cannot gate Track A. | **Optional/not started.** No GCS mutation is authorized by this plan. |
| **B8** | B / out of scope here | Release qualification | Future release work may define broader controls/contrasts, replication, scaling, adversarial robustness, release cards, and upstream gates. P5-E1/E2 and P0-A/P0-E1/P0-E2/P1–P4 gates are not executed, waived, or accepted by DISPATCH-063. | **Out of scope.** Master runsheet remains the decision authority. |

## 4. Track A dependency-ordered execution

### A0 — Freeze and inspect, read-only

1. Record checkout provenance, candidate image/closure values, resource profile, and validation manifest.
2. Confirm every generated artifact is canonical, reproducible, non-placeholder, and labelled as input/commitment data rather than execution evidence.
3. Confirm self-custody and the exact claim boundary; no document or output may imply independent evaluator custody or exact CPU timing.
4. Run repository validation. Any failure stops the track.

**Gate A0:** a reproducible repository baseline with no placeholder, fabricated-evidence, or claim-boundary violation.

### A1 — Generate, bind, and provision inputs (pre-launch; no input read)

1. Run the frozen project generator for the manifest, split, private truth/store, the selected one-task/one-control MVP contract, worker/evaluator contracts, policy, provenance, and lock representation. The selected case and control IDs are explicit; no full catalog is implied.
2. Verify canonical bytes and generator/version/seed/output digests.
3. Provision the exact public/private input package to the approved durable boundary and record transport/object digests, access policy, and immutable provisioning commitments. Do not read, rehydrate, derive, seed, or consume the inputs before verified Confidential Space attestation and capability activation.
4. Bind the exact generated and provisioned commitments to the candidate image/closure and final-result signing request. No task capability or task issue occurs in A1.

**Gate A1:** the pre-launch boundary contains only the exact project-generated inputs and commitments; provisioning is not execution evidence, and no input read or rehydration has occurred.

### A2 — Verify the exact candidate closure

1. Verify the immutable candidate image digest and native worker.
2. Verify runtime/crun, seccomp, argv, host closure, resource ceilings, no-network/no-pull/no-host-mount/no-privileged posture, and evidence/seal/rollback paths.
3. Recheck the closure at the invocation boundary. Any mismatch stops the track.

**Gate A2:** the one-shot invocation is bound to the exact candidate and closure.

### A3 — Launch once, verify attestation, and activate capabilities

1. Perform one real Confidential Space launch with the exact candidate.
2. Verify the Google-signed attestation and redacted binding before constructing or activating KMS, GCS, timing, or task capabilities.
3. Bind the attestation to the candidate, project/zone, hardware/TEE, Secure Boot/vTPM, WIP/IAM policy, generated/provisioned input commitments, and lock representation.
4. Activate only the capabilities authorized by the verified attestation. No input read, private-store rehydration, seed derivation, or task issue is permitted before this gate.

**Gate A3:** one verified real launch exists and capability activation is attestation-gated. Smoke/boot/readiness alone is diagnostic and cannot pass this gate.

### A4 — Read exact inputs after attestation, then verify timing before seed

1. From the attested workload, read the exact generated public inputs and private case store from the approved durable boundary.
2. Verify access policy, canonical bytes, transport/object digests, and all generated/provisioned commitments, then rehydrate the private store in a fresh process. A process-local truth fallback, stale object, digest mismatch, or failed rehydration stops the track.
3. Only after that post-attestation read/rehydration, submit the canonical public digest through the pinned FreeTSA/RFC-3161 timing bridge.
4. Verify CA/signer pins, imprint, policy, CMS purpose, freshness, V3 signature, sequence/previous digest, and durable ledger state; recover the chain head before the next event.
5. Issue the service-owned timing-first seed and compute the canonical three-digest chain. Refuse any caller timestamp, caller seed, local clock, or pre-timing private task input.

**Gate A4:** exact inputs have been read from the attested durable path and freshly rehydrated, then verified timing is durable and committed before any seed, input, or task execution. Timing establishes order/coarse bounds only, never exact CPU timing. Timing establishes order/coarse bounds only, never exact CPU timing.

### A5 — Run the bounded native MVP diagnostic

1. Consume only the exact input package read from the attested durable path and freshly rehydrated after A3, plus the selected one-task/one-control contract.
2. Recheck the candidate closure at the native invocation boundary.
3. Execute the one `cold_reset` task and the selected `illegal_action` control through the authenticated supervisor and the same worker/evaluator seam.
4. Capture authenticated normal lifecycle, worker exit, invocation count, bounded resource result, and explicit OOM/deadline/cleanup behavior. These safety checks do not add unselected P5 arms or controls.
5. On any timeout, OOM, receipt failure, malformed input/result, replay, authority mismatch, or cleanup uncertainty, terminate/rollback as applicable and emit only a typed redacted impasse.

**Gate A5:** native, OOM/deadline, and cleanup evidence is supervisor-authenticated and exact-bound; a callback, local process, worker boolean, or self-digested observation cannot satisfy it.

### A6 — Create canonical result, persist/verify seal, and KMS-sign

1. Append canonical signed receipts for every selected-MVP event, including timing, the one task, the selected control, resource/worker outcome, rollback, and closure/impasse as applicable. Unselected catalog entries have no receipt or claim.
2. Recompute and verify the receipt chain.
3. Create the canonical result from the exact immutable lock representation/digest, every generated/provisioned/read/rehydrated input commitment, the selected task/control contract, candidate/closure, verified attestation binding, timing/input digests, supervisor/resource evidence, receipts, and disposition.
4. Persist the canonical result seal to the approved durable seal path. Read it back and independently verify the persisted seal, its canonical bytes, and the exact seal/result digest. This verification is a hard prerequisite to final signing.
5. Apply the conditional signing branch frozen in the immutable lock: (a) **omit pre-run lock signing** and require the final KMS-signed result to bind the exact immutable canonical lock bytes/digest and every one of those inputs, or (b) **use pre-run lock signing**, in which case a real KMS operation in the approved signed boundary must sign that exact immutable lock digest and the returned signature must be verified against the bound public authority. A local signer, request, or claimed signature never satisfies mode (b); mode (b) does not replace final-result signing.
6. Obtain and verify the real KMS signature over the exact verified seal/result digest and all required commitments through the approved signed boundary and verify it against the bound public key. Emit only a redacted result after verification. If seal persistence/verification, final binding, or signature checking fails, emit a redacted impasse and preserve failure evidence.

**Gate A6:** the canonical result seal is durably persisted and verified before the real KMS signature binds the exact seal/result digest. The only Track A completion artifact is that verified KMS-signed final result. Pre-run lock signing may be present or absent, but omission is acceptable only under the exact-final-binding rule; final-result KMS signing is never optional.

### A7 — Optional post-sign persistence

After A6 only, optionally persist the already signed canonical result, verified result-seal digest, and required public receipt metadata to GCS. GCS is a transport/durability surface, not an authority; object existence cannot upgrade a result. Track A remains complete without this persistence step if the signed result and seal were verified at the signing boundary.

### Track A acceptance matrix (compact)

| Gate | Must be true for Track A | Failing or omitted evidence |
|---|---|---|
| Inputs and MVP selection | Inputs are provisioned pre-launch only; after attestation/capability activation the exact bytes are read from the attested durable path, freshly rehydrated, and bound with exactly one selected task, `cold_reset` arm, and one `illegal_action` control. | Pre-attestation read, local fixture/process-local truth, implicit full catalog, missing selected IDs, or delivery/rehydration drift → impasse. |
| Candidate and attestation | Exact image/native closure is rechecked and one real Google-signed Confidential Space attestation is verified before capability activation. | Boot/readiness, local claims, closure drift, or late/missing attestation → stop. |
| Timing and execution | After post-attestation input read/rehydration, verified FreeTSA/RFC-3161 timing is committed before seed/input/task; native supervisor supplies lifecycle, bounded resource, OOM/deadline, and cleanup evidence. | Pre-attestation input use, caller time/seed, exact-CPU wording, callback, synthetic/self-digested observation, or uncertain cleanup → impasse. |
| Receipts, result, and seal | Canonical receipts cover the selected task/control and applicable failure events; the canonical result seal is persisted and verified; a real KMS signature verifies the exact seal/result digest. | Standalone log, unsigned/unsealed result, unverified seal, invalid receipt chain, signing before seal verification, or non-real signature → no result. |
| Lock/signing branch | If no pre-run lock signature is used, the final signature covers exact immutable lock bytes/digest and **all inputs**; if used, it is real KMS signing of that exact lock and final signing still occurs. | Ambiguous final binding, local lock signature, request-only artifact, or missing final KMS signature → stop. |
| Claim boundary | Output is self-custodied diagnostic evidence only; no secrecy, independent custody/evaluation, exact CPU timing, P5-E1/E2, release, or broader unselected-arm claim. | Any prohibited claim or partial GO → fail closed. |

### Exact remaining Track A prerequisites

1. **Master-authorized MVP lock:** approve the exact selected case identity, `cold_reset` task contract, `illegal_action` control, resource/deadline profile, and explicit omission of all other arms/controls/contrasts; bind them immutably.
2. **Pre-run input boundary:** provide the reviewed durable provisioning path for public inputs and private truth, with access policy and byte/digest checks. Provisioning occurs before launch, but the attested workload must not read or rehydrate until after verified attestation and capability activation; fresh-process rehydration evidence is mandatory before timing/seed/task work. This remains required even when post-sign GCS publication is omitted.
3. **Candidate closure:** provide the exact image digest, native worker, crun/runtime, seccomp, argv, host/resource profile, and evidence/seal/rollback paths, rechecked at invocation.
4. **Real attestation:** execute one approved Confidential Space launch and verify the Google-signed image/project/zone/TEE/Secure Boot/vTPM/WIP-IAM/input/lock binding before capability activation.
5. **Timing-first path:** obtain verified FreeTSA/RFC-3161 evidence through the pinned bridge and durable ledger, then derive the seed/input chain before issuing the selected task.
6. **Bounded execution evidence:** run the selected task and control through the native worker and authenticated supervisor, including real lifecycle, OOM/deadline, process-group cleanup, and rollback/impasse evidence.
7. **Receipt and KMS authority:** verify the canonical receipt chain and a real KMS final-result signature against the bound public authority. If pre-run lock signing is selected, separately verify the real KMS lock signature; if omitted, verify the final signature’s exact immutable-lock/all-input coverage.
8. **Final disposition:** emit the redacted signed diagnostic or typed impasse, with no prohibited claim. Post-sign GCS publication is optional and cannot block or upgrade Track A.

## 5. Track B — optional hardening/release qualification

Track B is separate, non-blocking hardening. It may include:

- optional pre-run KMS lock signing as hardening (Track A may also select this signing mode, but it is never mandatory when exact final binding is present);
- durable post-sign GCS persistence and replay/restart rehydration;
- a separate GCS-only least-privilege cleanup/rollback proof;
- broader controls, contrasts, negative controls, and operational failure matrices;
- additional supervisor/resource stress evidence and deployment qualification; and
- future release-card work.

Track B must not be used to retroactively weaken Track A evidence or to relabel Track A as independent evaluation. P5-E1/E2 and P0-A/P0-E1/P0-E2/P1–P4 upstream gates remain out of scope here and require a future master-authorized release plan.

## 6. Fail-closed stop rules

Stop and seal a typed redacted impasse immediately if any of the following occurs:

- A generated input, lock representation, image, runtime, authority, policy, or closure value is missing, placeholder, non-canonical, or digest-mismatched.
- A generated artifact, fixture, caller value, local clock, local signer, local lock, callback, normal boot, or self-digested observation is presented as signed execution evidence.
- The exact candidate image/closure, attestation, generated-input commitments, supervisor evidence, or final-result binding does not match.
- The real Confidential Space attestation is absent, stale, malformed, locally authored, or not verified before capability activation.
- Timing proof, durable ledger state, or the timing-before-seed order cannot be verified; any timing/input digest is absent or not preserved through the final result.
- The native worker is replaced by a callback, fallback, unverified local process, privileged mode, image pull, host mount, network path, or unconfined seccomp.
- Authenticated supervisor evidence is absent or does not bind lifecycle, invocation, worker exit, OOM/deadline, cleanup, closure, run/task/sequence, and evidence digest.
- Canonical receipts cannot be verified, the canonical result seal cannot be persisted/read back/verified before final signing, the final result cannot bind the exact immutable lock representation/digest, or the real KMS signature is absent/invalid/mismatched.
- A pre-run lock signature is absent **and** exact final-result binding cannot be proved. Pre-run signing is optional only under the exact-final-binding rule; final-result signing is never optional.
- Post-sign result persistence/publication is forbidden before final signing, or GCS object presence is used as authority/evidence. Approved pre-run input delivery is a separate mandatory boundary when selected. GCS-only cleanup is optional hardening, but any attempted cleanup must fail closed and cannot mask a failure.
- OOM, deadline, process-group, receipt, rollback, credential expiry, or persistence cleanup is uncertain.
- Any output would imply independent evaluator custody, exact CPU timing, a P5-E1/E2 result, an upstream gate pass, release, adoption, positive transfer, or general intelligence.

The absence of an external task provider is not a stop condition: task generation and authorization are project-controlled. Failure to generate, bind, authorize, or consume the project-controlled task set remains a stop condition.

## 7. Validation and evidence locations

Repository-only validation remains local/read-only:

```text
.venv/bin/pytest -q services/p5_r0_evaluator/tests tests/test_p5_r0*.py
.venv/bin/python -m compileall -q evaluation/p5_r0 services/p5_r0_evaluator
python3 -m services.p5_r0_evaluator.deploy.controlled_run_materializer --output var/p5-r0-controlled-run/manifest.json
git diff --check
```

The materializer writes only a review manifest and performs no KMS, GCP, GCS, VM, FreeTSA, supervisor, or task operation. No command in this plan may mutate cloud resources, create a production task, fabricate worker/result/evidence objects, promote a local fixture, or mutate the master runsheet.

Primary evidence locations remain `services/p5_r0_evaluator/tests/`, `tests/test_p5_r0*.py`, `services/p5_r0_evaluator/deploy/`, and disposable `var/` review roots. The execution ledger records facts and gate decisions; it is not a substitute for the master runsheet.

## 8. Current decision

Track A is the active DISPATCH-063 frontier. Execute only the read-only/repository preparation and, after the separately approved signed-environment boundary is available, the one-shot sequence A1–A6. A7 and all Track B work are optional/non-blocking. Do not mutate cloud state from this plan. Do not edit runsheet state here; only the master may accept evidence or change a gate.

The strongest current claim remains:

> The repository contains tested, project-controlled, fail-closed attestation/timing/closure/evidence paths and a review-only controlled-run materializer, but it has not produced a KMS-signed, authorized native P5 diagnostic result under signed Confidential Space execution.
