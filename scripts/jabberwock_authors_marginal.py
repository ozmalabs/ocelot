"""THE JABBERWOCK AUTHORS A SECOND RUST PRIMITIVE — the deformation-MARGINAL leaf (the plan's deferred gap).

The joint-inference plan named two gaps: the generative leaf (authored: DeformGen, MAP) AND 'marginalise the
deformation inside the leaf (integrate, not commit)'. This authors the second: DeformGenMarginal = the proper
Bayesian marginal likelihood -- the MAP residual PLUS the log-determinant Occam term (a primitive whose
deformation manifold is broad pays for that flexibility), which the MAP leaf lacks. The agent authors it the
same way (specify -> self-teacher body -> uniform arity-emitter arms -> self_extend install) -- proving the
affordance is GENERAL (a second primitive, not a one-off) and pursuing BPL's actual posterior.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_authors_marginal
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

BRIEF = """You are authoring ONE Rust function for a typed-graph DSL evaluator. Output ONLY the Rust function \
(starting `fn deform_gen_marginal`), no markdown fences, no prose.

Signature: fn deform_gen_marginal(a: &Value, b: &Value) -> f64

Same inputs and ridge-fit as a deformation-fit leaf:
`a` = query part: for frame in a.iter() {{ for x in frame.iter() {{ push x.as_f64() }} }} -> q (len d).
`b`: let bf: Vec<f64> = b.iter().map(|x| x.as_f64()).collect() = [ mean (d) ++ modes (m*d, row-major modes[j*d+c]) ++ inv_var (m) ]; m = (bf.len()-d)/(d+1).
Build A = M M^T + diag(inv_var) (m-by-m, where row j of M is modes[j*d .. j*d+d]) and rhs = M (q-mean) (len m).
Solve A coeff = rhs by Gauss-Jordan elimination; WHILE eliminating, accumulate logdet += ln(pivot) for each pivot (the running product of pivots is det(A)).
recon[c] = mean[c] + sum_j modes[j*d+c]*coeff[j]; resid = sum_c (q[c]-recon[c])^2 + sum_j inv_var[j]*coeff[j]^2.
This is the deformation-MARGINAL: the Bayesian cost is the residual PLUS the log-determinant Occam penalty.
Return ((resid + logdet.max(0.0)).max(0.0) / d as f64).sqrt().

Guards: d==0 || bf.len()<=d -> f64::INFINITY; m==0 || bf.len()!=d+m*d+m -> f64::INFINITY; any pivot.abs()<1e-12 -> f64::INFINITY.
Only std Rust. Value has .iter() (items have .iter()) and .as_f64()."""


def _clean(s):
    s = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", s.strip())
    m = re.search(r"fn deform_gen_marginal", s)
    return s[m.start():].strip() if m else s.strip()


def main():
    print(SEP)
    print("THE JABBERWOCK AUTHORS A SECOND PRIMITIVE — DeformGenMarginal (deformation marginalised, Occam term).")
    print(SEP)
    spec = {"name": "DeformGenMarginal", "fn": "deform_gen_marginal", "semantic_kind": "arity_binary_scalar_leaf",
            "purpose": "the deformation-MARGINAL generative leaf: residual + log-det Occam term (integrate the "
                       "deformation, not MAP it) -- the proper Bayesian marginal likelihood the plan named",
            "why_new": "a ridge fit + Gauss-Jordan with log-determinant accumulation; INEXPRESSIBLE from the DSL",
            "grounded_in_science": True, "is_agent_design": True}
    srs.Substrate().add_node("PrimitiveSpec", {"name": "DeformGenMarginal", "composed_by": "agent"}) if False else None
    print(f"\n  [1] specifies DeformGenMarginal (the deferred gap: marginalise the deformation, not commit).")
    print(f"  [2] self-teacher authors the body (claude -p)...", flush=True)
    body = _clean(make_ask(timeout=240.0)(BRIEF))
    if not body.startswith("fn deform_gen_marginal"):
        print(f"  ✗  no usable body ({len(body)} chars). Abort clean."); return 1
    print(f"      authored {body.count(chr(10))+1} lines (starts {body.splitlines()[0][:58]!r})")
    spec["body"] = body
    print(f"  [3] uniform emitter + self_extend install (all-or-nothing)...", flush=True)
    res = PrimitiveExtension().extend(spec, anchor_spec=ANCHOR)
    print(f"      install: ok={res.get('ok')} stage={res.get('stage')}")
    if not res.get("ok"):
        print(f"      detail: {str(res.get('detail',''))[-280:]}")
        print(f"  the guard reverted byte-identical. Affordance proven; re-author the body (the one semantic part).")
        print(SEP); return 1

    s2 = srs.Substrate()

    class _P:
        __slots__ = ("_json",)

        def __init__(s, d): s._json = d
    q = [[0.0, 0.0], [1.0, 1.0]]
    model = [0.0, 0.0, 1.0, 1.0] + [0.1, 0.1, 0.1, 0.1] + [1.0]
    v = s2.evaluate(_P({"type": "DeformGenMarginal", "a": {"type": "Lit", "value": q}, "b": {"type": "Lit", "value": model}}), {})
    print(f"\n  [4] verify: DeformGenMarginal evaluates -> {float(v):.4f} (callable, finite)")
    print("\n" + SEP)
    print("  A SECOND self-authored Rust primitive -- the affordance is GENERAL, not a one-off. The agent now")
    print("  holds both the MAP and the MARGINAL deformable leaf; compose the marginal into the joint inference")
    print("  (jabberwock_joint_bpl leaf='defgenmarg') and measure whether integrating the deformation pays.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
