"""Equilibrium classifier sidecar v0 (track T3): stdlib HTTP, loopback only.

Serves the frozen Equilibrium seed pack (seeds/equilibrium_*.json) through the
thin adapter domains/equilibrium_classify.py. Wire contract = the Equilibrium
worker client (equilibrium_worker/classify.py, OcelotClassifier):

  GET  /healthz      -> 200 {"ok":true} while the base-unchanged check holds, else 503
  GET  /v1/info      -> taxonomy_version, seed_pack_sha256 (== seed_pack_digest),
                        ocelot_commit, label statuses, mode="fork_per_batch", no_llm=true
  POST /v1/classify  -> {"messages":[{"id","text","reply_to"?}]} (1..100)
                        -> {"ok":true,"provenance":{...},"labels":[{"id","speech_act"?,
                           "substantive_markers":[],"deescalation","concession",
                           "status_claim","hostility" (0.0/1.0),"domains":[],"rule_ids":[]}]}
  POST /v1/discourse -> {"taxonomy_version"?, "window":{"window_id","kind"},
                         "turns":[{"id","actor_ref","text","reply_to"?,"ts_ms"?}]} (1..500)
                        -> {"ok":true,"taxonomy_version","window_id","messages":[as /v1/classify],
                           "quanta":[{actor_ref,trait,polarity,match,evidence,counter_evidence,
                           target_ref?,rule_ids}],"episodes":[{episode_id,kind,actor_refs,turns,
                           facets:[{code,match}],generative,rule_ids}]}
                        (shared contract; one window = one fork; internally open +
                         turns in chunks of 100 + close, exactly as below)
  POST /v1/conversations/{id}/turns   (track T3c; id matches [A-Za-z0-9_.:~-]{1,200})
                     -> {"taxonomy_version"?, "kind": meeting|thread|channel,
                         "turns":[{"id","actor_ref","text","ts_ms"?,"reply_to"?,"platform_thread"?}],
                         "participants"?:[{"actor_ref","aliases"?:[str]}]}
                         (0..100 turns per call, ts_ms non-decreasing, ids unique in the conversation;
                          participants (0.7.0): <= 500 per call, <= 8 aliases of 1..64 chars each,
                          cumulative per conversation, applied from this call's turns on; an actor_ref
                          may not have spoken yet. Aliases are display names / handles as they appear in
                          text: TRANSIENT -- held only in the conversation's retained fork, never
                          logged, never returned. "addressees" may name participants who have not
                          spoken, and so may a quantum's actor_ref / target_ref)
                     -> {"ok","taxonomy_version","conversation_id","seq",
                         "turns":[{"id","labels"(as /v1/classify),"responds_to","basis",
                                   "addressees","thread_id","topic_id","answers"}],
                         "quanta_delta":[...],"episodes_delta":[...],"open_questions"}
                        (0.6.0 EVIDENCE DELTAS, relative to everything emitted earlier for
                         the conversation, in seq order; only quanta / episodes this call
                         changed appear:
                         quanta_delta  {quantum_id, op: upsert|retract; upsert: actor_ref,
                           trait, polarity, match, target_ref (first appearance; afterwards
                           only if changed), evidence_add/_remove, counter_add/_remove
                           (always; first appearance carries the full lists in *_add),
                           rule_ids (full; first appearance / when changed)}
                         episodes_delta {episode_id, op; upsert: kind?, actor_refs?,
                           turns_add, turns_remove, facets?, generative?, rule_ids?}
                         folding them in order gives exactly the full rows; open_questions
                         is a full list)
  POST /v1/conversations/{id}/close  -> same shape, "turns":[], deltas of this call (no ticks:
                                        empty); frees the retained fork
  GET  /v1/conversations/{id}        -> {"ok","conversation_id","seq","idle_ttl_s","kind"}
  POST /v1/conversations/_batch      (shared batch contract)
                     -> {"taxonomy_version"?, "items":[{"conversation_id","kind","turns":[as /turns],
                         "participants"?: [as /turns], "close"?: bool}]}  (1..64 items, <= 2,000 turns in total, <= 100 per item,
                         each conversation_id at most once)
                     -> {"ok":true,"taxonomy_version","results":[ {"conversation_id","ok":true,
                         seq,turns,quanta_delta,episodes_delta,open_questions} (as /turns)
                         | {"conversation_id","ok":false,"error":{code,message,retryable}} ]}
                        results in request order; items run in parallel on the worker pool; a
                        per-item failure does not fail the batch; "close":true frees the
                        conversation after its turns are ingested (the result is the turns read-out)
     errors: 404 unknown_conversation; 409 conversation_evicted | out_of_order | duplicate_turn;
             413 too_large; 400 bad_request -- {ok:false,error:{code,message,retryable}}, no input echo

Conversations: the first turns call opens a conversation as a RETAINED fork of the
frozen base snapshot (incremental ingest; see domains/equilibrium_classify.py).
Idle TTL (default 900 s, --conversation-idle-ttl-s / EQ_CONV_IDLE_TTL_S) and an LRU
cap (default 64, --max-conversations / EQ_CONV_MAX) evict retained forks; an evicted
id answers 409 conversation_evicted (the last 4,096 evicted ids are remembered).
Concurrency: one lock PER CONVERSATION (a conversation's batches are serialised),
a short metadata lock for the session map / counters, and a bounded worker pool
(--workers / EQ_WORKERS, default min(8, cpus)) that every engine call goes through;
independent conversations run in parallel (the engine releases the GIL inside
run_rules and every fork has its own engine mutex). The frozen base is shared
read-only; its revision is checked after every request.

Frozen fork-per-batch: the base substrate + pack is booted ONCE, snap =
base.snapshot(); every request classifies on branch = snap.fork(), which is
then dropped. After every batch snap.source_revision must equal its boot value
(503 base_drift + process exit otherwise); a strong digest (sha256 of the
canonical graph_to_dict(base)) is taken at boot, every 1,000 batches and on
/healthz.

This module decides NO label: the server only validates, forks, calls the
adapter, and re-shapes the adapter's read-out into the client's wire types.
Request bodies are never logged or persisted. OZMA_NO_LLM=1 is mandatory.

Run:  OZMA_NO_LLM=1 python3 services/equilibrium_classifier/server.py
      (EQ_SIDECAR_PORT may change the port; the host is fixed to 127.0.0.1.)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BIND_HOST = "127.0.0.1"
DEFAULT_PORT = 8790
MODE = "fork_per_batch"
MAX_MESSAGES = 100
MAX_BODY_BYTES = 1_048_576
MAX_ID_LEN = 64
MAX_TEXT_LEN = 4000
STRONG_CHECK_EVERY = 1_000
MSG_KEYS = frozenset({"id", "text", "reply_to"})
REQ_KEYS = frozenset({"messages", "taxonomy_version"})
# /v1/discourse (shared contract, design §3)
MAX_TURNS = 500
MAX_DISCOURSE_BODY_BYTES = 16_777_216  # 500 turns x 4000 chars, worst-case JSON escaping
DISCOURSE_KEYS = frozenset({"taxonomy_version", "window", "turns"})
WINDOW_KEYS = frozenset({"window_id", "kind"})
TURN_KEYS = frozenset({"id", "actor_ref", "text", "reply_to", "ts_ms"})
WINDOW_KINDS = frozenset({"meeting", "thread", "channel"})
# /v1/conversations (track T3c shared contract): one retained fork per conversation
CONV_ID_RE = re.compile(r"[A-Za-z0-9_.:~-]{1,200}")
CONV_KEYS = frozenset({"taxonomy_version", "kind", "turns", "participants"})
CONV_TURN_KEYS = frozenset({"id", "actor_ref", "text", "ts_ms", "reply_to", "platform_thread"})
MAX_CONV_TURNS = 100
# participants roster (optional on /turns and every /_batch item; cumulative per
# conversation): <= 500 entries per call, <= 8 aliases per entry, 1..64 chars each.
PARTICIPANT_KEYS = frozenset({"actor_ref", "aliases"})
MAX_PARTICIPANTS = 500
MAX_ALIASES = 8
MAX_ALIAS_LEN = 64
# worst-case JSON escaping of one full roster (500 x (255-char ref + 8 x 64-char alias), 6 bytes/char)
MAX_ROSTER_BYTES = 2_621_440
MAX_CONV_BODY_BYTES = 4_194_304 + MAX_ROSTER_BYTES  # 100 turns x 4000 chars + one roster, worst case
DEFAULT_IDLE_TTL_S = 900
DEFAULT_MAX_CONVERSATIONS = 64
# /v1/conversations/_batch (shared batch contract)
MAX_BATCH_ITEMS = 64
MAX_BATCH_TURNS = 2_000
MAX_BATCH_BODY_BYTES = MAX_CONV_BODY_BYTES * (MAX_BATCH_TURNS // MAX_CONV_TURNS)
BATCH_KEYS = frozenset({"taxonomy_version", "items"})
BATCH_ITEM_KEYS = frozenset({"conversation_id", "kind", "turns", "close", "participants"})
DEFAULT_WORKERS = max(1, min(8, os.cpu_count() or 1))
MAX_TOMBSTONES = 4096  # evicted ids remembered (-> 409 conversation_evicted), LRU-capped
BASES = frozenset({"declared", "tracked", "none"})
# The client's contract ID pattern (^[A-Za-z0-9_.:@!+=-]{1,255}$). Turn ids are
# capped 3 shorter so the derived episode id "ep:<root turn id>" still fits it.
ID_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.:@!+=-")
MAX_REF_LEN = 255
MAX_TURN_ID_LEN = 252
SERVICE_NAME = "ocelot-equilibrium-classifier"
BOOL_CUE_FIELDS = ("deescalation", "concession", "status_claim", "hostility")


class RefuseStart(SystemExit):
    def __init__(self, why: str) -> None:
        print(f"equilibrium_classifier: refusing to start: {why}", file=sys.stderr)
        super().__init__(2)


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(code)
        self.status, self.code, self.message, self.retryable = status, code, message, retryable


class BaseDrift(ApiError):
    def __init__(self) -> None:
        super().__init__(503, "base_drift", "frozen base changed; sidecar exiting")


def require_no_llm() -> None:
    if os.environ.get("OZMA_NO_LLM") != "1":
        raise RefuseStart("OZMA_NO_LLM must be exactly '1'")


def require_loopback(host: str) -> None:
    if host != BIND_HOST:
        raise RefuseStart(f"bind host must be {BIND_HOST}")


def _setup_engine() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from domains.engine_provenance import engine_preamble
    engine_preamble()


def seed_pack_files() -> list[Path]:
    return sorted((ROOT / "seeds").glob("equilibrium_*.json"))


def seed_pack_sha256() -> str:
    """sha256 over the equilibrium_*.json files, sorted by name; each file
    contributes `name NUL raw-bytes NUL`."""
    h = hashlib.sha256()
    for p in seed_pack_files():
        h.update(p.name.encode("utf-8") + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()


def ocelot_commit() -> tuple[str, bool]:
    """(HEAD sha, tree-dirty flag). Read-only git: optional locks disabled so
    no index refresh is written."""
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    try:
        sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], env=env,
                             capture_output=True, text=True, timeout=10, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(ROOT), "--no-optional-locks", "status",
                                "--porcelain"], env=env, capture_output=True, text=True,
                               timeout=30, check=True).stdout.strip() != ""
    except (OSError, subprocess.SubprocessError):
        return "unknown", True
    return (sha if sha and all(c in "0123456789abcdef" for c in sha) else "unknown"), dirty


def strong_digest(substrate) -> str:
    d = substrate.graph_to_dict()
    blob = json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def wire_rule_id(rid: str) -> str:
    """Adapter rule ids are `<rule name>@<pack version>`; the client's code
    pattern has no `@`, so the version is joined with `:` instead."""
    return rid.replace("@", ":")


def to_wire(result: dict) -> dict:
    """Re-shape one adapter read-out into the client's MessageLabels types.
    Type conversion only: every value comes from a rule that fired."""
    labels = result["labels"]
    out: dict[str, Any] = {"id": result["id"]}
    acts = labels.get("msg.speech_act", {}).get("values", [])
    # The client carries ONE speech act; zero or several fired values are not
    # representable, so the field is omitted (reported, never chosen here).
    if len(acts) == 1:
        out["speech_act"] = acts[0]
    out["substantive_markers"] = list(labels.get("msg.substantive_markers", {}).get("values", []))
    # deescalation / concession / status_claim / hostility are shadow boolean cue
    # labels (values [true] when a cue rule fired); the client wants a float in
    # [0, 1] and rejects bools, so each is emitted as 1.0 (fired) / 0.0 (no rule
    # fired). 0.0 means "no cue matched", not "measured absent".
    for field in BOOL_CUE_FIELDS:
        out[field] = 1.0 if True in labels.get(f"msg.{field}", {}).get("values", []) else 0.0
    out["domains"] = list(labels.get("msg.domain", {}).get("values", []))
    out["rule_ids"] = [wire_rule_id(r) for r in result["rule_ids"]]
    return out


def validate_request(doc: Any, taxonomy_version: str) -> list[dict]:
    """Closed validation. Error messages carry field paths only, never input."""
    def bad(path: str, why: str) -> ApiError:
        return ApiError(400, "schema_violation", f"{path}: {why}")
    if not isinstance(doc, dict):
        raise bad("$", "must be an object")
    if set(doc) - REQ_KEYS:
        raise bad("$", "unknown field")
    tv = doc.get("taxonomy_version")
    if tv is not None and tv != taxonomy_version:
        raise ApiError(409, "taxonomy_mismatch", "taxonomy_version does not match the served pack")
    msgs = doc.get("messages")
    if not isinstance(msgs, list):
        raise bad("$.messages", "must be an array")
    if len(msgs) > MAX_MESSAGES:
        raise ApiError(413, "too_large", f"at most {MAX_MESSAGES} messages per request")
    if not msgs:
        raise bad("$.messages", "must not be empty")
    seen: set[str] = set()
    out = []
    for i, m in enumerate(msgs):
        p = f"$.messages[{i}]"
        if not isinstance(m, dict):
            raise bad(p, "must be an object")
        if set(m) - MSG_KEYS:
            raise bad(p, "unknown field")
        mid, text, rt = m.get("id"), m.get("text"), m.get("reply_to")
        if not isinstance(mid, str) or not 1 <= len(mid) <= MAX_ID_LEN:
            raise bad(p + ".id", f"must be a string of 1..{MAX_ID_LEN} chars")
        if mid in seen:
            raise bad(p + ".id", "duplicate id in batch")
        seen.add(mid)
        if not isinstance(text, str) or len(text) > MAX_TEXT_LEN:
            raise bad(p + ".text", f"must be a string of at most {MAX_TEXT_LEN} chars")
        if rt is not None and (not isinstance(rt, str) or len(rt) > MAX_ID_LEN):
            raise bad(p + ".reply_to", f"must be null or a string of at most {MAX_ID_LEN} chars")
        out.append({"id": mid, "text": text, "reply_to": rt})
    return out


def _is_ref(v: Any, max_len: int = MAX_REF_LEN) -> bool:
    return isinstance(v, str) and 1 <= len(v) <= max_len and set(v) <= ID_CHARS


def _validate_turns(turns: list, keys: frozenset, bad) -> list[dict]:
    """Closed per-turn validation shared by /v1/discourse and /v1/conversations.
    Duplicate ids inside one array are a schema error here (400); a /v1/conversations
    batch is re-checked against the conversation (409 duplicate_turn) by the service."""
    seen: set[str] = set()
    out = []
    for i, t in enumerate(turns):
        p = f"$.turns[{i}]"
        if not isinstance(t, dict):
            raise bad(p, "must be an object")
        if set(t) - keys:
            raise bad(p, "unknown field")
        tid, actor, text = t.get("id"), t.get("actor_ref"), t.get("text")
        rt, ts, pt = t.get("reply_to"), t.get("ts_ms"), t.get("platform_thread")
        if not _is_ref(tid, MAX_TURN_ID_LEN):
            raise bad(p + ".id", f"must be an id string of 1..{MAX_TURN_ID_LEN} chars")
        if tid in seen and keys is TURN_KEYS:
            raise bad(p + ".id", "duplicate id in window")
        seen.add(tid)
        if not _is_ref(actor):
            raise bad(p + ".actor_ref", f"must be an id string of 1..{MAX_REF_LEN} chars")
        if not isinstance(text, str) or len(text) > MAX_TEXT_LEN:
            raise bad(p + ".text", f"must be a string of at most {MAX_TEXT_LEN} chars")
        if rt is not None and not _is_ref(rt):
            raise bad(p + ".reply_to", f"must be null or an id string of 1..{MAX_REF_LEN} chars")
        if ts is not None and (isinstance(ts, bool) or not isinstance(ts, int) or ts < 0):
            raise bad(p + ".ts_ms", "must be a non-negative integer")
        if "platform_thread" in t and not _is_ref(pt):
            raise bad(p + ".platform_thread", f"must be an id string of 1..{MAX_REF_LEN} chars")
        item = {"id": tid, "actor_ref": actor, "text": text, "reply_to": rt}
        if ts is not None:
            item["ts_ms"] = ts
        if pt is not None:
            item["platform_thread"] = pt
        out.append(item)
    return out


def _validate_participants(ps: Any, path: str, bad) -> list[dict]:
    """Closed validation of the optional conversation roster (shared contract):
    [{"actor_ref": id, "aliases"?: [str 1..64 chars, <= 8]}], <= 500 entries.
    Aliases are display names / handles as they appear in text: TRANSIENT content
    -- they are handed to the conversation's retained fork only, never logged,
    never echoed in an error (paths only), never returned."""
    if not isinstance(ps, list):
        raise bad(path, "must be an array")
    if len(ps) > MAX_PARTICIPANTS:
        raise ApiError(413, "too_large", f"at most {MAX_PARTICIPANTS} participants per call")
    out = []
    for i, p in enumerate(ps):
        pp = f"{path}[{i}]"
        if not isinstance(p, dict):
            raise bad(pp, "must be an object")
        if set(p) - PARTICIPANT_KEYS or "actor_ref" not in p:
            raise bad(pp, "must be an object with actor_ref and optional aliases")
        if not _is_ref(p["actor_ref"]):
            raise bad(pp + ".actor_ref", f"must be an id string of 1..{MAX_REF_LEN} chars")
        aliases = p.get("aliases", [])
        if not isinstance(aliases, list) or len(aliases) > MAX_ALIASES:
            raise bad(pp + ".aliases", f"must be an array of at most {MAX_ALIASES} strings")
        for k, a in enumerate(aliases):
            if not isinstance(a, str) or not 1 <= len(a) <= MAX_ALIAS_LEN:
                raise bad(f"{pp}.aliases[{k}]", f"must be a string of 1..{MAX_ALIAS_LEN} chars")
        out.append({"actor_ref": p["actor_ref"], "aliases": list(aliases)})
    return out

def valid_conversation_id(cid: str) -> bool:
    return CONV_ID_RE.fullmatch(cid) is not None


def validate_conversation(doc: Any, taxonomy_version: str) -> tuple[str, list[dict], list[dict] | None]:
    """Closed validation of a POST /v1/conversations/{id}/turns body ->
    (kind, turns, participants or None). Error messages carry field paths only, never input."""
    def bad(path: str, why: str) -> ApiError:
        return ApiError(400, "bad_request", f"{path}: {why}")
    if not isinstance(doc, dict):
        raise bad("$", "must be an object")
    if set(doc) - CONV_KEYS:
        raise bad("$", "unknown field")
    tv = doc.get("taxonomy_version")
    if tv is not None and tv != taxonomy_version:
        raise ApiError(409, "taxonomy_mismatch", "taxonomy_version does not match the served pack")
    kind = doc.get("kind")
    if kind not in WINDOW_KINDS:
        raise bad("$.kind", "must be 'meeting', 'thread' or 'channel'")
    turns = doc.get("turns")
    if not isinstance(turns, list):
        raise bad("$.turns", "must be an array")
    if len(turns) > MAX_CONV_TURNS:
        raise ApiError(413, "too_large", f"at most {MAX_CONV_TURNS} turns per call")
    turns = _validate_turns(turns, CONV_TURN_KEYS, bad)
    roster = _validate_participants(doc["participants"], "$.participants", bad) if "participants" in doc else None
    return kind, turns, roster


def validate_batch(doc: Any, taxonomy_version: str) -> list[dict]:
    """Closed validation of a POST /v1/conversations/_batch body (shared batch
    contract). Any schema error fails the whole request (400, path only, never
    input); per-item runtime errors are reported per item by the service."""
    def bad(path: str, why: str) -> ApiError:
        return ApiError(400, "bad_request", f"{path}: {why}")
    if not isinstance(doc, dict):
        raise bad("$", "must be an object")
    if set(doc) - BATCH_KEYS:
        raise bad("$", "unknown field")
    tv = doc.get("taxonomy_version")
    if tv is not None and tv != taxonomy_version:
        raise ApiError(409, "taxonomy_mismatch", "taxonomy_version does not match the served pack")
    items = doc.get("items")
    if not isinstance(items, list):
        raise bad("$.items", "must be an array")
    if not items:
        raise bad("$.items", "must not be empty")
    if len(items) > MAX_BATCH_ITEMS:
        raise ApiError(413, "too_large", f"at most {MAX_BATCH_ITEMS} items per batch")
    out, seen, total = [], set(), 0
    for i, it in enumerate(items):
        p = f"$.items[{i}]"
        if not isinstance(it, dict):
            raise bad(p, "must be an object")
        if set(it) - BATCH_ITEM_KEYS:
            raise bad(p, "unknown field")
        cid = it.get("conversation_id")
        if not isinstance(cid, str) or not valid_conversation_id(cid):
            raise bad(p + ".conversation_id", "must match [A-Za-z0-9_.:~-]{1,200}")
        if cid in seen:
            raise bad(p + ".conversation_id", "repeats in the batch")
        seen.add(cid)
        if it.get("kind") not in WINDOW_KINDS:
            raise bad(p + ".kind", "must be 'meeting', 'thread' or 'channel'")
        close = it.get("close", False)
        if not isinstance(close, bool):
            raise bad(p + ".close", "must be a boolean")
        turns = it.get("turns")
        if not isinstance(turns, list):
            raise bad(p + ".turns", "must be an array")
        if len(turns) > MAX_CONV_TURNS:
            raise ApiError(413, "too_large", f"at most {MAX_CONV_TURNS} turns per item")
        total += len(turns)
        if total > MAX_BATCH_TURNS:
            raise ApiError(413, "too_large", f"at most {MAX_BATCH_TURNS} turns per batch")

        def ibad(path: str, why: str, _p=p) -> ApiError:
            return bad(_p + path[1:], why)
        item = {"conversation_id": cid, "kind": it["kind"], "close": close,
                "turns": _validate_turns(turns, CONV_TURN_KEYS, ibad)}
        if "participants" in it:
            item["participants"] = _validate_participants(it["participants"], p + ".participants", bad)
        out.append(item)
    return out


def validate_discourse(doc: Any, taxonomy_version: str) -> tuple[dict, list[dict]]:
    """Closed validation of a /v1/discourse request (shared contract, design §3).
    Mechanical schema checks only; error messages carry field paths, never input."""
    def bad(path: str, why: str) -> ApiError:
        return ApiError(400, "bad_request", f"{path}: {why}")
    if not isinstance(doc, dict):
        raise bad("$", "must be an object")
    if set(doc) - DISCOURSE_KEYS:
        raise bad("$", "unknown field")
    tv = doc.get("taxonomy_version")
    if tv is not None and tv != taxonomy_version:
        raise ApiError(409, "taxonomy_mismatch", "taxonomy_version does not match the served pack")
    win = doc.get("window")
    if not isinstance(win, dict) or set(win) != WINDOW_KEYS:
        raise bad("$.window", "must be an object with exactly window_id and kind")
    if not _is_ref(win["window_id"]):
        raise bad("$.window.window_id", f"must be an id string of 1..{MAX_REF_LEN} chars")
    if win["kind"] not in WINDOW_KINDS:
        raise bad("$.window.kind", "must be 'meeting', 'thread' or 'channel'")
    turns = doc.get("turns")
    if not isinstance(turns, list):
        raise bad("$.turns", "must be an array")
    if len(turns) > MAX_TURNS:
        raise ApiError(413, "too_large", f"at most {MAX_TURNS} turns per window")
    if not turns:
        raise bad("$.turns", "must not be empty")
    out = _validate_turns(turns, TURN_KEYS, bad)
    return {"window_id": win["window_id"], "kind": win["kind"]}, out


def quanta_to_wire(quanta: list[dict]) -> list[dict]:
    """Type conversion only: every quantum is a rule's output."""
    out = []
    for q in quanta:
        if q["match"] not in ("exact", "partial", "weak"):
            raise RuntimeError("quantum without a match shape")  # -> 500, never a guess
        row = {k: q[k] for k in ("actor_ref", "trait", "polarity", "match", "evidence",
                                 "counter_evidence")}
        if "target_ref" in q:
            row["target_ref"] = q["target_ref"]
        row["rule_ids"] = [wire_rule_id(r) for r in q["rule_ids"]]
        out.append(row)
    return out


