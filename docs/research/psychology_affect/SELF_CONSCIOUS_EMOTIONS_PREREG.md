# Self-conscious emotions — PREREG

**Task**: user asked "is the CAN/PSI model sufficient to produce embarrassment
and otherwise, or do we need another system or different wiring... this
builds a functionally complete human simulacra." A prior research pass
(this session) established the answer: **not sufficient as-is**. Three
representational primitives are missing or misdirected:

1. A **reflexive second-order belief** — what a WITNESS believes about the
   appraised agent, structurally distinct from ground truth
   (`domains/character_tom.py`'s `belief_world` edge already has the right
   SHAPE — a nested SmEntity holding belief content, kept structurally
   separate from the real-world entity of the same name — but it is wired
   to NLP text comprehension, not a live social encounter, and its content
   is never reflexively about the appraising agent itself).
2. A **violable `Standard`** — genuinely absent anywhere in either repo
   (checked: CAN's belief network, `bigville_drama_social.json`,
   `world_frames`/laws/policies/charters — none represent a norm with a
   pass/fail evaluation, only belief strength and face-management behavior).
3. An **attribution-locus classification** to discriminate shame from guilt
   from embarrassment from pride.

This document registers the mechanism that supplies all three, before
building it.

## 1. Theoretical grounding (Lewis; Tracy & Robins; Tangney et al.)

- **Lewis (1971, *Shame and Guilt in Neurosis*)**: self-conscious emotions
  require a self-evaluation against an internalized standard, and the
  DISCRIMINATING variable between shame and guilt is the **attribution
  locus** — shame attributes the failure to the GLOBAL SELF ("I am bad"),
  guilt attributes it to a SPECIFIC ACT ("I did a bad thing"). Both can
  occur privately; neither strictly requires an audience.
- **Tracy & Robins (2004, "Putting the Self Into Self-Conscious Emotions")**:
  formalizes the appraisal sequence — self-relevance, standard comparison,
  internal (self) vs external attribution, then stable (global) vs unstable
  (specific) attribution — as the generative structure for the whole family,
  not a fixed list of named emotions.
- **Tracy & Robins (2007, "The Psychological Structure of Pride")**: pride
  bifurcates the SAME way shame/guilt do — **hubristic pride** (global-self
  attribution: "I am great") vs **authentic pride** (specific-act
  attribution: "I worked hard and did well") — the positive-valence mirror
  of the shame/guilt split, not a separate mechanism.
- **Miller (1996, *Embarrassment: Poise and Peril in Everyday Life*)**:
  embarrassment is characteristically attributed to CIRCUMSTANCE or
  involuntary exposure rather than a moral standard violation (tripping in
  public vs lying) — a THIRD attribution locus, not a milder shame.
