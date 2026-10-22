# Native execution and evidence contract

Status: Phase 16.01 specification freeze (2026-10-22). This contract defines what a future scored native execution may claim. It does not retroactively upgrade P15 or establish that the mechanisms described here are already implemented.

## Ownership and execution boundary

The agent owns candidate selection and expression evaluation. A graph rule must select an eligible, current process owned by the active agent, resolve its source-bound expression, and evaluate that expression under a declared native evaluator and work bound. The harness may install a world, expose its declared observations and affordances, enforce the evaluator boundary, and score emitted actions against hidden truth. It may not select a process by arm, build an arm-specific process, compute the intended outcome, or substitute a host-computed equivalent.

The native decision path is: world observation and affordance → graph-selected process/source → native expression evaluation → funded and authorized proposal → external world transition → independently observed receipt. A prediction is not an action, an action proposal is not an executed action, and a model-predicted result is not an observed receipt. Missing or stale source, unsupported syntax, exhausted work, or denied authorization must abstain without changing the world.

An expression is eligible only when its source identity, owner, source epoch, expression digest, domain/input-frame identity, policy/profile, and authorization context match the current request. Mutation or deletion invalidates the active expression before the next scored execution. The selected source identity and digest, evaluator version, traversed nodes, composition/application counts, work debit, authorization, proposal, world action, and receipt are recorded per trial.

## Support and comparator contract

| Form or adapter | Phase 16 disposition | Evidence permitted |
|---|---|---|
| Finite permutation, integer matrix/delta, and supported sequence composition | Supported only on explicitly declared bounded native operations | Exact result for the declared input; no general equivalence claim without a complete separating domain |
| Versioned reflected `Program` expression | Detached, fuel-bounded evaluation only where the native evaluator accepts its IR and no oracle/capability binding is used | Prediction only unless passed through the separate proposal, authorization, world, and receipt boundary |
| `DimensionGenerator` | Supported generator kinds only, compared with owning shape decoder | Exact finite transition for declared kind/input |
| `TransitionHypothesis` | Unsupported as a general process action; finite model predictions may be reported separately | Prediction only; never an observed transition |
| `CapabilityProgram`, `EmbodiedMotorProgram`, `FamilyProgram` | Opaque/unsupported for detached process execution | No action, effect, identity, or capability claim |
| Loopover and finite sliding-puzzle worlds | Supported only with primitive actions, state-dependent legality, and independent transition receipts | Executed path and observed state transition |
| Finite state-dependent tool worlds | Supported only for explicitly installed legal tools and a scorer-owned transition function | Executed tool action and observed receipt |
| Physical, broad capability, and unimplemented perceptual views | Unsupported | `UNSUPPORTED`/`NOT_RUN`, never zero skill or parity |

Baseline search, learned process, and any other comparator receive the same goal, primitive action set, legality queries, initial observations, transition protocol, limits, and per-agent funding. The primitive-search arm must actually search an explicit frontier under a declared expansion budget. A learned arm must execute its graph-selected expression. A hand-written greedy policy remains a named comparator and cannot stand in for primitive search. Failed search is a measured failure; a missing adapter is `UNSUPPORTED` and blocks the comparison.

## Causal and integrity controls

Every evaluation includes controls for absent, stale, and tampered expressions; wrapper/native mismatch; unauthorized emission; and mutation/deletion of the currently selected operator. A causal control changes or removes the graph-owned expression before a new trial and checks that the next decision changes accordingly or abstains. A fixture that merely checks metadata while executing a host-selected process does not pass.

The runtime attestation records distinct SHA-256 values for the wrapper, the exact loaded extension path and bytes, engine source closure, build receipt, resolved profile/seed closure, evaluator and world adapter source, and frozen allocation. The extension hash is computed from the module actually loaded by the process and bound to imported native symbols. Missing build metadata or inability to establish symbol-to-module identity yields `UNKNOWN`; dirty or mismatched artifacts are development-only and cannot freeze a new allocation. A commit ID or later rebuild cannot reconstruct the runtime bytes of an earlier evaluation.

Every request is funded before evaluation or external action. Receipts bind request ID, source ID/epoch/digest, owner, world and input epoch, action, debit, authorization, and terminal result. Count expression visits, compositions, applications, failed proposals, search expansions, world actions, graph growth, memory where available, ticks, and wall time. A host timeout is not a native budget debit. Each request has one terminal outcome; retry requires a new request identity.

## Freeze boundary and non-goals

This is specification-only. It does not rebuild the engine, patch P15, change historical hashes, grant candidate-specific approval, claim support for opaque process forms, or authorize a held-out allocation. P16.02–P16.E3 must implement and validate the contract on new artifacts and a fresh allocation. P15's recorded outcomes and provenance limitations remain unchanged.
