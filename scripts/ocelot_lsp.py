"""ocelot_lsp — a small, honest stdio Language Server Protocol bridge.

This is the compiler-accurate layer the tree-sitter repo map cannot provide
(see `docs/features/GRAPH_CODING_LANDSCAPE.md`, P0): definitions, references,
diagnostics, hover, document symbols, call hierarchy and rename previews from
the language server that already knows the project's types and scopes.

Design rules:

  * **Lazy and explicit.** A server process is spawned on the first query, one
    per (root, language, command) via `get_client`, and closed explicitly
    (`close()` or a `with` block). `server_status()` never starts a server.
  * **Read-only by construction.** `rename_preview` and `symbol_impact` never
    write. Canonical edits stay the op lists in `ocelot_code_edit.py`; this
    module only produces positions and previews.
  * **Honest absence.** A missing binary, an unsupported language, a dead
    server, a protocol error or a timeout returns `{"ok": False, ...}`; no
    print statements and no fabricated locations.
  * **Plain dicts.** Every public query returns a JSON-shaped dict suitable
    for the dev-memory wrappers, MCP tools and CLI verbs.

Positions are **LSP-native**: 0-based lines and UTF-16 code-unit characters.
Callers that expose 1-based editor lines (MCP, CLI) add 1 at that boundary.
Result locations carry both the flat `line`/`character` fields and the raw
`start`/`end` position dicts.

Stdio framing is JSON-RPC 2.0 with `Content-Length` headers. Notifications
(notably `textDocument/publishDiagnostics`) are dispatched on a reader thread;
server-to-client requests are answered conservatively (configuration -> null,
`workspace/applyEdit` -> refused) so servers do not stall.
"""
from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import signal
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TIMEOUT = 20.0
DEFAULT_INITIALIZE_TIMEOUT = 60.0
DEFAULT_DIAGNOSTICS_TIMEOUT = 5.0
DEFAULT_CLOSE_TIMEOUT = 5.0
MAX_MESSAGE_BYTES = 64 * 1024 * 1024
MAX_STDERR_LINES = 80
MAX_PROTOCOL_ERRORS = 20
# pyright can answer the very first workspace-wide reference query before its
# file scan finishes. An empty reference list is retried briefly; a legitimate
# zero-reference symbol pays at most these delays.
REFERENCES_RETRY_DELAYS = (0.2, 0.5)


# --------------------------------------------------------------------------- #
# Registry: language -> ordered server candidates
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ServerSpec:
    """One server binary candidate and the arguments it needs for stdio."""

    name: str
    args: tuple[str, ...] = ()


LANGUAGE_SERVERS: dict[str, tuple[ServerSpec, ...]] = {
    "python": (
        ServerSpec("pyright-langserver", ("--stdio",)),
        ServerSpec("pylsp"),
    ),
    "rust": (ServerSpec("rust-analyzer"),),
    "c": (ServerSpec("clangd"),),
    "cpp": (ServerSpec("clangd"),),
    "typescript": (ServerSpec("typescript-language-server", ("--stdio",)),),
    "javascript": (ServerSpec("typescript-language-server", ("--stdio",)),),
}

LANGUAGE_ALIASES = {
    "py": "python",
    "python3": "python",
    "rs": "rust",
    "rsx": "rust",
    "c++": "cpp",
    "cc": "cpp",
    "cxx": "cpp",
    "ts": "typescript",
    "tsx": "typescript",
    "js": "javascript",
    "jsx": "javascript",
}

SUFFIX_LANGUAGES = {
    ".py": "python",
    ".pyi": "python",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".hh": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
}

# LSP `languageId` is not always the registry language (TSX/JSX differ).
_LANGUAGE_IDS_BY_SUFFIX = {
    ".tsx": "typescriptreact",
    ".jsx": "javascriptreact",
    ".pyi": "python",
}

SYMBOL_KINDS = {
    1: "file", 2: "module", 3: "namespace", 4: "package", 5: "class",
    6: "method", 7: "property", 8: "field", 9: "constructor", 10: "enum",
    11: "interface", 12: "function", 13: "variable", 14: "constant",
    15: "string", 16: "number", 17: "boolean", 18: "array", 19: "object",
    20: "key", 21: "null", 22: "enum_member", 23: "struct", 24: "event",
    25: "operator", 26: "type_parameter",
}

SEVERITY_NAMES = {1: "error", 2: "warning", 3: "information", 4: "hint"}


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
class LSPError(RuntimeError):
    """A refused or failed LSP operation (server absent, dead, or unhappy)."""


class LSPTimeout(LSPError):
    """A JSON-RPC request did not answer inside its timeout."""


class LSPUnavailable(LSPError):
    """No usable server binary / language, or the server failed to start."""


# --------------------------------------------------------------------------- #
# Small helpers: language and command resolution, paths, ranges
# --------------------------------------------------------------------------- #
def normalize_language(language: str | None) -> str:
    low = str(language or "").strip().lower()
    return LANGUAGE_ALIASES.get(low, low)


def detect_language(path: str | Path) -> str | None:
    """Registry language for a path suffix, or None when unsupported."""
    return SUFFIX_LANGUAGES.get(Path(path).suffix.lower())


def _format_command(argv: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in argv)


def _resolve_binary(name: str, root: Path) -> str | None:
    """Find a server binary in the project venv first, then on PATH.

    The project-local search is what makes the repository's
    `.venv/bin/pyright-langserver` win over an unrelated global install.
    """
    candidate = Path(name)
    if candidate.is_absolute() or os.sep in name or (
            os.altsep and os.altsep in name):
        return str(candidate) if (candidate.is_file()
                                  and os.access(candidate, os.X_OK)) else None
    for base in (root / ".venv" / "bin", ROOT / ".venv" / "bin"):
        p = base / name
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return shutil.which(name)


def _binary_available(argv: Sequence[str], root: Path) -> bool:
    if not argv:
        return False
    first = str(argv[0])
    p = Path(first)
    if p.is_absolute() or os.sep in first or (
            os.altsep and os.altsep in first):
        if not p.is_absolute():
            p = root / p
        return p.is_file() and os.access(p, os.X_OK)
    return _resolve_binary(first, root) is not None


def server_candidates(language: str, root: str | Path = ROOT
                      ) -> list[dict[str, Any]]:
    """Ordered registry candidates for a language with availability flags."""
    root = Path(root).resolve()
    out: list[dict[str, Any]] = []
    for spec in LANGUAGE_SERVERS.get(normalize_language(language), ()):
        found = _resolve_binary(spec.name, root)
        argv = [found or spec.name, *spec.args]
        out.append({
            "name": spec.name,
            "args": list(spec.args),
            "available": found is not None,
            "path": found,
            "command": _format_command(argv),
        })
    return out


