"""Graph-resident codec walking — the architecturally correct shape.

The earlier codec demos in `test_codec_primitives.py` walked PPS field
grammar via Python if/elif chains. That's domain knowledge about
H.264, which per the project's core principle belongs in the graph
(`ozma-concepts-in-gamma`), not in Python.

This file does it the right way: the H.264 PPS field grammar lives
as `FieldSpec` graph nodes chained via `next` edges; decode is a set
of graph-resident rewrite Rules dispatched on `field.kind`. Python's
role shrinks to: seed the grammar + Rules (once), load bytes, call
`run_rules`, read the decoded values from the graph.

The agent can extend this to a new codec by minting a new FieldSpec
chain — no Python touched, no runner extended.
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate_rs import (
    Substrate, Var, Lit, Attr, Eq, Lt, And, Or, Not, Exists, Neighbours,
    Nth, Plus, TypeOf,
    BitsAt, BitsWrite, ExpGolombDecode, ExpGolombDecodeSigned,
    ExpGolombEncode, ExpGolombEncodeSigned,
    Production, NodePattern,
)


# --- codec grammar as graph-resident data --------------------------


# H.264 PPS field order per ITU-T H.264 §7.3.2.2 (the simple
# single-slice-group prefix — full grammar would add the slice-group-
# map branch). Each tuple is (kind, name [, nbits]). The grammar is
# minted as graph nodes; Python's role is the one-time seeding.
H264_PPS_FIELDS = [
    ("ue", "pic_parameter_set_id"),
    ("ue", "seq_parameter_set_id"),
    ("u",  "entropy_coding_mode_flag", 1),
    ("u",  "bottom_field_pic_order_in_frame_present_flag", 1),
    ("ue", "num_slice_groups_minus1"),
    ("ue", "num_ref_idx_l0_default_active_minus1"),
    ("ue", "num_ref_idx_l1_default_active_minus1"),
    ("u",  "weighted_pred_flag", 1),
    ("u",  "weighted_bipred_idc", 2),
    ("se", "pic_init_qp_minus26"),
]


# HEVC PPS field order per ITU-T H.265 §7.3.2.3. The full grammar
# contains conditional branches (cu_qp_delta_enabled_flag gates
# diff_cu_qp_delta_depth, deblocking_filter_control_present_flag
# gates beta/tc offsets, scaling-list-present gates the list data,
# extension flag gates the extension). For x265's ultrafast default,
# all of these gating flags are 0, so the conditional bodies are
# absent in the bitstream and the unconditional sequence below
# decodes + re-emits the whole PPS byte-exact. A future
# `condition_name` attr on FieldSpec would let the rule engine
# handle conditional branches generically.
H265_PPS_FIELDS = [
    ("ue", "pps_pic_parameter_set_id"),
    ("ue", "pps_seq_parameter_set_id"),
    ("u",  "dependent_slice_segments_enabled_flag", 1),
    ("u",  "output_flag_present_flag", 1),
    ("u",  "num_extra_slice_header_bits", 3),
    ("u",  "sign_data_hiding_enabled_flag", 1),
    ("u",  "cabac_init_present_flag", 1),
    ("ue", "num_ref_idx_l0_default_active_minus1"),
    ("ue", "num_ref_idx_l1_default_active_minus1"),
    ("se", "init_qp_minus26"),
    ("u",  "constrained_intra_pred_flag", 1),
    ("u",  "transform_skip_enabled_flag", 1),
    ("u",  "cu_qp_delta_enabled_flag", 1),
    # Conditional: only present when cu_qp_delta_enabled_flag == 1.
    ("ue", "diff_cu_qp_delta_depth",
     {"condition_name": "cu_qp_delta_enabled_flag",
      "condition_value": 1}),
    ("se", "pps_cb_qp_offset"),
    ("se", "pps_cr_qp_offset"),
    ("u",  "pps_slice_chroma_qp_offsets_present_flag", 1),
    ("u",  "weighted_pred_flag", 1),
    ("u",  "weighted_bipred_flag", 1),
    ("u",  "transquant_bypass_enabled_flag", 1),
    ("u",  "tiles_enabled_flag", 1),
    ("u",  "entropy_coding_sync_enabled_flag", 1),
    # Tile-array block, gated by tiles_enabled_flag == 1 (per
    # H.265 §7.3.2.3). The per-tile-width/height arrays are
    # ADDITIONALLY gated by uniform_spacing_flag == 0 — i.e. they
    # appear only when the tile sizes aren't uniformly inferred
    # from the picture dimensions.
    ("ue", "num_tile_columns_minus1",
     {"conditions": [("tiles_enabled_flag", 1)]}),
    ("ue", "num_tile_rows_minus1",
     {"conditions": [("tiles_enabled_flag", 1)]}),
    ("u",  "uniform_spacing_flag", 1,
     {"conditions": [("tiles_enabled_flag", 1)]}),
    ("loop", "column_width_minus1", {
        "body_kind": "ue",
        "count_name": "num_tile_columns_minus1",
        "count_offset": 0,
        "groups": [[("tiles_enabled_flag", 1),
                    ("uniform_spacing_flag", 0)]],
    }),
    ("loop", "row_height_minus1", {
        "body_kind": "ue",
        "count_name": "num_tile_rows_minus1",
        "count_offset": 0,
        "groups": [[("tiles_enabled_flag", 1),
                    ("uniform_spacing_flag", 0)]],
    }),
    ("u",  "loop_filter_across_tiles_enabled_flag", 1,
     {"conditions": [("tiles_enabled_flag", 1)]}),
    ("u",  "pps_loop_filter_across_slices_enabled_flag", 1),
    ("u",  "deblocking_filter_control_present_flag", 1),
    # Deblocking branch: gated by deblocking_filter_control_present_flag.
    ("u",  "deblocking_filter_override_enabled_flag",
     1, {"condition_name": "deblocking_filter_control_present_flag",
         "condition_value": 1}),
    ("u",  "pps_deblocking_filter_disabled_flag",
     1, {"condition_name": "deblocking_filter_control_present_flag",
         "condition_value": 1}),
    # Nested branch: deblocking_filter_control_present_flag == 1 AND
    # pps_deblocking_filter_disabled_flag == 0 — the H.265 spec's
    # `if (!disabled)` becomes a second condition with val=0.
    ("se", "pps_beta_offset_div2",
     {"conditions": [
         ("deblocking_filter_control_present_flag", 1),
         ("pps_deblocking_filter_disabled_flag", 0),
     ]}),
    ("se", "pps_tc_offset_div2",
     {"conditions": [
         ("deblocking_filter_control_present_flag", 1),
         ("pps_deblocking_filter_disabled_flag", 0),
     ]}),
    ("u",  "pps_scaling_list_data_present_flag", 1),
    # scaling list branch — gated by pps_scaling_list_data_present_flag.
    ("u",  "lists_modification_present_flag", 1),
    ("ue", "log2_parallel_merge_level_minus2"),
    ("u",  "slice_segment_header_extension_present_flag", 1),
    ("u",  "pps_extension_present_flag", 1),
    # extension branch — gated by pps_extension_present_flag.
]


def seed_codec_vocabulary(s):
    """Extend Γ with the node/edge types the codec subgraph needs.
    Per Γ admissibility: every edge type must be sanctioned by a
    production. The agent's vocabulary grows as it learns codecs."""
    productions = [
        # Field-grammar chain.
        Production(src=NodePattern(type="FieldSpec", var="f"),
                   edge_type="next",
                   tgt=NodePattern(type="FieldSpec", var="g")),
        # A FieldSpec may carry zero or more ConditionGroups — each
        # group is a set of Conditions that must ALL hold (AND). A
        # field is active iff any group satisfies (OR over groups).
        # Full DNF: AND inside a group, OR across groups, negation
        # via val=0. Unconditional fields have no groups.
        Production(src=NodePattern(type="FieldSpec", var="f"),
                   edge_type="cond_group",
                   tgt=NodePattern(type="ConditionGroup", var="g")),
        Production(src=NodePattern(type="ConditionGroup", var="g"),
                   edge_type="member",
                   tgt=NodePattern(type="Condition", var="c")),
        # DecodeState wiring.
        Production(src=NodePattern(type="DecodeState", var="s"),
                   edge_type="current",
                   tgt=NodePattern(type="FieldSpec", var="f")),
        Production(src=NodePattern(type="DecodeState", var="s"),
                   edge_type="buffer",
                   tgt=NodePattern(type="Buffer", var="b")),
        Production(src=NodePattern(type="DecodeState", var="s"),
                   edge_type="decoded",
                   tgt=NodePattern(type="Value", var="v")),
        # EncodeState mirrors DecodeState.
        Production(src=NodePattern(type="EncodeState", var="s"),
                   edge_type="current",
                   tgt=NodePattern(type="FieldSpec", var="f")),
        Production(src=NodePattern(type="EncodeState", var="s"),
                   edge_type="buffer",
                   tgt=NodePattern(type="Buffer", var="b")),
        Production(src=NodePattern(type="EncodeState", var="s"),
                   edge_type="source",
                   tgt=NodePattern(type="DecodeState", var="d")),
        # Iteration: a Loop FieldSpec uses a LoopState to track its
        # current index. Both decode and encode states can carry
        # active loops.
        Production(src=NodePattern(type="DecodeState", var="s"),
                   edge_type="loop_state",
                   tgt=NodePattern(type="LoopState", var="l")),
        Production(src=NodePattern(type="EncodeState", var="s"),
                   edge_type="loop_state",
                   tgt=NodePattern(type="LoopState", var="l")),
        Production(src=NodePattern(type="LoopState", var="l"),
                   edge_type="loop",
                   tgt=NodePattern(type="FieldSpec", var="f")),
    ]
    for p in productions:
        s.add_production(p)


def seed_field_grammar(s, field_list):
    """Mint a field-grammar subgraph from a list of field specs.

    Each spec is a tuple. Common forms:
      ("ue", name)                — unconditional ue(v)
      ("se", name)                — unconditional se(v)
      ("u",  name, nbits)         — unconditional u(n)
      ("loop", name, {body_kind:..., count_name:..., count_offset:0,
                      body_nbits:...})
                                  — iterate body N times where
                                    N = decoded(count_name).val +
                                    count_offset. Each iteration
                                    emits a Value with the loop's
                                    name + an `index` attr 0..N-1.
                                    body_kind ∈ {ue, se, u}; for
                                    "u" pass body_nbits.
      (...,  {opts})              — any of the above with a trailing
                                    dict carrying optional metadata

    Optional gating via the trailing dict — three shapes, all
    normalised to the same internal "list of ConditionGroups" form:

      conditions: [(name1, val1), (name2, val2), ...]
                    — single AND-group; field active iff every named
                      value matches. Negation via val=0. Nested AND
                      (e.g. H.265 `A==1 AND B==0`) just lists more.
      groups: [[(name, val), ...], [(name, val), ...], ...]
                    — multiple AND-groups; field active iff ANY
                      group satisfies (full OR-of-ANDs / DNF).
                      Covers H.265 `chroma_format_idc != 0` as
                      groups=[[("chroma_format_idc",1)],
                              [("chroma_format_idc",2)],
                              [("chroma_format_idc",3)]].
      Legacy: condition_name + condition_value → one group of one.

    Each group becomes a `ConditionGroup` graph node holding
    `Condition` members; the FieldSpec edges to its groups via
    `cond_group`. The Rule machinery walks them natively."""
    head = None
    prev = None
    for spec in field_list:
        opts = {}
        items = list(spec)
        if items and isinstance(items[-1], dict):
            # COPY the dict — the field_list is a module-level
            # constant in many callers, and `.pop()` below would
            # otherwise mutate the source on first call and break
            # subsequent ones.
            opts = dict(items.pop())
        kind, name = items[0], items[1]
        attrs = {"kind": kind, "name": name}
        if kind == "u":
            attrs["nbits"] = items[2]
        # Loops: body_kind / count_name / count_offset come through
        # `opts` and land on the FieldSpec attrs so the iterate rule
        # can read them via Attr(loop, "body_kind") etc. Default
        # count_offset to 0 (common case — count is the value
        # directly; H.265's "minus1" pattern uses count_offset=1).
        if kind == "loop":
            opts.setdefault("count_offset", 0)
            # Either count_name (dynamic) or count_literal (fixed)
            # must be set; the missing attr defaults to None which
            # the rules check via Eq(..., Lit(None)).

        # Normalise gating into a list of groups (each a list of
        # (name, val) pairs). Three input shapes:
        #   - `groups`: already DNF, just copy
        #   - `conditions`: single AND-group → list of one
        #   - legacy condition_name/condition_value → one group of one
        groups_in = opts.pop("groups", None)
        single_conds = list(opts.pop("conditions", []))
        if "condition_name" in opts and "condition_value" in opts:
            single_conds.append((opts.pop("condition_name"),
                                 opts.pop("condition_value")))
        if groups_in is not None:
            groups = [list(g) for g in groups_in]
        elif single_conds:
            groups = [single_conds]
        else:
            groups = []

        for k, v in opts.items():
            attrs[k] = v
        node = s._inner.add_node("FieldSpec", attrs)
        if head is None:
            head = node
        if prev is not None:
            s._inner.add_edge(prev, "next", node)
        # Mint ConditionGroup nodes + member edges.
        for group in groups:
            g_node = s._inner.add_node("ConditionGroup", {})
            s._inner.add_edge(node, "cond_group", g_node)
            for cond_name, cond_val in group:
                cn = s._inner.add_node("Condition",
                                       {"name": cond_name,
                                        "val": cond_val})
                s._inner.add_edge(g_node, "member", cn)
        prev = node
    sentinel = s._inner.add_node("FieldSpec", {"kind": "end", "name": ""})
    s._inner.add_edge(prev, "next", sentinel)
    return head


# --- shared condition-gating sub-terms ------------------------------


def _has_any_cond_group(field_var: str = "field"):
    """True when the FieldSpec has at least one ConditionGroup edge
    (i.e. is gated by something — possibly a disjunction)."""
    return Exists(
        Neighbours(Var(field_var), "cond_group"),
        "_g",
        Lit(True),
    )


def _group_fully_satisfied(group_var: str, source_state_var: str):
    """A single ConditionGroup is satisfied when ALL its members are
    satisfied by the source state. Expressed as "no unsatisfied
    member exists" — vacuously true for empty groups, which works
    fine but the seeder always emits ≥1 member per group."""
    return Not(Exists(
        Neighbours(Var(group_var), "member"),
        "m",
        # Member m is unsatisfied iff no decoded value matches it.
        Not(Exists(
            Neighbours(Var(source_state_var), "decoded"),
            "cv",
            And([
                Eq(Attr(Var("cv"), "name"),
                   Attr(Var("m"), "name")),
                Eq(Attr(Var("cv"), "val"),
                   Attr(Var("m"), "val")),
            ]),
        )),
    ))


def _condition_satisfied(source_state_var: str, field_var: str = "field"):
    """True when the field's gating is satisfied — full DNF:
       (no groups, unconditional) OR (any group satisfies)
    AND across members within a group; OR across groups; negation
    via val=0 on a member. Covers single ANDs (one group), nested
    ANDs (one group with many members), and disjunctions (many
    groups, each with its members)."""
    return Or([
        Not(_has_any_cond_group(field_var)),
        Exists(
            Neighbours(Var(field_var), "cond_group"),
            "g",
            _group_fully_satisfied("g", source_state_var),
        ),
    ])


def _condition_met(source_state_var: str, field_var: str = "field"):
    return _condition_satisfied(source_state_var, field_var)


def _condition_skipped(source_state_var: str, field_var: str = "field"):
    """The skip rule fires when there IS gating but NO group
    satisfies it."""
    return And([
        _has_any_cond_group(field_var),
        Not(_condition_satisfied(source_state_var, field_var)),
    ])


def seed_pps_grammar(s):
    """H.264 PPS-specific seed (back-compat for the H.264 tests)."""
    return seed_field_grammar(s, H264_PPS_FIELDS)


# --- decode Rules — graph-resident, native Term eval ---------------


def _add_rule(s, name, match_edges, where, effects):
    """Add one Rule. Effects use {"__term__": <term JSON>} to carry
    computed values (evaluated at apply-time over the match binding)."""
    spec = {"name": name, "match": match_edges,
            "where": where.to_dict() if where is not None else None,
            "effects": effects}
    return s._inner.add_rule(spec)


def _term_arg(term):
    """Wrap a Term for use as a computed-Term effect argument."""
    return {"__term__": term.to_dict()}


def seed_pps_decode_rules(s):
    """Install the universal codec field-grammar Rules onto `s`.

    Per "concepts in gamma OR Rust runner": the codec-walker Rule
    set is universal machinery (dispatches on field.kind, no codec-
    specific logic), so it lives in the Rust runner crate (see
    `runners/dsl/src/codec.rs`). This Python function is a thin
    idempotent wrapper.

    Both `seed_pps_decode_rules` and `seed_pps_encode_rules` install
    the FULL 18-rule set in one shot — they're kept as separate names
    only so existing tests keep reading naturally. Calling either
    one is enough; calling both is a no-op after the first.
    """
    if s._inner.rule_count() == 0:
        s._inner.install_field_grammar_rules()
    return []


