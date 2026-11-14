"""test_nav_wiring_migrated — symbol graph + LSP refinement, post-edit diagnostics.

Covers W3-B of DEV_TOOLING_V2_PLAN.md through `DevMemory` and the MCP server:

* `symbol_graph` callers / callees / impact / resolve on a small fixture repo;
* `precise=True`: LSP references confirm depth-1 rows, unconfirmed rows stay
  False, and an LSP-only reference maps to its innermost enclosing symbol;
* `precise=True` with no language server: a precision note and rows identical
  to the syntactic result;
* post-edit diagnostics after an applied write (didChange, then publish), and
  the journal record of their counts;
* the MCP tool list, string-boolean coercion and unknown-argument rejection.

The LSP side is a small fake stdio server written per test with its reply
configuration embedded. It is installed by replacing the python entry of
`LANGUAGE_SERVERS`, so the real server registry resolves to it. Nothing here
needs pyright. The live pyright check is a separate script, not a gate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.ocelot_dev_memory import (
    DevMemory, _name_utf16_col, _utf16_col, build_index)
from scripts.ocelot_dev_memory_mcp import DevMemoryServer
from scripts.ocelot_lsp import LANGUAGE_SERVERS, ServerSpec, close_all

CALC = (
    "# café α: comment above the target\n"   # line 1
    "def target(x):\n"                       # line 2
    "    return x + 1\n"                     # line 3
    "\n"                                     # line 4
    "\n"                                     # line 5
    "def caller_one():\n"                    # line 6
    "    return target(1)\n"                 # line 7
    "\n"                                     # line 8
    "\n"                                     # line 9
    "def caller_two():\n"                    # line 10
    "    return target(2)\n"                 # line 11
)
LATE = (
    "def dispatch(f):\n"                     # line 1
    "    def inner():\n"                     # line 2
    "        return f(3)\n"                  # line 3
    "    return inner\n"                     # line 4
)
EDIT_ME = "def tweak():\n    return 1\n"
TARGET = "domains/calc.py::target"

FAKE_SERVER = r'''"""Fake stdio LSP server for tests/test_nav_wiring_migrated.py."""
import json
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

CONFIG = json.loads(r"""__CONFIG__""")
ROOT = None
INITIALIZED = False


def log(message):
    with open(CONFIG["log"], "a", encoding="utf-8") as handle:
        handle.write(json.dumps(message, ensure_ascii=False) + "\n")


def read_message():
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        name, sep, value = line.decode("ascii").partition(":")
        if sep:
            headers[name.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = sys.stdin.buffer.read(length)
    return json.loads(body.decode("utf-8"))


def send(message):
    body = json.dumps(message, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def result(rid, value):
    send({"jsonrpc": "2.0", "id": rid, "result": value})


def error(rid, code, message):
    send({"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}})


def notify(method, params):
    send({"jsonrpc": "2.0", "method": method, "params": params})


def uri_to_path(value):
    return Path(unquote(urlparse(value).path))


def rng(sl, sc, el, ec):
    return {"start": {"line": sl, "character": sc},
            "end": {"line": el, "character": ec}}


def publish(doc):
    text = doc.get("text", "")
    diagnostics = []
    if "BROKEN" in text:
        diagnostics = [{"range": rng(0, 0, 0, 6), "severity": 1,
                        "source": "fake", "message": "broken token"}]
    notify("textDocument/publishDiagnostics",
           {"uri": doc.get("uri"), "version": doc.get("version"),
            "diagnostics": diagnostics})


def main():
    global ROOT, INITIALIZED
    while True:
        message = read_message()
        if message is None:
            return
        log(message)
        method = message.get("method")
        rid = message.get("id")
        params = message.get("params") or {}
        if method is None:
            continue
        if method == "initialize":
            ROOT = uri_to_path(params.get("rootUri") or "file:///")
            result(rid, {"capabilities": {"referencesProvider": True},
                         "serverInfo": {"name": "fake-pyright", "version": "1"}})
        elif method == "initialized":
            INITIALIZED = True
        elif method == "exit":
            return
        elif not INITIALIZED:
            error(rid, -32002, "server not initialized")
        elif method == "shutdown":
            result(rid, None)
        elif method == "textDocument/didOpen":
            publish(dict(params.get("textDocument") or {}))
        elif method == "textDocument/didChange":
            doc = dict(params.get("textDocument") or {})
            doc["text"] = (params.get("contentChanges") or [{}])[0].get("text", "")
            publish(doc)
        elif method == "textDocument/references":
            locations = []
            for ref in CONFIG["references"]:
                locations.append({
                    "uri": (ROOT / ref["path"]).resolve().as_uri(),
                    "range": rng(ref["line"], 0, ref["line"], 1)})
            result(rid, locations)
        else:
            error(rid, -32601, f"method not found: {method}")


if __name__ == "__main__":
    main()
'''


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


@pytest.fixture()
def repo(tmp_path: Path):
    _write(tmp_path / "domains" / "calc.py", CALC)
    _write(tmp_path / "domains" / "late.py", LATE)
    _write(tmp_path / "domains" / "edit_me.py", EDIT_ME)
    out = tmp_path / "var" / "dev_graph.json"
    build_index(tmp_path, out, include_docs="none",
                include_git=False, include_scripts=False)
    yield tmp_path
    close_all()


def _memory(root: Path) -> DevMemory:
    return DevMemory(root / "var" / "dev_graph.json",
                     root / "var" / "journal.jsonl", root=root)


def _install_fake_server(monkeypatch: pytest.MonkeyPatch, root: Path,
                         references: list[tuple[str, int]] = ()) -> Path:
    """Route the python LSP entry to the fake server. Returns its log file.

    `references` are (repo-relative path, 0-based line) pairs that the fake
    server returns for every textDocument/references request.
    """
    log = root.parent / f"{root.name}_fake_lsp.log"
    server = root.parent / f"{root.name}_fake_lsp_server.py"
    config = json.dumps({
        "log": str(log),
        "references": [{"path": p, "line": line} for p, line in references],
    })
    server.write_text(FAKE_SERVER.replace("__CONFIG__", config),
                      encoding="utf-8")
    monkeypatch.setitem(LANGUAGE_SERVERS, "python",
                        (ServerSpec(sys.executable, (str(server),)),))
    return log


def _install_missing_server(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(LANGUAGE_SERVERS, "python",
                        (ServerSpec("/nonexistent/pyright-langserver-missing"),))


def _messages(log: Path) -> list[dict[str, Any]]:
    if not log.exists():
        return []
    return [json.loads(line) for line in
            log.read_text(encoding="utf-8").splitlines() if line.strip()]


# --------------------------------------------------------------------------- #
# syntactic symbol graph through DevMemory
# --------------------------------------------------------------------------- #
def test_callers_callees_impact_resolve_without_lsp(repo: Path) -> None:
    mem = _memory(repo)
    callers = mem.symbol_graph("callers", TARGET)
    assert callers["ok"] is True
    assert callers["symbol"] == TARGET
    assert sorted(r["qualname"] for r in callers["results"]) == [
        "caller_one", "caller_two"]
    assert all(r["depth"] == 1 and r["resolution"] == "local"
               for r in callers["results"])
    assert "precision" not in callers and "lsp_only" not in callers

    bare = mem.symbol_graph("callers", "target")
    assert bare["ok"] is True and bare["symbol"] == TARGET

    callees = mem.symbol_graph("callees", "domains/calc.py::caller_one")
    assert callees["ok"] is True
    assert [r["id"] for r in callees["results"]] == [TARGET]

    impact = mem.symbol_graph("impact", TARGET, depth=2)
    assert impact["ok"] is True
    assert [f["file"] for f in impact["files"]] == ["domains/calc.py"]
    assert impact["files"][0]["symbols"] == 2

    resolved = mem.symbol_graph("resolve", "target")
    assert resolved["ok"] is True and resolved["matches"] == [TARGET]
    assert mem.symbol_graph("resolve", "no_such_symbol_here")["ok"] is False
    assert mem.symbol_graph("callers", TARGET, depth=0)["ok"] is False
    assert mem.symbol_graph("nonsense", TARGET)["ok"] is False


# --------------------------------------------------------------------------- #
# precise=True: LSP confirmation and LSP-only references
# --------------------------------------------------------------------------- #
def test_precise_confirms_callers_and_maps_lsp_only(
        repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # caller_one's call is on line 7 (0-based 6). The second reference sits on
    # line 3 of late.py (0-based 2), inside the nested `inner`, which no
    # syntactic row covers.
    log = _install_fake_server(monkeypatch, repo,
                               [("domains/calc.py", 6),
                                ("domains/late.py", 2)])
    mem = _memory(repo)
    res = mem.symbol_graph("callers", TARGET, precise=True)
    assert res["ok"] is True
    flags = {r["qualname"]: r["lsp_confirmed"] for r in res["results"]}
    assert flags == {"caller_one": True, "caller_two": False}
    assert res["lsp_only"] == [{
        "id": "domains/late.py::dispatch.inner",
        "file": "domains/late.py",
        "line": 3,
        "qualname": "dispatch.inner",
    }]
    assert res["precision"] == {
        "lsp": "used", "server": sys.executable, "references": 2,
        "confirmed": 1, "unconfirmed": 1, "lsp_only": 1,
    }
    # The request goes to the line of `def target` (0-based), at the UTF-16
    # column of `target` on that line: 4 ("def " is four ASCII characters).
    requests = [m for m in _messages(log)
                if m.get("method") == "textDocument/references"]
    assert len(requests) == 1
    assert requests[0]["params"]["position"] == {"line": 1, "character": 4}
    assert requests[0]["params"]["textDocument"]["uri"].endswith(
        "/domains/calc.py")


def test_precise_impact_uses_the_same_refinement(
        repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_server(monkeypatch, repo, [("domains/calc.py", 6)])
    res = _memory(repo).symbol_graph("impact", TARGET, depth=2, precise=True)
    flags = {r["qualname"]: r["lsp_confirmed"] for r in res["results"]}
    assert flags == {"caller_one": True, "caller_two": False}
    assert res["lsp_only"] == []
    assert res["precision"]["confirmed"] == 1


def test_precise_without_server_matches_syntactic_rows(
        repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_missing_server(monkeypatch)
    mem = _memory(repo)
    plain = mem.symbol_graph("callers", TARGET)
    precise = mem.symbol_graph("callers", TARGET, precise=True)
    assert precise["precision"]["lsp"].startswith("unavailable: ")
    assert precise["results"] == plain["results"]
    assert all("lsp_confirmed" not in r for r in precise["results"])
    assert "lsp_only" not in precise


def test_precise_on_other_ops_is_not_applicable(repo: Path) -> None:
    res = _memory(repo).symbol_graph("callees", "domains/calc.py::caller_one",
                                     precise=True)
    assert res["ok"] is True
    assert res["precision"]["lsp"].startswith("not applicable")


def test_precise_never_starts_a_server_when_none_is_available(
        repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = _install_fake_server(monkeypatch, repo)
    _install_missing_server(monkeypatch)
    _memory(repo).symbol_graph("callers", TARGET, precise=True)
    assert not log.exists()


# --------------------------------------------------------------------------- #
# UTF-16 columns
# --------------------------------------------------------------------------- #
def test_utf16_column_counts_astral_characters_as_two_units() -> None:
    assert _utf16_col("a\U0001F600b", 2) == 3  # "a" 1 unit, emoji 2 units
    assert _utf16_col("a\U0001F600b", 3) == 4  # end of string
    assert _utf16_col("café", 3) == 3          # BMP letters count as 1


def test_name_column_is_found_after_the_def_keyword() -> None:
    # "# 😀 def é(x):": the emoji is 2 UTF-16 units, so "é" starts at unit 9.
    assert _name_utf16_col("# \U0001F600 def \u00e9(x):", "\u00e9") == 9
    assert _name_utf16_col("def a(b):", "a") == 4
    # A name that also appears before the keyword is not picked.
    assert _name_utf16_col("class f(f):", "f") == 6
    assert _name_utf16_col("x = 1", "missing") is None


# --------------------------------------------------------------------------- #
# post-edit diagnostics
# --------------------------------------------------------------------------- #
def test_post_edit_diagnostics_reflect_the_new_content(
        repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = _install_fake_server(monkeypatch, repo)
    mem = _memory(repo)
    # Open the clean file first so the edit must go out as didChange.
    before = mem.lsp_diagnostics("domains/edit_me.py", timeout=5.0)
    assert before["ok"] is True and before["count"] == 0

    res = mem.edit({"file": "domains/edit_me.py", "apply": True,
                    "ops": [{"op": "replace_body", "symbol": "tweak",
                             "text": "return 'BROKEN'"}]})
    assert res["applied"] is True
    diag = res["diagnostics"]
    assert diag["ok"] is True
    assert diag["count"] == 1 and diag["errors"] == 1 and diag["warnings"] == 0
    assert diag["published"] is True
    assert diag["items"][0]["line1"] == 1
    assert diag["items"][0]["message"] == "broken token"

    changes = [m for m in _messages(log)
               if m.get("method") == "textDocument/didChange"]
    assert changes and changes[-1]["params"]["textDocument"]["version"] == 2
    assert "BROKEN" in changes[-1]["params"]["contentChanges"][0]["text"]

    entry = mem.journal_recent(1)[0]
    assert entry["diagnostics"]["errors"] == 1
    assert entry["diagnostics"]["count"] == 1
    assert "items" not in entry["diagnostics"]


def test_post_edit_diagnostics_can_be_turned_off(
        repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_server(monkeypatch, repo)
    mem = _memory(repo)
    res = mem.edit({"file": "domains/edit_me.py", "apply": True,
                    "ops": [{"op": "replace_body", "symbol": "tweak",
                             "text": "return 2"}]}, diagnostics=False)
    assert res["applied"] is True
    assert res["diagnostics"] == {"skipped": "diagnostics=false"}
    assert mem.journal_recent(1)[0]["diagnostics"] == {
        "skipped": "diagnostics=false"}


def test_preview_does_not_run_diagnostics(
        repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = _install_fake_server(monkeypatch, repo)
    res = _memory(repo).edit({"file": "domains/edit_me.py", "apply": False,
                              "ops": [{"op": "replace_body", "symbol": "tweak",
                                       "text": "return 3"}]})
    assert res["applied"] is False
    assert "diagnostics" not in res
    assert not any(m.get("method") == "textDocument/didOpen"
                   for m in _messages(log))


def test_edit_succeeds_and_records_skip_when_no_server(
        repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_missing_server(monkeypatch)
    mem = _memory(repo)
    res = mem.edit({"file": "domains/edit_me.py", "apply": True,
                    "ops": [{"op": "replace_body", "symbol": "tweak",
                             "text": "return 4"}]})
    assert res["applied"] is True
    assert res["diagnostics"]["skipped"].startswith("unavailable: ")
    assert mem.journal_recent(1)[0]["diagnostics"]["skipped"].startswith(
        "unavailable: ")


# --------------------------------------------------------------------------- #
# MCP surface
# --------------------------------------------------------------------------- #
def _call(name: str, arguments: Any, req_id: int = 1) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "method": "tools/call",
            "params": {"name": name, "arguments": arguments}}


def test_mcp_lists_the_symbol_tools_and_lsp_position_notes(repo: Path) -> None:
    server = DevMemoryServer(_memory(repo))
    listed = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    tools = {t["name"]: t for t in listed["result"]["tools"]}
    for name in ("dev_symbol_callers", "dev_symbol_callees",
                 "dev_symbol_graph_impact", "dev_symbol_resolve"):
        assert name in tools
        assert tools[name]["inputSchema"]["additionalProperties"] is False
    callers_props = tools["dev_symbol_callers"]["inputSchema"]["properties"]
    assert callers_props["depth"]["type"] == "integer"
    assert callers_props["min_confidence"]["type"] == "number"
    assert callers_props["precise"]["type"] == "boolean"
    assert tools["dev_symbol_callers"]["inputSchema"]["required"] == ["symbol"]
    impact_props = tools["dev_symbol_graph_impact"]["inputSchema"]["properties"]
    assert impact_props["depth"]["default"] == 3
    assert tools["dev_symbol_resolve"]["inputSchema"]["properties"].keys() == {
        "symbol"}
    assert "syntactic" in tools["dev_symbol_callers"]["description"]
    assert "precise=true" in tools["dev_symbol_callers"]["description"]
    assert "0-based" in tools["dev_definition"]["description"]
    assert "subtract 1" in tools["dev_references"]["description"]
    assert "diagnostics" in tools["dev_edit"]["inputSchema"]["properties"]


def test_mcp_string_boolean_is_coerced_and_unknown_arg_rejected(
        repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_server(monkeypatch, repo, [("domains/calc.py", 6)])
    server = DevMemoryServer(_memory(repo))
    resp = server.handle(_call("dev_symbol_callers",
                               {"symbol": TARGET, "precise": "false"}))
    assert resp["result"]["isError"] is False
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert "precision" not in payload

    resp = server.handle(_call("dev_symbol_callers",
                               {"symbol": TARGET, "precise": "true"}))
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["precision"]["lsp"] == "used"

    resp = server.handle(_call("dev_symbol_callers",
                               {"symbol": TARGET, "bogus": 1}))
    assert resp["error"]["code"] == -32602
    assert "bogus" in resp["error"]["message"]


def test_mcp_symbol_resolve_and_impact_round_trip(repo: Path) -> None:
    server = DevMemoryServer(_memory(repo))
    resp = server.handle(_call("dev_symbol_resolve", {"symbol": "target"}))
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["matches"] == [TARGET]
    resp = server.handle(_call("dev_symbol_graph_impact",
                               {"symbol": TARGET, "depth": "2"}))
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["ok"] is True and payload["depth"] == 2
