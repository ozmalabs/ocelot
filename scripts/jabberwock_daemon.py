#!/usr/bin/env python3
"""jabberwock_daemon — the always-on core, re-migrated onto `WorldAdapter`.

The original daemon (deleted in commit 56529c6d, "BURN THE HULL — delete
CuriousAgent") booted `CuriousAgent`, attached a `ChatWorld`, and let a Rust
`start_agent()` thread free-run `tick()`. `CuriousAgent` is gone; the agent is
now the graph loaded by `substrate.world_adapter.WorldAdapter` (seeds ->
`converse()` / `tick()` / `save()` / `load()`). This rebuild keeps the same
shape (boot -> checkpoint loop -> socket bus -> supervise) on the surviving
surface, and adds the HTTP API a companion web UI talks to.

Mechanical host I/O only, per CLAUDE.md: this file boots the agent, ticks it,
serialises it to disk, and shuttles bytes between sockets/HTTP and
`WorldAdapter.converse()` / graph queries. No decisions over graph state live
here — every conditional below is either persistence bookkeeping (which
snapshot loaded, when to rotate) or transport plumbing (which socket, which
route), never "what should the agent do."

Talk to it:
    python3 scripts/jbw_talk.py "what are you?"      # Unix socket (unchanged protocol)
    curl localhost:8787/api/status                    # HTTP API (see below)

HTTP API (fixed contract — a companion web UI is built against this exactly):
    GET  /                    -> web/index.html (static files under web/)
    POST /api/chat            {"text": "..."} -> {"ok": true, "status": "pending", "turn_id": N}
    GET  /api/chat/history    -> {"ok": true, "turns": [...]}
    GET  /api/chat/turns/<id> -> {"ok": true, "status": "pending|completed", ...}
    GET  /api/chat/turns/<id>/trace -> {"ok": true, "trace": {...}}
    POST /api/chat/turns/<id>/flag    {"note": "..."} -> {"ok", "concern_id", ...}
    POST /api/enroll          {"label": "cat", "audio_b64": "<base64 wav/webm/...>",
                                "filename": "cat.webm"} (filename optional, only used
                               to pick a decode suffix hint) ->
                               {"ok": true, "word": "...", "n_exemplars": N} — caregiver
                               teaches a word by voice (domains.speech_enrollment.enroll);
                               ANY ffmpeg-decodable audio format works (a browser
                               MediaRecorder webm/opus blob or a plain wav upload).
    POST /api/ingest          {"filename", "data_b64", "mime"?, "caption"?} ->
                               ingest an uploaded file (text/image/pdf/audio/…) into the
                               graph via domains.file_ingest.ingest_file; returns kind,
                               preview, message_id, and type-specific counts.
    GET  /api/status          -> {"ok": true, "uptime_s", "ticks", "node_count",
                                  "last_checkpoint_ts", "booted_from"}
    GET  /api/runtime/status  -> host-only liveness snapshot; never takes AGENT_LOCK,
                                  ticks cognition, or reads the live graph
    GET  /api/debug/graph     -> read-only graph summary
    GET  /api/debug/graph/nodes[?type=T&offset=N&limit=N] -> paged raw nodes
    GET  /api/debug/graph/nodes/<id> -> raw node plus incident edges
    GET  /api/debug/graph/edges[?type=E&source=I&target=I&offset=N&limit=N]
    GET  /api/debug/graph/rules[?name=substring&offset=N&limit=N]
    GET  /api/embodied/status -> read-only graph-grounded learning state and provenance
    GET  /api/sessions        -> {"ok": true, "sessions": [...]}   (Experiment nodes)
    GET  /api/sessions/<id>   -> {"ok": true, "session": {...}, "trace": [...]}
    POST /api/sessions/<id>/restart -> {"ok", "id", "status", "dispatched"} — re-queue a
                                  finished experiment (failed/done) for another child run.
    GET  /api/proposals       -> {"ok": true, "proposals": [...]}  (ExtensionProposal nodes,
                                  the rung-4 self-extension pipeline's output — see
                                  domains/self_extend_rust.py)
    GET  /api/proposals/<id>  -> {"ok": true, "proposal": {...}, "spec": {...}, "diff": "..."}
                                  (`diff` is the rendered Rust fragments, readable text)
    POST /api/proposals/<id>/approve -> {"ok": true/false, "installed", "requires_restart",
                                  "reason"?, "diagnostics"?} — calls
                                  domains.proposal_install.install_proposal (guardrailed;
                                  see that module for the policy). Synchronous: a real
                                  cargo/maturin build blocks AGENT_LOCK for its duration.
    GET  /api/auto_approve    -> {"ok": true, "enabled", "paused_until_restart",
                                  "max_installs_per_hour", "require_additive",
                                  "allowed_semantics_kinds", "installs_this_hour"} — the
                                  human-configured auto-approve SETTING (domains/
                                  auto_approve.py), OFF by default. Same shape nested under
                                  "auto_approve" in GET /api/status.
    POST /api/auto_approve    {"enabled"?, "max_installs_per_hour"?, "require_additive"?,
                                  "allowed_semantics_kinds"?} -> same shape as the GET —
                                  sets the policy node under AGENT_LOCK (domains.auto_approve.
                                  set_policy). `paused_until_restart` is NOT settable here —
                                  only a daemon restart clears it (see that module).
    GET  /api/self_concerns   -> {"ok": true, "self_concerns": [...]} — chat-originated
                                  SelfConcern nodes (seeds/conversation_self_concern.json),
                                  each {id, status, predicate, content, from_message,
                                  promoted_to}. A "noted" concern does nothing on its own.
    POST /api/self_concerns/<id>/promote -> {"ok", "standing_concern", "about"} — HUMAN-GATED:
                                  mints a StandingConcern{status:"pending"} the _concern_tick
                                  hook feeds through the agent's existing (frozen-core-denylist +
                                  human-approval) self-improvement pipeline. Marks the concern
                                  "promoted". Idempotent. Never auto-invoked.
    POST /api/self_concerns/<id>/repromote -> {"ok", ...} — HUMAN-GATED reset for a concern
                                  already promoted on a stale pipeline (e.g. old ARC bundle):
                                  tears down standing concern / experiment / minted rules, resets
                                  the SelfConcern to noted, and re-promotes with current routing.
    GET  /api/self_improvement -> {"ok", "items": [...], "has_world", "experiment_count"} —
                                  mechanical pipeline read for promoted concerns (standing
                                  concern status, CapabilityAxis, author rule, Experiment).
    POST /api/standing_concerns/<id>/adopt_gamma_production -> {"ok", "standing_concern",
                                  "triple", "reason"} — HUMAN-GATED: the ONLY path anywhere
                                  that may install a real Grammar `Production` (Theorem XII,
                                  reference-monitor containment). Requires the StandingConcern
                                  be kind="gamma_production" and already judged
                                  gamma_production_judge_status="ready_for_adopt" by
                                  _concern_tick (see domains/gamma_production_growth.py).
                                  Re-verifies the recorded triple is still inadmissible
                                  immediately before calling add_production. Idempotent: an
                                  already-adopted StandingConcern is rejected. Never
                                  auto-invoked.
    GET  /api/events          -> SSE stream: chat / status / session_update / enrolled /
                                  proposal_update / auto_approve_update events (a `chat`
                                  event carries `heard`: the list of Concept names the
                                  turn's per-turn recognition Rule grounded, [] if none —
                                  see domains/voice_world.py's `grounded_words_for`).
                                  Autonomy narration also arrives as `chat` events
                                  (text "[self-improvement update]", reply = the one-line
                                  narration — see _narrate_tick), and NL steering publishes
                                  the same self_concern_update / self_improvement_update
                                  events the HTTP promote handler does (see _steer_tick).

Usage:
    PYTHONPATH=runners/dsl/python:. python3 scripts/jabberwock_daemon.py \\
        [--ckpt-dir DIR] [--interval SECS] [--tick-hz HZ] [--keep N] \\
        [--seeds conversation|full|chat|embodied] [--socket PATH] [--http-port PORT] [--no-http] \\
        [--runs-dir DIR] [--dispatch-every N] [--fetch-every N] \\
        [--concern-every N] [--close-every N] [--world-every N] [--world-actions N] \\
        [--steer-every N] [--no-llm] [--shadow-read | --no-shadow-read] \\
        [--imagine-every N] [--collapse-every N] [--attach-libraries]
        [--attach-pybullet-humanoid [--pybullet-humanoid-protocol PATH]] [--once]

Shadow read (Wave 2, Deep-Reader — `WorldAdapter._shadow_read_turn`): ON by
default for this daemon (`--shadow-read`; `--no-shadow-read` disables it). Every
`converse()` turn gets a LIGHT deep-read of its own text on the LIVE substrate
under the `conversational` register's aperture (`register_source.
conversational_aperture` — `stages=['spine']` only, Wave 2 Task 1), recorded on
the inbound Message as `shadow_speech_act`/`shadow_focus`/`shadow_predicate`/
`shadow_latency_ms` + a `comprehended_as` link to the flow's own SentenceParse —
purely additive: `comp_*` stays authoritative for the reply, nothing here changes
what the agent says. This is the pre-cutover SHADOW gateway (Wave 3 decides
whether/how the deep read replaces `comp_*`, off the divergence numbers in
`tests/fixtures/comprehension_divergence/divergence.json`). Cost: the one-time
WordNet corpus warm-up (~1.5s) is paid on the first turn of the process's
lifetime (fresh boot OR resume — it is a process-wide NLTK cost, not a
checkpointed one), then ~30-60ms/turn steady state. `WorldAdapter.load()` (the
resume path) always restores `shadow_read=False` first (it bypasses `__init__`);
this daemon sets `adapter.shadow_read` explicitly from the CLI flag right after
`boot()` either way, so resume vs fresh-boot behave the same under this flag.

The autonomous self-improvement cycle is graph-selected: a pending
StandingConcern mints a supervised ``concern`` request; authored experiments
mint ``dispatch`` work; judged conclusions mint ``close`` work.  The host only
executes requested mechanisms and writes HostActionReceipt nodes.  Legacy
``--*-every`` flags remain accepted during migration but do not select work.
``--world-every`` only prepares the optional world capability for a later
graph-minted ``world`` request.

``--attach-pybullet-humanoid`` is a separate, opt-in mechanical body
capability.  It never starts a body loop: it waits for a graph-selected
``EmbodiedExternalTrialRequest`` and enacts only that request's opaque program,
pose affordance, and reset scenario.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import signal
import socket
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Empty, Queue

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))
sys.path.insert(0, str(ROOT / "scripts"))  # arc_run / arc3_env / worlds.arc (standing-world hook)

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds              # noqa: E402
from substrate.boot_profiles import prepass_conversation_turn  # noqa: E402
from substrate.seed_loader import manifest_for              # noqa: E402
import substrate_rs as srs                                  # noqa: E402
from domains import self_extend_rust as ser                 # noqa: E402
from domains.proposal_install import (install_proposal,     # noqa: E402
                                       _spec_dict_from_node)
from domains import auto_approve as auto_appr                # noqa: E402

# The small fast-boot seed set (mirrors scripts/converse_demo.py's CHAT_SEEDS) —
# for --seeds chat: a quick conversational agent for iteration/smoke-testing,
# layered on top of WorldAdapter()'s default CORE_SEEDS.
CHAT_SEEDS = ["relations", "intent", "conversation", "discourse", "conversation_reply",
              "reference_resolution", "language_foundation", "lang_production",
              "communication_concepts", "grounding"]
DEFAULT_SEED_PROFILE = "conversation"

WEB_DIR = ROOT / "web"

_SUFFIX = ".save"
_PREFIX = "snapshot-"
_CHAT_HISTORY_NAME = "chat_history.json"
_CHAT_HISTORY_MAX = 500


def _chat_history_path(ckpt_dir: Path) -> Path:
    return ckpt_dir.parent / _CHAT_HISTORY_NAME


def load_chat_history(path: Path) -> list[dict]:
    """Load persisted chat turns from disk. Mechanical host I/O."""
    try:
        if not path.is_file():
            return []
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        turns = data.get("turns") if isinstance(data, dict) else data
        return list(turns) if isinstance(turns, list) else []
    except Exception:  # noqa: BLE001 -- corrupt/missing file -> empty history
        return []


def save_chat_history(path: Path, turns: list[dict]) -> None:
    """Atomic write of chat turns (same publish pattern as checkpoint)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.tmp"
    payload = {"turns": turns[-_CHAT_HISTORY_MAX:]}
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=0)
    os.replace(tmp, path)


def _merge_chat_turns(file_turns: list[dict], graph_turns: list[dict]) -> list[dict]:
    """Union file + graph transcripts, preserving order, deduping (text, reply)."""
    seen = set()
    out = []
    for t in file_turns + graph_turns:
        if not isinstance(t, dict):
            continue
        text = str(t.get("text") or "").strip()
        reply = str(t.get("reply") or "").strip()
        if not text or not reply:
            continue
        key = text + "|||" + reply
        if key in seen:
            continue
        seen.add(key)
        out.append({"text": text, "reply": reply,
                    "heard": t.get("heard") or [],
                    "ts": t.get("ts")})
    return out[-_CHAT_HISTORY_MAX:]


def init_chat_history(state: "DaemonState", ckpt_dir: Path, adapter: WorldAdapter) -> None:
    """Load persisted turns; backfill from the agent graph when the file is empty."""
    path = _chat_history_path(ckpt_dir)
    file_turns = load_chat_history(path)
    graph_turns = []
    try:
        with AGENT_LOCK:
            graph_turns = adapter.chat_transcript()
    except Exception:  # noqa: BLE001
        graph_turns = []
    state.chat_turns = _merge_chat_turns(file_turns, graph_turns if not file_turns else [])
    state.chat_history_path = path
    if state.chat_turns and not file_turns:
        save_chat_history(path, state.chat_turns)


def record_chat_turn(state: "DaemonState", text: str, reply: str,
                     heard: list | None = None, turn_id: int | None = None,
                     reply_from: str | None = None) -> None:
    """Append one chat turn and persist. Mechanical bookkeeping only."""
    text = str(text or "").strip()
    reply = str(reply or "").strip()
    if not text:
        return
    turn = {"text": text, "reply": reply,
            "heard": list(heard or []),
            "ts": time.time()}
    if turn_id is not None:
        turn["turn_id"] = int(turn_id)
    if reply_from:
        turn["reply_from"] = str(reply_from)
    key = text + "|||" + reply
    if state.chat_turns and (state.chat_turns[-1].get("text", "") + "|||" +
                             state.chat_turns[-1].get("reply", "")) == key:
        return
    state.chat_turns.append(turn)
    if len(state.chat_turns) > _CHAT_HISTORY_MAX:
        state.chat_turns = state.chat_turns[-_CHAT_HISTORY_MAX:]
    try:
        save_chat_history(state.chat_history_path, state.chat_turns)
    except Exception as e:  # noqa: BLE001 -- persistence hiccup must not drop the reply
        log(f"chat-history save skipped ({type(e).__name__}: {e})")


def list_chat_history(state: "DaemonState") -> list[dict]:
    return list(state.chat_turns)


def reply_turn_trace(adapter: WorldAdapter, turn_id: str) -> dict | None:
    """Mechanical read of one turn's graph trace for the web UI."""
    with AGENT_LOCK:
        return adapter.reply_turn_trace(turn_id)


def flag_reply_turn(adapter: WorldAdapter, turn_id: str, note: str) -> dict:
    """Write a human fix note onto the turn's inbound Message and let the graph
    rule mint_reply_flag_concern file a SelfConcern. Mechanical I/O only."""
    note = str(note or "").strip()
    if not note:
        return {"ok": False, "error": "missing note"}
    try:
        import substrate_rs as srs
        mid = srs.NodeID(int(turn_id))
    except (ValueError, TypeError):
        return {"ok": False, "error": "bad turn id"}
    with AGENT_LOCK:
        if not adapter.s.has_node(mid):
            return {"ok": False, "error": "not found"}
        adapter._ensure_comprehension_seeds()
        adapter.inner.set_attr(mid, "reply_flag_note", note)
        adapter.inner.set_attr(mid, "reply_flag_pending", 1.0)
        adapter.comprehend()
        trace = adapter.reply_turn_trace(turn_id)
        concern_id = None
        if trace and trace.get("concerns"):
            for c in trace["concerns"]:
                if c.get("kind") == "reply_fix" and c.get("content") == note:
                    concern_id = c.get("id")
                    break
            if concern_id is None:
                concern_id = trace["concerns"][-1].get("id")
    return {"ok": True, "turn_id": int(turn_id), "concern_id": concern_id, "note": note}


# Serialises ALL agent access (chat turns, ticks, checkpointing, graph queries)
# against each other. HTTP/socket handler threads never touch the agent
# without holding this. Re-entrant so a caller already holding it (e.g. the
# tick loop calling the dispatch hook) can call another guarded helper.
AGENT_LOCK = threading.RLock()


def log(msg: str) -> None:
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] jabberwock: {msg}", flush=True)


# --- persistence -------------------------------------------------------------

def _snapshots(ckpt_dir: Path) -> list[Path]:
    """Existing checkpoints, newest first (by mtime)."""
    return sorted(ckpt_dir.glob(f"{_PREFIX}*{_SUFFIX}"),
                  key=lambda p: p.stat().st_mtime, reverse=True)


def _checkpoint_seed_profile(adapter: WorldAdapter) -> str | None:
    """Read the graph-resident daemon seed-profile marker, if present."""
    markers = adapter.s.nodes("DaemonSeedProfile")
    profiles = {
        str(adapter.s.node(node_id)["attrs"].get("profile", ""))
        for node_id in markers
    }
    profiles.discard("")
    if len(profiles) > 1 or (markers and not profiles):
        raise RuntimeError("checkpoint has conflicting/invalid daemon seed-profile markers")
    return next(iter(profiles), None)


def _stamp_checkpoint_seed_profile(adapter: WorldAdapter, seeds: str) -> None:
    """Persist profile identity in the graph so it travels with checkpoints."""
    current = _checkpoint_seed_profile(adapter)
    if current is not None and current != seeds:
        raise RuntimeError(
            f"cannot stamp {seeds!r} over checkpoint profile {current!r}")
    if current is None:
        adapter.s.add_node("DaemonSeedProfile", {"profile": seeds})