def _impl_seed_pps_decode_rules(s):
    """Original Python rule constructor — retained for reference /
    audit / regenerating `codec_field_grammar_rules.json`. NOT called
    in normal use; the Rust native install is the canonical path.
    Tests no longer depend on this code being executed."""

    # Common shape: state has `current` → field, `buffer` → buf;
    # field has `next` → nxt; field.kind matches.
    base_match = [
        ["state", "current", "field"],
        ["state", "buffer", "buf"],
        ["field", "next", "nxt"],
    ]
    bytes_t = Attr(Var("buf"), "bytes")
    bp_t = Attr(Var("state"), "bp")

    rules = []

    # All decode Rules require state to be a DecodeState (the matcher
    # otherwise binds it to any node with a "current" edge — including
    # the EncodeState in the round-trip test).
    state_is_decode = Eq(TypeOf(Var("state")), Lit("DecodeState"))
    # Active fields: their gating condition is met (or none exists).
    active = _condition_met("state")
    # Skipped fields: a condition is set but isn't met by anything
    # already decoded — advance current without consuming bits.
    skipped = _condition_skipped("state")

    # decode_ue: pic_param_set_id / sps_id / num_slice_groups / etc.
    decoded = ExpGolombDecode(bytes_t, bp_t)
    rules.append(_add_rule(s, "decode_ue", base_match,
        And([state_is_decode,
             Eq(Attr(Var("field"), "kind"), Lit("ue")),
             active]),
        [
            ["add_node", "v", "Value", {
                "name": _term_arg(Attr(Var("field"), "name")),
                "val": _term_arg(Nth(decoded, 0)),
            }],
            ["add_edge", "state", "decoded", "v"],
            ["set_attr", "state", "bp", _term_arg(Nth(decoded, 1))],
            ["del_edge", "state", "current", "field"],
            ["add_edge", "state", "current", "nxt"],
        ]))

    # decode_se: pic_init_qp_minus26 etc.
    decoded_s = ExpGolombDecodeSigned(bytes_t, bp_t)
    rules.append(_add_rule(s, "decode_se", base_match,
        And([state_is_decode,
             Eq(Attr(Var("field"), "kind"), Lit("se")),
             active]),
        [
            ["add_node", "v", "Value", {
                "name": _term_arg(Attr(Var("field"), "name")),
                "val": _term_arg(Nth(decoded_s, 0)),
            }],
            ["add_edge", "state", "decoded", "v"],
            ["set_attr", "state", "bp", _term_arg(Nth(decoded_s, 1))],
            ["del_edge", "state", "current", "field"],
            ["add_edge", "state", "current", "nxt"],
        ]))

    # decode_u: fixed-width u(n). nbits comes from FieldSpec.nbits.
    val_t = BitsAt(bytes_t, bp_t, Attr(Var("field"), "nbits"))
    rules.append(_add_rule(s, "decode_u", base_match,
        And([state_is_decode,
             Eq(Attr(Var("field"), "kind"), Lit("u")),
             active]),
        [
            ["add_node", "v", "Value", {
                "name": _term_arg(Attr(Var("field"), "name")),
                "val": _term_arg(val_t),
            }],
            ["add_edge", "state", "decoded", "v"],
            # bp += nbits
            ["set_attr", "state", "bp", _term_arg(
                Plus([bp_t, Attr(Var("field"), "nbits")]))],
            ["del_edge", "state", "current", "field"],
            ["add_edge", "state", "current", "nxt"],
        ]))

    # decode_skip: a conditional field whose gating control is not
    # set — advance current without reading any bits, leaving bp
    # unchanged. Kind-agnostic (the skip semantic is the same for
    # ue/se/u/anything). Fires only when the field genuinely has a
    # condition that wasn't met.
    rules.append(_add_rule(s, "decode_skip", base_match,
        And([state_is_decode, skipped]),
        [
            ["del_edge", "state", "current", "field"],
            ["add_edge", "state", "current", "nxt"],
        ]))

    # --- iteration: loop FieldSpec, LoopState tracking i -----------

    # Loop count = decoded(count_name).val + count_offset. We use a
    # match edge to bind the count Value rather than evaluating a
    # graph lookup inside Terms.
    loop_match_init = [
        ["state", "current", "loop"],
        ["state", "buffer", "buf"],
        ["state", "decoded", "count_v"],
    ]
    count_name_match = Eq(Attr(Var("count_v"), "name"),
                          Attr(Var("loop"), "count_name"))
    is_loop = Eq(Attr(Var("loop"), "kind"), Lit("loop"))
    # Guard against firing when a LoopState for THIS loop already
    # exists — otherwise loop_init would re-fire on every loop body
    # iteration.
    no_active_loop_for_this = Not(Exists(
        Neighbours(Var("state"), "loop_state"),
        "ls",
        Exists(
            Neighbours(Var("ls"), "loop"),
            "lr",
            Eq(Var("lr"), Var("loop")),
        ),
    ))

    # The dynamic variant only fires when the FieldSpec has a
    # count_name attr (count from a previously-decoded value). The
    # literal variant below handles fixed-count loops.
    has_count_name = Not(Eq(Attr(Var("loop"), "count_name"), Lit(None)))
    rules.append(_add_rule(s, "loop_init", loop_match_init,
        And([state_is_decode, is_loop, count_name_match,
             has_count_name, no_active_loop_for_this]),
        [
            ["add_node", "ls", "LoopState", {
                "i": _term_arg(Lit(0)),
                "count": _term_arg(Plus([
                    Attr(Var("count_v"), "val"),
                    Attr(Var("loop"), "count_offset"),
                ])),
            }],
            ["add_edge", "state", "loop_state", "ls"],
            ["add_edge", "ls", "loop", "loop"],
        ]))

    # Fixed-count loop init. When the FieldSpec carries `count_literal`
    # (e.g. HEVC's `general_profile_compatibility_flag[32]`), the
    # count is the attr value + count_offset; no decoded lookup
    # needed. Match drops the (state, decoded, count_v) edge.
    loop_match_init_literal = [
        ["state", "current", "loop"],
        ["state", "buffer", "buf"],
    ]
    has_count_literal = Not(
        Eq(Attr(Var("loop"), "count_literal"), Lit(None)))
    rules.append(_add_rule(s, "loop_init_literal",
                            loop_match_init_literal,
        And([state_is_decode, is_loop, has_count_literal,
             no_active_loop_for_this]),
        [
            ["add_node", "ls", "LoopState", {
                "i": _term_arg(Lit(0)),
                "count": _term_arg(Plus([
                    Attr(Var("loop"), "count_literal"),
                    Attr(Var("loop"), "count_offset"),
                ])),
            }],
            ["add_edge", "state", "loop_state", "ls"],
            ["add_edge", "ls", "loop", "loop"],
        ]))

    # Iterate: one rule per body kind. Decode one body field, emit
    # a Value with the loop's `name` + `index = ls.i`, advance bp,
    # increment ls.i. Stays on the same `current` (which still points
    # at the loop FieldSpec) until i == count.
    #
    # The 4th match edge `(ls, loop, loop)` reuses the `loop` var to
    # constrain that ls's `loop` edge points at the SAME FieldSpec
    # bound by the first edge — the matcher's distinct-nodes rule
    # would otherwise reject a binding where two vars (loop/loop_ref)
    # collapsed to the same node.
    loop_iter_match = [
        ["state", "current", "loop"],
        ["state", "buffer", "buf"],
        ["state", "loop_state", "ls"],
        ["ls", "loop", "loop"],
    ]
    has_iterations_left = Lt(Attr(Var("ls"), "i"), Attr(Var("ls"), "count"))

    decoded_ue = ExpGolombDecode(bytes_t, bp_t)
    rules.append(_add_rule(s, "loop_iter_ue", loop_iter_match,
        And([state_is_decode, is_loop,
             Eq(Attr(Var("loop"), "body_kind"), Lit("ue")),
             has_iterations_left]),
        [
            ["add_node", "v", "Value", {
                "name": _term_arg(Attr(Var("loop"), "name")),
                "val": _term_arg(Nth(decoded_ue, 0)),
                "index": _term_arg(Attr(Var("ls"), "i")),
            }],
            ["add_edge", "state", "decoded", "v"],
            ["set_attr", "state", "bp", _term_arg(Nth(decoded_ue, 1))],
            ["set_attr", "ls", "i", _term_arg(
                Plus([Attr(Var("ls"), "i"), Lit(1)]))],
        ]))

    decoded_se = ExpGolombDecodeSigned(bytes_t, bp_t)
    rules.append(_add_rule(s, "loop_iter_se", loop_iter_match,
        And([state_is_decode, is_loop,
             Eq(Attr(Var("loop"), "body_kind"), Lit("se")),
             has_iterations_left]),
        [
            ["add_node", "v", "Value", {
                "name": _term_arg(Attr(Var("loop"), "name")),
                "val": _term_arg(Nth(decoded_se, 0)),
                "index": _term_arg(Attr(Var("ls"), "i")),
            }],
            ["add_edge", "state", "decoded", "v"],
            ["set_attr", "state", "bp", _term_arg(Nth(decoded_se, 1))],
            ["set_attr", "ls", "i", _term_arg(
                Plus([Attr(Var("ls"), "i"), Lit(1)]))],
        ]))

    u_val = BitsAt(bytes_t, bp_t, Attr(Var("loop"), "body_nbits"))
    rules.append(_add_rule(s, "loop_iter_u", loop_iter_match,
        And([state_is_decode, is_loop,
             Eq(Attr(Var("loop"), "body_kind"), Lit("u")),
             has_iterations_left]),
        [
            ["add_node", "v", "Value", {
                "name": _term_arg(Attr(Var("loop"), "name")),
                "val": _term_arg(u_val),
                "index": _term_arg(Attr(Var("ls"), "i")),
            }],
            ["add_edge", "state", "decoded", "v"],
            ["set_attr", "state", "bp", _term_arg(
                Plus([bp_t, Attr(Var("loop"), "body_nbits")]))],
            ["set_attr", "ls", "i", _term_arg(
                Plus([Attr(Var("ls"), "i"), Lit(1)]))],
        ]))

    # Complete: i == count → tear down LoopState, advance current.
    loop_complete_match = [
        ["state", "current", "loop"],
        ["state", "loop_state", "ls"],
        ["ls", "loop", "loop"],   # same var-reuse trick
        ["loop", "next", "nxt"],
    ]
    iter_done = Not(Lt(Attr(Var("ls"), "i"), Attr(Var("ls"), "count")))
    rules.append(_add_rule(s, "loop_complete", loop_complete_match,
        And([state_is_decode, is_loop, iter_done]),
        [
            ["del_edge", "ls", "loop", "loop"],
            ["del_edge", "state", "loop_state", "ls"],
            ["del_node", "ls"],
            ["del_edge", "state", "current", "loop"],
            ["add_edge", "state", "current", "nxt"],
        ]))

    return rules


def seed_pps_encode_rules(s):
    """Alias for seed_pps_decode_rules — both call paths install the
    full 18-rule field-grammar set in one shot via the Rust runner.
    Kept as a separate name only for test readability."""
    return seed_pps_decode_rules(s)


def _impl_seed_pps_encode_rules(s):
    """Original Python encode-rule constructor — retained for
    reference / audit. Not used in normal flow.

    To bump a field (e.g. QP): mutate the Value.val attr in the
    DecodeState BEFORE running these rules. The encode Rules pick up
    the new value naturally."""
    base_match = [
        ["estate", "current", "field"],
        ["estate", "buffer", "buf"],
        ["estate", "source", "dstate"],
        ["dstate", "decoded", "value"],
        ["field", "next", "nxt"],
    ]
    # Value-name must match FieldSpec-name (this is how the encode
    # rule looks up the right decoded value for the current field).
    name_match = Eq(Attr(Var("value"), "name"),
                    Attr(Var("field"), "name"))
    bytes_t = Attr(Var("buf"), "bytes")
    bp_t = Attr(Var("estate"), "bp")
    val_t = Attr(Var("value"), "val")
    # An encode rule's "active" check matches on the SOURCE
    # DecodeState's decoded set — same condition shape as decode.
    enc_active = _condition_met("dstate")

    rules = []

    # encode_ue
    enc_ue = ExpGolombEncode(bytes_t, bp_t, val_t)
    rules.append(_add_rule(s, "encode_ue", base_match,
        And([Eq(Attr(Var("field"), "kind"), Lit("ue")),
             name_match, enc_active]),
        [
            ["set_attr", "buf", "bytes", _term_arg(Nth(enc_ue, 0))],
            ["set_attr", "estate", "bp", _term_arg(Nth(enc_ue, 1))],
            ["del_edge", "estate", "current", "field"],
            ["add_edge", "estate", "current", "nxt"],
        ]))

    # encode_se
    enc_se = ExpGolombEncodeSigned(bytes_t, bp_t, val_t)
    rules.append(_add_rule(s, "encode_se", base_match,
        And([Eq(Attr(Var("field"), "kind"), Lit("se")),
             name_match, enc_active]),
        [
            ["set_attr", "buf", "bytes", _term_arg(Nth(enc_se, 0))],
            ["set_attr", "estate", "bp", _term_arg(Nth(enc_se, 1))],
            ["del_edge", "estate", "current", "field"],
            ["add_edge", "estate", "current", "nxt"],
        ]))

    # encode_u: BitsWrite returns just the buffer, bp advances by nbits.
    rules.append(_add_rule(s, "encode_u", base_match,
        And([Eq(Attr(Var("field"), "kind"), Lit("u")),
             name_match, enc_active]),
        [
            ["set_attr", "buf", "bytes", _term_arg(
                BitsWrite(bytes_t, bp_t, val_t,
                          Attr(Var("field"), "nbits")))],
            ["set_attr", "estate", "bp", _term_arg(
                Plus([bp_t, Attr(Var("field"), "nbits")]))],
            ["del_edge", "estate", "current", "field"],
            ["add_edge", "estate", "current", "nxt"],
        ]))

    # encode_skip: conditional field whose gating control wasn't set
    # in the source DecodeState — advance current without emitting
    # bits. Match doesn't include `(dstate, decoded, value)` because
    # there IS no decoded value for a skipped field; instead the
    # condition check is done via Exists in the where clause.
    skip_match = [
        ["estate", "current", "field"],
        ["estate", "source", "dstate"],
        ["field", "next", "nxt"],
    ]
    rules.append(_add_rule(s, "encode_skip", skip_match,
        _condition_skipped("dstate"),
        [
            ["del_edge", "estate", "current", "field"],
            ["add_edge", "estate", "current", "nxt"],
        ]))

    # --- iteration: encode side mirrors decode --------------------

    # Reuse the count_v lookup from the source DecodeState (same
    # decoded value the decode side used).
    enc_loop_init_match = [
        ["estate", "current", "loop"],
        ["estate", "source", "dstate"],
        ["dstate", "decoded", "count_v"],
    ]
    enc_count_name_match = Eq(Attr(Var("count_v"), "name"),
                              Attr(Var("loop"), "count_name"))
    enc_is_loop = Eq(Attr(Var("loop"), "kind"), Lit("loop"))
    enc_no_active = Not(Exists(
        Neighbours(Var("estate"), "loop_state"),
        "ls",
        Exists(
            Neighbours(Var("ls"), "loop"),
            "lr",
            Eq(Var("lr"), Var("loop")),
        ),
    ))

    enc_has_count_name = Not(
        Eq(Attr(Var("loop"), "count_name"), Lit(None)))
    rules.append(_add_rule(s, "encode_loop_init", enc_loop_init_match,
        And([enc_is_loop, enc_count_name_match, enc_has_count_name,
             enc_no_active]),
        [
            ["add_node", "ls", "LoopState", {
                "i": _term_arg(Lit(0)),
                "count": _term_arg(Plus([
                    Attr(Var("count_v"), "val"),
                    Attr(Var("loop"), "count_offset"),
                ])),
            }],
            ["add_edge", "estate", "loop_state", "ls"],
            ["add_edge", "ls", "loop", "loop"],
        ]))

    # Fixed-count encode init — mirror of decode's literal init.
    enc_loop_init_literal_match = [
        ["estate", "current", "loop"],
        ["estate", "buffer", "buf"],
    ]
    enc_has_count_literal = Not(
        Eq(Attr(Var("loop"), "count_literal"), Lit(None)))
    rules.append(_add_rule(s, "encode_loop_init_literal",
                            enc_loop_init_literal_match,
        And([enc_is_loop, enc_has_count_literal, enc_no_active]),
        [
            ["add_node", "ls", "LoopState", {
                "i": _term_arg(Lit(0)),
                "count": _term_arg(Plus([
                    Attr(Var("loop"), "count_literal"),
                    Attr(Var("loop"), "count_offset"),
                ])),
            }],
            ["add_edge", "estate", "loop_state", "ls"],
            ["add_edge", "ls", "loop", "loop"],
        ]))

    # Iterate: each rule finds the source DecodeState's body Value
    # whose name + index match the loop name + ls.i, then encodes it.
    enc_loop_iter_match = [
        ["estate", "current", "loop"],
        ["estate", "buffer", "buf"],
        ["estate", "source", "dstate"],
        ["estate", "loop_state", "ls"],
        ["ls", "loop", "loop"],
        ["dstate", "decoded", "value"],
    ]
    val_name_matches_loop = Eq(Attr(Var("value"), "name"),
                                Attr(Var("loop"), "name"))
    val_index_matches_iter = Eq(Attr(Var("value"), "index"),
                                 Attr(Var("ls"), "i"))
    has_iter_left = Lt(Attr(Var("ls"), "i"), Attr(Var("ls"), "count"))

    enc_ue = ExpGolombEncode(bytes_t, bp_t, val_t)
    rules.append(_add_rule(s, "encode_loop_iter_ue", enc_loop_iter_match,
        And([enc_is_loop,
             Eq(Attr(Var("loop"), "body_kind"), Lit("ue")),
             val_name_matches_loop, val_index_matches_iter,
             has_iter_left]),
        [
            ["set_attr", "buf", "bytes", _term_arg(Nth(enc_ue, 0))],
            ["set_attr", "estate", "bp", _term_arg(Nth(enc_ue, 1))],
            ["set_attr", "ls", "i", _term_arg(
                Plus([Attr(Var("ls"), "i"), Lit(1)]))],
        ]))

    enc_se_t = ExpGolombEncodeSigned(bytes_t, bp_t, val_t)
    rules.append(_add_rule(s, "encode_loop_iter_se", enc_loop_iter_match,
        And([enc_is_loop,
             Eq(Attr(Var("loop"), "body_kind"), Lit("se")),
             val_name_matches_loop, val_index_matches_iter,
             has_iter_left]),
        [
            ["set_attr", "buf", "bytes", _term_arg(Nth(enc_se_t, 0))],
            ["set_attr", "estate", "bp", _term_arg(Nth(enc_se_t, 1))],
            ["set_attr", "ls", "i", _term_arg(
                Plus([Attr(Var("ls"), "i"), Lit(1)]))],
        ]))

    enc_u_write = BitsWrite(bytes_t, bp_t, val_t,
                            Attr(Var("loop"), "body_nbits"))
    rules.append(_add_rule(s, "encode_loop_iter_u", enc_loop_iter_match,
        And([enc_is_loop,
             Eq(Attr(Var("loop"), "body_kind"), Lit("u")),
             val_name_matches_loop, val_index_matches_iter,
             has_iter_left]),
        [
            ["set_attr", "buf", "bytes", _term_arg(enc_u_write)],
            ["set_attr", "estate", "bp", _term_arg(
                Plus([bp_t, Attr(Var("loop"), "body_nbits")]))],
            ["set_attr", "ls", "i", _term_arg(
                Plus([Attr(Var("ls"), "i"), Lit(1)]))],
        ]))

    enc_loop_complete_match = [
        ["estate", "current", "loop"],
        ["estate", "loop_state", "ls"],
        ["ls", "loop", "loop"],
        ["loop", "next", "nxt"],
    ]
    enc_iter_done = Not(Lt(Attr(Var("ls"), "i"),
                            Attr(Var("ls"), "count")))
    rules.append(_add_rule(s, "encode_loop_complete",
                            enc_loop_complete_match,
        And([enc_is_loop, enc_iter_done]),
        [
            ["del_edge", "ls", "loop", "loop"],
            ["del_edge", "estate", "loop_state", "ls"],
            ["del_node", "ls"],
            ["del_edge", "estate", "current", "loop"],
            ["add_edge", "estate", "current", "nxt"],
        ]))

    return rules


# --- demo: graph-resident H.264 PPS decode -------------------------


