# Local synthetic 320-study evidence

`LOCAL_SYNTHETIC_320_EVIDENCE.json` is a deterministic **development-control artifact**, regenerated with `python3 scripts/generate_p2_local_synthetic_evidence.py`. It invokes the locally built `p2_native_worker` for every canonical 4 × 8 × 5 × 2 envelope and requires every proposal to carry `P2BoundedFutureManifoldV1` selection provenance. Its receipt commitments are synthetic, its seed/key are fixed local development values, and it has no release lock, rootless-Podman custody, hardened-probe execution, evaluator receipt authority, or externally trusted signing authority.

It is therefore **not external P2-B1 release evidence** and cannot satisfy the preregistered primary gate. The current regenerated artifact records 320/320 route-provenanced proposals, Brier 0.935, ECE 0.021, validity 320/320, safety 320/320, and feasible-minimal 170/320. The last figure is expected for this synthetic fixture’s abstentions and is below the release threshold; it is retained to prevent synthetic controls from being mistaken for a capability claim.

A release result remains unpopulated until a separately locked run completes all 320 episodes, real hardened Podman controls (including both hostile probe images), evaluator receipt chaining, and the preregistered gate. See `PREREGISTRATION.md` and `RESULTS_TEMPLATE.md`.
