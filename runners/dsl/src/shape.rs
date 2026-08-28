//! Shape — the structural classification of a Term-tree, cached.
//!
//! Implements the function_shape Mt (seeds/function_shape.json,
//! v0.3.0). The vocabulary's THEN clauses name the requirements:
//!
//! - **every_function_admits_three_classification_axes**:
//!   `recursion_axis`, `order_n_axis`, `abstraction_axis` (the three
//!   fields of `Shape`).
//! - **function_identity_is_its_shape_not_its_return_value**: a
//!   function's identity for reasoning is its Shape, not its evaluated
//!   value. The `Shape` struct hashes structurally so two Term-trees
//!   with the same shape compare equal.
//! - **cached_shape_is_required_by_l6_bounded_coordination_latency**:
//!   shape lookups MUST be O(1) within the L6 tick period. `ShapeCache`
//!   is `FxHashMap<TermIdx, Shape>` — constant-time get/insert.
//! - **shape_keyed_lookup_is_memo_function_cache_hit**: the cache hit
//!   path returns without re-walking the Term-tree (Michie 1968).
//! - **cached_shape_inherits_semantics_from_memo_function**: the
//!   function CARRIES its shape — the Term-tree is keyed in the cache
//!   by its `TermIdx`, so the arena's stable indices are the carry.
//! - **shape_mismatch_prunes_negative_problem_space**: the
//!   `shapes_compatible` predicate is the substrate's pruning primitive
//!   (Cousot 1977 + Ashby variety match at L6).
//!
//! Per CLAUDE.md: this is Rust + graph data. The cache lives in Rust;
//! the substrate's reasoning over Shapes happens via Rules on Shape
//! nodes (added by a downstream seed).
//!
//! What this module does NOT do (yet, intentionally):
//! - Climb the reflective tower (meta_shape is one rung up — Smith
//!   1982). The walker assesses one Term-tree at a time; recursive
//!   application of order-N to the assessment itself
//!   (`function_shape_assessment_is_itself_a_function`) is a follow-up.
//! - Cross-Term recursion analysis. A Term-tree can call into Concepts
//!   (Holds) which resolve to other Term-trees; the current walker
//!   classifies recursion at the syntactic level. Full inter-term
//!   recursion analysis needs a `ConceptResolver` walk.
//! - Higher-order detection beyond function-typed variables. Genuine
//!   HOF detection needs a type system; for now we approximate via
//!   whether any Var binds to a TermIdx (rather than a Value).

use rustc_hash::FxHashMap;

use crate::graph::NodeID;
use crate::substrate::Substrate;
use crate::sym::{Interner, Sym};
use crate::term::{TermArena, TermIdx, TermNode};
use crate::value::Value;

// --- The three classification axes (function_shape Mt) ---

/// `recursion_axis` from function_shape Mt. Values from the vocabulary:
/// "none, direct, indirect, mutual, structural".
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum RecursionKind {
    /// No self-reference. The Term-tree is purely compositional.
    None,
    /// Term refers to itself via a Var bound in its own body (fold
    /// accumulator, Filter predicate that re-evaluates over the same
    /// source). Direct self-recursion at the syntactic level.
    Direct,
    /// Term recurses on its own structural arguments (a fold whose body
    /// recurses on the bound element). Distinct from direct because the
    /// recursion is on a STRUCTURALLY smaller argument — terminating by
    /// structural induction.
    Structural,
}

/// `order_n_axis` — the finite-difference structure / nesting depth
/// of fold-like reductions. Inherits from Pearlmutter & Siskind 2007
/// higher-order AD: order-N is D applied N times. For a Term-tree this
/// is the maximum nesting depth of {Fold, Sum, Prod, Argmax, Argmin,
/// MinOver, MaxOver, Count, Filter, Exists}.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct OrderN(pub u8);

/// `abstraction_axis` — whether the Term parametrises over a function
/// (HOF) vs over values only. Smith 1982 reflective tower: a HOF is one
/// rung up.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum AbstractionKind {
    /// Parametrises only over values (Vars + literals). The base case.
    Concrete,
    /// Body references variables that themselves resolve to Term-trees
    /// (fold body, Filter predicate, etc. — bodies that are themselves
    /// composable). One rung up the tower.
    Parametric,
}

/// `function_shape`: the structural identity of a Term-tree. Compared
/// structurally for use as a cache key for the three-axis classification.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct Shape {
    pub recursion: RecursionKind,
    pub order_n: OrderN,
    pub abstraction: AbstractionKind,
}

impl Shape {
    /// `function_identity_is_its_shape_not_its_return_value`: two
    /// Term-trees with the same shape are EQUIVALENT for substrate
    /// reasoning purposes, regardless of evaluation result.
    pub const fn new(
        recursion: RecursionKind,
        order_n: OrderN,
        abstraction: AbstractionKind,
    ) -> Self {
        Self {
            recursion,
            order_n,
            abstraction,
        }
    }

    /// Encode this Shape as graph node attributes. The substrate's Rule
    /// engine reasons over graph data; a Shape held as a node lets
    /// Rules dispatch on its axes via Attr(node, "recursion") etc.
    /// (function_shape_is_observed_by_l6_second_order_observation —
    /// the Shape's classification IS what the substrate's L6 monitoring
    /// channel reads.)
    pub fn to_attrs(self, interner: &mut Interner) -> FxHashMap<Sym, Value> {
        let mut attrs = FxHashMap::default();
        attrs.insert(
            interner.intern("recursion"),
            Value::Str(interner.intern(self.recursion.as_str())),
        );
        attrs.insert(
            interner.intern("order_n"),
            Value::Int(self.order_n.0 as i64),
        );
        attrs.insert(
            interner.intern("abstraction"),
            Value::Str(interner.intern(self.abstraction.as_str())),
        );
        attrs
    }

    /// Decode a Shape from a graph node's attribute store. Pair with
    /// `to_attrs`. Returns None when any axis is missing or malformed
    /// — partial Shape nodes are rejected so downstream code can rely
    /// on every returned Shape being complete.
    pub fn from_attrs(interner: &Interner, attrs: &crate::graph::Attrs) -> Option<Self> {
        let recursion_sym = interner.lookup("recursion")?;
        let order_sym = interner.lookup("order_n")?;
        let abstraction_sym = interner.lookup("abstraction")?;
        let Value::Str(rec_str_sym) = attrs.get(&recursion_sym)? else {
            return None;
        };
        let Value::Int(order_i) = attrs.get(&order_sym)? else {
            return None;
        };
        let Value::Str(abs_str_sym) = attrs.get(&abstraction_sym)? else {
            return None;
        };
        Some(Self {
            recursion: RecursionKind::from_str(interner.resolve(*rec_str_sym))?,
            order_n: OrderN(u8::try_from(*order_i).ok()?),
            abstraction: AbstractionKind::from_str(interner.resolve(*abs_str_sym))?,
        })
    }
}

