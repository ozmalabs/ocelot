//! `NetForward` — the native forward pass of a graph-resident, authored
//! (write-not-train) net. The Rust twin of `code_writing_cortex.py`'s
//! `forward()` (the pure-Python matmul at `forward()`), so a constructed
//! net can be evaluated INSIDE a Rule's `where`/effect at native speed —
//! the "very low cost default path" a reflex net needs to be genuinely
//! free rather than N Python round-trips per tick.
//!
//! ## What it reads (identical layout to `code_writing_cortex.forward`)
//!
//! `assemblage` evaluates to a `NetworkAssemblage` node. Its layers are
//! `-has_step-> AssemblageStep` nodes, walked in `order`-attr order.
//! A step with `dim_behavior == "loss"` is skipped (inference-only path).
//! Each step's `-has_weight-> WeightTensor` nodes carry `role`
//! (`"W1"`/`"b1"`/`"W2"`/`"b2"`) and `data` (the matrix / vector as a
//! nested `Value::Tuple`). A step missing any of the four roles is
//! skipped, exactly as the Python does.
//!
//! Per step: `hidden = ReLU(W1·x + b1)`, `out = W2·hidden + b2`, and the
//! step's output feeds the next step (function composition = layer
//! stacking). The final vector is returned as a `Value::Tuple` of
//! `Value::Float`.
//!
//! ## Purity
//!
//! Read-only over `G`; never mutates the graph (matches the `EvalCtx`
//! contract every Term evaluator obeys). Unresolved symbols (a graph
//! with no `has_step` edges interned at all) yield the input passed
//! through — a graceful identity, never a panic.

use std::sync::Arc;

use smallvec::SmallVec;

use crate::term::{evaluate, Env, EvalCtx, TermArena, TermIdx};
use crate::value::Value;

/// Coerce a scalar `Value` to `f64` (0.0 for non-numeric — matches the
/// Python `float(...)` on well-formed weight data; ill-formed entries
/// degrade to zero rather than crashing the tick).
fn val_f64(v: &Value) -> f64 {
    match v {
        Value::Float(f) => *f,
        Value::Int(i) => *i as f64,
        Value::Bool(b) => {
            if *b {
                1.0
            } else {
                0.0
            }
        }
        _ => 0.0,
    }
}

/// Coerce a list-shaped `Value` (`Tuple`/`Set`/`FrozenSet`) to `Vec<f64>`.
fn val_vec(v: &Value) -> Vec<f64> {
    match v {
        Value::Tuple(t) | Value::List(t) => t.iter().map(val_f64).collect(),
        Value::Set(s) | Value::FrozenSet(s) => s.iter().map(val_f64).collect(),
        _ => Vec::new(),
    }
}

/// Coerce a nested list-shaped `Value` to `Vec<Vec<f64>>` (a matrix).
fn val_mat(v: &Value) -> Vec<Vec<f64>> {
    match v {
        Value::Tuple(t) | Value::List(t) => t.iter().map(val_vec).collect(),
        Value::Set(s) | Value::FrozenSet(s) => s.iter().map(val_vec).collect(),
        _ => Vec::new(),
    }
}

/// Wrap a `Vec<f64>` back into the DSL `Value::Tuple` of `Value::Float`.
fn vec_to_value(x: &[f64]) -> Value {
    let out: SmallVec<[Value; 4]> = x.iter().map(|f| Value::Float(*f)).collect();
    Value::Tuple(Arc::new(out))
}

/// Wrap a `Vec<Vec<f64>>` into a nested `Value::Tuple` (a weight matrix).
fn mat_to_value(m: &[Vec<f64>]) -> Value {
    let rows: SmallVec<[Value; 4]> = m.iter().map(|row| vec_to_value(row)).collect();
    Value::Tuple(Arc::new(rows))
}

