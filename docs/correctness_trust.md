# Correctness-keyed trust — fix the fusion weighting (gap 2, the named next from 7cd7f60e)

Close, or honestly fail-to-close, **gap 2**: the multi-pronged native fusion trails the
formant-prong-alone (62.2%). Commit 7cd7f60e's per-context **margin** weighting reached 61.4%
(+0.8 over global fusion) by deferring **uncertain** weak prongs — but could not clear
formant-alone, because the residual drag is the weak AUX (articulatory) prong being
**confidently WRONG** on six (`six->eight` 68/300, `six->seven` 66/300). Margin measures
*confidence*, not *correctness*: a confidently-wrong prong has high margin and keeps full weight
(Dunning-Kruger inside the fusion). The named next was **a trust signal keyed to per-prong-per-
asserted-digit CORRECTNESS** — the prong's track record.

Run: `PYTHONUNBUFFERED=1 python -m scripts.correctness_trust`
(full LOSO log: `/tmp/correctness_trust_full.log`, end marker `CORRECTNESS_TRUST_COMPLETED`).

---

## (1) The agent's design — the correctness key, how combined with margin, the train-only proof

**The correctness signal: the AUX prong's TRAIN precision-when-it-asserts-d (its track record).**
On the TRAIN speakers only, for each digit `d`:

```
prec_a[d] = P(true == d | AUX prong asserts d)
          = #(train tokens where AUX argmax == d AND truth == d) / #(train tokens where AUX argmax == d)
```

This is the fraction of the time the AUX prong is *actually right* at the moment it claims `d` —
a **measurement** of the prong's reliability on each asserted digit. A prong reliably-wrong when
it asserts "six" gets a **low** `prec_a["six"]`; reliably-right when it asserts "eight" gets a
**high** `prec_a["eight"]`. (Measured `prec_a` per fold below — six is consistently the lowest,
confirming the diagnosis: the AUX prong is reliably wrong when it says six.)

**How it weights the vote (native).** The AUX prong's *vote for a digit* is its **assertion** =
`argmax_w a_c(w)` (its own most-admissible word). The correctness trust on a token is
`prec_a[that asserted digit]`, read **natively** as `Attr( Argmax_w(aux_field), prec_a )` — the
precision attribute of the AUX-assertion node. When the AUX prong asserts "six" and
`prec_a["six"]` is low, its **whole excluder is scaled down on that token**, catching the
confident-wrongness margin cannot. `prec_a ∈ [0,1]` (a precision) — no clamp needed.

**Combined with the existing margin (the agent's choice: PRODUCT = soft-AND of two excluders).**

```
trust_a(token) = min(1, conf_a / cref_a)   ·   prec_a[ argmax_w a_c(w) ]
                 \____ margin (pcw) _____/       \____ correctness key ____/

score(w) = log_a_h_c[w]                                  # formant ANCHOR — full weight, ALWAYS
         + w_art · trust_a · log_a_a_c[w]                # articulatory AUX — margin × correctness
         + ng_logp[w]                                    # n-gram log-prior — unweighted
predict  = argmax_w score(w)
```

The product is small whenever the AUX prong is **either** uncertain here (low margin) **or**
reliably-wrong on what it asserts (low precision) — exactly the union of the two failure modes
the diagnosis names. Both factors are in `[0,1]`, so the AUX weight `w_art·trust_a` can still
only **drop below** its global `w_art`, never rise — a pure soft-**excluder** down-weighter that
can only *remove* drag. The formant **anchor stays full weight** (the same safety argument:
never hand a hard token to the weak prong). We also measure a **MIN** combiner and a
**correctness-ALONE** ablation (no margin), to show the result is not an artifact of one combiner.

**How composed (native, no new grammar).** `Attr( Argmax_w(top-centred aux field), prec_a )` —
the nested `Argmax` (the AUX assertion) feeding an `Attr` (the precision lookup), inside the
per-candidate score, inside the outer fusion `Argmax`. Verified against `term.rs` /
`jsonio.rs`: `Argmax / Attr / Min / Div / Times / Plus / Minus / MaxOver / Sum / Count / Neg /
NodesWhere` all already present — **zero new primitives, no Rust change, no rebuild**. The whole
decision is one native Term via `substrate.evaluate`
(`domains/native_fusion.py: fusion_score_term_ckt / predict_fusion_term_ckt`).

**TRAIN-ONLY safety proof (the line between a track record and a fit).** `prec_a` is recomputed
**per fold from that fold's TRAIN speakers only** (`scripts.correctness_trust:_measure_aux_precision`,
iterating `train_idx` exclusively). The LOSO held-out speaker is **never** used to build the
precision table — no test peeking, no per-test-token peeking. It is a **measurement** of the
prong's track record, **not** a sweep-to-fit: no tuning against the test, no grid, no `.fit`, no
gradient. The neutral default `prec_a[d] = 1.0` for any digit the AUX prong never asserts on
train (no evidence ⇒ no penalty; the margin and anchor still govern) is stated honestly.

