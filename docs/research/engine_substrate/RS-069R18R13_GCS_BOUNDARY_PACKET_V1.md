# RS-069R18R13 GCS Boundary Packet V1

**Master run:** `P5-MASTER-001`  
**Approval context:** `P5-MASTER-001/APPROVAL-011` (broad sequence approval only)  
**Operation:** `ingest_generated_bundle_to_gcs` / order 4  
**Classification:** repository review only, non-release  
**Status:** `reviewed_candidate_binding_pending_credential_and_iam`

## Result

Prepared the machine-readable packet `services/p5_r0_evaluator/deploy/rs069r18r13-gcs-boundary-packet-v1.json`. The user-supplied project, bucket, and capability service-account candidates were confirmed with absolute `/home/matt/google-cloud-sdk/bin/gcloud` read-only commands. No cloud mutation, credential creation/export, object upload, IAM change, or master-runsheet edit was performed.

The selected safe namespace is:

```text
gs://p5-evaluator-ocelot-proof-141633828616/p5-r0/operation-4/rs069r18r13-op4-04a98e3e/{object_suffix}
```

The run ID is derived from the first eight hexadecimal characters of the canonical artifact-index digest (`04a98e3e`), and all exact 11 object names in that namespace returned HTTP 404. Therefore every object has a generation-0 precondition; no positive generation was invented. The packet preserves the artifact-index order, semantic artifact digests, raw file digests, and private flag. `private-truth/case-store.json` remains private and worker-public output remains false.

## Read-only cloud evidence

Absolute SDK used: `/home/matt/google-cloud-sdk/bin/gcloud`, Google Cloud SDK `585.0.0`.

| Read-only command | Exit | Observed result |
|---|---:|---|
| `/home/matt/google-cloud-sdk/bin/gcloud projects describe ocelot-proof --format=json` | 0 | Project `ocelot-proof`, number `141633828616`, lifecycle `ACTIVE`. |
| `/home/matt/google-cloud-sdk/bin/gcloud storage buckets describe gs://p5-evaluator-ocelot-proof-141633828616 --format=json --project=ocelot-proof` | 0 | Bucket exists; project binding matches; location `US-CENTRAL1`; uniform bucket-level access `true`; public-access-prevention `inherited`. |
| `/home/matt/google-cloud-sdk/bin/gcloud iam service-accounts describe p5-evaluator@ocelot-proof.iam.gserviceaccount.com --project=ocelot-proof --format=json` | 0 | Account exists in `ocelot-proof`; unique ID `107880936272403811527`; display name `P5 evaluator control plane`. |
| `/home/matt/google-cloud-sdk/bin/gcloud iam service-accounts get-iam-policy p5-evaluator@ocelot-proof.iam.gserviceaccount.com --project=ocelot-proof --format=json` | 0 | One `roles/iam.workloadIdentityUser` binding for an image-digest principal; no `roles/iam.serviceAccountTokenCreator` observed. |
| `/home/matt/google-cloud-sdk/bin/gcloud storage buckets get-iam-policy gs://p5-evaluator-ocelot-proof-141633828616 --format=json` | 0 | Capability account currently has broad `roles/storage.objectAdmin`; separate conditional `roles/storage.objectUser` binding targets the existing `v3/` prefix; no public principals observed. |
| `/home/matt/google-cloud-sdk/bin/gcloud projects get-iam-policy ocelot-proof ... --filter=bindings.members:p5-evaluator@ocelot-proof.iam.gserviceaccount.com ...` | 0 | Capability account has `roles/cloudkms.signerVerifier`. This is not operation-4 upload evidence. |
| `/home/matt/google-cloud-sdk/bin/gcloud auth list --format=json` and `gcloud config list --format=json` | 0 | Active local caller `hrdwrbob@gmail.com`; configured project `ocelot-proof`. No token/key/ADC material was inspected or created. |
| `/home/matt/google-cloud-sdk/bin/gcloud storage objects describe gs://p5-evaluator-ocelot-proof-141633828616/p5-r0/operation-4/rs069r18r13-op4-04a98e3e/{object_suffix} --format=json` | 1 for each of 11 exact names | All 11 returned `404 not found`; no remote generation, digest, or object metadata observed. |

The packet records the full summarized command/result evidence and the exact object records. The current broad `roles/storage.objectAdmin` grant is not accepted as least-privilege operation-4 evidence. The currently observed image-digest WIF principal is not reused as the exact signed-environment credential binding.

