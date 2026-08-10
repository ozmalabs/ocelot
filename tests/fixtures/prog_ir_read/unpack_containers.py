def unpack_containers(p):
    """Unpack + list/dict literals + subscript read/write + len oracle.
    Variants: TupleUnpack, ContainerLit(list/dict/tuple), Subscript,
    SubscriptSet, CallExtern(len)."""
    a, b = p
    xs = [a, b, a + b]
    d = {"lo": xs[0], "hi": xs[2]}
    d["mid"] = xs[1]
    xs[0] = 0
    d["hi"] += a
    return (d["lo"], d["mid"], d["hi"], xs[0], len(xs))
