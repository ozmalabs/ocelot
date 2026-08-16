# Rule dispute escalation — PREREG

**Task**: user asked for a testable scenario where two Bigville board-game
residents (Monopoly) disagree about a rule, and the disagreement either
defuses or escalates into an argument depending on (a) the nature of the
issue, (b) the two people, (c) who else is in the room. This document scopes
and pre-registers that mechanism before building it.

## 1. What already exists (confirmed by direct read, not assumed)

- `domains/cognitive_rule_frames.py::read_rule_document` gives each resident
  a private, deterministic `HeldRule` per rulebook sentence, keyed by
  `rule_key = f"{source_key}:{order}"` where `source_key = hash(name, kind,
  version, text)` — two residents reading the byte-identical rulebook text
  get MATCHING `rule_key`s, but there is no comparison mechanism anywhere in
  the file (`__all__` has no dispute/diff function). Confirmed: the NLP
  reading pipeline (`instruction_comprehension`/`reading_collapse`) is
  deterministic, so two residents independently reading the SAME clause will
  never naturally disagree — a genuine dispute needs an asymmetric-
  information source, not a parser artifact.
- The rulebook fixture itself (`scenarios/monopoly_rulebook.txt:151`) already
  states the real-world classic case: *"Free Parking has no reward and no
  penalty: it is a resting space only."* — the single most common house-rule
  myth in actual Monopoly play (many groups pay accumulated fines to whoever
  lands there). Line 235 explicitly separates ground-truth rules from
  proposed house rules requiring group agreement: *"A player may propose a
  house rule ... but it is not part of this rulebook unless everyone
  agrees."* This is a ready-made, real, unforced dispute case — not invented
  for this rung.
- `worlds/bigville_bond_world.py::_band_code` (reused verbatim by
  `bigville/bigville/game.py::_relationship_signal`, this session's own
  prior rung) already gives a discrete 0–5 (+/-1 rival) relationship band —
  "the people" signal.
- `seeds/bigville_loud_comm.json` (`lo_choose_loudness`/`lo_deliver_content`/
  `lo_observe_act`) already gates who hears a spoken act by distance/
  loudness — "who else is in the room" is a solved primitive at the world
  level; this rung only needs a COUNT of witnesses, not a new hearing model.
