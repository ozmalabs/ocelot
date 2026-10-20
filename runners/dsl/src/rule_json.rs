//! Rule and Effect JSON wire format serialization and deserialization.
//! Ported out of `py.rs` so that rule serialization is available unconditionally
//! without requiring PyO3 / CPython runtime symbols.

use crate::jsonio::{term_from_json, term_to_json};
use crate::persist::{decode_value, encode_value};
use crate::rewrite::{
    Effect, EffectArg, IndexJoinHint, IndexProbe, MatchEdge, RewriteRule, RuleUid, ScopeAnchor,
};
use crate::sym::{Interner, Sym};
use crate::term::TermArena;
use serde_json::{Map, Value as J};

/// Parse a rule dict into a Rust [`crate::rewrite::RewriteRule`].
/// Mirrors the encoding the existing `domains/graph_rewrite.py` uses
/// for storage so a rule authored in Python or JSON is usable here without
/// reshape.
/// Public wrapper around `parse_rule_json` so other Rust modules
/// (e.g. `codec`, `substrate`) can parse the same JSON dialect.
pub fn parse_rule_json_pub(
    j: &serde_json::Value,
    terms: &mut TermArena,
    interner: &mut Interner,
) -> Result<RewriteRule, String> {
    let terms_before = terms.nodes.len();
    let symbols_before = interner.len();
    match parse_rule_json(j, terms, interner) {
        Ok(rule) => Ok(rule),
        Err(err) => {
            terms.nodes.truncate(terms_before);
            interner.truncate(symbols_before);
            Err(err)
        }
    }
}