#[derive(Clone)]
struct LoadedStep {
    node: crate::graph::NodeID,
    w1: Vec<Vec<f64>>,
    b1: Vec<f64>,
    w2: Vec<Vec<f64>>,
    b2: Vec<f64>,
    w2_node: crate::graph::NodeID,
    b2_node: crate::graph::NodeID,
}

/// Resolve and copy a net's graph-resident weights into a compact execution
/// plan. A scalar call constructs one plan; a batch call constructs ONE plan
/// and reuses it for every row. The graph remains the source of truth.
///
/// `skip_loss` is true for inference, matching `NetForward`. Collapse keeps
/// the historical scalar semantics and considers every ordered step.
fn load_steps(
    graph: &crate::graph::TypedGraph,
    interner: &crate::sym::Interner,
    nid: crate::graph::NodeID,
    skip_loss: bool,
) -> (Vec<LoadedStep>, Option<crate::graph::NodeID>) {
    if !graph.has_node(nid) {
        return (Vec::new(), None);
    }
    let (Some(has_step), Some(has_weight), Some(data_k)) = (
        interner.lookup("has_step"),
        interner.lookup("has_weight"),
        interner.lookup("data"),
    ) else {
        return (Vec::new(), None);
    };
    let order_k = interner.lookup("order");
    let dimb_k = interner.lookup("dim_behavior");
    let role_k = interner.lookup("role");
    let loss_sym = interner.lookup("loss");

    let mut step_nodes = graph.neighbours(nid, Some(has_step));
    step_nodes.sort_by(|&sa, &sb| {
        let oa = order_k
            .and_then(|k| graph.node(sa).attrs.get(&k))
            .map(val_f64)
            .unwrap_or(0.0);
        let ob = order_k
            .and_then(|k| graph.node(sb).attrs.get(&k))
            .map(val_f64)
            .unwrap_or(0.0);
        oa.partial_cmp(&ob).unwrap_or(std::cmp::Ordering::Equal)
    });
    // Collapse historically updates only when the physically last ordered
    // step is complete. Keep that boundary even if earlier steps are skipped.
    let last = step_nodes.last().copied();
    let mut loaded = Vec::with_capacity(step_nodes.len());
    for step in step_nodes {
        if skip_loss {
            if let (Some(dk), Some(ls)) = (dimb_k, loss_sym) {
                if graph.node(step).attrs.get(&dk) == Some(&Value::Str(ls)) {
                    continue;
                }
            }
        }

        let (mut w1, mut b1, mut w2, mut b2) = (None, None, None, None);
        let (mut w2_node, mut b2_node) = (None, None);
        for weight in graph.neighbours(step, Some(has_weight)) {
            let attrs = &graph.node(weight).attrs;
            let role = role_k.and_then(|k| attrs.get(&k));
            let data = attrs.get(&data_k);
            let (Some(Value::Str(rsym)), Some(dv)) = (role, data) else {
                continue;
            };
            match interner.resolve(*rsym) {
                "W1" => w1 = Some(val_mat(dv)),
                "b1" => b1 = Some(val_vec(dv)),
                "W2" => {
                    w2 = Some(val_mat(dv));
                    w2_node = Some(weight);
                }
                "b2" => {
                    b2 = Some(val_vec(dv));
                    b2_node = Some(weight);
                }
                _ => {}
            }
        }
        let (Some(w1), Some(b1), Some(w2), Some(b2), Some(w2_node), Some(b2_node)) =
            (w1, b1, w2, b2, w2_node, b2_node)
        else {
            continue;
        };
        loaded.push(LoadedStep {
            node: step,
            w1,
            b1,
            w2,
            b2,
            w2_node,
            b2_node,
        });
    }
    (loaded, last)
}

