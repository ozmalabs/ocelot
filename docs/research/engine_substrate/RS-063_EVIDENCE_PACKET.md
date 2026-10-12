# RS-063 Evidence Packet

**Master run:** `P5-MASTER-001`
**Runsheet item:** `RS-063`
**Owner:** `agent-rs063-signed-run`
**Proposed state:** `PASS_REVIEW` for the repository-only request definition; production execution remains `NO_GO`/blocked. Master alone decides the transition.

## Result

Created a canonical, deterministic, rerunnable signed-environment execution request. It consumes the generated RS-062 artifact index and unsigned KMS lock-signing request by repository-relative path, preserves their generated digests, binds the RS-040 native closure and RS-060 bundle definitions, and references the existing `render_deployment` renderer. The request is explicitly `blocked_pending_approval` and `review_only_no_execution`.

No cloud, credential, KMS, object-store, Confidential Space, FreeTSA, supervisor, VM, deployment, or task operation was invoked.

## Files

- `services/p5_r0_evaluator/deploy/p5-r0-signed-environment-execution-request.json`
  - canonical request definition; current object/definition digest `sha256:d82fbce481c116d3865c8ade409253ab9b659519870783eeb5bf99151f11e743`
  - current raw file SHA-256 `sha256:d82fbce481c116d3865c8ade409253ab9b659519870783eeb5bf99151f11e743`
- `services/p5_r0_evaluator/deploy/execution_request.py`
  - fail-closed local validator/audit CLI; current raw file SHA-256 `sha256:9b919a3b1b5b03829538f4345e80801106fa748ba12d07b743cf86f4087919de`
- `services/p5_r0_evaluator/tests/test_execution_request.py`
  - RS-063 focused validator tests; current raw file SHA-256 `sha256:3be48ccdafe73dfaa1f37ce93e9d0194eecdcf3f04e8aca3af89c43985455a84`

## Commands and exit codes

| Command | Exit | Meaning |
|---|---:|---|
| `pwd` | 0 | Confirmed `/home/matt/ozmadev/ocelot`. |
| `PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.execution_request validate --allow-blocked` | 0 | Canonical inputs and review-only boundary validate; request remains blocked. |
| `PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.execution_request validate` | 2 | Expected fail-closed result: approval and production execution preconditions are absent. |
| `PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.execution_request audit --allow-blocked --output /tmp/rs063-execution-request-audit.json` | 0 | Wrote a local audit only; `cloud_operations=[]`, `mutations_performed=false`. |
| `python3 -m pytest services/p5_r0_evaluator/tests/test_execution_request.py services/p5_r0_evaluator/tests/test_controlled_run_materializer.py services/p5_r0_evaluator/tests/test_definition.py services/p5_r0_evaluator/tests/test_bundle_definition.py tests/test_p5_r0_diagnostic_generator.py -q` | 0 | `36 passed` in the current targeted validation. |
| `pytest -q services/p5_r0_evaluator/tests tests/test_p5_r0*.py` | 0 | `340 passed` in the current full permitted P5/service validation. |
| `git diff --check -- services/p5_r0_evaluator/deploy/execution_request.py services/p5_r0_evaluator/deploy/p5-r0-signed-environment-execution-request.json services/p5_r0_evaluator/tests/test_execution_request.py` | 0 | No whitespace errors in the implementation/request/test paths. |

## Bound artifacts and digests

The following values were read from the current canonical local files. Semantic/object digests use the repository canonical-JSON digest; raw file digests are SHA-256 of exact file bytes.

