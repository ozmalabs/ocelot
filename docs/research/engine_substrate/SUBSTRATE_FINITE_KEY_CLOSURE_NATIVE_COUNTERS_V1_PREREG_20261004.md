# Native closure counter and instrumentation overhead v1 preregistration

Date: 2026-10-04

## Design

Repeat the interaction degree-scaling factorial as paired audit-off/audit-on closures: N={32,64,128,256}, circulant out-degree d={1,2,4,8,16}, three fixed rule installation orders (ABC/CBA/BCA), and three fresh substrate constructions per order (180 pairs, 360 closures). Each input contains the next d directed neighbors under both `link` and `rel`. The unchanged A/B/C rule family derives shared witnesses and result edges. Pair order is counterbalanced by replicate.

The enabled arm turns on native global scale audit and per-rule attribution only for closure; the disabled arm explicitly turns both off. Record global counters, per-rule metrics, clause counts, exact graph, closure report, and end-to-end setup/closure/export wall time. Lock runner, analyzer, protocol, checker, manifest helper, relevant Rust matcher/substrate/audit sources, Cargo lock, build manifest, and loaded extension; require pre/post fingerprint equality.

## Gates

Require all 180 pairs, matching status/progress and exact normalized graphs between audit arms, independent monotone-oracle parity, finite-fragment admission M=3/E=5, fixed point, no budget overshoot, progress within the conservative fact bound, and rule-order-invariant terminal semantics. For the family, verify per-rule candidate counts: A = N·d; B = N·d + N·d²; C = 2N. Verify B's two clause counts N·d and N·d², C's two clause counts N each, global candidate enumeration/test counters reconcile with per-rule totals, and every enabled counter's named conservation checks. The disabled arm must report zero counters and no per-rule rows. Instrumentation overhead is descriptive and must be computed as paired audit-on/off timing ratios and differences.

## Claim boundary

Counters report instrumented native events under this one regular sparse finite-key workload. They do not establish that these counters capture every possible matcher cost, general closure complexity, natural graph prevalence, or workload representativeness.