def episodes_to_wire(episodes: list[dict]) -> list[dict]:
    out = []
    for e in episodes:
        if any(f["match"] not in ("exact", "partial", "weak") for f in e["facets"]):
            raise RuntimeError("facet without a match shape")
        out.append({"episode_id": e["episode_id"], "kind": e["kind"],
                    "actor_refs": list(e["actor_refs"]), "turns": list(e["turns"]),
                    "facets": [{"code": f["code"], "match": f["match"]} for f in e["facets"]],
                    "generative": e["generative"],
                    "rule_ids": [wire_rule_id(r) for r in e["rule_ids"]]})
    return out


MATCHES = ("exact", "partial", "weak")
QUANTUM_KEY_FIELDS = ("actor_ref", "trait", "polarity", "match", "target_ref")
DELTA_LISTS = ("evidence_add", "evidence_remove", "counter_add", "counter_remove")


def quanta_delta_to_wire(deltas: list[dict]) -> list[dict]:
    """Type conversion only (0.6.0 evidence deltas): every delta is the adapter's
    mechanical read of what the rules changed."""
    out = []
    for d in deltas:
        row = {"quantum_id": d["quantum_id"], "op": d["op"]}
        if d["op"] == "upsert":
            if "match" in d and d["match"] not in MATCHES:
                raise RuntimeError("quantum without a match shape")  # -> 500, never a guess
            row.update({k: d[k] for k in QUANTUM_KEY_FIELDS if k in d})
            row.update({k: list(d[k]) for k in DELTA_LISTS})
            if "rule_ids" in d:
                row["rule_ids"] = [wire_rule_id(r) for r in d["rule_ids"]]
        out.append(row)
    return out


