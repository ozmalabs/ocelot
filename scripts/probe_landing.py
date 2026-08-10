"""Standalone probe: build the LANDING-ROW Term (gravity falls until first collision) and verify it
matches the host drop() exactly. Fast (fresh substrate, no seeds)."""
import os, sys, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from domains.reflective_faculty import run_program_on_fresh
from tetris_world import EMPTY, SETTLED
H, W = 16, 8

L = lambda v: {"type": "Lit", "value": v}
Var = lambda n: {"type": "Var", "name": n}
IA = lambda s, i: {"type": "IndexAt", "seq": s, "index": i}
Plus = lambda *x: {"type": "Plus", "items": list(x)}
Minus = lambda a, b: {"type": "Minus", "a": a, "b": b}
Gt = lambda a, b: {"type": "Gt", "a": a, "b": b}
Gte = lambda a, b: {"type": "Gte", "a": a, "b": b}
Eq = lambda a, b: {"type": "Eq", "a": a, "b": b}
Not = lambda a: {"type": "Not", "arg": a}
Ite = lambda c, t, o: {"type": "IfThenElse", "cond": c, "then": t, "other": o}
Sum = lambda src, v, val: {"type": "Sum", "source": src, "var_name": v, "value": val}
MinOver = lambda src, v, val, d: {"type": "MinOver", "source": src, "var_name": v, "value": val, "default": d}


def landing_term(board, shape, col):
    r = Var("r"); cell = Var("c")
    dr = IA(cell, L(0)); dc = IA(cell, L(1))
    rr = Plus(r, dr); cc = Plus(L(col), dc)
    cellcol = Ite(Gte(rr, L(H)), L(1),
                  Ite(Not(Eq(IA(IA(L(board), rr), cc), L(EMPTY))), L(1), L(0)))
    collide = Gt(Sum(L([list(s) for s in shape]), "c", cellcol), L(0))
    first = MinOver(L(list(range(H + 1))), "r", Ite(collide, r, L(H + 5)), L(H + 5))
    return Minus(first, L(1))


def host_landing(board, shape, col):
    if col < 0 or col + max(c for _, c in shape) >= W:
        return None
    r = 0
    while not any(r + dr >= H or (r + dr >= 0 and board[r + dr][col + dc] != EMPTY) for dr, dc in shape):
        r += 1
    return r - 1


SHAPES = [[(0, 0), (0, 1), (1, 0), (1, 1)], [(0, 0), (1, 0), (2, 0), (3, 0)],
          [(0, 0), (1, 0), (2, 0), (2, 1)], [(0, 0), (0, 1), (0, 2), (1, 1)]]


def main():
    rng = random.Random(1); ok = 0; tot = 0; mism = []
    for _ in range(300):
        board = [[SETTLED if rng.random() < 0.25 and r > H // 2 else EMPTY for _ in range(W)] for r in range(H)]
        shape = rng.choice(SHAPES); col = rng.randint(0, W - 1 - max(c for _, c in shape))
        hl = host_landing(board, shape, col)
        res = run_program_on_fresh(landing_term(board, shape, col), {})
        if not res.get("ran"):
            print("EVAL FAIL:", res.get("reason")); return 1
        nl = int(res["value"])
        tot += 1
        if nl == hl:
            ok += 1
        elif len(mism) < 5:
            mism.append((hl, nl, col))
    print(f"landing Term matches host: {ok}/{tot}")
    if mism:
        print("  mismatches (host,native,col):", mism)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
