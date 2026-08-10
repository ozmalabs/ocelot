"""LLVM pass compiler — concise transformation-rule spec → substrate
RewriteRule dict, and the end-to-end install + run-rules + verify loop
on a hand-built IR fragment.

The constfold_add fixture below is the design's first concrete pass.
The end-to-end test:
  1. spins up a native substrate with an open grammar
  2. builds an LLVM IR fragment representing `%r = add i32 3, 5`
  3. installs constfold_add via the compiler module
  4. runs the rule engine
  5. asserts the add was rewritten to a constant 8

If the substrate's native binding is missing `add_rule` (a stale
wheel), the end-to-end test skips with a clear message. The unit
tests of the compiler are pure Python and always run.
"""
from __future__ import annotations

import pytest

from domains.llvm_pass_compiler import (
    compile_attr_term, compile_effect, compile_rule, compile_where,
    install_passes_seed, install_transformation_rule, load_passes_seed,
    term_to_json,
)


_REPO_ROOT = __file__.rsplit("/tests/", 1)[0]
_SEED_PATH = f"{_REPO_ROOT}/seeds/llvm_passes.json"


# ---------------------------------------------------------------------------
# The fixture — the first transformation rule the agent ingests.
# ---------------------------------------------------------------------------

CONSTFOLD_ADD = {
    "kind": "transformation",
    "name": "constfold_add",
    "doc": "add(c1, c2) where both are integer constants → fold to c1+c2.",
    # Drive matching from the instruction's operand edges. Both must be
    # constants — checked in the where-clause.
    "match": [
        ["?inst", "uses_op0", "?v1"],
        ["?inst", "uses_op1", "?v2"],
        ["?inst", "produces", "?old"],
    ],
    "where": {
        "all": [
            {"type_of": "?inst", "is": "LLVMInstruction"},
            {"attr": ["?inst", "opcode"], "eq": "add"},
            {"type_of": "?v1", "is": "LLVMConstant"},
            {"type_of": "?v2", "is": "LLVMConstant"},
        ]
    },
    "effect": [
        # Materialise the new constant with value = v1.value + v2.value
        # and the same type as v1.
        {"add_node": {
            "var": "?new_const",
            "type": "LLVMConstant",
            "attrs": {
                "value": {"add": [
                    {"attr": ["?v1", "value"]},
                    {"attr": ["?v2", "value"]},
                ]},
                "type": {"attr": ["?v1", "type"]},
            },
        }},
        # Every user of the old result now uses the new constant.
        {"replace_value": {"old": "?old", "new": "?new_const"}},
        # Delete the now-unused add instruction.
        {"delete": "?inst"},
    ],
}


# ---------------------------------------------------------------------------
# Unit tests — compile_* in isolation.
# ---------------------------------------------------------------------------

def test_compile_where_typeof_eq():
    spec = {"type_of": "?x", "is": "LLVMInstruction"}
    t = compile_where(spec)
    j = term_to_json(t)
    assert j["type"] == "Eq"
    assert j["a"]["type"] == "TypeOf"
    assert j["a"]["node"]["type"] == "Var"
    assert j["a"]["node"]["name"] == "x"
    assert j["b"]["type"] == "Lit"
    assert j["b"]["value"] == "LLVMInstruction"


def test_compile_where_attr_eq():
    spec = {"attr": ["?inst", "opcode"], "eq": "add"}
    t = compile_where(spec)
    j = term_to_json(t)
    assert j["type"] == "Eq"
    assert j["a"]["type"] == "Attr"
    assert j["a"]["key"] == "opcode"
    assert j["a"]["node"]["name"] == "inst"
    assert j["b"]["value"] == "add"


def test_compile_where_all_combines_with_and():
    spec = {"all": [
        {"type_of": "?x", "is": "T"},
        {"attr": ["?x", "k"], "eq": 1},
    ]}
    t = compile_where(spec)
    j = term_to_json(t)
    assert j["type"] == "And"
    assert len(j["items"]) == 2


def test_compile_attr_term_arithmetic():
    spec = {"add": [
        {"attr": ["?a", "value"]},
        {"attr": ["?b", "value"]},
    ]}
    t = compile_attr_term(spec)
    j = term_to_json(t)
    assert j["type"] == "Plus"
    assert len(j["items"]) == 2
    assert all(i["type"] == "Attr" for i in j["items"])


def test_compile_effect_replace_value():
    spec = {"replace_value": {"old": "?old", "new": "?new"}}
    e = compile_effect(spec)
    assert e == ["replace_value", "old", "new"]


def test_compile_effect_add_node_with_computed_attrs():
    spec = {"add_node": {
        "var": "?c",
        "type": "LLVMConstant",
        "attrs": {
            "value": {"add": [{"attr": ["?v1", "value"]},
                              {"attr": ["?v2", "value"]}]},
            "type": "i32",
        },
    }}
    e = compile_effect(spec)
    assert e[0] == "add_node"
    assert e[1] == "c"
    assert e[2] == "LLVMConstant"
    attrs = e[3]
    # Computed value wrapped in __term__
    assert "__term__" in attrs["value"]
    assert attrs["value"]["__term__"]["type"] == "Plus"
    # Literal value passes through
    assert attrs["type"] == "i32"


