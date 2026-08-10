"""Rule-inference layer — structural fingerprints + RuleFamily discovery.

The agent's installed LLVM passes are not opaque rule indices; each is
mirrored as a `RewriteRule` graph node carrying its structural
fingerprint (match-edges, effect-kinds, where-features). Rules sharing
a fingerprint are linked to the same `RuleFamily` node via `member_of`.
The agent's reasoning about its own optimization arsenal is then a
graph query — not an analysis pass run on demand.

These tests assert:
  1. Fingerprint extraction picks the right structural features.
  2. After installing the seed, rules with the same shape end up in
     the same RuleFamily.
  3. Rules with different shapes end up in different families.
  4. The family count is bounded by the number of distinct shapes
     (~3 for the current seed: constfold, identity-with-value-eq,
     identity-with-repeated-var).
"""
from __future__ import annotations

import pytest

from domains.llvm_pass_compiler import install_passes_seed
from domains.rule_inference import rule_fingerprint


_REPO_ROOT = __file__.rsplit("/tests/", 1)[0]
_SEED_PATH = f"{_REPO_ROOT}/seeds/llvm_passes.json"


# ---------------------------------------------------------------------------
# fingerprint — pure function over a rule spec
# ---------------------------------------------------------------------------

_CONSTFOLD_ADD = {
    "kind": "transformation",
    "name": "constfold_add",
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
        {"add_node": {"var": "?new_const", "type": "LLVMConstant",
                      "attrs": {"value": {"add": [{"attr": ["?v1", "value"]},
                                                  {"attr": ["?v2", "value"]}]},
                                "type": {"attr": ["?v1", "type"]}}}},
        {"replace_value": {"old": "?old", "new": "?new_const"}},
        {"delete": "?inst"},
    ],
}

_IDENTITY_ADD_ZERO_RIGHT = {
    "kind": "transformation",
    "name": "identity_add_zero_right",
    "match": [
        ["?inst", "uses_op0", "?x"],
        ["?inst", "uses_op1", "?v2"],
        ["?inst", "produces", "?old"],
    ],
    "where": {
        "all": [
            {"type_of": "?inst", "is": "LLVMInstruction"},
            {"attr": ["?inst", "opcode"], "eq": "add"},
            {"type_of": "?v2", "is": "LLVMConstant"},
            {"attr": ["?v2", "value"], "eq": 0},
        ]
    },
    "effect": [
        {"replace_value": {"old": "?old", "new": "?x"}},
        {"delete": "?inst"},
    ],
}

_IDENTITY_AND_SELF = {
    "kind": "transformation",
    "name": "identity_and_self",
    "match": [
        ["?inst", "uses_op0", "?x"],
        ["?inst", "uses_op1", "?x"],
        ["?inst", "produces", "?old"],
    ],
    "where": {
        "all": [
            {"type_of": "?inst", "is": "LLVMInstruction"},
            {"attr": ["?inst", "opcode"], "eq": "and"},
        ]
    },
    "effect": [
        {"replace_value": {"old": "?old", "new": "?x"}},
        {"delete": "?inst"},
    ],
}


def test_fingerprint_constfold_has_two_constants_and_computed_effect():
    fp = rule_fingerprint(_CONSTFOLD_ADD)
    assert fp["match_edges"] == ("uses_op0", "uses_op1", "produces")
    assert fp["match_repeated_var"] is False
    assert fp["effect_kinds"] == ("add_node", "replace_value", "del_node")
    assert fp["effect_computed_value"] is True
    assert fp["typeof_constant_count"] == 2
    assert fp["has_value_eq"] is False
    assert fp["has_opcode_eq"] is True


def test_fingerprint_identity_zero_right_has_value_eq_and_one_constant():
    fp = rule_fingerprint(_IDENTITY_ADD_ZERO_RIGHT)
    assert fp["effect_kinds"] == ("replace_value", "del_node")
    assert fp["effect_computed_value"] is False
    assert fp["typeof_constant_count"] == 1
    assert fp["has_value_eq"] is True
    assert fp["match_repeated_var"] is False


def test_fingerprint_identity_self_has_repeated_var_no_constants():
    fp = rule_fingerprint(_IDENTITY_AND_SELF)
    assert fp["match_repeated_var"] is True
    assert fp["typeof_constant_count"] == 0
    assert fp["has_value_eq"] is False
    assert fp["effect_kinds"] == ("replace_value", "del_node")


