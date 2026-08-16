# Persistent held_self_worth — PREREG

**Task**: user, immediately after the CAN self_worth wire-up: *"make it
properly persistent."* `HELD_SELF_WORTH_FROM_CAN_RESULTS.md` §3 named this
explicitly as unbuilt: the prior rung relaxed a STATIC personality prior
ONCE, fresh, per call — no resident's belief carried forward across
repeated incidents. This rung makes it a genuinely history-accumulating
belief: repeated self-conscious episodes shift a resident's `self_worth`
over time, and later appraisals read the UPDATED value.

## 1. A real engine gotcha, found live, before registering

`concept_apply_evidence` (`h_i ← h_i + alpha·evidence`, pre-existing PyO3
op, `runners/dsl/src/py.rs:2596`) mutates a Concept's `external_field`
OUTSIDE the rule-effect path. Probed directly: applying it and immediately
calling `run_rules()` reported `steps=0` and left `state` unchanged EVEN AT
`external_field=-5.0` (a massive, unambiguous push) — `run_rules()`'s
incremental dirty-tracking never re-examined the Concept, because nothing
marked it dirty outside the normal rule-effect write path. Confirmed the
mechanism itself was correct (forcing `state` to a different value via
`set_attr` before re-running correctly re-converged to `-1` in 3 steps) —
the fix is `inner.force_all_dirty()` (pre-existing engine API,
`dirty_marks`/`force_all_dirty`/`reset_dirty_marks` family) immediately
before the post-evidence `run_rules()` call. **Every evidence-then-relax
call in this rung's own code calls `force_all_dirty()` — this is not
optional, it is the fix for a real, reproducible silent no-op.**

## 2. Design

Two new capabilities in `domains/can_self_worth_bridge.py`:

- **`find_or_build_resident_can(inner, resident)`** — looks up an existing
  `Resident` node by `name` (walking `has_belief_mt`/`has_concept` to
  rebuild the `concepts` dict) before building a fresh one — the SAME
  resident, appraised twice on one substrate, reuses their one persistent
  CAN network rather than minting a duplicate with a reset belief.
- **`record_incident_outcome(inner, concepts, *, standard_met,
  attribution_locus, alpha=0.3, max_steps=3000)`** — feeds an
  ALREADY-DECIDED appraisal outcome back as evidence
  (`concept_apply_evidence(self_worth, ±1.0, alpha)`, mirroring
  `apply_scenario_evidence`'s own established mechanical-translation
  pattern — no NEW decision, `standard_met` was already decided by the
  dispute/self-conscious chain), `force_all_dirty()`, re-relaxes, and
  returns the updated `self_worth` state for the NEXT appraisal to read.

**Gated on `attribution_locus != "circumstance"`** — a genuine theoretical
claim, not an incidental scoping choice: an outcome attributed to
circumstance was, BY DEFINITION (Lewis 1971; Miller 1996), not attributed
to the self at all, so it should not move the self-concept. Only
`global_self`/`specific_act`-attributed episodes feed back. `alpha=0.3` is
a documented, un-fitted per-incident learning rate (same honesty class as
every other constant this arc has used).

## 3. Predictions

1. **`force_all_dirty()` is necessary** — without it, repeated evidence
   applications leave `state` unchanged regardless of magnitude (the found
   gotcha, encoded as a standing regression so a future refactor cannot
   silently drop the call).
2. **Repeated confirming incidents can flip a resident's `self_worth`
   basin.** A `Confident` resident (`prior_self_worth=0.9`, converges to
   `state=1`) subjected to enough repeated `standard_met=False` incidents
   (with `attribution_locus != circumstance`, so evidence actually applies)
   eventually converges to `state=-1` — a genuine identity shift from
   accumulated experience, not a single-incident overreaction (empirically:
   4-6 incidents at `alpha=0.3`, not 1).
3. **A `circumstance`-attributed incident does NOT move `self_worth`** —
   repeated circumstance-attributed episodes (no track record each time,
   or explicitly gated) leave the belief exactly where it was, confirming
   the theoretical gate is load-bearing, not decorative.
4. **The SAME resident, appraised twice with no intervening incident,
   reads the SAME persisted `self_worth`** — `find_or_build_resident_can`
   returns the EXISTING Concepts, not a freshly reset network.
5. **End to end**: a resident's drift over several dispute episodes changes
   which emotion they experience for an OTHERWISE IDENTICAL later dispute —
   the same claim/severity/exposure, but a different outcome because their
   own held pattern has shifted since the first one.

## 4. Scope boundaries

- `alpha=0.3` and the specific 4-6-incident flip threshold are measured,
  un-fitted facts about THIS resident's particular coupling structure
  (`identity_field=0.8`, one `+0.6`-weighted neighbour) — not a general
  claim about how many incidents it "should" take for any resident.
- Does not persist a resident's CAN network to disk / across process
  restarts — persistence here means "across multiple calls on the SAME
  live substrate," matching how the real agent's own substrate is meant to
  be long-running (CLAUDE.md), not a new serialization mechanism.
- Does not wire this into the dispute→self-conscious bridge's OWN rules
  (still an external Python loop calling appraise → record →
  re-appraise) — the bridge seed itself is unchanged.
