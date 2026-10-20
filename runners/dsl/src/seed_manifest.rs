//! Seed manifest parsing and installation directly onto the Substrate runtime.
//!
//! Provides a pure Rust loader for `seeds/*.json` manifests, decoupled from PyO3.
//! Used by both the Python binding (`py.rs`) and the WebAssembly binding (`runners/wasm`).

use crate::graph::{NodeData, NodeID};
use crate::jsonio::{grammar_from_json, term_from_json};
use crate::persist::decode_value;
use crate::rule_json::parse_rule_json;
use crate::substrate::Substrate;
use crate::sym::{Interner, Sym};
use crate::value::Value;
use rustc_hash::FxHashMap;
use serde_json::Value as J;

#[derive(Debug, Clone, Default, serde::Serialize, serde::Deserialize)]
pub struct SeedLoadSummary {
    pub id: Option<String>,
    pub nodes: usize,
    pub edges: usize,
    pub productions: usize,
    pub rules: usize,
    pub rules_skipped: Vec<String>,
    pub reflexes: usize,
    pub reflexes_skipped: Vec<String>,
    pub local_node_ids: Vec<(u64, u32)>,
}

pub fn decode_attrs_object(
    attrs: Option<&J>,
    interner: &mut Interner,
) -> FxHashMap<Sym, Value> {
    let mut out = FxHashMap::default();
    if let Some(J::Object(m)) = attrs {
        for (k, v) in m {
            let k_sym = interner.intern(k);
            out.insert(k_sym, decode_value(v, interner));
        }
    }
    out
}

pub fn resolve_seed_ref(
    raw: Option<&J>,
    local_to_global: &FxHashMap<u64, NodeID>,
    root_node: Option<NodeID>,
    inner: &Substrate,
) -> Result<NodeID, String> {
    let obj = raw
        .and_then(|v| v.as_object())
        .ok_or_else(|| "seed ref must be an object".to_string())?;
    if let Some(J::Number(n)) = obj.get("local") {
        if let Some(u) = n.as_u64() {
            return local_to_global.get(&u).copied().ok_or_else(|| {
                format!("seed ref local={} unresolved (out-of-order edge)", u)
            });
        }
    }
    if let Some(J::String(role)) = obj.get("role") {
        if role == "agent_root" {
            return root_node.ok_or_else(|| {
                "seed ref names role=agent_root but loader was invoked without a root_node".to_string()
            });
        }
        return Err(format!("seed ref: unknown role {:?}", role));
    }
    if let Some(J::String(kind)) = obj.get("type") {
        let Some(type_sym) = inner.interner.lookup(kind) else {
            return Err(format!("seed cross-ref to absent type {:?}", kind));
        };
        for nid in inner.graph.nodes_of_type(type_sym) {
            let n = inner.graph.node(nid);
            if seed_ref_attrs_match(obj, n, &inner.interner) {
                return Ok(nid);
            }
        }
        return Err(format!(
            "seed cross-ref {:?} unresolved (missing dep seed?)",
            obj
        ));
    }
    Err(format!("seed ref: unrecognised shape {:?}", obj))
}

pub fn seed_ref_attrs_match(
    ref_obj: &serde_json::Map<String, J>,
    node: &NodeData,
    interner: &Interner,
) -> bool {
    for (k, v) in ref_obj {
        if k == "type" {
            continue;
        }
        let Some(want_str) = v.as_str() else {
            return false;
        };
        let Some(attr_sym) = interner.lookup(k) else {
            return false;
        };
        let Some(attr_val) = node.attrs.get(&attr_sym) else {
            return false;
        };
        match attr_val {
            Value::Str(s) => {
                if interner.resolve(*s) != want_str {
                    return false;
                }
            }
            _ => return false,
        }
    }
    true
}

