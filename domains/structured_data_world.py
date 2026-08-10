"""StructuredDataWorld — a babble-loop world for teaching the substrate
the shared concept of STRUCTURED DATA across JSON / YAML / TOML / XML
(and their malformed variants).

Adapted from the HLEWorld pattern (domains/hle_world.py): a bank of
(text, expected_parsed_value) tasks; a TEACHER callable (in production
an LLM, here a heuristic stub); the substrate traverses the tasks. On
each one it CHECKS its grounded ParsingStrategy graph data; if no
strategy matches, it asks the teacher; it GROUNDS the response into
FormatID + CorruptionPattern + ParsingStrategy nodes; subsequent tasks
of the same shape resolve without teacher calls.

This is the "observe → identify gap → ask teacher → ground → parse →
re-use" cycle on a structured-data substrate.

Per CLAUDE.md this is world-adapter Python: mechanical text-to-graph
translation. No agent-side decisions live here — the strategy table
in graph form IS the agent's learned knowledge; future shapes match
against it via cheap heuristics.
"""
from __future__ import annotations

import json
import re
import subprocess
from typing import Any, Callable

import substrate_rs as srs


# ---------------------------------------------------------------------------
# Format detection — the substrate's quick "what shape is this?" heuristic.
# Sits at the I/O boundary; reports the lightest possible classification so
# the graph-resident strategy lookup can decide whether it already knows
# this shape.
# ---------------------------------------------------------------------------


_FORMAT_HEURISTICS = (
    # (format_id, regex-or-predicate)
    ("empty",
     lambda t: t.strip() == ""),
    ("xml",
     lambda t: t.lstrip().startswith("<")),
    ("json",
     lambda t: t.lstrip().startswith(("{", "[")) or t.strip() in ("null", "true", "false")
               or re.fullmatch(r"\s*-?\d+(\.\d+)?\s*", t) is not None),
    ("toml",
     lambda t: re.search(r"^\s*['\"]?\w[\w.-]*['\"]?\s*=\s*", t, re.MULTILINE) is not None
               and ":" not in t.split("=", 1)[0]),
    ("yaml",
     lambda t: re.search(r"^\s*\w[\w.-]*\s*:", t, re.MULTILINE) is not None
               or t.lstrip().startswith("- ")),
)


def _detect_format(text: str) -> str:
    """Lightweight format ID. Returns one of: empty / xml / json / toml / yaml
    / unknown. Pure syntactic — used to look up an already-grounded
    ParsingStrategy in the graph BEFORE asking the teacher."""
    for fmt, pred in _FORMAT_HEURISTICS:
        if pred(text):
            return fmt
    return "unknown"


def _detect_corruption(text: str, fmt: str) -> str:
    """Cheap corruption-class detector for a known format. Returns 'clean'
    when the format's strict parser would accept it, else one of the
    named corruption patterns the teacher can teach the substrate.

    The list isn't exhaustive — it's what the test bank exercises. Adding
    a new corruption pattern means adding a detector + a teacher rule;
    the architecture stays the same."""
    if fmt == "empty":
        return "empty"
    if fmt == "json":
        # Try strict json — if it parses we're clean.
        try:
            json.loads(text)
            return "clean"
        except json.JSONDecodeError:
            pass
        # Trailing comma before } or ]
        if re.search(r",\s*[}\]]", text):
            return "trailing_comma"
        # Unquoted key — bareword followed by colon inside an object
        if re.search(r"[{,]\s*[A-Za-z_]\w*\s*:", text):
            return "unquoted_key"
        # Missing closing brace/bracket — count mismatch
        if text.count("{") != text.count("}") or text.count("[") != text.count("]"):
            return "missing_brace"
        return "unknown_json_error"
    if fmt == "yaml":
        # YAML forbids tab indentation
        if "\n\t" in text or text.startswith("\t"):
            return "tab_indent"
        try:
            import yaml
            yaml.safe_load(text)
            return "clean"
        except Exception:
            return "unknown_yaml_error"
    if fmt == "toml":
        # Single-quoted key on the left of '=' is legal TOML literal-string
        # keys, but the test bank treats "'a' = 1" as a corruption pattern
        # the teacher will explain (it expects a bare key 'a').
        try:
            import tomllib
            tomllib.loads(text)
            # Real TOML accepts single-quoted keys; still flag if the
            # key was a *literal* single-quoted bareword the bank
            # considers a teaching moment.
            if re.match(r"^\s*'[A-Za-z_]\w*'\s*=", text):
                return "single_quoted_key"
            return "clean"
        except Exception:
            return "unknown_toml_error"
    if fmt == "xml":
        try:
            import xml.etree.ElementTree as ET
            ET.fromstring(text)
            return "clean"
        except ET.ParseError as e:
            msg = str(e).lower()
            if "mismatched" in msg or "tag" in msg:
                return "mismatched_tag"
            return "unknown_xml_error"
    return "unknown"


