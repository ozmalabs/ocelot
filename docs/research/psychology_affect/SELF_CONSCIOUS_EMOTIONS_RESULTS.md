# Self-conscious emotions — RESULTS

Registered design: `SELF_CONSCIOUS_EMOTIONS_PREREG.md`. Built:
`seeds/self_conscious_emotions.json` (via
`scripts/_build_self_conscious_emotions_seed.py`), demonstrated by
`scripts/self_conscious_emotions_demo.py`, regressed by
`tests/test_self_conscious_emotions.py` (11/11 green).

## 1. What this answers

User: *"is the CAN/PSI model sufficient to produce embarrassment and
otherwise, or do we need another system or different wiring... this builds
a functionally complete human simulacra at this level."* This session's own
research pass (fork report, prior turn) found the honest answer was
**no** — three primitives were missing: a reflexive second-order belief, a
violable `Standard`, and an attribution-locus classification. This rung
builds all three and demonstrates the full pride/shame/guilt/embarrassment
family from them.

## 2. What this is

`sc_decide_emotion` classifies a `SelfConsciousContext{standard_met,
attribution_locus}` plus 0+ `WitnessBelief{judgment}` children into
`{hubristic_pride, authentic_pride, shame, guilt, embarrassment, none}` via
a nested `IfThenElse` lookup — deliberately NOT the register/dispute rungs'
Argmin-over-codebook shape, because `attribution_locus` is categorical
(Lewis 1971's three-way split: global-self / specific-act / circumstance),
not a continuous scalar to nearest-point classify. Zero new Rust.

The genuine second-order-belief primitive: `WitnessBelief.judgment` is a
witness's OWN belief, independent of `standard_met` (ground truth) — reused
from `domains/character_tom.py`'s `SmEntity -belief_world-> nested SmEntity`
SHAPE (a belief and the real world coexist as structurally distinct nodes),
applied to a live, mechanically-triggered episode instead of NLP text.

## 3. Predictions — all 6 registered, all 6 held

```
PRIVATE SHAME / GUILT
broke a promise, blames own character, alone            -> shame
broke a promise, blames the one lapse, alone            -> guilt

HUBRISTIC VS AUTHENTIC PRIDE
won the game, 'I am just better than everyone'          -> hubristic_pride
won the game, 'I studied the odds hard this time'       -> authentic_pride

EMBARRASSMENT REQUIRES EXPOSURE
tripped over the rug, nobody around                     -> none
tripped over the rug, one person saw                    -> embarrassment

EMBARRASSMENT FROM A WITNESS'S MISTAKEN BELIEF
actually complied, but a witness THINKS you didn't      -> embarrassment
(standard_met=True -- ground truth is fine)

SHAME/GUILT ARE EXPOSURE-INDEPENDENT
private failure, global attribution, alone              -> shame
same failure, global attribution, 3 witnesses           -> shame
unchanged by exposure: True
```

1. **Private shame** (Lewis 1971) — `PASS`.
2. **Private guilt**, same violation, different attribution — `PASS`. Same
   standard, different emotion, purely from attribution locus: the
   discriminating claim, not incidental.
3. **Pride bifurcation** (Tracy & Robins 2007) — `PASS`. The positive-valence
   mirror of predictions 1-2, same mechanism, opposite standard-outcome.
4. **Embarrassment requires exposure** (Miller 1996; Tangney et al. 1996) —
   `PASS`. Zero witnesses on an otherwise-identical circumstance-attributed
   violation produces no emotion at all — not a weaker embarrassment, none.
5. **The load-bearing claim** — embarrassment fires from a witness's
   MISTAKEN belief even when the agent's own ground truth (`standard_met`)
   says nothing was wrong — `PASS`. This is the direct, falsifiable test
   that the mechanism reads PERCEIVED (believed) violation, not actual
   violation, which is the entire point of building a genuine second-order
   belief primitive instead of a `witnessed: bool` flag.
6. **Shame/guilt exposure-independence** — `PASS`, in both directions
   (a positive control for shame, a second one for guilt in the test file).
   This is a real, falsifiable, literature-grounded NEGATIVE claim
   (something the design deliberately does NOT do), not merely an absence
   of a positive result.

No null. Every registered prediction held on the first run.

## 4. Honesty notes — what this does and does not establish

**Does establish**: the three primitives the prior research pass identified
as missing (reflexive second-order belief, violable Standard, attribution
locus) are sufficient, when composed, to reproduce the qualitative structure
of the pride/shame/guilt/embarrassment family exactly as the literature
describes it — including the one genuinely subtle, easy-to-get-wrong
empirical fact (Tangney et al. 1996's audience-dependence asymmetry) as a
predicted, not assumed, outcome.

**Does NOT establish**: that `attribution_locus` is correctly INFERRED from
context — it is supplied as data here (PREREG Sec4), exactly as `band_code`
was pre-existing bigville data for the register/dispute rungs. A rule that
decides "was this a one-off accident or a pattern" (which would set
`attribution_locus` itself, rather than receive it) is unbuilt. Anything
about emotional INTENSITY, or integration with this session's own
`psychology_affect` mood/arousal line (modulators, window-of-tolerance) —
this rung produces a discrete label, not a felt magnitude. Anything about
jealousy/envy (a structurally different social-comparison mechanism, PREREG
Sec4, out of scope by design). Anything about a LIVE trigger — no world
adapter wires a real encounter (e.g. a witnessed `RuleDisputeSignal`
outcome) into `SelfConsciousContext`/`WitnessBelief` yet; this stays a
standalone harness, matching the register/dispute rungs' own precedent
before any live integration.

**Does NOT claim felt qualia** — same posture as `core_emotions.json`'s own
explicit stance ("the FUNCTIONAL regulator, NOT a claim to felt qualia").
This rung reproduces the FUNCTIONAL/appraisal structure the literature
specifies, nothing about subjective experience.

## 5. Cross-repo follow-on work — named, not built

1. **Live trigger wiring** — the most natural first integration is
   `rule_dispute_escalation.json`'s own `RuleDisputeSignal` outcome: an
   `escalate` verdict is itself evidence a Standard ("know the rules
   correctly," "argue in good faith") was perceived as violated, which
   could mechanically mint a `SelfConsciousContext` for the disputant who
   was wrong, with `witnesses` carried over from the dispute's own bystander
   count. Not attempted here — a genuinely separate integration rung.
2. **Attribution-locus inference** — a rule (not raw data) that decides
   global-self vs specific-act vs circumstance from a resident's OWN
   held-history (e.g. `CAN`'s `self_worth`/pattern-of-behavior signal): a
   repeated failure trending toward `global_self`, a first-time one toward
   `specific_act` — this is exactly the kind of "quantity that changes"
   the sd-loop exists for, not built here.
3. **Emotional intensity + mood integration** — connecting the discrete
   emotion label to this session's `psychology_affect` line's arousal/mood
   machinery (a `shame` verdict raising `mood_bias` toward depression-shaped
   suppression, per `core_emotions.json`'s own documented mechanism) —
   named, not built.
4. **Rendering** — turning `emotion=embarrassment` into observable behavior
   (a flushed response, an apology, withdrawal) is downstream work, exactly
   as `register_label` stopped at a discrete LABEL in the prior rung.

## 6. Files

- `docs/research/psychology_affect/SELF_CONSCIOUS_EMOTIONS_PREREG.md`
- `docs/research/psychology_affect/SELF_CONSCIOUS_EMOTIONS_RESULTS.md` (this file)
- `scripts/_build_self_conscious_emotions_seed.py`
- `seeds/self_conscious_emotions.json`
- `scripts/self_conscious_emotions_demo.py`
- `tests/test_self_conscious_emotions.py` (11/11)