pub fn parse_rule_json(
    j: &J,
    terms: &mut TermArena,
    interner: &mut Interner,
) -> Result<RewriteRule, String> {
    let obj = j
        .as_object()
        .ok_or_else(|| "rule must be an object".to_string())?;
    let name = obj
        .get("name")
        .and_then(|v| v.as_str())
        .unwrap_or("anonymous_rule");
    let schedule_explicit =
        obj.contains_key("area") || obj.contains_key("order") || obj.contains_key("latency_class");
    let uid = obj.get("rule_uid").and_then(|v| v.as_u64()).unwrap_or(0);
    let revision = obj.get("revision").and_then(|v| v.as_u64()).unwrap_or(0);
    let mutation_protected = obj
        .get("mutation_protected")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);
    // Do not intern derived defaults: interner allocation order is observable
    // in this non-confluent runtime. Legacy rules must not move one Sym.
    let area = obj
        .get("area")
        .and_then(|v| v.as_str())
        .map(|v| interner.intern(v))
        .unwrap_or_default();
    let order = obj.get("order").and_then(|v| v.as_u64()).unwrap_or(0) as u32;
    let latency_class = obj
        .get("latency_class")
        .and_then(|v| v.as_str())
        .map(|v| interner.intern(v))
        .unwrap_or_default();

    let match_arr = obj
        .get("match")
        .and_then(|v| v.as_array())
        .ok_or_else(|| "missing or non-array 'match'".to_string())?;
    let mut match_edges = Vec::with_capacity(match_arr.len());
    for me in match_arr {
        let arr = me
            .as_array()
            .ok_or_else(|| "match item must be array".to_string())?;
        if arr.len() != 3 {
            return Err(
                "match item must have 3 elements: [src_var, edge_type, tgt_var]".to_string(),
            );
        }
        let src_var = arr[0]
            .as_str()
            .ok_or_else(|| "match src_var must be str".to_string())?;
        let edge_type = arr[1]
            .as_str()
            .ok_or_else(|| "match edge_type must be str".to_string())?;
        let tgt_var = arr[2]
            .as_str()
            .ok_or_else(|| "match tgt_var must be str".to_string())?;
        match_edges.push(MatchEdge {
            src_var: interner.intern(src_var),
            edge_type: interner.intern(edge_type),
            tgt_var: interner.intern(tgt_var),
        });
    }

    let where_ = match obj.get("where") {
        Some(J::Null) | None => None,
        Some(other) => Some(
            term_from_json(other, terms, interner)
                .map_err(|e| format!("bad where Term: {:?}", e))?,
        ),
    };

    let effects_arr = obj
        .get("effects")
        .and_then(|v| v.as_array())
        .map(|a| a.as_slice())
        .unwrap_or(&[]);
    let mut effects = Vec::with_capacity(effects_arr.len());
    for ef in effects_arr {
        effects.push(parse_effect_json(ef, terms, interner)?);
    }

    let batch = obj.get("batch").and_then(|v| v.as_bool()).unwrap_or(false);
    let match_type = obj
        .get("match_type")
        .and_then(|v| v.as_str())
        .map(|s| interner.intern(s));
    let scope_anchor_keys = [
        "scope_anchor_var",
        "scope_anchor_type",
        "scope_anchor_owner_var",
        "scope_anchor_owner_type",
        "scope_anchor_owner_edge",
    ];
    let scope_anchor_values: Vec<Option<&str>> = scope_anchor_keys
        .iter()
        .map(|key| obj.get(*key).and_then(|value| value.as_str()))
        .collect();
    let scope_anchor_present = scope_anchor_values.iter().filter(|v| v.is_some()).count();
    let scope_anchor = match scope_anchor_present {
        0 => None,
        5 => Some(ScopeAnchor {
            anchor_var: interner.intern(scope_anchor_values[0].unwrap()),
            anchor_type: interner.intern(scope_anchor_values[1].unwrap()),
            owner_var: interner.intern(scope_anchor_values[2].unwrap()),
            owner_type: interner.intern(scope_anchor_values[3].unwrap()),
            owner_edge: interner.intern(scope_anchor_values[4].unwrap()),
        }),
        _ => return Err("scope anchor requires all five scope_anchor_* string fields".to_string()),
    };

    // R10 (join-index wave): optional "index_hints"
    let mut index_hints = Vec::new();
    if let Some(arr) = obj.get("index_hints").and_then(|v| v.as_array()) {
        for h in arr {
            let ho = h
                .as_object()
                .ok_or_else(|| "index_hints item must be an object".to_string())?;
            let get_str = |k: &str| -> Result<&str, String> {
                ho.get(k)
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| format!("index_hints item missing string field {k:?}"))
            };
            let probe = if let Some(literal) = ho.get("probe_value") {
                let value = literal.as_str().ok_or_else(|| {
                    "index_hints probe_value currently requires a string literal".to_string()
                })?;
                IndexProbe::LiteralString(interner.intern(value))
            } else {
                IndexProbe::BoundAttr {
                    via_var: interner.intern(get_str("via_var")?),
                    via_key: interner.intern(get_str("via_key")?),
                }
            };
            index_hints.push(IndexJoinHint {
                for_var: interner.intern(get_str("for_var")?),
                probe,
                node_type: interner.intern(get_str("node_type")?),
                this_key: interner.intern(get_str("this_key")?),
            });
        }
    }

    Ok(RewriteRule {
        uid: RuleUid(uid),
        revision,
        mutation_protected,
        name: interner.intern(name),
        area,
        order,
        latency_class,
        schedule_explicit,
        match_edges,
        where_,
        effects,
        batch,
        match_type,
        scope_anchor,
        index_hints,
        ..Default::default()
    })
}

