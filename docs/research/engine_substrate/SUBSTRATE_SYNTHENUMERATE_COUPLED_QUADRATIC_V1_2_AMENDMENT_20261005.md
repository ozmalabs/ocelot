# Bounded coupled-quadratic synthesis v1.2 amendment

V1.1 is preserved as an interrupted capture. At the larger size bound it found at least one term consistent with the training labels but wrong on held-out inputs; the reuse timer then raised because it assumed every found term transferred. This is a runner defect, not a substrate result. The partial raw file and v1.1 lock remain untouched and are excluded from outcome rates.

V1.2 retains v1.1's size bound of 11 and all task, grammar, constant, candidate, repetition, and schedule settings. It corrects the capture contract: every found term is scored on all held-outs, and reuse timing is performed only when all held-out predictions are exact. A failed-transfer candidate remains a found candidate with its predictions and is not treated as an execution failure. A fresh lock and complete raw capture are required. The original v1 design and v1.1 budget amendment remain linked for provenance.