def episodes_delta_to_wire(deltas: list[dict]) -> list[dict]:
    out = []
    for d in deltas:
        row = {"episode_id": d["episode_id"], "op": d["op"]}
        if d["op"] == "upsert":
            if any(f["match"] not in MATCHES for f in d.get("facets", ())):
                raise RuntimeError("facet without a match shape")
            for k in ("kind", "actor_refs"):
                if k in d:
                    row[k] = d[k] if k == "kind" else list(d[k])
            row["turns_add"], row["turns_remove"] = list(d["turns_add"]), list(d["turns_remove"])
            if "facets" in d:
                row["facets"] = [{"code": f["code"], "match": f["match"]} for f in d["facets"]]
            if "generative" in d:
                row["generative"] = d["generative"]
            if "rule_ids" in d:
                row["rule_ids"] = [wire_rule_id(r) for r in d["rule_ids"]]
        out.append(row)
    return out


def discourse_to_wire(result: dict, taxonomy_version: str) -> dict:
    """Re-shape the adapter read-out into the shared /v1/discourse response."""
    return {"ok": True, "taxonomy_version": taxonomy_version, "window_id": result["window_id"],
            "messages": [to_wire(m) for m in result["messages"]],
            "quanta": quanta_to_wire(result["quanta"]),
            "episodes": episodes_to_wire(result["episodes"])}


