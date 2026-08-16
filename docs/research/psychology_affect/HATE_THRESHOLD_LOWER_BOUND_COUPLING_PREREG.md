# Hate threshold lower-bound × arousal coupling — PREREG

**Task**: user, immediately after `HATE_STABILITY_AROUSAL_COUPLING_
RESULTS.md` landed: *"couple HATE_STABILITY_THRESHOLD lower bound to
arousal too."* That rung's own Sec4 scope boundary explicitly named and
deferred exactly this: *"Making the threshold itself arousal-dependent
(e.g. a lower bar when aroused) is a DIFFERENT, not-yet-named design and
is not what this rung builds."* This document registers that different
design — a second, distinct channel by which passion accelerates hate
crystallization, alongside (not replacing) the already-landed
per-incident streak-increment coupling.

## 1. Theoretical grounding

- **Slovic, Finucane, Peters & MacGregor (2007)'s affect heuristic**,
  already this arc's grounding for the increment coupling, makes a
  SECOND, independent claim beyond "an aroused incident feels like more
  evidence": strong affect also LOWERS the amount of evidence a judgment
  requires before it is treated as settled — affect substitutes for
  deliberation, so a highly aroused appraiser needs less accumulated
  confirmation before committing to a global attribution, not just more
  weight per confirmation.
- **This is a genuinely different mechanism from the already-landed
  increment coupling**, not a restatement of it: the increment coupling
  changes how fast `confirm_streak` climbs; this rung changes how far it
  has to climb. Both are real, separately motivated readings of the SAME
  affect-heuristic citation, and this document registers them as
  independent, additive channels — not a single idea built twice.

## 2. Design

**The base threshold constant (`HATE_STABILITY_THRESHOLD=3`) is
unchanged** — it is now the value read at ZERO arousal. The EFFECTIVE
threshold used by `crystallize_hate`'s gate is:

```
effective_threshold = HATE_STABILITY_THRESHOLD / (1 + TargetArousal.level)   [READ, same point in the fixpoint the increment coupling already reads at -- current, pre-this-incident arousal]
crystallize iff confirm_streak >= effective_threshold AND not already crystallized
```

At `level==0` this is exactly `HATE_STABILITY_THRESHOLD`, unchanged —
the same backward-compatibility property the increment coupling's own
`1+level` formula has. **No new floor constant is introduced**:
`shared_arousal`'s own dynamics (`level <- level*decay + intensity`,
`decay=0.7 < 1`) already converge to a fixed point
(`intensity/(1-decay) = 0.8/0.3 ≈ 2.667` under sustained maximum-intensity
incidents, `SHARED_AROUSAL_EXCITATION_TRANSFER_RESULTS.md`'s own
self-bounding design), so `effective_threshold` naturally floors around
`3/3.667 ≈ 0.818` under the most extreme sustained arousal this
substrate can produce — never collapsing to zero or negative, with no
hand-picked floor needed. This reuses the ALREADY-established bounded-
dynamics property rather than adding a new one.

Computed inside the EXISTING `crystallize_hate` Rule (one more
`Attr(Neighbours(pat,"tracks_arousal"),"level")` read, mirroring
`derive_hate_attribution`'s own arousal read exactly) — zero new Rust,
zero new Python decisions, zero new constants.

## 3. Predictions

1. **At zero arousal, `effective_threshold` equals the base constant** —
   a cold-start crystallization behaves identically to the pre-this-rung
   mechanism (backward compatibility).
2. **Elevated arousal lowers `effective_threshold` below the base
   constant** — the SAME `confirm_streak` value that would not yet
   crystallize at zero arousal DOES crystallize once arousal has built
   up, even holding the streak's own growth-rate coupling fixed.
3. **Compounding, measured honestly**: a run with BOTH couplings active
   (the pre-existing increment coupling AND this rung's threshold-lowering
   coupling) crystallizes in FEWER incidents than a run with the
   increment coupling alone — the two channels are additive, not
   redundant, and this rung reports the compounded effect size directly
   rather than assuming it from the individual mechanisms.
4. **Per-target isolation holds** — target A's arousal-lowered threshold
   does not affect target B's own `effective_threshold`.

## 4. Scope boundaries

- Does not change `HATE_STABILITY_THRESHOLD`'s role as the AT-REST
  (zero-arousal) constant — this rung's own name is precise: it couples
  the threshold's *effective, arousal-adjusted* value, not the registered
  base number, which stays the single documented, un-fitted constant this
  arc has always used.
- Does not add any new arousal-decay or intensity constant — reuses
  `AROUSAL_INTENSITY=0.8`/`AROUSAL_DECAY=0.7` verbatim, and the
  self-bounding fixed-point property is READ from, not re-derived.
- Does not touch `specific_act`'s reset behavior or the increment
  coupling's own formula — purely additive, both prior mechanisms stay
  byte-unchanged.