def test_constfold_variants_share_fingerprint():
    """add, sub, mul, and, or, xor, shl, lshr, ashr constfold rules
    have different OPCODES but the same SHAPE — they're members of
    the same family by inference."""
    base = dict(_CONSTFOLD_ADD)
    fp_add = rule_fingerprint(base)["key"]

    for op_name, op_key in (
        ("sub", "sub"), ("mul", "mul"),
        ("and", "bit_and"), ("or", "bit_or"), ("xor", "bit_xor"),
        ("shl", "shl"), ("lshr", "lshr"), ("ashr", "ashr"),
    ):
        spec = {
            **_CONSTFOLD_ADD,
            "name": f"constfold_{op_name}",
            "where": {
                "all": [
                    {"type_of": "?inst", "is": "LLVMInstruction"},
                    {"attr": ["?inst", "opcode"], "eq": op_name},
                    {"type_of": "?v1", "is": "LLVMConstant"},
                    {"type_of": "?v2", "is": "LLVMConstant"},
                ]
            },
            "effect": [
                {"add_node": {"var": "?new_const", "type": "LLVMConstant",
                              "attrs": {
                                  "value": {op_key: [{"attr": ["?v1", "value"]},
                                                     {"attr": ["?v2", "value"]}]},
                                  "type": {"attr": ["?v1", "type"]}}}},
                {"replace_value": {"old": "?old", "new": "?new_const"}},
                {"delete": "?inst"},
            ],
        }
        assert rule_fingerprint(spec)["key"] == fp_add, \
            f"constfold_{op_name} should share family with constfold_add"


def test_constfold_and_identity_have_different_fingerprints():
    f1 = rule_fingerprint(_CONSTFOLD_ADD)["key"]
    f2 = rule_fingerprint(_IDENTITY_ADD_ZERO_RIGHT)["key"]
    f3 = rule_fingerprint(_IDENTITY_AND_SELF)["key"]
    assert len({f1, f2, f3}) == 3, \
        "the three structural shapes should all be distinct"


# ---------------------------------------------------------------------------
# End-to-end install — RewriteRule + RuleFamily nodes appear, dedupe by
# fingerprint, and the discovered family count matches the seed's shapes.
# ---------------------------------------------------------------------------