def _load_conversation_content_prepass(path: Path | str | None):
    """Read and canonicalize an operator-authored connected content pre-pass."""
    if path is None:
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"cannot read conversation content pre-pass manifest: {exc}") from exc
    if (not isinstance(payload, dict)
            or payload.get("schema") != "conversation_content_prepass.v1"):
        raise ValueError(
            "content manifest schema must be conversation_content_prepass.v1")
    allowed = {"schema", "content_candidates", "content_keys",
               "scoped_content_refs", "sealed"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"content manifest has unsupported fields: {unknown}")
    sealed = payload.get("sealed", False)
    if not isinstance(sealed, bool):
        raise ValueError("content manifest sealed must be a boolean")

    def names(field):
        value = payload.get(field, [])
        if not isinstance(value, list):
            raise ValueError(f"content manifest {field} must be a list")
        normalized = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(
                    f"content manifest {field} entries must be non-empty strings")
            normalized.append(item.strip())
        return sorted(set(normalized))

    candidates = names("content_candidates")
    content_keys = names("content_keys")
    raw_scoped = payload.get("scoped_content_refs", {})
    if not isinstance(raw_scoped, dict):
        raise ValueError("content manifest scoped_content_refs must be an object")
    scoped = {}
    for raw_seed_id, raw_refs in raw_scoped.items():
        seed_id = str(raw_seed_id).strip()
        if not seed_id or not isinstance(raw_refs, list):
            raise ValueError(
                "scoped content refs require a seed id and a list of typed refs")
        refs = set()
        for ref in raw_refs:
            if not isinstance(ref, dict):
                raise ValueError("scoped content refs must be objects")
            node_type, name = ref.get("type"), ref.get("name")
            if (not isinstance(node_type, str) or not node_type.strip()
                    or not isinstance(name, str) or not name.strip()):
                raise ValueError(
                    "scoped content ref requires non-empty type and name")
            refs.add((node_type.strip(), name.strip()))
        if not refs:
            raise ValueError(f"content manifest has an empty ref group: {seed_id}")
        scoped[seed_id] = [
            {"type": node_type, "name": name}
            for node_type, name in sorted(refs)
        ]
    if not candidates and not content_keys and not scoped:
        raise ValueError("content manifest must select at least one content group")
    canonical = {
        "schema": "conversation_content_prepass.v1",
        "content_candidates": candidates,
        "content_keys": content_keys,
        "sealed": sealed,
        "scoped_content_refs": {
            seed_id: scoped[seed_id] for seed_id in sorted(scoped)
        },
    }
    digest = hashlib.sha256(json.dumps(
        canonical, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    return {**canonical, "digest": digest}


def _legacy_content_prepass_digest(prepass: dict) -> str:
    """Digest format used before manifests recorded their sealed/open mode."""
    legacy = {key: prepass[key] for key in (
        "schema", "content_candidates", "content_keys",
        "scoped_content_refs")}
    return hashlib.sha256(json.dumps(
        legacy, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def boot(ckpt_dir: Path, seeds: str, *, strict_profile: bool = False,
         content_manifest: Path | str | None = None):
    """Resume from the newest checkpoint that loads (WorldAdapter.load); a
    corrupt/broken snapshot falls back to the next older. No checkpoint loads
    -> fresh boot: `--seeds chat` for a fast smoke-test set,
    `--seeds conversation` for the validated connected conversational
    dependency closure, or the full seed closure (`load_all_seeds`, the same
    `WorldAdapter(seeds=()); load_all_seeds(agent)` pattern used elsewhere for
    a "full entity" boot). Returns (adapter, booted_from).

    Every path (resumed or fresh) is then run through `domains.auto_approve.
    ensure_policy_node` (mint the AutoApprovePolicy node, `enabled: False`,
    if this graph doesn't carry one yet -- a resumed checkpoint from before
    this feature existed is exactly that case) and `clear_pause_on_boot`
    (a process restart is the event that activates whatever the PREVIOUS
    process auto-installed, so any pause carried over in a resumed
    checkpoint is stale the instant this new process is up -- see that
    module's docstring)."""
    prepass = _load_conversation_content_prepass(content_manifest)
    if prepass is not None and seeds != "conversation":
        raise ValueError(
            "a conversation content manifest requires --seeds conversation")
    requested_prepass_digest = prepass.get("digest") if prepass else None
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    adapter = None
    booted_from = None
    legacy_checkpoint_seen = False
    mismatched_checkpoint_seen = False
    mismatched_content_prepass_seen = False
    for snap in _snapshots(ckpt_dir):
        try:
            adapter = WorldAdapter.load(str(snap))
            checkpoint_profile = _checkpoint_seed_profile(adapter)
            if checkpoint_profile is None:
                legacy_checkpoint_seen = True
                if strict_profile:
                    raise RuntimeError(
                        f"checkpoint {snap.name} has no seed-profile identity; "
                        "refusing ambiguous strict-profile resume")
                log(f"warning: {snap.name} has no seed-profile identity; "
                    "accepting legacy graph without claiming profile compatibility")
            elif checkpoint_profile != seeds:
                adapter = None
                mismatched_checkpoint_seen = True
                raise RuntimeError(
                    f"checkpoint profile {checkpoint_profile!r} does not match "
                    f"requested profile {seeds!r}")
            if adapter is not None and seeds == "conversation":
                profile_state = getattr(
                    adapter, "_conversation_seed_profile_state", None)
                checkpoint_prepass_digest = (
                    profile_state.get("content_prepass_manifest_digest")
                    if isinstance(profile_state, dict) else None)
                if checkpoint_prepass_digest != requested_prepass_digest:
                    legacy_digest = (
                        _legacy_content_prepass_digest(prepass)
                        if prepass is not None else None)
                    if (isinstance(profile_state, dict)
                            and checkpoint_prepass_digest == legacy_digest):
                        # The old manifest contract always sealed content.
                        # Its digest authenticates the same preloaded closure;
                        # migrate only that exact legacy digest, update the
                        # runtime mode, then bind the checkpoint to this digest.
                        profile_state["incremental_content_loading"] = (
                            not prepass.get("sealed", False))
                        profile_state[
                            "content_prepass_manifest_digest"] = \
                            requested_prepass_digest
                        log("migrated legacy conversation content manifest "
                            "checkpoint to explicit loading mode")
                    else:
                        mismatched_content_prepass_seen = True
                        adapter = None
                        raise RuntimeError(
                            "checkpoint conversation content pre-pass digest "
                            "does not match requested manifest; refusing "
                            "profile reuse")
            log(f"resumed <- {snap.name} ({adapter.s.node_count()} nodes)")
            booted_from = "checkpoint"
            break
        except Exception as e:  # noqa: BLE001 -- try the next-older snapshot
            adapter = None
            log(f"checkpoint {snap.name} failed to load ({e}); trying older")

    if mismatched_checkpoint_seen:
        raise RuntimeError(
            f"a newer checkpoint does not match requested seed profile {seeds!r}; "
            "refusing to fall back to a potentially stale graph; existing "
            "checkpoints were preserved")
    if mismatched_content_prepass_seen:
        raise RuntimeError(
            "a newer checkpoint does not match the requested conversation "
            "content pre-pass; refusing to fall back to a potentially stale "
            "graph; existing checkpoints were preserved")
    if adapter is None and strict_profile and legacy_checkpoint_seen:
        raise RuntimeError(
            "no compatible checkpoint found: one or more legacy checkpoints "
            "lack seed-profile identity; preserve them and select/migrate a "
            "checkpoint explicitly before strict-profile startup")

    if adapter is None:
        if seeds == "chat":
            adapter = WorldAdapter()
            for sid in CHAT_SEEDS:
                try:
                    adapter.inner.load_seed_manifest(manifest_for(sid), adapter.agent)
                except Exception as e:  # noqa: BLE001 -- one bad seed shouldn't block boot
                    log(f"  seed '{sid}' skipped: {e}")
            try:
                adapter.install_register_lexicon()
            except Exception as e:  # noqa: BLE001
                log(f"  register lexicon skipped: {e}")
            log(f"fresh CHAT boot ({adapter.s.node_count()} nodes)")
        elif seeds == "conversation":
            # Production conversation boot uses the cached dependency/content
            # pre-pass and its validated connected closure. Keep this distinct
            # from the deliberately tiny chat smoke profile and the full
            # all-faculty boot; an incomplete closure must not silently widen
            # into an unbounded full boot.
            from substrate.boot_profiles import load_conversation_seed_profile

            adapter = WorldAdapter(seeds=())
            rep = load_conversation_seed_profile(
                adapter,
                content_keys=(prepass or {}).get("content_keys", ()),
                content_candidates=(prepass or {}).get("content_candidates"),
                scoped_content_refs=(prepass or {}).get(
                    "scoped_content_refs"),
                content_prepass_manifest_digest=requested_prepass_digest,
                # A manifest eagerly installs its connected closure but does
                # not implicitly freeze future conversation vocabulary.
                # Unknown later content still goes through the validated,
                # dependency-closed provider path unless the operator marks
                # this fixed workload explicitly sealed.
                incremental_content_loading=(
                    prepass is None or not prepass.get("sealed", False)))
            if (not rep.get("selection_complete") or rep.get("failed")):
                raise RuntimeError(
                    "connected conversation seed profile failed: "
                    f"selection_complete={rep.get('selection_complete')}, "
                    f"failed={rep.get('failed')}")
            log(f"fresh CONVERSATION boot: {rep['loaded']}/{rep['total']} "
                f"connected seeds, {rep['concepts']} concepts, "
                f"{len(rep.get('runtime_modules_warmed', []))} runtime "
                f"modules prewarmed ({adapter.s.node_count()} nodes); "
                f"content_prepass={'incremental' if prepass is None else 'sealed'}")
        elif seeds == "embodied":
            # Dependency-closed real-body profile. It loads the same
            # instruction, developmental, supervision, and motor graph used
            # by the real-PyBullet tests, without unrelated library fan-out.
            adapter = WorldAdapter(seeds=(
                "embodied_motor_bootstrap", "embodied_instruction_goal",
                "comprehend_instruction", "learned_lexicon",
                # The energy ledger and the surprise/authority layer: without
                # these an attached body publishes readings nothing consumes.
                "energy_ledger", "surprise_promotion",
                # Without this the imagination trace is unbounded and quadratic
                # in the graph it records: growth7 reached 960,663
                # ImaginedConclusion nodes (96.1% of the graph) and was killed
                # by the kernel OOM killer at 8.4 GB.
                "imagination_trace_retention",
            ))
            log(f"fresh EMBODIED boot ({adapter.s.node_count()} nodes)")
        else:
            adapter = WorldAdapter(seeds=())
            rep = load_all_seeds(adapter)
            log(f"fresh FULL boot: {rep['loaded']}/{rep['total']} seeds, "
                f"{rep['concepts']} concepts, {len(rep['failed'])} failed "
                f"({adapter.s.node_count()} nodes)")
        booted_from = "seeds"

    reconcile_seed_ids = None
    if booted_from == "checkpoint" and seeds == "conversation":
        profile_state = getattr(
            adapter, "_conversation_seed_profile_state", None)
        loaded_seed_ids = (profile_state.get("loaded_seed_ids")
                           if isinstance(profile_state, dict) else None)
        if not loaded_seed_ids:
            raise RuntimeError(
                "conversation checkpoint has no recoverable connected seed "
                "scope; refusing full-seed reconciliation")
        reconcile_seed_ids = {str(seed_id) for seed_id in loaded_seed_ids}

    # SEED-ON-RESUME RECONCILIATION: a checkpoint captures the seed RULES that
    # existed when it was saved; seed edits made since (a new seed file, or a
    # new rule added to an existing one) are absent on resume, so the resumed
    # agent silently runs stale rules. A fresh boot loads current seeds via
    # load_all_seeds; a resume must reconcile. This installs any current-seed
    # executable RULE (by name) missing from the resumed graph -- rule-only and
    # name-guarded, so it never duplicates an existing rule and never touches
    # nodes/edges (which load_seed_manifest adds non-idempotently). New NODES on
    # resume stay out of scope (a fresh boot handles those).
    if booted_from == "checkpoint":
        try:
            n = _reconcile_seed_rules(
                adapter, seed_ids=reconcile_seed_ids)
            if n:
                log(f"seed-reconcile: installed {n} seed rule(s) missing from the resumed checkpoint")
        except Exception as e:  # noqa: BLE001 -- never let reconciliation block boot
            log(f"seed-reconcile skipped ({type(e).__name__}: {e})")
        try:
            nc = _reconcile_seed_concepts(
                adapter, seed_ids=reconcile_seed_ids)
            if nc:
                log(f"seed-reconcile: installed {nc} seed Concept(s) missing from the resumed checkpoint")
        except Exception as e:  # noqa: BLE001 -- never let reconciliation block boot
            log(f"seed-reconcile (concepts) skipped ({type(e).__name__}: {e})")
        try:
            nsp = _reconcile_seed_typed_nodes(
                adapter, "SelfProcess", "process", seed_ids=reconcile_seed_ids)
            if nsp:
                log(f"seed-reconcile: installed {nsp} seed SelfProcess account(s) missing from the resumed checkpoint")
        except Exception as e:  # noqa: BLE001 -- never let reconciliation block boot
            log(f"seed-reconcile (self-processes) skipped ({type(e).__name__}: {e})")
        try:
            nrc = _reconcile_seed_typed_nodes(
                adapter, "RelationCue", "name", seed_ids=reconcile_seed_ids)
            if nrc:
                log(f"seed-reconcile: installed {nrc} seed RelationCue(s) missing from the resumed checkpoint")
        except Exception as e:  # noqa: BLE001 -- never let reconciliation block boot
            log(f"seed-reconcile (relation-cues) skipped ({type(e).__name__}: {e})")
        try:
            nvo = _reconcile_seed_typed_nodes(
                adapter, "VariationOp", "name", seed_ids=reconcile_seed_ids)
            if nvo:
                log(f"seed-reconcile: installed {nvo} seed VariationOp(s) missing from the resumed checkpoint")
        except Exception as e:  # noqa: BLE001 -- never let reconciliation block boot
            log(f"seed-reconcile (variation-ops) skipped ({type(e).__name__}: {e})")
        try:
            # Wave 2 (Deep-Reader): a new register (e.g. `conversational`, the
            # aperture-as-graph-data register the chat shadow-read gateway looks
            # up by name) is a NODE, not a rule -- `_reconcile_seed_rules` never
            # installs it, so a resumed-from-checkpoint daemon booted before the
            # register existed would otherwise never see it.
            nrg = _reconcile_seed_typed_nodes(
                adapter, "ShapeSignatureRegister", "name",
                seed_ids=reconcile_seed_ids)
            if nrg:
                log(f"seed-reconcile: installed {nrg} seed ShapeSignatureRegister(s) missing from the resumed checkpoint")
        except Exception as e:  # noqa: BLE001 -- never let reconciliation block boot
            log(f"seed-reconcile (registers) skipped ({type(e).__name__}: {e})")
        try:
            # SELF-OPTIMISATION (Wave: 2026-07-10): the HealthNorm{metric, ceiling}
            # belief seeds/comprehension_health.json's note_comprehension_latency_gap
            # reads (via NodesOfType, not an edge — see that rule's own comment) is a
            # NODE, so `_reconcile_seed_rules` never installs it on a resumed
            # checkpoint older than this seed.
            nhn = _reconcile_seed_typed_nodes(
                adapter, "HealthNorm", "metric", seed_ids=reconcile_seed_ids)
            if nhn:
                log(f"seed-reconcile: installed {nhn} seed HealthNorm(s) missing from the resumed checkpoint")
        except Exception as e:  # noqa: BLE001 -- never let reconciliation block boot
            log(f"seed-reconcile (health-norms) skipped ({type(e).__name__}: {e})")
        try:
            # FOVEATION-AS-HINT (2026-07-11): the ApertureBudget{register,
            # max_escalations, max_stage_count, fallback_ratio_threshold}
            # belief seeds/reading_aperture.json's escalate_* rules read
            # (via NodesOfType, the SAME Argmax-by-key pattern as HealthNorm
            # above) is a NODE, so `_reconcile_seed_rules` never installs it
            # on a resumed checkpoint older than this seed.
            nab = _reconcile_seed_typed_nodes(
                adapter, "ApertureBudget", "register",
                seed_ids=reconcile_seed_ids)
            if nab:
                log(f"seed-reconcile: installed {nab} seed ApertureBudget(s) missing from the resumed checkpoint")
        except Exception as e:  # noqa: BLE001 -- never let reconciliation block boot
            log(f"seed-reconcile (aperture-budgets) skipped ({type(e).__name__}: {e})")
        try:
            # DYNAMIC-THRESHOLDS (Wave: 2026-07-11): the two held derivation
            # Programs (reading_derive_trace_capacity / reading_derive_max_order,
            # seeds/reading_aperture.json) are NODES read by domains/reading_norms
            # via _load_program-by-name, so `_reconcile_seed_rules` never installs
            # them on a resumed checkpoint older than this seed — without this the
            # resumed daemon silently falls back to the static base values
            # (graceful, but not dynamic). Key-guarded by `name`, idempotent —
            # the same treatment every other seed-shipped node type above gets.
            npr = _reconcile_seed_typed_nodes(
                adapter, "Program", "name", seed_ids=reconcile_seed_ids)
            if npr:
                log(f"seed-reconcile: installed {npr} seed Program(s) missing from the resumed checkpoint")
        except Exception as e:  # noqa: BLE001 -- never let reconciliation block boot
            log(f"seed-reconcile (programs) skipped ({type(e).__name__}: {e})")
        try:
            # INTERLOCUTOR-AS-MODELED-PARTICIPANT (Wave 2026-07-11): the
            # InterlocutorShape codebook (seeds/interlocutor_shapes.json,
            # priors-by-shape-matching for self-report reliability) ships
            # NODES only, so `_reconcile_seed_rules` never installs it on a
            # resumed checkpoint older than this wave.
            nis = _reconcile_seed_typed_nodes(
                adapter, "InterlocutorShape", "name",
                seed_ids=reconcile_seed_ids)
            if nis:
                log(f"seed-reconcile: installed {nis} seed InterlocutorShape(s) missing from the resumed checkpoint")
        except Exception as e:  # noqa: BLE001 -- never let reconciliation block boot
            log(f"seed-reconcile (interlocutor-shapes) skipped ({type(e).__name__}: {e})")
        try:
            nck = _reconcile_seed_capkeys(
                adapter, seed_ids=reconcile_seed_ids)
            if nck:
                log(f"seed-reconcile: backfilled {nck} seed CapKey edge(s) missing from the resumed checkpoint")
        except Exception as e:  # noqa: BLE001 -- never let reconciliation block boot
            log(f"seed-reconcile (capkeys) skipped ({type(e).__name__}: {e})")
        try:
            ns = _scrub_stale_author_rules(adapter)
            if ns:
                log(f"seed-reconcile: scrubbed {ns} stale author_experiment rule(s)")
            nc = _cancel_unscoped_experiments(adapter)
            if nc:
                log(f"seed-reconcile: cancelled {nc} unscoped experiment(s)")
        except Exception as e:  # noqa: BLE001
            log(f"author-rule scrub skipped ({type(e).__name__}: {e})")
    if booted_from == "seeds":
        _stamp_checkpoint_seed_profile(adapter, seeds)

    auto_appr.ensure_policy_node(adapter)
    auto_appr.clear_pause_on_boot(adapter)
    try:
        adapter.wire_substrate_identity()
    except Exception:  # noqa: BLE001
        pass
    try:
        adapter.refresh_stale_acronym_answers()
    except Exception:  # noqa: BLE001
        pass
    try:
        adapter.wire_upload_text_read_faculty()
    except Exception:  # noqa: BLE001
        pass
    # The asynchronous scheduler is intentionally self-load-only: it is a
    # daemon/world capability, not a tax every offline graph load pays.  Load
    # its rules mechanically here for both fresh and resumed daemon graphs.
    # The rules mint requests; this host never decides which action is due.
    try:
        n_supervisor = _ensure_supervisory_scheduler(adapter)
        if n_supervisor:
            log(f"supervisor: installed {n_supervisor} graph scheduling rule(s)")
    except Exception as e:  # noqa: BLE001 -- daemon remains usable without a new seed
        log(f"supervisor seed skipped ({type(e).__name__}: {e})")
    return adapter, booted_from


def _canon_rule_body(rule_json: dict) -> str:
    """Canonical string form of an executable rule's BODY (name + match + where +
    effects), obtained by round-tripping the rule through the Rust rule
    serializer (import_rules -> export_rules on a throwaway Substrate). Both a
    seed-FILE rule and a LIVE exported rule are normalised through the SAME
    encoder, so cosmetic JSON differences (key order, number/edge encoding) do
    NOT read as a body change -- only a genuine semantic edit does. The MATCH
    clause list is compared ORDER-INSENSITIVELY (canonical sort): the Rust
    `Substrate::add_rule` reorders match clauses cost-greedily at install time
    (and the greedy order on the LIVE populated graph can differ from the order
    on this throwaway empty one), so authored-vs-live clause order is an
    installation artefact, never a semantic edit -- comparing it order-sensitively
    made every such rule refresh on every resume (perpetual churn). Returns ""
    on any failure (treated as 'cannot compare' -> no refresh)."""
    from substrate.rule_ir import canonical_rule_body
    return canonical_rule_body(rule_json)


# Seeds whose rules are BODY-REFRESHED on resume (not just installed-if-missing).
# Scoped to the actively-developed conversation/gap/elaboration migration seeds:
# their rules are hand-authored from standard Term types that round-trip cleanly
# through _canon_rule_body, so the body-diff is reliable (no false refreshes). The
# broader rule zoo (some seeds use exotic Terms that don't round-trip byte-identically)
# stays install-if-missing only, so it is never churned. This is where the "edit a
# rule, restart, it applies" workflow lives.
_REFRESHABLE_SEEDS = frozenset({
    # Episodic message memory is part of live conversational cognition; its
    # graph-owned provenance rule must refresh on resumed daemon checkpoints.
    "memory_core",
    "communication_intent_arbitration",
    "speech_act_classify",
    "comprehend_instruction", "conversation_self_concern", "conversation_topic_route",
    "conversation_topic_tracking", "gap_awareness", "conversation_elaborate",
    "conversation_steering",
    "topic_search", "conversation_reply_flag", "conversation_capability_route",
    "conversation_capability_reply", "movement_affordances", "inference_affordances",
    "conversation_reply",
    "conversation_topic_reply", "conversation_honest_floor", "conversation_self_reply",
    "conversation_attachment_route", "conversation_attachment_reply",
    "conversation_upload_text_detect",
    "upload_foveated_text",
    "topic_sync_ground", "topic_search_verify",
    "improvement_integrity",
    "variation_ops",
    "adoption_safety",
    "literary_analysis_driving",
    "comprehension_health",
    "self_optimisation",
    "conversation_pronoun_enrichment",
    "reading_aperture",
    "conversation_grice",
    "interlocutor_trust",
    "reading_reform_ingest",
    "proposition_capture",
    "code_write_gap",
    "curriculum_study",
    # Embodied bootstrap and instruction bridges are actively evolved graph
    # rules. A resumed cognition must receive their canonical current bodies,
    # otherwise a checkpoint silently retains obsolete motor/mission logic.
    "embodied_motor_bootstrap", "embodied_instruction_goal",
    "embodied_learning_session", "embodied_adaptation", "cognitive_pareto",
    "cognitive_supervision",
})


def _reconcile_seed_rules(adapter: WorldAdapter, *,
                          seed_ids: set[str] | None = None) -> int:
    """Reconcile the resumed graph's executable rules (match + effect(s)) with the
    current seed files. Two moves, both name-guarded and idempotent:

      - INSTALL a seed rule whose name is absent (the original behaviour, ALL seeds).
      - REFRESH a seed rule (only for _REFRESHABLE_SEEDS) whose name is present but
        whose BODY changed since the checkpoint (an EDIT -- e.g. a new where-guard):
        tombstone the stale rule (remove_rule) and reinstall the file version, so
        the seed FILE stays canonical across restarts. Leak-free: a refresh fires
        ONLY on a real canonical-body diff (see _canon_rule_body), so an unchanged
        rule is never churned (no tombstone accumulation).

    Nodes/edges are still never touched here (see _reconcile_seed_concepts for
    Concept nodes). Encyclopedic prose 'rules' (no match/effect) are ignored.
    Returns the count installed + refreshed."""
    import glob as _glob
    import json as _json
    import os as _os
    from substrate.seed_loader import SEED_DIR
    try:
        live = list(adapter.inner.export_rules())
    except Exception:  # noqa: BLE001
        return 0
    # name -> (rule_idx, canonical body) for the ACTIVE live rules (index i == RuleIdx i)
    live_by_name: dict = {}
    for i, r in enumerate(live):
        if r.get("active") and r.get("name") and r["name"] not in live_by_name:
            live_by_name[r["name"]] = (i, _canon_rule_body(r))
    present = set(live_by_name)
    changed = 0
    added = 0
    allowed = None if seed_ids is None else {str(seed_id) for seed_id in seed_ids}
    paths = sorted(_glob.glob(_os.path.join(str(SEED_DIR), "*.json"))) \
        + sorted(_glob.glob(_os.path.join(str(SEED_DIR), "generated", "*.json")))
    for f in paths:
        try:
            d = _json.load(open(f))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(d, dict):
            continue
        seed_id = str(d.get("id") or _os.path.basename(f)[:-5])
        if allowed is not None and seed_id not in allowed:
            continue
        execu = [
            r for r in (d.get("rules") or [])
            if isinstance(r, dict) and r.get("name")
            and r.get("match") and (r.get("effects") or r.get("effect"))
        ]
        missing = [r for r in execu if r["name"] not in present]
        # A rule present but whose canonical body differs from the file = a
        # stale checkpoint copy of an edited rule -> refresh it. Only for the
        # migration seeds (reliable round-trip); other seeds are install-only.
        refresh = []
        if d.get("id") in _REFRESHABLE_SEEDS:
            for r in execu:
                if r["name"] in live_by_name:
                    idx, live_body = live_by_name[r["name"]]
                    seed_body = _canon_rule_body(r)
                    if seed_body and live_body and seed_body != live_body:
                        refresh.append((idx, r))
        if refresh:
            try:
                for idx, _r in refresh:
                    adapter.inner.remove_rule(idx)              # tombstone the stale body
                adapter.inner.load_seed_manifest(
                    {"id": d.get("id"), "rules": [r for _i, r in refresh]}, adapter.agent)
                changed += len(refresh)
                log(f"seed-reconcile: refreshed {len(refresh)} changed rule(s) from {d.get('id')}")
            except Exception as e:  # noqa: BLE001
                log(f"seed-reconcile (refresh) {d.get('id')} skipped ({type(e).__name__}: {e})")
        if missing:
            try:
                adapter.inner.load_seed_manifest({"id": d.get("id"), "rules": missing}, adapter.agent)
                for r in missing:
                    present.add(r["name"])
                added += len(missing)
                log(f"seed-reconcile: +{len(missing)} rule(s) from {d.get('id')}")
            except Exception as e:  # noqa: BLE001 -- one bad seed's rules shouldn't block the rest
                log(f"seed-reconcile: {d.get('id')} skipped ({type(e).__name__}: {e})")
    return added + changed


def _reconcile_seed_typed_nodes(adapter: WorldAdapter, node_type: str,
                                key_attr: str, *,
                                seed_ids: set[str] | None = None) -> int:
    """Install (find-or-create by `key_attr`) every `node_type` node declared in
    a TOP-LEVEL seed that the resumed graph doesn't already hold. Some seeds ship
    identity nodes their RULES / faculties depend on (gap_awareness's deficiency
    `Concept`s that the intent `refers_to` rule matches by NAME; self_processes'
    `SelfProcess` accounts that `find_self_process` matches by `process`);
    `_reconcile_seed_rules` installs rules but deliberately not nodes, so these
    must be reconciled here or the resumed agent lacks them. Key-guarded =>
    idempotent, never duplicates. Scoped to top-level `seeds/*.json` (the giant
    `seeds/acquired/**` sets are out of scope). Mechanical seed loading, no
    decision. Returns the count installed."""
    import glob as _glob
    import json as _json
    import os as _os
    from substrate.seed_loader import SEED_DIR
    try:
        held = {adapter.s.node(n)["attrs"].get(key_attr)
                for n in adapter.s.nodes(node_type)}
    except Exception:  # noqa: BLE001
        return 0
    added = 0
    allowed = None if seed_ids is None else {str(seed_id) for seed_id in seed_ids}
    for f in sorted(_glob.glob(_os.path.join(str(SEED_DIR), "*.json"))):
        try:
            d = _json.load(open(f))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(d, dict):
            continue
        seed_id = str(d.get("id") or _os.path.basename(f)[:-5])
        if allowed is not None and seed_id not in allowed:
            continue
        for node in (d.get("nodes") or []):
            if not isinstance(node, dict) or node.get("type") != node_type:
                continue
            attrs = node.get("attrs") or {}
            key = attrs.get(key_attr)
            if not key or key in held:
                continue
            try:
                adapter.s.add_node(node_type, dict(attrs))
                held.add(key)
                added += 1
            except Exception:  # noqa: BLE001 -- one bad node shouldn't block the rest
                pass
    return added


def _reconcile_seed_capkeys(adapter: WorldAdapter, *,
                            seed_ids: set[str] | None = None) -> int:
    """Reconcile the CapKey provenance join on resume (the
    `_reconcile_seed_typed_nodes` precedent, Wave 5): for every top-level seed
    manifest declaring a `capability_keys` list, ensure its SeedSummary exists
    (find-or-create — a checkpoint predating SeedSummary minting lacks them)
    and re-run substrate.boot_all._backfill_seed_capkeys (find-or-create
    CapKey{name} + SeedSummary -provides_key-> CapKey, edge-once) so a resumed
    daemon holds the same join a fresh boot mints at load time. Mechanical,
    idempotent; returns the number of provides_key edges added."""
    import glob as _glob
    import json as _json
    import os as _os
    from substrate.seed_loader import SEED_DIR
    from substrate.boot_all import _backfill_seed_capkeys, _mint_seed_summary
    added = 0
    allowed = None if seed_ids is None else {str(seed_id) for seed_id in seed_ids}
    for f in sorted(_glob.glob(_os.path.join(str(SEED_DIR), "*.json"))):
        try:
            d = _json.load(open(f))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(d, dict) or not d.get("capability_keys"):
            continue
        sid = d.get("id") or _os.path.basename(f)[:-5]
        if allowed is not None and str(sid) not in allowed:
            continue
        try:
            _mint_seed_summary(adapter, sid, d)          # idempotent find-or-create
            added += _backfill_seed_capkeys(adapter, sid, d)
        except Exception:  # noqa: BLE001 -- one bad seed shouldn't block the rest
            continue
    return added


def _reconcile_seed_concepts(adapter: WorldAdapter, *,
                             seed_ids: set[str] | None = None) -> int:
    """Reconcile top-level-seed `Concept` nodes by name (see
    _reconcile_seed_typed_nodes). Kept as a named entry point for callers/tests."""
    return _reconcile_seed_typed_nodes(
        adapter, "Concept", "name", seed_ids=seed_ids)


def _ensure_supervisory_scheduler(adapter: WorldAdapter) -> int:
    """Install only missing self-load-only supervisor rules.

    This is seed transport, not a host policy: the manifest is the source of
    the action demand and priority calculation.  Restricting the manifest to
    missing rule names makes it safe for a restored checkpoint and avoids
    loading the scheduler's optional native-worker fixtures into a chat graph.
    """
    manifest = manifest_for("cognitive_scheduler")
    live = {str(r.get("name")) for r in adapter.inner.export_rules() if r.get("name")}
    missing = [r for r in manifest.get("rules", []) if r.get("name") not in live]
    if not missing:
        return 0
    adapter.inner.load_seed_manifest({
        "id": "cognitive_scheduler",
        "depends_on": manifest.get("depends_on", []),
        "rules": missing,
    }, adapter.agent)
    return len(missing)


def _async_cycle_budget(adapter: WorldAdapter):
    """Read the single graph-authored asynchronous rewrite quantum.

    This intentionally performs no fallback selection.  A missing or
    ambiguous budget leaves legacy adapters on their own tick contract; a
    fully seeded cognition has exactly one ``AsyncDaemonCycleBudget`` whose
    value is adjusted by cognitive supervision.
    """
    try:
        budgets = [node for node in adapter.s.nodes("AsyncDaemonCycleBudget")
                   if adapter.s.has_node(node)
                   and adapter.s.node(node)["attrs"].get("status") == "active"]
    except Exception:  # noqa: BLE001 -- compatibility with partial/chat graphs
        return None, None
    if len(budgets) != 1:
        return None, None
    attrs = adapter.s.node(budgets[0])["attrs"]
    quantum = attrs.get("quantum_units")
    if type(quantum) is not int or quantum <= 0:
        return None, None
    return budgets[0], quantum


def _record_async_cycle_consumption(adapter: WorldAdapter, budget, quantum: int,
                                    rewrite_steps: int) -> None:
    """Record mechanical use of a graph-provided quantum without choosing it."""
    if budget is None or not adapter.s.has_node(budget):
        return
    adapter.inner.set_attr(budget, "last_consumed_quantum_units", int(quantum))
    adapter.inner.set_attr(budget, "last_consumed_rewrite_steps", int(rewrite_steps))


def checkpoint(adapter: WorldAdapter, ckpt_dir: Path, keep: int) -> Path:
    """Atomic, rotated checkpoint: save to a temp file, `os.replace()` into
    place (atomic on the same filesystem), then prune to the newest `keep`.
    Holds AGENT_LOCK so no turn/tick mutates the agent mid-save."""
    with AGENT_LOCK:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")  # us -> unique under rapid checkpointing
        final = ckpt_dir / f"{_PREFIX}{stamp}{_SUFFIX}"
        tmp = ckpt_dir / f".{_PREFIX}{stamp}.tmp"
        adapter.save(str(tmp))
        os.replace(tmp, final)                       # atomic publish
        for old in _snapshots(ckpt_dir)[keep:]:      # rotate: keep the newest `keep`
            try:
                old.unlink()
            except OSError:
                pass
        log(f"checkpoint -> {final.name} ({final.stat().st_size // 1024} KB, keep {keep})")
        return final


# --- shared daemon state -------------------------------------------------------

class DaemonState:
    """Everything the transport layers (socket/HTTP) need to read/publish.
    Plain bookkeeping — no agent decisions."""

    def __init__(self, adapter: WorldAdapter, booted_from: str):
        self.adapter = adapter
        # Remote retrieval is fulfilled only by graph-selected async host
        # actions in daemon mode; synchronous turns can still read local and
        # held evidence without waiting on network I/O.
        adapter._daemon_async_io_only = True
        self.booted_from = booted_from
        self.start_mono = time.monotonic()
        self.ticks = 0
        self.last_checkpoint_ts: float | None = None
        # signalled on any inbound event (chat, dispatch mutation) so the tick
        # loop can tick promptly without busy-spinning between signals.
        self.dirty = threading.Event()
        self.dirty.set()  # one tick right after boot
        # Transport bookkeeping only: graph nodes remain the turn and reply
        # authority.  This set tells the daemon which published turns require
        # their rule-admission pass before a reply can be read back.
        self.pending_turns: dict[int, str] = {}
        self._sse_clients: list[Queue] = []
        self._sse_lock = threading.Lock()
        self._sessions_prev: dict = {}   # session id -> last-seen status (session_update diff)
        self._improvement_prev: tuple = ()  # pipeline digest for self_improvement_update SSE
        self.chat_turns: list[dict] = []
        self.chat_history_path: Path = Path()
        self.runs_dir: str = ""
        # Host-observed snapshots for /api/runtime/status.  The status route
        # reads only these fields: it remains responsive while cognition holds
        # AGENT_LOCK or is inside a long native fixed point.
        self.runtime_state = "online"
        self.tick_active = False
        self.last_tick_mono: float | None = None
        self.last_tick_error: str = ""
        self.node_count_snapshot = adapter.s.node_count()
        self.host_actions_completed = 0
        self.last_host_action = ""
        self.last_host_action_outcome = ""
        # Search transport workers receive immutable request snapshots only.
        # Their futures are rejoined and committed by the daemon tick thread
        # while it owns AGENT_LOCK.
        self.search_io_executor = ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="topic-search-io")
        self.pending_search_host_actions: dict[int, dict] = {}
        _recover_interrupted_search_io(adapter)
        # Optional external body/simulator transducer.  It is host capability,
        # never policy: the graph must still author and schedule the exact
        # EmbodiedExternalTrialRequest before this callable is invoked.
        self.embodied_trial_executor = None
        self.embodied_trial_closer = None

    def publish_event(self, obj: dict) -> None:
        line = json.dumps(obj)
        with self._sse_lock:
            dead = []
            for q in self._sse_clients:
                try:
                    q.put_nowait(line)
                except Exception:  # noqa: BLE001 -- a full/broken queue drops this client
                    dead.append(q)
            for q in dead:
                self._sse_clients.remove(q)

    def add_sse_client(self) -> Queue:
        q: Queue = Queue()
        with self._sse_lock:
            self._sse_clients.append(q)
        return q

    def remove_sse_client(self, q: Queue) -> None:
        with self._sse_lock:
            if q in self._sse_clients:
                self._sse_clients.remove(q)


def _recover_interrupted_search_io(adapter: WorldAdapter) -> None:
    """Requeue persisted retrievals that lost their in-memory Future at restart."""
    sub, native = adapter.s, adapter.inner
    for req in list(sub.nodes("SearchRequest")):
        if native.has_node(req) and sub.node(req)["attrs"].get("status") == "running":
            native.set_attr(req, "status", "requested")
            native.set_attr(req, "search_io_token", None)
    for req in list(sub.nodes("GroundRequest")):
        if native.has_node(req) and sub.node(req)["attrs"].get("status") == "running":
            native.set_attr(req, "status", "requested")
            native.set_attr(req, "ground_io_token", None)
    for req in list(sub.nodes("DetailRequest")):
        if native.has_node(req) and sub.node(req)["attrs"].get("status") == "running":
            native.set_attr(req, "status", "requested")
            native.set_attr(req, "detail_io_token", None)
    for host in list(sub.nodes("HostActionRequest")):
        if not native.has_node(host):
            continue
        attrs = sub.node(host)["attrs"]
        if attrs.get("action") not in ("search", "detail") or attrs.get("status") != "io_pending":
            continue
        native.set_attr(host, "status", "requested")
        native.set_attr(host, "search_io_token", None)
        for task in native.neighbours(host, "scheduled_as"):
            if native.has_node(task):
                native.set_attr(task, "status", "host_requested")


def _status_dict(state: DaemonState) -> dict:
    with AGENT_LOCK:
        node_count = state.adapter.s.node_count()
        try:
            aa = auto_appr.policy_status(state.adapter)
        except Exception:  # noqa: BLE001 -- status must never 500 on this
            aa = {"enabled": False, "paused_until_restart": False, "installs_this_hour": 0}
    return {
        "ok": True,
        "uptime_s": round(time.monotonic() - state.start_mono, 3),
        "ticks": state.ticks,
        "node_count": node_count,
        "last_checkpoint_ts": state.last_checkpoint_ts,
        "booted_from": state.booted_from,
        "auto_approve": aa,
    }


def _runtime_status_dict(state: DaemonState) -> dict:
    """Constant-time host liveness; deliberately does not touch the graph."""
    now = time.monotonic()
    return {
        "ok": True,
        "runtime_state": state.runtime_state,
        "uptime_s": round(now - state.start_mono, 3),
        "ticks": state.ticks,
        "tick_active": state.tick_active,
        "last_tick_age_s": (None if state.last_tick_mono is None
                            else round(now - state.last_tick_mono, 3)),
        "last_tick_error": state.last_tick_error,
        "work_pending": state.dirty.is_set(),
        "node_count_snapshot": state.node_count_snapshot,
        "host_actions_completed": state.host_actions_completed,
        "last_host_action": state.last_host_action,
        "last_host_action_outcome": state.last_host_action_outcome,
        "last_checkpoint_ts": state.last_checkpoint_ts,
        "booted_from": state.booted_from,
        "requires_cognition": False,
    }


_DEBUG_PAGE_DEFAULT = 100
_DEBUG_PAGE_MAX = 1000


def _debug_page(query: dict[str, list[str]]) -> tuple[int, int]:
    def integer(name: str, default: int) -> int:
        try:
            return int((query.get(name) or [default])[0])
        except (TypeError, ValueError):
            return default
    return max(0, integer("offset", 0)), max(1, min(_DEBUG_PAGE_MAX,
                                                     integer("limit", _DEBUG_PAGE_DEFAULT)))


def _debug_graph_snapshot(adapter: WorldAdapter) -> dict:
    """Raw, read-only substrate export. Caller holds AGENT_LOCK."""
    return _debug_json_safe(adapter.inner.graph_to_dict())


def _debug_json_safe(value):
    """Lossless-enough JSON projection for graph debugging, never mutation."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return {"__bytes_hex__": value.hex(), "length": len(value)}
    if isinstance(value, dict):
        return {str(key): _debug_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_debug_json_safe(item) for item in value]
    if hasattr(value, "value"):
        return _debug_json_safe(value.value)
    return {"__repr__": repr(value), "type": type(value).__name__}


def debug_graph_summary(adapter: WorldAdapter) -> dict:
    graph = _debug_graph_snapshot(adapter)
    types: dict[str, int] = {}
    for node in graph.get("nodes", []):
        node_type = str(node.get("type") or "")
        types[node_type] = types.get(node_type, 0) + 1
    return {
        "ok": True,
        "read_only": True,
        "node_count": len(graph.get("nodes", [])),
        "edge_count": len(graph.get("edges", [])),
        "rule_count": len(adapter.inner.export_rules()),
        "next_id": graph.get("next_id"),
        "node_types": dict(sorted(types.items())),
    }


def debug_graph_nodes(adapter: WorldAdapter, query: dict[str, list[str]]) -> dict:
    graph = _debug_graph_snapshot(adapter)
    node_type = (query.get("type") or [""])[0]
    nodes = [node for node in graph.get("nodes", [])
             if not node_type or node.get("type") == node_type]
    offset, limit = _debug_page(query)
    return {"ok": True, "read_only": True, "total": len(nodes),
            "offset": offset, "limit": limit, "nodes": nodes[offset:offset + limit]}


def debug_graph_node(adapter: WorldAdapter, node_id: str) -> dict | None:
    try:
        wanted = int(node_id)
    except (TypeError, ValueError):
        return None
    graph = _debug_graph_snapshot(adapter)
    node = next((item for item in graph.get("nodes", []) if item.get("id") == wanted), None)
    if node is None:
        return None
    edges = [edge for edge in graph.get("edges", [])
             if edge.get("src") == wanted or edge.get("tgt") == wanted]
    return {"ok": True, "read_only": True, "node": node, "edges": edges}


def debug_graph_edges(adapter: WorldAdapter, query: dict[str, list[str]]) -> dict:
    graph = _debug_graph_snapshot(adapter)
    edge_type = (query.get("type") or [""])[0]
    source = (query.get("source") or [""])[0]
    target = (query.get("target") or [""])[0]
    edges = list(graph.get("edges", []))
    if edge_type:
        edges = [edge for edge in edges if edge.get("type") == edge_type]
    if source:
        try:
            edges = [edge for edge in edges if edge.get("src") == int(source)]
        except ValueError:
            edges = []
    if target:
        try:
            edges = [edge for edge in edges if edge.get("tgt") == int(target)]
        except ValueError:
            edges = []
    offset, limit = _debug_page(query)
    return {"ok": True, "read_only": True, "total": len(edges),
            "offset": offset, "limit": limit, "edges": edges[offset:offset + limit]}


def debug_graph_rules(adapter: WorldAdapter, query: dict[str, list[str]]) -> dict:
    needle = (query.get("name") or [""])[0].lower()
    rules = [_debug_json_safe(rule) for rule in adapter.inner.export_rules()
             if not needle or needle in str(rule.get("name") or "").lower()]
    offset, limit = _debug_page(query)
    return {"ok": True, "read_only": True, "total": len(rules),
            "offset": offset, "limit": limit, "rules": rules[offset:offset + limit]}


# --- mechanical graph queries: Experiment / Run / RunObservation -------------

def _nid_value(nid) -> int:
    return nid.value if hasattr(nid, "value") else nid


def _read_run_log_tail(run_dir, *, max_lines: int = 16) -> str | None:
    """Mechanical read of a child run's stderr/stdout log for display."""
    if not run_dir:
        return None
    try:
        p = Path(str(run_dir)) / "log.txt"
        if not p.is_file():
            return None
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-max_lines:]) if lines else None
    except Exception:  # noqa: BLE001
        return None


def _read_delta_summary(run_dir) -> dict | None:
    if not run_dir:
        return None
    try:
        with open(Path(str(run_dir)) / "delta.json", encoding="utf-8") as f:
            d = json.load(f)
        return {
            "skip_seeds": list(d.get("skip_seeds") or []),
            "add_rules": len(d.get("add_rules") or []),
            "remove_rules": list(d.get("remove_rules") or []),
        }
    except Exception:  # noqa: BLE001
        return None


def _self_concern_for_experiment(adapter: WorldAdapter, eid) -> int | None:
    """Reverse lookup: Experiment <-tested_by- CapabilityAxis -> promoted_self_concern_* key."""
    s = adapter.s
    try:
        axes = list(s.nodes("CapabilityAxis"))
    except Exception:  # noqa: BLE001
        return None
    eid_val = _nid_value(eid)
    for axis in axes:
        if not s.has_node(axis):
            continue
        try:
            tested = list(adapter.inner.neighbours(axis, "tested_by"))
        except Exception:  # noqa: BLE001
            tested = []
        if not any(_nid_value(t) == eid_val for t in tested if s.has_node(t)):
            continue
        keys = list(s.node(axis)["attrs"].get("capability_keys") or [])
        for key in keys:
            sk = str(key)
            if sk.startswith("promoted_self_concern_"):
                try:
                    return int(sk.rsplit("_", 1)[-1])
                except ValueError:
                    pass
    return None


def _experiment_entry(adapter: WorldAdapter, eid, *, include_log: bool = False) -> dict:
    """Shared mechanical fields for list_sessions and session_detail."""
    s = adapter.s
    a = s.node(eid)["attrs"]
    entry = {
        "id": _nid_value(eid),
        "kind": "experiment",
        "game": a.get("game"),
        "status": a.get("status"),
        "hypothesis": a.get("hypothesis"),
        "outcome": a.get("outcome"),
        "conclusion_ready": bool(a.get("conclusion_ready")),
        "error": a.get("error"),
        "frames": None,
        "score": None,
        "run_dir": a.get("run_dir"),
        "run_status": None,
        "self_concern_id": _self_concern_for_experiment(adapter, eid),
        "delta": _read_delta_summary(a.get("run_dir")),
    }
    try:
        run_ids = list(adapter.inner.neighbours(eid, "produced"))
    except Exception:  # noqa: BLE001
        run_ids = []
    for rid in run_ids:
        if not s.has_node(rid):
            continue
        ra = s.node(rid)["attrs"]
        entry["run_status"] = ra.get("status")
        if ra.get("frames") is not None:
            entry["frames"] = ra.get("frames")
        if ra.get("score") is not None:
            entry["score"] = ra.get("score")
        if entry.get("run_dir") is None:
            entry["run_dir"] = ra.get("run_dir")
        if not entry.get("error") and ra.get("error"):
            entry["error"] = ra.get("error")
    if not entry.get("error") and entry.get("status") == "failed":
        tail = _read_run_log_tail(entry.get("run_dir"))
        if tail:
            entry["error"] = tail
    if include_log and entry.get("run_dir"):
        entry["log_tail"] = _read_run_log_tail(entry.get("run_dir"), max_lines=40)
    return entry


def list_sessions(adapter: WorldAdapter) -> list:
    """Every Experiment node (+ its produced Run's frames/score), a pure
    mechanical query. Every raw node id is has_node-guarded (freelist ids
    recycle with no generation counter)."""
    s = adapter.s
    out = []
    with AGENT_LOCK:
        try:
            experiments = list(s.nodes("Experiment"))
        except Exception:  # noqa: BLE001 -- unknown type -> no such nodes
            experiments = []
        for eid in experiments:
            if not s.has_node(eid):
                continue
            out.append(_experiment_entry(adapter, eid))
    return out


def session_detail(adapter: WorldAdapter, id_str: str):
    """(session dict, trace list) for one Experiment id, or None if absent.
    Trace = run -observed-> RunObservation nodes, sorted by frame."""
    s = adapter.s
    try:
        eid = srs.NodeID(int(id_str))
    except (ValueError, TypeError):
        return None
    with AGENT_LOCK:
        if not s.has_node(eid):
            return None
        session = _experiment_entry(adapter, eid, include_log=True)
        trace = []
        try:
            run_ids = list(adapter.inner.neighbours(eid, "produced"))
        except Exception:  # noqa: BLE001
            run_ids = []
        for rid in run_ids:
            if not s.has_node(rid):
                continue
            try:
                obs_ids = list(adapter.inner.neighbours(rid, "observed"))
            except Exception:  # noqa: BLE001
                obs_ids = []
            for oid in obs_ids:
                if not s.has_node(oid):
                    continue
                oa = s.node(oid)["attrs"]
                trace.append({
                    "frame": oa.get("frame"),
                    "action": oa.get("action"),
                    "score": oa.get("score"),
                    "reasoning": oa.get("reasoning"),
                    "self_report": oa.get("self_report"),
                })
        trace.sort(key=lambda t: (t["frame"] is None, t["frame"]))
    return session, trace


# --- rung-4 proposal queries (mechanical graph reads; approval itself is
# domains.proposal_install.install_proposal, called from the HTTP handler) ---

def list_proposals(adapter: WorldAdapter) -> list:
    """Every ExtensionProposal node, joined with its RustExtensionSpec (via
    the `validates` edge) for display fields. Pure mechanical query, newest
    first (numeric id, matching list_sessions' own sort)."""
    s = adapter.s
    out = []
    with AGENT_LOCK:
        try:
            proposals = list(s.nodes("ExtensionProposal"))
        except Exception:  # noqa: BLE001 -- type not present in this seed set
            proposals = []
        for pid in proposals:
            if not s.has_node(pid):
                continue
            a = s.node(pid)["attrs"]
            entry = {
                "id": _nid_value(pid),
                "name": a.get("of"),
                "of": a.get("of"),
                "status": a.get("status"),
                "installed": bool(a.get("installed")),
                "requires_restart": bool(a.get("requires_restart", True)),
                "motivating_residual": None,
                "purpose": None,
                "sandbox_ok": a.get("status") in ("validated", "already_present"),
                "seconds": a.get("seconds"),
                "approved_by": a.get("approved_by"),
                "ts": a.get("ts"),
            }
            try:
                spec_ids = list(adapter.inner.neighbours(pid, "validates"))
            except Exception:  # noqa: BLE001
                spec_ids = []
            for sid in spec_ids:
                if not s.has_node(sid):
                    continue
                sa = s.node(sid)["attrs"]
                entry["motivating_residual"] = sa.get("motivating_residual")
                entry["purpose"] = sa.get("purpose")
                break
            out.append(entry)
    out.sort(key=lambda e: -int(e["id"]))
    return out


def proposal_detail(adapter: WorldAdapter, id_str: str):
    """(proposal dict, spec dict, rendered-diff text) for one ExtensionProposal
    id, or None if absent / not actually an ExtensionProposal. The diff is
    `self_extend_rust.render_spec` re-run read-only against the spec node's
    (possibly lossy -- see proposal_install._spec_dict_from_node) reconstructed
    fields, formatted as readable `--- home ---\\nfragment` blocks so a human
    can review the real Rust before approving."""
    s = adapter.s
    try:
        pid = srs.NodeID(int(id_str))
    except (ValueError, TypeError):
        return None
    with AGENT_LOCK:
        if not s.has_node(pid):
            return None
        pnode = s.node(pid)
        if pnode.get("type") != "ExtensionProposal":
            return None
        a = pnode["attrs"]
        proposal = {
            "id": _nid_value(pid),
            "of": a.get("of"),
            "status": a.get("status"),
            "installed": bool(a.get("installed")),
            "requires_restart": bool(a.get("requires_restart", True)),
            "approved_by": a.get("approved_by"),
            "approved_ts": a.get("approved_ts"),
            "seconds": a.get("seconds"),
            "last_error": a.get("last_error"),
        }
        spec: dict = {}
        diff = ""
        try:
            spec_ids = list(adapter.inner.neighbours(pid, "validates"))
        except Exception:  # noqa: BLE001
            spec_ids = []
        for sid in spec_ids:
            if not s.has_node(sid):
                continue
            sa = s.node(sid)["attrs"]
            spec = {
                "name": sa.get("name"),
                "purpose": sa.get("purpose"),
                "motivating_residual": sa.get("motivating_residual"),
                "why_new": sa.get("why_new"),
                "semantics_kind": sa.get("semantics_kind"),
            }
            try:
                frags = ser.render_spec(_spec_dict_from_node(sa))
                diff = "\n\n".join(f"--- {k} ---\n{v}" for k, v in sorted(frags.items()))
            except Exception as e:  # noqa: BLE001 -- diff is best-effort display only
                diff = f"(diff unavailable: {type(e).__name__}: {e})"
            break
    return proposal, spec, diff


# --- chat-originated self-concerns (Phase 3 continuation): list + human-gated
# promote. A SelfConcern is minted by seeds/conversation_self_concern.json when
# the interlocutor gives a self-directed instruction ("improve/fix your X"); it
# is filed status="noted" and does NOTHING on its own (the daemon's _concern_tick
# only processes StandingConcern{status:"pending"}). These two mechanical
# functions are the HUMAN-IN-THE-LOOP control surface: list what the agent filed,
# and -- only on an explicit human action -- PROMOTE one into the existing,
# already-safety-gated self-improvement pipeline (mint a StandingConcern the
# _concern_tick hook feeds through induce_concern/ground_concern, whose
# downstream adoption is gated by the frozen-core denylist + human approval for
# frozen provenance). No agent decision here; the DECISION to promote is the
# human's, the machinery it hands off to is the agent's own seeded rules.

_EXPERIMENT_GAME = "navigate"   # offline ARC game experiment_dispatch understands
_CONVERSATION_GAME = "conversation"   # the conversation-replay world (scripts/convo_child_run.py)
_PROMOTED_RULE_PREFIXES = (
    "author_experiment_from_residual_",
    "judge_experiment_outcome_",
    "mark_adopt_ready_",
)


def _remove_promoted_rules(adapter: WorldAdapter, key: str) -> int:
    """Tombstone live rules minted for one promoted concern key. Mechanical."""
    if not key:
        return 0
    names = {pfx + str(key) for pfx in _PROMOTED_RULE_PREFIXES}
    removed = 0
    try:
        live = list(adapter.inner.export_rules())
    except Exception:  # noqa: BLE001
        return 0
    for i in sorted(
            (idx for idx, r in enumerate(live)
             if r.get("active") and r.get("name") in names),
            reverse=True):
        try:
            adapter.inner.remove_rule(i)
            removed += 1
        except Exception:  # noqa: BLE001
            pass
    return removed


def _author_rule_has_axis_guards(rule: dict) -> bool:
    """True if an author_experiment rule scopes to its own capability_keys AND
    requires 'test' in residual_predicates (the post-cross-contamination guard)."""
    import json as _json
    try:
        blob = _json.dumps(rule.get("where") or {})
    except Exception:  # noqa: BLE001
        return False
    return "capability_keys" in blob and "residual_predicates" in blob and '"test"' in blob


def _scrub_stale_author_rules(adapter: WorldAdapter) -> int:
    """Tombstone author_experiment rules authored before the axis-scoping guard
    (they mint ARC experiments for comprehend-first concerns). Mechanical."""
    removed = 0
    try:
        live = list(adapter.inner.export_rules())
    except Exception:  # noqa: BLE001
        return 0
    for i in sorted(
            (idx for idx, r in enumerate(live)
             if r.get("active")
             and str(r.get("name") or "").startswith("author_experiment_from_residual_")
             and not _author_rule_has_axis_guards(r)),
            reverse=True):
        try:
            adapter.inner.remove_rule(i)
            removed += 1
        except Exception:  # noqa: BLE001
            pass
    return removed


def _cancel_unscoped_experiments(adapter: WorldAdapter) -> int:
    """Cancel requested/running experiments whose axis lacks 'test' in
    residual_predicates (comprehend-first concerns must not run ARC)."""
    try:
        from domains.experiment_dispatch import cancel_experiment
    except ImportError:
        return 0
    cancelled = 0
    try:
        exps = list(adapter.s.nodes("Experiment"))
    except Exception:  # noqa: BLE001
        return 0
    for exp in exps:
        if not adapter.s.has_node(exp):
            continue
        status = str(adapter.s.node(exp)["attrs"].get("status") or "")
        if status not in ("requested", "running"):
            continue
        axis = None
        try:
            for ax in adapter.s.nodes("CapabilityAxis"):
                if exp in adapter.inner.neighbours(ax, "tested_by"):
                    axis = ax
                    break
        except Exception:  # noqa: BLE001
            axis = None
        if axis is None:
            continue
        preds = adapter.s.node(axis)["attrs"].get("residual_predicates") or []
        if "test" in preds:
            continue
        res = cancel_experiment(adapter, str(_nid_value(exp)))
        if res.get("ok"):
            cancelled += 1
    return cancelled


def _tear_down_promoted_pipeline(adapter: WorldAdapter, sc, runs_dir: str | None = None) -> dict:
    """Clean standing concern / axis / experiment / minted rules for one
    SelfConcern so it can be re-promoted on the current routing policy."""
    out = {"standing_retired": [], "experiment_cancelled": [], "rules_removed": 0}
    key = None
    try:
        for standing in list(adapter.inner.neighbours(sc, "promoted_to")):
            if not adapter.s.has_node(standing):
                continue
            sat = adapter.s.node(standing)["attrs"]
            key = sat.get("name") or key
            adapter.s.set_attr(standing, "status", "retired")
            out["standing_retired"].append(_nid_value(standing))
            try:
                adapter.inner.remove_edge(sc, "promoted_to", standing)
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001
        pass
    if key:
        out["rules_removed"] = _remove_promoted_rules(adapter, key)
        axis = _axis_for_capability_key(adapter, key)
        exp = _experiment_for_axis(adapter, axis)
        if exp is not None:
            try:
                from domains.experiment_dispatch import cancel_experiment
                res = cancel_experiment(adapter, str(_nid_value(exp)))
                if res.get("ok"):
                    out["experiment_cancelled"].append(_nid_value(exp))
            except Exception:  # noqa: BLE001
                pass
        if axis is not None and adapter.s.has_node(axis):
            try:
                adapter.s.set_attr(axis, "status", "retired")
                # A retired axis must stop CLAIMING the capability key: the
                # sd loop's novelty guard (sd_mint_quantum / recognized_duplicate)
                # treats an induced axis with the same capability_keys as the
                # concern already surfaced, so a re-promoted concern could never
                # mint a fresh axis and never be re-tested (tranche 5). The old
                # keys are kept on the record for provenance.
                old_keys = list(adapter.s.node(axis)["attrs"].get("capability_keys") or [])
                adapter.s.set_attr(axis, "retired_capability_keys", old_keys)
                adapter.s.set_attr(axis, "capability_keys",
                                   [f"{k}#retired_{_nid_value(axis)}" for k in old_keys])
            except Exception:  # noqa: BLE001
                pass
    return out


_COMPOSITION_REPLY_HINTS = frozenset({
    "composition", "composed", "consists of", "made of", "made up",
    "regolith", "basalt", "silicate", "lunar crust", "crust is",
    "mantle", "mineral", "oxygen", "silicon", "iron", "nickel",
})


def _replay_reply_mentions_composition(reply: str) -> bool:
    low = str(reply or "").lower()
    return any(h in low for h in _COMPOSITION_REPLY_HINTS)


def _replay_reply_fix_judge(adapter: WorldAdapter) -> int:
    """For comprehend_first reply_fix concerns: replay the flagged turn's parse
    and judge routing quality mechanically (not ARC score). Returns count judged."""
    try:
        from domains import comprehend_text as ct
    except ImportError:
        return 0
    judged = 0
    try:
        standings = list(adapter.s.nodes("StandingConcern"))
    except Exception:  # noqa: BLE001
        return 0
    for standing in standings:
        if not adapter.s.has_node(standing):
            continue
        sat = adapter.s.node(standing)["attrs"]
        if sat.get("pipeline") != "comprehend_first":
            continue
        if sat.get("status") not in ("processed", "pending"):
            continue
        if sat.get("replay_verdict") and not (
                (str(sat.get("about") or "").lower().find("composition") >= 0
                 or "imagine" in str(sat.get("about") or "").lower()
                 or "counterfactual" in str(sat.get("about") or "").lower())
                and sat.get("replay_verdict") in ("pass", "fail")
                and "reply=" not in str(sat.get("replay_note") or "")):
            continue
        if str(sat.get("kind") or "") != "reply_fix":
            continue
        text = None
        try:
            for mid in adapter.inner.neighbours(standing, "about_message"):
                if adapter.s.has_node(mid):
                    text = adapter.s.node(mid)["attrs"].get("text")
                    break
            if text is None:
                sc_id = None
                name = str(sat.get("name") or "")
                if name.startswith("promoted_self_concern_"):
                    sc_id = name[len("promoted_self_concern_"):]
                if sc_id:
                    sc = srs.NodeID(int(sc_id))
                    for mid in adapter.inner.neighbours(sc, "about_message"):
                        if adapter.s.has_node(mid):
                            text = adapter.s.node(mid)["attrs"].get("text")
                            break
        except Exception:  # noqa: BLE001
            text = None
        if not text:
            continue
        comp = ct.comprehend_text(adapter, str(text))
        facts = adapter._topic_facts(comp)
        spec = (comp.dispatch or {}).get("spec")
        know = getattr(spec, "know_concept", None) if spec is not None else None
        bad_know = bool(know and "made of" in str(know).lower())
        topic = facts.get("topic")
        wants_composition = (
            facts.get("aspect") == "made_of"
            or "composition" in str(sat.get("about") or "").lower()
            or "made of" in str(sat.get("about") or "").lower()
        )
        wants_imagine = (
            "imagine" in str(sat.get("about") or "").lower()
            or "counterfactual" in str(sat.get("about") or "").lower()
            or "hypothetical" in str(sat.get("about") or "").lower()
        )
        reply = None
        if wants_composition or wants_imagine:
            try:
                reply = adapter.converse(str(text), speech_act="question")
            except Exception:  # noqa: BLE001
                reply = None
        if wants_imagine:
            routing_ok = (comp.dispatch or {}).get("path") == "imagine_capability"
            content_ok = "imagin" in (reply or "").lower()
        elif wants_composition:
            routing_ok = bool(topic and not bad_know and (facts.get("composition") or not comp.fastpath))
            content_ok = _replay_reply_mentions_composition(reply or "")
        else:
            routing_ok = bool(topic and not bad_know and (facts.get("composition") or not comp.fastpath))
            content_ok = (not wants_composition) or _replay_reply_mentions_composition(reply or "")
        if routing_ok and content_ok:
            adapter.s.set_attr(standing, "replay_verdict", "pass")
            note = f"topic={topic!r}"
            if facts.get("aspect"):
                note += f" aspect={facts.get('aspect')!r}"
            if wants_imagine:
                note += f" path={(comp.dispatch or {}).get('path')!r}"
            if (wants_composition or wants_imagine) and reply:
                note += f" reply={str(reply)[:120]!r}"
            adapter.s.set_attr(standing, "replay_note", note)
        else:
            adapter.s.set_attr(standing, "replay_verdict", "fail")
            adapter.s.set_attr(standing, "replay_note",
                               f"know={know!r} topic={topic!r} composition={facts.get('composition')!r} "
                               f"path={(comp.dispatch or {}).get('path')!r} "
                               f"routing_ok={routing_ok} content_ok={content_ok}")
        judged += 1
    return judged


def _ensure_experiment_world(adapter: WorldAdapter):
    """Mechanical prerequisite for author_experiment_from_residual_* when 'send'
    grounded: the mint rule reads game from agent -knows-> WorldInstance{name}."""
    wi = adapter.ensure_world_instance("Game", _EXPERIMENT_GAME)
    if adapter.s.has_node(wi):
        adapter.s.set_attr(wi, "name", _EXPERIMENT_GAME)
    return wi


def _ensure_conversation_world(adapter: WorldAdapter):
    """The conversation twin of _ensure_experiment_world (same mechanical
    ensure_world_instance precedent): the chat world is ALWAYS present for this
    daemon, so a conversation-replay concern's mint rule (pinned to
    world_type=='ChatWorld' + name=='conversation' by the composer) reads its
    game from a held `agent -knows-> WorldInstance{world_type:'ChatWorld',
    name:'conversation'}` fact. A DISTINCT world_type (not 'Game') keeps the
    two experiment families from cross-binding each other's worlds — the ARC
    mint rules are guarded world_type=='Game'. experiment_dispatch routes
    game=='conversation' to scripts/convo_child_run.py."""
    wi = adapter.ensure_world_instance("ChatWorld", _CONVERSATION_GAME)
    if adapter.s.has_node(wi):
        adapter.s.set_attr(wi, "name", _CONVERSATION_GAME)
    return wi


def _ensure_world_for_relations(adapter: WorldAdapter, relations) -> None:
    """Name-keyed mechanical mapping: which experiment world a promoted
    concern's relation bundle needs held. 'replay' (the conversation-replay
    family) -> the conversation world; else 'test' -> the standing offline-ARC
    world, exactly as before. Reads only the bundle the promote already chose —
    no new decision."""
    heads = {r[0] for r in (relations or []) if r}
    if "replay" in heads:
        _ensure_conversation_world(adapter)
    elif "test" in heads:
        _ensure_experiment_world(adapter)


def _agent_knows_game(adapter: WorldAdapter) -> bool:
    try:
        for wi in adapter.s.nodes("WorldInstance"):
            if not adapter.s.has_node(wi):
                continue
            if adapter.s.node(wi)["attrs"].get("world_type") == "Game":
                return True
    except Exception:  # noqa: BLE001
        pass
    return False


def _axis_for_capability_key(adapter: WorldAdapter, key: str):
    s = adapter.s
    try:
        axes = list(s.nodes("CapabilityAxis"))
    except Exception:  # noqa: BLE001
        return None
    for n in axes:
        if not s.has_node(n):
            continue
        at = s.node(n)["attrs"]
        if list(at.get("capability_keys") or []) == [str(key)]:
            return n
    return None


def _experiment_for_axis(adapter: WorldAdapter, axis):
    if axis is None:
        return None
    try:
        for e in adapter.inner.neighbours(axis, "tested_by"):
            if adapter.s.has_node(e):
                return e
    except Exception:  # noqa: BLE001
        pass
    return None


def _author_rule_present(adapter: WorldAdapter, tag: str) -> bool:
    name = "author_experiment_from_residual_" + str(tag)
    try:
        return any(r.get("name") == name for r in adapter.inner.export_rules())
    except Exception:  # noqa: BLE001
        return False


def _pipeline_stage(adapter: WorldAdapter, standing_status: str, key: str | None):
    """Mechanical stage label + optional blocker message for the UI."""
    if standing_status == "pending":
        return "pending_grounding", None
    if not key:
        return "processed", None
    axis = _axis_for_capability_key(adapter, key)
    has_world = _agent_knows_game(adapter)
    author = _author_rule_present(adapter, key)
    exp = _experiment_for_axis(adapter, axis)
    if axis is None:
        return "processed_no_axis", "standing concern processed but no CapabilityAxis"
    if not author:
        return "processed_no_rules", "composer rules not installed yet"
    if exp is None and not has_world:
        return "blocked_no_world", (
            "author rule needs agent -knows-> Game WorldInstance "
            "(standing world or promote hook supplies navigate)")
    if exp is None:
        return "awaiting_experiment", "rules ready — waiting for Experiment mint"
    exp_status = adapter.s.node(exp)["attrs"].get("status") if adapter.s.has_node(exp) else None
    if exp_status in ("requested", "running"):
        return "experiment_running", None
    if exp_status == "cancelled":
        return "experiment_cancelled", None
    if exp_status:
        return "experiment_" + str(exp_status), None
    return "experiment_minted", None


def _nudge_promoted_experiments(adapter: WorldAdapter, *, max_ticks: int = 12) -> int:
    """For processed promoted concerns whose axis lacks tested_by: ensure dispatch
    prerequisites and tick so the agent's own mint rules can fire. Returns extra
    ticks run (0 if nothing to nudge). Mechanical host I/O only."""
    s = adapter.s
    try:
        standing = list(s.nodes("StandingConcern"))
    except Exception:  # noqa: BLE001
        return 0
    keys = []
    relations_by_key = {}
    for n in standing:
        if not s.has_node(n):
            continue
        at = s.node(n)["attrs"]
        name = at.get("name") or ""
        if name.startswith("promoted_self_concern_") and at.get("status") == "processed":
            if not _axis_wants_experiment(adapter, name):
                continue
            keys.append(name)
            relations_by_key[name] = at.get("relations") or []
    if not keys:
        return 0
    need_keys = []
    for key in keys:
        axis = _axis_for_capability_key(adapter, key)
        if axis is not None and _experiment_for_axis(adapter, axis) is None:
            need_keys.append(key)
    if not need_keys:
        return 0
    for key in need_keys:
        _ensure_world_for_relations(adapter, relations_by_key.get(key))
    ran = 0
    for _ in range(max_ticks):
        adapter.tick()
        ran += 1
        pending = False
        for key in keys:
            axis = _axis_for_capability_key(adapter, key)
            if axis is not None and _experiment_for_axis(adapter, axis) is None:
                pending = True
                break
        if not pending:
            break
    return ran


def list_self_improvement(adapter: WorldAdapter) -> dict:
    """Mechanical read of the promoted-concern -> experiment pipeline."""
    items = []
    with AGENT_LOCK:
        has_world = _agent_knows_game(adapter)
        try:
            scs = list(adapter.s.nodes("SelfConcern"))
        except Exception:  # noqa: BLE001
            scs = []
        for sc in scs:
            if not adapter.s.has_node(sc):
                continue
            a = adapter.s.node(sc)["attrs"]
            if a.get("status") != "promoted":
                continue
            promoted_to = []
            try:
                promoted_to = [_nid_value(n) for n in adapter.inner.neighbours(sc, "promoted_to")]
            except Exception:  # noqa: BLE001
                pass
            standing_id = None
            if promoted_to:
                active = []
                for pid in promoted_to:
                    sid = srs.NodeID(int(pid))
                    if not adapter.s.has_node(sid):
                        continue
                    if adapter.s.node(sid)["attrs"].get("status") == "retired":
                        continue
                    active.append(int(pid))
                pick = (active or [int(x) for x in promoted_to])
                standing_id = str(max(pick)) if pick else None
            standing_status = None
            standing_name = None
            standing_about = None
            standing_pipeline = None
            replay_verdict = None
            replay_note = None
            if standing_id is not None:
                sid = srs.NodeID(int(standing_id))
                if adapter.s.has_node(sid):
                    sat = adapter.s.node(sid)["attrs"]
                    standing_status = sat.get("status")
                    standing_name = sat.get("name")
                    standing_about = sat.get("about")
                    standing_pipeline = sat.get("pipeline")
                    replay_verdict = sat.get("replay_verdict")
                    replay_note = sat.get("replay_note")
            key = standing_name if standing_name else None
            stage, blocker = _pipeline_stage(adapter, standing_status or "", key)
            if standing_pipeline == "comprehend_first" and not _standing_relations_include_test(adapter, key or ""):
                if standing_status == "pending":
                    stage, blocker = "pending_grounding", None
                elif replay_verdict == "pass":
                    stage, blocker = "replay_passed", None
                elif replay_verdict == "fail":
                    stage, blocker = "replay_failed", replay_note
                elif stage.startswith("experiment") or stage in ("blocked_no_world", "awaiting_experiment", "experiment_cancelled"):
                    stage, blocker = "comprehend_first", None
                elif stage == "processed_no_rules":
                    stage, blocker = "installing_rules", None
            axis = _axis_for_capability_key(adapter, key) if key else None
            exp = _experiment_for_axis(adapter, axis)
            exp_error = None
            exp_outcome = None
            if exp is not None and adapter.s.has_node(exp):
                eat = adapter.s.node(exp)["attrs"]
                exp_error = eat.get("error")
                exp_outcome = eat.get("outcome")
                if not exp_error and eat.get("status") == "failed":
                    exp_error = _read_run_log_tail(eat.get("run_dir"))
            entry = {
                "self_concern_id": _nid_value(sc),
                "standing_concern_id": standing_id,
                "standing_status": standing_status,
                "about": standing_about or a.get("content"),
                "kind": a.get("kind"),
                "pipeline": standing_pipeline,
                "replay_verdict": replay_verdict,
                "replay_note": replay_note,
                "capability_key": key,
                "capability_axis_id": _nid_value(axis) if axis is not None else None,
                "author_rule": ("author_experiment_from_residual_" + key) if key and _author_rule_present(adapter, key) else None,
                "stage": stage,
                "blocker": blocker,
                "experiment_id": _nid_value(exp) if exp is not None else None,
                "experiment_status": (adapter.s.node(exp)["attrs"].get("status")
                                      if exp is not None and adapter.s.has_node(exp) else None),
                "experiment_outcome": exp_outcome,
                "experiment_error": (str(exp_error)[:500] if exp_error else None),
            }
            items.append(entry)
        try:
            exp_count = len(list(adapter.s.nodes("Experiment")))
        except Exception:  # noqa: BLE001
            exp_count = 0
    items.sort(key=lambda e: -int(e["self_concern_id"]))
    return {"items": items, "has_world": has_world, "experiment_count": exp_count,
            "experiment_game": _EXPERIMENT_GAME}


def _concern_title(attrs: dict, from_text: str | None) -> str:
    """Human-readable one-line label for a SelfConcern (mechanical read only)."""
    source = str(attrs.get("source") or "")
    kind = str(attrs.get("kind") or "")
    content = str(attrs.get("content") or "").strip()
    predicate = str(attrs.get("predicate") or "").strip()
    if source == "conversation" and predicate:
        return f"{predicate} {content}".strip() if content else predicate
    if kind == "knowledge":
        return f"Knowledge gap: {content}" if content else "Knowledge gap"
    if kind == "self_account":
        return f"Self-account gap: {content}" if content else "Self-account gap"
    if kind == "reported":
        return "Reported limitation"
    if kind == "reply_fix":
        return "Reply fix"
    if kind == "capability":
        return f"Capability gap: {content}" if content else "Capability gap"
    if content:
        return content
    if from_text:
        return truncate(from_text, 80) if len(from_text) > 80 else from_text
    return "Self-concern"


def _concern_detail(attrs: dict, from_text: str | None) -> str | None:
    """Longer explanatory text — the original message or filed content."""
    if from_text:
        return str(from_text)
    content = str(attrs.get("content") or "").strip()
    return content or None


def truncate(s: str, n: int) -> str:
    s = str(s or "")
    return s if len(s) <= n else s[: n - 1] + "…"


def _self_concern_dict(adapter: WorldAdapter, sc) -> dict:
    a = adapter.s.node(sc)["attrs"]
    from_text = None
    try:
        for m in adapter.inner.neighbours(sc, "about_message"):
            if adapter.s.has_node(m):
                from_text = adapter.s.node(m)["attrs"].get("text")
                break
    except Exception:  # noqa: BLE001
        pass
    promoted_to = []
    try:
        promoted_to = [_nid_value(n) for n in adapter.inner.neighbours(sc, "promoted_to")]
    except Exception:  # noqa: BLE001
        pass
    title = _concern_title(a, from_text)
    detail = _concern_detail(a, from_text)
    return {
        "id": _nid_value(sc),
        "status": a.get("status"),
        "predicate": a.get("predicate"),
        "content": a.get("content"),
        "kind": a.get("kind"),
        "source": a.get("source"),
        "title": title,
        "detail": detail,
        "from_message": from_text,
        "promoted_to": promoted_to,
    }


def embodied_learning_status(adapter: WorldAdapter) -> dict:
    """Read the embodied learning graph without ticking or interpreting it."""
    native, sub = adapter.inner, adapter.s

    def node_projection(node) -> dict:
        return {
            "id": _nid_value(node),
            "type": sub.node(node)["type"],
            "attrs": _debug_json_safe(sub.node(node)["attrs"]),
        }

    def neighbours(source, edge_type) -> list[dict]:
        return [node_projection(node)
                for node in native.neighbours(source, edge_type)
                if native.has_node(node)]

    sessions = []
    for session in sub.nodes("EmbodiedLearningSession"):
        if not native.has_node(session):
            continue
        sessions.append({
            **node_projection(session),
            "goals": neighbours(session, "has_active_embodied_goal"),
            "frontiers": neighbours(session, "has_developmental_frontier"),
            "plans": neighbours(session, "has_learning_plan"),
            "selected_steps": neighbours(
                session, "has_selected_learning_plan_step"),
            "motor_programs": neighbours(
                session, "has_selected_embodied_motor_program"),
            "counterfactual_trials": neighbours(
                session, "has_counterfactual_embodied_trial"),
            "external_requests": neighbours(
                session, "has_grounded_external_trial_request"),
            "external_evidence": neighbours(
                session, "has_grounded_external_trial_evidence"),
        })
    missions = [node_projection(node)
                for node in sub.nodes("EmbodiedInstructionGoalProposal")
                if native.has_node(node)]
    return {
        "ok": True,
        "read_only": True,
        "requires_cognition": False,
        "sessions": sessions,
        "missions": missions,
    }


def list_self_concerns(adapter: WorldAdapter) -> list:
    """Every chat-originated SelfConcern node (mechanical query, newest first)."""
    out = []
    with AGENT_LOCK:
        try:
            scs = list(adapter.s.nodes("SelfConcern"))
        except Exception:  # noqa: BLE001 -- type not present in this seed set
            scs = []
        for sc in scs:
            if adapter.s.has_node(sc):
                d = _self_concern_dict(adapter, sc)
                if d.get("status") == "retired":
                    continue
                out.append(d)
    out.sort(key=lambda e: -int(e["id"]))
    return out


def _content_suggests_experiment(content_words: list[str]) -> bool:
    """Mechanical keyword read on the concern text — NOT an agent decision.
    When the human's note names acting/seed/variant ablation, include experiment
    cues; otherwise a reply_fix/knowledge concern stays comprehension-first."""
    signals = frozenset({
        "grammar", "acting", "navigation", "seed", "seeds", "variant", "variants",
        "ablation", "ablate", "skip", "rule", "rules", "arc", "game", "world",
        # RESIDUAL-CLOSURE wave: held-knob vocabulary — a concern naming a
        # threshold/knob belief is experimentable via the knob_edit variation
        # family (seeds/variation_ops.json v1.1.0). Same mechanical keyword
        # read as the rest of this set, NOT an agent decision.
        "threshold", "thresholds", "knob", "knobs", "aperture", "calibrate",
        "recalibrate",
        # COMPOSER-CAPABILITY wave: a concern naming interlocutor trust/
        # reliability tracking or person-shape vocabulary is experimentable
        # via the datum_feedback_rule / shape_mint variation families
        # (seeds/variation_ops.json v1.3.0). Same mechanical keyword read.
        "reliability", "trust", "trustworthiness", "shape", "shapes",
        "persona", "profile",
    })
    return any(w in signals for w in content_words)


def _standing_relations_include_test(adapter: WorldAdapter, standing_name: str) -> bool:
    try:
        for n in adapter.s.nodes("StandingConcern"):
            if not adapter.s.has_node(n):
                continue
            at = adapter.s.node(n)["attrs"]
            if at.get("name") == standing_name:
                rels = at.get("relations") or []
                return any(r and r[0] == "test" for r in rels)
    except Exception:  # noqa: BLE001
        pass
    return False


def _axis_wants_experiment(adapter: WorldAdapter, key: str) -> bool:
    """Mechanical: only nudge author rules when this concern's relations include test."""
    if _standing_relations_include_test(adapter, key):
        return True
    axis = _axis_for_capability_key(adapter, key)
    if axis is None:
        return False
    preds = adapter.s.node(axis)["attrs"].get("residual_predicates") or []
    return "test" in preds


_PROMOTE_CUE_WORDS = 12


def _promote_relations_for_concern(kind: str, content_words: list, tag: str) -> tuple[list, str]:
    """Pick StandingConcern relations from concern kind + content.

    Default for language gaps (reply_fix, knowledge, self_account): comprehend
    first — route to the comprehension composer, no forced ARC episode.

    Include test/… only when the concern genuinely needs an empirical
    self-experiment (self_improvement kind, or content words that name
    acting/seed/rule/world ablation). The agent CAN still mint an Experiment
    later if a concern's relations include test; it is never forced for a
    moon-routing reply fix.

    Which experiment WORLD: a conversation-behaviour concern (reply_fix /
    knowledge / instruction) that wants an experiment gets the CONVERSATION
    bundle — test/replay/send/judge/adopt — grounded to the conversation-replay
    world (seeds/conversation_experiment.json's 'replay' cue; the composer's
    conversation branch pins the mint rule to the 'conversation' WorldInstance
    and authors a targeted reply-rule ablation delta; scripts/convo_child_run.py
    replays the recorded corpus, judged flagged-turn-fixed minus regressions).
    A self_improvement concern keeps the ARC bundle (vary/gradient) unchanged.

    Wave 5: an `instruction` gap ALWAYS wants the conversation experiment —
    its content names an unrouted verb, and the cue-set-edit variation family
    (seeds/variation_ops.json + reflective_faculty._compose_cue_variant) can
    construct + validate a route for it via replay; comprehend-first has
    nothing to do with an unrouted verb (the parse already succeeded — the
    gap IS the missing route).

    SELF-OPTIMISATION (Wave: 2026-07-10): a `performance` or `comprehension`
    gap (seeds/comprehension_health.json's note_comprehension_latency_gap /
    note_recurring_speech_act_divergence — the agent noticing its OWN
    comprehension process is slow or systematically disagreeing with itself)
    ALWAYS wants the conversation experiment too, and gets the SAME
    test/replay/send/judge/adopt bundle as reply_fix/knowledge/instruction —
    the composer's existing reply-ablation variant (seeds/variation_ops.json)
    is a genuine efficiency lever (fewer reply rules firing per turn), and
    domains/experiment_dispatch.py._stamp_performance_baseline +
    seeds/self_optimisation.json's judge_performance_experiment_outcome give
    it an EFFICIENCY verdict on top of the unchanged correctness one."""
    if kind == "code_write":
        # CODE-CURRICULUM: a code_write concern is a CODE-4 composition
        # request, never an ARC/conversation experiment and never the
        # comprehend-first path -- _concern_tick routes a StandingConcern of
        # this kind DIRECTLY into domains.code_write_growth.work_on_code_write_gap
        # (see _process_code_write_standing below). These relations are
        # descriptive graph data (never read by induce_concern for this
        # kind), kept in the same relation-cue shape as every other pipeline
        # for uniformity of the StandingConcern record.
        relations = [["compose", "SHAPE", "from", "PREDICATION"]]
        for w in content_words[:4]:
            relations.append([w, "TARGET", "of", "WRITE"])
        return relations, "code_write"
    if kind == "prog_read":
        # ARC6 A25 (measured live): a prog_read concern fell through to the
        # comprehend_first default below, whose generic induce_concern/
        # ground_concern composer minted an INERT, misleadingly-named rule
        # (comprehend_describe_directive_<tag>, matched on a literal Mention
        # text 'describe' about a Scene -- structurally unrelated to
        # extending a program-reading frame) and reported it as "grounded:
        # true" with no record anywhere. _concern_tick now routes a
        # StandingConcern of this kind DIRECTLY into
        # domains.prog_read_growth.work_on_prog_read_gap (see
        # _process_prog_read_standing below), the code_write precedent
        # applied to the sibling gap kind. These relations are descriptive
        # graph data only (never read by induce_concern for this kind any
        # more), kept in the same relation-cue shape as every other pipeline
        # for uniformity of the StandingConcern record.
        relations = [["extend", "FRAME", "from", "BLOCKER"]]
        for w in content_words[:4]:
            relations.append([w, "TARGET", "of", "READ"])
        return relations, "prog_read"
    want_experiment = (kind in ("self_improvement", "instruction", "performance", "comprehension")
                       or _content_suggests_experiment(content_words))
    if want_experiment:
        # RESIDUAL-CLOSURE wave: a 'reported' concern (gap_awareness's
        # explicit-report surface — the interlocutor NAMED a deficiency over
        # NL) that wants an experiment is a CONVERSATION-behaviour concern by
        # construction (the report is about how the agent read/replied), so it
        # takes the same conversation replay bundle a reply_fix concern gets —
        # this is what lets a reported held-threshold gap reach the knob_edit
        # family + the replay world instead of a meaningless ARC episode.
        if kind in ("reply_fix", "knowledge", "instruction", "performance",
                    "comprehension", "reported"):
            relations = [
                ["test", "HYPOTHESIS", "about", tag],
                ["replay", "TURN", "in", "CONVERSATION"],
                ["send", "VARIANT", "to", "WORLD"],
                ["judge", "TRIAL", "by", "OUTCOME"],
                ["adopt", "WINNER", "as", "SELF"],
            ]
            # Up to _PROMOTE_CUE_WORDS content words (was 4): every word is
            # TARGET text the held RelationCue lexicon grounds, so truncation
            # silently dropped the cues that make other variation families
            # applicable ("...profile shape", "...threshold is too low";
            # tranche 4 measurement). Conversation bundle only.
            for w in content_words[:_PROMOTE_CUE_WORDS]:
                relations.append([w, "TARGET", "of", "SELF"])
            return relations, "experiment"
        relations = [
            ["test", "HYPOTHESIS", "about", tag],
            ["vary", "SEED", "of", tag],
            ["send", "VARIANT", "to", "WORLD"],
            ["judge", "TRIAL", "by", "OUTCOME"],
            ["gradient", "VARIANT", "of", "ACTING"],
            ["adopt", "WINNER", "as", "SELF"],
        ]
        for w in content_words[:4]:
            relations.append([w, "TARGET", "of", "SELF"])
        return relations, "experiment"
    relations = [["comprehend", "DIRECTIVE", "mint", "GOAL"]]
    for w in content_words[:4]:
        relations.append([w, "TARGET", "of", "SELF"])
    return relations, "comprehend_first"


def promote_self_concern(adapter: WorldAdapter, id_str: str) -> dict:
    """HUMAN-GATED promotion: turn a noted SelfConcern into a live
    StandingConcern{status:"pending"} that the _concern_tick hook feeds through
    the agent's existing self-improvement machinery. Relation cues are chosen
    from concern kind + content: reply_fix/knowledge defaults to comprehend-first
    (no forced ARC); self_improvement or content that names acting/seed ablation
    gets the full test/vary/send/judge bundle. The agent CAN still mint an
    Experiment later when relations include test; it is never forced for a
    moon-routing reply fix. Idempotent: a SelfConcern already promoted is not
    re-promoted."""
    try:
        sc = srs.NodeID(int(id_str))
    except (ValueError, TypeError):
        return {"ok": False, "error": "bad id"}
    with AGENT_LOCK:
        if not adapter.s.has_node(sc) or adapter.s.node(sc).get("type") != "SelfConcern":
            return {"ok": False, "error": "not found"}
        a = adapter.s.node(sc)["attrs"]
        if a.get("status") == "promoted":
            return {"ok": False, "error": "already promoted"}
        content = (a.get("content") or a.get("predicate") or "self")
        kind = str(a.get("kind") or "self_improvement")
        _STOP = {"your", "the", "a", "an", "of", "to", "my", "me", "it", "this",
                 "that", "for", "and", "on", "in", "with", "you", "yourself", "at"}
        content_words = [w.lower().strip(".,;:!?'\"") for w in str(content).split()]
        content_words = [w for w in content_words if len(w) > 2 and w not in _STOP]
        tag = (content_words[0].upper() if content_words else "SELF")[:24]
        relations, pipeline = _promote_relations_for_concern(kind, content_words, tag)
        standing = adapter.s.add_node("StandingConcern", {
            "name": f"promoted_self_concern_{_nid_value(sc)}",
            "relations": relations,
            "status": "pending",
            "source": "conversation_promoted",
            "about": str(content),
            "kind": kind,
            "pipeline": pipeline,
        })
        adapter.inner.add_edge_unchecked(sc, "promoted_to", standing)
        # Preserve the flagged turn link for reply_fix (replay context for humans).
        try:
            for mid in adapter.inner.neighbours(sc, "about_message"):
                if adapter.s.has_node(mid):
                    adapter.inner.add_edge_unchecked(standing, "about_message", mid)
                    break
        except Exception:  # noqa: BLE001
            pass
        # REQUESTER PROVENANCE (Wave: interlocutor-as-modeled-participant,
        # task 2): a knowledge-gap SelfConcern (note_unresolved_topic_gap)
        # carries `about_goal` -> the answer_topic Goal that gap came from;
        # that Goal carries `wanted_by` -> the Party who asked (task 2's
        # mint-time write). A mechanical readback of an EXISTING edge chain —
        # copying an already-decided fact onto the StandingConcern so
        # `_run_self_improvement_status` can render "requested by <name>"
        # without re-deriving it every read. Best-effort: most concerns carry
        # no such chain (a capability gap, an explicit report) and stay
        # byte-unchanged.
        try:
            for g in adapter.inner.neighbours(sc, "about_goal"):
                for p in adapter.inner.neighbours(g, "wanted_by"):
                    nm = adapter.s.node(p)["attrs"].get("name")
                    if nm:
                        adapter.s.set_attr(standing, "requested_by", nm)
                    break
                break
        except Exception:  # noqa: BLE001
            pass
        adapter.s.set_attr(sc, "status", "promoted")
        _ensure_world_for_relations(adapter, relations)
    return {"ok": True, "self_concern": _nid_value(sc),
            "standing_concern": _nid_value(standing), "about": str(content),
            "target_words": content_words[:4], "kind": kind, "pipeline": pipeline}


def repromote_self_concern(adapter: WorldAdapter, id_str: str,
                           runs_dir: str | None = None) -> dict:
    """HUMAN-GATED reset + re-promote for a concern stuck on a stale pipeline
    (e.g. an old ARC bundle from before comprehend_first routing). Tears down
    the prior StandingConcern, minted rules, and any linked Experiment, resets
    the SelfConcern to noted, then promotes again with current routing policy."""
    try:
        sc = srs.NodeID(int(id_str))
    except (ValueError, TypeError):
        return {"ok": False, "error": "bad id"}
    with AGENT_LOCK:
        if not adapter.s.has_node(sc) or adapter.s.node(sc).get("type") != "SelfConcern":
            return {"ok": False, "error": "not found"}
        a = adapter.s.node(sc)["attrs"]
        if a.get("status") != "promoted":
            return {"ok": False, "error": "not promoted — use promote instead"}
        teardown = _tear_down_promoted_pipeline(adapter, sc, runs_dir=runs_dir)
        adapter.s.set_attr(sc, "retry_requested", 0)   # a human retry supersedes a pending graph request
        adapter.s.set_attr(sc, "status", "noted")
        result = promote_self_concern(adapter, id_str)
        if result.get("ok"):
            result["teardown"] = teardown
            result["repromoted"] = True
        return result


def restart_experiment_session(adapter: WorldAdapter, id_str: str, runs_dir: str) -> dict:
    """Human-initiated experiment retry: re-queue + immediate dispatch attempt."""
    try:
        from domains.experiment_dispatch import restart_experiment, scan_and_dispatch
    except ImportError as e:
        return {"ok": False, "error": str(e)}
    with AGENT_LOCK:
        result = restart_experiment(adapter, id_str)
        if not result.get("ok"):
            return result
        _ensure_experiment_world(adapter)
        touched = scan_and_dispatch(adapter, runs_dir)
        result["dispatched"] = bool(touched)
        if touched:
            result["run_dir"] = touched[-1]
    return result


# --- auto-approve hook (opt-in via the AutoApprovePolicy node; mirrors the
# other soft hooks exactly, with one deliberate difference: a qualifying
# proposal triggers a REAL cargo+maturin build via domains.proposal_install.
# install_proposal, which can take tens of seconds to minutes. Everything in
# this daemon already serialises through AGENT_LOCK (tick_loop calls every
# hook, this one included, from inside `with AGENT_LOCK:`), so there is no
# way to run the build "off to the side" of chat without breaking the
# single-owner-substrate invariant this whole file is built on -- the
# tradeoff is made explicit instead: this hook is rare by design (--auto-
# approve-every defaults to 200 ticks, matching this module's own guidance
# to keep it infrequent) and LOGS LOUDLY before it does anything that might
# block, so a human reading the daemon log knows exactly why chat just
# stalled. The DECISION of which proposal (if any) qualifies is entirely
# domains.auto_approve.scan_and_auto_approve's mechanical policy evaluation
# (default OFF) -- this hook only calls it and logs its per-proposal
# decisions, never a decision itself.

def _auto_approve_tick(adapter: WorldAdapter) -> None:
    try:
        policy = auto_appr.get_policy(adapter)
        if not policy or not policy.get("enabled") or policy.get("paused_until_restart"):
            return  # cheap, no build possible -- skip the loud log entirely
        log("auto-approve: policy enabled -- scanning validated proposals "
            "(a qualifying one triggers a REAL cargo+maturin build, which "
            "blocks AGENT_LOCK -- and therefore chat/tick -- for up to "
            "tens of seconds)")
        results = auto_appr.scan_and_auto_approve(adapter, now_ts=time.time(), log=log)
        for r in results:
            log(f"auto-approve: {r['action']} {r.get('name')} (id={r['id']}): {r.get('reason')}")
    except Exception as e:  # noqa: BLE001 -- never let an auto-approve hiccup kill the tick loop
        log(f"auto-approve error (continuing): {e}")


# --- dispatch hook (best-effort; the module is built in parallel) ------------

def _dispatch_tick(adapter: WorldAdapter, runs_dir: str) -> None:
    try:
        from domains.experiment_dispatch import scan_and_dispatch
    except ImportError:
        return
    try:
        scan_and_dispatch(adapter, runs_dir)
    except Exception as e:  # noqa: BLE001 -- never let a dispatch hiccup kill the tick loop
        log(f"dispatch error (continuing): {e}")


# --- fetch hook (best-effort; mirrors the dispatch hook exactly) -------------
# The DECISION to fetch a URL is the agent's (it mints FetchRequest nodes via
# its own rules); this only notices a requested one, does the I/O, and
# ingests the result — see domains/fetch_dispatch.py.

def _fetch_tick(adapter: WorldAdapter) -> None:
    try:
        from domains.fetch_dispatch import scan_and_fetch
    except ImportError:
        return
    try:
        scan_and_fetch(adapter, log=log)
    except Exception as e:  # noqa: BLE001 -- never let a fetch hiccup kill the tick loop
        log(f"fetch error (continuing): {e}")


# --- search hook (best-effort; mirrors the fetch hook exactly) --------------
# The DECISION to search a topic is the agent's (the topic_search seed rule mints
# SearchRequest nodes from a routed-topic goal); this only notices a requested
# one, resolves + grounds it over HTTPS, and persists the result — see
# domains/fetch_dispatch.py::scan_and_search + domains/topic_grounding.py.

_MAX_PENDING_SEARCH_IO = 16

def _search_tick(adapter: WorldAdapter, state: "DaemonState | None" = None):
    try:
        from domains.fetch_dispatch import scan_and_search, scan_and_sync_ground
    except ImportError:
        return
    try:
        if state is not None:
            source = getattr(state, "active_host_action_source", None)
            source_id = (int(source.value) if hasattr(source, "value")
                         else int(source) if source is not None else None)
            if source_id is not None:
                source_node = srs.NodeID(source_id)
                if (adapter.inner.has_node(source_node)
                        and adapter.s.node(source_node)["type"] ==
                        "CausalRetrievalRequest"):
                    stage = _start_causal_retrieval_io(
                        adapter, state, source_node)
                    if stage["jobs"]:
                        return {"host_action_pending": True,
                                "jobs": stage["jobs"]}
                    if stage["deferred"]:
                        return {"host_action_deferred": True}
                    return None
            ground_stage = _start_ground_request_io(adapter, state)
            if ground_stage["jobs"]:
                return {"host_action_pending": True,
                        "jobs": ground_stage["jobs"]}
            if ground_stage["deferred"]:
                return {"host_action_deferred": True}
            source = getattr(state, "active_host_action_source", None)
            source_id = (int(source.value) if hasattr(source, "value")
                         else int(source) if source is not None else None)
            if source_id is not None:
                source_node = srs.NodeID(source_id)
                if (adapter.inner.has_node(source_node)
                        and adapter.s.node(source_node)["type"] == "GroundRequest"):
                    return None
            stage = _start_search_candidate_io(adapter, state)
            if stage["jobs"]:
                return {"host_action_pending": True, "jobs": stage["jobs"]}
            if stage["deferred"]:
                return {"host_action_deferred": True}
            return None
        # The direct WorldAdapter path retains its synchronous contract.
        # Specific grounding precedes generic search and successful specific
        # evidence supersedes the broad fallback.
        scan_and_sync_ground(adapter, log=log)
        scan_and_search(adapter, log=log)
    except Exception as e:  # noqa: BLE001 -- never let a search hiccup kill the tick loop
        log(f"search error (continuing): {e}")


def _start_causal_retrieval_io(adapter: WorldAdapter, state: "DaemonState",
                               request) -> dict:
    """Run typed causal retrieval in a worker from an immutable request copy."""
    from domains.causal_retrieval import retrieve_causal_candidate_payloads

    native = adapter.inner
    if not native.has_node(request):
        return {"jobs": [], "deferred": False}
    attrs = dict(adapter.s.node(request)["attrs"])
    if (attrs.get("schema") != "causal_retrieval_request.v1"
            or attrs.get("status") != "requested"):
        return {"jobs": [], "deferred": False}
    topic = str(attrs.get("topic") or "").strip()
    entity_id = str(attrs.get("topic_entity_id") or "").strip()
    if not topic:
        native.set_attr(request, "status", "failed")
        native.set_attr(request, "error", "empty causal topic")
        return {"jobs": [], "deferred": False}
    if not entity_id:
        native.set_attr(request, "status", "failed")
        native.set_attr(request, "error", "causal topic has no bound external identity")
        return {"jobs": [], "deferred": False}
    pending_count = sum(len(item["jobs"])
                        for item in state.pending_search_host_actions.values())
    if pending_count >= _MAX_PENDING_SEARCH_IO:
        return {"jobs": [], "deferred": True}
    token = f"causal:{int(request.value)}:{time.monotonic_ns()}"
    native.set_attr(request, "status", "running")
    native.set_attr(request, "causal_io_token", token)
    try:
        future = state.search_io_executor.submit(
            retrieve_causal_candidate_payloads, topic,
            entity_id=entity_id, timeout=8)
    except Exception as exc:  # noqa: BLE001 -- preserve failure in request data
        native.set_attr(request, "status", "failed")
        native.set_attr(request, "causal_io_token", None)
        native.set_attr(request, "error", f"{type(exc).__name__}: {exc}")
        return {"jobs": [], "deferred": False}
    future.add_done_callback(lambda _f, wake=state.dirty: wake.set())
    return {"jobs": [{"kind": "causal", "request_id": int(request.value),
                      "token": token, "query": topic, "future": future}],
            "deferred": False}


def _start_ground_request_io(adapter: WorldAdapter, state: "DaemonState") -> dict:
    """Try local grounding on-owner, then stage remote retrieval as data-only I/O."""
    from domains import topic_grounding as tg

    active_source = getattr(state, "active_host_action_source", None)
    source_id = (int(active_source.value) if hasattr(active_source, "value")
                 else int(active_source) if active_source is not None else None)
    source_node = srs.NodeID(source_id) if source_id is not None else None
    source_kind = (adapter.s.node(source_node)["type"]
                   if source_node is not None and adapter.inner.has_node(source_node)
                   else None)
    source_query = (str(adapter.s.node(source_node)["attrs"].get("query") or "").strip()
                    if source_node is not None and adapter.inner.has_node(source_node)
                    else "")

    pending_count = sum(len(item["jobs"])
                        for item in state.pending_search_host_actions.values())
    capacity = max(0, _MAX_PENDING_SEARCH_IO - pending_count)
    jobs = []
    eligible = []
    for req in list(adapter.s.nodes("GroundRequest")):
        if not adapter.inner.has_node(req):
            continue
        attrs = dict(adapter.s.node(req)["attrs"])
        if source_kind == "GroundRequest" and int(req.value) != source_id:
            continue
        if source_kind == "SearchRequest" and str(attrs.get("query") or "").strip() != source_query:
            continue
        if attrs.get("status") == "running" and attrs.get("ground_io_token"):
            eligible.append(req)
            continue
        if attrs.get("status") != "requested":
            continue
        eligible.append(req)
        query = str(attrs.get("query") or "").strip()
        aspect = str(attrs.get("aspect") or "").strip() or None
        if not query:
            adapter.inner.set_attr(req, "status", "failed")
            adapter.inner.set_attr(req, "error", "empty query")
            continue
        try:
            local = tg.ground_local_attempt(adapter, query, aspect)
        except Exception as exc:  # noqa: BLE001 -- preserve honest fallback
            adapter.inner.set_attr(req, "status", "failed")
            adapter.inner.set_attr(req, "error", f"{type(exc).__name__}: {exc}")
            continue
        if local["settled"]:
            answer = local.get("answer")
            adapter.inner.set_attr(req, "status", "done" if answer else "failed")
            if answer:
                adapter.inner.set_attr(req, "answer", str(answer)[:4000])
                for search in adapter.s.nodes("SearchRequest"):
                    if (adapter.inner.has_node(search)
                            and adapter.s.node(search)["attrs"].get("status")
                            in ("requested", "running", "io_pending")
                            and str(adapter.s.node(search)["attrs"].get("query") or "").strip().lower()
                            == query.lower()):
                        adapter.inner.set_attr(search, "status", "superseded")
                        adapter.inner.add_edge_unchecked(search, "superseded_by", req)
            else:
                adapter.inner.set_attr(req, "error", "no answer")
            continue
        if len(jobs) >= capacity:
            continue
        token = f"ground:{int(req.value)}:{time.monotonic_ns()}"
        adapter.inner.set_attr(req, "status", "running")
        adapter.inner.set_attr(req, "ground_io_token", token)
        try:
            future = state.search_io_executor.submit(
                tg.retrieve_ground_payload, query, aspect, timeout=8)
        except Exception as exc:  # noqa: BLE001 -- expose submit failure
            adapter.inner.set_attr(req, "status", "failed")
            adapter.inner.set_attr(req, "ground_io_token", None)
            adapter.inner.set_attr(req, "error", f"{type(exc).__name__}: {exc}")
            continue
        future.add_done_callback(lambda _f, wake=state.dirty: wake.set())
        jobs.append({"kind": "ground", "request_id": int(req.value),
                     "token": token, "query": query, "aspect": aspect,
                     "future": future})
    still_pending = any(
        adapter.inner.has_node(req)
        and adapter.s.node(req)["attrs"].get("status") in ("requested", "running")
        for req in eligible)
    return {"jobs": jobs, "deferred": bool(still_pending and not jobs)}


def _start_search_candidate_io(adapter: WorldAdapter, state: "DaemonState") -> dict:
    """Submit immutable SearchRequest snapshots; workers never touch the graph."""
    from domains.topic_grounding import retrieve_search_candidate_payloads

    active_source = getattr(state, "active_host_action_source", None)
    source_id = (int(active_source.value) if hasattr(active_source, "value")
                 else int(active_source) if active_source is not None else None)
    source_node = srs.NodeID(source_id) if source_id is not None else None
    source_kind = (adapter.s.node(source_node)["type"]
                   if source_node is not None and adapter.inner.has_node(source_node)
                   else None)
    source_query = (str(adapter.s.node(source_node)["attrs"].get("query") or "").strip()
                    if source_node is not None and adapter.inner.has_node(source_node)
                    else "")
    pending_count = sum(len(item["jobs"])
                        for item in state.pending_search_host_actions.values())
    capacity = max(0, _MAX_PENDING_SEARCH_IO - pending_count)
    jobs = []
    for req in list(adapter.s.nodes("SearchRequest")):
        if not adapter.inner.has_node(req):
            continue
        attrs = dict(adapter.s.node(req)["attrs"])
        if attrs.get("status") != "requested":
            continue
        if source_kind == "SearchRequest" and int(req.value) != source_id:
            continue
        if source_kind == "GroundRequest" and str(attrs.get("query") or "").strip() != source_query:
            continue
        if len(jobs) >= capacity:
            continue
        query = str(attrs.get("query") or "").strip()
        token = f"{int(req.value)}:{time.monotonic_ns()}"
        if not query:
            adapter.inner.set_attr(req, "status", "failed")
            adapter.inner.set_attr(req, "epistemic_status", "unknown")
            adapter.inner.set_attr(req, "evidence_path", "SearchRequest -> empty_query")
            adapter.inner.set_attr(req, "error", "empty query")
            continue
        # The graph's unresolved-topic rule already treats `running` as
        # pending and suppresses premature honest-miss output during retrieval.
        adapter.inner.set_attr(req, "status", "running")
        adapter.inner.set_attr(req, "search_io_token", token)
        try:
            future = state.search_io_executor.submit(
                retrieve_search_candidate_payloads, query,
                referent_status=attrs.get("referent_status", "supported"),
                referents=attrs.get("referents") or [query],
                referent_evidence_path=attrs.get("referent_evidence_path", ""),
                timeout=8)
        except Exception as exc:  # noqa: BLE001 -- expose submit failure
            adapter.inner.set_attr(req, "status", "failed")
            adapter.inner.set_attr(req, "search_io_token", None)
            adapter.inner.set_attr(req, "epistemic_status", "search_failed")
            adapter.inner.set_attr(req, "evidence_path",
                                   "SearchRequest -> retrieval_attempt -> submit_exception")
            adapter.inner.set_attr(req, "error", f"{type(exc).__name__}: {exc}")
            continue
        future.add_done_callback(lambda _f, wake=state.dirty: wake.set())
        jobs.append({"kind": "search", "request_id": int(req.value), "token": token,
                     "query": query, "future": future})
    has_eligible = any(
        adapter.inner.has_node(req)
        and adapter.s.node(req)["attrs"].get("status") == "requested"
        and (source_kind != "SearchRequest" or int(req.value) == source_id)
        and (source_kind != "GroundRequest"
             or str(adapter.s.node(req)["attrs"].get("query") or "").strip()
             == source_query)
        for req in adapter.s.nodes("SearchRequest"))
    return {"jobs": jobs, "deferred": bool(has_eligible and not jobs)}


# --- detail hook (best-effort; mirrors the search hook exactly) -------------
# The DECISION to prefetch a topic's detail is the agent's (the
# conversation_elaborate seed rule request_detail_for_current_topic mints a
# DetailRequest from the current-topic hub); this only notices a requested one,
# fetches the topic's progressive-detail chunks, and ingests them as a graph
# chain -- see domains/fetch_dispatch.py::scan_and_ingest_detail +
# domains/topic_grounding.py::topic_detail. The progressive-disclosure decision
# (serve the next chunk on 'tell me more') is itself a seed rule.

# --- study hook (WHOLE-CURRICULUM WAVE 1; mirrors the detail/browse hooks
# exactly) --- The DECISION of which lesson is next, whether it settled done
# or blocked, and whether a blocked lesson reopens are ALL graph-native
# (domains.curriculum_study.study_tick's held-Argmin pick + seeds/
# curriculum_study.json's rules); this hook only notices there is standing
# study work to advance and calls the ONE driver entry point.

def _study_tick(adapter: WorldAdapter) -> None:
    try:
        from domains.curriculum_study import study_tick
    except ImportError:
        return
    try:
        study_tick(adapter)
    except Exception as e:  # noqa: BLE001 -- never let a study hiccup kill the tick loop
        log(f"study error (continuing): {e}")


def _detail_tick(adapter: WorldAdapter, state: "DaemonState | None" = None):
    try:
        from domains.fetch_dispatch import scan_and_ingest_detail
    except ImportError:
        return
    try:
        if state is not None:
            stage = _start_detail_request_io(adapter, state)
            if stage["jobs"]:
                return {"host_action_pending": True, "jobs": stage["jobs"]}
            if stage["deferred"]:
                return {"host_action_deferred": True}
            return None
        scan_and_ingest_detail(adapter, log=log)
    except Exception as e:  # noqa: BLE001 -- never let a detail hiccup kill the tick loop
        log(f"detail error (continuing): {e}")


def _start_detail_request_io(adapter: WorldAdapter, state: "DaemonState") -> dict:
    """Use local detail on-owner, then retrieve remote chunks without graph access."""
    from domains import topic_grounding as tg
    from domains.fetch_dispatch import commit_detail_payload

    active_source = getattr(state, "active_host_action_source", None)
    source_id = (int(active_source.value) if hasattr(active_source, "value")
                 else int(active_source) if active_source is not None else None)
    source_node = srs.NodeID(source_id) if source_id is not None else None
    source_kind = (adapter.s.node(source_node)["type"]
                   if source_node is not None and adapter.inner.has_node(source_node)
                   else None)
    pending_count = sum(len(item["jobs"])
                        for item in state.pending_search_host_actions.values())
    capacity = max(0, _MAX_PENDING_SEARCH_IO - pending_count)
    jobs = []
    eligible = []
    for req in list(adapter.s.nodes("DetailRequest")):
        if not adapter.inner.has_node(req):
            continue
        attrs = dict(adapter.s.node(req)["attrs"])
        if source_kind == "DetailRequest" and int(req.value) != source_id:
            continue
        if attrs.get("status") == "running" and attrs.get("detail_io_token"):
            eligible.append(req)
            continue
        if attrs.get("status") != "requested":
            continue
        eligible.append(req)
        topic = str(attrs.get("topic") or "").strip()
        if not topic:
            adapter.inner.set_attr(req, "status", "failed")
            adapter.inner.set_attr(req, "error", "empty topic")
            continue
        try:
            local_chunks = tg.detail_local_chunks(adapter, topic)
        except Exception as exc:  # noqa: BLE001
            adapter.inner.set_attr(req, "status", "failed")
            adapter.inner.set_attr(req, "error", f"{type(exc).__name__}: {exc}")
            continue
        if local_chunks:
            try:
                commit_detail_payload(adapter, topic, local_chunks)
                adapter.inner.set_attr(req, "status", "done")
            except Exception as exc:  # noqa: BLE001
                adapter.inner.set_attr(req, "status", "failed")
                adapter.inner.set_attr(req, "error", f"ingest {type(exc).__name__}: {exc}")
            continue
        if len(jobs) >= capacity:
            continue
        token = f"detail:{int(req.value)}:{time.monotonic_ns()}"
        adapter.inner.set_attr(req, "status", "running")
        adapter.inner.set_attr(req, "detail_io_token", token)
        try:
            future = state.search_io_executor.submit(
                tg.retrieve_detail_payload, topic, timeout=8)
        except Exception as exc:  # noqa: BLE001
            adapter.inner.set_attr(req, "status", "failed")
            adapter.inner.set_attr(req, "detail_io_token", None)
            adapter.inner.set_attr(req, "error", f"{type(exc).__name__}: {exc}")
            continue
        future.add_done_callback(lambda _f, wake=state.dirty: wake.set())
        jobs.append({"kind": "detail", "request_id": int(req.value),
                     "token": token, "query": topic, "future": future})
    still_pending = any(
        adapter.inner.has_node(req)
        and adapter.s.node(req)["attrs"].get("status") in ("requested", "running")
        for req in eligible)
    return {"jobs": jobs, "deferred": bool(still_pending and not jobs)}


# --- browse hook (best-effort; mirrors the fetch hook exactly) ---------------
# The DECISION to browse a URL is the agent's (it mints BrowseRequest nodes via
# its own rules); this only notices a requested one, opens a BrowserWorld
# session, and runs the bounded tick/apply loop — see domains/browse_dispatch.py.

def _browse_tick(adapter: WorldAdapter) -> None:
    try:
        from domains.browse_dispatch import scan_and_browse
    except ImportError:
        return
    try:
        scan_and_browse(adapter, log=log)
    except Exception as e:  # noqa: BLE001 -- never let a browse hiccup kill the tick loop
        log(f"browse error (continuing): {e}")


# --- imagine hook (best-effort; mirrors the fetch/browse hooks exactly) ------
# The DECISION to imagine (and roughly what counterfactual to explore) is the
# agent's own — an escalated Impasse's authored engage rule mints an
# ImagineRequest (seeds/composer_imagination_graph.json); this only notices a
# requested one, runs imagine()/reground() (Python host calls that cannot
# execute inside a Rust rule effect), and writes back the trace the agent's
# own judge rule then reads — see domains/imagination_dispatch.py.

def _imagine_tick(adapter: WorldAdapter) -> None:
    try:
        from domains.imagination_dispatch import scan_and_imagine
    except ImportError:
        return
    try:
        scan_and_imagine(adapter)
    except Exception as e:  # noqa: BLE001 -- never let an imagine hiccup kill the tick loop
        log(f"imagine error (continuing): {e}")


# --- collapse-watch hook (best-effort; mirrors the imagine hook exactly) ----
# TIER 4: the graph's own model of its total collapse. The DECISION about
# what the model MEANS (attend the frontier, recognise the frozen core as
# stable self, escalate a predicted divergence to active cognition) is the
# agent's own -- its authored rules (seeds/composer_collapse_watch_graph.json,
# minted via ground_concern's 'predict' relation head) react to whatever
# CollapseModel this hook mints. This hook only calls domains.collapse_model.
# predict_collapse (a bounded tier-3 forward-look, an in-process Python call
# that cannot execute inside a Rust rule effect -- exactly why this hook
# exists), and wires `agent -has_collapse_model-> model` so the agent's
# rules have something to match on the tick that follows. The graph
# supervisor calls it only for a graph-minted
# ``HostActionRequest{action:collapse}``; no daemon cadence controls it.

def _collapse_tick(adapter: WorldAdapter) -> None:
    try:
        from domains.collapse_watch import scan_and_predict
    except ImportError:
        return
    try:
        scan_and_predict(adapter)
    except Exception as e:  # noqa: BLE001 -- never let a collapse-watch hiccup kill the tick loop
        log(f"collapse-watch error (continuing): {e}")


# --- self-correction hook (best-effort; mirrors the imagine/collapse hooks) --
# TIER 5, CLOSED THE LOOP: `domains.self_correct_dispatch.scan_and_self_
# correct` is the mechanical host hook (mirrors `domains.collapse_watch.
# scan_and_predict` / `domains.imagination_dispatch.scan_and_imagine`) that
# calls `domains.self_correction.intervene_on_divergence` -- the machinery
# (imagine a fix, predict whether it converges, adopt if the driving rule's
# provenance allows it, else propose for human review) -- an in-process
# Python call a Rust rule effect cannot make itself, the SAME reason every
# other `scan_and_*` hook in this file exists. WHICH divergence gets
# attempted is no longer this hook's decision (nor a blanket "try every
# one"): `scan_and_self_correct` only acts on an `Impasse{kind:predicted_
# divergence}` the agent's OWN authored `self_correct_gate_<tag>` rule
# (`seeds/composer_self_correct_graph.json`, dispatched via `ground_concern`'s
# 'correct' relation head) has marked `correct_ready` -- a genuine cost-
# worth-it gate (see that seed's own description). WHICH candidate fix gets
# tried first, when more than one would converge, is likewise the agent's
# own `self_correct_rank_<tag>` Argmin Program, consulted inside that same
# dispatch call. This hook is mechanical delegation only.
def _self_correct_tick(adapter: WorldAdapter) -> None:
    try:
        from domains.self_correct_dispatch import scan_and_self_correct
    except ImportError:
        return
    try:
        for item in scan_and_self_correct(adapter):
            result = item["result"]
            log(f"self-correct: chosen={result.get('chosen')} adopted={result.get('adopted')} "
                f"escalated={result.get('escalated')} target={item.get('target_rule')}")
    except Exception as e:  # noqa: BLE001 -- never let a self-correct hiccup kill the tick loop
        log(f"self-correct error (continuing): {e}")


# --- concern hook (standing self-improvement concern; mirrors the dispatch hook) --
# The CONCERN ITSELF is graph data, not host-authored text: seeds/standing_self_
# improvement_concern.json's StandingConcern node carries the exact test/send/
# judge/gradient/adopt relation-cue vocabulary scripts/jabberwock_improves_itself.py
# has always typed BY HAND, checked in instead. This hook only notices an
# unprocessed StandingConcern and feeds its `relations` attr through the agent's
# OWN induce_concern -> ground_concern machinery (domains.reflective_faculty) --
# whether that MINTS a CapabilityAxis (a genuine residual: no held term-shape
# covers this structure yet) or is RECOGNIZED (already covered), which composer
# it grounds to, and which mint/judge/adopt rules get authored are entirely the
# agent's own seeded-rule decisions (shape_decode_loop + composer_dispatch), never
# this hook's. Idempotent: guarded by the node's own `status` attr, so it fires
# at most once per StandingConcern per agent lifetime (a checkpoint-resumed agent
# carries `status: processed` forward and skips it; a genuinely fresh boot -- no
# checkpoint -- re-authors the SAME rules from the SAME seed, deterministically).

def _process_code_write_standing(adapter: WorldAdapter, standing_node, at: dict) -> None:
    """CODE-CURRICULUM (the named part-A seam): a promoted `code_write`
    StandingConcern grounds DIRECTLY into the CODE-4 compose path
    (domains.code_write_growth.work_on_code_write_gap) instead of the
    generic induce_concern/ground_concern capability-axis machinery, which
    has nothing to do with composing a write shape from a held predication.
    `about` is the original SelfConcern's own request text (copied verbatim
    at promotion time), so `work_on_code_write_gap`'s own content-word gap
    picking resolves it back to the SAME concern -- no re-derivation.

    Records a MECHANICAL outcome datum (`code_write_compose_ok` / `_reason`)
    onto the StandingConcern -- never a decision here. The seeded
    `note_code_write_composition_exhausted` rule (seeds/code_write_gap.json)
    DECIDES an unsuccessful compose is exhausted and marks
    `experiments_exhausted`/`exhausted_note` -- the note_experiments_exhausted
    precedent, pointed at this synchronous path instead of an async
    Experiment dispatch. A SUCCESSFUL compose already resolves the ORIGINAL
    SelfConcern via `resolve_code_write_gap`'s own `taught_for` read, in the
    very next run_rules pass -- nothing else to do here."""
    try:
        import domains.code_write_growth as cwg
    except ImportError as e:  # noqa: BLE001 -- never let a bad concern kill the tick loop
        adapter.s.set_attr(standing_node, "code_write_compose_ok", 0.0)
        adapter.s.set_attr(standing_node, "code_write_compose_reason",
                           "code_write_growth unavailable: %s" % e)
        return
    about = str(at.get("about") or "")
    try:
        result = cwg.work_on_code_write_gap(adapter, about)
    except Exception as e:  # noqa: BLE001 -- never let a bad concern kill the tick loop
        result = {"ok": False, "reason": "%s: %s" % (type(e).__name__, e)}
    ok = bool(result.get("ok"))
    reason = str(result.get("reason") or ("composed shape %r" % result.get("shape")))
    adapter.s.set_attr(standing_node, "code_write_compose_ok", 1.0 if ok else 0.0)
    adapter.s.set_attr(standing_node, "code_write_compose_reason", reason)


def _process_prog_read_standing(adapter: WorldAdapter, standing_node, at: dict) -> None:
    """ARC6 A25 -- the `_process_code_write_standing` precedent, applied to
    the sibling `prog_read` gap kind (measured LIVE to fall through to the
    generic induce_concern/ground_concern composer and mint an inert,
    misleadingly-named rule -- see the `_promote_relations_for_concern`
    comment above and PROGRAM_SYNTHESIS_ARC6_PROGREAD_SELFIMPROVE.md).

    A promoted `prog_read` StandingConcern grounds DIRECTLY into
    `domains.prog_read_growth.work_on_prog_read_gap` instead of the generic
    machinery. `about` is the original SelfConcern's own content text
    ('<frame> read blocked: <blockers>', copied verbatim at promotion time).

    Records a MECHANICAL outcome datum (`prog_read_compose_ok` / `_reason`)
    onto the StandingConcern -- never a decision here. The seeded
    `note_prog_read_composition_exhausted` rule (seeds/prog_read_gap.json)
    DECIDES an unsuccessful compose is exhausted and marks
    `experiments_exhausted`/`exhausted_note` -- the
    note_code_write_composition_exhausted precedent, pointed at this
    synchronous path. Every call exhausts honestly today (module docstring,
    domains/prog_read_growth.py): closing a prog_read gap for real needs new
    Rust engine Term/IR-variant coverage (named per-blocker in the reason),
    out of scope for a seed/adapter-level amendment -- this function's job is
    only to STOP the wrong generic composer from firing and to leave an
    honest, specific record in its place."""
    try:
        import domains.prog_read_growth as prg
    except ImportError as e:  # noqa: BLE001 -- never let a bad concern kill the tick loop
        adapter.s.set_attr(standing_node, "prog_read_compose_ok", 0.0)
        adapter.s.set_attr(standing_node, "prog_read_compose_reason",
                           "prog_read_growth unavailable: %s" % e)
        return
    about = str(at.get("about") or "")
    try:
        result = prg.work_on_prog_read_gap(adapter, about)
    except Exception as e:  # noqa: BLE001 -- never let a bad concern kill the tick loop
        result = {"ok": False, "reason": "%s: %s" % (type(e).__name__, e)}
    ok = bool(result.get("ok"))
    reason = str(result.get("reason") or ("extended frame %r" % result.get("frame")))
    adapter.s.set_attr(standing_node, "prog_read_compose_ok", 1.0 if ok else 0.0)
    adapter.s.set_attr(standing_node, "prog_read_compose_reason", reason)


def _process_gamma_production_standing(adapter: WorldAdapter, standing_node, at: dict) -> None:
    """GAMMA_PRODUCTION_ADOPT_HANDLER -- the `_process_prog_read_standing`
    precedent, applied to the `gamma_production` gap kind
    (GAMMA_COLLAPSE_ALGORITHM_RESULTS.md Q2's named, out-of-scope gap: "no
    gamma_production handler exists ... falls through to the generic
    comprehend_first default").

    UNLIKE every other kind this dispatch ladder routes, a `gamma_production`
    StandingConcern can NEVER be synchronously CLOSED here -- doing so would
    mean this Python path deciding, unsupervised, that a Production should
    become live, which is exactly what Theorem XII (reference-monitor
    containment, checker.rs:1-3) forbids. This function only calls
    `domains.gamma_production_growth.judge_gamma_production_gap` -- a
    READ-ONLY probe (`is_edge_admissible`, never `add_production`) -- and
    records the mechanical outcome (`gamma_production_judge_status` /
    `_reason` / `_candidate`, a JSON string of the candidate Production when
    one was built) onto the StandingConcern. `seeds/gamma_production_adopt.
    json`'s three rules read that datum and DECIDE what it means
    (awaiting_adopt / resolved-already / experiments_exhausted) -- never a
    decision here. Making the candidate LIVE is a SEPARATE, explicit,
    human-gated call: `adopt_gamma_production_standing` below, never invoked
    from this function or from _concern_tick."""
    try:
        import domains.gamma_production_growth as gpg
    except ImportError as e:  # noqa: BLE001 -- never let a bad concern kill the tick loop
        adapter.s.set_attr(standing_node, "gamma_production_judge_status", "unresolvable")
        adapter.s.set_attr(standing_node, "gamma_production_judge_reason",
                           "gamma_production_growth unavailable: %s" % e)
        return
    about = str(at.get("about") or "")
    try:
        result = gpg.judge_gamma_production_gap(adapter, about)
    except Exception as e:  # noqa: BLE001 -- never let a bad concern kill the tick loop
        result = {"status": "unresolvable",
                 "reason": "%s: %s" % (type(e).__name__, e)}
    status = str(result.get("status") or "unresolvable")
    reason = str(result.get("reason") or "")
    adapter.s.set_attr(standing_node, "gamma_production_judge_status", status)
    adapter.s.set_attr(standing_node, "gamma_production_judge_reason", reason)
    candidate = result.get("candidate_production")
    if candidate is not None:
        adapter.s.set_attr(standing_node, "gamma_production_candidate", json.dumps(candidate))


def adopt_gamma_production_standing(adapter: WorldAdapter, id_str: str) -> dict:
    """HUMAN-GATED adopt: the `promote_self_concern` precedent, for the ONE
    step in this whole rung that may call `add_production`. Reachable only
    by an explicit external call (a human action, or its stand-in in a
    test/demo) -- NEVER from `_concern_tick`, NEVER from a rule. Looks up
    the StandingConcern by id, requires it to be judged `ready_for_adopt`
    (a human/experiment decision the judge step already surfaced, never
    guessed here), reconstructs the candidate Production from the
    StandingConcern's OWN recorded JSON (never re-derived from scratch, so
    what gets adopted is exactly what was judged), and calls
    `domains.gamma_production_growth.adopt_gamma_production` -- which itself
    RE-VERIFIES the triple is still inadmissible immediately before calling
    `add_production` (judging on stale data would be a bug, not a shortcut).
    On success: marks the StandingConcern `status='adopted'` and the
    ORIGINAL SelfConcern `status='resolved'` (found via the `promoted_to`
    edge's reverse, `adapter.inner.in_neighbours`) -- mechanical bookkeeping
    of a fact THIS function itself just made true, the same status
    `promote_self_concern` sets `sc.status='promoted'` directly rather than
    via a rule. Idempotent: an already-adopted StandingConcern is rejected,
    not re-run."""
    try:
        import domains.gamma_production_growth as gpg
    except ImportError as e:  # noqa: BLE001
        return {"ok": False, "error": "gamma_production_growth unavailable: %s" % e}
    try:
        standing = srs.NodeID(int(id_str))
    except (ValueError, TypeError):
        return {"ok": False, "error": "bad id"}
    with AGENT_LOCK:
        if not adapter.s.has_node(standing) or adapter.s.node(standing).get("type") != "StandingConcern":
            return {"ok": False, "error": "not found"}
        at = adapter.s.node(standing)["attrs"]
        if at.get("kind") != "gamma_production":
            return {"ok": False, "error": "not a gamma_production concern"}
        if at.get("status") == "adopted":
            return {"ok": False, "error": "already adopted"}
        if at.get("gamma_production_judge_status") != "ready_for_adopt":
            return {"ok": False, "error": "not ready for adopt (judge_status=%r) -- "
                                          "the judge step must mark this "
                                          "ready_for_adopt first"
                                          % at.get("gamma_production_judge_status")}
        raw_candidate = at.get("gamma_production_candidate")
        if not raw_candidate:
            return {"ok": False, "error": "no candidate production recorded on this concern"}
        try:
            candidate = json.loads(raw_candidate)
        except (TypeError, ValueError) as e:
            return {"ok": False, "error": "malformed candidate JSON: %s: %s" % (type(e).__name__, e)}
        # No separate `expected_triple` to cross-check here: `candidate` IS the
        # StandingConcern's own recorded JSON (never re-derived), so there is
        # nothing independent to compare it against -- the real safety check
        # is `adopt_gamma_production`'s own immediate pre-adopt re-probe.
        result = gpg.adopt_gamma_production(adapter, candidate, expected_triple=None)
        if not result.get("ok"):
            return {"ok": False, "error": result.get("reason") or "adopt failed", "detail": result}
        adapter.s.set_attr(standing, "status", "adopted")
        adapter.s.set_attr(standing, "adopted_triple", " -> ".join(str(x) for x in result.get("triple", ())))
        try:
            for sc in adapter.inner.in_neighbours(standing, "promoted_to"):
                if adapter.s.has_node(sc) and adapter.s.node(sc).get("type") == "SelfConcern":
                    adapter.s.set_attr(sc, "status", "resolved")
        except Exception:  # noqa: BLE001
            pass
    return {"ok": True, "standing_concern": _nid_value(standing),
           "triple": result.get("triple"), "reason": result.get("reason")}


# --- GROUND_CONCERN SIX KINDS (Path 2, GROUND_CONCERN_SIX_KINDS_PREREG.md) --
# The honesty investigation's own §5 Path 2: give every concern kind that
# falls through to the generic comprehend_first/ground_concern fallback its
# own dedicated routing check BEFORE it reaches the shared composer -- the
# SAME shape code_write/prog_read already have above. A live measurement
# (the PREREG's §0) established the population precisely: knowledge and
# self_account ALWAYS fall through (comprehend_first, or for self_account
# also the equally-wrong ARC bundle); reply_fix falls through ONLY on its
# comprehend_first sub-case (its experiment sub-case is ALREADY correctly
# wired and must be left alone); instruction/performance/comprehension
# NEVER fall through (unconditional kind-membership in
# _promote_relations_for_concern already routes them to the genuine
# conversation-experiment composer) -- no interception needed or added for
# those three.

def _process_knowledge_standing(adapter: WorldAdapter, standing_node, at: dict) -> None:
    """Re-attempts the EXISTING self-heal chain (CLAUDE.md's "Knowledge gaps
    self-heal": WorldAdapter.answer_about / ground_unknowns) instead of the
    generic induce_concern/ground_concern composer, which was MEASURED (this
    rung) to mint the SAME inert comprehend_describe_directive_<tag> rule
    A25 found for prog_read. Records a MECHANICAL outcome datum
    (knowledge_compose_ok / _reason) onto the StandingConcern -- never a
    decision here; seeds/knowledge_gap_resolve.json's rules read it."""
    try:
        import domains.knowledge_growth as kng
    except ImportError as e:  # noqa: BLE001 -- never let a bad concern kill the tick loop
        adapter.s.set_attr(standing_node, "knowledge_compose_ok", 0.0)
        adapter.s.set_attr(standing_node, "knowledge_compose_reason",
                           "knowledge_growth unavailable: %s" % e)
        return
    about = str(at.get("about") or "")
    try:
        result = kng.work_on_knowledge_gap(adapter, about)
    except Exception as e:  # noqa: BLE001
        result = {"ok": False, "reason": "%s: %s" % (type(e).__name__, e)}
    ok = bool(result.get("ok"))
    reason = str(result.get("reason") or ("grounded topic %r" % result.get("topic")))
    adapter.s.set_attr(standing_node, "knowledge_compose_ok", 1.0 if ok else 0.0)
    adapter.s.set_attr(standing_node, "knowledge_compose_reason", reason)


def _process_self_account_standing(adapter: WorldAdapter, standing_node, at: dict) -> None:
    """Re-checks the EXISTING SelfProcess account lookup (CLAUDE.md's
    "self_processes": domains.self_model.find_self_process) instead of the
    generic composer -- self_account has NO safe existing pipeline value to
    defer to (measured, PREREG §0: both comprehend_first and the rare
    content-triggered ARC bundle are equally mismatched), so this
    interception is unconditional. Records a MECHANICAL outcome datum
    (self_account_compose_ok / _reason) -- never auto-authors a SelfProcess
    account (that would fabricate a self-account, forbidden by
    run_self_process's own docstring)."""
    try:
        import domains.self_account_growth as sag
    except ImportError as e:  # noqa: BLE001
        adapter.s.set_attr(standing_node, "self_account_compose_ok", 0.0)
        adapter.s.set_attr(standing_node, "self_account_compose_reason",
                           "self_account_growth unavailable: %s" % e)
        return
    about = str(at.get("about") or "")
    try:
        result = sag.work_on_self_account_gap(adapter, about)
    except Exception as e:  # noqa: BLE001
        result = {"ok": False, "reason": "%s: %s" % (type(e).__name__, e)}
    ok = bool(result.get("ok"))
    reason = str(result.get("reason") or ("held account for %r" % result.get("topic")))
    adapter.s.set_attr(standing_node, "self_account_compose_ok", 1.0 if ok else 0.0)
    adapter.s.set_attr(standing_node, "self_account_compose_reason", reason)


def _process_reply_fix_standing(adapter: WorldAdapter, standing_node, at: dict) -> None:
    """ONLY called for a reply_fix StandingConcern whose OWN stored
    `pipeline` attr is `comprehend_first` (_concern_tick's own guard below)
    -- an `experiment`-pipelined reply_fix concern (content names acting/
    seed/ablation vocabulary) is ALREADY correctly routed by the untouched
    generic branch and must never reach this function. Looks the concern's
    fixed content tag up in domains.reply_fix_growth's correspondence table
    instead of the generic composer, which was MEASURED (this rung) to mint
    the same inert rule for both known tags (upload_attachment_reply /
    upload_vision_wiring). Records a MECHANICAL outcome datum
    (reply_fix_compose_ok / _reason) -- never a decision here."""
    try:
        import domains.reply_fix_growth as rfg
    except ImportError as e:  # noqa: BLE001
        adapter.s.set_attr(standing_node, "reply_fix_compose_ok", 0.0)
        adapter.s.set_attr(standing_node, "reply_fix_compose_reason",
                           "reply_fix_growth unavailable: %s" % e)
        return
    about = str(at.get("about") or "")
    try:
        result = rfg.work_on_reply_fix_gap(adapter, about)
    except Exception as e:  # noqa: BLE001
        result = {"ok": False, "reason": "%s: %s" % (type(e).__name__, e)}
    ok = bool(result.get("ok"))
    reason = str(result.get("reason") or ("closed tag %r" % result.get("tag")))
    adapter.s.set_attr(standing_node, "reply_fix_compose_ok", 1.0 if ok else 0.0)
    adapter.s.set_attr(standing_node, "reply_fix_compose_reason", reason)


def _execute_requested_retries(adapter: WorldAdapter) -> list:
    """Mechanical executor for seeds/instruction_repair_retry.json: a
    SelfConcern the graph marked retry_requested=1 is torn down and
    re-promoted (the same path as the human-gated repromote); the mark is
    cleared. The DECISION to retry is the graph rule's, never made here."""
    done = []
    try:
        scs = list(adapter.s.nodes("SelfConcern"))
    except Exception:  # noqa: BLE001
        return done
    for sc in scs:
        if not adapter.s.has_node(sc) or adapter.s.node(sc)["attrs"].get("retry_requested") != 1:
            continue
        adapter.s.set_attr(sc, "retry_requested", 0)
        res = repromote_self_concern(adapter, str(_nid_value(sc)))
        done.append(res)
        log(f"self-improve: agent-requested retry of concern {_nid_value(sc)}: ok={res.get('ok')}")
    return done


def _concern_tick(adapter: WorldAdapter) -> None:
    try:
        import domains.reflective_faculty as rf
    except ImportError:
        return
    s = adapter.s
    _execute_requested_retries(adapter)
    try:
        nodes = list(s.nodes("StandingConcern"))
    except Exception:  # noqa: BLE001 -- type not present in this seed set
        return
    for n in nodes:
        if not s.has_node(n):
            continue
        at = s.node(n)["attrs"]
        if at.get("status") != "pending":
            continue
        try:
            if at.get("kind") == "code_write":
                _process_code_write_standing(adapter, n, at)
                s.set_attr(n, "status", "processed")
                continue
            if at.get("kind") == "prog_read":
                _process_prog_read_standing(adapter, n, at)
                s.set_attr(n, "status", "processed")
                continue
            if at.get("kind") == "knowledge" and at.get("pipeline") != "experiment":
                _process_knowledge_standing(adapter, n, at)
                s.set_attr(n, "status", "processed")
                continue
            if at.get("kind") == "self_account":
                _process_self_account_standing(adapter, n, at)
                s.set_attr(n, "status", "processed")
                continue
            if at.get("kind") == "reply_fix" and at.get("pipeline") != "experiment":
                _process_reply_fix_standing(adapter, n, at)
                s.set_attr(n, "status", "processed")
                continue
            if at.get("kind") == "gamma_production":
                _process_gamma_production_standing(adapter, n, at)
                s.set_attr(n, "status", "processed")
                continue
            relations = at.get("relations") or []
            _ensure_world_for_relations(adapter, relations)
            name = at.get("name") or f"standing_concern_{_nid_value(n)}"
            ind = rf.induce_concern(adapter, relations, name_hint=name)
            if ind.get("minted") and ind.get("capability_key"):
                rf.ground_concern(adapter, [ind["capability_key"]])
            s.set_attr(n, "status", "processed")
        except Exception as e:  # noqa: BLE001 -- never let a bad concern kill the tick loop
            log(f"concern-grounding error (continuing): {e}")
    nudged = _nudge_promoted_experiments(adapter)
    if nudged:
        log(f"self-improve: nudged author rules ({nudged} extra ticks)")
    scrubbed = _scrub_stale_author_rules(adapter)
    if scrubbed:
        log(f"self-improve: scrubbed {scrubbed} stale author rule(s)")
    cancelled = _cancel_unscoped_experiments(adapter)
    if cancelled:
        log(f"self-improve: cancelled {cancelled} unscoped experiment(s)")
    judged = _replay_reply_fix_judge(adapter)
    if judged:
        log(f"self-improve: replay-judged {judged} reply_fix concern(s)")


# --- NL-steering hook (executes what the steering RULES marked) --------------
# seeds/conversation_steering.json's steer_promote_concern DECIDES (graph-
# natively) that a chat turn asked to promote a specific noted SelfConcern and
# marks it `promote_requested=1.0`. This hook is the mechanical executor: it
# scans for that marker and calls the EXISTING human-gated promote_self_concern
# on each — the rule decided WHICH concern; the human's own utterance was the
# gate (only interlocutor turns can mark); this hook only performs the same
# mechanical promotion the POST /api/self_concerns/<id>/promote handler
# performs. promote flips status noted->promoted, so a promoted concern never
# re-fires the scan (no attr clearing needed). Zero decisions.

def _steer_tick(adapter: WorldAdapter, state: "DaemonState | None" = None) -> list:
    promoted = []
    try:
        scs = list(adapter.s.nodes("SelfConcern"))
    except Exception:  # noqa: BLE001 -- type not present in this seed set
        return promoted
    for sc in scs:
        if not adapter.s.has_node(sc):
            continue
        a = adapter.s.node(sc)["attrs"]
        if a.get("status") != "noted" or a.get("promote_requested") != 1.0:
            continue
        try:
            res = promote_self_concern(adapter, str(_nid_value(sc)))
        except Exception as e:  # noqa: BLE001 -- never let one concern kill the tick loop
            log(f"steer-promote error (continuing): {e}")
            continue
        if res.get("ok"):
            promoted.append(res)
            log(f"steer: promoted self-concern {res['self_concern']} "
                f"-> standing {res['standing_concern']} ({res.get('about')!r})")
            if state is not None:
                state.publish_event({"type": "self_concern_update",
                                     "id": str(res["self_concern"]),
                                     "status": "promoted",
                                     "standing_concern": res.get("standing_concern")})
                try:
                    state.publish_event({"type": "self_improvement_update",
                                         **list_self_improvement(adapter)})
                except Exception:  # noqa: BLE001
                    pass
    return promoted


# --- autonomy-narration hook (mechanical transition read -> one chat turn) ----
# When the self-improvement pipeline CONCLUDES something — an Experiment reaches
# done/failed, an Adoption is minted, a promoted StandingConcern finishes
# processing — the agent tells the human about it in chat, unprompted. This is
# a mechanical before/after read exactly like monitor_loop's session diff: the
# TRANSITIONS are the agent's own rules'/pipeline's doing; this hook only
# notices an un-narrated concluded node, stamps `narrated=1.0` ON THE NODE
# (graph-persistent, so idempotence survives a daemon restart — the
# conversation_elaborate served-marker precedent), formats one sentence from
# the node's own attrs, and publishes/records it through the SAME record+
# publish path the chat handlers use. THROTTLE: at most ONE narration per call;
# remaining candidates queue for subsequent passes.

def _narration_candidates(adapter: WorldAdapter) -> list:
    """(node, sentence) for every concluded-but-unnarrated pipeline node, in
    node-id order. Pure mechanical read + format."""
    out = []
    s = adapter.s
    try:
        for n in sorted(s.nodes("Experiment"), key=lambda x: int(_nid_value(x))):
            if not s.has_node(n):
                continue
            a = s.node(n)["attrs"]
            if a.get("status") not in ("done", "failed") or a.get("narrated") == 1.0:
                continue
            hyp = str(a.get("hypothesis") or a.get("name") or f"#{_nid_value(n)}")
            outcome = str(a.get("outcome") or a.get("status"))
            sent = f"Experiment on '{hyp}' concluded: {outcome}."
            if a.get("adopted"):
                sent += " I adopted the variant rule."
            out.append((n, sent))
    except Exception:  # noqa: BLE001
        pass
    try:
        for n in sorted(s.nodes("Adoption"), key=lambda x: int(_nid_value(x))):
            if not s.has_node(n):
                continue
            a = s.node(n)["attrs"]
            if a.get("narrated") == 1.0:
                continue
            sent = (f"I changed myself: replaced rule '{a.get('rule_removed')}' "
                    f"with '{a.get('rule_added')}' (experiment "
                    f"{a.get('experiment_id')}).")
            out.append((n, sent))
    except Exception:  # noqa: BLE001
        pass
    try:
        for n in sorted(s.nodes("StandingConcern"), key=lambda x: int(_nid_value(x))):
            if not s.has_node(n):
                continue
            a = s.node(n)["attrs"]
            if a.get("status") != "processed" or a.get("narrated") == 1.0:
                continue
            if a.get("source") != "conversation_promoted":
                continue   # only the promoted-concern pipeline narrates its close
            about = str(a.get("about") or a.get("name") or f"#{_nid_value(n)}")
            out.append((n, f"I finished grounding the promoted concern '{about}' "
                           f"— it is in my self-improvement pipeline now."))
    except Exception:  # noqa: BLE001
        pass
    out.sort(key=lambda t: int(_nid_value(t[0])))
    return out


def _narrate_tick(state: "DaemonState") -> dict | None:
    """Narrate AT MOST ONE concluded pipeline transition into chat. Returns the
    published turn dict, or None when nothing is waiting. Mechanical only:
    the marker write, the format, the record, the publish."""
    adapter = state.adapter
    with AGENT_LOCK:
        cands = _narration_candidates(adapter)
        if not cands:
            return None
        node, sentence = cands[0]
        adapter.inner.set_attr(node, "narrated", 1.0)   # restart-safe: lives in the graph
    text = "[self-improvement update]"
    state.publish_event({"type": "chat", "text": text, "reply": sentence,
                         "reply_from": "agent"})
    record_chat_turn(state, text, sentence, reply_from="agent")
    log(f"narrate: {sentence}")
    return {"text": text, "reply": sentence}


# --- close-experiment-loop hook (adopt/teach; mirrors the dispatch hook) -----
# WHICH Experiments are conclusion_ready / adopt_ready is the agent's own judge/
# adopt rules' decision (composed by domains.reflective_faculty._compose_
# experiment_rule, fired live via tick()/run_rules()); this hook only notices
# what they marked and performs the mechanical I/O close_experiment_loop already
# owns -- teach() the verdict into seeds/experiment_conclusions.json, and
# perform_adoptions() fold a genuinely-supported acting-variant back into the
# PARENT itself, gated by the hard provenance denylist. Never called from
# anywhere in this file before this change (previously exercised only by
# one-shot driver scripts / pytest -- see CLAUDE.md audit).

def _close_tick(adapter: WorldAdapter) -> None:
    try:
        import domains.reflective_faculty as rf
    except ImportError:
        return
    try:
        rf.close_experiment_loop(adapter)
    except Exception as e:  # noqa: BLE001 -- never let a close hiccup kill the tick loop
        log(f"close-experiment-loop error (continuing): {e}")


# --- standing-world hook (a genuine perceiving world; opt-in via --world-every) --
# Gives the daemon agent something to actually PERCEIVE on a cadence, between
# chat/voice turns: one short offline-ARC episode via scripts/arc_run.py's
# `run_episode` -- the SAME machinery arc_run.py's own CLI and every self-
# experiment driver script in this repo already uses. Every decision inside the
# episode (which action, what's salient, what to self-report) is the agent's own
# seeded move-space/perception/goal-derivation rules (arc_run.MS_CHOOSE_EXPAND et
# al., installed once); this hook only re-runs the same reset -> perceive -> tick
# loop those rules already drive. Its purpose in THIS loop is narrow and honest:
# it supplies the `ag -knows-> wi(Game)` fact the mint rule's 'send' grounding
# reads (WHICH world/game to dispatch a self-experiment to), and -- as a genuine
# bonus, not asserted by the autonomy gate -- gives seeds/self_fuel_drive.json's
# mint_curiosity_goal a real chance to fire on the world's own unexplained
# features. It does NOT itself decide to test a hypothesis about the agent --
# that is still _concern_tick's + the agent's own mint rule's business.

def _setup_world_ctx(adapter: WorldAdapter, n_actions: int):
    """Best-effort one-time setup: the speech + self-describe faculty and the
    tick-fired move-space EXPAND rule arc_run.boot_agent() installs on a fresh
    ARC-playing agent. Returns None (and logs) if ARC-play deps are unavailable
    -- the daemon runs fine without the standing world, same as --voice."""
    try:
        import arc_run
    except Exception as e:  # noqa: BLE001 -- ARC play deps may be absent
        log(f"world-tick setup skipped: {type(e).__name__}: {e}")
        return None
    try:
        existing = {r.get("name") for r in adapter.inner.export_rules()}
    except Exception:  # noqa: BLE001
        existing = set()
    if arc_run.MS_CHOOSE_EXPAND.get("name") not in existing:
        try:
            adapter.inner.add_rule(arc_run.MS_CHOOSE_EXPAND)
        except Exception as e:  # noqa: BLE001
            log(f"world-tick MS_CHOOSE_EXPAND install skipped: {e}")
    try:
        prod = arc_run._setup_speech(adapter)
        describe_ctx = arc_run.setup_describe(adapter, prod)
    except Exception as e:  # noqa: BLE001
        log(f"world-tick speech/describe setup skipped: {e}")
        prod, describe_ctx = None, None
    return {"arc_run": arc_run, "prod": prod, "describe_ctx": describe_ctx, "n_actions": n_actions}


def _world_tick(adapter: WorldAdapter, world_ctx) -> None:
    if world_ctx is None:
        return
    try:
        from worlds.arc import ArcWorld
        from arc3_env import NavigateEnv
        world_ctx["arc_run"].run_episode(
            adapter, ArcWorld(NavigateEnv()), world_ctx["n_actions"], "cells",
            world_ctx["prod"], world_ctx["describe_ctx"])
    except Exception as e:  # noqa: BLE001 -- never let a world hiccup kill the tick loop
        log(f"world-tick error (continuing): {e}")


# --- voice hook (best-effort; mirrors the fetch/browse hooks) ----------------
# A capture THREAD (started once in main(), if --voice) runs
# domains.voice_world.capture_utterances_from_mic and only pushes VAD-closed
# utterance arrays onto a plain queue.Queue -- no graph access, no decisions.
# ALL graph mutation happens here, under AGENT_LOCK, on the tick loop's own
# thread: ingest -> tick -> reply, exactly the shape the other hooks use.

class VoiceCtx:
    """Bookkeeping for the optional mic capture thread. Plain data, no agent
    decisions — mirrors DaemonState's role for the voice slice specifically."""

    def __init__(self, vw, queue, thread, stop, speak: bool, voice_variant: str):
        self.vw = vw
        self.queue = queue
        self.thread = thread
        self.stop = stop
        self.speak = speak
        self.voice_variant = voice_variant


def _start_voice_capture(adapter: WorldAdapter, device, speak: bool, voice_variant: str):
    """Boot the VoiceWorld adapter + start the mic capture thread. Raises if the
    capture device can't be opened (caller decides whether that's fatal)."""
    import queue as _queue
    import threading as _threading
    import domains.voice_world as voice_world
    vw = voice_world.VoiceWorld(adapter, lexicon_name="default")
    q: _queue.Queue = _queue.Queue()
    stop = _threading.Event()
    started = _threading.Event()
    error: list[BaseException] = []

    def _run() -> None:
        try:
            for utt in voice_world.capture_utterances_from_mic(
                    fs=voice_world.FS, device=device, stop_event=stop):
                started.set()
                q.put(utt)
        except BaseException as e:  # noqa: BLE001 -- surface to the starting thread once
            error.append(e)
            started.set()

    t = _threading.Thread(target=_run, daemon=True)
    t.start()
    started.wait(timeout=2.0)   # give arecord a moment to fail fast on a bad device
    if error and not q.qsize():
        raise error[0]
    return VoiceCtx(vw, q, t, stop, speak, voice_variant)


def _voice_tick(state: DaemonState, voice_ctx: "VoiceCtx | None") -> None:
    """Drain every mic utterance captured since the last tick: ingest -> tick ->
    reply, publishing each turn as a `chat` SSE event (same event the socket/HTTP
    chat handlers publish) so a web UI shows the spoken conversation too. Caller
    holds AGENT_LOCK. No ASR: `text` is a placeholder describing the utterance
    (see domains/voice_world.py for why — recognition is graph-native sign
    matching, not a transcript)."""
    if voice_ctx is None:
        return
    try:
        import domains.voice_world as voice_world
    except ImportError:
        return
    from queue import Empty as _Empty
    drained = 0
    while True:
        try:
            samples = voice_ctx.queue.get_nowait()
        except _Empty:
            break
        drained += 1
        try:
            results = voice_ctx.vw.hear(samples, fs=voice_world.FS)
            state.adapter.tick()
            dur_s = len(samples) / float(voice_world.FS)
            for r in results:
                reply = voice_ctx.vw.reply_for(r["message"])
                heard = voice_ctx.vw.grounded_words_for(r["message"])
                text = f"[spoken utterance #{drained}, {dur_s:.2f}s, sign={r['sign']}]"
                state.publish_event({"type": "chat", "text": text, "reply": reply, "heard": heard})
                record_chat_turn(state, text, reply, heard=heard)
                if voice_ctx.speak and reply:
                    try:
                        voice_ctx.vw.speak(reply, variant=voice_ctx.voice_variant, play=True)
                    except Exception as e:  # noqa: BLE001 -- playback failure isn't fatal
                        log(f"voice speak error (continuing): {e}")
        except Exception as e:  # noqa: BLE001 -- never let a bad utterance kill the tick loop
            log(f"voice ingest error (continuing): {e}")
    if drained:
        state.dirty.set()   # ingest/replies grew the graph; tick again promptly


# --- graph-selected host actions ---------------------------------------------

def _teacher_tick(adapter: WorldAdapter) -> None:
    """Optional structured-teacher mechanism supplied by the teacher slice.

    The dispatch label and the ``TeacherRequest`` demand are graph data in the
    supervisory seed.  This import/lookup is only a capability registry, in
    the same sense as the existing composer dispatch registry.
    """
    try:
        from domains.teacher_dispatch import scan_and_teach
    except ImportError:
        return
    scan_and_teach(adapter)


def _embodied_trial_tick(state: DaemonState) -> None:
    """Mechanically enact graph-selected embodied work through an attached world."""
    executor = state.embodied_trial_executor
    if executor is None:
        raise RuntimeError("no embodied trial world is attached")
    adapter = state.adapter
    # The generic executor has already marked exactly one selected request as
    # running.  Forward its graph-authored source identity to the transducer;
    # the host neither searches for nor chooses an embodied trial.
    selected_source = None
    for request in adapter.s.nodes("HostActionRequest"):
        attrs = adapter.s.node(request)["attrs"]
        if (attrs.get("action") == "embodied_trial"
                and attrs.get("status") == "running"):
            selected_source = attrs.get("source")
            break
    if selected_source is None or not adapter.inner.has_node(selected_source):
        raise RuntimeError("selected embodied trial has no live graph source")
    executor(adapter, selected_source)


def attach_pybullet_humanoid_trial_world(
    state: DaemonState,
    *,
    protocol_path: str | Path,
    seed: int | None = None,
) -> None:
    """Attach the optional real humanoid body as a mechanical host capability.

    Construction reads only declared simulator mechanics.  The resulting
    callable accepts a graph-selected ``EmbodiedExternalTrialRequest`` and
    publishes measured integer evidence; it contains no action selection.
    """
    from domains.pybullet_humanoid_trial_transducer import (
        PyBulletHumanoidTrialTransducer,
    )

    transducer = PyBulletHumanoidTrialTransducer.from_protocol(
        protocol_path, seed=seed,
    )
    state.embodied_trial_executor = transducer
    state.embodied_trial_closer = transducer.close
    # Mechanical body/world ingestion.  Higher-level body schema, world,
    # affordance and developmental-episode recognition is graph policy in the
    # embodied_body_ingest seed and runs on the next ordinary substrate tick.
    transducer.publish_body_world_capabilities(state.adapter)


def _attach_default_libraries(adapter: WorldAdapter, *, enable_llm: bool) -> dict:
    """Attach local teachers every daemon boot and Terra when permitted.

    Library availability is an observed capability fact, not a cognitive
    decision.  Dictionary/Wikipedia remain before Terra in the teacher chain;
    Terra is only exposed as the evidence transport consumed by a graph-picked
    TeacherRequest.
    """
    from domains.libraries import attach_libraries
    return attach_libraries(adapter, enable_llm=enable_llm, log=log)


def _host_action_handlers(state: DaemonState, world_ctx):
    """Mechanical action-name → host capability registry.

    The graph selected the action before this function is reached.  No source
    node, score, cadence, or priority is inspected here.
    """
    adapter = state.adapter
    return {
        "dispatch": lambda: _dispatch_tick(adapter, state.runs_dir),
        "fetch": lambda: _fetch_tick(adapter),
        "search": lambda: _search_tick(adapter, state),
        "causal_retrieval": lambda: _search_tick(adapter, state),
        "detail": lambda: _detail_tick(adapter, state),
        "browse": lambda: _browse_tick(adapter),
        "imagine": lambda: _imagine_tick(adapter),
        "self_correct": lambda: _self_correct_tick(adapter),
        "concern": lambda: _concern_tick(adapter),
        "close": lambda: _close_tick(adapter),
        "steer": lambda: _steer_tick(adapter, state),
        "study": lambda: _study_tick(adapter),
        "teacher": lambda: _teacher_tick(adapter),
        "embodied_trial": lambda: _embodied_trial_tick(state),
        "auto_approve": lambda: _auto_approve_tick(adapter),
        "collapse": lambda: _collapse_tick(adapter),
        "world": lambda: _world_tick(adapter, world_ctx),
    }


def _int_attr(attrs: dict, key: str) -> int:
    """Mechanical serialisation boundary for supervisory integer fields."""
    try:
        return int(attrs.get(key, 0))
    except (TypeError, ValueError):
        return 0


def _complete_pending_search_host_actions(state: DaemonState) -> int:
    """Join completed I/O and mutate the graph only on the daemon owner thread."""
    from domains.fetch_dispatch import commit_detail_payload
    from domains.topic_grounding import (commit_ground_payload,
                                         commit_search_candidate_payloads,
                                         commit_selected_search)

    adapter, sub, native = state.adapter, state.adapter.s, state.adapter.inner
    completed = 0
    for host_id, pending in list(state.pending_search_host_actions.items()):
        jobs = pending["jobs"]
        if not all(job["future"].done() for job in jobs):
            # Preserve the graph-selected request order at the mutation
            # boundary. I/O remains concurrent, but committing a later
            # conversation's result before an earlier outstanding retrieval
            # can change shared discourse focus across identical replays.
            # Futures are bounded; the owner never waits here under AGENT_LOCK.
            break
        commit_errors = []
        candidate_jobs = []
        fallback_queries = []
        for job in jobs:
            req = srs.NodeID(job["request_id"])
            if not native.has_node(req):
                continue
            attrs = sub.node(req)["attrs"]
            token_attr = {"ground": "ground_io_token", "detail": "detail_io_token",
                          "causal": "causal_io_token"}.get(
                job["kind"], "search_io_token")
            query_attr = ("topic" if job["kind"] in {"detail", "causal"}
                          else "query")
            if (attrs.get("status") != "running"
                    or attrs.get(token_attr) != job["token"]
                    or attrs.get(query_attr) != job["query"]):
                # The graph changed/superseded the request while I/O ran; its
                # result is stale and must not become graph evidence.
                continue
            try:
                payloads = job["future"].result()
            except Exception as exc:  # noqa: BLE001 -- expose honest failure
                native.set_attr(req, "status", "failed")
                if job["kind"] == "search":
                    native.set_attr(req, "epistemic_status", "search_failed")
                    native.set_attr(req, "evidence_path",
                                    "SearchRequest -> retrieval_attempt -> exception")
                native.set_attr(req, "error", f"{type(exc).__name__}: {exc}")
                if job["kind"] == "detail":
                    commit_errors.append(exc)
                continue
            if job["kind"] == "causal":
                try:
                    from domains.causal_retrieval import commit_causal_candidate_payloads
                    commit_causal_candidate_payloads(
                        adapter, req, payloads, io_token=job["token"])
                except Exception as exc:  # noqa: BLE001 -- owner records failure
                    native.set_attr(req, "status", "failed")
                    native.set_attr(req, "error", f"{type(exc).__name__}: {exc}")
                    commit_errors.append(exc)
                continue
            if job["kind"] == "detail":
                try:
                    if not payloads:
                        raise RuntimeError("no detail chunks")
                    commit_detail_payload(adapter, job["query"], payloads)
                    native.set_attr(req, "status", "done")
                    native.set_attr(req, "error", "")
                except Exception as exc:  # noqa: BLE001 -- owner records failure
                    native.set_attr(req, "status", "failed")
                    native.set_attr(req, "error", f"{type(exc).__name__}: {exc}")
                    commit_errors.append(exc)
                continue
            if job["kind"] == "ground":
                try:
                    answer = commit_ground_payload(
                        adapter, job["query"], job["aspect"], payloads)
                except Exception as exc:  # noqa: BLE001
                    native.set_attr(req, "status", "failed")
                    native.set_attr(req, "error", f"{type(exc).__name__}: {exc}")
                    continue
                if answer:
                    native.set_attr(req, "answer", str(answer)[:4000])
                    native.set_attr(req, "status", "done")
                    for search in sub.nodes("SearchRequest"):
                        if not native.has_node(search):
                            continue
                        sa = sub.node(search)["attrs"]
                        if (sa.get("status") in ("requested", "running", "io_pending")
                                and str(sa.get("query") or "").strip().lower()
                                == job["query"].lower()):
                            native.set_attr(search, "status", "superseded")
                            native.add_edge_unchecked(search, "superseded_by", req)
                else:
                    native.set_attr(req, "status", "failed")
                    native.set_attr(req, "error", "no answer")
                    fallback_queries.append(job["query"])
                continue
            try:
                count = commit_search_candidate_payloads(adapter, req, payloads)
            except Exception as exc:  # noqa: BLE001 -- graph owner records failure
                native.set_attr(req, "status", "failed")
                native.set_attr(req, "epistemic_status", "search_failed")
                native.set_attr(req, "evidence_path",
                                "SearchRequest -> retrieval_attempt -> commit_exception")
                native.set_attr(req, "error", f"{type(exc).__name__}: {exc}")
                commit_errors.append(exc)
                continue
            if count:
                native.set_attr(req, "status", "candidates_ready")
                candidate_jobs.append((job, req))
            else:
                native.set_attr(req, "status", "failed")
                native.set_attr(req, "epistemic_status", "unknown")
                native.set_attr(req, "evidence_path",
                                "SearchRequest -> retrieval_attempt -> no_candidates")
                native.set_attr(req, "error", "no candidates")

        try:
            if candidate_jobs:
                adapter.comprehend()
            for job, req in candidate_jobs:
                ans = commit_selected_search(adapter, req, job["query"])
                if ans:
                    native.set_attr(req, "answer", str(ans)[:4000])
                    native.set_attr(req, "status", "done")
                    native.set_attr(req, "epistemic_status", "supported")
                    native.set_attr(req, "error", "")
                else:
                    attrs = sub.node(req)["attrs"]
                    candidates = [sub.node(c)["attrs"] for c in
                                  native.neighbours(req, "has_candidate")
                                  if sub.has_node(c)]
                    epistemic = ("contradicted" if any(
                        c.get("epistemic_status") == "contradicted"
                        for c in candidates) else "unknown")
                    native.set_attr(req, "status", "failed")
                    native.set_attr(req, "epistemic_status", epistemic)
                    native.set_attr(req, "evidence_path",
                                    "SearchRequest -> has_candidate -> verification -> no_supported_candidate")
                    native.set_attr(req, "error", "no verified candidate")
        except Exception as exc:  # noqa: BLE001
            commit_errors.append(exc)
            for _, req in candidate_jobs:
                if native.has_node(req):
                    native.set_attr(req, "status", "failed")
                    native.set_attr(req, "epistemic_status", "search_failed")
                    native.set_attr(req, "evidence_path",
                                    "SearchRequest -> graph_commit -> exception")
                    native.set_attr(req, "error", f"{type(exc).__name__}: {exc}")

        for job in jobs:
            req = srs.NodeID(job["request_id"])
            if not native.has_node(req):
                continue
            attrs = sub.node(req)["attrs"]
            token_attr = {"ground": "ground_io_token", "detail": "detail_io_token",
                          "causal": "causal_io_token"}.get(
                job["kind"], "search_io_token")
            if (attrs.get(token_attr) == job["token"]
                    and attrs.get("status") not in ("running", "candidates_ready")):
                native.set_attr(req, token_attr, None)

        host = srs.NodeID(host_id)
        if (not native.has_node(host)
                or sub.node(host)["attrs"].get("status") != "io_pending"
                or sub.node(host)["attrs"].get("search_io_token")
                != pending["host_token"]):
            # A removed/recycled parent action must not strand valid child
            # requests in `running`; release only jobs still carrying their
            # own exact tokens, then let native supervision mint/serve again.
            for job in jobs:
                req = srs.NodeID(job["request_id"])
                if not native.has_node(req):
                    continue
                token_attr = {"ground": "ground_io_token", "detail": "detail_io_token",
                              "causal": "causal_io_token"}.get(
                    job["kind"], "search_io_token")
                attrs = sub.node(req)["attrs"]
                if (attrs.get("status") == "running"
                        and attrs.get(token_attr) == job["token"]):
                    native.set_attr(req, "status", "requested")
                    native.set_attr(req, token_attr, None)
                    state.dirty.set()
            del state.pending_search_host_actions[host_id]
            continue
        host_attrs = pending["attrs"]
        # A graph-selected generic search action stages matching specific
        # grounding first. If that grounding honestly misses, reuse the same
        # selected action for its generic SearchRequest fallback; the graph's
        # mint-once guard correctly will not mint a second action for the
        # already-consumed source request.
        source = host_attrs.get("source")
        source_id = (int(source.value) if hasattr(source, "value")
                     else int(source) if source is not None else None)
        source_node = srs.NodeID(source_id) if source_id is not None else None
        if (fallback_queries and source_node is not None
                and native.has_node(source_node)
                and sub.node(source_node)["type"] == "SearchRequest"):
            source_attrs = sub.node(source_node)["attrs"]
            if (source_attrs.get("status") == "requested"
                    and str(source_attrs.get("query") or "").strip()
                    in {str(query).strip() for query in fallback_queries}):
                # Free this completed grounding job's bounded I/O slot before
                # staging the fallback, then restore the same pending parent
                # action if a fallback future was submitted.
                del state.pending_search_host_actions[host_id]
                state.active_host_action_source = source_node
                try:
                    fallback_stage = _start_search_candidate_io(adapter, state)
                finally:
                    state.active_host_action_source = None
                if fallback_stage["jobs"]:
                    pending["jobs"] = fallback_stage["jobs"]
                    state.pending_search_host_actions[host_id] = pending
                    continue
                state.pending_search_host_actions[host_id] = pending
        action = pending["action"]
        outcome = "failed" if commit_errors else "done"
        error = (f"{type(commit_errors[0]).__name__}: {commit_errors[0]}"
                 if commit_errors else "")
        native.set_attr(host, "status", outcome)
        native.set_attr(host, "search_io_token", None)
        for task in pending["tasks"]:
            if native.has_node(task):
                native.set_attr(task, "status", outcome)
        receipt = sub.add_node("HostActionReceipt", {
            "action": action, "status": outcome,
            "urgency": _int_attr(host_attrs, "urgency"),
            "residual": _int_attr(host_attrs, "residual"),
            "estimated_cost": _int_attr(host_attrs, "estimated_cost"),
            "deadline": _int_attr(host_attrs, "deadline"),
            "logical_time": int(state.ticks), "error": error,
        })
        native.add_edge_unchecked(host, "has_receipt", receipt)
        state.host_actions_completed += 1
        state.last_host_action = action
        state.last_host_action_outcome = outcome
        del state.pending_search_host_actions[host_id]
        completed += 1
    return completed


def _execute_host_action_requests(state: DaemonState, world_ctx=None) -> int:
    """Execute graph-requested host work and write a receipt for every request.

    This deliberately scans only ``HostActionRequest{status:requested}``.
    The supervising graph rules decide whether a demand merits a request and
    carry its integer urgency/residual/cost/deadline coordinates.  The daemon
    merely invokes the selected external mechanism, then records completion or
    an honest capability/error receipt.
    """
    try:
        from evaluation.p0a.legacy_io_guard import deny_direct_io
        deny_direct_io("raw.host.dispatch")
    except ImportError:
        pass
    adapter = state.adapter
    sub, native = adapter.s, adapter.inner
    handlers = _host_action_handlers(state, world_ctx)
    completed = _complete_pending_search_host_actions(state)
    for request in list(sub.nodes("HostActionRequest")):
        if not native.has_node(request):
            continue
        attrs = sub.node(request)["attrs"]
        if attrs.get("status") != "requested":
            continue
        action = str(attrs.get("action") or "")
        receipt_attrs = dict(attrs)
        handler = handlers.get(action)
        outcome = "done"
        error = ""
        native.set_attr(request, "status", "running")
        tasks = list(native.neighbours(request, "scheduled_as"))
        for task in tasks:
            if native.has_node(task):
                native.set_attr(task, "status", "host_running")
        if handler is None:
            outcome = "unavailable"
            error = f"no host capability registered for {action!r}"
        else:
            try:
                state.active_host_action_source = attrs.get("source")
                result = handler()
                state.active_host_action_source = None
                if isinstance(result, dict) and result.get("host_action_deferred"):
                    native.set_attr(request, "status", "requested")
                    for task in tasks:
                        if native.has_node(task):
                            native.set_attr(task, "status", "host_requested")
                    continue
                if isinstance(result, dict) and result.get("host_action_pending"):
                    host_token = f"host:{int(request.value)}:{time.monotonic_ns()}"
                    native.set_attr(request, "status", "io_pending")
                    native.set_attr(request, "search_io_token", host_token)
                    for task in tasks:
                        if native.has_node(task):
                            native.set_attr(task, "status", "io_pending")
                    state.pending_search_host_actions[int(request.value)] = {
                        "action": action, "attrs": receipt_attrs, "tasks": tasks,
                        "jobs": result["jobs"], "host_token": host_token,
                    }
                    continue
            except Exception as e:  # noqa: BLE001 -- write failure into graph, keep daemon alive
                state.active_host_action_source = None
                outcome = "failed"
                error = f"{type(e).__name__}: {e}"
                log(f"host action {action!r} failed (continuing): {error}")
        native.set_attr(request, "status", outcome)
        for task in tasks:
            if native.has_node(task):
                native.set_attr(task, "status", "done" if outcome == "done" else outcome)
        receipt = sub.add_node("HostActionReceipt", {
            "action": action,
            "status": outcome,
            "urgency": _int_attr(attrs, "urgency"),
            "residual": _int_attr(attrs, "residual"),
            "estimated_cost": _int_attr(attrs, "estimated_cost"),
            "deadline": _int_attr(attrs, "deadline"),
            "logical_time": int(state.ticks),
            "error": error,
        })
        native.add_edge_unchecked(request, "has_receipt", receipt)
        state.host_actions_completed += 1
        state.last_host_action = action
        state.last_host_action_outcome = outcome
        completed += 1
    return completed


# --- tick loop -----------------------------------------------------------------

_IDLE_KEEPALIVE_S = 1.0  # tick at least this often even with no explicit signal,
                          # so time-independent reflex/dispatch work can still progress


def tick_loop(state: DaemonState, stop: threading.Event, hz: float,
              dispatch_every: int, runs_dir: str, fetch_every: int = 0,
              browse_every: int = 0, voice_ctx: "VoiceCtx | None" = None,
              voice_every: int = 0, concern_every: int = 0, close_every: int = 0,
              world_every: int = 0, world_ctx=None,
              auto_approve_every: int = 0, imagine_every: int = 0, collapse_every: int = 0,
              self_correct_every: int = 0, search_every: int = 0,
              detail_every: int = 0, steer_every: int = 0, study_every: int = 0,
              evaluation_action_client=None) -> None:
    """Event/request-driven graph cognition loop.

    The ``*_every`` arguments are retained only as deprecated invocation
    compatibility.  They no longer select work: graph rules mint and release
    HostActionRequests, and this loop mechanically executes those requests.
    """
    interval = 1.0 / max(hz, 1.0)
    last_tick = 0.0
    legacy = {
        "dispatch": dispatch_every, "fetch": fetch_every, "search": search_every,
        "detail": detail_every, "browse": browse_every, "concern": concern_every,
        "close": close_every, "steer": steer_every, "study": study_every,
        "imagine": imagine_every, "collapse": collapse_every,
        "self_correct": self_correct_every, "auto_approve": auto_approve_every,
        "world": world_every, "voice": voice_every,
    }
    supplied = [name for name, value in legacy.items() if value]
    log(f"tick loop running (up to {hz:.0f} Hz; graph-selected host actions)")
    if supplied:
        log("deprecated cadence flags ignored by cognition: " + ", ".join(supplied))
    while not stop.is_set():
        woke = state.dirty.wait(timeout=interval)
        now = time.monotonic()
        if woke:
            state.dirty.clear()
        elif now - last_tick < _IDLE_KEEPALIVE_S:
            continue   # nothing to do yet and not due for the idle keepalive
        with AGENT_LOCK:
            state.tick_active = True
            progressed = 0
            try:
                budget, quantum = _async_cycle_budget(state.adapter)
                if quantum is None:
                    progressed = state.adapter.tick()
                else:
                    progressed = state.adapter.tick(max_steps=quantum)
                    _record_async_cycle_consumption(
                        state.adapter, budget, quantum, progressed
                    )
                # ``run_cycle(default)`` prioritises the default-mode
                # schedule and can defer a newly ingested instruction rule
                # population indefinitely.  A pending turn is graph evidence
                # that explicitly admits its bounded rule pass; no reply is
                # selected here.
                if state.pending_turns:
                    progressed += int(state.adapter.comprehend())
                    progressed += int(
                        state.adapter.settle_post_comprehension_authority(
                            list(state.pending_turns)))
                    import substrate_rs as srs
                    completed_turns = []
                    for turn_id, text in state.pending_turns.items():
                        reply = state.adapter.release_graph_selected_response(
                            srs.NodeID(turn_id))
                        terminal_status = (
                            "reply_released" if reply is not None else
                            state.adapter.graph_turn_reply_outcome(turn_id)
                        )
                        if terminal_status in {
                                "expected", "unrepresented", "reply_ready"}:
                            continue
                        if terminal_status == "explicit_error":
                            reply = state.adapter.graph_turn_reply(turn_id)
                        completed_turns.append(turn_id)
                        completion = {
                            "type": "chat_completed", "text": text,
                            "turn_id": turn_id,
                            "status": (
                                "error" if terminal_status == "explicit_error"
                                else "completed" if reply is not None
                                else "no_response_expected"),
                            "reply": reply,
                        }
                        state.publish_event(completion)
                        if reply is not None and terminal_status != "explicit_error":
                            record_chat_turn(state, text, reply, turn_id=turn_id,
                                             reply_from="agent")
                    for turn_id in completed_turns:
                        state.pending_turns.pop(turn_id, None)
                state.last_tick_error = ""
            except Exception as e:  # noqa: BLE001 -- never let one bad tick kill the loop
                state.last_tick_error = f"{type(e).__name__}: {e}"
                log(f"tick error (continuing): {e}")
            finally:
                state.tick_active = False
                state.last_tick_mono = time.monotonic()
                state.node_count_snapshot = state.adapter.s.node_count()
            state.ticks += 1
        last_tick = now
        with AGENT_LOCK:
            if evaluation_action_client is None:
                completed = _execute_host_action_requests(state, world_ctx)
            else:
                # Evaluation owns a separate, broker-only graph proposal pump.
                # It never builds a legacy handler registry or world context.
                from evaluation.p0a.graph_proposals import execute_evaluation_graph_proposals
                completed = execute_evaluation_graph_proposals(
                    state.adapter, evaluation_action_client, logical_time=state.ticks)
            # Voice is an external queue: draining it on a wake is mechanical
            # event handling, not a graph-cognitive periodic policy.
            if voice_ctx is not None and evaluation_action_client is None:
                _voice_tick(state, voice_ctx)
        if completed:
            # A host receipt is new grounded evidence.  It is the only
            # mechanical continuation emitted here: a bounded rewrite count
            # says that a quantum was consumed, not that the graph has an
            # unfinished consequence.  Treating ``progressed >= quantum`` as
            # continuation made one-unit quanta spin indefinitely, repeatedly
            # minting planning epochs without a new observation.  Further
            # cognition is instead woken by this receipt, a transport event,
            # or an explicit graph-owned host action released from that
            # receipt.
            state.dirty.set()
    # Futures are process-local. Return their graph-owned requests to the
    # scheduler before the final checkpoint so restart can safely resume them.
    with AGENT_LOCK:
        for host_id, pending in list(state.pending_search_host_actions.items()):
            for job in pending["jobs"]:
                job["future"].cancel()
                req = srs.NodeID(job["request_id"])
                token_attr = {"ground": "ground_io_token", "detail": "detail_io_token",
                              "causal": "causal_io_token"}.get(
                    job["kind"], "search_io_token")
                if (state.adapter.inner.has_node(req)
                        and state.adapter.s.node(req)["attrs"].get(
                            token_attr) == job["token"]):
                    state.adapter.inner.set_attr(req, "status", "requested")
                    state.adapter.inner.set_attr(req, token_attr, None)
            host = srs.NodeID(host_id)
            if state.adapter.inner.has_node(host):
                state.adapter.inner.set_attr(host, "status", "requested")
                state.adapter.inner.set_attr(host, "search_io_token", None)
                for task in state.adapter.inner.neighbours(host, "scheduled_as"):
                    if state.adapter.inner.has_node(task):
                        state.adapter.inner.set_attr(task, "status", "host_requested")
        state.pending_search_host_actions.clear()
    state.search_io_executor.shutdown(wait=False, cancel_futures=True)
    state.runtime_state = "stopped"
    log("tick loop stopped")


def monitor_loop(state: DaemonState, stop: threading.Event,
                 status_every: float = 5.0, session_every: float = 2.0) -> None:
    """Publishes periodic `status` SSE events and `session_update` events on
    Experiment status changes (a mechanical before/after diff of list_sessions,
    not a decision)."""
    last_status = 0.0
    last_session = 0.0
    while not stop.is_set():
        now = time.monotonic()
        if now - last_status >= status_every:
            last_status = now
            state.publish_event({"type": "status", **_status_dict(state)})
        if now - last_session >= session_every:
            last_session = now
            try:
                sessions = list_sessions(state.adapter)
            except Exception:  # noqa: BLE001
                sessions = []
            for sess in sessions:
                sid = sess["id"]
                prev = state._sessions_prev.get(sid)
                if prev != sess["status"]:
                    state._sessions_prev[sid] = sess["status"]
                    state.publish_event({"type": "session_update", "id": sid,
                                         "status": sess["status"]})
            try:
                pipe = list_self_improvement(state.adapter)
                digest = tuple((i["self_concern_id"], i["stage"], i["experiment_id"])
                               for i in pipe.get("items") or [])
                if digest != state._improvement_prev:
                    state._improvement_prev = digest
                    state.publish_event({"type": "self_improvement_update", **pipe})
            except Exception:  # noqa: BLE001
                pass
            # Autonomy narration: a concluded pipeline transition (Experiment
            # done/failed, Adoption minted, promoted concern processed) becomes
            # ONE agent-initiated chat turn per pass — mechanical read of
            # un-narrated nodes, marker on the node so a restart never repeats.
            try:
                _narrate_tick(state)
            except Exception:  # noqa: BLE001
                pass
        stop.wait(0.5)


# --- Unix socket bus: scripts/jbw_talk.py's exact protocol -------------------
#
# jbw_talk.py: opens a fresh AF_UNIX SOCK_STREAM connection per message,
# writes "<line-with-newlines-replaced-by-spaces>\n", reads exactly ONE line
# back (readline()), and expects the connection to be reusable for a REPL (a
# NEW connection each turn). This handler matches that exactly: one line in,
# one line out.

def _ingest_daemon_chat_turn(state: DaemonState, text: str) -> int:
    """Prepare connected content, then publish one pending daemon turn.

    The pre-pass is a mechanical seed/dependency lookup. It must precede text
    parsing and native arbitration, matching ``WorldAdapter.converse()``;
    full-profile agents have no connected-profile state and make it a no-op.
    """
    try:
        prepass_conversation_turn(state.adapter, text)
    except Exception as exc:  # keep ingress available; unresolved stays honest
        log(f"conversation content pre-pass unavailable: {type(exc).__name__}: {exc}")
    speech_act = state.adapter.classify_speech_act(text)
    inbound = state.adapter.ingest_turn(text, speech_act=speech_act)
    turn_id = int(inbound.value if hasattr(inbound, "value") else inbound)
    state.pending_turns[turn_id] = text
    return turn_id

def _handle_conn(conn: socket.socket, state: DaemonState) -> None:
    with conn, conn.makefile("rwb", buffering=0) as f:
        for raw in f:
            text = raw.decode("utf-8", "replace").rstrip("\n")
            if not text:
                continue
            turn_id = None
            if text.startswith("poll "):
                try:
                    import substrate_rs as srs
                    turn_id = int(text.split(None, 1)[1])
                    with AGENT_LOCK:
                        mid = srs.NodeID(turn_id)
                        reply = state.adapter.graph_turn_reply(mid)
                        expectation = state.adapter.graph_turn_reply_expectation(mid)
                    if reply is not None:
                        result = reply
                    elif expectation["status"] == "not_expected":
                        result = f"no_response_expected:{turn_id}"
                    else:
                        result = f"pending:{turn_id}"
                except Exception as e:  # noqa: BLE001
                    result = f"error: {type(e).__name__}: {e}"
                f.write((result.replace("\n", " ") + "\n").encode("utf-8"))
                continue
            try:
                with AGENT_LOCK:
                    # Publish only mechanical turn evidence here. The daemon's
                    # graph quanta settle cognition and mint the reply later.
                    turn_id = _ingest_daemon_chat_turn(state, text)
                    reply = f"pending:{turn_id}"
                state.dirty.set()
            except Exception as e:  # noqa: BLE001 -- one bad turn shouldn't drop the client
                reply = f"error: {type(e).__name__}: {e}"
            state.publish_event({"type": "chat", "text": text, "reply": reply,
                                 "turn_id": turn_id, "pending": True})
            f.write((reply.replace("\n", " ") + "\n").encode("utf-8"))


def serve_socket(state: DaemonState, sock_path: Path, stop: threading.Event) -> threading.Thread:
    sock_path.parent.mkdir(parents=True, exist_ok=True)
    if sock_path.exists():
        sock_path.unlink()
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(str(sock_path))
    srv.listen(8)
    srv.settimeout(0.5)  # so the accept loop notices `stop`

    def _accept_loop() -> None:
        log(f"socket bus listening on {sock_path}")
        while not stop.is_set():
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=_handle_conn, args=(conn, state), daemon=True).start()
        srv.close()
        try:
            sock_path.unlink()
        except OSError:
            pass
        log("socket bus closed")

    t = threading.Thread(target=_accept_loop, daemon=True)
    t.start()
    return t


