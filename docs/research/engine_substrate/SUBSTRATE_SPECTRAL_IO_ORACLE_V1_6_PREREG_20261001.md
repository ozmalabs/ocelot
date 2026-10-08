# Spectral primitive I/O oracle v1.6 — current-source replay preregistration

**Purpose.** Replay the v1.5 forward-construction and inverse-refusal panel against the current checkout after its prior source lock drifted. This is a current-source replication of one registered construction family, not a new-family or autonomous-invention test.

## Frozen cases and procedure

Use the unchanged v1.5 cases: six `spectral_value` forward requests and six magnitude-only `recover_signal` inverse requests, crossed with the two existing faculty-key arms and three replicates per request. Build a fresh `WorldAdapter(seeds=())` graph per case. Call the production `extend_for_gap(..., verify=True)` path. The runner imports the frozen v1.5 case/measurement helper, but hashes that helper and all current implementation/native dependencies into this v1.6 lock. Randomize the 12-case order with seed `20261016`. Capture each returned Term tree, held primitive/request nodes, independent-forward-oracle values, outcome, and wall/CPU time.

The analyzer independently recomputes the direct DFT log-magnitude oracle from the fixed length-32 tone, mixed-tone, and shifted-impulse signals. It must verify every returned value within `1e-6`; confirm all six forward requests are installed as `spectral_value`; confirm all six inverse requests produce no accepted Term or `recover_signal` primitive and instead produce a `PrimitiveRequest`; and confirm two distinct signals with numerically equal one-sided magnitudes remain non-identifiable (maximum difference `<= 1e-10`). It also checks the pre/post source lock and all 12 unique fresh graph identities.

## Interpretation and limits

A pass means the captured current source still builds the registered forward recipe correctly and refuses this underdetermined inverse. It does not show that the substrate selected the formula: the construction registry, formula, constraints, and task labels are supplied by `domains/substrate_extension.py` and this fixture. It does not generalize beyond this alias, operator composition, and input signature. No source is modified by the run. The resulting lock and raw capture are immutable evidence for the source version recorded in the lock.

## Artifacts and execution

- Runner: [`spectral_io_oracle_v1_6.py`](../../../evaluation/substrate_capability/spectral_io_oracle_v1_6.py)
- Independent analyzer: [`analyze_spectral_io_oracle_v1_6.py`](../../../evaluation/substrate_capability/analyze_spectral_io_oracle_v1_6.py)
- Lock: [`spectral_io_oracle_v1_6_lock_20261001.json`](../../../evaluation/substrate_capability/spectral_io_oracle_v1_6_lock_20261001.json)
- Raw: [`spectral_io_oracle_v1_6_raw_20261001.json`](../../../evaluation/reports/spectral_io_oracle_v1_6_raw_20261001.json)

From the repository root, first capture `python3 evaluation/substrate_capability/spectral_io_oracle_v1_6.py --lock`, then run `python3 evaluation/substrate_capability/spectral_io_oracle_v1_6.py`, and independently analyze with `python3 evaluation/substrate_capability/analyze_spectral_io_oracle_v1_6.py`.