def available_servers(root: str | Path = ROOT) -> dict[str, Any]:
    """Registry snapshot for status surfaces; does not spawn anything."""
    root = Path(root).resolve()
    return {
        "ok": True,
        "root": str(root),
        "languages": {lang: server_candidates(lang, root)
                      for lang in sorted(LANGUAGE_SERVERS)},
    }


def _normalize_command(command: Any) -> tuple[str, ...] | None:
    if command is None:
        return None
    if isinstance(command, (str, os.PathLike)):
        parts = shlex.split(os.fspath(command))
    elif isinstance(command, (list, tuple)):
        parts = [os.fspath(part) for part in command]
    else:
        raise TypeError("command must be a string, a path-like or a list/tuple")
    if not parts:
        raise ValueError("command is empty")
    return tuple(parts)


def _stop_process(proc: subprocess.Popen[bytes], timeout: float = 2.0) -> None:
    """Terminate a server (and its session group) if it did not exit cleanly."""
    if proc.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGTERM)
        else:
            proc.terminate()
    except (OSError, ValueError):
        try:
            proc.terminate()
        except OSError:
            pass
    try:
        proc.wait(timeout=timeout)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except (OSError, ValueError):
        try:
            proc.kill()
        except OSError:
            pass
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        pass


def _uri_to_path(uri: str) -> Path | None:
    try:
        parsed = urlparse(uri)
    except ValueError:
        return None
    if parsed.scheme != "file":
        return None
    raw = unquote(parsed.path)
    if parsed.netloc and parsed.netloc not in ("", "localhost"):
        raw = f"//{parsed.netloc}{raw}"
    if os.name == "nt" and raw.startswith("/") and len(raw) > 2 and raw[2] == ":":
        raw = raw[1:]
    return Path(raw)


def _normalize_uri(uri: str) -> str:
    path = _uri_to_path(uri)
    if path is None:
        return str(uri)
    try:
        return path.resolve().as_uri()
    except (OSError, ValueError):
        return str(uri)


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except (OSError, ValueError):
        return str(path)


def _range_fields(rng: Any) -> dict[str, Any]:
    rng = rng if isinstance(rng, dict) else {}
    start = rng.get("start") if isinstance(rng.get("start"), dict) else {}
    end = rng.get("end") if isinstance(rng.get("end"), dict) else {}

    def _int(value: Any) -> int:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    sl, sc = _int(start.get("line")), _int(start.get("character"))
    el, ec = _int(end.get("line")), _int(end.get("character"))
    return {
        "start": {"line": sl, "character": sc},
        "end": {"line": el, "character": ec},
        "line": sl,
        "character": sc,
        "end_line": el,
        "end_character": ec,
    }


def _position(line: Any, character: Any) -> dict[str, int]:
    try:
        ln = int(line)
        ch = int(character)
    except (TypeError, ValueError) as exc:
        raise LSPError("line and character must be integers") from exc
    if ln < 0 or ch < 0:
        raise LSPError("line and character are 0-based and must be >= 0")
    return {"line": ln, "character": ch}


def _normalize_location(uri: str, rng: Any, root: Path) -> dict[str, Any]:
    path = _uri_to_path(uri)
    out: dict[str, Any] = {"uri": uri, "path": None}
    if path is not None:
        out["path"] = _display_path(path, root)
    out.update(_range_fields(rng))
    return out


def _normalize_locations(result: Any, root: Path) -> list[dict[str, Any]]:
    """Accept Location, LocationLink, or arrays of either."""
    if result is None:
        return []
    items = result if isinstance(result, list) else [result]
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if "targetUri" in item:
            uri = str(item.get("targetUri") or "")
            selection = item.get("targetSelectionRange")
            target = item.get("targetRange")
            loc = _normalize_location(uri, selection or target or {}, root)
            if target is not None:
                loc["target_range"] = _range_fields(target)
        elif "uri" in item:
            uri = str(item.get("uri") or "")
            loc = _normalize_location(uri, item.get("range") or {}, root)
        else:
            continue
        out.append(loc)
    return out


def _has_results(raw: Any) -> bool:
    if isinstance(raw, list):
        return bool(raw)
    return raw is not None


def _normalize_symbol(item: Any, root: Path, default_path: str | None,
                      default_uri: str | None) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    uri = default_uri
    path = default_path
    rng: Any = item.get("selectionRange") or item.get("range") or {}
    if isinstance(item.get("location"), dict):
        loc = item["location"]
        uri = str(loc.get("uri") or default_uri or "")
        rng = loc.get("range") or {}
        p = _uri_to_path(uri) if uri else None
        path = _display_path(p, root) if p is not None else default_path
    kid = item.get("kind")
    try:
        kind = int(kid) if kid is not None else None
    except (TypeError, ValueError):
        kind = None
    entry: dict[str, Any] = {
        "name": str(item.get("name") or ""),
        "detail": item.get("detail"),
        "kind": kind,
        "kind_name": SYMBOL_KINDS.get(kind, str(kind) if kind is not None else None),
        "path": path,
        "uri": uri,
    }
    entry.update(_range_fields(rng))
    children: list[dict[str, Any]] = []
    for child in item.get("children") or []:
        normalized = _normalize_symbol(child, root, path, uri)
        if normalized is not None:
            children.append(normalized)
    entry["children"] = children
    return entry


def _count_symbols(symbols: Iterable[dict[str, Any]]) -> int:
    n = 0
    for symbol in symbols:
        n += 1 + _count_symbols(symbol.get("children") or [])
    return n


def _normalize_call_item(item: Any, root: Path) -> dict[str, Any]:
    item = item if isinstance(item, dict) else {}
    uri = str(item.get("uri") or "")
    path = _uri_to_path(uri) if uri else None
    kid = item.get("kind")
    try:
        kind = int(kid) if kid is not None else None
    except (TypeError, ValueError):
        kind = None
    out: dict[str, Any] = {
        "name": str(item.get("name") or ""),
        "detail": item.get("detail"),
        "kind": kind,
        "kind_name": SYMBOL_KINDS.get(kind, str(kind) if kind is not None else None),
        "uri": uri,
        "path": _display_path(path, root) if path is not None else None,
    }
    out.update(_range_fields(item.get("selectionRange") or item.get("range") or {}))
    return out


def _markup_text(contents: Any) -> str:
    if contents is None:
        return ""
    if isinstance(contents, str):
        return contents
    if isinstance(contents, dict):
        if "value" in contents:
            value = str(contents.get("value") or "")
            if contents.get("language"):
                return f"```{contents['language']}\n{value}\n```"
            return value
        return json.dumps(contents, sort_keys=True)
    if isinstance(contents, list):
        return "\n\n".join(_markup_text(part) for part in contents if part)
    return str(contents)