pub fn load_reflex_json(
    j: &J,
    inner: &mut Substrate,
    agent_root: Option<NodeID>,
) -> Result<(), String> {
    let obj = j
        .as_object()
        .ok_or_else(|| "reflex must be an object".to_string())?;
    let name = obj
        .get("name")
        .and_then(|v| v.as_str())
        .ok_or_else(|| "missing 'name'".to_string())?;
    let response = obj
        .get("response")
        .and_then(|v| v.as_str())
        .ok_or_else(|| "missing 'response'".to_string())?;
    let refractory_ticks = obj
        .get("refractory_ticks")
        .and_then(|v| v.as_i64())
        .unwrap_or(0);
    let autonomous = obj
        .get("autonomous")
        .and_then(|v| v.as_i64().or_else(|| v.as_f64().map(|f| f as i64)))
        .unwrap_or(0);
    let stimulus = obj
        .get("stimulus")
        .ok_or_else(|| "missing 'stimulus'".to_string())?;

    let terms_snapshot = inner.terms.nodes.len();
    let idx = match term_from_json(stimulus, &mut inner.terms, &mut inner.interner) {
        Ok(idx) => idx,
        Err(err) => {
            inner.terms.nodes.truncate(terms_snapshot);
            return Err(format!("bad stimulus Term: {:?}", err));
        }
    };
    let stim_root =
        crate::reflect::term_to_subgraph(&inner.terms, idx, &mut inner.graph, &mut inner.interner);
    inner.terms.nodes.truncate(terms_snapshot);

    let reflex_type = inner.interner.intern("Reflex");
    let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
    attrs.insert(
        inner.interner.intern("name"),
        Value::Str(inner.interner.intern(name)),
    );
    attrs.insert(
        inner.interner.intern("response"),
        Value::Str(inner.interner.intern(response)),
    );
    attrs.insert(
        inner.interner.intern("refractory_ticks"),
        Value::Int(refractory_ticks),
    );
    attrs.insert(
        inner.interner.intern("last_fired_tick"),
        Value::Int(-1_000_000_000),
    );
    attrs.insert(inner.interner.intern("fire_count"), Value::Int(0));
    attrs.insert(inner.interner.intern("autonomous"), Value::Int(autonomous));
    let reflex_nid = inner.add_node(reflex_type, attrs);

    let has_reflex = inner.interner.intern("has_reflex");
    let stimulus_term = inner.interner.intern("stimulus_term");
    if let Some(agent) = agent_root {
        let _ = inner
            .graph
            .insert_edge(agent, has_reflex, reflex_nid, FxHashMap::default());
    }
    let _ = inner
        .graph
        .insert_edge(reflex_nid, stimulus_term, stim_root, FxHashMap::default());
    Ok(())
}

impl Substrate {
    /// Load a parsed seed manifest into this substrate instance.
    pub fn load_seed_manifest_value(
        &mut self,
        m: &J,
        root_node: Option<NodeID>,
    ) -> Result<SeedLoadSummary, String> {
        let mut summary = SeedLoadSummary::default();

        if let Some(J::String(id)) = m.get("id") {
            summary.id = Some(id.clone());
        }

        // 1) Nodes
        let mut local_to_global: FxHashMap<u64, NodeID> = FxHashMap::default();
        if let Some(J::Array(nodes)) = m.get("nodes") {
            for n in nodes {
                let n_obj = n
                    .as_object()
                    .ok_or_else(|| "seed node must be an object".to_string())?;
                let local_id = n_obj
                    .get("local_id")
                    .and_then(|v| v.as_u64())
                    .ok_or_else(|| "seed node missing local_id".to_string())?;
                let type_str = n_obj
                    .get("type")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| "seed node missing type".to_string())?;
                let type_sym = self.interner.intern(type_str);
                let attrs = decode_attrs_object(n_obj.get("attrs"), &mut self.interner);
                let new_nid = self.add_node(type_sym, attrs);
                local_to_global.insert(local_id, new_nid);
                summary.nodes += 1;
            }
        }
        summary.local_node_ids = local_to_global
            .iter()
            .map(|(local_id, global_id)| (*local_id, global_id.0))
            .collect();

