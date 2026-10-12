# Finite-key closure rule interaction v3 degree-scaling preregistration

Date: 2026-10-04

## Question and design

Measure how candidate join work and end-to-end cost vary with graph degree for the same interacting three-rule positive family. Use directed circulant ring graphs: each node has edges to its next d nodes modulo N, separately for `link` and `rel`. Cross N={32,64,128,256}, d={1,2,4,8,16}, three rule installation orders (ABC, CBA, BCA), and three fresh replicates, for 180 cases. The existing fixed rule family is retained: A matches one link edge and derives `made_a`; B joins `link(x,y)` with `rel(y,z)` and derives `made_b`; C joins the A/B witnesses and emits result edges.

## Frozen gates and records

The runner and analyzer are frozen by a SHA-256 lock alongside protocol, finite-fragment checker, manifest helper, relevant Rust source, Cargo lock, native build manifest, and loaded extension. Require pre/post source equality, fragment admission with M=3 and E=5, fixed-point status, no budget overshoot, progress within the static finite-fact bound, exact normalized terminal graph equality with an independent monotone closure interpreter, exact 180-cell coverage, and order-invariant terminal semantics per N/d. Preserve raw per-case graph, analysis, report, and setup/closure/export wall time in gzip. Timing is descriptive. Report median candidate counts analytically as N*d² for B's two-edge join on this regular graph; this is not a native matcher counter and does not include engine-specific index work.

## Claim boundary

The result applies to one regular sparse three-rule family with finite literal mint keys. It does not establish performance on arbitrary dense graphs, natural task graphs, general analyzer/runtime equivalence, unrestricted termination, or an asymptotic bound for native work.
