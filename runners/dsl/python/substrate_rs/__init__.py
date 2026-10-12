"""substrate_rs — Rust runtime for the (G, Γ) substrate DSL.

Drop-in replacement for `substrate/`. The 50 Term variants are
dataclass-style Python factories (matching `substrate/dsl.py` exactly);
Substrate / Grammar / persistence delegate to the native Rust engine.

The native module lives at `substrate_rs._native`; the surface here
matches the existing Python `substrate` package so a caller can swap
`from substrate import Filter, Lit, Var` → `from substrate_rs import
Filter, Lit, Var` without other changes.

The `substrate_rs.ext` submodule will carry capability extensions
(attr indices, EdgeAttr, hooks, observability) that go beyond the
Python baseline — those live there so the core drop-in surface stays
parity-pinned.
"""
from __future__ import annotations

import dataclasses
from typing import Any, Iterable

from . import _native

# --- Re-exports from the native module ---

#: Lightweight handle for a graph node. Hashable, equal-by-value.
NodeID = _native.NodeID

#: Raised when the consistency checker C rejects a proposed edge under
#: Γ. Message carries the Type-1 vs Type-2 distinction.
InadmissibleEdge = _native.InadmissibleEdge

#: Context-aware EFFORT DIAL — composes the EDF deadline / thread-mode /
#: CPU / memory bound / shape-salience surprise into one effort knob
#: (L6 register_knob_u64) that scales order-N analysis passes + the
#: salience threshold. See runners/dsl/src/effort_dial.rs.
EffortDial = _native.EffortDial

#: Native Substrate — wrapped below by `Substrate` for the Pythonic
#: surface (mostly the `with substrate.transform()` context manager
#: that the native side doesn't expose).
_NativeSubstrate = _native.Substrate
_NativeSubstrateSnapshot = _native.SubstrateSnapshot


def version() -> str:
    """Native crate version — useful when debugging which wheel is loaded."""
    return _native.version()


# --- Term factories ----------------------------------------------------

class Term:
    """Base class for every Term factory.

    Each subclass is a frozen dataclass mirroring `substrate/dsl.py`. The
    constructor captures kwargs into a JSON dict on `self._json` — that
    dict is the wire form the native engine understands. `evaluate(env,
    substrate)` ships the dict over the FFI boundary; `to_dict` and
    `from_dict` round-trip via the same form.
    """

    __slots__ = ("_json",)

    def __init__(self, type_name: str, **fields: Any):
        # `_serialise_field` recurses on Term children so a nested
        # Filter(...) becomes a nested dict, matching jsonio.py output.
        out: dict[str, Any] = {"type": type_name}
        for k, v in fields.items():
            out[k] = _serialise_field(v)
        object.__setattr__(self, "_json", out)

    def to_dict(self) -> dict[str, Any]:
        """The JSON wire form. Identical to the Python `term_to_json` output."""
        return self._json

    def evaluate(self, env: dict[str, Any] | None, substrate: "Substrate | _NativeSubstrate") -> Any:
        """Evaluate this Term against `substrate`'s graph under `env`.

        Matches the existing API surface — Python tests call
        `term.evaluate(env, substrate.graph)` or `term.evaluate(env,
        substrate)`. Either works.
        """
        inner = substrate._inner if isinstance(substrate, Substrate) else substrate
        return inner.evaluate(self._json, env)

    def __repr__(self) -> str:  # debugging aid
        return f"{self._json['type']}({', '.join(f'{k}={v!r}' for k, v in self._json.items() if k != 'type')})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Term) and self._json == other._json

    def __hash__(self) -> int:
        # Term JSON is JSON-serialisable so a stable hash falls out.
        import json
        return hash(json.dumps(self._json, sort_keys=True, default=str))


def _serialise_field(v: Any) -> Any:
    """Recursively convert a field value to its JSON wire form.

    NodeID is the one substrate-side value type JSON doesn't know
    natively — we tag it as `{"__nid__": int}` so the Rust-side
    `decode_value` recovers it as `Value::Node`. Matches the
    `substrate.persistence.encode` convention exactly so wire-format
    files round-trip between the engines.
    """
    if isinstance(v, Term):
        return v._json
    if isinstance(v, (list, tuple)):
        return [_serialise_field(x) for x in v]
    if isinstance(v, NodeID):
        return {"__nid__": v.value}
    if isinstance(v, bytes):
        # Surface(Bytes) wire format — matches `persist.rs::encode_value`
        # so Lit(b"...") rehydrates as Value::Surface(Bytes, ...) on the
        # Rust side. Hex string payload to keep JSON ASCII-safe.
        return {"__surface__": None, "kind": "bytes",
                "payload": v.hex()}
    return v


# Each variant below maps 1:1 onto a TermNode variant in `term.rs`. The
# arg names match `substrate/dsl.py` so tests don't need to change.
def Var(name: str) -> Term:
    return Term("Var", name=name)


def Lit(value: Any) -> Term:
    return Term("Lit", value=value)


def TypeOf(node: Term) -> Term:
    return Term("TypeOf", node=node)


def Attr(node: Term, key: str) -> Term:
    return Term("Attr", node=node, key=key)


def SetT(items: tuple | list = ()) -> Term:
    return Term("SetT", items=tuple(items))


def In(member: Term, container: Term) -> Term:
    return Term("In", member=member, container=container)


def Eq(a: Term, b: Term) -> Term: return Term("Eq", a=a, b=b)
def Lt(a: Term, b: Term) -> Term: return Term("Lt", a=a, b=b)
def Lte(a: Term, b: Term) -> Term: return Term("Lte", a=a, b=b)
def Gt(a: Term, b: Term) -> Term: return Term("Gt", a=a, b=b)
def Gte(a: Term, b: Term) -> Term: return Term("Gte", a=a, b=b)


def FbFrameSeq(fb: Term) -> Term:
    """The attached shared-memory framebuffer's current `frame_seq` (an
    Int), or `None` if `fb` isn't a live-attached `fb_id` — the
    "when to look" oracle a Rule's `where`-clause gates on. `fb`
    evaluates to the Int `fb_id` a prior `fb_attach` call returned.
    See `runners/dsl/src/framebuffer.rs`'s wire contract + `term.rs`'s
    `TermNode::FbFrameSeq` doc comment."""
    return Term("FbFrameSeq", fb=fb)


def Neighbours(node: Term, edge_type: str | None = None) -> Term:
    return Term("Neighbours", node=node, edge_type=edge_type)


def InNeighbours(node: Term, edge_type: str | None = None) -> Term:
    return Term("InNeighbours", node=node, edge_type=edge_type)


def MapNeighbours(source: Term, edge_type: str | None = None) -> Term:
    return Term("MapNeighbours", source=source, edge_type=edge_type)


def Count(source: Term) -> Term:
    return Term("Count", source=source)


def Filter(source: Term, var_name: str, predicate: Term) -> Term:
    return Term("Filter", source=source, var_name=var_name, predicate=predicate)


def Exists(source: Term, var_name: str, predicate: Term) -> Term:
    return Term("Exists", source=source, var_name=var_name, predicate=predicate)


def Sum(source: Term, var_name: str, value: Term) -> Term:
    return Term("Sum", source=source, var_name=var_name, value=value)


def Prod(source: Term, var_name: str, value: Term) -> Term:
    return Term("Prod", source=source, var_name=var_name, value=value)


def MinOver(source: Term, var_name: str, value: Term, default: Term | None = None) -> Term:
    return Term("MinOver", source=source, var_name=var_name, value=value, default=default)


def MaxOver(source: Term, var_name: str, value: Term, default: Term | None = None) -> Term:
    return Term("MaxOver", source=source, var_name=var_name, value=value, default=default)


def Pick(source: Term) -> Term:
    return Term("Pick", source=source)


def Tokenize(text: Term) -> Term:
    """Whitespace-tokenize a string; returns tuple of (start, byte_len)
    position pairs. Agent-built via babble loop."""
    return Term("Tokenize", text=text)


