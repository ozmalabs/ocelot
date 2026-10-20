"""PROCESS-ALGEBRA INVENTION PROBE (exploration only, not agent code).

Question: can a generic operator set INVENT processes nobody supplied, by
algebra over the processes already held, and do those inventions let the
agent do something it could not do before?

Invention operators (domain-neutral, only need compose + inverse):
    inverse(a)          undo a
    compose(a, b)       a then b
    conjugate(a, s)     s, a, s^-1        "do a, but in s's frame"   (analogy)
    commutator(a, b)    a, b, a^-1, b^-1  "the part of a and b that does not commute"

Candidates are judged by EFFECT, not description (two expressions with the
same effect are the same process; keep the cheapest = MDL):
    novelty    effect not already in the library
    precision  support = how much of the world it touches (small = a tool)
    cost       primitive steps

Domains:
  1. Loopover NxN (rows shift right, columns shift down). Task nobody gave a
     process for: put a scrambled board back. Compare primitive-only search
     against search with invented tools.
  2. The shape-decode DimensionGenerators (rotation90, reflection_r,
     reflection_c) as 2x2 integer matrices: what does the algebra invent, and
     what LAWS (relations) fall out?

This is a Python prototype of operator SEMANTICS to decide whether a graph-
native version (a Term + seed rules) is worth building. It makes no agent
decisions in the substrate and touches no seed.
"""
from __future__ import annotations

import itertools
import random
from collections import deque

# --------------------------------------------------------------------------
# Generic process algebra over permutations (process = position -> position)
# --------------------------------------------------------------------------


def compose(a, b):            # a then b
    return tuple(b[a[i]] for i in range(len(a)))


def inverse(a):
    inv = [0] * len(a)
    for i, j in enumerate(a):
        inv[j] = i
    return tuple(inv)


def conjugate(a, s):          # s, a, s^-1
    return compose(compose(s, a), inverse(s))


def commutator(a, b):         # a, b, a^-1, b^-1
    return compose(compose(compose(a, b), inverse(a)), inverse(b))


def support(a):
    return [i for i, j in enumerate(a) if i != j]


def identity(n):
    return tuple(range(n))


def apply(state, p):          # content at i moves to p[i]
    out = [None] * len(state)
    for i, j in enumerate(p):
        out[j] = state[i]
    return tuple(out)


# --------------------------------------------------------------------------
# Domain 1: Loopover
# --------------------------------------------------------------------------


def loopover_primitives(n):
    prims = {}
    for i in range(n):
        p = list(range(n * n))
        for c in range(n):
            p[i * n + c] = i * n + (c + 1) % n
        prims[f"R{i}"] = tuple(p)
    for j in range(n):
        p = list(range(n * n))
        for r in range(n):
            p[r * n + j] = ((r + 1) % n) * n + j
        prims[f"C{j}"] = tuple(p)
    # inverses are held too (an undo is part of knowing a move)
    for k in list(prims):
        prims[k + "'"] = inverse(prims[k])
    return prims


def invent(prims, max_support=3, rounds=1):
    """One invention round: inverse/compose/conjugate/commutator over the
    library, dedup by effect, keep cheapest, mint precise novel effects."""
    lib = {eff: (name, 1) for name, eff in prims.items()}   # effect -> (expr, cost)
    n = len(next(iter(prims.values())))
    lib.setdefault(identity(n), ("I", 0))
    minted = []
    for _ in range(rounds):
        items = list(lib.items())
        for (ea, (xa, ca)), (eb, (xb, cb)) in itertools.product(items, items):
            for op, eff, expr, cost in (
                ("comm", commutator(ea, eb), f"[{xa},{xb}]", 2 * (ca + cb)),
                ("conj", conjugate(ea, eb), f"{xb}·{xa}·{xb}⁻¹", ca + 2 * cb),
            ):
                s = len(support(eff))
                if s == 0:
                    continue
                if eff not in lib or cost < lib[eff][1]:
                    is_new = eff not in lib
                    lib[eff] = (expr, cost)
                    if is_new and s <= max_support:
                        minted.append((op, expr, cost, s, eff))
    return lib, minted


def three_cycle_closure(base_tools, prims, n):
    """Conjugate invented 3-cycles by primitive setups (BFS over setups) until
    every 3-cycle of the board is reachable. Returns effect -> (expr, cost)."""
    target = n * n * (n * n - 1) * (n * n - 2) // 3
    tools = {}
    for expr, cost, eff in base_tools:
        tools.setdefault(eff, (expr, cost))
    frontier = deque([((), identity(n * n))])
    seen_setups = {identity(n * n)}
    while frontier and len(tools) < target:
        word, setup = frontier.popleft()
        for expr, cost, eff in base_tools:
            c = conjugate(eff, setup)
            ccost = cost + 2 * len(word)
            if c not in tools or ccost < tools[c][1]:
                tools[c] = (f"{'·'.join(word) or 'ε'}⟨{expr}⟩", ccost)
        if len(word) < 6:
            for name, p in prims.items():
                ns = compose(setup, p)
                if ns not in seen_setups:
                    seen_setups.add(ns)
                    frontier.append((word + (name,), ns))
    return tools, target


