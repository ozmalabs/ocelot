# List PBE pilot results (2026-09-25)

**Run state:** pilot. **Protocol:** [`SUBSTRATE_LIST_PBE_PREREG_20260925.md`](SUBSTRATE_LIST_PBE_PREREG_20260925.md). **Raw record:** [`substrate_list_pbe_pilot_20260925.json`](../../../evaluation/reports/substrate_list_pbe_pilot_20260925.json). **Pre-run lock:** [`list_pbe_pilot_lock_20260925.json`](../../../evaluation/substrate_capability/list_pbe_pilot_lock_20260925.json).

## Result

The direct native `SynthEnumerate` run completed all 44 task/condition searches without a crash, in 3.73 s wall time. On 22 paired tasks, fixed declared grammar passed 16/22 (72.7%, descriptive Wilson 95% interval 51.8–86.8%) and typed-default passed 14/22 (63.6%, 43.0–80.3%). Fourteen tasks passed in both arms, two only in the fixed grammar, none only in typed-default, and six in neither. The pilot is too small and synthetic to support a population estimate or general induction claim.

The fixed grammar used 857,966 candidate evaluations in total (median 4,784/task); typed-default used 1,237,950 (median 2,884/task). Summed search time was 1.53 s and 2.11 s respectively. Maximum per-search time was 586 ms and 450 ms respectively. Each arm found two programs that failed at least one holdout. All six shared failures reached the 200,000-candidate budget: `map_abs`, `sum_positive`, `sum_squares`, `sum_even`, `median`, and `unique_count` (the latter two belong to the declared-inventory controls). The fixed grammar solved `reverse` and the one-off `map_plus_three`, which typed-default did not solve within budget. Both arms passed all tested reductions, all filters, and the underdetermined last-element control; results by category and each program are in the raw record.

The two false accepts expose concrete limits: both arms selected `1 + min(1, xs[-1])` for the even-sum task, and a short length-based expression for unique-count. The revealed examples did not exclude these spurious programs; held-out evaluation correctly rejected them. The out-of-inventory controls are negative only relative to the fixed declared operator list: typed-default can have a different inventory, so they do not establish a universal negative control.

## Cost and provenance

Parent peak RSS was 335,332 KiB for the process; this is a process high-water mark including imports and both arms. Recorded parent CPU time covers the measurement loop after imports (3.69 s user, 0.04 s system). The native extension hash is `ca49e588a9787dad9b957f3e18718d0f0cd72cde85091d2b9edca350965cd4d9`. The lock contains hashes for generator, data, harness, protocol, synthesizer, codec, PBE wiring, Cargo lock, and extension. The worktree was dirty at run time, so the report records content hashes and commit rather than implying a clean checkout.

## Interpretation and next step

This establishes a fresh task-family measurement for bounded direct enumeration, including a held-out check and budget failures. It does not exercise the P4 residual trigger, rung routing, hypothesis expansion, mint/adoption, reuse, or learning economics. The difference between grammars is descriptive and confounded by their operator inventories and enumeration order; do not interpret it as a causal grammar-quality estimate. The next E2 step is an instrumented end-to-end residual-to-search pilot on a separate frozen family, recording when the residual activates, rung transitions, candidate depth, mint/reuse, and total acquisition/application cost. Confirmatory work still needs a larger independently held-out family and preregistered controls.
