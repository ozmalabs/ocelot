def out_of_set(xs):
    """OUT-OF-SET on purpose: With + Lambda + Delete + Assert — the honest
    residual test expects exactly these blocker names, no partial emit."""
    with open("f") as fh:
        data = fh.read()
    g2 = lambda t: t + 1
    del data
    assert xs
    return [g2(x) for x in xs]
