"""ACTUALLY PORT the donkey COMPUTE-CORES to agent-owned native Term-trees.

donkey_to_graph.py classified; this EXECUTES the second port category: each pure
compute-core (arithmetic) the session wrote in Python is ingested as AST, emitted
to a native Term-tree by the agent's FIXED AST->Term map, and EVALUATED IN RUST.
We assert the Rust-evaluated Term-tree == the original Python on sample inputs:
the compute now lives as graph data the agent owns, the Rust substrate runs it, and
only I/O stays Python. (Port category #1 — relational rank -> held shape_signature
op — is already done across the speech scripts, commit a1b684d6.)

Run:  python -m scripts.port_compute_to_terms
"""
from __future__ import annotations
import sys

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
import substrate_rs as srs
from domains.ast_to_term import open_ast_productions, ingest_ast, AstTermEmitter, EmitError

# pure-arithmetic donkey compute-cores from this session (no held leaf), each with
# the Python reference + sample inputs to check Rust-eval against.
CORES = [
    ("ema_background", "def ema_background(bg, frame):\n    return 0.95 * bg + 0.05 * frame",
     lambda bg, frame: 0.95 * bg + 0.05 * frame, {"bg": 2.0, "frame": 10.0}),
    ("blend", "def blend(a, b, w):\n    return a * w + b * (1 - w)",
     lambda a, b, w: a * w + b * (1 - w), {"a": 4.0, "b": 9.0, "w": 0.25}),
    ("motion_norm", "def motion_norm(d, span):\n    return d / span",
     lambda d, span: d / span, {"d": 7.0, "span": 4.0}),
    ("mi_term_noleaf", "def mi_term_noleaf(p, pa, pc):\n    return p * (p / (pa * pc))",
     lambda p, pa, pc: p * (p / (pa * pc)), {"p": 0.2, "pa": 0.4, "pc": 0.5}),
]


def main():
    print("=" * 78)
    print("PORT COMPUTE-CORES -> NATIVE TERM-TREES (Rust-evaluated, == Python)")
    print("=" * 78)
    s = srs.Substrate()
    open_ast_productions(s)
    all_ok = True
    for name, src, pyfn, env in CORES:
        rec = ingest_ast(s, src, root_label="donkey_compute")
        root = rec["func_roots"].get(name)
        em = AstTermEmitter(s, held_leaves={})
        try:
            tj = em.emit_function(root)
        except EmitError as e:
            print(f"  {name:<16} EMIT-ERROR (not pure compute): {e}")
            all_ok = False
            continue
        got = float(s._inner.evaluate(tj, env))
        exp = float(pyfn(**env))
        ok = abs(got - exp) < 1e-9
        all_ok = all_ok and ok
        print(f"  {name:<16} Term parts {em.parts}")
        print(f"  {'':<16} Rust-eval={got:.6g}  python={exp:.6g}  MATCH={ok}  "
              f"({rec['n_nodes']} ast nodes -> native Term-tree)")
    print("\n  " + ("ALL compute-cores now run as agent-owned, Rust-evaluated Term-trees."
                    if all_ok else "some cores did not port — see above."))
    print("  The compute is graph data the agent owns; the substrate evaluates it;")
    print("  only I/O stays world-adapter Python. (Vectorising the elementwise EMA")
    print("  over a whole frame is the one genuinely-new vision primitive: a")
    print("  vector-elementwise Term, agent_specify + emit_primitive_rust.)")
    print("=" * 78)


if __name__ == "__main__":
    main()
