"""Phase 3 — RewriteRules that emit DesignedPatch nodes from PrimitiveSpec.

The agent's own seed (`agent_source_vocabulary`) names the ten source
homes a new TermNode variant must live in. Phase 3 installs ten
RewriteRules, one per home, that fire on PrimitiveSpec nodes and emit
DesignedPatch nodes carrying the splice for that home. Each patch is
composed natively in the rule's effects (StringConcat over Var("spec")
and the spec's `name` Attr) — the rule does the composition; Python
only installs the rules.

Trigger constraint (honest):

The substrate's rule engine requires every rule to have at least one
match_edge — a rule with zero edges never enters the indexed match
loop, so "match a node by type alone" is not expressible. PrimitiveSpec
nodes as introspected today have NO outbound or inbound edges (see
runtime_design.agent_specify_primitive — it adds the node and stops).
A rule like `match: [["spec", "is_a", "spec"]]` therefore would never
fire on the specs the agent has actually created.

Resolution: this module wires every PrimitiveSpec node to a sentinel
Microtheory (`phase3_trigger`) via a `has_primitive_spec` edge BEFORE
the rules look. Each rule matches that exact edge shape, binds the
spec to `"spec"`, and emits a DesignedPatch. The trigger is added by
`install_phase3_rules` for every PrimitiveSpec already in the graph
AND repeatedly on each call, so callers that mint specs after install
must either (a) call `wire_existing_specs(substrate)` again, or (b)
emit the `has_primitive_spec` edge themselves at spec-creation time.

Engine boundary discovered during smoke testing — multi-spec fan-out:

The Rust rule engine's incremental matcher
(`Substrate::try_incremental_match`) advances per-edge-type cursors
to `lengths_before` after the FIRST progressing binding per pass, then
returns. On the subsequent pass, no edges are "new" any more, so the
rule never re-fires on the second spec wired by the same edge-type. In
practice this means **a single `substrate.tick()` after install
produces N=10 DesignedPatches for the FIRST PrimitiveSpec only** — the
second/third/etc. PrimitiveSpec waits its turn but never gets one with
the current install pattern.

Workarounds available to callers (verified, smoke-tested):
  (1) wire_existing_specs + tick **per spec**: wire one spec at a time
      and tick between each — each tick fires all 10 rules once for the
      single newly-visible binding, then deadlocks at no-progress.
  (2) Mint a fresh trigger edge per spec on a unique edge-type (e.g.,
      has_primitive_spec_<spec_id>) and install a rule per-spec — at
      the cost of an O(spec_count) rule explosion.

Phase 4 (the verifier) operates on a single PrimitiveSpec (the one
`runtime_design.agent_specify_primitive` produces), so the single-pass
limitation does not affect the goal — the 10 patches for that ArgMax
spec appear after a single tick.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Term-JSON builders. We construct effect Terms as raw JSON dicts (the
# wire shape parse_effect_json consumes); this avoids round-tripping
# substrate_rs Term wrappers when the result has to be a plain dict
# anyway.
# ---------------------------------------------------------------------------

def _lit(value: Any) -> dict:
    return {"type": "Lit", "value": value}


def _var(name: str) -> dict:
    return {"type": "Var", "name": name}


def _attr(node_term: dict, key: str) -> dict:
    return {"type": "Attr", "node": node_term, "key": key}


def _concat(*parts: dict) -> dict:
    return {"type": "StringConcat", "parts": list(parts)}


def _computed(term: dict) -> dict:
    """Wrap a Term so parse_effect_json treats it as a computed effect arg."""
    return {"__term__": term}


# ---------------------------------------------------------------------------
# Per-home patch templates.
#
# Each entry says: which file the patch lands in, what anchor it splices
# after, and what prefix/suffix wraps the spec name in the emitted source.
# Anchors are Tokenize lines — Tokenize is the explicit exemplar in the
# `agent_source_vocabulary` seed (`tokenize_is_exemplar`), the only
# variant guaranteed to be wired across every home. By splicing AFTER an
# anchor that ALREADY contains Tokenize, the new variant lands in the
# same indentation context as a known-good neighbour.
#
# All anchor strings are intentionally short snippets that are unique
# enough at install time but kept conservative — phase 4's verifier may
# need to tighten them based on actual file contents. Where a single
# canonical anchor is uncertain, the rule still produces a patch; the
# world's `checkpoint_and_restart` button surfaces an anchor miss as a
# `patch_anchor_not_found` BuildError, which is the right place for
# that diagnosis to surface (graph-resident, agent-sensable).
# ---------------------------------------------------------------------------

# Sentinel placeholder used in `parts` lists below — every occurrence is
# replaced at rule-construction time by `Attr(Var("spec"), "name")` so
# the StringConcat splices the new variant's name in EVERY position the
# Tokenize exemplar's name appeared. A `parts` list is the sequence of
# literal strings + name placeholders that compose the patch content;
# the StringConcat collapses them in the rule effects, so `{name}` in
# the content is composed by the rule, never baked in.
_NAME = object()


_HOMES = [
    # 1. term.rs — enum variant declaration. Anchor is the full Tokenize
    # variant line (including trailing comma); the patch content is a
    # newline-prefixed sibling line so the new variant lands on its own
    # row directly under the exemplar.
    #     `    {name} { text: TermIdx },`
    {
        "home":        "term_rs_enum_variant_home",
        "target_path": "src/term.rs",
        "anchor":      "    Tokenize { text: TermIdx },",
        "parts": [
            "\n    ",
            _NAME,
            " { text: TermIdx },",
        ],
    },
    # 2. term.rs — copy_subtree arm. Anchor is the FULL line in src/term.rs
    # (truncating it to the first `=> TermNode::Tokenize` was the build
    # error: anchor must match verbatim, including the rest of the line).
    #     `        TermNode::{name} { text } => TermNode::{name} { text: copy_subtree(src, dst, text) },`
    {
        "home":        "term_rs_copy_subtree_arm_home",
        "target_path": "src/term.rs",
        "anchor":      "        TermNode::Tokenize { text } => TermNode::Tokenize { text: copy_subtree(src, dst, text) },",
        "parts": [
            "\n        TermNode::",
            _NAME,
            " { text } => TermNode::",
            _NAME,
            " { text: copy_subtree(src, dst, text) },",
        ],
    },
    # 3. term.rs — evaluator arm. Anchor is the COMPLETE Tokenize evaluator
    # block (from `TermNode::Tokenize { text } => {` through the closing
    # brace); splicing AFTER it lands at the start of the next arm. The
    # content body is identical to Tokenize's (whitespace tokenize, return
    # Tuple of (start, len) pairs) — only the variant name on the pattern
    # head is substituted. The body uses `text`, `evaluate()`, etc. and
    # needs no name substitution.
    {
        "home":        "term_rs_evaluator_arm_home",
        "target_path": "src/term.rs",
        "anchor":      (
            "        TermNode::Tokenize { text } => {\n"
            "            let tv = evaluate(arena, *text, env, ctx);\n"
            "            let Value::Str(sym) = tv else {\n"
            "                return Value::Tuple(std::sync::Arc::new(smallvec::smallvec![]));\n"
            "            };\n"
            "            let s = ctx.interner.resolve(sym);\n"
            "            let mut positions: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];\n"
            "            let base = s.as_ptr() as usize;\n"
            "            for tok in s.split_whitespace() {\n"
            "                let start = (tok.as_ptr() as usize) - base;\n"
            "                let len = tok.len();\n"
            "                positions.push(Value::Tuple(std::sync::Arc::new(\n"
            "                    smallvec::smallvec![Value::Int(start as i64), Value::Int(len as i64)]\n"
            "                )));\n"
            "            }\n"
            "            Value::Tuple(std::sync::Arc::new(positions))\n"
            "        }"
        ),
        "parts": [
            "\n\n        TermNode::",
            _NAME,
            " { text } => {\n"
            "            let tv = evaluate(arena, *text, env, ctx);\n"
            "            let Value::Str(sym) = tv else {\n"
            "                return Value::Tuple(std::sync::Arc::new(smallvec::smallvec![]));\n"
            "            };\n"
            "            let s = ctx.interner.resolve(sym);\n"
            "            let mut positions: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];\n"
            "            let base = s.as_ptr() as usize;\n"
            "            for tok in s.split_whitespace() {\n"
            "                let start = (tok.as_ptr() as usize) - base;\n"
            "                let len = tok.len();\n"
            "                positions.push(Value::Tuple(std::sync::Arc::new(\n"
            "                    smallvec::smallvec![Value::Int(start as i64), Value::Int(len as i64)]\n"
            "                )));\n"
            "            }\n"
            "            Value::Tuple(std::sync::Arc::new(positions))\n"
            "        }",
        ],
    },
    # 4. term.rs — children arm. Anchor is the FULL line including the
    # trailing comma; content is newline-prefixed.
    #     `        TermNode::{name} { text } => out.push(*text),`
    {
        "home":        "term_rs_children_arm_home",
        "target_path": "src/term.rs",
        "anchor":      "        TermNode::Tokenize { text } => out.push(*text),",
        "parts": [
            "\n        TermNode::",
            _NAME,
            " { text } => out.push(*text),",
        ],
    },
    # 5. jsonio.rs — name arm. Anchor is the full line including trailing
    # comma.
    #     `        TermNode::{name} { .. } => "{name}",`
    {
        "home":        "jsonio_rs_name_arm_home",
        "target_path": "src/jsonio.rs",
        "anchor":      '        TermNode::Tokenize { .. } => "Tokenize",',
        "parts": [
            "\n        TermNode::",
            _NAME,
            ' { .. } => "',
            _NAME,
            '",',
        ],
    },
    # 6. jsonio.rs — parse arm. Anchor is the COMPLETE three-line block
    # (header line, body line, closing `},`) so splicing after lands at
    # the start of the next arm.
    #     `        "{name}" => TermNode::{name} {
    #              text: child_of("text", obj, arena, interner, variant)?,
    #          },`
    {
        "home":        "jsonio_rs_parse_arm_home",
        "target_path": "src/jsonio.rs",
        "anchor":      (
            '        "Tokenize" => TermNode::Tokenize {\n'
            '            text: child_of("text", obj, arena, interner, variant)?,\n'
            '        },'
        ),
        "parts": [
            '\n        "',
            _NAME,
            '" => TermNode::',
            _NAME,
            ' {\n'
            '            text: child_of("text", obj, arena, interner, variant)?,\n'
            '        },',
        ],
    },
    # 7. jsonio.rs — serialize arm. Anchor is the COMPLETE three-line
    # block: header line, body line, closing `}`. Splicing AFTER lands at
    # the start of the next arm.
    #     `        TermNode::{name} { text } => {
    #              m.insert("text".into(), child(*text, arena, interner));
    #          }`
    {
        "home":        "jsonio_rs_serialize_arm_home",
        "target_path": "src/jsonio.rs",
        "anchor":      (
            '        TermNode::Tokenize { text } => {\n'
            '            m.insert("text".into(), child(*text, arena, interner));\n'
            '        }'
        ),
        "parts": [
            "\n        TermNode::",
            _NAME,
            ' { text } => {\n'
            '            m.insert("text".into(), child(*text, arena, interner));\n'
            '        }',
        ],
    },
    # 8. reflect.rs — describe arm. Anchor is the full line.
    #     `        TermNode::{name} { text } => ("{name}", vec![Child { name: "text", child: *text }]),`
    {
        "home":        "reflect_rs_describe_arm_home",
        "target_path": "src/reflect.rs",
        "anchor":      '        TermNode::Tokenize { text } => ("Tokenize", vec![Child { name: "text", child: *text }]),',
        "parts": [
            "\n        TermNode::",
            _NAME,
            ' { text } => ("',
            _NAME,
            '", vec![Child { name: "text", child: *text }]),',
        ],
    },
    # 9. reflect.rs — parse_from_subgraph arm. Anchor is the full line.
    #     `        "{name}" => TermNode::{name} { text: take_child!("text") },`
    {
        "home":        "reflect_rs_parse_arm_home",
        "target_path": "src/reflect.rs",
        "anchor":      '        "Tokenize" => TermNode::Tokenize { text: take_child!("text") },',
        "parts": [
            '\n        "',
            _NAME,
            '" => TermNode::',
            _NAME,
            ' { text: take_child!("text") },',
        ],
    },
    # 10. python/substrate_rs/__init__.py — constructor. Anchor is the
    # COMPLETE def + docstring + body (the whole Tokenize function), so
    # splicing after lands at the blank line before the next function.
    {
        "home":        "python_init_constructor_home",
        "target_path": "python/substrate_rs/__init__.py",
        "anchor":      (
            "def Tokenize(text: Term) -> Term:\n"
            '    """Whitespace-tokenize a string; returns tuple of (start, byte_len)\n'
            '    position pairs. Agent-built via babble loop."""\n'
            '    return Term("Tokenize", text=text)'
        ),
        "parts": [
            "\n\n\ndef ",
            _NAME,
            '(text: Term) -> Term:\n    return Term("',
            _NAME,
            '", text=text)',
        ],
    },
]


