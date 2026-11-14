"""ocelot_scip_import — ingest SCIP indexes into symbol/reference records.

Primary supported path: the JSON emitted by the Sourcegraph SCIP CLI::

    scip print --json index.scip > index.scip.json

The accepted shape is an index with ``documents``; each document has a
``relative_path``, ``occurrences`` and (optionally) ``symbols``. Occurrences
carry ``symbol``, ``symbol_roles`` and ``range``. Both the snake_case spellings
shown here and the protobuf-JSON lowerCamelCase spellings (``relativePath``,
``symbolRoles``, ``displayName``) are normalized.

A ``.scip`` protobuf index is accepted *only* when the Sourcegraph
``scip_pb2`` bindings and ``protobuf`` are importable. When they are not, this
module refuses honestly: it never guesses at the protobuf wire format.

The normalized records are file-level and symbol-level:

* definitions/references keep the SCIP symbol string and a human-readable
  name parsed from its descriptors;
* ranges stay 0-based exactly as SCIP defines them; ``line`` is the
  1-based editor line for repo-map compatibility;
* duplicate occurrences are merged, role masks are OR-ed;
* references convert to repo-map-compatible edges ``{src, tgt, weight}``
  where ``src`` references a symbol defined in ``tgt``.

DEV TOOLING, NOT AGENT RUNTIME. This module only reads indexes and returns
plain JSON-safe dictionaries. It never edits source and never prints.

The central integrator wires the public functions into the dev-memory MCP
surface (``dev_scip``) and the CLI; this file does not touch shared files.
"""
from __future__ import annotations

import gzip
import importlib
import json
import posixpath
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import unquote, urlsplit

__all__ = [
    "SCIPProtobufUnavailable",
    "ScipFormatError",
    "ScipImportError",
    "ScipProtobufUnavailable",
    "ScipProtobufUnavailableError",
    "load_scip",
    "load_scip_json",
    "load_scip_protobuf",
    "normalize_path",
    "parse_scip_symbol",
    "role_mask_names",
    "scip_dumps",
    "scip_file_summary",
    "scip_graph_records",
    "scip_import",
    "scip_protobuf_status",
    "scip_records",
    "scip_summary",
    "scip_symbol_name",
    "scip_to_graph_records",
    "scip_to_repo_map_edges",
]


class ScipImportError(Exception):
    """Base class for SCIP ingestion errors."""


class ScipFormatError(ScipImportError, ValueError):
    """The input is not a usable SCIP JSON/protobuf index."""


class ScipProtobufUnavailableError(ScipImportError, RuntimeError):
    """The optional protobuf/scip_pb2 path is unavailable."""


# Compatibility aliases: callers should not have to guess capitalisation.
SCIPProtobufUnavailable = ScipProtobufUnavailableError
ScipProtobufUnavailable = ScipProtobufUnavailableError


# SCIP SymbolRole bit mask (scip.proto).
DEFINITION_ROLE = 1
IMPORT_ROLE = 2
WRITE_ACCESS_ROLE = 4
READ_ACCESS_ROLE = 8
GENERATED_ROLE = 16
TEST_ROLE = 32
FORWARD_DEFINITION_ROLE = 64

_ROLE_ORDER: tuple[tuple[int, str], ...] = (
    (DEFINITION_ROLE, "definition"),
    (IMPORT_ROLE, "import"),
    (WRITE_ACCESS_ROLE, "write_access"),
    (READ_ACCESS_ROLE, "read_access"),
    (GENERATED_ROLE, "generated"),
    (TEST_ROLE, "test"),
    (FORWARD_DEFINITION_ROLE, "forward_definition"),
)
_ROLE_BY_NAME = {
    re.sub(r"[^a-z0-9]", "", name): mask for mask, name in _ROLE_ORDER
}
_ROLE_BY_NAME.update({
    "def": DEFINITION_ROLE,
    "read": READ_ACCESS_ROLE,
    "write": WRITE_ACCESS_ROLE,
    "forward": FORWARD_DEFINITION_ROLE,
})
_REFERENCE_ROLE_MASK = IMPORT_ROLE | WRITE_ACCESS_ROLE | READ_ACCESS_ROLE

# Proto `SymbolInformation.Kind` values. Used only to make JSON/protobuf
# integer kinds readable; an unknown value is preserved as a string.
_SYMBOL_KINDS = {
    0: "UnspecifiedKind", 1: "Array", 2: "Boolean", 3: "Class",
    4: "Constant", 5: "Constructor", 6: "DataFamily", 7: "Enum",
    8: "EnumMember", 9: "Event", 10: "Field", 11: "Function",
    12: "Getter", 13: "Grammar", 14: "Instance", 15: "Interface",
    16: "Key", 17: "Lang", 18: "Lemma", 19: "Library", 20: "Macro",
    21: "Method", 22: "Module", 23: "Namespace", 24: "Null",
    25: "Number", 26: "Object", 27: "Operator", 28: "Package",
    29: "Parameter", 30: "Property", 31: "Protocol", 32: "Self",
    33: "Setter", 34: "Struct", 35: "Style", 36: "Trait", 37: "Type",
    38: "TypeAlias", 39: "TypeClass", 40: "TypeFamily",
    41: "TypeParameter", 42: "Union", 43: "Value", 44: "Variable",
}

_PROTOBUF_HELP = (
    "SCIP protobuf ingestion is unavailable: protobuf/scip_pb2 is not "
    "installed. Install the Sourcegraph SCIP protobuf bindings (protobuf + "
    "scip_pb2) and retry, or export JSON with "
    "`scip print --json <index.scip>` and use load_scip_json()."
)

_PATH_KEYS = (
    "relative_path", "relativePath", "path", "file", "filename", "file_path",
    "filePath",
)
_DOC_CONTAINER_KEYS = ("documents", "docs")
_SYMBOL_KEYS = ("symbol", "symbol_string", "symbolString")
_ROLE_KEYS = ("symbol_roles", "symbolRoles", "roles", "role")
_RANGE_KEYS = ("range",)
_START_LINE_KEYS = (
    "start_line", "startLine", "start_line_number", "startLineNumber",
    "line",
)
_START_CHAR_KEYS = (
    "start_character", "startCharacter", "start_char", "startChar",
    "start_column", "startColumn", "character", "char", "column",
)
_END_LINE_KEYS = (
    "end_line", "endLine", "end_line_number", "endLineNumber",
)
_END_CHAR_KEYS = (
    "end_character", "endCharacter", "end_char", "endChar",
    "end_column", "endColumn",
)


