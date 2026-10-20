//! WebAssembly bindings for the OCELOT (G, Γ, C) cognitive substrate.
//!
//! Provides a browser-ready cognitive engine running client-side either
//! in a dedicated Web Worker or directly on the main thread.

use wasm_bindgen::prelude::*;
use serde_json::Value as JsonValue;
use rustc_hash::FxHashMap;
use std::sync::Arc;

use substrate_rs::graph::NodeID;
use substrate_rs::substrate::Substrate;
use substrate_rs::sym::Sym;
use substrate_rs::value::Value;

fn to_js<T: serde::Serialize + ?Sized>(val: &T) -> Result<JsValue, JsValue> {
    val.serialize(&serde_wasm_bindgen::Serializer::json_compatible())
        .map_err(|e| JsValue::from_str(&e.to_string()))
}

#[wasm_bindgen]
pub struct WasmSubstrate {
    inner: Substrate,
}

#[wasm_bindgen]
impl WasmSubstrate {
    /// Create a new, clean substrate with empty (G, Γ, C).
    #[wasm_bindgen(constructor)]
    pub fn new() -> WasmSubstrate {
        console_error_panic_hook::set_once();
        WasmSubstrate {
            inner: Substrate::empty(),
        }
    }

    /// Add a node of type `type_name` with optional JSON attributes object: `{"name": "agent", "health": 100}`.
    /// Returns the allocated NodeID integer.
    pub fn add_node(&mut self, type_name: &str, attrs_json: Option<String>) -> Result<u64, JsValue> {
        let type_sym = self.inner.interner.intern(type_name);
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        if let Some(json_str) = attrs_json {
            if !json_str.trim().is_empty() {
                let parsed: JsonValue = serde_json::from_str(&json_str)
                    .map_err(|e| JsValue::from_str(&format!("Invalid attrs JSON: {e}")))?;
                if let JsonValue::Object(map) = parsed {
                    for (k, v) in map {
                        let k_sym = self.inner.interner.intern(&k);
                        let val = substrate_rs::persist::decode_value(&v, &mut self.inner.interner);
                        attrs.insert(k_sym, val);
                    }
                }
            }
        }
        let nid = self.inner.add_node(type_sym, attrs);
        Ok(nid.0 as u64)
    }

    /// Add a directed edge `src -edge_type-> tgt` with optional JSON attributes.
    /// Fails with an error if C rejects the proposed edge according to the current grammar Γ.
    pub fn add_edge(
        &mut self,
        src: u64,
        edge_type: &str,
        tgt: u64,
        attrs_json: Option<String>,
    ) -> Result<(), JsValue> {
        let et_sym = self.inner.interner.intern(edge_type);
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        if let Some(json_str) = attrs_json {
            if !json_str.trim().is_empty() {
                let parsed: JsonValue = serde_json::from_str(&json_str)
                    .map_err(|e| JsValue::from_str(&format!("Invalid edge attrs JSON: {e}")))?;
                if let JsonValue::Object(map) = parsed {
                    for (k, v) in map {
                        let k_sym = self.inner.interner.intern(&k);
                        let val = substrate_rs::persist::decode_value(&v, &mut self.inner.interner);
                        attrs.insert(k_sym, val);
                    }
                }
            }
        }
        self.inner
            .add_edge(NodeID(src as u32), et_sym, NodeID(tgt as u32), attrs)
            .map_err(|e| JsValue::from_str(&format!("Inadmissible edge: {e:?}")))?;
        Ok(())
    }

    /// Delete a node and all its incident edges. Returns true if the node existed.
    pub fn delete_node(&mut self, node: u64) -> bool {
        self.inner.graph.delete_node(NodeID(node as u32)).is_some()
    }

    /// Delete an edge `src -edge_type-> tgt`. Returns true if the edge existed.
    pub fn delete_edge(&mut self, src: u64, edge_type: &str, tgt: u64) -> bool {
        let et_sym = self.inner.interner.intern(edge_type);
        if let Some(idx) = self.inner.graph.edge_idx(NodeID(src as u32), et_sym, NodeID(tgt as u32)) {
            self.inner.graph.delete_edge(idx).is_some()
        } else {
            false
        }
    }