/// Serialise one installed rule (including its `active` tombstone flag) to
/// the `add_rule` dict dialect.
pub fn rule_to_json(
    rule: &RewriteRule,
    terms: &TermArena,
    interner: &Interner,
) -> J {
    let match_arr: Vec<J> = rule
        .match_edges
        .iter()
        .map(|me| {
            serde_json::json!([
                interner.resolve(me.src_var),
                interner.resolve(me.edge_type),
                interner.resolve(me.tgt_var),
            ])
        })
        .collect();
    let where_j = match rule.where_ {
        Some(idx) => term_to_json(terms, idx, interner),
        None => J::Null,
    };
    let effects_j: Vec<J> = rule
        .effects
        .iter()
        .map(|e| effect_to_json(e, terms, interner))
        .collect();
    let match_type_j = match rule.match_type {
        Some(s) => J::String(interner.resolve(s).to_string()),
        None => J::Null,
    };
    let mut out = serde_json::json!({
        "rule_uid": rule.uid.0,
        "revision": rule.revision,
        "content_hash": rule.content_hash,
        "name": interner.resolve(rule.name),
        "match": match_arr,
        "where": where_j,
        "effects": effects_j,
        "batch": rule.batch,
        "match_type": match_type_j,
        "active": rule.active,
    });
    if let Some(anchor) = rule.scope_anchor {
        out["scope_anchor_var"] = J::String(interner.resolve(anchor.anchor_var).to_string());
        out["scope_anchor_type"] = J::String(interner.resolve(anchor.anchor_type).to_string());
        out["scope_anchor_owner_var"] = J::String(interner.resolve(anchor.owner_var).to_string());
        out["scope_anchor_owner_type"] = J::String(interner.resolve(anchor.owner_type).to_string());
        out["scope_anchor_owner_edge"] = J::String(interner.resolve(anchor.owner_edge).to_string());
    }
    if !rule.index_hints.is_empty() {
        let index_hints_j: Vec<J> = rule
            .index_hints
            .iter()
            .map(|h| {
                let mut item = Map::new();
                item.insert(
                    "for_var".into(),
                    J::String(interner.resolve(h.for_var).to_string()),
                );
                item.insert(
                    "node_type".into(),
                    J::String(interner.resolve(h.node_type).to_string()),
                );
                item.insert(
                    "this_key".into(),
                    J::String(interner.resolve(h.this_key).to_string()),
                );
                match &h.probe {
                    IndexProbe::BoundAttr { via_var, via_key } => {
                        item.insert(
                            "via_var".into(),
                            J::String(interner.resolve(*via_var).to_string()),
                        );
                        item.insert(
                            "via_key".into(),
                            J::String(interner.resolve(*via_key).to_string()),
                        );
                    }
                    IndexProbe::LiteralString(value) => {
                        item.insert(
                            "probe_value".into(),
                            J::String(interner.resolve(*value).to_string()),
                        );
                    }
                }
                J::Object(item)
            })
            .collect();
        out["index_hints"] = J::Array(index_hints_j);
    }
    if rule.mutation_protected {
        out["mutation_protected"] = J::Bool(true);
    }
    if rule.schedule_explicit {
        out["area"] = J::String(interner.resolve(rule.area).to_string());
        out["order"] = J::Number(serde_json::Number::from(rule.order));
        out["latency_class"] = J::String(interner.resolve(rule.latency_class).to_string());
    }
    out
}

pub fn effect_arg_to_json(
    arg: &EffectArg,
    terms: &TermArena,
    interner: &Interner,
) -> J {
    match arg {
        EffectArg::Literal(v) => encode_value(v, interner),
        EffectArg::Computed(idx) => {
            serde_json::json!({ "__term__": term_to_json(terms, *idx, interner) })
        }
    }
}

pub fn attrs_to_json(
    attrs: &[(Sym, EffectArg)],
    terms: &TermArena,
    interner: &Interner,
) -> J {
    let mut m = Map::with_capacity(attrs.len());
    for (k, v) in attrs {
        m.insert(
            interner.resolve(*k).to_string(),
            effect_arg_to_json(v, terms, interner),
        );
    }
    J::Object(m)
}

