def fstring_is(v, x):
    """f-string + is/is not None.
    Variants: FString, IsOp (both polarities); DSL IfThenElse (IfExp)."""
    kind = "none" if v is None else "some"
    msg = f"v={kind}, x={x}"
    ok = v is not None
    return (msg, ok)