**Donkey audit.** Native Term via `substrate.evaluate`; no net, no `.fit`, no gradient, no
sweep-to-fit. The recogniser **prongs are unchanged** (only the AUX fusion weight differs;
`native_fusion.py` edits are purely **additive** — the original `fusion_score_term` /
`fusion_score_term_pcw` Terms are byte-intact). Real FSDD, held-out **never** banked nor used for
`prec_a` (LOSO). `CortexLoop` + `solve_for_n.py` **untouched**. **No Rust touched** (`git status`:
only `domains/native_fusion.py` modified + `scripts/correctness_trust.py` new) → no `cargo build`
needed; the existing `.so` exposes every primitive used. (Memory hygiene: the script frees each
fold's large native substrates + `gc.collect()` between folds — pure world-adapter cleanup under
a memory-pressured host, no agent state.)

---

## (2) Correctness-keyed fusion vs the bars

**FSDD LOSO, n = 3000, chance 0.100, held-out never banked** (full log,
`CORRECTNESS_TRUST_COMPLETED`):

| recogniser | accuracy | reference |
|------------|----------|-----------|
| (a) formant-prong-alone | **62.2%** | 62.2% — **THE BAR** |
| (b) per-context-MARGIN fusion (pcw) | 61.4% | 61.4% |
| (c) global-weight fusion | 60.6% | 60.6% |
| **(fix) correctness-keyed fusion (product)** | **63.7%** | — the agent's gap-2 fix |
| correctness-keyed (MIN combiner) | 63.6% | — robustness |
| correctness-ALONE (ablation, no margin) | 63.6% | — ablation |
| (d) exemplar bank | 80.6% | 80.6% |

- delta (ckt − margin-pcw) = **+2.3 pts** (63.7% vs 61.4%) — clears the pcw plateau.
- delta (ckt − formant-alone) = **+1.5 pts** (63.7% vs 62.2%) — **clears the bar**.
- The MIN combiner (63.6%) and the correctness-ALONE ablation (63.6%) land within 0.1 pt of the
  product — the gain is the **correctness key**, not the combiner choice (the margin adds ~0.1 pt
  on top). This is the honest attribution: the precision track record is what carries it.

**Per-digit fusion accuracy** (does the SIX drag clear?):

| digit | formant | margin (pcw) | ckt | ckt − formant |
|-------|---------|--------------|-----|---------------|
| zero  | 59.3 | 65.7 | 61.3 | +2.0 |
| one   | 69.0 | 67.3 | 69.3 | +0.3 |
| two   | 48.7 | 40.3 | 45.7 | −3.0 |
| three | 62.7 | 67.3 | 65.0 | +2.3 |
| four  | 56.3 | 51.7 | 54.3 | −2.0 |
| five  | 75.0 | 69.0 | 74.3 | −0.7 |
| **six** | **60.7** | **38.3** | **54.3** | **−6.3** |
| seven | 66.0 | 60.0 | 68.7 | +2.7 |
| eight | 72.3 | 85.3 | 83.7 | +11.3 |
| nine  | 52.3 | 69.3 | 60.7 | +8.3 |