def test_compile_effect_delete():
    assert compile_effect({"delete": "?x"}) == ["del_node", "x"]
    assert compile_effect({"del_node": "?x"}) == ["del_node", "x"]


def test_compile_effect_add_edge_with_attrs():
    spec = {"add_edge": ["?a", "uses", "?b"], "attrs": {"weight": 1.5}}
    e = compile_effect(spec)
    assert e == ["add_edge", "a", "uses", "b", {"weight": 1.5}]


def test_compile_rule_assembles_all_pieces():
    spec = {
        "kind": "transformation",
        "name": "demo",
        "match": [["?x", "edge", "?y"]],
        "where": {"type_of": "?x", "is": "T"},
        "effect": [{"delete": "?x"}],
    }
    rule = compile_rule(spec)
    assert rule["name"] == "demo"
    assert rule["match"] == [["x", "edge", "y"]]
    assert rule["where"]["type"] == "Eq"
    assert rule["effects"] == [["del_node", "x"]]


def test_compile_rule_rejects_non_transformation_kind():
    with pytest.raises(ValueError, match="only 'transformation' kind"):
        compile_rule({"kind": "analysis", "name": "x"})


# ---------------------------------------------------------------------------
# constfold_add — verify the fixture itself compiles cleanly.
# ---------------------------------------------------------------------------

def test_constfold_add_compiles():
    rule = compile_rule(CONSTFOLD_ADD)
    assert rule["name"] == "constfold_add"
    # 3 match-edges (operands + produces)
    assert len(rule["match"]) == 3
    assert rule["match"][0] == ["inst", "uses_op0", "v1"]
    assert rule["match"][1] == ["inst", "uses_op1", "v2"]
    assert rule["match"][2] == ["inst", "produces", "old"]
    # where is a 4-way And
    assert rule["where"]["type"] == "And"
    assert len(rule["where"]["items"]) == 4
    # 3 effects: add the new constant, replace uses, delete the inst
    assert len(rule["effects"]) == 3
    assert rule["effects"][0][0] == "add_node"
    assert rule["effects"][0][2] == "LLVMConstant"
    assert rule["effects"][1] == ["replace_value", "old", "new_const"]
    assert rule["effects"][2] == ["del_node", "inst"]


# ---------------------------------------------------------------------------
# End-to-end — install constfold_add into a native substrate, build an
# IR fragment, run rules, verify the add was folded.
# ---------------------------------------------------------------------------

def _native_substrate_with_add_rule():
    """Return a fresh _native.Substrate if the build has the rule API,
    else None (signals the e2e test to skip)."""
    try:
        from substrate_rs import _native
    except ImportError:
        return None
    if not hasattr(_native.Substrate, "add_rule"):
        return None
    return _native.Substrate()


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_constfold_add_folds_an_add_instruction():
    """The end-to-end loop: install constfold_add, build IR for
    `%r = add i32 3, 5`, run rules, assert the result is a constant 8
    and the add is gone."""
    from substrate_rs import _native

    s = _native.Substrate()

    # Open the grammar for every (LLVM*, edge, LLVM*) triple the rule
    # touches. Production weights default to 1.0 — we just need
    # admissibility.
    types = ["LLVMInstruction", "LLVMConstant", "LLVMValue"]
    edge_types = ["uses_op0", "uses_op1", "uses_op2", "produces"]
    for src_t in types:
        for tgt_t in types:
            for et in edge_types:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })

    # IR: %r = add i32 3, 5
    c3 = s.add_node("LLVMConstant", {"value": 3, "type": "i32"})
    c5 = s.add_node("LLVMConstant", {"value": 5, "type": "i32"})
    inst = s.add_node("LLVMInstruction", {"opcode": "add"})
    result = s.add_node("LLVMValue", {"type": "i32"})
    # A downstream "user" instruction so we can verify replace_value
    # rewires it.
    user = s.add_node("LLVMInstruction", {"opcode": "ret"})

    s.add_edge(inst, "uses_op0", c3, {})
    s.add_edge(inst, "uses_op1", c5, {})
    s.add_edge(inst, "produces", result, {})
    s.add_edge(user, "uses_op0", result, {})

    # Install constfold_add.
    install_transformation_rule(s, CONSTFOLD_ADD)

    # Run rules to fixed point.
    s.run_rules(100)

    # The add instruction is gone (it had no other uses).
    assert not s.has_node(inst), "add instruction should be deleted"

    # The user instruction now references a NEW constant (not the old
    # result). Find it.
    user_operands = s.neighbours(user, "uses_op0")
    assert len(user_operands) == 1, \
        f"user should have one uses_op0; got {user_operands}"
    new_target = user_operands[0]
    new_attrs = s.node(new_target)["attrs"]
    assert new_attrs.get("value") == 8, \
        f"new target should be a constant 8; got {new_attrs}"