# ---------------------------------------------------------------------------
# Trigger plumbing.
# ---------------------------------------------------------------------------

_TRIGGER_MT_NAME = "phase3_trigger"
_TRIGGER_EDGE = "has_primitive_spec"


def _find_or_create_trigger_mt(substrate) -> int:
    """Idempotent: find (or mint) the sentinel `phase3_trigger`
    Microtheory the rules' match patterns key off."""
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == _TRIGGER_MT_NAME:
            return n
    return substrate.add_node("Microtheory", {
        "name":        _TRIGGER_MT_NAME,
        "description": ("Sentinel Mt whose has_primitive_spec edges fire the "
                        "phase-3 RewriteRules. Each PrimitiveSpec the agent "
                        "creates is wired here so the rule engine has an edge "
                        "to match on (match_edges cannot be empty)."),
        "origin":      "phase3_rules",
    })


def _ensure_productions(substrate) -> None:
    """Open productions so the trigger edge and the DesignedPatch nodes
    the rules emit pass grammar admissibility. Idempotent — failures
    (duplicate production, etc.) are swallowed."""
    prods = [
        # Trigger edge: Mt -> PrimitiveSpec.
        ("Microtheory", _TRIGGER_EDGE, "PrimitiveSpec",
         "phase3_rules:trigger_edge"),
        # The rules emit DesignedPatch via add_node — admission of the
        # NODE type isn't grammar-gated, but downstream edges from the
        # PrimitiveSpec to its DesignedPatches (used in phase 4 traceback,
        # not in this module's effects) would be.
        ("PrimitiveSpec", "emits_patch", "DesignedPatch",
         "phase3_rules:emits_patch"),
    ]
    for src_t, edge_t, tgt_t, prov in prods:
        try:
            substrate.add_production({
                "src":        {"type": src_t, "var": "s"},
                "edge_type":  edge_t,
                "tgt":        {"type": tgt_t, "var": "t"},
                "where":      None,
                "weight":     {"type": "Lit", "value": 1.0},
                "provenance": prov,
            })
        except Exception:
            pass


