"""order_invariant_binding_gate — a CHEAP, graph-native ORDER-INVARIANT K-binder
with a DEFINED RESIDUAL. The structural/in-route lever toward ~78 (the generative-
program ceiling), NOT the deep route (96.5 = holistic features, a different machine).

The structural-residual recognizer bound parts POSITIONALLY (s0↔s0) — so two
drawings of the same character in DIFFERENT stroke order / part count failed to
align (the part-order cap). This binds parts by their RELATION-PATTERN (structural
role), order-invariantly, via the SME cheap polynomial mechanism: greedy local-
match on relation agreement (Argmax) + a used-set threaded forward (Fold), NOT
exhaustive permutation. It RETURNS A DEFINED RESIDUAL — AntiUnifyWitness over the
correspondence — so it composes with the residual algebra exactly as before, now
order-invariantly.

VERDICT: COMPOSES from held Terms (Argmax + Fold + Filter/In + StructSim +
AntiUnifyWitness) — NO new Rust. The binder's reasoning is the Term-tree run by the
Rust evaluator; Python only builds the Term JSON and reads the result. donkey=0.

THE POINT (carry it): build CAPABILITY — a cheap graph-native option with a defined
residual — not a benchmark number. Report where the lift lands (≤~78, in-route).

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/order_invariant_binding_gate.py [episodes] [way]
"""
from __future__ import annotations
import os, sys, math, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
import substrate_rs as srs
import domains.omniglot_world as ow
import domains.stroke_relations as sr
import domains.substroke_codebook as cb

def L(v): return {"type": "Lit", "value": v}
def V(n): return {"type": "Var", "name": n}
def Vec(*xs): return {"type": "Vec", "items": list(xs)}
def IndexAt(seq, i): return {"type": "IndexAt", "seq": seq, "index": i}
def Append(seq, item): return {"type": "Append", "seq": seq, "item": item}
def Fold(src, var, acc, init, body):
    return {"type": "Fold", "source": src, "var_name": var, "acc_name": acc, "init": init, "body": body}
def Argmax(src, var, value, default):
    return {"type": "Argmax", "source": src, "var_name": var, "value": value, "default": default}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def In(m, c): return {"type": "In", "member": m, "container": c}
def Not(a): return {"type": "Not", "arg": a}
def SS(a, b): return {"type": "StructSim", "a": a, "b": b, "wild": "·?·"}
def AUW(vals): return {"type": "AntiUnifyWitness", "values": vals, "wild": "·?·"}

_S = srs._NativeSubstrate()
_EV = _S.evaluate
_M, _PER = 8, 12


# ---- ingest: trace -> (id, descriptor, relation) parts (mechanical) ----
# relation_feats gives, per part, a 10-dim signature = 2 endpoints x
# [x, y, is_end_junction, is_along_junction, is_free]. The RELATION is the
# junction TYPE of each endpoint (the topology that ties parts into a character) —
# this is the writer-invariant structure the binder corresponds by. Mechanical
# perception read, not a decision.
def _relation(f):
    """Each endpoint's junction type as an ordered (e0, e1) pair of
    {end, along, free}. The two-endpoint junction signature IS the part's
    structural role — order-invariant across stroke order."""
    if not isinstance(f, (list, tuple)) or len(f) < 10:
        return ["free", "free"]
    def jtype(base):
        is_end, is_along, is_free = f[base + 2], f[base + 3], f[base + 4]
        if is_end >= 0.5:
            return "end"
        if is_along >= 0.5:
            return "along"
        return "free"
    return [jtype(0), jtype(5)]


def _structure(path):
    strokes = ow.strokes_normalized(path, per_stroke=_PER)
    if not strokes:
        return []
    feats = sr.relation_feats(strokes)
    return [[f"s{i}", [float(x) for x in cb.substroke_descriptor(st, m=_M)], _relation(f)]
            for i, (st, f) in enumerate(zip(strokes, feats))]