## Desired, not-applied IAM and credentials

The packet proposes, without applying it:

- A project custom role `projects/ocelot-proof/roles/p5R0Operation4BundleWriterV1` containing only `storage.objects.create` and `storage.objects.get`.
- A conditional binding for `serviceAccount:p5-evaluator@ocelot-proof.iam.gserviceaccount.com` whose resource expression starts exactly at `projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/p5-r0/operation-4/rs069r18r13-op4-04a98e3e/`.
- Removal of the current broad capability-account `roles/storage.objectAdmin` grant; this is desired remediation, not evidence of application.
- A separate `roles/iam.serviceAccountTokenCreator` grant on the exact capability account for the exact reviewed signed-environment WIF principal. That principal is intentionally `null` until the signed-environment attestation binding is reviewed; no principal is invented.
- Credential delivery only as an injected short-lived token from the reviewed signed-environment STS → IAM Credentials path. No service-account key, local token, ADC export, or credential-generation action is permitted.

## Conditional one-operation plan

This packet does not authorize execution and does not claim desired IAM is applied. Before one operation-4 attempt, a separate reviewed IaC change must apply and re-observe the narrow IAM proposal, and the exact signed-environment principal/token must be available through the reviewed execution path. Then, subject to a fresh exact child approval bound to `APPROVAL-011` and unchanged packet/index digests:

1. Invoke only the reviewed operation-4 adapter with the injected capability token.
2. GET each exact object without listing; require `404 → ifGenerationMatch=0`, or an exact positive observed generation if a future re-observation finds an existing object.
3. Create only absent objects with generation 0 and GET each created object to verify bytes/digests. Existing exact matches are read-only no-ops; drift fails closed.
4. Append the dedicated operation-4 ledger and stop. Keep Cloud Run, supervisor/run preparation, cleanup/rollback, signing, attestation, timing, and task operations disabled.

No direct `gcloud` mutation, credential generation/key creation, object listing/deletion/overwrite, downstream enablement, or historical-ledger rewrite is part of this plan.

## Local validation and digests

| Artifact | Digest |
|---|---|
| `services/p5_r0_evaluator/deploy/rs069r18r13-gcs-boundary-packet-v1.json` semantic `packet_digest` | `sha256:a8c313f6e5b775b4ba48a8e8ff4cc5e2561c560930c4e89ec2e9666fb509c447` |
| packet raw file SHA-256 | `a6a51ad61d4f03095fc4d5f252a022951ed2bb00987cc72d5d526435d477e45a` |
| `services/p5_r0_evaluator/deploy/gcs_boundary_packet.py` raw file SHA-256 | `6ff3a984d22b5b8411ce81275654d9296b55be4fe0f3a0ec418874d5c9464512` |
| `services/p5_r0_evaluator/tests/test_gcs_boundary_packet.py` raw file SHA-256 | `34be26adb5bca7b1d0d29bfbcfe64a5d0be835dd81c43aff44ecad17e6ebf3b1` |
| artifact index semantic digest | `sha256:04a98e3e48685228fd68ea757de276fe1c1a7ce347bd027a2756a48595897768` |
| unsigned lock digest | `sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df` |

Commands:

```text
PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.gcs_boundary_packet --packet services/p5_r0_evaluator/deploy/rs069r18r13-gcs-boundary-packet-v1.json
# exit 0; 11 objects, expected_generation=0, cloud_operations=[], mutations_performed=false

PYTHONPATH=. python3 -m pytest services/p5_r0_evaluator/tests/test_gcs_boundary_packet.py -q
# exit 0; 5 passed

git diff --check -- services/p5_r0_evaluator/deploy/rs069r18r13-gcs-boundary-packet-v1.json services/p5_r0_evaluator/deploy/gcs_boundary_packet.py services/p5_r0_evaluator/tests/test_gcs_boundary_packet.py
# exit 0
```

The packet, validator, and tests are new local artifacts. The master runsheet and existing R18R13 contract/binding/approval files were not edited. This packet should not be promoted to an executable child approval until the missing credential/WIF and narrow IAM evidence is supplied and independently reviewed.


## Review hardening

The V1 validator additionally binds one absolute SDK probe command/result to each object record (11 exact names, each exit 1/HTTP 404/generation null), cross-checks `request_digest` and `unsigned_lock_digest` against the canonical RS-063 request, and requires the future authenticated receipt shape before success can be reported. These checks are covered by tamper tests; they do not create remote evidence or alter the operation-4 handler.
