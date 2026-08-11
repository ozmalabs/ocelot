# Fusion weighting — per-context reliability weighting of the multi-pronged fusion

Close, or honestly fail-to-close, the **fusion-weighting gap** (the open issue from the TFS
validation, commit 90b799c9): the multi-pronged native fusion **trails the formant-prong-alone
(62.2%)** because the weak prongs (articulatory ~25–33%, voicing) are multiplied in at a
**global** train weight on *every* token — so where they are locally flat/uncertain they drag
the strong formant prong wherever the prongs disagree (the margin-error).

Run: `PYTHONUNBUFFERED=1 python -m scripts.fusion_weighting`
(full LOSO log: `/tmp/fusion_weighting_full.log`, end marker `FUSION_WEIGHTING_COMPLETED`).

---

## (1) The agent's design — the per-context trust signal, how composed, the safety argument

**The trust signal: each prong's PER-CONTEXT DECISION MARGIN (peakiness of its own
admissibility field).** Each prong is top-centred (best word = 0, the rest ≤ 0); the margin is
the *mean depth* of the field below the winner:

```
conf_p(token) = -(1/N) · Σ_w score_c_p(w)        score_c_p(w) = p(w) - max_w' p(w')
```

- **FLAT field** (the prong has no opinion here — every word near-equally admissible) →
  `conf_p ≈ 0` → the prong **defers** (its excluder flattens toward neutral; it cannot corrupt).
- **PEAKED field** (one word clearly stands out) → `conf_p` large → the prong **constrains**.

**How composed (native, no new grammar).** `conf_p = Neg(Div(Sum_w(top_centred), Count))`,
verified against `term.rs` (Sum / Count / Div / Neg / Max / Minus / Plus / Times / Argmax /
NodesWhere all already present — zero new primitives, no Rust change, no rebuild). The whole
fused decision — top-centring, the margin, the per-context weighting, the sum, the argmax — is
**one native Term** evaluated by `substrate.evaluate` (`domains/native_fusion.py:
fusion_score_term_pcw` / `predict_fusion_term_pcw`).

**The weighting (ASYMMETRIC — this is the safety argument).** Only the **weak articulatory AUX
prong** is re-weighted per-context; the **formant ANCHOR** (the 62.2% prong) keeps **full
weight** on every token:

```
score(w) = h_c(w)                                          # formant ANCHOR — full weight, ALWAYS
         + w_art · min(1, conf_a / cref_a) · a_c(w)        # articulatory AUX — global × per-context
         + ng_logp(w)                                      # n-gram prior — unweighted
```

`w_art` keeps the prong's **global** reliability (the existing train-measured weight); the
clamped ratio adds the **per-context** trust. `cref_a` = **median train AUX margin** (a
MEASUREMENT, train-only, makes the ratio dimensionless), not a tuned knob.

- **Why asymmetric.** A first symmetric version that confidence-weighted *both* prongs **hurt**
  (seven 55.6%→19.4%, one/five collapsed): on a hard token the *formant* field is flat too, so
  `conf_h→0` down-weighted the **strong** prong and handed the call to the weak prongs — the
  opposite of safe. The anchor must keep full weight.
- **Why the clamp to [0,1].** `min(1, conf_a/cref_a)` means the AUX weight can only ever **drop
  below** its global `w_art` (defer when uncertain), never rise **above** it. So per-context
  weighting is a pure soft-**excluder down-weighter**: it can only *remove* the drag the global
  weight caused, never grant the weak prong more trust than its measured global reliability.

**Safety argument.** Where the articulatory prong is flat/uncertain on a token, `conf_a → 0` so
its weight → 0 and the formant anchor decides that token **alone** — the fusion cannot
underperform formant-alone on the tokens the weak prong would otherwise have dragged. Where the
AUX prong is locally peaked **and** globally reliable, it still helps (**additive**: it can
break an anchor near-tie on a digit it knows).

