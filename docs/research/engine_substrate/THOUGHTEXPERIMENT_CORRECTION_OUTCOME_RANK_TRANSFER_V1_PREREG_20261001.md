# Thoughtexperiment correction outcome rank transfer v1 — preregistration

**Date:** 2026-10-01  
**Question:** Can the graph-authored correction rank Program use typed outcome records from a prior executed correction episode to order candidates differently on a fresh substrate instance?

## Design

Three fresh worker processes each run one training episode, one clean no-history episode, and one fresh experience-informed episode, for nine episodes total. All use the existing bounded runaway-correction fixture and the same graph-authored rank Program. Training records are derived only from candidates actually tried in the training episode: a selected, adopted candidate whose final model converges receives `task_utility=1`; a tried candidate that does not converge receives `task_utility=0`. These typed records are explicitly copied into the treatment graph; this transport step is host-managed and is not counted as substrate learning.

The two evaluation arms start from fresh substrate instances. The cold arm receives no `CorrectionOutcome` nodes. The transfer arm receives the training episode's typed records before the candidate ranker runs. Candidate enumeration, task inputs, and authored policy are otherwise unchanged. The primary measure is whether transferred evidence changes candidate ordering in the predicted direction; secondary measures are candidates tried, adoption, and the existing third-wave held-out oracle.

## Gates

- Three worker processes and exactly nine episodes, with distinct substrate instances.
- Every episode grounds both composers through the graph path, marks the correction Impasse ready, and identifies `sd_mint_quantum`.
- Each training episode produces at least one observed failure and one adopted successful outcome record.
- Cold graphs contain no outcome history; treatment graphs contain exactly the transported training records.
- On the transfer arm, the graph rank trace exposes nonzero prior counts for the matching target and candidate label, and places the prior-success candidate ahead of the candidate with prior failure.
- Both arms adopt `dedup_identity_fix` and pass the held-out continuation oracle.
- Source/build/native fingerprints remain stable within each worker.

## Interpretation limits

This is a repeated instance of one authored correction family. It tests whether graph data can condition rank ordering after explicit record transport; it does not establish autonomous experience persistence, learned policy construction, broad generalization, task utility prediction, or self-improvement. Timing is descriptive. A subsequent study must vary correction families and independently score task utility.
