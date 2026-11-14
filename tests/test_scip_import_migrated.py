"""test_scip_import_migrated — SCIP JSON normalization, records, edges.

The supported path is the JSON export from the Sourcegraph SCIP CLI
(``scip print --json``). The fixture exercises two documents, definition and
reference roles, a duplicate occurrence, local and external symbols, several
accepted range/role spellings, path normalization, repo-map edges, the
file-level summary, deterministic JSON, and the honest protobuf refusal.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ocelot_scip_import import (
    ScipFormatError,
    ScipProtobufUnavailableError,
    load_scip,
    load_scip_json,
    normalize_path,
    parse_scip_symbol,
    scip_dumps,
    scip_file_summary,
    scip_import,
    scip_protobuf_status,
    scip_records,
    scip_summary,
    scip_to_graph_records,
    scip_to_repo_map_edges,
)

ALPHA = "scip-python python demo 0.1.0 `src/app.py`/alpha()."
REMOTE = "scip-python python lib 1.0.0 `lib/remote.py`/remote()."


def _fixture() -> dict:
    return {
        "metadata": {
            "version": 0,
            "project_root": "file:///repo",
            "tool_info": {"name": "scip-python", "version": "0.1.0"},
        },
        "documents": [
            {
                "relative_path": "./src/app.py",
                "language": "python",
                "occurrences": [
                    {"symbol": ALPHA, "symbol_roles": 1,
                     "range": [4, 6, 4, 11]},
                ],
                "symbols": [
                    {"symbol": ALPHA, "display_name": "alpha",
                     "kind": "Function", "documentation": ["Does alpha."]},
                ],
            },
            {
                "relativePath": "src\\use.py",
                "language": "python",
                "occurrences": [
                    # A read reference, repeated verbatim. Must dedup.
                    {"symbol": ALPHA, "symbol_roles": 8,
                     "range": [2, 15, 2, 20]},
                    {"symbol": ALPHA, "symbol_roles": 8,
                     "range": [2, 15, 2, 20]},
                    # SCIP's compact 3-integer single-line range, role text.
                    {"symbol": ALPHA, "symbolRoles": "ReadAccess",
                     "range": [5, 12, 17]},
                    # Local symbol: a record, never a cross-file edge.
                    {"symbol": "local 1", "symbol_roles": 8,
                     "range": {"start": {"line": 8, "character": 4},
                               "end": {"line": 8, "character": 9}}},
                    # Flat camelCase range fields, unspecified role = ref.
                    {"symbol": REMOTE, "symbol_roles": 0,
                     "startLine": 10, "startCharacter": 1,
                     "endLine": 10, "endCharacter": 6},
                ],
            },
        ],
        "external_symbols": [
            {"symbol": REMOTE, "displayName": "remote_fn", "kind": 11},
        ],
    }


@pytest.fixture()
def index_path(tmp_path: Path) -> Path:
    path = tmp_path / "index.scip.json"
    path.write_text(json.dumps(_fixture()), encoding="utf-8")
    return path


def test_load_normalizes_paths_and_spellings(index_path: Path) -> None:
    index = load_scip_json(index_path)
    assert index["format"] == "scip-json"
    assert [doc["path"] for doc in index["documents"]] == [
        "src/app.py", "src/use.py"]
    app, use = index["documents"]
    assert app["occurrences"][0]["range"] == [4, 6, 4, 11]
    ranges = [item["range"] for item in use["occurrences"]]
    # load_scip_json preserves occurrence multiplicity; records merge it.
    assert ranges.count([2, 15, 2, 20]) == 2
    assert [5, 12, 5, 17] in ranges
    assert [8, 4, 8, 9] in ranges
    assert [10, 1, 10, 6] in ranges
    # Local and external symbol metadata are normalized too.
    assert index["external_symbols"][0]["display_name"] == "remote_fn"
    assert index["external_symbols"][0]["kind"] == "Function"


def test_definitions_references_and_dedup(index_path: Path) -> None:
    index = load_scip_json(index_path)
    app, use = index["documents"]

    app_records = scip_records(app)
    assert set(app_records) == {"definitions", "references"}
    assert len(app_records["definitions"]) == 1
    definition = app_records["definitions"][0]
    assert definition["path"] == "src/app.py"
    assert definition["symbol"] == ALPHA
    assert definition["name"] == "alpha"
    assert definition["kind"] == "definition"
    assert definition["roles"] == ["definition"]
    assert definition["range"] == [4, 6, 4, 11]
    assert definition["line"] == 5  # 1-based editor line
    assert app_records["references"] == []

    use_records = scip_records(use)
    assert use_records["definitions"] == []
    assert len(use_records["references"]) == 4
    assert all(rec["path"] == "src/use.py"
               for rec in use_records["references"])
    alpha_refs = [rec for rec in use_records["references"]
                  if rec["symbol"] == ALPHA]
    # The duplicate occurrence was merged, the other range remained.
    assert [rec["range"] for rec in alpha_refs] == [
        [2, 15, 2, 20], [5, 12, 5, 17]]
    assert all(rec["roles"] == ["read_access"] for rec in alpha_refs)
    local = next(rec for rec in use_records["references"]
                 if rec["symbol"] == "local 1")
    assert local["local"] is True
    remote = next(rec for rec in use_records["references"]
                  if rec["symbol"] == REMOTE)
    assert remote["name"] == "remote"  # parsed from the symbol string
    assert remote["roles"] == []

    # Aggregating the whole index yields the same unique records, and uses
    # index-level external_symbols for the human-readable remote name.
    aggregate = scip_records(index)
    assert len(aggregate["definitions"]) == 1
    assert len(aggregate["references"]) == 4
    aggregate_remote = next(
        rec for rec in aggregate["references"] if rec["symbol"] == REMOTE)
    assert aggregate_remote["name"] == "remote_fn"


def test_edges_skip_local_and_external() -> None:
    records = scip_records(_fixture())
    assert scip_to_repo_map_edges(records) == [
        {"src": "src/use.py", "tgt": "src/app.py", "weight": 2.0},
    ]


def test_graph_records_summary_and_stable_json(index_path: Path) -> None:
    index = load_scip_json(index_path)
    graph = scip_to_graph_records(index)
    assert graph["ok"] is True
    assert graph["format"] == "scip-graph-records"
    assert graph["documents"] == 2
    assert graph["totals"] == {
        "files": 2,
        "definitions": 1,
        "references": 4,
        "local_definitions": 0,
        "local_references": 1,
        "symbols": 2,
        "defined_symbols": 1,
        "edges": 1,
    }
    app = next(row for row in graph["files"] if row["path"] == "src/app.py")
    use = next(row for row in graph["files"] if row["path"] == "src/use.py")
    assert app["definitions"] == 1 and app["incoming_edges"] == 1
    assert use["references"] == 4 and use["outgoing_edges"] == 1
    assert use["local_references"] == 1

    summary = scip_file_summary(index)
    assert summary["format"] == "scip-file-summary"
    assert summary["totals"] == graph["totals"]
    assert summary["files"] == graph["files"]
    assert scip_summary(index)["totals"] == graph["totals"]
    # The payload can be fed back without losing its file summary.
    assert scip_file_summary(graph)["totals"] == graph["totals"]
    assert scip_to_graph_records(graph)["documents"] == 2

    # Same input -> byte-identical sorted JSON; the payload round-trips.
    assert scip_dumps(graph) == scip_dumps(scip_to_graph_records(index))
    assert json.loads(scip_dumps(graph)) == graph


def test_one_shot_cli_payload_is_json_safe(
        index_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    payload = scip_import(index_path)
    assert payload["ok"] is True
    assert payload["input_format"] == "scip-json"
    assert payload["source"] == str(index_path)
    assert payload["edges"] == [
        {"src": "src/use.py", "tgt": "src/app.py", "weight": 2.0},
    ]
    assert payload["definitions"][0]["name"] == "alpha"
    assert payload["totals"]["references"] == 4
    json.dumps(payload, sort_keys=True)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_symbol_and_path_parsing() -> None:
    parsed = parse_scip_symbol(ALPHA)
    assert parsed["scheme"] == "scip-python"
    assert parsed["package_manager"] == "python"
    assert parsed["package_name"] == "demo"
    assert parsed["package_version"] == "0.1.0"
    assert parsed["name"] == "alpha"
    assert parsed["qualname"].endswith("alpha")
    assert parsed["local"] is False
    escaped = parse_scip_symbol(
        "scip-python python demo 0.1.0 `src/x.py`/`odd name`().")
    assert escaped["name"] == "odd name"
    local = parse_scip_symbol("local 7")
    assert local["local"] is True
    assert local["name"] == "7"

    assert normalize_path("./src//app.py") == "src/app.py"
    assert normalize_path("src\\use.py") == "src/use.py"
    assert normalize_path("file:///repo/src/a.py", root="/repo") == "src/a.py"
    assert normalize_path("/repo/src/a.py", root="/repo") == "src/a.py"
    assert normalize_path("C:\\repo\\src\\a.py",
                          root="C:\\repo") == "src/a.py"
    with pytest.raises(ValueError):
        normalize_path("../outside.py")
    with pytest.raises(ValueError):
        normalize_path("/absolute/without/root.py")

    absolute = load_scip_json({
        "documents": [{
            "relative_path": "/repo/src/a.py",
            "occurrences": [],
        }],
    }, root="/repo")
    assert absolute["documents"][0]["path"] == "src/a.py"
    project_root = load_scip_json({
        "metadata": {"project_root": "file:///repo"},
        "documents": [{
            "relativePath": "/repo/src/b.py",
            "occurrences": [],
        }],
    })
    assert project_root["documents"][0]["path"] == "src/b.py"


def test_invalid_json_is_refused_honestly(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(ScipFormatError, match="invalid SCIP JSON"):
        load_scip_json(broken)
    with pytest.raises(ScipFormatError, match="missing a documents"):
        load_scip_json({"metadata": {}})


def test_protobuf_path_refuses_without_scip_pb2(tmp_path: Path) -> None:
    status = scip_protobuf_status()
    if status["available"]:
        pytest.skip("scip_pb2 is installed; the protobuf path is live")
    dummy = tmp_path / "index.scip"
    dummy.write_bytes(b"\x0a\x00")
    with pytest.raises(ScipProtobufUnavailableError) as error:
        load_scip(dummy)
    message = str(error.value).lower()
    assert "protobuf" in message
    assert "scip_pb2" in message
    assert "not installed" in message
    # A JSON export remains the supported path in this environment.
    with pytest.raises(ScipProtobufUnavailableError):
        load_scip(dummy, format_hint="protobuf")