fn forward_step(step: &LoadedStep, input: &[f64]) -> (Vec<f64>, Vec<f64>) {
    let mut hidden = Vec::with_capacity(step.w1.len());
    for (r, row) in step.w1.iter().enumerate() {
        let mut sum = step.b1.get(r).copied().unwrap_or(0.0);
        for (c, weight) in row.iter().enumerate() {
            sum += weight * input.get(c).copied().unwrap_or(0.0);
        }
        hidden.push(sum.max(0.0));
    }
    let mut output = Vec::with_capacity(step.w2.len());
    for (r, row) in step.w2.iter().enumerate() {
        let mut sum = step.b2.get(r).copied().unwrap_or(0.0);
        for (c, weight) in row.iter().enumerate() {
            sum += weight * hidden.get(c).copied().unwrap_or(0.0);
        }
        output.push(sum);
    }
    (hidden, output)
}

fn forward_loaded(steps: &[LoadedStep], mut input: Vec<f64>) -> Vec<f64> {
    for step in steps {
        input = forward_step(step, &input).1;
    }
    input
}

/// One SURPRISE-DRIVEN COLLAPSE step of a net's readout — the `WeightTensor`
/// twin of `can_ops::hebbian_update_J`, and the piece that makes a reflex
/// net SELF-TRAINING.
///
/// The net PREDICTS via forward; its SURPRISE is `target − prediction`
/// (meta-shape #33, prediction_minus_observation); and the readout weights
/// COLLAPSE toward reducing that surprise by the local delta rule
/// (`W2 += η·e·hiddenᵀ`, `b2 += η·e`), with `W1`/`b1` the FIXED random-feature
/// layer (ELM-online — local, no backprop, one step per observed
/// (input, target) pair). The last step's `W2`/`b2` `WeightTensor.data` is
/// mutated in place; earlier steps are fixed features fed forward. Returns
/// the surprise magnitude `Σ e²` (which drops toward 0 as the net learns —
/// the same "surprise falls on recurrence" signal `native_collapse` reports
/// for discrete constructs, here for continuous weights).
///
/// This is "collapse and surprise WITHIN the net": the net trains itself
/// from its own prediction error as part of the collapse loop, rather than
/// being fit by an external optimizer.
pub fn net_collapse_step(
    graph: &mut crate::graph::TypedGraph,
    interner: &crate::sym::Interner,
    nid: crate::graph::NodeID,
    input: &[f64],
    target: &[f64],
    eta: f64,
) -> f64 {
    let (mut steps, last) = load_steps(graph, interner, nid, false);
    let surprise = collapse_loaded_one(&mut steps, last, input, target, eta);
    write_collapsed_readout(graph, interner, &steps, last);
    surprise
}

fn collapse_loaded_one(
    steps: &mut [LoadedStep],
    last: Option<crate::graph::NodeID>,
    input: &[f64],
    target: &[f64],
    eta: f64,
) -> f64 {
    let mut x = input.to_vec();
    for step in steps {
        let (hidden, output) = forward_step(step, &x);
        if Some(step.node) == last {
            let error: Vec<f64> = (0..output.len())
                .map(|i| target.get(i).copied().unwrap_or(0.0) - output[i])
                .collect();
            let surprise = error.iter().map(|value| value * value).sum();
            // Normalized local delta update, byte-for-byte the scalar
            // collapse arithmetic. Keeping the loaded readout in memory lets
            // the next row observe precisely the prior row's update.
            let norm = 1.0 + hidden.iter().map(|value| value * value).sum::<f64>();
            let scale = eta / norm;
            for i in 0..step.w2.len() {
                if let Some(err) = error.get(i) {
                    if let Some(bias) = step.b2.get_mut(i) {
                        *bias += scale * err;
                    }
                    for j in 0..step.w2[i].len() {
                        step.w2[i][j] += scale * err * hidden.get(j).copied().unwrap_or(0.0);
                    }
                }
            }
            return surprise;
        }
        x = output;
    }
    0.0
}

fn write_collapsed_readout(
    graph: &mut crate::graph::TypedGraph,
    interner: &crate::sym::Interner,
    steps: &[LoadedStep],
    last: Option<crate::graph::NodeID>,
) {
    let Some(data_k) = interner.lookup("data") else {
        return;
    };
    let Some(step) = steps.iter().find(|step| Some(step.node) == last) else {
        return;
    };
    graph.set_node_attr(step.w2_node, data_k, mat_to_value(&step.w2));
    graph.set_node_attr(step.b2_node, data_k, vec_to_value(&step.b2));
}

