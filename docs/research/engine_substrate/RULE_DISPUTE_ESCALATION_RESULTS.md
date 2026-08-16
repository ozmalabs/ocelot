# Rule dispute escalation — RESULTS

Registered design: `RULE_DISPUTE_ESCALATION_PREREG.md`. Built:
`seeds/rule_dispute_escalation.json` (via
`scripts/_build_rule_dispute_escalation_seed.py`), demonstrated by
`scripts/rule_dispute_escalation_demo.py`, regressed by
`tests/test_rule_dispute_escalation.py` (9/9 green).

## 1. What this is

The `rd_decide_outcome` rule composes a scalar `pressure` from three inputs
on a `DisputeContext` node — `issue_severity`, `closeness` (`band_code/5.0`,
reusing bigville's `band_code`/`tie_strength` plumbing verbatim, commit
`1b79a0f`), and `witnesses` (bystander count) — then classifies it via
`Argmin` nearest-point decode against a 2-entry `DisputeOutcomeAnchor`
codebook (`defuse: -1.0`, `escalate: 1.0`). Same compose-then-Argmin-classify
shape as `can_register_decode_band` (`seeds/can_register_quantization.json`,
this session's prior rung), reused rather than reinvented. Zero new Rust.

## 2. The scenario the user asked for

`scenarios/monopoly_rulebook.txt:151` states the real rule: *"Free Parking
has no reward and no penalty: it is a resting space only."* Bob (a common
real-world house-rule myth) claims it pays out the collected fines. Whether
that dispute defuses or escalates is exactly what this mechanism decides,
using three concrete cases:

```
close friends, ambiguous issue, private aside            closeness=0.80 pressure=-0.600 -> defuse
near-strangers, confident contradiction, whole table watching  closeness=0.00 pressure=+1.350 -> escalate
```

Both directions are real, live outcomes of the same rule — not a fixed
verdict. The scenario the user described (defuses OR escalates, depending on
issue/people/bystanders) is reproduced end to end.

## 3. Predictions — all 5 registered, all 5 held

1. **Manipulation check** — pressure strictly decreases as closeness
   increases (severity=0.8, witnesses=3, band 0→5): `1.250 → 0.960 → 0.670 →
   0.380 → 0.090 → -0.200`, strictly monotonic. **PASS.**
2. **Defuses easily** — close friends (`band_code=4`), low severity (0.2),
   private (0 witnesses): `outcome=defuse`. **PASS.**
3. **Escalates** — near-strangers (`band_code=0`), high severity (0.9),
   several witnesses (3): `outcome=escalate`. **PASS.**
4. **Interaction (load-bearing)** — at FIXED high witness count (3) and high
   severity (0.8), raising closeness from `band_code=0` to `band_code=5`
   flips the outcome from `escalate` to `defuse`. From the sweep table, the
   flip happens between `band_code=4` (`pressure=+0.090`, escalate) and
   `band_code=5` (`pressure=-0.200`, defuse) — the same public dispute plays
   out differently depending on who is having it, exactly the claim
   `(1-closeness)` was designed to produce, not merely a monotonic trend
   crossing zero somewhere convenient. **PASS under Rung 1's formula.**
   **RETRACTED under Rung 2 (Sec3b below)**: Rung 1 achieved this by
   conflating the DYAD's closeness with generic bystanders' own closeness —
   Rung 2 corrects that conflation, and the same sweep no longer flips
   (stays `escalate` throughout `band_code=0→5`, `pressure: 1.250→0.250`).
   The dyad-closeness mechanism itself (Prediction 1) still holds; the
   claim that it was SUPPRESSING anonymous-audience amplification was
   wrong. See Sec3b for what replaces it.
5. **Rival floor** — `band_code=-1` (rival): `pressure=1.540`;
   `band_code=0` (stranger): `pressure=1.250`. Rival pressure is HIGHER
   (more escalation-prone), never lower — rivalry does not accidentally read
   as safer than ordinary distance. **PASS.**

No null. Every registered prediction held on the first run, with no
post-hoc formula adjustment — the composition in the PREREG is the exact
composition tested.

## 3b. Rung 2 — a regulating witness (PREREG Sec3b)

User: *"try it with near strangers, but one has their partner there to
regulate them."* Rung 1's `witnesses` was a bare count with no slot for a
bystander's OWN relationship to a disputant — genuinely unable to represent
this case. Generalized `witnesses` into `WitnessPresence` nodes, each
carrying its own `closeness`; the audience term is now a `Sum` over present
witnesses of `audience_gain*(1-witness.closeness)` instead of
`audience_gain*witnesses*(1-dyad_closeness)`. Zero new Rust (`Sum`/
`Neighbours` pre-existed).

