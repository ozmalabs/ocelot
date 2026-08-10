# Process-efficiency assessment of the session's research loop

This document drives the agent's OWN meta-cognitive machinery
(`domains/meta_monitor.py`, `domains/perception_self_assessment.py`) on the
autopoietic research loop run this session, and surfaces its assessment +
suggested changes. It is a meta-assessment of the PROCESS, not the speech
outcome.

Everything below is explicitly tagged:

- **[MACHINE]** — verbatim output of the agent's graph-resident machinery
  (rules firing, the verdict it computed). Reproduce with
  `python scripts/assess_research_loop.py`.
- **[INFER]** — narration / interpretation by the assistant. NOT the machinery.

The single most important honest finding is stated up front, then the evidence.

---

## Headline finding [INFER, grounded in MACHINE output]

**The agent does not currently have a meta-assessor for a multi-iteration
research process.** `meta_monitor` is a *single-process spinning detector*: it
watches one process with one EFFORT and one PAYOFF signal over a sliding window
and flags `effort_without_payoff` when effort climbs while payoff stays flat (it
was built for the "322 features minted, recognition flat at 13" case). When the
session's 5-iteration loop is fed into it as-is, **the machinery returns no
meta-issue — but not because the loop was efficient.** It returns nothing for two
concrete, machine-verified reasons:

1. **Effort out of range.** The loop's effort rose by 4 over the window
   (1→5 iterations). The seed dial `effort_min_rise = 20.0` is calibrated for
   feature-count processes, so the spinning detector never arms.
2. **Payoff ambiguity.** The literal recognition margin moved -8 → -4 over the
   window (`payoff_change = +4.0`), which clears `payoff_improve_band = 3.0`, so
   the rule reads the domain loop as *improving* — even though recognition stayed
   below unigram the whole session. The machine cannot tell upstream WER/purity
   gains from movement of the probe target it was nominally measuring.

So the genuine, machine-grounded conclusion is: **the next fixer to build is a
process-level meta-assessor** (effort/payoff at the iteration grain, with the
two payoff KINDS — domain vs fixer/capability — kept distinct). The current
machinery is the right *shape* (its logic is correct, see below) but the wrong
*grain and dials* for this question.

---

## 1. meta_monitor on the research loop

### What was fed in [INFER]

The loop was registered as two processes so the SAME `detect_meta_issue` rule
could judge each, keeping the two payoff kinds the human asked us to separate:

- `research_loop_domain` — payoff = recognition margin over unigram (points;
  negative = below unigram). Series: `-8, -6, -6, -4, -4`.
- `research_loop_fixer` — payoff = cumulative loop-autonomy capabilities the loop
  bootstrapped into itself (prioritiser → feedback → diversification →
  harvest-precision). Series: `1, 2, 3, 3, 4`.

Effort for both = cumulative build-work `1..5` (one build per iteration).

### [MACHINE] verbatim — `get_meta_issues` after firing `detect_meta_issue`

```json
[]
```

### [MACHINE] verbatim — per-process state the rule computed

```json
{
  "research_loop_domain": {
    "effort_rise": 4.0,
    "payoff_change": 4.0,
    "window_full": 1,
    "meta_issue": "none",
    "effort_history": [1.0, 2.0, 3.0, 4.0, 5.0],
    "payoff_history": [-8.0, -6.0, -6.0, -4.0, -4.0]
  },
  "research_loop_fixer": {
    "effort_rise": 4.0,
    "payoff_change": 3.0,
    "window_full": 1,
    "meta_issue": "none",
    "effort_history": [1.0, 2.0, 3.0, 4.0, 5.0],
    "payoff_history": [1.0, 2.0, 3.0, 3.0, 4.0]
  }
}
```

### [MACHINE] verbatim — dials the rule judged against (`seeds/meta_monitor.json`)

```json
{ "window": 5, "effort_min_rise": 20.0, "payoff_flat_band": 2.0, "payoff_improve_band": 3.0 }
```