- **Tangney, Miller, Flicker & Barlow (1996, "Are Shame, Guilt, and
  Embarrassment Distinct Emotions?")**: the load-bearing empirical citation
  for this design's exposure-gating — embarrassment is reliably
  audience-DEPENDENT in a way shame and guilt are not; shame/guilt occur at
  comparable intensity whether public or private.

## 2. Design

**Reused, not reinvented**: the `SmEntity -belief_world-> nested SmEntity`
SHAPE from `character_tom.py` (a witness's belief about the agent is a
node structurally distinct from ground truth — the SAME "false belief and
real world coexist as two distinct graph nodes" property, `character_tom.py`
:43-45), applied to a NEW, live-encounter trigger (mechanical world-adapter
minting, not NLP parsing) and NEW, reflexively self-directed content (a
witness's judgment of the APPRAISING agent, not a narrative third party).

**New primitives, genuinely absent before this rung:**
- `Standard{name}` — a violable norm.
- `SelfConsciousContext{standard_met, attribution_locus}` — the episode: did
  the agent (by its OWN knowledge) meet the standard, and what is the
  attribution locus (`global_self` | `specific_act` | `circumstance`,
  Sec1's three-way split, held as data, not inferred by this rung — a
  caller/adapter decides it from context, exactly as `band_code` was
  bigville's own pre-existing classification for the register/dispute
  rungs).
- `WitnessBelief{judgment}` (0+ per episode, `ctx -has_witness_belief->
  witness`) — a witness's OWN judgment (`"violated"` | `"met"`), independent
  of `standard_met`. This is the genuine second-order piece: a witness can
  hold a belief that DIFFERS from ground truth (mistakenly believing a met
  standard was violated, or vice versa) — the appraisal reads what
  witnesses BELIEVE, not raw fact, matching Tracy & Robins' appraisal model
  being about PERCEIVED social evaluation.

**Classification** (`sc_decide_emotion` rule, categorical — implemented as a
nested `IfThenElse` chain over discrete equality checks, deliberately NOT
forced through the register/dispute rungs' Argmin-over-codebook shape:
`attribution_locus` is categorical, not a continuous scalar to nearest-point
classify, so `IfThenElse` is the correct existing primitive here, not a
misapplication of "SHAPES NOT NUMBERS" — the rule is: pick the shape that
fits the data, and a lookup table over 3×2(+gate) discrete cells is a lookup
table, not a quantization problem):

```
perceived_violation = Exists(witnesses, judgment == "violated")

attribution_locus == "circumstance":
    perceived_violation  -> embarrassment
    else                 -> none
attribution_locus == "global_self":
    standard_met          -> hubristic_pride
    else                  -> shame
attribution_locus == "specific_act":
    standard_met          -> authentic_pride
    else                  -> guilt
```

`standard_met` (the agent's own ground truth) drives the shame/guilt/pride
axis regardless of exposure (Tangney et al. 1996: shame/guilt are NOT
reliably audience-dependent). `perceived_violation` (derived from WITNESS
BELIEF, which may diverge from `standard_met`) drives embarrassment
specifically, and ONLY for the circumstance-attributed cell (Miller 1996) —
this is the one cell in the table gated on exposure, matching the one
emotion the literature says is exposure-dependent.

## 3. Predictions (registered before building)

1. **Private shame**: `standard_met=0`, `attribution_locus=global_self`,
   zero witnesses → `shame` (audience-independent, per Tangney et al.).
2. **Private guilt**: `standard_met=0`, `attribution_locus=specific_act`,
   zero witnesses → `guilt`.
3. **Hubristic vs authentic pride**: `standard_met=1`, holding everything
   else fixed, `attribution_locus=global_self` → `hubristic_pride`;
   `attribution_locus=specific_act` → `authentic_pride`. Same standard met,
   different attribution, different emotion — the discriminating variable
   is attribution, not outcome.
4. **Embarrassment requires exposure**: `standard_met=0`,
   `attribution_locus=circumstance`, zero witnesses → `none`; the SAME
   episode with one witness whose `judgment="violated"` → `embarrassment`.
5. **Embarrassment from a witness's MISTAKEN belief**: `standard_met=1`
   (the agent actually complied) but a witness's `judgment="violated"`
   (they got it wrong) → `embarrassment` fires anyway — the appraisal reads
   PERCEIVED, not actual, violation for this cell. This is the direct test
   of the second-order-belief primitive: ground truth and the outcome
   diverge.
6. **Shame/guilt are exposure-INDEPENDENT**: `standard_met=0`,
   `attribution_locus=global_self`, holding this fixed, adding witnesses
   (any `judgment`) does NOT change the outcome away from `shame` — the
   direct, falsifiable encoding of Tangney et al.'s finding that this
   design deliberately does NOT gate shame/guilt on exposure.

## 4. Scope boundaries

- Does NOT build a live NLP-driven trigger (no "the agent reads a sentence
  and infers it was embarrassed") — `SelfConsciousContext`/`WitnessBelief`
  are minted mechanically by a harness/adapter, exactly like
  `DisputeContext`/`RegisterProfile` before them. Wiring a live trigger
  (e.g., off `cognitive_rule_frames`'s rule-violation detection, or a
  witnessed dispute's own `RuleDisputeSignal` outcome) is named, not built.
- Does NOT model INTENSITY (how STRONG the emotion is) — only which
  discrete emotion fires. Mood/arousal integration (this session's own
  `psychology_affect` line — modulators, window-of-tolerance) is a real,
  separate, named follow-on, not attempted here.
- Does NOT model third-party attribution of WHO decides `attribution_locus`
  — it is supplied as data (mirroring `band_code` in the register/dispute
  rungs), not inferred by a rule. A rule that infers attribution locus from
  richer context (was this a one-off accident vs a pattern of behavior) is
  a real, separate, named follow-on.
- Does NOT model jealousy/envy — genuinely different structure (social
  comparison to ANOTHER's standing on a shared resource/relationship, not
  self-evaluation against an internalized standard) — explicitly out of
  scope, not an oversight.
- Reuses `character_tom.py`'s `belief_world` SHAPE by citation and design
  precedent, not by importing/calling that module — its NLP pipeline
  (attitude-verb scanning, ShapeDecode construction matching) is the wrong
  tool for a live, mechanically-triggered episode, exactly as Sec2 states.