def conversation_to_wire(result: dict, taxonomy_version: str) -> dict:
    """Re-shape one conversation read-out (turns batch or close) into the shared
    /v1/conversations response. Per-turn `labels` is the /v1/classify object."""
    turns = []
    for t in result["turns"]:
        if t["basis"] not in BASES or not isinstance(t["thread_id"], str):
            raise RuntimeError("turn without a structure basis / thread")
        turns.append({"id": t["id"], "labels": to_wire(t["read"]),
                      "responds_to": list(t["responds_to"]), "basis": t["basis"],
                      "addressees": list(t["addressees"]), "thread_id": t["thread_id"],
                      "topic_id": t["topic_id"], "answers": list(t["answers"])})
    return {"ok": True, "taxonomy_version": taxonomy_version,
            "conversation_id": result["conversation_id"], "seq": result["seq"], "turns": turns,
            "quanta_delta": quanta_delta_to_wire(result["quanta_delta"]),
            "episodes_delta": episodes_delta_to_wire(result["episodes_delta"]),
            "open_questions": list(result["open_questions"])}


def _no_dupes(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError("duplicate key")
        d[k] = v
    return d


def _no_constants(_):
    raise ValueError("non-finite number")


def parse_json(raw: bytes) -> Any:
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_no_dupes,
                          parse_constant=_no_constants)
    except (UnicodeDecodeError, ValueError):
        raise ApiError(400, "bad_json", "body is not valid UTF-8 JSON") from None


