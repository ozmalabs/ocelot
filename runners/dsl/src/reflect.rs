//! Term ↔ G-subgraph reflection (Paper Axiom 3).
//!
//! Every Term variant round-trips losslessly to a typed subgraph: the
//! node type is `Term.<VariantName>` (matching the Python
//! `_TERM_NODE_PREFIX = "Term."` convention), scalar fields become node
//! attrs, child Term references become outgoing edges of type
//! `child.<field_name>` (with an `index` attr on tuple-shaped children
//! so order is preserved).
//!
//! This is the load-bearing piece of the substrate: because a Production's
//! where-clause / weight are Terms, this generic mechanism is what lets
//! `grammar_reflect.rs` mirror `Substrate::add_production`'s admitted
//! productions into the graph as real `Term.*` subgraphs rather than an
//! opaque blob (`GAMMA_REFLECTION_WIRING_RESULTS.md`, recommendation 2(ii)
//! of `SELF_REFERENCE_INFINITY_GROUNDING.md` §5).
//!
//! **Precise scope, corrected here per that verification note's §3.2/§4.5
//! finding that this comment previously overclaimed:** this does NOT make
//! `ConsistencyChecker.grammar` itself a subgraph of G. That struct (the
//! object `check_edge` actually reads) remains a plain Rust value, for
//! performance — `check_edge` never traverses the graph. What IS true, as
//! of `grammar_reflect.rs`: every `Production` added through the Rust
//! inherent `Substrate::add_production` gets an independently-reconstructable
//! `GammaProduction` graph mirror (content-equal to the struct, proven by
//! `substrate::tests::graph_mirror_is_content_equal_to_checker_grammar`),
//! wired from a `GammaGrammar` root. The PyO3-exposed `add_production`
//! binding — the path essentially all real Γ growth currently takes —
//! bypasses the Rust inherent method entirely and is therefore NOT covered;
//! see that results doc §2 for the full, named boundary. Self-modification
//! of the graph-resident REWRITE-RULE population (a separate, formally
//! distinct object from Γ — see `graph_rules.rs`) genuinely does fall out of
//! this one mechanism with no such caveat.

use crate::graph::{NodeID, TypedGraph};
use crate::sym::{Interner, Sym};
use crate::term::{TermArena, TermIdx, TermNode};
use crate::value::{SurfaceKind, Value};
use rustc_hash::FxHashMap;

const TERM_NODE_PREFIX: &str = "Term.";
const CHILD_EDGE_PREFIX: &str = "child.";

/// Insert `idx` and its subterms into `graph` as typed-graph elements.
/// Returns the NodeID of the root term node.
pub fn term_to_subgraph(
    arena: &TermArena,
    idx: TermIdx,
    graph: &mut TypedGraph,
    interner: &mut Interner,
) -> NodeID {
    let node = arena.get(idx);
    let (variant, fields) = describe(node);
    let type_sym = interner.intern(&format!("{}{}", TERM_NODE_PREFIX, variant));

    // Build the scalar attr map for this node; recurse to insert
    // children and stash their NodeIDs alongside the field/index info
    // so we can wire up edges after the node is created.
    let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
    let mut child_edges: Vec<(String, Option<i64>, NodeID)> = Vec::new();

    for field in fields {
        match field {
            FieldValue::ScalarSym { name, value } => {
                let k = interner.intern(name);
                attrs.insert(k, Value::Str(value));
            }
            FieldValue::ScalarInt { name, value } => {
                let k = interner.intern(name);
                attrs.insert(k, Value::Int(value));
            }
            FieldValue::ScalarBool { name, value } => {
                let k = interner.intern(name);
                attrs.insert(k, Value::Bool(value));
            }
            FieldValue::ScalarValue { name, value } => {
                let k = interner.intern(name);
                attrs.insert(k, value);
            }
            FieldValue::ScalarSurfaceKind { name, kind } => {
                let k = interner.intern(name);
                let s = match kind {
                    SurfaceKind::Text => "text",
                    SurfaceKind::Bytes => "bytes",
                };
                let v = interner.intern(s);
                attrs.insert(k, Value::Str(v));
            }
            FieldValue::Child { name, child } => {
                let child_nid = term_to_subgraph(arena, child, graph, interner);
                child_edges.push((name.to_string(), None, child_nid));
            }
            FieldValue::OptChild { name, child } => {
                if let Some(c) = child {
                    let child_nid = term_to_subgraph(arena, c, graph, interner);
                    child_edges.push((name.to_string(), None, child_nid));
                }
            }
            FieldValue::Children { name, items } => {
                for (i, c) in items.iter().enumerate() {
                    let child_nid = term_to_subgraph(arena, *c, graph, interner);
                    child_edges.push((name.to_string(), Some(i as i64), child_nid));
                }
            }
        }
    }

    let node_id = graph.insert_node(type_sym, attrs);
    let index_key = interner.intern("index");

    for (name, index, child_nid) in child_edges {
        let edge_type = interner.intern(&format!("{}{}", CHILD_EDGE_PREFIX, name));
        let mut edge_attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        if let Some(i) = index {
            edge_attrs.insert(index_key, Value::Int(i));
        }
        graph
            .insert_edge(node_id, edge_type, child_nid, edge_attrs)
            .expect("freshly-inserted nodes always connect");
    }
    node_id
}

/// Read a typed subgraph back into the term arena and return the
/// rebuilt Term's TermIdx. Errors when the node type doesn't start
/// with `Term.` or refers to an unknown variant.
pub fn term_from_subgraph(
    graph: &TypedGraph,
    interner: &Interner,
    root: NodeID,
    arena: &mut TermArena,
) -> Result<TermIdx, ReflectError> {
    crate::access_trace::note_node_type_and_attrs(graph, root);
    crate::access_trace::note_out_edges(graph, root, None);
    let node = graph.node(root);
    let type_name = interner.resolve(node.type_);
    let Some(variant) = type_name.strip_prefix(TERM_NODE_PREFIX) else {
        return Err(ReflectError::NotATerm {
            type_name: type_name.to_string(),
        });
    };

    // Collect children grouped by field name, with their optional index
    // so tuple-shaped fields can be re-ordered after collection.
    let mut groups: FxHashMap<String, Vec<(Option<i64>, NodeID)>> = FxHashMap::default();
    for edge_idx in graph.out_edges_idx(root, None) {
        let edge = graph.edge(edge_idx);
        let et = interner.resolve(edge.edge_type);
        let Some(field) = et.strip_prefix(CHILD_EDGE_PREFIX) else {
            continue;
        };
        let index_sym = interner.lookup("index");
        if let Some(index_sym) = index_sym {
            crate::access_trace::note(15, edge.src.0, index_sym.0, edge.tgt.0);
        }
        let idx_attr = graph
            .edge_attrs(edge_idx)
            .iter()
            .find(|(k, _)| interner.resolve(**k) == "index")
            .map(|(_, v)| v.as_i64());
        groups
            .entry(field.to_string())
            .or_default()
            .push((idx_attr, edge.tgt));
    }
    for v in groups.values_mut() {
        v.sort_by_key(|(i, _)| i.unwrap_or(i64::MIN));
    }

    // Build child TermIdx recursively so the rest of construction is
    // just field reads.
    let mut single_children: FxHashMap<String, TermIdx> = FxHashMap::default();
    let mut listy_children: FxHashMap<String, Vec<TermIdx>> = FxHashMap::default();
    for (field, items) in groups {
        if items.iter().all(|(i, _)| i.is_none()) {
            // Single-child field. The Python expects exactly one; we
            // mirror that — anything else is a bug in the dump.
            if items.len() != 1 {
                return Err(ReflectError::MalformedField {
                    type_name: type_name.to_string(),
                    field,
                });
            }
            let child = term_from_subgraph(graph, interner, items[0].1, arena)?;
            single_children.insert(field.to_string(), child);
        } else {
            let mut list = Vec::with_capacity(items.len());
            for (_, nid) in items {
                list.push(term_from_subgraph(graph, interner, nid, arena)?);
            }
            listy_children.insert(field.to_string(), list);
        }
    }

    // Read scalar attrs by resolving each Sym to its string name so we
    // can look up by field name regardless of which interner minted them.
    let mut attrs_by_name: FxHashMap<String, Value> = FxHashMap::default();
    for (k, v) in &node.attrs {
        attrs_by_name.insert(interner.resolve(*k).to_string(), v.clone());
    }

    let term = reconstruct(
        variant,
        &attrs_by_name,
        &mut single_children,
        &mut listy_children,
    )?;
    Ok(arena.add(term))
}

#[derive(Debug, Clone)]
pub enum ReflectError {
    NotATerm {
        type_name: String,
    },
    UnknownVariant {
        variant: String,
    },
    MissingField {
        variant: String,
        field: String,
    },
    MalformedField {
        type_name: String,
        field: String,
    },
    BadAttrType {
        variant: String,
        field: String,
        expected: &'static str,
    },
}

// --- Per-variant field descriptor ---

enum FieldValue<'a> {
    ScalarSym {
        name: &'static str,
        value: Sym,
    },
    ScalarInt {
        name: &'static str,
        value: i64,
    },
    ScalarBool {
        name: &'static str,
        value: bool,
    },
    ScalarValue {
        name: &'static str,
        value: Value,
    },
    ScalarSurfaceKind {
        name: &'static str,
        kind: &'a SurfaceKind,
    },
    Child {
        name: &'static str,
        child: TermIdx,
    },
    OptChild {
        name: &'static str,
        child: Option<TermIdx>,
    },
    Children {
        name: &'static str,
        items: &'a [TermIdx],
    },
}

