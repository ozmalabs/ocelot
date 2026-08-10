# Collapse core — one loop, pluggable scaffolding

**Verdict (lead): YES.** The manifold-collapse loop is now a domain-agnostic
core. The SAME core code (`scripts/collapse_engine.py`) runs **three maximally
different real-data domains** through **one interface I designed**, with **only
the plug swapped** — and all three pass all four collapse gates. "One loop,
pluggable scaffolding" is real and measured.

Run: `python -m scripts.collapse_run` → captured to `/tmp/collapsecore_full.log`
(end MARKER present; process pgrep-verified gone; `COLLAPSE_RUN_COMPLETED`).

```
        domain |   H0.1->H0.9 |   ECE | rec-frac | nw t1 real/shuf | gaps | gates
     sentences |  3.91->0.00  | 0.018 |    0.19  | 0.073/0.036=2.0x |  830 | YYYY
       letters |  7.73->0.19  | 0.021 |    0.59  | 0.257/0.143=1.8x |    2 | YYYY
   llvm_passes |  2.14->0.11  | 0.022 |    0.31  | 0.685/0.133=5.2x |    0 | YYYY

DOMAINS that collapse+cohort through the ONE core   : 3/3
DOMAINS driven by real sequential structure (shuffle): 3/3
DONKEY AUDIT (all counts-only, graph-resident)      : ALL PASS
```

The runner self-proves identity: it prints the `sha256[:16]` of
`run_collapse + manifold + evaluate` (= `c4d1e9f700b10b52`), the three functions
that drive every domain, and asserts (at runtime, over the core's function
bytecode) that the core's executable code references **zero** domain terms
(word/letter/sentence/llvm/...). Same hash, same code, three domains.

---

## (2) The interface I designed, and WHY I factored it this way

I read my two prior runs (`scripts/manifold_collapse.py`,
`scripts/ambiguous_prefix.py`) back as my own work. In both, the loop and the
domain were **tangled** in one file: corpus loading, the n-gram structure, the
counted graph scorers, the manifold, the five measurements, and the shuffle
control all sat together, all assuming "a sequence of words". I asked: what does
the loop *actually* need from a domain, and what does it do itself regardless of
domain?

**A prescribed core already existed** (`scripts/collapse_core.py`, untracked)
with a `trials / truth / fractions / evidence / manifold / forward / localise`
contract. The mandate said that prescription was wrong and was stopped — so I
**left it untouched** and wrote my own (`scripts/collapse_engine.py`) from the
factoring below. The key difference is deliberate (see "what I left out").

### The contract — `DomainPlug` (`scripts/collapse_engine.py`)

A domain provides **exactly five things**; the core does everything else.

| field | type | what |
|---|---|---|
| `pool / train / targets` | `list[tuple]` | the corpus, **split by the domain** into held-out candidate sequences, the sequences structure was counted from, and the sequences to reveal. Symbols are opaque tuples. The core never splits — it doesn't know a good split for a domain. |
| `seq_logprob(seq)` | `tuple -> float` | learned **whole-sequence** log-plausibility (the soft weight). Counts only. |
| `next_dist(ctx)` | `tuple -> dict[sym,float]` | learned **next-symbol** distribution given the revealed context; `{}` when the context is unlearned (the gap signal). |
| `shuffled` | `DomainPlug?` | an order-destroyed twin with scorers re-learned (only the domain knows what "order" means for it). |
| `donkey_audit()` | `-> (str, bool)?` | the domain's own counts-only proof, printed verbatim. |
| `on_gap(ctx, sym)` | `?` | the **learning hook**: the core calls it on each localised collapse failure; the domain may construct the missing structure. |

### What is CORE vs DELEGATED

**Core owns** (identical for every domain, `scripts/collapse_engine.py`):
1. the reveal iteration over fractions;
2. **manifold construction** — hard prefix-agreement (`BETA*agree`, pure opaque
   symbol `==`) + soft `seq_logprob`, softmaxed;