impl RecursionKind {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::None => "none",
            Self::Direct => "direct",
            Self::Structural => "structural",
        }
    }
    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "none" => Some(Self::None),
            "direct" => Some(Self::Direct),
            "structural" => Some(Self::Structural),
            _ => None,
        }
    }
}

impl AbstractionKind {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Concrete => "concrete",
            Self::Parametric => "parametric",
        }
    }
    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "concrete" => Some(Self::Concrete),
            "parametric" => Some(Self::Parametric),
            _ => None,
        }
    }
}

/// Add a `Shape` node to the substrate's graph and return its NodeID.
/// The node's type is "Shape" and its attributes encode the three axes
/// per `Shape::to_attrs`. Use when a Rule needs to reason about the
/// Shape (e.g. via Filter over `Shape` nodes whose `order_n > 1`).
pub fn add_shape_node(substrate: &mut Substrate, shape: Shape) -> NodeID {
    let type_sym = substrate.interner.intern("Shape");
    let attrs = shape.to_attrs(&mut substrate.interner);
    substrate.add_node(type_sym, attrs)
}

/// Look up the Shape encoded on an existing graph node. Returns None if
/// the node attrs are incomplete or malformed.
pub fn read_shape_node(substrate: &Substrate, nid: NodeID) -> Option<Shape> {
    if !substrate.graph.has_node(nid) {
        return None;
    }
    let attrs = &substrate.graph.node(nid).attrs;
    Shape::from_attrs(&substrate.interner, attrs)
}

// --- The cache (Michie 1968 / L6 bounded coordination latency) ---

/// `cached_shape`: the substrate's memo-function cache for Shape.
/// Keyed by TermIdx because the arena's indices are stable per
/// Term-tree. Hash lookup is O(1).
#[derive(Default, Clone, Debug)]
pub struct ShapeCache {
    entries: FxHashMap<TermIdx, Shape>,
}

impl ShapeCache {
    pub fn new() -> Self {
        Self::default()
    }

    /// `shape_keyed_lookup_is_memo_function_cache_hit`: O(1) lookup,
    /// no Term-tree re-evaluation. None on miss; pair with
    /// `assess_and_cache` to compute + insert.
    pub fn get(&self, idx: TermIdx) -> Option<Shape> {
        self.entries.get(&idx).copied()
    }

    pub fn insert(&mut self, idx: TermIdx, shape: Shape) {
        self.entries.insert(idx, shape);
    }

    /// `memoisation_lifts_from_runtime_to_reasoning`: if cached, return
    /// instantly; else walk the arena, classify, cache, return. The
    /// caller's downstream cost is amortised across all uses of the
    /// same Term-tree.
    pub fn assess_and_cache(&mut self, idx: TermIdx, arena: &TermArena) -> Shape {
        if let Some(s) = self.get(idx) {
            return s;
        }
        let shape = assess_shape(idx, arena);
        self.insert(idx, shape);
        shape
    }

    pub fn len(&self) -> usize {
        self.entries.len()
    }
    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }
}

// --- The walker ---

/// `function_shape_assessment_is_itself_a_function` — assess the shape
/// of a Term-tree by walking it once. The three axes are computed in
/// one pass: recursion via Var-tracking against the root, order_n via
/// max nesting depth, abstraction via presence of parametric bodies.
pub fn assess_shape(idx: TermIdx, arena: &TermArena) -> Shape {
    let mut s = WalkState::default();
    walk(idx, arena, &mut s, 0);
    Shape {
        recursion: s.recursion(),
        order_n: OrderN(s.max_order),
        abstraction: if s.has_parametric_body {
            AbstractionKind::Parametric
        } else {
            AbstractionKind::Concrete
        },
    }
}

/// `negative_problem_space_pruning_combines_cousot_lattice_with_nelson_narens
/// _control`: given a target shape + a slice of candidate Term-tree
/// indices, return only the ones whose Shape is compatible with the
/// target. Computes each candidate's shape via the substrate's cache —
/// repeat calls on the same candidates pay no per-walker cost.
///
/// This is the substrate's pruning primitive. Callers (rule engine,
/// dispatch, evaluation) use it to skip candidates without evaluating
/// them — the cost saving the vocabulary's
/// `shape_mismatch_prunes_negative_problem_space` rule names.
pub fn prune_candidates_by_shape(
    candidates: &[TermIdx],
    target: &Shape,
    substrate: &mut Substrate,
) -> Vec<TermIdx> {
    candidates
        .iter()
        .copied()
        .filter(|idx| {
            let s = substrate.shape_of_term(*idx);
            shapes_compatible(&s, target)
        })
        .collect()
}

/// `meta_shape_is_one_rung_up_l6_circular_causality`: apply the order-N
/// operator to a Shape, yielding its meta_shape — the Shape one rung up
/// the Smith reflective tower (Smith 1982).
///
/// Per the vocabulary's `applying_order_n_to_a_function_yields_meta_shape`:
/// if `f` has shape `S = {recursion, order_n, abstraction}`, then the
/// result of applying the order-N operator to `f` (treating `f` itself
/// as a function from input domain to output) has the meta_shape:
///
///   meta_shape(S) = {
///     recursion:    S.recursion       (preserved — climbing doesn't
///                                       change the underlying recursive
///                                       structure)
///     order_n:      S.order_n + 1     (D applied once more, per
///                                       Pearlmutter-Siskind D^n)
///     abstraction:  Parametric        (climbing always parametricises:
///                                       the meta-level always takes
///                                       the object-level function as
///                                       input — Smith 3-LISP reify)
///   }
///
/// Repeated application climbs further:
///   `meta_shape(meta_shape(S)).order_n == S.order_n + 2`
///
/// This is the calculus form of L6's `circular_causality_between_layers`
/// invariant: each application crosses one layer boundary and exposes
/// the level below to the level above.
pub fn meta_shape(shape: Shape) -> Shape {
    Shape {
        recursion: shape.recursion,
        order_n: OrderN(shape.order_n.0.saturating_add(1)),
        abstraction: AbstractionKind::Parametric,
    }
}

