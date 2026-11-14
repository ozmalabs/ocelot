"""test_cst_edit_migrated — Rust/Lua edits address the CST, not a text patch.

The graph is synthetic in these tests: `tree_sitter` is not installed in the
repository `.venv`, and the adapter's contract is the same `CstNode` graph
`domains.ts_ingest.ingest_source` produces when the grammars are present.
Comments and whitespace are explicit leaves, so the round-trip and
outside-target preservation claims are exercised on the real lossless shape.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ocelot_code_edit import CodeEditError, sha256_text
from scripts.ocelot_cst_edit import (
    CstGraph,
    apply_cst_edit_script,
    cst_graph_from_nested,
    parse_cst_path,
    tree_sitter_available,
)

RUST_SOURCE = (
    "fn main() {\n"
    "    // keep café before\n"
    "    let x = 1;\n"
    "\n"
    "    let y = 2;\n"
    "    // keep after\n"
    "}\n"
)

INT_X = "child[0].child[5].child[3].child[5]"
LET_X = "child[0].child[5].child[3]"
LET_Y = "child[0].child[5].child[5]"
INT_Y = "child[0].child[5].child[5].child[5]"

LUA_SOURCE = (
    "local function f()\n"
    "    -- keep lua\n"
    "    local x = 1\n"
    "    return x\n"
    "end\n"
)

LUA_INT_X = "child[0].child[3].child[3].child[5]"


def _leaf(kind: str, text: str) -> dict:
    return {"kind": kind, "text": text}


def _rust_tree() -> dict:
    let_x = {
        "kind": "let_declaration",
        "children": [
            _leaf("keyword", "let "),
            _leaf("identifier", "x"),
            _leaf("whitespace", " "),
            _leaf("operator", "="),
            _leaf("whitespace", " "),
            _leaf("integer_literal", "1"),
            _leaf("punctuation", ";"),
        ],
    }
    let_y = {
        "kind": "let_declaration",
        "children": [
            _leaf("keyword", "let "),
            _leaf("identifier", "y"),
            _leaf("whitespace", " "),
            _leaf("operator", "="),
            _leaf("whitespace", " "),
            _leaf("integer_literal", "2"),
            _leaf("punctuation", ";"),
        ],
    }
    block = {
        "kind": "block",
        "children": [
            _leaf("whitespace", "\n    "),
            _leaf("line_comment", "// keep café before"),
            _leaf("whitespace", "\n    "),
            let_x,
            _leaf("whitespace", "\n\n    "),
            let_y,
            _leaf("whitespace", "\n    "),
            _leaf("line_comment", "// keep after"),
            _leaf("whitespace", "\n"),
        ],
    }
    function = {
        "kind": "function_item",
        "children": [
            _leaf("keyword", "fn "),
            _leaf("identifier", "main"),
            _leaf("parameters", "()"),
            _leaf("whitespace", " "),
            _leaf("punctuation", "{"),
            block,
            _leaf("punctuation", "}"),
        ],
    }
    return {
        "kind": "source_file",
        "children": [function, _leaf("whitespace", "\n")],
    }


def _lua_tree() -> dict:
    block = {
        "kind": "block",
        "children": [
            _leaf("whitespace", "\n    "),
            _leaf("comment", "-- keep lua"),
            _leaf("whitespace", "\n    "),
            {
                "kind": "variable_declaration",
                "children": [
                    _leaf("keyword", "local "),
                    _leaf("identifier", "x"),
                    _leaf("whitespace", " "),
                    _leaf("operator", "="),
                    _leaf("whitespace", " "),
                    _leaf("integer", "1"),
                ],
            },
            _leaf("whitespace", "\n    "),
            {
                "kind": "return_statement",
                "children": [
                    _leaf("keyword", "return"),
                    _leaf("whitespace", " "),
                    _leaf("identifier", "x"),
                ],
            },
            _leaf("whitespace", "\n"),
        ],
    }
    function = {
        "kind": "function_declaration",
        "children": [
            _leaf("keyword", "local function "),
            _leaf("identifier", "f"),
            _leaf("parameters", "()"),
            block,
            _leaf("keyword", "end"),
        ],
    }
    return {
        "kind": "source_file",
        "children": [function, _leaf("whitespace", "\n")],
    }


def _fixture(root: Path, name: str = "lib.rs") -> Path:
    graph = cst_graph_from_nested(_rust_tree() if name.endswith(".rs")
                                  else _lua_tree())
    path = root / name
    path.write_text(graph.render(), encoding="utf-8")
    return path


def _apply(root: Path, graph: CstGraph, ops: list[dict], *,
           write: bool = False, file: str = "lib.rs", **extra):
    script = {"file": file, "cst_graph": graph, "ops": ops}
    script.update(extra)
    return apply_cst_edit_script(root, script, write=write)


def _reparse_is_honest(result: dict) -> None:
    reparse = result["lossless"]["reparse"]
    if reparse["checked"]:
        assert reparse["ok"] is True
    else:
        assert reparse["ok"] is None
        assert reparse["reason"]


# --------------------------------------------------------------------------- #
# graph + addressing
# --------------------------------------------------------------------------- #
def test_synthetic_cst_round_trips_with_comments_and_whitespace() -> None:
    graph = cst_graph_from_nested(_rust_tree())
    assert graph.render() == RUST_SOURCE
    assert graph.flat_text(graph.root) == RUST_SOURCE
    assert graph.ranges()[graph.root] == (0, len(RUST_SOURCE))
    kinds = {record["kind"] for record in graph.leaf_records()}
    assert {"line_comment", "whitespace", "identifier",
            "integer_literal"} <= kinds
    assert graph.node_count > graph.leaf_count
    assert parse_cst_path("") == []
    assert parse_cst_path("root") == []
    assert parse_cst_path("child[0].child[4]") == [0, 4]
    assert parse_cst_path("children[2].[1]") == [2, 1]


def test_serialized_cst_graph_is_accepted(tmp_path: Path) -> None:
    source = "fn main() {}\n"
    serialized = {
        "root": 0,
        "nodes": [
            {"id": 0, "attrs": {"kind": "source_file", "text": source,
                                "child_index": -1}},
        ],
    }
    graph = CstGraph.from_dict(serialized)
    assert graph.render() == source
    path = tmp_path / "lib.rs"
    path.write_bytes(source.encode("utf-8"))
    result = apply_cst_edit_script(tmp_path, {
        "file": "lib.rs",
        "cst_graph": serialized,
        "ops": [{"op": "replace_span", "start": 3, "end": 7,
                 "text": "other"}],
    }, write=True)
    assert result["applied"] is True
    assert path.read_bytes() == b"fn other() {}\n"


def test_live_substrate_cst_graph_is_accepted(tmp_path: Path) -> None:
    srs = pytest.importorskip("substrate_rs")
    source = "fn main() {}\n"
    substrate = srs.Substrate()
    root = substrate.add_node("CstNode", {
        "kind": "source_file", "field": "", "child_index": -1,
        "named": True, "origin": "test",
    })
    inner = getattr(substrate, "_inner", substrate)
    leaves = [
        ("keyword", "fn "), ("identifier", "main"), ("parameters", "()"),
        ("whitespace", " "), ("punctuation", "{"), ("punctuation", "}"),
        ("whitespace", "\n"),
    ]
    for index, (kind, text) in enumerate(leaves):
        child = substrate.add_node("CstNode", {
            "kind": kind, "text": text, "field": "", "child_index": index,
            "named": True, "origin": "test",
        })
        inner.add_edge_unchecked(root, "child", child)

    path = tmp_path / "lib.rs"
    path.write_bytes(source.encode("utf-8"))
    result = apply_cst_edit_script(tmp_path, {
        "file": "lib.rs",
        "cst_graph": {"substrate": substrate, "root": root},
        "ops": [{"op": "replace_node", "path": "child[1]", "text": "other"}],
    }, write=True)
    assert result["applied"] is True
    assert result["lossless"]["cst_backend"] == "substrate"
    assert path.read_bytes() == b"fn other() {}\n"


def test_crlf_bytes_survive_an_edit(tmp_path: Path) -> None:
    graph = cst_graph_from_nested({
        "kind": "source_file",
        "children": [
            _leaf("keyword", "return "),
            _leaf("integer", "1"),
            _leaf("whitespace", "\r\n"),
        ],
    })
    path = tmp_path / "lib.lua"
    path.write_bytes(graph.render().encode("utf-8"))
    result = _apply(tmp_path, graph, [
        {"op": "replace_node", "path": "child[1]", "text": "2"},
    ], file="lib.lua", write=True)
    assert result["applied"] is True
    assert path.read_bytes() == b"return 2\r\n"


def test_cst_that_does_not_round_trip_is_refused(tmp_path: Path) -> None:
    graph = cst_graph_from_nested(_rust_tree())
    path = tmp_path / "lib.rs"
    path.write_text(RUST_SOURCE.replace("main", "other"), encoding="utf-8")
    with pytest.raises(CodeEditError, match="does not round-trip"):
        _apply(tmp_path, graph, [
            {"op": "replace_node", "path": INT_X, "text": "7"},
        ])


# --------------------------------------------------------------------------- #
# node ops
# --------------------------------------------------------------------------- #
def test_replace_node_keeps_everything_else(tmp_path: Path) -> None:
    path = _fixture(tmp_path)
    graph = cst_graph_from_nested(_rust_tree())
    before = path.read_text(encoding="utf-8")
    expected = before.replace("= 1;", "= 41;", 1)

    result = _apply(tmp_path, graph, [
        {"op": "replace_node", "path": INT_X, "text": "41"},
    ], write=True)

    assert result["ok"] is True
    assert result["applied"] is True
    assert result["format"] == "rust"
    assert path.read_text(encoding="utf-8") == expected
    assert "// keep café before" in path.read_text(encoding="utf-8")
    assert "// keep after" in path.read_text(encoding="utf-8")
    assert result["changes"][0]["path"] == INT_X
    assert result["changes"][0]["node_kind"] == "integer_literal"
    assert result["lossless"]["roundtrip"] is True
    assert result["lossless"]["cst_backend"] == "synthetic"
    assert result["lossless"]["nodes"] == graph.node_count
    assert result["lossless"]["leaves"] == graph.leaf_count
    _reparse_is_honest(result)


def test_multiple_disjoint_edits_apply_bottom_up(tmp_path: Path) -> None:
    path = _fixture(tmp_path)
    graph = cst_graph_from_nested(_rust_tree())
    result = _apply(tmp_path, graph, [
        {"op": "replace_node", "path": INT_X, "text": "5"},
        {"op": "replace_node", "path": INT_Y, "text": "6"},
    ], write=True)
    assert result["applied"] is True
    assert path.read_text(encoding="utf-8") == RUST_SOURCE.replace(
        "let x = 1;", "let x = 5;").replace("let y = 2;", "let y = 6;")
    assert [change["path"] for change in result["changes"]] == [INT_X, INT_Y]


def test_insert_before_and_after_node(tmp_path: Path) -> None:
    path = _fixture(tmp_path)
    graph = cst_graph_from_nested(_rust_tree())

    before = _apply(tmp_path, graph, [
        {"op": "insert_before_node", "path": LET_X,
         "text": "let z = 0;\n    "},
    ], write=True)
    assert before["applied"] is True
    assert path.read_text(encoding="utf-8") == RUST_SOURCE.replace(
        "    let x = 1;", "    let z = 0;\n    let x = 1;", 1)

    # Reset to the graph's base source, then insert after the same node.
    path.write_text(RUST_SOURCE, encoding="utf-8")
    graph = cst_graph_from_nested(_rust_tree())
    after = _apply(tmp_path, graph, [
        {"op": "insert_after_node", "path": LET_X,
         "text": "\n    let w = 3;"},
    ], write=True)
    assert after["applied"] is True
    text = path.read_text(encoding="utf-8")
    assert "let x = 1;\n    let w = 3;\n\n    let y = 2;" in text


def test_delete_node_removes_the_line_and_one_blank_line(tmp_path: Path) -> None:
    path = _fixture(tmp_path)
    graph = cst_graph_from_nested(_rust_tree())
    result = _apply(tmp_path, graph, [
        {"op": "delete_node", "path": LET_X},
    ], write=True)
    expected = (
        "fn main() {\n"
        "    // keep café before\n"
        "    let y = 2;\n"
        "    // keep after\n"
        "}\n"
    )
    assert result["applied"] is True
    assert path.read_text(encoding="utf-8") == expected
    assert "// keep café before" in path.read_text(encoding="utf-8")
    assert "whole line" in result["changes"][0]["summary"]


def test_delete_adjacent_statements_in_one_script(tmp_path: Path) -> None:
    path = _fixture(tmp_path)
    graph = cst_graph_from_nested(_rust_tree())
    result = _apply(tmp_path, graph, [
        {"op": "delete_node", "path": LET_X},
        {"op": "delete_node", "path": LET_Y},
    ], write=True)
    expected = (
        "fn main() {\n"
        "    // keep café before\n"
        "    // keep after\n"
        "}\n"
    )
    assert result["applied"] is True
    assert path.read_text(encoding="utf-8") == expected


def test_wrap_node_is_raw_text(tmp_path: Path) -> None:
    path = _fixture(tmp_path)
    graph = cst_graph_from_nested(_rust_tree())
    result = _apply(tmp_path, graph, [
        {"op": "wrap_node", "path": INT_X, "prefix": "(", "suffix": ")"},
    ], write=True)
    assert result["applied"] is True
    assert path.read_text(encoding="utf-8") == RUST_SOURCE.replace(
        "= 1;", "= (1);", 1)


def test_replace_span_char_offsets(tmp_path: Path) -> None:
    path = _fixture(tmp_path)
    graph = cst_graph_from_nested(_rust_tree())
    start = RUST_SOURCE.index("= 1;") + 2
    result = _apply(tmp_path, graph, [
        {"op": "replace_span", "start": start, "end": start + 1, "text": "7"},
    ], write=True)
    assert result["applied"] is True
    assert path.read_text(encoding="utf-8") == RUST_SOURCE.replace(
        "= 1;", "= 7;", 1)


def test_replace_span_byte_offsets_with_unicode(tmp_path: Path) -> None:
    path = _fixture(tmp_path)
    graph = cst_graph_from_nested(_rust_tree())
    char_start = RUST_SOURCE.index("= 1;") + 2
    byte_start = len(RUST_SOURCE[:char_start].encode("utf-8"))
    byte_end = byte_start + len("1".encode("utf-8"))
    assert byte_start != char_start  # the café comment shifted the bytes
    result = _apply(tmp_path, graph, [
        {"op": "replace_span", "start_byte": byte_start,
         "end_byte": byte_end, "text": "8"},
    ], write=True)
    assert result["applied"] is True
    assert path.read_text(encoding="utf-8") == RUST_SOURCE.replace(
        "= 1;", "= 8;", 1)


def test_lua_format_and_paths(tmp_path: Path) -> None:
    path = _fixture(tmp_path, "lib.lua")
    graph = cst_graph_from_nested(_lua_tree())
    result = _apply(tmp_path, graph, [
        {"op": "replace_node", "path": LUA_INT_X, "text": "2"},
    ], file="lib.lua", write=True)
    assert result["format"] == "lua"
    assert result["applied"] is True
    assert path.read_text(encoding="utf-8") == LUA_SOURCE.replace(
        "local x = 1", "local x = 2", 1)
    assert "-- keep lua" in path.read_text(encoding="utf-8")
    _reparse_is_honest(result)


# --------------------------------------------------------------------------- #
# transactional contract
# --------------------------------------------------------------------------- #
def test_preview_is_not_apply(tmp_path: Path) -> None:
    path = _fixture(tmp_path)
    graph = cst_graph_from_nested(_rust_tree())
    before = path.read_text(encoding="utf-8")
    expected = before.replace("= 1;", "= 9;", 1)
    result = _apply(tmp_path, graph, [
        {"op": "replace_node", "path": INT_X, "text": "9"},
    ])
    assert result["ok"] is True
    assert result["applied"] is False
    assert result["graph_stale"] is False
    assert result["backup"] is None
    assert path.read_text(encoding="utf-8") == before
    assert result["before"]["sha256"] == sha256_text(before)
    assert result["after"]["sha256"] == sha256_text(expected)
    assert result["new_sha256"] == sha256_text(expected)
    assert result["diff_note"].startswith(
        "a unified diff is a rendered view")
    assert "+    let x = 9;" in result["diff_view"]
    # Outside-target text is not touched by the rendered diff.
    assert not any(line.startswith(("-", "+"))
                   and "keep café before" in line
                   for line in result["diff_view"].splitlines())


def test_apply_backs_up_and_stale_base_is_refused(tmp_path: Path) -> None:
    path = _fixture(tmp_path)
    graph = cst_graph_from_nested(_rust_tree())
    before = path.read_text(encoding="utf-8")
    base = sha256_text(before)

    result = _apply(tmp_path, graph, [
        {"op": "replace_node", "path": INT_X, "text": "3"},
    ], base_sha256=base, write=True)
    assert result["applied"] is True
    assert result["graph_stale"] is True
    assert result["before"]["sha256"] == base
    assert result["after"]["sha256"] == sha256_text(path.read_text(
        encoding="utf-8"))
    backup = Path(result["backup"])
    assert backup.is_file()
    assert backup.read_text(encoding="utf-8") == before
    assert backup.parent == (tmp_path / "var" / "ocelot_dev_edits"
                             / "backups").resolve()

    with pytest.raises(CodeEditError, match="stale base"):
        _apply(tmp_path, graph, [
            {"op": "replace_node", "path": INT_X, "text": "4"},
        ], base_sha256=base)


def test_raw_diff_is_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    with pytest.raises(CodeEditError, match="raw 'diff'"):
        apply_cst_edit_script(tmp_path, {
            "file": "lib.rs",
            "diff": "--- a/lib.rs\n+++ b/lib.rs\n",
            "ops": [],
        })


def test_path_escape_and_non_source_files_are_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    graph = cst_graph_from_nested(_rust_tree())
    with pytest.raises(CodeEditError, match="escapes"):
        apply_cst_edit_script(tmp_path, {
            "file": "../outside.rs",
            "cst_graph": graph,
            "ops": [{"op": "replace_node", "path": INT_X, "text": "1"}],
        })
    with pytest.raises(CodeEditError, match="only edits .rs/.lua"):
        apply_cst_edit_script(tmp_path, {
            "file": "mod.py",
            "cst_graph": graph,
            "ops": [{"op": "replace_node", "path": INT_X, "text": "1"}],
        })


def test_bad_and_overlapping_paths_are_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    graph = cst_graph_from_nested(_rust_tree())
    with pytest.raises(CodeEditError, match="bad CST path"):
        _apply(tmp_path, graph, [
            {"op": "replace_node", "path": "body[0]", "text": "x"},
        ])
    with pytest.raises(CodeEditError, match="no CST node at path"):
        _apply(tmp_path, graph, [
            {"op": "replace_node", "path": "child[9]", "text": "x"},
        ])
    with pytest.raises(CodeEditError, match="overlapping CST edits"):
        _apply(tmp_path, graph, [
            {"op": "replace_node", "path": INT_X, "text": "2"},
            {"op": "replace_node", "path": LET_X, "text": "let x = 3;"},
        ])
    with pytest.raises(CodeEditError, match="root is refused"):
        _apply(tmp_path, graph, [
            {"op": "delete_node", "path": ""},
        ])
    with pytest.raises(CodeEditError, match="unknown CST op"):
        _apply(tmp_path, graph, [
            {"op": "rename_symbol", "path": INT_X, "text": "x"},
        ])
    with pytest.raises(CodeEditError, match="empty text is refused"):
        _apply(tmp_path, graph, [
            {"op": "replace_node", "path": INT_X, "text": ""},
        ])


def test_missing_tree_sitter_requires_a_synthetic_graph(
        tmp_path: Path) -> None:
    if tree_sitter_available("rust"):
        pytest.skip("tree-sitter is available; the parser path can be used")
    path = _fixture(tmp_path)
    assert path.is_file()
    with pytest.raises(CodeEditError, match="tree_sitter backend unavailable"):
        apply_cst_edit_script(tmp_path, {
            "file": "lib.rs",
            "ops": [{"op": "replace_span", "start": 0, "end": 0, "text": ""}],
        })


@pytest.mark.skipif(not tree_sitter_available("rust"),
                    reason="tree-sitter rust grammar is not installed")
def test_tree_sitter_backend_when_available(tmp_path: Path) -> None:
    source = "fn main() {\n    let x = 1;\n}\n"
    path = tmp_path / "lib.rs"
    path.write_text(source, encoding="utf-8")
    start = source.index("1")
    result = apply_cst_edit_script(tmp_path, {
        "file": "lib.rs",
        "ops": [{"op": "replace_span", "start": start, "end": start + 1,
                 "text": "2"}],
    })
    assert result["lossless"]["cst_backend"] == "tree_sitter"
    assert result["lossless"]["reparse"]["checked"] is True
    assert result["lossless"]["reparse"]["ok"] is True
    assert "+    let x = 2;" in result["diff_view"]