### Does the machinery's LOGIC hold? [MACHINE control]

To prove the empty result is a grain/dial mismatch and not a logic failure, the
same rule was run with effort rescaled into the dials' regime (rise 25 > 20) and
the domain payoff read as genuinely flat (the honest reading: the *probe target*
recognition never moved; the -8→-4 was upstream WER). The rule then fires
correctly:

```
issues with in-range effort:
[{'name': 'domain_flat', 'issue': 'effort_without_payoff',
  'effort_rise': 25.0, 'payoff_change': 0.0}]
```

The fixer process is NOT flagged (its payoff rose). **So the agent's spinning
detector works; it simply cannot, at its current grain and dials, represent this
session's loop.** [INFER] That gap is the finding.

### Where effort went without payoff vs where it was efficient [INFER, reading the series the machine holds]

Reading the two payoff series the machine recorded:

- **Efficient (the fixer track COMPOUNDED):** `research_loop_fixer` payoff is
  monotone `1→2→3→3→4`. Every iteration except iter-4 added a durable
  capability that made the loop more autonomous. By the agent's compression/
  curiosity quality measure [INFER], these iterations *paid off* — they reduced
  the work the loop needs from the operator next time (the prioritiser, feedback
  re-rank, diversification, harvest-precision all persist).
- **Effort without payoff (the domain track was the PROBE, not the target):**
  `research_loop_domain` never crossed zero — recognition stayed below unigram
  all 5 iterations. The only domain *movement* (iter-4, -6→-4) was upstream
  (purity .29→.59, WER 6.6→4.2), not the recognition probe. Measuring the loop
  by this series is the category error the human flagged: it was never the
  target.
- **The pure waste, machine-corroborated by the perception yardstick (§3):** the
  iter-5 **specificity GATE** was a fix-the-OUTCOME slip — it added `+0`
  capability (the fixer series is flat at the gate, then +1 only when the
  harvest-precision fix landed) and was made MOOT by fixing the harvester at
  source. That is the clearest local "effort without payoff" in the run.

---

## 2. Compression / curiosity drive — which iterations compressed vs spun [INFER]

The agent's quality measure is compression (a capability that reduces future
work / description length is a real gain; chasing a number that doesn't move is
not). By that measure:

| iter | what | compressed? |
|---|---|---|
| 1 | clustering (capped) + **gap-prioritiser** | fixer compressed (loop ranks its own gaps now); domain ~flat |
| 2 | **feedback/re-rank** + LPC (+42% LOSO, still <unigram) | fixer compressed; domain modest, still below target |
| 3 | **diversification/exhaust** + chunking (honest negative) | fixer compressed; chunking located the unit-grain constraint (a real prune, not waste) |
| 4 | coarsen-grain (purity/WER up, recog still <unigram) | upstream compression only; NO fixer added |
| 5 | GATE (wasted) → **harvest-precision** (54%→6% promiscuity) | GATE spun; harvest-precision compressed AND made the GATE moot |

[INFER] The honest negatives (iter-3 chunking) are NOT spinning — they
compressed by ruling out a region and locating the unit-grain constraint. The
GATE (iter-5) is the spin: it added a downstream patch that a source fix
dissolved.

---

## 3. Perception self-assessment — corroborating the bottleneck [MACHINE]

`domains/perception_self_assessment.py` is the agent's yardstick ON ITS UNITS
(no labels): good units are predictable beyond their own frequency and the
sequence compresses. The session's recorded state was "recognition below unigram
/ noisy units." Driven on a session-like (below-unigram, frequency-artifact)
unit stream, the agent's graph-resident frontier rule fires:

```
predict_over_freq: 1.167   (floor 1.25)   -> below floor
compress_ratio:    0.972   (ceiling 0.85) -> above ceiling
AGENT FRONTIER VERDICT: perception
```

