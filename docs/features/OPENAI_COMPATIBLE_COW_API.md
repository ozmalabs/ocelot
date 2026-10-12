# Ocelot OpenAI-Compatible API

For the existing daemon HTTP and Unix-socket boundaries, see the
[network interface audit](NETWORK_INTERFACE_AUDIT.md).

For a rootless Podman image and Quadlet service, see the
[Podman deployment guide](../../deploy/podman/README.md).

## Current implementation

Run the separate API process with a bearer-token map:

```sh
export OCELOT_API_TOKENS='{"replace-with-secret":"alice"}'
PYTHONPATH=runners/dsl/python .venv/bin/python -m scripts.ocelot_api
```

The command boots the daemon's validated connected conversation seed profile
before pinning the shared baseline. Programmatic users of `make_server` pass
their own already-booted `WorldAdapter` explicitly.

The server listens on `127.0.0.1:8790` by default. Configure `OCELOT_API_HOST`
and `OCELOT_API_PORT` to change the listener, and `OCELOT_STATE_DIR` to choose
the per-user session directory (default `~/.ocelot/api`). The server requires
Bearer authentication on every `/v1` route, including local requests. Do not
bind it to a public interface without a TLS reverse proxy and protected
networking. The service does not expose the daemon's debug, graph, or
administrative routes. It limits request bodies to 1 MiB and active workers to
32; remote installations should also use proxy-level rate and connection
limits.

Each bearer token maps to one stable principal. A principal receives a private
namespace branched from the shared seeded baseline. Session branches use the
whole `WorldAdapter` CoW snapshot. Session files and metadata are written under
the SHA-256 name of the principal, with owner-only file permissions. The
principal is recorded in its metadata to detect a mismatched mapping on load.

## Routes

| Route | Behavior |
| --- | --- |
| `GET /health` | Liveness check; does not expose model or session data. |
| `GET /v1/models` | Advertises the `ocelot` model. |
| `POST /v1/chat/completions` | Stateful, non-streaming text chat. Uses the `Ocelot-Session-ID` header or creates/uses the principal's default session. |
| `GET /v1/ocelot/sessions` | Lists only the authenticated principal's sessions. |
| `POST /v1/ocelot/sessions` | Creates a session from the principal's namespace baseline. |
| `POST /v1/ocelot/sessions/{id}/fork` | Creates a CoW child from that principal's session. |
| `GET /v1/ocelot/sessions/{id}` | Returns ownership-scoped lifecycle state, creation/update timestamps, parent lineage, baseline mode, and checkpoint revision. |
| `DELETE /v1/ocelot/sessions/{id}` | Resets that session to the principal's baseline. |
| `DELETE /v1/ocelot/namespace` | Explicitly clears that principal's sessions and user namespace. |

