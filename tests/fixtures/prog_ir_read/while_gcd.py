def while_gcd(a, b):
    """while + tuple-unpack swap (Euclid).
    Variants: While, TupleUnpack, ContainerLit(tuple); DSL Mod, Not(Eq)."""
    while b != 0:
        a, b = b, a % b
    return a