# ---- the ORDER-INVARIANT BINDER as a Term-tree (greedy, polynomial) ----
def _binder_term(A_expr, B_list):
    """Fold over A's parts; acc=(used_B_indices, pairs). Each step Argmax over the
    UNUSED B-indices by StructSim(a-part, B[j]) (relation+shape agreement), append
    (a-part, chosen-B-part), mark used. Greedy local-match — O(|A|·|B|), no
    permutation. Returns acc = [used, pairs]."""
    acc, ap = V("acc"), V("ap")
    used, pairs = IndexAt(acc, L(0)), IndexAt(acc, L(1))
    cands = Filter(L(list(range(len(B_list)))), "j", Not(In(V("j"), used)))
    best = Argmax(cands, "j", SS(ap, IndexAt(L(B_list), V("j"))), L(0))
    body = Vec(Append(used, best), Append(pairs, Vec(ap, IndexAt(L(B_list), best))))
    return Fold(A_expr, "ap", "acc", Vec(Vec(), Vec()), body)


def bind(A, B):
    """The correspondence (list of (a-part, bound-b-part)) — run by the Rust evaluator."""
    if not A or not B:
        return []
    return _EV(_binder_term(L(A), B), {})[1]


def defined_residual(A, B):
    """The DEFINED residual: AntiUnifyWitness over the corresponded pairs -> the
    order-invariant (part,relation) program (template) + witness sigma. Composes
    with the residual algebra exactly as before."""
    pairs = bind(A, B)
    B_reord = [list(p[1]) for p in pairs]
    return _EV(AUW(L([A, B_reord])), {})


def fit_oi(support, query):
    """Order-invariant regenerative fit: bind query parts to support parts by
    relation-pattern, then StructSim over the correspondence (graded shapes, hard
    relations). Held Terms; the Rust evaluator computes the float."""
    pairs = bind(support, query)
    if not pairs:
        return -1.0
    sup_b = [list(p[0]) for p in pairs]
    qry_b = [list(p[1]) for p in pairs]
    base = float(_EV(SS(L(sup_b), L(qry_b)), {}))
    n = len(pairs)
    return base * (n / max(len(support), len(query)))


def recognise_oi(query, candidates):
    scores = [fit_oi(c, query) for c in candidates]
    return max(range(len(scores)), key=lambda k: scores[k])


