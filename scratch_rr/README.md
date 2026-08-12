# scratch_rr — measurement drivers for RULE_REFERENCE_LAYER_SIZING_RESULTS.md

Every number in `docs/research/engine_substrate/RULE_REFERENCE_LAYER_SIZING_RESULTS.md`
comes from a script in this directory. They are committed for reproducibility,
exactly as `scripts/rule_signature_measure.py` was for the rule-signature slice.

**These are NOT agent code and NOT production code.** Each one:
  * is read-only over `seeds/` (parses manifests, never writes them);
  * builds throwaway `Substrate` handles it discards;
  * imports nothing production-side except `domains/rule_signature.py`
    (read and called, never edited) and `substrate/world_adapter.py` +
    `substrate/boot_*.py` for the two live-boot probes;
  * contains no decision over agent graph state.

| script | bar | what it measures |
|---|---|---|
| `rr1_covers_witness_probe.py` | RR1 | three candidate signature encodings against `Covers` / `AntiUnifyWitness` / `Substitute`, on the design spike's own worked example |
| `rr1_corpus_sweep.py` | RR1 | the same three identities over 300 positive + 150 negative real rule pairs |
| `rr2_mirror_size_and_replay.py` | RR2 | per-rule mirror node cost (via the already-exposed `add_term_subgraph`), the live booted rule population, and the checkpoint-replay amplification |
| `rr2_at_risk_files.json` | RR2 | **the enumerated at-risk file list** — the artifact CLAUDE.md's standing rule requires instead of a count |
| `rr3_completeness_probe.py` | RR3 | `RuleSummary` mirror completeness on a full `boot_core` + `load_all_seeds` agent |
| `rr4_find_families.py` | RR4 | seed-rule families sharing one tree skeleton |
| `rr4_find_parallelogram.py` | RR4 | triples with disjoint a→b / a→c path sets and a MISSING fourth corner |
| `rr4_analogical_transfer.py` | RR4 | the headline: derive the missing corner by shape math, install it, fire the 2×2 grid. Exits non-zero if any cell is wrong |
| `rr4_transfer_at_scale.py` | RR4 | the same transfer's algebraic soundness over 200 triples |
| `out/` | — | captured stdout of each, so the numbers are readable without re-running |