- Artifact index: `var/p5-r0-diagnostic-inputs/artifact-index.json`; current `index_digest` `sha256:04a98e3e48685228fd68ea757de276fe1c1a7ce347bd027a2756a48595897768`; raw file SHA-256 `sha256:23ec2e4863660c9d38adfaa615fe5eac75d0aac0c6692e5903cd1879c7077bfb`.
- Generated diagnostic manifest: `var/p5-r0-diagnostic-inputs/public/manifest.json`; current `manifest_digest` `sha256:190fe19fe7f70b181f11f0b375cf6241a2cc2c0c49abbf2b52f8ce8899b2f01a`; raw file SHA-256 `sha256:78694af8056e5d141546ba15b9e489aa3afe7e05e74653bb94ab0b00cb4794d5`.
- Unsigned KMS lock-signing request: `var/p5-r0-diagnostic-inputs/public/lock-signing-request.json`; current `request_digest` `sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d`; raw file SHA-256 `sha256:0e8d1f306446ba4e62d31f3eaab523430b372671772db0593516a702bee5f45`.
- Exact unsigned lock digest nested in the request, for a future reviewed KMS operation: `sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df`. No standalone unsigned-lock file exists; this is the canonical nested `unsigned_lock.lock_digest`.
- Controlled-run manifest: `var/p5-r0-controlled-run/manifest.json`; current stored/recomputed `manifest_digest` `sha256:d6ba67499ae411877c58680c3054fb54564bf02c3b7b299e5aa16e277b3b28f7`; raw file SHA-256 `sha256:64b5ae5890839323bb8572a65deecd2db73a0a5b102ba41807d9e92b1fb9ab6a`.
- Execution request: `services/p5_r0_evaluator/deploy/p5-r0-signed-environment-execution-request.json`; current object/definition digest and raw file SHA-256 are both `sha256:d82fbce481c116d3865c8ade409253ab9b659519870783eeb5bf99151f11e743`.
- Private case store: `sha256:0ec34adc958b2565aa24599be477c3e6b3488e83df9e8f1811715262ea7b55e1`.
- Task set: `sha256:725b59168b83b2305e76500774ddca6e0b59185cec3527bf2d6133e657c29aa7`.
- Control commitment: `sha256:ac9cefc8910d3cec2053259e5a053c7bdd34ed0e9381fe920a9b4b19878c5f58`.

The request preserves every artifact record from the current index, including public/private paths, object digests, and file digests. The private store remains `private-truth/case-store.json`, private, and disposable `var/` custody only.

The controlled-run manifest was regenerated from the current deterministic materializer. Its current `manifest_digest` and raw file digest are recorded above, and its embedded `source_commitments.rs063` now matches the current execution-request file digest `sha256:d82fbce481c116d3865c8ade409253ab9b659519870783eeb5bf99151f11e743`.

## Defined gates and prohibitions

The definition specifies the target Confidential Space kind, immutable `crun`/read-only/no-network/drop-capabilities closure contract, reviewed image/closure digests as required-but-null inputs, KMS operation as request-only with `signature=null`, and a GCS object-boundary plan with bucket/prefix required-but-null. IAM, WIP, capability-account, KMS-account, and bridge values are required-but-null; fixed issuer/TEE/AMD SEV/Secure Boot/workload contracts are inherited from RS-040/renderer. Every planned run-order step is disabled; future externally mutating steps are explicitly marked but forbidden in this request.

The apply plan forbids: `gcloud mutation`, VM creation, KMS signing, GCS upload, secret access, FreeTSA call, task submission, and deployment. The command set contains only local validator/audit commands and no cloud mutation command.

## Limitations and proposed state

Missing or deliberately false preconditions are: reviewed RS-040 inputs, reviewed RS-060 inputs, reviewed deployment policy, reviewed authority/KMS binding, master approval, real KMS signature, durable GCS ingestion, Confidential Space activation, authenticated supervisor evidence, and task execution. No independent evaluator authority is required or claimed; this is a self-custodied diagnostic request.

Proposed state is `PASS_REVIEW` for RS-063’s local definition and validation evidence only. Preserve the overall no-go until real KMS signing, durable ingestion, Confidential Space activation, supervisor evidence, and task execution occur. Do not update the master runsheet from this packet; master alone decides RS-063.


## Repair addendum (review follow-up)

The original NEEDS_CHANGES findings are addressed locally without changing the production signed schemas or executing any external operation. The canonical request now binds `P5R0DiagnosticInputGeneratorV1`, seed `p5-r0-diagnostic-seed-v1`, split seed `p5-r0-v2`, the six expected generated commitments, and the disposable `var/p5-r0-diagnostic-inputs` output root. Validation first rebuilds the generated bundle in memory; it does not write private truth. If ignored `var/` inputs are absent, the reproducible in-memory artifact/index equivalent is validated; any present files are then checked against that equivalent.

`source_files` is closed and paired with `source_verification_digests`: exact raw SHA-256 commitments cover the canonical protocol, diagnostic generator and direct dependencies, RS-040 closure sources, RS-060 validator/runner sources, renderer, authority client, and RS-063 validator. Any source-content drift blocks validation before artifact checking.

