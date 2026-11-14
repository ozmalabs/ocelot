"""ocelot_edit — the format-dispatching graph edit entry point.

One edit-script contract, multiple format adapters:

    .py                 -> scripts.ocelot_code_edit (AST/symbol ops); IR ops
                           or engine="ir" -> scripts.ocelot_ir_edit
    .md / .markdown     -> scripts.ocelot_markdown_edit (section ops)
    .json               -> scripts.ocelot_json_edit (span-preserving path ops)
    .yaml / .yml / ...  -> refused in v0 (no silent text-patch fallback)
    .rs / .lua         -> scripts.ocelot_cst_edit (CstNode subtree/leaf ops;
                           tree-sitter backend or a supplied synthetic graph)

The adapters share the transaction contract: preview by default, optional
`base_sha256` staleness check, parse/structural validation, atomic write,
backup under `var/ocelot_dev_edits/backups/`, and a `diff_view` that is only a
rendering. Raw diff/patch input is refused everywhere.

The point is that adding a format means adding a parser + renderer for that
format's block graph, not adding a new text-patch convention. The eventual
Rust/hub-IR adapter is the same interface with the graph renderer on the other
side.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.ocelot_code_edit import CodeEditError
from scripts.ocelot_code_edit import apply_edit_script as apply_python_edit
from scripts.ocelot_cst_edit import apply_cst_edit_script
from scripts.ocelot_ir_edit import SUPPORTED_OPS as IR_OPS
from scripts.ocelot_ir_edit import apply_ir_edit_script
from scripts.ocelot_json_edit import apply_json_edit_script
from scripts.ocelot_markdown_edit import apply_markdown_edit_script

__all__ = ["CodeEditError", "apply_edit_script", "adapter_for"]


def adapter_for(file: str) -> str:
    suffix = Path(str(file or "")).suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in (".md", ".markdown"):
        return "markdown"
    if suffix == ".json":
        return "json"
    if suffix in (".yaml", ".yml"):
        return "yaml-refused"
    if suffix == ".rs":
        return "rust"
    if suffix == ".lua":
        return "lua"
    if suffix in (".toml", ".cfg", ".ini"):
        return "source-refused"
    return "unknown"


def apply_edit_script(root: str | Path, script: dict[str, Any], *,
                      write: bool = False) -> dict[str, Any]:
    if not isinstance(script, dict):
        raise CodeEditError("edit script must be an object")
    file = str(script.get("file") or "").strip()
    if not file:
        raise CodeEditError("edit script needs file")
    kind = adapter_for(file)
    if kind == "python":
        ops = script.get("ops") or []
        # IR intent is explicit (`engine: "ir"`) or implied by an IR op name.
        # `fallback_check` also routes here; it is read-only by construction.
        ir_intent = (str(script.get("engine") or "").lower() == "ir"
                     or any(isinstance(op, dict)
                            and op.get("op") in IR_OPS for op in ops))
        if ir_intent:
            return apply_ir_edit_script(root, script, write=write)
        return apply_python_edit(root, script, write=write)
    if kind == "markdown":
        return apply_markdown_edit_script(root, script, write=write)
    if kind == "json":
        return apply_json_edit_script(root, script, write=write)
    if kind in ("rust", "lua"):
        return apply_cst_edit_script(root, script, write=write)
    if kind in ("yaml-refused", "source-refused"):
        raise CodeEditError(
            f"no graph edit adapter for {Path(file).suffix!r} yet; supported "
            f"in v0: .py (symbol/AST/IR ops), .md/.markdown (section ops), "
            f".json (path ops), and .rs/.lua (CST ops). "
            f"Refusing rather than falling back to a text patch.")
    raise CodeEditError(f"unsupported file type: {file}")