def FinalToken(text: Term) -> Term:
    return Term("FinalToken", text=text)


def Tokenize2(text: Term) -> Term:
    """Whitespace-tokenize a string; returns tuple of (start, byte_len)
    position pairs. Agent-built via babble loop."""
    return Term("Tokenize2", text=text)


def ReadFile(path: Term) -> Term:
    """Read a file at `path` (a string). Returns a Text surface with the
    file contents, or None on read error. Agent-built via babble loop."""
    return Term("ReadFile", path=path)


def StringIndexOf(haystack: Term, needle: Term) -> Term:
    """Find `needle` in `haystack` (both strings). Returns the byte offset
    as Int, or -1 if not found / non-string inputs. Agent-built."""
    return Term("StringIndexOf", haystack=haystack, needle=needle)


def StringSlice(s: Term, start: Term, end: Term) -> Term:
    """Byte-slice s[start..end]. Out-of-bounds clamps to 0..len.
    Returns a Text surface. Agent-built via babble loop."""
    return Term("StringSlice", s=s, start=start, end=end)


def StringConcat(parts: tuple | list = ()) -> Term:
    """Concatenate Str / Text-surface `parts` into a single Text surface.
    Other value types are skipped. Agent-built via babble loop."""
    return Term("StringConcat", parts=tuple(parts))


def Verify(term: Term, env: Term, expected: Term) -> Term:
    """Verify that `term` (evaluated under bindings from `env`) equals
    `expected`. `env` should evaluate to a Dict of (Str, Value) pairs —
    each entry is pushed onto the eval env stack as a Var binding before
    `term` runs, then popped. Non-Dict `env` → empty bindings. Returns
    a Bool. The substrate's "does this Term-tree compute X" primitive."""
    return Term("Verify", term=term, env=env, expected=expected)


def MkDict(items: tuple | list = ()) -> Term:
    """Build a Dict at evaluate time from an alternating (key, value,
    key, value, ...) sequence of child Terms. Keys must evaluate to
    Str (or Surface Text); pairs with non-string keys are skipped.
    Odd-length items: the trailing key with no value is dropped.
    Pairs are canonical-sorted by key. The substrate's generic
    Term-tree composition primitive — rule effects compose Term-JSON-
    shaped Dicts at fire time with match-binding values spliced in."""
    return Term("MkDict", items=tuple(items))


def ToJsonString(value: Term) -> Term:
    """Serialise `value` (typically a `MkDict`/`Append`-built structure)
    to JSON text, returned as a Text surface (the same Str-vs-Surface
    convention `StringConcat` uses). Lets a meta-rule land a graph-native
    Dict/Tuple into a flat STRING attr (e.g. a `SeedDelta.add_rules`
    JSON-list attr `domains/experiment_dispatch.py` reads with
    `json.loads`) -- `MkDict`/`Append` alone produce a Dict/Tuple Value,
    which `json.loads` can't consume directly."""
    return Term("ToJsonString", value=value)


def FromJsonString(text: Term) -> Term:
    """Inverse of `ToJsonString`: parse `text` (a Str or Text surface
    holding JSON) into a graph-native Value tree -- object -> Dict (keys
    as Text surfaces), array -> Tuple, string -> Text surface, number ->
    Int/Float, true/false -> Bool, null -> None. Invalid JSON or a
    non-string `text` -> None. Lets a meta-rule read a JSON-string
    provenance attr (e.g. a `RuleSummary.rule_json` mirror) back into
    Term-tree land for structural inspection/rewrite (see
    `ShiftThresholdLits`)."""
    return Term("FromJsonString", text=text)


def ShiftThresholdLits(tree: Term, shift: Term) -> Term:
    """Deep-copy `tree` (a Value tree -- from `FromJsonString`, or a
    graph-native Rule node's own `effect`/`where` attr), shifting every
    numeric decision-threshold Lit it finds: a
    `{"type":"Lt","b":{"type":"Lit","value":N}}` node's N becomes
    N - `shift`; a `{"type":"Gt", ...}` node's N becomes N + `shift`.
    Every other Dict/Tuple node is copied unchanged, recursing so a
    nested Lt/Gt deeper in the tree is still found. Mirrors
    `domains/reflective_faculty.py`'s `_find_threshold_lits` +
    `_shift_rule_thresholds` exactly -- the graph-native primitive for a
    meta-rule to do that structural rewrite itself."""
    return Term("ShiftThresholdLits", tree=tree, shift=shift)


def DictGet(dict_: Term, key: Term) -> Term:
    """Read a field out of a Dict VALUE by key -- the Dict-value twin of
    `Attr` (which only reads graph-Node attrs; `Attr(some_dict_value, ...)`
    is always None). `key` compares string-like (Str or Text surface)
    against the Dict's own keys, so it reads both a `MkDict`-built Dict
    (Str keys) and a `FromJsonString`-parsed Dict (Text-surface keys)
    uniformly. None if `dict_` isn't a Dict or no pair matches."""
    return Term("DictGet", **{"dict": dict_, "key": key})


def RewriteTreeNodes(tree: Term, field: Term, value_map: Term, type_filter: Term | None = None) -> Term:
    """Deep-copy `tree` (a Value tree -- typically from `FromJsonString`,
    or a graph-native Rule node's own `effect`/`where` attr), and for every
    Dict node reachable inside it (recursing into children FIRST, same
    order `ShiftThresholdLits` uses): if `type_filter` is given, require
    the node's own `"type"` field to string-like-equal it; then look up
    the node's `field` entry's CURRENT value in `value_map` (a Dict Value,
    e.g. `MkDict`-built, mapping old field-values -> new field-values,
    string-like compared the same way `DictGet` compares keys) -- if a
    mapping is found, replace ONLY that one field's value, leaving every
    other field untouched. `type_filter=None` matches every Dict node.

    The general conditional-tree-rewrite primitive `domains/edit_ops.py`'s
    two effects-only structural appliers need -- one Term covers both:

      - `apply_flip_comparison` (Lt<->Gt, Lte<->Gte): `field=Lit("type")`,
        `type_filter=None` (the field being checked IS the field being
        rewritten -- `value_map`'s own keys are the guard), `value_map`
        holding all four pairs so a single pass flips every comparison
        node without a double-flip risk from sequential re-application.
      - `apply_swap_term_leaf` (swap which attr key a decision reads):
        `type_filter=Lit("Attr")`, `field=Lit("key")`,
        `value_map={old_key: new_key}`.

    `ShiftThresholdLits` stays separate -- it shifts a NUMERIC VALUE by an
    arithmetic amount depending on which of two types the node is, not a
    same-shaped string-to-string field remap."""
    return Term("RewriteTreeNodes", tree=tree, type_filter=type_filter, field=field, value_map=value_map)


def AttrKeyRanking(tree: Term) -> Term:
    """Collect every distinct `{"type":"Attr","key":<str>}` node's `key`
    value reachable inside `tree` (recursing into every Dict node's
    children AND Tuple items -- the SAME walk `RewriteTreeNodes` performs),
    tally occurrence COUNTS per distinct key, and return them as a RANKED
    Tuple of `(key, count)` pairs, sorted by `(-count, key)` -- IDENTICAL to
    `domains/edit_ops.py`'s `find_attr_keys`, the Python oracle
    `_compose_structural_variant`'s `swap_term_leaf` branch uses to pick its
    SITE (the two most-referenced Attr keys in a rule's effects tree).

    Deliberately a Tuple (ORDER preserved), not a Dict -- a Dict's pairs
    get canonically re-sorted BY KEY (see `MkDict`), which would destroy
    the frequency ranking. A caller reads the #1 (most-referenced) key via
    `IndexAt(IndexAt(ranking, 0), 0)` and the #2 via `IndexAt(IndexAt(
    ranking, 1), 0)`, then builds `{#1: #2}` via `MkDict` for
    `RewriteTreeNodes`'s own `value_map` (`type_filter=Lit("Attr")`,
    `field=Lit("key")`) -- the SITE-COMPUTATION half `RewriteTreeNodes`
    alone can't provide (it only REWRITES matching nodes in place; it has
    no way to accumulate a frequency table across a tree walk). This is
    the one missing primitive `apply_swap_term_leaf`'s composition needed
    to go fully graph-native -- see
    `seeds/composer_experiment_graph.json`'s
    `compose_experiment_structure_graph` swap branch."""
    return Term("AttrKeyRanking", tree=tree)