    /// Add a graph rewrite rule from its JSON representation.
    /// Returns the local rule index integer.
    pub fn add_rule(&mut self, rule_json: &str) -> Result<u32, JsValue> {
        let parsed: JsonValue = serde_json::from_str(rule_json)
            .map_err(|e| JsValue::from_str(&format!("Invalid rule JSON: {e}")))?;
        let rule = substrate_rs::rule_json::parse_rule_json_pub(
            &parsed,
            &mut self.inner.terms,
            &mut self.inner.interner,
        )
        .map_err(|e| JsValue::from_str(&format!("Rule parse error: {e}")))?;
        let idx = self.inner.add_rule(rule);
        Ok(idx.0)
    }

    /// Load a seed manifest (`seeds/*.json`) into the substrate.
    /// Returns a summary object `{ nodes_added, edges_added, rules_added, reflexes_added }`.
    pub fn load_seed_manifest(
        &mut self,
        manifest_json: &str,
        root_node: Option<u64>,
    ) -> Result<JsValue, JsValue> {
        let parsed: JsonValue = serde_json::from_str(manifest_json)
            .map_err(|e| JsValue::from_str(&format!("Invalid manifest JSON: {e}")))?;
        let root = root_node.map(|id| NodeID(id as u32));
        let summary = self
            .inner
            .load_seed_manifest_value(&parsed, root)
            .map_err(|e| JsValue::from_str(&format!("Failed to load seed manifest: {e}")))?;
        to_js(&summary)
    }

    /// Step the cognitive rule-firing loop for up to `max_steps` iterations.
    /// Returns the number of iterations actually executed.
    pub fn tick(&mut self, max_steps: usize) -> usize {
        self.inner.run_rules(max_steps)
    }

    /// Run rules until fixed point or `max_steps` reached. Alias for `tick`.
    pub fn run_rules(&mut self, max_steps: usize) -> usize {
        self.inner.run_rules(max_steps)
    }

    /// Evaluate an IR Term JSON with optional environment variables JSON (e.g. `{"x": 10}`).
    /// Returns the evaluated Value converted to a JS value.
    pub fn evaluate(
        &mut self,
        term_json: &str,
        env_json: Option<String>,
    ) -> Result<JsValue, JsValue> {
        let term: JsonValue = serde_json::from_str(term_json)
            .map_err(|e| JsValue::from_str(&format!("Invalid term JSON: {e}")))?;
        let env_parsed: Option<JsonValue> = match env_json {
            Some(s) if !s.trim().is_empty() => Some(
                serde_json::from_str(&s)
                    .map_err(|e| JsValue::from_str(&format!("Invalid env JSON: {e}")))?,
            ),
            _ => None,
        };
        let res = self
            .inner
            .evaluate_json(&term, env_parsed.as_ref())
            .map_err(|e| JsValue::from_str(&format!("Evaluation error: {e}")))?;
        to_js(&res)
    }

    /// Serialize the entire typed graph to a JSON string matching python wire format.
    pub fn graph_to_json(&self) -> Result<String, JsValue> {
        let val = substrate_rs::persist::graph_to_value(&self.inner.graph, &self.inner.interner);
        serde_json::to_string(&val)
            .map_err(|e| JsValue::from_str(&format!("Graph serialization error: {e}")))
    }

    /// Snapshot the entire typed graph directly into a JavaScript Object.
    pub fn graph_snapshot(&self) -> Result<JsValue, JsValue> {
        let val = substrate_rs::persist::graph_to_value(&self.inner.graph, &self.inner.interner);
        to_js(&val)
    }

