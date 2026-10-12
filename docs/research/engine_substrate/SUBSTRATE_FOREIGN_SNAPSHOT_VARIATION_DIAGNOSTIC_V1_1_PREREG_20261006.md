# Foreign-snapshot variation diagnostic v1.1: hash-seed contrast

Date: 2026-10-06  
Status: prospective amendment after the fixed-seed v1 capture passed all repeatability checks.

## Question

Does the foreign-snapshot input, reconstructed enumeration, or generated model output vary when otherwise identical fresh workers use distinct recorded Python hash seeds?

## Design

Repeat the same three-worker global held-topic workload and read-only producer trace from v1, using `PYTHONHASHSEED` values 1, 2, and 3 for workers 0, 1, and 2 respectively. The seed-zero v1 capture is the fixed-seed comparator. Keep the same source closure, task order, teaching facts, and three-worker count. Do not change production source or disable rules.

At each foreign-snapshot call compare the exact input graph digest and contents, reconstructed foreign enumeration IDs and semantic labels, returned fixed/volatile samples, and generated model attributes. Treat hash-seed differences as observations; do not assume repeatability across different seeds is required. Report whether the differing final graph records are explained by input graph differences, enumeration differences, or later model construction.

## Gates and limits

- Three distinct worker processes; each reports its assigned seed, seven turns, and stable source fingerprints.
- Analyzer verifies complete capture and reports per-call cross-seed equality separately for inputs, enumeration, and model outputs.
- The existing seed-zero capture remains immutable. This contrast diagnoses one authored workload and does not establish cross-runtime determinism or scheduler parity.