class Session:
    """One retained conversation: its fork of the frozen base + the adapter handle
    (the conversation node id) + its lock (one batch at a time per conversation).
    Turns, actors, seq and order marks live in the fork. `branch is None` means
    the session was dropped (closed / evicted / failed) while someone waited."""
    __slots__ = ("branch", "state", "kind", "last_used", "lock", "fresh")

    def __init__(self, branch, state, kind: str, now: float) -> None:
        self.branch, self.state, self.kind, self.last_used = branch, state, kind, now
        self.lock = threading.Lock()
        self.fresh = True  # registered, first batch not yet accepted


class ClassifierService:
    """Boots the frozen base once; serves fork-per-batch classification and
    retained-fork conversations.

    Concurrency: every engine call runs under one of `workers` slots (a bounded
    semaphore; /_batch items are dispatched on a pool of the same size), so at
    most `workers` forks are being worked at once. A conversation's batches are
    serialised by its own lock; independent conversations proceed in parallel on
    their own forks (each fork has its own engine mutex and run_rules releases the
    GIL). `_meta` guards only the session map, tombstones and counters and is
    never held across engine work; a busy session is never evicted. The frozen
    base is never mutated: its source revision is checked after every request and
    a strong digest every `strong_every` requests."""

    def __init__(self, strong_every: int = STRONG_CHECK_EVERY,
                 idle_ttl_s: float = DEFAULT_IDLE_TTL_S,
                 max_conversations: int = DEFAULT_MAX_CONVERSATIONS, clock=time.monotonic,
                 workers: int = DEFAULT_WORKERS) -> None:
        from domains import equilibrium_classify as ec
        self._ec = ec
        self._meta = threading.Lock()
        self._strong_lock = threading.Lock()
        self.workers = max(1, int(workers))
        self._slots = threading.BoundedSemaphore(self.workers)
        self._pool = ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix="eq-conv")
        self.strong_every = strong_every
        self.base, self.root = ec.boot()
        self.snap = self.base.snapshot()
        self.rev0 = tuple(self.snap.source_revision)
        self.digest0 = strong_digest(self.base)
        self.last_strong = {"batch": 0, "digest": self.digest0, "ok": True}
        self.idle_ttl_s = idle_ttl_s
        self.max_conversations = max_conversations
        self._clock = clock
        self.sessions: OrderedDict[str, Session] = OrderedDict()  # LRU order
        self.tombstones: OrderedDict[str, str] = OrderedDict()   # evicted id -> reason
        self.conversations_opened = 0
        self.conversations_closed = 0
        self.conversations_evicted = {"idle_ttl": 0, "lru": 0}
        self.batches = 0
        self.batch_requests = 0
        self.messages = 0
        self.windows = 0
        self.turns = 0
        self.healthy = True
        rows = ec._label_status(self.base, self.root)
        self.label_status = {k: v.get("status") for k, v in sorted(rows.items())}
        self.trait_status = {k: v["status"] for k, v in sorted(rows.items()) if v.get("kind") == "trait"}
        self.episode_kind_status = {k.split(".", 1)[1]: v["status"] for k, v in sorted(rows.items())
                                    if v.get("kind") == "episode_kind"}
        self.facet_status = {k.split(".", 1)[1]: v["status"] for k, v in sorted(rows.items())
                             if v.get("kind") == "facet"}
        self.commit, self.dirty = ocelot_commit()
        self.pack_sha256 = seed_pack_sha256()
        self.provenance = {"taxonomy_version": ec.TAXONOMY_VERSION,
                           "seed_pack_version": ec.PACK_VERSION,
                           "seed_pack_sha256": self.pack_sha256,
                           "ocelot_commit": self.commit, "mode": MODE}

    @contextmanager
    def _slot(self):
        self._slots.acquire()
        try:
            yield
        finally:
            self._slots.release()

    def _strong_check(self) -> bool:
        with self._strong_lock:
            d = strong_digest(self.base)
            ok = d == self.digest0
            with self._meta:
                self.last_strong = {"batch": self.batches, "digest": d, "ok": ok}
                if not ok:
                    self.healthy = False
            return ok

    def _after_batch(self, **counts: int) -> None:
        """Base checks after every request: source revision always, strong digest
        every `strong_every` requests (outside the metadata lock)."""
        with self._meta:
            self.batches += 1
            for k, v in counts.items():
                setattr(self, k, getattr(self, k) + v)
            due = self.batches % self.strong_every == 0
        if tuple(self.snap.source_revision) != self.rev0:
            self.healthy = False
            raise BaseDrift()
        if due and not self._strong_check():
            raise BaseDrift()

    def _require_healthy(self) -> None:
        if not self.healthy:
            raise BaseDrift()

    def classify(self, messages: list[dict]) -> list[dict]:
        self._require_healthy()
        with self._slot():
            branch = self.snap.fork()
            try:
                results = self._ec.classify(branch, self.root, messages)
            finally:
                del branch
        self._after_batch(messages=len(messages))
        return [to_wire(r) for r in results]

    def _budget(self, fn, *args):
        try:
            return fn(*args)
        except self._ec.BudgetExhausted:
            raise ApiError(422, "budget_exhausted", "rule fuel exhausted before the fixpoint") from None

    def _check_order(self, branch, state, turns: list[dict]) -> None:
        why = self._ec.conversation_check(branch, state, turns)
        if why == "duplicate_turn":
            raise ApiError(409, "duplicate_turn", "a turn id repeats or already exists in the conversation")
        if why == "out_of_order":
            raise ApiError(409, "out_of_order", "turns must be time-ordered (ts_ms non-decreasing)")

    def discourse(self, window: dict, turns: list[dict]) -> dict:
        """/v1/discourse = open + turns (chunks of MAX_CONV_TURNS) + close on one
        fork that is dropped afterwards; quanta/episodes are the full read-out."""
        self._require_healthy()
        ec = self._ec
        with self._slot():
            branch = self.snap.fork()
            try:
                st = ec.conversation_open(branch, self.root, window["window_id"], window["kind"])
                self._check_order(branch, st, turns)
                got = []
                for i in range(0, len(turns), MAX_CONV_TURNS):
                    got += self._budget(ec.conversation_ingest, branch, self.root, st,
                                        turns[i:i + MAX_CONV_TURNS])["turns"]
                fin = self._budget(ec.conversation_full, branch, self.root, st)
            finally:
                del branch
        self._after_batch(windows=1, turns=len(turns))
        result = {"window_id": window["window_id"], "messages": [t["read"] for t in got],
                  "quanta": fin["quanta"], "episodes": fin["episodes"]}
        return discourse_to_wire(result, ec.TAXONOMY_VERSION)

    # ---- /v1/conversations ----------------------------------------------------
    # Lock order: a worker slot, then (briefly) _meta, then a session lock; _meta
    # is released before a session lock is waited on. Eviction only takes a
    # session lock non-blockingly, so it never waits on (or drops) a busy session.
    def _drop(self, cid: str, sess: Session, reason: str | None) -> None:
        """Drop a session whose lock the caller holds. reason=None: closed or
        failed (no tombstone); else evicted ('idle_ttl' | 'lru'). Caller holds _meta."""
        if self.sessions.get(cid) is sess:
            del self.sessions[cid]
        sess.branch = sess.state = None  # drop the retained fork
        if reason is not None:
            self.tombstones[cid] = reason
            self.tombstones.move_to_end(cid)
            while len(self.tombstones) > MAX_TOMBSTONES:
                self.tombstones.popitem(last=False)
            self.conversations_evicted[reason] += 1

    def _try_evict(self, cid: str, reason: str) -> bool:
        sess = self.sessions[cid]
        if not sess.lock.acquire(blocking=False):
            return False  # busy: never evicted under a running batch
        try:
            self._drop(cid, sess, reason)
        finally:
            sess.lock.release()
        return True

    def _sweep(self, now: float) -> None:
        for cid in [c for c, x in self.sessions.items() if now - x.last_used > self.idle_ttl_s]:
            self._try_evict(cid, "idle_ttl")

    def _make_room(self, keep: str) -> None:
        """LRU cap: evict the least recently used IDLE sessions (never `keep`, never
        a busy one). With every older session busy the map may exceed the cap by at
        most the number of in-flight requests until the next accepted batch."""
        for cid in list(self.sessions):
            if len(self.sessions) <= self.max_conversations:
                return
            if cid != keep:
                self._try_evict(cid, "lru")

    def _acquire(self, cid: str, now: float, kind: str | None) -> Session:
        """Return the session for `cid` with its lock HELD. kind=None: it must
        exist; else a missing one is registered (fresh) for `kind`."""
        while True:
            with self._meta:
                self._sweep(now)
                sess = self.sessions.get(cid)
                if sess is None:
                    if cid in self.tombstones:
                        raise ApiError(409, "conversation_evicted",
                                       "conversation state was evicted (idle TTL or capacity); "
                                       "resubmit it under a new conversation id")
                    if kind is None:
                        raise ApiError(404, "unknown_conversation", "no such open conversation")
                    branch = self.snap.fork()
                    sess = Session(branch, self._ec.conversation_open(branch, self.root, cid, kind),
                                   kind, now)
                    self.sessions[cid] = sess
                    self.conversations_opened += 1
            sess.lock.acquire()
            if sess.branch is not None:
                return sess
            sess.lock.release()  # dropped while we waited: look it up again

    def _drop_fresh(self, cid: str, sess: Session) -> None:
        """A fresh session whose first batch was refused leaves no state behind."""
        with self._meta:
            self._drop(cid, sess, None)
            self.conversations_opened -= 1

    def conversation_turns(self, cid: str, kind: str, turns: list[dict],
                           participants: list[dict] | None = None) -> dict:
        """One batch of turns (and optionally roster entries, cumulative; aliases are
        transient: they live only in this conversation's retained fork)."""
        self._require_healthy()
        ec = self._ec
        with self._slot():
            now = self._clock()
            sess = self._acquire(cid, now, kind)
            try:
                if sess.kind != kind:
                    raise ApiError(400, "bad_request", "$.kind: does not match the conversation")
                try:
                    self._check_order(sess.branch, sess.state, turns)  # atomic: nothing ingested on 409
                except ApiError:
                    if sess.fresh:
                        self._drop_fresh(cid, sess)
                    raise
                if sess.fresh:
                    sess.fresh = False
                    with self._meta:
                        self._make_room(keep=cid)
                try:
                    result = ec.conversation_ingest(sess.branch, self.root, sess.state, turns, participants)
                except ec.BudgetExhausted:
                    with self._meta:
                        self._drop(cid, sess, None)  # state is partial: drop it
                    raise ApiError(422, "budget_exhausted",
                                   "rule fuel exhausted before the fixpoint; conversation dropped") from None
                sess.last_used = now
                with self._meta:
                    if self.sessions.get(cid) is sess:
                        self.sessions.move_to_end(cid)
            finally:
                sess.lock.release()
        self._after_batch(turns=len(turns))
        return conversation_to_wire(result, ec.TAXONOMY_VERSION)

    def conversation_close(self, cid: str, read_out: bool = True) -> dict | None:
        """Close: the final read-out (deltas of this call; read_out=False: just free the fork,
        used by /_batch `close`), then drop the retained fork."""
        self._require_healthy()
        ec = self._ec
        with self._slot():
            sess = self._acquire(cid, self._clock(), None)
            try:
                result = (self._budget(ec.conversation_close, sess.branch, self.root, sess.state)
                          if read_out else None)
            finally:
                with self._meta:
                    self._drop(cid, sess, None)
                sess.lock.release()
        self._after_batch(conversations_closed=1)
        return conversation_to_wire(result, ec.TAXONOMY_VERSION) if read_out else None

    def _batch_item(self, item: dict) -> dict:
        cid = item["conversation_id"]
        try:
            out = self.conversation_turns(cid, item["kind"], item["turns"], item.get("participants"))
            if item.get("close") is True:
                self.conversation_close(cid, read_out=False)
        except BaseDrift:
            raise
        except ApiError as e:
            return {"conversation_id": cid, "ok": False,
                    "error": {"code": e.code, "message": e.message, "retryable": e.retryable}}
        except Exception:  # never echo input or tracebacks
            return {"conversation_id": cid, "ok": False,
                    "error": {"code": "internal", "message": "internal error", "retryable": False}}
        out.pop("taxonomy_version")
        return out

    def conversation_batch(self, items: list[dict]) -> dict:
        """/v1/conversations/_batch: items run in parallel on the worker pool;
        results in request order; a per-item failure is reported in its result."""
        self._require_healthy()
        futures = [self._pool.submit(self._batch_item, it) for it in items]
        results = [f.result() for f in futures]  # BaseDrift propagates (process exits)
        with self._meta:
            self.batch_requests += 1
        return {"ok": True, "taxonomy_version": self._ec.TAXONOMY_VERSION, "results": results}

    def conversation_get(self, cid: str) -> dict:
        sess = self._acquire(cid, self._clock(), None)
        try:
            info = self._ec.conversation_info(sess.branch, sess.state)
        finally:
            sess.lock.release()
        return {"ok": True, "conversation_id": info["conversation_id"], "seq": info["seq"],
                "idle_ttl_s": int(self.idle_ttl_s), "kind": info["kind"]}

    def health(self) -> bool:
        if self.healthy and tuple(self.snap.source_revision) != self.rev0:
            self.healthy = False
        if self.healthy:
            self._strong_check()
        return self.healthy

    def info(self) -> dict:
        with self._meta:
            return {
                "ok": True, "name": SERVICE_NAME,
                "taxonomy_version": self._ec.TAXONOMY_VERSION,
                "seed_pack_version": self._ec.PACK_VERSION,
                "seed_pack_sha256": self.pack_sha256,
                "seed_pack_digest": self.pack_sha256,
                "seed_pack_files": [p.name for p in seed_pack_files()],
                "ocelot_commit": self.commit, "ocelot_tree_dirty": self.dirty,
                "mode": MODE, "no_llm": True, "ozma_no_llm": True,
                "labels": dict(self.label_status),
                "trait_status": dict(self.trait_status),
                "episode_kind_status": dict(self.episode_kind_status),
                "facet_codes": dict(self.facet_status),
                "boundary_tokens": {"lemma": "wordnet.morphy(v,n)|form",
                                    "eq_class": "<num>|first-sense wordnet noun lexname"},
                "base": {"source_revision": list(self.snap.source_revision),
                         "boot_source_revision": list(self.rev0),
                         "strong_digest_boot": self.digest0,
                         "strong_digest_last": dict(self.last_strong),
                         "batches_served": self.batches, "messages_served": self.messages,
                         "windows_served": self.windows, "turns_served": self.turns,
                         "batch_requests_served": self.batch_requests,
                         "healthy": self.healthy},
                "limits": {"max_messages": MAX_MESSAGES, "max_body_bytes": MAX_BODY_BYTES,
                           "max_text_chars": MAX_TEXT_LEN,
                           "max_turns": MAX_TURNS, "max_discourse_body_bytes": MAX_DISCOURSE_BODY_BYTES,
                           "discourse_fuel_per_stratum": self._ec.DISCOURSE_FUEL,
                           "strong_check_every_batches": self.strong_every,
                           "max_conversation_turns_per_call": MAX_CONV_TURNS,
                           "max_conversation_body_bytes": MAX_CONV_BODY_BYTES,
                           "max_participants_per_call": MAX_PARTICIPANTS,
                           "max_aliases_per_participant": MAX_ALIASES,
                           "max_alias_chars": MAX_ALIAS_LEN,
                           "max_batch_items": MAX_BATCH_ITEMS,
                           "max_batch_turns": MAX_BATCH_TURNS,
                           "max_batch_body_bytes": MAX_BATCH_BODY_BYTES,
                           "conversation_idle_ttl_s": self.idle_ttl_s,
                           "max_conversations": self.max_conversations},
                "conversations": {"open": len(self.sessions), "opened": self.conversations_opened,
                                  "closed": self.conversations_closed,
                                  "evicted": dict(self.conversations_evicted),
                                  "concurrency": "per_conversation_locks",
                                  "workers": self.workers},
                "endpoints": {"/v1/classify": "ok", "/v1/discourse": "ok",
                              "/v1/conversations/{id}/turns": "ok",
                              "/v1/conversations/{id}/close": "ok",
                              "GET /v1/conversations/{id}": "ok",
                              "/v1/conversations/_batch": "ok"},
            }