Example SDK configuration:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8790/v1",
    api_key="replace-with-secret",
)
reply = client.chat.completions.create(
    model="ocelot",
    messages=[{"role": "user", "content": "What do you know about this?"}],
)
print(reply.choices[0].message.content)
```

The API uses the latest user message in each request because prior turns are
already held in the selected stateful session. System/developer messages are
prepended as labeled text context for that turn; this is a text adaptation, not
a role-aware system-prompt facility. Tool/function calling, image/audio
content, sampling controls, token limits, streaming, and tokenizer usage
  accounting are not implemented yet. Unsupported streaming requests return an
OpenAI-shaped `501` error. Usage counters currently report zero because Ocelot
does not yet provide compatible token counts.

### Request compatibility

| Field or behavior | Status | Notes |
| --- | --- | --- |
| `model` | Supported | `ocelot` is the only accepted and advertised model. |
| `messages` | Supported with stateful semantics | Requires at least one user message. Only the latest user message is passed as the turn input; earlier turns are held in the Ocelot session. |
| `system`, `developer` roles | Adapted | Text is prepended as labeled context to the latest user message. |
| `assistant` role | Accepted, ignored as input | Assistant history is already represented in the selected Ocelot session. |
| `content` string or text parts | Supported | Other content-part types are rejected. |
| `Ocelot-Session-ID` header | Supported | Selects an owned session; absent header uses the authenticated principal's default session. |
| `user` field | Ignored | It cannot change the authenticated principal or namespace. |
| `stream: false` | Supported | Returns one completed chat-completion object. |
| `stream: true` | Rejected | Returns HTTP 501; SSE is not implemented. |
| Tool/function, sampling, token-limit, and response-format fields | Rejected with HTTP 501 | Ocelot returns `unsupported_parameter`; it does not silently pretend to apply these controls. |
| Image/audio content parts | Rejected with HTTP 400 | Only text content parts are accepted. |
| Usage accounting | Placeholder | Token counts are returned as zero because compatible tokenizer counts are unavailable. |

Unrecognized top-level request fields are ignored. Invalid models, message
roles, or content produce OpenAI-shaped errors rather than selecting a fallback
model or input mode.

## State and lifecycle notes

- CoW applies to the native graph; Python-side adapter containers are copied
  when branching. Branch creation fails closed if the adapter has an attached
  storage mmap, vision handle/substrate, active teacher thread, or if the
  native snapshot rejects the graph state. Graph-bound caches such as the
  discourse store are reset and rebuilt against the child branch.
- Session state is stored in the adapter checkpoint plus a versioned JSON
  sidecar for serializable Python adapter fields. Runtime-only handles are
  reinitialized. If a newly used adapter field cannot be safely encoded, the
  save fails rather than silently dropping it. Baseline identity covers graph,
  grammar, rules, and serializable adapter runtime fields, with unordered
  containers normalized before hashing. Checkpoint metadata schema v3 migrates
  v2 graph-only digests and v1 flat checkpoint names before committing the new
  metadata pointer; failed recovery never leaves a partially initialized user
  namespace cached in the manager.
- Checkpoints currently serialize each session as a full adapter save file;
  CoW sharing is an in-memory graph optimization. Disk-level shared page storage
  and compaction are not implemented, so persistent storage grows with the
  number and size of active sessions. Superseded revisions are removed after a
  new commit; orphaned revisions and temporary files are collected on recovery.
  A revision staging failure removes its uncommitted graph/runtime files before
  returning the error.
- Turns in distinct sessions may run concurrently under per-session locks.
  Registry snapshots and session lifecycle operations use a short manager lock;
  same-session turns and fork/clear operations serialize against one another.
  Tests cover both cross-session concurrency and fork/clear waiting on an
  in-flight turn. User-wide clear takes an exclusive per-principal gate, so it
  waits for existing operations and new sessions begin only after the clear.
  Checkpoint writes still happen synchronously before the chat response. A
  failed turn or checkpoint commit restores the pre-turn branch; session and
  namespace clears publish their metadata pointer before removing old files.
- Use one API process per state directory. Cross-process locking/coordination is
  not implemented; multiple server instances sharing the same directory can
  race session revisions and metadata commits.
- Session state is loaded lazily for each authenticated principal. Restart
  recovery therefore requires the same token-to-principal mapping and state
  directory.
- `OCELOT_BASELINE_MODE=shared` is the default and uses a CoW branch of one
  shared baseline. `OCELOT_BASELINE_MODE=isolated` creates a separate baseline
  branch per principal from the configured seeded adapter; library callers
  can supply a baseline factory for independently provisioned content or
  policy. Whole-adapter isolation is supported;
  `conversation_only` isolation is not implemented because Ocelot does not yet
  have a safe graph-level boundary between conversational memory and learned
  agent state. `OCELOT_ISOLATION_MODE` accepts `whole_adapter` (the default);
  requesting `conversation_only` fails at startup rather than silently using
  whole-adapter isolation.

## Verification

Focused tests cover graph and Python-state branch isolation, cross-principal
session access, fork/clear behavior, persistence recovery, bearer auth, and
OpenAI-shaped chat responses. An optional test exercises `models.list()` and
chat completions through the official OpenAI Python SDK when it is installed.
A process-level test launches the documented module command, serves a real
conversation, restarts against the same state directory, and verifies that
the recovered session continues at the next revision.
