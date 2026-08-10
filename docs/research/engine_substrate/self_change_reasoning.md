# Proof-carrying self-change

`self_change_reasoning` turns self-modification into an ordinary graph-native
learning process. It does not grant the agent arbitrary source editing. It
requires the agent to state what failed, explain a candidate intervention,
risk that explanation against controls, canary it, and retain it only after the
gain survives restart and transfer.

The world boundary may record observations and measured outcomes. It must not
choose a patch, rank candidates, waive a proof, or decide whether to keep a
change. Those decisions are rules in
`seeds/self_change_reasoning.json`, executed by Rust.

## Graph protocol

```text
FaultProbe
  → ObservedGap
  → CausalHypothesis
  → ChangeSpec → RulePatch
  → ProofObligation
  → Trial
  → Canary
  → Commit | Abort
  → Consolidation
```

A `FaultProbe` is measurement, not interpretation. It can report false
positives, false negatives, outcome mismatch, relation counterfactuals, repeated
no-op firings and resource excess. The graph currently holds five deliberately
small patch families:

| Family | Smallest proposed intervention |
|---|---|
| `threshold_adjustment` | Move or relax one threshold |
| `guard_strengthening` | Add one context discriminator |
| `relation_addition` | Add one causally supported relation |
| `effect_substitution` | Replace one effect while holding the trigger fixed |
| `firing_budget_guard` | Add one epoch/idempotence guard |

These are a repair algebra, not an answer table. A family becomes admissible
only when the observations support its causal shape. Several can remain live at
once.

Every `RulePatch` carries:

- `target_uid`: immutable executable-rule identity;
- `expected_revision` and `expected_content_hash`: compare-and-swap
  preconditions;
- `field`: `where` or `effect`;
- `proposed_clause`;
- optional provisional `inverse_clause` (Rust replaces it with the
  authoritative previous clause on commit);
- `mdl_cost` and `blast_radius`;
- `status` written authoritatively by the Rust transaction boundary.

Name-addressed mutation is intentionally absent from this protocol.

## Proof burden

Each patch receives six graph `ProofObligation` nodes:

1. causal gain;
2. preservation of protected invariants;
3. superiority to a literal no-op;
4. superiority to a same-sized placebo edit;
5. resource-budget compliance;
6. replication.

The trial gate is conjunctive. A strong aggregate score cannot compensate for
one protected regression. MDL is used only after the proof gate: among proven
patches, the graph selects the smallest description. If no patch survives and
the mechanical experiment runner closes its `EvidenceBatch`, the graph emits
an honest `Abort`; it never installs the least-bad failure.

Rejected trials remain graph evidence. This is important negative memory: a
later repair process can distinguish “not yet tried” from “falsified by the
no-op/placebo controls”.

## Rust transaction handshake

After a selected patch passes its canary, the rule mints
`Commit{status:"ready"}` and fires:

```json
["apply_rule_patch", "patch"]
```

The Rust engine owns staging and atomicity. It validates target identity,
revision, content hash, clause shape, and the target's mutation policy. The
graph proof gate validates behavioural invariants. It then writes onto the
same `RulePatch`:

- `status = "committed" | "refused"`;
- a stable `reason`;
- `result_revision`;
- `result_content_hash`;
- authoritative previous revision/hash and `inverse_clause` after success.

A refused transaction becomes an `Abort` node. It is not retried unchanged.
The graph only creates `Consolidation{status:"retained"}` after independent
post-commit evidence reports restart survival, cross-context survival, retained
gain and zero protected regressions. Failure at that point creates an abort
with `rollback_required=1`; the same Rust transaction boundary must enact the
stored inverse.

Seed-installed rules are mutation-protected by default. A seed must explicitly
name a rule in `self_modification_patchable_rules` to expose it to this
transaction surface; the live discriminator repair is one such declared
experiment. Rules authored by the running graph are patchable by default. A
copied prior therefore becomes a new revisable successor without making the
boot prior itself writable, and checkpoint import preserves the protection
bit.

## Blinded benchmark

`tests/fixtures/self_change_blind_faults.json` contains seven cases. Runtime
input contains observations and arm measurements but no expected family,
correct patch, or answer key. The held graph must diagnose:

- a threshold false-negative;
- a missing context guard;
- a missing relation;
- a wrong effect;
- repeated no-op firing;
- an ambiguous case where two patches work and MDL chooses the smaller;
- a correlation-only case where neither candidate beats both controls.

The test owns the hidden scoring key; it is not ingested into the substrate.
The final case is the important negative control: “found a plausible patch” is
not enough to produce a change.

## Extension points

New candidate families should be added only when a blinded fault cannot be
expressed by the existing algebra. Each new family must declare a local edit,
an inverse, its expected evidence signature and its MDL/blast-radius cost. Do
not add a family named after one benchmark case.

Future diagnosis should replace manually surfaced counterfactual measurements
with graph-visible rule traces and causal dependency cones. That changes the
source of `FaultProbe` measurements, not the proof protocol.
