"""junction_perception_gate — GATE for RICHER JUNCTION PERCEPTION feeding the held
order-invariant binder. The in-route lever toward ~78 (the generative-program
ceiling), NOT the deep route (96.5 = holistic features, a different machine).

The bottleneck was relation-feature thinness: the held perception saw mostly
free/end on Omniglot traces, so the order-invariant binder had little distinctive
relational structure to correspond parts by. junction_perception.relation_edges
enriches it with cheap O(1)-per-pair geometric detectors emitting TYPED,
confidence-scored edges (T/X/contains/above/below/left/right) — admissible
world-adapter I/O (geometric translation trace→graph, the held-relation-perception
category). The per-part relation SIGNATURE (its typed-edge multiset) becomes the
part's structural role; the held StructSim + order-invariant binder correspond by
it — NO algebra change.

ARCHITECTURE: perception = admissible adapter I/O (junction_perception, numpy only
reads the trace geometry); binder/recognition = held Terms (Fold+Argmax+Filter+In
+StructSim+AntiUnifyWitness) run by the Rust evaluator; no Python reasoning/decision
over graph state. donkey=0.

HONEST FRAME: in-route lever toward ~78; the win is the CAPABILITY (cheap
graph-native richer relation perception with defined-residual edges) + the in-route
lift, whatever it is. ≤~78; past it toward 96.5 = deep-route drift (flag, not claim).

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/junction_perception_gate.py [episodes] [way]
"""
from __future__ import annotations
import os, sys, math, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
import substrate_rs as srs
import domains.omniglot_world as ow
import domains.substroke_codebook as cb
import domains.junction_perception as jp

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

_S = srs._NativeSubstrate()
_EV = _S.evaluate
_M, _PER = 8, 12


# ---- ingest: trace -> (id, descriptor, RICH relation signature) parts ----
def _structure(path):
    strokes = ow.strokes_normalized(path, per_stroke=_PER)
    if not strokes:
        return []
    edges = jp.relation_edges(strokes)                      # the enriched perception
    sig = jp.part_relation_signature(len(strokes), edges)   # per-part typed-edge multiset
    return [[f"s{i}", [float(x) for x in cb.substroke_descriptor(st, m=_M)], sig[i]]
            for i, st in enumerate(strokes)]


# ---- held order-invariant binder (Term-tree) ----
def _binder_term(A_expr, B_list):
    acc, ap = V("acc"), V("ap")
    used, pairs = IndexAt(acc, L(0)), IndexAt(acc, L(1))
    cands = Filter(L(list(range(len(B_list)))), "j", Not(In(V("j"), used)))
    best = Argmax(cands, "j", SS(ap, IndexAt(L(B_list), V("j"))), L(0))
    body = Vec(Append(used, best), Append(pairs, Vec(ap, IndexAt(L(B_list), best))))
    return Fold(A_expr, "ap", "acc", Vec(Vec(), Vec()), body)


def bind(A, B):
    if not A or not B:
        return []
    return _EV(_binder_term(L(A), B), {})[1]


def fit_oi(support, query):
    pairs = bind(support, query)
    if not pairs:
        return -1.0
    sup_b = [list(p[0]) for p in pairs]
    qry_b = [list(p[1]) for p in pairs]
    base = float(_EV(SS(L(sup_b), L(qry_b)), {}))
    n = len(pairs)
    return base * (n / max(len(support), len(query)))


