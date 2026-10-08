# RS-067 Evidence Packet — self-custodied authority/transport binding contract

```text
item_id: RS-067
run_id: P5-MASTER-001
owner: agent-rs067-authority-binding
state_proposed: PASS_REVIEW for the repository-only contract and validator; signed-environment authority approval remains BLOCKED/NO_GO.
master_decision: Master alone decides RS-067. This packet is evidence only.
```

## Scope and boundary

This item defines the next reviewable input contract for the generated self-custodied diagnostic data. It uses the closed `P5R0PublicAuthorityV4` and `P5R0AuthorityTransportV1` shapes and binds the future authority to the selected evaluator KMS key candidate, canonical WIP provider, separate token audience, transport event, project/zone/workload claims, and Confidential Space approval requirements.

The checked-in contract deliberately does **not** invent or promote the missing RS-066 authority ID, key ID, evaluator public key, public-key digest, KMS key version, provider, audience, event, or production claim values. Those fields are `REQUIRED_INPUT:` markers. Actual authority metadata, KMS public material, KMS authority binding, approval, and signature are null. The contract is blocked and never permits production promotion.

`authority_binding.py` validates supplied review inputs locally only. It does not call KMS, gcloud, GCS, FreeTSA, STS, a VM, deployment, Confidential Space, a supervisor, or a task runner; it creates no authority, approval, signature, credential, or production output. Test-only ephemeral Ed25519 keys exercise equality and digest checks in memory and are not written as authority inputs.

## Files

- `services/p5_r0_evaluator/deploy/authority_binding.py` — canonical marker-contract validator and local candidate-binding validator.
- `services/p5_r0_evaluator/deploy/p5-r0-authority-binding-contract.json` — canonical review-only contract with required-input markers and null actual authority/approval/signature state.
- `services/p5_r0_evaluator/tests/test_authority_binding.py` — nine focused structural and adversarial tests.
- `docs/research/engine_substrate/RS-067_EVIDENCE_PACKET.md` — this evidence packet.

No master runsheet state was changed. Existing unrelated dirty files were preserved.

## Commands and exit codes

All commands ran with `pwd=/home/matt/ozmadev/ocelot`.

| command | exit |
|---|---:|
| `pwd && git status --short --branch` | 0 |
| `python3 -m py_compile services/p5_r0_evaluator/deploy/authority_binding.py services/p5_r0_evaluator/tests/test_authority_binding.py` | 0 |
| `python3 -m pytest services/p5_r0_evaluator/tests/test_authority_binding.py -q` | 0 |
| `python3 -m services.p5_r0_evaluator.deploy.authority_binding validate` | 0 |
| `python3 -m pytest services/p5_r0_evaluator/tests/test_authority_binding.py services/p5_r0_evaluator/tests/test_confidential_space.py services/p5_r0_evaluator/tests/test_deployments.py -q` | 0 |
| `git diff --check -- services/p5_r0_evaluator/deploy/authority_binding.py services/p5_r0_evaluator/deploy/p5-r0-authority-binding-contract.json services/p5_r0_evaluator/tests/test_authority_binding.py` | 0 |
| `sha256sum services/p5_r0_evaluator/deploy/authority_binding.py services/p5_r0_evaluator/deploy/p5-r0-authority-binding-contract.json services/p5_r0_evaluator/tests/test_authority_binding.py` | 0 |

The final focused result was **9 passed**. The adjacent existing slice was **73 passed**.

The local CLI output was:

```json
{"approval_present":false,"authority_metadata_present":false,"production_promotable":false,"schema":"P5R0SignedEnvironmentAuthorityBindingContractV1","signature_present":false,"status":"blocked_pending_reviewed_authority_and_confidential_space_approval"}
```

## Adversarial coverage

- wrong KMS public key is rejected even when its replacement digest is internally correct;
- provider used as token audience is rejected;
- provider project number drift from the signed project claim is rejected;
- missing transport field is rejected by closed-field validation;
- self-authored/local approval is rejected;
- absent approval remains review-only and non-promotable;
- KMS/public-key/authority identifier binding and digest checks are exercised;
- exact claim-path map, evaluator workload, issuer, secure boot, and diagnostic smoke requirements are checked;
- the marker contract rejects authority/KMS/approval/signature promotion and preserves null state.

## Artifact digests

Raw SHA-256 digests from the final checkout:

| artifact | raw SHA-256 |
|---|---|
| `services/p5_r0_evaluator/deploy/authority_binding.py` | `82a04fa2cbde52c3206c149dfe2c83402c098bbf4a556773b760e862024f0050` |
| `services/p5_r0_evaluator/deploy/p5-r0-authority-binding-contract.json` | `6436950f8e7a0d73bfb52cf2f9523108252baa0b4a5434357e79fdf9e9a81f7d` |
| `services/p5_r0_evaluator/tests/test_authority_binding.py` | `03ca67e4046592b9f5b425f7acf24edf4ab5f1abedc841e780fd0cba35f6fa65` |

The RS-065 evidence commitments retained in the contract are the historical request digest `sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d` and unsigned-lock digest `sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df`; they are not newly generated or signed by RS-067.

## Limitations and proposed state

No standalone RS-066 packet or exact current evaluator KMS candidate values were present in the checkout. The master runsheet records RS-066 as `BLOCKED` because the read-only inventory lacked closed authority/transport metadata, a unique deployed-evaluator binding, and Confidential Space approval. Therefore the markers in this contract must not be replaced with test fixtures, historical bridge values, or guessed production values.

The validator proves repository-level shape, digest, cross-field, and fail-closed behavior only. It cannot establish KMS ownership, provider trust, attestation authenticity, deployment identity, or approval provenance. A future approved Confidential Space path must supply and review the missing inputs, then independently validate them before any signing or ingestion. Actual signing and approval remain inside that approved path; no signature or authority claim is proposed here.

Proposed state: **`PASS_REVIEW` for the repository-only RS-067 contract/validator, with signed-environment authority binding and all production execution remaining `BLOCKED`/`NO_GO`**. Master review is required before any state transition.
