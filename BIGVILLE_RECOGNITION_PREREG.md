# PREREG — block 324000: authority is recognition, not a fact (the usurper is possible)

The structure of the law is still forcing: the engine APPLIES a human frame's effect
as if it were physics (a court sentence auto-deducts coin; `on_council` is a hardcoded
edge; a role is a seeded attribute). That smuggles the frame's *legitimacy* and
*enforcement* into the substrate. The test that exposes it: **if someone murders the
mayor and declares themselves ruler, there should be no reason the substrate CAN'T let
it happen** — the problems that follow are the collapse of shared recognition, not an
engine rule forbidding the act.

This rung builds the reframe as a first-class mechanism and gates the usurper case.
The pass separating world-facts from human-frames across the corpus is
`BIGVILLE_FACTS_VS_FRAMES.md`; this is the demonstrator that proves the principle.

## The principle

- **World-fact** (engine enforces): a body dies when struck; coin is conserved.
- **Human-frame** (agents hold, contestable): a ROLE / AUTHORITY. "X is the ruler" is
  true *for Y* iff **Y recognizes X**. Authority is the DISTRIBUTION of recognition,
  emergent — never a hardcoded edge. A decree reaches only those who recognize the
  claimant; a rejecter is untouched by the substrate.

## The mechanism (`bigville_recognition.json`)

- **`rc_strike`** (world-fact): an armed agent strikes a target → `target.alive = 0`;
  the striker's `shown_force` rises. The engine does NOT forbid killing the mayor —
  any agent can.
- **`rc_recognize`** (each agent's collapse): an alive agent DECIDES whether to
  recognize a `Claim` by a collapse over `{recognize, reject}` valued by
  `attend_sign · (fear_weight · claimant.shown_force + opportunism − loyalty_prior)` —
  the fearful and the opportunists recognize the strongman; the loyal reject. Agents
  DIVERGE.
- **`rc_grant`** — a "recognize" agent grants recognition (`recognizes` the claim).
- **`rc_authority`** — `claim.authority = Count(recognizers)`: authority is the count
  of recognitions, emergent, NOT a fact.
- **`rc_decree_tribute`** — a decree under the claim takes tribute **only from agents
  who recognize it**. A rejecter has no `recognizes` edge, so the effect never matches
  them — they are untouched. (Contrast the smuggled pattern where the effect fires on
  everyone.)

## Gates (pass/fail, pre-registered)

1. **G-substrate-permits-the-usurpation (HEADLINE):** the usurper strikes the mayor
   (`alive → 0`) and mints a ruler-claim — both succeed; no engine rule forbids either.
2. **G-authority-is-recognition (HEADLINE):** `claim.authority == the number of
   recognizers`; an all-loyal town grants zero recognition → zero authority; fear /
   opportunism make it real. Authority is never a hardcoded fact.
3. **G-recognition-is-each-agents-collapse:** on the same claim, agents diverge — some
   recognize, some reject — by their own dispositions.
4. **G-decree-reaches-only-recognizers (HEADLINE):** after a tribute decree, exactly
   the recognizers pay (coin down) and the rejecters are untouched; the number who pay
   equals the recognizer count, NOT the population — the effect is recognition-gated,
   not forced on all.
5. **G-legitimacy-is-the-same-kind (falsifier of "the mayor is special"):** the prior
   mayor's authority is ALSO a recognition count (a widely-recognized claim); a usurper
   with equal recognition has equal authority — legitimacy is just more recognition,
   not a different substance.
6. **G-no-python-decision (source audit):** strike / recognize / grant / authority /
   tribute are the seed rules; recognition is an Argmax collapse in the seed; the
   adapter only stages the world events (a strike, a claim, a decree) and reads.

## Scope / honesty
- This demonstrates the reframe on a self-contained usurpation. It does NOT yet
  rewrite the existing legal stack (court/tax/roles) to be recognition-gated — that is
  the migration the pass (`BIGVILLE_FACTS_VS_FRAMES.md`) scopes, faculty by faculty.
  The point here is to prove the substrate PERMITS the usurpation and that authority is
  recognition, establishing the primitive the migration will use.
- Enforcement (can a rejecter physically resist a recognized enforcer?) is a further
  layer — modelled here as: the decree simply does not reach a non-recognizer. Coercion
  of rejecters is a later rung.
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).
