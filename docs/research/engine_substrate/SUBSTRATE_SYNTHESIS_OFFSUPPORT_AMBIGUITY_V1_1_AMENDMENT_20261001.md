# Off-support ambiguity v1.1 amendment — process provenance capture

The v1 capture is retained as a development diagnostic. Its runner launched a separate subprocess for every scheduled cell, but the worker row omitted its PID, so the independent analyzer could not verify the preregistered distinct-process gate. The v1 analysis records that gate as failed; v1 is not confirmatory.

V1.1 keeps the task examples, analytic oracle, candidate cap, schedule seed, and synthesis route unchanged. It adds each worker PID to the capture, points the runner lock at the matching independent analyzer, and requires 15 unique worker PIDs. The v1.1 lock includes this amendment. No v1 rows are pooled with v1.1.
