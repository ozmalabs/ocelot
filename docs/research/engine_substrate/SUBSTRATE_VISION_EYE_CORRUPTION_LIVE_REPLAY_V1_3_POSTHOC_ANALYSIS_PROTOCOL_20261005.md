# Live corruption replay v1.3 post-hoc analysis protocol

This is exploratory numerical analysis of the fixed live v1 capture. No new engine run occurs, and the observed winner-parity issue predates this protocol.

Recreate each corrupted mask from its clean v2.1 held-out probe using the exact SHA-256-derived seed string and the same set-copy, sorted sample, `difference_update`/`update` operations as the offline v1.2 scorer. Preserve that reconstructed set object when summing weights so its iteration order matches the reference scorer. Require its sorted members to equal the live capture mask and its digest to equal the offline record. Check activation reconstruction with relative tolerance `2e-15` and absolute floor `1e-300`.

Report native winners' exact membership in the reconstructed maximum set separately from membership within one ULP. The ULP tolerance is exploratory and cannot change the original strict exact-max result. Derive unit regions from weight-based receptive centers; report native single-winner accuracy separately from exact-max set-valued accuracy and mark ties spanning both correct and incorrect regions ambiguous.

Integrity gates cover locked inputs, original capture and v2.1 source consistency, 12 unique workers/six pairs, exact weights and clean outputs, all 3,456 corruption masks, frozen weights, activation reconstruction, and one-ULP winner membership. Since this analysis was specified after observing the result, passing is a reproducibility result only; it is not independent robustness, semantic visual capability, online learning, or self-improvement evidence.

The v1.1 and v1.2 analyzers are preserved as invalidated attempts: v1.1 summed a sorted mask; v1.2 rebuilt a set from sorted members and did not preserve the corruption routine's insertion history. Reproduce v1.3 with `python3 evaluation/substrate_capability/analyze_vision_eye_corruption_live_replay_v1_3.py --lock`, then invoke it without arguments.
