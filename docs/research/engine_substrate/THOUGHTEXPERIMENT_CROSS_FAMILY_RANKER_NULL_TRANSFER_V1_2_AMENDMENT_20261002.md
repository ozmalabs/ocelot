# Cross-family ranker null-transfer probe v1.2 — amendment

V1.1 wrote a complete three-worker order artifact with source parity, then exited nonzero while serializing a `Path` in its console summary. The order data are retained as a failed harness attempt and will not be used for scoring. V1.2 corrects the summary serialization and writes to new lock, order, and score paths; it repeats the order stage from fresh workers before launching separate held-out scorers. The earlier v1 digest-join failure and v1.1 post-write exit failure remain preserved and disclosed.