# --------------------------------------------------------------------------- #
# small parsing helpers
# --------------------------------------------------------------------------- #
def _first(mapping: Mapping[str, Any], keys: Iterable[str],
           default: Any = None) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return default


def _as_int(value: Any, what: str) -> int:
    if isinstance(value, bool):
        raise ScipFormatError(f"{what} must be an integer, got a boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value.strip()):
        return int(value.strip())
    raise ScipFormatError(f"{what} must be an integer, got {value!r}")


def _uri_path(value: str) -> str:
    if value.startswith("file://"):
        parts = urlsplit(value)
        return unquote(parts.path)
    return value


def normalize_path(path: Any, *, root: str | Path | None = None) -> str:
    """Normalize a SCIP document path to a canonical repo-relative POSIX path.

    Backslashes become slashes, ``./`` and duplicate slashes are collapsed,
    ``..`` escapes are refused. An absolute path is accepted only when the
    repository ``root`` is supplied and contains it.
    """
    if path is None:
        raise ValueError("SCIP path is missing")
    text = _uri_path(str(path).strip())
    if not text:
        raise ValueError("SCIP path is empty")
    if "\x00" in text:
        raise ValueError("SCIP path contains a NUL byte")
    text = text.replace("\\", "/")
    root_path: Path | None = None
    root_text: str | None = None
    if root is not None:
        root_text = _uri_path(str(root).strip()).replace("\\", "/").rstrip("/")
        try:
            root_path = Path(root).resolve()
        except OSError:
            root_path = Path(root).absolute()
    if text.startswith("/") or re.match(r"^[A-Za-z]:/", text):
        if root_path is None or root_text is None:
            raise ValueError(
                f"absolute SCIP path requires a repo root: {text!r}")
        # Prefer a textual prefix match so Windows drive roots also work when
        # this code runs on Linux (Path.resolve cannot interpret "C:/...").
        prefix = root_text + "/"
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):]
        else:
            try:
                text = Path(text).resolve().relative_to(root_path).as_posix()
            except ValueError as exc:
                raise ValueError(
                    f"SCIP path escapes repo root {str(root_path)!r}: {text!r}"
                ) from exc
    normalized = posixpath.normpath(text)
    if normalized in ("", "."):
        raise ValueError("SCIP path normalizes to the repo root")
    if normalized == ".." or normalized.startswith("../"):
        raise ValueError(f"SCIP path escapes repo root: {text!r}")
    return normalized


def role_mask_names(mask: int) -> list[str]:
    """Human-readable names for a SCIP ``symbol_roles`` bit mask."""
    value = int(mask)
    return [name for bit, name in _ROLE_ORDER if value & bit]


def _normalize_role_key(name: Any) -> str:
    key = re.sub(r"[^a-z0-9]", "", str(name).strip().lower())
    for prefix in ("symbolrole", "symbolroles"):
        if key.startswith(prefix):
            key = key[len(prefix):]
    return key


def _role_mask(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, bool):
        raise ScipFormatError("symbol_roles must be a mask or role names")
    if isinstance(value, int):
        if value < 0:
            raise ScipFormatError("symbol_roles must be non-negative")
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0
        if re.fullmatch(r"[+-]?\d+", text):
            number = int(text)
            if number < 0:
                raise ScipFormatError("symbol_roles must be non-negative")
            return number
        mask = 0
        for part in re.split(r"[\s,|;+]+", text):
            key = _normalize_role_key(part)
            if not key:
                continue
            if key not in _ROLE_BY_NAME:
                raise ScipFormatError(f"unknown SCIP symbol role: {part!r}")
            mask |= _ROLE_BY_NAME[key]
        return mask
    if isinstance(value, (list, tuple, set)):
        mask = 0
        for item in value:
            mask |= _role_mask(item)
        return mask
    raise ScipFormatError(f"unsupported symbol_roles value: {value!r}")


def _symbol_kind_name(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, int) and not isinstance(value, bool):
        return _SYMBOL_KINDS.get(value, str(value))
    if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value.strip()):
        return _SYMBOL_KINDS.get(int(value.strip()), value.strip())
    return str(value).strip()


def _documentation(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item)]
    return [str(value)]


# --------------------------------------------------------------------------- #
# SCIP symbol-string parsing
# --------------------------------------------------------------------------- #
def _split_symbol_header(symbol: str) -> tuple[list[str], str]:
    """Split ``scheme manager package version descriptors``.

    SCIP escapes a literal space inside a header field with a double space.
    Desktop paths do not normally hit that, but handling it keeps the parser
    faithful to the symbol grammar in ``scip.proto``.
    """
    fields: list[str] = []
    buffer: list[str] = []
    index = 0
    while index < len(symbol) and len(fields) < 4:
        char = symbol[index]
        if char == " ":
            if index + 1 < len(symbol) and symbol[index + 1] == " ":
                buffer.append(" ")
                index += 2
                continue
            fields.append("".join(buffer))
            buffer = []
            index += 1
            continue
        buffer.append(char)
        index += 1
    if len(fields) < 4:
        return [], symbol
    return fields, symbol[index:]


def _split_descriptors(text: str) -> list[str]:
    """Split a descriptor list, respecting escaped identifiers in backticks."""
    parts: list[str] = []
    buffer: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "`":
            buffer.append(char)
            index += 1
            while index < len(text):
                if text[index] == "`":
                    if index + 1 < len(text) and text[index + 1] == "`":
                        buffer.append("``")
                        index += 2
                        continue
                    buffer.append("`")
                    index += 1
                    break
                buffer.append(text[index])
                index += 1
            continue
        if char == "(":
            # Method disambiguator or parameter descriptor; either way it
            # closes at the next ')'.
            buffer.append(char)
            index += 1
            while index < len(text) and text[index] != ")":
                buffer.append(text[index])
                index += 1
            if index < len(text):
                buffer.append(")")
                index += 1
            continue
        if char in "/#.!:":
            buffer.append(char)
            parts.append("".join(buffer))
            buffer = []
            index += 1
            continue
        buffer.append(char)
        index += 1
    if buffer:
        parts.append("".join(buffer))
    return parts


