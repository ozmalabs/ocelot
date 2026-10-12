# Spectral primitive I/O guard replication v1.5 preregistration

This reruns the v1.4 12-case current/candidate-key panel after adding requested-operation and declared-port checks to the spectral construction registry. All fixtures, direct-DFT signals, magnitude ambiguity witness, arms, and replicates remain unchanged. The runner additionally captures held primitive and PrimitiveRequest names.

Expected contract: all six B forward cases build `spectral_value`, pass the independent direct-DFT oracle on all three signals, and remain accepted. All six C inverse cases must not produce an accepted `recover_signal` HeldPrimitive; the expected honest outcome is a `PrimitiveRequest` for `recover_signal`, with no term tree. The independently verified ambiguity witness remains part of the report. The source lock hashes the changed extension and current native artifact before/after the calls.

This is a targeted correction panel, not a general semantic verifier result. It does not establish capability rates beyond these fixtures or resolve all possible aliases/port conventions.

```sh
python3 evaluation/substrate_capability/spectral_io_oracle_v1_5.py --lock
python3 evaluation/substrate_capability/spectral_io_oracle_v1_5.py
python3 evaluation/substrate_capability/analyze_spectral_io_oracle_v1_5.py
```
