# Cognition process execution contract

Status: Phase 6.01 semantic freeze. This records the current implementation and the conformance requirements for Phases 6–10. It does not claim that the unfinished adapters or benchmark arms already exist.

## Process view contract

`ProcessSchema` is a non-authoritative view. A native source remains the owner of its representation and behavior. The schema is linked to its agent through `has_process_schema`; `realised_by` stores a node-valued source identity because current rule effects cannot create an edge to a computed node value. Never infer source identity from a display name or process fingerprint.

| Native source | Current schema view | Preconditions / effects | Current evaluation | Required provenance and freshness |
|---|---|---|---|---|
| `DimensionGenerator` | `kind=generator_step`; `params=["gen", kind, coord_dims, modulus, matrix, offset, 1]`; domain currently `shape_coords_2d` | Source parameters constrain the generator; the view currently writes `pre=None`, `post=None` | `ProcessApply` delegates to `shape_decode::apply_generator_k_with_coefficients`; unsupported/malformed inputs return `None`. `ProcessInverse` has a narrower explicit kind list and may return `None` for an applicable generator such as `scale2`. `EffectFingerprint` is output on the finite probe list. It is probe-relative; two shape probes are not a completeness proof. P6 conformance tests must compare each supported kind with the native decode path. | Preserve source node ID, owning agent, generator/codebook epoch, domain/probe version, and supported kind/parameter digest. Current view does not refresh when its source mutates. |
| `Program` | `kind=program`; `params=None`; construction metadata copied; `pre=None`, `post=None` | Native program guards/contracts are not projected to the view today | Opaque. `process_algebra` does not invoke `ProgEval`; a `None` fingerprint means unavailable, never identity. A future evaluator must use bounded, side-effect-free execution with the same declared input and external-call contract as the native evaluator. | Preserve source node ID, owner, program/version digest, allowed external capabilities, and input-frame identity. A program edit invalidates prior view/evidence. |
| `CapabilityProgram` | `kind=capability`; `params=None`; `order` copied; `pre=None`, `post=None` | Capability boundary and requested capability are not projected today | Opaque. No capability dispatch in `process_algebra`. | Preserve source node ID, owner, capability/order version, and any authorization/profile boundary. A view never authorizes a capability invocation. |
| `TransitionHypothesis` | `kind=transition`; `params=None`; source/action/successor state kinds copied; `pre=None`, `post=None` | Hypothesis conditions/effects are not projected today | Opaque in process algebra. Do not treat a predicted transition or a `CognitionManifold` prediction as an observed transition receipt. A future adapter must call only the finite model evaluator that owns the hypothesis and report model prediction separately from observed world result. | Preserve source node ID, owner, hypothesis/model epoch, source-state/action identity, and evidence epoch. Model change invalidates its projection. |
| `EmbodiedMotorProgram` | `kind=motor`; `params=None`; `pre=None`, `post=None` | Body/world preconditions and actuator authorization are not projected today | Opaque. No motor execution is available through `ProcessApply`. Detached evaluation must never emit motor commands or be reported as a real trial. | Preserve source node ID, owner, body schema, motor/model version, world epoch, and authorization identity. Only the existing guarded native action boundary can emit. |
| `FamilyProgram` | `kind=family_program`; `params=None`; `pre=None`, `post=None` | Cue, parent family, and eligibility conditions are not projected today | Opaque. Do not execute an authorship family by reading a schema view. | Preserve source node ID, owner, family/program version, parent, and probation/judgment epoch. A retired or changed family invalidates the view. |

The current generator emits `pre=None` and `post=None` for all six view forms. `None` here means that the view has no projected predicate; it is not an always-true precondition, an identity effect, or proof that the native source has no guards. Future adapters may fill these fields only from source-owned semantics and must preserve the native three-valued/unknown behavior. Missing preconditions stay unknown; missing effects stay opaque.

All six view kinds currently lack explicit source-epoch refresh and stale-view retirement. Phase 6 implementation must add source/model/domain epoch binding before a view is eligible for evaluation, fingerprint comparison, or adoption. Ownership is per agent and per domain; cross-owner or cross-domain equality is not a merge condition.

## Effect, fingerprint, and deduplication semantics

The current Rust algebra parses finite permutations, integer matrices, integer deltas, shape-decode generator steps, and sequences. It implements composition, supported inverses, application, support for permutations/matrices/deltas, and effect fingerprints as outputs on every supplied probe. Parse failure, failed application, unsupported source kinds, invalid dimensions, overflow, or a non-invertible process return `Value::None` where the operation cannot be established. `None` must remain distinguishable from the empty sequence, identity, zero support, and an empty observed effect.