        // 2) Edges
        if let Some(J::Array(edges)) = m.get("edges") {
            for e in edges {
                let e_obj = e
                    .as_object()
                    .ok_or_else(|| "seed edge must be an object".to_string())?;
                let src = resolve_seed_ref(e_obj.get("src"), &local_to_global, root_node, self)?;
                let tgt = resolve_seed_ref(e_obj.get("tgt"), &local_to_global, root_node, self)?;
                let et_str = e_obj
                    .get("type")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| "seed edge missing type".to_string())?;
                let et_sym = self.interner.intern(et_str);
                let attrs = decode_attrs_object(e_obj.get("attrs"), &mut self.interner);
                let _ = self.graph.insert_edge(src, et_sym, tgt, attrs);
                summary.edges += 1;
            }
        }

        // 3) Productions
        if let Some(J::Array(prods)) = m.get("productions") {
            for p in prods {
                let p_json = if !p.is_object()
                    || !p.as_object().unwrap().contains_key("productions")
                {
                    serde_json::json!({ "productions": [p] })
                } else {
                    p.clone()
                };
                if let Ok(parsed) = grammar_from_json(&p_json, &mut self.terms, &mut self.interner)
                {
                    for prod in parsed.productions {
                        self.add_production_no_mirror(prod);
                        summary.productions += 1;
                    }
                }
            }
        }

        // 4) Rules
        if let Some(J::Array(rules)) = m.get("rules") {
            let patchable_rule_names: std::collections::HashSet<&str> = m
                .get("self_modification_patchable_rules")
                .and_then(|value| value.as_array())
                .into_iter()
                .flatten()
                .filter_map(|value| value.as_str())
                .collect();
            let manifest_area = m.get("area").and_then(|v| v.as_str());
            let manifest_order = m.get("order").and_then(|v| v.as_u64());
            let manifest_latency = m.get("latency_class").and_then(|v| v.as_str());

            for r in rules {
                let mut scheduled = r.clone();
                if let Some(obj) = scheduled.as_object_mut() {
                    if !obj.contains_key("area") {
                        if let Some(area) = manifest_area {
                            obj.insert("area".into(), J::String(area.into()));
                        }
                    }
                    if !obj.contains_key("order") {
                        if let Some(order) = manifest_order {
                            obj.insert("order".into(), J::Number(order.into()));
                        }
                    }
                    if !obj.contains_key("latency_class") {
                        if let Some(latency) = manifest_latency {
                            obj.insert("latency_class".into(), J::String(latency.into()));
                        }
                    }
                }
                match parse_rule_json(&scheduled, &mut self.terms, &mut self.interner) {
                    Ok(mut rule) => {
                        let rule_name = r
                            .get("name")
                            .and_then(|value| value.as_str())
                            .unwrap_or("anonymous_rule");
                        rule.mutation_protected = !patchable_rule_names.contains(rule_name);
                        self.add_rule(rule);
                        summary.rules += 1;
                    }
                    Err(e) => {
                        let nm = r
                            .get("name")
                            .and_then(|n| n.as_str())
                            .unwrap_or("<unnamed>");
                        eprintln!("[seed] WARNING: skipping malformed rule '{}': {}", nm, e);
                        summary.rules_skipped.push(format!("{}: {}", nm, e));
                    }
                }
            }
        }

        // 5) Reflexes
        if let Some(J::Array(reflexes)) = m.get("reflexes") {
            for r in reflexes {
                match load_reflex_json(r, self, root_node) {
                    Ok(()) => summary.reflexes += 1,
                    Err(e) => {
                        let nm = r
                            .get("name")
                            .and_then(|n| n.as_str())
                            .unwrap_or("<unnamed>");
                        eprintln!("[seed] WARNING: skipping malformed reflex '{}': {}", nm, e);
                        summary.reflexes_skipped.push(format!("{}: {}", nm, e));
                    }
                }
            }
        }

        Ok(summary)
    }
}