The request carries and validates `authority_contract.authority_mode: self_custodied_diagnostic`, `independent_evaluator_required: false`, and the explicit interpretation that inherited `external_authority_required: true` is a supplied trust-binding gate rather than an independent evaluator requirement. Signed Confidential Space execution remains a separate future attestation gate.

Adversarial coverage now includes absent `var/` inputs in a clean-checkout-style temporary repository, copied renderer content drift, and authority-policy ambiguity. The current focused command reports 36 passed tests. Successful blocked audits continue to assert `ready: false`, `cloud_operations: []`, and `mutations_performed: false`.

Repaired validation commands:

```text
PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.execution_request validate --allow-blocked
PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.execution_request audit --allow-blocked --output /tmp/rs063-repaired-audit.json
python3 -m pytest services/p5_r0_evaluator/tests/test_execution_request.py services/p5_r0_evaluator/tests/test_controlled_run_materializer.py services/p5_r0_evaluator/tests/test_definition.py services/p5_r0_evaluator/tests/test_bundle_definition.py tests/test_p5_r0_diagnostic_generator.py -q
```

The resulting state remains `blocked_pending_approval`; this supports **PASS_REVIEW** for the repository-only request and does not support RS-063 production PASS. No gcloud mutation, KMS signing, GCS upload, VM/deployment, FreeTSA, secret access, or task execution was invoked. The generated private case store remains disposable ignored `var/` custody only and is not part of the repair.



## RS-068 source-digest refresh

After the repository-side RS-068 `deployments.py` renderer changes, the canonical source map was recomputed from the current repository bytes with the RS-063 validator's closed `_EXPECTED_SOURCE_PATHS` map. Only `source_verification_digests.deployment_renderer` changed: the refreshed value is `sha256:a2945b9a9ab4f7316437ed8386b0e1600bf2b071f9ca8c37083b6796e0b0c4d8` (the other source commitments are unchanged). The canonical request was rewritten with that map; its current canonical request/raw-file digest is `sha256:d82fbce481c116d3865c8ade409253ab9b659519870783eeb5bf99151f11e743`.

The generated diagnostic inputs and unsigned lock request were not regenerated or edited. Their current commitments are: artifact index `sha256:04a98e3e48685228fd68ea757de276fe1c1a7ce347bd027a2756a48595897768` (raw file `sha256:23ec2e4863660c9d38adfaa615fe5eac75d0aac0c6692e5903cd1879c7077bfb`), generated manifest `sha256:190fe19fe7f70b181f11f0b375cf6241a2cc2c0c49abbf2b52f8ce8899b2f01a` (raw file `sha256:78694af8056e5d141546ba15b9e489aa3afe7e05e74653bb94ab0b00cb4794d5`), unsigned lock digest `sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df`, lock-signing request digest `sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d`, and raw lock-signing request file SHA-256 `sha256:0e8d1f306446ba4e62d31f3eaab523430b372671772db0593516a702bee5f45`.

The current controlled-run manifest is `sha256:d6ba67499ae411877c58680c3054fb54564bf02c3b7b299e5aa16e277b3b28f7` (raw file `sha256:64b5ae5890839323bb8572a65deecd2db73a0a5b102ba41807d9e92b1fb9ab6a`). It was regenerated from the current deterministic materializer; its RS-063 source commitment now matches `sha256:d82fbce481c116d3865c8ade409253ab9b659519870783eeb5bf99151f11e743`.

Current refresh validation, all local-only, returned the following results:

```text
PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.execution_request validate --allow-blocked  # exit 0
PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.execution_request validate  # exit 2, expected fail-closed block
python3 -m pytest services/p5_r0_evaluator/tests/test_execution_request.py services/p5_r0_evaluator/tests/test_controlled_run_materializer.py services/p5_r0_evaluator/tests/test_definition.py services/p5_r0_evaluator/tests/test_bundle_definition.py tests/test_p5_r0_diagnostic_generator.py -q  # 36 passed
```

The audit remains `status=blocked_pending_approval`, `ready=false`, `cloud_operations=[]`, and `mutations_performed=false`; production values remain unresolved and no cloud operation was invoked. The proposed state remains **PASS_REVIEW** for the repository-only RS-063 request definition, while production remains **NO_GO**/blocked and master alone decides any transition.