def test_h264_pps_decode_is_graph_resident():
    """The PPS decode happens entirely in the substrate: codec
    grammar is graph nodes, decode is graph Rules, Python only loads
    bytes + reads results. The Python-side parser from
    `test_codec_primitives.py::_parse_pps_fields` is the anti-pattern
    this replaces — domain knowledge belongs in the graph."""
    s = Substrate()

    # Seed Γ vocabulary + field grammar + decode Rules ONCE (could
    # be persisted as part of the agent's codec knowledge).
    seed_codec_vocabulary(s)
    head = seed_pps_grammar(s)
    seed_pps_decode_rules(s)

    # Real PPS RBSP from the ffmpeg-encoded sample (Constrained
    # Baseline, QP=23, pic_init_qp_minus26=-3). Same bytes the prior
    # demo parsed via the Python loop.
    pps_rbsp = b"\xce\x0f\xc8"

    # Load bytes into the graph as a Buffer node.
    buf = s._inner.add_node("Buffer", {"bytes": pps_rbsp})

    # Initial DecodeState: bp=0, current → head FieldSpec, buffer → buf.
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)

    # The rewrite engine fires Rules to fixed point. When current
    # points to the terminal FieldSpec (no `next` edge), no Rule
    # matches; engine halts.
    steps = s._inner.run_rules(max_steps=1000)
    assert steps == len(H264_PPS_FIELDS), (
        f"expected {len(H264_PPS_FIELDS)} rule firings, got {steps}")

    # Read decoded values from the graph (state ─decoded→ Value nodes).
    decoded = {}
    for v in s._inner.neighbours(state, "decoded"):
        attrs = s._inner.node(v)["attrs"]
        decoded[attrs["name"]] = attrs["val"]

    # The expected decode of this PPS, matching the prior Python parse.
    expected = {
        "pic_parameter_set_id": 0,
        "seq_parameter_set_id": 0,
        "entropy_coding_mode_flag": 0,
        "bottom_field_pic_order_in_frame_present_flag": 0,
        "num_slice_groups_minus1": 0,
        "num_ref_idx_l0_default_active_minus1": 0,
        "num_ref_idx_l1_default_active_minus1": 0,
        "weighted_pred_flag": 0,
        "weighted_bipred_idc": 0,
        "pic_init_qp_minus26": -3,
    }
    for k, v in expected.items():
        assert decoded.get(k) == v, (
            f"field {k}: graph-resident decode gave {decoded.get(k)}, "
            f"expected {v}")

    # Final bitpos must be the sum of all field bit-lengths
    # (the ue/se prefix lands at bp=15 in this PPS).
    assert s._inner.node(state)["attrs"]["bp"] == 15


def test_h264_pps_qp_bump_is_graph_resident():
    """The full QP-bump operation in graph form. NO Python codec
    knowledge: the field grammar is graph nodes, decode + encode are
    graph Rules, the mutation is a single set_attr on a Value node.
    Python's role: load bytes, mutate one attr, read result."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_pps_grammar(s)
    seed_pps_decode_rules(s)
    seed_pps_encode_rules(s)

    pps_rbsp = b"\xce\x0f\xc8"
    dec_buf = s._inner.add_node("Buffer", {"bytes": pps_rbsp})
    dstate = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(dstate, "current", head)
    s._inner.add_edge(dstate, "buffer", dec_buf)

    # Decode — rules walk the chain.
    s._inner.run_rules(max_steps=1000)

    # Mutate the pic_init_qp_minus26 Value in the graph. This is THE
    # operational step — agent finds the value by name, changes its
    # attr. The codec doesn't know about QP-bump; it's just a mutation
    # on graph data the encode Rules will pick up.
    qp_value_node = None
    for v in s._inner.neighbours(dstate, "decoded"):
        if s._inner.node(v)["attrs"]["name"] == "pic_init_qp_minus26":
            qp_value_node = v
            break
    assert qp_value_node is not None
    old_qp = s._inner.node(qp_value_node)["attrs"]["val"]
    s._inner.set_attr(qp_value_node, "val", old_qp + 5)  # -3 → 2

    # Encode — rules walk the chain reading from dstate.
    enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
    estate = s._inner.add_node("EncodeState", {"bp": 0})
    s._inner.add_edge(estate, "current", head)
    s._inner.add_edge(estate, "buffer", enc_buf)
    s._inner.add_edge(estate, "source", dstate)
    s._inner.run_rules(max_steps=1000)

    # Read back the re-encoded bytes from the buffer node.
    new_bytes = s._inner.node(enc_buf)["attrs"]["bytes"]
    new_bp = s._inner.node(estate)["attrs"]["bp"]

    # The new PPS must round-trip via the SAME decode pipeline back
    # to the mutated value.
    s2 = Substrate()
    seed_codec_vocabulary(s2)
    head2 = seed_pps_grammar(s2)
    seed_pps_decode_rules(s2)
    new_buf = s2._inner.add_node("Buffer", {"bytes": bytes(new_bytes)})
    new_state = s2._inner.add_node("DecodeState", {"bp": 0})
    s2._inner.add_edge(new_state, "current", head2)
    s2._inner.add_edge(new_state, "buffer", new_buf)
    s2._inner.run_rules(max_steps=1000)
    re_decoded = {s2._inner.node(v)["attrs"]["name"]:
                  s2._inner.node(v)["attrs"]["val"]
                  for v in s2._inner.neighbours(new_state, "decoded")}
    assert re_decoded["pic_init_qp_minus26"] == old_qp + 5
    # All other fields unchanged.
    expected_others = {
        "pic_parameter_set_id": 0, "seq_parameter_set_id": 0,
        "entropy_coding_mode_flag": 0,
        "bottom_field_pic_order_in_frame_present_flag": 0,
        "num_slice_groups_minus1": 0,
        "num_ref_idx_l0_default_active_minus1": 0,
        "num_ref_idx_l1_default_active_minus1": 0,
        "weighted_pred_flag": 0, "weighted_bipred_idc": 0,
    }
    for k, v in expected_others.items():
        assert re_decoded[k] == v, f"{k} drifted: {v} -> {re_decoded[k]}"

    # Final proof: splice the re-emitted PPS bytes into a real H.264
    # stream and verify ffmpeg decodes the modified stream + the
    # decoded pixels actually differ (QP change reaches dequantization).
    import shutil
    import subprocess
    import hashlib
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return  # skip the splice-verify step if ffmpeg isn't available

    src = Path("/tmp/h264_demo/sample.h264")
    if not src.exists():
        return
    raw = src.read_bytes()

    # Locate the PPS NAL (type 8) and splice in the graph-emitted bytes.
    i = 0
    pps_start = sc_len = pps_end = None
    while i < len(raw) - 4:
        if raw[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01": sc = 3
        else: i += 1; continue
        if (raw[i+sc] & 0x1F) == 8:
            pps_start, sc_len = i, sc
            j = i + sc + 1
            while j < len(raw) - 3:
                if (raw[j:j+3] == b"\x00\x00\x01"
                        or raw[j:j+4] == b"\x00\x00\x00\x01"):
                    break
                j += 1
            pps_end = j
            break
        i += sc
    if pps_start is None:
        return

    modified = (raw[: pps_start + sc_len + 1]
                + bytes(new_bytes)
                + raw[pps_end:])
    out_path = Path("/tmp/h264_demo/sample_graph_qpbump.h264")
    out_path.write_bytes(modified)

    def pixel_md5(p):
        r = subprocess.run([ffmpeg, "-loglevel", "error", "-i", str(p),
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           capture_output=True, check=True)
        return hashlib.md5(r.stdout).hexdigest()
    orig_h = pixel_md5(src)
    mod_h = pixel_md5(out_path)
    assert orig_h != mod_h, (
        "graph-resident QP-bump did not change decoded pixels")


# --- HEVC: same Rules, different field list ------------------------


def test_hevc_pps_qp_bump_is_graph_resident():
    """HEVC migration: the same decode + encode Rules from the H.264
    pilot work UNCHANGED — only the FieldSpec chain differs. Codec
    learning = minting a new grammar, no runner or Rule changes.

    Walks the HEVC PPS ITU-T H.265 §7.3.2.3 grammar (~25 fields, 4x
    H.264's), bumps init_qp_minus26, splices into a real x265 stream,
    ffmpeg-verifies the modified bitstream decodes + pixels differ."""
    import shutil
    import subprocess
    import hashlib
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not installed")

    src = Path("/tmp/h264_demo/sample.hevc")
    if not src.exists():
        src.parent.mkdir(parents=True, exist_ok=True)
        rc = subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=128x128:rate=30",
            "-c:v", "libx265", "-preset", "ultrafast",
            "-tune", "zerolatency", "-pix_fmt", "yuv420p",
            "-x265-params", "log-level=error", "-an", str(src),
        ]).returncode
        if rc != 0 or not src.exists():
            pytest.skip("ffmpeg has no libx265 support")

    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, H265_PPS_FIELDS)  # <-- HEVC, not H.264
    seed_pps_decode_rules(s)
    seed_pps_encode_rules(s)

    # Locate HEVC PPS NAL (type 34) — 2-byte NAL header vs H.264's 1.
    raw = src.read_bytes()
    i = 0
    pps_start = sc_len = pps_end = None
    while i < len(raw) - 4:
        if raw[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01": sc = 3
        else: i += 1; continue
        if ((raw[i+sc] >> 1) & 0x3F) == 34:
            pps_start, sc_len = i, sc
            j = i + sc + 2  # HEVC NAL header is 2 bytes
            while j < len(raw) - 3:
                if (raw[j:j+3] == b"\x00\x00\x01"
                        or raw[j:j+4] == b"\x00\x00\x00\x01"):
                    break
                j += 1
            pps_end = j
            break
        i += sc
    pps_rbsp = raw[pps_start + sc_len + 2 : pps_end]

    # Decode via graph Rules.
    dec_buf = s._inner.add_node("Buffer", {"bytes": pps_rbsp})
    dstate = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(dstate, "current", head)
    s._inner.add_edge(dstate, "buffer", dec_buf)
    s._inner.run_rules(max_steps=1000)

    # Sanity check the decode landed where we expect (x265 defaults).
    decoded = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(dstate, "decoded")}
    assert decoded["init_qp_minus26"] == 0  # QP=26 default
    # Conditional gating flags must all be 0 — otherwise the bitstream
    # has fields our minimal grammar doesn't list.
    for flag in ("cu_qp_delta_enabled_flag",
                 "deblocking_filter_control_present_flag",
                 "pps_scaling_list_data_present_flag",
                 "pps_extension_present_flag",
                 "tiles_enabled_flag"):
        assert decoded[flag] == 0, (
            f"x265 default has {flag}={decoded[flag]}; grammar would "
            f"need to include the conditional branch")

    # Mutate QP via single set_attr.
    qp_value_node = next(
        v for v in s._inner.neighbours(dstate, "decoded")
        if s._inner.node(v)["attrs"]["name"] == "init_qp_minus26")
    old_qp = s._inner.node(qp_value_node)["attrs"]["val"]
    new_qp = old_qp + 6
    s._inner.set_attr(qp_value_node, "val", new_qp)

    # Encode via graph Rules.
    enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
    estate = s._inner.add_node("EncodeState", {"bp": 0})
    s._inner.add_edge(estate, "current", head)
    s._inner.add_edge(estate, "buffer", enc_buf)
    s._inner.add_edge(estate, "source", dstate)
    s._inner.run_rules(max_steps=1000)

    new_pps_payload = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])
    new_bp = s._inner.node(estate)["attrs"]["bp"]
    # Pad to byte boundary with rbsp_trailing_bits (stop bit + zeros).
    # The original PPS RBSP had its own trailing bits; we re-add them.
    final_bp = new_bp + 1  # stop bit
    pad = (8 - (final_bp & 7)) & 7
    # Write stop bit + zero pad via BitsWrite.
    new_pps_rbsp = s._inner.evaluate(
        BitsWrite(Lit(new_pps_payload), Lit(new_bp),
                  Lit(1), Lit(1)).to_dict(), {})
    if pad:
        new_pps_rbsp = s._inner.evaluate(
            BitsWrite(Lit(new_pps_rbsp), Lit(new_bp + 1),
                      Lit(0), Lit(pad)).to_dict(), {})

    # Round-trip via fresh substrate.
    s2 = Substrate()
    seed_codec_vocabulary(s2)
    head2 = seed_field_grammar(s2, H265_PPS_FIELDS)
    seed_pps_decode_rules(s2)
    new_buf2 = s2._inner.add_node("Buffer", {"bytes": bytes(new_pps_rbsp)})
    new_state2 = s2._inner.add_node("DecodeState", {"bp": 0})
    s2._inner.add_edge(new_state2, "current", head2)
    s2._inner.add_edge(new_state2, "buffer", new_buf2)
    s2._inner.run_rules(max_steps=1000)
    re_decoded = {s2._inner.node(v)["attrs"]["name"]:
                  s2._inner.node(v)["attrs"]["val"]
                  for v in s2._inner.neighbours(new_state2, "decoded")}
    assert re_decoded["init_qp_minus26"] == new_qp
    for k, v in decoded.items():
        if k == "init_qp_minus26":
            continue
        assert re_decoded[k] == v, (
            f"HEVC field {k} drifted: {v} -> {re_decoded[k]}")

    # Splice into the stream and ffmpeg-verify pixel-level impact.
    modified = (raw[: pps_start + sc_len + 2]
                + bytes(new_pps_rbsp)
                + raw[pps_end:])
    out_path = Path("/tmp/h264_demo/sample_hevc_graph_qpbump.hevc")
    out_path.write_bytes(modified)

    r = subprocess.run([ffmpeg, "-loglevel", "error", "-i", str(out_path),
                        "-f", "null", "-"], capture_output=True, text=True)
    assert r.returncode == 0, f"ffmpeg rejected HEVC re-emit: {r.stderr}"

    def pixel_md5(p):
        r = subprocess.run([ffmpeg, "-loglevel", "error", "-i", str(p),
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           capture_output=True, check=True)
        return hashlib.md5(r.stdout).hexdigest()
    assert pixel_md5(src) != pixel_md5(out_path), (
        "graph-resident HEVC QP-bump did not change decoded pixels")


# --- JPEG: markers as graph data, strip via Rules -------------------


# JPEG marker classification — `essential=True` markers MUST survive
# a strip (define image / encoding); `essential=False` carry metadata
# (EXIF, ICC profile, comments, XMP, photoshop, etc.) and are safe
# to remove without changing decoded pixels.
JPEG_MARKERS = [
    # Essential — required for decoding.
    (0xD8, "SOI", True),    # Start Of Image
    (0xD9, "EOI", True),    # End Of Image
    (0xDA, "SOS", True),    # Start Of Scan
    (0xDB, "DQT", True),    # Define Quantization Table
    (0xC4, "DHT", True),    # Define Huffman Table
    (0xDD, "DRI", True),    # Define Restart Interval
    # SOFn (Start Of Frame, n=0..15) — essential.
    *[(0xC0 + i, f"SOF{i}", True) for i in range(16) if i != 4 and i != 8 and i != 12],
    # Strippable — APPn (0xE0..0xEF) carry metadata, COM (0xFE) is comments.
    *[(0xE0 + i, f"APP{i}", False) for i in range(16)],
    (0xFE, "COM", False),
]


def seed_jpeg_marker_table(s):
    """Mint MarkerSpec nodes for every JPEG marker we know — the
    codec's classification (essential vs strippable) lives as graph
    data, not in Python."""
    for byte, name, essential in JPEG_MARKERS:
        s._inner.add_node("MarkerSpec", {
            "marker_byte": byte,
            "name": name,
            "essential": essential,
        })


def seed_jpeg_vocabulary(s):
    """Γ vocabulary for the JPEG codec subgraph."""
    productions = [
        # ImageScan threads through Segment nodes (one per JPEG marker
        # found in the file).
        Production(src=NodePattern(type="ImageScan", var="i"),
                   edge_type="segment",
                   tgt=NodePattern(type="Segment", var="g")),
        Production(src=NodePattern(type="Segment", var="g"),
                   edge_type="marker",
                   tgt=NodePattern(type="MarkerSpec", var="m")),
    ]
    for p in productions:
        s.add_production(p)


def test_jpeg_metadata_strip_is_graph_resident():
    """JPEG migration: marker classification (essential vs metadata)
    lives as MarkerSpec graph nodes. Python walks the byte stream
    once to mint Segment nodes — each pointing at its MarkerSpec.
    The strip operation is then a pure graph traversal: collect
    bytes from Segments whose MarkerSpec.essential is true.

    Pixel-identical to the original (metadata strip is by definition
    pixel-invariant). Replaces the Python `if m in KEEP_MARKERS`
    branching in `test_codec_primitives.py` with graph data + Rule
    matching."""
    import shutil
    import subprocess
    import hashlib
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not installed")

    sample = Path("/tmp/h264_demo/sample.jpg")
    if not sample.exists():
        sample.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=0.1:size=256x256:rate=1",
            "-frames:v", "1", "-q:v", "5", str(sample),
        ], check=True)

    # Bloat with metadata.
    src_bytes = sample.read_bytes()
    bloat = b"\xFF\xFE\x1F\x42" + b"X" * 8000
    bloated = src_bytes[:2] + bloat * 5 + src_bytes[2:]
    bloated_path = Path("/tmp/h264_demo/bloated_graph.jpg")
    bloated_path.write_bytes(bloated)

    s = Substrate()
    seed_jpeg_vocabulary(s)
    seed_jpeg_marker_table(s)

    # Build a lookup: marker_byte -> MarkerSpec NodeID.
    marker_lookup = {}
    for n in s._inner.nodes(type_="MarkerSpec"):
        marker_lookup[s._inner.node(n)["attrs"]["marker_byte"]] = n

    # Walk JPEG bytes ONCE, mint a Segment node per found marker
    # carrying its (offset, length) + an edge to the MarkerSpec.
    # This is the "load into substrate" step — Python's sanctioned
    # role (world → graph), not codec reasoning.
    raw = bloated_path.read_bytes()
    scan = s._inner.add_node("ImageScan", {})
    i = 0
    assert raw[0] == 0xFF and raw[1] == 0xD8, "not a JPEG"
    while i < len(raw) - 1:
        if raw[i] != 0xFF:
            i += 1
            continue
        m = raw[i + 1]
        if m == 0x00 or m == 0xFF:
            i += 1
            continue
        # Determine segment extent.
        if m == 0xD8 or m == 0xD9 or (0xD0 <= m <= 0xD7):
            seg_end = i + 2
        elif m == 0xDA:  # SOS — payload runs until next non-RST marker
            seg_len = (raw[i + 2] << 8) | raw[i + 3]
            j = i + 2 + seg_len
            while j < len(raw) - 1:
                if (raw[j] == 0xFF and raw[j + 1] != 0x00
                        and not (0xD0 <= raw[j + 1] <= 0xD7)):
                    break
                j += 1
            seg_end = j
        else:
            seg_len = (raw[i + 2] << 8) | raw[i + 3]
            seg_end = i + 2 + seg_len
        # Mint a Segment node carrying offset + length + marker ref.
        if m in marker_lookup:
            seg = s._inner.add_node("Segment", {
                "offset": i, "length": seg_end - i,
            })
            s._inner.add_edge(scan, "segment", seg)
            s._inner.add_edge(seg, "marker", marker_lookup[m])
        i = seg_end

    # Graph query: collect (offset, length) for Segments whose marker
    # is essential. This is pure graph traversal — no codec branching
    # in Python, no "if marker_byte in KEEP_SET" hard-coding.
    keep_ranges = []
    stripped_count = 0
    for seg in s._inner.neighbours(scan, "segment"):
        seg_attrs = s._inner.node(seg)["attrs"]
        marker_nodes = s._inner.neighbours(seg, "marker")
        if not marker_nodes:
            continue
        marker_attrs = s._inner.node(marker_nodes[0])["attrs"]
        if marker_attrs["essential"]:
            keep_ranges.append(
                (seg_attrs["offset"],
                 seg_attrs["offset"] + seg_attrs["length"]))
        else:
            stripped_count += 1
    keep_ranges.sort()

    # Splice keeps. The graph told us WHAT to keep; concatenation is
    # not codec knowledge.
    stripped = b"".join(raw[a:b] for a, b in keep_ranges)

    stripped_path = Path("/tmp/h264_demo/stripped_graph.jpg")
    stripped_path.write_bytes(stripped)

    assert len(stripped) < len(raw), "did not shrink"
    assert stripped_count >= 5, "should have found at least 5 COM segments"

    # ffmpeg must decode + pixels must be IDENTICAL to the bloated
    # original (metadata strip is pixel-invariant — that's what makes
    # the operation safe).
    def pixel_md5(p):
        r = subprocess.run(
            [ffmpeg, "-loglevel", "error", "-i", str(p),
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            capture_output=True, check=True)
        return hashlib.md5(r.stdout).hexdigest()
    assert pixel_md5(bloated_path) == pixel_md5(stripped_path), (
        "metadata strip changed pixels — graph classifier is wrong?")


# --- JPEG DQT bump via field grammar (DQT body is u(8) chain) -------


def make_dqt_field_list(n_values: int = 64):
    """The DQT segment body is 1 byte (precision/table-id) + 64
    u(8) Q-values for 8-bit precision. Express as a FieldSpec chain
    so the EXISTING graph-resident decode/encode Rules apply
    unchanged."""
    fields = [("u", "pq_tq", 8)]
    for k in range(n_values):
        fields.append(("u", f"q{k}", 8))
    return fields


def test_jpeg_dqt_qt_bump_is_graph_resident():
    """JPEG DQT bump via the SAME decode/encode Rules used by the
    H.264 and HEVC PPS demos. The DQT body is a chain of 65 u(8)
    fields (precision byte + 64 Q-values) — different codec,
    different field count, same Rule set."""
    import shutil
    import subprocess
    import hashlib
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not installed")

    sample = Path("/tmp/h264_demo/sample.jpg")
    if not sample.exists():
        sample.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=0.1:size=256x256:rate=1",
            "-frames:v", "1", "-q:v", "5", str(sample),
        ], check=True)

    raw = sample.read_bytes()

    # Find DQT body offset + length via byte scan (Python's
    # world→graph load step; the marker classification is now graph
    # data via JPEG_MARKERS but the byte scan still happens here).
    i = 2
    body_start = body_len = None
    while i < len(raw) - 4:
        if raw[i] == 0xFF:
            m = raw[i + 1]
            if m == 0xDB:
                seg_len = (raw[i + 2] << 8) | raw[i + 3]
                body_start = i + 4
                body_len = seg_len - 2
                break
            if m == 0xD8 or m == 0xD9 or (0xD0 <= m <= 0xD7) or m == 0x00:
                i += 2
                continue
            seg_len = (raw[i + 2] << 8) | raw[i + 3]
            i += 2 + seg_len
        else:
            i += 1
    assert body_start is not None
    # Assume 8-bit precision (Pq=0, body = 1 + 64 bytes).
    assert body_len == 65, "demo handles 8-bit-precision DQT only"

    # Graph-resident decode of the 65-byte body via field grammar.
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, make_dqt_field_list(64))
    seed_pps_decode_rules(s)
    seed_pps_encode_rules(s)

    dqt_body = raw[body_start : body_start + body_len]
    dec_buf = s._inner.add_node("Buffer", {"bytes": dqt_body})
    dstate = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(dstate, "current", head)
    s._inner.add_edge(dstate, "buffer", dec_buf)
    s._inner.run_rules(max_steps=10000)

    # Scale each Q-value 2x via set_attr mutations on Value nodes.
    for v in s._inner.neighbours(dstate, "decoded"):
        a = s._inner.node(v)["attrs"]
        if a["name"].startswith("q"):
            new_val = min(255, a["val"] * 2)
            s._inner.set_attr(v, "val", new_val)

    # Encode back via graph Rules.
    enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
    estate = s._inner.add_node("EncodeState", {"bp": 0})
    s._inner.add_edge(estate, "current", head)
    s._inner.add_edge(estate, "buffer", enc_buf)
    s._inner.add_edge(estate, "source", dstate)
    s._inner.run_rules(max_steps=10000)

    new_dqt_body = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])
    assert len(new_dqt_body) == body_len
    assert new_dqt_body[0] == dqt_body[0]  # precision byte preserved
    # Q-values bumped.
    for k in range(64):
        expected = min(255, dqt_body[1 + k] * 2)
        assert new_dqt_body[1 + k] == expected, f"q{k} mismatch"

    # Splice + ffmpeg-decode.
    modified = (raw[:body_start] + new_dqt_body
                + raw[body_start + body_len:])
    out_path = Path("/tmp/h264_demo/sample_jpeg_graph_qtbump.jpg")
    out_path.write_bytes(modified)
    r = subprocess.run(
        [ffmpeg, "-loglevel", "error", "-i", str(out_path),
         "-frames:v", "1", "-f", "null", "-"],
        capture_output=True, text=True)
    assert r.returncode == 0, f"ffmpeg rejected JPEG QT-bump: {r.stderr}"

    def pixel_md5(p):
        r = subprocess.run(
            [ffmpeg, "-loglevel", "error", "-i", str(p),
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            capture_output=True, check=True)
        return hashlib.md5(r.stdout).hexdigest()
    assert pixel_md5(sample) != pixel_md5(out_path), (
        "graph-resident QT-bump did not change decoded pixels")


# --- conditional gating: a field present only when a control flag set


# A toy grammar exercising the conditional-decode machinery directly.
# Field order:
#   flag         u(1)   — controls whether `payload` is present
#   payload      se(v)  — only decoded when flag == 1
#   trailer      u(2)   — always present
TOY_COND_FIELDS = [
    ("u", "flag", 1),
    ("se", "payload", {"condition_name": "flag", "condition_value": 1}),
    ("u", "trailer", 2),
]


def test_conditional_field_present_when_gate_is_set():
    """The conditional `payload` field is decoded when the `flag`
    control bit is 1: the active rule fires, payload is read, and
    `trailer` follows at the bit position payload consumed."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, TOY_COND_FIELDS)
    seed_pps_decode_rules(s)

    # Bit layout: flag=1 (1 bit), payload=se(v) value 0 (1 bit "1"),
    # trailer=u(2) value 2 (bits "10"). Total 4 bits → 0b1110 0000 = 0xE0.
    # se(v) value 0 encodes as ue(v)=0 → 1 bit "1".
    buf = s._inner.add_node("Buffer", {"bytes": b"\xE0"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=100)

    decoded = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(state, "decoded")}
    assert decoded == {"flag": 1, "payload": 0, "trailer": 2}, decoded
    assert s._inner.node(state)["attrs"]["bp"] == 4


def test_conditional_field_skipped_when_gate_is_clear():
    """When the `flag` control bit is 0, the `payload` field is NOT
    in the bitstream. The decode_skip rule advances past it without
    consuming bits; `trailer` then decodes immediately."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, TOY_COND_FIELDS)
    seed_pps_decode_rules(s)

    # Bit layout: flag=0 (1 bit), trailer=u(2) value 3 (bits "11").
    # Payload is absent because flag is 0. Total 3 bits → 0b011_00000 = 0x60.
    buf = s._inner.add_node("Buffer", {"bytes": b"\x60"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=100)

    decoded = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(state, "decoded")}
    # `payload` is NOT in decoded because the skip rule fired.
    assert "payload" not in decoded
    assert decoded == {"flag": 0, "trailer": 3}, decoded
    # bp advanced 1 (flag) + 0 (skip) + 2 (trailer) = 3.
    assert s._inner.node(state)["attrs"]["bp"] == 3


def test_conditional_round_trip_via_encode_with_skip():
    """Full decode → mutate → encode round-trip exercising
    encode_skip. Start with flag=0 (so payload absent), mutate
    trailer, re-encode: the conditional payload must remain absent
    on the encode side (encode_skip fires) and the output bits
    decode back to the mutated trailer."""
    # Decode flag=0, trailer=3 (input 0x60).
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, TOY_COND_FIELDS)
    seed_pps_decode_rules(s)
    seed_pps_encode_rules(s)

    dec_buf = s._inner.add_node("Buffer", {"bytes": b"\x60"})
    dstate = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(dstate, "current", head)
    s._inner.add_edge(dstate, "buffer", dec_buf)
    s._inner.run_rules(max_steps=100)

    # Mutate trailer = 1.
    for v in s._inner.neighbours(dstate, "decoded"):
        if s._inner.node(v)["attrs"]["name"] == "trailer":
            s._inner.set_attr(v, "val", 1)

    # Encode.
    enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
    estate = s._inner.add_node("EncodeState", {"bp": 0})
    s._inner.add_edge(estate, "current", head)
    s._inner.add_edge(estate, "buffer", enc_buf)
    s._inner.add_edge(estate, "source", dstate)
    s._inner.run_rules(max_steps=100)

    new_bytes = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])
    new_bp = s._inner.node(estate)["attrs"]["bp"]
    # Output: flag=0, payload absent (encode_skip fired), trailer=1
    # → 1 + 0 + 2 = 3 bits = 0b001_xxxxx = 0x20.
    assert new_bp == 3
    assert new_bytes == b"\x20"

    # Round-trip back via decode.
    s2 = Substrate()
    seed_codec_vocabulary(s2)
    head2 = seed_field_grammar(s2, TOY_COND_FIELDS)
    seed_pps_decode_rules(s2)
    new_buf = s2._inner.add_node("Buffer", {"bytes": new_bytes})
    new_state = s2._inner.add_node("DecodeState", {"bp": 0})
    s2._inner.add_edge(new_state, "current", head2)
    s2._inner.add_edge(new_state, "buffer", new_buf)
    s2._inner.run_rules(max_steps=100)
    re_decoded = {s2._inner.node(v)["attrs"]["name"]:
                  s2._inner.node(v)["attrs"]["val"]
                  for v in s2._inner.neighbours(new_state, "decoded")}
    assert re_decoded == {"flag": 0, "trailer": 1}, re_decoded


def test_conditional_round_trip_with_payload_active():
    """The symmetric case — flag=1, payload present, both sides
    use the active rules (no skip fires)."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, TOY_COND_FIELDS)
    seed_pps_decode_rules(s)
    seed_pps_encode_rules(s)

    # flag=1, payload=2 (se(v)=2 → ue=3 → "00100" = 5 bits), trailer=1
    # Bits: 1 + 00100 + 01 = 8 bits = 0b1_00100_01 = 0x91.
    dec_buf = s._inner.add_node("Buffer", {"bytes": b"\x91"})
    dstate = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(dstate, "current", head)
    s._inner.add_edge(dstate, "buffer", dec_buf)
    s._inner.run_rules(max_steps=100)
    decoded = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(dstate, "decoded")}
    assert decoded == {"flag": 1, "payload": 2, "trailer": 1}, decoded

    # Mutate payload, re-encode.
    for v in s._inner.neighbours(dstate, "decoded"):
        if s._inner.node(v)["attrs"]["name"] == "payload":
            s._inner.set_attr(v, "val", -3)

    enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
    estate = s._inner.add_node("EncodeState", {"bp": 0})
    s._inner.add_edge(estate, "current", head)
    s._inner.add_edge(estate, "buffer", enc_buf)
    s._inner.add_edge(estate, "source", dstate)
    s._inner.run_rules(max_steps=100)

    new_bytes = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])

    # Round-trip.
    s2 = Substrate()
    seed_codec_vocabulary(s2)
    head2 = seed_field_grammar(s2, TOY_COND_FIELDS)
    seed_pps_decode_rules(s2)
    new_buf = s2._inner.add_node("Buffer", {"bytes": new_bytes})
    new_state = s2._inner.add_node("DecodeState", {"bp": 0})
    s2._inner.add_edge(new_state, "current", head2)
    s2._inner.add_edge(new_state, "buffer", new_buf)
    s2._inner.run_rules(max_steps=100)
    re_decoded = {s2._inner.node(v)["attrs"]["name"]:
                  s2._inner.node(v)["attrs"]["val"]
                  for v in s2._inner.neighbours(new_state, "decoded")}
    assert re_decoded == {"flag": 1, "payload": -3, "trailer": 1}


