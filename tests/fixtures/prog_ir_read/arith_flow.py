def arith_flow(a, b, k=3):
    """Sequencing + arithmetic + aug-assign + default param + tuple return
    + the floordiv statement-lift (q — exact int semantics via the native
    ProgAugAssign floordiv prelude).
    Variants: Seq, DefFnParam(default), AssignVar, AugAssign, Return,
    ContainerLit(tuple); DSL Plus/Times/Minus/Div/Mod/Pow/Neg."""
    t = a * b + k
    t += a
    u = t - b
    u %= 7
    v = t / 2
    w = k ** 2
    n = -u
    q = (t + u) // 3
    return (t, u, v, w, n, q)