def ListDrop(list_: Term, index: Term) -> Term:
    """Drop the element at `index` from `list_` (a Tuple Value -- e.g. a
    rule's own `match` array read via `DictGet`), returning a NEW Tuple
    with that element removed, order preserved. Negative `index` counts
    from the end (`IndexAt`'s convention). An `index` out of range (after
    that adjustment) is a no-op: `list_`'s elements come back unchanged,
    in order -- the caller decides whether an out-of-range/too-short drop
    is "inert" for its purposes (mirrors `domains/edit_ops.py`'s
    `apply_drop_match_edge`, whose own inert check -- index out of range
    OR would leave `match` with fewer than 1 edge -- is the CALLER's
    concern; this Term only performs the mechanical removal). The
    index-based twin of `FilterList` (content-predicate removal) --
    `FilterList`'s predicate only sees the element itself, never its
    position, so it can't express a positional drop."""
    return Term("ListDrop", **{"list": list_, "index": index})


def TextShape(text: Term) -> Term:
    """Observe the abstract structural SHAPE of `text` (a Str or
    Text-surface). Returns a Dict whose keys classify the input
    surface-format-agnostically:

      delimiters    Str — braces / brackets / angles / indent / flat / unbalanced
      kind          Str — mapping / sequence / atomic / nested
      nesting_depth Int — max balanced-delimiter depth
      kv_pair_count Int — estimated top-level key-value pairs
      seq_item_count Int — estimated top-level sequence items
      has_quotes    Bool
      balanced      Bool — all delimiter pairs balance
      whitespace_kind Str — compact / multiline

    A structural fingerprint, NOT a parser — the goal is to cluster
    "similar shapes" across surface formats (JSON / YAML / TOML /
    XML / etc.) so cumulative learning generalises."""
    return Term("TextShape", text=text)


def Argmax(source: Term, var_name: str, value: Term,
           default: Term | None = None) -> Term:
    """Return the ELEMENT of `source` maximising `value`. Tiebreaker:
    first encountered. Empty source → `default` (or None)."""
    return Term("Argmax", source=source, var_name=var_name,
                value=value, default=default)


def Argmin(source: Term, var_name: str, value: Term,
           default: Term | None = None) -> Term:
    """Mirror of Argmax — element minimising `value`."""
    return Term("Argmin", source=source, var_name=var_name,
                value=value, default=default)


# --- universal codec primitives (Phase 16b/16c) -----------------------
#
# Orthogonal building blocks every entropy-coded format needs.
# BitsAt/BitsWrite — CORE; any binary format. HuffmanDecodeStream/
# HuffmanEncodeStream — optional `huffman` feature block (ISA §3.3);
# software fallback over graph-resident HuffmanTable nodes; hardware
# runners dispatch to codec silicon. Compose with codec-specific
# graph structure (Mp3Granule, H264Slice, JpegBlock, …) to express
# any codec transform as graph data + Rules.

def BitsAt(buffer: Term, bitpos: Term, n_bits: Term) -> Term:
    """Read `n_bits` MSB-first from a Surface(Bytes) buffer at `bitpos`.
    Returns Int. Universal bit-field access for any binary format."""
    return Term("BitsAt", buffer=buffer, bitpos=bitpos, n_bits=n_bits)


def BitsWrite(buffer: Term, bitpos: Term, value: Term,
              n_bits: Term) -> Term:
    """Write the low `n_bits` of `value` MSB-first into a fresh copy
    of `buffer` at `bitpos`. Returns Surface(Bytes). Pure
    (immutable) — chain via Let when building a stream."""
    return Term("BitsWrite", buffer=buffer, bitpos=bitpos,
                value=value, n_bits=n_bits)


def BitsAtAll(buffer: Term, reads: Term) -> Term:
    """Vectorised BitsAt — read many bit-fields from `buffer` in ONE
    runner call. `reads` is a Tuple of (bitpos, n_bits) pairs.
    Returns Tuple of Ints of the same arity. The amortised version
    of BitsAt for bulk parses (codec tables, multi-field walks)."""
    return Term("BitsAtAll", buffer=buffer, reads=reads)


def BitsWriteAll(buffer: Term, writes: Term) -> Term:
    """Vectorised BitsWrite — apply many bit-field writes to `buffer`
    in ONE copy. `writes` is a Tuple of (bitpos, value, n_bits)
    triples. Returns the rewritten Surface(Bytes). Use for bulk
    edits (codec tables, multi-field rewrites) where per-call copies
    of large buffers dominate. The amortised version of BitsWrite."""
    return Term("BitsWriteAll", buffer=buffer, writes=writes)


def HuffmanDecodeStream(buffer: Term, bitpos: Term, table: Term,
                        n_pairs: Term) -> Term:
    """Decode `n_pairs` (x, y) pairs from `buffer` starting at
    `bitpos` using the graph-resident HuffmanTable that `table`
    resolves to. Returns `Tuple(pairs_tuple, new_bitpos)`. Universal
    Huffman pair decoder — MP3, JPEG, H.264 CAVLC, Vorbis, FLAC
    all use this shape with different tables."""
    return Term("HuffmanDecodeStream", buffer=buffer, bitpos=bitpos,
                table=table, n_pairs=n_pairs)


def HuffmanEncodeStream(buffer: Term, bitpos: Term, pairs: Term,
                        table: Term) -> Term:
    """Mirror of HuffmanDecodeStream. `pairs` is a Tuple of
    (x, y) Int pairs. Returns `Tuple(new_buffer, new_bitpos)`."""
    return Term("HuffmanEncodeStream", buffer=buffer, bitpos=bitpos,
                pairs=pairs, table=table)


def ExpGolombDecode(buffer: Term, bitpos: Term) -> Term:
    """Universal Exp-Golomb decode (ITU-T H.264 §9.1 ue(v)). Count
    leading zeros M; read 1-bit marker; read M-bit suffix;
    value = 2^M - 1 + suffix. Returns `Tuple(value, new_bitpos)` or
    `None` if buffer underflows. H.264, HEVC, VVC, AVS3 all entropy-
    code unsigned integers this way."""
    return Term("ExpGolombDecode", buffer=buffer, bitpos=bitpos)


def ExpGolombDecodeSigned(buffer: Term, bitpos: Term) -> Term:
    """Signed Exp-Golomb decode (H.264 §9.1.1 se(v)). Decodes the
    unsigned codeword `k`, then maps to signed: k=0 → 0, k=1 → 1,
    k=2 → -1, k=3 → 2, k=4 → -2, ... Returns `Tuple(value, new_bp)`."""
    return Term("ExpGolombDecodeSigned", buffer=buffer, bitpos=bitpos)


def ExpGolombEncode(buffer: Term, bitpos: Term, value: Term) -> Term:
    """Mirror of ExpGolombDecode. Writes ue(v) of unsigned `value`
    into `buffer` at `bitpos`; extends the buffer if needed.
    Returns `Tuple(new_buffer, new_bitpos)`."""
    return Term("ExpGolombEncode", buffer=buffer, bitpos=bitpos,
                value=value)


def ExpGolombEncodeSigned(buffer: Term, bitpos: Term, value: Term) -> Term:
    """Mirror of ExpGolombDecodeSigned. Writes se(v) of signed `value`
    into `buffer` at `bitpos`. Returns `Tuple(new_buffer, new_bp)`."""
    return Term("ExpGolombEncodeSigned", buffer=buffer, bitpos=bitpos,
                value=value)


def Holds(concept: str, node: Term | None = None, node2: Term | None = None) -> Term:
    return Term("Holds", concept=concept, node=node, node2=node2)


