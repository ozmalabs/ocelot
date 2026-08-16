//! Term ↔ JSON wire format. `substrate/jsonio.py` port.
//!
//! JSON shape: `{"type": "Filter", "source": {...}, "var_name": "n",
//! "predicate": {...}}`. Scalar fields pass through as JSON scalars;
//! Sym fields serialise as strings (resolved through the interner);
//! child Terms recurse; tuple children become JSON arrays of Terms.
//!
//! Wire-compatible with the Python `jsonio.py` — a Term written here
//! loads in Python and vice versa, which lets external tools (the
//! frontend, the grammar diff visualiser, anything that wants to read
//! Γ as text) operate without needing the runtime.

use crate::grammar::{Grammar, NodePattern, Production};
use crate::persist::{decode_value, encode_value};
use crate::sym::{Interner, Sym};
use crate::term::{TermArena, TermIdx, TermNode};
use crate::value::{SurfaceKind, Value};
use serde_json::{json, Map, Value as J};

/// Default forward-projection horizon for `TimeInfer`'s `crossing` field.
/// A bound on how far the fitted generator is walked, never an order cap.
const DEFAULT_TIME_INFER_MAX_STEPS: i64 = 1024;

/// Serialise a Term subtree to the Python wire format.
pub fn term_to_json(arena: &TermArena, idx: TermIdx, interner: &Interner) -> J {
    let node = arena.get(idx);
    let mut m = Map::new();
    m.insert("type".into(), J::String(variant_name(node).to_string()));
    write_fields(node, arena, interner, &mut m);
    J::Object(m)
}

/// Inverse of `term_to_json`. Interns string fields on the way in;
/// builds Term children into `arena` recursively.
pub fn term_from_json(
    j: &J,
    arena: &mut TermArena,
    interner: &mut Interner,
) -> Result<TermIdx, JsonError> {
    let obj = j
        .as_object()
        .ok_or(JsonError::ShapeMismatch("expected JSON object for Term"))?;
    let variant = obj
        .get("type")
        .and_then(|v| v.as_str())
        .ok_or(JsonError::ShapeMismatch("missing 'type' field"))?;
    read_term(variant, obj, arena, interner)
}

/// Serialise a Grammar (its productions) to JSON. Matches the Python
/// `grammar_to_json` shape exactly so a grammar.json file moves
/// between Python and Rust unmodified.
pub fn grammar_to_json(grammar: &Grammar, arena: &TermArena, interner: &Interner) -> J {
    let mut prods = Vec::new();
    for p in &grammar.productions {
        let where_ = p.where_.map(|w| term_to_json(arena, w, interner));
        // weight is always present here (paper requirement); on the
        // wire it stays Optional for Python compat — None encoded as
        // the Lit(1.0) default Term.
        let weight_default_lit_1 = matches!(arena.get(p.weight), TermNode::Lit { value: Value::Float(f) } if *f == 1.0);
        let weight = if weight_default_lit_1 {
            None
        } else {
            Some(term_to_json(arena, p.weight, interner))
        };
        prods.push(json!({
            "provenance": interner.resolve(p.provenance),
            "src": { "type": interner.resolve(p.src.type_), "var": interner.resolve(p.src.var) },
            "edge_type": interner.resolve(p.edge_type),
            "tgt": { "type": interner.resolve(p.tgt.type_), "var": interner.resolve(p.tgt.var) },
            "where": where_.unwrap_or(J::Null),
            "weight": weight.unwrap_or(J::Null),
        }));
    }
    json!({ "productions": J::Array(prods) })
}

/// Inverse of `grammar_to_json`. Builds the indexed Grammar.
pub fn grammar_from_json(
    j: &J,
    arena: &mut TermArena,
    interner: &mut Interner,
) -> Result<Grammar, JsonError> {
    let obj = j
        .as_object()
        .ok_or(JsonError::ShapeMismatch("grammar object"))?;
    let prods = obj
        .get("productions")
        .and_then(|p| p.as_array())
        .ok_or(JsonError::ShapeMismatch("productions array"))?;
    let mut g = Grammar::new();
    for pd in prods {
        let src = pd
            .get("src")
            .and_then(|s| s.as_object())
            .ok_or(JsonError::ShapeMismatch("production src"))?;
        let tgt = pd
            .get("tgt")
            .and_then(|s| s.as_object())
            .ok_or(JsonError::ShapeMismatch("production tgt"))?;
        let edge_type = pd
            .get("edge_type")
            .and_then(|s| s.as_str())
            .ok_or(JsonError::ShapeMismatch("edge_type"))?;
        let provenance = pd.get("provenance").and_then(|s| s.as_str()).unwrap_or("");
        let where_ = match pd.get("where") {
            Some(J::Null) | None => None,
            Some(other) => Some(term_from_json(other, arena, interner)?),
        };
        let weight = match pd.get("weight") {
            Some(J::Null) | None => Grammar::default_weight(arena),
            Some(other) => term_from_json(other, arena, interner)?,
        };
        g.add(Production {
            src: NodePattern {
                type_: interner.intern(node_pattern_type(src)?),
                var: interner.intern(node_pattern_var(src)?),
            },
            edge_type: interner.intern(edge_type),
            tgt: NodePattern {
                type_: interner.intern(node_pattern_type(tgt)?),
                var: interner.intern(node_pattern_var(tgt)?),
            },
            where_,
            weight,
            provenance: interner.intern(provenance),
        });
    }
    Ok(g)
}

fn node_pattern_type(m: &Map<String, J>) -> Result<&str, JsonError> {
    m.get("type")
        .and_then(|s| s.as_str())
        .ok_or(JsonError::ShapeMismatch("node pattern type"))
}

fn node_pattern_var(m: &Map<String, J>) -> Result<&str, JsonError> {
    m.get("var")
        .and_then(|s| s.as_str())
        .ok_or(JsonError::ShapeMismatch("node pattern var"))
}

#[derive(Debug, Clone)]
pub enum JsonError {
    ShapeMismatch(&'static str),
    UnknownTermType(String),
    MissingField { variant: String, field: String },
}

// --- Per-variant emit / read ---

fn variant_name(node: &TermNode) -> &'static str {
    match node {
        TermNode::Var { .. } => "Var",
        TermNode::Lit { .. } => "Lit",
        TermNode::TypeOf { .. } => "TypeOf",
        TermNode::Attr { .. } => "Attr",
        TermNode::UseTool { .. } => "UseTool",
        TermNode::SetT { .. } => "SetT",
        TermNode::In { .. } => "In",
        TermNode::Eq { .. } => "Eq",
        TermNode::Lt { .. } => "Lt",
        TermNode::Lte { .. } => "Lte",
        TermNode::Gt { .. } => "Gt",
        TermNode::Gte { .. } => "Gte",
        TermNode::Neighbours { .. } => "Neighbours",
        TermNode::ReachableFrom { .. } => "ReachableFrom",

        TermNode::SlideNeighbours { .. } => "SlideNeighbours",
        TermNode::InNeighbours { .. } => "InNeighbours",
        TermNode::MapNeighbours { .. } => "MapNeighbours",
        TermNode::Count { .. } => "Count",
        TermNode::Filter { .. } => "Filter",
        TermNode::FilterList { .. } => "FilterList",
        TermNode::Exists { .. } => "Exists",
        TermNode::Sum { .. } => "Sum",
        TermNode::Prod { .. } => "Prod",
        TermNode::MinOver { .. } => "MinOver",
        TermNode::MaxOver { .. } => "MaxOver",
        TermNode::Pick { .. } => "Pick",
        TermNode::PickUnique { .. } => "PickUnique",
        TermNode::Tokenize { .. } => "Tokenize",
        TermNode::MorphHead { .. } => "MorphHead",
        TermNode::MorphTail { .. } => "MorphTail",
        TermNode::FinalToken { .. } => "FinalToken",
        TermNode::Tokenize2 { .. } => "Tokenize2",
        TermNode::ReadFile { .. } => "ReadFile",
        TermNode::StringIndexOf { .. } => "StringIndexOf",
        TermNode::StringSlice { .. } => "StringSlice",
        TermNode::Verify { .. } => "Verify",
        TermNode::MkDict { .. } => "MkDict",
        TermNode::ToJsonString { .. } => "ToJsonString",
        TermNode::FromJsonString { .. } => "FromJsonString",
        TermNode::ShiftThresholdLits { .. } => "ShiftThresholdLits",
        TermNode::DictGet { .. } => "DictGet",
        TermNode::RewriteTreeNodes { .. } => "RewriteTreeNodes",
        TermNode::AttrKeyRanking { .. } => "AttrKeyRanking",
        TermNode::TextShape { .. } => "TextShape",
        TermNode::FbFrameSeq { .. } => "FbFrameSeq",
        TermNode::ChangeDetect { .. } => "ChangeDetect",
        TermNode::TemporalDiff { .. } => "TemporalDiff",
        TermNode::Foveate { .. } => "Foveate",
        TermNode::StringConcat { .. } => "StringConcat",
        // Rung 1 Tier-1 stdlib Term ports.
        TermNode::Replace { .. } => "Replace",
        TermNode::Str { .. } => "Str",
        TermNode::Split { .. } => "Split",
        TermNode::StrCount { .. } => "StrCount",
        TermNode::Round { .. } => "Round",
        TermNode::Reverse { .. } => "Reverse",
        TermNode::IndexedMap { .. } => "IndexedMap",
        TermNode::Capitalize { .. } => "Capitalize",
        TermNode::ParseInt { .. } => "ParseInt",
        TermNode::Slice { .. } => "Slice",
        TermNode::Sort { .. } => "Sort",
        TermNode::DictItems { .. } => "DictItems",
        TermNode::SortBy { .. } => "SortBy",
        TermNode::GroupCount { .. } => "GroupCount",
        TermNode::DictMerge { .. } => "DictMerge",
        TermNode::ZipWith { .. } => "ZipWith",
        TermNode::Argmax { .. } => "Argmax",
        TermNode::Argmin { .. } => "Argmin",
        TermNode::ArgminUnique { .. } => "ArgminUnique",
        TermNode::ArgminRefusal { .. } => "ArgminRefusal",
        TermNode::Fold { .. } => "Fold",
        TermNode::BitsAt { .. } => "BitsAt",
        TermNode::BitsWrite { .. } => "BitsWrite",
        TermNode::BitsWriteAll { .. } => "BitsWriteAll",
        TermNode::BitsAtAll { .. } => "BitsAtAll",
        TermNode::HuffmanDecodeStream { .. } => "HuffmanDecodeStream",
        TermNode::HuffmanEncodeStream { .. } => "HuffmanEncodeStream",
        TermNode::ExpGolombDecode { .. } => "ExpGolombDecode",
        TermNode::ExpGolombDecodeSigned { .. } => "ExpGolombDecodeSigned",
        TermNode::ExpGolombEncode { .. } => "ExpGolombEncode",
        TermNode::ExpGolombEncodeSigned { .. } => "ExpGolombEncodeSigned",
        TermNode::Holds { .. } => "Holds",
        TermNode::EvalSubgraph { .. } => "EvalSubgraph",
        TermNode::And { .. } => "And",
        TermNode::Or { .. } => "Or",
        TermNode::Not { .. } => "Not",
        TermNode::Abs { .. } => "Abs",
        TermNode::Neg { .. } => "Neg",
        TermNode::Plus { .. } => "Plus",
        TermNode::Minus { .. } => "Minus",
        TermNode::Times { .. } => "Times",
        TermNode::Div { .. } => "Div",
        TermNode::DtwTo { .. } => "DtwTo",
        TermNode::ApcEncode { .. } => "ApcEncode",
        TermNode::PointSetDist { .. } => "PointSetDist",
        TermNode::MahalLeaf { .. } => "MahalLeaf",
        TermNode::MahalFull { .. } => "MahalFull",
        TermNode::DeformGenMarginal { .. } => "DeformGenMarginal",
        TermNode::DeformGen { .. } => "DeformGen",
        TermNode::DeformDist { .. } => "DeformDist",
        TermNode::SmoothDeformDist { .. } => "SmoothDeformDist",
        TermNode::TpsDeformDist { .. } => "TpsDeformDist",
        TermNode::SmoothDeformComponents { .. } => "SmoothDeformComponents",
        TermNode::ShapeContextDist { .. } => "ShapeContextDist",
        TermNode::EnclosedCount { .. } => "EnclosedCount",
        TermNode::ScTpsDist { .. } => "ScTpsDist",
        TermNode::BlendCover { .. } => "BlendCover",
        TermNode::XCorrPeak { .. } => "XCorrPeak",
        TermNode::Whiten { .. } => "Whiten",
        TermNode::WhitenMany { .. } => "WhitenMany",
        TermNode::WithinScatter { .. } => "WithinScatter",
        TermNode::BetweenScatter { .. } => "BetweenScatter",
        TermNode::Mod { .. } => "Mod",
        TermNode::Pow { .. } => "Pow",
        TermNode::BitAnd { .. } => "BitAnd",
        TermNode::BitOr  { .. } => "BitOr",
        TermNode::BitXor { .. } => "BitXor",
        TermNode::Shl  { .. } => "Shl",
        TermNode::Lshr { .. } => "Lshr",
        TermNode::Ashr { .. } => "Ashr",
        TermNode::IDiv { .. } => "IDiv",
        TermNode::IRem { .. } => "IRem",
        TermNode::Sqrt { .. } => "Sqrt",
        TermNode::Log { .. } => "Log",
        TermNode::Exp { .. } => "Exp",
        TermNode::Min { .. } => "Min",
        TermNode::Max { .. } => "Max",
        TermNode::ArgMax { .. } => "ArgMax",
        TermNode::IfThenElse { .. } => "IfThenElse",
        TermNode::Vec_ { .. } => "Vec",
        TermNode::VecAdd { .. } => "VecAdd",
        TermNode::VecSub { .. } => "VecSub",
        TermNode::Dot { .. } => "Dot",
        TermNode::Magnitude { .. } => "Magnitude",
        TermNode::Sin { .. } => "Sin",
        TermNode::Cos { .. } => "Cos",
        TermNode::Atan2 { .. } => "Atan2",
        TermNode::Bearing { .. } => "Bearing",
        TermNode::Rotate { .. } => "Rotate",
        TermNode::AngleBetween { .. } => "AngleBetween",
        TermNode::Surface { .. } => "Surface",
        TermNode::Cat { .. } => "Cat",
        TermNode::Slot { .. } => "Slot",
        TermNode::Join { .. } => "Join",
        TermNode::Bytes { .. } => "Bytes",
        TermNode::U8 { .. } => "U8",
        TermNode::U16LE { .. } => "U16LE",
        TermNode::U32LE { .. } => "U32LE",
        TermNode::U64LE { .. } => "U64LE",
        TermNode::LEB128 { .. } => "LEB128",
        TermNode::Lines { .. } => "Lines",
        TermNode::Label { .. } => "Label",
        TermNode::Let { .. } => "Let",
        TermNode::Nth { .. } => "Nth",
        TermNode::Render { .. } => "Render",
        TermNode::LitRepr { .. } => "LitRepr",
        // --- Phase 7 ext additions ---
        TermNode::Union { .. } => "Union",
        TermNode::Last { .. } => "Last",
        TermNode::IndexAt { .. } => "IndexAt",
        TermNode::Append { .. } => "Append",
        TermNode::ListDrop { .. } => "ListDrop",
        TermNode::Intersect { .. } => "Intersect",
        TermNode::Difference { .. } => "Difference",
        TermNode::MapSet { .. } => "MapSet",
        TermNode::MapList { .. } => "MapList",
        TermNode::Edges { .. } => "Edges",
        TermNode::EdgeAttr { .. } => "EdgeAttr",
        TermNode::NodesWhere { .. } => "NodesWhere",
        TermNode::NodesOfType { .. } => "NodesOfType",
        TermNode::AntiUnify { .. } => "AntiUnify",
        TermNode::FixedCount { .. } => "FixedCount",
        TermNode::Covers { .. } => "Covers",
        TermNode::CoversOpen { .. } => "CoversOpen",
        TermNode::AntiUnifyWitness { .. } => "AntiUnifyWitness",
        TermNode::Substitute { .. } => "Substitute",
        TermNode::Unify { .. } => "Unify",
        TermNode::StructSim { .. } => "StructSim",
        TermNode::ShapeDecode { .. } => "ShapeDecode",
        TermNode::MotorCompose { .. } => "MotorCompose",
        TermNode::TransformDecode { .. } => "TransformDecode",
        TermNode::NetForward { .. } => "NetForward",
        TermNode::DimInfer { .. } => "DimInfer",
        TermNode::GenInfer { .. } => "GenInfer",
        TermNode::TimeInfer { .. } => "TimeInfer",
        TermNode::DepthInfer { .. } => "DepthInfer",
        TermNode::BlinkBridge { .. } => "BlinkBridge",
        TermNode::GapAbduce { .. } => "GapAbduce",
        TermNode::GapVerify { .. } => "GapVerify",
        TermNode::SupportInfer { .. } => "SupportInfer",
        TermNode::MotionEnergy { .. } => "MotionEnergy",
        TermNode::TransferDecode { .. } => "TransferDecode",
        TermNode::RecogniseShape { .. } => "RecogniseShape",
        TermNode::MetaShapeMint { .. } => "MetaShapeMint",
        TermNode::StrokeQuantize { .. } => "StrokeQuantize",
        TermNode::StrokeRender { .. } => "StrokeRender",
        TermNode::SigmaLognormalGenerate { .. } => "SigmaLognormalGenerate",
        TermNode::LookaheadValue { .. } => "LookaheadValue",
        TermNode::ScalarAttrTriples { .. } => "ScalarAttrTriples",
        TermNode::AttrByName { .. } => "AttrByName",
        TermNode::ArgMin { .. } => "ArgMin",
        TermNode::TrackIdentityCorrespondence { .. } => "TrackIdentityCorrespondence",
        // --- Program IR (P1) ---
        TermNode::ProgSeq { .. } => "ProgSeq",
        TermNode::ProgAssignVar { .. } => "ProgAssignVar",
        TermNode::ProgAugAssign { .. } => "ProgAugAssign",
        TermNode::ProgTupleUnpack { .. } => "ProgTupleUnpack",
        TermNode::ProgIfStmt { .. } => "ProgIfStmt",
        TermNode::ProgForEach { .. } => "ProgForEach",
        TermNode::ProgWhile { .. } => "ProgWhile",
        TermNode::ProgLoopCtl { .. } => "ProgLoopCtl",
        TermNode::ProgReturn { .. } => "ProgReturn",
        TermNode::ProgTryOr { .. } => "ProgTryOr",
        TermNode::ProgRaise { .. } => "ProgRaise",
        TermNode::ProgImportStmt { .. } => "ProgImportStmt",
        TermNode::ProgSubscriptSet { .. } => "ProgSubscriptSet",
        TermNode::ProgAttrSet { .. } => "ProgAttrSet",
        TermNode::ProgDefFnParam { .. } => "ProgDefFnParam",
        TermNode::ProgCallExtern { .. } => "ProgCallExtern",
        TermNode::ProgAttrGet { .. } => "ProgAttrGet",
        TermNode::ProgSubscript { .. } => "ProgSubscript",
        TermNode::ProgSlice { .. } => "ProgSlice",
        TermNode::ProgContainerLit { .. } => "ProgContainerLit",
        TermNode::ProgComprehensionList { .. } => "ProgComprehensionList",
        TermNode::ProgComprehensionGen { .. } => "ProgComprehensionGen",
        TermNode::ProgIsOp { .. } => "ProgIsOp",
        TermNode::ProgFString { .. } => "ProgFString",
        TermNode::ProgEval { .. } => "ProgEval",
        TermNode::SnakeCase { .. } => "SnakeCase",
        TermNode::CaseFold { .. } => "CaseFold",
        TermNode::SynthEnumerate { .. } => "SynthEnumerate",
        TermNode::Call { .. } => "Call",
        TermNode::ParetoDominates { .. } => "ParetoDominates",
    }
}