def solve_with_tools(state, tools, n):
    """Place pieces one at a time; each step is ONE invented 3-cycle that moves
    the needed piece home without disturbing already-placed cells."""
    by_move = {}
    for eff, (expr, cost) in tools.items():
        sup = support(eff)
        for a in sup:
            by_move.setdefault((a, eff[a]), []).append((cost, eff, sup))
    state = list(state)
    goal = list(range(n * n))
    moves, steps = 0, 0
    placed = set()
    for i in range(n * n - 2):
        if state[i] != i:
            j = state.index(i)
            best = None
            for cost, eff, sup in by_move.get((j, i), []):
                if any(s in placed for s in sup):
                    continue
                if best is None or cost < best[0]:
                    best = (cost, eff)
            if best is None:
                return False, moves, steps
            state = list(apply(state, best[1]))
            moves += best[0]
            steps += 1
        placed.add(i)
    return state == goal, moves, steps


def primitive_iddfs(state, prims, max_depth):
    goal = tuple(range(len(state)))
    frontier = {tuple(state)}
    seen = set(frontier)
    for d in range(max_depth + 1):
        if goal in frontier:
            return True, d
        nxt = set()
        for s in frontier:
            for p in prims.values():
                t = apply(s, p)
                if t not in seen:
                    seen.add(t)
                    nxt.add(t)
        frontier = nxt
    return False, None


def run_loopover(n=3, trials=40, scramble_len=30, prim_depth=None, seed=7):
    print(f"\n=== Loopover {n}x{n} ===")
    prims = loopover_primitives(n)
    lib, minted = invent(prims, max_support=3)
    print(f"held primitives: {len(prims)}  distinct effects after 1 invention round: {len(lib)}")
    print(f"minted precise novel tools (support<=3): {len(minted)}")
    by_op = {}
    for op, *_ in minted:
        by_op[op] = by_op.get(op, 0) + 1
    print(f"  by operator: {by_op}")
    cheapest = sorted(minted, key=lambda m: (m[3], m[2]))[:3]
    for op, expr, cost, s, eff in cheapest:
        print(f"  e.g. {expr:<14} cost={cost:2d} moves {s} cells: {support(eff)}")
    base = [(expr, cost, eff) for op, expr, cost, s, eff in minted if s == 3]
    tools, target = three_cycle_closure(base, prims, n)
    print(f"3-cycle tools after conjugation closure: {len(tools)}/{target}")

    rng = random.Random(seed)
    names = list(prims)
    ok_tools = ok_prim = 0
    tot_moves = tot_steps = 0
    unreachable = 0
    depth = prim_depth if prim_depth is not None else (5 if n == 3 else 4)
    for _ in range(trials):
        s = tuple(range(n * n))
        for _ in range(scramble_len):
            s = apply(s, prims[rng.choice(names)])
        solved, moves, steps = solve_with_tools(s, tools, n)
        ok_tools += solved
        if solved:
            tot_moves += moves
            tot_steps += steps
        else:
            unreachable += 1
        ok_prim += primitive_iddfs(s, prims, depth)[0]
    print(f"solve rate, primitives only (search depth {depth}): {ok_prim}/{trials}")
    print(f"solve rate, with invented tools:                 {ok_tools}/{trials}"
          + (f"  (mean {tot_steps/ok_tools:.1f} tool uses, {tot_moves/ok_tools:.0f} primitive moves)"
             if ok_tools else ""))
    return {"n": n, "minted": len(minted), "tools": len(tools), "target": target,
            "ok_tools": ok_tools, "ok_prim": ok_prim, "trials": trials,
            "unsolved_with_tools": unreachable}


def lifted_law(max_n=5):
    """Is the invented tool a SCHEMA? Test [R_i, C_j] across all i, j, n."""
    print("\n=== Lifting: is [R_i, C_j] the same process at every size? ===")
    for n in range(2, max_n + 1):
        prims = loopover_primitives(n)
        sizes = set()
        for i in range(n):
            for j in range(n):
                sizes.add(len(support(commutator(prims[f"R{i}"], prims[f"C{j}"]))))
        print(f"  n={n}: support of [R_i,C_j] over all i,j = {sorted(sizes)}")


def parity_probe(max_n=5):
    """Odd board sizes give even primitives; even sizes give odd ones. Does
    the invented-tool solver hit a wall the algebra can EXPLAIN?"""
    print("\n=== Parity: which boards can 3-cycles alone finish? ===")
    for n in range(2, max_n + 1):
        prims = loopover_primitives(n)
        r0 = prims["R0"]
        # parity of an n-cycle = n-1
        par = "odd" if (n - 1) % 2 else "even"
        print(f"  n={n}: a row shift is an {n}-cycle -> {par} permutation; "
              f"3-cycles are even, so {'they cannot fix an odd scramble alone' if par=='odd' else 'they generate every reachable scramble'}")