# ---------------------------------------------------------------------------
# JSON-seed loading — the agent-facing path.
# ---------------------------------------------------------------------------

def test_passes_seed_loads_from_disk():
    """The seed file at seeds/llvm_passes.json parses + names the
    expected passes."""
    manifest = load_passes_seed(_SEED_PATH)
    assert manifest["id"] == "llvm_passes"
    assert manifest["depends_on"] == ["llvm_ir"]
    assert isinstance(manifest["passes"], list)
    assert len(manifest["passes"]) >= 1
    names = {p["name"] for p in manifest["passes"]}
    assert "constfold_add" in names


def test_passes_seed_constfold_compiles():
    """Every pass in the seed compiles cleanly via the standard pipeline."""
    manifest = load_passes_seed(_SEED_PATH)
    for pass_spec in manifest["passes"]:
        rule = compile_rule(pass_spec)
        assert rule["name"] == pass_spec["name"]
        assert isinstance(rule["match"], list)
        assert isinstance(rule["effects"], list)


def test_passes_seed_rejects_missing_passes_key(tmp_path):
    """A manifest without 'passes' is rejected with a clear message."""
    bad = tmp_path / "bad.json"
    bad.write_text('{"id": "bad", "version": "1.0.0"}')
    with pytest.raises(ValueError, match="missing 'passes' key"):
        load_passes_seed(bad)


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_install_passes_seed_end_to_end_folds_an_add():
    """Load the seed from disk → install every pass into a fresh
    substrate → build %r = add i32 3, 5 → run rules → assert fold."""
    from substrate_rs import _native

    s = _native.Substrate()

    # Same open-grammar setup as the in-line e2e test.
    types = ["LLVMInstruction", "LLVMConstant", "LLVMValue"]
    edge_types = ["uses_op0", "uses_op1", "uses_op2", "produces"]
    for src_t in types:
        for tgt_t in types:
            for et in edge_types:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })

    # Install passes FROM DISK — the JSON-loadable path.
    rule_idxs = install_passes_seed(s, _SEED_PATH)
    assert len(rule_idxs) >= 1, "at least constfold_add should install"

    # Build IR.
    c3 = s.add_node("LLVMConstant", {"value": 3, "type": "i32"})
    c5 = s.add_node("LLVMConstant", {"value": 5, "type": "i32"})
    inst = s.add_node("LLVMInstruction", {"opcode": "add"})
    result = s.add_node("LLVMValue", {"type": "i32"})
    user = s.add_node("LLVMInstruction", {"opcode": "ret"})
    s.add_edge(inst, "uses_op0", c3, {})
    s.add_edge(inst, "uses_op1", c5, {})
    s.add_edge(inst, "produces", result, {})
    s.add_edge(user, "uses_op0", result, {})

    s.run_rules(100)

    # Same assertions as the in-line variant.
    assert not s.has_node(inst)
    user_operands = s.neighbours(user, "uses_op0")
    assert len(user_operands) == 1
    new_target = user_operands[0]
    assert s.node(new_target)["attrs"].get("value") == 8


# ---------------------------------------------------------------------------
# Per-pass integration tests — verify each pass in the seed actually
# does the right rewrite on a representative IR fragment.
# ---------------------------------------------------------------------------

def _make_open_substrate_with_passes():
    """Helper: fresh substrate with open grammar + every pass from the
    on-disk seed installed. Returns (substrate, rule_idxs)."""
    from substrate_rs import _native
    s = _native.Substrate()
    types = ["LLVMInstruction", "LLVMConstant", "LLVMValue"]
    edge_types = ["uses_op0", "uses_op1", "uses_op2", "produces"]
    for src_t in types:
        for tgt_t in types:
            for et in edge_types:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    rule_idxs = install_passes_seed(s, _SEED_PATH)
    return s, rule_idxs


def _build_binop(s, opcode: str, lhs: int, rhs: int, *,
                 lhs_is_const: bool = True, rhs_is_const: bool = True):
    """Build an LLVM binop instruction with the given operands. Returns
    (inst_id, lhs_id, rhs_id, result_id, user_id). `lhs`/`rhs` are the
    integer constant values when *_is_const; when False they're built as
    LLVMValue (typed but not constant) and the integer is unused."""
    if lhs_is_const:
        lhs_id = s.add_node("LLVMConstant", {"value": lhs, "type": "i32"})
    else:
        lhs_id = s.add_node("LLVMValue", {"type": "i32"})
    if rhs_is_const:
        rhs_id = s.add_node("LLVMConstant", {"value": rhs, "type": "i32"})
    else:
        rhs_id = s.add_node("LLVMValue", {"type": "i32"})
    inst = s.add_node("LLVMInstruction", {"opcode": opcode})
    result = s.add_node("LLVMValue", {"type": "i32"})
    user = s.add_node("LLVMInstruction", {"opcode": "ret"})
    s.add_edge(inst, "uses_op0", lhs_id, {})
    s.add_edge(inst, "uses_op1", rhs_id, {})
    s.add_edge(inst, "produces", result, {})
    s.add_edge(user, "uses_op0", result, {})
    return inst, lhs_id, rhs_id, result, user