/// Climb the reflective tower N rungs. Equivalent to applying
/// `meta_shape` N times; saturates at u8::MAX to prevent overflow on
/// deep climbs (the cap is well above any practical tower depth).
pub fn climb_tower(shape: Shape, rungs: u8) -> Shape {
    let mut s = shape;
    for _ in 0..rungs {
        s = meta_shape(s);
    }
    s
}

/// `shape_mismatch_prunes_negative_problem_space`: the predicate that
/// drives `negative_problem_space_pruning`. A candidate shape is
/// compatible with a target shape when the candidate could produce the
/// target — currently a structural-equality check on each axis (target
/// kind ⊆ candidate kind). Generalisable to a lattice order
/// (Cousot 1977 + L6 Ashby variety match) when the axes get richer.
pub fn shapes_compatible(candidate: &Shape, target: &Shape) -> bool {
    if candidate.recursion != target.recursion {
        return false;
    }
    if candidate.order_n.0 < target.order_n.0 {
        return false;
    }
    // abstraction: Parametric can satisfy Concrete (HOF specialised to
    // value), but Concrete cannot satisfy Parametric.
    match (candidate.abstraction, target.abstraction) {
        (AbstractionKind::Concrete, AbstractionKind::Parametric) => false,
        _ => true,
    }
}

// --- internals ---

#[derive(Default)]
struct WalkState {
    max_order: u8,
    has_parametric_body: bool,
    has_var_in_body: bool,
    has_structural_recursion: bool,
}

impl WalkState {
    fn recursion(&self) -> RecursionKind {
        if self.has_structural_recursion {
            RecursionKind::Structural
        } else if self.has_var_in_body {
            RecursionKind::Direct
        } else {
            RecursionKind::None
        }
    }
}

fn walk(idx: TermIdx, arena: &TermArena, s: &mut WalkState, depth: u8) {
    let node = arena.get(idx);
    let order_here = depth_bump_for(node);
    // jabberwock change 2 (stretch): track syntactic compositional
    // depth for non-fold structural variants (Plus / Times / Eq /
    // Holds / etc.). Without this, every grounded equation Term-tree
    // collapses to `order_n = 0` because folds dominate the axis and
    // pure-arithmetic / Holds chains never bump. Equation depth IS
    // the substrate's compositional "order" for grounded postulates;
    // counting it lets the abstract-domain partition the donor space.
    //
    // Folds still get their full Pearlmutter-Siskind D^n bump (each
    // fold = one rung up). Structural composition variants get a 1
    // bump per nesting level. Leaves (Var / Lit / Surface) get 0.
    let struct_here = structural_depth_bump_for(node);
    let bump = order_here.max(struct_here);
    if bump > 0 {
        let new_depth = depth.saturating_add(bump);
        if new_depth > s.max_order {
            s.max_order = new_depth;
        }
        if order_here > 0 {
            // a fold-like reduction with a body that references Vars is
            // the parametric case (Smith one-rung-up)
            if is_parametric(node) {
                s.has_parametric_body = true;
            }
            if has_var_in_body(node, arena) {
                s.has_var_in_body = true;
                // a fold body that references the bound element on a
                // structurally smaller argument is structural recursion
                if uses_bound_var(node, arena) {
                    s.has_structural_recursion = true;
                }
            }
        }
        // jabberwock change 2: detect STRUCTURAL recursion across
        // siblings in a composition node — Times(Holds(c1, x),
        // Holds(c2, x)) re-applies the SAME Term-shape (Holds-by-var)
        // to multiple arguments. That's the substrate's syntactic
        // analogue of fold-body-uses-bound-var: the same function-tree
        // pattern recurs across the composition's children.
        if !s.has_structural_recursion
            && struct_here > 0
            && has_sibling_pattern_recurrence(node, arena)
        {
            s.has_structural_recursion = true;
        }
        for child in children(node) {
            walk(child, arena, s, depth + bump);
        }
    } else {
        for child in children(node) {
            walk(child, arena, s, depth);
        }
    }
}

fn depth_bump_for(node: &TermNode) -> u8 {
    matches!(
        node,
        TermNode::Fold { .. }
            | TermNode::Sum { .. }
            | TermNode::Prod { .. }
            | TermNode::Argmax { .. }
            | TermNode::Argmin { .. }
            | TermNode::ArgminUnique { .. }
            | TermNode::MaxOver { .. }
            | TermNode::MinOver { .. }
            | TermNode::Count { .. }
            | TermNode::Filter { .. }
            | TermNode::Exists { .. }
    ) as u8
}

/// jabberwock change 2 (stretch): structural compositional bump for the
/// non-fold variants that make up grounded-equation Term-trees. Each
/// nesting level counts 1. Leaves (Var, Lit, Surface) bump 0 so a
/// trivial Lit stays at order_n = 0. Eq / arithmetic / Holds / boolean
/// composition all count — this is what differentiates the 90 grounded
/// donors from a flat Eq(Lit, Lit).
fn structural_depth_bump_for(node: &TermNode) -> u8 {
    use TermNode::*;
    matches!(
        node,
        Eq { .. }
            | Lt { .. }
            | Lte { .. }
            | Gt { .. }
            | Gte { .. }
            | Plus { .. }
            | Times { .. }
            | Minus { .. }
            | Div { .. }
            | Mod { .. }
            | Pow { .. }
            | IDiv { .. }
            | IRem { .. }
            | Abs { .. }
            | Neg { .. }
            | Sqrt { .. }
            | EnclosedCount { .. }
            | Min { .. }
            | Max { .. }
            | ArgMax { .. }
            | And { .. }
            | Or { .. }
            | Not { .. }
            | Holds { .. }
            | IfThenElse { .. }
            | BitAnd { .. }
            | BitOr { .. }
            | BitXor { .. }
            | Shl { .. }
            | Lshr { .. }
            | Ashr { .. }
            | DtwTo { .. }
            | PointSetDist { .. }
            | MahalLeaf { .. }
            | MahalFull { .. }
            | DeformGenMarginal { .. }
            | DeformGen { .. }
            | DeformDist { .. }
            | SmoothDeformDist { .. }
            | TpsDeformDist { .. }
            | SmoothDeformComponents { .. }
            | ShapeContextDist { .. }
            | ScTpsDist { .. }
            | XCorrPeak { .. }
            | EvalSubgraph { .. }
            | Vec_ { .. }
            | SetT { .. }
            | In { .. }
            | TypeOf { .. }
            | Attr { .. }
            | Neighbours { .. }
            | InNeighbours { .. }
            | MapNeighbours { .. }
            | Pick { .. }
    ) as u8
}

