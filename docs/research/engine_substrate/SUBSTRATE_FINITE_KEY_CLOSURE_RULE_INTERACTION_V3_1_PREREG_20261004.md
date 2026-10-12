# Finite-key closure rule interaction v3.1 degree-scaling preregistration

Date: 2026-10-04

This confirmatory replay uses the v3 design with an independently indexed closure oracle to avoid repeated full-edge scans. The v3 capture is retained as an unaudited pilot because its original oracle exceeded the practical analysis budget; it is not confirmatory evidence.

Cross N={32,64,128,256}, directed circulant out-degree d={1,2,4,8,16}, three rule installation orders (ABC/CBA/BCA), and three fresh replicates (180 cases). For each node, edges to its next d nodes modulo N exist under both `link` and `rel`. The unchanged rules are A: `link`→A witness/`made_a`; B: `link(x,y)` plus `rel(y,z)`→B witness/`made_b`; C: join A/B witnesses→C and result edges.

The runner locks itself, this preregistration, the independent analyzer, finite-fragment checker, manifest helper, relevant Rust sources, Cargo lock, native build manifest, and loaded extension. Require pre/post source equality, admission M=3/E=5, native fixed point, zero budget overshoot, progress within the finite-fact bound, exact normalized nodes and edges against an independent monotone interpreter, complete 180-case factorial coverage, and terminal order invariance per N/d. Gzip preserves raw cases and graph state. Setup/closure/export time is descriptive; analytical join multiplicity N*d² describes B's candidate-binding count on the regular input, not a native matcher counter.

The claim is limited to this regular sparse three-rule finite-key family. It does not establish natural workload prevalence, arbitrary dense behavior, general analyzer/runtime equivalence, unrestricted termination, or a general native complexity exponent.