# ---------------------------------------------------------------------------
# Teacher stub — plays the role of an LLM teacher. In production this is a
# Claude subagent; here it's a heuristic Python parser. The substrate
# doesn't care which: the spec it returns is the same shape.
# ---------------------------------------------------------------------------


def teacher_stub(gap_description: str, text: str) -> dict[str, Any]:
    """Given a gap description and the raw text, return:
        {'format': str,
         'corruption_pattern': str,  # 'clean' when no corruption
         'parsed': Any | None,        # Python value, or None on legit failure
         'reasoning': str}            # one-line explanation
    """
    fmt = _detect_format(text)
    corruption = _detect_corruption(text, fmt)
    parsed, reasoning = _teacher_parse(text, fmt, corruption)
    return {
        "format": fmt,
        "corruption_pattern": corruption,
        "parsed": parsed,
        "reasoning": reasoning,
    }


# ---------------------------------------------------------------------------
# Real-LLM teacher — shells out to the `claude` CLI per request. Same return
# shape as teacher_stub; intended as a drop-in replacement so the substrate's
# graph-resident grounding logic is untouched. World-adapter I/O only:
# compose prompt, run subprocess, parse JSON, return spec dict.
# ---------------------------------------------------------------------------


_CLAUDE_CLI = "/home/matt/.local/bin/claude"

_TEACHER_PROMPT_TEMPLATE = """Parse this structured data text. Identify its format (json/yaml/toml/xml/csv/ini/unknown) and any corruption pattern.

Return ONLY a JSON object with these fields:
  format: one of json/yaml/toml/xml/csv/ini/unknown
  corruption: string ("clean" or a short label like "trailing_comma", "unquoted_key", etc.)
  parsed: the parsed structure (object/list/scalar/null)
  reasoning: one sentence

Text to parse:
{text}
"""


def _extract_json_payload(raw: str) -> str:
    """The CLI may wrap its JSON in ```json ... ``` fences or surround it
    with prose. Pull out the first balanced JSON object/array. Returns the
    raw string when no fence/braces present so the json.loads error surfaces
    clearly in the caller."""
    s = raw.strip()
    # ```json ... ``` fence
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", s, re.DOTALL)
    if m:
        s = m.group(1).strip()
    # First {...} balanced object (cheap counter, ignores strings — good
    # enough for the small responses we expect from the teacher).
    start = s.find("{")
    if start < 0:
        return s
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        c = s[i]
        if esc:
            esc = False
            continue
        if c == "\\":
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start:i + 1]
    return s[start:]


