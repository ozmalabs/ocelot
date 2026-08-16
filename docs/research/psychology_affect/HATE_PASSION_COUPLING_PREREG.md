# Hate × passion coupling — PREREG

**Task**: user, immediately after `HATE_ATTRIBUTION_RESULTS.md` landed:
*"couple removal_desire alpha to shared_arousal's TargetArousal."* This is
the named-not-attempted follow-on from that rung's own scope boundary
(`HATE_ATTRIBUTION_PREREG.md` Sec4: *"Passion (Sternberg's second
component) is NOT re-derived here... coupling `HATE_STABILITY_THRESHOLD`
or `effective_alpha` to it... is a real, named follow-on"*) and from
`SHARED_AROUSAL_EXCITATION_TRANSFER_PREREG.md`'s own Sec4 (*"does NOT
build the full hate attribution mechanism"*). This rung is the join point
between the two already-landed mechanisms.

## 1. Theoretical grounding

- **Sternberg (2003)'s Duplex Theory of Hate** — passion is one of hate's
  three components alongside negation-of-intimacy and decision/commitment.
  A crystallizing incident reached amid HIGH arousal is, on the theory,
  a more forceful commitment than the identical incident reached cold —
  the SAME structural incident (confirm_streak crossing threshold) should
  not produce a fixed-magnitude motivational consequence regardless of
  how heated the run-up to it was.
- **Reuses, does not reinvent**: `shared_arousal.mint_target_arousal`
  (the SAME `TargetArousal{level}` node — this rung adds ONE new edge,
  `TargetPattern -tracks_arousal-> TargetArousal`, so a target's hate
  pattern and its shared arousal pool are the SAME pool
  `SHARED_AROUSAL_EXCITATION_TRANSFER_PREREG.md` already built for any
  OTHER co-target belief, e.g. `desire_for:<target>` — a hostile
  incident's own arousal contribution is available to amplify the SAME
  target's eventual hate crystallization, exactly the cross-belief
  transfer that PREREG registered generically), and the SAME
  `effective_alpha = base_alpha * (1 + level)` /
  `level <- level*decay + intensity` formula, `decay=0.7`, byte-identical
  constant, reused not re-derived.
- **Valence-blind intensity, per Schachter & Singer (1962)**: intensity is
  a FIXED constant per incident (`0.8`, the SAME value
  `shared_arousal_demo.py`'s own hostile-incident example already uses),
  not conditioned on the incident's sign — arousal magnitude and belief
  valence are deliberately independent quantities, per `SHARED_AROUSAL_
  EXCITATION_TRANSFER_PREREG.md`'s own design.

## 2. Design

`mint_target_pattern` now additionally mints (via the EXISTING
`shared_arousal.mint_target_arousal`) and tracks the target's
`TargetArousal` (`tracks_arousal` edge — one new Gamma production).

**Every incident** (regardless of locus) raises the shared arousal pool
by the fixed intensity, THEN decays it (read-before/update-after, the
same convention `shared_arousal.record_targeted_incident` already
established):

```
arousal.level <- arousal.level*0.7 + 0.8    [AFTER this incident's own appraisal]
```

**Only the crystallizing incident's `removal_desire_for` evidence is
coupled** (Sternberg's passion component is specifically about the
COMMITMENT act, not every ordinary appraisal):

```
effective_removal_alpha = base_alpha * (1 + arousal.level)   [READ, BEFORE this incident's own update]
removal_desire_for <- concept_apply_evidence(evidence=+1.0, effective_removal_alpha)
```

Zero new Rust, zero new decisions in Python (the formula is arithmetic,
not a branch — same acceptable shape this arc's every prior coupling has
used); the ONLY new graph-structural addition is the `tracks_arousal`
production, admitting an edge type that did not exist between these two
node types before.

## 3. Predictions

1. **Coupled removal-desire evidence at crystallization is strictly
   greater than the uncoupled `base_alpha`** — back-to-back incidents
   build real arousal before the crystallizing incident even fires.
2. **The amplification matches the formula exactly**:
   `effective_removal_alpha == base_alpha * (1 + arousal_level_read_
   before_this_incident)`, not an approximation.
3. **"Hot" vs "cold" crystallization** — the IDENTICAL crystallizing
   incident (same confirm_streak, same threshold crossing) produces a
   MARKEDLY smaller `effective_removal_alpha` when arousal is allowed to
   decay to near-zero between incidents (simulating a long gap) than when
   incidents fire back-to-back — the SAME structural event, a different
   motivational strength, purely from timing.
4. **Per-target isolation holds** — target A's arousal build-up does not
   change target B's `effective_removal_alpha` at B's own crystallization.

## 4. Scope boundaries

- Does not couple `HATE_STABILITY_THRESHOLD` itself to arousal (a second,
  independently named follow-on in `HATE_ATTRIBUTION_PREREG.md` — e.g. "a
  sufficiently aroused incident could count double toward the streak") —
  out of scope for THIS rung, which is titled and scoped to `removal_
  desire`'s `alpha` specifically, per the user's own instruction.
- `intensity=0.8` and `decay=0.7` are the SAME documented, un-fitted
  constants `shared_arousal`'s own PREREG already registered and
  RESULTS already confirmed — not re-validated here, reused verbatim.
- Ordinary (non-crystallizing) `global_other`/`specific_act` incidents
  still contribute to the arousal pool (so a run-up genuinely builds
  passion) but their OWN evidence application (`regard_for`) stays
  UNCOUPLED — only the removal-desire consequence, gated to the single
  crystallizing incident, is coupled, per the user's literal instruction.
