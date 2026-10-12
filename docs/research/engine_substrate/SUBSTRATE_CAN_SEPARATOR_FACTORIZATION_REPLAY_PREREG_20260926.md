# Current-source CAN separator-factorization replay preregistration

## Question

Do the existing global junction-tree and conditional-frame exact-MAP implementations continue to agree on the explicit shared-separator model family, with the predicted work count `F·d^(k+m)`, on the current source and native graph artifact?

## Workload and design

Replay the 96-case grid in `scripts/can_separator_factorization_envelope.py`: F∈{2,4,8}, private frame size m∈{2,4}, shared boundary size k∈{0,1,2,3}, domain size d∈{2,3}, and the two deterministic model replicates. Execute the whole grid in three fresh worker processes. This yields three timing observations for each fixed seeded model and six observations per structural configuration (two fixed models × three processes). Each worker captures native graph insertion/extraction, min-fill width, global junction-tree MAP, conditional-frame enumeration, traced Python peak, exact energy gap, and operation counts. Aggregate worker results without conflating the two deterministic model draws with fresh model sampling.

## Gates and provenance

At each worker's start/end, lock the protocol, wrapper, underlying experiment runner, `domains/can_junction_tree.py`, `domains/graph_treewidth.py`, relevant native sources, native extension and build manifest, and commit. Require all 96 configurations per worker; exact graph extraction; width `k+m-1` (or `m-1` for disconnected k=0 frames); exact MAP energy agreement; local assignment count `F·d^(k+m)`; and stable worker inputs. An independent analyzer recomputes these structural and operation-count identities from the raw records.

## Claim boundary

The replay validates the exact cost law for one explicit common-separator construction and current implementations. It does not show native rule closure or the substrate discovers, maintains, or schedules these frames; nor does it establish natural workload locality, native allocation costs, or an arbitrary hierarchy theorem.
