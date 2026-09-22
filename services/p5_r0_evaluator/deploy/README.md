The Cloud Run YAML is a reviewable manifest only. Replace placeholders and apply IAM through the target project's reviewed change process; this task does not deploy or create service accounts, buckets, keys, or permissions.

The Confidential Space adapter artifacts are review-only: `Dockerfile.confidential-space`, `Containerfile`, `confidential-space.metadata.example`, `confidential-space.allowed-env`, `confidential-space.policy.example.json`, `confidential-space-lock.md`, and `wip-provider-policy.cel.tmpl` contain non-secret policy placeholders only. The metadata file must remain non-secret; the closed claim paths, WIP token audience (default `https://sts.googleapis.com`), and canonical WIP provider resource must be frozen from a real token and reviewed separately before policy rendering. No cloud resources are created by tests or by this change.

The dedicated image launches `services.p5_r0_evaluator.confidential_space_app:application`, not the Cloud Run `app:application` entrypoint. Its `/healthz` response remains `locked` until attestation, STS/WIP exchange, fixed IAM Credentials `generateAccessToken` impersonation to `P5R0_CAPABILITY_SERVICE_ACCOUNT`, and explicit capability construction succeed. `/startup-attestation` reports only policy bindings and digests of the launcher JWT, claims, nonce, and federated token; it never returns those secret-bearing values.

The locked bootstrap rejects extra authority fields, private-key-like material, malformed public-key bindings, unknown claim paths, noncanonical WIP provider forms, and provider-as-token-audience confusion before an attestation request is made. Its production claim defaults follow the official token shape: issuer `https://confidentialcomputing.googleapis.com`, `eat_nonce`, nested `submods.container.image_digest`/`submods.gce.*`, `dbgstat`, `swname`, `hwmodel`, `secboot`, and the committed workload environment claim. `P5R0_ALLOWED_SUBJECTS` remains the exact caller/application identity allowlist; the separate `P5R0_ATTESTATION_SUBJECT_PREFIX` is the immutable project/zone Compute self-link prefix for the attested VM JWT subject and must end in `/instances/`. The adapter requests the default WIP OIDC token audience `https://sts.googleapis.com` (custom HTTPS audiences must remain explicitly separate from the provider) by POSTing canonical JSON `{"audience": ..., "token_type": "OIDC", "nonces": [opaque_nonce]}` to `/v1/token` over the fixed launcher Unix socket `/run/container_launcher/teeserver.sock`; metadata-host URLs, DNS, redirects, and URL overrides are not part of the production path. It verifies the JWT signature, issuer, exact token audience, 10-74-byte nonce, expiry/time claims, VM subject prefix, and exact image/project/zone/debug/TEE/secure-boot/workload claims, then exchanges it through the exact canonical WIP provider resource as the STS audience, impersonates the committed `P5R0_CAPABILITY_SERVICE_ACCOUNT` through fixed IAM Credentials `generateAccessToken`, and creates explicit GCS/KMS clients with only the resulting short-lived token. The independent timing bridge, when configured, continues to use the original federated token for its separate `generateIdToken` target.

After activation, the bundle-read capability can issue a child capability for one derived run only. State, receipts, timing, evidence, observations, seal, and idempotency objects must remain below `runs/{run_id}/`; traversal, slash normalization, cross-run paths, and bundle writes are rejected. Local KMS timing records are diagnostic and cannot set `timing_certified`; only signed, independently pinned V2 ledger records may do so.

Terminal result seals are V4 signed commitments. The close receipt binds the commitment digest, and `/result` re-verifies the seal signature, commitment, terminal receipt, complete receipt hash/signature chain, final digest, and count before serving it. Persistence failures are fail-closed.

The manifest deliberately uses `run.googleapis.com/ingress: internal`, max scale one, and an immutable image digest. Before review/apply, render every authority, WIP, claim-path, endpoint, image, KMS, bucket, and runtime commitment value from one reviewed policy. A deployment gate must reject any `REPLACE_`, `PROJECT_`, `POOL`, `PROVIDER`, `LOCATION`, `VERSION`, or `REVIEWED_` placeholder and must reject `P5R0_IMAGE_DIGEST` as a substitute for `P5R0_EXPECTED_IMAGE_DIGEST`. Never put credentials, tokens, private keys, truth, or signed assertions in these artifacts.

Local validation (no cloud mutation):

```text
PYTHONPATH=. python3 -m pytest services/p5_r0_evaluator/tests -q
python3 -m py_compile services/p5_r0_evaluator/*.py services/cs_attestation_probe/probe.py
```

