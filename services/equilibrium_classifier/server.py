"""Equilibrium classifier sidecar v0 (track T3): stdlib HTTP, loopback only.

Serves the frozen Equilibrium seed pack (seeds/equilibrium_*.json) through the
thin adapter domains/equilibrium_classify.py. Wire contract = the Equilibrium
worker client (equilibrium_worker/classify.py, OcelotClassifier):

  GET  /healthz      -> 200 {"ok":true} while the base-unchanged check holds, else 503
  GET  /v1/info      -> taxonomy_version, seed_pack_sha256 (== seed_pack_digest),
                        ocelot_commit, label statuses, mode="fork_per_batch", no_llm=true
  POST /v1/classify  -> {"messages":[{"id","text","reply_to"?}]} (1..100)
                        -> {"ok":true,"provenance":{...},"labels":[{"id","speech_act"?,
                           "substantive_markers":[],"deescalation"?,"rule_ids":[]}]}
  POST /v1/discourse -> 501 in v0

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
import subprocess
import sys
import threading
import time
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
SERVICE_NAME = "ocelot-equilibrium-classifier"


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
    # deescalation is a shadow boolean label (values [true] when a cue rule
    # fired); the client wants a float in [0, 1] and rejects bools.
    out["deescalation"] = 1.0 if True in labels.get("msg.deescalation", {}).get("values", []) else 0.0
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


class ClassifierService:
    """Boots the frozen base once and serves fork-per-batch classification."""

    def __init__(self, strong_every: int = STRONG_CHECK_EVERY) -> None:
        from domains import equilibrium_classify as ec
        self._ec = ec
        self._lock = threading.Lock()
        self.strong_every = strong_every
        self.base, self.root = ec.boot()
        self.snap = self.base.snapshot()
        self.rev0 = tuple(self.snap.source_revision)
        self.digest0 = strong_digest(self.base)
        self.last_strong = {"batch": 0, "digest": self.digest0, "ok": True}
        self.batches = 0
        self.messages = 0
        self.healthy = True
        self.label_status = {k: v.get("status") for k, v in
                             sorted(ec._label_status(self.base, self.root).items())}
        self.commit, self.dirty = ocelot_commit()
        self.pack_sha256 = seed_pack_sha256()
        self.provenance = {"taxonomy_version": ec.TAXONOMY_VERSION,
                           "seed_pack_version": ec.PACK_VERSION,
                           "seed_pack_sha256": self.pack_sha256,
                           "ocelot_commit": self.commit, "mode": MODE}

    def _strong_check(self) -> bool:
        d = strong_digest(self.base)
        ok = d == self.digest0
        self.last_strong = {"batch": self.batches, "digest": d, "ok": ok}
        if not ok:
            self.healthy = False
        return ok

    def classify(self, messages: list[dict]) -> list[dict]:
        with self._lock:
            if not self.healthy:
                raise BaseDrift()
            branch = self.snap.fork()
            try:
                results = self._ec.classify(branch, self.root, messages)
            finally:
                del branch
            self.batches += 1
            self.messages += len(messages)
            if tuple(self.snap.source_revision) != self.rev0:
                self.healthy = False
                raise BaseDrift()
            if self.batches % self.strong_every == 0 and not self._strong_check():
                raise BaseDrift()
            return [to_wire(r) for r in results]

    def health(self) -> bool:
        with self._lock:
            if self.healthy and tuple(self.snap.source_revision) != self.rev0:
                self.healthy = False
            if self.healthy:
                self._strong_check()
            return self.healthy

    def info(self) -> dict:
        with self._lock:
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
                "base": {"source_revision": list(self.snap.source_revision),
                         "boot_source_revision": list(self.rev0),
                         "strong_digest_boot": self.digest0,
                         "strong_digest_last": dict(self.last_strong),
                         "batches_served": self.batches, "messages_served": self.messages,
                         "healthy": self.healthy},
                "limits": {"max_messages": MAX_MESSAGES, "max_body_bytes": MAX_BODY_BYTES,
                           "max_text_chars": MAX_TEXT_LEN,
                           "strong_check_every_batches": self.strong_every},
                "endpoints": {"/v1/discourse": "not_implemented"},
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

        def _body(self) -> bytes:
            if self.headers.get("Transfer-Encoding"):
                self.close_connection = True
                raise ApiError(413, "too_large", "chunked bodies are not accepted")
            try:
                n = int(self.headers.get("Content-Length", ""))
            except ValueError:
                n = -1
            if n < 0 or n > MAX_BODY_BYTES:
                self.close_connection = True  # unread body: do not reuse the socket
                raise ApiError(413, "too_large",
                               f"Content-Length required and at most {MAX_BODY_BYTES} bytes")
            return self.rfile.read(n)

        def do_GET(self):
            p = self._path()
            if p == "/healthz":
                ok = service.health()
                self._send(200 if ok else 503, {"ok": ok})
            elif p == "/v1/info":
                self._send(200, service.info())
            else:
                self._err(ApiError(404, "not_found", "unknown path"))

        def do_POST(self):
            p = self._path()
            try:
                if p == "/v1/discourse":
                    self.close_connection = True
                    raise ApiError(501, "not_implemented", "/v1/discourse is not served in v0")
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


def serve(host: str, port: int) -> None:
    require_no_llm()
    require_loopback(host)
    _setup_engine()
    t0 = time.perf_counter()
    service = ClassifierService()
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
    a = ap.parse_args(argv)
    serve(a.host, a.port)


if __name__ == "__main__":
    main()
