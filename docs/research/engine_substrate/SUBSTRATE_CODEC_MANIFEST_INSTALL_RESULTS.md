# Codec rule-manifest installation results

## Implementation and successful-path evidence

`codec::install_field_grammar_rules` now parses the complete embedded manifest into staged rule values before adding any rule to the live substrate. If parsing fails at any position, it truncates the TermArena and interner to their entry lengths and returns the indexed error. On success it installs each staged rule through `Substrate::add_rule`, preserving rule order and activation bookkeeping.

A locked three-replicate fresh-substrate probe confirms the successful path: every run adds, stores, and exports 20 rules; the first and last names match the manifest order (`decode_ue` and `encode_loop_complete`); every rule is active; and all three outputs are identical. The extension was rebuilt from the current source and its hash is in the lock/report.

The current runtime exposes only the compiled embedded manifest, so the probe cannot inject a malformed later rule. The failure branch is source-reviewed but not dynamically exercised. The public Rust `parse_rule_json_pub` wrapper's local rollback also remains without a direct runtime probe; native `add_rule` and `import_rules` cover their own failure paths separately.

## Reproduction

- Runner: [`substrate_codec_manifest_install_probe.py`](../../../scripts/substrate_codec_manifest_install_probe.py)
- Lock: [`codec_manifest_install_lock_20260925.json`](../../../evaluation/substrate_capability/codec_manifest_install_lock_20260925.json)
- Raw report: [`substrate_codec_manifest_install_20260925.json`](../../../evaluation/reports/substrate_codec_manifest_install_20260925.json)
- Implementation: [`codec.rs`](../../../runners/dsl/src/codec.rs)

`cargo check`, the native release build, and engine provenance passed. The build script printed its pytest command but did not run it; no ordinary tests were run. No performance claim is made.
