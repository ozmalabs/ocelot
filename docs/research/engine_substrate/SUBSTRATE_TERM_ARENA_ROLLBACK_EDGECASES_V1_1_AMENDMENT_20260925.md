# Amendment 1.1: TermArena rollback edge-case probe

The first runner execution used assertion keys reflexes_added/reflexes_skipped for the seed-loader summary. Inspection of the authoritative PyO3 return dict showed the loader returns reflexes/reflexes_skipped. No engine result was inferred from that failed assertion: the raw v1 record is retained at substrate_term_arena_rollback_edgecases_20260925.json.

This amendment changes only the runner's expected count field to reflexes. The protocol cases and pass conditions are otherwise unchanged. The amended runner and native extension are content-locked before rerun; output is written to a separate v1.1 record.