def make_handler(service: ClassifierService):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        disable_nagle_algorithm = True  # headers+body are two writes; avoid delayed-ACK stalls
        server_version = SERVICE_NAME
        sys_version = ""

        def log_message(self, fmt, *args):  # never log request lines/bodies
            return

        def _send(self, status: int, doc: dict) -> None:
            body = json.dumps(doc, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            if self.close_connection:
                self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)

        def _err(self, e: ApiError) -> None:
            self._send(e.status, {"ok": False, "error": {
                "code": e.code, "message": e.message, "retryable": e.retryable}})

        def _path(self) -> str:
            return self.path.split("?", 1)[0]

        def _body(self, cap: int = MAX_BODY_BYTES) -> bytes:
            if self.headers.get("Transfer-Encoding"):
                self.close_connection = True
                raise ApiError(413, "too_large", "chunked bodies are not accepted")
            try:
                n = int(self.headers.get("Content-Length", ""))
            except ValueError:
                n = -1
            if n < 0 or n > cap:
                self.close_connection = True  # unread body: do not reuse the socket
                raise ApiError(413, "too_large",
                               f"Content-Length required and at most {cap} bytes")
            return self.rfile.read(n)

        def _conv_path(self) -> tuple[str, str] | None:
            """('/v1/conversations/{id}[/<action>]') -> (id, action) or None.
            A malformed id is a 400 that never echoes the id."""
            parts = self._path().split("/")
            if len(parts) not in (4, 5) or parts[:3] != ["", "v1", "conversations"]:
                return None
            if not valid_conversation_id(parts[3]):
                self.close_connection = True  # any body stays unread
                raise ApiError(400, "bad_request", "conversation_id: must match [A-Za-z0-9_.:~-]{1,200}")
            return parts[3], (parts[4] if len(parts) == 5 else "")

        def do_GET(self):
            p = self._path()
            if p.startswith("/v1/conversations/"):
                try:
                    cp = self._conv_path()
                    if cp is None or cp[1] != "":
                        raise ApiError(404, "not_found", "unknown path")
                    self._send(200, service.conversation_get(cp[0]))
                except ApiError as e:
                    self._err(e)
                except Exception:
                    self.close_connection = True
                    self._err(ApiError(500, "internal", "internal error"))
            elif p == "/healthz":
                ok = service.health()
                self._send(200 if ok else 503, {"ok": ok})
            elif p == "/v1/info":
                self._send(200, service.info())
            else:
                self._err(ApiError(404, "not_found", "unknown path"))

        def do_POST(self):
            p = self._path()
            try:
                if p == "/v1/conversations/_batch":
                    tax = service.provenance["taxonomy_version"]
                    items = validate_batch(parse_json(self._body(MAX_BATCH_BODY_BYTES)), tax)
                    self._send(200, service.conversation_batch(items))
                    return
                cp = self._conv_path() if p.startswith("/v1/conversations/") else None
                if cp is not None and cp[1] == "turns":
                    tax = service.provenance["taxonomy_version"]
                    kind, turns, roster = validate_conversation(parse_json(self._body(MAX_CONV_BODY_BYTES)), tax)
                    self._send(200, service.conversation_turns(cp[0], kind, turns, roster))
                    return
                if cp is not None and cp[1] == "close":
                    if self.headers.get("Content-Length") is not None or self.headers.get("Transfer-Encoding"):
                        self._body(MAX_BODY_BYTES)  # an (ignored) body is drained, never parsed
                    self._send(200, service.conversation_close(cp[0]))
                    return
                if p == "/v1/discourse":
                    tax = service.provenance["taxonomy_version"]
                    window, turns = validate_discourse(
                        parse_json(self._body(MAX_DISCOURSE_BODY_BYTES)), tax)
                    self._send(200, service.discourse(window, turns))
                    return
                if p != "/v1/classify":
                    self.close_connection = True
                    raise ApiError(404, "not_found", "unknown path")
                msgs = validate_request(parse_json(self._body()), service.provenance["taxonomy_version"])
                labels = service.classify(msgs)
                self._send(200, {"ok": True, "provenance": service.provenance, "labels": labels})
            except BaseDrift as e:
                self.close_connection = True
                self._err(e)
                self.wfile.flush()
                print("equilibrium_classifier: base_drift; exiting", file=sys.stderr)
                os._exit(3)
            except ApiError as e:
                self._err(e)
            except Exception:  # never echo input or tracebacks to the client
                self.close_connection = True
                self._err(ApiError(500, "internal", "internal error"))

        def _method_not_allowed(self):
            self.close_connection = True
            self._err(ApiError(405, "method_not_allowed", "method not allowed"))

        do_PUT = do_DELETE = do_PATCH = _method_not_allowed

    return Handler


