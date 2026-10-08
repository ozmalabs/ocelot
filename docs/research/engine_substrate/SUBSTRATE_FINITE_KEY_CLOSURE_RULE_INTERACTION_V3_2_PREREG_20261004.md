# Finite-key closure rule interaction v3.2 degree-scaling preregistration

Date: 2026-10-04

This confirmatory replay corrects the v3.1 expected case-ID template to match the recorded `n{N}_d{degree}_{order}_r{replicate}` IDs. The v3 and v3.1 captures are retained as pilots; neither is confirmatory because the v3 oracle was too slow and the v3.1 analyzer factorial assertion used the wrong ID form.

The frozen design is 180 cases crossing N={32,64,128,256}, directed circulant out-degree d={1,2,4,8,16}, rule installation orders ABC/CBA/BCA, and three fresh replicates. Each node connects to its next d nodes modulo N under both `link` and `rel`. The unchanged positive rules are A: `link`→A witness/`made_a`; B: `link(x,y)` plus `rel(y,z)`→B witness/`made_b`; C: join A/B witnesses→C and result edges.

Lock runner, indexed independent analyzer, this protocol, finite-fragment checker, manifest helper, relevant Rust sources, Cargo lock, build manifest, and loaded extension. Require source equality pre/post, M=3/E=5 admission, fixed point, zero budget overshoot, progress within the finite-fact bound, exact normalized graph equality against the monotone closure interpreter, exact factorial IDs, and terminal invariance across rule orders for each N/d. Preserve raw graph states in gzip. Wall time includes setup, closure, and export and is descriptive. Candidate multiplicity N*d² is a combinatorial count for B's join on this regular input, not a measured native matcher counter.

Claim limits: one regular sparse positive rule family, finite literal mint keys, and the tested sizes/degrees only. No unrestricted termination, arbitrary-density, natural-task prevalence, or general native complexity theorem is inferred.
