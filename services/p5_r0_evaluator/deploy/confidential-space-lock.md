# Confidential Space lock and release checklist

The adapter stays locked until a verified Confidential Space launcher token with the WIP token audience (default `https://sts.googleapis.com`) is exchanged through the exact WIP provider resource. The launcher request is an HTTP POST for `/v1/token` over `/run/container_launcher/teeserver.sock` with canonical JSON `{audience, token_type: "OIDC", nonces: [opaque_nonce]}`; the later RFC 8693 STS `audience` is the exact provider resource. There is no metadata hostname, URL path, DNS lookup, or production URL override.

## Immutable inputs to freeze

Record the exact values in the deployment change, never in source control as secrets:

- production image **digest**, not a tag;
- runtime and resource-profile digests;
- project number and project ID;
- one allowed zone;
- verified Confidential Space token issuer and the actual claim paths for image, project, zone, debug, TEE, secure boot, workload, standard audience/nonce/time claims, and `exp`;
- WIP token audience (default `https://sts.googleapis.com`) and WIP provider resource name, frozen as separate values; the provider resource is the exact STS exchange/IAM binding;
- one KMS Ed25519 key version and the matching public authority digest;
- the exact GCS capability service account (`P5R0_CAPABILITY_SERVICE_ACCOUNT`, normally `p5-r0-gcs-only@PROJECT_ID.iam.gserviceaccount.com`) that owns only the reviewed operation-4 GCS grants; the KMS authority account is separate;
- the private GCS bucket `p5-evaluator-ocelot-proof-141633828616` and exact operation-4 run prefix `p5-r0/operation-4/rs069r18r13-op4-04a98e3e/`;

The claim paths must be copied from a real token obtained from the target Confidential Space image and then reviewed. The production defaults are `aud`, `eat_nonce`, `iat`, `exp`, `iss`, `sub`, `submods.container.image_digest`, `submods.gce.project_number`, `submods.gce.project_id`, `submods.gce.zone`, `dbgstat`, `swname`, `hwmodel`, `secboot`, and `submods.container.env.P5R0_EXPECTED_WORKLOAD`; the production issuer is `https://confidentialcomputing.googleapis.com`. A token is not accepted merely because it parses as a JWT: signature, issuer, audience, expiry, nonce, exact image digest, project, zone, debug-disabled, TEE, hardware-model, workload, and secure-boot checks all have to pass.

## Capability boundary

The locked bootstrap parses only this non-secret policy. It does not instantiate Google Storage/KMS clients, read GCS, load truth, read ADC, accept a service-account key, or export a private key. After the gate, STS returns a short-lived federated access token. The capability factory immediately exchanges that explicit token through the fixed IAM Credentials `generateAccessToken` endpoint for the committed `P5R0_CAPABILITY_SERVICE_ACCOUNT`; only the resulting bounded-lifetime token is passed to GCS and KMS. The timing bridge remains separate and uses the original federated token for its own `generateIdToken` target. There is no metadata hostname, URL path, DNS lookup, or production URL override.

GCS is restricted in code and IAM to reads of `locks/`, `manifests/`, `truth/`, and run state, plus generation-checked creates/replaces below `runs/`. There is no list, delete, bucket-admin, or worker-facing storage capability. KMS is restricted to public-key read and signing on the one pinned Ed25519 key version. The signer verifies the public key and every signature locally; private key material never enters the process.

The worker receives only the authenticated task protocol. It receives no GCS, KMS, STS, metadata, or capability-factory object. `native_verified` remains false and the existing evaluator emits signed impasse/receipt outputs rather than truth or a positive claim.

## WIP policy workflow

1. Obtain and verify one representative token from the exact immutable image.
2. Replace all `REPLACE_*` values and claim paths in the metadata example in the reviewed deployment system.
3. Render the WIP provider mapping/condition from `wip-provider-policy.cel.tmpl`.
4. Have IAM/security reviewers confirm direct resource grants are limited to the provider principal set and one key version/bucket prefix.
5. Apply resources separately through the approved infrastructure process. This repository does not create a pool, provider, VM, bucket, key, or permission.
6. Test failed attestation, wrong digest, debug enabled, wrong zone/project, expired token, STS failure, KMS mismatch, and GCS path violations locally before any deployment review.
