# Finite-key closure scale v1.2 current-source preregistration

Date: 2026-10-04

## Question

Does the previously validated finite-key monotone insertion fragment continue to reach exact fixed points within its conservative fact bound on current source as graph size increases beyond 64 nodes, under sparse and dense initial topology?

## Design

Use the same one-edge positive rule schema as scale v1.1: each of M={1,2,4} fixed literal signatures matches `link(x,y)`, conditionally creates a `Witness{tag:literal}`, and inserts `link(y,witness)` with empty edge attrs. Cross N={4,16,64,128,256} initial nodes, cycle and dense directed no-self-loop initial graphs, and three fresh `Substrate` constructions per cell: 90 cases. The dense maximum is N=256 (65,280 initial edges). Keep the 200,000 progress budget. Compute the theorem's syntactic bound using the independent fragment analyzer and compare terminal nodes/edges with an independently reconstructed oracle. Record case wall time separately from graph size and native progress/pass counts.

## Gates and limits

Lock the runner, analyzer, finite-key checker, protocol, graph/rewrite/substrate/parser source files, native build manifest, loaded native extension, and Cargo lock before capture; require identical lock inputs after capture. Preserve all cells and failures. Require analyzer admission, native fixed point, exact terminal graph, and progress within the formula `B=M+(N+M)^2-e0`. The result measures selected synthetic instances of one fixed rule family. It does not prove uniform wall-time scaling, general closure termination, or natural workload prevalence. V1.1 through N=64 remains historical and is not overwritten.
