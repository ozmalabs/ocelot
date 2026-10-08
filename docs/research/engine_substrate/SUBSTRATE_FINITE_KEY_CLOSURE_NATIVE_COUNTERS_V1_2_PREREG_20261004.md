# Native closure counter and instrumentation overhead v1.2 preregistration

Date: 2026-10-04

This confirmatory replay corrects the retained v1.1 candidate formula to account for rule-order-dependent native enumeration counts. The v1.1 capture is retained as a pilot: its exact graphs and raw counters remain useful, but its fixed two-enumeration assumption rejects valid BCA schedules.

Repeat the paired native scale-audit off/on factorial: N={32,64,128,256}, circulant out-degree d={1,2,4,8,16}, orders ABC/CBA/BCA, and three fresh pairs per order (180 pairs, 360 closures). Each node links to the next d nodes modulo N under `link` and `rel`; fixed positive finite-key rules A/B/C derive shared witnesses and result edges. Pair execution order alternates by replicate.

Lock runner, analyzer, protocol, checker, manifest helper, relevant Rust matcher/substrate/audit sources, Cargo lock, native build manifest, and loaded extension; require pre/post source equality. Gate M=3/E=5 admission, fixed point, no budget overshoot, progress within finite-fact bound, exact independent oracle parity, paired graph parity, full factorial coverage, canonical rule-order invariance, and zero counters in audit-off arms. For each enabled arm, derive the expected count from the observed native `rule_enumerations` metric per rule: A contributes N·d per enumeration; B contributes N·d + N·d²; C contributes 2N. Clause expectations are respectively (N·d), (N·d,N·d²), and (N,N), multiplied by that rule's enumeration count. Require global/per-rule and clause/path/first-repeat conservation. Report paired instrumentation cost descriptively.

The result concerns instrumented events on this regular synthetic family. It does not establish counter coverage for every matcher path, natural workload prevalence, unrestricted closure complexity, or general performance.