pub fn effect_to_json(
    eff: &Effect,
    terms: &TermArena,
    interner: &Interner,
) -> J {
    use Effect as E;
    let s = |sym: Sym| interner.resolve(sym).to_string();
    match eff {
        E::AddEdge {
            src_var,
            edge_type,
            tgt_var,
            attrs,
        } => J::Array(vec![
            J::String("add_edge".into()),
            J::String(s(*src_var)),
            J::String(s(*edge_type)),
            J::String(s(*tgt_var)),
            attrs_to_json(attrs, terms, interner),
        ]),
        E::DelEdge {
            src_var,
            edge_type,
            tgt_var,
        } => J::Array(vec![
            J::String("del_edge".into()),
            J::String(s(*src_var)),
            J::String(s(*edge_type)),
            J::String(s(*tgt_var)),
        ]),
        E::AddNode {
            new_var,
            type_,
            attrs,
        } => J::Array(vec![
            J::String("add_node".into()),
            J::String(s(*new_var)),
            J::String(s(*type_)),
            attrs_to_json(attrs, terms, interner),
        ]),
        E::AddNodeIfAbsent {
            new_var,
            type_,
            attrs,
        } => J::Array(vec![
            J::String("add_node_if_absent".into()),
            J::String(s(*new_var)),
            J::String(s(*type_)),
            attrs_to_json(attrs, terms, interner),
        ]),
        E::DelNode { var } => J::Array(vec![J::String("del_node".into()), J::String(s(*var))]),
        E::SetAttr { var, key, value } => J::Array(vec![
            J::String("set_attr".into()),
            J::String(s(*var)),
            J::String(s(*key)),
            effect_arg_to_json(value, terms, interner),
        ]),
        E::SetAttrIfDifferent { var, key, value } => J::Array(vec![
            J::String("set_attr_if_different".into()),
            J::String(s(*var)),
            J::String(s(*key)),
            effect_arg_to_json(value, terms, interner),
        ]),
        E::ReplaceValue { old_var, new_var } => J::Array(vec![
            J::String("replace_value".into()),
            J::String(s(*old_var)),
            J::String(s(*new_var)),
        ]),
        E::DefineConcept { name, term } => J::Array(vec![
            J::String("define_concept".into()),
            effect_arg_to_json(name, terms, interner),
            effect_arg_to_json(term, terms, interner),
        ]),
        E::SetRuleClause {
            rule_name,
            field,
            term,
        } => J::Array(vec![
            J::String("set_rule_clause".into()),
            effect_arg_to_json(rule_name, terms, interner),
            effect_arg_to_json(field, terms, interner),
            effect_arg_to_json(term, terms, interner),
        ]),
        E::ApplyRulePatch { patch_var } => J::Array(vec![
            J::String("apply_rule_patch".into()),
            J::String(s(*patch_var)),
        ]),
        E::FbSample {
            fb,
            game_var,
            grid_w,
            grid_h,
        } => J::Array(vec![
            J::String("fb_sample".into()),
            effect_arg_to_json(fb, terms, interner),
            J::String(s(*game_var)),
            effect_arg_to_json(grid_w, terms, interner),
            effect_arg_to_json(grid_h, terms, interner),
        ]),
        E::NetCollapse {
            reflex_net,
            input,
            target,
            eta,
        } => J::Array(vec![
            J::String("net_collapse".into()),
            J::String(s(*reflex_net)),
            effect_arg_to_json(input, terms, interner),
            effect_arg_to_json(target, terms, interner),
            effect_arg_to_json(eta, terms, interner),
        ]),
        E::TrackIdentity {
            prev,
            cur,
            feature_key,
            category_key,
            extent_key,
            identity_key,
            radius,
        } => {
            let cat_val = match category_key {
                Some(k) => J::String(s(*k)),
                None => J::Null,
            };
            let ext_val = match extent_key {
                Some(k) => J::String(s(*k)),
                None => J::Null,
            };
            J::Array(vec![
                J::String("track_identity".into()),
                effect_arg_to_json(prev, terms, interner),
                effect_arg_to_json(cur, terms, interner),
                J::String(s(*feature_key)),
                cat_val,
                ext_val,
                J::String(s(*identity_key)),
                effect_arg_to_json(radius, terms, interner),
            ])
        }
    }
}