def _unescape_identifier(value: str) -> str:
    text = value
    if text.startswith("`") and text.endswith("`") and len(text) >= 2:
        text = text[1:-1].replace("``", "`")
    return text


def _descriptor(raw: str) -> dict[str, str]:
    text = raw
    kind = "unknown"
    if text.endswith(")."):
        kind = "method"
        text = text[:text.rfind("(")]
    elif text.startswith("(") and text.endswith(")"):
        kind = "parameter"
        text = text[1:-1]
    elif text.startswith("[") and text.endswith("]"):
        kind = "type_parameter"
        text = text[1:-1]
    elif text.endswith("/"):
        kind = "namespace"
        text = text[:-1]
    elif text.endswith("#"):
        kind = "type"
        text = text[:-1]
    elif text.endswith("."):
        kind = "term"
        text = text[:-1]
    elif text.endswith("!"):
        kind = "macro"
        text = text[:-1]
    elif text.endswith(":"):
        kind = "meta"
        text = text[:-1]
    elif text.endswith(")"):
        # A method descriptor whose trailing '.' is absent in malformed
        # exports, or a parameter with a suffix we did not recognise.
        kind = "method" if "(" in text else "unknown"
        text = text[:text.rfind("(")] if "(" in text else text
    return {"name": _unescape_identifier(text), "kind": kind, "raw": raw}


def parse_scip_symbol(symbol: Any) -> dict[str, Any]:
    """Parse a SCIP symbol string into header fields and descriptors.

    The interesting field is ``name``: the last descriptor's human-readable
    identifier (for example ``scip-python python pkg 0.1.0 `a.py`/f().`` has
    name ``f``). ``qualname`` joins the descriptor names. Local symbols
    (``local 0``) are marked ``local=True`` and never become file edges.
    """
    text = str(symbol or "").strip()
    result: dict[str, Any] = {
        "symbol": text,
        "local": False,
        "scheme": "",
        "package_manager": "",
        "package_name": "",
        "package_version": "",
        "descriptors": [],
        "name": "",
        "qualname": "",
    }
    if not text:
        return result
    if text == "local" or text.startswith("local "):
        local_id = text[6:].strip()
        result.update({
            "local": True,
            "name": local_id or "local",
            "qualname": local_id or "local",
        })
        return result
    fields, remainder = _split_symbol_header(text)
    descriptor_text = remainder
    if len(fields) == 4:
        scheme, manager, package, version = fields
        result.update({
            "scheme": _unescape_identifier(scheme),
            "package_manager": "" if manager == "." else manager,
            "package_name": "" if package == "." else package,
            "package_version": "" if version == "." else version,
        })
    else:
        descriptor_text = text
    raw_descriptors = _split_descriptors(descriptor_text)
    descriptors = [_descriptor(raw) for raw in raw_descriptors]
    descriptors = [item for item in descriptors if item["name"] or item["raw"]]
    result["descriptors"] = descriptors
    names = [item["name"] for item in descriptors if item["name"]]
    result["name"] = names[-1] if names else ""
    result["qualname"] = ".".join(names)
    return result


def scip_symbol_name(symbol: Any) -> str:
    """The human-readable last-component name of a SCIP symbol."""
    return parse_scip_symbol(symbol)["name"]


# --------------------------------------------------------------------------- #
# range / occurrence / document normalization
# --------------------------------------------------------------------------- #
def _endpoint(mapping: Mapping[str, Any], *, end: bool,
              context: str) -> tuple[int, int]:
    line_keys = _END_LINE_KEYS if end else _START_LINE_KEYS
    char_keys = _END_CHAR_KEYS if end else _START_CHAR_KEYS
    if end:
        # Inside {"start": {...}, "end": {...}} the endpoint object uses the
        # unprefixed line/character keys.
        line_keys = (*line_keys, "line", "line_number", "lineNumber")
        char_keys = (*char_keys, "character", "char", "column")
    line_raw = _first(mapping, line_keys)
    char_raw = _first(mapping, char_keys, 0)
    if line_raw is None:
        raise ScipFormatError(f"{context}: range endpoint has no line")
    return (_as_int(line_raw, f"{context} line"),
            _as_int(char_raw, f"{context} character"))


def _coerce_range(values: Any, *, context: str) -> list[int]:
    if isinstance(values, str):
        raise ScipFormatError(f"{context}: range must be an array")
    try:
        raw = list(values)
    except TypeError as exc:
        raise ScipFormatError(f"{context}: range must be an array") from exc
    numbers = [_as_int(value, f"{context} range component") for value in raw]
    if len(numbers) == 3:
        line, start_char, end_char = numbers
        numbers = [line, start_char, line, end_char]
    if len(numbers) != 4:
        raise ScipFormatError(
            f"{context}: range must have 3 or 4 integers, got {len(numbers)}")
    start_line, start_char, end_line, end_char = numbers
    if min(numbers) < 0:
        raise ScipFormatError(f"{context}: range values must be non-negative")
    if (end_line, end_char) < (start_line, start_char):
        raise ScipFormatError(f"{context}: range end precedes start")
    return numbers


def _normalize_range(occurrence: Mapping[str, Any], *, context: str) -> list[int]:
    raw = _first(occurrence, _RANGE_KEYS)
    if isinstance(raw, Mapping):
        start = _first(raw, ("start", "start_position", "startPosition"))
        end = _first(raw, ("end", "end_position", "endPosition"))
        if isinstance(start, Mapping) or isinstance(end, Mapping):
            if not isinstance(start, Mapping) or not isinstance(end, Mapping):
                raise ScipFormatError(f"{context}: range needs both start and end")
            start_line, start_char = _endpoint(start, end=False, context=context)
            end_line, end_char = _endpoint(end, end=True, context=context)
            return _coerce_range([start_line, start_char, end_line, end_char],
                                 context=context)
        return _coerce_range([
            _first(raw, _START_LINE_KEYS),
            _first(raw, _START_CHAR_KEYS, 0),
            _first(raw, _END_LINE_KEYS),
            _first(raw, _END_CHAR_KEYS, 0),
        ], context=context)
    if raw is not None:
        return _coerce_range(raw, context=context)
    # Flat fields directly on the occurrence.
    start_line = _first(occurrence, _START_LINE_KEYS)
    if start_line is None:
        raise ScipFormatError(f"{context}: occurrence is missing range")
    start_char = _first(occurrence, _START_CHAR_KEYS, 0)
    end_line = _first(occurrence, _END_LINE_KEYS, start_line)
    end_char = _first(occurrence, _END_CHAR_KEYS, start_char)
    return _coerce_range([start_line, start_char, end_line, end_char],
                         context=context)


