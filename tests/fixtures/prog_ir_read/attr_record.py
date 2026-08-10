def attr_record(r, k):
    """Attribute get/set on a program value (ProgEval records are dicts —
    the documented P1 record convention; CPython twin uses an object).
    Variants: AttrSet, AttrGet (incl. the aug-assign desugar)."""
    r.count = k + 1
    r.count += 2
    total = r.count * 2
    return total
