//! Order-0 reflex scheduling in the native runtime.
//!
//! One reflex is exposed at a time so the host can enact a genuine external
//! response before the next stimulus is evaluated. This preserves today's
//! load-bearing callback interleaving while moving clock, refractory, stimulus
//! evaluation and firing stamps into Rust.

use crate::graph::NodeID;
use crate::substrate::Substrate;
use crate::term::{evaluate, Env, EvalCache, EvalCtx, TermNode};
use crate::value::Value;
use rustc_hash::FxHashSet;

#[derive(Clone, Debug)]
pub struct ReflexDispatch {
    pub node: NodeID,
    pub name: String,
    pub response: String,
}

fn int_attr(value: Option<&Value>, default: i64) -> i64 {
    match value {
        Some(Value::Int(v)) => *v,
        Some(Value::Float(v)) => *v as i64,
        _ => default,
    }
}

fn truthy(value: &Value) -> bool {
    match value {
        Value::Bool(v) => *v,
        Value::Int(v) => *v > 0,
        Value::Float(v) => *v > 0.0,
        Value::None => false,
        _ => true,
    }
}

/// ORDER 0 IS INVOLUNTARY, so it cannot be something the host chooses to call.
///
/// A reflex marked `autonomous` fires inside the engine's own cycle
/// (`cognitive_cycle::execute`) and is SKIPPED by `next_ready`, which is the
/// host-dispatch path.  The split is total: a reflex is either host-dispatched
/// (it needs a Python response callable to enact something external) or
/// autonomous (its response is graph-resident, so the engine can apply it with
/// nothing outside the graph involved).  Nothing fires on both paths, so no
/// existing reflex changes behaviour -- absent `autonomous` reads 0.
///
/// The stamp IS the response channel.  `next_ready` already writes
/// `last_fired_tick` and `fire_count` before returning, so a rule can read
/// "this reflex just fired" out of the graph.  That is what makes a
/// graph-resident response possible at all: the engine does not need to know
/// what the response MEANS, only that it happened, and the meaning is a rule.
fn is_autonomous(substrate: &Substrate, reflex: NodeID, autonomous_k: crate::sym::Sym) -> bool {
    match substrate.graph.node(reflex).attrs.get(&autonomous_k) {
        Some(Value::Bool(v)) => *v,
        Some(Value::Int(v)) => *v > 0,
        Some(Value::Float(v)) => *v > 0.5,
        _ => false,
    }
}

/// Fire every armed autonomous reflex once, in the engine's own cycle.
///
/// Returns the number that fired.  The clock is the agent's `tick` attr, the
/// same one the host path reads, so refractory periods mean the same thing on
/// both paths.  With no Agent node there is nothing to bind `a`/`agent` to and
/// the pass is a no-op.
pub fn fire_autonomous(substrate: &mut Substrate) -> usize {
    let agent_t = substrate.interner.intern("Agent");
    let Some(agent) = substrate.graph.nodes_of_type(agent_t).first().copied() else {
        return 0;
    };
    let tick_k = substrate.interner.intern("tick");
    let now = int_attr(substrate.graph.node(agent).attrs.get(&tick_k), 0);
    let reflex_t = substrate.interner.intern("Reflex");
    let autonomous_k = substrate.interner.intern("autonomous");
    let candidates: Vec<NodeID> = substrate
        .graph
        .nodes_of_type(reflex_t)
        .into_iter()
        .filter(|&reflex| is_autonomous(substrate, reflex, autonomous_k))
        .collect();
    if candidates.is_empty() {
        return 0;
    }
    // A rule cannot match a node no edge reaches, so the engine links the
    // reflex to the agent the first time it fires.  This is what makes a
    // GRAPH-RESIDENT response possible: the response is a rule matching
    // `agent -has_fired_reflex-> reflex` and reading `fire_count`, not a host
    // callable the engine has to call out to.  Added once and only once --
    // two same-type edges on one node can break matching for that edge type.
    let fired_edge = substrate.interner.intern("has_fired_reflex");
    let mut fired = 0usize;
    let mut excluded: FxHashSet<NodeID> = FxHashSet::default();
    while let Some(dispatch) =
        dispatch_next(substrate, agent, now, &candidates, &excluded, true)
    {
        let already = substrate
            .graph
            .neighbours(agent, Some(fired_edge))
            .contains(&dispatch.node);
        if !already {
            let _ = substrate.graph.insert_edge(
                agent, fired_edge, dispatch.node,
                rustc_hash::FxHashMap::default());
            substrate.mark_edge_type_dirty(fired_edge);
        }
        excluded.insert(dispatch.node);
        fired += 1;
    }
    fired
}