/// Cheap variant-tag for a TermNode. Two nodes with the same tag have
/// the same Term constructor — used by `has_sibling_pattern_recurrence`
/// to detect when a composition node's children share a Term-shape
/// (syntactic structural recursion).
fn variant_tag(node: &TermNode) -> u8 {
    use TermNode::*;
    match node {
        Var { .. } => 1,
        Lit { .. } => 2,
        Holds { .. } => 3,
        Plus { .. } => 4,
        Times { .. } => 5,
        Minus { .. } => 6,
        Div { .. } => 7,
        Pow { .. } => 8,
        Eq { .. } => 9,
        Lt { .. } | Lte { .. } | Gt { .. } | Gte { .. } => 10,
        And { .. } => 11,
        Or { .. } => 12,
        Not { .. } => 13,
        Fold { .. } => 14,
        Sum { .. } => 15,
        Prod { .. } => 16,
        Filter { .. } => 17,
        Exists { .. } => 18,
        Argmax { .. } | Argmin { .. } | ArgminUnique { .. } => 19,
        MinOver { .. } | MaxOver { .. } => 20,
        Attr { .. } => 21,
        Neighbours { .. } | InNeighbours { .. } | MapNeighbours { .. } => 22,
        SetT { .. } => 23,
        IfThenElse { .. } => 24,
        _ => 255,
    }
}

/// jabberwock change 2: structural recursion at the syntactic level.
/// A composition node whose children share a Term-tree shape (same
/// variant tag, deeper than a leaf) is re-applying the same
/// function-tree pattern across its arguments — the syntactic analogue
/// of a fold body referencing its bound element on each iteration.
/// Newton's grounded form Times(Holds(mass, x), Holds(acc, x)) trips
/// this: both children are Holds nodes.
fn has_sibling_pattern_recurrence(node: &TermNode, arena: &TermArena) -> bool {
    let ch = children(node);
    if ch.len() < 2 {
        return false;
    }
    let mut seen: Option<u8> = None;
    for c in ch {
        let tag = variant_tag(arena.get(c));
        // Leaves don't count as a recurring pattern — only structural
        // composition variants (Holds, Times, Eq, etc.) do.
        if tag == 1 || tag == 2 || tag == 255 {
            continue;
        }
        if let Some(prev) = seen {
            if prev == tag {
                return true;
            }
        } else {
            seen = Some(tag);
        }
    }
    false
}

fn is_parametric(node: &TermNode) -> bool {
    // every fold-like reducer that takes a body Term is parametric in
    // its body — the body composes over the bound variable.
    matches!(
        node,
        TermNode::Fold { .. }
            | TermNode::Sum { .. }
            | TermNode::Prod { .. }
            | TermNode::Argmax { .. }
            | TermNode::Argmin { .. }
            | TermNode::ArgminUnique { .. }
            | TermNode::MaxOver { .. }
            | TermNode::MinOver { .. }
            | TermNode::Filter { .. }
            | TermNode::Exists { .. }
    )
}

fn has_var_in_body(node: &TermNode, arena: &TermArena) -> bool {
    // any body TermIdx that contains a Var
    let body_idx = match node {
        TermNode::Fold { body, .. } => Some(*body),
        TermNode::Sum { value, .. }
        | TermNode::Prod { value, .. }
        | TermNode::Argmax { value, .. }
        | TermNode::Argmin { value, .. }
        | TermNode::ArgminUnique { value, .. }
        | TermNode::MaxOver { value, .. }
        | TermNode::MinOver { value, .. } => Some(*value),
        TermNode::Filter { predicate, .. } | TermNode::Exists { predicate, .. } => Some(*predicate),
        _ => None,
    };
    body_idx.is_some_and(|i| contains_var(i, arena))
}

fn uses_bound_var(node: &TermNode, arena: &TermArena) -> bool {
    // a fold-body that references the LOOP's bound variable name (the
    // var_name on the reducer) is structurally recursive: the body
    // re-runs on each element.
    let (var_name, body_idx) = match node {
        TermNode::Fold { var_name, body, .. } => (*var_name, *body),
        TermNode::Sum {
            var_name, value, ..
        }
        | TermNode::Prod {
            var_name, value, ..
        }
        | TermNode::Argmax {
            var_name, value, ..
        }
        | TermNode::Argmin {
            var_name, value, ..
        }
        | TermNode::ArgminUnique {
            var_name, value, ..
        }
        | TermNode::MaxOver {
            var_name, value, ..
        }
        | TermNode::MinOver {
            var_name, value, ..
        } => (*var_name, *value),
        TermNode::Filter {
            var_name,
            predicate,
            ..
        }
        | TermNode::Exists {
            var_name,
            predicate,
            ..
        } => (*var_name, *predicate),
        _ => return false,
    };
    references_var(body_idx, arena, var_name)
}

fn contains_var(idx: TermIdx, arena: &TermArena) -> bool {
    let n = arena.get(idx);
    if matches!(n, TermNode::Var { .. }) {
        return true;
    }
    children(n).iter().any(|c| contains_var(*c, arena))
}

fn references_var(idx: TermIdx, arena: &TermArena, var_name: crate::sym::Sym) -> bool {
    let n = arena.get(idx);
    if let TermNode::Var { name } = n {
        return *name == var_name;
    }
    children(n)
        .iter()
        .any(|c| references_var(*c, arena, var_name))
}

