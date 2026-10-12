# Substrate edge-identity composer v1 — preregistration

## Question

Can the general structural composer produce a useful edge-identity guard directly from a residual cue, with site hypotheses derived by the reusable `domains.edit_ops` vocabulary and selected as graph-resident `EditSite` nodes? This gate removes the thoughtexperiment harness's edge-site scanner and finite candidate pool from the proposal path.

## Tasks and procedure

Use the same faulted recurrence and conversation rules as the bidirectional guard pilot. For each family, a fixed residual cue identifies the target rule and describes the observed failure. It does not provide a candidate rule, operator name, or site list. The runner calls `compose_general_structural_variant` once and records the resulting operator, site, rule digest, and timing. Two fresh training episodes score the proposal; the selected proposal is frozen before a separate held-out process scores two fresh episodes. Four source/native-locked workers repeat both families.

Positive controls run the unmodified source rule. A no-overlap cue must abstain. A conversation cue that identifies the target and operator but leaves three edge sites indistinguishable must also abstain on the site choice. Primary source rules must remain unchanged by composition. The harness may construct the fault, residual cue, episode data, and independent oracle; it must not scan rule ASTs for edge sites, enumerate guard variants, call `_default_candidates`, or rank candidate edits.

## Fixed cues and expected outputs

- Recurrence cue: `mrl offer due once edge output candidate`; expected generic edit class/site: `add_edge_identity_guard`, outgoing `candidate` / `has_mint_offer`.
- Conversation cue: `reply adjacency message response responds_to once edge output`; expected generic edit class/site: `add_edge_identity_guard`, incoming `m` / `responds_to`.
- Ambiguous-site control: `reply adjacency message once edge output`; target/operator may be selected, but equal site scores must yield an honest abstention.
- No-overlap control: `unrelated`; no target or proposal may be selected.

## Gates and interpretation

Require four complete workers, exact target/operator/site in every order record, all training and held-out proposals correct, both source controls correct, both abstention controls correct, unchanged primary target rules, stable locked sources, and complete nonnegative phase timing. Record proposal-generation and oracle-scoring time separately. This is a prompted two-family proposal-generation result, not autonomous residual discovery, open-ended operator invention, or general self-improvement. Failure to select the intended site is an informative composer boundary and must not be repaired after lock without a new version.

Capture source lock, then training orders, then held-out scores, and analyze the frozen artifacts. The runner imports only the earlier episode/target helpers from the bidirectional-guard harness; that helper source is included in the lock.