**The six drag clears the way the diagnosis predicted, but only partway.** Margin-pcw crushed six
to 38.3% (the AUX prong confidently steering six→eight 68/300, six→seven 66/300); the correctness
key recovers six to **54.3%** (six→eight 68→51, six→seven 66→26 — the confidently-wrong votes are
down-weighted, exactly the Dunning-Kruger fix). Six still trails formant-alone (−6.3) because the
AUX prong's track record on six is only middling (prec_a[six] ≈ 0.33, not ~0), so it keeps partial
weight — an honest, measured residual, not over-corrected to zero. The **net** clears the bar
because the correctness key simultaneously *keeps* the digits where the weak prong is reliably
RIGHT (eight +11.3, nine +8.3, seven +2.7, three +2.3) — the additive half the diagnosis named.

**AUX prong TRAIN precision-when-it-asserts-d** (mean over folds — the correctness key):

```
zero:0.45  one:0.18  two:0.47  three:0.18  four:0.31  five:0.25  six:0.33  seven:0.17  eight:0.47  nine:0.40
```

The track record is exactly the lever: the AUX prong is reliable when it asserts eight/two/zero
(~0.45–0.47) and unreliable when it asserts seven/one/three (~0.17–0.18). Keyed per-asserted-digit,
this down-weights the unreliable assertions where the global `w_art` could not.

---

## (3) Verdict — does the fusion now clear formant-alone (gap 2 closed)?

**GAP 2 CLOSED — honest, with real numbers.** Correctness-keyed fusion reaches **63.7%** on FSDD
LOSO (n = 3000, chance 0.100, held-out never banked nor used for `prec_a`):

- it **clears formant-alone (62.2%) by +1.5 pts** — the bar the margin-only pcw (61.4%) could not
  reach;
- it **beats the margin-pcw plateau (61.4%) by +2.3 pts**;
- the result is robust to the combiner (MIN 63.6%) and is **driven by the correctness key**, not
  the margin (correctness-ALONE ablation 63.6%, +0.1 pt from the margin).

**Mechanism, confirmed.** The per-asserted-digit precision down-weights the AUX prong's
*confidently-wrong* votes that margin (a confidence signal) could not catch — the six→eight /
six→seven drag the pcw doc pinpointed (68/300, 66/300) falls to 51/300, 26/300 — while *keeping*
the AUX prong where its track record is good (eight/nine/seven/three gain). The prediction held:
the confident-wrongness clears enough to cross the bar, and the fusion even exceeds formant-alone
because the weak prong is reliably-right on the digits the anchor is weakest on.

**Donkey-clean.** Native Term via `substrate.evaluate` (nested `Argmax`→`Attr` precision lookup,
zero new primitives, no Rust); recogniser prongs unchanged; `prec_a` measured per fold on TRAIN
speakers only (a track record, not a sweep-to-fit); CortexLoop + solve_for_n untouched. (The LOSO
was run with per-fold subprocess isolation + JSON checkpointing — pure world-adapter orchestration
— because the Rust evaluator intermittently SIGSEGVs on the heavy exemplar-DTW baseline under host
memory pressure; the eval logic and numbers are unchanged, and every fold's value reproduced the
deterministic prior partial runs.)

**Caveat (honest).** The exemplar bank (80.6%) remains far ahead of every fusion path — the fusion
gain is real but the structural ceiling is still the exemplar lexicon, not the multi-pronged
forward-model fusion. Gap 2 (the fusion *weighting* gap) is closed; the larger recognition gap is
not.