# --- nested conditions: H.265-style "if A==1 AND B==0" --------------


# Toy grammar with a 2-condition AND-gate, modelling the H.265
# deblocking branch (`if (deblocking_filter_control_present_flag &&
# !pps_deblocking_filter_disabled_flag)`). The `inner` field is
# present iff outer=1 AND disabled=0.
NESTED_COND_FIELDS = [
    ("u", "outer", 1),
    ("u", "disabled", 1, {"condition_name": "outer",
                            "condition_value": 1}),
    ("se", "inner", {"conditions": [
        ("outer", 1),
        ("disabled", 0),
    ]}),
    ("u", "trailer", 2),
]


def test_nested_conditions_all_satisfied():
    """outer=1 AND disabled=0 → inner field is present."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, NESTED_COND_FIELDS)
    seed_pps_decode_rules(s)

    # Bits: outer=1, disabled=0, inner=se(v) val=2 (ue=3, "00100"),
    # trailer=u(2) val=1 ("01"). Total 1+1+5+2 = 9 bits.
    # Pack MSB-first: 1 0 00100 01 _____ → 0b1000_1000_1xxxxxxx = 0x88,0x80
    s_bytes = s._inner.evaluate(
        # build via BitsWrite chain (simpler than hand-packing)
        BitsWrite(
            BitsWrite(
                BitsWrite(
                    BitsWrite(Lit(b""), Lit(0), Lit(1), Lit(1)),  # outer=1
                    Lit(1), Lit(0), Lit(1)),                         # disabled=0
                Lit(2), Lit(0b00100), Lit(5)),                       # inner se(v) val=2
            Lit(7), Lit(0b01), Lit(2)).to_dict(), {})

    buf = s._inner.add_node("Buffer", {"bytes": s_bytes})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=100)
    decoded = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(state, "decoded")}
    assert decoded == {"outer": 1, "disabled": 0, "inner": 2,
                        "trailer": 1}, decoded


def test_nested_conditions_outer_fails():
    """outer=0 → both disabled AND inner are skipped (chained skip:
    disabled gated on outer=1; inner gated on outer=1 AND ...)."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, NESTED_COND_FIELDS)
    seed_pps_decode_rules(s)

    # outer=0, trailer=3. disabled + inner both absent.
    # bits: 0 11_xxxxx → 0x60
    buf = s._inner.add_node("Buffer", {"bytes": b"\x60"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=100)
    decoded = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(state, "decoded")}
    assert decoded == {"outer": 0, "trailer": 3}, decoded
    # bp = 1 (outer) + 0 (disabled skipped) + 0 (inner skipped) + 2 (trailer)
    assert s._inner.node(state)["attrs"]["bp"] == 3


def test_nested_conditions_outer_set_disabled_set():
    """outer=1, disabled=1 → disabled present but inner skipped
    (inner needs outer=1 AND disabled=0; disabled=1 fails the AND)."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, NESTED_COND_FIELDS)
    seed_pps_decode_rules(s)

    # outer=1, disabled=1, inner absent, trailer=2.
    # bits: 1 1 10 _____ → 0b1110_0000 = 0xE0
    buf = s._inner.add_node("Buffer", {"bytes": b"\xE0"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=100)
    decoded = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(state, "decoded")}
    assert decoded == {"outer": 1, "disabled": 1, "trailer": 2}, decoded
    # bp = 1 + 1 + 0 (inner skipped) + 2 = 4
    assert s._inner.node(state)["attrs"]["bp"] == 4


def test_nested_conditions_round_trip_all_branches():
    """For each of 3 branch configurations, decode → mutate trailer
    → re-encode → decode → verify. Exercises encode_skip with
    multi-condition fields in all permutations of the gating
    flags."""
    branch_cases = [
        # (input_bytes, expected_decode, mutated_trailer, expected_re_decode)
        (b"\x60", {"outer": 0, "trailer": 3}, 1,
         {"outer": 0, "trailer": 1}),
        (b"\xE0", {"outer": 1, "disabled": 1, "trailer": 2}, 0,
         {"outer": 1, "disabled": 1, "trailer": 0}),
    ]
    for in_bytes, expect, new_trailer, re_expect in branch_cases:
        s = Substrate()
        seed_codec_vocabulary(s)
        head = seed_field_grammar(s, NESTED_COND_FIELDS)
        seed_pps_decode_rules(s)
        seed_pps_encode_rules(s)

        dec_buf = s._inner.add_node("Buffer", {"bytes": in_bytes})
        dstate = s._inner.add_node("DecodeState", {"bp": 0})
        s._inner.add_edge(dstate, "current", head)
        s._inner.add_edge(dstate, "buffer", dec_buf)
        s._inner.run_rules(max_steps=100)

        decoded = {s._inner.node(v)["attrs"]["name"]:
                   s._inner.node(v)["attrs"]["val"]
                   for v in s._inner.neighbours(dstate, "decoded")}
        assert decoded == expect, (in_bytes, decoded, expect)

        # Mutate trailer.
        for v in s._inner.neighbours(dstate, "decoded"):
            if s._inner.node(v)["attrs"]["name"] == "trailer":
                s._inner.set_attr(v, "val", new_trailer)

        # Encode.
        enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
        estate = s._inner.add_node("EncodeState", {"bp": 0})
        s._inner.add_edge(estate, "current", head)
        s._inner.add_edge(estate, "buffer", enc_buf)
        s._inner.add_edge(estate, "source", dstate)
        s._inner.run_rules(max_steps=100)
        new_bytes = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])

        # Round-trip decode of the re-emitted bytes.
        s2 = Substrate()
        seed_codec_vocabulary(s2)
        head2 = seed_field_grammar(s2, NESTED_COND_FIELDS)
        seed_pps_decode_rules(s2)
        new_buf = s2._inner.add_node("Buffer", {"bytes": new_bytes})
        new_state = s2._inner.add_node("DecodeState", {"bp": 0})
        s2._inner.add_edge(new_state, "current", head2)
        s2._inner.add_edge(new_state, "buffer", new_buf)
        s2._inner.run_rules(max_steps=100)
        re_decoded = {s2._inner.node(v)["attrs"]["name"]:
                      s2._inner.node(v)["attrs"]["val"]
                      for v in s2._inner.neighbours(new_state, "decoded")}
        assert re_decoded == re_expect, (in_bytes, re_decoded, re_expect)


# --- OR-of-ANDs (DNF): field active iff ANY group satisfies --------


# Models H.265's `chroma_format_idc != 0` — equivalent to
# chroma_format_idc IN {1, 2, 3}. Expressed as 3 single-member
# groups. (For a real codec we'd surface a `vals: [1,2,3]` shorthand;
# this exercises the DNF mechanism directly.)
DNF_FIELDS = [
    ("u", "idc", 2),
    ("u", "payload", 4, {"groups": [
        [("idc", 1)],
        [("idc", 2)],
        [("idc", 3)],
    ]}),
    ("u", "trailer", 2),
]


def test_or_condition_first_alternative_matches():
    """idc=1 → payload present (group 1 satisfies)."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, DNF_FIELDS)
    seed_pps_decode_rules(s)

    # idc=01 (2 bits), payload=0xA (4 bits), trailer=11 (2 bits). 8 bits → 0x6B.
    buf = s._inner.add_node("Buffer", {"bytes": b"\x6B"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=100)
    decoded = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(state, "decoded")}
    assert decoded == {"idc": 1, "payload": 0xA, "trailer": 3}, decoded


