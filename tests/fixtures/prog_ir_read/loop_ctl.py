def loop_ctl(n):
    """for over range + break/continue + for-else.
    Variants: ForEach(orelse), LoopCtl(break, continue), CallExtern(range)."""
    total = 0
    for i in range(n):
        if i == 5:
            break
        if i % 2 == 0:
            continue
        total += i
    else:
        total = total + 100
    return total