def _native_substrate_or_skip():
    try:
        from substrate_rs import _native
        s = _native.Substrate()
        # Open the LLVM-side grammar so rule application doesn't fail.
        for src_t in ("LLVMInstruction", "LLVMConstant", "LLVMValue"):
            for tgt_t in ("LLVMInstruction", "LLVMConstant", "LLVMValue"):
                for et in ("uses_op0", "uses_op1", "uses_op2", "produces"):
                    s.add_production({
                        "src": {"type": src_t, "var": "src"},
                        "edge_type": et,
                        "tgt": {"type": tgt_t, "var": "tgt"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "test:open",
                    })
        return s
    except Exception as e:
        pytest.skip(f"native substrate unavailable: {e}")


def test_install_seed_creates_rewrite_rule_nodes():
    s = _native_substrate_or_skip()
    install_passes_seed(s, _SEED_PATH)
    rrs = s.nodes("RewriteRule")
    assert len(rrs) == 72, f"expected 72 RewriteRule mirrors; got {len(rrs)}"
    # Every mirror has a non-empty fingerprint string.
    for r in rrs:
        attrs = s.node(r)["attrs"]
        assert isinstance(attrs.get("fingerprint"), str)
        assert attrs["fingerprint"], f"empty fingerprint on {attrs.get('name')!r}"


def test_dce_rules_share_one_family():
    """All 9 dce_* rules have the same structural shape — single
    `del_node` effect with a use-count-zero where-clause."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _SEED_PATH)

    dce_families = set()
    for r in s.nodes("RewriteRule"):
        attrs = s.node(r)["attrs"]
        if not attrs.get("name", "").startswith("dce_"):
            continue
        assert attrs.get("has_use_count_zero") is True, \
            f"{attrs['name']} should carry use-count-zero feature"
        fams = s.neighbours(r, "member_of")
        assert len(fams) == 1
        dce_families.add(fams[0])

    assert len(dce_families) == 1, \
        f"all 9 dce_* rules should share one family; got {len(dce_families)}"


def test_reassoc_rules_share_one_family():
    """All reassoc_* rules share a single structurally-distinct family
    — characterised by the long del_edge/add_edge effect chain (8 ops)
    that distinguishes them from CSE (same 6-edge match, different
    effects) and from any single-instruction pattern."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _SEED_PATH)

    reassoc_families = set()
    for r in s.nodes("RewriteRule"):
        attrs = s.node(r)["attrs"]
        if not attrs.get("name", "").startswith("reassoc_"):
            continue
        # 6 match edges (two instructions), 8 effect ops (4 del + 4 add).
        assert len(attrs["match_edges"]) == 6
        assert len(attrs["effect_kinds"]) == 8
        fams = s.neighbours(r, "member_of")
        assert len(fams) == 1
        reassoc_families.add(fams[0])

    assert len(reassoc_families) == 1, \
        f"all reassoc_* rules should share one family; got " \
        f"{len(reassoc_families)}"


def test_cse_rules_share_one_family():
    """All cse_* rules have the same structural shape — a 6-edge
    match (two instructions worth of operand+produces edges) with
    repeated operand vars across the pair."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _SEED_PATH)

    cse_families = set()
    for r in s.nodes("RewriteRule"):
        attrs = s.node(r)["attrs"]
        if not attrs.get("name", "").startswith("cse_"):
            continue
        # 6 match edges (twice through op0/op1/produces).
        assert len(attrs["match_edges"]) == 6, \
            f"cse rule {attrs['name']} should have 6 match edges; got " \
            f"{len(attrs['match_edges'])}"
        fams = s.neighbours(r, "member_of")
        assert len(fams) == 1
        cse_families.add(fams[0])

    assert len(cse_families) == 1, \
        f"all cse_* rules should share one family; got {len(cse_families)}"


def test_strength_reduction_rules_share_one_family():
    """All strength_reduce_* rules share a single structurally-distinct
    family — they're characterised by the four-effect sequence
    (add_node, del_edge, add_edge, set_attr) that no other family has."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _SEED_PATH)

    sr_families = set()
    for r in s.nodes("RewriteRule"):
        attrs = s.node(r)["attrs"]
        if not attrs.get("name", "").startswith("strength_reduce_"):
            continue
        fams = s.neighbours(r, "member_of")
        assert len(fams) == 1
        sr_families.add(fams[0])

    assert len(sr_families) == 1, \
        f"all strength_reduce_* rules should share one family; got " \
        f"{len(sr_families)}"


def test_install_seed_collapses_constfold_into_one_family():
    s = _native_substrate_or_skip()
    install_passes_seed(s, _SEED_PATH)

    # Find every RewriteRule with name starting with "constfold_" and
    # walk its `member_of` edge to a family. All constfold rules —
    # including the icmp_* variants whose output type is i1 — share
    # the same structural shape and so should land in one family.
    constfold_families = set()
    for r in s.nodes("RewriteRule"):
        attrs = s.node(r)["attrs"]
        if not attrs.get("name", "").startswith("constfold_"):
            continue
        fams = s.neighbours(r, "member_of")
        assert len(fams) == 1, \
            f"{attrs['name']} should belong to exactly one family; got {fams}"
        constfold_families.add(fams[0])

    assert len(constfold_families) == 1, \
        f"all constfold_* rules should share one RuleFamily; got " \
        f"{len(constfold_families)}"


def test_install_seed_keeps_distinct_shapes_in_distinct_families():
    """constfold / identity-with-value-eq / identity-self are different
    structural shapes and end up in distinct families."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _SEED_PATH)

    def family_of(rule_name: str) -> int:
        for r in s.nodes("RewriteRule"):
            if s.node(r)["attrs"].get("name") == rule_name:
                fams = s.neighbours(r, "member_of")
                assert len(fams) == 1
                return fams[0]
        raise AssertionError(f"{rule_name} not installed")

    f_constfold = family_of("constfold_add")
    f_zero_right = family_of("identity_add_zero_right")
    f_self = family_of("identity_and_self")
    assert len({f_constfold, f_zero_right, f_self}) == 3, \
        "the three observable shapes should resolve to three families"


def test_family_count_is_small_enough_to_carry_meaning():
    """Discovered families should be small in number (~5–10) — fewer
    than rules (29). If we end up with one family per rule, the
    fingerprint isn't abstract enough; if we end up with one for
    everything, it's too coarse."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _SEED_PATH)
    families = s.nodes("RuleFamily")
    n_rules = len(s.nodes("RewriteRule"))
    assert 2 <= len(families) < n_rules, \
        f"got {len(families)} families across {n_rules} rules — " \
        f"fingerprint too {'coarse' if len(families) < 2 else 'fine'}"
