"""shape_generation_programs — the reified GENERATE / RECOVER Programs as
graph-resident Term-trees (the compositions verified in shape_generation_gate.py,
now graph data the substrate evaluator runs).

These are TERM-TREE BUILDERS (admissible seed/builder work — they EMIT graph data,
no reasoning, no decisions). The generation/recovery reasoning IS the Term-tree
(Fold/Substitute/AntiUnifyWitness/Atan2 run by the Rust evaluator); a builder just
assembles that tree. The residual-LAW is supplied at invocation via env Vars
(turn0, dturn, nsteps), so ONE GENERATE Program yields circle (constant turn,
dturn=0), spiral (compounding, dturn>0), or line (turn0=0). RECOVER differences a
trail's consecutive steps into the turning residual (constant => circle; constant
2nd-difference => spiral).

A shape = the fed-forward iterate of the held difference operator:
    state_{n+1} = advance(state_n, sigma_n);  sigma_{n+1} = update(sigma_n).
"""
from __future__ import annotations

# turtle-state Tuple = (x, y, heading, turn, dturn, trail); positional (read by IndexAt —
# Attr reads only graph nodes, not Dict values, so state is a Tuple).
_X, _Y, _H, _TURN, _DTURN, _TRAIL = 0, 1, 2, 3, 4, 5
STEP = 1.0


def _L(v): return {"type": "Lit", "value": v}
def _V(n): return {"type": "Var", "name": n}
def _Vec(*items): return {"type": "Vec", "items": list(items)}
def _IndexAt(seq, i): return {"type": "IndexAt", "seq": seq, "index": i}
def _Plus(*xs): return {"type": "Plus", "items": list(xs)}
def _Times(*xs): return {"type": "Times", "items": list(xs)}
def _Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def _Sin(a): return {"type": "Sin", "arg": a}
def _Cos(a): return {"type": "Cos", "arg": a}
def _Atan2(y, x): return {"type": "Atan2", "y": y, "x": x}
def _Append(seq, item): return {"type": "Append", "seq": seq, "item": item}
def _Fold(src, var, acc, init, body):
    return {"type": "Fold", "source": src, "var_name": var, "acc_name": acc,
            "init": init, "body": body}
def _MapList(src, var, value):
    return {"type": "MapList", "source": src, "var_name": var, "value": value}


def generate_program() -> dict:
    """GENERATE Program (Term-tree): the Fold-iterate of the residual operator over
    a threaded turtle-state Tuple. Reads its residual-LAW from env Vars:
        turn0  — initial residual (constant turn);  dturn — its update (0 => circle/line,
        >0 => spiral);  steps — the step-index list (length = #steps).
    Returns the threaded final state (whose TRAIL slot is the trajectory = the shape).
    state_{n+1}: h+=turn; advance by STEP along h; turn+=dturn; append the new point."""
    st = _V("st")
    h_n = _Plus(_IndexAt(st, _L(_H)), _IndexAt(st, _L(_TURN)))             # h += turn
    x_n = _Plus(_IndexAt(st, _L(_X)), _Times(_L(STEP), _Cos(h_n)))         # forward
    y_n = _Plus(_IndexAt(st, _L(_Y)), _Times(_L(STEP), _Sin(h_n)))
    turn_n = _Plus(_IndexAt(st, _L(_TURN)), _IndexAt(st, _L(_DTURN)))      # sigma update
    body = _Vec(x_n, y_n, h_n, turn_n, _IndexAt(st, _L(_DTURN)),
                _Append(_IndexAt(st, _L(_TRAIL)), _Vec(x_n, y_n)))
    init = _Vec(_L(0.0), _L(0.0), _L(0.0), _V("turn0"), _V("dturn"), _Vec())
    return _Fold(_V("steps"), "i", "st", init, body)


def recover_program() -> dict:
    """RECOVER Program (Term-tree): the INVERSE — differences a trajectory's
    consecutive steps into the turning RESIDUAL sequence (system-ID). Reads env Var
    `trail` (the list of (x,y) points) and `idx` (the indices 2..n-1). For each i:
    turn_i = atan2(sin dh, cos dh), dh = heading(i,i-1) - heading(i-1,i-2);
    heading(a,b) = atan2(dy, dx) of the segment b->a. A CONSTANT turn-sequence is a
    circle's residual-law; a constant 2nd-difference is a spiral's. Returns the
    turn-sequence (the recovered residual, which the read-out classifies)."""
    trail = _V("trail")
    def pt(k): return _IndexAt(trail, k)
    def heading(i, j):
        pi, pj = pt(i), pt(j)
        return _Atan2(_Minus(_IndexAt(pi, _L(1)), _IndexAt(pj, _L(1))),
                      _Minus(_IndexAt(pi, _L(0)), _IndexAt(pj, _L(0))))
    i = _V("i")
    im1 = _Minus(i, _L(1))
    im2 = _Minus(i, _L(2))
    dh = _Minus(heading(i, im1), heading(im1, im2))
    turn_i = _Atan2(_Sin(dh), _Cos(dh))                                   # wrap-free turning residual
    return _MapList(_V("idx"), "i", turn_i)
