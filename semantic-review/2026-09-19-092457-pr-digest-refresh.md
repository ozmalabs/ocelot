# Controlled-run digest refresh and non-release boundary review

This documentation refresh updates the RS-063 evidence packet to the current generated artifact, lock-request, controlled-run, and execution-request commitments after the RS-068 renderer change. The current generated artifact index, diagnostic manifest, unsigned lock request, RS-068 proposal, and RS-069 plan can be independently rehashed and their shared RS-062/065 commitments agree. Two current records still carry superseded source digests: the controlled-run manifest embeds the prior RS-063 request digest, and the master runsheet reports the prior RS-069 plan digest. The request, proposal, plan, and manifest continue to describe repository-only, blocked, non-release state; no signed or production result claim was introduced.

Watch for: **confirmed** the current controlled-run manifest is internally hashed but still binds RS-063 to `sha256:7378f39e…` instead of the current request `sha256:d82fbce4…`; **confirmed** the current master runsheet still reports RS-069 plan digest `sha256:6fa81383…` instead of the validator’s current `sha256:418e5640…`. These records need refresh before the cross-stage documentation can be considered fully consistent.

**Verdict**: NEEDS_CHANGES

## High-level view

The shared generated-input chain is consistent: artifact index `sha256:04a98e3e…`, generated manifest `sha256:190fe19f…`, lock request `sha256:922085ca…`, and unsigned lock `sha256:4fc80599…` are the values used by the current RS-065/067/068/069 records and the RS-063 request.

**Confirmed:** the stored controlled-run manifest has outer digest `sha256:ec4a44b8…`, but its RS-063 source and validator-report commitments still contain `sha256:7378f39e…`. Fresh materialization emits the current request binding `sha256:d82fbce4…`, so the stored manifest is stale even though its own outer digest validates.

**Confirmed:** the current master runsheet’s RS-069 row still records `sha256:6fa81383…`; the current plan validator reports `sha256:418e5640…`, `ready=false`, and no cloud operations. The old value is present in prior review records, but the runsheet is a current operational record.

The signed/production boundary remains closed: signatures and authority bindings are null, promotion and cloud-operation flags are false, mutation steps are disabled, validation is not ready, and no signed execution evidence exists.

<details>
<summary>Issues (2)</summary>

1. **Current controlled-run manifest commitment** — **confirmed:** `var/p5-r0-controlled-run/manifest.json` binds RS-063 to the superseded `sha256:7378f39e…` while the current request and materializer use `sha256:d82fbce4…`; regenerate the manifest and refresh its dependent documentation.
2. **RS-069 runsheet digest** — **confirmed:** `P5_MASTER_RUNSHEET.md` records superseded plan digest `sha256:6fa81383…` while the current validator reports `sha256:418e5640…`; update the current runsheet and keep its separate approval-scope digest distinct.

</details>

<details>
<summary>Details</summary>

### Shared generated commitments across RS-063, RS-065, RS-067, RS-068, and RS-069

**Confirmed:** current generated files recompute to the documented values. The artifact index is semantic/raw `sha256:04a98e3e48685228fd68ea757de276fe1c1a7ce347bd027a2756a48595897768` / `sha256:23ec2e4863660c9d38adfaa615fe5eac75d0aac0c6692e5903cd1879c7077bfb`; the generated diagnostic manifest is `sha256:190fe19fe7f70b181f11f0b375cf6241a2cc2c0c49abbf2b52f8ce8899b2f01a` / `sha256:78694af8056e5d141546ba15b9e489aa3afe7e05e74653bb94ab0b00cb4794d5`; the unsigned lock request is semantic `sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d` with raw file digest `sha256:0e8d1f306446ba4e62d31f3eaab523430b372671772db0593516a702bee5f45`; and the nested unsigned lock is `sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df`. RS-065 and RS-067 retain the request/lock pair, while the RS-068 proposal and RS-069 plan bind the same pair. RS-069 also carries the current artifact-index, manifest, private-store, task-set, and control-commitment values used by RS-063.

