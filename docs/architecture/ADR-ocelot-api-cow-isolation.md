# ADR: Authenticated API with whole-adapter CoW sessions

- **Status:** Accepted for the initial API implementation
- **Date:** 2026-10-07
- **Decision owners:** Ocelot maintainers

## Context

Ocelot's existing daemon interfaces are intended for local control. The daemon
HTTP interface is loopback-bound and includes operational/debug capabilities;
the Unix socket is local IPC. Neither is an authenticated, session-scoped
remote OpenAI API. Exposing those listeners directly would mix user chat with
administrative operations.

The substrate supports native graph snapshots and forks
(`runners/dsl/python/substrate_rs/__init__.py`, `Substrate.snapshot` and
`SubstrateSnapshot.fork`). These are CoW graph branches with eligibility
constraints. They do not clone a `WorldAdapter`: the adapter also owns Python
indexes and runtime fields. Conversation turn recording uses adapter-level
`_last_message` and `_last_turn_inbound` references, and conversation helpers
use graph-derived caches such as `_discourse_store`. A graph-only fork could
therefore have correct graph pages but stale or shared host state.

Conversation state is currently embedded in the same graph as learned and
cognitive state. In particular, conversation turns append `Message` nodes and
links to one `Channel`, update `ConversationContext`/discourse state, and can
also cause broader learning writes. The adapter's turn spine is global to the
adapter. There is no established ownership tag or write boundary that can
selectively fork only conversation state while safely sharing all other
mutable state.

## Decision

1. Run the OpenAI-compatible listener as a separate process/service. It uses
   bearer-token authentication mapped to a server-side principal and exposes
   only chat, model, and Ocelot session-management routes. Keep loopback as the
   default bind. Remote deployments must terminate TLS at a trusted proxy or
   equivalent and protect the listener.
2. Give each authenticated principal a private namespace. The default baseline
   is one pinned, immutable seeded adapter that namespaces branch from using
   native graph CoW. An optional isolated-baseline mode provisions a separate
   baseline per principal. Baseline mode and isolation mode are separate
   settings.
3. Support `whole_adapter` isolation only. Fork captures a graph snapshot and
   deep-copies adapter-owned Python state under the conversation lock, keeps
   native `NodeID`s stable, and resets graph-derived caches so they rebuild
   against the child branch. Active teacher workers, storage mmap, attached
   vision/eye resources, and any uncopyable state fail closed.
4. Persist each session's graph and adapter-runtime sidecar as numbered
   revisions. Commit by atomically replacing a per-user metadata pointer after
   writing and syncing both files. Record hashes for the revision files and
   baseline; recovery verifies them and rejects mismatched baselines. Principal
   names are hashed for directory names, directories are owner-only, and
   request data never selects a principal or filesystem path. Baseline identity
   includes graph, grammar, rules, and serializable adapter runtime state.
5. Provide explicit session create/list/inspect/fork/clear routes. Clearing a
   session resets it to its user's pinned baseline. Clearing the namespace is
   a separate explicit operation. Fork preserves parent lineage and begins at
   a consistent session revision.
6. Keep `conversation_only` as a future opt-in. Do not approximate it by
   copying selected message nodes: graph rules, context/discourse writes,
   shared-channel links, global turn references, and learning side effects
   make that boundary incomplete. The current API rejects this setting rather
   than silently weakening isolation. Supporting it requires an explicit
   conversation-state ownership model and tests that prove shared/private
   writes against the full turn pipeline.

## Consequences

- Whole-adapter sessions have the clearest isolation semantics and are the
  default, at the cost of more branch-local state and disk growth.
- The first API is stateful and supports non-streaming text chat. It does not
  provide tool calls, multimodal content, or tokenizer-accurate usage counts.
- CoW is a graph-storage optimization, not a guarantee that every adapter
  operation is eligible. Unsupported attached resources or runtime values
  prevent fork/recovery and must produce explicit errors.
- The current service should be treated as a single-process API deployment.
  Multi-process coordination and operational rate limiting remain deployment
  work before a horizontally scaled public service.

## Verification

Focused tests cover graph and Python-state branch isolation, cache rebinding,
fail-closed fork eligibility, per-principal ownership, nested fork and clear
semantics, checkpoint restart recovery and tampering, concurrent independent
sessions, HTTP response shape, and an optional real OpenAI SDK request.