def _normalize_occurrence(occurrence: Any, *, context: str) -> dict[str, Any] | None:
    if not isinstance(occurrence, Mapping):
        raise ScipFormatError(f"{context}: occurrence must be an object")
    symbol = _first(occurrence, _SYMBOL_KEYS, "")
    symbol_text = str(symbol).strip()
    if not symbol_text:
        # SCIP permits occurrences without a symbol (e.g. syntax-only data);
        # they carry no reference information and are dropped.
        return None
    mask = _role_mask(_first(occurrence, _ROLE_KEYS))
    return {
        "symbol": symbol_text,
        "role_mask": mask,
        "roles": role_mask_names(mask),
        "range": _normalize_range(occurrence, context=context),
    }


def _normalize_symbol_info(item: Any, *, context: str) -> dict[str, Any] | None:
    if not isinstance(item, Mapping):
        raise ScipFormatError(f"{context}: symbol info must be an object")
    symbol = str(_first(item, _SYMBOL_KEYS, "")).strip()
    if not symbol:
        return None
    return {
        "symbol": symbol,
        "display_name": str(
            _first(item, ("display_name", "displayName"), "") or ""),
        "kind": _symbol_kind_name(_first(item, ("kind",))),
        "documentation": _documentation(
            _first(item, ("documentation", "docs"))),
        "enclosing_symbol": str(
            _first(item, ("enclosing_symbol", "enclosingSymbol"), "") or ""),
    }


def _symbol_list(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, Mapping):
        if any(key in raw for key in _SYMBOL_KEYS):
            return [raw]
        # A few exporters key symbol information by symbol string.
        out: list[Any] = []
        for key, value in raw.items():
            if isinstance(value, Mapping):
                item = dict(value)
                item.setdefault("symbol", key)
                out.append(item)
        return out
    if isinstance(raw, (list, tuple)):
        return list(raw)
    raise ScipFormatError("symbols must be an array or object")


