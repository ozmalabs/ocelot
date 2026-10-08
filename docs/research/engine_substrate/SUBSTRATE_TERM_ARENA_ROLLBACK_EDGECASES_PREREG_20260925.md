# Reflected TermArena rollback edge-case preregistration

**Question.** Do malformed partial Term parses leave arena or graph residue, and does seed reflex loading retain only its durable graph representation rather than the parsed AST?

## Procedure

Use fresh native Substrates and a fixed malformed Cat Term whose first child is valid Lit JSON and whose second child has an unknown variant. For direct add_term_subgraph, require ValueError, unchanged TermArena length, and unchanged whole-graph fingerprint.

For seed loading, run one malformed reflex entry with that stimulus and require it to be skipped, with no arena or graph mutation. Then load one valid reflex with the fixed four-node Cat Term; require one Reflex node, one stimulus_term root with exact Term JSON read-back, and unchanged arena length. Record provenance against the current native extension and seed loader adapter. This is a registered evaluation probe, not ordinary pytest.

## Claim boundary

This covers one malformed parser shape and one valid/invalid reflex manifest entry. It does not cover every parse error, multi-entry partial seed failures, persistence round-trip, or long-run RSS.