def EvalSubgraph(node: Term) -> Term:
    """Evaluate the Term-tree rooted at the NodeID `node` resolves to.
    The runner walks that node as a Term subgraph root, re-arenas it,
    and evaluates under the CURRENT env. Lets graph-resident Terms
    reference other graph-resident Terms by NodeID — the substrate's
    "evaluate what this attr/edge points to" primitive."""
    return Term("EvalSubgraph", node=node)


def And(items: tuple | list = ()) -> Term: return Term("And", items=tuple(items))
def Or(items: tuple | list = ()) -> Term:  return Term("Or",  items=tuple(items))
def Not(arg: Term) -> Term:                 return Term("Not", arg=arg)
def Abs(arg: Term) -> Term:                 return Term("Abs", arg=arg)
def Neg(arg: Term) -> Term:                 return Term("Neg", arg=arg)
def Plus(items: tuple | list = ()) -> Term: return Term("Plus", items=tuple(items))
def Times(items: tuple | list = ()) -> Term:return Term("Times", items=tuple(items))
def Min(items: tuple | list = ()) -> Term:  return Term("Min", items=tuple(items))
def Max(items: tuple | list = ()) -> Term:  return Term("Max", items=tuple(items))


def Minus(a: Term, b: Term) -> Term:  return Term("Minus", a=a, b=b)
def Div(a: Term, b: Term) -> Term:    return Term("Div", a=a, b=b)
def Mod(a: Term, b: Term) -> Term:    return Term("Mod", a=a, b=b)
def Pow(a: Term, b: Term) -> Term:    return Term("Pow", a=a, b=b)
def Sqrt(arg: Term) -> Term:          return Term("Sqrt", arg=arg)
def Log(arg: Term) -> Term:           return Term("Log", arg=arg)   # ln(x); x<=0 -> -inf
def Exp(arg: Term) -> Term:           return Term("Exp", arg=arg)   # e**x (inverse of Log)

# Enigma recovery — hard graph-admissibility kernels. The candidate is a
# graph NodeID bound by a rule/filter variable; machine settings and crib
# data remain ordinary candidate attrs.
def EnigmaCrib(candidate: Term) -> Term:
    return Term("EnigmaCrib", candidate=candidate)
def EnigmaBombe(candidate: Term) -> Term:
    return Term("EnigmaBombe", candidate=candidate)
def EnigmaBombeWitness(candidate: Term) -> Term:
    return Term("EnigmaBombeWitness", candidate=candidate)

# Bitwise integer ops on i64. Shift counts outside [0, 63] yield 0
# (or -1 for Ashr on negative `a`) — matches the Div/Mod fallback
# convention. LLVM-shift-by-overshift = poison, this substrate's
# choice is silent-zero.
def BitAnd(a: Term, b: Term) -> Term: return Term("BitAnd", a=a, b=b)
def BitOr(a: Term, b: Term) -> Term:  return Term("BitOr",  a=a, b=b)
def BitXor(a: Term, b: Term) -> Term: return Term("BitXor", a=a, b=b)
def Shl(a: Term, b: Term) -> Term:    return Term("Shl",    a=a, b=b)
def Lshr(a: Term, b: Term) -> Term:   return Term("Lshr",   a=a, b=b)
def Ashr(a: Term, b: Term) -> Term:   return Term("Ashr",   a=a, b=b)

# Integer (truncating) signed division and remainder — matches Rust's
# wrapping_div / wrapping_rem (and C's `/`/`%`, LLVM's sdiv/srem).
# Divide-by-zero yields 0 (silent-zero convention). LLVM-style folding
# rules MUST gate on `rhs != 0` in their where-clause to preserve LLVM's
# undefined-behaviour semantics — the kernel's silent-zero is a
# substrate convention, not a license to introduce UB.
def IDiv(a: Term, b: Term) -> Term:   return Term("IDiv",   a=a, b=b)
def IRem(a: Term, b: Term) -> Term:   return Term("IRem",   a=a, b=b)

def IfThenElse(cond: Term, then: Term, other: Term) -> Term:
    return Term("IfThenElse", cond=cond, then=then, other=other)


# Vector / geometry — Python `Vec` is the constructor (named `Vec_` on
# the Rust side to avoid the std::vec clash).
def Vec(items: tuple | list = ()) -> Term: return Term("Vec", items=tuple(items))
def VecAdd(a: Term, b: Term) -> Term: return Term("VecAdd", a=a, b=b)
def VecSub(a: Term, b: Term) -> Term: return Term("VecSub", a=a, b=b)
def Dot(a: Term, b: Term) -> Term:    return Term("Dot", a=a, b=b)
def Magnitude(arg: Term) -> Term:     return Term("Magnitude", arg=arg)

def Sin(arg: Term) -> Term:           return Term("Sin", arg=arg)
def Cos(arg: Term) -> Term:           return Term("Cos", arg=arg)
def Atan2(y: Term, x: Term) -> Term:  return Term("Atan2", y=y, x=x)
def Bearing(arg: Term) -> Term:       return Term("Bearing", arg=arg)
def Rotate(vec: Term, angle: Term) -> Term: return Term("Rotate", vec=vec, angle=angle)
def AngleBetween(a: Term, b: Term) -> Term: return Term("AngleBetween", a=a, b=b)

# Render / surface / byte family.
def Surface(kind: str = "text", payload: Any = "") -> Term:
    return Term("Surface", kind=kind, payload=payload)
def Cat(items: tuple | list = ()) -> Term:   return Term("Cat", items=tuple(items))
def Lines(items: tuple | list = ()) -> Term: return Term("Lines", items=tuple(items))
def Bytes(items: tuple | list = ()) -> Term: return Term("Bytes", items=tuple(items))
def Slot(name: str = "") -> Term:            return Term("Slot", name=name)
def Label(prefix: str = "") -> Term:         return Term("Label", prefix=prefix)
def Join(separator: Term | None = None, items: Term | None = None) -> Term:
    return Term("Join", separator=separator, items=items)
def U8(expr: Term | None = None) -> Term:    return Term("U8", expr=expr)
def U16LE(expr: Term | None = None) -> Term: return Term("U16LE", expr=expr)
def U32LE(expr: Term | None = None) -> Term: return Term("U32LE", expr=expr)
def U64LE(expr: Term | None = None) -> Term: return Term("U64LE", expr=expr)
def LEB128(expr: Term | None = None) -> Term:return Term("LEB128", expr=expr)
def Let(name: str = "", value: Term | None = None, body: Term | None = None) -> Term:
    return Term("Let", name=name, value=value, body=body)
def Nth(items: Term | None = None, index: int = 0) -> Term:
    return Term("Nth", items=items, index=index)
def Render(term: Term | None = None, lang: Term | None = None) -> Term:
    return Term("Render", term=term, lang=lang)


# --- Grammar / Production / NodePattern ----------------------------------

@dataclasses.dataclass(frozen=True)
class NodePattern:
    """Matches a node by type and binds its NodeID to `var`."""
    type: str
    var: str

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "var": self.var}


@dataclasses.dataclass
class Production:
    """One Γ production. `weight` defaults to `Lit(1.0)` (paper §1
    Definition 2 — weights are always present)."""
    src: NodePattern
    edge_type: str
    tgt: NodePattern
    where: Term | None = None
    weight: Term | None = None
    provenance: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance": self.provenance,
            "src": self.src.to_dict(),
            "edge_type": self.edge_type,
            "tgt": self.tgt.to_dict(),
            "where": self.where.to_dict() if self.where is not None else None,
            "weight": self.weight.to_dict() if self.weight is not None else None,
        }


# --- Substrate ---------------------------------------------------------