# --------------------------------------------------------------------------
# Domain 2: the held DimensionGenerators as 2x2 integer matrices
# --------------------------------------------------------------------------


def mat(a, b, c, d):
    return (a, b, c, d)


def mmul(x, y):  # x then y  (as maps on column vectors: y @ x)
    a, b, c, d = y
    e, f, g, h = x
    return (a * e + b * g, a * f + b * h, c * e + d * g, c * f + d * h)


def minv(x):
    a, b, c, d = x
    det = a * d - b * c
    assert det in (1, -1)
    return (d * det, -b * det, -c * det, a * det)


def run_matrices():
    print("\n=== Shape-decode generators as matrices ===")
    I = mat(1, 0, 0, 1)
    held = {"rot90": mat(0, -1, 1, 0), "refl_r": mat(1, 0, 0, -1), "refl_c": mat(-1, 0, 0, 1)}
    names = {v: k for k, v in held.items()}
    names[I] = "I"
    frontier = dict(held)
    invented = {}
    for _round in range(2):
        new = {}
        items = list({**held, **invented}.items())
        for (na, a), (nb, b) in itertools.product(items, items):
            for expr, eff in ((f"{na}·{nb}", mmul(a, b)),
                              (f"{nb}·{na}·{nb}⁻¹", mmul(mmul(minv(b), a), b)),
                              (f"[{na},{nb}]", mmul(mmul(mmul(a, b), minv(a)), minv(b)))):
                if eff not in names and eff not in new:
                    new[eff] = expr
        for eff, expr in new.items():
            names[eff] = expr
            invented[expr] = eff
    meaning = {mat(-1, 0, 0, -1): "rot180", mat(0, 1, -1, 0): "rot270",
               mat(0, 1, 1, 0): "transpose (diagonal reflection)",
               mat(0, -1, -1, 0): "anti-transpose"}
    print(f"held 3, invented {len(invented)} new transforms (closure = {len(names)} incl. identity):")
    for expr, eff in invented.items():
        print(f"  {expr:<22} = {meaning.get(eff, eff)}")
    print("laws discovered (relations equal to identity, shortest first):")
    laws = []
    for k in (2, 4):
        for name, g in held.items():
            p = I
            for _ in range(k):
                p = mmul(p, g)
            if p == I and not any(l.startswith(name) for l in laws):
                laws.append(f"{name}^{k} = I")
    for (na, a), (nb, b) in itertools.combinations(held.items(), 2):
        if mmul(mmul(mmul(a, b), minv(a)), minv(b)) == I:
            laws.append(f"{na} and {nb} commute")
        elif mmul(mmul(minv(b), a), b) in held.values():
            laws.append(f"{nb}·{na}·{nb}⁻¹ = {names[mmul(mmul(minv(b), a), b)]}  (conjugation = same process in another frame)")
    for l in laws:
        print(f"  {l}")


def parity(p):
    seen, odd = set(), 0
    for i in range(len(p)):
        if i in seen:
            continue
        j, length = i, 0
        while j not in seen:
            seen.add(j)
            j = p[j]
            length += 1
        odd ^= (length - 1) & 1
    return odd


def state_as_perm(state):
    # state[i] = which piece sits at i; the permutation that restores it
    return tuple(state[i] for i in range(len(state)))


def run_parity_wall(n=4, trials=20, seed=11):
    """Odd-length scrambles on an even board. The invented 3-cycles are all
    EVEN, so they cannot finish an odd scramble. The algebra predicts this
    from an invariant (permutation parity is a homomorphism), and the same
    invariant names the fix: spend one ODD held process first."""
    print(f"\n=== Parity wall on {n}x{n} (odd scrambles) ===")
    prims = loopover_primitives(n)
    _, minted = invent(prims, max_support=3)
    base = [(expr, cost, eff) for op, expr, cost, s, eff in minted if s == 3]
    tools, _ = three_cycle_closure(base, prims, n)
    tool_par = {parity(e) for e in tools}
    odd_prims = sorted(k for k, p in prims.items() if parity(p) == 1)
    print(f"parity of every invented tool: {tool_par};  odd held primitives: {len(odd_prims)}")
    rng = random.Random(seed)
    names = list(prims)
    plain = fixed = 0
    for _ in range(trials):
        s = tuple(range(n * n))
        for _ in range(31):
            s = apply(s, prims[rng.choice(names)])
        plain += solve_with_tools(s, tools, n)[0]
        # invariant-driven repair: if the scramble's parity differs from the
        # tools' reachable parity, apply one odd primitive, then solve.
        if parity(state_as_perm(s)) == 1:
            s = apply(s, prims[odd_prims[0]])
        fixed += solve_with_tools(s, tools, n)[0]
    print(f"solve rate, invented 3-cycles only:           {plain}/{trials}")
    print(f"solve rate, 3-cycles + parity-invariant fix:  {fixed}/{trials}")


if __name__ == "__main__":
    r3 = run_loopover(3)
    r4 = run_loopover(4, trials=20, scramble_len=30)
    run_parity_wall(4)
    lifted_law()
    parity_probe()
    run_matrices()