/// Ordered online collapse over a batch. This is deliberately NOT a
/// simultaneous gradient reduction: row `i + 1` observes the graph-resident
/// readout after row `i`, exactly as repeated `net_collapse_step` calls do.
/// We load all tensors once, update the compact plan in order, then publish
/// the final readout back to its original `WeightTensor` nodes once.
pub fn net_collapse_batch_ordered(
    graph: &mut crate::graph::TypedGraph,
    interner: &crate::sym::Interner,
    nid: crate::graph::NodeID,
    inputs: &[Vec<f64>],
    targets: &[Vec<f64>],
    eta: f64,
) -> Vec<f64> {
    let (mut steps, last) = load_steps(graph, interner, nid, false);
    let surprises = inputs
        .iter()
        .zip(targets)
        .map(|(input, target)| collapse_loaded_one(&mut steps, last, input, target, eta))
        .collect();
    write_collapsed_readout(graph, interner, &steps, last);
    surprises
}

/// Read a node's list-of-strings attr (e.g. a component's `basin_parts` —
/// the shape-quanta keys it holds jurisdiction over) into a set.
fn str_set_attr(
    graph: &crate::graph::TypedGraph,
    interner: &crate::sym::Interner,
    nid: crate::graph::NodeID,
    key: crate::sym::Sym,
) -> std::collections::HashSet<String> {
    let mut set = std::collections::HashSet::new();
    let items: &[Value] = match graph.node(nid).attrs.get(&key) {
        Some(Value::Tuple(t) | Value::List(t)) => &t[..],
        Some(Value::Set(s)) | Some(Value::FrozenSet(s)) => &s[..],
        _ => return set,
    };
    for v in items {
        if let Value::Str(s) = v {
            set.insert(interner.resolve(*s).to_string());
        }
    }
    set
}

/// The ordered block assemblages of a cascade (`-has_block->`, sorted by the
/// block's `order` attr).
fn cascade_blocks(
    graph: &crate::graph::TypedGraph,
    interner: &crate::sym::Interner,
    cascade: crate::graph::NodeID,
) -> Vec<crate::graph::NodeID> {
    let Some(has_block) = interner.lookup("has_block") else {
        return Vec::new();
    };
    let order_k = interner.lookup("order");
    let mut blocks = graph.neighbours(cascade, Some(has_block));
    blocks.sort_by(|&a, &b| {
        let oa = order_k
            .and_then(|k| graph.node(a).attrs.get(&k))
            .map(val_f64)
            .unwrap_or(0.0);
        let ob = order_k
            .and_then(|k| graph.node(b).attrs.get(&k))
            .map(val_f64)
            .unwrap_or(0.0);
        oa.partial_cmp(&ob).unwrap_or(std::cmp::Ordering::Equal)
    });
    blocks
}

/// `cascade_forward` — the forward pass of a CASCADE net: the SUM of its
/// blocks' `NetForward`s. Each block predicts a piece; the cascade output is
/// their sum (a residual cascade / additive ensemble). Read-only.
pub fn cascade_forward(
    graph: &crate::graph::TypedGraph,
    interner: &crate::sym::Interner,
    cascade: crate::graph::NodeID,
    input: Vec<f64>,
) -> Vec<f64> {
    let mut acc: Vec<f64> = Vec::new();
    for block in cascade_blocks(graph, interner, cascade) {
        let out = net_forward_core(graph, interner, block, input.clone());
        if acc.len() < out.len() {
            acc.resize(out.len(), 0.0);
        }
        for (i, v) in out.iter().enumerate() {
            acc[i] += v;
        }
    }
    acc
}

