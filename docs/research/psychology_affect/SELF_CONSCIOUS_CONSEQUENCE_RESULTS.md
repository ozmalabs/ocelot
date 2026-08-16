# Self-conscious emotion consequences — RESULTS

Registered design: `SELF_CONSCIOUS_CONSEQUENCE_PREREG.md`. **All 5
predictions confirmed**, including a real end-to-end integration through
the guilt→shame flip scenario `test_rule_dispute_full_pipeline.py`
already established.

## 1. Live run (`scripts/self_conscious_consequence_demo.py`)

```
=== Predictions 1/2: guilt -> reparative only, shame -> withdrawal only ===
guilt: {'consequence': 'reparative', 'reparative_desire_state': 0.30000001192092896, 'withdrawal_desire_state': 0.0}
shame: {'consequence': 'withdrawal', 'reparative_desire_state': 0.30000001192092896, 'withdrawal_desire_state': 0.30000001192092896}

=== Prediction 3: every other classification moves neither ===
hubristic_pride: {'consequence': None, 'reparative_desire_state': 0.0, 'withdrawal_desire_state': 0.0}
authentic_pride: {'consequence': None, 'reparative_desire_state': 0.0, 'withdrawal_desire_state': 0.0}
embarrassment: {'consequence': None, 'reparative_desire_state': 0.0, 'withdrawal_desire_state': 0.0}
none: {'consequence': None, 'reparative_desire_state': 0.0, 'withdrawal_desire_state': 0.0}

=== Prediction 4: repeated guilt accumulates ===
guilt 0: reparative_desire_state=0.3000
guilt 1: reparative_desire_state=0.6000
guilt 2: reparative_desire_state=0.9000

=== Prediction 5: domain isolation ===
monopoly, unaffected by chess's 2 prior guilts: {'consequence': 'reparative', 'reparative_desire_state': 0.30000001192092896, 'withdrawal_desire_state': 0.0}

=== Integration: the real guilt -> shame flip scenario ===
dispute 0: emotion=guilt reparative=0.3000 withdrawal=0.0000
dispute 1: emotion=guilt reparative=0.6000 withdrawal=0.0000
dispute 2: emotion=guilt reparative=0.9000 withdrawal=0.0000
dispute 3: emotion=guilt reparative=1.2000 withdrawal=0.0000
dispute 4: emotion=shame reparative=1.2000 withdrawal=0.3000
```

## 2. Predictions

1. **Guilt applies evidence to `reparative_desire_for`, not
   `withdrawal_desire_for`** — `PASS`.
2. **Shame applies evidence to `withdrawal_desire_for`, not `reparative_
   desire_for`** — `PASS`.
3. **Every other classification (hubristic_pride/authentic_pride/
   embarrassment/none) moves neither** — `PASS`, confirmed across all
   four remaining values, not merely the two tested by predictions 1/2.
4. **Repeated guilt in the same domain accumulates** — `PASS`,
   `0.30 → 0.60 → 0.90` across three guilt incidents.
5. **Domain isolation holds** — `PASS`. `monopoly`'s `reparative_desire`
   reads exactly `0.30` (the base single-incident value) despite
   `chess` already having accumulated two prior guilt incidents on the
   SAME resident — no cross-domain leakage.

**Integration, not just isolated unit checks**: the real guilt→shame
flip scenario (`test_rule_dispute_full_pipeline.py`'s own established
fixture — Bob repeats the same monopoly-rules dispute 5 times, the
pattern solidifies from `specific_act` to `global_self` attribution on
the 5th) now shows `reparative_desire` climbing across the first 4
(guilt) disputes — `0.30 → 0.60 → 0.90 → 1.20` — then FREEZING exactly
when the classification flips to shame on the 5th, at which point
`withdrawal_desire` receives its first-ever evidence (`0.30`) instead.
The two consequence channels track the emotion classification's own
transition precisely, live, not just in staged unit tests.

## 3. Honesty notes

**Does establish**: shame and guilt now have differentiated,
Tangney & Dearing (2002)-grounded motivational consequences, closing
exactly the asymmetry named after the hate→pity rung landed (hate/pity
got `removal_desire_for`/`pity_for`; shame/guilt had nothing). Built
entirely in the bridge layer (`domains/can_self_worth_bridge.py`,
`domains/rule_dispute_full_pipeline.py`) — `seeds/self_conscious_
emotions.json`, a foundational, independently-tested seed, is completely
untouched (confirmed by a git-status-gated test, matching this arc's own
precedent for not touching foundational seeds when a bridge layer
suffices).

**Does NOT establish**: any arousal/resentment-debt-style amplification
of `reparative_desire`/`withdrawal_desire` (flat `alpha`, by design —
scope boundary, not an oversight). Does NOT model the actual downstream
behavioral act (an apology, an actual withdrawal) — scoped to the
motivational Concept existing and accumulating evidence, matching hate's
own consequence-Concept-not-enacted-behavior convention.

## 4. Files

- `docs/research/psychology_affect/SELF_CONSCIOUS_CONSEQUENCE_PREREG.md`
- `docs/research/psychology_affect/SELF_CONSCIOUS_CONSEQUENCE_RESULTS.md` (this file)
- `domains/can_self_worth_bridge.py` (edited: `mint_domain_reparative_desire`, `mint_domain_withdrawal_desire`, `record_self_conscious_consequence`)
- `domains/rule_dispute_full_pipeline.py` (edited: wires the new consequence call into `run_rule_dispute`)
- `scripts/self_conscious_consequence_demo.py` (new)
- `tests/test_self_conscious_consequence.py` (10/10, new)
