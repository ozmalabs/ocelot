# Semantic ingress contract v1 preregistration

Date: 2026-10-03  
Runner: [`semantic_ingress_contract_v1.py`](../../../evaluation/substrate_capability/semantic_ingress_contract_v1.py)  
Lock: [`semantic_ingress_contract_v1_lock_20261003.json`](../../../evaluation/substrate_capability/semantic_ingress_contract_v1_lock_20261003.json)

## Question

Does the substrate's explicit semantic-event API materialize a supplied neutral proposition with source-event provenance, keep a proposal distinct from accepted knowledge, and fail closed on raw-text and text-bearing proposition inputs?

## Design

Run three fresh `WorldAdapter(seeds=())` graphs per condition, loading only the `proposition_commitment_lifecycle` rule manifest. The three conditions are: (1) valid, explicitly structured neutral proposition marked `proposed`; (2) otherwise valid proposition containing a forbidden `text` field; (3) raw string supplied as the semantic frame. Each case uses a unique evidence ID. Record graph node counts, bridge result, proposition status, evidence and origin links, accepted-claim edge, and exception type. The lock covers runner and Python ingress sources, graph/seed wrappers, the loaded native extension, and the lifecycle seed; hashes are checked before and after execution.

## Preregistered gates

- Valid structured proposition: supported, exactly one Proposition added, an evidence node and source-event link exist, status remains `proposed`, and no `accepted_claim` edge is present.
- Text-bearing proposition: explicit unsupported result and zero Proposition nodes added.
- Raw string frame: `TypeError` and no graph mutation.
- All three replicates per condition must satisfy their gate; report every row and all locked input hashes.

## Scope limits

This is the substrate's explicit adapter contract under a minimal lifecycle seed. The provider supplies the predicate, argument, polarity, and provenance. The assay does not measure natural-language extraction, authentication of provider identity, truth of an assertion, memory retrieval, or general self-improvement. The previous all-seed evaluator is not used because it booted the complete seed set separately for every case and did not finish during the observed run; the minimal fixture tests this ingress seam directly.