def _user_op0_value(s, user):
    """The operand-0 target of `user`'s instruction — what the binop's
    result was rewired to (or the original result if no fold)."""
    ops = s.neighbours(user, "uses_op0")
    assert len(ops) == 1, f"user should have exactly one op0; got {ops}"
    return ops[0]


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_constfold_sub_folds_to_difference():
    s, _ = _make_open_substrate_with_passes()
    inst, _, _, _, user = _build_binop(s, "sub", 10, 3)
    s.run_rules(100)
    assert not s.has_node(inst), "sub instruction should be folded away"
    new_target = _user_op0_value(s, user)
    assert s.node(new_target)["attrs"].get("value") == 7


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_constfold_mul_folds_to_product():
    s, _ = _make_open_substrate_with_passes()
    inst, _, _, _, user = _build_binop(s, "mul", 4, 7)
    s.run_rules(100)
    assert not s.has_node(inst), "mul instruction should be folded away"
    new_target = _user_op0_value(s, user)
    assert s.node(new_target)["attrs"].get("value") == 28


# --- bitwise constant folds ----------------------------------------------

@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_constfold_and_folds_to_bitwise_and():
    s, _ = _make_open_substrate_with_passes()
    inst, _, _, _, user = _build_binop(s, "and", 0xF0, 0xCC)
    s.run_rules(100)
    assert not s.has_node(inst), "and should fold"
    assert s.node(_user_op0_value(s, user))["attrs"].get("value") == 0xC0


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_constfold_or_folds_to_bitwise_or():
    s, _ = _make_open_substrate_with_passes()
    inst, _, _, _, user = _build_binop(s, "or", 0xF0, 0x0C)
    s.run_rules(100)
    assert not s.has_node(inst), "or should fold"
    assert s.node(_user_op0_value(s, user))["attrs"].get("value") == 0xFC


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_constfold_xor_folds_to_bitwise_xor():
    s, _ = _make_open_substrate_with_passes()
    inst, _, _, _, user = _build_binop(s, "xor", 0xFF, 0x0F)
    s.run_rules(100)
    assert not s.has_node(inst), "xor should fold"
    assert s.node(_user_op0_value(s, user))["attrs"].get("value") == 0xF0


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_constfold_shl_folds_to_shift_left():
    s, _ = _make_open_substrate_with_passes()
    inst, _, _, _, user = _build_binop(s, "shl", 3, 4)  # 3 << 4 = 48
    s.run_rules(100)
    assert not s.has_node(inst), "shl should fold"
    assert s.node(_user_op0_value(s, user))["attrs"].get("value") == 48


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_constfold_lshr_folds_to_logical_shift_right():
    """Logical shift fills with zeros — `-1 lshr 1` on i64 is 2^63 - 1."""
    s, _ = _make_open_substrate_with_passes()
    inst, _, _, _, user = _build_binop(s, "lshr", -1, 1)
    s.run_rules(100)
    assert not s.has_node(inst), "lshr should fold"
    assert s.node(_user_op0_value(s, user))["attrs"].get("value") == (1 << 63) - 1


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_constfold_ashr_folds_to_arithmetic_shift_right():
    """Arithmetic shift preserves the sign bit — `-8 ashr 1` is -4."""
    s, _ = _make_open_substrate_with_passes()
    inst, _, _, _, user = _build_binop(s, "ashr", -8, 1)
    s.run_rules(100)
    assert not s.has_node(inst), "ashr should fold"
    assert s.node(_user_op0_value(s, user))["attrs"].get("value") == -4


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_identity_add_zero_right_eliminates_inst():
    """add %x, 0 → %x (non-constant lhs, constant zero rhs)."""
    s, _ = _make_open_substrate_with_passes()
    inst, x_val, _, _, user = _build_binop(
        s, "add", 0, 0, lhs_is_const=False, rhs_is_const=True
    )
    s.run_rules(100)
    assert not s.has_node(inst), "add X, 0 should fold to X"
    assert _user_op0_value(s, user) == x_val


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_identity_add_zero_left_eliminates_inst():
    """add 0, %x → %x (constant zero lhs, non-constant rhs)."""
    s, _ = _make_open_substrate_with_passes()
    inst, _, x_val, _, user = _build_binop(
        s, "add", 0, 0, lhs_is_const=True, rhs_is_const=False
    )
    s.run_rules(100)
    assert not s.has_node(inst), "add 0, X should fold to X"
    assert _user_op0_value(s, user) == x_val


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_identity_mul_one_right_eliminates_inst():
    """mul %x, 1 → %x."""
    s, _ = _make_open_substrate_with_passes()
    inst, x_val, _, _, user = _build_binop(
        s, "mul", 0, 1, lhs_is_const=False, rhs_is_const=True
    )
    s.run_rules(100)
    assert not s.has_node(inst), "mul X, 1 should fold to X"
    assert _user_op0_value(s, user) == x_val


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_identity_mul_zero_right_folds_to_zero():
    """mul %x, 0 → 0 (the zero constant absorbs the product)."""
    s, _ = _make_open_substrate_with_passes()
    inst, _, zero_const, _, user = _build_binop(
        s, "mul", 0, 0, lhs_is_const=False, rhs_is_const=True
    )
    s.run_rules(100)
    assert not s.has_node(inst), "mul X, 0 should fold to the zero const"
    # User's op0 should be the original zero constant.
    assert _user_op0_value(s, user) == zero_const
    assert s.node(zero_const)["attrs"].get("value") == 0


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_identity_sub_self_folds_to_zero():
    """sub %x, %x → 0 — both operands the SAME node."""
    s, _ = _make_open_substrate_with_passes()
    x_val = s.add_node("LLVMValue", {"type": "i32"})
    inst = s.add_node("LLVMInstruction", {"opcode": "sub"})
    result = s.add_node("LLVMValue", {"type": "i32"})
    user = s.add_node("LLVMInstruction", {"opcode": "ret"})
    s.add_edge(inst, "uses_op0", x_val, {})
    s.add_edge(inst, "uses_op1", x_val, {})  # same node both ops
    s.add_edge(inst, "produces", result, {})
    s.add_edge(user, "uses_op0", result, {})
    s.run_rules(100)
    assert not s.has_node(inst), "sub X, X should fold to 0"
    new_target = _user_op0_value(s, user)
    assert s.node(new_target)["attrs"].get("value") == 0


