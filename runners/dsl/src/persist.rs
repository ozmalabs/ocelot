//! Graph persistence — `substrate/persistence.py` port.
//!
//! Encoding format is the Python wire format unchanged: tagged dicts
//! for structural Values (`__nid__`, `__tuple__`, `__set__`, `__fset__`,
//! `__dict__`), scalars pass through verbatim. This means a graph
//! serialised by `substrate.persistence.graph_to_dict` loads here, and
//! vice versa — important for the substrate's "mind is durable JSON"
//! stance.
//!
//! NodeID preservation: the dump records each node's exact id; restore
//! reconstructs the slab so existing NodeID handles (held in the
//! agent's index dicts on the Python side) remain valid after a load.

use crate::graph::{NodeID, TypedGraph};
use crate::sym::Interner;
use crate::value::{cmp_value, SurfaceKind, Value};
use rustc_hash::FxHashMap;
use serde_json::{json, Map, Value as J};
use smallvec::SmallVec;
use std::sync::Arc;

/// Encode a substrate Value into the Python-compatible JSON form.
/// Strings are resolved through the interner so the dump is portable
/// across instances.
pub fn encode_value(v: &Value, interner: &Interner) -> J {
    match v {
        Value::None => J::Null,
        Value::Bool(b) => J::Bool(*b),
        Value::Int(n) => J::Number((*n).into()),
        Value::Float(f) => {
            serde_json::Number::from_f64(*f).map(J::Number).unwrap_or(J::Null)
        }
        // Exact rational — the PROGRAM value domain's in-frame numeric
        // type. Tagged like every other structural Value here
        // (`__nid__`, `__tuple__`, ...) rather than collapsed to a
        // float: this is the wire form `decode_value` below reverses,
        // and the shape `domains/prog_exact.py` / `SynthEnumerate`
        // literals emit so a fitted rational parameter round-trips
        // exactly instead of collapsing to float at render time.
        Value::Rational(n, d) => {
            let mut m = Map::new();
            m.insert("__rational__".into(), J::Array(vec![J::Number((*n).into()), J::Number((*d).into())]));
            J::Object(m)
        }
        Value::Str(s) => J::String(interner.resolve(*s).to_string()),
        Value::Node(nid) => {
            let mut m = Map::new();
            m.insert("__nid__".into(), J::Number(nid.0.into()));
            J::Object(m)
        }
        Value::Tuple(items) => {
            let mut m = Map::new();
            m.insert(
                "__tuple__".into(),
                J::Array(items.iter().map(|x| encode_value(x, interner)).collect()),
            );
            J::Object(m)
        }
        // ARC6 value layer: a `List` gets its OWN tag, symmetric with
        // `__tuple__` / `__set__` / `__fset__`, so a graph checkpoint
        // round-trips the Python-side container type. FORWARD-ONLY: an
        // engine that predates this tag decodes `{"__list__": [...]}` as
        // a string-keyed Dict. Recorded, not fixed.
        Value::List(items) => {
            let mut m = Map::new();
            m.insert(
                "__list__".into(),
                J::Array(items.iter().map(|x| encode_value(x, interner)).collect()),
            );
            J::Object(m)
        }
        Value::Set(items) => {
            let mut m = Map::new();
            m.insert(
                "__set__".into(),
                J::Array(items.iter().map(|x| encode_value(x, interner)).collect()),
            );
            J::Object(m)
        }
        Value::FrozenSet(items) => {
            let mut m = Map::new();
            m.insert(
                "__fset__".into(),
                J::Array(items.iter().map(|x| encode_value(x, interner)).collect()),
            );
            J::Object(m)
        }
        Value::Dict(pairs) => {
            // If all keys are Str, emit as a plain JSON object;
            // otherwise use the `__dict__` tagged form that preserves
            // non-string keys (matches Python's behaviour exactly).
            let all_string_keys = pairs.iter().all(|(k, _)| matches!(k, Value::Str(_)));
            if all_string_keys {
                let mut m = Map::new();
                for (k, v) in pairs.iter() {
                    if let Value::Str(s) = k {
                        m.insert(
                            interner.resolve(*s).to_string(),
                            encode_value(v, interner),
                        );
                    }
                }
                J::Object(m)
            } else {
                let mut m = Map::new();
                m.insert(
                    "__dict__".into(),
                    J::Array(
                        pairs
                            .iter()
                            .map(|(k, v)| {
                                J::Array(vec![encode_value(k, interner), encode_value(v, interner)])
                            })
                            .collect(),
                    ),
                );
                J::Object(m)
            }
        }
        Value::Surface(kind, bytes) => {
            // Surfaces aren't in the Python persistence's vocabulary
            // (they're a Rust-side runtime type for render output, not
            // a stored attribute shape). Round-trip via a custom tag
            // so they survive a save/load if any caller does manage to
            // park one in node attrs.
            let mut m = Map::new();
            m.insert("__surface__".into(), J::Null);
            m.insert(
                "kind".into(),
                J::String(match kind {
                    SurfaceKind::Text => "text".into(),
                    SurfaceKind::Bytes => "bytes".into(),
                }),
            );
            // Bytes encoded as base64-free hex string to keep the JSON
            // ASCII-safe without bringing in another dependency.
            let hex: String = bytes.iter().map(|b| format!("{:02x}", b)).collect();
            m.insert("payload".into(), J::String(hex));
            J::Object(m)
        }
    }
}

