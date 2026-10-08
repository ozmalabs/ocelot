# Live self-report all-scope work trace v1.2 amendment

Date: 2026-09-28  
Status: isolated source snapshot after two shared-worktree drift censures.

## Reason

V1 attempt 1 changed `domains/comprehend_text.py` during worker 0. V1.1 aligned its lock to actual loader inputs, but `substrate/world_adapter.py` changed during worker 1. These were concurrent edits in the shared worktree, not workload failures. Both raw attempts and locks are preserved and excluded.

## Amendment

- Keep v1 prompts, task criteria, counter equations, and scheduler/deferred instrumentation unchanged.
- Capture a source closure manifest from the live worktree twice and require exact equality before snapshotting.
- Copy the locked Python runtime, bindings/native extension, full Rust-source fingerprint inputs, selected seed manifests, protocol, and runner/analyzer into an isolated `/tmp` tree. Use the existing repository only for unmeasured support paths; copy all source families named by the v1.1 lock so task execution imports the isolated versions.
- Hash the copied source closure and require it to match the stable live-worktree manifest before lock/capture. Workers then run only from this isolated tree.
- Save the snapshot source bundle and lock with the result so later replay does not depend on the mutable worktree.
- Use new v1.2 lock/raw/analysis paths; refuse overwrite.

The three-worker source stability gates remain in force. The isolated snapshot is the source of truth for this capture; the current main-worktree contents may continue to evolve independently.

## Claim boundary

The snapshot pins Python and seed inputs selected by `load_all_seeds`, the imported adapter/binding source trees, all Rust files used by the extension build fingerprint, and the native extension/build record. It does not pin the host kernel, installed third-party packages, or data reached through runtime paths outside those source/manifest closures. Task or counter claims remain limited to the declared live self-report workload.