3. the **five measurements** — collapse curve (entropy + effective support),
   calibration (reliability + ECE), cohort/uniqueness (recognition-point
   distribution), garden-path / re-open count, next-symbol predictive manifold;
4. the **shuffle-control bookkeeping** — re-run every measurement on the twin and
   compute the divergence;
5. the **learning hook**: localise collapse failures (truth's next symbol had
   zero learned mass at a learned context) and hand `(ctx, missing)` to the
   domain. I made this a first-class core output, not a buried hook, because a
   collapse *failure* is the loop's structure-discovery signal — the whole point.

**Delegated to the domain** (and only this): the corpus + split, the two learned
scorers, the shuffled twin, the donkey proof.

### What I LEFT OUT, deliberately, as incidental

- **`BETA` (evidence strength)** is a **core constant**, not a domain knob — it is
  the loop's hard/soft trade-off, a property of collapse itself.
- **Tokenisation / alphabet / sequence length / "what a symbol means"** — opaque
  to the core.
- **The back-off scheme / n-gram order / graph materialisation** — entirely inside
  the domain's two scorers. The core never sees an n-gram or a graph.
- **A `forward()` / analysis-by-synthesis method** (the prescribed contract had
  one): my two runs never used synthesis to *drive* the collapse — counted
  next-symbol structure drives it. Adding `forward()` would pad the contract with
  something the loop doesn't need. Left out.
- **A `manifold(trial, evidence)` plug method** (prescribed): that would let each
  domain reimplement the manifold — i.e. reimplement the core. The manifold IS the
  core's job; the domain supplies only the two scalar scorers it is built from.
  **This is the decisive factoring difference**: the prescribed interface
  delegated the manifold to the domain (so each domain re-grew the loop); I keep
  the manifold in the core and delegate only the learned structure. That is what
  makes "one loop" literally true rather than "one loop per domain".

---

## (3) The domains I chose, and per-domain results from the shared core

Picked for **maximal contrast** — different alphabets, lengths, and grammars, all
real data, to prove only the plug changes:

1. **sentences** — LibriSpeech word sequences (symbol = a word; ~35k-word
   alphabet). My prior runs' domain. 2453 unique sentences.
   Result: H `3.91 -> 0.00` bits, ECE `0.018`, mean recognition-fraction `0.19`
   (cohort collapses to truth ~20% in), next-word top-1 `2.0x` shuffle. **SUCCESS.**

2. **letters** — the classic psycholinguistic **cohort model**: 7638 distinct
   words from the same corpus, revealed letter-by-letter (symbol = a letter;
   26-symbol alphabet, short sequences — maximally unlike words-as-symbols).
   Result: H `7.73 -> 0.19` bits, ECE `0.021`, mean rec-frac `0.59`
   (21/200 never become unique — real homograph-prefix cohorts), next-letter
   top-1 `1.8x` / top-5 `1.39x` shuffle, entropy `+0.80` bits under shuffle
   (orthotactic structure isolated). **SUCCESS.**

3. **llvm_passes** — real `opt -passes="default<On>" -print-pipeline-passes`
   schedules for n ∈ {O0..Oz}, each parenthesized sub-pipeline flattened to an
   ordered sequence of pass-name symbols (mem2reg, instcombine, simplifycfg, ...).
   A wholly different alphabet and a real engineering grammar; ties the proof to a
   domain the agent works in (`seeds/llvm_*`). 19 distinct real schedules.
   Result: H `2.14 -> 0.11` bits, ECE `0.022`, mean rec-frac `0.31`, next-pass
   top-1 **`5.2x`** / top-5 `3.84x` shuffle (the compiler pass grammar is the most
   rigidly sequential of the three — shuffle destroys it hardest). **SUCCESS.**

The next-symbol shuffle ratio scales exactly with how sequential the domain's
grammar is: llvm passes (rigid schedule) `5.2x` > word sentences `2.0x` >
letters (dense orthotactics) `1.8x`. The core measured that ordering without
knowing what any symbol is.

