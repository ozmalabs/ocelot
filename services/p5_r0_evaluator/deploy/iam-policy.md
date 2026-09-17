# Runtime IAM (not applied by this change)

Use a dedicated `p5-evaluator@PROJECT_ID.iam.gserviceaccount.com` runtime identity and a separate `p5-runner@PROJECT_ID.iam.gserviceaccount.com` invoker identity. Grant the runtime identity only:

- `storage.objects.get` on `locks/`, `manifests/`, and `truth/` objects;
- `storage.objects.get`, `storage.objects.create`, and the minimum object update permission needed for generation-checked `runs/` state (receipts/evidence/seals are create-only in application code);
- `cloudkms.cryptoKeyVersions.useToSign` and public-key read on the single configured Ed25519 key version.

Grant the runner identity only Cloud Run `run.invoker`; it receives no GCS or KMS permissions. Keep bucket retention/lock and KMS administration with separate custodians. Apply IAM conditions/prefix-scoped custom roles in the target project; this file intentionally contains no project identifiers, credentials, or deployment command.


The Cloud Run service must use internal ingress (not `internal-and-cloud-load-balancing` or `all`). The application endpoints are not public APIs; enforce the Cloud Run invoker binding and the application OIDC allowlist together. Runtime configuration must bind the immutable image, evaluator runtime, and resource-profile digests through `P5R0_IMAGE_DIGEST`, `P5R0_RUNTIME_DIGEST`, and `P5R0_RESOURCE_PROFILE_DIGEST`; these values are commitments, not secrets.