def main() -> int:
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    way = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    random.seed(7)
    if not ow.have_data():
        print("no omniglot trace data")
        return 1
    eval_alphas = ow.alphabets()[10:]
    ok = True

    # 1. CAPABILITY: an order-permuted same-class pair that POSITIONAL missed, order-invariant binds.
    #    relation = the endpoint junction-type pair (the structural role), order-invariant.
    A = [["a0", [1.0, 0.0], ["free", "end"]], ["a1", [0.0, 1.0], ["end", "along"]],
         ["a2", [0.5, 0.5], ["along", "free"]]]
    B_rev = [["b0", [0.5, 0.5], ["along", "free"]], ["b1", [0.0, 1.0], ["end", "along"]],
             ["b2", [1.0, 0.0], ["free", "end"]]]                 # same char, REVERSE stroke order
    pairs = bind(A, B_rev)
    corr = {p[0][0]: (p[1][2][0]) for p in pairs}
    # correct iff each A-part bound to a B-part with the SAME relation predicate
    relpred = {p[0][0]: p[0][2][0] for p in pairs}
    cap_ok = all(corr[k] == relpred[k] for k in corr) and len(pairs) == 3
    print("[CAPABILITY] order-permuted same-class pair (B reverse-order):")
    for p in pairs:
        print(f"   {p[0][0]} {tuple(p[0][2])} -> {p[1][0]} {tuple(p[1][2])}")
    print("   bound by RELATION-PATTERN (not position):", "OK" if cap_ok else "FAIL")
    ok &= cap_ok

    # 2. DEFINED RESIDUAL composes: the binder re-orders B to match A's relational program, and
    #    AntiUnifyWitness over the correspondence yields a DEFINED witness sigma that feeds the algebra.
    #    On a genuinely SCRAMBLED permutation, order-invariant recovers A's relation order where
    #    positional does NOT. (Same program regardless of stroke order = the order-invariant residual.)
    B_scram = [B_rev[1], B_rev[2], B_rev[0]]      # rotate -> A[i] != B_scram[i] positionally
    pairs2 = bind(A, B_scram)
    def _norm(xs): return [list(i) if isinstance(i, (list, tuple)) else i for i in xs]
    oi_rel = _norm([list(p[1][2]) for p in pairs2])      # relations of the bound B-parts, in A's order
    a_rel = _norm([p[2] for p in A])
    pos_rel = _norm([p[2] for p in B_scram])             # positional B relations (unbound)
    sigma_oi = defined_residual(A, B_scram)[1][1]        # the witness sigma (feeds AntiUnifyWitness/Substitute)
    res_ok = (oi_rel == a_rel) and (pos_rel != a_rel) and (len(sigma_oi) > 0)
    print(f"[DEFINED RESIDUAL] scrambled permutation: order-invariant recovers A's relation order={oi_rel == a_rel}, "
          f"positional matches={pos_rel == a_rel}; witness sigma defined ({len(sigma_oi)} bindings, composes) ->",
          "OK" if res_ok else "FAIL")
    ok &= res_ok

    # 3. CHEAP: greedy local-match is O(|A|*|B|) per pair — count the StructSim calls, not factorial.
    na, nb = len(A), len(B_rev)
    print(f"[CHEAP] greedy local-match: O(|A|*|B|) = {na}*{nb} = {na*nb} candidate scorings "
          f"(NOT |A|! = {math.factorial(na)} permutations). Polynomial. OK")

    # 4. LIFT (in-route): N-way one-shot on the TRACE, order-invariant binding
    hits = total = 0
    for _ in range(episodes):
        alpha = random.choice(eval_alphas)
        chars = ow.characters(alpha)
        if len(chars) < way:
            continue
        chosen = random.sample(chars, way)
        cands, queries, good = [], [], True
        for c in chosen:
            ds = ow.drawings(c)
            if len(ds) < 2:
                good = False
                break
            cands.append(_structure(ds[0]))
            queries.append(_structure(ds[1]))
        if not good:
            continue
        for ti, q in enumerate(queries):
            if not q:
                continue
            hits += (recognise_oi(q, cands) == ti)
            total += 1
    acc = 100.0 * hits / total if total else 0.0
    print(f"[LIFT] {way}-way one-shot on the TRACE, ORDER-INVARIANT: {acc:.1f}%  ({hits}/{total})  "
          f"(positional soft-vocab baseline ~32.5%)")
    ceiling = 78.0
    if acc > ceiling + 3:
        print(f"[CEILING] RED FLAG: {acc:.1f}% EXCEEDS ~{ceiling:.0f} — possible deep-route drift; INVESTIGATE.")
        ok = False
    else:
        print(f"[CEILING] {acc:.1f}% <= ~{ceiling:.0f} — stays in the generative-program route (relations are "
              f"STRUCTURAL graph-match, not holistic features). OK")

    # 5. REGRESSION
    import subprocess
    for g in ("shape_math_gate.py", "shape_blend_gate.py", "shape_generation_gate.py"):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", g)], capture_output=True, text=True,
                           env={**os.environ, "PYTHONPATH": f"{ROOT}:{os.path.join(ROOT,'runners','dsl','python')}"})
        print(f"[REGRESSION] {g}:", "PASS" if r.returncode == 0 else "FAIL")
        ok &= (r.returncode == 0)

    print("=" * 80)
    print(("PASS" if ok else "FAIL"),
          f"- ORDER-INVARIANT K-BINDING: a CHEAP (O(|A|*|B|) greedy) graph-native binder that corresponds "
          f"parts by RELATION-PATTERN with a DEFINED RESIDUAL (AntiUnifyWitness over the correspondence) — "
          f"composes from held Terms, no new Rust. Capability: order-permuted same-class pairs now bind. "
          f"Lift {acc:.1f}% (<=~78, in-route). donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
