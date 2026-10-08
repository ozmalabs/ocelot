//! Universal codec field-grammar Rules — installed in the runner.
//!
//! These Rules walk any FieldSpec chain (linear or with conditional
//! gating or with loops) dispatching on `field.kind` and the gating
//! / iteration graph structure. They are codec-AGNOSTIC: a new codec
//! is a new FieldSpec chain, not new code.
//!
//! Before this module the Rule definitions lived in
//! `tests/test_codec_graph_resident.py` (~600 lines of Python
//! Term-builder code). Per the project's "concepts in gamma OR Rust
//! runner" principle, the universal machinery belongs with the runner
//! (graph-data Rules, but installed natively); test-side Python
//! merely calls `install_field_grammar_rules` and supplies the
//! per-codec field grammar.
//!
//! Rule set (18 total):
//!   decode_ue / decode_se / decode_u   — linear ue/se/u(n)
//!   decode_skip                         — conditional miss
//!   loop_init / loop_iter_ue/se/u       — iteration
//!   loop_complete
//!   encode_ue / encode_se / encode_u   — mirror of decode
//!   encode_skip
//!   encode_loop_init / encode_loop_iter_ue/se/u
//!   encode_loop_complete
//!
//! The rule data is embedded as a JSON string (built once from the
//! Python reference and pasted in). Parsing into native
//! `RewriteRule`s reuses the existing `parse_rule_json` path so a
//! single source of truth for the JSON dialect remains.

use crate::jsonio;
use crate::substrate::Substrate;

const FIELD_GRAMMAR_RULES_JSON: &str = include_str!("codec_field_grammar_rules.json");

/// Install the universal field-grammar Rule set on `substrate`.
/// Returns the number of rules added. Safe to call multiple times
/// (each call adds an independent copy) — but typical use is once
/// per Substrate, before seeding any per-codec FieldSpec chains.
pub fn install_field_grammar_rules(substrate: &mut Substrate) -> Result<usize, String> {
    let json: serde_json::Value = serde_json::from_str(FIELD_GRAMMAR_RULES_JSON)
        .map_err(|e| format!("bad embedded codec rules JSON: {}", e))?;
    let arr = json
        .as_array()
        .ok_or_else(|| "rules JSON must be an array".to_string())?;
    let initial = substrate.rules.len();
    let terms_before = substrate.terms.nodes.len();
    let symbols_before = substrate.interner.len();
    let mut staged = Vec::with_capacity(arr.len());
    for (i, rule_json) in arr.iter().enumerate() {
        let rule = match crate::py::parse_rule_json_pub(
            rule_json,
            &mut substrate.terms,
            &mut substrate.interner,
        ) {
            Ok(rule) => rule,
            Err(err) => {
                substrate.terms.nodes.truncate(terms_before);
                substrate.interner.truncate(symbols_before);
                return Err(format!("rule {}: {}", i, err));
            }
        };
        staged.push(rule);
    }
    for rule in staged {
        // Route through `add_rule` — the SOLE path that makes a newly-installed
        // rule live. A raw `substrate.rules.push(rule)` here left every rule
        // `active: false` (the matcher skips them) AND skipped the cost-based
        // match-edge reorder, index-hint provisioning, `derive_access`, and the
        // parallel bookkeeping vectors add_rule maintains — so all 20 codec
        // field-grammar rules installed DEAD (0 firings) for ~48 days. See
        // VISION_BASELINE_LIST_RESULTS.md §1 and VISION_CODEC_ACTIVATE_RESULTS.md.
        substrate.add_rule(rule);
    }
    // Avoid an unused-import warning if jsonio isn't referenced.
    let _ = jsonio::term_from_json;
    Ok(substrate.rules.len() - initial)
}