def teacher_via_claude(gap_description: str, text: str) -> dict[str, Any]:
    """Real-LLM teacher: shells out to `claude --print` to get a structured
    parse for `text`. Same spec dict shape as teacher_stub so the substrate's
    grounding code is teacher-agnostic.

    On any failure (timeout, non-zero exit, malformed JSON, missing field)
    returns a safe-default dict — the substrate then grounds it as an
    'unknown' parse and the test scores it as a miss; no crash."""
    from domains.no_llm import assert_llm_allowed
    assert_llm_allowed("structured_data_world.teacher_via_claude "
                       "(`claude --print` shell-out)")   # OZMA_NO_LLM hard switch
    prompt = _TEACHER_PROMPT_TEMPLATE.format(text=text)
    default = {
        "format": "unknown",
        "corruption_pattern": "unknown",
        "parsed": None,
        "reasoning": "teacher_via_claude: default (no usable response)",
    }
    try:
        result = subprocess.run(
            [_CLAUDE_CLI, "--print", prompt],
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        default["reasoning"] = "teacher_via_claude: subprocess timeout"
        return default
    except Exception as e:  # noqa: BLE001 — CLI invocation failures
        default["reasoning"] = f"teacher_via_claude: invocation failed: {e}"
        return default

    if result.returncode != 0:
        default["reasoning"] = (
            f"teacher_via_claude: nonzero exit {result.returncode}: "
            f"{(result.stderr or '').strip()[:120]}"
        )
        return default

    payload = _extract_json_payload(result.stdout or "")
    try:
        spec = json.loads(payload)
    except (json.JSONDecodeError, ValueError) as e:
        default["reasoning"] = (
            f"teacher_via_claude: malformed JSON ({e}): "
            f"{(result.stdout or '').strip()[:120]}"
        )
        return default

    if not isinstance(spec, dict):
        default["reasoning"] = "teacher_via_claude: response not an object"
        return default

    # Map LLM-side `corruption` field to the substrate's
    # `corruption_pattern` key. Default each field if absent.
    return {
        "format": spec.get("format") or "unknown",
        "corruption_pattern": (
            spec.get("corruption_pattern")
            or spec.get("corruption")
            or "clean"
        ),
        "parsed": spec.get("parsed"),
        "reasoning": spec.get("reasoning") or "teacher_via_claude: (no reasoning)",
    }


def _teacher_parse(text: str, fmt: str, corruption: str) -> tuple[Any, str]:
    """The teacher's actual parsing logic. Clean cases go through the
    standard parser; corruption cases apply the matching repair then
    retry. Returns (parsed_value, reasoning_string)."""
    if fmt == "empty" or corruption == "empty":
        return None, "empty input — no value"
    if fmt == "json":
        if corruption == "clean":
            return json.loads(text), "strict json parse"
        if corruption == "trailing_comma":
            repaired = re.sub(r",(\s*[}\]])", r"\1", text)
            try:
                return json.loads(repaired), "drop trailing comma, then strict parse"
            except json.JSONDecodeError as e:
                return None, f"trailing-comma repair failed: {e}"
        if corruption == "unquoted_key":
            # Quote bareword keys (preceded by { or ,).
            repaired = re.sub(
                r"([{,]\s*)([A-Za-z_]\w*)(\s*:)",
                r'\1"\2"\3', text)
            try:
                return json.loads(repaired), "quote bareword keys, then strict parse"
            except json.JSONDecodeError as e:
                return None, f"unquoted-key repair failed: {e}"
        if corruption == "missing_brace":
            # Append the missing closers in stack order — best-effort.
            repaired = text
            need_close_brace = repaired.count("{") - repaired.count("}")
            need_close_brack = repaired.count("[") - repaired.count("]")
            repaired += "}" * max(0, need_close_brace) + "]" * max(0, need_close_brack)
            try:
                return json.loads(repaired), "append missing closers, then strict parse"
            except json.JSONDecodeError as e:
                return None, f"missing-brace repair failed: {e}"
        return None, f"unhandled json corruption {corruption!r}"
    if fmt == "yaml":
        import yaml
        if corruption == "clean":
            return yaml.safe_load(text), "strict yaml parse"
        if corruption == "tab_indent":
            # First repair: drop the leading tab(s) entirely (treat the
            # tab-indented line as a sibling key, which is the user's most
            # likely intent — they meant a flat mapping, not a nested one,
            # and YAML rejects tab indentation outright).
            repaired = re.sub(r"^\t+", "", text, flags=re.MULTILINE)
            try:
                return yaml.safe_load(repaired), "drop leading tabs (sibling keys)"
            except Exception:
                pass
            # Fallback: replace tabs with two spaces (the literal indent).
            repaired = text.replace("\t", "  ")
            try:
                return yaml.safe_load(repaired), "replace tabs with 2 spaces"
            except Exception as e:
                return None, f"tab-indent repair failed: {e}"
        return None, f"unhandled yaml corruption {corruption!r}"
    if fmt == "toml":
        import tomllib
        if corruption == "clean":
            return tomllib.loads(text), "strict toml parse"
        if corruption == "single_quoted_key":
            # TOML actually allows literal-string keys, so try strict first
            try:
                return tomllib.loads(text), "literal-string keys are valid TOML"
            except Exception:
                pass
            repaired = re.sub(r"^\s*'([A-Za-z_]\w*)'\s*=", r"\1 =", text, flags=re.MULTILINE)
            try:
                return tomllib.loads(repaired), "drop single quotes from bareword keys"
            except Exception as e:
                return None, f"single-quoted-key repair failed: {e}"
        return None, f"unhandled toml corruption {corruption!r}"
    if fmt == "xml":
        import xml.etree.ElementTree as ET
        if corruption == "clean":
            root = ET.fromstring(text)
            return _xml_to_value(root), "strict xml parse, structural translation"
        if corruption == "mismatched_tag":
            return None, "mismatched tag — no safe repair"
        return None, f"unhandled xml corruption {corruption!r}"
    return None, f"unknown format {fmt!r}"


def _xml_to_value(elem) -> Any:
    """Translate an XML element to the structural Python value used as the
    expected output in the test bank. Children with repeated tags collapse
    to a list; otherwise we produce a dict keyed by child tag, with leaf
    text coerced to int when it looks numeric."""
    # Leaf with text only
    if len(list(elem)) == 0:
        txt = (elem.text or "").strip()
        if not txt:
            return None
        try:
            return int(txt)
        except ValueError:
            try:
                return float(txt)
            except ValueError:
                return txt
    # Collect children. Detect a list pattern (all same tag) vs dict.
    children = list(elem)
    tags = [c.tag for c in children]
    if len(set(tags)) == 1 and len(tags) > 1:
        return [_xml_to_value(c) for c in children]
    out: dict[str, Any] = {}
    for c in children:
        v = _xml_to_value(c)
        if c.tag in out:
            # Promote to list on second occurrence.
            if not isinstance(out[c.tag], list):
                out[c.tag] = [out[c.tag]]
            out[c.tag].append(v)
        else:
            out[c.tag] = v
    return out


# ---------------------------------------------------------------------------
# The world adapter itself.
# ---------------------------------------------------------------------------


# Edge types and node types the world adapter uses. Productions for these
# are opened in __init__ so the substrate's grammar permits the edges.
_NODE_TYPES = ("FormatID", "CorruptionPattern", "ParsingStrategy",
                "StructuredDataObservation", "TextShape")
_EDGE_TYPES = ("handles_format", "handles_corruption",
                "observed_strategy", "depends_on", "has_shape")


def _bucket_depth(d: int) -> str:
    """Bucket nesting_depth into 0 / 1 / 2 / 3+ so JSON depth=2 and YAML
    depth=0 don't fragment the shape space unnecessarily. The TextShape
    primitive measures DELIMITER depth, which is 0 for YAML (indent-based
    structure) and non-zero for JSON/TOML — so the buckets matter for
    cross-format clustering."""
    if d <= 0:
        return "0"
    if d == 1:
        return "1"
    if d == 2:
        return "2"
    return "3plus"


def _bucket_count(n: int) -> str:
    """Bucket a content-dependent count (kv_pair_count or seq_item_count)
    into 0 / 1 / 2-3 / 4+ so '[1,2,3]' and '[100,200,300,400]' share a
    shape — what matters is "has a few items", not the exact count.
    Without bucketing, every novel-content held-out input lands in a
    fresh cell and the cache is useless."""
    if n <= 0:
        return "0"
    if n == 1:
        return "1"
    if n <= 3:
        return "2to3"
    return "4plus"


def _shape_key_from_dict(shape: dict[str, Any]) -> str:
    """Compose a stable, hashable cache key from the TextShape Dict.
    Deliberately EXCLUDES `delimiters` (the surface family — braces vs
    indent vs angles) for the mapping/sequence/nested kinds, so
    JSON/YAML/TOML cluster onto the same key.

    EXCEPTION: when `kind == atomic` the structural signal is too thin
    (every isolated token, every empty, every XML leaf would collide)
    so the delimiter family is included to keep '42' (flat), '[]'
    (brackets), '<a>1</a>' (angles), '' (flat-empty) from sharing one
    cell. Without this, atoms across formats lump together and the
    cache mis-dispatches.

    Honest design note: `has_quotes` and `nesting_depth` were both in
    the original spec but they're surface-format markers in practice
    (JSON uses both, YAML/TOML use neither for the same structure).
    Including them fragments the cluster — '{\"x\":1}' and 'x: 1' carry
    the SAME structure but diverge on has_quotes and depth. We keep
    them only in the `kind=atomic` arm (where they help separate '\"a\"'
    from `a` and `[]` from ``) and drop them for structured cases."""
    kind = shape.get("kind", "atomic")
    kv = int(shape.get("kv_pair_count", 0) or 0)
    seq = int(shape.get("seq_item_count", 0) or 0)
    bal = bool(shape.get("balanced", True))
    base = (f"{kind}_kv{_bucket_count(kv)}_seq{_bucket_count(seq)}_"
            f"{'balanced' if bal else 'unbalanced'}")
    if kind == "atomic":
        quoted = bool(shape.get("has_quotes", False))
        depth_bucket = _bucket_depth(int(shape.get("nesting_depth", 0) or 0))
        delim = shape.get("delimiters", "flat")
        return (f"{base}_"
                f"{'quoted' if quoted else 'unquoted'}_"
                f"d{depth_bucket}_{delim}")
    return base


def _parser_succeeded(reasoning: str) -> bool:
    """Heuristic: did the underlying _teacher_parse actually produce a
    usable parse? Conventions in _teacher_parse:
      * 'failed:' / 'unhandled' / 'unknown format' → genuine non-parse
      * 'empty input — no value' → legitimate None (count as success)
      * 'mismatched tag — no safe repair' → legitimate None
      * anything else describing the parse → success
    The cache picks the first parser that succeeds for the input."""
    r = reasoning.lower()
    if "failed" in r:
        return False
    if r.startswith("unhandled"):
        return False
    if r.startswith("unknown format"):
        return False
    return True


class StructuredDataWorld:
    """Bank of (text, expected_parsed_value) tasks across JSON/YAML/TOML/XML
    + malformed variants. The substrate observes each text, identifies what
    it can't parse, asks the teacher, grounds the response (format ID +
    parse + corruption-handling pattern), then parses. Subsequent texts of
    same shape resolve without teacher calls."""

    def __init__(self, substrate, tasks: list[dict], teacher: Callable[[str, str], dict]):
        self.s = substrate
        self.tasks = list(tasks)
        self.teacher = teacher
        # graph-resident caches of FormatID and CorruptionPattern node IDs,
        # so we don't search by name on every task. The substrate is the
        # source of truth — these are query caches, not agent state.
        self._format_nodes: dict[str, Any] = {}
        self._corruption_nodes: dict[str, Any] = {}
        # shape_key -> TextShape Concept NodeID
        self._shape_nodes: dict[str, Any] = {}
        # shape_key -> {
        #     "parsers": [
        #         {"format": str, "corruption": str,
        #          "strategy_nid": NodeID,
        #          "success_count": int, "fail_count": int}
        #     ]
        # }
        # The substrate accumulates which (format, corruption) parsers
        # work for each abstract shape. On lookup, parsers are tried in
        # success-order; the first that produces a usable parse wins.
        self._strategy_cache: dict[str, dict[str, Any]] = {}
        self._teacher_call_count = 0

        # Open the productions the world's edges need. Each is best-effort —
        # if the production exists already (re-use), the native side raises;
        # we swallow it.
        for nt_a in _NODE_TYPES:
            for nt_b in _NODE_TYPES:
                for et in _EDGE_TYPES:
                    try:
                        self.s.add_production({
                            "src": {"type": nt_a, "var": "a"},
                            "edge_type": et,
                            "tgt": {"type": nt_b, "var": "b"},
                            "where": None,
                            "weight": {"type": "Lit", "value": 1.0},
                            "provenance": "structured_data_world",
                        })
                    except Exception:
                        pass

        # Re-load the strategy cache from the graph. The substrate is the
        # source of truth — when a fresh world adapter is constructed on
        # an already-trained substrate (e.g. for held-out evaluation), the
        # ParsingStrategy nodes already exist with a `shape_key` attr.
        # Re-build the in-memory record so the same lookup logic works.
        self._reload_cache_from_graph()

    def _reload_cache_from_graph(self) -> None:
        """Walk the substrate's ParsingStrategy nodes and rebuild
        self._strategy_cache from their shape_key attr. The substrate IS
        the source of truth; this method makes that explicit on world
        re-construction (cold-load)."""
        for sid in self.s.nodes("ParsingStrategy"):
            attrs = self.s.node(sid)["attrs"]
            shape_key = attrs.get("shape_key")
            if not shape_key:
                continue
            fmt = attrs.get("format", "unknown")
            corruption = attrs.get("corruption", "clean")
            rec = self._strategy_cache.setdefault(shape_key,
                                                  {"parsers": []})
            # De-dup by (format, corruption, strategy_nid).
            if any(p["strategy_nid"] == sid for p in rec["parsers"]):
                continue
            rec["parsers"].append({
                "format": fmt,
                "corruption": corruption,
                "strategy_nid": sid,
                # Reload with neutral counts; success-order will re-form
                # as the world runs.
                "success_count": 1,
                "fail_count": 0,
            })

    # ----- graph-resident lookup ------------------------------------------

    def _get_or_create_format(self, fmt: str):
        """Find a FormatID node by name (graph), creating one if absent.
        Caches the NodeID for subsequent lookups."""
        if fmt in self._format_nodes:
            return self._format_nodes[fmt]
        for nid in self.s.nodes("FormatID"):
            attrs = self.s.node(nid)["attrs"]
            if attrs.get("name") == fmt:
                self._format_nodes[fmt] = nid
                return nid
        nid = self.s.add_node("FormatID", {"name": fmt})
        self._format_nodes[fmt] = nid
        return nid

    def _get_or_create_corruption(self, pattern: str):
        if pattern in self._corruption_nodes:
            return self._corruption_nodes[pattern]
        for nid in self.s.nodes("CorruptionPattern"):
            attrs = self.s.node(nid)["attrs"]
            if attrs.get("name") == pattern:
                self._corruption_nodes[pattern] = nid
                return nid
        nid = self.s.add_node("CorruptionPattern", {"name": pattern})
        self._corruption_nodes[pattern] = nid
        return nid

    def _get_or_create_shape(self, shape_key: str, shape_dict: dict[str, Any]):
        """TextShape Concept node — the abstract structural fingerprint
        the substrate has now SEEN. The shape_key is its name; the raw
        TextShape Dict fields are attached as attrs so the knowledge is
        inspectable in the graph."""
        if shape_key in self._shape_nodes:
            return self._shape_nodes[shape_key]
        for nid in self.s.nodes("TextShape"):
            attrs = self.s.node(nid)["attrs"]
            if attrs.get("name") == shape_key:
                self._shape_nodes[shape_key] = nid
                return nid
        attrs = {"name": shape_key}
        # Carry the raw shape fields as attrs for inspection.
        for k, v in shape_dict.items():
            if isinstance(v, (str, int, float, bool)):
                attrs[k] = v
        nid = self.s.add_node("TextShape", attrs)
        self._shape_nodes[shape_key] = nid
        return nid

    def _compute_shape_key(self, text: str) -> tuple[str, dict[str, Any]]:
        """Evaluate the TextShape primitive on the input and reduce it
        to a stable cache key. The key abstracts away surface delimiter
        family (braces vs indent vs angles) so JSON / YAML / TOML with
        the same abstract structure share strategies."""
        term = srs.TextShape(srs.Lit(text))
        shape: dict[str, Any] = self.s.evaluate(term._json, None)
        return _shape_key_from_dict(shape), shape

    def _check_grounded_strategy(self, text: str):
        """Compute the abstract TextShape for `text`, look up the cached
        record. Returns (record, shape_key, shape_dict) if a record
        exists, else None.

        The record is `{"parsers": [{format, corruption, strategy_nid,
        success_count, fail_count}, ...]}`. _apply_strategy iterates the
        parsers in success-order, applies the first one that succeeds."""
        shape_key, shape_dict = self._compute_shape_key(text)
        rec = self._strategy_cache.get(shape_key)
        if rec is not None:
            return rec, shape_key, shape_dict
        return None

    def _identify_gap(self, text: str, shape_key: str | None = None) -> str:
        """Describe what the substrate doesn't know about this text. Used
        as the human-readable gap description sent to the teacher. With
        TextShape-keyed caching the gap is at the SHAPE level: either
        the shape is new to the substrate, or the shape is known but
        none of its grounded parsers handle this particular surface."""
        fmt = _detect_format(text)
        suffix = (f" (shape={shape_key})" if shape_key else "")
        if fmt == "unknown":
            return f"unknown format — cannot classify text{suffix}"
        corruption = _detect_corruption(text, fmt)
        if corruption == "clean":
            return f"format={fmt}: no ParsingStrategy for this shape{suffix}"
        return (f"format={fmt} corruption={corruption}: no ParsingStrategy"
                f" for this shape{suffix}")

    def _ground(self, spec: dict, text: str, shape_key: str,
                shape_dict: dict[str, Any]):
        """Ground the teacher's spec into the graph. Creates FormatID,
        CorruptionPattern, ParsingStrategy, TextShape nodes (if absent)
        and the depends_on / handles_* / has_shape edges that wire them.
        Appends the new parser to the shape's strategy record so future
        same-shape inputs try it first."""
        fmt = spec["format"]
        corruption = spec.get("corruption_pattern") or "clean"
        reasoning = spec.get("reasoning", "")
        parsed_ok = _parser_succeeded(reasoning)

        fmt_nid = self._get_or_create_format(fmt)
        corr_nid = self._get_or_create_corruption(corruption)
        shape_nid = self._get_or_create_shape(shape_key, shape_dict)

        # ParsingStrategy node — the substrate's learned recipe.
        strat_nid = self.s.add_node("ParsingStrategy", {
            "format": fmt,
            "corruption": corruption,
            "reasoning": reasoning,
            "shape_key": shape_key,
        })
        # Wire it: strategy handles_format → fmt; strategy
        # handles_corruption → corr; strategy depends_on each;
        # strategy has_shape → TextShape Concept. Edges make the
        # learned knowledge inspectable in the graph.
        for et, tgt in (("handles_format", fmt_nid),
                        ("handles_corruption", corr_nid),
                        ("depends_on", fmt_nid),
                        ("depends_on", corr_nid),
                        ("has_shape", shape_nid)):
            try:
                self.s.add_edge(strat_nid, et, tgt, None)
            except Exception:
                pass

        rec = self._strategy_cache.setdefault(shape_key, {"parsers": []})
        rec["parsers"].append({
            "format": fmt,
            "corruption": corruption,
            "strategy_nid": strat_nid,
            "success_count": 1 if parsed_ok else 0,
            "fail_count": 0 if parsed_ok else 1,
        })
        return strat_nid, rec

    def _apply_strategy(self, record: dict, text: str):
        """Try the shape's grounded parsers in success-order. First one
        whose _teacher_parse yields a usable result wins; its
        success_count is bumped so it sorts higher next time. If no
        parser succeeds, return None and let the caller fall back to
        the teacher (cross-format generalisation may have suggested a
        parser whose surface format doesn't actually accept this text).

        Parser invocations are wrapped: _teacher_parse for the (clean)
        path of each format calls the strict parser directly and lets
        exceptions propagate. When we try a cross-format parser on a
        surface it can't accept we want to FAIL CLEANLY, not crash —
        so each attempt sits inside try/except and a raised exception
        counts as a fail."""
        parsers = record["parsers"]
        # Stable sort: succeed-rate descending, tiebreaker by
        # success_count - fail_count.
        parsers.sort(key=lambda p: (p["success_count"] - p["fail_count"],
                                    p["success_count"]),
                     reverse=True)
        text_is_blank = text.strip() == ""
        for p in parsers:
            # An (empty, empty) parser legitimately produces None for
            # an empty input but is INAPPLICABLE to a non-empty input
            # (it would mask a "didn't recognise" as success). Gate it.
            if p["format"] == "empty" and not text_is_blank:
                p["fail_count"] += 1
                continue
            try:
                parsed, reason = _teacher_parse(text, p["format"],
                                                p["corruption"])
            except Exception as e:  # noqa: BLE001 — any parse exception
                reason = f"cross-format parse failed: {e}"
                parsed = None
            if _parser_succeeded(reason):
                p["success_count"] += 1
                return parsed, p["format"], p["corruption"], p["strategy_nid"]
            else:
                p["fail_count"] += 1
        return None  # cache miss — caller falls back to teacher

    def _record_observation(self, text: str, fmt: str, corruption: str, parsed: Any):
        """Add a StructuredDataObservation node with the raw text + outcome.
        Kept lightweight — the truth is the ParsingStrategy."""
        try:
            self.s.add_node("StructuredDataObservation", {
                "text": text,
                "format": fmt,
                "corruption": corruption,
                "parsed_repr": repr(parsed),
            })
        except Exception:
            pass

    # ----- the world's traversal ------------------------------------------

    def run(self) -> list[dict]:
        """For each task: compute the abstract TextShape; look up its
        cached parser-record; try parsers in success-order. On a record
        miss OR all-parsers-fail, ask the teacher and ground the spec
        (which appends a parser to the shape's record). Cross-format
        generalisation: a parser grounded under one (format, corruption)
        is tried for ALL shape-equivalent texts in other formats."""
        log: list[dict] = []
        for task in self.tasks:
            text = task["text"]
            expected = task["expected"]
            calls_before = self._teacher_call_count
            gaps_asked: list[str] = []
            strat_nid: Any = None
            parsed: Any = None
            fmt = "unknown"
            corruption = "unhandled"

            grounded = self._check_grounded_strategy(text)
            shape_key: str | None = None
            shape_dict: dict[str, Any] | None = None
            applied = None
            if grounded is not None:
                record, shape_key, shape_dict = grounded
                applied = self._apply_strategy(record, text)
                if applied is not None:
                    parsed, fmt, corruption, strat_nid = applied

            if applied is None:
                # Either no record for this shape, or every grounded
                # parser failed on this surface. Ask the teacher.
                if shape_key is None:
                    shape_key, shape_dict = self._compute_shape_key(text)
                gap = self._identify_gap(text, shape_key)
                gaps_asked.append(gap)
                spec = self.teacher(gap, text)
                self._teacher_call_count += 1
                strat_nid, _rec = self._ground(spec, text, shape_key,
                                               shape_dict or {})
                fmt = spec["format"]
                corruption = spec.get("corruption_pattern") or "clean"
                # The teacher already produced 'parsed'; we use it
                # directly for THIS task. Future tasks of the same shape
                # will try this parser first.
                parsed = spec["parsed"]

            self._record_observation(text, fmt, corruption, parsed)
            matched = _values_equal(parsed, expected)
            log.append({
                "text": text,
                "expected": expected,
                "format_id": fmt,
                "corruption": corruption,
                "parsed": parsed,
                "matched": matched,
                "gaps_asked": gaps_asked,
                "teacher_calls": self._teacher_call_count - calls_before,
                "strategy_nid": strat_nid,
                "shape_key": shape_key,
            })
        return log

    # ----- summary helpers ------------------------------------------------

    @staticmethod
    def summary(log: list[dict]) -> dict:
        return {
            "tasks": len(log),
            "matched": sum(1 for e in log if e["matched"]),
            "teacher_calls": sum(e["teacher_calls"] for e in log),
            "asks": sum(len(e["gaps_asked"]) for e in log),
        }


def _values_equal(a: Any, b: Any) -> bool:
    """Comparison robust to small numeric / type drift (1 == 1.0 inside
    dicts; sequences compare elementwise). Used to score 'matched' in the
    task log without forcing the test bank to be byte-exact."""
    if a is None and b is None:
        return True
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_values_equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(_values_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    return a == b


# ---------------------------------------------------------------------------
# Standard test bank — the 12 tasks the spec calls for.
# ---------------------------------------------------------------------------


def default_task_bank() -> list[dict]:
    """The bank described in the spec: clean JSON/YAML/TOML/XML + 7
    malformed variants + empty + the literal 'null'. Each task records a
    text, an expected Python value (or None for legitimate failures), and
    an optional format hint."""
    return [
        # Clean cases — one per format.
        {"text": '{"a": 1, "b": [2, 3]}',
         "expected": {"a": 1, "b": [2, 3]},
         "format_hint": "json"},
        {"text": "a: 1\nb:\n  - 2\n  - 3\n",
         "expected": {"a": 1, "b": [2, 3]},
         "format_hint": "yaml"},
        {"text": "a = 1\nb = [2, 3]\n",
         "expected": {"a": 1, "b": [2, 3]},
         "format_hint": "toml"},
        {"text": "<root><a>1</a><b><item>2</item><item>3</item></b></root>",
         "expected": {"a": 1, "b": [2, 3]},
         "format_hint": "xml"},
        # JSON malformed.
        {"text": '{"a": 1, "b": 2,}',
         "expected": {"a": 1, "b": 2},
         "format_hint": "json"},
        {"text": '{a: 1, b: 2}',
         "expected": {"a": 1, "b": 2},
         "format_hint": "json"},
        # YAML malformed.
        {"text": "a: 1\n\tb: 2\n",
         "expected": {"a": 1, "b": 2},
         "format_hint": "yaml"},
        # TOML malformed (the bank treats single-quoted bareword keys as a
        # teaching moment, even though they're technically valid TOML).
        {"text": "'a' = 1\n",
         "expected": {"a": 1},
         "format_hint": "toml"},
        # XML malformed — mismatched tag has no safe parse, expected None.
        {"text": "<a>1</b>",
         "expected": None,
         "format_hint": "xml"},
        # JSON missing brace.
        {"text": '{"a": {"b": 1}',
         "expected": {"a": {"b": 1}},
         "format_hint": "json"},
        # Empty.
        {"text": "",
         "expected": None,
         "format_hint": None},
        # The string literal 'null' — JSON's null.
        {"text": "null",
         "expected": None,
         "format_hint": "json"},
    ]