/// Inverse of `encode_value`. Interns strings on the way in.
pub fn decode_value(v: &J, interner: &mut Interner) -> Value {
    match v {
        J::Null => Value::None,
        J::Bool(b) => Value::Bool(*b),
        J::Number(n) => {
            if let Some(i) = n.as_i64() {
                Value::Int(i)
            } else if let Some(f) = n.as_f64() {
                Value::Float(f)
            } else {
                Value::Float(0.0)
            }
        }
        J::String(s) => Value::Str(interner.intern(s)),
        J::Array(items) => {
            // A bare JSON array decodes as a Tuple — matches the Python
            // `decode` fallthrough for plain lists. Tagged tuples /
            // sets come through Object below.
            let mut out: SmallVec<[Value; 4]> = SmallVec::new();
            for x in items {
                out.push(decode_value(x, interner));
            }
            Value::Tuple(Arc::new(out))
        }
        J::Object(m) => {
            if let Some(J::Number(n)) = m.get("__nid__") {
                if let Some(u) = n.as_u64() {
                    return Value::Node(NodeID(u as u32));
                }
            }
            if let Some(J::Array(items)) = m.get("__rational__") {
                if let [J::Number(n), J::Number(d)] = items.as_slice() {
                    if let (Some(n), Some(d)) = (n.as_i64(), d.as_i64()) {
                        // `make_rational` collapses an integral fraction
                        // to `Value::Int` and returns `None` on a zero
                        // denominator (malformed wire data) — degrade to
                        // Int(0) rather than panic on untrusted input.
                        return crate::value::make_rational(n, d).unwrap_or(Value::Int(0));
                    }
                }
            }
            if let Some(J::Array(items)) = m.get("__tuple__") {
                let mut out: SmallVec<[Value; 4]> = SmallVec::new();
                for x in items {
                    out.push(decode_value(x, interner));
                }
                return Value::Tuple(Arc::new(out));
            }
            if let Some(J::Array(items)) = m.get("__list__") {
                let mut out: SmallVec<[Value; 4]> = SmallVec::new();
                for x in items {
                    out.push(decode_value(x, interner));
                }
                return Value::List(Arc::new(out));
            }
            if let Some(J::Array(items)) = m.get("__set__") {
                let mut items_d: Vec<Value> =
                    items.iter().map(|x| decode_value(x, interner)).collect();
                items_d.sort_by(cmp_value);
                items_d.dedup_by(|a, b| cmp_value(a, b) == std::cmp::Ordering::Equal);
                return Value::Set(items_d.into());
            }
            if let Some(J::Array(items)) = m.get("__fset__") {
                let mut items_d: Vec<Value> =
                    items.iter().map(|x| decode_value(x, interner)).collect();
                items_d.sort_by(cmp_value);
                items_d.dedup_by(|a, b| cmp_value(a, b) == std::cmp::Ordering::Equal);
                return Value::FrozenSet(items_d.into());
            }
            if let Some(J::Array(pairs)) = m.get("__dict__") {
                let mut out: Vec<(Value, Value)> = Vec::new();
                for p in pairs {
                    if let J::Array(kv) = p {
                        if kv.len() == 2 {
                            out.push((
                                decode_value(&kv[0], interner),
                                decode_value(&kv[1], interner),
                            ));
                        }
                    }
                }
                return Value::Dict(out.into());
            }
            if m.contains_key("__surface__") {
                let kind = match m.get("kind").and_then(|k| k.as_str()) {
                    Some("bytes") => SurfaceKind::Bytes,
                    _ => SurfaceKind::Text,
                };
                let hex = m.get("payload").and_then(|p| p.as_str()).unwrap_or("");
                let bytes = (0..hex.len())
                    .step_by(2)
                    .filter_map(|i| u8::from_str_radix(&hex[i..i + 2], 16).ok())
                    .collect::<Vec<u8>>();
                return Value::Surface(kind, Arc::from(bytes));
            }
            // Bare object => string-keyed Dict.
            let mut out: Vec<(Value, Value)> = Vec::new();
            for (k, v) in m {
                let k_sym = interner.intern(k);
                out.push((Value::Str(k_sym), decode_value(v, interner)));
            }
            out.sort_by(|a, b| cmp_value(&a.0, &b.0));
            Value::Dict(out.into())
        }
    }
}