/// `cascade_collapse_step` — the SELF-TRAINING step of the new net type: a
/// RESIDUAL CASCADE of local-delta blocks, each learning the SURPRISE the
/// previous block could not explain.
///
/// For each block in order: train it (the local NLMS delta rule,
/// `net_collapse_step`) toward the running residual `r` (initially the
/// target); then subtract the block's updated output from `r`, so the NEXT
/// block sees only what remains — `r ← r − blockₖ(x)` is exactly
/// prediction_minus_observation, passed UP the stack. This is online
/// gradient-boosting with local-delta readouts: depth by successive
/// refinement of the residual, every block local + online + no backprop + no
/// external optimizer. Returns the FINAL residual magnitude `Σr²` — the
/// surprise the whole cascade still can't explain, which falls as depth
/// (blocks) or training grows. The complement of the composite (breadth):
/// the cascade is depth / refinement.
pub fn cascade_collapse_step(
    graph: &mut crate::graph::TypedGraph,
    interner: &crate::sym::Interner,
    cascade: crate::graph::NodeID,
    input: &[f64],
    target: &[f64],
    eta: f64,
) -> f64 {
    let blocks = cascade_blocks(graph, interner, cascade);
    let mut r = target.to_vec();
    for block in blocks {
        // Block learns the current residual (the prior blocks' surprise).
        net_collapse_step(graph, interner, block, input, &r, eta);
        // Recompute its (updated) output and pass the remainder up the stack.
        let out = net_forward_core(graph, interner, block, input.to_vec());
        for i in 0..r.len() {
            r[i] -= out.get(i).copied().unwrap_or(0.0);
        }
    }
    r.iter().map(|v| v * v).sum()
}

/// `composite_forward` — the forward pass of a COMPOSITE net: a net nested
/// out of component nets, each a SHAPE specialist. Routing is by GROUNDED
/// shape-residual, NOT a trained gate: each component's jurisdiction is the
/// set of shape-quanta it holds (`basin_parts`); the input's shape-quanta
/// (`sig_keys`) are matched against each, and the component covering the
/// MOST of the input's shape (lowest residual) wins — provided that residual
/// fraction is within its `basin_threshold`. The winner's `NetForward` (its
/// within-shape parametrization) is the output. If NO component covers the
/// input's shape, the composite has no jurisdiction and DEFERS (empty output
/// + component `-1`) — the seam goes to cognition.
///
/// Because a component's jurisdiction is a SHAPE (not a content domain), one
/// component serves every domain that instantiates its shape — a specialist
/// at a shape is a generalist. Returns `(output, chosen_component_id_or_-1,
/// residual_fraction)`.
pub fn composite_forward(
    graph: &crate::graph::TypedGraph,
    interner: &crate::sym::Interner,
    composite: crate::graph::NodeID,
    input: Vec<f64>,
    sig_keys: Vec<String>,
) -> (Vec<f64>, i64, f64) {
    if !graph.has_node(composite) {
        return (Vec::new(), -1, 1.0);
    }
    let (Some(has_component), Some(na)) = (
        interner.lookup("has_component"),
        interner.lookup("net_assemblage"),
    ) else {
        return (Vec::new(), -1, 1.0);
    };
    let bp_k = interner.lookup("basin_parts");
    let bt_k = interner.lookup("basin_threshold");
    let sig_len = sig_keys.len().max(1) as f64;

    // Route: the component covering the most of the input's shape wins.
    let mut best: Option<(crate::graph::NodeID, usize, f64)> = None; // (comp, residual, frac)
    for c in graph.neighbours(composite, Some(has_component)) {
        let basin = bp_k
            .map(|k| str_set_attr(graph, interner, c, k))
            .unwrap_or_default();
        let residual = sig_keys.iter().filter(|k| !basin.contains(*k)).count();
        let frac = residual as f64 / sig_len;
        // basin_threshold is a fraction (default 0.4); a component only claims
        // an input whose shape it mostly covers.
        let thresh = bt_k
            .and_then(|k| graph.node(c).attrs.get(&k))
            .map(val_f64)
            .unwrap_or(0.4);
        if frac <= thresh && best.as_ref().map_or(true, |(_, r, _)| residual < *r) {
            best = Some((c, residual, frac));
        }
    }

    match best {
        Some((c, _, frac)) => match graph.neighbours(c, Some(na)).first().copied() {
            Some(asm) => (
                net_forward_core(graph, interner, asm, input),
                c.0 as i64,
                frac,
            ),
            None => (Vec::new(), -1, 1.0),
        },
        None => (Vec::new(), -1, 1.0), // no component covers the shape — defer to cognition
    }
}