# --- HTTP API (stdlib only) ---------------------------------------------------

class JbwHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr, handler_cls, state: DaemonState):
        super().__init__(addr, handler_cls)
        self.state = state


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args) -> None:  # noqa: A003 -- quiet; daemon has its own log()
        pass

    # -- helpers --
    def _json(self, obj: dict, status: int = 200, *, cors: bool = True) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if cors:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_OPTIONS(self) -> None:  # CORS preflight for a browser-based web UI
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # -- routes --
    def do_GET(self) -> None:
        state: DaemonState = self.server.state
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)

        if path == "/api/runtime/status":
            return self._json(_runtime_status_dict(state))
        if path == "/api/status":
            return self._json(_status_dict(state))
        if path == "/api/debug/graph":
            with AGENT_LOCK:
                result = debug_graph_summary(state.adapter)
            return self._json(result, cors=False)
        if path == "/api/debug/graph/nodes":
            with AGENT_LOCK:
                result = debug_graph_nodes(state.adapter, query)
            return self._json(result, cors=False)
        if path.startswith("/api/debug/graph/nodes/"):
            node_id = path[len("/api/debug/graph/nodes/"):]
            with AGENT_LOCK:
                result = debug_graph_node(state.adapter, node_id)
            if result is None:
                return self._json({"ok": False, "error": "not found"}, 404, cors=False)
            return self._json(result, cors=False)
        if path == "/api/debug/graph/edges":
            with AGENT_LOCK:
                result = debug_graph_edges(state.adapter, query)
            return self._json(result, cors=False)
        if path == "/api/debug/graph/rules":
            with AGENT_LOCK:
                result = debug_graph_rules(state.adapter, query)
            return self._json(result, cors=False)
        if path == "/api/embodied/status":
            with AGENT_LOCK:
                result = embodied_learning_status(state.adapter)
            return self._json(result)
        if path == "/api/chat/history":
            return self._json({"ok": True, "turns": list_chat_history(state)})
        if path.startswith("/api/chat/turns/"):
            tid = path[len("/api/chat/turns/"):]
            if tid and "/" not in tid:
                try:
                    import substrate_rs as srs
                    turn_id = int(tid)
                    with AGENT_LOCK:
                        mid = srs.NodeID(turn_id)
                        if not state.adapter.s.has_node(mid):
                            return self._json({"ok": False, "error": "not found"}, 404)
                        reply = state.adapter.graph_turn_reply(mid)
                        expectation = state.adapter.graph_turn_reply_expectation(mid)
                        outcome = state.adapter.graph_turn_reply_outcome(mid)
                        pending = turn_id in state.pending_turns
                except (TypeError, ValueError):
                    return self._json({"ok": False, "error": "invalid turn id"}, 400)
                except Exception as e:  # noqa: BLE001 -- read-only transport boundary
                    return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
                status = ("error" if outcome == "explicit_error" else
                          "completed" if outcome == "reply_ready" else
                          "no_response_expected"
                          if outcome == "not_expected" else "pending")
                result = {"ok": True, "turn_id": turn_id, "status": status,
                          "reply_expected": expectation["status"] == "expected"}
                if reply is not None:
                    result["reply"] = reply
                # Reply/no-response terminality is read from graph evidence;
                # transport bookkeeping is diagnostic and cannot turn a
                # graph-complete turn back into ``pending``.
                result["transport_pending"] = pending
                return self._json(result)
        if path.startswith("/api/chat/turns/") and path.endswith("/trace"):
            tid = path[len("/api/chat/turns/"):-len("/trace")]
            try:
                trace = reply_turn_trace(state.adapter, tid)
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
            if trace is None:
                return self._json({"ok": False, "error": "not found"}, 404)
            return self._json({"ok": True, "trace": trace})
        if path == "/api/sessions":
            try:
                sessions = list_sessions(state.adapter)
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
            return self._json({"ok": True, "sessions": sessions})
        if path.startswith("/api/sessions/") and path.endswith("/restart"):
            return self._json({"ok": False, "error": "use POST"}, 405)
        if path.startswith("/api/sessions/"):
            sid = path[len("/api/sessions/"):]
            try:
                res = session_detail(state.adapter, sid)
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
            if res is None:
                return self._json({"ok": False, "error": "not found"}, 404)
            session, trace = res
            return self._json({"ok": True, "session": session, "trace": trace})
        if path == "/api/proposals":
            try:
                proposals = list_proposals(state.adapter)
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
            return self._json({"ok": True, "proposals": proposals})
        if path.startswith("/api/proposals/"):
            pid_str = path[len("/api/proposals/"):]
            try:
                res = proposal_detail(state.adapter, pid_str)
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
            if res is None:
                return self._json({"ok": False, "error": "not found"}, 404)
            proposal, spec, diff = res
            return self._json({"ok": True, "proposal": proposal, "spec": spec, "diff": diff})
        if path == "/api/auto_approve":
            try:
                with AGENT_LOCK:
                    status = auto_appr.policy_status(state.adapter)
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
            return self._json({"ok": True, **status})
        if path == "/api/self_concerns":
            try:
                scs = list_self_concerns(state.adapter)
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
            return self._json({"ok": True, "self_concerns": scs})
        if path == "/api/self_improvement":
            try:
                pipe = list_self_improvement(state.adapter)
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
            return self._json({"ok": True, **pipe})
        if path == "/api/events":
            return self._sse(state)
        if path.startswith("/api/"):
            return self._json({"ok": False, "error": "not found"}, 404)
        return self._static(path)

    def do_POST(self) -> None:
        state: DaemonState = self.server.state
        path = urllib.parse.urlsplit(self.path).path
        if path == "/api/chat":
            return self._chat(state)
        if path.startswith("/api/chat/turns/") and path.endswith("/flag"):
            tid = path[len("/api/chat/turns/"):-len("/flag")]
            return self._flag_reply(state, tid)
        if path == "/api/enroll":
            return self._enroll(state)
        if path == "/api/ingest":
            return self._ingest(state)
        if path.startswith("/api/proposals/") and path.endswith("/approve"):
            pid_str = path[len("/api/proposals/"):-len("/approve")]
            return self._approve_proposal(state, pid_str)
        if path.startswith("/api/sessions/") and path.endswith("/restart"):
            sid = path[len("/api/sessions/"):-len("/restart")]
            try:
                result = restart_experiment_session(
                    state.adapter, sid, state.runs_dir or os.path.expanduser("~/.jabberwock/runs"))
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
            if result.get("ok"):
                state.dirty.set()
                state.publish_event({"type": "session_update", "id": sid, "status": "requested"})
            return self._json(result, 200 if result.get("ok") else 400)
        if path.startswith("/api/self_concerns/") and path.endswith("/promote"):
            sid = path[len("/api/self_concerns/"):-len("/promote")]
            try:
                result = promote_self_concern(state.adapter, sid)
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
            if result.get("ok"):
                state.dirty.set()
                state.publish_event({"type": "self_concern_update", "id": sid,
                                     "status": "promoted",
                                     "standing_concern": result.get("standing_concern")})
                try:
                    state.publish_event({"type": "self_improvement_update",
                                         **list_self_improvement(state.adapter)})
                except Exception:  # noqa: BLE001
                    pass
            return self._json(result, 200 if result.get("ok") else 400)
        if path.startswith("/api/self_concerns/") and path.endswith("/repromote"):
            sid = path[len("/api/self_concerns/"):-len("/repromote")]
            try:
                result = repromote_self_concern(
                    state.adapter, sid,
                    runs_dir=state.runs_dir or os.path.expanduser("~/.jabberwock/runs"))
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
            if result.get("ok"):
                state.dirty.set()
                state.publish_event({"type": "self_concern_update", "id": sid,
                                     "status": "promoted",
                                     "standing_concern": result.get("standing_concern"),
                                     "repromoted": True})
                try:
                    state.publish_event({"type": "self_improvement_update",
                                         **list_self_improvement(state.adapter)})
                except Exception:  # noqa: BLE001
                    pass
            return self._json(result, 200 if result.get("ok") else 400)
        if path.startswith("/api/standing_concerns/") and path.endswith("/adopt_gamma_production"):
            sid = path[len("/api/standing_concerns/"):-len("/adopt_gamma_production")]
            try:
                result = adopt_gamma_production_standing(state.adapter, sid)
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
            if result.get("ok"):
                state.dirty.set()
                state.publish_event({"type": "standing_concern_update", "id": sid,
                                     "status": "adopted", "triple": result.get("triple")})
                try:
                    state.publish_event({"type": "self_improvement_update",
                                         **list_self_improvement(state.adapter)})
                except Exception:  # noqa: BLE001
                    pass
            return self._json(result, 200 if result.get("ok") else 400)
        if path == "/api/auto_approve":
            return self._set_auto_approve(state)
        return self._json({"ok": False, "error": "not found"}, 404)

    def _chat(self, state: DaemonState) -> None:
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw or b"{}")
        except Exception:
            return self._json({"ok": False, "error": "bad json"}, 400)
        text = (payload.get("text") or "").strip()
        if not text:
            return self._json({"ok": False, "error": "missing text"}, 400)
        turn_id = None
        try:
            with AGENT_LOCK:
                turn_id = _ingest_daemon_chat_turn(state, text)
            state.dirty.set()
        except Exception as e:  # noqa: BLE001
            return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
        state.publish_event({"type": "chat", "text": text, "turn_id": turn_id,
                             "pending": True})
        return self._json({"ok": True, "status": "pending", "turn_id": turn_id})

    def _flag_reply(self, state: DaemonState, turn_id: str) -> None:
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw or b"{}")
        except Exception:
            return self._json({"ok": False, "error": "bad json"}, 400)
        note = (payload.get("note") or "").strip()
        try:
            result = flag_reply_turn(state.adapter, turn_id, note)
        except Exception as e:  # noqa: BLE001
            return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
        if result.get("ok"):
            state.dirty.set()
            if result.get("concern_id") is not None:
                state.publish_event({"type": "self_concern_update",
                                     "id": str(result["concern_id"]),
                                     "status": "noted"})
        return self._json(result, 200 if result.get("ok") else 400)

    def _enroll(self, state: DaemonState) -> None:
        """Caregiver enrollment: {"label", "audio_b64", "filename"?} -> ingest via
        `domains.speech_enrollment.enroll` (mechanical host I/O: decode base64,
        write a temp file, hand off — the grounding decision is entirely the
        agent's graph Rules, see domains/voice_world.py). `filename`'s extension
        (if given) only hints ffmpeg's decode; any container it understands works
        (a browser MediaRecorder webm/opus blob, or a plain wav upload)."""
        import base64
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw or b"{}")
        except Exception:
            return self._json({"ok": False, "error": "bad json"}, 400)
        label = str(payload.get("label") or "").strip()
        audio_b64 = payload.get("audio_b64")
        if not label or not audio_b64:
            return self._json({"ok": False, "error": "missing label or audio_b64"}, 400)
        try:
            audio_bytes = base64.b64decode(audio_b64)
        except Exception:
            return self._json({"ok": False, "error": "bad base64"}, 400)
        suffix = os.path.splitext(str(payload.get("filename") or ""))[1] or ".webm"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        try:
            with open(tmp_path, "wb") as f:
                f.write(audio_bytes)
            import domains.speech_enrollment as speech_enrollment
            with AGENT_LOCK:
                result = speech_enrollment.enroll(state.adapter, tmp_path, label)
            state.dirty.set()
        except Exception as e:  # noqa: BLE001
            return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        state.publish_event({"type": "enrolled", "word": label,
                             "n_exemplars": result["n_exemplars"]})
        return self._json({"ok": True, "word": label, "n_exemplars": result["n_exemplars"]})

    def _ingest(self, state: DaemonState) -> None:
        """File upload ingest: {"filename", "data_b64", "mime"?, "caption"?} ->
        domains.file_ingest.ingest_file (mechanical host I/O)."""
        import base64
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw or b"{}")
        except Exception:
            return self._json({"ok": False, "error": "bad json"}, 400)
        filename = str(payload.get("filename") or "").strip()
        data_b64 = payload.get("data_b64")
        if not filename or not data_b64:
            return self._json({"ok": False, "error": "missing filename or data_b64"}, 400)
        try:
            file_bytes = base64.b64decode(data_b64)
        except Exception:
            return self._json({"ok": False, "error": "bad base64"}, 400)
        suffix = os.path.splitext(filename)[1] or ".bin"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        try:
            with open(tmp_path, "wb") as f:
                f.write(file_bytes)
            import domains.file_ingest as file_ingest
            with AGENT_LOCK:
                result = file_ingest.ingest_file(
                    state.adapter, tmp_path,
                    filename=filename,
                    mime=payload.get("mime"),
                    caption=payload.get("caption"))
            state.dirty.set()
        except Exception as e:  # noqa: BLE001
            return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        out = {"ok": True, "filename": result.get("filename"),
               "mime": result.get("mime"), "kind": result.get("kind"),
               "preview": result.get("preview")}
        if result.get("message_id") is not None:
            out["message_id"] = _nid_value(result["message_id"])
        for key in ("n_mentions", "n_utterances", "page_count", "byte_length", "width", "height"):
            if result.get(key) is not None:
                out[key] = result[key]
        if result.get("document_id") is not None:
            out["document_id"] = _nid_value(result["document_id"])
        if result.get("heard"):
            out["heard"] = result["heard"]
        if result.get("image_ids"):
            out["image_ids"] = [_nid_value(x) for x in result["image_ids"]]
        try:
            state.publish_event({"type": "ingested", **out})
        except Exception:  # noqa: BLE001 -- SSE must not break a successful ingest
            pass
        return self._json(out)

    def _approve_proposal(self, state: DaemonState, pid_str: str) -> None:
        """Human-approved install: domains.proposal_install.install_proposal
        under AGENT_LOCK. Synchronous -- a real cargo/maturin build is
        seconds-to-minutes, which blocks the lock (and so briefly stalls
        chat/tick) for that long. Acceptable: this is a rare, deliberate,
        human-initiated action, not a hot path. requires_restart is always
        surfaced honestly (see domains/proposal_install.py's RESTART
        SEMANTICS) -- this handler never restarts the daemon itself."""
        try:
            with AGENT_LOCK:
                result = install_proposal(state.adapter, pid_str, approver="web")
        except Exception as e:  # noqa: BLE001
            return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
        state.dirty.set()
        status = "installed" if result.get("installed") else (
            "failed" if not result.get("ok") else "pending")
        state.publish_event({"type": "proposal_update", "id": pid_str,
                             "status": status, "installed": bool(result.get("installed"))})
        return self._json({
            "ok": bool(result.get("ok")),
            "installed": bool(result.get("installed")),
            "requires_restart": bool(result.get("requires_restart", True)),
            "reason": result.get("reason"),
            "diagnostics": result.get("diagnostics"),
        })

    def _set_auto_approve(self, state: DaemonState) -> None:
        """Human toggle for the auto-approve SETTING: {"enabled"?, "max_installs_
        per_hour"?, "require_additive"?, "allowed_semantics_kinds"?} -> sets
        domains.auto_approve's AutoApprovePolicy node under AGENT_LOCK and
        publishes the new state on SSE. `paused_until_restart` is deliberately
        NOT accepted here -- see domains/auto_approve.py's module docstring
        for why only a daemon restart may clear that flag (a human re-enabling
        the master switch must not be able to force another install before
        restarting)."""
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw or b"{}")
        except Exception:
            return self._json({"ok": False, "error": "bad json"}, 400)
        fields: dict = {}
        if "enabled" in payload:
            fields["enabled"] = bool(payload["enabled"])
        if "max_installs_per_hour" in payload:
            try:
                fields["max_installs_per_hour"] = int(payload["max_installs_per_hour"])
            except (TypeError, ValueError):
                return self._json({"ok": False, "error": "max_installs_per_hour must be an int"}, 400)
        if "require_additive" in payload:
            fields["require_additive"] = bool(payload["require_additive"])
        if "allowed_semantics_kinds" in payload:
            kinds = payload["allowed_semantics_kinds"]
            if not isinstance(kinds, list) or not all(isinstance(k, str) for k in kinds):
                return self._json({"ok": False, "error": "allowed_semantics_kinds must be a list of strings"}, 400)
            fields["allowed_semantics_kinds"] = kinds
        try:
            with AGENT_LOCK:
                auto_appr.set_policy(state.adapter, **fields)
                status = auto_appr.policy_status(state.adapter)
        except Exception as e:  # noqa: BLE001
            return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
        state.publish_event({"type": "auto_approve_update", **status})
        return self._json({"ok": True, **status})

    def _sse(self, state: DaemonState) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        q = state.add_sse_client()
        try:
            while True:
                try:
                    line = q.get(timeout=15.0)
                except Empty:
                    line = None
                try:
                    if line is not None:
                        self.wfile.write(f"data: {line}\n\n".encode("utf-8"))
                    else:
                        self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    break
        finally:
            state.remove_sse_client(q)

    def _static(self, path: str) -> None:
        if path == "/":
            path = "/index.html"
        rel = path.lstrip("/")
        try:
            target = (WEB_DIR / rel).resolve()
            target.relative_to(WEB_DIR.resolve())
        except (ValueError, OSError):
            return self._json({"ok": False, "error": "forbidden"}, 403)
        if not target.is_file():
            return self._json({"ok": False, "error": "not found"}, 404)
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