/// Serialise the whole graph. `next_id` matches the Python
/// `_next_id` semantic — the smallest unused NodeID after the dump
/// (here: the high-water mark of allocated slots).
pub fn graph_to_value(graph: &TypedGraph, interner: &Interner) -> J {
    let mut nodes = Vec::with_capacity(graph.node_count());
    for (nid, n) in graph.iter_nodes() {
        let mut attrs = Map::new();
        for (k, v) in &n.attrs {
            attrs.insert(interner.resolve(*k).to_string(), encode_value(v, interner));
        }
        nodes.push(json!({
            "id": nid.0,
            "type": interner.resolve(n.type_),
            "attrs": J::Object(attrs),
        }));
    }
    let mut edges = Vec::with_capacity(graph.edge_count());
    for (idx, e) in graph.iter_edges() {
        let mut attrs = Map::new();
        for (k, v) in graph.edge_attrs(idx) {
            attrs.insert(interner.resolve(*k).to_string(), encode_value(v, interner));
        }
        edges.push(json!({
            "src": e.src.0,
            "type": interner.resolve(e.edge_type),
            "tgt": e.tgt.0,
            "attrs": J::Object(attrs),
        }));
    }
    // next_id: largest allocated id + 1 (matches Python's monotonic
    // counter so reloads don't collide).
    let next_id = graph
        .iter_nodes()
        .map(|(nid, _)| nid.0 + 1)
        .max()
        .unwrap_or(0);
    json!({
        "next_id": next_id,
        "nodes": J::Array(nodes),
        "edges": J::Array(edges),
    })
}

