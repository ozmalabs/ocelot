# P0-A local runtime readiness audit — 2026-10-04

## Scope

Static code inspection and read-only inspection of the current shell runtime.
No worker, proposal, simulator action, process-scope creation, or kill probe was
run. The expansion plan reserves start/stop probes to the project-controlled
evaluation role.

## Findings

| Requirement | Current evidence | Assessment |
|---|---|---|
| Namespace launcher present | `/usr/bin/bwrap`, version 0.9.0; `evaluation/p0a/sandbox.py` constructs user/PID/network/IPC/UTS/cgroup namespaces, an empty root, read-only runtime/agent/input binds, a tmpfs workspace, and seccomp. | Launcher binary is available in this shell; this is not evidence that a complete worker launch succeeds. |
| Seccomp/no-new-privileges baseline | Current process reports `Seccomp: 2` and `NoNewPrivs: 1` in `/proc/self/status`. | Confirms confinement on this inspection process only; does not attest the future worker. |
| Whole-worker externally killable scope | `sandbox.py` defines `CgroupController` and `WorkerScope` as protocols; `entrypoint.py` requires `controller.create_scope()` before worker exec. No concrete controller implementation is present under `evaluation/p0a`. `/sys/fs/cgroup` is cgroup v2, lists `cpuset cpu io memory hugetlb pids rdma misc`, and is mounted `dr-xr-xr-x nobody:nogroup`; this process is uid 1000. | No delegated writable cgroup scope or evaluator controller is evidenced. External process-group kill remains unverified. |
| Evaluator input mount custody | `evaluation/p0a/mounts.py` labels `LocalMountContract` a local approximation; it stages files and applies mode `0400`. | Same-UID file permissions are not a read-only mount or separate custody authority. |
| Evaluator-controlled orchestration | `evaluation/p0a/entrypoint.py` requires a supplied launcher, run-bound scope, and `CgroupSupervisor`; the module docs explicitly characterize this harness as local-only. | Interfaces and fail-closed checks exist, but no project-controlled launcher/controller/key custody is evidenced here. |

Runtime snapshot: Linux `6.8.0-142-generic`, x86_64; `bwrap 0.9.0`; cgroup v2; current process `NoNewPrivs=1`, `Seccomp=2`; `/sys/fs/cgroup` read-only. Relevant source SHA-256 values at inspection:

- `evaluation/p0a/sandbox.py`: `06e070131588f801807b35ec5d986b0906e2795e6640a1b29f90e2dbcc6afade`
- `evaluation/p0a/mounts.py`: `3dc06c68fc1df757a0e13e76055d156ce0157b520ec79223f9a43cd8a3c83b37`
- `evaluation/p0a/supervisor.py`: `1fc485d034398e944387f9119a7f64567e3ede436679458b6fade322116207ee`
- `evaluation/p0a/entrypoint.py`: `f065a46be29a53966d26bfad99f1e6bfbb9084e6727c0ca69ac75fa3f2abeb82`

## Gate disposition

P0-A remains **no-go for worker launch**. The concrete unresolved prerequisites
are a project-controlled evaluator/launcher, a delegated run-bound cgroup
controller and external kill authority, and actual read-only/write-only mount
and channel attestation. `bwrap` availability and the current shell's seccomp
state do not satisfy these requirements. The shell-level Landlock fallback
reported by the operator is useful for this development environment, but no
evidence currently binds it to a P0 worker image or an evaluator-held run.

The next admissible work is to provision evaluator-owned cgroup scopes and
mount/channel custody, then capture the P0-A route/interception inventory and
complete its prescribed 100 kill and 200 control-plane adversarial probes in
two fresh reruns. Until that exists, capability experiments remain
noninteractive research evidence and cannot authorize agent action or learned
artifact adoption.