fn children(node: &TermNode) -> Vec<TermIdx> {
    use TermNode::*;
    match node {
        Var { .. } | Lit { .. } => vec![],
        TypeOf { node } => vec![*node],
        Attr { node, .. } => vec![*node],
        SetT { items } => items.clone(),
        In { member, container } => vec![*member, *container],
        Eq { a, b } | Lt { a, b } | Lte { a, b } | Gt { a, b } | Gte { a, b } => vec![*a, *b],
        Neighbours { node, .. }
        | InNeighbours { node, .. }
        | MapNeighbours { source: node, .. } => vec![*node],
        Count { source } => vec![*source],
        Filter {
            source, predicate, ..
        }
        | Exists {
            source, predicate, ..
        } => vec![*source, *predicate],
        Sum { source, value, .. } | Prod { source, value, .. } => vec![*source, *value],
        MinOver {
            source,
            value,
            default,
            ..
        }
        | MaxOver {
            source,
            value,
            default,
            ..
        } => {
            let mut v = vec![*source, *value];
            if let Some(d) = default {
                v.push(*d);
            }
            v
        }
        Argmax {
            source,
            value,
            default,
            ..
        }
        | ArgminUnique {
            source,
            value,
            default,
            ..
        }
        | Argmin {
            source,
            value,
            default,
            ..
        } => {
            let mut v = vec![*source, *value];
            if let Some(d) = default {
                v.push(*d);
            }
            v
        }
        Pick { source } => vec![*source],
        Fold {
            source, init, body, ..
        } => vec![*source, *init, *body],
        // --- arithmetic / Holds / boolean variants ---
        // jabberwock change 2: recurse into the grounded-equation Term
        // structure (Plus/Times/Minus/Div/Pow/Holds + And/Or/Not for
        // composed predicates) so the Shape walker actually traverses
        // the depth of equation Term-trees like
        //   Eq(Holds(force, x), Times(Holds(mass, x), Holds(acc, x)))
        // Without this the abstract-domain axes (recursion / order_n /
        // abstraction) collapse all 90 grounded donors to the same
        // {none, 0, concrete} bucket — the walker never sees what the
        // tree contains below the top Eq.
        Plus { items }
        | Times { items }
        | Min { items }
        | Max { items }
        | ArgMax { items }
        | And { items }
        | Or { items }
        | Vec_ { items } => items.clone(),
        UseTool { args, .. } => args.clone(),
        Minus { a, b }
        | Div { a, b }
        | Mod { a, b }
        | Pow { a, b }
        | IDiv { a, b }
        | IRem { a, b }
        | BitAnd { a, b }
        | BitOr { a, b }
        | BitXor { a, b }
        | Shl { a, b }
        | Lshr { a, b }
        | Ashr { a, b }
        | DtwTo { a, b }
        | PointSetDist { a, b }
        | MahalLeaf { a, b }
        | MahalFull { a, b }
        | DeformGenMarginal { a, b }
        | DeformGen { a, b }
        | DeformDist { a, b }
        | SmoothDeformDist { a, b }
        | TpsDeformDist { a, b }
        | SmoothDeformComponents { a, b }
        | ShapeContextDist { a, b }
        | ScTpsDist { a, b }
        | XCorrPeak { a, b }
        | Whiten { a, b }
        | WhitenMany { a, b }
        | WithinScatter { a, b }
        | BetweenScatter { a, b } => vec![*a, *b],
        Abs { arg } | Neg { arg } | Sqrt { arg } | Not { arg } | EnclosedCount { arg } => {
            vec![*arg]
        }
        IfThenElse { cond, then, other } => vec![*cond, *then, *other],
        Holds { node, node2, .. } => {
            let mut v = Vec::with_capacity(2);
            if let Some(n) = node {
                v.push(*n);
            }
            if let Some(n) = node2 {
                v.push(*n);
            }
            v
        }
        EvalSubgraph { node } => vec![*node],
        // For variants this module hasn't classified yet (codec
        // primitives, etc.), return empty children — they don't
        // contribute to order/recursion/abstraction at this
        // granularity. Extending the walker is a follow-up commit
        // when a use case names a specific variant's contribution.
        _ => vec![],
    }
}

