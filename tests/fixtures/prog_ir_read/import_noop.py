def import_noop(z):
    """import + from-import inside the body (ProgEval no-ops; uses trap at
    use sites). Variants: ImportStmt (both forms)."""
    import math
    from os import path, sep
    w = z + 1
    return w