    /// Query node details: `{ type: string, attrs: Record<string, any> }` or null if not found.
    pub fn get_node(&self, node: u64) -> Result<JsValue, JsValue> {
        let nid = NodeID(node as u32);
        if self.inner.graph.has_node(nid) {
            let data = self.inner.graph.node(nid);
            let mut obj = serde_json::Map::new();
            obj.insert(
                "type".into(),
                JsonValue::String(self.inner.interner.resolve(data.type_).to_string()),
            );
            let mut attrs_map = serde_json::Map::new();
            for (&k, v) in &data.attrs {
                let key_str = self.inner.interner.resolve(k).to_string();
                let encoded = substrate_rs::persist::encode_value(v, &self.inner.interner);
                attrs_map.insert(key_str, encoded);
            }
            obj.insert("attrs".into(), JsonValue::Object(attrs_map));
            to_js(&JsonValue::Object(obj))
        } else {
            Ok(JsValue::NULL)
        }
    }

    /// Get current engine observability counters.
    pub fn counters(&self) -> Result<JsValue, JsValue> {
        let c = &self.inner.counters;
        let mut d = serde_json::Map::new();
        d.insert("nodes_inserted_total".into(), JsonValue::from(c.nodes_inserted_total));
        d.insert("edges_inserted_total".into(), JsonValue::from(c.edges_inserted_total));
        d.insert("admissibility_checks_total".into(), JsonValue::from(c.admissibility_checks_total));
        d.insert("rejections_type1".into(), JsonValue::from(c.rejections_type1));
        d.insert("rejections_type2".into(), JsonValue::from(c.rejections_type2));
        d.insert("evaluations_total".into(), JsonValue::from(c.evaluations_total));
        d.insert("cache_neighbours_hits".into(), JsonValue::from(c.cache_neighbours_hits));
        d.insert("cache_neighbours_misses".into(), JsonValue::from(c.cache_neighbours_misses));
        d.insert("cache_filter_hits".into(), JsonValue::from(c.cache_filter_hits));
        d.insert("cache_filter_misses".into(), JsonValue::from(c.cache_filter_misses));

        let mut by_type = serde_json::Map::new();
        for (&sym, &n) in &c.nodes_inserted_by_type {
            by_type.insert(self.inner.interner.resolve(sym).to_string(), JsonValue::from(n));
        }
        d.insert("nodes_inserted_by_type".into(), JsonValue::Object(by_type));

        let mut edge_by_type = serde_json::Map::new();
        for (&sym, &n) in &c.edges_inserted_by_type {
            edge_by_type.insert(self.inner.interner.resolve(sym).to_string(), JsonValue::from(n));
        }
        d.insert("edges_inserted_by_type".into(), JsonValue::Object(edge_by_type));

        to_js(&JsonValue::Object(d))
    }

    /// Reset engine observability counters.
    pub fn counters_clear(&mut self) {
        self.inner.counters.clear();
    }

    /// Register a JavaScript function as a named native tool callback.
    /// The JS function receives arguments array and returns a value.
    pub fn register_tool_handler(&self, tool_name: &str, callback: js_sys::Function) {
        struct SendJsFn(js_sys::Function);
        unsafe impl Send for SendJsFn {}
        unsafe impl Sync for SendJsFn {}

        let cb = Arc::new(SendJsFn(callback));
        let tool_fn: substrate_rs::tools::NativeToolFn = Arc::new(move |args, interner| {
            let js_args = js_sys::Array::new();
            for arg in args {
                let j = substrate_rs::persist::encode_value(arg, interner);
                if let Ok(js_val) = serde_wasm_bindgen::to_value(&j) {
                    js_args.push(&js_val);
                }
            }
            if let Ok(result) = cb.0.apply(&JsValue::NULL, &js_args) {
                if let Ok(json_res) = serde_wasm_bindgen::from_value::<JsonValue>(result) {
                    let mut dummy_interner = substrate_rs::sym::Interner::new();
                    return substrate_rs::persist::decode_value(&json_res, &mut dummy_interner);
                }
            }
            Value::Int(0)
        });
        substrate_rs::tools::register_native_tool(tool_name.to_string(), tool_fn);
    }

    /// Total number of live nodes in the graph.
    pub fn node_count(&self) -> usize {
        self.inner.graph.node_count()
    }

    /// Total number of live edges in the graph.
    pub fn edge_count(&self) -> usize {
        self.inner.graph.edge_count()
    }

    /// Total number of registered rewrite rules.
    pub fn rule_count(&self) -> usize {
        self.inner.rules.len()
    }
}