# Parametric identity-pass tests — one entry per pass in the seed.
# Each entry describes: opcode, the position of the identity constant
# (0 or 1, or "self" for both-operands-same), the constant value, and
# the expected outcome (what user.uses_op0 should resolve to after).
#
# "outcome":
#   "lhs"        — result is the non-constant operand on the left
#   "rhs"        — result is the non-constant operand on the right
#   "rhs_const"  — result is the constant on the right (absorbing zero)
#   "lhs_const"  — result is the constant on the left
#   "self"       — both operands the same node; result is that node
#   "zero_new"   — a new zero constant takes the result's place

_IDENTITY_CASES = [
    # opcode, name (for diagnostics), const_pos, const_val, outcome
    ("sub", "identity_sub_zero",         1, 0, "lhs"),
    ("mul", "identity_mul_one_left",     0, 1, "rhs"),
    ("mul", "identity_mul_zero_left",    0, 0, "lhs_const"),
    ("and", "identity_and_zero_right",   1, 0, "rhs_const"),
    ("and", "identity_and_zero_left",    0, 0, "lhs_const"),
    ("or",  "identity_or_zero_right",    1, 0, "lhs"),
    ("or",  "identity_or_zero_left",     0, 0, "rhs"),
    ("xor", "identity_xor_zero_right",   1, 0, "lhs"),
    ("xor", "identity_xor_zero_left",    0, 0, "rhs"),
    ("shl", "identity_shl_zero",         1, 0, "lhs"),
    ("lshr", "identity_lshr_zero",       1, 0, "lhs"),
    ("ashr", "identity_ashr_zero",       1, 0, "lhs"),
]


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
@pytest.mark.parametrize("opcode,pass_name,const_pos,const_val,outcome",
                         _IDENTITY_CASES)