/// Restore a graph from its serialised form. NodeIDs are preserved —
/// the same NodeID returned in the original lives in the rebuilt
/// graph, so external indexes keyed by NodeID survive a round-trip.
pub fn graph_from_value(v: &J, interner: &mut Interner) -> Result<TypedGraph, PersistError> {
    let mut g = TypedGraph::new();
    let obj = v.as_object().ok_or(PersistError::ShapeMismatch("expected object"))?;
    let nodes = obj
        .get("nodes")
        .and_then(|n| n.as_array())
        .ok_or(PersistError::ShapeMismatch("nodes"))?;
    for nd in nodes {
        let nid = nd
            .get("id")
            .and_then(|x| x.as_u64())
            .ok_or(PersistError::ShapeMismatch("node id"))? as u32;
        let type_str = nd
            .get("type")
            .and_then(|x| x.as_str())
            .ok_or(PersistError::ShapeMismatch("node type"))?;
        let mut attrs: FxHashMap<crate::sym::Sym, Value> = FxHashMap::default();
        if let Some(J::Object(amap)) = nd.get("attrs") {
            for (k, av) in amap {
                let k_sym = interner.intern(k);
                attrs.insert(k_sym, decode_value(av, interner));
            }
        }
        let type_sym = interner.intern(type_str);
        g.restore_node(NodeID(nid), type_sym, attrs);
    }
    let edges = obj
        .get("edges")
        .and_then(|e| e.as_array())
        .ok_or(PersistError::ShapeMismatch("edges"))?;
    for ed in edges {
        let src = ed
            .get("src")
            .and_then(|x| x.as_u64())
            .ok_or(PersistError::ShapeMismatch("edge src"))? as u32;
        let tgt = ed
            .get("tgt")
            .and_then(|x| x.as_u64())
            .ok_or(PersistError::ShapeMismatch("edge tgt"))? as u32;
        let type_str = ed
            .get("type")
            .and_then(|x| x.as_str())
            .ok_or(PersistError::ShapeMismatch("edge type"))?;
        let mut attrs: FxHashMap<crate::sym::Sym, Value> = FxHashMap::default();
        if let Some(J::Object(amap)) = ed.get("attrs") {
            for (k, av) in amap {
                let k_sym = interner.intern(k);
                attrs.insert(k_sym, decode_value(av, interner));
            }
        }
        let edge_type = interner.intern(type_str);
        g.restore_edge(NodeID(src), edge_type, NodeID(tgt), attrs);
    }
    Ok(g)
}