def _normalize_diagnostic(diag: Any) -> dict[str, Any]:
    diag = diag if isinstance(diag, dict) else {}
    severity = diag.get("severity")
    try:
        severity = int(severity) if severity is not None else None
    except (TypeError, ValueError):
        severity = None
    out: dict[str, Any] = {
        "message": str(diag.get("message") or ""),
        "severity": severity,
        "severity_name": SEVERITY_NAMES.get(severity,
                                              str(severity) if severity is not None else None),
        "source": diag.get("source"),
        "code": diag.get("code"),
        "tags": list(diag.get("tags") or []),
    }
    out.update(_range_fields(diag.get("range")))
    return out


def _normalize_workspace_edit(edit: Any, root: Path) -> dict[str, Any]:
    """Flatten a WorkspaceEdit into per-file TextEdits without applying it."""
    grouped: dict[str, dict[str, Any]] = {}
    resource: list[dict[str, Any]] = []

    def _add(uri: Any, edits: Any) -> None:
        if not uri:
            return
        uri_s = str(uri)
        key = _normalize_uri(uri_s)
        entry = grouped.setdefault(key, {
            "uri": key,
            "path": None,
            "edits": [],
        })
        if entry["path"] is None:
            path = _uri_to_path(key)
            entry["path"] = _display_path(path, root) if path is not None else None
        for text_edit in edits or []:
            if not isinstance(text_edit, dict):
                continue
            normalized: dict[str, Any] = {
                "newText": str(text_edit.get("newText") or ""),
            }
            normalized.update(_range_fields(text_edit.get("range")))
            entry["edits"].append(normalized)

    if isinstance(edit, dict):
        changes = edit.get("changes")
        if isinstance(changes, dict):
            for uri, edits in changes.items():
                _add(uri, edits)
        for change in edit.get("documentChanges") or []:
            if not isinstance(change, dict):
                continue
            if "textDocument" in change and "edits" in change:
                text_doc = change.get("textDocument") or {}
                _add(text_doc.get("uri"), change.get("edits") or [])
            elif change.get("kind"):
                resource.append({
                    "kind": change.get("kind"),
                    "uri": change.get("uri"),
                    "oldUri": change.get("oldUri"),
                    "newUri": change.get("newUri"),
                })
    files: list[dict[str, Any]] = []
    for entry in grouped.values():
        edits = sorted(entry["edits"], key=lambda e: (
            e["line"], e["character"], e["end_line"], e["end_character"]))
        entry["edits"] = edits
        entry["count"] = len(edits)
        files.append(entry)
    files.sort(key=lambda f: (f["path"] or "", f["uri"]))
    return {"files": files, "resource_operations": resource}