def test_identity_pass_fires(opcode, pass_name, const_pos, const_val, outcome):
    """One test per identity pass. Builds an IR fragment that ONLY that
    pass targets, runs rules, asserts the rewrite landed."""
    s, _ = _make_open_substrate_with_passes()
    # const_pos=1 means RHS is the identity constant; const_pos=0 means LHS.
    if const_pos == 1:
        inst, lhs, rhs, _, user = _build_binop(
            s, opcode, 0, const_val,
            lhs_is_const=False, rhs_is_const=True,
        )
    else:
        inst, lhs, rhs, _, user = _build_binop(
            s, opcode, const_val, 0,
            lhs_is_const=True, rhs_is_const=False,
        )
    # rhs/lhs identifies which physical node is the constant.
    s.run_rules(100)

    # The instruction's opcode shouldn't appear among live instructions.
    live_opcodes = {
        s.node(nid)["attrs"].get("opcode")
        for nid in s.nodes()
        if s.node(nid)["type"] == "LLVMInstruction"
        and nid != user  # exclude the test's user/ret instruction
    }
    assert opcode not in live_opcodes, \
        f"{pass_name}: {opcode} instruction should be folded away"

    final = _user_op0_value(s, user)
    if outcome == "lhs":
        assert final == lhs, f"{pass_name}: expected user → lhs ({lhs}), got {final}"
    elif outcome == "rhs":
        assert final == rhs, f"{pass_name}: expected user → rhs ({rhs}), got {final}"
    elif outcome == "rhs_const":
        assert final == rhs, f"{pass_name}: expected user → rhs constant"
        assert s.node(final)["attrs"].get("value") == const_val
    elif outcome == "lhs_const":
        assert final == lhs, f"{pass_name}: expected user → lhs constant"
        assert s.node(final)["attrs"].get("value") == const_val
    else:
        raise AssertionError(f"unknown outcome {outcome!r}")


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
@pytest.mark.parametrize("opcode,pass_name", [
    ("and", "identity_and_self"),
    ("or",  "identity_or_self"),
])
def test_identity_self_idempotent(opcode, pass_name):
    """and X, X → X; or X, X → X. Both operands the SAME node."""
    s, _ = _make_open_substrate_with_passes()
    x = s.add_node("LLVMValue", {"type": "i32"})
    inst = s.add_node("LLVMInstruction", {"opcode": opcode})
    result = s.add_node("LLVMValue", {"type": "i32"})
    user = s.add_node("LLVMInstruction", {"opcode": "ret"})
    s.add_edge(inst, "uses_op0", x, {})
    s.add_edge(inst, "uses_op1", x, {})
    s.add_edge(inst, "produces", result, {})
    s.add_edge(user, "uses_op0", result, {})

    s.run_rules(100)

    live_opcodes = {
        s.node(nid)["attrs"].get("opcode")
        for nid in s.nodes()
        if s.node(nid)["type"] == "LLVMInstruction" and nid != user
    }
    assert opcode not in live_opcodes
    assert _user_op0_value(s, user) == x


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_identity_xor_self_folds_to_zero():
    """xor X, X → 0. Same operand both sides, result is a fresh zero
    constant (not X)."""
    s, _ = _make_open_substrate_with_passes()
    x = s.add_node("LLVMValue", {"type": "i32"})
    inst = s.add_node("LLVMInstruction", {"opcode": "xor"})
    result = s.add_node("LLVMValue", {"type": "i32"})
    user = s.add_node("LLVMInstruction", {"opcode": "ret"})
    s.add_edge(inst, "uses_op0", x, {})
    s.add_edge(inst, "uses_op1", x, {})
    s.add_edge(inst, "produces", result, {})
    s.add_edge(user, "uses_op0", result, {})

    s.run_rules(100)

    final = _user_op0_value(s, user)
    assert s.node(final)["type"] == "LLVMConstant"
    assert s.node(final)["attrs"].get("value") == 0


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_constfold_add_chains_into_constfold_mul():
    """Compose passes: ((1+2) * 3) folds to a single constant 9 across
    two passes firing in sequence. Tests that fixed-point semantics
    actually compose."""
    s, _ = _make_open_substrate_with_passes()
    c1 = s.add_node("LLVMConstant", {"value": 1, "type": "i32"})
    c2 = s.add_node("LLVMConstant", {"value": 2, "type": "i32"})
    c3 = s.add_node("LLVMConstant", {"value": 3, "type": "i32"})
    # inner: add 1, 2
    add_inst = s.add_node("LLVMInstruction", {"opcode": "add"})
    add_result = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(add_inst, "uses_op0", c1, {})
    s.add_edge(add_inst, "uses_op1", c2, {})
    s.add_edge(add_inst, "produces", add_result, {})
    # outer: mul (add_result), 3
    mul_inst = s.add_node("LLVMInstruction", {"opcode": "mul"})
    mul_result = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(mul_inst, "uses_op0", add_result, {})
    s.add_edge(mul_inst, "uses_op1", c3, {})
    s.add_edge(mul_inst, "produces", mul_result, {})
    user = s.add_node("LLVMInstruction", {"opcode": "ret"})
    s.add_edge(user, "uses_op0", mul_result, {})

    s.run_rules(100)

    # Both instructions are gone; user points at a single constant 9.
    # NodeID stability: the substrate's slab reuses freed slot indices,
    # so `has_node(add_inst)` may return True for a SLOT now occupied
    # by some other node. Check no LIVE node is still an add/mul
    # instruction instead.
    live_opcodes = {
        s.node(nid)["attrs"].get("opcode")
        for nid in s.nodes()
        if s.node(nid)["type"] == "LLVMInstruction"
    }
    assert "add" not in live_opcodes, "add instruction should be folded away"
    assert "mul" not in live_opcodes, "mul instruction should be folded away"
    final = _user_op0_value(s, user)
    assert s.node(final)["attrs"].get("value") == 9


# ---------------------------------------------------------------------------
# Dead Code Elimination — Phase 3c
# ---------------------------------------------------------------------------