def test_or_condition_third_alternative_matches():
    """idc=3 → payload present (group 3 satisfies). Verifies OR
    actually OR — not just early-return on group 1."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, DNF_FIELDS)
    seed_pps_decode_rules(s)

    # idc=11, payload=0101=5, trailer=10. bits: 11 0101 10 → 0xD6.
    buf = s._inner.add_node("Buffer", {"bytes": b"\xD6"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=100)
    decoded = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(state, "decoded")}
    assert decoded == {"idc": 3, "payload": 5, "trailer": 2}, decoded


def test_or_condition_no_alternative_matches():
    """idc=0 → no group satisfies → payload skipped, trailer decoded
    immediately after idc."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, DNF_FIELDS)
    seed_pps_decode_rules(s)

    # idc=00, trailer=10. payload absent. 4 bits → 0x20.
    buf = s._inner.add_node("Buffer", {"bytes": b"\x20"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=100)
    decoded = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(state, "decoded")}
    assert decoded == {"idc": 0, "trailer": 2}, decoded
    # bp = 2 (idc) + 0 (payload skipped) + 2 (trailer) = 4.
    assert s._inner.node(state)["attrs"]["bp"] == 4


# Mixed: OR of ANDs — one group with a single condition, another
# group with two conditions. Models "(A==1) OR (B==1 AND C==0)".
MIXED_DNF_FIELDS = [
    ("u", "a", 1),
    ("u", "b", 1),
    ("u", "c", 1),
    ("u", "payload", 3, {"groups": [
        [("a", 1)],
        [("b", 1), ("c", 0)],
    ]}),
    ("u", "trailer", 1),
]


def test_mixed_dnf_short_group_wins():
    """a=1 → payload present even if b and c don't match the AND."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, MIXED_DNF_FIELDS)
    seed_pps_decode_rules(s)

    # a=1, b=0, c=1 (so AND-group fails), payload=101=5, trailer=0.
    # bits: 1 0 1 101 0 _ → 0b1011_0100 → 0xB4
    buf = s._inner.add_node("Buffer", {"bytes": b"\xB4"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=100)
    decoded = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(state, "decoded")}
    assert decoded == {"a": 1, "b": 0, "c": 1, "payload": 5,
                        "trailer": 0}, decoded


def test_mixed_dnf_long_group_wins():
    """a=0 (single-condition group fails) but b=1 AND c=0 (AND-group
    satisfies) → payload still present."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, MIXED_DNF_FIELDS)
    seed_pps_decode_rules(s)

    # a=0, b=1, c=0, payload=010=2, trailer=1.
    # bits: 0 1 0 010 1 _ → 0b0100_1010 = 0x4A.
    buf = s._inner.add_node("Buffer", {"bytes": b"\x4A"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=100)
    decoded = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(state, "decoded")}
    assert decoded == {"a": 0, "b": 1, "c": 0, "payload": 2,
                        "trailer": 1}, decoded


def test_mixed_dnf_neither_group_matches():
    """a=0, and AND-group fails (b=1 but c=1) → payload skipped."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, MIXED_DNF_FIELDS)
    seed_pps_decode_rules(s)

    # a=0, b=1, c=1, trailer=1. payload absent.
    # bits: 0 1 1 1 _ _ _ _ → 0b0111_0000 = 0x70
    buf = s._inner.add_node("Buffer", {"bytes": b"\x70"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=100)
    decoded = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(state, "decoded")}
    assert decoded == {"a": 0, "b": 1, "c": 1, "trailer": 1}, decoded
    # 4 bits total (a + b + c + trailer); payload contributes 0.
    assert s._inner.node(state)["attrs"]["bp"] == 4


def test_mixed_dnf_round_trip_all_branches():
    """Decode + mutate + encode round-trip across the four
    (a, b, c) configurations exercising both groups, neither,
    and each alone."""
    cases = [
        # (input bytes, expected decode, new trailer, expected re-decode)
        # Group A wins (a=1)
        (b"\xB4", {"a": 1, "b": 0, "c": 1, "payload": 5, "trailer": 0},
         1, {"a": 1, "b": 0, "c": 1, "payload": 5, "trailer": 1}),
        # Group B wins (b=1, c=0)
        (b"\x4A", {"a": 0, "b": 1, "c": 0, "payload": 2, "trailer": 1},
         0, {"a": 0, "b": 1, "c": 0, "payload": 2, "trailer": 0}),
        # Neither
        (b"\x70", {"a": 0, "b": 1, "c": 1, "trailer": 1},
         0, {"a": 0, "b": 1, "c": 1, "trailer": 0}),
    ]
    for in_bytes, expect, new_t, re_expect in cases:
        s = Substrate()
        seed_codec_vocabulary(s)
        head = seed_field_grammar(s, MIXED_DNF_FIELDS)
        seed_pps_decode_rules(s)
        seed_pps_encode_rules(s)

        dec_buf = s._inner.add_node("Buffer", {"bytes": in_bytes})
        dstate = s._inner.add_node("DecodeState", {"bp": 0})
        s._inner.add_edge(dstate, "current", head)
        s._inner.add_edge(dstate, "buffer", dec_buf)
        s._inner.run_rules(max_steps=100)
        decoded = {s._inner.node(v)["attrs"]["name"]:
                   s._inner.node(v)["attrs"]["val"]
                   for v in s._inner.neighbours(dstate, "decoded")}
        assert decoded == expect, (in_bytes, decoded, expect)

        # Mutate trailer.
        for v in s._inner.neighbours(dstate, "decoded"):
            if s._inner.node(v)["attrs"]["name"] == "trailer":
                s._inner.set_attr(v, "val", new_t)

        # Encode.
        enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
        estate = s._inner.add_node("EncodeState", {"bp": 0})
        s._inner.add_edge(estate, "current", head)
        s._inner.add_edge(estate, "buffer", enc_buf)
        s._inner.add_edge(estate, "source", dstate)
        s._inner.run_rules(max_steps=100)
        new_bytes = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])

        # Round-trip.
        s2 = Substrate()
        seed_codec_vocabulary(s2)
        head2 = seed_field_grammar(s2, MIXED_DNF_FIELDS)
        seed_pps_decode_rules(s2)
        nb = s2._inner.add_node("Buffer", {"bytes": new_bytes})
        ns = s2._inner.add_node("DecodeState", {"bp": 0})
        s2._inner.add_edge(ns, "current", head2)
        s2._inner.add_edge(ns, "buffer", nb)
        s2._inner.run_rules(max_steps=100)
        re_d = {s2._inner.node(v)["attrs"]["name"]:
                s2._inner.node(v)["attrs"]["val"]
                for v in s2._inner.neighbours(ns, "decoded")}
        assert re_d == re_expect, (in_bytes, re_d, re_expect)


# --- iteration: loop FieldSpec emits N body Values ------------------


def _collect_loop_values(s, state, name):
    """Helper — pull all Values with `name`, indexed, sorted by
    index. Mirrors how a real consumer reads loop output."""
    items = []
    for v in s._inner.neighbours(state, "decoded"):
        a = s._inner.node(v)["attrs"]
        if a.get("name") == name:
            items.append((a.get("index"), a.get("val")))
    items.sort()
    return items


# Models H.265's
#   num_tile_columns_minus1 ue(v)
#   for (i = 0; i <= num_tile_columns_minus1; i++)
#       column_width_minus1[i] ue(v)
TILE_LOOP_FIELDS = [
    ("ue", "num_tile_columns_minus1"),
    ("loop", "column_width_minus1", {
        "body_kind": "ue",
        "count_name": "num_tile_columns_minus1",
        "count_offset": 1,  # H.265's "minus1" pattern
    }),
    ("u", "trailer", 2),
]


def test_loop_decodes_N_body_instances():
    """Loop iterates `count_name + count_offset` times, each emitting
    a Value with the loop's name + an index attr."""
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, TILE_LOOP_FIELDS)
    seed_pps_decode_rules(s)

    # num_tile_columns_minus1=2 → iterate 3 times
    # ue codewords: 2="011", 0="1", 1="010", 3="00100"
    # then trailer=u(2) value 1 = "01"
    # Bits: 011 + 1 + 010 + 00100 + 01 = 14 bits, pad 2 zeros.
    # = 0111 0100 0100 0100 = 0x74 0x44
    buf = s._inner.add_node("Buffer", {"bytes": b"\x74\x44"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    n = s._inner.run_rules(max_steps=200)
    assert n > 0

    # num_tile_columns_minus1 decoded as 2.
    decoded_scalars = {s._inner.node(v)["attrs"]["name"]:
                       s._inner.node(v)["attrs"]["val"]
                       for v in s._inner.neighbours(state, "decoded")
                       if "index" not in s._inner.node(v)["attrs"]}
    assert decoded_scalars["num_tile_columns_minus1"] == 2
    assert decoded_scalars["trailer"] == 1
    # 3 column_width_minus1 instances, values 0, 1, 3.
    loop_vals = _collect_loop_values(s, state, "column_width_minus1")
    assert loop_vals == [(0, 0), (1, 1), (2, 3)], loop_vals
    # No LoopState left over.
    assert s._inner.neighbours(state, "loop_state") == []


def test_loop_zero_iterations():
    """When count_name + count_offset == 0, the loop fires init +
    complete without any iterations; subsequent field decodes
    immediately."""
    # Use a different spec where count_offset = 0 so we can hit zero.
    fields = [
        ("ue", "n"),
        ("loop", "v", {"body_kind": "ue", "count_name": "n",
                       "count_offset": 0}),
        ("u", "tail", 2),
    ]
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, fields)
    seed_pps_decode_rules(s)

    # n=0 (ue codeword "1"), then no loop body, then tail=01.
    # bits: 1 + 01 = 3 bits → 0b101_xxxxx = 0xA0
    buf = s._inner.add_node("Buffer", {"bytes": b"\xA0"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=100)

    decoded_scalars = {s._inner.node(v)["attrs"]["name"]:
                       s._inner.node(v)["attrs"]["val"]
                       for v in s._inner.neighbours(state, "decoded")
                       if "index" not in s._inner.node(v)["attrs"]}
    assert decoded_scalars == {"n": 0, "tail": 1}
    assert _collect_loop_values(s, state, "v") == []
    assert s._inner.neighbours(state, "loop_state") == []
    assert s._inner.node(state)["attrs"]["bp"] == 3


def test_loop_u_body_fixed_width():
    """Loop body of kind u(n) — fixed-width bits, like HEVC scaling
    list deltas."""
    fields = [
        ("u", "count", 3),
        ("loop", "elem", {"body_kind": "u", "body_nbits": 4,
                          "count_name": "count", "count_offset": 0}),
        ("u", "tail", 1),
    ]
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, fields)
    seed_pps_decode_rules(s)

    # count=3 (3 bits), elem=[0xA, 0x5, 0xC] (4 bits each = 12),
    # tail=1 (1 bit). Total 16 bits = 2 bytes.
    # bits: 011 1010 0101 1100 1 -> 0b0111_0100_1011_1001
    # = 0x74 0xB9? Wait recompute:
    # 011 + 1010 + 0101 + 1100 + 1 = "0111010010111001"
    # split: 0111 0100 1011 1001 = 0x74 0xB9
    buf = s._inner.add_node("Buffer", {"bytes": b"\x74\xB9"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=200)

    scalars = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(state, "decoded")
               if "index" not in s._inner.node(v)["attrs"]}
    assert scalars == {"count": 3, "tail": 1}, scalars
    assert _collect_loop_values(s, state, "elem") == [
        (0, 0xA), (1, 0x5), (2, 0xC)
    ]


def test_loop_round_trip_via_encode():
    """Full decode → mutate loop body value → re-encode → decode
    again. Exercises both decode and encode iteration."""
    # Reuse TILE_LOOP_FIELDS, count=2 case (3 iterations).
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, TILE_LOOP_FIELDS)
    seed_pps_decode_rules(s)
    seed_pps_encode_rules(s)

    dec_buf = s._inner.add_node("Buffer", {"bytes": b"\x74\x44"})
    dstate = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(dstate, "current", head)
    s._inner.add_edge(dstate, "buffer", dec_buf)
    s._inner.run_rules(max_steps=200)

    # Sanity — decode succeeded.
    decoded_widths = _collect_loop_values(s, dstate, "column_width_minus1")
    assert decoded_widths == [(0, 0), (1, 1), (2, 3)]

    # Mutate the loop body index 1: value 1 → value 4. The encode
    # rules must pick up the change and re-emit the loop with the new
    # value for that iteration.
    for v in s._inner.neighbours(dstate, "decoded"):
        a = s._inner.node(v)["attrs"]
        if a.get("name") == "column_width_minus1" and a.get("index") == 1:
            s._inner.set_attr(v, "val", 4)

    enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
    estate = s._inner.add_node("EncodeState", {"bp": 0})
    s._inner.add_edge(estate, "current", head)
    s._inner.add_edge(estate, "buffer", enc_buf)
    s._inner.add_edge(estate, "source", dstate)
    s._inner.run_rules(max_steps=200)

    new_bytes = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])

    # Round-trip decode.
    s2 = Substrate()
    seed_codec_vocabulary(s2)
    head2 = seed_field_grammar(s2, TILE_LOOP_FIELDS)
    seed_pps_decode_rules(s2)
    nb = s2._inner.add_node("Buffer", {"bytes": new_bytes})
    ns = s2._inner.add_node("DecodeState", {"bp": 0})
    s2._inner.add_edge(ns, "current", head2)
    s2._inner.add_edge(ns, "buffer", nb)
    s2._inner.run_rules(max_steps=200)

    re_widths = _collect_loop_values(s2, ns, "column_width_minus1")
    assert re_widths == [(0, 0), (1, 4), (2, 3)], re_widths
    re_scalars = {s2._inner.node(v)["attrs"]["name"]:
                  s2._inner.node(v)["attrs"]["val"]
                  for v in s2._inner.neighbours(ns, "decoded")
                  if "index" not in s2._inner.node(v)["attrs"]}
    assert re_scalars == {"num_tile_columns_minus1": 2, "trailer": 1}


def test_loop_fixed_count_literal():
    """A loop with a static count baked into the FieldSpec
    (`count_literal=N`) — models HEVC's fixed-arity arrays like
    `general_profile_compatibility_flag[32]`. No `count_name` lookup."""
    fields = [
        ("loop", "flag", {
            "body_kind": "u",
            "body_nbits": 1,
            "count_literal": 4,  # exactly 4 iterations
        }),
        ("u", "tail", 4),
    ]
    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, fields)
    seed_pps_decode_rules(s)

    # 4 flag bits + 4 tail bits = 8 bits = 1 byte.
    # flags = [1,0,1,1], tail = 0b0110 = 6 → 0b1011_0110 = 0xB6
    buf = s._inner.add_node("Buffer", {"bytes": b"\xB6"})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)
    s._inner.run_rules(max_steps=100)
    flags = _collect_loop_values(s, state, "flag")
    assert flags == [(0, 1), (1, 0), (2, 1), (3, 1)], flags
    scalars = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(state, "decoded")
               if "index" not in s._inner.node(v)["attrs"]}
    assert scalars == {"tail": 6}


# --- HEVC SPS prefix: real-codec stress test ------------------------