**A real regression, found and corrected, not hidden.** Rung 1's own
"prediction 4" (interaction sweep) no longer holds: with all-anonymous
witnesses, dyad closeness now has ZERO effect on the audience term (it only
had one before because Rung 1 conflated the dyad's closeness with generic
bystanders' — a modeling shortcut, not a real claim). Re-run at the ORIGINAL
prediction-4 parameters (severity=0.8, witnesses=3 anonymous, band 0→5):
`1.250 → 1.050 → 0.850 → 0.650 → 0.450 → 0.250` — monotonic (the dyad term
alone still works), but never crosses into `defuse` any more, where Rung 1
crossed at `band_code=5`. **This is retracted, not silently updated**: Rung
1's claim that closeness suppresses generic-audience amplification was
wrong; the corrected model (a witness's OWN closeness does that, not the
dyad's) is more realistic — anonymous strangers' presence-pressure doesn't
care how close YOU are with your OWN dispute partner. Encoded as a standing
regression, `test_anonymous_witness_pressure_is_independent_of_dyad_closeness`.

**Prediction 6, run honestly — direction holds, flip does not (at the
originally-proposed severe scenario):**

```
3 anonymous witnesses                                   pressure=+1.350 -> escalate
2 anonymous + 1 regulating partner (closeness=0.9)      pressure=+1.215 -> escalate
partner lowers pressure: True
outcome flips escalate -> defuse: False
```

The registered PREREG hedge ("checked, not assumed, since the flip threshold
is an empirical fact") was necessary — it did not flip. Structural reason,
found by range-search rather than asserted: each `WitnessPresence`
contributes at most `audience_gain` (0.15) to `pressure`, so swapping ONE
anonymous witness for a fully-regulating partner (`closeness=0.9`) moves
`pressure` by only `0.15*0.9=0.135` — small relative to `issue_severity=0.9`
dominating the sum. **A single calm bystander cannot, on its own, overcome a
genuinely severe near-stranger dispute in front of a crowd — realistic, not
a bug.** Range-search over `{band_code, issue_severity}` at 1 witness found
where the SAME mechanism DOES flip a dispute already close to the
defuse/escalate boundary:

```
near-stranger, mild issue, 1 anonymous witness          pressure=+0.050 -> escalate
near-stranger, mild issue, 1 regulating partner         pressure=-0.085 -> defuse
outcome flips escalate -> defuse: True
```

Grounding for the witness-specific mechanism: Sbarra & Hazan (2008),
"Coregulation, Dysregulation, Self-Regulation" — an attachment partner's
presence measurably down-regulates physiological arousal during stress, a
distinct, evidenced mechanism from generic audience-size effects (Felson,
Rung 1). 4 new tests (12 total, all green): direction always holds; the
severe-scenario null; the borderline flip; and the anonymous-witness
closed-form check (`audience_gain` per witness, confirming Rung 2 is a
strict generalization of Rung 1's per-witness contribution, not a rewrite).

## 4. Honesty notes — what this does and does not establish

**Does establish**: the mechanical shape works — a real, held, discrete
`band_code` (this session's own bigville plumbing) composes with a severity
and witness signal into a defuse-or-escalate classification via the same
reusable Argmin-codebook pattern the register rung established, entirely
inside `run_rules()`, zero Python decision.

**Does NOT establish**: that `audience_gain=0.15` or the specific additive/
interaction formula are FITTED or empirically validated constants — they are
documented, un-fitted demo choices (same honesty class as `k=3.0` in CAT,
`res_gain=1.0` in CAN, `resolution_bins=6` in the register-backend rung).
The Felson / Coleman-Deutsch-Marcus citations (PREREG Sec2) motivate the
DIRECTION of the interaction term, not its magnitude. Anything about what
happens to the relationship or the game AFTER an escalation (no consequence
mechanic — PREREG Sec4). Anything about active third-party mediation (only
passive-witness audience pressure is modeled). Anything about a live
integration into `BigvilleGame`'s tick loop or the per-resident
`BigvilleOcelotResident` graphs — this stays a standalone harness, exactly
like `can_register_quantization_demo.py` before it (PREREG Sec4's own scope
boundary, not a gap discovered after the fact).

## 5. Cross-repo follow-on work — named, not built

1. **Wiring `issue_severity` from a real `HeldRule.confidence` contradiction**
   — `domains/cognitive_rule_frames.py::read_rule_document` already computes
   a per-clause `confidence`; nothing yet compares a resident's asserted
   claim against another resident's `HeldRule` to derive a real
   `issue_severity` instead of a hand-set demo value.
2. **Live `witnesses` from `seeds/bigville_loud_comm.json`'s hearing-radius
   mechanism** — this rung uses a bare integer; the real primitive
   (`lo_choose_loudness`/`lo_observe_act`) already computes who is in
   earshot and could supply a live count.
3. **A consequence mechanic** — what an `escalate` outcome actually does to
   the game state or the relationship (spite, `band_code` decay, a filed
   `SelfConcern`-style grudge) is unbuilt.
4. **Live integration into a `CognitionBackend`** — analogous to
   `domains/bigville_register_backend.py`'s `decide_registers`, a
   `decide_disputes`-shaped entry point over real `ActorContext` data is
   named but not built.

## 6. Files

- `docs/research/engine_substrate/RULE_DISPUTE_ESCALATION_PREREG.md`
- `docs/research/engine_substrate/RULE_DISPUTE_ESCALATION_RESULTS.md` (this file)
- `scripts/_build_rule_dispute_escalation_seed.py`
- `seeds/rule_dispute_escalation.json`
- `scripts/rule_dispute_escalation_demo.py`
- `tests/test_rule_dispute_escalation.py` (12/12, v1.1.0/Rung 2)
