def try_raise(x):
    """try/except Exception + raise (constructed exception -> extern trap,
    caught either way — the documented raise-spelling divergence).
    Variants: TryOr, Raise, IfStmt."""
    try:
        if x < 0:
            raise ValueError("neg")
        y = x * 2
    except Exception as e:
        y = -1
    return y