pub fn next_ready(
    substrate: &mut Substrate,
    agent: NodeID,
    now: i64,
    ordered: &[NodeID],
    excluded: &FxHashSet<NodeID>,
) -> Option<ReflexDispatch> {
    dispatch_next(substrate, agent, now, ordered, excluded, false)
}

fn dispatch_next(
    substrate: &mut Substrate,
    agent: NodeID,
    now: i64,
    ordered: &[NodeID],
    excluded: &FxHashSet<NodeID>,
    autonomous: bool,
) -> Option<ReflexDispatch> {
    let reflex_t = substrate.interner.intern("Reflex");
    let autonomous_k = substrate.interner.intern("autonomous");
    let stimulus_edge = substrate.interner.intern("stimulus_term");
    let name_k = substrate.interner.intern("name");
    let response_k = substrate.interner.intern("response");
    let refractory_k = substrate.interner.intern("refractory_ticks");
    let last_k = substrate.interner.intern("last_fired_tick");
    let count_k = substrate.interner.intern("fire_count");
    let a_sym = substrate.interner.intern("a");
    let agent_sym = substrate.interner.intern("agent");

    let fallback;
    let reflexes = if ordered.is_empty() {
        fallback = substrate.graph.nodes_of_type(reflex_t);
        fallback.as_slice()
    } else {
        ordered
    };
    for &reflex in reflexes {
        if !substrate.graph.has_node(reflex)
            || substrate.graph.node(reflex).type_ != reflex_t
        {
            continue;
        }
        if excluded.contains(&reflex) {
            continue;
        }
        // The two paths are disjoint: the host never sees an autonomous
        // reflex, and the engine pass never sees a host-dispatched one.
        if is_autonomous(substrate, reflex, autonomous_k) != autonomous {
            continue;
        }
        let attrs = &substrate.graph.node(reflex).attrs;
        let last = int_attr(attrs.get(&last_k), -1_000_000_000);
        let refractory = int_attr(attrs.get(&refractory_k), 0);
        if now - last < refractory {
            continue;
        }
        let Some(root) = substrate.graph.neighbours(reflex, Some(stimulus_edge)).first().copied()
        else {
            continue;
        };
        let name = match attrs.get(&name_k) {
            Some(Value::Str(v)) => substrate.interner.resolve(*v).to_owned(),
            _ => continue,
        };
        let response = match attrs.get(&response_k) {
            Some(Value::Str(v)) => substrate.interner.resolve(*v).to_owned(),
            _ => String::new(),
        };

        let arena_len = substrate.terms.nodes.len();
        let node_term = substrate.terms.add(TermNode::Lit { value: Value::Node(root) });
        let eval_term = substrate.terms.add(TermNode::EvalSubgraph { node: node_term });
        let mut env: Env = smallvec::smallvec![
            (a_sym, Value::Node(agent)),
            (agent_sym, Value::Node(agent)),
        ];
        let mut cache = EvalCache::default();
        let value = {
            let Substrate {
                graph, interner, concepts, terms, counters, shape_cache, ..
            } = substrate;
            let mut ctx = EvalCtx::new(graph, interner)
                .with_cache(&mut cache)
                .with_counters(counters)
                .with_shape_cache(shape_cache);
            if !concepts.is_empty() {
                ctx = ctx.with_concepts(concepts);
            }
            evaluate(terms, eval_term, &mut env, &mut ctx)
        };
        substrate.terms.nodes.truncate(arena_len);
        if !truthy(&value) {
            continue;
        }
        let count = int_attr(substrate.graph.node(reflex).attrs.get(&count_k), 0);
        substrate.set_attr(reflex, last_k, Value::Int(now));
        substrate.set_attr(reflex, count_k, Value::Int(count + 1));
        return Some(ReflexDispatch { node: reflex, name, response });
    }
    None
}
