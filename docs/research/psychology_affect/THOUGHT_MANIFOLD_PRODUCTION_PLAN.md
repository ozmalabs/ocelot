# Thought-Manifold Production Plan

**Status:** planning only; no production capability or general-agency claim.

**Parent plans:**

- [`GENERAL_INTELLIGENCE_EXPANSION_PLAN.md`](../engine_substrate/GENERAL_INTELLIGENCE_EXPANSION_PLAN.md) — canonical P0–P5 roadmap and gate thresholds.
- [`GENERAL_INTELLIGENCE_EXECUTION_LEDGER.md`](../engine_substrate/GENERAL_INTELLIGENCE_EXECUTION_LEDGER.md) — execution, provenance, custody, and blocker record.
- [`CAPABILITY_SUITE_PLAN.md`](CAPABILITY_SUITE_PLAN.md) — local T1–T5 capability-evidence plan.
- [`evaluation/p5_r0/PREREGISTRATION.local.md`](../../../evaluation/p5_r0/PREREGISTRATION.local.md) — local-only P5-R0 boundary.

## 1. Scope and non-claims

This plan defines how the landed thought-manifold arc can become a versioned, bounded, evaluator-reviewable capability package. It covers blocks 348–351:

- concept-region and aperture-grain trajectory control;
- discrete width/deviation quanta;
- optional global-workspace broadcast/competition and ignition silence;
- persistence-gated dimension minting and duplicate refusal.

It does not claim consciousness, AGI, general agency, human equivalence, unrestricted autonomy, physical deployment, operator-independent custody, or P5 release. Local experiment PASS results are prerequisite signals only. A production label is forbidden until the architecture, custody, containment, schema, held-out, and self-custodied evaluation gates in this document and the parent roadmap pass.

## 2. Landed local baseline

The current local evidence is documented in:

- [`THOUGHT_MANIFOLD_TRAJECTORY_CONTROL_RESULTS.md`](THOUGHT_MANIFOLD_TRAJECTORY_CONTROL_RESULTS.md) — block 348 concept-region trajectory control and discrete deviation/width behavior.
- [`APERTURE_GRAIN_TUBE_RESULTS.md`](APERTURE_GRAIN_TUBE_RESULTS.md) — block 349 qualia/dynamical aperture-grain tube behavior.
- [`GLOBAL_WORKSPACE_RESULTS.md`](GLOBAL_WORKSPACE_RESULTS.md) — block 350 optional broadcast/competition, Argmax, and ignition silence.
- [`GATED_MINTING_RESULTS.md`](GATED_MINTING_RESULTS.md) — block 351 persistence-gated dimension minting and duplicate resistance.
- [`CAPABILITY_T1_T3_RESULTS.md`](CAPABILITY_T1_T3_RESULTS.md), [`CAPABILITY_T2_T4_RESULTS.md`](CAPABILITY_T2_T4_RESULTS.md), and [`CAPABILITY_T5_RESULTS.md`](CAPABILITY_T5_RESULTS.md) — local capability-suite tracks.

The local invariants to preserve are:

- teacher-free held paths at loop time;
- integer/discrete-quanta decisions, with any continuous input snapped at the boundary;
- duplicate-mint refusal;
- persistence before minting;
- honest sub-threshold workspace silence;
- byte-identical default FIFO behavior when no workspace selector is supplied;
- deterministic bounded termination and explicit no-go/impasse behavior.

These are local mechanism properties, not production authorization.

## 3. Current production gap

The thought-manifold code is not currently part of the P5 evaluator contract. There is no production adapter, canonical manifold serializer, task-envelope field, lock commitment, manifest field, durable manifold case store, or HTTP client integration.

The current source also has an architecture gap against `CLAUDE.md`’s native-ownership rule:

- `domains/regulated_train_of_thought.py` contains the trajectory loop, deviation feedback, width changes, frontier selection, and stop decisions in Python.
- `domains/minting_train_of_thought.py` contains the segment loop, residual handling, frontier choice, and minting orchestration in Python.
- `domains/train_of_thought.py` retains the FIFO loop and accepts an optional selector callback.
- `domains/global_workspace.py` performs Python-side scoring and has a Python fallback when native Argmax is unavailable.

The production decision is therefore explicit:

1. migrate state, iteration, width control, frontier selection, workspace competition, recurrence accumulation, and mint admission into native graph/Rust rules; or
2. quarantine these Python paths as non-production research harnesses and build a separate native production implementation.

Relabelling the Python orchestration “graph-native” is not acceptable.

## 4. Versioned capability contract

The production adapter must introduce closed canonical objects. Proposed initial schemas:

### `P5ThoughtManifoldRequestV1`

Binds the task/run to:

- topic and topic digest;
- tube kind: `concept_region` or `aperture_grain`;
- set-point/aperture digest;
- observer and grain configuration digests;
- selector mode: `fifo` or `workspace_argmax`; 
- segment and graph/resource limits;
- runtime, image, closure, policy, and worker-contract digests.

### `P5ThoughtManifoldSegmentV1`

Contains only evaluator-approved public or result-visible fields:

- segment sequence and previous digest;
- admitted-tube digest;
- trajectory digest;
- integer deviation and width quantum;
- workspace candidate/winner digest, if enabled;
- ignition outcome and stop reason;
- recurrence/residual digest;
- bounded resource-use evidence.

Private concepts, held-out labels, truth, teacher answers, and evaluator-only targets remain outside the worker-visible object.

### `P5ThoughtManifoldMintV1`

Binds a proposed minted axis to:

- residual digest and recurrence count;
- persistence threshold and observation window;
- source signature/axis digest;
- duplicate-check digest;
- candidate axis schema and quantum;
- evaluator decision: `proposed`, `accepted`, `rejected`, or `impasse`;
- rollback snapshot and receipt references.

No worker-submitted boolean may claim that a dimension was genuinely new, persistent, or adopted.

Every object requires canonical encoding, a schema version, content digest, producer/authority identity, monotonic sequence, and references rather than duplicated mutable state. Unknown fields, missing required fields, invalid quanta, malformed digests, sequence gaps, and over-budget graph growth fail closed.

## 5. Seed and package contract

The reviewed package must declare and hash the complete dependency closure for:

- `seeds/shape_vocabulary.json`;
- `seeds/qualia_space.json`;
- concept-signature and aperture-grain schemas;
- thought-manifold tube/deviation rules;
- global-workspace candidate, Argmax, and ignition rules;
- recurrence/residual and gated-minting rules;
- native runtime and binary;
- worker/evaluator protocol;
- resource and closure profile.

The package must prove that the selected seed set is sufficient. Missing qualia axes, absent workspace rules, absent shape-decode rules, or fallback Python paths are explicit no-go conditions, not silently disabled features.

A production private case store must be durable and evaluator-held. The in-process `_PRIVATE_STORES` registry and locally generated signer remain test-only. Public manifest, private truth/store, lock, authority, and object names must be content-addressed and cross-checked before task release.

## 6. Architecture and safety gates

Before manifold task execution:

1. The evaluator signs the immutable control-plane manifest.
2. The native runtime owns canonical manifold state, segment sequencing, recurrence state, workspace decisions, mint admission, rollback, and audit hashes.
3. Python is limited to lossless transport/adaptation and cannot choose a winner, change width, decide persistence, mint an axis, or mutate canonical state.
4. The worker receives bounded observations and legal opaque actions only; it receives no GCS, KMS, STS, authority, truth, or evaluator-private capability.
5. Workspace ignition below threshold yields explicit silence; it must not force a thought.
6. A malformed candidate, unknown concept, invalid residual, duplicate mint, cycle, resource exhaustion, stale sequence, or failed receipt yields no durable mutation.
7. External kill/liveness supervision covers the native runtime, worker, broker, receipt writer, and timing path.
8. Rollback restores the exact pre-mint/pre-segment graph and produces a signed receipt.
9. No network, host filesystem, package installation, ambient credentials, or unrestricted command/tool path is reachable from the evaluation build.
10. The same worker/evaluator seam is used for primary tasks and controls; control-only shortcuts are forbidden.

