# Contempt — PREREG

**Task**: Phase G (final phase) of the expanded emotional+preference
system build plan
(`/home/matt/.claude/plans/distributed-frolicking-waterfall.md`) — a
third `consequence_route` alongside `hate_attribution.py`'s existing
`"removal"`/`"pity"`, reusing the SAME crystallization ladder end to end.

## 1. Theoretical grounding

- **Rozin, Lowery & Haidt (1999), "The CAD Triad Hypothesis: A Mapping
  Between Three Moral Emotions and Three Moral Codes," *Journal of
  Personality and Social Psychology*** — three distinct moral-violation
  types map to three distinct moral emotions: Autonomy violations
  (direct harm/wronging of a person) → Anger (this arc's existing
  `removal_desire_for`, Fischer et al. 2018's elimination motive);
  Community violations (violating social role/status/group norms
  WITHOUT necessarily directly harming anyone) → Contempt; Divinity
  violations (purity/sanctity) → Disgust (out of scope). This rung adds
  the SECOND leg — Contempt for Community violations.
- **Contempt's own, distinct motivational profile** (Rozin, Lowery &
  Haidt's own emotion-mapping data, and the broader contempt literature
  they cite): contempt motivates SOCIAL DEVALUATION/EXCLUSION — treating
  the target as beneath consideration, disregarding their standing —
  distinct from hate's active ELIMINATION goal (Fischer et al. 2018,
  already cited). Contempt is also characterized as a "COLDER," less
  physiologically arousing emotion than anger/hate — a detached
  dismissal rather than a hot reactive state.

## 2. Design

**One new caller-supplied datum, not a new decision**: `record_hate_
incident` gains `violation_type: str = "harm"` — `"harm"` (autonomy
violation, the existing default, byte-compatible with every prior
caller) or `"norm"` (community violation). Stored on `IncidentReport`
and copied mechanically onto `TargetPattern.violation_type` by `derive_
hate_attribution`'s own existing effects (a literal passthrough, no
computed decision).

**`crystallize_hate`'s `consequence_route` Term gains a second
branching level**, WITHIN the controllable case only (uncontrollable
still routes to pity regardless of violation type — Weiner's own
controllability gate is orthogonal to the CAD triad's own violation-type
axis):

```
consequence_route = IfThenElse(controllable,
    IfThenElse(violation_type == "norm", Lit("devaluation"), Lit("removal")),
    Lit("pity"))
```

`devaluation_for:<target>` is a new target-scoped Concept (`mint_target_
concept`, same shape as every other consequence Concept). Its evidence
is UNAMPLIFIED by arousal or resentment_debt — flat `base_alpha`, the
SAME choice `pity_for` already made — reflecting contempt's own
documented "colder" character (deliberate, not an oversight: Fischer et
al.'s passion-amplification citation is specifically about hate's hot
elimination drive, which contempt's own literature explicitly contrasts
against).

## 3. Predictions

1. **Backward compatibility**: every EXISTING caller (no `violation_
   type` argument) still routes a controllable negative pattern to
   `"removal"` exactly as before — the default `"harm"` reproduces
   `v1.7.0`'s behavior byte-for-byte.
2. **A controllable, norm-violation pattern routes to `"devaluation"`**,
   not `"removal"` — `removal_desire_for` receives ZERO evidence;
   `devaluation_for` receives it instead.
3. **Controllability still gates independently of violation type** — an
   UNCONTROLLABLE norm-violation pattern still routes to `"pity"`, not
   `"devaluation"` — the two axes (controllability, violation type)
   compose, neither overrides the other.
4. **`devaluation_for`'s alpha is unamplified** — arousal and
   resentment_debt built up identically to a matched `"removal"` scenario
   produce a HIGHER `effective_removal_alpha` than `devaluation_for`'s
   own flat `base_alpha`, confirming the "colder" design choice is real,
   not just asserted.
5. **Per-target isolation** holds for `violation_type` and `devaluation_
   for` exactly as for every other target-scoped mechanism in this arc.

## 4. Scope boundaries

- Does not build Disgust (the CAD triad's third leg, Divinity
  violations) — a real, separate, un-built emotion; this rung completes
  two of three legs, not all three.
- `violation_type` is read from the CRYSTALLIZING incident only (the
  same snapshot-at-crystallization convention `consequence_route`'s own
  controllability read already uses), not aggregated across the whole
  confirming pattern — a documented simplification, same class as every
  other "read at crystallization time" design in this arc.
- Does not model any behavioral enactment of devaluation (actual social
  exclusion) — scoped to the motivational Concept existing, matching
  every other consequence-Concept-not-enacted-behavior convention here.