**Confirmed:** the current RS-063 request and packet agree on execution-request digest `sha256:d82fbce481c116d3865c8ade409253ab9b659519870783eeb5bf99151f11e743`; the RS-068 proposal’s current semantic/raw digest is `sha256:35e0317cf7ef2b1a1f012aef23d6cfa445392b50331fbda21a41388c847e415b`; and the current RS-069 plan’s full semantic digest is `sha256:418e5640229c62c64d367017fde945f54d391317b197b63002c6831159eaa52c` with raw file digest `sha256:b65f1eb3a2242815fd728a0da1a7ac1ced8335c8cb469bc4bfb61168a58e4330`. The RS-069 approval-scope digest is a separate derived domain from the full plan digest and must not be substituted for it.

### Stale RS-063 commitment in the current controlled-run manifest

**Confirmed:** `var/p5-r0-controlled-run/manifest.json` records `source_commitments.rs063.file_digest` and `.semantic_digest` as `sha256:7378f39e6be5c5fd94f8aa341cd5ceb89dc457d87178b579bfdc3be13b5dbb60`, and its `validator_reports.RS-063.definition_digest` repeats that value. The actual request file, current validator audit, and fresh `controlled_run_materializer.materialize()` output use `sha256:d82fbce481c116d3865c8ade409253ab9b659519870783eeb5bf99151f11e743`. The evidence packet labels `7378f39e…` historical and says the manifest was not rewritten, but the manifest is still the current controlled-run artifact rather than a historical review record.

Regenerate the controlled-run manifest from the current materializer, verify its new outer manifest and raw-file digests, and refresh packet or downstream references that record the manifest’s outer commitment. Keep the old `7378f39e…` value only in historical review records or an explicitly archived prior-manifest record.

### Stale RS-069 digest in the current master runsheet

**Confirmed:** `docs/research/engine_substrate/P5_MASTER_RUNSHEET.md` reports `sha256:6fa813832770f9034e31b66a78413f2c6eaea40b58f1dd7297e4fefa0cd04cb1` for RS-069, while the checked-in plan loaded by `rs069_change_plan.validate_plan()` reports `sha256:418e5640229c62c64d367017fde945f54d391317b197b63002c6831159eaa52c`, with `blocked_pending_master_approval`, `ready=false`, and `cloud_operations=[]`. The `6fa81383…` value remains in earlier RS-069 review documents as historical context, but the master runsheet is the current operational record.

Refresh the RS-069 runsheet digest to the validator’s current full-plan digest, and distinguish it from the separate approval-scope digest used inside approval records. Do not change RS-069 to an applyable or production state as part of this documentation correction.

### Signed and production claim boundary

**Confirmed:** no signed or production claim was introduced. RS-063 remains `blocked_pending_approval` with `definition_digest=d82fbce4…`, `ready=false`, and no cloud operations; the RS-065/067 contracts retain null authority/signature material; RS-068 remains `BLOCKED` with `signature_present=false`, `authority_created=false`, and `production_promotable=false`; RS-069 remains blocked with unresolved production inputs and no commands; and the controlled-run manifest says `execution_evidence_present=false`, `signature_generated=false`, `production_promotable=false`, and `cloud_operations=[]`.

The proposed state is **NEEDS_CHANGES for documentation consistency only**. After the two current-record refreshes, retain RS-063/065/067/068/069 as repository-only `PASS_REVIEW` evidence, preserve the overall `NO_GO`/blocked decision, and perform no cloud, KMS, signing, ingestion, deployment, supervisor, or task operation.

</details>

<details>
<summary>File map</summary>

- `docs/research/engine_substrate/RS-063_EVIDENCE_PACKET.md` — refreshed RS-063 commitments and explicit historical-manifest note.
- `var/p5-r0-controlled-run/manifest.json` — current controlled-run manifest with stale embedded RS-063 source commitment.
- `var/p5-r0-diagnostic-inputs/artifact-index.json` — current generated artifact-index commitment.
- `var/p5-r0-diagnostic-inputs/public/lock-signing-request.json` — current unsigned request and lock commitments.
- `var/p5-r0-diagnostic-inputs/public/rs-068-authority-binding-proposal.json` — blocked unsigned RS-068 proposal.
- `services/p5_r0_evaluator/deploy/p5-r0-signed-environment-execution-request.json` — current blocked RS-063 request.
- `services/p5_r0_evaluator/deploy/rs-069-iac-change-plan.json` — current blocked RS-069 plan.
- `docs/research/engine_substrate/P5_MASTER_RUNSHEET.md` — current runsheet containing the stale RS-069 digest.
- Full diff/reference: `git diff main` plus the untracked generated and evidence artifacts in the working tree.

</details>
