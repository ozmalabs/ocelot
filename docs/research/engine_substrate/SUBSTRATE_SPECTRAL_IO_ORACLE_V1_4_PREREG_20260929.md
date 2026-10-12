# Spectral primitive independent I/O oracle v1.4 preregistration

## Purpose

Measure whether the accepted primitive's artifact satisfies the gap's declared input/output contract, using an independent numerical oracle. The v1.3 result motivates two fixtures: supported forward log-magnitude (`signal`→`spectrum`) and unsupported inverse (`magnitude_spectrum`→`recovered_signal`). The inverse fixture is deliberately magnitude-only; distinct real signals can share a DFT magnitude, so a unique inverse is not identifiable without additional information.

## Panel

Use the current `extend_for_gap(..., verify=True)` route in fresh graphs. Cross two key arms (unchanged faculty key; faculty plus sorted operation-head multiset), two fixtures (B forward, C inverse), and three replicates: 12 fresh graphs/calls. Preserve all returned term trees, labels, accepted decisions, and internal verifier gates. No production files are changed during the measurement.

## Independent oracle

For any returned term tree, evaluate it on three fixed length-32 real inputs: a single 3-bin cosine, a 3+7-bin mixture, and a shifted impulse. Independently compute expected one-sided `log(|DFT[k]| + 1e-9)` values with a direct complex-exponential DFT in Python. The forward contract passes only if the returned values match for every bin within absolute tolerance `1e-6`.

For C, separately construct x with x[0]=1,x[1]=2 and y with y[0]=1,y[31]=2. Verify independently that x≠y but their one-sided DFT magnitudes match within `1e-10`. The C contract is therefore not satisfied by any procedure that claims to recover a unique signal from magnitude alone. Also record term-tree free variables, whether the returned term equals B's forward term, output granularity, and the substrate verifier's accepted result. The independent oracle takes precedence over the substrate's generic tone-peak verdict.

## Gates and limits

Gate: 12/12 locked calls, stable pre/post hashes, 6/6 forward artifacts pass the numerical oracle, the non-identifiability witness passes, and every accepted C artifact is separately counted as a semantic false acceptance if it claims `recover_signal` without resolving the ambiguity. This estimates behavior only on these deterministic fixtures; it is not a natural-task capability rate.

```sh
python3 evaluation/substrate_capability/spectral_io_oracle_v1_4.py --lock
python3 evaluation/substrate_capability/spectral_io_oracle_v1_4.py
python3 evaluation/substrate_capability/analyze_spectral_io_oracle_v1_4.py
```
