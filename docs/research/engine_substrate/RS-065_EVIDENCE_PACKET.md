# RS-065 Evidence Packet — repository-only KMS lock-signing boundary

```text
item_id: RS-065
run_id: P5-MASTER-001
owner: agent-rs065-kms-adapter
state_proposed: PASS_REVIEW for the repository-only adapter/contract; signed Confidential Space execution remains BLOCKED pending master approval and reviewed authority/KMS inputs.
master_decision: Master alone decides RS-065. This packet is evidence only.
```

## Scope and boundary

The adapter accepts only the exact generated RS-062 request at `var/p5-r0-diagnostic-inputs/public/lock-signing-request.json`. Its frozen unsigned lock digest is `sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df`; request digest is `sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d`. Authority, KMS key version, authority-binding digest, and signature remain null in the request.

The operation is expressed against the existing `services.p5_r0_evaluator.interfaces.Signer.sign_digest` capability. The adapter does not call that capability. A future response validator requires Confidential Space approval, self-custodied project authority, a closed KMS authority binding, returned Ed25519 public-key equality, key/version equality, exact lock-digest signature verification, and unchanged diagnostic/non-release fields. No function creates, persists, exports, or promotes a signature.

Forbidden in this item: gcloud, KMS, GCS, VM, deployment, FreeTSA, supervisor, task execution, authority creation, and production promotion.

## Files

- `services/p5_r0_evaluator/deploy/kms_lock_signing.py` — request-only adapter, operation descriptor, unsigned-request validator, future signed-response validator, and local CLI.
- `services/p5_r0_evaluator/deploy/p5-r0-kms-lock-signing-contract.json` — canonical reviewable contract with null signature output and blocked status.
- `services/p5_r0_evaluator/tests/test_kms_lock_signing.py` — positive contract/response tests and adversarial wrong-digest, wrong-key, malformed-signature, and local/unapproved-promotion tests.
- `var/p5-r0-diagnostic-inputs/public/lock-signing-request.json` — current generated input; not modified.

## Commands and exit codes

All commands ran with `pwd=/home/matt/ozmadev/ocelot`.

| command | exit |
|---|---:|
| `pwd` | 0 |
| `python3 -m services.p5_r0_evaluator.deploy.kms_lock_signing validate` | 0 |
| `python3 -m py_compile services/p5_r0_evaluator/deploy/kms_lock_signing.py services/p5_r0_evaluator/tests/test_kms_lock_signing.py` | 0 |
| `git diff --check -- services/p5_r0_evaluator/deploy/kms_lock_signing.py services/p5_r0_evaluator/deploy/p5-r0-kms-lock-signing-contract.json services/p5_r0_evaluator/tests/test_kms_lock_signing.py` | 0 |
| `python3 -m pytest services/p5_r0_evaluator/tests/test_kms_lock_signing.py services/p5_r0_evaluator/tests/test_execution_request.py tests/test_p5_r0_diagnostic_generator.py -q` | 0 |
| `sha256sum ...` for the four listed artifacts | 0 |
| `ruff check ...` | 127 — `ruff` is not installed; py_compile and pytest were used instead. |

Original packet validation recorded **26 passed** (9 RS-065 tests plus 17 RS-063/RS-062 compatibility tests). After refreshing the generated request commitments, the focused P5/service validation passed **49 tests**, and the full permitted service/P5 suite passed **340 tests**.

Adversarial coverage:

- wrong unsigned lock digest rejected before any response validation;
- returned public key not matching authority rejected;
- malformed/non-64-byte signature rejected;
- local execution or unapproved promotion rejected;
- valid future response remains `production_promotable=False` and `non_release=True`;
- injected `Signer.sign_digest` is never invoked by the operation descriptor.

## Artifact digests

| artifact | raw SHA-256 |
|---|---|
| `services/p5_r0_evaluator/deploy/kms_lock_signing.py` | `91aae665560864f24b88d0e6227e8e937e98da5d446fb5fa665228d5c580e893` |
| `services/p5_r0_evaluator/deploy/p5-r0-kms-lock-signing-contract.json` | `4d6728daa328167f26ddc96be32ac1e4246a11ce0b69943035b47a3857c0ff00` |
| `services/p5_r0_evaluator/tests/test_kms_lock_signing.py` | `39666c1d65f74cefefbd8a7363284bc6bed8e9696e79d3e1865a1d7dac326158` |
| `var/p5-r0-diagnostic-inputs/public/lock-signing-request.json` | `0e8d1f306446ba4e62d31f3eaab523430b372671772db0593516a702bee5f45` |

The request's canonical semantic commitments are the `request_digest` and `unsigned_lock_digest` recorded above; the raw file digest is distinct and recorded separately.

## Limitations and proposed state

This work proves the repository contract and local validator only. No actual Confidential Space attestation, KMS public-key response, KMS signature, authority trust decision, durable ingestion, deployment, VM, or task execution was performed. The local response validator can verify a supplied attestation-shaped approval and Ed25519 response, but it cannot manufacture or independently establish the external attestation trust root; that remains a signed-environment/master boundary.

Proposed state: **`PASS_REVIEW` for the repository-only RS-065 contract, with the signed-environment operation still blocked/no-go**. No production authority or release claim is proposed.