# --------------------------------------------------------------------------- #
# Client
# --------------------------------------------------------------------------- #
class LSPClient:
    """A single lazy stdio LSP session for one language and repository root.

    Typical use::

        with LSPClient(root, "python") as lsp:
            result = lsp.definition("src/app.py", 10, 4)

    All query methods return plain dicts. They never raise for an absent
    server, a dead process, a timeout or a server error; the failure is in
    `{"ok": False, "error": ...}`. Programming errors (bad command type) still
    raise at construction time.
    """

    def __init__(self, root: str | Path = ROOT, language: str = "python",
                 command: Any = None, *,
                 timeout: float = DEFAULT_TIMEOUT,
                 initialize_timeout: float = DEFAULT_INITIALIZE_TIMEOUT,
                 diagnostics_timeout: float = DEFAULT_DIAGNOSTICS_TIMEOUT,
                 env: dict[str, str] | None = None) -> None:
        self.root = Path(root).resolve()
        self.language = normalize_language(language)
        self.timeout = float(timeout)
        self.initialize_timeout = float(initialize_timeout)
        self.diagnostics_timeout = float(diagnostics_timeout)
        self._env = dict(env) if env else None
        self._explicit = _normalize_command(command)

        self._proc: subprocess.Popen[bytes] | None = None
        self._reader: threading.Thread | None = None
        self._stderr_reader: threading.Thread | None = None
        self._write_lock = threading.Lock()
        self._state_lock = threading.RLock()
        self._start_lock = threading.Lock()

        self._next_id = 0
        self._pending: dict[int, dict[str, Any]] = {}
        self._docs: dict[str, dict[str, Any]] = {}
        self._doc_events: dict[str, threading.Event] = {}
        self._diagnostics: dict[str, dict[str, Any]] = {}

        self._protocol_errors: deque[str] = deque(maxlen=MAX_PROTOCOL_ERRORS)
        self._stderr_tail: deque[str] = deque(maxlen=MAX_STDERR_LINES)
        self._server_messages: deque[str] = deque(maxlen=20)

        self._closed = False
        self._initialized = False
        self._capabilities: dict[str, Any] = {}
        self._server_info: dict[str, Any] | None = None
        self._resolved_command: list[str] | None = None
        self._command_error: str | None = None
        self._start_error: str | None = None

        # Resolve once for status. This only stats files / searches PATH.
        self._resolve_command()

    # -- context manager / lifecycle -------------------------------------- #
    def __enter__(self) -> "LSPClient":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    @property
    def closed(self) -> bool:
        return self._closed

    def _resolve_command(self) -> list[str] | None:
        if self._explicit is not None:
            argv = list(self._explicit)
            first = argv[0]
            if not _binary_available(argv, self.root):
                self._resolved_command = None
                self._command_error = f"language server binary not found: {first}"
                return None
            p = Path(first)
            if not p.is_absolute():
                resolved = _resolve_binary(first, self.root)
                if resolved:
                    argv[0] = resolved
            self._resolved_command = argv
            self._command_error = None
            return argv
        specs = LANGUAGE_SERVERS.get(self.language)
        if not specs:
            self._resolved_command = None
            self._command_error = (
                f"unsupported language {self.language!r}; supported: "
                + ", ".join(sorted(LANGUAGE_SERVERS)))
            return None
        tried: list[str] = []
        for spec in specs:
            tried.append(spec.name)
            found = _resolve_binary(spec.name, self.root)
            if found:
                self._resolved_command = [found, *spec.args]
                self._command_error = None
                return self._resolved_command
        self._resolved_command = None
        self._command_error = (
            f"no language server found for {self.language!r}; tried: "
            + ", ".join(tried)
            + " (install one or pass command=...)")
        return None

    def _ensure_started(self) -> None:
        if self._closed:
            raise LSPError("LSP client is closed")
        proc = self._proc
        if proc is not None and proc.poll() is None:
            return
        if proc is not None:
            raise LSPError(
                f"language server is not running (exit code {proc.returncode}); "
                f"status: {self._exit_detail() or 'no stderr output'}")
        with self._start_lock:
            proc = self._proc
            if proc is not None and proc.poll() is None:
                return
            if self._closed:
                raise LSPError("LSP client is closed")
            self._start_unlocked()

    def _start_unlocked(self) -> None:
        argv = self._resolve_command()
        if argv is None:
            raise LSPUnavailable(self._command_error or "language server absent")
        env = os.environ.copy()
        if self._env:
            env.update(self._env)
        try:
            proc = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.root),
                env=env,
                start_new_session=True,
            )
        except OSError as exc:
            raise LSPUnavailable(
                f"could not start language server {argv[0]}: {exc}") from exc
        self._proc = proc
        self._reader = threading.Thread(
            target=self._read_loop, args=(proc,),
            name=f"ocelot-lsp-reader-{self.language}", daemon=True)
        self._reader.start()
        self._stderr_reader = threading.Thread(
            target=self._stderr_loop, args=(proc,),
            name=f"ocelot-lsp-stderr-{self.language}", daemon=True)
        self._stderr_reader.start()
        try:
            self._initialize()
        except Exception as exc:
            failure = exc if isinstance(exc, LSPError) else LSPError(str(exc))
            self._cleanup_failed_start(proc)
            detail = self._exit_detail()
            message = str(failure)
            if detail and detail not in message:
                message = f"{message}; stderr: {detail}"
            self._start_error = message
            raise LSPError(message) from exc

    def _initialize(self) -> None:
        params = {
            "processId": os.getpid(),
            "clientInfo": {"name": "ocelot-lsp", "version": "1"},
            "rootUri": self.root.as_uri(),
            "rootPath": str(self.root),
            "workspaceFolders": ([{"uri": self.root.as_uri(),
                                   "name": self.root.name}]
                                 if self.root.name else None),
            "capabilities": _client_capabilities(),
        }
        result = self._request_raw("initialize", params,
                                   timeout=self.initialize_timeout)
        if isinstance(result, dict):
            self._capabilities = result.get("capabilities") or {}
            info = result.get("serverInfo")
            self._server_info = info if isinstance(info, dict) else None
        self._send_notification("initialized", {})
        self._initialized = True
        self._start_error = None

    def _cleanup_failed_start(self, proc: subprocess.Popen[bytes]) -> None:
        _stop_process(proc)
        for thread in (self._reader, self._stderr_reader):
            if thread is not None:
                thread.join(timeout=1.0)
        self._fail_pending(LSPError("language server failed to initialize"))
        if self._proc is proc:
            self._proc = None
        self._close_pipes(proc)

    def close(self, *, timeout: float = DEFAULT_CLOSE_TIMEOUT) -> dict[str, Any]:
        """Shut the server down (LSP shutdown/exit), then terminate if needed."""
        with self._state_lock:
            if self._closed:
                proc = self._proc
                return {"ok": True, "closed": True, "already_closed": True,
                        "language": self.language,
                        "running": bool(proc is not None
                                        and proc.poll() is None)}
            self._closed = True
            proc = self._proc
        started = proc is not None
        if proc is not None and proc.poll() is None:
            try:
                self._request_raw("shutdown", None, timeout=timeout)
            except LSPError:
                pass
            try:
                self._send_notification("exit", None)
            except LSPError:
                pass
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                _stop_process(proc)
        for thread in (self._reader, self._stderr_reader):
            if thread is not None:
                thread.join(timeout=2.0)
        self._fail_pending(LSPError("LSP client closed"))
        if proc is not None:
            self._close_pipes(proc)
        return {
            "ok": True,
            "closed": True,
            "already_closed": False,
            "language": self.language,
            "started": started,
            "returncode": proc.returncode if proc is not None else None,
            "running": bool(proc is not None and proc.poll() is None),
        }

    def _close_pipes(self, proc: subprocess.Popen[bytes]) -> None:
        for name in ("stdin", "stdout", "stderr"):
            stream = getattr(proc, name, None)
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass

    # -- framing / reader / writer ---------------------------------------- #
    def _send(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False,
                          separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
        with self._write_lock:
            proc = self._proc
            if proc is None or proc.stdin is None:
                raise LSPError("language server is not running")
            if proc.poll() is not None:
                raise LSPError(
                    f"language server exited (code {proc.returncode})")
            try:
                proc.stdin.write(header + data)
                proc.stdin.flush()
            except (BrokenPipeError, OSError) as exc:
                raise LSPError(
                    f"write to language server failed: {exc}") from exc

    def _send_notification(self, method: str, params: Any = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

    def _read_loop(self, proc: subprocess.Popen[bytes]) -> None:
        stream = proc.stdout
        if stream is None:
            self._fail_pending(LSPError("language server has no stdout"))
            return
        try:
            while True:
                message = self._read_message(stream)
                if message is None:
                    break
                try:
                    self._dispatch(message)
                except Exception as exc:  # one malformed message must not kill the reader
                    self._protocol_errors.append(
                        f"dispatch error: {type(exc).__name__}: {exc}")
        except (ValueError, OSError) as exc:
            self._protocol_errors.append(f"reader stopped: {exc}")
        finally:
            code = proc.poll()
            self._fail_pending(LSPError(
                f"language server stream closed (exit code {code})"
                + (f"; {self._exit_detail()}" if self._exit_detail() else "")))
            with self._state_lock:
                for event in self._doc_events.values():
                    event.set()

    def _read_message(self, stream: Any) -> dict[str, Any] | None:
        headers: dict[str, str] = {}
        while True:
            line = stream.readline()
            if not line:
                return None
            if line in (b"\r\n", b"\n"):
                break
            try:
                text = line.decode("ascii").strip()
            except UnicodeDecodeError:
                self._protocol_errors.append("non-ASCII protocol header")
                return None
            if not text:
                continue
            name, sep, value = text.partition(":")
            if sep:
                headers[name.strip().lower()] = value.strip()
        raw_length = headers.get("content-length")
        if raw_length is None:
            self._protocol_errors.append("message without Content-Length")
            return None
        try:
            length = int(raw_length)
        except ValueError:
            self._protocol_errors.append(
                f"bad Content-Length {raw_length!r}")
            return None
        if length <= 0 or length > MAX_MESSAGE_BYTES:
            self._protocol_errors.append(
                f"refused Content-Length {length}")
            return None
        body = stream.read(length)
        if body is None or len(body) != length:
            self._protocol_errors.append(
                f"short message body ({len(body or b'')}/{length} bytes)")
            return None
        try:
            message = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._protocol_errors.append(f"bad JSON body: {exc}")
            return None
        if not isinstance(message, dict):
            self._protocol_errors.append("JSON-RPC message is not an object")
            return None
        return message

    def _dispatch(self, message: dict[str, Any]) -> None:
        if "id" in message and ("result" in message or "error" in message):
            rid = message.get("id")
            try:
                rid_int = int(rid)
            except (TypeError, ValueError):
                self._protocol_errors.append(f"response with bad id {rid!r}")
                return
            with self._state_lock:
                slot = self._pending.pop(rid_int, None)
            if slot is None:
                # Late answer to a timed-out request is harmless.
                return
            if "error" in message:
                slot["error"] = message.get("error")
            else:
                slot["result"] = message.get("result")
            slot["event"].set()
            return
        method = message.get("method")
        if not isinstance(method, str) or not method:
            self._protocol_errors.append("message without method or result")
            return
        params = message.get("params")
        if "id" in message:
            self._answer_server_request(method, message.get("id"), params)
            return
        if method == "textDocument/publishDiagnostics":
            self._on_publish_diagnostics(params)
        elif method == "window/showMessage":
            message_text = str((params or {}).get("message") or "")
            if message_text:
                self._server_messages.append(f"showMessage: {message_text[:300]}")
        elif method == "window/logMessage":
            message_text = str((params or {}).get("message") or "")
            if message_text:
                self._server_messages.append(f"logMessage: {message_text[:300]}")
        # $/progress, telemetry/event and other notifications are ignored.

    def _answer_server_request(self, method: str, rid: Any,
                               params: Any) -> None:
        if method == "workspace/configuration":
            items = (params or {}).get("items") if isinstance(params, dict) else None
            result: Any = [None] * (len(items) if isinstance(items, list) else 0)
        elif method == "workspace/applyEdit":
            result = {"applied": False,
                      "failureReason": "ocelot LSP bridge is read-only"}
        else:
            result = None
        payload = {"jsonrpc": "2.0", "id": rid, "result": result}
        try:
            self._send(payload)
        except LSPError as exc:
            self._protocol_errors.append(
                f"could not answer {method}: {exc}")

    def _on_publish_diagnostics(self, params: Any) -> None:
        if not isinstance(params, dict):
            return
        uri = _normalize_uri(str(params.get("uri") or ""))
        if not uri:
            return
        diagnostics = params.get("diagnostics")
        diagnostics = diagnostics if isinstance(diagnostics, list) else []
        version = params.get("version")
        with self._state_lock:
            doc = self._docs.get(uri)
            if (doc is not None and version is not None
                    and isinstance(version, int)
                    and version < int(doc.get("version") or 0)):
                return  # stale publish for an older document version
            self._diagnostics[uri] = {
                "diagnostics": diagnostics,
                "version": version,
                "received_at": time.time(),
            }
            event = self._doc_events.get(uri)
            if event is not None:
                event.set()

    def _stderr_loop(self, proc: subprocess.Popen[bytes]) -> None:
        stream = proc.stderr
        if stream is None:
            return
        try:
            for raw in iter(stream.readline, b""):
                try:
                    line = raw.decode("utf-8", errors="replace").strip()
                except Exception:
                    continue
                if line:
                    self._stderr_tail.append(line[:500])
        except (OSError, ValueError):
            pass

    def _exit_detail(self) -> str:
        lines = [line for line in list(self._stderr_tail)[-4:] if line]
        return " | ".join(lines)[-700:]

    def _fail_pending(self, error: LSPError) -> None:
        with self._state_lock:
            pending = list(self._pending.values())
            self._pending.clear()
        for slot in pending:
            slot["error"] = str(error)
            slot["event"].set()

    def _request_raw(self, method: str, params: Any,
                     *, timeout: float) -> Any:
        if not isinstance(method, str) or not method:
            raise ValueError("method must be a non-empty string")
        with self._state_lock:
            proc = self._proc
            if proc is None:
                raise LSPError(f"{method}: language server is not running")
            self._next_id += 1
            rid = self._next_id
            slot: dict[str, Any] = {
                "event": threading.Event(),
                "result": None,
                "error": None,
                "method": method,
            }
            self._pending[rid] = slot
        payload: dict[str, Any] = {
            "jsonrpc": "2.0", "id": rid, "method": method,
        }
        if params is not None:
            payload["params"] = params
        try:
            self._send(payload)
        except LSPError:
            with self._state_lock:
                self._pending.pop(rid, None)
            raise
        if not slot["event"].wait(max(0.01, float(timeout))):
            with self._state_lock:
                self._pending.pop(rid, None)
            raise LSPTimeout(
                f"{method} timed out after {float(timeout):.1f}s")
        if slot["error"] is not None:
            error = slot["error"]
            if isinstance(error, dict):
                code = error.get("code")
                text = error.get("message") or error
                raise LSPError(f"{method} failed: server error {code}: {text}")
            raise LSPError(f"{method} failed: {error}")
        return slot["result"]

    # -- generic request (advanced integration use) ----------------------- #
    def request(self, method: str, params: Any = None, *,
                timeout: float | None = None) -> dict[str, Any]:
        """Send an arbitrary JSON-RPC request. Returns `{ok, result|error}`."""
        try:
            self._ensure_started()
            result = self._request_raw(
                method, params, timeout=self._timeout(timeout))
            return {"ok": True, "method": method, "result": result}
        except (LSPError, ValueError, TypeError) as exc:
            return self._fail(exc, extra={"method": method})

    # -- failure rendering ------------------------------------------------ #
    def _fail(self, exc: Exception, *,
              extra: dict[str, Any] | None = None) -> dict[str, Any]:
        proc = self._proc
        out: dict[str, Any] = {
            "ok": False,
            "error": str(exc),
            "language": self.language,
            "root": str(self.root),
            "available": self._resolve_command() is not None,
            "running": bool(proc is not None and proc.poll() is None),
        }
        if isinstance(exc, LSPTimeout):
            out["timeout"] = True
        if proc is not None and proc.poll() is not None:
            out["exit_code"] = proc.returncode
        if extra:
            out.update(extra)
        return out

    def _timeout(self, override: float | None) -> float:
        return self.timeout if override is None else float(override)

    # -- document synchronization ----------------------------------------- #
    def _path(self, path: str | Path) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self.root / p
        return p.resolve()

    def _language_id(self, path: Path) -> str:
        return _LANGUAGE_IDS_BY_SUFFIX.get(path.suffix.lower(), self.language)

    def _ensure_open(self, path: str | Path) -> dict[str, Any]:
        p = self._path(path)
        if not p.is_file():
            raise LSPError(f"no such file: {path}")
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise LSPError(f"cannot read {p}: {exc}") from exc
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        uri = p.as_uri()
        display = _display_path(p, self.root)
        self._ensure_started()
        with self._state_lock:
            record = self._docs.get(uri)
            if record is None:
                version = 1
                record = {
                    "uri": uri,
                    "path": display,
                    "version": version,
                    "sha256": digest,
                }
                self._docs[uri] = record
                self._diagnostics.pop(uri, None)
                self._doc_events[uri] = threading.Event()
                self._send_notification("textDocument/didOpen", {
                    "textDocument": {
                        "uri": uri,
                        "languageId": self._language_id(p),
                        "version": version,
                        "text": text,
                    },
                })
            elif record.get("sha256") != digest:
                version = int(record.get("version") or 1) + 1
                record["version"] = version
                record["sha256"] = digest
                self._diagnostics.pop(uri, None)
                self._doc_events[uri] = threading.Event()
                self._send_notification("textDocument/didChange", {
                    "textDocument": {"uri": uri, "version": version},
                    "contentChanges": [{"text": text}],
                })
            return dict(record)

    # -- queries ----------------------------------------------------------- #
    def definition(self, path: str | Path, line: int, character: int, *,
                   timeout: float | None = None) -> dict[str, Any]:
        """Compiler-resolved definitions at a position."""
        try:
            doc = self._ensure_open(path)
            pos = _position(line, character)
            raw = self._request_raw(
                "textDocument/definition",
                {"textDocument": {"uri": doc["uri"]}, "position": pos},
                timeout=self._timeout(timeout))
            locations = _normalize_locations(raw, self.root)
            return {
                "ok": True,
                "method": "textDocument/definition",
                "path": doc["path"],
                "line": pos["line"],
                "character": pos["character"],
                "locations": locations,
                "count": len(locations),
                "found": bool(locations),
            }
        except (LSPError, OSError, ValueError) as exc:
            return self._fail(exc, extra={
                "method": "textDocument/definition", "path": str(path)})

    def _references_raw(self, doc: dict[str, Any], pos: dict[str, int],
                        include_declaration: bool,
                        timeout: float | None, *,
                        retry_empty: bool) -> tuple[Any, int]:
        params = {
            "textDocument": {"uri": doc["uri"]},
            "position": pos,
            "context": {"includeDeclaration": bool(include_declaration)},
        }
        raw = self._request_raw("textDocument/references", params,
                                timeout=self._timeout(timeout))
        attempts = 1
        if retry_empty:
            for delay in REFERENCES_RETRY_DELAYS:
                if _has_results(raw):
                    break
                # A cold pyright can report zero before its first file scan
                # completes; retry a bounded number of times rather than
                # presenting a false "no references".
                time.sleep(delay)
                raw = self._request_raw("textDocument/references", params,
                                        timeout=self._timeout(timeout))
                attempts += 1
        return raw, attempts

    def references(self, path: str | Path, line: int, character: int, *,
                   include_declaration: bool = False,
                   retry_empty: bool = True,
                   timeout: float | None = None) -> dict[str, Any]:
        """Resolved references at a position (declaration optional).

        An empty answer is retried briefly by default because a cold server
        can answer before its workspace scan finishes. Pass
        `retry_empty=False` for a strictly single request.
        """
        try:
            doc = self._ensure_open(path)
            pos = _position(line, character)
            raw, attempts = self._references_raw(
                doc, pos, include_declaration, timeout,
                retry_empty=retry_empty)
            locations = _normalize_locations(raw, self.root)
            return {
                "ok": True,
                "method": "textDocument/references",
                "path": doc["path"],
                "line": pos["line"],
                "character": pos["character"],
                "include_declaration": bool(include_declaration),
                "locations": locations,
                "count": len(locations),
                "attempts": attempts,
                "retried": attempts > 1,
            }
        except (LSPError, OSError, ValueError) as exc:
            return self._fail(exc, extra={
                "method": "textDocument/references", "path": str(path)})

    def document_symbols(self, path: str | Path, *,
                         timeout: float | None = None) -> dict[str, Any]:
        """Document symbols, preserving the server's hierarchy."""
        try:
            doc = self._ensure_open(path)
            raw = self._request_raw(
                "textDocument/documentSymbol",
                {"textDocument": {"uri": doc["uri"]}},
                timeout=self._timeout(timeout))
            items = raw if isinstance(raw, list) else ([] if raw is None else [raw])
            symbols: list[dict[str, Any]] = []
            for item in items:
                normalized = _normalize_symbol(item, self.root,
                                               doc["path"], doc["uri"])
                if normalized is not None:
                    symbols.append(normalized)
            return {
                "ok": True,
                "method": "textDocument/documentSymbol",
                "path": doc["path"],
                "symbols": symbols,
                "count": _count_symbols(symbols),
                "top_level": len(symbols),
            }
        except (LSPError, OSError, ValueError) as exc:
            return self._fail(exc, extra={
                "method": "textDocument/documentSymbol", "path": str(path)})

    def hover(self, path: str | Path, line: int, character: int, *,
              timeout: float | None = None) -> dict[str, Any]:
        """Hover text at a position, flattened to Markdown/plain text."""
        try:
            doc = self._ensure_open(path)
            pos = _position(line, character)
            raw = self._request_raw(
                "textDocument/hover",
                {"textDocument": {"uri": doc["uri"]}, "position": pos},
                timeout=self._timeout(timeout))
            raw_dict = raw if isinstance(raw, dict) else {}
            contents = _markup_text(raw_dict.get("contents"))
            markup = raw_dict.get("contents")
            kind = markup.get("kind") if isinstance(markup, dict) else None
            return {
                "ok": True,
                "method": "textDocument/hover",
                "path": doc["path"],
                "line": pos["line"],
                "character": pos["character"],
                "found": bool(contents),
                "contents": contents,
                "markup_kind": kind,
                "range": (_range_fields(raw_dict.get("range"))
                          if raw_dict.get("range") else None),
            }
        except (LSPError, OSError, ValueError) as exc:
            return self._fail(exc, extra={
                "method": "textDocument/hover", "path": str(path)})

    def diagnostics(self, path: str | Path, *,
                    timeout: float | None = None) -> dict[str, Any]:
        """Push diagnostics from the cache, waiting for the first publish.

        Publish diagnostics is a notification, not a request. The first call
        after opening/changing a document waits up to `diagnostics_timeout`;
        later calls are served from the cache and never touch the server.
        """
        try:
            doc = self._ensure_open(path)
            uri = doc["uri"]
            with self._state_lock:
                entry = self._diagnostics.get(uri)
                event = self._doc_events.get(uri)
            if entry is not None:
                return self._diagnostic_result(doc, entry, cached=True,
                                               waited=False)
            wait = self.diagnostics_timeout if timeout is None else float(timeout)
            received = bool(event is not None and event.wait(max(0.01, wait)))
            with self._state_lock:
                entry = self._diagnostics.get(uri)
            if entry is not None:
                return self._diagnostic_result(doc, entry, cached=False,
                                               waited=True)
            return {
                "ok": True,
                "method": "textDocument/publishDiagnostics",
                "path": doc["path"],
                "uri": uri,
                "diagnostics": [],
                "count": 0,
                "cached": False,
                "waited": True,
                "published": False,
                "received": received,
                "note": (f"server published no diagnostics within "
                         f"{wait:.1f}s"),
            }
        except (LSPError, OSError, ValueError) as exc:
            return self._fail(exc, extra={
                "method": "textDocument/publishDiagnostics",
                "path": str(path)})

    def _diagnostic_result(self, doc: dict[str, Any], entry: dict[str, Any], *,
                           cached: bool, waited: bool) -> dict[str, Any]:
        items = [_normalize_diagnostic(d)
                 for d in (entry.get("diagnostics") or [])]
        items.sort(key=lambda d: (d["line"], d["character"], d["message"]))
        return {
            "ok": True,
            "method": "textDocument/publishDiagnostics",
            "path": doc["path"],
            "uri": doc["uri"],
            "diagnostics": items,
            "count": len(items),
            "cached": cached,
            "waited": waited,
            "published": True,
            "version": entry.get("version"),
            "received_at": round(float(entry.get("received_at") or 0.0), 3),
        }

    # -- call hierarchy ---------------------------------------------------- #
    def _prepare_raw(self, doc: dict[str, Any], pos: dict[str, int],
                     timeout: float | None) -> list[dict[str, Any]]:
        raw = self._request_raw(
            "textDocument/prepareCallHierarchy",
            {"textDocument": {"uri": doc["uri"]}, "position": pos},
            timeout=self._timeout(timeout))
        items = raw if isinstance(raw, list) else ([] if raw is None else [raw])
        return [item for item in items if isinstance(item, dict)]

    def prepare_call_hierarchy(self, path: str | Path, line: int,
                               character: int, *,
                               timeout: float | None = None) -> dict[str, Any]:
        """Call-hierarchy roots at a position (usually one function/method)."""
        try:
            doc = self._ensure_open(path)
            pos = _position(line, character)
            raw_items = self._prepare_raw(doc, pos, timeout)
            items = [_normalize_call_item(item, self.root)
                     for item in raw_items]
            return {
                "ok": True,
                "method": "textDocument/prepareCallHierarchy",
                "path": doc["path"],
                "line": pos["line"],
                "character": pos["character"],
                "items": items,
                "count": len(items),
            }
        except (LSPError, OSError, ValueError) as exc:
            return self._fail(exc, extra={
                "method": "textDocument/prepareCallHierarchy",
                "path": str(path)})

    def incoming_calls(self, path: str | Path, line: int, character: int, *,
                       timeout: float | None = None) -> dict[str, Any]:
        """Callers of the symbol at a position (symbol-level impact)."""
        return self._calls(path, line, character, direction="incoming",
                           timeout=timeout)

    def outgoing_calls(self, path: str | Path, line: int, character: int, *,
                       timeout: float | None = None) -> dict[str, Any]:
        """Callees of the symbol at a position (symbol-level dependencies)."""
        return self._calls(path, line, character, direction="outgoing",
                           timeout=timeout)

    def _calls(self, path: str | Path, line: int, character: int, *,
               direction: str, timeout: float | None) -> dict[str, Any]:
        method = (f"callHierarchy/{direction}Calls")
        try:
            doc = self._ensure_open(path)
            pos = _position(line, character)
            raw_items = self._prepare_raw(doc, pos, timeout)
            calls: list[dict[str, Any]] = []
            for item in raw_items:
                raw = self._request_raw(
                    method, {"item": item},
                    timeout=self._timeout(timeout))
                entries = raw if isinstance(raw, list) else ([] if raw is None else [raw])
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    node_key = "from" if direction == "incoming" else "to"
                    normalized = _normalize_call_item(
                        entry.get(node_key), self.root)
                    normalized["direction"] = direction
                    normalized["ranges"] = [
                        _range_fields(rng)
                        for rng in (entry.get("fromRanges") or [])
                        if isinstance(rng, dict)
                    ]
                    calls.append(normalized)
            return {
                "ok": True,
                "method": method,
                "path": doc["path"],
                "line": pos["line"],
                "character": pos["character"],
                "direction": direction,
                "items": len(raw_items),
                "calls": calls,
                "count": len(calls),
                **({"note": "no call-hierarchy item at this position"}
                   if not raw_items else {}),
            }
        except (LSPError, OSError, ValueError) as exc:
            return self._fail(exc, extra={"method": method, "path": str(path)})

    # -- rename preview (never writes) ------------------------------------ #
    def rename_preview(self, path: str | Path, line: int, character: int,
                       new_name: str, *,
                       timeout: float | None = None) -> dict[str, Any]:
        """Return a server WorkspaceEdit as a read-only preview.

        No file is read back and no edit is applied. The canonical edit path
        remains `ocelot_code_edit.apply_edit_script` (op list, preview first).
        """
        method = "textDocument/rename"
        try:
            name = str(new_name or "").strip()
            if not name:
                raise LSPError("new_name must be a non-empty string")
            doc = self._ensure_open(path)
            pos = _position(line, character)
            raw = self._request_raw(
                method,
                {
                    "textDocument": {"uri": doc["uri"]},
                    "position": pos,
                    "newName": name,
                },
                timeout=self._timeout(timeout))
            normalized = _normalize_workspace_edit(raw, self.root)
            total = sum(f["count"] for f in normalized["files"])
            return {
                "ok": True,
                "method": method,
                "path": doc["path"],
                "line": pos["line"],
                "character": pos["character"],
                "new_name": name,
                "files": normalized["files"],
                "file_count": len(normalized["files"]),
                "total_edits": total,
                "resource_operations": normalized["resource_operations"],
                "empty": (total == 0
                          and not normalized["resource_operations"]),
                "applied": False,
                "writes": False,
                "preview": True,
                "note": ("rename preview only; no files were written. Apply "
                         "through the semantic edit transaction."),
            }
        except (LSPError, OSError, ValueError) as exc:
            return self._fail(exc, extra={"method": method,
                                          "path": str(path),
                                          "written": False,
                                          "writes": False,
                                          "applied": False})

    # -- symbol impact ----------------------------------------------------- #
    def symbol_impact(self, path: str | Path, line: int, character: int, *,
                      include_declaration: bool = False,
                      retry_empty: bool = True,
                      timeout: float | None = None) -> dict[str, Any]:
        """Group resolved references by file for a symbol at a position.

        This is the symbol-level complement to `ocelot_repo_map.impact`; it
        never edits and returns `written: False` explicitly.
        """
        try:
            doc = self._ensure_open(path)
            pos = _position(line, character)
            refs = self.references(path, line, character,
                                   include_declaration=include_declaration,
                                   retry_empty=retry_empty,
                                   timeout=timeout)
            if not refs.get("ok"):
                return {
                    "ok": False,
                    "error": refs.get("error", "references failed"),
                    "language": self.language,
                    "root": str(self.root),
                    "path": doc["path"],
                    "line": pos["line"],
                    "character": pos["character"],
                    "files": [],
                    "file_count": 0,
                    "total": 0,
                    "written": False,
                    "writes": False,
                    "read_only": True,
                }
            groups: dict[str, dict[str, Any]] = {}
            for loc in refs.get("locations") or []:
                key = str(loc.get("path") or loc.get("uri") or "")
                group = groups.setdefault(key, {
                    "path": loc.get("path"),
                    "uri": loc.get("uri"),
                    "references": [],
                    "count": 0,
                })
                group["references"].append({
                    "line": loc["line"],
                    "character": loc["character"],
                    "end_line": loc["end_line"],
                    "end_character": loc["end_character"],
                })
                group["count"] += 1
            files = sorted(groups.values(),
                           key=lambda g: (-g["count"], g["path"] or g["uri"] or ""))
            for group in files:
                group["references"].sort(
                    key=lambda r: (r["line"], r["character"]))
            total = sum(group["count"] for group in files)
            return {
                "ok": True,
                "method": "textDocument/references",
                "symbol": {
                    "path": doc["path"],
                    "uri": doc["uri"],
                    "line": pos["line"],
                    "character": pos["character"],
                },
                "include_declaration": bool(include_declaration),
                "files": files,
                "file_count": len(files),
                "total": total,
                "attempts": int(refs.get("attempts") or 1),
                "retried": bool(refs.get("retried")),
                "written": False,
                "writes": False,
                "read_only": True,
                **({"note": "no references found"} if total == 0 else {}),
            }
        except (LSPError, OSError, ValueError) as exc:
            return self._fail(exc, extra={
                "method": "textDocument/references",
                "path": str(path),
                "written": False,
                "writes": False,
                "read_only": True})

    # -- status ------------------------------------------------------------ #
    def server_status(self) -> dict[str, Any]:
        """Honest status; never starts a server and never raises."""
        try:
            argv = self._resolve_command()
        except Exception as exc:  # defensive: status must always answer
            argv = None
            self._command_error = f"{type(exc).__name__}: {exc}"
        proc = self._proc
        running = bool(proc is not None and proc.poll() is None)
        diag_items = sum(len(entry.get("diagnostics") or [])
                         for entry in self._diagnostics.values())
        if self._explicit is not None:
            candidates = [{
                "name": Path(self._explicit[0]).name,
                "args": list(self._explicit[1:]),
                "available": argv is not None,
                "path": (argv[0] if argv else None),
                "command": _format_command(argv or self._explicit),
                "explicit": True,
            }]
        else:
            candidates = server_candidates(self.language, self.root)
        out: dict[str, Any] = {
            "ok": argv is not None and self._start_error is None,
            "language": self.language,
            "supported": self.language in LANGUAGE_SERVERS,
            "root": str(self.root),
            "command": _format_command(argv) if argv else None,
            "available": argv is not None,
            "running": running,
            "initialized": self._initialized,
            "closed": self._closed,
            "pid": proc.pid if proc is not None else None,
            "returncode": proc.returncode if proc is not None else None,
            "opened_documents": len(self._docs),
            "diagnostics": {
                "documents": len(self._diagnostics),
                "items": diag_items,
            },
            "server_info": self._server_info,
            "capabilities": sorted((self._capabilities or {}).keys()),
            "candidates": candidates,
            "stderr_tail": list(self._stderr_tail)[-10:],
            "messages": list(self._server_messages)[-5:],
            "protocol_errors": list(self._protocol_errors),
        }
        if argv is None:
            out["error"] = self._command_error or "language server unavailable"
        if self._start_error:
            out["last_start_error"] = self._start_error
        return out


def _client_capabilities() -> dict[str, Any]:
    """The conservative capability set we actually use."""
    return {
        "workspace": {
            "workspaceFolders": True,
            "configuration": True,
            "didChangeConfiguration": {"dynamicRegistration": False},
        },
        "textDocument": {
            "synchronization": {
                "dynamicRegistration": False,
                "willSave": False,
                "didSave": False,
            },
            "definition": {"dynamicRegistration": False, "linkSupport": True},
            "references": {"dynamicRegistration": False},
            "documentSymbol": {
                "dynamicRegistration": False,
                "hierarchicalDocumentSymbolSupport": True,
            },
            "hover": {
                "dynamicRegistration": False,
                "contentFormat": ["markdown", "plaintext"],
            },
            "callHierarchy": {"dynamicRegistration": False},
            "rename": {"dynamicRegistration": False, "prepareSupport": False},
            "publishDiagnostics": {
                "relatedInformation": True,
                "versionSupport": True,
            },
        },
        "window": {"workDoneProgress": True},
        "general": {"positionEncodings": ["utf-16"]},
    }


# --------------------------------------------------------------------------- #
# Shared per-language clients and explicit process cleanup
# --------------------------------------------------------------------------- #
_CLIENTS: dict[tuple[str, str, str], LSPClient] = {}
_CLIENTS_LOCK = threading.Lock()


def _command_key(command: Any) -> str:
    try:
        normalized = _normalize_command(command)
    except (TypeError, ValueError):
        return repr(command)
    return "" if normalized is None else "\x1f".join(normalized)


def get_client(root: str | Path = ROOT, language: str = "python",
               command: Any = None, **kwargs: Any) -> LSPClient:
    """Return the shared client for (root, language, command), creating it once.

    Servers are lazy: constructing the client does not spawn anything. The
    first construction's options (timeouts, env) win for later callers with
    the same key. Call `close_all()` or each client's `close()` when the
    process is shutting down; daemon threads alone do not guarantee child
    reaping.
    """
    key = (str(Path(root).resolve()), normalize_language(language),
           _command_key(command))
    with _CLIENTS_LOCK:
        client = _CLIENTS.get(key)
        if client is None or client.closed:
            client = LSPClient(root, language, command, **kwargs)
            _CLIENTS[key] = client
        return client


def close_all() -> dict[str, Any]:
    """Close every shared client. Returns a compact receipt."""
    with _CLIENTS_LOCK:
        clients = list(_CLIENTS.values())
        _CLIENTS.clear()
    results = [client.close() for client in clients]
    return {
        "ok": True,
        "closed": len(results),
        "started": sum(1 for r in results if r.get("started")),
    }


__all__ = [
    "DEFAULT_CLOSE_TIMEOUT",
    "DEFAULT_DIAGNOSTICS_TIMEOUT",
    "DEFAULT_INITIALIZE_TIMEOUT",
    "DEFAULT_TIMEOUT",
    "LANGUAGE_ALIASES",
    "LANGUAGE_SERVERS",
    "LSPClient",
    "LSPError",
    "LSPTimeout",
    "LSPUnavailable",
    "REFERENCES_RETRY_DELAYS",
    "ROOT",
    "SEVERITY_NAMES",
    "SUFFIX_LANGUAGES",
    "SYMBOL_KINDS",
    "ServerSpec",
    "available_servers",
    "close_all",
    "detect_language",
    "get_client",
    "normalize_language",
    "server_candidates",
]
