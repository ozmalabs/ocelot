# LLM transport varied-topology separator census v1.1 amendment

Date: 2026-10-03

The v1 worker-specific anonymous permutations intentionally change separator vertex IDs between workers. The initial repeatability gate incorrectly compared those anonymized IDs directly, so it failed despite matching all 960 source topology hashes. V1.1 retains the randomization and search, records the source topology hash only for independent post-run pairing, and compares separator cardinality, number of minima, and component-size profiles by source topology across workers. Candidate discovery still receives only the randomized anonymous graph. The failed v1 capture and source lock are retained as diagnostics; only v1.1 is confirmatory.