def _symbol_info_map(raw: Any, *, context: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(_symbol_list(raw)):
        info = _normalize_symbol_info(item, context=f"{context} symbols[{index}]")
        if info is not None:
            result[info["symbol"]] = info
    return result


def _document_path(document: Mapping[str, Any]) -> str:
    raw = _first(document, _PATH_KEYS)
    if raw is None:
        raw = _first(document, ("uri",))
        if raw is not None:
            raw = _uri_path(str(raw))
    if raw is None:
        raise ScipFormatError(
            "document is missing relative_path/relativePath/path")
    return str(raw)


def _normalize_document(document: Any, *, root: str | Path | None,
                        context: str) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        raise ScipFormatError(f"{context}: document must be an object")
    try:
        path = normalize_path(_document_path(document), root=root)
    except ValueError as exc:
        raise ScipFormatError(f"{context}: {exc}") from exc
    occurrences_raw = document.get("occurrences") or []
    if isinstance(occurrences_raw, Mapping):
        occurrences_raw = list(occurrences_raw.values())
    if not isinstance(occurrences_raw, (list, tuple)):
        raise ScipFormatError(f"{context}: occurrences must be an array")
    occurrences: list[dict[str, Any]] = []
    for index, occurrence in enumerate(occurrences_raw):
        normalized = _normalize_occurrence(
            occurrence, context=f"{context} occurrence[{index}]")
        if normalized is not None:
            occurrences.append(normalized)
    occurrences.sort(key=lambda item: (
        item["range"], item["symbol"], item["role_mask"]))
    symbols_raw = _first(document, (
        "symbols", "symbol_information", "symbolInformation"))
    symbols = []
    for index, item in enumerate(_symbol_list(symbols_raw)):
        info = _normalize_symbol_info(
            item, context=f"{context} symbols[{index}]")
        if info is not None:
            symbols.append(info)
    symbols.sort(key=lambda item: item["symbol"])
    return {
        "path": path,
        "language": str(document.get("language") or ""),
        "position_encoding": str(
            _first(document, ("position_encoding", "positionEncoding")) or ""),
        "occurrences": occurrences,
        "symbols": symbols,
    }


def _project_root(metadata: Mapping[str, Any]) -> str | None:
    raw = _first(metadata, ("project_root", "projectRoot"))
    if not raw:
        return None
    return _uri_path(str(raw))


def _normalize_index(data: Any, *, fmt: str,
                     root: str | Path | None) -> dict[str, Any]:
    if isinstance(data, Mapping) and "index" in data \
            and isinstance(data["index"], Mapping) \
            and not any(key in data for key in _DOC_CONTAINER_KEYS):
        data = data["index"]
    metadata_raw = data.get("metadata") if isinstance(data, Mapping) else None
    metadata = dict(metadata_raw) if isinstance(metadata_raw, Mapping) else {}
    effective_root = root if root is not None else _project_root(metadata)

    if isinstance(data, Mapping):
        documents_raw = _first(data, _DOC_CONTAINER_KEYS)
        if documents_raw is None:
            if "occurrences" in data or any(key in data for key in _PATH_KEYS):
                documents_raw = [data]
            elif any(key in data for key in (
                    "external_symbols", "externalSymbols")):
                documents_raw = []
            else:
                raise ScipFormatError(
                    "SCIP JSON is missing a documents/docs array")
    elif isinstance(data, (list, tuple)):
        documents_raw = list(data)
    else:
        raise ScipFormatError(
            "SCIP JSON must be an object with documents or a document array")

    if isinstance(documents_raw, Mapping):
        expanded: list[Any] = []
        for key, value in documents_raw.items():
            if not isinstance(value, Mapping):
                raise ScipFormatError(
                    "documents object values must be document objects")
            item = dict(value)
            item.setdefault("relative_path", key)
            expanded.append(item)
        documents_raw = expanded
    if not isinstance(documents_raw, (list, tuple)):
        raise ScipFormatError("documents must be an array or object")

    documents = []
    for index, document in enumerate(documents_raw):
        documents.append(_normalize_document(
            document, root=effective_root, context=f"document[{index}]"))
    documents.sort(key=lambda item: (item["path"], item["language"]))

    external_raw = _first(data, ("external_symbols", "externalSymbols")) \
        if isinstance(data, Mapping) else None
    external = []
    for index, item in enumerate(_symbol_list(external_raw)):
        info = _normalize_symbol_info(
            item, context=f"external_symbols[{index}]")
        if info is not None:
            external.append(info)
    external.sort(key=lambda item: item["symbol"])
    return {
        "format": fmt,
        "metadata": metadata,
        "documents": documents,
        "external_symbols": external,
    }


# --------------------------------------------------------------------------- #
# loaders
# --------------------------------------------------------------------------- #
def load_scip_json(source: str | Path | Mapping[str, Any] | list[Any], *,
                   root: str | Path | None = None) -> dict[str, Any]:
    """Load and normalize a SCIP JSON export.

    ``source`` is a path to a JSON file, or an already-parsed mapping/list.
    Raises :class:`ScipFormatError` for unreadable JSON or invalid schema.
    """
    if isinstance(source, (Mapping, list, tuple)):
        data: Any = source
    else:
        path = Path(source)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ScipFormatError(f"cannot read SCIP JSON {str(path)!r}: {exc}") \
                from exc
        if text.startswith("\ufeff"):
            text = text[1:]
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ScipFormatError(
                f"invalid SCIP JSON in {str(path)!r}: "
                f"line {exc.lineno} column {exc.colno}: {exc.msg}") from exc
    return _normalize_index(data, fmt="scip-json", root=root)


def _import_scip_pb2() -> Any:
    failures = []
    for module_name in ("scip_pb2", "scip.scip_pb2"):
        try:
            return importlib.import_module(module_name)
        except Exception as exc:  # ImportError, or protobuf runtime missing
            failures.append(f"{module_name}: {exc}")
    detail = "; ".join(failures) if failures else "module not found"
    raise ScipProtobufUnavailableError(f"{_PROTOBUF_HELP} ({detail})")


def scip_protobuf_status() -> dict[str, Any]:
    """Honest availability report for the optional ``.scip`` protobuf path."""
    try:
        module = _import_scip_pb2()
    except ScipProtobufUnavailableError as exc:
        return {"available": False, "module": None, "error": str(exc)}
    return {"available": True, "module": getattr(module, "__name__", "scip_pb2"),
            "error": None}


def _proto_symbol_info(module: Any, item: Any) -> dict[str, Any]:
    kind = getattr(item, "kind", 0)
    try:
        kind_name = module.SymbolInformation.Kind.Name(int(kind))
    except Exception:
        kind_name = _symbol_kind_name(kind)
    return {
        "symbol": getattr(item, "symbol", ""),
        "display_name": getattr(item, "display_name", ""),
        "kind": kind_name,
        "documentation": list(getattr(item, "documentation", []) or []),
        "enclosing_symbol": getattr(item, "enclosing_symbol", ""),
    }


def load_scip_protobuf(path: str | Path, *,
                       root: str | Path | None = None) -> dict[str, Any]:
    """Load a ``.scip`` protobuf index when ``scip_pb2`` is importable.

    The refusal is intentional when the bindings are absent: this module does
    not implement a partial protobuf wire-format parser.
    """
    module = _import_scip_pb2()
    source = Path(path)
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise ScipFormatError(f"cannot read SCIP protobuf {str(source)!r}: {exc}") \
            from exc
    if raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except OSError as exc:
            raise ScipFormatError(
                f"invalid gzip-compressed SCIP index {str(source)!r}: {exc}") \
                from exc
    index = module.Index()
    try:
        index.ParseFromString(raw)
    except Exception as exc:
        raise ScipFormatError(
            f"invalid SCIP protobuf {str(source)!r}: {exc}") from exc

    documents = []
    for document in index.documents:
        occurrences = []
        for occurrence in document.occurrences:
            occurrences.append({
                "symbol": getattr(occurrence, "symbol", ""),
                "symbol_roles": int(getattr(occurrence, "symbol_roles", 0)),
                "range": [int(value) for value in occurrence.range],
            })
        documents.append({
            "relative_path": getattr(document, "relative_path", ""),
            "language": getattr(document, "language", ""),
            "occurrences": occurrences,
            "symbols": [_proto_symbol_info(module, item)
                        for item in document.symbols],
        })
    metadata = index.metadata
    tool = metadata.tool_info
    data = {
        "metadata": {
            "version": int(getattr(metadata, "version", 0)),
            "project_root": getattr(metadata, "project_root", ""),
            "text_document_encoding": int(
                getattr(metadata, "text_document_encoding", 0)),
            "tool_info": {
                "name": getattr(tool, "name", ""),
                "version": getattr(tool, "version", ""),
                "arguments": list(getattr(tool, "arguments", []) or []),
            },
        },
        "documents": documents,
        "external_symbols": [_proto_symbol_info(module, item)
                             for item in index.external_symbols],
    }
    return _normalize_index(data, fmt="scip-protobuf", root=root)


def load_scip(path: str | Path, *, root: str | Path | None = None,
              format_hint: str | None = None) -> dict[str, Any]:
    """Load either a SCIP JSON export or an optional ``.scip`` protobuf.

    ``.json``/``--json`` exports take the primary path. `.scip`/`.pb` inputs
    require the optional bindings and otherwise raise
    :class:`ScipProtobufUnavailableError`.
    """
    source = Path(path)
    hint = (format_hint or "").strip().lower()
    name = source.name.lower()
    if hint in ("json", "scip-json") or name.endswith(".json"):
        return load_scip_json(source, root=root)
    if hint in ("protobuf", "proto", "scip", "pb") or name.endswith(
            (".scip", ".scip.gz", ".pb", ".bin")):
        return load_scip_protobuf(source, root=root)
    try:
        head = source.read_bytes()[:64].lstrip()
    except OSError as exc:
        raise ScipFormatError(f"cannot read SCIP index {str(source)!r}: {exc}") \
            from exc
    if head[:1] in (b"{", b"["):
        return load_scip_json(source, root=root)
    return load_scip_protobuf(source, root=root)


# --------------------------------------------------------------------------- #
# records
# --------------------------------------------------------------------------- #
def _occurrence_kind(mask: int) -> str:
    # Definition wins for the rare occurrence carrying both a definition and
    # a read/write role; the role names still record the full mask.
    return "definition" if int(mask) & DEFINITION_ROLE else "reference"


def _make_record(path: str, symbol: str, mask: int, range_: list[int],
                 kind: str, info: Mapping[str, Any] | None) -> dict[str, Any]:
    parsed = parse_scip_symbol(symbol)
    display = str((info or {}).get("display_name") or "")
    name = display or parsed["name"] or symbol
    return {
        "path": path,
        "symbol": symbol,
        "name": name,
        "qualname": parsed["qualname"],
        "kind": kind,
        "symbol_kind": str((info or {}).get("kind") or ""),
        "roles": role_mask_names(mask),
        "role_mask": int(mask),
        "range": list(range_),
        "line": int(range_[0]) + 1,
        "character": int(range_[1]),
        "end_line": int(range_[2]) + 1,
        "end_character": int(range_[3]),
        "local": bool(parsed["local"]),
    }


def _doc_records(document: Any, *, root: str | Path | None,
                 context: str = "document") -> tuple[
                     list[dict[str, Any]], list[dict[str, Any]],
                     dict[str, Any], dict[str, dict[str, Any]]]:
    if not isinstance(document, Mapping):
        raise ScipFormatError(f"{context}: document must be an object")
    occurrences_raw = document.get("occurrences")
    already_normalized = (
        "path" in document
        and isinstance(occurrences_raw, (list, tuple))
        and all(isinstance(item, Mapping) and "role_mask" in item
                and isinstance(item.get("range"), (list, tuple))
                for item in occurrences_raw)
    )
    if already_normalized:
        try:
            path = normalize_path(document["path"], root=root)
        except ValueError as exc:
            raise ScipFormatError(f"{context}: {exc}") from exc
        normalized = {
            "path": path,
            "language": str(document.get("language") or ""),
            "occurrences": list(occurrences_raw),
            "symbols": document.get("symbols") or [],
        }
    elif "occurrences" in document or any(
            key in document for key in _PATH_KEYS):
        normalized = _normalize_document(document, root=root, context=context)
    else:
        raise ScipFormatError(f"{context}: not a SCIP document")
    path = str(normalized["path"])
    info = _symbol_info_map(normalized.get("symbols") or [],
                            context=f"{context} {path}")
    occurrences = normalized.get("occurrences") or []
    merged: dict[tuple[str, tuple[int, ...], str], dict[str, Any]] = {}
    for index, occurrence in enumerate(occurrences):
        if not isinstance(occurrence, Mapping):
            raise ScipFormatError(
                f"{context} {path} occurrence[{index}]: not an object")
        if "role_mask" in occurrence and isinstance(
                occurrence.get("range"), (list, tuple)):
            symbol = str(occurrence.get("symbol") or "").strip()
            if not symbol:
                continue
            mask = _as_int(occurrence.get("role_mask", 0),
                           "occurrence role_mask")
            range_ = _coerce_range(occurrence.get("range"),
                                   context=f"{context} {path} occurrence[{index}]")
        else:
            item = _normalize_occurrence(
                occurrence, context=f"{context} {path} occurrence[{index}]")
            if item is None:
                continue
            symbol = item["symbol"]
            mask = item["role_mask"]
            range_ = item["range"]
        kind = _occurrence_kind(mask)
        key = (symbol, tuple(range_), kind)
        if key in merged:
            merged[key]["role_mask"] |= mask
        else:
            merged[key] = {"symbol": symbol, "range": range_,
                           "role_mask": mask}
    definitions: list[dict[str, Any]] = []
    references: list[dict[str, Any]] = []
    for key in sorted(merged):
        item = merged[key]
        kind = key[2]
        record = _make_record(path, item["symbol"], item["role_mask"],
                              item["range"], kind, info.get(item["symbol"]))
        (definitions if kind == "definition" else references).append(record)
    definitions.sort(key=_record_sort_key)
    references.sort(key=_record_sort_key)
    return definitions, references, {
        "path": path,
        "language": str(normalized.get("language") or ""),
    }, info


def _record_sort_key(record: Mapping[str, Any]) -> tuple[Any, ...]:
    range_ = record.get("range") or [0, 0, 0, 0]
    return (str(record.get("path") or ""), *range_,
            str(record.get("symbol") or ""))


def _is_record_like(item: Any) -> bool:
    if not isinstance(item, Mapping):
        return False
    has_path = any(key in item for key in ("path", "file", "relative_path",
                                           "relativePath"))
    has_kind = "kind" in item or "role_mask" in item or "roles" in item
    return bool(item.get("symbol")) and has_path and has_kind


def _record_range(item: Mapping[str, Any], *, context: str) -> list[int]:
    raw = item.get("range")
    if raw is not None:
        return _coerce_range(raw, context=context)
    line = _first(item, ("line",))
    if line is not None:
        line_number = _as_int(line, f"{context} line")
        if line_number > 0:
            line_number -= 1
        char = _as_int(_first(item, ("character", "char"), 0),
                       f"{context} character")
        return _coerce_range([line_number, char, line_number, char],
                             context=context)
    return [0, 0, 0, 0]


def _coerce_record(item: Any, *, default_kind: str,
                   root: str | Path | None) -> dict[str, Any] | None:
    if not isinstance(item, Mapping):
        raise ScipFormatError("record must be an object")
    symbol = str(item.get("symbol") or "").strip()
    if not symbol:
        return None
    raw_path = _first(item, ("path", "file", "relative_path", "relativePath"))
    if raw_path is None:
        raise ScipFormatError("record is missing a file path")
    try:
        path = normalize_path(raw_path, root=root)
    except ValueError as exc:
        raise ScipFormatError(f"record path: {exc}") from exc
    mask_raw = item.get("role_mask")
    if mask_raw is None:
        mask = _role_mask(item.get("roles") or item.get("symbol_roles")
                          or item.get("symbolRoles"))
    else:
        mask = _as_int(mask_raw, "record role_mask")
    kind_raw = item.get("kind")
    if kind_raw is None:
        kind = _occurrence_kind(mask) if mask else default_kind
    else:
        kind = str(kind_raw).strip().lower()
        kind = {"def": "definition", "definition": "definition",
                "ref": "reference", "reference": "reference"}.get(kind, kind)
    if kind not in ("definition", "reference"):
        kind = _occurrence_kind(mask)
    range_ = _record_range(item, context=f"record {path} {symbol}")
    parsed = parse_scip_symbol(symbol)
    name = str(item.get("name") or "") or parsed["name"] or symbol
    return {
        "path": path,
        "symbol": symbol,
        "name": name,
        "qualname": str(item.get("qualname") or parsed["qualname"]),
        "kind": kind,
        "symbol_kind": str(item.get("symbol_kind") or ""),
        "roles": role_mask_names(mask),
        "role_mask": mask,
        "range": range_,
        "line": range_[0] + 1,
        "character": range_[1],
        "end_line": range_[2] + 1,
        "end_character": range_[3],
        "local": bool(item.get("local")) or bool(parsed["local"]),
    }


def _merge_records(*groups: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, tuple[int, ...]], dict[str, Any]] = {}
    for group in groups:
        for record in group:
            key = (str(record["path"]), str(record["symbol"]),
                   tuple(record["range"]))
            if key in merged:
                current = merged[key]
                current["role_mask"] |= int(record.get("role_mask") or 0)
                current["roles"] = role_mask_names(current["role_mask"])
                if not current.get("name"):
                    current["name"] = record.get("name") or record["symbol"]
                if not current.get("symbol_kind"):
                    current["symbol_kind"] = record.get("symbol_kind") or ""
                current["local"] = bool(current.get("local")) \
                    or bool(record.get("local"))
            else:
                merged[key] = dict(record)
    return sorted(merged.values(), key=_record_sort_key)


