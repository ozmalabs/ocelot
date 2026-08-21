# Argmin/Argmax tie census — measured on live seed-driven decision paths

**Status: measurement complete. No behaviour changed.** Run in `count` mode, which
the instrument documents as byte-identical to the pre-rung engine: a tie still returns
the first-encountered extremum. This is a census, not an intervention.

## HEADLINE CORRECTION — the 64% figure is a conversation artefact

**Read this before quoting any number from this document.** The 64.19% below was measured
on one workload of 148 firings. Four further workloads, measured afterwards
(§Multi-workload census), give a total of **2,041 ties in 174,750 firings — 1.17%**:

| workload | firings | ties | rate |
|---|---|---|---|
| conversation | 148 | 95 | **64.19%** |
| ARC (transform / decompose / magnitude) | 159,813 | 645 | 0.40% |
| ls20 (see / mapnav) | 13,256 | 1,187 | 8.95% |
| quanta navigation | 1,523 | 114 | 7.49% |
| embodied | 10 | 0 | 0.00% |
| **total** | **174,750** | **2,041** | **1.17%** |

The conversational workload is **three orders of magnitude smaller** than ARC and its rate
is 160× higher. Its figure is dominated by a single site firing 90 times. Quoting 64.19%
as *the* tie rate would be wrong by a factor of ~55.

The original document carried the caveat "one workload, conversation paths only". The
caveat was correct and insufficient: a caveat that a reader can skip past is not the same
as a number they cannot misread. The correction is therefore at the top, not in a section.

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
| `Argmax` | `ranked_source.salience` (`default_mode_mint_episode_context`) | 90 | **90** |
| `Argmax` | recovery/threshold composite | — | — |
| `Argmax` | `AntiUnify` pattern | — | — |
| `Argmin` | `x.priority` | 1 | 1 |

Four distinct tied sites. One dominates.

## CORRECTION (same day, before any downstream use)

**The first version of this section was wrong twice, and is corrected here rather than
silently edited.** It named the wrong rule and drew the wrong conclusion from evidence
about the wrong nodes. Both errors came from the same mistake: I read a site's
`value_term` off the census, assumed which rule authored it, and measured the node set
that assumption implied instead of the one the selector actually reads.

What was published:

> `Argmax` over `ranked_source.salience` in `default_mode_mint_goal_context` ties on 90 of
> 90 firings because `salience` is **unset on every candidate**… two goals, both `None`.

What is true:

1. **Wrong rule.** Two rules in `seeds/default_mode_core.json` bind `ranked_source`.
   `default_mode_mint_goal_context` ranks by `{"type":"Lit","value":0.0}` — a constant, so
   it ties *by construction and by design*: it is a "pick any unresolved goal" written as
   an `Argmax`. The salience selector is **`default_mode_mint_episode_context`**.
2. **Wrong node set.** That selector ranges over `agent -recorded_episode->` filtered to
   `consolidated == true` — **episodes, not goals**. The published measurement read
   `has_goal` neighbours, which the selector never looks at.
3. **Wrong diagnosis.** Measured on the correct set: **5 consolidated episodes, all with
   `salience = 1.0`.** Salience is not unset. It is *uniform*.

## The dominant site: a constant where a ranking was intended

`Argmax` over `ranked_source.salience` in `default_mode_mint_episode_context` ties on
**90 of 90** firings. Not because the attribute is missing, but because
`seeds/memory_core.json::rule_episode_from_message` mints every message-derived episode
with

```json
"salience": {"__term__": {"value": 1.0, "type": "Lit"}}
```

a hardcoded literal. Every episode of that kind therefore carries identical salience by
construction, and an `Argmax` over a constant cannot rank. The selector returns the
first-encountered consolidated episode while presenting as a salience ranking.

This is milder than the retracted claim in one respect — the attribute is populated, so
nothing is reading a `None` — and identical in the respect that matters: **the ranking is
vacuous, and the outcome is decided by enumeration order.** It is also an instance of this
repo's own standing pattern, a scalar written where a shape belongs.

Other rules *do* derive salience from a real quantity — `episodic_bind_observed_event_once`
and `working_memory_output_gate` both set it from an `Attr` rather than a literal. Those
paths are not exercised by a conversational workload, so whether salience differentiates
episodes elsewhere is **open and unmeasured here**.

## What this does and does not establish

**Establishes:** the tie rate on this workload is 64.19% of 148 firings; four sites tie;
one site accounts for 90 of the 95 ties and ranks by an attribute that is a hardcoded
constant on every candidate it sees, so it cannot rank them.

**Does not establish:**

- *That ties are wrong answers.* The instrument counts exact non-uniqueness at the
  extremum, not incorrect outcomes. Where candidates are genuinely interchangeable, a tie
  is harmless. At the salience site nothing is ranking, so order decides — but this census
  does not show a downstream error, only the absence of ranking.
- *A rate for the system.* One workload, conversation paths only. Motor, vision, program
  synthesis and humanoid paths are unexercised, and their selector populations differ.
- *Total coverage.* The instrument reaches `Argmin`/`Argmax` Terms. Selection also happens
  in rule-order scanning, first-binding-wins, and `admissible_moves` weighting, none of
  which this counts. **The true order-dependence of the system is at least this and
  probably more.**
- *Anything about `refuse_min`/`refuse_all`.* Not run. Whether refusing on non-uniqueness
  reproduces the committed bench is a separate, unmeasured question.

## Multi-workload census

Run with the same instrument and mode, one pytest invocation per domain, counters reset at
session start and read at session end (`scratchpad/tie_plugin.py`).

| workload | tests | firings | ties | rate | pick-any idiom | genuine |
|---|---|---|---|---|---|---|
| conversation | — | 148 | 95 | 64.19% | — | — |
| ARC | 84 | 159,813 | 645 | 0.40% | 387 | 258 |
| ls20 | 17 | 13,256 | 1,187 | 8.95% | 0 | 1,187 |
| quanta navigation | 8 | 1,523 | 114 | 7.49% | 0 | 114 |
| embodied | 31 | 10 | 0 | 0.00% | 0 | 0 |
| **total** | | **174,750** | **2,041** | **1.17%** | | |

"pick-any idiom" counts ties at a selector whose entire `value` term is a `Lit` — the
`Argmin(…, 0)` "does any element exist" form the static census identified. Those ties are
by design and are separated rather than folded into the headline. In ARC they are 60% of
all ties; genuine ties there are 258 in 159,813 firings — **0.16%**.

Two observations that matter more than the aggregate:

1. **Tie rate is a property of the workload, not of the engine.** It spans 0% to 64%
   across five workloads of the same system. Any single-workload figure — including the
   one this document originally led with — describes that workload.

2. **`ls20` and `quanta` tie at ~8% with zero idiom ties**, so those are all genuine
   non-unique extrema on spatial/perceptual paths. That is the population worth looking at
   next if anyone wants to know whether ties are ever consequential: bigger than
   conversation's by an order of magnitude, and not explained away as a deliberate
   pick-any.

The `refuse_all` result in `DECISION_LAYER_PREREG.md` §4 — refusing every tie changed no
reply — was measured on the **conversation** workload only. It has not been run against
ARC, ls20 or quanta, and this census gives no reason to assume it transfers.

## Consequence for the gap review

§7 of the gap review is updated from "unmeasured" to the figure above, with its caveats
and the correction in §CORRECTION. The sharper point it should carry: the substrate's determinism is not merely
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
