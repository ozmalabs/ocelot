"""Independent Boolean oracles for the adequacy evidence noise panel."""
def label(task, inputs):
    if task == "parity":
        if set(inputs) != {"value"}:
            raise ValueError("parity takes exactly value")
        return inputs["value"] % 2 == 0
    if task == "threshold":
        if set(inputs) != {"left", "right", "limit"}:
            raise ValueError("threshold takes left, right, and limit")
        return inputs["left"] + inputs["right"] > inputs["limit"]
    raise ValueError(f"unknown task: {task}")