class _TransactionCtx:
    """Context-manager facade so callers can use the Python `with
    substrate.transform()` shape. Buffered mutations on the native side;
    rollback by walking the inserted-list on exception.
    """

    def __init__(self, substrate: "Substrate"):
        self._s = substrate
        self._inserted_nodes: list[NodeID] = []
        self._inserted_edges: list[tuple[NodeID, str, NodeID]] = []

    def add_node(self, type: str, attrs: dict[str, Any] | None = None) -> NodeID:
        nid = self._s.add_node(type, attrs)
        self._inserted_nodes.append(nid)
        return nid

    def add_edge(self, src: NodeID, edge_type: str, tgt: NodeID, attrs: dict[str, Any] | None = None) -> None:
        self._s.add_edge(src, edge_type, tgt, attrs)
        self._inserted_edges.append((src, edge_type, tgt))

    def _rollback(self) -> None:
        for src, et, tgt in reversed(self._inserted_edges):
            self._s.remove_edge(src, et, tgt)
        for nid in reversed(self._inserted_nodes):
            self._s.remove_node(nid)


class SubstrateSnapshot:
    """Immutable reusable base with storage-independent branch creation."""

    def __init__(self, inner: _NativeSubstrateSnapshot, measurement_backend: str | None = None) -> None:
        self._inner = inner
        self._measurement_backend = measurement_backend

    @property
    def id(self) -> int:
        return self._inner.id

    @property
    def source_revision(self) -> tuple[int, int, int]:
        return self._inner.source_revision

    def fork(self) -> "Substrate":
        """Create an isolated mutable branch from this immutable base."""
        branch = Substrate()
        branch._inner = self._inner.fork()
        return branch


