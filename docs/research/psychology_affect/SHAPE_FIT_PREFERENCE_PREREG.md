# Shape-fit preference — PREREG

**Task**: Phase B of the expanded emotional+preference system build plan
(`/home/matt/.claude/plans/distributed-frolicking-waterfall.md`). The
user's own framing: *"an agent likes things by shape."* This registers a
preference primitive that is a direct READ-OFF of the sd loop's own
decode fluency — not a third scalar Concept updated by ad hoc evidence,
qualitatively different from every valence Concept (`regard_for` etc.)
built earlier in this arc.

## 1. Theoretical grounding

- **Zajonc (1968, "Attitudinal Effects of Mere Exposure"; 1980, "Feeling
  and Thinking: Preferences Need No Inferences")** — affect can be a
  near-primitive computation, not downstream of full cognitive
  evaluation; preference tracks something more immediate than deliberate
  judgment.
- **Reber, Winkielman & Schwarz (2004), "Processing Fluency and
  Aesthetic Pleasure"** — things easier to process (better fit to a held
  representation, less residual) are liked more.
- **Winkielman, Halberstadt, Fazio & Catty (2006), "Prototypes Are
  Attractive Because They Are Easy on the Mind"** — prototypicality
  (closeness to a held category's central tendency) drives preference
  BECAUSE it is more fluently processed.
- **Berlyne (1971), *Aesthetics and Psychobiology*** — the piece that
  makes this NON-monotonic: preference is an INVERTED-U over
  novelty/complexity relative to what is already known (the Wundt
  curve). Perfect familiarity is boring; total novelty is unpleasant;
  MODERATE mismatch against a held schema is preferred. This is the
  registered, falsifiable claim — not "more fit = more liked."

## 2. Design

**Reuses 100% of already-verified infrastructure** (Phase 0 of the plan
confirmed both facts directly, not assumed): `ShapeDecode`'s
`covered_count`/`goal_relations`/`residual` are already surfaced as
plain `Value` dict fields — a one-line Python read, zero new plumbing;
`shared_arousal.mint_target_arousal`'s `target` param is generic
string-keyed bookkeeping, a clean reuse for a non-agent STIMULUS
identifier.

```
fluency = covered_count / goal_relations              # in [0, 1]
preference = 4 * fluency * (1 - fluency)               # inverted-U, peak 1.0 at fluency=0.5, 0 at both extremes
```

The `4x(1-x)` parabola is the simplest, standard inverted-U form peaking
at the midpoint with range `[0, 1]` — chosen for being the minimal
functional form matching Berlyne's QUALITATIVE claim (symmetric,
zero at both extremes, single interior peak), not independently fit to
data (documented, un-fitted, same honesty class as every other
functional-form choice in this arc).

**Novelty also feeds the SAME shared arousal pool** every other rung in
this arc already reads/writes (`AROUSAL_DECAY` reused verbatim, not
re-derived):

```
novelty_intensity = 1 - fluency
TargetArousal.level <- TargetArousal.level * AROUSAL_DECAY + novelty_intensity
```

This is registered as a SEPARATE, side observable this rung produces —
NOT folded multiplicatively into the preference formula itself. Berlyne's
own model is qualitative about how fluency and arousal-potential combine;
inventing a specific interaction weight without a citable functional
form would be exactly the kind of unfitted-constant-standing-in-for-a-
shape this arc's own CLAUDE.md section warns against. The two channels
are reported together, composed by nothing.

## 3. Predictions

1. **A goal EXACTLY matching a held prototype (`fluency=1.0`) scores
   `preference=0.0`** — the over-familiar/boring extreme, confirming
   this is NOT a monotonic "more fit = more liked" formula.
2. **A goal sharing NOTHING with any held prototype (`fluency=0.0`)
   ALSO scores `preference=0.0`** — the overwhelming/incoherent extreme.
3. **A goal partially matching (`fluency=0.5`) scores STRICTLY HIGHER**
   than both extremes — the actual interior peak.
4. **Symmetry**: a `fluency=0.3` goal and a `fluency=0.7` goal score
   IDENTICALLY — confirms the registered parabola shape precisely, not
   an ad hoc asymmetric curve.
5. **Novelty feeds arousal**: a highly novel stimulus (`fluency` near 0)
   raises `TargetArousal.level` more than a highly familiar one
   (`fluency` near 1), tracked as the documented side observable.

## 4. Scope boundaries

- This is a SEPARATE preference channel from `regard_for`'s accumulated-
  evidence valence (hate/pity/admiration's own family) — not a
  replacement. A named, deferred integration point: using this signal as
  a COLD-START prior for `regard_for` before enough incidents exist to
  drive it via evidence — not built here.
- The `4x(1-x)` functional form is a documented design choice matching
  Berlyne's qualitative shape, not independently validated against real
  preference-rating data.
- Fluency/arousal composition is NOT built as a single combined formula
  (Sec2) — a real, citable interaction term is a named follow-on, not
  fabricated here.
- Does not build a "codebook growth" mechanism (the sd loop's own
  `sd_mint_quantum` ladder already exists generically for that) — this
  rung reads an EXISTING held codebook, it does not decide when/how new
  prototypes get minted into it.