- `seeds/can_register_quantization.json`'s `can_register_decode_band`
  (this session's own prior rung) already established the exact SHAPE this
  rung reuses: compose a scalar from held traits, then `Argmin`-classify
  against a small fixed anchor codebook. That is reused here, not
  reinvented — same Term vocabulary (`Times`/`Plus`/`Minus`/`IfThenElse`/
  `Argmin`/`Abs`), zero new Rust.

**Genuinely missing** (confirmed by the research fork): a mechanism that
takes {issue severity, dyad closeness, witness count} and decides
defuse-vs-escalate. Nothing in either repo does this today.

## 2. Design

**Dispute source**: NOT two independent readings of the same text (proven
deterministic, §1). A dispute is one resident's `HeldRule` (ground truth,
from `read_rule_document`) contradicted by another resident's ASSERTED CLAIM
about the same topic (a remembered house-rule myth, e.g. "Free Parking pays
the pot") — the realistic shape of an actual tabletop rules argument.

**Composition** (`RuleDisputeSignal` node, one per encounter):
- `issue_severity` ∈ [0,1]: how starkly the claim contradicts the document
  (the contradicting `HeldRule.confidence` — already computed by the reader,
  §1, not invented for this rung; a low-confidence/ambiguous rule reading
  produces a low-severity, easily-shrugged-off dispute; a confidently-read,
  flatly-contradicted rule produces a high-severity one).
- `closeness` = `tie_strength` from the already-built `band_code`/
  `tie_strength` plumbing (bigville commit `1b79a0f`), clipped to [0,1] via
  `band_code/5.0` for a documented, un-fitted normalization (same honesty
  class as `resolution_bins=6` default in the register rung).
- `witnesses` = count of OTHER residents present (table size − 2), a bare
  integer from the scenario's own actor list — no new sensing model.

**Pressure formula** (documented, un-fitted, DEMO input — same honesty class
as `k=3.0` in CAT, `res_gain=1.0` in CAN):

```
pressure = issue_severity + audience_gain*witnesses*(1 - closeness) - closeness
```

The `(1 - closeness)` interaction term is the load-bearing design choice,
grounded in two real, independently-converging literatures rather than
picked to fit an outcome:
- **Felson (1982), "Impression Management and the Escalation of Aggression
  and Violence"** (Social Psychology Quarterly): audience presence reliably
  INCREASES escalation when face/status is at stake — bystanders more often
  amplify than dampen a conflict in naturalistic observation, because
  backing down in front of others costs face.
- **Coleman, Deutsch & Marcus, Handbook of Conflict Resolution**: established
  close relationships carry cooperative norms that actively resist
  destructive escalation regardless of audience — closeness doesn't just
  add a separate calming term, it SUPPRESSES the audience-amplification
  specifically (friends de-escalate for each other even when watched;
  strangers/rivals do not have that norm to fall back on).
  This is the SAME interaction-effect shape Giles' Communication
  Accommodation Theory already gave this session (convergence for in-group,
  divergence for out-group) — reused, not a new principle.

**Classification**: `Argmin` over a 2-entry `DisputeOutcomeAnchor` codebook
(`defuse: -1.0`, `escalate: 1.0`), byte-identical shape to
`can_register_decode_band`'s `RegisterLabelAnchor` decode.

## 3. Predictions (registered before running)

1. **Manipulation check**: holding severity/witnesses fixed, `pressure`
   strictly decreases as `closeness` increases (both the direct `-closeness`
   term and the interaction term point the same way).
2. **Primary — defuses easily**: high closeness (close friends, `band_code`
   ≥ 4), low severity (ambiguous rule reading), few/no witnesses (private
   aside) → `escalate` never wins.
3. **Primary — escalates**: low closeness (`band_code` ≤ 1, near-strangers or
   rivals), high severity (confidently, flatly contradicted claim), several
   witnesses → `escalate` wins.
4. **Interaction (the load-bearing claim, §2)**: at FIXED high witness count,
   raising closeness from low to high flips the outcome from escalate to
   defuse — i.e. the same public dispute plays out differently depending on
   who is having it, not merely on how public it is.
5. **Structural**: `band_code == -1` (rival) never produces a smaller
   `pressure` than `band_code == 0` (stranger) — rivalry does not read as
   ordinary distance, it should never accidentally look SAFER than a
   stranger tie (a floor sanity check on the `/5.0` normalization, since -1
   is out of the 0–5 scale it was built for).

## 4. Scope boundaries

- Does NOT wire this live into `BigvilleGame`'s tick loop or the
  `BigvilleOcelotResident` per-resident graphs (that integration is
  separate, larger, and not what "test a scenario" asked for — mirrors
  exactly how `can_register_quantization_demo.py` stayed a standalone
  harness rather than a live `CognitionBackend`, this session's own already-
  accepted precedent).
- Does NOT model what happens to the game/relationship AFTER an escalation
  (no consequence mechanic) — this rung answers "does it escalate", not
  "then what."
- Does NOT model active third-party MEDIATION (a bystander choosing to
  intervene) — only passive-witness audience pressure (Felson's finding);
  Coleman & Deutsch's mediation literature is cited only for the closeness-
  suppression term, not built as its own mechanic.
- `band_code == -1` (rival) is included in this rung (unlike
  `CAN_REGISTER_QUANTIZATION`, which explicitly excluded it) because rivalry
  IS meaningful here (a rival's claim is more likely to be contested, not
  less) — scoped narrowly to the floor-sanity check in Prediction 5, not a
  full divergence mechanism.
