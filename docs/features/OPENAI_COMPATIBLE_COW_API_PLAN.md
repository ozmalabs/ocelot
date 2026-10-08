# OpenAI-Compatible API with CoW User Namespaces — Plan

## Execution status (2026-10-07)

Implemented in this branch: the daemon/interface audit and ADR; a separate
bearer-authenticated standard-library HTTP service (`scripts/ocelot_api.py`),
whole-`WorldAdapter` CoW branch helper, per-principal sessions with fork/clear
operations, shared and separately seeded baseline modes, and owner-only
checkpoint plus Python-runtime sidecar persistence. Focused tests exercise
branch isolation, actual-turn cross-user noninterference, ownership checks,
clear/fork behavior, active lifecycle state and timestamps, persistence recovery,
same-session turn/fork/clear races, exclusive user-wide clear, and the HTTP
response contract. A
subprocess acceptance test also starts the documented CLI, chats, restarts with
the same state directory, and continues the recovered session.

Still open before production readiness: `conversation_only` isolation;
streaming/tool/multimodal support; and remote deployment hardening. Checkpoint
revisions are committed through an atomic metadata pointer, directory-synced,
and verified by digest on recovery; orphaned revisions are collected after
recovery selects a committed revision. Session metadata is bound to a digest of
its starting baseline, so changed seed/rule state fails closed on recovery
instead of silently changing reset behavior. The digest covers the graph,
grammar, rules, and serializable adapter runtime state. Failed turns and failed
clear commits restore the prior in-memory state. Metadata v1 and v2 are migrated
to v3 with staged checkpoints and an atomic pointer update. The official OpenAI SDK is
exercised by an optional interoperability test. The API is text-only,
non-streaming, and stateful. The native snapshot rejects ineligible adapter
states; the wrapper also refuses attached storage/vision resources and active
teacher threads.

## Goal

Expose Ocelot to external services through an OpenAI-compatible chat API while
preserving per-user state isolation. Each authenticated user receives a
copy-on-write (CoW) namespace. The default namespace contains the **whole
`WorldAdapter` state**, branched from a shared baseline; conversation-only
isolation is an opt-in mode. Users can clear or fork sessions through an
Ocelot-specific session-management API.

This document tracks the design and implementation. The network interface
audit is in [`NETWORK_INTERFACE_AUDIT.md`](NETWORK_INTERFACE_AUDIT.md). The separate API and
whole-adapter per-user CoW session service are implemented as described in
[`OPENAI_COMPATIBLE_COW_API.md`](OPENAI_COMPATIBLE_COW_API.md). The existing
daemon HTTP API and Unix socket remain local control interfaces. The accepted
fork-boundary decision and current conversation-only limitation are recorded
in [`ADR-ocelot-api-cow-isolation.md`](../architecture/ADR-ocelot-api-cow-isolation.md).

## Defaults and contract decisions

1. **Baseline:** share one immutable, seeded baseline. Each user gets a private
   writable branch. Writes from one user must never appear in another user's
   branch.
2. **Isolation boundary:** `whole_adapter` is the default. Fork and clear
   operate on all branch-local `WorldAdapter` state, including graph state,
   conversation/discourse state, and persisted metadata needed to resume it.
   `conversation_only` is an explicit opt-in for deployments that intend users
   to share learned agent state.
3. **Optional isolated baseline:** deployments may select a separately
   provisioned baseline per user when seed data or operational policy requires
   it. Keep baseline mode distinct from isolation-boundary mode in config and
   API metadata.
4. **Fork:** create a new session from a consistent point-in-time snapshot of
   a source session. Parent and child share unchanged CoW storage and diverge on
   write. The operation must be atomic from the caller's perspective.
5. **Clear:** default to resetting the selected session to its user's configured
   baseline. A separate explicit operation may reset all of that user's
   sessions/state. Never interpret a missing or ambiguous session ID as a
   request to clear the entire user namespace.
6. **Identity:** derive the namespace from an authenticated principal, never
   from a caller-supplied user ID alone. `user` and `session_id` fields in
   requests cannot override the authenticated mapping.
7. **OpenAI compatibility:** start with non-streaming
   `POST /v1/chat/completions`, a stable advertised model ID, standard
   `messages`, and OpenAI-shaped success/error payloads. Streaming is a later
   phase unless the turn lifecycle can be mapped without ambiguous completion
   or cancellation semantics.

## Phase 0 — Repository and runtime audit

- Document the current daemon API, HTTP and Unix-socket boundaries, turn
  submission/completion behavior, SSE event format, persistence/checkpoint
  layout, and authentication status.
- Trace the full `WorldAdapter` object graph and identify all mutable state
  reachable outside the CoW `TypedGraph` (Python dictionaries, caches,
  executors, handles, locks, pending effects, external resources).
- Trace existing graph CoW operations and `fork_experiment` constraints. Verify
  whether a whole adapter snapshot can safely share graph pages while giving
  each branch independent mutation and runtime state.
- Record file-format/version compatibility and a baseline creation strategy.
- Deliverable: short architecture decision record (ADR) with confirmed fork
  boundary, snapshot consistency mechanism, and any state that must be copied
  eagerly or reinitialized.

**Gate:** do not implement whole-adapter branching by cloning only the graph.
If adapter state cannot be safely forked yet, identify and close that gap before
advertising whole-adapter CoW.

## Phase 1 — Namespace and session model

- Define durable records for users/namespaces, baseline version, session ID,
  parent session, snapshot/checkpoint reference, isolation mode, timestamps,
  and lifecycle state.
- Implement an authenticated-principal-to-namespace resolver and a storage
  layout that prevents path traversal and cross-user snapshot lookup.
