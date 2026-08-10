"""Standalone probe: the resulting-board EMPOWERMENT VALUE as a held Term (landing -> place -> features
free/holes/maxh -> value), verified against the host empowerment. Fast (no seeds)."""
import os, sys, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from domains.reflective_faculty import run_program_on_fresh
from probe_landing import landing_term, host_landing, SHAPES
from tetris_world import EMPTY, SETTLED
H, W = 16, 8

L = lambda v: {"type": "Lit", "value": v}
Var = lambda n: {"type": "Var", "name": n}
IA = lambda s, i: {"type": "IndexAt", "seq": s, "index": i}
Plus = lambda *x: {"type": "Plus", "items": list(x)}
Times = lambda *x: {"type": "Times", "items": list(x)}
Minus = lambda a, b: {"type": "Minus", "a": a, "b": b}
Eq = lambda a, b: {"type": "Eq", "a": a, "b": b}
Lte = lambda a, b: {"type": "Lte", "a": a, "b": b}
Not = lambda a: {"type": "Not", "arg": a}
Ite = lambda c, t, o: {"type": "IfThenElse", "cond": c, "then": t, "other": o}
Sum = lambda src, v, val: {"type": "Sum", "source": src, "var_name": v, "value": val}
MinOver = lambda src, v, val, d: {"type": "MinOver", "source": src, "var_name": v, "value": val, "default": d}
MaxOver = lambda src, v, val, d: {"type": "MaxOver", "source": src, "var_name": v, "value": val, "default": d}
Let = lambda n, val, body: {"type": "Let", "name": n, "value": val, "body": body}

ROWS = L(list(range(H))); COLS = L(list(range(W)))
filled = lambda i, c: Not(Eq(IA(IA(L_BOARD, i), c), L(EMPTY)))   # set L_BOARD per call


def value_term(board, shape, col):
    global L_BOARD
    L_BOARD = L(board)
    sh = L([list(s) for s in shape]); rs = Var("rs")
    origfilled = Sum(L(board), "row", Sum(Var("row"), "x", Ite(Not(Eq(Var("x"), L(EMPTY))), L(1), L(0))))
    free = Minus(Minus(L(H * W), origfilled), L(4))

    def colheight(cv):
        origtop = MinOver(ROWS, "i", Ite(Not(Eq(IA(IA(L(board), Var("i")), cv), L(EMPTY))), Var("i"), L(H)), L(H))
        piecetop = MinOver(sh, "c", Ite(Eq(Plus(L(col), IA(Var("c"), L(1))), cv), Plus(rs, IA(Var("c"), L(0))), L(H)), L(H))
        newtop = Ite(Lte(origtop, piecetop), origtop, piecetop)
        return Minus(L(H), newtop)

    def filledcol(cv):
        of = Sum(ROWS, "i", Ite(Not(Eq(IA(IA(L(board), Var("i")), cv), L(EMPTY))), L(1), L(0)))
        pc = Sum(sh, "c", Ite(Eq(Plus(L(col), IA(Var("c"), L(1))), cv), L(1), L(0)))
        return Plus(of, pc)

    maxh = MaxOver(COLS, "col", colheight(Var("col")), L(0))
    holes = Sum(COLS, "col", Minus(colheight(Var("col")), filledcol(Var("col"))))
    value = Minus(free, Plus(Times(L(4), holes), Times(L(0.5), maxh)))
    return Let("rs", landing_term(board, shape, col), value)


def host_value(board, shape, col):
    r = host_landing(board, shape, col)
    if r is None or r < 0:
        return None
    nb = [row[:] for row in board]
    for dr, dc in shape:
        if 0 <= r + dr < H:
            nb[r + dr][col + dc] = SETTLED
    free = sum(row.count(EMPTY) for row in nb)
    holes = 0
    for c in range(W):
        seen = False
        for i in range(H):
            if nb[i][c] != EMPTY:
                seen = True
            elif seen:
                holes += 1
    maxh = max((H - next((i for i in range(H) if nb[i][c] != EMPTY), H) for c in range(W)), default=0)
    return free - 4 * holes - 0.5 * maxh


def main():
    rng = random.Random(2); ok = 0; tot = 0; mism = []
    for _ in range(250):
        board = [[SETTLED if rng.random() < 0.25 and r > H // 2 else EMPTY for _ in range(W)] for r in range(H)]
        shape = rng.choice(SHAPES); col = rng.randint(0, W - 1 - max(c for _, c in shape))
        hv = host_value(board, shape, col)
        res = run_program_on_fresh(value_term(board, shape, col), {})
        if not res.get("ran"):
            print("EVAL FAIL:", res.get("reason")); return 1
        nv = float(res["value"])
        tot += 1
        if abs(nv - hv) < 1e-6:
            ok += 1
        elif len(mism) < 6:
            mism.append((hv, nv, col))
    print(f"empowerment VALUE Term matches host: {ok}/{tot}")
    if mism:
        print("  mismatches (host,native,col):", mism)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