// --- tests ---

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sym::Interner;
    use crate::value::Value;

    #[test]
    fn empty_shape_compares_concrete_order_zero_none() {
        let mut arena = TermArena::new();
        let idx = arena.add(TermNode::Lit {
            value: Value::Int(42),
        });
        let s = assess_shape(idx, &arena);
        assert_eq!(s.recursion, RecursionKind::None);
        assert_eq!(s.order_n, OrderN(0));
        assert_eq!(s.abstraction, AbstractionKind::Concrete);
    }

    #[test]
    fn fold_lifts_order_to_one_and_is_parametric() {
        let mut arena = TermArena::new();
        let mut sym = Interner::new();
        let src = arena.add(TermNode::Lit { value: Value::None });
        let init = arena.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let x = sym.intern("x");
        let acc = sym.intern("a");
        let body = arena.add(TermNode::Var { name: x });
        let fold = arena.add(TermNode::Fold {
            source: src,
            var_name: x,
            acc_name: acc,
            init,
            body,
        });
        let s = assess_shape(fold, &arena);
        assert_eq!(s.order_n, OrderN(1));
        assert_eq!(s.abstraction, AbstractionKind::Parametric);
        // body references the BOUND var x → structural recursion
        assert_eq!(s.recursion, RecursionKind::Structural);
    }

    #[test]
    fn nested_folds_lift_order_to_two() {
        let mut arena = TermArena::new();
        let mut sym = Interner::new();
        let src = arena.add(TermNode::Lit { value: Value::None });
        let init = arena.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let x = sym.intern("x");
        let y = sym.intern("y");
        let acc = sym.intern("a");
        let inner_body = arena.add(TermNode::Var { name: y });
        let inner_fold = arena.add(TermNode::Fold {
            source: src,
            var_name: y,
            acc_name: acc,
            init,
            body: inner_body,
        });
        let outer_fold = arena.add(TermNode::Fold {
            source: src,
            var_name: x,
            acc_name: acc,
            init,
            body: inner_fold,
        });
        let s = assess_shape(outer_fold, &arena);
        assert_eq!(s.order_n, OrderN(2));
    }

    #[test]
    fn shape_cache_is_o1_on_hit() {
        let mut arena = TermArena::new();
        let idx = arena.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let mut cache = ShapeCache::new();
        let first = cache.assess_and_cache(idx, &arena);
        assert!(cache.get(idx).is_some());
        let second = cache.assess_and_cache(idx, &arena);
        assert_eq!(first, second);
        assert_eq!(cache.len(), 1);
    }

    #[test]
    fn shape_identity_is_structural_not_value() {
        let mut arena = TermArena::new();
        let a = arena.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let b = arena.add(TermNode::Lit {
            value: Value::Int(999),
        });
        let sa = assess_shape(a, &arena);
        let sb = assess_shape(b, &arena);
        assert_eq!(sa, sb);
    }

    #[test]
    fn substrate_caches_shape_of_term() {
        use crate::checker::ConsistencyChecker;
        use crate::grammar::Grammar;
        let mut substrate = Substrate::new(ConsistencyChecker::new(Grammar::new()));
        // Build a Fold via the substrate's own arena so the cache is
        // exercised end-to-end.
        let src = substrate.terms.add(TermNode::Lit { value: Value::None });
        let init = substrate.terms.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let x = substrate.interner.intern("x");
        let acc = substrate.interner.intern("a");
        let body = substrate.terms.add(TermNode::Var { name: x });
        let fold = substrate.terms.add(TermNode::Fold {
            source: src,
            var_name: x,
            acc_name: acc,
            init,
            body,
        });
        // First call: walks + caches.
        let s1 = substrate.shape_of_term(fold);
        // Second call: cache hit, same Shape returned.
        let s2 = substrate.shape_of_term(fold);
        assert_eq!(s1, s2);
        assert_eq!(s1.order_n, OrderN(1));
        assert!(substrate.shape_cache.len() >= 1);
    }

    #[test]
    fn shape_round_trips_through_graph_node() {
        use crate::checker::ConsistencyChecker;
        use crate::grammar::Grammar;
        let mut substrate = Substrate::new(ConsistencyChecker::new(Grammar::new()));
        let shape = Shape::new(
            RecursionKind::Structural,
            OrderN(3),
            AbstractionKind::Parametric,
        );
        let nid = add_shape_node(&mut substrate, shape);
        let recovered =
            read_shape_node(&substrate, nid).expect("Shape node round-trip must succeed");
        assert_eq!(shape, recovered);
    }

    #[test]
    fn prune_candidates_filters_negative_space() {
        use crate::checker::ConsistencyChecker;
        use crate::grammar::Grammar;
        let mut s = Substrate::new(ConsistencyChecker::new(Grammar::new()));

        // 3 candidates: a Lit (order-0 concrete), a single Fold (order-1
        // parametric), a nested Fold (order-2 parametric).
        let lit = s.terms.add(TermNode::Lit {
            value: Value::Int(7),
        });
        let src1 = s.terms.add(TermNode::Lit { value: Value::None });
        let init1 = s.terms.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let x = s.interner.intern("x");
        let acc = s.interner.intern("a");
        let body1 = s.terms.add(TermNode::Var { name: x });
        let fold1 = s.terms.add(TermNode::Fold {
            source: src1,
            var_name: x,
            acc_name: acc,
            init: init1,
            body: body1,
        });
        let body2 = s.terms.add(TermNode::Var { name: x });
        let inner = s.terms.add(TermNode::Fold {
            source: src1,
            var_name: x,
            acc_name: acc,
            init: init1,
            body: body2,
        });
        let fold2 = s.terms.add(TermNode::Fold {
            source: src1,
            var_name: x,
            acc_name: acc,
            init: init1,
            body: inner,
        });

        let candidates = [lit, fold1, fold2];

        // Target: structural recursion, order >= 1, parametric.
        // Compatible: fold1 (exact), fold2 (more structure OK).
        // Excluded: lit (recursion mismatch).
        let target = Shape::new(
            RecursionKind::Structural,
            OrderN(1),
            AbstractionKind::Parametric,
        );
        let kept = prune_candidates_by_shape(&candidates, &target, &mut s);
        assert_eq!(kept.len(), 2);
        assert!(kept.contains(&fold1));
        assert!(kept.contains(&fold2));
        assert!(!kept.contains(&lit));
    }

    #[test]
    fn substrate_skips_rules_in_negative_shape_space() {
        use crate::checker::ConsistencyChecker;
        use crate::grammar::Grammar;
        use crate::rewrite::RewriteRule;
        let mut s = Substrate::new(ConsistencyChecker::new(Grammar::new()));
        let x = s.interner.intern("x");

        // Concrete rule (Lit where-clause — order 0 concrete).
        let concrete_where = s.terms.add(TermNode::Lit {
            value: Value::Bool(true),
        });
        let concrete_name = s.interner.intern("concrete_rule");
        let rule_concrete = RewriteRule {
            name: concrete_name,
            match_edges: vec![],
            where_: Some(concrete_where),
            effects: vec![],
            ..Default::default()
        };
        let idx_concrete = s.add_rule(rule_concrete);

        // Parametric rule (Fold where-clause — order 1 parametric).
        let init = s.terms.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let src = s.terms.add(TermNode::Lit { value: Value::None });
        let body = s.terms.add(TermNode::Var { name: x });
        let parametric_where = s.terms.add(TermNode::Fold {
            source: src,
            var_name: x,
            acc_name: x,
            init,
            body,
        });
        let parametric_name = s.interner.intern("parametric_rule");
        let rule_parametric = RewriteRule {
            name: parametric_name,
            match_edges: vec![],
            where_: Some(parametric_where),
            effects: vec![],
            ..Default::default()
        };
        let idx_parametric = s.add_rule(rule_parametric);

        // No target -> neither rule is in negative space.
        assert!(!s.rule_in_negative_space(idx_concrete));
        assert!(!s.rule_in_negative_space(idx_parametric));

        // Target requires parametric -> concrete is negative space.
        let target = Shape::new(
            RecursionKind::Structural,
            OrderN(1),
            AbstractionKind::Parametric,
        );
        s.set_shape_target(Some(target));
        assert!(s.rule_in_negative_space(idx_concrete));
        assert!(!s.rule_in_negative_space(idx_parametric));

        // apply_rule_once on concrete rule short-circuits + bumps counter.
        let before = s.shape_pruned_count;
        let fired = s.apply_rule_once(idx_concrete);
        assert!(!fired);
        assert_eq!(s.shape_pruned_count, before + 1);
    }

    #[test]
    fn derivation_dispatch_shape_pruned_falls_back_to_native() {
        use crate::checker::ConsistencyChecker;
        use crate::grammar::Grammar;
        use crate::term::{evaluate, Derivation, DerivationRegistry, Env, EvalCtx};
        let mut s = Substrate::new(ConsistencyChecker::new(Grammar::new()));
        // Register a Lte derivation: Lte(a,b) = Not(Gt(a,b))) — but
        // for this test we use the trivially-derived form Lte(a,b) =
        // (a == b) OR (a < b). What MATTERS for the test is that the
        // derivation's Term-tree has a known Shape; we'll check the
        // shape-pruning path uses it.

        let a = s.interner.intern("a");
        let b = s.interner.intern("b");
        let var_a = s.terms.add(TermNode::Var { name: a });
        let var_b = s.terms.add(TermNode::Var { name: b });
        let eq = s.terms.add(TermNode::Eq { a: var_a, b: var_b });
        let lt = s.terms.add(TermNode::Lt { a: var_a, b: var_b });
        // Build Lte body: Or(Eq, Lt) → via SetT containing both, then
        // Exists over the set. Same shape pattern Lte's derivation uses.
        let lte_body = s.terms.add(TermNode::SetT {
            items: vec![eq, lt],
        });
        let lte_sym = s.interner.intern("Lte");
        let mut derivs: DerivationRegistry = rustc_hash::FxHashMap::default();
        derivs.insert(lte_sym, Derivation::ValueTaker(lte_body));

        // The derivation's Shape (Lte body = SetT(Eq, Lt) — no
        // recursion, concrete; order_n counts compositional depth
        // post-jabberwock-change-2: SetT(1) + Eq/Lt(1) = 2).
        let derivation_shape = assess_shape(lte_body, &s.terms);
        assert_eq!(derivation_shape.recursion, RecursionKind::None);
        assert_eq!(derivation_shape.order_n, OrderN(2));
        assert_eq!(derivation_shape.abstraction, AbstractionKind::Concrete);

        // Target requires parametric — the Lte derivation is concrete,
        // so it's incompatible regardless of order. Build an EvalCtx
        // with the target + call lookup_value_taker_def-equivalent
        // logic via dispatch.

        let target = Shape::new(RecursionKind::None, OrderN(1), AbstractionKind::Parametric);

        // Construct an EvalCtx with target + counters + verify the
        // dispatch path skips the derivation. Build a simple Lit term
        // to evaluate (Lits don't use the registry; this test focuses
        // on the lookup_value_taker_def behaviour).
        // Build an Lte call — the registered derivation is the
        // ValueTaker. Without a target, the dispatch picks the
        // derivation; with an incompatible target, it falls back to
        // the kernel.
        let lit_a = s.terms.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let lit_b = s.terms.add(TermNode::Lit {
            value: Value::Int(7),
        });
        let lte_call = s.terms.add(TermNode::Lte { a: lit_a, b: lit_b });

        // Phase 1: no target → derivation dispatch fires; counter doesn't bump.
        let counter_no_target;
        {
            let Substrate {
                graph,
                interner,
                counters,
                terms,
                ..
            } = &mut s;
            let mut env = Env::new();
            let mut ctx = EvalCtx::new(graph, interner)
                .with_counters(counters)
                .with_derivations(&derivs);
            // No with_shape_target — dispatch should use the registered
            // derivation.
            let _ = evaluate(terms, lte_call, &mut env, &mut ctx);
            counter_no_target = ctx.counters.unwrap().derivation_shape_pruned;
        }
        // No pruning happened.
        assert_eq!(counter_no_target, 0);

        // Phase 2: incompatible target → dispatch skips derivation
        // (falls back to kernel); counter bumps.
        let counter_with_target;
        {
            let Substrate {
                graph,
                interner,
                counters,
                terms,
                ..
            } = &mut s;
            let mut env = Env::new();
            let mut ctx = EvalCtx::new(graph, interner)
                .with_counters(counters)
                .with_derivations(&derivs)
                .with_shape_target(target);
            let _ = evaluate(terms, lte_call, &mut env, &mut ctx);
            counter_with_target = ctx.counters.unwrap().derivation_shape_pruned;
        }
        // Pruning fired.
        assert!(
            counter_with_target > counter_no_target,
            "shape_target should have pruned at least one derivation \
                  dispatch; before={} after={}",
            counter_no_target,
            counter_with_target
        );
    }

    #[test]
    fn concept_dispatch_shape_pruned() {
        use crate::checker::ConsistencyChecker;
        use crate::grammar::Grammar;
        use crate::term::{evaluate, ConceptResolver, Env, EvalCtx};
        let mut s = Substrate::new(ConsistencyChecker::new(Grammar::new()));

        // Define a concept with a Lit definition (Shape: none, order 0,
        // concrete).
        let concept_sym = s.interner.intern("my_concept");
        let def = s.terms.add(TermNode::Lit {
            value: Value::Bool(true),
        });
        let mut concepts = ConceptResolver::default();
        concepts.insert(concept_sym, def);

        // Build a Holds call.
        let node = s.terms.add(TermNode::Lit {
            value: Value::Node(crate::graph::NodeID(0)),
        });
        let holds = s.terms.add(TermNode::Holds {
            concept: concept_sym,
            node: Some(node),
            node2: None,
        });

        // Phase 1: no target → concept resolves; counter stays at 0.
        let phase1 = {
            let Substrate {
                graph,
                interner,
                counters,
                terms,
                ..
            } = &mut s;
            let mut env = Env::new();
            let mut ctx = EvalCtx::new(graph, interner)
                .with_counters(counters)
                .with_concepts(&concepts);
            let _ = evaluate(terms, holds, &mut env, &mut ctx);
            ctx.counters.unwrap().concept_shape_pruned
        };
        assert_eq!(phase1, 0);

        // Phase 2: incompatible target → concept pruned, counter bumps.
        let target = Shape::new(
            RecursionKind::Structural,
            OrderN(2),
            AbstractionKind::Parametric,
        );
        let phase2 = {
            let Substrate {
                graph,
                interner,
                counters,
                terms,
                ..
            } = &mut s;
            let mut env = Env::new();
            let mut ctx = EvalCtx::new(graph, interner)
                .with_counters(counters)
                .with_concepts(&concepts)
                .with_shape_target(target);
            let _ = evaluate(terms, holds, &mut env, &mut ctx);
            ctx.counters.unwrap().concept_shape_pruned
        };
        assert!(phase2 > phase1);
    }

    #[test]
    fn shape_filter_terms_helper_filters_by_active_target() {
        use crate::checker::ConsistencyChecker;
        use crate::grammar::Grammar;
        let mut s = Substrate::new(ConsistencyChecker::new(Grammar::new()));

        let lit = s.terms.add(TermNode::Lit {
            value: Value::Int(7),
        });
        let src = s.terms.add(TermNode::Lit { value: Value::None });
        let init = s.terms.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let x = s.interner.intern("x");
        let acc = s.interner.intern("a");
        let body = s.terms.add(TermNode::Var { name: x });
        let fold = s.terms.add(TermNode::Fold {
            source: src,
            var_name: x,
            acc_name: acc,
            init,
            body,
        });
        let candidates = [lit, fold];

        // No active target: returns all.
        let all = s.shape_filter_terms(&candidates);
        assert_eq!(all.len(), 2);

        // With parametric target: only the Fold passes.
        let target = Shape::new(
            RecursionKind::Structural,
            OrderN(1),
            AbstractionKind::Parametric,
        );
        s.set_shape_target(Some(target));
        let filtered = s.shape_filter_terms(&candidates);
        assert_eq!(filtered.len(), 1);
        assert!(filtered.contains(&fold));
        assert!(!filtered.contains(&lit));
    }

    #[test]
    fn shape_cache_threaded_through_evalctx_hits() {
        // The substrate's shape_cache should accumulate entries when
        // threaded through dispatch — verify the cache is populated by
        // evaluate calls that exercise the shape check.
        use crate::checker::ConsistencyChecker;
        use crate::grammar::Grammar;
        use crate::term::{evaluate, Derivation, DerivationRegistry, Env, EvalCtx};
        let mut s = Substrate::new(ConsistencyChecker::new(Grammar::new()));

        // Set up a Lte derivation + active target so the shape check fires.
        let a = s.interner.intern("a");
        let b = s.interner.intern("b");
        let va = s.terms.add(TermNode::Var { name: a });
        let vb = s.terms.add(TermNode::Var { name: b });
        let body = s.terms.add(TermNode::Lt { a: va, b: vb });
        let lte_sym = s.interner.intern("Lte");
        let mut derivs: DerivationRegistry = rustc_hash::FxHashMap::default();
        derivs.insert(lte_sym, Derivation::ValueTaker(body));

        let target = Shape::new(
            RecursionKind::Structural,
            OrderN(2),
            AbstractionKind::Parametric,
        );
        let lit_a = s.terms.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let lit_b = s.terms.add(TermNode::Lit {
            value: Value::Int(7),
        });
        let call = s.terms.add(TermNode::Lte { a: lit_a, b: lit_b });

        // Cache empty before.
        assert_eq!(s.shape_cache.len(), 0);

        {
            let Substrate {
                graph,
                interner,
                counters,
                terms,
                shape_cache,
                ..
            } = &mut s;
            let mut env = Env::new();
            let mut ctx = EvalCtx::new(graph, interner)
                .with_counters(counters)
                .with_derivations(&derivs)
                .with_shape_target(target)
                .with_shape_cache(shape_cache);
            let _ = evaluate(terms, call, &mut env, &mut ctx);
        }

        // Cache populated.
        assert!(
            s.shape_cache.len() >= 1,
            "shape_cache should have at least one entry after threaded dispatch"
        );
    }

    #[test]
    fn run_rules_resets_shape_counters() {
        use crate::checker::ConsistencyChecker;
        use crate::grammar::Grammar;
        let mut s = Substrate::new(ConsistencyChecker::new(Grammar::new()));

        // Seed nonzero counters.
        s.shape_pruned_count = 7;
        s.counters.derivation_shape_pruned = 11;
        s.counters.concept_shape_pruned = 13;

        // run_rules with zero steps still resets at the top.
        s.run_rules(0);
        assert_eq!(s.shape_pruned_count, 0);
        assert_eq!(s.counters.derivation_shape_pruned, 0);
        assert_eq!(s.counters.concept_shape_pruned, 0);

        // Manual reset method too.
        s.shape_pruned_count = 5;
        s.counters.concept_shape_pruned = 3;
        s.reset_shape_counters();
        assert_eq!(s.shape_pruned_count, 0);
        assert_eq!(s.counters.concept_shape_pruned, 0);
    }

    #[test]
    fn meta_shape_climbs_one_rung() {
        // Order increments by 1; abstraction becomes parametric;
        // recursion preserved (Smith 1982 / Pearlmutter-Siskind D).
        let s = Shape::new(RecursionKind::Direct, OrderN(2), AbstractionKind::Concrete);
        let meta = meta_shape(s);
        assert_eq!(meta.recursion, RecursionKind::Direct);
        assert_eq!(meta.order_n, OrderN(3));
        assert_eq!(meta.abstraction, AbstractionKind::Parametric);
    }

    #[test]
    fn tower_climb_composes() {
        // Climbing N rungs == applying meta_shape N times.
        let s = Shape::new(RecursionKind::None, OrderN(0), AbstractionKind::Concrete);
        let three = climb_tower(s, 3);
        assert_eq!(three.order_n, OrderN(3));
        let three_iter = meta_shape(meta_shape(meta_shape(s)));
        assert_eq!(three, three_iter);
    }

    #[test]
    fn meta_shape_of_assessment_function_is_higher_order() {
        // function_shape_assessment_is_itself_a_function: if we represent
        // the assessment as a Term-tree (fold over the arena), its own
        // Shape is order-1 parametric. Applying meta_shape climbs to
        // order-2 — one rung up Smith's reflective tower.
        let mut arena = TermArena::new();
        let mut sym = Interner::new();
        let src = arena.add(TermNode::Lit { value: Value::None });
        let init = arena.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let x = sym.intern("x");
        let acc = sym.intern("a");
        let body = arena.add(TermNode::Var { name: x });
        let assessment_fn = arena.add(TermNode::Fold {
            source: src,
            var_name: x,
            acc_name: acc,
            init,
            body,
        });
        let s = assess_shape(assessment_fn, &arena);
        assert_eq!(s.order_n, OrderN(1));
        let meta = meta_shape(s);
        assert_eq!(meta.order_n, OrderN(2));
        // Climbing applies D again per Pearlmutter-Siskind:
        let meta_meta = meta_shape(meta);
        assert_eq!(meta_meta.order_n, OrderN(3));
    }

    #[test]
    fn shape_mismatch_prunes() {
        // shape_mismatch_prunes_negative_problem_space:
        // a concrete shape cannot satisfy a parametric target.
        let concrete = Shape::new(RecursionKind::None, OrderN(0), AbstractionKind::Concrete);
        let parametric = Shape::new(RecursionKind::None, OrderN(1), AbstractionKind::Parametric);
        assert!(!shapes_compatible(&concrete, &parametric));
        // and an order-1 candidate satisfies an order-0 target (more
        // structure is always permissible).
        let order1 = Shape::new(RecursionKind::None, OrderN(1), AbstractionKind::Parametric);
        let order0 = Shape::new(RecursionKind::None, OrderN(0), AbstractionKind::Concrete);
        assert!(shapes_compatible(&order1, &order0));
    }
}