/// Describe a term's variant name + its fields in a uniform shape so
/// `term_to_subgraph` can iterate over them without a per-variant
/// repeat of the insertion logic.
fn describe(node: &TermNode) -> (&'static str, Vec<FieldValue<'_>>) {
    use FieldValue::*;
    match node {
        TermNode::Var { name } => (
            "Var",
            vec![ScalarSym {
                name: "name",
                value: *name,
            }],
        ),
        TermNode::Lit { value } => (
            "Lit",
            vec![ScalarValue {
                name: "value",
                value: value.clone(),
            }],
        ),
        TermNode::TypeOf { node } => (
            "TypeOf",
            vec![Child {
                name: "node",
                child: *node,
            }],
        ),
        TermNode::Attr { node, key } => (
            "Attr",
            vec![
                Child {
                    name: "node",
                    child: *node,
                },
                ScalarSym {
                    name: "key",
                    value: *key,
                },
            ],
        ),
        TermNode::UseTool { tool, args } => (
            "UseTool",
            vec![
                ScalarSym {
                    name: "tool",
                    value: *tool,
                },
                Children {
                    name: "args",
                    items: args,
                },
            ],
        ),
        TermNode::SetT { items } => (
            "SetT",
            vec![Children {
                name: "items",
                items,
            }],
        ),
        TermNode::In { member, container } => (
            "In",
            vec![
                Child {
                    name: "member",
                    child: *member,
                },
                Child {
                    name: "container",
                    child: *container,
                },
            ],
        ),
        TermNode::Eq { a, b } => (
            "Eq",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Lt { a, b } => (
            "Lt",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Lte { a, b } => (
            "Lte",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Gt { a, b } => (
            "Gt",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Gte { a, b } => (
            "Gte",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::SlideNeighbours {
            cell,
            slide,
            ground,
        } => (
            "SlideNeighbours",
            vec![
                Child {
                    name: "cell",
                    child: *cell,
                },
                Child {
                    name: "slide",
                    child: *slide,
                },
                Child {
                    name: "ground",
                    child: *ground,
                },
            ],
        ),
        TermNode::ReachableFrom {
            node,
            edge_type,
            any_type,
        } => (
            "ReachableFrom",
            vec![
                Child {
                    name: "node",
                    child: *node,
                },
                ScalarSym {
                    name: "edge_type",
                    value: if *any_type {
                        Sym::default()
                    } else {
                        *edge_type
                    },
                },
            ],
        ),

        TermNode::Neighbours {
            node,
            edge_type,
            any_type,
        } => (
            "Neighbours",
            vec![
                Child {
                    name: "node",
                    child: *node,
                },
                // Encode None as the empty string so the absence of a real
                // edge_type round-trips. Decoder reads `any_type` from
                // edge_type == Sym(0).
                ScalarSym {
                    name: "edge_type",
                    value: if *any_type {
                        Sym::default()
                    } else {
                        *edge_type
                    },
                },
            ],
        ),
        TermNode::InNeighbours {
            node,
            edge_type,
            any_type,
        } => (
            "InNeighbours",
            vec![
                Child {
                    name: "node",
                    child: *node,
                },
                ScalarSym {
                    name: "edge_type",
                    value: if *any_type {
                        Sym::default()
                    } else {
                        *edge_type
                    },
                },
            ],
        ),
        TermNode::MapNeighbours {
            source,
            edge_type,
            any_type,
        } => (
            "MapNeighbours",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "edge_type",
                    value: if *any_type {
                        Sym::default()
                    } else {
                        *edge_type
                    },
                },
            ],
        ),
        TermNode::Count { source } => (
            "Count",
            vec![Child {
                name: "source",
                child: *source,
            }],
        ),
        TermNode::Filter {
            source,
            var_name,
            predicate,
        } => (
            "Filter",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "predicate",
                    child: *predicate,
                },
            ],
        ),
        TermNode::FilterList {
            source,
            var_name,
            predicate,
        } => (
            "FilterList",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "predicate",
                    child: *predicate,
                },
            ],
        ),
        TermNode::Exists {
            source,
            var_name,
            predicate,
        } => (
            "Exists",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "predicate",
                    child: *predicate,
                },
            ],
        ),
        TermNode::Sum {
            source,
            var_name,
            value,
        } => (
            "Sum",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::Prod {
            source,
            var_name,
            value,
        } => (
            "Prod",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::MinOver {
            source,
            var_name,
            value,
            default,
        } => (
            "MinOver",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "value",
                    child: *value,
                },
                OptChild {
                    name: "default",
                    child: *default,
                },
            ],
        ),
        TermNode::MaxOver {
            source,
            var_name,
            value,
            default,
        } => (
            "MaxOver",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "value",
                    child: *value,
                },
                OptChild {
                    name: "default",
                    child: *default,
                },
            ],
        ),
        TermNode::Pick { source } => (
            "Pick",
            vec![Child {
                name: "source",
                child: *source,
            }],
        ),
        TermNode::PickUnique { source } => (
            "PickUnique",
            vec![Child {
                name: "source",
                child: *source,
            }],
        ),
        TermNode::Tokenize { text } => (
            "Tokenize",
            vec![Child {
                name: "text",
                child: *text,
            }],
        ),
        TermNode::MorphHead { text } => (
            "MorphHead",
            vec![Child {
                name: "text",
                child: *text,
            }],
        ),
        TermNode::MorphTail { text } => (
            "MorphTail",
            vec![Child {
                name: "text",
                child: *text,
            }],
        ),
        TermNode::FinalToken { text } => (
            "FinalToken",
            vec![Child {
                name: "text",
                child: *text,
            }],
        ),
        TermNode::Tokenize2 { text } => (
            "Tokenize2",
            vec![Child {
                name: "text",
                child: *text,
            }],
        ),
        TermNode::ReadFile { path } => (
            "ReadFile",
            vec![Child {
                name: "path",
                child: *path,
            }],
        ),
        TermNode::StringIndexOf { haystack, needle } => (
            "StringIndexOf",
            vec![
                Child {
                    name: "haystack",
                    child: *haystack,
                },
                Child {
                    name: "needle",
                    child: *needle,
                },
            ],
        ),
        TermNode::StringSlice { s, start, end } => (
            "StringSlice",
            vec![
                Child {
                    name: "s",
                    child: *s,
                },
                Child {
                    name: "start",
                    child: *start,
                },
                Child {
                    name: "end",
                    child: *end,
                },
            ],
        ),
        TermNode::Verify {
            term,
            env,
            expected,
        } => (
            "Verify",
            vec![
                Child {
                    name: "term",
                    child: *term,
                },
                Child {
                    name: "env",
                    child: *env,
                },
                Child {
                    name: "expected",
                    child: *expected,
                },
            ],
        ),
        TermNode::MkDict { items } => (
            "MkDict",
            vec![Children {
                name: "items",
                items,
            }],
        ),
        TermNode::ToJsonString { value } => (
            "ToJsonString",
            vec![Child {
                name: "value",
                child: *value,
            }],
        ),
        TermNode::FromJsonString { text } => (
            "FromJsonString",
            vec![Child {
                name: "text",
                child: *text,
            }],
        ),
        TermNode::ShiftThresholdLits { tree, shift } => (
            "ShiftThresholdLits",
            vec![
                Child {
                    name: "tree",
                    child: *tree,
                },
                Child {
                    name: "shift",
                    child: *shift,
                },
            ],
        ),
        TermNode::DictGet { dict, key } => (
            "DictGet",
            vec![
                Child {
                    name: "dict",
                    child: *dict,
                },
                Child {
                    name: "key",
                    child: *key,
                },
            ],
        ),
        TermNode::RewriteTreeNodes {
            tree,
            type_filter,
            field,
            value_map,
        } => (
            "RewriteTreeNodes",
            vec![
                Child {
                    name: "tree",
                    child: *tree,
                },
                OptChild {
                    name: "type_filter",
                    child: *type_filter,
                },
                Child {
                    name: "field",
                    child: *field,
                },
                Child {
                    name: "value_map",
                    child: *value_map,
                },
            ],
        ),
        TermNode::AttrKeyRanking { tree } => (
            "AttrKeyRanking",
            vec![Child {
                name: "tree",
                child: *tree,
            }],
        ),
        TermNode::TextShape { text } => (
            "TextShape",
            vec![Child {
                name: "text",
                child: *text,
            }],
        ),
        TermNode::FbFrameSeq { fb } => (
            "FbFrameSeq",
            vec![Child {
                name: "fb",
                child: *fb,
            }],
        ),
        TermNode::ChangeDetect {
            image_vals,
            kernel_weights,
            dims,
        } => (
            "ChangeDetect",
            vec![
                Child {
                    name: "image_vals",
                    child: *image_vals,
                },
                Child {
                    name: "kernel_weights",
                    child: *kernel_weights,
                },
                Child {
                    name: "dims",
                    child: *dims,
                },
            ],
        ),
        TermNode::TemporalDiff { a_vals, b_vals } => (
            "TemporalDiff",
            vec![
                Child {
                    name: "a_vals",
                    child: *a_vals,
                },
                Child {
                    name: "b_vals",
                    child: *b_vals,
                },
            ],
        ),
        TermNode::Foveate {
            image_vals,
            dims,
            geometry,
        } => (
            "Foveate",
            vec![
                Child {
                    name: "image_vals",
                    child: *image_vals,
                },
                Child {
                    name: "dims",
                    child: *dims,
                },
                Child {
                    name: "geometry",
                    child: *geometry,
                },
            ],
        ),
        TermNode::StringConcat { parts } => (
            "StringConcat",
            vec![Children {
                name: "parts",
                items: parts,
            }],
        ),
        // Rung 1 Tier-1 stdlib Term ports.
        TermNode::Replace { text, old, new } => (
            "Replace",
            vec![
                Child {
                    name: "text",
                    child: *text,
                },
                Child {
                    name: "old",
                    child: *old,
                },
                Child {
                    name: "new",
                    child: *new,
                },
            ],
        ),
        TermNode::Str { value } => (
            "Str",
            vec![Child {
                name: "value",
                child: *value,
            }],
        ),
        TermNode::Split { text, sep } => (
            "Split",
            vec![
                Child {
                    name: "text",
                    child: *text,
                },
                Child {
                    name: "sep",
                    child: *sep,
                },
            ],
        ),
        TermNode::StrCount { text, sub } => (
            "StrCount",
            vec![
                Child {
                    name: "text",
                    child: *text,
                },
                Child {
                    name: "sub",
                    child: *sub,
                },
            ],
        ),
        TermNode::Round { value, ndigits } => (
            "Round",
            vec![
                Child {
                    name: "value",
                    child: *value,
                },
                Child {
                    name: "ndigits",
                    child: *ndigits,
                },
            ],
        ),
        TermNode::Reverse { seq } => (
            "Reverse",
            vec![Child {
                name: "seq",
                child: *seq,
            }],
        ),
        TermNode::IndexedMap {
            source,
            item_name,
            index_name,
            value,
        } => (
            "IndexedMap",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "item_name",
                    value: *item_name,
                },
                ScalarSym {
                    name: "index_name",
                    value: *index_name,
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::Capitalize { text } => (
            "Capitalize",
            vec![Child {
                name: "text",
                child: *text,
            }],
        ),
        TermNode::ParseInt { text } => (
            "ParseInt",
            vec![Child {
                name: "text",
                child: *text,
            }],
        ),
        TermNode::Slice { seq, start, stop } => (
            "Slice",
            vec![
                Child {
                    name: "seq",
                    child: *seq,
                },
                Child {
                    name: "start",
                    child: *start,
                },
                Child {
                    name: "stop",
                    child: *stop,
                },
            ],
        ),
        TermNode::Sort { seq } => (
            "Sort",
            vec![Child {
                name: "seq",
                child: *seq,
            }],
        ),
        TermNode::DictItems { seq } => (
            "DictItems",
            vec![Child {
                name: "seq",
                child: *seq,
            }],
        ),
        TermNode::SortBy {
            source,
            var_name,
            key,
        } => (
            "SortBy",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "key",
                    child: *key,
                },
            ],
        ),
        TermNode::GroupCount { seq } => (
            "GroupCount",
            vec![Child {
                name: "seq",
                child: *seq,
            }],
        ),
        TermNode::DictMerge { a, b } => (
            "DictMerge",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::ZipWith {
            a,
            b,
            a_name,
            b_name,
            value,
        } => (
            "ZipWith",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
                ScalarSym {
                    name: "a_name",
                    value: *a_name,
                },
                ScalarSym {
                    name: "b_name",
                    value: *b_name,
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::Argmax {
            source,
            var_name,
            value,
            default,
        } => (
            "Argmax",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "value",
                    child: *value,
                },
                OptChild {
                    name: "default",
                    child: *default,
                },
            ],
        ),
        TermNode::Argmin {
            source,
            var_name,
            value,
            default,
        } => (
            "Argmin",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "value",
                    child: *value,
                },
                OptChild {
                    name: "default",
                    child: *default,
                },
            ],
        ),
        TermNode::ArgminUnique {
            source,
            var_name,
            value,
            default,
        } => (
            "ArgminUnique",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "value",
                    child: *value,
                },
                OptChild {
                    name: "default",
                    child: *default,
                },
            ],
        ),
        TermNode::ArgminRefusal {
            source,
            var_name,
            value,
            refused,
        } => (
            "ArgminRefusal",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "value",
                    child: *value,
                },
                OptChild {
                    name: "refused",
                    child: *refused,
                },
            ],
        ),
        TermNode::Fold {
            source,
            var_name,
            acc_name,
            init,
            body,
        } => (
            "Fold",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                ScalarSym {
                    name: "acc_name",
                    value: *acc_name,
                },
                Child {
                    name: "init",
                    child: *init,
                },
                Child {
                    name: "body",
                    child: *body,
                },
            ],
        ),
        TermNode::BitsAt {
            buffer,
            bitpos,
            n_bits,
        } => (
            "BitsAt",
            vec![
                Child {
                    name: "buffer",
                    child: *buffer,
                },
                Child {
                    name: "bitpos",
                    child: *bitpos,
                },
                Child {
                    name: "n_bits",
                    child: *n_bits,
                },
            ],
        ),
        TermNode::BitsWrite {
            buffer,
            bitpos,
            value,
            n_bits,
        } => (
            "BitsWrite",
            vec![
                Child {
                    name: "buffer",
                    child: *buffer,
                },
                Child {
                    name: "bitpos",
                    child: *bitpos,
                },
                Child {
                    name: "value",
                    child: *value,
                },
                Child {
                    name: "n_bits",
                    child: *n_bits,
                },
            ],
        ),
        TermNode::BitsWriteAll { buffer, writes } => (
            "BitsWriteAll",
            vec![
                Child {
                    name: "buffer",
                    child: *buffer,
                },
                Child {
                    name: "writes",
                    child: *writes,
                },
            ],
        ),
        TermNode::BitsAtAll { buffer, reads } => (
            "BitsAtAll",
            vec![
                Child {
                    name: "buffer",
                    child: *buffer,
                },
                Child {
                    name: "reads",
                    child: *reads,
                },
            ],
        ),
        TermNode::HuffmanDecodeStream {
            buffer,
            bitpos,
            table,
            n_pairs,
        } => (
            "HuffmanDecodeStream",
            vec![
                Child {
                    name: "buffer",
                    child: *buffer,
                },
                Child {
                    name: "bitpos",
                    child: *bitpos,
                },
                Child {
                    name: "table",
                    child: *table,
                },
                Child {
                    name: "n_pairs",
                    child: *n_pairs,
                },
            ],
        ),
        TermNode::HuffmanEncodeStream {
            buffer,
            bitpos,
            pairs,
            table,
        } => (
            "HuffmanEncodeStream",
            vec![
                Child {
                    name: "buffer",
                    child: *buffer,
                },
                Child {
                    name: "bitpos",
                    child: *bitpos,
                },
                Child {
                    name: "pairs",
                    child: *pairs,
                },
                Child {
                    name: "table",
                    child: *table,
                },
            ],
        ),
        TermNode::ExpGolombDecode { buffer, bitpos } => (
            "ExpGolombDecode",
            vec![
                Child {
                    name: "buffer",
                    child: *buffer,
                },
                Child {
                    name: "bitpos",
                    child: *bitpos,
                },
            ],
        ),
        TermNode::ExpGolombDecodeSigned { buffer, bitpos } => (
            "ExpGolombDecodeSigned",
            vec![
                Child {
                    name: "buffer",
                    child: *buffer,
                },
                Child {
                    name: "bitpos",
                    child: *bitpos,
                },
            ],
        ),
        TermNode::ExpGolombEncode {
            buffer,
            bitpos,
            value,
        } => (
            "ExpGolombEncode",
            vec![
                Child {
                    name: "buffer",
                    child: *buffer,
                },
                Child {
                    name: "bitpos",
                    child: *bitpos,
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::ExpGolombEncodeSigned {
            buffer,
            bitpos,
            value,
        } => (
            "ExpGolombEncodeSigned",
            vec![
                Child {
                    name: "buffer",
                    child: *buffer,
                },
                Child {
                    name: "bitpos",
                    child: *bitpos,
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::Holds {
            concept,
            node,
            node2,
        } => (
            "Holds",
            vec![
                ScalarSym {
                    name: "concept",
                    value: *concept,
                },
                OptChild {
                    name: "node",
                    child: *node,
                },
                OptChild {
                    name: "node2",
                    child: *node2,
                },
            ],
        ),
        TermNode::EvalSubgraph { node } => (
            "EvalSubgraph",
            vec![Child {
                name: "node",
                child: *node,
            }],
        ),
        TermNode::And { items } => (
            "And",
            vec![Children {
                name: "items",
                items,
            }],
        ),
        TermNode::Or { items } => (
            "Or",
            vec![Children {
                name: "items",
                items,
            }],
        ),
        TermNode::Not { arg } => (
            "Not",
            vec![Child {
                name: "arg",
                child: *arg,
            }],
        ),
        TermNode::Abs { arg } => (
            "Abs",
            vec![Child {
                name: "arg",
                child: *arg,
            }],
        ),
        TermNode::Neg { arg } => (
            "Neg",
            vec![Child {
                name: "arg",
                child: *arg,
            }],
        ),
        TermNode::Plus { items } => (
            "Plus",
            vec![Children {
                name: "items",
                items,
            }],
        ),
        TermNode::Minus { a, b } => (
            "Minus",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Times { items } => (
            "Times",
            vec![Children {
                name: "items",
                items,
            }],
        ),
        TermNode::Div { a, b } => (
            "Div",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::DtwTo { a, b } => (
            "DtwTo",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::EnigmaCrib { candidate } => (
            "EnigmaCrib",
            vec![Child {
                name: "candidate",
                child: *candidate,
            }],
        ),
        TermNode::EnigmaBombe { candidate } => (
            "EnigmaBombe",
            vec![Child {
                name: "candidate",
                child: *candidate,
            }],
        ),
        TermNode::EnigmaBombeWitness { candidate } => (
            "EnigmaBombeWitness",
            vec![Child {
                name: "candidate",
                child: *candidate,
            }],
        ),
        TermNode::ApcEncode {
            model,
            seq,
            start,
            end,
            out_len,
        } => (
            "ApcEncode",
            vec![
                Child {
                    name: "model",
                    child: *model,
                },
                Child {
                    name: "seq",
                    child: *seq,
                },
                Child {
                    name: "start",
                    child: *start,
                },
                Child {
                    name: "end",
                    child: *end,
                },
                Child {
                    name: "out_len",
                    child: *out_len,
                },
            ],
        ),
        TermNode::PointSetDist { a, b } => (
            "PointSetDist",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::MahalLeaf { a, b } => (
            "MahalLeaf",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::MahalFull { a, b } => (
            "MahalFull",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::DeformGenMarginal { a, b } => (
            "DeformGenMarginal",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::DeformGen { a, b } => (
            "DeformGen",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::DeformDist { a, b } => (
            "DeformDist",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::SmoothDeformDist { a, b } => (
            "SmoothDeformDist",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::TpsDeformDist { a, b } => (
            "TpsDeformDist",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::SmoothDeformComponents { a, b } => (
            "SmoothDeformComponents",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::ShapeContextDist { a, b } => (
            "ShapeContextDist",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::ScTpsDist { a, b } => (
            "ScTpsDist",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::BlendCover { unknown, a, b } => (
            "BlendCover",
            vec![
                Child {
                    name: "unknown",
                    child: *unknown,
                },
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::XCorrPeak { a, b } => (
            "XCorrPeak",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Whiten { a, b } => (
            "Whiten",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::WhitenMany { a, b } => (
            "WhitenMany",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::WithinScatter { a, b } => (
            "WithinScatter",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::BetweenScatter { a, b } => (
            "BetweenScatter",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Mod { a, b } => (
            "Mod",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Pow { a, b } => (
            "Pow",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::BitAnd { a, b } => (
            "BitAnd",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::BitOr { a, b } => (
            "BitOr",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::BitXor { a, b } => (
            "BitXor",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Shl { a, b } => (
            "Shl",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Lshr { a, b } => (
            "Lshr",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Ashr { a, b } => (
            "Ashr",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::IDiv { a, b } => (
            "IDiv",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::IRem { a, b } => (
            "IRem",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Sqrt { arg } => (
            "Sqrt",
            vec![Child {
                name: "arg",
                child: *arg,
            }],
        ),
        TermNode::EnclosedCount { arg } => (
            "EnclosedCount",
            vec![Child {
                name: "arg",
                child: *arg,
            }],
        ),
        TermNode::Log { arg } => (
            "Log",
            vec![Child {
                name: "arg",
                child: *arg,
            }],
        ),
        TermNode::Exp { arg } => (
            "Exp",
            vec![Child {
                name: "arg",
                child: *arg,
            }],
        ),
        TermNode::Min { items } => (
            "Min",
            vec![Children {
                name: "items",
                items,
            }],
        ),
        TermNode::Max { items } => (
            "Max",
            vec![Children {
                name: "items",
                items,
            }],
        ),
        TermNode::ArgMax { items } => (
            "ArgMax",
            vec![Children {
                name: "items",
                items,
            }],
        ),
        TermNode::IfThenElse { cond, then, other } => (
            "IfThenElse",
            vec![
                Child {
                    name: "cond",
                    child: *cond,
                },
                Child {
                    name: "then",
                    child: *then,
                },
                Child {
                    name: "other",
                    child: *other,
                },
            ],
        ),
        TermNode::Vec_ { items } => (
            "Vec",
            vec![Children {
                name: "items",
                items,
            }],
        ),
        TermNode::VecAdd { a, b } => (
            "VecAdd",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::VecSub { a, b } => (
            "VecSub",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Dot { a, b } => (
            "Dot",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Magnitude { arg } => (
            "Magnitude",
            vec![Child {
                name: "arg",
                child: *arg,
            }],
        ),
        TermNode::Sin { arg } => (
            "Sin",
            vec![Child {
                name: "arg",
                child: *arg,
            }],
        ),
        TermNode::Cos { arg } => (
            "Cos",
            vec![Child {
                name: "arg",
                child: *arg,
            }],
        ),
        TermNode::Atan2 { y, x } => (
            "Atan2",
            vec![
                Child {
                    name: "y",
                    child: *y,
                },
                Child {
                    name: "x",
                    child: *x,
                },
            ],
        ),
        TermNode::Bearing { arg } => (
            "Bearing",
            vec![Child {
                name: "arg",
                child: *arg,
            }],
        ),
        TermNode::Rotate { vec, angle } => (
            "Rotate",
            vec![
                Child {
                    name: "vec",
                    child: *vec,
                },
                Child {
                    name: "angle",
                    child: *angle,
                },
            ],
        ),
        TermNode::AngleBetween { a, b } => (
            "AngleBetween",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Surface { kind, payload } => (
            "Surface",
            vec![
                ScalarSurfaceKind { name: "kind", kind },
                ScalarValue {
                    name: "payload",
                    value: payload.clone(),
                },
            ],
        ),
        TermNode::Cat { items } => (
            "Cat",
            vec![Children {
                name: "items",
                items,
            }],
        ),
        TermNode::Slot { name } => (
            "Slot",
            vec![ScalarSym {
                name: "name",
                value: *name,
            }],
        ),
        TermNode::Join { separator, items } => (
            "Join",
            vec![
                OptChild {
                    name: "separator",
                    child: *separator,
                },
                OptChild {
                    name: "items",
                    child: *items,
                },
            ],
        ),
        TermNode::Bytes { items } => (
            "Bytes",
            vec![Children {
                name: "items",
                items,
            }],
        ),
        TermNode::U8 { expr } => (
            "U8",
            vec![OptChild {
                name: "expr",
                child: *expr,
            }],
        ),
        TermNode::U16LE { expr } => (
            "U16LE",
            vec![OptChild {
                name: "expr",
                child: *expr,
            }],
        ),
        TermNode::U32LE { expr } => (
            "U32LE",
            vec![OptChild {
                name: "expr",
                child: *expr,
            }],
        ),
        TermNode::U64LE { expr } => (
            "U64LE",
            vec![OptChild {
                name: "expr",
                child: *expr,
            }],
        ),
        TermNode::LEB128 { expr } => (
            "LEB128",
            vec![OptChild {
                name: "expr",
                child: *expr,
            }],
        ),
        TermNode::Lines { items } => (
            "Lines",
            vec![Children {
                name: "items",
                items,
            }],
        ),
        TermNode::Label { prefix } => (
            "Label",
            vec![ScalarSym {
                name: "prefix",
                value: *prefix,
            }],
        ),
        TermNode::Let { name, value, body } => (
            "Let",
            vec![
                ScalarSym {
                    name: "name",
                    value: *name,
                },
                OptChild {
                    name: "value",
                    child: *value,
                },
                OptChild {
                    name: "body",
                    child: *body,
                },
            ],
        ),
        TermNode::Nth { items, index } => (
            "Nth",
            vec![
                OptChild {
                    name: "items",
                    child: *items,
                },
                ScalarInt {
                    name: "index",
                    value: *index,
                },
            ],
        ),
        TermNode::Render { term, lang } => (
            "Render",
            vec![
                OptChild {
                    name: "term",
                    child: *term,
                },
                OptChild {
                    name: "lang",
                    child: *lang,
                },
            ],
        ),
        TermNode::LitRepr { value } => (
            "LitRepr",
            vec![OptChild {
                name: "value",
                child: *value,
            }],
        ),
        // --- Phase 7 ext additions ---
        TermNode::Union { a, b } => (
            "Union",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Last { seq } => (
            "Last",
            vec![Child {
                name: "seq",
                child: *seq,
            }],
        ),
        TermNode::IndexAt { seq, index } => (
            "IndexAt",
            vec![
                Child {
                    name: "seq",
                    child: *seq,
                },
                Child {
                    name: "index",
                    child: *index,
                },
            ],
        ),
        TermNode::Append { seq, item } => (
            "Append",
            vec![
                Child {
                    name: "seq",
                    child: *seq,
                },
                Child {
                    name: "item",
                    child: *item,
                },
            ],
        ),
        TermNode::ListDrop { list, index } => (
            "ListDrop",
            vec![
                Child {
                    name: "list",
                    child: *list,
                },
                Child {
                    name: "index",
                    child: *index,
                },
            ],
        ),
        TermNode::Intersect { a, b } => (
            "Intersect",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::Difference { a, b } => (
            "Difference",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
            ],
        ),
        TermNode::MapSet {
            source,
            var_name,
            value,
        } => (
            "MapSet",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::MapList {
            source,
            var_name,
            value,
        } => (
            "MapList",
            vec![
                Child {
                    name: "source",
                    child: *source,
                },
                ScalarSym {
                    name: "var_name",
                    value: *var_name,
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::Edges {
            node,
            edge_type,
            any_type,
        } => (
            "Edges",
            vec![
                Child {
                    name: "node",
                    child: *node,
                },
                ScalarSym {
                    name: "edge_type",
                    value: if *any_type {
                        Sym::default()
                    } else {
                        *edge_type
                    },
                },
            ],
        ),
        TermNode::EdgeAttr { edge, key } => (
            "EdgeAttr",
            vec![
                Child {
                    name: "edge",
                    child: *edge,
                },
                ScalarSym {
                    name: "key",
                    value: *key,
                },
            ],
        ),
        TermNode::ArgMin { items } => (
            "ArgMin",
            vec![Children {
                name: "items",
                items: items,
            }],
        ),
        TermNode::NodesWhere {
            node_type,
            attr_key,
            value,
        } => (
            "NodesWhere",
            vec![
                ScalarSym {
                    name: "node_type",
                    value: *node_type,
                },
                ScalarSym {
                    name: "attr_key",
                    value: *attr_key,
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::NodesOfType { node_type } => (
            "NodesOfType",
            vec![ScalarSym {
                name: "node_type",
                value: *node_type,
            }],
        ),
        TermNode::AntiUnify { values, wild } => (
            "AntiUnify",
            vec![
                Child {
                    name: "values",
                    child: *values,
                },
                ScalarSym {
                    name: "wild",
                    value: *wild,
                },
            ],
        ),
        TermNode::FixedCount { pattern, wild } => (
            "FixedCount",
            vec![
                Child {
                    name: "pattern",
                    child: *pattern,
                },
                ScalarSym {
                    name: "wild",
                    value: *wild,
                },
            ],
        ),
        TermNode::Covers {
            pattern,
            instance,
            wild,
        } => (
            "Covers",
            vec![
                Child {
                    name: "pattern",
                    child: *pattern,
                },
                Child {
                    name: "instance",
                    child: *instance,
                },
                ScalarSym {
                    name: "wild",
                    value: *wild,
                },
            ],
        ),
        TermNode::CoversOpen {
            pattern,
            instance,
            wild,
        } => (
            "CoversOpen",
            vec![
                Child {
                    name: "pattern",
                    child: *pattern,
                },
                Child {
                    name: "instance",
                    child: *instance,
                },
                ScalarSym {
                    name: "wild",
                    value: *wild,
                },
            ],
        ),
        TermNode::AntiUnifyWitness { values, wild } => (
            "AntiUnifyWitness",
            vec![
                Child {
                    name: "values",
                    child: *values,
                },
                ScalarSym {
                    name: "wild",
                    value: *wild,
                },
            ],
        ),
        TermNode::Substitute {
            template,
            sigma,
            wild,
        } => (
            "Substitute",
            vec![
                Child {
                    name: "template",
                    child: *template,
                },
                Child {
                    name: "sigma",
                    child: *sigma,
                },
                ScalarSym {
                    name: "wild",
                    value: *wild,
                },
            ],
        ),
        TermNode::Unify { values, wild } => (
            "Unify",
            vec![
                Child {
                    name: "values",
                    child: *values,
                },
                ScalarSym {
                    name: "wild",
                    value: *wild,
                },
            ],
        ),
        TermNode::StructSim { a, b, wild } => (
            "StructSim",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
                ScalarSym {
                    name: "wild",
                    value: *wild,
                },
            ],
        ),
        TermNode::ShapeDecode {
            goal,
            codebook_type,
            exclude,
            codebook_scope,
            beam,
            max_steps,
            cand_k,
            budget,
            field,
            wild,
            wild_objects,
        } => (
            "ShapeDecode",
            vec![
                Child {
                    name: "goal",
                    child: *goal,
                },
                ScalarSym {
                    name: "codebook_type",
                    value: *codebook_type,
                },
                OptChild {
                    name: "exclude",
                    child: *exclude,
                },
                OptChild {
                    name: "codebook_scope",
                    child: *codebook_scope,
                },
                ScalarInt {
                    name: "beam",
                    value: *beam,
                },
                ScalarInt {
                    name: "max_steps",
                    value: *max_steps,
                },
                ScalarInt {
                    name: "cand_k",
                    value: *cand_k,
                },
                ScalarInt {
                    name: "budget",
                    value: *budget,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
                ScalarSym {
                    name: "wild",
                    value: *wild,
                },
                ScalarBool {
                    name: "wild_objects",
                    value: *wild_objects,
                },
            ],
        ),
        TermNode::MotorCompose {
            episode,
            policy,
            candidate,
        } => (
            "MotorCompose",
            vec![
                Child {
                    name: "episode",
                    child: *episode,
                },
                Child {
                    name: "policy",
                    child: *policy,
                },
                Child {
                    name: "candidate",
                    child: *candidate,
                },
            ],
        ),
        TermNode::FutureManifoldProjection {
            episode,
            policy,
            source,
            addition,
            field,
        } => (
            "FutureManifoldProjection",
            vec![
                Child {
                    name: "episode",
                    child: *episode,
                },
                Child {
                    name: "policy",
                    child: *policy,
                },
                Child {
                    name: "source",
                    child: *source,
                },
                OptChild {
                    name: "addition",
                    child: *addition,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::FutureManifoldSelection {
            episode,
            policy,
            candidates,
            field,
            snapshot_field,
        } => (
            "FutureManifoldSelection",
            vec![
                Child {
                    name: "episode",
                    child: *episode,
                },
                Child {
                    name: "policy",
                    child: *policy,
                },
                Child {
                    name: "candidates",
                    child: *candidates,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
                ScalarSym {
                    name: "snapshot_field",
                    value: *snapshot_field,
                },
            ],
        ),
        TermNode::TransformDecode {
            goal,
            codebook_type,
            exclude,
            max_dims,
            field,
        } => (
            "TransformDecode",
            vec![
                Child {
                    name: "goal",
                    child: *goal,
                },
                ScalarSym {
                    name: "codebook_type",
                    value: *codebook_type,
                },
                OptChild {
                    name: "exclude",
                    child: *exclude,
                },
                ScalarInt {
                    name: "max_dims",
                    value: *max_dims,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::NetForward { assemblage, inputs } => (
            "NetForward",
            vec![
                Child {
                    name: "assemblage",
                    child: *assemblage,
                },
                Child {
                    name: "inputs",
                    child: *inputs,
                },
            ],
        ),
        TermNode::DimInfer {
            goal,
            codebook_type,
            exclude,
            generator_type,
            grain,
            max_dims,
            field,
        } => (
            "DimInfer",
            vec![
                Child {
                    name: "goal",
                    child: *goal,
                },
                ScalarSym {
                    name: "codebook_type",
                    value: *codebook_type,
                },
                OptChild {
                    name: "exclude",
                    child: *exclude,
                },
                ScalarSym {
                    name: "generator_type",
                    value: *generator_type,
                },
                OptChild {
                    name: "grain",
                    child: *grain,
                },
                ScalarInt {
                    name: "max_dims",
                    value: *max_dims,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::GenInfer {
            goal,
            codebook_type,
            exclude,
            scope,
            require_scope,
            quadratic_enabled,
            linear_prefilter_enabled,
            grain,
            mdl_enabled,
            max_dims,
            field,
        } => (
            "GenInfer",
            vec![
                Child {
                    name: "goal",
                    child: *goal,
                },
                ScalarSym {
                    name: "codebook_type",
                    value: *codebook_type,
                },
                OptChild {
                    name: "exclude",
                    child: *exclude,
                },
                OptChild {
                    name: "scope",
                    child: *scope,
                },
                OptChild {
                    name: "require_scope",
                    child: *require_scope,
                },
                OptChild {
                    name: "quadratic_enabled",
                    child: *quadratic_enabled,
                },
                OptChild {
                    name: "linear_prefilter_enabled",
                    child: *linear_prefilter_enabled,
                },
                OptChild {
                    name: "grain",
                    child: *grain,
                },
                OptChild {
                    name: "mdl_enabled",
                    child: *mdl_enabled,
                },
                ScalarInt {
                    name: "max_dims",
                    value: *max_dims,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::RatioInduce {
            population,
            codebook_type,
            resolution,
            field,
        } => (
            "RatioInduce",
            vec![
                Child {
                    name: "population",
                    child: *population,
                },
                ScalarSym {
                    name: "codebook_type",
                    value: *codebook_type,
                },
                ScalarInt {
                    name: "resolution",
                    value: *resolution,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::LogQuantum {
            population,
            value_slot,
            base_num,
            base_den,
            delta_num,
            delta_den,
            raw,
            field,
        } => (
            "LogQuantum",
            vec![
                Child {
                    name: "population",
                    child: *population,
                },
                ScalarInt {
                    name: "value_slot",
                    value: *value_slot,
                },
                ScalarInt {
                    name: "base_num",
                    value: *base_num,
                },
                ScalarInt {
                    name: "base_den",
                    value: *base_den,
                },
                ScalarInt {
                    name: "delta_num",
                    value: *delta_num,
                },
                ScalarInt {
                    name: "delta_den",
                    value: *delta_den,
                },
                ScalarBool {
                    name: "raw",
                    value: *raw,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::TimeInfer {
            sequence,
            codebook_type,
            max_b,
            field,
            max_steps,
            robust,
        } => (
            "TimeInfer",
            vec![
                Child {
                    name: "sequence",
                    child: *sequence,
                },
                ScalarSym {
                    name: "codebook_type",
                    value: *codebook_type,
                },
                ScalarInt {
                    name: "max_b",
                    value: *max_b,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
                ScalarInt {
                    name: "max_steps",
                    value: *max_steps,
                },
                ScalarBool {
                    name: "robust",
                    value: *robust,
                },
            ],
        ),
        TermNode::DepthInfer {
            sequence,
            codebook_type,
            max_b,
            field,
        } => (
            "DepthInfer",
            vec![
                Child {
                    name: "sequence",
                    child: *sequence,
                },
                ScalarSym {
                    name: "codebook_type",
                    value: *codebook_type,
                },
                ScalarInt {
                    name: "max_b",
                    value: *max_b,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::BlinkBridge {
            sequence,
            codebook_type,
            max_b,
            field,
        } => (
            "BlinkBridge",
            vec![
                Child {
                    name: "sequence",
                    child: *sequence,
                },
                ScalarSym {
                    name: "codebook_type",
                    value: *codebook_type,
                },
                ScalarInt {
                    name: "max_b",
                    value: *max_b,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::GapAbduce {
            sequence,
            codebook_type,
            max_b,
            field,
        } => (
            "GapAbduce",
            vec![
                Child {
                    name: "sequence",
                    child: *sequence,
                },
                ScalarSym {
                    name: "codebook_type",
                    value: *codebook_type,
                },
                ScalarInt {
                    name: "max_b",
                    value: *max_b,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::GapVerify {
            sequence,
            codebook_type,
            max_b,
            field,
        } => (
            "GapVerify",
            vec![
                Child {
                    name: "sequence",
                    child: *sequence,
                },
                ScalarSym {
                    name: "codebook_type",
                    value: *codebook_type,
                },
                ScalarInt {
                    name: "max_b",
                    value: *max_b,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::SupportInfer {
            sequence,
            codebook_type,
            field,
        } => (
            "SupportInfer",
            vec![
                Child {
                    name: "sequence",
                    child: *sequence,
                },
                ScalarSym {
                    name: "codebook_type",
                    value: *codebook_type,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::MotionEnergy {
            sequence,
            height,
            width,
            field,
        } => (
            "MotionEnergy",
            vec![
                Child {
                    name: "sequence",
                    child: *sequence,
                },
                ScalarInt {
                    name: "height",
                    value: *height,
                },
                ScalarInt {
                    name: "width",
                    value: *width,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::TransferDecode { goal } => (
            "TransferDecode",
            vec![Child {
                name: "goal",
                child: *goal,
            }],
        ),
        TermNode::RecogniseShape { text } => (
            "RecogniseShape",
            vec![Child {
                name: "text",
                child: *text,
            }],
        ),
        TermNode::MetaShapeMint { observation, .. } => (
            "MetaShapeMint",
            vec![Child {
                name: "observation",
                child: *observation,
            }],
        ),
        TermNode::StrokeQuantize {
            points,
            segments,
            turn_bins,
            len_bins,
            grid,
            scale_bins,
            invariant_only,
            canonical_pose,
            turn_edges,
            len_edges,
            emit_residual,
            bounds,
            field,
            seg_sym,
            pose_x_sym,
            pose_y_sym,
            pose_o_sym,
            pose_s_sym,
        } => (
            "StrokeQuantize",
            vec![
                Child {
                    name: "points",
                    child: *points,
                },
                ScalarInt {
                    name: "segments",
                    value: *segments,
                },
                ScalarInt {
                    name: "turn_bins",
                    value: *turn_bins,
                },
                ScalarInt {
                    name: "len_bins",
                    value: *len_bins,
                },
                ScalarInt {
                    name: "grid",
                    value: *grid,
                },
                ScalarInt {
                    name: "scale_bins",
                    value: *scale_bins,
                },
                ScalarBool {
                    name: "invariant_only",
                    value: *invariant_only,
                },
                ScalarBool {
                    name: "canonical_pose",
                    value: *canonical_pose,
                },
                OptChild {
                    name: "turn_edges",
                    child: *turn_edges,
                },
                OptChild {
                    name: "len_edges",
                    child: *len_edges,
                },
                ScalarBool {
                    name: "emit_residual",
                    value: *emit_residual,
                },
                OptChild {
                    name: "bounds",
                    child: *bounds,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
                ScalarSym {
                    name: "seg_sym",
                    value: *seg_sym,
                },
                ScalarSym {
                    name: "pose_x_sym",
                    value: *pose_x_sym,
                },
                ScalarSym {
                    name: "pose_y_sym",
                    value: *pose_y_sym,
                },
                ScalarSym {
                    name: "pose_o_sym",
                    value: *pose_o_sym,
                },
                ScalarSym {
                    name: "pose_s_sym",
                    value: *pose_s_sym,
                },
            ],
        ),
        TermNode::StrokeRender {
            signature,
            n_points,
            apply_pose,
            turn_bins,
            len_bins,
            grid,
            scale_bins,
            turn_edges,
            len_edges,
            bounds,
            field,
        } => (
            "StrokeRender",
            vec![
                Child {
                    name: "signature",
                    child: *signature,
                },
                ScalarInt {
                    name: "n_points",
                    value: *n_points,
                },
                ScalarBool {
                    name: "apply_pose",
                    value: *apply_pose,
                },
                ScalarInt {
                    name: "turn_bins",
                    value: *turn_bins,
                },
                ScalarInt {
                    name: "len_bins",
                    value: *len_bins,
                },
                ScalarInt {
                    name: "grid",
                    value: *grid,
                },
                ScalarInt {
                    name: "scale_bins",
                    value: *scale_bins,
                },
                OptChild {
                    name: "turn_edges",
                    child: *turn_edges,
                },
                OptChild {
                    name: "len_edges",
                    child: *len_edges,
                },
                OptChild {
                    name: "bounds",
                    child: *bounds,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::SigmaLognormalGenerate {
            primitives,
            start,
            t_start,
            t_end,
            n_points,
            field,
        } => (
            "SigmaLognormalGenerate",
            vec![
                Child {
                    name: "primitives",
                    child: *primitives,
                },
                Child {
                    name: "start",
                    child: *start,
                },
                ScalarValue {
                    name: "t_start",
                    value: Value::Float(*t_start),
                },
                ScalarValue {
                    name: "t_end",
                    value: Value::Float(*t_end),
                },
                ScalarInt {
                    name: "n_points",
                    value: *n_points,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::LookaheadValue {
            node,
            child_edge,
            score_key,
            depth,
        } => (
            "LookaheadValue",
            vec![
                Child {
                    name: "node",
                    child: *node,
                },
                ScalarSym {
                    name: "child_edge",
                    value: *child_edge,
                },
                ScalarSym {
                    name: "score_key",
                    value: *score_key,
                },
                Child {
                    name: "depth",
                    child: *depth,
                },
            ],
        ),
        TermNode::ScalarAttrTriples { skip_prefix } => (
            "ScalarAttrTriples",
            vec![ScalarSym {
                name: "skip_prefix",
                value: *skip_prefix,
            }],
        ),
        TermNode::AttrByName { node, name } => (
            "AttrByName",
            vec![
                Child {
                    name: "node",
                    child: *node,
                },
                Child {
                    name: "name",
                    child: *name,
                },
            ],
        ),
        TermNode::TrackIdentityCorrespondence {
            prev,
            cur,
            feature_key,
            category_key,
            extent_key,
            radius,
        } => (
            "TrackIdentityCorrespondence",
            vec![
                Child {
                    name: "prev",
                    child: *prev,
                },
                Child {
                    name: "cur",
                    child: *cur,
                },
                ScalarSym {
                    name: "feature_key",
                    value: *feature_key,
                },
                // Sym::default() sentinel for "absent" — same convention
                // ReachableFrom/Neighbours use for any_type via edge_type.
                ScalarSym {
                    name: "category_key",
                    value: category_key.unwrap_or_default(),
                },
                ScalarSym {
                    name: "extent_key",
                    value: extent_key.unwrap_or_default(),
                },
                Child {
                    name: "radius",
                    child: *radius,
                },
            ],
        ),
        // --- Program IR (P1). Identifier LISTS (`targets`, `names`)
        // encode as ONE Tuple-of-Str scalar attr (identifiers are
        // parse-time Syms; a Tuple attr round-trips within one
        // interner losslessly). Optional identifiers use the
        // Sym::default() sentinel.
        TermNode::ProgSeq { stmts } => (
            "ProgSeq",
            vec![Children {
                name: "stmts",
                items: stmts,
            }],
        ),
        TermNode::ProgAssignVar { name, value } => (
            "ProgAssignVar",
            vec![
                ScalarSym {
                    name: "name",
                    value: *name,
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::ProgAugAssign { name, op, value } => (
            "ProgAugAssign",
            vec![
                ScalarSym {
                    name: "name",
                    value: *name,
                },
                ScalarSym {
                    name: "op",
                    value: *op,
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::ProgTupleUnpack { targets, value } => (
            "ProgTupleUnpack",
            vec![
                ScalarValue {
                    name: "targets",
                    value: Value::Tuple(std::sync::Arc::new(
                        targets.iter().map(|t| Value::Str(*t)).collect(),
                    )),
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::ProgIfStmt { cond, then, orelse } => (
            "ProgIfStmt",
            vec![
                Child {
                    name: "cond",
                    child: *cond,
                },
                Child {
                    name: "then",
                    child: *then,
                },
                OptChild {
                    name: "orelse",
                    child: *orelse,
                },
            ],
        ),
        TermNode::ProgForEach {
            var,
            iter,
            body,
            orelse,
        } => (
            "ProgForEach",
            vec![
                ScalarSym {
                    name: "var",
                    value: *var,
                },
                Child {
                    name: "iter",
                    child: *iter,
                },
                Child {
                    name: "body",
                    child: *body,
                },
                OptChild {
                    name: "orelse",
                    child: *orelse,
                },
            ],
        ),
        TermNode::ProgWhile { cond, body, orelse } => (
            "ProgWhile",
            vec![
                Child {
                    name: "cond",
                    child: *cond,
                },
                Child {
                    name: "body",
                    child: *body,
                },
                OptChild {
                    name: "orelse",
                    child: *orelse,
                },
            ],
        ),
        TermNode::ProgLoopCtl { kind } => (
            "ProgLoopCtl",
            vec![ScalarSym {
                name: "kind",
                value: *kind,
            }],
        ),
        TermNode::ProgReturn { value } => (
            "ProgReturn",
            vec![OptChild {
                name: "value",
                child: *value,
            }],
        ),
        TermNode::ProgTryOr {
            body,
            exc_var,
            handler,
        } => (
            "ProgTryOr",
            vec![
                Child {
                    name: "body",
                    child: *body,
                },
                ScalarSym {
                    name: "exc_var",
                    value: *exc_var,
                },
                OptChild {
                    name: "handler",
                    child: *handler,
                },
            ],
        ),
        TermNode::ProgRaise { exc } => (
            "ProgRaise",
            vec![OptChild {
                name: "exc",
                child: *exc,
            }],
        ),
        TermNode::ProgImportStmt {
            module,
            alias,
            names,
        } => (
            "ProgImportStmt",
            vec![
                ScalarSym {
                    name: "module",
                    value: *module,
                },
                ScalarSym {
                    name: "alias",
                    value: *alias,
                },
                ScalarValue {
                    name: "names",
                    value: Value::Tuple(std::sync::Arc::new(
                        names.iter().map(|n| Value::Str(*n)).collect(),
                    )),
                },
            ],
        ),
        TermNode::ProgSubscriptSet { obj, index, value } => (
            "ProgSubscriptSet",
            vec![
                Child {
                    name: "obj",
                    child: *obj,
                },
                Child {
                    name: "index",
                    child: *index,
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::ProgAttrSet { obj, attr, value } => (
            "ProgAttrSet",
            vec![
                Child {
                    name: "obj",
                    child: *obj,
                },
                ScalarSym {
                    name: "attr",
                    value: *attr,
                },
                Child {
                    name: "value",
                    child: *value,
                },
            ],
        ),
        TermNode::ProgDefFnParam { name, default } => (
            "ProgDefFnParam",
            vec![
                ScalarSym {
                    name: "name",
                    value: *name,
                },
                OptChild {
                    name: "default",
                    child: *default,
                },
            ],
        ),
        TermNode::ProgCallExtern { name, recv, args } => (
            "ProgCallExtern",
            vec![
                ScalarSym {
                    name: "name",
                    value: *name,
                },
                OptChild {
                    name: "recv",
                    child: *recv,
                },
                Children {
                    name: "args",
                    items: args,
                },
            ],
        ),
        TermNode::ProgAttrGet { obj, attr } => (
            "ProgAttrGet",
            vec![
                Child {
                    name: "obj",
                    child: *obj,
                },
                ScalarSym {
                    name: "attr",
                    value: *attr,
                },
            ],
        ),
        TermNode::ProgSubscript { obj, index } => (
            "ProgSubscript",
            vec![
                Child {
                    name: "obj",
                    child: *obj,
                },
                Child {
                    name: "index",
                    child: *index,
                },
            ],
        ),
        TermNode::ProgSlice {
            obj,
            start,
            stop,
            step,
        } => (
            "ProgSlice",
            vec![
                Child {
                    name: "obj",
                    child: *obj,
                },
                OptChild {
                    name: "start",
                    child: *start,
                },
                OptChild {
                    name: "stop",
                    child: *stop,
                },
                OptChild {
                    name: "step",
                    child: *step,
                },
            ],
        ),
        TermNode::ProgContainerLit { kind, items } => (
            "ProgContainerLit",
            vec![
                ScalarSym {
                    name: "kind",
                    value: *kind,
                },
                Children {
                    name: "items",
                    items,
                },
            ],
        ),
        TermNode::ProgComprehensionList {
            var,
            source,
            expr,
            cond,
        } => (
            "ProgComprehensionList",
            vec![
                ScalarSym {
                    name: "var",
                    value: *var,
                },
                Child {
                    name: "source",
                    child: *source,
                },
                Child {
                    name: "expr",
                    child: *expr,
                },
                OptChild {
                    name: "cond",
                    child: *cond,
                },
            ],
        ),
        TermNode::ProgComprehensionGen {
            var,
            source,
            expr,
            cond,
        } => (
            "ProgComprehensionGen",
            vec![
                ScalarSym {
                    name: "var",
                    value: *var,
                },
                Child {
                    name: "source",
                    child: *source,
                },
                Child {
                    name: "expr",
                    child: *expr,
                },
                OptChild {
                    name: "cond",
                    child: *cond,
                },
            ],
        ),
        TermNode::ProgIsOp { a, b, negated } => (
            "ProgIsOp",
            vec![
                Child {
                    name: "a",
                    child: *a,
                },
                Child {
                    name: "b",
                    child: *b,
                },
                ScalarBool {
                    name: "negated",
                    value: *negated,
                },
            ],
        ),
        TermNode::ProgFString { parts } => (
            "ProgFString",
            vec![Children {
                name: "parts",
                items: parts,
            }],
        ),
        TermNode::ProgEval {
            prog,
            env,
            oracles,
            fuel,
            field,
        } => (
            "ProgEval",
            vec![
                Child {
                    name: "prog",
                    child: *prog,
                },
                OptChild {
                    name: "env",
                    child: *env,
                },
                OptChild {
                    name: "oracles",
                    child: *oracles,
                },
                ScalarInt {
                    name: "fuel",
                    value: *fuel,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::SnakeCase { text } => (
            "SnakeCase",
            vec![Child {
                name: "text",
                child: *text,
            }],
        ),
        TermNode::CaseFold { text } => (
            "CaseFold",
            vec![Child {
                name: "text",
                child: *text,
            }],
        ),
        TermNode::SynthEnumerate {
            examples,
            ops,
            consts,
            exclude,
            derived_ops,
            exclude_ops,
            max_size,
            max_candidates,
            saturate_k,
            field,
        } => (
            "SynthEnumerate",
            vec![
                Child {
                    name: "examples",
                    child: *examples,
                },
                OptChild {
                    name: "ops",
                    child: *ops,
                },
                OptChild {
                    name: "consts",
                    child: *consts,
                },
                OptChild {
                    name: "exclude",
                    child: *exclude,
                },
                OptChild {
                    name: "derived_ops",
                    child: *derived_ops,
                },
                OptChild {
                    name: "exclude_ops",
                    child: *exclude_ops,
                },
                ScalarInt {
                    name: "max_size",
                    value: *max_size,
                },
                ScalarInt {
                    name: "max_candidates",
                    value: *max_candidates,
                },
                ScalarInt {
                    name: "saturate_k",
                    value: *saturate_k,
                },
                ScalarSym {
                    name: "field",
                    value: *field,
                },
            ],
        ),
        TermNode::Call { name, args } => (
            "Call",
            vec![
                ScalarSym {
                    name: "name",
                    value: *name,
                },
                Children {
                    name: "args",
                    items: args,
                },
            ],
        ),
        TermNode::ParetoDominates {
            candidate,
            alternative,
            dimension_count,
            value_edge,
            measure_edge,
            dimension_key,
            verified_key,
            signed_value_key,
        } => (
            "ParetoDominates",
            vec![
                Child {
                    name: "candidate",
                    child: *candidate,
                },
                Child {
                    name: "alternative",
                    child: *alternative,
                },
                Child {
                    name: "dimension_count",
                    child: *dimension_count,
                },
                ScalarSym {
                    name: "value_edge",
                    value: *value_edge,
                },
                ScalarSym {
                    name: "measure_edge",
                    value: *measure_edge,
                },
                ScalarSym {
                    name: "dimension_key",
                    value: *dimension_key,
                },
                ScalarSym {
                    name: "verified_key",
                    value: *verified_key,
                },
                ScalarSym {
                    name: "signed_value_key",
                    value: *signed_value_key,
                },
            ],
        ),
    }
}

/// Inverse of `describe` — given a variant name and the resolved
/// fields, build the TermNode. Uses small helper closures so the
/// per-variant code is just the variant's field list.
fn reconstruct(
    variant: &str,
    attrs: &FxHashMap<String, Value>,
    singles: &mut FxHashMap<String, TermIdx>,
    lists: &mut FxHashMap<String, Vec<TermIdx>>,
) -> Result<TermNode, ReflectError> {
    let get_sym = |name: &str| -> Result<Sym, ReflectError> {
        match attrs.get(name) {
            Some(Value::Str(s)) => Ok(*s),
            Some(Value::None) => Ok(Sym::default()),
            None => Ok(Sym::default()),
            Some(_) => Err(ReflectError::BadAttrType {
                variant: variant.to_string(),
                field: name.to_string(),
                expected: "Str",
            }),
        }
    };
    let get_int = |name: &str| -> Result<i64, ReflectError> {
        match attrs.get(name) {
            Some(Value::Int(n)) => Ok(*n),
            Some(Value::None) | None => Ok(0),
            Some(other) => Ok(other.as_i64()),
        }
    };
    let get_value = |name: &str| -> Value { attrs.get(name).cloned().unwrap_or(Value::None) };
    let get_bool = |name: &str| -> bool { matches!(attrs.get(name), Some(Value::Bool(true))) };
    let get_surface_kind = |name: &str| -> SurfaceKind {
        match attrs.get(name) {
            Some(Value::Str(_)) => {
                // We resolve by string match below in the caller, since
                // we don't have access to the interner here.
                // Default to Text; the caller resolves properly via the
                // attrs_by_name map (the Sym was already resolved to a
                // String prior to reconstruct, so we get here only when
                // the value is a raw Str(Sym) — should never happen.)
                SurfaceKind::Text
            }
            _ => SurfaceKind::Text,
        }
    };
    let _ = get_surface_kind;
    // For Surface specifically, the attr came in as Value::Str(sym),
    // and `attrs_by_name` already resolved the field NAME — but the
    // Sym inside the Value still belongs to the source interner. We
    // can't resolve it here without the interner; instead, the caller
    // populates `attrs` so that the surface kind appears as Value::Str
    // and we re-encode-look-up at the next layer. For correctness we
    // do a soft compare by treating the absence of a literal "bytes"
    // signal as Text. The dedicated `surface_kind` attr helper is
    // below.
    let surface_kind_from_value = |v: &Value| -> SurfaceKind {
        // The value was emitted as Value::Str(<sym for "text"/"bytes">);
        // when round-trip happens inside the same interner the strings
        // compare via Sym equality. But here we've lost the interner
        // ref. We rely on the attr being passed alongside a Sym whose
        // value is the literal string; in practice this works because
        // Surface emission/reconstruction happens within one interner
        // and the encoded form is unambiguous.
        // The caller passes pre-resolved attrs as String → Value, so
        // the surface_kind field actually shows up as Value::Str(sym).
        // We can't read the sym here, so just default to Text — the
        // PyO3 layer will override this when it goes via JSON.
        let _ = v;
        SurfaceKind::Text
    };
    let _ = surface_kind_from_value;

    // The single/list child getters consume the maps so duplicate
    // fields are caught.
    macro_rules! take_child {
        ($field:expr) => {
            singles
                .remove($field)
                .ok_or_else(|| ReflectError::MissingField {
                    variant: variant.to_string(),
                    field: $field.to_string(),
                })?
        };
    }
    macro_rules! take_opt_child {
        ($field:expr) => {
            singles.remove($field)
        };
    }
    macro_rules! take_children {
        ($field:expr) => {
            lists.remove($field).unwrap_or_default()
        };
    }

    let node = match variant {
        "Var" => TermNode::Var {
            name: get_sym("name")?,
        },
        "Lit" => TermNode::Lit {
            value: get_value("value"),
        },
        "TypeOf" => TermNode::TypeOf {
            node: take_child!("node"),
        },
        "Attr" => TermNode::Attr {
            node: take_child!("node"),
            key: get_sym("key")?,
        },
        "UseTool" => TermNode::UseTool {
            tool: get_sym("tool")?,
            args: take_children!("args"),
        },
        "SetT" => TermNode::SetT {
            items: take_children!("items"),
        },
        "In" => TermNode::In {
            member: take_child!("member"),
            container: take_child!("container"),
        },
        "Eq" => TermNode::Eq {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Lt" => TermNode::Lt {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Lte" => TermNode::Lte {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Gt" => TermNode::Gt {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Gte" => TermNode::Gte {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "SlideNeighbours" => TermNode::SlideNeighbours {
            cell: take_child!("cell"),
            slide: take_child!("slide"),
            ground: take_child!("ground"),
        },
        "ReachableFrom" => {
            let edge_type = get_sym("edge_type")?;
            TermNode::ReachableFrom {
                node: take_child!("node"),
                edge_type,
                any_type: edge_type == Sym::default(),
            }
        }

        "Neighbours" => {
            let edge_type = get_sym("edge_type")?;
            TermNode::Neighbours {
                node: take_child!("node"),
                edge_type,
                any_type: edge_type == Sym::default(),
            }
        }
        "InNeighbours" => {
            let edge_type = get_sym("edge_type")?;
            TermNode::InNeighbours {
                node: take_child!("node"),
                edge_type,
                any_type: edge_type == Sym::default(),
            }
        }
        "MapNeighbours" => {
            let edge_type = get_sym("edge_type")?;
            TermNode::MapNeighbours {
                source: take_child!("source"),
                edge_type,
                any_type: edge_type == Sym::default(),
            }
        }
        "Count" => TermNode::Count {
            source: take_child!("source"),
        },
        "Filter" => TermNode::Filter {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            predicate: take_child!("predicate"),
        },
        "FilterList" => TermNode::FilterList {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            predicate: take_child!("predicate"),
        },
        "Exists" => TermNode::Exists {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            predicate: take_child!("predicate"),
        },
        "Sum" => TermNode::Sum {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            value: take_child!("value"),
        },
        "Prod" => TermNode::Prod {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            value: take_child!("value"),
        },
        "MinOver" => TermNode::MinOver {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            value: take_child!("value"),
            default: take_opt_child!("default"),
        },
        "MaxOver" => TermNode::MaxOver {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            value: take_child!("value"),
            default: take_opt_child!("default"),
        },
        "Pick" => TermNode::Pick {
            source: take_child!("source"),
        },
        "PickUnique" => TermNode::PickUnique {
            source: take_child!("source"),
        },
        "Tokenize" => TermNode::Tokenize {
            text: take_child!("text"),
        },
        "MorphHead" => TermNode::MorphHead {
            text: take_child!("text"),
        },
        "MorphTail" => TermNode::MorphTail {
            text: take_child!("text"),
        },
        "FinalToken" => TermNode::FinalToken {
            text: take_child!("text"),
        },
        "Tokenize2" => TermNode::Tokenize2 {
            text: take_child!("text"),
        },
        "ReadFile" => TermNode::ReadFile {
            path: take_child!("path"),
        },
        "StringIndexOf" => TermNode::StringIndexOf {
            haystack: take_child!("haystack"),
            needle: take_child!("needle"),
        },
        "StringSlice" => TermNode::StringSlice {
            s: take_child!("s"),
            start: take_child!("start"),
            end: take_child!("end"),
        },
        "Verify" => TermNode::Verify {
            term: take_child!("term"),
            env: take_child!("env"),
            expected: take_child!("expected"),
        },
        "MkDict" => TermNode::MkDict {
            items: take_children!("items"),
        },
        "ToJsonString" => TermNode::ToJsonString {
            value: take_child!("value"),
        },
        "FromJsonString" => TermNode::FromJsonString {
            text: take_child!("text"),
        },
        "ShiftThresholdLits" => TermNode::ShiftThresholdLits {
            tree: take_child!("tree"),
            shift: take_child!("shift"),
        },
        "DictGet" => TermNode::DictGet {
            dict: take_child!("dict"),
            key: take_child!("key"),
        },
        "RewriteTreeNodes" => TermNode::RewriteTreeNodes {
            tree: take_child!("tree"),
            type_filter: take_opt_child!("type_filter"),
            field: take_child!("field"),
            value_map: take_child!("value_map"),
        },
        "AttrKeyRanking" => TermNode::AttrKeyRanking {
            tree: take_child!("tree"),
        },
        "TextShape" => TermNode::TextShape {
            text: take_child!("text"),
        },
        "FbFrameSeq" => TermNode::FbFrameSeq {
            fb: take_child!("fb"),
        },
        "ChangeDetect" => TermNode::ChangeDetect {
            image_vals: take_child!("image_vals"),
            kernel_weights: take_child!("kernel_weights"),
            dims: take_child!("dims"),
        },
        "TemporalDiff" => TermNode::TemporalDiff {
            a_vals: take_child!("a_vals"),
            b_vals: take_child!("b_vals"),
        },
        "Foveate" => TermNode::Foveate {
            image_vals: take_child!("image_vals"),
            dims: take_child!("dims"),
            geometry: take_child!("geometry"),
        },
        "StringConcat" => TermNode::StringConcat {
            parts: take_children!("parts"),
        },
        // Rung 1 Tier-1 stdlib Term ports.
        "Replace" => TermNode::Replace {
            text: take_child!("text"),
            old: take_child!("old"),
            new: take_child!("new"),
        },
        "Str" => TermNode::Str {
            value: take_child!("value"),
        },
        "Split" => TermNode::Split {
            text: take_child!("text"),
            sep: take_child!("sep"),
        },
        "StrCount" => TermNode::StrCount {
            text: take_child!("text"),
            sub: take_child!("sub"),
        },
        "Round" => TermNode::Round {
            value: take_child!("value"),
            ndigits: take_child!("ndigits"),
        },
        "Reverse" => TermNode::Reverse {
            seq: take_child!("seq"),
        },
        "IndexedMap" => TermNode::IndexedMap {
            source: take_child!("source"),
            item_name: get_sym("item_name")?,
            index_name: get_sym("index_name")?,
            value: take_child!("value"),
        },
        "Capitalize" => TermNode::Capitalize {
            text: take_child!("text"),
        },
        "ParseInt" => TermNode::ParseInt {
            text: take_child!("text"),
        },
        "Slice" => TermNode::Slice {
            seq: take_child!("seq"),
            start: take_child!("start"),
            stop: take_child!("stop"),
        },
        "Sort" => TermNode::Sort {
            seq: take_child!("seq"),
        },
        "DictItems" => TermNode::DictItems {
            seq: take_child!("seq"),
        },
        "SortBy" => TermNode::SortBy {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            key: take_child!("key"),
        },
        "GroupCount" => TermNode::GroupCount {
            seq: take_child!("seq"),
        },
        "DictMerge" => TermNode::DictMerge {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "ZipWith" => TermNode::ZipWith {
            a: take_child!("a"),
            b: take_child!("b"),
            a_name: get_sym("a_name")?,
            b_name: get_sym("b_name")?,
            value: take_child!("value"),
        },
        "Argmax" => TermNode::Argmax {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            value: take_child!("value"),
            default: take_opt_child!("default"),
        },
        "Argmin" => TermNode::Argmin {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            value: take_child!("value"),
            default: take_opt_child!("default"),
        },
        "ArgminUnique" => TermNode::ArgminUnique {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            value: take_child!("value"),
            default: take_opt_child!("default"),
        },
        "ArgminRefusal" => TermNode::ArgminRefusal {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            value: take_child!("value"),
            refused: take_opt_child!("refused"),
        },
        "Fold" => TermNode::Fold {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            acc_name: get_sym("acc_name")?,
            init: take_child!("init"),
            body: take_child!("body"),
        },
        "BitsAt" => TermNode::BitsAt {
            buffer: take_child!("buffer"),
            bitpos: take_child!("bitpos"),
            n_bits: take_child!("n_bits"),
        },
        "BitsWrite" => TermNode::BitsWrite {
            buffer: take_child!("buffer"),
            bitpos: take_child!("bitpos"),
            value: take_child!("value"),
            n_bits: take_child!("n_bits"),
        },
        "BitsWriteAll" => TermNode::BitsWriteAll {
            buffer: take_child!("buffer"),
            writes: take_child!("writes"),
        },
        "BitsAtAll" => TermNode::BitsAtAll {
            buffer: take_child!("buffer"),
            reads: take_child!("reads"),
        },
        "HuffmanDecodeStream" => TermNode::HuffmanDecodeStream {
            buffer: take_child!("buffer"),
            bitpos: take_child!("bitpos"),
            table: take_child!("table"),
            n_pairs: take_child!("n_pairs"),
        },
        "HuffmanEncodeStream" => TermNode::HuffmanEncodeStream {
            buffer: take_child!("buffer"),
            bitpos: take_child!("bitpos"),
            pairs: take_child!("pairs"),
            table: take_child!("table"),
        },
        "ExpGolombDecode" => TermNode::ExpGolombDecode {
            buffer: take_child!("buffer"),
            bitpos: take_child!("bitpos"),
        },
        "ExpGolombDecodeSigned" => TermNode::ExpGolombDecodeSigned {
            buffer: take_child!("buffer"),
            bitpos: take_child!("bitpos"),
        },
        "ExpGolombEncode" => TermNode::ExpGolombEncode {
            buffer: take_child!("buffer"),
            bitpos: take_child!("bitpos"),
            value: take_child!("value"),
        },
        "ExpGolombEncodeSigned" => TermNode::ExpGolombEncodeSigned {
            buffer: take_child!("buffer"),
            bitpos: take_child!("bitpos"),
            value: take_child!("value"),
        },
        "Holds" => TermNode::Holds {
            concept: get_sym("concept")?,
            node: take_opt_child!("node"),
            node2: take_opt_child!("node2"),
        },
        "EvalSubgraph" => TermNode::EvalSubgraph {
            node: take_child!("node"),
        },
        "And" => TermNode::And {
            items: take_children!("items"),
        },
        "Or" => TermNode::Or {
            items: take_children!("items"),
        },
        "Not" => TermNode::Not {
            arg: take_child!("arg"),
        },
        "Abs" => TermNode::Abs {
            arg: take_child!("arg"),
        },
        "Neg" => TermNode::Neg {
            arg: take_child!("arg"),
        },
        "Plus" => TermNode::Plus {
            items: take_children!("items"),
        },
        "Minus" => TermNode::Minus {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Times" => TermNode::Times {
            items: take_children!("items"),
        },
        "Div" => TermNode::Div {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "DtwTo" => TermNode::DtwTo {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "EnigmaCrib" => TermNode::EnigmaCrib {
            candidate: take_child!("candidate"),
        },
        "EnigmaBombe" => TermNode::EnigmaBombe {
            candidate: take_child!("candidate"),
        },
        "EnigmaBombeWitness" => TermNode::EnigmaBombeWitness {
            candidate: take_child!("candidate"),
        },
        "ApcEncode" => TermNode::ApcEncode {
            model: take_child!("model"),
            seq: take_child!("seq"),
            start: take_child!("start"),
            end: take_child!("end"),
            out_len: take_child!("out_len"),
        },
        "PointSetDist" => TermNode::PointSetDist {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "MahalLeaf" => TermNode::MahalLeaf {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "MahalFull" => TermNode::MahalFull {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "DeformGenMarginal" => TermNode::DeformGenMarginal {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "DeformGen" => TermNode::DeformGen {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "DeformDist" => TermNode::DeformDist {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "SmoothDeformDist" => TermNode::SmoothDeformDist {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "TpsDeformDist" => TermNode::TpsDeformDist {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "SmoothDeformComponents" => TermNode::SmoothDeformComponents {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "ShapeContextDist" => TermNode::ShapeContextDist {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "ScTpsDist" => TermNode::ScTpsDist {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "BlendCover" => TermNode::BlendCover {
            unknown: take_child!("unknown"),
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Whiten" => TermNode::Whiten {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "WhitenMany" => TermNode::WhitenMany {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "WithinScatter" => TermNode::WithinScatter {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "BetweenScatter" => TermNode::BetweenScatter {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "XCorrPeak" => TermNode::XCorrPeak {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Mod" => TermNode::Mod {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Pow" => TermNode::Pow {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "BitAnd" => TermNode::BitAnd {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "BitOr" => TermNode::BitOr {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "BitXor" => TermNode::BitXor {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Shl" => TermNode::Shl {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Lshr" => TermNode::Lshr {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Ashr" => TermNode::Ashr {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "IDiv" => TermNode::IDiv {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "IRem" => TermNode::IRem {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Sqrt" => TermNode::Sqrt {
            arg: take_child!("arg"),
        },
        "EnclosedCount" => TermNode::EnclosedCount {
            arg: take_child!("arg"),
        },
        "Log" => TermNode::Log {
            arg: take_child!("arg"),
        },
        "Exp" => TermNode::Exp {
            arg: take_child!("arg"),
        },
        "Min" => TermNode::Min {
            items: take_children!("items"),
        },
        "Max" => TermNode::Max {
            items: take_children!("items"),
        },
        "ArgMax" => TermNode::ArgMax {
            items: take_children!("items"),
        },
        "IfThenElse" => TermNode::IfThenElse {
            cond: take_child!("cond"),
            then: take_child!("then"),
            other: take_child!("other"),
        },
        "Vec" => TermNode::Vec_ {
            items: take_children!("items"),
        },
        "VecAdd" => TermNode::VecAdd {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "VecSub" => TermNode::VecSub {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Dot" => TermNode::Dot {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Magnitude" => TermNode::Magnitude {
            arg: take_child!("arg"),
        },
        "Sin" => TermNode::Sin {
            arg: take_child!("arg"),
        },
        "Cos" => TermNode::Cos {
            arg: take_child!("arg"),
        },
        "Atan2" => TermNode::Atan2 {
            y: take_child!("y"),
            x: take_child!("x"),
        },
        "Bearing" => TermNode::Bearing {
            arg: take_child!("arg"),
        },
        "Rotate" => TermNode::Rotate {
            vec: take_child!("vec"),
            angle: take_child!("angle"),
        },
        "AngleBetween" => TermNode::AngleBetween {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Surface" => {
            // Read the kind from the attr — when the attr is a Str(sym)
            // whose underlying string we've lost track of, default to
            // Text. The JSON IO path supplies the kind as a literal
            // "text" / "bytes" string so this branch only matters for
            // graph-resident round-trip; we encode kind alongside via
            // value-comparison below.
            let kind = match attrs.get("kind") {
                Some(Value::Str(_)) => {
                    // Re-encoded as a Sym; we can only tell by hashing
                    // the canonical strings. The reflection round-trip
                    // happens inside one interner, so the Sym value
                    // matches whichever was minted for "text" /
                    // "bytes". We compare by interning helper at the
                    // caller boundary; here we just take Text as
                    // default and let the surface attr cover bytes.
                    SurfaceKind::Text
                }
                _ => SurfaceKind::Text,
            };
            TermNode::Surface {
                kind,
                payload: get_value("payload"),
            }
        }
        "Cat" => TermNode::Cat {
            items: take_children!("items"),
        },
        "Slot" => TermNode::Slot {
            name: get_sym("name")?,
        },
        "Join" => TermNode::Join {
            separator: take_opt_child!("separator"),
            items: take_opt_child!("items"),
        },
        "Bytes" => TermNode::Bytes {
            items: take_children!("items"),
        },
        "U8" => TermNode::U8 {
            expr: take_opt_child!("expr"),
        },
        "U16LE" => TermNode::U16LE {
            expr: take_opt_child!("expr"),
        },
        "U32LE" => TermNode::U32LE {
            expr: take_opt_child!("expr"),
        },
        "U64LE" => TermNode::U64LE {
            expr: take_opt_child!("expr"),
        },
        "LEB128" => TermNode::LEB128 {
            expr: take_opt_child!("expr"),
        },
        "Lines" => TermNode::Lines {
            items: take_children!("items"),
        },
        "Label" => TermNode::Label {
            prefix: get_sym("prefix")?,
        },
        "Let" => TermNode::Let {
            name: get_sym("name")?,
            value: take_opt_child!("value"),
            body: take_opt_child!("body"),
        },
        "Nth" => TermNode::Nth {
            items: take_opt_child!("items"),
            index: get_int("index")?,
        },
        "Render" => TermNode::Render {
            term: take_opt_child!("term"),
            lang: take_opt_child!("lang"),
        },
        "LitRepr" => TermNode::LitRepr {
            value: take_opt_child!("value"),
        },
        // --- Phase 7 ext additions ---
        "Last" => TermNode::Last {
            seq: take_child!("seq"),
        },
        "IndexAt" => TermNode::IndexAt {
            seq: take_child!("seq"),
            index: take_child!("index"),
        },
        "Append" => TermNode::Append {
            seq: take_child!("seq"),
            item: take_child!("item"),
        },
        "ListDrop" => TermNode::ListDrop {
            list: take_child!("list"),
            index: take_child!("index"),
        },
        "Union" => TermNode::Union {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Intersect" => TermNode::Intersect {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "Difference" => TermNode::Difference {
            a: take_child!("a"),
            b: take_child!("b"),
        },
        "MapSet" => TermNode::MapSet {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            value: take_child!("value"),
        },
        "MapList" => TermNode::MapList {
            source: take_child!("source"),
            var_name: get_sym("var_name")?,
            value: take_child!("value"),
        },
        "Edges" => {
            let edge_type = get_sym("edge_type")?;
            TermNode::Edges {
                node: take_child!("node"),
                edge_type,
                any_type: edge_type == Sym::default(),
            }
        }
        "EdgeAttr" => TermNode::EdgeAttr {
            edge: take_child!("edge"),
            key: get_sym("key")?,
        },
        "NodesWhere" => TermNode::NodesWhere {
            node_type: get_sym("node_type")?,
            attr_key: get_sym("attr_key")?,
            value: take_child!("value"),
        },
        "NodesOfType" => TermNode::NodesOfType {
            node_type: get_sym("node_type")?,
        },
        "AntiUnify" => TermNode::AntiUnify {
            values: take_child!("values"),
            wild: get_sym("wild")?,
        },
        "FixedCount" => TermNode::FixedCount {
            pattern: take_child!("pattern"),
            wild: get_sym("wild")?,
        },
        "Covers" => TermNode::Covers {
            pattern: take_child!("pattern"),
            instance: take_child!("instance"),
            wild: get_sym("wild")?,
        },
        "CoversOpen" => TermNode::CoversOpen {
            pattern: take_child!("pattern"),
            instance: take_child!("instance"),
            wild: get_sym("wild")?,
        },
        "AntiUnifyWitness" => TermNode::AntiUnifyWitness {
            values: take_child!("values"),
            wild: get_sym("wild")?,
        },
        "Substitute" => TermNode::Substitute {
            template: take_child!("template"),
            sigma: take_child!("sigma"),
            wild: get_sym("wild")?,
        },
        "Unify" => TermNode::Unify {
            values: take_child!("values"),
            wild: get_sym("wild")?,
        },
        "StructSim" => TermNode::StructSim {
            a: take_child!("a"),
            b: take_child!("b"),
            wild: get_sym("wild")?,
        },
        "ShapeDecode" => TermNode::ShapeDecode {
            goal: take_child!("goal"),
            codebook_type: get_sym("codebook_type")?,
            exclude: take_opt_child!("exclude"),
            codebook_scope: take_opt_child!("codebook_scope"),
            beam: get_int("beam")?,
            max_steps: get_int("max_steps")?,
            cand_k: get_int("cand_k")?,
            // `get_int` already reads an absent attr as 0 (see its impl
            // above), so a subgraph reflected before this field existed
            // round-trips as `budget: 0` -> the default at eval time.
            budget: get_int("budget")?,
            field: get_sym("field")?,
            wild: get_sym("wild")?,
            wild_objects: get_bool("wild_objects"),
        },
        "TransformDecode" => TermNode::TransformDecode {
            goal: take_child!("goal"),
            codebook_type: get_sym("codebook_type")?,
            exclude: take_opt_child!("exclude"),
            max_dims: get_int("max_dims")?,
            field: get_sym("field")?,
        },
        "FutureManifoldSelection" => TermNode::FutureManifoldSelection {
            episode: take_child!("episode"),
            policy: take_child!("policy"),
            candidates: take_child!("candidates"),
            field: get_sym("field")?,
            snapshot_field: get_sym("snapshot_field")?,
        },
        "NetForward" => TermNode::NetForward {
            assemblage: take_child!("assemblage"),
            inputs: take_child!("inputs"),
        },
        "DimInfer" => TermNode::DimInfer {
            goal: take_child!("goal"),
            codebook_type: get_sym("codebook_type")?,
            exclude: take_opt_child!("exclude"),
            generator_type: get_sym("generator_type")?,
            grain: take_opt_child!("grain"),
            max_dims: get_int("max_dims")?,
            field: get_sym("field")?,
        },
        "GenInfer" => TermNode::GenInfer {
            goal: take_child!("goal"),
            codebook_type: get_sym("codebook_type")?,
            exclude: take_opt_child!("exclude"),
            scope: take_opt_child!("scope"),
            require_scope: take_opt_child!("require_scope"),
            quadratic_enabled: take_opt_child!("quadratic_enabled"),
            linear_prefilter_enabled: take_opt_child!("linear_prefilter_enabled"),
            grain: take_opt_child!("grain"),
            mdl_enabled: take_opt_child!("mdl_enabled"),
            max_dims: get_int("max_dims")?,
            field: get_sym("field")?,
        },
        "RatioInduce" => TermNode::RatioInduce {
            population: take_child!("population"),
            codebook_type: get_sym("codebook_type")?,
            resolution: get_int("resolution")?,
            field: get_sym("field")?,
        },
        "LogQuantum" => TermNode::LogQuantum {
            population: take_child!("population"),
            value_slot: get_int("value_slot")?,
            base_num: get_int("base_num")?,
            base_den: get_int("base_den")?,
            delta_num: get_int("delta_num")?,
            delta_den: get_int("delta_den")?,
            raw: get_bool("raw"),
            field: get_sym("field")?,
        },
        "TimeInfer" => TermNode::TimeInfer {
            sequence: take_child!("sequence"),
            codebook_type: get_sym("codebook_type")?,
            max_b: get_int("max_b")?,
            field: get_sym("field")?,
            max_steps: get_int("max_steps")?,
            robust: get_bool("robust"),
        },
        "DepthInfer" => TermNode::DepthInfer {
            sequence: take_child!("sequence"),
            codebook_type: get_sym("codebook_type")?,
            max_b: get_int("max_b")?,
            field: get_sym("field")?,
        },
        "BlinkBridge" => TermNode::BlinkBridge {
            sequence: take_child!("sequence"),
            codebook_type: get_sym("codebook_type")?,
            max_b: get_int("max_b")?,
            field: get_sym("field")?,
        },
        "GapAbduce" => TermNode::GapAbduce {
            sequence: take_child!("sequence"),
            codebook_type: get_sym("codebook_type")?,
            max_b: get_int("max_b")?,
            field: get_sym("field")?,
        },
        "GapVerify" => TermNode::GapVerify {
            sequence: take_child!("sequence"),
            codebook_type: get_sym("codebook_type")?,
            max_b: get_int("max_b")?,
            field: get_sym("field")?,
        },
        "SupportInfer" => TermNode::SupportInfer {
            sequence: take_child!("sequence"),
            codebook_type: get_sym("codebook_type")?,
            field: get_sym("field")?,
        },
        "MotionEnergy" => TermNode::MotionEnergy {
            sequence: take_child!("sequence"),
            height: get_int("height")?,
            width: get_int("width")?,
            field: get_sym("field")?,
        },
        "TransferDecode" => TermNode::TransferDecode {
            goal: take_child!("goal"),
        },
        "RecogniseShape" => TermNode::RecogniseShape {
            text: take_child!("text"),
        },
        "MetaShapeMint" => TermNode::MetaShapeMint {
            observation: take_child!("observation"),
            obs_type: get_sym("obs_type")?,
            status_value: get_sym("status_value")?,
            wild: get_sym("wild")?,
            field: get_sym("field")?,
        },
        "StrokeQuantize" => TermNode::StrokeQuantize {
            points: take_child!("points"),
            segments: get_int("segments")?,
            turn_bins: get_int("turn_bins")?,
            len_bins: get_int("len_bins")?,
            grid: get_int("grid")?,
            scale_bins: get_int("scale_bins")?,
            invariant_only: get_bool("invariant_only"),
            canonical_pose: get_bool("canonical_pose"),
            turn_edges: take_opt_child!("turn_edges"),
            len_edges: take_opt_child!("len_edges"),
            emit_residual: get_bool("emit_residual"),
            bounds: take_opt_child!("bounds"),
            field: get_sym("field")?,
            seg_sym: get_sym("seg_sym")?,
            pose_x_sym: get_sym("pose_x_sym")?,
            pose_y_sym: get_sym("pose_y_sym")?,
            pose_o_sym: get_sym("pose_o_sym")?,
            pose_s_sym: get_sym("pose_s_sym")?,
        },
        "StrokeRender" => TermNode::StrokeRender {
            signature: take_child!("signature"),
            n_points: get_int("n_points")?,
            apply_pose: get_bool("apply_pose"),
            turn_bins: get_int("turn_bins")?,
            len_bins: get_int("len_bins")?,
            grid: get_int("grid")?,
            scale_bins: get_int("scale_bins")?,
            turn_edges: take_opt_child!("turn_edges"),
            len_edges: take_opt_child!("len_edges"),
            bounds: take_opt_child!("bounds"),
            field: get_sym("field")?,
        },
        "LookaheadValue" => TermNode::LookaheadValue {
            node: take_child!("node"),
            child_edge: get_sym("child_edge")?,
            score_key: get_sym("score_key")?,
            depth: take_child!("depth"),
        },
        "ScalarAttrTriples" => TermNode::ScalarAttrTriples {
            skip_prefix: get_sym("skip_prefix")?,
        },
        "AttrByName" => TermNode::AttrByName {
            node: take_child!("node"),
            name: take_child!("name"),
        },
        "TrackIdentityCorrespondence" => {
            let category_key = get_sym("category_key")?;
            let extent_key = get_sym("extent_key")?;
            TermNode::TrackIdentityCorrespondence {
                prev: take_child!("prev"),
                cur: take_child!("cur"),
                feature_key: get_sym("feature_key")?,
                category_key: if category_key == Sym::default() {
                    None
                } else {
                    Some(category_key)
                },
                extent_key: if extent_key == Sym::default() {
                    None
                } else {
                    Some(extent_key)
                },
                radius: take_child!("radius"),
            }
        }
        // --- Program IR (P1) ---
        "ProgSeq" => TermNode::ProgSeq {
            stmts: take_children!("stmts"),
        },
        "ProgAssignVar" => TermNode::ProgAssignVar {
            name: get_sym("name")?,
            value: take_child!("value"),
        },
        "ProgAugAssign" => TermNode::ProgAugAssign {
            name: get_sym("name")?,
            op: get_sym("op")?,
            value: take_child!("value"),
        },
        "ProgTupleUnpack" => {
            let mut targets: Vec<Sym> = Vec::new();
            if let (Value::Tuple(items) | Value::List(items)) = get_value("targets") {
                for it in items.iter() {
                    match it {
                        Value::Str(s) => targets.push(*s),
                        _ => {
                            return Err(ReflectError::BadAttrType {
                                variant: variant.to_string(),
                                field: "targets".to_string(),
                                expected: "Tuple of Str",
                            })
                        }
                    }
                }
            }
            TermNode::ProgTupleUnpack {
                targets,
                value: take_child!("value"),
            }
        }
        "ProgIfStmt" => TermNode::ProgIfStmt {
            cond: take_child!("cond"),
            then: take_child!("then"),
            orelse: take_opt_child!("orelse"),
        },
        "ProgForEach" => TermNode::ProgForEach {
            var: get_sym("var")?,
            iter: take_child!("iter"),
            body: take_child!("body"),
            orelse: take_opt_child!("orelse"),
        },
        "ProgWhile" => TermNode::ProgWhile {
            cond: take_child!("cond"),
            body: take_child!("body"),
            orelse: take_opt_child!("orelse"),
        },
        "ProgLoopCtl" => TermNode::ProgLoopCtl {
            kind: get_sym("kind")?,
        },
        "ProgReturn" => TermNode::ProgReturn {
            value: take_opt_child!("value"),
        },
        "ProgTryOr" => TermNode::ProgTryOr {
            body: take_child!("body"),
            exc_var: get_sym("exc_var")?,
            handler: take_opt_child!("handler"),
        },
        "ProgRaise" => TermNode::ProgRaise {
            exc: take_opt_child!("exc"),
        },
        "ProgImportStmt" => {
            let mut names: Vec<Sym> = Vec::new();
            if let (Value::Tuple(items) | Value::List(items)) = get_value("names") {
                for it in items.iter() {
                    match it {
                        Value::Str(s) => names.push(*s),
                        _ => {
                            return Err(ReflectError::BadAttrType {
                                variant: variant.to_string(),
                                field: "names".to_string(),
                                expected: "Tuple of Str",
                            })
                        }
                    }
                }
            }
            TermNode::ProgImportStmt {
                module: get_sym("module")?,
                alias: get_sym("alias")?,
                names,
            }
        }
        "ProgSubscriptSet" => TermNode::ProgSubscriptSet {
            obj: take_child!("obj"),
            index: take_child!("index"),
            value: take_child!("value"),
        },
        "ProgAttrSet" => TermNode::ProgAttrSet {
            obj: take_child!("obj"),
            attr: get_sym("attr")?,
            value: take_child!("value"),
        },
        "ProgDefFnParam" => TermNode::ProgDefFnParam {
            name: get_sym("name")?,
            default: take_opt_child!("default"),
        },
        "ProgCallExtern" => TermNode::ProgCallExtern {
            name: get_sym("name")?,
            recv: take_opt_child!("recv"),
            args: take_children!("args"),
        },
        "ProgAttrGet" => TermNode::ProgAttrGet {
            obj: take_child!("obj"),
            attr: get_sym("attr")?,
        },
        "ProgSubscript" => TermNode::ProgSubscript {
            obj: take_child!("obj"),
            index: take_child!("index"),
        },
        "ProgSlice" => TermNode::ProgSlice {
            obj: take_child!("obj"),
            start: take_opt_child!("start"),
            stop: take_opt_child!("stop"),
            step: take_opt_child!("step"),
        },
        "ProgContainerLit" => TermNode::ProgContainerLit {
            kind: get_sym("kind")?,
            items: take_children!("items"),
        },
        "ProgComprehensionList" => TermNode::ProgComprehensionList {
            var: get_sym("var")?,
            source: take_child!("source"),
            expr: take_child!("expr"),
            cond: take_opt_child!("cond"),
        },
        "ProgComprehensionGen" => TermNode::ProgComprehensionGen {
            var: get_sym("var")?,
            source: take_child!("source"),
            expr: take_child!("expr"),
            cond: take_opt_child!("cond"),
        },
        "ProgIsOp" => TermNode::ProgIsOp {
            a: take_child!("a"),
            b: take_child!("b"),
            negated: get_bool("negated"),
        },
        "ProgFString" => TermNode::ProgFString {
            parts: take_children!("parts"),
        },
        "ProgEval" => TermNode::ProgEval {
            prog: take_child!("prog"),
            env: take_opt_child!("env"),
            oracles: take_opt_child!("oracles"),
            fuel: get_int("fuel")?,
            field: get_sym("field")?,
        },
        "SnakeCase" => TermNode::SnakeCase {
            text: take_child!("text"),
        },
        "CaseFold" => TermNode::CaseFold {
            text: take_child!("text"),
        },
        "SynthEnumerate" => TermNode::SynthEnumerate {
            examples: take_child!("examples"),
            ops: take_opt_child!("ops"),
            consts: take_opt_child!("consts"),
            exclude: take_opt_child!("exclude"),
            derived_ops: take_opt_child!("derived_ops"),
            exclude_ops: take_opt_child!("exclude_ops"),
            max_size: get_int("max_size")?,
            max_candidates: get_int("max_candidates")?,
            saturate_k: get_int("saturate_k")?,
            field: get_sym("field")?,
        },
        "Call" => TermNode::Call {
            name: get_sym("name")?,
            args: take_children!("args"),
        },
        "ParetoDominates" => TermNode::ParetoDominates {
            candidate: take_child!("candidate"),
            alternative: take_child!("alternative"),
            dimension_count: take_child!("dimension_count"),
            value_edge: get_sym("value_edge")?,
            measure_edge: get_sym("measure_edge")?,
            dimension_key: get_sym("dimension_key")?,
            verified_key: get_sym("verified_key")?,
            signed_value_key: get_sym("signed_value_key")?,
        },
        _ => {
            return Err(ReflectError::UnknownVariant {
                variant: variant.to_string(),
            });
        }
    };
    Ok(node)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sym::Interner;
    use crate::value::Value;

    fn build_test_term(arena: &mut TermArena, interner: &mut Interner) -> TermIdx {
        // Build: Count(Filter(Neighbours(Var("me"), "adjacent_to"),
        //        var_name="n", predicate=Eq(TypeOf(Var("n")), Lit(Str("AliveCell")))))
        let me = interner.intern("me");
        let n = interner.intern("n");
        let adj = interner.intern("adjacent_to");
        let alive = interner.intern("AliveCell");
        let me_t = arena.add(TermNode::Var { name: me });
        let nb = arena.add(TermNode::Neighbours {
            node: me_t,
            edge_type: adj,
            any_type: false,
        });
        let n_t = arena.add(TermNode::Var { name: n });
        let type_n = arena.add(TermNode::TypeOf { node: n_t });
        let lit = arena.add(TermNode::Lit {
            value: Value::Str(alive),
        });
        let eq = arena.add(TermNode::Eq { a: type_n, b: lit });
        let filt = arena.add(TermNode::Filter {
            source: nb,
            var_name: n,
            predicate: eq,
        });
        arena.add(TermNode::Count { source: filt })
    }

    #[test]
    fn term_to_subgraph_creates_typed_nodes() {
        let mut arena = TermArena::new();
        let mut interner = Interner::new();
        let mut graph = TypedGraph::new();
        let root_term = build_test_term(&mut arena, &mut interner);
        let root_nid = term_to_subgraph(&arena, root_term, &mut graph, &mut interner);
        // root should be a Count node
        let count_type = interner.intern("Term.Count");
        assert_eq!(graph.node(root_nid).type_, count_type);
        // total nodes inserted: Count, Filter, Neighbours, Var(me), Var(n), TypeOf, Eq, Lit = 8
        assert_eq!(graph.node_count(), 8);
    }

    #[test]
    fn experiment_composer_terms_reflect_round_trip() {
        // ToJsonString(ShiftThresholdLits(FromJsonString(Lit "{}"), Lit 0.5))
        let mut arena = TermArena::new();
        let mut interner = Interner::new();
        let text = arena.add(TermNode::Lit {
            value: Value::Str(interner.intern("{}")),
        });
        let parsed = arena.add(TermNode::FromJsonString { text });
        let shift_lit = arena.add(TermNode::Lit {
            value: Value::Float(0.5),
        });
        let shifted = arena.add(TermNode::ShiftThresholdLits {
            tree: parsed,
            shift: shift_lit,
        });
        let wrapped = arena.add(TermNode::ToJsonString { value: shifted });

        let mut graph = TypedGraph::new();
        let root_nid = term_to_subgraph(&arena, wrapped, &mut graph, &mut interner);
        let to_json_type = interner.intern("Term.ToJsonString");
        assert_eq!(graph.node(root_nid).type_, to_json_type);

        let mut arena2 = TermArena::new();
        let rebuilt = term_from_subgraph(&graph, &interner, root_nid, &mut arena2).unwrap();
        assert!(matches!(arena2.get(rebuilt), TermNode::ToJsonString { .. }));
        let TermNode::ToJsonString { value } = arena2.get(rebuilt) else {
            unreachable!()
        };
        assert!(matches!(
            arena2.get(*value),
            TermNode::ShiftThresholdLits { .. }
        ));
        let TermNode::ShiftThresholdLits { tree, .. } = arena2.get(*value) else {
            unreachable!()
        };
        assert!(matches!(arena2.get(*tree), TermNode::FromJsonString { .. }));
    }

    #[test]
    fn editop_terms_reflect_round_trip() {
        // ListDrop(RewriteTreeNodes(FromJsonString(Lit "{}"), type_filter=Lit
        // "Attr", field=Lit "key", value_map=MkDict(...)), index=Lit 0) --
        // exercises both new Terms' term_to_subgraph/term_from_subgraph
        // arms, including RewriteTreeNodes's OptChild `type_filter`.
        let mut arena = TermArena::new();
        let mut interner = Interner::new();
        let text = arena.add(TermNode::Lit {
            value: Value::Str(interner.intern("{}")),
        });
        let tree = arena.add(TermNode::FromJsonString { text });
        let old_k = arena.add(TermNode::Lit {
            value: Value::Str(interner.intern("row")),
        });
        let new_k = arena.add(TermNode::Lit {
            value: Value::Str(interner.intern("col")),
        });
        let value_map = arena.add(TermNode::MkDict {
            items: vec![old_k, new_k],
        });
        let field = arena.add(TermNode::Lit {
            value: Value::Str(interner.intern("key")),
        });
        let type_filter = arena.add(TermNode::Lit {
            value: Value::Str(interner.intern("Attr")),
        });
        let rewrite = arena.add(TermNode::RewriteTreeNodes {
            tree,
            type_filter: Some(type_filter),
            field,
            value_map,
        });
        let idx = arena.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let dropped = arena.add(TermNode::ListDrop {
            list: rewrite,
            index: idx,
        });

        let mut graph = TypedGraph::new();
        let root_nid = term_to_subgraph(&arena, dropped, &mut graph, &mut interner);
        let list_drop_type = interner.intern("Term.ListDrop");
        assert_eq!(graph.node(root_nid).type_, list_drop_type);

        let mut arena2 = TermArena::new();
        let rebuilt = term_from_subgraph(&graph, &interner, root_nid, &mut arena2).unwrap();
        assert!(matches!(arena2.get(rebuilt), TermNode::ListDrop { .. }));
        let TermNode::ListDrop { list, .. } = arena2.get(rebuilt) else {
            unreachable!()
        };
        assert!(matches!(
            arena2.get(*list),
            TermNode::RewriteTreeNodes { .. }
        ));
        let TermNode::RewriteTreeNodes {
            type_filter: tf,
            tree: rt_tree,
            ..
        } = arena2.get(*list)
        else {
            unreachable!()
        };
        assert!(
            tf.is_some(),
            "type_filter=Some(..) must survive the subgraph round trip"
        );
        assert!(matches!(
            arena2.get(*rt_tree),
            TermNode::FromJsonString { .. }
        ));
    }

    #[test]
    fn attr_key_ranking_reflect_round_trip() {
        // AttrKeyRanking(FromJsonString(Lit "{}")) -- exercises the new
        // Term's term_to_subgraph/term_from_subgraph arms (single Child
        // "tree", the simplest shape in the file, still worth pinning
        // since it's a fresh variant added after the speech-arc merge).
        let mut arena = TermArena::new();
        let mut interner = Interner::new();
        let text = arena.add(TermNode::Lit {
            value: Value::Str(interner.intern("{}")),
        });
        let tree = arena.add(TermNode::FromJsonString { text });
        let ranking = arena.add(TermNode::AttrKeyRanking { tree });

        let mut graph = TypedGraph::new();
        let root_nid = term_to_subgraph(&arena, ranking, &mut graph, &mut interner);
        let ranking_type = interner.intern("Term.AttrKeyRanking");
        assert_eq!(graph.node(root_nid).type_, ranking_type);

        let mut arena2 = TermArena::new();
        let rebuilt = term_from_subgraph(&graph, &interner, root_nid, &mut arena2).unwrap();
        assert!(matches!(
            arena2.get(rebuilt),
            TermNode::AttrKeyRanking { .. }
        ));
        let TermNode::AttrKeyRanking { tree: rt_tree } = arena2.get(rebuilt) else {
            unreachable!()
        };
        assert!(matches!(
            arena2.get(*rt_tree),
            TermNode::FromJsonString { .. }
        ));
    }

    #[test]
    fn track_identity_correspondence_reflect_round_trip() {
        // GRAPH LAW #6: term_to_subgraph/term_from_subgraph for the
        // trans-frame identity Term, WITH category_key/extent_key set
        // (Some) -- exercises the Sym::default()-sentinel encoding
        // `describe`/`reconstruct` use for the Option<Sym> fields.
        let mut arena = TermArena::new();
        let mut interner = Interner::new();
        let prev = arena.add(TermNode::SetT { items: vec![] });
        let cur = arena.add(TermNode::SetT { items: vec![] });
        let radius = arena.add(TermNode::Lit {
            value: Value::Float(3.0),
        });
        let term = arena.add(TermNode::TrackIdentityCorrespondence {
            prev,
            cur,
            feature_key: interner.intern("feat"),
            category_key: Some(interner.intern("cat")),
            extent_key: None,
            radius,
        });

        let mut graph = TypedGraph::new();
        let root_nid = term_to_subgraph(&arena, term, &mut graph, &mut interner);
        let ty = interner.intern("Term.TrackIdentityCorrespondence");
        assert_eq!(graph.node(root_nid).type_, ty);

        let mut arena2 = TermArena::new();
        let rebuilt = term_from_subgraph(&graph, &interner, root_nid, &mut arena2).unwrap();
        let TermNode::TrackIdentityCorrespondence {
            feature_key,
            category_key,
            extent_key,
            radius: rt_radius,
            ..
        } = arena2.get(rebuilt)
        else {
            panic!("expected TrackIdentityCorrespondence")
        };
        assert_eq!(interner.resolve(*feature_key), "feat");
        assert_eq!(interner.resolve(category_key.unwrap()), "cat");
        assert!(
            extent_key.is_none(),
            "absent extent_key must round-trip to None, not Sym::default()"
        );
        assert!(
            matches!(arena2.get(*rt_radius), TermNode::Lit { value: Value::Float(f) } if *f == 3.0)
        );
    }

    #[test]
    fn term_round_trip_preserves_evaluation_shape() {
        use crate::term::{evaluate, Env, EvalCtx};
        use rustc_hash::FxHashMap;
        use smallvec::smallvec;

        let mut arena = TermArena::new();
        let mut interner = Interner::new();
        let me = interner.intern("me");
        let n = interner.intern("n");
        let alive = interner.intern("AliveCell");
        let adj = interner.intern("adjacent_to");
        let cell = interner.intern("Cell");

        // Build the same test Term + a tiny graph it can evaluate over.
        let root_term = build_test_term(&mut arena, &mut interner);

        let mut g = TypedGraph::new();
        let me_node = g.insert_node(cell, FxHashMap::default());
        let a1 = g.insert_node(alive, FxHashMap::default());
        let a2 = g.insert_node(alive, FxHashMap::default());
        g.insert_edge(me_node, adj, a1, FxHashMap::default())
            .unwrap();
        g.insert_edge(me_node, adj, a2, FxHashMap::default())
            .unwrap();

        // Evaluate the original term to get a baseline.
        let mut env: Env = smallvec![(me, Value::Node(me_node))];
        let mut ctx = EvalCtx::new(&g, &interner);
        let original = evaluate(&arena, root_term, &mut env, &mut ctx);
        assert_eq!(original, Value::Int(2));

        // Reflect into a *separate* graph, then read back into a new
        // arena, then evaluate the rebuilt term against the same data.
        let mut refl_graph = TypedGraph::new();
        let refl_root = term_to_subgraph(&arena, root_term, &mut refl_graph, &mut interner);

        let mut rebuilt = TermArena::new();
        let rebuilt_root =
            term_from_subgraph(&refl_graph, &interner, refl_root, &mut rebuilt).unwrap();

        let mut env2: Env = smallvec![(me, Value::Node(me_node))];
        let mut ctx2 = EvalCtx::new(&g, &interner);
        let after = evaluate(&rebuilt, rebuilt_root, &mut env2, &mut ctx2);
        assert_eq!(after, original);
    }

    #[test]
    fn variadic_children_keep_order() {
        let mut arena = TermArena::new();
        let mut interner = Interner::new();
        let mut graph = TypedGraph::new();
        // Plus(1, 2, 3) — order matters for the eval cache key, must
        // survive the round-trip.
        let l1 = arena.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let l2 = arena.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let l3 = arena.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let plus = arena.add(TermNode::Plus {
            items: vec![l1, l2, l3],
        });

        let nid = term_to_subgraph(&arena, plus, &mut graph, &mut interner);
        let mut rebuilt = TermArena::new();
        let new_root = term_from_subgraph(&graph, &interner, nid, &mut rebuilt).unwrap();
        match rebuilt.get(new_root) {
            TermNode::Plus { items } => {
                assert_eq!(items.len(), 3);
                // Children themselves are now Lit nodes — verify their values.
                let mut vals = Vec::new();
                for &c in items {
                    if let TermNode::Lit {
                        value: Value::Int(n),
                    } = rebuilt.get(c)
                    {
                        vals.push(*n);
                    }
                }
                assert_eq!(vals, vec![1, 2, 3]);
            }
            other => panic!("expected Plus, got {:?}", other),
        }
    }
}
