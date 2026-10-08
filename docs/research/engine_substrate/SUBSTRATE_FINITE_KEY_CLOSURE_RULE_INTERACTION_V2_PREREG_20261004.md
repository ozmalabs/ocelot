# Finite-key closure rule interaction v2 current-source preregistration

Date: 2026-10-04

## Question and frozen rule family

Repeat the prior three-rule positive interaction gate on current source and expand graph size. Initial nodes N={4,8,16,32,64,128,256}; topologies are a directed cycle and a directed path, each present independently under both `link` and `rel`. Rule A matches one `link` edge, mints/reuses `Witness{tag:A}`, and adds `made_a(x,A)`. Rule B joins `link(x,y)` and `rel(y,z)`, mints/reuses `Witness{tag:B}`, and adds `made_b(x,B)`. Rule C joins `made_a(x,a)` and `made_b(x,b)`, mints/reuses `Witness{tag:C}`, and adds `result(a,C)` and `result(b,C)`. Install in ABC, CBA, or BCA order. Run three fresh Substrate constructions per cell, 126 total cases.

## Gates

Lock runner, independent analyzer, protocol, finite-fragment checker, manifest helper, native parser/matcher/graph/scheduler sources, build manifest, Cargo lock, and loaded extension. Require pre/post lock equality; checker admission with M=3 and E=5; native `fixed_point`, no budget overshoot, and progress ≤ the computed finite-fact bound; exact normalized node/edge parity with an independent monotone closure interpreter; and order-invariant terminal semantics for every N/topology pair. Record setup-plus-closure-plus-export time as descriptive, not as the proof. Preserve all cases and failures; the v1 N≤8 capture remains historical.

## Claim boundary

This is one three-rule positive family over two path-like topologies and three installation orders. It does not prove all analyzer-admitted programs, unrestricted termination, a general wall-time exponent, or natural graph prevalence. It excludes deletion, updates, negation, computed mint values, and external state.