class Substrate:
    """Python wrapper around the native Substrate.

    Adds the `with substrate.transform()` context manager and tightens
    the Production / Term ingest path so callers don't have to drop to
    JSON dicts.
    """

    def __init__(self) -> None:
        self._inner = _NativeSubstrate()

    def snapshot(self) -> SubstrateSnapshot:
        """Capture an immutable base for storage-independent branch consumers."""
        return SubstrateSnapshot(self._inner.snapshot())

    def _snapshot_with_backend(self, backend: str) -> SubstrateSnapshot:
        """Backend-selecting hook for controlled measurements and diagnostics.

        Application consumers should use :meth:`snapshot`; keeping backend
        choice out of that API lets the implementation evolve independently.
        """
        return SubstrateSnapshot(self._inner._experiment_snapshot_with_backend(backend), backend)

    def fork_full_copy_experiment(self) -> "Substrate":
        """Return an isolated native deep-copy control for a thoughtexperiment.

        This is deliberately a full copy, not CoW. It refuses external or
        wrapper-owned state that cannot be copied safely.
        """
        branch = Substrate()
        branch._inner = self._inner.fork_full_copy_experiment()
        return branch

    def fork_shared_slab_experiment(self) -> "Substrate":
        """Return an isolated branch sharing only node/edge slab pages.

        All graph indexes and other substrate state remain eager copies; this
        backend measures the slab contribution independently of full CoW.
        """
        branch = Substrate()
        branch._inner = self._inner.fork_shared_slab_experiment()
        return branch

    def fork_shared_graph_pages_experiment(self) -> "Substrate":
        """Return an isolated branch sharing graph record and adjacency pages.

        Hash query indexes and other substrate state remain eager copies.
        """
        branch = Substrate()
        branch._inner = self._inner.fork_shared_graph_pages_experiment()
        return branch

    def set_experiment_edge_scope(self, node_ids: list[int], hops: int) -> int:
        """Filter branch edge reads through a sparse focus aperture.

        The inherited graph storage remains intact; future branch edges are
        visible through the same read view. This is intended for isolated
        thoughtexperiment branches only.
        """
        return self._inner.set_experiment_edge_scope(node_ids, hops)

    def replace_active_rule_by_name(self, name: str, variant: dict[str, Any] | None) -> bool:
        """Patch one active rule in an isolated branch without exporting all rules."""
        return self._inner.replace_active_rule_by_name(name, variant)

    def begin_experiment_delta_journal(self) -> None:
        """Begin sparse graph-delta capture for an isolated experiment."""
        self._inner.begin_experiment_delta_journal()

    def checkpoint_experiment_delta_journal(self) -> None:
        """Mark the injected-hypothesis state for derived-only readout."""
        self._inner.checkpoint_experiment_delta_journal()

    def finish_experiment_delta_journal(self) -> dict[str, Any]:
        """Return exact total and derived-only diffs from touched graph state."""
        return self._inner.finish_experiment_delta_journal()

    def assert_experiment_fork_safe(self) -> None:
        """Raise if wrapper/native state is unsafe to inherit across OS fork."""
        self._inner.assert_experiment_fork_safe()

    def experiment_graph_rule_revision(self) -> tuple[int, int, int]:
        """Return the O(1) tracked graph/Γ revision and rule-slot count."""
        return self._inner.experiment_graph_rule_revision()

    def rayon_current_num_threads(self) -> int:
        """Return the active global Rayon pool size for diagnostics."""
        return self._inner.rayon_current_num_threads()

    def apply_experiment_graph_delta(
        self, expected_revision: tuple[int, int, int], delta: dict[str, Any]
    ) -> None:
        """Atomically adopt a graph-diff residual against its exact base revision.

        Raises RuntimeError when the primary revision is stale or when the
        receipt conflicts with current graph contents. This is a structural
        merge primitive; callers must reground and authorize hypothetical
        conclusions before using it to change an authoritative live graph.
        """
        self._inner.apply_experiment_graph_delta(expected_revision, delta)

    # --- mutation ---

    def add_node(self, type: str, attrs: dict[str, Any] | None = None) -> NodeID:
        return self._inner.add_node(type, attrs)

    def add_edge(self, src: NodeID, edge_type: str, tgt: NodeID, attrs: dict[str, Any] | None = None) -> None:
        self._inner.add_edge(src, edge_type, tgt, attrs)

    def add_edge_unchecked(self, src: NodeID, edge_type: str, tgt: NodeID,
                            attrs: dict[str, Any] | None = None) -> None:
        """Skip grammar admissibility — used by the seed loader, which
        installs edges authorised by the seed's own productions rather
        than by what's currently registered in the live grammar."""
        self._inner.add_edge_unchecked(src, edge_type, tgt, attrs)

    def load_seed_manifest(self, manifest: dict,
                             root_node: NodeID | None = None) -> dict:
        """Apply a JSON-shaped seed manifest to this substrate. Native loader
        semantics use nodes, edges, productions, rules, reflexes, id,
        self_modification_patchable_rules, area, order, and latency_class;
        other top-level keys are ignored by the native loader.

        Allocates fresh global NodeIDs for the seed's nodes, resolves
        cross-references against the live graph, and registers the
        seed's productions on the Rust grammar.

        `root_node` binds the `{"role": "agent_root"}` cross-ref to a
        specific NodeID. Agents pass `agent.agent_root`; non-agent
        compositions (transcoding pipelines, subtitle generators, any
        graph-resident task) omit it — their manifests don't reference
        the role. The loader raises if a manifest's ref names a role
        with no binding.

        Returns a summary dict {nodes, edges, productions, id}."""
        return self._inner.load_seed_manifest(manifest, root_node)

    def remove_edge(self, src: NodeID, edge_type: str, tgt: NodeID) -> bool:
        return self._inner.remove_edge(src, edge_type, tgt)

    def remove_node(self, nid: NodeID) -> bool:
        return self._inner.remove_node(nid)

    def set_attr(self, nid: NodeID, key: str, value: Any) -> None:
        self._inner.set_attr(nid, key, value)

    def set_type(self, nid: NodeID, new_type: str) -> None:
        self._inner.set_type(nid, new_type)

    # --- bulk attribute access: ONE FFI crossing instead of N ---------------
    # Pure performance, no new capability. Exactly equivalent to the per-node
    # loops they replace (see the contract in `runners/dsl/src/py.rs`):
    #   get_attr_many(ns, k) == [node(n)["attrs"].get(k) for n in ns]
    #   set_attr_many(ns, k, v) == [set_attr(n, k, v) for n in ns]   (v uniform)
    #   set_attr_each(ns, k, vs) == [set_attr(n, k, v) for n, v in zip(ns, vs)]
    # A caller still decides WHICH nodes and WHAT value; only the LOOP is Rust.

    def set_attr_many(self, nids: list[NodeID], key: str, value: Any) -> None:
        self._inner.set_attr_many(nids, key, value)

    def set_attr_each(self, nids: list[NodeID], key: str, values: list[Any]) -> None:
        # Per-node-VALUE bulk write (the values DIFFER per node, so
        # set_attr_many's uniform value cannot express it). Byte-identical to
        # the per-node set_attr loop; see the contract in runners/dsl/src/py.rs.
        self._inner.set_attr_each(nids, key, values)

    # --- query ---

    def get_attr_many(self, nids: list[NodeID], key: str) -> list[Any]:
        return self._inner.get_attr_many(nids, key)

    def node(self, nid: NodeID) -> dict[str, Any]:
        return self._inner.node(nid)

    def has_node(self, nid: NodeID) -> bool:
        return self._inner.has_node(nid)

    def has_edge(self, src: NodeID, edge_type: str, tgt: NodeID) -> bool:
        return self._inner.has_edge(src, edge_type, tgt)

    def edge_attrs(self, src: NodeID, edge_type: str, tgt: NodeID) -> dict[str, Any] | None:
        """Return a copy of one edge's attributes, or None if the edge is absent."""
        result = self._inner.edge_attrs(src, edge_type, tgt)
        return None if result is None else dict(result)

    def incident_edges(self, nid: NodeID) -> list[dict[str, Any]]:
        """Return exact incoming/outgoing edge facts in O(degree(nid))."""
        return self._inner.incident_edges(nid)

    def nodes(self, type: str | None = None) -> list[NodeID]:
        return self._inner.nodes(type)

    def neighbours(self, nid: NodeID, edge_type: str | None = None) -> list[NodeID]:
        return self._inner.neighbours(nid, edge_type)

    def in_neighbours(self, nid: NodeID, edge_type: str | None = None) -> list[NodeID]:
        return self._inner.in_neighbours(nid, edge_type)

    def node_count(self) -> int:
        return self._inner.node_count()

    def next_live_node_id(self) -> int:
        """Return max live NodeID plus one for sparse experiment writeback."""
        return self._inner.next_live_node_id()

    def edge_count(self) -> int:
        return self._inner.edge_count()

    # --- Term + Grammar ---

    def evaluate(self, term: Term, env: dict[str, Any] | None = None) -> Any:
        return self._inner.evaluate(term._json, env)

    def add_production(self, prod: Production | dict[str, Any]) -> None:
        if isinstance(prod, Production):
            self._inner.add_production(prod.to_dict())
        else:
            self._inner.add_production(prod)

    def add_productions(self, prods: Iterable[Production]) -> None:
        for p in prods:
            self.add_production(p)

    def grammar_to_json(self) -> dict[str, Any]:
        return self._inner.grammar_to_json()

    # --- Shape (function_shape Mt) ---
    #
    # Thin world-adapter forwarders for the Rust Shape primitives
    # (runners/dsl/src/shape.rs, exposed via py.rs). No Python logic —
    # each is a one-line delegation to the native substrate so callers
    # using the wrapped `Substrate` reach the same primitive the native
    # object exposes. Without these forwarders `substrate.shape_of_term`
    # raised AttributeError on the wrapped object and the Shape-aware
    # transfer path in order_n_postulates / harvester_shape silently
    # no-opped (the `except Exception` swallowed it).

    def shape_of_term(self, term_json: dict[str, Any]) -> dict[str, Any]:
        """Return the three-axis Shape {recursion, order_n, abstraction}
        of a Term-tree (JSON encoding, same as evaluate)."""
        return self._inner.shape_of_term(term_json)

    def shapes_compatible(self, candidate: dict[str, Any],
                          target: dict[str, Any]) -> bool:
        """Does the candidate Shape structurally admit the target Shape?
        (shape_mismatch_prunes_negative_problem_space.)"""
        return self._inner.shapes_compatible(candidate, target)

    def add_shape_node_for_term(self, term_json: dict[str, Any]) -> NodeID:
        return self._inner.add_shape_node_for_term(term_json)

    def meta_shape(self, shape: dict[str, Any]) -> dict[str, Any]:
        return self._inner.meta_shape(shape)

    def set_shape_target(self, target: dict[str, Any] | None) -> None:
        self._inner.set_shape_target(target)

    def shape_pruned_count(self) -> int:
        return self._inner.shape_pruned_count()

    def reset_shape_counters(self) -> None:
        self._inner.reset_shape_counters()

    # --- agent tick: run all graph-resident Rule nodes to fixed point.
    # The unified-runtime entry point (CLAUDE.md): world adapters call
    # this after writing inbound events; rule matching + effect
    # application happens entirely in Rust.

    def tick(self, max_steps: int = 100_000, detect_cycles: bool = False) -> int:
        # `detect_cycles` defaults False — PROTOCOL §9: the new termination
        # semantics is OFF unless a caller asks, so every committed result
        # reproduces byte-identically. Mechanical pass-through; the decision
        # to enable it lives in the caller's params, never here.
        return self._inner.tick(max_steps, detect_cycles)

    def tick_graph_then_struct(self, max_steps: int = 100_000,
                               detect_cycles: bool = False) -> int:
        """Run graph-resident Rules, then the structural rewrite-rule store.

        This explicit plan is used by detached thoughtexperiments, where both
        rule stores must see the same counterfactual graph. Ordinary ``tick``
        retains its configured Default plan.
        """
        return self._inner.tick_graph_then_struct(max_steps, detect_cycles)

    def tick_with_rule_state_trace(
        self,
        watch_rule_names: list[str],
        watch_node_ids: list[int],
        watch_attrs: list[str],
        max_events: int = 10_000,
        max_steps: int = 100_000,
        detect_cycles: bool = False,
    ) -> dict[str, Any]:
        """Run the same native tick plan with bounded post-rule state samples.

        This is explicit diagnostic instrumentation. The observer records
        selected numeric graph attributes after each successful invocation of
        one of `watch_rule_names`; the ordinary `tick` path is unchanged.
        """
        return self._inner.tick_with_rule_state_trace(
            watch_rule_names, watch_node_ids, watch_attrs, max_events,
            max_steps, detect_cycles,
        )

    def wave_stencil_tick(self, max_steps: int = 200_000,
                          run_rest: bool = True) -> bool:
        """ADMISSIBLE vectorized stencil fast path (block 134000). Returns True
        iff the RetinaCell state dynamics are the recognised uniform local
        stencil and were applied in one vectorized pass (⇒ do NOT also call
        `tick`); False iff inadmissible (⇒ fall back to `tick`). Mechanical
        pass-through — the routing DECISION is the Rust admissibility gate."""
        return self._inner.wave_stencil_tick(max_steps, run_rest)

    # --- autonomous agent loop -----------------------------------------
    #
    # The agent runs as a Rust thread holding an Arc clone of the
    # inner substrate. World adapters keep writing to the same
    # substrate through this Python wrapper; their writes acquire the
    # same mutex briefly. Tick + write are NOT synchronised through a
    # central scheduler — they contend on the inner-state mutex for
    # microseconds each, and otherwise run independently.
    #
    # This is the "long-running agent + hot-pluggable worlds" shape:
    # the agent's loop never has to ask the world for permission to
    # think; the world never has to ask the agent for permission to
    # speak. Worlds can attach, write events, detach — the agent's
    # loop is oblivious to that lifecycle.

    def start_agent(self,
                    tick_rate_hz: float = 10.0,
                    n_runners: int = 1,
                    n_threads_per_runner: int = 1,
                    max_steps_per_tick: int = 100_000) -> None:
        """Start the agent. Spawns a Rust thread that ticks the
        substrate at `tick_rate_hz` Hz. World adapters can write
        concurrently — they only contend with the tick at the inner
        mutex, which is held for microseconds per operation.

        Exactly one live-graph runner is allowed. ``n_threads_per_runner``
        sizes the native pure CognitiveTask workers; their typed results
        commit through one deterministic serial fold. ``n_runners != 1``
        fails closed because multiple graph writers remain forbidden.

        `max_steps_per_tick`: hard cap on rule applications per
        tick. The runtime stops a tick at fixed point regardless;
        the cap protects against pathological loops.
        """
        self._inner.start_agent(
            tick_rate_hz, n_runners, n_threads_per_runner,
            max_steps_per_tick)

    def stop_agent(self, timeout: float = 1.0) -> None:
        """Stop the agent's background tick thread. The Rust side
        joins the thread; `timeout` is accepted for API parity with
        the previous Python implementation but is ignored — the
        thread exits at the boundary of its next tick (microseconds
        to milliseconds depending on rule-set size)."""
        self._inner.stop_agent()

    def agent_running(self) -> bool:
        """True iff the Rust tick thread is currently running."""
        return self._inner.agent_running()

    # --- admissibility probes ---

    def is_edge_admissible(
        self,
        src: NodeID,
        edge_type: str,
        candidate_tgt_type: str,
        candidate_tgt_attrs: dict[str, Any] | None = None,
    ) -> bool:
        return self._inner.is_edge_admissible(src, edge_type, candidate_tgt_type, candidate_tgt_attrs)

    def admissible_edges_from(
        self, src: NodeID, edge_type: str, candidates: Iterable[NodeID]
    ) -> list[NodeID]:
        return self._inner.admissible_edges_from(src, edge_type, list(candidates))

    def admissible_moves(
        self,
        src: NodeID,
        edge_type: str,
        candidates: Iterable[tuple[str, dict[str, Any] | None]],
    ) -> list[tuple[str, dict[str, Any], float]]:
        return self._inner.admissible_moves(src, edge_type, list(candidates))

    def define_concept(self, name: str, def_term: Term) -> None:
        self._inner.define_concept(name, def_term._json)

    # --- transaction (context manager) ---

    def transform(self):
        substrate = self
        ctx = _TransactionCtx(substrate)
        class _Wrapper:
            def __enter__(self_w):
                return ctx
            def __exit__(self_w, exc_type, exc, tb):
                if exc is not None:
                    ctx._rollback()
                return False
        return _Wrapper()

    # --- persistence ---

    def graph_to_dict(self) -> dict[str, Any]:
        return self._inner.graph_to_dict()

    def graph_from_dict(self, d: dict[str, Any]) -> None:
        self._inner.graph_from_dict(d)

    # --- memory faculty (keep/forget/index decision lives in Rust) ---
    # Thin delegations to the native faculty; no Python decision logic.

    def memory_bound(self, budget_nodes: int = 5000,
                     budget_bytes: int = 64 * 1024 * 1024,
                     hot_window: int = 3) -> None:
        self._inner.memory_bound(budget_nodes, budget_bytes, hot_window)

    def memory_set_hot_window(self, hot_window: int) -> None:
        self._inner.memory_set_hot_window(hot_window)

    def memory_forget_over_budget(self) -> dict[str, int]:
        return self._inner.memory_forget_over_budget()

    def memory_observe_and_bound(self) -> dict[str, Any]:
        return self._inner.memory_observe_and_bound()

    def memory_total_bytes(self) -> int:
        return self._inner.memory_total_bytes()

    def memory_value_report(self) -> list[dict[str, Any]]:
        """The agent's own value-for-compute verdict per resident node type
        (sorted ascending by keep_value_per_byte = its forget order). Each
        dict: type, count, bytes, keep_value, keep_value_per_byte,
        miss_penalty, non_rebuildability, never_forget, saturating, tier."""
        return self._inner.memory_value_report()

    @staticmethod
    def value_tier(type_name: str) -> str:
        """The memory tier the agent assigns a type: 'keep' / 'working' /
        'disposable' (echoic sensory scratch — dropped eagerly, never kept)."""
        return _NativeSubstrate.value_tier(type_name)

    def memory_forget_type(self, type_name: str) -> int:
        """Forget all nodes of a named type at a consolidation boundary, leaving
        a compressed MemorySummary. Returns the number forgotten."""
        return self._inner.memory_forget_type(type_name)

    def memory_disposable_capacity(self, bytes: int, nodes: int) -> None:
        """Set the disposable circular-buffer capacity (the sensory-register
        span): byte bound (primary) + node-count safety bound."""
        self._inner.memory_disposable_capacity(bytes, nodes)

    def memory_roll_disposable(self) -> dict[str, int]:
        """Roll the sensory register (disposable tier as a CIRCULAR BUFFER):
        admit new disposable nodes, evict oldest past capacity. A rolling
        window of recent raw input across ticks, not a flush. Call each tick."""
        return self._inner.memory_roll_disposable()

    def memory_drop_disposable(self) -> dict[str, int]:
        """Eager FULL flush: drop every disposable-tier node now. Unconditional;
        clears the ring. Prefer memory_roll_disposable for the rolling window."""
        return self._inner.memory_drop_disposable()

    def memory_consolidate(self, store_dir: str, key: str, nid, round_no: int,
                           cat_vec, leaf_vec) -> str:
        return self._inner.memory_consolidate(store_dir, key, nid, round_no,
                                              list(cat_vec), list(leaf_vec))

    def memory_index_disk_record(self, key: str, path: str, round_no: int,
                                 cat_vec, leaf_vec) -> str:
        return self._inner.memory_index_disk_record(key, path, round_no,
                                                    list(cat_vec), list(leaf_vec))

    def memory_unindex_disk_record(self, key: str) -> None:
        self._inner.memory_unindex_disk_record(key)

    def memory_recall_by_key(self, key: str, round_no: int):
        return self._inner.memory_recall_by_key(key, round_no)

    def memory_shuffle(self, round_no: int) -> list[str]:
        return self._inner.memory_shuffle(round_no)

    def memory_recall_by_shape(self, cat_vec, leaf_vec, round_no: int):
        return self._inner.memory_recall_by_shape(list(cat_vec), list(leaf_vec),
                                                  round_no)

    def memory_index_clusters(self) -> int:
        return self._inner.memory_index_clusters()

    def memory_subsystem(self):
        return self._inner.memory_subsystem()

    @staticmethod
    def shape_salience(seq) -> float:
        """ORDER-N SHAPE SALIENCE — the agent's GENERAL salience operator
        over ANY trajectory's order-N shape (growth / pitch / rhythm /
        motion). High for a DIRECTED, RESOLVING build->peak (the "tada");
        low for a FLAT or RANDOM trajectory. Composes the held order_n
        (velocity + curvature) and relational_shape (ordinal rank of the
        resolution) operators, native in Rust, no ML. This is the SAME
        operator memory's keep_value uses for tiering — one salience for
        both memory AND perception. A world adapter (audio/video front-end)
        extracts the trajectory; the salience itself lives in the runtime."""
        return _NativeSubstrate.shape_salience([float(v) for v in seq])

    @staticmethod
    def shape_signature(seq):
        """The order-N shape SIGNATURE of a trajectory — its relational-shape
        ordinal-rank key (gain/level-invariant). Two clips that share the
        order-N SHAPE but differ in every surface way (timbre, instrument,
        loudness) get NEIGHBOURING signatures. Returns a list of int ranks."""
        return _NativeSubstrate.shape_signature([float(v) for v in seq])

    @staticmethod
    def shape_signature_distance(a, b) -> int:
        """L1 distance between two shape signatures — the shape-neighbour
        metric. Close => same order-N shape regardless of surface."""
        return _NativeSubstrate.shape_signature_distance(
            [int(v) for v in a], [int(v) for v in b])

    @staticmethod
    def foreground(frame, background):
        """VISION FOREGROUND (object isolation): elementwise |frame - background|.
        The named object is what deviates from the persistent background; this
        suppresses the constant presenter/set so the cue is the object. Held op."""
        f = frame.tolist() if hasattr(frame, "tolist") else [float(v) for v in frame]
        b = (background.tolist() if hasattr(background, "tolist")
             else [float(v) for v in background])
        return _NativeSubstrate.foreground(f, b)

    @staticmethod
    def ema_blend(background, frame, alpha):
        """EMA background update: elementwise background*(1-alpha)+frame*alpha —
        the running background model the foreground op subtracts. Held op."""
        b = (background.tolist() if hasattr(background, "tolist")
             else [float(v) for v in background])
        f = frame.tolist() if hasattr(frame, "tolist") else [float(v) for v in frame]
        return _NativeSubstrate.ema_blend(b, f, float(alpha))

    @staticmethod
    def shape_neighbour_threshold(n: int) -> int:
        """The scale-derived shape-neighbour threshold for a length-n
        signature (set from the rank scale, NOT tuned to an answer)."""
        return _NativeSubstrate.shape_neighbour_threshold(int(n))

    def declare_shares_shape(self) -> None:
        """Declare the `shares_shape` edge type admissible in Γ:
        (SalientShape) -[shares_shape]-> (SalientShape). ONE edge type added
        to the grammar; existing edge types untouched."""
        self._inner.declare_shares_shape()

    def add_salient_shape(self, label: str, signature):
        """Add a SalientShape NODE carrying a clip/event's order-N shape
        signature, then WIRE `shares_shape` edges to existing SalientShape
        nodes that are shape-NEIGHBOURS. Returns (node_id, [(neighbour_id,
        distance), ...])."""
        return self._inner.add_salient_shape(label, [int(v) for v in signature])

    def spread(self, cue: NodeID, max_hops: int = 2):
        """SPREADING-ACTIVATION recall from a cue node — traverse MULTIPLE
        edge types (shares_shape + co-occurrence + ...) up to max_hops.
        Returns [(node_id, edge_type_name, hop), ...]. NOT a single-key
        lookup."""
        return self._inner.spread(cue, max_hops)

    def declare_relation_edge(self, edge_type: str, provenance: str = ""):
        """Declare ONE multi-relational edge type admissible in Γ:
        (SalientShape) -[edge_type]-> (SalientShape). Used for the timbre /
        affect / function relations alongside shares_shape."""
        self._inner.declare_relation_edge(edge_type, provenance)

    def wire_relation(self, node: NodeID, edge_type: str, sig_attr: str,
                      signature, provenance: str = ""):
        """Attach a relation SIGNATURE (under sig_attr) to an EXISTING
        SalientShape node, then WIRE `edge_type` edges to other SalientShape
        nodes within the scale-derived threshold. The SAME node carries many
        relation signatures (shape, timbre, affect, function), each its own
        attr + edge. Returns [(neighbour_id, distance), ...]."""
        return self._inner.wire_relation(
            node, edge_type, sig_attr, [int(v) for v in signature], provenance)

    # --- PER-RELATION METRICS (affect: normalised L2; function: categorical)

    @staticmethod
    def affect_normalize(vectors):
        """PER-FEATURE z-score normalisation of a population of affect vectors,
        returned as fixed-point milli-z ints (z * 1000). Makes heterogeneous-
        unit features comparable before L2. Mechanical mean/std, no fit."""
        return _NativeSubstrate.affect_normalize(
            [[float(v) for v in row] for row in vectors])

    @staticmethod
    def l2_signature_distance(a, b) -> int:
        """L2 (Euclidean) distance between two normalised affect signatures —
        the proper affect-neighbour metric."""
        return _NativeSubstrate.l2_signature_distance(
            [int(v) for v in a], [int(v) for v in b])

    @staticmethod
    def affect_neighbour_threshold(n: int) -> int:
        """The scale-derived affect-neighbour threshold (sqrt(n)*1000 milli-z =
        ~1 std per feature). NOT tuned."""
        return _NativeSubstrate.affect_neighbour_threshold(int(n))

    @staticmethod
    def categorical_signature_distance(a, b) -> int:
        """CATEGORICAL (Hamming) distance between two bucketed role
        signatures — the proper function-neighbour metric."""
        return _NativeSubstrate.categorical_signature_distance(
            [int(v) for v in a], [int(v) for v in b])

    @staticmethod
    def categorical_neighbour_threshold(n: int) -> int:
        """The function-neighbour threshold (categorical match: Hamming<=1 =
        distance<2). NOT tuned."""
        return _NativeSubstrate.categorical_neighbour_threshold(int(n))

    def wire_relation_affect(self, nodes, edge_type: str, sig_attr: str,
                             raw, provenance: str = ""):
        """AFFECT relation wiring with the PROPER metric: per-feature normalised
        L2 (NOT ordinal rank). `nodes` parallel to `raw` (the RAW heterogeneous
        affect vectors). Normalises each feature across the population in the
        core, wires pairs within the scale-derived affect threshold. Returns,
        per node index, [(neighbour_id, distance), ...]."""
        return self._inner.wire_relation_affect(
            list(nodes), edge_type, sig_attr,
            [[float(v) for v in row] for row in raw], provenance)

    def wire_relation_categorical(self, node: NodeID, edge_type: str,
                                  sig_attr: str, signature, provenance: str = ""):
        """FUNCTION relation wiring with the PROPER metric: CATEGORICAL
        (Hamming) match on the bucketed role vector (NOT ordinal rank). Wires
        to other nodes whose role category matches within Hamming<=1. Returns
        [(neighbour_id, distance), ...]."""
        return self._inner.wire_relation_categorical(
            node, edge_type, sig_attr, [int(v) for v in signature], provenance)


