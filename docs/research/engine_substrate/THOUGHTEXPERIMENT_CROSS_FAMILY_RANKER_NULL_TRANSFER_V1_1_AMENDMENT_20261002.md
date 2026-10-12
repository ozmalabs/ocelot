# Cross-family ranker null-transfer probe v1.1 — amendment

The v1 reviewer could not join the emitted candidate digests to the held-out control-kind capture: adding the graph-composer seed changes the generated candidate bundle digests, even though candidate labels match. The v1 capture is preserved, but its held-out utility comparison is invalid and is not evidence.

V1.1 replaces the cross-capture join with an explicit two-stage protocol. First, three rank workers capture their full candidate bundles and cold/experience orders in an immutable order artifact. Only after that artifact exists does the parent launch separate fresh scoring workers with the exact captured bundles. The scoring workers run the held-out control-name oracle and return utilities; they do not call the ranker. The new lock includes both code paths, task seed, and recurrence training capture. No v1.1 utility value is inferred from v1 or from candidate labels alone.