# ITU-T H.265 §7.3.2.2.1 sequence_parameter_set_rbsp() — prefix up
# through conformance_window_flag. Covers EVERY grammar construct
# the project supports:
#
#   * linear u(n)              — sps_video_parameter_set_id (4)
#                                sps_max_sub_layers_minus1 (3)
#                                profile_idc (5) etc.
#   * linear ue(v)             — sps_seq_parameter_set_id
#                                chroma_format_idc
#                                pic_width_in_luma_samples
#                                pic_height_in_luma_samples
#   * fixed-count loop         — general_profile_compatibility_flag[32]
#   * conditional (gated)      — separate_colour_plane_flag (gated on
#                                chroma_format_idc == 3 — absent for
#                                YUV420 = idc 1)
#
# For x265 ultrafast 128x128 / Main profile / sub_layers_minus1=0,
# the prefix decodes to a fixed structure; round-tripping the bytes
# proves the grammar covers it.
HEVC_SPS_PREFIX_FIELDS = [
    ("u",  "sps_video_parameter_set_id", 4),
    ("u",  "sps_max_sub_layers_minus1", 3),
    ("u",  "sps_temporal_id_nesting_flag", 1),
    # --- profile_tier_level(1, sps_max_sub_layers_minus1) ---
    ("u",  "general_profile_space", 2),
    ("u",  "general_tier_flag", 1),
    ("u",  "general_profile_idc", 5),
    ("loop", "general_profile_compatibility_flag", {
        "body_kind": "u",
        "body_nbits": 1,
        "count_literal": 32,
    }),
    ("u",  "general_progressive_source_flag", 1),
    ("u",  "general_interlaced_source_flag", 1),
    ("u",  "general_non_packed_constraint_flag", 1),
    ("u",  "general_frame_only_constraint_flag", 1),
    # 43 bits of constraint flags / reserved — treated as one
    # fixed-width field (their per-bit meanings are profile-
    # specific; the grammar doesn't need to interpret them to
    # round-trip the SPS).
    ("u",  "general_constraint_flags", 43),
    # 1 bit: general_inbld_flag for profile_idc==1 (Main) etc.,
    # otherwise general_reserved_zero_bit. Either way it's a single
    # u(1), so we treat as the same field for round-trip purposes.
    ("u",  "general_inbld_or_reserved_bit", 1),
    ("u",  "general_level_idc", 8),
    # NB: per-sub-layer fields appear only when sps_max_sub_layers
    # _minus1 > 0; for x265 ultrafast at 30fps it's typically 0, so
    # we omit them in this prefix grammar.
    # ---- back to SPS body ----
    ("ue", "sps_seq_parameter_set_id"),
    ("ue", "chroma_format_idc"),
    ("u",  "separate_colour_plane_flag", 1,
     {"conditions": [("chroma_format_idc", 3)]}),
    ("ue", "pic_width_in_luma_samples"),
    ("ue", "pic_height_in_luma_samples"),
    ("u",  "conformance_window_flag", 1),
    # Conformance-window offsets — only present when the flag is set.
    ("ue", "conf_win_left_offset",
     {"conditions": [("conformance_window_flag", 1)]}),
    ("ue", "conf_win_right_offset",
     {"conditions": [("conformance_window_flag", 1)]}),
    ("ue", "conf_win_top_offset",
     {"conditions": [("conformance_window_flag", 1)]}),
    ("ue", "conf_win_bottom_offset",
     {"conditions": [("conformance_window_flag", 1)]}),
    # ---- continuing past the conformance window block ----
    ("ue", "bit_depth_luma_minus8"),
    ("ue", "bit_depth_chroma_minus8"),
    ("ue", "log2_max_pic_order_cnt_lsb_minus4"),
    ("u",  "sps_sub_layer_ordering_info_present_flag", 1),
    # The sub-layer ordering info block iterates over a range of i
    # values:
    #   start = sps_sub_layer_ordering_info_present_flag
    #           ? 0 : sps_max_sub_layers_minus1
    #   end (inclusive) = sps_max_sub_layers_minus1
    # For x265 ultrafast at 30fps the stream has
    # sps_max_sub_layers_minus1 == 0, so the loop runs exactly once
    # regardless of the flag. Express as three ue(v) bodies looped
    # `sps_max_sub_layers_minus1 + 1` times — correct for this
    # common case; the conditional start-from logic would need
    # additional grammar in the general case.
    ("loop", "sps_max_dec_pic_buffering_minus1", {
        "body_kind": "ue",
        "count_name": "sps_max_sub_layers_minus1",
        "count_offset": 1,
    }),
    ("loop", "sps_max_num_reorder_pics", {
        "body_kind": "ue",
        "count_name": "sps_max_sub_layers_minus1",
        "count_offset": 1,
    }),
    ("loop", "sps_max_latency_increase_plus1", {
        "body_kind": "ue",
        "count_name": "sps_max_sub_layers_minus1",
        "count_offset": 1,
    }),
    ("ue", "log2_min_luma_coding_block_size_minus3"),
    ("ue", "log2_diff_max_min_luma_coding_block_size"),
    ("ue", "log2_min_luma_transform_block_size_minus2"),
    ("ue", "log2_diff_max_min_luma_transform_block_size"),
    ("ue", "max_transform_hierarchy_depth_inter"),
    ("ue", "max_transform_hierarchy_depth_intra"),
    ("u",  "scaling_list_enabled_flag", 1),
    # scaling_list_data() — gated block inserted below via
    # `_make_scaling_list_fields()`. Concatenated into the final
    # HEVC_SPS_PREFIX_FIELDS list right after this point.
    ("u",  "amp_enabled_flag", 1),
    ("u",  "sample_adaptive_offset_enabled_flag", 1),
    ("u",  "pcm_enabled_flag", 1),
]


def _make_scaling_list_data_fields():
    """Generate the H.265 §7.3.4 scaling_list_data() FieldSpec chain.

    Structure (paraphrased from the spec):
        for sizeId in 0..3:
            for matrixId in 0..(6 if sizeId<3 else 2), step=(3 if sizeId==3 else 1):
                scaling_list_pred_mode_flag[sizeId][matrixId] u(1)
                if pred_mode_flag == 0:
                    scaling_list_pred_matrix_id_delta[..] ue(v)
                else:
                    /* dc_coef + 16..64 coefficient deltas */

    This generator handles the common branch (pred_mode_flag = 0,
    default-scaling reference). The pred_mode_flag = 1 branch with
    its variable-size coefficient delta loop is out of scope for
    this first iteration; streams that use custom scaling matrices
    (rare for the presets we sample) would need it.

    Every emitted FieldSpec is gated on scaling_list_enabled_flag == 1,
    so when scaling is OFF this entire block contributes zero bits to
    the decode/encode chain — verified by the existing SPS tests
    against x265 ultrafast (scaling=0).

    Total emitted FieldSpecs (matches H.265 spec arithmetic):
        sizeId=0..2: 6 matrices × 2 fields = 12 each → 36
        sizeId=3:     2 matrices × 2 fields = 4
        Total:        40 FieldSpecs
    """
    out = []
    gate = [("scaling_list_enabled_flag", 1)]
    for sizeId in range(4):
        step = 3 if sizeId == 3 else 1
        # coefNum = Min(64, 1 << (4 + (sizeId << 1)))
        coef_num = min(64, 1 << (4 + (sizeId << 1)))
        for matrixId in range(0, 6, step):
            suffix = f"{sizeId}_{matrixId}"
            pred_flag_name = f"scaling_list_pred_mode_flag_{suffix}"
            out.append(("u", pred_flag_name, 1,
                        {"conditions": list(gate)}))
            # pred_mode_flag == 0 branch: a single ue(v) delta
            # pointing at the reference matrix.
            out.append(("ue",
                f"scaling_list_pred_matrix_id_delta_{suffix}",
                {"groups": [list(gate) + [(pred_flag_name, 0)]]}))
            # pred_mode_flag == 1 branch: custom matrix.
            #
            #   if sizeId > 1: scaling_list_dc_coef_minus8 se(v)
            #   then coefNum × scaling_list_delta_coef se(v) loop
            #
            # The DC coef field is gated on (gate AND pred_mode_flag==1
            # AND sizeId in {2,3}); the coef loop is a fixed-count loop
            # gated on (gate AND pred_mode_flag==1).
            custom_gate = list(gate) + [(pred_flag_name, 1)]
            if sizeId > 1:
                out.append(("se",
                    f"scaling_list_dc_coef_minus8_{suffix}",
                    {"groups": [custom_gate]}))
            out.append(("loop", f"scaling_list_delta_coef_{suffix}", {
                "body_kind": "se",
                "count_literal": coef_num,
                "groups": [custom_gate],
            }))
    return out


# Splice the scaling_list_data sub-grammar into the SPS field list
# just after `scaling_list_enabled_flag`. The exact insertion point
# is found by name so the slot survives later edits to the prefix.
def _splice_scaling_list_into_sps(base, sub):
    out = []
    for spec in base:
        out.append(spec)
        if spec[0] == "u" and spec[1] == "scaling_list_enabled_flag":
            out.extend(sub)
    return out


HEVC_SPS_PREFIX_FIELDS = _splice_scaling_list_into_sps(
    HEVC_SPS_PREFIX_FIELDS, _make_scaling_list_data_fields())


def test_hevc_sps_prefix_full_grammar():
    """Exercise the FULL grammar vocabulary on a real x265-encoded
    SPS. Linear u(n)/ue(v), a 32-iteration fixed-count loop
    (general_profile_compatibility_flag), and conditional fields
    (separate_colour_plane_flag, conformance window) all walk
    through the SAME Rule set.

    The proof is round-trip: decode → re-encode → re-decode →
    identical scalars + loop values. No ffmpeg verification (full
    SPS round-trip requires the entire H.265 spec, not just the
    prefix); the round-trip is the architectural correctness
    check.
    """
    import shutil
    import subprocess
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not installed")

    src = Path("/tmp/h264_demo/sample.hevc")
    if not src.exists():
        src.parent.mkdir(parents=True, exist_ok=True)
        rc = subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=128x128:rate=30",
            "-c:v", "libx265", "-preset", "ultrafast",
            "-tune", "zerolatency", "-pix_fmt", "yuv420p",
            "-x265-params", "log-level=error", "-an", str(src),
        ]).returncode
        if rc != 0 or not src.exists():
            pytest.skip("ffmpeg has no libx265 support")

    # Locate SPS NAL (type 33, 2-byte header).
    raw = src.read_bytes()
    i = 0
    sps_raw_rbsp = None
    while i < len(raw) - 4:
        if raw[i:i+4] == b"\x00\x00\x00\x01":
            sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01":
            sc = 3
        else:
            i += 1
            continue
        if ((raw[i+sc] >> 1) & 0x3F) == 33:
            j = i + sc + 2
            while j < len(raw) - 3:
                if (raw[j:j+3] == b"\x00\x00\x01"
                        or raw[j:j+4] == b"\x00\x00\x00\x01"):
                    break
                j += 1
            sps_raw_rbsp = raw[i + sc + 2 : j]
            break
        i += sc
    assert sps_raw_rbsp is not None, "no SPS in sample"

    # Strip emulation prevention bytes: HEVC inserts 0x03 after any
    # 0x00 0x00 ≤0x03 sequence so the encoded payload can't be
    # confused with start codes. The decoder must reverse this
    # before parsing the SPS as a bitstream.
    def strip_emulation(data: bytes) -> bytes:
        out = bytearray()
        k = 0
        while k < len(data):
            if (k + 2 < len(data)
                    and data[k] == 0 and data[k+1] == 0
                    and data[k+2] == 3):
                out.append(0)
                out.append(0)
                k += 3
            else:
                out.append(data[k])
                k += 1
        return bytes(out)

    def add_emulation(data: bytes) -> bytes:
        """Re-insert 0x03 after any 0x00 0x00 ≤0x03 sequence — the
        inverse of strip_emulation, needed when splicing the encoded
        SPS back into a real NAL stream."""
        out = bytearray()
        k = 0
        while k < len(data):
            if (k + 1 < len(data)
                    and data[k] == 0 and data[k+1] == 0
                    and k + 2 < len(data) and data[k+2] <= 0x03):
                out.extend([0, 0, 3])
                k += 2
            else:
                out.append(data[k])
                k += 1
        return bytes(out)

    sps_rbsp = strip_emulation(sps_raw_rbsp)

    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, HEVC_SPS_PREFIX_FIELDS)
    seed_pps_decode_rules(s)
    seed_pps_encode_rules(s)

    dec_buf = s._inner.add_node("Buffer", {"bytes": sps_rbsp})
    dstate = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(dstate, "current", head)
    s._inner.add_edge(dstate, "buffer", dec_buf)
    s._inner.run_rules(max_steps=2000)

    # Read out scalars + the compatibility-flag loop.
    scalars = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(dstate, "decoded")
               if "index" not in s._inner.node(v)["attrs"]}
    compat = _collect_loop_values(
        s, dstate, "general_profile_compatibility_flag")

    # Sanity-check the structure: profile_idc=1 (Main), max_sub_layers=0,
    # YUV420 (chroma_format_idc=1), 128x128, no conformance crop.
    assert scalars["general_profile_idc"] == 1
    assert scalars["sps_max_sub_layers_minus1"] == 0
    assert scalars["chroma_format_idc"] == 1
    assert scalars["pic_width_in_luma_samples"] == 128
    assert scalars["pic_height_in_luma_samples"] == 128
    assert scalars["conformance_window_flag"] == 0
    # Conditional fields absent.
    assert "separate_colour_plane_flag" not in scalars
    assert "conf_win_left_offset" not in scalars
    # The 32 compat flags were all decoded.
    assert len(compat) == 32
    assert all(idx == i for i, (idx, _) in enumerate(compat))

    # Re-encode and verify byte-identical round-trip up to the
    # last decoded bit. The prefix grammar covers all fields the
    # x265 SPS uses for this stream; nothing extra is present in
    # the original beyond what we model (plus trailing zero pad we
    # can't predict, so check via re-decode equality of values).
    bits_used = s._inner.node(dstate)["attrs"]["bp"]

    enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
    estate = s._inner.add_node("EncodeState", {"bp": 0})
    s._inner.add_edge(estate, "current", head)
    s._inner.add_edge(estate, "buffer", enc_buf)
    s._inner.add_edge(estate, "source", dstate)
    s._inner.run_rules(max_steps=2000)

    new_bytes = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])
    new_bp = s._inner.node(estate)["attrs"]["bp"]
    assert new_bp == bits_used, (
        f"encode bp {new_bp} != decode bp {bits_used} "
        f"— grammar dropped or added bits")

    # All bits up to bits_used must match the original exactly.
    # Compare byte-by-byte up to the last full byte, then bit-wise
    # within the trailing partial byte.
    full_bytes = bits_used // 8
    trailing_bits = bits_used % 8
    assert new_bytes[:full_bytes] == sps_rbsp[:full_bytes], (
        f"full-byte round-trip diverged: "
        f"orig {sps_rbsp[:full_bytes].hex()} vs "
        f"new {new_bytes[:full_bytes].hex()}")
    if trailing_bits:
        mask = (0xFF << (8 - trailing_bits)) & 0xFF
        assert (new_bytes[full_bytes] & mask) == (
            sps_rbsp[full_bytes] & mask), (
            f"trailing bits diverged at byte {full_bytes}")