def serve(host: str, port: int, idle_ttl_s: float = DEFAULT_IDLE_TTL_S,
          max_conversations: int = DEFAULT_MAX_CONVERSATIONS, workers: int = DEFAULT_WORKERS) -> None:
    require_no_llm()
    require_loopback(host)
    _setup_engine()
    t0 = time.perf_counter()
    service = ClassifierService(idle_ttl_s=idle_ttl_s, max_conversations=max_conversations,
                                workers=workers)
    httpd = ThreadingHTTPServer((BIND_HOST, port), make_handler(service))
    httpd.daemon_threads = True
    if httpd.server_address[0] != BIND_HOST:
        raise RefuseStart("socket did not bind to loopback")
    print(f"equilibrium_classifier: serving {MODE} on http://{BIND_HOST}:{httpd.server_address[1]} "
          f"(boot {time.perf_counter() - t0:.2f}s, rev {service.rev0}, "
          f"pack {service.pack_sha256[:12]})", file=sys.stderr, flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default=BIND_HOST, help="must be 127.0.0.1 (anything else is refused)")
    ap.add_argument("--port", type=int, default=int(os.environ.get("EQ_SIDECAR_PORT", DEFAULT_PORT)))
    ap.add_argument("--conversation-idle-ttl-s", type=float,
                    default=float(os.environ.get("EQ_CONV_IDLE_TTL_S", DEFAULT_IDLE_TTL_S)))
    ap.add_argument("--max-conversations", type=int,
                    default=int(os.environ.get("EQ_CONV_MAX", DEFAULT_MAX_CONVERSATIONS)))
    ap.add_argument("--workers", type=int, default=int(os.environ.get("EQ_WORKERS", DEFAULT_WORKERS)),
                    help="engine worker slots (parallel conversations)")
    a = ap.parse_args(argv)
    if a.conversation_idle_ttl_s <= 0 or a.max_conversations < 1 or a.workers < 1:
        raise RefuseStart("conversation TTL must be > 0, max conversations >= 1, workers >= 1")
    serve(a.host, a.port, a.conversation_idle_ttl_s, a.max_conversations, a.workers)


if __name__ == "__main__":
    main()