/// Evaluate `NetForward { assemblage, inputs }`.
pub fn eval_net_forward(
    arena: &TermArena,
    assemblage: TermIdx,
    inputs: TermIdx,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    // The assemblage handle arrives as a `Node` when bound from a rule
    // match, or as a bare `Int` node id when called across the Python
    // boundary (a node id IS a u32). Accept both.
    let a_val = evaluate(arena, assemblage, env, ctx);
    let nid = match a_val {
        Value::Node(n) => n,
        Value::Int(i) if i >= 0 => crate::graph::NodeID(i as u32),
        _ => return Value::None,
    };
    if !ctx.graph.has_node(nid) {
        return Value::None;
    }
    let x = val_vec(&evaluate(arena, inputs, env, ctx));
    vec_to_value(&net_forward_core(ctx.graph, ctx.interner, nid, x))
}

/// The forward pass itself — a pure `(graph, node, input) -> output`
/// function, no Term arena / Env / JSON. `eval_net_forward` (the Term
/// path, usable inside a rule) and the `Substrate::net_forward` PyO3
/// method (the FAST serve path from Python — skips the per-call
/// `evaluate()` term-parse) both call this. `has_step`/`has_weight`
/// unresolved or the node missing steps ⇒ identity (input passed through).
pub fn net_forward_core(
    graph: &crate::graph::TypedGraph,
    interner: &crate::sym::Interner,
    nid: crate::graph::NodeID,
    input: Vec<f64>,
) -> Vec<f64> {
    let (steps, _) = load_steps(graph, interner, nid, true);
    forward_loaded(&steps, input)
}