## 7. Evidence ladder

Evidence is accumulated in four stages:

### Stage A — native unit and migration tests

Test schema validation, canonical digests, quanta, tube projection, workspace Argmax, ignition silence, recurrence, duplicate refusal, persistence, rollback, malformed inputs, and deterministic termination. Require the default FIFO path to remain byte-identical when explicitly declared.

### Stage B — clean-checkout local replay

Run the complete package from a clean checkout with pinned seed/code/native/runtime hashes. Reproduce local T1–T5 and blocks 348–351 in two independent runs. Record all skips, failures, resource use, and negative controls. This remains local evidence.

### Stage C — self-custodied bounded capability run

The project-controlled evaluator role supplies held-out cases, private truth, signed lock, native closure, external supervisor, receipt authority, and write-only result custody. These are technically separated project components, not independent evaluator custody. The manifold digest and selected mode are locked before task unsealing. Primary, control, mechanics, duplicate, persistence, and negative-transfer cases run through the same production seam.

### Stage D — parent-roadmap gate

Only after upstream P0–P4 trusted gates pass may this capability contribute to P5-E1/E2. P5 thresholds, unseen-domain coverage, 10,000 red-team episodes, scaling, graceful degradation, and no-adoption requirements remain those of the parent roadmap; this plan does not relax them.

## 8. Rollout

1. **Quarantine and inventory:** classify current Python paths as research-only; freeze the landed local outputs and seed hashes.
2. **Native contract:** implement the versioned request/segment/mint schemas and native state machine without changing the local result documents.
3. **Native selector:** move workspace scoring, Argmax, ignition, and selector state into native rules; retain FIFO only as an explicit compatibility mode.
4. **Native persistence/mint:** move residual recurrence, persistence windows, duplicate checking, and rollback into the native graph/runtime.
5. **Local adapter replay:** run Stage A/B with malformed, adversarial, reset, restart, and resource-exhaustion controls.
6. **Evaluator packaging:** produce the signed manifest, closure, private bundle, lock, task release, receipts, timing, and external kill evidence.
7. **P5 integration decision:** only after upstream custody/containment gates pass, map manifold objects into P5 task/result schemas through an explicit adapter and preregistration.
8. **Normal production client:** configure a real OIDC audience/subject and an authorized client before any non-smoke task. Diagnostic placeholders such as `aud` and `runner` are never production credentials.

## 9. Stop rules and open risks

Stop and record no-go if any condition holds:

- Python still owns a production decision or canonical manifold state;
- workspace selection silently falls back to Python or FIFO when workspace mode is locked;
- a residual can mint without persistence or duplicate refusal;
- private truth or authority material reaches the worker;
- a result omits a segment, recurrence, control, rollback, or receipt record;
- timing, KMS, GCS, or authority verification is absent;
- graph/state/resource growth exceeds the locked budget;
- restart changes the result without a declared new run identity;
- the native/runtime/image/closure digest changes after preregistration;
- observer grain changes the result outside its locked semantics;
- a missing optional seed is silently treated as a passing capability;
- a local result is described as P5 trusted release or general agency.

Open risks include observer/grain sensitivity, qualia-axis dependence, resource growth under persistent residuals, semantic drift between concept-region and aperture-grain tubes, workspace competition under sparse salience, and the gap between the local Python harness and native ownership.

## 10. Current decision

The thought-manifold capability is **landed local research evidence** and **not production-integrated**. The current P5 software attestation/timing substrate is separately verified at smoke level, and the normal service boots, but no authorized normal evaluator task has been submitted. This plan remains in planning status until the native architecture gate, versioned adapter, evaluator custody, and parent-roadmap prerequisites are satisfied.
