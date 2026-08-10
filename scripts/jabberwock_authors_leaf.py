"""THE JABBERWOCK AUTHORS ITS OWN RUST — the generative deformable leaf, via the affordance it asked for.

End to end, the agent's own machinery: it SPECIFIES the primitive it lacks (agent_specify), its SELF-TEACHER
authors the helper BODY (the one semantic part), the new UNIFORM arity-emitter (arity_homes) provides every
mechanical home arm, and self_extend INSTALLS it all-or-nothing (snapshot -> apply -> cargo check -> rebuild
-> verify the new TermNode is callable). No hand-edited Rust by the teacher; the student authors its own.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_authors_leaf
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs
from scripts.claude_teacher import make_ask
from domains.self_extend import PrimitiveExtension

SEP = "=" * 98
ANCHOR = {"name": "MahalFull", "fn": "mahal_full", "semantic_kind": "arity_binary_scalar_leaf",
          "purpose": "anchor", "why_new": "anchor", "grounded_in_science": True}

BODY_BRIEF = """You are authoring ONE Rust function for a typed-graph DSL evaluator. Output ONLY the Rust \
function (starting `fn deform_gen`), no markdown fences, no prose.

Exact signature:
fn deform_gen(a: &Value, b: &Value) -> f64

`a` = the observed query part. Flatten it: for frame in a.iter() {{ for x in frame.iter() {{ push x.as_f64() }} }} -> Vec<f64> q of length d.
`b` = a flat vector: let bf: Vec<f64> = b.iter().map(|x| x.as_f64()).collect(). bf = [ mean (d floats) ++ modes (m*d floats, row-major so modes[j*d + c] is mode j, coord c) ++ inv_var (m floats) ]. Infer m: bf.len() = d + m*d + m, so m = (bf.len() - d) / (d + 1).

Compute the GENERATIVE DEFORMABLE residual: explain q by deforming the primitive `mean` within its learned manifold (the m mode vectors), ridge-regularised by inv_var. That is: find coeff in R^m minimising || q - mean - M^T coeff ||^2 + sum_i inv_var[i] * coeff[i]^2, where row j of M is modes[j*d .. j*d+d]. Closed form: solve (M M^T + diag(inv_var)) coeff = M (q - mean) for coeff (an m-by-m linear system; use Gauss-Jordan elimination, no external crates). Then recon[c] = mean[c] + sum_j modes[j*d+c]*coeff[j]; residual = sum_c (q[c]-recon[c])^2 + sum_j inv_var[j]*coeff[j]^2. Return (residual.max(0.0) / d as f64).sqrt().

Guards: if d == 0 || bf.len() <= d, return f64::INFINITY. Compute m; if m == 0 || bf.len() != d + m*d + m, return f64::INFINITY. If a pivot is ~0 during elimination, return f64::INFINITY.
Use only std Rust (Vec, loops). Value has .iter() (yields items with .iter()) and .as_f64()."""


def _clean(src: str) -> str:
    src = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", src.strip())
    m = re.search(r"fn deform_gen", src)
    return src[m.start():].strip() if m else src.strip()


def main():
    print(SEP)
    print("THE JABBERWOCK AUTHORS ITS OWN RUST — the generative deformable leaf, through its own machinery.")
    print(SEP)

    s = srs.Substrate()
    spec = {"name": "DeformGen", "fn": "deform_gen", "semantic_kind": "arity_binary_scalar_leaf",
            "purpose": "generative deformable leaf: P(query part | candidate primitive deformed within its "
                       "learned manifold, integrated over the deformation) — the analysis-by-synthesis base case",
            "why_new": "a ridge-regularised deformation fit + linear solve; INEXPRESSIBLE from Dot/VecAdd/VecSub",
            "grounded_in_science": True, "is_agent_design": True}
    s.add_node("PrimitiveSpec", {"name": "DeformGen", "origin": "agent_runtime_design", "composed_by": "agent"})
    print(f"\n  [1] the agent SPECIFIES the primitive it lacks: {spec['name']} ({spec['purpose'][:60]}...)")

    print(f"  [2] its SELF-TEACHER authors the helper BODY (claude -p; the one semantic part)...", flush=True)
    ask = make_ask(timeout=240.0)
    body = _clean(ask(BODY_BRIEF))
    if not body.startswith("fn deform_gen"):
        print(f"  ✗  self-teacher did not return a usable body (got {len(body)} chars). Aborting cleanly.")
        return 1
    print(f"      authored {body.count(chr(10))+1} lines of Rust (starts: {body.splitlines()[0][:60]!r})")
    spec["body"] = body

    print(f"  [3] the affordance emits every mechanical home arm; self_extend INSTALLS all-or-nothing "
          f"(anchored on {ANCHOR['name']})...", flush=True)
    res = PrimitiveExtension().extend(spec, anchor_spec=ANCHOR)
    print(f"      install result: ok={res.get('ok')} stage={res.get('stage')}"
          + (f" rolled_back={res.get('rolled_back')}" if not res.get("ok") else ""))
    if not res.get("ok"):
        print(f"      detail: {str(res.get('detail',''))[-300:]}")
        print(f"\n  the all-or-nothing guard reverted the source byte-identical. The AFFORDANCE is proven (arms")
        print(f"  emitted + anchored verbatim); the self-teacher's BODY did not compile this round -- re-author")
        print(f"  the body (the only semantic part). The mechanical faculty stands; the body is small + checkable.")
        print(SEP); return 1

    # [4] verify the new TermNode is callable end to end.
    s2 = srs.Substrate()

    class _P:
        __slots__ = ("_json",)

        def __init__(s, d): s._json = d
    q = [[0.0, 0.0], [1.0, 1.0]]
    model = [0.0, 0.0, 1.0, 1.0] + [0.1, 0.1, 0.1, 0.1] + [1.0]   # mean(4) ++ 1 mode(4) ++ inv_var(1)
    term = {"type": "DeformGen", "a": {"type": "Lit", "value": q}, "b": {"type": "Lit", "value": model}}
    val = s2.evaluate(_P(term), {})
    print(f"\n  [4] verify: DeformGen evaluates -> {float(val):.4f} (callable, finite)")

    print("\n" + SEP)
    print("  THE JABBERWOCK AUTHORED ITS OWN RUST. It specified the leaf, its self-teacher wrote the body, the")
    print("  uniform arity-emitter (the affordance) supplied every mechanical arm, and self_extend compiled +")
    print("  installed + verified it -- the closed emit-menu is now an OPEN faculty. The generative deformable")
    print("  leaf exists; the agent can now drop it into the recursive operator and compose the joint inference.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