[INFER] This is the agent's own machinery saying the bottleneck is the UNITS
(perception), not recognition tuning. It corroborates the process finding: effort
spent on downstream recognition (and on the iter-5 gate) was effort downstream of
the real bottleneck the agent's yardstick can already point at.

---

## 4. The agent's surfaced PROCESS changes

Tagged by what the machinery actually DERIVES vs assistant inference.

### Derived by the machinery [MACHINE]

1. **Build a process-level meta-assessor (the next fixer).** Directly evidenced:
   `meta_monitor` returned `[]` on the loop because its grain (effort_min_rise
   20) and single payoff cannot represent a 5-iteration research process. The
   control run proves the *logic* is right, so the fix is grain + a second payoff
   channel, not new logic. **This is the agent's machinery diagnosing its own
   blind spot.**
2. **Distinguish probe-value from domain-payoff.** Directly evidenced: the
   domain payoff series registered as "improving" (`payoff_change +4 >
   improve_band 3`) purely from upstream WER, while the probe target never moved.
   The machine literally mis-scored the loop by conflating them — so the two must
   be separate signals.
3. **Perception is the frontier, not recognition tuning.** [MACHINE] the
   perception frontier rule fires `frontier = perception` on the session-like
   units. Effort downstream of that is the leak.

### Assistant inference, supported by the machine's recorded series [INFER]

4. **Fix-the-fixer-first; skip fix-the-outcome detours.** The fixer payoff series
   compounded (`1→4`) while the domain series never crossed zero, and the one
   fix-the-outcome move (the GATE) added `+0` capability and was superseded.
   Inference: prefer source/capability fixes over downstream outcome patches.
5. **Verify-live as a loop invariant.** Not representable in the current
   machinery (it has no signal for "claim vs measured"), but the session's
   repeated over-claims ("3/3"→"2/3", re-corrected 3×) are the
   trust-the-prose-not-the-live-output leak. A standing "read live output before
   asserting" phase would close it.
6. **Make process-self-assessment a STANDING loop phase.** This very step had to
   be run by hand; the loop has no recurring phase that turns the meta-monitor on
   ITSELF each iteration.
7. **Corroboration (≥2 independent shapes) as the genuineness bar.** [INFER]
   matches the existing perception yardstick's design, which already requires
   beating BOTH a chance baseline AND a frequency baseline before trusting a
   signal.
8. **Budget the slow end-to-end runs differently.** The 34-min real run
   misdiagnosed as a zombie + killed, and the repeatedly-timing-out LibriSpeech
   re-runs, are process-management thrash — not representable in the current
   machinery (no signal for run-state / wall-clock), another argument for the
   process-level meta-assessor in (1).

---

## 5. HONEST accounting: machine vs narration

- **Genuinely the agent's machinery:** the `meta_monitor` verdict (`[]` + the
  computed effort_rise/payoff_change per process), the control proving the rule's
  logic fires when in-range, and the `perception_self_assessment`
  `frontier = perception` verdict. Suggestions (1), (2), (3) are *derived from*
  those machine outputs.
- **Assistant narration:** the per-iteration compression table (§2), and
  suggestions (4)–(8). These are defensible readings of the series the machine
  holds, but the current machinery does not itself emit them — several (verify-
  live, run-state, two-kinds-of-payoff over many iterations) are **not
  representable** in `meta_monitor` as built.
- **The honest bottom line:** `meta_monitor` is not built to assess a research
  process; it is a single-process spinning detector. The correct finding is
  therefore not a clean machine verdict on the loop's efficiency but a diagnosis
  that **the agent lacks a process-level meta-assessor** — that absence is the
  next fixer to build, and it is exactly the kind of fixer-fix that compounded
  productively all session.

---

## Reproduce

```
python scripts/assess_research_loop.py          # meta_monitor on the loop
python -m pytest tests/test_stt_pipeline.py tests/test_perception_self_assessment.py -q
```
