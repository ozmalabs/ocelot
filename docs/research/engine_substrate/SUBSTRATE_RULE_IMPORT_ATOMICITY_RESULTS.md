# Rule parse and import atomicity results

## Change

`add_rule` now snapshots the TermArena and interner lengths before parsing and rolls both back if parsing fails. `import_rules` parses the full input into staged `RewriteRule` values before installing any of them. A parse error discards the staged values and restores both suffixes, preventing a partial rule prefix. Successful installation remains in input order and restores inactive entries as tombstones. Failed `define_concept` parsing now also restores newly interned symbols as well as Term nodes.

The new `Interner::truncate` removes only symbols appended after a known checkpoint. These rollback calls occur while newly parsed rules/concepts remain local and before their Sym values escape into persistent substrate state.

## Verification

The post-change locked runner used three replicates and 25 fresh Substrate instances per failure case. All 75 malformed `add_rule` calls and all 75 imports that parsed a valid first rule before failing on the second rule were rejected. In every case, TermArena length and rule count stayed at baseline, and a subsequent unique interned marker received exactly the next pre-failure Sym ID. A successful import control retained two rules in their original order and restored the second rule as inactive.

`cargo check -p substrate-rs`, `scripts/engine_build.sh`, and engine provenance verification passed. The build script printed its pytest command but did not run it; no ordinary tests were run. The run verifies parse-failure atomicity for the covered APIs; it does not directly invoke the public Rust `parse_rule_json_pub` helper, measure allocator capacity/RSS, cover panic recovery during installation, or exercise concurrent import behavior.

## Reproduction

- Runner: [`substrate_rule_import_atomicity_probe.py`](../../../scripts/substrate_rule_import_atomicity_probe.py)
- Lock: [`rule_import_atomicity_lock_20260925.json`](../../../evaluation/substrate_capability/rule_import_atomicity_lock_20260925.json)
- Raw report: [`substrate_rule_import_atomicity_20260925.json`](../../../evaluation/reports/substrate_rule_import_atomicity_20260925.json)
- Ownership context: [`SUBSTRATE_TERM_ARENA_OWNERSHIP_AUDIT.md`](SUBSTRATE_TERM_ARENA_OWNERSHIP_AUDIT.md)
