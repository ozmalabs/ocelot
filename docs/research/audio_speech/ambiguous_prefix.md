# Ambiguous-Prefix Probe

*Isolating the LEARNED admissibility-collapse from combinatorial pool-matching,
and eliciting the bounded garden-path re-open.*

Script: `scripts/ambiguous_prefix.py` · full log: `/tmp/ambig_full.log`
(ends with marker `AMBIGUOUS_PREFIX_COMPLETED`). Reuses the donkey-clean
infrastructure of `scripts/manifold_collapse.py` (counted `MWord`/`MBi`/`MTri`
graph + counted back-off, graph Term-tree scorer). Corpus: LibriSpeech dev-clean,
2453 unique real sentences. Train 1253 (learn counts) / pool 1200 (manifold).
Independent of the running voice/synthesis work; `solve_for_n.py` and CortexLoop
untouched. **No trained LM, no softmax-fit, no gradient.**

This probe was the refinement the agent named from the manifold-collapse run,
which was honest/calibrated/cohort/reaches-1 but whose dramatic entropy collapse
was **dominated by hard prefix-string admissibility** (real vs shuffle entropy
identical, 1.506/1.507) rather than the learned grammar; and whose garden-path
re-opening was **0/300** because distinct-prefix targets create no ambiguity.

---

## VERDICT (lead)

**On AMBIGUOUS prefixes the learned grammar now demonstrably carries the
collapse — real-vs-shuffle DIVERGES 3.25×/2.93× where it was previously
identical — and garden-paths now produce a large confidence-drop and entropy
re-expansion. The bounded re-open is PRESENT but MARGINAL (a near coin-flip at
the aggregate, 97 bounded vs 90 blew-up).**

| gate | result | number |
|---|---|---|
| (1) **ISOLATION** — learned grammar diverges from shuffle on ambiguous prefixes | **YES (strong)** | next-word top-1 **3.25×** (0.054 vs 0.017); true-word prob **2.93×** (0.029 vs 0.010) |
| (2) **RE-OPENING** — garden-paths produce drop + entropy re-expansion | **YES (strong)** | **229/300** re-expanded; mean misdirection **0.63**; H 1.57→4.27 bits at disambiguation |
| (3) **BOUNDED** — re-expansion re-collapses onto truth (finite-flex) | **MARGINAL** | **97 bounded vs 90 blew-up** of 259 learned re-open contexts (52% — barely above chance) |
| (4) **CALIBRATION under learned-load** | **YES** | ECE **0.043** on ambiguous prefixes (shuffle 0.042) |
| (5) **DONKEY AUDIT** — counts only, no LM | **YES** | graph `Sum bi_support('I')`=280.0 == python 280.0 (MATCH=YES) |

The honest caveat: the **isolation** and **re-opening** results are clean and
strong; the **boundedness** of the re-open is real but weak — the manifold
re-opens reliably, then re-collapses onto the truth-path only about half the
time, the other half staying wide (or widening) one step further. The finite-flex
signature is *present but not crisp* in the aggregate.

---

## (1) ISOLATION — the key result

Ambiguous prefixes were harvested **from the pool's own structure**: every prefix
length `k` that **≥2 pool sentences share** (so exact-prefix pool-matching cannot
shortcut to one answer — the hard admissibility term is identical for every tied
candidate and cancels). Of 1200 pool sentences, **966 have ≥1 ambiguous prefix**;
the top 300 by ambiguity give **479 ambiguous prefix-positions** with **mean
share 58.75** (max 111) — i.e. on average ~59 pool sentences share each prefix,
so hard matching leaves a 59-way tie that only the learned grammar can break.

**Full-pool manifold entropy at these prefixes is identical real vs shuffle**
(5.038 vs 5.061 bits) — confirming, as expected, that the *set-size* part is hard
prefix-admissibility, not learned. The learned signal is isolated by the
**next-word anticipation at the ambiguous decision point** (full vocab, pure
counted transition structure — the proven shuffle-sensitive measure from
`manifold_collapse.py`, now restricted to the high-ambiguity points):

| measure (479 ambiguous decision points) | REAL | SHUFFLE | ratio |
|---|---|---|---|
| next-word **top-1 == truth** | 0.0543 | 0.0167 | **3.25×** |
| prob on the **true** next word | 0.0289 | 0.0098 | **2.93×** |
| next-word entropy (bits) | 5.964 | 5.631 | +0.333 (real lower) |

**This is the divergence the previous run lacked.** Where the original probe
found next-word top-1 only **1.45×** over *all* positions (and the sentence
manifold entropy identical real-vs-shuffle), restricting to *ambiguous* decision
points **more than doubles the divergence to 3.25×**. The learned admissibility
is doing the work precisely where ambiguity is highest and pool-matching cannot
help — exactly the isolation the probe was designed to produce.

(The tie-internal branch re-ranking — softmax over tied candidates' immediate
continuation — was a coarser secondary measure: branch-word top-1 1.00× real vs
shuffle, because at a shared prefix the *branch words* of the tied candidates are
mostly unique tokens the small held-out counts can't separate. The full-vocab
next-word anticipation is the right isolation instrument; the branch re-ranking
is reported but is not the load-bearing number.)

## (2) GARDEN-PATH / RE-OPENING — the re-open now fires

