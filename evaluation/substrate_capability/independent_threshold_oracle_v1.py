"""Separately implemented oracle for the threshold adequacy transfer panel."""
def label(inputs):
    if set(inputs) != {"left", "right", "limit"}:
        raise ValueError("expected exactly left, right, and limit")
    return inputs["left"] + inputs["right"] > inputs["limit"]