def wire_existing_specs(substrate, trigger_mt: int | None = None) -> int:
    """Mint a `has_primitive_spec` edge from the sentinel Mt to every
    PrimitiveSpec that doesn't yet have one. Returns the number of new
    edges. Callers should re-invoke this after creating new PrimitiveSpec
    nodes so subsequent ticks pick them up."""
    if trigger_mt is None:
        trigger_mt = _find_or_create_trigger_mt(substrate)
    _ensure_productions(substrate)
    n_wired = 0
    existing = set(substrate.neighbours(trigger_mt, _TRIGGER_EDGE))
    for spec in substrate.nodes("PrimitiveSpec"):
        if spec in existing:
            continue
        try:
            substrate.add_edge(trigger_mt, _TRIGGER_EDGE, spec, {})
            n_wired += 1
        except Exception:
            # Grammar may reject if a different upstream seeder added
            # a divergent edge schema; try unchecked.
            try:
                substrate.add_edge_unchecked(
                    trigger_mt, _TRIGGER_EDGE, spec, {})
                n_wired += 1
            except Exception:
                pass
    return n_wired


# ---------------------------------------------------------------------------
# Rule construction.
# ---------------------------------------------------------------------------

def _rule_for_home(home_spec: dict) -> dict:
    """Build one RewriteRule JSON dict. The rule:
      MATCH:  the sentinel Mt -> has_primitive_spec -> PrimitiveSpec
              (binding the spec to "spec").
      WHERE:  none (every wired spec gets a patch for this home; phase 4
              may add a `where` filtering by semantic_kind).
      EFFECT: add a DesignedPatch with literal target_path/anchor/position
              and a StringConcat-computed content composed from the
              home's `parts` list — every `_NAME` sentinel becomes
              `Attr(Var("spec"), "name")`, every other entry becomes
              `Lit(<str>)`. The variant's name is therefore spliced in
              EVERY position it appears in the template (e.g. the
              jsonio name-arm splices it twice: pattern + string tag).
    """
    name = f"phase3_emit_{home_spec['home']}"

    concat_parts: list[dict] = []
    for piece in home_spec["parts"]:
        if piece is _NAME:
            concat_parts.append(_attr(_var("spec"), "name"))
        else:
            # piece is a literal string fragment of the template.
            concat_parts.append(_lit(piece))
    content_term = _concat(*concat_parts)
    # Anchor is a fixed literal — the splice point is the same for any
    # spec that lands in this home. The home itself encodes the file +
    # the exemplar's verbatim line.
    return {
        "name":  name,
        "match": [["trigger", _TRIGGER_EDGE, "spec"]],
        "where": None,
        "effects": [[
            "add_node", "patch", "DesignedPatch", {
                "target_path": home_spec["target_path"],
                "anchor":      home_spec["anchor"],
                "position":    "after",
                "content":     _computed(content_term),
                "home":        home_spec["home"],
                "origin":      "phase3_rules",
            },
        ]],
    }


