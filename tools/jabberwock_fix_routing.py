"""The jabberwock fixes its own spatial-routing iteration — adds a native
fixed-point relaxation driver to its Rust runtime via the self-modification
keystone: backup -> apply -> cargo check -> rollback-on-failure -> audit, then
rebuild the native layer. All-or-nothing; a failed build leaves py.rs
byte-identical.

WHY. Passability-aware spatial distance is a Bellman relaxation. The per-step
relax (what a distance is, which neighbour is passable) is ALREADY a
graph-resident Term (domains/spatial_routing.py) and evaluates correctly. But
the fixpoint ITERATION had nowhere correct to live:
  * a Python while/deque loop is forbidden agent decision-logic (CLAUDE.md);
  * the incremental rule engine (run_rules/tick) re-fires a rule only when the
    EDGE TYPES it MATCHES change, not when an attr it READS in its effect
    changes — so an attr-relaxation rule fires once then is marked clean and the
    fixpoint stalls (proven: apply_rule_once relaxes fully, run_rules halts at
    one step).

THE FIX (primitive in Rust, composition in graph). A generic `relax_to_fixpoint`
substrate primitive: given a graph-resident relax Term + a cell set + a register
attr, it sweeps the Term to convergence in Rust (Jacobi; fresh EvalCache per
eval so a neighbour's just-written value is seen). The routing DECISION stays in
the Term (graph data); only the iteration MECHANISM is the Rust primitive —
reusable for any attr-relaxation, and it bypasses the incremental engine's
edge-keyed dirty tracking entirely.
"""
from __future__ import annotations

from domains.self_modification import SelfModification

# Anchor: insert before `fn evaluate` — INCLUDING its own #[pyo3(signature)]
# attribute, so the new method lands above that attribute (not between it and
# the fn, which would steal evaluate's signature).
OLD = '''    #[pyo3(signature = (term_json, env=None))]
    fn evaluate<'py>(
        &mut self,
        py: Python<'py>,
        term_json: &Bound<'_, PyAny>,
        env: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<Bound<'py, PyAny>> {'''

NEW = '''    /// Relax a graph-resident Term to a fixed point over a set of cells,
    /// writing each cell's value into the `register` attr — the native
    /// iteration driver for attr-relaxation (passability-aware spatial distance
    /// is the first user). The relaxation DECISION lives wholly in `term` (graph
    /// data: what a distance is, which neighbour is passable); this primitive
    /// only sweeps it to convergence in Rust, so no Python loop drives the
    /// fixpoint and the incremental rule engine (which re-fires on matched EDGE
    /// types, not attrs read in effects, and so cannot drive an attr-relaxation
    /// rule) is bypassed. Jacobi sweeps: each sweep evaluates `term` for every
    /// cell (env binds "cell" -> the cell node) against the previous register
    /// values, then commits the changed registers; repeats until nothing
    /// changes or `max_sweeps` (0 = bound by the cell count, since no finite
    /// shortest path is longer). Returns the sweeps taken. Each cell eval uses a
    /// FRESH EvalCache so a neighbour's just-written value is seen — the
    /// staleness that froze run_rules cannot occur here.
    #[pyo3(signature = (term_json, cells, register, max_sweeps=0))]
    fn relax_to_fixpoint(
        &mut self,
        py: Python<'_>,
        term_json: &Bound<'_, PyAny>,
        cells: Vec<u32>,
        register: &str,
        max_sweeps: usize,
    ) -> PyResult<usize> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let json = pyobj_to_json(py, term_json)?;
        let pre_parse = inner.terms.nodes.len();
        let idx = term_from_json(&json, &mut inner.terms, &mut inner.interner)
            .map_err(|e| PyValueError::new_err(format!("bad Term JSON: {:?}", e)))?;
        let post_parse = inner.terms.nodes.len();
        let reg = inner.interner.intern(register);
        let cell_sym = inner.interner.intern("cell");
        let cell_ids: Vec<NodeID> = cells.iter().map(|&v| NodeID(v)).collect();
        let cap = if max_sweeps == 0 { cell_ids.len() + 1 } else { max_sweeps };
        let mut sweeps = 0usize;
        for _ in 0..cap {
            let mut updates: Vec<(NodeID, f64)> = Vec::new();
            for &c in &cell_ids {
                if !inner.graph.has_node(c) {
                    continue;
                }
                let mut env_v: Env = Default::default();
                env_v.push((cell_sym, Value::Node(c)));
                let mut cache = EvalCache::default();
                let nv = {
                    let SubstrateRs {
                        graph, interner, concepts, terms, counters,
                        active_shape_target, shape_cache, ..
                    } = &mut *inner;
                    let shape_target_copy = *active_shape_target;
                    let mut ctx = EvalCtx::new(graph, interner)
                        .with_cache(&mut cache)
                        .with_counters(counters)
                        .with_shape_cache(shape_cache);
                    if !concepts.is_empty() {
                        ctx = ctx.with_concepts(concepts);
                    }
                    if let Some(target) = shape_target_copy {
                        ctx = ctx.with_shape_target(target);
                    }
                    match evaluate(terms, idx, &mut env_v, &mut ctx) {
                        Value::Float(f) => Some(f),
                        Value::Int(i) => Some(i as f64),
                        _ => None,
                    }
                };
                inner.terms.nodes.truncate(post_parse);
                if let Some(nv) = nv {
                    let old = match inner.graph.node(c).attrs.get(&reg) {
                        Some(Value::Float(f)) => Some(*f),
                        Some(Value::Int(i)) => Some(*i as f64),
                        _ => None,
                    };
                    if old != Some(nv) {
                        updates.push((c, nv));
                    }
                }
            }
            if updates.is_empty() {
                break;
            }
            for (c, nv) in updates {
                inner.graph.set_node_attr(c, reg, Value::Float(nv));
            }
            sweeps += 1;
        }
        inner.terms.nodes.truncate(pre_parse);
        Ok(sweeps)
    }

''' + OLD


def main() -> None:
    sm = SelfModification()
    res = sm.edit("runners/dsl/src/py.rs", OLD, NEW, check=True)
    print("edit result:", res)
    if not res.get("ok"):
        print("cargo check FAILED — rolled back; py.rs is byte-identical.")
        return
    print("cargo check PASSED. Rebuilding native layer (slow)…")
    rb = sm.rebuild_native()
    print("rebuild:", {k: rb[k] for k in ("ok",)}, rb.get("tail", "")[-300:])


if __name__ == "__main__":
    main()