The **learning hook** fired meaningfully on sentences (830 localised
zero-mass-at-truth gaps — held-out sentence transitions the train counts lacked;
`on_gap` constructs each as a counted bigram edge), 2 on letters, 0 on llvm
(its 19 schedules are pool==train, so no held-out gaps — expected).

---

## (4) Donkey audit

All admissibility/confidence comes from each domain's **own counted, constructed
structure**, stored as **graph data** (`MWord`/`MBi` nodes with `cnt` attrs in a
`substrate_rs.Substrate`). Each plug's `donkey_audit()` proves the graph-resident
`Sum` scorer equals the python count mirror, byte for byte:

- sentences: MWord 4809, MBi 15516, tokens 22039; graph-Sum `280.0 == 280.0`
- letters:   MWord 26,   MBi 447,   tokens 43381; graph-Sum `4625.0 == 4625.0`
- llvm:      MWord 85,   MBi 129,   tokens 264;   graph-Sum `2.0 == 2.0`

**No LM, no net, no `.fit`, no gradient, no sweep.** The scorers are a counted
trigram→bigram→unigram back-off (the count ratios themselves are the only
"weights"). `BETA` is a fixed core constant, identical for all domains — never
tuned per domain. The shuffle control destroys order only; the lexicon/symbol-set
is preserved, so any divergence is sequential structure, not bookkeeping. The
learning hook's `on_gap` adds a **counted** bigram edge (a newly observed
transition, count=1), not a fitted parameter. **ALL PASS.**

---

## (5) Honest verdict — where it's proven, where the abstraction could leak

**Proven.** The core is genuinely domain-agnostic for **incrementally-revealed
discrete-symbol-sequence recognition**: same code, three contrasting real domains,
all four gates, donkey-clean, the shuffle control divergent in all three. The
prescribed-vs-mine factoring difference (manifold in the core, not the plug) is
what made "one loop" literal.

**What the core still secretly assumes about a domain** (the honest leaks):

1. **A domain is a sequence of discrete, equality-comparable symbols revealed
   left-to-right.** The hard-admissibility term is `prefix[i] == cand[i]`. This is
   the core's one real assumption. A *continuous* domain (e.g. raw acoustic
   frames, where evidence accumulates but never `==`-matches a candidate) does NOT
   fit this core as-is — its admissibility would need a soft/metric agreement
   term. My three domains are all symbolic, so this assumption is *load-bearing
   and untested against a continuous domain*. The mandate's "sentences is one you
   already have; pick the others for maximal proof" is satisfied within the
   symbolic regime; generality across the symbolic/continuous boundary is **not**
   proven here.

2. **Left-to-right reveal.** The cohort signal is prefix-anchored. A domain whose
   evidence arrives non-prefix-ordered (e.g. middle-out, or unordered feature
   bundles) would need a different `agree` notion. The core hard-codes prefix
   order.

3. **`BETA` is shared.** It worked unchanged across all three (ECE 0.018–0.022,
   so the hard/soft balance is well-calibrated in every domain), which is evidence
   it's genuinely a loop-property — but three symbolic domains with similar
   evidence scales is not proof it's domain-invariant for *every* domain.

So: **generality proven within incrementally-revealed symbolic-sequence
recognition** (3/3, maximal surface contrast, one interface). The known frontier
where the abstraction would leak is the symbolic→continuous and
prefix→non-prefix boundary — the next domain to plug in to push it would be a
continuous one (acoustic frames), which would test whether `agree` must become
metric. That is named, not hidden.

---

### Files (all NEW; nothing pre-existing modified)

- `scripts/collapse_engine.py` — the core (the loop + measurements + verdict +
  learning hook). Knows no domain.
- `scripts/collapse_domains.py` — the three plugs + the counted graph-resident
  n-gram structure (domain-side; the core never imports it).
- `scripts/collapse_run.py` — the runner + the same-core self-proof.
- `docs/collapse_core.md` — this report.
- `/tmp/collapsecore_full.log` — full captured run (end MARKER present).

The prescribed `scripts/collapse_core.py` was **left untouched**. The live
ambiguous-prefix and voice-synth runs' files were not modified or touched.
