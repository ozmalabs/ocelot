# ProblemShape minimal checkpoint hardening preregistration

**Status:** isolated format and recovery probe; no production/default persistence change.

## Question

Can the prepared-goal ProblemShape continuation bundle be versioned and rejected fail-closed when required structure is absent or inconsistent, and can its writer replace a prior bundle atomically under an injected pre-replacement failure?

## Contract

Schema version 1 names the exact `prepared_goal_problem_shape_continuation_v1` contract. Validation occurs before native graph/rule import. It requires the agent epoch, unique prepared goals, valid typed nodes and edges, observation-to-goal/index links, exact index support counts, recognized status/event agreement, minted-shape attrs, the eight required Γ production triples, and exactly the five ProblemShape rules. Unknown root fields, node/edge types, or rule edge types are rejected. Truncated JSON must fail parsing.

The write probe writes and fsyncs a same-directory temporary file, then uses `os.replace` and fsyncs the parent directory. An injected exception after temporary-file fsync and before replacement must preserve the old target and remove the temporary file. A successful replacement must yield a bundle accepted by the reader.

## Procedure and gate

Run the existing N=8 full-adapter control, compact writer, and compact reader as separate processes. Before reader continuation, mutate one valid serialized bundle in each of eight ways (unsupported schema version, missing rule, missing production, dangling edge, incorrect index count, missing residual event, status/event mismatch, missing index link) and separately truncate the JSON. Every mutation must be rejected. Then run the injected write failure and a successful replacement; require prior-target preservation, temp cleanup, and valid replacement. The original exact-continuation parity gates remain in force.

## Limits

This is a local format-level probe, not proof against arbitrary hostile input, concurrent writers, process kill at every instruction, power loss, filesystem bugs, migration between schema versions, or general solver/WorldAdapter recovery. The injected failure is deliberately placed before `os.replace`; it does not establish crash consistency after replacement or across storage hardware. The JSON Schema file documents the envelope; runtime cross-field validation is performed by the runner and is authoritative for this probe.
