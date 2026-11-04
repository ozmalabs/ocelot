# Representation search and process-transfer contract v1

Status: semantic freeze for P11.01–P11.E3. `RepresentationSearchPolicy` and `ProcessTransferPolicy` are disabled by default. A proposed representation or frame map is candidate evidence; it is not an adopted frame, verified process, or solved task.

## 1. Representation identity and transitions

A representation identity is the tuple `(owner_id, domain_id, domain_kind, source_epoch, model_epoch, frame_epoch, frame_id, basis_id, grain, aperture_id, latent_schema_id)`. Missing or unknown components remain explicit; they are not copied from another owner or inferred from a display name. A changed component creates a new identity. Frame changes are graph-visible transitions that retain the old frame and source evidence, record the retained/lost/escape residuals, and invalidate dependent recall, transfer candidates, and decoder receipts until reverified.

`RepresentationProposal` may vary basis, grain, aperture, latent schema, or a typed feature map. It records the training evidence IDs, source and target representation identities, proposal operator, retained/lost/escape information, model, exceptions, forward map, optional inverse map, decoder, evidence status, full description package, and cost. Acquired QualiaDimension distinctions may inform candidates only through witnessed experience features and current source epochs. A target label, held-out answer, or solution trace cannot supply the selected dimension or map.

## 2. Full description cost and split boundary

The canonical package contains at least:

```json
{
  "basis": {}, "grain": {}, "aperture": {}, "latent_schema": {},
  "model": {}, "parameters": {}, "forward_map": {}, "inverse_map": null,
  "exceptions": [], "decoder": {},
  "retained_residuals": [], "lost_residuals": [], "escape_residuals": []
}
```

Canonical JSON uses sorted keys, compact separators, UTF-8 and no non-finite numbers. Package description length is `8 * len(canonical_json_utf8(package))` bits. Training residual code length is added using the preregistered residual code; all map, parameter, exception, decoder, basis/grain/aperture/latent, and retained/lost/escape costs count. Baseline and candidate use the same serializer, residual code, event IDs, and training rows. Omitting a decoder or counting a map as free is invalid.

Proposal choice and parameter fitting use only the frozen development/training split. For an untouched held-out split, report `package_bits + heldout_residual_bits` under the frozen model without refitting, adding held-out exceptions, changing the map, or selecting a different frame. Held-out results can reject adoption but cannot choose or repair a representation. The exact residual code and task allocation are frozen in P11.E2.

## 3. Frame authority, map direction and exact transfer

Frame identity uses the Observer contract: observer owner, frame key, source epoch, selected adapter dimensions, basis, grain and aperture. A chosen frame may request a funded probe under the aperture contract. A forced frame is a hard constraint and cannot be relaxed, replaced, or downgraded to hide residuals. Unknown VOI and missing coordinates remain unknown; zero is not a substitute for missing.

Maps declare direction, source/target identities, dimensions, units, inverse status, witnesses and epochs. `A -> B` and `B -> A` are separate typed maps. Exact conjugation of source process `g_A` into target process `g_B` requires a two-sided bijection `f` with a verified inverse `f_inv`, and fresh target verification of `g_B = f ∘ g_A ∘ f_inv` under the frozen composition convention. A noninvertible abstraction can be tested as a lossy predictor, but it is never called exact conjugation and cannot mint an exact transferred ProcessSchema. Finite probes are witnessed agreement only unless the representation supplies a complete separating set.

## 4. Funding, verification and adoption

Search requests identify operation, source, owner, training split, epoch tuple, and candidate cap before work. One approved ThinkingBudget debit funds one bounded search episode; each terminal path restores the temporary policy. Candidates remain isolated from authoritative frames and process libraries until native verification succeeds on fresh target states. Failed candidates and residuals remain auditable. A stale source/model/frame/probe epoch invalidates the candidate and any dependent recall. Missing evaluators, noninvertible maps presented as exact, mismatched units, incomplete probes, and holdout leakage all return unknown/rejected.

Adoption requires lower total held-out description length under the frozen cost, no more than two percentage points solve loss, no wrong-frame acceptance, and current target-effect verification. A candidate that saves target interventions or exact checks but increases total description is not adopted. Search budget cannot lower verification, conflict, confidence, or host-safety requirements.

## 5. Acceptance and controls

- `test_decoder_cost_included`: a compact model with an expensive decoder is not treated as a shorter package.
- `test_forced_frame_not_relaxed`: a forced frame remains selected and its residual cannot be discarded by search.
- `test_noninvertible_map_not_conjugation`: one-way abstraction is never an exact process transfer.
- `test_holdout_not_selection_input`: changing held-out evidence cannot alter a training-selected candidate.
- P11.02 adds funded candidate search, full map/model/decoder/residual cost, stale-epoch invalidation and restoration.
- P11.03 adds target-native effect verification, wrong-frame refusal and nonconjugate abstention.

Registered P11 comparison remains separate: 200 source→target pairs per direction over two new process-domain pairings; 100 wrong-frame/nonconjugate controls each; fresh, source-exposed and mismatched-source arms receive matched training evidence and compute. Primary is at least 25% fewer target interventions or exact checks with solve loss ≤2 points and zero wrong-frame acceptance. Human comparison and external ARC/LS20 coverage remain unavailable unless a sourced adapter is registered.