def build_phase3_rules() -> list[dict]:
    """Return the ten phase-3 RewriteRule dicts. No substrate state
    touched — usable for inspection / golden tests / phase 4."""
    return [_rule_for_home(h) for h in _HOMES]


def install_phase3_rules(substrate, world=None) -> dict:
    """Install the phase-3 RewriteRules + trigger plumbing.

    Steps:
      1. Open productions for the sentinel trigger edge + emits_patch.
      2. Create (idempotently) the `phase3_trigger` sentinel Microtheory.
      3. Wire every existing PrimitiveSpec to it via has_primitive_spec.
      4. add_rule for each of the ten home rules.

    `world` is accepted for symmetry with phase 2's installer but is
    only consulted to record provenance on the sentinel Mt; if None,
    the rules + trigger still install fine.

    Returns:
      {
        "trigger_mt":   NodeID,
        "rules":        list[(name, rule_idx)],
        "wired_specs":  int,
        "homes":        list[str],  # the home names installed
      }
    """
    trigger_mt = _find_or_create_trigger_mt(substrate)
    _ensure_productions(substrate)
    n_wired = wire_existing_specs(substrate, trigger_mt)

    if world is not None:
        try:
            substrate.set_attr(trigger_mt, "world_kind",
                               type(world).__name__)
        except Exception:
            pass

    installed = []
    for home in _HOMES:
        rule = _rule_for_home(home)
        try:
            idx = substrate.add_rule(rule)
            installed.append((rule["name"], idx))
        except Exception as exc:
            installed.append((rule["name"], f"add_rule_failed: {exc}"))

    return {
        "trigger_mt":   trigger_mt,
        "rules":        installed,
        "wired_specs":  n_wired,
        "homes":        [h["home"] for h in _HOMES],
    }


__all__ = [
    "install_phase3_rules",
    "build_phase3_rules",
    "wire_existing_specs",
]
