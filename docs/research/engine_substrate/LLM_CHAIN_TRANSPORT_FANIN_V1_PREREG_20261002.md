# LLM chain transport fan-in replication v1 preregistration

## Question and data

Does the cost/accuracy effect of learned transport sparsity repeat across independently fit adjacent-layer transitions? Use the existing Qwen3-0.6B `chain_L10_14.npz` export, containing 60 training and ten held-out coefficient vectors at each of L10–L14. Fit a separate 32×32 transport for each of L10→11, L11→12, L12→13, and L13→14 using only that hop's training pairs and ridge 1.0.

For every hop and held-out input, select the eight largest-absolute source coefficients and first eight target modes. Keep each target's strongest 1/2/4/8 fitted incoming weights, tie-breaking by source-column order. Construct a fresh 3-state CAN graph and compare exact JT, an exhaustive 3^8-source-assignment oracle with conditional target minimization, BP, and the pruned linear readout. Three fresh workers process the complete hop × input × fan-in grid.

## Gates

Verify source/export stability, full coverage, exact live-graph factor extraction, expected node/edge counts, component accounting, valid min-fill triangulation widths, JT/oracle/direct-energy equality, prediction-score arithmetic, topology signatures across workers, and no graph mutation. Record graph construction, extraction, ordering, JT, and BP times separately. Report each hop/fan-in pair; do not collapse hop variation into a single universal estimate.

## Claim boundary

This is a replication across four adjacent transitions from the same model, corpus, and layer-chain export. It tests transfer across layer-specific fitted transports but not independent model or task transfer, natural graph construction, autonomous separator discovery, or language-task utility. The fan-in operation remains explicitly authored using training-fitted weights.

## Artifacts

- Runner: [llm_chain_transport_fanin_v1.py](../../../evaluation/substrate_capability/llm_chain_transport_fanin_v1.py)
- Analyzer: [analyze_llm_chain_transport_fanin_v1.py](../../../evaluation/substrate_capability/analyze_llm_chain_transport_fanin_v1.py)
- Lock: [llm_chain_transport_fanin_v1_lock_20261002.json](../../../evaluation/substrate_capability/llm_chain_transport_fanin_v1_lock_20261002.json)
- Capture: [llm_chain_transport_fanin_v1_20261002.json](../../../evaluation/reports/llm_chain_transport_fanin_v1_20261002.json)
- Analysis: [llm_chain_transport_fanin_v1_analysis_20261002.json](../../../evaluation/reports/llm_chain_transport_fanin_v1_analysis_20261002.json)
