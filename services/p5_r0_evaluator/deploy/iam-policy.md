# Runtime IAM (not applied by this change)

# The GCS operation-4 capability is deliberately separate from the existing
# KMS-capable evaluator account.  The deployment must bind the reviewed
# p5-r0-gcs-only account after IAM provisioning; the KMS authority path uses
# its own separately reviewed account.
Use the dedicated `p5-r0-gcs-only@PROJECT_ID.iam.gserviceaccount.com` capability service account for operation-4 GCS access, configured as the locked `P5R0_CAPABILITY_SERVICE_ACCOUNT` value. After attestation and STS, the evaluator uses the original federated token only to call the fixed IAM Credentials `generateAccessToken` endpoint for that exact account; GCS receives only the resulting short-lived token. Grant the WIP provider principal set only `roles/iam.serviceAccountTokenCreator` on this account. Grant this capability account only the reviewed custom create/get role on the exact operation-4 run prefix. Do not grant the provider principal direct GCS access.

The existing `p5-evaluator@PROJECT_ID.iam.gserviceaccount.com` account remains the KMS-capable authority identity and must not be reused for GCS. The current shared capability bootstrap is therefore not an applied/runtime-ready state: a reviewed KMS-specific token path must be wired before any signer use. The timing bridge target account is separate (`P5R0_TIMING_BRIDGE_SERVICE_ACCOUNT`) and continues to receive `generateIdToken` requests using the original federated token. Do not reuse the bridge account as the evaluator capability account unless separately reviewed.


The Cloud Run service must use internal ingress (not `internal-and-cloud-load-balancing` or `all`). The application endpoints are not public APIs; enforce the Cloud Run invoker binding and the application OIDC allowlist together. Runtime configuration must bind the immutable image, evaluator runtime, and resource-profile digests through `P5R0_IMAGE_DIGEST`, `P5R0_RUNTIME_DIGEST`, and `P5R0_RESOURCE_PROFILE_DIGEST`; these values are commitments, not secrets.
