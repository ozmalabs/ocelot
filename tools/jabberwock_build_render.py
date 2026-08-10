"""The jabberwock builds its own render engine — fills in the stubbed Rust
`Render` evaluator (the deferred "Phase 6" engine) via the self-modification
keystone: backup -> apply -> cargo check -> rollback-on-failure -> audit, then
rebuild the native layer. All-or-nothing; a failed build leaves term.rs
byte-identical.

The Render term re-dispatches per source-Term head + target language. Source
terms are `Term.<Variant>` subgraph nodes (reflect.rs), children on
`child.<field>` edges; a Language node carries `has_rule` RenderRules with a
`head` attr, a `binding_pattern` tuple of slot names, and a `template` edge to a
Surface/Cat/Slot/Render Term subgraph. The engine: resolve the source node, find
the matching RenderRule, bind its binding_pattern slots to the source's children,
and EvalSubgraph the template under that env — nested Render(Slot) terms recurse
on the bound children. Pure graph composition over existing primitives; shares
the holds_depth recursion budget.
"""
from __future__ import annotations

from domains.self_modification import SelfModification

OLD = '''        TermNode::Render { .. } => {
            // Render dispatches to a registered renderer Term per source
            // kind + target language. The full registry lives in the
            // engine extension layer (Phase 6); for now return None to
            // surface as "render gap".
            Value::None
        }'''

NEW = '''        TermNode::Render { term, lang } => {
            // Render a source Term (a `Term.*` subgraph node) into a Surface via
            // the named Language's RenderRules. `term` evaluates to the source
            // Node; `lang` (or env "render_lang") to the Language Node. Find the
            // RenderRule whose `head` matches the source variant, bind its
            // binding_pattern slots to the source's `child.<name>` children, and
            // evaluate the rule's `template` subgraph under that env — nested
            // Render(Slot) sub-terms recurse on the bound children. None on a
            // render gap (no matching rule). Shares the holds_depth budget.
            let Some(t) = term else { return Value::None; };
            let Value::Node(src_nid) = evaluate(arena, *t, env, ctx) else {
                return Value::None;
            };
            if !ctx.graph.has_node(src_nid) {
                return Value::None;
            }
            let lang_val = match lang {
                Some(l) => evaluate(arena, *l, env, ctx),
                None => ctx
                    .interner
                    .lookup("render_lang")
                    .and_then(|s| env_get(env, s).cloned())
                    .unwrap_or(Value::None),
            };
            let Value::Node(lang_nid) = lang_val else {
                return Value::None;
            };
            if ctx.holds_depth > 256 {
                return Value::None;
            }
            // head = source node type with the "Term." prefix stripped.
            let ty_str = ctx.interner.resolve(ctx.graph.node(src_nid).type_);
            let head = ty_str.strip_prefix("Term.").unwrap_or(ty_str).to_string();
            let (Some(has_rule), Some(head_key)) =
                (ctx.interner.lookup("has_rule"), ctx.interner.lookup("head"))
            else {
                return Value::None;
            };
            let mut rule_nid: Option<NodeID> = None;
            for r in ctx.graph.neighbours(lang_nid, Some(has_rule)) {
                if let Some(Value::Str(h)) = ctx.graph.node(r).attrs.get(&head_key) {
                    if ctx.interner.resolve(*h) == head.as_str() {
                        rule_nid = Some(r);
                        break;
                    }
                }
            }
            let Some(rule_nid) = rule_nid else {
                return Value::None;
            };
            // Bind binding_pattern slots to the source's child.<name> children.
            let mut pushed = 0usize;
            if let Some(bp_key) = ctx.interner.lookup("binding_pattern") {
                if let Some(bp) = ctx.graph.node(rule_nid).attrs.get(&bp_key) {
                    let names: Vec<Value> = match bp {
                        Value::Tuple(t) => t.iter().cloned().collect(),
                        Value::Set(s) | Value::FrozenSet(s) => s.to_vec(),
                        _ => Vec::new(),
                    };
                    for nv in names {
                        let Value::Str(name_sym) = nv else { continue; };
                        // A binding name is either a child Term (on a
                        // `child.<name>` edge -> bind the child Node) or a scalar
                        // field (a node attr -> bind the attr Value directly).
                        let edge_name =
                            format!("child.{}", ctx.interner.resolve(name_sym));
                        let bound = ctx
                            .interner
                            .lookup(&edge_name)
                            .and_then(|esym| {
                                ctx.graph.neighbours(src_nid, Some(esym)).first().copied()
                            })
                            .map(Value::Node)
                            .or_else(|| {
                                ctx.graph.node(src_nid).attrs.get(&name_sym).cloned()
                            });
                        if let Some(v) = bound {
                            env.push((name_sym, v));
                            pushed += 1;
                        }
                    }
                }
            }
            // Evaluate the template subgraph under the slot env.
            let mut result = Value::None;
            if let Some(tmpl_key) = ctx.interner.lookup("template") {
                let tmpls = ctx.graph.neighbours(rule_nid, Some(tmpl_key));
                if let Some(&tmpl_nid) = tmpls.first() {
                    let mut tmp = TermArena::new();
                    if let Ok(sub) = crate::reflect::term_from_subgraph(
                        ctx.graph,
                        ctx.interner,
                        tmpl_nid,
                        &mut tmp,
                    ) {
                        ctx.holds_depth += 1;
                        result = evaluate(&tmp, sub, env, ctx);
                        ctx.holds_depth -= 1;
                    }
                }
            }
            for _ in 0..pushed {
                env.pop();
            }
            result
        }'''


def main() -> int:
    mod = SelfModification()
    res = mod.edit("runners/dsl/src/term.rs", OLD, NEW, check=True)
    print("edit:", res)
    if not res.get("ok"):
        print("ABORTED (rolled back if applied) — tree unchanged.")
        return 1
    rb = mod.rebuild_native()
    print("rebuild:", {k: rb.get(k) for k in ("ok",)})
    if not rb.get("ok"):
        mod.restore("runners/dsl/src/term.rs")
        mod.rebuild_native()
        print("REBUILD FAILED — restored + resynced. tail:", rb.get("tail", "")[-400:])
        return 1
    print("OK — Render evaluator built + native layer rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
