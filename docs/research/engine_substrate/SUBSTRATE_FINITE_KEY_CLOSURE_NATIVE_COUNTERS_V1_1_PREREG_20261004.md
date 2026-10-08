# Native closure counter and instrumentation overhead v1.1 preregistration

Date: 2026-10-04

This confirmatory replay corrects two analysis defects in the retained v1 pilot: the native scheduler enumerates each fixed rule twice, and terminal state comparison must canonicalize sets rather than compare their string representations. The v1 capture remains unscored.

Repeat the paired native scale-audit off/on factorial: N={32,64,128,256}, circulant out-degree d={1,2,4,8,16}, orders ABC/CBA/BCA, and three fresh pairs per order (180 pairs, 360 closures). Each node links to the next d nodes modulo N under both `link` and `rel`; the fixed A/B/C positive finite-key rules derive shared witnesses and result edges. Pair execution order alternates by replicate.

Lock runner, analyzer, protocol, checker, manifest helper, relevant Rust matcher/substrate/audit sources, Cargo lock, native build manifest, and loaded extension; require pre/post source equality. Gate admission M=3/E=5, fixed point, no budget overshoot, progress within the finite-fact bound, exact oracle parity, exact paired graph parity, complete factorial coverage, rule-order invariance, and zero counters in the off arm. For two native enumerations per rule, expected counts are A=2Nd; B=2(Nd+Nd²); C=4N. B's clause counts are (2Nd,2Nd²), while C's are (2N,2N). Verify global/per-rule and clause/path/first-repeat conservation. Report paired instrumentation overhead descriptively.

The result concerns instrumented events on this regular synthetic family. It does not establish that these counters capture every matcher cost, natural workload prevalence, unrestricted closure complexity, or general performance.