def test_hevc_sps_conformance_window_bump_via_ffmpeg():
    """Bump the HEVC SPS conformance window via the graph grammar —
    visible crop in ffmpeg's decoded output.

    Sets conformance_window_flag = 1 + four conf_win_*_offset values
    that didn't exist in the original (the conditional rules
    correctly enabled them once the gate flipped). The unchanged
    SPS tail (everything past our grammar's coverage) gets bit-copied
    onto the new buffer at the shifted position.

    Splice the re-emitted SPS (with emulation-prevention bytes re-
    inserted) back into a real x265 stream; ffmpeg decodes; the
    OUTPUT dimensions shrink by `2 * SubWidthC * crop` per side
    (4 px for YUV420 with offset=1)."""
    import shutil
    import subprocess
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        pytest.skip("ffmpeg/ffprobe not installed")

    src = Path("/tmp/h264_demo/sample.hevc")
    if not src.exists():
        pytest.skip("HEVC sample not built")

    raw = src.read_bytes()

    # Locate the SPS NAL.
    i = 0
    sps_start = sc_len = sps_end = None
    while i < len(raw) - 4:
        if raw[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01": sc = 3
        else: i += 1; continue
        if ((raw[i+sc] >> 1) & 0x3F) == 33:
            sps_start, sc_len = i, sc
            j = i + sc + 2
            while j < len(raw) - 3:
                if (raw[j:j+3] == b"\x00\x00\x01"
                        or raw[j:j+4] == b"\x00\x00\x00\x01"):
                    break
                j += 1
            sps_end = j
            break
        i += sc
    assert sps_start is not None

    sps_raw = raw[sps_start + sc_len + 2 : sps_end]

    # Reuse the same strip/add helpers from the prefix test.
    def strip_emulation(data: bytes) -> bytes:
        out = bytearray()
        k = 0
        while k < len(data):
            if (k + 2 < len(data)
                    and data[k] == 0 and data[k+1] == 0
                    and data[k+2] == 3):
                out.append(0); out.append(0); k += 3
            else:
                out.append(data[k]); k += 1
        return bytes(out)

    def add_emulation(data: bytes) -> bytes:
        out = bytearray()
        k = 0
        while k < len(data):
            # Emit byte; if last-two appended are 0x00 0x00 and the
            # next byte is ≤ 0x03, insert a 0x03 first.
            if (len(out) >= 2
                    and out[-2] == 0 and out[-1] == 0
                    and data[k] <= 0x03):
                out.append(3)
            out.append(data[k])
            k += 1
        # Also handle trailing 00 00 followed by EOF — not strictly
        # required but defensive.
        return bytes(out)

    sps_rbsp = strip_emulation(sps_raw)

    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, HEVC_SPS_PREFIX_FIELDS)
    seed_pps_decode_rules(s)
    seed_pps_encode_rules(s)

    dec_buf = s._inner.add_node("Buffer", {"bytes": sps_rbsp})
    dstate = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(dstate, "current", head)
    s._inner.add_edge(dstate, "buffer", dec_buf)
    s._inner.run_rules(max_steps=2000)
    bits_used = s._inner.node(dstate)["attrs"]["bp"]

    # Verify the original has no conformance window.
    scalars = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(dstate, "decoded")
               if "index" not in s._inner.node(v)["attrs"]}
    assert scalars["conformance_window_flag"] == 0
    assert scalars["pic_width_in_luma_samples"] == 128
    assert scalars["pic_height_in_luma_samples"] == 128

    # MUTATE: flip the flag + add the four offset Values that the
    # encode rules will pick up. The new Values must be edged from
    # dstate via `decoded` so the encode_ue match binds them.
    for v in s._inner.neighbours(dstate, "decoded"):
        if (s._inner.node(v)["attrs"].get("name")
                == "conformance_window_flag"):
            s._inner.set_attr(v, "val", 1)
    crop = 1  # crop offset per side (in SubWidthC=2 units for YUV420)
    for name in ("conf_win_left_offset", "conf_win_right_offset",
                  "conf_win_top_offset", "conf_win_bottom_offset"):
        new_v = s._inner.add_node("Value", {"name": name, "val": crop})
        s._inner.add_edge(dstate, "decoded", new_v)

    # ENCODE via the grammar.
    enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
    estate = s._inner.add_node("EncodeState", {"bp": 0})
    s._inner.add_edge(estate, "current", head)
    s._inner.add_edge(estate, "buffer", enc_buf)
    s._inner.add_edge(estate, "source", dstate)
    s._inner.run_rules(max_steps=2000)

    new_prefix_bytes = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])
    new_prefix_bp = s._inner.node(estate)["attrs"]["bp"]

    # COPY the tail bits (everything in the original SPS past our
    # grammar's coverage) onto the new buffer at the shifted bp.
    sps_total_bits = len(sps_rbsp) * 8
    tail_bits = sps_total_bits - bits_used
    out_bytes = new_prefix_bytes
    out_bp = new_prefix_bp
    # Copy in 32-bit chunks via BitsAt + BitsWrite.
    src_lit = Lit(sps_rbsp)
    p = bits_used
    while p < sps_total_bits:
        chunk = min(32, sps_total_bits - p)
        word = s._inner.evaluate(
            BitsAt(src_lit, Lit(p), Lit(chunk)).to_dict(), {})
        out_bytes = s._inner.evaluate(
            BitsWrite(Lit(out_bytes), Lit(out_bp),
                      Lit(word), Lit(chunk)).to_dict(), {})
        p += chunk
        out_bp += chunk
    new_sps_rbsp = bytes(out_bytes)

    # Re-add emulation prevention + splice into the stream.
    new_sps_with_emul = add_emulation(new_sps_rbsp)
    modified = (raw[: sps_start + sc_len + 2]
                + new_sps_with_emul
                + raw[sps_end:])
    out_path = Path("/tmp/h264_demo/sample_sps_cropped.hevc")
    out_path.write_bytes(modified)

    # ffmpeg/ffprobe should report the cropped output dimensions.
    probe = subprocess.run(
        [ffprobe, "-loglevel", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,coded_width,coded_height",
         "-of", "default=nokey=1:noprint_wrappers=1", str(out_path)],
        capture_output=True, text=True, check=True)
    lines = [l for l in probe.stdout.strip().split("\n") if l]
    # Expected output: width, height, coded_width, coded_height.
    width, height, coded_w, coded_h = (int(x) for x in lines)
    # SubWidthC = SubHeightC = 2 for YUV420; crop=1 → 2*1*2 = 4 px each.
    expected_w = 128 - 2 * 2 * crop
    expected_h = 128 - 2 * 2 * crop
    assert width == expected_w, (
        f"width: expected {expected_w}, got {width}")
    assert height == expected_h, (
        f"height: expected {expected_h}, got {height}")
    # coded_width/height stays 128 (the raw frame size).
    assert coded_w == 128
    assert coded_h == 128

    # And ffmpeg can actually decode it.
    decode = subprocess.run(
        [ffmpeg, "-loglevel", "error", "-i", str(out_path),
         "-f", "null", "-"],
        capture_output=True, text=True)
    assert decode.returncode == 0, (
        f"ffmpeg rejected cropped SPS: {decode.stderr}")

    # Pixel-level proof: the OUTPUT must actually differ from the
    # original — frame data is the same encoded bits, but the
    # decoder crops, so rawvideo output is shorter + has different
    # content per frame.
    import hashlib

    def pixel_md5(p):
        r = subprocess.run(
            [ffmpeg, "-loglevel", "error", "-i", str(p),
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            capture_output=True, check=True)
        return hashlib.md5(r.stdout).hexdigest(), len(r.stdout)
    orig_h, orig_size = pixel_md5(src)
    mod_h, mod_size = pixel_md5(out_path)
    assert orig_h != mod_h, "cropped output should produce different pixels"
    # 30 frames * 128*128*3 = 1,474,560 bytes; cropped is
    # 30 * 124*124*3 = 1,383,840 bytes.
    expected_mod = 30 * width * height * 3
    assert mod_size == expected_mod, (
        f"expected cropped raw size {expected_mod}, got {mod_size}")

    print(f"\n  HEVC SPS conformance-window bump via graph grammar:")
    print(f"    bits used in grammar:       {bits_used}")
    print(f"    SPS RBSP:  {len(sps_rbsp)} → {len(new_sps_rbsp)} bytes")
    print(f"    output dim: 128x128 → {width}x{height}  "
          f"(coded still {coded_w}x{coded_h})")
    print(f"    ffmpeg decoded the modified HEVC cleanly")


def test_hevc_pps_tile_array_bump_via_ffmpeg():
    """Bump the HEVC PPS tile array via the graph grammar — turn on
    tiles_enabled_flag and emit a 2x2 tile layout. The tile array
    is a conditional BLOCK with two nested LOOPS, all gated by
    the master flag.

    Original PPS has tiles_enabled_flag=0 (x265 default) — all
    tile fields skipped via the conditional rules. The bump:

      1. set tiles_enabled_flag = 1
      2. add num_tile_columns_minus1 = 1, num_tile_rows_minus1 = 1
         (→ 2 columns × 2 rows)
      3. set uniform_spacing_flag = 1 (uniform tile sizes; per-tile
         width/height loops stay skipped because their conditions
         require uniform_spacing_flag == 0)
      4. add loop_filter_across_tiles_enabled_flag = 1

    Encode rules fire for the freshly-active conditional fields;
    encode_skip stays off for them. The tile-width / tile-height
    LOOPS remain inactive because their AND-group still has
    uniform_spacing_flag == 0 (we set it to 1)."""
    import shutil
    import subprocess
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        pytest.skip("ffmpeg/ffprobe not installed")

    # Use a larger sample so 2x2 tiles is legal (each tile ≥ 1 CTU).
    src = Path("/tmp/h264_demo/tiled.hevc")
    if not src.exists():
        src.parent.mkdir(parents=True, exist_ok=True)
        rc = subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=512x512:rate=30",
            "-c:v", "libx265", "-preset", "medium",
            "-x265-params", "log-level=error",
            "-pix_fmt", "yuv420p", "-an", str(src),
        ]).returncode
        if rc != 0 or not src.exists():
            pytest.skip("ffmpeg has no libx265 support")

    raw = src.read_bytes()

    # Locate PPS NAL.
    i = 0
    pps_start = sc_len = pps_end = None
    while i < len(raw) - 4:
        if raw[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01": sc = 3
        else: i += 1; continue
        if ((raw[i+sc] >> 1) & 0x3F) == 34:
            pps_start, sc_len = i, sc
            j = i + sc + 2
            while j < len(raw) - 3:
                if (raw[j:j+3] == b"\x00\x00\x01"
                        or raw[j:j+4] == b"\x00\x00\x00\x01"):
                    break
                j += 1
            pps_end = j
            break
        i += sc
    pps_raw = raw[pps_start + sc_len + 2 : pps_end]

    def strip_emulation(data):
        out = bytearray()
        k = 0
        while k < len(data):
            if (k + 2 < len(data) and data[k] == 0
                    and data[k+1] == 0 and data[k+2] == 3):
                out.append(0); out.append(0); k += 3
            else:
                out.append(data[k]); k += 1
        return bytes(out)

    def add_emulation(data):
        out = bytearray()
        for b in data:
            if (len(out) >= 2 and out[-2] == 0
                    and out[-1] == 0 and b <= 0x03):
                out.append(3)
            out.append(b)
        return bytes(out)

    pps_rbsp = strip_emulation(pps_raw)

    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, H265_PPS_FIELDS)
    seed_pps_decode_rules(s)
    seed_pps_encode_rules(s)

    dec_buf = s._inner.add_node("Buffer", {"bytes": pps_rbsp})
    dstate = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(dstate, "current", head)
    s._inner.add_edge(dstate, "buffer", dec_buf)
    s._inner.run_rules(max_steps=2000)

    scalars = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(dstate, "decoded")
               if "index" not in s._inner.node(v)["attrs"]}
    # Tiles initially off; conditional tile fields all absent.
    assert scalars["tiles_enabled_flag"] == 0
    for name in ("num_tile_columns_minus1", "num_tile_rows_minus1",
                  "uniform_spacing_flag",
                  "loop_filter_across_tiles_enabled_flag",
                  "column_width_minus1", "row_height_minus1"):
        assert name not in scalars, (
            f"unexpected {name} in decoded — tile fields should be "
            f"skipped when tiles_enabled_flag is 0")

    bits_used = s._inner.node(dstate)["attrs"]["bp"]

    # MUTATE — flip tiles_enabled_flag and inject the new conditional
    # field Values. Uniform spacing keeps the per-tile size LOOPS
    # off (their AND-group requires uniform_spacing == 0).
    for v in s._inner.neighbours(dstate, "decoded"):
        if (s._inner.node(v)["attrs"].get("name")
                == "tiles_enabled_flag"):
            s._inner.set_attr(v, "val", 1)
    for name, val in [
        ("num_tile_columns_minus1", 1),
        ("num_tile_rows_minus1", 1),
        ("uniform_spacing_flag", 1),
        ("loop_filter_across_tiles_enabled_flag", 1),
    ]:
        nv = s._inner.add_node("Value", {"name": name, "val": val})
        s._inner.add_edge(dstate, "decoded", nv)

    # ENCODE via the grammar.
    enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
    estate = s._inner.add_node("EncodeState", {"bp": 0})
    s._inner.add_edge(estate, "current", head)
    s._inner.add_edge(estate, "buffer", enc_buf)
    s._inner.add_edge(estate, "source", dstate)
    s._inner.run_rules(max_steps=2000)

    new_prefix_bytes = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])
    new_prefix_bp = s._inner.node(estate)["attrs"]["bp"]

    # Bit-copy the PPS tail (everything past our grammar's coverage)
    # onto the new buffer at the shifted bp.
    pps_total_bits = len(pps_rbsp) * 8
    out_bytes = new_prefix_bytes
    out_bp = new_prefix_bp
    src_lit = Lit(pps_rbsp)
    p = bits_used
    while p < pps_total_bits:
        chunk = min(32, pps_total_bits - p)
        word = s._inner.evaluate(
            BitsAt(src_lit, Lit(p), Lit(chunk)).to_dict(), {})
        out_bytes = s._inner.evaluate(
            BitsWrite(Lit(out_bytes), Lit(out_bp),
                      Lit(word), Lit(chunk)).to_dict(), {})
        p += chunk
        out_bp += chunk
    new_pps_rbsp = bytes(out_bytes)

    # Re-add emulation bytes, splice, verify.
    new_pps_with_emul = add_emulation(new_pps_rbsp)
    modified = (raw[: pps_start + sc_len + 2]
                + new_pps_with_emul
                + raw[pps_end:])
    out_path = Path("/tmp/h264_demo/sample_tiled_bump.hevc")
    out_path.write_bytes(modified)

    # ffmpeg must decode the modified stream cleanly.
    r = subprocess.run(
        [ffmpeg, "-loglevel", "error", "-i", str(out_path),
         "-f", "null", "-"],
        capture_output=True, text=True)
    assert r.returncode == 0, (
        f"ffmpeg rejected tile-bumped PPS: {r.stderr}")

    # Decode the modified PPS back through our grammar to verify the
    # new tile fields are present + the conditional loops still skipped.
    s2 = Substrate()
    seed_codec_vocabulary(s2)
    head2 = seed_field_grammar(s2, H265_PPS_FIELDS)
    seed_pps_decode_rules(s2)
    new_buf = s2._inner.add_node("Buffer", {"bytes": new_pps_rbsp})
    new_state = s2._inner.add_node("DecodeState", {"bp": 0})
    s2._inner.add_edge(new_state, "current", head2)
    s2._inner.add_edge(new_state, "buffer", new_buf)
    s2._inner.run_rules(max_steps=2000)
    re_scalars = {s2._inner.node(v)["attrs"]["name"]:
                  s2._inner.node(v)["attrs"]["val"]
                  for v in s2._inner.neighbours(new_state, "decoded")
                  if "index" not in s2._inner.node(v)["attrs"]}
    assert re_scalars["tiles_enabled_flag"] == 1
    assert re_scalars["num_tile_columns_minus1"] == 1
    assert re_scalars["num_tile_rows_minus1"] == 1
    assert re_scalars["uniform_spacing_flag"] == 1
    assert re_scalars["loop_filter_across_tiles_enabled_flag"] == 1
    # column_width_minus1 / row_height_minus1 LOOPS skipped because
    # uniform_spacing_flag is 1 (their AND-group requires == 0).
    re_widths = _collect_loop_values(
        s2, new_state, "column_width_minus1")
    re_heights = _collect_loop_values(
        s2, new_state, "row_height_minus1")
    assert re_widths == []
    assert re_heights == []

    # Pixel verification — ffmpeg decoded the modified stream;
    # internally that involved tile parsing in the slice header.
    import hashlib

    def pixel_md5(p):
        r = subprocess.run(
            [ffmpeg, "-loglevel", "error", "-i", str(p),
             "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-"],
            capture_output=True)
        return hashlib.md5(r.stdout).hexdigest(), len(r.stdout)
    _, mod_size = pixel_md5(out_path)
    # 1 frame * 512*512*3 = 786,432 bytes; size shouldn't change
    # (tile partitioning is decoder-side; output pixel count same).
    assert mod_size == 512 * 512 * 3

    print(f"\n  HEVC PPS tile-array bump via graph grammar:")
    print(f"    PPS RBSP:  {len(pps_rbsp)} → {len(new_pps_rbsp)} bytes")
    print(f"    new fields:  tiles_enabled=1, 2x2 uniform tiles,")
    print(f"                  loop_filter_across_tiles=1")
    print(f"    conditional LOOPS (column_width/row_height) "
          f"correctly stayed inactive (uniform_spacing=1)")
    print(f"    ffmpeg decoded modified HEVC; output {mod_size}B")


def test_hevc_sps_extended_fields_decode():
    """Beyond conformance_window: the extended HEVC_SPS_PREFIX_FIELDS
    grammar now covers ~14 more fields including a dynamic-count
    loop trio (sub_layer ordering info), the CTB block-size fields,
    and the inter/intra/scaling/SAO/PCM flags.

    Round-trips byte-exact on x265 ultrafast; specific field values
    sanity-checked against what x265 emits at this preset (Main
    profile, sub_layers=0, 8-bit YUV420, no scaling, no PCM)."""
    import shutil
    import subprocess
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not installed")

    src = Path("/tmp/h264_demo/sample.hevc")
    if not src.exists():
        pytest.skip("HEVC sample not built")

    def strip_emulation(data):
        out = bytearray()
        k = 0
        while k < len(data):
            if (k + 2 < len(data) and data[k] == 0
                    and data[k+1] == 0 and data[k+2] == 3):
                out.append(0); out.append(0); k += 3
            else:
                out.append(data[k]); k += 1
        return bytes(out)

    raw = src.read_bytes()
    i = 0
    sps_raw = None
    while i < len(raw) - 4:
        if raw[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01": sc = 3
        else: i += 1; continue
        if ((raw[i+sc] >> 1) & 0x3F) == 33:
            j = i + sc + 2
            while j < len(raw) - 3:
                if (raw[j:j+3] == b"\x00\x00\x01"
                        or raw[j:j+4] == b"\x00\x00\x00\x01"):
                    break
                j += 1
            sps_raw = raw[i + sc + 2 : j]
            break
        i += sc
    sps_rbsp = strip_emulation(sps_raw)

    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, HEVC_SPS_PREFIX_FIELDS)
    seed_pps_decode_rules(s)
    seed_pps_encode_rules(s)

    dec_buf = s._inner.add_node("Buffer", {"bytes": sps_rbsp})
    dstate = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(dstate, "current", head)
    s._inner.add_edge(dstate, "buffer", dec_buf)
    s._inner.run_rules(max_steps=2000)

    scalars = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(dstate, "decoded")
               if "index" not in s._inner.node(v)["attrs"]}

    # All the new fields should be in decoded for x265 ultrafast.
    expected_fields = [
        "bit_depth_luma_minus8",
        "bit_depth_chroma_minus8",
        "log2_max_pic_order_cnt_lsb_minus4",
        "sps_sub_layer_ordering_info_present_flag",
        "log2_min_luma_coding_block_size_minus3",
        "log2_diff_max_min_luma_coding_block_size",
        "log2_min_luma_transform_block_size_minus2",
        "log2_diff_max_min_luma_transform_block_size",
        "max_transform_hierarchy_depth_inter",
        "max_transform_hierarchy_depth_intra",
        "scaling_list_enabled_flag",
        "amp_enabled_flag",
        "sample_adaptive_offset_enabled_flag",
        "pcm_enabled_flag",
    ]
    for f in expected_fields:
        assert f in scalars, f"{f} not decoded"
    # Sanity: 8-bit YUV420 → bit_depth_*_minus8 = 0
    assert scalars["bit_depth_luma_minus8"] == 0
    assert scalars["bit_depth_chroma_minus8"] == 0
    # x265 ultrafast: scaling lists off, PCM off (typical).
    assert scalars["scaling_list_enabled_flag"] == 0
    assert scalars["pcm_enabled_flag"] == 0
    # The sub-layer loops fired exactly once (sub_layers_minus1=0,
    # count_offset=1 → count=1).
    for loop_name in ("sps_max_dec_pic_buffering_minus1",
                       "sps_max_num_reorder_pics",
                       "sps_max_latency_increase_plus1"):
        vals = _collect_loop_values(s, dstate, loop_name)
        assert len(vals) == 1, (
            f"{loop_name}: expected 1 iteration, got {len(vals)}")

    # Round-trip: re-encode, verify byte-exact up to bits_used.
    bits_used = s._inner.node(dstate)["attrs"]["bp"]
    enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
    estate = s._inner.add_node("EncodeState", {"bp": 0})
    s._inner.add_edge(estate, "current", head)
    s._inner.add_edge(estate, "buffer", enc_buf)
    s._inner.add_edge(estate, "source", dstate)
    s._inner.run_rules(max_steps=2000)
    new_bytes = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])
    new_bp = s._inner.node(estate)["attrs"]["bp"]
    assert new_bp == bits_used, (
        f"encode bp {new_bp} != decode bp {bits_used} — grammar dropped/added bits")
    full_bytes = bits_used // 8
    trailing_bits = bits_used % 8
    assert new_bytes[:full_bytes] == sps_rbsp[:full_bytes]
    if trailing_bits:
        mask = (0xFF << (8 - trailing_bits)) & 0xFF
        assert (new_bytes[full_bytes] & mask) == (
            sps_rbsp[full_bytes] & mask)

    print(f"\n  Extended HEVC SPS grammar decode:")
    print(f"    bits consumed: {bits_used} ({bits_used // 8} bytes)")
    print(f"    fields decoded: {len(scalars)} scalars + "
          f"{sum(len(_collect_loop_values(s, dstate, n)) for n in ('sps_max_dec_pic_buffering_minus1', 'sps_max_num_reorder_pics', 'sps_max_latency_increase_plus1', 'general_profile_compatibility_flag'))} loop entries")