**Honest limit (stated up front).** A prong can be **confidently WRONG** — peaked on the wrong
word. Margin/peakiness cannot catch that; it down-weights *uncertain* prongs (disagreement born
of the weak prong's fuzziness), not confidently-wrong ones. The driver measures whether that is
enough to clear 62.2%.

**Donkey audit.** Fusion = native Term via `substrate.evaluate` — no net, no `.fit`, no
gradient, no sweep-to-fit. The recogniser **prongs are unchanged** (only the fusion weighting
differs). `conf_ref` is a train-only median (a measurement). Real FSDD, held-out **never**
banked (LOSO). `CortexLoop` + `solve_for_n.py` untouched. No Rust touched (`git status`: only
`domains/native_fusion.py` modified + `scripts/fusion_weighting.py` new) → no `cargo build`
needed; the existing `.so` already exposes every primitive used.

---

## (2) Per-context-weighted fusion vs the bars

**FSDD LOSO, n = 3000, chance 0.100, held-out never banked** (full log,
`FUSION_WEIGHTING_COMPLETED`):

| recogniser | accuracy | reference |
|------------|----------|-----------|
| (a) formant-prong-alone | **62.2%** | 62.2% — **THE BAR** |
| (b) global-weight fusion (TFS) | 60.6% | 60.6% |
| **(fix) per-context-weighted fusion** | **61.4%** | — the agent's fix |
| (c) exemplar bank | 80.6% | 83.5% |

- delta (pcw − global-weight) = **+0.8 pts** (61.4% vs 60.6%) — the fix improves the fusion.
- delta (pcw − formant-alone) = **−0.8 pts** (61.4% vs 62.2%) — it does **not** clear the bar.

**Per-digit fusion accuracy** (does the margin-error clear — does seven/three stop being
dragged?):

| digit | formant | global | pcw | pcw − global |
|-------|---------|--------|-----|--------------|
| zero  | 59.3 | 66.0 | 65.7 | −0.3 |
| one   | 69.0 | 67.0 | 67.3 | +0.3 |
| two   | 48.7 | 36.7 | 40.3 | **+3.7** |
| three | 62.7 | 67.7 | 67.3 | −0.3 |
| four  | 56.3 | 48.3 | 51.7 | **+3.3** |
| five  | 75.0 | 68.7 | 69.0 | +0.3 |
| six   | 60.7 | 38.0 | 38.3 | +0.3 |
| seven | 66.0 | 58.3 | 60.0 | **+1.7** |
| eight | 72.3 | 85.3 | 85.3 | +0.0 |
| nine  | 52.3 | 70.0 | 69.3 | −0.7 |

The per-context weighting moves the *dragged* digits in the right direction (**two +3.7, four
+3.3, seven +1.7** — seven, the very digit the binary gate over-corrected, recovers) while
leaving the digits the fusion already helped (eight, three, nine, zero) essentially untouched.
No digit regresses by more than 0.7. SIX-SINK (non-six wrongly → six): formant 288 → global 239
→ **pcw 232** (per-context weighting removes a few more).

But the two biggest losses vs formant-alone — **six (60.7→38.3)** and **two (48.7→40.3)** — are
**not** uncertainty-driven: the weak prongs there are *confidently* steering six → eight/seven
(`six→eight 68/300`, `six→seven 66/300`, both essentially unchanged by the per-context
weighting). Those are confidently-wrong prongs, which margin cannot down-weight.

---

## (3) Verdict — does the fusion now clear the best single prong?

**PARTIAL — honest.** Per-context reliability weighting **beats the global-weight fusion (61.4%
vs 60.6%, +0.8)** and recovers the specific dragged digits (two/four/seven), confirming the
mechanism: where the weak prong is *uncertain* on a token, deferring it removes the drag. But it
**does not clear the formant-prong-alone bar (61.4% vs 62.2%, −0.8)**.

**Why, pinpointed (not "more data").** The trust signal *does* separate the *uncertain*-prong
drag — that part of the gap closes. The residual gap is **not** uncertainty: it is the weak
prongs being **confidently wrong** on six and two (`six→eight` 68/300, `six→seven` 66/300 — both
flat across global→pcw). Those prongs are *peaked* there, so their per-context margin is *high*,
so per-context weighting (correctly, by its own definition) keeps them at full `w_art` — and
they out-vote the anchor on tokens the anchor had right. **Decision margin measures confidence,
not correctness; a confidently-wrong prong has high margin.** This is exactly the honest limit
stated in the design, now measured.

**Net.** The fusion-weighting fix is real and correct as far as it goes (weak prongs defer where
unreliable → the fusion strictly improves over the global weight and the dragged digits
recover), but per-context *margin* is the wrong signal for the *remaining* drag, which is
confidently-wrong prongs on six/two. Closing the last 0.8 pt to clear 62.2% needs a trust signal
keyed to **per-prong-per-digit correctness** (e.g. a train-measured reliability of the AUX prong
*on the digit it is currently asserting*, so a prong that is reliably-wrong when it claims "six"
is down-weighted there) — a *different* signal, not more weighting of the same margin and not
more audio.