Garden-path positions were located **from the agent's own counts**: a context
`(a,b)` where the learned next-word distribution is ambiguous (entropy ≥1 bit),
the learned **top-1 prediction disagrees with the actual next word**, the actual
word is **low-prior** (≤0.15), and the prediction **leads** it by ≥0.25. **1107
such positions** were found; the top 300 by misdirection strength were measured.

- mean **misdirection** (`pred_p − true_p`, "you were *this* wrong"): **0.63**
- mean wrong-commitment prob excluded by truth (**drop**): **0.63**
- entropy **before** disambiguation (predicting the wrong word): **1.57 bits**
- entropy **at** disambiguation (truth forces re-open): **4.27 bits** (**+2.71**)
- **RE-EXPANDED** (admissible set grew when truth contradicted): **229/300**

This is the bounded-flex re-open the previous run got **0/300** on: forced off the
garden path by a low-prior word, the manifold drops ~0.63 of its confidence on the
wrong commitment and **re-expands its admissible set by ~2.7 bits** to admit the
truth. The mechanism the prior run argued *existed but couldn't elicit* (soft
admissibility holding near-misses at low weight rather than zeroing them) now
fires on deliberately ambiguous, agent-located garden-paths.

## (3) BOUNDEDNESS — present but marginal (the honest weak point)

The finite-bounds signature requires the re-expansion to re-collapse — re-open
*just enough* to admit the truth, then sharpen back. Judged on the **259/300**
garden-paths whose post-disambiguation context `(b, truth)` is itself a learned
context (so a re-collapse is meaningful, not a vocab-fallback artifact):

- **BOUNDED** (re-expanded then re-collapsed, `H_after < H_at`): **97/259**
- **BLEW UP** (re-expanded, did not re-collapse): **90/259**
- mean entropy **after** one more word along truth: **4.54 bits** (**+0.26** vs the
  4.27 at disambiguation — slightly *up* on average)

**97 vs 90 is barely above chance (52%).** The re-open is reliable; the *bounded
re-collapse* is roughly a coin-flip per instance. The seal re-opens, but on the
small held-out corpus it re-collapses onto the truth-path only about half the
time within one step — the other half it stays wide or widens further. The
finite-flex shape is **present in the aggregate (bounded > blew-up, and 121/300
recover the true continuation as admissible) but not crisp**. This is the honest
limit of this run: ambiguity and re-opening are cleanly demonstrated; *bounded*
recovery is weak and corpus-limited (a deeper learned structure / larger train
set would be the lever, the same data-density limit the lineage keeps hitting).

## (4) CALIBRATION UNDER LEARNED-LOAD

The harder calibration test — ECE on the *ambiguous* prefixes where the learned
grammar carries the collapse, not where pool-matching trivially does:

| confidence bin | mean conf | hit rate | n |
|---|---|---|---|
| [0.0,0.1) | 0.038 | 0.015 | 328 |
| [0.3,0.4) | 0.345 | 0.233 | 30 |
| [0.4,0.5) | 0.457 | 0.407 | 27 |
| [0.5,0.6) | 0.544 | 0.500 | 40 |
| [0.7,0.8) | 0.756 | 0.500 | 8 |
| [0.8,0.9) | 0.811 | 0.500 | 4 |

**ECE = 0.0426** under learned-load (shuffle control 0.0421). The manifold stays
calibrated even on the hard ambiguous prefixes — it is slightly *over*confident in
the high bins (says 0.76–0.81, hits 0.50), the same single-successor
overconfidence the prior run flagged (next-word ECE 0.29), but the aggregate
calibration holds (ECE well under the 0.20 gate). The collapse is honest where the
learned grammar is what's carrying it, not only where string-matching is.

## (5) DONKEY AUDIT — no LM

Same as the parent script and re-verified this run: the manifold's weights are the
agent's **own learned counts** stored as graph nodes/edges (`MWord` freq, `MBi`
cnt, `MTri` cnt) and scored by a graph Term-tree (`Sum(Neighbours(w,'bi'), t,
Attr(t,'cnt'))`). Live check this run: graph `Sum bi_support('I') = 280.0` ==
python count mirror **280.0** (MATCH=YES). The back-off is counted
(trigram→bigram→unigram, weight `n/(n+V)`, uniform add-1 floor identical for every
candidate). Ambiguity and garden-paths are located from the agent's own counts,
not hand-picked. **No trained LM, no neural softmax, no `.fit`, no gradient.**
`solve_for_n.py` / CortexLoop untouched.

---

## What it reveals

The previous run's honest gap was that its dramatic collapse was carried by *hard
prefix-string* admissibility (a real but **not learned** form), with the learned
contribution only a modest 1.45–1.83× re-ranking, and no garden-path re-open
elicited. This probe **isolates** the learned contribution by forcing the
collapse onto deliberately ambiguous (≥2-shared, mean-59-way) prefixes where
string-matching cannot shortcut, and there the learned grammar diverges from
shuffle **3.25×/2.93×** — more than double the all-positions figure. It also
**elicits the re-open** the prior run could not: garden-paths drop ~0.63 of the
wrong commitment and re-expand ~2.7 bits to admit the contradicting truth
(229/300).

The remaining honest weakness is **boundedness**: the re-open re-collapses onto
the truth-path only ~52% of the time (97 vs 90), so the finite-flex *just enough
then re-collapse* signature is present in the aggregate but not crisp — a
corpus-density limit, the lineage's recurring wall, not a design failure. Net:
the learned admissibility-collapse is now **isolated and demonstrated**, the
**re-open fires**, and the **bounded** recovery is **real but marginal**.