The fingerprint is a finite observation, not a universal process identity. Two schemas may be deduplicated as exactly equivalent only when their representation declares a complete separating test and both were evaluated under the same owner, domain, source/model epoch, input frame, and probe version. Current exactness metadata is conservative: a permutation domain containing the identity permutation probe separates every valid permutation of that size. A finite set of ordinary shape probes, examples for a program, observed transition states, or motor trials establishes agreement on those probes only. A hash or equal output vector does not repair an incomplete probe set. Until completeness is proven, preserve both candidates and seek a distinguishing probe; do not merge the more expensive one merely because its current fingerprint matches.

Where exact equivalence is established, keep the lowest declared primitive cost. Equal-cost ties use a stable source identity ordering. Provenance and source lineage remain inspectable after a merge. Approximate agreement may rank candidates for further testing but cannot retire a candidate, establish an inverse, or become an adoption proof. In particular, opaque `None` values are excluded from equality, deduplication, identity tests, laws, and support thresholds.

## Resource, operation, and receipt identity

Every process evaluation or experimental action must be funded before it executes. The future request/receipt contract binds at least: operation kind, source node and source epoch, owner/domain, probe or input-frame version, requested work bound, budget node and debit ID. One request has at most one debit and exactly one terminal outcome (`completed`, `denied`, `expired`, `interrupted`, or `failed`); retrying after interruption requires an explicit new request identity. Budget exhaustion or missing source evidence returns an honest status and performs no partial adoption or external action.

Probe count, probe size, program steps, model candidates, graph growth, detached memory, and wall-clock/tick limits are separately bounded. A host tick limit does not count as a ThinkingBudget debit. Refinement that obtains observations is a world action: its request is distinct from the predicted result, and only a source-bound world receipt can establish what happened. This Phase 6.01 contract freezes the requirement; the current process-schema fingerprint rules do not yet meter their work, so they cannot be treated as funded process execution.

## PMB comparison arms and records

Baseline and Track I arms use the same generated world instances, affordances, initial evidence, evaluator, and limits. Each agent has isolated graph state and an identical budget allocation/ledger policy; one arm cannot spend or observe the other's state. The baseline profile omits Track I seeds and policies. The invention arm opts into named Track I seeds/policies. The current `evaluation.process_mastery.harness.Agent` always adds Track I seeds and enables Track I policies; it is not a baseline constructor and cannot be used to report a Track-I-disabled score.

World installation is mechanical I/O, never strategy. The agent may receive declared affordances and observations, not the hidden target, evaluator answer, future outcome, solver trace, answer-conditioned hint, or a source process created from a benchmark solution. The scorer alone holds hidden truth and checks actual emitted behavior. If a family has no functioning adapter, record `NOT_RUN` or `UNSUPPORTED`, not zero, failure, or parity. Timeout, invalid output, missing evidence, and evaluator failure have distinct statuses.

Every raw trial records phase/family/version, split and concrete seed, world and hidden-truth digest (scorer-side only), profile and resolved seed closure, engine build/source fingerprint, agent policy and budget allocation, source/model/probe epochs, ticks/native steps, graph and detached-buffer growth, chosen process IDs and lineage, request/debit/receipt IDs, actual observed outcomes, and terminal status. Aggregates retain paired rows, missingness, exclusions and uncertainty intervals. Held-out allocation is frozen before evaluation; only development seeds may be used for debugging. A corrected evaluator or invalid comparator gets a new protocol version and untouched split.

The original PMB v1 seed ranges remain `0..9999` for development and `1000000..1009999` for held-out instances. The linear phase plan reserves separate phase/family/control blocks for later protocols; record the concrete allocation and prove disjointness before each preregistration freeze. A human comparison remains unavailable until its task, population, instructions, affordances, stopping rule and scoring protocol match the agent arm and are cited.

## Phase 6 acceptance contract

The implementation tasks after this spec must establish, without changing the frozen semantics:

- six native sources retain their source identity, owner, supported fields, and truthful unknown/opaque state;
- evaluator outputs match the owning native evaluator on declared supported inputs, and unsupported inputs fail closed with no mutation;
- stale source/model/probe epochs invalidate prior views and evidence;
- exact complete probes can deduplicate equal effects while incomplete probes retain colliding candidates;
- baseline boot contains no Track I seeds or enabled Track I policies; paired arms have isolated state and identical limits;
- raw scorecards distinguish unsupported, not-run, timeout, failure, and measured outcome and preserve the scorer/agent evidence boundary.

These are mechanism/conformance criteria. Passing them does not establish a human-level PMB capability or close any L1–L7 claim.
