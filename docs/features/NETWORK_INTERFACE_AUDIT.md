# Ocelot network interface audit

**Reviewed:** 2026-10-07

## Existing daemon interfaces

The daemon has two local interfaces. They serve the companion UI and local
automation; they do not provide authenticated multi-user namespaces.

| Interface | Current behavior | Boundary |
| --- | --- | --- |
| HTTP | `scripts/jabberwock_daemon.py` starts `JbwHTTPServer` on `127.0.0.1:8787` by default. `--http-port` changes the port, while `serve_http` still binds loopback. | No bearer authentication or principal mapping. It exposes the web UI, chat submission/history/turn polling, SSE events, graph/debug reads, ingestion, proposals, and administrative controls. It is not suitable as an Internet-facing API. |
| Unix socket | `--socket` defaults to `~/.jabberwock/jbw.sock`; `serve_socket` binds `AF_UNIX` and dispatches local commands. | Local IPC. Access depends on filesystem permissions and deployment environment; there is no application principal/session namespace. |

Daemon chat uses a pending-turn contract: `POST /api/chat` queues work and
returns a turn ID; clients poll `/api/chat/turns/{id}` for terminal graph
evidence. `GET /api/events` streams server-sent events. This differs from the
synchronous OpenAI chat completion contract and is why the new API runs as a
separate process rather than exposing daemon routes through another listener.

The daemon checkpoint loop writes full `WorldAdapter` saves using a temporary
file and atomic rename, then rotates old checkpoints. A daemon checkpoint is a
single-agent recovery artifact; it is not a per-user session store. The new API
has its own state directory and revision metadata.

## CoW and adapter boundary

Native `Substrate.snapshot().fork()` provides graph-level CoW snapshots. It
does not copy Python fields on `WorldAdapter`. Adapter fields include mutable
indexes and conversation-turn references; `_discourse_store` holds a direct
substrate reference. `domains.world_adapter_cow.fork_world_adapter` therefore
captures the graph under the adapter lock, deep-copies branch-local Python
state while preserving `NodeID` identity, and clears that graph-derived cache.
Attached worker/storage/vision resources and snapshot-ineligible states fail
closed.

The live default adapter inventory was inspected directly. Its Python-side
state falls into these categories:

- graph indexes and world mappings (`_concepts`, `_instances`, `_body_types`,
  relation/type/triple indexes);
- turn and event state (`_event_clock`, `_n_events`, `_activity`, action and
  locus counters, and lazily created `_last_message`/`_last_turn_inbound`);
- policy, learning, and theorem caches (for example `_policy_lits`, `_seen`,
  `_taught_lookup`, `_theorem_candidate_holds`);
- vision projection buffers and optional eye/vision handles;
- locks and teacher-worker references.

Plain Python indexes, counters, tuples, and graph `NodeID` references are
copied per branch. The discourse store is discarded and lazily rebuilt. Locks
are rebound to the fork's native substrate. Vision/eye handles, mmap storage,
and active teacher workers are rejected because their lifetime and mutation
are not represented by graph CoW. Dynamic adapter fields are included in the
same copy/checkpoint path; a field that cannot be copied or encoded blocks the
operation explicitly.

The supported isolation contract is whole-adapter: each user and session gets
a private branch, and session clear returns to the user's pinned baseline.
Shared-baseline mode is the default; isolated mode provisions a separately
seeded baseline adapter per user. `conversation_only` remains unavailable:
turns append to shared graph structures and may update learned state, with no
complete ownership boundary that can split those writes. The API rejects this
mode explicitly.

To separate eager seed loading from turn-time writes, a probe started with the
validated API conversation profile (2,105 graph nodes), forked it, and ran
`converse("Hello, my name is Alice.")`. The turn added 165 nodes and 165 edges:
among them 4 `Message` nodes, 5 `Mention` nodes, a `ConversationContext`,
`Channel`, `DiscourseState`, `CommonGround`, and `DiscourseEvent`, but also 58
`Concept` nodes, three `Microtheory` nodes including `learned_lexicon`, seven
`Rule` nodes, and 51 `RegisterSurface` nodes. Some of these are lazy connected
content/lexicon writes and some are conversation evidence. This single-turn
write set shows that filtering by message/discourse node type would omit
relevant learned and cognitive effects; a safe conversation-only mode needs an
explicit ownership/commit model across these writes.

The substrate does expose JSON graph snapshots and structural diffs, plus an
experimental revision-checked graph-delta apply operation. These are not a
conversation overlay: diffs report structural changes without assigning
ownership, delta apply requires the exact source revision and updates graph
records only, and neither operation partitions grammar/rules or adapter-side
Python state. They can support future diagnostics or a serialized merge
prototype, but do not establish a safe shared-learning/private-conversation
boundary. Conversation-only mode therefore still requires native or adapter
support for explicit ownership and defined merge policy, then validation over
the full turn pipeline.

## New authenticated API

`scripts/ocelot_api.py` is a separate standard-library HTTP process. It exposes
`/health`, `/v1/models`, `/v1/chat/completions`, and principal-scoped Ocelot
session routes. Every `/v1` request requires a bearer token mapped server-side
to a principal. The default bind is loopback (`127.0.0.1:8790`). It is
stateful, non-streaming, text-only, and intended for one process per state
directory. TLS termination, network policy, and deployment-level rate limits
are required for remote access.

See [the API guide](OPENAI_COMPATIBLE_COW_API.md), [the implementation plan](OPENAI_COMPATIBLE_COW_API_PLAN.md),
and [the accepted architecture decision](../architecture/ADR-ocelot-api-cow-isolation.md).