def _build_dead_binop(s, opcode: str):
    """Build a pure binop with two non-constant operands and NO user
    of its result. The DCE rule should delete it."""
    op0 = s.add_node("LLVMValue", {"type": "i32"})
    op1 = s.add_node("LLVMValue", {"type": "i32"})
    inst = s.add_node("LLVMInstruction", {"opcode": opcode})
    result = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(inst, "uses_op0", op0, {})
    s.add_edge(inst, "uses_op1", op1, {})
    s.add_edge(inst, "produces", result, {})
    return inst, op0, op1, result


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
@pytest.mark.parametrize("opcode", [
    "add", "sub", "mul", "and", "or", "xor", "shl", "lshr", "ashr",
])
def test_dce_deletes_pure_binop_with_no_uses(opcode):
    s, _ = _make_open_substrate_with_passes()
    inst, _, _, result = _build_dead_binop(s, opcode)
    s.run_rules(100)

    live_insts = [n for n in s.nodes("LLVMInstruction")
                  if s.node(n)["attrs"].get("opcode") == opcode]
    assert not live_insts, \
        f"DCE should have removed the unused {opcode} instruction; " \
        f"got {len(live_insts)} survivors"


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_dce_preserves_used_instruction():
    """DCE must NOT touch an instruction whose result is consumed."""
    s, _ = _make_open_substrate_with_passes()
    op0 = s.add_node("LLVMValue", {"type": "i32"})
    op1 = s.add_node("LLVMValue", {"type": "i32"})
    inst = s.add_node("LLVMInstruction", {"opcode": "add"})
    result = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(inst, "uses_op0", op0, {})
    s.add_edge(inst, "uses_op1", op1, {})
    s.add_edge(inst, "produces", result, {})
    # A user that consumes the result — DCE must NOT fire.
    user = s.add_node("LLVMInstruction", {"opcode": "ret"})
    s.add_edge(user, "uses_op0", result, {})

    s.run_rules(100)

    live_adds = [n for n in s.nodes("LLVMInstruction")
                 if s.node(n)["attrs"].get("opcode") == "add"]
    assert len(live_adds) == 1, \
        f"used add instruction should survive; got {len(live_adds)} adds"


# ---------------------------------------------------------------------------
# Reassociation — (a op b) op c → a op (b op c) for associative ops
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_reassoc_add_then_constfold_collapses_chain():
    """`(x + 1) + 2 → x + (1 + 2) → x + 3` — the canonical normalize-
    then-reduce cascade. Reassoc isn't a reducer itself; it migrates
    the two constants into adjacency so constfold can attack them."""
    s, _ = _make_open_substrate_with_passes()
    x = s.add_node("LLVMValue", {"type": "i32"})
    c1 = s.add_node("LLVMConstant", {"value": 1, "type": "i32"})
    c2 = s.add_node("LLVMConstant", {"value": 2, "type": "i32"})

    # Inner: x + 1
    inner = s.add_node("LLVMInstruction", {"opcode": "add"})
    t = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(inner, "uses_op0", x, {})
    s.add_edge(inner, "uses_op1", c1, {})
    s.add_edge(inner, "produces", t, {})

    # Outer: t + 2
    outer = s.add_node("LLVMInstruction", {"opcode": "add"})
    r = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(outer, "uses_op0", t, {})
    s.add_edge(outer, "uses_op1", c2, {})
    s.add_edge(outer, "produces", r, {})

    # A consumer of r so DCE doesn't eat the whole chain.
    user = s.add_node("LLVMInstruction", {"opcode": "ret"})
    s.add_edge(user, "uses_op0", r, {})

    s.run_rules(200)

    # After reassoc: outer = x + new_t, inner = 1 + 2.
    # After constfold on the new inner: inner's result is constant 3.
    # outer is then x + 3, which is the final state.
    add_insts = [n for n in s.nodes("LLVMInstruction")
                 if s.node(n)["attrs"].get("opcode") == "add"]
    # Should be exactly one surviving add: x + 3.
    assert len(add_insts) == 1, \
        f"expected one surviving add after reassoc+constfold; got {len(add_insts)}"

    surviving = add_insts[0]
    op0_targets = s.neighbours(surviving, "uses_op0")
    op1_targets = s.neighbours(surviving, "uses_op1")
    assert len(op0_targets) == 1 and len(op1_targets) == 1
    # Operands: x (LLVMValue) + 3 (LLVMConstant).
    operands = (s.node(op0_targets[0]), s.node(op1_targets[0]))
    types = {operands[0]["type"], operands[1]["type"]}
    assert types == {"LLVMValue", "LLVMConstant"}, \
        f"one operand should be the SSA x, one the folded 3; got {types}"
    const_op = operands[0] if operands[0]["type"] == "LLVMConstant" else operands[1]
    assert const_op["attrs"].get("value") == 3, \
        f"the folded constant should be 3 (= 1+2); got {const_op['attrs'].get('value')!r}"


