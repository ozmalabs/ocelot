# Exact CAN inference with a shared separator

**Run date:** 2026-09-25  
**Runner:** [`can_separator_factorization_envelope.py`](../../../scripts/can_separator_factorization_envelope.py)  
**Raw report:** [`can_separator_factorization_envelope_20260925.json`](../../../evaluation/reports/can_separator_factorization_envelope_20260925.json)

## Question and protocol

This measurement isolates the exact inference consequence of a cheap separator. It constructs modular pairwise CAN models with one shared separator of k variables and F frame interiors of m private variables each. Each frame factor is a complete graph over the shared separator plus that frame's private variables; there are no direct edges between private interiors from different frames. The model has N = k + Fm variables, domain size 2 or 3, and two deterministic replicates per configuration.

The grid covers F ∈ {2,4,8}, m ∈ {2,4}, k ∈ {0,1,2,3}, and d ∈ {2,3}: 96 graph cases, up to 35 nodes. Each case is built in the substrate graph and extracted back to an inference snapshot. The current global junction-tree MAP is compared against an independent exact algorithm that enumerates each of d^k boundary assignments, then independently enumerates each frame's d^m interior assignments under that boundary. An independent energy scorer checks both returned states. The exact clique structure supplies width k+m−1 (with disconnected frames when k=0); the measured min-fill order matches that value in every case. Cost and Python `tracemalloc` peak are separately measured for the two inference algorithms; graph construction and extraction are timed separately.

## Results

All 96 extracted factor models matched their generated fields/couplings; all global junction-tree and conditional-frame answers agreed in energy; all widths matched the constructed clique bound; and conditional work counts matched F·d^(k+m) local assignments plus d^k boundary assignments. The decomposition is exact for this explicit shared-separator construction.

Selected 3-state, m=4 measurements illustrate the scaling:

| Frames F | Boundary k | Nodes | Width | Local assignment checks | Junction-tree median | Conditional-frame median | Traced peak: junction tree / conditional |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1 | 9 | 4 | 486 | 10.27 ms | 7.05 ms | 45.9 / 3.2 KiB |
| 4 | 1 | 17 | 4 | 972 | 20.30 ms | 14.71 ms | 83.9 / 4.1 KiB |
| 8 | 1 | 33 | 4 | 1,944 | 43.19 ms | 30.42 ms | 137.3 / 5.9 KiB |
| 2 | 3 | 11 | 6 | 4,374 | 98.21 ms | 72.66 ms | 378.6 / 4.2 KiB |
| 4 | 3 | 19 | 6 | 8,748 | 223.50 ms | 148.24 ms | 794.3 / 4.7 KiB |
| 8 | 3 | 35 | 6 | 17,496 | 460.25 ms | 293.67 ms | 1,694.7 / 6.7 KiB |

For fixed m=4, k=3, d=3, doubling F approximately doubles local candidate checks (4,374 → 8,748 → 17,496) and conditional solver time (72.7 → 148.2 → 293.7 ms). At F=8 and m=4, increasing k from 1 to 3 increases conditional time from 30.4 to 293.7 ms as the conditioned boundary assignments increase from 3 to 27 and the local width grows. At F=8, m=4, k=3, changing d from 2 to 3 increases conditional time from 18.6 to 293.7 ms, reflecting the exponential dependence on the combined local scope k+m.

On these constructed cases, conditional enumeration was faster than global junction-tree and used much less traced Python peak memory. For the largest 3-state k=3 case it took about 294 ms versus 460 ms and 6.7 KiB versus 1.7 MiB. This compares two Python implementations on this specific factor shape; it does not show a general solver speedup. Both algorithms scale roughly linearly in F when k,m,d are fixed, while cost rises exponentially as local scope or domain size grows.

## Interpretation and limits

The measurement confirms the narrow mathematical point: when a model genuinely separates into frame interiors conditioned on a bounded separator, exact inference can enumerate boundary states and solve frame-local factors while preserving the global MAP. It gives a measured operation-count law for this construction and shows the expected linear-in-frame-count behavior over F=2/4/8. It also quantifies the exponential penalty in separator and local-frame dimensions.

It does not show that the substrate discovers these cuts, that its learned Frames correspond to them, or that native scoped rule execution can exchange the required separator messages. It does not validate frame maintenance under graph mutation, process RSS/native allocations, or natural task locality. The tested graphs are generated to have the desired separator by construction; Python allocation tracing excludes native graph storage.

## Next gate

Apply the same comparison to access graphs extracted from loaded runtime rules and dynamic traces. Validate every proposed cut against runtime reads/writes; then compare monolithic execution with boundary-preserving frame execution under boundary perturbations. Include frame construction, boundary updates, notifications, and synchronization in the cost. Retain disconnected components as a separate positive control.
