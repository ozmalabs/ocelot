# Hate stability × arousal coupling — PREREG

**Task**: user, immediately after `HATE_PASSION_COUPLING_RESULTS.md`
landed: *"couple HATE_STABILITY_THRESHOLD to arousal too."* This is the
SECOND named-not-attempted follow-on from that rung's own honesty notes
(Sec3: *"coupling `HATE_STABILITY_THRESHOLD` to arousal (a separately
named, still-deferred follow-on — an aroused incident could plausibly
count more toward the streak itself, not attempted here)"*) — this
document registers exactly that design.

## 1. Theoretical grounding

- **Sternberg (2003)'s Duplex Theory of Hate** — the three components
  (negation of intimacy, passion, decision/commitment) are not merely
  co-occurring; the theory treats them as INTERACTING — high passion
  accelerates how quickly a pattern of negative incidents crystallizes
  into a stable commitment, not just how strongly the eventual commitment
  motivates action (already built, `HATE_PASSION_COUPLING_PREREG.md`).
- **Slovic, Finucane, Peters & MacGregor (2007), "The Affect Heuristic,"
  *European Journal of Operational Research*** — strong affect biases
  pattern/probability judgments: a more AROUSING confirming incident is
  read as MORE representative of a stable underlying trait than a mild
  one carrying the identical objective information. This grounds the
  coupling as a genuine (if imperfect) BIAS, consistent with hate's own
  essentialist-attribution character (`HATE_ATTRIBUTION_PREREG.md`'s own
  Fischer et al. 2018 citation) rather than a neutral, purely rational
  update rule.

## 2. Design

**The literal threshold constant (`HATE_STABILITY_THRESHOLD=3`) stays
fixed** — the SAME number of "confirmation units" is still required. What
changes is how many units ONE incident contributes: instead of always
`+1`, a confirming (`global_other`) incident's contribution to
`confirm_streak` is scaled by the SAME shared `TargetArousal.level` this
target's `tracks_arousal` edge already tracks (`HATE_PASSION_COUPLING_
PREREG.md`), read BEFORE this incident's own update — the identical
read-before/update-after convention every prior coupling in this arc has
used:

```
streak_increment = 1 + TargetArousal.level    [READ, before this incident's own update]
confirm_streak <- confirm_streak + streak_increment   if this incident's locus == global_other
confirm_streak <- 0                                    otherwise (unchanged -- an exception still fully resets it)
```

At `TargetArousal.level == 0` (a cold start, or the very first confirming
incident) this is exactly `+1`, byte-identical to the pre-existing
behavior — the coupling is a strict generalization, not a redefinition.
Computed entirely inside the SAME `derive_hate_attribution` Rule that
already reads `held_regard` via `tracks_concept` (`HATE_ATTRIBUTION_
PREREG.md` Sec2) — one more `Attr(PickUnique(Neighbours(pat,
"tracks_arousal")), "level")` read, zero new Rust, zero new Python
decisions (the formula is arithmetic inside a Term tree, evaluated by the
Rule, not a Python branch).

## 3. Predictions

1. **At zero arousal, the increment is unchanged (`+1`)** — a cold-start
   confirming incident crystallizes at exactly the same pace this arc's
   prior rungs already measured, a backward-compatibility control.
2. **The SAME sequence of confirming incidents crystallizes in FEWER
   incidents when arousal has built up** — a "hot" run of confirming
   incidents (arousal compounding between them) reaches
   `confirm_streak >= HATE_STABILITY_THRESHOLD` sooner than an
   arousal-decayed "cold" run of the identical incidents.
3. **The increment matches the formula exactly**:
   `streak_increment == 1 + arousal_level_read_before_this_incident`, not
   an approximation.
4. **Per-target isolation holds** — target A's arousal-accelerated streak
   growth does not change target B's own streak-increment size.

## 4. Scope boundaries

- The threshold CONSTANT itself (`3`) is not changed or made dynamic —
  only the per-incident contribution toward it. Making the threshold
  itself arousal-dependent (e.g. a lower bar when aroused) is a
  DIFFERENT, not-yet-named design and is not what this rung builds.
- `specific_act`'s full reset to `0` is UNCHANGED — an exception still
  breaks the pattern completely regardless of how aroused the exception
  itself was; this rung does not soften that reset.
- Reuses `AROUSAL_INTENSITY=0.8`/`AROUSAL_DECAY=0.7` verbatim (no new
  constants introduced by this rung at all — the only new element is the
  `1 + level` streak-increment formula itself, whose shape mirrors
  `effective_alpha`'s own `base_alpha * (1 + level)`, not a new
  independently-fitted number).