# ---------------------------------------------------------------------------
# Common Subexpression Elimination — two structurally-identical pure ops
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
@pytest.mark.parametrize("opcode", ["add", "sub", "mul", "and", "or", "xor"])
def test_cse_merges_duplicate_pure_ops(opcode):
    """Two pure ops with same opcode and same operands → keep one, merge
    uses, delete the duplicate."""
    s, _ = _make_open_substrate_with_passes()
    x = s.add_node("LLVMValue", {"type": "i32"})
    y = s.add_node("LLVMValue", {"type": "i32"})

    # Two structurally identical add instructions.
    inst1 = s.add_node("LLVMInstruction", {"opcode": opcode})
    val1 = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(inst1, "uses_op0", x, {})
    s.add_edge(inst1, "uses_op1", y, {})
    s.add_edge(inst1, "produces", val1, {})

    inst2 = s.add_node("LLVMInstruction", {"opcode": opcode})
    val2 = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(inst2, "uses_op0", x, {})
    s.add_edge(inst2, "uses_op1", y, {})
    s.add_edge(inst2, "produces", val2, {})

    # A user of val2 — should get rewired to val1 (or vice-versa) after CSE.
    user = s.add_node("LLVMInstruction", {"opcode": "ret"})
    s.add_edge(user, "uses_op0", val2, {})

    s.run_rules(100)

    # One of the two should be gone.
    live = [n for n in s.nodes("LLVMInstruction")
            if s.node(n)["attrs"].get("opcode") == opcode]
    assert len(live) == 1, \
        f"CSE should leave exactly one {opcode}; got {len(live)}"

    # The user's operand should now point at the surviving instruction's
    # produces value (either val1 or val2, depending on which was kept).
    user_ops = s.neighbours(user, "uses_op0")
    assert len(user_ops) == 1
    # The target is one of the two LLVMValues that the surviving inst
    # produces — i.e. it's still a live LLVMValue.
    assert s.has_node(user_ops[0])


# ---------------------------------------------------------------------------
# Strength reduction — mul X, 2^k → shl X, k
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
@pytest.mark.parametrize("constant,shift", [
    (2, 1), (4, 2), (8, 3), (16, 4),
])
def test_strength_reduce_mul_by_power_of_two(constant, shift):
    """mul X, 2^k → shl X, k. The instruction's opcode flips to shl,
    its second operand is rewired from the original constant to the
    new shift amount."""
    s, _ = _make_open_substrate_with_passes()
    x = s.add_node("LLVMValue", {"type": "i32"})
    c = s.add_node("LLVMConstant", {"value": constant, "type": "i32"})
    inst = s.add_node("LLVMInstruction", {"opcode": "mul"})
    result = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(inst, "uses_op0", x, {})
    s.add_edge(inst, "uses_op1", c, {})
    s.add_edge(inst, "produces", result, {})
    user = s.add_node("LLVMInstruction", {"opcode": "ret"})
    s.add_edge(user, "uses_op0", result, {})

    s.run_rules(100)

    # Opcode flipped to shl.
    assert s.node(inst)["attrs"].get("opcode") == "shl", \
        f"opcode should be shl after strength reduction; got " \
        f"{s.node(inst)['attrs'].get('opcode')!r}"

    # Operand 1 now points at a constant with value `shift`.
    ops = s.neighbours(inst, "uses_op1")
    assert len(ops) == 1
    new_attrs = s.node(ops[0])["attrs"]
    assert new_attrs.get("value") == shift, \
        f"new shift amount should be {shift}; got {new_attrs.get('value')}"

    # Operand 0 still points at the original SSA value X.
    assert s.neighbours(inst, "uses_op0") == [x]


@pytest.mark.skipif(
    _native_substrate_with_add_rule() is None,
    reason="substrate_rs native binding lacks add_rule (stale wheel?)",
)
def test_dce_cascades_to_fixed_point():
    """An unused chain — add feeds mul feeds nothing — should be wholly
    removed: deleting mul makes add's result unused, which fires DCE
    again on the next round. Verifies the engine's eval_cache + cursor
    invalidation work correctly across rule-driven deletes."""
    s, _ = _make_open_substrate_with_passes()
    a = s.add_node("LLVMValue", {"type": "i32"})
    b = s.add_node("LLVMValue", {"type": "i32"})
    add_inst = s.add_node("LLVMInstruction", {"opcode": "add"})
    add_result = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(add_inst, "uses_op0", a, {})
    s.add_edge(add_inst, "uses_op1", b, {})
    s.add_edge(add_inst, "produces", add_result, {})

    c = s.add_node("LLVMValue", {"type": "i32"})
    mul_inst = s.add_node("LLVMInstruction", {"opcode": "mul"})
    mul_result = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(mul_inst, "uses_op0", add_result, {})
    s.add_edge(mul_inst, "uses_op1", c, {})
    s.add_edge(mul_inst, "produces", mul_result, {})
    # No user of mul_result — dead chain.

    s.run_rules(100)

    live_opcodes = {
        s.node(n)["attrs"].get("opcode")
        for n in s.nodes("LLVMInstruction")
    }
    assert "add" not in live_opcodes
    assert "mul" not in live_opcodes