- Define concurrency controls for same-session writes, fork-versus-write,
  clear-versus-write, and daemon restart recovery. Use per-session serialization
  or revision/precondition checks rather than a process-wide lock for all users.
- Define retention/deletion semantics and failure recovery for partially
  persisted forks or clears.
- Add an internal namespace manager API, independent of HTTP, so lifecycle
  semantics can be exercised directly.

## Phase 2 — CoW adapter lifecycle

- Implement creation of a user namespace from the shared baseline and lazy
  branch creation for sessions.
- Implement whole-adapter fork/snapshot semantics. The graph may share CoW
  pages; non-graph mutable fields must be safely copied or re-bound, and
  in-flight effects must either be drained or make the fork fail clearly.
- Implement `conversation_only` as a distinct mode with explicit shared-state
  policy. Do not silently fall back from whole-adapter to conversation-only.
- Implement `clear_session` and `clear_user` (or equivalent internal names):
  clear a session to baseline, or reset the entire user namespace only when
  explicitly requested.
- Persist branch metadata and snapshots durably; recover an interrupted
  operation deterministically on startup.
- Expose fork provenance and baseline/session revision in internal results for
  audit and debugging.

## Phase 3 — OpenAI-compatible and Ocelot management APIs

- Add `POST /v1/chat/completions` backed by the authenticated user's active
  session. Translate roles and message content into the Ocelot conversation
  input; map completed turns, usage availability, model ID, timestamps, and
  errors into the documented response shape.
- Add `GET /v1/models` (or document one fixed model without listing if client
  compatibility permits).
- Add Ocelot-specific management routes, for example:
  - `POST /v1/ocelot/sessions` — create a session.
  - `POST /v1/ocelot/sessions/{id}/fork` — fork a session.
  - `DELETE /v1/ocelot/sessions/{id}` — clear/reset a session, with explicit
    reset semantics in the response.
  - `GET /v1/ocelot/sessions` and `GET /v1/ocelot/sessions/{id}` — list and
    inspect only sessions owned by the authenticated principal.
- Keep broad daemon administration, raw graph/debug routes, extension approval,
  and process controls outside the OpenAI-facing listener unless separately
  authorized and protected.
- Configure bind address explicitly. Keep loopback as the development default;
  require authentication for any non-loopback listener. Document TLS/reverse
  proxy expectations for network deployment, request limits, timeouts, and
  rate/concurrency limits.
- Add streaming only after defining turn completion, disconnect cancellation,
  event framing, and namespace-lock lifetime. Match OpenAI SSE framing and
  terminal `[DONE]` behavior if implemented.

## Phase 4 — Documentation and operator workflow

Create/update documentation for:

- Local startup, endpoint list, bind configuration, authentication setup, and
  minimal OpenAI SDK/curl examples.
- Namespace defaults: shared immutable baseline, private user branch, whole
  adapter isolation, and the conversation-only/isolated-baseline options.
- Session create/fork/clear semantics, including what “clear” does and does
  not erase, parent-child lineage, and recovery behavior.
- Storage footprint and CoW growth/compaction/retention controls.
- Security boundary and deployment guidance, including that the existing daemon
  loopback API is not itself an authenticated remote service.
- Compatibility matrix: supported OpenAI request fields and unsupported or
  ignored fields, streaming status, tool calls, multimodal input, and usage
  accounting.

## Phase 5 — Verification and release gates

### Unit and property tests

- CoW graph branch mutation isolation: parent and sibling retain their own
  values; read-only pages are shared until mutation where measurable.
- Whole-adapter branch completeness: mutate each relevant state category in one
  branch and confirm no mutation reaches parent/sibling.
- Conversation-only mode: prove its documented shared/private state boundary.
- Clear semantics: selected-session reset returns to baseline; unrelated
  sessions remain unchanged; user-wide reset is explicit and complete.
- Fork semantics: snapshot consistency, branch lineage, unique IDs, nested
  forks, and defined rejection/handling of in-flight effects.
- Serialization, restart recovery, version mismatch, interrupted persistence,
  and concurrent lifecycle operations.

### API and interoperability tests

- OpenAI-shaped request/response, role handling, empty/invalid messages,
  malformed JSON, model selection, timeouts, turn failures, and error mapping.
- Exercise the official OpenAI Python client against the local endpoint using a
  test transport/key; verify standard `base_url` integration.
- Verify authenticated user A cannot list, read, fork, clear, or infer user B's
  namespace/session IDs or content.
- Verify unauthorized access, unsupported methods/fields, payload-size limits,
  and loopback/non-loopback configuration behavior.
- If streaming is added: event ordering, chunk encoding, final chunk, `[DONE]`,
  disconnect behavior, cancellation, and concurrent clients.

### End-to-end acceptance

1. Two users start from the same shared baseline and see the same baseline
   content.
2. User A learns/mutates state; User B and the shared baseline remain unchanged.
3. User A forks; parent and child initially match, then diverge independently.
4. Clearing the child restores that child to baseline while preserving the
   parent; clearing the full user namespace requires an explicit operation.
5. Restart the daemon and confirm all sessions, branches, ownership mappings,
   and lineage recover correctly.
6. An OpenAI SDK client sends a chat request using `base_url`; its reply is
   produced through the intended Ocelot session.

## Suggested delivery sequence

1. Phase 0 ADR and small prototype proving whole-`WorldAdapter` CoW safety.
2. Phase 1 namespace manager plus Phase 2 lifecycle internals and focused tests.
3. Phase 3 non-streaming local API and OpenAI SDK interoperability.
4. Phase 4 user/operator documentation and Phase 5 end-to-end/security gates.
5. Streaming and remote deployment hardening as separately gated follow-up
   work.

Do not claim the feature ready until the whole-adapter isolation and cross-user
noninterference acceptance checks pass. The graph-level CoW primitives alone
are insufficient evidence.