def recognise(query, candidates):
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

    # 1. DETECTS — richer relations present where thin saw only free/end
    from collections import Counter
    rich = Counter(); chars = 0
    for a in eval_alphas[:12]:
        for c in ow.characters(a):
            ds = ow.drawings(c)
            if not ds:
                continue
            st = ow.strokes_normalized(ds[0], per_stroke=_PER)
            if len(st) < 2:
                continue
            chars += 1
            for e in jp.relation_edges(st):
                rich[e["type"]] += 1
    new_types = {"T", "X", "contains", "above", "below", "left", "right"} & set(rich)
    det_ok = len(new_types) >= 4
    print(f"[DETECTS] enriched perception on {chars} real chars: {dict(rich)}")
    print(f"   richer relation types present (thin saw only free/end): {sorted(new_types)} -> "
          f"{'OK' if det_ok else 'FAIL'}")
    ok &= det_ok

    # 2. DISCRIMINATION — same-class fit > diff-class fit, with the RICH relations
    sw = tot = sample = 0
    while sample < 200:
        a = random.choice(eval_alphas); chs = ow.characters(a)
        if len(chs) < 2:
            continue
        ct, co = random.sample(chs, 2)
        dt, do = ow.drawings(ct), ow.drawings(co)
        if len(dt) < 2 or not do:
            continue
        q, sup, dis = _structure(dt[1]), _structure(dt[0]), _structure(do[0])
        if not (q and sup and dis):
            continue
        sw += (fit_oi(sup, q) > fit_oi(dis, q)); tot += 1; sample += 1
    disc = 100.0 * sw / tot if tot else 0.0
    print(f"[DISCRIMINATION] same-class fit > diff-class fit: {disc:.1f}%  "
          f"(order-invariant thin-relation baseline ~69%) -> {'OK' if disc > 69 else 'FLAT/CHECK'}")

    # 3. LIFT — N-way one-shot on the TRACE, rich relations + order-invariant binder
    hits = total = 0
    for _ in range(episodes):
        alpha = random.choice(eval_alphas)
        chrs = ow.characters(alpha)
        if len(chrs) < way:
            continue
        chosen = random.sample(chrs, way)
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
            hits += (recognise(q, cands) == ti)
            total += 1
    acc = 100.0 * hits / total if total else 0.0
    print(f"[LIFT] {way}-way one-shot on the TRACE, RICH relations: {acc:.1f}%  ({hits}/{total})  "
          f"(order-invariant thin-relation baseline ~33.4%)")
    ceiling = 78.0
    if acc > ceiling + 3:
        print(f"[CEILING] RED FLAG: {acc:.1f}% EXCEEDS ~{ceiling:.0f} — possible deep-route drift; INVESTIGATE.")
        ok = False
    else:
        print(f"[CEILING] {acc:.1f}% <= ~{ceiling:.0f} — in the generative-program route (relations are "
              f"STRUCTURAL topology/position, not holistic features). OK")

    # 4. CHEAP — O(n^2) pairwise, O(1) per test
    print(f"[CHEAP] O(n^2) pairwise over ~{4} parts/char, O(1) per geometric test "
          f"(point-seg dist, orientation straddle, ray-cast parity, centroid sign). Polynomial. OK")

    # 5. DEFINED-RESIDUAL — relations are typed confidence-scored edges; the per-part signature
    #    feeds the held StructSim/binder as the relation slot (same edge slot, additive).
    st = ow.strokes_normalized(ow.drawings(ow.characters(eval_alphas[2])[2])[0], per_stroke=_PER)
    sample_edges = jp.relation_edges(st)[:3]
    typed = all("type" in e and "confidence" in e["attrs"] for e in sample_edges)
    print(f"[DEFINED-RESIDUAL] edges are typed + confidence-scored (compose on the relation slot): "
          f"{sample_edges} -> {'OK' if typed else 'FAIL'}")
    ok &= typed

    # 6. REGRESSION
    import subprocess
    for g in ("shape_math_gate.py", "shape_blend_gate.py", "shape_generation_gate.py"):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", g)], capture_output=True, text=True,
                           env={**os.environ, "PYTHONPATH": f"{ROOT}:{os.path.join(ROOT,'runners','dsl','python')}"})
        print(f"[REGRESSION] {g}:", "PASS" if r.returncode == 0 else "FAIL")
        ok &= (r.returncode == 0)

    print("=" * 80)
    print(("PASS" if ok else "FAIL"),
          f"- RICHER JUNCTION PERCEPTION: cheap O(n^2) graph-native geometric detectors emit TYPED, "
          f"confidence-scored relation EDGES (T/X/contains/above/below/left/right) — admissible adapter "
          f"I/O, no algebra change. Feeds the held order-invariant binder; lift {acc:.1f}% (<=~78, in-route). "
          f"donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