Review-only image and VM commands are available from
`confidential_space_commands(policy, vm_name)`. The exact sequence is:

```text
docker build --file services/p5_r0_evaluator/Dockerfile.confidential-space --tag REGION-docker.pkg.dev/PROJECT_ID/p5-cs/evaluator:candidate .
docker push REGION-docker.pkg.dev/PROJECT_ID/p5-cs/evaluator:candidate
gcloud artifacts docker images describe REGION-docker.pkg.dev/PROJECT_ID/p5-cs/evaluator:candidate --project=PROJECT_ID --format=value(image_summary.digest)
gcloud compute instances create VM_NAME --project=PROJECT_ID --zone=ZONE --machine-type=n2d-standard-2 --confidential-compute-type=SEV --maintenance-policy=TERMINATE --image-family=confidential-space --image-project=confidential-space-images --metadata='^|^$(awk '\''BEGIN { sep="" } /^[[:space:]]*#/ || NF == 0 { next } { key=$1; sub(/^[^=]*=/, ""); printf "%s%s=%s", sep, key, $0; sep="|" }'\'' rendered-p5-evaluator.metadata)'
```

Replace the uppercase terms only after the digest is resolved and the reviewed
policy renderer has produced `rendered-p5-evaluator.metadata`; do not run this
sequence as part of local tests. The metadata command uses a custom delimiter so
JSON authority values retain their commas, and includes both
`tee-image-reference` and `tee-container-log-redirect=true`.


## RS-040 repository definition (authoritative local source)

`p5-r0-native-deployment.json` is the checked-in RS-040 definition for the
native closure and deployment boundary. It records the exact `crun` runtime,
`--pull=never`/`--network=none` policy, read-only/drop-capability argv,
`65532:65532` identity, fixed resource profile, seccomp path/default action,
full V3 host closure, and the existing `DeploymentPolicy` renderer/preflight
entry points. The production bindings are intentionally `null`: no candidate
image, runtime/seccomp/host digest, authority, token claim record, private
truth, task set, or supervisor evidence is invented here.

Validate the definition without any cloud access:

```text
PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.definition validate --allow-blocked
```

The command must report `ready: false` until reviewed production inputs are
provided. Running it without `--allow-blocked` exits non-zero and is the
required gate before rendering. After the master has supplied and reviewed the
complete definition and a separate policy input exists, render only local
review artifacts:

```text
PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.definition render --policy services/p5_r0_evaluator/deploy/p5-r0-deployment-policy.json --output-dir var/p5-r0-rendered
```

The render command calls `render_deployment` and `preflight_deployment`, writes
metadata/CEL/VM/Containerfile artifacts, and never invokes `gcloud`, Docker,
Podman, an image push, IAM, a VM, or a deployment. The JSON apply plan is
review-only and contains no executable commands. Any later infrastructure
change must first update this definition, pass local validation, and receive a
separate master-approved apply decision through the approved IaC workflow.


## RS-060 production-bundle definition (repository-only)

`p5-r0-production-bundle.json` is the checked-in, re-runnable RS-060 definition. It records the canonical digest implementation, repository-relative input locations for the manifest, explicit private store, production lock, self-custodied authority trust binding, KMS authority binding, worker/evaluator contracts, policy, and task-set commitment. Those reviewed input locations and all expected commitments are intentionally `null`; private truth, authorized tasks, candidate digests, signature material, and P5 results are explicitly blocked and are not created here.

The validator composes the existing `evaluation/p5_r0` manifest/private-store integrity checks with a separate production-lock contract. It rejects local-readiness locks, noncanonical JSON, path escape, digest drift, authority/KMS binding drift, worker/evaluator/policy/task-set drift, and invalid production-lock signatures. It performs no cloud, credential, KMS, secret, container, deployment, or timing-endpoint operation.

Run the auditable preparation report, which writes only a canonical blocked audit record:

```text
PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.bundle_definition prepare --allow-blocked --audit-output var/p5-r0-bundle-preparation.json
```

Validate the checked-in definition in blocked mode:

```text
PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.bundle_definition validate --allow-blocked
```

Strict validation intentionally exits non-zero until reviewed inputs and exact commitments are supplied:

```text
PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.bundle_definition validate
```

The preparation audit is not a production bundle and does not authorize RS-070 task release, candidate use, infrastructure mutation, or any P5 result claim. Any future populated definition must remain a reviewed repository artifact and must be independently accepted by the master session.
