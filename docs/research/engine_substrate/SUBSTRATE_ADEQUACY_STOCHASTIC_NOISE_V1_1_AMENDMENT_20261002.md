# Stochastic noise panel v1.1 pre-capture amendment

The initial lock was written successfully, but the runner's next invocation compared a JSON-decoded lock (whose tuple-valued schedule fields become lists) with an in-memory manifest containing tuples. The mismatch was detected before any worker started. The design constants now use lists consistently; no conditions, noise probabilities, provider counts, or trial counts changed. The initial lock remains as a diagnostic artifact, and the confirmatory run uses the v1.1 lock, which also binds this amendment.
