# Digest-bound authenticity repair for RS-069R15

The R15 repair separates local build provenance from remote image identity and stops projecting either remote provenance or repository immutability when no corresponding observation exists. The corrected candidate binding and interpretation artifact preserve the R14 image digest while leaving both unsupported remote claims `null`, and the historical operation ledger is unchanged. The focused regression suite passes 24 tests and the reviewed commands performed no cloud operation. **Watch for:** **confirmed** — positive remote provenance and immutability claims still accept a caller-authored self-digesting record without verifying that a remote boundary produced it; **confirmed** — registry digest and publication fields admit malformed digest text and integer boolean substitutes; **confirmed** — the no-cloud result is exercised indirectly rather than protected by a direct subprocess guard test.

**Proposed state**: `RS-069R15 = NEEDS_CHANGES`. The current null-only projection is safe for review, but the validator must not authorize future positive remote claims until the evidence and type boundaries are tightened.

**Verdict**: NEEDS_CHANGES

## High-level view

The current projection preserves the intended claim boundary: local provenance remains verified, the Artifact Registry digest observation remains separate, and remote provenance and immutability remain unknown. This keeps unsupported remote claims truthful as `null` instead of upgrading a local build record or a digest lookup.

The positive-evidence path is more than shape-only validation, but **confirmed** — it is not yet provenance verification. The loader recomputes canonical record and outer evidence digests and binds operation, request, image, source, and command values; because the evidence is supplied by the caller and no signed or independently fetched artifact is checked, a fabricated record can still pass those checks.

The historical boundary is intact: the 30-record ledger and its hash chain were not rewritten, later operations remain disabled, and the focused tests complete without invoking operation 1. **confirmed** — two input-validation gaps—non-boolean publication flags and non-cryptographic digest strings—must be closed before any positive remote state is treated as authoritative.

<details>
<summary>Issues (4)</summary>

1. **Caller-authored remote evidence** — **confirmed**: self-digests and field bindings do not prove that a remote provenance lookup or immutability observation occurred. Require an authenticated canonical evidence artifact from the approved remote boundary, or reject positive claims.
2. **Non-boolean publication flags** — **confirmed**: integer `0`/`1` values pass the `{False, True}` membership checks for registry verification and push state. Require exact booleans and add regression cases for both fields.
3. **Malformed registry digest accepted** — **confirmed**: `sha256:x` can be carried through a self-consistent candidate as a positive registry digest. Apply the full 64-hex digest predicate to every image and remote digest field.
4. **Indirect no-cloud coverage** — **confirmed**: the suite avoids the cloud path through stale approval, but does not assert that cloud-capable subprocesses are not called. Add a direct subprocess/network guard test for the local repair path.

</details>

<details>
<summary>Details</summary>

### Self-digesting remote evidence is not independently verifiable

`_validate_canonical_remote_evidence()` recomputes `record_digest` and `evidence_digest`, then checks exact request, operation, image, resource, command, and timestamp bindings. **confirmed** — those checks establish canonical integrity and internal consistency, not that the remote lookup or policy observation occurred. The test helper constructs the entire “valid” evidence object locally, and `test_valid_digest_bound_remote_provenance_evidence_is_accepted` accepts it without a signature, fetched artifact, attestation verification, or trusted evidence-store reference. The same is true for the immutability helper.

This conflicts with the repository evidence contract that fabricated or caller-supplied evidence is not execution evidence. **confirmed** — the positive path needs an authoritative evidence boundary: for example, a canonical remote artifact whose bytes are fetched from the approved source and whose digest is recomputed, plus whatever remote signature/attestation or independently authenticated observation is required for that claim. Until then, positive remote claims should remain rejected or restricted to evidence produced by the actual operation handler rather than accepted from the binding JSON.

### Registry identity and publication types are not closed tightly enough

The candidate loader tests `target["registry_digest_verified"] not in {False, True}` and `target["push_performed"] not in {False, True}`. **confirmed** — Python equality makes integer `0` and `1` members of that set; a canonical candidate with `registry_digest_verified=0` or `push_performed=0` is accepted. The repair’s non-boolean test covers remote provenance but not these adjacent publication claims, so the stated fail-closed caller-value boundary is incomplete.

The same loader accepts any value beginning with `sha256:` for `candidate.image_digest`. **confirmed** — a canonical binding using `sha256:x`, with all references and commitments made internally consistent, is accepted as `registry_digest_verified=true`; the positive registry claim therefore is not guaranteed to name a 256-bit digest. Require `type(value) is bool` for these flags and `_DIGEST_RE.fullmatch()` for every image, observed, and remote digest field before accepting a positive registry result.

### Historical ledger and no-cloud test boundary

The preserved ledger has 30 records, raw digest `sha256:7e4835d39c7cd0abe56adbf159179cf73546018f5db09de56b5ce6b2c0bf1d9a`, and final event digest `sha256:7545a9083e8bfb41a9380e3a90b41a603be7df7d91d1a25f07721cef34bdd953`; recomputation of the event chain succeeds. **confirmed** — the R15 artifacts and ledger-adjacent correction are canonical, and the master runsheet remains unchanged with R15 still `IN_PROGRESS`, so this review cannot be treated as master acceptance or production authorization.

`PYTHONPATH=. python3 -m pytest -q services/p5_r0_evaluator/tests/test_rs069_apply_runner.py` passes 24 tests, and both reviewed Python files compile. **confirmed** — those tests stop before the cloud-capable operation path because the stale approval/binding boundary rejects execution, but they do not monkeypatch or assert that `subprocess.run`, `gcloud`, or `podman push` is unreachable during this local repair. The current no-cloud claim is supported for this review execution, while a direct regression test would make the boundary durable.

## File map

<details>
<summary>Reviewed records</summary>

- `services/p5_r0_evaluator/deploy/rs069_apply_runner.py` — canonical remote-evidence validation, candidate projection, approval boundary, and operation gate.
- `services/p5_r0_evaluator/tests/test_rs069_apply_runner.py` — R15 projection, adversarial evidence, approval, and fail-closed regression coverage.
- `var/p5-r0-rs069r1/candidate-image-binding.json` — corrected registry-bound candidate projection with truthful remote nulls.
- `var/p5-r0-rs069/r15-provenance-interpretation.json` — ledger-adjacent interpretation correction.
- `var/p5-r0-rs069/operation-ledger.jsonl` — preserved append-only R14 history.
- `docs/research/engine_substrate/RS-069R15_PROVENANCE_CORRECTION.md` — stated correction boundary and proposed state.
- `docs/research/engine_substrate/P5_ATTESTED_RESULT_REQUIREMENTS.md` — canonical/fabricated-evidence requirements used for the review.
- `docs/research/engine_substrate/P5_MASTER_RUNSHEET.md` — master-controlled state and no-go boundary.

Full comparison input: `git diff main`; the repair runner/tests are untracked in this working tree, so their current files and referenced artifacts were reviewed directly. The repository also contains unrelated dirty changes outside this repair scope.

</details>
