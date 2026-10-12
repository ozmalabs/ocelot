# Varied-topology transport solver v1 preregistration

Date: 2026-10-03  
Status: registered before capture.

## Question

Can graph-only minimum-separator proposals be passed into the generic exact conditioning solver across the varied Qwen3 transport topology census, with exact parity and lower end-to-end batch cost than monolithic junction-tree MAP?

## Fixed workload

Use the two source-locked Qwen3 exports and shared generated text corpus already used by the cross-model transport evaluation. Refit transport maps with the registered ridge value 1.0. For each of two models, four adjacent layer transitions, ten held-out inputs, and fan-in values 1, 2, 4, and 8, retain each target's top `fan_in` absolute transport coefficients among the eight dominant input modes. This yields 320 unique factor graphs. Factor semantics follow `llm_chain_transport_fanin_v1.py`: input unary fields are the selected source coefficients, output unary fields are zero, and retained bipartite pair factors are the corresponding fitted transport weights. Use vocabulary `{-1,0,1}`.

Run three fresh workers with stable opaque node permutations. Each worker compares (a) graph construction, factor extraction, min-fill ordering, and exact junction-tree MAP, and (b) graph construction, factor extraction, exhaustive graph-only minimum separator proposal, and generic exact conditioning. Reuse a proposal only for an identical anonymous topology signature within that worker. Charge proposal discovery once to the batch, report its amortized per-case cost, and report the total batch route cost. The candidate is the lexicographically first minimum separator returned by the exhaustive proposer.

## Gates

1. Three distinct worker processes each cover all 320 cases; source hashes remain stable.
2. Every reconstructed source topology matches the upstream locked topology signature and the varied-topology census key.
3. Independent recomputation confirms the proposed separator is minimum and its components match the captured graph.
4. For all cases, conditioned and junction-tree energies agree within `1e-8`; each state directly rescores to that energy; returned target signs agree; states use only the registered vocabulary; source graph/factors and substrate state are unchanged.
5. Report per-case solver timings, all charged graph/proposal/solver components, topology-cache hits, aggregate end-to-end batch ratio, and results by model/fan-in. Do not require a speedup for the experiment to pass.

## Claim boundary

This measures a specific exact solver pipeline on 320 generated, evaluator-pruned, model-derived 16-node graphs. It does not establish naturally occurring separator prevalence, task utility, general frame discovery, scaling beyond these graphs, or substrate-driven learning. Junction-tree and conditioning implementations are both Python and may have different optimization levels; performance claims are implementation-specific. Proposal amortization assumes repeated topology within the registered batch and must be shown alongside cold proposal cost.