def serve_http(state: DaemonState, port: int):
    srv = JbwHTTPServer(("127.0.0.1", port), Handler, state)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    log(f"http listening on http://127.0.0.1:{port}")
    return srv, t


# --- daemon --------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="jabberwock always-on daemon (WorldAdapter)")
    ap.add_argument("--ckpt-dir", default=os.path.expanduser("~/.jabberwock/checkpoints"))
    ap.add_argument("--interval", type=float, default=60.0, help="checkpoint interval (s)")
    ap.add_argument("--tick-hz", type=float, default=20.0, help="agent tick rate")
    ap.add_argument("--keep", type=int, default=10, help="checkpoints to retain")
    ap.add_argument("--seeds", default=DEFAULT_SEED_PROFILE,
                    choices=["full", "chat", "conversation", "embodied"],
                    help="fresh-boot seed set (default: conversation, validated "
                         "cached connected-seed profile); 'full' loads all seeds, "
                         "'chat' is a small smoke profile, and 'embodied' is the "
                         "dependency-closed real-body profile")
    ap.add_argument("--conversation-content-manifest", default=None,
                    help="optional JSON conversation_content_prepass.v1 manifest; "
                         "preloads its connected content groups before the first "
                         "turn and keeps connected loading available for later "
                         "content; set manifest field sealed=true for a fixed "
                         "offline workload. The manifest "
                         "digest is checkpoint-bound; use only with --seeds conversation")
    ap.add_argument("--strict-seed-profile-checkpoints", action="store_true",
                    help="refuse legacy checkpoints without graph-resident "
                         "seed-profile identity; mismatched profiles are always refused")
    ap.add_argument("--socket", default=os.path.expanduser("~/.jabberwock/jbw.sock"),
                    help="Unix socket to talk to the running agent ('' to disable)")
    ap.add_argument("--http-port", type=int, default=8787, help="HTTP API port (127.0.0.1)")
    ap.add_argument("--no-http", action="store_true", help="disable the HTTP API")
    ap.add_argument("--runs-dir", default=os.path.expanduser("~/.jabberwock/runs"),
                    help="passed to domains.experiment_dispatch.scan_and_dispatch, if present")
    # Compatibility-only aliases.  The graph-native supervisor now releases
    # HostActionRequest nodes from actual demand facts; these values do not
    # govern cognition and will be removed after downstream launchers migrate.
    ap.add_argument("--dispatch-every", type=int, default=0,
                    help="deprecated compatibility flag; graph requests dispatch work")
    ap.add_argument("--fetch-every", type=int, default=0,
                    help="deprecated compatibility flag; graph requests fetch work")
    ap.add_argument("--detail-every", type=int, default=0,
                    help="deprecated compatibility flag; graph requests detail work")
    ap.add_argument("--search-every", type=int, default=0,
                    help="deprecated compatibility flag; graph requests search work")
    ap.add_argument("--browse-every", type=int, default=0,
                    help="deprecated compatibility flag; graph requests browse work")
    ap.add_argument("--concern-every", type=int, default=0,
                    help="deprecated compatibility flag; graph requests concern work")
    ap.add_argument("--steer-every", type=int, default=0,
                    help="deprecated compatibility flag; graph requests steering work")
    ap.add_argument("--no-llm", action="store_true",
                    help="hard kill-switch for hosted-LLM assistance: sets OZMA_NO_LLM=1 "
                         "before any teacher chain is constructed (domains/no_llm.py), so "
                         "every LLM link is skipped and chains fall through to their "
                         "honest-miss paths; an attempted hosted call raises loudly")
    ap.add_argument("--study-every", type=int, default=0,
                    help="deprecated compatibility flag; graph requests study work")
    ap.add_argument("--close-every", type=int, default=0,
                    help="deprecated compatibility flag; graph requests experiment closure")
    ap.add_argument("--auto-approve-every", type=int, default=0,
                    help="deprecated compatibility flag; graph may request auto-approval")
    ap.add_argument("--imagine-every", type=int, default=0,
                    help="deprecated compatibility flag; graph requests imagination")
    ap.add_argument("--collapse-every", type=int, default=0,
                    help="deprecated compatibility flag; graph may request collapse prediction")
    ap.add_argument("--self-correct-every", type=int, default=0,
                    help="deprecated compatibility flag; graph requests correction")
    ap.add_argument("--world-every", type=int, default=0,
                    help="deprecated setup flag; a positive value only prepares the world capability")
    ap.add_argument("--world-actions", type=int, default=8,
                    help="actions per standing-world episode (with --world-every > 0)")
    ap.add_argument("--attach-pybullet-humanoid", action="store_true",
                    help="attach the optional real PyBullet humanoid trial transducer; "
                    "graph-selected EmbodiedExternalTrialRequest nodes remain the only "
                    "source of motor authority")
    ap.add_argument("--pybullet-humanoid-protocol",
                    default="protocols/humanoid_developmental_smoke_v1.json",
                    help="external PyBullet humanoid mechanics protocol used with "
                    "--attach-pybullet-humanoid")
    ap.add_argument("--pybullet-humanoid-seed", type=int, default=None,
                    help="optional integer override for the attached PyBullet humanoid world")
    ap.add_argument("--attach-libraries", dest="attach_libraries", action="store_true",
                    default=True,
                    help="compatibility no-op: local teachers attach by default")
    ap.add_argument("--no-attach-libraries", dest="attach_libraries", action="store_false",
                    help="disable library attachment for isolated/offline debugging")
    ap.add_argument("--voice", action="store_true",
                    help="enable mic capture + spoken conversation: a capture thread "
                         "(domains.voice_world.capture_utterances_from_mic, energy-VAD) "
                         "feeds utterances into the tick loop (ingest -> tick -> reply); "
                         "replies are published on /api/events as {type: chat} and, if a "
                         "Piper voice is installed, spoken aloud (see domains/voice_world.py)")
    ap.add_argument("--voice-device", default=None,
                    help="ALSA capture device for arecord -D (default: system default)")
    ap.add_argument("--voice-variant", default="lessac",
                    help="Piper voice variant for spoken replies")
    ap.add_argument("--voice-no-speak", action="store_true",
                    help="with --voice: ingest/reply but never synthesise/play audio")
    ap.add_argument("--voice-every", type=int, default=0,
                    help="deprecated compatibility flag; voice is drained on queue wake")
    ap.add_argument("--once", action="store_true", help="boot, one checkpoint, exit (test)")
    ap.add_argument("--shadow-read", dest="shadow_read", action="store_true",
                    default=False,
                    help="Wave 2 (Deep-Reader): run a light deep-read of every "
                    "chat turn on the live substrate (arm the deictic centre + "
                    "the conversational-aperture reading flow), purely additive "
                    "and recorded on the Message as shadow_* attrs -- comp_* "
                    "stays authoritative for the reply. Disabled by default to "
                    "reduce daemon cold RSS and first-turn latency; use "
                    "--shadow-read to opt in when the resource budget permits.")
    ap.add_argument("--no-shadow-read", dest="shadow_read", action="store_false",
                    help="disable the Wave 2 shadow read (see --shadow-read)")
    args = ap.parse_args()

    ckpt_dir = Path(args.ckpt_dir)
    runs_dir = Path(args.runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)

    if args.no_llm:
        # Must land in the environment BEFORE boot/attach_libraries constructs
        # any teacher chain — domains/no_llm.py reads it at the construction/
        # invocation boundary. Mechanical host policy, not an agent decision.
        os.environ["OZMA_NO_LLM"] = "1"
        log("OZMA_NO_LLM=1 — hosted-LLM assistance disabled for this run "
            "(teacher chains fall through to their non-LLM links / honest miss)")

    log(f"booting (ckpt-dir={ckpt_dir}, interval={args.interval}s, tick={args.tick_hz}Hz, "
        f"seeds={args.seeds})")
    adapter, booted_from = boot(
        ckpt_dir, args.seeds,
        strict_profile=args.strict_seed_profile_checkpoints,
        content_manifest=args.conversation_content_manifest)
    # Wave 2 (Deep-Reader): set explicitly AFTER boot/load either way, since
    # `WorldAdapter.load()` (the resume path) bypasses `__init__` and always
    # restores `shadow_read=False` — the CLI flag is the single source of
    # truth for the daemon regardless of fresh-boot vs resume.
    adapter.shadow_read = bool(args.shadow_read)
    # Wave 4 (Deep-Reader unification): `deep_ingest` travels with `shadow_read`
    # for this daemon (no separate CLI flag -- same "same flag family" as
    # WorldAdapter.__init__'s default) -- set explicitly for the SAME reason
    # (`load()` bypasses `__init__` on resume).
    adapter.deep_ingest = bool(args.shadow_read)
    log(f"shadow-read: {'ON' if adapter.shadow_read else 'off'}")
    state = DaemonState(adapter, booted_from)
    state.runs_dir = str(runs_dir)
    init_chat_history(state, ckpt_dir, adapter)
    if state.chat_turns:
        log(f"chat history loaded ({len(state.chat_turns)} turn(s))")
    log(f"booted: {adapter.s.node_count()} nodes, from={booted_from}")
    if args.attach_pybullet_humanoid:
        try:
            attach_pybullet_humanoid_trial_world(
                state,
                protocol_path=args.pybullet_humanoid_protocol,
                seed=args.pybullet_humanoid_seed,
            )
            log("PyBullet humanoid trial transducer attached "
                f"(protocol={args.pybullet_humanoid_protocol})")
        except Exception as e:  # noqa: BLE001 -- optional simulator remains an honest absent capability
            log("PyBullet humanoid trial transducer unavailable (continuing without it): "
                f"{type(e).__name__}: {e}")
    with AGENT_LOCK:
        nudged = _nudge_promoted_experiments(adapter)
        if nudged:
            log(f"self-improve: repaired promoted pipeline on boot ({nudged} extra ticks)")
            state.dirty.set()

    if args.attach_libraries:
        try:
            rep = _attach_default_libraries(adapter, enable_llm=not args.no_llm)
            log(f"libraries attached: teachers={rep['teachers']}, "
                f"structured_teacher={rep['teacher']}, skipped={rep['skipped']}")
        except Exception as e:  # noqa: BLE001 -- reference data dirs may be absent
            log(f"attach-libraries skipped: {type(e).__name__}: {e}")

    if args.once:
        checkpoint(adapter, ckpt_dir, args.keep)
        if state.embodied_trial_closer is not None:
            state.embodied_trial_closer()
        log("once-mode complete")
        return 0

    world_ctx = None
    if args.world_every > 0:
        world_ctx = _setup_world_ctx(adapter, args.world_actions)
        if world_ctx is not None:
            log(f"standing world enabled (every {args.world_every} ticks, "
                f"{args.world_actions} actions/episode)")

    voice_ctx = None
    if args.voice:
        try:
            voice_ctx = _start_voice_capture(
                adapter, args.voice_device, not args.voice_no_speak, args.voice_variant)
            log(f"voice capture enabled (device={args.voice_device or 'default'}, "
                f"speak={not args.voice_no_speak}, variant={args.voice_variant})")
        except Exception as e:  # noqa: BLE001 -- run without voice rather than fail to boot
            log(f"voice capture failed to start (continuing without it): "
                f"{type(e).__name__}: {e}")
            voice_ctx = None

    stop = threading.Event()

    def _on_signal(signum, _frame):
        log(f"signal {signal.Signals(signum).name} -> graceful shutdown")
        stop.set()

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    if args.socket:
        serve_socket(state, Path(args.socket), stop)

    threading.Thread(target=tick_loop, args=(state, stop, args.tick_hz,
                                              args.dispatch_every, str(runs_dir),
                                              args.fetch_every, args.browse_every,
                                              voice_ctx, args.voice_every,
                                              args.concern_every, args.close_every,
                                              args.world_every, world_ctx,
                                              args.auto_approve_every, args.imagine_every,
                                              args.collapse_every, args.self_correct_every,
                                              args.search_every),
                     kwargs={"detail_every": args.detail_every,
                             "steer_every": args.steer_every,
                             "study_every": args.study_every},
                     daemon=True).start()
    threading.Thread(target=monitor_loop, args=(state, stop), daemon=True).start()

    http_srv = None
    if not args.no_http:
        http_srv, _ = serve_http(state, args.http_port)

    log("online. checkpointing on interval; Ctrl-C / SIGTERM to stop. "
        f"talk: python3 scripts/jbw_talk.py --socket {args.socket or '(disabled)'}  "
        f"http: http://127.0.0.1:{args.http_port}")
    try:
        while not stop.is_set():
            if stop.wait(args.interval):       # interruptible sleep
                break
            try:
                checkpoint(adapter, ckpt_dir, args.keep)
                state.last_checkpoint_ts = time.time()
            except Exception as e:             # noqa: BLE001 -- never die on a save hiccup
                log(f"checkpoint failed (continuing): {e}")
    finally:
        if voice_ctx is not None:
            voice_ctx.stop.set()
        if state.embodied_trial_closer is not None:
            try:
                state.embodied_trial_closer()
            except Exception as e:  # noqa: BLE001 -- shutdown must not lose checkpointing
                log(f"PyBullet humanoid trial transducer close failed: {e}")
        log("final checkpoint before exit")
        try:
            checkpoint(adapter, ckpt_dir, args.keep)
            state.last_checkpoint_ts = time.time()
        except Exception as e:                 # noqa: BLE001
            log(f"final checkpoint failed: {e}")
        if http_srv is not None:
            try:
                http_srv.shutdown()
                http_srv.server_close()
            except Exception:  # noqa: BLE001
                pass
    log("offline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
