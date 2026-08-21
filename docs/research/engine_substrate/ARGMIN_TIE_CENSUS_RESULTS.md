# Argmin/Argmax tie census — measured on live seed-driven decision paths

**Status: measurement complete. No behaviour changed.** Run in `count` mode, which
the instrument documents as byte-identical to the pre-rung engine: a tie still returns
the first-encountered extremum. This is a census, not an intervention.

## Why this was run

`docs/research/theory_convergence/GRAPHIC_EQUALISATION_V22_SUBSTRATE_GAP.md` §7 recorded
that ocelot passes the theory's determinism commitment **by means of** violating its
non-semantic-enumeration-order commitment: rules scan in insertion order, and within a
rule the first binding that progresses wins. `runners/dsl/src/argmin_tie.rs:5-15` already
quoted a prior measurement — *"`Argmin` returned a winner from FIVE IDENTICAL CANDIDATES
… on all 200 draws"* — and named `ArgminUnique` as the fix. But the module header also
recorded that its coverage was "185 CONFIGURATION reads and ZERO VERDICT reads": the
instrument existed and was not wired to anything that decides.

§7 therefore left the rate **unmeasured**. This closes that.

## Method

Full seed set (`load_all_seeds`), five utterances through `converse`, instrument in
`count` mode, counters read at the end. The counters are process aggregates, which is the
right shape here — a whole-process rate needs a whole-process total, and no per-caller
attribution is required for a ratio.

Probe: `scratchpad/tie_probe.py` (reproduced in §Reproduce). Elapsed 37s.

An earlier attempt measured through a 131-test pytest slice and did not complete: the
baseline pass alone took 18m35s and the instrumented pass was killed before
`pytest_sessionfinish` could write its sidecar. Driving the agent directly is two orders
of magnitude cheaper and exercises the same seed rules.

## Result

```
firings   : 148
ties      :  95
empties   :   0
refusals  :   0   (count mode — expected)
tie rate  : 95/148 = 64.19%
```

**Roughly two thirds of selector firings on a plain conversational workload are exact
ties, resolved by enumeration order.**

Per-site attribution (the instrument keys tied sites by the selector's own `value` Term,
so a site maps back to the rule that authored it):

| selector | value term | firings | ties |
|---|---|---|---|
| `Argmax` | `ranked_source.salience` | 90 | **90** |
| `Argmax` | recovery/threshold composite | — | — |
| `Argmax` | `AntiUnify` pattern | — | — |
| `Argmin` | `x.priority` | 1 | 1 |

Four distinct tied sites. One dominates.

## The dominant site is not a tie between equals

`Argmax` over `ranked_source.salience` ties on **90 of 90** firings. The obvious reading —
several goals that happen to be equally salient — is wrong. Measured directly:

```
goal count: 2
salience values: [(None, 2)]
sample: [('answer_topic', None), ('communicate', None)]
```

`salience` is **unset on every candidate**. The selector in
`seeds/default_mode_core.json::default_mode_mint_goal_context` ranks goals by an attribute
that is never populated on those goals, so every comparison is between two missing values.
It does not rank. It selects the first-encountered goal, while presenting as a salience
ranking.

13 rules across the seed corpus write *a* `salience` attribute — `pattern_salience`,
`mark_feature_salience`, `photon_column_synthesizes_retinal_percept`, and others — but on
episodes, features, patterns and retinal percepts, not on the `Goal` nodes this rule
ranks. Whether some other workload populates `Goal.salience` is **not established here**;
what is established is that this workload's goals have none and the selector still fires.

## What this does and does not establish

**Establishes:** the tie rate on this workload is 64.19% of 148 firings; four sites tie;
one site accounts for 90 of the 95 ties and ranks on an unpopulated attribute.

**Does not establish:**

- *That ties are wrong answers.* The instrument counts exact non-uniqueness at the
  extremum, not incorrect outcomes. Where candidates are genuinely interchangeable, a tie
  is harmless. Where they are not — the salience site — order is deciding something it
  should not, but this census does not show a downstream error, only that nothing is
  ranking.
- *A rate for the system.* One workload, conversation paths only. Motor, vision, program
  synthesis and humanoid paths are unexercised, and their selector populations differ.
- *Total coverage.* The instrument reaches `Argmin`/`Argmax` Terms. Selection also happens
  in rule-order scanning, first-binding-wins, and `admissible_moves` weighting, none of
  which this counts. **The true order-dependence of the system is at least this and
  probably more.**
- *Anything about `refuse_min`/`refuse_all`.* Not run. Whether refusing on non-uniqueness
  reproduces the committed bench is a separate, unmeasured question.

## Consequence for the gap review

§7 of the gap review can be updated from "unmeasured" to the figure above, with its
caveats. The sharper point it should carry: the substrate's determinism is not merely
*achieved through* semantic enumeration order — on this workload, order is the **primary**
decider in a majority of selector firings, and at the dominant site it is the **only**
decider.

## Reproduce

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0,'runners/dsl/python'); sys.path.insert(0,'.')
from substrate_rs import _native
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
_native.argmin_tie_enable("count"); _native.argmin_tie_reset()
a = WorldAdapter(seeds=()); load_all_seeds(a)
for u in ("What do you know about the moon?", "tell me more", "What are you?",
          "what gaps do you have?", "How does your collapse function work?"):
    a.converse(u, speech_act="question")
print(_native.argmin_tie_stats())
for row in _native.argmin_tie_sites(): print(row)
EOF
```
