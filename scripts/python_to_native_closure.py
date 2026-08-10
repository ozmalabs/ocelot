"""Layer C closure — MOVE Python to native and PROVE the move is faithful.

The donkey classifier (scripts/donkey_to_graph.py) maps each Python compute-core to a Term-tree
or a named residual, but STOPS at classification — it never runs the emitted Term, so "graph-native"
was asserted, not demonstrated. This script closes that: it emits the native Term-tree AND evaluates
it on the Rust evaluator, comparing to the original Python across inputs. A faithful move means the
Python function can be DELETED — the compute now lives as graph data the agent owns.

The 4-way verdict (donkey_to_graph) routes each piece; this script makes each route concrete:
  · GRAPH-NATIVE  -> emit Term-tree, evaluate natively, assert == Python  (proven here)
  · HELD-LEAF     -> the leaf Call is an existing Rust op (delete the donkey, call the op)
  · EMIT-ERROR (loop/dict) -> a DECISION -> a graph Rule (not a primitive)
  · EMIT-ERROR (no held op) -> a genuinely NEW primitive -> the Layer B loop
       (agent_specify_primitive -> emit_primitive_rust -> domains/self_extend.PrimitiveExtension),
       which now lands + verifies the primitive autonomously (see self_extend).

Together with the verified "edit Python live" half, this completes Layer C: the agent can move its
own Python down to the native layer — composable compute as Term-trees, inexpressible compute as new
primitives via B — and verify the result, per CLAUDE.md (primitive in Rust, composition in graph).

Run:  python -m scripts.python_to_native_closure
"""
from __future__ import annotations

import substrate_rs as srs

from domains.ast_to_term import AstTermEmitter, EmitError, ingest_ast, open_ast_productions

# GRAPH-NATIVE donkey compute-cores: pure expressions that emit to a Term-tree of held variadic
# ops (Plus/Times/...). Each carries a Python reference impl + sample inputs for the faithful-move
# check. (These mirror the vision/measurement donkey from scripts/donkey_to_graph.)
GRAPH_NATIVE = [
    ("ema_background", "def ema_background(bg, frame):\n    return 0.95 * bg + 0.05 * frame",
     lambda bg, frame: 0.95 * bg + 0.05 * frame,
     [{"bg": 2.0, "frame": 10.0}, {"bg": 0.0, "frame": 1.0},
      {"bg": 5.0, "frame": -3.0}, {"bg": 100.0, "frame": 100.0}]),
    ("lerp", "def lerp(a, b, t):\n    return a + (b - a) * t",
     lambda a, b, t: a + (b - a) * t,
     [{"a": 0.0, "b": 10.0, "t": 0.25}, {"a": -4.0, "b": 4.0, "t": 0.5},
      {"a": 3.0, "b": 3.0, "t": 0.9}]),
    ("sound_pressure", "def sound_pressure(p0, gain, n):\n    return p0 * gain * gain + n",
     lambda p0, gain, n: p0 * gain * gain + n,
     [{"p0": 1.0, "gain": 2.0, "n": 0.5}, {"p0": 0.2, "gain": 3.0, "n": -1.0}]),
]


# The BOUNDARY: complex Python the fixed map cannot faithfully translate. These MUST surface as
# named residuals (EmitError), never a lossy Term. `collapse_runs` is the regression case — a loop
# that once emitted a bare `Var out`, silently dropping the dedup (now guarded in emit_function).
COMPLEX = [
    ("collapse_runs",
     "def collapse_runs(seq):\n    out = []\n    for u in seq:\n"
     "        if not out or out[-1] != u:\n            out.append(u)\n    return out",
     "a dedup LOOP -> a graph Rule (a decision), not a Term"),
    ("tp_table",
     "def tp_table(uni, fwd):\n    return {a: {b: c / uni[a] for b, c in nx.items()} "
     "for a, nx in fwd.items()}",
     "a DictComp -> statistical-learning graph Rule, not a Term"),
]


def _emit(s, name: str, src: str):
    open_ast_productions(s)
    rec = ingest_ast(s, src, root_label="c")
    root = rec["func_roots"][name]
    em = AstTermEmitter(s, held_leaves={})
    return em.emit_function(root), em.parts


def main() -> None:
    s = srs.Substrate()
    nat = s._inner                               # native handle: evaluate(Term-JSON dict, env)
    print("=" * 78)
    print("LAYER C closure — MOVE Python to native Term-trees, PROVE the move is faithful")
    print("=" * 78)
    all_ok = True
    for name, src, ref, cases in GRAPH_NATIVE:
        try:
            term, parts = _emit(s, name, src)
        except EmitError as e:
            print(f"\n  {name}: EMIT-ERROR (residual) -> {e}")
            all_ok = False
            continue
        print(f"\n  {name}  ->  native Term parts {parts}")
        for env in cases:
            native = float(nat.evaluate(term, env))
            py = float(ref(**env))
            ok = abs(native - py) < 1e-9
            all_ok &= ok
            args = " ".join(f"{k}={v}" for k, v in env.items())
            print(f"    {args:<28} native={native:10.4f}  python={py:10.4f}  "
                  f"{'OK' if ok else 'MISMATCH'}")
    # The boundary: complex Python MUST be refused as a named residual, never moved lossily.
    print("\n  BOUNDARY — complex Python the map cannot faithfully translate (must be residuals):")
    boundary_ok = True
    for name, src, where in COMPLEX:
        try:
            _emit(s, name, src)
            print(f"    {name:<16} MOVED (BUG: should have refused — silent loss!)")
            boundary_ok = False
        except EmitError as e:
            print(f"    {name:<16} residual OK  [{where}]")
            print(f"    {'':<16}   -> {str(e)[:84]}")

    print("\n" + "=" * 78)
    print(f"  FAITHFUL MOVE for all graph-native cores: {all_ok}")
    print(f"  COMPLEX Python correctly refused (no silent loss): {boundary_ok}")
    print("  -> a faithful core's donkey Python can be deleted; the compute is graph data.")
    print("  -> complex Python (loops/branches/dicts) -> a graph Rule (a decision).")
    print("  -> inexpressible NEW compute (no held op) -> the Layer B primitive loop.")
    print("=" * 78)


if __name__ == "__main__":
    main()