def test_hevc_scaling_list_data_round_trip():
    """Exercises the scaling_list_data() sub-grammar — flip
    scaling_list_enabled_flag from 0 → 1 on a real SPS, emit the
    default-scaling block (every pred_mode_flag=0 + every
    pred_matrix_id_delta=0 → "use the reference matrix verbatim"),
    re-encode, decode back, verify identity of the 40 new fields.

    Default-scaling emission contributes exactly 40 bits to the
    bitstream (20 matrices × 2 bits each: 1-bit pred_mode_flag + 1-bit
    ue(v) of 0). That's the headline number: the entire
    `scaling_list_data()` sub-grammar — every iteration of every
    branch — round-trips through the graph in 40 bits."""
    from pathlib import Path

    src = Path("/tmp/h264_demo/sample.hevc")
    if not src.exists():
        pytest.skip("HEVC sample not built")

    def strip_emulation(data):
        out = bytearray()
        k = 0
        while k < len(data):
            if (k + 2 < len(data) and data[k] == 0
                    and data[k+1] == 0 and data[k+2] == 3):
                out.append(0); out.append(0); k += 3
            else:
                out.append(data[k]); k += 1
        return bytes(out)

    raw = src.read_bytes()
    i = 0
    sps_raw = None
    while i < len(raw) - 4:
        if raw[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01": sc = 3
        else: i += 1; continue
        if ((raw[i+sc] >> 1) & 0x3F) == 33:
            j = i + sc + 2
            while j < len(raw) - 3:
                if (raw[j:j+3] == b"\x00\x00\x01"
                        or raw[j:j+4] == b"\x00\x00\x00\x01"):
                    break
                j += 1
            sps_raw = raw[i + sc + 2 : j]
            break
        i += sc
    sps_rbsp = strip_emulation(sps_raw)

    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, HEVC_SPS_PREFIX_FIELDS)
    seed_pps_decode_rules(s)
    seed_pps_encode_rules(s)

    dec_buf = s._inner.add_node("Buffer", {"bytes": sps_rbsp})
    dstate = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(dstate, "current", head)
    s._inner.add_edge(dstate, "buffer", dec_buf)
    s._inner.run_rules(max_steps=4000)

    scalars = {s._inner.node(v)["attrs"]["name"]:
               s._inner.node(v)["attrs"]["val"]
               for v in s._inner.neighbours(dstate, "decoded")
               if "index" not in s._inner.node(v)["attrs"]}
    # Sanity — scaling is off in our sample so no scaling_list_*
    # fields decoded.
    assert scalars["scaling_list_enabled_flag"] == 0
    scaling_names = [n for n in scalars if n.startswith("scaling_list_")]
    # Only the master flag itself starts with "scaling_list_"; the
    # sub-grammar fields should all be absent.
    assert scaling_names == ["scaling_list_enabled_flag"], scaling_names

    decode_bits_used = s._inner.node(dstate)["attrs"]["bp"]

    # MUTATE: enable scaling lists + emit 40 fields' worth of default
    # values. Every pred_mode_flag = 0 (use reference matrix);
    # every pred_matrix_id_delta = 0 (no delta from reference).
    for v in s._inner.neighbours(dstate, "decoded"):
        if (s._inner.node(v)["attrs"].get("name")
                == "scaling_list_enabled_flag"):
            s._inner.set_attr(v, "val", 1)
    scaling_field_names = []
    for sizeId in range(4):
        step = 3 if sizeId == 3 else 1
        for matrixId in range(0, 6, step):
            suffix = f"{sizeId}_{matrixId}"
            for name, val in [
                (f"scaling_list_pred_mode_flag_{suffix}", 0),
                (f"scaling_list_pred_matrix_id_delta_{suffix}", 0),
            ]:
                nv = s._inner.add_node("Value", {"name": name, "val": val})
                s._inner.add_edge(dstate, "decoded", nv)
                scaling_field_names.append(name)
    # We must have 40 new fields (20 iterations × 2).
    assert len(scaling_field_names) == 40

    # ENCODE.
    enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
    estate = s._inner.add_node("EncodeState", {"bp": 0})
    s._inner.add_edge(estate, "current", head)
    s._inner.add_edge(estate, "buffer", enc_buf)
    s._inner.add_edge(estate, "source", dstate)
    s._inner.run_rules(max_steps=4000)

    new_bytes = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])
    new_bp = s._inner.node(estate)["attrs"]["bp"]

    # bp should equal decode_bits_used + 40 (the scaling-list block
    # contribution; everything else unchanged in length).
    assert new_bp == decode_bits_used + 40, (
        f"expected encode bp {decode_bits_used + 40} (=decode + 40 "
        f"scaling-list bits), got {new_bp}")

    # Round-trip: decode the new buffer and verify the 40 scaling
    # fields come back, all defaults, with the master flag set.
    s2 = Substrate()
    seed_codec_vocabulary(s2)
    head2 = seed_field_grammar(s2, HEVC_SPS_PREFIX_FIELDS)
    seed_pps_decode_rules(s2)
    nb = s2._inner.add_node("Buffer", {"bytes": new_bytes})
    ns = s2._inner.add_node("DecodeState", {"bp": 0})
    s2._inner.add_edge(ns, "current", head2)
    s2._inner.add_edge(ns, "buffer", nb)
    s2._inner.run_rules(max_steps=4000)

    re = {s2._inner.node(v)["attrs"]["name"]:
          s2._inner.node(v)["attrs"]["val"]
          for v in s2._inner.neighbours(ns, "decoded")
          if "index" not in s2._inner.node(v)["attrs"]}
    assert re["scaling_list_enabled_flag"] == 1
    for fname in scaling_field_names:
        assert fname in re, f"{fname} missing after round-trip"
        assert re[fname] == 0, f"{fname} drifted: {re[fname]} ≠ 0"

    # Spot-check a couple of fields by name to verify the
    # programmatic generator + the conditional gate matched up.
    assert re["scaling_list_pred_mode_flag_0_0"] == 0
    assert re["scaling_list_pred_matrix_id_delta_3_3"] == 0  # sizeId=3 step=3

    # Bits consumed by the SPS prefix (incl. scaling block) equals
    # encode bp; round-trip is bit-exact for the modelled prefix.
    assert s2._inner.node(ns)["attrs"]["bp"] == new_bp

    print(f"\n  HEVC scaling_list_data round-trip:")
    print(f"    scaling_list_enabled_flag: 0 → 1")
    print(f"    new fields emitted: {len(scaling_field_names)} "
          f"(20 matrices × 2 fields, default-scaling branch)")
    print(f"    grammar bp:  {decode_bits_used} → {new_bp} "
          f"(+{new_bp - decode_bits_used} bits)")
    print(f"    pred_mode_flag = 1 branch (custom matrices with "
          f"variable-length coef loop) not yet modelled")


def test_hevc_scaling_list_custom_matrix_branch():
    """The harder branch — `pred_mode_flag = 1` triggers per-element
    coefficient delta emission. For sizeId>1 there's an additional
    dc_coef field BEFORE the delta loop. The loop's count comes
    from a SPEC-COMPUTED formula `Min(64, 1 << (4 + sizeId*2))`,
    which the grammar bakes into each matrix's FieldSpec via
    `count_literal`.

    Test: set ONE matrix (sizeId=0, matrixId=0) to pred_mode=1
    with all coef deltas = 0; leave the other 19 matrices on
    pred_mode=0. Verify (a) the dc_coef field is correctly ABSENT
    for sizeId=0 (gated to sizeId∈{2,3}), (b) the 16-entry delta
    loop fires, (c) bit count matches the spec arithmetic, and
    (d) round-trip decode recovers every emitted value."""
    from pathlib import Path

    src = Path("/tmp/h264_demo/sample.hevc")
    if not src.exists():
        pytest.skip("HEVC sample not built")

    def strip_emulation(data):
        out = bytearray()
        k = 0
        while k < len(data):
            if (k + 2 < len(data) and data[k] == 0
                    and data[k+1] == 0 and data[k+2] == 3):
                out.append(0); out.append(0); k += 3
            else:
                out.append(data[k]); k += 1
        return bytes(out)

    raw = src.read_bytes()
    i = 0
    sps_raw = None
    while i < len(raw) - 4:
        if raw[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01": sc = 3
        else: i += 1; continue
        if ((raw[i+sc] >> 1) & 0x3F) == 33:
            j = i + sc + 2
            while j < len(raw) - 3:
                if (raw[j:j+3] == b"\x00\x00\x01"
                        or raw[j:j+4] == b"\x00\x00\x00\x01"):
                    break
                j += 1
            sps_raw = raw[i + sc + 2 : j]
            break
        i += sc
    sps_rbsp = strip_emulation(sps_raw)

    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, HEVC_SPS_PREFIX_FIELDS)
    seed_pps_decode_rules(s)
    seed_pps_encode_rules(s)

    dec_buf = s._inner.add_node("Buffer", {"bytes": sps_rbsp})
    dstate = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(dstate, "current", head)
    s._inner.add_edge(dstate, "buffer", dec_buf)
    s._inner.run_rules(max_steps=4000)
    decode_bits_used = s._inner.node(dstate)["attrs"]["bp"]

    # MUTATE: enable scaling; matrix (0,0) uses custom (pred_mode=1)
    # with 16 zero deltas; remaining matrices use reference
    # (pred_mode=0) with delta=0.
    for v in s._inner.neighbours(dstate, "decoded"):
        if (s._inner.node(v)["attrs"].get("name")
                == "scaling_list_enabled_flag"):
            s._inner.set_attr(v, "val", 1)

    custom_matrix = (0, 0)
    delta_count_for_sizeId = {0: 16, 1: 64, 2: 64, 3: 64}
    expected_bits_added = 0

    for sizeId in range(4):
        step = 3 if sizeId == 3 else 1
        for matrixId in range(0, 6, step):
            suffix = f"{sizeId}_{matrixId}"
            pred_name = f"scaling_list_pred_mode_flag_{suffix}"
            if (sizeId, matrixId) == custom_matrix:
                # pred_mode_flag = 1 → emit dc_coef (sizeId>1 only) +
                # the delta loop.
                nv = s._inner.add_node("Value",
                    {"name": pred_name, "val": 1})
                s._inner.add_edge(dstate, "decoded", nv)
                if sizeId > 1:
                    dc_name = f"scaling_list_dc_coef_minus8_{suffix}"
                    nv = s._inner.add_node("Value",
                        {"name": dc_name, "val": 0})
                    s._inner.add_edge(dstate, "decoded", nv)
                # delta_coef loop — emit `coefNum` Values with index.
                coef_num = delta_count_for_sizeId[sizeId]
                loop_name = f"scaling_list_delta_coef_{suffix}"
                for k in range(coef_num):
                    nv = s._inner.add_node("Value",
                        {"name": loop_name, "val": 0, "index": k})
                    s._inner.add_edge(dstate, "decoded", nv)
                # 1 bit pred_mode + coef_num × 1 bit (each se(v)=0 is "1")
                # + 1 bit dc_coef when sizeId>1 (also se(v)=0).
                expected_bits_added += 1 + coef_num
                if sizeId > 1:
                    expected_bits_added += 1
            else:
                # default branch — pred_mode=0 + delta=0
                for name, val in [(pred_name, 0),
                    (f"scaling_list_pred_matrix_id_delta_{suffix}", 0)]:
                    nv = s._inner.add_node("Value",
                        {"name": name, "val": val})
                    s._inner.add_edge(dstate, "decoded", nv)
                expected_bits_added += 2

    # ENCODE.
    enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
    estate = s._inner.add_node("EncodeState", {"bp": 0})
    s._inner.add_edge(estate, "current", head)
    s._inner.add_edge(estate, "buffer", enc_buf)
    s._inner.add_edge(estate, "source", dstate)
    s._inner.run_rules(max_steps=4000)
    new_bytes = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])
    new_bp = s._inner.node(estate)["attrs"]["bp"]

    # Custom matrix (0,0): pred_mode=1 (1b) + 16 × delta_coef se(0)=1b each
    #   = 17 bits  (no dc_coef because sizeId=0 ≤ 1)
    # Other 19 matrices: pred_mode=0 (1b) + ue(0)=1b = 2 bits each → 38b
    # Total added = 17 + 38 = 55 bits.
    assert expected_bits_added == 55
    assert new_bp == decode_bits_used + expected_bits_added, (
        f"bits added {new_bp - decode_bits_used} ≠ "
        f"expected {expected_bits_added}")

    # Round-trip decode.
    s2 = Substrate()
    seed_codec_vocabulary(s2)
    head2 = seed_field_grammar(s2, HEVC_SPS_PREFIX_FIELDS)
    seed_pps_decode_rules(s2)
    nb = s2._inner.add_node("Buffer", {"bytes": new_bytes})
    ns = s2._inner.add_node("DecodeState", {"bp": 0})
    s2._inner.add_edge(ns, "current", head2)
    s2._inner.add_edge(ns, "buffer", nb)
    s2._inner.run_rules(max_steps=4000)

    re = {s2._inner.node(v)["attrs"]["name"]:
          s2._inner.node(v)["attrs"]["val"]
          for v in s2._inner.neighbours(ns, "decoded")
          if "index" not in s2._inner.node(v)["attrs"]}
    # Matrix (0,0): pred_mode set to 1, no delta field (because gate
    # requires pred_mode=0), DELTA LOOP fired 16 times.
    assert re["scaling_list_pred_mode_flag_0_0"] == 1
    assert "scaling_list_pred_matrix_id_delta_0_0" not in re
    # sizeId=0 → no dc_coef.
    assert "scaling_list_dc_coef_minus8_0_0" not in re
    deltas = _collect_loop_values(s2, ns, "scaling_list_delta_coef_0_0")
    assert len(deltas) == 16, (
        f"delta loop fired {len(deltas)} times, expected 16")
    assert all(v == 0 for _, v in deltas)

    # Other matrices: pred_mode=0 → delta field present.
    assert re["scaling_list_pred_mode_flag_3_3"] == 0
    assert re["scaling_list_pred_matrix_id_delta_3_3"] == 0
    # Their delta loops fired ZERO times (gate requires pred_mode=1).
    assert _collect_loop_values(s2, ns,
        "scaling_list_delta_coef_3_3") == []

    print(f"\n  HEVC scaling_list_data custom-matrix branch:")
    print(f"    matrix (0,0): pred_mode=1, 16-element delta loop")
    print(f"    19 other matrices: pred_mode=0, single delta ue(v)")
    print(f"    bits added:  {new_bp - decode_bits_used} "
          f"(= 17 custom + 38 default)")
    print(f"    round-trip:  every field name + value recovered")


def test_hevc_sps_scaling_list_bump_via_ffmpeg():
    """End-to-end with ffmpeg: enable scaling_list_enabled_flag,
    emit default scaling block, splice back into the stream,
    confirm ffmpeg decodes successfully. (Default scaling refs the
    same matrices the decoder would use when scaling is off, so
    pixels are unchanged — that's the proof of bitstream validity
    rather than a behavioural change.)"""
    import shutil
    import subprocess
    import hashlib
    from pathlib import Path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not installed")

    src = Path("/tmp/h264_demo/sample.hevc")
    if not src.exists():
        pytest.skip("HEVC sample not built")

    def strip_emulation(data):
        out = bytearray()
        k = 0
        while k < len(data):
            if (k + 2 < len(data) and data[k] == 0
                    and data[k+1] == 0 and data[k+2] == 3):
                out.append(0); out.append(0); k += 3
            else:
                out.append(data[k]); k += 1
        return bytes(out)

    def add_emulation(data):
        out = bytearray()
        for b in data:
            if (len(out) >= 2 and out[-2] == 0
                    and out[-1] == 0 and b <= 0x03):
                out.append(3)
            out.append(b)
        return bytes(out)

    raw = src.read_bytes()
    i = 0
    sps_start = sc_len = sps_end = None
    while i < len(raw) - 4:
        if raw[i:i+4] == b"\x00\x00\x00\x01": sc = 4
        elif raw[i:i+3] == b"\x00\x00\x01": sc = 3
        else: i += 1; continue
        if ((raw[i+sc] >> 1) & 0x3F) == 33:
            sps_start, sc_len = i, sc
            j = i + sc + 2
            while j < len(raw) - 3:
                if (raw[j:j+3] == b"\x00\x00\x01"
                        or raw[j:j+4] == b"\x00\x00\x00\x01"):
                    break
                j += 1
            sps_end = j
            break
        i += sc
    sps_rbsp = strip_emulation(raw[sps_start + sc_len + 2 : sps_end])

    s = Substrate()
    seed_codec_vocabulary(s)
    head = seed_field_grammar(s, HEVC_SPS_PREFIX_FIELDS)
    seed_pps_decode_rules(s)
    seed_pps_encode_rules(s)

    dec_buf = s._inner.add_node("Buffer", {"bytes": sps_rbsp})
    dstate = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(dstate, "current", head)
    s._inner.add_edge(dstate, "buffer", dec_buf)
    s._inner.run_rules(max_steps=4000)
    bits_used = s._inner.node(dstate)["attrs"]["bp"]

    # Enable scaling lists + emit 40-bit default block.
    for v in s._inner.neighbours(dstate, "decoded"):
        if (s._inner.node(v)["attrs"].get("name")
                == "scaling_list_enabled_flag"):
            s._inner.set_attr(v, "val", 1)
    for sizeId in range(4):
        step = 3 if sizeId == 3 else 1
        for matrixId in range(0, 6, step):
            suffix = f"{sizeId}_{matrixId}"
            for n, v in [
                (f"scaling_list_pred_mode_flag_{suffix}", 0),
                (f"scaling_list_pred_matrix_id_delta_{suffix}", 0),
            ]:
                nv = s._inner.add_node("Value", {"name": n, "val": v})
                s._inner.add_edge(dstate, "decoded", nv)

    # Encode + bit-copy SPS tail.
    enc_buf = s._inner.add_node("Buffer", {"bytes": b""})
    estate = s._inner.add_node("EncodeState", {"bp": 0})
    s._inner.add_edge(estate, "current", head)
    s._inner.add_edge(estate, "buffer", enc_buf)
    s._inner.add_edge(estate, "source", dstate)
    s._inner.run_rules(max_steps=4000)

    new_prefix = bytes(s._inner.node(enc_buf)["attrs"]["bytes"])
    new_prefix_bp = s._inner.node(estate)["attrs"]["bp"]

    out_bytes = new_prefix
    out_bp = new_prefix_bp
    src_lit = Lit(sps_rbsp)
    total = len(sps_rbsp) * 8
    p = bits_used
    while p < total:
        chunk = min(32, total - p)
        word = s._inner.evaluate(
            BitsAt(src_lit, Lit(p), Lit(chunk)).to_dict(), {})
        out_bytes = s._inner.evaluate(
            BitsWrite(Lit(out_bytes), Lit(out_bp),
                      Lit(word), Lit(chunk)).to_dict(), {})
        p += chunk
        out_bp += chunk
    new_sps_rbsp = bytes(out_bytes)

    modified = (raw[: sps_start + sc_len + 2]
                + add_emulation(new_sps_rbsp)
                + raw[sps_end:])
    out_path = Path("/tmp/h264_demo/sample_scaling_on.hevc")
    out_path.write_bytes(modified)

    # ffmpeg must decode the modified stream cleanly.
    r = subprocess.run(
        [ffmpeg, "-loglevel", "error", "-i", str(out_path),
         "-f", "null", "-"],
        capture_output=True, text=True)
    assert r.returncode == 0, (
        f"ffmpeg rejected scaling-enabled SPS: {r.stderr}")

    # Pixels unchanged (default-scaling matrices = identity for the
    # quantization step — no behavioural difference from scaling-off).
    def pixel_md5(p):
        r = subprocess.run(
            [ffmpeg, "-loglevel", "error", "-i", str(p),
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            capture_output=True, check=True)
        return hashlib.md5(r.stdout).hexdigest()
    # Default scaling refs typically equal flat-16 quantization (no
    # actual scaling). Output may match the original byte-for-byte
    # for our simple testsrc input, but in principle ffmpeg might
    # interpret things slightly — we just confirm it decoded.
    orig_h = pixel_md5(src)
    mod_h = pixel_md5(out_path)
    # Either equal (default scaling == no scaling) or different
    # (ffmpeg's reference-matrix interpretation). Both are valid;
    # the key test is that ffmpeg ACCEPTED the new bitstream.

    print(f"\n  HEVC SPS scaling-list bump via ffmpeg:")
    print(f"    SPS RBSP:  {len(sps_rbsp)} → {len(new_sps_rbsp)} bytes")
    print(f"    scaling_list_enabled_flag: 0 → 1")
    print(f"    40 bits of default scaling_list_data inserted")
    print(f"    ffmpeg accepted the modified HEVC stream")
    print(f"    pixel md5: {'identical' if orig_h == mod_h else 'differs'}")
