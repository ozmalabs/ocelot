# P0-A provisioned Podman acceptance probe

This document specifies the evaluator-owned **test-only** Podman acceptance gate in `tests/evaluation/podman_acceptance.py`. It is not a product launcher, does not modify the Bubblewrap-only production launch path, and does not establish evaluator custody beyond the exact profile tested here. Same-user rootless Podman is not independent evaluator custody.

## Required local inputs and preflight

The requested gate fails closed unless `podman info --format json` proves a local, non-remote rootless engine and the exact cached local base image exists:

`sha256:a6f700b96627c9d19a0147d664febb16fa0039b631cf2351b4c51365048ca962`

It also requires `/usr/share/containers/seccomp.json`. No missing prerequisite is converted to a pass or a fallback. The fresh context contains exactly `evaluation/__init__.py` and `evaluation/p0a/{__init__,agent_worker,agent_protocol,canonical,broker,manifest,simulator}.py`; the explicit Ed25519 `cryptography` closure rooted at the verified `cryptography` module; its required `_rust.abi3.so` extension; the digest-bound hostile target; and a generated non-secret contract. It does not rely on optional `importlib.metadata.distribution(...).files`, copies no `cffi` package or another ambient package, and never copies a checkout directory or mounts any host path. The one required `_cffi_backend` native extension is named explicitly in the manifest because the cryptography Rust extension imports it. Every staged file, source interpreter, package version, and digest is recorded. Before a hostile worker is allowed to start, the evaluator launches the derived local image under the same no-network, read-only, rootless user/mapping, capability, seccomp, namespace, limit, and no-mount profile to import the complete closure through both `/usr/local/bin/python3` and `/usr/local/bin/python3.13` when provided by the pinned image. The check records every loaded path and rejects any missing, unexpected, or non-image package path. The local Containerfile has no `RUN` instruction and only `COPY` operations.

The exact local build profile is:

```bash
podman build --pull=never --network=none --http-proxy=false --layers=false \
  --file <fresh-context>/Containerfile --tag localhost/p0a-acceptance:<nonce> <fresh-context>
```

The evaluator then launches (not the worker) a fresh named container with `Popen(..., close_fds=True)`, only stdio pipes, and this enforced profile: `--pull=never --network=none --read-only --read-only-tmpfs=false`, tmpfs `/workspace:rw,nosuid,nodev,noexec,size=64m,mode=0700`, private user/PID/IPC/UTS/cgroup namespaces, UID/GID `65534:65534`, all capabilities dropped, no-new-privileges, the explicit seccomp policy, limits `pids=64`, memory/swap `256m`, CPUs `0.5`, `nofile=128`, `nproc=64`, `--log-driver=none`, and a fixed minimal environment. There are no `--volume`, `--mount`, devices, group additions, privileged mode, host namespaces, `keep-id`, `--env-host`, or Podman socket mounts.

The image is referenced by the inspected local derived image ID/tag created for that run, not an ambient registry tag. Live inspection requires the exact worker user `65534:65534`; exact `HostConfig.IDMappings` UID/GID maps `0:1:65536`; private PID/IPC/UTS/cgroup namespaces; read-only root; network mode `none`; all capabilities dropped; no-new-privileges; the exact seccomp policy; exact pids/memory/swap/CPU/ulimit/log limits; no bind/volume mounts; and `/workspace` as the sole writable tmpfs. Any absent, malformed, or mismatched field fails the acceptance gate rather than being treated as recorded evidence. Engine-internal mounts are recorded in evidence and are not represented as host paths.

## Probe assertions

Every case uses a new named container. For the legacy **precomputed-export proposal-mediation** probe, the digest-verified worker target submits a complete bounded `GraphActionProposalV1` candidate over stdio; the old opaque proposal-ID frame is rejected by the evaluator protocol. The evaluator verifies the signed native-export attestation and admits the candidate only when it exactly equals its matching canonical record in the evaluator-attested native export; trusted code then projects it. The signed `ActionReceiptV3` records the export/attestation digests and the P0 default-deny `method_not_enabled` result. A candidate that is forged, mismatched, or replayed receives a signed chained denial with zero effects; an unverified candidate is intentionally **not** represented as an attested V3 receipt. A forged raw authority frame must instead result in `sandbox_protocol_violation`, a terminal runtime record, and zero effects.

The stop case starts a worker descendant, records `podman top` plus the init cgroup metadata while live, and stops from the evaluator using `podman stop --time 2 <name>`. It rejects surviving container processes or a nonzero post-stop container PID. The worker cannot select or suppress the stop.

`podman-acceptance-evidence.json` is evaluator-side only (under pytest `tmp_path`, for CI export). It records preflight engine facts, base/derived image IDs, immutable staged input and Containerfile digests, command/profile, full inspect result and mount decision, worker FD/path/network report, sentinel before/after values, receipt/runtime hashes and provenance, descendant snapshot, stop result, and post-stop state. In every case `finally`, the evaluator first lists and counts only the launcher's exact `p0a-<nonce>` container and `localhost/p0a-acceptance:<nonce>` image, confirms both prefixes in this evidence, then stops/removes that container and removes that image tag. This cleanup executes after build, import, or run failures as well; it neither pulls nor prunes images, and never targets a base image, a running/unrelated container, another image namespace, or a non-P0A artifact.

For the evaluator-owned dynamic native execution path, closure table, two-pass reconstruction, and same-user limitation, see [P1 dynamic-native Podman acceptance](P1_DYNAMIC_NATIVE_PODMAN_ACCEPTANCE.md). The local P3 staged-worker readiness profile is documented in [P3-R0 local readiness design](P3_R0_LOCAL_READINESS_DESIGN.md); it consumes provisioned evidence rather than expanding this P0 scope or claiming evaluator custody. The legacy cases in this document remain **precomputed-export proposal mediation** cases; they must not be relabeled as native substrate execution.

Normal test runs skip this file. On a provisioned machine, run exactly:

```bash
P0_RUN_OS_ISOLATION_TESTS=1 P0_OS_ISOLATION_PROVISIONED=1 \
pytest -q tests/evaluation/test_os_isolation_integration.py
```

A missing local image, attempted pull, networked build, rootful or remote service, unsupported hardened flag, failed inspection, evidence mismatch, or inability to externally stop the container is a failure. This probe makes no AppArmor/SELinux/MAC-layer claim and remains evidence for this specific provisioned profile only.
