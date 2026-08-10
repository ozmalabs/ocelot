def branchy(x, name):
    """if/elif/else + boolean OPERAND semantics + ternary + comparisons.
    Variants: IfStmt (elif chain); DSL IfThenElse (BoolOp desugar + IfExp),
    Eq/Not(Eq)/Gt/Gte/Lt."""
    if x > 10:
        label = "big"
    elif x > 3 and x != 7:
        label = "mid"
    else:
        label = "small"
    who = name or "anon"
    flag = 1 if x >= 0 else -1
    low = x < 0 or x == 0
    return (label, who, flag, low)