pub fn parse_effect_json(
    j: &J,
    terms: &mut TermArena,
    interner: &mut Interner,
) -> Result<Effect, String> {
    let arr = j
        .as_array()
        .ok_or_else(|| "effect must be an array".to_string())?;
    let kind = arr
        .first()
        .and_then(|v| v.as_str())
        .ok_or_else(|| "effect kind missing".to_string())?;
    let s = |i: usize| -> Result<String, String> {
        arr.get(i)
            .and_then(|v| v.as_str())
            .map(String::from)
            .ok_or_else(|| format!("effect arg {} must be str", i))
    };
    let arg_to_effect = |v: &J,
                         terms: &mut TermArena,
                         interner: &mut Interner|
     -> Result<EffectArg, String> {
        if let Some(obj) = v.as_object() {
            if let Some(inner) = obj.get("__term__") {
                let idx = term_from_json(inner, terms, interner)
                    .map_err(|e| format!("bad computed effect arg: {:?}", e))?;
                return Ok(EffectArg::Computed(idx));
            }
        }
        Ok(EffectArg::Literal(decode_value(v, interner)))
    };
    let attrs_dict = |arr_i: usize,
                      terms: &mut TermArena,
                      interner: &mut Interner|
     -> Result<Vec<(Sym, EffectArg)>, String> {
        let Some(raw) = arr.get(arr_i) else {
            return Ok(Vec::new());
        };
        let obj = raw
            .as_object()
            .ok_or_else(|| format!("effect attrs at {} must be object", arr_i))?;
        let mut out = Vec::with_capacity(obj.len());
        for (k, v) in obj {
            let arg = arg_to_effect(v, terms, interner)?;
            out.push((interner.intern(k), arg));
        }
        Ok(out)
    };
    match kind {
        "add_edge" => Ok(Effect::AddEdge {
            src_var: interner.intern(&s(1)?),
            edge_type: interner.intern(&s(2)?),
            tgt_var: interner.intern(&s(3)?),
            attrs: attrs_dict(4, terms, interner)?,
        }),
        "del_edge" => Ok(Effect::DelEdge {
            src_var: interner.intern(&s(1)?),
            edge_type: interner.intern(&s(2)?),
            tgt_var: interner.intern(&s(3)?),
        }),
        "add_node" => Ok(Effect::AddNode {
            new_var: interner.intern(&s(1)?),
            type_: interner.intern(&s(2)?),
            attrs: attrs_dict(3, terms, interner)?,
        }),
        "add_node_if_absent" => Ok(Effect::AddNodeIfAbsent {
            new_var: interner.intern(&s(1)?),
            type_: interner.intern(&s(2)?),
            attrs: attrs_dict(3, terms, interner)?,
        }),
        "del_node" => Ok(Effect::DelNode {
            var: interner.intern(&s(1)?),
        }),
        "set_attr" => {
            let var = interner.intern(&s(1)?);
            let key = interner.intern(&s(2)?);
            let raw = arr
                .get(3)
                .ok_or_else(|| "set_attr missing value".to_string())?;
            let value = arg_to_effect(raw, terms, interner)?;
            Ok(Effect::SetAttr { var, key, value })
        }
        "set_attr_if_different" => {
            let var = interner.intern(&s(1)?);
            let key = interner.intern(&s(2)?);
            let raw = arr
                .get(3)
                .ok_or_else(|| "set_attr_if_different missing value".to_string())?;
            let value = arg_to_effect(raw, terms, interner)?;
            Ok(Effect::SetAttrIfDifferent { var, key, value })
        }
        "replace_value" => Ok(Effect::ReplaceValue {
            old_var: interner.intern(&s(1)?),
            new_var: interner.intern(&s(2)?),
        }),
        "define_concept" => {
            let name_raw = arr
                .get(1)
                .ok_or_else(|| "define_concept missing name".to_string())?;
            let name = arg_to_effect(name_raw, terms, interner)?;
            let term_raw = arr
                .get(2)
                .ok_or_else(|| "define_concept missing term".to_string())?;
            let term = arg_to_effect(term_raw, terms, interner)?;
            Ok(Effect::DefineConcept { name, term })
        }
        "set_rule_clause" => {
            let rule_name = arg_to_effect(
                arr.get(1)
                    .ok_or_else(|| "set_rule_clause missing rule_name".to_string())?,
                terms,
                interner,
            )?;
            let field = arg_to_effect(
                arr.get(2)
                    .ok_or_else(|| "set_rule_clause missing field".to_string())?,
                terms,
                interner,
            )?;
            let term = arg_to_effect(
                arr.get(3)
                    .ok_or_else(|| "set_rule_clause missing clause term".to_string())?,
                terms,
                interner,
            )?;
            Ok(Effect::SetRuleClause {
                rule_name,
                field,
                term,
            })
        }
        "apply_rule_patch" => Ok(Effect::ApplyRulePatch {
            patch_var: interner.intern(&s(1)?),
        }),
        "fb_sample" => {
            let fb = arg_to_effect(
                arr.get(1)
                    .ok_or_else(|| "fb_sample missing fb_id".to_string())?,
                terms,
                interner,
            )?;
            let game_var = interner.intern(&s(2)?);
            let grid_w = arg_to_effect(
                arr.get(3)
                    .ok_or_else(|| "fb_sample missing grid_w".to_string())?,
                terms,
                interner,
            )?;
            let grid_h = arg_to_effect(
                arr.get(4)
                    .ok_or_else(|| "fb_sample missing grid_h".to_string())?,
                terms,
                interner,
            )?;
            Ok(Effect::FbSample {
                fb,
                game_var,
                grid_w,
                grid_h,
            })
        }
        "net_collapse" => {
            let reflex_net = interner.intern(&s(1)?);
            let input = arg_to_effect(
                arr.get(2)
                    .ok_or_else(|| "net_collapse missing input".to_string())?,
                terms,
                interner,
            )?;
            let target = arg_to_effect(
                arr.get(3)
                    .ok_or_else(|| "net_collapse missing target".to_string())?,
                terms,
                interner,
            )?;
            let eta = arg_to_effect(
                arr.get(4)
                    .ok_or_else(|| "net_collapse missing eta".to_string())?,
                terms,
                interner,
            )?;
            Ok(Effect::NetCollapse {
                reflex_net,
                input,
                target,
                eta,
            })
        }
        "track_identity" => {
            let prev = arg_to_effect(
                arr.get(1)
                    .ok_or_else(|| "track_identity missing prev".to_string())?,
                terms,
                interner,
            )?;
            let cur = arg_to_effect(
                arr.get(2)
                    .ok_or_else(|| "track_identity missing cur".to_string())?,
                terms,
                interner,
            )?;
            let feature_key = interner.intern(&s(3)?);
            let category_key = match arr.get(4) {
                Some(J::String(k)) => Some(interner.intern(k)),
                _ => None,
            };
            let extent_key = match arr.get(5) {
                Some(J::String(k)) => Some(interner.intern(k)),
                _ => None,
            };
            let identity_key = interner.intern(&s(6)?);
            let radius = arg_to_effect(
                arr.get(7)
                    .ok_or_else(|| "track_identity missing radius".to_string())?,
                terms,
                interner,
            )?;
            Ok(Effect::TrackIdentity {
                prev,
                cur,
                feature_key,
                category_key,
                extent_key,
                identity_key,
                radius,
            })
        }
        other => Err(format!("unknown effect kind: {}", other)),
    }
}