#[derive(Debug, Clone)]
pub enum PersistError {
    ShapeMismatch(&'static str),
}

/// Diff two `graph_to_value` dicts. Node identity is the node `id`
/// (graph_from_value preserves ids across a save/load, so a parent
/// snapshot and a dispatched child's final graph are id-aligned — this is
/// built for exactly that: diffing a parent agent's pre-dispatch snapshot
/// against a child's post-run graph). Edge identity is the structural
/// `(src, type, tgt)` triple — `TypedGraph::insert_edge` already enforces
/// that triple is unique (a second insert overwrites attrs on the same
/// edge, see `insert_edge`), so it's a sound key with no separate edge id
/// needed.
///
/// Pure JSON-level diff — deliberately does NOT decode `Value`s through an
/// `Interner` (no interner is available for two independently-serialised
/// dicts, and `serde_json::Value` already has structural `PartialEq`, so
/// there's nothing decoding would buy here).
///
/// Linear, not quadratic: nodes and edges are indexed into hash maps keyed
/// by identity ONE time each (`O(|a| + |b|)`), then every lookup below is
/// O(1) amortised — no nested scans. Built for parent-vs-child snapshots
/// in the 10^4-10^5 node/edge range.
///
/// Output shape (see `graph_diff` in the `PySubstrate` PyO3 surface for
/// the exact JSON returned to Python):
///   nodes_added:   [{id, type, attrs}]        — in b, not in a
///   nodes_removed: [id, ...]                  — in a, not in b
///   nodes_changed: [{id, attrs_before, attrs_after, ...}]
///                  — in both; attrs_before/attrs_after hold ONLY the
///                    attr keys that differ (added/removed/changed-value);
///                    a `type_before`/`type_after` pair is added too, but
///                    only on the rare node whose `type` itself changed.
///   edges_added:   [{src, type, tgt}]         — in b, not in a
///   edges_removed: [{src, type, tgt}]         — in a, not in b
///
/// All four list outputs are sorted (by id, or by (src, type, tgt)) for
/// deterministic output — the two source hash maps have no stable
/// iteration order on their own.
pub fn graph_diff(a: &J, b: &J) -> Result<J, PersistError> {
    fn get_array<'a>(v: &'a J, key: &'static str) -> Result<&'a Vec<J>, PersistError> {
        v.get(key)
            .and_then(|x| x.as_array())
            .ok_or(PersistError::ShapeMismatch(key))
    }
    fn empty_map() -> Map<String, J> {
        Map::new()
    }

    let nodes_a = get_array(a, "nodes")?;
    let nodes_b = get_array(b, "nodes")?;
    let edges_a = get_array(a, "edges")?;
    let edges_b = get_array(b, "edges")?;

    // --- nodes: index by id --------------------------------------------
    let mut idx_a: FxHashMap<u64, &Map<String, J>> = FxHashMap::default();
    idx_a.reserve(nodes_a.len());
    for n in nodes_a {
        let obj = n.as_object().ok_or(PersistError::ShapeMismatch("node: not an object"))?;
        let id = obj.get("id").and_then(|v| v.as_u64())
            .ok_or(PersistError::ShapeMismatch("node: missing/bad id"))?;
        idx_a.insert(id, obj);
    }
    let mut idx_b: FxHashMap<u64, &Map<String, J>> = FxHashMap::default();
    idx_b.reserve(nodes_b.len());
    for n in nodes_b {
        let obj = n.as_object().ok_or(PersistError::ShapeMismatch("node: not an object"))?;
        let id = obj.get("id").and_then(|v| v.as_u64())
            .ok_or(PersistError::ShapeMismatch("node: missing/bad id"))?;
        idx_b.insert(id, obj);
    }

    let empty = empty_map();
    let mut nodes_added: Vec<(u64, J)> = Vec::new();
    let mut nodes_changed: Vec<(u64, J)> = Vec::new();
    for (&id, &obj_b) in idx_b.iter() {
        match idx_a.get(&id) {
            None => {
                nodes_added.push((id, json!({
                    "id": id,
                    "type": obj_b.get("type").cloned().unwrap_or(J::Null),
                    "attrs": obj_b.get("attrs").cloned().unwrap_or_else(|| J::Object(empty_map())),
                })));
            }
            Some(&obj_a) => {
                let attrs_a = obj_a.get("attrs").and_then(|v| v.as_object()).unwrap_or(&empty);
                let attrs_b = obj_b.get("attrs").and_then(|v| v.as_object()).unwrap_or(&empty);
                let mut before = empty_map();
                let mut after = empty_map();
                for (k, vb) in attrs_b.iter() {
                    match attrs_a.get(k) {
                        Some(va) if va == vb => {}
                        Some(va) => {
                            before.insert(k.clone(), va.clone());
                            after.insert(k.clone(), vb.clone());
                        }
                        None => {
                            after.insert(k.clone(), vb.clone());
                        }
                    }
                }
                for (k, va) in attrs_a.iter() {
                    if !attrs_b.contains_key(k) {
                        before.insert(k.clone(), va.clone());
                    }
                }
                let type_a = obj_a.get("type").and_then(|v| v.as_str()).unwrap_or("");
                let type_b = obj_b.get("type").and_then(|v| v.as_str()).unwrap_or("");
                let type_changed = type_a != type_b;
                if !before.is_empty() || !after.is_empty() || type_changed {
                    let mut entry = empty_map();
                    entry.insert("id".into(), json!(id));
                    entry.insert("attrs_before".into(), J::Object(before));
                    entry.insert("attrs_after".into(), J::Object(after));
                    if type_changed {
                        entry.insert("type_before".into(), json!(type_a));
                        entry.insert("type_after".into(), json!(type_b));
                    }
                    nodes_changed.push((id, J::Object(entry)));
                }
            }
        }
    }
    let mut nodes_removed: Vec<u64> = idx_a.keys().copied().filter(|id| !idx_b.contains_key(id)).collect();
    nodes_removed.sort_unstable();
    nodes_added.sort_by_key(|(id, _)| *id);
    nodes_changed.sort_by_key(|(id, _)| *id);

    // --- edges: index by (src, type, tgt) -------------------------------
    fn edge_key(obj: &Map<String, J>) -> Result<(u64, String, u64), PersistError> {
        let src = obj.get("src").and_then(|v| v.as_u64())
            .ok_or(PersistError::ShapeMismatch("edge: missing/bad src"))?;
        let tgt = obj.get("tgt").and_then(|v| v.as_u64())
            .ok_or(PersistError::ShapeMismatch("edge: missing/bad tgt"))?;
        let ty = obj.get("type").and_then(|v| v.as_str())
            .ok_or(PersistError::ShapeMismatch("edge: missing/bad type"))?
            .to_string();
        Ok((src, ty, tgt))
    }

    let mut set_a: FxHashMap<(u64, String, u64), ()> = FxHashMap::default();
    set_a.reserve(edges_a.len());
    for e in edges_a {
        let obj = e.as_object().ok_or(PersistError::ShapeMismatch("edge: not an object"))?;
        set_a.insert(edge_key(obj)?, ());
    }
    let mut set_b: FxHashMap<(u64, String, u64), ()> = FxHashMap::default();
    set_b.reserve(edges_b.len());
    for e in edges_b {
        let obj = e.as_object().ok_or(PersistError::ShapeMismatch("edge: not an object"))?;
        set_b.insert(edge_key(obj)?, ());
    }

    let mut edges_added: Vec<(u64, String, u64)> =
        set_b.keys().filter(|k| !set_a.contains_key(*k)).cloned().collect();
    let mut edges_removed: Vec<(u64, String, u64)> =
        set_a.keys().filter(|k| !set_b.contains_key(*k)).cloned().collect();
    edges_added.sort();
    edges_removed.sort();

    let edge_json = |(src, ty, tgt): &(u64, String, u64)| json!({ "src": src, "type": ty, "tgt": tgt });

    Ok(json!({
        "nodes_added": nodes_added.into_iter().map(|(_, j)| j).collect::<Vec<J>>(),
        "nodes_removed": nodes_removed,
        "nodes_changed": nodes_changed.into_iter().map(|(_, j)| j).collect::<Vec<J>>(),
        "edges_added": edges_added.iter().map(edge_json).collect::<Vec<J>>(),
        "edges_removed": edges_removed.iter().map(edge_json).collect::<Vec<J>>(),
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn primitives_round_trip() {
        let mut i = Interner::new();
        for v in [
            Value::None,
            Value::Bool(true),
            Value::Int(42),
            Value::Float(std::f64::consts::PI),
            Value::Str(i.intern("hello")),
            Value::Node(NodeID(7)),
        ] {
            let j = encode_value(&v, &i);
            let back = decode_value(&j, &mut i);
            assert_eq!(back, v, "round-trip failed for {:?}", v);
        }
    }

    #[test]
    fn set_and_frozenset_distinct_after_round_trip() {
        let mut i = Interner::new();
        let s = Value::make_set(vec![Value::Int(1), Value::Int(2)]);
        let fs = Value::make_frozenset(vec![Value::Int(1), Value::Int(2)]);
        let s_j = encode_value(&s, &i);
        let fs_j = encode_value(&fs, &i);
        // tag carries the distinction even though == considers them equal
        let back_s = decode_value(&s_j, &mut i);
        let back_fs = decode_value(&fs_j, &mut i);
        assert!(matches!(back_s, Value::Set(_)));
        assert!(matches!(back_fs, Value::FrozenSet(_)));
    }

    #[test]
    fn tuple_round_trip() {
        let mut i = Interner::new();
        let t = Value::Tuple(Arc::new(SmallVec::from_vec(vec![
            Value::Int(1),
            Value::Str(i.intern("x")),
            Value::Node(NodeID(3)),
        ])));
        let j = encode_value(&t, &i);
        let back = decode_value(&j, &mut i);
        assert_eq!(back, t);
    }

    #[test]
    fn graph_round_trip_preserves_node_ids() {
        let mut i = Interner::new();
        let mut g = TypedGraph::new();
        let t = i.intern("Cell");
        let adj = i.intern("adjacent_to");
        let a = g.insert_node(t, FxHashMap::default());
        let b = g.insert_node(t, FxHashMap::default());
        let _c = g.insert_node(t, FxHashMap::default());
        // Delete one in the middle so the freelist has a gap.
        g.delete_node(b);
        let _d = g.insert_node(t, FxHashMap::default()); // recycles b's slot
        g.insert_edge(a, adj, NodeID(0), FxHashMap::default()).unwrap(); // self-edge
        let id_a_before = a;

        let dumped = graph_to_value(&g, &i);
        let restored = graph_from_value(&dumped, &mut i).unwrap();
        assert_eq!(restored.node_count(), g.node_count());
        assert_eq!(restored.edge_count(), g.edge_count());
        // NodeID a still resolves to a live node of the same type.
        assert!(restored.has_node(id_a_before));
        assert_eq!(restored.node(id_a_before).type_, t);
    }

    #[test]
    fn nodes_carry_attrs() {
        let mut i = Interner::new();
        let mut g = TypedGraph::new();
        let t = i.intern("Cell");
        let mut attrs: FxHashMap<crate::sym::Sym, Value> = FxHashMap::default();
        let key = i.intern("score");
        attrs.insert(key, Value::Float(2.5));
        let id = g.insert_node(t, attrs);
        let dumped = graph_to_value(&g, &i);
        let restored = graph_from_value(&dumped, &mut i).unwrap();
        let restored_score = restored.node(id).attrs.get(&key).cloned();
        assert_eq!(restored_score, Some(Value::Float(2.5)));
    }

    // --- graph_diff ------------------------------------------------------

    fn empty_diff_lists(d: &J) -> bool {
        for k in ["nodes_added", "nodes_removed", "nodes_changed", "edges_added", "edges_removed"] {
            let arr = d.get(k).and_then(|v| v.as_array()).unwrap_or_else(|| panic!("missing '{}'", k));
            if !arr.is_empty() {
                return false;
            }
        }
        true
    }

    #[test]
    fn graph_diff_identical_graphs_is_empty() {
        let mut i = Interner::new();
        let mut g = TypedGraph::new();
        let t = i.intern("Cell");
        let adj = i.intern("adjacent_to");
        let mut attrs: FxHashMap<crate::sym::Sym, Value> = FxHashMap::default();
        attrs.insert(i.intern("score"), Value::Float(1.0));
        let a = g.insert_node(t, attrs);
        let b = g.insert_node(t, FxHashMap::default());
        g.insert_edge(a, adj, b, FxHashMap::default()).unwrap();
        let dumped = graph_to_value(&g, &i);

        let d = graph_diff(&dumped, &dumped).expect("diff should succeed");
        assert!(empty_diff_lists(&d), "identical graphs should diff to empty: {:?}", d);
    }

    #[test]
    fn graph_diff_detects_added_node() {
        let mut i = Interner::new();
        let mut g_a = TypedGraph::new();
        let t = i.intern("Cell");
        let _a = g_a.insert_node(t, FxHashMap::default());
        let dumped_a = graph_to_value(&g_a, &i);

        let mut g_b = graph_from_value(&graph_to_value(&g_a, &i), &mut i).unwrap();
        let new_id = g_b.insert_node(t, FxHashMap::default());
        let dumped_b = graph_to_value(&g_b, &i);

        let d = graph_diff(&dumped_a, &dumped_b).unwrap();
        let added = d["nodes_added"].as_array().unwrap();
        assert_eq!(added.len(), 1, "{:?}", d);
        assert_eq!(added[0]["id"].as_u64().unwrap(), new_id.0 as u64);
        assert_eq!(added[0]["type"].as_str().unwrap(), "Cell");
        assert!(d["nodes_removed"].as_array().unwrap().is_empty());
        assert!(d["nodes_changed"].as_array().unwrap().is_empty());
    }

    #[test]
    fn graph_diff_detects_removed_node() {
        let mut i = Interner::new();
        let mut g_a = TypedGraph::new();
        let t = i.intern("Cell");
        let a = g_a.insert_node(t, FxHashMap::default());
        let doomed = g_a.insert_node(t, FxHashMap::default());
        let dumped_a = graph_to_value(&g_a, &i);

        let mut g_b = graph_from_value(&graph_to_value(&g_a, &i), &mut i).unwrap();
        g_b.delete_node(doomed);
        let dumped_b = graph_to_value(&g_b, &i);

        let d = graph_diff(&dumped_a, &dumped_b).unwrap();
        let removed = d["nodes_removed"].as_array().unwrap();
        assert_eq!(removed, &vec![J::from(doomed.0 as u64)], "{:?}", d);
        assert!(d["nodes_added"].as_array().unwrap().is_empty());
        // `a` untouched -> not in nodes_changed.
        assert!(!d["nodes_changed"].as_array().unwrap().iter()
            .any(|c| c["id"].as_u64() == Some(a.0 as u64)));
    }

    #[test]
    fn graph_diff_detects_changed_attrs_only_changed_keys() {
        let mut i = Interner::new();
        let mut g_a = TypedGraph::new();
        let t = i.intern("Cell");
        let k_score = i.intern("score");
        let k_stable = i.intern("stable_attr");
        let k_gone = i.intern("will_be_removed");
        let mut attrs_a: FxHashMap<crate::sym::Sym, Value> = FxHashMap::default();
        attrs_a.insert(k_score, Value::Float(1.0));
        attrs_a.insert(k_stable, Value::Int(9));
        attrs_a.insert(k_gone, Value::Bool(true));
        let id = g_a.insert_node(t, attrs_a);
        let dumped_a = graph_to_value(&g_a, &i);

        let mut g_b = graph_from_value(&graph_to_value(&g_a, &i), &mut i).unwrap();
        g_b.node_mut(id).attrs.insert(k_score, Value::Float(2.0)); // changed
        g_b.node_mut(id).attrs.remove(&k_gone); // removed
        // k_stable untouched; a brand-new key added too.
        let k_new = i.intern("new_attr");
        g_b.node_mut(id).attrs.insert(k_new, Value::Str(i.intern("hi")));
        let dumped_b = graph_to_value(&g_b, &i);

        let d = graph_diff(&dumped_a, &dumped_b).unwrap();
        let changed = d["nodes_changed"].as_array().unwrap();
        assert_eq!(changed.len(), 1, "{:?}", d);
        let entry = &changed[0];
        assert_eq!(entry["id"].as_u64().unwrap(), id.0 as u64);
        let before = entry["attrs_before"].as_object().unwrap();
        let after = entry["attrs_after"].as_object().unwrap();
        // Only the touched keys appear, never the untouched `stable_attr`.
        assert!(!before.contains_key("stable_attr"));
        assert!(!after.contains_key("stable_attr"));
        assert_eq!(before.get("score").and_then(|v| v.as_f64()), Some(1.0));
        assert_eq!(after.get("score").and_then(|v| v.as_f64()), Some(2.0));
        assert_eq!(before.get("will_be_removed").and_then(|v| v.as_bool()), Some(true));
        assert!(!after.contains_key("will_be_removed"));
        assert!(!before.contains_key("new_attr"));
        assert_eq!(after.get("new_attr").and_then(|v| v.as_str()), Some("hi"));
    }

    #[test]
    fn graph_diff_detects_edge_added_and_removed() {
        let mut i = Interner::new();
        let mut g_a = TypedGraph::new();
        let t = i.intern("Cell");
        let adj = i.intern("adjacent_to");
        let touches = i.intern("touches");
        let a = g_a.insert_node(t, FxHashMap::default());
        let b = g_a.insert_node(t, FxHashMap::default());
        g_a.insert_edge(a, adj, b, FxHashMap::default()).unwrap();
        let dumped_a = graph_to_value(&g_a, &i);

        let mut g_b = graph_from_value(&graph_to_value(&g_a, &i), &mut i).unwrap();
        // Remove the adjacent_to edge, add a new touches edge (same endpoints,
        // different type -> distinct identity, not a "changed" edge).
        let e = g_b.edge_idx(a, adj, b).unwrap();
        g_b.delete_edge(e);
        g_b.insert_edge(a, touches, b, FxHashMap::default()).unwrap();
        let dumped_b = graph_to_value(&g_b, &i);

        let d = graph_diff(&dumped_a, &dumped_b).unwrap();
        let added = d["edges_added"].as_array().unwrap();
        let removed = d["edges_removed"].as_array().unwrap();
        assert_eq!(added.len(), 1, "{:?}", d);
        assert_eq!(added[0]["type"].as_str().unwrap(), "touches");
        assert_eq!(added[0]["src"].as_u64().unwrap(), a.0 as u64);
        assert_eq!(added[0]["tgt"].as_u64().unwrap(), b.0 as u64);
        assert_eq!(removed.len(), 1, "{:?}", d);
        assert_eq!(removed[0]["type"].as_str().unwrap(), "adjacent_to");
    }

    #[test]
    fn graph_diff_bad_shape_errors_instead_of_panicking() {
        let bad = json!({"nodes": "not an array", "edges": []});
        let ok = json!({"nodes": [], "edges": []});
        assert!(graph_diff(&bad, &ok).is_err());
        assert!(graph_diff(&ok, &bad).is_err());
    }
}
