# Term-directed floating-point edge probes v1.2 amendment

The v1.1 analyzer replayed the policy and independently obtained the same 520/0/0 wide-domain mismatch counts, but compared its recomputed finite holdout object with a capture field that intentionally stores only the finite exactness flag. The resulting schema check failed. V1.1 is diagnostic. V1.2 changes only that analyzer comparison, binds the corrected analyzer and runner in a fresh lock, and repeats the deterministic capture. No policy, candidate, probe, or holdout changes.