fn sym_str(s: Sym, interner: &Interner) -> J {
    J::String(interner.resolve(s).to_string())
}

fn sym_or_null(s: Sym, any: bool, interner: &Interner) -> J {
    if any {
        J::Null
    } else {
        sym_str(s, interner)
    }
}

fn child(idx: TermIdx, arena: &TermArena, interner: &Interner) -> J {
    term_to_json(arena, idx, interner)
}

fn opt_child(idx: Option<TermIdx>, arena: &TermArena, interner: &Interner) -> J {
    match idx {
        Some(c) => term_to_json(arena, c, interner),
        None => J::Null,
    }
}

fn children(items: &[TermIdx], arena: &TermArena, interner: &Interner) -> J {
    J::Array(items.iter().map(|c| term_to_json(arena, *c, interner)).collect())
}

/// Emit the variant-specific fields onto `m`. Mirrors `describe` in
/// `reflect.rs` but produces the Python-flat JSON shape rather than
/// the typed-subgraph form.
fn write_fields(
    node: &TermNode,
    arena: &TermArena,
    interner: &Interner,
    m: &mut Map<String, J>,
) {
    match node {
        TermNode::Var { name } => {
            m.insert("name".into(), sym_str(*name, interner));
        }
        TermNode::Lit { value } => {
            // Lit's value is encoded verbatim — same encoding as
            // persistence so Set/Tuple/NodeID values keep their tags.
            m.insert("value".into(), encode_value(value, interner));
        }
        TermNode::TypeOf { node } => {
            m.insert("node".into(), child(*node, arena, interner));
        }
        TermNode::Attr { node, key } => {
            m.insert("node".into(), child(*node, arena, interner));
            m.insert("key".into(), sym_str(*key, interner));
        }
        TermNode::UseTool { tool, args } => {
            m.insert("tool".into(), sym_str(*tool, interner));
            m.insert("args".into(), children(args, arena, interner));
        }
        TermNode::SetT { items } => {
            m.insert("items".into(), children(items, arena, interner));
        }
        TermNode::In { member, container } => {
            m.insert("member".into(), child(*member, arena, interner));
            m.insert("container".into(), child(*container, arena, interner));
        }
        TermNode::Eq { a, b }
        | TermNode::Lt { a, b }
        | TermNode::Lte { a, b }
        | TermNode::Gt { a, b }
        | TermNode::Gte { a, b }
        | TermNode::Minus { a, b }
        | TermNode::Div { a, b }
        | TermNode::DtwTo { a, b }
        | TermNode::PointSetDist { a, b }
        | TermNode::MahalLeaf { a, b }
        | TermNode::MahalFull { a, b } | TermNode::DeformGenMarginal { a, b } | TermNode::DeformGen { a, b }
        | TermNode::DeformDist { a, b }
        | TermNode::SmoothDeformDist { a, b }
        | TermNode::TpsDeformDist { a, b }
        | TermNode::SmoothDeformComponents { a, b }
        | TermNode::ShapeContextDist { a, b }
        | TermNode::ScTpsDist { a, b }
        | TermNode::XCorrPeak { a, b }
        | TermNode::Whiten { a, b }
        | TermNode::WhitenMany { a, b }
        | TermNode::WithinScatter { a, b }
        | TermNode::BetweenScatter { a, b }
        | TermNode::Mod { a, b }
        | TermNode::Pow { a, b }
        | TermNode::VecAdd { a, b }
        | TermNode::VecSub { a, b }
        | TermNode::Dot { a, b }
        | TermNode::AngleBetween { a, b }
        | TermNode::BitAnd { a, b }
        | TermNode::BitOr { a, b }
        | TermNode::BitXor { a, b }
        | TermNode::Shl { a, b }
        | TermNode::Lshr { a, b }
        | TermNode::Ashr { a, b }
        | TermNode::IDiv { a, b }
        | TermNode::IRem { a, b } => {
            m.insert("a".into(), child(*a, arena, interner));
            m.insert("b".into(), child(*b, arena, interner));
        }
        TermNode::ReachableFrom { node, edge_type, any_type } => {
            m.insert("node".into(), child(*node, arena, interner));
            m.insert("edge_type".into(), sym_or_null(*edge_type, *any_type, interner));
        }

        TermNode::Neighbours { node, edge_type, any_type }
        | TermNode::InNeighbours { node, edge_type, any_type } => {
            m.insert("node".into(), child(*node, arena, interner));
            m.insert("edge_type".into(), sym_or_null(*edge_type, *any_type, interner));
        }
        TermNode::SlideNeighbours { cell, slide, ground } => {
            m.insert("cell".into(), child(*cell, arena, interner));
            m.insert("slide".into(), child(*slide, arena, interner));
            m.insert("ground".into(), child(*ground, arena, interner));
        }
        TermNode::MapNeighbours { source, edge_type, any_type } => {
            m.insert("source".into(), child(*source, arena, interner));
            m.insert("edge_type".into(), sym_or_null(*edge_type, *any_type, interner));
        }
        TermNode::Count { source } | TermNode::Pick { source }
            | TermNode::PickUnique { source } => {
            m.insert("source".into(), child(*source, arena, interner));
        }
        TermNode::Tokenize { text } => {
            m.insert("text".into(), child(*text, arena, interner));
        }
        TermNode::MorphHead { text } => {
            m.insert("text".into(), child(*text, arena, interner));
        }
        TermNode::MorphTail { text } => {
            m.insert("text".into(), child(*text, arena, interner));
        }
        TermNode::FinalToken { text } => {
            m.insert("text".into(), child(*text, arena, interner));
        }
        TermNode::Tokenize2 { text } => {
            m.insert("text".into(), child(*text, arena, interner));
        }
        TermNode::ReadFile { path } => {
            m.insert("path".into(), child(*path, arena, interner));
        }
        TermNode::StringIndexOf { haystack, needle } => {
            m.insert("haystack".into(), child(*haystack, arena, interner));
            m.insert("needle".into(), child(*needle, arena, interner));
        }
        TermNode::StringSlice { s, start, end } => {
            m.insert("s".into(), child(*s, arena, interner));
            m.insert("start".into(), child(*start, arena, interner));
            m.insert("end".into(), child(*end, arena, interner));
        }
        TermNode::BlendCover { unknown, a, b } => {
            m.insert("unknown".into(), child(*unknown, arena, interner));
            m.insert("a".into(), child(*a, arena, interner));
            m.insert("b".into(), child(*b, arena, interner));
        }
        TermNode::Verify { term, env, expected } => {
            m.insert("term".into(), child(*term, arena, interner));
            m.insert("env".into(), child(*env, arena, interner));
            m.insert("expected".into(), child(*expected, arena, interner));
        }
        TermNode::MkDict { items } => {
            m.insert("items".into(), children(items, arena, interner));
        }
        TermNode::ToJsonString { value } => {
            m.insert("value".into(), child(*value, arena, interner));
        }
        TermNode::FromJsonString { text } => {
            m.insert("text".into(), child(*text, arena, interner));
        }
        TermNode::ShiftThresholdLits { tree, shift } => {
            m.insert("tree".into(), child(*tree, arena, interner));
            m.insert("shift".into(), child(*shift, arena, interner));
        }
        TermNode::DictGet { dict, key } => {
            m.insert("dict".into(), child(*dict, arena, interner));
            m.insert("key".into(), child(*key, arena, interner));
        }
        TermNode::RewriteTreeNodes { tree, type_filter, field, value_map } => {
            m.insert("tree".into(), child(*tree, arena, interner));
            m.insert("type_filter".into(), opt_child(*type_filter, arena, interner));
            m.insert("field".into(), child(*field, arena, interner));
            m.insert("value_map".into(), child(*value_map, arena, interner));
        }
        TermNode::AttrKeyRanking { tree } => {
            m.insert("tree".into(), child(*tree, arena, interner));
        }
        TermNode::TextShape { text } => {
            m.insert("text".into(), child(*text, arena, interner));
        }
        TermNode::FbFrameSeq { fb } => {
            m.insert("fb".into(), child(*fb, arena, interner));
        }
        TermNode::ChangeDetect { image_vals, kernel_weights, dims } => {
            m.insert("image_vals".into(), child(*image_vals, arena, interner));
            m.insert("kernel_weights".into(), child(*kernel_weights, arena, interner));
            m.insert("dims".into(), child(*dims, arena, interner));
        }
        TermNode::TemporalDiff { a_vals, b_vals } => {
            m.insert("a_vals".into(), child(*a_vals, arena, interner));
            m.insert("b_vals".into(), child(*b_vals, arena, interner));
        }
        TermNode::Foveate { image_vals, dims, geometry } => {
            m.insert("image_vals".into(), child(*image_vals, arena, interner));
            m.insert("dims".into(), child(*dims, arena, interner));
            m.insert("geometry".into(), child(*geometry, arena, interner));
        }
        TermNode::StringConcat { parts } => {
            m.insert("parts".into(), J::Array(parts.iter().map(|c| child(*c, arena, interner)).collect()));
        }
        // Rung 1 Tier-1 stdlib Term ports.
        TermNode::Replace { text, old, new } => {
            m.insert("text".into(), child(*text, arena, interner));
            m.insert("old".into(), child(*old, arena, interner));
            m.insert("new".into(), child(*new, arena, interner));
        }
        TermNode::Str { value } => {
            m.insert("value".into(), child(*value, arena, interner));
        }
        TermNode::Split { text, sep } => {
            m.insert("text".into(), child(*text, arena, interner));
            m.insert("sep".into(), child(*sep, arena, interner));
        }
        TermNode::StrCount { text, sub } => {
            m.insert("text".into(), child(*text, arena, interner));
            m.insert("sub".into(), child(*sub, arena, interner));
        }
        TermNode::Round { value, ndigits } => {
            m.insert("value".into(), child(*value, arena, interner));
            m.insert("ndigits".into(), child(*ndigits, arena, interner));
        }
        TermNode::Reverse { seq } => {
            m.insert("seq".into(), child(*seq, arena, interner));
        }
        TermNode::IndexedMap { source, item_name, index_name, value } => {
            m.insert("source".into(), child(*source, arena, interner));
            m.insert("item_name".into(), sym_str(*item_name, interner));
            m.insert("index_name".into(), sym_str(*index_name, interner));
            m.insert("value".into(), child(*value, arena, interner));
        }
        TermNode::Capitalize { text } => {
            m.insert("text".into(), child(*text, arena, interner));
        }
        TermNode::ParseInt { text } => {
            m.insert("text".into(), child(*text, arena, interner));
        }
        TermNode::Slice { seq, start, stop } => {
            m.insert("seq".into(), child(*seq, arena, interner));
            m.insert("start".into(), child(*start, arena, interner));
            m.insert("stop".into(), child(*stop, arena, interner));
        }
        TermNode::Sort { seq } => {
            m.insert("seq".into(), child(*seq, arena, interner));
        }
        TermNode::DictItems { seq } => {
            m.insert("seq".into(), child(*seq, arena, interner));
        }
        TermNode::SortBy { source, var_name, key } => {
            m.insert("source".into(), child(*source, arena, interner));
            m.insert("var_name".into(), sym_str(*var_name, interner));
            m.insert("key".into(), child(*key, arena, interner));
        }
        TermNode::GroupCount { seq } => {
            m.insert("seq".into(), child(*seq, arena, interner));
        }
        TermNode::DictMerge { a, b } => {
            m.insert("a".into(), child(*a, arena, interner));
            m.insert("b".into(), child(*b, arena, interner));
        }
        TermNode::ZipWith { a, b, a_name, b_name, value } => {
            m.insert("a".into(), child(*a, arena, interner));
            m.insert("b".into(), child(*b, arena, interner));
            m.insert("a_name".into(), sym_str(*a_name, interner));
            m.insert("b_name".into(), sym_str(*b_name, interner));
            m.insert("value".into(), child(*value, arena, interner));
        }
        TermNode::Filter { source, var_name, predicate }
        | TermNode::FilterList { source, var_name, predicate }
        | TermNode::Exists { source, var_name, predicate } => {
            m.insert("source".into(), child(*source, arena, interner));
            m.insert("var_name".into(), sym_str(*var_name, interner));
            m.insert("predicate".into(), child(*predicate, arena, interner));
        }
        TermNode::Sum { source, var_name, value } | TermNode::Prod { source, var_name, value } => {
            m.insert("source".into(), child(*source, arena, interner));
            m.insert("var_name".into(), sym_str(*var_name, interner));
            m.insert("value".into(), child(*value, arena, interner));
        }
        TermNode::MinOver { source, var_name, value, default }
        | TermNode::MaxOver { source, var_name, value, default }
        | TermNode::Argmin { source, var_name, value, default }
        | TermNode::ArgminUnique { source, var_name, value, default }
        | TermNode::Argmax { source, var_name, value, default } => {
            m.insert("source".into(), child(*source, arena, interner));
            m.insert("var_name".into(), sym_str(*var_name, interner));
            m.insert("value".into(), child(*value, arena, interner));
            m.insert("default".into(), opt_child(*default, arena, interner));
        }
        TermNode::ArgminRefusal { source, var_name, value, refused } => {
            m.insert("source".into(), child(*source, arena, interner));
            m.insert("var_name".into(), sym_str(*var_name, interner));
            m.insert("value".into(), child(*value, arena, interner));
            m.insert("refused".into(), opt_child(*refused, arena, interner));
        }
        TermNode::Fold { source, var_name, acc_name, init, body } => {
            m.insert("source".into(), child(*source, arena, interner));
            m.insert("var_name".into(), sym_str(*var_name, interner));
            m.insert("acc_name".into(), sym_str(*acc_name, interner));
            m.insert("init".into(), child(*init, arena, interner));
            m.insert("body".into(), child(*body, arena, interner));
        }
        TermNode::Holds { concept, node, node2 } => {
            m.insert("concept".into(), sym_str(*concept, interner));
            m.insert("node".into(), opt_child(*node, arena, interner));
            m.insert("node2".into(), opt_child(*node2, arena, interner));
        }
        TermNode::BitsAt { buffer, bitpos, n_bits } => {
            m.insert("buffer".into(), child(*buffer, arena, interner));
            m.insert("bitpos".into(), child(*bitpos, arena, interner));
            m.insert("n_bits".into(), child(*n_bits, arena, interner));
        }
        TermNode::BitsWrite { buffer, bitpos, value, n_bits } => {
            m.insert("buffer".into(), child(*buffer, arena, interner));
            m.insert("bitpos".into(), child(*bitpos, arena, interner));
            m.insert("value".into(), child(*value, arena, interner));
            m.insert("n_bits".into(), child(*n_bits, arena, interner));
        }
        TermNode::BitsWriteAll { buffer, writes } => {
            m.insert("buffer".into(), child(*buffer, arena, interner));
            m.insert("writes".into(), child(*writes, arena, interner));
        }
        TermNode::BitsAtAll { buffer, reads } => {
            m.insert("buffer".into(), child(*buffer, arena, interner));
            m.insert("reads".into(), child(*reads, arena, interner));
        }
        TermNode::HuffmanDecodeStream { buffer, bitpos, table, n_pairs } => {
            m.insert("buffer".into(), child(*buffer, arena, interner));
            m.insert("bitpos".into(), child(*bitpos, arena, interner));
            m.insert("table".into(), child(*table, arena, interner));
            m.insert("n_pairs".into(), child(*n_pairs, arena, interner));
        }
        TermNode::HuffmanEncodeStream { buffer, bitpos, pairs, table } => {
            m.insert("buffer".into(), child(*buffer, arena, interner));
            m.insert("bitpos".into(), child(*bitpos, arena, interner));
            m.insert("pairs".into(), child(*pairs, arena, interner));
            m.insert("table".into(), child(*table, arena, interner));
        }
        TermNode::ExpGolombDecode { buffer, bitpos }
        | TermNode::ExpGolombDecodeSigned { buffer, bitpos } => {
            m.insert("buffer".into(), child(*buffer, arena, interner));
            m.insert("bitpos".into(), child(*bitpos, arena, interner));
        }
        TermNode::ExpGolombEncode { buffer, bitpos, value }
        | TermNode::ExpGolombEncodeSigned { buffer, bitpos, value } => {
            m.insert("buffer".into(), child(*buffer, arena, interner));
            m.insert("bitpos".into(), child(*bitpos, arena, interner));
            m.insert("value".into(), child(*value, arena, interner));
        }
        TermNode::EvalSubgraph { node } => {
            m.insert("node".into(), child(*node, arena, interner));
        }
        TermNode::And { items } | TermNode::Or { items }
        | TermNode::Plus { items } | TermNode::Times { items }
        | TermNode::Min { items } | TermNode::Max { items } | TermNode::ArgMax { items } | TermNode::ArgMin { items }
        | TermNode::Vec_ { items } | TermNode::Cat { items }
        | TermNode::Bytes { items } | TermNode::Lines { items } => {
            m.insert("items".into(), children(items, arena, interner));
        }
        TermNode::Not { arg } | TermNode::Abs { arg } | TermNode::Neg { arg }
        | TermNode::EnclosedCount { arg }
        | TermNode::Sqrt { arg } | TermNode::Log { arg } | TermNode::Exp { arg }
        | TermNode::Magnitude { arg }
        | TermNode::Sin { arg } | TermNode::Cos { arg } | TermNode::Bearing { arg } => {
            m.insert("arg".into(), child(*arg, arena, interner));
        }
        TermNode::IfThenElse { cond, then, other } => {
            m.insert("cond".into(), child(*cond, arena, interner));
            m.insert("then".into(), child(*then, arena, interner));
            m.insert("other".into(), child(*other, arena, interner));
        }
        TermNode::ApcEncode { model, seq, start, end, out_len } => {
            m.insert("model".into(), child(*model, arena, interner));
            m.insert("seq".into(), child(*seq, arena, interner));
            m.insert("start".into(), child(*start, arena, interner));
            m.insert("end".into(), child(*end, arena, interner));
            m.insert("out_len".into(), child(*out_len, arena, interner));
        }
        TermNode::Atan2 { y, x } => {
            m.insert("y".into(), child(*y, arena, interner));
            m.insert("x".into(), child(*x, arena, interner));
        }
        TermNode::Rotate { vec, angle } => {
            m.insert("vec".into(), child(*vec, arena, interner));
            m.insert("angle".into(), child(*angle, arena, interner));
        }
        TermNode::Surface { kind, payload } => {
            m.insert(
                "kind".into(),
                J::String(match kind {
                    SurfaceKind::Text => "text".into(),
                    SurfaceKind::Bytes => "bytes".into(),
                }),
            );
            m.insert("payload".into(), encode_value(payload, interner));
        }
        TermNode::Slot { name } | TermNode::Label { prefix: name } => {
            // Label uses `prefix` in JSON shape to match Python.
            let key = match node {
                TermNode::Label { .. } => "prefix",
                _ => "name",
            };
            m.insert(key.into(), sym_str(*name, interner));
        }
        TermNode::Join { separator, items } => {
            m.insert("separator".into(), opt_child(*separator, arena, interner));
            m.insert("items".into(), opt_child(*items, arena, interner));
        }
        TermNode::U8 { expr } | TermNode::U16LE { expr } | TermNode::U32LE { expr }
        | TermNode::U64LE { expr } | TermNode::LEB128 { expr } => {
            m.insert("expr".into(), opt_child(*expr, arena, interner));
        }
        TermNode::Let { name, value, body } => {
            m.insert("name".into(), sym_str(*name, interner));
            m.insert("value".into(), opt_child(*value, arena, interner));
            m.insert("body".into(), opt_child(*body, arena, interner));
        }
        TermNode::Nth { items, index } => {
            m.insert("items".into(), opt_child(*items, arena, interner));
            m.insert("index".into(), J::Number((*index).into()));
        }
        TermNode::Render { term, lang } => {
            m.insert("term".into(), opt_child(*term, arena, interner));
            m.insert("lang".into(), opt_child(*lang, arena, interner));
        }
        TermNode::LitRepr { value } => {
            m.insert("value".into(), opt_child(*value, arena, interner));
        }
        // --- Phase 7 ext additions ---
        TermNode::Last { seq } => {
            m.insert("seq".into(), child(*seq, arena, interner));
        }
        TermNode::IndexAt { seq, index } => {
            m.insert("seq".into(), child(*seq, arena, interner));
            m.insert("index".into(), child(*index, arena, interner));
        }
        TermNode::Append { seq, item } => {
            m.insert("seq".into(), child(*seq, arena, interner));
            m.insert("item".into(), child(*item, arena, interner));
        }
        TermNode::ListDrop { list, index } => {
            m.insert("list".into(), child(*list, arena, interner));
            m.insert("index".into(), child(*index, arena, interner));
        }
        TermNode::Union { a, b } | TermNode::Intersect { a, b } | TermNode::Difference { a, b } => {
            m.insert("a".into(), child(*a, arena, interner));
            m.insert("b".into(), child(*b, arena, interner));
        }
        TermNode::MapSet { source, var_name, value }
        | TermNode::MapList { source, var_name, value } => {
            m.insert("source".into(), child(*source, arena, interner));
            m.insert("var_name".into(), sym_str(*var_name, interner));
            m.insert("value".into(), child(*value, arena, interner));
        }
        TermNode::Edges { node, edge_type, any_type } => {
            m.insert("node".into(), child(*node, arena, interner));
            m.insert("edge_type".into(), sym_or_null(*edge_type, *any_type, interner));
        }
        TermNode::EdgeAttr { edge, key } => {
            m.insert("edge".into(), child(*edge, arena, interner));
            m.insert("key".into(), sym_str(*key, interner));
        }
        TermNode::NodesWhere { node_type, attr_key, value } => {
            m.insert("node_type".into(), sym_str(*node_type, interner));
            m.insert("attr_key".into(), sym_str(*attr_key, interner));
            m.insert("value".into(), child(*value, arena, interner));
        }
        TermNode::NodesOfType { node_type } => {
            m.insert("node_type".into(), sym_str(*node_type, interner));
        }
        TermNode::AntiUnify { values, .. } => {
            // `wild` is a fixed sentinel re-derived on parse — not emitted.
            m.insert("values".into(), child(*values, arena, interner));
        }
        TermNode::FixedCount { pattern, .. } => {
            m.insert("pattern".into(), child(*pattern, arena, interner));
        }
        TermNode::Covers { pattern, instance, .. } => {
            m.insert("pattern".into(), child(*pattern, arena, interner));
            m.insert("instance".into(), child(*instance, arena, interner));
        }
        TermNode::CoversOpen { pattern, instance, .. } => {
            m.insert("pattern".into(), child(*pattern, arena, interner));
            m.insert("instance".into(), child(*instance, arena, interner));
        }
        TermNode::AntiUnifyWitness { values, .. } => {
            // `wild` is a fixed sentinel re-derived on parse — not emitted.
            m.insert("values".into(), child(*values, arena, interner));
        }
        TermNode::Substitute { template, sigma, .. } => {
            m.insert("template".into(), child(*template, arena, interner));
            m.insert("sigma".into(), child(*sigma, arena, interner));
        }
        TermNode::Unify { values, .. } => {
            // `wild` is a fixed sentinel re-derived on parse — not emitted.
            m.insert("values".into(), child(*values, arena, interner));
        }
        TermNode::StructSim { a, b, .. } => {
            m.insert("a".into(), child(*a, arena, interner));
            m.insert("b".into(), child(*b, arena, interner));
        }
        TermNode::ShapeDecode { goal, codebook_type, exclude, codebook_scope, beam, max_steps, cand_k, budget, field, wild_objects, .. } => {
            // `wild` is a fixed sentinel re-derived on parse — not emitted.
            m.insert("goal".into(), child(*goal, arena, interner));
            m.insert("codebook_type".into(), sym_str(*codebook_type, interner));
            m.insert("exclude".into(), opt_child(*exclude, arena, interner));
            m.insert("codebook_scope".into(), opt_child(*codebook_scope, arena, interner));
            m.insert("beam".into(), J::Number((*beam).into()));
            m.insert("max_steps".into(), J::Number((*max_steps).into()));
            m.insert("cand_k".into(), J::Number((*cand_k).into()));
            m.insert("budget".into(), J::Number((*budget).into()));
            m.insert("field".into(), sym_str(*field, interner));
            m.insert("wild_objects".into(), J::Bool(*wild_objects));
        }
        TermNode::MotorCompose { episode, policy, candidate } => {
            m.insert("episode".into(), child(*episode, arena, interner));
            m.insert("policy".into(), child(*policy, arena, interner));
            m.insert("candidate".into(), child(*candidate, arena, interner));
        }
        TermNode::TransformDecode { goal, codebook_type, exclude, max_dims, field } => {
            m.insert("goal".into(), child(*goal, arena, interner));
            m.insert("codebook_type".into(), sym_str(*codebook_type, interner));
            m.insert("exclude".into(), opt_child(*exclude, arena, interner));
            m.insert("max_dims".into(), J::Number((*max_dims).into()));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::NetForward { assemblage, inputs } => {
            m.insert("assemblage".into(), child(*assemblage, arena, interner));
            m.insert("inputs".into(), child(*inputs, arena, interner));
        }
        TermNode::DimInfer { goal, codebook_type, exclude, generator_type, max_dims, field } => {
            m.insert("goal".into(), child(*goal, arena, interner));
            m.insert("codebook_type".into(), sym_str(*codebook_type, interner));
            m.insert("exclude".into(), opt_child(*exclude, arena, interner));
            m.insert("generator_type".into(), sym_str(*generator_type, interner));
            m.insert("max_dims".into(), J::Number((*max_dims).into()));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::GenInfer { goal, codebook_type, exclude, max_dims, field } => {
            m.insert("goal".into(), child(*goal, arena, interner));
            m.insert("codebook_type".into(), sym_str(*codebook_type, interner));
            m.insert("exclude".into(), opt_child(*exclude, arena, interner));
            m.insert("max_dims".into(), J::Number((*max_dims).into()));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::TimeInfer { sequence, codebook_type, max_b, field, max_steps, robust } => {
            m.insert("sequence".into(), child(*sequence, arena, interner));
            m.insert("codebook_type".into(), sym_str(*codebook_type, interner));
            m.insert("max_b".into(), J::Number((*max_b).into()));
            m.insert("field".into(), sym_str(*field, interner));
            // Omit the defaults so existing serialized terms are byte-
            // identical; only a term that sets them carries the keys.
            if *max_steps != DEFAULT_TIME_INFER_MAX_STEPS {
                m.insert("max_steps".into(), J::Number((*max_steps).into()));
            }
            if *robust { m.insert("robust".into(), J::Bool(true)); }
        }
        TermNode::DepthInfer { sequence, codebook_type, max_b, field } => {
            m.insert("sequence".into(), child(*sequence, arena, interner));
            m.insert("codebook_type".into(), sym_str(*codebook_type, interner));
            m.insert("max_b".into(), J::Number((*max_b).into()));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::BlinkBridge { sequence, codebook_type, max_b, field } => {
            m.insert("sequence".into(), child(*sequence, arena, interner));
            m.insert("codebook_type".into(), sym_str(*codebook_type, interner));
            m.insert("max_b".into(), J::Number((*max_b).into()));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::GapAbduce { sequence, codebook_type, max_b, field } => {
            m.insert("sequence".into(), child(*sequence, arena, interner));
            m.insert("codebook_type".into(), sym_str(*codebook_type, interner));
            m.insert("max_b".into(), J::Number((*max_b).into()));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::GapVerify { sequence, codebook_type, max_b, field } => {
            m.insert("sequence".into(), child(*sequence, arena, interner));
            m.insert("codebook_type".into(), sym_str(*codebook_type, interner));
            m.insert("max_b".into(), J::Number((*max_b).into()));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::SupportInfer { sequence, codebook_type, field } => {
            m.insert("sequence".into(), child(*sequence, arena, interner));
            m.insert("codebook_type".into(), sym_str(*codebook_type, interner));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::MotionEnergy { sequence, height, width, field } => {
            m.insert("sequence".into(), child(*sequence, arena, interner));
            m.insert("height".into(), J::Number((*height).into()));
            m.insert("width".into(), J::Number((*width).into()));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::TransferDecode { goal } => {
            m.insert("goal".into(), child(*goal, arena, interner));
        }
        TermNode::RecogniseShape { text } => {
            m.insert("text".into(), child(*text, arena, interner));
        }
        TermNode::MetaShapeMint { observation, obs_type, status_value, wild, field } => {
            m.insert("observation".into(), child(*observation, arena, interner));
            m.insert("obs_type".into(), sym_str(*obs_type, interner));
            m.insert("status_value".into(), sym_str(*status_value, interner));
            m.insert("wild".into(), sym_str(*wild, interner));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::StrokeQuantize {
            points, segments, turn_bins, len_bins, grid, scale_bins, invariant_only, canonical_pose,
            turn_edges, len_edges, emit_residual,
            bounds, field, ..
        } => {
            // `seg_sym`/`pose_*_sym` are fixed sentinels re-derived on
            // parse (interned fresh from the literal predicate strings)
            // — not emitted, same convention as `AntiUnify`'s `wild`.
            m.insert("points".into(), child(*points, arena, interner));
            m.insert("segments".into(), J::Number((*segments).into()));
            m.insert("turn_bins".into(), J::Number((*turn_bins).into()));
            m.insert("len_bins".into(), J::Number((*len_bins).into()));
            m.insert("grid".into(), J::Number((*grid).into()));
            m.insert("scale_bins".into(), J::Number((*scale_bins).into()));
            m.insert("invariant_only".into(), J::Bool(*invariant_only));
            m.insert("canonical_pose".into(), J::Bool(*canonical_pose));
            m.insert("turn_edges".into(), opt_child(*turn_edges, arena, interner));
            m.insert("len_edges".into(), opt_child(*len_edges, arena, interner));
            m.insert("emit_residual".into(), J::Bool(*emit_residual));
            m.insert("bounds".into(), opt_child(*bounds, arena, interner));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::StrokeRender {
            signature, n_points, apply_pose, turn_bins, len_bins, grid, scale_bins,
            turn_edges, len_edges, bounds, field,
        } => {
            // No sentinel Syms to omit here (contrast StrokeQuantize):
            // StrokeRender never emits a relation predicate, so it never
            // needed any pre-interned Sym fields in the first place.
            m.insert("signature".into(), child(*signature, arena, interner));
            m.insert("n_points".into(), J::Number((*n_points).into()));
            m.insert("apply_pose".into(), J::Bool(*apply_pose));
            m.insert("turn_bins".into(), J::Number((*turn_bins).into()));
            m.insert("len_bins".into(), J::Number((*len_bins).into()));
            m.insert("grid".into(), J::Number((*grid).into()));
            m.insert("scale_bins".into(), J::Number((*scale_bins).into()));
            m.insert("turn_edges".into(), opt_child(*turn_edges, arena, interner));
            m.insert("len_edges".into(), opt_child(*len_edges, arena, interner));
            m.insert("bounds".into(), opt_child(*bounds, arena, interner));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::SigmaLognormalGenerate { primitives, start, t_start, t_end, n_points, field } => {
            m.insert("primitives".into(), child(*primitives, arena, interner));
            m.insert("start".into(), child(*start, arena, interner));
            m.insert("t_start".into(), J::from(*t_start));
            m.insert("t_end".into(), J::from(*t_end));
            m.insert("n_points".into(), J::Number((*n_points).into()));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::LookaheadValue { node, child_edge, score_key, depth } => {
            m.insert("node".into(), child(*node, arena, interner));
            m.insert("child_edge".into(), sym_str(*child_edge, interner));
            m.insert("score_key".into(), sym_str(*score_key, interner));
            m.insert("depth".into(), child(*depth, arena, interner));
        }
        TermNode::ScalarAttrTriples { skip_prefix } => {
            m.insert("skip_prefix".into(), sym_str(*skip_prefix, interner));
        }
        TermNode::AttrByName { node, name } => {
            m.insert("node".into(), child(*node, arena, interner));
            m.insert("name".into(), child(*name, arena, interner));
        }
        TermNode::TrackIdentityCorrespondence { prev, cur, feature_key, category_key, extent_key, radius } => {
            m.insert("prev".into(), child(*prev, arena, interner));
            m.insert("cur".into(), child(*cur, arena, interner));
            m.insert("feature_key".into(), sym_str(*feature_key, interner));
            m.insert("category_key".into(), sym_opt_json(*category_key, interner));
            m.insert("extent_key".into(), sym_opt_json(*extent_key, interner));
            m.insert("radius".into(), child(*radius, arena, interner));
        }
        // --- Program IR (P1). Identifier lists emit as JSON arrays of
        // strings; optional Sym sentinels (Sym::default()) emit as "".
        TermNode::ProgSeq { stmts } => {
            m.insert("stmts".into(), J::Array(stmts.iter().map(|c| child(*c, arena, interner)).collect()));
        }
        TermNode::ProgAssignVar { name, value } => {
            m.insert("name".into(), sym_str(*name, interner));
            m.insert("value".into(), child(*value, arena, interner));
        }
        TermNode::ProgAugAssign { name, op, value } => {
            m.insert("name".into(), sym_str(*name, interner));
            m.insert("op".into(), sym_str(*op, interner));
            m.insert("value".into(), child(*value, arena, interner));
        }
        TermNode::ProgTupleUnpack { targets, value } => {
            m.insert(
                "targets".into(),
                J::Array(targets.iter().map(|t| sym_str(*t, interner)).collect()),
            );
            m.insert("value".into(), child(*value, arena, interner));
        }
        TermNode::ProgIfStmt { cond, then, orelse } => {
            m.insert("cond".into(), child(*cond, arena, interner));
            m.insert("then".into(), child(*then, arena, interner));
            m.insert("orelse".into(), opt_child(*orelse, arena, interner));
        }
        TermNode::ProgForEach { var, iter, body, orelse } => {
            m.insert("var".into(), sym_str(*var, interner));
            m.insert("iter".into(), child(*iter, arena, interner));
            m.insert("body".into(), child(*body, arena, interner));
            m.insert("orelse".into(), opt_child(*orelse, arena, interner));
        }
        TermNode::ProgWhile { cond, body, orelse } => {
            m.insert("cond".into(), child(*cond, arena, interner));
            m.insert("body".into(), child(*body, arena, interner));
            m.insert("orelse".into(), opt_child(*orelse, arena, interner));
        }
        TermNode::ProgLoopCtl { kind } => {
            m.insert("kind".into(), sym_str(*kind, interner));
        }
        TermNode::ProgReturn { value } => {
            m.insert("value".into(), opt_child(*value, arena, interner));
        }
        TermNode::ProgTryOr { body, exc_var, handler } => {
            m.insert("body".into(), child(*body, arena, interner));
            m.insert("exc_var".into(), sym_str(*exc_var, interner));
            m.insert("handler".into(), opt_child(*handler, arena, interner));
        }
        TermNode::ProgRaise { exc } => {
            m.insert("exc".into(), opt_child(*exc, arena, interner));
        }
        TermNode::ProgImportStmt { module, alias, names } => {
            m.insert("module".into(), sym_str(*module, interner));
            m.insert("alias".into(), sym_str(*alias, interner));
            m.insert(
                "names".into(),
                J::Array(names.iter().map(|n| sym_str(*n, interner)).collect()),
            );
        }
        TermNode::ProgSubscriptSet { obj, index, value } => {
            m.insert("obj".into(), child(*obj, arena, interner));
            m.insert("index".into(), child(*index, arena, interner));
            m.insert("value".into(), child(*value, arena, interner));
        }
        TermNode::ProgAttrSet { obj, attr, value } => {
            m.insert("obj".into(), child(*obj, arena, interner));
            m.insert("attr".into(), sym_str(*attr, interner));
            m.insert("value".into(), child(*value, arena, interner));
        }
        TermNode::ProgDefFnParam { name, default } => {
            m.insert("name".into(), sym_str(*name, interner));
            m.insert("default".into(), opt_child(*default, arena, interner));
        }
        TermNode::ProgCallExtern { name, recv, args } => {
            m.insert("name".into(), sym_str(*name, interner));
            m.insert("recv".into(), opt_child(*recv, arena, interner));
            m.insert("args".into(), J::Array(args.iter().map(|c| child(*c, arena, interner)).collect()));
        }
        TermNode::ProgAttrGet { obj, attr } => {
            m.insert("obj".into(), child(*obj, arena, interner));
            m.insert("attr".into(), sym_str(*attr, interner));
        }
        TermNode::ProgSubscript { obj, index } => {
            m.insert("obj".into(), child(*obj, arena, interner));
            m.insert("index".into(), child(*index, arena, interner));
        }
        TermNode::ProgSlice { obj, start, stop, step } => {
            m.insert("obj".into(), child(*obj, arena, interner));
            m.insert("start".into(), opt_child(*start, arena, interner));
            m.insert("stop".into(), opt_child(*stop, arena, interner));
            m.insert("step".into(), opt_child(*step, arena, interner));
        }
        TermNode::ProgContainerLit { kind, items } => {
            m.insert("kind".into(), sym_str(*kind, interner));
            m.insert("items".into(), J::Array(items.iter().map(|c| child(*c, arena, interner)).collect()));
        }
        TermNode::ProgComprehensionList { var, source, expr, cond }
        | TermNode::ProgComprehensionGen { var, source, expr, cond } => {
            m.insert("var".into(), sym_str(*var, interner));
            m.insert("source".into(), child(*source, arena, interner));
            m.insert("expr".into(), child(*expr, arena, interner));
            m.insert("cond".into(), opt_child(*cond, arena, interner));
        }
        TermNode::ProgIsOp { a, b, negated } => {
            m.insert("a".into(), child(*a, arena, interner));
            m.insert("b".into(), child(*b, arena, interner));
            m.insert("negated".into(), J::Bool(*negated));
        }
        TermNode::ProgFString { parts } => {
            m.insert("parts".into(), J::Array(parts.iter().map(|c| child(*c, arena, interner)).collect()));
        }
        TermNode::ProgEval { prog, env, oracles, fuel, field } => {
            m.insert("prog".into(), child(*prog, arena, interner));
            m.insert("env".into(), opt_child(*env, arena, interner));
            m.insert("oracles".into(), opt_child(*oracles, arena, interner));
            m.insert("fuel".into(), J::Number(serde_json::Number::from(*fuel)));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::SnakeCase { text } => {
            m.insert("text".into(), child(*text, arena, interner));
        }
        TermNode::CaseFold { text } => {
            m.insert("text".into(), child(*text, arena, interner));
        }
        TermNode::SynthEnumerate { examples, ops, consts, exclude, derived_ops, exclude_ops, max_size, max_candidates, saturate_k, field } => {
            m.insert("examples".into(), child(*examples, arena, interner));
            m.insert("ops".into(), opt_child(*ops, arena, interner));
            m.insert("consts".into(), opt_child(*consts, arena, interner));
            m.insert("exclude".into(), opt_child(*exclude, arena, interner));
            m.insert("derived_ops".into(), opt_child(*derived_ops, arena, interner));
            m.insert("exclude_ops".into(), opt_child(*exclude_ops, arena, interner));
            m.insert("max_size".into(), J::Number(serde_json::Number::from(*max_size)));
            m.insert("max_candidates".into(), J::Number(serde_json::Number::from(*max_candidates)));
            m.insert("saturate_k".into(), J::Number(serde_json::Number::from(*saturate_k)));
            m.insert("field".into(), sym_str(*field, interner));
        }
        TermNode::Call { name, args } => {
            m.insert("name".into(), sym_str(*name, interner));
            m.insert("args".into(), children(args, arena, interner));
        }
        TermNode::ParetoDominates {
            candidate, alternative, dimension_count, value_edge, measure_edge,
            dimension_key, verified_key, signed_value_key,
        } => {
            m.insert("candidate".into(), child(*candidate, arena, interner));
            m.insert("alternative".into(), child(*alternative, arena, interner));
            m.insert("dimension_count".into(), child(*dimension_count, arena, interner));
            m.insert("value_edge".into(), sym_str(*value_edge, interner));
            m.insert("measure_edge".into(), sym_str(*measure_edge, interner));
            m.insert("dimension_key".into(), sym_str(*dimension_key, interner));
            m.insert("verified_key".into(), sym_str(*verified_key, interner));
            m.insert("signed_value_key".into(), sym_str(*signed_value_key, interner));
        }
    }
}

/// JSON for an `Option<Sym>` field: `null` when absent, else the
/// resolved string — the Sym-field twin of `opt_child`'s Option<TermIdx>.
fn sym_opt_json(s: Option<Sym>, interner: &Interner) -> J {
    match s {
        Some(sym) => sym_str(sym, interner),
        None => J::Null,
    }
}

fn read_term(
    variant: &str,
    obj: &Map<String, J>,
    arena: &mut TermArena,
    interner: &mut Interner,
) -> Result<TermIdx, JsonError> {
    let get_str = |field: &str| -> Result<String, JsonError> {
        obj.get(field)
            .and_then(|v| v.as_str())
            .map(String::from)
            .ok_or(JsonError::MissingField {
                variant: variant.to_string(),
                field: field.to_string(),
            })
    };
    let get_str_or_empty = |field: &str| -> String {
        obj.get(field)
            .and_then(|v| v.as_str())
            .map(String::from)
            .unwrap_or_default()
    };
    let get_sym = |field: &str, i: &mut Interner| -> Result<Sym, JsonError> {
        Ok(i.intern(&get_str(field)?))
    };
    let get_optional_sym = |field: &str, i: &mut Interner| -> Sym {
        match obj.get(field) {
            Some(J::String(s)) => i.intern(s),
            _ => Sym::default(),
        }
    };
    let get_value = |field: &str, i: &mut Interner| -> Value {
        match obj.get(field) {
            Some(v) => decode_value(v, i),
            None => Value::None,
        }
    };
    let get_int = |field: &str| -> i64 {
        obj.get(field)
            .and_then(|v| v.as_i64())
            .unwrap_or(0)
    };

    fn child_of(
        field: &str,
        obj: &Map<String, J>,
        arena: &mut TermArena,
        interner: &mut Interner,
        variant: &str,
    ) -> Result<TermIdx, JsonError> {
        let v = obj
            .get(field)
            .ok_or(JsonError::MissingField {
                variant: variant.to_string(),
                field: field.to_string(),
            })?;
        term_from_json(v, arena, interner)
    }
    fn opt_child_of(
        field: &str,
        obj: &Map<String, J>,
        arena: &mut TermArena,
        interner: &mut Interner,
    ) -> Result<Option<TermIdx>, JsonError> {
        match obj.get(field) {
            None | Some(J::Null) => Ok(None),
            Some(v) => Ok(Some(term_from_json(v, arena, interner)?)),
        }
    }
    fn children_of(
        field: &str,
        obj: &Map<String, J>,
        arena: &mut TermArena,
        interner: &mut Interner,
    ) -> Result<Vec<TermIdx>, JsonError> {
        match obj.get(field) {
            Some(J::Array(items)) => items
                .iter()
                .map(|x| term_from_json(x, arena, interner))
                .collect(),
            _ => Ok(Vec::new()),
        }
    }
    /// Identifier-list field (Program IR `targets`/`names`): a JSON
    /// array of strings, each interned HERE (the parse-time path).
    fn sym_array_of(field: &str, obj: &Map<String, J>, interner: &mut Interner) -> Vec<Sym> {
        match obj.get(field) {
            Some(J::Array(items)) => items
                .iter()
                .filter_map(|x| x.as_str())
                .map(|s| interner.intern(s))
                .collect(),
            _ => Vec::new(),
        }
    }

    let node = match variant {
        "Var" => TermNode::Var { name: get_sym("name", interner)? },
        "Lit" => TermNode::Lit { value: get_value("value", interner) },
        "TypeOf" => TermNode::TypeOf { node: child_of("node", obj, arena, interner, variant)? },
        "Attr" => TermNode::Attr {
            node: child_of("node", obj, arena, interner, variant)?,
            key: get_sym("key", interner)?,
        },
        "UseTool" => TermNode::UseTool {
            tool: get_sym("tool", interner)?,
            args: children_of("args", obj, arena, interner)?,
        },
        "SetT" => TermNode::SetT { items: children_of("items", obj, arena, interner)? },
        "In" => TermNode::In {
            member: child_of("member", obj, arena, interner, variant)?,
            container: child_of("container", obj, arena, interner, variant)?,
        },
        "Tokenize" => TermNode::Tokenize {
            text: child_of("text", obj, arena, interner, variant)?,
        },
        "MorphHead" => TermNode::MorphHead {
            text: child_of("text", obj, arena, interner, variant)?,
        },
        "MorphTail" => TermNode::MorphTail {
            text: child_of("text", obj, arena, interner, variant)?,
        },
        "FinalToken" => TermNode::FinalToken {
            text: child_of("text", obj, arena, interner, variant)?,
        },
        "Tokenize2" => TermNode::Tokenize2 {
            text: child_of("text", obj, arena, interner, variant)?,
        },
        "ReadFile" => TermNode::ReadFile {
            path: child_of("path", obj, arena, interner, variant)?,
        },
        "StringIndexOf" => TermNode::StringIndexOf {
            haystack: child_of("haystack", obj, arena, interner, variant)?,
            needle: child_of("needle", obj, arena, interner, variant)?,
        },
        "StringSlice" => TermNode::StringSlice {
            s: child_of("s", obj, arena, interner, variant)?,
            start: child_of("start", obj, arena, interner, variant)?,
            end: child_of("end", obj, arena, interner, variant)?,
        },
        "Verify" => TermNode::Verify {
            term: child_of("term", obj, arena, interner, variant)?,
            env: child_of("env", obj, arena, interner, variant)?,
            expected: child_of("expected", obj, arena, interner, variant)?,
        },
        "MkDict" => TermNode::MkDict { items: children_of("items", obj, arena, interner)? },
        "ToJsonString" => TermNode::ToJsonString {
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "FromJsonString" => TermNode::FromJsonString {
            text: child_of("text", obj, arena, interner, variant)?,
        },
        "ShiftThresholdLits" => TermNode::ShiftThresholdLits {
            tree: child_of("tree", obj, arena, interner, variant)?,
            shift: child_of("shift", obj, arena, interner, variant)?,
        },
        "DictGet" => TermNode::DictGet {
            dict: child_of("dict", obj, arena, interner, variant)?,
            key: child_of("key", obj, arena, interner, variant)?,
        },
        "RewriteTreeNodes" => TermNode::RewriteTreeNodes {
            tree: child_of("tree", obj, arena, interner, variant)?,
            type_filter: opt_child_of("type_filter", obj, arena, interner)?,
            field: child_of("field", obj, arena, interner, variant)?,
            value_map: child_of("value_map", obj, arena, interner, variant)?,
        },
        "AttrKeyRanking" => TermNode::AttrKeyRanking {
            tree: child_of("tree", obj, arena, interner, variant)?,
        },
        "TextShape" => TermNode::TextShape {
            text: child_of("text", obj, arena, interner, variant)?,
        },
        "FbFrameSeq" => TermNode::FbFrameSeq {
            fb: child_of("fb", obj, arena, interner, variant)?,
        },
        "ChangeDetect" => TermNode::ChangeDetect {
            image_vals: child_of("image_vals", obj, arena, interner, variant)?,
            kernel_weights: child_of("kernel_weights", obj, arena, interner, variant)?,
            dims: child_of("dims", obj, arena, interner, variant)?,
        },
        "TemporalDiff" => TermNode::TemporalDiff {
            a_vals: child_of("a_vals", obj, arena, interner, variant)?,
            b_vals: child_of("b_vals", obj, arena, interner, variant)?,
        },
        "Foveate" => TermNode::Foveate {
            image_vals: child_of("image_vals", obj, arena, interner, variant)?,
            dims: child_of("dims", obj, arena, interner, variant)?,
            geometry: child_of("geometry", obj, arena, interner, variant)?,
        },
        "StringConcat" => TermNode::StringConcat {
            parts: children_of("parts", obj, arena, interner)?,
        },
        // Rung 1 Tier-1 stdlib Term ports.
        "Replace" => TermNode::Replace {
            text: child_of("text", obj, arena, interner, variant)?,
            old: child_of("old", obj, arena, interner, variant)?,
            new: child_of("new", obj, arena, interner, variant)?,
        },
        "Str" => TermNode::Str {
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "Split" => TermNode::Split {
            text: child_of("text", obj, arena, interner, variant)?,
            sep: child_of("sep", obj, arena, interner, variant)?,
        },
        "StrCount" => TermNode::StrCount {
            text: child_of("text", obj, arena, interner, variant)?,
            sub: child_of("sub", obj, arena, interner, variant)?,
        },
        "Round" => TermNode::Round {
            value: child_of("value", obj, arena, interner, variant)?,
            ndigits: child_of("ndigits", obj, arena, interner, variant)?,
        },
        "Reverse" => TermNode::Reverse {
            seq: child_of("seq", obj, arena, interner, variant)?,
        },
        "IndexedMap" => TermNode::IndexedMap {
            source: child_of("source", obj, arena, interner, variant)?,
            item_name: get_sym("item_name", interner)?,
            index_name: get_sym("index_name", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "Capitalize" => TermNode::Capitalize {
            text: child_of("text", obj, arena, interner, variant)?,
        },
        "ParseInt" => TermNode::ParseInt {
            text: child_of("text", obj, arena, interner, variant)?,
        },
        "Slice" => TermNode::Slice {
            seq: child_of("seq", obj, arena, interner, variant)?,
            start: child_of("start", obj, arena, interner, variant)?,
            stop: child_of("stop", obj, arena, interner, variant)?,
        },
        "Sort" => TermNode::Sort {
            seq: child_of("seq", obj, arena, interner, variant)?,
        },
        "DictItems" => TermNode::DictItems {
            seq: child_of("seq", obj, arena, interner, variant)?,
        },
        "SortBy" => TermNode::SortBy {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            key: child_of("key", obj, arena, interner, variant)?,
        },
        "GroupCount" => TermNode::GroupCount {
            seq: child_of("seq", obj, arena, interner, variant)?,
        },
        "DictMerge" => TermNode::DictMerge {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "ZipWith" => TermNode::ZipWith {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
            a_name: get_sym("a_name", interner)?,
            b_name: get_sym("b_name", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "Eq" => TermNode::Eq {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Lt" => TermNode::Lt {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Lte" => TermNode::Lte {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Gt" => TermNode::Gt {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Gte" => TermNode::Gte {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "SlideNeighbours" => TermNode::SlideNeighbours {
            cell: child_of("cell", obj, arena, interner, variant)?,
            slide: child_of("slide", obj, arena, interner, variant)?,
            ground: child_of("ground", obj, arena, interner, variant)?,
        },
        "ReachableFrom" => {
            let edge_type = get_optional_sym("edge_type", interner);
            let any_type = !matches!(obj.get("edge_type"), Some(J::String(_)));
            TermNode::ReachableFrom {
                node: child_of("node", obj, arena, interner, variant)?,
                edge_type,
                any_type,
            }
        }

        "Neighbours" => {
            let edge_type = get_optional_sym("edge_type", interner);
            let any_type = !matches!(obj.get("edge_type"), Some(J::String(_)));
            TermNode::Neighbours {
                node: child_of("node", obj, arena, interner, variant)?,
                edge_type,
                any_type,
            }
        }
        "InNeighbours" => {
            let edge_type = get_optional_sym("edge_type", interner);
            let any_type = !matches!(obj.get("edge_type"), Some(J::String(_)));
            TermNode::InNeighbours {
                node: child_of("node", obj, arena, interner, variant)?,
                edge_type,
                any_type,
            }
        }
        "MapNeighbours" => {
            let edge_type = get_optional_sym("edge_type", interner);
            let any_type = !matches!(obj.get("edge_type"), Some(J::String(_)));
            TermNode::MapNeighbours {
                source: child_of("source", obj, arena, interner, variant)?,
                edge_type,
                any_type,
            }
        }
        "Count" => TermNode::Count { source: child_of("source", obj, arena, interner, variant)? },
        "Filter" => TermNode::Filter {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            predicate: child_of("predicate", obj, arena, interner, variant)?,
        },
        "FilterList" => TermNode::FilterList {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            predicate: child_of("predicate", obj, arena, interner, variant)?,
        },
        "Exists" => TermNode::Exists {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            predicate: child_of("predicate", obj, arena, interner, variant)?,
        },
        "Sum" => TermNode::Sum {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "Prod" => TermNode::Prod {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "MinOver" => TermNode::MinOver {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
            default: opt_child_of("default", obj, arena, interner)?,
        },
        "MaxOver" => TermNode::MaxOver {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
            default: opt_child_of("default", obj, arena, interner)?,
        },
        "Pick" => TermNode::Pick { source: child_of("source", obj, arena, interner, variant)? },
        "PickUnique" => TermNode::PickUnique { source: child_of("source", obj, arena, interner, variant)? },
        "Argmax" => TermNode::Argmax {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
            default: opt_child_of("default", obj, arena, interner)?,
        },
        "Argmin" => TermNode::Argmin {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
            default: opt_child_of("default", obj, arena, interner)?,
        },
        "ArgminUnique" => TermNode::ArgminUnique {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
            default: opt_child_of("default", obj, arena, interner)?,
        },
        "ArgminRefusal" => TermNode::ArgminRefusal {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
            refused: opt_child_of("refused", obj, arena, interner)?,
        },
        "Fold" => TermNode::Fold {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            acc_name: get_sym("acc_name", interner)?,
            init: child_of("init", obj, arena, interner, variant)?,
            body: child_of("body", obj, arena, interner, variant)?,
        },
        "BitsAt" => TermNode::BitsAt {
            buffer: child_of("buffer", obj, arena, interner, variant)?,
            bitpos: child_of("bitpos", obj, arena, interner, variant)?,
            n_bits: child_of("n_bits", obj, arena, interner, variant)?,
        },
        "BitsWrite" => TermNode::BitsWrite {
            buffer: child_of("buffer", obj, arena, interner, variant)?,
            bitpos: child_of("bitpos", obj, arena, interner, variant)?,
            value: child_of("value", obj, arena, interner, variant)?,
            n_bits: child_of("n_bits", obj, arena, interner, variant)?,
        },
        "BitsWriteAll" => TermNode::BitsWriteAll {
            buffer: child_of("buffer", obj, arena, interner, variant)?,
            writes: child_of("writes", obj, arena, interner, variant)?,
        },
        "BitsAtAll" => TermNode::BitsAtAll {
            buffer: child_of("buffer", obj, arena, interner, variant)?,
            reads: child_of("reads", obj, arena, interner, variant)?,
        },
        "HuffmanDecodeStream" => TermNode::HuffmanDecodeStream {
            buffer: child_of("buffer", obj, arena, interner, variant)?,
            bitpos: child_of("bitpos", obj, arena, interner, variant)?,
            table: child_of("table", obj, arena, interner, variant)?,
            n_pairs: child_of("n_pairs", obj, arena, interner, variant)?,
        },
        "HuffmanEncodeStream" => TermNode::HuffmanEncodeStream {
            buffer: child_of("buffer", obj, arena, interner, variant)?,
            bitpos: child_of("bitpos", obj, arena, interner, variant)?,
            pairs: child_of("pairs", obj, arena, interner, variant)?,
            table: child_of("table", obj, arena, interner, variant)?,
        },
        "ExpGolombDecode" => TermNode::ExpGolombDecode {
            buffer: child_of("buffer", obj, arena, interner, variant)?,
            bitpos: child_of("bitpos", obj, arena, interner, variant)?,
        },
        "ExpGolombDecodeSigned" => TermNode::ExpGolombDecodeSigned {
            buffer: child_of("buffer", obj, arena, interner, variant)?,
            bitpos: child_of("bitpos", obj, arena, interner, variant)?,
        },
        "ExpGolombEncode" => TermNode::ExpGolombEncode {
            buffer: child_of("buffer", obj, arena, interner, variant)?,
            bitpos: child_of("bitpos", obj, arena, interner, variant)?,
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "ExpGolombEncodeSigned" => TermNode::ExpGolombEncodeSigned {
            buffer: child_of("buffer", obj, arena, interner, variant)?,
            bitpos: child_of("bitpos", obj, arena, interner, variant)?,
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "Holds" => TermNode::Holds {
            concept: get_sym("concept", interner)?,
            node: opt_child_of("node", obj, arena, interner)?,
            node2: opt_child_of("node2", obj, arena, interner)?,
        },
        "EvalSubgraph" => TermNode::EvalSubgraph {
            node: child_of("node", obj, arena, interner, variant)?,
        },
        "And" => TermNode::And { items: children_of("items", obj, arena, interner)? },
        "Or" => TermNode::Or { items: children_of("items", obj, arena, interner)? },
        "Not" => TermNode::Not { arg: child_of("arg", obj, arena, interner, variant)? },
        "Abs" => TermNode::Abs { arg: child_of("arg", obj, arena, interner, variant)? },
        "Neg" => TermNode::Neg { arg: child_of("arg", obj, arena, interner, variant)? },
        "Plus" => TermNode::Plus { items: children_of("items", obj, arena, interner)? },
        "Minus" => TermNode::Minus {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Times" => TermNode::Times { items: children_of("items", obj, arena, interner)? },
        "Div" => TermNode::Div {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "ApcEncode" => TermNode::ApcEncode {
            model: child_of("model", obj, arena, interner, variant)?,
            seq: child_of("seq", obj, arena, interner, variant)?,
            start: child_of("start", obj, arena, interner, variant)?,
            end: child_of("end", obj, arena, interner, variant)?,
            out_len: child_of("out_len", obj, arena, interner, variant)?,
        },
        "DtwTo" => TermNode::DtwTo {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "PointSetDist" => TermNode::PointSetDist {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "MahalLeaf" => TermNode::MahalLeaf {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "MahalFull" => TermNode::MahalFull {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "DeformGenMarginal" => TermNode::DeformGenMarginal {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "DeformGen" => TermNode::DeformGen {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "DeformDist" => TermNode::DeformDist {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "SmoothDeformDist" => TermNode::SmoothDeformDist {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "TpsDeformDist" => TermNode::TpsDeformDist {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "SmoothDeformComponents" => TermNode::SmoothDeformComponents {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "ShapeContextDist" => TermNode::ShapeContextDist {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "ScTpsDist" => TermNode::ScTpsDist {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "BlendCover" => TermNode::BlendCover {
            unknown: child_of("unknown", obj, arena, interner, variant)?,
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "XCorrPeak" => TermNode::XCorrPeak {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Whiten" => TermNode::Whiten {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "WhitenMany" => TermNode::WhitenMany {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "WithinScatter" => TermNode::WithinScatter {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "BetweenScatter" => TermNode::BetweenScatter {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Mod" => TermNode::Mod {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Pow" => TermNode::Pow {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "BitAnd" => TermNode::BitAnd {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "BitOr" => TermNode::BitOr {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "BitXor" => TermNode::BitXor {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Shl" => TermNode::Shl {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Lshr" => TermNode::Lshr {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Ashr" => TermNode::Ashr {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "IDiv" => TermNode::IDiv {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "IRem" => TermNode::IRem {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Sqrt" => TermNode::Sqrt { arg: child_of("arg", obj, arena, interner, variant)? },
        "EnclosedCount" => TermNode::EnclosedCount { arg: child_of("arg", obj, arena, interner, variant)? },
        "Log" => TermNode::Log { arg: child_of("arg", obj, arena, interner, variant)? },
        "Exp" => TermNode::Exp { arg: child_of("arg", obj, arena, interner, variant)? },
        "Min" => TermNode::Min { items: children_of("items", obj, arena, interner)? },
        "Max" => TermNode::Max { items: children_of("items", obj, arena, interner)? },
        "ArgMax" => TermNode::ArgMax { items: children_of("items", obj, arena, interner)? },
        "IfThenElse" => TermNode::IfThenElse {
            cond: child_of("cond", obj, arena, interner, variant)?,
            then: child_of("then", obj, arena, interner, variant)?,
            other: child_of("other", obj, arena, interner, variant)?,
        },
        "Vec" => TermNode::Vec_ { items: children_of("items", obj, arena, interner)? },
        "VecAdd" => TermNode::VecAdd {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "VecSub" => TermNode::VecSub {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Dot" => TermNode::Dot {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Magnitude" => TermNode::Magnitude { arg: child_of("arg", obj, arena, interner, variant)? },
        "Sin" => TermNode::Sin { arg: child_of("arg", obj, arena, interner, variant)? },
        "Cos" => TermNode::Cos { arg: child_of("arg", obj, arena, interner, variant)? },
        "Atan2" => TermNode::Atan2 {
            y: child_of("y", obj, arena, interner, variant)?,
            x: child_of("x", obj, arena, interner, variant)?,
        },
        "Bearing" => TermNode::Bearing { arg: child_of("arg", obj, arena, interner, variant)? },
        "Rotate" => TermNode::Rotate {
            vec: child_of("vec", obj, arena, interner, variant)?,
            angle: child_of("angle", obj, arena, interner, variant)?,
        },
        "AngleBetween" => TermNode::AngleBetween {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Surface" => {
            let kind = match obj.get("kind").and_then(|k| k.as_str()) {
                Some("bytes") => SurfaceKind::Bytes,
                _ => SurfaceKind::Text,
            };
            TermNode::Surface { kind, payload: get_value("payload", interner) }
        }
        "Cat" => TermNode::Cat { items: children_of("items", obj, arena, interner)? },
        "Slot" => TermNode::Slot { name: get_sym("name", interner)? },
        "Join" => TermNode::Join {
            separator: opt_child_of("separator", obj, arena, interner)?,
            items: opt_child_of("items", obj, arena, interner)?,
        },
        "Bytes" => TermNode::Bytes { items: children_of("items", obj, arena, interner)? },
        "U8" => TermNode::U8 { expr: opt_child_of("expr", obj, arena, interner)? },
        "U16LE" => TermNode::U16LE { expr: opt_child_of("expr", obj, arena, interner)? },
        "U32LE" => TermNode::U32LE { expr: opt_child_of("expr", obj, arena, interner)? },
        "U64LE" => TermNode::U64LE { expr: opt_child_of("expr", obj, arena, interner)? },
        "LEB128" => TermNode::LEB128 { expr: opt_child_of("expr", obj, arena, interner)? },
        "Lines" => TermNode::Lines { items: children_of("items", obj, arena, interner)? },
        "Label" => TermNode::Label { prefix: interner.intern(&get_str_or_empty("prefix")) },
        "Let" => TermNode::Let {
            name: get_sym("name", interner)?,
            value: opt_child_of("value", obj, arena, interner)?,
            body: opt_child_of("body", obj, arena, interner)?,
        },
        "Nth" => TermNode::Nth {
            items: opt_child_of("items", obj, arena, interner)?,
            index: get_int("index"),
        },
        "Render" => TermNode::Render {
            term: opt_child_of("term", obj, arena, interner)?,
            lang: opt_child_of("lang", obj, arena, interner)?,
        },
        "LitRepr" => TermNode::LitRepr {
            value: opt_child_of("value", obj, arena, interner)?,
        },
        // --- Phase 7 ext additions ---
        "Last" => TermNode::Last { seq: child_of("seq", obj, arena, interner, variant)? },
        "IndexAt" => TermNode::IndexAt {
            seq: child_of("seq", obj, arena, interner, variant)?,
            index: child_of("index", obj, arena, interner, variant)?,
        },
        "Append" => TermNode::Append {
            seq: child_of("seq", obj, arena, interner, variant)?,
            item: child_of("item", obj, arena, interner, variant)?,
        },
        "ListDrop" => TermNode::ListDrop {
            list: child_of("list", obj, arena, interner, variant)?,
            index: child_of("index", obj, arena, interner, variant)?,
        },
        "Union" => TermNode::Union {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Intersect" => TermNode::Intersect {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "Difference" => TermNode::Difference {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
        },
        "MapSet" => TermNode::MapSet {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "MapList" => TermNode::MapList {
            source: child_of("source", obj, arena, interner, variant)?,
            var_name: get_sym("var_name", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "Edges" => {
            let edge_type = get_optional_sym("edge_type", interner);
            let any_type = !matches!(obj.get("edge_type"), Some(J::String(_)));
            TermNode::Edges {
                node: child_of("node", obj, arena, interner, variant)?,
                edge_type,
                any_type,
            }
        }
        "EdgeAttr" => TermNode::EdgeAttr {
            edge: child_of("edge", obj, arena, interner, variant)?,
            key: get_sym("key", interner)?,
        },
        "NodesWhere" => TermNode::NodesWhere {
            node_type: get_sym("node_type", interner)?,
            attr_key: get_sym("attr_key", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "NodesOfType" => TermNode::NodesOfType {
            node_type: get_sym("node_type", interner)?,
        },
        "AntiUnify" => TermNode::AntiUnify {
            values: child_of("values", obj, arena, interner, variant)?,
            wild: interner.intern("·?·"),
        },
        "FixedCount" => TermNode::FixedCount {
            pattern: child_of("pattern", obj, arena, interner, variant)?,
            wild: interner.intern("·?·"),
        },
        "Covers" => TermNode::Covers {
            pattern: child_of("pattern", obj, arena, interner, variant)?,
            instance: child_of("instance", obj, arena, interner, variant)?,
            wild: interner.intern("·?·"),
        },
        "CoversOpen" => TermNode::CoversOpen {
            pattern: child_of("pattern", obj, arena, interner, variant)?,
            instance: child_of("instance", obj, arena, interner, variant)?,
            wild: interner.intern("·?·"),
        },
        "AntiUnifyWitness" => TermNode::AntiUnifyWitness {
            values: child_of("values", obj, arena, interner, variant)?,
            wild: interner.intern("·?·"),
        },
        "Substitute" => TermNode::Substitute {
            template: child_of("template", obj, arena, interner, variant)?,
            sigma: child_of("sigma", obj, arena, interner, variant)?,
            wild: interner.intern("·?·"),
        },
        "Unify" => TermNode::Unify {
            values: child_of("values", obj, arena, interner, variant)?,
            wild: interner.intern("·?·"),
        },
        "StructSim" => TermNode::StructSim {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
            wild: interner.intern("·?·"),
        },
        "ShapeDecode" => TermNode::ShapeDecode {
            goal: child_of("goal", obj, arena, interner, variant)?,
            codebook_type: interner.intern(
                obj.get("codebook_type").and_then(|v| v.as_str()).unwrap_or("ShapeSignature"),
            ),
            exclude: opt_child_of("exclude", obj, arena, interner)?,
            codebook_scope: opt_child_of("codebook_scope", obj, arena, interner)?,
            beam: obj.get("beam").and_then(|v| v.as_i64()).unwrap_or(3),
            max_steps: obj.get("max_steps").and_then(|v| v.as_i64()).unwrap_or(8),
            cand_k: obj.get("cand_k").and_then(|v| v.as_i64()).unwrap_or(3),
            // <=0 (including absent, the near-universal case in shipped seed
            // JSON) selects `shape_decode::DEFAULT_SD_BUDGET` at eval time —
            // see the `budget` field's doc on `TermNode::ShapeDecode`.
            budget: obj.get("budget").and_then(|v| v.as_i64()).unwrap_or(0),
            field: get_optional_sym("field", interner),
            wild: interner.intern("·?·"),
            wild_objects: obj.get("wild_objects").and_then(|v| v.as_bool()).unwrap_or(false),
        },
        "MotorCompose" => TermNode::MotorCompose {
            episode: child_of("episode", obj, arena, interner, variant)?,
            policy: child_of("policy", obj, arena, interner, variant)?,
            candidate: child_of("candidate", obj, arena, interner, variant)?,
        },
        "TransformDecode" => TermNode::TransformDecode {
            goal: child_of("goal", obj, arena, interner, variant)?,
            codebook_type: interner.intern(
                obj.get("codebook_type").and_then(|v| v.as_str()).unwrap_or("ShapeSignature"),
            ),
            exclude: opt_child_of("exclude", obj, arena, interner)?,
            max_dims: obj.get("max_dims").and_then(|v| v.as_i64()).unwrap_or(2),
            field: get_optional_sym("field", interner),
        },
        "NetForward" => TermNode::NetForward {
            assemblage: child_of("assemblage", obj, arena, interner, variant)?,
            inputs: child_of("inputs", obj, arena, interner, variant)?,
        },
        "DimInfer" => TermNode::DimInfer {
            goal: child_of("goal", obj, arena, interner, variant)?,
            codebook_type: interner.intern(
                obj.get("codebook_type").and_then(|v| v.as_str()).unwrap_or("ShapeSignature"),
            ),
            exclude: opt_child_of("exclude", obj, arena, interner)?,
            generator_type: interner.intern(
                obj.get("generator_type").and_then(|v| v.as_str()).unwrap_or("DimensionGenerator"),
            ),
            max_dims: obj.get("max_dims").and_then(|v| v.as_i64()).unwrap_or(2),
            field: get_optional_sym("field", interner),
        },
        "GenInfer" => TermNode::GenInfer {
            goal: child_of("goal", obj, arena, interner, variant)?,
            codebook_type: interner.intern(
                obj.get("codebook_type").and_then(|v| v.as_str()).unwrap_or("ShapeSignature"),
            ),
            exclude: opt_child_of("exclude", obj, arena, interner)?,
            max_dims: obj.get("max_dims").and_then(|v| v.as_i64()).unwrap_or(2),
            field: get_optional_sym("field", interner),
        },
        "TimeInfer" => TermNode::TimeInfer {
            sequence: child_of("sequence", obj, arena, interner, variant)?,
            codebook_type: interner.intern(
                obj.get("codebook_type").and_then(|v| v.as_str()).unwrap_or("ShapeSignature"),
            ),
            max_b: obj.get("max_b").and_then(|v| v.as_i64()).unwrap_or(8),
            field: get_optional_sym("field", interner),
            max_steps: obj.get("max_steps").and_then(|v| v.as_i64())
                .unwrap_or(DEFAULT_TIME_INFER_MAX_STEPS),
            robust: obj.get("robust").and_then(|v| v.as_bool()).unwrap_or(false),
        },
        "DepthInfer" => TermNode::DepthInfer {
            sequence: child_of("sequence", obj, arena, interner, variant)?,
            codebook_type: interner.intern(
                obj.get("codebook_type").and_then(|v| v.as_str()).unwrap_or("ShapeSignature"),
            ),
            max_b: obj.get("max_b").and_then(|v| v.as_i64()).unwrap_or(8),
            field: get_optional_sym("field", interner),
        },
        "BlinkBridge" => TermNode::BlinkBridge {
            sequence: child_of("sequence", obj, arena, interner, variant)?,
            codebook_type: interner.intern(
                obj.get("codebook_type").and_then(|v| v.as_str()).unwrap_or("ShapeSignature"),
            ),
            max_b: obj.get("max_b").and_then(|v| v.as_i64()).unwrap_or(8),
            field: get_optional_sym("field", interner),
        },
        "GapAbduce" => TermNode::GapAbduce {
            sequence: child_of("sequence", obj, arena, interner, variant)?,
            codebook_type: interner.intern(
                obj.get("codebook_type").and_then(|v| v.as_str()).unwrap_or("ShapeSignature"),
            ),
            max_b: obj.get("max_b").and_then(|v| v.as_i64()).unwrap_or(8),
            field: get_optional_sym("field", interner),
        },
        "GapVerify" => TermNode::GapVerify {
            sequence: child_of("sequence", obj, arena, interner, variant)?,
            codebook_type: interner.intern(
                obj.get("codebook_type").and_then(|v| v.as_str()).unwrap_or("ShapeSignature"),
            ),
            max_b: obj.get("max_b").and_then(|v| v.as_i64()).unwrap_or(8),
            field: get_optional_sym("field", interner),
        },
        "SupportInfer" => TermNode::SupportInfer {
            sequence: child_of("sequence", obj, arena, interner, variant)?,
            codebook_type: interner.intern(
                obj.get("codebook_type").and_then(|v| v.as_str()).unwrap_or("ShapeSignature"),
            ),
            field: get_optional_sym("field", interner),
        },
        "MotionEnergy" => TermNode::MotionEnergy {
            sequence: child_of("sequence", obj, arena, interner, variant)?,
            height: obj.get("height").and_then(|v| v.as_i64()).unwrap_or(0),
            width: obj.get("width").and_then(|v| v.as_i64()).unwrap_or(0),
            field: get_optional_sym("field", interner),
        },
        "TransferDecode" => TermNode::TransferDecode {
            goal: child_of("goal", obj, arena, interner, variant)?,
        },
        "RecogniseShape" => TermNode::RecogniseShape {
            text: child_of("text", obj, arena, interner, variant)?,
        },
        "MetaShapeMint" => TermNode::MetaShapeMint {
            observation: child_of("observation", obj, arena, interner, variant)?,
            obs_type: interner.intern(
                obj.get("obs_type").and_then(|v| v.as_str()).unwrap_or("ShapeObservation"),
            ),
            status_value: interner.intern(
                obj.get("status_value").and_then(|v| v.as_str()).unwrap_or("residual"),
            ),
            wild: interner.intern(obj.get("wild").and_then(|v| v.as_str()).unwrap_or("\u{b7}?\u{b7}")),
            field: get_optional_sym("field", interner),
        },
        "StrokeQuantize" => TermNode::StrokeQuantize {
            points: child_of("points", obj, arena, interner, variant)?,
            segments: obj.get("segments").and_then(|v| v.as_i64()).unwrap_or(12),
            turn_bins: obj.get("turn_bins").and_then(|v| v.as_i64()).unwrap_or(16),
            len_bins: obj.get("len_bins").and_then(|v| v.as_i64()).unwrap_or(8),
            grid: obj.get("grid").and_then(|v| v.as_i64()).unwrap_or(8),
            scale_bins: obj.get("scale_bins").and_then(|v| v.as_i64()).unwrap_or(8),
            invariant_only: obj.get("invariant_only").and_then(|v| v.as_bool()).unwrap_or(false),
            canonical_pose: obj.get("canonical_pose").and_then(|v| v.as_bool()).unwrap_or(false),
            turn_edges: opt_child_of("turn_edges", obj, arena, interner)?,
            len_edges: opt_child_of("len_edges", obj, arena, interner)?,
            emit_residual: obj.get("emit_residual").and_then(|v| v.as_bool()).unwrap_or(false),
            bounds: opt_child_of("bounds", obj, arena, interner)?,
            field: get_optional_sym("field", interner),
            seg_sym: interner.intern("seg"),
            pose_x_sym: interner.intern("pose_x"),
            pose_y_sym: interner.intern("pose_y"),
            pose_o_sym: interner.intern("pose_o"),
            pose_s_sym: interner.intern("pose_s"),
        },
        "StrokeRender" => TermNode::StrokeRender {
            signature: child_of("signature", obj, arena, interner, variant)?,
            n_points: obj.get("n_points").and_then(|v| v.as_i64()).unwrap_or(24),
            apply_pose: obj.get("apply_pose").and_then(|v| v.as_bool()).unwrap_or(true),
            turn_bins: obj.get("turn_bins").and_then(|v| v.as_i64()).unwrap_or(16),
            len_bins: obj.get("len_bins").and_then(|v| v.as_i64()).unwrap_or(8),
            grid: obj.get("grid").and_then(|v| v.as_i64()).unwrap_or(8),
            scale_bins: obj.get("scale_bins").and_then(|v| v.as_i64()).unwrap_or(8),
            turn_edges: opt_child_of("turn_edges", obj, arena, interner)?,
            len_edges: opt_child_of("len_edges", obj, arena, interner)?,
            bounds: opt_child_of("bounds", obj, arena, interner)?,
            field: get_optional_sym("field", interner),
        },
        "SigmaLognormalGenerate" => TermNode::SigmaLognormalGenerate {
            primitives: child_of("primitives", obj, arena, interner, variant)?,
            start: child_of("start", obj, arena, interner, variant)?,
            t_start: obj.get("t_start").and_then(|v| v.as_f64()).unwrap_or(0.0),
            t_end: obj.get("t_end").and_then(|v| v.as_f64()).unwrap_or(1.0),
            n_points: obj.get("n_points").and_then(|v| v.as_i64()).unwrap_or(24),
            field: get_optional_sym("field", interner),
        },
        "LookaheadValue" => TermNode::LookaheadValue {
            node: child_of("node", obj, arena, interner, variant)?,
            child_edge: get_sym("child_edge", interner)?,
            score_key: get_sym("score_key", interner)?,
            depth: child_of("depth", obj, arena, interner, variant)?,
        },
        "ScalarAttrTriples" => TermNode::ScalarAttrTriples {
            skip_prefix: get_optional_sym("skip_prefix", interner),
        },
        "AttrByName" => TermNode::AttrByName {
            node: child_of("node", obj, arena, interner, variant)?,
            name: child_of("name", obj, arena, interner, variant)?,
        },
        "ArgMin" => TermNode::ArgMin { items: children_of("items", obj, arena, interner)? },
        "TrackIdentityCorrespondence" => {
            let get_opt_sym = |field: &str, i: &mut Interner| -> Option<Sym> {
                match obj.get(field) {
                    Some(J::String(s)) => Some(i.intern(s)),
                    _ => None,
                }
            };
            TermNode::TrackIdentityCorrespondence {
                prev: child_of("prev", obj, arena, interner, variant)?,
                cur: child_of("cur", obj, arena, interner, variant)?,
                feature_key: get_sym("feature_key", interner)?,
                category_key: get_opt_sym("category_key", interner),
                extent_key: get_opt_sym("extent_key", interner),
                radius: child_of("radius", obj, arena, interner, variant)?,
            }
        }
        // --- Program IR (P1). This is the parse-time interning path:
        // every identifier in the wire form becomes a real Sym HERE
        // (jsonio holds `&mut Interner`), which is why eval-time
        // interning is never needed for IR-carried names.
        "ProgSeq" => TermNode::ProgSeq { stmts: children_of("stmts", obj, arena, interner)? },
        "ProgAssignVar" => TermNode::ProgAssignVar {
            name: get_sym("name", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "ProgAugAssign" => TermNode::ProgAugAssign {
            name: get_sym("name", interner)?,
            op: get_sym("op", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "ProgTupleUnpack" => {
            let targets = sym_array_of("targets", obj, interner);
            TermNode::ProgTupleUnpack {
                targets,
                value: child_of("value", obj, arena, interner, variant)?,
            }
        }
        "ProgIfStmt" => TermNode::ProgIfStmt {
            cond: child_of("cond", obj, arena, interner, variant)?,
            then: child_of("then", obj, arena, interner, variant)?,
            orelse: opt_child_of("orelse", obj, arena, interner)?,
        },
        "ProgForEach" => TermNode::ProgForEach {
            var: get_sym("var", interner)?,
            iter: child_of("iter", obj, arena, interner, variant)?,
            body: child_of("body", obj, arena, interner, variant)?,
            orelse: opt_child_of("orelse", obj, arena, interner)?,
        },
        "ProgWhile" => TermNode::ProgWhile {
            cond: child_of("cond", obj, arena, interner, variant)?,
            body: child_of("body", obj, arena, interner, variant)?,
            orelse: opt_child_of("orelse", obj, arena, interner)?,
        },
        "ProgLoopCtl" => TermNode::ProgLoopCtl { kind: get_sym("kind", interner)? },
        "ProgReturn" => TermNode::ProgReturn {
            value: opt_child_of("value", obj, arena, interner)?,
        },
        "ProgTryOr" => TermNode::ProgTryOr {
            body: child_of("body", obj, arena, interner, variant)?,
            exc_var: get_optional_sym("exc_var", interner),
            handler: opt_child_of("handler", obj, arena, interner)?,
        },
        "ProgRaise" => TermNode::ProgRaise {
            exc: opt_child_of("exc", obj, arena, interner)?,
        },
        "ProgImportStmt" => TermNode::ProgImportStmt {
            module: get_sym("module", interner)?,
            alias: get_optional_sym("alias", interner),
            names: sym_array_of("names", obj, interner),
        },
        "ProgSubscriptSet" => TermNode::ProgSubscriptSet {
            obj: child_of("obj", obj, arena, interner, variant)?,
            index: child_of("index", obj, arena, interner, variant)?,
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "ProgAttrSet" => TermNode::ProgAttrSet {
            obj: child_of("obj", obj, arena, interner, variant)?,
            attr: get_sym("attr", interner)?,
            value: child_of("value", obj, arena, interner, variant)?,
        },
        "ProgDefFnParam" => TermNode::ProgDefFnParam {
            name: get_sym("name", interner)?,
            default: opt_child_of("default", obj, arena, interner)?,
        },
        "ProgCallExtern" => TermNode::ProgCallExtern {
            name: get_sym("name", interner)?,
            recv: opt_child_of("recv", obj, arena, interner)?,
            args: children_of("args", obj, arena, interner)?,
        },
        "ProgAttrGet" => TermNode::ProgAttrGet {
            obj: child_of("obj", obj, arena, interner, variant)?,
            attr: get_sym("attr", interner)?,
        },
        "ProgSubscript" => TermNode::ProgSubscript {
            obj: child_of("obj", obj, arena, interner, variant)?,
            index: child_of("index", obj, arena, interner, variant)?,
        },
        "ProgSlice" => TermNode::ProgSlice {
            obj: child_of("obj", obj, arena, interner, variant)?,
            start: opt_child_of("start", obj, arena, interner)?,
            stop: opt_child_of("stop", obj, arena, interner)?,
            step: opt_child_of("step", obj, arena, interner)?,
        },
        "ProgContainerLit" => TermNode::ProgContainerLit {
            kind: get_sym("kind", interner)?,
            items: children_of("items", obj, arena, interner)?,
        },
        "ProgComprehensionList" => TermNode::ProgComprehensionList {
            var: get_sym("var", interner)?,
            source: child_of("source", obj, arena, interner, variant)?,
            expr: child_of("expr", obj, arena, interner, variant)?,
            cond: opt_child_of("cond", obj, arena, interner)?,
        },
        "ProgComprehensionGen" => TermNode::ProgComprehensionGen {
            var: get_sym("var", interner)?,
            source: child_of("source", obj, arena, interner, variant)?,
            expr: child_of("expr", obj, arena, interner, variant)?,
            cond: opt_child_of("cond", obj, arena, interner)?,
        },
        "ProgIsOp" => TermNode::ProgIsOp {
            a: child_of("a", obj, arena, interner, variant)?,
            b: child_of("b", obj, arena, interner, variant)?,
            negated: obj.get("negated").and_then(|v| v.as_bool()).unwrap_or(false),
        },
        "ProgFString" => TermNode::ProgFString {
            parts: children_of("parts", obj, arena, interner)?,
        },
        "ProgEval" => TermNode::ProgEval {
            prog: child_of("prog", obj, arena, interner, variant)?,
            env: opt_child_of("env", obj, arena, interner)?,
            oracles: opt_child_of("oracles", obj, arena, interner)?,
            fuel: get_int("fuel"),
            field: get_optional_sym("field", interner),
        },
        "SnakeCase" => TermNode::SnakeCase {
            text: child_of("text", obj, arena, interner, variant)?,
        },
        "CaseFold" => TermNode::CaseFold {
            text: child_of("text", obj, arena, interner, variant)?,
        },
        "SynthEnumerate" => TermNode::SynthEnumerate {
            examples: child_of("examples", obj, arena, interner, variant)?,
            ops: opt_child_of("ops", obj, arena, interner)?,
            consts: opt_child_of("consts", obj, arena, interner)?,
            exclude: opt_child_of("exclude", obj, arena, interner)?,
            derived_ops: opt_child_of("derived_ops", obj, arena, interner)?,
            exclude_ops: opt_child_of("exclude_ops", obj, arena, interner)?,
            max_size: get_int("max_size"),
            max_candidates: get_int("max_candidates"),
            saturate_k: get_int("saturate_k"),
            field: get_optional_sym("field", interner),
        },
        "Call" => TermNode::Call {
            name: get_sym("name", interner)?,
            args: children_of("args", obj, arena, interner)?,
        },
        "ParetoDominates" => TermNode::ParetoDominates {
            candidate: child_of("candidate", obj, arena, interner, variant)?,
            alternative: child_of("alternative", obj, arena, interner, variant)?,
            dimension_count: child_of("dimension_count", obj, arena, interner, variant)?,
            value_edge: interner.intern(
                obj.get("value_edge").and_then(|v| v.as_str()).unwrap_or("has_pareto_value"),
            ),
            measure_edge: interner.intern(
                obj.get("measure_edge").and_then(|v| v.as_str()).unwrap_or("measures_goal"),
            ),
            dimension_key: interner.intern(
                obj.get("dimension_key").and_then(|v| v.as_str()).unwrap_or("dimension_ordinal"),
            ),
            verified_key: interner.intern(
                obj.get("verified_key").and_then(|v| v.as_str()).unwrap_or("verified"),
            ),
            signed_value_key: interner.intern(
                obj.get("signed_value_key").and_then(|v| v.as_str()).unwrap_or("signed_value"),
            ),
        },
        other => return Err(JsonError::UnknownTermType(other.to_string())),
    };
    Ok(arena.add(node))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::grammar::Grammar;
    use crate::term::TermNode;
    use crate::value::Value;

    #[test]
    fn term_round_trips_via_json() {
        let mut a = TermArena::new();
        let mut i = Interner::new();
        let n = i.intern("n");
        let alive = i.intern("AliveCell");
        // Filter(SetT(Lit Int 1, Lit Int 2), n, Eq(Var n, Lit Str AliveCell))
        let one = a.add(TermNode::Lit { value: Value::Int(1) });
        let two = a.add(TermNode::Lit { value: Value::Int(2) });
        let set = a.add(TermNode::SetT { items: vec![one, two] });
        let n_t = a.add(TermNode::Var { name: n });
        let lit = a.add(TermNode::Lit { value: Value::Str(alive) });
        let eq = a.add(TermNode::Eq { a: n_t, b: lit });
        let filt = a.add(TermNode::Filter { source: set, var_name: n, predicate: eq });

        let j = term_to_json(&a, filt, &i);
        // Re-parse into a fresh arena.
        let mut a2 = TermArena::new();
        let mut i2 = Interner::new();
        let rebuilt = term_from_json(&j, &mut a2, &mut i2).unwrap();
        // The text serialisation matches itself.
        let j2 = term_to_json(&a2, rebuilt, &i2);
        assert_eq!(j, j2);
    }

    #[test]
    fn pareto_dominates_term_round_trips_via_json() {
        let mut arena = TermArena::new();
        let mut interner = Interner::new();
        let candidate_name = interner.intern("candidate");
        let alternative_name = interner.intern("alternative");
        let candidate = arena.add(TermNode::Var {
            name: candidate_name,
        });
        let alternative = arena.add(TermNode::Var {
            name: alternative_name,
        });
        let dimension_count = arena.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let term = arena.add(TermNode::ParetoDominates {
            candidate,
            alternative,
            dimension_count,
            value_edge: interner.intern("has_value"),
            measure_edge: interner.intern("measures"),
            dimension_key: interner.intern("dimension"),
            verified_key: interner.intern("trusted"),
            signed_value_key: interner.intern("utility"),
        });

        let json = term_to_json(&arena, term, &interner);
        let mut rebuilt_arena = TermArena::new();
        let mut rebuilt_interner = Interner::new();
        let rebuilt = term_from_json(
            &json,
            &mut rebuilt_arena,
            &mut rebuilt_interner,
        )
        .unwrap();

        assert_eq!(
            json,
            term_to_json(&rebuilt_arena, rebuilt, &rebuilt_interner)
        );
    }

    #[test]
    fn experiment_composer_terms_round_trip_via_json() {
        // ShiftThresholdLits(FromJsonString(Lit text), ToJsonString(MkDict(...)))
        // -- exercises all three new Terms' to_json/from_json arms together.
        let mut a = TermArena::new();
        let mut i = Interner::new();
        let text = a.add(TermNode::Lit { value: Value::Str(i.intern("{}")) });
        let parsed = a.add(TermNode::FromJsonString { text });
        let key = a.add(TermNode::Lit { value: Value::Str(i.intern("effects")) });
        let got = a.add(TermNode::DictGet { dict: parsed, key });
        let shift_lit = a.add(TermNode::Lit { value: Value::Float(0.5) });
        let shifted = a.add(TermNode::ShiftThresholdLits { tree: got, shift: shift_lit });
        let wrapped = a.add(TermNode::ToJsonString { value: shifted });

        let j = term_to_json(&a, wrapped, &i);
        let mut a2 = TermArena::new();
        let mut i2 = Interner::new();
        let rebuilt = term_from_json(&j, &mut a2, &mut i2).unwrap();
        let j2 = term_to_json(&a2, rebuilt, &i2);
        assert_eq!(j, j2);
        assert_eq!(j["type"], "ToJsonString");
        assert_eq!(j["value"]["type"], "ShiftThresholdLits");
        assert_eq!(j["value"]["tree"]["type"], "DictGet");
        assert_eq!(j["value"]["tree"]["dict"]["type"], "FromJsonString");
    }

    #[test]
    fn editop_terms_round_trip_via_json() {
        // RewriteTreeNodes(FromJsonString(Lit text), type_filter=Lit("Attr"),
        // field=Lit("key"), value_map=MkDict(...)) and ListDrop(..., index)
        // -- exercises both new Terms' to_json/from_json arms, including
        // RewriteTreeNodes's OptChild `type_filter` field (both Some and None).
        let mut a = TermArena::new();
        let mut i = Interner::new();
        let text = a.add(TermNode::Lit { value: Value::Str(i.intern(r#"{"type":"Attr","key":"row"}"#)) });
        let tree = a.add(TermNode::FromJsonString { text });
        let old_k = a.add(TermNode::Lit { value: Value::Str(i.intern("row")) });
        let new_k = a.add(TermNode::Lit { value: Value::Str(i.intern("col")) });
        let value_map = a.add(TermNode::MkDict { items: vec![old_k, new_k] });
        let field = a.add(TermNode::Lit { value: Value::Str(i.intern("key")) });
        let type_filter = a.add(TermNode::Lit { value: Value::Str(i.intern("Attr")) });
        let rewrite = a.add(TermNode::RewriteTreeNodes {
            tree, type_filter: Some(type_filter), field, value_map,
        });
        let idx = a.add(TermNode::Lit { value: Value::Int(0) });
        let dropped = a.add(TermNode::ListDrop { list: rewrite, index: idx });

        let j = term_to_json(&a, dropped, &i);
        let mut a2 = TermArena::new();
        let mut i2 = Interner::new();
        let rebuilt = term_from_json(&j, &mut a2, &mut i2).unwrap();
        let j2 = term_to_json(&a2, rebuilt, &i2);
        assert_eq!(j, j2);
        assert_eq!(j["type"], "ListDrop");
        assert_eq!(j["list"]["type"], "RewriteTreeNodes");
        assert_eq!(j["list"]["type_filter"]["type"], "Lit");
        assert_eq!(j["list"]["tree"]["type"], "FromJsonString");

        // type_filter=None round-trips too (missing/null field -> None).
        // Fresh Lit nodes in a2 -- `field`/`value_map` are TermIdx handles
        // into arena `a`, not valid in `a2`.
        let field2 = a2.add(TermNode::Lit { value: Value::Str(i2.intern("type")) });
        let value_map2 = a2.add(TermNode::MkDict { items: vec![] });
        let rewrite_no_filter = a2.add(TermNode::RewriteTreeNodes {
            tree: rebuilt, type_filter: None, field: field2, value_map: value_map2,
        });
        let j3 = term_to_json(&a2, rewrite_no_filter, &i2);
        assert_eq!(j3["type_filter"], serde_json::Value::Null);
        let rebuilt3 = term_from_json(&j3, &mut a2, &mut i2).unwrap();
        let TermNode::RewriteTreeNodes { type_filter: tf, .. } = a2.get(rebuilt3) else { panic!("expected RewriteTreeNodes") };
        assert!(tf.is_none());
    }

    #[test]
    fn attr_key_ranking_round_trip_via_json() {
        // AttrKeyRanking(FromJsonString(Lit text)) -- the swap-site
        // ranking Term (see term.rs's own eval-correctness unit tests for
        // the walk/sort semantics; this pins the to_json/from_json arms).
        let mut a = TermArena::new();
        let mut i = Interner::new();
        let text = a.add(TermNode::Lit { value: Value::Str(i.intern(r#"{"type":"Attr","key":"row"}"#)) });
        let tree = a.add(TermNode::FromJsonString { text });
        let ranking = a.add(TermNode::AttrKeyRanking { tree });

        let j = term_to_json(&a, ranking, &i);
        let mut a2 = TermArena::new();
        let mut i2 = Interner::new();
        let rebuilt = term_from_json(&j, &mut a2, &mut i2).unwrap();
        let j2 = term_to_json(&a2, rebuilt, &i2);
        assert_eq!(j, j2);
        assert_eq!(j["type"], "AttrKeyRanking");
        assert_eq!(j["tree"]["type"], "FromJsonString");
        assert!(matches!(a2.get(rebuilt), TermNode::AttrKeyRanking { .. }));
    }

    #[test]
    fn track_identity_correspondence_round_trips_via_json() {
        // GRAPH LAW #6: exercises the to_json/from_json arms for the
        // trans-frame identity Term, both WITH category_key/extent_key
        // present (Some) and absent (None) -- the Option<Sym> encoding
        // (null on the wire) is the novel bit vs. the other Sym fields.
        let mut a = TermArena::new();
        let mut i = Interner::new();
        let prev = a.add(TermNode::SetT { items: vec![] });
        let cur = a.add(TermNode::SetT { items: vec![] });
        let radius = a.add(TermNode::Lit { value: Value::Float(2.5) });
        let term = a.add(TermNode::TrackIdentityCorrespondence {
            prev, cur,
            feature_key: i.intern("feat"),
            category_key: Some(i.intern("cat")),
            extent_key: Some(i.intern("extent")),
            radius,
        });

        let j = term_to_json(&a, term, &i);
        assert_eq!(j["type"], "TrackIdentityCorrespondence");
        assert_eq!(j["feature_key"], "feat");
        assert_eq!(j["category_key"], "cat");
        assert_eq!(j["extent_key"], "extent");
        assert_eq!(j["radius"]["type"], "Lit");

        let mut a2 = TermArena::new();
        let mut i2 = Interner::new();
        let rebuilt = term_from_json(&j, &mut a2, &mut i2).unwrap();
        let j2 = term_to_json(&a2, rebuilt, &i2);
        assert_eq!(j, j2);
        let TermNode::TrackIdentityCorrespondence { category_key, extent_key, .. } = a2.get(rebuilt) else {
            panic!("expected TrackIdentityCorrespondence")
        };
        assert_eq!(i2.resolve(category_key.unwrap()), "cat");
        assert_eq!(i2.resolve(extent_key.unwrap()), "extent");

        // Absent case: category_key/extent_key both None -> null on the
        // wire -> None on the way back.
        let term_none = a.add(TermNode::TrackIdentityCorrespondence {
            prev, cur, feature_key: i.intern("feat2"), category_key: None, extent_key: None, radius,
        });
        let j3 = term_to_json(&a, term_none, &i);
        assert_eq!(j3["category_key"], serde_json::Value::Null);
        assert_eq!(j3["extent_key"], serde_json::Value::Null);
        let rebuilt3 = term_from_json(&j3, &mut a2, &mut i2).unwrap();
        let TermNode::TrackIdentityCorrespondence { category_key: ck3, extent_key: ek3, .. } = a2.get(rebuilt3) else {
            panic!("expected TrackIdentityCorrespondence")
        };
        assert!(ck3.is_none());
        assert!(ek3.is_none());
    }

    #[test]
    fn grammar_round_trips_with_weighted_production() {
        use crate::grammar::{NodePattern, Production};
        let mut a = TermArena::new();
        let mut i = Interner::new();
        let alive = i.intern("AliveCell");
        let adj = i.intern("adjacent_to");
        let src_var = i.intern("src");
        let tgt_var = i.intern("tgt");
        let prov = i.intern("test:default");
        // Default weight (Lit 1.0) — serialisation should omit it (null
        // on the wire).
        let mut g = Grammar::new();
        let w_default = Grammar::default_weight(&mut a);
        g.add(Production {
            src: NodePattern { type_: alive, var: src_var },
            edge_type: adj,
            tgt: NodePattern { type_: alive, var: tgt_var },
            where_: None,
            weight: w_default,
            provenance: prov,
        });
        // Non-default weight.
        let w_25 = a.add(TermNode::Lit { value: Value::Float(2.5) });
        g.add(Production {
            src: NodePattern { type_: alive, var: src_var },
            edge_type: adj,
            tgt: NodePattern { type_: alive, var: tgt_var },
            where_: None,
            weight: w_25,
            provenance: i.intern("test:weighted"),
        });

        let j = grammar_to_json(&g, &a, &i);
        // Round-trip
        let mut a2 = TermArena::new();
        let mut i2 = Interner::new();
        let g2 = grammar_from_json(&j, &mut a2, &mut i2).unwrap();
        assert_eq!(g2.productions.len(), 2);
        // First production: weight should evaluate to 1.0
        // (default_weight). Second: 2.5.
        match a2.get(g2.productions[0].weight) {
            TermNode::Lit { value: Value::Float(f) } => assert_eq!(*f, 1.0),
            other => panic!("expected Lit(1.0) for default weight, got {:?}", other),
        }
        match a2.get(g2.productions[1].weight) {
            TermNode::Lit { value: Value::Float(f) } => assert_eq!(*f, 2.5),
            other => panic!("expected Lit(2.5) for explicit weight, got {:?}", other),
        }
    }

    #[test]
    fn unknown_variant_errors() {
        let mut a = TermArena::new();
        let mut i = Interner::new();
        let j = json!({"type": "BogusTerm"});
        let r = term_from_json(&j, &mut a, &mut i);
        assert!(matches!(r, Err(JsonError::UnknownTermType(_))));
    }
}