# --- top-level codec ----------------------------------------------------

def humanoid_cost_terms() -> dict:
    """The nine per-term contributions of the last humanoid plan scored.

    OBSERVABILITY ONLY -- a mechanical read of a thread-local the Rust
    composer writes; nothing reads it back into a decision and the cost sum
    is byte-identical with or without it. Pays the contribution-reporting
    debt registered in CONTACT_WRENCH_PREREG.md.
    """
    return _native.humanoid_cost_terms()


def encode(value: Any) -> Any:
    """Encode a Python value to the substrate's JSON-tagged form.
    Same wire format as `substrate.persistence.encode`."""
    return _native.encode(value)


def decode(value: Any) -> Any:
    """Inverse of `encode`."""
    return _native.decode(value)


__all__ = [
    "humanoid_cost_terms",
    # core
    "NodeID", "Substrate", "SubstrateSnapshot", "Term", "Production", "NodePattern",
    "InadmissibleEdge", "version", "encode", "decode",
    # Term factories
    "Var", "Lit", "TypeOf", "Attr", "SetT", "In",
    "Eq", "Lt", "Lte", "Gt", "Gte",
    "Neighbours", "InNeighbours", "MapNeighbours",
    "Count", "Filter", "Exists", "Sum", "Prod", "MinOver", "MaxOver", "Pick",
    "Holds",
    "EvalSubgraph",
    "Argmax",
    "Argmin",
    "BitsAt", "BitsAtAll", "BitsWrite", "BitsWriteAll",
    "HuffmanDecodeStream", "HuffmanEncodeStream",
    "ExpGolombDecode", "ExpGolombDecodeSigned",
    "ExpGolombEncode", "ExpGolombEncodeSigned",
    "And", "Or", "Not",
    "Abs", "Neg", "Plus", "Minus", "Times", "Div", "Mod", "Pow", "Sqrt", "Log", "Exp", "Min", "Max",
    "EnigmaCrib", "EnigmaBombe", "EnigmaBombeWitness",
    "BitAnd", "BitOr", "BitXor", "Shl", "Lshr", "Ashr", "IDiv", "IRem",
    "IfThenElse",
    "Vec", "VecAdd", "VecSub", "Dot", "Magnitude",
    "Sin", "Cos", "Atan2", "Bearing", "Rotate", "AngleBetween",
    "Surface", "Cat", "Lines", "Bytes", "Slot", "Label", "Join",
    "U8", "U16LE", "U32LE", "U64LE", "LEB128",
    "Let", "Nth", "Render",
]
