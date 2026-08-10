def comp_pipeline(xs, lo):
    """List comprehension with condition + generator comprehension via sum
    + min/len oracles.
    Variants: ComprehensionList(cond), ComprehensionGen,
    CallExtern(sum/min/len)."""
    ys = [x * x for x in xs if x > lo]
    total = sum(y + 1 for y in ys)
    n = min(len(ys), 4)
    return (ys, total, n)