def _apply_symbol_info(definitions: list[dict[str, Any]],
                       references: list[dict[str, Any]],
                       info: Mapping[str, Mapping[str, Any]]) -> None:
    for record in definitions + references:
        entry = info.get(str(record.get("symbol") or ""))
        if not entry:
            continue
        display = str(entry.get("display_name") or "")
        if display:
            record["name"] = display
        kind = str(entry.get("kind") or "")
        if kind:
            record["symbol_kind"] = kind


def _collect(records: Any, *, root: str | Path | None) -> tuple[
        list[dict[str, Any]], list[dict[str, Any]],
        list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Collect definitions/references from any supported input shape."""
    definitions: list[dict[str, Any]] = []
    references: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []
    info: dict[str, dict[str, Any]] = {}

    if records is None:
        return definitions, references, documents, info
    if isinstance(records, Mapping):
        if "definitions" in records or "references" in records:
            definitions.extend(
                item for item in (
                    _coerce_record(record, default_kind="definition",
                                   root=root)
                    for record in (records.get("definitions") or []))
                if item is not None)
            references.extend(
                item for item in (
                    _coerce_record(record, default_kind="reference",
                                   root=root)
                    for record in (records.get("references") or []))
                if item is not None)
            file_rows = records.get("files") or []
            if isinstance(file_rows, (list, tuple)):
                for file_row in file_rows:
                    if isinstance(file_row, Mapping) and file_row.get("path"):
                        documents.append({
                            "path": str(file_row["path"]),
                            "language": str(file_row.get("language") or ""),
                        })
            definitions = _merge_records(definitions)
            references = _merge_records(references)
            return definitions, references, documents, info
        if "index" in records and isinstance(records["index"], Mapping) \
                and "documents" not in records:
            return _collect(records["index"], root=root)
        if "documents" in records and isinstance(
                records["documents"], (list, tuple, Mapping)):
            raw_documents = records["documents"]
            if isinstance(raw_documents, Mapping):
                expanded = []
                for key, value in raw_documents.items():
                    if isinstance(value, Mapping):
                        item = dict(value)
                        item.setdefault("relative_path", key)
                        expanded.append(item)
                raw_documents = expanded
            for index, document in enumerate(raw_documents):
                defs, refs, meta, local_info = _doc_records(
                    document, root=root, context=f"document[{index}]")
                definitions.extend(defs)
                references.extend(refs)
                documents.append(meta)
                info.update(local_info)
            info.update(_symbol_info_map(
                _first(records, ("external_symbols", "externalSymbols")) or [],
                context="external_symbols"))
            definitions = _merge_records(definitions)
            references = _merge_records(references)
            _apply_symbol_info(definitions, references, info)
            return definitions, references, documents, info
        if "occurrences" in records or any(
                key in records for key in _PATH_KEYS):
            defs, refs, meta, local_info = _doc_records(
                records, root=root, context="document")
            _apply_symbol_info(defs, refs, local_info)
            return defs, refs, [meta], local_info
        return [], [], [], {}
    if isinstance(records, (list, tuple)):
        items = list(records)
        if items and all(_is_record_like(item) for item in items):
            coerced = [item for item in (
                _coerce_record(record, default_kind="reference", root=root)
                for record in items) if item is not None]
            definitions = _merge_records(
                record for record in coerced
                if record.get("kind") == "definition")
            references = _merge_records(
                record for record in coerced
                if record.get("kind") == "reference")
            return definitions, references, [], {}
        for index, item in enumerate(items):
            defs, refs, docs, local_info = _collect(item, root=root)
            definitions.extend(defs)
            references.extend(refs)
            documents.extend(docs)
            info.update(local_info)
        definitions = _merge_records(definitions)
        references = _merge_records(references)
        _apply_symbol_info(definitions, references, info)
        return definitions, references, documents, info
    raise ScipFormatError(f"unsupported SCIP records input: {type(records)!r}")


def scip_records(document: Any, *, root: str | Path | None = None) -> dict[str, Any]:
    """Normalized ``{"definitions": [...], "references": [...]}`` for a doc.

    A whole index (or a list of documents) is also accepted for convenience;
    all documents are aggregated and duplicate occurrences are merged.
    """
    definitions, references, _documents, _info = _collect(document, root=root)
    return {"definitions": definitions, "references": references}


# --------------------------------------------------------------------------- #
# edges, summaries, one-shot payload
# --------------------------------------------------------------------------- #
def _build_edges(definitions: Iterable[Mapping[str, Any]],
                 references: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    defined: dict[str, set[str]] = defaultdict(set)
    for record in definitions:
        if record.get("local") or not record.get("symbol"):
            continue
        defined[str(record["symbol"])].add(str(record["path"]))
    weights: dict[tuple[str, str], float] = defaultdict(float)
    for record in references:
        if record.get("local"):
            continue
        targets = defined.get(str(record.get("symbol") or ""))
        if not targets:
            continue
        source = str(record["path"])
        for target in sorted(targets):
            if target == source:
                continue
            weights[(source, target)] += 1.0
    return [{"src": source, "tgt": target, "weight": float(weight)}
            for (source, target), weight in sorted(weights.items())]


def _file_rows(definitions: Iterable[Mapping[str, Any]],
               references: Iterable[Mapping[str, Any]],
               edges: Iterable[Mapping[str, Any]],
               documents: Iterable[Mapping[str, Any]]) -> tuple[
                   list[dict[str, Any]], dict[str, int]]:
    files: dict[str, dict[str, Any]] = {}
    symbols: dict[str, set[str]] = defaultdict(set)

    def row(path: str) -> dict[str, Any]:
        if path not in files:
            files[path] = {
                "path": path,
                "language": "",
                "definitions": 0,
                "references": 0,
                "local_definitions": 0,
                "local_references": 0,
                "unique_symbols": 0,
                "incoming_edges": 0,
                "outgoing_edges": 0,
            }
        return files[path]

    for document in documents:
        item = row(str(document["path"]))
        if document.get("language"):
            item["language"] = str(document["language"])
    for record in definitions:
        item = row(str(record["path"]))
        item["definitions"] += 1
        if record.get("local"):
            item["local_definitions"] += 1
        else:
            symbols[str(record["path"])].add(str(record["symbol"]))
    for record in references:
        item = row(str(record["path"]))
        item["references"] += 1
        if record.get("local"):
            item["local_references"] += 1
        else:
            symbols[str(record["path"])].add(str(record["symbol"]))
    for edge in edges:
        row(str(edge["src"]))["outgoing_edges"] += 1
        row(str(edge["tgt"]))["incoming_edges"] += 1
    rows = []
    for path in sorted(files):
        item = files[path]
        item["unique_symbols"] = len(symbols.get(path, set()))
        rows.append(item)
    totals = {
        "files": len(rows),
        "definitions": sum(1 for _ in definitions),
        "references": sum(1 for _ in references),
        "local_definitions": sum(1 for item in definitions if item.get("local")),
        "local_references": sum(1 for item in references if item.get("local")),
        "symbols": len({
            str(item["symbol"]) for item in definitions + references
            if not item.get("local")}),
        "defined_symbols": len({
            str(item["symbol"]) for item in definitions
            if not item.get("local")}),
        "edges": sum(1 for _ in edges),
    }
    return rows, totals


def scip_to_repo_map_edges(records: Any, *,
                           root: str | Path | None = None) -> list[dict[str, Any]]:
    """Repo-map-compatible edges ``{src, tgt, weight}`` from SCIP records.

    ``src`` is the referencing file, ``tgt`` the file defining the symbol.
    Local symbols and references to external/undefined symbols produce no
    edge. Weight is the number of distinct occurrence ranges merged into the
    edge (duplicates are already removed).
    """
    definitions, references, _documents, _info = _collect(records, root=root)
    return _build_edges(definitions, references)


def _graph_payload(records: Any, *, root: str | Path | None) -> dict[str, Any]:
    definitions, references, documents, _info = _collect(records, root=root)
    edges = _build_edges(definitions, references)
    files, totals = _file_rows(definitions, references, edges, documents)
    return {
        "ok": True,
        "format": "scip-graph-records",
        "version": 1,
        "documents": len(documents) if documents else len(files),
        "definitions": definitions,
        "references": references,
        "edges": edges,
        "files": files,
        "totals": totals,
    }


def scip_to_graph_records(records: Any, *,
                          root: str | Path | None = None) -> dict[str, Any]:
    """Stable, JSON-safe payload with records, edges and a file summary."""
    return _graph_payload(records, root=root)


def scip_graph_records(records: Any, *,
                       root: str | Path | None = None) -> dict[str, Any]:
    """Alias for :func:`scip_to_graph_records`."""
    return _graph_payload(records, root=root)


def scip_file_summary(records: Any, *,
                      root: str | Path | None = None) -> dict[str, Any]:
    """Per-file definition/reference/edge counts plus totals."""
    definitions, references, documents, _info = _collect(records, root=root)
    edges = _build_edges(definitions, references)
    files, totals = _file_rows(definitions, references, edges, documents)
    return {
        "ok": True,
        "format": "scip-file-summary",
        "version": 1,
        "documents": len(documents) if documents else len(files),
        "files": files,
        "totals": totals,
    }


def scip_summary(records: Any, *,
                 root: str | Path | None = None) -> dict[str, Any]:
    """Alias for :func:`scip_file_summary`."""
    return scip_file_summary(records, root=root)


def scip_import(path: str | Path, *,
                root: str | Path | None = None) -> dict[str, Any]:
    """One-shot CLI/MCP-friendly import: load an index and return the payload."""
    index = load_scip(path, root=root)
    payload = _graph_payload(index, root=root)
    payload["source"] = str(path)
    payload["input_format"] = str(index.get("format") or "")
    return payload


def scip_dumps(payload: Any, *, indent: int | None = 2) -> str:
    """Deterministic JSON rendering (sorted keys) for CLI/file output."""
    return json.dumps(payload, indent=indent, sort_keys=True,
                      ensure_ascii=False)
