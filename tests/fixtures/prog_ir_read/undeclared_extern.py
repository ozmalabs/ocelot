def undeclared_extern(x):
    """Calls a name no oracle declares — IR-representable, and ProgEval
    traps extern:helper_quantity honestly (never a value)."""
    y = helper_quantity(x)
    return y + 1