/// Batch serve path for tile/reflex workloads. Tensors are resolved from their
/// graph-resident `WeightTensor` nodes exactly once, then the same immutable
/// execution plan is applied to every input row in caller order.
pub fn net_forward_batch_core(
    graph: &crate::graph::TypedGraph,
    interner: &crate::sym::Interner,
    nid: crate::graph::NodeID,
    inputs: &[Vec<f64>],
) -> Vec<Vec<f64>> {
    let (steps, _) = load_steps(graph, interner, nid, true);
    inputs
        .iter()
        .map(|input| forward_loaded(&steps, input.clone()))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::graph::{Attrs, NodeID, TypedGraph};
    use crate::sym::Interner;

    struct TestNet {
        graph: TypedGraph,
        interner: Interner,
        net: NodeID,
        w2: NodeID,
        b2: NodeID,
    }

    fn build_test_net() -> TestNet {
        let mut interner = Interner::new();
        let network_t = interner.intern("NetworkAssemblage");
        let step_t = interner.intern("AssemblageStep");
        let weight_t = interner.intern("WeightTensor");
        let has_step = interner.intern("has_step");
        let has_weight = interner.intern("has_weight");
        let order = interner.intern("order");
        let dim_behavior = interner.intern("dim_behavior");
        let transform = interner.intern("transform");
        let role = interner.intern("role");
        let data = interner.intern("data");
        let w1_role = interner.intern("W1");
        let b1_role = interner.intern("b1");
        let w2_role = interner.intern("W2");
        let b2_role = interner.intern("b2");

        let mut graph = TypedGraph::new();
        let net = graph.insert_node(network_t, Attrs::new());
        let step = graph.insert_node(
            step_t,
            Attrs(vec![
                (order, Value::Float(0.0)),
                (dim_behavior, Value::Str(transform)),
            ]),
        );
        graph
            .insert_edge(net, has_step, step, Attrs::new())
            .unwrap();

        let tensors = [
            (w1_role, mat_to_value(&[vec![1.0, 2.0], vec![-1.0, 1.0]])),
            (b1_role, vec_to_value(&[0.5, -0.25])),
            (w2_role, mat_to_value(&[vec![3.0, -2.0]])),
            (b2_role, vec_to_value(&[0.25])),
        ];
        let mut w2 = None;
        let mut b2 = None;
        for (role_value, tensor_data) in tensors {
            let node = graph.insert_node(
                weight_t,
                Attrs(vec![(role, Value::Str(role_value)), (data, tensor_data)]),
            );
            if role_value == w2_role {
                w2 = Some(node);
            }
            if role_value == b2_role {
                b2 = Some(node);
            }
            graph
                .insert_edge(step, has_weight, node, Attrs::new())
                .unwrap();
        }
        TestNet {
            graph,
            interner,
            net,
            w2: w2.unwrap(),
            b2: b2.unwrap(),
        }
    }

    #[test]
    fn batch_forward_is_exactly_scalar_forward_in_input_order() {
        let net = build_test_net();
        let inputs = vec![
            vec![0.0, 0.0],
            vec![1.0, -0.5],
            vec![-2.0, 3.0],
            vec![0.25, 0.75],
        ];
        let scalar: Vec<Vec<f64>> = inputs
            .iter()
            .map(|input| net_forward_core(&net.graph, &net.interner, net.net, input.clone()))
            .collect();
        let batch = net_forward_batch_core(&net.graph, &net.interner, net.net, &inputs);
        assert_eq!(batch, scalar);
    }

    #[test]
    fn batch_forward_keeps_identity_semantics_for_a_non_net() {
        let mut net = build_test_net();
        let concept_t = net.interner.intern("Concept");
        let concept = net.graph.insert_node(concept_t, Attrs::new());
        let inputs = vec![vec![1.0, 2.0], vec![-3.0, 4.5]];
        assert_eq!(
            net_forward_batch_core(&net.graph, &net.interner, concept, &inputs,),
            inputs,
        );
    }

    #[test]
    fn ordered_batch_collapse_is_exactly_sequential_scalar_collapse() {
        let mut scalar = build_test_net();
        let mut batch = build_test_net();
        let inputs = vec![
            vec![0.2, -0.1],
            vec![1.0, 0.5],
            vec![-0.75, 1.25],
            vec![0.4, 0.9],
        ];
        let targets = vec![vec![0.3], vec![-0.2], vec![1.1], vec![0.0]];
        let eta = 0.35;

        let scalar_surprise: Vec<f64> = inputs
            .iter()
            .zip(&targets)
            .map(|(input, target)| {
                net_collapse_step(
                    &mut scalar.graph,
                    &scalar.interner,
                    scalar.net,
                    input,
                    target,
                    eta,
                )
            })
            .collect();
        let batch_surprise = net_collapse_batch_ordered(
            &mut batch.graph,
            &batch.interner,
            batch.net,
            &inputs,
            &targets,
            eta,
        );
        assert_eq!(batch_surprise, scalar_surprise);

        let data_scalar = scalar.interner.lookup("data").unwrap();
        let data_batch = batch.interner.lookup("data").unwrap();
        assert_eq!(
            batch.graph.node(batch.w2).attrs.get(&data_batch),
            scalar.graph.node(scalar.w2).attrs.get(&data_scalar),
        );
        assert_eq!(
            batch.graph.node(batch.b2).attrs.get(&data_batch),
            scalar.graph.node(scalar.b2).attrs.get(&data_scalar),
        );

        for input in &inputs {
            assert_eq!(
                net_forward_core(&batch.graph, &batch.interner, batch.net, input.clone(),),
                net_forward_core(&scalar.graph, &scalar.interner, scalar.net, input.clone(),),
            );
        }
    }
}
