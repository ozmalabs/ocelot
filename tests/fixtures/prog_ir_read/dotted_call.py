def dotted_call(x):
    """Dotted extern name captured verbatim (math.sqrt) + a native oracle
    (abs). Representable; NOT ProgEval-predictable (math.sqrt undeclared)."""
    import math
    y = math.sqrt(x)
    z = abs(x)
    return (y, z)
